"""Le lecteur accepte une tranche dérivée de l'archive figée (#691, lot 2).

Ce lot ne cesse toujours rien d'écrire : il rend le **lecteur** capable de
servir une tranche que le manifeste déclare dérivable. La suppression viendra
après, et seulement après.

La règle que ces tests protègent tient en une phrase : **le manifeste doit le
dire, et le silence reste une panne**. Aller chercher l'archive « au cas où le
fichier manquerait » ferait lire une tranche perdue comme une tranche dérivée,
et republierait un profil amputé sans que rien ne le signale — exactement ce que
`PartitionIllisible` existe pour empêcher (#580).
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


def _amendement(uid, leg="16"):
    return {
        "uid": uid, "texte_vise": "PRJLANR5L16B0017", "sort": None,
        "base_juridique_irrecevabilite": None, "premier_signataire": "an:PA1",
        "co_signataires": ["an:PA2"], "type_deposant": "depute",
        "date": "2022-07-11", "numero": uid[-1], "source_url": None,
    }


@pytest.fixture
def archive(tmp_path, monkeypatch):
    """Une archive figée à la place où le module la cherche.

    `monkeypatch.chdir` plutôt qu'un paramètre : les constantes de ce dépôt sont
    relatives exprès, et c'est ce qui permet aux tests de s'isoler (#721).
    """
    racine = tmp_path / "raw_data" / "amendements_an_figes" / "16"
    racine.mkdir(parents=True)
    store = {"AM1": _amendement("AM1"), "AM2": _amendement("AM2")}
    par_acteur = {"PA1": [
        {"uid": "AM1", "role_signataire": "auteur_principal"},
        {"uid": "AM2", "role_signataire": "cosignataire"},
    ]}
    for nom, contenu in ((figees.NOM_STORE, store), (figees.NOM_INDEX_ACTEUR, par_acteur)):
        with gzip.open(racine / nom, "wt", encoding="utf-8") as f:
            json.dump(contenu, f)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _socle(tmp_path, tranches, ordre):
    chemin = tmp_path / "profiles" / "un-depute.json"
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(json.dumps({
        "slug": "un-depute",
        profil_brut.CLE_MANIFESTE: {
            "schema": profil_brut.SCHEMA_PARTITION,
            "total": sum(t.get("nombre", 0) for t in tranches),
            "tranches": tranches,
            "ordre": ordre,
        },
    }), encoding="utf-8")
    return chemin


def _tranche_derivee(nombre=2):
    return {"legislature": "16", profil_brut.CLE_TRANCHE_DERIVEE: True,
            profil_brut.CLE_ACTEUR_TRANCHE: "an:PA1", "nombre": nombre}


# ---------------------------------------------------------------------------
# Le cas nominal
# ---------------------------------------------------------------------------


def test_un_profil_a_tranche_derivee_se_recompose(archive):
    chemin = _socle(archive, [_tranche_derivee()], [[0, 2]])
    profil = profil_brut.charger_profil_brut(chemin)
    assert [a["uid"] for a in profil["amendements"]] == ["AM1", "AM2"]
    assert profil["amendements"][0]["role_signataire"] == "auteur_principal"
    assert profil["amendements"][0]["legislature"] == "16"


def test_literation_sert_aussi_la_tranche_derivee(archive):
    """Les index passent par là, une tranche à la fois."""
    chemin = _socle(archive, [_tranche_derivee()], [[0, 2]])
    assert [a["uid"] for a in profil_brut.iter_amendements_du_profil(chemin)] == ["AM1", "AM2"]
    assert profil_brut.compter_amendements(chemin) == 2


def test_une_tranche_derivee_et_une_tranche_fichier_cohabitent(archive):
    """La bascule sera progressive : 14/15/16 dérivables, la XVIIe non."""
    dossier = archive / "profiles" / "un-depute"
    dossier.mkdir(parents=True, exist_ok=True)
    (dossier / "17.json").write_text(json.dumps({
        "schema": profil_brut.SCHEMA_TRANCHE, "slug": "un-depute",
        "legislature": "17", "amendements": [_amendement("AM9", "17")],
    }), encoding="utf-8")
    chemin = _socle(
        archive,
        [_tranche_derivee(), {"legislature": "17", "fichier": "17.json", "nombre": 1}],
        [[1, 1], [0, 2]],
    )
    profil = profil_brut.charger_profil_brut(chemin)
    assert [a["uid"] for a in profil["amendements"]] == ["AM9", "AM1", "AM2"]


def test_la_tranche_derivee_na_pas_de_fichier_a_transporter(archive):
    """`fichiers_du_profil` sert les artifacts CI : l'archive est committée,
    il n'y a rien à déplacer."""
    _socle(archive, [_tranche_derivee()], [[0, 2]])
    fichiers = profil_brut.fichiers_du_profil(archive / "profiles", "un-depute")
    assert [f.name for f in fichiers] == ["un-depute.json"]


# ---------------------------------------------------------------------------
# Ce qui doit lever plutôt que rendre vide
# ---------------------------------------------------------------------------


def test_le_silence_reste_une_panne(archive):
    """LE test de ce lot. Une tranche NON marquée dont le fichier manque ne
    doit surtout pas se replier sur l'archive : une tranche perdue se lirait
    comme une tranche dérivée."""
    chemin = _socle(archive, [{"legislature": "16", "fichier": "16.json", "nombre": 2}], [[0, 2]])
    with pytest.raises(profil_brut.PartitionIllisible, match="illisible|absente"):
        profil_brut.charger_profil_brut(chemin)


def test_une_tranche_derivee_sans_acteur_leve(archive):
    declaree = _tranche_derivee()
    del declaree[profil_brut.CLE_ACTEUR_TRANCHE]
    chemin = _socle(archive, [declaree], [[0, 2]])
    with pytest.raises(profil_brut.PartitionIllisible, match="acteur_ref"):
        profil_brut.charger_profil_brut(chemin)


def test_une_tranche_derivee_sans_legislature_leve(archive):
    declaree = _tranche_derivee()
    declaree["legislature"] = ""
    chemin = _socle(archive, [declaree], [[0, 2]])
    with pytest.raises(profil_brut.PartitionIllisible, match="legislature"):
        profil_brut.charger_profil_brut(chemin)


def test_un_acteur_inconnu_de_larchive_leve(archive):
    """« Déclarée dérivée » et « non dérivable » ne peuvent pas coexister en
    silence : ce serait un profil publié sans ses amendements."""
    declaree = _tranche_derivee()
    declaree[profil_brut.CLE_ACTEUR_TRANCHE] = "an:PA404"
    chemin = _socle(archive, [declaree], [[0, 2]])
    with pytest.raises(profil_brut.PartitionIllisible, match="inconnu de l'archive"):
        profil_brut.charger_profil_brut(chemin)


def test_une_archive_absente_leve(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    chemin = _socle(tmp_path, [_tranche_derivee()], [[0, 2]])
    with pytest.raises(profil_brut.PartitionIllisible):
        profil_brut.charger_profil_brut(chemin)


def test_le_nombre_annonce_est_un_controle_pas_une_source(archive):
    """Un contrôle qui lit sa conclusion dans le document contrôlé ne contrôle
    rien (#576, #579) : le compte du manifeste est CONFRONTÉ au reconstruit."""
    chemin = _socle(archive, [_tranche_derivee(nombre=99)], [[0, 99]])
    with pytest.raises(profil_brut.PartitionIllisible, match="2 amendement.* pour 99"):
        profil_brut.charger_profil_brut(chemin)


# ---------------------------------------------------------------------------
# Une seule définition du nom
# ---------------------------------------------------------------------------


def test_le_nom_dune_tranche_declaree_a_une_seule_definition():
    """Trois lecteurs indexaient le même manifeste par le même calcul recopié ;
    une tranche sans `fichier` aurait divergé chez l'un d'eux."""
    source = (RACINE / "src" / "profil_brut.py").read_text(encoding="utf-8")
    code = "\n".join(l for l in source.split("\n") if not l.lstrip().startswith("#"))
    assert code.count("def _nom_declaree") == 1
    # Ce sont les trois LECTEURS qui doivent passer par `_nom_declaree` : une
    # tranche dérivée n'a pas de `fichier`, et l'un d'eux qui le relirait
    # divergerait des deux autres en silence. Les écrivains
    # (`_marquer_derivables`, `ecrire_profil_brut`) ont le droit d'y toucher :
    # c'est eux qui posent ou retirent la clé.
    import re

    for nom in ("charger_tranches", "recomposer", "iter_amendements_du_profil"):
        bloc = re.search(rf"\ndef {nom}\(.*?(?=\ndef |\Z)", code, re.DOTALL)
        assert bloc, f"fonction {nom} introuvable"
        assert '"fichier"' not in bloc.group(0), (
            f"{nom} lit le champ `fichier` du manifeste au lieu de passer par "
            "`_nom_declaree` — une tranche dérivée n'en a pas"
        )
