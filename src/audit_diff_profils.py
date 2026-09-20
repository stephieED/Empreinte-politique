#!/usr/bin/env python3
"""
audit_diff_profils.py — Compare la couche publiée `pivot_data/` d'une référence
git à celle du disque, fichier par fichier et champ par champ, pour détecter ce
qu'une régénération a perdu.

**Pourquoi.** La fusion additive de `merge_profile.py` n'est pas un confort :
elle préserve les données d'un run à l'autre quand une collecte échoue. On l'a
constaté le 18/08/2026 — les 283 textes de la XV d'Édouard Philippe ont
survécu à une collecte ratée uniquement grâce à elle.

Un run `--no-merge` (`existing_profiles=overwrite`) abandonne cette mémoire : tout ce que la
collecte du jour ne récupère pas est définitivement perdu, **silencieusement**.
Ce script est le contrôle qui manque avant de committer une telle
régénération.

**Comparaison par fichier et par champ, jamais en agrégat** : un gain global
masquerait des pertes individuelles. C'est précisément ce qui rend le contrôle
utile — la correction de clé de #440 fait mécaniquement grimper le nombre
d'amendements, et cette hausse cacherait n'importe quelle perte de votes ou de
mandats si on ne regardait que le total.

Trois catégories de constats, deux statuts :

  - **listes stables** — une baisse est une alerte **bloquante**. Votes,
    mandats, textes portés, interventions, tags thématiques, cohésion de vote
    d'un groupe n'ont aucune raison de diminuer d'un run à l'autre.
  - **listes signalées** — une baisse est relevée sans bloquer : les
    amendements (la correction de clé de #440 les fait varier des deux côtés,
    × 2,8 à × 7,1 selon la législature) et `sources`, dont l'historique montre
    des variations légitimes (16 → 15, 4 → 3) au gré des sous-collectes.
  - **scalaires** — seule la régression **renseigné → null** bloque. Un
    changement de valeur (A → B) est relevé sans bloquer : voir plus bas.

## Périmètre étendu par #470

Jusqu'à cette issue, le contrôle ne regardait que `pivot_data/profiles` et n'y
comparait que des longueurs de listes. Deux pertes réelles sont passées au
travers, alors qu'il tournait :

  1. **La cohésion de vote du groupe SOC-16 est tombée de 814 à 0** entre
     `25f7bc7` et `a125e9e`, sur la couche publiée. 24 des mandats perdus
     étaient des `mandat_electif`, la catégorie qui détermine si un membre
     était en fonction à la date d'un scrutin
     (`group_profile._member_eligibility_intervals`). Sans mandat électif,
     aucun membre n'est éligible, aucun scrutin n'est comptable, et
     `cohesion_votes` tombe à zéro. Ce n'est pas une fiche incomplète : c'est
     un **dénominateur publié devenu faux** (AGENTS.md §2.7). Même run,
     REN-16 : `mandats_agreges` 1 032 → 646.
  2. **`parti` est passé de renseigné à `null`** sur `jean-luc-melenchon`,
     `edouard-philippe` et `laurent-wauquiez` entre `e4d71cf` et `ffa24ec`,
     et l'UI ne le montrait pas non plus — `pivotAdapter` retombe sur
     `manifestEntry.parti`, issu de `candidats.json`. La donnée publiée était
     fausse, l'affichage restait juste.

Le contrôle couvre donc désormais les cinq répertoires de `pivot_data/` et les
index partagés. Ce qu'il ne couvre toujours pas est énuméré dans
`docs/decisions/perimetre-controle-perte.md`.

## Pourquoi un changement de valeur ne bloque pas

Mesuré sur les 13 transitions committées entre le 16 et le 20/08/2026, sur les
209 profils :

  - **10 régressions `renseigné → null`, dont 10 défauts réels** — les quatre
    `parti` écrasés par la passe roster-driven, les trois `parti` des
    restaurations de #460/#465, deux `identite` perdues, un `groupe`. Aucun
    faux positif. C'est ce qui justifie de bloquer dessus, et AGENTS.md §3 le
    dit déjà du côté de la fusion : « Scalars: new value if populated, else
    keep old (**never regress to null**) ». Une régression vers `null` est donc
    toujours une violation de contrat, jamais un fait mesuré (règle §2.5).
  - **129 changements de valeur, quasi tous légitimes** — normalisations
    (`'REN'` → `'Renaissance'`, `'LREM'` → `'Ensemble pour la République'`),
    accents (`'Edouard Philippe'` → `'Édouard Philippe'`), bascules de source
    (`nosdeputes` ↔ `nossenateurs`, et le `chambre` qui suit), et
    `meta.provenance` qui alterne `candidat_declare` / `roster_groupe` selon
    l'ordre des passes. Bloquer là-dessus interdirait presque tous les commits
    de données.

D'où l'arbitrage, explicite : **faux négatif assumé sur le changement de
valeur, faux positif refusé**. Un changement suspect (Mélenchon passant de
`AN` à `Senat`) est relevé dans le rapport, à charge de relecture humaine.

## Pourquoi une chute d'agrégat ne bloque pas non plus (#649)

Le run `33351244845` du 31/08/2026 a divisé par 5 à 32 le compteur principal de
cinq fiches de groupe (`AN:RN` 1 175 535 → 37 093, `AN:LFI` 2 600 765 →
131 202) et le commit `3c8e1f0c` est passé sans qu'aucun contrôle ne bloque ni
ne signale. La question posée était : faut-il une **quatrième** famille de
constats bloquants, sur l'ordre de grandeur d'un compteur ?

Non, et la raison est une mesure, pas une prudence. Les deux seules chutes
d'ordre de grandeur du corpus se rangent dans le mauvais sens :

  - `a125e9e` — **défaut réel** (#460 / #470) : `AN:LFI-16` × 0,00,
    `AN:SOC-16` × 0,52, `AN:LR-16` × 0,64 ;
  - `3c8e1f0c` — **correction juste** (#643, un amendement cosigné n'est pas N
    amendements) : les cinq fiches entre × 0,03 et × 0,21.

La chute légitime est **plus forte que la chute défectueuse sur chacune des
fiches**. Aucun seuil de ratio ne les sépare : réglé pour attraper `a125e9e`
(× 0,64) il aurait bloqué `3c8e1f0c`, c'est-à-dire le run qui corrigeait le
défaut, et il aurait fallu cocher `allow_declared_losses` — une tolérance de
corpus, qui désarme du même coup les contrôles précis par profil. C'est
l'échange que ce fichier refuse déjà pour les index partagés.

Ce qui change, c'est le **silence** : ces compteurs sont désormais des
scalaires surveillés, donc une chute de × 20 apparaît comme un changement de
valeur dans le rapport, à charge de relecture humaine — et leur disparition ou
leur passage à `null`, lui, bloque. Un compteur à **zéro** n'est pas une
absence de compteur : `_resume_scalaire` rend `0` tel quel et ne teste que
`is None`, comme il le fait pour `False`.

## Dimensionnement

Ce script tourne AVANT le commit : s'il meurt, rien n'est publié. Il s'est
déjà fait tuer par l'OOM killer une fois (#460), et un garde-fou qui meurt est
pire qu'un garde-fou absent — il donne une assurance qu'il ne tient pas.

Deux règles tenues ici :

  - un seul document en mémoire à la fois, jamais le corpus (lecture en flux
    du `git cat-file --batch`, cf. `lire_collection_git`) ;
  - les fichiers `<legislature>.cosignatures.json` ne sont **pas** ouverts :
    à eux seuls ils portent le pic de mémoire (222 Mio pour les 25,7 Mo de
    `15.cosignatures.json`, soit plus que tout le reste du contrôle réuni),
    aucun consommateur ne les lit (AGENTS.md §3), et leur **disparition** —
    le seul cas catastrophique — est détectée gratuitement par la comparaison
    des listings.

Mesuré sur les 209 profils de `3a8455a` (`--ref HEAD`, `/usr/bin/time -v`,
médiane de trois exécutions) : **2,79 s / 133,4 Mio** pour les profils seuls,
**4,74 s / 184,8 Mio** pour les six collections. Sous les 236 Mio actés par
#460, et `--seulement-profils` rend exactement les chiffres d'avant.

Sortie non nulle si un fichier a perdu sur un champ stable, a disparu, ou a vu
un scalaire surveillé régresser vers `null` — utilisable comme garde-fou avant
commit.

Usage :
    python3 src/audit_diff_profils.py --ref origin/main \\
        --profils-dir pivot_data/profiles --pivot-dir pivot_data \\
        --out audit/diff.md
"""

