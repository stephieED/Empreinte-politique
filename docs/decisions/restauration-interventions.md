<a id="restauration-interventions"></a>
# Restaurer 789 interventions sans revenir sur le reste du schéma (#460) (2026-08-19)

`2026-08-19`

> **En bref** — restaurer 789 interventions champ par champ, sans revenir sur le reste du schéma.

Le commit de données `a125e9e` a effacé la totalité des interventions du
corpus, brut **et** pivot, et la perte s'est propagée aux deux champs qui en
dérivent — `tags_thematiques` des profils, `tags_thematiques_agreges` des
groupes, tous deux **publiés** (AGENTS.md §6). Le mécanisme est celui de
l'issue : `overwrite_profiles=true` lève `--no-merge`,
`extract_interventions=false` lève `--skip-interventions`, et le profil est
réécrit sans ce que le run n'a pas collecté.

Ce qui était perdu, mesuré profil par profil sur `a125e9e^` :

| profil | interventions | `tags_thematiques` |
| --- | --- | --- |
| `jerome-guedj` | 395 | 179 |
| `marine-le-pen` | 302 | 318 |
| `edouard-philippe` | 50 | 150 |
| `laurent-wauquiez` | 22 | 0 |
| `jean-luc-melenchon` | 15 | 0 |
| `gabriel-attal` | 5 | 0 |
| **total** | **789** | **647** |

Côté groupes, 497 `tags_thematiques_agreges` : 318 sur `groupe-AN-RN-16`
(via `marine-le-pen`), 179 sur `groupe-AN-SOC-16` (via `jerome-guedj`). Les
150 tags d'`edouard-philippe` n'alimentent aucun groupe — il n'appartient à
aucun des 7 rosters committés.

## Pourquoi ne pas avoir attendu la régénération

Le run `32302557156` portait `extract_interventions=true` et aurait dû les
recollecter. Il a perdu **4 de ses 8 shards `extract-an` sur annulation
externe** — le motif récurrent de #221/#228 — et l'arbitrage se lit
directement dans la liste :

| shard | issue | interventions en jeu |
| --- | --- | --- |
| `jerome-guedj` | succès | 395 |
| `edouard-philippe` | succès | 50 |
| `gabriel-attal` | succès | 5 |
| `marine-le-pen` | **annulé** | 302 |
| `laurent-wauquiez` | **annulé** | 22 |
| `jean-luc-melenchon` | **annulé** | 15 |
| `bruno-retailleau` | **annulé** | 0 |

Le run ne pouvait donc rendre que **450 des 789 interventions**. Les 339
restantes, dont les 302 de `marine-le-pen`, seraient restées perdues — et avec
elles la totalité des 318 `tags_thematiques_agreges` de `groupe-AN-RN-16`,
qu'elle alimente à elle seule. Un run qui annule la moitié de ses shards ne
peut pas servir de plan de restauration : il rend les profils qu'il a eu le
temps de traiter, et rien, dans le commit produit, ne signale lesquels.
Attendre revenait à faire dépendre la récupération d'un aléa d'ordonnancement.

