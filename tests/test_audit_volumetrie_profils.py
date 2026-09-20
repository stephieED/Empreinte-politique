"""Tests de `audit_volumetrie_profils.py` (#429)."""

import gzip
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from audit_volumetrie_profils import (
    FENETRE_COMMITS_DONNEES,
    RUNS_RECENTS,
    SEUIL_DEPOT_RECOMMANDE_GO,
    _poids_champ,
    analyser_profil,
    analyser_repertoires,
    compute_fenetre_donnees,
    compute_historique_git,
    compute_leviers,
    compute_projection,
    compute_volumetrie,
    generate_markdown_report,
)


def _ecrire(repertoire: Path, nom: str, profil: dict, indent: int = 2) -> Path:
    chemin = repertoire / nom
    chemin.write_text(json.dumps(profil, ensure_ascii=False, indent=indent), encoding="utf-8")
    return chemin


# ---------------------------------------------------------------------------
# _poids_champ — champs imbriqués
# ---------------------------------------------------------------------------

def test_poids_champ_simple():
    profil = {"votes": [{"a": 1}, {"a": 2}]}
    assert _poids_champ(profil, ("votes",)) > 0
    assert _poids_champ(profil, ("absent",)) == 0


def test_poids_champ_imbrique_ne_compte_que_le_sous_champ():
    """`co_signataires` vit DANS chaque amendement : mesurer son poids demande
    de sommer le sous-champ, pas la liste entière."""
    profil = {"amendements": [
        {"numero": "1", "co_signataires": ["an:PA1", "an:PA2"]},
        {"numero": "2", "co_signataires": []},
    ]}
    imbrique = _poids_champ(profil, ("amendements", "co_signataires"))
    entier = _poids_champ(profil, ("amendements",))
    assert 0 < imbrique < entier


def test_poids_champ_tolere_les_entrees_non_dict():
    profil = {"amendements": ["pas un dict", {"co_signataires": ["an:PA1"]}]}
    assert _poids_champ(profil, ("amendements", "co_signataires")) > 0


# ---------------------------------------------------------------------------
# analyser_profil
# ---------------------------------------------------------------------------

def test_analyser_profil_mesure_les_trois_formes(tmp_path):
    chemin = _ecrire(tmp_path, "p.json", {"votes": [{"x": "é" * 500}]})
    mesure = analyser_profil(chemin)
    assert mesure["octets_compact"] < mesure["octets"], "le compact doit être plus petit"
    assert mesure["octets_gzip"] < mesure["octets_compact"], "gzip doit être plus petit encore"


def test_analyser_profil_json_illisible_retourne_none(tmp_path):
    """Un fichier malformé ne doit jamais interrompre le scan."""
    (tmp_path / "casse.json").write_text("{ pas du json", encoding="utf-8")
    assert analyser_profil(tmp_path / "casse.json") is None


def test_analyser_profil_accents_non_echappes(tmp_path):
    """`ensure_ascii=True` gonflerait chaque accent en `\\uXXXX` et fausserait
    la mesure au profit du compact."""
    chemin = _ecrire(tmp_path, "p.json", {"nom": "é" * 100}, indent=None)
    mesure = analyser_profil(chemin)
    assert mesure["octets_compact"] <= mesure["octets"] + 2


# ---------------------------------------------------------------------------
# compute_volumetrie — extrapolation de l'échantillon
# ---------------------------------------------------------------------------

def test_compute_volumetrie_extrapole_sur_le_total_exact():
    """Les ratios viennent de l'échantillon, mais doivent être rapportés au
    volume RÉEL : rapporter le poids de l'échantillon ne représenterait rien."""
    mesures = [{"fichier": "a.json", "octets": 100, "octets_compact": 60,
                "octets_gzip": 10, "champs": {"votes": 50}}]
    exact = {"nb_profils": 10, "octets_total": 1000, "octets_median": 100,
             "octets_max": 100, "fichier_max": "a.json"}
    vol = compute_volumetrie(mesures, exact)

    assert vol["nb_profils"] == 10
    assert vol["octets_total"] == 1000
    assert vol["extrapole"] is True
    assert vol["octets_compact_total"] == 600, "60 % de 1000, pas 60"
    assert vol["poids_par_champ"]["votes"] == 500


