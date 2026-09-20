import sys
from pathlib import Path

# Les modules testés vivent dans src/, à côté du dossier tests/.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from normalize_profil import normalize_profil
from schema_pivot import SCHEMA_VERSION, validate_profil


# ---------------------------------------------------------------------------
# Fixture : profil brut minimal (format candidate_profile.py)
#
# Les URLs `www.nosdeputes.fr` qu'elle porte encore sont VOULUES : ce sont
# celles des interventions et des dossiers déjà collectés, que la fusion
# additive conserve dans `raw_data/profiles/` et que l'adaptateur doit
# continuer de savoir lire après #529 (AGENTS.md §2 règle 5). De même pour
# `synchro_sources.nosdeputes`. Ce que la collecte ÉCRIT aujourd'hui est
# testé par `test_pivot_sources_portent_toujours_la_provenance` et par
# `tests/test_candidate_profile.py`.
# ---------------------------------------------------------------------------

def _raw_depute(extra: dict = None) -> dict:
    """Retourne un profil brut minimal pour les tests."""
    base = {
        "slug": "jean-dupont",
        "chambre": "deputes",
        "source": "https://www.nosdeputes.fr/jean-dupont",
        "identite": {
            "nom_complet": "Jean Dupont",
            "groupe_sigle": "RE",
            "groupe_nom": "Renaissance",
            "profession": "Avocat",
            "date_naissance": "1970-01-01",
            "num_circo": 3,
            "nb_mandats": 2,
            "url_an_ou_senat": "https://www.assemblee-nationale.fr/dyn/deputes/PA123456",
        },
        "mandats": [
            {
                "categorie": "mandat_electif",
                "type": "mandat",
                "label": "Mandat parlementaire (Renaissance)",
                "debut": "2022-06-20",
                "fin": None,
                "actif": True,
            },
            {
                "categorie": "commission",
                "type": "membre",
                "label": "Commission des lois",
                "debut": "2022-07-01",
                "fin": None,
                "actif": True,
            },
        ],
        "votes": [
            {
                "date": "2023-11-10",
                "titre": "Projet de loi de finances 2024",
                "position": "pour",
                "numero_scrutin": 1234,
                "sort": "adopté",
            },
            {
                "date": "2022-10-05",
                "titre": "Motion de censure",
                "position": "contre",
                "numero_scrutin": 567,
                "sort": "rejeté",
            },
        ],
        "votes_source": "open data Assemblée nationale (data.assemblee-nationale.fr, législature 17)",
        "dossiers_legislatifs": [
            {
                "legislature": "17",
                "id": "2023-PLF",
                "titre": "Projet de loi de finances 2024",
                "date_min": "2023-09-01",
                "date_max": "2023-12-20",
                "sort": "adopte",
                "url_source": "https://www.nosdeputes.fr/17/dossier/2023-PLF",
                "url_institution": "https://www.assemblee-nationale.fr/dyn/17/dossiers/2023-PLF",
            }
        ],
        "interventions": [
            {
                "type": "Intervention",
                "id": "42",
                "url": "https://www.nosdeputes.fr/seance/abc",
                "date": "2023-03-15",
                "created_at": "2023-03-15T14:30:00",
                "type_detail": "loi",
                "texte": "Je soutiens ce projet de loi.",
                "url_detail": "https://www.nosdeputes.fr/seance/abc#inter_42",
                "classification": {"mode": "prise_de_parole", "reason": "..."},
                "sujet": "Budget 2024",
                "mots_cles": ["budget", "fiscalité"],
                "fonction": "Rapporteur",
                "nb_mots": 48,
                "format": "prise_de_parole_developpee",
            }
        ],
        "meta": {
            "genere_le": "2026-07-29T10:00:00+0000",
            "licence_donnees": "ODbL (Regards Citoyens, ...)",
            "synchro_sources": {
                "nosdeputes": "2026-07-29T10:00:00+0000",
                "assemblee_nationale": "2026-07-29T10:00:00+0000",
            },
            "warnings": [],
        },
    }
    if extra:
        base.update(extra)
    return base


