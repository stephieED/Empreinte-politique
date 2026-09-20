#!/usr/bin/env python3
"""
test_poser_mandats_anterieurs_860.py — La reprise qui pose `mandats_anterieurs`
sur les profils déjà écrits, et le critère de vérification qui a failli être
faux (#860).

#861 a livré la table relue et le champ dérivé, posé à chaque écriture de
profil. Aucun run n'ayant régénéré les profils depuis, le champ était absent des
32 profils de candidats déclarés au 12/09/2026 — et l'accueil, qui calcule sa
ligne « Mandat antérieur à la publication des données de l'Assemblée » en
filtrant ce champ, affichait une liste vide là où la table nomme cinq personnes.

Ce que ces tests verrouillent :

- **relu ≠ non relu** : un slug dans la table reçoit sa liste ; un slug absent
  reçoit `null` et son motif, parce qu'absent n'est pas « aucun » (§2 règle 5) ;
- **la population** : un membre de roster n'est pas touché — il ne publie pas de
  fiche, et les deux populations partagent un répertoire (#630) ;
- **le critère de `--verifier`**, qui est le test le plus important du fichier.
  Le premier jet comptait comme manquant l'absence de
  `mandats_anterieurs_non_resolu` — or c'est justement ce qu'un profil **relu**
  ne doit pas porter. La vérification échouait donc sur les cinq profils qu'elle
  venait de remplir correctement ;
- **la reprise ne dérive pas du pipeline** : ce qu'elle pose est ce que
  `appliquer_mandats_anterieurs` poserait, à l'octet près.

Aucun test ne lit `pivot_data/`, `raw_data/profiles/` ni le réseau : la racine
est construite dans `tmp_path`.
"""

from pathlib import Path
import importlib.util
import json
import sys

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from mandats_anterieurs import appliquer_mandats_anterieurs, charger_table  # noqa: E402


