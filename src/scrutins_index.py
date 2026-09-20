#!/usr/bin/env python3
"""scrutins_index.py — Liste dédupliquée des scrutins, partagée (#432).

CE QUI GOUVERNE CE MODULE, si vous n'en lisez que trois choses :
  - `docs/decisions/qualification-scrutins-et-cle-dossier-639.md` — la
    qualification d'un scrutin et la clé de son dossier étaient lues puis
    jetées à la fusion ; `merge_scrutins_index` est écrit contre ça.
  - `docs/decisions/rattachement-scrutin-dossier-758.md` — un scrutin AN ne
    nomme PAS le texte qu'il tranche (0/18 311 scrutins bruts). Le lien
    n'existe qu'en sens inverse, et il vit désormais dans
    `pivot_data/scrutins_dossiers.json` — pas ici, et surtout pas dans
    `texte_lie_id`, réservé aux motions de censure.
  - `docs/decisions/audit-champs-deplaces-726.md` — un consommateur qui lit un
    champ déplacé ne se tait pas ; `cohesion_votes[].date` vit ici depuis #432.

Un scrutin est **identique pour tous ses votants** : `texte`, `date`, `sort`,
`type_vote`, `source_url`… Seule la `position` est propre au membre. Le titre
d'un scrutin était donc recopié jusqu'à 74 fois, et le méta complet autant.

Ce module porte la liste dédupliquée que profils et groupes référencent, et
rien d'autre. Mesuré sur les données committées au 19/08/2026 : 398 085 paires
(membre, vote) pour **17 422 scrutins distincts**.

POURQUOI UN FICHIER PARTAGÉ, ET PAS UNE LISTE PAR PROFIL. Les 4 104 scrutins
qu'agrègent les profils de groupe sont **intégralement inclus** dans les 17 422
des profils individuels : zéro scrutin propre aux groupes. Une seule liste sert
donc les deux, sans exception à gérer. Une liste par profil, elle, ne
dédupliquerait qu'à l'intérieur d'un profil — un scrutin voté par 74 membres
resterait stocké 74 fois.

C'est la seule dépendance entre fichiers de `pivot_data/`, et elle est assumée :
`pivot_data/profiles/<slug>.pivot.json` ne se lit plus seul pour ses votes. Les
consommateurs (UI, `group_profile`, audits) chargent l'index une fois.

CE QUI RESTE DANS LE PROFIL. Le mapping `{scrutin_id, position}` — c'est-à-dire
exactement ce qui a de la valeur analytique et que l'agrégat de groupe ne donne
pas : la position individuelle, dissidences comprises. Principe directeur de
l'épic #429 : normaliser, jamais supprimer.

L'IDENTIFIANT. `an:<legislature>:<numero_scrutin>` — convention
`<source>:<identifiant_source>` du dépôt (cf. `id` d'un profil pivot). La
législature en fait partie parce que le numéro repart à 1 à chaque législature
(AGENTS.md §5) ; un identifiant qui ne la porterait pas confondrait le scrutin
n° 1000 de la 16e et celui de la 17e. Elle est résolue par
`scrutins_legislature` (jointure sur jumeau étiqueté, puis calendrier, jamais de
défaut) avant toute construction d'identifiant.
"""

import json
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional

from json_io import ecrire_profil_json
from licences import LICENCE_AN
from scrutins_legislature import (
    LegislatureIrresoluble,
    PROVENANCE_COLLECTEE,
    CleScrutin,
    resoudre_legislatures,
)

SCHEMA_VERSION = "scrutins-v1"
SOURCE_AN = "an"

DEFAULT_SCRUTINS_PATH = Path("pivot_data") / "scrutins.json"

# Champs du scrutin, communs à tous ses votants. Le mapping du profil ne porte
# aucun d'eux : les y laisser, c'est le facteur 22,8 × que #432 supprime.
CHAMPS_SCRUTIN = (
    "date", "texte", "sort", "type_scrutin", "type_vote", "demandeur",
    "texte_lie_id", "source_url",
)