def _raw_senateur() -> dict:
    """Profil brut NosSénateurs minimal."""
    p = _raw_depute()
    p["chambre"] = "senateurs"
    p["source"] = "https://archive.nossenateurs.fr/marie-martin"
    p["slug"] = "marie-martin"
    p["identite"]["nom_complet"] = "Marie Martin"
    return p


# ---------------------------------------------------------------------------
# Tests de structure de base
# ---------------------------------------------------------------------------

def test_pivot_valide_selon_schema():
    pivot = normalize_profil(_raw_depute())
    errors = validate_profil(pivot)
    assert errors == [], f"Erreurs de schéma inattendues : {errors}"


def test_pivot_schema_version():
    pivot = normalize_profil(_raw_depute())
    assert pivot["schema_version"] == SCHEMA_VERSION


def test_pivot_id_est_le_slug_cote_deputes():
    # Sans préfixe de provenance depuis #487 : le préfixe dérivait de la
    # chambre qui avait répondu, donc changeait de valeur sur une carrière
    # inchangée. Garde-fou de fond : tests/test_id_pivot_sans_prefixe.py.
    pivot = normalize_profil(_raw_depute())
    assert pivot["id"] == "jean-dupont"


def test_pivot_id_est_le_slug_cote_senateurs():
    pivot = normalize_profil(_raw_senateur())
    assert pivot["id"] == "marie-martin"


def test_pivot_sources_portent_toujours_la_provenance():
    """`sources[].type` décrit la provenance d'UNE source (#487) — ce qui est
    vrai et stable, contrairement au préfixe d'`id` qu'il a remplacé.

    `_SOURCE_TYPE_MAP` la faisait dépendre de la chambre
    (`deputes` → `nosdeputes`, `senateurs` → `nossenateurs`). Depuis #529 il
    n'y a plus qu'une provenance possible : la chambre du profil brut ne décide
    plus rien ici."""
    assert normalize_profil(_raw_depute())["sources"][0]["type"] == "assemblee_nationale"
    assert normalize_profil(_raw_senateur())["sources"][0]["type"] == "assemblee_nationale"


def test_pivot_nom_depuis_identite():
    pivot = normalize_profil(_raw_depute())
    assert pivot["nom"] == "Jean Dupont"


def test_pivot_chambre_deputes_mappe_an():
    pivot = normalize_profil(_raw_depute())
    assert pivot["chambre"] == "AN"


def test_pivot_chambre_senateurs_mappe_senat():
    pivot = normalize_profil(_raw_senateur())
    assert pivot["chambre"] == "Senat"


def test_pivot_groupe_depuis_identite():
    pivot = normalize_profil(_raw_depute())
    assert pivot["groupe"] == "Renaissance"


def test_pivot_parti_optionnel():
    pivot = normalize_profil(_raw_depute(), parti="Renaissance")
    assert pivot["parti"] == "Renaissance"


def test_pivot_parti_absent_par_defaut():
    pivot = normalize_profil(_raw_depute())
    assert pivot["parti"] is None


def test_pivot_provenance_defaut_candidat_declare():
    pivot = normalize_profil(_raw_depute())
    assert pivot["meta"]["provenance"] == "candidat_declare"


def test_pivot_provenance_roster_groupe_propagee():
    pivot = normalize_profil(_raw_depute(), provenance="roster_groupe")
    assert pivot["meta"]["provenance"] == "roster_groupe"


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------

def test_pivot_source_du_profil_pointe_la_fiche_de_l_elu():
    """La PREMIÈRE source est celle du profil : son `url` est la fiche de
    l'élu, reprise telle quelle du brut. C'était `www.nosdeputes.fr/<slug>`,
    c'est la fiche AN depuis #529 — mais l'adaptateur ne fabrique pas cette
    URL, il la relaie, donc ce test relaie le brut."""
    raw = _raw_depute()
    raw["source"] = "https://www2.assemblee-nationale.fr/deputes/fiche/OMC_PA123456"
    pivot = normalize_profil(raw)
    assert pivot["sources"][0]["url"] == raw["source"]


