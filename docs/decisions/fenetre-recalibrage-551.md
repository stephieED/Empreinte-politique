<a id="fenetre-recalibrage-551"></a>
# La fenêtre de 30 ne pose pas le plateau qu'on croit, et la table mesurée ne le dit pas (#551) (2026-08-28)

`2026-08-28`

> **En bref** — mesure, projection et quatre arbitrages rendus sur la fenêtre de squash.

**Les quatre arbitrages sont rendus** (voir « Arbitrage rendu » dans chaque
section, 28/08/2026).** Cette entrée mesure, projette et recommande.
La valeur de la fenêtre, l'unité dans laquelle elle se compte, son déclenchement
et la destination de l'archive restent à trancher. `FENETRE=30` n'a pas été
changé.

> **⚠ Deux tables, deux questions. Ne pas les confondre.**
>
> **(a) rétrospective** — « que gagnerais-je à resserrer *aujourd'hui* ? »
> Réponse : presque rien avant 6. **Elle ne fonde aucune politique.**
>
> **(b) prospective** — « quel *plateau* la fenêtre pose-t-elle en régime
> permanent ? » **C'est celle-là qui fonde une politique**, et c'est la seule à
> laquelle une valeur de fenêtre répond.
>
> La table (a) sature par le bas *uniquement* parce que sa queue est faite de
> commits écrits en phase de développement, quand le corpus faisait 8 à
> 48 profils. Ce n'est pas une propriété de la fenêtre : c'est une trace de
> l'histoire du projet, et ces commits-là ne reviendront pas.

## Population et méthode

Sauf mention contraire, tout ce qui suit est mesuré le 28/08/2026 sur
`origin/main` = **`dc3ba83`**, qui porte **479 profils** dans `raw_data/profiles`
et **28 commits de données** (sujet « mise à jour automatique des données »).

**Cette population a bougé pendant la mesure** : `origin/main` est passé à
`0e2edf0` avec un 29<sup>e</sup> commit de données, `f5e20b6` (28/08,
481 profils). La table (a) reste rapportée à `dc3ba83` pour rester cohérente ;
la mesure du coût marginal, plus tardive, part de `f5e20b6`. Conséquence
pratique : **il ne reste plus qu'un commit de données avant que la fenêtre de 30
morde**, et non deux comme l'annonçait l'issue.

Méthode de (a), identique à celle de #434 : `git clone --mirror --no-hardlinks`
dans un temporaire, **ramené à la seule ref `refs/heads/main`** — une ref oubliée
ré-épingle l'ancien historique et le gain mesuré serait faux —, `reflog expire`,
puis `gc --prune=now` et `du -sm`. Aucune écriture dans le dépôt de travail,
aucun push. Les fonctions de coupure et de rejeu sont celles du script, extraites
telles quelles.

