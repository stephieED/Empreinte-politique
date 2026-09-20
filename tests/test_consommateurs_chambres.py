"""Les consommateurs de `chambre` migrés vers `chambres` (#494).

Sous-issue **E** de l'épic **#486**, après #493 (D) qui a créé la liste dérivée
et l'a fait coexister avec le scalaire « le temps de reprendre les consommateurs
un par un ».

Ce que ces tests verrouillent :

1. **`lire_chambres()` est la porte unique**, et son repli est ce qui rend la
   migration possible *avant* la régénération : aucun des 209 profils publiés ne
   porte encore `chambres` (0/209, mesuré sur `07e9147` le 20/08/2026). Sans
   repli, `population_an` passerait de 207 à 0 — le signal de régression
   s'éteindrait sur le corpus même qu'il surveille.
2. **Les deux filtres de population ne peuvent plus perdre un bicaméral.**
   C'est l'angle mort que `check_quality_gate` consigne déjà en commentaire :
   `jean-luc-melenchon`, 18 721 amendements AN publiés, sorti de la §3c en
   passant à `chambre: "Senat"`. Un scalaire ne peut porter qu'une chambre ;
   `"AN" in chambres` ne peut plus la perdre.
3. **La répartition par chambre cesse d'être une partition**, et le dit
   (§2.7) : un bicaméral est compté dans chacune de ses chambres, donc la somme
   dépasse le nombre de profils.
4. **Le contrôle chambre/sources porte sur chaque chambre**, ce que le scalaire
   ne pouvait pas tenir.

Aucune lecture du corpus vivant (`pivot_data/`, `raw_data/profiles/`) : ces
tests tournent en CI, où le corpus est absent du disque (#473).
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from audit_pivot_dataset import (  # noqa: E402
    compute_coherence_chambre_sources,
    compute_repartition_chambre,
)
from check_quality_gate import (  # noqa: E402
    _report_amendements_coverage,
    _report_low_syceron_coverage,
)
from schema_pivot import libelle_chambres, lire_chambres  # noqa: E402


# ---------------------------------------------------------------------------
# lire_chambres — la porte unique
# ---------------------------------------------------------------------------

def test_la_liste_fait_foi_quand_elle_est_presente():
    profil = {"chambres": ["AN", "Senat"], "chambre": "AN"}
    assert lire_chambres(profil) == ["AN", "Senat"]


def test_le_scalaire_sert_de_repli_tant_que_la_liste_est_absente():
    """Le cas de tout le corpus publié aujourd'hui : 209 profils sur 209."""
    assert lire_chambres({"chambre": "Senat"}) == ["Senat"]


def test_une_liste_vide_ne_ressuscite_pas_le_scalaire():
    """`chambres` présente fait foi, y compris vide.

    La fabrique garantit `chambre == chambres[0]` : une liste vide veut dire un
    scalaire nul, et retomber dessus ne pourrait que republier une valeur que
    `validate_profil` refuse déjà comme divergente.
    """
    assert lire_chambres({"chambres": [], "chambre": "AN"}) == []


def test_la_chambre_de_collecte_reste_toleree_en_repli():
    """`check_quality_gate` testait `chambre in ("AN", "deputes")` : la
    tolérance historique pour la valeur de collecte ne doit pas se perdre en
    migrant, sinon un profil ancien sortirait de la population sans bruit."""
    assert lire_chambres({"chambre": "deputes"}) == ["AN"]
    assert lire_chambres({"chambre": "senateurs"}) == ["Senat"]


def test_l_ordre_canonique_est_impose_et_les_doublons_ecartes():
    profil = {"chambres": ["PE", "AN", "AN", "Senat"]}
    assert lire_chambres(profil) == ["AN", "Senat", "PE"]


def test_les_valeurs_inconnues_sont_ecartees_des_deux_cotes():
    assert lire_chambres({"chambres": ["AN", "Bundestag"]}) == ["AN"]
    assert lire_chambres({"chambre": "Bundestag"}) == []


@pytest.mark.parametrize("valeur", [None, "AN", 42, ["AN"], {"chambre": None}])
def test_une_donnee_malformee_donne_chambre_non_determinee_jamais_une_exception(valeur):
    """Cette fonction tourne dans les rapports **avant** toute validation : une
    donnée mal formée doit produire « on ne sait pas », pas tuer le rapport."""
    assert lire_chambres(valeur) == []


def test_le_libelle_dit_non_determine_plutot_que_de_choisir():
    assert libelle_chambres(["AN", "PE"]) == "AN+PE"
    assert libelle_chambres([]) == "?"
    assert libelle_chambres([], vide="—") == "—"


# ---------------------------------------------------------------------------
# check_quality_gate — les deux filtres de population
# ---------------------------------------------------------------------------

