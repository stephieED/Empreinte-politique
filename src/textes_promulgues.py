#!/usr/bin/env python3
"""textes_promulgues.py — Construit `pivot_data/textes_promulgues.json`.

CE QUE LE FICHIER PORTE. Une entrée par dossier législatif **promulgué**, lue
dans les archives de dossiers de l'Assemblée : la date de promulgation, le
numéro de la loi, son intitulé, la nature de la procédure (projet ou
proposition), la commission saisie au fond et la chambre de première lecture.
607 dossiers sur les 10 967 des archives XIV à XVII (mesuré le 23/09/2026).

POURQUOI CETTE POPULATION, ET PAS UNE AUTRE. Remonté par l'interface le
23/09/2026 : mettre en regard, sur une fiche de gouvernement, les textes
promulgués et les actes parus au Journal officiel. Les deux populations
lisibles jusqu'ici ne le permettaient pas —

- les `textes[]` d'une fiche de gouvernement sont ceux qu'un de ses membres a
  **initiés** : 1 seul promulgué sur la fenêtre de LECORNU_II ;
- l'union des `textes_portes` des profils collectés est **ce que nos rosters
  portent**, pas ce que le Parlement a promulgué : 13 dossiers sur la même
  fenêtre, et l'écart avec la réalité n'est pas mesurable de l'intérieur.

Une loi promulguée n'appartient à personne : elle est un fait du Parlement. Ce
fichier la publie donc pour elle-même, et le rattachement à un gouvernement se
fait par la **date de promulgation** contre la période de la fiche — jamais par
l'initiative, qui attribuerait au gouvernement le travail du Parlement.

CE QU'IL NE PORTE PAS. Aucun lien vers les décrets d'application : la source ne
qualifie plus ce lien depuis 2024 (0 des 188 lois du fonds promulguées depuis le
01/01/2024, voir `docs/sources/jorf-dila.md`), et une colonne à moitié vide se
lirait comme un manquement de l'exécutif.

LA CHAMBRE DE PREMIÈRE LECTURE EST DÉRIVÉE DES DATES DE DÉPÔT, et c'est à
déclarer : **tout** dossier promulgué porte un `AN1-DEPOT` et un `SN1-DEPOT`
(607 sur 607), le second étant la transmission quand le texte vient de
l'Assemblée. C'est donc le dépôt le **plus ancien** qui dit l'origine, et deux
dates égales ou absentes rendent `null` plutôt qu'un choix arbitraire
(§2 règle 5). Mesuré sur les 607 : 242 dossiers de première lecture au Sénat.

LA DERNIÈRE ADOPTION PAR L'ASSEMBLÉE (#1320). Une loi se rattache à la
législature où l'Assemblée l'a adoptée — ni l'ouverture du dossier ni la
promulgation ne la disent. Chaque entrée publie donc `derniere_adoption_an` :
le dernier acte de décision de l'Assemblée (`AN1-DEBATS-DEC`, `AN2-…`,
`ANNLEC-…`, `ANLDEF-…`, `CMP-DEBATS-AN-DEC`) dont `statutConclusion.fam_code`
est une adoption, avec sa date, son uid et son `mode` (`KNOWN_MODES_ADOPTION_AN`).
Le mode se lit sur l'acte lui-même, jamais ailleurs :

- `considere_adopte_49_3` — `fam_code` TSORTF06, « considéré comme adopté […]
  article 49, alinéa 3 ». Un fait de procédure, **jamais un vote** (§2 règle 4) :
  aucune référence de scrutin n'est publiée, même si la source en posait une ;
- `scrutin_public` — l'acte porte `voteRefs` : les scrutins, en clé du corpus
  (`an:<législature>:<numéro>`, celle de `pivot_data/scrutins.json`) ;
- `sans_scrutin_public` — ni l'un ni l'autre. **Jamais « à main levée »** : le
  dossier ne distingue pas la main levée, l'assis et levé et la procédure
  d'examen simplifiée, et aucun de ses champs ne les nomme.

À côté, `senat_statue_apres` : le Sénat a-t-il rendu une décision datée
**strictement après** cette adoption, et `date_derniere_decision_senat`. Les
dates de la source sont au jour (`T00:00:00`) : une décision du Sénat le même
jour ne dit pas qui a statué en dernier, et l'indicateur reste alors `null`
(`decisions_le_meme_jour`) — sauf en lecture définitive, que la Constitution
place après la nouvelle lecture du Sénat (art. 45, al. 4). Même règle que la
chambre de première lecture : deux dates égales ne départagent rien.

Une absence est `null` avec son `*_non_resolu` et un motif fermé (§2 règle 5) :
`KNOWN_MOTIFS_ADOPTION_AN_NON_RESOLUE`, `KNOWN_MOTIFS_SENAT_APRES_NON_RESOLU`.

ADDITIF, JAMAIS DESTRUCTEUR. Même règle que `build_commissions_dossiers.py` : un
run sans archives lisibles rend une table vide, et le fichier publié est
conservé (AGENTS.md §3a). `--no-merge` force la reconstruction complète.

Usage :
    python3 src/textes_promulgues.py
    python3 src/textes_promulgues.py --out pivot_data/textes_promulgues.json
    python3 src/textes_promulgues.py --no-merge
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Iterator, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from gouvernement_textes import (  # noqa: E402
    _source_url, ensure_dossiers_zips_downloaded, iter_dossiers_bruts,
)
from json_io import dumps_indente, ecrire_index_json  # noqa: E402
import lois_jorf  # noqa: E402
from licences import LICENCE_AN  # noqa: E402
from scrutins_dossiers_an import cle_depuis_uid  # noqa: E402

SCHEMA_VERSION = "textes-promulgues-v1"

DEFAUT_SORTIE = Path("pivot_data") / "textes_promulgues.json"
DEFAUT_COMMISSIONS = Path("pivot_data") / "commissions_dossiers.json"

#: L'acte qui fait qu'une loi est promulguée, tel que la source le code.
CODE_PROMULGATION = "PROM-PUB"

#: Les deux dépôts de première lecture, et la chambre qu'ils désignent. Les
#: valeurs sont celles de `schema_pivot.KNOWN_CHAMBRES`.
CHAMBRE_PAR_DEPOT = {"AN1-DEPOT": "assemblee_nationale", "SN1-DEPOT": "senat"}

# ── La dernière adoption par l'Assemblée (#1320) ──────────────────────────────

#: Comment l'Assemblée a adopté le texte la dernière fois, lu sur l'acte de
#: décision. Fermé, comme les `KNOWN_*` du schéma pivot (`AGENTS.md` §4) : une
#: valeur s'y ajoute délibérément, jamais par effet de bord.
MODE_SCRUTIN_PUBLIC = "scrutin_public"
MODE_SANS_SCRUTIN_PUBLIC = "sans_scrutin_public"
MODE_49_3 = "considere_adopte_49_3"
KNOWN_MODES_ADOPTION_AN: frozenset[str] = frozenset({
    MODE_SCRUTIN_PUBLIC, MODE_SANS_SCRUTIN_PUBLIC, MODE_49_3,
})

#: Pourquoi `derniere_adoption_an` est `null`. `sans_adoption_an` : aucun acte
#: de décision de l'Assemblée au statut d'adoption. `fam_code_inconnu` : une
#: décision de l'Assemblée postérieure à la dernière adoption reconnue porte un
#: statut que la table ne connaît pas — l'adoption retenue ne serait peut-être
#: pas la dernière. `decision_non_datee` : une décision de l'Assemblée n'a pas
#: de date, l'ordre n'est donc pas établi.
#: `lecture_cmp_an_absente` : une CMP a conclu à un **accord** après la
#: dernière adoption trouvée, et avant la promulgation, sans que le dossier
#: porte la lecture de ses conclusions par l'Assemblée. Un texte de CMP ne
#: devient loi qu'adopté par les deux chambres (art. 45, al. 3) : l'adoption
#: retenue n'est donc pas la dernière, et la publier rattacherait la loi à la
#: mauvaise législature. Mesuré le 21/10/2026 : 4 lois sur 1 017, dont 3
#: dossiers ouverts en XVIe et conclus en XVIIe.
KNOWN_MOTIFS_ADOPTION_AN_NON_RESOLUE: frozenset[str] = frozenset({
    "sans_adoption_an", "fam_code_inconnu", "decision_non_datee",
    "lecture_cmp_an_absente",
})

#: L'acte d'une commission mixte paritaire et son statut d'accord.
CODE_DECISION_CMP = "CMP-DEC"
FAM_CODE_ACCORD_CMP = "TCCMP01"

#: Pourquoi `senat_statue_apres` est `null`. `adoption_an_non_resolue` : rien à
#: quoi comparer. `sans_decision_senat` : le dossier ne porte aucune décision du
#: Sénat datée (`date_derniere_decision_senat` est alors `null` aussi) — un
#: Sénat qui écarte le texte par une motion ne laisse qu'un vote de motion, pas
#: une décision, et ce n'est pas à nous de la reconstruire.
#: `decisions_le_meme_jour` : le Sénat a statué le jour de la dernière adoption
#: de l'Assemblée, et la source date au jour.
#: Pourquoi `derniere_adoption_an.mode` est `null` alors que l'adoption est
#: datée. `scrutin_non_reconnu` : l'acte porte un `voteRefs` qui n'est pas un
#: scrutin de l'Assemblée (mesuré : `VTSNR5L17V844`, un scrutin du Sénat, sur
#: la lecture des conclusions de CMP de DLR5L16N49726). Ni « scrutin public »,
#: puisque la référence ne désigne aucun scrutin publié, ni « sans scrutin
#: public », puisque la source en cite un : la référence est recopiée telle quelle.
KNOWN_MOTIFS_MODE_NON_RESOLU: frozenset[str] = frozenset({"scrutin_non_reconnu"})

KNOWN_MOTIFS_SENAT_APRES_NON_RESOLU: frozenset[str] = frozenset({
    "adoption_an_non_resolue", "sans_decision_senat", "decisions_le_meme_jour",
})

#: Les `statutConclusion.fam_code` d'une décision de séance qui adoptent le
#: texte, au sens de `gouvernement_textes._FAM_CODE_STATUT_MAP` : « adopté »,
#: « avec modifications », « sans modification », « définitivement », « modifié »
#: (l'Assemblée adopte le texte du Sénat en le modifiant), 49.3, termes
#: identiques, conclusions de CMP. « Considéré comme REJETÉ » (TSORTF24) n'y est
#: pas : c'est une motion de censure adoptée.
FAM_CODES_ADOPTION: frozenset[str] = frozenset({
    "TSORTF01", "TSORTF02", "TSORTF03", "TSORTF04", "TSORTF05", "TSORTF06",
    "TSORTF14", "TSORTF18",
})
FAM_CODE_49_3 = "TSORTF06"
#: Ceux qui disent le contraire d'une adoption — rejet, rejet définitif,
#: considéré comme rejeté. Tout autre `fam_code`, y compris la sentinelle
#: `TSORTFnull` et un statut absent, est inconnu : une décision sans statut
#: pourrait être une adoption, et la taire ferait retenir la précédente.
FAM_CODES_NON_ADOPTION: frozenset[str] = frozenset({"TSORTF07", "TSORTF13", "TSORTF24"})

#: Les décisions de séance d'une chambre : un code `…-DEC` qui commence par sa
#: chambre, ou la lecture des conclusions de CMP qui la nomme. `CMP-DEC` (accord
#: ou désaccord de la commission mixte) n'est pas une décision de séance ;
#: `CMP-DEBATS-DEC` ne nomme pas de chambre et `CG22-…` est le Congrès : aucun
#: n'est rangé d'un côté.
PREFIXE_LECTURE_DEFINITIVE = "ANLDEF-"


def chambre_de_decision(code_acte: Any) -> Optional[str]:
    """`"AN"`, `"SN"` ou `None` : la chambre d'un acte de décision de séance."""
    if not isinstance(code_acte, str) or not code_acte.endswith("-DEC"):
        return None
    if code_acte == "CMP-DEBATS-AN-DEC" or (code_acte.startswith("AN")):
        return "AN"
    if code_acte == "CMP-DEBATS-SN-DEC" or code_acte.startswith("SN"):
        return "SN"
    return None


