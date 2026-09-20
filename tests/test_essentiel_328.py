"""Les cinq arbitrages rendus sur « L'essentiel » sont verrouillés dans le code exécuté (#328).

La propriétaire a relu le bloc issu de la PR #694 et rendu cinq décisions le
01/09/2026. Chacune est le genre de choix qu'une session suivante défait sans
s'en apercevoir, parce qu'il a l'air d'un détail de style :

  1. La section s'appelle « L'essentiel » — « Coup d'œil » promettait de la
     rapidité, pas du contenu.
  2. Les deux moitiés de la phrase d'introduction ont MÊME TAILLE et MÊME
     GRAISSE : ce sont les deux termes d'une opposition, et n'accentuer que la
     seconde faisait lire la première comme sa légende. L'accent porte sur les
     DEUX MOTS opposés, jamais sur une ligne entière.
  3. Les cinq points sont tirés d'un VIVIER, avec la garantie d'au moins un
     point par rôle réellement tenu (option C).
  4. Le point « amendements » publie un COUPLE de nombres regroupé par dossier
     législatif, plus la commission saisie au fond — jamais un compte brut, un
     filtre sur les adoptés, ni un décompte de `texte_vise`.
  5. Le rendu s'adapte au cas : barre pour les commissions saisies au fond,
     podium pour les mandats en commission, liste pour les textes portés.

Le dépôt n'a pas de harnais de test JS — `package.json` ne déclare que `dev`,
`build`, `lint` et `sync-data`. Ces garde-fous sont donc en Python et lisent le
**code exécuté** : les commentaires sont retirés avant toute assertion, pour
qu'un commentaire parlant de « Coup d'œil » ne fasse ni passer ni échouer un
test qui vérifie que le libellé a disparu.

CE QU'ILS NE COUVRENT PAS, et il faut le dire (§2 règle 5) : ils ne rendent
aucun composant React. Le comportement de `selectionnerPoints` est vérifié par
lecture de sa source, pas par exécution. La vérification par rendu réel
(`react-dom/server` sur les 13 profils publiés) a été faite hors dépôt et ne
couvre ni la mise en page, ni le responsive, ni le contraste, ni le parcours
clavier.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale" / "src"

MODULE_REGLES = UI / "utils" / "profilCandidat.js"
# NOTE (#328) : « L'essentiel » a été remplacé par « Les grands chiffres », et
# les CINQ tests qui décrivaient sa vue — le titre de la section, l'accent
# typographique sur « réaction » / « initiative », et les trois règles CSS de la
# thèse et de la barre — sont retirés avec elle. Ce
# qui reste ici teste le VIVIER, qui n'est pas retiré : la décision prévoit
# qu'un vrai résumé prenne la place que le bloc libère. Le bloc lui-même est
# verrouillé par `tests/test_grands_chiffres_328.py`.

COMPOSANT = UI / "components" / "CandidateProfile.jsx"
FEUILLE = UI / "components" / "CandidateProfile.css"

#: Le module qui dérive la commission saisie au fond, et le script qui la publie.
MODULE_COMMISSIONS = RACINE / "src" / "commissions_dossiers_an.py"
BUILDER_COMMISSIONS = RACINE / "src" / "build_commissions_dossiers.py"


def sans_commentaires(source: str) -> str:
    """Le code exécuté seul : ni `/* … */`, ni `// …`.

    Le retrait de `//` épargne les `://` (une URL n'est pas un commentaire).
    """
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"(?<!:)//[^\n]*", "", source)


def sans_commentaires_css(source: str) -> str:
    return re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)


@pytest.fixture(scope="module")
def regles() -> str:
    return sans_commentaires(MODULE_REGLES.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def composant() -> str:
    return sans_commentaires(COMPOSANT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def feuille() -> str:
    return sans_commentaires_css(FEUILLE.read_text(encoding="utf-8"))


def _bloc_css(feuille: str, selecteur: str) -> str:
    trouve = re.search(rf"^{re.escape(selecteur)}\s*\{{(.*?)\n\}}", feuille, re.DOTALL | re.M)
    assert trouve, f"le sélecteur `{selecteur}` n'est plus déclaré dans CandidateProfile.css"
    return trouve.group(1)


# ---------------------------------------------------------------------------
# 1. Le titre
# ---------------------------------------------------------------------------


def test_coup_d_oeil_ne_survit_nulle_part_dans_la_fiche(regles, composant, feuille):
    """Un libellé retiré de l'écran mais gardé en classe CSS ou en nom de champ
    revient au premier copier-coller."""
    for nom, source in (("règles", regles), ("composant", composant), ("feuille", feuille)):
        for interdit in ("Coup d’œil", "Coup d'œil", "coupOeil", "COUP_OEIL", "coup-oeil"):
            assert interdit not in source, (
                f"« {interdit} » subsiste dans le {nom} de la fiche candidat : "
                "la section s'appelle « L’essentiel » partout, code compris"
            )


# ---------------------------------------------------------------------------
# 2. Les deux moitiés de la thèse
# ---------------------------------------------------------------------------


def test_le_vivier_porte_plus_de_points_que_la_section_n_en_montre(regles):
    """Un « vivier » de cinq pour cinq places n'est pas un vivier : la sélection
    n'aurait rien à sélectionner. Sept sortes de points sont déclarées."""
    debut = regles.index("function vivierDesPoints(")
    corps = regles[debut : regles.index("\nexport function selectionnerPoints", debut)]
    cles = set(re.findall(r"'([\w_]+)'", corps))
    attendues = {
        "interventions",
        "amendements",
        "commissions",
        "questions",
        "textes_gouvernement",
        "textes_parlement",
        "qualite",
    }
    assert attendues <= cles, f"points manquants dans le vivier : {sorted(attendues - cles)}"


def test_les_deux_points_de_textes_portes_sont_distincts(regles):
    """Porter un projet de loi au nom du gouvernement n'est pas déposer une
    proposition comme parlementaire. La source rangeait les deux sous le même
    `role: auteur` jusqu'à #689 ; les additionner sous « textes portés » faisait
    lire 34 textes personnels là où 30 sont ceux du gouvernement."""
    assert "textes_gouvernement" in regles and "textes_parlement" in regles


def test_la_garantie_reserve_une_place_avant_de_remplir(regles):
    """La garantie doit s'appliquer AVANT le remplissage dans l'ordre, sans quoi
    elle ne change jamais rien."""
    debut = regles.index("export function selectionnerPoints(")
    corps = regles[debut : regles.index("\n}", debut)]
    place_garantie = corps.index("for (const role of rolesTenus)")
    place_remplissage = corps.index("for (let i = 0;")
    assert place_garantie < place_remplissage, (
        "la place réservée à chaque rôle tenu doit être prise avant le "
        "remplissage dans l'ordre du vivier"
    )
    assert ".sort((a, b) => a - b)" in corps, (
        "la sélection est remise dans l'ordre du vivier : la garantie change QUI "
        "est retenu, jamais l'ordre de lecture"
    )


def test_la_garantie_ne_fabrique_pas_un_point_pour_un_role_sans_donnee(regles):
    """Ségolène Royal et Xavier Bertrand ont été membres d'un gouvernement et le
    corpus n'en publie ni intervention, ni question, ni texte porté. La section
    le DIT (§2 règle 5) au lieu d'inventer un chiffre."""
    assert "rolesSansPoint" in regles
    assert "LIBELLE_ROLE_ABSENT" in regles


def test_le_role_gouvernemental_se_lit_sur_un_fait_collecte(regles):
    """`appartenancesGouvernementales` — être MEMBRE d'un gouvernement, jamais
    une catégorie éditoriale. Un⋅e parlementaire en mission n'en est pas
    membre : c'est ce qui écarte correctement les deux mandats « en mission » de
    Jérôme Guedj."""
    debut = regles.index("export function essentiel(")
    corps = regles[debut : regles.index("\n}\n", debut)]
    assert "(appartenances || []).length > 0" in corps, (
        "le rôle gouvernemental se déduit de `appartenancesGouvernementales`, "
        "pas d'un intitulé de mandat"
    )


def test_le_role_d_un_texte_porte_lit_le_role_avant_la_nature(regles):
    """Gabriel Attal est RAPPORTEUR d'un projet de loi : un acte parlementaire
    sur un texte du gouvernement. Le ranger au gouvernement sur sa seule nature
    serait le contresens exact que #689 a corrigé dans l'autre sens."""
    debut = regles.index("const ROLE_INSTITUTION = {")
    corps = regles[debut : regles.index("\n};", debut)]
    assert "rapporteur" in corps and "'co-rapporteur'" in corps, (
        "`rapporteur` et `co-rapporteur` relèvent du parlement, quelle que soit "
        "la nature du texte rapporté"
    )
    fonction = regles[regles.index("export function institutionDuTexte(") :]
    fonction = fonction[: fonction.index("\n}")]
    assert fonction.index("ROLE_INSTITUTION[") < fonction.index("nature_texte"), (
        "`role` est lu AVANT `nature_texte`"
    )


def test_un_texte_sans_nature_n_est_range_d_aucun_cote(regles):
    """Trois états, pas deux : 4 des 423 textes portés des 13 candidats
    ne portent ni rôle qualifiant ni nature. Ranger par défaut au parlement
    inventerait une initiative personnelle (§2 règle 5)."""
    assert "sansNature" in regles


# ---------------------------------------------------------------------------
# 4. Le point « amendements »
# ---------------------------------------------------------------------------


def test_les_depots_se_regroupent_par_dossier_jamais_par_texte_vise(regles):
    """Un `texte_vise` est une LECTURE, pas une loi : un PLFSS revenant en
    nouvelle lecture compterait double. Jérôme Guedj passe de 47 lectures à 25
    dossiers une fois replié sur `dossier_id`."""
    debut = regles.index("export function agregerAmendements(")
    corps = regles[debut : regles.index("\n}\n", debut)]
    assert "a.dossier_id ||" not in corps and "dossier_id || a.texte_vise" not in corps, (
        "la clé de regroupement ne doit pas être `dossier_id || texte_vise` : "
        "elle publiait « 34 dossiers législatifs » là où il y en a 25 et 9 textes "
        "visés orphelins (défaut de clé `a or b`, AGENTS.md §3a / #668)"
    )
    assert "if (a.dossier_id) {" in corps, (
        "les dépôts se regroupent sur `dossier_id` seul ; ceux qui n'en ont pas "
        "sont comptés à part"
    )


def test_la_borne_des_depots_sans_dossier_est_declaree(regles):
    """Chez Jean-Luc Mélenchon la répartition reposerait sur 12 % de ses dépôts
    (332 des 2 831) : la page l'écrit au lieu de la présenter comme complète
    (§2 règle 5). La cause est l'issue #696, déclarée et non corrigée ici."""
    assert "sansDossier" in regles
    debut = regles.index("export function agregerAmendements(")
    corps = regles[debut : regles.index("\n}\n", debut)]
    assert "depotsSansDossier" in corps and "textesSansDossier" in corps


def test_le_point_amendements_publie_un_couple_pas_un_compte_brut(regles):
    """Un nombre seul appellerait un classement ; deux nombres qui varient en
    sens inverse appellent une lecture. Marine Le Pen fait 83 dossiers pour 685
    dépôts, Laurent Wauquiez 14 pour 326 — aucun des deux n'est « meilleur »."""
    assert "RENDU_COUPLE" in regles
    assert "couple: [" in regles


def test_aucun_taux_d_adoption_ni_filtre_sur_les_adoptes(regles):
    """AGENTS.md §6 interdit tout taux d'adoption entre types de déposants, et
    le `sort` est inconnu sur 1 822 des 2 831 dépôts de Jean-Luc Mélenchon —
    un décompte sur un dénominateur amputé de 64 % viole §2 règle 5."""
    debut = regles.index("function vivierDesPoints(")
    corps = regles[debut : regles.index("\nexport function selectionnerPoints", debut)]
    assert "adopte" not in corps.lower(), (
        "aucun point de « L’essentiel » ne filtre ni ne compte les amendements "
        "adoptés : le chiffre mesure le terrain, pas la personne"
    )


def test_la_commission_est_lue_dans_la_source_jamais_deduite_d_un_intitule():
    """« Lois » couvre l'immigration, la justice et les institutions. Bâtir la
    correspondance intitulé → thème serait une classification construite par ce
    dépôt, c'est-à-dire un acte éditorial (§2 règle 1)."""
    assert MODULE_COMMISSIONS.is_file(), f"{MODULE_COMMISSIONS} est attendu par #328"
    assert BUILDER_COMMISSIONS.is_file(), f"{BUILDER_COMMISSIONS} est attendu par #328"
    source = MODULE_COMMISSIONS.read_text(encoding="utf-8")
    assert 'CODE_ACTE_SAISIE_FOND = "AN1-COM-FOND-SAISIE"' in source, (
        "la commission saisie au fond est lue sur le seul acte "
        "`AN1-COM-FOND-SAISIE` de l'archive AN"
    )


def test_le_libelle_dit_examinees_par_jamais_travaille_sur(regles):
    """Une commission n'est pas un sujet : « Lois » couvre l'immigration, la
    justice et les institutions. Aide à la lecture (§2 règle 8), pas position
    déclarée."""
    assert "'Dossiers examinés par'" in regles
    assert "travaille sur" not in regles.lower()


# ---------------------------------------------------------------------------
# 5. Le rendu s'adapte au cas
# ---------------------------------------------------------------------------


def test_trois_rendus_declares_et_fermes(regles):
    """La forme suit le cas — « 27 sur 60 » se compare mal en prose, cinq
    intitulés de texte se lisent très bien en liste."""
    debut = regles.index("export const RENDUS_POINT = [")
    corps = regles[debut : regles.index("];", debut)]
    for rendu in ("RENDU_RATIO", "RENDU_COUPLE", "RENDU_PODIUM"):
        assert rendu in corps, f"`{rendu}` doit figurer dans le vocabulaire fermé des rendus"


def test_aucun_seuil_arbitraire_ne_decide_qu_il_y_a_une_tendance(regles):
    """La contrainte « une tendance quand elle existe, rien quand elle n'existe
    pas » se règle SANS seuil : la barre montre la répartition et laisse la
    forme parler. Un seuil serait un arbitrage éditorial (§2 règle 1)."""
    debut = regles.index("function vivierDesPoints(")
    corps = regles[debut : regles.index("\nexport function selectionnerPoints", debut)]
    assert "tendance" not in corps.lower(), (
        "aucun point ne qualifie une répartition de « tendance » : la donnée la "
        "produit ou non, et la barre le montre"
    )


def test_le_jaune_signal_ne_sert_ni_de_filet_ni_de_decor(feuille):
    """DESIGN_SYSTEM §3 : jaune signal = sélection, action, source vérifiée."""
    debut = feuille.index(".cp-gc {")
    fin = feuille.index(".cp-section {")
    assert "#DFFF00" not in feuille[debut:fin].upper(), (
        "le jaune signal n'apparaît nulle part dans « Les grands chiffres » : ni filet, "
        "ni segment, ni décor"
    )


def test_la_repartition_n_est_pas_normalisee_a_cent_pour_cent(regles):
    """DESIGN_SYSTEM §5 : segments proportionnels au décompte réel. Le
    dénominateur est le TOTAL des dossiers amendés, pas la somme des trois
    segments — ce qui reste demeure visible comme du vide."""
    debut = regles.index("repartition: dossiers.commissions.length")
    corps = regles[debut : regles.index("texte:", debut)]
    assert "total: dossiers.distincts," in corps, (
        "le dénominateur de la barre est `dossiers.distincts`, jamais la somme "
        "des segments montrés"
    )
