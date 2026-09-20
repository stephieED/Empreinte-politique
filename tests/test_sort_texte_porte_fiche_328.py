"""Le sort d'un texte porté entre dans la fiche, sans jamais remplacer son stade (#743 / #328).

`textes_portes[].sort` est publié depuis #747. La fiche l'affiche — mais pas
n'importe où, et c'est ce que ces garde-fous protègent.

CE QUI A ÉTÉ DEMANDÉ, ET POURQUOI IL A FALLU LE DÉCALER. La demande était de
« remplacer les labels du sankey » par le sort. Mesuré sur les 13 candidats
déclarés au commit de données `acd7f5b7` : **aucune barre n'est homogène en
sort**. La barre « non adopté » d'Édouard Philippe porte 2 textes en navette,
1 adopté via 49.3 et 1 retiré ; la barre finale « promulgué » de Gabriel Attal
porte 6 adoptés en CMP, 5 adoptés, 4 adoptés via 49.3 et 3 promulgués. Une
étiquette de barre ne peut donc pas nommer un sort sans mentir sur les autres.
La figure garde le STADE pour axe, et le sort vit dans la liste, texte par
texte, où chacun répond de lui-même.

LE 49.3 EST LE CAS QUI RENDAIT LE SILENCE INTENABLE. Cinq textes sur les 414
publiés ont été adoptés sans vote — quatre de Gabriel Attal, fondus dans la
barre « promulgué », et un d'Édouard Philippe, tombé dans une barre « non
adopté » qui le contredisait. `AGENTS.md` §2 règle 4 veut qu'un 49.3 soit un
fait procédural séparé : il est donc compté à part et nommé à côté de la
figure, jamais dedans.

CE QU'ILS NE COUVRENT PAS : ils ne rendent aucun composant React. L'affichage
et l'interaction (ouverture de la liste par le bouton 49.3, juxtaposition des
deux pastilles) ont été vérifiés en navigateur hors dépôt.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale" / "src"

LECTURE = UI / "utils" / "lecture.js"
REGLES = UI / "utils" / "profilCandidat.js"
CASCADE = UI / "utils" / "cascadeTextes.js"
COMPOSANT = UI / "components" / "CandidateProfile.jsx"
#: La cascade et sa liste sont sorties de la fiche candidat pour être partagées
#: avec la fiche de lignée (#329) : la liste se lit là où elle vit.
FIGURE = UI / "components" / "CascadeTextes.jsx"
ADAPTATEUR = UI / "data" / "pivotAdapter.js"
SCHEMA = RACINE / "src" / "schema_pivot.py"


def sans_commentaires(source: str) -> str:
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"(?<!:)//[^\n]*", "", source)


def _cles_js(source: str, nom: str) -> set[str]:
    bloc = re.search(rf"export const {nom} = \{{(.*?)\n\}};", source, re.DOTALL)
    assert bloc, f"`{nom}` n'est plus une table exportée de lecture.js"
    return set(re.findall(r"^\s{2}([a-z0-9_]+):", bloc.group(1), re.M))


def _frozenset_py(source: str, nom: str) -> set[str]:
    bloc = re.search(rf"{nom}: frozenset\[str\] = frozenset\(\{{(.*?)\}}\)", source, re.DOTALL)
    assert bloc, f"`{nom}` n'est plus déclarée dans schema_pivot.py"
    return set(re.findall(r'"([a-z0-9_]+)"', bloc.group(1)))


@pytest.fixture(scope="module")
def lecture() -> str:
    return LECTURE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def composant() -> str:
    return sans_commentaires(
        COMPOSANT.read_text(encoding="utf-8") + "\n" + FIGURE.read_text(encoding="utf-8")
    )


# ---------------------------------------------------------------------------
# 1. Le vocabulaire est celui du schéma, et il n'existe qu'une fois
# ---------------------------------------------------------------------------

def test_les_libelles_couvrent_exactement_le_vocabulaire_du_schema(lecture):
    """Ni plus, ni moins que `KNOWN_SORTS_TEXTE_PORTE`.

    Un sort de plus côté schéma sans libellé s'afficherait en clé technique ;
    un libellé de plus ici décrirait une valeur que la source ne produit pas.
    C'est le seul test du dépôt qui compare ce frozenset Python à sa table JS.
    """
    attendu = _frozenset_py(SCHEMA.read_text(encoding="utf-8"), "KNOWN_SORTS_TEXTE_PORTE")
    obtenu = _cles_js(lecture, "LIBELLE_SORT_TEXTE")
    assert obtenu == attendu, (
        f"la table des libellés a divergé du schéma : en trop {sorted(obtenu - attendu)}, "
        f"manquants {sorted(attendu - obtenu)}"
    )


def test_les_motifs_couvrent_exactement_ceux_du_schema(lecture):
    """Un motif sans libellé s'afficherait en clé technique à la place d'une raison."""
    attendu = _frozenset_py(SCHEMA.read_text(encoding="utf-8"), "KNOWN_MOTIFS_SORT_NON_RESOLU")
    assert _cles_js(lecture, "MOTIF_SORT") == attendu


def test_le_vocabulaire_n_est_declare_qu_une_fois():
    """Il vivait dans `pivotAdapter.js`, au service des seules fiches de gouvernement.

    La fiche candidat le lit maintenant aussi : écrit deux fois, il divergerait.
    """
    adaptateur = sans_commentaires(ADAPTATEUR.read_text(encoding="utf-8"))
    assert "GOVERNMENT_TEXTE_STATUT_LABELS" not in adaptateur, (
        "la table locale de `pivotAdapter.js` est revenue : le vocabulaire vit "
        "dans `utils/lecture.js`, et nulle part ailleurs"
    )
    assert "LIBELLE_SORT_TEXTE" in adaptateur, (
        "la fiche de gouvernement doit lire la table partagée"
    )


# ---------------------------------------------------------------------------
# 2. Le sort n'est pas le stade, et ne s'en déduit jamais
# ---------------------------------------------------------------------------

def test_aucun_sort_n_est_derive_d_un_stade():
    """« Discuté en séance et pas adopté » ne devient « rejeté » nulle part.

    Le stade encode une progression, le sort une issue. Une table qui traduirait
    l'un dans l'autre est exactement ce que §2 règles 2 et 5 interdisent.
    """
    for chemin in (REGLES, CASCADE, COMPOSANT, FIGURE):
        source = sans_commentaires(chemin.read_text(encoding="utf-8"))
        for stade in ("discute_seance", "examine_commission", "adopte", "promulgue"):
            motif = rf"{stade}\s*:\s*'(?:rejete|retire|navette_en_cours|adopte_49_3)"
            assert not re.search(motif, source), (
                f"{chemin.name} : un sort est dérivé du stade `{stade}`"
            )


def test_le_sort_s_affiche_a_cote_du_stade_pas_a_sa_place(composant):
    """Les deux pastilles coexistent dans la même ligne de liste."""
    bloc = re.search(r"export function ListeCascade\((.*?)\n\}\n", composant, re.DOTALL)
    assert bloc, "`ListeCascade` n'est plus déclarée"
    corps = bloc.group(1)
    assert "cp-ter-pastille" in corps, "la pastille de STADE a disparu de la liste"
    assert "cp-ter-sort" in corps, "la mention du SORT n'est pas dans la liste"


def test_un_sort_absent_affiche_son_motif_jamais_un_sort_par_defaut(composant):
    """§2 règle 5 : une absence est un fait, elle ne se comble pas."""
    bloc = re.search(r"export function ListeCascade\((.*?)\n\}\n", composant, re.DOTALL)
    corps = bloc.group(1)
    assert "MOTIF_SORT" in corps and "sortMotif" in corps, (
        "un sort nul doit afficher son motif"
    )
    assert not re.search(r"sortCle\s*\|\|\s*'(?:adopte|navette_en_cours|rejete)", corps), (
        "un sort par défaut est appliqué quand la source n'en donne pas"
    )


# ---------------------------------------------------------------------------
# 3. Le 49.3 est un fait procédural, compté à part
# ---------------------------------------------------------------------------

def test_le_49_3_a_ses_deux_valeurs_et_ne_se_confond_pas_avec_une_adoption(lecture):
    bloc = re.search(r"export const SORTS_PROCEDURE_49_3 = new Set\(\[(.*?)\]\)", lecture, re.DOTALL)
    assert bloc, "`SORTS_PROCEDURE_49_3` n'est plus déclarée"
    valeurs = set(re.findall(r"'([a-z0-9_]+)'", bloc.group(1)))
    assert valeurs == {"adopte_49_3", "rejete_49_3"}, (
        f"le 49.3 doit couvrir ses DEUX issues, adoptée et rejetée — trouvé {sorted(valeurs)}"
    )


def test_le_49_3_est_compte_a_part_et_jamais_fondu(composant):
    """Il est nommé à côté de la figure, parce que la figure ne peut pas le porter.

    Son axe est le stade : les quatre 49.3 de Gabriel Attal s'y rangent dans la
    barre « promulgué », invisibles.
    """
    assert "procedure493" in composant, "le compte des 49.3 n'est plus lu par la vue"
    assert "cp-ter-493" in composant, "la mention nommée du 49.3 a disparu de la section"
    assert re.search(r"fait procédural", composant), (
        "la mention doit dire que c'est un fait procédural, jamais une position de vote "
        "(§2 règle 4)"
    )


def test_le_compte_des_49_3_ne_porte_aucun_taux():
    """Un compte, jamais une part : §6 interdit le taux, ici comme ailleurs."""
    regles = sans_commentaires(REGLES.read_text(encoding="utf-8"))
    bloc = re.search(r"function cascadeDesTextes\((.*?)\n\}", regles, re.DOTALL)
    corps = bloc.group(1)
    assert "procedure493" in corps, "`procedure493` n'est plus calculé"
    assert not re.search(r"procedure493\s*/\s*|/\s*procedure493", corps), (
        "un rapport est calculé sur les 49.3"
    )
