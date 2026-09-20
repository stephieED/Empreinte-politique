#!/usr/bin/env python3
"""Le `texte_vise` d'un amendement est un uid, jamais un intitulé (issue #696).

LE DÉFAUT. #639 a corrigé la **collecte** : elle écrasait le code sourcé du
document amendé par le titre du dossier avant d'écrire le profil brut. Elle ne
le fait plus. Mais `pivot_data/amendements/` est fusionné additivement, et
`merge_amendements_index` laisse gagner « la nouvelle valeur si elle est
renseignée » — un intitulé **est** renseigné. Mesuré le 01/09/2026 sur
`origin/main` à `f635cb60` : **2 500 des 484 132 amendements publiés** portent
un intitulé, tous en XVe législature, pour 5 intitulés distincts.

Quatrième occurrence de la famille nommée par AGENTS.md §3a (#492
`mandats[].chambre`, #639 `type_scrutin`, #641 `identite.profession`), et
**le test qui manquait aux trois couvre la transition, pas les étapes** : c'est
`test_transition_*` ci-dessous.

CE QUE CES TESTS VERROUILLENT.

  1. Le critère de détection, écrit et mesuré — sur des valeurs **réelles**,
     les quatre formes d'uid des archives et les cinq intitulés publiés.
  2. Que la valeur de substitution vienne de l'archive figée, jamais d'une
     reconstruction depuis le titre ni d'un appariement de libellé (#639, #672).
  3. La monotonie stricte : un uid déjà en place n'est jamais écrasé, une entrée
     sans source garde son intitulé, aucune entrée n'est créée ni supprimée,
     aucun autre champ n'est touché, la clé de fusion ne bouge pas (#668).
  4. Que le report soit câblé sur les **deux** chemins d'appel — la CI ne passe
     jamais par `build_amendements_index_pivot.py`.

FIXTURES. `tests/fixtures/amendements_an_figes/15/amendements.json.gz` est une
réduction **verbatim** de `raw_data/amendements_an_figes/15/amendements.json.gz`
(4 enregistrements, aucun octet réécrit), et les intitulés cités le sont
verbatim depuis `pivot_data/amendements/15.json`. Aucune valeur n'est inventée
(leçon de #510 : les deux fixtures inventées ont été supprimées, pas dépréciées).
"""

import gzip
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import amendements_index  # noqa: E402
from amendements_index import (  # noqa: E402
    AmendementsIndex,
    backfill_texte_vise,
    charger,
    construire_index,
    ecrire,
    merge_amendements_index,
    rafraichir,
)
from textes_vises_figes import (  # noqa: E402
    NOM_ARCHIVE_AMENDEMENTS,
    chemin_archive,
    est_uid_texte,
    lire_textes_vises,
)

ARCHIVES_FIXTURE = Path(__file__).parent / "fixtures" / "amendements_an_figes"

#: L'amendement de la table de l'issue #696, verbatim des deux côtés.
UID = "AMANR5L15PO717460B2623P0D1N000629"
ID = f"an:{UID}"
TEXTE_SOURCE = "PRJLANR5L15B2623"
INTITULE_PUBLIE = "Système universel de retraite"

#: L'amendement que trois profils bruts portaient correctement et que l'index
#: publie malgré tout avec l'intitulé — la fusion ne conserve pas seulement le
#: défaut, elle peut le réintroduire (ordre des fichiers de profils).
UID_REINTRODUIT = "AMANR5L15PO59051B4857P0D1N000045"
ID_REINTRODUIT = f"an:{UID_REINTRODUIT}"
TEXTE_SOURCE_REINTRODUIT = "PRJLANR5L15B4857"
INTITULE_REINTRODUIT = (
    "Projet de loi renforçant les outils de gestion de la crise sanitaire et "
    "modifiant le code de la santé publique"
)

#: Les quatre formes de série réellement observées dans les archives figées.
UID_BTC = "AMANR5L15PO717460BTC1237P0D1N000016"
TEXTE_SOURCE_BTC = "PRJLANR5L15BTC1237"
UID_BTA = "AMANR5L15PO717460BTA0749P0D1N000006"
TEXTE_SOURCE_BTA = "PRJLANR5L15BTA0749"

