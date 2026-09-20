"""La règle « dernière lecture » est appliquée, et par la DATE (#711).

`AGENTS.md` §6 publie « `votes[]` vote sur le texte (`vote_texte`, dernière
lecture) », et `web/UI_finale/DESIGN_SYSTEM.md` §6 cite la formule comme exemple
de la voix de la maison. Aucun code ne l'appliquait : `isWholeTextVote` (#672)
sélectionnait les votes sur l'ensemble d'un texte et s'arrêtait là.

Mesuré au commit de données `f635cb60` le 02/09/2026, sur les 17 748 scrutins
publiés de `pivot_data/scrutins.json` : 925 votes sur l'ensemble d'un texte,
697 textes distincts une fois les lectures repliées, 187 textes votés plusieurs
fois — 228 scrutins, soit 24,6 %, comptaient une lecture déjà comptée.

Ce que ces tests verrouillent, dans l'ordre où le repli peut casser :

  1. le VOCABULAIRE des mentions de lecture, écrit une seule fois et mesuré ;
  2. ce qui n'est PAS une mention et ne doit jamais être retiré ;
  3. l'ordre par la DATE, jamais par le rang — mesuré sur les 4 groupes où les
     deux divergent ;
  4. les 51 intitulés sans mention, qui ne deviennent pas des premières
     lectures par défaut (§2 règle 5) ;
  5. la clé portant la LÉGISLATURE, qui empêche de souder deux textes
     homonymes ;
  6. le corpus des scrutins comme référence, jamais les seuls votes de la
     personne.

Le dépôt n'a pas de runner JS (`oxlint` seul), donc ces tests font deux choses,
sur le patron de `tests/test_selection_vote_ensemble_672.py` :

  1. ils lisent le **code exécuté** — commentaires retirés — pour vérifier que
     la règle est écrite une seule fois et branchée là où elle doit l'être ;
  2. ils **extraient les motifs du fichier JS** et rejouent en Python ce que le
     module fait, étape par étape, chaque étape n'étant appliquée que si le
     corps JS l'applique vraiment. Une étape retirée du module fait donc échouer
     un test de COMPORTEMENT, pas seulement un test de forme.

Aucun test ne lit `pivot_data/` (#473) : les libellés ci-dessous sont recopiés
verbatim dans le fichier.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale" / "src"

MODULE_REGLES = UI / "utils" / "lecture.js"
MODULE_GROUPE = UI / "utils" / "groupe.js"
MODULE_CANDIDAT = UI / "utils" / "profilCandidat.js"
ADAPTATEUR = UI / "data" / "pivotAdapter.js"
VUE_CANDIDAT = UI / "components" / "CandidateProfile.jsx"
PAGE_METHODO = UI / "pages" / "MethodologyPage.jsx"

#: Distribution MESURÉE des mentions finales sur les 925 scrutins « sur
#: l'ensemble d'un texte », commit de données `f635cb60`, 02/09/2026. Le
#: cadrage de l'issue en nommait 8 ; la mesure en trouve 16, dont quatre
#: coquilles de la source. Chacune doit être reconnue, sinon deux lectures d'un
#: même texte restent comptées deux fois.
MENTIONS_MESUREES = {
    "première lecture": 546,
    "texte de la commission mixte paritaire": 158,
    "lecture définitive": 54,
    "deuxième lecture": 48,
    "nouvelle lecture": 46,
    "texte de la commission paritaire": 8,
    "1ère lecture": 3,
    "2e lecture": 2,
    "troisième lecture": 2,
    "1re lecture": 1,
    "texte cmp": 1,
    "premiere lecture": 1,
    "texte de la commisison mixte paritaire": 1,
    "texte de la commisson mixte pariraire": 1,
    "lecture défintive": 1,
    "lecture défnitive": 1,
}

#: Les parenthèses finales qui ne sont PAS des mentions de lecture. Les retirer
#: souderait des textes distincts — c'est-à-dire l'erreur que `texte_vise`
#: (#696) a interdite, celle qui affirme au lieu de manquer.
#:
#: `article 34-1` : une résolution de l'article 34-1 de la Constitution n'a pas
#: de lecture ; 2 scrutins sur les 925.
#: `(2)` : le SECOND projet de loi de finances rectificative pour 2020 — la
#: parenthèse distingue deux textes, pas deux lectures.
#: `(2ème vote)` : `an:14:1086`, le scrutin qui REMPLACE le scrutin annulé
#: `an:14:1085`. C'est pour lui que les ordinaux en chiffres exigent le mot
#: « lecture » derrière eux.
PARENTHESES_QUI_NE_SONT_PAS_UNE_LECTURE = {
    "an:16:924": (
        "l'ensemble de la proposition de résolution tendant à la création d'une "
        "commission d'enquête sur le coût de la vie dans les collectivités "
        "régies par les articles 73 et 74 de la Constitution "
        "(article 34-1 de la Constitution)"
    ),
    "an:17:685-abrege": (
        "l'ensemble de la proposition de résolution européenne relative à "
        "l'adoption d'exigences à l'importation (art. 34-1 de la Constitution)"
    ),
    "an:15:2737": (
        "l'ensemble du projet de loi de finances rectificative pour 2020 (2) "
        "(première lecture)."
    ),
    "an:14:1086": (
        "l'ensemble du projet de loi, adopté par le Sénat, après engagement de "
        "la procédure accélérée, ratifiant l'ordonnance n° 2014-1543 du 19 "
        "décembre 2014 portant diverses mesures relatives à la création de la "
        "métropole de Lyon (2ème vote)"
    ),
}

#: Les DEUX lectures du projet de loi de simplification de la vie économique,
#: verbatim. Gabriel Attal, qui l'avait déposé comme Premier ministre le
#: 24/04/2024, a voté CONTRE en première lecture ; la loi a été adoptée sur le
#: texte de la commission mixte paritaire, scrutin où aucune position de lui
#: n'est enregistrée. Publier son « contre » comme sa position sur cette loi
#: aurait été faux — et dire pourquoi il manque au scrutin final publierait une
#: absence individuelle (§2 règle 3).
SIMPLIFICATION = [
    {
        "id": "an:17:2458",
        "legislature": "17",
        "numero_scrutin": "2458",
        "date": "2025-06-17",
        "type_vote": "vote_texte",
        "texte": (
            "l'ensemble du projet de loi de simplification de la vie économique "
            "(première lecture)."
        ),
    },
    {
        "id": "an:17:6184",
        "legislature": "17",
        "numero_scrutin": "6184",
        "date": "2026-04-14",
        "type_vote": "vote_texte",
        "texte": (
            "l'ensemble du projet de loi de simplification de la vie économique "
            "(texte de la commission mixte paritaire)."
        ),
    },
]

#: Le groupe qui prouve que le RANG ne peut pas ordonner : deux « première
#: lecture » encadrant une « lecture définitive ». L'Assemblée réemploie le
#: titre pour les deux collectifs budgétaires de 2017 ; un tri par rang
#: retiendrait la lecture définitive du 14 novembre, alors que le dernier
#: scrutin est celui du 12 décembre. 4 groupes des 697 sont dans ce cas.
PLFR_2017 = [
    {
        "id": "an:15:227",
        "legislature": "15",
        "numero_scrutin": "227",
        "date": "2017-11-06",
        "type_vote": "vote_texte",
        "texte": (
            "l'ensemble du projet de loi de finances rectificative pour 2017 "
            "(première lecture)."
        ),
    },
    {
        "id": "an:15:246",
        "legislature": "15",
        "numero_scrutin": "246",
        "date": "2017-11-14",
        "type_vote": "vote_texte",
        "texte": (
            "l'ensemble du projet de loi de finances rectificative pour 2017 "
            "(lecture définitive)."
        ),
    },
    {
        "id": "an:15:345",
        "legislature": "15",
        "numero_scrutin": "345",
        "date": "2017-12-12",
        "type_vote": "vote_texte",
        "texte": (
            "l'ensemble du projet de loi de finances rectificative pour 2017 "
            "(première lecture)."
        ),
    },
]

#: Le groupe où la dernière lecture ne porte AUCUNE mention. 51 des 925
#: intitulés sont dans ce cas — 49 sans parenthèse finale, 2 avec une
#: parenthèse qui n'est pas une lecture. Ils ne deviennent pas « première
#: lecture » par défaut : leur rang reste inconnu, et c'est la DATE qui tranche.
#: Ici la table des rangs mettrait `an:14:590` en dernier ; la date retient
#: `an:14:594`, qui n'a pas de mention du tout.
TRANSPARENCE_VIE_PUBLIQUE = [
    {
        "id": "an:14:536",
        "legislature": "14",
        "numero_scrutin": "536",
        "date": "2013-06-25",
        "type_vote": "vote_texte",
        "texte": "l'ensemble du projet de loi relatif à la transparence de la vie publique.",
    },
    {
        "id": "an:14:590",
        "legislature": "14",
        "numero_scrutin": "590",
        "date": "2013-07-23",
        "type_vote": "vote_texte",
        "texte": (
            "l'ensemble du projet de loi relatif à la transparence de la vie "
            "publique (nouvelle lecture)."
        ),
    },
    {
        "id": "an:14:594",
        "legislature": "14",
        "numero_scrutin": "594",
        "date": "2013-09-17",
        "type_vote": "vote_texte",
        "texte": "l'ensemble du projet de loi relatif à la transparence de la vie publique",
    },
]

#: Deux textes HOMONYMES de deux législatures. 10 groupes des 925 sont dans ce
#: cas si la clé ne porte pas la législature. Le repli doit ÉCHOUER À
#: REGROUPER : compter le texte deux fois est un manque, le souder à un autre
#: texte serait une affirmation.
HOMONYMES_DE_DEUX_LEGISLATURES = [
    {
        "id": "an:15:3888",
        "legislature": "15",
        "numero_scrutin": "3888",
        "date": "2021-07-08",
        "type_vote": "vote_texte",
        "texte": "l'ensemble du projet de loi relatif à la protection des enfants (première lecture).",
    },
    {
        "id": "an:17:8430",
        "legislature": "17",
        "numero_scrutin": "8430",
        "date": "2026-07-21",
        "type_vote": "vote_texte",
        "texte": "l'ensemble du projet de loi relatif à la protection des enfants (première lecture).",
    },
]

#: Le seul ex aequo de date des 697 groupes : deux votes du même jour sur le
#: même texte. Le numéro de scrutin départage, et il ne le peut QUE parce que la
#: clé porte la législature — le numéro repart à 1 à chaque législature
#: (`AGENTS.md` §5).
#:
#: L'ordre de la liste est VOLONTAIREMENT l'inverse de l'ordre attendu : un tri
#: stable qui ne départagerait plus rien rendrait `an:15:2769`, et le test doit
#: tomber dans ce cas. Vérifié par mutation le 02/09/2026 — dans l'ordre
#: naturel, retirer le tri par numéro laissait ce test au vert.
ETHIQUE_DE_L_URGENCE = [
    {
        "id": "an:15:2770",
        "legislature": "15",
        "numero_scrutin": "2770",
        "date": "2020-06-25",
        "type_vote": "vote_texte",
        "texte": (
            "l'ensemble de la proposition de loi pour une éthique de l'urgence "
            "(première lecture)."
        ),
    },
    {
        "id": "an:15:2769",
        "legislature": "15",
        "numero_scrutin": "2769",
        "date": "2020-06-25",
        "type_vote": "vote_texte",
        "texte": (
            "l'ensemble de la proposition de loi pour une éthique de l'urgence "
            "(première lecture)."
        ),
    },
]

#: Le même texte, deux lectures, deux apostrophes DANS LE TITRE. 18 groupes des
#: 697 mêlent l'ASCII `\'` et la typographique `\u2019` entre leurs lectures :
#: sans la normalisation de #672, ces textes seraient comptés deux fois. Et la
#: typographique n'apparaît que dans les législatures 16 et 17, les deux plus
#: récentes — le défaut s'aggraverait avec le temps.
#:
#: L'apostrophe choisie est celle d'« accélération », À L'INTÉRIEUR du titre,
#: et non celle de « l'ensemble » : `OUVERTURE_VOTE_ENSEMBLE` accepte déjà les
#: deux formes, si bien qu'une paire ne différant que là passerait au vert sur
#: un module amputé de sa normalisation. Vérifié par mutation le 02/09/2026.
NOUVELLES_INSTALLATIONS_NUCLEAIRES = [
    {
        "id": "an:16:1243",
        "legislature": "16",
        "numero_scrutin": "1243",
        "date": "2023-03-21",
        "type_vote": "vote_texte",
        "texte": (
            "l'ensemble du projet de loi relatif à l\u2019accélération des procédures "
            "liées à la construction de nouvelles installations nucléaires à "
            "proximité de sites nucléaires existants et au fonctionnement des "
            "installations existantes (première lecture)."
        ),
    },
    {
        "id": "an:16:1533",
        "legislature": "16",
        "numero_scrutin": "1533",
        "date": "2023-05-16",
        "type_vote": "vote_texte",
        "texte": (
            "l'ensemble du projet de loi relatif à l'accélération des procédures "
            "liées à la construction de nouvelles installations nucléaires à "
            "proximité de sites nucléaires existants et au fonctionnement des "
            "installations existantes (texte de la commission mixte paritaire)."
        ),
    },
]

#: Une mention de lecture qui n'est PAS en fin d'intitulé. Aucun des 925
#: scrutins « sur l'ensemble d'un texte » n'est dans ce cas — mais 432 des
#: 17 748 publiés le sont, tous des votes sur un article ou un amendement, que
#: `isWholeTextVote` écarte. L'ancrage en fin est donc une garde dont l'effet
#: n'est pas observable sur la population que ce lot replie, et c'est
#: exactement pour cela qu'elle est testée ici plutôt que supposée.
MENTION_QUI_N_EST_PAS_EN_FIN = (
    "l'amendement n° 494 de M. Ratenon à l'article 39 et État B de la seconde "
    "partie du projet de loi de finances pour 2019 (première lecture) - Mission "
    "Outre-mer"
)


def sans_commentaires(source: str) -> str:
    """Le code exécuté seul : ni `/* … */`, ni `// …`.

    Indispensable ici : les commentaires de `utils/lecture.js` CITENT la
    distribution des mentions, ligne par ligne. Un test qui lirait le fichier
    brut passerait sur la documentation de la règle au lieu de la règle.
    """
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"(?<!:)//[^\n]*", "", source)


@pytest.fixture(scope="module")
def regles() -> str:
    return sans_commentaires(MODULE_REGLES.read_text(encoding="utf-8"))


def _litteral(regles: str, nom: str) -> tuple[str, str]:
    """Le littéral d'expression régulière déclaré en JS, motif et drapeaux."""
    trouve = re.search(rf"{nom}\s*=\s*\n?\s*/(.+?)/([gimsuy]*);", regles)
    assert trouve, f"`{nom}` n'est plus déclaré dans utils/lecture.js"
    return trouve.group(1), trouve.group(2)


