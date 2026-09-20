import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scrutins_index import ScrutinsIndex  # noqa: E402

from audit_groupe_dataset import (
    MOTIFS_DATE_NON_RESOLUE,
    _build_arg_parser,
    build_report,
    compute_agregation_warnings,
    compute_coherence_schema_version,
    compute_distribution_amendements,
    compute_doublons_groupe_id,
    compute_ecart_couverture_roster,
    compute_effectifs,
    compute_fraicheur_sources,
    compute_groupes_membres_sans_cohesion,
    compute_groupes_perimes,
    compute_nombre_cohesion_votes,
    compute_plage_dates_groupes,
    compute_presence_tags_thematiques,
    compute_tableau_croise_groupes,
    compute_validation_schema,
    generate_markdown_report,
    load_groupe_directory,
    main,
)


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "audit_groupe"


# ---------------------------------------------------------------------------
# load_groupe_directory : chargement des fixtures du dépôt
# ---------------------------------------------------------------------------

def test_load_groupe_directory_charge_les_groupes_valides():
    groupes_valides, _ = load_groupe_directory(FIXTURES_DIR)

    ids = {g["groupe_id"] for g in groupes_valides}
    assert ids == {"AN:LFI", "Senat:SOC"}  # AN:LFI apparaît deux fois (doublon volontaire)
    assert len(groupes_valides) == 3


def test_load_groupe_directory_scanne_recursivement():
    groupes_valides, _ = load_groupe_directory(FIXTURES_DIR)

    # groupe-3.json est dans un sous-dossier : doit être trouvé malgré tout.
    assert sum(1 for g in groupes_valides if g["groupe_id"] == "AN:LFI") == 2


def test_load_groupe_directory_ne_s_interrompt_pas_sur_fichier_invalide():
    groupes_valides, erreurs_lecture = load_groupe_directory(FIXTURES_DIR)

    assert len(groupes_valides) == 3
    assert len(erreurs_lecture) == 1


def test_load_groupe_directory_contenu_erreurs_lecture():
    _, erreurs_lecture = load_groupe_directory(FIXTURES_DIR)

    assert len(erreurs_lecture) == 1
    erreur = erreurs_lecture[0]
    assert set(erreur.keys()) == {"fichier", "erreur"}
    assert erreur["fichier"].endswith("invalide.json")
    assert isinstance(erreur["erreur"], str)
    assert erreur["erreur"]  # message non vide


# ---------------------------------------------------------------------------
# load_groupe_directory : cas limites construits en mémoire (tmp_path)
# ---------------------------------------------------------------------------

def test_load_groupe_directory_repertoire_vide(tmp_path):
    groupes_valides, erreurs_lecture = load_groupe_directory(tmp_path)

    assert groupes_valides == []
    assert erreurs_lecture == []


def test_load_groupe_directory_ignore_fichiers_non_json(tmp_path):
    (tmp_path / "notes.txt").write_text("pas un groupe", encoding="utf-8")

    groupes_valides, erreurs_lecture = load_groupe_directory(tmp_path)

    assert groupes_valides == []
    assert erreurs_lecture == []


def test_load_groupe_directory_objet_racine_non_dict(tmp_path):
    (tmp_path / "liste.json").write_text("[1, 2, 3]", encoding="utf-8")

    groupes_valides, erreurs_lecture = load_groupe_directory(tmp_path)

    assert groupes_valides == []
    assert len(erreurs_lecture) == 1
    assert erreurs_lecture[0]["fichier"].endswith("liste.json")


def test_load_groupe_directory_est_pure(tmp_path):
    fichier = tmp_path / "groupe.json"
    contenu = {"schema_version": "1", "groupe_id": "AN:TEST"}
    fichier.write_text(json.dumps(contenu), encoding="utf-8")

    load_groupe_directory(tmp_path)

    assert json.loads(fichier.read_text(encoding="utf-8")) == contenu


# ---------------------------------------------------------------------------
# Fixtures minimalistes en mémoire.
# ---------------------------------------------------------------------------

def make_amendements(**overrides):
    par_type_deposant = {
        t: {"nb_amendements": 0, "nb_adoptes": 0, "nb_rejetes": 0, "nb_irrecevables": 0,
            "nb_retires_ou_tombes": 0, "taux_adoption": None}
        for t in ("commission_rapporteur", "depute", "gouvernement", "inconnu")
    }
    par_type_deposant.update(overrides.pop("par_type_deposant", {}))
    return {
        "nb_amendements": 0, "nb_adoptes": 0, "nb_rejetes": 0, "nb_irrecevables": 0,
        "nb_retires_ou_tombes": 0, "taux_adoption": None,
        "par_type_deposant": par_type_deposant,
        **overrides,
    }


def groupe(groupe_id="AN:X", effectif=None, nb_membres=0, nb_cohesion=0,
           tags=None, amendements=None, sources=None):
    return {
        "groupe_id": groupe_id,
        "effectif": effectif if effectif is not None else {"actuel": 0, "min_historique": None, "max_historique": None},
        "membres": [{"membre_id": f"m{i}"} for i in range(nb_membres)],
        "cohesion_votes": [{"numero_scrutin": str(i)} for i in range(nb_cohesion)],
        "tags_thematiques_agreges": tags if tags is not None else [],
        "amendements_agreges": amendements if amendements is not None else make_amendements(),
        "sources": sources if sources is not None else [],
    }


# ---------------------------------------------------------------------------
# compute_effectifs
# ---------------------------------------------------------------------------

def test_compute_effectifs_liste_vide():
    resultat = compute_effectifs([])

    for champ in ("actuel", "min_historique", "max_historique"):
        assert resultat[champ] == {
            "nombre_groupes_renseignes": 0, "min": None, "max": None, "mediane": None, "moyenne": None,
        }


def test_compute_effectifs_actuel_toujours_renseigne():
    groupes = [
        groupe(effectif={"actuel": 0, "min_historique": None, "max_historique": None}),
        groupe(effectif={"actuel": 10, "min_historique": None, "max_historique": None}),
    ]

    resultat = compute_effectifs(groupes)

    assert resultat["actuel"] == {
        "nombre_groupes_renseignes": 2, "min": 0, "max": 10, "mediane": 5, "moyenne": 5.0,
    }


