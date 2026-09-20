"""La sélection des votes « sur l'ensemble d'un texte » est verrouillée (#672).

Cinq vues de la refonte #324 sélectionnent ces scrutins. Avant cette issue la
règle n'était écrite nulle part, et la sélection était fausse dans les deux
sens — 22 scrutins manqués sur les législatures 16 et 17 à cause d'une
apostrophe typographique, 6 capturés à tort par une recherche en sous-chaîne.

Les deux erreurs ne se compensent pas, et la seconde est la plus grave :
publier un vote sur un amendement, sur un article ou sur une motion de rejet
comme un vote sur l'ensemble d'un texte affirme une position que la personne
n'a pas prise (AGENTS.md §2 règle 2, et §2 règle 4 pour la motion). Un vote
manqué est un vide ; un vote inventé est une affirmation.

Le dépôt n'a pas de runner JS (`oxlint` seul), donc ces tests font deux choses,
sur le patron de `tests/test_fondations_lecture_326.py` :

  1. ils lisent le **code exécuté** — commentaires retirés — pour vérifier que
     la règle est écrite une seule fois, ancrée, et normalisée ;
  2. ils **extraient les motifs du fichier JS** et les exécutent en Python sur
     un tableau gelé de libellés réels, pour vérifier ce qu'ils retiennent et
     ce qu'ils écartent. Un motif redevenu sous-chaîne échoue alors sur les
     faux positifs nommés, pas seulement sur sa forme.

Chiffres cités : mesurés au commit de données `c6edee05` le 31/08/2026, sur les
17 748 scrutins publiés de `pivot_data/scrutins.json`. Aucun test ne lit
`pivot_data/` (#473) : les libellés ci-dessous sont recopiés dans le fichier.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale" / "src"

MODULE_REGLES = UI / "utils" / "lecture.js"

#: Les 5 scrutins que la recherche en sous-chaîne publiait à tort comme des
#: votes sur l'ensemble d'un texte. Ce sont les faux positifs de l'issue #672 :
#: 1 motion de rejet préalable, 1 article unique, 2 amendements, 1 article
#: premier. Libellés recopiés verbatim de `pivot_data/scrutins.json`.
FAUX_POSITIFS_SOUS_CHAINE = {
    "an:14:1353": (
        "la motion de rejet préalable, déposée par M. Bruno Le Roux, de la "
        "proposition de loi visant à garantir un accès aux soins égal sur "
        "l'ensemble du territoire (première lecture)."
    ),
    "an:17:7003": (
        "l'article unique de la proposition de loi visant à étendre à toutes les "
        "communes la compensation financière prévue pour les communes de plus de "
        "3 500 habitants pour l'exercice de l'ensemble des compétences du service "
        "public de la petite enfance (première lecture)."
    ),
    "an:17:915": (
        "l'amendement n° 5 de M. de Lépinau à l'article premier de la proposition "
        "de loi visant à instaurer un dispositif de sanction contraventionnelle "
        "pour prévenir le développement des vignes non cultivées qui représentent "
        "une menace sanitaire pour l'ensemble du vignoble français (première "
        "lecture)."
    ),
    "an:17:916": (
        "l'amendement n° 6 de M. Fugit et l'amendement identique suivant à "
        "l'article premier de la proposition de loi visant à instaurer un "
        "dispositif de sanction contraventionnelle pour prévenir le développement "
        "des vignes non cultivées qui représentent une menace sanitaire pour "
        "l'ensemble du vignoble français (première lecture)."
    ),
    "an:17:917": (
        "l'article premier de la proposition de loi visant à instaurer un "
        "dispositif de sanction contraventionnelle pour prévenir le développement "
        "des vignes non cultivées qui représentent une menace sanitaire pour "
        "l'ensemble du vignoble français (première lecture)."
    ),
}

#: Les 8 scrutins que l'ancrage seul laisse passer : ils commencent bien par
#: « l'ensemble », mais leur objet est une SOUS-PARTIE du texte — 5 votes sur un
#: article, 3 sur une partie de budget dont un scrutin SOLENNEL. Les publier
#: comme des votes sur un texte entier serait exactement le contresens que
#: l'ancrage vient de fermer. L'issue #672 ne les avait pas relevés.
SOUS_PARTIES_ANCREES = {
    "an:14:1224": (
        "l'ensemble de l'article Premier du projet de loi constitutionnelle de "
        "protection de la Nation (première lecture)."
    ),
    "an:14:1236": (
        "l'ensemble de l'article premier du projet de loi constitutionnelle de "
        "protection de la Nation (seconde délibération) (première lecture)."
    ),
    "an:14:663": (
        "l'ensemble de la première partie du projet de loi de finances pour 2014."
    ),
    "an:14:875": (
        "l'ensemble de l'article 5 bis du projet de loi de finances rectificative "
        "pour 2014 (nouvelle lecture)."
    ),
    "an:14:886": (
        "l'ensemble de l'article premier du projet de loi relatif à la "
        "délimitation des régions, aux élections régionales et départementales et "
        "modifiant le calendrier électoral"
    ),
    "an:14:891": (
        "l'ensemble de l'article 3 du projet de loi relatif à la délimitation des "
        "régions, aux élections régionales et départementales et modifiant le "
        "calendrier électoral"
    ),
    "an:17:242": (
        "l'ensemble de la deuxième partie du projet de loi de financement de la "
        "sécurité sociale pour 2025 (première lecture)."
    ),
    "an:17:445": (
        "l'ensemble de la première partie du projet de loi de finances de fin des "
        "gestion pour 2024 (première lecture)."
    ),
}

#: Les libellés qui DOIVENT être retenus. `an:14:1189` est la forme dominante ;
#: `an:14:32` est le SEUL scrutin sur 17 748 dont l'intitulé commence par « sur
#: l'ensemble », un vote solennel qu'un ancrage strict écartait ; `an:16:1410`
#: et `an:16:1778` portent l'apostrophe typographique, celle des 884 scrutins
#: des législatures 16 et 17 sur lesquels le motif ASCII décrochait ;
#: `an:16:3407` vérifie qu'un objet inhabituel — une proposition européenne —
#: reste retenu, parce que la règle porte sur la locution, pas sur une liste
#: fermée de types de texte.
VRAIS_VOTES_SUR_ENSEMBLE = {
    "an:14:1189": (
        "l'ensemble du projet de loi de finances pour 2016 (première lecture)."
    ),
    "an:14:32": (
        "sur l'ensemble du projet de loi organique relatif à la programmation et "
        "à la gouvernance des finances publiques."
    ),
    "an:16:1410": (
        "l\u2019ensemble de la proposition de loi portant fusion des filières à "
        "responsabilité élargie des producteurs d\u2019emballages ménagers et des "
        "producteurs de papier (texte de la commission mixte paritaire)."
    ),
    "an:16:1778": (
        "l\u2019ensemble du projet de loi relatif à la programmation militaire pour "
        "les années 2024 à 2030 et portant diverses dispositions intéressant la "
        "défense (première lecture)."
    ),
    "an:16:3407": (
        "l'ensemble de la proposition européenne relative à l'adoption d'une loi "
        "européenne sur l'espace."
    ),
}


def sans_commentaires(source: str) -> str:
    """Le code exécuté seul : ni `/* … */`, ni `// …`.

    Indispensable ici : les commentaires de `utils/lecture.js` CITENT les faux
    positifs, ligne par ligne. Un test qui lirait le fichier brut passerait sur
    la documentation du défaut au lieu de la règle qui le ferme.
    """
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"(?<!:)//[^\n]*", "", source)


@pytest.fixture(scope="module")
def regles() -> str:
    return sans_commentaires(MODULE_REGLES.read_text(encoding="utf-8"))


def _motif(regles: str, nom: str) -> re.Pattern[str]:
    """Compile en Python le littéral d'expression régulière déclaré en JS.

    Les deux motifs de #672 n'emploient que de la syntaxe commune aux deux
    langages — ancrage, groupe non capturant, classe de caractères, `\\b`. Les
    exécuter ici est donc légitime, et c'est le seul moyen de tester un
    COMPORTEMENT sans runner JS.
    """
    trouve = re.search(rf"{nom}\s*=\s*\n?\s*/(.+)/;", regles)
    assert trouve, f"`{nom}` n'est plus déclaré dans utils/lecture.js"
    return re.compile(trouve.group(1))


def _corps(regles: str, signature: str) -> str:
    trouve = re.search(rf"function {signature}\s*\{{(.*?)\n\}}", regles, flags=re.DOTALL)
    assert trouve, f"`{signature}` a disparu de utils/lecture.js"
    return trouve.group(1)


@pytest.fixture(scope="module")
def selectionne(regles):
    """Rejoue en Python ce que `isWholeTextVote` fait en JS.

    Le rejeu est DÉRIVÉ de la source, jamais réécrit à côté d'elle : chaque
    étape n'est appliquée que si le corps JS l'applique vraiment. C'est ce qui
    fait qu'une étape retirée du module fait échouer un test de comportement,
    et pas seulement un test de forme — une réécriture indépendante passerait
    au vert sur un module amputé.

    Deux pièges de traduction, tous deux vérifiés par mutation le 31/08/2026 :

      - `re.match` ancre implicitement en tête, `RegExp.prototype.test` non.
        Le rejeu emploie donc `re.search` : c'est le `^` du littéral JS qui
        ancre, exactement comme dans le navigateur. Avec `re.match`, un motif
        redevenu sous-chaîne passait tous les faux positifs au vert.
      - une normalisation recopiée à la main dans le test survit à sa
        suppression dans le module. Elle est donc lue, pas recopiée.
    """
    ancre = _motif(regles, "WHOLE_TEXT_VOTE_PATTERN")
    sous_partie = _motif(regles, "SUBPART_VOTE_PATTERN")

    corps_normalisation = _corps(regles, r"normalizeLabel\(texte\)")
    corps_selection = _corps(regles, r"isWholeTextVote\(scrutin\)")

    applique_nfc = "normalize('NFC')" in corps_normalisation
    applique_apostrophes = "APOSTROPHES" in corps_normalisation
    applique_espaces = re.search(r"\\s\+", corps_normalisation) is not None
    applique_casse = "toLowerCase()" in corps_normalisation

    normalise_avant_comparaison = "normalizeLabel(" in corps_selection
    exclut_sous_parties = "SUBPART_VOTE_PATTERN" in corps_selection
    filtre_type_vote = "type_vote" in corps_selection

    def _selectionne(texte: str, type_vote: str = "vote_texte") -> bool:
        if filtre_type_vote and type_vote != "vote_texte":
            return False

        libelle = texte
        if normalise_avant_comparaison:
            if applique_nfc:
                libelle = unicodedata.normalize("NFC", libelle)
            if applique_apostrophes:
                libelle = re.sub(r"[’ʼʹ′]", "'", libelle)
            if applique_espaces:
                libelle = re.sub(r"\s+", " ", libelle).strip()
            if applique_casse:
                libelle = libelle.lower()

        if not ancre.search(libelle):
            return False
        return not (exclut_sous_parties and sous_partie.search(libelle))

    return _selectionne


def test_la_regle_est_ecrite_dans_le_module_partage(regles):
    """Une seule fois, dans `utils/lecture.js` — pas cinq fois dans cinq vues."""
    for symbole in (
        "normalizeLabel",
        "WHOLE_TEXT_VOTE_PATTERN",
        "SUBPART_VOTE_PATTERN",
        "isWholeTextVote",
        "selectWholeTextVotes",
        "WHOLE_TEXT_VOTE_BOUND",
    ):
        assert f"export const {symbole}" in regles or f"export function {symbole}" in regles, (
            f"`{symbole}` doit être exporté par utils/lecture.js : la règle de "
            "#672 est écrite une seule fois, et les cinq vues l'appellent"
        )


def test_le_motif_est_ancre_en_tete_jamais_une_sous_chaine(regles):
    """L'ancrage est ce qui écarte les 4 faux positifs « article » et « amendement »."""
    littéral = re.search(r"WHOLE_TEXT_VOTE_PATTERN\s*=\s*/(.+)/;", regles)
    assert littéral, "`WHOLE_TEXT_VOTE_PATTERN` a disparu"
    assert littéral.group(1).startswith("^"), (
        "le motif doit être ANCRÉ EN TÊTE de libellé. Sans l'ancrage il capture "
        "6 scrutins de plus, dont 2 votes sur un amendement, 2 sur un article et "
        "une motion de rejet préalable — soit une position publiée que la "
        "personne n'a pas prise (AGENTS.md §2 règle 2 et règle 4)"
    )
    assert re.search(r"\.(includes|indexOf|search)\(", regles) is None, (
        "aucune recherche en sous-chaîne dans le module : c'est le défaut que "
        "#672 ferme"
    )


