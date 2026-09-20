#!/usr/bin/env python3
"""Tests de `amendements_index` — liste dédupliquée des amendements (#431).

Le test central de ce module est `test_la_forme_plate_nest_jamais_rematerialisee` :
c'est le critère d'acceptation explicite de l'issue, et la panne qu'il verrouille
a déjà eu lieu (#377, OOM, facteur ~21).
"""

import json
import sys
import tracemalloc
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from amendements_index import (  # noqa: E402
    AmendementsIndex,
    CosignaturesNonChargees,
    LEGISLATURE_INCONNUE,
    charger,
    cle_amendement,
    construire_index,
    decomposer_id,
    ecrire,
    iter_amendements_du_repertoire,
    joindre,
    legislature_de_id,
    legislature_de_uid,
    merge_amendements_index,
    rafraichir,
)

UID_17 = "AMANR5L17PO59047BTC1376P0D1N000012"
UID_16 = "AMANR5L16PO59047BTC2071P0D1N000029"
ID_17 = f"an:{UID_17}"
ID_16 = f"an:{UID_16}"


def _brut(uid=UID_17, **kwargs):
    """Enregistrement plat tel que `_parse_amendement_entry` le produit."""
    base = {
        "uid": uid,
        "texte_vise": "PRJLANR5L17B0324",
        "sort": "adopté",
        "base_juridique_irrecevabilite": None,
        "role_signataire": "auteur_principal",
        "premier_signataire": "an:PA722382",
        "co_signataires": ["an:PA842311", "an:PA795144"],
        "type_deposant": "depute",
        "date": "2026-04-23",
        "numero": "CL312",
        "source_url": None,
    }
    base.update(kwargs)
    return base


# ---------------------------------------------------------------------------
# Identifiant
# ---------------------------------------------------------------------------

def test_cle_amendement_suit_la_convention_du_depot():
    assert cle_amendement(UID_17) == ID_17
    assert decomposer_id(ID_17) == UID_17


def test_cle_amendement_sans_uid_est_none_jamais_inventee():
    """Un amendement sans `uid` n'a pas de clé (AGENTS.md §2.5)."""
    assert cle_amendement(None) is None
    assert cle_amendement("") is None


def test_decomposer_id_refuse_une_forme_inconnue():
    assert decomposer_id(UID_17) is None       # sans le préfixe de source
    assert decomposer_id("senat:AM123") is None
    assert decomposer_id("an:") is None
    assert decomposer_id(None) is None


def test_legislature_se_lit_dans_luid():
    assert legislature_de_uid(UID_17) == "17"
    assert legislature_de_uid(UID_16) == "16"
    assert legislature_de_id(ID_17) == "17"
    assert legislature_de_uid("INCONNU") is None


# ---------------------------------------------------------------------------
# construire_index
# ---------------------------------------------------------------------------

def test_construire_index_deduplique_les_copies_par_signataire():
    """810 552 paires pour 207 238 amendements distincts : c'est le sujet."""
    index = construire_index([_brut(), _brut(role_signataire="cosignataire"), _brut()])
    assert len(index) == 1
    assert index.get(ID_17)["sort"] == "adopté"


def test_construire_index_ignore_les_entrees_sans_uid():
    """Sans clé, l'entrée reste côté profil : elle n'entre pas dans l'index et
    n'y est pas rangée sous une clé devinée."""
    index = construire_index([_brut(uid=None), _brut()])
    assert list(index.par_id) == [ID_17]


def test_construire_index_ne_porte_pas_le_role_signataire():
    """`role_signataire` est le seul champ propre au membre : il reste dans le
    mapping, sans quoi deux signataires du même amendement se disputeraient
    l'entrée partagée."""
    index = construire_index([_brut()])
    assert "role_signataire" not in index.get(ID_17)