# Motif publié sur une motion de censure dont le texte lié n'est pas résoluble.
#
# POURQUOI UNE DÉCLARATION ET PAS UN CHAMP VIDE (#639). AGENTS.md §5 exige
# qu'un `type_vote == "motion_censure"` porte un `texte_lie_id` — invariant que
# rien ne satisfaisait tant que `type_vote` valait « vote_texte » pour tout le
# monde. Il devient exigible dès que les 66 motions de censure sont qualifiées,
# et il n'est PAS satisfiable : le scrutin AN ne porte aucune référence
# législative. Ni `objet.referenceLegislative` ni `demandeur.referenceLegislative`
# ne sont renseignés sur **0 / 18 311** scrutins bruts des législatures 14 à 17
# (relevé du 31/08/2026 sur les archives réelles, les quatre législatures).
#
# Une part des motions n'a d'ailleurs aucun texte à lier : une motion de
# l'article 49 alinéa 2 est spontanée, sans 49.3 en regard. Exiger la clé
# reviendrait à exiger un fait inexistant.
#
# On applique donc le patron `*_non_resolu` déjà écrit du dépôt (AGENTS.md §5,
# amendements sans uid AN) : clé `null`, enregistrement de déclaration à côté.
# Ce n'est pas un assouplissement de la règle 4 — la motion reste un fait
# procédural distinct, et aucune position n'est dérivée d'un type.
MOTIF_TEXTE_LIE_NON_SOURCE = (
    "le scrutin AN ne publie aucune référence législative : "
    "objet.referenceLegislative et demandeur.referenceLegislative sont nuls sur "
    "0/18311 scrutins bruts des législatures 14 à 17 (relevé du 31/08/2026). "
    "Le rattachement au dossier n'existe qu'en lien inverse, depuis "
    "actesLegislatifs[].voteRefs du dossier législatif — non collecté (#639, rang 4)."
)


def cle_scrutin(legislature: Any, numero_scrutin: Any) -> str:
    """`an:16:4084`. Les deux composantes sont obligatoires : un identifiant
    partiel se confondrait avec celui d'une autre législature."""
    return f"{SOURCE_AN}:{legislature}:{numero_scrutin}"


def decomposer_id(scrutin_id: str) -> tuple[Optional[str], Optional[str]]:
    """`"an:16:4084"` → `("16", "4084")`. `(None, None)` si la forme n'est pas
    reconnue — un identifiant mal formé ne doit pas se faire deviner."""
    if not isinstance(scrutin_id, str):
        return None, None
    morceaux = scrutin_id.split(":")
    if len(morceaux) != 3 or morceaux[0] != SOURCE_AN or not morceaux[1] or not morceaux[2]:
        return None, None
    return morceaux[1], morceaux[2]


class ScrutinsIndex:
    """Liste dédupliquée + résolution `(numero_scrutin, date)` → identifiant.

    Deux accès, parce que les deux appelants n'ont pas la même information :
    `identifiant_de_vote` sert à la normalisation, qui part d'un enregistrement
    brut ; `get` sert aux consommateurs, qui partent d'un identifiant.
    """

    def __init__(self, scrutins: Optional[dict[str, dict[str, Any]]] = None) -> None:
        self.par_id: dict[str, dict[str, Any]] = dict(scrutins or {})
        self._par_cle: dict[CleScrutin, str] = {}
        for scrutin_id, scrutin in self.par_id.items():
            self._par_cle[CleScrutin(scrutin.get("numero_scrutin"), scrutin.get("date"))] = scrutin_id

    def __len__(self) -> int:
        return len(self.par_id)

    def __contains__(self, scrutin_id: object) -> bool:
        return scrutin_id in self.par_id

    def get(self, scrutin_id: Optional[str]) -> Optional[dict[str, Any]]:
        """Scrutin d'un identifiant, `None` s'il est inconnu.

        `None` et pas une exception : un profil peut référencer un scrutin
        qu'un index partiel ne connaît pas encore (index reconstruit sur un
        sous-ensemble). Aux appelants d'en faire une donnée manquante — jamais
        une valeur inventée.
        """
        return self.par_id.get(scrutin_id) if scrutin_id else None

    def identifiant_de_vote(self, vote: dict[str, Any]) -> Optional[str]:
        """Identifiant du scrutin d'un vote brut, `None` s'il est introuvable.

        La résolution passe par `(numero_scrutin, date)` et non par
        `(legislature, numero_scrutin)` : c'est précisément parce que 22,5 % des
        votes n'ont pas de législature que l'index existe.
        """
        return self._par_cle.get(CleScrutin(_texte(vote.get("numero_scrutin")), vote.get("date")))

    def liste(self) -> list[dict[str, Any]]:
        """Scrutins triés par identifiant — ordre stable d'un run à l'autre,
        pour que git ne voie que les vraies différences."""
        return [self.par_id[k] for k in sorted(self.par_id)]