import argparse
import fnmatch
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from profil_brut import CLE_MANIFESTE, CLE_PARTITIONNEE


@dataclass(frozen=True)
class Collection:
    """Un répertoire (ou un fichier) de `pivot_data/` et ce qu'on y surveille.

    `motif_present` désigne les fichiers dont la **disparition** est une perte.
    `motif_exclu` en retire ceux dont le **contenu** n'est pas comparé : un
    fichier présent mais non lu ne coûte que sa ligne de listing.
    """

    nom: str
    sous_chemin: str
    listes_stables: tuple[str, ...] = ()
    listes_signalees: tuple[str, ...] = ()
    #: Listes dont le relevé garde les VALEURS, pas seulement leur nombre
    #: (#823). Un compte ne voit pas un échange : une entrée remplacée par une
    #: autre laisse le total inchangé, et le contrôle ne dit rien. Réservé aux
    #: listes de chaînes courtes et peu nombreuses — 5 911 valeurs distinctes
    #: pour les 53 183 `tags_thematiques` des 1 035 profils publiés, 2,6 Mio de
    #: relevé qui ne quitte jamais la mémoire. Le faire sur `amendements`
    #: coûterait des millions de clés, et c'est pourquoi ce n'est pas le
    #: comportement par défaut.
    listes_nommees: tuple[str, ...] = ()
    scalaires: tuple[str, ...] = ()
    motif_present: str = "*.json"
    #: Motif des fichiers présents mais volontairement non ouverts. `fnmatch`
    #: et non un motif positif : `*` y traverse le point, si bien que
    #: `[0-9]*.json` attraperait aussi `14.cosignatures.json`.
    motif_exclu: str = ""
    #: `True` pour `pivot_data/profiles`, dont l'absence dans la référence est
    #: une erreur d'invocation (`--ref-dir`) et non un constat.
    obligatoire: bool = False

    @property
    def tous_champs(self) -> tuple[str, ...]:
        return self.listes_stables + self.listes_signalees

    def concerne(self, nom_fichier: str) -> bool:
        return fnmatch.fnmatch(nom_fichier, self.motif_present)

    def se_lit(self, nom_fichier: str) -> bool:
        if not self.concerne(nom_fichier):
            return False
        return not (self.motif_exclu
                    and fnmatch.fnmatch(nom_fichier, self.motif_exclu))


#: Combien d'entrées disparues un constat d'échange nomme au plus. Le rapport
#: est lu par un humain qui cherche une cause, pas un inventaire : au-delà, le
#: compte total (`nb_disparues`) dit l'ampleur et les premières disent la
#: nature.
LIMITE_ENTREES_NOMMEES = 20

# --- Profils individuels ----------------------------------------------------
#
# `tags_thematiques` a rejoint les champs stables avec #470 : c'est un champ
# **publié** (AGENTS.md §6), il est passé de 647 à 0 dans le run `a125e9e` que
# #460 documente — et il ne figurait dans aucune des deux catégories. Le
# rapport de #460 le comptait dans ses dégâts sans que le contrôle le regarde.
#
# `dossiers_legislatifs` est conservé bien qu'inerte : mesuré sur les 209
# profils de `3a8455a` et sur les 7 refs de l'historique récent, aucun pivot ne
# porte cette clé — c'est un champ de `raw_data/profiles`, que
# `normalize_profil` verse dans `textes_portes`. Le garder ne coûte rien et
# couvre `--profils-dir raw_data/profiles`.
#
# `chambres` (#493) est signalé et non bloquant. Signalé, parce qu'un champ
# publié qui ne figure dans aucune des deux catégories est exactement la faille
# que #470 a payée sur `tags_thematiques`. Non bloquant, parce que la perte qui
# compte est déjà couverte : `chambre` est un scalaire surveillé, et il vaut
# `chambres[0]` — `chambres` ne peut pas se vider sans que `chambre` régresse
# vers `null`, ce qui bloque déjà. En faire un champ stable ajouterait un
# second verrou sur le même événement. Et la seule baisse réelle possible —
# `--no-merge` recollectant moins de mandats qu'avant — fait d'abord tomber
# `mandats`, qui est un champ **stable** : le blocage est déjà là, sur la cause
# plutôt que sur son reflet.
#
# `sources` est signalé et non bloquant : son historique montre des baisses
# (2 → 1, 3 → 2) qui accompagnent aussi bien une perte réelle qu'une
# sous-collecte non rejouée. Bloquer dessus doublerait l'alerte des champs qui
# la causent vraiment.
COLLECTION_PROFILS = Collection(
    nom="profiles",
    sous_chemin="profiles",
    listes_stables=(
        "votes", "mandats", "textes_portes", "interventions",
        "tags_thematiques", "dossiers_legislatifs",
    ),
    listes_signalees=("amendements", "sources", "chambres"),
    listes_nommees=("tags_thematiques",),
    scalaires=("id", "nom", "chambre", "parti", "groupe", "identite",
               "meta.provenance"),
    motif_present="*.json",
    obligatoire=True,
)