def _ecrire_pivot(repertoire: Path, slug: str, **champs) -> None:
    profil = {
        "id": slug,
        "nom": slug.replace("-", " ").title(),
        "identite": {"nom_complet": slug},
        "mandats": [],
        "interventions": [],
        "votes": [],
        "textes_portes": [],
        "amendements": [],
        "tags_thematiques": [],
        "sources": [],
        "meta": {"warnings": []},
    }
    profil.update(champs)
    (repertoire / f"{slug}.pivot.json").write_text(json.dumps(profil), encoding="utf-8")


def test_population_an_garde_un_bicameral_que_le_scalaire_perdait(tmp_path):
    """L'angle mort de #447, refermé par construction.

    Le profil publie 2 amendements AN et a siégé dans les deux chambres, mais son
    scalaire vaut `"Senat"` — exactement la configuration de
    `jean-luc-melenchon`, 18 721 amendements AN publiés, que le commentaire de
    `check_quality_gate` consigne comme sorti de la §3c. `chambre in ("AN",
    "deputes")` le rejetait ; `"AN" in chambres` le garde.

    Le compteur `Profils AN avec identité` **est** l'assiette de la §3c : il
    passe de 0 à 1 pour ce profil. Il s'appelait « Candidats AN avec
    identité » jusqu'à #630 : il compte 477 profils sur le corpus publié,
    dont 468 membres de roster — le libellé enseignait la confusion, et la
    cellule porte désormais sa ventilation.
    """
    _ecrire_pivot(
        tmp_path, "bicameral",
        chambres=["AN", "Senat"], chambre="Senat",
        amendements=[{"amendement_id": "an:1"}, {"amendement_id": "an:2"}],
    )

    soft, regression, console, md = _report_amendements_coverage(tmp_path)

    assert "| ✅ Profils AN avec identité | 1 (1 candidats · 0 membres de roster) |" in md
    # Corollaire : il n'est plus dans les profils qui publient des amendements
    # sans appartenir à la population dont on en attend.
    assert "hors population AN" not in md


def test_population_an_perd_le_bicameral_quand_la_liste_ne_dit_pas_AN(tmp_path):
    """Le contre-témoin : mêmes données, `chambres` sans `AN`.

    Sans lui, le test précédent pourrait passer pour une raison sans rapport —
    c'est la lecture de la liste qui décide, et rien d'autre.
    """
    _ecrire_pivot(
        tmp_path, "senateur",
        chambres=["Senat"], chambre="Senat",
        amendements=[{"amendement_id": "an:1"}, {"amendement_id": "an:2"}],
    )

    soft, regression, console, md = _report_amendements_coverage(tmp_path)

    assert "| ✅ Profils AN avec identité | 0 (0 candidats · 0 membres de roster) |" in md
    assert "hors population AN" in md


def test_population_an_inchangee_sur_le_corpus_publie(tmp_path):
    """Des profils tels qu'ils sont publiés aujourd'hui — scalaire seul, pas de
    `chambres` — sont comptés exactement comme avant la migration."""
    _ecrire_pivot(tmp_path, "depute", chambre="AN", amendements=[{"amendement_id": "an:1"}])
    _ecrire_pivot(tmp_path, "depute-collecte", chambre="deputes", amendements=[])
    _ecrire_pivot(tmp_path, "senateur", chambre="Senat", amendements=[])

    soft, regression, console, md = _report_amendements_coverage(tmp_path)

    assert "Profils AN avec identité | 2 (2 candidats · 0 membres de roster) |" in md


def test_syceron_garde_un_bicameral_que_le_scalaire_perdait(tmp_path):
    """Second filtre de population, même défaut, même correction."""
    _ecrire_pivot(
        tmp_path, "bicameral",
        chambres=["AN", "Senat"], chambre="Senat",
        mandats=[{
            "label": "Mandat parlementaire", "categorie": "mandat_electif",
            "legislature": "17", "debut": "2022-06-01",
        }],
    )

    soft, console, md = _report_low_syceron_coverage(tmp_path, threshold=1)

    assert len(soft) == 1
    assert "bicameral" in soft[0]


def test_syceron_ignore_toujours_un_profil_sans_aucune_chambre_an(tmp_path):
    """La migration élargit la population, elle ne la rend pas universelle."""
    _ecrire_pivot(
        tmp_path, "senateur",
        chambres=["Senat"], chambre="Senat",
        mandats=[{
            "label": "Mandat parlementaire", "categorie": "mandat_electif",
            "legislature": "17", "debut": "2022-06-01",
        }],
    )

    soft, console, md = _report_low_syceron_coverage(tmp_path, threshold=1)

    assert soft == []


