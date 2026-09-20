"""Les amendements, deux parlements et un seul commutateur (#901).

CE QUE CE LOT RÈGLE. La carte « Les amendements dont il est l'auteur » trie par
COMMISSION, et le référentiel des commissions de l'Assemblée ne connaît aucun
dossier européen. Les deux populations mêlées, Emmanuel Maurel affichait
« 2 944 amendements · 18 dossiers · 38 adoptés » avec 2 615 lignes dans
« Matière non établie » — pour un fait que la source publie parfaitement : la
commission saisie au fond du dossier européen, que portent 3 557 des 3 690
dépôts des candidats déclarés (96 %, mesuré le 17/09/2026).

CE QUE CES GARDE-FOUS PROTÈGENT, et qui n'est pas graphique :

1. **Le partage se lit dans la donnée.** Un dépôt français porte un
   `amendement_id`, un dépôt européen porte `amendement_non_resolu.institution` ;
   172 244 contre 7 303 chez les candidats déclarés, sans aucun cas mixte.
   Jamais une heuristique sur la forme du `texte_vise`.
2. **Les deux populations ne s'additionnent jamais**, et leurs dossiers non plus :
   18 dossiers français et 170 européens chez Maurel restent deux comptes.
3. **Un sort absent n'est pas un sort nul** (§2 règle 5) : aucun des dépôts
   européens n'en porte, la carte dit « sort non publié ».
4. **Les articles 40 et 45 sont une règle de l'Assemblée** : la mention
   d'irrecevabilité suit la population affichée, elle ne se recopie pas.
5. **Un commutateur, un vocabulaire.** Les étiquettes sont celles de « Ce qu'il
   a dit » (`LIBELLE_QUALITE`), jamais une seconde formulation écrite à la main.

CE QU'ILS NE COUVRENT PAS, et il faut le dire (§2 règle 5) : aucun composant
React n'est rendu ici, et aucun test ne lit `pivot_data/`. Le rendu — les deux
commutateurs qui bougent ensemble, la colonne des noms élargie — a été vérifié
hors dépôt sur le serveur de développement, sur Maurel, Mélenchon et Philippot.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale" / "src"
ADAPTATEUR = UI / "data" / "pivotAdapter.js"
REGLES = UI / "utils" / "profilCandidat.js"
FICHE = UI / "components" / "CandidateProfile.jsx"
STYLE = UI / "components" / "CandidateProfile.css"


def _sans_commentaires(source: str) -> str:
    """Une règle citée en commentaire n'est pas une règle appliquée."""
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"^\s*//.*$", "", source, flags=re.MULTILINE)


