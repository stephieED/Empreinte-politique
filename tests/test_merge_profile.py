"""Tests pour merge_profile.py (fusion additive des profils bruts et pivot)."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from profil_brut import charger_profil_brut, est_partitionne
from merge_profile import (
    preserver_collectes_non_vides,
    clean_stale_textes_portes,
    load_existing_document,
    merge_lists_by_key,
    merge_pivot_profile,
    merge_raw_dirs,
    merge_raw_profile,
    preserve_stable_freshness_timestamps,
)


def test_merge_lists_by_key_keeps_old_and_adds_new_only():
    old = [{"id": 1, "titre": "A"}, {"id": 2, "titre": "B"}]
    new = [{"id": 2, "titre": "B modifié"}, {"id": 3, "titre": "C"}]
    merged = merge_lists_by_key(old, new, key_fn=lambda x: x["id"])
    assert merged == [{"id": 1, "titre": "A"}, {"id": 2, "titre": "B"}, {"id": 3, "titre": "C"}]


def test_merge_lists_by_key_handles_empty_inputs():
    assert merge_lists_by_key(None, None, key_fn=lambda x: x["id"]) == []
    assert merge_lists_by_key([{"id": 1}], None, key_fn=lambda x: x["id"]) == [{"id": 1}]
    assert merge_lists_by_key(None, [{"id": 1}], key_fn=lambda x: x["id"]) == [{"id": 1}]


def test_merge_raw_profile_returns_new_when_no_existing_file():
    new = {"slug": "x", "votes": [{"numero_scrutin": "1", "date": "2024-01-01"}]}
    assert merge_raw_profile(None, new) is new


def test_merge_raw_profile_preserves_votes_lost_in_new_fetch():
    old = {
        "slug": "x",
        "chambre": "deputes",
        "identite": {"nom_complet": "X Y"},
        "mandats": [],
        "votes": [
            {"numero_scrutin": "100", "date": "2023-01-01", "titre": "Ancien vote", "position": "pour"},
        ],
        "votes_source": "open data Assemblée nationale (législature 15)",
        "dossiers_legislatifs": [],
        "interventions": [
            {"id": 111, "url": "https://a.fr/1", "texte": "ancienne intervention"},
        ],
        "meta": {"warnings": []},
    }
    # Nouvelle collecte : l'API des votes/interventions a temporairement échoué.
    new = {
        "slug": "x",
        "chambre": "deputes",
        "identite": {"nom_complet": "X Y"},
        "mandats": [],
        "votes": [],
        "votes_source": None,
        "dossiers_legislatifs": [],
        "interventions": [],
        "meta": {"warnings": ["votes introuvables : ...", "identité introuvable : ..."]},
    }

    merged = merge_raw_profile(old, new)

    assert merged["votes"] == old["votes"]
    assert merged["interventions"] == old["interventions"]
    assert merged["votes_source"] == old["votes_source"]
    # Les avertissements devenus faux après restauration des données doivent disparaître.
    assert not any(w.startswith("votes introuvables") for w in merged["meta"]["warnings"])


def test_merge_raw_profile_adds_new_entries_without_dropping_old_ones():
    old = {
        "votes": [{"numero_scrutin": "1", "date": "2024-01-01"}],
        "interventions": [{"id": 1, "url": "u1"}],
        "mandats": [],
        "dossiers_legislatifs": [],
        "meta": {"warnings": []},
    }
    new = {
        "votes": [
            {"numero_scrutin": "1", "date": "2024-01-01"},
            {"numero_scrutin": "2", "date": "2024-02-01"},
        ],
        "interventions": [{"id": 1, "url": "u1"}, {"id": 2, "url": "u2"}],
        "mandats": [],
        "dossiers_legislatifs": [],
        "meta": {"warnings": []},
    }

    merged = merge_raw_profile(old, new)

    assert len(merged["votes"]) == 2
    assert len(merged["interventions"]) == 2


def test_merge_raw_profile_ecarte_dossiers_legislatifs_sans_role_connu():
    old = {
        "votes": [], "interventions": [], "mandats": [],
        "dossiers_legislatifs": [
            {"legislature": "16", "id": "2020-XYZ", "titre": "Dossier hérité (liste globale)", "date_max": "2020-02-01"},
        ],
        "meta": {"warnings": []},
    }
    new = {
        "votes": [], "interventions": [], "mandats": [],
        "dossiers_legislatifs": [
            {"legislature": "17", "id": "DLR5L17N1", "titre": "Dossier officiel", "role": "auteur", "type_rapport": None, "stade_procedural": "depose", "date_max": "2024-02-01"},
        ],
        "meta": {"warnings": []},
    }

    merged = merge_raw_profile(old, new)

    assert len(merged["dossiers_legislatifs"]) == 1
    assert merged["dossiers_legislatifs"][0]["titre"] == "Dossier officiel"


def test_merge_raw_profile_merges_mandat_europeen():
    old = {
        "votes": [], "interventions": [], "mandats": [], "dossiers_legislatifs": [],
        "meta": {"warnings": []},
        "mandat_europeen": {"mandats_europeens": [{"type": "MEMBER", "organisation_sigle": "AFET", "role": None, "debut": "2019-07-02"}]},
    }
    new = {
        "votes": [], "interventions": [], "mandats": [], "dossiers_legislatifs": [],
        "meta": {"warnings": []},
        "mandat_europeen": {"mandats_europeens": [{"type": "MEMBER", "organisation_sigle": "ENVI", "role": None, "debut": "2024-07-16"}]},
    }

    merged = merge_raw_profile(old, new)

    keys = {(m["organisation_sigle"]) for m in merged["mandat_europeen"]["mandats_europeens"]}
    assert keys == {"AFET", "ENVI"}


def test_merge_raw_profile_preserves_amendements_on_empty_new_fetch():
    # Un échec/vide transitoire de l'open data amendements ne doit pas effacer
    # des amendements déjà collectés lors d'une régénération précédente.
    old = {
        "votes": [], "interventions": [], "mandats": [], "dossiers_legislatifs": [],
        "meta": {"warnings": []},
        "amendements": [{"numero": "AS1", "texte_vise": "PRJL01", "date": "2024-01-10", "source_url": None}],
    }
    new = {
        "votes": [], "interventions": [], "mandats": [], "dossiers_legislatifs": [],
        "meta": {"warnings": []},
        "amendements": [],
    }

    merged = merge_raw_profile(old, new)

    assert merged["amendements"] == old["amendements"]


def test_merge_raw_profile_amendements_new_value_wins_on_collision():
    old = {
        "votes": [], "interventions": [], "mandats": [], "dossiers_legislatifs": [],
        "meta": {"warnings": []},
        "amendements": [{"numero": "AS1", "texte_vise": "PRJL01", "date": "2024-01-10", "source_url": None, "sort": "Adopté"}],
    }
    new = {
        "votes": [], "interventions": [], "mandats": [], "dossiers_legislatifs": [],
        "meta": {"warnings": []},
        "amendements": [
            {"numero": "AS1", "texte_vise": "PRJL01", "date": "2024-01-10", "source_url": None, "sort": "Rejeté"},
            {"numero": "AS2", "texte_vise": "PRJL01", "date": "2024-01-11", "source_url": None, "sort": "Adopté"},
        ],
    }

    merged = merge_raw_profile(old, new)

    assert len(merged["amendements"]) == 2
    as1 = next(a for a in merged["amendements"] if a["numero"] == "AS1")
    assert as1["sort"] == "Rejeté"


def test_merge_pivot_profile_preserves_data_and_dedups_sources():
    old = {
        "sources": [{"type": "nosdeputes", "url": "u", "synchro_le": "2026-01-01T00:00:00"}],
        "mandats": [{"label": "Commission X", "categorie": "commission", "fonction": "membre", "debut": "2022-01-01"}],
        "votes": [{"numero_scrutin": "1", "date": "2024-01-01", "texte": "T"}],
        "textes_portes": [],
        # #710 — les tags sont DÉRIVÉS des interventions, plus unis d'une liste à
        # l'autre : les interventions du fixture portent donc le thème dont on
        # attend le tag.
        "interventions": [
            {"source_url": "https://a.fr/1", "date": "2023-01-01", "theme_officiel": "Budget"}
        ],
        "tags_thematiques": ["budget"],
        "meta": {"warnings": []},
    }
    new = {
        "sources": [{"type": "nosdeputes", "url": "u2", "synchro_le": "2026-02-01T00:00:00"}],
        "mandats": [],
        "votes": [],
        "textes_portes": [],
        "interventions": [
            {"source_url": "https://a.fr/2", "date": "2023-02-01", "theme_officiel": "Fiscalité"}
        ],
        "tags_thematiques": ["fiscalité"],
        "meta": {"warnings": ["votes introuvables : ..."]},
    }

    merged = merge_pivot_profile(old, new)

    assert merged["votes"] == old["votes"]
    assert merged["mandats"] == old["mandats"]
    assert merged["interventions"] == old["interventions"] + new["interventions"]
    assert merged["sources"] == [{"type": "nosdeputes", "url": "u2", "synchro_le": "2026-02-01T00:00:00"}]
    assert merged["tags_thematiques"] == ["budget", "fiscalité"]
    assert not any(w.startswith("votes introuvables") for w in merged["meta"]["warnings"])


def test_merge_pivot_profile_dedups_textes_portes_sur_meme_dossier():
    # Deux entrées du même dossier (même source_url) avec un rôle factuel
    # connu des deux côtés : la nouvelle version l'emporte (pas de doublon).
    old = {
        "sources": [], "mandats": [], "votes": [],
        "textes_portes": [
            {"titre": "Texte X", "role": "rapporteur", "date_min": "2024-01-01", "date_max": "2024-02-01", "legislature": "16", "source_url": "https://a.fr/1"},
        ],
        "interventions": [], "tags_thematiques": [], "meta": {"warnings": []},
    }
    new = {
        "sources": [], "mandats": [], "votes": [],
        "textes_portes": [
            {"titre": "Texte X", "role": "co-rapporteur", "type_rapport": "rapporteur_avis", "stade_procedural": "adopte", "date_min": "2024-01-01", "date_max": "2024-02-01", "legislature": "16", "source_url": "https://a.fr/1"},
        ],
        "interventions": [], "tags_thematiques": [], "meta": {"warnings": []},
    }

    merged = merge_pivot_profile(old, new)

    assert len(merged["textes_portes"]) == 1
    assert merged["textes_portes"][0]["role"] == "co-rapporteur"


def test_merge_pivot_profile_ecarte_textes_portes_sans_role_connu():
    # Liste globale héritée de NosDéputés (mêmes dossiers pour tout le monde,
    # role toujours null) : doit être écartée lors de la fusion, même si elle
    # ne rentre pas en collision avec les nouvelles entrées officielles.
    old = {
        "sources": [], "mandats": [], "votes": [],
        "textes_portes": [
            {"titre": "Texte hérité (liste globale)", "role": None, "date_min": "2020-01-01", "date_max": "2020-02-01", "legislature": "16", "source_url": "https://www.nosdeputes.fr/16/dossier/texte-herite"},
        ],
        "interventions": [], "tags_thematiques": [], "meta": {"warnings": []},
    }
    new = {
        "sources": [], "mandats": [], "votes": [],
        "textes_portes": [
            {"titre": "Texte officiel", "role": "auteur", "type_rapport": None, "stade_procedural": "depose", "date_min": "2024-01-01", "date_max": "2024-02-01", "legislature": "17", "source_url": "https://www.assemblee-nationale.fr/dyn/17/dossiers/texte-officiel"},
        ],
        "interventions": [], "tags_thematiques": [], "meta": {"warnings": []},
    }

    merged = merge_pivot_profile(old, new)

    assert len(merged["textes_portes"]) == 1
    assert merged["textes_portes"][0]["titre"] == "Texte officiel"


def test_clean_stale_textes_portes_garde_l_entree_identifiee():
    """Depuis #668 la reprise départage sur l'IDENTIFIANT, plus sur le schéma.

    Le critère d'origine — « l'entrée la plus complète », `type_rapport` et
    `stade_procedural` présents — ne discriminait plus rien : les 940 entrées
    publiées le 31/08/2026 portent toutes les deux clés. Voir
    `tests/test_textes_portes_cle_fusion_668.py` pour le garde-fou complet, sur
    réductions verbatim du corpus.
    """
    textes = [
        {"titre": "Texte Y", "role": "rapporteur", "type_rapport": None, "stade_procedural": None, "date_min": "2024-01-01", "legislature": "16", "source_url": None},
        {"titre": "Texte Y", "dossier_id": "DLR5L16N00001", "role": "rapporteur", "type_rapport": None, "stade_procedural": None, "date_min": "2024-01-01", "legislature": "16", "source_url": "https://a.fr/2"},
    ]

    cleaned = clean_stale_textes_portes(textes)

    assert len(cleaned) == 1
    assert cleaned[0]["dossier_id"] == "DLR5L16N00001"


def test_merge_pivot_profile_amendements_additifs_preserve_anciennes_entrees():
    # Un échec/vide transitoire de la source open data amendements ne doit pas
    # effacer des amendements déjà collectés lors d'une régénération précédente.
    old = {
        "sources": [], "mandats": [], "votes": [], "textes_portes": [],
        "amendements": [
            {"numero": "AS1", "texte_vise": "T1", "date": "2025-01-01", "sort": "adopté", "type_deposant": "depute"},
        ],
        "interventions": [], "tags_thematiques": [], "meta": {"warnings": []},
    }
    new = {
        "sources": [], "mandats": [], "votes": [], "textes_portes": [],
        "amendements": [],
        "interventions": [], "tags_thematiques": [], "meta": {"warnings": []},
    }

    merged = merge_pivot_profile(old, new)

    assert merged["amendements"] == old["amendements"]


def test_merge_pivot_profile_amendements_nouvelle_valeur_gagne_sur_collision():
    old = {
        "sources": [], "mandats": [], "votes": [], "textes_portes": [],
        "amendements": [
            {"numero": "AS1", "texte_vise": "T1", "date": "2025-01-01", "sort": "en attente", "type_deposant": "depute"},
        ],
        "interventions": [], "tags_thematiques": [], "meta": {"warnings": []},
    }
    new = {
        "sources": [], "mandats": [], "votes": [], "textes_portes": [],
        "amendements": [
            {"numero": "AS1", "texte_vise": "T1", "date": "2025-01-01", "sort": "adopté", "type_deposant": "depute"},
            {"numero": "AS2", "texte_vise": "T2", "date": "2025-02-01", "sort": "rejeté", "type_deposant": "depute"},
        ],
        "interventions": [], "tags_thematiques": [], "meta": {"warnings": []},
    }

    merged = merge_pivot_profile(old, new)

    assert len(merged["amendements"]) == 2
    as1 = next(a for a in merged["amendements"] if a["numero"] == "AS1")
    assert as1["sort"] == "adopté"


def test_prune_stale_warnings_removes_questions_warning_when_questions_present():
    """Le warning "questions indisponibles" doit être retiré après fusion si des
    questions (type_detail == "question") sont présentes dans les interventions."""
    from merge_profile import merge_raw_profile

    old = {
        "slug": "jean-dupont",
        "chambre": "deputes",
        "identite": {"nom_complet": "Jean Dupont"},
        "mandats": [],
        "votes": [],
        "votes_source": None,
        "dossiers_legislatifs": [],
        "amendements": [],
        "interventions": [
            {"id": "question_QANR5L17QE1", "type_detail": "question", "url": "https://..."},
        ],
        "meta": {"warnings": [], "synchro_sources": {}},
    }
    new = {
        "slug": "jean-dupont",
        "chambre": "deputes",
        "identite": {"nom_complet": "Jean Dupont"},
        "mandats": [],
        "votes": [],
        "votes_source": None,
        "dossiers_legislatifs": [],
        "amendements": [],
        "interventions": [],
        "meta": {
            "warnings": ["questions indisponibles : erreur réseau"],
            "synchro_sources": {"nosdeputes": None, "assemblee_nationale": None, "assemblee_nationale_questions": None},
        },
    }
    merged = merge_raw_profile(old, new)
    assert not any("questions indisponibles" in w for w in merged["meta"]["warnings"])


def test_prune_stale_warnings_keeps_questions_warning_when_no_questions():
    """Le warning "questions indisponibles" doit être conservé si aucune question
    n'est présente dans les interventions après fusion."""
    from merge_profile import merge_raw_profile

    old = {
        "slug": "jean-dupont",
        "chambre": "deputes",
        "identite": {"nom_complet": "Jean Dupont"},
        "mandats": [], "votes": [], "votes_source": None,
        "dossiers_legislatifs": [], "amendements": [], "interventions": [],
        "meta": {"warnings": [], "synchro_sources": {}},
    }
    new = {
        "slug": "jean-dupont",
        "chambre": "deputes",
        "identite": {"nom_complet": "Jean Dupont"},
        "mandats": [], "votes": [], "votes_source": None,
        "dossiers_legislatifs": [], "amendements": [], "interventions": [],
        "meta": {
            "warnings": ["questions indisponibles : erreur réseau"],
            "synchro_sources": {"nosdeputes": None, "assemblee_nationale": None, "assemblee_nationale_questions": None},
        },
    }
    merged = merge_raw_profile(old, new)
    assert any("questions indisponibles" in w for w in merged["meta"]["warnings"])


