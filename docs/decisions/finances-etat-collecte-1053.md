<a id="finances-etat-collecte-1053"></a>

# Les finances de l'État : l'exercice pour unité, le ministère pour maille (#1053) (2026-10-12)

`2026-10-12`

> **En bref** — Une vue des finances publiques sur les fiches de gouvernement était
> à l'étude. Quatre arbitrages l'ont cadrée : l'exercice budgétaire est l'unité, le
> voté et le réalisé se montrent côte à côte, la maille est le ministère à partir de
> 2015, et aucun écart n'est calculé. `src/finances_etat.py` lit le portail du
> ministère de l'Économie, dans un job à part ; rien n'en est encore publié.

## Contexte

Demande de la propriétaire, le 08/10/2026 : trouver des sources de l'État qui
permettent de montrer, pour chaque gouvernement, comment le budget est utilisé et
d'où vient l'argent. #1053 posait quatre questions à trancher avant toute ligne de
code. L'inventaire mesuré vit dans `docs/sources/finances-etat.md` et dans les
commentaires de l'issue.

Une affirmation de l'issue était périmée : le portefeuille ministériel n'est plus
hors périmètre depuis #382/#383. Mesuré le 08/10/2026 sur les 17 fiches de
gouvernement : 768 des 770 lignes `membres[]` portent un `portefeuille` sourcé.

## Décision

| Question de l'issue | Arbitrage | Date |
| --- | --- | --- |
| 3. À quoi rattache-t-on un budget | **À l'exercice.** Une fiche montre un budget avec, datés, le gouvernement qui l'a fait voter et ceux en fonction pendant son exécution. Aucun montant n'est réparti entre gouvernements | 08/10/2026 |
| 1. Quel budget | **Le voté et le réalisé**, côte à côte | 12/10/2026 |
| 2. Quelle maille | **Le ministère, à partir de 2015.** Les recettes restent aux grandes lignes, aucun fichier ne les rattachant à un ministère | 12/10/2026 |
| 4. Comment dire l'écart | **Deux montants juxtaposés.** Ni différence, ni pourcentage, ni tri des ministères ; rien ne s'affiche quand l'un des deux manque | 12/10/2026 |

Ce que le module en tire :

1. **Une seule source, le portail du ministère** (`data.economie.gouv.fr`, Licence
   Ouverte 2.0). `budget.gouv.fr` est derrière une protection anti-robots, qui
   n'est pas contournée.
2. **`raw_data/finances_etat.json` garde le programme**, pas seulement le
   ministère : c'est par le numéro de programme que le consommé de 2023 à 2025
   retrouve son ministère, les fichiers d'exécution n'en portant pas.
3. **Un côté sans fichier se déclare** (`vote_non_resolu`, `realise_non_resolu`),
   avec sa raison et un drapeau `a_retenter` : faux quand la source ne le publie
   pas, vrai quand la lecture a échoué. Au 12/10/2026 : le voté 2015, le consommé
   2021 et 2022.
4. **Un exercice clos depuis plus d'un an et entièrement résolu ne se relit pas.**
   Les grandes lignes et les deux derniers exercices se relisent à chaque passage.
5. **Une lecture en échec n'écrase jamais un bloc résolu**, et un fichier qui rend
   moins de 100 programmes ou des montants tous nuls est refusé : une colonne
   renommée par la source se lirait sinon sans erreur.
6. **Un job à part, `extract-finances-etat`**, sur le modèle d'`extract-gouvernements` :
   il ne lit pas le corpus pivot, ne rallonge pas le chemin critique, et son échec
   laisse la fusion sur le fichier du run précédent.
7. **Le rattachement à un gouvernement ne demande aucune collecte** :
   `pivot_data/textes_promulgues.json` porte déjà les quatorze lois de finances de
   2013 à 2026 avec leur date de promulgation.

Mesuré le 12/10/2026 sur le portail réel : onze exercices lus, de 115 à 139
programmes du budget général par côté ; 129 libellés de ministère sur 141 se
retrouvent mot pour mot dans un portefeuille de plein exercice en fonction la même
année, sur les exercices 2015 à 2019 et 2023 à 2025.

## Alternatives écartées

- **Le mois pour unité** (borner les cumuls mensuels aux dates d'un gouvernement) :
  possible depuis 2013 seulement, sans ministère, et un gouvernement ne commence
  pas un premier du mois.
- **Les grandes lignes seules** : complètes de 2013 à 2025 dans un seul jeu, mais
  sans lien avec les portefeuilles. Elles sont collectées, pour les recettes.
- **Commencer en 2011** : les libellés de ministère de 2011 à 2014 sont abrégés par
  la source (55 retrouvés sur 95), ce qui demandait une table tenue à la main.
- **Lire les PDF** des lois de règlement 2021 et 2022 : fragile, et hors du motif
  du projet.
- **Eurostat et l'Insee** : comptabilité nationale, annuelle ; écartés par la
  propriétaire le 08/10/2026.

## Ce qui reste

- Le pivot et son schéma, qui attendent la maquette (AGENTS.md §11).
- La loi de finances 2015 par ministère, non trouvée.
