"""Parseur XML Syceron — mesuré sur des RÉDUCTIONS de l'archive réelle (#510).

Ce fichier travaillait sur `syceron_minimal.xml` et `syceron_missing_fields.xml`,
deux fixtures écrites avant toute lecture de l'archive : elles portaient
`<id>PA123456</id>` et un `<titreStruct><intitule>` sous `<point>`, or **ni l'un
ni l'autre n'existe** — 0 identifiant d'orateur préfixé, et 0 `<titreStruct>` sous
`<contenu>` sur les 162 073 points des législatures 15, 16 et 17. Le parseur était
donc validé contre sa propre hypothèse, et c'est ce qui a laissé passer #510 puis
ses deux défauts de parseur pendant toute la vie du projet.

Les deux fixtures inventées sont retirées. Toute mesure se prend désormais sur des
réductions **verbatim** de comptes rendus réels, obtenues en supprimant des frères,
jamais en écrivant du balisage.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from parse_syceron import parse_syceron_xml

FIXTURES = Path(__file__).resolve().parent / "fixtures"

STRUCTURE = "syceron_reel_leg17_structure.xml"
ATTRIBUTION_REFUSEE = "syceron_reel_leg17_attribution_refusee.xml"
IMBRICATION = "syceron_reel_leg17.xml"


def _load(filename: str) -> bytes:
    return (FIXTURES / filename).read_bytes()


@pytest.fixture(scope="module")
def structure():
    return parse_syceron_xml(_load(STRUCTURE))


# ---------------------------------------------------------------------------
# 1. Métadonnées de séance
# ---------------------------------------------------------------------------

def test_seance_uid(structure):
    assert structure["seance"]["uid"] == "CRSANR5L17S2026O1N187"


def test_seance_refs(structure):
    assert structure["seance"]["seance_ref"] == "RUANR5L17S2026IDS30420"
    assert structure["seance"]["session_ref"] == "SCR5A2026O1"


def test_seance_date_iso(structure):
    """`<dateSeance>20260331150000000</dateSeance>` → ISO."""
    assert structure["seance"]["date"] == "2026-03-31"


def test_seance_legislature_et_numero(structure):
    assert structure["seance"]["legislature"] == "17"
    assert structure["seance"]["numero_seance"] == "187"


def test_seance_etat_et_version(structure):
    assert structure["seance"]["etat"] == "complet"
    assert structure["seance"]["version"] == "avant_JO"


def test_metadonnees_propagees_a_chaque_intervention(structure):
    for i in structure["interventions"]:
        assert i["date"] == "2026-03-31"
        assert i["source_id"] == "CRSANR5L17S2026O1N187"
        assert i["etat_compte_rendu"] == "complet"
        assert i["version_compte_rendu"] == "avant_JO"
        assert i["mots_cles"] == []
        assert i["source_url"] is None


# ---------------------------------------------------------------------------
# 2. La forme réelle de l'identifiant d'orateur
# ---------------------------------------------------------------------------

def test_lidentifiant_dorateur_est_publie_nu(structure):
    """`<orateur><id>721908</id>` — jamais `PA721908`, qui vit dans `id_acteur`."""
    ids = [i["orateur_id_source"] for i in structure["interventions"] if i["orateur_id_source"]]
    assert ids
    assert all(not i.startswith("PA") for i in ids)
    assert "721908" in ids


def test_le_prefixe_est_publie_dans_lattribut_id_acteur(structure):
    """La preuve du préfixage de #510 : la source écrit les deux formes côte à côte."""
    for i in structure["interventions"]:
        if i["orateur_id_source"] and i["orateur_id_acteur"]:
            assert i["orateur_id_acteur"] == "PA" + i["orateur_id_source"]


# ---------------------------------------------------------------------------
# 3. Le parcours : points frères, points imbriqués, conteneurs intermédiaires
# ---------------------------------------------------------------------------

def test_les_points_de_nivpoint_1_a_3_sont_des_freres_pas_des_descendants():
    """La hiérarchie du sommaire n'est pas l'imbrication XML.

    Mesuré sur la 17e : les 1 749 + 5 085 + 4 831 points de nivpoint 1, 2 et 3
    sont tous à la profondeur XML 1. Un parcours qui ne suivrait que
    l'imbrication rattacherait « Article 9 terdecies » à rien du tout.
    """
    brut = (FIXTURES / STRUCTURE).read_text(encoding="utf-8")
    assert 'nivpoint="1"' in brut and 'nivpoint="2"' in brut and 'nivpoint="3"' in brut

    parsed = parse_syceron_xml(_load(STRUCTURE))
    chemins = {i["point_ordre_du_jour"] for i in parsed["interventions"]}
    assert "Lutte contre les fraudes sociales et fiscales > Discussion des articles (suite) > Article 9 terdecies" in chemins


def test_les_paragraphes_des_points_imbriques_sont_vus():
    """Le défaut nº1 de #510 : `point.findall("paragraphe")` n'était pas récursif.

    Mesuré sur les trois archives, il ne voyait que 180 755 des 1 444 564
    paragraphes (12,5 %). Dans `syceron_reel_leg17.xml`, PA795310 ne parle que
    dans le `<point nivpoint="2">` imbriqué : il était invisible.
    """
    parsed = parse_syceron_xml(_load(IMBRICATION))
    ids = {i["orateur_id_source"] for i in parsed["interventions"]}
    assert "795310" in ids


