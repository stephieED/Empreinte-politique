"""Le titre d'un texte européen est publié en français quand la source l'a (#901).

Le dump ParlTrack donne les titres en ANGLAIS — « JOINT MOTION FOR A RESOLUTION
on Azerbaijan… ». Le portail du Parlement publie le même document en 22 à 23
langues, français compris, et `ResolveurDocuments` téléchargeait déjà cette
réponse pour n'en tirer qu'un booléen d'existence : le titre français était
récupéré puis jeté.

Ce n'est donc pas une traduction que nous fabriquerions — ce serait interdit —,
c'est la version française officielle, sous la licence du portail (§7).

Mesuré le 16/09/2026 sur 20 des 628 résolutions sans dossier : 20 sur 20 ont un
titre français, 19 un titre anglais.

Ce que ce test tient surtout : **le repli**. Quand le portail n'a rien à dire —
pas de référence citée, document introuvable, question non posée — le titre
anglais du dump est conservé et `titre_langue` le dit. Publier un titre vide
serait pire que le publier dans la mauvaise langue (§2 règle 5).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))

from europarl_documents import ResolveurDocuments  # noqa: E402
from normalize_parltrack_dumps import _titre_publie  # noqa: E402

TITRE_EN = "JOINT MOTION FOR A RESOLUTION on Azerbaijan, notably the repression"
TITRE_FR = "PROPOSITION DE RÉSOLUTION COMMUNE sur l’Azerbaïdjan, notamment la répression"
DOCEO = "RC-9-2024-0227"


class _Reponse:
    def __init__(self, status_code, charge=None, headers=None):
        self.status_code = status_code
        self._charge = charge
        self.headers = headers or {}

    def json(self):
        if self._charge is None:
            raise ValueError("pas de corps JSON")
        return self._charge


class _Session:
    """Rejoue le portail. `data` en objet OU en liste : les deux se rencontrent."""

    def __init__(self, titres, en_liste=False):
        self.titres = titres
        self.en_liste = en_liste
        self.appels = []

    def get(self, url, params=None, timeout=None):
        self.appels.append(url)
        doceo = url.rsplit("/", 1)[-1]
        if doceo not in self.titres:
            return _Reponse(404)
        data = {"title_dcterms": {"fr": self.titres[doceo], "en": TITRE_EN}}
        return _Reponse(200, {"data": [data] if self.en_liste else data})


def _resolveur(tmp_path, session):
    return ResolveurDocuments(cache_path=tmp_path / "c.json", session=session)


# --- le résolveur -----------------------------------------------------------

@pytest.mark.parametrize("en_liste", [False, True])
def test_le_titre_francais_est_lu_quelle_que_soit_la_forme(tmp_path, en_liste):
    r = _resolveur(tmp_path, _Session({DOCEO: TITRE_FR}, en_liste=en_liste))
    assert r.titre_francais(DOCEO) == TITRE_FR


def test_un_document_introuvable_n_a_pas_de_titre(tmp_path):
    r = _resolveur(tmp_path, _Session({}))
    assert r.existe(DOCEO) is False
    assert r.titre_francais(DOCEO) is None


def test_le_titre_ne_coute_pas_une_requete_de_plus(tmp_path):
    """Le portail est lent et limité : existence et titre viennent du MÊME appel."""
    session = _Session({DOCEO: TITRE_FR})
    r = _resolveur(tmp_path, session)
    r.existe(DOCEO)
    r.titre_francais(DOCEO)
    assert len(session.appels) == 1


def test_hors_ligne_ne_rend_pas_un_titre_vide(tmp_path):
    r = ResolveurDocuments(cache_path=tmp_path / "c.json", hors_ligne=True)
    assert r.titre_francais(DOCEO) is None


def test_un_cache_v1_se_relit_sans_etre_invalide(tmp_path):
    """Les booléens déjà en cache valent « existe, titre inconnu »."""
    p = tmp_path / "c.json"
    p.write_text(json.dumps({"schema_version": "documents-doceo-v1",
                             "documents": {DOCEO: True, "B-8-2015-0001": False}}),
                 encoding="utf-8")
    r = ResolveurDocuments(cache_path=p, hors_ligne=True)
    assert r.existe(DOCEO) is True
    assert r.existe("B-8-2015-0001") is False
    assert r.titre_francais(DOCEO) is None


def test_le_cache_ecrit_porte_le_titre(tmp_path):
    p = tmp_path / "c.json"
    r = ResolveurDocuments(cache_path=p, session=_Session({DOCEO: TITRE_FR}))
    r.titre_francais(DOCEO)
    r.enregistrer()
    ecrit = json.loads(p.read_text(encoding="utf-8"))
    # v3 depuis l'ajout des concepts EuroVoc (#901) : la réponse du portail en
    # porte trois faits, et les jeter pour en garder un seul était le défaut.
    assert ecrit["schema_version"] == "documents-doceo-v3"
    assert ecrit["documents"][DOCEO] == {
        "existe": True, "titre_fr": TITRE_FR, "concepts": []}


# --- le titre publié sur la fiche -------------------------------------------

# Entrées COPIÉES du corpus (origin/main 46216eb7e), pas inventées. La version
# précédente de ces deux tests plaçait une référence « (A9-0227/2024) » dans le
# titre ; aucun des 694 titres publiés n'en porte, et le run 35087127267 a
# publié 0 titre français pendant que ces tests passaient.
ENTREE_MAUREL = {  # emmanuel-maurel.pivot.json
    "titre": "JOINT MOTION FOR A RESOLUTION on Azerbaijan, notably the repression of "
             "civil society and the cases of Dr Gubad Ibadoghlu and Ilhamiz Guliyev",
    "source_url": "https://www.europarl.europa.eu/doceo/document/RC-9-2024-0227_EN.html",
}
ENTREE_PHILIPPOT = {  # florian-philippot.pivot.json — en http://, comme 625 URL du corpus
    "titre": "Motion for a resolution on accessibility of goods and services",
    "source_url": "http://www.europarl.europa.eu/doceo/document/B-8-2017-0240_EN.html",
}


def test_aucun_titre_reel_ne_porte_de_reference():
    """La prémisse de la première version, démentie : elle est tenue ici."""
    from europarl_documents import reference_doceo
    assert reference_doceo(ENTREE_MAUREL["titre"]) is None
    assert reference_doceo(ENTREE_PHILIPPOT["titre"]) is None


def test_le_francais_remplace_l_anglais_et_la_langue_le_dit(tmp_path):
    r = _resolveur(tmp_path, _Session({"RC-9-2024-0227": TITRE_FR}))
    assert _titre_publie(ENTREE_MAUREL, r) == (TITRE_FR, "fr")


def test_une_url_en_http_trouve_aussi_son_titre(tmp_path):
    r = _resolveur(tmp_path, _Session({"B-8-2017-0240": "PROPOSITION DE RÉSOLUTION"}))
    assert _titre_publie(ENTREE_PHILIPPOT, r) == ("PROPOSITION DE RÉSOLUTION", "fr")


def test_sans_titre_francais_l_anglais_est_conserve(tmp_path):
    """Le repli : un titre dans la mauvaise langue vaut mieux qu'un titre vide."""
    titre, langue = _titre_publie(ENTREE_MAUREL, _resolveur(tmp_path, _Session({})))
    assert (titre, langue) == (ENTREE_MAUREL["titre"], "en")