def test_merge_pivot_profile_intervention_enrichie_syceron_ancienne_entree_gagne():
    """Quand une intervention déjà présente dans le pivot est enrichie par Syceron
    (theme_officiel, seance, dossier, source renseignés), la stratégie additive
    (ancienne entrée gagne) doit préserver les champs Syceron en cas de refusion
    avec une version NosDéputés seule (champs Syceron absents/null).
    Pas de duplication : une seule entrée pour la même source_url."""
    source_url = "https://nosdeputes.fr/seance/2025-01-15#intervention-123"
    old_interv_enrichie = {
        "date": "2025-01-15",
        "type_detail": "intervention",
        "sujet": "Débat sur le budget",
        "texte": "Je prends la parole pour...",
        "source_url": source_url,
        "theme_officiel": "Finances publiques",
        "seance": {"ref": "PRJLANR5L17B1234", "session_ref": "17ord2024-2025"},
        "dossier": {"point_ordre_du_jour": "PLF 2025"},
        "source": {
            "type": "syceron",
            "url": "https://data.assemblee-nationale.fr/debats/17/2025-01-15.zip",
            "source_id": "syceron_123",
            "legislature": "17",
        },
    }
    old = {
        "sources": [], "mandats": [], "votes": [], "textes_portes": [],
        "amendements": [],
        "interventions": [old_interv_enrichie],
        "tags_thematiques": [], "meta": {"warnings": []},
    }
    # Nouvelle collecte sans Syceron (fallback NosDéputés) : même source_url,
    # champs Syceron absents.
    new_interv_nosdeputes = {
        "date": "2025-01-15",
        "type_detail": "intervention",
        "sujet": "Débat sur le budget",
        "texte": "Je prends la parole pour...",
        "source_url": source_url,
        "theme_officiel": None,
        "seance": None,
        "dossier": None,
        "source": None,
    }
    new = {
        "sources": [], "mandats": [], "votes": [], "textes_portes": [],
        "amendements": [],
        "interventions": [new_interv_nosdeputes],
        "tags_thematiques": [], "meta": {"warnings": []},
    }

    merged = merge_pivot_profile(old, new)

    # Pas de duplication : une seule intervention.
    assert len(merged["interventions"]) == 1
    interv = merged["interventions"][0]
    # L'ancienne entrée (enrichie Syceron) est préservée intégralement.
    assert interv["theme_officiel"] == "Finances publiques"
    assert interv["seance"] is not None
    assert interv["dossier"] is not None
    assert interv["source"] is not None
    assert interv["source"]["type"] == "syceron"


