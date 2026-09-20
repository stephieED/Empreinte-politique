#!/usr/bin/env python3
"""#640 — un profil publie TOUS ses mandats de député, plus un seul.

Ce que ces tests verrouillent, et pourquoi ils tournent sur une **réduction
verbatim** de l'archive AMO30 plutôt que sur une fixture écrite à la main :
la question de départ de l'issue est factuelle — *AMO30 porte-t-il l'historique
des mandats d'un acteur ?* Une fixture inventée y répondrait par construction.
`tests/fixtures/amo30_mandats_assemblee_640.zip` est un extrait **octet pour
octet** de `AMO30_tous_acteurs_tous_mandats_tous_organes_historique.json.zip`
(quatre acteurs et les organes GP qu'ils citent), pour la même raison que
`docs/decisions/syceron-archives-verifiees-parseur-510.md` a fait supprimer les
deux fixtures inventées du parseur Syceron.

Les quatre acteurs ne sont pas pris au hasard : chacun porte un cas que la
reconstruction devait traiter, et deux d'entre eux disent qu'une règle plus
simple aurait fabriqué un fait faux.

| Acteur | Ce qu'il prouve |
| --- | --- |
| `PA720614` (Marine Le Pen) | l'historique existe : 3 mandats ASSEMBLEE, 15e/16e/17e |
| `PA267080` (Xavier Bertrand) | 3 enregistrements de 13e législature pour UN siège, interrompu par deux nominations au gouvernement |
| `PA344201` (Bertrand Petit) | 2 mandats de 16e législature séparés par une élection annulée — regrouper sur la seule législature publierait un mandat pendant lequel il n'était pas député |
| `PA267285` (Laurent Wauquiez) | changement de groupe en cours de mandat (UMP → Les Républicains) et transit « Non inscrit » en début de législature |

Aucun test ici ne lit `pivot_data/` ni `raw_data/profiles/`, et aucun ne sort
sur le réseau : la fixture est copiée dans le cache disque, que
`_ensure_acteurs_historique_zip_downloaded` trouve déjà rempli (AGENTS.md §3b).
"""

import json
import shutil
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import candidate_profile  # noqa: E402
from candidate_profile import (  # noqa: E402
    _build_acteur_identite_index,
    _groupe_du_mandat,
    _periodes_mandats_assemblee,
    build_profile,
)

ARCHIVE = Path(__file__).resolve().parent / "fixtures" / "amo30_mandats_assemblee_640.zip"


@pytest.fixture
def cache_amo30(tmp_path):
    """Le cache disque, garni de la réduction verbatim : aucun téléchargement."""
    shutil.copy(ARCHIVE, tmp_path / "acteurs_historique.zip")
    with patch("candidate_profile.ACTEURS_HISTORIQUE_CACHE_DIR", tmp_path):
        yield tmp_path


def _mandats_de(acteur_ref: str) -> list:
    import zipfile

    with zipfile.ZipFile(ARCHIVE) as zf:
        acteur = json.loads(zf.read(f"json/acteur/{acteur_ref}.json"))["acteur"]
    mandats = (acteur.get("mandats") or {}).get("mandat")
    return mandats if isinstance(mandats, list) else [mandats]


# ---------------------------------------------------------------------------
# 1. Le verdict factuel : AMO30 porte bien l'historique
# ---------------------------------------------------------------------------

def test_amo30_porte_l_historique_des_mandats_d_un_acteur():
    """La question qui ouvre #640, tranchée sur la donnée elle-même.

    Le profil publié n'en portait que **deux** (2022-2024 et 2024→) : le mandat
    de 15e législature n'avait été vu par aucun run, il n'existait nulle part.
    """
    assemblee = [m for m in _mandats_de("PA720614") if m["typeOrgane"] == "ASSEMBLEE"]
    assert sorted(m["legislature"] for m in assemblee) == ["15", "16", "17"]
    assert {(m["dateDebut"], m["dateFin"]) for m in assemblee} == {
        ("2017-06-18", "2022-06-21"),
        ("2022-06-19", "2024-06-09"),
        ("2024-06-30", None),
    }


def test_les_trois_mandats_sont_reconstruits(cache_amo30):
    periodes = _periodes_mandats_assemblee(_mandats_de("PA720614"), {})
    assert [(p["legislature"], p["debut"], p["fin"]) for p in periodes] == [
        ("17", "2024-06-30", None),
        ("16", "2022-06-19", "2024-06-09"),
        ("15", "2017-06-18", "2022-06-21"),
    ]


# ---------------------------------------------------------------------------
# 2. Les deux pièges de la clé de regroupement
# ---------------------------------------------------------------------------