def test_compute_effectifs_min_max_historique_null_exclu_du_calcul():
    groupes = [
        groupe(effectif={"actuel": 5, "min_historique": None, "max_historique": None}),
        groupe(effectif={"actuel": 5, "min_historique": 3, "max_historique": 8}),
    ]

    resultat = compute_effectifs(groupes)

    # Un seul groupe a un historique renseigné : le null n'est jamais compté comme 0.
    assert resultat["min_historique"] == {
        "nombre_groupes_renseignes": 1, "min": 3, "max": 3, "mediane": 3, "moyenne": 3.0,
    }
    assert resultat["max_historique"]["nombre_groupes_renseignes"] == 1
    assert resultat["max_historique"]["min"] == 8


def test_compute_effectifs_champ_effectif_absent():
    resultat = compute_effectifs([{"groupe_id": "AN:X"}])

    assert resultat["actuel"]["nombre_groupes_renseignes"] == 0


# ---------------------------------------------------------------------------
# compute_nombre_cohesion_votes
# ---------------------------------------------------------------------------

def test_compute_nombre_cohesion_votes_liste_vide():
    resultat = compute_nombre_cohesion_votes([])

    assert resultat == {"min": None, "max": None, "mediane": None, "moyenne": None, "pct_groupes_a_zero": 0.0}


def test_compute_nombre_cohesion_votes_distribution():
    groupes = [groupe(nb_cohesion=0), groupe(nb_cohesion=4), groupe(nb_cohesion=8)]

    resultat = compute_nombre_cohesion_votes(groupes)

    assert resultat["min"] == 0
    assert resultat["max"] == 8
    assert resultat["mediane"] == 4
    assert resultat["moyenne"] == 4.0
    assert resultat["pct_groupes_a_zero"] == round(100 / 3, 2)


def test_compute_nombre_cohesion_votes_champ_absent_compte_comme_zero():
    resultat = compute_nombre_cohesion_votes([{"groupe_id": "AN:X"}])

    assert resultat["min"] == 0
    assert resultat["pct_groupes_a_zero"] == 100.0


# ---------------------------------------------------------------------------
# compute_distribution_amendements
# ---------------------------------------------------------------------------

def test_compute_distribution_amendements_liste_vide():
    resultat = compute_distribution_amendements([])

    for champ in ("nb_amendements", "nb_adoptes", "nb_rejetes", "nb_irrecevables", "nb_retires_ou_tombes"):
        assert resultat["global"][champ] == {"min": None, "max": None, "mediane": None, "moyenne": None}
    assert set(resultat["par_type_deposant"]) == {"commission_rapporteur", "depute", "gouvernement", "inconnu"}
    for type_deposant in resultat["par_type_deposant"]:
        assert resultat["par_type_deposant"][type_deposant]["nb_amendements"] == {
            "min": None, "max": None, "mediane": None, "moyenne": None,
        }


def test_compute_distribution_amendements_global():
    groupes = [
        groupe(amendements=make_amendements(nb_amendements=10, nb_adoptes=2)),
        groupe(amendements=make_amendements(nb_amendements=20, nb_adoptes=8)),
    ]

    resultat = compute_distribution_amendements(groupes)

    assert resultat["global"]["nb_amendements"] == {"min": 10, "max": 20, "mediane": 15, "moyenne": 15.0}
    assert resultat["global"]["nb_adoptes"] == {"min": 2, "max": 8, "mediane": 5, "moyenne": 5.0}


def test_compute_distribution_amendements_par_type_deposant_independant():
    groupes = [
        groupe(amendements=make_amendements(par_type_deposant={
            "depute": {"nb_amendements": 5, "nb_adoptes": 1, "nb_rejetes": 0, "nb_irrecevables": 0,
                       "nb_retires_ou_tombes": 0, "taux_adoption": 0.2},
            "gouvernement": {"nb_amendements": 3, "nb_adoptes": 3, "nb_rejetes": 0, "nb_irrecevables": 0,
                              "nb_retires_ou_tombes": 0, "taux_adoption": 1.0},
        })),
    ]

    resultat = compute_distribution_amendements(groupes)

    assert resultat["par_type_deposant"]["depute"]["nb_amendements"]["min"] == 5
    assert resultat["par_type_deposant"]["gouvernement"]["nb_amendements"]["min"] == 3
    # jamais agrégé entre types : "depute" ne doit jamais refléter le total.
    assert resultat["par_type_deposant"]["depute"]["nb_amendements"]["max"] != 8


def test_compute_distribution_amendements_bloc_absent_ou_invalide_ignore():
    groupes = [{"groupe_id": "AN:X"}, {"groupe_id": "AN:Y", "amendements_agreges": None}]

    resultat = compute_distribution_amendements(groupes)

    assert resultat["global"]["nb_amendements"]["min"] is None


# ---------------------------------------------------------------------------
# compute_presence_tags_thematiques
# ---------------------------------------------------------------------------

def test_compute_presence_tags_thematiques_liste_vide():
    assert compute_presence_tags_thematiques([]) == {"renseignes": 0, "total": 0, "taux_pct": 0.0}


def test_compute_presence_tags_thematiques_distingue_vide_et_renseigne():
    groupes = [
        groupe(tags=[]),
        groupe(tags=[{"tag": "budget", "nb_membres_porteurs": 1, "poids_relatif": 1.0}]),
    ]

    resultat = compute_presence_tags_thematiques(groupes)

    assert resultat == {"renseignes": 1, "total": 2, "taux_pct": 50.0}


def test_compute_presence_tags_thematiques_champ_absent():
    resultat = compute_presence_tags_thematiques([{"groupe_id": "AN:X"}])

    assert resultat == {"renseignes": 0, "total": 1, "taux_pct": 0.0}


# ---------------------------------------------------------------------------
# compute_groupes_membres_sans_cohesion
# ---------------------------------------------------------------------------

def test_compute_groupes_membres_sans_cohesion_liste_vide():
    resultat = compute_groupes_membres_sans_cohesion([])

    assert resultat == {
        "total_groupes": 0, "nb_groupes_membres_sans_cohesion": 0, "groupes_membres_sans_cohesion": [],
    }


def test_compute_groupes_membres_sans_cohesion_detecte_le_cas():
    groupes = [
        groupe(groupe_id="AN:X", nb_membres=3, nb_cohesion=0),
        groupe(groupe_id="AN:Y", nb_membres=3, nb_cohesion=5),
        groupe(groupe_id="AN:Z", nb_membres=0, nb_cohesion=0),  # pas de membre : jamais signalé
    ]

    resultat = compute_groupes_membres_sans_cohesion(groupes)

    assert resultat["total_groupes"] == 3
    assert resultat["nb_groupes_membres_sans_cohesion"] == 1
    assert resultat["groupes_membres_sans_cohesion"] == ["AN:X"]