def _charger_script():
    chemin = RACINE / "scripts" / "poser_mandats_anterieurs_860.py"
    spec = importlib.util.spec_from_file_location("poser_860", chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


REPRISE = _charger_script()

LIGNE = {
    "institution": "assemblee_nationale",
    "libelle": "Députée des Deux-Sèvres",
    "legislature": "9",
    "debut": "1988-06-13",
    "fin": "1992-05-02",
    "source_url": "https://www2.assemblee-nationale.fr/sycomore/fiche?num_dept=6174",
    "verifie_le": "2026-09-11",
}


def _profil(slug, provenance="candidat_declare", **extra):
    profil = {
        "id": slug,
        "nom": slug.replace("-", " ").title(),
        "mandats": [],
        "meta": {"provenance": provenance},
    }
    profil.update(extra)
    return profil


def _racine(tmp_path, profils, table_candidats):
    """Une racine de dépôt minimale : des profils pivot et la table relue."""
    dossier = tmp_path / "pivot_data" / "profiles"
    dossier.mkdir(parents=True)
    for profil in profils:
        (dossier / f"{profil['id']}.pivot.json").write_text(
            json.dumps(profil, ensure_ascii=False), encoding="utf-8"
        )
    table = tmp_path / "raw_data"
    table.mkdir(parents=True)
    (table / "mandats_anterieurs.json").write_text(
        json.dumps({"_meta": {"description": "table d'essai"}, "candidats": table_candidats},
                   ensure_ascii=False),
        encoding="utf-8",
    )
    return tmp_path


def _lire(racine, slug):
    return json.loads(
        (racine / "pivot_data" / "profiles" / f"{slug}.pivot.json").read_text(encoding="utf-8")
    )


def test_un_candidat_relu_recoit_sa_liste_et_aucun_motif(tmp_path):
    racine = _racine(
        tmp_path,
        [_profil("segolene-royal")],
        {"segolene-royal": [LIGNE]},
    )
    REPRISE.poser(racine, ecrire=True)
    profil = _lire(racine, "segolene-royal")
    assert profil["mandats_anterieurs"] == [LIGNE]
    # Un profil relu ne porte PAS de motif : sa liste est complète.
    assert "mandats_anterieurs_non_resolu" not in profil


def test_un_candidat_absent_de_la_table_est_declare_non_relu(tmp_path):
    """Absent n'est pas « aucun » — §2 règle 5."""
    racine = _racine(tmp_path, [_profil("marine-tondelier")], {"segolene-royal": [LIGNE]})
    REPRISE.poser(racine, ecrire=True)
    profil = _lire(racine, "marine-tondelier")
    assert profil["mandats_anterieurs"] is None
    assert profil["mandats_anterieurs_non_resolu"] == {"motif": "non_relu"}


def test_un_membre_de_roster_n_est_pas_touche(tmp_path):
    """Les deux populations partagent le répertoire (#630) : seule la fiche publiée compte."""
    racine = _racine(
        tmp_path,
        [_profil("un-depute-de-roster", provenance="roster_groupe")],
        {"un-depute-de-roster": [LIGNE]},
    )
    rapport = REPRISE.poser(racine, ecrire=True)
    profil = _lire(racine, "un-depute-de-roster")
    assert "mandats_anterieurs" not in profil
    assert rapport["profils"] == 0


def test_le_dry_run_n_ecrit_rien(tmp_path):
    racine = _racine(tmp_path, [_profil("segolene-royal")], {"segolene-royal": [LIGNE]})
    rapport = REPRISE.poser(racine, ecrire=False)
    assert rapport["relus"] == 1
    assert "mandats_anterieurs" not in _lire(racine, "segolene-royal")


def test_verifier_ne_compte_pas_le_motif_absent_d_un_profil_relu(tmp_path):
    """Le test le plus important : le critère de `--verifier`.

    Le premier jet comptait comme manquant l'absence de
    `mandats_anterieurs_non_resolu`, que le profil relu ne doit justement pas
    porter. La vérification échouait donc sur les profils qu'elle venait de
    remplir — 5 sur 32, mesuré le 12/09/2026 sur le corpus réel.
    """
    racine = _racine(
        tmp_path,
        [_profil("segolene-royal"), _profil("marine-tondelier")],
        {"segolene-royal": [LIGNE]},
    )
    # Avant la reprise : les deux profils manquent le champ.
    assert REPRISE.poser(racine, ecrire=False)["manquants"] == 2

    REPRISE.poser(racine, ecrire=True)

    # Après : plus rien ne manque, le profil relu comme le non relu.
    rapport = REPRISE.poser(racine, ecrire=False)
    assert rapport["manquants"] == 0
    assert (rapport["relus"], rapport["non_relus"]) == (1, 1)


def test_la_reprise_pose_ce_que_le_pipeline_poserait(tmp_path):
    """La reprise avance la date, elle ne crée pas un second chemin."""
    racine = _racine(tmp_path, [_profil("segolene-royal"), _profil("nathalie-arthaud")],
                     {"segolene-royal": [LIGNE]})
    REPRISE.poser(racine, ecrire=True)

    # `appliquer_mandats_anterieurs` consomme la table NORMALISÉE que rend
    # `charger_table`, pas la forme du fichier : depuis #860 les deux diffèrent,
    # une entrée sans mandat portant son constat.
    table = charger_table(racine / "raw_data" / "mandats_anterieurs.json")
    for slug in ("segolene-royal", "nathalie-arthaud"):
        attendu = _profil(slug)
        appliquer_mandats_anterieurs(attendu, table)
        obtenu = _lire(racine, slug)
        assert obtenu["mandats_anterieurs"] == attendu["mandats_anterieurs"]
        assert obtenu.get("mandats_anterieurs_non_resolu") == attendu.get(
            "mandats_anterieurs_non_resolu"
        )


def test_la_reprise_ne_touche_aucun_autre_champ(tmp_path):
    racine = _racine(
        tmp_path,
        [_profil("segolene-royal", votes=[{"scrutin_id": "x"}], chambres=["AN"])],
        {"segolene-royal": [LIGNE]},
    )
    REPRISE.poser(racine, ecrire=True)
    profil = _lire(racine, "segolene-royal")
    assert profil["votes"] == [{"scrutin_id": "x"}]
    assert profil["chambres"] == ["AN"]
    assert profil["meta"] == {"provenance": "candidat_declare"}


def test_la_reprise_ne_reecrit_pas_un_profil_gele(tmp_path):
    """#760 : un profil gelé est conservé tel quel, et la passe des candidats
    déclarés ne le réécrit pas. La reprise non plus — sinon elle ferait ce que
    le run refuse de faire. Cas réel du 16/09/2026 : Jordan Bardella, dont la
    table porte le constat d'absence, et que rien ne régénère."""
    constat = {"source_url": "https://www2.assemblee-nationale.fr/sycomore/recherche",
               "constate_le": "2026-09-16", "methode": "relecture_humaine"}
    racine = _racine(tmp_path, [_profil("jordan-bardella"), _profil("selma-labib")],
                     {"jordan-bardella": {"mandats": [], "constat": constat},
                      "selma-labib": {"mandats": [], "constat": constat}})
    (racine / "raw_data" / "candidats.json").write_text(json.dumps({"candidats": [
        {"slug": "jordan-bardella", "statut": "decline"},
        {"slug": "selma-labib", "statut": "declare"},
    ]}), encoding="utf-8")

    avant = _lire(racine, "jordan-bardella")
    rapport = REPRISE.poser(racine, ecrire=True)

    assert _lire(racine, "jordan-bardella") == avant
    assert _lire(racine, "selma-labib")["mandats_anterieurs_constat"] == constat
    assert rapport["profils"] == 1
