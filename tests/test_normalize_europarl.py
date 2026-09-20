import sys
from pathlib import Path

# Les modules testés vivent dans src/, à côté du dossier tests/.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from licences import LICENCE_EUROPARL
from normalize_europarl import _extract_groupe, normalize_europarl
from schema_pivot import SCHEMA_VERSION, validate_profil


# ---------------------------------------------------------------------------
# Fixture : profil brut Open Data Portal Parlement européen minimal
# ---------------------------------------------------------------------------

def _raw_ue_profile(extra: dict = None) -> dict:
    """Retourne un profil brut europarl minimal pour les tests."""
    base = {
        "identifiant_pe": "1234",
        "nom_complet": "Jean Dupont",
        "url_source": "https://www.europarl.europa.eu/meps/fr/1234",
        "meta": {
            "genere_le": "2026-07-29T10:00:00+0000",
            "licence_donnees": "CC0",
        },
        "mandats_europeens": [
            {
                "type": "EU_POLITICAL_GROUP",
                "organisation_nom": "Rassemblement ID",
                "organisation_sigle": "ID",
                "role": "def/ep-roles/MEMBER",
                "role_label": "Membre",
                "debut": "2019-07-02",
                "fin": "2024-07-15",
                "actif": False,
            },
            {
                "type": "EU_POLITICAL_GROUP",
                "organisation_nom": "Patriotes pour l'Europe",
                "organisation_sigle": "PfE",
                "role": "def/ep-roles/MEMBER",
                "role_label": "Membre",
                "debut": "2024-07-16",
                "fin": None,
                "actif": True,
            },
            {
                "type": "EU_INSTITUTION",
                "organisation_nom": None,
                "organisation_sigle": "10e législature",
                "role": "def/ep-roles/MEMBER",
                "role_label": "Député européen",
                "debut": "2024-07-16",
                "fin": None,
                "actif": True,
            },
            {
                "type": "COMMITTEE_PARLIAMENTARY_STANDING",
                "organisation_nom": "Commission des affaires étrangères",
                "organisation_sigle": "AFET",
                "role": "def/ep-roles/MEMBER",
                "role_label": "Membre",
                "debut": "2024-09-01",
                "fin": None,
                "actif": True,
            },
        ],
    }
    if extra:
        base.update(extra)
    return base


# ---------------------------------------------------------------------------
# _extract_groupe
# ---------------------------------------------------------------------------

def test_extract_groupe_retourne_groupe_actif_en_priorite():
    mandats = _raw_ue_profile()["mandats_europeens"]
    assert _extract_groupe(mandats) == "Patriotes pour l'Europe"


def test_extract_groupe_retourne_groupe_inactif_si_aucun_actif():
    mandats = [
        {
            "type": "EU_POLITICAL_GROUP",
            "organisation_nom": "Ancien groupe",
            "organisation_sigle": "AG",
            "actif": False,
        }
    ]
    assert _extract_groupe(mandats) == "Ancien groupe"


def test_extract_groupe_retourne_none_si_aucun_groupe():
    mandats = [
        {
            "type": "EU_INSTITUTION",
            "organisation_nom": None,
            "organisation_sigle": "10e législature",
            "actif": True,
        }
    ]
    assert _extract_groupe(mandats) is None


def test_extract_groupe_utilise_sigle_si_nom_absent():
    mandats = [
        {
            "type": "EU_POLITICAL_GROUP",
            "organisation_nom": None,
            "organisation_sigle": "GUE",
            "actif": True,
        }
    ]
    assert _extract_groupe(mandats) == "GUE"


# ---------------------------------------------------------------------------
# Mapping _CATEGORIE_MAP via normalize_europarl
# ---------------------------------------------------------------------------

def test_categorie_map_eu_institution_mappe_mandat_electif():
    pivot = normalize_europarl(_raw_ue_profile())
    m = next(m for m in pivot["mandats"] if m["label"] == "10e législature")
    assert m["categorie"] == "mandat_electif"