def test_compute_volumetrie_sans_exact_reste_coherent():
    mesures = [{"fichier": "a.json", "octets": 100, "octets_compact": 60,
                "octets_gzip": 10, "champs": {"votes": 50}}]
    vol = compute_volumetrie(mesures)
    assert vol["extrapole"] is False
    assert vol["octets_total"] == 100


def test_compute_volumetrie_liste_vide():
    assert compute_volumetrie([])["nb_profils"] == 0


# ---------------------------------------------------------------------------
# compute_leviers
# ---------------------------------------------------------------------------

def test_compute_leviers_trie_par_gain_decroissant():
    vol = {"octets_total": 1000, "octets_compact_total": 700, "octets_gzip_total": 50,
           "poids_par_champ": {"votes": 100, "amendements": 600}}
    leviers = compute_leviers(vol)
    gains = [l["gain_octets"] for l in leviers]
    assert gains == sorted(gains, reverse=True)


def test_compute_leviers_aucun_ne_declare_de_perte():
    """Garde-fou #429 : tous les leviers proposés doivent DÉPLACER la donnée,
    jamais la supprimer. L'UI n'est pas définitive et la refonte analytics
    (#324) aura besoin de champs aujourd'hui inexploités."""
    vol = {"octets_total": 1000, "octets_compact_total": 700, "octets_gzip_total": 50,
           "poids_par_champ": {"amendements": 600}}
    assert all(l["perte"] is False for l in compute_leviers(vol))


def test_compute_leviers_total_nul():
    assert compute_leviers({"octets_total": 0}) == []


# ---------------------------------------------------------------------------
# compute_projection
# ---------------------------------------------------------------------------

def test_compute_projection_signale_les_deux_seuils():
    vol = {"nb_profils": 100, "octets_total": 1024 ** 3}  # 1 Go pour 100 profils
    proj = compute_projection(vol, cible=752, facteur_duplication=2.0)
    assert proj["go_projetes"] > SEUIL_DEPOT_RECOMMANDE_GO
    assert proj["depasse_seuil_push"] is True
    assert proj["depasse_seuil_depot"] is True


def test_compute_projection_facteur_duplication_agit():
    vol = {"nb_profils": 100, "octets_total": 1024 ** 3}
    seul = compute_projection(vol, 752, 1.0)["go_projetes"]
    double = compute_projection(vol, 752, 2.0)["go_projetes"]
    assert abs(double - 2 * seul) < 0.05


def test_compute_projection_estime_le_seuil_en_profils():
    vol = {"nb_profils": 100, "octets_total": 1024 ** 3}
    proj = compute_projection(vol, 752, 1.0)
    assert proj["profils_avant_seuil_depot"] == 500  # 5 Go / 10 Mo par profil


# ---------------------------------------------------------------------------
# Échantillonnage
# ---------------------------------------------------------------------------

def test_echantillon_couvre_toute_la_distribution(tmp_path):
    """Échantillon pris à intervalle régulier sur les fichiers TRIÉS par taille :
    il doit atteindre le plus gros profil. Un tirage aléatoire pourrait le
    manquer et sous-estimer le poids des gros déposants d'amendements."""
    for i in range(40):
        _ecrire(tmp_path, f"p{i:02d}.json", {"votes": [{"x": "a" * (i * 200 + 10)}]})

    mesures, erreurs, exact = analyser_repertoires([tmp_path], echantillon=8)

    assert exact["nb_profils"] == 40, "le total porte sur TOUS les fichiers"
    assert len(mesures) == 8, "l'analyse profonde ne porte que sur l'échantillon"
    assert not erreurs
    assert max(m["octets"] for m in mesures) == exact["octets_max"]


def test_echantillon_est_deterministe(tmp_path):
    for i in range(30):
        _ecrire(tmp_path, f"p{i:02d}.json", {"votes": [{"x": "a" * (i * 100 + 10)}]})
    premier = [m["fichier"] for m in analyser_repertoires([tmp_path], 6)[0]]
    second = [m["fichier"] for m in analyser_repertoires([tmp_path], 6)[0]]
    assert premier == second