def _regexp_construite(regles: str, nom: str) -> re.Pattern[str]:
    """Compile en Python un `new RegExp(\\`…\\`, '…')` construit sur le
    vocabulaire partagé.

    Le gabarit est LU dans la source, jamais recopié ici : sans cela, retirer le
    `$` du littéral JS laisserait ce test au vert. C'est le seul moyen, sans
    runner JS, de tester l'ANCRAGE et pas seulement le vocabulaire.
    """
    trouve = re.search(
        rf"{nom}\s*=\s*new RegExp\(\s*`([^`]*)`,\s*'([a-z]*)',?\s*\)", regles, flags=re.DOTALL
    )
    assert trouve, f"`{nom}` n'est plus construit par `new RegExp` dans utils/lecture.js"

    gabarit, drapeaux = trouve.group(1), trouve.group(2)
    assert "${MENTIONS_DE_LECTURE.source}" in gabarit, (
        f"`{nom}` doit être construit sur `MENTIONS_DE_LECTURE.source` : le "
        "vocabulaire des mentions est écrit UNE fois, seul l'ancrage varie (#711)"
    )

    vocabulaire, _ = _litteral(regles, "MENTIONS_DE_LECTURE")
    # Dans un littéral de gabarit JS, `\\s` désigne le `\s` d'une expression
    # régulière : on défait l'échappement du langage, pas celui du motif.
    motif = gabarit.replace("\\\\", "\\").replace("${MENTIONS_DE_LECTURE.source}", vocabulaire)
    return re.compile(motif, re.IGNORECASE if "i" in drapeaux else 0)


