"""Un membre de roster sans correspondance relue reçoit un slug (#708).

## Ce que ce fichier verrouille

`build_roster_candidats_detaille` écarte un membre sans slug **depuis
toujours**, et c'était inoffensif tant que NosDéputés servait le roster avec
ses slugs. #527 a basculé la source sur AMO30, qui ne publie qu'un `PA######`
et de l'état civil — et l'exclusion est devenue muette, parce que la table qui
donne les slugs (`raw_data/correspondance_acteurs_an.json`, #525) est
construite depuis les profils **publiés** : il fallait un profil pour avoir un
slug, et un slug pour avoir un profil.

Quatre invariants, et aucun n'est décoratif :

1. **le slug se fabrique avec `text_utils.slugify`**, la seule fabrique de
   slugs du dépôt — pas une seconde, pas une variante ;
2. **la table passe devant**, toujours : un slug déjà relu ne se refabrique pas
   quand le nom d'usage change (#487, #668, #540 — trois défauts de la même
   famille) ;
3. **une collision ne s'attribue jamais en silence** : trois motifs fermés,
   nommés, comptés ;
4. **`membres_sans_slug` reste vrai** — il compte ce qui reste réellement
   écarté, jamais zéro par construction.

## Les fixtures

L'archive est `tests/fixtures/amo30_gp_leg16_17.zip`, la **réduction** de
l'archive réelle utilisée par `tests/test_an_roster.py` (#510 : une fixture de
ce chemin se réduit, elle ne se rédige pas). Les tables de correspondance de
collision, elles, sont écrites en `tmp_path` : ce sont des fichiers de
configuration de ce dépôt, pas un schéma que l'Assemblée publie, et le corpus
réel ne porte **aucune** collision aujourd'hui — ce que le dernier test mesure
plutôt que de le supposer.

Aucun réseau, aucune lecture de `pivot_data/` ni de `raw_data/profiles/`, et
`raw_data/correspondance_acteurs_an.json` n'est pas lue non plus : elle est
hors du sparse-checkout de `tests.yml`.
"""

import json
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

import an_roster  # noqa: E402
import correspondance_acteurs_an  # noqa: E402
import group_roster  # noqa: E402
import text_utils  # noqa: E402
from generate_roster_candidats import (  # noqa: E402
    membres_sans_slug,
    membres_slug_fabrique,
    resume_membres_slug_fabrique,
)

#: Ce fichier de tests lit la configuration committée nommée ci-dessous.
#: Le garde-fou de `conftest.py` refuse tout `.json` de `raw_data/` qu'un
#: test n'a pas déclaré (#791), et n'accepte la déclaration que si le chemin
#: est dans le `sparse-checkout` de `tests.yml` — sinon le test ne tournerait
#: qu'en local, sur ce qu'un run y a laissé.
pytestmark = pytest.mark.lit_reference_committee("raw_data/groupes_reels.json")

ARCHIVE = Path(__file__).resolve().parent / "fixtures" / "amo30_gp_leg16_17.zip"
CORRESPONDANCE = (
    Path(__file__).resolve().parent / "fixtures" / "correspondance_acteurs_an_extrait.json"
)
CONFIG = RACINE / "raw_data" / "groupes_reels.json"

#: Nicolas Forissier, `LR` 16e — présent dans l'archive réduite, **absent** de
#: la table de correspondance : c'est exactement le cas que #708 ouvre.
FORISSIER = "PA1327"


@pytest.fixture(autouse=True)
def _memos_propres():
    an_roster.vider_memo()
    correspondance_acteurs_an.vider_memo()
    yield
    an_roster.vider_memo()
    correspondance_acteurs_an.vider_memo()


