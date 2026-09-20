"""La composition des groupes AN dérivée d'AMO30 (#526), et sa bascule (#527).

Tout tourne sur `tests/fixtures/amo30_gp_leg16_17.zip`, **extraite de l'archive
réelle** téléchargée le 26/08/2026 à
`https://data.assemblee-nationale.fr/static/openData/repository/17/amo/`
`tous_acteurs_mandats_organes_xi_legislature/AMO30_tous_acteurs_tous_mandats_`
`tous_organes_historique.json.zip` (13,6 Mo, 3 119 acteurs).

Réduction, sans qu'une seule valeur soit inventée ni modifiée : **tous** les
organes `codeType == "GP"` (63, toutes législatures), et pour chaque acteur
portant au moins un mandat `GP` de la 16e ou de la 17e, son état civil et ses
seuls mandats `GP` de ces deux législatures (833 acteurs, 525 Ko). Elle porte
donc les trois pièges à leur taille réelle : les **592** acteurs de `NI` 16e,
les deux organes `SOC` successifs, et la 17e entière.

C'est délibérément une extraction et non une fixture écrite à la main : #510 a
coûté un défaut invisible pendant des mois parce que `syceron_minimal.xml`
décrivait un schéma que l'Assemblée ne publie pas. Une fixture de ce module ne
doit jamais être *rédigée* — seulement *réduite*.

Les législatures 13 à 15 sont hors de la fixture (leurs organes y sont, leurs
mandats non) : aucune mesure ne doit être prise sur elles ici.

Aucun réseau, aucune lecture de `pivot_data/` ni de `raw_data/profiles/`.
"""

import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

import an_roster  # noqa: E402
import group_roster  # noqa: E402

#: Ce fichier de tests lit la configuration committée nommée ci-dessous.
#: Le garde-fou de `conftest.py` refuse tout `.json` de `raw_data/` qu'un
#: test n'a pas déclaré (#791), et n'accepte la déclaration que si le chemin
#: est dans le `sparse-checkout` de `tests.yml` — sinon le test ne tournerait
#: qu'en local, sur ce qu'un run y a laissé.
pytestmark = pytest.mark.lit_reference_committee("raw_data/groupes_reels.json")

#: Le nombre d'entrées de `correspondance_sigles_an`, lu depuis le fichier
#: plutôt que figé (#777). Il valait 10 jusqu'aux huit groupes des XVe et XVIe ;
#: le figer obligeait à toucher quatre tests à chaque groupe publié, c'est-à-dire
#: à faire de la garde une formalité — et une formalité, on la met à jour sans la
#: lire. Ce qui compte n'est pas le nombre, c'est que la table et `groupes[]`
#: décrivent le MÊME ensemble : c'est ce que vérifie
#: `test_la_table_et_les_groupes_decrivent_le_meme_ensemble`.
def _entrees_committees() -> list:
    import json
    from pathlib import Path as _P
    racine = _P(__file__).resolve().parents[1]
    return json.loads((racine / "raw_data" / "groupes_reels.json").read_text(encoding="utf-8"))[
        "correspondance_sigles_an"
    ]["groupes"]


_ATTENDU = len(_entrees_committees())


ARCHIVE = Path(__file__).resolve().parent / "fixtures" / "amo30_gp_leg16_17.zip"
CORRESPONDANCE = (
    Path(__file__).resolve().parent / "fixtures" / "correspondance_acteurs_an_extrait.json"
)
CONFIG = RACINE / "raw_data" / "groupes_reels.json"

#: Organes de référence, tels que le référentiel AN les publie.
NI_16 = "PO793087"
NI_17 = "PO840056"
SOC_16 = "PO800496"
SOC_A_16 = "PO830170"


@pytest.fixture(autouse=True)
def _drapeau_restaure():
    """Le drapeau est un état de module : le rendre tel qu'il était."""
    initial = an_roster.AN_ROSTER_ACTIF
    an_roster.vider_memo()
    yield
    an_roster.activer_roster_an(initial)
    an_roster.vider_memo()


@pytest.fixture
def actif(tmp_path, monkeypatch):
    """Drapeau levé, et cache d'index dans un `tmp_path` — jamais dans le dépôt."""
    monkeypatch.chdir(tmp_path)
    an_roster.activer_roster_an(True)
    return tmp_path


@pytest.fixture
def index(actif):
    return an_roster.charger_index_gp(ARCHIVE)


def _roster(sigle, legislature):
    return an_roster.deriver_roster_groupe(
        sigle,
        legislature,
        zip_path=ARCHIVE,
        chemin_config=CONFIG,
        chemin_correspondance=CORRESPONDANCE,
    )


def _entrees_table(legislature=None):
    return [
        e
        for e in an_roster.charger_correspondance_sigles(CONFIG)
        if legislature is None or e["legislature"] == legislature
    ]