def test_la_comparaison_normalise_l_apostrophe(regles):
    """884 scrutins des législatures 16 et 17 portent l'apostrophe typographique."""
    corps = re.search(r"function normalizeLabel\(texte\)\s*\{(.*?)\n\}", regles, flags=re.DOTALL)
    assert corps, "`normalizeLabel` a disparu : c'est lui qui porte la normalisation"

    assert "normalize('NFC')" in corps.group(1), (
        "la normalisation Unicode NFC vient AVANT toute comparaison : un « é » "
        "composé et un « e » + accent combinant sont le même caractère pour un "
        "lecteur, pas pour une comparaison de chaînes"
    )
    assert "’" in regles, (
        "l'apostrophe typographique doit être ramenée sur l'ASCII avant "
        "comparaison — c'est elle qui faisait décrocher 22 scrutins des "
        "législatures 16 et 17, les deux plus récentes"
    )


def test_la_moitie_sourcee_de_la_regle_ecarte_les_motions_de_censure(regles):
    """`type_vote` vient de `typeVote.codeTypeVote` (#639) : il ne rouille pas."""
    corps = re.search(r"function isWholeTextVote\(scrutin\)\s*\{(.*?)\n\}", regles, flags=re.DOTALL)
    assert corps, "`isWholeTextVote` a disparu"

    assert "type_vote !== 'vote_texte'" in corps.group(1), (
        "la règle s'appuie d'abord sur `type_vote`, un champ SOURCÉ : il écarte "
        "les 66 motions de censure des 17 748 scrutins publiés, qui sont des "
        "faits de procédure et jamais des positions sur un texte (§2 règle 4)"
    )
    assert "normalizeLabel(" in corps.group(1), (
        "le libellé est normalisé AVANT d'être comparé, jamais comparé brut"
    )


