<a id="cache-fraicheur-interventions-555"></a>
# Les `restore-keys` du cache AN traversaient les semaines : la fraîcheur ne se met pas dans la clé, elle se lit dans celle qu'on a restaurée (#555) (2026-08-28)

`2026-08-28`

> **En bref** — la semaine était dans la clé depuis toujours ; c'est la restauration qui la contournait.

Cinquième reprise de la même famille — mais la première où **la clé ne cache
rien**. Les quatre précédentes ont ajouté à la clé la dimension qui lui
manquait. Ici, la semaine y est depuis toujours ; c'est la **restauration** qui
la contourne.

| Forme | Issue | Ce qui manquait | Conséquence mesurée |
| --- | --- | --- | --- |
| 1re | #424 | les répertoires réellement couverts | ~438 Mo re-téléchargés par run |
| 2e | #498 | (même forme, sur les interventions) | 12 shards tués sans rien publier |
| 3e | #505 | le mode d'extraction (`-interv`) | 650,5 Mo × 7 shards par run |
| 4e | #550 | la complétude du CONTENU indexé | 113-219 s × 7 shards par run |
| **5e** | **#555** | **rien dans la clé — c'est le `restore-keys` à préfixe nu qui la blanchit** | **une entrée du 20/08 resauvegardée sous la clé du 24/08 en 18 s** |

## Ce qui s'est passé, relevé dans les journaux

Run `32738726729`, lundi 24/08/2026 — **première exécution de la semaine
W35** —, shard `jean-luc-melenchon`, job `97468417763` :

```
14:28:54  Cache hit for restore-key: public-data-cache-an-2026-W34
14:28:54  Cache Size: ~21 MB (21880744 B)
14:28:54  Cache restored from key: public-data-cache-an-2026-W34
14:28:55  Cache restored from key: public-data-cache-dossiers-2026-W34
14:28:58  Extraction AN (NosDéputés) — jean-luc-melenchon
14:29:09  Elapsed (wall clock) time (h:mm:ss or m:ss): 0:10.12
14:29:12  Cache saved with key: public-data-cache-an-2026-W35
```

Dix-huit secondes entre la restauration d'une entrée écrite le **20/08** et sa
sauvegarde sous la clé du **24/08**. L'extraction qui les sépare dure 10,12 s :
**aucune archive n'a été rouverte**. Confirmé par l'API des caches du dépôt —
`public-data-cache-an-2026-W34` (21 880 744 o, créée le 20/08 à 18:54) porte un
`lastAccessedAt` du 24/08 à 14:28:54, et `public-data-cache-an-2026-W35`
(21 855 225 o) est créée dix-huit secondes plus tard.

La clé hebdomadaire n'a donc **rien périmé**. Et le mécanisme se reconduit :
W35 blanchit W34, W36 blanchira W35. L'ancienneté n'est pas bornée par une
semaine, elle n'est bornée par rien.

## Pourquoi la semaine est le seul recours

Aucun constructeur d'index AN ne regarde l'âge de ce qu'il trouve :

| Fonction | Condition de réutilisation du cache |
| --- | --- |
| `_ensure_acteurs_historique_zip_downloaded` | `zip_path.is_file()` |
| `_build_acteur_questions_index` | `index_path.is_file()` |
| `_read_cached_interventions_syceron_acteur` | `index_dir.is_dir()` |

Pas un `mtime`, pas un TTL, pas une date. C'est ce qui fait de la clé
hebdomadaire le **seul** mécanisme de fraîcheur — et donc du préfixe nu un
contournement total, pas partiel. Cette prémisse n'est pas écrite dans un
commentaire : `test_aucun_constructeur_d_index_an_ne_regarde_l_age_du_cache`
la lit dans le source des trois fonctions. Le jour où l'une acquiert sa propre
péremption, le test tombe et cette décision est à relire.

## Pourquoi la correction évidente est fausse

**Retirer la dernière ligne des `restore-keys`.** Elle règle la fraîcheur et
rouvre #424 : le premier run de chaque semaine repart d'un cache AN vide. Pire,
elle jette avec les archives vivantes les index des législatures **closes**,
dont le réchauffement inter-semaines est parfaitement légitime — mesures #550 :
147 s de réindexation pour la 15e, 55 s pour la 16e, 42 s pour la 17e. On
paierait 244 s chaque semaine pour rafraîchir 42 s de contenu.

