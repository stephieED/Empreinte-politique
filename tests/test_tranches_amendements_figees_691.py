"""Reconstruire une tranche depuis l'archive figée, sans rien supprimer (#691a).

Ce lot ne touche pas au disque : il **prouve** qu'on sait reproduire ce qu'on
voudra cesser d'écrire. C'est l'ordre qui compte — rien ne sera supprimé avant
que le lot suivant ait tranché les deux questions que celui-ci laisse ouvertes
(le filet de `merge_profile`, et l'ordre).

Les fixtures reproduisent la **forme réelle** de l'archive, y compris son défaut
— les 8 `@xsi:nil` sur 624 180 entrées. C'est la leçon de #726 et de #788 : une
fixture qui décrit le monde tel que le code l'imagine ne révèle rien.
"""

import gzip
import json
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

import tranches_amendements_figees as archives  # noqa: E402


@pytest.fixture(autouse=True)
def _memo_propre():
    archives.vider_memo()
    yield
    archives.vider_memo()


NIL_XML = {"@xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance", "@xsi:nil": "true"}


def _ecrire_archive(racine: Path, legislature: str, store: dict, par_acteur: dict) -> Path:
    base = racine / legislature
    base.mkdir(parents=True, exist_ok=True)
    for nom, contenu in ((archives.NOM_STORE, store), (archives.NOM_INDEX_ACTEUR, par_acteur)):
        with gzip.open(base / nom, "wt", encoding="utf-8") as fichier:
            json.dump(contenu, fichier)
    return racine


@pytest.fixture
def archive(tmp_path):
    store = {
        "AM001": {
            "uid": "AM001", "texte_vise": "PRJLANR5L16B0017", "sort": "rejeté",
            "base_juridique_irrecevabilite": None, "premier_signataire": "an:PA720892",
            "co_signataires": ["an:PA795228", "an:PA793262"], "type_deposant": "depute",
            "date": "2022-07-11", "numero": "AC1", "source_url": None,
        },
        "AM002": {
            "uid": "AM002", "texte_vise": "PRJLANR5L16B0017", "sort": None,
            "base_juridique_irrecevabilite": None, "premier_signataire": "an:PA795228",
            "co_signataires": ["an:PA720892"], "type_deposant": "depute",
            # Le résidu XML que la collecte normalise en `null`.
            "date": dict(NIL_XML), "numero": "AC2", "source_url": None,
        },
    }
    par_acteur = {
        "PA720892": [
            {"uid": "AM001", "role_signataire": "auteur_principal"},
            {"uid": "AM002", "role_signataire": "cosignataire"},
        ],
        "PA999999": [],
    }
    return _ecrire_archive(tmp_path / "figes", "16", store, par_acteur)


# ---------------------------------------------------------------------------
# L'équivalence
# ---------------------------------------------------------------------------


def test_la_tranche_reconstruite_a_la_forme_dune_tranche(archive):
    tranche = archives.reconstruire_tranche("an:PA720892", "16", archive)
    assert [a["uid"] for a in tranche] == ["AM001", "AM002"]
    premier = tranche[0]
    assert premier["role_signataire"] == "auteur_principal"
    assert premier["legislature"] == "16"
    assert premier["co_signataires"] == ["an:PA795228", "an:PA793262"]
    assert set(premier) == {
        "uid", "texte_vise", "sort", "base_juridique_irrecevabilite",
        "premier_signataire", "co_signataires", "type_deposant", "date",
        "numero", "source_url", "role_signataire", "legislature",
    }


def test_les_deux_champs_derives_sont_les_seuls_ajouts(archive):
    """`role_signataire` vient de l'index, `legislature` du nom de fichier.
    Ce sont exactement les deux que #691 avait identifiés comme dérivables."""
    store, _ = archives.charger_archive("16", archive)
    tranche = archives.reconstruire_tranche("an:PA720892", "16", archive)
    ajouts = set(tranche[0]) - set(store["AM001"])
    assert ajouts == {"role_signataire", "legislature"}


def test_le_nil_xml_devient_null(archive):
    """8 entrées sur 624 180 dans le corpus réel — assez rares pour passer
    inaperçues, assez réelles pour écrire un objet XML là où le corpus
    porte `null` (§2 règle 5)."""
    tranche = archives.reconstruire_tranche("an:PA720892", "16", archive)
    second = next(a for a in tranche if a["uid"] == "AM002")
    assert second["date"] is None
    assert second["date"] != NIL_XML


def test_un_null_ordinaire_reste_null(archive):
    """Contre-épreuve : la normalisation ne doit pas inventer de valeur."""
    tranche = archives.reconstruire_tranche("an:PA720892", "16", archive)
    assert tranche[0]["sort"] == "rejeté"
    assert tranche[0]["source_url"] is None


# ---------------------------------------------------------------------------
# Absence connue vs absence inconnue
# ---------------------------------------------------------------------------


def test_un_acteur_sans_amendement_rend_une_liste_vide(archive):
    """Un FAIT : il est dans l'archive, il n'a rien signé."""
    assert archives.reconstruire_tranche("an:PA999999", "16", archive) == []


