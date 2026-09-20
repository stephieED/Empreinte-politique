<a id="publication-scopee-artifacts"></a>
# Un artifact = la contribution d'un job : ce qu'on publie décide de ce qu'on peut corriger (#450) (2026-08-19)

`2026-08-19`

> **En bref** — republier la ligne de base défait `--no-merge` et fait entrer les shards en collision.

Le run `32277443716` (19/08/2026, sha `698a882`, `overwrite_profiles=true` +
`roster_refresh_existing=true` + `roster_extraction_limit=0`) devait faire
passer les 205 profils de roster sur la clé `uid` de #440. Les 8 shards ont
tourné, chacun a écrit sa tranche, et le résultat committé est celui-ci :

| | avant | après |
| --- | --- | --- |
| profils à 100 % d'`uid` | 19 | 21 |
| profils à 0 % | 135 | 119 |
| profils **mixtes** | 6 | **22** |
| amendements committés | 620 208 | **727 132** |

Les profils régénérés ne sont pas passés à 100 % : ils sont devenus mixtes, et
le volume a **augmenté de 107 000 entrées**. Sur `antoine-armand`, 3 335
amendements = 1 289 périmés (présents à l'identique avant le run) + 2 046
corrigés : le profil corrigé n'a pas remplacé l'ancien, il s'y est **ajouté**.

## La cause : le `path:` de l'upload, pas la fusion

Chaque job d'extraction commence par un `actions/checkout` — `raw_data/profiles/`
y contient donc les ~209 profils committés, dont la quasi-totalité que ce job ne
touchera jamais. `extract-senat`, `extract-ue-officiel` et les 8 shards de
`extract-roster-groupes` uploadaient `path: raw_data/profiles/` : chaque artifact
publiait sa tranche fraîche **et** une copie périmée de tout le reste.

`extract-an` avait déjà, lui, un `path:` scopé (#344) — il n'était pas porteur,
mais **victime** : ses 3 profils mixtes qui ne figurent même pas au roster
(`edouard-philippe`, `jean-luc-melenchon`, `laurent-wauquiez`) ont été réinjectés
par les artifacts Sénat/UE, qui transportaient tout le répertoire.

De là, deux dégâts distincts et indépendants.

**1. Réinjection.** `merge_raw_dirs` fusionne les répertoires sources
additivement, slug par slug. Une version fraîche et une version périmée du même
profil donnent leur **union**, jamais un remplacement. `--no-merge` faisait
correctement son travail dans le job d'extraction, et se faisait défaire à
l'étape de fusion. Aucune correction de clé ne pouvait aboutir, quels que soient
les inputs — et le volume enflait à chaque run.

Ce n'est pas qu'une question de taille : un amendement compté deux fois n'est pas
une donnée incomplète, c'est un **fait faux**. Les dénominateurs publiés en
dépendent (AGENTS.md §2.7).

**2. Collision entre shards.** Les 8 artifacts du roster arrivent par `pattern`
+ `merge-multiple`, qui les **aplatit dans un seul dossier** : à nom de fichier
égal, un seul survit. Comme chaque shard publiait les 752 profils, les 8
entraient en collision sur chacun des noms. Nombre de profils régénérés lu dans
les logs de chaque shard ; trace d'arrivée au commit mesurée sur les fichiers
committés, un profil devenu **mixte** prouvant qu'une version fraîche l'a
atteint (les slugs présents aussi dans `candidats.json` sont exclus : leur
version fraîche vient d'`extract-an`, dont le `path:` était déjà scopé) :

| shard | régénérés (logs) | devenus mixtes |
| --- | --- | --- |
| 0 | 24 | 0 |
| 1 | 24 | 0 |
| 2 | 26 | 0 |
| 3 | 24 | 0 |
| 4 | 26 | 0 |
| 5 | 26 | 0 |
| 6 | 28 | **16** |
| 7 | 27 | 0 |

Un seul shard laisse une trace ; les sept autres, aucune. **177 profils de
travail réseau écrasés sans le moindre signal**, run après run. Que ce soit le
shard 6 qui l'emporte n'est décidé nulle part dans ce dépôt : c'est l'ordre
d'extraction concurrent de `download-artifact`.

Ce défaut-là est antérieur à #440 et indépendant de toute correction de clé — il
rendait le sharding du roster (#394) essentiellement décoratif. Personne ne
l'aurait vu sans une mesure profil par profil : le run se termine en `success`,
les 8 shards impriment la ligne attendue, et les logs de `merge-and-pivot`
annoncent « Total of 8 artifact(s) downloaded ».

## La décision

Rétablir la propriété manquante — **un artifact = la contribution d'un job** —
plutôt que d'arbitrer à la fusion.

`generate_all_profiles.py --manifest-out FICHIER` consigne le nom de fichier de
chaque profil brut réellement écrit, une ligne à la fois, sous verrou.
`.github/actions/publish-written-profiles` recopie ces seuls fichiers dans
`_publish/profiles/`, et c'est ce répertoire que les 4 jobs d'extraction
uploadent.

Traiter les deux dégâts **par construction plutôt que par arbitrage** est ce qui
motive ce choix : des jobs qui ne publient que leur propre tranche produisent des
jeux de fichiers **disjoints**. Il ne reste ni baseline périmée à réinjecter, ni
nom en collision à départager — le second défaut disparaît sans qu'aucune règle
ne le vise.

L'alternative envisagée — retenir à la fusion la version la plus récente en mode
écrasement — était plus simple mais laissait le problème entier pour tout autre
consommateur des artifacts, et faisait dépendre `merge-and-pivot` d'un input
appartenant à un autre job.

**Écriture au fil de l'eau, pas un dump final.** Les préemptions sont fréquentes
ici (#228) : un manifeste écrit à la fin serait perdu précisément quand il sert.
Tronqué au démarrage puis complété ligne à ligne, il laisse un préfixe **valide**
décrivant exactement ce qui est sur le disque — le principe de #443 appliqué à la
publication.

**Aucun repli sur `raw_data/profiles/`.** Manifeste absent (échec avant la
première écriture) → artifact vide, avec un `::warning::`. Un repli « publier
tout le répertoire » restaurerait le bug dans le seul cas où il est certain que
le job n'a rien produit.

## Ce qui a été vérifié avant de conclure

**La baseline n'a jamais eu besoin de transiter par un artifact.**
`merge-and-pivot` fait son propre `actions/checkout`, et `merge_raw_dirs` boucle
sur les fichiers **sources** : il ne réécrit que les slugs présents dans les
artifacts. Un profil qu'aucun job n'a touché conserve donc sa version committée
sans que rien ne le transporte. Le commentaire d'`extract-an` qui justifiait le
transport par les autres jobs (« merge-and-pivot reçoit toujours la baseline
complète via eux ») décrivait un besoin qui n'existait pas.

**L'union entre sources différentes reste intacte.** Un slug couvert par deux
jobs (candidat déclaré présent aussi au roster : `gabriel-attal`,
`marine-le-pen`, `bruno-retailleau`, `jerome-guedj`) reste l'union de leurs
contributions — les deux sont fraîches, la fusion additive y joue son rôle
légitime. C'est le seul cas où elle doit encore intervenir entre artifacts.

**`fresh_run` n'est pas la purge globale que son nom suggère** — et ne l'était
pas non plus avant #450. La purge de `raw_data/profiles/` a lieu sur les runners
d'**extraction** ; le checkout de `merge-and-pivot`, lui, n'est pas purgé. Un
profil qu'aucun job d'extraction ne couvre survit donc à un `fresh_run`.
Constaté, non traité ici.

**Le cas « rien écrit » était un angle mort d'`extract-an`.** Son `path:` scopé
désignait le chemin *attendu* d'un slug, pas une écriture *constatée* : une
extraction sans identité trouvée (statut `introuvable`) republiait la copie
périmée laissée par le checkout. Le manifeste ferme ce cas.

## Remise en état

Les 22 profils mixtes portent aujourd'hui les deux versions de chaque amendement.
Ils sont à **régénérer** après cette correction, pas à fusionner :
`src/audit_diff_profils.py` signalera une baisse sur `amendements`, qui est ici
le résultat attendu et non une perte.