def test_les_18_senateurs_sans_mandat_electif_restent_comptes_a_l_identique(tmp_path):
    """Le cas mesuré par #493 : 18 sénateurs publiés `chambre: "AN"`, sans aucun
    `mandat_electif`, et dont la source est `nosdeputes.fr`.

    `chambres` ne les corrige pas — le repli reconduit `"AN"`, faute de mandat
    qui dise autre chose — mais **ne les dégrade pas non plus** : ils restent
    dans la population AN, exactement comme avant. Leur correction relève de la
    collecte, pas du schéma (`ROADMAP.md`), et #493 leur a posé le warning qui
    le dit.
    """
    _ecrire_pivot(
        tmp_path, "senateur-publie-an",
        chambres=["AN"], chambre="AN", mandats=[],
        amendements=[{"amendement_id": "an:1"}],
    )

    soft, regression, console, md = _report_amendements_coverage(tmp_path)

    assert "| ✅ Profils AN avec identité | 1 (1 candidats · 0 membres de roster) |" in md


# ---------------------------------------------------------------------------
# audit_pivot_dataset — répartition et cohérence
# ---------------------------------------------------------------------------

def test_la_repartition_compte_un_bicameral_dans_chacune_de_ses_chambres():
    profils = [
        {"chambres": ["AN", "PE"], "chambre": "AN"},
        {"chambres": ["AN"], "chambre": "AN"},
    ]

    resultat = compute_repartition_chambre(profils)

    assert resultat["par_chambre"]["AN"] == 2
    assert resultat["par_chambre"]["PE"] == 1


def test_la_repartition_dit_que_sa_somme_n_est_pas_le_nombre_de_profils():
    """§2.7 : un dénominateur se publie avec ce qu'il dénombre. Sans
    `total_attributions`, 3 lignes pour 2 profils passeraient pour une erreur."""
    profils = [{"chambres": ["AN", "PE"]}, {"chambres": ["AN"]}]

    resultat = compute_repartition_chambre(profils)

    assert resultat["total_profils"] == 2
    assert resultat["total_attributions"] == 3
    assert sum(resultat["par_chambre"].values()) == 3


def test_la_repartition_est_inchangee_sur_le_corpus_publie():
    """Scalaire seul — le cas des 209 profils : une attribution par profil, et
    la somme retombe sur le nombre de profils."""
    profils = [{"chambre": "AN"}, {"chambre": "AN"}, {"chambre": "Senat"}, {"chambre": None}]

    resultat = compute_repartition_chambre(profils)

    assert resultat["par_chambre"] == {"AN": 2, "Senat": 1, "PE": 0, "mairie": 0, "null": 1}
    assert resultat["total_attributions"] == resultat["total_profils"] == 4


# ---------------------------------------------------------------------------
# Le constat sur `_prefer_non_empty` — #484 n'est pas corrigée ici
# ---------------------------------------------------------------------------

def test_la_chambre_collante_survit_a_la_migration_mais_ne_peut_plus_evincer():
    """**Constat, pas correction.** #494 ne referme pas la moitié « collance »
    de #484 — elle la contient et la déclare.

    `merge_pivot_profile` fait `_prefer_non_empty(new.chambre, old.chambre)`
    (l. 447), puis `appliquer_chambres` (l. ~468) recalcule les deux champs avec
    ce scalaire pour **repli**. Or `deriver_chambres` ajoute *toujours* le repli
    (#493, « retirer une chambre observée est une suppression »). Une chambre
    fausse qui a survécu à une collecte muette survit donc dans `chambres`.

    Deux choses changent tout de même, et ce sont les deux qui comptent :

    1. elle ne peut plus **évincer** une chambre que les mandats attestent — le
       scalaire remplaçait, la liste s'ajoute ;
    2. elle est **déclarée** non corroborée, donc distinguable d'une chambre
       étayée.

    Corriger la collance elle-même appartient à #484, avec l'autre moitié (le
    squelette *truthy* qui écrase une `identite` réelle).
    """
    ancien = {"chambres": ["Senat"], "chambre": "Senat", "mandats": []}
    neuf = {"chambre": None, "mandats": [
        {"label": "Mandat parlementaire", "categorie": "mandat_electif",
         "chambre": "AN", "debut": "2017-06-21"},
    ]}

    from merge_profile import merge_pivot_profile

    fusionne = merge_pivot_profile(ancien, neuf)

    # La chambre collante est toujours là — la migration ne l'a pas fermée…
    assert "Senat" in fusionne["chambres"]
    # …mais elle n'évince plus la chambre que le mandat atteste.
    assert fusionne["chambres"] == ["AN", "Senat"]


def test_la_coherence_signale_la_chambre_qui_n_a_aucune_source_attendue():
    profils = [{
        "id": "bicameral",
        "chambres": ["AN", "Senat"],
        "sources": [{"type": "nosdeputes"}],
    }]

    incoherents = compute_coherence_chambre_sources(profils)["profils_incoherents"]

    assert [p["chambres_sans_source"] for p in incoherents] == [["Senat"]]
