"""Identifiant de dossier législatif sur les textes portés (issue #639, rang 2).

`_normalize_texte_porte` construisait un dict de huit clés où `id` ne figurait
pas, alors que le profil brut le porte : `dossiers_legislatifs[].id`, forme
`DLR5L15N37607`, écrit par `candidate_profile._build_acteur_textes_portes_index`
depuis le `uid` du dossier AN. Mesuré le 31/08/2026 sur le corpus committé :
**472 / 472** entrées brutes en portent un, 464 dossiers distincts, 22 profils —
et **0 / 472** entrées publiées le portaient.

Le nom `dossier_id` n'est pas choisi ici : c'est celui que les fiches de
gouvernement publient déjà pour les mêmes dossiers (`textes[].dossier_id`,
63 / 63 sur LECORNU_II). Deux noms pour un même identifiant obligeraient
n'importe quel croisement à retomber sur le libellé.

FIXTURE. Réduction verbatim d'une entrée réelle de
`raw_data/profiles/edouard-philippe.json` (283 / 283 y portent un `id`).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from normalize_profil import _normalize_texte_porte, normalize_profil  # noqa: E402
from schema_pivot import validate_profil  # noqa: E402

# Verbatim : première entrée de `dossiers_legislatifs` d'edouard-philippe.
DOSSIER_REEL = {
    "id": "DLR5L15N37607",
    "titre": "Accord économique et commercial global (CETA) et accord de partenariat "
             "stratégique entre l'UE et le Canada",
    "role": "auteur",
    "type_rapport": None,
    "stade_procedural": "adopte",
    "sort": "adopte",
    "date_min": "2019-06-19",
    "date_max": "2024-03-21",
    "legislature": "15",
    "source_url": "https://www.assemblee-nationale.fr/dyn/15/dossiers/"
                  "aecg_partenariat_strategique_ue-canada",
}


def test_dossier_id_est_recopie_verbatim():
    """La clé est déjà collectée : elle est reprise telle quelle, jamais
    reconstruite depuis un titre ou une URL (AGENTS.md §2 règle 2)."""
    assert _normalize_texte_porte(DOSSIER_REEL)["dossier_id"] == "DLR5L15N37607"


def test_dossier_id_absent_reste_null():
    """Une entrée héritée sans `id` ne se voit pas inventer de clé : la
    normalisation traverse la fusion additive avec des entrées anciennes
    (AGENTS.md §2 règle 5)."""
    sans_id = {k: v for k, v in DOSSIER_REEL.items() if k != "id"}
    assert _normalize_texte_porte(sans_id)["dossier_id"] is None
    assert _normalize_texte_porte({**DOSSIER_REEL, "id": ""})["dossier_id"] is None


def test_le_reste_du_texte_porte_est_inchange():
    """Rang 2 est une addition de champ, pas une refonte : les huit clés
    existantes doivent sortir identiques, sinon le contrôle de perte verrait
    une régression là où il n'y a qu'un ajout."""
    normalise = _normalize_texte_porte(DOSSIER_REEL)
    assert normalise["titre"] == DOSSIER_REEL["titre"]
    assert normalise["role"] == "auteur"
    assert normalise["stade_procedural"] == "adopte"
    assert normalise["date_min"] == "2019-06-19"
    assert normalise["date_max"] == "2024-03-21"
    assert normalise["legislature"] == "15"
    assert normalise["source_url"] == DOSSIER_REEL["source_url"], (
        "La collecte AN écrit `source_url` depuis #400 : ne pas la lire publiait "
        "472 / 472 textes portés sans source primaire (AGENTS.md §2 règle 2)"
    )
    assert set(normalise) == {
        "titre", "dossier_id", "role", "nature_texte", "type_rapport",
        "stade_procedural", "date_min", "date_max", "legislature", "source_url",
        "sort", "sort_non_resolu",
    }, "clés ajoutées : `nature_texte` (#689), `sort` et `sort_non_resolu` (#743)"
    # #743 — l'ISSUE se lit à côté de la PROGRESSION, jamais à sa place.
    # #747 — le sort de la fixture est RECOPIÉ, pas dérivé : la preuve tient au
    # contre-exemple ci-dessous, où stade et sort divergent, et non à une
    # entrée qui n'en porterait aucun. Cette fixture-là décrivait le monde
    # d'avant #743 ; les 423 entrées brutes du corpus portent toutes les deux
    # clés, et une entrée qui n'en porterait aucune est désormais refusée par
    # `validate_profil` (absence sans cause, §2 règle 5).
    assert normalise["sort"] == "adopte"
    assert normalise["sort_non_resolu"] is None
    divergent = _normalize_texte_porte(
        {**DOSSIER_REEL, "stade_procedural": "adopte", "sort": "rejete"}
    )
    assert divergent["sort"] == "rejete", (
        "la normalisation ne doit pas déduire le sort du stade procédural"
    )


def test_profil_pivot_complet_reste_valide():
    """Le champ ajouté ne doit rien casser côté `validate_profil`."""
    brut = {
        "slug": "edouard-philippe",
        "chambre": "deputes",
        "identite": {"nom_complet": "Édouard Philippe"},
        "dossiers_legislatifs": [DOSSIER_REEL],
    }
    pivot = normalize_profil(brut)

    assert pivot["textes_portes"][0]["dossier_id"] == "DLR5L15N37607"
    assert validate_profil(pivot) == []


def test_le_nom_du_champ_est_celui_des_fiches_de_gouvernement():
    """`schema_gouvernement` publie `textes[].dossier_id` pour les mêmes
    dossiers : si l'un des deux noms dérive, le croisement retombe sur le
    libellé, ce que l'issue #639 mesure comme impraticable (13 libellés communs
    aux trois matières, tous budgétaires)."""
    from schema_gouvernement import REQUIRED_TEXTE_KEYS

    assert "dossier_id" in REQUIRED_TEXTE_KEYS