# --------------------------------------------------------------------------
# 1. Le drapeau : levé par #527, et « baissé » veut toujours dire refus bruyant
# --------------------------------------------------------------------------
#
# Les deux verrous que le lot 1 avait posés ici — drapeau `False`, aucun
# appelant dans `src/` — ont fait leur travail : ils ont obligé la bascule à
# être une PR à elle seule. Ils ne disparaissent pas pour autant, ils changent
# de valeur attendue. Un verrou qu'on retire le jour où il se déclenche
# n'aurait rien gardé du tout.

def test_le_drapeau_est_leve_dans_le_source():
    """La bascule du lot 1b (#527) EST cette ligne, et ce test la fige.

    Le lot 1 figeait `False` pour que la bascule soit une décision prise seule ;
    ce test fige `True` pour que le retour en arrière en soit une aussi.

    Ce que « baissé » veut dire a changé avec #529 : il n'y a plus de repli
    NosDéputés vers lequel basculer. Le drapeau est devenu un interrupteur —
    baissé, il n'y a plus de roster du tout, et le module refuse bruyamment.
    C'est ce refus, testé juste en dessous, qui reste sa seule raison d'être.
    """
    assert an_roster.AN_ROSTER_ACTIF is True


@pytest.mark.parametrize(
    "appel",
    [
        lambda: an_roster.fetch_full_roster_an("16", zip_path=ARCHIVE),
        lambda: an_roster.deriver_roster_groupe("LR", "16", zip_path=ARCHIVE),
        lambda: an_roster.rapport_divergence(zip_path=ARCHIVE),
    ],
)
def test_inactif_refuse_au_lieu_de_rendre_une_liste_vide(appel):
    """Un roster vide est indiscernable d'un groupe dissous, une fois écrit.

    C'est ce que #511 puis #524 ont payé : « collecte en échec » et « 0 membre »
    doivent rester deux faits différents (AGENTS §2 règle 5). Le drapeau est
    levé depuis #527, mais ce refus reste la seule réponse admise quand il est
    baissé — c'est lui qui rend le repli sûr.
    """
    an_roster.activer_roster_an(False)
    with pytest.raises(an_roster.RosterAnInactif) as exc:
        appel()
    assert "activer_roster_an" in str(exc.value)


#: Modules de `src/` autorisés à importer `an_roster`, et la raison de chacun.
#: Une liste, pas un `[]` : le verrou du lot 1 interdisait tout appelant, celui
#: du lot 1b interdit tout appelant **imprévu**. C'est le même verrou, à la
#: valeur près, et il continue de faire échouer la suite quand la source du
#: roster gagne un consommateur en douce.
APPELANTS_ATTENDUS = {
    # L'aiguillage lui-même : `fetch_full_roster` délègue la clé `deputes`.
    "group_roster.py",
    # #996 lot 2 : le roster des gouvernements réutilise `resoudre_slugs` au
    # lieu de le recopier — c'est ce qui garantit que la table de
    # correspondance passe devant et que l'univers de collision des slugs
    # reste entier, ministres et députés confondus.
    "gouvernement_roster_an.py",
    # #996 lot 2 : le producteur du roster brut télécharge l'archive et charge
    # l'index GP pour cette union.
    "generate_roster_candidats.py",
    # `group_profile.py` n'y est PLUS depuis #529. Il lisait le drapeau pour
    # choisir entre deux rédactions du `meta.warnings` de fraîcheur — celle
    # d'AMO30 et celle de NosDéputés. Le repli retiré, il n'y a plus qu'une
    # source à nommer, donc plus de drapeau à lire : l'avertissement est écrit
    # une fois pour toutes (AGENTS §2 règle 2, toujours respectée — c'est le
    # nombre de sources qui a changé, pas l'exigence).
}


def test_les_appelants_de_ce_module_sont_ceux_qu_on_attend():
    """Qui dérive le roster AN, nommément (#526 lot 1 → #527 lot 1b).

    Un drapeau se lève par mégarde ; une liste d'appelants, non. Le jour où un
    troisième module s'y branche, ce test échoue et demande qu'on écrive
    pourquoi.
    """
    import re

    importe = re.compile(r"^\s*(?:import an_roster|from an_roster import)", re.M)
    appelants = {
        chemin.name
        for chemin in (RACINE / "src").glob("*.py")
        if chemin.name != "an_roster.py" and importe.search(chemin.read_text(encoding="utf-8"))
    }
    assert appelants == APPELANTS_ATTENDUS, (
        f"Appelants inattendus : {sorted(appelants - APPELANTS_ATTENDUS)} ; "
        f"disparus : {sorted(APPELANTS_ATTENDUS - appelants)}. La source du "
        "roster AN se gagne ou se perd un consommateur par décision écrite."
    )