# ---------------------------------------------------------------------------
# compute_tableau_croise_groupes
# ---------------------------------------------------------------------------

def test_compute_tableau_croise_groupes_liste_vide():
    resultat = compute_tableau_croise_groupes([])

    assert resultat == {"lignes": []}


def test_compute_tableau_croise_groupes_groupe_toutes_categories_renseignees():
    groupes = [
        {
            "groupe_id": "AN:LFI",
            "groupe_nom": "La France insoumise",
            "chambre": "AN",
            "membres": [{"membre_id": "a"}, {"membre_id": "b"}],
            "cohesion_votes": [{"numero_scrutin": "1"}],
            "tags_thematiques_agreges": [{"tag": "budget"}, {"tag": "sante"}, {"tag": "climat"}],
            "amendements_agreges": {"nb_amendements": 10},
        },
    ]

    resultat = compute_tableau_croise_groupes(groupes)

    assert resultat["lignes"] == [
        {
            "groupe_id": "AN:LFI", "groupe_nom": "La France insoumise", "chambre": "AN",
            "membres": 2, "cohesion_votes": 1, "tags_thematiques_agreges": 3, "amendements": 10,
        },
    ]


def test_compute_tableau_croise_groupes_categories_vides_ou_absentes():
    groupes = [
        {"groupe_id": "AN:X", "groupe_nom": "X", "chambre": "AN", "membres": [], "cohesion_votes": None},
        {"groupe_id": "AN:Y", "groupe_nom": "Y", "chambre": "AN"},
    ]

    resultat = compute_tableau_croise_groupes(groupes)

    assert resultat["lignes"] == [
        {
            "groupe_id": "AN:X", "groupe_nom": "X", "chambre": "AN",
            "membres": 0, "cohesion_votes": 0, "tags_thematiques_agreges": 0, "amendements": 0,
        },
        {
            "groupe_id": "AN:Y", "groupe_nom": "Y", "chambre": "AN",
            "membres": 0, "cohesion_votes": 0, "tags_thematiques_agreges": 0, "amendements": 0,
        },
    ]


def test_compute_tableau_croise_groupes_amendements_agreges_absent_ou_invalide():
    groupes = [
        {"groupe_id": "AN:X", "amendements_agreges": None},
        {"groupe_id": "AN:Y"},
        {"groupe_id": "AN:Z", "amendements_agreges": {"nb_amendements": "12"}},  # type invalide
    ]

    resultat = compute_tableau_croise_groupes(groupes)

    assert [ligne["amendements"] for ligne in resultat["lignes"]] == [0, 0, 0]


def test_compute_tableau_croise_groupes_trie_par_nom():
    groupes = [
        {"groupe_id": "x:z", "groupe_nom": "Zoé", "chambre": "AN"},
        {"groupe_id": "x:a", "groupe_nom": "Alban", "chambre": "AN"},
        {"groupe_id": "x:m", "groupe_nom": "Marc", "chambre": "AN"},
    ]

    resultat = compute_tableau_croise_groupes(groupes)

    assert [ligne["groupe_nom"] for ligne in resultat["lignes"]] == ["Alban", "Marc", "Zoé"]


def test_compute_tableau_croise_groupes_nom_absent_tri_deterministe_par_id():
    groupes = [
        {"groupe_id": "x:b", "groupe_nom": None, "chambre": "AN"},
        {"groupe_id": "x:a", "groupe_nom": None, "chambre": "AN"},
    ]

    resultat = compute_tableau_croise_groupes(groupes)

    assert [ligne["groupe_id"] for ligne in resultat["lignes"]] == ["x:a", "x:b"]


# ---------------------------------------------------------------------------
# compute_plage_dates_groupes
# ---------------------------------------------------------------------------

#: Index minimal, de la même classe que celui du pipeline : `cohesion_votes[]`
#: ne porte qu'un `scrutin_id` depuis #432, la date vit ici (#726).
def _index(scrutins):
    return ScrutinsIndex({s["id"]: s for s in scrutins})


def test_compute_plage_dates_groupes_liste_vide():
    resultat = compute_plage_dates_groupes([], _index([{"id": "an:16:1", "date": "2023-05-10"}]))

    assert resultat == {"lignes": [], "index_disponible": True, "dates_non_resolues": {}}


def test_compute_plage_dates_groupes_sans_cohesion_votes_cellule_null():
    groupes = [{"groupe_id": "AN:X", "groupe_nom": "X", "chambre": "AN"}]

    resultat = compute_plage_dates_groupes(groupes, _index([{"id": "an:16:1", "date": "2023-05-10"}]))

    assert resultat["lignes"] == [
        {
            "groupe_id": "AN:X", "groupe_nom": "X", "chambre": "AN",
            "cohesion_votes": None, "amendements_agreges": None,
        },
    ]
    assert resultat["dates_non_resolues"] == {}


def test_compute_plage_dates_groupes_cohesion_votes_vide_cellule_null():
    groupes = [{"groupe_id": "AN:X", "groupe_nom": "X", "chambre": "AN", "cohesion_votes": []}]

    resultat = compute_plage_dates_groupes(groupes, _index([]))

    assert resultat["lignes"][0]["cohesion_votes"] is None


def test_compute_plage_dates_groupes_la_date_vient_de_l_index_pas_de_l_entree():
    """#726 — la fonction lisait `entree["date"]`, une clé qu'aucune des 61 596
    entrées publiées ne porte : le tableau était vide par construction depuis
    #432, et 61 596 lignes de « date invalide » enterraient le reste du rapport."""
    groupes = [
        {
            "groupe_id": "AN:X", "groupe_nom": "X", "chambre": "AN",
            "cohesion_votes": [
                {"scrutin_id": "an:16:1"},
                {"scrutin_id": "an:16:2"},
                {"scrutin_id": "an:16:3"},
            ],
        },
    ]
    index = _index([
        {"id": "an:16:1", "date": "2023-05-10"},
        {"id": "an:16:2", "date": "2024-06-07"},
        {"id": "an:16:3", "date": "2022-01-01"},
    ])

    resultat = compute_plage_dates_groupes(groupes, index)

    assert resultat["lignes"][0]["cohesion_votes"] == {"min": "2022-01-01", "max": "2024-06-07"}
    assert resultat["dates_non_resolues"] == {}


