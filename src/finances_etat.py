#!/usr/bin/env python3
"""Les finances de l'État, lues au portail du ministère de l'Économie (#1053).

Les fiches de gouvernement ne disaient rien du budget. Ce module lit ce que
`data.economie.gouv.fr` publie sous **Licence Ouverte 2.0**, et l'écrit tel
quel sous `raw_data/finances_etat.json` — rien n'y est agrégé par gouvernement,
rien n'y est réparti : l'unité est **l'exercice budgétaire** (arbitré le
08/10/2026), et c'est la date de la loi de finances, déjà dans
`pivot_data/textes_promulgues.json`, qui dira plus loin quel gouvernement l'a
fait voter.

## Ce que ce module lit

Deux familles, qui ne se recouvrent pas :

- **les grandes lignes** — un seul jeu, les situations mensuelles budgétaires
  de la DGFiP : 26 lignes (recettes par impôt, dépenses par nature, soldes),
  en cumul à chaque fin de mois depuis janvier 2013, et pour les mêmes lignes
  les montants des lois de finances. **Aucun ministère** ;
- **les crédits de paiement du budget général, programme par programme, avec
  leur ministère** — un fichier par exercice et par côté (voté, consommé), de
  2015 à 2025. La maille publiée plus loin est le ministère (arbitré le
  12/10/2026) ; le programme est gardé ici parce que c'est par lui que le
  consommé de 2023 à 2025 retrouve son ministère.

## La borne, et pourquoi elle est à 2015

Avant 2015 les libellés de ministère sont abrégés par la source
(« AffSoc&Santé », « Enseign sup et rech ») : les relier aux portefeuilles
demanderait une table tenue à la main. Arbitré le 12/10/2026 : on commence en
2015 et on le déclare. Les grandes lignes, elles, commencent en 2013 parce que
la source commence là.

## Ce qui manque, et qui se déclare

Un côté qu'aucun fichier ne porte n'est ni tu ni mis à zéro (§2 règle 5) : il
est publié `null` à côté de son `*_non_resolu`, qui nomme la raison. Au
12/10/2026 : le voté par ministère de 2015 (seul le projet est publié), le
consommé de 2021 et de 2022 (PDF seulement).

## Les pièges, tous payés en mesurant

1. **Onze années, onze formats.** CSV en cp1252 avec quatre lignes de titre
   avant les colonnes (2015-2017), CSV aux fins de ligne `\\r` (2018), export
   JSON (2018, 2019), classeur `.xls` dont le ministère n'est qu'un code
   (2019, 2020), CSV en UTF-8 à virgule décimale (2023-2025). D'où un lecteur
   par forme, et `LECTEURS` qui dit lequel sert à quoi.
2. **Le serveur compresse sans le dire.** Une pièce jointe peut arriver en
   gzip sans en-tête `Content-Encoding`, ou en UTF-16 : `decoder()` regarde
   les premiers octets, jamais l'extension.
3. **Les fichiers d'exécution 2023-2025 n'ont pas de colonne ministère.** Ils
   portent le programme (« … - 105 ») ; le ministère vient de la nomenclature
   du budget de la même année, où chaque programme relève d'un seul ministère
   (mesuré sur les trois années : zéro programme à deux ministères).
4. **Les colonnes « loi votée » du jeu 2023 par ministère valent 4.0 partout.**
   Ce jeu ne sert donc que de nomenclature ; le voté de 2023 à 2025 se lit dans
   la colonne `LFI` du fichier d'exécution, qui le met sur la même ligne que le
   consommé.
5. **La colonne `Exécution` du fichier des textes est décalée d'un an de 2019
   à 2021.** Elle est gardée telle que la source la donne ; le réalisé d'un
   exercice se lit dans le cumul de décembre des séries mensuelles.

Usage :

    python3 src/finances_etat.py                 # ce qui peut avoir bougé
    python3 src/finances_etat.py --tout          # tout relire
    python3 src/finances_etat.py --exercices 2024 2025
"""

from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import re
import sys
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from licences import LICENCE_FINANCES_ETAT  # noqa: E402

CHEMIN_PAR_DEFAUT = Path("raw_data") / "finances_etat.json"
SCHEMA_VERSION = "finances-etat-v1"

#: La couverture par ministère commence ici. Voir le docstring du module.
BORNE_MINISTERE = 2015

#: Le portail, et la forme de ses trois adresses. Une pièce jointe garde son
#: identifiant tant que le ministère ne republie pas le jeu ; un exercice clos
#: ne se republie pas.
PORTAIL = "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets"
URL_PIECE = PORTAIL + "/{jeu}/attachments/{piece}"
URL_EXPORT = PORTAIL + "/{jeu}/exports/json"
URL_FICHE = "https://data.economie.gouv.fr/explore/dataset/{jeu}/"