def _texte(valeur: Any) -> Optional[str]:
    return str(valeur) if valeur is not None else None


def construire_index(
    votes: Iterable[dict[str, Any]], *, strict: bool = True
) -> tuple[ScrutinsIndex, list[Any]]:
    """Construit l'index à partir d'un **flux** de votes bruts.

    Un flux, et une seule passe : charger les 209 profils bruts en mémoire pour
    les reparcourir deux fois coûtait 1,1 Go de JSON et se faisait tuer par
    l'OOM killer — le même mode d'échec que #377 et #392 sur l'index des
    amendements. Ici, seuls les 17 422 scrutins distincts sont retenus, jamais
    les 398 085 paires.

    La résolution de la législature reste globale au corpus : les étiquettes
    vues sur n'importe quelle occurrence d'un scrutin servent à toutes les
    autres (jointure sur jumeau étiqueté, `scrutins_legislature`). C'est
    précisément ce qu'une construction profil par profil ne pourrait pas faire.

    `strict=True` (défaut) lève `LegislatureIrresoluble` si un seul scrutin
    reste sans législature : un index amputé produirait des profils dont une
    partie des votes ne référence rien, sans que rien ne le signale.
    """
    champs_par_cle: dict[CleScrutin, dict[str, Any]] = {}
    etiquettes: dict[CleScrutin, set[str]] = {}
    etiquetes: set[CleScrutin] = set()

    for vote in votes:
        if not isinstance(vote, dict):
            continue
        cle = CleScrutin(_texte(vote.get("numero_scrutin")), vote.get("date"))
        legislature = vote.get("legislature")
        if legislature:
            etiquettes.setdefault(cle, set()).add(str(legislature))
            etiquetes.add(cle)
        champs = champs_par_cle.get(cle)
        if champs is None:
            champs_par_cle[cle] = {c: _valeur_scrutin(c, vote) for c in CHAMPS_SCRUTIN}
            continue
        # Occurrences suivantes : ne compléter que ce qui manque. Mesuré au
        # 19/08/2026, les 7 champs communs sont strictement identiques sur les
        # 398 085 paires — mais une collecte partielle peut laisser un champ à
        # null chez l'un et renseigné chez l'autre.
        for champ in CHAMPS_SCRUTIN:
            if champs.get(champ) is None:
                champs[champ] = _valeur_scrutin(champ, vote)

    occurrences = [
        (cle.numero_scrutin, cle.date, next(iter(etiquettes.get(cle, ())), None))
        for cle in champs_par_cle
    ]
    # Les clés portant PLUSIEURS étiquettes doivent rester ambiguës : ne pas en
    # choisir une arbitrairement en aplatissant le set ci-dessus.
    occurrences += [
        (cle.numero_scrutin, cle.date, legislature)
        for cle, valeurs in etiquettes.items()
        if len(valeurs) > 1
        for legislature in sorted(valeurs)
    ]

    resolutions, echecs = resoudre_legislatures(occurrences)
    if echecs and strict:
        raise LegislatureIrresoluble(echecs)

    scrutins: dict[str, dict[str, Any]] = {}
    for cle, champs in champs_par_cle.items():
        resolution = resolutions.get(cle)
        if resolution is None:
            continue
        scrutin_id = cle_scrutin(resolution.legislature, cle.numero_scrutin)
        scrutins[scrutin_id] = {
            "id": scrutin_id,
            "legislature": resolution.legislature,
            # Provenance de la LÉGISLATURE, pas du scrutin. Stockée une fois
            # ici, jamais recopiée sur chacune des paires (membre, vote).
            #
            # Au niveau du scrutin il n'y a que deux cas : soit au moins une de
            # ses occurrences portait l'étiquette — c'est une donnée collectée,
            # et c'est elle qui sert de jumeau aux autres — soit aucune, et la
            # législature vient du calendrier. « Résolue par jumeau » qualifie
            # une OCCURRENCE, pas le scrutin (voir provenance_par_occurrence).
            "legislature_provenance": (
                PROVENANCE_COLLECTEE if cle in etiquetes else resolution.provenance
            ),
            "numero_scrutin": cle.numero_scrutin,
            **champs,
        }
        _declarer_texte_lie_non_resolu(scrutins[scrutin_id])

    return ScrutinsIndex(scrutins), echecs