def test_echantillon_zero_analyse_tout(tmp_path):
    for i in range(5):
        _ecrire(tmp_path, f"p{i}.json", {"votes": []})
    mesures, _err, exact = analyser_repertoires([tmp_path], echantillon=0)
    assert len(mesures) == exact["nb_profils"] == 5


def test_repertoire_absent_est_ignore(tmp_path):
    _ecrire(tmp_path, "p.json", {"votes": []})
    mesures, _err, exact = analyser_repertoires([tmp_path, tmp_path / "nexiste-pas"], 0)
    assert exact["nb_profils"] == 1 and len(mesures) == 1


# ---------------------------------------------------------------------------
# Rapport
# ---------------------------------------------------------------------------

def test_rapport_markdown_mentionne_le_biais_dechantillon(tmp_path):
    vol = compute_volumetrie(
        [{"fichier": "a.json", "octets": 100, "octets_compact": 60,
          "octets_gzip": 10, "champs": {"amendements": 50}}],
        {"nb_profils": 10, "octets_total": 1000, "octets_median": 100,
         "octets_max": 100, "fichier_max": "a.json"},
    )
    rapport = {"volumetrie": vol, "leviers": compute_leviers(vol),
               "projection": compute_projection(vol, 752, 2.0), "erreurs_lecture": []}
    md = generate_markdown_report(rapport)
    assert "biaisé" in md, "le biais d'échantillon doit être dit, pas supposé connu"
    assert "sans perte" in md


def test_rapport_markdown_sans_profil():
    assert "Aucun profil" in generate_markdown_report({"volumetrie": {"nb_profils": 0}})


# ---------------------------------------------------------------------------
# Avertissement de représentativité (conditionnel)
# ---------------------------------------------------------------------------

def _rapport(nb_profils: int, cible: int) -> dict:
    vol = compute_volumetrie(
        [{"fichier": "a.json", "octets": 100, "octets_compact": 60,
          "octets_gzip": 10, "champs": {"amendements": 50}}],
        {"nb_profils": nb_profils, "octets_total": nb_profils * 100,
         "octets_median": 100, "octets_max": 100, "fichier_max": "a.json"},
    )
    return {"volumetrie": vol, "leviers": compute_leviers(vol),
            "projection": compute_projection(vol, cible, 1.0), "erreurs_lecture": []}


def test_avertissement_absent_quand_la_population_est_complete():
    """Douter d'un chiffre mesuré est aussi trompeur qu'omettre la réserve sur
    un chiffre extrapolé : l'avertissement doit disparaître à population
    complète."""
    md = generate_markdown_report(_rapport(nb_profils=752, cible=752))
    assert "complète" in md
    assert "biaisé" not in md


def test_avertissement_present_quand_la_population_est_partielle():
    md = generate_markdown_report(_rapport(nb_profils=40, cible=752))
    assert "biaisé" in md


def test_entete_distingue_population_et_echantillon():
    """La population porte le total exact, l'échantillon les seuls ratios :
    confondre les deux ferait passer une mesure pour une extrapolation."""
    md = generate_markdown_report(_rapport(nb_profils=752, cible=752))
    assert "Population : **752 profils**" in md
    assert "Ratios" in md and "**1 profils**" in md


# ---------------------------------------------------------------------------
# compute_historique_git — la mesure comparable aux seuils GitHub
#
# Ce script comparait un total d'ARBRE DE TRAVAIL aux seuils GitHub, qui portent
# sur le DÉPÔT. L'écart n'est pas marginal : mesuré le 19/08/2026, les profils
# JSON se déltifient d'un facteur 10 à 14 (3 017 Mo d'arbre de travail pour
# 670 Mo de `.git`). Le cadrage de #429 a repris cette erreur telle quelle et
# annonçait une urgence d'un ordre de grandeur au-dessus du réel.
#
# Et surtout : la photo ne grandit qu'avec le nombre de profils, l'historique
# grandit à CHAQUE run. C'est le coût par run qui décide.
# ---------------------------------------------------------------------------

def _init_depot(tmp_path: Path) -> Path:
    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    return tmp_path


def _commit(depot: Path, message: str) -> None:
    import subprocess
    subprocess.run(["git", "add", "-A"], cwd=depot, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=depot, check=True)