def _corps(regles: str, signature: str) -> str:
    trouve = re.search(rf"function {signature}\s*\{{(.*?)\n\}}", regles, flags=re.DOTALL)
    assert trouve, f"`{signature}` a disparu de utils/lecture.js"
    return trouve.group(1)


@pytest.fixture(scope="module")
def moteur(regles):
    """Rejoue en Python ce que `utils/lecture.js` fait en JS.

    Chaque étape n'est appliquée que si le corps JS l'applique vraiment : la
    normalisation, le retrait de l'ouverture « l'ensemble du… », le retrait de
    la mention de lecture, la législature dans la clé, le tri par date puis par
    numéro, la garde sur une lecture sans date. Retirer l'une d'elles du module
    fait échouer un test de comportement, pas seulement un test de forme.
    """
    fin = _regexp_construite(regles, "MENTION_DE_LECTURE")
    ouverture_motif, ouverture_drapeaux = _litteral(regles, "OUVERTURE_VOTE_ENSEMBLE")
    ouverture = re.compile(ouverture_motif, re.IGNORECASE if "i" in ouverture_drapeaux else 0)

    corps_normalisation = _corps(regles, r"normalizeLabel\(texte\)")
    corps_cle = _corps(regles, r"cleDuTexteVote\(scrutin\)")
    corps_ordre = _corps(regles, r"ordreDesLectures\(a, b\)")
    corps_derniere = _corps(regles, r"derniereLecture\(lectures\)")

    applique_nfc = "normalize('NFC')" in corps_normalisation
    applique_apostrophes = "APOSTROPHES" in corps_normalisation
    applique_espaces = re.search(r"\\s\+", corps_normalisation) is not None
    applique_casse = "toLowerCase()" in corps_normalisation

    normalise = "normalizeLabel(" in corps_cle
    retire_ouverture = "OUVERTURE_VOTE_ENSEMBLE" in corps_cle
    retire_mention = "MENTION_DE_LECTURE" in corps_cle
    cle_porte_la_legislature = "legislature" in corps_cle

    ordonne_par_date = "date" in corps_ordre
    ordonne_par_numero = "numero_scrutin" in corps_ordre

    garde_sans_date = "date" in corps_derniere and "some(" in corps_derniere
    exception_lecture_unique = "length === 1" in corps_derniere
    prend_la_derniere = re.search(r"length - 1\]", corps_derniere) is not None

    def _normalise(texte: str) -> str:
        if not isinstance(texte, str):
            return ""
        libelle = texte
        if applique_nfc:
            libelle = unicodedata.normalize("NFC", libelle)
        if applique_apostrophes:
            libelle = re.sub(r"[’ʼʹ′]", "'", libelle)
        if applique_espaces:
            libelle = re.sub(r"\s+", " ", libelle).strip()
        if applique_casse:
            libelle = libelle.lower()
        return libelle

    def _cle(scrutin: dict) -> str | None:
        libelle = _normalise(scrutin.get("texte")) if normalise else (scrutin.get("texte") or "")
        if not libelle:
            return None
        titre = libelle
        if retire_ouverture:
            titre = ouverture.sub("", titre)
        if retire_mention:
            titre = fin.sub("", titre)
        titre = re.sub(r"[.\s]+$", "", titre).strip()
        if not titre:
            return None
        prefixe = f"{scrutin.get('legislature') or ''}\0" if cle_porte_la_legislature else ""
        return prefixe + titre

    def _ordre(scrutin: dict):
        return (
            str(scrutin.get("date") or "") if ordonne_par_date else "",
            int(scrutin.get("numero_scrutin") or 0) if ordonne_par_numero else 0,
        )

    def _derniere(lectures: list[dict]) -> dict | None:
        if not lectures:
            return None
        if exception_lecture_unique and len(lectures) == 1:
            return lectures[0]
        if garde_sans_date and any(not s.get("date") for s in lectures):
            return None
        triees = sorted(lectures, key=_ordre)
        return triees[-1] if prend_la_derniere else triees[0]

    def _grouper(scrutins: list[dict]) -> dict[str, list[dict]]:
        groupes: dict[str, list[dict]] = {}
        for scrutin in scrutins:
            cle = _cle(scrutin)
            if cle is None:
                continue
            groupes.setdefault(cle, []).append(scrutin)
        return groupes

    return {
        "normalise": _normalise,
        "mention": fin,
        "cle": _cle,
        "grouper": _grouper,
        "derniere": _derniere,
    }


