"""« Ce qu'il a voté » range les positions par période politique (#328).

La section publiait un décompte de carrière — « 123 pour, 34 contre, 11
abstentions » — qui ne dit rien, parce qu'un même vote n'a pas le même sens
selon d'où il est émis. Elle publie maintenant les positions de dernière lecture
découpées en PÉRIODES POLITIQUES, une nouvelle dès que le banc ou le
gouvernement change, avec la matière du texte, son origine et son sort.

Ce que ces garde-fous protègent est éditorial, pas graphique. Trois pentes,
toutes tentantes pour une session qui « améliorerait » la vue :

1. **Recalculer l'échelle à chaque filtre.** Une échelle qui suit le filtre fait
   paraître 2 textes parlementaires aussi larges que 37 gouvernementaux : cocher
   un filtre n'apprend plus rien, et deux périodes ne se comparent plus.
   `porteeCommune` se calcule sur TOUTES les périodes, sans garde.
2. **Combler un repère manquant par celui de la période voisine.** Le banc et le
   gouvernement ne sont pas publiés ensemble : avant 2017 le corpus n'a aucune
   fiche de gouvernement, depuis 2024 l'Assemblée ne déclare plus le banc. Le
   titre NOMME ce qui manque (§2 règle 5).
3. **Déduire l'origine ou la matière d'un intitulé, en sous-chaîne.** L'origine
   est lue sur un mot ANCRÉ en tête que la source pose elle-même ; la matière
   vient du dossier, jamais d'un rapprochement de libellés
   (`docs/decisions/regrouper-nest-pas-joindre-639.md`).

CE QU'ILS NE COUVRENT PAS, et il faut le dire (§2 règle 5) : comme
`test_cascade_textes_328.py`, ils ne rendent aucun composant React. Le
comportement en navigateur — navigation par flèches et par rail, clic sur une
barre, isolement d'une colonne, échelle inchangée sous filtre, mise en page
mobile — a été vérifié hors dépôt sur `marine-le-pen`, `jerome-guedj`,
`edouard-philippe` et `nathalie-arthaud` (profil sans vote), à 1 280 et 390 px.
Rien de tout cela n'est rejoué ici.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale"
SRC = UI / "src"

MODULE = SRC / "utils" / "votesParPeriode.js"
COMPOSANT = SRC / "components" / "VotesParPeriode.jsx"
FEUILLE = SRC / "components" / "VotesParPeriode.css"
ADAPTATEUR = SRC / "data" / "pivotAdapter.js"
CHARGEUR = SRC / "data" / "index.js"
SYNC = UI / "scripts" / "sync-data.mjs"
FICHE = SRC / "components" / "CandidateProfile.jsx"
METHODO = SRC / "pages" / "MethodologyPage.jsx"
PAGE_STATIQUE = SRC / "components" / "StaticPage.jsx"


def sans_commentaires(source: str) -> str:
    """Le code exécuté seul : ni `/* … */`, ni `// …`.

    Indispensable ici : l'en-tête du module EXPLIQUE pourquoi la rayure a été
    écartée et pourquoi l'échelle ne se recalcule pas. Un test qui chercherait
    ces mots dans tout le fichier passerait sur la phrase qui les proscrit.
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
def adaptateur() -> str:
    return sans_commentaires(ADAPTATEUR.read_text(encoding="utf-8"))


# ── Les fichiers existent, et le calcul est séparé du rendu ──────────────────


def test_les_quatre_fichiers_de_la_section_existent() -> None:
    for chemin in (MODULE, COMPOSANT, FEUILLE):
        assert chemin.exists(), f"{chemin.relative_to(RACINE)} manquant"


def test_le_module_de_calcul_ne_connait_ni_react_ni_jsx(module: str) -> None:
    """Un calcul dans le composant est un calcul qu'aucun test ne peut lire.

    Les périodes, les matières et l'échelle sont des FAITS : ils se testent. Le
    jour où l'un d'eux migre dans le JSX, il sort du périmètre de ce fichier
    sans que rien ne le signale.
    """
    assert "react" not in module.lower()
    assert "useState" not in module
    assert "</" not in module


# ── Règle 1 : une seule échelle, calculée sur tous les votes ─────────────────


