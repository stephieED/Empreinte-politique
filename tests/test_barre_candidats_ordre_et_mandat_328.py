"""La barre des candidats : ordre alphabétique, et ce que la fiche peut montrer (#328).

Deux demandes de la propriétaire, le 09/09/2026.

**L'ordre.** `raw_data/candidats.json` suit l'ordre de collecte, que rien ne
rend lisible : une barre de trente pastilles où l'œil ne peut pas prédire la
place d'un nom se parcourt en entier à chaque fois. Le tri porte sur `nom` — ce
que le lecteur lit — et non sur un patronyme reconstruit : découper « Le Pen »
ou « Dupont-Aignan » demanderait une règle que la source ne donne pas.

**Le grisé, retiré le 07/10/2026.** Une pastille grisée disait que la fiche ne
porte NI mandat à l'Assemblée nationale NI fonction gouvernementale. La
propriétaire l'a retiré, sur la barre comme sur l'accueil : toutes les pastilles
ont la même forme, et ce que la fiche ne porte pas se lit sur la fiche. Le
manifeste garde le fait (`aSiegeOuGouverne`), que plus rien n'affiche.

DEUX FAITS, ET AUCUN DEVINÉ. `chambres` est le champ dérivé des mandats (#493) :
il vaut `["PE"]` pour un député européen, et un mandat au Parlement européen
n'est pas un mandat à l'Assemblée. `fonction_gouvernementale` est une catégorie
de mandat, pas une inférence sur un intitulé. Mesuré sur les 30 candidats du
manifeste : 16 ont l'un des deux, 14 n'ont ni l'un ni l'autre. Ségolène Royal
n'a aucun vote publié mais sept fonctions gouvernementales : elle n'est PAS
comptée sans mandat, parce que le critère porte sur ce qu'elle a exercé et non sur ce que
nous avons collecté.

CE QUE CES TESTS NE COUVRENT PAS (§2 règle 5) : ils ne rendent aucun composant
et n'exécutent pas `sync-data.mjs`. L'ordre affiché a été vérifié hors dépôt sur le paquet construit, à 1 440 px.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale"
SYNC = UI / "scripts" / "sync-data.mjs"
BARRE = UI / "src" / "components" / "CandidatesBar.jsx"
FEUILLE = UI / "src" / "components" / "CandidatesBar.css"
CHARGEUR = UI / "src" / "data" / "index.js"
ACCUEIL_LISTE = UI / "src" / "components" / "landing" / "CommencerAExplorer.jsx"


def sans_commentaires(source: str) -> str:
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    source = re.sub(r"\{/\*.*?\*/\}", "", source, flags=re.DOTALL)
    return re.sub(r"(?<!:)//[^\n]*", "", source)


@pytest.fixture(scope="module")
def sync() -> str:
    return sans_commentaires(SYNC.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def barre() -> str:
    return sans_commentaires(BARRE.read_text(encoding="utf-8"))


def test_le_tri_est_fait_a_la_source_et_pas_dans_l_ui(sync: str, barre: str) -> None:
    """Deux tris pour une même liste sont deux listes qui divergeront."""
    assert "localeCompare(b.nom, 'fr'" in sync
    assert ".sort(" not in barre, "l'UI retrie une liste déjà triée"


def test_le_tri_porte_sur_le_libelle_affiche(sync: str) -> None:
    """Trier sur le slug rangerait « Édouard Philippe » sous « e », loin du É."""
    bloc = sync[sync.index(".sort((a, b)") :]
    bloc = bloc[: bloc.index("\n")]
    assert "a.nom" in bloc and "b.nom" in bloc
    assert "slug" not in bloc


def test_le_critere_lit_deux_faits_sourcees(sync: str) -> None:
    """Deux faits publiés, jamais un intitulé : le champ dérivé `chambres`, et
    la catégorie du mandat."""
    bloc = sync[sync.index("const aSiegeOuGouverne") :]
    bloc = bloc[: bloc.index("\n};")]
    assert "chambres" in bloc, "le banc n'est pas lu dans le champ dérivé"
    assert "fonction_gouvernementale" in bloc


def test_un_mandat_dans_l_une_des_quatre_institutions_suffit(sync: str) -> None:
    """ARBITRAGE RENVERSÉ LE 13/09/2026, et c'est volontaire.

    Ce test s'appelait `test_le_parlement_europeen_ne_vaut_pas_un_mandat_a_l_assemblee`
    et exigeait `includes('AN')` : le Parlement européen ne comptait pas, ce qui
    grisait quatre fiches dont toute la carrière y est. Trois d'entre elles
    portent pourtant de l'activité — Glucksmann 4 672 entrées, Philippot 3 466,
    Massard 432 — et la pastille affirmait « ni vote, ni intervention, ni
    amendement ».

    La propriétaire a tranché : est grisée une fiche **sans mandat dans aucune
    des quatre institutions** — Assemblée nationale, Sénat, Parlement européen,
    gouvernement. `chambres` porte les trois assemblées, la catégorie du mandat
    porte la quatrième, d'où `chambres.length > 0 || gouvernement`.

    Ce que le renversement ne change pas : le critère reste ce qui a été
    EXERCÉ, jamais ce que nous avons collecté — Ségolène Royal, sept fonctions
    gouvernementales et aucun vote publié, n'est pas grisée.
    """
    bloc = sync[sync.index("const aSiegeOuGouverne") :]
    bloc = bloc[: bloc.index("\n};")]
    assert "chambres.length > 0" in bloc, (
        "le critère est redevenu une liste d'institutions nommées : une "
        "cinquième chambre publiée un jour y serait oubliée en silence"
    )
    assert "includes('AN')" not in bloc, (
        "l'Assemblée est redevenue un cas particulier, et le Parlement "
        "européen ne compte plus (arbitrage du 13/09/2026)"
    )


def test_le_manifeste_publie_la_cle_et_le_chargeur_la_lit(sync: str) -> None:
    assert "aSiegeOuGouverne: aSiegeOuGouverne(c.slug)" in sync
    chargeur = sans_commentaires(CHARGEUR.read_text(encoding="utf-8"))
    assert "aSiegeOuGouverne" in chargeur


def test_l_absence_de_cle_ne_grise_pas(chargeur=CHARGEUR) -> None:
    """Un manifeste d'une version antérieure ne doit pas griser tout le monde.

    `!== false` : la clé absente vaut « on ne sait pas », et on ne sait pas ne
    se rend pas comme un fait négatif (§2 règle 5).
    """
    source = sans_commentaires(chargeur.read_text(encoding="utf-8"))
    assert "c.aSiegeOuGouverne !== false" in source


def test_aucune_pastille_n_est_grisee(barre: str) -> None:
    """Retiré par la propriétaire le 07/10/2026, avec son infobulle.

    Ni grisé, ni `disabled`, ni retrait de la liste : toutes les pastilles ont
    la même forme, sur la barre comme sur l'accueil.
    """
    accueil = sans_commentaires(ACCUEIL_LISTE.read_text(encoding="utf-8"))
    feuille = sans_commentaires(FEUILLE.read_text(encoding="utf-8"))
    for nom, source in (("la barre", barre), ("l'accueil", accueil), ("la feuille", feuille)):
        assert "sans-mandat" not in source, f"{nom} grise encore une pastille"
    for nom, source in (("la barre", barre), ("l'accueil", accueil)):
        assert "disabled" not in source
        assert "aSiegeOuGouverne" not in source, f"{nom} distingue encore les fiches sans mandat"
        assert "ni vote, ni intervention, ni amendement" not in source