# ---------------------------------------------------------------------------
# merge_pivot_profile — politique de fusion provenance (#189)
# ---------------------------------------------------------------------------

def _base_pivot(meta_extra=None):
    return {
        "sources": [], "mandats": [], "votes": [], "textes_portes": [],
        "amendements": [], "interventions": [], "tags_thematiques": [],
        "meta": {"warnings": [], **(meta_extra or {})},
    }


def test_merge_pivot_profile_candidat_declare_non_degrade_par_run_roster():
    """Un profil déjà enrichi via candidats.json (provenance="candidat_declare",
    parti renseigné) régénéré par un run roster-driven du même slug (#188) ne doit
    jamais perdre son enrichissement éditorial : `parti` reste renseigné et
    `meta.provenance` reste "candidat_declare" (jamais rétrogradé)."""
    old = _base_pivot({"provenance": "candidat_declare"})
    old["parti"] = "La France Insoumise"

    new = _base_pivot({"provenance": "roster_groupe"})
    new["parti"] = None  # generate_roster_candidats.py ne renseigne jamais `parti`.

    merged = merge_pivot_profile(old, new)

    assert merged["parti"] == "La France Insoumise"
    assert merged["meta"]["provenance"] == "candidat_declare"


def test_merge_pivot_profile_candidat_declare_sans_provenance_existante_traite_comme_candidat_declare():
    """Rétro-compatibilité : un pivot existant écrit avant #189 (pas de
    meta.provenance) régénéré par un run roster-driven doit être traité comme
    s'il était "candidat_declare" (valeur par défaut), donc pas rétrogradé."""
    old = _base_pivot()  # pas de "provenance" dans meta
    old["parti"] = "Renaissance"

    new = _base_pivot({"provenance": "roster_groupe"})
    new["parti"] = None

    merged = merge_pivot_profile(old, new)

    assert merged["parti"] == "Renaissance"
    assert merged["meta"]["provenance"] == "candidat_declare"


