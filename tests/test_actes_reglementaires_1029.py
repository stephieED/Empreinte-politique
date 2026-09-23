"""#1029 voie 1 — les actes réglementaires du Journal officiel, et leur index de mots.

Les fixtures sous `tests/fixtures/jorf/` sont les fichiers XML RÉELS de la
livraison DILA `JORF_20260921-220149.tar.gz` (22/09/2026), recopiés sans
retouche : deux arrêtés du 18/09/2026 et leurs quatre articles. Le test
reconstruit une archive de la même forme que la DILA et la sert par `file://` —
le module lit donc la vraie structure, jamais une fixture écrite à la main.
"""
from __future__ import annotations

import json
import sys
import tarfile
from datetime import date
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))

import actes_reglementaires as ar  # noqa: E402

FIXTURES = RACINE / "tests" / "fixtures" / "jorf"
ARRETE_ARMEES = "JORFTEXT000054861441"
ARRETE_FDES = "JORFTEXT000054861513"
ARTICLES = {
    ARRETE_ARMEES: ("JORFARTI000054861446", "JORFARTI000054861448"),
    ARRETE_FDES: ("JORFARTI000054861515", "JORFARTI000054861516"),
}


def _archive(chemin: Path, textes=(ARRETE_ARMEES, ARRETE_FDES)) -> str:
    """Une archive à la forme DILA : `<horodatage>/jorf/global/{texte/version,article}/…`."""
    with tarfile.open(chemin, "w:gz") as tar:
        for cid in textes:
            tar.add(FIXTURES / f"{cid}.xml",
                    arcname=f"20260921-220149/jorf/global/texte/version/JORF/TEXT/00/{cid}.xml")
            for article in ARTICLES[cid]:
                tar.add(FIXTURES / f"{article}.xml",
                        arcname=f"20260921-220149/jorf/global/article/JORF/ARTI/00/{article}.xml")
    return chemin.parent.as_uri() + "/"


def _moisson(tmp_path: Path, **kwargs):
    base = _archive(tmp_path / "JORF_20260921-220149.tar.gz")
    return ar.collecter(["JORF_20260921-220149.tar.gz"], tmp_path / "spool", base=base, **kwargs)


def test_la_collecte_lit_les_actes_et_les_mots_de_leurs_articles(tmp_path):
    moisson, derniere = _moisson(tmp_path)
    par_mois = dict(moisson.par_mois())

    assert derniere == "JORF_20260921-220149.tar.gz"
    assert set(par_mois) == {"2026-09"}
    acte = par_mois["2026-09"][ARRETE_ARMEES]
    assert acte["nature"] == "ARRETE"
    assert acte["date_publi"] == "2026-09-20"
    assert acte["ministere"] == "Ministère des armées et des anciens combattants"
    assert acte["nor"] == "ARMK2624825A"
    assert acte["num"] is None, "un arrêté n'est pas numéroté comme un décret"
    assert "praticiens" in acte["mots"], "les mots du titre sont indexés"
    assert moisson.articles == 4


def test_le_document_publie_porte_ses_actes_et_leurs_renvois(tmp_path, monkeypatch):
    from amendements_contenu import decoder

    # Deux actes seulement : au seuil réel, un mot présent une fois pèse 50 %
    # des actes du mois et n'est pas indexé. Le seuil est donc neutralisé ici
    # pour observer les renvois ; il a son propre test.
    monkeypatch.setattr(ar, "SEUIL_FREQUENCE", 1.0)
    monkeypatch.setattr(ar, "SEUIL_AVANT_FUSION", 1.0)
    moisson, _ = _moisson(tmp_path)
    doc = ar.document("2026-09", dict(moisson.par_mois())["2026-09"],
                      derniere_livraison="JORF_20260921-220149.tar.gz",
                      genere_le="2026-09-22T19:00:00+0200")

    assert doc["schema_version"] == ar.SCHEMA_VERSION
    assert doc["prefixe_ids"] == "JORFTEXT"
    assert doc["ids"] == [ARRETE_ARMEES[8:], ARRETE_FDES[8:]]
    rang_nature, titre, date_publi, rang_ministere, nor, num = doc["actes"][0]
    assert doc["natures"][rang_nature] == "ARRETE"
    assert titre.startswith("Arrêté du 18 septembre 2026 modifiant deux arrêtés")
    assert (date_publi, nor, num) == ("2026-09-20", "ARMK2624825A", None)
    assert doc["ministeres"][rang_ministere] == "Ministère des armées et des anciens combattants"
    assert decoder(doc["mots"]["praticiens"]) == [0], "le renvoi est la position dans ids"
    assert "développement" not in doc["mots"], "les mots sont sans accents"


