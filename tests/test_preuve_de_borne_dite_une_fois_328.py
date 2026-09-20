"""Une preuve de borne se dit une fois par liste, jamais deux (#328).

« Ce qu'on n'a pas pu lire » range chaque liste du profil sous ses états —
« couvert depuis le 19/06/2002 », « hors couverture jusqu'au 18/06/2002 » — et
chaque état porte la PREUVE de sa borne. Une même borne explique souvent les
deux : le référentiel AMO30 ne rattache aucun acteur à un mandat antérieur à la
XIIe législature, ce qui dit à la fois jusqu'où la couverture va et à partir de
quand elle commence.

Le corpus porte donc la même chaîne sur les deux entrées, et la fiche
l'imprimait deux fois. Mesuré sur la page rendue, le 09/09/2026 : **148 mots en
double** sur `jerome-guedj` et `marine-le-pen`, **197** sur `edouard-philippe`.

LA CORRECTION NE PASSE PAS PAR LA SOURCE, et c'est le point que ces tests
tiennent. `couverture_profil._deriver` écrit deux entrées par liste : la seconde
porte toujours `borne.preuve`, la première la porte aussi SAUF quand un fait
« hors AN » est établi, où elle porte la sienne. Mesuré hors dépôt sur les 27
candidats, 135 listes portant au moins une preuve : 69 répètent la
même, **35 en portent de différentes** — sur `marine-tondelier`, la borne AMO30
et l'absence déclarée dans la table de correspondance expliquent deux états
distincts de la même liste. Supprimer la seconde preuve « parce qu'elle fait
doublon » effacerait un fait dans ces 35 cas.

La donnée reste donc vraie sur chaque état ; c'est l'affichage qui ne répète
pas, par `preuveDejaDite`.

CE QUE CES TESTS NE COUVRENT PAS (§2 règle 5) : aucun composant React n'est
rendu ici. La disparition effective du doublon a été vérifiée hors dépôt contre
le paquet construit, sur les quatre profils cités — 0 mot en double après, et
les deux preuves distinctes de `marine-tondelier` toujours affichées.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
SRC = RACINE / "web" / "UI_finale" / "src"
PROFIL = SRC / "utils" / "profilCandidat.js"
FICHE = SRC / "components" / "CandidateProfile.jsx"


def sans_commentaires(source: str) -> str:
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"(?<!:)//[^\n]*", "", source)


@pytest.fixture(scope="module")
def profil() -> str:
    return sans_commentaires(PROFIL.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def fiche() -> str:
    return sans_commentaires(FICHE.read_text(encoding="utf-8"))


def test_la_marque_est_posee_par_le_calcul_et_non_par_le_rendu(profil: str) -> None:
    """Un dédoublonnage écrit dans le JSX est un dédoublonnage qu'aucun test ne lit."""
    bloc = profil[profil.index("export function couvertureDesListes") :]
    bloc = bloc[: bloc.index("\n}")]
    assert "preuveDejaDite" in bloc
    assert "new Set()" in bloc, "rien ne mémorise les preuves déjà dites"


def test_la_preuve_reste_portee_par_chaque_etat(profil: str) -> None:
    """La marque dit « ne la répète pas », pas « cet état n'a pas de preuve ».

    Mettre `preuve: null` sur la seconde occurrence rendrait la donnée fausse :
    les deux états portent bien la même borne, et c'est vrai.
    """
    bloc = profil[profil.index("export function couvertureDesListes") :]
    bloc = bloc[: bloc.index("\n}")]
    assert "preuve," in bloc
    # `borne ? null : e.preuve` est la SEULE mise à null tolérée, et elle porte
    # sur une preuve qui n'est pas supprimée mais déplacée sur `/couverture`
    # (#328). Toute autre annulerait un fait propre à la personne.
    assert bloc.count("null") == bloc.count("borne ? null : e.preuve ?? null") + bloc.count("?? null")


