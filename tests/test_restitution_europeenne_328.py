"""Une fiche européenne ne se voit plus reprocher une limite qui est la nôtre (#328).

La revue de l'intégration européenne, 13/09/2026, a mesuré sept écarts sur les
7 fiches concernées. Trois d'entre eux ne demandaient ni donnée nouvelle ni
arbitrage : la page disait quelque chose de faux sur ce qu'elle affichait déjà.

**1 et 2 — la section des votes se contredisait avec le tableau d'à côté.** Sur
`raphael-glucksmann`, le tableau « ce que chaque liste porte » annonçait
« Votes : 1 977 entrées — couvert depuis le 18 juillet 2019 » pendant que la
section affichait « Aucun résultat », expliqué par : « Aucune de ses positions
ne porte sur l'ensemble d'un texte au sens de la règle publiée ». Cette règle est
celle de l'Assemblée ; sur une fiche 100 % européenne, elle attribuait à la
personne une limite qui est la nôtre (§2 règle 2). La cause réelle est mesurable :
**0 des 11 013 votes européens** ne porte de `scrutin_id`, donc notre index n'en
rattache aucun.

**3 — « 0 adopté » là où aucun sort n'est publié.** Les 7 303 amendements
européens n'en portent aucun : le compte était juste, mais le lecteur lisait
« aucun n'a été adopté » là où la vérité est « le sort n'est publié pour aucun »
(§2 règle 5).

Ce que ces tests verrouillent, et pourquoi chacun a failli être faux :

- **le cas européen ne se déclenche que si TOUS les votes le sont** : sur une
  fiche mixte — Maurel, Mélenchon, Le Pen — la section doit continuer d'afficher
  les votes de l'Assemblée, et c'est vérifié hors dépôt ;
- **la cause reste `couvert`, jamais `non_collecte`.** Premier jet : le badge
  affichait « Non collecté » au-dessus d'une phrase disant « sont collectées »,
  c'est-à-dire exactement la contradiction que ce correctif retire ;
- **le compte d'adoptés n'est publié que si un sort l'est.**

CE QU'ILS NE COUVRENT PAS (§2 règle 5) : aucun composant React n'est rendu ici.
Vérifié hors dépôt le 13/09/2026 — Glucksmann : « Ses 1 977 positions au
Parlement européen sont collectées, mais aucune n'est rattachée à un scrutin
identifié », et « 590 amendements · 0 dossiers · sort non publié ». Guedj
(2 429 amendements · 25 dossiers · 160 adoptés) et Maurel (64 textes votés) sont
inchangés.
"""

from __future__ import annotations

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale" / "src"

MODULE_REGLES = UI / "utils" / "profilCandidat.js"
COMPOSANT = UI / "components" / "CandidateProfile.jsx"


def sans_commentaires(source: str) -> str:
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"(?<!:)//[^\n]*", "", source)


def test_les_votes_europeens_non_resolus_sont_comptes():
    code = sans_commentaires(MODULE_REGLES.read_text(encoding="utf-8"))
    assert "INSTITUTION_PE_SOURCE = 'parlement_europeen'" in code, (
        "Le marqueur d'institution doit être nommé une fois : trois littéraux "
        "vivaient dans le module, et un quatrième aurait divergé."
    )
    assert "nonResolusEuropeens" in code, (
        "Sans ce compte, la section ne peut pas distinguer « aucun vote sur "
        "l'ensemble d'un texte » de « aucun vote rattaché à un scrutin »."
    )
    bloc = re.search(r"const nonResolusEuropeens = liste\.filter\((.*?)\)\.length;", code, re.DOTALL)
    assert bloc, "Le compte a changé de forme — relire le test."
    assert "!v.scrutin_id" in bloc.group(1), (
        "Un vote rattaché à un scrutin n'est pas un vote non résolu."
    )


def test_les_votes_europeens_ne_sont_plus_declares_hors_de_portee():
    """CE QUE CE TEST TENAIT, ET CE QU'IL TIENT MAINTENANT (#901, 17/09/2026).

    Il verrouillait le message qui remplaçait la figure sur une fiche dont TOUS
    les votes sont européens : « ses N positions au Parlement européen sont
    collectées, mais aucune n'est rattachée à un scrutin identifié ». La cause
    était la nôtre — l'index de l'Assemblée ne résout pas ces positions — et le
    message le disait, avec la bonne cause (`couvert`, pas `non_collecte`).

    Ces positions sont désormais rattachées par NUMÉRO + DATE à
    `pivot_data/scrutins_europeens.json`, et la fiche les AFFICHE. Le message
    n'a plus d'objet, et le garder serait publier un manque qui n'existe pas
    (§2 règle 5). Ce que le test tient désormais : la phrase a disparu, et la
    figure européenne a pris sa place.
    """
    code = sans_commentaires(COMPOSANT.read_text(encoding="utf-8"))
    assert "rattachée à un scrutin identifié" not in code
    assert "votes.nonResolusEuropeens === votes.total" not in code
    bloc = code.split("function Votes({")[1].split("function VotesFrancais")[0]
    assert "europe.periodes" in bloc, (
        "Le versant européen des votes doit être servi par sa propre figure."
    )
    assert "dernier vote retenu pour chaque texte" in bloc, (
        "La règle de sélection se dit à côté du chiffre, comme la dernière "
        "lecture côté français (#711)."
    )


def test_le_compte_des_votes_europeens_non_rattaches_reste_calcule():
    """`nonResolusEuropeens` ne sert plus de motif, mais il mesure encore ce que
    l'index ne résout pas : un compte retiré est un compte qu'on ne peut plus
    surveiller."""
    regles = sans_commentaires(MODULE_REGLES.read_text(encoding="utf-8"))
    assert "nonResolusEuropeens" in regles


def test_le_compte_d_adoptes_n_est_publie_que_si_un_sort_l_est():
    regles = sans_commentaires(MODULE_REGLES.read_text(encoding="utf-8"))
    assert "if (a.sort) sortsPublies += 1;" in regles, (
        "Sans ce compte, rien ne distingue « aucun adopté » de « aucun sort "
        "publié » (§2 règle 5)."
    )
    assert "sortsPublies," in regles, "`sortsPublies` n'est pas rendu à la vue."

    composant = sans_commentaires(COMPOSANT.read_text(encoding="utf-8"))
    # La garde porte désormais sur la population AFFICHÉE (`amdt`), depuis que
    # la section sépare les deux parlements (`amendements-deux-parlements-901`) :
    # le fait tenu est le même, le porteur a changé de nom.
    assert "amdt.sortsPublies === 0" in composant, (
        "La ligne de tête publie encore un `0` quand la source ne dit rien du "
        "sort : les 7 303 amendements européens affichaient « 0 adopté »."
    )
    assert "'sort non publié'" in composant, (
        "Le remplacement du zéro a disparu : une absence redeviendrait un zéro."
    )
