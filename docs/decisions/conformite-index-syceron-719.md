<a id="conformite-index-syceron-719"></a>
# Un index Syceron en cache est un parsage en cache, et l'existence n'y est pas la conformité (#719) (2026-09-02)

`2026-09-02`

> **En bref** — le run `33652389393`, lancé avec `collect_interventions=true` pour appliquer #710, a **réussi** et n'a corrigé **aucun** des 2 041 sujets de créneau (chiffre pour chiffre, 14 817 interventions à sujet inchangées sur un corpus passé à 680 298) : les profils bruts qu'il venait d'écrire portaient **0** clé `sujet_code_grammaire` sur les 3 963 de `gabriel-attal` et les 2 376 d'`edouard-philippe`, parce que `.cache/syceron_an/<leg>/index_par_acteur` **n'est pas une archive mise de côté mais le produit de `parse_syceron`** — un index en cache est un *parsage* en cache, et sa clé `public-data-cache-an-<semaine>-interv-<empreinte>` dit quand, dans quel mode et sur quelles archives l'entrée a été écrite (#550), **jamais avec quel parseur** ; les deux gardes existantes ne couvraient pas le cas (#505/#510 refusent un index construit sur une archive absente ou n'ayant résolu aucun acteur, #550 une entrée écrite pendant une panne d'archive — aucune ne refuse un index correct écrit par un code périmé) ; la règle manquante existait pourtant **deux fois** — `AGENTS.md` §5 pour le cache d'amendements, #639 pour celui des scrutins, où accepter un store sans `type_scrutin` aurait publié 43 des 66 motions de censure en `vote_texte` — d'où `_syceron_index_qualifie`, qui lit un répertoire non qualifié **comme absent** et laisse l'appelant reconstruire : test sur la **clé** et non sa valeur (`sujet_code_grammaire` vaut légitimement `None`, règle de `_scrutins_store_qualifie`), **une seule tranche lue et c'est la plus petite** (une entrée tranche, et #628 interdit de charger une tranche de plusieurs Mio pour ça), refus par `continue` et non `return None` pour qu'un index complet périmé ne masque pas un index réduit conforme (asymétrie de #657 intacte), verdict mémoïsé par **chemin absolu** (piège de #377) et **oublié à la publication** — sans cet oubli, l'index qu'on vient d'écrire serait refusé et chaque acteur reparcourrait l'archive, 12,5 s et 3,8 Gio de pic par candidat (#510) ; **le lot ne corrige pas #710, il lève ce qui l'empêchait** — les 2 041 tombent au prochain run avec `collect_interventions=true`, et c'est là que se mesurera enfin la perte sur `tags_thematiques` (765 interventions, 93 couples annoncés sur 481 profils, à remesurer sur 641), le `allow_declared_losses` de #710 restant à ce jour **non vérifié** puisque les deux runs ont rendu « aucune perte bloquante » faute d'avoir rien corrigé ; **aucun `cold_start` n'est nécessaire** et il ne protégeait rien (le prochain champ ajouté au parseur serait retombé dans le même trou) ; condition de retrait écrite — la clé de cache cesse d'être un mensonge le jour où elle porte une empreinte du **code**, et d'ici là chaque champ neuf doit rejoindre `SYCERON_CHAMP_QUALIFICATION` ou passer inaperçu ; effet de bord mesuré et **déclaré non corrigé** : les 6 tests qui échouaient en local et pas en CI (688 interventions rendues pour 1 attendue) passent parce que le cache du poste est antérieur à #710 et donc refusé — un test dont le verdict dépend du cache du développeur reste un défaut, seulement devenu invisible. 13 tests, suite complète à 3 671, 0 échec.

## 1. Le défaut : une correction qui tourne et ne corrige rien

Le run `33652389393` du 02/09/2026 a été lancé avec `collect_interventions=true`
dans un seul but : appliquer la correction de [[creneau-de-seance-nest-pas-un-sujet-710]],
fusionnée le matin même. Il a **réussi**, produit le commit de données
`25895974` — et n'a corrigé **aucun** sujet.

| Intitulé procédural publié comme `sujet` | Avant | Après |
| --- | ---: | ---: |
| « Déclaration du Gouvernement » | 742 | **742** |
| « Motions de censure » | 520 | **520** |
| « Motion de censure » | 320 | **320** |
| « Questions au Premier ministre » | 179 | **179** |
| « Déclaration du gouvernement » | 156 | **156** |
| « Questions au gouvernement » | 124 | **124** |
| **Total** | **2 041** | **2 041** |