def _vote_refs(acte: dict[str, Any]) -> list[str]:
    """Les uid de scrutin d'un acte : `voteRefs` est `null`, `{"voteRef": uid}`
    ou `{"voteRef": [uid, …]}` (neuf décisions de première lecture de lois de
    finances en portent deux : la première partie et l'ensemble)."""
    refs = acte.get("voteRefs")
    if isinstance(refs, dict):
        refs = refs.get("voteRef")
    if isinstance(refs, str):
        return [refs]
    if isinstance(refs, list):
        return [r for r in refs if isinstance(r, str) and r]
    return []


def _fam_code(acte: dict[str, Any]) -> Optional[str]:
    statut = acte.get("statutConclusion")
    return statut.get("fam_code") if isinstance(statut, dict) else None


def derniere_adoption_an(dossier: dict[str, Any]) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    """`(adoption, None)` ou `(None, motif)` — la dernière adoption de l'Assemblée.

    « Dernière » se lit sur la date, et à date égale sur l'ordre du dossier, qui
    est chronologique (aucun cas mesuré sur les quatre archives).
    """
    decisions = [
        (rang, acte) for rang, acte in enumerate(iter_actes(dossier.get("actesLegislatifs")))
        if chambre_de_decision(acte.get("codeActe")) == "AN"
    ]
    if any(not _jour(acte.get("dateActe")) for _rang, acte in decisions):
        return None, "decision_non_datee"
    adoptions = [(_jour(a.get("dateActe")), rang, a) for rang, a in decisions
                 if _fam_code(a) in FAM_CODES_ADOPTION]
    if not adoptions:
        return None, "sans_adoption_an"
    jour, _rang, acte = max(adoptions, key=lambda x: (x[0], x[1]))
    if any(_fam_code(a) not in FAM_CODES_ADOPTION | FAM_CODES_NON_ADOPTION
           and _jour(a.get("dateActe")) >= jour for _r, a in decisions):
        return None, "fam_code_inconnu"
    prom = promulgation(dossier)
    borne = _jour(((prom or {}).get("infoJO") or {}).get("dateJO")) or _jour((prom or {}).get("dateActe"))
    for cmp in iter_actes(dossier.get("actesLegislatifs")):
        jour_cmp = _jour(cmp.get("dateActe"))
        if (cmp.get("codeActe") == CODE_DECISION_CMP and _fam_code(cmp) == FAM_CODE_ACCORD_CMP
                and jour_cmp and jour_cmp > jour and (borne is None or jour_cmp <= borne)):
            # Borné par la promulgation : un accord daté après elle (1 cas
            # mesuré, DLR5L15N37357) ne concerne pas cette loi.
            return None, "lecture_cmp_an_absente"

    statut = acte.get("statutConclusion") or {}
    mode_non_resolu = None
    if statut.get("fam_code") == FAM_CODE_49_3:
        # §2 règle 4 : un fait de procédure. Aucune référence de scrutin, même
        # si la source en posait une — la motion de censure est un autre objet.
        mode, scrutins = MODE_49_3, None
    else:
        refs = _vote_refs(acte)
        cles = [cle_depuis_uid(r) for r in refs]
        if refs and not all(cles):
            mode, scrutins = None, None
            mode_non_resolu = {"motif": "scrutin_non_reconnu", "vote_refs": refs}
        elif cles:
            mode, scrutins = MODE_SCRUTIN_PUBLIC, cles
        else:
            mode, scrutins = MODE_SANS_SCRUTIN_PUBLIC, None
    return {
        "date": jour,
        "mode": mode,
        "mode_non_resolu": mode_non_resolu,
        "scrutin_ids": scrutins,
        "acte_uid": acte.get("uid"),
        "code_acte": acte.get("codeActe"),
        "libelle_statut": statut.get("libelle"),
    }, None