def test_compute_plage_dates_groupes_une_date_dans_l_entree_ne_compte_pas():
    """La date portée par l'entrée est ignorée : le champ n'existe pas au schéma,
    et le lire ferait dépendre le rapport d'une donnée que rien ne produit."""
    groupes = [
        {
            "groupe_id": "AN:X", "groupe_nom": "X", "chambre": "AN",
            "cohesion_votes": [{"scrutin_id": "an:16:1", "date": "1999-01-01"}],
        },
    ]

    resultat = compute_plage_dates_groupes(groupes, _index([{"id": "an:16:1", "date": "2023-05-10"}]))

    assert resultat["lignes"][0]["cohesion_votes"] == {"min": "2023-05-10", "max": "2023-05-10"}


def test_compute_plage_dates_groupes_amendements_agreges_toujours_null():
    groupes = [{"groupe_id": "AN:X", "groupe_nom": "X", "chambre": "AN"}]

    resultat = compute_plage_dates_groupes(groupes, _index([]))

    assert resultat["lignes"][0]["amendements_agreges"] is None


def test_compute_plage_dates_groupes_motifs_comptes_jamais_enumeres():
    """Trois motifs fermés, chacun compté : « le scrutin n'est pas dans l'index »
    et « sa date est illisible » ne se réparent pas au même endroit."""
    groupes = [
        {
            "groupe_id": "AN:X", "groupe_nom": "X", "chambre": "AN",
            "cohesion_votes": [
                {"scrutin_id": "an:16:1"},
                {"scrutin_id": "an:16:absent"},
                {"scrutin_id": "an:16:muet"},
                {},
            ],
        },
    ]
    index = _index([
        {"id": "an:16:1", "date": "2024-06-07"},
        {"id": "an:16:muet", "date": "pas-une-date"},
    ])

    resultat = compute_plage_dates_groupes(groupes, index)

    assert resultat["lignes"][0]["cohesion_votes"] == {"min": "2024-06-07", "max": "2024-06-07"}
    assert resultat["dates_non_resolues"] == {
        "date_invalide": 1, "scrutin_id_absent": 1, "scrutin_inconnu": 1,
    }
    assert set(resultat["dates_non_resolues"]) <= MOTIFS_DATE_NON_RESOLUE


def test_compute_plage_dates_groupes_index_absent_est_un_trou_declare():
    """Sans index, la cellule est `None` — mais `index_disponible: False` empêche
    de lire ce `None` comme « ce groupe n'a pas de scrutin » (§2 règle 5)."""
    groupes = [
        {
            "groupe_id": "AN:X", "groupe_nom": "X", "chambre": "AN",
            "cohesion_votes": [{"scrutin_id": "an:16:1"}],
        },
    ]

    resultat = compute_plage_dates_groupes(groupes, None)

    assert resultat["lignes"][0]["cohesion_votes"] is None
    assert resultat["index_disponible"] is False


def test_compute_plage_dates_groupes_index_vide_vaut_index_absent():
    """`scrutins_index.charger()` rend un index VIDE sur un fichier absent : le
    traiter comme disponible ferait passer « le fichier manquait » pour « ces
    groupes n'ont pas de scrutin » — la règle de #510."""
    groupes = [
        {
            "groupe_id": "AN:X", "groupe_nom": "X", "chambre": "AN",
            "cohesion_votes": [{"scrutin_id": "an:16:1"}],
        },
    ]

    resultat = compute_plage_dates_groupes(groupes, _index([]))

    assert resultat["index_disponible"] is False


def test_compute_plage_dates_groupes_trie_par_nom_comme_tableau_croise():
    groupes = [
        {"groupe_id": "x:z", "groupe_nom": "Zoé", "chambre": "AN"},
        {"groupe_id": "x:a", "groupe_nom": "Alban", "chambre": "AN"},
    ]

    resultat = compute_plage_dates_groupes(groupes, _index([]))

    assert [ligne["groupe_nom"] for ligne in resultat["lignes"]] == ["Alban", "Zoé"]


# ---------------------------------------------------------------------------
# compute_validation_schema
# ---------------------------------------------------------------------------

def test_compute_validation_schema_liste_vide():
    assert compute_validation_schema([]) == {
        "total_groupes": 0, "nb_groupes_invalides": 0, "groupes_invalides": [],
    }


def test_compute_validation_schema_groupes_valides_des_fixtures():
    groupes_valides, _ = load_groupe_directory(FIXTURES_DIR)

    resultat = compute_validation_schema(groupes_valides)

    assert resultat["total_groupes"] == 3
    assert resultat["nb_groupes_invalides"] == 0
    assert resultat["groupes_invalides"] == []


def test_compute_validation_schema_detecte_les_erreurs():
    groupes = [{"groupe_id": "AN:X"}]  # clés obligatoires manquantes

    resultat = compute_validation_schema(groupes)

    assert resultat["nb_groupes_invalides"] == 1
    entree = resultat["groupes_invalides"][0]
    assert entree["groupe_id"] == "AN:X"
    assert entree["erreurs"]  # au moins une erreur remontée


def test_compute_validation_schema_trie_par_groupe_id():
    groupes = [{"groupe_id": "AN:Z"}, {"groupe_id": "AN:A"}]

    resultat = compute_validation_schema(groupes)

    assert [e["groupe_id"] for e in resultat["groupes_invalides"]] == ["AN:A", "AN:Z"]


# ---------------------------------------------------------------------------
# compute_coherence_schema_version
# ---------------------------------------------------------------------------

def test_compute_coherence_schema_version_liste_vide():
    assert compute_coherence_schema_version([]) == {"groupes_incoherents": []}


def test_compute_coherence_schema_version_coherente():
    groupes = [{"groupe_id": "AN:X", "schema_version": "1", "meta": {"schema_version": "1"}}]

    assert compute_coherence_schema_version(groupes) == {"groupes_incoherents": []}


def test_compute_coherence_schema_version_divergente():
    groupes = [{"groupe_id": "AN:X", "schema_version": "1", "meta": {"schema_version": "2"}}]

    resultat = compute_coherence_schema_version(groupes)

    assert resultat == {
        "groupes_incoherents": [
            {"groupe_id": "AN:X", "schema_version": "1", "meta_schema_version": "2"}
        ]
    }