def test_la_memoire_est_desormais_celle_de_la_SECTION(profil: str) -> None:
    """La mémoire est partagée entre les listes — et c'est le renversement de #328.

    #802 l'avait délibérément remise à zéro par liste : partagée, la borne AMO30
    aurait disparu de « Votes » parce que « Mandats et fonctions » l'avait déjà
    écrite, alors que ce sont deux listes indépendantes.

    CETTE RAISON TOMBE AVEC LA BORNE. Les preuves de borne ne sont plus rendues
    du tout (`ETATS_PORTANT_LA_BORNE`) : elles vivent sur `/couverture`. Ce qui
    reste est propre à la personne ou au run — « aucun acteur AMO30 pour X »,
    « extraction du groupe Senat:LR suspendue » —, identique d'une liste à
    l'autre, et se répétait cinq fois pour rien : 700 mots sur la fiche
    Retailleau, dont 140 par liste pour le seul certificat de suspension.
    """
    bloc = profil[profil.index("export function couvertureDesListes") :]
    bloc = bloc[: bloc.index("\n}")]
    avant_map = bloc[: bloc.index("return LISTES_COUVERTES.map")]
    assert "new Set()" in avant_map, "la mémoire est redevenue locale à une liste"


def test_la_borne_de_source_n_est_plus_rendue_sur_la_fiche(profil: str) -> None:
    """Elle ne dit rien de la personne : elle dit ce que l'Assemblée publie.

    Le discriminant est l'ÉTAT, garanti par `couverture_profil._deriver` qui
    attache `borne.preuve` à `couvert` et `hors_couverture` et bascule sur
    `fait_etabli` dès que la preuve devient propre à la personne — pas une
    reconnaissance du texte de la preuve, qui serait une jointure par
    ressemblance (#639).
    """
    assert "export const ETATS_PORTANT_LA_BORNE" in profil
    bloc = profil[profil.index("export const ETATS_PORTANT_LA_BORNE") :]
    assert "'couvert'" in bloc[:200] and "'hors_couverture'" in bloc[:200]
    calcul = profil[profil.index("export function couvertureDesListes") :]
    calcul = calcul[: calcul.index("\n}")]
    assert "ETATS_PORTANT_LA_BORNE.has(e.etat)" in calcul


def test_le_rendu_saute_la_repetition_et_rien_d_autre(fiche: str) -> None:
    assert "e.preuve && !e.preuveDejaDite" in fiche


def test_le_producteur_pose_bien_les_deux_cas() -> None:
    """Le garde-fou n'a de sens que si les deux cas existent vraiment.

    `couverture_profil._deriver` écrit DEUX entrées par liste : l'état dans la
    fenêtre et l'état hors couverture. La seconde porte toujours `borne.preuve` ;
    la première la porte AUSSI, sauf quand un fait « hors AN » est établi, où
    elle porte la sienne. C'est de là que viennent les deux cas — la répétition
    et la divergence —, et c'est pourquoi le dédoublonnage ne peut pas se faire
    à la source : il effacerait un fait dans le second cas.

    Ce test lit le PRODUCTEUR, jamais `pivot_data/` : aucun test ne lit le corpus
    vivant (AGENTS.md §3b), et `test_ci_perimetre_sparse_checkout.py` refuse le
    chemin — un test qui le lirait passerait en local et échouerait en CI.
    """
    source = (RACINE / "src" / "couverture_profil.py").read_text(encoding="utf-8")
    # Le DERNIER `couverture[liste] = [` est celui des deux entrées bornées ;
    # les précédents traitent les collectes écartées et les pannes.
    depart = source.rindex("couverture[liste] = [")
    bloc = source[depart:]
    bloc = bloc[: bloc.index("\n        ]")]
    assert bloc.count("borne.preuve") == 1, (
        "l'entrée hors couverture ne porte plus la preuve de la borne"
    )
    assert "preuve_dans_la_fenetre" in bloc, (
        "l'entrée dans la fenêtre ne porte plus de preuve distincte possible"
    )
    amont = source[:depart]
    assert "preuve_dans_la_fenetre = borne.preuve" in amont, "le cas RÉPÉTÉ a disparu"
    assert "preuve_dans_la_fenetre = fait_hors_an.preuve" in amont, (
        "le cas DIVERGENT a disparu : le dédoublonnage pourrait alors se faire à la source"
    )
