<a id="max-parallel-sur-cle-chaude-1137"></a>
# `extract-an` ne sérialise ses shards que sur un cache froid (#1137) (2026-09-25)

`2026-09-25`

> **En bref** — `max-parallel: 1` a une seule raison, le réchauffement du cache AN de shard en shard, et cette raison ne vaut qu'au **premier run de la semaine** : une fois la clé écrite, chaque shard fait un *exact key hit* dès le premier et la chaîne ne transmet rien ; `prepare-an-matrix` sonde donc la clé en `lookup-only` et `extract-an` prend `max-parallel: 4` quand elle est déjà chaude, `1` sinon — **~23 min projetées, jamais mesurées**, et le repli sur toute réponse autre qu'un oui franc est l'état d'avant ce lot.

## 1. Le constat

Sur le run `36040086663` (24/09/2026, 2 h 06 au total), `extract-an` occupe
**31 minutes de temps mur** pour 31 shards dont la **médiane est de 60 s**. La
somme du travail réel fait 30 minutes : le job ne perd rien à attendre, il
attend tout ce qu'il fait. C'est le plus gros poste restant du chemin critique
une fois #1130 et #1131 passés.

## 2. Pourquoi la sérialisation existe — et l'argument n'est pas balayé

`max-parallel: 1` est **conservé par #412** sur l'argument *cache* de #222 et
lui seul ([[concurrence-shards-extraction-412]]) : les shards se passent le
cache AN de proche en proche. Le premier restaure par préfixe, complète ce qui
manque et **écrit la clé de la semaine** ; les suivants font un *exact key hit*.
Des shards parallèles retéléchargeraient chacun les dumps AN Open Data — c'est
#424 par un autre chemin.

Cet argument est **exact**. Il est seulement **daté** : il décrit le run qui
rencontre une clé neuve.

## 3. La faille : l'argument ne vaut que sur une clé froide

Quand la clé existe déjà, la chaîne ne transmet **rien**. Chaque shard fait un
hit exact dès le premier, `actions/cache` saute la sauvegarde de tous — la
condition de sauvegarde d'`extract-an` compare précisément la clé restaurée à
celle qu'il écrirait, et les trouve égales. Il n'y a plus de « proche en
proche » : il y a 31 lectures indépendantes de la même entrée immuable.

C'est **mot pour mot** la situation du job roster, que **#467 a ouvert à
`max-parallel: 4`** pour cette raison précise ([[budget-execution-pleine-echelle-467]]) :
« sa clé est déjà chaude quand sa matrice commence, ses shards ne se passent
rien et n'ont donc rien à sérialiser ».

L'asymétrie entre les deux jobs était donc réelle, mais mal placée : elle
n'oppose pas `extract-an` au roster, elle oppose **deux états du cache**. Un
seul run par semaine est dans l'état que #412 décrit ; les autres — les runs
sont programmés toutes les 4 h — paient une sérialisation qui ne leur rend rien.

## 4. Décision

`prepare-an-matrix`, qui conclut avant que la matrice ne démarre, **sonde la
clé** (`actions/cache/restore` en `lookup-only: true`) et publie `cache_chaud`.
`extract-an` prend :

```yaml
max-parallel: ${{ needs.prepare-an-matrix.outputs.cache_chaud == 'true' && 4 || 1 }}
```

`jobs.<id>.strategy` accepte les expressions, avec les contextes `github`,
`needs`, `vars` et `inputs` (documentation GitHub, vérifiée le 25/09/2026) —
d'où la sonde dans un job amont, et non dans un `steps` d'`extract-an`, qui ne
s'évaluerait pas.

**4, comme le roster** : la valeur n'a pas été re-arbitrée, et l'aligner évite
d'avoir deux plafonds à défendre.

**Le repli est `1`, c'est-à-dire l'état d'avant ce lot.** Une sonde en échec,
une sortie vide, un job amont skippé, un mode non sondé : tout ce qui n'est pas
un oui franc sérialise.

`extract-an` reste le **seul écrivain** de la clé AN, et rien de #424, #505,
#550 ou #555 ne bouge : ce lot ne touche ni au `path:`, ni aux clés, ni à la
péremption sélective. Une entrée de cache est immuable et aucun autre job
n'écrit cette clé, donc ce que la sonde constate au démarrage de la matrice est
encore vrai quand les shards partent.

### Les deux modes qui restent en série, et pourquoi