def senat_apres(dossier: dict[str, Any], adoption: Optional[dict[str, Any]]
                ) -> tuple[Optional[bool], Optional[str], Optional[str]]:
    """`(senat_statue_apres, date_derniere_decision_senat, motif)`.

    Toute décision de séance du Sénat compte, rejet compris : la question est
    « qui a statué en dernier », pas « qui a adopté ».
    """
    jours = sorted(
        j for j in (
            _jour(a.get("dateActe")) for a in iter_actes(dossier.get("actesLegislatifs"))
            if chambre_de_decision(a.get("codeActe")) == "SN"
        ) if j
    )
    derniere = jours[-1] if jours else None
    if adoption is None:
        return None, derniere, "adoption_an_non_resolue"
    if derniere is None:
        return None, None, "sans_decision_senat"
    if derniere > adoption["date"]:
        return True, derniere, None
    if derniere == adoption["date"] and not str(adoption.get("code_acte") or "").startswith(
            PREFIXE_LECTURE_DEFINITIVE):
        return None, derniere, "decisions_le_meme_jour"
    return False, derniere, None


def iter_actes(noeud: Any) -> Iterator[dict[str, Any]]:
    """Tous les actes législatifs d'un dossier, à tous les étages.

    Les actes s'imbriquent (`actesLegislatifs.acteLegislatif.actesLegislatifs`…)
    et la source alterne entre un objet et une liste au même endroit : le
    parcours ne suppose ni l'un ni l'autre.
    """
    if isinstance(noeud, dict):
        if noeud.get("codeActe"):
            yield noeud
        for valeur in noeud.values():
            yield from iter_actes(valeur)
    elif isinstance(noeud, list):
        for element in noeud:
            yield from iter_actes(element)