def test_construire_index_retient_la_reference_an_du_premier_signataire():
    """`_normalize_amendement` réécrivait `premier_signataire` à l'identifiant
    pivot du profil lecteur : une valeur propre au lecteur n'a rien à faire dans
    une liste partagée (44 139 cas mesurés sur 207 238 amendements)."""
    index = construire_index([
        _brut(premier_signataire="nosdeputes:alexandre-holroyd"),
        _brut(premier_signataire="an:PA721150", role_signataire="cosignataire"),
    ])
    assert index.get(ID_17)["premier_signataire"] == "an:PA721150"


def test_construire_index_ne_regresse_pas_vers_null():
    index = construire_index([_brut(sort=None), _brut(sort="rejeté"), _brut(sort=None)])
    assert index.get(ID_17)["sort"] == "rejeté"


def test_cosignatures_vivent_a_part_du_meta():
    """Elles pèsent 59 % de l'index et personne ne les lit : les garder dans le
    méta ferait payer ce poids à tous les consommateurs."""
    index = construire_index([_brut()])
    assert "co_signataires" not in index.get(ID_17)
    assert index.co_signataires(ID_17) == ["an:PA842311", "an:PA795144"]


def test_co_signataires_distingue_absence_damendement_et_absence_de_cosignataire():
    index = construire_index([_brut(co_signataires=[])])
    assert index.co_signataires(ID_17) == []       # amendement connu, sans cosignataire
    assert index.co_signataires(ID_16) is None     # amendement inconnu
    partiel = AmendementsIndex({ID_17: {}}, cosignatures_chargees=False)
    assert partiel.co_signataires(ID_17) is None   # cosignatures non chargées


def test_get_dun_amendement_inconnu_est_none_pas_une_exception():
    index = construire_index([_brut()])
    assert index.get(ID_16) is None
    assert index.get(None) is None


# ---------------------------------------------------------------------------
# LE critère d'acceptation : la forme plate n'est jamais re-matérialisée
# ---------------------------------------------------------------------------

def test_joindre_est_un_generateur_pas_une_liste():
    """Rendre une liste jointe reconstruirait les 810 552 enregistrements
    complets que la normalisation vient de supprimer (#377, facteur ~21, OOM)."""
    index = construire_index([_brut()])
    resultat = joindre([{"amendement_id": ID_17, "role_signataire": "auteur_principal"}], index)
    assert not isinstance(resultat, (list, tuple))
    assert hasattr(resultat, "__next__")


def test_joindre_rend_lobjet_partage_pas_une_copie():
    """Une copie par paire, c'est exactement la duplication supprimée."""
    index = construire_index([_brut()])
    mapping = [
        {"amendement_id": ID_17, "role_signataire": "auteur_principal"},
        {"amendement_id": ID_17, "role_signataire": "cosignataire"},
    ]
    rendus = [amendement for _, amendement in joindre(mapping, index)]
    assert rendus[0] is index.get(ID_17)
    assert rendus[0] is rendus[1]


def test_la_forme_plate_nest_jamais_rematerialisee():
    """Critère d'acceptation explicite de #431.

    5 000 paires pointant vers 10 amendements distincts. Le pic d'allocation de
    la jointure doit rester de l'ordre de l'index (10 enregistrements), pas de
    l'ordre des paires (5 000). Le témoin mesure ce que coûterait la forme plate
    — c'est lui qui calibre le seuil, pour que le test ne dépende pas de la
    version de Python.
    """
    n_distincts, n_paires = 10, 5000
    bruts = [_brut(uid=f"AMANR5L17PO0B0000P0D1N{i:06d}") for i in range(n_distincts)]
    index = construire_index(bruts)
    mapping = [
        {
            "amendement_id": f"an:AMANR5L17PO0B0000P0D1N{i % n_distincts:06d}",
            "role_signataire": "cosignataire",
        }
        for i in range(n_paires)
    ]

    # Témoin : la forme plate, un enregistrement complet par paire.
    tracemalloc.start()
    plat = [dict(index.get(e["amendement_id"]), **e) for e in mapping]
    pic_plat = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    assert len(plat) == n_paires
    del plat

    # La jointure réelle : consommée en flux, elle n'accumule rien.
    tracemalloc.start()
    vus = 0
    for _entree, amendement in joindre(mapping, index):
        vus += 1 if amendement is not None else 0
    pic_joint = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()

    assert vus == n_paires
    assert pic_joint * 10 < pic_plat, (
        f"la jointure alloue {pic_joint} octets contre {pic_plat} pour la forme "
        "plate : elle re-matérialise ce que #431 supprime"
    )