def test_pivot_source_par_defaut_ne_pretend_pas_identifier_l_elu():
    """Sans `source` dans le brut, le repli nommait la personne
    (`www.nosdeputes.fr/<slug>`) alors qu'on ne l'avait pas résolue. Il nomme
    désormais le JEU DE DONNÉES, ce qui est exactement ce qu'on sait (#529)."""
    raw = _raw_depute()
    raw.pop("source")
    pivot = normalize_profil(raw)
    assert pivot["sources"][0]["url"] == "https://data.assemblee-nationale.fr/"


def test_pivot_sources_contient_assemblee_nationale_quand_votes_officiels():
    pivot = normalize_profil(_raw_depute())
    types = [s["type"] for s in pivot["sources"]]
    assert "assemblee_nationale" in types


def test_pivot_sources_une_seule_entree_si_votes_source_absent():
    """Sans votes officiels, il ne reste que la source du profil.

    Le test posait `"assemblee_nationale" not in types` : la seconde entrée
    était la seule à porter ce type, la première valant `nosdeputes`. Les deux
    portent désormais le même type — ce qui est vérifiable est donc leur
    NOMBRE, pas leur type."""
    raw = _raw_depute()
    raw["votes_source"] = None
    pivot = normalize_profil(raw)
    assert len(pivot["sources"]) == 1
    assert pivot["sources"][0]["url"] != "https://data.assemblee-nationale.fr/"


def test_pivot_source_synchro_le_propagee():
    pivot = normalize_profil(_raw_depute())
    assert pivot["sources"][0]["synchro_le"] == "2026-07-29T10:00:00+0000"


def test_pivot_source_synchro_le_relit_les_profils_collectes_avant_529():
    """Le repli de lecture, et pourquoi il existe.

    Les profils bruts déjà collectés ne portent que
    `synchro_sources.nosdeputes` ; la fusion additive les garde indéfiniment.
    Sauter cette clé ferait reculer `sources[].synchro_le` de tout profil non
    recollecté vers son `genere_le` — un horodatage de fraîcheur qui régresse
    sans qu'aucune donnée n'ait bougé."""
    raw = _raw_depute()
    raw["meta"]["synchro_sources"] = {"nosdeputes": "2026-07-29T10:00:00+0000"}
    pivot = normalize_profil(raw)
    assert pivot["sources"][0]["synchro_le"] == "2026-07-29T10:00:00+0000"


# ---------------------------------------------------------------------------
# Mandats
# ---------------------------------------------------------------------------

def test_pivot_mandats_count():
    pivot = normalize_profil(_raw_depute())
    assert len(pivot["mandats"]) == 2


def test_pivot_mandat_electif_champs():
    pivot = normalize_profil(_raw_depute())
    m = next(m for m in pivot["mandats"] if m["categorie"] == "mandat_electif")
    assert m["label"] == "Mandat parlementaire (Renaissance)"
    assert m["fonction"] == "mandat"
    assert m["debut"] == "2022-06-20"
    assert m["fin"] is None
    assert m["actif"] is True


def test_pivot_commission_champs():
    pivot = normalize_profil(_raw_depute())
    m = next(m for m in pivot["mandats"] if m["categorie"] == "commission")
    assert m["label"] == "Commission des lois"
    assert m["fonction"] == "membre"


# ---------------------------------------------------------------------------
# Votes
# ---------------------------------------------------------------------------

def test_pivot_votes_count():
    pivot = normalize_profil(_raw_depute())
    assert len(pivot["votes"]) == 2


def test_pivot_vote_ne_garde_que_le_mapping():
    """#432 : un scrutin est identique pour tous ses votants. Son méta vit une
    seule fois dans l'index partagé ; le profil ne garde que ce qui est propre
    au membre — mesuré, 179,8 Mo de votes deviennent 18,0 Mo de mapping."""
    v = normalize_profil(_raw_depute())["votes"][0]

    assert v["position"] == "pour"
    assert v["scrutin_id"] == "an:16:1234"   # date 2023-11-10 → XVIe législature
    assert set(v) == {"scrutin_id", "position"}


def test_pivot_vote_identifiant_porte_la_legislature_du_vote():
    """Le numéro de scrutin repart à 1 à chaque législature : un identifiant qui
    ne porterait pas la législature confondrait deux scrutins sans rapport."""
    raw = _raw_depute()
    raw["votes"][0]["legislature"] = "17"
    assert normalize_profil(raw)["votes"][0]["scrutin_id"] == "an:17:1234"


