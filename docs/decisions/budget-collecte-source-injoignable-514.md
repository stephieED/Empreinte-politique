<a id="budget-collecte-source-injoignable-514"></a>
# Une source injoignable ne consomme plus le timeout d'un job, et son silence cesse de se lire comme un constat (#514) (2026-08-21)

`2026-08-21`

> **En bref** — une source injoignable ne consomme plus le timeout du job, et son silence cesse de se lire comme un constat.

**État relu le 21/08/2026 à 06:40 UTC ; `origin/main` = `921d1fd`.** Toutes les
mesures ci-dessous viennent des logs du run `32421439590` (job `extract-senat` =
`96594132947`, job `merge-and-pivot` = `96601126605`), relus après coup —
`archive.nossenateurs.fr` n'a **pas** été interrogé pendant l'instruction : la
source était à terre, la marteler pour vérifier n'aurait rien appris et aurait
été discourtois. Les doublures des tests rejouent le log.

## Le défaut

`generate_all_profiles.build_profile_any_chambre`, depuis #500 :

```python
budget = (
    BudgetCollecte(budget_interventions_secondes, libelle="collecte d'interventions")
    if budget_interventions_secondes and not skip_interventions
    else None
)
```

Le `and not skip_interventions` était **juste sur son périmètre** : un budget
d'interventions n'a rien à borner quand on ne collecte pas d'interventions.
#502 a ensuite posé `--skip-interventions` en dur sur `extract-senat`, pour une
raison mesurée et bonne (la collecte sénatorielle ne retenait rien, par
construction). Aucune des deux décisions n'était fausse. Ce qui manquait, c'est
qu'**aucune des deux n'avait à se prononcer sur le budget de l'autre** : le job
a perdu le seul plafond interne dont il disposait, alors qu'identité, votes et
dossiers n'en avaient jamais eu.

Mesuré sur le run `32421439590` : `extract-senat` a consommé **15 min 18 s**,
exactement son `timeout-minutes: 15`, dont **13 min 27 s** d'extraction, et a
publié **1 profil**.

## Quatre corrections au diagnostic de l'issue

**1. La source n'était pas « totalement injoignable ». Elle a répondu 3 fois
sur 45 tentatives.** Une identité complète (`/jean-luc-melenchon/xml`, 21:54:33
UTC) et deux HTTP 404 (`/jerome-guedj/votes/xml` 22:00:53,
`/15/dossiers/nom/json` 22:01:09). Le même chemin `/15/dossiers/nom/json` a
rendu un 404 pour un candidat et expiré pour le suivant : hôte saturé qui
bat de l'aile, pas hôte mort. La phrase « un hôte qui n'a jamais répondu une
seule fois » est fausse, et c'est elle qui rendait la piste du circuit ouvert
attirante.

**2. « 5 sur 13 » n'est pas cinq collectes.** Trois des cinq candidats
progressés (Arthaud, Tondelier, Royal) n'ont **pas de slug** et sortent en
0 ms sans une requête. Le job a mené **deux** collectes complètes et une
troisième interrompue. Population correcte : 8 des 13 candidats de
`raw_data/candidats.json` ont un slug résolvable, eux seuls coûtent quelque
chose.

**3. La répartition des 42 échecs n'est pas celle annoncée.** Relevé ligne à
ligne : **17** pour `jean-luc-melenchon` (et non pour `edouard-philippe`),
**12** pour `jerome-guedj` — plus 2 réponses 404, non comptées comme échecs de
requête — et **13** pour `edouard-philippe`, coupé en vol. L'issue additionnait
17 + 15 + 15 = 47 pour un total de 42.

**4. Et surtout : un budget seul n'aurait PAS fait écrire treize profils
partiels.** C'est la correction qui change la conception. Sans identité
résolue, `build_profile_any_chambre` rend `None`, `process_candidat` sort en
`introuvable` et **n'écrit rien** — quel que soit le temps qu'on lui laisse.
`jerome-guedj` et `edouard-philippe` seraient sortis les mains vides avec
n'importe quel budget. Le seul profil du run existe parce que l'identité de
Mélenchon est passée, pas parce que sa collecte a été bornée.

Corollaire : la promesse de #502 — « `_manifest_append` publie candidat par
candidat, donc un timeout ne perd que le candidat en cours » — n'est vraie que
pour un candidat dont l'identité est résolue. Elle ne l'était pas ici.

## Piste 1 retenue : deux budgets emboîtés, plus un troisième déjà là

