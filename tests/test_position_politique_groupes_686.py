"""La position politique déclarée d'un groupe (#686).

L'Assemblée nationale qualifie **elle-même** chacun de ses groupes politiques —
`Majoritaire`, `Opposition`, `Minoritaire` — dans `organe.positionPolitique` du
référentiel AMO30. Le pipeline lisait déjà ce champ pour les profils
individuels et ne le lisait nulle part pour les fiches de groupe, où il commande
pourtant la lecture de tous les compteurs.

Tout ce qui se mesure ici tourne sur `tests/fixtures/amo30_gp_leg16_17.zip`,
**réduction verbatim** de l'archive réelle (voir l'en-tête de
`tests/test_an_roster.py`) : les 63 organes `GP` y sont, avec leur
`positionPolitique` tel que l'Assemblée l'écrit. Aucune valeur n'est inventée —
#510 a coûté un défaut invisible pendant des mois parce qu'une fixture décrivait
un schéma que la source ne publie pas.

Aucun réseau, aucune lecture de `pivot_data/` ni de `raw_data/profiles/`.
"""

import json
import sys
from pathlib import Path

import pytest

#: Ce fichier de tests lit la configuration committée nommée ci-dessous.
#: Le garde-fou de `conftest.py` refuse tout `.json` de `raw_data/` qu'un
#: test n'a pas déclaré (#791), et n'accepte la déclaration que si le chemin
#: est dans le `sparse-checkout` de `tests.yml` — sinon le test ne tournerait
#: qu'en local, sur ce qu'un run y a laissé.
pytestmark = pytest.mark.lit_reference_committee("raw_data/groupes_reels.json")

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

import an_roster  # noqa: E402
import groupes_config  # noqa: E402
import schema_groupe  # noqa: E402

ARCHIVE = Path(__file__).resolve().parent / "fixtures" / "amo30_gp_leg16_17.zip"
CONFIG = RACINE / "raw_data" / "groupes_reels.json"

SOURCE_AMO30 = (
    "https://data.assemblee-nationale.fr/static/openData/repository/17/amo/"
    "tous_acteurs_mandats_organes_xi_legislature/"
    "AMO30_tous_acteurs_tous_mandats_tous_organes_historique.json.zip"
)


@pytest.fixture(autouse=True)
def _drapeau_restaure():
    initial = an_roster.AN_ROSTER_ACTIF
    an_roster.vider_memo()
    yield
    an_roster.activer_roster_an(initial)


@pytest.fixture
def index(tmp_path):
    return an_roster.charger_index_gp(ARCHIVE, repertoire_cache=tmp_path)


# --------------------------------------------------------------------------
# 1. Ce que l'archive déclare — mesuré, jamais supposé
# --------------------------------------------------------------------------

def test_larchive_qualifie_40_des_63_organes(index):
    """Mesure de l'issue, figée : 40 organes `GP` qualifiés sur 63."""
    valeurs = [o.get("position_politique") for o in index["organes"].values()]
    assert len(valeurs) == 63
    assert sum(1 for v in valeurs if v) == 40
    assert set(v for v in valeurs if v) == {"Majoritaire", "Opposition", "Minoritaire"}


def test_aucun_groupe_de_la_17e_ne_porte_de_position(index):
    """0 sur 14 : l'AN ne qualifie qu'une fois la législature achevée.

    C'est le deuxième obstacle de l'issue, et la raison d'être de
    `non_declaree` : la XVIIe est en cours, et une posture déduite d'un
    comportement de vote serait exactement le jugement que ce dépôt refuse de
    porter (AGENTS.md §2 règle 1).
    """
    organes_17 = [
        o for o in index["organes"].values() if o.get("legislature") == "17"
    ]
    assert len(organes_17) == 14
    assert [o for o in organes_17 if o.get("position_politique")] == []


