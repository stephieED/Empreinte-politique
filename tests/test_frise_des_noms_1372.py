"""Au téléphone, les noms au-dessus des frises de gouvernements (#1372, lot 3 suite).

Arrêté le 28/10/2026 avec la propriétaire, sur maquettes :

- **fiche de législature, forme F** : chaque nom part d'un trait vertical à sa
  date de début ; les gouvernements consécutifs d'un même Premier ministre se
  réunissent (« Lecornu I et II ») ; les noms se rangent sur le plus petit
  nombre de niveaux tels que (a) deux noms d'un même niveau ne se touchent pas,
  (b) le trait d'un nom ne traverse jamais le texte d'un nom placé plus bas,
  (c) le texte d'un nom n'est traversé par aucun trait d'un nom placé plus haut ;
- **fiche de gouvernement, forme C** : le même rangement, sur une fenêtre de six
  gouvernements autour de celui de la fiche ;
- **fiche de groupe, forme C** : les années de la courbe à 13 px, celles qui
  tiennent avec une année de blanc entre deux.

CE QUE CES TESTS COUVRENT : les fonctions pures de `utils/frise.js`, exécutées
par node. Les largeurs des noms sont COPIÉES du rendu à 390 px du 28/10/2026
(Chromium, Manrope) : elles changent avec la police, et un autre téléphone
donnera d'autres largeurs. CE QU'ILS NE COUVRENT PAS : le rendu React, la mesure
à l'écran, la police de repli — cela se vérifie sur captures.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale" / "src"
FRISE = UI / "utils" / "frise.js"
LEGISLATURE = UI / "components" / "LegislatureProfile.jsx"
GOUVERNEMENT = UI / "components" / "GovernmentProfile.jsx"


def _executer(script: str):
    if shutil.which("node") is None:
        pytest.skip("node absent")
    entete = f"const f = await import({json.dumps(FRISE.as_uri())});\n"
    res = subprocess.run(
        ["node", "--input-type=module", "-e", entete + script],
        capture_output=True, text=True, check=False,
    )
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout.strip().splitlines()[-1])


def _ranger(noms: list[dict], largeur: int) -> dict:
    etiquettes = [{"x": n["x"], "largeur": n["largeur"]} for n in noms]
    return _executer(
        f"console.log(JSON.stringify(f.rangerEtiquettes({json.dumps(etiquettes)}, {largeur})));"
    )


def _verifier_contraintes(noms: list[dict], r: dict, ecart=4, garde=4, trait=2):
    """Les trois conditions, recalculées à part de l'algorithme."""
    boites = []
    for n, niveau, droite in zip(noms, r["niveaux"], r["aDroite"]):
        x, w = n["x"], n["largeur"]
        a, b = (x - w, x) if droite else (x, x + w)
        t0, t1 = (x - trait, x) if droite else (x, x + trait)
        boites.append((n["nom"], niveau, a, b, t0, t1))
    for nom, lv, a, b, t0, t1 in boites:
        for autre, lv2, a2, b2, u0, u1 in boites:
            if autre == nom:
                continue
            if lv == lv2:
                assert b + ecart <= a2 or a >= b2 + ecart, f"{nom} et {autre} se touchent"
            if lv > lv2:  # mon trait descend à travers le niveau de l'autre
                assert t1 < a2 - garde or t0 > b2 + garde, f"le trait de {nom} traverse {autre}"
    assert r["nombre"] == max(r["niveaux"]) + 1


# Largeurs mesurées à 390 px le 28/10/2026 (frise de 340 px) : `x` est le trait.
XVII = [
    {"nom": "Attal", "x": 0, "largeur": 92},
    {"nom": "Barnier", "x": 26.8, "largeur": 91},
    {"nom": "Bayrou", "x": 66.5, "largeur": 100},
    {"nom": "Lecornu I et II", "x": 174.6, "largeur": 121},
]
XIV = [
    {"nom": "Ayrault II", "x": 0, "largeur": 121},
    {"nom": "Valls I et II", "x": 121, "largeur": 128},
    {"nom": "Cazeneuve", "x": 303.7, "largeur": 98},
    {"nom": "Philippe I", "x": 333.9, "largeur": 80},
]
XV = [
    {"nom": "Philippe II", "x": 0, "largeur": 90},
    {"nom": "Castex", "x": 207, "largeur": 124},
    {"nom": "Borne", "x": 333.5, "largeur": 90},
]


def test_la_xviie_tient_sur_trois_niveaux():
    """Le résultat montré sur la maquette F : Attal en haut, Barnier, puis
    Bayrou et Lecornu I et II contre la barre."""
    r = _ranger(XVII, 340)
    assert r["nombre"] == 3
    assert r["niveaux"] == [2, 1, 0, 0]
    assert r["aDroite"] == [False] * 4
    _verifier_contraintes(XVII, r)