# ── 1. La règle vit dans le module partagé, une seule fois ──────────────────


def test_la_regle_est_ecrite_dans_le_module_partage(regles):
    """Un seul endroit, à côté d'`isWholeTextVote` — pas une seconde façon de
    sélectionner un vote sur l'ensemble d'un texte (la contrainte de #672)."""
    for symbole in (
        "MENTION_DE_LECTURE",
        "MENTION_DE_LECTURE_PARTOUT",
        "cleDuTexteVote",
        "grouperLecturesParTexte",
        "derniereLecture",
        "selectDerniereLectureVotes",
        "LAST_READING_LABEL",
        "LAST_READING_RULE",
    ):
        assert (
            f"export const {symbole}" in regles or f"export function {symbole}" in regles
        ), (
            f"`{symbole}` doit être exporté par utils/lecture.js : la règle de "
            "#711 est écrite une seule fois, et les vues l'appellent"
        )


def test_le_regroupement_part_de_la_selection_de_672(regles):
    """`grouperLecturesParTexte` REGROUPE ce que #672 sélectionne ; il ne
    redéfinit pas ce qu'est un vote sur l'ensemble d'un texte."""
    corps = _corps(regles, r"grouperLecturesParTexte\(scrutins\)")
    assert "selectWholeTextVotes(" in corps, (
        "le regroupement doit partir de `selectWholeTextVotes` (#672) : une "
        "seconde définition de « vote sur l'ensemble d'un texte » est "
        "exactement ce que #672 a fermé"
    )


