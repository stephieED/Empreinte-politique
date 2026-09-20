<a id="cache-completude-interventions-550"></a>
# La clé de cache AN porte la COMPLÉTUDE, et la sauvegarde devient explicite (#550) (2026-08-28)

`2026-08-28`

> **En bref** — une clé doit décrire la complétude de ce qu'elle protège.

Quatrième reprise de la même forme : **une clé de cache qui ne décrit pas ce
qu'elle protège.**

| Forme | Issue | Ce que la clé ignorait | Conséquence mesurée |
| --- | --- | --- | --- |
| 1re | #424 | les répertoires réellement couverts | ~438 Mo re-téléchargés par run |
| 2e | #498 | (même forme, sur les interventions) | 12 shards tués sans rien publier |
| 3e | #505 | le mode d'extraction (`-interv`) | 650,5 Mo × 7 shards par run |
| **4e** | **#550** | **la complétude du CONTENU indexé** | **113-219 s × 7 shards par run** |

## Ce qui s'est passé, relevé dans les journaux

Run `33100214165` (27/08/2026, shard `jean-luc-melenchon`, job `98616438651`) —
quatre archives tombent en `IncompleteRead` :

```
[!] Débats Syceron législature 16 indisponibles : IncompleteRead(7 785 604 lus, 49 768 099 attendus)
[!] Index des débats Syceron (législature 16) NON mis en cache : aucun compte rendu lisible
[!] Débats Syceron législature 15 indisponibles : IncompleteRead(16 897 786 lus, 132 057 083 attendus)
[!] Questions QE législature 15 indisponibles : IncompleteRead(...)
[!] Questions QE législature 14 indisponibles : IncompleteRead(...)
```

