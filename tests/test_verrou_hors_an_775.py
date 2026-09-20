"""Le verrou : sans profil pas d'entrée, sans entrée pas de profil (#775).

Le run `34168924759` a réussi et committé — et il a laissé **cinq candidats
déclarés** sans profil ni entrée de table : Asselineau, Kazib, Lalanne,
Bouamrane, Durif. Le portail les signale en **soft**, donc rien ne bloque, et
**aucun run futur ne les aurait débloqués** :

  pour recevoir une ENTRÉE, il faut un PROFIL publié — filtre 2 de #715, il n'y
  a rien à corroborer sans lui ;
  pour recevoir un PROFIL, il fallait une ENTRÉE déclarant `hors_an` (#539).

Trois candidats y avaient échappé parce qu'une main avait écrit leur entrée
(#766), trois autres parce que la branche UE leur avait donné un profil. Les
cinq restants n'avaient ni l'un ni l'autre.

Le lot ajoute une **seconde déclaration** : un identifiant externe qui ne connaît
aucun mandat AN à cette personne. Ce que ces tests protègent, c'est ce qu'elle ne
relâche pas — `indetermine` n'est pas une déclaration, et une panne de collecte
n'en devient pas une.
"""

import json
import re
from pathlib import Path

import pytest

import perimetre_candidats as perimetre


@pytest.fixture(autouse=True)
def _memo_propre():
    perimetre.vider_memo_resolutions()
    yield
    perimetre.vider_memo_resolutions()


def _resolutions(tmp_path: Path, **issues) -> Path:
    chemin = tmp_path / "resolutions.json"
    chemin.write_text(
        json.dumps(
            {
                "schema_version": "resolutions-candidats-v1",
                "resolutions": {
                    nom: {"nom": nom, "issue": issue, "acteur_ref": None, "qid": "Q1",
                          "preuve": "https://www.wikidata.org/wiki/Q1"}
                    for nom, issue in issues.items()
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return chemin


def test_un_hors_an_est_une_declaration(tmp_path):
    chemin = _resolutions(tmp_path, Asselineau="hors_an")
    assert perimetre.declare_hors_an_par_identifiant("Asselineau", chemin) is True


def test_un_acteur_nest_pas_une_declaration_dabsence(tmp_path):
    chemin = _resolutions(tmp_path, Cazeneuve="acteur")
    assert perimetre.declare_hors_an_par_identifiant("Cazeneuve", chemin) is False


def test_indetermine_ne_vaut_PAS_declaration(tmp_path):
    """« Wikidata ne décrit pas cette personne » et « Wikidata la décrit et ne
    lui connaît aucun mandat » sont deux affirmations différentes (#757).

    Une seule est un fait. Confondre les deux écrirait « n'a jamais siégé » sur
    quelqu'un dont on ne sait rien.
    """
    chemin = _resolutions(tmp_path, Labib="indetermine")
    assert perimetre.declare_hors_an_par_identifiant("Labib", chemin) is False


def test_un_nom_absent_du_fichier_ne_declare_rien(tmp_path):
    chemin = _resolutions(tmp_path, Autre="hors_an")
    assert perimetre.declare_hors_an_par_identifiant("Inconnu", chemin) is False


def test_un_fichier_absent_ou_illisible_ne_declare_rien(tmp_path):
    """L'absence de preuve n'est pas une preuve d'absence : l'appelant retombe
    sur son comportement d'avant."""
    assert perimetre.declare_hors_an_par_identifiant("X", tmp_path / "pas_la.json") is False
    casse = tmp_path / "casse.json"
    casse.write_text("{ pas du json", encoding="utf-8")
    perimetre.vider_memo_resolutions()
    assert perimetre.declare_hors_an_par_identifiant("X", casse) is False


def test_aucun_chemin_ne_declare_rien():
    assert perimetre.declare_hors_an_par_identifiant("X", None) is False


def test_le_memo_ne_relit_pas_le_fichier(tmp_path, monkeypatch):
    """Relu une fois par candidat dans un shard, et il ne change pas du run."""
    chemin = _resolutions(tmp_path, A="hors_an")
    assert perimetre.declare_hors_an_par_identifiant("A", chemin) is True
    chemin.unlink()
    assert perimetre.declare_hors_an_par_identifiant("A", chemin) is True


# ---------------------------------------------------------------------------
# Ce que la garde de #484 continue de protéger
# ---------------------------------------------------------------------------


def test_la_condition_du_squelette_garde_en_echec():
    """La seconde déclaration s'ajoute à la première ; elle ne desserre pas la
    garde qui distingue une ABSENCE d'une PANNE.

    Une collecte en panne rend exactement le même vide qu'une absence, et écrire
    un squelette dessus reste le défaut de #484.
    """
    src = (Path(__file__).resolve().parents[1] / "src" / "generate_all_profiles.py").read_text(
        encoding="utf-8"
    )
    assert "if not en_echec and declaree_hors_an:" in src, (
        "la garde `en_echec` a disparu de la condition du profil minimal"
    )
    assert "declare_hors_an_par_identifiant" in src


# ---------------------------------------------------------------------------
# La symétrie des deux places (#781)
# ---------------------------------------------------------------------------


def _source_generate() -> str:
    return (Path(__file__).resolve().parents[1] / "src" / "generate_all_profiles.py").read_text(
        encoding="utf-8"
    )


def test_les_deux_places_acceptent_la_meme_declaration():
    """Écrire le brut et le publier en pivot sont deux décisions, au même titre.

    #775 n'avait étendu que la première. Le run `34211117684` a donc écrit cinq
    profils bruts sans aucun pivot, et le garde-fou de #511 a bloqué le commit —
    « collecté mais non publié », exactement ce que le commentaire de
    `_normaliser_en_pivot` annonçait.

    Une déclaration qui autorise la COLLECTE doit autoriser la PUBLICATION :
    sans quoi le profil existe et n'atteint aucune vue.
    """
    src = _source_generate()
    assert src.count("declare_hors_an_par_identifiant") >= 2, (
        "une seule des deux places consulte l'identifiant externe — l'autre "
        "produira un « collecté mais non publié »"
    )


def test_la_place_du_pivot_consulte_bien_lidentifiant():
    """Le test ci-dessus compte ; celui-ci vise l'endroit."""
    src = _source_generate()
    bloc = re.search(r"def _normaliser_en_pivot\((.*?)\n    if mandat_ue is not None:", src, re.DOTALL)
    assert bloc, "`_normaliser_en_pivot` a changé de forme"
    assert "declare_hors_an_par_identifiant" in bloc.group(1)
    assert 'entree.get("ecart") == "hors_an"' in bloc.group(1), (
        "la table reste la première déclaration ; elle ne doit pas disparaître"
    )
