#!/usr/bin/env python3
"""
Tests du lot #836 — génération des fiches de lignée.

Un fichier par lot (#840). Ce qu'ils vérifient, et pourquoi chacun existe :

- la **partition déclarée** (`groupes[].lignee_id`) et la **chaîne écrite**
  (`succede_a`) disent le même fait par deux chemins. Le test le mesure sur la
  configuration réellement committée, parce que c'est là qu'une main l'écrit —
  et c'est le défaut que #815 a payé, où seule l'une des deux listes du fichier
  avait été corrigée ;
- une succession qui traverse deux lignées est **refusée**. C'est la porte qui
  tient une scission tant que sa forme n'est pas tranchée — un cas abstrait :
  celui qu'on croyait tenir, `AD`/`DR`, a été infirmé par la mesure (#815) ;
- un maillon déclaré sans fiche publiée est **refusé**, pas publié amputé ;
- l'union dédoublonne réellement, sur une chaîne complète et non sur un appel
  isolé — la leçon de #809, dont les tests sautaient le filtre qui jetait le
  champ.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from generate_lignee_profiles import (  # noqa: E402
    LigneeIncoherente,
    appartenances_declarees,
    charger_fiches_groupes,
    generate_all,
    verifier_partition,
)
from groupes_config import LigneeConfigInvalide, charger_lignees  # noqa: E402
from lignee_profile import ordonner_maillons  # noqa: E402
from schema_lignee import validate_profil_lignee  # noqa: E402

pytestmark = pytest.mark.lit_reference_committee("raw_data/groupes_reels.json")

CONFIG_COMMITTEE = RACINE / "raw_data" / "groupes_reels.json"


# ---------------------------------------------------------------------------
# La configuration committée
# ---------------------------------------------------------------------------

def _document() -> dict:
    return json.loads(CONFIG_COMMITTEE.read_text(encoding="utf-8"))


def test_chaque_groupe_declare_une_lignee_qui_existe():
    """`charger_lignees` valide la configuration réelle, sans exception."""
    lignees = charger_lignees(CONFIG_COMMITTEE)
    assert lignees, "aucune lignée déclarée"
    declarees = {l["lignee_id"] for l in lignees}
    for groupe in _document()["groupes"]:
        assert groupe["lignee_id"] in declarees, groupe["groupe_id"]


def test_la_partition_declaree_est_celle_de_la_chaine_ecrite():
    """L'appartenance déclarée coïncide avec les composantes de `succede_a`.

    Les deux vivent dans le même fichier et disent le même fait : `lignee_id`
    sur chaque entrée de `groupes[]`, `succede_a` sur chaque entrée de
    `correspondance_sigles_an.groupes`. Rien n'oblige un humain à les garder
    d'accord — sinon ce test, et le contrôle homonyme du script.

    Mesuré le 11/09/2026 : **23 fiches publiées, 10 composantes**, soit
    exactement les 10 lignées déclarées.
    """
    document = _document()
    appartenance = {
        g["groupe_id"]: g["lignee_id"]
        for g in document["groupes"]
        if g.get("groupe_id")
    }
    parent = {gid: gid for gid in appartenance}

    def racine(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for entree in document["correspondance_sigles_an"]["groupes"]:
        gid = entree.get("groupe_id")
        if gid not in parent:
            continue
        for cible in entree.get("succede_a") or []:
            if cible in parent:
                a, b = racine(gid), racine(cible)
                if a != b:
                    parent[a] = b

    composantes: dict[str, set[str]] = {}
    for gid in appartenance:
        composantes.setdefault(racine(gid), set()).add(gid)

    par_lignee: dict[str, set[str]] = {}
    for gid, lignee in appartenance.items():
        par_lignee.setdefault(lignee, set()).add(gid)

    assert sorted(map(sorted, composantes.values())) == sorted(
        map(sorted, par_lignee.values())
    ), (
        "la partition déclarée par `lignee_id` n'est pas celle que `succede_a` "
        "dessine : l'une des deux écritures a bougé sans l'autre (#815)."
    )
    assert len(par_lignee) == len(charger_lignees(CONFIG_COMMITTEE))


def test_un_fichier_de_lignee_par_lignee_et_aucun_doublon():
    lignees = charger_lignees(CONFIG_COMMITTEE)
    fichiers = [l["fichier"] for l in lignees]
    assert len(set(fichiers)) == len(fichiers)
    for lignee in lignees:
        assert lignee["fichier"].startswith("lignee-")
        assert lignee["fichier"].endswith(".json")


# ---------------------------------------------------------------------------
# Les refus de `charger_lignees`
# ---------------------------------------------------------------------------

def _config_minimale(tmp_path: Path, **surcharges) -> Path:
    document = {
        "lignees": [
            {"lignee_id": "AN:LIGNEE:X", "lignee_nom": "X", "chambre": "AN",
             "fichier": "lignee-AN-X.json", "verifie_le": "2026-09-11"},
        ],
        "groupes": [
            {"groupe_id": "AN:X:16", "lignee_id": "AN:LIGNEE:X", "chambre": "AN",
             "groupe_sigle": "X", "groupe_nom": "X", "legislature": "16",
             "roster_chambre": "deputes", "fichier": "groupe-AN-X-16.json"},
        ],
    }
    document.update(surcharges)
    chemin = tmp_path / "groupes_reels.json"
    chemin.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    return chemin


def test_une_lignee_sans_identifiant_est_refusee(tmp_path):
    chemin = _config_minimale(tmp_path, lignees=[
        {"lignee_nom": "X", "chambre": "AN", "fichier": "f.json", "verifie_le": "2026-09-11"},
    ])
    with pytest.raises(LigneeConfigInvalide, match="clé\\(s\\) exigée\\(s\\)"):
        charger_lignees(chemin)


def test_deux_lignees_de_meme_identifiant_sont_refusees(tmp_path):
    entree = {"lignee_id": "AN:LIGNEE:X", "lignee_nom": "X", "chambre": "AN",
              "fichier": "f.json", "verifie_le": "2026-09-11"}
    chemin = _config_minimale(tmp_path, lignees=[entree, dict(entree)])
    with pytest.raises(LigneeConfigInvalide, match="déclaré deux fois"):
        charger_lignees(chemin)


def test_un_groupe_sans_lignee_est_refuse(tmp_path):
    chemin = _config_minimale(tmp_path, groupes=[
        {"groupe_id": "AN:X:16", "chambre": "AN"},
    ])
    with pytest.raises(LigneeConfigInvalide, match="ne déclare pas de 'lignee_id'"):
        charger_lignees(chemin)


def test_une_lignee_que_personne_ne_nomme_est_refusee(tmp_path):
    chemin = _config_minimale(tmp_path, lignees=[
        {"lignee_id": "AN:LIGNEE:X", "lignee_nom": "X", "chambre": "AN",
         "fichier": "f.json", "verifie_le": "2026-09-11"},
        {"lignee_id": "AN:LIGNEE:ORPHELINE", "lignee_nom": "O", "chambre": "AN",
         "fichier": "o.json", "verifie_le": "2026-09-11"},
    ])
    with pytest.raises(LigneeConfigInvalide, match="nommées par aucun groupe"):
        charger_lignees(chemin)


def test_un_groupe_dans_la_mauvaise_chambre_est_refuse(tmp_path):
    chemin = _config_minimale(tmp_path, groupes=[
        {"groupe_id": "Senat:X", "lignee_id": "AN:LIGNEE:X", "chambre": "Senat"},
    ])
    with pytest.raises(LigneeConfigInvalide, match="chambre"):
        charger_lignees(chemin)


# ---------------------------------------------------------------------------
# La partition contre la chaîne — la porte qui tiendrait une scission
# ---------------------------------------------------------------------------

def _fiche(groupe_id, legislature, membres, succede_a=None, cohesion=()):
    return {
        "groupe_id": groupe_id,
        "groupe_sigle": groupe_id.split(":")[1],
        "groupe_nom": groupe_id,
        "chambre": "AN",
        "legislature": legislature,
        "periode": {"debut": f"20{legislature}-01-01", "fin": f"20{legislature}-12-31"},
        "membres": [
            {"membre_id": m, "nom": m, "debut_dans_groupe": f"20{legislature}-01-01",
             "fin_dans_groupe": f"20{legislature}-12-31"}
            for m in membres
        ],
        "cohesion_votes": [{"scrutin_id": s} for s in cohesion],
        "mandats_agreges": [],
        "tags_thematiques_agreges": [],
        "amendements_agreges": {},
        "sources": [],
        "succede_a": [{"groupe_id": g} for g in (succede_a or [])] or None,
        "position_politique": None,
    }


def test_une_succession_qui_traverse_deux_lignees_est_refusee():
    """Une succession entre deux lignées déclarées échoue plutôt que d'être absorbée.

    Sigles neutres, et c'est voulu : l'exemple portait `DR` et `UDR`, un cas que
    la mesure du 11/09/2026 a infirmé (#815). Un test ne met pas de vrais
    sigles sur un fait inventé.
    """
    fiches = {
        "AN:B:17": _fiche("AN:B:17", "17", ["a"], succede_a=["AN:A:16"]),
        "AN:A:16": _fiche("AN:A:16", "16", ["a"]),
    }
    appartenances = {"AN:B:17": "AN:LIGNEE:Y", "AN:A:16": "AN:LIGNEE:X"}
    with pytest.raises(LigneeIncoherente, match="SCISSION"):
        verifier_partition(fiches, appartenances)


def test_un_predecesseur_hors_du_corpus_nest_pas_une_faute():
    """Le périmètre du dépôt n'est pas un trou (§2 règle 5)."""
    fiches = {"AN:LR:16": _fiche("AN:LR:16", "16", ["a"], succede_a=["AN:LR:14"])}
    verifier_partition(fiches, {"AN:LR:16": "AN:LIGNEE:LR"})


def test_un_cycle_dans_la_chaine_est_refuse():
    fiches = {
        "AN:A:16": _fiche("AN:A:16", "16", ["a"], succede_a=["AN:B:17"]),
        "AN:B:17": _fiche("AN:B:17", "17", ["a"], succede_a=["AN:A:16"]),
    }
    with pytest.raises(ValueError, match="cycle"):
        ordonner_maillons(fiches, ["AN:A:16", "AN:B:17"])


# ---------------------------------------------------------------------------
# La chaîne complète, du disque au fichier écrit
# ---------------------------------------------------------------------------

def _corpus(tmp_path: Path, fiches: list[dict]) -> tuple[Path, Path, Path]:
    groupes_dir = tmp_path / "groupes"
    groupes_dir.mkdir()
    for fiche in fiches:
        nom = "groupe-" + fiche["groupe_id"].replace(":", "-") + ".json"
        (groupes_dir / nom).write_text(json.dumps(fiche, ensure_ascii=False), encoding="utf-8")
    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir()
    return groupes_dir, profiles_dir, tmp_path / "out"


def _config(tmp_path: Path, groupes: list[tuple[str, str]]) -> Path:
    chemin = tmp_path / "config.json"
    chemin.write_text(json.dumps({
        "lignees": [{"lignee_id": "AN:LIGNEE:T", "lignee_nom": "T", "chambre": "AN",
                     "fichier": "lignee-AN-T.json", "verifie_le": "2026-09-11"}],
        "groupes": [
            {"groupe_id": gid, "lignee_id": "AN:LIGNEE:T", "chambre": "AN",
             "legislature": leg}
            for gid, leg in groupes
        ],
    }, ensure_ascii=False), encoding="utf-8")
    return chemin


def test_deux_maillons_de_la_meme_legislature_ne_comptent_pas_deux_fois(tmp_path):
    """L'union sur `membre_id` et sur `scrutin_id`, sur la chaîne réelle.

    C'est le cas `NG:15` / `SOC:15` : deux maillons d'une MÊME législature, les
    seuls du corpus qui se recouvrent. Mesuré sur la lignée socialiste réelle,
    170 entrées de maillon pour 96 personnes et 20 524 scrutins pour 16 420.
    """
    fiches = [
        _fiche("AN:NG:15", "15", ["alice", "bob"], cohesion=["s1", "s2"]),
        _fiche("AN:SOC:15", "15", ["bob", "carole"], succede_a=["AN:NG:15"],
               cohesion=["s2", "s3"]),
    ]
    groupes_dir, profiles_dir, out_dir = _corpus(tmp_path, fiches)
    config = _config(tmp_path, [("AN:NG:15", "15"), ("AN:SOC:15", "15")])

    resultat = generate_all(
        groupes_dir=groupes_dir, profiles_dir=profiles_dir, out_dir=out_dir,
        chemin_config=config, amendements_path=tmp_path / "absent", validate=True,
    )
    assert resultat.echecs == []
    profil = json.loads((out_dir / "lignee-AN-T.json").read_text(encoding="utf-8"))

    assert [m["membre_id"] for m in profil["membres"]] == ["alice", "bob", "carole"]
    assert profil["effectif"]["cumul_historique"] == 3
    assert sorted(v["scrutin_id"] for v in profil["cohesion_votes"]) == ["s1", "s2", "s3"]
    assert [m["groupe_id"] for m in profil["maillons"]] == ["AN:NG:15", "AN:SOC:15"]
    assert validate_profil_lignee(profil) == []


def test_un_maillon_sans_fiche_publiee_refuse_la_lignee(tmp_path):
    """Amputée, la lignée sortirait des chiffres plus petits sans le dire."""
    groupes_dir, profiles_dir, out_dir = _corpus(
        tmp_path, [_fiche("AN:NG:15", "15", ["alice"])]
    )
    config = _config(tmp_path, [("AN:NG:15", "15"), ("AN:SOC:15", "15")])
    resultat = generate_all(
        groupes_dir=groupes_dir, profiles_dir=profiles_dir, out_dir=out_dir,
        chemin_config=config, amendements_path=tmp_path / "absent", validate=True,
    )
    assert resultat.ecrites == []
    assert len(resultat.echecs) == 1
    assert "AN:SOC:15" in resultat.echecs[0][1]
    assert not (out_dir / "lignee-AN-T.json").exists()


def test_la_fiche_est_ecrite_compacte(tmp_path):
    """#433 : le critère est « relu à la main », et une lignée pèse jusqu'à 11,5 Mo."""
    groupes_dir, profiles_dir, out_dir = _corpus(
        tmp_path, [_fiche("AN:NG:15", "15", ["alice"])]
    )
    config = _config(tmp_path, [("AN:NG:15", "15")])
    generate_all(
        groupes_dir=groupes_dir, profiles_dir=profiles_dir, out_dir=out_dir,
        chemin_config=config, amendements_path=tmp_path / "absent",
    )
    texte = (out_dir / "lignee-AN-T.json").read_text(encoding="utf-8")
    assert "\n" not in texte
    assert '", "' not in texte  # séparateurs compacts


def test_le_compteur_est_le_cardinal_de_lunion_jamais_une_somme():
    """`validate_profil_lignee` refuse la contradiction entre les deux champs."""
    from schema_lignee import make_empty_profil_lignee

    profil = make_empty_profil_lignee("AN:LIGNEE:T", "T", "AN")
    profil["maillons"] = [{"groupe_id": "AN:NG:15"}]
    profil["membres"] = [{"membre_id": "alice"}, {"membre_id": "bob"}]
    profil["effectif"] = {"cumul_historique": 4}
    erreurs = validate_profil_lignee(profil)
    assert any("CARDINAL" in e for e in erreurs), erreurs


def test_une_lignee_sans_maillon_ne_decrit_rien():
    from schema_lignee import make_empty_profil_lignee

    profil = make_empty_profil_lignee("AN:LIGNEE:T", "T", "AN")
    assert any("maillon" in e for e in validate_profil_lignee(profil))


# ---------------------------------------------------------------------------
# Les lectures de disque du script
# ---------------------------------------------------------------------------

def test_charger_fiches_groupes_indexe_par_groupe_id(tmp_path):
    groupes_dir, _, _ = _corpus(tmp_path, [
        _fiche("AN:NG:15", "15", ["alice"]),
        _fiche("AN:SOC:15", "15", ["bob"]),
    ])
    fiches = charger_fiches_groupes(groupes_dir)
    assert sorted(fiches) == ["AN:NG:15", "AN:SOC:15"]


def test_appartenances_declarees_lit_la_configuration(tmp_path):
    config = _config(tmp_path, [("AN:NG:15", "15")])
    assert appartenances_declarees(config) == {"AN:NG:15": "AN:LIGNEE:T"}


def test_lagregat_de_lignee_porte_les_memes_noms_que_celui_dune_fiche_de_groupe(tmp_path):
    """Un même fait ne se publie pas sous deux noms selon la collection.

    La première rédaction de `recalculer_agregats` écrivait
    `nb_amendements_sans_identifiant` là où toute la chaîne — fiche de groupe,
    contrôle de perte, audit — lit `nb_sans_identifiant`, et ne publiait ni
    `signatures` (§6) ni `taux_adoption`. Elle n'était couverte par aucun test :
    le lot qui l'a posée n'en a écrit aucun sur elle.
    """
    groupes_dir, profiles_dir, out_dir = _corpus(
        tmp_path, [_fiche("AN:NG:15", "15", ["alice"])]
    )
    (profiles_dir / "alice.pivot.json").write_text(json.dumps({
        "schema_version": "1", "id": "alice", "nom": "Alice",
        "amendements": [
            {"amendement_id": "AMANR5L15X1", "sort": "adopté", "type_deposant": "depute"},
            {"amendement_id": "AMANR5L15X1", "sort": "adopté", "type_deposant": "depute"},
            {"amendement_id": "AMANR5L15X2", "sort": "rejeté", "type_deposant": "depute"},
        ],
    }, ensure_ascii=False), encoding="utf-8")

    config = _config(tmp_path, [("AN:NG:15", "15")])
    generate_all(
        groupes_dir=groupes_dir, profiles_dir=profiles_dir, out_dir=out_dir,
        chemin_config=config, amendements_path=tmp_path / "absent", validate=True,
    )
    agrege = json.loads(
        (out_dir / "lignee-AN-T.json").read_text(encoding="utf-8")
    )["amendements_agreges"]

    assert "nb_sans_identifiant" in agrege
    assert "nb_amendements_sans_identifiant" not in agrege
    # Deux signatures du même amendement : UN amendement distinct (#643).
    assert agrege["nb_amendements"] == 2
    assert agrege["signatures"]["nb_signatures"] == 3
    assert agrege["taux_adoption"] == 0.5