Le chiffre de référence est **434 Mo** (miroir de `dc3ba83`, une seule ref, après
`gc`), contre 284 Mo le 20/08 à 209 profils. Il ne coïncide pas avec les 415 Mo
de [l'entrée #429 ci-dessous](critere-sortie-volumetrie-429.md), pris le même jour :
deux variantes de la même méthode diffèrent — le commit mesuré et la réduction à
une seule ref — et **l'écart n'a pas été instrumenté**. Aucun raisonnement de
cette entrée ne repose dessus.

## (a) La table rétrospective

Taille du dépôt selon la fenêtre, en mégaoctets, à 28 commits de données
(« 28 » = historique complet) :

| fenêtre | 0 | 1 | 2 | 3 | 4 | 6 | 8 | 10 | 12 | 15 | 20 | 24 | 27 | 28 (complet) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dépôt (Mo) | 180 | 194 | 208 | 219 | 225 | 312 | 364 | 394 | 405 | 430 | 430 | 433 | 433 | 434 |

| fenêtre ramenée de 28 à… | 27 | 24 | 20 | 15 | 12 | 10 | 8 | 6 | 4 | 2 | 0 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| gain (Mo) | 1 | 1 | 4 | 4 | 29 | 40 | 70 | 122 | 209 | 226 | 254 |
| soit | 0,2 % | 0,2 % | 0,9 % | 0,9 % | 6,7 % | 9,2 % | 16,1 % | 28,1 % | 48,2 % | 52,1 % | 58,5 % |

Et celle du 20/08/2026, à 23 commits de données et 209 profils :

| fenêtre | 0 | 1 | 2 | 3 | 4 | 6 | 8 | 10 | 15 | 20 | 23 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dépôt (Mo) | 127 | 169 | 175 | 218 | 246 | 258 | 259 | 280 | 280 | 284 | 284 |

**Les deux tables saturent, mais par des bouts opposés.** Celle du 20/08 saturait
par le haut : la queue de l'historique était bon marché, une fenêtre généreuse ne
coûtait rien, d'où le « borner à 30 ne retire RIEN » de l'en-tête du script.
Celle du 28/08 sature par le bas : la queue est bon marché et **la tête est
chère**.

La cause tient en une ligne. Coût d'un commit de données mesuré en **pack
isolé** — `git pack-objects` sur `rev-list --objects <c> --not <c>^` —, les
28 commits coupés en deux moitiés de 14 :

| moitié | corpus | médiane | moyenne | min | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| 14 plus anciens (01 → 17/08) | 8 → 48 profils | **1,6 Mo** | 1,5 | 0,2 | 2,6 |
| 14 plus récents (18 → 27/08) | 129 → 476 profils | **29,3 Mo** | 34,6 | 0,1 | 78,6 |

Facteur 18 sur la médiane, à l'intérieur du même historique. C'est l'hypothèse de
calibrage écrite dans l'en-tête du script — « les commits de données […] ont été
écrits quand le corpus faisait 14 à 30 profils, ils ne pèsent presque rien » —
qui était juste pour la moitié basse et fausse pour la moitié haute.

**Mais la moitié basse est un artefact d'histoire.** Elle date de la phase de
développement du pipeline ; elle ne se reproduira pas. Toute conclusion tirée de
la forme de cette courbe — y compris « resserrer ne rapporte rien » — est
rétrospective et périmée d'avance.

## (b) La table prospective : le plateau

En régime permanent, les N commits de la fenêtre coûtent tous à peu près le même
prix. La courbe cesse de saturer et devient **linéaire** : `socle + N × marginal`.
Et la fenêtre devient le **seul** mécanisme qui borne la croissance du dépôt.

Il faut donc le coût **marginal réel** d'un commit conservé — pas le pack isolé,
qui ne peut pas se déltifier contre les arbres voisins. Mesuré le 28/08/2026 en
empilant les arbres du plus récent vers le plus ancien et en repackant à chaque
étape (`pack-objects` sur l'union des objets des arbres), sur le seul bloc en
régime de production :

| étape | commit | date | corpus | cumul | **marginal** |
| --- | --- | --- | ---: | ---: | ---: |
| socle | `f5e20b6` (arbre complet) | 28/08 | 481 | 153,6 Mo | — |
| +1 | `e87490c` | 27/08 | 476 | 163,5 Mo | **9,9 Mo** |
| +2 | `74c77c2` | 27/08 | 476 | 178,7 Mo | **15,1 Mo** |
| +3 | `bf063f2` | 26/08 | 476 | 193,9 Mo | **15,3 Mo** |
| +4 | `de23b62` (729 fichiers) | 24/08 | 476 | 209,1 Mo | **15,2 Mo** |

**Le coût marginal est de 10 à 15 Mo, pas de 29,3.** Les mêmes quatre commits
mesurés en packs isolés coûtent 22,3 à 78,6 Mo — un facteur 2 à 5 de plus.
Projeter le plateau sur les packs isolés le **double**.

Deux enseignements que la mesure impose :

- **le nombre de fichiers réécrits ne dit rien du coût.** `de23b62` réécrit
  729 fichiers — tout le corpus — et ne coûte que 15,2 Mo en marginal. Ce qui
  compte est le contenu **réellement nouveau**, pas le brassage ;
- **l'avertissement de #434 se vérifie, avec un facteur à jour.** Les 28 packs
  isolés totalisent 506 Mo alors que tout l'historique de données ne pèse que
  434 − 180 = 254 Mo dans le dépôt : facteur **2,0**.

D'où le plateau, `socle 180 Mo + N × marginal`, en donnant une **fourchette** et
non un point :

| fenêtre | 4 | 10 | 15 | 20 | **30** |
| --- | ---: | ---: | ---: | ---: | ---: |
| **(a) mesuré, rétrospectif** | 225 | 394 | 430 | 430 | *jamais atteinte* |
| (b) plateau, bas (10,4 Mo/commit) | 222 | 284 | 336 | 388 | **492** |
| (b) plateau, central (14,4) | 238 | 324 | 396 | 468 | **612** |
| (b) plateau, haut (16,0) | 244 | 340 | 420 | 500 | **660** |
| *pour mémoire, sur packs isolés (29,3)* | *297* | *473* | *620* | *766* | *1 059* |

La colonne 4 valide le modèle : 222–244 projetés contre 225 mesurés, parce que
les quatre commits les plus récents **sont déjà** en régime de production. C'est
au-delà que les deux lectures divergent, et **l'écart est le sujet** : passer de
30 à 15 ne gagnera pas 4 Mo mais **~220 Mo**.

**Le marginal suit la taille du corpus, et un peu moins que proportionnellement.**
En poursuivant l'empilement au-delà du bloc de production, la même mesure rend
11,5 Mo pour `68bc094` (229 profils) et 7,7 Mo pour `e4d71cf` (209 profils),
contre ~15,2 Mo à 476. Le corpus double (209 → 476, × 2,28) et le marginal fait
× 1,97. C'est ce qui permet d'extrapoler, et c'est aussi ce qui rend
l'extrapolation prudente.

Au passage, cette prolongation tue un croquemitaine : `e4d71cf` et `a125e9e`
sont les deux propagations `--no-merge` que #434 signalait comme
« structurellement exceptionnelles » et qui coûtent 47 et 67 Mo en pack isolé.
En marginal réel, `e4d71cf` coûte **7,7 Mo**. Une propagation ne crée pas de
contenu ; elle le recopie, et git le sait.

**Extrapolation à 752 membres** — le seul chiffre de cette entrée qui ne soit pas
mesuré. En appliquant le facteur 1,58 que #429 tire de la projection du push
complet (110,5 Mo à 476 → ~175 Mo à 752) au socle **et** au marginal : socle
~285 Mo, marginal 16 à 25 Mo, plateau à fenêtre 30 de **780 à 1 040 Mo**.

| | dépôt | marge contre les 2 Go de #429 |
| --- | ---: | ---: |
| aujourd'hui, mesuré | 434 Mo | **× 4,7** |
| plateau à 30, 479 profils | 490 – 660 Mo | **× 3,3** |
| plateau à 30, 752 membres (extrapolé) | 780 – 1 040 Mo | **× 2,0 à × 2,6** |

**C'est ça, la valeur de la fenêtre : le plafond qu'elle pose, pas ce qu'elle
économise.** Aujourd'hui elle ne fait rien ; en régime permanent elle sera le
seul mécanisme empêchant la croissance, et sa valeur décidera du plateau.

## Ce que « 30 » voulait dire, et ce qui a changé

Il faut lever un malentendu que l'issue installe : **30 n'a jamais été un budget
en octets.** #434 l'a tiré d'une règle de latence, écrite dans
[l'entrée #434](fenetre-historique-donnees.md) :

> fenêtre = cadence de pointe × période sans surveillance — 4 commits/jour ×
> 7 jours = 28, arrondi à 30.

Les octets n'intervenaient que dans la **conséquence** : #434 en déduisait un
plafond d'environ 2,9 Go à 752 profils — socle projeté 457 Mo plus 30 × 81 Mo de
coût moyen par run. Ce chiffre-là **surestime** : les 81 Mo sont de l'ordre de
grandeur d'un pack isolé, et le marginal réel mesuré est de 10 à 15 Mo à
479 profils.

Ce qui a changé n'est donc pas la règle, c'est son prix — et il ne se lit que sur
la table (b). La règle elle-même, re-mesurée, ne pousse pas dans le sens qu'on
croit :

- **la cadence de pointe est passée de 4 à 5 commits de données par jour**
  (le 18/08/2026) — la règle inchangée donnerait 5 × 7 = **35**, pas 30 ;
- mais **la cadence courante est de 0,56 commit/jour** (5 commits de données
  entre le 20/08 et le 28/08), parce que le `schedule: cron` de
  `generate-data.yml` est **commenté** : le workflow ne part qu'en
  `workflow_dispatch`. À ce régime, 30 commits couvrent une cinquantaine de
  jours, pas sept.

L'écart entre 4 et 35 selon la lecture qu'on fait de « cadence » est exactement ce
qui reste à trancher. Ce n'est pas une mesure manquante, c'est un choix — et
c'est aussi lui qui détermine **à quelle vitesse le plateau est atteint**.

## Question 1 — la valeur de la fenêtre

**Recommandation : garder 30, parce que le plateau qu'elle pose laisse encore de
la marge — et non parce que resserrer ne rapporterait rien.**

L'argument « descendre ne rend presque rien » est rétrospectif, et il est retiré.
Le bon argument est celui-ci :

1. **Le plateau tient.** 490 à 660 Mo à 479 profils, 780 à 1 040 Mo extrapolés à
   752 membres — sous les 2 Go du critère de sortie récrit en #429, et loin des
   5 Go déconseillés par GitHub.
2. **Mais le confort disparaît, et il faut le dire.** La marge passe de **× 4,7**
   aujourd'hui à **× 3,3** au plateau, et à **× 2,0 à × 2,6** à pleine échelle.
   Ce n'est plus un ordre de grandeur, c'est un facteur 2.
3. **La règle de latence, elle, ne demande pas moins de 30** — elle donnerait
   plutôt 35 à la cadence de pointe mesurée.

Si la fenêtre doit changer, **la re-dériver de la règle** (cadence de pointe ×
période sans surveillance) et **vérifier le plateau qu'elle pose**, dans cet
ordre. La table (b) dit ce que ça coûte ; elle ne dit pas ce dont on a besoin.

**Attention à l'exécution :** la valeur 30 est écrite à **deux endroits**, et un
arbitrage qui n'en changerait qu'un donnerait deux réponses différentes à la
question « la fenêtre est-elle contraignante ? » — `FENETRE=30` dans
`scripts/borner_historique_donnees.sh` et `FENETRE_COMMITS_DONNEES = 30` dans
`src/audit_volumetrie_profils.py`. Un test le verrouille désormais.

### Arbitrage rendu — 28/08/2026

**La fenêtre vaut un mois de données. 30 en est la conversion, pas la décision.**

La valeur ne change pas ; **sa justification, si**, et c'est le point.

#434 avait dimensionné 30 sur une **latence de détection** — « cadence de pointe
× période sans surveillance », une estimation de ce qui pourrait passer inaperçu.
L'arbitrage la remplace par une question sur le produit : **jusqu'où veut-on
pouvoir remonter dans les données publiées ?** Réponse : un mois.

C'est un meilleur fondement pour trois raisons. Il se relit sans reconstituer un
calcul ; il donne un critère de révision explicite (la cadence) ; et il ne
dépend pas d'une hypothèse sur la surveillance, qui n'était vérifiable par
personne.

**La conversion, mesurée le 28/08/2026 sur `origin/main` :**

| | |
| --- | ---: |
| Commits de données, 01/08 → 28/08 | **29 en 28 jours**, soit **1,04/jour** |
| Jours distincts portant au moins un commit | 15 sur 28 |
| Jour le plus chargé | 5 (18/08) |
| `schedule: cron` de `generate-data.yml`, une fois réactivé | **1 run/jour** |

Un mois fait donc **~30 commits dans les deux régimes** — le développement
d'aujourd'hui, tout en `workflow_dispatch`, et la production de demain, cadencée
par le cron. Que le chiffre soit inchangé n'est pas une coïncidence : le cron est
quotidien.

**Le plateau tient** : 490 à 660 Mo à 479 profils, 780 Mo à 1 Go extrapolés à
752 membres — sous les 2 Go du critère de sortie récrit en #429. Il n'y a pas de
conflit entre la profondeur voulue et le budget.

**Condition de révision, nommée.** Le seul cas où 30 cesserait de valoir un mois
est une cadence durablement supérieure à 1/jour — typiquement si les runs
manuels restent aussi fréquents qu'en août **une fois le cron actif** : à 2/jour,
la fenêtre ne couvrirait plus que quinze jours. Ça se voit sans effort, le step
« Fenêtre de rétention de l'historique de données » affichant le compte à chaque
run (question 2). Recalculer alors la conversion, pas la profondeur : c'est un
mois qui est décidé, pas trente.

**Ce que cet arbitrage ne dit pas** : ni l'unité dans laquelle la rétention se
compte (question 3), ni la destination de l'archive (question 4). Un mois de
profondeur ne vaut que si l'historique coupé est conservé quelque part — sans
quoi c'est un mois de mémoire et rien avant.

---

## Question 2 — borner automatiquement, ou rester manuel

**Recommandation : la réécriture reste manuelle ; c'est la détection qui doit
devenir automatique, et elle ne l'est pas.**

Les trois raisons de #434 de ne pas automatiser la réécriture tiennent toujours,
et la première est verrouillée par un test : `test_le_script_ne_pousse_jamais`.
Automatiser le push contredirait la garantie centrale du script. S'ajoute ce que
la procédure `--preparer` exige et qu'aucun script ne peut faire seul : choisir la
destination de l'archive, supprimer les autres branches distantes, prévenir les
porteurs de clones.

En revanche, **une des trois raisons de #434 vient de tomber.** « Le gain est nul
aujourd'hui » n'était vrai que tant que la fenêtre n'est pas contraignante : il ne
reste plus qu'**un commit de données** avant qu'elle le devienne. Et la lecture
prospective déplace l'enjeu : ce n'est pas le gain, c'est que **le bornage devient
l'unique frein à la croissance**. Une opération qui n'a jamais tourné en
conditions réelles va devenir la seule chose qui tienne le plateau.

Et l'automatisation qui manque n'est pas celle qu'on croit. #434 affirme : « ce
qui est automatisé, c'est la **détection** ». **Le code existe, mais rien ne le
lance** : `src/audit_volumetrie_profils.py` sait dire si la fenêtre est
contraignante, et il n'est invoqué par **aucun workflow** — seulement par
`scripts/mesure_volumetrie_roster.sh`, qui se lance à la main. La détection est
outillée, pas armée.

Ce qui est proposé, dans l'ordre de coût croissant :

1. **Armer la détection.** Un pas dans un workflow qui compte les commits de
   données (`git log --grep | wc -l`) et alerte au-delà d'un seuil. Coût : une
   commande, pas de clone. Surtout pas `--mesurer` en CI : il clone le dépôt
   entier et le repacke deux fois — le seul clone + `gc` a pris 1 min 52 s de
   temps réel et 3 min 37 s de CPU au 28/08, pour ~434 Mo dans un temporaire.
2. **Rendre le franchissement visible là où on regarde** — le résumé de run,
   plutôt qu'une alerte de plus.
3. **Ne jamais automatiser `--preparer` ni le push.**

### Arbitrage rendu — 28/08/2026

**La détection est armée ; la réécriture reste manuelle.**

Un step `Fenêtre de rétention de l'historique de données (#551)` est branché dans
`merge-and-pivot`, après le commit de données — compter ailleurs que là où l'on
committe, c'est compter un état qui n'est pas encore celui du dépôt. Il écrit
dans le résumé de run, et émet un `::warning::` quand la fenêtre est atteinte,
un `::notice::` à trois commits ou moins.

Trois propriétés, chacune verrouillée par `tests/test_ci_fenetre_retention.py`
et vérifiée mordante par mutation :

1. **La valeur de la fenêtre est lue, jamais recopiée.** Le step importe
   `FENETRE_COMMITS_DONNEES` et `MOTIF_COMMIT_DONNEES` depuis
   `src/audit_volumetrie_profils.py`. Un test interdit que la valeur apparaisse
   en dur dans le step : elle vit déjà à deux endroits tenus égaux par
   `tests/test_borner_historique_donnees.py`, un troisième domicile ferait
   répondre deux valeurs différentes à « la fenêtre est-elle contraignante ? ».
2. **Aucun workflow n'invoque `borner_historique_donnees.sh`.** La réécriture
   d'historique est irréversible pour tous les clones existants ; l'appeler
   depuis la CI contournerait la garantie que le script tient par test
   (`test_le_script_ne_pousse_jamais`).
3. **Aucun workflow n'appelle `--mesurer`.** Cette mesure clone le dépôt entier
   et le repacke deux fois — 1 min 52 s de temps réel et 3 min 37 s de CPU pour
   ~434 Mo au 28/08/2026. Compter des commits coûte une commande.

**Ce que le message ne fait pas** : il ne recopie pas la procédure de bornage,
il renvoie à cette entrée. Une procédure irréversible écrite à deux endroits
diverge, et c'est la version la moins relue qu'on suit sous pression.

État au moment de l'armement : **29 commits de données pour une fenêtre de 30**.

**Correction du 28/08/2026, même jour — le step tournait et ne voyait rien.** Au
run `33185097538`, il a affiché « Commits de données dans l'historique : **1** »
et conclu « non contraignante », alors que la fenêtre était pleine à 30 sur 30.

`actions/checkout` cloue l'historique à un commit (`fetch-depth: 1` par défaut)
et `merge-and-pivot` ne demande rien d'autre : `git log --grep` ne voyait que le
commit de données que le job venait d'écrire. Le compteur rendait donc toujours
0 ou 1, **l'alerte ne pouvait jamais se déclencher**.

C'est la faute reprochée à #434 — « le code existe, mais rien ne le lance » —
remplacée par une pire : **il tourne et ne voit rien**, ce qui a l'air de
marcher. Aucun des six tests ne pouvait l'attraper : ils vérifiaient que le step
existe, qu'il lit la constante, qu'il n'écrit pas la valeur en dur. Le défaut
était dans l'**environnement d'exécution**, pas dans le script.

Corrigé par un approfondissement **sans blobs** avant le comptage :

```
git fetch --quiet --filter=blob:none --deepen=$(( FENETRE + 10 )) origin
```

`--filter=blob:none` n'est pas une optimisation : le corpus pèse 4,85 Go, et
approfondir avec les blobs coûterait ~600 Mo pour ne lire que des sujets de
commit. Ce serait transformer un compteur en poste de coût — exactement ce que
la question 2 refusait pour `--mesurer`.

Trois tests neufs verrouillent la correction, vérifiés mordants : approfondissement
retiré → 3 échecs, profondeur écrite en dur → 1, filtre de blobs retiré → 1. Le
deuxième compte autant que le premier : une profondeur littérale se
désynchroniserait de la fenêtre le jour où celle-ci grandit, et le compteur
continuerait de rendre un nombre plausible.

---

## Question 3 — la rétention se compte-t-elle en commits ou en octets

**Recommandation : garder la coupure en commits, et déplacer le critère de
déclenchement vers les octets.** Ce sont deux choses différentes, et les confondre
est ce qui rend la question difficile.

Ce qui plaide pour les octets : un rapport de 1 à 603 entre le commit le moins
cher (`8ff8ff2`, 3 fichiers, 0,1 Mo) et le plus cher (`de23b62`, 729 fichiers,
78,6 Mo) **en pack isolé**.

Ce qui plaide contre, et qui est décisif — **la dispersion s'effondre quand on
mesure ce qui compte.** En marginal réel, les quatre commits de production coûtent
9,9 / 15,1 / 15,3 / 15,2 Mo : un rapport de 1 à 1,5, là où les mêmes en packs
isolés vont de 22,3 à 78,6. **En régime permanent, une fenêtre en commits redevient
une bonne approximation d'une fenêtre en octets**, parce que c'est le contenu
nouveau qui coûte, et qu'il est régulier.

S'ajoutent trois objections de forme :

- **une coupure en octets ne serait pas déterministe.** `_coupure` rend le
  (N+1)<sup>e</sup> commit de données ; c'est reproductible et vérifiable de tête.
  Une coupure « au premier commit qui fait passer le cumul sous X Mo » se déplace
  à chaque run ;
- **le cumul en octets facile à calculer est le mauvais** — les packs isolés,
  facteur 2,0 de surestimation. Une fenêtre bâtie dessus couperait deux fois trop
  tôt ;
- **le bon cumul ne se mesure qu'après coup**, par repack, soit plusieurs minutes
  de calcul par point.

D'où la forme proposée, **à deux bornes** :

- **un plancher en commits**, celui de la règle de latence — c'est un besoin
  forensique, il se compte en incidents ;
- **un plafond en octets**, celui déjà écrit en #429 : dépôt sous 2 Go après
  `gc --prune=now`, push complet sous 1 Go. C'est lui qui doit **déclencher**
  l'examen — et c'est sur le **plateau projeté**, pas sur la taille du jour, qu'il
  faut le lire.

Quand les deux bornes se contredisent, il n'y a pas de formule : c'est
l'arbitrage. Aujourd'hui elles ne se contredisent pas ; à 752 membres avec une
marge de × 2,0, la question sera moins confortable.

### Arbitrage rendu — 28/08/2026

**La rétention se compte en temps. Les commits en sont la conversion, les octets
ne sont qu'un contrôle — et ce contrôle se déclenche sur un événement, jamais sur
une horloge.**

La question telle qu'elle était posée — commits *ou* octets — est en partie
dissoute par l'arbitrage de la question 1 : la rétention ne se compte ni en
commits ni en octets, elle se compte en **mois**. Les commits sont l'unité de
coupure parce que c'est celle qui est déterministe ; les octets restent une
grandeur à surveiller, pas à définir.

**Pourquoi la coupure reste en commits**, indépendamment de cela :

- **la dispersion s'effondre quand on mesure ce qui compte.** En pack isolé, le
  rapport entre le commit le moins cher (0,1 Mo) et le plus cher (78,6 Mo) est de
  **1 à 603** — l'argument massif en faveur des octets. En **coût marginal réel**,
  les quatre commits de production coûtent 9,9 / 15,1 / 15,3 / 15,2 Mo : **1 à
  1,5**. En régime permanent, une fenêtre en commits *est déjà* une bonne
  approximation d'une fenêtre en octets ;
- **une coupure en octets ne serait pas déterministe.** « Le (N+1)<sup>e</sup>
  commit de données » se vérifie de tête et rend toujours le même point. « Le
  premier commit qui fait passer le cumul sous X Mo » se déplace à chaque run.

**Ce qui est écarté, et pourquoi.** Une alerte de taille automatique en CI coûte
**1 min 52 s de temps réel et 3 min 37 s de CPU** par mesure — elle clone le dépôt
entier et le repacke deux fois. C'est exactement ce que le step armé en question 2
évite en comptant des commits. Une alerte à ce prix, qui dit « tout va bien » à
chaque run, finit par n'être plus lue : on paierait trois minutes de CPU pour
fabriquer du bruit.

**Ce qui est retenu : la revérification déclenchée par un événement.** On remesure
quand une décision change la taille du corpus, pas à intervalle fixe. Aujourd'hui
la marge est de ×3 à ×4 (un mois pèse ~450 Mo contre 2 Go), et **un seul événement
de ce type est à l'horizon** :

| Événement | Effet attendu | Décision qui le porte |
| --- | --- | --- |
| Réouverture du Sénat | +300 membres, corpus × 1,6 | #528 |
| Passage du roster à pleine échelle au-delà de 752 | proportionnel | — |
| Doublement de la cadence de runs | fenêtre plus courte, pas plus lourde | question 1 |

Le jour où l'un survient : relancer `src/audit_volumetrie_profils.py` (hors CI) et
vérifier que la fenêtre d'un mois tient toujours sous les 2 Go du critère de #429.

**Ce que cet arbitrage n'affranchit pas** : la profondeur d'un mois ne vaut que si
l'historique coupé est archivé. C'est la question 4, et elle reste entière.

---

## Question 4 — où va l'archive, et qui garantit qu'elle a tourné

Cette question n'était pas dans l'issue ; elle change la nature des trois autres,
parce qu'elle transforme le bornage d'une **suppression** en un **déplacement**.

L'étape 2 de la procédure `--preparer` l'exige déjà — « archiver l'ancien
historique AILLEURS, sinon les SHA cités dans `docs/technical_decisions.md` et
dans les issues cessent de résoudre » — **sans dire où, ni comment on vérifie que
ça a marché**. Et la solution facile est interdite juste au-dessus : pousser le
tag sur le même dépôt garderait tout l'historique atteignable, et le gain serait
nul.

**Le périmètre, mesuré.** Sur les 42 fichiers `.md` suivis par git à `dc3ba83` et
les 253 corps d'issues du dépôt au 28/08 (tous états, commentaires exclus — la
vraie population est donc un peu plus large), 124 chaînes hexadécimales de
7 caractères ou plus ont été extraites ; **42 résolvent en commit** du dépôt.
`docs/technical_decisions.md` en porte 29 à lui seul.

**Combien en perd-on selon la fenêtre** — un SHA cité est perdu s'il est ancêtre
strict de la coupure :

| fenêtre | 0 | 2 | 4 | 6 | 8 | 10 | 12 | 15 | 20 | 24 | 27 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SHA cités qui cessent de résoudre (sur 42) | 39 | 35 | 31 | 14 | 10 | 10 | 10 | 6 | 2 | 0 | 0 |

**Et c'est encore une lecture rétrospective.** Le chiffre qui se transporte n'est
pas la profondeur en commits, c'est l'**âge calendaire** : les 42 commits cités
s'échelonnent du **12 au 28/08/2026**, soit **seize jours**, et 40 des 42 tiennent
dans les douze derniers.

| date du commit cité | 12/08 | 14/08 | 16/08 | 17/08 | 18/08 | 19/08 | 20/08 | 24/08 | 26/08 | 27/08 | 28/08 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SHA cités | 2 | 1 | 3 | 3 | 1 | 8 | 16 | 1 | 1 | 5 | 1 |

**Le besoin forensique s'exprime en jours ; la fenêtre se compte en commits ; le
facteur de conversion est la cadence.** C'est exactement la règle de #434, et
c'est ce qui la valide comme forme, indépendamment de sa valeur :

| cadence | 16 jours de citations valent… | une fenêtre de 30 couvre… |
| --- | ---: | ---: |
| pointe mesurée, 5/jour (18/08) | 80 commits | 6 jours |
| 1/jour (`cron` quotidien réactivé) | 16 commits | 30 jours |
| courante, 0,56/jour (`workflow_dispatch`) | 9 commits | 54 jours |

Autrement dit : **en régime de production à un run par jour, une fenêtre de 30
couvre confortablement le besoin forensique observé** ; c'est en régime de rafale
qu'elle serait courte. Et la corrélation entre gain et coût forensique subsiste,
mais sur une pente linéaire, non sur un plateau : chaque commit retiré rendra
~10 à 15 Mo **et** rapprochera la coupure de la zone citée.

**La forme, évaluée contre la raison invoquée par le script** — que les SHA cités
continuent de résoudre, pas que les données restent au chaud :

| forme | les SHA résolvent | vérifiable par un tiers | coût |
| --- | --- | --- | --- |
| **dépôt nu privé sur GitHub** | oui, `git log` / `git show` normaux après ajout d'un remote | **oui** | un push de ~433 Mo, un dépôt de plus |
| **bundle** (`git bundle create`) | seulement après un `git fetch` depuis le bundle | non, sauf à distribuer le fichier | un fichier de ~433 Mo à héberger |
| **tarball des données** | **non** — perd le graphe et les SHA | non | — |

Le tarball est à **écarter explicitement** : il ne sert pas la raison invoquée.

**La distinction qui décide de l'ordre.** Un miroir sur le disque local répond à
la capacité de récupération de l'humaine, mais **pas** à la raison écrite dans le
script : quelqu'un qui lit « mesuré sur `de23b62` » dans une issue et veut
vérifier n'est pas aidé par un disque qu'il n'a pas.

**Recommandation, dans cet ordre :**

1. **Un dépôt d'archive privé sur GitHub**, poussé en miroir avant tout push
   forcé. C'est la forme qui sert la raison écrite. Son URL doit être consignée
   dans cette entrée le jour où il existe, sinon l'archive est introuvable.
2. **Un miroir local**, en second, pour la reprise après incident.
3. **Une vérification après archivage, sinon c'est un rituel.** Reprendre les
   42 SHA effectivement cités et confirmer que chacun résout dans l'archive
   (`git -C <archive> cat-file -t <sha>` = `commit`).
4. **Jamais de tag d'archive sur `origin`** — n'importe quelle ref distante
   oubliée ré-épingle l'ancien historique et annule le gain.

### Arbitrage rendu — 28/08/2026

**L'archive de référence est Software Heritage. Un miroir local est un confort,
pas une sécurité.**

**Pourquoi pas un second dépôt GitHub**, qui était la recommandation initiale de
cette section. Une archive accumule tout ce qu'on coupe, indéfiniment : elle a
donc la même croissance que le dépôt principal, sans le coût de checkout. À
~450 Mo par mois depuis les 415 Mo mesurés le 28/08 :

| | Taille projetée | |
| --- | ---: | --- |
| aujourd'hui | 0,4 Go | |
| +6 mois | 3,0 Go | dépasse les 2 Go du critère de #429 |
| **+12 mois** | **5,7 Go** | **dépasse les 5 Go déconseillés par GitHub** |
| +24 mois | 11,0 Go | |

Un dépôt d'archive GitHub franchirait le seuil recommandé **en un an**, et il
faudrait le borner à son tour. On aurait résolu le problème en le recopiant.
**Une archive qui grandit sans borne ne peut pas vivre sous un hébergeur qui
borne.**

**Ce que Software Heritage apporte, vérifié le 28/08/2026 par l'API :**

- **le SHA git EST l'identifiant.** Une révision interrogée par son SHA rend le
  même hash : `/api/1/revision/<sha>/`. Une citation comme « mesuré sur
  `deb28a7` » reste donc vérifiable **par un tiers**, après la coupure ;
- **aucun plafond de taille annoncé.** La seule limite exposée est un débit de
  **120 requêtes/heure** en anonyme — une limite de lecture, pas de stockage. Et
  ils archivent `torvalds/linux` et `chromium/chromium`, tous deux `full` au
  27 et 24/08 : l'échelle de ce dépôt ne pose aucune question ;
- **c'est une sauvegarde complète, pas seulement une preuve.** La route
  `/api/1/vault/git-bare/` reconstruit un **dépôt git nu** depuis une révision
  archivée — testée `status: done`, `fetch_url` servie. Après récupération,
  `git log`, `git diff` et `audit_diff_profils --ref` fonctionnent normalement.

**Ce qui n'a pas pu être vérifié** : leur page de politique n'est pas
récupérable automatiquement (protection anti-robot). Il n'existe donc **pas de
garantie écrite** d'absence de quota — seulement l'absence de quota annoncé dans
l'API et la preuve par l'usage. Consigné comme tel, pas comme un fait établi.

**Le miroir local, et son rôle exact.** Il ne sauve de rien que SWH ne sauve
déjà : il rend la récupération *immédiate* là où le vault demande une cuisson
asynchrone. C'est un raccourci, pas une sécurité — et il ne survit pas au
matériel, contrairement à SWH. Coût mesuré : ~5,7 Go la première année sur
131 Go libres au 28/08. À prendre si l'on veut, à laisser sans risque.

**La règle qui l'annule s'il est mal fait** : un miroir doit être **additif
seulement**. `git clone --mirror` suivi d'un `git remote update` **supprime** les
refs disparues en amont — exactement ce que l'archive existe pour garder. On y
pousse le tag avant chaque coupure ; on n'y synchronise jamais. Le mot « miroir »
suggère précisément l'inverse de ce qu'il faut faire.

**État opérationnel — archivage déclenché le 28/08/2026.** La demande « Save Code
Now » a été soumise à **14:51:37 UTC** et acceptée ; la **visite n°1** de l'origine
`https://github.com/stephieED/Empreinte-politique-src` a été créée à **14:51:47**,
ingestion en cours. Le filet est donc posé **avant** toute coupure — l'ordre
inverse serait irrécupérable.

Vérifier périodiquement que la visite conclut en `full` et que son `snapshot`
n'est plus `null` :

```
curl -s "https://archive.softwareheritage.org/api/1/origin/\
https://github.com/stephieED/Empreinte-politique-src/visit/latest/"
```

**Le renouvellement est automatique, mesuré.** Une fois l'origine connue de
Software Heritage, elle entre dans leur planificateur. Relevé le 28/08/2026 sur
`github.com/git/git` : **362 visites**, dont douze entre le 26/04 et le 28/08,
soit **une tous les 11,3 jours** en moyenne, toutes en statut `full`, sans
qu'aucune ne soit demandée. « Save Code Now » ne sert donc qu'à deux choses :
faire entrer une origine inconnue, et forcer une visite immédiate — ce qui est
exactement le besoin **juste avant une coupure**, où l'on ne peut pas attendre
onze jours.

Cette cadence est une **observation, pas une garantie** : elle est relevée sur un
dépôt très actif et très référencé, et rien dans l'API n'annonce de politique de
fréquence. À revérifier sur ce dépôt-ci une fois quelques visites accumulées.

**L'ordre, non négociable** : archiver, vérifier que les SHA cités résolvent,
**puis** couper. Software Heritage archive ce qui est atteignable au moment de
son passage ; après la coupure, c'est perdu. L'étape 2 de la procédure
`--preparer` porte désormais ce déroulé.

### Outillage — et ce que la vérification a trouvé le premier jour (#568)

Le point 3 de la recommandation ci-dessus — « une vérification après archivage,
sinon c'est un rituel » — était **un geste décrit en prose**, à l'étape 2b de la
procédure `--preparer`. Il est désormais une commande :
`python3 src/verifier_archivage_swh.py`, que l'étape 2b appelle.

**La boucle `curl` remplacée ne pouvait pas tourner telle quelle**, et deux
raisons valent d'être notées parce qu'elles ne se voient qu'en essayant. Elle
itérait sur `git log --format=%H`, soit les 677 commits de `main`, pour un quota
de 120 requêtes/heure : près de six heures de temporisation pour une population
qui n'est pas celle qui compte. Et le heredoc de la procédure est un `cat <<FIN`
non quoté, donc `$(git log --format=%H)` y était **substitué à l'affichage** :
la procédure imprimait la liste des 677 commits au milieu de ses propres
instructions. Personne ne l'avait vu parce que personne n'a encore déroulé cette
étape — ce qui est le sujet de #566.

**La population, remesurée le 28/08/2026** — elle bouge, et c'est l'argument
pour l'outiller plutôt que de la recopier :

| | relevé ci-dessus (`dc3ba83`) | script, le même jour |
| --- | ---: | ---: |
| fichiers `.md` suivis | 42 | 42 |
| corps d'issues | 253 | 260 |
| chaînes hexadécimales de 7+ caractères | 124 | **135** |
| dont résolvent en commit | 42 | **47** |

Le tri est fait par `git cat-file --batch-check` en une invocation : le reste
est fait d'horodatages, d'identifiants de run GitHub et de sommes de contrôle.
Les commentaires d'issues restent hors périmètre — `gh issue list` ne les rend
pas —, et la sortie le dit désormais plutôt que de le laisser croire.

**Résultat sur l'état réel, 28/08/2026 : 46 des 47 SHA cités résolvent**, dans
une visite `full` (snapshot `6ad9782`). Verdict VÉRIFIÉ : **aucun trou
d'archive**. Le quarante-septième est `efed279`, cité dans ce fichier, et il
révèle une situation que cette section n'avait pas prévue.

**Une quatrième situation : la citation orpheline.** `efed279` est un commit de
la PR #478 qui n'est atteignable depuis **aucune ref** — ni branche, ni tag, ni
`origin/*`. La branche de la PR a été récrite avant fusion (`refs/pull/478/head`
vaut `721cf64`), et le commit ne survit que comme objet pendant dans ce clone.
GitHub ne l'a jamais servi depuis une ref ; Software Heritage archive ce qui est
atteignable depuis les refs de l'origine ; il n'a donc **jamais pu être
archivé**, et relancer « Save Code Now » n'y changera rien.

Ce n'est pas un défaut d'archive, c'est un défaut de citation — et elle est
**déjà cassée pour un tiers aujourd'hui**, sans qu'aucune coupure ait eu lieu.
Le script la nomme à part, sous l'étiquette CITATIONS ORPHELINES, et **ne bloque
pas** dessus : la coupure ne lui fait rien perdre, et un verdict rouge permanent
finirait par ne plus être lu. Ce qui bloque, c'est un SHA atteignable depuis une
ref et pourtant absent de l'archive — celui-là, la coupure le perdrait
vraiment.

**« Atteignable » veut dire quelque chose de précis, et s'y tromper coûte.** Le
script ne balaie que `refs/heads`, `refs/tags` et `refs/remotes/origin` — ce
qu'une origine offre à un archiveur. `refs/pull/<n>/head` en est exclue (GitHub
la sert, Software Heritage ne l'archive pas), et `refs/claude/*` ou `refs/stash`
aussi : les compter ferait passer pour un trou d'archive un commit que l'origine
n'a jamais porté. Ça reste une approximation — une branche locale déjà supprimée
en amont compte encore —, et **elle penche du bon côté** : elle peut rendre
MANQUANT ce qui est orphelin, jamais l'inverse. Un blocage de trop, jamais une
autorisation de trop.

C'est la même discipline que la distinction visite/manque, appliquée une fois de
plus : trois causes différentes d'un même symptôme, trois gestes différents.

| verdict | code | ce qu'on fait |
| --- | ---: | --- |
| VÉRIFIÉ | 0 | visite `full`, tout ce qui est archivable résout. Couper. |
| MANQUANTS | 1 | trou d'archive réel. Relancer 2a, revérifier. |
| INDÉTERMINÉ | 2 | visite non conclue, quota, réseau. **Rien n'est établi** : réessayer. |

**Le quota est plus serré qu'il n'y paraît, et c'est mesuré.** Une passe complète
coûte 48 requêtes (1 visite + 47 révisions) sur les 120/heure : **deux passes par
heure au plus**, et la fenêtre est une heure pleine, pas un débit lissé. Lancée
sur un seau déjà entamé, la vérification a temporisé deux fois — 702 s puis
1 504 s — et l'a annoncé à chaque fois, comme #568 le demandait. La passe
complète a duré **37 min 22 s** pour 3,7 s de CPU : c'est de l'attente, pas du
calcul, et c'est le prix d'une vérification lancée sur un seau déjà entamé.

Deuxième constat du même relevé : la route `/origin/.../visit/latest/` a **son
propre seau, à 700 requêtes/heure**. Lire ses en-têtes dans le compteur des
révisions ferait croire à six fois plus de marge qu'il n'y en a.

Troisième, et c'est un défaut que seule l'exécution réelle pouvait sortir :
`X-RateLimit-Remaining` est une **photographie de la réponse précédente**, et
elle se périme à l'horodatage `reset`. Sans cette distinction, le script a
annoncé vingt « quota épuisé — attente de 1 s » d'affilée après un reset,
chacune suivie d'une requête qui passait très bien. Un garde-fou qui crie sans
raison finit par n'être plus lu — et ce bavardage masquait précisément les deux
temporisations réelles de la même exécution.

**Rien de tout cela ne tourne en CI**, conformément à la question 2 : la
vérification est un geste de pré-coupure, pas un contrôle de run. Un test
l'interdit explicitement — la brancher dans un workflow consommerait à chaque
push un quota anonyme partagé, et ferait échouer des jobs sur l'état d'un
service tiers. Les 41 tests de `tests/test_verifier_archivage_swh.py` portent sur
des entrées simulées ; aucun ne joint l'API.

---

## Ce qui n'a pas pu être établi

- **Le coût marginal n'est mesuré que sur quatre commits**, tous entre le 24 et le
  28/08 à 476-481 profils. C'est le seul bloc en régime de production disponible ;
  quatre points, c'est peu. La fourchette 10 à 16 Mo en tient compte, mais elle
  est étroite parce que l'échantillon l'est.
- **Le marginal grandira, et le taux exact n'est pas établi.** Sa dépendance au
  corpus est mesurée sur trois points seulement (209, 229, 476 profils) et sur
  une seule direction de croissance — l'ajout de membres. Le Sénat rouvrant
  ajouterait ~300 membres (#553) et l'accumulation de la XVII<sup>e</sup>
  législature est en cours : ce sont deux régimes différents, et le second
  (plus d'activité par membre) n'est pas couvert par cette mesure. Le facteur
  1,58 retenu vient de la projection de push de #429 ; les trois points mesurés
  suggèrent qu'il **majore** légèrement, donc que le plateau projeté à 752 est
  plutôt un majorant.
- **La cadence future** est le paramètre dont dépend le reste : elle bascule d'un
  facteur ~10 selon que le `schedule: cron` de `generate-data.yml` est réactivé.
  Ça ne se mesure pas, ça se décide.
- **Un fork GitHub est probablement disqualifié comme archive** : les forks
  partagent leur réservoir d'objets avec le dépôt d'origine. **Non vérifié** — à
  traiter comme une raison de choisir un dépôt indépendant, pas comme un fait.
- **La taille annoncée par l'API GitHub** n'a pas été relevée ce jour. Le rappel
  de #434 vaut toujours : un push forcé ne la fait pas baisser tant que GitHub n'a
  pas ramassé, et ce `gc` n'est ni annonçable ni déclenchable.
- **On ne sait pas combien de citations orphelines s'écriront** (#568). Une sur
  les 47 en est une aujourd'hui — `efed279`, commit d'une branche de PR récrite —
  et rien ne mesure à quelle fréquence une décision se documente sur un SHA
  qui ne survivra pas à la fusion de sa propre PR. Le script les nomme quand il
  en trouve ; il ne les empêche pas. Le geste qui les éviterait — citer le
  commit de fusion plutôt que celui de la branche — n'est écrit nulle part, et
  n'est pas décidé ici.
- **Les commentaires d'issues restent hors du périmètre vérifié** (#568), comme
  du relevé de population ci-dessus. `gh issue list` ne les rend pas et les
  tirer coûterait une requête API par issue. Un SHA cité uniquement dans un
  commentaire n'est donc vérifié par rien.

---

