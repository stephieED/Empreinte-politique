"""Un texte porté européen est identifié par son document, pas par son titre (#901).

Mesuré le 16/09/2026 sur `origin/main` `c6990c688` : 311 textes portés européens
publiés deux fois dans le même profil — Philippot 250, Le Pen 57, Mélenchon 4.
Un texte européen n'a pas de `dossier_id`, il était donc rangé sur le repli
`(titre, date_min, legislature)`. #938 a nettoyé les titres, le repli a changé,
et la fusion additive a ajouté au lieu de reconnaître.

LES ENTRÉES CI-DESSOUS SONT COPIÉES DU CORPUS, pas imaginées. Le lot précédent
(#960) avait été testé sur un titre fabriqué — « …(A9-0227/2024) » — qui n'existe
dans aucun des 694 titres publiés, et il n'a produit aucun titre français. Une
fixture qui décrit le monde comme le code l'imagine ne peut pas révéler que le
monde est autrement (#726).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))

from merge_profile import _pivot_texte_key, merge_dossier_records  # noqa: E402

# florian-philippot.pivot.json, origin/main c6990c688 — les deux copies réelles.
SALE = {
    "titre": "Motion for a resolution on accessibility of goods and services PDF (181 KB) DOC (45 KB)",
    "institution": "parlement_europeen",
    "nature_texte": "proposition_de_resolution",
    "role": "auteur_proposition_de_resolution",
    "type_rapport": None,
    "reference_dossier": None,
    "stade_procedural": None,
    "stade_procedural_non_resolu": {"motif": "activite_sans_dossier"},
    "sort": None,
    "sort_non_resolu": {"motif": "source_sans_sort"},
    "date_min": "2016-11-22",
    "date_max": "2016-11-22",
    "legislature": None,
    "source_url": "http://www.europarl.europa.eu/doceo/document/B-8-2017-0240_EN.html",
}
PROPRE = {**SALE, "titre": "Motion for a resolution on accessibility of goods and services",
          "titre_langue": "en"}

# emmanuel-maurel.pivot.json — deux textes DIFFÉRENTS sur la même procédure.
AVIS_MAUREL = {
    "titre": "OPINION on the role of EU development policy in transforming extractive "
             "industries for sustainable development in developing countries",
    "institution": "parlement_europeen", "role": "rapporteur", "nature_texte": None,
    "date_min": "2023-07-20", "source_url": None, "reference_dossier": "2023/2031(INI)",
}
DOSSIER_MAUREL = {
    "titre": "The role of EU development policy in transforming extractive industries "
             "for sustainable development in developing countries",
    "institution": "parlement_europeen", "role": "rapporteur", "nature_texte": None,
    "date_min": "2023-03-21", "reference_dossier": "2023/2031(INI)",
    "source_url": "https://oeil.secure.europarl.europa.eu/oeil/popups/ficheprocedure.do"
                  "?reference=2023/2031(INI)&l=en",
}


def test_les_deux_copies_reelles_partagent_une_cle():
    assert _pivot_texte_key(SALE) == _pivot_texte_key(PROPRE) == ("doceo", "B-8-2017-0240")


def test_la_fusion_garde_une_seule_copie_la_propre():
    fusion = merge_dossier_records([SALE], [PROPRE], _pivot_texte_key)
    assert fusion == [PROPRE]


def test_deux_copies_deja_publiees_se_reduisent_a_la_derniere():
    """L'état exact du corpus : les deux copies dans l'ancienne liste, sale d'abord."""
    fusion = merge_dossier_records([SALE, PROPRE], [], _pivot_texte_key)
    assert fusion == [PROPRE]


def test_le_schema_de_l_url_ne_fait_pas_deux_textes():
    """625 source_url en http://, 56 en https:// : une migration ne doit rien doubler."""
    https = {**PROPRE, "source_url": PROPRE["source_url"].replace("http://", "https://")}
    assert _pivot_texte_key(https) == _pivot_texte_key(PROPRE)


def test_deux_textes_de_la_meme_procedure_restent_deux():
    """Pourquoi la clé n'est PAS `reference_dossier` : elle aurait supprimé l'avis."""
    fusion = merge_dossier_records([AVIS_MAUREL], [DOSSIER_MAUREL], _pivot_texte_key)
    assert len(fusion) == 2


def test_un_texte_de_l_assemblee_garde_sa_cle():
    t = {"titre": "Proposition de loi", "dossier_id": "DLR5L17N47389",
         "source_url": "https://www.europarl.europa.eu/doceo/document/B-8-2017-0240_EN.html"}
    assert _pivot_texte_key(t) == ("dossier_id", "DLR5L17N47389")


def test_un_document_doceo_non_europeen_n_est_pas_lu_comme_tel():
    """Seule `institution == parlement_europeen` emprunte la branche doceo."""
    t = {"titre": "x", "date_min": "2020-01-01", "legislature": 15,
         "source_url": "https://www.europarl.europa.eu/doceo/document/B-8-2017-0240_EN.html"}
    assert _pivot_texte_key(t)[0] == "repli"


def _script():
    chemin = RACINE / "scripts" / "purger_doublons_textes_europeens_901.py"
    spec = importlib.util.spec_from_file_location("purge901", chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_la_reprise_retire_le_doublon_et_rien_d_autre():
    profil = {"textes_portes": [SALE, AVIS_MAUREL, PROPRE, DOSSIER_MAUREL]}
    retires, restants = _script().purger(profil)
    assert (retires, restants) == (1, 3)
    assert PROPRE in profil["textes_portes"] and SALE not in profil["textes_portes"]


def test_la_reprise_ne_touche_pas_un_profil_sain():
    profil = {"textes_portes": [PROPRE, AVIS_MAUREL, DOSSIER_MAUREL]}
    avant = list(profil["textes_portes"])
    assert _script().purger(profil) == (0, 3)
    assert profil["textes_portes"] == avant