# --- Groupes parlementaires -------------------------------------------------
#
# `cohesion_votes` est LE champ de #470 : un dénominateur publié (AGENTS.md
# §2.7). `membres`, `mandats_agreges` et `tags_thematiques_agreges` en sont les
# entrées amont — les trois sont tombés ensemble sur SOC-16.
#
# `effectif.actuel` est volontairement absent des scalaires : c'est un compte
# de membres **actifs**, qui baisse légitimement quand un élu quitte le groupe
# (observé : REN-16 50 → 77 dans l'autre sens sur le même run). `membres`
# couvre déjà la perte d'enregistrement.
#
# `meta.couverture_roster.roster_total` en revanche est surveillé : c'est le
# dénominateur réel du groupe, issu d'un fetch réseau, et le seul champ dont la
# disparition rendrait un ratio publié incalculable sans que rien ne le dise.
#
# ## `amendements_agreges` (#649)
#
# Le raisonnement ci-dessus ne disait rien des AGRÉGATS — les chiffres que la
# fiche affiche en gros. Ils n'avaient pas été écartés : ils n'avaient pas été
# vus. Ce qui est surveillé ici, et ce qui ne l'est pas, est mesuré sur les 23
# transitions committées de `pivot_data/groupes` entre le 17/08 et le
# 31/08/2026 :
#
#   - `amendements_agreges` (présence du bloc), `nb_amendements`,
#     `taux_adoption` et `par_type_deposant.depute.nb_amendements` sont des
#     **scalaires surveillés** : seule la régression renseigné → `null` bloque.
#     La mesure qui justifie l'inclusion est le run `a125e9e` — celui de #460 /
#     #470 : `AN:LFI-16` y perd ses 11 561 amendements (→ 0) et son
#     `taux_adoption` passe de `0.0476` à `null`, pendant que `membres` (3),
#     `cohesion_votes` (1 996) et `mandats_agreges` (50) restent identiques au
#     bit près. Aucune liste stable ne bouge : le contrôle se taisait sur cette
#     fiche. La régression vers `null` de `taux_adoption`, elle, tombe
#     exactement dans la catégorie bloquante qui existe déjà.
#   - `par_type_deposant` est une **liste stable** : `len()` y rend le nombre de
#     types de déposant publiés. L'ensemble est fermé
#     (`schema_groupe.AMENDEMENTS_TYPES_DEPOSANT`, 4 valeurs) et
#     `validate_profil_groupe` ne vérifie que son type, jamais ses clés — une
#     ventilation qui perd une catégorie ne serait vue par rien d'autre.
#   - `nb_adoptes`, `nb_rejetes`, `nb_irrecevables`, `nb_retires_ou_tombes`,
#     `nb_sort_non_renseigne`, `nb_sort_non_reconnu`, `nb_sans_identifiant`
#     sont **écartés** : ils sortent tous de la même fabrique
#     (`schema_groupe.make_empty_amendements_stats`) que `nb_amendements`, donc
#     ils ne peuvent pas disparaître seuls. Les surveiller n'ajouterait aucun
#     événement, seulement des lignes de rapport.
#   - `signatures` (#643) est **écarté** : ce bloc n'a qu'un seul état commité
#     au 31/08/2026, celui de son apparition. Surveiller un champ dont la seule
#     transition observée est sa propre naissance serait une intuition, pas une
#     mesure.
#   - `effectif.min_historique` / `max_historique` restent écartés pour la
#     raison déjà donnée sur `effectif.actuel`.
COLLECTION_GROUPES = Collection(
    nom="groupes",
    sous_chemin="groupes",
    listes_stables=("membres", "cohesion_votes", "mandats_agreges",
                    "tags_thematiques_agreges", "historique_noms",
                    "amendements_agreges.par_type_deposant"),
    listes_signalees=("sources",),
    # #823 — c'est ICI que l'échange s'est vu, sur `REN-16` et `EPR-17`, alors
    # qu'il naissait à l'étage profil : une union expose ce que ses membres
    # masquent. Nommer des deux côtés dit lequel des deux étages a bougé.
    listes_nommees=("tags_thematiques_agreges",),
    scalaires=("groupe_id", "groupe_sigle", "groupe_nom", "chambre",
               "legislature", "periode.debut",
               "meta.couverture_roster.roster_total",
               "amendements_agreges",
               "amendements_agreges.nb_amendements",
               "amendements_agreges.taux_adoption",
               "amendements_agreges.par_type_deposant.depute.nb_amendements"),
)

# Les fiches de LIGNÉE (#836). Une collection à part de `groupes`, et c'est le
# point de la décision : le contrôle de perte raisonne par collection, et deux
# types de documents dans un même répertoire est le défaut que #630 a payé.
#
# `membres` et `cohesion_votes` y sont des UNIONS, donc stables au même titre
# que sur la fiche de groupe — une union ne perd un élément que si aucun maillon
# ne le porte plus. `maillons` est stable pour une raison plus forte : sa
# longueur est le nombre de fiches de la lignée, et la voir baisser est le seul
# signal qu'une déclaration a été retirée sans que personne ne le veuille.
COLLECTION_LIGNEES = Collection(
    nom="lignees",
    sous_chemin="lignees",
    listes_stables=("maillons", "membres", "cohesion_votes", "mandats_agreges",
                    "tags_thematiques_agreges",
                    "amendements_agreges.par_type_deposant"),
    listes_signalees=("sources",),
    listes_nommees=("tags_thematiques_agreges",),
    scalaires=("lignee_id", "lignee_nom", "chambre", "periode.debut",
               "effectif.cumul_historique",
               "amendements_agreges.nb_amendements",
               "amendements_agreges.taux_adoption"),
)

COLLECTION_PARTIS = Collection(
    nom="partis",
    sous_chemin="partis",
    listes_stables=("candidats", "tags_thematiques_agreges"),
    listes_signalees=("sources",),
    listes_nommees=("tags_thematiques_agreges",),
    scalaires=("parti_id", "parti_nom"),
)

