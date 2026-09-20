"""#901 — l'axe de couleur européen : le domaine EuroVoc d'une matière, la
famille OEIL d'un dossier. Lus dans la source, jamais déduits d'un libellé.

Les formes sont celles de la source, relevées le 17/09/2026 : la réponse du
point SPARQL de l'Office des publications (`c`, `dn`, `dl`) pour le concept 218
« coopération militaire », et les `procedure.subject` réels du dump
`ep_dossiers` (2007/2149(INI), 2002/2264(INI), 2008/2122(INI)).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "tests"))

from documents_europeens import construire, resoudre_domaines  # noqa: E402
from dossiers_europeens import (  # noqa: E402
    choisir_libelles_de_famille,
    construire as construire_dossiers,
    document as document_dossiers,
    familles,
    libelles_de_famille,
)
from test_documents_europeens_901 import _Resolveur, _SessionSparql  # noqa: E402
from test_dossiers_europeens_901 import _dump  # noqa: E402

RELATIONS = ("08", "08 RELATIONS INTERNATIONALES")
VIE_POLITIQUE = ("04", "04 VIE POLITIQUE")


# --- le domaine EuroVoc ------------------------------------------------------

def test_chaque_matiere_porte_son_domaine():
    entrees = construire(
        ["A-10-2025-0084"],
        _Resolveur({"A-10-2025-0084": ["218"]}),
        _SessionSparql({"218": "coopération militaire"}, domaines={"218": [RELATIONS]}),
    )
    assert entrees[0]["matieres"] == [{
        "code": "218", "libelle": "coopération militaire",
        "domaine": {"code": "08", "libelle": "08 RELATIONS INTERNATIONALES"},
    }]
    assert "domaines_non_resolu" not in entrees[0]


def test_un_domaine_introuvable_est_declare_sans_perdre_la_matiere():
    """100145 est lui-même un domaine : le thésaurus ne lui en rend pas."""
    entrees = construire(
        ["X-9-2024-0001"],
        _Resolveur({"X-9-2024-0001": ["218", "100145"]}),
        _SessionSparql({"218": "coopération militaire", "100145": "UNION EUROPÉENNE"},
                       domaines={"218": [RELATIONS]}),
    )
    matieres = {m["code"]: m for m in entrees[0]["matieres"]}
    assert matieres["100145"]["domaine"] is None
    assert matieres["218"]["domaine"]["code"] == "08"
    assert entrees[0]["domaines_non_resolu"] == {
        "motif": "domaine_eurovoc_introuvable", "codes": ["100145"]}


def test_deux_domaines_pour_un_concept_n_en_publient_aucun():
    """En choisir un serait une classification de notre fait."""
    session = _SessionSparql({}, domaines={"218": [RELATIONS, VIE_POLITIQUE]})
    assert resoudre_domaines(["218"], session) == {}


def test_les_domaines_ne_sont_demandes_que_pour_les_concepts_nommes():
    session = _SessionSparql({"218": "coopération militaire"}, domaines={"218": [RELATIONS]})
    construire(["A"], _Resolveur({"A": ["218", "9999"]}), session)
    requete_domaines = [r for r in session.requetes if "ev:domain" in r]
    assert len(requete_domaines) == 1
    assert "/9999>" not in requete_domaines[0]


# --- la famille OEIL ---------------------------------------------------------

def test_le_libelle_de_famille_se_lit_dans_les_trois_formes():
    # dict, clé numérique seule — 2007/2149(INI)
    assert libelles_de_famille({"procedure": {"subject": {
        "4": "Economic, social and territorial cohesion",
        "4.10.16": "Social and community life, associations, foundations",
    }}}) == {"4": "Economic, social and territorial cohesion"}
    # liste, code et libellé collés — 2002/2264(INI)
    assert libelles_de_famille({"procedure": {"subject": ["3 Community policies"]}}) == {
        "3": "Community policies"}
    # liste mêlée : les codes profonds ne sont pas des familles — 2008/2122(INI)
    assert libelles_de_famille({"procedure": {"subject": [
        "2.50.04 Banks and credit",
        "4 Economic, social and territorial cohesion",
    ]}}) == {"4": "Economic, social and territorial cohesion"}


def test_le_libelle_le_plus_recent_gagne():
    vus = {"2": {"Internal market, SLIM": "2013-02-09T00:47:05.691000",
                 "Internal market, single market": "2026-07-18T01:03:32+00:00"}}
    assert choisir_libelles_de_famille(vus) == {"2": "Internal market, single market"}


def test_une_famille_sans_libelle_est_declaree():
    publiees, non_resolu = familles(
        [{"code": "6.40.10", "libelle": "x"}, {"code": "9.10", "libelle": "y"}],
        {"6": "External relations of the Union"},
    )
    assert publiees == [{"code": "6", "libelle": "External relations of the Union"}]
    assert non_resolu == {"motif": "libelle_famille_oeil_introuvable", "codes": ["9"]}


def test_de_bout_en_bout_le_libelle_vient_d_un_autre_dossier_du_dump(tmp_path):
    """Le dossier visé ne porte que des codes profonds : sa famille est nommée
    par un autre dossier du dump, qui n'entre pas dans l'index."""
    chemin = _dump(tmp_path, [
        {"procedure": {"reference": "2009/2213(INI)", "title": "EU strategy for the relations with Latin America",
                       "stage_reached": "Procedure completed",
                       "subject": {"6.40.10": "Relations with Latin America, Central America, Caribbean islands"}},
         "meta": {"updated": "2024-01-01T00:00:00"}},
        {"procedure": {"reference": "2020/0001(INI)", "subject": {"6": "External relations of the Union"}},
         "meta": {"updated": "2023-08-03T13:47:25"}},
    ])
    entrees = construire_dossiers({"2009/2213(INI)"}, dump_path=chemin)

    assert [e["reference"] for e in entrees] == ["2009/2213(INI)"]
    assert entrees[0]["familles"] == [{"code": "6", "libelle": "External relations of the Union"}]
    assert "familles_non_resolu" not in entrees[0]
    assert document_dossiers(entrees)["schema_version"] == "dossiers-europeens-v4"
    json.dumps(entrees)  # sérialisable tel quel
