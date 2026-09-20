"""Les arbitrages de la fiche de groupe (#329) sont verrouillés dans le code exécuté.

La fiche de groupe est devenue, le 11/09/2026, une **fiche de lignée** : la
propriétaire a tranché la veille qu'on publie une fiche par lignée (#836), et la
page a été reconstruite en maquette avec elle, seize versions annotées. Ce qui a
été tranché, avec ses mesures : `docs/decisions/fiche-de-lignee-ui-329.md`.

Les garanties éditoriales de la fiche par législature SURVIVENT à la refonte, et
ce fichier les garde :

  1. **Les absences ne franchissent jamais l'écran** — ni l'adaptateur, ni la
     projection, ni le composant ne lisent `absents` ou `excuses` (§2 règle 3).
  2. **Aucun taux synthétique ne sort du fichier** (§2 règle 1).
  3. **Déposer comme rapporteur et comme député sont deux actes** : jamais
     additionnés, jamais un taux d'adoption commun (`AGENTS.md` §6).
  4. **La posture est recopiée, jamais déduite** (#686).
  5. **« Nuance » n'est pas « opposé »**, et les convergences se rangent par
     nombre de textes communs, jamais par accord.
  6. **La fiche ne nomme jamais qui s'est écarté de la ligne** (§2 règle 7).

Et elle garde ce que la refonte a décidé :

  7. **Une lignée DÉCLARÉE**, lue dans `pivot_data/lignees/`, jamais un
     chaînage de `succede_a` refait par l'interface ; une adresse de fiche par
     législature mène à sa lignée.
  8. **Une projection de build**, calculée par les règles de `utils/` que le
     navigateur importe — jamais une seconde écriture des nombres.
  9. **Le raisonnement en méthodologie**, une ancre par section ; la fiche garde
     la limite et le renvoi (règle de forme 2).

Ces tests lisent le **code exécuté** : les commentaires sont retirés avant toute
assertion. Le comportement des règles est vérifié à part, en les exécutant,
dans `tests/test_regles_de_lignee_329.py`.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale"
SRC = UI / "src"

MODULE_REGLES_GROUPE = SRC / "utils" / "groupe.js"
MODULE_REGLES_LIGNEE = SRC / "utils" / "lignee.js"
MODULE_REGLES_LECTURE = SRC / "utils" / "lecture.js"
COMPOSANT = SRC / "components" / "LigneeProfile.jsx"
FEUILLE = SRC / "components" / "LigneeProfile.css"
PAGE = SRC / "pages" / "GroupProfilePage.jsx"
CHARGEUR = SRC / "data" / "index.js"
ADAPTATEUR = SRC / "data" / "pivotAdapter.js"
METHODO = SRC / "pages" / "MethodologyPage.jsx"
PROJECTION = UI / "scripts" / "vue-lignee.mjs"
AMENDEMENTS = UI / "scripts" / "amendements-lignees.mjs"
COMPARAISON = UI / "scripts" / "comparaison-groupes.mjs"
SYNC = UI / "scripts" / "sync-data.mjs"

#: Les six sections, dans l'ordre où la fiche les rend.
SECTIONS = (
    "Qui sont-ils",
    "Sur quoi ils ont pris la parole",
    "Ce qu'ils ont proposé",
    "Ce qu'ils ont voté",
    "Avec qui ils votent",
    "Ce qu'on n'a pas pu lire",
)

#: Une ancre de méthodologie par section — minuscules seules : c'est la forme
#: que `test_pourquoi_en_methodologie_328` sait vérifier.
ANCRES = ("lignee", "paroles", "depots", "cohesion", "convergences")

DECOMPTES_INTERDITS = ("absents", "excuses")
TAUX_INTERDITS = ("taux_coherence", "taux_coherence_hors_absents", "taux_participation")


def sans_commentaires(source: str) -> str:
    """Le code exécuté seul : ni `/* … */`, ni `// …`, ni `{/* … */}` de JSX.

    Le retrait de `//` épargne les `://` (une URL n'est pas un commentaire).
    """
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"(?<!:)//[^\n]*", "", source)


def lire(chemin: Path) -> str:
    return sans_commentaires(chemin.read_text(encoding="utf-8"))


def corps(source: str, signature: str) -> str:
    """Le corps d'une fonction de premier niveau, jusqu'à l'accolade de colonne 0."""
    debut = source.index(signature)
    fin = source.index("\n}\n", debut)
    return source[debut:fin]


@pytest.fixture(scope="module")
def regles() -> str:
    return lire(MODULE_REGLES_GROUPE)


@pytest.fixture(scope="module")
def regles_lignee() -> str:
    return lire(MODULE_REGLES_LIGNEE)


@pytest.fixture(scope="module")
def composant() -> str:
    return lire(COMPOSANT)


@pytest.fixture(scope="module")
def projection() -> str:
    return lire(PROJECTION)


@pytest.fixture(scope="module")
def amendements() -> str:
    return lire(AMENDEMENTS)


@pytest.fixture(scope="module")
def sync() -> str:
    return lire(SYNC)


# ── Les modules, et une seule écriture de chaque règle ──────────────────────

def test_les_modules_de_la_fiche_existent():
    for chemin in (MODULE_REGLES_GROUPE, MODULE_REGLES_LIGNEE, MODULE_REGLES_LECTURE,
                   COMPOSANT, FEUILLE, PROJECTION, AMENDEMENTS, COMPARAISON):
        assert chemin.is_file(), f"{chemin} est attendu par #329"


def test_l_ancienne_fiche_par_legislature_est_partie():
    """Deux fiches pour le même groupe se liraient comme deux groupes."""
    assert not (SRC / "components" / "GroupProfile.jsx").exists()
    assert "buildGroupView" not in lire(ADAPTATEUR)


def test_les_regles_sont_importables_par_node_et_par_vite(regles, regles_lignee):
    """La projection de build importe les MÊMES règles que le navigateur : Node
    exige l'extension, Vite l'accepte. Sans elle, le build réécrirait la règle."""
    assert "from './lecture.js'" in regles, (
        "`utils/groupe.js` importe les primitives du lot 1 — avec l'extension, "
        "que Node exige pour la projection de build"
    )
    assert "from './lecture.js'" in regles_lignee
    for primitive in ("ratio", "formatNumber", "isWholeTextVote", "normalizeLabel"):
        for source, nom in ((regles, "groupe.js"), (regles_lignee, "lignee.js")):
            assert not re.search(rf"^\s*(export\s+)?function\s+{primitive}\s*\(", source, flags=re.M), (
                f"`{primitive}` est une primitive du lot 1 : {nom} ne la redéfinit pas"
            )


def test_la_projection_calcule_par_les_regles_de_l_interface(projection, amendements):
    """Un nombre écrit deux fois diverge au premier ajustement (#672)."""
    assert "from '../src/utils/groupe.js'" in projection
    assert "from '../src/utils/lignee.js'" in projection
    assert "from '../src/utils/lignee.js'" in amendements
    for regle in ("partageDuGroupe(", "quorumDeLaFiche(", "convergences(", "scrutinsParNature(",
                  "scrutinsParPartage(", "etiquettesThematiques(", "postureDuGroupe(",
                  "effectifDuGroupe(", "dateDeReference(", "couvertureRoster(",
                  "serieEffectif(", "personnesParMaillon("):
        assert regle in projection, f"la projection doit appeler `{regle.rstrip('(')}`, pas la réécrire"


def test_le_composant_ne_recalcule_rien(composant):
    """La page REND : ses nombres arrivent dans la projection."""
    assert "'../utils/lecture'" in composant and "'../utils/lignee'" in composant
    for calcul in ("partageDuGroupe(", "convergences(", "quorumDeLaFiche(", "repartitionParCommission("):
        assert calcul not in composant, f"`{calcul.rstrip('(')}` est calculé au build, pas à l'écran"


# ── Les six sections, dans l'ordre ───────────────────────────────────────────

def test_les_six_sections_sont_rendues_dans_l_ordre(composant):
    positions = []
    for titre in SECTIONS:
        motif = re.escape(titre).replace("\\'", "'").replace("'", "['’]")
        trouve = re.search(rf'titre="{motif}"', composant)
        assert trouve, f"la section « {titre} » a disparu du rendu (#329)"
        positions.append(trouve.start())
    assert positions == sorted(positions), f"les sections doivent se suivre ainsi : {SECTIONS}"


def test_le_quorum_ouvre_la_section_des_votes(composant):
    """Tout ce qui suit dépend du quorum : il vient avant la barre de partage."""
    vote = corps(composant, "function CeQuIlsOntVote(")
    assert vote.index("le quorum du groupe est atteint") < vote.index("lp-trois"), (
        "le quorum ouvre la section des votes, avant tout décompte de partage"
    )


# ── 1. Les absences ne franchissent jamais l'écran ──────────────────────────

def test_les_deux_decomptes_interdits_sont_nommes_dans_les_regles(regles):
    bloc = re.search(r"DECOMPTES_JAMAIS_PUBLIES\s*=\s*\[(.*?)\];", regles, flags=re.DOTALL)
    assert bloc, "`DECOMPTES_JAMAIS_PUBLIES` déclare les décomptes que la page ne publie pas"
    assert tuple(re.findall(r"'(\w+)'", bloc.group(1))) == DECOMPTES_INTERDITS


@pytest.mark.parametrize("decompte", DECOMPTES_INTERDITS)
def test_aucune_absence_n_est_lue_par_la_fiche(decompte, composant, projection, amendements, regles_lignee):
    """Un libellé prudent sur une donnée interdite reste la donnée interdite."""
    for source, nom in (
        (composant, COMPOSANT.name),
        (projection, PROJECTION.name),
        (amendements, AMENDEMENTS.name),
        (regles_lignee, MODULE_REGLES_LIGNEE.name),
        (lire(COMPARAISON), COMPARAISON.name),
    ):
        assert not re.search(rf"[.\[]\s*'?{decompte}'?\s*\]?", source), (
            f"`{decompte}` est lu dans {nom} : publié, agrégé ou non, ce décompte devient "
            "un taux de présence sur des personnes nommées (AGENTS.md §2 règle 3)"
        )


def test_les_largeurs_affichees_ne_rapportent_rien_aux_membres_eligibles(regles):
    bloc = corps(regles, "export function partageDuGroupe(groupe)")
    assert "/ total" in bloc, "la part de chaque position se calcule sur les voix EXPRIMÉES"
    assert not re.search(r"/\s*(entree\.)?membres_eligibles", bloc)


# ── 2. Aucun taux synthétique ────────────────────────────────────────────────

@pytest.mark.parametrize("taux", TAUX_INTERDITS)
def test_aucun_taux_synthetique_n_atteint_l_ecran(taux, regles, regles_lignee, composant, projection):
    for source, nom in ((regles, "groupe.js"), (regles_lignee, "lignee.js"),
                        (composant, COMPOSANT.name), (projection, PROJECTION.name)):
        assert taux not in source, (
            f"`{taux}` est lu dans {nom} : un chiffre unique par groupe est une note, et "
            "treize notes sont un classement (AGENTS.md §2 règle 1)"
        )


def test_la_cohesion_ne_se_publie_pas_en_barre_de_progression(composant):
    feuille = lire(FEUILLE)
    for source in (composant, feuille):
        assert "coherence" not in source, (
            "une barre de cohésion place les positions sur une échelle du pire au "
            "meilleur (AGENTS.md §2 règle 1)"
        )


# ── 3. Rapporteur et député ne s'additionnent pas ───────────────────────────

def test_les_types_de_deposant_restent_separes(regles_lignee, composant, amendements, projection):
    bloc = re.search(r"TYPES_DEPOSANT_GROUPE\s*=\s*\[(.*?)\];", regles_lignee, flags=re.DOTALL)
    assert bloc and re.findall(r"'(\w+)'", bloc.group(1)) == ["depute", "commission_rapporteur"], (
        "les deux types qu'un groupe porte ; `gouvernement` n'en est pas un — sa ligne « 0 » "
        "ne disait rien au lecteur (règle de forme 1)"
    )
    # Depuis la relecture du 11/09/2026, les deux types se sélectionnent
    # ENSEMBLE et les comptes portent alors sur les deux réunis. La réunion est
    # une RÈGLE (`cumulerTypes`), exécutée par `test_regles_de_lignee_329` ; le
    # composant ne l'écrit pas une seconde fois.
    propose = corps(composant, "function CeQuIlsOntPropose(")
    assert "cumulerTypes(m.amendements.parType, selection)" in propose
    assert not re.search(r"\.amendements\s*\+|adoptes\s*\+|\.reduce\(", propose), (
        "le composant n'additionne rien : la règle le fait, une fois"
    )
    for source, nom in ((composant, COMPOSANT.name), (amendements, AMENDEMENTS.name),
                        (projection, PROJECTION.name), (regles_lignee, "lignee.js")):
        assert "taux_adoption" not in source, f"`taux_adoption` atteint {nom} (AGENTS.md §6)"


def test_la_repartition_par_commission_ne_se_publie_que_verifiee(amendements):
    """Une seconde écriture de #821 n'est tolérable que si elle retombe sur le publié."""
    assert "par_type_deposant" in amendements and "nb_amendements" in amendements
    assert "recompte !== attendu" in amendements, (
        "chaque type recompté se compare au total que la fiche publie"
    )
    assert "verifies[type] = types[type]" in amendements, (
        "seul un type qui retombe sur le publié est servi ; un écart n'est pas arrondi"
    )


# ── 4. La posture est recopiée, jamais déduite ──────────────────────────────

def test_une_posture_absente_se_declare_et_ne_se_replie_sur_rien(regles):
    bloc = corps(regles, "export function postureDuGroupe(groupe)")
    assert "declaree: false" in bloc and "position_politique" in bloc
    for signal in ("cohesion_votes", "position_majoritaire", "convergences("):
        assert signal not in bloc, f"`{signal}` : une posture ne se déduit JAMAIS d'un vote (§2 règle 1)"


def test_non_declaree_reste_distincte_d_un_champ_absent(regles, regles_lignee):
    assert "non_declaree" in regles and "'Posture non publiée'" in regles
    bloc = corps(regles_lignee, "export function motifDePosture(posture)")
    assert "posture?.declaree" in bloc and "'absente'" in bloc, (
        "une fiche qui ne porte pas le champ n'a pas de motif : « l'Assemblée ne l'a pas "
        "déclaré » n'est pas « notre fiche ne porte pas le champ » (§2 règle 5)"
    )
    for signal in ("cohesion", "vote", "amendement"):
        assert signal not in bloc, "le motif se lit sur la posture déclarée, rien d'autre"


# ── 5. Les convergences ──────────────────────────────────────────────────────

def test_l_ordre_des_convergences_est_celui_des_textes_communs_puis_de_l_accord(regles):
    """Relecture du 11/09/2026 : l'accord DÉPARTAGE, il ne classe pas.

    Trier sur l'accord seul rangerait des parts calculées sur des bases
    différentes — un classement des alliés (§2 règle 1). À nombre de textes
    communs égal, le dénominateur est le même, et l'accord se compare."""
    bloc = corps(regles, "export function convergences(comparaison, sigleDuGroupe)")
    tri = re.search(r"\.sort\(\(a, b\) => (.*?)\);", bloc, flags=re.DOTALL)
    assert tri, "le tri des convergences a disparu"
    cles = [c.strip() for c in tri.group(1).split("||")]
    assert cles[0] == "b.communs - a.communs", "le nombre de textes communs range d'abord"
    assert cles[1] == "memeSens(b) - memeSens(a)", "l'accord départage, et seulement ensuite"
    assert "localeCompare" in cles[2], "puis le sigle, jamais l'ordre d'insertion"


def test_une_abstention_n_est_jamais_comptee_comme_un_vote_contraire(regles):
    bloc = corps(regles, "export function natureDeConvergence(positionA, positionB)")
    oppose = bloc[bloc.index("return 'oppose'") - 400: bloc.index("return 'oppose'")]
    assert "abstention" not in oppose, "« opposé » ne se prononce que sur pour / contre"
    assert "'autres'" in bloc, "un couple que les trois natures ne décrivent pas se compte à part"


def test_les_convergences_ne_comparent_que_la_derniere_lecture(projection, sync):
    """Un texte, une position (#711) — relecture de la propriétaire, 11/09/2026."""
    assert "selectDerniereLectureVotes(" in sync, (
        "la dernière lecture se choisit sur le corpus ENTIER des scrutins, une fois, au build"
    )
    bloc = corps(projection, "function convergencesDeroulables(")
    assert "dernieres.has(id)" in bloc and bloc.index("dernieres.has(id)") < bloc.index("scrutinsParNature("), (
        "le filtre porte sur la projection AVANT les règles de `groupe.js` : un compte et sa "
        "liste restent le même nombre par construction"
    )


def test_la_comparaison_ne_transporte_que_ce_qui_a_atteint_son_quorum():
    assert "quorum_atteint !== true" in lire(COMPARAISON)


# ── 6. La fiche ne nomme jamais qui s'est écarté ────────────────────────────

def test_le_nombre_de_voix_minoritaires_range_et_ne_sort_jamais(regles, projection, composant):
    partage = corps(regles, "export function partageDuGroupe(groupe)")
    assert "membre" not in partage.replace("membres_eligibles", "")
    listes = corps(regles, "export function scrutinsParPartage(")
    assert "l.map((x) => x.entree)" in listes, (
        "`scrutinsParPartage` range sur les voix minoritaires et ne rend que l'entrée : un "
        "« nombre de dissidents » publié serait l'indice individuel de §2 règle 7"
    )
    for source, nom in ((projection, PROJECTION.name), (composant, COMPOSANT.name)):
        assert "minoritaires" not in source, f"le nombre de voix minoritaires atteint {nom}"
    assert "ecartsAvecLeGroupe" not in composant


# ── 7. Une lignée déclarée ───────────────────────────────────────────────────

def test_les_lignees_sont_lues_et_jamais_rechainees(sync):
    """Le chaînage de `succede_a` coïncidait avec les 13 lignées déclarées le
    11/09/2026 — jusqu'à la première scission (#815), où il divergerait."""
    assert "'pivot_data', 'lignees'" in sync or '"pivot_data", "lignees"' in sync
    assert "succede_a" not in sync, "l'interface ne rechaîne plus les fiches : elle lit les lignées"
    assert "ligneeTete" not in sync and "ligneeTete" not in lire(CHARGEUR)


def test_une_adresse_de_fiche_par_legislature_mene_a_sa_lignee():
    page = lire(PAGE)
    assert "ligneeDeLaFiche(" in page and "<Navigate" in page and "replace" in page, (
        "un lien partagé vers `/groupes/AN-SOC-17` ne casse pas parce que le découpage a changé"
    )


def test_la_barre_des_groupes_donne_une_entree_par_lignee():
    chargeur = lire(CHARGEUR)
    bloc = corps(chargeur, "export async function getGroupsList()")
    assert "manifest.lignees" in bloc and "fiches:" in bloc, (
        "une entrée par lignée, avec ses fiches — le filtre des candidats en dépend"
    )
    assert "groupIds: c.groupIds" in corps(chargeur, "export async function getCandidatesList()"), (
        "sans `groupIds`, sélectionner un groupe ne retenait aucun candidat"
    )


# ── 8. Les limites sur la fiche, le raisonnement en méthodologie ─────────────

def test_chaque_section_renvoie_a_son_ancre_de_methodologie(composant):
    methodo = lire(METHODO)
    for ancre in ANCRES:
        assert f"id: '{ancre}'" in methodo, f"l'ancre #{ancre} manque à la méthodologie"
        assert f"ancre: '{ancre}'" in composant, f"aucune section ne renvoie à #{ancre}"


def test_les_refus_de_la_fiche_de_groupe_vivent_en_methodologie(regles, composant):
    assert "'indice-de-cohesion'" in regles and "'ecarts-individuels'" in regles
    assert "REFUS_FICHE_GROUPE.map" in lire(METHODO), (
        "ce qui est interdit est écrit — en méthodologie, une fois, plus sur la fiche"
    )
    assert "REFUS_FICHE_GROUPE" not in composant


def test_une_etiquette_part_avec_son_nombre_de_porteurs(composant):
    assert "t.porteurs" in composant and "t.denominateur" in composant
    assert "poids_relatif" not in composant
    assert "jamais des positions du groupe" in re.sub(r"\s+", " ", composant), (
        "ce sont des sujets d'intervention, jamais des positions du groupe (§2 règle 8)"
    )


def test_l_intitule_porte_le_lien_de_source(composant):
    """Relecture du 11/09/2026 : plus de badge « Source » sous chaque ligne."""
    assert "function LienSource(" in composant and "BadgeSource" not in composant
    assert "lien de source non publié" in composant, (
        "sans URL publiée, l'intitulé le dit — « non publié » parle de nous (DESIGN_SYSTEM §5)"
    )


def test_ce_qu_on_n_a_pas_pu_lire_renvoie_le_corpus_a_la_page_de_couverture(projection, composant):
    """Le partage de `page-couverture-commune-328` : la fiche ne garde que ce
    que CHAQUE fiche signale d'elle-même ; ce qui vaut pour tout le corpus vit
    sur `/couverture`, le pourquoi sous `/methodologie#couverture`."""
    assert "signalementsDuMaillon(groupe)" in projection
    section = corps(composant, "function CeQuOnNaPasPuLire(")
    assert "vers: '/sources#frise'" in section and "vers: '/methodologie#couverture'" in section
    assert "m.signalements" in section, "la section rend la projection, elle ne relit pas les avertissements"
    assert "warnings" not in section


def test_les_textes_portes_reprennent_la_figure_et_la_regle_de_la_fiche_candidat(projection, composant):
    """La même cascade (`CascadeTextes.jsx`) et la même règle (`textesPortes`) :
    une figure recopiée divergerait au premier correctif."""
    assert "import { Cascade, ListeCascade } from './CascadeTextes'" in composant
    assert "textesPortes(" in composant and "textesDesQualites(" in composant
    assert "function Cascade(" not in composant
    candidat = lire(SRC / "components" / "CandidateProfile.jsx")
    assert "from './CascadeTextes'" in candidat and "function Cascade(" not in candidat
    assert "textes: repartitions.get(maillon.fichier)?.textes ?? null" in projection
    assert "ne sont pas collectés" not in composant, "les textes portés des membres sont collectés depuis #835"


def test_un_maillon_sans_liste_dit_pourquoi(projection, composant):
    assert "couvertureRoster(groupe)" in projection
    assert "causeListeVide" in composant, "une liste vide dit POURQUOI (#326)"


def test_aucun_compteur_publie_ne_se_dit_actuel(composant):
    assert not re.search(r"'[^']*[Aa]ctuel", composant), (
        "un compteur « actuel » mesurait la carrière ultérieure des membres (#653)"
    )


# ── Les fonctions exercées : retirées de la page, pas des règles ─────────────
#
# La section « instances et fonctions » est retirée tant que `mandats_agreges`
# compte la carrière des membres et non leur passage dans le groupe (#853). Les
# règles restent : elles reviendront avec la section, et leur garde avec elles.

def test_un_libelle_de_fonction_inconnu_tombe_dans_autre_et_jamais_dans_le_vide(regles):
    bloc = corps(regles, "export function classeDeFonction(libelle)")
    assert bloc.rstrip().endswith("return 'autre';"), (
        "un libellé que la table ne reconnaît pas tombe dans `autre`, jamais ignoré"
    )
    ordre = re.search(r"ORDRE_CLASSES_FONCTION\s*=\s*\[(.*?)\];", regles, flags=re.DOTALL)
    assert ordre and "'autre'" in ordre.group(1)


def test_la_classe_autre_garde_les_intitules_de_la_source(regles):
    assert re.search(r"libelles:\s*\[", regles), (
        "`fonctionsDuGroupe` conserve les intitulés d'origine de chaque classe"
    )


def test_la_table_des_fonctions_ne_reconnait_pas_un_prefixe_de_presidence(regles):
    prefixes = re.search(r"PREFIXES_SIEGE\s*=\s*\[(.*?)\];", regles, flags=re.DOTALL)
    assert prefixes and "'membre de droit'" in prefixes.group(1)
