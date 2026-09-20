"""Partition des profils bruts par législature (#580).

Ce que ces tests verrouillent, dans l'ordre du risque :

1. **La découpe ne perd rien.** Nombre d'amendements et multi-ensemble des
   `uid` identiques avant/après — c'est la garantie sur laquelle repose tout le
   lot, et celle qu'un profil de 56 Mo ne permet pas de vérifier à l'œil.
2. **La recomposition rend l'original**, à l'ordre de la liste ET à l'ordre des
   clés près. Un profil interfolié — dont les amendements ne sont pas groupés
   par législature — se recompose aussi : 36 des 481 profils du corpus du
   29/08/2026 ne sont pas parfaitement groupés.
3. **Aucune tranche ne dépasse le seuil.** Sur un corpus de doublure : la suite
   ne lit jamais `raw_data/profiles`, dont le sparse-checkout de `tests.yml`
   l'écarte délibérément (#473).
4. **Les deux formes cohabitent.** Un profil monolithique se lit sans rien
   changer — c'est la condition de la transition, l'ancienne forme étant encore
   committée pendant la bascule.
5. **Une partition cassée refuse, elle ne rend pas une liste vide.** C'est le
   défaut que ce lot ne doit surtout pas introduire : un profil amputé qui se
   republie sans que rien ne le dise.
"""

import json
from collections import Counter

import pytest

import profil_brut
from profil_brut import (
    CLE_MANIFESTE,
    CLE_PARTITIONNEE,
    PartitionIllisible,
    charger_profil_brut,
    charger_socle,
    compter_amendements,
    ecrire_profil_brut,
    est_partitionne,
    fichiers_du_profil,
    iter_amendements_du_profil,
    partitionner,
    recomposer,
    slugs_du_repertoire,
)


# ---------------------------------------------------------------------------
# Doublures
# ---------------------------------------------------------------------------

def _amendement(uid: str, legislature, **extra):
    """Un amendement de doublure, avec les champs que porte le corpus réel."""
    doc = {
        "uid": uid,
        "texte_vise": f"TXT{uid}",
        "sort": None,
        "base_juridique_irrecevabilite": None,
        "premier_signataire": "an:PA1",
        "co_signataires": ["an:PA2", "an:PA3"],
        "role_signataire": "cosignataire",
        "type_deposant": "depute",
        "numero": uid[-4:],
        "date": "2024-01-01",
        "legislature": legislature,
        "source_url": f"https://example.invalid/{uid}",
    }
    doc.update(extra)
    return doc


def profil_doublure(sequence):
    """Profil brut de doublure. `sequence` : suite de législatures, un
    amendement par entrée — c'est elle qui décide si le profil est groupé."""
    return {
        "slug": "jeanne-doublure",
        "chambre": "AN",
        "source": "an",
        "identite": {"nom": "Jeanne Doublure", "url_an_ou_senat": "https://an.invalid/PA1"},
        "mandats": [{"label": "Députée", "categorie": "mandat_electif"}],
        "votes": [{"numero_scrutin": 12, "legislature": "16", "position": "pour"}],
        "votes_source": "an",
        "dossiers_legislatifs": [],
        "amendements": [
            _amendement(f"AM{i:05d}", legis) for i, legis in enumerate(sequence)
        ],
        "interventions": [{"date": "2024-02-02", "texte": "…"}],
        "meta": {"genere_le": "2026-08-29T00:00:00Z", "warnings": []},
    }


GROUPE = ["15"] * 4 + ["16"] * 3 + ["17"] * 2
INTERFOLIE = ["16", "15", "16", "17", "15", "16", "17", "17", "15"]