def test_pivot_vote_numero_non_str_est_converti():
    raw = _raw_depute()
    raw["votes"][0]["numero_scrutin"] = 1234
    assert normalize_profil(raw)["votes"][0]["scrutin_id"].endswith(":1234")


def test_pivot_vote_index_prime_sur_la_derivation_locale():
    """L'index porte la résolution de corpus (jointure sur jumeau étiqueté), la
    seule qui voie au-delà du profil : elle l'emporte sur le calendrier."""
    from scrutins_index import ScrutinsIndex

    raw = _raw_depute()
    raw["votes"][0]["legislature"] = None
    index = ScrutinsIndex({"an:16:1234": {
        "id": "an:16:1234", "numero_scrutin": "1234", "date": "2023-11-10",
    }})
    assert normalize_profil(raw, scrutins_index=index)["votes"][0]["scrutin_id"] == "an:16:1234"


def test_pivot_vote_groupe_au_moment_du_vote_omis_quand_vide():
    """Seule exception à « missing = null », et elle est chiffrée : le champ
    n'est jamais peuplé (0 sur 398 085) et l'écrire coûtait 12,1 Mo de null,
    soit 40 % du mapping."""
    assert "groupe_au_moment_du_vote" not in normalize_profil(_raw_depute())["votes"][0]


def test_pivot_vote_groupe_au_moment_du_vote_conserve_quand_renseigne():
    raw = _raw_depute()
    raw["votes"][0]["groupe_au_moment_du_vote"] = "SOC"
    assert normalize_profil(raw)["votes"][0]["groupe_au_moment_du_vote"] == "SOC"


def test_pivot_vote_non_resolu_garde_son_enregistrement_complet():
    """Ni supprimé, ni doté d'une clé inventée : une donnée qu'on ne sait pas
    normaliser reste une donnée (AGENTS.md §2.5). La date choisie tombe dans
    l'entre-deux dissolution/ouverture de 2024, qui n'appartient à aucune
    législature."""
    raw = _raw_depute()
    raw["votes"][0].update({"legislature": None, "date": "2024-07-01"})

    v = normalize_profil(raw)["votes"][0]

    assert v["scrutin_id"] is None
    assert v["scrutin_non_resolu"]["numero_scrutin"] == "1234"
    assert v["scrutin_non_resolu"]["texte"] == "Projet de loi de finances 2024"
    assert v["scrutin_non_resolu"]["date"] == "2024-07-01"
    assert v["position"] == "pour"


def test_pivot_vote_49_3_et_motion_censure_migrent_vers_l_index():
    """`type_scrutin`, `type_vote` et `texte_lie_id` sont des champs du SCRUTIN :
    ils ne sont plus recopiés sur chacun de ses votants. Leur validation a suivi
    (`schema_pivot.validate_scrutins_index`)."""
    raw = _raw_depute()
    raw["votes"][0].update({
        "type_scrutin": "solennel",
        "type_vote": "motion_censure",
        "texte_lie_id": "texte-49-3-1",
    })
    vote = normalize_profil(raw)["votes"][0]

    assert "type_scrutin" not in vote
    assert "type_vote" not in vote
    assert "texte_lie_id" not in vote


# ---------------------------------------------------------------------------
# Textes portés (depuis dossiers_legislatifs)
# ---------------------------------------------------------------------------

def test_pivot_textes_portes_count():
    pivot = normalize_profil(_raw_depute())
    assert len(pivot["textes_portes"]) == 1


def test_pivot_texte_porte_champs():
    pivot = normalize_profil(_raw_depute())
    t = pivot["textes_portes"][0]
    assert t["titre"] == "Projet de loi de finances 2024"
    assert t["role"] is None
    assert t["legislature"] == "17"
    assert t["date_min"] == "2023-09-01"
    assert t["date_max"] == "2023-12-20"


def test_pivot_texte_porte_preserve_role_et_stade_factuels():
    raw = _raw_depute()
    raw["dossiers_legislatifs"][0].update({
        "role": "auteur",
        "type_rapport": None,
        "stade_procedural": "discute_seance",
    })
    texte = normalize_profil(raw)["textes_portes"][0]
    assert texte["role"] == "auteur"
    assert texte["stade_procedural"] == "discute_seance"