def test_le_vocabulaire_des_mentions_n_est_ecrit_qu_une_fois():
    """Trois modules retiraient la mention de lecture ; deux la déclaraient.

    `utils/groupe.js` portait sa propre liste, sans les formes en chiffres — 60
    des 17 748 scrutins publiés portaient « (1ère lecture) » ou « (2ème
    lecture) » et fabriquaient une désignation de texte de plus.
    """
    groupe = sans_commentaires(MODULE_GROUPE.read_text(encoding="utf-8"))
    assert "MENTION_DE_LECTURE_PARTOUT" in groupe, (
        "`utils/groupe.js` doit IMPORTER le vocabulaire des mentions de "
        "`utils/lecture.js`, pas en redéclarer une copie (#711)"
    )
    assert re.search(r"/[^/\n]*lecture[^/\n]*/[gimsuy]*\s*;", groupe) is None, (
        "aucun littéral d'expression régulière sur « lecture » hors du module "
        f"partagé : {MODULE_GROUPE.name} en portait un, et il divergeait"
    )


# ── 2. Le vocabulaire, mesuré ────────────────────────────────────────────────


@pytest.mark.parametrize("mention", sorted(MENTIONS_MESUREES), ids=lambda m: m)
def test_les_seize_mentions_mesurees_sont_toutes_reconnues(moteur, mention):
    """Une mention non reconnue ne soude pas à tort : elle ÉCHOUE À REGROUPER,
    et les deux lectures restent comptées deux fois — l'état d'avant ce lot."""
    libelle = moteur["normalise"](
        f"l'ensemble du projet de loi de contrôle ({mention})."
    )
    assert moteur["mention"].search(libelle), (
        f"« ({mention}) » est une mention de lecture mesurée "
        f"{MENTIONS_MESUREES[mention]} fois sur les 925 scrutins « sur "
        "l'ensemble d'un texte » : elle doit être repliée"
    )