def test_un_mot_de_plus_de_trois_pour_cent_des_actes_n_est_pas_indexe(tmp_path):
    """Le seuil de la voie 2, appliqué ici : sur deux actes, un mot commun aux
    deux dépasse 3 % et ne sert à aucune recherche."""
    moisson, _ = _moisson(tmp_path)
    actes = dict(moisson.par_mois())["2026-09"]
    communs = actes[ARRETE_ARMEES]["mots"] & actes[ARRETE_FDES]["mots"]

    doc = ar.document("2026-09", actes)

    assert communs, "les deux arrêtés partagent au moins un mot"
    assert doc["mots"] == {}, "sur deux actes, tout mot dépasse le seuil"
    assert doc["seuil_frequence"] == 0.03, "la règle est publiée dans le fichier"


def test_les_natures_hors_perimetre_et_les_dates_hors_borne_sont_ecartees():
    assert ar.retenu("DECRET", "2007-01-01") and ar.retenu("ORDONNANCE", "2026-09-20")
    assert not ar.retenu("LOI", "2026-09-20"), "une loi passe par le Parlement (#664)"
    assert not ar.retenu("DECISION", "2026-09-20")
    assert not ar.retenu("ARRETE", "2006-12-31"), "la borne basse est 2007"
    assert not ar.retenu("ARRETE", None)


def test_la_date_bouche_trou_de_la_source_ne_fait_pas_un_mois():
    """386 actes du fonds portent `2999-…`. Publiée dans un mois, cette date
    serait lue comme un fait (§2 règle 5)."""
    assert ar.retenu("DECRET", "2999-01-01"), "l'acte existe, sa date est inconnue"
    assert ar.mois_de("2999-01-01") == ar.MOIS_SANS_DATE
    assert ar.document(ar.MOIS_SANS_DATE, {})["mois"] is None


def test_la_fenetre_de_relecture_couvre_le_mois_en_cours_et_le_precedent():
    assert ar.mois_a_relire(date(2026, 9, 22)) == ["2026-08", "2026-09"]
    assert ar.mois_a_relire(date(2026, 1, 3)) == ["2025-12", "2026-01"]
    assert ar.premiere_livraison_utile(["2026-08", "2026-09"]) == "20260725", \
        "une livraison de fin de mois porte des actes du lendemain"


def test_un_acte_deja_publie_absent_de_la_relecture_arrete_la_publication(tmp_path):
    """Le fichier d'un mois est RÉÉCRIT, pas fusionné : un acte que la fenêtre
    de livraisons n'aurait pas couvert disparaîtrait sans trace (§3c)."""
    complet = tmp_path / "complet"
    complet.mkdir()
    moisson, derniere = ar.collecter(["JORF_20260921-220149.tar.gz"], tmp_path / "spool",
                                     base=_archive(complet / "JORF_20260921-220149.tar.gz"))
    publie = tmp_path / "publie"
    ar.publier(moisson.par_mois(), publie, derniere_livraison=derniere)

    partielle = tmp_path / "partielle"
    partielle.mkdir()
    amputee, _ = ar.collecter(
        ["JORF_20260921-220149.tar.gz"], tmp_path / "spool2",
        base=_archive(partielle / "JORF_20260921-220149.tar.gz", textes=(ARRETE_ARMEES,)))

    with pytest.raises(ar.ActesPerdus) as erreur:
        ar.publier(amputee.par_mois(), publie, derniere_livraison=derniere)
    assert ARRETE_FDES in str(erreur.value)