# `premier_ministre` est un bloc nullable : sa perte a été observée dans
# l'autre sens (null → renseigné, run `d96799c`), ce qui prouve qu'il peut
# aussi repartir.
#
# ## `comptages` (#649)
#
# Même angle mort que sur les groupes, et une porte laissée ouverte en amont :
# `comptages` figure bien dans `REQUIRED_TOP_LEVEL_KEYS`, mais
# `validate_profil_gouvernement` accepte `comptages: null` sans un mot — la clé
# est là, le bloc est vide, et les neuf compteurs publiés ont disparu. C'est
# `comptages` **présent mais nul** qui est surveillé ici, avec
# `comptages.par_statut` pour la même raison d'un cran plus bas.
#
# `adopte_49_3` et `rejete_49_3` sont surveillés nommément : le 49.3 est le
# fait procédural que la ligne éditoriale publie (AGENTS.md §2 règle 4, §6), et
# `BORNE` en porte 6. Un bloc disparu y publierait « aucun 49.3 » là où la
# mesure disait 6, ce qu'interdit §2 règle 5.
#
# Les **sept autres statuts** sont écartés, et leur VALEUR aussi, pour deux
# raisons mesurées sur les 27 transitions committées de
# `pivot_data/gouvernements` (14/08 → 28/08/2026) :
#
#   - aucune clé de `par_statut` n'y a jamais disparu, et elle ne le pourrait
#     pas en silence : `validate_profil_gouvernement` compare les clés à
#     `KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL` et fait échouer la porte de qualité
#     sur une clé manquante. Un second verrou sur le même événement n'ajoute
#     rien — c'est l'argument qui écarte déjà `chambres` côté profils ;
#   - une baisse par statut est la contrepartie NORMALE d'une requalification :
#     le run `720110d2` a déplacé 27 textes de `BORNE` vers `adopte_cmp` et 19
#     vers `promulgue` en une passe. La perte réelle serait que `textes`
#     rétrécisse, et `textes` est déjà une liste stable bloquante.
COLLECTION_GOUVERNEMENTS = Collection(
    nom="gouvernements",
    sous_chemin="gouvernements",
    listes_stables=("membres", "textes"),
    listes_signalees=("sources",),
    scalaires=("gouvernement_id", "nom", "premier_ministre", "periode.debut",
               "comptages", "comptages.par_statut",
               "comptages.par_statut.adopte_49_3",
               "comptages.par_statut.rejete_49_3"),
)

# --- Index partagés (#431, #432) --------------------------------------------
#
# `scrutins` et `amendements` sont des CONTENEURS d'entrées distinctes : une
# liste pour l'un, un dict indexé par `amendement_id` pour l'autre. `len()`
# rend le nombre d'entrées distinctes dans les deux cas.
#
# Baisse SIGNALÉE et non bloquante — l'arbitrage est explicite. Une baisse y
# serait grave (AGENTS.md : « an uncommitted index leaves every mapping
# pointing at nothing, silently ») mais elle est aussi le résultat attendu
# d'une correction de clé, ce qu'ont fait #431 et #432. Or ces compteurs sont
# des totaux de corpus, pas des mesures par fiche : les bloquer forcerait
# l'opérateur à relancer avec `--tolerer-pertes`, qui désarme du même coup les
# contrôles **précis** par profil et par groupe. Bloquer sur le compteur le
# plus grossier pour faire taire les plus fins serait le pire des échanges.
#
# La disparition d'un fichier d'index, elle, reste bloquante : elle n'a aucune
# explication légitime et laisse chaque mapping pointer dans le vide.
COLLECTION_INDEX_SCRUTINS = Collection(
    nom="index scrutins",
    sous_chemin="",
    listes_signalees=("scrutins",),
    scalaires=("schema_version", "licence_donnees"),
    motif_present="scrutins.json",
)

COLLECTION_INDEX_AMENDEMENTS = Collection(
    nom="index amendements",
    sous_chemin="amendements",
    listes_signalees=("amendements",),
    scalaires=("schema_version", "legislature", "licence_donnees"),
    motif_present="*.json",
    # Les `*.cosignatures.json` sont listés mais jamais ouverts : 222 Mio de
    # RSS pour le seul `15.cosignatures.json`, aucun consommateur (AGENTS.md
    # §3), et leur disparition est détectée par le listing.
    motif_exclu="*.cosignatures.json",
)

COLLECTIONS_AGREGATS: tuple[Collection, ...] = (
    COLLECTION_GROUPES,
    COLLECTION_LIGNEES,
    COLLECTION_PARTIS,
    COLLECTION_GOUVERNEMENTS,
    COLLECTION_INDEX_SCRUTINS,
    COLLECTION_INDEX_AMENDEMENTS,
)

# Compatibilité : ces noms désignent le périmètre historique, celui des
# profils. Ils restent le vocabulaire du rapport et des tests.
CHAMPS_STABLES: tuple[str, ...] = COLLECTION_PROFILS.listes_stables
CHAMPS_HAUSSE_ATTENDUE: tuple[str, ...] = COLLECTION_PROFILS.listes_signalees
TOUS_CHAMPS: tuple[str, ...] = COLLECTION_PROFILS.tous_champs


# ---------------------------------------------------------------------------
# Relevé d'un document
# ---------------------------------------------------------------------------

def _chemin_pointe(doc: Any, chemin: str) -> Any:
    """Valeur d'un chemin pointé (`meta.provenance`), `None` si la route casse."""
    courant = doc
    for segment in chemin.split("."):
        if not isinstance(courant, dict):
            return None
        courant = courant.get(segment)
    return courant


def _resume_scalaire(valeur: Any) -> Any:
    """Réduit un scalaire à une valeur comparable et sérialisable en JSON.

    `None` signifie « non renseigné », et c'est la seule chose sur laquelle le
    contrôle bloque. Un conteneur vide (`{}`, `[]`) ou une chaîne blanche
    valent `None` : la convention du dépôt est que manquant s'écrit `null`, et
    un `""` qui remplace un nom n'est pas moins une perte (règle §2.5).

    `0` et `False` sont en revanche des valeurs **renseignées** — d'où le test
    `is None` partout, jamais un test de vérité.
    """
    if valeur is None:
        return None
    if isinstance(valeur, str):
        return valeur if valeur.strip() else None
    if isinstance(valeur, bool) or isinstance(valeur, (int, float)):
        return valeur
    if isinstance(valeur, (dict, list, tuple)):
        # Le contenu d'un bloc (`identite`, `premier_ministre`) n'est pas
        # comparé : seule sa présence l'est. Comparer les blocs entiers ferait
        # du bruit sur chaque enrichissement.
        return "<renseigné>" if len(valeur) else None
    return str(valeur)


def _identites(valeur: Any) -> Optional[set[str]]:
    """Les entrées d'une liste, nommées — ou `None` si elles ne se nomment pas.

    Deux formes dans le corpus, et une seule règle : l'entrée est son propre
    nom quand c'est une chaîne (`tags_thematiques` d'un profil), et c'est sa
    clé `tag` quand c'est un objet (`tags_thematiques_agreges` d'une fiche de
    groupe, qui porte aussi `nb_membres_porteurs` et `poids_relatif`).

    `None` — et non un ensemble vide — quand la liste n'est pas de cette forme.
    Un ensemble vide dirait « cette liste ne porte rien », ce qui ferait passer
    une lecture impossible pour un fait sur les données (§2 règle 5).
    """
    if not isinstance(valeur, list):
        return None
    noms: set[str] = set()
    for entree in valeur:
        if isinstance(entree, str):
            noms.add(entree)
        elif isinstance(entree, dict) and isinstance(entree.get("tag"), str):
            noms.add(entree["tag"])
        else:
            return None
    return noms


