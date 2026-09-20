"""#827 — une clé de déduplication ne doit dépendre d'aucun champ qui apparaît.

`_interv_key` passait par `source_url` avant le contenu. Les explications de
vote n'ayant pas d'`intervention_id`, leur clé était le contenu avant #827 et
l'URL après : la fusion additive a publié 1 462 doublons.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from normalize_parltrack_dumps import enrich_pivot_with_parltrack  # noqa: E402,F401
from purger_doublons_interventions_827 import cle_de_contenu, purger  # noqa: E402


def _expl(sujet, texte, url=None):
    e = {"intervention_id": None, "date": "2017-05-01", "sujet": sujet,
         "texte": texte, "type_detail": "explication_de_vote"}
    if url:
        e["source_url"] = url
    return e


# ---------------------------------------------------------------------------
# La purge
# ---------------------------------------------------------------------------

def test_le_doublon_est_retire_et_c_est_l_exemplaire_avec_lien_qui_reste():
    """Les deux entrées sont identiques par ailleurs : garder celle sans lien
    rejetterait le travail de #827."""
    profil = {"interventions": [
        _expl("EGF (A8-0196/2017)", "J'ai voté pour."),
        _expl("EGF (A8-0196/2017)", "J'ai voté pour.", "https://exemple/doc"),
    ]}
    retirees, restantes = purger(profil)
    assert (retirees, restantes) == (1, 1)
    assert profil["interventions"][0]["source_url"] == "https://exemple/doc"


def test_l_ordre_des_deux_exemplaires_est_indifferent():
    profil = {"interventions": [
        _expl("EGF", "J'ai voté pour.", "https://exemple/doc"),
        _expl("EGF", "J'ai voté pour."),
    ]}
    purger(profil)
    assert profil["interventions"][0]["source_url"] == "https://exemple/doc"


def test_sans_lien_des_deux_cotes_une_seule_survit():
    """Les 271 explications dont l'intitulé ne cite aucun document."""
    profil = {"interventions": [
        _expl("Allocation of slots", "Je me suis abstenue."),
        _expl("Allocation of slots", "Je me suis abstenue."),
    ]}
    retirees, restantes = purger(profil)
    assert (retirees, restantes) == (1, 1)


def test_deux_explications_differentes_ne_sont_pas_fusionnees():
    profil = {"interventions": [
        _expl("EGF", "J'ai voté pour."),
        _expl("EGF", "J'ai voté contre."),
    ]}
    assert purger(profil) == (0, 2)


def test_les_interventions_a_identifiant_ne_sont_JAMAIS_touchees():
    """902 457 entrées à identifiants différents partagent une clé de contenu —
    les interventions en mode thème-seul n'ont ni sujet ni texte. Les
    dédoublonner sur le contenu détruirait 88 % du corpus."""
    profil = {"interventions": [
        {"intervention_id": "syceron_CRSANR5L16S2023O1N245_000001",
         "date": "2023-01-01", "sujet": None, "texte": None},
        {"intervention_id": "syceron_CRSANR5L16S2023O1N245_000002",
         "date": "2023-01-01", "sujet": None, "texte": None},
    ]}
    assert purger(profil) == (0, 2)


def test_un_profil_sans_interventions_ne_casse_pas():
    assert purger({}) == (0, 0)
    assert purger({"interventions": None}) == (0, 0)


def test_la_cle_de_contenu_ignore_l_url():
    """C'est tout le point : l'URL peut apparaître, la clé ne doit pas bouger."""
    sans = _expl("EGF", "J'ai voté pour.")
    avec = _expl("EGF", "J'ai voté pour.", "https://exemple/doc")
    assert cle_de_contenu(sans) == cle_de_contenu(avec)


# ---------------------------------------------------------------------------
# La clé corrigée, à la source
# ---------------------------------------------------------------------------

def test_la_cle_de_fusion_ne_depend_plus_de_source_url():
    """Le témoin de la récidive : si `source_url` revenait dans la cascade, une
    entrée déjà publiée cesserait d'être reconnue dès qu'elle gagne un lien."""
    source = (Path(__file__).resolve().parents[1]
              / "src" / "normalize_parltrack_dumps.py").read_text(encoding="utf-8")
    debut = source.index("def _interv_key(")
    corps = source[debut:source.index("cles_interv = {", debut)]
    apres_docstring = corps.split('"""')[-1]
    assert "source_url" not in apres_docstring, (
        "`source_url` est de retour dans la cascade de `_interv_key` : une clé "
        "de déduplication ne doit dépendre d'aucun champ qui peut apparaître "
        "après une première publication (#827)."
    )
