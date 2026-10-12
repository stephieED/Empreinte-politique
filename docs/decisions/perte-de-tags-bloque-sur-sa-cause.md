# Une baisse de tags thématiques bloque sur sa cause, pas sur son compte

`2026-10-12`

> **En bref** — les runs planifiés des 10 et 11/10/2026 ont échoué au contrôle de perte sur **7 profils à −1 tag** : l'Assemblée avait réuni deux intitulés du même texte, et aucune intervention n'avait perdu le sien. `tags_thematiques` reste une liste stable, mais sa baisse ne bloque plus que si une intervention a disparu ou si moins d'interventions alimentent la liste (`listes_derivees`, `porte_un_tag_thematique`). Pas de seuil. Non étendu aux agrégats de groupe.

## Contexte

`tags_thematiques` d'un profil est **dérivé** de ses `interventions[]` : les
intitulés des points d'ordre du jour sous lesquels la personne a parlé
(`theme_officiel`), dédoublonnés (`schema_pivot.deriver_tags_thematiques`). Il
est recalculé à chaque run, jamais fusionné.

Depuis #470 il figure parmi les listes **stables** de `audit_diff_profils` : toute
baisse de son compte annule le commit. La raison était réelle — il était passé de
647 à 0 dans le run `a125e9e`, parce que les interventions avaient été effacées.

Or la source renomme. Au 09/10/2026, le même texte était publié sous deux
intitulés selon la séance :

| Séance | Intitulé publié le 09/10 |
| --- | --- |
| 1er, 2, 5 et 6/10 | « Réponse intégrale aux violences sexuelles et sexistes contre les femmes et les enfants » |
| 7/10 | « Réponse intégrale au phénomène des violences sexuelles et sexistes contre les femmes et les enfants » |

Le lendemain, la source avait retouché ces intitulés. Mesuré dans l'artifact
`diff-profils` du run `38163449634`, croisé avec les profils du 09/10 :

| Le profil portait | Profils | Intitulé disparu | Compte de tags |
| --- | ---: | --- | --- |
| les deux | 7 | « au phénomène des » | **−1** |
| les deux | 11 | « au phénomène des » | égal ou en hausse |
| « au phénomène des » seul | 6 | « au phénomène des » | égal ou en hausse |
| « aux » seul | 8 | « aux » | égal ou en hausse |

L'intitulé « au phénomène des » a disparu de tous les profils qui le portaient.
**Ce que la source publie à la place n'a pas été lu** : la sortie d'un run en
échec n'est pas publiée, et l'artifact nomme ce qui disparaît, pas ce qui
arrive. La lecture la plus simple des 7 profils à −1 — la séance du 7/10 a pris
l'intitulé des autres — est une inférence.

## Ce que ça a coûté

| Run | Fin (Paris) | Constat |
| --- | --- | --- |
| `38075385375`, planifié | 10/10, 21 h 57 | 7 profils, `tags_thematiques` −1 chacun, commit annulé |
| `38163449634`, planifié | 11/10, 21 h 53 | les 7 mêmes |

Les 7 profils sont les mêmes aux deux runs (`claire-marais-beuil`, `david-magnier`, `estelle-youssouffa`, `florence-goulet`,
`graziella-melchior`, `perrine-goulet`, `violette-spillebout`). Sur ces mêmes
1 403 profils, `interventions` passe de 1 305 545 à 1 309 363 : rien n'est perdu.

Un run à pertes déclarées avait déjà été lancé le 09/10 pour un cas rapporté
comme voisin (Hélène Laporte, −1 tag, « reclassement par la source » — non
remesuré ici). Le blocage ne signalait plus un
incident, il signalait le fonctionnement normal de la source — et chaque run
planifié échouait jusqu'à ce que quelqu'un lance un run manuel avec
`allow_declared_losses`, qui désarme le contrôle pour **toutes** les pertes du
run.

## Décision

**Une baisse sur une liste dérivée bloque sur sa cause.** `Collection` déclare
`listes_derivees`, des couples (liste dérivée, liste source) ; pour les profils,
`("tags_thematiques", "interventions")`. La baisse de la dérivée reste bloquante
sauf si, sur le même fichier :

1. la source ne porte pas moins d'entrées qu'avant ; **et**
2. il n'y a pas moins d'entrées de la source qui **alimentent** la dérivée.

« Alimenter » est lu par `schema_pivot.porte_un_tag_thematique`, qui dit d'une
intervention si `deriver_tags_thematiques` en tire au moins un tag. Le contrôle
ne redéfinit pas la règle de dérivation : il l'importe, et un test tient les
deux ensemble.

Quand les deux conditions tiennent, la baisse est rapportée dans une section à
part (« sans perte en amont »), et les intitulés disparus restent nommés par le
relevé de #823. Quand un des deux comptes n'a pas pu être pris, la baisse
bloque : ce qu'on n'a pas mesuré ne lève pas un blocage.

| Cas | Interventions | Qui alimentent | Tags | Verdict |
| --- | --- | --- | --- | --- |
| Deux intitulés réunis par la source | = | = | −1 | signalé |
| Une intervention perd son intitulé | = | −1 | −1 | **bloque** |
| Interventions effacées (#470) | −n | −n | −n | **bloque**, sur les deux listes |
| Renommage et intitulé perdu dans le même run | = | −1 | −2 | **bloque** |

Rejoué le 12/10/2026 sur les 7 profils, lus dans `pivot_data/` au 09/10 : le
second intitulé remplacé par le premier dans leurs `interventions[]`, les tags
redérivés — chacun rend exactement le −1 du run, et aucun ne bloque. C'est une
simulation du renommage : la sortie des runs en échec n'est pas publiée.

Coût : nul à la mesure. Le contrôle complet (`--ref HEAD`, six collections, 1 403
profils, poste local, une exécution de chaque) : 153 s et 633 Mio avant, 140 s et
634 Mio après — l'écart de durée est du bruit.

## Ce que la décision ne couvre pas

- **`tags_thematiques_agreges`** des fiches de groupe et de lignée reste une liste
  stable sans exception. La fiche ne porte pas les interventions : la cause ne
  s'y lit pas. Un renommage qui retire un intitulé de **tous** les membres d'un
  groupe bloquera encore — ce n'est pas arrivé les 10 et 11/10, où les gains du
  jour couvraient la baisse.
- **Un intitulé renommé et un intitulé perdu qui se compensent** — une
  intervention perd le sien pendant qu'une nouvelle, arrivée le même jour, en
  porte un. Le compte de celles qui alimentent ne baisse pas. Seul un renommage
  simultané sur le même profil fait alors passer la baisse.

## Alternatives rejetées

- **Ne bloquer que quand la liste se vide.** Laisse passer une perte partielle
  réelle : la moitié des intitulés effacés ne viderait rien.
- **Un seuil de baisse.** Écarté pour le contrôle entier (`controle-de-perte-avant-commit`) :
  aucune proportion ne sépare une baisse correcte d'une baisse défectueuse.
- **Retirer `tags_thematiques` des listes stables.** C'est rouvrir #470.
- **Garder le blocage et déclarer chaque renommage à la main.** `allow_declared_losses`
  désarme le contrôle pour tout le run, et les runs planifiés échouent entre-temps.
