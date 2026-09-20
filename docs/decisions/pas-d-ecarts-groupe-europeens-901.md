<a id="pas-d-ecarts-groupe-europeens-901"></a>
# « Ses divergences » ne sera pas transposée au Parlement européen (#901) (2026-09-14)

`2026-09-14`

> **En bref** — la section « Ses divergences », validée le 08/09/2026, juxtapose la position d'une personne et celle de son groupe, scrutin par scrutin. `pivot_data/scrutins_europeens.json` (#919) apporte enfin de quoi l'alimenter côté européen : **1 977 / 1 977** des votes de `raphael-glucksmann` s'y apparient, et chaque scrutin porte sa ventilation `par_groupe`. Elle ne sera pourtant **pas** transposée : trois des six champs qu'elle consomme — `position_majoritaire`, `membres_eligibles`, `absents` — n'existent nulle part dans le corpus européen, et les produire supposerait d'agréger l'effectif complet du Parlement, groupe par groupe et date par date. Arbitré par la propriétaire le 14/09/2026.

## 1. Ce que la section consomme, et ce que l'Europe porte

`ecartsAvecLeGroupe` (`web/UI_finale/src/utils/ecartsGroupe.js:83`) ne lit pas les votes de la personne seuls : elle les apparie aux `cohesion_votes[]` d'une **fiche de groupe**. Six champs par scrutin, mesurés le 14/09/2026 sur `origin/main` :

| Champ | Côté Assemblée | Côté Parlement européen |
| --- | --- | --- |
| jointure du scrutin | `scrutin_id` | **présente** — 1 977 / 1 977 par `numero_scrutin` |
| `pour` / `contre` / `abstention` | `cohesion_votes[]` | **présents** — `par_groupe` de `scrutins_europeens.json` |
| `position_majoritaire` | publiée | **absente** |
| `absents` + `non_votant` | publiés | **absents** — le dump ne porte aucune liste nominative (#919, refus délibéré) |
| `membres_eligibles` | publié | **absent**, même cause |
| `quorum_atteint` | dérivé de `membres_eligibles` | **non calculable** |

Et au-dessus de ces six champs, il en manque un septième : **aucune fiche de groupe européen n'existe**. La fiche le dit déjà proprement — « Rien n'est comparable — ce n'est pas la même chose qu'"aucune divergence" » — et c'est ce comportement qui reste.

## 2. Pourquoi ce n'est pas un champ à ajouter

`par_groupe` donne les trois effectifs des **votants**. Les trois champs manquants parlent tous des **non-votants** : qui était éligible, qui était absent, et donc quel poids accorder à la position majoritaire. Les produire ne demande pas une clé de plus dans un index : il faut connaître, **à la date de chaque scrutin**, la composition complète de chaque groupe du Parlement — soit l'appartenance de quelque 700 députés européens sur quatre législatures, reconstituée pour 5 571 scrutins.

C'est un pipeline entier, pour alimenter une seule section d'une fiche. Le rapport entre le coût de collecte et ce que l'écran y gagne ne le justifie pas, et c'est le motif de l'arbitrage.

## 3. L'alternative écartée : dériver la position majoritaire

`par_groupe` permettrait de calculer une position majoritaire — le plus grand des trois nombres. **Refusé**, et pas pour des raisons de coût.

Sur le scrutin `A9-0387/2023` du 16 janvier 2024, le groupe S&D se répartit en **1 pour, 13 contre, 105 abstentions**. Sa « position majoritaire » serait l'abstention. Écrire que Raphaël Glucksmann, qui a voté contre, « s'est écarté de son groupe » ferait passer un groupe qui se tait pour un groupe qui tranche — et publierait comme un fait une position que la source n'établit pas (`AGENTS.md` §2 règle 5, et règle 2).

Le défaut est structurel, pas anecdotique : à l'Assemblée, `position_majoritaire` est **publiée par la source** avec son quorum ; au Parlement européen elle serait **inférée par nous**, sans rien pour dire quand l'inférence ne vaut pas.

## 4. Ce que la décision ne ferme pas

- **La juxtaposition reste autorisée** par §2 règle 7, et `scrutins_europeens.json` la rendrait possible sous une autre forme — une ventilation montrée telle quelle, sans mot qui la résume. Rien n'est décidé là-dessus ; cette décision dit seulement que **la section existante** ne sera pas transposée.
- **Le compte reste interdit** dans tous les cas. « A voté contre son groupe *n* fois » est l'indice individuel mesuré contre une moyenne de groupe : rapport interne uniquement (§2 règle 7). Ce nombre a été calculé pour instruire l'arbitrage ; il n'a pas sa place à l'écran, ni dans ce fichier.
- **Les votes européens ne restent pas invisibles pour autant** : leur affichage dépend de `isWholeTextVote` et de la sélection de dernière lecture, pas de cette section.

## 5. Ce qui aurait pu tourner mal, et qu'on évite

La section aurait pu être transposée « avec ses trous déclarés » — c'était la recommandation initiale de la session interface, au nom de la cohérence : une fiche doit se lire pareil quelle que soit la chambre. Elle se serait affichée avec une position majoritaire inférée, un quorum jamais renseigné et un effectif éligible à zéro. **Une section qui déclare trois trous sur six champs ne dit plus rien** ; elle donne la forme d'une comparaison sans en avoir la substance, ce qui est plus trompeur que son absence.

→ voisin : [`derniere-lecture-retenue-711`](derniere-lecture-retenue-711.md), [`index-dossiers-europeens-901`](index-dossiers-europeens-901.md)
