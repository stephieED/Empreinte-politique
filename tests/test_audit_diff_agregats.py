"""Tests du périmètre étendu d'`audit_diff_profils.py` (#470).

Le contrôle de perte branché par #460 avant le commit de données avait deux
angles morts, et les deux ont laissé passer une perte réelle **alors qu'il
tournait** :

  1. il ne regardait que `pivot_data/profiles` — jamais `groupes/`, `partis/`,
     `gouvernements/`, ni les index partagés `scrutins.json` et
     `amendements/`. La cohésion de vote du groupe SOC-16 est tombée de 814 à
     0 sans un mot : un **dénominateur publié devenu faux** (AGENTS.md §2.7) ;
  2. il ne comparait que des longueurs de listes — `parti` est passé de
     renseigné à `null` sur trois profils sans que rien ne le signale.

Ces tests ne partent pas d'exemples inventés : ils rejouent les deux pertes,
extraites de l'historique git en **fixtures figées**
(`tests/fixtures/audit_diff_pertes_reelles/`, provenance dans `meta.fixture`).
Vérifier qu'un contrôle attrape ce qu'il a réellement laissé passer est la
seule preuve qui vaille — et la fixture évite de lire le corpus vivant, absent
du disque en CI (#473).
"""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from audit_diff_profils import (  # noqa: E402
    COLLECTION_GROUPES,
    COLLECTION_INDEX_AMENDEMENTS,
    COLLECTION_INDEX_SCRUTINS,
    COLLECTION_PROFILS,
    _resume_scalaire,
    comparer,
    comparer_tout,
    generate_markdown_report,
    lire_collection_disque,
    lire_collection_git,
    relever,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "audit_diff_pertes_reelles"


def _releve_brut(listes=None, scalaires=None, lu=True) -> dict:
    return {"listes": listes or {}, "scalaires": scalaires or {}, "lu": lu}


def _paire(avant: str, apres: str, collection):
    return (lire_collection_disque(FIXTURES / avant, collection),
            lire_collection_disque(FIXTURES / apres, collection))


def test_les_fixtures_declarent_leur_provenance():
    """Une fixture sans provenance est une donnée inventée dans six mois."""
    fichiers = sorted(FIXTURES.rglob("*.json"))
    assert len(fichiers) == 10
    for chemin in fichiers:
        fixture = json.loads(chemin.read_text(encoding="utf-8"))["meta"]["fixture"]
        assert fixture["source"].startswith("pivot_data/"), chemin
        assert len(fixture["ref"]) == 40, chemin
        assert fixture["reduction"], chemin


# ---------------------------------------------------------------------------
# Perte n°1 — la cohésion de vote de SOC-16, 814 → 0
# ---------------------------------------------------------------------------

def test_la_cohesion_de_vote_perdue_par_soc16_est_detectee():
    """Le cas de #470. Entre `25f7bc7` et `a125e9e`, 24 `mandat_electif` ont
    disparu ; sans mandat électif aucun membre n'est éligible à la date d'un
    scrutin, donc aucun scrutin n'est comptable et `cohesion_votes` tombe à
    zéro. Ce n'est pas une fiche incomplète, c'est un **dénominateur publié
    devenu faux** (AGENTS.md §2.7)."""
    avant, apres = _paire("groupes_avant", "groupes_apres", COLLECTION_GROUPES)
    rapport = comparer(avant, apres, COLLECTION_GROUPES)

    pertes = {(p["fichier"], p["champ"]): (p["avant"], p["apres"])
              for p in rapport["pertes_sur_champs_stables"]}
    assert pertes[("groupe-AN-SOC-16.json", "cohesion_votes")] == (814, 0)
    assert pertes[("groupe-AN-SOC-16.json", "mandats_agreges")] == (44, 23)
    assert pertes[("groupe-AN-SOC-16.json", "tags_thematiques_agreges")] == (179, 0)
    assert rapport["bloquant"]


def test_la_perte_de_ren16_du_meme_run_est_detectee():
    """REN-16 était touché par le même run : `mandats_agreges` 1 032 → 646."""
    avant, apres = _paire("groupes_avant", "groupes_apres", COLLECTION_GROUPES)
    rapport = comparer(avant, apres, COLLECTION_GROUPES)

    pertes = {(p["fichier"], p["champ"]): (p["avant"], p["apres"])
              for p in rapport["pertes_sur_champs_stables"]}
    assert pertes[("groupe-AN-REN-16.json", "mandats_agreges")] == (1032, 646)


def test_le_perimetre_d_avant_470_etait_aveugle_a_la_perte_soc16():
    """La preuve du trou. Les champs surveillés jusqu'ici — `votes`, `mandats`,
    `textes_portes`, `interventions` — n'existent pas dans un fichier de
    groupe : appliquer le périmètre des profils aux groupes ne relève rien,
    quelle que soit l'ampleur de la perte."""
    avant, apres = _paire("groupes_avant", "groupes_apres", COLLECTION_PROFILS)
    rapport = comparer(avant, apres, COLLECTION_PROFILS)

    assert not rapport["pertes_sur_champs_stables"]
    assert not rapport["bloquant"]


def test_un_changement_de_valeur_scalaire_ne_bloque_pas():
    """Sur ce même run, `periode.debut` de SOC-16 passe de `2022-06-22` à
    `2024-07-07`. Un changement de valeur est relevé — il mérite un regard —
    mais ne bloque pas."""
    avant, apres = _paire("groupes_avant", "groupes_apres", COLLECTION_GROUPES)
    rapport = comparer(avant, apres, COLLECTION_GROUPES)

    evolutions = {(e["fichier"], e["champ"]): (e["avant"], e["apres"])
                  for e in rapport["evolutions_scalaires"]}
    assert evolutions[("groupe-AN-SOC-16.json", "periode.debut")] == (
        "2022-06-22", "2024-07-07")
    assert not rapport["pertes_scalaires"], (
        "un changement de valeur n'est pas une régression vers null"
    )


# ---------------------------------------------------------------------------
# Perte n°2 — `parti` renseigné → null sur trois profils
# ---------------------------------------------------------------------------

def test_la_perte_du_parti_sur_trois_profils_est_detectee():
    """L'autre cas de #470. Entre `e4d71cf` et `ffa24ec`, `parti` est passé de
    renseigné à `null` sur trois candidats déclarés, à travers deux
    restaurations et une relecture. L'UI ne le montrait pas non plus :
    `pivotAdapter` retombe sur `manifestEntry.parti`, issu de
    `candidats.json`. La donnée publiée était fausse, l'affichage restait
    juste — le pire cas pour être repéré."""
    avant, apres = _paire("profils_avant", "profils_apres", COLLECTION_PROFILS)
    rapport = comparer(avant, apres, COLLECTION_PROFILS)

    perdus = {(p["fichier"], p["champ"]): p["avant"]
              for p in rapport["pertes_scalaires"]}
    assert perdus[("edouard-philippe.pivot.json", "parti")] == "Horizons"
    assert perdus[("jean-luc-melenchon.pivot.json", "parti")] == \
        "La France Insoumise (LFI)"
    assert perdus[("laurent-wauquiez.pivot.json", "parti")] == \
        "Les Républicains (LR)"
    assert rapport["bloquant"]


def test_ce_run_ne_perdait_aucune_liste_et_passait_donc_inapercu():
    """Pourquoi le contrôle s'est tu : sur ce run **toutes** les listes ne font
    que croître — `jean-luc-melenchon` regagne 1 016 votes et 18 721
    amendements, `edouard-philippe` 50 interventions. Un contrôle qui ne
    compare que des longueurs de listes voyait un run exemplaire."""
    avant, apres = _paire("profils_avant", "profils_apres", COLLECTION_PROFILS)
    rapport = comparer(avant, apres, COLLECTION_PROFILS)

    assert not rapport["pertes"], (
        "aucune liste ne baisse : c'est exactement ce qui a rendu la perte "
        "invisible"
    )
    assert rapport["gains"]
    assert rapport["bloquant"], "et pourtant le run doit être bloqué"


def test_le_rapport_nomme_les_scalaires_perdus():
    """Un verdict sans le détail obligerait à rejouer le contrôle à la main."""
    avant, apres = _paire("profils_avant", "profils_apres", COLLECTION_PROFILS)
    md = generate_markdown_report(comparer(avant, apres, COLLECTION_PROFILS),
                                  "e4d71cf")
    assert "parti" in md
    assert "Horizons" in md
    assert "renseigné" in md


# ---------------------------------------------------------------------------
# Ce qui compte comme « renseigné »
# ---------------------------------------------------------------------------

def test_zero_et_faux_sont_des_valeurs_renseignees():
    """Règle AGENTS.md §2.5 lue à l'envers : `0` est un fait mesuré, pas une
    absence. Un contrôle qui testerait la vérité plutôt que `is None`
    signalerait une perte à chaque compteur retombé à zéro."""
    assert _resume_scalaire(0) == 0
    assert _resume_scalaire(False) is False
    assert _resume_scalaire(0.0) == 0.0


def test_chaine_vide_et_conteneur_vide_valent_non_renseigne():
    """La convention du dépôt est que manquant s'écrit `null` : un `""` qui
    remplace un nom est une perte déguisée, pas une valeur."""
    assert _resume_scalaire("") is None
    assert _resume_scalaire("   ") is None
    assert _resume_scalaire({}) is None
    assert _resume_scalaire([]) is None
    assert _resume_scalaire({"a": 1}) == "<renseigné>"


def test_un_scalaire_qui_apparait_est_un_gain_pas_un_constat():
    """`premier_ministre` est passé de `null` à renseigné sur trois
    gouvernements (run `d96799c`). L'inverse du cas bloquant, et il ne doit
    produire aucun bruit."""
    rapport = comparer({"a.json": _releve_brut(scalaires={"parti": None})},
                       {"a.json": _releve_brut(scalaires={"parti": "LR"})},
                       COLLECTION_PROFILS)
    assert not rapport["pertes_scalaires"]
    assert not rapport["evolutions_scalaires"]
    assert not rapport["bloquant"]


def test_le_chemin_pointe_traverse_les_blocs():
    """`meta.provenance` vit sous `meta`, pas à la racine."""
    releve = relever({"meta": {"provenance": "roster_groupe"}}, COLLECTION_PROFILS)
    assert releve["scalaires"]["meta.provenance"] == "roster_groupe"
    assert releve["scalaires"]["parti"] is None


def test_un_chemin_pointe_qui_casse_vaut_non_renseigne():
    """`meta` absent ne doit pas faire exploser le contrôle sur un document
    malformé — il doit le compter comme non renseigné et continuer."""
    releve = relever({"nom": "X"}, COLLECTION_PROFILS)
    assert releve["scalaires"]["meta.provenance"] is None


# ---------------------------------------------------------------------------
# Index partagés (#431, #432) — et le dimensionnement
# ---------------------------------------------------------------------------

def test_index_amendements_compte_les_entrees_distinctes(tmp_path):
    """`amendements` est un **dict** indexé par `amendement_id`, pas une liste :
    le nombre d'entrées distinctes est `len()` du dict."""
    (tmp_path / "17.json").write_text(json.dumps({
        "schema_version": "amendements-v1", "legislature": "17",
        "amendements": {"an:A1": {}, "an:A2": {}, "an:A3": {}},
    }), encoding="utf-8")

    releve = lire_collection_disque(tmp_path, COLLECTION_INDEX_AMENDEMENTS)

    assert releve["17.json"]["listes"]["amendements"] == 3


def test_baisse_d_un_index_est_signalee_sans_bloquer():
    """Arbitrage explicite (#470) : une baisse d'entrées distinctes serait
    grave, mais elle est aussi le résultat attendu d'une correction de clé
    (#431, #432). Or ces compteurs sont des totaux de corpus : les rendre
    bloquants forcerait l'opérateur à relancer avec `--tolerer-pertes`, qui
    désarmerait du même coup les contrôles précis par profil et par groupe.
    Bloquer sur le compteur le plus grossier pour faire taire les plus fins
    serait le pire des échanges."""
    rapport = comparer(
        {"17.json": _releve_brut(listes={"amendements": 34689})},
        {"17.json": _releve_brut(listes={"amendements": 12000})},
        COLLECTION_INDEX_AMENDEMENTS)

    assert rapport["pertes"], "la baisse doit être visible dans le rapport"
    assert not rapport["bloquant"], "mais elle ne doit pas annuler le commit"


def test_disparition_d_un_fichier_d_index_bloque():
    """La disparition, elle, n'a aucune explication légitime : « an uncommitted
    index leaves every mapping pointing at nothing, silently » (AGENTS.md §3)."""
    rapport = comparer({"17.json": _releve_brut(listes={"amendements": 34689})},
                       {}, COLLECTION_INDEX_AMENDEMENTS)

    assert rapport["bloquant"]
    assert rapport["pertes_sur_champs_stables"][0]["champ"] == "(fichier entier)"


def test_les_cosignatures_ne_sont_jamais_ouvertes(tmp_path):
    """Dimensionnement (#470) : `15.cosignatures.json` coûte à lui seul 222 Mio
    de RSS à parser, plus que tout le reste du contrôle réuni, et aucun
    consommateur ne le lit (AGENTS.md §3). Il est listé, jamais ouvert — un
    contenu illisible ne doit donc rien changer.

    Le motif d'exclusion est négatif et non positif : `fnmatch` laisse `*`
    traverser le point, si bien qu'un `[0-9]*.json` attraperait aussi
    `14.cosignatures.json`."""
    (tmp_path / "17.json").write_text(
        json.dumps({"amendements": {"an:A1": {}}}), encoding="utf-8")
    (tmp_path / "17.cosignatures.json").write_text(
        "ceci n'est pas du JSON", encoding="utf-8")

    releve = lire_collection_disque(tmp_path, COLLECTION_INDEX_AMENDEMENTS)

    assert releve["17.cosignatures.json"]["lu"] is False
    assert releve["17.json"]["lu"] is True


def test_la_disparition_dun_cosignatures_reste_une_perte():
    """Le cas catastrophique — la suppression du fichier — reste couvert, et
    gratuitement : il se lit dans le listing, pas dans le contenu."""
    avant = {"17.json": _releve_brut(listes={"amendements": 1}),
             "17.cosignatures.json": _releve_brut(lu=False)}
    apres = {"17.json": _releve_brut(listes={"amendements": 1})}

    rapport = comparer(avant, apres, COLLECTION_INDEX_AMENDEMENTS)

    assert rapport["bloquant"]
    assert [p["fichier"] for p in rapport["pertes_sur_champs_stables"]] == \
        ["17.cosignatures.json"]


def test_index_scrutins_ne_lit_que_son_fichier(tmp_path):
    """`scrutins.json` vit à la racine de `pivot_data/`, aux côtés des
    répertoires : le motif doit écarter tout le reste."""
    (tmp_path / "scrutins.json").write_text(
        json.dumps({"schema_version": "scrutins-v1",
                    "scrutins": [{"id": 1}, {"id": 2}]}), encoding="utf-8")
    (tmp_path / "autre.json").write_text(
        json.dumps({"scrutins": []}), encoding="utf-8")

    releve = lire_collection_disque(tmp_path, COLLECTION_INDEX_SCRUTINS)

    assert set(releve) == {"scrutins.json"}
    assert releve["scrutins.json"]["listes"]["scrutins"] == 2


# ---------------------------------------------------------------------------
# Collections absentes — ne jamais inventer un point de comparaison
# ---------------------------------------------------------------------------

def test_collection_absente_des_deux_cotes_est_ignoree():
    """Un répertoire qui n'existe ni avant ni après n'est pas une perte : c'est
    une absence de point de comparaison. L'inventer serait une valeur par
    défaut sur une donnée non résolue (AGENTS.md §2.5)."""
    rapport = comparer_tout([(COLLECTION_GROUPES, None, None)])

    assert rapport["collections_ignorees"] == ["groupes"]
    assert not rapport["bloquant"]


def test_collection_presente_avant_et_absente_apres_est_une_perte_totale():
    avant = {"groupe-AN-SOC-16.json": _releve_brut(listes={"cohesion_votes": 814})}

    rapport = comparer_tout([(COLLECTION_GROUPES, avant, None)])

    assert rapport["bloquant"]
    assert rapport["collections"][0]["absente_apres"] is True


def test_collection_absente_de_la_reference_ne_produit_que_des_gains():
    apres = {"groupe-AN-SOC-16.json": _releve_brut(listes={"cohesion_votes": 814})}

    rapport = comparer_tout([(COLLECTION_GROUPES, None, apres)])

    assert not rapport["bloquant"]
    assert rapport["collections"][0]["absente_avant"] is True


def test_lecture_disque_dun_repertoire_absent_ne_leve_pas(tmp_path):
    assert lire_collection_disque(tmp_path / "nexiste-pas", COLLECTION_GROUPES) is None


# ---------------------------------------------------------------------------
# Lecture git des agrégats
# ---------------------------------------------------------------------------

def _depot(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    return tmp_path


def _committer(depot: Path, message: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=depot, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=depot, check=True)


def test_lecture_git_dun_chemin_absent_est_toleree_hors_profils(tmp_path, monkeypatch):
    """Sur les agrégats, un chemin absent de la référence n'est pas une erreur
    d'invocation : le répertoire peut ne pas avoir encore existé. Sur les
    profils, si — c'est là que `--ref-dir` se trompe."""
    depot = _depot(tmp_path)
    (depot / "vide.txt").write_text("x", encoding="utf-8")
    _committer(depot, "init")
    monkeypatch.chdir(depot)

    assert lire_collection_git("HEAD", "pivot_data/groupes", COLLECTION_GROUPES) is None


def test_lecture_git_releve_un_agregat(tmp_path, monkeypatch):
    """La lecture en flux du `--batch` sert toutes les collections, pas
    seulement les profils : le préfixe de chemin doit suivre."""
    depot = _depot(tmp_path)
    groupes = depot / "pivot_data" / "groupes"
    groupes.mkdir(parents=True)
    (groupes / "groupe-AN-SOC-16.json").write_text(json.dumps({
        "groupe_id": "AN:SOC", "cohesion_votes": [1, 2, 3], "membres": [1],
        "meta": {"couverture_roster": {"roster_total": 62}},
    }), encoding="utf-8")
    _committer(depot, "groupes")
    monkeypatch.chdir(depot)

    releve = lire_collection_git("HEAD", "pivot_data/groupes", COLLECTION_GROUPES)

    assert releve["groupe-AN-SOC-16.json"]["listes"]["cohesion_votes"] == 3
    assert releve["groupe-AN-SOC-16.json"]["scalaires"]["groupe_id"] == "AN:SOC"
    assert releve["groupe-AN-SOC-16.json"]["scalaires"][
        "meta.couverture_roster.roster_total"] == 62


def test_lecture_git_de_lindex_scrutins_a_la_racine(tmp_path, monkeypatch):
    """`scrutins.json` n'est pas dans un sous-répertoire : le chemin de la
    collection est la racine `pivot_data` elle-même, et le préfixe envoyé au
    `--batch` doit rester correct."""
    depot = _depot(tmp_path)
    pivot = depot / "pivot_data"
    (pivot / "groupes").mkdir(parents=True)
    (pivot / "scrutins.json").write_text(
        json.dumps({"schema_version": "scrutins-v1", "scrutins": [1, 2, 3, 4]}),
        encoding="utf-8")
    _committer(depot, "index")
    monkeypatch.chdir(depot)

    releve = lire_collection_git("HEAD", "pivot_data", COLLECTION_INDEX_SCRUTINS)

    assert set(releve) == {"scrutins.json"}
    assert releve["scrutins.json"]["listes"]["scrutins"] == 4


def test_lecture_git_ne_demande_pas_les_cosignatures(tmp_path, monkeypatch):
    """Le blob des cosignatures n'est pas seulement écarté du parsing : il
    n'est jamais demandé au `--batch`, donc jamais rapatrié en mémoire. Un
    blob illisible le prouve — s'il était lu, la lecture se
    désynchroniserait."""
    depot = _depot(tmp_path)
    rep = depot / "pivot_data" / "amendements"
    rep.mkdir(parents=True)
    (rep / "17.json").write_text(
        json.dumps({"amendements": {"an:A1": {}, "an:A2": {}}}), encoding="utf-8")
    (rep / "17.cosignatures.json").write_text("pas du JSON", encoding="utf-8")
    _committer(depot, "index")
    monkeypatch.chdir(depot)

    releve = lire_collection_git("HEAD", "pivot_data/amendements",
                                 COLLECTION_INDEX_AMENDEMENTS)

    assert releve["17.json"]["listes"]["amendements"] == 2
    assert releve["17.cosignatures.json"]["lu"] is False


# ---------------------------------------------------------------------------
# Le verdict global
# ---------------------------------------------------------------------------

def test_une_seule_collection_en_perte_bloque_le_tout():
    """Le contrôle décide si un commit de données part : il suffit qu'une
    couche ait perdu."""
    sain = {"a.json": _releve_brut(listes={"votes": 10})}
    rapport = comparer_tout([
        (COLLECTION_PROFILS, sain, sain),
        (COLLECTION_GROUPES,
         {"g.json": _releve_brut(listes={"cohesion_votes": 814})},
         {"g.json": _releve_brut(listes={"cohesion_votes": 0})}),
    ])

    assert rapport["bloquant"]
    assert rapport["nb_pertes_bloquantes"] == 1


def test_le_rapport_global_enonce_son_hors_perimetre():
    """Un périmètre tacite se croit complet. Celui-ci se dit — et c'est la
    seule façon qu'il se rediscute."""
    sain = {"a.json": _releve_brut(listes={"votes": 5})}
    md = generate_markdown_report(
        comparer_tout([(COLLECTION_PROFILS, sain, sain)]), "origin/main")

    assert "Hors périmètre de ce contrôle" in md
    assert "cosignatures" in md
    assert "intégrité référentielle" in md


def test_les_six_couches_et_les_deux_index_sont_couverts():
    """Garde-fou du périmètre lui-même : c'est son rétrécissement silencieux
    qui a coûté #470.

    `lignees` y est entrée avec #836. Un répertoire de `pivot_data/` publié
    mais absent de ce périmètre est un répertoire dont la disparition ne
    bloque rien — et l'interface ne publie QUE ces fiches-là.
    """
    from audit_diff_profils import COLLECTIONS_AGREGATS

    noms = {COLLECTION_PROFILS.nom} | {c.nom for c in COLLECTIONS_AGREGATS}
    assert noms == {"profiles", "groupes", "lignees", "partis", "gouvernements",
                    "index scrutins", "index amendements"}
    assert "cohesion_votes" in COLLECTION_GROUPES.listes_stables
    assert "parti" in COLLECTION_PROFILS.scalaires
    assert "tags_thematiques" in COLLECTION_PROFILS.listes_stables, (
        "champ publié, passé de 647 à 0 dans le run de #460, et qui n'était "
        "surveillé nulle part"
    )