def test_la_xive_tient_sur_trois_niveaux_sans_trait_masque():
    """Cazeneuve et Philippe I débordaient à droite : ils s'écrivent vers la
    gauche de leur trait."""
    r = _ranger(XIV, 340)
    assert r["nombre"] == 3
    assert r["aDroite"] == [False, False, True, True]
    assert r["niveaux"] == [1, 0, 1, 2]
    _verifier_contraintes(XIV, r)


def test_un_texte_ne_se_colle_pas_au_trait_d_au_dessus():
    """XVe : à 2 px de garde, « 1 an 10 mois 9 jours » (Castex) touchait
    presque le trait de Borne, placé plus haut. Castex monte."""
    r = _ranger(XV, 340)
    _verifier_contraintes(XV, r)
    assert r["niveaux"][1] > r["niveaux"][2], "Castex passe au-dessus de Borne"


def test_au_dela_de_sept_noms_le_placement_reste_valide():
    """Glouton au-delà de sept : moins bon peut-être, jamais fautif — tant
    qu'un rangement existe (deux noms dont chacun couvre le trait de l'autre
    n'en ont aucun : voir le test suivant)."""
    noms = [{"nom": f"G{i}", "x": i * 45, "largeur": 70 + (i % 3) * 10} for i in range(10)]
    r = _ranger(noms, 500)
    _verifier_contraintes(noms, r)


def test_deux_noms_le_meme_jour_ne_plantent_pas():
    noms = [{"nom": "A", "x": 50, "largeur": 60}, {"nom": "B", "x": 50, "largeur": 60}]
    r = _ranger(noms, 340)
    assert sorted(r["niveaux"]) == [0, 1]


def test_un_meme_premier_ministre_se_reunit_s_il_se_suit():
    r = _executer("""
const g = (nom) => ({ nom });
const out = (gs) => f.reunirParPremierMinistre(gs.map(g)).map((x) => [x.premierMinistre, x.membres.map((m) => m.libelle)]);
console.log(JSON.stringify({
  lecornu: out(['Attal', 'Barnier', 'Bayrou', 'Lecornu I', 'Lecornu II']),
  fillon: out(['Fillon I', 'Fillon II', 'Fillon III', 'Ayrault I']),
  separes: out(['Philippe I', 'Castex', 'Philippe II']),
  liaisons: [0, 1, 2].map((i) => f.liaison(i, 3)),
}));
""")
    assert r["lecornu"][-1] == ["Lecornu", ["Lecornu I", "II"]]
    assert len(r["lecornu"]) == 4
    assert r["fillon"][0] == ["Fillon", ["Fillon I", "II", "III"]]
    assert [x[0] for x in r["separes"]] == ["Philippe", "Castex", "Philippe"], (
        "deux gouvernements d'un même Premier ministre séparés par un autre restent séparés"
    )
    assert r["liaisons"] == ["", ", ", " et "]


def test_la_duree_reunie_se_calcule_sur_les_dates():
    """« 1 an 1 mois 17 jours » sur la maquette additionnait deux textes ; la
    durée se calcule du début du premier à la fin du dernier."""
    code = LEGISLATURE.read_text(encoding="utf-8")
    assert "sous: dureeEnClair(premier.d0, dernier.d1).join(' ')" in code


def test_la_fiche_de_gouvernement_montre_ci_moins_4_a_ci_plus_1():
    code = GOUVERNEMENT.read_text(encoding="utf-8")
    assert "tries.slice(Math.max(0, ci - 4), ci + 2)" in code
    assert re.search(r"<FriseDesNoms hauteurNiveau=\{22\}", code)


def test_les_annees_de_la_lignee_une_par_legislature():
    """Lignée socialiste à 390 px : ~20,5 px par an, « 2013 » fait 33 px."""
    r = _executer("console.log(JSON.stringify([f.pasDesAnnees(20.5, 33), f.pasDesAnnees(70, 33), f.pasDesAnnees(40, 33)]));")
    assert r == [4, 1, 2]


def test_les_annees_d_une_fenetre_ne_se_touchent_pas():
    """CASTEX : dix ans dans 340 px ; 2023 et 2024 se chevauchaient au bord."""
    r = _executer("""
const xs = [9, 45, 81, 117, 153, 189, 225, 261, 297, 333];
console.log(JSON.stringify(f.anneesLisibles(xs, 340, 32)));
""")
    gauches = [g["gauche"] for g in r]
    assert all(0 <= g <= 340 - 32 for g in gauches)
    assert all(b - a >= 32 + 8 for a, b in zip(gauches, gauches[1:]))
    assert [g["i"] for g in r] == [0, 2, 4, 6, 8]