def _jour(valeur: Any) -> Optional[str]:
    """`AAAA-MM-JJ` d'une date de la source, qui l'écrit avec son fuseau."""
    if not isinstance(valeur, str) or len(valeur) < 10:
        return None
    return valeur[:10]


def promulgation(dossier: dict[str, Any]) -> Optional[dict[str, Any]]:
    """L'acte de promulgation d'un dossier, ou `None` s'il n'en porte pas."""
    for acte in iter_actes(dossier.get("actesLegislatifs")):
        if acte.get("codeActe") == CODE_PROMULGATION:
            return acte
    return None


def chambre_premiere_lecture(dossier: dict[str, Any]) -> Optional[str]:
    """La chambre du dépôt le plus ancien, ou `None` si rien ne la départage."""
    dates: dict[str, str] = {}
    for acte in iter_actes(dossier.get("actesLegislatifs")):
        chambre = CHAMBRE_PAR_DEPOT.get(acte.get("codeActe") or "")
        jour = _jour(acte.get("dateActe"))
        if chambre and jour:
            dates.setdefault(chambre, jour)
    if len(dates) < 2:
        # Un seul dépôt daté : il dit la chambre. Aucun : rien à dire.
        return next(iter(dates), None)
    (premiere, jour_premier), (_, jour_second) = sorted(dates.items(), key=lambda x: x[1])
    return premiere if jour_premier < jour_second else None


