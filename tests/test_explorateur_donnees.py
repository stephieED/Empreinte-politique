"""L'explorateur des données : pivot_data et raw_data en tableaux reliés (29/10/2026).

Un dépôt réduit, construit dans `tmp_path` à la forme du corpus (profil pivot,
socle brut et tranche d'amendements, groupe, lignée, gouvernement, scrutins) :
aucun test ne lit le corpus vivant.
"""
from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

import explorateur_donnees as ex  # noqa: E402


def _ecrire(chemin: Path, contenu) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(json.dumps(contenu, ensure_ascii=False), encoding="utf-8")


@pytest.fixture
def depot(tmp_path):
    d = tmp_path / "depot"
    p, b = d / "pivot_data", d / "raw_data"
    _ecrire(p / "profiles" / "marine-le-pen.pivot.json", {
        "id": "marine-le-pen", "nom": "Marine Le Pen", "meta": {"provenance": "candidat_declare"},
        "identite": {"date_naissance": "1968-08-05"},
        "mandats": [{"label": "Députée", "debut": "2017-06-21", "fin": None}],
        "votes": [{"scrutin_id": "an:17:8705", "position": "pour"}],
        "amendements": [{"amendement_id": "A1", "sort": "Rejeté"}]})
    _ecrire(p / "profiles" / "herve-de-lepinau.pivot.json", {
        "id": "herve-de-lepinau", "nom": "Hervé de Lépinau", "meta": {"provenance": "roster_groupe"},
        "mandats": [{"label": "Député"}],
        "votes": [{"scrutin_id": "an:17:8705", "position": "pour"}] * 3,
        "amendements": [{"amendement_id": "A2"}]})
    _ecrire(p / "groupes" / "groupe-AN-RN-17.json", {
        "groupe_id": "AN:RN:17", "groupe_nom": "Rassemblement National", "legislature": "17",
        "membres": [{"membre_id": "herve-de-lepinau", "periodes": [{"debut": "2024-07-19"}]}]})
    _ecrire(p / "lignees" / "lignee-AN-RN.json", {
        "lignee_id": "AN:RN", "lignee_nom": "Rassemblement national",
        "maillons": [{"groupe_id": "AN:RN:17", "legislature": "17"}]})
    _ecrire(p / "gouvernements" / "gouvernement-ATTAL.json", {
        "gouvernement_id": "gouvernement:ATTAL", "nom": "Attal",
        "membres": [{"membre_id": "marine-le-pen", "portefeuille": "exemple"}]})
    _ecrire(p / "scrutins.json", {"scrutins": [{"id": "an:17:8705", "texte": "la proposition de loi…"}]})
    _ecrire(b / "profiles" / "marine-le-pen.json", {
        "slug": "marine-le-pen", "mandats": [{"label": "Députée"}],
        "amendements_partitionnes": {"total": 1, "tranches": [{"legislature": "17", "fichier": "17.json"}]}})
    _ecrire(b / "profiles" / "marine-le-pen" / "17.json", {"amendements": [{"uid": "AMANR5L17", "sort": "Rejeté"}]})
    _ecrire(b / "profiles" / "herve-de-lepinau.json", {"slug": "herve-de-lepinau", "votes": [{"scrutin_id": "x"}]})
    _ecrire(b / "profiles" / "herve-de-lepinau" / "17.json", {"amendements": [{"uid": "AM2"}]})
    _ecrire(b / "candidats.json", {"candidats": [{"slug": "marine-le-pen", "statut": "declare"}]})
    # La forme de `lois_jorf.json` : un dictionnaire indexé dont les valeurs sont des listes.
    _ecrire(b / "lois_jorf.json", {"schema_version": "lois-jorf-v1",
                                   "lois": {str(1600 + i): [["JORFTEXT0000", "1802-05-29"]] for i in range(60)}})
    subprocess.run(["git", "init", "-q", str(d)], check=True)
    subprocess.run(["git", "-C", str(d), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(d), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x"], check=True)
    return d


@pytest.fixture
def base(depot, tmp_path):
    chemin = tmp_path / "donnees.db"
    ex.construire(depot, chemin)
    cx = sqlite3.connect(chemin)
    yield cx
    cx.close()


def _tables(cx):
    return {r[0] for r in cx.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def _liens(cx, table):
    return {(r[3], r[2], r[4]) for r in cx.execute(f'PRAGMA foreign_key_list("{table}")')}


def test_chaque_liste_devient_une_table_reliee_a_son_parent(base):
    assert {"profils", "profils__mandats", "profils__votes", "groupes__membres",
            "groupes__membres__periodes", "lignees__maillons", "gouvernements__membres",
            "brut_profils", "brut_profils__amendements", "brut_candidats__candidats"} <= _tables(base)
    assert ("_parent", "profils", "id") in _liens(base, "profils__mandats")
    assert ("_parent", "groupes__membres", "_id") in _liens(base, "groupes__membres__periodes")


def test_les_identifiants_connus_deviennent_des_liens(base):
    assert ("scrutin_id", "scrutins", "id") in _liens(base, "profils__votes")
    assert ("membre_id", "profils", "id") in _liens(base, "groupes__membres")
    assert ("groupe_id", "groupes", "groupe_id") in _liens(base, "lignees__maillons")
    assert ("brut", "brut_profils", "slug") in _liens(base, "profils")
    assert ("profil", "profils", "id") in _liens(base, "brut_profils")


def test_un_objet_imbrique_est_aplati_en_colonnes(base):
    assert base.execute("SELECT identite_date_naissance FROM profils WHERE id='marine-le-pen'").fetchone() == ("1968-08-05",)


def test_les_listes_lourdes_des_membres_des_groupes_ne_sont_pas_chargees(base):
    assert base.execute("SELECT count(*) FROM profils__votes WHERE _parent='herve-de-lepinau'").fetchone() == (0,)
    assert base.execute("SELECT votes__non_charge FROM profils WHERE id='herve-de-lepinau'").fetchone() == (3,)
    assert base.execute("SELECT count(*) FROM brut_profils__amendements WHERE _parent='herve-de-lepinau'").fetchone() == (0,)
    # …mais leurs mandats, oui, et tout pour une candidate déclarée.
    assert base.execute("SELECT count(*) FROM profils__mandats WHERE _parent='herve-de-lepinau'").fetchone() == (1,)
    assert base.execute("SELECT count(*) FROM brut_profils__amendements WHERE _parent='marine-le-pen'").fetchone() == (1,)


def test_un_grand_dictionnaire_devient_une_table_fille(base):
    assert base.execute("SELECT count(*) FROM brut_lois_jorf__lois").fetchone() == (60,)
    assert base.execute("SELECT _cle, valeur FROM brut_lois_jorf__lois WHERE _cle='1600'").fetchone() == \
        ("1600", '[["JORFTEXT0000", "1802-05-29"]]')


def test_le_document_entier_n_est_garde_que_pour_les_populations_legeres(base):
    cles = {r[0] for r in base.execute("SELECT cle FROM documents")}
    assert {"profil:marine-le-pen", "groupes:AN:RN:17", "lignees:AN:RN", "brut:candidats"} <= cles
    assert "profil:herve-de-lepinau" not in cles


def test_la_base_porte_le_commit_lu_et_ne_se_reconstruit_pas_sans_lui(depot, tmp_path, capsys):
    chemin = tmp_path / "donnees.db"
    assert ex.main(["--depot", str(depot), "--base", str(chemin)]) == 0
    commit = subprocess.run(["git", "-C", str(depot), "rev-parse", "HEAD"], capture_output=True,
                            text=True).stdout.strip()
    assert ex.commit_de_la_base(chemin) == commit
    capsys.readouterr()
    assert ex.main(["--depot", str(depot), "--base", str(chemin), "--si-perimee"]) == 0
    assert "rien à reconstruire" in capsys.readouterr().out


def test_deux_cles_qui_ne_different_que_par_la_casse_gardent_leurs_valeurs(tmp_path):
    """SQLite ne distingue pas `Sur` de `sur` dans un nom de colonne (mesuré le
    29/10/2026 : la construction réelle échouait sur un agrégat de mandats)."""
    base = ex.Base(tmp_path / "b.db")
    base.ajouter("t", {"_id": "1", "Par fonction": 1, "par fonction": 2}, "_id")
    base.fermer()
    cx = sqlite3.connect(tmp_path / "b.db")
    colonnes = [r[1] for r in cx.execute('PRAGMA table_info("t")')]
    assert colonnes == ["_id", "Par fonction", "par fonction (2)"]
    assert cx.execute('SELECT * FROM "t"').fetchone() == ("1", 1, 2)


def test_une_cle_qui_porte_des_guillemets_reste_une_colonne(tmp_path):
    """Clé réelle de `groupe-AN-UMP-14.json` (29/10/2026) : la construction
    échouait sur « duplicate column name »."""
    cle = 'rapporteur sur "la fiscalité des hébergements touristiques"'
    base = ex.Base(tmp_path / "b.db")
    base.ajouter("t", {"_id": "1", cle: 3, "rapporteur sur ": 4}, "_id")
    base.fermer()
    cx = sqlite3.connect(tmp_path / "b.db")
    assert [r[1] for r in cx.execute('PRAGMA table_info("t")')] == ["_id", cle, "rapporteur sur "]
    assert cx.execute('SELECT * FROM "t"').fetchone() == ("1", 3, 4)


def test_le_depot_n_est_pas_touche(depot, tmp_path):
    avant = subprocess.run(["git", "-C", str(depot), "status", "--porcelain"], capture_output=True,
                           text=True).stdout
    ex.construire(depot, tmp_path / "donnees.db")
    apres = subprocess.run(["git", "-C", str(depot), "status", "--porcelain"], capture_output=True,
                           text=True).stdout
    assert avant == apres == ""


def test_la_commande_ne_lance_le_serveur_que_sur_cette_machine():
    script = (RACINE / "scripts" / "explorateur.sh").read_text(encoding="utf-8")
    assert "--host 127.0.0.1" in script
    assert ".cache/explorateur" in script
