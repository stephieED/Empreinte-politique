"""`README.md` est la porte d'entrée, et elle tient sur une page (#1139).

`AGENTS.md` §8 le dit depuis longtemps — « **The front door, one page.** » — et
rien ne le tenait. Mesuré le 25/09/2026 : **341 lignes, 22 736 caractères, 12
sections**, dont une de **114 lignes** qui doublait la page « Sources » du site.
Le fichier portait aussi `389 397 actes` et `389 456 décrets`, deux chiffres nus
que le corpus avait déjà dépassés (389 506), et `5 041 tests` quand la suite en
comptait plus de 6 000.

## Pourquoi la dérive ne se voyait pas

Elle est invisible au coup par coup : chaque lot ajoute trois lignes « pour que
ce soit dit quelque part », et personne ne mesure le total. `AGENTS.md`, lui, est
tenu contre sa propre règle par `test_agents_sans_etat_courant_chiffre.py`. Le
README n'avait pas un problème de garde manquant en général — **il lui manquait
celui-là**, et ce fichier est le même patron pointé sur lui.

## Ce que ce fichier tient, et ce qu'il ne tient pas

Il mesure la **taille** et refuse les **chiffres d'inventaire sans date**. Il ne
juge pas le contenu : ce que le README doit nommer — chaque source vivante, la
licence du code — est déjà tenu par `test_sources_documentees.py` et
`test_licence_du_code_1032.py`, et le dupliquer ici ferait deux endroits à
corriger pour une même règle.
"""

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
README = RACINE / "README.md"

#: Mesuré après la réécriture de #1139 : 232 lignes, 13 591 caractères.
#: La marge est étroite **exprès**. Elle ne dit pas « voilà la place qui
#: reste » : elle dit qu'au-delà, on n'ajoute pas — on choisit ce qui part, ou
#: on écrit ailleurs. Relever ces seuils est une décision, pas un ajustement.
LIGNES_MAX = 250
CARACTERES_MAX = 15_000

#: Une section de plus, c'est une raison de plus de venir écrire ici. Neuf, plus
#: l'en-tête. La section « Ce que la couverture ne couvre pas encore » avait à
#: elle seule un tiers du fichier — c'est ce que ce plafond empêche de refaire.
SECTIONS_MAX = 10

#: Les chiffres d'inventaire : un nombre à séparateur de milliers, ou un nombre
#: de trois chiffres et plus suivi d'une chose que le pipeline produit. Ce sont
#: les deux formes qui ont vieilli dans ce fichier.
#:
#: **Trois chiffres et non quatre** : « couvriront 305 des 461 membres » n'a pas
#: de séparateur de milliers et périme exactement comme les autres. Descendre
#: sous trois attraperait « 8 shards » et les numéros de législature, qui sont de
#: l'architecture.
INVENTAIRE = re.compile(
    r"\b\d{1,3}(?: \d{3})+\b"
    # `[\s*_]+` et non `\s+` : le gras Markdown se glisse entre le nombre et le
    # nom — « **305 des 461** membres » est la forme réelle qui a été publiée.
    r"|\b\d{3,}[\s*_]+(?:actes|décrets|arrêtés|ordonnances|tests|profils|fiches|"
    r"interventions|amendements|scrutins|mandats|membres|personnes|textes|"
    r"appartenances|dossiers)\b",
    re.IGNORECASE,
)

#: Une date suffit à rendre un chiffre lisible : il dit un état à un jour, pas
#: l'état courant. C'est la règle que `docs/data-architecture.md` applique déjà.
DATE = re.compile(r"\b\d{2}/\d{2}/\d{4}\b")


def _lignes_hors_code():
    """Saute les blocs de code : une sortie de commande n'est pas une affirmation."""
    dans_code = False
    for numero, ligne in enumerate(README.read_text(encoding="utf-8").split("\n"), 1):
        if ligne.lstrip().startswith("```"):
            dans_code = not dans_code
            continue
        if not dans_code:
            yield numero, ligne