@pytest.fixture
def actif(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    an_roster.activer_roster_an(True)
    yield tmp_path
    an_roster.activer_roster_an(True)


@pytest.fixture
def index(actif):
    return an_roster.charger_index_gp(ARCHIVE)


def _table(tmp_path, correspondances):
    """Écrit une table de correspondance au format committé, en `tmp_path`."""
    chemin = tmp_path / "correspondance.json"
    chemin.write_text(
        json.dumps(
            {
                "schema_version": correspondance_acteurs_an.SCHEMA_VERSION,
                "genere_le": "2026-09-01",
                "source_referentiel": "fixture #708",
                "correspondances": correspondances,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return chemin


def _entree(acteur_ref, *, ecart=None, motif=None):
    entree = {
        "acteur_ref": acteur_ref,
        "etat_civil": {"nom_complet": "peu importe"},
        "preuve": "https://www.assemblee-nationale.fr/dyn/deputes/PA0",
        "verifie_le": "2026-09-01",
    }
    if ecart:
        entree["ecart"] = ecart
        entree["motif"] = motif or "fixture"
    return entree


# --------------------------------------------------------------------------
# 1. Il n'y a qu'une seule fabrique de slugs dans ce dépôt
# --------------------------------------------------------------------------

def test_le_slug_est_fabrique_par_la_fonction_du_depot():
    """`an_roster.slugify` **est** `text_utils.slugify`, pas une copie.

    Une seconde fabrique dériverait le jour où l'une des deux est corrigée, et
    le slug est le nom de fichier du profil (#487) : deux conventions, deux
    fichiers pour une personne.
    """
    assert an_roster.slugify is text_utils.slugify


def test_le_slug_fabrique_est_bien_slugify_de_letat_civil(index):
    slugs, origines, non_attribues = an_roster.resoudre_slugs(index, CORRESPONDANCE)
    assert non_attribues == []
    assert origines[FORISSIER] == "fabrique"
    assert slugs[FORISSIER] == text_utils.slugify(index["acteurs"][FORISSIER])
    assert slugs[FORISSIER] == "nicolas-forissier"


def test_lorigine_du_slug_est_un_vocabulaire_ferme(index):
    _, origines, _ = an_roster.resoudre_slugs(index, CORRESPONDANCE)
    assert set(origines.values()) <= an_roster.ORIGINES_SLUG
    assert set(origines.values()) == {"table", "fabrique"}


# --------------------------------------------------------------------------
# 2. La table passe devant — un nom qui bouge ne déplace pas un identifiant
# --------------------------------------------------------------------------
#
# C'est le piège de #487 (un `id` qui changeait de valeur sur une carrière
# inchangée), de #668 (une clé `a or b` qui change de branche le jour où `a` se
# remplit) et de #540 (une clé collante). Le slug est le nom du fichier publié :
# le déplacer, c'est publier deux fois la même personne — ou perdre la première.

def test_un_nom_qui_change_ne_deplace_pas_un_slug_deja_relu(index, tmp_path):
    """`PA1327` est relu sous un slug qui ne ressemble plus à son état civil.

    L'archive dit « Nicolas Forissier » ; la table dit `nicolas-forissier-1789`.
    C'est la table qui décide, sans discussion — sinon le premier changement de
    nom d'usage renommerait un profil publié, ce qu'`audit_diff_profils` lit
    comme une **disparition** (#460/#470).
    """
    chemin = _table(tmp_path, {"nicolas-forissier-1789": _entree(FORISSIER)})
    slugs, origines, non_attribues = an_roster.resoudre_slugs(index, chemin)

    assert slugs[FORISSIER] == "nicolas-forissier-1789"
    assert origines[FORISSIER] == "table"
    assert text_utils.slugify(index["acteurs"][FORISSIER]) != slugs[FORISSIER]
    assert all(n["acteur_ref"] != FORISSIER for n in non_attribues)


def test_le_slug_fabrique_ne_depend_pas_des_groupes_configures(index, tmp_path):
    """L'univers de résolution est l'index entier, jamais un sous-ensemble.

    Un identifiant qui dépendrait de la config changerait de valeur le jour où
    la config change. La preuve : le slug de `PA1327` est le même que le roster
    demandé soit `LR-16` (son groupe) ou `RN-17` (où il n'est pas).
    """
    chemin = _table(tmp_path, {})
    slugs_a, _, _ = an_roster.resoudre_slugs(index, chemin)
    membres_lr, _ = an_roster.deriver_roster_groupe(
        "LR", "16", zip_path=ARCHIVE, chemin_config=CONFIG, chemin_correspondance=chemin
    )
    membres_rn, _ = an_roster.deriver_roster_groupe(
        "RN", "17", zip_path=ARCHIVE, chemin_config=CONFIG, chemin_correspondance=chemin
    )
    dans_lr = {m["acteur_ref"]: m["slug"] for m in membres_lr}
    assert dans_lr[FORISSIER] == slugs_a[FORISSIER] == "nicolas-forissier"
    assert FORISSIER not in {m["acteur_ref"] for m in membres_rn}


# --------------------------------------------------------------------------
# 3. Une collision ne s'attribue jamais en silence
# --------------------------------------------------------------------------

def test_un_slug_deja_porte_par_quelquun_dautre_nest_jamais_attribue(index, tmp_path):
    """Le cas nommé par #525 §5 : « une deuxième Alexandra Martin élue ».

    Attribuer ici, ce serait écrire les votes d'une personne dans le profil
    d'une autre — la clé collante de #540, sur le seul identifiant que le dépôt
    possède.
    """
    chemin = _table(tmp_path, {"nicolas-forissier": _entree("PA999999")})
    slugs, origines, non_attribues = an_roster.resoudre_slugs(index, chemin)

    assert FORISSIER not in slugs
    assert FORISSIER not in origines
    (refuse,) = [n for n in non_attribues if n["acteur_ref"] == FORISSIER]
    assert refuse["motif"] == "slug_deja_publie"
    assert refuse["slug_vise"] == "nicolas-forissier"
    assert refuse["nom"], "un refus nomme la personne, jamais un simple identifiant"
    assert "PA999999" in refuse["detail"]


def test_le_slug_quon_porte_deja_soi_meme_nest_pas_une_collision(index, tmp_path):
    """L'autre moitié de #525 §5, et c'est elle qui décide qui entre.

    Une collision est un slug porté par **quelqu'un d'autre**. Le même slug
    porté par la **même** personne n'en est pas une : `PA1327` est relu sous
    `nicolas-forissier`, exactement ce que `slugify` aurait fabriqué. Rien ne
    doit l'écarter — il sort avec son slug, en origine `table`.

    Ce n'est pas une redondance de `test_un_nom_qui_change...` : là-bas la
    table diverge de l'état civil, ici elle coïncide, et c'est la coïncidence
    qui rend le faux positif possible. Inverser l'ordre de `resoudre_slugs` —
    contrôler la collision avant de consulter la table — écarterait d'un coup
    tous les membres déjà publiés, avec le motif `slug_deja_publie` pointant
    sur eux-mêmes.
    """
    chemin = _table(tmp_path, {"nicolas-forissier": _entree(FORISSIER)})
    slugs, origines, non_attribues = an_roster.resoudre_slugs(index, chemin)

    assert slugs[FORISSIER] == "nicolas-forissier" == text_utils.slugify(
        index["acteurs"][FORISSIER]
    )
    assert origines[FORISSIER] == "table"
    assert non_attribues == []


def test_un_slug_declare_hors_an_bloque_aussi(index, tmp_path):
    """`jordan-bardella` porte `acteur_ref: null` et `ecart: hors_an` (#525).

    Un acteur AMO30 qui viserait ce slug est soit une autre personne, soit une
    déclaration périmée. Les deux se relisent ; aucune ne s'attribue.
    """
    chemin = _table(
        tmp_path,
        {"nicolas-forissier": _entree(None, ecart="hors_an", motif="député européen")},
    )
    _, _, non_attribues = an_roster.resoudre_slugs(index, chemin)
    (refuse,) = [n for n in non_attribues if n["acteur_ref"] == FORISSIER]
    assert refuse["motif"] == "slug_deja_publie"


def test_deux_acteurs_sans_entree_visant_le_meme_slug_sont_tous_deux_refuses(tmp_path):
    """L'homonymie entre deux **nouveaux** : ni l'un ni l'autre ne l'emporte.

    L'ordre alphabétique des `acteur_ref` donnerait un gagnant, et ce gagnant
    changerait le jour où l'AN attribue un `PA######` plus petit : un
    identifiant tiré au sort est pire qu'un identifiant absent (§2 règle 5).

    L'index est ici un dictionnaire minimal et non une archive : `acteurs` est
    une forme que **ce module produit** (`construire_index_gp`), pas un schéma
    que l'Assemblée publie — la règle de #510 porte sur le second. Le corpus
    réel n'a aucune homonymie de ce type, ce que le dernier test mesure.
    """
    index = {"acteurs": {"PA111": "Jean Martin", "PA222": "Jean Martin"}}
    chemin = _table(tmp_path, {})
    slugs, origines, non_attribues = an_roster.resoudre_slugs(index, chemin)

    assert slugs == {} and origines == {}
    assert {n["acteur_ref"] for n in non_attribues} == {"PA111", "PA222"}
    assert {n["motif"] for n in non_attribues} == {"homonymie_amo30"}
    assert all(n["slug_vise"] == "jean-martin" for n in non_attribues)
    assert "PA222" in [n for n in non_attribues if n["acteur_ref"] == "PA111"][0]["detail"]


def test_un_etat_civil_absent_ne_produit_aucun_slug(tmp_path):
    """Pas de nom, pas de slug — et surtout pas un slug vide (§2 règle 5)."""
    index = {"acteurs": {"PA111": "", "PA222": None}}
    slugs, _, non_attribues = an_roster.resoudre_slugs(index, _table(tmp_path, {}))
    assert slugs == {}
    assert {n["motif"] for n in non_attribues} == {"nom_absent"}
    assert {n["acteur_ref"] for n in non_attribues} == {"PA111", "PA222"}


def test_les_motifs_sont_un_vocabulaire_ferme(index, tmp_path):
    chemin = _table(tmp_path, {"nicolas-forissier": _entree("PA999999")})
    _, _, non_attribues = an_roster.resoudre_slugs(index, chemin)
    assert non_attribues
    assert {n["motif"] for n in non_attribues} <= an_roster.MOTIFS_SLUG_NON_ATTRIBUE


# --------------------------------------------------------------------------
# 4. `ROSTER_SANS_SLUG` reste vrai : il compte ce qui reste écarté
# --------------------------------------------------------------------------

def _rosters_bruts(chemin_correspondance, legislature="16"):
    roster = an_roster.fetch_full_roster_an(
        legislature,
        zip_path=ARCHIVE,
        chemin_config=CONFIG,
        chemin_correspondance=chemin_correspondance,
    )
    return {("deputes", legislature): roster}


_GROUPE_LR_16 = {
    "groupe_id": "AN:LR",
    "chambre": "AN",
    "groupe_sigle": "LR",
    "groupe_nom": "Les Républicains",
    "roster_chambre": "deputes",
    "legislature": "16",
}


def test_le_compteur_ne_tombe_pas_a_zero_par_construction(actif, tmp_path):
    """Une collision reste comptée par `membres_sans_slug` (#527, maintenu).

    C'est la garantie que #708 n'a pas *supprimé* le compteur en le
    satisfaisant : la seule façon de le faire mentir serait d'attribuer les
    collisions, ce que le §3 interdit.
    """
    chemin = _table(tmp_path, {"nicolas-forissier": _entree("PA999999")})
    bruts = _rosters_bruts(chemin)

    ecartes = membres_sans_slug([_GROUPE_LR_16], bruts)
    assert [m["nom"] for m in ecartes] == ["Nicolas Forissier"]
    assert all(m["groupe"] == "AN:LR" for m in ecartes)


def test_ce_qui_entre_par_la_porte_neuve_est_compte_et_nomme(actif, tmp_path):
    """Le miroir : une porte qui s'ouvre sans compteur est le trou de #510."""
    chemin = _table(tmp_path, {})
    bruts = _rosters_bruts(chemin)

    fabriques = membres_slug_fabrique([_GROUPE_LR_16], bruts)
    assert membres_sans_slug([_GROUPE_LR_16], bruts) == []
    assert len(fabriques) == 63, "les 63 membres LR-16 entrent tous par la fabrication"
    assert {m["groupe"] for m in fabriques} == {"AN:LR"}
    assert all(m["slug"] for m in fabriques)

    resume = resume_membres_slug_fabrique(fabriques)
    assert resume.startswith("ROSTER_SLUG_FABRIQUE — 63 membre(s)")
    assert "\n" not in resume, "une annotation GitHub Actions tient sur une ligne"
    assert "check_quality_gate" in resume or "§5b" in resume


def test_lorigine_traverse_le_filtre_par_sigle(actif, tmp_path):
    """Sans ce champ, `generate_roster_candidats` ne peut rien compter.

    `filter_roster_by_sigle` projette une liste blanche de champs : un champ
    qu'elle ne nomme pas disparaît en silence entre les deux étages.
    """
    chemin = _table(tmp_path, {"nicolas-forissier": _entree(FORISSIER)})
    roster = an_roster.fetch_full_roster_an(
        "16", zip_path=ARCHIVE, chemin_config=CONFIG, chemin_correspondance=chemin
    )
    filtre = group_roster.filter_roster_by_sigle(roster, "deputes", "LR")
    par_ref = {m["acteur_ref"]: m for m in filtre}
    assert par_ref[FORISSIER]["slug_origine"] == "table"
    assert {m["slug_origine"] for m in filtre} <= an_roster.ORIGINES_SLUG | {None}


# --------------------------------------------------------------------------
# 5. Ce que le corpus réduit mesure aujourd'hui
# --------------------------------------------------------------------------

def test_la_16e_et_la_17e_nont_aucune_collision_sur_larchive_reduite(index, tmp_path):
    """Le zéro est une **mesure**, pas une propriété du code.

    833 acteurs portant un mandat `GP` de la 16e ou de la 17e, table vide : si
    deux d'entre eux portaient le même état civil, ce test le dirait. Il vaut 0
    le 01/09/2026, et il vaudra 2 le jour où une deuxième *Alexandra Martin*
    est élue sans que l'AN la désambiguïse.
    """
    slugs, origines, non_attribues = an_roster.resoudre_slugs(index, _table(tmp_path, {}))
    assert non_attribues == []
    assert len(slugs) == len(index["acteurs"]) == 833
    assert len(set(slugs.values())) == 833, "833 acteurs, 833 slugs distincts"
    assert set(origines.values()) == {"fabrique"}


def test_les_rosters_de_la_17e_entrent_en_entier(actif):
    """Le défaut mesuré par #708 : 156 des 461 entrées écartées, 33,8 %.

    Avec la fixture (12 entrées de table seulement) la proportion n'est pas
    celle du corpus réel — ce qui se vérifie ici est **l'invariant** : plus
    aucun membre n'est écarté faute de slug, quel que soit le nombre de
    groupes déclarés sur la 17e. Ils étaient cinq, ils sont sept depuis #815 ;
    le total suit la table plutôt qu'une constante, sans quoi déclarer un
    groupe de plus ferait échouer un test qui ne parle pas de lui.
    """
    total = 0
    attendus = 0
    for entree in an_roster.charger_correspondance_sigles(CONFIG):
        if entree["legislature"] != "17":
            continue
        membres, rapport = an_roster.deriver_roster_groupe(
            entree["groupe_sigle"],
            "17",
            zip_path=ARCHIVE,
            chemin_config=CONFIG,
            chemin_correspondance=CORRESPONDANCE,
        )
        assert rapport["membres_sans_slug"] == []
        assert all(m["slug"] for m in membres)
        total += len(membres)
        attendus += entree["effectif_amo30"]
    assert total == attendus