def test_deux_groupes_minoritaires_sont_declares_sur_la_16e(index):
    """`DEM` et `HOR`, et les deux ont désormais leur fiche.

    Troisième obstacle de l'issue : la troisième posture existait dans le
    référentiel et pas dans le corpus, et se publiait comme catégorie vide — la
    replier sur « majorité » ou « opposition » aurait été un acte éditorial.
    Depuis que #815 déclare les lignées MoDem et Horizons (11/09/2026), elle a
    ses deux groupes sur la XVIe. Ce test disait « aucun » ; il dit maintenant
    « les deux », et c'est la même vérification : ce que le référentiel qualifie
    minoritaire, la table le recopie sans le replier.
    """
    minoritaires = sorted(
        o["sigle"]
        for o in index["organes"].values()
        if o.get("legislature") == "16" and o.get("position_politique") == "Minoritaire"
    )
    assert minoritaires == ["DEM", "HOR"]

    publies = {
        e["groupe_sigle"]: e["position_politique_an"]["position"]
        for e in groupes_config.charger_correspondance_sigles(CONFIG)
        if e["legislature"] == "16"
    }
    assert {s: publies.get(s) for s in minoritaires} == {
        "DEM": "minoritaire", "HOR": "minoritaire",
    }


def test_un_index_v1_du_cache_ci_nest_jamais_resservi(tmp_path):
    """`.cache/acteurs_historique_an/` traverse les jobs par la clé de cache CI.

    Un index construit avant #686 ne porte pas `position_politique` : le relire
    « au mieux » ferait mesurer « aucun groupe n'est qualifié » sur une archive
    qui en qualifie 40 — la forme exacte du trou muet de #510. La version du
    contenu est donc dans la clé, et l'index se reconstruit.
    """
    index_path = tmp_path / an_roster.NOM_INDEX_GP
    index_path.write_text(json.dumps({
        "version": "an-roster-gp-v1",
        "archive_taille": ARCHIVE.stat().st_size,
        "organes": {"PO800538": {"sigle": "RE", "legislature": "16"}},
        "mandats": {},
        "acteurs": {},
    }), encoding="utf-8")

    index = an_roster.charger_index_gp(ARCHIVE, repertoire_cache=tmp_path)

    assert index["version"] == an_roster.VERSION_INDEX_GP
    assert index["organes"]["PO800538"]["position_politique"] == "Majoritaire"


# --------------------------------------------------------------------------
# 2. L'appariement passe par la table committée, jamais par le sigle
# --------------------------------------------------------------------------

def test_le_sigle_publie_ne_ressemble_pas_au_sigle_an(index):
    """`REN` et `LFI` n'existent pas dans le référentiel — `RE` et `LFI-NUPES`, si.

    Premier obstacle de l'issue, et le plus silencieux : un appariement direct
    rendrait `None` sur deux fiches sur cinq, dont la seule majoritaire.
    """
    sigles_an_16 = {
        o["sigle"] for o in index["organes"].values() if o.get("legislature") == "16"
    }
    assert "REN" not in sigles_an_16 and "RE" in sigles_an_16
    assert "LFI" not in sigles_an_16 and "LFI-NUPES" in sigles_an_16


@pytest.mark.parametrize(
    "sigle_publie, legislature, attendu",
    [
        ("REN", "16", "majorite"),      # la seule majoritaire du corpus publié
        ("LFI", "16", "opposition"),    # l'autre sigle que l'appariement direct ratait
        ("SOC", "16", "opposition"),
        ("RN", "16", "opposition"),
        ("LR", "16", "opposition"),
        ("EPR", "17", "non_declaree"),
        ("DR", "17", "non_declaree"),
    ],
)
def test_la_position_se_mesure_par_la_table(sigle_publie, legislature, attendu, tmp_path):
    an_roster.activer_roster_an(True)
    an_roster.charger_index_gp(ARCHIVE, repertoire_cache=tmp_path)
    mesure = an_roster.position_politique_mesuree(
        sigle_publie, legislature, zip_path=ARCHIVE, chemin_config=CONFIG
    )
    assert mesure["position"] == attendu


def test_la_table_committee_dit_ce_que_larchive_dit(tmp_path):
    """Le fil-piège : committé face à mesuré, entrée par entrée.

    Une divergence ici veut dire que l'AN a changé (ou publié pour la première
    fois) une qualification, et que la table doit être relue à la main. Le jour
    où la XVIIe s'achèvera, ses 5 entrées passeront de `non_declaree` à une
    valeur, et c'est ce test qui le dira.
    """
    an_roster.activer_roster_an(True)
    an_roster.charger_index_gp(ARCHIVE, repertoire_cache=tmp_path)
    rapport = an_roster.rapport_positions_politiques(
        zip_path=ARCHIVE, chemin_config=CONFIG
    )
    assert rapport["ecarts"] == []
    assert len(rapport["groupes"]) == _ATTENDU


