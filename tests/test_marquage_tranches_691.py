"""L'écriture marque les tranches closes, et le `nombre` vient de l'archive (#691, lot 3b).

C'est le lot qui **cesse d'écrire**. `partitionner` marque en `derivee` toute
tranche de législature close que l'archive couvre pour cet acteur ; elle sort du
dictionnaire rendu, donc `ecrire_profil_brut` la supprime — par le nettoyage des
« non attendus » qui existait déjà, sans une ligne de plus.

**Le `nombre` d'une tranche dérivée vient de l'archive**, arbitrage rendu par la
propriétaire le 09/09/2026 : une divergence avec la collecte ne doit pas rendre
un profil illisible à la relecture, très loin de sa cause (#771). Elle se
déclare **là où elle naît**, par `nombre_collecte`, écrit uniquement en cas
d'écart — un champ qui n'apparaît que quand quelque chose ne va pas se remarque,
là où un champ toujours présent et presque toujours égal ne se lit plus (#510).
"""

import gzip
import json
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

import profil_brut  # noqa: E402
import tranches_amendements_figees as figees  # noqa: E402


@pytest.fixture(autouse=True)
def _memo_propre():
    figees.vider_memo()
    yield
    figees.vider_memo()


def _am(uid, leg):
    return {"uid": uid, "legislature": leg, "date": None, "co_signataires": []}


@pytest.fixture
def corpus(tmp_path, monkeypatch):
    """Archive : `PA1` a signé AM1 et AM2 en XVIe. Rien en XVIIe (vivante)."""
    base = tmp_path / "raw_data" / "amendements_an_figes" / "16"
    base.mkdir(parents=True)
    store = {"AM1": _am("AM1", "16"), "AM2": _am("AM2", "16")}
    par_acteur = {"PA1": [{"uid": "AM1", "role_signataire": "auteur_principal"},
                          {"uid": "AM2", "role_signataire": "cosignataire"}]}
    for nom, contenu in ((figees.NOM_STORE, store), (figees.NOM_INDEX_ACTEUR, par_acteur)):
        with gzip.open(base / nom, "wt", encoding="utf-8") as f:
            json.dump(contenu, f)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _profil(amendements):
    return {"slug": "un-depute", "votes": [], "amendements": amendements}


# ---------------------------------------------------------------------------
# Le marquage
# ---------------------------------------------------------------------------


def test_une_legislature_close_est_marquee_et_nest_plus_rendue(corpus):
    socle, tranches = profil_brut.partitionner(
        _profil([_am("AM1", "16"), _am("AM2", "16")]), acteur_ref="an:PA1"
    )
    declaree = socle[profil_brut.CLE_MANIFESTE]["tranches"][0]
    assert declaree[profil_brut.CLE_TRANCHE_DERIVEE] is True
    assert declaree[profil_brut.CLE_ACTEUR_TRANCHE] == "an:PA1"
    assert "fichier" not in declaree, "une tranche dérivée n'a pas de fichier"
    assert tranches == {}, "la tranche marquée ne doit plus être écrite"


def test_une_legislature_vivante_reste_un_fichier(corpus):
    socle, tranches = profil_brut.partitionner(
        _profil([_am("AM9", "17")]), acteur_ref="an:PA1"
    )
    declaree = socle[profil_brut.CLE_MANIFESTE]["tranches"][0]
    assert profil_brut.CLE_TRANCHE_DERIVEE not in declaree
    assert declaree["fichier"] == "17.json"
    assert set(tranches) == {"17"}


def test_sans_acteur_rien_nest_marque(corpus):
    """Le défaut penche du bon côté : ne rien marquer, c'est le comportement
    d'avant, à l'octet près."""
    socle, tranches = profil_brut.partitionner(_profil([_am("AM1", "16")]))
    assert profil_brut.CLE_TRANCHE_DERIVEE not in socle[profil_brut.CLE_MANIFESTE]["tranches"][0]
    assert set(tranches) == {"16"}


def test_un_acteur_absent_de_larchive_nest_pas_marque(corpus):
    """L'archive ne le couvre pas : sa tranche reste un fichier."""
    socle, tranches = profil_brut.partitionner(
        _profil([_am("AM1", "16")]), acteur_ref="an:PA404"
    )
    assert profil_brut.CLE_TRANCHE_DERIVEE not in socle[profil_brut.CLE_MANIFESTE]["tranches"][0]
    assert set(tranches) == {"16"}