#: Les 5 intitulés distincts publiés à la place d'un uid, verbatim
#: (`pivot_data/amendements/15.json`, 01/09/2026).
INTITULES_PUBLIES = (
    "Système universel de retraite",
    "Système universel de retraite (loi organique)",
    "Parrainages citoyens pour la candidature à l'élection présidentielle",
    "Droit au logement effectif",
    "Projet de loi renforçant les outils de gestion de la crise sanitaire et "
    "modifiant le code de la santé publique",
)


def _lecteur(dir_archives=ARCHIVES_FIXTURE):
    """Lecteur des archives figées, branché sur les fixtures verbatim."""
    def lire(legislature, uids):
        return lire_textes_vises(legislature, uids, dir_archives=dir_archives)
    return lire


def _index(**textes_vises) -> AmendementsIndex:
    """Index minimal `{id: {texte_vise, …}}`, avec deux champs témoins."""
    return AmendementsIndex({
        amendement_id: {
            "texte_vise": valeur,
            "sort": "rejeté",
            "numero": "629",
        }
        for amendement_id, valeur in textes_vises.items()
    })


def _brut(uid, texte_vise, **kwargs):
    """Enregistrement plat, tel que la collecte le produit dans le profil brut."""
    base = {
        "uid": uid,
        "texte_vise": texte_vise,
        "sort": "rejeté",
        "base_juridique_irrecevabilite": None,
        "role_signataire": "auteur_principal",
        "premier_signataire": "an:PA2150",
        "co_signataires": [],
        "type_deposant": "depute",
        "date": "2020-02-12",
        "numero": "629",
        "source_url": None,
    }
    base.update(kwargs)
    return base


