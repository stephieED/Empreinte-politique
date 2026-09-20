<a id="budget-collecte-interventions"></a>
# Borner la collecte d'interventions, pas le job qui la contient (#498) (2026-08-20)

`2026-08-20`

> **En bref** — un shard tué par `timeout-minutes` n'écrit aucun profil ; un budget épuisé écrit et le déclare.

`timeout-minutes: 5` sur `extract-an` tuait les shards dès que
`collect_interventions=true`. Sur les deux seuls runs connus dans ce mode :
4 shards tués sur 8 (run `32302557156`, 19/08 21:11), puis **8 sur 8** (run
`32379928098`, 20/08 14:24) — ce dernier n'a collecté aucun profil AN.

## Deux chiffres, deux populations

Le commentaire qui justifiait `5` s'appuyait sur des durées de « 1m18s-2m10s ».
Elles sont exactes — et elles portent **toutes sur des runs qui ne collectent
pas d'interventions**, `collect_interventions` valant `false` par défaut.

En séparant les populations, le relevé par step change complètement de sens :

| population | n | job total | dont extraction | dont préambule |
| --- | ---: | ---: | ---: | ---: |
| `collect_interventions=false` (runs `32233766814`, `32288588518`) | 16 shards | 117-207 s | **8-18 s** | 107-193 s |
| `collect_interventions=true` (runs `32302557156`, `32379928098`) | 16 shards | 208-321 s | 59-286 s | 30-149 s |

Le « pire cas normal » de 2m10 n'était donc **pas** un coût d'extraction : dans
le mode par défaut, l'extraction coûte 8 à 18 secondes. Les deux minutes sont le
préambule du job — `actions/checkout` (14 à 127 s selon les shards),
`setup-python`, `pip install`, restauration des deux caches, téléchargement de
l'artifact d'amendements.

Conséquence, jamais nommée jusqu'ici : `timeout-minutes` ne borne pas la
collecte, il borne `préambule + collecte`. Ce qui reste réellement à
l'extraction varie de 107 s à 270 s **d'un shard à l'autre du même run**, selon
la durée du checkout. `laurent-wauquiez` (run `32302557156`) a été tué après
173 s d'extraction seulement : son checkout en avait consommé 126.

## Ce que le mode interventions ajoute

Trois charges, dont deux que l'issue n'avait pas identifiées :

1. **la recherche NosDéputés** (jusqu'à `nosdeputes_max_pages` pages × 4
   domaines) — 90 s mesurées sur `jean-luc-melenchon`, run `32379928098` ;
2. **les archives de débats Syceron**, 3 législatures, 22 à 55 s chacune quand
   `data.assemblee-nationale.fr` répond, 118 s au total sur `laurent-wauquiez` ;
3. **les archives de questions officielles** QE/QG/QOSD, jusqu'à 12 fichiers ;
4. et seulement ensuite, **le repli NosDéputés document par document**, qui ne
   se déclenche que si Syceron ne rend rien pour cet `acteurRef`.