def test_le_readme_tient_sur_une_page():
    texte = README.read_text(encoding="utf-8")
    lignes = len(texte.split("\n"))
    assert lignes <= LIGNES_MAX and len(texte) <= CARACTERES_MAX, (
        f"README.md : {lignes} lignes, {len(texte)} caractères "
        f"(plafonds : {LIGNES_MAX} / {CARACTERES_MAX}).\n"
        "AGENTS.md §8 : « the front door, one page ». Il avait atteint 341 lignes "
        "sans que personne le mesure, dont un tiers qui doublait la page "
        "« Sources » du site. Ce qui doit être dit en détail se dit dans "
        "`docs/` — ici, on le nomme et on renvoie."
    )


def test_le_readme_ne_compte_pas_plus_de_sections_qu_il_n_en_faut():
    titres = [l for _, l in _lignes_hors_code() if l.startswith("## ")]
    assert len(titres) <= SECTIONS_MAX, (
        f"{len(titres)} sections de niveau 2 (plafond : {SECTIONS_MAX}) :\n  "
        + "\n  ".join(t[3:] for t in titres)
        + "\n\nUne section de plus est une raison de plus de venir écrire ici."
    )


def test_le_readme_ne_porte_aucun_chiffre_d_inventaire_sans_sa_date():
    """Un chiffre nu se périme sans bruit, et celui-ci l'avait déjà fait.

    Deux issues possibles, et la première est la bonne : **retirer** le chiffre,
    parce que la front door n'a pas à dénombrer ; ou le garder en écrivant le
    jour où il a été mesuré, comme `docs/data-architecture.md` le fait.
    """
    fautes = [
        (numero, m.group(0), ligne.strip()[:80])
        for numero, ligne in _lignes_hors_code()
        if not DATE.search(ligne)
        for m in [INVENTAIRE.search(ligne)] if m
    ]
    assert not fautes, (
        "README.md porte un chiffre d'inventaire sans date de mesure :\n"
        + "\n".join(f"  ligne {n} — « {q} » : {t}" for n, q, t in fautes)
        + "\n\n`389 397 actes` a été lu comme l'état courant pendant trois jours "
        "après avoir cessé de l'être. Retirer le chiffre, ou écrire sa date."
    )


def test_le_motif_attrape_ce_qui_a_casse_et_epargne_le_reste():
    """Sans ce test, un motif trop large finit désarmé — et un trop étroit ne
    voit pas repasser ce qui est déjà passé une fois."""
    # Ce qui a vieilli dans ce fichier.
    assert INVENTAIRE.search("| 389 397 actes, relus sur les deux derniers mois |")
    assert INVENTAIRE.search("**389 456 décrets, arrêtés et ordonnances**")
    assert INVENTAIRE.search("La suite tourne en un peu plus d'une minute (**5 041 tests**")
    assert INVENTAIRE.search("couvriront **305 des 461** membres")

    # Ce qu'il doit épargner : une année, une date, une version, un numéro
    # d'issue, un identifiant de licence, un compte d'architecture en lettres.
    assert not INVENTAIRE.search("l'élection présidentielle française de 2027")
    assert not INVENTAIRE.search("antérieurs au 19/06/2002, relus à la main")
    assert not INVENTAIRE.search("L'interface de production : React 19 + Vite")
    assert not INVENTAIRE.search("Le code est sous AGPL-3.0 ([`LICENSE`](LICENSE))")
    assert not INVENTAIRE.search("les huit règles non négociables")
    assert not INVENTAIRE.search("depuis Fillon I (17/05/2007)")
    assert not INVENTAIRE.search("8 shards découpés par modulo")
    assert not INVENTAIRE.search("la XIV<sup>e</sup> législature")

    # Un petit compte passe : « 35 mandats sur 15 profils » est un ordre de
    # grandeur, pas un inventaire, et il ne vaut pas la peine d'un plafond.
    assert not INVENTAIRE.search("**35 mandats sur 15 profils**")

    # Et la date sauve une ligne que le motif attrape : c'est tout l'objet de
    # l'exception, et la seule façon de garder un chiffre ici.
    ligne = "**389 506 actes** au 26/09/2026"
    assert INVENTAIRE.search(ligne) and DATE.search(ligne)