def test_pivot_texte_porte_source_url_prefere_url_source():
    pivot = normalize_profil(_raw_depute())
    t = pivot["textes_portes"][0]
    assert t["source_url"] == "https://www.nosdeputes.fr/17/dossier/2023-PLF"


# ---------------------------------------------------------------------------
# Interventions
# ---------------------------------------------------------------------------

def test_pivot_interventions_count():
    pivot = normalize_profil(_raw_depute())
    assert len(pivot["interventions"]) == 1


def test_pivot_intervention_champs():
    pivot = normalize_profil(_raw_depute())
    i = pivot["interventions"][0]
    assert i["date"] == "2023-03-15"
    assert i["type_detail"] == "loi"
    assert i["sujet"] == "Budget 2024"
    assert i["fonction"] == "Rapporteur"
    assert i["format"] == "prise_de_parole_developpee"
    assert "budget" in i["mots_cles"]
    assert i["source_url"] == "https://www.nosdeputes.fr/seance/abc#inter_42"


# ---------------------------------------------------------------------------
# Amendements
# ---------------------------------------------------------------------------

def test_pivot_amendements_vides_si_absent():
    pivot = normalize_profil(_raw_depute())
    assert pivot["amendements"] == []


def test_pivot_amendement_est_un_mapping_seul():
    """#431 : le profil ne garde que `{amendement_id, role_signataire}`.

    Le méta de l'amendement — identique pour tous ses signataires — vit dans
    l'index partagé. Le voir réapparaître ici, c'est la duplication qui pesait
    1 342,4 Mo.
    """
    raw = _raw_depute()
    raw["amendements"] = [
        {
            "uid": "AMANR5L17PO59047BTC1376P0D1N000012",
            "texte_vise": "PIONANR5L17B0904",
            "sort": "adopté",
            "base_juridique_irrecevabilite": None,
            "role_signataire": "auteur_principal",
            "co_signataires": ["an:PA842001"],
            "type_deposant": "depute",
            "date": "2025-02-17",
            "numero": "AS1",
            "source_url": None,
        }
    ]
    pivot = normalize_profil(raw)
    assert len(pivot["amendements"]) == 1
    a = pivot["amendements"][0]
    assert a == {
        "amendement_id": "an:AMANR5L17PO59047BTC1376P0D1N000012",
        "role_signataire": "auteur_principal",
    }


def test_pivot_amendement_role_signataire_reste_dans_le_mapping():
    """`role_signataire` est le SEUL champ propre au membre : il reste."""
    raw = _raw_depute()
    raw["amendements"] = [
        {
            "uid": "AMANR5L17PO59047BTC1376P0D1N000012",
            "texte_vise": "PIONANR5L17B0904",
            "sort": "adopté",
            "base_juridique_irrecevabilite": None,
            "role_signataire": "cosignataire",
            "premier_signataire": "an:PA111111",
            "co_signataires": ["an:PA842001"],
            "type_deposant": "depute",
            "date": "2025-02-17",
            "numero": "AS1",
            "source_url": None,
        }
    ]
    pivot = normalize_profil(raw)
    a = pivot["amendements"][0]
    assert a["role_signataire"] == "cosignataire"
    assert a["amendement_id"] == "an:AMANR5L17PO59047BTC1376P0D1N000012"
    assert "premier_signataire" not in a
    assert "co_signataires" not in a


def test_pivot_amendement_sans_uid_garde_son_enregistrement():
    """Sans `uid`, pas de clé — et pas de clé inventée (AGENTS.md §2.5).

    L'enregistrement complet est conservé sous `amendement_non_resolu` : ni
    supprimé, ni deviné. Le `premier_signataire` d'un⋅e auteur⋅rice y garde son
    identifiant pivot, comportement d'avant #431 préservé pour ces seules
    entrées.
    """
    raw = _raw_depute()
    raw["amendements"] = [
        {
            "texte_vise": "PIONANR5L17B0904",
            "sort": "adopté",
            "base_juridique_irrecevabilite": None,
            "co_signataires": ["an:PA842001"],
            "type_deposant": "depute",
            "date": "2025-02-17",
            "numero": "AS1",
            "source_url": None,
        }
    ]
    pivot = normalize_profil(raw)
    a = pivot["amendements"][0]
    assert a["amendement_id"] is None
    non_resolu = a["amendement_non_resolu"]
    assert non_resolu["texte_vise"] == "PIONANR5L17B0904"
    assert non_resolu["sort"] == "adopté"
    assert non_resolu["premier_signataire"] == pivot["id"]
    assert non_resolu["co_signataires"] == ["an:PA842001"]
    assert non_resolu["numero"] == "AS1"


