"""« Collecté = publié » doit compter une tranche dérivée (#691, lot 3a).

Sans ce chemin, le garde-fou de #511 lirait « 0 amendement collecté » face à des
millions publiés dès la première tranche dérivée — le défaut que son propre
docstring donne comme celui à éviter, et qui le rendrait aveugle sur 96,7 % du
volume.

**Le principe du contrôle est préservé, et c'est ce qui autorise l'exception.**
Ce qui est interdit, c'est de recopier le `nombre` que le manifeste ANNONCE : un
contrôle qui lit sa conclusion dans le document contrôlé ne contrôle rien (#576,
#579). L'archive figée n'est pas ce document — elle est versionnée, close, et le
compte y est **mesuré** exactement comme dans une tranche sur disque. Le
manifeste ne sert qu'à dire OÙ compter.
"""

import gzip
import json
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

import audit_collecte_vs_publie as audit  # noqa: E402
import profil_brut  # noqa: E402
import tranches_amendements_figees as figees  # noqa: E402


@pytest.fixture(autouse=True)
def _memo_propre():
    figees.vider_memo()
    yield
    figees.vider_memo()


@pytest.fixture
def corpus(tmp_path, monkeypatch):
    """Une archive de 3 amendements pour `PA1`, et un répertoire de profils."""
    base = tmp_path / "raw_data" / "amendements_an_figes" / "16"
    base.mkdir(parents=True)
    store = {f"AM{i}": {"uid": f"AM{i}", "date": None} for i in (1, 2, 3)}
    par_acteur = {"PA1": [{"uid": f"AM{i}", "role_signataire": "cosignataire"} for i in (1, 2, 3)],
                  "PA_MUET": []}
    for nom, contenu in ((figees.NOM_STORE, store), (figees.NOM_INDEX_ACTEUR, par_acteur)):
        with gzip.open(base / nom, "wt", encoding="utf-8") as f:
            json.dump(contenu, f)
    monkeypatch.chdir(tmp_path)
    profils = tmp_path / "profiles"
    profils.mkdir()
    return profils


def _ecrire_socle(profils, slug, tranches):
    (profils / f"{slug}.json").write_text(json.dumps({
        "slug": slug, "votes": [],
        profil_brut.CLE_MANIFESTE: {
            "schema": profil_brut.SCHEMA_PARTITION,
            "total": sum(t.get("nombre", 0) for t in tranches),
            "tranches": tranches, "ordre": [],
        },
    }), encoding="utf-8")


DERIVEE = {"legislature": "16", profil_brut.CLE_TRANCHE_DERIVEE: True,
           profil_brut.CLE_ACTEUR_TRANCHE: "an:PA1", "nombre": 3}


def test_une_tranche_derivee_est_comptee(corpus):
    """LE test de ce lot : sans lui, ce contrôle rendrait 0."""
    _ecrire_socle(corpus, "un-depute", [DERIVEE])
    releve = audit.compter_listes_profil_brut(corpus, "un-depute")
    assert releve[profil_brut.CLE_PARTITIONNEE] == 3


def test_le_compte_vient_de_larchive_pas_du_manifeste(corpus):
    """Le `nombre` annoncé est faux exprès : s'il était recopié, le contrôle
    lirait sa conclusion dans le document qu'il contrôle (#576, #579)."""
    menteur = dict(DERIVEE, nombre=999)
    _ecrire_socle(corpus, "un-depute", [menteur])
    assert audit.compter_listes_profil_brut(corpus, "un-depute")[
        profil_brut.CLE_PARTITIONNEE] == 3


def test_une_tranche_fichier_et_une_derivee_sadditionnent(corpus):
    """La bascule est progressive : 14/15/16 dérivables, la XVIIe non."""
    dossier = corpus / "un-depute"
    dossier.mkdir()
    (dossier / "17.json").write_text(json.dumps({
        "legislature": "17", "amendements": [{"uid": "AM9"}, {"uid": "AM10"}],
    }), encoding="utf-8")
    _ecrire_socle(corpus, "un-depute",
                  [DERIVEE, {"legislature": "17", "fichier": "17.json", "nombre": 2}])
    assert audit.compter_listes_profil_brut(corpus, "un-depute")[
        profil_brut.CLE_PARTITIONNEE] == 5


def test_un_acteur_sans_amendement_compte_zero_sans_lever(corpus):
    """`[]` est un fait : il est dans l'archive et n'a rien signé."""
    _ecrire_socle(corpus, "un-depute", [dict(DERIVEE, acteur_ref="an:PA_MUET", nombre=0)])
    assert audit.compter_listes_profil_brut(corpus, "un-depute")[
        profil_brut.CLE_PARTITIONNEE] == 0


def test_une_tranche_derivee_non_derivable_leve(corpus):
    """Taire ça ferait passer un déficit pour une absence (#511)."""
    _ecrire_socle(corpus, "un-depute", [dict(DERIVEE, acteur_ref="an:PA404")])
    with pytest.raises(ValueError, match="non dérivable"):
        audit.compter_listes_profil_brut(corpus, "un-depute")


def test_un_profil_sans_partition_est_inchange(corpus):
    """Non-régression : le chemin d'avant ne bouge pas."""
    (corpus / "monolithe.json").write_text(json.dumps({
        "slug": "monolithe", "amendements": [{"uid": "A"}, {"uid": "B"}],
    }), encoding="utf-8")
    assert audit.compter_listes_profil_brut(corpus, "monolithe")[
        profil_brut.CLE_PARTITIONNEE] == 2


def test_le_socle_ne_peut_pas_porter_les_deux(corpus):
    """La donnée serait comptée deux fois."""
    (corpus / "double.json").write_text(json.dumps({
        "slug": "double", "amendements": [{"uid": "A"}],
        profil_brut.CLE_MANIFESTE: {
            "schema": profil_brut.SCHEMA_PARTITION, "total": 3,
            "tranches": [DERIVEE], "ordre": [],
        },
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="comptée deux fois"):
        audit.compter_listes_profil_brut(corpus, "double")


def test_compter_nouvre_pas_le_store_des_amendements(corpus, monkeypatch):
    """`signatures()` et non `reconstruire_tranche()` : compter n'a besoin que
    de l'index par acteur — 10,5 Mo au lieu de plusieurs centaines, sur un
    contrôle qui boucle sur tout le corpus."""
    appels = []
    vrai = figees.reconstruire_tranche
    monkeypatch.setattr(figees, "reconstruire_tranche",
                        lambda *a, **k: appels.append(a) or vrai(*a, **k))
    _ecrire_socle(corpus, "un-depute", [DERIVEE])
    audit.compter_listes_profil_brut(corpus, "un-depute")
    assert appels == []