def test_un_siege_interrompu_par_le_gouvernement_est_recolle_en_une_periode():
    """Trois enregistrements AMO30, un seul mandat.

    Xavier Bertrand a trois mandats de 13e législature, tous ouverts au
    2007-06-20 : le siège est rendu à chaque nomination au gouvernement puis
    repris. Les publier séparément produirait trois `mandat_electif` de même
    date d'ouverture, donc **la même clé de fusion** (`label`, `categorie`,
    `fonction`, `debut`) — deux des trois disparaîtraient sans un mot.
    """
    treizieme = [
        m for m in _mandats_de("PA267080")
        if m["typeOrgane"] == "ASSEMBLEE" and m["legislature"] == "13"
    ]
    assert len(treizieme) == 3
    assert {m["dateDebut"] for m in treizieme} == {"2007-06-20"}

    periodes = _periodes_mandats_assemblee(_mandats_de("PA267080"), {})
    par_leg = {p["legislature"]: p for p in periodes}
    assert par_leg["13"]["debut"] == "2007-06-20"
    assert par_leg["13"]["fin"] == "2012-06-19"
    assert par_leg["13"]["segments"] == 3
    assert len(periodes) == 2, "13e et 14e législatures, pas quatre mandats"


def test_deux_mandats_dans_une_legislature_ne_sont_pas_fusionnes():
    """Regrouper sur la seule législature fabriquerait un fait faux.

    L'élection de Bertrand Petit est annulée le 2022-12-02 ; il revient le
    2023-01-29 par une partielle. Une union par législature publierait
    2022-06-19 → 2024-06-09, donc deux mois pendant lesquels il n'était pas
    député (AGENTS.md §2 règle 2). La date d'ouverture sépare les deux cas
    sans arbitrage.
    """
    periodes = _periodes_mandats_assemblee(_mandats_de("PA344201"), {})
    assert [(p["debut"], p["fin"]) for p in periodes] == [
        ("2023-01-29", "2024-06-09"),
        ("2022-06-19", "2022-12-02"),
    ]
    assert all(p["legislature"] == "16" for p in periodes)
    couvre_decembre = [
        p for p in periodes
        if p["debut"] <= "2022-12-15" <= (p["fin"] or "9999-12-31")
    ]
    assert couvre_decembre == [], "aucune période ne doit couvrir l'interruption"


# ---------------------------------------------------------------------------
# 3. Le groupe du libellé : le dernier rejoint pendant le mandat
# ---------------------------------------------------------------------------

def test_le_groupe_du_libelle_ecarte_le_transit_non_inscrit(cache_amo30):
    """Tout le monde est « Non inscrit » les premiers jours d'une législature.

    Les groupes ne sont constitués qu'après l'ouverture : AMO30 porte pour
    chaque élu un mandat `GP` de quelques jours vers `NI`. « Le groupe au début
    du mandat » rendrait donc « Non inscrit » pour la quasi-totalité du corpus
    — c'est le transit mesuré par #526 sur les rosters, au même endroit.
    """
    organes = candidate_profile._build_organe_index()
    mandats = _mandats_de("PA720614")
    # 16e législature : NI du 22 au 28 juin 2022, puis RN.
    assert _groupe_du_mandat(mandats, organes, "2022-06-19", "2024-06-09") == (
        "RN", "Rassemblement National",
    )


def test_le_groupe_du_libelle_suit_le_changement_en_cours_de_mandat(cache_amo30):
    """Wauquiez est UMP de 2012 à juin 2015, puis Les Républicains.

    Le dernier groupe rejoint pendant le mandat est le seul des deux qui soit
    encore vrai à sa clôture — et c'est celui que le profil publie déjà pour
    cette période.
    """
    organes = candidate_profile._build_organe_index()
    assert _groupe_du_mandat(_mandats_de("PA267285"), organes, "2012-06-20", "2017-06-20") == (
        "Les Républicains", "Les Républicains",
    )


def test_aucun_groupe_recouvrant_ne_donne_aucune_parenthese(cache_amo30):
    """Une absence reste une absence : pas de groupe par défaut (§2 règle 5)."""
    assert _groupe_du_mandat(_mandats_de("PA267285"), {}, "1997-06-01", "2002-06-18") == (None, None)


# ---------------------------------------------------------------------------
# 4. L'index d'identité, et la stabilité de la clé de fusion
# ---------------------------------------------------------------------------

def test_l_index_d_identite_publie_la_liste_a_cote_du_compteur(cache_amo30):
    """`nb_mandats` et `mandats_assemblee` vivent dans le même objet — c'est
    leur désaccord qui a produit #640. Le compteur reste le compte
    d'enregistrements AMO30 : il devient le témoin de couverture avec lequel la
    liste se compare, il ne devient pas la liste."""
    index = _build_acteur_identite_index()
    entree = index["PA720614"]
    assert entree["nb_mandats"] == 3
    assert [p["debut"] for p in entree["mandats_assemblee"]] == [
        "2024-06-30", "2022-06-19", "2017-06-18",
    ]
    # Xavier Bertrand : 4 enregistrements, 2 sièges. L'écart est légitime et
    # nommé (un siège interrompu par une nomination au gouvernement), pas lissé.
    assert index["PA267080"]["nb_mandats"] == 4
    assert len(index["PA267080"]["mandats_assemblee"]) == 2