@pytest.mark.parametrize("cas", sorted(FAUX_POSITIFS_SOUS_CHAINE), ids=lambda c: c)
def test_les_cinq_faux_positifs_de_la_sous_chaine_sont_ecartes(selectionne, cas):
    """Un vote inventé est une affirmation ; un vote manqué n'est qu'un vide."""
    texte = FAUX_POSITIFS_SOUS_CHAINE[cas]
    assert "l'ensemble" in texte.lower(), (
        f"le libellé de contrôle « {cas} » doit bien porter la locution : c'est "
        "ce qui en fait un faux positif de la recherche en sous-chaîne"
    )
    assert not selectionne(texte), (
        f"« {cas} » ne porte PAS sur l'ensemble d'un texte et ne doit pas être "
        f"retenu : {texte[:80]}…"
    )


@pytest.mark.parametrize("scrutin_id", sorted(SOUS_PARTIES_ANCREES), ids=lambda i: i)
def test_les_huit_votes_sur_une_sous_partie_sont_ecartes(selectionne, scrutin_id):
    """L'ancrage seul ne suffit pas : 8 des 933 ancrés portent sur un article
    ou sur une partie de budget."""
    texte = SOUS_PARTIES_ANCREES[scrutin_id]
    assert texte.lower().startswith("l'ensemble"), (
        f"le libellé de contrôle {scrutin_id} doit commencer par la locution : "
        "c'est ce qui en fait un cas que l'ancrage ne rattrape pas"
    )
    assert not selectionne(texte), (
        f"{scrutin_id} porte sur une sous-partie du texte, pas sur son ensemble, "
        f"et ne doit pas être retenu : {texte[:80]}…"
    )


