<a id="conservation-du-prefixe-laissee-ouverte-1125"></a>
# La conservation du préfixe entre deux runs reste ouverte, et c'est une décision (#1125) (2026-09-24)

`2026-09-24`

> **En bref** — Trois obstacles empêchent un run de reprendre l'archive partielle du précédent, et le troisième n'est pas un réglage : la clé hebdomadaire **est** la politique de fraîcheur, donc il faudrait un second cache. Non construit, parce que le corpus est complet, que #1123 rend le besoin moins probable, et qu'aucune mesure en CI ne le confirme. Ce qui rouvrirait le sujet est écrit.

## Ce qu'on voudrait, et ce qui existe déjà

Un run tire 200 Mo sur les 648 d'une archive figée puis s'arrête ; le suivant
reprend à l'octet 200 000 000. En trois ou quatre runs, l'archive est là.

**La moitié difficile est écrite depuis longtemps** :
`_download_amendements_zip` sonde la taille distante, la compare au fichier
local et reprend en mode ajout — fichier déjà complet : aucune requête ;
partiel : reprise ; sonde en échec ou taille incohérente : redémarrage plutôt
que deviner un décalage.

## Les trois obstacles, vérifiés le 24/09/2026

| # | Obstacle | Où |
| --- | --- | --- |
| 1 | L'archive partielle est effacée à chaque tentative | `build_amendements_index.py`, `construire_un_contenu_fige` : `finally: zip_path.unlink(missing_ok=True)` |
| 2 | Le cache n'est pas sauvegardé quand l'étape échoue ou est annulée | mesuré sur quatre runs consécutifs |
| 3 | La clé `…-amendements-<semaine ISO>` existe déjà | GitHub ne réécrit pas une clé primaire présente |

Pour l'obstacle 2, les quatre runs mesurés :

| Run | Conclusion du job | `Post Run actions/cache` |
| --- | --- | --- |
| `35884784132` | `success` | **sauvegardé** |
| `35910007684` | `failure` | sauté |
| `35926731615` | `cancelled` | sauté |
| `35963887207` | `cancelled` | sauté |

**C'est l'ironie du mécanisme** : le cache n'est sauvegardé que sur les runs
réussis, donc exactement ceux qui n'ont aucun préfixe partiel à transmettre.
Les seuls runs qui auraient quelque chose à léguer sont ceux où la sauvegarde
ne s'exécute pas.

## Pourquoi le troisième obstacle n'est pas un réglage

**La rotation hebdomadaire de la clé EST la politique de fraîcheur** du corpus
d'amendements (#249, puis #749 quand son propre repli la désamorçait). Deux
besoins tirent la clé dans des sens opposés :

- un préfixe qui survit veut une clé qui **tourne à chaque run**, pour être
  réécrite à chaque fois ;
- la fraîcheur des amendements veut une clé qui **tourne chaque semaine**, pour
  forcer la reconstruction des législatures actives.

Une seule clé ne peut pas faire les deux. Il faudrait un **second cache**,
dédié au préfixe, avec sa propre clé tournante — un objet nouveau dans le
workflow, pas un paramètre à changer.

## Décision : ne pas construire, et écrire pourquoi

1. **Le corpus est complet.** Les quatre `<lég>.contenu.json` sont publiés.
   Ce chantier ne paie que le jour où une archive close devra être
   reconstruite : cache purgé, `cold_start`, ou un schéma qui change.
2. **#1123 rend ce jour-là moins coûteux.** Avec la plage sans borne, une
   archive entière est venue en une session.
3. **Le coût est réel et permanent.** Un second cache de 650 Mo par run pèse
   sur les 10 Go du dépôt, et l'éviction LRU frapperait les autres caches —
   ceux dont dépendent des jobs qui, eux, tournent à chaque run.
4. **Aucune mesure en CI ne confirme le besoin.** On ne sait pas encore ce que
   rend une plage ouverte depuis un runner GitHub ; construire un mécanisme
   pour un problème qu'on n'a pas remesuré depuis qu'on l'a changé, c'est le
   travers que ce dépôt évite ailleurs.

## Ce qui rouvrirait le sujet

**Un run qui échoue deux fois de suite à reconstruire une archive figée, AVEC
la plage sans borne de #1123.** C'est la mesure qui manque, et elle ne
s'obtient qu'en situation — pas en la simulant.

## Ce qu'il ne faut pas refaire

**Augmenter `AMENDEMENTS_SOURCE_STALL_MAX_CYCLES`**, écarté le 23/09/2026 : une
constante en cycles ne sait pas combien de temps un cycle prend, et c'est le
job qui est borné en temps, pas en cycles (#1100).

**Relancer des runs à l'aveugle** : le cache hebdomadaire n'étant pas réécrit
quand sa clé existe, un contenu construit sans être publié est perdu au run
suivant — c'est l'obstacle 3 vu depuis l'autre bout.