# ---------------------------------------------------------------------------
# 1. La découpe ne perd rien
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("sequence", [GROUPE, INTERFOLIE], ids=["groupe", "interfolie"])
def test_decoupe_preserve_le_nombre_et_les_uid(sequence):
    profil = profil_doublure(sequence)
    attendus = profil[CLE_PARTITIONNEE]

    socle, tranches = partitionner(profil)

    decoupes = [a for nom in sorted(tranches) for a in tranches[nom]]
    assert len(decoupes) == len(attendus)
    assert Counter(a["uid"] for a in decoupes) == Counter(a["uid"] for a in attendus)

    # Le socle ne porte plus la clé : ABSENTE, pas vide. Une liste vide se
    # confondrait avec « ce profil n'a déposé aucun amendement ».
    assert CLE_PARTITIONNEE not in socle
    assert socle[CLE_MANIFESTE]["total"] == len(attendus)

    # Aucun champ n'a été retouché : ce sont les mêmes objets, déplacés.
    par_uid = {a["uid"]: a for a in decoupes}
    for original in attendus:
        assert par_uid[original["uid"]] is original


def test_decoupe_ne_modifie_pas_le_profil_source():
    profil = profil_doublure(GROUPE)
    avant = json.dumps(profil, sort_keys=True)
    partitionner(profil)
    assert json.dumps(profil, sort_keys=True) == avant


def test_une_tranche_par_legislature():
    socle, tranches = partitionner(profil_doublure(GROUPE))
    assert sorted(tranches) == ["15", "16", "17"]
    assert [t["nombre"] for t in socle[CLE_MANIFESTE]["tranches"]] == [4, 3, 2]


def test_amendement_sans_legislature_va_dans_sa_propre_tranche():
    """Une législature manquante reste manquante — elle n'est pas rangée
    d'office dans une législature voisine (AGENTS.md §2.5)."""
    socle, tranches = partitionner(profil_doublure(["16", None, "16", ""]))
    assert profil_brut.NOM_SANS_LEGISLATURE in tranches
    assert len(tranches[profil_brut.NOM_SANS_LEGISLATURE]) == 2


# ---------------------------------------------------------------------------
# 2. La recomposition rend l'original
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("sequence", [GROUPE, INTERFOLIE], ids=["groupe", "interfolie"])
def test_recomposer_rend_exactement_l_original(sequence):
    profil = profil_doublure(sequence)
    refait = recomposer(*partitionner(profil))

    assert refait == profil
    # L'ORDRE de la liste, que l'égalité de dict ne suffirait pas à garantir si
    # `amendements` était un ensemble — il est une liste, donc elle le garantit,
    # mais on le dit explicitement : c'est la propriété qui a coûté la séquence
    # par plages du manifeste.
    assert [a["uid"] for a in refait[CLE_PARTITIONNEE]] == [
        a["uid"] for a in profil[CLE_PARTITIONNEE]
    ]
    # L'ordre des CLÉS aussi : c'est ce qui rend l'aller-retour identique
    # octet pour octet, et donc comparable par empreinte à la migration.
    assert list(refait) == list(profil)


def test_liste_vide_reste_une_liste_vide_dans_le_socle():
    """Une liste vide est un FAIT collecté — « ce profil n'a déposé aucun
    amendement » — et pas une donnée rangée ailleurs. Elle reste donc dans le
    socle, sans manifeste ni répertoire : la partition est un remède au volume,
    pas une cérémonie."""
    profil = profil_doublure([])
    socle, tranches = partitionner(profil)
    assert tranches == {}
    assert socle == profil
    assert socle[CLE_PARTITIONNEE] == []
    assert not est_partitionne(socle)


def test_profil_sans_la_cle_ne_recoit_pas_de_manifeste_vide():
    """Un profil UE n'a jamais porté `amendements` : lui poser un manifeste
    à zéro inventerait un fait mesuré là où il n'y a rien."""
    profil = {"slug": "x", "mandat_europeen": {"mandats_europeens": []}}
    socle, tranches = partitionner(profil)
    assert tranches == {}
    assert CLE_MANIFESTE not in socle
    assert not est_partitionne(socle)


# ---------------------------------------------------------------------------
# 3. Écriture / relecture sur disque, les deux formes
# ---------------------------------------------------------------------------

def test_aller_retour_disque(tmp_path):
    profil = profil_doublure(INTERFOLIE)
    ecrire_profil_brut(tmp_path, "jeanne-doublure", profil)

    socle_path = tmp_path / "jeanne-doublure.json"
    assert socle_path.is_file()
    assert sorted(p.name for p in (tmp_path / "jeanne-doublure").glob("*.json")) == [
        "15.json", "16.json", "17.json",
    ]

    assert charger_profil_brut(socle_path) == profil
    assert compter_amendements(socle_path) == len(profil[CLE_PARTITIONNEE])