def _declarer_texte_lie_non_resolu(scrutin: dict[str, Any]) -> None:
    """Pose (ou retire) la déclaration d'absence de texte lié sur un scrutin.

    Retirée dès que `texte_lie_id` est renseigné : garder une déclaration
    « non résolu » à côté d'une clé résolue serait un fait faux, et c'est
    exactement ce que le rang 4 de #639 viendra corriger scrutin par scrutin.
    """
    if scrutin.get("type_vote") != "motion_censure" or scrutin.get("texte_lie_id"):
        scrutin.pop("texte_lie_non_resolu", None)
        return
    scrutin["texte_lie_non_resolu"] = {"motif": MOTIF_TEXTE_LIE_NON_SOURCE}


def _valeur_scrutin(champ: str, vote: dict[str, Any]) -> Any:
    """Lit un champ de scrutin indifféremment sur un vote brut ou pivot.

    Le schéma brut nomme `titre`/`url_source` ce que le pivot nomme
    `texte`/`source_url`. Accepter les deux permet de reconstruire l'index
    depuis `raw_data/profiles` comme depuis un `pivot_data/profiles` d'avant
    #432 — indispensable pour comparer avant/après sur les mêmes données.
    """
    if champ == "texte":
        return vote.get("texte") or vote.get("titre") or None
    if champ == "source_url":
        return vote.get("source_url") or vote.get("url_source") or None
    # `type_vote` N'A PLUS DE DÉFAUT (#639, réouverture du 31/08/2026). Le repli
    # « vote_texte » était antérieur à la qualification sourcée, et il est
    # devenu le second maillon qui la perdait : `construire_index` ne complète
    # une occurrence suivante que sur un champ resté `None`, donc la première
    # occurrence non qualifiée d'un scrutin verrouillait « vote_texte » et
    # aucune occurrence qualifiée ne pouvait plus le corriger. Une motion de
    # censure votée par un profil régénéré ET par un profil qui ne l'est pas
    # serait restée publiée sous le type d'un vote sur texte, c'est-à-dire un
    # fait faux (§2 règle 4). Un scrutin que personne ne qualifie sort donc
    # `null`, et `merge_scrutins_index` conserve la valeur déjà publiée plutôt
    # que de régresser.
    return vote.get(champ)


def merge_scrutins_index(ancien: ScrutinsIndex, nouveau: ScrutinsIndex) -> ScrutinsIndex:
    """Fusion additive de deux index : jamais une suppression.

    Un run qui ne régénère qu'une tranche de profils ne voit qu'une partie des
    scrutins. Écraser l'index par ce qu'il vient de voir effacerait les scrutins
    des profils non retraités, et les mappings qui les référencent pointeraient
    dans le vide — la panne exacte que #450 vient de traiter à l'échelle des
    profils.

    Sur les champs, la nouvelle valeur gagne si elle est renseignée (même règle
    que `merge_dossier_records` pour les amendements : permet une correction),
    sinon l'ancienne est conservée (jamais de régression vers `null`).
    """
    fusionnes: dict[str, dict[str, Any]] = {k: dict(v) for k, v in ancien.par_id.items()}
    for scrutin_id, scrutin in nouveau.par_id.items():
        existant = fusionnes.get(scrutin_id)
        if existant is None:
            fusionnes[scrutin_id] = dict(scrutin)
            continue
        for champ, valeur in scrutin.items():
            if valeur is not None:
                existant[champ] = valeur
    # Champ dérivé, jamais fusionné : un scrutin requalifié `motion_censure`
    # par un run récent doit gagner sa déclaration, et un scrutin dont le rang 4
    # aura résolu le texte lié doit la perdre. Même règle que `chambres` ou
    # `licence_donnees` côté profil (AGENTS.md §4).
    for scrutin in fusionnes.values():
        _declarer_texte_lie_non_resolu(scrutin)
    return ScrutinsIndex(fusionnes)