def relever(doc: Any, collection: Collection) -> dict[str, Any]:
    """Relevé d'un document : longueurs de conteneurs + scalaires surveillés.

    Un champ absent vaut 0 — indistinct d'une liste vide, ce qui est le
    comportement voulu : dans les deux cas le document ne porte aucune entrée.

    `len()` et non `len(list)` : les index partagés indexent leurs entrées dans
    un **dict** (`amendements` par `amendement_id`), les profils dans une
    liste. Le nombre d'entrées distinctes est `len()` des deux côtés.

    Un champ de liste peut être un **chemin pointé**
    (`amendements_agreges.par_type_deposant`, #649), comme un scalaire l'est
    depuis #470 : un nom simple est un chemin d'un seul segment, et une route
    qui casse rend `None`, donc 0 — exactement ce que rendait `doc.get()`.
    """
    if not isinstance(doc, dict):
        raise ValueError("document JSON qui n'est pas un objet")

    # #580 — un profil brut partitionné ne porte plus `amendements` dans son
    # socle : la liste vit en tranches sous `<slug>/<legislature>.json`. Sans
    # ceci, ce contrôle lirait 0 amendement des deux côtés d'un diff et
    # rapporterait une chute de plusieurs millions d'entrées à la migration.
    #
    # Le compte est pris au manifeste, et c'est ici — et seulement ici —
    # légitime : cet audit compare deux DÉCLARATIONS, une par référence, et il
    # lit les deux côtés de la même façon, y compris depuis un blob git où les
    # tranches ne sont pas atteignables sans un second parcours de l'arbre. Un
    # manifeste qui mentirait ne survivrait pas jusqu'ici : `recomposer()`
    # refuse un profil dont les tranches ne rendent pas le compte annoncé, et
    # `audit_collecte_vs_publie` mesure ce compte, tranche par tranche, avant
    # le commit.
    partition = doc.get(CLE_MANIFESTE)
    total_partitionne = (
        partition.get("total") if isinstance(partition, dict) else None
    )

    listes: dict[str, int] = {}
    for champ in collection.tous_champs:
        if champ == CLE_PARTITIONNEE and isinstance(total_partitionne, int):
            listes[champ] = total_partitionne
            continue
        valeur = _chemin_pointe(doc, champ)
        listes[champ] = len(valeur) if isinstance(valeur, (list, dict)) else 0
    scalaires = {
        chemin: _resume_scalaire(_chemin_pointe(doc, chemin))
        for chemin in collection.scalaires
    }
    # #823 — les valeurs, pour les seules listes qui les déclarent.
    valeurs: dict[str, list[str]] = {}
    for champ in collection.listes_nommees:
        noms = _identites(_chemin_pointe(doc, champ))
        if noms is not None:
            valeurs[champ] = sorted(noms)
    releve: dict[str, Any] = {"listes": listes, "scalaires": scalaires, "lu": True}
    if valeurs:
        releve["valeurs"] = valeurs
    return releve


def _releve_non_lu() -> dict[str, Any]:
    """Fichier dont on ne surveille que la présence (`*.cosignatures.json`)."""
    return {"listes": {}, "scalaires": {}, "lu": False}


# ---------------------------------------------------------------------------
# Lecture
# ---------------------------------------------------------------------------