@pytest.mark.parametrize("cas", sorted(VRAIS_VOTES_SUR_ENSEMBLE), ids=lambda c: c)
def test_les_vrais_votes_sur_l_ensemble_sont_retenus(selectionne, cas):
    """Dont le « sur » initial et l'apostrophe typographique, les deux pièges."""
    assert selectionne(VRAIS_VOTES_SUR_ENSEMBLE[cas]), (
        f"« {cas} » est un vote sur l'ensemble d'un texte et doit être retenu : "
        f"{VRAIS_VOTES_SUR_ENSEMBLE[cas][:80]}…"
    )


def test_une_motion_de_censure_n_est_jamais_un_vote_sur_un_texte(selectionne):
    """§2 règle 4 : un fait de procédure n'est jamais une position de vote.

    Le libellé ne suffirait pas — c'est `type_vote`, champ sourcé (#639), qui
    écarte les 66 motions de censure des 17 748 scrutins publiés.
    """
    libelle = VRAIS_VOTES_SUR_ENSEMBLE["an:14:1189"]
    assert selectionne(libelle, type_vote="vote_texte")
    assert not selectionne(libelle, type_vote="motion_censure"), (
        "un scrutin qualifié `motion_censure` ne doit jamais être retenu comme "
        "un vote sur l'ensemble d'un texte, quel que soit son libellé "
        "(AGENTS.md §2 règle 4)"
    )
    assert not selectionne(libelle, type_vote=None), (
        "un `type_vote` absent ne devient pas `vote_texte` par défaut : sans le "
        "champ on ne sait pas, et §2 règle 5 interdit de combler"
    )