def test_les_conteneurs_intermediaires_sont_traverses(structure):
    """`<interExtraction>` porte 86 163 des 103 213 paragraphes d'un échantillon
    de 200 comptes rendus de la 15e : ne pas le traverser perd la 15e entière."""
    brut = (FIXTURES / STRUCTURE).read_text(encoding="utf-8")
    assert "<interExtraction" in brut
    assert len(structure["interventions"]) >= 10


def test_ouverture_et_fin_de_seance_restent_hors_perimetre(structure):
    """Contrat inchangé : le périmètre reste « sous un `<point>` »."""
    brut = (FIXTURES / STRUCTURE).read_text(encoding="utf-8")
    assert "<ouvertureSeance" in brut
    textes = [i["texte"] for i in structure["interventions"] if i["texte"]]
    assert not any("La séance est ouverte" in t for t in textes)


# ---------------------------------------------------------------------------
# 4. Le sujet : lu là où la source le publie, et jamais fabriqué
# ---------------------------------------------------------------------------

def test_le_titre_du_point_vit_dans_point_texte_pas_dans_titrestruct(structure):
    """Défaut nº2 de #510 : `<titreStruct>` n'existe pas sous `<contenu>`.

    Il existe, mais dans `<metadonnees><sommaire>` — la fixture le montre.
    """
    import xml.etree.ElementTree as ET
    ns = "{http://schemas.assemblee-nationale.fr/referentiel}"
    racine = ET.fromstring(_load(STRUCTURE))
    metadonnees = racine.find(ns + "metadonnees")
    contenu = racine.find(ns + "contenu")

    assert list(metadonnees.iter(ns + "titreStruct")), "le sommaire réel en porte"
    assert not list(contenu.iter(ns + "titreStruct")), (
        "0 occurrence sur les 162 073 points des législatures 15, 16 et 17"
    )
    assert any(i["sujet"] for i in structure["interventions"])


def test_le_sujet_vient_du_point_qui_en_porte_un(structure):
    """`QG_1_1` porte le sujet de la question, `TITRE_TEXTE_DISCUSSION` le texte
    en discussion — mesurés comme les seuls codes de matière sur 30 322 points."""
    par_sujet = {}
    for i in structure["interventions"]:
        par_sujet.setdefault(i["sujet"], []).append(i["point_code_grammaire"])

    assert "Racisme envers les nouveaux élus" in par_sujet
    assert "Lutte contre les fraudes sociales et fiscales" in par_sujet


def test_le_sujet_survit_aux_points_de_procedure_intercales(structure):
    """Un paragraphe prononcé sous « Article 9 terdecies » garde pour sujet le
    texte en discussion, pas l'intitulé de l'article."""
    sous_article = [
        i for i in structure["interventions"]
        if (i["point_ordre_du_jour"] or "").endswith("Article 9 terdecies")
    ]
    assert sous_article
    for i in sous_article:
        assert i["sujet"] == "Lutte contre les fraudes sociales et fiscales"


def test_un_intitule_de_procedure_ne_devient_jamais_un_sujet():
    """§2 règle 8 : les tags thématiques ne sont pas des faits de procédure.

    `sujet` alimente `theme_officiel` puis `tags_thematiques` : publier
    « article 11 », « suspension et reprise de la séance » (1 009 occurrences sur
    la 17e) ou « rappel au règlement » (788) y fabriquerait de faux thèmes. Le
    titre reste lisible dans `point_ordre_du_jour`, qui est du contexte, pas un
    thème — et `sujet` reste `None`, ce qui est un résultat, pas un défaut
    (§2 règle 5). Mesuré : 12,0 % des 1 227 415 interventions indexables des
    trois archives sont dans ce cas.
    """
    parsed = parse_syceron_xml(_load(ATTRIBUTION_REFUSEE))
    inter = parsed["interventions"][0]
    assert inter["point_ordre_du_jour"] == "Article 11 (appelé par priorité - suite)"
    assert inter["point_code_grammaire"] == "DISC_ARTICLES_2_4"
    assert inter["sujet"] is None
    assert inter["type_detail"] == "debat"


def test_type_detail_vient_du_code_grammaire_avant_le_titre(structure):
    """`QG_1_1` → `question_gouvernement`, sans regex sur la prose du titre."""
    qg = [i for i in structure["interventions"] if i["point_code_grammaire"] == "QG_1_1"]
    assert qg
    for i in qg:
        assert i["type_detail"] == "question_gouvernement"


# ---------------------------------------------------------------------------
# 5. Ce que la source refuse d'attribuer
# ---------------------------------------------------------------------------

