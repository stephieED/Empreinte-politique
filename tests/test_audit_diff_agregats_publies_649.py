"""Les agrégats publiés entrent dans le contrôle de perte (#649).

`audit_diff_profils.py` raisonnait explicitement sur ce qu'il surveillait des
fiches de groupe — `effectif.actuel` écarté parce qu'il baisse légitimement,
`meta.couverture_roster.roster_total` inclus parce que sa disparition rendrait
un ratio publié incalculable — **et pas un mot sur les agrégats**, c'est-à-dire
sur les chiffres que les pages affichent en gros. Ni `amendements_agreges` côté
groupe, ni `comptages.par_statut` côté gouvernement.

Ces tests rejouent deux runs réels, en fixtures figées réduites verbatim
(`tests/fixtures/audit_diff_agregats_649/`, provenance dans `meta.fixture`) :

  - `0fb4369f` → `a125e9e0`, le run de #460 / #470 : `AN:LFI-16` y perd ses
    11 561 amendements et son `taux_adoption` passe de `0.0476` à `null`,
    pendant que `membres`, `cohesion_votes` et `mandats_agreges` ne bougent
    pas d'une entrée. Rien ne bloquait sur cette fiche ;
  - `be960bce` → `3c8e1f0c`, le run `33351244845` du 31/08/2026 : la
    correction de #643 divise par 5 à 32 le compteur principal de cinq fiches.
    Chute **juste** — elle ne doit rien bloquer, et elle doit être visible.

Aucun accès au corpus vivant (#473) : tout se lit dans les fixtures.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from audit_diff_profils import (  # noqa: E402
    COLLECTION_GOUVERNEMENTS,
    COLLECTION_GROUPES,
    comparer,
    generate_markdown_report,
    lire_collection_disque,
    relever,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "audit_diff_agregats_649"


def _paire(avant: str, apres: str, collection=COLLECTION_GROUPES):
    return (lire_collection_disque(FIXTURES / avant, collection),
            lire_collection_disque(FIXTURES / apres, collection))


def _rapport_perte_reelle():
    avant, apres = _paire("perte_reelle_avant", "perte_reelle_apres")
    return comparer(avant, apres, COLLECTION_GROUPES)


def _rapport_chute_juste():
    avant, apres = _paire("chute_juste_avant", "chute_juste_apres")
    return comparer(avant, apres, COLLECTION_GROUPES)


def test_les_fixtures_declarent_leur_provenance():
    """Une fixture sans provenance est une donnée inventée dans six mois."""
    fichiers = sorted(FIXTURES.rglob("*.json"))
    assert len(fichiers) == 7
    for chemin in fichiers:
        fixture = json.loads(chemin.read_text(encoding="utf-8"))["meta"]["fixture"]
        assert fixture["source"].startswith("pivot_data/"), chemin
        assert len(fixture["ref"]) == 40, chemin
        assert "VERBATIM" in fixture["reduction"], chemin


# ---------------------------------------------------------------------------
# La perte réelle : AN:LFI-16, run `a125e9e`
# ---------------------------------------------------------------------------

def test_le_taux_d_adoption_perdu_par_lfi16_bloque():
    """La mesure qui justifie l'inclusion. `amendements_agreges.taux_adoption`
    passe de `0.0476` à `null` : une régression renseigné → `null`, la
    catégorie sur laquelle ce contrôle bloque depuis #470."""
    rapport = _rapport_perte_reelle()

    pertes = {(p["fichier"], p["champ"]): (p["avant"], p["apres"])
              for p in rapport["pertes_scalaires"]}
    assert pertes[("groupe-AN-LFI-16.json",
                   "amendements_agreges.taux_adoption")] == (0.0476, None)
    assert rapport["bloquant"]


def test_aucune_liste_ne_bougeait_sur_cette_fiche():
    """La preuve du trou : sur `AN:LFI-16`, `membres` (3), `cohesion_votes`
    (1 996) et `mandats_agreges` (50) sont identiques des deux côtés. Les
    listes stables — le seul verrou qui existait sur une fiche de groupe — ne
    voyaient rien, quelle que soit l'ampleur de la perte d'agrégat."""
    rapport = _rapport_perte_reelle()

    assert not rapport["pertes_sur_champs_stables"]
    assert not [p for p in rapport["pertes"] if p["champ"] != "amendements"]


def test_le_compteur_tombe_a_zero_est_signale_sans_bloquer():
    """`nb_amendements` 11 561 → 0 est un **changement de valeur**, relevé et
    non bloquant. Un compteur à zéro n'est pas une absence de compteur : c'est
    la régression vers `null` du taux qui bloque, pas le zéro."""
    rapport = _rapport_perte_reelle()

    evolutions = {(e["fichier"], e["champ"]): (e["avant"], e["apres"])
                  for e in rapport["evolutions_scalaires"]}
    assert evolutions[("groupe-AN-LFI-16.json",
                       "amendements_agreges.nb_amendements")] == (11561, 0)
    assert evolutions[("groupe-AN-LFI-16.json",
                       "amendements_agreges.par_type_deposant.depute."
                       "nb_amendements")] == (11358, 0)
    assert not any(p["champ"] == "amendements_agreges.nb_amendements"
                   for p in rapport["pertes_scalaires"]), (
        "0 est une valeur renseignée, pas une disparition")