def test_sans_source_url_le_titre_reste_anglais(tmp_path):
    entree = {"titre": ENTREE_MAUREL["titre"], "source_url": None}
    r = _resolveur(tmp_path, _Session({"RC-9-2024-0227": TITRE_FR}))
    assert _titre_publie(entree, r) == (ENTREE_MAUREL["titre"], "en")


# --- le cache qui ne se réinterrogeait jamais --------------------------------

def test_une_entree_v1_est_reinterrogee_pour_son_titre(tmp_path):
    """Troisième défaut du run 35087127267 : la promesse « le titre se remplira
    à la prochaine interrogation » n'était tenue par rien — une entrée en cache
    n'était jamais redemandée."""
    p = tmp_path / "c.json"
    p.write_text(json.dumps({"schema_version": "documents-doceo-v1",
                             "documents": {"RC-9-2024-0227": True}}), encoding="utf-8")
    session = _Session({"RC-9-2024-0227": TITRE_FR})
    r = ResolveurDocuments(cache_path=p, session=session)
    assert r.titre_francais("RC-9-2024-0227") == TITRE_FR
    assert len(session.appels) == 1


def test_existe_seul_ne_reinterroge_pas_une_entree_v1(tmp_path):
    """Sinon les ~1 500 explications de vote déjà connues seraient redemandées."""
    p = tmp_path / "c.json"
    p.write_text(json.dumps({"schema_version": "documents-doceo-v1",
                             "documents": {"RC-9-2024-0227": True}}), encoding="utf-8")
    session = _Session({"RC-9-2024-0227": TITRE_FR})
    r = ResolveurDocuments(cache_path=p, session=session)
    assert r.existe("RC-9-2024-0227") is True
    assert session.appels == []


