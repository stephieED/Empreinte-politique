"""Le balisage est validé contre le vocabulaire de schema.org (#1008).

Mesuré le 18/09/2026 : le validateur en ligne de Google refuse les requêtes
au-delà d'une trentaine — 34 sur 34 bloquées, même espacées de six secondes —
alors que le critère de fin de #1008 demande que CHAQUE fiche soit vérifiée.
`scripts/vocabulaire-schema-org.mjs` fait la vérification depuis le vocabulaire
que schema.org publie, sans dépendre de Google.

LE PIÈGE, PAYÉ LE MÊME JOUR : une première passe a rendu 420 anomalies, toutes
fausses, venues du patron `Role` — un rôle daté porte la propriété par laquelle
il est rattaché, ce que `domainIncludes` ne peut pas exprimer.

FIXTURE. Un extrait du vocabulaire réel (mêmes clés, mêmes formes qu'en ligne)
et les objets que le site publie, copiés de la production le 18/09/2026.

CE QU'ILS NE COUVRENT PAS : le téléchargement du vocabulaire, qui demande le
réseau. Le contrôle complet a tourné sur la production le 18/09/2026 :
« 64 adresses, 60 objets JSON-LD, validés contre le vocabulaire de
schema.org. Aucun défaut. »
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale"
MODULE = UI / "scripts" / "vocabulaire-schema-org.mjs"
CONTROLE = UI / "scripts" / "verifier-referencement.mjs"

VOCABULAIRE = {
    "@graph": [
        {"@id": "schema:Thing", "@type": "rdfs:Class"},
        {"@id": "schema:Person", "@type": "rdfs:Class", "rdfs:subClassOf": {"@id": "schema:Thing"}},
        {"@id": "schema:Organization", "@type": "rdfs:Class", "rdfs:subClassOf": {"@id": "schema:Thing"}},
        {"@id": "schema:GovernmentOrganization", "@type": "rdfs:Class", "rdfs:subClassOf": {"@id": "schema:Organization"}},
        {"@id": "schema:Intangible", "@type": "rdfs:Class", "rdfs:subClassOf": {"@id": "schema:Thing"}},
        {"@id": "schema:Role", "@type": "rdfs:Class", "rdfs:subClassOf": {"@id": "schema:Intangible"}},
        {"@id": "schema:OrganizationRole", "@type": "rdfs:Class", "rdfs:subClassOf": {"@id": "schema:Role"}},
        {"@id": "schema:name", "@type": "rdf:Property", "schema:domainIncludes": {"@id": "schema:Thing"}},
        {"@id": "schema:memberOf", "@type": "rdf:Property", "schema:domainIncludes": [{"@id": "schema:Person"}, {"@id": "schema:Organization"}]},
        {"@id": "schema:roleName", "@type": "rdf:Property", "schema:domainIncludes": {"@id": "schema:Role"}},
        {"@id": "schema:startDate", "@type": "rdf:Property", "schema:domainIncludes": {"@id": "schema:Role"}},
        {"@id": "schema:foundingDate", "@type": "rdf:Property", "schema:domainIncludes": {"@id": "schema:Organization"}},
    ],
}

PERSONNE = {
    "@context": "https://schema.org", "@type": "Person", "name": "Jean-Luc Mélenchon",
    "memberOf": [{
        "@type": "OrganizationRole", "roleName": "Mandat de sénateur", "startDate": "1986-10-02",
        "memberOf": {"@type": "Organization", "name": "Sénat"},
    }],
}


def _node(corps: str) -> str:
    if shutil.which("node") is None:
        pytest.skip("node absent")
    script = f"import * as V from {json.dumps(MODULE.as_uri())};\nconst VOC = {json.dumps(VOCABULAIRE)};\n{corps}"
    res = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    return res.stdout


def _anomalies(objet: dict) -> list[str]:
    return json.loads(_node(
        f"const v = V.construireVocabulaire(VOC);\n"
        f"console.log(JSON.stringify(V.anomalies(v, {json.dumps(objet, ensure_ascii=False)})));"
    ))


def test_le_balisage_publie_ne_porte_aucune_anomalie():
    assert _anomalies(PERSONNE) == []


def test_le_patron_role_est_accepte():
    """`Person.memberOf` → `OrganizationRole.memberOf` → `Organization`.

    Le rôle porte la propriété par laquelle il est rattaché : c'est la règle de
    schema.org, et une lecture naïve de `domainIncludes` la refuse — 420 fausses
    anomalies le 18/09/2026.
    """
    role = PERSONNE["memberOf"][0]
    assert "memberOf" in role
    assert _anomalies(role) == []


def test_une_propriete_hors_du_domaine_est_signalee():
    objet = {"@type": "Organization", "name": "X", "roleName": "pas ici"}
    assert _anomalies(objet) == ["/roleName : hors du domaine de Organization"]


def test_une_propriete_inconnue_est_signalee():
    assert _anomalies({"@type": "Person", "nom": "X"}) == ["/nom : propriété inconnue de schema.org"]


def test_un_type_inconnu_est_signale():
    assert _anomalies({"@type": "Politicien", "name": "X"}) == ["/ : type inconnu de schema.org — Politicien"]


def test_une_anomalie_imbriquee_porte_son_chemin():
    objet = {"@type": "Person", "name": "X", "memberOf": {"@type": "Organization", "name": "Y", "inconnue": 1}}
    assert _anomalies(objet) == ["/memberOf/inconnue : propriété inconnue de schema.org"]


def test_un_type_herite_garde_les_proprietes_du_parent():
    objet = {"@type": "GovernmentOrganization", "name": "Gouvernement", "foundingDate": "2025-10-11"}
    assert _anomalies(objet) == []


def test_le_controle_valide_et_sait_s_en_passer():
    source = CONTROLE.read_text(encoding="utf-8")
    assert "vocabulaire-schema-org.mjs" in source
    assert "--sans-vocabulaire" in source
    assert "validation sautée" in source, (
        "un vocabulaire indisponible ne doit pas faire échouer le contrôle du site"
    )
