"""« Ce qu'il a dit » publie les mots, rangés par période politique (#328).

La section publiait quatre listes de totaux de carrière — combien
d'interventions, de quelle nature, sous quelle qualité, sur quels sujets de
questions au gouvernement — et un paragraphe de méthode. Elle disait COMMENT ON
SAIT et jamais CE QUI A ÉTÉ DIT, alors que le corpus porte 16 188 verbatims du
compte rendu intégral pour 21 725 interventions collectées (10 des 27 candidats
déclarés).

Elle publie maintenant, dans cet ordre : la période politique, la nature de
l'intervention, le sujet à l'ordre du jour, puis le fil des interventions
elles-mêmes.

CE QUE CES GARDE-FOUS PROTÈGENT est éditorial, pas graphique. Quatre pentes,
toutes tentantes pour une session qui « améliorerait » la vue :

1. **Lire le sujet au même niveau du chemin pour tous les types.** La grammaire
   de l'ordre du jour change avec le type : le sujet d'une question au
   gouvernement est la FEUILLE, celui d'un examen de texte la RACINE. Prendre
   partout le même bout range 2 885 des 3 660 questions sous « Questions au
   Gouvernement », un créneau de séance ; ou bien fait des textes examinés
   autant de « Suspension et reprise de la séance ».
2. **Publier le champ `format`.** « Réaction courte » / « prise de parole
   développée » est NOTRE déduction — un seuil de cinquante mots posé dans
   `src/parse_syceron.py` —, jamais un fait du compte rendu.
3. **Ouvrir le fil par défaut.** La première phrase d'une liste ouverte est, de
   fait, une phrase mise en avant (§2 règle 1).
4. **Recalculer l'échelle des barres à chaque filtre.** Le plafond est celui de
   la fiche, pas celui de la sélection — un filtre retire de la masse, il ne
   redimensionne pas. L'échelle d'ensemble est la seule exception, et
   l'affichage l'écrit.

CE QU'ILS NE COUVRENT PAS, et il faut le dire (§2 règle 5) : aucun composant
React n'est rendu ici. Le comportement en navigateur — navigation par flèches,
par rail et au clavier, croisement des deux facettes, bascule « toutes les
périodes », fil fermé puis ouvert — a été vérifié hors dépôt sur `gabriel-attal`
(3 963 interventions, 10 périodes) contre le paquet construit, à 1 440 px. Rien
de tout cela n'est rejoué ici.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale"
SRC = UI / "src"

MODULE = SRC / "utils" / "parolesParPeriode.js"
COMPOSANT = SRC / "components" / "ParolesParPeriode.jsx"
FEUILLE = SRC / "components" / "ParolesParPeriode.css"
NAV = SRC / "components" / "NavigationPeriodes.jsx"
NAV_CSS = SRC / "components" / "NavigationPeriodes.css"
VOTES = SRC / "components" / "VotesParPeriode.jsx"
VOTES_CSS = SRC / "components" / "VotesParPeriode.css"
ADAPTATEUR = SRC / "data" / "pivotAdapter.js"
FICHE = SRC / "components" / "CandidateProfile.jsx"
PROFIL = SRC / "utils" / "profilCandidat.js"
METHODO = SRC / "pages" / "MethodologyPage.jsx"


def sans_commentaires(source: str) -> str:
    """Le code exécuté seul : ni `/* … */`, ni `// …`.

    Indispensable ici : l'en-tête du module EXPLIQUE pourquoi `format` n'est pas
    publié et pourquoi le fil reste fermé. Un test qui chercherait ces mots dans
    tout le fichier passerait sur la phrase qui les proscrit.
    """
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"(?<!:)//[^\n]*", "", source)


@pytest.fixture(scope="module")
def module() -> str:
    return sans_commentaires(MODULE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def composant() -> str:
    return sans_commentaires(COMPOSANT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def feuille() -> str:
    return sans_commentaires(FEUILLE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def nav() -> str:
    return sans_commentaires(NAV.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def adaptateur() -> str:
    return sans_commentaires(ADAPTATEUR.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def fiche() -> str:
    return sans_commentaires(FICHE.read_text(encoding="utf-8"))


# ── Les fichiers existent, et le calcul reste séparé du rendu ────────────────


def test_les_fichiers_de_la_section_existent() -> None:
    for chemin in (MODULE, COMPOSANT, FEUILLE, NAV, NAV_CSS):
        assert chemin.exists(), f"{chemin.relative_to(RACINE)} manquant"


def test_le_module_de_calcul_ne_connait_ni_react_ni_jsx(module: str) -> None:
    """Un calcul dans le composant est un calcul qu'aucun test ne peut lire."""
    assert "react" not in module.lower()
    assert "useState" not in module
    assert "</" not in module