def test_compute_coherence_schema_version_meta_absente_ou_invalide():
    groupes = [
        {"groupe_id": "AN:X", "schema_version": "1"},
        {"groupe_id": "AN:Y", "schema_version": "1", "meta": "pas un dict"},
    ]

    resultat = compute_coherence_schema_version(groupes)

    assert {g["groupe_id"] for g in resultat["groupes_incoherents"]} == {"AN:X", "AN:Y"}
    assert all(g["meta_schema_version"] is None for g in resultat["groupes_incoherents"])


# ---------------------------------------------------------------------------
# compute_ecart_couverture_roster
# ---------------------------------------------------------------------------

def test_compute_ecart_couverture_roster_liste_vide():
    assert compute_ecart_couverture_roster([]) == {"groupes": []}


def test_compute_ecart_couverture_roster_absent_jamais_inclus():
    groupes = [
        {"groupe_id": "AN:X", "meta": {}},
        {"groupe_id": "AN:Y", "meta": {"couverture_roster": None}},
        {"groupe_id": "AN:Z"},
    ]

    assert compute_ecart_couverture_roster(groupes) == {"groupes": []}


def test_compute_ecart_couverture_roster_calcule_l_ecart():
    groupes = [
        {"groupe_id": "AN:X", "meta": {"couverture_roster": {"roster_total": 10, "profils_disponibles": 3}}},
    ]

    resultat = compute_ecart_couverture_roster(groupes)

    assert resultat == {
        "groupes": [
            {
                "groupe_id": "AN:X", "roster_total": 10, "profils_disponibles": 3,
                "ecart": 7, "taux_couverture_pct": 30.0,
            }
        ]
    }


def test_compute_ecart_couverture_roster_taux_couverture_zero_pourcent():
    groupes = [
        {"groupe_id": "AN:X", "meta": {"couverture_roster": {"roster_total": 76, "profils_disponibles": 0}}},
    ]

    resultat = compute_ecart_couverture_roster(groupes)

    assert resultat["groupes"][0]["taux_couverture_pct"] == 0.0


def test_compute_ecart_couverture_roster_taux_couverture_partiel():
    groupes = [
        {"groupe_id": "AN:X", "meta": {"couverture_roster": {"roster_total": 193, "profils_disponibles": 1}}},
    ]

    resultat = compute_ecart_couverture_roster(groupes)

    assert resultat["groupes"][0]["taux_couverture_pct"] == round(100 / 193, 2)


def test_compute_ecart_couverture_roster_taux_couverture_quasi_complete():
    groupes = [
        {"groupe_id": "AN:X", "meta": {"couverture_roster": {"roster_total": 100, "profils_disponibles": 99}}},
    ]

    resultat = compute_ecart_couverture_roster(groupes)

    assert resultat["groupes"][0]["taux_couverture_pct"] == 99.0


def test_compute_ecart_couverture_roster_roster_total_zero_ne_divise_pas_par_zero():
    groupes = [
        {"groupe_id": "AN:X", "meta": {"couverture_roster": {"roster_total": 0, "profils_disponibles": 0}}},
    ]

    resultat = compute_ecart_couverture_roster(groupes)

    assert resultat["groupes"][0]["taux_couverture_pct"] == 0.0
    assert resultat["groupes"][0]["ecart"] == 0


def test_compute_ecart_couverture_roster_trie_par_groupe_id():
    groupes = [
        {"groupe_id": "AN:Z", "meta": {"couverture_roster": {"roster_total": 1, "profils_disponibles": 1}}},
        {"groupe_id": "AN:A", "meta": {"couverture_roster": {"roster_total": 2, "profils_disponibles": 1}}},
    ]

    resultat = compute_ecart_couverture_roster(groupes)

    assert [g["groupe_id"] for g in resultat["groupes"]] == ["AN:A", "AN:Z"]


def test_compute_ecart_couverture_roster_ignore_valeurs_non_entieres():
    groupes = [
        {"groupe_id": "AN:X", "meta": {"couverture_roster": {"roster_total": "10", "profils_disponibles": 3}}},
    ]

    assert compute_ecart_couverture_roster(groupes) == {"groupes": []}


# ---------------------------------------------------------------------------
# compute_doublons_groupe_id
# ---------------------------------------------------------------------------

def test_compute_doublons_groupe_id_liste_vide():
    assert compute_doublons_groupe_id([]) == {"doublons": []}


def test_compute_doublons_groupe_id_sans_doublon():
    groupes = [{"groupe_id": "AN:X"}, {"groupe_id": "AN:Y"}]

    assert compute_doublons_groupe_id(groupes) == {"doublons": []}


def test_compute_doublons_groupe_id_detecte_les_doublons():
    groupes = [
        {"groupe_id": "AN:X"}, {"groupe_id": "AN:X"}, {"groupe_id": "AN:Y"}, {"groupe_id": "AN:X"},
    ]

    resultat = compute_doublons_groupe_id(groupes)

    assert resultat == {"doublons": [{"groupe_id": "AN:X", "occurrences": 3}]}


def test_compute_doublons_groupe_id_ignore_id_absent_ou_vide():
    groupes = [{"groupe_id": ""}, {"groupe_id": ""}, {}, {}]

    assert compute_doublons_groupe_id(groupes) == {"doublons": []}


def test_compute_doublons_groupe_id_sur_les_fixtures_du_depot():
    groupes_valides, _ = load_groupe_directory(FIXTURES_DIR)

    resultat = compute_doublons_groupe_id(groupes_valides)

    assert resultat == {"doublons": [{"groupe_id": "AN:LFI", "occurrences": 2}]}


# ---------------------------------------------------------------------------
# Fixtures pour compute_fraicheur_sources.
# ---------------------------------------------------------------------------

REFERENCE = datetime(2026, 8, 9, tzinfo=timezone.utc)


def source(type_source, jours_anciennete):
    synchro = REFERENCE - timedelta(days=jours_anciennete)
    return {"type": type_source, "url": "u", "synchro_le": synchro.isoformat()}


def groupe_sources(groupe_id, *sources):
    return {"groupe_id": groupe_id, "sources": list(sources)}


# ---------------------------------------------------------------------------
# compute_fraicheur_sources
# ---------------------------------------------------------------------------

def test_compute_fraicheur_sources_liste_vide():
    resultat = compute_fraicheur_sources([], reference_date=REFERENCE)

    assert resultat == {"total_sources_datees": 0, "par_type_source": {}}