def test_un_acteur_inconnu_rend_none(archive):
    """Pas un fait : on ne sait pas. Confondre les deux écrirait « aucun
    amendement » sur un membre simplement absent de l'index."""
    assert archives.reconstruire_tranche("an:PA000001", "16", archive) is None
    assert archives.signatures("an:PA000001", "16", archive) is None
    assert archives.signatures("an:PA999999", "16", archive) == []


def test_une_reference_vide_rend_none(archive):
    for valeur in (None, "", 42, []):
        assert archives.reconstruire_tranche(valeur, "16", archive) is None


def test_lacteur_se_lit_prefixe_ou_nu(archive):
    """La table préfixe (`an:PA…`), l'index d'archive est nu."""
    assert archives.reconstruire_tranche("PA720892", "16", archive) == \
        archives.reconstruire_tranche("an:PA720892", "16", archive)


# ---------------------------------------------------------------------------
# L'archive elle-même
# ---------------------------------------------------------------------------


def test_une_archive_a_moitie_presente_est_absente(tmp_path):
    """Le store sans l'index ne dit pas qui a signé quoi. La traiter comme
    disponible produirait des tranches vides pour un fichier manquant (#484)."""
    base = tmp_path / "figes" / "16"
    base.mkdir(parents=True)
    with gzip.open(base / archives.NOM_STORE, "wt", encoding="utf-8") as f:
        json.dump({}, f)
    assert archives.archive_disponible("16", tmp_path / "figes") is False


def test_une_archive_complete_est_disponible(archive):
    assert archives.archive_disponible("16", archive) is True
    assert archives.archive_disponible("15", archive) is False


def test_une_archive_absente_leve_plutot_que_de_rendre_vide(tmp_path):
    """Ce module ne rend jamais un couple vide : il se lirait « ce membre n'a
    signé aucun amendement »."""
    with pytest.raises(FileNotFoundError):
        archives.charger_archive("16", tmp_path / "nulle-part")


def test_un_uid_absent_du_store_est_saute_et_non_ecrit_vide(tmp_path):
    """Archive incohérente : on saute, on n'écrit pas une ligne creuse."""
    racine = _ecrire_archive(
        tmp_path / "figes", "16",
        {"AM001": {"uid": "AM001", "date": None}},
        {"PA1": [{"uid": "AM001", "role_signataire": "auteur_principal"},
                 {"uid": "FANTOME", "role_signataire": "cosignataire"}]},
    )
    tranche = archives.reconstruire_tranche("an:PA1", "16", racine)
    assert [a["uid"] for a in tranche] == ["AM001"]


# ---------------------------------------------------------------------------
# Le mapping pivot : la forme de #431, sans passer par la tranche
# ---------------------------------------------------------------------------


def test_le_mapping_pivot_ne_passe_pas_par_la_tranche(archive):
    """Reconstruire une liste dupliquée pour la dédupliquer trois lignes plus
    loin serait payer la duplication en calcul après l'avoir ôtée du disque."""
    assert archives.mapping_pivot("an:PA720892", "16", dir_archives=archive) == [
        {"amendement_id": "an:AM001", "role_signataire": "auteur_principal"},
        {"amendement_id": "an:AM002", "role_signataire": "cosignataire"},
    ]


def test_le_mapping_pivot_distingue_lui_aussi_vide_et_inconnu(archive):
    assert archives.mapping_pivot("an:PA999999", "16", dir_archives=archive) == []
    assert archives.mapping_pivot("an:PA000001", "16", dir_archives=archive) is None


# ---------------------------------------------------------------------------
# Le mémo
# ---------------------------------------------------------------------------


def test_le_memo_est_par_legislature_et_liberable(archive):
    """L'archive de la XVIe pèse 4,7 Go en clair, et une relecture entière a
    déjà déclenché l'OOM killer sur un run réel."""
    archives.charger_archive("16", archive)
    assert set(archives._MEMO_ACTEURS) == {"16"}
    archives.vider_memo()
    assert archives._MEMO_ACTEURS == {} and archives._MEMO_STORE == {}


def test_les_legislatures_figees_sont_les_trois_closes():
    """Une législature vivante n'a pas d'archive : ses amendements bougent."""
    assert archives.LEGISLATURES_FIGEES == ("14", "15", "16")
    assert "17" not in archives.LEGISLATURES_FIGEES


def test_compter_ne_charge_pas_le_store(archive):
    """Mesuré à la dure : un essai de marquage sur `mathilde-panot` — deux
    législatures closes — s'est fait tuer par l'OOM killer sur une machine à
    7 Go, parce que `signatures()` chargeait aussi le store des amendements.

    Compter et marquer n'ont besoin que de l'index par acteur : 10,5 Mo pour
    la XVe, contre plusieurs centaines pour le store en clair.
    """
    archives.signatures("an:PA720892", "16", archive)
    assert set(archives._MEMO_ACTEURS) == {"16"}
    assert archives._MEMO_STORE == {}, (
        "compter a chargé le store : c'est le chemin qui a produit l'OOM"
    )


def test_reconstruire_charge_bien_le_store(archive):
    """Contre-épreuve : sans elle, le test ci-dessus passerait sur un module
    qui ne lit plus rien."""
    archives.reconstruire_tranche("an:PA720892", "16", archive)
    assert set(archives._MEMO_STORE) == {"16"}