@pytest.fixture(scope="module")
def adaptateur() -> str:
    return _sans_commentaires(ADAPTATEUR.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def fiche() -> str:
    return _sans_commentaires(FICHE.read_text(encoding="utf-8"))


def _executer(script: str) -> object:
    if shutil.which("node") is None:
        pytest.skip("node absent")
    entete = f"const a = await import({json.dumps(REGLES.as_uri())});\n"
    res = subprocess.run(
        ["node", "--input-type=module", "-e", entete + script],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout.strip().splitlines()[-1])


# ---------------------------------------------------------------------------
# 1. Le partage des deux populations
# ---------------------------------------------------------------------------


def test_un_depot_europeen_se_reconnait_a_son_institution() -> None:
    """Et un dépôt français à son `amendement_id`. Aucun profil ne porte les
    deux champs sur la même entrée — le test est donc exclusif."""
    out = _executer("""
      const cas = [
        { amendement_id: 4210, role_signataire: 'auteur_principal' },
        { amendement_id: null, amendement_non_resolu: { institution: 'parlement_europeen' } },
        { amendement_id: null, amendement_non_resolu: { institution: 'autre_chambre' } },
        {},
      ];
      console.log(JSON.stringify(cas.map(a.estAmendementEuropeen)));
    """)
    assert out == [False, True, False, False]


def test_le_dossier_europeen_n_est_pose_que_s_il_existe() -> None:
    """`joinAmendements` laisse `dossier_id` à null : la table qu'il consulte est
    celle de l'AN. Le rattachement ne comble pas ce vide en devinant — une
    référence hors index reste sans dossier, et sa matière non établie."""
    out = _executer("""
      const dossiers = { '2021/0136(COD)': { titre: 'Cadre pour une identité numérique' } };
      const joints = [
        { texte_vise: '2021/0136(COD)', dossier_id: null, dossier_titre: null },
        { texte_vise: '2029/9999(COD)', dossier_id: null, dossier_titre: null },
        { texte_vise: null, dossier_id: null, dossier_titre: null },
      ];
      const out = [...a.rattacheDossierEuropeen(joints, (r) => dossiers[r] || null)];
      console.log(JSON.stringify(out.map((x) => [x.dossier_id, x.dossier_titre])));
    """)
    assert out == [
        ["2021/0136(COD)", "Cadre pour une identité numérique"],
        [None, None],
        [None, None],
    ]


def test_l_axe_europeen_a_quitte_la_commission_pour_les_themes() -> None:
    """L'axe « commission saisie au fond » a été essayé puis écarté le
    17/09/2026 — « les catégories doivent être en cohérence entre le sankey des
    textes et les amendements ». Ce que ce test tenait (une saisine conjointe ne
    vaut qu'à défaut d'une saisine au fond) n'a plus de lecteur ; ce qu'il tient
    maintenant, c'est qu'aucune règle sans lecteur ne survit dans le module, et
    que la cascade des thèmes a pris sa place. Les thèmes eux-mêmes sont tenus
    par `tests/test_lecture_europeenne_901.py`."""
    regles = REGLES.read_text(encoding="utf-8")
    assert "commissionAuFondEuropeenne" not in regles
    adaptateur = ADAPTATEUR.read_text(encoding="utf-8")
    assert "themesDuDossier" in adaptateur


def test_les_deux_populations_sont_agregees_separement(adaptateur) -> None:
    """Chacune avec SON référentiel de commissions : mélanger les résolveurs
    renverrait les dépôts européens dans « Matière non établie »."""
    bloc = adaptateur.split("const amendementsParVersant")[1].split("};")[0]
    assert "estAmendementEuropeen(a)" in bloc, "le versant français exclut les dépôts européens"
    assert "joinsEuropeens" in bloc, "le versant européen consomme la liste jointe européenne"
    assert "commissionDuDossier" in bloc, "le versant français garde les commissions de l'AN"


def test_la_population_entiere_reste_celle_des_grands_chiffres(adaptateur) -> None:
    """Le partage est celui de LA SECTION. « Les grands chiffres » et « En bref »
    continuent de compter tous les dépôts : les ranger par institution est un
    autre lot, et retirer les dépôts européens d'ici les ferait disparaître de
    la fiche (§2 règle 5)."""
    assert "grandsChiffres({" in adaptateur
    grands = adaptateur.split("grandsChiffres({")[1].split("})")[0]
    assert "amendements," in grands
    # Depuis le 17/09/2026, les grands chiffres reçoivent AUSSI le partage : la
    # colonne « À l'Assemblée » comptait les 2 609 dépôts européens de Maurel.
    assert "amendementsParVersant," in grands


# ---------------------------------------------------------------------------
# 2. La section : un seul versant, deux commutateurs
# ---------------------------------------------------------------------------


def test_les_deux_commutateurs_reglent_le_meme_etat(fiche) -> None:
    """Celui des textes et celui des amendements appellent `changerVersant` :
    on change de parlement sans remonter d'un écran, et les deux figures ne
    peuvent pas se contredire."""
    assert fiche.count("<CommutateurVersant") == 4, (
        "textes, amendements, la carte du versant vide, et les votes (#901)"
    )
    assert "const [versantAmdt" not in fiche, "aucun second état de versant"
    # Les trois commutateurs de « Ce qu'il a proposé » règlent le MÊME état ;
    # celui des votes (#901) est dans une autre section, donc dans un autre état.
    section = fiche.split("function Propositions({")[1].split("function Paroles")[0]
    assert section.count("<CommutateurVersant") == 3
    for bloc in section.split("<CommutateurVersant")[1:]:
        entete = bloc.split("/>")[0]
        assert "changerVersant('fr')" in entete and "changerVersant('ue')" in entete


def test_le_commutateur_reprend_les_mots_de_ce_qu_il_a_dit(fiche) -> None:
    """Une seule formulation pour les deux parlements sur toute la fiche."""
    assert "LIBELLE_QUALITE[QUALITE_AN]" in fiche and "LIBELLE_QUALITE[QUALITE_PE]" in fiche
    assert "Au niveau français" not in fiche and "Au niveau européen" not in fiche


def test_la_puce_du_commutateur_n_est_pas_redefinie(fiche) -> None:
    """La forme vient de `ParolesParPeriode.css` : deux définitions de la même
    puce dériveraient l'une de l'autre (#672)."""
    assert "pp-qualite pp-qualite--an" in fiche and "pp-qualite pp-qualite--pe" in fiche
    style = STYLE.read_text(encoding="utf-8")
    assert ".pp-qualite" not in style, "la puce reste définie à un seul endroit"


def test_la_figure_suit_la_population_affichee(fiche) -> None:
    """Y compris ses irrecevabilités : les articles 40 et 45 ne concernent que
    l'Assemblée, et la carte européenne n'en affiche aucune."""
    section = fiche.split("amdt.totalAuteur === 0")[1]
    for lu in ("amdt.chute", "amdt.totalAuteur", "amdt.sortsPublies", "amdt.irrecevabilites"):
        assert lu in section, f"{lu} se lit sur la population affichée"
    assert "amendements.chute" not in section and "amendements.irrecevabilites" not in section


def test_changer_de_parlement_ferme_la_matiere_choisie(fiche) -> None:
    """« Finances » et « Legal Affairs » ne vivent pas dans le même référentiel :
    la garder ouvrirait une liste de dossiers sans rapport."""
    corps = fiche.split("const changerVersant")[1].split("};")[0]
    assert "setMatiere(null)" in corps


def test_un_versant_vide_nomme_son_parlement(fiche) -> None:
    """« Aucun amendement » se lirait comme un vide de collecte là où l'autre
    versant en porte des milliers."""
    vide = fiche.split("amdt.totalAuteur === 0 ? (")[1].split(") : amdt.chute")[0]
    assert "au Parlement européen" in vide and "Assemblée nationale" in vide
    assert "<CommutateurVersant" in vide


# ---------------------------------------------------------------------------
# 3. La colonne des noms, élargie pour les commissions européennes
# ---------------------------------------------------------------------------


def test_la_colonne_des_noms_tient_les_intitules_europeens() -> None:
    """« Environment, Public Health and Food Safety » fait 41 signes, là où
    « Finances » en fait 8 : quatre noms sur dix-neuf étaient tronqués. La barre
    qui suit rend la place, la colonne ne s'élargit qu'autant que le contenu le
    demande, et la mise en page mobile n'est pas touchée."""
    style = STYLE.read_text(encoding="utf-8")
    grille = [l for l in style.splitlines() if "grid-template-columns" in l and "290px" in l]
    assert grille, "la colonne des noms monte à 290 px"
    assert "minmax(120px, 290px) minmax(0, 0.9fr)" in grille[0], (
        "la place vient de la barre voisine, pas de la largeur de la carte"
    )


def test_la_liste_des_dossiers_ne_publie_pas_de_zero_sans_sort(fiche) -> None:
    """« aucun adopté » sous un dossier européen se lisait « rien n'a été
    adopté » : aucun des dépôts européens ne porte de sort. La ligne ne dit rien
    de l'adoption quand la population affichée n'a aucun sort publié (§2 règle 5)."""
    liste = fiche.split("dossiersDeLaMatiere.map")[1].split("</ul>")[0]
    assert "amdt.sortsPublies === 0 ? null" in liste
    assert liste.index("amdt.sortsPublies === 0") < liste.index("aucun adopté")