def test_categorie_map_committee_standing_mappe_commission():
    pivot = normalize_europarl(_raw_ue_profile())
    m = next(m for m in pivot["mandats"] if m["label"] == "Commission des affaires étrangères")
    assert m["categorie"] == "commission"


def test_categorie_map_eu_political_group_mappe_autre():
    pivot = normalize_europarl(_raw_ue_profile())
    groupes = [m for m in pivot["mandats"] if "Patriotes" in m["label"] or "ID" in m["label"]]
    for m in groupes:
        assert m["categorie"] == "autre"


def test_categorie_map_type_inconnu_mappe_autre():
    raw = _raw_ue_profile()
    raw["mandats_europeens"] = [
        {
            "type": "TYPE_INCONNU",
            "organisation_nom": "Inconnu",
            "organisation_sigle": "INC",
            "role": "def/ep-roles/MEMBER",
            "role_label": "Membre",
            "debut": "2024-01-01",
            "fin": None,
            "actif": True,
        }
    ]
    pivot = normalize_europarl(raw)
    assert pivot["mandats"][0]["categorie"] == "autre"


# ---------------------------------------------------------------------------
# synchro_le / meta.genere_le
# ---------------------------------------------------------------------------

def test_synchro_le_propagee_depuis_meta():
    pivot = normalize_europarl(_raw_ue_profile())
    assert pivot["sources"][0]["synchro_le"] == "2026-07-29T10:00:00+0000"


def test_meta_genere_le_propagee_depuis_meta():
    pivot = normalize_europarl(_raw_ue_profile())
    assert pivot["meta"]["genere_le"] == "2026-07-29T10:00:00+0000"


# ---------------------------------------------------------------------------
# Structure générale
# ---------------------------------------------------------------------------

def test_pivot_valide_selon_schema():
    pivot = normalize_europarl(_raw_ue_profile())
    errors = validate_profil(pivot)
    assert errors == [], f"Erreurs de schéma inattendues : {errors}"


def test_pivot_schema_version():
    pivot = normalize_europarl(_raw_ue_profile())
    assert pivot["schema_version"] == SCHEMA_VERSION


def test_pivot_chambre_est_pe():
    pivot = normalize_europarl(_raw_ue_profile())
    assert pivot["chambre"] == "PE"


def test_pivot_id_est_le_slug_quand_il_est_fourni():
    # #487 : l'`id` pivot est le slug. `normalize_europarl` ne peut pas le
    # déduire de `ue_profile`, il lui est donc passé par le pipeline.
    pivot = normalize_europarl(_raw_ue_profile(), slug="jean-dupont")
    assert pivot["id"] == "jean-dupont"


def test_pivot_id_repli_sur_l_identifiant_de_source_sans_slug():
    # Sans slug, pas de slug inventé depuis `nom_complet` : ce serait dériver
    # l'identifiant d'une donnée de collecte, le défaut que #487 retire.
    pivot = normalize_europarl(_raw_ue_profile())
    assert pivot["id"] == "europarl:1234"


def test_pivot_nom():
    pivot = normalize_europarl(_raw_ue_profile())
    assert pivot["nom"] == "Jean Dupont"


def test_pivot_groupe_actif():
    pivot = normalize_europarl(_raw_ue_profile())
    assert pivot["groupe"] == "Patriotes pour l'Europe"


def test_pivot_parti_optionnel():
    pivot = normalize_europarl(_raw_ue_profile(), parti="Rassemblement National")
    assert pivot["parti"] == "Rassemblement National"


def test_pivot_parti_absent_par_defaut():
    pivot = normalize_europarl(_raw_ue_profile())
    assert pivot["parti"] is None


def test_pivot_provenance_defaut_candidat_declare():
    pivot = normalize_europarl(_raw_ue_profile())
    assert pivot["meta"]["provenance"] == "candidat_declare"


def test_pivot_provenance_roster_groupe_propagee():
    pivot = normalize_europarl(_raw_ue_profile(), provenance="roster_groupe")
    assert pivot["meta"]["provenance"] == "roster_groupe"


def test_pivot_source_type_europarl():
    pivot = normalize_europarl(_raw_ue_profile())
    assert pivot["sources"][0]["type"] == "europarl"