def charger(chemin: Path) -> ScrutinsIndex:
    """Charge l'index depuis son fichier. Index vide si le fichier est absent —
    un premier run n'a rien à charger."""
    if not Path(chemin).exists():
        return ScrutinsIndex()
    with open(chemin, encoding="utf-8") as f:
        donnees = json.load(f)
    scrutins = {}
    for scrutin in (donnees.get("scrutins") or []):
        if isinstance(scrutin, dict) and scrutin.get("id"):
            scrutins[scrutin["id"]] = scrutin
    return ScrutinsIndex(scrutins)


def ecrire(chemin: Path, index: ScrutinsIndex, *, genere_le: Optional[str] = None) -> None:
    """Écrit l'index en JSON compact (#433) : 17 422 scrutins, ~8,7 Mo."""
    chemin = Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    ecrire_profil_json(chemin, {
        "schema_version": SCHEMA_VERSION,
        "genere_le": genere_le,
        "licence_donnees": LICENCE_AN,
        "scrutins": index.liste(),
    })


def iter_votes_du_repertoire(profils_dir: Path) -> Iterator[dict[str, Any]]:
    """Itère les votes de tous les profils d'un répertoire, **un profil à la
    fois**.

    Le profil est relâché avant d'ouvrir le suivant : accumuler les 209 profils
    bruts (1,1 Go de JSON) faisait tuer le process par l'OOM killer, comme sur
    l'index des amendements en #377 et #392.

    Un fichier illisible est signalé et sauté — il ne doit pas priver l'index
    des scrutins de tous les autres.

    Depuis la partition des profils bruts par législature (#580), `votes` reste
    dans le **socle** `<slug>.json` : cette boucle est donc inchangée, et elle y
    gagne — le socle pèse 1,85 Mo là où le profil monolithique en pesait 56.
    Seuls `amendements` sont partitionnés ; les lire demande `profil_brut`.
    """
    if not Path(profils_dir).is_dir():
        return
    for chemin in sorted(Path(profils_dir).glob("*.json")):
        if chemin.name.startswith("."):
            continue
        try:
            with open(chemin, encoding="utf-8") as f:
                profil = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            print(f"  [!] Lecture impossible de {chemin}, ignoré : {exc}")
            continue
        for vote in (profil.get("votes") or []):
            if isinstance(vote, dict):
                yield vote
        del profil


def rafraichir(
    profils_dir: Path,
    chemin_index: Path = DEFAULT_SCRUTINS_PATH,
    *,
    strict: bool = True,
    fusionner: bool = True,
    genere_le: Optional[str] = None,
) -> tuple[ScrutinsIndex, list[Any]]:
    """Reconstruit l'index depuis `profils_dir` et l'écrit, en fusionnant avec
    l'existant par défaut.

    `fusionner=True` est le défaut **et le mode sûr** : un run qui ne régénère
    qu'une tranche de profils ne voit qu'une partie des scrutins, et écraser
    l'index par ce qu'il vient de voir laisserait les mappings des profils non
    retraités pointer dans le vide. C'est la version « index » de la leçon de
    #450 — ne jamais publier comme total ce qu'un job n'a vu que partiellement.

    `fusionner=False` correspond à `--no-merge` : reconstruction complète, à
    n'utiliser que sur un corpus complet.
    """
    index, echecs = construire_index(iter_votes_du_repertoire(profils_dir), strict=strict)
    if fusionner:
        index = merge_scrutins_index(charger(chemin_index), index)
    ecrire(chemin_index, index, genere_le=genere_le)
    return index, echecs
