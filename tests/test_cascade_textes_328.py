"""La cascade des textes portés ne publie pas de sort, et ne filtre rien (#328).

La section « Ce qu'il a proposé » s'aligne sur la maquette validée le
06/09/2026 : la cascade procédurale remplace la barre segmentée des textes
portés, et l'ordre des cartes suit les deux populations — les textes dont il est
auteur ou rapporteur d'abord, les amendements déposés sur les textes des autres
ensuite.

Ce que ces garde-fous protègent est éditorial, pas graphique. Une session
suivante qui « améliore » les libellés de la figure a toutes les chances
d'écrire « rejeté » sous la branche basse : c'est le mot que le lecteur attend,
et c'est précisément celui que la source n'établit pas. `_STADE_RANKS` et
`KNOWN_STADES_PROCEDURAUX` ne connaissent que des valeurs CROISSANTES, dont
l'absence du cran suivant est un fait à la date du corpus — pas une issue
(§2 règles 2 et 5).

CE QU'ILS NE COUVRENT PAS, et il faut le dire (§2 règle 5) : comme
`test_essentiel_328.py`, ils ne rendent aucun composant React et n'exécutent pas
d3-sankey. La géométrie — conservation des textes, branche basse plus fin de
course égale le total, aucun chemin `NaN`, contiguïté des barres — a été
vérifiée hors dépôt sur les **13 candidats** à quatre largeurs, et
l'interaction en navigateur (clic ruban, clic étiquette, remise à zéro, mobile)
sur cinq profils. Rien de tout cela n'est rejoué ici.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale" / "src"

MODULE_CASCADE = UI / "utils" / "cascadeTextes.js"
MODULE_REGLES = UI / "utils" / "profilCandidat.js"
COMPOSANT = UI / "components" / "CandidateProfile.jsx"


def sans_commentaires(source: str) -> str:
    """Le code exécuté seul : ni `/* … */`, ni `// …`.

    Indispensable ici : l'en-tête du module EXPLIQUE pourquoi « rejeté » est
    interdit, et un test qui cherche le mot dans tout le fichier échouerait sur
    la phrase qui le proscrit.
    """
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"(?<!:)//[^\n]*", "", source)


@pytest.fixture(scope="module")
def cascade() -> str:
    return sans_commentaires(MODULE_CASCADE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def regles() -> str:
    return sans_commentaires(MODULE_REGLES.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def composant() -> str:
    return sans_commentaires(COMPOSANT.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# 1. La branche basse constate une absence, elle ne publie pas un sort
# ---------------------------------------------------------------------------

INTERDITS = ("rejeté", "rejete", "abandonné", "abandonne", "échec", "echec", "retiré")


def test_la_branche_basse_ne_nomme_aucun_sort(cascade, composant):
    """« non adopté » constate ; « rejeté » invente (§2 règle 5)."""
    for mot in INTERDITS:
        assert mot not in cascade.lower(), (
            f"« {mot} » est apparu dans la mise en page de la cascade : la source "
            "ne publie pas le sort d'un texte porté, seulement l'étape la plus "
            "avancée qu'il a atteinte"
        )


def test_la_negation_se_derive_du_cran_suivant(cascade):
    """Elle n'est pas écrite en dur : « non » + le libellé de l'étape suivante.

    C'est ce qui fait que l'échelle peut gagner un cran sans qu'une chaîne
    devienne fausse en silence.
    """
    assert "`non ${nom(i + 1)}`" in cascade, (
        "la négation de la branche basse doit se composer sur le libellé du cran "
        "SUIVANT, jamais être une constante"
    )


def test_les_mots_courts_sont_indexes_par_cle_de_stade(cascade):
    """Deux tables, pas deux tableaux parallèles.

    Des tableaux indexés par position se décalent en silence le jour où
    l'échelle gagne un cran — et elle peut en gagner un.
    """
    for table in ("MOT_COURT_STADE", "NEGATION_STADE"):
        bloc = re.search(rf"export const {table} = \{{(.*?)\}};", cascade, re.DOTALL)
        assert bloc, f"`{table}` n'est plus une table exportée"
        assert "examine_commission" in bloc.group(1) or "adopte" in bloc.group(1), (
            f"`{table}` doit être indexée par CLÉ de stade, pas par position"
        )


# ---------------------------------------------------------------------------
# 2. Aucun seuil : un fait n'a pas de taille minimale
# ---------------------------------------------------------------------------

def test_aucun_flux_n_est_ecarte_pour_sa_petitesse(cascade):
    """Du plus gros ruban au trait d'un seul texte, tous sont tracés.

    Un seuil arbitraire qui déciderait qu'un fait existe est exactement ce que
    §2 règle 1 interdit. Les seules bornes admises portent sur la LISIBILITÉ
    d'un trait déjà tracé (`Math.max(l.width, 1)`), jamais sur son existence.
    """
    for garde in ("Math.max(l.width, 1)", "Math.max(seg.h, 1.2)"):
        assert garde in cascade, (
            "la borne de lisibilité d'un trait a disparu : un ruban d'un seul "
            "texte doit rester visible, donc tracé à au moins un pixel"
        )
    assert not re.search(r"filter\(\s*\(\w+\)\s*=>\s*\w+(\.value|\[2\])\s*[><]=?\s*[1-9]", cascade), (
        "un filtre sur la VALEUR d'un flux est apparu : aucun seuil ne décide "
        "qu'un texte porté existe"
    )


# ---------------------------------------------------------------------------
# 3. La matière : une absence reste une absence
# ---------------------------------------------------------------------------

def test_un_texte_sans_commission_tombe_sous_matiere_non_etablie(regles):
    """Jamais réparti au prorata, jamais déduit de l'intitulé (§2 règle 5)."""
    bloc = re.search(r"function cascadeDesTextes\((.*?)\n\}", regles, re.DOTALL)
    assert bloc, "`cascadeDesTextes` n'est plus déclarée"
    corps = bloc.group(1)
    assert "MATIERE_NON_ETABLIE" in corps, (
        "l'absence de commission saisie au fond doit tomber dans une catégorie "
        "NOMMÉE, comptée et déclarée — pas être répartie ni devinée"
    )
    assert "titre" not in re.sub(r"titre: t\.titre,", "", corps), (
        "la matière ne se déduit jamais de l'intitulé du texte"
    )


