"""La dernière adoption par l'Assemblée de chaque loi promulguée (#1320).

FIXTURES. Copies **intégrales** de dossiers des archives réelles, téléchargées
le 21/10/2026 — jamais inventées :

- `DLR5L17N50689` (archive XVIIe) : adoptée par scrutin public, le Sénat statue après ;
- `DLR5L17N50957` (XVIIe) : adoptée sans scrutin public, l'Assemblée statue en dernier ;
- `DLR5L16N46346` (XVIe) : considérée comme adoptée en lecture définitive (49.3) ;
- `DLR5L16N48839` (XVIe) : conclusions de CMP lues le même jour par les deux chambres ;
- `DLR5L16N47722` (XVIIe) : accord de CMP sans lecture de ses conclusions à l'Assemblée ;
- `DLR5L16N49726` (XVIIe) : un `voteRefs` qui désigne un scrutin du Sénat ;
- `monolithe_XIV_DLR5L14N33609.json` : la seule entrée `DLR5L14N33609` de
  l'archive monolithique de la XIVe, dans son emballage d'origine.
"""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))

import textes_promulgues as tp  # noqa: E402

FIXTURES = RACINE / "tests" / "fixtures" / "dossiers_promulgues"


def _dossier(uid: str) -> dict:
    return json.loads((FIXTURES / f"dossier_{uid}.json").read_text(encoding="utf-8"))["dossierParlementaire"]


def test_une_adoption_par_scrutin_public_porte_ses_scrutins_et_le_senat_apres():
    ligne = tp.entree(_dossier("DLR5L17N50689"), None)
    adoption = ligne["derniere_adoption_an"]

    assert adoption["mode"] == tp.MODE_SCRUTIN_PUBLIC
    assert adoption["scrutin_ids"] and all(s.startswith("an:17:") for s in adoption["scrutin_ids"])
    assert adoption["acte_uid"] and adoption["code_acte"] == "AN1-DEBATS-DEC"
    assert ligne["derniere_adoption_an_non_resolue"] is None
    assert ligne["senat_statue_apres"] is True
    assert ligne["date_derniere_decision_senat"] > adoption["date"]
    assert ligne["source_url"].startswith("https://www.assemblee-nationale.fr/dyn/17/dossiers/")


def test_sans_scrutin_public_ne_dit_rien_de_plus():
    """La source ne distingue pas main levée, assis et levé et procédure
    d'examen simplifiée : le mode ne le dit pas non plus."""
    ligne = tp.entree(_dossier("DLR5L17N50957"), None)
    adoption = ligne["derniere_adoption_an"]

    assert adoption["mode"] == tp.MODE_SANS_SCRUTIN_PUBLIC
    assert adoption["scrutin_ids"] is None
    assert ligne["senat_statue_apres"] is False
    assert "main lev" not in json.dumps(ligne, ensure_ascii=False).lower()


def test_un_49_3_n_est_jamais_un_vote():
    """§2 règle 4 : fait de procédure, aucune référence de scrutin. La date est
    celle de l'acte « considéré comme adopté » — ici le jour du vote de la
    dernière motion de censure (15/11/2023)."""
    ligne = tp.entree(_dossier("DLR5L16N46346"), None)
    adoption = ligne["derniere_adoption_an"]

    assert adoption["mode"] == tp.MODE_49_3
    assert adoption["scrutin_ids"] is None
    assert adoption["code_acte"] == "ANLDEF-DEBATS-DEC"
    assert adoption["date"] == "2023-11-15"
    assert "49" in adoption["libelle_statut"]


def test_le_49_3_ignore_un_voterefs_pose_par_la_source():
    dossier = _dossier("DLR5L16N46346")
    for acte in tp.iter_actes(dossier["actesLegislatifs"]):
        if acte.get("codeActe") == "ANLDEF-DEBATS-DEC":
            acte["voteRefs"] = {"voteRef": "VTANR5L16V1"}

    assert tp.entree(dossier, None)["derniere_adoption_an"]["scrutin_ids"] is None


def test_deux_decisions_le_meme_jour_ne_disent_pas_qui_a_statue_en_dernier():
    ligne = tp.entree(_dossier("DLR5L16N48839"), None)

    assert ligne["derniere_adoption_an"]["code_acte"] == "CMP-DEBATS-AN-DEC"
    assert ligne["senat_statue_apres"] is None
    assert ligne["senat_statue_apres_non_resolu"] == {"motif": "decisions_le_meme_jour"}
    assert ligne["date_derniere_decision_senat"] == ligne["derniere_adoption_an"]["date"]


def test_la_lecture_definitive_clot_la_navette_meme_le_jour_du_senat():
    dossier = _dossier("DLR5L16N46346")
    adoption, _ = tp.derniere_adoption_an(dossier)
    for acte in tp.iter_actes(dossier["actesLegislatifs"]):
        if tp.chambre_de_decision(acte.get("codeActe")) == "SN":
            acte["dateActe"] = adoption["date"] + "T00:00:00.000+01:00"

    assert tp.senat_apres(dossier, adoption)[0] is False