# --------------------------------------------------------------------------
# 3. Les organes successifs : l'union, pas un choix
# --------------------------------------------------------------------------

def test_les_deux_organes_soc_de_la_16e_sont_publies_tous_les_deux(tmp_path):
    """`SOC` a deux organes successifs dans la même législature (#526 piège 3).

    Les deux sont publiés avec leur déclaration : n'en garder qu'un déciderait
    laquelle des deux moitiés de la législature définit le groupe.
    """
    an_roster.activer_roster_an(True)
    an_roster.charger_index_gp(ARCHIVE, repertoire_cache=tmp_path)
    mesure = an_roster.position_politique_mesuree(
        "SOC", "16", zip_path=ARCHIVE, chemin_config=CONFIG
    )
    assert [o["organe_an"] for o in mesure["organes"]] == ["PO800496", "PO830170"]
    assert [o["sigle_an"] for o in mesure["organes"]] == ["SOC", "SOC-A"]
    assert [o["valeur_source"] for o in mesure["organes"]] == ["Opposition", "Opposition"]
    assert mesure["position"] == "opposition"


def test_deux_organes_qui_divergent_ne_se_replient_sur_aucun_des_deux():
    """La décision du lot, figée : `divergente`, jamais le dernier organe.

    Les deux organes `SOC` de la XVIe s'accordent aujourd'hui — rien ne le
    garantit demain, et un cas non prévu se replierait sinon sur le premier
    organe venu.
    """
    declarations = [
        {"organe_an": "PO800496", "sigle_an": "SOC",
         "valeur_source": "Opposition", "position": "opposition"},
        {"organe_an": "PO830170", "sigle_an": "SOC-A",
         "valeur_source": "Majoritaire", "position": "majorite"},
    ]
    assert schema_groupe.resumer_position_politique(declarations) == "divergente"


def test_un_organe_muet_ne_fait_pas_taire_un_organe_qui_declare():
    """Muet ≠ contradiction. La qualification déclarée l'emporte, le détail reste lisible."""
    declarations = [
        {"organe_an": "PO800496", "valeur_source": "Opposition", "position": "opposition"},
        {"organe_an": "PO830170", "valeur_source": None, "position": None},
    ]
    assert schema_groupe.resumer_position_politique(declarations) == "opposition"
    assert schema_groupe.resumer_position_politique([]) == "non_declaree"


# --------------------------------------------------------------------------
# 4. Le champ publié : vocabulaire, preuve, et un résumé qui ne se choisit pas
# --------------------------------------------------------------------------

def _fiche(position_politique):
    fiche = schema_groupe.make_empty_profil_groupe("AN:REN", "REN", "Renaissance", "AN", "16")
    fiche["position_politique"] = position_politique
    return fiche


def _bloc_valide(**surcharges):
    bloc = {
        "position": "majorite",
        "source_url": SOURCE_AMO30,
        "verifie_le": "2026-09-01",
        "organes": [
            {"organe_an": "PO800538", "sigle_an": "RE",
             "valeur_source": "Majoritaire", "position": "majorite"},
        ],
    }
    bloc.update(surcharges)
    return bloc


def test_le_champ_absent_reste_valide():
    """Les 7 fiches publiées avant le lot n'en portent pas — les invalider ne
    dirait rien de vrai sur elles (même précédent que #653 et #558)."""
    assert schema_groupe.validate_profil_groupe(_fiche(None)) == []


def test_le_bloc_complet_est_valide():
    assert schema_groupe.validate_profil_groupe(_fiche(_bloc_valide())) == []


def test_non_declaree_est_une_valeur_publiee():
    """Distincte d'un champ absent : la source n'a rien déclaré, et le dit."""
    bloc = _bloc_valide(
        position="non_declaree",
        organes=[{"organe_an": "PO845407", "sigle_an": "EPR",
                  "valeur_source": None, "position": None}],
    )
    assert schema_groupe.validate_profil_groupe(_fiche(bloc)) == []
    assert "non_declaree" in schema_groupe.POSITIONS_POLITIQUES_GROUPE


