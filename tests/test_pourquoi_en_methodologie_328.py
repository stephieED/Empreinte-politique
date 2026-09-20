"""Le « pourquoi » descend en méthodologie, la fiche garde la limite (#328).

`DESIGN_SYSTEM.md` §7 règle 2 : « Le texte explicatif est un aveu d'échec. […]
une limite tient en deux mots, une explication en paragraphe. » Un audit de la
page rendue, le 09/09/2026, a mesuré six blocs au-dessus de cette limite — le
critère de « Ce qu'il a voté » à **58 mots** en tête — et deux modes d'emploi
qui ne s'accordaient même pas sur le vouvoiement.

La propriétaire a tranché : le raisonnement va dans la méthodologie, la fiche ne
garde qu'une mention brève et le lien vers le paragraphe. Pour que ce lien
dépose le lecteur devant SA règle et non en haut d'une page de douze sections,
**chaque section de la fiche a son ancre, et une seule** :

    fonctions · propose · votes · ecarts · interventions · couverture

CE QUE CES GARDE-FOUS PROTÈGENT, et qui se reperd tout seul :

1. **Un critère de section qui regrossit.** Le critère est la mise en garde
   permanente qui a remplacé les KPI au survol ; c'est là que les phrases
   s'accumulent, parce que chacune paraît utile isolément.
2. **Une explication écrite aux deux endroits.** Le `pourquoi` des trois refus
   n'est pas recopié dans la méthodologie : les deux pages rendent le même
   `STATED_REFUSALS`. Une phrase écrite deux fois est une phrase qui divergera.
3. **Une ancre qui ne correspond à rien d'affichable.** Une section de
   méthodologie que nul renvoi n'atteint est une section que personne ne lit.

CE QU'ILS NE COUVRENT PAS (§2 règle 5) : aucun composant React n'est rendu ici.
La longueur effective a été mesurée hors dépôt sur la page construite,
`jerome-guedj` à 1 440 px — **1 772 mots de notre copie avant, 1 562 après**, et
les six ancres répondent.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
SRC = RACINE / "web" / "UI_finale" / "src"
FICHE = SRC / "components" / "CandidateProfile.jsx"
METHODO = SRC / "pages" / "MethodologyPage.jsx"
LECTURE_JSX = SRC / "components" / "Lecture.jsx"
LECTURE_JS = SRC / "utils" / "lecture.js"
PROFIL = SRC / "utils" / "profilCandidat.js"
VOTES = SRC / "components" / "VotesParPeriode.jsx"

#: Une ancre par section de la fiche, et l'ordre est celui de la fiche.
ANCRES = ("fonctions", "propose", "votes", "ecarts", "interventions", "couverture")

#: Au-delà, ce n'est plus une limite, c'est une explication.
MOTS_MAX_CRITERE = 22


def sans_commentaires(source: str) -> str:
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    source = re.sub(r"\{/\*.*?\*/\}", "", source, flags=re.DOTALL)
    return re.sub(r"(?<!:)//[^\n]*", "", source)


@pytest.fixture(scope="module")
def fiche() -> str:
    return sans_commentaires(FICHE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def methodo() -> str:
    return METHODO.read_text(encoding="utf-8")


# ── Les six ancres, et le renvoi qui les atteint ─────────────────────────────


def test_la_methodologie_porte_une_ancre_par_section_de_la_fiche(methodo: str) -> None:
    for ancre in ANCRES:
        assert f"id: '{ancre}'" in methodo, f"ancre #{ancre} absente de la méthodologie"


def test_chaque_ancre_est_atteinte_par_un_renvoi_de_la_fiche(fiche: str) -> None:
    """Une section de méthodologie que nul lien n'atteint est une section morte."""
    liens = set(re.findall(r"/methodologie#([a-z]+)", fiche))
    for autre in (VOTES, SRC / "components" / "ParolesParPeriode.jsx",
                  SRC / "components" / "EcartsGroupe.jsx"):
        liens |= set(re.findall(r"/methodologie#([a-z]+)", autre.read_text(encoding="utf-8")))
    manquantes = [a for a in ANCRES if a not in liens]
    assert not manquantes, f"ancres sans renvoi : {manquantes}"


def test_aucun_renvoi_ne_pointe_vers_une_ancre_inexistante(methodo: str) -> None:
    ids = set(re.findall(r"id: '([a-z]+)'", methodo))
    for fichier in SRC.rglob("*.jsx"):
        for ancre in re.findall(r"/methodologie#([a-z]+)", fichier.read_text(encoding="utf-8")):
            assert ancre in ids, f"{fichier.name} renvoie vers #{ancre}, qui n'existe pas"