def test_historique_git_mesure_chaque_repertoire(tmp_path, monkeypatch):
    depot = _init_depot(tmp_path)
    (depot / "profils").mkdir()
    _ecrire(depot / "profils", "alice.json", {"votes": [{"x": i} for i in range(200)]})
    _commit(depot, "initial")
    monkeypatch.chdir(depot)

    hist = compute_historique_git([Path("profils")])

    assert hist["octets_total"] > 0
    assert hist["par_repertoire"]["profils"] > 0
    assert hist["par_repertoire"]["profils"] <= hist["octets_total"]


def test_historique_git_isole_le_cout_du_dernier_run_de_donnees(tmp_path, monkeypatch):
    """Le coût par run est le chiffre qui décide : il s'ajoute définitivement,
    run après run, alors que la photo ne bouge qu'avec le nombre de profils."""
    depot = _init_depot(tmp_path)
    (depot / "profils").mkdir()
    _ecrire(depot / "profils", "alice.json", {"votes": [{"x": i} for i in range(50)]})
    _commit(depot, "initial")
    _ecrire(depot / "profils", "bob.json", {"votes": [{"y": i} for i in range(500)]})
    _commit(depot, "chore: mise à jour automatique des données (2026-08-19)")
    monkeypatch.chdir(depot)

    run = compute_historique_git([Path("profils")])["dernier_run"]

    assert run is not None
    assert len(run["sha"]) == 7
    assert run["octets"] > 0
    assert run["par_repertoire"]["profils"] > 0


def test_rapport_dit_que_le_total_du_depot_est_un_majorant():
    """`rev-list --disk-usage` additionne la représentation actuelle de chaque
    objet : sur des packs mal compactés il surestime (409 Mo annoncés contre
    295 Mo après `gc --prune=now`, mesuré le 20/08/2026, #434). Le rapport
    désigne ce total comme « la mesure à comparer aux seuils GitHub » — sans la
    réserve, il rejoue la confusion qui a fait recadrer #429 quatre fois, à
    l'endroit précis où le chiffre se lit."""
    rapport = dict(_rapport(nb_profils=752, cible=752))
    rapport["historique_git"] = {"octets_total": 409 * 1024 ** 2,
                                 "par_repertoire": {}, "dernier_run": None}

    md = generate_markdown_report(rapport)

    assert "majorant" in md
    assert "gc --prune=now" in md


def test_historique_git_sans_commit_de_donnees_ne_rend_pas_de_run(tmp_path, monkeypatch):
    depot = _init_depot(tmp_path)
    (depot / "profils").mkdir()
    _ecrire(depot / "profils", "alice.json", {"votes": []})
    _commit(depot, "initial")
    monkeypatch.chdir(depot)

    assert compute_historique_git([Path("profils")])["dernier_run"] is None


def test_historique_git_hors_depot_rend_un_dict_vide(tmp_path, monkeypatch):
    """La volumétrie de l'arbre de travail reste utile seule : elle ne doit pas
    dépendre de la présence d'un dépôt git."""
    monkeypatch.chdir(tmp_path)
    assert compute_historique_git([Path("profils")]) == {}


def test_rapport_signale_que_la_projection_porte_sur_l_arbre_de_travail():
    """La confusion coûte cher : #429 a été cadrée sur une projection d'arbre de
    travail comparée à un seuil de dépôt."""
    rapport = {
        "volumetrie": {
            "nb_profils": 2, "octets_total": 2_000_000, "octets_median": 1_000_000,
            "octets_moyen": 1_000_000, "octets_max": 1_000_000, "fichier_max": "a.json",
        },
        "leviers": [],
        "projection": compute_projection(
            {"nb_profils": 2, "octets_total": 2_000_000}, cible=752, facteur_duplication=1.0
        ),
        "historique_git": {},
    }
    markdown = generate_markdown_report(rapport)

    assert "arbre de travail" in markdown
    assert "pas la taille du dépôt" in markdown
    # Le piège du comptage en fichiers, qui m'a fait produire une mesure fausse.
    assert "compte des **fichiers**" in markdown