# ── Règle 1 : le sujet se lit au niveau que le type porte ────────────────────


def test_les_trois_types_a_sujet_en_feuille_sont_nommes(module: str) -> None:
    """Question au gouvernement, question écrite, question orale.

    Sur ces trois-là, la racine du chemin est le créneau de séance — une seule
    valeur pour 3 660 lignes — et le sujet est la feuille.
    """
    assert "SUJET_EN_FEUILLE" in module
    for cle in ("question_gouvernement", "question_orale"):
        assert cle in module, f"{cle} absent de la table des sujets en feuille"


def test_le_sujet_choisit_la_feuille_ou_la_racine_selon_le_type(module: str) -> None:
    bloc = module[module.index("export function sujetDeIntervention") :]
    bloc = bloc[: bloc.index("\n}")]
    assert "SUJET_EN_FEUILLE.has" in bloc, "le niveau ne dépend pas du type"
    assert "segments[segments.length - 1]" in bloc, "la feuille n'est jamais prise"
    assert "segments[0]" in bloc, "la racine n'est jamais prise"


def test_le_chemin_est_decoupe_sur_le_separateur_de_la_source(module: str) -> None:
    """La source écrit « racine > étape > article ». On la lit, on ne la devine pas."""
    assert 'SEPARATEUR_CHEMIN' in module
    assert "'>'" in module


def test_aucun_rapprochement_de_libelles(module: str, composant: str) -> None:
    """Deux intitulés voisins ne se rejoignent jamais (#639).

    Ni normalisation de casse, ni suppression d'accents, ni distance entre
    chaînes : « Motion de censure » et « Motions de censure » restent deux
    entrées, et c'est un fait de la source.
    """
    for interdit in ("toLowerCase", "normalize(", "localeCompare(a", "startsWith("):
        assert interdit not in module, f"{interdit} ouvre la porte au rapprochement"
    assert "toLowerCase" not in composant


# ── Règle 2 : `format` n'est jamais publié ───────────────────────────────────


def test_le_champ_format_n_est_lu_nulle_part(module: str, composant: str) -> None:
    """Un seuil de cinquante mots posé à la collecte n'est pas un fait de source.

    `src/parse_syceron.py::_infer_format` le déduit du nombre de mots. Le
    publier ferait passer un choix d'implémentation pour une donnée.
    """
    for source in (module, composant):
        assert "reaction_courte" not in source
        assert "prise_de_parole_developpee" not in source
        assert ".format" not in source


def test_le_seuil_de_format_est_bien_une_deduction_du_depot() -> None:
    """Le garde-fou ci-dessus n'a de sens que si le champ est bien dérivé.

    Si un jour la source publiait elle-même ce format, la règle changerait de
    nature — et ce test tomberait, ce qui est exactement ce qu'on veut.
    """
    parseur = (RACINE / "src" / "parse_syceron.py").read_text(encoding="utf-8")
    assert "_FORMAT_SEUIL_MOTS" in parseur
    assert "def _infer_format" in parseur


# ── Règle 3 : aucun total de carrière, aucune densité, aucun taux ────────────


def test_la_section_ne_publie_plus_de_liste_de_natures_de_carriere(
    adaptateur: str, fiche: str
) -> None:
    """`interventionsParNature` totalisait les natures toutes périodes confondues.

    La nature est devenue une FACETTE, comptée sous la période et le sujet
    retenus. La fonction est partie avec son seul lecteur.
    """
    assert "interventionsParNature" not in adaptateur
    assert "interventionsParNature" not in fiche
    profil = sans_commentaires(PROFIL.read_text(encoding="utf-8"))
    assert "export function interventionsParNature" not in profil


def test_aucun_taux_ni_pourcentage_dans_le_module(module: str) -> None:
    assert "%" not in module
    assert "/ total" not in module


# ── Règle 4 : deux plafonds, tous deux nommés ────────────────────────────────