`BudgetCollecte` gagne un `parent` : une section ouverte sur un budget ouvre
aussi celle de son parent, et `epuise()` est vrai dès qu'un maillon de la
chaîne l'est. C'est ce qui permet au budget par candidat de borner la collecte
d'interventions **sans toucher une ligne de #500** — tous ses
`budget_epuise(...)` existants voient l'épuisement du parent par la méthode
qu'ils appelaient déjà.

| Portée | Option | Valeur sur `extract-senat` |
| --- | --- | --- |
| phase d'interventions (#498) | `--budget-interventions-secondes` | absente (rien à borner) |
| candidat (#514) | `--budget-collecte-secondes` | **160 s** |
| process (#514) | `--budget-job-secondes` | **600 s** |

**160 s par candidat — les deux conditions de source, nommées.**

- *Source dégradée* (run `32421439590`, candidat avec slug,
  `--source senat --skip-interventions`) : la résolution d'identité — 2 formats
  × 3 tentatives, seule porte vers un profil écrit — a coûté **103 s**
  (`jerome-guedj`), **109 s** (`jean-luc-melenchon`), **125 s**
  (`edouard-philippe`). Pire cas structurel : 6 × (25 s de watchdog + 1,5 s de
  backoff) = **159 s**. 160 s la couvre entièrement et coupe ce qui vient
  après, qui ne peut plus rien produire à ce prix-là.
- *Source saine* (#501, `bruno-retailleau`, 20/08/2026) : **2,7 s** pour les
  4 requêtes du candidat. Le budget vaut **59×** la mesure : il ne peut pas se
  déclencher, donc il n'introduit aucun `meta.warnings` de bruit.

**600 s pour le job — dérivé, pas observé.** 900 s de `timeout-minutes` − 240 s
de préambule provisionné (6-170 s mesurés sur 15 runs, 105 s sur celui-ci)
− 25 s de dépassement possible de la requête en vol − 30 s de publication
(6 s mesurées) = 605 s, arrondi à 600.

**Pourquoi deux et pas un.** 8 slugs × 160 s = 1 280 s, contre 660 s
disponibles : borner le candidat ne borne donc pas le job. Et l'inverse ne
marche pas non plus — répartir 600 s en huit parts de 75 s placerait chaque
candidat **sous** les 103 s minimum de la résolution d'identité, ce qui
garantirait zéro profil au lieu d'en sauver ceux dont la source répond encore
par intermittence. Arbitrage assumé : sur une source à terre, environ quatre
candidats obtiennent une vraie tentative, les autres sortent en
`budget_job_epuise` — déclarés, comptés, annotés.

`timeout-minutes: 15` est **inchangé** (#502). Le budget le rend désormais
inatteignable : le job rend la main vers 14 min avec un résumé complet, au lieu
d'un `##[error]The operation was canceled` à 15 min.

## Pistes 2 et 3 écartées, et la mesure qui les écarte

L'objection de #498 au circuit ouvert tombe bien pour le Sénat : vérifié,
`BASE_URLS["senateurs"]` ne contient qu'un hôte depuis la fermeture de
`www.nossenateurs.fr`, là où le chemin AN en compte trois (`nosdeputes.fr`,
`data.assemblee-nationale.fr`, `questions.assemblee-nationale.fr`). L'issue a
raison sur ce point.

Mais **aucune des deux pistes n'est dimensionnable sur la population
disponible**, et les deux auraient détruit la seule donnée du run :

- la réponse qui a produit l'unique profil est arrivée après **exactement
  5 échecs consécutifs** sur l'hôte. Un circuit ouvert à N ≤ 5 s'ouvre une
  tentative avant elle ; à N ≥ 6 il s'ouvre pendant `jerome-guedj`, avant ses
  deux 404 — qui sont des réponses. Il n'existe aucun N que cette mesure
  justifie ;
- cette même réponse est venue de la **3ᵉ tentative**, après deux timeouts sur
  le même format. « Ne pas retenter après un timeout » l'aurait supprimée.

Choisir un N ici serait exactement la faute que l'issue documente sur trois
générations : une valeur tirée d'une condition de source et appliquée hors
d'elle. Le budget, lui, ne suppose rien de la source — il borne du temps, et
c'est son *effet* qui dépend de l'état de la source, pas sa justesse.

Ce qui a été gardé de la piste 3, sans sa règle : le budget est vérifié
**entre deux tentatives** dans `_get_payload`, ce qui plafonne le dépassement à
une tentative (25 s) au lieu d'un cycle de reprise entier (78 s). Tant que le
budget tient, les trois tentatives ont lieu.

Un précédent existait pour la piste 2, et il est instructif :
`_mark_amendements_legislature_failed` (#239/#246) renonce pour tout le run à
une **législature** dont l'archive a définitivement échoué. La granularité y est
la ressource, pas l'hôte, et le déclencheur est l'épuisement complet d'un cycle
de retry — pas un compteur d'échecs consécutifs à calibrer.

## Le silence de la source cesse de ressembler à un constat

Deuxième moitié du correctif, et celle que la correction n°4 rendait
nécessaire. `_get_payload` compte désormais les requêtes restées **sans
réponse** (`compteur_requetes_sans_reponse`), distinctes des requêtes émises :
un 404 est une réponse.

- **Profil écrit mais partiel** — le cas Mélenchon, dont le profil publié porte
  `votes: []` et `dossiers_legislatifs: []` après dix requêtes en timeout, sans
  un mot : `meta.warnings[]` reçoit désormais un `source injoignable` qui nomme
  les sections concernées. Le rapprochement se fait **section par section**, et
  le total ne compte que les sections citées — un compteur global déclarerait
  « identité injoignable » d'un slug dont l'identité a reçu un franc 404 et dont
  seuls les votes ont expiré.
- **Aucun profil** — `process_candidat` distingue `source_indisponible` de
  `introuvable`, sur le critère des requêtes **d'identité** restées sans réponse,
  et sur elles seules : c'est l'identité qui décide qu'un profil est écrit ou
  jeté. Les deux statuts sont comptés au résumé et remontés en `::warning::`.

**Aucun profil n'est fabriqué** dans le second cas. Écrire un squelette à la
place d'une collecte manquée serait la donnée par défaut qu'interdit la règle 5
d'AGENTS.md §2, et ferait basculer `chambre` sur une défaillance transitoire —
le défaut même de #484.

Le cumul se fait sur les chambres et non par hôte, et le run le justifie : à
22:24 UTC, `merge-and-pivot` a échoué sur `ROSTER_INCOMPLET` pour **`deputes` et `senateurs` à la fois**. Les deux sources étaient à terre simultanément. La
question qui décide du statut d'un candidat n'est pas « quel hôte est tombé »
mais « une source a-t-elle tranché, ou aucune n'a répondu ».

## Le garde-fou contre la classe

`--budget-collecte-secondes` a pour défaut `None`, et **`0` est une valeur
distincte** : « pas de budget, décidé » ne s'obtient plus en ne tapant rien.

- `tests/test_ci_budget_par_job.py` inventorie les 6 invocations de
  `generate_all_profiles.py` du workflow et impose que chacune tombe dans un
  régime explicite : bornée, absence déclarée, ou hors collecte FR
  (`--pivot-only` / `--source ue`). Une septième invocation muette échoue.
  `extract-an` et `extract-roster-groupes` portent donc un
  `--budget-collecte-secondes 0` motivé ;
- un test lit le code et refuse qu'une condition de mode revienne conditionner
  la **fabrique** du budget — la ligne exacte qui a produit cette issue ;
- `valider_budgets` refuse à l'exécution un budget mort
  (`--budget-interventions-secondes` sous `--skip-interventions`) et signale une
  collecte sans budget déclaré. Signale, et n'échoue pas : rendre l'option
  obligatoire casserait les commandes locales de `README.md`, et un garde-fou
  qu'on désactive pour travailler ne garde rien (#460) ;
- `budget_collecte.creer` ne dépend que de la valeur, et son docstring dit
  pourquoi.

**Vérifié par mutation**, comme l'exige la leçon de #460. Les 11 régressions
font toutes échouer la suite : retirer le budget d'`extract-senat`, le ramener à
0, le passer sous la résolution d'identité mesurée, gonfler le budget de job
au-delà du timeout, retirer la déclaration d'`extract-an` ou du job roster,
poser un budget d'interventions mort, réintroduire la condition de mode dans la
fabrique, cesser de vérifier le budget entre deux tentatives, cesser de
propager l'épuisement du parent, cesser de distinguer une source muette d'une
absence.

## Ce qui reste ouvert

- **L'ordre de passage est figé.** Sur une source à terre, ce sont toujours les
  mêmes premiers candidats qui obtiennent les 600 s. `extract-senat` n'a ni
  `--resume` ni rotation, contrairement au job roster. Consigné dans
  `ROADMAP.md`.
- **Le job roster n'a pas de budget dimensionné**, faute d'une mesure sur ses
  752 membres. Poser un chiffre mesuré ailleurs serait la faute que cette issue
  corrige.