@pytest.mark.parametrize(
    "cas", sorted(PARENTHESES_QUI_NE_SONT_PAS_UNE_LECTURE), ids=lambda c: c
)
def test_ce_qui_n_est_pas_une_mention_de_lecture_reste_dans_la_cle(moteur, cas):
    """Retirer « (2) » ou « (2ème vote) » souderait deux TEXTES distincts.

    C'est l'erreur que #696 a interdite sur `texte_vise` : un appariement par
    libellé qui fusionne au lieu de manquer. Le repli n'a le droit d'échouer
    que dans un sens.
    """
    intitule = PARENTHESES_QUI_NE_SONT_PAS_UNE_LECTURE[cas]
    cle = moteur["cle"]({"legislature": "17", "texte": intitule})
    assert cle is not None

    for temoin in ("(2)", "(2ème vote)", "34-1"):
        if temoin.lower() in intitule.lower():
            assert temoin.lower().strip("()") in cle, (
                f"« {temoin} » distingue un texte, pas une lecture : il doit "
                f"rester dans la clé de regroupement de {cas}"
            )


def test_les_cinquante_et_un_intitules_sans_mention_ne_deviennent_pas_une_premiere_lecture(
    moteur,
):
    """51 des 925 intitulés ne portent aucune mention de lecture.

    Ils ne prennent AUCUN rang par défaut (§2 règle 5) : ils gardent leur titre
    nu, qui est justement la clé de regroupement, et c'est la DATE qui les
    ordonne. Ici la dernière lecture du texte est un intitulé SANS mention —
    une table de rangs, elle, aurait retenu la « nouvelle lecture ».
    """
    groupes = moteur["grouper"](TRANSPARENCE_VIE_PUBLIQUE)
    assert len(groupes) == 1, (
        "un intitulé sans mention porte le titre nu, donc la même clé que ses "
        f"lectures mentionnées : {list(groupes)}"
    )

    derniere = moteur["derniere"](next(iter(groupes.values())))
    assert derniere["id"] == "an:14:594", (
        "la dernière lecture du 17/09/2013 ne porte AUCUNE mention. La retenir "
        "vient de sa date ; un classement par rang aurait retenu la « nouvelle "
        "lecture » du 23/07/2013"
    )


# ── 3. La date ordonne, jamais le rang ──────────────────────────────────────


def test_la_derniere_lecture_se_choisit_par_la_date_jamais_par_le_rang(moteur):
    """4 groupes des 697 mettent les deux ordres en contradiction.

    La date est COLLECTÉE ; le rang n'existe que dans l'intitulé, et il y manque
    51 fois sur 925. Le repli sert à grouper, la date à ordonner.
    """
    groupes = moteur["grouper"](PLFR_2017)
    assert len(groupes) == 1

    derniere = moteur["derniere"](next(iter(groupes.values())))
    assert derniere["id"] == "an:15:345", (
        "le dernier scrutin du projet de loi de finances rectificative pour "
        "2017 est celui du 12/12/2017, une « première lecture ». Un tri par "
        "rang retiendrait la « lecture définitive » du 14/11/2017, qui n'est "
        "pas la plus récente"
    )


def test_la_lecture_la_plus_tardive_est_retenue_meme_quand_la_personne_y_manque(moteur):
    """Le cas qui retire une affirmation fausse.

    Gabriel Attal a voté CONTRE le projet de loi de simplification de la vie
    économique en première lecture le 17/06/2025 ; la loi a été adoptée sur le
    texte de la commission mixte paritaire le 14/04/2026, scrutin où aucune
    position de lui n'est enregistrée. La dernière lecture est celle de la CMP,
    et son « contre » ne peut donc pas être publié comme sa position sur cette
    loi.
    """
    groupes = moteur["grouper"](SIMPLIFICATION)
    assert len(groupes) == 1, (
        "les deux lectures du même texte partagent leur clé : c'est le repli de "
        f"la mention qui le permet — {list(groupes)}"
    )

    derniere = moteur["derniere"](next(iter(groupes.values())))
    assert derniere["id"] == "an:17:6184"


def test_l_ex_aequo_de_date_est_departage_par_le_numero_de_scrutin(moteur):
    """Un seul groupe des 697 en a besoin, et le numéro ne peut le faire que
    parce que la clé porte la législature : il repart à 1 à chaque
    législature (`AGENTS.md` §5)."""
    groupes = moteur["grouper"](ETHIQUE_DE_L_URGENCE)
    assert len(groupes) == 1

    derniere = moteur["derniere"](next(iter(groupes.values())))
    assert derniere["id"] == "an:15:2770", (
        "deux scrutins du 25/06/2020 sur le même texte : le départage est "
        "déterministe, par le numéro de scrutin, jamais par l'ordre de lecture "
        "du fichier"
    )


def test_les_deux_apostrophes_designent_le_meme_texte(moteur):
    """18 groupes des 697 mêlent l'ASCII et la typographique ENTRE leurs lectures.

    Sans la normalisation de #672, ces textes seraient comptés deux fois — et
    l'apostrophe typographique n'apparaît que dans les législatures 16 et 17,
    les deux plus récentes : le défaut s'aggraverait avec le temps.
    """
    groupes = moteur["grouper"](NOUVELLES_INSTALLATIONS_NUCLEAIRES)
    assert len(groupes) == 1, (
        "« l'ensemble » et « l’ensemble » nomment le même texte : la clé se "
        f"compare sous forme normalisée, jamais brute — {list(groupes)}"
    )

    derniere = moteur["derniere"](next(iter(groupes.values())))
    assert derniere["id"] == "an:16:1533"