def test_la_periode_courante_garde_le_groupe_courant(cache_amo30):
    """La clé de fusion d'un mandat est `(label, categorie, fonction, debut)`.

    Le libellé de la période courante est donc celui **déjà publié** : un
    libellé qui bouge ferait apparaître un doublon de période au lieu de
    retrouver l'entrée existante, la fusion additive ne retirant jamais
    l'ancienne (`docs/decisions/collecte-vide-necrase-jamais.md`).
    """
    index = _build_acteur_identite_index()
    entree = index["PA720614"]
    courante = entree["mandats_assemblee"][0]
    assert courante["debut"] == entree["mandat_debut"]
    assert courante["groupe_sigle"] == entree["groupe_sigle"]
    assert courante["groupe_nom"] == entree["groupe_nom"]


def test_l_index_versionne_ignore_le_fichier_de_la_version_precedente(cache_amo30):
    """Un index dont le CONTENU change change de nom de fichier (#556).

    Sans ça, le cache disque — restauré d'un run à l'autre par le cache GitHub
    Actions — rendrait l'ancien index et le code corrigé ne s'exécuterait
    jamais. Le v2 posé ici ne doit rien rendre.
    """
    (cache_amo30 / "index_identite_v2.json").write_text(
        json.dumps({"PA720614": {"nom_complet": "index périmé"}}), encoding="utf-8"
    )
    index = _build_acteur_identite_index()
    assert index["PA720614"]["nom_complet"] != "index périmé"
    assert "mandats_assemblee" in index["PA720614"]


# ---------------------------------------------------------------------------
# 5. Ce que le profil publie
# ---------------------------------------------------------------------------

def _build_profile_sans_reseau(identite_an):
    with (
        patch("candidate_profile.time.sleep", return_value=None),
        patch("candidate_profile.fetch_identite_officielle_par_slug",
              return_value=(identite_an, "PA720614")),
        patch("candidate_profile._extract_mandats_officiels", return_value=[]),
        patch("candidate_profile.fetch_positions_hemicycle_officielles", return_value=[]),
        patch("candidate_profile.fetch_votes_officiels", return_value=([], [])),
        patch("candidate_profile.fetch_amendements_officiels", return_value=[]),
        patch("candidate_profile.fetch_textes_portes_officiels", return_value=[]),
        patch("candidate_profile.fetch_interventions_syceron", return_value=[]),
        patch("candidate_profile.fetch_questions_officielles", return_value=[]),
    ):
        return build_profile("deputes", "marine-le-pen")


def test_le_profil_publie_une_entree_par_mandat(cache_amo30):
    identite_an = _build_acteur_identite_index()["PA720614"]
    profile = _build_profile_sans_reseau(identite_an)

    electifs = [m for m in profile["mandats"] if m["categorie"] == "mandat_electif"]
    assert [(m["debut"], m["fin"], m["actif"]) for m in electifs] == [
        ("2024-06-30", None, True),
        ("2022-06-19", "2024-06-09", False),
        ("2017-06-18", "2022-06-21", False),
    ]
    # #492 : la chambre est celle du jeu de données qui a rendu le mandat, pour
    # une période reconstruite rétrospectivement comme pour la période courante.
    assert {m["chambre"] for m in electifs} == {"deputes"}
    # §2 règle 2 : aucune des périodes reconstruites n'est publiée sans source.
    assert {m["source_url"] for m in electifs} == {
        candidate_profile.AN_ACTEURS_HISTORIQUE_ZIP_URL
    }
    assert electifs[0]["label"] == "Mandat parlementaire (Rassemblement National)"


def test_une_identite_sans_liste_publie_encore_le_mandat_courant(cache_amo30):
    """Le repli, verrouillé : une identité construite avant #640 ne doit pas
    faire régresser le profil à zéro mandat électif. Elle publie ce qu'elle
    portait — le couple unique —, pas rien."""
    profile = _build_profile_sans_reseau({
        "nom_complet": "Marine Le Pen",
        "groupe_sigle": "RN",
        "groupe_nom": "Rassemblement National",
        "mandat_debut": "2024-06-30",
        "mandat_fin": None,
    })
    electifs = [m for m in profile["mandats"] if m["categorie"] == "mandat_electif"]
    assert [(m["debut"], m["fin"]) for m in electifs] == [("2024-06-30", None)]
    assert electifs[0]["label"] == "Mandat parlementaire (Rassemblement National)"