def test_une_position_sans_source_url_est_refusee():
    """Miroir de la règle 6 : la posture individuelle exige déjà un `source_url`."""
    erreurs = schema_groupe.validate_profil_groupe(_fiche(_bloc_valide(source_url="")))
    assert any("source_url" in e for e in erreurs)


def test_non_declaree_exige_aussi_sa_source():
    """Un constat d'absence nomme sa source comme un constat de présence."""
    bloc = _bloc_valide(
        position="non_declaree",
        source_url=None,
        organes=[{"organe_an": "PO845407", "valeur_source": None, "position": None}],
    )
    assert any("source_url" in e for e in schema_groupe.validate_profil_groupe(_fiche(bloc)))


def test_un_resume_que_les_organes_ne_portent_pas_est_refuse():
    """L'invariant central : la posture se dérive des déclarations, jamais choisie."""
    bloc = _bloc_valide(position="opposition")
    erreurs = schema_groupe.validate_profil_groupe(_fiche(bloc))
    assert any("les déclarations publiées" in e for e in erreurs)


def test_un_organe_ne_porte_jamais_une_valeur_de_resume():
    """`non_declaree`/`divergente` résument plusieurs organes, n'en décrivent aucun."""
    bloc = _bloc_valide(
        position="non_declaree",
        organes=[{"organe_an": "PO800538", "valeur_source": None,
                  "position": "divergente"}],
    )
    assert any("organes[0].position" in e for e in schema_groupe.validate_profil_groupe(_fiche(bloc)))


def test_une_traduction_que_la_source_ne_porte_pas_est_refusee():
    bloc = _bloc_valide(
        organes=[{"organe_an": "PO800538", "valeur_source": "Opposition",
                  "position": "majorite"}],
    )
    assert any("ne se traduit pas" in e for e in schema_groupe.validate_profil_groupe(_fiche(bloc)))


# --------------------------------------------------------------------------
# 5. La table committée : chaque entrée porte sa qualification relue
# --------------------------------------------------------------------------

def test_les_dix_entrees_de_la_table_portent_leur_position():
    entrees = groupes_config.charger_correspondance_sigles(CONFIG)
    assert len(entrees) == _ATTENDU
    for entree in entrees:
        bloc = entree[groupes_config.CLE_POSITION_POLITIQUE]
        assert bloc["position"] in schema_groupe.POSITIONS_POLITIQUES_GROUPE
        assert bloc["verifie_le"]
        assert [o["organe_an"] for o in bloc["organes"]] == entree["organes_an"]


def _config_mutee(tmp_path, mutation):
    document = json.loads(CONFIG.read_text(encoding="utf-8"))
    mutation(document["correspondance_sigles_an"])
    chemin = tmp_path / "groupes_reels.json"
    chemin.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    return chemin


@pytest.mark.parametrize(
    "mutation, attendu",
    [
        (lambda bloc: bloc["groupes"][0].pop("position_politique_an"),
         "position_politique_an"),
        (lambda bloc: bloc["groupes"][0]["position_politique_an"].__setitem__(
            "position", "majoritaire"), "hors vocabulaire"),
        (lambda bloc: bloc["groupes"][0]["position_politique_an"].__setitem__(
            "position", "opposition"), "Le résumé se dérive"),
        (lambda bloc: bloc["groupes"][0]["position_politique_an"].pop("verifie_le"),
         "verifie_le"),
        (lambda bloc: bloc["groupes"][0]["position_politique_an"]["organes"][0].__setitem__(
            "organe_an", "PO999999"), "fil-piège"),
        (lambda bloc: bloc["groupes"][0]["position_politique_an"]["organes"][0].__setitem__(
            "valeur_source", "Opposition"), "ne se traduit pas"),
    ],
)
def test_une_table_qui_ment_est_refusee(tmp_path, mutation, attendu):
    chemin = _config_mutee(tmp_path, mutation)
    with pytest.raises(groupes_config.CorrespondanceSiglesInvalide) as exc:
        groupes_config.charger_correspondance_sigles(chemin)
    assert attendu in str(exc.value)