def test_forme_monolithique_encore_lue(tmp_path):
    """La transition n'est pas atomique : l'ancienne forme est encore
    committée pendant la bascule et doit se lire sans rien changer."""
    profil = profil_doublure(GROUPE)
    chemin = tmp_path / "jeanne-doublure.json"
    chemin.write_text(json.dumps(profil, ensure_ascii=False), encoding="utf-8")

    assert not est_partitionne(json.loads(chemin.read_text(encoding="utf-8")))
    assert charger_profil_brut(chemin) == profil
    assert compter_amendements(chemin) == len(profil[CLE_PARTITIONNEE])
    assert [a["uid"] for a in iter_amendements_du_profil(chemin)] == [
        a["uid"] for a in profil[CLE_PARTITIONNEE]
    ]


def test_ecriture_migre_un_profil_monolithique(tmp_path):
    profil = profil_doublure(GROUPE)
    chemin = tmp_path / "jeanne-doublure.json"
    chemin.write_text(json.dumps(profil, ensure_ascii=False), encoding="utf-8")

    ecrire_profil_brut(tmp_path, "jeanne-doublure", charger_profil_brut(chemin))

    assert est_partitionne(charger_socle(chemin))
    assert charger_profil_brut(chemin) == profil


def test_tranche_devenue_sans_objet_est_retiree(tmp_path):
    """Une législature qui disparaît d'un profil ne doit pas laisser derrière
    elle une tranche que la recomposition rejouerait."""
    ecrire_profil_brut(tmp_path, "jeanne-doublure", profil_doublure(GROUPE))
    assert (tmp_path / "jeanne-doublure" / "17.json").is_file()

    ecrire_profil_brut(tmp_path, "jeanne-doublure", profil_doublure(["15", "16"]))
    assert not (tmp_path / "jeanne-doublure" / "17.json").exists()
    assert sorted(p.name for p in (tmp_path / "jeanne-doublure").glob("*.json")) == [
        "15.json", "16.json",
    ]


def test_socle_porte_tout_sauf_les_amendements(tmp_path):
    """Le socle reste un document autonome : mandats, votes, interventions y
    sont, et c'est ce qui laisse `iter_votes_du_repertoire` inchangé."""
    profil = profil_doublure(GROUPE)
    ecrire_profil_brut(tmp_path, "jeanne-doublure", profil)
    socle = charger_socle(tmp_path / "jeanne-doublure.json")
    for champ in ("identite", "mandats", "votes", "interventions", "meta"):
        assert socle[champ] == profil[champ]


def test_enumeration_des_slugs_ignore_les_repertoires_de_tranches(tmp_path):
    """La propriété qui a décidé la disposition : les `glob("*.json")` du dépôt
    continuent de rendre exactement les mêmes slugs qu'avant."""
    for slug in ("aline", "boris"):
        ecrire_profil_brut(tmp_path, slug, profil_doublure(GROUPE))
    (tmp_path / ".generation_checkpoint.json").write_text("{}", encoding="utf-8")

    assert slugs_du_repertoire(tmp_path) == ["aline", "boris"]
    assert sorted(p.name for p in tmp_path.glob("*.json")) == [
        ".generation_checkpoint.json", "aline.json", "boris.json",
    ]


def test_fichiers_du_profil_liste_socle_et_tranches(tmp_path):
    ecrire_profil_brut(tmp_path, "aline", profil_doublure(GROUPE))
    noms = [p.name for p in fichiers_du_profil(tmp_path, "aline")]
    assert noms == ["aline.json", "15.json", "16.json", "17.json"]


# ---------------------------------------------------------------------------
# 4. Une partition cassée REFUSE — elle ne rend jamais une liste vide
# ---------------------------------------------------------------------------