def test_la_portee_se_calcule_sans_garde(module: str) -> None:
    """`porteeCommune` n'accepte aucun filtre : c'est ce qui la fige.

    Lui passer la garde du composant ferait suivre l'échelle aux filtres, et
    c'est exactement ce que la vue interdit.
    """
    signature = re.search(r"export function porteeCommune\(([^)]*)\)", module)
    assert signature, "porteeCommune introuvable"
    assert signature.group(1).strip() == "periodes"

    corps = module.split("export function porteeCommune(")[1]
    corps = corps.split("\nexport ")[0]
    assert "matieresDePeriode(p)" in corps, (
        "porteeCommune doit appeler matieresDePeriode SANS garde : "
        "un second argument y ferait entrer le filtre."
    )


def test_le_composant_recoit_la_portee_et_ne_la_recalcule_pas(composant: str) -> None:
    assert "porteeCommune" not in composant
    assert "portee" in composant


# ── Règle 2 : un repère manquant est nommé, jamais comblé ────────────────────


def test_une_periode_sans_aucun_repere_est_declaree(module: str) -> None:
    assert "REPERE_NON_PUBLIE" in module
    assert "sansRepere: !p.banc && !p.gouvernementId" in module


def test_le_titre_nomme_le_repere_manquant(composant: str) -> None:
    """« Gouvernement Borne » seul laisserait croire que le banc n'existait pas.

    Ce sont deux faits différents : un banc non déclaré par la source, et
    l'absence de banc. Le titre écrit le premier.
    """
    assert "banc non publié" in composant
    assert "gouvernement non publié" in composant
    assert "REPERE_NON_PUBLIE" in composant


def test_le_banc_vient_du_mandat_et_jamais_du_groupe_voisin(module: str) -> None:
    """Le banc se lit à la DATE du vote, sur un mandat qui le porte.

    `x.position` dans le filtre garantit qu'un mandat sans position déclarée
    n'est pas retenu : sans lui, un siège muet renverrait `position: undefined`
    et la période changerait de clé sans qu'aucun fait n'ait changé.
    """
    corps = module.split("export function bancALaDate(")[1].split("\n}")[0]
    assert "x.debut <= date && date <= x.fin" in corps
    assert "x.position" in corps


# ── Règle 3 : l'origine est un mot de la source, ancré en tête ───────────────


def test_l_origine_est_ancree_en_tete(module: str) -> None:
    assert "const PROJET_DE_LOI = /^projet de loi\\b/;" in module
    assert "const PROPOSITION = /^proposition\\b/;" in module


def test_l_origine_a_un_troisieme_etat(module: str) -> None:
    """Ni « projet », ni « proposition » : l'origine n'est pas établie.

    Ranger le texte au Parlement par défaut inventerait une initiative
    parlementaire. La couverture est aujourd'hui de 100 %, ce qui ne dispense
    pas du troisième état — une couverture n'est pas une garantie de schéma.
    """
    corps = module.split("export function origineDuScrutin(")[1].split("\n}")[0]
    assert corps.rstrip().endswith("return null;")


def test_la_matiere_vient_du_dossier_pas_de_l_intitule(module: str) -> None:
    corps = module.split("export function qualifierVotes(")[1].split("\nexport ")[0]
    assert "commissionDuDossier(dossierId)" in corps
    assert "commission?.sigle ?? null" in corps


# ── Règle 4 : le repli sur la dernière lecture n'a qu'une implémentation ─────


def test_le_module_ne_reimplemente_pas_la_derniere_lecture(module: str) -> None:
    """AGENTS.md §6 : la sélection vit UNIQUEMENT dans `utils/lecture.js` (#711).

    Le module consomme des votes déjà retenus ; il ne trie pas les lectures.
    """
    for interdit in ("selectDerniereLectureVotes", "isWholeTextVote", "grouperLecturesParTexte"):
        assert interdit not in module, f"{interdit} ne doit pas être appelé ici"


def test_l_adaptateur_part_des_votes_deja_retenus(adaptateur: str) -> None:
    assert "qualifierVotes(lectureVotes.retenus" in adaptateur


def test_votes_du_profil_rend_les_votes_retenus() -> None:
    source = sans_commentaires(
        (SRC / "utils" / "profilCandidat.js").read_text(encoding="utf-8")
    )
    corps = source.split("export function votesDuProfil(")[1].split("\nexport ")[0]
    assert re.search(r"^\s*retenus,\s*$", corps, flags=re.MULTILINE), (
        "votesDuProfil doit rendre la liste retenue, pas seulement son compte : "
        "sinon la vue par période refait le repli, et il existe en deux versions."
    )