def test_compute_fraicheur_sources_min_max_mediane_moyenne():
    groupes = [
        groupe_sources("a", source("nosdeputes", 0)),
        groupe_sources("b", source("nosdeputes", 10)),
        groupe_sources("c", source("nosdeputes", 20)),
    ]

    resultat = compute_fraicheur_sources(groupes, reference_date=REFERENCE)
    stats = resultat["par_type_source"]["nosdeputes"]

    assert resultat["total_sources_datees"] == 3
    assert stats["nombre_sources"] == 3
    assert stats["min_jours"] == 0
    assert stats["max_jours"] == 20
    assert stats["mediane_jours"] == 10
    assert stats["moyenne_jours"] == 10.0


def test_compute_fraicheur_sources_regroupe_par_type():
    groupes = [groupe_sources("a", source("nosdeputes", 5), source("nossenateurs", 50))]

    resultat = compute_fraicheur_sources(groupes, reference_date=REFERENCE)

    assert set(resultat["par_type_source"]) == {"nosdeputes", "nossenateurs"}
    assert resultat["par_type_source"]["nosdeputes"]["min_jours"] == 5
    assert resultat["par_type_source"]["nossenateurs"]["min_jours"] == 50


def test_compute_fraicheur_sources_type_absent_regroupe_sous_null():
    groupes = [groupe_sources("a", {"url": "u", "synchro_le": REFERENCE.isoformat()})]

    resultat = compute_fraicheur_sources(groupes, reference_date=REFERENCE)

    assert resultat["par_type_source"]["null"]["nombre_sources"] == 1


def test_compute_fraicheur_sources_ignore_synchro_le_invalide_ou_absente():
    groupes = [
        groupe_sources("a", {"type": "nosdeputes", "url": "u", "synchro_le": "pas-une-date"}),
        groupe_sources("b", {"type": "nosdeputes", "url": "u"}),
        groupe_sources("c", source("nosdeputes", 1)),
    ]

    resultat = compute_fraicheur_sources(groupes, reference_date=REFERENCE)

    assert resultat["total_sources_datees"] == 1
    assert resultat["par_type_source"]["nosdeputes"]["nombre_sources"] == 1


def test_compute_fraicheur_sources_ignore_groupes_sans_sources():
    resultat = compute_fraicheur_sources(
        [groupe_sources("a"), {"groupe_id": "b"}], reference_date=REFERENCE
    )

    assert resultat == {"total_sources_datees": 0, "par_type_source": {}}


def test_compute_fraicheur_sources_sans_reference_date_utilise_maintenant():
    hier = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    groupes = [groupe_sources("a", {"type": "nosdeputes", "url": "u", "synchro_le": hier})]

    resultat = compute_fraicheur_sources(groupes)

    assert resultat["par_type_source"]["nosdeputes"]["min_jours"] == 1


# ---------------------------------------------------------------------------
# compute_groupes_perimes
# ---------------------------------------------------------------------------

def test_compute_groupes_perimes_toutes_sources_perimees():
    groupes = [groupe_sources("a", source("nosdeputes", 100))]

    resultat = compute_groupes_perimes(groupes, staleness_days=30, reference_date=REFERENCE)

    assert resultat == ["a"]


def test_compute_groupes_perimes_une_source_fraiche_suffit_a_exclure():
    groupes = [groupe_sources("a", source("nosdeputes", 100), source("nossenateurs", 5))]

    resultat = compute_groupes_perimes(groupes, staleness_days=30, reference_date=REFERENCE)

    assert resultat == []


def test_compute_groupes_perimes_seuil_variable():
    groupes = [groupe_sources("a", source("nosdeputes", 15))]

    assert compute_groupes_perimes(groupes, staleness_days=10, reference_date=REFERENCE) == ["a"]
    assert compute_groupes_perimes(groupes, staleness_days=20, reference_date=REFERENCE) == []


def test_compute_groupes_perimes_exactement_au_seuil_n_est_pas_perime():
    groupes = [groupe_sources("a", source("nosdeputes", 30))]

    resultat = compute_groupes_perimes(groupes, staleness_days=30, reference_date=REFERENCE)

    assert resultat == []


def test_compute_groupes_perimes_aucune_source_n_est_jamais_perime():
    groupes = [groupe_sources("a"), {"groupe_id": "b"}]

    resultat = compute_groupes_perimes(groupes, staleness_days=0, reference_date=REFERENCE)

    assert resultat == []


def test_compute_groupes_perimes_trie_les_resultats():
    groupes = [
        groupe_sources("z", source("nosdeputes", 100)),
        groupe_sources("a", source("nosdeputes", 100)),
    ]

    resultat = compute_groupes_perimes(groupes, staleness_days=30, reference_date=REFERENCE)

    assert resultat == ["a", "z"]


# ---------------------------------------------------------------------------
# compute_agregation_warnings
# ---------------------------------------------------------------------------

def groupe_warnings(groupe_id, *warnings):
    return {"groupe_id": groupe_id, "meta": {"warnings": list(warnings)}}


def test_compute_agregation_warnings_aucun_groupe():
    assert compute_agregation_warnings([]) == {"total_warnings": 0, "par_type": {}}


def test_compute_agregation_warnings_groupes_sans_warnings():
    groupes = [groupe_warnings("a"), {"groupe_id": "b"}, {"groupe_id": "c", "meta": {}}]

    resultat = compute_agregation_warnings(groupes)

    assert resultat == {"total_warnings": 0, "par_type": {}}


def test_compute_agregation_warnings_type_par_prefixe_avant_les_deux_points():
    groupes = [
        groupe_warnings("a", "couverture_roster : profils disponibles inferieurs au roster reel."),
        groupe_warnings("b", "couverture_roster : ecart important."),
    ]

    resultat = compute_agregation_warnings(groupes)

    assert resultat["total_warnings"] == 2
    assert resultat["par_type"]["couverture_roster"] == {"frequence": 2, "groupe_ids": ["a", "b"]}


def test_compute_agregation_warnings_message_sans_deux_points_utilise_le_message_entier():
    groupes = [groupe_warnings("a", "tags_thematiques calcules en repli sur les interventions.")]

    resultat = compute_agregation_warnings(groupes)

    assert resultat["par_type"] == {
        "tags_thematiques calcules en repli sur les interventions.": {"frequence": 1, "groupe_ids": ["a"]},
    }