def test_le_cli_annonce_le_drapeau_et_ses_mesures():
    sortie = subprocess.run(
        [sys.executable, str(RACINE / "src" / "an_roster.py"), "--help"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    # `--activer-roster-an` a disparu et ne doit PAS revenir : en `store_true`
    # sur un drapeau déjà levé, il aurait baissé le drapeau à chaque appel qui
    # l'omet — un défaut muet, du type que ce module refuse.
    assert "--activer-roster-an" not in sortie
    assert "--desactiver-roster-an" in sortie
    assert "#527" in an_roster.AIDE_ROSTER_AN
    assert "#526" in an_roster.AIDE_ROSTER_AN
    assert not hasattr(an_roster, "AIDE_ACTIVER_ROSTER_AN")


# --------------------------------------------------------------------------
# 2. Ce que l'archive publie
# --------------------------------------------------------------------------

def test_larchive_porte_63_organes_gp(index):
    """Mesure de l'issue, figée : 63 organes `GP` sur l'archive complète."""
    assert len(index["organes"]) == 63
    assert index["organes"][NI_16]["legislature"] == "16"


def test_le_sigle_an_est_libelleabrev_et_pas_libelleabrege(index):
    """`libelleAbrege` ne distingue PAS les deux organes `SOC` de la 16e.

    C'est le champ qu'on aurait pris par réflexe, et il rend `SOC` pour les
    deux : un roster « par sigle » construit dessus fusionnerait deux organes
    sans le dire. `libelleAbrev` rend `SOC` puis `SOC-A`.
    """
    assert index["organes"][SOC_16]["sigle"] == "SOC"
    assert index["organes"][SOC_A_16]["sigle"] == "SOC-A"
    assert index["organes"][SOC_16]["sigle_abrege"] == "SOC"
    assert index["organes"][SOC_A_16]["sigle_abrege"] == "SOC"
    # Et l'inverse : `libelleAbrege` écrit des espaces là où la table n'en a pas.
    assert index["organes"]["PO800490"]["sigle"] == "LFI-NUPES"
    assert index["organes"]["PO800490"]["sigle_abrege"] == "LFI - NUPES"


# --------------------------------------------------------------------------
# 3. Piège n°1 — le filtrage par dates, sur le cas NI
# --------------------------------------------------------------------------

def test_la_date_de_constitution_est_lue_dans_le_referentiel(index):
    """Jamais écrite en dur : le plus petit `dateDebut` des organes hors `NI`."""
    assert an_roster.date_constitution_groupes(index, "16") == "2022-06-28"
    assert an_roster.date_constitution_groupes(index, "17") == "2024-07-18"
    # Et c'est bien `NI` qui ouvre avant les groupes — la cause du piège.
    assert index["organes"][NI_16]["debut"] == "2022-06-22"
    assert index["organes"][NI_17]["debut"] == "2024-07-01"


def test_une_legislature_sans_groupe_ne_filtre_rien(index):
    """Sans date de constitution connue, rien n'est écarté (règle 5)."""
    assert an_roster.date_constitution_groupes(index, "99") is None
    assert an_roster.est_mandat_de_transit("2022-06-28", None) is False


@pytest.mark.parametrize(
    "legislature, organe, brut, filtre",
    [("16", NI_16, 592, 39), ("17", NI_17, 640, 94)],
)
def test_le_filtrage_par_dates_sur_le_cas_NI(index, legislature, organe, brut, filtre):
    """`NI` 16e : **592 → 39**. `NI` 17e : **640 → 94**.

    Tout le monde transite par « Non inscrit » entre l'ouverture de la
    législature et la constitution des groupes. Sans ce filtrage, `NI`
    ressemblerait à un groupe de 592 membres — et le filtrage n'est donc pas
    cosmétique, c'est lui qui distingue une appartenance d'un passage
    administratif.
    """
    assert len({m[0] for m in index["mandats"][organe]}) == brut
    membres = an_roster.deriver_membres_organes(index, [organe], legislature, {}, "NI")
    assert len(membres) == filtre


def test_le_filtrage_ne_coupe_aucun_autre_groupe(index):
    """Le filtre ne touche que ce qu'il vise : mesuré sur les 10 entrées."""
    for entree in _entrees_table():
        organes = an_roster.organes_du_groupe(index, entree["legislature"], entree["sigles_an"])
        brut = {m[0] for organe in organes for m in index["mandats"].get(organe, [])}
        filtres = an_roster.deriver_membres_organes(
            index, organes, entree["legislature"], {}, entree["groupe_sigle"]
        )
        assert len(filtres) == len(brut), (
            f"{entree['groupe_sigle']}-{entree['legislature']} perd des membres au "
            "filtrage par dates, ce qu'aucune mesure du 26/08/2026 ne montrait."
        )


def test_un_mandat_ouvert_nest_jamais_un_transit():
    assert an_roster.est_mandat_de_transit(None, "2024-07-18") is False
    assert an_roster.est_mandat_de_transit("2024-07-18", "2024-07-18") is True
    assert an_roster.est_mandat_de_transit("2024-07-19", "2024-07-18") is False


# --------------------------------------------------------------------------
# 4. Piège n°3 — l'union des organes successifs (SOC / SOC-A)
# --------------------------------------------------------------------------

def test_lunion_des_organes_successifs_soc_soc_a(index, actif):
    """`SOC` 16e vit dans DEUX organes ; un roster par sigle en perdrait un.

    `PO800496` s'arrête le 2023-10-18, `PO830170` reprend le lendemain. Les
    deux comptent 31 membres, mais ce ne sont pas « 31 membres » deux fois :
    c'est un groupe continu dont l'AN a rouvert l'organe.
    """
    membres, rapport = _roster("SOC", "16")
    assert rapport["organes_trouves"] == [SOC_16, SOC_A_16]
    assert rapport["sigles_an"] == ["SOC", "SOC-A"]
    assert len(membres) == 31
    # Chaque membre est déclaré une seule fois, sur les deux organes.
    assert len({m["acteur_ref"] for m in membres}) == 31
    assert all(m["organes_an"] == [SOC_16, SOC_A_16] for m in membres)


def test_lunion_recolle_les_periodes_et_ne_referme_pas_le_mandat(index, actif):
    """Le second organe porte la fin réelle ; le premier s'arrête en 2023.

    Un roster construit sur le seul `PO800496` daterait la sortie de groupe au
    2023-10-18 pour les 31 membres — la moitié de l'année perdue, sans qu'aucun
    décompte ne bouge.
    """
    membres, _ = _roster("SOC", "16")
    seul_premier = an_roster.deriver_membres_organes(index, [SOC_16], "16", {}, "SOC")
    fins_premier = {m["mandat_fin"] for m in seul_premier}
    fins_union = {m["mandat_fin"] for m in membres}
    assert fins_premier == {"2023-10-18"}
    assert fins_union == {"2024-06-09"}
    assert {m["mandat_debut"] for m in membres} == {"2022-06-29"}


def test_un_mandat_ouvert_lemporte_sur_un_mandat_clos():
    """Recollement : `None` gagne. Un retour dans le groupe ne se referme pas."""
    assert an_roster._fusionner_periodes(
        [("2024-07-18", "2025-01-10"), ("2025-03-01", None)]
    ) == ("2024-07-18", None)
    assert an_roster._fusionner_periodes(
        [("2022-06-29", "2023-10-18"), ("2023-10-19", "2024-06-09")]
    ) == ("2022-06-29", "2024-06-09")


# --------------------------------------------------------------------------
# 5. Piège n°2 — la table de correspondance des sigles, committée
# --------------------------------------------------------------------------

def test_la_table_committee_est_valide():
    entrees = an_roster.charger_correspondance_sigles(CONFIG)
    assert len(entrees) == _ATTENDU
    # Les législatures couvertes se LISENT, elles ne se figent pas (#777) : la
    # table portait {16, 17} jusqu'aux huit groupes des XVe et XVIe, et le
    # prochain lot y ajoutera peut-être la XIVe. Ce qui doit rester vrai est que
    # chacune est une législature CONNUE et que la table et `groupes[]` décrivent
    # le même ensemble — pas qu'elles soient deux.
    legislatures = {e["legislature"] for e in entrees}
    assert legislatures <= {"14", "15", "16", "17"}, legislatures
    assert {"16", "17"} <= legislatures, "les deux législatures publiées ont disparu"


def test_les_organes_de_la_table_sont_le_fil_piege(index):
    """`organes_an` est relu, pas utilisé : il doit coïncider avec le mesuré.

    Le roster se construit par SIGLE (pour qu'un organe successif nouvellement
    ouvert entre quand même), et la liste committée sert à dire qu'il a bougé.
    """
    for entree in _entrees_table():
        trouves = an_roster.organes_du_groupe(index, entree["legislature"], entree["sigles_an"])
        assert trouves == entree["organes_an"], (
            f"{entree['groupe_sigle']}-{entree['legislature']} : l'AN a ouvert ou "
            "fermé un organe — relire la table de correspondance (#526)."
        )


def test_un_sigle_absent_de_la_table_echoue_en_nommant_le_couple(actif):
    with pytest.raises(an_roster.CorrespondanceSiglesInvalide) as exc:
        an_roster.deriver_roster_groupe("INEXISTANT", "16", zip_path=ARCHIVE, chemin_config=CONFIG)
    assert "INEXISTANT" in str(exc.value)


@pytest.mark.parametrize(
    "mutation, fragment",
    [
        (lambda t: t.pop("groupes"), "groupes"),
        (lambda t: t["groupes"][0].update(sigles_an=[]), "sigles_an"),
        (lambda t: t["groupes"][0].update(organes_an=["RE"]), "organes_an"),
        (lambda t: t["groupes"][0].pop("verifie_le"), "verifie_le"),
        (lambda t: t["groupes"].append(dict(t["groupes"][0])), "deux entrées"),
    ],
)
def test_une_table_degradee_echoue_bruyamment(tmp_path, mutation, fragment):
    document = json.loads(CONFIG.read_text(encoding="utf-8"))
    mutation(document[an_roster.CLE_CORRESPONDANCE_SIGLES])
    chemin = tmp_path / "groupes_reels.json"
    chemin.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(an_roster.CorrespondanceSiglesInvalide) as exc:
        an_roster.charger_correspondance_sigles(chemin)
    assert fragment in str(exc.value)


# --------------------------------------------------------------------------
# 6. Les 5 rosters de la 16e, et chaque écart nommé
# --------------------------------------------------------------------------

def test_les_cinq_rosters_de_la_16e_sont_reproduits(actif):
    """Effectifs dérivés == effectifs committés, mesurés le 26/08/2026."""
    mesures = {}
    for entree in _entrees_table("16"):
        _, rapport = _roster(entree["groupe_sigle"], "16")
        mesures[entree["groupe_sigle"]] = rapport["effectif_mesure"]
        assert rapport["effectif_mesure"] == entree["effectif_amo30"]
    # Les cinq groupes PUBLIÉS de la 16e. Une entrée configurée et non encore
    # parue (#700, #777) n'a pas de fiche à reproduire : la comparer à une
    # mesure comparerait un chiffre à un vide.
    publies = {e["groupe_sigle"] for e in _entrees_table("16")
               if e.get("effectif_publie") is not None}
    assert {k: v for k, v in mesures.items() if k in publies} == {
        "REN": 196, "SOC": 31, "RN": 90, "LFI": 76, "LR": 63}


def test_chaque_ecart_de_la_16e_est_nomme_et_date(actif):
    """« ~3 de plus » n'est pas une mesure : 4 acteurs, nommés, avec leurs dates.

    Les 4 écarts (1 `LR`, 3 `REN`) sont exactement des membres **partis avant
    la fin de la 16e législature** (2024-06-09) : absents de la dernière
    composition connue de NosDéputés, sans profil publié, donc sans entrée dans
    la table du lot 2. C'est une catégorie fermée, pas un résidu.
    """
    total_ecarts = 0
    for entree in _entrees_table("16"):
        # `effectif_publie: null` = entrée CONFIGURÉE, pas encore parue
        # (#700 pour la 17e, #777 pour ECOLO et GDR de la 16e). Un écart se
        # mesure contre une fiche PUBLIÉE ; sans elle il n'y a rien à
        # comparer, et soustraire None serait une erreur de type qu'on lirait
        # comme un défaut de données.
        if entree.get("effectif_publie") is None:
            continue
        membres, _ = _roster(entree["groupe_sigle"], "16")
        par_acteur = {m["acteur_ref"]: m for m in membres}
        attendu = entree["effectif_amo30"] - entree["effectif_publie"]
        assert len(entree["ecart_membres"]) == attendu, (
            f"{entree['groupe_sigle']}-16 : {attendu} écart(s) annoncé(s), "
            f"{len(entree['ecart_membres'])} nommé(s)."
        )
        for nomme in entree["ecart_membres"]:
            total_ecarts += 1
            mesure = par_acteur.get(nomme["acteur_ref"])
            assert mesure is not None, f"{nomme['acteur_ref']} absent du roster dérivé"
            assert mesure["nom"] == nomme["nom"]
            assert mesure["mandat_debut"] == nomme["mandat_debut"]
            assert mesure["mandat_fin"] == nomme["mandat_fin"]
            assert mesure["mandat_fin"] < "2024-06-09", (
                f"{nomme['acteur_ref']} n'est pas parti avant la fin de la "
                "législature : l'explication committée ne tient plus."
            )
    assert total_ecarts == 4


# --------------------------------------------------------------------------
# 7. La 17e législature — ce que NosDéputés n'a jamais servi
# --------------------------------------------------------------------------

def test_les_tables_de_domaines_ont_disparu():
    """Critère d'acceptation du lot 1 (#526), élargi par le lot 5 (#529).

    `LEGISLATURE_BY_BASE_URL` avait disparu la première : elle n'avait qu'un
    usage — construire son propre inverse — et laissait croire qu'un
    sous-domaine est une façon légitime d'apprendre une législature.
    `_BASE_URL_BY_LEGISLATURE_AN`, l'inverse en question, la suit : c'est elle
    qui portait la raison d'être du lot, **la source s'arrêtait à la 16e**, et
    elle n'a plus d'appelant depuis que `fetch_full_roster` délègue tout à
    AMO30. Ce que le test disait — « NosDéputés ne sert pas la 17e » — reste
    vrai et n'a plus besoin d'être vérifié à l'exécution : la 17e est servie,
    par AMO30, et c'est le test suivant qui le mesure.
    """
    for nom in ("LEGISLATURE_BY_BASE_URL", "_BASE_URL_BY_LEGISLATURE_AN", "_base_url_for"):
        assert not hasattr(group_roster, nom), (
            f"`group_roster.{nom}` est de retour : c'est une table de domaines "
            "NosDéputés, retirée par #526 puis #529."
        )


def test_la_17e_est_servie_par_amo30(actif):
    mesures = {}
    for entree in _entrees_table("17"):
        membres, rapport = _roster(entree["groupe_sigle"], "17")
        assert rapport["effectif_mesure"] == entree["effectif_amo30"]
        assert rapport["date_constitution_groupes"] == "2024-07-18"
        assert all(m["legislature"] == "17" for m in membres)
        mesures[entree["groupe_sigle"]] = rapport["effectif_mesure"]
    # #815 — SEPT groupes depuis que `GDR-17` et `ECOS-17` ferment leurs
    # lignées, DIX depuis que MoDem, Horizons et LIOT ont la leur (11/09/2026),
    # ONZE avec UDR, union de trois organes renommés (AD, UDR, UDDPLR).
    # Ceux d'avant gardent leur effectif au membre près : c'est ce qui
    # distingue un élargissement d'une régression.
    assert mesures == {"EPR": 123, "SOC": 70, "RN": 131, "LFI": 73, "DR": 64,
                       "GDR": 18, "ECOS": 38, "DEM": 42, "HOR": 44, "LIOT": 26,
                       "UDR": 18}


#: Groupes de la 17e déclarés SANS prédécesseur, par décision datée (#815).
SANS_PREDECESSEUR_17E = frozenset({"AN:UDR:17"})


def test_le_perimetre_de_la_17e_est_ecrit_groupe_par_groupe():
    """Élargir n'est pas gratuit : chaque entrée dit ce qu'elle coûte.

    `membres_avec_slug` est le nombre de membres qui ont DÉJÀ un profil publié ;
    la différence est le nombre de profils à collecter. C'est cette soustraction
    que le lot 1b doit assumer, et elle est committée plutôt que redécouverte.
    """
    entrees = _entrees_table("17")
    # #815 : sept depuis que `GDR-17` et `ECOS-17` ferment leurs lignées, dix
    # depuis `DEM-17`, `HOR-17` et `LIOT-17`, onze avec `UDR-17`.
    assert len(entrees) == 11
    total, deja = 0, 0
    for entree in entrees:
        assert entree["effectif_publie"] is None, "aucune fiche 17e n'est publiée"
        # Chaque groupe de la 17e nomme son prédécesseur, SAUF ceux qu'une
        # décision datée déclare sans : UDR (#815, 11/09/2026), dont 0 membre
        # sur 16 ne vient de DR et 2 seulement de LR-16. La liste est explicite
        # pour qu'un oubli de `succede_a` reste un échec, pas une exception.
        if entree["groupe_id"] in SANS_PREDECESSEUR_17E:
            assert "succede_a" not in entree, entree["groupe_id"]
        else:
            assert entree["succede_a"], "chaque groupe de la 17e nomme son prédécesseur"
        assert isinstance(entree["membres_avec_slug"], int)
        assert 0 <= entree["membres_avec_slug"] <= entree["effectif_amo30"]
        total += entree["effectif_amo30"]
        deja += entree["membres_avec_slug"]
    # +56 membres (GDR 18, ECOS 38), dont 39 ont déjà un profil : le lot #815
    # en collecte 17 de plus sur la 17e. Le couple est écrit plutôt que
    # recalculé — c'est ce qui fait qu'élargir se décide au lieu de se subir.
    # Puis +112 (DEM 42, HOR 44, LIOT 26), dont 25 ont déjà une entrée dans la
    # table : 87 de plus sur la 17e (11/09/2026). Puis +18 (UDR), dont 2 ont
    # déjà une entrée — Ciotti et D'Intorni, venus de LR-16 : 16 de plus.
    assert (total, deja) == (647, 371)


# --------------------------------------------------------------------------
# 8. Le contrat de sortie : celui de `group_roster.fetch_full_roster`
# --------------------------------------------------------------------------

def test_le_contrat_de_sortie_est_celui_de_fetch_full_roster(actif):
    """`filter_roster_by_sigle` s'applique tel quel — condition du lot 1b."""
    roster = an_roster.fetch_full_roster_an(
        "16", zip_path=ARCHIVE, chemin_config=CONFIG, chemin_correspondance=CORRESPONDANCE
    )
    # 456 = 196 + 31 + 90 + 76 + 63, les cinq groupes PUBLIÉS de la 16e. Le
    # roster en porte davantage depuis #777 : ECOLO et GDR y sont configurés
    # et collectés, sans fiche encore parue.
    assert len(roster) >= 456
    for membre in roster:
        assert set(membre) >= {"slug", "nom", "groupe_sigle", "mandat_debut", "mandat_fin"}

    filtre = group_roster.filter_roster_by_sigle(roster, "deputes", "REN")
    assert len(filtre) == 196
    assert {m["groupe_sigle"] for m in filtre} == {"REN"}
    assert all(m["actif"] is False for m in filtre), "la 16e est close depuis 2024-06-09"


def test_le_sigle_rendu_est_le_sigle_PUBLIE_pas_celui_de_lAN(actif):
    """`REN`, pas `RE` : sinon la config d'aval ne reconnaît plus son groupe."""
    membres, _ = _roster("REN", "16")
    assert {m["groupe_sigle"] for m in membres} == {"REN"}
    assert {s for m in membres for s in m["sigles_an"]} == {"RE"}


# --------------------------------------------------------------------------
# 9. Le slug vient du lot 2, et son absence est déclarée
# --------------------------------------------------------------------------

def test_un_membre_sans_slug_est_declare_jamais_absent(actif):
    """Un trou muet est ce qui a produit #510 et #501 (AGENTS §2 règle 5).

    La chaîne aval (`build_roster_candidats_detaille`) ignore un membre sans
    slug : le rendre ici, nommé et daté, est ce qui empêche la perte
    silencieuse.

    Depuis #708 la porte d'entrée existe, donc ce que le rapport doit garantir
    n'est plus « la liste est non vide » mais **la partition** : tout membre est
    dans exactement une des deux listes ou porte un slug relu. Une fabrication
    qui viderait `membres_sans_slug` par construction supprimerait le compteur
    de #527 au lieu de le satisfaire — c'est ce que ce test refuse.
    """
    membres, rapport = _roster("LR", "16")
    sans_slug_mesure = [m for m in membres if not m["slug"]]
    assert len(rapport["membres_sans_slug"]) == len(sans_slug_mesure)
    assert {m["acteur_ref"] for m in rapport["membres_sans_slug"]} == {
        m["acteur_ref"] for m in sans_slug_mesure
    }
    for entree in rapport["membres_sans_slug"]:
        assert entree["nom"], "un membre non résolu est nommé, jamais un simple identifiant"
        assert set(entree) >= {
            "acteur_ref", "nom", "mandat_debut", "mandat_fin", "organes_an", "motif",
        }
        assert entree["motif"] in an_roster.MOTIFS_SLUG_NON_ATTRIBUE

    # La partition, sur le roster entier : personne ne sort par une porte que
    # le rapport ne nomme pas.
    nommes = {m["acteur_ref"] for m in rapport["membres_sans_slug"]}
    nommes |= {m["acteur_ref"] for m in rapport["membres_slug_fabrique"]}
    nommes |= {m["acteur_ref"] for m in membres if m.get("slug_origine") == "table"}
    assert nommes == {m["acteur_ref"] for m in membres}


def test_le_slug_du_lot_2_est_lu_a_lenvers(actif):
    """La table `acteur_ref → slug` est celle de #525, sans arbitrage.

    Elle passe **devant** la fabrication de #708 : là où elle a une entrée,
    c'est elle qui décide, et `slug_origine` le dit.
    """
    table = json.loads(CORRESPONDANCE.read_text(encoding="utf-8"))["correspondances"]
    attendu = {e["acteur_ref"]: s for s, e in table.items() if e.get("acteur_ref")}
    membres, _ = _roster("LR", "16")
    relus = [m for m in membres if m["acteur_ref"] in attendu]
    assert relus, "la fixture couvre au moins un membre LR"
    for membre in relus:
        assert membre["slug"] == attendu[membre["acteur_ref"]]
        assert membre["slug_origine"] == "table"
    for membre in membres:
        if membre["acteur_ref"] not in attendu:
            assert membre["slug_origine"] in (None, "fabrique")


# --------------------------------------------------------------------------
# 10. Patron #493 : l'écart est publié entrée par entrée
# --------------------------------------------------------------------------

def test_divergence_groupe_nomme_chaque_entree():
    """Fonction pure : deux compositions, trois catégories, aucun volume seul."""
    membres = [
        {"slug": "a", "acteur_ref": "PA1", "nom": "A", "mandat_debut": "2022-06-29", "mandat_fin": None},
        {"slug": "b", "acteur_ref": "PA2", "nom": "B", "mandat_debut": "2022-06-29", "mandat_fin": "2024-03-19"},
        {"slug": None, "acteur_ref": "PA3", "nom": "C", "mandat_debut": "2022-06-29", "mandat_fin": "2023-08-29"},
    ]
    divergence = an_roster.divergence_groupe(membres, ["a", "z"])
    assert divergence["commun"] == ["a"]
    assert [m["slug"] for m in divergence["amo30_seulement"]] == ["b"]
    assert divergence["amo30_seulement"][0]["mandat_fin"] == "2024-03-19"
    assert divergence["publie_seulement"] == ["z"]
    assert [m["acteur_ref"] for m in divergence["sans_slug"]] == ["PA3"]


def test_le_rapport_de_divergence_compte_la_migration(actif, tmp_path):
    """`ecart_total` est le compteur de migration ; une fiche absente n'en est pas.

    Un groupe de la 17e n'a pas d'écart, il a un périmètre : le confondre ferait
    passer une décision éditoriale pour une régression de données.
    """
    groupes = tmp_path / "groupes"
    groupes.mkdir()
    membres, _ = _roster("RN", "16")
    slugs = [m["slug"] for m in membres if m["slug"]]
    (groupes / "groupe-AN-RN-16.json").write_text(
        json.dumps({"membres": [{"membre_id": s} for s in slugs]}, ensure_ascii=False),
        encoding="utf-8",
    )

    rapport = an_roster.rapport_divergence(
        zip_path=ARCHIVE,
        chemin_config=CONFIG,
        chemin_correspondance=CORRESPONDANCE,
        chemin_groupes_pivot=groupes,
    )
    par_groupe = {bloc["groupe"]: bloc for bloc in rapport["groupes"]}
    # Le banc n'écrit qu'une fiche (`groupe-AN-RN-16.json`) : tout le reste de
    # la table est « non publié », et la liste grandit à chaque groupe configuré
    # (#777 en ajoute huit). Ce qui doit rester vrai n'est pas la liste, c'est
    # qu'elle soit exactement le complément de ce que le banc a écrit.
    attendu = {
        f"{e['groupe_sigle']}-{e['legislature']}"
        for e in an_roster.charger_correspondance_sigles(CONFIG)
    } - {"RN-16"}
    assert set(rapport["non_publies"]) == attendu
    divergence = par_groupe["RN-16"]["divergence"]
    assert divergence["amo30_seulement"] == []
    assert divergence["publie_seulement"] == []
    assert len(divergence["sans_slug"]) == 90 - len(slugs)
    assert rapport["ecart_total"] == len(divergence["sans_slug"])


# --------------------------------------------------------------------------
# 11. Le cache : jamais un index vide figé sur une archive lisible (#505/#510)
# --------------------------------------------------------------------------

def test_un_index_sans_organe_gp_nest_ni_rendu_ni_mis_en_cache(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    archive = tmp_path / "sans_gp.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr(
            "json/organe/PO1.json",
            json.dumps({"organe": {"uid": "PO1", "codeType": "COMPER", "libelleAbrev": "FIN"}}),
        )
    with pytest.raises(an_roster.RosterAnIndisponible) as exc:
        an_roster.charger_index_gp(archive)
    assert "#510" in str(exc.value)
    assert not (tmp_path / an_roster.REPERTOIRE_CACHE_PAR_DEFAUT / an_roster.NOM_INDEX_GP).exists()


def test_une_archive_illisible_echoue_sans_index_vide(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    archive = tmp_path / "corrompue.zip"
    archive.write_bytes(b"ceci n'est pas un zip")
    with pytest.raises(an_roster.RosterAnIndisponible):
        an_roster.charger_index_gp(archive)


def test_lindex_est_mis_en_cache_et_relu(actif):
    index_path = actif / an_roster.REPERTOIRE_CACHE_PAR_DEFAUT / an_roster.NOM_INDEX_GP
    premier = an_roster.charger_index_gp(ARCHIVE)
    assert index_path.is_file()
    an_roster.vider_memo()
    relu = an_roster.charger_index_gp(ARCHIVE)
    assert relu["organes"] == premier["organes"]
    assert json.loads(index_path.read_text(encoding="utf-8"))["archive_taille"] == (
        ARCHIVE.stat().st_size
    )


def test_un_index_dune_autre_archive_nest_jamais_resservi(actif):
    """La clé de #505 : un contenu qui dépend d'une entrée porte cette entrée.

    `.cache/acteurs_historique_an/` est partagé entre les jobs par la clé de
    cache CI. Un index construit sur une archive et servi à une autre, c'est
    la composition de la semaine passée publiée comme celle du jour.
    """
    index_path = actif / an_roster.REPERTOIRE_CACHE_PAR_DEFAUT / an_roster.NOM_INDEX_GP
    an_roster.charger_index_gp(ARCHIVE)
    an_roster.vider_memo()

    autre = actif / "autre.zip"
    with zipfile.ZipFile(autre, "w") as zf:
        zf.writestr(
            "json/organe/PO9.json",
            json.dumps({"organe": {"uid": "PO9", "codeType": "GP", "libelleAbrev": "X",
                                   "legislature": "17", "viMoDe": {"dateDebut": "2024-07-18"}}}),
        )
    index = an_roster.charger_index_gp(autre)
    assert list(index["organes"]) == ["PO9"]
    assert json.loads(index_path.read_text(encoding="utf-8"))["archive_taille"] == (
        autre.stat().st_size
    )


def test_le_memo_est_indexe_par_chemin_darchive(actif):
    """Jamais par nom logique : c'est le piège qui avait fait revenir #377."""
    premier = an_roster.charger_index_gp(ARCHIVE)
    assert an_roster.charger_index_gp(ARCHIVE) is premier


# --------------------------------------------------------------------------
# 12. Zéro appel réseau hors data.assemblee-nationale.fr
# --------------------------------------------------------------------------

def test_le_chemin_roster_ne_connait_quune_seule_origine():
    """Critère d'acceptation : zéro appel hors `data.assemblee-nationale.fr`.

    Le module n'ouvre lui-même aucune connexion : il n'importe pas `requests`,
    et son unique source de données est l'archive AMO30 que
    `candidate_profile._ensure_acteurs_historique_zip_downloaded` télécharge
    déjà pour quatre autres index. Vérifier l'URL de cette archive suffit donc
    à vérifier le chemin entier — c'est le seul téléchargement possible.
    """
    import re
    import candidate_profile

    source = (RACINE / "src" / "an_roster.py").read_text(encoding="utf-8")
    assert not re.search(r"^\s*import requests", source, re.M), (
        "an_roster ne parle jamais lui-même au réseau"
    )
    assert not re.search(r"^\s*(?:import|from) group_roster", source, re.M), (
        "importer group_roster ramènerait NosDéputés dans le chemin roster"
    )
    assert "_ensure_acteurs_historique_zip_downloaded" in source

    assert candidate_profile.AN_ACTEURS_HISTORIQUE_ZIP_URL.startswith(
        "https://data.assemblee-nationale.fr/"
    ), candidate_profile.AN_ACTEURS_HISTORIQUE_ZIP_URL