def test_le_fichier_n_est_pas_reecrit_quand_seule_sa_date_change(tmp_path):
    """#1075 : un index ne se réécrit que si son contenu change."""
    moisson, derniere = _moisson(tmp_path)
    publie = tmp_path / "publie"

    assert ar.publier(moisson.par_mois(), publie, derniere_livraison=derniere) == ["2026-09"]
    assert ar.publier(moisson.par_mois(), publie, derniere_livraison=derniere) == []


def test_le_seau_d_un_acte_ne_depend_pas_du_processus():
    """`hash()` d'une chaîne est randomisé à chaque démarrage de Python : un
    acte doit tomber dans le même seau d'un run à l'autre."""
    assert ar.hash_seau(ARRETE_ARMEES) == ar.hash_seau(ARRETE_ARMEES)
    assert 0 <= ar.hash_seau(ARRETE_FDES) < ar.NB_SEAUX


def test_le_listing_dila_donne_le_dump_global_et_les_livraisons():
    listing = '''<a href="Freemium_jorf_global_20250713-140000.tar.gz">x</a>
    <a href="JORF_20260921-220149.tar.gz">x</a> <a href="JORF_20260922-002206.tar.gz">x</a>'''

    dump, livraisons = ar.livraisons_disponibles(listing)

    assert dump == "Freemium_jorf_global_20250713-140000.tar.gz"
    assert livraisons == [("JORF_20260921-220149.tar.gz", "20260921"),
                          ("JORF_20260922-002206.tar.gz", "20260922")]


def test_la_licence_du_journal_officiel_ne_touche_aucun_profil():
    from licences import LICENCE_JORF, LICENCE_PAR_TYPE_SOURCE, LICENCES_SHARE_ALIKE

    assert LICENCE_JORF not in LICENCE_PAR_TYPE_SOURCE.values()
    assert LICENCE_JORF not in LICENCES_SHARE_ALIKE
    assert json.loads(json.dumps({"licence_donnees": LICENCE_JORF}))["licence_donnees"]


# ---------------------------------------------------------------------------
# Les liens vers une loi, et leur correction après coup (arbitré le 23/09/2026)
# ---------------------------------------------------------------------------

DECRET_2013 = "JORFTEXT000027904809"   # décret de 2013, REDÉLIVRÉ le 21/09/2026
ARRETE_CITANT = "JORFTEXT000054861494"  # arrêté du 18/09/2026, cite une loi en visa


def _xml(cid: str) -> str:
    return (FIXTURES / f"{cid}.xml").read_text(encoding="utf-8")


def test_la_source_distingue_appliquer_et_citer():
    """Un décret qui cite une loi en visa n'en est pas un décret d'application
    (§2 règle 2) : la source pose deux `typelien`, on publie deux listes."""
    appliquees, citees = ar.liens_vers_une_loi(_xml(DECRET_2013))
    assert appliquees == ["JORFTEXT000000869866", "JORFTEXT000000869867"]
    assert citees == []

    appliquees, citees = ar.liens_vers_une_loi(_xml(ARRETE_CITANT))
    assert appliquees == []
    assert citees == ["JORFTEXT000051538879"], "dédoublonné : la source répète le lien"


def test_un_acte_sans_lien_n_a_pas_de_cle():
    """Une clé absente est « aucun lien déclaré », jamais « aucune loi » : la
    source ne qualifie plus depuis 2024 (docs/sources/jorf-dila.md)."""
    assert ar.liens_vers_une_loi(_xml(ARRETE_ARMEES)) == ([], [])

    doc = ar.document("2026-09", {ARRETE_ARMEES: {"nature": "ARRETE", "mots": set()}})

    assert doc["liens_lois"] == {}