Les gardes de #505/#510 font exactement leur travail : **rien de tout cela n'est
mis en cache**. Et pourtant, à 17:55:27, le même shard écrit
`Cache saved with key: public-data-cache-an-2026-W35-interv` — **114 481 867 o**
(taille confirmée par l'API des caches du dépôt) dont, côté interventions :

```
.cache/syceron_an/17/index_par_acteur/
.cache/questions_an/16/index_par_acteur.json
.cache/questions_an/17/index_par_acteur.json
```

Une législature de débats sur trois, deux législatures de questions sur quatre —
sous une clé qui ne dit que la semaine et le mode.

Deux heures plus tard, run `33110395663`, job `98652271090` (`jean-luc-melenchon`,
premier shard de la matrice) :

```
19:56:47  Cache hit for: public-data-cache-an-2026-W35-interv
19:56:49  Cache Size: ~109 MB (114481867 B)
19:57:02  -> Téléchargement des débats Syceron ... /16/vp/syceronbrut/syseron.xml.zip
19:57:57  -> Index des débats Syceron (législature 16) : 605 CR, 656 acteurs, 305 862 interventions
19:58:05  -> Téléchargement des débats Syceron ... /15/vp/syceronbrut/syseron.xml.zip
20:00:33  -> Index des débats Syceron (législature 15) : 1 562 CR, 687 acteurs, 633 764 interventions
20:02:40  Cache hit occurred on the primary key public-data-cache-an-2026-W35-interv, not saving cache.
```

**55 s et 147 s d'indexation, jetées à la fin du job** — et refaites à
l'identique par les six shards porteurs suivants, `max-parallel: 1` les faisant
défiler l'un après l'autre devant la même entrée partielle.

## Pourquoi aucune des deux corrections évidentes ne suffit seule

**Ajouter la complétude à la clé, et rien d'autre.** `actions/cache` combiné ne
connaît **qu'une** clé : celle qu'il restaure est celle qu'il sauvegarde. À la
fin du job il écrit ce qui est sur le disque, complet ou non, sous cette clé —
donc sous une clé qui annoncerait une complétude que l'entrée n'a pas. C'est mot
pour mot le mécanisme du 27/08, avec un nom plus long.

**Passer en `restore` + `save` explicite, et rien d'autre.** Une entrée de cache
GitHub est identifiée par `(clé, version)` et n'est **jamais réécrite** — la
table de [#cache-mode-interventions-505](cache-mode-interventions-505.md) le montre
déjà en creux, avec trois entrées coexistant sous `public-data-cache-an-2026-W34`
parce que leurs `path`, donc leurs versions, diffèrent. Sauvegarder explicitement
sous la clé fautive de la semaine serait donc refusé jusqu'au lundi suivant. Et
un run qui échouerait à tout indexer ne sauvegarderait plus rien du tout, y
compris `acteurs_historique_an` et `scrutins_an` : on perdrait le réchauffement
que #424 a établi.

**Les deux ensemble** se répondent : la complétude dans la clé donne une clé
libre à écrire, la sauvegarde explicite permet d'écrire sur une clé autre que
celle restaurée.

## Ce qui est retenu

1. **Une empreinte de complétude, lisible, suffixée à la clé en mode
   interventions** — `syc15.16.17-q14.15.16.17` pour un cache complet,
   `syc17-q16.17` pour l'entrée du 27/08. Produite par
   `src/cache_an_empreinte.py`, **dérivée des constantes du code**
   (`SYCERON_AVAILABLE_LEGISLATURES`, `AN_QUESTIONS_PATH`) et non d'une liste
   recopiée dans le workflow : recopiée, elle deviendrait fausse à l'ouverture
   de la 18e législature, l'empreinte attendue ne serait plus jamais atteinte,
   et chaque shard se remettrait à sauvegarder. Pas un hachage : la clé se lit
   dans l'interface Actions, et c'est là qu'on voit d'un coup d'œil qu'une
   entrée est partielle et ce qui lui manque.
2. **On restaure sur la complétude ATTENDUE, on sauvegarde sur la complétude
   ATTEINTE.** Un shard qui n'a pu indexer que deux législatures sur trois écrit
   une entrée dont la clé le dit ; le shard suivant la restaure par
   `restore-keys`, complète la troisième et sauvegarde sous la clé complète. La
   semaine se réchauffe de proche en proche au lieu de se figer sur son premier
   échec.
3. **L'empreinte est calculée sur le DISQUE, exactement sur les fichiers que le
   `path:` capture** (`.cache/questions_an/*/index_par_acteur.json`,
   `.cache/syceron_an/*/index_par_acteur`) — jamais sur ce que le code croit
   avoir écrit. C'est la seule façon qu'elle ne puisse pas mentir sur le contenu
   de l'entrée, et un test compare les deux listes de motifs.
4. **La sauvegarde est le dernier step du job, après la publication et l'upload
   du profil.** L'archivage est le seul poste qui puisse s'étirer, et le
   `timeout-minutes` le couvre : coupé, il ne coûte qu'une entrée de cache,
   jamais un profil. C'est #498 pris à l'envers, où 12 shards tués avaient tous
   publié « 0 profil(s) ». Même raison pour son `continue-on-error: true`.
5. **Rien n'est sauvegardé si la clé n'a pas changé** : la condition compare
   `cache-matched-key` à la clé qui serait écrite. Égales, l'entrée existe déjà
   et le seul effet d'un appel serait de payer l'archivage pour un refus — le
   cas de tous les shards qui suivent celui qui a complété l'index.
6. **Les gardes de #505/#510 ne sont pas touchées.** Le refus de mettre en cache
   une législature illisible est juste : c'est lui qui garantit qu'une
   législature comptée dans l'empreinte a été lue en entier. Ce que #550 corrige
   n'est pas le refus, c'est l'entrée que ce refus laissait passer pour
   complète. `tests/test_cache_an_empreinte.py` éprouve la jonction sur les
   **vrais** constructeurs d'index, pas sur une doublure de l'empreinte : la
   garde et l'empreinte ne peuvent plus diverger sans qu'un test tombe.

## Le gain, et ce qu'il n'est pas

Population : les 7 shards porteurs du run `33110395663`, colonne
« réindexation » (Syceron 16 + Syceron 15) de
[#budgets-extract-an-remesures-546](budgets-extract-an-remesures-546.md).

| | Aujourd'hui | Après #550 |
| --- | ---: | ---: |
| Shards qui réindexent | 7 | 1 |
| Secondes de réindexation par run | 1 110 | 202 |
| **Économie d'horloge de collecte par run** | — | **908 s ≈ 15 min** |

Le coût d'indexation **ne disparaît pas** : il cesse d'être payé sept fois. Le
shard qui construit l'index le paie en entier, et pour lui rien ne change.

Ce que cela donne, shard par shard, en horloge de collecte (mesurée moins
réindexation) contre le budget de 250 s :

| Shard | Mesuré | Réindexation | Après |
| --- | ---: | ---: | ---: |
| jerome-guedj | 247\* | 205 | 42 + la législature de questions que le budget avait coupée |
| marine-le-pen | 244 | 157 | 87 |
| bruno-retailleau | 208 | 129 | 79 |
| edouard-philippe | 208 | 142 | 66 |
| gabriel-attal | 200 | 148 | 52 |
| laurent-wauquiez | 166 | 127 | 39 |

`*` = tronqué. Les six tiennent très largement. **`jean-luc-melenchon` est le cas
à ne pas surestimer** : il est le PREMIER shard de la matrice (démarré à
19:53:48), donc celui qui construit l'index. Coût complet d'une construction à
froid, mesuré : **42 s** pour la 17e législature (run `33100214165`, 17:53:37 →
17:54:19), **55 s** pour la 16e et **147 s** pour la 15e (run `33110395663`) =
**244 s**, soit la quasi-totalité du budget de 250 s. **Le premier shard d'un run
qui construit l'index restera donc tronqué** — perte déclarée, comme #514 l'a
conçu. Dès que l'index de la semaine est complet à son démarrage, en revanche,
son horloge tombe à ~130 s et les **sept** profils tiennent dans le budget
actuel.

Autrement dit : la troncature n'est plus attachée à `jean-luc-melenchon` mais au
premier shard d'un run qui doit (re)construire l'index — au plus un par semaine.

## Ce qui n'a pas pu être établi sans un run réel

- **Le poids d'une entrée complète.** L'entrée du 27/08 pèse 114 481 867 o avec
  UNE législature de débats sur trois ; le dépôt utilise 826 173 608 o au total
  (13 entrées, mesuré le 28/08) contre un quota de 10 Go. Le quota n'est
  manifestement pas la contrainte active, mais le poids d'une entrée complète
  n'est pas mesuré, et le nombre d'entrées par semaine passe de 1 à « une par
  état de complétude réellement atteint » — 2 ou 3 dans les scénarios connus.
- **La durée de l'archivage.** Mesurée à **5,2 s** pour les 114 Mo du 27/08
  (17:55:21,87 → 17:55:27,06). Une entrée complète est plus lourde et surtout
  plus fragmentée (l'index est un répertoire de ~700 tranches par législature).
  Cette durée n'entre dans **aucun** des trois postes de l'interlock de #546 —
  préambule, budget, unité en vol — et n'y entrait pas davantage avant #550 :
  l'omission est antérieure, elle devient simplement atteignable maintenant que
  la sauvegarde a de nouveau lieu. Marge disponible : **15 s** (585 s
  provisionnés sur 600). À remesurer au premier run réel ; c'est le seul chiffre
  de cette entrée qui pourrait imposer un re-dimensionnement.
- **Le budget de 250 s n'est pas retouché**, ni le `timeout-minutes` de 10 min.
  Ils ont été posés par #546 sur des horloges mesurées AVANT cette correction ;
  les remesurer demande un run réel, et poser un chiffre sur une mesure périmée
  est exactement la faute que #546 a corrigée.

## Ce qui est écarté, et pourquoi

**Indexer une fois pour toutes les shards, dans un job dédié en amont** (piste 3
de l'issue). Ce n'est pas une alternative à la correction ci-dessus : **c'en est
un consommateur**. L'index pèse 1 664,8 Mio pour les trois législatures — il ne
se transmet pas par artifact, il se transmet par le cache, donc par la clé, donc
il lui faut d'abord une clé qui ne mente pas. Un tel job ajouterait par ailleurs
un préambule complet (146-197 s mesurés sur les 8 shards de `33110395663`) au
chemin critique du run, là où la correction retenue paie l'indexation dans un job
qui existe déjà et a déjà payé son préambule.

Ce qu'il apporterait, et que #550 n'apporte pas : sortir la construction de
l'index du budget d'un shard, donc supprimer la troncature du shard constructeur.
**Condition de réouverture, à mesurer** : si un run réel montre que le shard
constructeur est tronqué chaque semaine — c'est-à-dire que la reconstruction
hebdomadaire coûte un profil — alors le job dédié devient la façon de payer ce
coût hors de tout budget.

La raison pour laquelle #505 écartait ce même job — « côté Syceron, il
construirait un index vide » — **est morte** : c'était le défaut #510, corrigé le
27/08, et l'index porte désormais 1 227 415 interventions indexables. L'argument
ci-dessus est donc neuf, pas une reconduction.

**Étendre l'empreinte à `acteurs_historique_an` et `scrutins_an`**, également
couverts par la même clé. Leur complétude n'est pas observable sur le disque de
la même façon : les législatures figées (`AN_SCRUTINS_LEGISLATURES_FIGEES`) sont
matérialisées **dans le dépôt**, pas dans `.cache`, si bien qu'une absence sous
`.cache/scrutins_an` n'y est pas un manque. Aucun défaut mesuré ne les implique.
Les ajouter demanderait d'abord d'établir ce qu'est un état complet pour eux —
c'est une autre mesure, pas un ajout gratuit.

## Ce qui reste latent, et n'est pas traité ici

> **TRAITÉ depuis, par #555** :
> [#cache-fraicheur-interventions-555](cache-fraicheur-interventions-555.md). Le
> phénomène décrit ci-dessous a été mesuré (run `32738726729`, 24/08, une entrée
> du 20/08 resauvegardée sous la clé du 24/08 en 18 s) et borné. Une nuance de
> ce paragraphe y est corrigée : le modèle d'`AMENDEMENTS_FRAICHEUR_FILENAME`
> a été écarté — un fichier sentinelle doit entrer dans le `path:` du step de
> cache pour survivre au run, donc en change la *version*, donc coûte une
> semaine de cache froid à déployer. Le marqueur retenu est
> `cache-matched-key`, la clé effectivement restaurée, qui porte déjà sa semaine
> et ne coûte rien.

**`restore-keys: public-data-cache-an-` traverse les semaines.** À défaut d'entrée
de la semaine, un run restaure la plus récente entrée AN, toutes semaines et tous
modes confondus. Si c'est une entrée d'interventions de la semaine précédente, le
code ne rouvre **aucune** archive — `_read_cached_interventions_syceron_acteur` et
`_build_acteur_questions_index` court-circuitent le réseau dès que l'index existe
— et l'entrée est re-sauvegardée sous la clé de la nouvelle semaine. La clé
hebdomadaire est le **seul** mécanisme de fraîcheur de ces deux index (les
amendements, eux, portent un `fraicheur.json`) : une chaîne de restaurations par
préfixe peut donc reporter indéfiniment un index vieux d'une semaine, sur une 17e
législature qui, elle, continue de siéger.

Ce défaut est **antérieur à #550 et inchangé par lui** : la ligne `restore-keys`
est reprise telle quelle, #550 n'y ajoute qu'un préfixe plus spécifique en tête.
Il ne se déclenche que si aucune entrée de la semaine n'existe encore au moment
du run — en pratique le run quotidien en mode par défaut écrit
`public-data-cache-an-<semaine>` très tôt, ce qui le masque, mais c'est un
accident d'ordonnancement, pas une garantie. **À ouvrir en issue propre** : ce
qui manque n'est pas une clé mais un marqueur de fraîcheur à côté de l'index, sur
le modèle de `AMENDEMENTS_FRAICHEUR_FILENAME`.

---