# ── Règle 5 : un 49.3 n'est jamais une position de vote ──────────────────────


def test_le_49_3_est_lu_par_la_fonction_partagee(module: str) -> None:
    assert "estProcedure49_3" in module
    assert "procedure49_3: estProcedure49_3(" in module


def test_le_49_3_est_marque_a_part_dans_la_liste(composant: str, feuille: str) -> None:
    assert "vp-49-3" in composant
    assert ".vp-49-3" in feuille


# ── Règle 6 : la section publie ses propres trous ────────────────────────────


def test_la_couverture_des_reperes_porte_son_denominateur(module: str) -> None:
    corps = module.split("export function couvertureDesReperes(")[1].split("\n}")[0]
    for cle in ("total", "banc", "gouvernement", "unRepereAuMoins", "matiere", "origine", "statut"):
        assert f"{cle}:" in corps, f"couvertureDesReperes doit publier « {cle} »"


def test_la_section_affiche_ce_qu_elle_ne_sait_pas(composant: str) -> None:
    assert "Ce que cette figure ne sait pas" in composant
    assert "reperes.matiere" in composant
    assert "reperes.total" in composant


# ── L'origine se dit par la forme, jamais par une texture ────────────────────


def test_le_parlement_est_voile_et_filete_jamais_raye(feuille: str) -> None:
    """La rayure éclaircissait la teinte et disparaissait sur un texte ou deux.

    Le voile rend au segment son poids, le filet garde l'arête. La teinte de
    position n'est jamais altérée : elle porte l'autre information.
    """
    assert "repeating-linear-gradient" not in feuille, (
        "la rayure a été écartée : elle éclaircit la teinte de position et "
        "s'efface sur les segments d'un ou deux textes"
    )
    bloc = feuille.split(".vp-seg--parlement")[1].split("}")[0]
    assert "color-mix" in bloc
    assert "inset 0 0 0 1.6px var(--pc)" in bloc


def test_les_teintes_de_position_ne_sont_pas_reecrites(feuille: str, composant: str) -> None:
    """Une couleur écrite deux fois est une couleur qui divergera.

    Les trois teintes vivent dans `VOTE_STYLE` (utils/lecture.js) et arrivent
    par `--pc`. Aucun hexadécimal de position dans la feuille.
    """
    for hexa in ("#007A45", "#E53420", "#8B8794", "#007a45", "#e53420", "#8b8794"):
        assert hexa not in feuille
    assert "VOTE_STYLE" in composant


# ── L'ordre des positions est le même aux trois endroits ─────────────────────


def test_un_seul_ordre_de_positions(module: str, composant: str) -> None:
    """Figure, filtres et colonnes suivent le même ordre : contre, abstention, pour.

    Une colonne doit se retrouver sous la portion de barre dont elle vient.
    """
    assert "export const POSITIONS_ORDONNEES = ['contre', 'abstention', 'pour'];" in module
    # Les trois usages du composant lisent la constante, aucun ne réécrit l'ordre.
    assert composant.count("POSITIONS_ORDONNEES") >= 3
    assert "['pour', 'contre', 'abstention']" not in composant


# ── Le chargement du fichier de rattachement ─────────────────────────────────


def test_l_index_scrutin_dossier_est_charge_et_copie() -> None:
    chargeur = sans_commentaires(CHARGEUR.read_text(encoding="utf-8"))
    assert "/data/scrutins_dossiers.json" in chargeur
    sync = sans_commentaires(SYNC.read_text(encoding="utf-8"))
    assert "scrutins_dossiers.json" in sync


def test_une_absence_d_index_n_est_pas_une_absence_de_commission() -> None:
    """`rattachementDisponible` distingue les deux, comme #510 pour les scrutins.

    Index illisible : la matière manque pour TOUS les votes. Index lu mais sans
    entrée : ce texte n'a pas de commission saisie au fond publiée. Confondre
    les deux ferait lire « le fichier était absent » comme « ces textes n'ont
    pas de commission ».
    """
    adaptateur = sans_commentaires(ADAPTATEUR.read_text(encoding="utf-8"))
    assert "rattachementDisponible: scrutinsDossiers !== null" in adaptateur


# ── Le renvoi vers la méthodologie mène quelque part ─────────────────────────


