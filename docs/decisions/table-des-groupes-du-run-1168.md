# La table des groupes du run : composée à chaque run, dans `raw_data/` (#1168, lot 2c)

`2026-10-02`

> **En bref** — le run tient désormais sa propre table des groupes, `raw_data/groupes_du_run.json`, **composée** dans `prepare-roster-matrix` avant le roster : la table **écrite à la main** (`config/groupes_reels.json`, qui a toujours raison sur ce qu'elle porte), plus les groupes que les runs précédents ont ajoutés (repris tels quels — c'est ce qui fige un lien et une adresse), plus ce que l'archive AMO30 apporte de neuf. Elle vit dans `raw_data/` parce que `config/` est recopié du dépôt privé à chaque run, et sous **un autre nom** que la table écrite, comme #1057 l'exige. Les lecteurs passent tous par `groupes_config.CHEMIN_CONFIG_GROUPES`, qui ne retient la table du run que si elle porte **l'empreinte de la table écrite du jour** : une correction faite à la main entre deux runs reprend la main aussitôt. Une contradiction avec une adresse déjà publiée **arrête** la composition au lieu d'être tranchée. **Cette décision remplace la section de `repertoire-config-1057` qui disait la lignée et la sélection des groupes non dérivables** — la propriétaire a arbitré le contraire le 02/10/2026. **Touche `generate-data.yml` ; aucun run ne l'a encore exécutée.**

## Le problème

Le lot 2a sait compléter une table depuis la source. Encore faut-il que le run
garde ce qu'il ajoute : un groupe entré aujourd'hui doit retrouver demain le
même identifiant, le même lien, la même adresse — la propriétaire l'a demandé
(« que les lignées ne soient reconstruites que lorsqu'il y a un nouveau
groupe »).

Or le run ne peut rien garder dans `config/`. `.github/actions/code-du-prive`
recopie tout le dépôt privé sur le checkout, sauf `pivot_data/` et `raw_data/`,
avec `rsync --delete`. Et #1057 a posé le critère : `config/` porte ce qu'une
**personne** écrit, `raw_data/` ce qu'un **run** écrit.

## Ce qui est décidé

**Deux tables, deux auteurs, deux noms.**

| Table | Qui l'écrit | Ce qu'elle porte |
| --- | --- | --- |
| `config/groupes_reels.json` | une personne, en PR | les noms : sigle publié, identifiants, adresses ; `extraction_suspendue` ; `fiches_retirees` |
| `raw_data/groupes_du_run.json` | chaque run | la précédente, plus ce que les runs ont ajouté et ce que la source dit |

**La composition** (`groupes_amo30.composer_table`), à chaque run, dans cet ordre :

1. partir de la table écrite ;
2. reprendre de la table du run précédente toute entrée dont **aucun** organe
   n'est porté par la table écrite — un groupe que seul un run a ajouté —, avec
   son entrée de `groupes[]` et sa lignée ;
3. appliquer `mettre_a_jour_table` : organes renommés, groupes nouveaux, champs
   rafraîchis ;
4. consigner l'empreinte SHA-256 de la table écrite dans
   `_meta.table_ecrite_a_la_main`.

Un prédécesseur que la table écrite a renommé ou réuni depuis — mêmes organes,
autre identifiant — est **retrouvé par ses organes**, et le lien repris le suit.

Une date `verifie_le` ne bouge que si le contenu a bougé : la table étant
refaite de la table écrite à chaque run, un effectif rafraîchi une fois
reprendrait sinon la date du jour tous les jours, et le fichier changerait à
chaque run. Un fichier inchangé n'est pas réécrit.

**Ce qui arrête la composition** — rien n'est écrit, la table précédente reste :