def _ecrire_profil(dossier: Path, nom: str, amendements: list) -> None:
    dossier.mkdir(parents=True, exist_ok=True)
    (dossier / nom).write_text(
        json.dumps({"amendements": amendements}, ensure_ascii=False), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# 1. Le critère : « ne ressemble pas à un uid », écrit et mesuré
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("uid_texte", [
    TEXTE_SOURCE,               # PRJL…B<n>
    TEXTE_SOURCE_BTC,           # PRJL…BTC<n>
    TEXTE_SOURCE_BTA,           # PRJL…BTA<n>
    "PIONANR5L17BTC0699",       # PION, XVIIe (fixture de #639)
    "PNREANR5L15B0169",         # PNRE, verbatim de l'archive figée XV
    "RAPPANR5L14BTC1938",       # RAPP, verbatim de l'archive figée XIV
])
def test_le_critere_accepte_les_formes_reelles_duid(uid_texte):
    """Les quatre préfixes et les trois séries observés dans les archives.

    Mesuré le 01/09/2026 : le critère accepte les **2 086 valeurs distinctes**
    des trois archives figées (781 en XIVe, 855 en XVe, 450 en XVIe) et les
    2 382 valeurs d'uid distinctes publiées, sans exception.
    """
    assert est_uid_texte(uid_texte)


@pytest.mark.parametrize("intitule", INTITULES_PUBLIES)
def test_le_critere_refuse_les_intitules_reellement_publies(intitule):
    """Les 5 seuls intitulés que porte `pivot_data/amendements/`, verbatim."""
    assert not est_uid_texte(intitule)


def test_le_critere_refuse_une_absence_sans_la_confondre_avec_un_intitule():
    """`None` et `""` ne sont pas des uid non plus. Le report les compte à part
    (`entrees_sans_texte_vise`) : l'absence et l'intitulé ne sont pas le même
    fait (AGENTS.md §2 règle 5)."""
    assert not est_uid_texte(None)
    assert not est_uid_texte("")
    assert not est_uid_texte(1088)


def test_le_critere_est_plus_strict_que_labsence_despace():
    """L'issue proposait « un uid AN ne contient pas d'espace ». Mesuré, les deux
    critères rendent **le même verdict** sur les 2 387 valeurs distinctes
    publiées comme sur les 2 086 des archives — aucun contre-exemple.

    La grammaire est retenue parce qu'elle est strictement plus stricte : un
    titre de dossier d'un seul mot passerait le critère de l'espace.
    « Bioéthique » est un titre de dossier réel de la XVe (#689)."""
    assert " " not in "Bioéthique"
    assert not est_uid_texte("Bioéthique")


# ---------------------------------------------------------------------------
# 2. La valeur de substitution vient de l'archive, jamais d'un libellé
# ---------------------------------------------------------------------------

def test_larchive_figee_porte_luid_que_lindex_publie_a_perdu():
    """La table de l'issue #696, sur la fixture verbatim : la source a raison."""
    lus = lire_textes_vises("15", {UID}, dir_archives=ARCHIVES_FIXTURE)
    assert lus == {UID: TEXTE_SOURCE}


def test_la_lecture_ne_rend_que_les_uid_demandes():
    """Projection : l'archive de la XVe pèse 134 Mio décompressés pour 307 644
    enregistrements, et la charger telle quelle coûte 610 Mio de RSS (mesuré).
    Rien d'autre que ce qui est demandé n'est retenu (AGENTS.md §3a)."""
    lus = lire_textes_vises("15", {UID}, dir_archives=ARCHIVES_FIXTURE)
    assert set(lus) == {UID}
    assert UID_BTC not in lus


def test_une_legislature_sans_archive_figee_ne_rend_rien_et_ne_leve_pas():
    """La XVIIe est en cours : elle n'a pas d'archive figée. Le report le
    compte, il ne retombe pas sur une autre source en silence (#510)."""
    assert lire_textes_vises("17", {UID}, dir_archives=ARCHIVES_FIXTURE) == {}


def test_une_archive_illisible_ne_rend_rien_et_ne_leve_pas(tmp_path, capsys):
    """Même convention que `textes_dossiers_an.charger_table` : l'appelant en
    fait une réparation impossible et **comptée**, jamais une suppression."""
    (tmp_path / "15").mkdir()
    (tmp_path / "15" / NOM_ARCHIVE_AMENDEMENTS).write_bytes(b"pas du gzip")
    assert lire_textes_vises("15", {UID}, dir_archives=tmp_path) == {}
    assert "Archive figée illisible" in capsys.readouterr().out


def test_la_lecture_refuse_une_valeur_darchive_qui_nest_pas_un_uid(tmp_path):
    """Substituer un intitulé de l'archive à un intitulé de l'index ne
    réparerait rien. Les archives réelles n'en portent aucun (0 sur 2 086
    valeurs distinctes) ; le refus est structurel, pas une confiance."""
    (tmp_path / "15").mkdir()
    with gzip.open(tmp_path / "15" / NOM_ARCHIVE_AMENDEMENTS, "wt", encoding="utf-8") as f:
        json.dump({UID: {"uid": UID, "texte_vise": INTITULE_PUBLIE}}, f, ensure_ascii=False)
    assert lire_textes_vises("15", {UID}, dir_archives=tmp_path) == {}


def test_le_chemin_darchive_est_celui_des_legislatures_figees():
    assert chemin_archive("15", ARCHIVES_FIXTURE).is_file()
    assert chemin_archive("15", ARCHIVES_FIXTURE).name == NOM_ARCHIVE_AMENDEMENTS


# ---------------------------------------------------------------------------
# 3. Le report : strictement monotone
# ---------------------------------------------------------------------------

def test_le_report_substitue_luid_source_a_lintitule():
    index = _index(**{ID: INTITULE_PUBLIE})
    releve = backfill_texte_vise(index, _lecteur())

    assert index.par_id[ID]["texte_vise"] == TEXTE_SOURCE
    assert releve["entrees_a_reparer"] == 1
    assert releve["entrees_corrigees"] == 1
    assert releve["entrees_sans_source"] == 0
    assert releve["legislatures_lues"] == 1


def test_le_report_necrase_jamais_un_uid_deja_en_place():
    """La monotonie dans l'autre sens : une entrée saine n'est pas relue, et
    l'archive n'est pas ouverte du tout s'il n'y a rien à réparer."""
    index = _index(**{ID: TEXTE_SOURCE_BTC})

    def _refuse(legislature, uids):  # pragma: no cover - ne doit pas être appelé
        raise AssertionError("l'archive ne doit pas être ouverte sur un index sain")

    releve = backfill_texte_vise(index, _refuse)
    assert index.par_id[ID]["texte_vise"] == TEXTE_SOURCE_BTC
    assert releve == {
        "entrees_a_reparer": 0, "entrees_sans_texte_vise": 0,
        "entrees_corrigees": 0, "entrees_sans_source": 0,
        "legislatures_lues": 0, "legislatures_sans_source": 0,
    }


def test_le_report_ne_vide_rien_quand_larchive_ne_sait_pas():
    """Un amendement absent de l'archive garde son intitulé : un trou déclaré,
    jamais un trou creusé (AGENTS.md §2 règle 5)."""
    inconnu = "an:AMANR5L15PO717460B9999P0D1N000001"
    index = _index(**{inconnu: INTITULE_PUBLIE})
    releve = backfill_texte_vise(index, _lecteur())

    assert index.par_id[inconnu]["texte_vise"] == INTITULE_PUBLIE
    assert releve["entrees_a_reparer"] == 1
    assert releve["entrees_corrigees"] == 0
    assert releve["entrees_sans_source"] == 1


def test_le_report_compte_la_legislature_qui_na_pas_darchive():
    """Ce que le report ne peut pas réparer, nommé : la XVIIe est en cours et
    n'a pas d'archive figée. Le cas est aujourd'hui vide (0 des 96 893
    amendements publiés de la XVIIe), il n'est pas pour autant tu."""
    id_17 = "an:AMANR5L17PO59047BTC1376P0D1N000012"
    index = _index(**{id_17: INTITULE_PUBLIE})
    releve = backfill_texte_vise(index, _lecteur())

    assert index.par_id[id_17]["texte_vise"] == INTITULE_PUBLIE
    assert releve["legislatures_sans_source"] == 1
    assert releve["legislatures_lues"] == 0
    assert releve["entrees_sans_source"] == 1


def test_le_report_compte_une_absence_a_part_dun_intitule():
    """`entrees_sans_texte_vise` est un sous-ensemble de `entrees_a_reparer` :
    nommer la population de chaque chiffre (AGENTS.md §9)."""
    index = _index(**{ID: None, ID_REINTRODUIT: INTITULE_REINTRODUIT})
    releve = backfill_texte_vise(index, _lecteur())

    assert releve["entrees_a_reparer"] == 2
    assert releve["entrees_sans_texte_vise"] == 1
    assert releve["entrees_corrigees"] == 2
    assert index.par_id[ID]["texte_vise"] == TEXTE_SOURCE


def test_le_report_ne_touche_ni_les_autres_champs_ni_la_cle_de_fusion():
    """Élargir la clé pour y porter le champ corrigé est le défaut de #668 —
    468 doublons sur 940 entrées de `textes_portes`."""
    index = _index(**{ID: INTITULE_PUBLIE, ID_REINTRODUIT: INTITULE_REINTRODUIT})
    avant = set(index.par_id)
    backfill_texte_vise(index, _lecteur())

    assert set(index.par_id) == avant
    assert index.par_id[ID]["sort"] == "rejeté"
    assert index.par_id[ID]["numero"] == "629"
    assert set(index.par_id[ID]) == {"texte_vise", "sort", "numero"}


def test_le_report_ne_cree_aucune_entree_pour_ce_que_larchive_porte_en_plus():
    """L'archive fixture porte 4 enregistrements ; l'index n'en référence qu'un.
    Le report répare, il ne collecte pas."""
    index = _index(**{ID: INTITULE_PUBLIE})
    backfill_texte_vise(index, _lecteur())
    assert set(index.par_id) == {ID}


def test_le_report_est_idempotent():
    index = _index(**{ID: INTITULE_PUBLIE})
    backfill_texte_vise(index, _lecteur())
    releve = backfill_texte_vise(index, _lecteur())

    assert index.par_id[ID]["texte_vise"] == TEXTE_SOURCE
    assert releve["entrees_a_reparer"] == 0


def test_sans_lecteur_declare_rien_nest_relu_et_le_compte_le_dit():
    """Même convention que `table_textes=None` (#639) : un run sans archives ne
    perd rien et n'invente rien — mais il ne se tait pas."""
    index = _index(**{ID: INTITULE_PUBLIE})
    releve = backfill_texte_vise(index, None)

    assert index.par_id[ID]["texte_vise"] == INTITULE_PUBLIE
    assert releve["entrees_a_reparer"] == 1
    assert releve["entrees_sans_source"] == 1
    assert releve["legislatures_sans_source"] == 1


def test_une_entree_sans_uid_an_na_pas_de_source_a_relire():
    """Un amendement du Parlement européen n'a pas d'uid AN : l'archive, keyée
    par uid, n'a rien à en dire. Compté, jamais réparé au jugé."""
    index = AmendementsIndex({"ep:A9-0123/2021": {"texte_vise": INTITULE_PUBLIE}})
    releve = backfill_texte_vise(index, _lecteur())

    assert index.par_id["ep:A9-0123/2021"]["texte_vise"] == INTITULE_PUBLIE
    assert releve["entrees_sans_source"] == 1
    assert releve["legislatures_lues"] == 0


# ---------------------------------------------------------------------------
# 4. La transition — le test qui manquait à #492, #639 et #641
# ---------------------------------------------------------------------------

def test_transition_lindex_publie_avant_639_acquiert_luid_a_la_reconstruction(tmp_path):
    """Le cas réel, bout en bout : l'index publié porte l'intitulé, le profil
    brut aussi (les 13 399 paires fautives du corpus vivent dans **un seul**
    profil, `jean-luc-melenchon`), et la fusion additive laisse gagner
    « la nouvelle valeur si elle est renseignée » — un intitulé l'est.

    Sans le report, l'entrée garde son intitulé à chaque run. C'est l'étape que
    ni #492, ni #639, ni #641 ne testaient : les steps passaient, la transition
    perdait la donnée."""
    index_dir = tmp_path / "index"
    profils = tmp_path / "profils"
    ecrire(index_dir, _index(**{ID: INTITULE_PUBLIE}))
    _ecrire_profil(profils, "jean-luc-melenchon.json", [_brut(UID, INTITULE_PUBLIE)])

    sans_report = rafraichir(profils, index_dir)
    assert sans_report.par_id[ID]["texte_vise"] == INTITULE_PUBLIE, (
        "sans report, la fusion additive préserve l'intitulé — c'est le défaut")

    comptes: dict[str, int] = {}
    avec_report = rafraichir(
        profils, index_dir, lire_textes_vises=_lecteur(), comptes=comptes)
    assert avec_report.par_id[ID]["texte_vise"] == TEXTE_SOURCE
    assert comptes["entrees_corrigees"] == 1
    assert charger(index_dir).par_id[ID]["texte_vise"] == TEXTE_SOURCE


def test_transition_la_fusion_peut_reintroduire_lintitule_le_report_le_reprend(tmp_path):
    """L'autre sens, et il n'est pas hypothétique : `an:AMANR5L15PO59051B4857…`
    est porté avec son uid par **trois** profils bruts (`benedicte-taurine`,
    `caroline-fiat`, `francois-ruffin`) et avec l'intitulé par un quatrième —
    l'index publié porte l'intitulé, parce que le quatrième l'emporte par
    l'ordre des fichiers. La fusion ne conserve pas seulement le défaut, elle
    le réintroduit."""
    index_dir = tmp_path / "index"
    profils = tmp_path / "profils"
    ecrire(index_dir, _index(**{ID_REINTRODUIT: TEXTE_SOURCE_REINTRODUIT}))
    _ecrire_profil(profils, "caroline-fiat.json",
                   [_brut(UID_REINTRODUIT, TEXTE_SOURCE_REINTRODUIT)])
    _ecrire_profil(profils, "jean-luc-melenchon.json",
                   [_brut(UID_REINTRODUIT, INTITULE_REINTRODUIT)])

    sans_report = rafraichir(profils, index_dir)
    assert sans_report.par_id[ID_REINTRODUIT]["texte_vise"] == INTITULE_REINTRODUIT, (
        "sans report, la fusion réintroduit l'intitulé sur une entrée saine")

    avec_report = rafraichir(profils, index_dir, lire_textes_vises=_lecteur())
    assert avec_report.par_id[ID_REINTRODUIT]["texte_vise"] == TEXTE_SOURCE_REINTRODUIT


def test_le_report_precede_la_resolution_des_dossiers(tmp_path):
    """Un `texte_vise` réparé doit gagner son dossier dans le **même** run,
    sinon la correction ne se voit qu'à la reconstruction suivante — et le
    rattachement au dossier est tout l'objet de #696 (2 499 des 2 831 dépôts de
    `jean-luc-melenchon` sans dossier, mesuré le 01/09/2026)."""
    index_dir = tmp_path / "index"
    profils = tmp_path / "profils"
    ecrire(index_dir, _index(**{ID: INTITULE_PUBLIE}))
    profils.mkdir()

    index = rafraichir(
        profils, index_dir,
        table_textes={TEXTE_SOURCE: {"dossier_id": "DLR5L15N38565",
                                     "titre": "Système universel de retraite"}},
        lire_textes_vises=_lecteur(),
    )
    assert index.dossier_de(index.get(ID)) == "DLR5L15N38565"


# ---------------------------------------------------------------------------
# 5. Les deux chemins d'appel — la CI ne passe pas par le script
# ---------------------------------------------------------------------------

def test_les_deux_chemins_dappel_branchent_le_report():
    """`build_amendements_index_pivot.py` est le script en ligne de commande ;
    `generate_all_profiles._rafraichir_index_amendements` est ce que la CI
    appelle. Un report câblé sur le seul premier n'atteindrait jamais l'index
    publié — le piège de #657, « un consommateur que personne ne grep »."""
    for module in ("build_amendements_index_pivot.py", "generate_all_profiles.py"):
        source = (Path(__file__).resolve().parents[1] / "src" / module).read_text(
            encoding="utf-8")
        assert "lire_textes_vises=" in source, (
            f"{module} appelle `rafraichir` sans brancher le report de #696")


def test_le_report_est_actif_par_defaut_dans_la_ci():
    """La CI n'a pas de drapeau pour l'activer : il l'est. Un report derrière un
    interrupteur laisse le défaut armé (#510, sur le mode Syceron)."""
    source = (Path(__file__).resolve().parents[1] / "src"
              / "generate_all_profiles.py").read_text(encoding="utf-8")
    assert "lire_textes_vises=lire_textes_vises," in source


# ---------------------------------------------------------------------------
# 6. La règle de #431 tient toujours
# ---------------------------------------------------------------------------

def test_le_report_ne_rematerialise_pas_la_forme_plate():
    """`get()` rend l'objet partagé lui-même, avant comme après le report : le
    facteur ~21 et l'OOM de #377 ne reviennent pas par cette porte."""
    index = _index(**{ID: INTITULE_PUBLIE})
    partage = index.par_id[ID]
    backfill_texte_vise(index, _lecteur())
    assert index.get(ID) is partage


def test_la_fusion_garde_luid_repare_face_a_un_index_ancien():
    """`merge_amendements_index` laisse gagner la valeur renseignée du nouvel
    index : un index réparé fusionné avec un ancien porteur d'intitulé garde
    l'uid."""
    ancien = _index(**{ID: INTITULE_PUBLIE})
    nouveau = _index(**{ID: TEXTE_SOURCE})
    assert merge_amendements_index(ancien, nouveau).par_id[ID]["texte_vise"] == TEXTE_SOURCE


def test_construire_index_ne_juge_pas_le_texte_vise():
    """Le report est un maillon nommé, pas un filtre glissé dans la
    construction : `construire_index` republie ce que le profil brut porte, et
    c'est `backfill_texte_vise` — et lui seul — qui corrige."""
    index = construire_index([_brut(UID, INTITULE_PUBLIE)])
    assert index.par_id[ID]["texte_vise"] == INTITULE_PUBLIE


def test_le_module_ne_lit_pas_le_corpus_vivant():
    """AGENTS.md §3b : aucun test ne lit `pivot_data/` ni `raw_data/profiles/`.
    Les fixtures de ce fichier sont des réductions verbatim committées."""
    assert ARCHIVES_FIXTURE.is_dir()
    assert amendements_index.DEFAULT_AMENDEMENTS_DIR == Path("pivot_data") / "amendements"