def test_compute_agregation_warnings_plusieurs_types_et_frequences():
    groupes = [
        groupe_warnings("a", "cohesion introuvable : x", "amendements indisponibles : y"),
        groupe_warnings("b", "cohesion introuvable : z"),
    ]

    resultat = compute_agregation_warnings(groupes)

    assert resultat["total_warnings"] == 3
    assert resultat["par_type"]["cohesion introuvable"] == {"frequence": 2, "groupe_ids": ["a", "b"]}
    assert resultat["par_type"]["amendements indisponibles"] == {"frequence": 1, "groupe_ids": ["a"]}


def test_compute_agregation_warnings_meme_type_deux_fois_meme_groupe_ids_dedupliques():
    groupes = [groupe_warnings("a", "cohesion introuvable : x", "cohesion introuvable : y")]

    resultat = compute_agregation_warnings(groupes)

    assert resultat["par_type"]["cohesion introuvable"] == {"frequence": 2, "groupe_ids": ["a"]}


def test_compute_agregation_warnings_sur_les_fixtures_du_depot():
    groupes_valides, _ = load_groupe_directory(FIXTURES_DIR)

    resultat = compute_agregation_warnings(groupes_valides)

    assert resultat["total_warnings"] == 1
    assert resultat["par_type"]["couverture_roster"]["groupe_ids"] == ["AN:LFI"]


# ---------------------------------------------------------------------------
# Toutes les fonctions compute_* restent pures et sérialisables en JSON
# sur le corpus de fixtures du dépôt.
# ---------------------------------------------------------------------------

def test_toutes_les_fonctions_compute_sur_les_fixtures_du_depot_sont_serialisables():
    groupes_valides, _ = load_groupe_directory(FIXTURES_DIR)

    rapport = {
        "effectifs": compute_effectifs(groupes_valides),
        "nombre_cohesion_votes": compute_nombre_cohesion_votes(groupes_valides),
        "distribution_amendements": compute_distribution_amendements(groupes_valides),
        "presence_tags_thematiques": compute_presence_tags_thematiques(groupes_valides),
        "groupes_membres_sans_cohesion": compute_groupes_membres_sans_cohesion(groupes_valides),
        "validation_schema": compute_validation_schema(groupes_valides),
        "coherence_schema_version": compute_coherence_schema_version(groupes_valides),
        "ecart_couverture_roster": compute_ecart_couverture_roster(groupes_valides),
        "doublons_groupe_id": compute_doublons_groupe_id(groupes_valides),
        "fraicheur_sources": compute_fraicheur_sources(groupes_valides, reference_date=REFERENCE),
        "warnings": compute_agregation_warnings(groupes_valides),
    }

    json.dumps(rapport, ensure_ascii=False)


# ---------------------------------------------------------------------------
# build_report
# ---------------------------------------------------------------------------

def test_build_report_structure_top_level_keys():
    rapport = build_report([], [], staleness_days=30, reference_date=REFERENCE)

    assert set(rapport.keys()) == {
        "meta", "volumetrie", "completude", "coherence", "fraicheur",
        "warnings", "tableau_croise_groupes", "plage_dates_groupes", "erreurs_lecture",
    }
    assert set(rapport["volumetrie"].keys()) == {
        "effectifs", "nombre_cohesion_votes", "distribution_amendements",
    }
    assert set(rapport["completude"].keys()) == {
        "presence_tags_thematiques", "groupes_membres_sans_cohesion",
    }
    assert set(rapport["coherence"].keys()) == {
        "validation_schema", "coherence_schema_version",
        "ecart_couverture_roster", "doublons_groupe_id",
    }
    assert set(rapport["fraicheur"].keys()) == {"fraicheur_sources", "groupes_perimes"}


def test_build_report_meta_section():
    erreurs = [{"fichier": "x.json", "erreur": "boom"}]
    groupes = [groupe_sources("a", source("nosdeputes", 5))]

    rapport = build_report(groupes, erreurs, staleness_days=15, reference_date=REFERENCE)

    assert rapport["meta"] == {
        "genere_le": REFERENCE.isoformat(),
        "total_groupes": 1,
        "total_erreurs_lecture": 1,
        "staleness_days": 15,
    }


def test_build_report_erreurs_lecture_passthrough():
    erreurs = [{"fichier": "a.json", "erreur": "JSON invalide"}]

    rapport = build_report([], erreurs, reference_date=REFERENCE)

    assert rapport["erreurs_lecture"] == erreurs


def test_build_report_delegue_aux_fonctions_compute():
    groupes = [
        groupe_warnings("a", "cohesion introuvable : x"),
        groupe(groupe_id="b", nb_membres=3, nb_cohesion=0),
    ]
    erreurs = []

    rapport = build_report(groupes, erreurs, staleness_days=30, reference_date=REFERENCE)

    assert rapport["volumetrie"]["effectifs"] == compute_effectifs(groupes)
    assert rapport["volumetrie"]["nombre_cohesion_votes"] == compute_nombre_cohesion_votes(groupes)
    assert (
        rapport["volumetrie"]["distribution_amendements"]
        == compute_distribution_amendements(groupes)
    )
    assert (
        rapport["completude"]["presence_tags_thematiques"]
        == compute_presence_tags_thematiques(groupes)
    )
    assert (
        rapport["completude"]["groupes_membres_sans_cohesion"]
        == compute_groupes_membres_sans_cohesion(groupes)
    )
    assert rapport["coherence"]["validation_schema"] == compute_validation_schema(groupes)
    assert (
        rapport["coherence"]["coherence_schema_version"]
        == compute_coherence_schema_version(groupes)
    )
    assert (
        rapport["coherence"]["ecart_couverture_roster"]
        == compute_ecart_couverture_roster(groupes)
    )
    assert rapport["coherence"]["doublons_groupe_id"] == compute_doublons_groupe_id(groupes)
    assert (
        rapport["fraicheur"]["fraicheur_sources"]
        == compute_fraicheur_sources(groupes, reference_date=REFERENCE)
    )
    assert (
        rapport["fraicheur"]["groupes_perimes"]
        == compute_groupes_perimes(groupes, staleness_days=30, reference_date=REFERENCE)
    )
    assert rapport["warnings"] == compute_agregation_warnings(groupes)
    assert (
        rapport["tableau_croise_groupes"]
        == compute_tableau_croise_groupes(groupes)
    )
    assert (
        rapport["plage_dates_groupes"]
        == compute_plage_dates_groupes(groupes)
    )


def test_build_report_staleness_days_par_defaut():
    rapport = build_report([], [], reference_date=REFERENCE)

    assert rapport["meta"]["staleness_days"] == 30