def test_pivot_meta_licence_derivee_des_sources():
    """`licence_donnees` vient de `sources[]`, plus du profil brut (#530).

    Le profil brut de ce test annonce « CC0 » ; le pivot publie la licence du
    Portail Open Data du Parlement européen, parce que c'est de là que vient
    `sources[0]`. La propagation d'avant permettait à un collecteur d'annoncer
    n'importe quelle licence pour la source qu'il venait d'écrire — et sur les
    données réelles elle ne changeait rien, `candidate_profile_ue` écrivant déjà
    ce libellé mot pour mot.
    """
    pivot = normalize_europarl(_raw_ue_profile())
    assert pivot["meta"]["licence_donnees"] == LICENCE_EUROPARL


def test_pivot_mandats_count():
    pivot = normalize_europarl(_raw_ue_profile())
    assert len(pivot["mandats"]) == 4


def test_pivot_profil_vide_ne_leve_pas():
    pivot = normalize_europarl({})
    assert isinstance(pivot, dict)


# ---------------------------------------------------------------------------
# #922 — l'identité d'un profil européen, et pourquoi elle manquait
#
# Ce normaliseur ne posait AUCUN bloc `identite`. La conséquence ne se voyait
# pas dans le profil : elle se voyait dans l'appariement au Répertoire national
# des élus, dont la clé praticable est (nom, prénom, date de naissance). Les
# quatre candidats déclarés dont tout le parcours est européen — Bardella,
# Philippot, Massard, Glucksmann — ressortaient « sans date de naissance »,
# donc non appariables automatiquement, alors que le portail la publie et que
# le profil BRUT la portait déjà sous `mandat_europeen.date_naissance`.
#
# Mesuré le 15/09/2026 sur `origin/main` : les quatre ont `identite` vide dans
# `pivot_data/`, et `1995-09-13`, `1981-10-24`, `1978-08-24`, `1979-10-15` dans
# `raw_data/`. La donnée était collectée, elle s'arrêtait à la normalisation.
# ---------------------------------------------------------------------------

def test_la_date_de_naissance_atteint_le_pivot():
    profil = normalize_europarl(_raw_ue_profile({"date_naissance": "1995-09-13"}))

    assert profil["identite"]["date_naissance"] == "1995-09-13"


def test_le_lieu_de_naissance_est_recopie_verbatim():
    """Le portail écrit parfois un lieu mal espacé — « Saint- Brieuc », mesuré
    sur lydie-massard. Ce n'est pas corrigé : c'est ce que la source publie, et
    le réparer supposerait de savoir où le mot se coupe."""
    profil = normalize_europarl(_raw_ue_profile({"lieu_naissance": "Saint- Brieuc"}))

    assert profil["identite"]["lieu_naissance"] == "Saint- Brieuc"


def test_sans_etat_civil_aucun_bloc_identite_n_est_publie():
    """Un bloc qui ne porterait que `source_url` dirait « on a cherché », pas
    « voici qui c'est ». Même règle que `normalize_profil` (§2 règle 5)."""
    profil = normalize_europarl(_raw_ue_profile())

    assert "identite" not in profil or not profil["identite"]


def test_une_date_absente_reste_nulle_jamais_vide():
    """`null`, jamais `""` — AGENTS.md §4."""
    profil = normalize_europarl(
        _raw_ue_profile({"date_naissance": "", "lieu_naissance": "Drancy"}))

    assert profil["identite"]["date_naissance"] is None
    assert profil["identite"]["lieu_naissance"] == "Drancy"


def test_l_identite_porte_sa_source():
    profil = normalize_europarl(_raw_ue_profile({"date_naissance": "1979-10-15"}))

    assert profil["identite"]["source_url"] == "https://www.europarl.europa.eu/meps/fr/1234"


def test_le_profil_reste_valide_avec_son_identite():
    profil = normalize_europarl(_raw_ue_profile({
        "date_naissance": "1979-10-15", "lieu_naissance": "Boulogne-Billancourt"}))
    profil["meta"].pop("avertissements", None)

    assert validate_profil(profil) == []
