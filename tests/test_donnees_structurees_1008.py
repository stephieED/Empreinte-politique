"""Le balisage Schema.org de chaque fiche (#1008).

Mesuré le 18/09/2026 : aucune des 64 pages publiées ne portait
`application/ld+json`. #1003 a rendu les fiches LISIBLES ; ce balisage les rend
INTERPRÉTABLES — une personne, une fonction, des dates, une source, typées.

FIXTURES. Entrées copiées du corpus le 18/09/2026. Les cas qui font les règles :
le mandat local d'Hénin-Beaumont (clos, `actif` faux, sans date de fin), le
`source_url` d'un mandat gouvernemental qui pointe vers une ARCHIVE AMO30 et non
vers une page de personne, et une lignée à plusieurs maillons.

CE QU'ILS NE COUVRENT PAS : la validation par les outils de Google et de
schema.org, qui demandent une page en ligne. À faire après déploiement.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale"
MODULE = UI / "scripts" / "donnees-structurees.mjs"
CONTROLE = UI / "scripts" / "verifier-referencement.mjs"

PROFIL = {
    "identite": {"source_url": "https://www2.assemblee-nationale.fr/deputes/fiche/OMC_PA2150", "date_naissance": "1951-08-19", "profession": "Professeur"},
    "mandats": [
        {"categorie": "mandat_electif", "chambre": "AN", "label": "Mandat parlementaire (La France insoumise)", "debut": "2017-06-18", "fin": "2022-06-21", "actif": False, "source_url": None},
        {"categorie": "mandat_electif", "chambre": "Senat", "label": "Mandat de sénateur", "debut": "1986-10-02", "fin": "1995-10-01", "actif": False, "source_url": "https://www.senat.fr/senateur/86039k.html"},
        {"categorie": "fonction_gouvernementale", "label": "Gouvernement (PHILIPPE 2)", "debut": "2017-06-20", "fin": "2020-07-06", "actif": False, "source_url": "https://data.assemblee-nationale.fr/static/openData/repository/17/amo/AMO30.json.zip"},
        {"categorie": "mandat_local", "label": "Hénin-Beaumont", "debut": "2020-05-18", "fin": None, "actif": False, "source_url": "https://www.data.gouv.fr/datasets/repertoire-national-des-elus-1"},
        {"categorie": "commission", "label": "Commission des affaires étrangères", "debut": "2017-06-29", "fin": None, "actif": False, "source_url": None},
    ],
}
LIGNEE = {
    "id": "AN-SOC", "nom": "Socialistes", "chambre": "AN",
    "periode": {"debut": "2017-06-27", "fin": None},
    "maillons": [
        {"nom": "Nouvelle Gauche", "periode": {"debut": "2017-06-27", "fin": "2018-09-11"}},
        {"nom": "Socialistes et apparentés", "periode": {"debut": "2018-09-12", "fin": "2022-06-21"}},
    ],
}
GOUVERNEMENT = {
    "nom": "Gouvernement Lecornu II",
    "periode": {"debut": "2025-10-11", "fin": None, "actif": True},
    "membres": [{"nom": "Annie Genevard", "portefeuille": "Ministère de l'agriculture", "debut": "2025-10-13", "fin": None, "actif": True}],
}


def _node(corps: str) -> str:
    if shutil.which("node") is None:
        pytest.skip("node absent")
    script = f"import * as S from {json.dumps(MODULE.as_uri())};\n{corps}"
    res = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    return res.stdout


@pytest.fixture(scope="module")
def objets() -> dict:
    donnees = json.dumps({"p": PROFIL, "l": LIGNEE, "g": GOUVERNEMENT}, ensure_ascii=False)
    return json.loads(_node(
        f"const D = {donnees};\n"
        "console.log(JSON.stringify({\n"
        "  personne: S.jsonldCandidat({nom: 'Jean-Luc Mélenchon', parti: 'La France Insoumise (LFI)'}, D.p, 'https://e/candidats/x'),\n"
        "  lignee: S.jsonldLignee(D.l, 'https://e/groupes/AN-SOC'),\n"
        "  gouvernement: S.jsonldGouvernement(D.g, 'https://e/gouvernements/LECORNU_II'),\n"
        "  accueil: S.jsonldAccueil('empreinte-politique.fr', 'Des faits sourcés.'),\n"
        "}));"
    ))


def test_la_personne_porte_ses_mandats_dates_et_leur_organisation(objets):
    roles = objets["personne"]["memberOf"]
    assert [r["roleName"] for r in roles] == [
        "Mandat local", "Gouvernement (PHILIPPE 2)", "Mandat parlementaire (La France insoumise)", "Mandat de sénateur",
    ]
    senat = next(r for r in roles if r["roleName"] == "Mandat de sénateur")
    assert senat == {
        "@type": "OrganizationRole", "roleName": "Mandat de sénateur",
        "startDate": "1986-10-02", "endDate": "1995-10-01",
        "memberOf": {"@type": "Organization", "name": "Sénat"},
    }


def test_un_mandat_clos_sans_fin_n_a_pas_de_date_de_fin(objets):
    """§2 règle 5 : la date manque, elle ne s'invente pas (#922/#966)."""
    local = next(r for r in objets["personne"]["memberOf"] if r["roleName"] == "Mandat local")
    assert "endDate" not in local
    assert local["memberOf"]["name"] == "Hénin-Beaumont", "la collectivité nomme l'organisation, pas le rôle"