def test_le_bloc_publie_porte_lurl_de_la_source():
    """Une seule URL dans le fichier, recopiée dans chaque fiche : une URL
    répétée dix fois se corrige neuf fois."""
    bloc = groupes_config.position_politique_publiee("REN", "16", CONFIG)
    assert bloc["source_url"] == SOURCE_AMO30
    assert bloc["position"] == "majorite"
    assert schema_groupe.validate_profil_groupe(_fiche(bloc)) == []


def test_un_groupe_sans_legislature_ne_recoit_aucune_position():
    """L'AN qualifie ses groupes législature par législature : sans elle, il n'y
    a rien à lire, et un repli inventerait une posture."""
    with pytest.raises(groupes_config.CorrespondanceSiglesInvalide):
        groupes_config.position_politique_publiee("LR", None, CONFIG)


# --------------------------------------------------------------------------
# 6. Le garde-fou : §4b du portail de qualité, seuil 0 (patron du §5b, #525)
# --------------------------------------------------------------------------

import check_quality_gate  # noqa: E402

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



def _fiche_publiee(dossier: Path, nom: str, chambre: str, sigle: str,
                   legislature, position_politique=None) -> None:
    fiche = schema_groupe.make_empty_profil_groupe(
        f"{chambre}:{sigle}", sigle, sigle, chambre, legislature
    )
    fiche["position_politique"] = position_politique
    dossier.mkdir(parents=True, exist_ok=True)
    (dossier / nom).write_text(json.dumps(fiche, ensure_ascii=False), encoding="utf-8")


def test_le_gate_bloque_une_fiche_an_sans_entree_dans_la_table(tmp_path):
    """Seuil 0, et le message NOMME le couple manquant.

    C'est le patron du §5b (#525) : une correspondance manquante ne se
    manifeste pas comme une erreur, elle se manifeste comme une posture absente
    sur la fiche où elle comptait le plus.
    """
    groupes = tmp_path / "groupes"
    _fiche_publiee(groupes, "groupe-AN-XYZ-16.json", "AN", "XYZ", "16")
    hard, console, _ = check_quality_gate._report_position_politique(CONFIG, groupes)
    assert len(hard) == 1
    assert "'XYZ'" in hard[0] and "16" in hard[0]
    assert "✗" in console


def test_le_gate_laisse_passer_une_fiche_senatoriale(tmp_path):
    """AMO30 ne qualifie que les organes de l'Assemblée : réclamer la donnée
    aux 2 fiches `groupe-Senat-*` serait en réclamer une qui n'existe pas."""
    groupes = tmp_path / "groupes"
    _fiche_publiee(groupes, "groupe-Senat-LR.json", "Senat", "LR", None)
    hard, _, _ = check_quality_gate._report_position_politique(CONFIG, groupes)
    assert hard == []


def test_le_gate_ne_reclame_pas_le_champ_aux_fiches_davant_le_lot(tmp_path):
    """Non bloquant, et compté : c'est le compteur de migration, il tombe à 0
    au premier run réel."""
    groupes = tmp_path / "groupes"
    _fiche_publiee(groupes, "groupe-AN-REN-16.json", "AN", "REN", "16")
    hard, console, _ = check_quality_gate._report_position_politique(CONFIG, groupes)
    assert hard == []
    assert "sans le champ" in console


def test_le_gate_bloque_une_position_publiee_qui_contredit_la_table(tmp_path):
    """Une qualification publiée qui n'est plus adossée à sa preuve relue n'est
    plus traçable (AGENTS.md §2 règle 2)."""
    groupes = tmp_path / "groupes"
    _fiche_publiee(
        groupes, "groupe-AN-REN-16.json", "AN", "REN", "16",
        position_politique=_bloc_valide(
            position="opposition",
            organes=[{"organe_an": "PO800538", "sigle_an": "RE",
                      "valeur_source": "Opposition", "position": "opposition"}],
        ),
    )
    hard, _, _ = check_quality_gate._report_position_politique(CONFIG, groupes)
    assert len(hard) == 1
    assert "≠ position committée" in hard[0]


def test_le_gate_accepte_la_position_que_la_table_committe(tmp_path):
    groupes = tmp_path / "groupes"
    _fiche_publiee(
        groupes, "groupe-AN-REN-16.json", "AN", "REN", "16",
        position_politique=groupes_config.position_politique_publiee("REN", "16", CONFIG),
    )
    hard, console, _ = check_quality_gate._report_position_politique(CONFIG, groupes)
    assert hard == []
    assert "majorite : 1" in console