def test_attribution_contredite_par_la_source_exposee_telle_quelle():
    """Le parseur transcrit, il n'arbitre pas : `id_acteur="PA0"` est rendu tel
    quel à côté de l'identifiant nu. L'arbitrage est celui de
    `candidate_profile._normaliser_orateur_id_syceron`."""
    parsed = parse_syceron_xml(_load(ATTRIBUTION_REFUSEE))
    assert len(parsed["interventions"]) == 1
    inter = parsed["interventions"][0]
    assert inter["orateur_id_source"] == "335612"
    assert inter["orateur_id_acteur"] == "PA0"
    # L'archive écrit une espace insécable après la civilité : transcrite telle quelle.
    assert inter["orateur_nom"] == "M. Jean-Paul Lecoq"


def test_orateurs_multiples_distincts_non_attribues():
    """Correspondance ambiguë : on préfère ne rien attribuer.

    Réduction du cas réel, avec la forme réelle de l'identifiant (nue).
    """
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<compteRendu xmlns="http://schemas.assemblee-nationale.fr/referentiel">
  <uid>CRSANR5L17S2026O1N187</uid>
  <metadonnees><dateSeance>20260331150000000</dateSeance></metadonnees>
  <contenu>
    <point nivpoint="1" code_grammaire="TITRE_TEXTE_DISCUSSION">
      <texte>Questions au gouvernement</texte>
      <paragraphe id_acteur="PA0">
        <orateurs>
          <orateur><id>721908</id><nom>Mme la présidente</nom></orateur>
          <orateur><id>842013</id><nom>M. le ministre</nom></orateur>
        </orateurs>
        <texte>Texte attribuable sans ambiguïté impossible.</texte>
      </paragraphe>
    </point>
  </contenu>
</compteRendu>""".encode("utf-8")
    result = parse_syceron_xml(xml)
    assert len(result["interventions"]) == 1
    assert result["interventions"][0]["orateur_id_source"] is None
    assert result["interventions"][0]["orateur_nom"] is None


# ---------------------------------------------------------------------------
# 6. Champs manquants — jamais "" ni 0
# ---------------------------------------------------------------------------

def test_qualite_absente_donne_none(structure):
    """`<qualite />` vide → `fonction` à `None`, jamais `""` (§2 règle 5)."""
    brut = (FIXTURES / STRUCTURE).read_text(encoding="utf-8")
    assert "<qualite />" in brut
    assert any(i["fonction"] is None for i in structure["interventions"])


def test_aucun_champ_scalaire_nest_une_chaine_vide(structure):
    scalar_keys = ("date", "type_detail", "sujet", "texte", "fonction",
                   "source_id", "seance_ref", "session_ref",
                   "orateur_id_source", "orateur_id_acteur", "orateur_nom",
                   "point_ordre_du_jour", "point_code_grammaire",
                   "etat_compte_rendu", "version_compte_rendu")
    for inter in structure["interventions"]:
        for key in scalar_keys:
            assert inter.get(key) != "", f"Champ '{key}' ne doit pas être une chaîne vide"


def test_texte_inline_normalise(structure):
    """`<italique>`, `<br/>`, `<sup>` : contenu conservé, balise supprimée."""
    textes = [i["texte"] for i in structure["interventions"] if i["texte"]]
    assert textes
    for t in textes:
        assert "<" not in t


def test_format_deduit_du_volume(structure):
    formats = {i["format"] for i in structure["interventions"]}
    assert formats <= {"reaction_courte", "prise_de_parole_developpee"}
    assert "prise_de_parole_developpee" in formats


# ---------------------------------------------------------------------------
# 7. Robustesse
# ---------------------------------------------------------------------------

def test_xml_sans_contenu_retourne_liste_vide():
    xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<compteRendu xmlns="http://schemas.assemblee-nationale.fr/referentiel">
  <uid>CRSANR5L17TEST</uid>
  <metadonnees>
    <dateSeance>20250101000000000</dateSeance>
    <legislature>17</legislature>
    <etat>complet</etat>
    <version>JO</version>
  </metadonnees>
</compteRendu>"""
    result = parse_syceron_xml(xml)
    assert result["interventions"] == []
    assert result["seance"]["uid"] == "CRSANR5L17TEST"


def test_xml_accepts_str_input():
    xml_str = """<?xml version="1.0" encoding="UTF-8"?>
<compteRendu xmlns="http://schemas.assemblee-nationale.fr/referentiel">
  <uid>CRSTEST</uid>
  <metadonnees><dateSeance>20260101</dateSeance></metadonnees>
</compteRendu>"""
    result = parse_syceron_xml(xml_str)
    assert result["seance"]["uid"] == "CRSTEST"


def test_xml_malformed_raises():
    import xml.etree.ElementTree as ET
    with pytest.raises(ET.ParseError):
        parse_syceron_xml(b"<not valid xml")


def test_les_fixtures_inventees_ne_reviennent_pas():
    """Garde-fou de contexte : `syceron_minimal.xml` et `syceron_missing_fields.xml`
    décrivaient un schéma que l'Assemblée nationale ne publie pas. Elles sont
    retirées ; les réintroduire, c'est réarmer la cause de #510."""
    for nom in ("syceron_minimal.xml", "syceron_missing_fields.xml"):
        assert not (FIXTURES / nom).exists(), (
            f"{nom} décrit un schéma inventé — relire #510 avant de la réintroduire"
        )