def test_les_deux_plafonds_existent_et_ne_prennent_aucun_filtre(module: str) -> None:
    """Le plafond se calcule sur les périodes, jamais sur une sélection.

    Une échelle qui suit le filtre ferait paraître deux interventions aussi
    larges que trois cent soixante-sept : cocher un filtre n'apprendrait plus
    rien, et deux périodes cesseraient de se comparer.
    """
    for nom in ("plafondParPeriode", "plafondToutesPeriodes"):
        signature = module[module.index(f"export function {nom}(") :]
        signature = signature[: signature.index(")")]
        assert signature.count(",") == 0, f"{nom} accepte un second argument"


def test_le_composant_choisit_le_plafond_selon_l_etendue(composant: str) -> None:
    assert "tout ? plafondEnsemble : plafondPeriode" in composant


def test_l_echelle_d_ensemble_se_declare_a_l_ecran(composant: str) -> None:
    """Une échelle qui change sans le dire est le seul vrai défaut ici."""
    assert "non comparable à celle d’une période" in composant
    assert "échelle commune aux périodes" in composant


# ── Règle 5 : le détail reste fermé tant qu'aucun sujet n'est choisi ─────────


def test_le_fil_est_ferme_par_defaut(composant: str) -> None:
    assert "useState(null)" in composant, "aucun sujet retenu au départ"
    assert "Choisissez un sujet" in composant


def test_le_fil_ne_s_ouvre_que_sur_un_sujet(composant: str) -> None:
    """Un clic sur une nature ne doit pas rouvrir 1 294 interventions.

    Une seule exception, et elle est nommée : `deplie`, quand un mot est tapé
    dans le filtre de la fiche (#979, arbitré le 17/09/2026) — la fiche est
    alors déjà réduite à ce que le mot porte."""
    bloc = composant[composant.index("const visibles = useMemo") :]
    bloc = bloc[: bloc.index("[lot,")]
    assert "sujet ? (i.sujet || SUJET_NON_PUBLIE) === sujet : deplie" in bloc, (
        "le fil ne dépend pas du sujet retenu, ou s'ouvre hors filtre"
    )
    assert "deplie = false" in composant, "le dépliage n'est pas l'état par défaut"


def test_la_periode_la_plus_recente_est_celle_du_depart(composant: str) -> None:
    """Sauf sous un mot du filtre de la fiche, où toutes les périodes sont
    montrées d'emblée (#979)."""
    assert "useState(deplie && !sansDecoupage ? null : periodes.length - 1)" in composant


# ── Règle 6 : ce que la source ne dit pas est publié, jamais deviné ──────────


def test_la_couverture_publie_ses_quatre_denominateurs(module: str) -> None:
    bloc = module[module.index("export function couvertureDesParoles") :]
    for cle in ("total", "datees", "sujet", "verbatim", "fonction", "themeSeul"):
        assert f"{cle}:" in bloc, f"{cle} absent de la couverture"


def test_le_regime_theme_seul_est_nomme_a_l_ecran(module: str, composant: str) -> None:
    """Aucun verbatim sur 5 483 interventions n'est pas un silence de la personne."""
    assert "theme_seul" in module
    assert "themeSeul" in composant
    assert "n’est pas un silence de la personne" in composant


def test_la_qualite_absente_n_est_jamais_comblee(composant: str) -> None:
    """La source ne publie la qualité que pour une fonction particulière.

    Lire ce silence comme « il parlait comme député » serait une inférence, et
    la section ne la fait pas : elle écrit la qualité quand elle existe.

    LE POURQUOI A DÉMÉNAGÉ, PAS LA RÈGLE. Le paragraphe qui expliquait le
    silence de la source était identique sous les 30 fiches et noyait les quatre
    chiffres qui, eux, parlent de la personne affichée. Il vit maintenant dans
    la méthodologie, et la fiche y renvoie : le test suit les deux moitiés,
    faute de quoi supprimer le renvoi ou vider la méthodologie passerait.
    """
    assert "i.fonction &&" in composant
    assert 'to="/methodologie#interventions"' in composant

    methodo = (SRC / "pages" / "MethodologyPage.jsx").read_text(encoding="utf-8")
    assert "silence de la source" in methodo
    assert "La qualité de l'orateur" in methodo