#: Les fichiers de 2015 à 2017 ne sont plus que sur data.gouv.fr, à une adresse
#: datée qui ne bouge pas.
URL_ARCHIVE = ("https://static.data.gouv.fr/resources/plr-{an}-projet-de-loi-de-"
               "reglement-pour-lannee-{an}-donnees-de-lexecution-budgetaire/"
               "{horodatage}/PLR{an}-Exec-Min_CP-BG.csv")

JEU_MENSUEL = "situations-mensuelles-budgetaires-series-longues"
PIECES_MENSUELLES = ("series_longues_smb_dgfip_2013_2023_csv",
                     "serie_longue_smb_dgfip_2024_xxcsv")
PIECES_TEXTES = ("textes_legislatifs_open_data_2013_2023_csv",
                 "textes_legislatifs_2024_xxcsv")

#: Sous ce nombre de programmes, un fichier n'est pas un budget général : le
#: plus petit mesuré en porte 121. Un champ déplacé par la source rendrait une
#: liste courte ou des montants nuls, qui se publieraient comme un budget.
PLANCHER_PROGRAMMES = 100


class FinancesIndisponibles(RuntimeError):
    """Le portail n'a rien rendu d'exploitable pour ce fichier.

    Levée plutôt que de rendre une liste vide : une liste vide se publierait
    comme « aucun crédit », qui est un constat sur le budget et non sur la
    panne (§2 règle 5).
    """


# ── Décodage ────────────────────────────────────────────────────────────────