def lire_collection_git(
    ref: str, repertoire: str, collection: Collection
) -> Optional[dict[str, dict[str, Any]]]:
    """Relève chaque fichier d'une collection dans une référence git.

    `git cat-file --batch` plutôt qu'un `git show` par fichier : sur 752
    profils de ~10 Mo, lancer autant de processus prend des minutes. Ici un
    seul processus reçoit la liste des chemins et renvoie les blobs à la
    suite.

    Rend `None` si le chemin n'existe pas dans la référence et que la
    collection n'est pas obligatoire — un répertoire qui n'existait pas encore
    n'est pas un constat de perte, c'est une absence de point de comparaison.
    """
    listing = subprocess.run(
        ["git", "ls-tree", "--name-only", f"{ref}:{repertoire}".rstrip(":")],
        capture_output=True, text=True,
    )
    if listing.returncode != 0:
        if not collection.obligatoire:
            return None
        # Deux causes très différentes derrière le même échec de `ls-tree`, et
        # le conseil n'est pas le même. Les confondre coûte cher au pire
        # moment : après un bornage d'historique, ce contrôle est justement
        # celui qu'on vient vérifier, et on chercherait un problème de chemin
        # là où le commit entier a disparu (#569).
        if subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
            capture_output=True, text=True,
        ).returncode != 0:
            raise SystemExit(
                f"[!] Référence git introuvable : {ref}\n"
                "    Ce n'est pas un problème de chemin : le commit lui-même est "
                "absent de ce dépôt.\n"
                "    Causes possibles — une faute de frappe, une branche "
                "supprimée, un clone superficiel, ou un bornage d'historique\n"
                "    (docs/decisions/fenetre-recalibrage-551.md) qui a "
                "retiré un commit antérieur à la coupure. Dans ce dernier cas\n"
                "    l'ancien historique est archivé sur Software Heritage ; il "
                "ne sera pas retrouvé ici."
            )
        raise SystemExit(
            f"[!] Chemin introuvable dans la référence git : {ref}:{repertoire}\n"
            "    La référence existe ; c'est le chemin qui n'y est pas. "
            "`--ref-dir` vaut par défaut `--profils-dir`. Si les profils "
            "régénérés sont hors du dépôt (répertoire de mesure, worktree...), "
            "préciser le chemin côté référence :\n"
            "      --profils-dir /chemin/hors/depot --ref-dir pivot_data/profiles"
        )
    fichiers = [f for f in listing.stdout.split() if collection.concerne(f)]
    if not fichiers:
        return {}

    a_lire = [f for f in fichiers if collection.se_lit(f)]
    resultats: dict[str, dict[str, Any]] = {
        f: _releve_non_lu() for f in fichiers if not collection.se_lit(f)
    }
    if not a_lire:
        return resultats

    # Lecture EN FLUX du `--batch`, blob par blob. `capture_output=True`
    # bufferisait la totalité des profils avant d'en compter la première
    # entrée : 3,2 Gio de RSS sur les 209 profils du 19/08/2026, et un process
    # tué par l'OOM killer. À 752 profils ce serait ~11 Go, donc un échec
    # certain en CI — pour un script dont tout l'intérêt est de tourner AVANT
    # le commit (#460).
    #
    # Seuls les relevés sont retenus, jamais les documents : la mémoire ne
    # dépend plus que du plus gros blob (~26 Mo), pas du corpus. Même
    # correction que sur l'index des scrutins (#432) et sur celui des
    # amendements (#431) — c'est le troisième outil de ce dépôt à buter là-
    # dessus. Les `*.cosignatures.json` ne sont même pas demandés au `--batch`
    # (#470) : leur présence se lit dans le listing ci-dessus.
    prefixe = f"{ref}:{repertoire}/" if repertoire else f"{ref}:"
    proc = subprocess.Popen(
        ["git", "cat-file", "--batch"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
    )
    assert proc.stdin is not None and proc.stdout is not None

    try:
        for fichier in a_lire:
            proc.stdin.write(f"{prefixe}{fichier}\n".encode())
            proc.stdin.flush()
            entete = proc.stdout.readline().split()
            if len(entete) < 3:        # « <oid> missing »
                continue
            taille = int(entete[2])
            contenu = proc.stdout.read(taille)
            proc.stdout.read(1)        # saut de ligne final
            try:
                resultats[fichier] = relever(json.loads(contenu), collection)
            except ValueError:
                continue
            finally:
                del contenu
    finally:
        proc.stdin.close()
        proc.stdout.read()
        proc.wait()
    return resultats


def lire_collection_disque(
    repertoire: Path, collection: Collection
) -> Optional[dict[str, dict[str, Any]]]:
    """Relève chaque fichier d'une collection sur le disque.

    Rend `None` si le répertoire n'existe pas et que la collection n'est pas
    obligatoire — symétrique de `lire_collection_git`.
    """
    if not repertoire.is_dir():
        return None if not collection.obligatoire else {}
    resultats: dict[str, dict[str, Any]] = {}
    for chemin in sorted(repertoire.iterdir()):
        if not chemin.is_file() or not collection.concerne(chemin.name):
            continue
        if not collection.se_lit(chemin.name):
            resultats[chemin.name] = _releve_non_lu()
            continue
        try:
            resultats[chemin.name] = relever(
                json.loads(chemin.read_bytes()), collection)
        except (OSError, ValueError):
            continue
    return resultats


def lire_profils_git(ref: str, repertoire: str) -> dict[str, dict[str, Any]]:
    """Relevé des profils d'une référence git (périmètre historique)."""
    return lire_collection_git(ref, repertoire, COLLECTION_PROFILS) or {}


def lire_profils_disque(repertoire: Path) -> dict[str, dict[str, Any]]:
    """Relevé des profils sur le disque (périmètre historique)."""
    return lire_collection_disque(repertoire, COLLECTION_PROFILS) or {}


# ---------------------------------------------------------------------------
# Comparaison
# ---------------------------------------------------------------------------

def _listes(releve: dict[str, Any], champ: str) -> int:
    return int(releve.get("listes", {}).get(champ, 0))


def comparer(
    avant: dict[str, dict[str, Any]],
    apres: dict[str, dict[str, Any]],
    collection: Collection = COLLECTION_PROFILS,
) -> dict[str, Any]:
    """Compare deux relevés d'une même collection. Fonction pure.

    Trois familles de constats bloquants :
      - un fichier présent avant et absent après ;
      - une baisse sur une liste stable ;
      - un scalaire surveillé passé de renseigné à `null`.

    Et deux familles non bloquantes, relevées dans le rapport : les baisses sur
    les listes signalées, et les changements de valeur d'un scalaire.
    """
    pertes: list[dict[str, Any]] = []
    gains: list[dict[str, Any]] = []
    echanges: list[dict[str, Any]] = []
    pertes_scalaires: list[dict[str, Any]] = []
    evolutions_scalaires: list[dict[str, Any]] = []

    for fichier in sorted(set(avant) | set(apres)):
        a, b = avant.get(fichier), apres.get(fichier)
        if a is None:
            gains.append({"fichier": fichier, "champ": "(fichier entier)",
                          "avant": 0, "apres": sum(b.get("listes", {}).values()),
                          "stable": False})
            continue
        if b is None:
            # Un fichier disparu est une perte, y compris quand son contenu
            # n'était pas lu (`*.cosignatures.json`) : c'est justement le cas
            # catastrophique que le listing seul suffit à voir.
            pertes.append({"fichier": fichier, "champ": "(fichier entier)",
                           "avant": sum(a.get("listes", {}).values()) or 1,
                           "apres": 0, "stable": True})
            continue
        # #823 — CE QUE LE COMPTE NE VOIT PAS. Une entrée remplacée par une
        # autre laisse le total inchangé : `tags_thematiques` est passé de
        # 43 811 à 53 581 sur les 953 profils du run 34454305520 — aucune perte
        # au compte — pendant que `REN-16` perdait une étiquette que plus aucun
        # membre ne portait. Une union ne peut perdre un élément que si aucun
        # de ses membres ne le porte plus ; l'échange était donc à l'étage
        # profil, invisible, et ne se voyait qu'à l'étage groupe, où il ne
        # naissait pas. Ici on le nomme, des deux côtés.
        for champ in collection.listes_nommees:
            avant_noms = a.get("valeurs", {}).get(champ)
            apres_noms = b.get("valeurs", {}).get(champ)
            if avant_noms is None or apres_noms is None:
                continue
            disparues = sorted(set(avant_noms) - set(apres_noms))
            if disparues:
                echanges.append({
                    "fichier": fichier, "champ": champ,
                    "avant": len(avant_noms), "apres": len(apres_noms),
                    "disparues": disparues[:LIMITE_ENTREES_NOMMEES],
                    "nb_disparues": len(disparues),
                })
        for champ in collection.tous_champs:
            av, ap = _listes(a, champ), _listes(b, champ)
            if ap < av:
                pertes.append({"fichier": fichier, "champ": champ,
                               "avant": av, "apres": ap,
                               "stable": champ in collection.listes_stables})
            elif ap > av:
                gains.append({"fichier": fichier, "champ": champ,
                              "avant": av, "apres": ap,
                              "stable": champ in collection.listes_stables})
        for chemin in collection.scalaires:
            va = a.get("scalaires", {}).get(chemin)
            vb = b.get("scalaires", {}).get(chemin)
            if va == vb:
                continue
            if va is not None and vb is None:
                pertes_scalaires.append(
                    {"fichier": fichier, "champ": chemin, "avant": va, "apres": None})
            elif va is not None:
                evolutions_scalaires.append(
                    {"fichier": fichier, "champ": chemin, "avant": va, "apres": vb})
            # va is None : le scalaire apparaît. C'est un gain, pas un constat.

    pertes_stables = [p for p in pertes if p["stable"]]
    return {
        "collection": collection.nom,
        # #823 — NON BLOQUANT, et c'est délibéré. `tags_thematiques` est un
        # champ DÉRIVÉ, recalculé à chaque run et jamais fusionné (§4) : une
        # recomputation qui remplace une étiquette par d'autres est son
        # fonctionnement normal, pas un incident. Bloquer dessus ferait échouer
        # des runs légitimes. Ce que ce constat apporte, c'est de quoi
        # EXPLIQUER une perte de compte sans rejouer le run — ce qui manquait
        # au 34454305520, dont la sortie n'existe plus.
        "echanges": echanges,
        "nb_avant": len(avant),
        "nb_apres": len(apres),
        "pertes": pertes,
        "gains": gains,
        "pertes_sur_champs_stables": pertes_stables,
        "pertes_scalaires": pertes_scalaires,
        "evolutions_scalaires": evolutions_scalaires,
        "bloquant": bool(pertes_stables) or bool(pertes_scalaires),
        "totaux_avant": {c: sum(_listes(v, c) for v in avant.values())
                         for c in collection.tous_champs},
        "totaux_apres": {c: sum(_listes(v, c) for v in apres.values())
                         for c in collection.tous_champs},
    }


def comparer_tout(
    releves: list[tuple[Collection, Optional[dict], Optional[dict]]]
) -> dict[str, Any]:
    """Assemble les rapports de chaque collection en un verdict unique."""
    rapports: list[dict[str, Any]] = []
    ignorees: list[str] = []
    for collection, avant, apres in releves:
        if avant is None and apres is None:
            ignorees.append(collection.nom)
            continue
        rapport = comparer(avant or {}, apres or {}, collection)
        rapport["absente_avant"] = avant is None
        rapport["absente_apres"] = apres is None
        rapports.append(rapport)
    return {
        "collections": rapports,
        "collections_ignorees": ignorees,
        "bloquant": any(r["bloquant"] for r in rapports),
        "nb_pertes_bloquantes": sum(
            len(r["pertes_sur_champs_stables"]) + len(r["pertes_scalaires"])
            for r in rapports
        ),
    }


# ---------------------------------------------------------------------------
# Rapport
# ---------------------------------------------------------------------------

_PLAFOND = 40


def _tableau(lignes: list[dict[str, Any]], entete: str) -> list[str]:
    out = [entete, "| --- | --- | --- | --- |"]
    for ligne in lignes[:_PLAFOND]:
        out.append(f"| `{ligne['fichier']}` | `{ligne['champ']}` | "
                   f"{ligne['avant']} | {ligne['apres']} |")
    if len(lignes) > _PLAFOND:
        out.append(f"| … | | | {len(lignes) - _PLAFOND} de plus |")
    out.append("")
    return out


def _section_collection(rapport: dict[str, Any]) -> list[str]:
    nom = rapport["collection"]
    lignes = [f"## `{nom}`", ""]
    if rapport["absente_avant"]:
        lignes += ["Absente de la référence : tout y est un gain.", ""]
    if rapport["absente_apres"]:
        lignes += ["**Absente du disque alors qu'elle existait dans la "
                   "référence.** Perte totale.", ""]
    lignes += [f"{rapport['nb_avant']} fichier(s) avant, "
               f"{rapport['nb_apres']} après.", ""]

    if rapport["totaux_avant"]:
        lignes += ["| Champ | Avant | Après | Écart |", "| --- | --- | --- | --- |"]
        for champ, avant in rapport["totaux_avant"].items():
            apres = rapport["totaux_apres"][champ]
            lignes.append(f"| `{champ}` | {avant} | {apres} | {apres - avant:+} |")
        lignes.append("")

    pertes_stables = rapport["pertes_sur_champs_stables"]
    if pertes_stables:
        lignes += [f"**{len(pertes_stables)} perte(s) sur une liste stable** — "
                   "une baisse n'y a pas d'explication attendue.", ""]
        lignes += _tableau(pertes_stables,
                           "| Fichier | Champ | Avant | Après |")
    pertes_scalaires = rapport["pertes_scalaires"]
    if pertes_scalaires:
        lignes += [f"**{len(pertes_scalaires)} scalaire(s) passé(s) de renseigné "
                   "à `null`** — la fusion ne régresse jamais vers `null` "
                   "(AGENTS.md §3) : c'est une violation de contrat, pas un "
                   "fait mesuré.", ""]
        lignes += _tableau(pertes_scalaires,
                           "| Fichier | Champ | Avant | Après |")
    if not pertes_stables and not pertes_scalaires:
        lignes += ["Aucune perte bloquante.", ""]

    # #823 — les entrées disparues, nommées. Placé AVANT les baisses signalées
    # parce que c'est la section qui explique les autres : une perte de compte
    # sur une union se lit ici, à l'étage où elle est née.
    echanges = rapport.get("echanges") or []
    if echanges:
        total = sum(e["nb_disparues"] for e in echanges)
        a_compte_egal = [e for e in echanges if e["apres"] >= e["avant"]]
        lignes += [
            f"<details><summary>{total} entrée(s) disparue(s) sur "
            f"{len(echanges)} fichier(s), nommée(s) — non bloquant</summary>", "",
            "Une entrée remplacée par une autre laisse le compte inchangé : "
            "sans ce relevé, l'échange est invisible et une baisse d'union "
            "reste inexplicable sans rejouer le run (#823).", "",
        ]
        if a_compte_egal:
            lignes += [
                f"**{len(a_compte_egal)} de ces fichiers n'ont perdu aucun "
                "compte** — leur liste a été échangée, pas réduite. Aucun "
                "autre contrôle ne les voit.", "",
            ]
        lignes += ["| Fichier | Champ | Avant | Après | Disparues |",
                   "| --- | --- | --- | --- | --- |"]
        for e in echanges[:_PLAFOND]:
            noms = ", ".join(f"`{d}`" for d in e["disparues"])
            if e["nb_disparues"] > len(e["disparues"]):
                noms += f" … (+{e['nb_disparues'] - len(e['disparues'])})"
            lignes.append(f"| `{e['fichier']}` | `{e['champ']}` | {e['avant']} | "
                          f"{e['apres']} | {noms} |")
        if len(echanges) > _PLAFOND:
            lignes.append(f"| … | | | | {len(echanges) - _PLAFOND} de plus |")
        lignes += ["", "</details>", ""]

    signalees = [p for p in rapport["pertes"] if not p["stable"]]
    if signalees:
        lignes += [f"<details><summary>{len(signalees)} baisse(s) signalée(s), "
                   "non bloquante(s)</summary>", ""]
        lignes += _tableau(signalees, "| Fichier | Champ | Avant | Après |")
        lignes += ["</details>", ""]
    evolutions = rapport["evolutions_scalaires"]
    if evolutions:
        lignes += [f"<details><summary>{len(evolutions)} changement(s) de valeur "
                   "d'un scalaire, non bloquant(s)</summary>", "",
                   "Normalisations, accents et bascules de source sont "
                   "légitimes et majoritaires ; un changement de `chambre` ou "
                   "d'`id` mérite un regard.", ""]
        lignes += _tableau(evolutions, "| Fichier | Champ | Avant | Après |")
        lignes += ["</details>", ""]
    lignes += [f"{len(rapport['gains'])} augmentation(s) relevée(s).", ""]
    return lignes


def generate_markdown_report(rapport: dict[str, Any], ref: str) -> str:
    """Rapport Markdown. Accepte un rapport de collection ou le rapport global."""
    if "collections" not in rapport:      # rapport d'une seule collection
        rapport = {"collections": [dict(rapport, absente_avant=False,
                                        absente_apres=False)],
                   "collections_ignorees": [],
                   "bloquant": rapport["bloquant"],
                   "nb_pertes_bloquantes": (
                       len(rapport["pertes_sur_champs_stables"])
                       + len(rapport["pertes_scalaires"]))}

    lignes = [
        "# Diff de `pivot_data/` avant / après régénération",
        "",
        f"Référence comparée : `{ref}`.",
        "",
        "> Les totaux ne suffisent pas : une hausse globale des amendements "
        "masquerait des pertes individuelles. Le verdict porte sur le détail "
        "de chaque fichier.",
        "",
    ]
    if rapport["bloquant"]:
        lignes += [f"**{rapport['nb_pertes_bloquantes']} constat(s) bloquant(s)** "
                   "— à élucider avant de committer.", ""]
    else:
        lignes += ["**Aucune perte bloquante**, sur aucune des collections "
                   "comparées.", ""]
    if rapport["collections_ignorees"]:
        lignes += ["Collections absentes des deux côtés, donc non comparées : "
                   + ", ".join(f"`{n}`" for n in rapport["collections_ignorees"])
                   + ".", ""]
    for sous in rapport["collections"]:
        lignes += _section_collection(sous)
    lignes += [
        "## Hors périmètre de ce contrôle",
        "",
        "- le **contenu** d'un scalaire de type bloc (`identite`, "
        "`premier_ministre`) : seule sa présence est comparée ;",
        "- les `*.cosignatures.json`, dont seule la présence est vérifiée "
        "(222 Mio de RSS pour les ouvrir, aucun consommateur) ;",
        "- l'**intégrité référentielle** entre un `votes[].scrutin_id` et "
        "`scrutins.json` : un mapping peut pointer dans le vide sans qu'aucun "
        "compteur ne bouge. Couverte depuis #485 par un contrôle distinct, "
        "`src/audit_integrite_referentielle.py`, qui tourne juste après "
        "celui-ci — une invariance dans un état donné n'est pas une variation "
        "dans le temps, et sa tolérance est cloisonnée de celle-ci ;",
        "- la **valeur** des entrées d'une liste : seule leur cardinalité est "
        "comparée. `cohesion_votes[].membres_eligibles` en relève — il a bougé "
        "de 4,8 à 30,9 en moyenne sur `AN:SOC` au run `3c8e1f0c` sans qu'aucun "
        "compteur de fiche ne le montre (#649) ;",
        "- l'**ordre de grandeur** d'un compteur d'agrégat : une chute y est "
        "relevée comme un changement de valeur, jamais bloquée — aucun seuil "
        "de ratio ne sépare la chute défectueuse de `a125e9e` (× 0,52 à × 0,00) "
        "de la chute juste de `3c8e1f0c` (× 0,21 à × 0,03), la seconde étant "
        "la plus forte (#649).",
        "",
    ]
    return "\n".join(lignes)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--ref", default="origin/main", metavar="REF",
                        help="Référence git servant d'avant (défaut : origin/main).")
    parser.add_argument("--profils-dir", default="pivot_data/profiles", metavar="REP",
                        help="Répertoire des profils régénérés (défaut : pivot_data/profiles).")
    parser.add_argument("--ref-dir", default=None, metavar="REP",
                        help="Répertoire des profils côté référence, si différent de --profils-dir.")
    parser.add_argument("--pivot-dir", default="pivot_data", metavar="REP",
                        help="Racine des agrégats et index (groupes, partis, "
                             "gouvernements, scrutins.json, amendements/). "
                             "Défaut : pivot_data.")
    parser.add_argument("--ref-pivot-dir", default=None, metavar="REP",
                        help="Racine des agrégats côté référence, si différente de --pivot-dir.")
    parser.add_argument("--seulement-profils", action="store_true",
                        help="Restreindre au périmètre d'avant #470 : les "
                             "profils seuls, sans les agrégats ni les index.")
    parser.add_argument("--out", metavar="FICHIER", help="Rapport Markdown.")
    parser.add_argument("--out-json", metavar="FICHIER", help="Rapport JSON.")
    parser.add_argument(
        "--tolerer-pertes", action="store_true",
        help="Ne pas sortir en erreur en cas de perte bloquante. "
             "À n'utiliser qu'après avoir élucidé chaque perte.",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    ref_dir = args.ref_dir or args.profils_dir
    ref_pivot = args.ref_pivot_dir or args.pivot_dir

    releves: list[tuple[Collection, Optional[dict], Optional[dict]]] = []

    print(f"→ {COLLECTION_PROFILS.nom} : {args.ref}:{ref_dir} ↔ {args.profils_dir}…",
          file=sys.stderr)
    releves.append((
        COLLECTION_PROFILS,
        lire_profils_git(args.ref, ref_dir),
        lire_profils_disque(Path(args.profils_dir)),
    ))

    if not args.seulement_profils:
        for collection in COLLECTIONS_AGREGATS:
            chemin_ref = f"{ref_pivot}/{collection.sous_chemin}".rstrip("/")
            chemin_disque = Path(args.pivot_dir) / collection.sous_chemin
            print(f"→ {collection.nom} : {args.ref}:{chemin_ref} ↔ {chemin_disque}…",
                  file=sys.stderr)
            releves.append((
                collection,
                lire_collection_git(args.ref, chemin_ref, collection),
                lire_collection_disque(chemin_disque, collection),
            ))

    profils_avant, profils_apres = releves[0][1], releves[0][2]
    if not profils_avant and not profils_apres:
        print("[!] Aucun profil des deux côtés.", file=sys.stderr)
        return 1

    rapport = comparer_tout(releves)
    markdown = generate_markdown_report(rapport, args.ref)

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(markdown, encoding="utf-8")
        print(f"→ Rapport écrit : {args.out}", file=sys.stderr)
    else:
        print(markdown)
    if args.out_json:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(
            json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    if rapport["bloquant"]:
        for sous in rapport["collections"]:
            for perte in sous["pertes_sur_champs_stables"]:
                print(f"[!] {sous['collection']} · {perte['fichier']} · "
                      f"{perte['champ']} : {perte['avant']} → {perte['apres']}",
                      file=sys.stderr)
            for perte in sous["pertes_scalaires"]:
                print(f"[!] {sous['collection']} · {perte['fichier']} · "
                      f"{perte['champ']} : {perte['avant']!r} → null",
                      file=sys.stderr)
        print(f"[!] {rapport['nb_pertes_bloquantes']} constat(s) bloquant(s).",
              file=sys.stderr)
        return 0 if args.tolerer_pertes else 1
    print("✓ Aucune perte bloquante sur les collections comparées.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
