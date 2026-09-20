"""Les arbitrages du lot 1 (#326) sont verrouillés dans le code exécuté.

Trois décisions ont été rendues le 31/08/2026 sur le rendu d'écran soumis avant
implémentation. Chacune est le genre de choix qu'une session suivante défait
sans s'en apercevoir, parce qu'elle a l'air d'un détail de style :

  1. « Absent » n'est PAS une catégorie de vote — elle n'apparaît dans aucune
     des 1 312 951 positions publiées, et publier une absence comme un fait de
     vote serait le taux de présence individuel qu'interdit AGENTS.md §2
     règle 3.
  2. `non_votant` se distingue par la FORME, jamais par une teinte : c'est ce
     qui empêche les quatre valeurs de se lire comme un dégradé du meilleur au
     pire (§2 règle 1).
  3. Le badge dit « Lien de source non publié », jamais « non vérifié » : le
     premier parle de nous, le second ferait porter le doute sur les 484 132
     amendements, qui viennent tous de l'open data de l'Assemblée nationale.

Ces tests lisent le **code exécuté** — les commentaires sont retirés avant
toute assertion. Un commentaire qui parle d'« absent » ne doit pas faire passer
un test qui vérifie que la catégorie n'existe pas, ni en faire échouer un.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale" / "src"

MODULE_REGLES = UI / "utils" / "lecture.js"
COMPOSANTS_LECTURE = UI / "components" / "Lecture.jsx"

#: Les deux composants qui portaient chacun leur copie de `VOTE_STYLE`, sans
#: `non_votant` — le « risque de divergence silencieuse » que le DESIGN_SYSTEM §2
#: signalait, et que ce lot ferme.
COMPOSANTS_HISTORIQUES = (
    UI / "components" / "CandidateProfile.jsx",
    # `GroupProfile.jsx` a laissé la place à la fiche de lignée (#329) : la
    # garde suit la page de groupe, pas le nom de fichier.
    UI / "components" / "LigneeProfile.jsx",
)

#: Les couleurs des positions EXPRIMÉES, telles que le DESIGN_SYSTEM les fixe.
COULEURS_POSITIONS_EXPRIMEES = {
    "pour": "#007A45",
    "contre": "#E53420",
    "abstention": "#8B8794",
}

#: Les quatre valeurs que prennent les 1 312 951 positions publiées, mesurées au
#: commit de données `245511b4` le 31/08/2026.
POSITIONS_PUBLIEES = frozenset({"pour", "contre", "abstention", "non_votant"})


def sans_commentaires(source: str) -> str:
    """Le code exécuté seul : ni `/* … */`, ni `// …`.

    Le retrait de `//` épargne les `://` (une URL n'est pas un commentaire),
    parce que les composants du site en portent.
    """
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"(?<!:)//[^\n]*", "", source)


@pytest.fixture(scope="module")
def regles() -> str:
    return sans_commentaires(MODULE_REGLES.read_text(encoding="utf-8"))


def _bloc_vote_style(regles: str) -> str:
    trouve = re.search(r"VOTE_STYLE\s*=\s*\{(.*?)\n\};", regles, flags=re.DOTALL)
    assert trouve, "`VOTE_STYLE` n'est plus déclaré dans utils/lecture.js"
    return trouve.group(1)


def test_le_module_des_regles_existe():
    """Un module unique : six règles réécrites trois fois divergent trois fois."""
    assert MODULE_REGLES.is_file(), f"{MODULE_REGLES} est attendu par #326"
    assert COMPOSANTS_LECTURE.is_file(), f"{COMPOSANTS_LECTURE} est attendu par #326"


def test_les_positions_declarees_sont_exactement_celles_qui_sont_publiees(regles):
    """Quatre valeurs, pas cinq — et pas trois non plus.

    Trois, c'est l'état d'avant ce lot : `non_votant` tombait sur `undefined`,
    et ses 21 229 entrées s'affichaient sans couleur ni libellé.
    """
    declarees = set(re.findall(r"^\s{2}(\w+):", _bloc_vote_style(regles), flags=re.M))
    assert declarees == set(POSITIONS_PUBLIEES), (
        "`VOTE_STYLE` doit déclarer exactement les quatre positions publiées "
        f"({sorted(POSITIONS_PUBLIEES)}), pas {sorted(declarees)}"
    )


def test_absent_n_est_pas_une_categorie_de_vote(regles):
    """Publier une absence comme un fait de vote est un taux de présence (§2 règle 3)."""
    assert "absent" not in _bloc_vote_style(regles), (
        "« absent » ne doit pas être une catégorie de vote : elle n'apparaît dans "
        "aucune des 1 312 951 positions publiées, et la publier comme telle "
        "reviendrait à publier un taux de présence individuel (AGENTS.md §2 règle 3)"
    )


def test_les_positions_exprimees_gardent_les_couleurs_du_design_system(regles):
    bloc = _bloc_vote_style(regles)
    for position, hexa in COULEURS_POSITIONS_EXPRIMEES.items():
        ligne = re.search(rf"^\s*{position}:\s*\{{(.*)\}},?$", bloc, flags=re.M)
        assert ligne, f"la position `{position}` a disparu de `VOTE_STYLE`"
        assert hexa in ligne.group(1), (
            f"`{position}` doit garder {hexa}, la valeur du DESIGN_SYSTEM §2"
        )


def test_non_votant_ne_porte_aucune_couleur(regles):
    """La forme, jamais la teinte — sinon les quatre valeurs font une échelle."""
    ligne = re.search(r"^\s*non_votant:\s*\{(.*)\},?$", _bloc_vote_style(regles), flags=re.M)
    assert ligne, "`non_votant` a disparu de `VOTE_STYLE`"

    corps = ligne.group(1)
    assert "color: null" in corps, (
        "`non_votant` n'est pas une position exprimée : elle ne porte aucune "
        "couleur. Lui en donner une la placerait sur la même échelle que Pour, "
        "Contre et Abstention, ce qui fabrique un jugement (AGENTS.md §2 règle 1)"
    )
    assert not re.search(r"#[0-9A-Fa-f]{3,8}", corps), (
        f"`non_votant` ne doit porter aucune valeur de couleur : {corps.strip()}"
    )
    assert "outlined: true" in corps, (
        "`non_votant` se distingue par la forme : `outlined: true` est ce que le "
        "rendu lit pour tracer le contour tireté"
    )


def test_une_position_inconnue_tombe_sur_la_forme_jamais_sur_une_couleur(regles):
    """`absent`, si la source en produisait une un jour, ne prend pas de teinte."""
    repli = re.search(r"styleForPosition\(position\)\s*\{(.*?)\n\}", regles, flags=re.DOTALL)
    assert repli, "`styleForPosition` a disparu : c'est lui qui porte le repli"

    corps = repli.group(1)
    assert "color: null" in corps and "outlined: true" in corps, (
        "le repli d'une position inconnue doit être sans couleur et à contour "
        f"tireté, jamais une teinte : {corps.strip()}"
    )
    assert not re.search(r"#[0-9A-Fa-f]{3,8}", corps), (
        "le repli ne doit contenir aucune valeur de couleur"
    )


def test_le_badge_parle_de_nous_pas_de_la_donnee(regles):
    """« Lien de source non publié » et jamais « non vérifié »."""
    assert "'Lien de source non publié'" in regles, (
        "le libellé du badge absent doit rester « Lien de source non publié » : "
        "il dit que NOUS ne publions pas encore l'adresse"
    )
    assert "non vérifié" not in regles.lower().replace("non vérifiée", ""), (
        "« non vérifié » ferait porter le doute sur les 484 132 amendements "
        "eux-mêmes, qui viennent tous de l'open data de l'Assemblée nationale "
        "(AGENTS.md §2 règle 2)"
    )


def test_les_quatre_causes_de_liste_vide_disent_chacune_autre_chose(regles):
    """Les confondre publierait un zéro là où rien n'a été collecté (§2 règle 5)."""
    bloc = re.search(r"EMPTY_LIST_CAUSES\s*=\s*\{(.*?)\n\};", regles, flags=re.DOTALL)
    assert bloc, "`EMPTY_LIST_CAUSES` a disparu"

    attendues = {"couvert", "fait_etabli", "hors_couverture", "non_collecte"}
    declarees = set(re.findall(r"^\s{2}(\w+):\s*\{", bloc.group(1), flags=re.M))
    assert declarees == attendues, (
        "les quatre états du bloc `couverture` (#539) doivent être couverts un "
        f"par un : {sorted(attendues)}, pas {sorted(declarees)}"
    )

    phrases = re.findall(r"defaut:\s*\n?\s*['\"](.+?)['\"],", bloc.group(1), flags=re.DOTALL)
    assert len(phrases) == len(attendues), (
        "chaque cause porte sa propre phrase par défaut"
    )
    assert len(set(phrases)) == len(phrases), (
        "deux causes partagent la même phrase : elles n'affirment pourtant pas "
        "la même chose — un fait établi parle de la personne, un hors-couverture "
        "parle de la source"
    )


@pytest.mark.parametrize("chemin", COMPOSANTS_HISTORIQUES, ids=lambda p: p.name)
def test_les_couleurs_de_vote_ne_sont_plus_dupliquees(chemin):
    """Le DESIGN_SYSTEM §2 signalait « aucun partage de source actuellement »."""
    source = sans_commentaires(chemin.read_text(encoding="utf-8"))

    for constante in ("VOTE_STYLE", "OUTCOME_COLOR"):
        assert not re.search(rf"const\s+{constante}\s*=", source), (
            f"{chemin.name} redéclare `{constante}` au lieu de l'importer de "
            "`utils/lecture.js` : c'est la divergence silencieuse que #326 ferme"
        )

    assert "utils/lecture" in source, (
        f"{chemin.name} doit lire les couleurs de vote du module partagé"
    )
