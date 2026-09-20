"""La baseline du site (#1026).

« 100 % automatisé • 100 % sourcé • 0 score • 0 filtre ». Avant le 18/09/2026,
la promesse du site était écrite là où elle ne se lit pas : dans le `<title>`,
dans la `meta description` et dans l'introduction de /methodologie. L'en-tête et
l'accueil n'en disaient rien — l'accueil portait une sous-ligne qui en disait
deux traits sur trois, « Des faits sourcés, sans note ni classement ».

Ce que ces garde-fous protègent :

1. **Une seule définition.** Les quatre mentions vivent dans `Baseline.jsx`. Une
   promesse recopiée dans deux composants est une promesse qui divergera, et
   c'est exactement ce qui s'était produit entre la `meta description` et
   /methodologie, qui ne disaient déjà pas la même chose.
2. **Deux places, arbitrées.** Le bandeau de l'accueil et le pied de page, sous
   la marque. **Pas l'en-tête collé** : une phrase répétée en haut de chaque
   écran devient du décor, et la rangée est à hauteur fixe (#968).
3. **Le jaune ne porte le texte que sur fond sombre.** 16,01:1 sur l'encre,
   1,05:1 sur le fond clair (DESIGN_SYSTEM §2) : les puces prennent l'accent
   dans le bandeau sombre de l'accueil, le gris dans le pied de page.

CE QU'ILS NE COUVRENT PAS (§2 règle 5) : aucun composant React n'est rendu ici.
Le rendu a été capturé le 18/09/2026 à 1440 px et 390 px, sans erreur console.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
SRC = RACINE / "web" / "UI_finale" / "src"

BASELINE = SRC / "components" / "Baseline.jsx"
BASELINE_CSS = SRC / "components" / "Baseline.css"
PIED = SRC / "components" / "PiedDeSite.jsx"
HERO = SRC / "components" / "landing" / "Hero.jsx"
ENTETE = SRC / "components" / "EnTeteSite.jsx"

MENTIONS = ("automatisé", "sourcé", "0 score", "0 filtre")


def sans_commentaires(source: str) -> str:
    """Le code exécuté seul : les en-têtes CITENT ce qu'ils proscrivent."""
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"(?<!:)//[^\n]*", "", source)


@pytest.fixture(scope="module")
def baseline() -> str:
    return sans_commentaires(BASELINE.read_text(encoding="utf-8"))


def test_les_quatre_mentions_sont_definies_une_seule_fois(baseline: str) -> None:
    """Elles sont dans `Baseline.jsx`, et nulle part ailleurs."""
    for mention in MENTIONS:
        assert mention in baseline, mention
    for hote in (PIED, HERO, ENTETE):
        source = sans_commentaires(hote.read_text(encoding="utf-8"))
        assert "0 score" not in source, f"{hote.name} recopie la baseline"


def test_l_espace_avant_le_pourcent_est_insecable(baseline: str) -> None:
    """« 100 » et « % » ne se séparent pas en fin de ligne : le pied de page
    passe sur deux lignes sous 900 px."""
    assert "100 % automatisé" in baseline or "100\\u00a0% automatisé" in baseline
    assert "100 % automatisé" not in baseline


def test_les_deux_hotes_la_lisent() -> None:
    """Le bandeau de l'accueil et le pied de page, avec leur propre échelle."""
    hero = sans_commentaires(HERO.read_text(encoding="utf-8"))
    pied = sans_commentaires(PIED.read_text(encoding="utf-8"))
    assert 'className="baseline--bandeau"' in hero
    assert 'className="baseline--pied"' in pied
    for source in (hero, pied):
        assert "Baseline" in source


def test_l_en_tete_colle_ne_la_porte_pas() -> None:
    """Arbitré le 18/09/2026, sur maquette rendue : répétée en haut de chaque
    écran, elle devient du décor — et la rangée est à hauteur fixe (#968)."""
    entete = sans_commentaires(ENTETE.read_text(encoding="utf-8"))
    assert "Baseline" not in entete
    assert "baseline" not in entete


def test_l_ancienne_sous_ligne_de_l_accueil_a_disparu() -> None:
    """Elle disait deux des trois traits, et la liste des candidats juste
    dessous dit déjà par où entrer : garder les deux, c'était les répéter."""
    hero = HERO.read_text(encoding="utf-8")
    assert "<p>Des faits sourcés, sans note ni classement" not in hero


def test_le_jaune_ne_porte_le_texte_que_sur_fond_sombre() -> None:
    """1,05:1 sur le fond clair : le pied de page garde le gris."""
    css = BASELINE_CSS.read_text(encoding="utf-8")
    bandeau = css.split(".baseline--bandeau .baseline-puce {")[1].split("}")[0]
    assert "var(--accent)" in bandeau
    pied = css.split(".baseline--pied {")[1].split("}")[0]
    assert "var(--muted)" in pied
    assert "var(--accent)" not in pied