def test_une_archive_absente_nampute_pas_le_profil(tmp_path, monkeypatch):
    """Une panne d'archive ne doit pas cesser d'écrire une tranche (#484)."""
    monkeypatch.chdir(tmp_path)
    socle, tranches = profil_brut.partitionner(
        _profil([_am("AM1", "16")]), acteur_ref="an:PA1"
    )
    assert profil_brut.CLE_TRANCHE_DERIVEE not in socle[profil_brut.CLE_MANIFESTE]["tranches"][0]
    assert set(tranches) == {"16"}


# ---------------------------------------------------------------------------
# Le `nombre` vient de l'archive
# ---------------------------------------------------------------------------


def test_le_nombre_vient_de_larchive(corpus):
    """La collecte n'en a qu'un, l'archive en connaît deux."""
    socle, _ = profil_brut.partitionner(_profil([_am("AM1", "16")]), acteur_ref="an:PA1")
    declaree = socle[profil_brut.CLE_MANIFESTE]["tranches"][0]
    assert declaree["nombre"] == 2
    assert declaree["nombre_collecte"] == 1


def test_sans_ecart_aucun_nombre_collecte(corpus):
    """Un champ qui n'apparaît que quand ça ne va pas se remarque ; un champ
    toujours présent et presque toujours égal ne se lit plus (#510)."""
    socle, _ = profil_brut.partitionner(
        _profil([_am("AM1", "16"), _am("AM2", "16")]), acteur_ref="an:PA1"
    )
    assert "nombre_collecte" not in socle[profil_brut.CLE_MANIFESTE]["tranches"][0]


def test_un_ecart_ne_rend_pas_le_profil_illisible(corpus, tmp_path):
    """L'arbitrage, vérifié de bout en bout : la collecte n'a qu'un amendement,
    l'archive en a deux, et le profil se relit quand même."""
    profil_brut.ecrire_profil_brut(
        corpus / "profiles", "un-depute", _profil([_am("AM1", "16")]), acteur_ref="an:PA1"
    )
    relu = profil_brut.charger_profil_brut(corpus / "profiles" / "un-depute.json")
    assert [a["uid"] for a in relu["amendements"]] == ["AM1", "AM2"]


# ---------------------------------------------------------------------------
# L'écriture supprime le fichier devenu inutile
# ---------------------------------------------------------------------------


def test_lecriture_supprime_la_tranche_devenue_derivee(corpus):
    profils = corpus / "profiles"
    profil = _profil([_am("AM1", "16"), _am("AM2", "16"), _am("AM9", "17")])
    profil_brut.ecrire_profil_brut(profils, "un-depute", profil)
    assert sorted(p.name for p in (profils / "un-depute").glob("*.json")) == \
        ["16.json", "17.json"]

    profil_brut.ecrire_profil_brut(profils, "un-depute", profil, acteur_ref="an:PA1")
    assert sorted(p.name for p in (profils / "un-depute").glob("*.json")) == ["17.json"]


def test_un_profil_entierement_derive_perd_son_repertoire(corpus):
    profils = corpus / "profiles"
    profil = _profil([_am("AM1", "16"), _am("AM2", "16")])
    profil_brut.ecrire_profil_brut(profils, "un-depute", profil)
    assert (profils / "un-depute").is_dir()
    profil_brut.ecrire_profil_brut(profils, "un-depute", profil, acteur_ref="an:PA1")
    assert not (profils / "un-depute").exists()


def test_laller_retour_reste_exact_sans_tranche_derivee(corpus):
    """La propriété d'origine (#580) n'est pas touchée là où elle a un sens."""
    profils = corpus / "profiles"
    profil = _profil([_am("AM9", "17"), _am("AM8", "17")])
    profil_brut.ecrire_profil_brut(profils, "un-depute", profil)
    relu = profil_brut.charger_profil_brut(profils / "un-depute.json")
    assert relu["amendements"] == profil["amendements"]