**Il manquait donc un marqueur de fraîcheur, pas une clé.** Et il existait
déjà : `actions/cache/restore` rend dans `cache-matched-key` la clé
**effectivement** restaurée, qui porte sa semaine. Rien à écrire sur le disque,
donc rien à ajouter au `path:` — un `path:` modifié change la *version* de
l'entrée (`actions/cache` la hache), et la correction aurait coûté une semaine
de cache froid sur les deux jobs rien qu'à se déployer.

## Ce qui est retenu

1. **Le préfixe nu reste**, dans les deux jobs AN. C'est le réchauffement de
   #424, et il est désormais *borné* au lieu d'être *subi*.
2. **La semaine de la clé restaurée est comparée à la semaine courante**
   (`src/cache_an_fraicheur.py`), juste après la restauration et avant toute
   extraction.
3. **Péremption SÉLECTIVE, jamais en bloc.** Ne sont supprimés que les chemins
   qui vieillissent : `.cache/acteurs_historique_an` en entier — le référentiel
   des acteurs n'a aucune structure par législature et l'AN le republie en
   continu — et, sous `scrutins_an` / `questions_an` / `syceron_an`, les seuls
   répertoires de législatures **non figées**. Les closes restent en place.
4. **La frontière est dérivée du code**, jamais recopiée : intersection de
   `AN_SCRUTINS_LEGISLATURES_FIGEES` et `AN_AMENDEMENTS_LEGISLATURES_FIGEES`.
   Même règle que l'empreinte de #550, et pour la même raison — recopiée, elle
   deviendrait fausse à la clôture de la 17e ou à l'ouverture de la 18e.
   *Intersection* et non union : une divergence entre les deux référentiels
   ferait périmer une législature **de trop**, soit un coût de réindexation,
   jamais une donnée conservée à tort. Le sens de l'erreur est choisi.
5. **Une clé dont la semaine ne se lit pas périme par précaution**, avec un
   `::warning::`. Une réindexation coûte 42 s ; un silence coûterait la
   fraîcheur de toutes les semaines suivantes.
6. **Le PRODUCTEUR périme, le CONSOMMATEUR déclare.** `extract-an` est le seul
   écrivain de la clé AN (#505/#550) : il paie la réindexation et la persiste
   pour les autres. `extract-roster-groupes` est en restauration seule — y
   périmer ferait retélécharger ~40 Mo d'archives par chacun de ses 8 shards
   sans que rien ne soit persisté en retour, soit #424 recréé. Il émet un
   `::warning::` nommant la semaine servie, et ne supprime rien. C'est la
   distinction *qui produit / qui écrit la clé* de #424/#505, appliquée à la
   fraîcheur.
7. **Aucun constructeur d'index n'est touché.** Les gardes de #505/#510 — ne
   jamais mettre en cache un index construit sur une archive absente ou vide —
   sont intactes, et un test vérifie qu'après péremption l'empreinte de #550
   décrit correctement le disque partiel qui reste. Les deux corrections ne
   peuvent pas diverger sans qu'un test tombe.
8. **Les deux steps sont en `continue-on-error`.** La péremption est un
   rafraîchissement, pas une garde : elle ne doit jamais tuer un shard qui a des
   profils à publier. Même arbitrage que la sauvegarde explicite de #550.

## Le gain, et ce qu'il n'est pas

| | Aujourd'hui | Après #555 |
| --- | --- | --- |
| Index de la 17e législature (débats, questions) | jamais rafraîchi tant qu'une entrée existe sous le préfixe | rafraîchi une fois par semaine |
| Référentiel des acteurs, scrutins de la 17e | idem | idem |
| Index des 15e/16e (closes) | réchauffés par accident | réchauffés **par décision** |
| Coût hebdomadaire de réindexation | 0 s, et une donnée qui vieillit sans borne | **42 s**, sur le premier shard de la semaine |
| Coût si l'on avait retiré le préfixe nu | — | 244 s/semaine **et** #424 rouvert |

Le gain n'est pas une seconde gagnée : c'est une **borne** posée là où il n'y en
avait aucune. Les 42 s sont ce qu'elle coûte, et ce coût est payé une fois par
semaine par le shard que #550 a déjà déclaré tronqué — celui qui construit
l'index. Pour lui, #555 remplace une reconstruction de 244 s (les trois
législatures, quand elle a lieu) par une de 42 s (la 17e seule, chaque semaine).

## Ce qui est écarté, et pourquoi