La restauration depuis git est immédiate, exhaustive et vérifiable. Elle ne
concurrence pas la recollecte : la fusion additive de `merge_profile.py`
(`interventions` : additif, l'ancienne entrée gagne) fait que tout run
ultérieur s'ajoute à ce qui est restauré, sans doublon ni écrasement.

## Ce qui a été écarté : recopier les fichiers de `a125e9e^`

C'était la voie évidente et elle est fausse. Les profils de `a125e9e^`
sont à l'**ancien schéma** — d'avant la normalisation des votes
([[normalisation-votes]], #432) et des amendements
([[normalisation-amendements]], #431). Les recopier aurait restauré 789
interventions en annulant 84,8 % de réduction de volume et en remettant en
place les `votes[]` dénormalisés que #432 vient de sortir des profils. On
répare une perte, on ne rejoue pas un état.

**Seul le champ `interventions` a donc été extrait de `a125e9e^`**, réinjecté
dans le brut au schéma courant, puis le pivot a été **re-dérivé** par le code
d'aujourd'hui : `_normalize_intervention` pour `interventions[]`, la dérivation
`theme_officiel` / `mots_cles` de `normalize_nosdeputes` pour
`tags_thematiques`, `group_profile.aggregate_tags_thematiques` pour les
groupes.

Ce qui autorise ce découpage est une propriété vérifiée, pas supposée :
appliquer `_normalize_intervention` d'aujourd'hui aux interventions brutes de
`a125e9e^` redonne **exactement**, pour les 6 profils, les
`interventions[]` pivot de `a125e9e^`. La normalisation des interventions n'a
pas bougé depuis ; #431 et #432 n'ont touché ni ce champ ni ses dérivés. Les
`tags_thematiques_agreges` recalculés sont eux aussi identiques, entrée pour
entrée, à ceux de `a125e9e^`.

## Vérification par l'outil prévu pour ça

`audit_diff_profils.py --ref origin/main`, c'est-à-dire le contrôle que #460
reprochait de n'être branché nulle part, appliqué à la correction elle-même :

| champ | avant | après | écart |
| --- | --- | --- | --- |
| `votes` | 524 353 | 524 353 | +0 |
| `mandats` | 16 498 | 16 498 | +0 |
| `textes_portes` | 423 | 423 | +0 |
| `interventions` | 0 | **789** | **+789** |
| `amendements` | 810 552 | 810 552 | +0 |

*« Aucune perte sur les champs stables »*, et un gain sur le seul champ visé.
Le diff est confiné : les 6 profils bruts ne changent que sur `interventions`,
les 6 pivots que sur `interventions` et `tags_thematiques`, les 2 groupes que
sur `tags_thematiques_agreges`. `validate_profil()` rend le **même nombre
d'erreurs qu'avant** sur les profils touchés (2 979 sur `gabriel-attal`,
15 804 sur `marine-le-pen` — des `votes[]` sans `scrutin_id`, antérieurs et
sans rapport), et aucune ne mentionne les interventions ni les tags.

Au passage, l'outil s'est fait **tuer par l'OOM killer** sur ce corpus dans sa
version de `main` — 3,14 Gio, `exit 137`. La vérification ci-dessus a été
conduite avec la version corrigée de [[controle-de-perte-avant-commit]]
(236 Mio). Un garde-fou qui meurt avant de conclure ne garde rien : c'est la
même classe de panne muette que celle qui a produit #460.

## Le commit de données est fait à la main

14 fichiers de données sont modifiés hors pipeline. C'est assumé et signalé
comme tel : aucun run ne peut produire ce résultat, puisque la recollecte
dépend de sources tierces dont deux jobs viennent d'être annulés. La
traçabilité (AGENTS.md §2.2) est intacte — chaque intervention restaurée
porte son `source_url` d'origine, aucune valeur n'est inventée, aucun champ
absent n'est comblé par un défaut (§2.5).

## Le garde-fou : avertir au lancement, refuser au commit

#460 listait deux pistes non exclusives. [[controle-de-perte-avant-commit]]
pose le contrôle **générique** : toute perte sur un champ stable échoue le job
avant l'étape de commit. Il manquait le signal **en amont** — rien ne disait,
au moment de lancer le run, que la combinaison d'inputs allait détruire des
données déjà acquises.

Un step de `prepare-an-matrix` s'en charge. Ce job n'a aucun `needs` : il
démarre immédiatement, donc l'avertissement est lisible avant qu'une minute de
runner ait été consommée. Sa condition reproduit **en négatif** le calcul de
`MERGE_FLAG` des jobs d'extraction (`fresh_run` **ou** `overwrite_profiles`),
parce que c'est `--no-merge`, et lui seul, qui rend l'écrasement destructeur —
un test échoue si les deux formulations divergent.

**Avertissement et non refus.** Un `exit 1` ici ferait double emploi avec le
refus d'aval, et casserait un usage légitime : propager une correction de clé
(#431, #432) sans repayer la collecte des interventions est un choix valide
dès lors qu'il est conscient. Ce qui manquait n'était pas un veto, c'était de
rendre le choix conscient. Le refus, lui, reste en aval, où il porte sur une
perte **mesurée** plutôt que **prédite**, avec `tolerer_pertes_profils` pour
la déclarer. Même forme et même ton que le `::warning::` de
`roster_refresh_existing` sans `overwrite_profiles` (#445).

**Le signal porte sur une variation, pas sur un niveau.** C'est ce qui
manquait à la quality gate : sa §3 se déclenchait sur 209 profils sur 209 et
ne distinguait donc pas « n'en a jamais eu » de « vient d'en perdre 789 ». Le
step compte les interventions réellement committées et **ne dit rien s'il n'y
en a aucune** — il n'y a alors rien à détruire, et un garde-fou qui crie à
vide se fait ignorer, ce qui est précisément le mécanisme par lequel le
signal de la §3 est devenu inaudible. Quand il parle, il chiffre : « ce run va
EFFACER les 789 interventions sur 6 profils », avec le détail par profil dans
le résumé de job, où il survit au bruit des logs.

Le comptage lit un profil à la fois et le libère : le corpus pèse ~1,5 Go par
répertoire, et trois outils de ce dépôt s'y sont déjà fait tuer par l'OOM
killer — dont `audit_diff_profils.py` deux paragraphes plus haut.