def test_zero_reste_une_valeur_renseignee_dans_le_releve():
    """Le relevé lui-même, pas seulement la comparaison : `nb_amendements: 0`
    doit ressortir `0`, jamais `None` — sans quoi le prochain run repartirait
    de zéro sans que la reprise soit visible (AGENTS.md §2 règle 5)."""
    apres = lire_collection_disque(FIXTURES / "perte_reelle_apres",
                                   COLLECTION_GROUPES)
    scalaires = apres["groupe-AN-LFI-16.json"]["scalaires"]

    assert scalaires["amendements_agreges.nb_amendements"] == 0
    assert scalaires["amendements_agreges.taux_adoption"] is None
    assert scalaires["amendements_agreges"] == "<renseigné>"


# ---------------------------------------------------------------------------
# La chute juste : run `33351244845`, `be960bce` → `3c8e1f0c`
# ---------------------------------------------------------------------------

def test_la_chute_de_x20_de_643_ne_bloque_pas():
    """Le garde-fou du garde-fou. `AN:RN` ÷ 31,7 et `AN:LFI` ÷ 19,8 sont la
    correction de #643 — un amendement cosigné n'est pas N amendements. Si
    cette chute bloquait, chaque run demanderait `allow_declared_losses`, et
    une tolérance cochée par habitude ne protège plus de rien."""
    rapport = _rapport_chute_juste()

    assert not rapport["bloquant"], rapport["pertes_scalaires"]


def test_la_chute_de_x20_cesse_d_etre_muette():
    """Ce que le run `33351244845` a établi : le commit `3c8e1f0c` est passé
    sans une ligne. Il en porte désormais trois par fiche."""
    rapport = _rapport_chute_juste()

    evolutions = {(e["fichier"], e["champ"]): (e["avant"], e["apres"])
                  for e in rapport["evolutions_scalaires"]}
    assert evolutions[("groupe-AN-RN-16.json",
                       "amendements_agreges.nb_amendements")] == (1184090, 37812)
    assert evolutions[("groupe-AN-RN-16.json",
                       "amendements_agreges.par_type_deposant.depute."
                       "nb_amendements")] == (1175535, 37093)
    assert evolutions[("groupe-AN-LFI-16.json",
                       "amendements_agreges.par_type_deposant.depute."
                       "nb_amendements")] == (2600765, 131202)


def test_la_ventilation_par_type_de_deposant_est_une_liste_stable():
    """`par_type_deposant` a quatre catégories des deux côtés du run. Son
    `len()` est surveillé comme une liste stable : `validate_profil_groupe` ne
    vérifie que son type, jamais ses clés — une ventilation qui perdrait une
    catégorie ne serait vue par rien d'autre."""
    avant, apres = _paire("chute_juste_avant", "chute_juste_apres")
    champ = "amendements_agreges.par_type_deposant"

    assert champ in COLLECTION_GROUPES.listes_stables
    assert avant["groupe-AN-RN-16.json"]["listes"][champ] == 4
    assert apres["groupe-AN-RN-16.json"]["listes"][champ] == 4


def test_une_ventilation_qui_perd_une_categorie_bloque():
    """Le relevé, sur un document dont la ventilation est amputée : trois
    catégories au lieu de quatre est une perte bloquante."""
    doc = json.loads(
        (FIXTURES / "chute_juste_apres" / "groupe-AN-RN-16.json")
        .read_text(encoding="utf-8"))
    ampute = json.loads(json.dumps(doc))
    ampute["amendements_agreges"]["par_type_deposant"].pop("inconnu")

    rapport = comparer({"g.json": relever(doc, COLLECTION_GROUPES)},
                       {"g.json": relever(ampute, COLLECTION_GROUPES)},
                       COLLECTION_GROUPES)

    assert [(p["champ"], p["avant"], p["apres"])
            for p in rapport["pertes_sur_champs_stables"]] == [
        ("amendements_agreges.par_type_deposant", 4, 3)]
    assert rapport["bloquant"]


# ---------------------------------------------------------------------------
# Gouvernements — `comptages.par_statut`
# ---------------------------------------------------------------------------

def test_les_comptages_de_borne_sont_releves():
    """`BORNE` porte 6 `adopte_49_3`. C'est le fait procédural que la ligne
    éditoriale publie (AGENTS.md §2 règle 4, §6), et le plus lisible d'une
    fiche de gouvernement."""
    releve = lire_collection_disque(FIXTURES / "gouvernements_borne",
                                    COLLECTION_GOUVERNEMENTS)
    scalaires = releve["gouvernement-BORNE.json"]["scalaires"]

    assert scalaires["comptages.par_statut.adopte_49_3"] == 6
    assert scalaires["comptages.par_statut.rejete_49_3"] == 0
    assert scalaires["comptages"] == "<renseigné>"
    assert scalaires["comptages.par_statut"] == "<renseigné>"


