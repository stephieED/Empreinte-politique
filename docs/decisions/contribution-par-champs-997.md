<a id="contribution-par-champs-997"></a>
# Un artifact ne porte plus que les champs que son job a collectés (#997) (2026-09-19)

`2026-09-19`

> **En bref** — Le correctif de fusion de #997 a atteint 1 350 profils sur
> 1 383, et raté **les 33 que le site publie**. `extract-mandats-locaux`
> publiait le profil **entier** — donc `dossiers_legislatifs` recopiés de sa
> baseline — et il parle en dernier : il a reposé les vieux stades sur ce que
> l'extraction AN venait de corriger. Mesuré : Édouard Philippe, **9**
> `examine_commission` dans les deux artifacts d'extraction, **127** committés.
> Les jobs d'enrichissement ne publient plus qu'un champ, celui qu'ils
> collectent.

## Ce que #450 avait fait, et ce qu'il restait

#450 a rétabli « un artifact = les **slugs** d'un job » : un job ne publie plus
que les profils qu'il a écrits, ce qui a supprimé la réinjection de baseline et
la collision entre shards. L'autre moitié est restée : un job publie le profil
**entier**, donc tous les **champs** qu'il n'a pas collectés, recopiés de la
baseline de son checkout.

Tant que `dossiers_legislatifs[]` se fusionnait en additif pur, cette copie
périmée ne pouvait rien écraser — elle était inerte. Depuis que la source la
plus récente gagne
([`fusion-dossiers-brut-la-neuve-gagne-997`](./fusion-dossiers-brut-la-neuve-gagne-997.md)),
**la dernière source de `--dirs` l'emporte**, et
`_artifacts/mandats-locaux` est la dernière.

## La mesure

Sur le run 35430469408, artifact contre baseline, champ par champ :

| Job | Champs qui diffèrent de la baseline | Profils |
| --- | --- | ---: |
| `extract-mandats-locaux` | `mandats_locaux` | 33 |
| `extract-senat` | `mandat_senatorial` | 2 |

**Un seul champ chacun.** Tout le reste — `dossiers_legislatifs`, `votes`,
`interventions` — partait avec, figé au run précédent.

Et l'effet, mesuré en rejouant la vraie fusion sur les artifacts réels
d'Édouard Philippe :

| | `examine_commission` | `depose` | `mandats_locaux` |
| --- | ---: | ---: | ---: |
| Avant (ce que le run a publié) | **127** | 2 | 5 |
| Après, contribution réduite | **9** | 120 | 5 |

## Décision

**Un job déclare ses champs, et ne publie que ceux-là.**
`.github/actions/publish-written-profiles` gagne un input `champs:` ; fourni,
la contribution du staging est réduite par `profil_brut.projeter_contribution`.
Absent, le profil entier part — ce qu'il faut pour une collecte complète (AN,
roster), qui n'a pas de baseline à reposer.

Le manifeste de partition part avec les amendements : un socle qui annonce une
tranche absente est **illisible**, pas partiel, et `charger_profil_brut` le
refuse bruyamment.

## Deux filets essayés, un seul tient

**L'ordre des `--dirs` : rejeté, et c'est la mesure qui l'a rejeté.** Mettre les
jobs d'enrichissement en tête paraissait évident. Rejoué sur les artifacts
réels, ce filet **fait perdre ce qu'il devait protéger** : `_artifacts/an`
porte `mandats_locaux: []`, le job AN ne les collectant pas, et repasser en
dernier lui fait effacer les 5 mandats locaux d'Édouard Philippe. Une source
qui **apporte** un champ doit rester la dernière à parler : l'ordre historique
est le bon. `CHAMPS_PROTEGES_DU_VIDE` ne rend pas l'ordre indifférent non plus
— il ne sert qu'à `preserver_collectes_non_vides`, en mode `--no-merge`, et ne
traverse pas `merge_raw_dirs`.

**La baseline en première source de la fusion : rejetée, et c'est un test du
dépôt qui l'a rejetée.** Elle protégeait le cas où une contribution réduite est
la seule à parler d'un slug. Mais elle réinjecte exactement ce que #450 a
supprimé, et `test_publication_scopee_laisse_aboutir_la_correction_de_cle` est
tombé : une correction de clé d'amendement cessait d'aboutir.

**Ce qui tient : une contribution réduite seule ne réécrit rien.** Elle porte
un marqueur `contribution_partielle`. Si aucune collecte complète ne parle de
ce slug — extraction en échec, `continue-on-error` étant la règle —, le profil
committé reste en place, comme pour un slug qu'aucun job n'a touché (#450).
L'apport du run est perdu pour ce slug, il est **dit** sur la sortie, et le run
suivant le reprend. Un profil amputé publié serait pire qu'un apport reporté
(§2 règle 5).

## Garde

`tests/test_contribution_par_champs_997.py`, sept cas : la projection et son
manifeste, les tranches retirées du staging, le défaut reproduit (contribution
entière qui repose le vieux stade), sa correction, le cas nominal, et le
garde-fou dans les deux sens.

## Ce qui reste ouvert

**Les autres champs recopiés ne sont pas couverts.** Ce lot déclare les champs
de deux jobs, mesurés. Un job ajouté demain sans `champs:` republiera le profil
entier, et rien ne le détectera — l'ordre des `--dirs` redeviendra le seul
rempart. Une garde qui refuserait un artifact portant un champ qu'il n'a pas
collecté demanderait que chaque job déclare son périmètre, ce qu'aucun ne fait
aujourd'hui.