Chiffre pour chiffre. Et `interventions` portant un sujet reste à **14 817**,
alors que le corpus est passé à 680 298 interventions publiées.

Rien n'a échoué, rien n'a été signalé. C'est la forme de panne que ce dépôt paie
le plus cher : un garde-fou existe pour la classe du défaut, il n'a simplement
jamais été posé ici.

## 2. La cause : le cache ne dit rien du parseur

Mesuré sur les profils bruts que ce run venait d'écrire : `gabriel-attal` porte
3 963 interventions brutes dont **0** avec la clé `sujet_code_grammaire`,
`edouard-philippe` 2 376 dont **0**. Le champ introduit par #710 n'existe nulle
part dans la couche brute.

Le journal de `extract-an` donne la raison en une ligne :

```
Cache restored from key: public-data-cache-an-2026-W36-interv-syc15.16.17-q14.15.16.17
```

**`.cache/syceron_an/<leg>/index_par_acteur` n'est pas une archive mise de
côté : c'est le produit de `parse_syceron`.** Un index en cache est donc un
*parsage* en cache. Sa clé décrit *quand* l'entrée a été écrite (la semaine ISO),
*dans quel mode* (`-interv`) et *sur quelles archives* (l'empreinte de complétude
de [[cache-completude-interventions-550]]) — **jamais avec quel parseur**.

L'enchaînement est mécanique :

1. l'index restauré date d'avant #710, il ne porte pas la clé ;
2. la couche brute ne la reçoit donc pas ;
3. `merge_profile.backfill_sujet_seance` exige au brut « la présence de la clé
   `sujet_code_grammaire`, fût-elle à `None` » comme **preuve** — aucune entrée
   ne la satisfait ;
4. le report ne s'applique à rien.

Corollaire, qui explique une prédiction fausse faite le même jour : le contrôle
de perte a rendu « Aucune perte bloquante » aux **deux** runs, non pas parce que
la perte annoncée par #710 était surestimée, mais parce qu'il n'y avait **rien à
perdre**. La nécessité du `allow_declared_losses` que #710 prévoit reste, à ce
jour, **non vérifiée**.

## 3. La règle existait déjà, deux fois, et pas ici

`AGENTS.md` §5 la pose pour le cache d'amendements — *« un répertoire qui existe
n'est pas la preuve de ce qu'il contient »* — et #639 l'a appliquée au cache de
scrutins : un store qui ne porte pas `type_scrutin` est **refusé et
reconstruit**, jamais relu au mieux. L'accepter aurait publié 43 des 66 motions
de censure comme `vote_texte`.

Le cache Syceron n'avait pas son équivalent. Il avait pourtant **deux** gardes,
et aucune ne couvrait ce cas :

| Garde existante | Ce qu'elle refuse | Ce qu'elle laisse passer |
| --- | --- | --- |
| #505 / #510 | un index construit sur une archive absente, ou n'ayant résolu aucun acteur | un index complet, correct, **écrit par un parseur périmé** |
| #550 (empreinte de complétude) | une entrée de cache écrite alors que des archives manquaient | la même chose : l'empreinte nomme les archives, pas le code |

## 4. La décision

`candidate_profile._syceron_index_qualifie(index_dir)` : un répertoire de
tranches dont aucune entrée ne porte `sujet_code_grammaire` est **lu comme
absent**, avec une ligne qui le dit, et l'appelant reconstruit.

Quatre choix, chacun contre un défaut connu :