def test_un_type_vote_absent_ne_devient_jamais_vote_texte(regles):
    """Sans le champ on ne sait pas, et §2 règle 5 interdit de combler."""
    corps = re.search(r"function isWholeTextVote\(scrutin\)\s*\{(.*?)\n\}", regles, flags=re.DOTALL)
    assert corps, "`isWholeTextVote` a disparu"
    assert not re.search(r"type_vote\s*(\?\?|\|\|)", corps.group(1)), (
        "un `type_vote` absent ne prend aucune valeur par défaut : il fait "
        "répondre `false`, pas `vote_texte` (AGENTS.md §2 règle 5)"
    )


def test_la_borne_est_publiee_et_dit_plancher(regles):
    """`SPO` couvre l'ensemble, l'article et l'amendement : le compte est un
    plancher, et la page doit le dire (§2 règle 5)."""
    bloc = re.search(r"WHOLE_TEXT_VOTE_BOUND\s*=\s*\{(.*?)\n\};", regles, flags=re.DOTALL)
    assert bloc, "`WHOLE_TEXT_VOTE_BOUND` a disparu : la borne est du texte publié"

    texte = bloc.group(1)
    assert "plancher" in texte, (
        "la borne doit dire que le décompte est un PLANCHER : tant que le code "
        "de scrutin ne distingue pas l'ensemble de l'article, la sélection reste "
        "approchée et la page ne peut pas la présenter comme exhaustive"
    )
    assert "exhaustif" in texte, (
        "la borne doit refuser explicitement l'exhaustivité, pas seulement la "
        "nuancer"
    )
    for cle in ("phrase:", "pourquoi:"):
        assert cle in texte, (
            f"la borne porte `{cle}` comme les refus déclarés du lot 1 : la "
            "phrase est ce que le lecteur voit, le pourquoi ce qu'il peut vérifier"
        )


def test_aucune_vue_ne_reecrit_le_motif():
    """Cinq vues appliquent la règle ; aucune ne la redéfinit (le défaut #326)."""
    fautifs = []
    for chemin in sorted(UI.rglob("*.js")) + sorted(UI.rglob("*.jsx")):
        if chemin == MODULE_REGLES:
            continue
        source = sans_commentaires(chemin.read_text(encoding="utf-8"))
        if re.search(r"\.(includes|indexOf|match|test|search)\([^)]*ensemble", source):
            fautifs.append(f"{chemin.relative_to(UI)} : recherche sur « ensemble »")
        if re.search(r"/[^/\n]*ensemble[^/\n]*/[gimsuy]*", source):
            fautifs.append(f"{chemin.relative_to(UI)} : motif littéral sur « ensemble »")

    assert not fautifs, (
        "la règle de #672 s'importe de `utils/lecture.js`, elle ne se réécrit "
        f"pas : {fautifs}"
    )