| Conflit | Pourquoi on ne tranche pas |
| --- | --- |
| la table écrite range dans une autre lignée un groupe déjà publié | l'adresse d'une page ne se déplace pas (#836) |
| la table écrite reprend l'identifiant d'un groupe ajouté par un run, pour d'autres organes | deux groupes sous un nom |
| un lien repris nomme un prédécesseur que plus rien ne porte | une succession orpheline (#700) |

**Quelle table lire** (`groupes_config.chemin_table_groupes`) : celle du run si
elle existe **et** si son empreinte est celle de la table écrite telle qu'elle
est sur le disque ; sinon la table écrite. `CHEMIN_CONFIG_GROUPES` est résolu
une fois, au chargement du module — chaque étape d'un run est un processus neuf.

## La suite de tests ne lit jamais la table du run

La table du run revient sur un poste par la synchronisation des données. Mesuré
le 02/10/2026 en la posant dans un worktree : **26 tests au rouge**, parce que
les lecteurs appelés sans chemin se mettaient à la suivre. En local seulement —
le checkout de `tests.yml` ne matérialise pas ce fichier, la CI ne l'aurait
jamais vu.

`tests/conftest.py` pose donc `EMPREINTE_TABLE_GROUPES_ECRITE_SEULE=1` avant
tout import de `src/`, et `chemin_table_groupes()` rend alors la table écrite.
Avec la table du run sur le disque : 6 329 réussis, 0 échec. C'est le seul
usage de cette variable ; aucune étape du run ne la pose.

## Dans le workflow

| Endroit | Changement |
| --- | --- |
| `prepare-roster-matrix` | un step compose la table **avant** le roster, qui la lit |
| artifact `roster-candidats` | transporte aussi `raw_data/groupes_du_run.json` ; les shards et la fusion le téléchargent dans `raw_data` |
| `merge-and-pivot`, génération des fiches de groupe, de lignée, portail | ne passent plus `config/groupes_reels.json` en dur : le défaut résolu s'applique |
| commit de fin de run | `git add` de la table du run, **conditionnel** — un chemin absent est fatal pour `git add` |
| `extract-an` | la table du run précédent entre dans son checkout creux |

Aucun code de sortie de la composition n'arrête le job. Sans table composée, les
lecteurs retombent sur la table écrite : le run continue sur ce qu'un humain a
relu, et un groupe que seul un run avait ajouté laisse une fiche sans entrée,
sur laquelle le portail de qualité bloque. Dégradé et visible, jamais faux.

## Ce que cette décision remplace

`repertoire-config-1057` (21/09/2026) explique « pourquoi `groupes_reels.json`
n'est pas dérivable » par trois choses que le fichier garde. Deux ne tiennent
plus depuis les arbitrages du 02/10/2026 :

| Ce que #1057 disait non dérivable | Depuis le 02/10/2026 |
| --- | --- |
| la lignée — « un jugement, pas une lecture » | calculée par la règle de la moitié du plus petit des deux groupes, une fois, à l'entrée du groupe |
| la sélection des groupes qui méritent une fiche | tous les groupes de l'Assemblée depuis la XVe |
| `extraction_suspendue` | **inchangé** : une décision d'exploitation, dans la table écrite |

Le critère de #1057, lui, tient entièrement — qui écrit le fichier — et c'est lui
qui place la table du run dans `raw_data/` sous son propre nom.

## Mesuré

Archive AMO30 du 02/10/2026, table écrite d'`origin/main` (32 entrées) :

- la table composée porte l'empreinte de la table écrite, et **une seconde
  composition ne réécrit rien** ;
- un seul champ diffère de la table écrite : l'effectif de `LIOT-17`, 26 → 27 ;
- `NG` et `SOC` de la XVe sont signalés à fusionner (lot 2b, PR #1181).

## Ce qui n'a pas été vérifié

- **Aucun run n'a exécuté ce workflow.** Les modifications du YAML sont tenues
  par des tests qui lisent le fichier, pas par une exécution : le transport par
  l'artifact, le `git add` et l'ordre des steps ne seront prouvés qu'au premier
  run.
- **`extract-an` lit la table du run précédent**, pas celle du run en cours : il
  ne dépend pas de `prepare-roster-matrix`. Un candidat déclaré membre d'un
  groupe entré le jour même n'aura sa couverture juste qu'au run suivant.
- `scripts/generate_data_local.sh` passe toujours la table écrite en dur : en
  local, on lit ce qu'un humain a relu.
- Le coût d'une législature neuve pour la matrice roster.

## Alternatives écartées

- **Faire écrire le run dans `config/`.** Écrasé au run suivant, et contraire à
  #1057.
- **Une seule table, dans `raw_data/`.** Une correction de nom ou un retrait ne
  pourrait plus se faire en PR : les données ne viennent que du dépôt public.
- **Lire la table du run dès qu'elle existe.** Une PR qui corrige la table écrite
  entre deux runs serait ignorée de tous les outils locaux, sans un mot.
- **Tout recalculer à chaque run, sans rien garder.** Un lien pourrait bouger
  sans relecture ; la propriétaire a demandé l'inverse.
- **Un job à part, au patron d'`extract-gouvernements`.** Le roster lit la
  table : la composer dans le même job, et la transporter dans le même artifact,
  garantit que la table et le roster d'un run sont ceux d'une même seconde
  (#518).