# ---------------------------------------------------------------------------
# Tags thématiques
# ---------------------------------------------------------------------------

def test_pivot_tags_thematiques_agrege_mots_cles():
    pivot = normalize_profil(_raw_depute())
    assert "budget" in pivot["tags_thematiques"]
    assert "fiscalité" in pivot["tags_thematiques"]


def test_pivot_tags_thematiques_minuscules():
    raw = _raw_depute()
    raw["interventions"][0]["mots_cles"] = ["Budget", "FISCALITÉ"]
    pivot = normalize_profil(raw)
    assert "budget" in pivot["tags_thematiques"]
    assert "fiscalité" in pivot["tags_thematiques"]


def test_pivot_tags_thematiques_tries():
    pivot = normalize_profil(_raw_depute())
    assert pivot["tags_thematiques"] == sorted(pivot["tags_thematiques"])


def test_pivot_tags_thematiques_vide_si_pas_interventions():
    raw = _raw_depute()
    raw["interventions"] = []
    pivot = normalize_profil(raw)
    assert pivot["tags_thematiques"] == []


# ---------------------------------------------------------------------------
# Métadonnées
# ---------------------------------------------------------------------------

def test_pivot_meta_licence_propagee():
    pivot = normalize_profil(_raw_depute())
    assert "ODbL" in pivot["meta"]["licence_donnees"]


def test_pivot_meta_warnings_propagees():
    raw = _raw_depute()
    raw["meta"]["warnings"] = ["test warning"]
    pivot = normalize_profil(raw)
    assert "test warning" in pivot["meta"]["warnings"]


def test_pivot_meta_avertissement_si_synchro_an_nulle():
    """La clé surveillée est `assemblee_nationale` depuis #529.

    L'ancienne, `nosdeputes`, était `None` sur presque tout le corpus depuis
    #369 — un député résolu dans le référentiel AN ne déclenchait aucun appel
    NosDéputés, donc aucune synchro à horodater : le warning décrivait le
    fonctionnement normal. `assemblee_nationale` est renseignée dès que
    l'identité est trouvée : à `None`, elle signale une vraie absence."""
    raw = _raw_depute()
    raw["meta"]["synchro_sources"]["assemblee_nationale"] = None
    pivot = normalize_profil(raw)
    assert any("synchro_sources" in w for w in pivot["meta"]["warnings"])


def test_pivot_meta_pas_avertissement_si_synchro_ok():
    pivot = normalize_profil(_raw_depute())
    synchro_warnings = [w for w in pivot["meta"]["warnings"] if "synchro_sources" in w]
    assert synchro_warnings == []


# ---------------------------------------------------------------------------
# Profil brut incomplet (résilience)
# ---------------------------------------------------------------------------

def test_pivot_profil_vide_ne_leve_pas():
    pivot = normalize_profil({})
    assert isinstance(pivot, dict)
    # Un profil vide produit un nom vide → le schéma le signale, c'est normal.
    # Ce test vérifie uniquement qu'aucune exception n'est levée.
    errors = validate_profil(pivot)
    assert all(isinstance(e, str) for e in errors)


def test_pivot_identite_nulle_utilise_slug_pour_nom():
    raw = {"slug": "jean-dupont", "chambre": "deputes", "meta": {}}
    pivot = normalize_profil(raw)
    assert pivot["nom"] == "Jean Dupont"


def test_pivot_mandats_vides_si_absent():
    raw = _raw_depute()
    raw["mandats"] = []
    pivot = normalize_profil(raw)
    assert pivot["mandats"] == []