def test_un_accord_de_cmp_sans_lecture_a_l_assemblee_n_est_pas_comble():
    """La dernière adoption trouvée (29/01/2024, XVIe) n'est pas la dernière :
    la CMP s'est accordée en octobre 2024. La publier rattacherait la loi à la
    mauvaise législature."""
    ligne = tp.entree(_dossier("DLR5L16N47722"), None)

    assert ligne["derniere_adoption_an"] is None
    assert ligne["derniere_adoption_an_non_resolue"] == {"motif": "lecture_cmp_an_absente"}
    assert ligne["senat_statue_apres_non_resolu"] == {"motif": "adoption_an_non_resolue"}


def test_une_reference_de_scrutin_hors_assemblee_est_declaree():
    adoption = tp.entree(_dossier("DLR5L16N49726"), None)["derniere_adoption_an"]

    assert adoption["mode"] is None and adoption["scrutin_ids"] is None
    assert adoption["mode_non_resolu"] == {"motif": "scrutin_non_reconnu",
                                           "vote_refs": ["VTSNR5L17V844"]}
    assert adoption["date"] == "2025-02-20", "la date reste publiée"


def test_un_statut_inconnu_apres_l_adoption_la_rend_non_resolue():
    dossier = _dossier("DLR5L17N50957")
    for acte in tp.iter_actes(dossier["actesLegislatifs"]):
        if tp.chambre_de_decision(acte.get("codeActe")) == "AN":
            acte["statutConclusion"] = {"fam_code": "TSORTF99", "libelle": "?"}
            break
    adoption, motif = tp.derniere_adoption_an(dossier)

    assert adoption is None and motif in tp.KNOWN_MOTIFS_ADOPTION_AN_NON_RESOLUE


def test_les_valeurs_publiees_sont_dans_les_vocabulaires_fermes():
    for uid in ("DLR5L17N50689", "DLR5L17N50957", "DLR5L16N46346", "DLR5L16N48839",
                "DLR5L16N47722", "DLR5L16N49726", "DLR5L17N52781", "DLR5L17N53940"):
        ligne = tp.entree(_dossier(uid), None)
        adoption, motif = ligne["derniere_adoption_an"], ligne["derniere_adoption_an_non_resolue"]
        assert (adoption is None) != (motif is None), uid
        if adoption:
            assert (adoption["mode"] is None) != (adoption["mode_non_resolu"] is None), uid
            assert adoption["mode"] in tp.KNOWN_MODES_ADOPTION_AN | {None}
        else:
            assert motif["motif"] in tp.KNOWN_MOTIFS_ADOPTION_AN_NON_RESOLUE
        apres, non_resolu = ligne["senat_statue_apres"], ligne["senat_statue_apres_non_resolu"]
        assert (apres is None) == (non_resolu is not None), uid
        if non_resolu:
            assert non_resolu["motif"] in tp.KNOWN_MOTIFS_SENAT_APRES_NON_RESOLU


def test_l_archive_monolithique_de_la_xive_est_lue(tmp_path):
    archive = tmp_path / "Dossiers_Legislatifs_XIV.json.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.write(FIXTURES / "monolithe_XIV_DLR5L14N33609.json", "Dossiers_Legislatifs_XIV.json")

    table = tp.construire_table([(14, archive)], {})

    ligne = table["DLR5L14N33609"]
    assert ligne["derniere_adoption_an"]["mode"] == tp.MODE_SANS_SCRUTIN_PUBLIC
    assert ligne["senat_statue_apres"] is True
    assert ligne["source_url"].startswith("https://www.assemblee-nationale.fr/dyn/14/dossiers/")


def test_une_entree_deja_publiee_recoit_les_nouveaux_champs(tmp_path, monkeypatch):
    """La fusion remplace l'entrée d'un dossier relu : celle d'un run antérieur à
    #1320 gagne ses champs au prochain run, et un dossier non relu est gardé."""
    archive = tmp_path / "17.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.write(FIXTURES / "dossier_DLR5L17N50689.json", "json/dossierParlementaire/DLR5L17N50689.json")
    monkeypatch.setattr(tp, "ensure_dossiers_zips_downloaded", lambda: [(17, archive)])
    chemin = tmp_path / "textes_promulgues.json"
    chemin.write_text(json.dumps({"textes": {
        "DLR5L17N50689": {"titre": "ancienne forme"},
        "DLR5L99N00001": {"titre": "non relu"},
    }}), encoding="utf-8")

    assert tp.main(["--out", str(chemin), "--commissions", str(tmp_path / "x.json"),
                    "--table-lois", str(tmp_path / "y.json")]) == 0
    textes = json.loads(chemin.read_text(encoding="utf-8"))["textes"]

    assert textes["DLR5L17N50689"]["derniere_adoption_an"]["mode"] == tp.MODE_SCRUTIN_PUBLIC
    assert textes["DLR5L99N00001"] == {"titre": "non relu"}
