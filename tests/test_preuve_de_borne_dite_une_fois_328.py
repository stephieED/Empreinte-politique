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

LA FICHE NE REND PLUS AUCUNE PREUVE, DEPUIS LE 01/10/2026. Le tableau « Ce que
chaque liste porte » a quitté « Ce qu'on n'a pas pu lire » : la section est
devenue une seule liste de manques, et ni les états du pipeline (`couvert`,
`hors_couverture`, `non_collecte`, `fait_etabli`) ni leur preuve ne s'y
affichent. `couvertureDesListes`, `preuveDejaDite` et `ETATS_PORTANT_LA_BORNE`
sont partis avec lui : il n'y a plus de répétition à sauter là où plus rien
n'est imprimé.

CE QUI SE GARDE DE LA RÈGLE, et c'est ce que ces tests tiennent désormais :
- ce qui se dit une fois ne se dit pas trois — les listes qui partagent le même
  manque et la même date tiennent sur UNE ligne ;
- la preuve de borne ne revient pas sur la fiche, la DATE seule y paraît, et
  seulement en face d'un mandat qu'elle laisse hors de la source ;
- LA DONNÉE N'EST TOUJOURS PAS CORRIGÉE À LA SOURCE : le producteur écrit ses
  deux entrées par liste, et le dernier test le garde tel quel.

CE QUE CES TESTS NE COUVRENT PAS (§2 règle 5) : aucun composant React n'est
rendu ici. La liste rendue a été vérifiée hors dépôt par rendu serveur sur les
31 fiches publiées, le 01/10/2026 ; `tests/test_section_6_liste_de_manques.py`
exécute le calcul sur des entrées copiées du corpus.
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


def test_la_liste_est_posee_par_le_calcul_et_non_par_le_rendu(profil: str, fiche: str) -> None:
    """Un regroupement écrit dans le JSX est un regroupement qu'aucun test ne lit.

    C'était vrai du dédoublonnage des preuves (`preuveDejaDite`), ça l'est de la
    liste qui le remplace : l'ordre, les textes et les regroupements sont
    calculés dans `manquesDeLaFiche`, et le composant ne fait que poser des
    lignes.
    """
    assert "export function manquesDeLaFiche" in profil
    bloc = fiche[fiche.index("function Couverture(") :]
    bloc = bloc[: bloc.index("\n}\n")]
    assert "lignes.map((l) => (" in bloc
    assert "<b>{l.titre}</b>" in bloc and "<span>{l.texte}</span>" in bloc
    assert ".sort(" not in bloc and ".filter(" not in bloc, (
        "le composant trie ou filtre les lignes : la règle a quitté le calcul"
    )


def test_la_date_de_source_reste_lue_sur_les_etats_qui_la_portent(profil: str) -> None:
    """La donnée n'est pas réécrite : elle est LUE, sur les états qui datent.

    `couverture_profil._deriver` pose `portee.debut` sur `couvert` et sur
    `fait_etabli` — les deux disent « publiée à partir de ». Ne retenir que le
    premier laissait la borne vide sur les fiches hors AN, dont les cinq listes
    sont `fait_etabli`. Une entrée EUROPÉENNE n'est pas une borne : sa portée va
    de la première à la dernière donnée de la personne.
    """
    assert "const ETATS_DATANT_LA_SOURCE = new Set(['couvert', 'fait_etabli'])" in profil
    bloc = profil[profil.index("export function debutDeSource") :]
    bloc = bloc[: bloc.index("\n}")]
    assert "ETATS_DATANT_LA_SOURCE.has(e.etat)" in bloc
    assert "e.source !== INSTITUTION_PE_SOURCE" in bloc
    assert "e.portee?.debut" in bloc
    assert "bornesDuCorpus?.[liste]" in bloc, (
        "sans le repli sur les bornes du corpus, une liste `non_collecte` — sans "
        "portée — n'a plus de date, et ses mandats non couverts ne se disent plus"
    )


def test_un_meme_manque_se_dit_une_fois_pour_les_listes_qui_le_partagent(profil: str) -> None:
    """Ce qui se répétait cinq fois pour rien ne se répète plus trois fois.

    #802 puis #328 avaient réglé la mémoire des PREUVES — par liste, puis pour
    la section. La liste n'imprime plus de preuve ; ce qui pourrait encore se
    répéter, c'est la phrase : votes, amendements et textes portés commencent le
    même jour et laissent donc le même mandat hors de la source. Ils tiennent
    sur UNE ligne, « Votes, Amendements, Textes portés ».
    """
    bloc = profil[profil.index("export function mandatsNonCouverts") :]
    bloc = bloc[: bloc.index("\n}\n")]
    avant_boucle = bloc[: bloc.index("for (const { cle, titre } of LISTES_D_ACTIVITE)")]
    assert "const groupes = new Map();" in avant_boucle, (
        "la mémoire est redevenue locale à une liste : trois lignes identiques"
    )
    assert "g.titres.join(', ')" in bloc


def test_la_preuve_de_borne_n_est_pas_rendue_et_sa_date_ne_l_est_que_face_a_un_mandat(
    profil: str, fiche: str,
) -> None:
    """Une borne ne dit rien de la personne : elle dit ce que l'Assemblée publie.

    Sa PREUVE vit sur `/couverture` depuis #328, et n'est pas revenue. Sa DATE,
    elle, ne paraît plus sur toutes les fiches (« couvert depuis le 20.06.2012 »
    s'imprimait sur les 31) : seulement dans la phrase d'un mandat qu'elle
    laisse hors de la source, et dans « Avant juin 2002 ».
    """
    assert "preuve" not in fiche, "une preuve de couverture est revenue dans le composant"
    assert "couvertureDesListes" not in profil and "ETATS_PORTANT_LA_BORNE" not in profil
    bloc = profil[profil.index("export function mandatsNonCouverts") :]
    bloc = bloc[: bloc.index("\n}\n")]
    assert "if (!segments.length) continue;" in bloc, (
        "une liste sans mandat non couvert écrirait quand même sa borne"
    )
    assert "la source commence le ${jourEnLettres(g.borne)}" in bloc
    assert "e.preuve" not in profil[profil.index("export function debutDeSource") :], (
        "le calcul de la liste lit une preuve : il n'a besoin que des dates"
    )


def test_le_rendu_ne_connait_plus_aucun_etat_de_pipeline(fiche: str) -> None:
    """« non collecté — collecte écartée par le run qui a produit le profil brut
    (meta.collecte_ecartee, #357) » s'affichait sous une liste de 3 522 entrées.

    L'état décrit le dernier run, pas ce que le dépôt porte : il ne se rend
    plus, ni lui ni les trois autres.
    """
    for etat in ("non_collecte:", "hors_couverture:", "fait_etabli:", "LIBELLE_ETAT", "e.etat"):
        assert etat not in fiche, f"`{etat}` : la fiche rend de nouveau un état de couverture"


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