def test_build_report_sans_reference_date_utilise_maintenant():
    rapport = build_report([], [])

    genere_le = datetime.fromisoformat(rapport["meta"]["genere_le"])
    assert (datetime.now(timezone.utc) - genere_le).total_seconds() < 5


def test_build_report_sur_les_fixtures_du_depot():
    groupes_valides, erreurs_lecture = load_groupe_directory(FIXTURES_DIR)

    rapport = build_report(groupes_valides, erreurs_lecture, staleness_days=30, reference_date=REFERENCE)

    assert rapport["meta"]["total_groupes"] == 3
    assert rapport["meta"]["total_erreurs_lecture"] == 1
    # Le rapport doit rester intégralement sérialisable en JSON.
    json.dumps(rapport, ensure_ascii=False)


# ---------------------------------------------------------------------------
# generate_markdown_report
# ---------------------------------------------------------------------------

def test_generate_markdown_report_contient_toutes_les_sections():
    rapport = build_report([], [], reference_date=REFERENCE)

    markdown = generate_markdown_report(rapport)

    assert "# Rapport d'audit du jeu de données groupes" in markdown
    assert "## Volumétrie" in markdown
    assert "## Tableau croisé des volumes par groupe" in markdown
    assert "## Tableau croisé des plages temporelles par groupe" in markdown
    assert "## Complétude" in markdown
    assert "## Cohérence" in markdown
    assert "## Fraîcheur" in markdown
    assert "## Warnings" in markdown
    assert "## Erreurs de lecture" in markdown


def test_generate_markdown_report_sections_vides_affichent_un_message_explicite():
    rapport = build_report([], [], reference_date=REFERENCE)

    markdown = generate_markdown_report(rapport)

    assert "Aucun groupe invalide détecté." in markdown
    assert "Aucune divergence détectée." in markdown
    assert "Aucune donnée de couverture roster" in markdown
    assert "Aucun doublon détecté." in markdown
    assert "Aucune source datée." in markdown
    assert "Aucun groupe périmé." in markdown
    assert "Aucun warning." in markdown
    assert "Aucune erreur de lecture." in markdown
    assert "Toutes les dates de scrutin se résolvent." in markdown


def test_generate_markdown_report_reflete_les_donnees_du_rapport():
    groupes = [{"groupe_id": "a"}, {"groupe_id": "a"}]  # doublon volontaire
    erreurs = [{"fichier": "casse.json", "erreur": "JSON invalide"}]

    rapport = build_report(groupes, erreurs, reference_date=REFERENCE)
    markdown = generate_markdown_report(rapport)

    assert "casse.json" in markdown
    assert "JSON invalide" in markdown
    assert "| a | 2 |" in markdown  # doublons_groupe_id : "a" en double


def test_generate_markdown_report_amendements_agreges_documente_non_applicable():
    groupes = [{"groupe_id": "AN:X", "groupe_nom": "X", "chambre": "AN"}]

    rapport = build_report(groupes, [], reference_date=REFERENCE)
    markdown = generate_markdown_report(rapport)

    # La colonne amendements_agreges est explicitement documentée comme non
    # applicable, jamais une cellule vide silencieuse.
    assert "N/A (non applicable)" in markdown
    assert "ne stocke que des compteurs" in markdown
    assert "N/D" in markdown  # cellule cohesion_votes du groupe sans cohesion_votes


def test_generate_markdown_report_retourne_une_chaine_non_vide():
    groupes_valides, erreurs_lecture = load_groupe_directory(FIXTURES_DIR)
    rapport = build_report(groupes_valides, erreurs_lecture, reference_date=REFERENCE)

    markdown = generate_markdown_report(rapport)

    assert isinstance(markdown, str)
    assert len(markdown) > 0


# ---------------------------------------------------------------------------
# CLI : _build_arg_parser / main
# ---------------------------------------------------------------------------

def test_build_arg_parser_defauts():
    parser = _build_arg_parser()
    args = parser.parse_args([])

    assert args.input_dir == "pivot_data/groupes"
    assert args.staleness_days == 30
    assert args.output_json is None
    assert args.output_md is None


def test_main_ecrit_json_et_markdown(tmp_path):
    output_json = tmp_path / "rapport.json"
    output_md = tmp_path / "rapport.md"

    code = main([
        "--input-dir", str(FIXTURES_DIR),
        "--output-json", str(output_json),
        "--output-md", str(output_md),
        "--staleness-days", "30",
    ])

    assert code == 0
    assert output_json.exists()
    assert output_md.exists()

    rapport = json.loads(output_json.read_text(encoding="utf-8"))
    assert rapport["meta"]["total_groupes"] == 3
    assert rapport["meta"]["total_erreurs_lecture"] == 1
    assert rapport["meta"]["staleness_days"] == 30

    markdown = output_md.read_text(encoding="utf-8")
    assert "# Rapport d'audit du jeu de données groupes" in markdown


def test_main_sans_output_json_ecrit_sur_stdout(capsys):
    code = main(["--input-dir", str(FIXTURES_DIR)])

    assert code == 0
    captured = capsys.readouterr()
    rapport = json.loads(captured.out)
    assert rapport["meta"]["total_groupes"] == 3


def test_main_dossier_introuvable_retourne_1(tmp_path):
    code = main(["--input-dir", str(tmp_path / "n-existe-pas")])

    assert code == 1


def test_main_out_dir_est_cree_si_absent(tmp_path):
    output_json = tmp_path / "sous" / "dossier" / "rapport.json"

    code = main(["--input-dir", str(FIXTURES_DIR), "--output-json", str(output_json)])

    assert code == 0
    assert output_json.exists()


def test_main_output_dir_ecrit_json_et_markdown_horodates(tmp_path):
    code = main(["--input-dir", str(FIXTURES_DIR), "--output-dir", str(tmp_path)])

    assert code == 0
    json_files = list(tmp_path.glob("audit_groupe_*.json"))
    md_files = list(tmp_path.glob("audit_groupe_*.md"))
    assert len(json_files) == 1
    assert len(md_files) == 1


def test_main_output_dir_incompatible_avec_output_json(tmp_path):
    code = main([
        "--input-dir", str(FIXTURES_DIR),
        "--output-dir", str(tmp_path),
        "--output-json", str(tmp_path / "rapport.json"),
    ])

    assert code == 1
    assert list(tmp_path.glob("*.json")) == []