def test_joindre_sans_index_rend_none_plutot_quune_valeur_inventee():
    mapping = [{"amendement_id": ID_17, "role_signataire": "auteur_principal"}]
    assert [a for _, a in joindre(mapping, None)] == [None]
    assert [a for _, a in joindre(mapping, construire_index([]))] == [None]


# ---------------------------------------------------------------------------
# Fusion additive
# ---------------------------------------------------------------------------

def test_merge_est_additif_un_run_partiel_neffce_rien():
    """Leçon de #450 transposée à l'index : un run qui ne voit qu'une tranche ne
    doit pas faire disparaître ce que d'autres mappings référencent."""
    ancien = construire_index([_brut()])
    nouveau = construire_index([_brut(uid=UID_16)])
    fusionne = merge_amendements_index(ancien, nouveau)
    assert set(fusionne.par_id) == {ID_17, ID_16}
    assert fusionne.co_signataires(ID_17) == ["an:PA842311", "an:PA795144"]


def test_merge_la_nouvelle_valeur_corrige_lancienne():
    ancien = construire_index([_brut(sort="rejeté")])
    nouveau = construire_index([_brut(sort="adopté")])
    assert merge_amendements_index(ancien, nouveau).get(ID_17)["sort"] == "adopté"


def test_merge_ne_regresse_pas_vers_null():
    ancien = construire_index([_brut(numero="CL312")])
    nouveau = construire_index([_brut(numero=None)])
    assert merge_amendements_index(ancien, nouveau).get(ID_17)["numero"] == "CL312"


def test_merge_ne_duplique_pas_les_cosignatures():
    ancien = construire_index([_brut()])
    nouveau = construire_index([_brut()])
    assert merge_amendements_index(ancien, nouveau).co_signataires(ID_17) == [
        "an:PA842311", "an:PA795144",
    ]


def test_merge_avec_un_index_sans_cosignatures_se_declare_ampute():
    ancien = AmendementsIndex({ID_17: {}}, cosignatures_chargees=False)
    fusionne = merge_amendements_index(ancien, construire_index([_brut()]))
    assert fusionne.cosignatures_chargees is False


# ---------------------------------------------------------------------------
# Écriture / lecture
# ---------------------------------------------------------------------------

def test_ecrire_shard_par_legislature(tmp_path):
    """Un fichier global pèserait 128,8 Mo sur les seuls profils actuels, au-delà
    de la limite GitHub de 100 Mo par blob."""
    index = construire_index([_brut(), _brut(uid=UID_16)])
    ecrire(tmp_path, index, genere_le="2026-08-19T22:00:00+0200")
    noms = sorted(p.name for p in tmp_path.iterdir())
    assert noms == [
        "16.cosignatures.json", "16.json", "17.cosignatures.json", "17.json",
    ]
    contenu = json.loads((tmp_path / "17.json").read_text(encoding="utf-8"))
    assert contenu["schema_version"] == "amendements-v1"
    assert contenu["legislature"] == "17"
    assert list(contenu["amendements"]) == [ID_17]
    # La législature est portée une fois par fichier, jamais par entrée.
    assert "legislature" not in contenu["amendements"][ID_17]


def test_ecrire_puis_charger_conserve_tout(tmp_path):
    index = construire_index([_brut(), _brut(uid=UID_16)])
    ecrire(tmp_path, index)
    relu = charger(tmp_path)
    assert set(relu.par_id) == {ID_17, ID_16}
    assert relu.get(ID_17) == index.get(ID_17)
    assert relu.co_signataires(ID_17) == index.co_signataires(ID_17)


