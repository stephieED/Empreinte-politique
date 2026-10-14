"""La section « Les budgets que ce gouvernement a fait voter » (#1053).

Arbitrée en maquette le 13/10/2026 (version 68) : deux colonnes « reçoit /
dépense » à la même échelle et la cascade des soldes pour l'État, les mêmes
deux colonnes pour la sécurité sociale.

CE QUE CES TESTS NE COUVRENT PAS : ils ne dessinent rien. Les exercices sont
ÉCRITS ICI, montants arrondis, dans la forme de `pivot_data/budgets_gouvernements.json`
que décrit la branche `backend/budget-fiche-gouvernement-1053` : le fichier
n'est pas encore sur `main`, et le seul exemplaire avec ses missions a été
produit hors dépôt. Une entrée copiée du corpus les remplacera quand il y sera.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale"
MODULE = UI / "src" / "utils" / "budgetsGouvernement.js"
FICHE = UI / "src" / "components" / "GovernmentProfile.jsx"
SYNC = UI / "scripts" / "sync-data.mjs"

MD = 1e9


def _etat(an, missions=True, complet=True, solde=-142 * MD):
    """Un budget de l'État : 300 Md€ de recettes nettes, 380 de dépenses.

    Le solde est celui que la source compose, et que les fichiers réels
    vérifient : toutes les lignes de recettes, fonds de concours compris, moins
    les dépenses nettes et ce qui est reversé, plus les comptes à part —
    308 − 380 − 67 − 3."""
    bloc = {
        "dernier_mois": f"{an}-12" if complet else f"{an}-08",
        "exercice_complet": complet,
        "recettes": [
            {"ligne": "Impôt sur le revenu", "montant": 90 * MD},
            {"ligne": "Taxe sur la valeur ajoutée", "montant": 100 * MD},
            {"ligne": "Autres recettes fiscales", "montant": 90 * MD},
            {"ligne": "Total recettes non fiscales", "montant": 20 * MD},
            {"ligne": "Fonds de concours et attribution de produits", "montant": 8 * MD},
        ],
        "recettes_nettes": 300 * MD,
        "depenses_nettes": 380 * MD,
        "reverse": [
            {"ligne": "PSR au profit des collectivités territoriales", "montant": 45 * MD},
            {"ligne": "PSR au profit de l'Union européenne", "montant": 22 * MD},
        ],
        "comptes_a_part": -3 * MD,
        "solde": solde,
    }
    if missions:
        # Douze missions : 375 Md€, les 5 qui manquent aux dépenses nettes
        # sont les dégrèvements d'impôts locaux.
        bloc["missions"] = [{"mission": f"Mission {i:02d}", "montant": (40 - i) * MD} for i in range(1, 13)]
        bloc["missions"].append({"mission": "Crédits non répartis", "montant": 0.0})
        reste = 375 * MD - sum(m["montant"] for m in bloc["missions"])
        bloc["missions"][0]["montant"] += reste
        bloc["degrevements_d_impots_locaux"] = 5 * MD
    else:
        bloc["missions"] = None
        bloc["missions_non_resolu"] = {"raison": "non publiées"}
    return bloc


def _secu(separees=True):
    """En millions d'euros, comme la source."""
    cotisations = ([{"origine": "Cotisations sociales d'employeurs", "montant": 280000.0},
                    {"origine": "Cotisations sociales de salariés", "montant": 90000.0}]
                   if separees else [{"origine": "Cotisations sociales d'employeurs", "montant": 370000.0}])
    return {
        "statut": "DEF" if separees else "PROV",
        "ressources": cotisations + [
            {"origine": "Impôts et taxes affectés", "montant": 280000.0},
            {"origine": "Produits financiers (depuis 1981)", "montant": 5000.0},
            {"origine": "Recettes du compte de capital (depuis 2006)", "montant": -4000.0},
        ],
        "prestations": [
            {"regime": "Caisse nationale d’assurance vieillesse", "montant": 150000.0},
            {"regime": "UNEDIC et autres régimes", "montant": 35000.0},
        ] + [{"regime": f"Régime {i:02d}", "montant": 40000.0 - 1000 * i} for i in range(1, 12)],
        "autres_emplois": 45000.0,
    }


def _exercice(an, **etat):
    secu = etat.pop("secu", _secu())
    sortie = {"exercice": an, "loi_de_finances_promulguee_le": f"{int(an) - 1}-12-30",
              "budget_de_l_etat": _etat(an, **etat)}
    if secu is None:
        sortie["securite_sociale"] = None
        sortie["securite_sociale_non_resolu"] = {"raison": "non publiée"}
    else:
        sortie["securite_sociale"] = secu
    return sortie


def _appel(fonction, exercices):
    if shutil.which("node") is None:
        pytest.skip("node absent")
    script = "const m = await import(%r);\nprocess.stdout.write(JSON.stringify(m.%s(%s)));" % (
        MODULE.as_uri(), fonction, json.dumps(exercices))
    res = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout)


def _somme(lignes, cle="montant"):
    return sum(l[cle] for l in lignes)


# ── Le budget de l'État ──────────────────────────────────────────────────────


def test_les_deux_colonnes_de_l_etat_ont_la_meme_hauteur_et_l_emprunt_les_egalise() -> None:
    c = _appel("colonnesDuBudget", [_exercice("2023"), _exercice("2024")])
    assert c["annees"] == ["2023", "2024"]
    emprunt = [l for l in c["recoit"] if l["nom"] == "Emprunt"]
    assert len(emprunt) == 1 and emprunt[0]["montant"] == pytest.approx(284 * MD)
    assert _somme(c["recoit"]) == pytest.approx(_somme(c["depense"]))
    assert c["recu"] == pytest.approx(_somme(c["recoit"]) - 284 * MD)