def test_la_cascade_lit_la_meme_table_de_commissions_que_la_chute(regles):
    """Les deux figures de la section doivent colorier pareil.

    Deux résolutions de matière produiraient deux ordres, donc deux palettes, et
    la section se lirait comme deux sections.

    RÉÉCRIT LE 16/09/2026, ET CE QU'IL TENAIT. Il exigeait la chaîne
    `export function textesPortes(textes, commissionDuDossier` — la signature
    exacte, sur une ligne. Le versant européen lui a ajouté un troisième
    paramètre (`dossierEuropeen`, #901), la signature est passée sur plusieurs
    lignes, et le test a rougi sans qu'aucune des deux figures ait changé de
    table. Il vérifie donc l'INTENTION : le paramètre existe, et l'adaptateur
    passe le même résolveur aux deux figures.
    """
    signature = re.search(
        r"export function textesPortes\(([^)]*)\)", regles, re.DOTALL,
    )
    assert signature, "`textesPortes` doit rester une fonction exportée"
    assert "commissionDuDossier" in signature.group(1), (
        "`textesPortes` doit recevoir le MÊME résolveur de commission que "
        "`agregerAmendements`"
    )
    adaptateur = (UI / "data" / "pivotAdapter.js").read_text(
        encoding="utf-8",
    )
    assert "agregerAmendements(" in adaptateur and "textesPortes(" in adaptateur
    for appel in ("agregerAmendements", "textesPortes"):
        bloc = re.search(rf"{appel}\((.*?)\);", adaptateur, re.DOTALL).group(1)
        assert "commissionDuDossier" in bloc, (
            f"`{appel}` doit recevoir `commissionDuDossier`, sans quoi les deux "
            "figures de la section coloriraient différemment"
        )