def test_pivot_votes_vides_si_absent():
    raw = _raw_depute()
    raw["votes"] = []
    pivot = normalize_profil(raw)
    assert pivot["votes"] == []


def test_pivot_identite_reprend_profession_et_naissance():
    raw = _raw_depute()
    pivot = normalize_profil(raw)
    assert pivot["identite"]["profession"] == "Avocat"
    assert pivot["identite"]["date_naissance"] == "1970-01-01"
    assert pivot["identite"]["num_circo"] == 3
    assert pivot["identite"]["source_url"] == "https://www.assemblee-nationale.fr/dyn/deputes/PA123456"


def test_pivot_identite_inclut_enrichissement_an():
    raw = _raw_depute()
    raw["identite"]["lieu_naissance"] = "Nantes (Loire-Atlantique)"
    raw["identite"]["uri_hatvp"] = "https://www.hatvp.fr/pages_nominatives/x"
    pivot = normalize_profil(raw)
    assert pivot["identite"]["lieu_naissance"] == "Nantes (Loire-Atlantique)"
    assert pivot["identite"]["uri_hatvp"] == "https://www.hatvp.fr/pages_nominatives/x"


def test_pivot_identite_reste_none_si_aucun_champ_renseigne():
    raw = {
        "slug": "jean-dupont",
        "chambre": "deputes",
        "identite": {"nom_complet": "Jean Dupont", "groupe_nom": "Renaissance"},
        "meta": {},
    }
    pivot = normalize_profil(raw)
    assert pivot["identite"] is None


def test_normalize_intervention_question_includes_extra_fields():
    """Les interventions de type "question" doivent inclure sous_type, ministere,
    reponse et date_reponse dans le pivot ; ces champs sont absents pour les
    autres types d'interventions."""
    raw = _raw_depute()
    raw["interventions"] = [
        {
            "date": "2025-01-15",
            "type_detail": "question",
            "sous_type": "QE",
            "sujet": "Budget 2025",
            "texte": "Monsieur le ministre...",
            "reponse": "La réponse est...",
            "date_reponse": "2025-03-10",
            "ministere": "Ministère de l'Économie",
            "groupe_sigle": "LFI",
            "fonction": None,
            "format": "prise_de_parole_developpee",
            "mots_cles": [],
            "url": "https://questions.assemblee-nationale.fr/q17/QANR5L17QE1.htm",
            "url_detail": "https://questions.assemblee-nationale.fr/q17/QANR5L17QE1.htm",
        }
    ]
    pivot = normalize_profil(raw)

    assert len(pivot["interventions"]) == 1
    i = pivot["interventions"][0]
    assert i["type_detail"] == "question"
    assert i["sous_type"] == "QE"
    assert i["ministere"] == "Ministère de l'Économie"
    assert i["reponse"] == "La réponse est..."
    assert i["date_reponse"] == "2025-03-10"
    assert i["source_url"] == "https://questions.assemblee-nationale.fr/q17/QANR5L17QE1.htm"


def test_normalize_intervention_non_question_has_no_extra_fields():
    """Pour les interventions qui ne sont pas des questions, les champs
    supplémentaires (sous_type, ministere, reponse, date_reponse) ne doivent
    pas être présents dans le pivot."""
    raw = _raw_depute()
    raw["interventions"] = [
        {
            "date": "2023-03-15",
            "type_detail": "loi",
            "sujet": "PLF 2024",
            "texte": "Je prends la parole...",
            "fonction": "Rapporteur",
            "format": "prise_de_parole_developpee",
            "mots_cles": ["budget"],
            "url_detail": "https://...",
        }
    ]
    pivot = normalize_profil(raw)

    assert len(pivot["interventions"]) == 1
    i = pivot["interventions"][0]
    assert "sous_type" not in i
    assert "ministere" not in i
    assert "reponse" not in i
    assert "date_reponse" not in i


# ---------------------------------------------------------------------------
# #80 — mapping Syceron → champs pivot (theme_officiel, seance, dossier, source)
# ---------------------------------------------------------------------------