def test_dix_missions_puis_les_autres_et_ce_qui_n_est_pas_reparti() -> None:
    c = _appel("colonnesDuBudget", [_exercice("2024")])
    noms = [l["nom"] for l in c["depense"]]
    assert sum(n.startswith("Mission ") for n in noms) == 10
    assert "Autres missions (2)" in noms, "deux missions au-delà des dix, la mission vide écartée"
    assert {"Reversé aux collectivités", "Reversé à l’Union européenne"} <= set(noms)
    # Dégrèvements locaux (5) + comptes à part négatifs (3).
    non_reparti = next(l for l in c["depense"] if l["nom"] == "Non réparti par mission, comptes à part")
    assert non_reparti["montant"] == pytest.approx(8 * MD)


def test_pour_100_euros_chaque_colonne_fait_son_total() -> None:
    c = _appel("colonnesDuBudget", [_exercice("2024")])
    assert _somme(c["depense"], "euros") == 100
    assert _somme(c["recoit"], "euros") == 100
    emprunt = next(l for l in c["recoit"] if l["nom"] == "Emprunt")
    assert c["recuPour100"] == 100 - emprunt["euros"], "le total écrit est la somme des lignes affichées"


def test_une_annee_sans_missions_est_nommee_et_n_entre_pas_dans_les_colonnes() -> None:
    c = _appel("colonnesDuBudget", [_exercice("2022", missions=False), _exercice("2023")])
    assert c["annees"] == ["2023"]
    assert c["sansDetail"] == ["2022"]
    assert _somme(c["depense"]) == pytest.approx(380 * MD + 67 * MD + 3 * MD)


def test_la_cascade_mene_au_solde_de_tous_les_budgets_et_dit_l_annee_en_cours() -> None:
    c = _appel("cascadeDesBudgets", [_exercice("2025"), _exercice("2026", missions=False, complet=False, solde=-100 * MD)])
    assert c["solde"] == pytest.approx(-242 * MD)
    assert [a["periode"] for a in c["annees"]] == [None, "janv.–août"]
    premier = c["annees"][0]
    assert premier["niveau"] == pytest.approx(premier["depart"] + premier["recettes"] - premier["depenses"] + premier["reste"])
    assert c["annees"][1]["depart"] == pytest.approx(-142 * MD)


def test_le_survol_d_une_mission_detaille_ses_programmes_sur_toutes_les_annees() -> None:
    """Champ `programmes` livré par Backend le 14/10/2026 ; un nom absent garde le numéro."""
    exercices = [_exercice("2023"), _exercice("2024")]
    for e in exercices:
        m = e["budget_de_l_etat"]["missions"][1]
        m["programmes"] = [{"programme": "117", "libelle": "Charge de la dette", "montant": m["montant"] - 2 * MD},
                           {"programme": "355", "libelle": None, "montant": 2 * MD}]
    c = _appel("colonnesDuBudget", exercices)
    ligne = next(l for l in c["depense"] if l["nom"] == "Mission 02")
    assert [(d["nom"], round(d["montant"] / MD)) for d in ligne["detail"]] == [
        ("Charge de la dette", round(ligne["montant"] / MD) - 4), ("Programme 355", 4)]


# ── La sécurité sociale ──────────────────────────────────────────────────────


def test_la_securite_sociale_est_rendue_en_euros_et_nomme_son_complement() -> None:
    c = _appel("colonnesDeLaSecuriteSociale", [_exercice("2023")])
    vieillesse = next(l for l in c["depense"] if l["nom"] == "Assurance vieillesse (Cnav)")
    assert vieillesse["montant"] == pytest.approx(150 * MD)
    assert any(l["nom"] == "Chômage (Unédic)" for l in c["depense"])
    assert any(l["nom"].startswith("Autres régimes (") for l in c["depense"])
    assert _somme(c["recoit"]) == pytest.approx(_somme(c["depense"]))


def test_les_cotisations_non_separees_le_disent_avec_leur_annee() -> None:
    c = _appel("colonnesDeLaSecuriteSociale", [_exercice("2023"), _exercice("2024", secu=_secu(separees=False))])
    noms = [l["nom"] for l in c["recoit"]]
    assert "Cotisations non séparées (2024)" in noms
    employeurs = next(l for l in c["recoit"] if l["nom"] == "Cotisations des employeurs")
    assert employeurs["montant"] == pytest.approx(280 * MD), "la ligne de 2024 n'est pas comptée aux employeurs"


def test_une_annee_sans_comptes_sociaux_est_nommee() -> None:
    c = _appel("colonnesDeLaSecuriteSociale", [_exercice("2025", secu=None)])
    assert c["annees"] == [] and c["sansDetail"] == ["2025"]
    assert c["recoit"] == [] and c["depense"] == []


# ── La fiche ─────────────────────────────────────────────────────────────────


def test_la_section_ne_s_affiche_que_pour_un_gouvernement_qui_a_fait_voter_un_budget() -> None:
    fiche = FICHE.read_text(encoding="utf-8")
    assert "{budgets && <LesBudgetsQuIlAFaitVoter exercices={budgets} />}" in fiche
    assert "numero={budgets ? '07' : '06'}" in fiche, "les limites restent la dernière section, numérotée à la suite"
    sync = SYNC.read_text(encoding="utf-8")
    assert "if ((entree.exercices || []).length) budgetsParGouvernement.set(" in sync
    assert "budgets: budgetsParGouvernement.has(gouvernement.gouvernement_id)" in sync


def test_aucun_montant_vote_n_est_lu() -> None:
    """Arbitré le 13/10/2026 : seuls les montants encaissés et dépensés."""
    module = MODULE.read_text(encoding="utf-8")
    assert "vote" not in module.replace("voter", "").replace("votés", "")