def decoder(contenu: bytes) -> str:
    """Le texte d'un fichier du portail, quel que soit son emballage.

    Trois emballages mesurés le 12/10/2026 sur un même jeu : gzip sans en-tête
    HTTP, UTF-16 avec marque d'ordre, cp1252 nu. L'extension ne dit rien.
    """
    if contenu[:2] == b"\x1f\x8b":
        contenu = gzip.decompress(contenu)
    if contenu[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return contenu.decode("utf-16")
    try:
        return contenu.decode("utf-8-sig")
    except UnicodeDecodeError:
        return contenu.decode("cp1252")


def nombre(valeur: Any) -> Optional[float]:
    """Un montant de la source, ou `None` s'il n'y en a pas.

    La source écrit « 1 961 961 115 », « 742542019,3 » ou un flottant. Une
    cellule vide rend `None`, jamais 0 : le zéro est un montant (§2 règle 5).
    """
    if isinstance(valeur, bool):
        return None
    if isinstance(valeur, (int, float)):
        return float(valeur)
    texte = (valeur or "").strip().replace("\xa0", "").replace(" ", "").replace(",", ".")
    if not texte:
        return None
    try:
        return float(texte)
    except ValueError:
        return None


def code_nu(valeur: Any) -> Optional[str]:
    """`MIN01`, `01`, `1.0` et `1` désignent le même ministère : `1`.

    Le code est stable d'une année à l'autre quand le libellé change à chaque
    remaniement — mais la source l'écrit de quatre façons.
    """
    if valeur is None:
        return None
    if isinstance(valeur, float) and valeur.is_integer():
        valeur = int(valeur)
    chiffres = re.sub(r"\D", "", str(valeur).split(".")[0])
    return chiffres.lstrip("0") or ("0" if chiffres else None)


def _libelle(valeur: Any) -> Optional[str]:
    """Le libellé tel que la source l'écrit, espaces doubles repliés."""
    texte = " ".join(str(valeur or "").split())
    return texte or None


def _lignes_csv(texte: str, premiere_colonne: Optional[str] = None) -> list[dict[str, str]]:
    """Les lignes d'un CSV à point-virgule, en sautant ses lignes de titre.

    Les fichiers de 2015 à 2017 ouvrent sur quatre lignes (« GESTION;2015 »…)
    avant les noms de colonnes : `premiere_colonne` dit où ils commencent.
    """
    lignes = texte.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    debut = 0
    if premiere_colonne:
        debut = next((i for i, ligne in enumerate(lignes)
                      if ligne.startswith(premiere_colonne + ";")), -1)
        if debut < 0:
            raise FinancesIndisponibles(
                f"colonne « {premiere_colonne} » introuvable en tête de fichier")
    return list(csv.DictReader(io.StringIO("\n".join(lignes[debut:])), delimiter=";"))


def _colonne(ligne: dict[str, Any], *morceaux: str) -> str:
    """Le nom de la colonne qui contient tous ces morceaux.

    Les en-têtes portent l'année (« CP (T2 + HORS T2)  LFI 2018 ») et des
    espaces doubles : on les cherche par ce qu'ils disent, pas à la lettre.
    """
    for nom in ligne:
        plat = " ".join((nom or "").split()).lower()
        if all(m.lower() in plat for m in morceaux):
            return nom
    raise FinancesIndisponibles(f"colonne introuvable : {morceaux}")


# ── Les programmes d'un exercice ────────────────────────────────────────────

class _Cumul:
    """Additionne les lignes d'un fichier en une ligne par programme.

    Les fichiers descendent à l'action, au titre ou à la catégorie ; ce module
    s'arrête au programme. Un programme vu sous deux ministères lève : la
    jointure de 2023-2025 repose sur le fait que cela n'arrive pas.
    """

    def __init__(self) -> None:
        self.cp: dict[str, float] = defaultdict(float)
        self.ministere: dict[str, tuple[Optional[str], Optional[str]]] = {}

    def ajouter(self, programme: Any, montant: Any, code: Any = None, libelle: Any = None) -> None:
        prog = code_nu(programme)
        if not prog:
            return
        valeur = nombre(montant)
        self.cp[prog] += valeur or 0.0
        if code is not None or libelle is not None:
            vu = (code_nu(code), _libelle(libelle))
            deja = self.ministere.setdefault(prog, vu)
            if deja != vu:
                raise FinancesIndisponibles(
                    f"programme {prog} rattaché à deux ministères : {deja} et {vu}")

    def lignes(self, libelles: Optional[dict[str, str]] = None,
               ministeres: Optional[dict[str, tuple[Optional[str], Optional[str]]]] = None,
               ) -> list[dict[str, Any]]:
        sortie = []
        for prog in sorted(self.cp, key=int):
            code, lib = (ministeres or self.ministere).get(prog, (None, None))
            if lib is None and code and libelles:
                lib = libelles.get(code)
            sortie.append({"programme": prog, "ministere_code": code, "ministere": lib,
                           "cp": round(self.cp[prog], 2)})
        return sortie


def _est_bg(valeur: Any) -> bool:
    return str(valeur or "").strip() in ("BG", "Budget général")


def lire_vote_2016(texte: str) -> list[dict[str, Any]]:
    """`LFI2016-T2_HT2-BG-Ministere.csv`, et le même en 2017 : budget général seul."""
    cumul = _Cumul()
    for ligne in _lignes_csv(texte, "Ministère"):
        cumul.ajouter(ligne.get("Programme"), ligne.get(_colonne(ligne, "total cp")),
                      ligne.get("Ministère"), ligne.get(_colonne(ligne, "libellé ministère")))
    return cumul.lignes()


def lire_vote_2018(texte: str) -> list[dict[str, Any]]:
    """`LFI_2018_…_PROG_MIN.csv` : tous les budgets, une ligne par programme."""
    cumul = _Cumul()
    for ligne in _lignes_csv(texte):
        if _est_bg(ligne.get("Type de Budget")):
            cumul.ajouter(ligne.get("Code Programme"),
                          ligne.get(_colonne(ligne, "cp (t2 + hors t2)")),
                          ligne.get("Code Ministère"), ligne.get("Ministère"))
    return cumul.lignes()


def lire_vote_2019(texte: str) -> list[dict[str, Any]]:
    """L'export JSON du jeu « LFI 2019 »."""
    cumul = _Cumul()
    for ligne in json.loads(texte):
        if _est_bg(ligne.get("type_de_budget")):
            cumul.ajouter(ligne.get("code_programme"), ligne.get("cp_t2_hors_t2_lfi_2019"),
                          ligne.get("code_ministere"), ligne.get("ministere"))
    return cumul.lignes()


def lire_nomenclature_2020(texte: str) -> dict[str, str]:
    """`LFI2020-Nomenclature.csv` : le libellé de chaque code de ministère."""
    return {code_nu(l["code"]): _libelle(l["Libelle"])
            for l in _lignes_csv(texte) if (l.get("Type ligne") or "").strip() == "Ministere"}


def lire_vote_2020(texte: str, libelles: dict[str, str]) -> list[dict[str, Any]]:
    """`LFI2020-crédits.csv` : le ministère n'y est qu'un code."""
    cumul = _Cumul()
    for ligne in _lignes_csv(texte):
        if _est_bg(ligne.get("typeBudget")):
            cumul.ajouter(ligne.get("programme"), ligne.get(_colonne(ligne, "cp lfi")),
                          ligne.get("ministere"))
    return cumul.lignes(libelles)


def lire_vote_2021(texte: str) -> list[dict[str, Any]]:
    """`LFI2021_crédits-AE_CP.csv` et `LFI2022_detaillee.csv` : projet,
    amendements et loi votée côte à côte — seule la loi votée est lue ici."""
    cumul = _Cumul()
    for ligne in _lignes_csv(texte):
        if _est_bg(ligne.get("Type Mission")):
            cumul.ajouter(ligne.get("Programme"), ligne.get(_colonne(ligne, "cp ( t2 + ht2) lfi")),
                          ligne.get("Code Ministère"), ligne.get("Libellé Ministère"))
    return cumul.lignes()


def lire_realise_2015(texte: str) -> list[dict[str, Any]]:
    """`PLR2015-Exec-Min_CP-BG.csv`, et le même en 2016."""
    cumul = _Cumul()
    for ligne in _lignes_csv(texte, "Ministère"):
        cumul.ajouter(ligne.get("Programme"), ligne.get(_colonne(ligne, "total général")),
                      ligne.get("Ministère"), ligne.get(_colonne(ligne, "libellé ministère")))
    return cumul.lignes()


def lire_realise_2017(texte: str) -> list[dict[str, Any]]:
    """`PLR2017-Exec-Min_CP-BG.csv` : sept colonnes de titres, sans total."""
    cumul = _Cumul()
    for ligne in _lignes_csv(texte):
        if not _est_bg(ligne.get(_colonne(ligne, "type de budget"))):
            continue
        titres = [nombre(v) for nom, v in ligne.items() if nom and "EXEC CP" in nom]
        cumul.ajouter(ligne.get("Code Programme"), sum(t for t in titres if t is not None),
                      ligne.get(_colonne(ligne, "code ministère")),
                      ligne.get(next(n for n in ligne if n and n.startswith("Ministère au"))))
    return cumul.lignes()


def lire_realise_2018(texte: str) -> list[dict[str, Any]]:
    """L'export JSON du jeu « PLR 2018 », au ministère « du 1er janvier »."""
    cumul = _Cumul()
    for ligne in json.loads(texte):
        if _est_bg(ligne.get("type_de_budget")):
            cumul.ajouter(ligne.get("code_programme"), ligne.get("exec_cp_t2_hors_t2_2018_rap_2018"),
                          ligne.get("code_ministere_au_1er_janvier_2018"),
                          ligne.get("ministere_au_1er_janvier_2018"))
    return cumul.lignes()


def _feuille(contenu: bytes) -> list[list[Any]]:
    """Les lignes de la première feuille d'un classeur `.xls`."""
    import xlrd  # import tardif : seuls 2019 et 2020 en ont besoin

    feuille = xlrd.open_workbook(file_contents=contenu).sheet_by_index(0)
    return [feuille.row_values(i) for i in range(feuille.nrows)]


def lire_nomenclature_xls(contenu: bytes) -> dict[str, str]:
    """`PLR2019-Nomenclature.xls` : les lignes `MIN` donnent code et libellé."""
    lignes = _feuille(contenu)
    return {code_nu(l[2]): _libelle(l[5]) for l in lignes[1:]
            if str(l[0]).strip() == "MIN" and code_nu(l[2])}


def lire_realise_xls(contenu: bytes, libelles: dict[str, str]) -> list[dict[str, Any]]:
    """`PLR2019-Credits_Destination_Nature.xls`, et le même en 2020."""
    lignes = _feuille(contenu)
    entete = [str(c).strip() for c in lignes[0]]
    i_bud, i_min, i_pgm, i_cp = (entete.index(n) for n in
                                 ("typeBudget", "ministere", "programme", "CP EXEC"))
    cumul = _Cumul()
    for ligne in lignes[1:]:
        if _est_bg(ligne[i_bud]):
            cumul.ajouter(ligne[i_pgm], ligne[i_cp], ligne[i_min])
    return cumul.lignes(libelles)


def lire_nomenclature_json(texte: str) -> dict[str, tuple[Optional[str], Optional[str]]]:
    """Programme → ministère, dans le jeu du budget de l'année (2023-2025).

    Trois jeux, trois nommages : `type_mission` ou `typebudget`, le libellé
    sous `libelle_ministere` ou sous `ministere`, et pas de code en 2024.
    """
    cumul = _Cumul()
    for ligne in json.loads(texte):
        if not _est_bg(ligne.get("type_mission", ligne.get("typebudget"))):
            continue
        if "libelle_ministere" in ligne:
            code, lib = ligne.get("code_ministere", ligne.get("ministere")), ligne["libelle_ministere"]
        else:
            code, lib = None, ligne.get("ministere")
        cumul.ajouter(ligne.get("programme"), 0, code, lib)
    return dict(cumul.ministere)


def lire_etat_cp(texte: str, ministeres: dict[str, tuple[Optional[str], Optional[str]]],
                 ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """`Annexe1-Etat_CP-2025.csv` : le voté et le consommé sur la même ligne.

    Rend `(voté, consommé)`. Le programme est la fin du libellé (« … - 105 »).
    Un programme absent de la nomenclature garde un ministère `null` : il n'est
    pas rangé ailleurs (mesuré : le 367, à montant nul, en 2023 et 2024).
    """
    vote, realise = _Cumul(), _Cumul()
    for ligne in _lignes_csv(texte):
        m = re.search(r"-\s*(\d{3})\s*$", ligne.get("Programme") or "")
        if not m:
            raise FinancesIndisponibles(f"programme sans code : {ligne.get('Programme')!r}")
        vote.ajouter(m.group(1), ligne.get("LFI"))
        realise.ajouter(m.group(1), ligne.get("Depenses_constatees"))
    return vote.lignes(ministeres=ministeres), realise.lignes(ministeres=ministeres)


# ── Ce que chaque exercice lit ──────────────────────────────────────────────

def _piece(jeu: str, piece: str) -> str:
    return URL_PIECE.format(jeu=jeu, piece=piece)


def _archive(an: int, horodatage: str) -> str:
    return URL_ARCHIVE.format(an=an, horodatage=horodatage)


_LFI = "loi-de-finances-initiale-pour-{an}-lfi-{an}"
_PLFI = "projet-de-loi-de-finances-initiale-pour-{an}-lfi-{an}"
_PLRG = ("projet-de-loi-relatif-aux-resultats-de-la-gestion-et-portant-approbation-"
         "des-comptes-de-lannee-plrg-{an}")

#: Exercice → côté → ce qu'il faut lire. `fichier` porte les montants,
#: `nomenclature` ce qui donne le ministère quand le fichier ne le porte pas.
#: Une `raison` à la place déclare l'absence. **Ajouter un exercice, c'est
#: ajouter une entrée ici** — et un test sur une ligne copiée de son fichier.
LECTEURS: dict[int, dict[str, dict[str, Any]]] = {
    2015: {
        "vote": {"raison": "la loi de finances 2015 par ministère n'est pas publiée en "
                           "données : seul le projet l'est"},
        "realise": {"fichier": _archive(2015, "20160606-181537"), "lire": "realise_2015"},
    },
    2016: {
        "vote": {"fichier": _piece(_LFI.format(an=2016), "lfi2016_t2_ht2_bg_ministere_csv"),
                 "lire": "vote_2016"},
        "realise": {"fichier": _archive(2016, "20170706-113850"), "lire": "realise_2015"},
    },
    2017: {
        "vote": {"fichier": _piece(_LFI.format(an=2017), "lfi2017_t2_ht2_bg_ministere_csv"),
                 "lire": "vote_2016"},
        "realise": {"fichier": _archive(2017, "20180601-181647"), "lire": "realise_2017"},
    },
    2018: {
        "vote": {"fichier": _piece(_LFI.format(an=2018),
                                   "lfi_2018_t2_ht2_etpt_bg_cas_ccf_ba_prog_min_csv"),
                 "lire": "vote_2018"},
        "realise": {"fichier": URL_EXPORT.format(jeu="projet-de-loi-de-reglement-2019-plr-2019"),
                    "lire": "realise_2018"},
    },
    2019: {
        "vote": {"fichier": URL_EXPORT.format(jeu=_LFI.format(an=2019)), "lire": "vote_2019"},
        "realise": {"fichier": _piece("projet-de-loi-de-reglement-2019-plr-20192",
                                      "plr2019_credits_destination_nature_xls"),
                    "nomenclature": _piece("projet-de-loi-de-reglement-2019-plr-20192",
                                           "plr2019_nomenclature_xls"),
                    "lire": "realise_xls"},
    },
    2020: {
        "vote": {"fichier": _piece(_PLFI.format(an=2020), "lfi2020_credits_csv"),
                 "nomenclature": _piece(_PLFI.format(an=2020), "lfi2020_nomenclature_csv"),
                 "lire": "vote_2020"},
        "realise": {"fichier": _piece("projet-de-loi-de-reglement-2020-plr-2020",
                                      "plr2020_credits_destination_nature_xls"),
                    "nomenclature": _piece("projet-de-loi-de-reglement-2020-plr-2020",
                                           "plr2020_nomenclature_xls"),
                    "lire": "realise_xls"},
    },
    2021: {
        "vote": {"fichier": _piece(_PLFI.format(an=2021), "lfi2021_credits_ae_cp_csv"),
                 "lire": "vote_2021"},
        "realise": {"raison": "le ministère n'a publié l'exécution 2021 par programme "
                              "qu'en PDF"},
    },
    2022: {
        "vote": {"fichier": _piece(_PLFI.format(an=2022), "lfi2022_detaillee_csv"),
                 "lire": "vote_2021"},
        "realise": {"raison": "le ministère n'a publié l'exécution 2022 par programme "
                              "qu'en PDF"},
    },
    2023: {
        "etat": {"fichier": _piece(_PLRG.format(an=2023), "annexe1_etat_cp_2023_csv"),
                 "nomenclature": URL_EXPORT.format(
                     jeu="credits-ae-et-cp-votes-nomenclature-par-destination-et-nature-lfi-2023")},
    },
    2024: {
        "etat": {"fichier": _piece("plrg-2024", "annexe1_etat_cp_2024_csv"),
                 "nomenclature": URL_EXPORT.format(
                     jeu="plf-2024-depenses-2024-selon-nomenclatures-destination-et-nature")},
    },
    2025: {
        "etat": {"fichier": _piece(_PLRG.format(an=2025), "annexe1_etat_cp_2025csv"),
                 "nomenclature": URL_EXPORT.format(jeu="plf25-depenses-2025-selon-destination")},
    },
}


def _verifier(lignes: list[dict[str, Any]], quoi: str) -> list[dict[str, Any]]:
    """Refuse ce qui ne peut pas être un budget général.

    Un fichier dont la source a renommé une colonne se lirait sans erreur et
    rendrait trois lignes ou des zéros. Mieux vaut échouer ici que publier.
    """
    if len(lignes) < PLANCHER_PROGRAMMES:
        raise FinancesIndisponibles(
            f"{quoi} : {len(lignes)} programmes lus, moins que les {PLANCHER_PROGRAMMES} attendus")
    if not any(l["cp"] for l in lignes):
        raise FinancesIndisponibles(f"{quoi} : tous les montants sont nuls")
    return lignes


def _bloc(source: dict[str, Any], lignes: list[dict[str, Any]]) -> dict[str, Any]:
    urls = [source["fichier"]] + ([source["nomenclature"]] if source.get("nomenclature") else [])
    return {"source_urls": urls, "programmes": lignes}


def lire_cote(source: dict[str, Any], appel: Callable[[str], bytes], quoi: str) -> dict[str, Any]:
    """Un côté (voté ou consommé) d'un exercice de 2015 à 2022."""
    contenu = appel(source["fichier"])
    lire = source["lire"]
    if lire == "realise_xls":
        lignes = lire_realise_xls(contenu, lire_nomenclature_xls(appel(source["nomenclature"])))
    elif lire == "vote_2020":
        lignes = lire_vote_2020(decoder(contenu),
                                lire_nomenclature_2020(decoder(appel(source["nomenclature"]))))
    else:
        lignes = globals()["lire_" + lire](decoder(contenu))
    return _bloc(source, _verifier(lignes, quoi))


def lire_exercice(an: int, appel: Callable[[str], bytes]) -> dict[str, Any]:
    """Les deux côtés d'un exercice, chacun résolu ou déclaré absent.

    Un fichier injoignable ou illisible ne fait pas tomber l'autre côté : il
    devient un `*_non_resolu` que le run suivant retentera.
    """
    plan = LECTEURS[an]
    sortie: dict[str, Any] = {}
    if "etat" in plan:
        source = plan["etat"]
        try:
            ministeres = lire_nomenclature_json(decoder(appel(source["nomenclature"])))
            vote, realise = lire_etat_cp(decoder(appel(source["fichier"])), ministeres)
            sortie["vote"] = _bloc(source, _verifier(vote, f"voté {an}"))
            sortie["realise"] = _bloc(source, _verifier(realise, f"consommé {an}"))
        except (FinancesIndisponibles, OSError, ValueError, KeyError) as erreur:
            for cote in ("vote", "realise"):
                sortie[cote] = None
                sortie[cote + "_non_resolu"] = {"raison": f"lecture en échec : {erreur}",
                                                "a_retenter": True}
        return sortie
    for cote in ("vote", "realise"):
        source = plan[cote]
        if "raison" in source:
            sortie[cote] = None
            sortie[cote + "_non_resolu"] = {"raison": source["raison"], "a_retenter": False}
            continue
        try:
            sortie[cote] = lire_cote(source, appel, f"{cote} {an}")
        except (FinancesIndisponibles, OSError, ValueError, KeyError) as erreur:
            sortie[cote] = None
            sortie[cote + "_non_resolu"] = {"raison": f"lecture en échec : {erreur}",
                                            "a_retenter": True}
    return sortie


# ── Les grandes lignes ──────────────────────────────────────────────────────

def lire_series_mensuelles(textes: Iterable[str]) -> dict[tuple[str, str, str], dict[str, Any]]:
    """Les cumuls de fin de mois, par ligne. La clé d'un mois est `AAAA-MM`."""
    lignes: dict[tuple[str, str, str], dict[str, Any]] = {}
    for texte in textes:
        tableau = list(csv.reader(io.StringIO(texte), delimiter=";"))
        entete = tableau[0]
        for rang in tableau[1:]:
            if len(rang) < 6 or not rang[4].strip():
                continue
            cle = (rang[2].strip(), rang[3].strip(), rang[4].strip())
            bloc = lignes.setdefault(cle, {"niveau": rang[0].strip(), "mensuel": {}})
            for i in range(5, min(len(entete), len(rang))):
                jour = entete[i].strip()
                valeur = nombre(rang[i])
                if re.fullmatch(r"\d{2}/\d{2}/\d{4}", jour) and valeur is not None:
                    bloc["mensuel"][f"{jour[6:]}-{jour[3:5]}"] = valeur
    return lignes


def lire_textes(textes: Iterable[str]) -> dict[tuple[str, str, str], dict[str, dict[str, float]]]:
    """Les montants des lois de finances, par ligne, par texte, par exercice.

    Les trois textes de la source sont gardés tels quels : `LFI`,
    `Dernière LFR/LFG`, `Exécution` — celle-ci décalée d'un an de 2019 à 2021.
    """
    lignes: dict[tuple[str, str, str], dict[str, dict[str, float]]] = {}
    for texte in textes:
        tableau = list(csv.reader(io.StringIO(texte), delimiter=";"))
        entete = tableau[0]
        for rang in tableau[1:]:
            if len(rang) < 7 or not rang[4].strip():
                continue
            cle = (rang[2].strip(), rang[3].strip(), rang[4].strip())
            for i in range(6, min(len(entete), len(rang))):
                an, valeur = entete[i].strip(), nombre(rang[i])
                if an.isdigit() and valeur is not None:
                    lignes.setdefault(cle, {}).setdefault(rang[5].strip(), {})[an] = valeur
    return lignes


def lire_grandes_lignes(appel: Callable[[str], bytes]) -> dict[str, Any]:
    """Le jeu mensuel de la DGFiP, en une liste de lignes."""
    urls_m = [_piece(JEU_MENSUEL, p) for p in PIECES_MENSUELLES]
    urls_t = [_piece(JEU_MENSUEL, p) for p in PIECES_TEXTES]
    mensuel = lire_series_mensuelles(decoder(appel(u)) for u in urls_m)
    textes = lire_textes(decoder(appel(u)) for u in urls_t)
    if len(mensuel) < 20:
        raise FinancesIndisponibles(f"séries mensuelles : {len(mensuel)} lignes lues")
    lignes = [{"categorie": c, "sous_categorie": s, "ligne": l, "niveau": bloc["niveau"],
               "mensuel": dict(sorted(bloc["mensuel"].items())),
               "textes": {t: dict(sorted(v.items())) for t, v in sorted(textes.get((c, s, l), {}).items())}}
              for (c, s, l), bloc in mensuel.items()]
    return {"source_urls": urls_m + urls_t, "fiche": URL_FICHE.format(jeu=JEU_MENSUEL),
            "lignes": lignes}


# ── La collecte ─────────────────────────────────────────────────────────────

def charger(chemin: Path = CHEMIN_PAR_DEFAUT) -> dict[str, Any]:
    """Le document publié, ou `{}` — un fichier illisible ne fait pas échouer."""
    try:
        publie = json.loads(Path(chemin).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return publie if isinstance(publie, dict) else {}


def est_fige(bloc: Optional[dict[str, Any]], an: int, aujourd_hui: date) -> bool:
    """Un exercice dont rien ne peut plus bouger ne se relit pas.

    Figé : ses deux côtés sont résolus ou déclarés définitivement absents, et
    l'exercice est clos depuis plus d'un an — la loi de règlement de l'année N
    paraît au printemps N+1, et peut être republiée dans l'année.
    """
    if not bloc or an >= aujourd_hui.year - 1:
        return False
    for cote in ("vote", "realise"):
        if bloc.get(cote) is None and (bloc.get(cote + "_non_resolu") or {}).get("a_retenter", True):
            return False
    return True


def collecter(existant: dict[str, Any], appel: Callable[[str], bytes], *,
              exercices: Optional[Iterable[int]] = None, tout: bool = False,
              aujourd_hui: Optional[date] = None) -> dict[str, Any]:
    """Le document à écrire, composé de l'existant et de ce qui a été relu.

    Une lecture en échec **n'écrase jamais** un bloc déjà résolu : il reste en
    place, et l'échec est rendu dans `echecs` pour que l'appelant le signale.
    """
    aujourd_hui = aujourd_hui or date.today()
    anciens = dict(existant.get("exercices") or {})
    voulus = sorted(exercices) if exercices else sorted(LECTEURS)
    echecs: list[str] = []
    sortie_ex: dict[str, Any] = dict(anciens)
    for an in voulus:
        if an not in LECTEURS:
            echecs.append(f"{an} : aucun lecteur déclaré")
            continue
        ancien = anciens.get(str(an))
        if not tout and not exercices and est_fige(ancien, an, aujourd_hui):
            continue
        nouveau = lire_exercice(an, appel)
        for cote in ("vote", "realise"):
            rate = nouveau.get(cote) is None and (nouveau.get(cote + "_non_resolu") or {}).get("a_retenter")
            if rate:
                echecs.append(f"{an} {cote} : {nouveau[cote + '_non_resolu']['raison']}")
                if ancien and ancien.get(cote) is not None:
                    nouveau[cote] = ancien[cote]
                    nouveau.pop(cote + "_non_resolu", None)
        sortie_ex[str(an)] = nouveau
    try:
        grandes = lire_grandes_lignes(appel)
    except (FinancesIndisponibles, OSError, ValueError, KeyError, IndexError) as erreur:
        echecs.append(f"grandes lignes : {erreur}")
        grandes = existant.get("grandes_lignes")
    return {
        "schema_version": SCHEMA_VERSION,
        "genere_le": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "licence_donnees": LICENCE_FINANCES_ETAT,
        "borne_ministere": BORNE_MINISTERE,
        "grandes_lignes": grandes,
        "exercices": dict(sorted(sortie_ex.items())),
        "echecs": echecs,
    }


def _appel_reseau(url: str) -> bytes:
    """Un GET, borné en temps. Le portail ne demande ni clé ni en-tête."""
    import urllib.parse
    import urllib.request

    coupe = urllib.parse.urlsplit(url)
    propre = urllib.parse.urlunsplit(coupe._replace(path=urllib.parse.quote(coupe.path)))
    requete = urllib.request.Request(propre, headers={"User-Agent": "empreinte-politique"})
    with urllib.request.urlopen(requete, timeout=60) as reponse:
        return reponse.read()


def resume(document: dict[str, Any]) -> list[str]:
    """Ce que le document porte, une ligne par exercice — pour le journal du run."""
    lignes = []
    for an, bloc in (document.get("exercices") or {}).items():
        morceaux = []
        for cote, nom in (("vote", "voté"), ("realise", "consommé")):
            if bloc.get(cote):
                progs = bloc[cote]["programmes"]
                total = sum(p["cp"] for p in progs) / 1e9
                morceaux.append(f"{nom} {len(progs)} programmes, {total:.1f} Md€")
            else:
                morceaux.append(f"{nom} absent ({(bloc.get(cote + '_non_resolu') or {}).get('raison')})")
        lignes.append(f"{an} : " + " ; ".join(morceaux))
    grandes = document.get("grandes_lignes") or {}
    mois = sorted({m for l in grandes.get("lignes") or [] for m in l["mensuel"]})
    if mois:
        lignes.append(f"grandes lignes : {len(grandes['lignes'])} lignes, de {mois[0]} à {mois[-1]}")
    return lignes


def main(argv: Optional[list[str]] = None) -> int:
    analyseur = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    analyseur.add_argument("--sortie", type=Path, default=CHEMIN_PAR_DEFAUT)
    analyseur.add_argument("--tout", action="store_true",
                           help="relire aussi les exercices figés")
    analyseur.add_argument("--exercices", type=int, nargs="+",
                           help="ne relire que ces exercices")
    args = analyseur.parse_args(argv)

    from json_io import dumps_indente, ecrire_index_json

    document = collecter(charger(args.sortie), _appel_reseau,
                         exercices=args.exercices, tout=args.tout)
    echecs = document.pop("echecs")
    ecrit = ecrire_index_json(args.sortie, document, dumps_indente)
    for ligne in resume(document):
        print(ligne)
    print(f"{args.sortie} : {'écrit' if ecrit else 'inchangé'}")
    for echec in echecs:
        print(f"ÉCHEC — {echec}", file=sys.stderr)
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