def _raw_syceron_intervention() -> dict:
    """Retourne une intervention brute au format Syceron (depuis fetch_interventions_syceron)."""
    return {
        "id": "syceron_CRS17_000001",
        "date": "2025-02-11",
        "type_detail": "loi",
        "sujet": "Débat sur le budget rectificatif",
        "texte": "Je soutiens ce texte.",
        "fonction": "Président de groupe",
        "format": "prise_de_parole_developpee",
        "mots_cles": ["budget", "déficit"],
        "source_url": "https://data.assemblee-nationale.fr/static/openData/repository/17/vp/syceronbrut/syseron.xml.zip",
        "url": "https://data.assemblee-nationale.fr/static/openData/repository/17/vp/syceronbrut/syseron.xml.zip",
        "url_detail": None,
        "source_id": "CRS17_000001",
        "seance_ref": "RUANR5L17S2025O1N037",
        "session_ref": "S2024-2025",
        "orateur_id_source": "PA123456",
        "orateur_nom": "Jean Dupont",
        "point_ordre_du_jour": "Examen du PLF 2026",
        "legislature": "17",
    }


def test_normalize_syceron_intervention_theme_officiel():
    """Quand seance_ref est présent, theme_officiel doit être le sujet du débat."""
    raw = _raw_depute()
    raw["interventions"] = [_raw_syceron_intervention()]
    pivot = normalize_profil(raw)
    i = pivot["interventions"][0]
    assert i["theme_officiel"] == "Débat sur le budget rectificatif"


def test_normalize_syceron_intervention_seance():
    """Le champ seance doit contenir ref et session_ref depuis Syceron."""
    raw = _raw_depute()
    raw["interventions"] = [_raw_syceron_intervention()]
    pivot = normalize_profil(raw)
    i = pivot["interventions"][0]
    assert i["seance"] is not None
    assert i["seance"]["ref"] == "RUANR5L17S2025O1N037"
    assert i["seance"]["session_ref"] == "S2024-2025"


def test_normalize_syceron_intervention_dossier():
    """Le champ dossier doit contenir point_ordre_du_jour depuis Syceron."""
    raw = _raw_depute()
    raw["interventions"] = [_raw_syceron_intervention()]
    pivot = normalize_profil(raw)
    i = pivot["interventions"][0]
    assert i["dossier"] is not None
    assert i["dossier"]["point_ordre_du_jour"] == "Examen du PLF 2026"


def test_normalize_syceron_intervention_source():
    """Le champ source doit contenir les métadonnées de source Syceron."""
    raw = _raw_depute()
    raw["interventions"] = [_raw_syceron_intervention()]
    pivot = normalize_profil(raw)
    i = pivot["interventions"][0]
    assert i["source"] is not None
    assert i["source"]["type"] == "syceron"
    assert i["source"]["legislature"] == "17"


def test_normalize_profil_intervention_sans_syceron_champs_null():
    """Une intervention NosDéputés (sans seance_ref) doit avoir theme_officiel/seance/dossier/source à None."""
    raw = _raw_depute()
    # Intervention classique NosDéputés sans champs Syceron
    pivot = normalize_profil(raw)
    i = pivot["interventions"][0]
    assert i["theme_officiel"] is None
    assert i["seance"] is None
    assert i["dossier"] is None
    assert i["source"] is None


def test_tags_preferent_theme_officiel_si_disponible():
    """Quand theme_officiel est renseigné, il est préféré aux mots_cles pour les tags."""
    raw = _raw_depute()
    raw["interventions"] = [_raw_syceron_intervention()]
    pivot = normalize_profil(raw)
    # Le sujet Syceron doit être dans les tags
    assert "débat sur le budget rectificatif" in pivot["tags_thematiques"]
    # Les mots-clés scraping ne doivent PAS être dans les tags (theme_officiel prioritaire)
    assert "budget" not in pivot["tags_thematiques"]
    assert "déficit" not in pivot["tags_thematiques"]


def test_tags_fallback_mots_cles_sans_theme_officiel():
    """Sans theme_officiel, les mots_cles sont utilisés comme avant."""
    raw = _raw_depute()
    # L'intervention fixture n'a pas de seance_ref, donc theme_officiel = None
    pivot = normalize_profil(raw)
    assert "budget" in pivot["tags_thematiques"]
    assert "fiscalité" in pivot["tags_thematiques"]