def test_sameas_ne_pointe_que_vers_une_page_de_personne(objets):
    """Une archive de jeu de données n'est pas une page « à propos de »."""
    assert objets["personne"]["sameAs"] == [
        "https://www2.assemblee-nationale.fr/deputes/fiche/OMC_PA2150",
        "https://www.senat.fr/senateur/86039k.html",
    ]


def test_ni_naissance_ni_profession_ni_agregat(objets):
    rendu = json.dumps(objets, ensure_ascii=False)
    for interdit in ("1951-08-19", "birthDate", "Professeur", "Commission des affaires", "ClaimReview", "aggregateRating", "ratingValue"):
        assert interdit not in rendu, interdit


def test_la_lignee_porte_ses_maillons_et_sa_chambre(objets):
    lignee = objets["lignee"]
    assert lignee["parentOrganization"] == {"@type": "GovernmentOrganization", "name": "Assemblée nationale"}
    assert lignee["foundingDate"] == "2017-06-27" and "dissolutionDate" not in lignee
    assert [m["name"] for m in lignee["subOrganization"]] == ["Nouvelle Gauche", "Socialistes et apparentés"]


def test_le_gouvernement_porte_ses_membres_avec_leur_portefeuille(objets):
    gouvernement = objets["gouvernement"]
    assert gouvernement["@type"] == "GovernmentOrganization"
    assert gouvernement["member"] == [{
        "@type": "OrganizationRole", "roleName": "Ministère de l'agriculture", "startDate": "2025-10-13",
        "member": {"@type": "Person", "name": "Annie Genevard"},
    }]


def test_l_editeur_n_est_jamais_une_personne(objets):
    """Les mentions légales déclarent une édition par une personne qui ne se nomme pas."""
    editeur = objets["accueil"]["publisher"]
    assert editeur["@type"] == "Organization" and editeur["name"] == "Empreinte politique"


def test_une_chambre_sans_organisation_arrete_le_build():
    sortie = _node(
        "try { S.jsonldLignee({id:'X', nom:'X', chambre:'Cese', periode:{}}, 'u'); console.log('passe'); }"
        " catch (e) { console.log('erreur'); }"
    )
    assert sortie.strip() == "erreur"


def test_la_balise_neutralise_une_fermeture_de_script():
    sortie = _node("console.log(S.baliseJsonld({name: '</script><img src=x>'}));")
    assert "<\\/script>" in sortie
    assert sortie.count("</script>") == 1, "une donnée ne doit pas pouvoir fermer la balise"


def test_le_controle_releve_un_balisage_absent_ou_illisible():
    source = CONTROLE.read_text(encoding="utf-8")
    assert "aucun balisage Schema.org" in source and "balisage Schema.org illisible" in source


def test_le_build_pose_le_balisage():
    script = (UI / "scripts" / "pages-par-adresse.mjs").read_text(encoding="utf-8")
    assert "donnees-structurees.mjs" in script and "avecJsonld(" in script