def test_rapport_affiche_l_historique_quand_il_est_mesure():
    rapport = {
        "volumetrie": {
            "nb_profils": 1, "octets_total": 1000, "octets_median": 1000,
            "octets_moyen": 1000, "octets_max": 1000, "fichier_max": "a.json",
        },
        "leviers": [],
        "projection": {},
        "historique_git": {
            "octets_total": 350 * 1024 ** 2,
            "par_repertoire": {"pivot_data/profiles": 109 * 1024 ** 2},
            "dernier_run": {"sha": "a125e9e", "octets": 49 * 1024 ** 2, "par_repertoire": {}},
        },
    }
    markdown = generate_markdown_report(rapport)

    assert "Historique git" in markdown
    assert "a125e9e" in markdown
    assert "définitivement" in markdown


def test_rapport_sans_historique_n_affiche_pas_la_section():
    rapport = {
        "volumetrie": {
            "nb_profils": 1, "octets_total": 1000, "octets_median": 1000,
            "octets_moyen": 1000, "octets_max": 1000, "fichier_max": "a.json",
        },
        "leviers": [], "projection": {}, "historique_git": {},
    }
    assert "Historique git" not in generate_markdown_report(rapport)


# ---------------------------------------------------------------------------
# compute_fenetre_donnees — la fenêtre glissante de #434
# ---------------------------------------------------------------------------

def _commits(couts: list[int]) -> list[dict]:
    """Commits de données du plus récent au plus ancien, coûts en octets."""
    return [
        {"sha": f"sha{i:04d}", "date": "2026-08-20T00:00:00Z", "octets": c}
        for i, c in enumerate(couts)
    ]


def test_fenetre_non_contraignante_quand_moins_de_commits_que_la_fenetre():
    """Le cas d'aujourd'hui : 23 commits de données pour une fenêtre de 30.
    Rien à borner — et surtout, aucune réécriture d'historique à mener."""
    resultat = compute_fenetre_donnees(_commits([10] * 23), fenetre=30)

    assert resultat["contraignante"] is False
    assert resultat["sha_coupure"] is None
    assert resultat["majorant_gain_octets"] == 0
    assert resultat["nb_commits_donnees"] == 23


def test_fenetre_contraignante_designe_la_coupure_et_majore_le_gain():
    """Sens inverse : plus de commits que la fenêtre. La coupure est le
    (fenêtre+1)-ième commit, et le majorant somme ce qui est au-delà."""
    resultat = compute_fenetre_donnees(_commits([5, 7, 11, 13, 17]), fenetre=2)

    assert resultat["contraignante"] is True
    assert resultat["sha_coupure"] == "sha0002"
    assert resultat["majorant_gain_octets"] == 11 + 13 + 17


def test_fenetre_exactement_a_la_limite_n_est_pas_contraignante():
    """Frontière : `fenetre` commits tiennent dans une fenêtre de `fenetre`.
    C'est `>` et non `>=` qui décide — une erreur d'un cran ici déclencherait
    une réécriture d'historique pour zéro gain."""
    assert compute_fenetre_donnees(_commits([1] * 10), fenetre=10)["contraignante"] is False
    assert compute_fenetre_donnees(_commits([1] * 11), fenetre=10)["contraignante"] is True


def test_fenetre_rend_la_distribution_pas_seulement_la_moyenne():
    """C'est la distribution qui dimensionne : les runs mesurés vont de 0,2 à
    53,5 Mo pour une médiane de 12,6. Une moyenne seule décrirait un run
    inexistant."""
    couts = compute_fenetre_donnees(_commits([10, 20, 30, 40, 900]))["couts"]

    assert couts["min"] == 10
    assert couts["max"] == 900
    assert couts["median"] == 30
    assert couts["moyen"] == 200
    assert couts["max"] / couts["median"] == 30


def test_fenetre_sans_commit_ne_plante_pas():
    """Hors dépôt git, `collecte_commits_donnees` rend une liste vide : la
    mesure de fenêtre est un complément, elle ne doit jamais faire échouer le
    rapport."""
    resultat = compute_fenetre_donnees([], fenetre=30)

    assert resultat["nb_commits_donnees"] == 0
    assert resultat["contraignante"] is False
    assert resultat["couts"] == {}


def test_fenetre_calcule_le_plafond_quand_le_socle_est_connu():
    """Le plafond est ce que l'option D achète : socle + fenêtre × coût moyen."""
    resultat = compute_fenetre_donnees(
        _commits([100, 200, 300]), fenetre=10, socle_octets=1000
    )
    assert resultat["plafond_octets"] == 1000 + 10 * 200