def test_le_renvoi_methodo_est_ancre_et_la_cible_existe() -> None:
    """Un lien posé sous une figure doit déposer le lecteur DEVANT la règle.

    Sans `id`, `/methodologie#votes` ouvre une page de dix sections en haut.
    """
    composant = COMPOSANT.read_text(encoding="utf-8")
    assert '"/methodologie#votes"' in composant

    methodo = METHODO.read_text(encoding="utf-8")
    assert "id: 'votes'," in methodo

    statique = sans_commentaires(PAGE_STATIQUE.read_text(encoding="utf-8"))
    assert "id={section.id}" in statique


def test_seul_le_pourquoi_des_deux_regles_part_dans_la_methodologie() -> None:
    """Ce qui part est le raisonnement, jamais la règle elle-même.

    La fiche portait les deux règles EN ENTIER sous la figure — `phrase` et
    `pourquoi` —, soit deux paragraphes qui font lire la légende à la place du
    fait. Le `pourquoi` passe dans la page de méthodologie, où mène le renvoi
    posé sous la figure.

    Les deux `phrase` RESTENT sur la fiche : #711 les veut à côté du chiffre,
    et la garde de `test_derniere_lecture_711.py` le vérifie de son côté. La
    méthodologie annonçait déjà la règle de la dernière lecture à l'époque où
    rien ne l'appliquait — c'est précisément l'incident que #711 a corrigé, et
    la déplacer entièrement le rejouerait.
    """
    methodo = METHODO.read_text(encoding="utf-8")
    assert "LAST_READING_RULE" in methodo
    assert "WHOLE_TEXT_VOTE_BOUND" in methodo
    assert "périodes politiques" in methodo

    fiche = sans_commentaires(FICHE.read_text(encoding="utf-8"))
    # Les deux `phrase` ont quitté la fiche le 10/09 : la règle est APPLIQUÉE
    # par `utils/lecture.js` depuis #711, et l'incident que #711 corrigeait — une
    # règle annoncée que rien n'appliquait — ne peut plus se reproduire en
    # silence. Ce qui reste sous les yeux du lecteur est l'étiquette courte du
    # chiffre, et le renvoi vers le raisonnement.
    assert "LAST_READING_RULE" not in fiche
    assert "WHOLE_TEXT_VOTE_BOUND" not in fiche
    assert "LAST_READING_LABEL" in fiche, "l'étiquette du chiffre reste sur la fiche"
    # Le renvoi est posé SOUS LA FIGURE, donc dans le composant qui la rend —
    # pas dans la fiche, qui ne fait que l'appeler.
    figure = (RACINE / "web" / "UI_finale" / "src" / "components" / "VotesParPeriode.jsx").read_text(
        encoding="utf-8",
    )
    assert 'to="/methodologie#votes"' in figure, "le renvoi vers le raisonnement reste"
    assert ".pourquoi" not in fiche, (
        "le raisonnement long vit dans la méthodologie, jamais sur la fiche"
    )


# ── Le contrat de forme se lit chez le PRODUCTEUR, jamais dans le corpus ─────


def test_l_ui_lit_l_index_sous_la_forme_que_le_producteur_ecrit() -> None:
    """Deux tables, et un statut par DOSSIER — pas un statut par scrutin.

    Un même dossier porte plusieurs scrutins : ranger le sort sous le scrutin le
    dupliquerait et le ferait diverger d'une lecture à l'autre.

    Le contrat se vérifie sur `src/scrutins_dossiers_an.py`, qui l'écrit, et
    JAMAIS sur `pivot_data/scrutins_dossiers.json` : le sparse-checkout de
    `tests.yml` refuse `pivot_data/` sur le disque de la CI (#473, AGENTS.md
    §3b). Un test qui lirait le corpus passerait en local et échouerait en CI —
    et c'est bien ce qu'a fait la première version de ce fichier, attrapée par
    `test_ci_perimetre_sparse_checkout.py`.
    """
    producteur = (RACINE / "src" / "scrutins_dossiers_an.py").read_text(encoding="utf-8")
    assert 'SCHEMA_VERSION = "scrutins-dossiers-v1"' in producteur
    assert '{"statut": statut, "sort_49_3": sort_49_3}' in producteur

    chargeur = sans_commentaires(CHARGEUR.read_text(encoding="utf-8"))
    assert "scrutins: d.scrutins || {}, dossiers: d.dossiers || {}" in chargeur

    module = sans_commentaires(MODULE.read_text(encoding="utf-8"))
    assert "scrutinsDossiers?.scrutins" in module
    assert "scrutinsDossiers?.dossiers" in module
