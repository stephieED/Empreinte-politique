"""#1042 — un singulier et un pluriel sont le même sujet.

« motion de censure » et « motions de censure » arrivaient en première et
deuxième ligne de la fiche du gouvernement Borne, avec 19 et 12 porteurs.
Signalé par la session « UI gouv » le 20/09/2026, reproduit côté backend.

Mesuré avant d'écrire la règle, sur un profil publié sur quatre : 4 025 clés,
**10 à plusieurs formes**. Et parmi ces 10, **4 ont une forme normalisée que la
source n'écrit jamais** — « pénurie de médicament », « fermeture de classe ».
D'où la règle : la clé GROUPE, la forme publiée reste OBSERVÉE.
"""
from __future__ import annotations

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from collections import Counter  # noqa: E402

from schema_pivot import (  # noqa: E402
    cle_tag_thematique,
    deriver_tags_thematiques,
    forme_publiee,
)
from gouvernement_profile import agreger_tags_thematiques  # noqa: E402


def _interv(date: str, theme: str) -> dict:
    return {"intervention_id": f"s_{theme}_{date}", "date": date,
            "theme_officiel": theme, "mots_cles": []}


# ── La clé ────────────────────────────────────────────────────────────────

def test_la_cle_rapproche_un_pluriel_de_son_singulier():
    assert cle_tag_thematique("motions de censure") == cle_tag_thematique("motion de censure")


def test_la_cle_laisse_intact_un_mot_tres_court_en_s():
    """« gaz » n'est pas un pluriel, et le seuil de 3 lettres le protège.

    Il ne protège PAS « sens » ni « ours », qui rendent « sen » et « our ».
    C'est assumé : la clé ne sert qu'à regrouper, et il faudrait qu'un « sen »
    existe par ailleurs pour que deux sujets se confondent — sur les 4 025
    clés mesurées, les 10 groupes formés sont tous légitimes.
    """
    assert cle_tag_thematique("gaz") == "gaz"
    assert cle_tag_thematique("sens") == "sen"


def test_la_cle_ne_lemmatise_pas():
    """Elle ne rapproche que ce qu'un `s` final sépare — pas « travail » et
    « travaux ». Une lemmatisation déciderait que deux intitulés publiés n'en
    font qu'un, ce qui n'a pas été arbitré."""
    assert cle_tag_thematique("travail") != cle_tag_thematique("travaux")


# ── La forme publiée ──────────────────────────────────────────────────────

def test_la_forme_publiee_est_la_plus_frequente():
    assert forme_publiee(Counter({"motion de censure": 109, "motions de censure": 69})) \
        == "motion de censure"


def test_une_egalite_se_departage_par_l_alphabet():
    """Déterministe : deux profils traités séparément doivent publier la même."""
    assert forme_publiee(Counter({"b": 2, "a": 2})) == "a"


def test_la_forme_publiee_n_est_jamais_une_forme_inventee():
    """Le cas qui a décidé de la règle : la source écrit toujours
    « médicaments » au pluriel, la clé vaut « pénurie de médicament »."""
    compte = Counter({"pénurie de médicaments": 7, "pénuries de médicaments": 1})
    assert forme_publiee(compte) == "pénurie de médicaments"
    assert forme_publiee(compte) != cle_tag_thematique("pénurie de médicaments")


# ── La fabrique et les agrégats ───────────────────────────────────────────

def test_les_deux_formes_ne_font_qu_une_etiquette():
    tags = deriver_tags_thematiques(
        [_interv("2024-01-01", "Motion de censure")] * 3
        + [_interv("2024-01-02", "Motions de censure")])

    assert tags == ["motion de censure"]


def test_l_agregat_de_gouvernement_compte_un_seul_sujet():
    """Deux membres, deux formes : une ligne, deux porteurs — et non deux
    lignes d'un porteur. C'est ce que la fiche de Borne affichait."""
    fenetres = {"a": [("2024-01-01", "2024-12-31")], "b": [("2024-01-01", "2024-12-31")]}
    interventions = {
        "a": [_interv("2024-03-01", "Motion de censure")],
        "b": [_interv("2024-03-02", "Motions de censure")],
    }

    tags, porteurs, _, _ = agreger_tags_thematiques(
        fenetres, lambda membre_id: interventions.get(membre_id, []))

    assert tags == [{"tag": "motion de censure", "nb_membres_porteurs": 2}]
    assert porteurs == 2