def test_charger_sans_cosignatures_epargne_59_pourcent(tmp_path):
    index = construire_index([_brut()])
    ecrire(tmp_path, index)
    leger = charger(tmp_path, avec_cosignatures=False)
    assert len(leger) == 1
    assert leger.cosignatures_chargees is False
    assert leger.co_signataires(ID_17) is None


def test_charger_une_seule_legislature(tmp_path):
    ecrire(tmp_path, construire_index([_brut(), _brut(uid=UID_16)]))
    relu = charger(tmp_path, legislatures=["17"])
    assert set(relu.par_id) == {ID_17}


def test_ecrire_un_index_sans_cosignatures_est_refuse(tmp_path):
    """Le publier effacerait 4,96 M entrées de cosignatures sans rien dire."""
    ecrire(tmp_path, construire_index([_brut()]))
    leger = charger(tmp_path, avec_cosignatures=False)
    with pytest.raises(CosignaturesNonChargees):
        ecrire(tmp_path, leger)


def test_amendement_sans_legislature_lisible_va_dans_un_bucket_nomme(tmp_path):
    """Pas de législature devinée : un bucket nommé, visible."""
    index = construire_index([_brut(uid="AMSENAT0001")])
    assert index.legislatures() == [LEGISLATURE_INCONNUE]
    ecrire(tmp_path, index)
    assert (tmp_path / f"{LEGISLATURE_INCONNUE}.json").exists()


def test_charger_un_dossier_absent_rend_un_index_vide(tmp_path):
    assert len(charger(tmp_path / "absent")) == 0


def test_ordre_stable_dun_run_a_lautre(tmp_path):
    index = construire_index([_brut(uid=f"AMANR5L17PO0B0000P0D1N{i:06d}") for i in (3, 1, 2)])
    ecrire(tmp_path, index)
    premier = (tmp_path / "17.json").read_text(encoding="utf-8")
    ecrire(tmp_path, charger(tmp_path))
    assert (tmp_path / "17.json").read_text(encoding="utf-8") == premier


# ---------------------------------------------------------------------------
# Lecture en flux d'un répertoire de profils
# ---------------------------------------------------------------------------

def _ecrire_profil(dossier: Path, nom: str, amendements: list) -> None:
    dossier.mkdir(parents=True, exist_ok=True)
    (dossier / nom).write_text(
        json.dumps({"amendements": amendements}, ensure_ascii=False), encoding="utf-8"
    )


def test_iter_amendements_du_repertoire(tmp_path):
    _ecrire_profil(tmp_path, "a.json", [_brut()])
    _ecrire_profil(tmp_path, "b.json", [_brut(uid=UID_16)])
    uids = {a["uid"] for a in iter_amendements_du_repertoire(tmp_path)}
    assert uids == {UID_17, UID_16}


def test_un_profil_illisible_ne_prive_pas_les_autres(tmp_path, capsys):
    _ecrire_profil(tmp_path, "a.json", [_brut()])
    (tmp_path / "casse.json").write_text("{ pas du json", encoding="utf-8")
    uids = {a["uid"] for a in iter_amendements_du_repertoire(tmp_path)}
    assert uids == {UID_17}
    assert "Lecture impossible" in capsys.readouterr().out


def test_rafraichir_fusionne_par_defaut(tmp_path):
    profils = tmp_path / "profils"
    index_dir = tmp_path / "index"
    _ecrire_profil(profils, "a.json", [_brut()])
    rafraichir(profils, index_dir)

    # Deuxième run sur une TRANCHE : le premier amendement doit survivre.
    (profils / "a.json").unlink()
    _ecrire_profil(profils, "b.json", [_brut(uid=UID_16)])
    index = rafraichir(profils, index_dir)
    assert set(index.par_id) == {ID_17, ID_16}

    # --no-merge : reconstruction complète, à réserver à un corpus complet.
    index = rafraichir(profils, index_dir, fusionner=False)
    assert set(index.par_id) == {ID_16}