def test_une_mention_qui_n_est_pas_en_fin_reste_dans_la_cle(regles, moteur):
    """L'ancrage en fin est une garde, et son effet n'est pas observable sur les
    925 : aucun n'a de mention ailleurs qu'en fin.

    432 des 17 748 scrutins publiés en ont une — tous des votes sur un article
    ou un amendement, qu'`isWholeTextVote` écarte. Sans l'ancrage, le libellé
    ci-dessous perdrait « (première lecture) » et garderait « - Mission
    Outre-mer », c'est-à-dire une clé qui ne nomme plus la même chose.
    """
    gabarit = re.search(
        r"MENTION_DE_LECTURE\s*=\s*new RegExp\(\s*`([^`]*)`", regles, flags=re.DOTALL
    )
    assert gabarit, "`MENTION_DE_LECTURE` a disparu"
    assert gabarit.group(1).rstrip().endswith("$"), (
        "la mention se cherche EN FIN d'intitulé. Non ancrée, elle se retire "
        "n'importe où — et `MENTION_DE_LECTURE_PARTOUT` existe justement pour "
        "le cas où c'est ce que l'on veut"
    )

    cle = moteur["cle"]({"legislature": "15", "texte": MENTION_QUI_N_EST_PAS_EN_FIN})
    assert "première lecture" in cle, (
        "une mention suivie d'autre chose n'est pas la mention finale : la "
        "retirer changerait le texte que la clé désigne"
    )


# ── 4. Ce que la clé refuse de souder ───────────────────────────────────────


def test_deux_textes_homonymes_de_deux_legislatures_ne_sont_pas_soudes(moteur):
    """10 groupes des 925 seraient soudés par une clé sans législature.

    Compter deux fois un texte réellement repris après une dissolution est un
    MANQUE ; souder deux textes distincts serait une AFFIRMATION. Le repli n'a
    le droit d'échouer que dans le premier sens.
    """
    groupes = moteur["grouper"](HOMONYMES_DE_DEUX_LEGISLATURES)
    assert len(groupes) == 2, (
        "« projet de loi relatif à la protection des enfants » est voté en "
        "législature 15 et en législature 17 ; rien dans le corpus ne dit que "
        "c'est le même texte, et la clé doit donc porter la législature"
    )


# ── 5. Une lecture sans date ne s'ordonne pas ───────────────────────────────


def test_un_groupe_dont_une_lecture_n_a_pas_de_date_n_a_pas_de_derniere_lecture(moteur):
    """Aucun des 925 scrutins mesurés n'est dans ce cas : la garde est écrite
    parce qu'un tri sur une date absente choisirait au hasard (§2 règle 5)."""
    sans_date = [dict(SIMPLIFICATION[0], date=None), SIMPLIFICATION[1]]
    assert moteur["derniere"](sans_date) is None, (
        "une lecture sans date ne s'ordonne pas : mieux vaut ne rien publier "
        "que de désigner une « dernière lecture » au hasard"
    )


def test_une_lecture_unique_sans_date_reste_la_derniere(moteur):
    """Il n'y a alors rien à ordonner : refuser publierait un vide là où la
    source a bien un scrutin."""
    unique = [dict(SIMPLIFICATION[0], date=None)]
    assert moteur["derniere"](unique) is not None


# ── 6. Le corpus, jamais les seuls votes de la personne ─────────────────────


def test_le_decompte_lit_le_corpus_des_scrutins_pas_les_votes_du_profil():
    """La dernière lecture d'un texte se lit sur TOUTES ses lectures.

    Sur `gabriel-attal`, ordonner ses propres lectures donne 120 textes ;
    ordonner celles du corpus en donne 111. Les 9 d'écart sont des textes dont
    il a voté une lecture antérieure et pas la dernière.
    """
    candidat = sans_commentaires(MODULE_CANDIDAT.read_text(encoding="utf-8"))
    adaptateur = sans_commentaires(ADAPTATEUR.read_text(encoding="utf-8"))

    corps = re.search(
        r"function votesDuProfil\((.*?)\)\s*\{(.*?)\n\}", candidat, flags=re.DOTALL
    )
    assert corps, "`votesDuProfil` a disparu de utils/profilCandidat.js"

    assert "scrutinsCorpus" in corps.group(1), (
        "`votesDuProfil` doit recevoir le CORPUS des scrutins : la dernière "
        "lecture ne se déduit pas des seuls votes de la personne (#711)"
    )
    assert "selectDerniereLectureVotes(scrutinsCorpus)" in corps.group(2), (
        "la sélection vient du module partagé (`utils/lecture.js`) et n'est pas "
        "réécrite dans la fiche candidat"
    )
    assert re.search(r"votesDuProfil\((?:.|\n)*?scrutinsIndex", adaptateur), (
        "`pivotAdapter` doit passer `scrutinsIndex` à `votesDuProfil` : sans "
        "lui, la règle publiée n'est pas celle qui s'applique"
    )