def test_un_bloc_comptages_nul_bloque():
    """`comptages` figure dans `REQUIRED_TOP_LEVEL_KEYS`, mais
    `validate_profil_gouvernement` accepte `comptages: null` sans un mot : la
    clé est là, les neuf compteurs publiés ont disparu. C'est la porte que ce
    contrôle ferme."""
    doc = json.loads(
        (FIXTURES / "gouvernements_borne" / "gouvernement-BORNE.json")
        .read_text(encoding="utf-8"))
    vide = json.loads(json.dumps(doc))
    vide["comptages"] = None

    rapport = comparer({"g.json": relever(doc, COLLECTION_GOUVERNEMENTS)},
                       {"g.json": relever(vide, COLLECTION_GOUVERNEMENTS)},
                       COLLECTION_GOUVERNEMENTS)

    perdus = {(p["champ"], p["avant"]) for p in rapport["pertes_scalaires"]}
    assert perdus == {
        ("comptages", "<renseigné>"),
        ("comptages.par_statut", "<renseigné>"),
        ("comptages.par_statut.adopte_49_3", 6),
        ("comptages.par_statut.rejete_49_3", 0),
    }, ("`rejete_49_3` valait 0, et 0 → null EST une régression : un compteur "
        "à zéro est une mesure, un compteur absent n'en est pas une")
    assert rapport["bloquant"]


def test_une_requalification_entre_statuts_ne_bloque_pas():
    """Le run `720110d2` a déplacé 27 textes de `BORNE` vers `adopte_cmp` et
    19 vers `promulgue` en une passe. Une baisse par statut est la contrepartie
    normale d'une requalification ; la perte réelle serait que `textes`
    rétrécisse, et `textes` est déjà une liste stable bloquante."""
    doc = json.loads(
        (FIXTURES / "gouvernements_borne" / "gouvernement-BORNE.json")
        .read_text(encoding="utf-8"))
    requalifie = json.loads(json.dumps(doc))
    statuts = requalifie["comptages"]["par_statut"]
    statuts["adopte_49_3"] -= 4
    statuts["promulgue"] += 4

    rapport = comparer({"g.json": relever(doc, COLLECTION_GOUVERNEMENTS)},
                       {"g.json": relever(requalifie, COLLECTION_GOUVERNEMENTS)},
                       COLLECTION_GOUVERNEMENTS)

    assert not rapport["bloquant"]
    assert [(e["champ"], e["avant"], e["apres"])
            for e in rapport["evolutions_scalaires"]] == [
        ("comptages.par_statut.adopte_49_3", 6, 2)]


# ---------------------------------------------------------------------------
# Ce qui est écarté, et pourquoi
# ---------------------------------------------------------------------------

def test_les_compteurs_de_la_meme_fabrique_restent_ecartes():
    """`nb_adoptes`, `nb_rejetes`, `nb_irrecevables`, `nb_retires_ou_tombes`
    sortent de la même fabrique que `nb_amendements`
    (`schema_groupe.make_empty_amendements_stats`) : ils ne peuvent pas
    disparaître seuls. Les surveiller n'ajouterait aucun événement, seulement
    des lignes de rapport."""
    surveilles = set(COLLECTION_GROUPES.scalaires)

    for champ in ("nb_adoptes", "nb_rejetes", "nb_irrecevables",
                  "nb_retires_ou_tombes", "nb_sort_non_renseigne",
                  "nb_sans_identifiant", "signatures"):
        assert f"amendements_agreges.{champ}" not in surveilles


def test_l_effectif_reste_ecarte():
    """L'exclusion motivée qui préexiste à #649 : `effectif.actuel` baisse
    légitimement quand un élu quitte le groupe."""
    surveilles = set(COLLECTION_GROUPES.scalaires)

    assert not any(c.startswith("effectif") for c in surveilles)


def test_les_sept_autres_statuts_restent_ecartes():
    """`validate_profil_gouvernement` compare les clés de `par_statut` à
    `KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL` et fait échouer la porte de qualité
    sur une clé manquante : un second verrou sur le même événement n'ajoute
    rien. Seuls les deux compteurs de 49.3 sont nommés, pour leur valeur
    éditoriale."""
    statuts = {c.rsplit(".", 1)[1] for c in COLLECTION_GOUVERNEMENTS.scalaires
               if c.startswith("comptages.par_statut.")}

    assert statuts == {"adopte_49_3", "rejete_49_3"}


def test_le_rapport_enonce_le_hors_perimetre_des_ordres_de_grandeur():
    """L'arbitrage de la question 3, écrit là où on le lit : pas de quatrième
    famille bloquante sur l'ordre de grandeur d'un compteur."""
    markdown = generate_markdown_report(_rapport_chute_juste(), "be960bce")

    assert "ordre de grandeur" in markdown
    assert "membres_eligibles" in markdown