def test_le_gate_sans_fiche_an_ne_reclame_pas_la_table(tmp_path):
    """Une table absente n'est pas un défaut quand aucune fiche AN n'est
    publiée : un contrôle sans objet ne bloque pas un commit."""
    config_vide = tmp_path / "groupes_reels.json"
    config_vide.write_text(json.dumps({"groupes": []}), encoding="utf-8")
    groupes = tmp_path / "groupes"
    groupes.mkdir()
    hard, _, _ = check_quality_gate._report_position_politique(config_vide, groupes)
    assert hard == []


def test_le_gate_bloque_sur_une_table_invalide_quand_une_fiche_an_existe(tmp_path):
    config_vide = tmp_path / "groupes_reels.json"
    config_vide.write_text(json.dumps({"groupes": []}), encoding="utf-8")
    groupes = tmp_path / "groupes"
    _fiche_publiee(groupes, "groupe-AN-REN-16.json", "AN", "REN", "16")
    hard, _, _ = check_quality_gate._report_position_politique(config_vide, groupes)
    assert len(hard) == 1
    assert "correspondance_sigles_an" in hard[0]


def test_la_section_4b_compte_dans_le_code_de_sortie(tmp_path, monkeypatch, capsys):
    """Une section qui rapporte sans peser sur `exit_code` ne garde rien."""
    profils = tmp_path / "profiles"
    profils.mkdir()
    groupes = tmp_path / "groupes"
    _fiche_publiee(groupes, "groupe-AN-XYZ-16.json", "AN", "XYZ", "16")
    for nom in ("gouvernements", "raw", "figes_absent"):
        (tmp_path / nom).mkdir()
    for nom, cle in (("gouvernements_reels.json", "gouvernements"),
                     ("candidats.json", "candidats")):
        (tmp_path / nom).write_text(json.dumps({cle: []}), encoding="utf-8")
    # `groupes: []` : la §4 n'attend alors AUCUN fichier et ne peut pas
    # bloquer, si bien qu'un `exit 1` ne peut venir que de la §4b. La table de
    # correspondance, elle, est celle du dépôt — la fiche `XYZ` n'y est pas.
    config = tmp_path / "groupes_reels.json"
    config.write_text(json.dumps({
        "groupes": [],
        "correspondance_sigles_an": json.loads(
            CONFIG.read_text(encoding="utf-8")
        )["correspondance_sigles_an"],
    }, ensure_ascii=False), encoding="utf-8")

    correspondance = tmp_path / "correspondance_acteurs_an.json"
    correspondance.write_text(json.dumps({
        "schema_version": "1",
        "genere_le": "2026-09-01T00:00:00+0000",
        "source_referentiel": "https://data.assemblee-nationale.fr/",
        "correspondances": {},
    }), encoding="utf-8")

    monkeypatch.setattr(sys, "argv", [
        "check_quality_gate.py",
        "--profiles-dir", str(profils),
        "--groupes-dir", str(groupes),
        "--gouvernements-dir", str(tmp_path / "gouvernements"),
        "--raw-dir", str(tmp_path / "raw"),
        "--candidats", str(tmp_path / "candidats.json"),
        "--groupes-config", str(config),
        "--gouvernements-config", str(tmp_path / "gouvernements_reels.json"),
        "--amendements-cache-dir", str(tmp_path / "cache_absent"),
        "--amendements-figes-dir", str(tmp_path / "figes_absent"),
        "--correspondance-acteurs", str(correspondance),
        "--blob-warn-mo", "0",
    ])
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    code = check_quality_gate.main()
    sortie = capsys.readouterr().out
    assert code == 1
    assert "COMMIT BLOQUÉ" in sortie
    bloc_4b = sortie.partition("┌─ 4b/6")[2].partition("└")[0]
    assert "✗" in bloc_4b and "XYZ" in bloc_4b
    # Et rien d'autre n'a bloqué : la §4 n'attendait aucun fichier.
    assert "✗" not in sortie.partition("┌─ 4/4")[2].partition("└")[0]