def test_tranche_absente_refuse(tmp_path):
    ecrire_profil_brut(tmp_path, "aline", profil_doublure(GROUPE))
    (tmp_path / "aline" / "16.json").unlink()

    with pytest.raises(PartitionIllisible, match="16.json"):
        charger_profil_brut(tmp_path / "aline.json")


def test_tranche_tronquee_refuse(tmp_path):
    ecrire_profil_brut(tmp_path, "aline", profil_doublure(GROUPE))
    chemin = tmp_path / "aline" / "16.json"
    doc = json.loads(chemin.read_text(encoding="utf-8"))
    doc[CLE_PARTITIONNEE] = doc[CLE_PARTITIONNEE][:1]
    chemin.write_text(json.dumps(doc), encoding="utf-8")

    with pytest.raises(PartitionIllisible):
        charger_profil_brut(tmp_path / "aline.json")


def test_schema_de_partition_inconnu_refuse(tmp_path):
    ecrire_profil_brut(tmp_path, "aline", profil_doublure(GROUPE))
    chemin = tmp_path / "aline.json"
    socle = json.loads(chemin.read_text(encoding="utf-8"))
    socle[CLE_MANIFESTE]["schema"] = "profil-brut-partitionne-v99"
    chemin.write_text(json.dumps(socle), encoding="utf-8")

    with pytest.raises(PartitionIllisible, match="v99"):
        charger_profil_brut(chemin)


def test_nom_de_tranche_hors_du_repertoire_refuse(tmp_path):
    """Un nom de fichier venu du manifeste ne doit jamais pouvoir sortir du
    répertoire de tranches."""
    ecrire_profil_brut(tmp_path, "aline", profil_doublure(GROUPE))
    chemin = tmp_path / "aline.json"
    socle = json.loads(chemin.read_text(encoding="utf-8"))
    socle[CLE_MANIFESTE]["tranches"][0]["fichier"] = "../../secret.json"
    chemin.write_text(json.dumps(socle), encoding="utf-8")

    with pytest.raises(PartitionIllisible, match="refusé"):
        charger_profil_brut(chemin)


# ---------------------------------------------------------------------------
# 5. Aucune tranche ne dépasse le seuil, sur le corpus de doublure
# ---------------------------------------------------------------------------

def test_aucun_fichier_ne_depasse_le_plus_gros_fragment_attendu(tmp_path):
    """La propriété que la découpe achète, éprouvée sur un corpus de doublure.

    Sur une doublure, pas sur `raw_data/profiles` : `tests.yml` sparse-checkout
    délibérément sans le corpus (#473), donc un test qui le lirait serait vert
    en local et sans objet en CI. Le corpus réel est mesuré par le garde-fou du
    quality gate, qui tourne là où le corpus existe.

    Ce qui est vérifié ici est la propriété structurelle, pas un chiffre : le
    plus gros fichier écrit est une tranche, chaque tranche est strictement
    plus légère que le profil monolithique, et le seuil du garde-fou n'est
    franchi par aucun fichier.
    """
    from garde_fou_blobs import SEUIL_AVERTISSEMENT_OCTETS, inventorier

    # Réparti sur trois législatures, majoritaire sur la 16 : la plus grosse
    # tranche est donc bien plus petite que le tout, comme sur le corpus réel
    # (56,0 Mo → 23,4 Mo).
    gros = profil_doublure(["15"] * 300 + ["16"] * 900 + ["17"] * 400)
    monolithique = len(json.dumps(gros, ensure_ascii=False).encode("utf-8"))

    ecrire_profil_brut(tmp_path, "gros", gros)
    fichiers = fichiers_du_profil(tmp_path, "gros")
    tailles = {f.name: f.stat().st_size for f in fichiers}

    assert max(tailles.values()) < monolithique
    assert tailles["16.json"] == max(tailles.values())     # la plus grosse tranche
    assert tailles["gros.json"] < monolithique // 10       # le socle est marginal
    assert all(t < SEUIL_AVERTISSEMENT_OCTETS for t in tailles.values())
    assert not inventorier([tmp_path], plancher_octets=SEUIL_AVERTISSEMENT_OCTETS)

    assert charger_profil_brut(tmp_path / "gros.json") == gros