# ── La fiche garde la limite, pas l'explication ──────────────────────────────


def test_les_criteres_de_section_tiennent_en_une_limite(fiche: str) -> None:
    criteres = re.findall(r'critere="([^"]+)"', fiche)
    assert criteres, "aucun critère trouvé : le sélecteur a changé"
    trop_longs = [(len(c.split()), c) for c in criteres if len(c.split()) > MOTS_MAX_CRITERE]
    assert not trop_longs, (
        "ces critères expliquent au lieu de limiter — le paragraphe va dans la "
        f"méthodologie (DESIGN_SYSTEM §7 règle 2) : {trop_longs}"
    )


def test_le_critere_des_votes_ne_redit_plus_la_regle_de_derniere_lecture(fiche: str) -> None:
    """Elle est publiée SOUS la figure, où #711 la veut — à côté du chiffre.

    L'écrire aussi en tête de section la faisait lire deux fois, et c'est cette
    répétition qui portait le critère à 58 mots.
    """
    # Le critère de section a été retiré le 10/09 : « Une position par texte,
    # rangée par période politique. Aucun taux de participation n'est publié. »
    # disait deux choses déjà dites — la première par la figure elle-même, la
    # seconde par la méthodologie et le pied du site.
    # L'ancrage est sur « taux de participation », propre au critère des VOTES :
    # celui des interventions parle lui aussi de période politique, et s'y caler
    # ferait passer ce test pour une garde de la section voisine.
    assert not [c for c in re.findall(r'critere="([^"]+)"', fiche) if "taux de participation" in c], (
        "le critère de la section des votes est revenu"
    )
    assert "LAST_READING_LABEL" in fiche, (
        "l'étiquette courte reste à côté du chiffre : c'est ce que #711 garantit "
        "encore, le raisonnement vivant en méthodologie"
    )


def test_les_trois_refus_ne_sont_plus_rendus_que_par_la_methodologie() -> None:
    """#801 avait laissé la phrase sur la fiche et descendu le `pourquoi`.

    #328 retire la phrase aussi : mesuré sur la page rendue de `delphine-batho`,
    « aucun classement » y apparaissait TROIS fois — le bloc des refus en §6, le
    pied de la fiche juste en dessous, et le pied du site. Les trois refus
    restent publiés là où ils s'argumentent : la méthodologie, source unique, et
    « Ce que vous ne trouverez pas ici » sur l'accueil.

    `STATED_REFUSALS` n'est donc plus rendu qu'une fois — et le `pourquoi` n'est
    pas supprimé, il est là.
    """
    lecture_jsx = LECTURE_JSX.read_text(encoding="utf-8")
    assert "export function Interdits" not in lecture_jsx, (
        "la fiche republie les refus sous la figure"
    )
    fiche = FICHE.read_text(encoding="utf-8")
    assert "<Interdits" not in fiche

    donnees = LECTURE_JS.read_text(encoding="utf-8")
    assert "pourquoi:" in donnees, "le pourquoi a été supprimé au lieu d'être déplacé"
    methodo = METHODO.read_text(encoding="utf-8")
    assert "STATED_REFUSALS.map" in methodo, "la méthodologie ne publie pas les refus"
    assert "refus.pourquoi" in methodo


def test_les_limites_disent_un_fait_et_pas_sa_raison() -> None:
    """Ce sont les textes de `limitesDuProfil`, calculés sur CE profil.

    Le raisonnement — « le déduire d'un comportement de vote serait un jugement »
    — vit sous `#couverture`, où mène le renvoi posé sous la liste.
    """
    profil = sans_commentaires(PROFIL.read_text(encoding="utf-8"))
    bloc = profil[profil.index("const limites = [];") :]
    bloc = bloc[: bloc.index("return limites;")]
    for phrase in ("serait un jugement", "estampillage de la chambre",
                   "signés comme ministre"):
        assert phrase not in bloc, f"« {phrase} » explique au lieu de constater"
    methodo = METHODO.read_text(encoding="utf-8")
    assert "serait un jugement, pas une lecture" in methodo
    assert "estampillage de la chambre" in methodo


# ── Une seule voix ───────────────────────────────────────────────────────────


def test_la_fiche_vouvoie_partout(fiche: str) -> None:
    """« Clique un ruban » et « Cliquez une barre » cohabitaient sur la page."""
    votes = sans_commentaires(VOTES.read_text(encoding="utf-8"))
    for source in (fiche, votes):
        assert not re.search(r"\bClique\b", source), "un tutoiement subsiste"