| Mode | Sondé ? | Raison |
| --- | --- | --- |
| Par défaut | **oui** | La clé est la semaine ISO nue, `prepare-an-matrix` sait la composer |
| `cold_start` | non | Rien n'est restauré ni sauvegardé, donc la chaîne ne sert effectivement à rien — mais c'est le mode où **chaque shard repart des archives**, et on ne multiplie pas par 4 ce qu'on demande à `data.assemblee-nationale.fr` ce jour-là |
| `collect_interventions` | non | La clé porte en plus l'**empreinte de complétude** (#550), que seul `src/cache_an_empreinte.py` sait calculer — et il importe `candidate_profile`, donc `requests`, que ce job n'installe pas |

Le troisième cas mérite sa ligne : `prepare-an-matrix` tourne en `python3`
système, **sans aucune dépendance**, sous un `timeout-minutes: 5` que #674 lui a
déjà vu dépasser **dans `actions/checkout`**. Lui ajouter un `pip install` pour
sonder une clé serait payer un risque réel contre un gain projeté. Sonder une
clé *fausse* coûterait le cache ; ne pas sonder ne coûte que le statu quo.
`tests/test_ci_max_parallel_cle_chaude_1137.py` tient cette raison : le jour où
ce job gagne des dépendances, le test le dit, et la sonde pourra couvrir les
deux modes.

## 5. Le gain, et ce qu'il n'est pas

**~23 minutes, PROJETÉES.** 31 min → ~8 min à 4 shards en parallèle sur une clé
chaude. Aucun run n'a tourné ainsi, et `max-parallel` **ne se teste pas en
local** — la même réserve qu'au §5 de #467. La médiane de 60 s masque une
dispersion (certains shards dépassent 3 min), donc le gain réel sera **inférieur
à la division par 4** : une vague coûte son shard le plus lent.

Le premier run qui portera ce changement en dira le prix réel. C'est pourquoi le
lot est livré **seul** : une seule variable à lire.

## 6. Ce qui échoue en silence, et ce qui le rattrape

Le revers d'un mécanisme qui retombe proprement sur l'état antérieur est qu'il
**échoue sans bruit** : une sonde qui se trompe ne casse aucun run, ne lève
aucune alerte, et coûte simplement les minutes qu'elle devait faire gagner.
Trois façons de se tromper, une garde chacune :

| Dérive | Effet | Garde |
| --- | --- | --- |
| Le `path:` de la sonde diverge de celui d'`extract-an` | La **version** d'une entrée de cache est un hachage du `path` : la sonde ne trouve plus rien et répond « froid » **pour toujours** | `test_la_sonde_et_extract_an_ont_le_meme_path` compare les deux blocs ligne à ligne |
| La **clé** diverge | La réponse porte sur une autre entrée que celle dont dépend la chaîne | `test_la_sonde_et_extract_an_ont_la_meme_cle` |
| Un `restore-keys` s'y glisse | Le préfixe nu **traverse les semaines** (#555) : la sonde répondrait « chaud » sur une clé pas encore écrite, et 4 shards partiraient sur un cache froid | `test_la_sonde_ne_se_replie_sur_aucun_prefixe` |

S'y ajoutent le repli (`test_le_repli_est_la_serialisation`), la provenance de
la condition (`strategy` n'accepte pas le contexte `steps`), et la cohérence de
l'avertissement de temps mur de `prepare-an-matrix`, qui annonce désormais des
**vagues** et non des shards en file — même règle qu'à `AN_TIMEOUT_MINUTES`
(#498) : un avertissement faux au moment précis où il sert ne vaut pas mieux
que pas d'avertissement.

Les trois dérives ont été **vérifiées par mutation** du workflow avant
livraison, pas seulement écrites.

## 7. L'alternative rejetée

**Ouvrir `max-parallel` à 4 inconditionnellement**, en acceptant que le premier
run de la semaine retélécharge quatre fois les dumps. C'est ce que ce lot aurait
pu être, en une ligne et sans sonde.

Rejeté : l'argument de #412 n'est pas faux, il est **conditionnel**. Le
neutraliser en bloc reviendrait à écarter une mesure (#424 : ~438 Mo
retéléchargés par run quand la chaîne casse) au profit d'une projection. Une
sonde coûte quelques secondes dans un job qui en a cinq minutes, et elle laisse
l'argument de #412 vivre là où il vaut.

**Non instruit ici**, et laissé ouvert : `extract-roster-groupes` de 4 à 8
(20 min → ~10), et le `filter: blob:none` sur le checkout de `merge-and-pivot`
(572 s), qui serait à **mesurer** avant d'être proposé — un checkout creux y est
impossible, le job committant le dépôt entier.