def _archive_avec(chemin: Path, cid: str) -> str:
    with tarfile.open(chemin, "w:gz") as tar:
        tar.add(FIXTURES / f"{cid}.xml",
                arcname=f"20260921-220149/jorf/global/texte/version/JORF/TEXT/00/{cid}.xml")
    return chemin.parent.as_uri() + "/"


def test_un_acte_d_un_mois_clos_est_garde_pour_ses_seuls_liens(tmp_path):
    """La redélivrance d'un décret de 2013 ne reconstruit pas août 2013 — ses
    articles ne sont pas relus —, mais ses liens sont repris."""
    base = _archive_avec(tmp_path / "JORF_20260921-220149.tar.gz", DECRET_2013)

    moisson, _ = ar.collecter(["JORF_20260921-220149.tar.gz"], tmp_path / "spool",
                              mois_retenus={"2026-09"}, base=base)

    assert dict(moisson.par_mois()) == {}, "aucun mois reconstruit"
    assert list(moisson.redelivres) == [DECRET_2013]
    assert moisson.redelivres[DECRET_2013]["date_publi"] == "2013-08-29"


def test_la_correction_ecrit_les_liens_dans_le_mois_deja_publie(tmp_path):
    publie = tmp_path / "actes"
    publie.mkdir()
    (publie / "2013-08.json").write_text(json.dumps({
        "schema_version": ar.SCHEMA_VERSION, "mois": "2013-08",
        "genere_le": "2026-09-22T00:00:00+0200", "prefixe_ids": "JORFTEXT",
        "ids": [DECRET_2013[8:]], "actes": [[1, "Décret n° 2013-776", "2013-08-29", None, None, "2013-776"]],
        "liens_lois": {}, "mots": {},
    }, ensure_ascii=False), encoding="utf-8")
    redelivres = {DECRET_2013: {"date_publi": "2013-08-29",
                                "lois_appliquees": ["JORFTEXT000000869866"], "lois_citees": []}}

    assert ar.corriger_les_liens(redelivres, publie) == ["2013-08"]

    doc = json.loads((publie / "2013-08.json").read_text(encoding="utf-8"))
    assert doc["liens_lois"] == {DECRET_2013[8:]: [["JORFTEXT000000869866"], []]}
    assert doc["liens_revus_le"], "le jour du constat est publié avec la correction"


def test_la_correction_retire_un_lien_que_la_source_ne_pose_plus(tmp_path):
    publie = tmp_path / "actes"
    publie.mkdir()
    (publie / "2013-08.json").write_text(json.dumps({
        "schema_version": ar.SCHEMA_VERSION, "mois": "2013-08", "prefixe_ids": "JORFTEXT",
        "genere_le": "2026-09-22T00:00:00+0200", "ids": [DECRET_2013[8:]],
        "actes": [[1, "Décret", "2013-08-29", None, None, None]],
        "liens_lois": {DECRET_2013[8:]: [["JORFTEXT000000869866"], []]}, "mots": {},
    }, ensure_ascii=False), encoding="utf-8")
    redelivres = {DECRET_2013: {"date_publi": "2013-08-29", "lois_appliquees": [], "lois_citees": []}}

    ar.corriger_les_liens(redelivres, publie)

    doc = json.loads((publie / "2013-08.json").read_text(encoding="utf-8"))
    assert doc["liens_lois"] == {}, "publier une qualification retirée serait la nôtre"


def test_un_mois_jamais_publie_n_est_pas_fabrique_par_la_correction(tmp_path):
    publie = tmp_path / "actes"
    publie.mkdir()
    redelivres = {DECRET_2013: {"date_publi": "2013-08-29",
                                "lois_appliquees": ["JORFTEXT000000869866"], "lois_citees": []}}

    assert ar.corriger_les_liens(redelivres, publie) == []
    assert list(publie.iterdir()) == [], "un mois absent se construit entier, pas par un patch"
