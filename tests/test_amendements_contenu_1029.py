"""#1029, voie 2 — l'article visé et l'index de mots de l'exposé des amendements.

Le besoin : TROUVER les amendements d'un sujet (« carburant »), que l'intitulé
du dossier (« projet de loi de finances ») ne nomme jamais. Mesuré le
22/09/2026 sur l'archive de la XVIIe : 624 amendements dont l'exposé contient
`carbur*` ou `ticpe`, 0 trouvable avant ce lot.

Les deux fixtures sont des RÉDUCTIONS d'amendements réels, champs lus
seulement : `AMANR5L17PO419604B0324P2D1N000013` (XVIIe, un fichier par
amendement, « ÉTAT B » d'une loi de finances) et
`AMANR5L14SEA644420B0013P0D1N7` (XIVe, forme héritée : un seul JSON).
"""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))

import amendements_contenu as ac  # noqa: E402
import build_amendements_index as bai  # noqa: E402
import build_amendements_index_pivot as baip  # noqa: E402
from amendements_index import AmendementsIndex, charger, poser_articles  # noqa: E402

FIXTURES = RACINE / "tests" / "fixtures"
LEG17 = json.loads((FIXTURES / "amendement_reel_leg17_carburant.json").read_text(encoding="utf-8"))
LEG14 = json.loads((FIXTURES / "amendements_reel_leg14_forme_heritee.json").read_text(encoding="utf-8"))


def _zip(tmp_path, fichiers):
    chemin = tmp_path / "archive.zip"
    with zipfile.ZipFile(chemin, "w") as z:
        for nom, contenu in fichiers.items():
            z.writestr(nom, json.dumps(contenu, ensure_ascii=False))
    return chemin


# ── Ce qu'on lit dans l'archive ──────────────────────────────────────────

def test_les_mots_de_l_expose_sans_html_ni_accents():
    mots = ac.mots_du_texte(LEG17["amendement"]["corps"]["contenuAuteur"]["exposeSommaire"])

    assert any(m.startswith("carbur") for m in mots)
    assert "present" in mots  # « présent », désaccentué
    assert not any(len(m) < 4 for m in mots)
    assert not any("<" in m or "&" in m for m in mots)


def test_l_article_vise_est_celui_que_la_source_ecrit():
    assert ac.article_vise(LEG17["amendement"]) == ["ÉTAT B", "A"]


def test_les_deux_formes_d_archive_se_lisent(tmp_path):
    chemin = _zip(tmp_path, {
        "json/AMANR5L17PO419604B0324P2D1N000013.json": LEG17,
        "Amendements_XIV.json": LEG14,
    })

    contenu = ac.lire_archive(chemin)

    assert set(contenu) == {"AMANR5L17PO419604B0324P2D1N000013", "AMANR5L14SEA644420B0013P0D1N7"}
    article14, mots14 = contenu["AMANR5L14SEA644420B0013P0D1N7"]
    assert article14 == ["Article 3", "A"]
    assert "ondam" in mots14  # exposé sous `corps`, pas sous `contenuAuteur`


# ── Le fichier publié ────────────────────────────────────────────────────

def test_les_renvois_se_decodent_a_l_identique():
    positions = [0, 3, 13, 14, 1000, 99999]
    assert ac.decoder(ac._encoder(positions)) == positions
    assert ac._encoder([3, 13, 14]) == "3,a,1"


def _position(doc, uid):
    return doc["ids"].index(uid[len(doc["prefixe_ids"]):])


def test_un_mot_trop_frequent_n_est_pas_indexe():
    """« amendement » dans chaque exposé : il ne servirait à aucune recherche."""
    contenu = {f"AMANR5L17X{n:03d}": (None, {"amendement", f"sujet{n:03d}"}) for n in range(40)}
    contenu["AMANR5L17X999"] = (["Article 1", "A"], {"amendement", "carburant"})

    doc = ac.document("17", contenu, genere_le="2026-09-22")

    assert "amendement" not in doc["mots"]
    assert ac.decoder(doc["mots"]["carburant"]) == [_position(doc, "AMANR5L17X999")]
    assert doc["articles"][_position(doc, "AMANR5L17X999")] == ["Article 1", "A"]