- **Le test porte sur la clé, pas sur sa valeur.** `sujet_code_grammaire` vaut
  légitimement `None` sur un point dont la grammaire ne porte pas de sujet ;
  exiger une valeur refuserait un index correct. Mot pour mot la règle de
  `_scrutins_store_qualifie` (#639).
- **Une seule tranche est lue, et c'est la plus petite.** Toute entrée du
  parseur corrigé porte la clé, aucune de l'ancien ne la porte : une entrée
  tranche. La plus petite est le témoin le moins cher — une tranche d'acteur
  bavard pèse plusieurs Mio, et #628 interdit de charger ce qu'on n'a pas besoin
  de garder. Un répertoire vide est déclaré non qualifié : il n'y a rien à en
  tirer et le reconstruire ne coûte rien.
- **Le refus est un `continue`, pas un `return None`.** Un index complet périmé
  ne doit pas masquer un index réduit conforme : l'asymétrie de #657 — un run
  réduit lit l'index complet, jamais l'inverse — reste entière.
- **Le verdict est mémoïsé par CHEMIN absolu**, jamais par un nom logique : les
  tests règlent leur propre cache par cas, et un mémo global ferait fuiter le
  verdict d'un test dans le suivant (le piège qui a fait revenir #377).

### Le piège du mémo, et il est coûteux

Un verdict porte sur un **contenu**, pas sur un chemin. Le garder après
réécriture ferait refuser l'index qu'on vient de produire, et **chaque acteur
suivant reparcourrait l'archive entière** — 12,5 s et 3,8 Gio de pic mesurés en
#510, multipliés par le nombre de candidats du shard. L'oubli est donc posé dans
`_write_syceron_index_par_acteur`, la seule fonction qui publie, et il ne porte
que la forme publiée : une publication réduite ne blanchit pas la forme complète.

### Ce que la mesure du témoin ne peut pas dire

`_reduire_au_theme` **pose** `sujet_code_grammaire` à `None` sur toute entrée
qu'elle produit, y compris dérivée d'un index périmé. Une entrée réduite
paraîtrait donc conforme. C'est sans effet ici parce que le verdict porte sur le
répertoire **sur disque**, avant toute réduction — mais la fixture de #657 le
vérifie désormais sur la **valeur** et non sur la seule présence de la clé, pour
que ce raisonnement reste testé plutôt qu'écrit.

## 5. Ce qui se répare tout seul, et ce qui ne se répare pas

Le premier run qui suit ce lot reconstruit les index des trois législatures avec
le parseur corrigé, et #710 s'applique enfin. Aucun `cold_start` n'est
nécessaire — c'était le contournement disponible avant ce lot, et il ne
protégeait rien : le prochain champ ajouté au parseur serait retombé dans le
même trou.

**Ce que le lot ne fait pas** : il ne corrige pas #710, il lève ce qui
l'empêchait. Les 2 041 sujets de créneau tombent au prochain run avec
`collect_interventions=true`, et c'est **là** que se mesurera la perte sur
`tags_thematiques` — 765 interventions et 93 couples `(profil, tag)` annoncés par
#710 sur 481 profils, à remesurer sur 641.

**Sa condition de retrait** est celle de son jumeau de #639 : la clé de cache
cesse d'être un mensonge le jour où elle porte une empreinte du **code** qui a
produit l'entrée, et non seulement des archives qu'il a lues. Tant qu'elle n'en
porte pas, chaque champ ajouté au parseur devra rejoindre
`SYCERON_CHAMP_QUALIFICATION` ou passer inaperçu — et c'est une charge de
maintenance, pas une garantie.

## 6. Un effet de bord mesuré, et qui n'est pas un hasard

Six tests de la suite échouaient **en local et pas en CI** —
`test_budget_interventions` (4) et `test_candidate_profile` (2) —, en rendant
688 interventions là où leur fixture en attendait 1. Ils lisaient le cache
Syceron réel du poste au lieu de leur fixture. Ce lot les fait passer : le cache
local est antérieur à #710 (`.cache/syceron_an/16` et `/17`, 656 et 675 tranches,
verdict `False` sur les deux), donc désormais refusé.

**Ce n'est pas la correction de ce défaut-là.** Un test dont le verdict dépend du
cache du développeur reste un défaut ; il est seulement devenu invisible parce
que ce cache est maintenant rejeté. Il le redeviendra visible le jour où un cache
conforme traînera sur un poste. Constat déclaré ici plutôt que traité, faute
d'appartenir à ce lot.

## 7. Vérification

`tests/test_conformite_index_syceron_719.py` — 13 tests : le verdict dans ses
cinq cas (qualifié, périmé, clé à `None`, répertoire vide, tranche illisible),
le choix du témoin le moins cher, le refus lu comme une absence et non comme un
`[]`, le repli d'un run réduit sur l'autre forme, l'asymétrie de #657 préservée,
et le mémo dans **les deux sens** — mémoïsé par chemin, oublié à la publication.

Suite complète : **3 671 tests, 0 échec**.