def test_fenetre_ignore_le_plafond_sans_socle():
    assert "plafond_octets" not in compute_fenetre_donnees(_commits([1, 2]), fenetre=5)


def test_la_fenetre_par_defaut_couvre_une_semaine_a_cadence_de_pointe():
    """Dimensionnement (#434) : 4 commits de données par jour au pic mesuré
    (18 et 19/08/2026), et une semaine sans surveillance. 4 × 7 = 28, arrondi
    à 30. La valeur n'est pas ronde par hasard — elle est choisie pour la
    latence de détection d'un incident."""
    assert FENETRE_COMMITS_DONNEES >= 4 * 7


def test_rapport_affiche_la_fenetre_non_contraignante_sans_alarmer():
    rapport = {
        "volumetrie": {
            "nb_profils": 1, "octets_total": 1000, "octets_median": 1000,
            "octets_moyen": 1000, "octets_max": 1000, "fichier_max": "a.json",
        },
        "leviers": [], "projection": {}, "historique_git": {},
        "fenetre_donnees": compute_fenetre_donnees(_commits([10] * 23), fenetre=30),
    }
    markdown = generate_markdown_report(rapport)

    assert "Fenêtre d'historique de données" in markdown
    assert "n'est pas contraignante" in markdown
    assert "aucune réécriture d'historique" in markdown


def test_rapport_avertit_que_le_majorant_n_est_pas_le_gain():
    """Le piège mesuré : la somme des coûts par run surestime le gain d'un
    facteur 2 à 15. Le rapport doit le dire là où le chiffre se lit."""
    rapport = {
        "volumetrie": {
            "nb_profils": 1, "octets_total": 1000, "octets_median": 1000,
            "octets_moyen": 1000, "octets_max": 1000, "fichier_max": "a.json",
        },
        "leviers": [], "projection": {}, "historique_git": {},
        "fenetre_donnees": compute_fenetre_donnees(_commits([10] * 40), fenetre=30),
    }
    markdown = generate_markdown_report(rapport)

    assert "contraignante" in markdown
    assert "n'est **pas** le gain" in markdown
    assert "repackant un clone" in markdown


def test_rapport_sans_fenetre_n_affiche_pas_la_section():
    rapport = {
        "volumetrie": {
            "nb_profils": 1, "octets_total": 1000, "octets_median": 1000,
            "octets_moyen": 1000, "octets_max": 1000, "fichier_max": "a.json",
        },
        "leviers": [], "projection": {}, "historique_git": {}, "fenetre_donnees": {},
    }
    assert "Fenêtre d'historique" not in generate_markdown_report(rapport)


def test_la_distribution_ignore_les_runs_anterieurs_au_corpus_actuel():
    """Le coût d'un run suit la taille du corpus. Mesuré sur le dépôt réel le
    20/08/2026 : sur les 8 runs récents la médiane vaut 12,6 Mo, sur les 23
    commits de données elle tombe à 2,6 Mo et l'écart min/max grimpe à × 1 790
    — un chiffre qui ne décrit aucun run existant. La distribution porte donc
    sur les `recents` derniers, jamais sur tous."""
    recents = [100] * 8          # runs à corpus courant
    anciens = [1] * 15           # runs d'un corpus 10× plus petit
    resultat = compute_fenetre_donnees(_commits(recents + anciens), fenetre=30, recents=8)

    assert resultat["nb_runs_mesures"] == 8
    assert resultat["couts"]["median"] == 100
    assert resultat["couts"]["min"] == 100      # aucun ancien dans l'échantillon
    # ... alors que tout prendre écraserait la médiane :
    tout = compute_fenetre_donnees(_commits(recents + anciens), fenetre=30, recents=0)
    assert tout["nb_runs_mesures"] == 23
    assert tout["couts"]["median"] == 1


def test_la_distribution_ne_deborde_pas_quand_il_y_a_moins_de_runs():
    """Moins de runs que `recents` : on mesure ce qu'on a, sans extrapoler."""
    resultat = compute_fenetre_donnees(_commits([5, 7, 9]), fenetre=30, recents=RUNS_RECENTS)

    assert resultat["nb_runs_mesures"] == 3
    assert resultat["couts"]["median"] == 7