def test_une_date_illisible_sort_du_decoupage_et_le_dit(module: str, composant: str) -> None:
    assert "export function dateISO" in module
    assert "i.date)" in module
    assert "date exploitable" in composant


# ── Règle 7 : un seul mécanisme de navigation pour les deux sections ─────────


def test_les_deux_sections_appellent_la_meme_navigation(composant: str) -> None:
    votes = sans_commentaires(VOTES.read_text(encoding="utf-8"))
    assert "NavigationPeriodes" in composant
    assert "NavigationPeriodes" in votes
    assert "function Navigation(" not in votes, "une seconde navigation est réapparue"


def test_le_rail_a_quitte_la_feuille_des_votes() -> None:
    """Deux copies d'une même règle de style sont deux règles qui divergeront."""
    votes_css = sans_commentaires(VOTES_CSS.read_text(encoding="utf-8"))
    for classe in (".vp-rail", ".vp-fleche", ".vp-nav"):
        assert classe not in votes_css, f"{classe} vit encore dans VotesParPeriode.css"
    nav_css = sans_commentaires(NAV_CSS.read_text(encoding="utf-8"))
    for classe in (".np-rail", ".np-fleche", ".np-nav", ".np-position"):
        assert classe in nav_css


def test_les_fleches_du_clavier_ne_sont_plus_globales(nav: str) -> None:
    """Deux sections écoutant `window` déplaçaient les deux à la fois.

    L'écouteur est porté par le conteneur : il n'agit que si le focus est dans
    la navigation — l'état où l'on vient de cliquer une flèche ou un segment.
    """
    assert "window.addEventListener" not in nav
    assert "onKeyDown" in nav
    votes = sans_commentaires(VOTES.read_text(encoding="utf-8"))
    assert "window.addEventListener" not in votes


def test_les_deux_fleches_desactivees_nomment_deux_bouts_differents(nav: str) -> None:
    """À droite, on est au bout le plus RÉCENT, pas au début de la période."""
    assert "début de la période couverte" in nav
    assert "fin de la période couverte" in nav


def test_toutes_les_periodes_reste_optionnel(nav: str) -> None:
    """« Ce qu'il a voté » n'en a pas : y cumuler deux périodes reformerait le
    total de carrière que la vue refuse."""
    assert "avecTout = false" in nav
    votes = sans_commentaires(VOTES.read_text(encoding="utf-8"))
    assert "avecTout" not in votes


def test_le_pluriel_de_l_unite_est_tenu(nav: str) -> None:
    """« 1 textes » est une faute que le lecteur voit avant le chiffre."""
    assert "uniteSingulier" in nav


# ── Le branchement : une seule source pour les repères ───────────────────────


def test_les_reperes_viennent_du_module_des_votes(module: str) -> None:
    """Deux sections qui découpent le temps pareil doivent le faire au même endroit."""
    assert "from './votesParPeriode'" in module
    assert "bancALaDate" in module
    assert "gouvernementALaDate" in module


def test_l_adaptateur_passe_la_chronologie_entiere(adaptateur: str) -> None:
    """Ce qui découpe la carrière est le gouvernement EN PLACE, pas l'appartenance."""
    bloc = adaptateur[adaptateur.index("const parolesQualifiees") :]
    bloc = bloc[: bloc.index("periodesDeParole(")]
    assert "tousLesGouvernements" in bloc
    assert "INSTITUTION_PARLEMENT" in bloc


def test_la_fiche_declare_le_vide_quand_aucune_date_n_est_lisible(fiche: str) -> None:
    assert "interventions.periodes?.length" in fiche
    assert "ListeVide" in fiche


def test_la_methodologie_porte_l_ancre_du_renvoi(composant: str) -> None:
    methodo = METHODO.read_text(encoding="utf-8")
    assert "/methodologie#interventions" in composant
    assert "id: 'interventions'" in methodo


def test_la_methodologie_porte_les_regles_que_la_figure_n_ecrit_plus() -> None:
    """Le raisonnement sort de la figure, il ne disparaît pas.

    DESIGN_SYSTEM §7 règle 2 : « une limite tient en deux mots, une explication
    en paragraphe ». Les paragraphes vont là.
    """
    methodo = METHODO.read_text(encoding="utf-8")
    for mot in ("feuille", "racine", "cinquante mots", "densité par jour"):
        assert mot in methodo, f"« {mot} » absent de la méthodologie"