def test_un_corpus_absent_se_declare_et_ne_retombe_sur_rien():
    """Une règle de repli qui remplace silencieusement la règle publiée est ce
    qui a rendu #510 invisible."""
    candidat = sans_commentaires(MODULE_CANDIDAT.read_text(encoding="utf-8"))
    vue = sans_commentaires(VUE_CANDIDAT.read_text(encoding="utf-8"))

    assert "derniereLectureDisponible" in candidat, (
        "l'indisponibilité du corpus est un fait DÉCLARÉ, pas un décompte "
        "silencieusement non replié (§2 règle 5)"
    )
    assert "derniereLectureDisponible" in vue, (
        "la vue doit lire cette déclaration : un compteur non replié affirmerait "
        "une position de première lecture comme la position sur la loi"
    )


# ── 7. Le compteur dit sa règle ─────────────────────────────────────────────


def test_la_regle_est_publiee_avec_sa_phrase_et_son_pourquoi(regles):
    """Un compteur qui replie sans le dire ment par omission (DESIGN_SYSTEM §6 :
    chaque métrique porte sa propre limite)."""
    bloc = re.search(r"LAST_READING_RULE\s*=\s*\{(.*?)\n\};", regles, flags=re.DOTALL)
    assert bloc, "`LAST_READING_RULE` a disparu : la règle est du texte publié"

    texte = bloc.group(1)
    for cle in ("phrase:", "pourquoi:"):
        assert cle in texte, (
            f"la règle porte `{cle}` comme `WHOLE_TEXT_VOTE_BOUND` : la phrase "
            "est ce que le lecteur voit, le pourquoi ce qu'il peut vérifier"
        )
    assert "dernière lecture" in texte, (
        "la phrase publiée doit nommer la dernière lecture — c'est la règle "
        "qu'`AGENTS.md` §6 et le DESIGN_SYSTEM §6 annoncent"
    )
    assert "absence individuelle" in texte, (
        "le pourquoi doit dire ce qui arrive quand la personne n'a pas de "
        "position sur la dernière lecture : le texte n'est pas affiché, et nous "
        "ne disons pas pourquoi elle y manque (§2 règle 3)"
    )

    etiquette = re.search(r"LAST_READING_LABEL\s*=\s*'([^']*)'", regles)
    assert etiquette, "`LAST_READING_LABEL` a disparu"
    assert "dernière lecture" in etiquette.group(1), (
        "l'étiquette qui accompagne le CHIFFRE doit dire la règle : « 111 "
        "textes » sans elle se lit comme « 111 votes »"
    )


def test_le_libelle_affiche_dit_la_regle_a_cote_du_chiffre():
    """Le chiffre porte son étiquette sur la fiche ; le raisonnement, la méthodologie.

    #711 EST RENVERSÉ SUR CE POINT, ET C'EST UNE DÉCISION, PAS UN OUBLI.

    #711 exigeait que la règle de la dernière lecture soit publiée SUR LA FICHE,
    à côté du chiffre — parce que la méthodologie l'annonçait déjà à l'époque où
    rien ne l'appliquait, et qu'une règle annoncée sans être appliquée est pire
    que pas de règle du tout.

    Ce qui a changé le 10/09 : la règle EST appliquée, et depuis #711 —
    `isWholeTextVote` et le repli sur la dernière lecture vivent dans
    `utils/lecture.js`, et le chiffre affiché en dérive. L'incident que #711
    corrigeait ne peut plus se reproduire en silence : c'est le CODE qui applique
    la règle, plus une phrase qui promet qu'elle l'est.

    Ce qui reste garanti ici, et qui est l'essentiel de #711 : le chiffre porte
    son étiquette courte (`LAST_READING_LABEL`), il est bâti sur les TEXTES
    retenus, et le raisonnement complet est publié en méthodologie, où mène le
    renvoi posé sous la figure.

    → `docs/decisions/regle-de-lecture-en-methodologie-328.md`
    """
    vue = sans_commentaires(VUE_CANDIDAT.read_text(encoding="utf-8"))
    methodo = sans_commentaires(PAGE_METHODO.read_text(encoding="utf-8"))

    assert "LAST_READING_LABEL" in vue, (
        "le chiffre affiché sur la fiche candidat porte son étiquette : sans "
        "elle, le lecteur compare des textes à des votes"
    )
    assert "votes.textes" in vue, (
        "la barre de positions doit être bâtie sur les TEXTES retenus, pas sur "
        "les votes sur l'ensemble d'un texte"
    )
    assert "LAST_READING_RULE" in methodo, (
        "le raisonnement de la règle est publié en méthodologie, où mène le "
        "renvoi posé sous la figure"
    )