def test_lordre_devient_par_blocs_des_quune_tranche_est_derivee(corpus):
    """L'ordre d'origine n'est plus restituable — la tranche dérivée est relue
    dans celui de l'archive. Aucun consommateur ne lit l'ordre : le contrôle de
    perte relève une liste par un entier."""
    socle, _ = profil_brut.partitionner(
        _profil([_am("AM9", "17"), _am("AM1", "16"), _am("AM2", "16")]),
        acteur_ref="an:PA1",
    )
    manifeste = socle[profil_brut.CLE_MANIFESTE]
    assert manifeste["ordre"] == [[0, 2], [1, 1]]
    assert manifeste["total"] == 3


# ---------------------------------------------------------------------------
# L'amorçage : la fusion reconduit ce que la collecte a marqué (#691, lot 3c)
# ---------------------------------------------------------------------------


def test_la_fusion_reconduit_le_marquage_des_sources(corpus):
    """Le défaut que le run `34329085168` a rendu visible : vert, et rien basculé.

    Les shards avaient bien marqué leurs socles — vérifié dans l'artifact de
    `gabriel-attal` —, et la fusion les a défaits : elle lisait l'acteur dans le
    socle de **destination**, celui du corpus committé, jamais marqué, donc
    `None`, donc aucun marquage, donc les tranches réécrites.

    Le principe était juste, l'implémentation lisait le mauvais fichier.
    """
    import merge_profile

    source = corpus / "_artifacts" / "an"
    source.mkdir(parents=True)
    profil_brut.ecrire_profil_brut(
        source, "un-depute", _profil([_am("AM1", "16"), _am("AM9", "17")]),
        acteur_ref="an:PA1",
    )
    socle_source = json.loads((source / "un-depute.json").read_text(encoding="utf-8"))
    assert any(t.get(profil_brut.CLE_TRANCHE_DERIVEE)
               for t in socle_source[profil_brut.CLE_MANIFESTE]["tranches"]), \
        "prérequis : la source doit être marquée"

    destination = corpus / "profiles"
    destination.mkdir(exist_ok=True)
    merge_profile.merge_raw_dirs([source], destination)

    socle = json.loads((destination / "un-depute.json").read_text(encoding="utf-8"))
    tranches = socle[profil_brut.CLE_MANIFESTE]["tranches"]
    derivees = [t for t in tranches if t.get(profil_brut.CLE_TRANCHE_DERIVEE)]
    assert [t["legislature"] for t in derivees] == ["16"], (
        "la fusion a défait le marquage de la collecte"
    )
    assert sorted(p.name for p in (destination / "un-depute").glob("*.json")) == ["17.json"]


def test_la_fusion_dit_ce_quelle_a_fait_aux_tranches(corpus, capsys):
    """Un mode de test ne vaut que ce que le log donne à voir.

    Le run de test qui précédait `34329085168` portait déjà le défaut et ne
    pouvait pas le montrer : l'effet vit dans le commit, et un run de test ne
    committe pas. `✓ N profil(s) écrits` ne disait rien de la bascule.
    """
    import merge_profile

    source = corpus / "_artifacts" / "an"
    source.mkdir(parents=True)
    profil_brut.ecrire_profil_brut(
        source, "un-depute", _profil([_am("AM1", "16"), _am("AM9", "17")]),
        acteur_ref="an:PA1",
    )
    destination = corpus / "profiles"
    destination.mkdir(exist_ok=True)
    # Un premier passage NON marqué : la tranche 16 existe en fichier.
    profil_brut.ecrire_profil_brut(
        destination, "un-depute", _profil([_am("AM1", "16"), _am("AM9", "17")])
    )
    capsys.readouterr()

    merge_profile.merge_raw_dirs([source], destination)
    sortie = capsys.readouterr().out
    assert "1 dérivée(s) de l'archive" in sortie
    assert "1 en fichier" in sortie
    assert "1 fichier(s) retiré(s) ce run" in sortie


def test_la_fusion_se_tait_quand_il_ny_a_rien_a_dire(corpus, capsys):
    """Un compteur toujours imprimé, presque toujours à zéro, ne se lit plus
    (#510) : la ligne n'apparaît que si une tranche est dérivée ou retirée."""
    import merge_profile

    source = corpus / "_artifacts" / "an"
    source.mkdir(parents=True)
    profil_brut.ecrire_profil_brut(source, "un-depute", _profil([_am("AM9", "17")]))
    destination = corpus / "profiles"
    destination.mkdir(exist_ok=True)
    capsys.readouterr()

    merge_profile.merge_raw_dirs([source], destination)
    assert "tranches d'amendements" not in capsys.readouterr().out