def test_merge_pivot_profile_roster_groupe_sans_conflit_ecriture_normale():
    """Un profil "roster_groupe" régénéré par un nouveau run roster-driven (pas de
    profil candidat_declare préexistant pour ce slug) garde provenance="roster_groupe" :
    aucune règle de préservation ne s'applique."""
    old = _base_pivot({"provenance": "roster_groupe"})
    new = _base_pivot({"provenance": "roster_groupe"})

    merged = merge_pivot_profile(old, new)

    assert merged["meta"]["provenance"] == "roster_groupe"


def test_merge_pivot_profile_roster_groupe_regenere_par_candidat_declare_prend_le_dessus():
    """Cas inverse : un profil "roster_groupe" devient "candidat_declare" si le
    même slug est désormais suivi via candidats.json (pas de règle de préservation
    à l'envers — seul "candidat_declare" côté ancien profil est protégé)."""
    old = _base_pivot({"provenance": "roster_groupe"})
    new = _base_pivot({"provenance": "candidat_declare"})
    new["parti"] = "Horizons"

    merged = merge_pivot_profile(old, new)

    assert merged["meta"]["provenance"] == "candidat_declare"
    assert merged["parti"] == "Horizons"


def test_preserve_stable_freshness_timestamps_garde_ancien_horodatage_si_contenu_identique():
    """#343 : --pivot-only re-dérive le pivot depuis le profil brut existant (pas de
    réseau) et re-tamponnait genere_le/synchro_le à chaque exécution même quand le
    contenu n'avait pas bougé — trompeur pour un audit de fraîcheur."""
    old = _base_pivot({"genere_le": "2026-08-13T09:17:48+0000"})
    old["sources"] = [{"type": "nosdeputes", "url": "u", "synchro_le": "2026-08-13T09:17:48+0000"}]
    old["votes"] = [{"numero_scrutin": "1", "date": "2024-01-01", "texte": "T"}]

    new = _base_pivot({"genere_le": "2026-08-16T06:50:38+0000"})
    new["sources"] = [{"type": "nosdeputes", "url": "u", "synchro_le": "2026-08-16T06:39:22+0000"}]
    new["votes"] = [{"numero_scrutin": "1", "date": "2024-01-01", "texte": "T"}]

    result = preserve_stable_freshness_timestamps(old, new)

    assert result["meta"]["genere_le"] == "2026-08-13T09:17:48+0000"
    assert result["sources"][0]["synchro_le"] == "2026-08-13T09:17:48+0000"


def test_preserve_stable_freshness_timestamps_laisse_avancer_si_contenu_change():
    old = _base_pivot({"genere_le": "2026-08-13T09:17:48+0000"})
    old["sources"] = [{"type": "nosdeputes", "url": "u", "synchro_le": "2026-08-13T09:17:48+0000"}]
    old["votes"] = [{"numero_scrutin": "1", "date": "2024-01-01", "texte": "T"}]

    new = _base_pivot({"genere_le": "2026-08-16T06:50:38+0000"})
    new["sources"] = [{"type": "nosdeputes", "url": "u", "synchro_le": "2026-08-16T06:39:22+0000"}]
    new["votes"] = [
        {"numero_scrutin": "1", "date": "2024-01-01", "texte": "T"},
        {"numero_scrutin": "2", "date": "2024-02-01", "texte": "T2"},
    ]

    result = preserve_stable_freshness_timestamps(old, new)

    assert result["meta"]["genere_le"] == "2026-08-16T06:50:38+0000"
    assert result["sources"][0]["synchro_le"] == "2026-08-16T06:39:22+0000"


def test_preserve_stable_freshness_timestamps_sans_ancien_pivot():
    new = _base_pivot({"genere_le": "2026-08-16T06:50:38+0000"})
    assert preserve_stable_freshness_timestamps(None, new) is new


def test_preserve_stable_freshness_timestamps_apparie_les_sources_par_type_et_url():
    """#343, extension aux profils groupe/gouvernement/parti : ces documents
    portent une source PAR MEMBRE, donc plusieurs dizaines d'entrées partageant
    le même `type` (mesuré : 63 sources pour 3 types distincts sur un groupe).
    Un appariement sur le seul `type` les écraserait toutes sur la dernière —
    chaque source doit retrouver SON horodatage, pas celui d'une autre."""
    def _doc(genere_le, synchros):
        return {
            "schema_version": "1",
            "type_document": "groupe",
            "meta": {"genere_le": genere_le},
            "sources": [
                {"type": "nosdeputes", "url": f"u{i}", "synchro_le": s}
                for i, s in enumerate(synchros)
            ],
        }

    old = _doc("2026-08-13T00:00:00+0000", ["2026-08-01T00:00:00+0000",
                                            "2026-08-02T00:00:00+0000",
                                            "2026-08-03T00:00:00+0000"])
    new = _doc("2026-08-17T00:00:00+0000", ["2026-08-17T00:00:00+0000",
                                            "2026-08-17T00:00:00+0000",
                                            "2026-08-17T00:00:00+0000"])

    result = preserve_stable_freshness_timestamps(old, new)

    assert result["meta"]["genere_le"] == "2026-08-13T00:00:00+0000"
    assert [s["synchro_le"] for s in result["sources"]] == [
        "2026-08-01T00:00:00+0000",
        "2026-08-02T00:00:00+0000",
        "2026-08-03T00:00:00+0000",
    ], "Chaque source doit récupérer son propre horodatage, apparié par (type, url)"


def test_load_existing_document_absent_ou_illisible_retourne_none(tmp_path):
    """Un document absent ou corrompu est traité comme absent : la seule
    conséquence est un re-tamponnage des horodatages, jamais une perte de
    donnée (le document régénéré est écrit dans tous les cas)."""
    assert load_existing_document(tmp_path / "n-existe-pas.json") is None

    corrompu = tmp_path / "corrompu.json"
    corrompu.write_text("{ceci n'est pas du JSON", encoding="utf-8")
    assert load_existing_document(corrompu) is None

    liste = tmp_path / "liste.json"
    liste.write_text("[1, 2, 3]", encoding="utf-8")
    assert load_existing_document(liste) is None, "Un JSON non-objet n'est pas un document exploitable"

    valide = tmp_path / "valide.json"
    valide.write_text('{"meta": {"genere_le": "2026-08-13T00:00:00+0000"}}', encoding="utf-8")
    assert load_existing_document(valide) == {"meta": {"genere_le": "2026-08-13T00:00:00+0000"}}


# ---------------------------------------------------------------------------
# merge_raw_dirs : sortie compacte (#433)
# ---------------------------------------------------------------------------