def test_le_seuil_est_de_3_pour_cent_apres_fusion():
    """Un mot dans 2 amendements sur 50 (4 %) disparaît ; dans 1 sur 50, il reste."""
    contenu = {f"AMANR5L17Y{n:03d}": (None, {f"sujet{n:03d}"}) for n in range(50)}
    contenu["AMANR5L17Y000"] = (None, {"taxe", "sujet000"})
    contenu["AMANR5L17Y001"] = (None, {"taxes", "sujet001", "ticpe"})

    doc = ac.document("17", contenu)

    assert "taxe" not in doc["mots"] and "taxes" not in doc["mots"]  # 2 / 50 une fois fusionnés
    assert "ticpe" in doc["mots"]


def test_les_formes_se_fusionnent_sur_une_forme_presente_dans_l_index():
    vocabulaire = {"carburant", "carburants", "fiscal", "fiscale", "fiscales", "fiscaux", "publiques"}

    assert ac.forme_indexee("carburants", vocabulaire) == "carburant"
    assert {ac.forme_indexee(m, vocabulaire) for m in ("fiscale", "fiscales", "fiscaux")} == {"fiscal"}
    assert ac.forme_indexee("publiques", vocabulaire) == "publiques"  # « public » absent : rien de deviné


def test_une_recherche_retrouve_les_deux_formes():
    contenu = {f"AMANR5L17Z{n:03d}": (None, {f"sujet{n:03d}"}) for n in range(100)}
    contenu["AMANR5L17Z000"] = (None, {"carburant", "sujet000"})
    contenu["AMANR5L17Z001"] = (None, {"carburants", "sujet001"})

    doc = ac.document("17", contenu)

    cle = ac.forme_indexee("carburants", doc["mots"])
    assert [ac.uid_complet(doc, p) for p in ac.decoder(doc["mots"][cle])] == [
        "AMANR5L17Z000", "AMANR5L17Z001"]
    assert doc["prefixe_ids"] == "AMANR5L17" and doc["ids"][0] == "Z000"


# ── Le pipeline ──────────────────────────────────────────────────────────

def test_le_contenu_construit_est_publie_et_donne_ses_articles(tmp_path):
    cache, out = tmp_path / "cache", tmp_path / "out"
    doc = ac.document("17", {"AMANR5L17PO419604B0324P2D1N000013": (["ÉTAT B", "A"], {"carburant"})})
    ac.chemin_cache("17", cache).parent.mkdir(parents=True)
    ac.chemin_cache("17", cache).write_text(json.dumps(doc), encoding="utf-8")

    articles = baip.publier_contenus(out, cache)

    assert ac.charger(ac.chemin_publie("17", out))["ids"] == doc["ids"]
    assert articles == {"AMANR5L17PO419604B0324P2D1N000013": ["ÉTAT B", "A"]}