def entree(dossier: dict[str, Any], commission: Optional[dict[str, Any]],
           lois: Optional[dict[str, list[list[str]]]] = None) -> Optional[dict[str, Any]]:
    """L'enregistrement publié d'un dossier promulgué, ou `None`.

    `commission` vient de `pivot_data/commissions_dossiers.json`, construit juste
    avant : son absence est publiée `null`, jamais rattrapée depuis l'intitulé —
    c'est la matière de la ligne, et une matière devinée est une matière fausse
    (§2 règle 8).
    """
    acte = promulgation(dossier)
    if acte is None:
        return None
    info_jo = acte.get("infoJO") or {}
    jorftext = lois_jorf.resoudre(lois or {}, acte.get("codeLoi"))
    titre_dossier = dossier.get("titreDossier") or {}
    procedure = dossier.get("procedureParlementaire") or {}
    adoption, motif_adoption = derniere_adoption_an(dossier)
    apres, date_senat, motif_senat = senat_apres(dossier, adoption)
    return {
        "date_promulgation": _jour(info_jo.get("dateJO")) or _jour(acte.get("dateActe")),
        "numero_loi": acte.get("codeLoi"),
        "nor": info_jo.get("referenceNOR"),
        "titre": titre_dossier.get("titre"),
        "nature_procedure": procedure.get("libelle") or procedure.get("code"),
        "commission": commission,
        "chambre_premiere_lecture": chambre_premiere_lecture(dossier),
        # L'identifiant de la loi au Journal officiel, par où se joignent les
        # `liens_lois` des actes réglementaires (`lois_jorf`). Les archives de
        # l'Assemblée ne le publient pas ; le NOR ne suffirait pas, absent sur
        # 412 des 1 015 textes. `null` quand la table ne le résout pas, et une
        # liste quand la source a publié la loi deux fois (rectificatif).
        "jorftext": (jorftext[0] if jorftext else None),
        "jorftext_autres": (jorftext[1:] or None),
        # Le dossier sur le site de l'Assemblée : la page où se relisent la
        # promulgation, les décisions de chaque lecture et leurs scrutins.
        "source_url": _source_url(dossier.get("legislature"), titre_dossier.get("titreChemin")),
        # #1320 — voir le docstring du module. Exactement un des deux est non nul.
        "derniere_adoption_an": adoption,
        "derniere_adoption_an_non_resolue": {"motif": motif_adoption} if motif_adoption else None,
        "senat_statue_apres": apres,
        "senat_statue_apres_non_resolu": {"motif": motif_senat} if motif_senat else None,
        "date_derniere_decision_senat": date_senat,
    }


