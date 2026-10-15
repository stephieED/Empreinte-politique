"""rattachement_deduit.py — Le dossier d'un vote que l'Assemblée ne rattache pas (#1289).

CE QUE CE MODULE FAIT, ET POURQUOI IL EST À PART. `scrutins_dossiers_an` lit le
lien vote → dossier là où l'Assemblée le pose (`actesLegislatifs[].voteRefs`) et
ne devine rien. Mesuré le 15/10/2026 : **265 des 934 votes sur l'ensemble d'un
texte** n'y figurent dans aucun dossier, et l'interface, faute de clé, regroupe
leurs lectures par l'intitulé — une loi dont l'Assemblée a reformulé le titre
entre deux lectures s'affiche deux fois (21 textes, 11 fiches de candidats).

Ce module déduit le dossier de ces votes, et SEULEMENT d'eux. Une déduction est
retenue quand **un seul** dossier remplit les trois conditions :

1. il inscrit une **décision de l'Assemblée en séance le jour du vote**
   (`codeActe` en `-DEC`, chambre AN, CMP comprise) ;
2. cette décision **n'a pas de vote attaché** — sinon la place est prise ;
3. son **titre** reprend au moins la moitié de ses mots dans l'intitulé du
   vote (`SEUIL_TITRE`), et dit « organique » quand le vote le dit.

Mesuré le 15/10/2026 en rejouant la règle sur les 669 votes que la source
rattache elle-même : 621 retrouvés, 6 faux (1 %) — quatre lois organiques et
ordinaires jumelles, votées le même jour sous le même titre, et deux erreurs de
la source elle-même. Sur les 265 votes sans dossier : 223 déduits.

L'EXCEPTION À `regrouper-nest-pas-joindre-639`, ET SES DEUX GARDE-FOUS.
Arbitrée par la propriétaire le 15/10/2026 : le rattachement déduit est
**marqué** dans le fichier publié (`provenance`), il ne remplace jamais un
rattachement de la source, et la table relue à la main
(`config/rattachements_scrutins_dossiers.json`) ne sert qu'en dernier, pour les
votes que ni la source ni la déduction ne rattachent.
→ `docs/decisions/rattachement-deduit-votes-sans-dossier-1289.md`
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Iterable, Optional

from gouvernement_textes import _determine_statut, iter_dossiers_bruts

#: La table relue à la main : une ligne par vote que ni la source ni la
#: déduction ne rattachent — le dernier rang de la cascade, jamais un
#: remplacement. Écrite par un humain, jamais par un run (#1057).
TABLE_MANUELLE = Path("config") / "rattachements_scrutins_dossiers.json"

#: Les deux marques d'un rattachement qui ne vient pas de la source. Absent de
#: `provenance`, un rattachement est celui que l'Assemblée publie.
PROVENANCE_TABLE = "table_relue"
PROVENANCE_DEDUITE = "deduit_date_et_titre"

#: Part des mots du titre du dossier qu'on doit retrouver dans l'intitulé du
#: vote. 0,5 : 621 justes et 6 faux sur 669 ; 0,7 : 546 justes, 1 faux, mais
#: 112 votes sans proposition (mesuré le 15/10/2026).
SEUIL_TITRE = 0.5

#: Les mots qui ne distinguent aucun texte : un titre de dossier qui n'aurait
#: que ceux-là en commun avec le vote ne prouve rien.
MOTS_VIDES = frozenset(
    "pour dans avec sans entre leur leurs relative relatif relatives relatifs "
    "visant portant proposition projet diverses divers dispositions mesures "
    "loi lois".split()
)

APOSTROPHES = re.compile(r"[‘’ʼ]")

# Même règle que `isWholeTextVote` (web/UI_finale/src/utils/lecture.js, #672) :
# seuls les votes sur l'ensemble d'un texte sont regroupés par lecture, et seuls
# eux reçoivent une déduction. Un vote d'amendement le même jour sur le même
# texte n'a pas de décision de séance à lui.
RX_ENSEMBLE = re.compile(r"^(?:sur )?l'ensemble\b")
RX_SOUS_PARTIE = re.compile(
    r"^(?:sur )?l'ensemble (?:de l'article\b|de la (?:[a-zàâçéèêëîïôûùüÿœ]+ )?partie\b)"
)


def normaliser(texte: Any) -> str:
    if not isinstance(texte, str):
        return ""
    texte = APOSTROPHES.sub("'", unicodedata.normalize("NFC", texte))
    # « œuvre » et « oeuvre » coexistent dans la source, d'un fichier à l'autre
    # (DLR5L16N46880 contre son vote an:16:2257).
    texte = texte.replace("œ", "oe").replace("Œ", "Oe").replace("æ", "ae")
    return re.sub(r"\s+", " ", texte).strip().lower()


def est_vote_sur_l_ensemble(scrutin: dict[str, Any]) -> bool:
    if scrutin.get("type_vote") != "vote_texte":
        return False
    libelle = normaliser(scrutin.get("texte"))
    return bool(RX_ENSEMBLE.search(libelle)) and not RX_SOUS_PARTIE.search(libelle)


def mots(texte: Any) -> set[str]:
    return set(re.findall(r"[a-zàâçéèêëîïôûùüÿœ]{4,}", normaliser(texte))) - MOTS_VIDES


def _est_decision_an(code: Any) -> bool:
    return (
        isinstance(code, str)
        and code.endswith("-DEC")
        and "DEBATS" in code
        and (code.startswith("AN") or "-AN-" in code)
    )


def _refs(valeur: Any) -> list[str]:
    if isinstance(valeur, str):
        return [valeur]
    if isinstance(valeur, dict):
        return _refs(valeur.get("voteRef"))
    if isinstance(valeur, list):
        return [r for element in valeur for r in _refs(element)]
    return []


def _cle(uid: str) -> Optional[str]:
    trouve = re.match(r"^VTANR5L(\d+)V(\d+)$", uid.strip())
    return f"an:{trouve.group(1)}:{trouve.group(2)}" if trouve else None


def _decisions(noeud: Any, trouvees: list[tuple[str, list[str]]]) -> None:
    """Ramasse `(date, clés des votes attachés)` de chaque décision AN en
    séance, quelle que soit la forme de l'arbre — même parcours que
    `_collecter_vote_refs`."""
    if isinstance(noeud, dict):
        code, date = noeud.get("codeActe"), noeud.get("dateActe")
        if _est_decision_an(code) and isinstance(date, str) and len(date) >= 10:
            cles = [c for c in (_cle(r) for r in _refs(noeud.get("voteRefs"))) if c]
            trouvees.append((date[:10], cles))
        for valeur in noeud.values():
            _decisions(valeur, trouvees)
    elif isinstance(noeud, list):
        for element in noeud:
            _decisions(element, trouvees)


def indexer_decisions(archives: list[tuple[int, Path]]) -> dict[str, Any]:
    """`{"decisions": {date: [(uid, votes attachés)]}, "dossiers": {uid: {titre, statut, sort_49_3}}}`.

    `dossiers` porte de quoi publier l'issue d'un dossier qu'aucun vote de la
    source ne nomme, par la même `_determine_statut` que la table de la source.
    """
    par_date: dict[str, list[tuple[str, list[str]]]] = {}
    dossiers: dict[str, dict[str, Any]] = {}
    for _legislature, dossier in iter_dossiers_bruts(archives):
        uid = dossier.get("uid")
        if not isinstance(uid, str) or not uid:
            continue
        trouvees: list[tuple[str, list[str]]] = []
        _decisions(dossier.get("actesLegislatifs"), trouvees)
        if not trouvees:
            continue
        statut, sort_49_3, _ = _determine_statut(uid, dossier.get("actesLegislatifs"))
        titre = (dossier.get("titreDossier") or {}).get("titre")
        dossiers[uid] = {"titre": titre, "statut": statut, "sort_49_3": sort_49_3}
        for date, cles in trouvees:
            par_date.setdefault(date, []).append((uid, cles))
    return {"decisions": par_date, "dossiers": dossiers}


def proposer(
    scrutin: dict[str, Any], decisions: dict[str, Any], sur_l_ensemble: set[str]
) -> Optional[str]:
    """Le dossier déduit pour ce vote, ou `None` si aucun ou plusieurs.

    Une décision est LIBRE quand aucun vote sur l'ensemble ne lui est attaché :
    celle qui a déjà le sien n'attend personne. Un vote d'amendement ou de
    motion attaché ne la prend pas — la source pose parfois là le vote de la
    motion de rejet au lieu de celui sur l'ensemble (DLR5L16N47637, 15/11/2023).
    """
    date = scrutin.get("date")
    if not isinstance(date, str):
        return None
    candidats = sorted({
        uid for uid, cles in decisions["decisions"].get(date) or []
        if not any(c in sur_l_ensemble for c in cles)
    })
    if not candidats:
        return None
    du_vote = mots(scrutin.get("texte"))
    organique = "organique" in normaliser(scrutin.get("texte"))
    retenus = []
    for uid in candidats:
        titre = (decisions["dossiers"].get(uid) or {}).get("titre")
        du_titre = mots(titre)
        if not du_titre or len(du_vote & du_titre) / len(du_titre) < SEUIL_TITRE:
            continue
        # Un titre de dossier qui dit « organique » ne reçoit qu'un vote qui le
        # dit aussi, et réciproquement — les jumelles organique / ordinaire
        # sont votées le même jour sous le même titre.
        if ("organique" in normaliser(titre)) != organique:
            continue
        retenus.append(uid)
    return retenus[0] if len(retenus) == 1 else None


def deduire(
    scrutins: Iterable[dict[str, Any]],
    deja_rattaches: set[str],
    decisions: dict[str, Any],
) -> dict[str, str]:
    """`{clé de scrutin: uid}` pour les votes sur l'ensemble que la source ne
    rattache pas et dont un seul dossier remplit les conditions."""
    scrutins = list(scrutins)
    sur_l_ensemble = {
        s["id"] for s in scrutins if isinstance(s.get("id"), str) and est_vote_sur_l_ensemble(s)
    }
    deduits: dict[str, str] = {}
    for scrutin in scrutins:
        cle = scrutin.get("id")
        if not isinstance(cle, str) or not cle.startswith("an:") or cle in deja_rattaches:
            continue
        if not est_vote_sur_l_ensemble(scrutin):
            continue
        uid = proposer(scrutin, decisions, sur_l_ensemble)
        if uid:
            deduits[cle] = uid
    return deduits


def charger_table_manuelle(chemin: Path = TABLE_MANUELLE) -> dict[str, Any]:
    """`{"rattachements": {clé: {dossier, …}}, "textes_distincts": [[clé, …]]}`.

    Fichier absent ou illisible : table vide — la cascade se réduit alors à la
    source et à la déduction, ce qui n'efface rien.
    """
    vide: dict[str, Any] = {"rattachements": {}, "textes_distincts": []}
    try:
        with open(chemin, encoding="utf-8") as f:
            table = json.load(f)
    except (OSError, json.JSONDecodeError):
        return vide
    if not isinstance(table, dict):
        return vide
    rattachements = {
        cle: ligne
        for cle, ligne in (table.get("rattachements") or {}).items()
        if isinstance(ligne, dict) and isinstance(ligne.get("dossier"), str)
    }
    distincts = [
        groupe for groupe in (table.get("textes_distincts") or [])
        if isinstance(groupe, list)
    ]
    return {"rattachements": rattachements, "textes_distincts": distincts}