def test_une_legislature_close_se_relit_dans_le_fichier_publie(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    doc = ac.document("14", {"AMANR5L14SEA644420B0013P0D1N7": (["Article 3", "A"], {"ondam"})})
    ac.chemin_publie("14", out).write_text(json.dumps(doc), encoding="utf-8")

    assert baip.publier_contenus(out, tmp_path / "cache_vide") == {
        "AMANR5L14SEA644420B0013P0D1N7": ["Article 3", "A"]}


def test_l_article_est_pose_sur_l_index_publie():
    index = AmendementsIndex({"an:AMANR5L17PO419604B0324P2D1N000013": {"numero": "13"}})

    assert poser_articles(index, {"AMANR5L17PO419604B0324P2D1N000013": ["ÉTAT B", "A"]}) == 1
    assert index.par_id["an:AMANR5L17PO419604B0324P2D1N000013"]["article"] == ["ÉTAT B", "A"]


def test_le_fichier_de_contenu_n_est_pas_lu_comme_une_legislature(tmp_path):
    (tmp_path / "17.contenu.json").write_text(json.dumps(
        {"schema_version": ac.SCHEMA_VERSION, "amendements": {"x": {}}}), encoding="utf-8")

    assert charger(tmp_path, avec_cosignatures=False).legislatures() == []


def test_une_seule_legislature_close_est_construite_par_run(tmp_path, monkeypatch):
    monkeypatch.setattr(bai, "AMENDEMENTS_CACHE_DIR", tmp_path / "cache")
    telechargees = []

    def telecharger(url, chemin, leg, **bornes):
        # `**bornes` : le téléchargeur reçoit `budget_secondes` depuis #1100, et
        # un faux à la signature figée ferait échouer la construction.
        telechargees.append(leg)
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_bytes(b"")

    monkeypatch.setattr(bai, "_download_amendements_zip", telecharger)
    monkeypatch.setattr(bai, "ecrire_contenu_cache", lambda leg, chemin, cache: None)
    publie = tmp_path / "publie"
    publie.mkdir()
    (publie / "14.contenu.json").write_text("{}", encoding="utf-8")

    assert bai.construire_un_contenu_fige(publie) is True
    assert telechargees == ["15"]  # la XIVe est déjà publiée ; une seule par run


# ── L'étalement sur disque (#1115 bis) ───────────────────────────────────


def test_les_deux_fabriques_rendent_le_meme_document(tmp_path):
    """La garde de l'étalement : même archive, même document, au bit près.

    `document_depuis_archive` réordonne tout le calcul — comptage avant
    fusion, inversion par seaux — pour ne plus tenir l'archive en mémoire. Un
    seul écart, et le corpus publié dépendrait de la fabrique employée.
    """
    entrees = {"Amendements_XIV.json": LEG14}
    for n in range(40):
        entrees[f"json/A{n:03d}.json"] = {"amendement": {
            "uid": f"AMANR5L17X{n:03d}",
            "pointeurFragmentTexte": {"division": {"titre": f"Article {n}", "avant_A_Apres": "A"}},
            "corps": {"contenuAuteur": {"exposeSommaire":
                      f"<p>Le présent amendement vise les carburants fiscaux du sujet{n:03d}.</p>"}},
        }}
    chemin = _zip(tmp_path, entrees)

    en_memoire = ac.document("17", ac.lire_archive(chemin), genere_le="2026-09-24")
    par_seaux = ac.document_depuis_archive("17", chemin, genere_le="2026-09-24")

    assert par_seaux == en_memoire


def test_le_temporaire_ne_survit_pas_a_la_construction(tmp_path):
    """Un seau oublié, et un run de CI remplit son disque au fil des archives."""
    chemin = _zip(tmp_path, {"json/A000.json": LEG17})
    atelier = tmp_path / "atelier"

    ac.document_depuis_archive("17", chemin, repertoire=atelier)

    assert atelier.exists(), "un répertoire fourni par l'appelant lui appartient"
    assert list(atelier.glob("seau-*.tsv")) == [], "les seaux ne sont pas nettoyés"
    assert not (atelier / "exposes.tsv").exists(), "le fichier d'exposés reste sur disque"


def test_le_seau_d_une_forme_ne_depend_pas_du_processus():
    """`hash()` d'une chaîne est randomisé par Python : deux exécutions
    rangeraient la même forme dans deux seaux, et les positions d'un mot
    seraient réparties sur plusieurs fichiers."""
    assert ac.hash_seau("carburant") == ac.hash_seau("carburant")
    assert 0 <= ac.hash_seau("carburant") < ac.NB_SEAUX
    assert ac.hash_seau("fiscal") == sum(b"fiscal") % ac.NB_SEAUX