def construire_table(
    archives: list[tuple[int, Path]],
    commissions: dict[str, dict[str, Any]],
    lois: Optional[dict[str, list[list[str]]]] = None,
) -> dict[str, dict[str, Any]]:
    """`{uid de dossier: entrée}` pour les seuls dossiers promulgués."""
    table: dict[str, dict[str, Any]] = {}
    for _legislature, dossier in iter_dossiers_bruts(archives):
        uid = dossier.get("uid")
        if not isinstance(uid, str) or not uid:
            continue
        ligne = entree(dossier, commissions.get(uid), lois)
        if ligne is not None:
            table[uid] = ligne
    return table


def charger_commissions(chemin: Path) -> dict[str, dict[str, Any]]:
    """La table `dossier → commission au fond` déjà publiée, ou `{}`."""
    try:
        publie = json.loads(Path(chemin).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    commissions = publie.get("commissions") if isinstance(publie, dict) else None
    return commissions if isinstance(commissions, dict) else {}


def _lire_existant(chemin: Path) -> dict[str, dict[str, Any]]:
    """Table déjà publiée, ou `{}` — un fichier illisible ne fait pas échouer."""
    try:
        publie = json.loads(Path(chemin).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    textes = publie.get("textes") if isinstance(publie, dict) else None
    return textes if isinstance(textes, dict) else {}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--out", default=str(DEFAUT_SORTIE),
                        help=f"Fichier à écrire (défaut : {DEFAUT_SORTIE}).")
    parser.add_argument("--commissions", default=str(DEFAUT_COMMISSIONS),
                        help="Table des commissions saisies au fond, pour la matière "
                             f"de chaque ligne (défaut : {DEFAUT_COMMISSIONS}).")
    parser.add_argument("--table-lois", default=str(lois_jorf.CHEMIN_PAR_DEFAUT),
                        help="Table `numéro de loi → identifiant JORFTEXT` (défaut : "
                             f"{lois_jorf.CHEMIN_PAR_DEFAUT}), tenue à jour par "
                             "`actes_reglementaires.py`.")
    parser.add_argument("--no-merge", action="store_true",
                        help="Reconstruction complète au lieu d'une fusion additive. "
                             "À réserver à un run qui a lu toutes les archives : sur un "
                             "run partiel, les dossiers non revus disparaîtraient.")
    args = parser.parse_args(argv)

    chemin = Path(args.out)
    commissions = charger_commissions(Path(args.commissions))
    if not commissions:
        print(f"  [!] {args.commissions} illisible ou absent : aucune matière sur les "
              "lignes de ce run (la commission reste `null`, jamais devinée).")
    try:
        archives = ensure_dossiers_zips_downloaded()
    except Exception as exc:  # noqa: BLE001 — une source absente est nommée, pas fatale
        print(f"  [!] Archives de dossiers indisponibles ({exc}) : aucun texte promulgué "
              "collecté à ce run.")
        archives = []

    lois = lois_jorf.charger(Path(args.table_lois))
    if not lois:
        print(f"  [!] {args.table_lois} illisible ou absente : aucun identifiant JORFTEXT "
              "sur les textes de ce run (`jorftext` reste `null`).")
    collectee = construire_table(archives, commissions, lois) if archives else {}
    if not collectee:
        print("  [!] Aucun texte promulgué collecté à ce run.")

    table = dict({} if args.no_merge else _lire_existant(chemin))
    table.update(collectee)
    if not table:
        print("  [!] Table vide et rien de publié : aucun fichier écrit.")
        return 0

    ecrire_index_json(
        chemin,
        {
            "schema_version": SCHEMA_VERSION,
            "genere_le": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "licence_donnees": LICENCE_AN,
            "textes": table,
        },
        dumps_indente,
    )
    sans_commission = sum(1 for v in table.values() if not v.get("commission"))
    conservees = len(table) - len(collectee)
    print(f"  ✓ {len(table)} texte(s) promulgué(s) → {chemin}")
    print(f"      sans commission au fond : {sans_commission} (absence déclarée)")
    if conservees > 0:
        print(f"      dont {conservees} conservé(s) d'un run précédent (non revus par celui-ci)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