**Les points 1 et 4 ont été retirés le 27/08/2026** avec le repli NosDéputés
([#syceron-actif-510](syceron-actif-510.md)) : il ne reste que les deux charges
d'archives AN, et les 90 s de recherche sont rendues au budget. Ce qui suit
décrit le mode tel qu'il était quand le budget a été dimensionné — le solde
n'est pas remesuré.

L'issue attribuait le surcoût au seul point 4. `laurent-wauquiez` le dément :
**zéro** appel de détail NosDéputés, et pourtant un timeout — il était encore
dans les archives de questions à la 5ᵉ minute. Un circuit ouvert sur
`nosdeputes.fr` (piste 3 de l'issue) ne l'aurait pas sauvé.

## Décision : un budget interne, et un timeout conditionnel qui le contient

**Un budget de temps mur pour la collecte d'interventions d'un candidat**
(`src/budget_collecte.py`, `--budget-interventions-secondes`, 240 s en CI). Il
est vérifié entre deux unités de travail : entre deux législatures Syceron,
entre deux législatures de questions, et **à l'entrée de chaque document**
NosDéputés — la seule granularité fine du parcours, où un document coûte jusqu'à
45 s sur une source dégradée (`read timeout=15` × 3 tentatives) et où il y en a
jusqu'à ~250 par candidat. Jamais au milieu d'une législature : son index par
acteur n'est mis en cache qu'une fois l'archive entièrement lue, et un index
partiel ferait passer une collecte incomplète pour une collecte faite.

Épuisé, il rend la main. Le profil partiel est **écrit**, donc publié, et la
troncature part dans `meta.warnings[]` (`collecte d'interventions tronquée
(budget de temps)`, propagé au pivot par `normalize_nosdeputes`) et en
`::warning::` GitHub, en nommant ce qui n'a pas été collecté :
`87 document(s) d'intervention NosDéputés, 2 législature(s) de questions
officielles`.

C'est là que le budget se distingue du timeout, et c'est la vraie raison de le
préférer. **Un shard tué par `timeout-minutes` ne publie rien du tout.**
L'issue supposait l'inverse (« ce qui avait été collecté avant la coupure est
publié ») parce que les steps `Profils écrits par ce job` et `Upload artifact
AN` s'exécutent bien, en `success`, sur un job tué. Ils s'exécutent — et
rapportent `Publication : 0 profil(s) écrits par ce job`, sur les 12 shards tués
des deux runs, vérifiés un par un, sans exception. Le profil n'est écrit qu'à la fin de la collecte
du candidat : coupé avant, le manifeste est vide et l'artifact aussi. Cinq
minutes de runner par shard pour aucune donnée.

**Le `timeout-minutes` devient conditionnel au mode** :
`${{ inputs.collect_interventions && 9 || 5 }}`.

- 5 min sans interventions : inchangé, et désormais justifié par la bonne
  population (extraction 8-18 s, préambule 107-193 s) ;
- 9 min avec : 240 s de préambule provisionné (mesure max : 193 s) + les 240 s
  du budget + ~60 s de marge.

240 s de budget, c'est 1,5× la plus longue extraction qui soit allée au bout
dans ce mode (160 s, `edouard-philippe`, run `32302557156`) — une mesure prise
dans le mode où la valeur s'applique, ce qui manquait à la valeur qu'elle
remplace.

## Le risque d'origine reste borné

Ce qui justifiait 5 min était un shard resté bloqué 20+ min sans signature
reconnue (run du 16/08, `jerome-guedj`), qui avait immobilisé tout le matrix
séquentiel (`max-parallel: 1`) derrière lui. Trois raisons pour lesquelles 9 min
ne le réintroduit pas :

1. la valeur ne s'applique que si `collect_interventions` est coché, ce qui
   n'est pas le défaut ;
2. dans ce mode, la collecte se borne elle-même : le timeout de job n'est plus
   le mécanisme d'arrêt normal, mais le dernier recours contre un vrai gel — que
   le budget, vérifié entre deux unités, ne peut pas voir (c'est le rôle des
   watchdogs par requête, `_get_with_watchdog` #340 et `download_watchdog` #370) ;
3. un tel gel coûte alors 9 min au lieu de 20+.

Le couplage entre les deux valeurs est vérifié par
`tests/test_ci_budget_interventions.py` : budget + préambule provisionné doit
tenir dans le timeout du mode où il s'applique, le timeout du mode par défaut ne
peut pas augmenter, et celui du mode interventions ne peut pas dépasser 10 min.
Le message de temps mur de `prepare-an-matrix` lit la même valeur — annoncer
5 min par shard pendant qu'un run en consomme 9 rendrait cet avertissement faux
au moment précis où il sert.

## Alternatives écartées

**Élargir simplement le timeout.** C'est la solution que le commentaire existant
interdisait déjà, à raison : elle rend au blocage silencieux exactement le coût
qu'on lui avait retiré, et elle ne produit toujours aucun signal — un shard
tronqué resterait indiscernable d'un shard complet.

**Un circuit ouvert après N échecs consécutifs sur un hôte** (piste 3 de
l'issue). Réduirait le coût du repli NosDéputés dégradé, mais `laurent-wauquiez`
montre qu'on peut atteindre le timeout sans un seul appel de détail : le
mécanisme ne couvre qu'une des trois charges. Le budget, lui, les couvre toutes,
et son plafond est indépendant du mode de panne. Reste une piste valable pour
réduire le *gaspillage* (3 × 15 s par document sur une source à terre), pas pour
borner la phase.

**Faire du budget un `input` du workflow.** Refusé : les inputs viennent d'être
refondus (#497) et un dixième bouton ferait porter à l'opérateur un arbitrage
qui se déduit du timeout. La valeur vit à côté de celui-ci, avec le test qui les
tient ensemble.

## Ce qui n'est pas traité ici, et qui est le vrai coût fixe du mode

Les archives Syceron et de questions **sont** dans le `path:` du cache
`public-data-cache-an-<semaine>` — mais elles n'y arrivent jamais. La clé de la
semaine est écrite par le premier job qui la touche, et ce sont des jobs en
`--skip-interventions` : ils ne remplissent ni `.cache/syceron_an` ni
`.cache/questions_an`. Les shards en mode interventions font ensuite un *exact
key hit* et `actions/cache` saute leur sauvegarde post-job — `Cache hit occurred
on the primary key public-data-cache-an-2026-W34, not saving cache` (job
`96228895556`). Vérifié sur le run `32379928098` : le tar restauré ne contient
que `acteurs_historique_an`, `scrutins_an` et `dossiers_an`.

Chaque shard re-télécharge donc l'intégralité des archives de débats et de
questions — c'est le défaut de #424, reparu sur les deux répertoires que seul le
mode interventions remplit. Le corriger proprement demande le même traitement
qu'aux amendements : un job dédié qui construit les index une fois et les publie
en artifact, `extract-an` les consommant en lecture seule. Une clé de cache
séparée ne suffirait pas — le premier shard sauvegarderait un index partiel et
les suivants, en *exact key hit*, ne pourraient plus le compléter de toute la
semaine. Hors périmètre de cette PR, consigné dans `ROADMAP.md`.

Tant que ce coût fixe reste, le budget de 240 s sera souvent consommé par des
téléchargements déjà faits par le shard précédent : les profils seront partiels,
mais partiels **et déclarés**, au lieu d'absents et muets.

---