def test_une_entree_complete_n_est_pas_redemandee(tmp_path):
    session = _Session({"RC-9-2024-0227": TITRE_FR})
    r = _resolveur(tmp_path, session)
    r.titre_francais("RC-9-2024-0227")
    r.titre_francais("RC-9-2024-0227")
    r.concepts_eurovoc("RC-9-2024-0227")
    assert len(session.appels) == 1


def test_un_document_inexistant_n_est_pas_redemande(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps({"schema_version": "documents-doceo-v1",
                             "documents": {"B-8-2015-0001": False}}), encoding="utf-8")
    session = _Session({})
    r = ResolveurDocuments(cache_path=p, session=session)
    assert r.titre_francais("B-8-2015-0001") is None
    assert session.appels == []


def test_un_echec_garde_ce_qu_on_savait(tmp_path):
    """Portail muet sur une entrée v1 : l'existence connue n'est pas perdue."""
    class _Muet:
        def get(self, *a, **k):
            raise TimeoutError("silence")
    p = tmp_path / "c.json"
    p.write_text(json.dumps({"schema_version": "documents-doceo-v1",
                             "documents": {"RC-9-2024-0227": True}}), encoding="utf-8")
    r = ResolveurDocuments(cache_path=p, session=_Muet())
    assert r.titre_francais("RC-9-2024-0227") is None
    assert r.existe("RC-9-2024-0227") is True


def test_sans_resolveur_rien_ne_change(tmp_path):
    entree = {"titre": TITRE_EN}
    assert _titre_publie(entree, None) == (TITRE_EN, "en")


def test_un_titre_absent_ne_fabrique_pas_de_langue():
    assert _titre_publie({}, None) == ("", None)


def test_un_cache_v2_ne_ment_pas_sur_les_concepts(tmp_path):
    """v2 ne connaissait pas les concepts : `None`, jamais `[]`.

    Une liste vide dirait « ce document n'est classé sous aucun concept », ce
    que le cache v2 ne peut pas savoir. L'entrée vaut « concepts inconnus », et
    se remplira à la prochaine interrogation (§2 règle 5).
    """
    p = tmp_path / "c.json"
    p.write_text(json.dumps({"schema_version": "documents-doceo-v2",
                             "documents": {DOCEO: {"existe": True, "titre_fr": TITRE_FR}}}),
                 encoding="utf-8")
    r = ResolveurDocuments(cache_path=p, hors_ligne=True)
    assert r.existe(DOCEO) is True
    assert r.titre_francais(DOCEO) == TITRE_FR
    assert r.concepts_eurovoc(DOCEO) is None


def test_les_concepts_sont_lus_depuis_is_about(tmp_path):
    class _S:
        def get(self, url, params=None, timeout=None):
            return _Reponse(200, {"data": {"is_about": [
                "http://eurovoc.europa.eu/2155", "http://eurovoc.europa.eu/5454"]}})

    r = ResolveurDocuments(cache_path=tmp_path / "c.json", session=_S())
    assert r.concepts_eurovoc(DOCEO) == ["2155", "5454"]


def test_un_document_sans_is_about_rend_une_liste_vide(tmp_path):
    """Le portail répond et ne classe pas : `[]`, pas `None`."""
    class _S:
        def get(self, url, params=None, timeout=None):
            return _Reponse(200, {"data": {"title_dcterms": {"fr": "T"}}})

    r = ResolveurDocuments(cache_path=tmp_path / "c.json", session=_S())
    assert r.concepts_eurovoc(DOCEO) == []