def test_la_teinte_vient_de_la_palette_partagee(composant):
    """Une seconde palette dans le composant ferait diverger les deux figures."""
    assert "teinteMatiere" in composant, "la cascade doit teinter par `teinteMatiere`"
    assert not re.search(r"const PALETTE\w* = \[", composant), (
        "une palette de matières a été redéclarée dans le composant : elle vit "
        "dans `utils/matiere.js`, et nulle part ailleurs"
    )


# ---------------------------------------------------------------------------
# 4. L'échelle des crans est celle que le corpus remplit
# ---------------------------------------------------------------------------

def test_un_cran_n_existe_que_si_un_texte_s_y_arrete(regles):
    """La règle est générale, pas une exception codée en dur sur un stade.

    `inscrit_ordre_jour` n'est porté par aucun des 423 textes des 13 candidats
    déclarés. L'écarter NOMMÉMENT ferait disparaître un texte le jour où il en
    portera un ; le déduire des arrêts le fait apparaître tout seul.
    """
    bloc = re.search(r"function cascadeDesTextes\((.*?)\n\}", regles, re.DOTALL)
    corps = bloc.group(1)
    assert "STADES_PUBLIES.filter" in corps, (
        "l'échelle doit se déduire de STADES_PUBLIES par filtrage sur les arrêts"
    )
    assert "inscrit_ordre_jour" not in corps, (
        "un stade est écarté nommément : la règle doit porter sur le CORPUS "
        "(aucun texte ne s'y arrête), jamais sur le nom du cran"
    )


# ---------------------------------------------------------------------------
# 5. L'ordre de la section suit les deux populations
# ---------------------------------------------------------------------------

def test_les_textes_portes_viennent_avant_les_amendements(composant):
    """Les textes dont il est l'auteur, puis les amendements sur ceux des autres.

    Deux populations distinctes, jamais additionnées, et la première éclaire la
    seconde.
    """
    bloc = re.search(r"function Propositions\((.*?)\n\}\n", composant, re.DOTALL)
    assert bloc, "`Propositions` n'est plus déclarée"
    corps = bloc.group(1)
    # L'ancrage est STRUCTUREL, pas sur le libellé : les titres de carte sont
    # de la copie et ils changent (« Où en sont les textes… » est devenu « Les
    # textes qu'il a portés » le 07/09). Un test calé sur une phrase casse au
    # premier mot réécrit et ne dit rien de l'ordre qu'il prétend garder.
    # `<Chute>` — la cascade des amendements par année — est devenue
    # `<Matieres>`, le tableau des deux mesures. L'ancrage reste STRUCTUREL :
    # c'est l'ordre des deux populations qui est gardé, pas le nom du composant.
    place_textes = corps.index("<Cascade")
    place_amdts = corps.index("<Matieres")
    assert place_textes < place_amdts, (
        "la carte des textes portés doit ouvrir la section, avant les "
        "amendements déposés sur les textes des autres"
    )


def test_aucun_rapport_entre_les_deux_populations(composant):
    """Rien n'est additionné ni mis en rapport entre textes portés et amendements.

    Un « N textes pour M amendements » serait un taux que §6 interdit, sur deux
    populations qui n'ont pas le même dénominateur.
    """
    bloc = re.search(r"function Propositions\((.*?)\n\}\n", composant, re.DOTALL)
    corps = bloc.group(1)
    assert not re.search(r"(textes\.\w+\s*/\s*amendements|amendements\.\w+\s*/\s*textes)", corps), (
        "un rapport entre les deux populations est apparu dans la section"
    )