def test_merge_raw_dirs_ecrit_compact_a_partir_de_sources_indentees(tmp_path):
    """La fusion des répertoires d'extraction parallèles (jobs AN / Sénat / UE)
    relit indifféremment des sources indentées ou compactes et écrit compact
    (#433) — sans rien perdre de la fusion additive."""
    dir_an = tmp_path / "an"
    dir_ue = tmp_path / "ue"
    dir_an.mkdir()
    dir_ue.mkdir()

    vote_an = {"numero_scrutin": 1, "date": "2026-01-05", "position": "pour"}
    vote_ue = {"numero_scrutin": 2, "date": "2026-02-09", "position": "contre"}
    (dir_an / "alice.json").write_text(
        json.dumps({"slug": "alice", "votes": [vote_an]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (dir_ue / "alice.json").write_text(
        json.dumps({"slug": "alice", "votes": [vote_ue]}, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    out_dir = tmp_path / "out"
    assert merge_raw_dirs([dir_an, dir_ue], out_dir) == 1

    contenu = (out_dir / "alice.json").read_text(encoding="utf-8")
    assert len(contenu.splitlines()) == 1
    assert '": ' not in contenu
    fusionne = json.loads(contenu)
    assert sorted(v["numero_scrutin"] for v in fusionne["votes"]) == [1, 2]


# ---------------------------------------------------------------------------
# #450 — acceptance : la portée de publication décide de la correction de clé
#
# `merge_raw_dirs` est identique avant et après #450 : c'est ce qu'on lui donne
# à fusionner qui change. Les deux tests ci-dessous sont donc écrits en miroir,
# sur le même scénario (2 shards régénérant chacun sa tranche sur la clé `uid`
# corrigée de #440, à partir d'une baseline committée sans `uid`), et ne
# diffèrent QUE par le contenu des répertoires publiés.
# ---------------------------------------------------------------------------

def _amendement(uid=None, numero=None):
    """Même entrée logique selon les deux clés : avec `uid` (corrigée, #440) ou
    sans (périmée). `_amendement_key` les voit comme deux entrées distinctes —
    c'est précisément pourquoi la réinjection double les volumes au lieu de
    remplacer."""
    if uid:
        return {"uid": uid, "numero": numero, "texte_vise": "PLF 2026", "sort": "adopté"}
    return {"numero": numero, "texte_vise": "Projet de loi de finances pour 2026", "sort": None}


def _profil(slug, amendements):
    return {"slug": slug, "chambre": "deputes", "amendements": amendements}


def _ecrire(dossier, slug, profil):
    dossier.mkdir(parents=True, exist_ok=True)
    (dossier / f"{slug}.json").write_text(json.dumps(profil, ensure_ascii=False), encoding="utf-8")


def _scenario_deux_shards(tmp_path):
    """Baseline committée (périmée, sans `uid`) + 2 shards régénérant chacun un
    slug distinct sur la clé corrigée. Renvoie `(baseline, frais_par_shard)`."""
    baseline = {
        "alice": _profil("alice", [_amendement(numero=1), _amendement(numero=2)]),
        "bob": _profil("bob", [_amendement(numero=3)]),
    }
    frais = {
        0: ("alice", _profil("alice", [_amendement("AMANR5L17-1", 1), _amendement("AMANR5L17-2", 2)])),
        1: ("bob", _profil("bob", [_amendement("AMANR5L17-3", 3)])),
    }
    return baseline, frais


def test_publication_du_repertoire_entier_reinjecte_les_donnees_perimees(tmp_path):
    """Reproduction du bug #450, conservée pour que la correction reste lisible
    comme un choix et non comme un détail de configuration.

    Chaque shard publiait tout `raw_data/profiles/` : sa tranche fraîche PLUS la
    baseline que son checkout venait d'y déposer. La fusion additive réunit
    alors les deux versions de chaque amendement au lieu de remplacer, et
    `--no-merge`, correctement appliqué côté extraction, est défait ici.
    Mesuré sur `antoine-armand` au run 32277443716 : 3 335 = 1 289 + 2 046.
    """
    baseline, frais = _scenario_deux_shards(tmp_path)

    dirs = []
    for shard, (slug_frais, profil_frais) in frais.items():
        d = tmp_path / f"artifact-shard-{shard}"
        for slug, profil in baseline.items():          # ← la baseline republiée
            _ecrire(d, slug, profil)
        _ecrire(d, slug_frais, profil_frais)           # ← écrasée par la tranche fraîche
        dirs.append(d)

    out = tmp_path / "out"
    merge_raw_dirs(dirs, out)

    alice = charger_profil_brut(out / "alice.json")
    assert len(alice["amendements"]) == 4, "attendu : 2 périmés + 2 corrigés, l'union"
    assert sum(1 for a in alice["amendements"] if not a.get("uid")) == 2


def test_publication_scopee_laisse_aboutir_la_correction_de_cle(tmp_path):
    """Critère d'acceptation de #450. Mêmes shards, même fusion : seuls les
    répertoires publiés changent. Chaque shard ne publiant que ce qu'il a
    écrit, les jeux de fichiers sont disjoints — il ne reste ni version périmée
    à réunir à la version corrigée, ni nom en collision entre shards."""
    baseline, frais = _scenario_deux_shards(tmp_path)

    dirs = []
    for shard, (slug_frais, profil_frais) in frais.items():
        d = tmp_path / f"staging-shard-{shard}"
        _ecrire(d, slug_frais, profil_frais)           # ← uniquement sa tranche
        dirs.append(d)

    out = tmp_path / "out"
    # La baseline vit dans le checkout de merge-and-pivot, pas dans un artifact.
    for slug, profil in baseline.items():
        _ecrire(out, slug, profil)

    merge_raw_dirs(dirs, out)

    for slug in ("alice", "bob"):
        profil = charger_profil_brut(out / f"{slug}.json")
        assert all(a.get("uid") for a in profil["amendements"]), (
            f"{slug} porte encore des entrées sans uid : la version périmée a été réinjectée."
        )
    assert len(charger_profil_brut(out / "alice.json")["amendements"]) == 2


def test_publication_scopee_preserve_un_profil_qu_aucun_job_n_a_touche(tmp_path):
    """Corollaire : ne plus transporter la baseline ne la perd pas.
    `merge_raw_dirs` boucle sur les fichiers SOURCES et ne réécrit que ceux-là ;
    un slug absent de tout artifact garde sa version committée."""
    out = tmp_path / "out"
    _ecrire(out, "carla", _profil("carla", [_amendement(numero=9)]))

    staging = tmp_path / "staging"
    _ecrire(staging, "alice", _profil("alice", [_amendement("AMANR5L17-1", 1)]))

    merge_raw_dirs([staging], out)

    carla = charger_profil_brut(out / "carla.json")
    assert carla["amendements"] == [_amendement(numero=9)]


def test_merge_raw_dirs_ecrit_la_forme_partitionnee(tmp_path):
    """#580 — c'est ici que la migration se fait d'elle-même : `merge-and-pivot`
    relit une source monolithique (l'ancienne forme, encore committée) et
    réécrit toujours partitionné, sans perdre un amendement."""
    source = tmp_path / "shard"
    _ecrire(source, "alice", {
        "slug": "alice", "chambre": "deputes",
        "amendements": [
            {"uid": "A1", "legislature": "16"},
            {"uid": "A2", "legislature": "17"},
        ],
    })

    out = tmp_path / "out"
    merge_raw_dirs([source], out)

    socle = json.loads((out / "alice.json").read_text(encoding="utf-8"))
    assert est_partitionne(socle)
    assert "amendements" not in socle
    assert sorted(p.name for p in (out / "alice").glob("*.json")) == ["16.json", "17.json"]
    assert [a["uid"] for a in charger_profil_brut(out / "alice.json")["amendements"]] == ["A1", "A2"]


def test_publication_scopee_conserve_l_union_entre_sources_differentes(tmp_path):
    """Ce que la correction ne doit PAS casser : un slug couvert par deux jobs
    (un candidat déclaré présent aussi dans le roster) reste l'union de leurs
    contributions — les deux sont fraîches, la fusion additive joue ici son
    rôle légitime."""
    dir_an = tmp_path / "an"
    dir_roster = tmp_path / "roster"
    _ecrire(dir_an, "alice", _profil("alice", [_amendement("AMANR5L17-1", 1)]))
    _ecrire(dir_roster, "alice", _profil("alice", [_amendement("AMANR5L17-2", 2)]))

    out = tmp_path / "out"
    merge_raw_dirs([dir_an, dir_roster], out)

    alice = charger_profil_brut(out / "alice.json")
    assert sorted(a["uid"] for a in alice["amendements"]) == ["AMANR5L17-1", "AMANR5L17-2"]


# ---------------------------------------------------------------------------
# #465 — une collecte vide n'écrase jamais une collecte non vide
#
# En mode écrasement (`--no-merge`), la fusion additive ne protège plus rien.
# Or une sous-collecte peut échouer sans que le profil écrit n'ait l'air
# anormal : identité introuvable, endpoint en panne, archive indisponible. Le
# profil part alors avec un champ simplement vide, et il écrase le bon.
#
# Vécu le 19/08/2026 sur le run 32302557156 : `jean-luc-melenchon` a perdu
# 18 721 amendements, 1 016 votes et 33 textes portés ; `marine-le-pen` a perdu
# ses 23 textes portés SANS le moindre avertissement dans son profil.
#
# Le motif est celui de #427 sur les gouvernements, déjà énoncé là-bas :
# distinguer « zéro constaté » de « collecte incomplète ». Les profils étaient
# le seul endroit qui ne l'appliquait pas.
# ---------------------------------------------------------------------------

def test_collecte_vide_ne_remplace_pas_des_entrees_existantes():
    ancien = {"votes": [{"numero_scrutin": "1"}], "amendements": [{"uid": "A1"}]}
    nouveau = {"votes": [], "amendements": []}

    profil, preserves = preserver_collectes_non_vides(ancien, nouveau)

    assert len(profil["votes"]) == 1
    assert len(profil["amendements"]) == 1
    assert sorted(preserves) == ["amendements", "votes"]


def test_collecte_non_vide_ecrase_normalement():
    """Le point qui distingue ce garde-fou d'une demi-fusion : une correction de
    clé DOIT pouvoir aboutir. #440 a remplacé 2 018 amendements par 944 — c'est
    une baisse massive, et elle est légitime parce qu'elle n'est pas un vide."""
    ancien = {"amendements": [{"uid": None, "numero": str(i)} for i in range(2018)]}
    nouveau = {"amendements": [{"uid": f"A{i}"} for i in range(944)]}

    profil, preserves = preserver_collectes_non_vides(ancien, nouveau)

    assert len(profil["amendements"]) == 944
    assert preserves == []


def test_champ_par_champ_et_non_tout_ou_rien():
    """`marine-le-pen` avait ses amendements et ses votes intacts, et seuls ses
    textes portés à zéro. Un garde-fou qui raisonnerait sur le profil entier
    l'aurait laissé passer."""
    ancien = {"amendements": [{"uid": "A1"}], "dossiers_legislatifs": [{"id": "D1"}]}
    nouveau = {"amendements": [{"uid": "A2"}, {"uid": "A3"}], "dossiers_legislatifs": []}

    profil, preserves = preserver_collectes_non_vides(ancien, nouveau)

    assert len(profil["amendements"]) == 2, "la collecte réussie doit écraser"
    assert len(profil["dossiers_legislatifs"]) == 1, "la collecte vide ne doit pas écraser"
    assert preserves == ["dossiers_legislatifs"]


def test_garde_fou_ne_depend_pas_d_un_avertissement():
    """Le cas le plus instructif du 19/08 : le profil de `marine-le-pen` ne
    portait AUCUN avertissement. Un garde-fou conditionné à la présence d'un
    warning ne l'aurait pas vu — celui-ci ne regarde que le résultat."""
    ancien = {"dossiers_legislatifs": [{"id": "D1"}], "meta": {"warnings": []}}
    nouveau = {"dossiers_legislatifs": [], "meta": {"warnings": []}}

    profil, preserves = preserver_collectes_non_vides(ancien, nouveau)

    assert len(profil["dossiers_legislatifs"]) == 1
    assert preserves == ["dossiers_legislatifs"]


def test_couvre_les_deux_schemas():
    """`dossiers_legislatifs` côté brut, `textes_portes` côté pivot : le même
    fait porte deux noms selon la couche."""
    for champ in ("dossiers_legislatifs", "textes_portes"):
        profil, preserves = preserver_collectes_non_vides({champ: [{"id": "X"}]}, {champ: []})
        assert preserves == [champ], champ


def test_champ_vide_des_deux_cotes_nest_pas_signale():
    profil, preserves = preserver_collectes_non_vides({"votes": []}, {"votes": []})
    assert preserves == []


def test_profil_neuf_nest_pas_concerne():
    """Un premier passage n'a rien à préserver — et ne doit pas se plaindre."""
    profil, preserves = preserver_collectes_non_vides(None, {"votes": []})
    assert preserves == []
    assert profil["votes"] == []


def test_ancien_champ_de_mauvais_type_est_ignore():
    """Un profil corrompu ne doit pas faire échouer l'écriture du bon."""
    profil, preserves = preserver_collectes_non_vides({"votes": "pas une liste"}, {"votes": []})
    assert preserves == []


def test_le_profil_source_nest_pas_modifie():
    nouveau = {"votes": []}
    preserver_collectes_non_vides({"votes": [{"numero_scrutin": "1"}]}, nouveau)
    assert nouveau["votes"] == [], "la fonction doit être pure vis-à-vis de son entrée"


# ---------------------------------------------------------------------------
# #484 — un bloc structuré sans fond n'écrase jamais un bloc renseigné
# ---------------------------------------------------------------------------
#
# Le run 33262372122 (29/08/2026) est la scène de crime, et elle est
# reproductible sans réseau : trois jobs écrivent le même slug, le dernier est
# `extract-ue-officiel`, qui n'interroge JAMAIS l'Assemblée nationale
# (`--source ue`) et écrit donc le squelette de `build_minimal_profile`. Il
# gagnait la fusion finale parce que son bloc `identite` est truthy.

_IDENTITE_AN = {
    "nom_complet": "Jean-Luc Mélenchon",
    "groupe_sigle": "FI",
    "groupe_nom": "La France insoumise",
    "profession": "Professeur",
    "date_naissance": "1951-08-19",
    "num_circo": "4",
    "nb_mandats": 1,
    "url_an_ou_senat": "https://www2.assemblee-nationale.fr/deputes/fiche/OMC_PA2150",
}

#: Ce que `build_minimal_profile` produit : deux champs, tous deux recopiés de
#: `raw_data/candidats.json`, et rien d'autre.
_IDENTITE_SQUELETTE = {
    "nom_complet": "Jean-Luc Mélenchon",
    "groupe_sigle": None,
    "groupe_nom": "La France Insoumise (LFI)",
    "profession": None,
    "date_naissance": None,
    "num_circo": None,
    "nb_mandats": None,
    "url_an_ou_senat": None,
}


def test_le_squelette_du_profil_minimal_nefface_pas_une_identite_collectee():
    merged = merge_raw_profile(
        {"slug": "jean-luc-melenchon", "identite": dict(_IDENTITE_AN)},
        {"slug": "jean-luc-melenchon", "identite": dict(_IDENTITE_SQUELETTE)},
    )
    assert merged["identite"] == _IDENTITE_AN


def test_la_meme_regle_vaut_sur_le_pivot():
    merged = merge_pivot_profile(
        {"id": "jean-luc-melenchon", "identite": dict(_IDENTITE_AN)},
        {"id": "jean-luc-melenchon", "identite": dict(_IDENTITE_SQUELETTE)},
    )
    assert merged["identite"] == _IDENTITE_AN


def test_une_valeur_corrigee_gagne_champ_par_champ_sans_emporter_les_autres():
    """La règle de #465 n'est pas devenue « la nouvelle valeur ne gagne
    jamais » : une valeur réellement collectée gagne.

    Depuis #601, elle gagne **sur son champ** et sur lui seul : la fusion
    compose au lieu de choisir un bloc entier. La correction aboutit donc — la
    profession publiée est la neuve — sans que les cinq champs que le nouvel
    écrivain ne renseigne pas régressent vers `null` (§2.5). Avant #601, ce même
    scénario publiait le bloc neuf en entier, et les cinq disparaissaient.
    """
    corrigee = dict(_IDENTITE_SQUELETTE, profession="Professeur certifié")
    merged = merge_raw_profile(
        {"identite": dict(_IDENTITE_AN)}, {"identite": corrigee}
    )
    assert merged["identite"]["profession"] == "Professeur certifié"
    assert merged["identite"]["date_naissance"] == _IDENTITE_AN["date_naissance"]
    assert merged["identite"]["num_circo"] == _IDENTITE_AN["num_circo"]
    assert merged["identite"]["url_an_ou_senat"] == _IDENTITE_AN["url_an_ou_senat"]


def test_un_squelette_nefface_pas_un_squelette_et_ne_casse_rien():
    """Bardella : aucune identité AN d'aucun côté. Le bloc neuf passe."""
    merged = merge_raw_profile(
        {"identite": dict(_IDENTITE_SQUELETTE)},
        {"identite": dict(_IDENTITE_SQUELETTE, nom_complet="Jordan Bardella")},
    )
    assert merged["identite"]["nom_complet"] == "Jordan Bardella"


def test_une_identite_absente_ne_regresse_pas_vers_null():
    """Le comportement historique de `_prefer_non_empty` est conservé."""
    merged = merge_raw_profile({"identite": dict(_IDENTITE_AN)}, {"identite": None})
    assert merged["identite"] == _IDENTITE_AN


def test_les_champs_sans_source_du_squelette_sont_ceux_que_le_profil_minimal_remplit():
    """Le garde-fou de la table : si `build_minimal_profile` apprend à remplir
    un champ de plus sans source, `BLOCS_PROTEGES_DU_VIDE` doit le savoir —
    sinon le squelette redevient « renseigné » et le défaut revient."""
    from generate_all_profiles import build_minimal_profile
    from merge_profile import BLOCS_PROTEGES_DU_VIDE, bloc_sans_fond

    minimal = build_minimal_profile(
        "Jean-Luc Mélenchon", "jean-luc-melenchon", {"parti": "La France Insoumise (LFI)"}
    )
    assert bloc_sans_fond(minimal["identite"], BLOCS_PROTEGES_DU_VIDE["identite"]), (
        "le profil minimal remplit un champ que BLOCS_PROTEGES_DU_VIDE ne "
        "déclare pas comme rempli sans source"
    )


def test_le_mode_ecrasement_protege_aussi_les_blocs():
    """#465 ne couvrait que des listes : `identite` y passait au travers."""
    profil, preserves = preserver_collectes_non_vides(
        {"identite": dict(_IDENTITE_AN)}, {"identite": dict(_IDENTITE_SQUELETTE)}
    )
    assert preserves == ["identite"]
    assert profil["identite"] == _IDENTITE_AN

    profil, preserves = preserver_collectes_non_vides(
        {"identite": dict(_IDENTITE_AN)}, {"identite": None}
    )
    assert preserves == ["identite"]


def test_aucun_mandat_francais_connu_est_retire_quand_lidentite_le_dement():
    from candidate_profile import WARNING_AUCUN_MANDAT_FR

    merged = merge_raw_profile(
        {"identite": dict(_IDENTITE_AN), "meta": {"warnings": []}},
        {
            "identite": dict(_IDENTITE_SQUELETTE),
            "meta": {"warnings": [f"{WARNING_AUCUN_MANDAT_FR} (slug absent…)"]},
        },
    )
    assert merged["meta"]["warnings"] == []


def test_aucun_mandat_francais_connu_survit_a_un_profil_purement_europeen():
    """`jordan-bardella` : 22 mandats européens, et l'avertissement reste VRAI.
    Le critère de purge est l'identité AN, jamais `mandats`."""
    from candidate_profile import WARNING_AUCUN_MANDAT_FR

    w = f"{WARNING_AUCUN_MANDAT_FR} (slug absent…)"
    merged = merge_raw_profile(
        {"identite": dict(_IDENTITE_SQUELETTE), "mandats": [], "meta": {"warnings": [w]}},
        {
            "identite": dict(_IDENTITE_SQUELETTE),
            "mandats": [{"categorie": "mandat_electif", "label": "PE", "debut": "2019-07-02"}],
            "meta": {"warnings": [w]},
        },
    )
    assert merged["meta"]["warnings"] == [w]


def test_un_horodatage_de_synchro_ne_recule_jamais():
    """Le champ qui a fait passer un correctif de fusion pour une panne CI.

    L'artifact UE, fusionné APRÈS l'artifact AN, portait le 19/08 recopié du
    profil committé ; il gagnait sur le 29/08 que le job AN venait d'écrire.
    """
    merged = merge_raw_profile(
        {"meta": {"synchro_sources": {"assemblee_nationale": "2026-08-29T16:22:05+0000"}}},
        {"meta": {"synchro_sources": {"assemblee_nationale": "2026-08-19T18:43:46+0000"}}},
    )
    assert merged["meta"]["synchro_sources"]["assemblee_nationale"] == "2026-08-29T16:22:05+0000"

    # et dans l'autre sens : l'ordre de fusion ne doit rien changer
    merged = merge_raw_profile(
        {"meta": {"synchro_sources": {"assemblee_nationale": "2026-08-19T18:43:46+0000"}}},
        {"meta": {"synchro_sources": {"assemblee_nationale": "2026-08-29T16:22:05+0000"}}},
    )
    assert merged["meta"]["synchro_sources"]["assemblee_nationale"] == "2026-08-29T16:22:05+0000"


def test_un_horodatage_de_synchro_illisible_ne_fait_pas_lever_la_fusion():
    merged = merge_raw_profile(
        {"meta": {"synchro_sources": {"an": "pas une date"}}},
        {"meta": {"synchro_sources": {"an": "2026-08-29T16:22:05+0000"}}},
    )
    assert merged["meta"]["synchro_sources"]["an"] == "2026-08-29T16:22:05+0000"
    merged = merge_raw_profile(
        {"meta": {"synchro_sources": {"an": "2026-08-29T16:22:05+0000"}}},
        {"meta": {"synchro_sources": {"an": None}}},
    )
    assert merged["meta"]["synchro_sources"]["an"] == "2026-08-29T16:22:05+0000"


def test_la_scene_de_crime_du_run_33262372122_ne_se_rejoue_plus():
    """Reproduction bout en bout de l'ordre `--dirs _artifacts/an _artifacts/ue`.

    Chaque job fusionne d'abord avec le profil committé de son checkout, puis
    `merge_raw_dirs` fusionne les artifacts dans l'ordre des répertoires.
    """
    committe = {
        "slug": "jean-luc-melenchon",
        "chambre": "senateurs",
        "identite": dict(_IDENTITE_SQUELETTE),
        "mandats": [],
        "meta": {
            "synchro_sources": {"assemblee_nationale": "2026-08-19T18:43:46+0000"},
            "warnings": ["aucun mandat français connu (slug absent…)"],
        },
    }
    collecte_an = {
        "slug": "jean-luc-melenchon",
        "chambre": "deputes",
        "identite": dict(_IDENTITE_AN),
        "mandats": [
            {"categorie": "mandat_electif", "type": "mandat",
             "label": "Mandat parlementaire (La France insoumise)",
             "debut": "2017-06-18", "chambre": "deputes"}
        ],
        "meta": {
            "synchro_sources": {"assemblee_nationale": "2026-08-29T16:22:05+0000"},
            "warnings": [],
        },
    }
    minimal_ue = {
        "slug": "jean-luc-melenchon",
        "chambre": None,
        "identite": dict(_IDENTITE_SQUELETTE),
        "mandats": [],
        "meta": {"warnings": ["aucun mandat français connu (slug absent…)"]},
    }

    artefact_an = merge_raw_profile(json.loads(json.dumps(committe)), collecte_an)
    artefact_ue = merge_raw_profile(json.loads(json.dumps(committe)), minimal_ue)
    final = merge_raw_profile(merge_raw_profile(None, artefact_an), artefact_ue)

    assert final["identite"]["profession"] == "Professeur"
    assert final["meta"]["synchro_sources"]["assemblee_nationale"] == "2026-08-29T16:22:05+0000"
    assert final["meta"]["warnings"] == []
    assert len(final["mandats"]) == 1


# ---------------------------------------------------------------------------
# #997 — un dossier déjà collecté apprend de la régénération
# ---------------------------------------------------------------------------
#
# `dossiers_legislatifs[]` se fusionnait en ADDITIF PUR : l'entrée ancienne
# était conservée inchangée et la neuve de même clé ignorée. Le correctif de
# stade de #997 a traversé QUATRE runs sans atteindre le corpus pour cette
# seule raison — le pivot, lui, faisait bien gagner la neuve, mais il
# normalise depuis le brut, donc il recevait la vieille valeur et n'avait rien
# à écraser. Les deux étages étaient d'accord sur une donnée périmée.
#
# Mesuré le 18/09/2026, collecte réelle contre brut publié d'Édouard Philippe :
# 290 dossiers de part et d'autre, exactement les mêmes clés, AUCUN champ
# perdu, et 118 transitions `examine_commission` → `depose`.
#
# Rien ne verrouillait l'ancienne politique : toute la suite passait avant ce
# changement comme après. Ces deux cas sont la garde qui manquait.


def _dossier_brut(id_: str, **champs):
    base = {
        "id": id_, "titre": f"Dossier {id_}", "role": "auteur",
        "type_rapport": None, "stade_procedural": "examine_commission",
        "sort": "navette_en_cours", "date_min": "2024-01-01",
        "date_max": "2024-06-01", "legislature": "17",
        "source_url": f"https://www.assemblee-nationale.fr/dyn/17/dossiers/{id_}",
        "nature_texte": "projet_de_loi",
    }
    base.update(champs)
    return base


def test_un_stade_corrige_atteint_le_profil_brut():
    """Le cas de #997 : le dossier est déjà là, seul son stade a changé."""
    old = {"slug": "x", "votes": [], "interventions": [], "mandats": [],
           "dossiers_legislatifs": [_dossier_brut("DLR5L17N1")]}
    new = {"slug": "x", "votes": [], "interventions": [], "mandats": [],
           "dossiers_legislatifs": [_dossier_brut("DLR5L17N1", stade_procedural="depose",
                                                  sort="navette_en_cours")]}

    merged = merge_raw_profile(old, new)

    assert len(merged["dossiers_legislatifs"]) == 1
    assert merged["dossiers_legislatifs"][0]["stade_procedural"] == "depose"


def test_un_dossier_que_la_collecte_ne_rend_plus_reste_publie():
    """L'autre moitié du contrat : la neuve gagne, mais elle ne retire rien.

    Un texte porté dont l'AN ne sert plus le dossier garde ce qu'il avait —
    une absence n'est pas une correction (§2 règle 5).
    """
    old = {"slug": "x", "votes": [], "interventions": [], "mandats": [],
           "dossiers_legislatifs": [_dossier_brut("DLR5L17N1"), _dossier_brut("DLR5L17N2")]}
    new = {"slug": "x", "votes": [], "interventions": [], "mandats": [],
           "dossiers_legislatifs": [_dossier_brut("DLR5L17N1", stade_procedural="depose")]}

    merged = merge_raw_profile(old, new)

    par_id = {d["id"]: d for d in merged["dossiers_legislatifs"]}
    assert set(par_id) == {"DLR5L17N1", "DLR5L17N2"}
    assert par_id["DLR5L17N1"]["stade_procedural"] == "depose"
    assert par_id["DLR5L17N2"]["stade_procedural"] == "examine_commission"


def test_une_collecte_vide_ne_remplace_rien():
    """`CHAMPS_PROTEGES_DU_VIDE` en amont : rien collecté, rien remplacé."""
    old = {"slug": "x", "votes": [], "interventions": [], "mandats": [],
           "dossiers_legislatifs": [_dossier_brut("DLR5L17N1")]}
    new = {"slug": "x", "votes": [], "interventions": [], "mandats": [],
           "dossiers_legislatifs": []}

    merged = merge_raw_profile(old, new)

    assert [d["id"] for d in merged["dossiers_legislatifs"]] == ["DLR5L17N1"]
    assert merged["dossiers_legislatifs"][0]["stade_procedural"] == "examine_commission"