**Piste 1 de l'issue — deux clés séparées, l'une pour les répertoires figés,
l'autre pour les vivants.** La frontière figé/vivant ne passe pas entre les
répertoires mais **à l'intérieur** de trois d'entre eux : `scrutins_an`,
`questions_an` et `syceron_an` mélangent chacun des législatures closes et la
17e ; `acteurs_historique_an`, lui, n'a aucune structure par législature et est
entièrement vivant. Séparer en deux clés obligerait donc le `path:` du workflow
à énumérer des numéros de législature — une liste recopiée dans le YAML,
exactement ce que #550 a refusé, et fausse le jour où la 17e se clôt. Et
modifier le `path:` change la *version* des entrées : la correction se déploie
au prix d'une semaine de cache froid sur les deux clés et les deux jobs. La
solution retenue prend la **sémantique** de cette piste — distinguer selon la
péremption — sans son mécanisme.

**Piste 2 — restaurer largement, dater et déclarer, sans rien corriger.**
Écartée comme réponse entière, retenue là où périmer coûterait plus que le
défaut : le job consommateur (point 6 ci-dessus). Seule, elle laisse la
correction à la charge d'un humain qui relit les journaux d'un run
`workflow_dispatch` — et le défaut décrit ici a vécu trois issues sans que
personne ne le lise dans un journal. Un avertissement sur lequel rien n'agit
n'est pas une borne.

**Piste 3 — réindexer sélectivement au démarrage ce que la semaine restaurée ne
couvre pas.** C'est la piste retenue, mais **par la suppression et non par la
réindexation**. Apprendre au code à réindexer sélectivement demanderait
d'ajouter un second chemin de fraîcheur dans `candidate_profile.py`, à côté de
celui qui existe — « le fichier est là, donc il est bon ». Deux chemins de
fraîcheur qui doivent s'accorder, c'est la configuration qui a produit #505 et
#510. Supprimer le fichier fait faire au chemin existant exactement ce qu'il
faut, sans le toucher.

**Un fichier sentinelle `fraicheur.json` à côté de l'index**, sur le modèle
d'`AMENDEMENTS_FRAICHEUR_FILENAME` (#253) — c'est ce que la section « ce qui
reste latent » de #550 suggérait. Écarté pour une raison qui n'apparaît qu'en
l'écrivant : le sidecar doit entrer dans le `path:` du step de cache pour
survivre au run, donc changer la version des entrées, donc coûter une semaine de
cache froid. Le modèle des amendements reste juste **chez eux** : leur index est
transmis par artifact et par une clé propre, et leur `fraicheur.json` qualifie
une *construction* (réussie ou non), pas un *âge*. Ici, la clé restaurée dit
déjà l'âge, gratuitement.

## Ce qui n'a pas pu être établi sans un run réel

- **Le coût complet d'une péremption.** Seule la part Syceron est mesurée
  (42 s pour la 17e, run `33100214165`). Le retéléchargement
  d'`acteurs_historique_an` (13,6 Mo) et des scrutins de la 17e (26,3 Mo,
  relevé #467) n'a pas de durée mesurée **isolément** : les 8-18 s d'une
  extraction en mode par défaut sont un chiffre à cache CHAUD, il ne s'applique
  pas ici. C'est le seul chiffre de cette entrée qui pourrait imposer un
  re-dimensionnement.
- **Si le shard qui ouvre la semaine reste tronqué.** #550 l'a déjà déclaré
  tronqué quand il construit l'index (244 s pour 250 s de budget) ; #555 fait
  tomber cette construction à 42 s, donc le risque baisse. Mais « baisse » n'est
  pas « mesuré », et le budget de 250 s a été posé par #546 sur des horloges
  antérieures aux deux corrections.
- **Le nombre et le poids des entrées par semaine.** #550 les fait passer de 1 à
  une par état de complétude atteint (7 entrées AN coexistent au 28/08, dont 5
  écrites dans le seul run `33165786207`) ; #555 ne change pas ce compte, mais
  aucune mesure ne dit ce que devient le total avec des semaines réellement
  distinctes. Le quota du dépôt n'est pas la contrainte active à ce jour
  (826 Mo utilisés sur 10 Go, mesuré le 28/08).

## Le re-dimensionnement proposé, non appliqué

`--budget-interventions-secondes 250` et le `timeout-minutes: 10` du job restent
**intacts** — ils sont verrouillés ensemble par
`tests/test_ci_budget_interventions.py` (interlock #546). #555 va dans le sens
d'une marge plus confortable, pas moins : la reconstruction hebdomadaire du
shard qui ouvre la semaine passe de 244 s à 42 s. **La proposition est donc de
remesurer, et rien d'autre** : baisser un budget sur une amélioration non
mesurée serait exactement la faute que #546 a corrigée. Condition de réouverture
écrite : deux runs réels consécutifs franchissant une semaine, dont le premier
shard de la semaine neuve n'est pas tronqué.

---

