# Tous les comptes d'une fiche de groupe se rapportent à une date, et elle est publiée (#653) (2026-08-31)

`2026-08-31`

> **En bref** — aucune des 7 fiches ne décrit la législature en cours, or trois compteurs disaient « aujourd'hui » et mesuraient en fait la **carrière ultérieure** des membres : `effectif.actuel` égalait exactement le nombre de membres portant un mandat électif ouvert (38/38, 85/85, 60/60 sur `LR`, `REN`, `LFI`) et `nb_membres_actifs` comptait leur commission **d'aujourd'hui** ; une `date_reference` dérivée — clôture de la période si toutes les appartenances sont refermées, génération sinon — est **publiée** dans la fiche et les trois compteurs s'y rapportent, renommés pour le dire (`a_la_date_de_reference`, `present_a_la_date_de_reference`) ; les valeurs annoncées à l'arbitrage **ne se reproduisent pas** (REN 85 → 169), et deux contrôles indépendants établissent les nouvelles — égalité avec les mandats de groupe clos le jour de la dissolution, et la contrainte « une seule commission permanente » (#656) retrouvée à l'unité près sur 4 fiches sur 5 ; sélectionner le mandat **ouvert à cette date** est ce qui rend le compteur juste (sans quoi les affaires sociales LFI tombent de 9 à 3), le cumul et le nombre d'entrées restant identiques au bit près.

Une fiche de groupe décrit **une législature**, et aucune des 7 publiées ne
décrit la législature en cours. Tout compteur ancré sur « aujourd'hui » y est
donc vide de sens. Trois l'étaient :

| Champ | Ce qu'il disait compter | Ce qu'il comptait réellement |
| --- | --- | --- |
| `effectif.actuel` | l'effectif du groupe | les membres de la XVIe **encore député⋅es le jour du run** |
| `mandats_agreges[].nb_membres_actifs` | qui siège à cette commission | les membres dont la commission **d'aujourd'hui** est celle-là |
| `membres[].actif` | membre du groupe | encore député⋅e aujourd'hui |

Aucun des trois ne décrivait le groupe : tous décrivaient la **carrière
ultérieure** de ses membres. Le défaut est le même que celui des dates
d'appartenance (`docs/decisions/dates-appartenance-groupe-653.md`), un cran plus
loin : là c'était la source de la date, ici c'est la date elle-même.

## La décision

**Une fiche de groupe porte une date de référence, et tous ses comptes s'y
rapportent.** Elle est **dérivée**, jamais devinée, sur un seul critère —
l'état des appartenances publiées :

- **toutes refermées** → la fiche décrit une législature close, la date est la
  plus tardive des fins (`2024-06-09` pour la XVIe, la dissolution) ;
- **au moins une ouverte** → la législature court, la date est celle de la
  génération.

Elle est **publiée** dans la fiche, sous `date_reference`, avec son origine
(`cloture_legislature` | `generation`) : un compteur daté qu'on ne peut pas
dater à la lecture est un compteur nu (AGENTS.md §2 règle 2).

Une fiche close est un **objet historique et figé** — ses scrutins, ses
amendements et son cumul de mandats l'étaient déjà. Seul ce qui prétendait au
présent était mal cadré.

## L'écart, mesuré

Sur les 5 fiches AN de la XVIe législature publiées en `3c8e1f0c`, membres
chargés depuis les profils pivot du même commit, roster dérivé de l'archive
AMO30 du 17/08/2026. Les trois compteurs, avant et après :

| Fiche | Membres | `effectif` avant | `effectif` après | Σ « qui y siège » avant | après | Σ cumul (inchangé) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `groupe-AN-REN-16` | 193 | 85 | **169** | 1 462 | 3 367 | 8 453 |
| `groupe-AN-RN-16` | 90 | 75 | **88** | 1 603 | 1 722 | 3 403 |
| `groupe-AN-LFI-16` | 76 | 60 | **75** | 909 | 836 | 2 384 |
| `groupe-AN-LR-16` | 62 | 38 | **61** | 813 | 1 927 | 4 865 |
| `groupe-AN-SOC-16` | 31 | 27 | **31** | 445 | 493 | 1 398 |

`date_reference` vaut `2024-06-09` / `cloture_legislature` sur les cinq. Le
**nombre d'entrées** de `mandats_agreges` et le **cumul historique** sont
identiques au bit près sur les cinq fiches : ce lot déplace la date, il ne
retire ni n'ajoute d'entrée à une liste surveillée par `audit_diff_profils`.

Les six commissions les plus peuplées de `groupe-AN-LFI-16` :

| Commission | « siège » avant | après | Cumul |
| --- | ---: | ---: | ---: |
| Finances | 5 | **10** | 67 |
| Affaires sociales | 9 | **10** | 66 |
| Affaires économiques | 9 | **10** | 64 |
| Développement durable | 8 | **9** | 61 |
| Défense nationale | 6 | **9** | 59 |
| Lois | 8 | **9** | 58 |

## Les valeurs d'avant ne sont pas les valeurs de la clôture

Le cadrage a été arbitré en annonçant que `effectif` retrouverait les valeurs
d'avant le lot — LFI 60, REN 85, RN 75, LR 38, SOC 27. **Il ne les retrouve
pas**, et les anciennes valeurs n'étaient pas un décompte à la clôture :
re-mesuré profil par profil, `effectif.actuel` égale **exactement**, sur les
trois fiches vérifiées, le nombre de membres portant un `mandat_electif`
**ouvert** — 38/38 pour `AN:LR`, 85/85 pour `AN:REN`, 60/60 pour `AN:LFI`. Ce
sont les réélu⋅es de 2024, pas les membres du groupe en juin 2024.

Deux contrôles indépendants établissent que les nouvelles valeurs sont bien
celles de la clôture :

1. **Elles égalent le nombre de mandats de groupe se terminant le jour de la
   dissolution** — 169, 88, 75, 61, 31 sur les cinq fiches, sans écart. Qui est
   dans le groupe à sa dissolution y a un mandat qui se ferme ce jour-là.
2. **Elles sont retrouvées par une contrainte institutionnelle que le calcul
   n'utilise pas** : un⋅e député⋅e ne siège qu'à **une** commission permanente à
   la fois (#656). La somme des huit commissions permanentes vaut 31, 88, 75 et
   61 sur `SOC`, `RN`, `LFI` et `LR` — **exactement l'effectif**. Sur `REN` elle
   vaut 170 pour 169 : 164 membres comptés une fois, **3 comptés sur deux
   commissions** au 2024-06-09 (`eric-poulliat`, `guillaume-gouffier-cha`,
   `emilie-chandler`) et 2 sur aucune. Le chevauchement d'un jour à la bascule
   est précisément ce que #656 a mesuré — 12 des 452 acteurs ont deux
   commissions permanentes ouvertes le même jour.

Sous l'ancienne règle, aucune de ces deux identités ne tient.

## Les noms cessent de mentir

« Actuel » et « actifs » disent un présent que la fiche n'a pas. Les trois
champs portent désormais la date à laquelle ils se rapportent :

| Avant | Après |
| --- | --- |
| `effectif.actuel` | `effectif.a_la_date_de_reference` |
| `mandats_agreges[].nb_membres_actifs` | `mandats_agreges[].nb_membres_a_la_date_de_reference` |
| `membres[].actif` | `membres[].present_a_la_date_de_reference` |

Les noms sont longs, et c'est le point : ils renvoient à `date_reference`, qui
est dans le même fichier. Un nom court qui se lit « aujourd'hui » est ce qui a
produit le défaut.

`periode.actif` n'est **pas** renommé ni rapporté à la date : il décrit la
**période** du groupe, pas un effectif à un instant. `false` sur une
législature close est exact.

## Ce qu'il a fallu corriger en plus, et pourquoi

Rapporter `nb_membres_actifs` à la date de référence ne suffisait pas.
`_select_mandat_entree_unique` (#656, inchangé) choisit, parmi les mandats en
doublon d'un même membre pour un même `(categorie, label)`, celui qui est
`actif` — donc, pour un⋅e réélu⋅e, sa commission de la législature
**suivante**, qui ne couvre pas la clôture de celle que la fiche décrit.

Mesuré sur `AN:LFI-16` : **1 000 des 2 384 entrées** ont plusieurs candidats.
En n'évaluant que l'entrée choisie, la commission des affaires sociales tombe
de 9 à **3** membres siégeant et celle des lois de 8 à **1** — et le mandat
publié serait celui d'une autre législature que le drapeau qui l'accompagne.

`_select_mandat_a_la_date` préfère donc un mandat **ouvert à la date de
référence**, et délègue à `_select_mandat_entree_unique` à défaut. La règle de
#656 est appelée, jamais réécrite ; sa forme à trois champs, son tri et sa copie
sont intacts.

Un mandat **sans date de début** ne compte comme ouvert à aucune date :
`_intervals_overlap` traite une borne absente comme non bornée, ce qui le ferait
couvrir toutes les dates. Mesuré : 0 des 7 249 entrées retenues de `AN:LFI-16`
et `AN:LR-16` est dans ce cas — le garde-fou ne retire rien, il empêche une
donnée manquante de se compter comme un siège (AGENTS.md §2 règle 5).

## Les deux fiches Sénat

`groupe-Senat-LR` et `groupe-Senat-SER` sont **gelées** (`extraction_suspendue`,
#516) : elles ne seront pas régénérées, donc elles **ne porteront pas**
`date_reference` et gardent `effectif.actuel` et `nb_membres_actifs`. C'est
pourquoi `date_reference` est **optionnelle** et n'entre pas dans
`REQUIRED_TOP_LEVEL_KEYS` : l'exiger les ferait échouer au portail de qualité,
qui hard-fail sur un schéma de groupe invalide. Une migration ne se paie pas en
cassant ce qui est déjà publié.

Conséquences assumées, chacune traitée là où elle se pose : `validate_profil_groupe`
valide le bloc **s'il est présent** ; `audit_groupe_dataset.CHAMPS_EFFECTIF` lit
les **deux** noms, faute de quoi l'audit publierait « 2 groupes non renseignés »
au lieu de leurs valeurs ; l'interface retombe sur une formulation **sans date**
plutôt que d'en inventer une.

## L'alternative écartée : garder « actuel » et le laisser à 0

Publier `effectif.actuel = 0` sur les cinq fiches, avec un avertissement
l'expliquant, était l'état de ce lot avant l'arbitrage. C'était exact —
personne n'appartient aujourd'hui à un groupe de la XVIe — et inutilisable :
`nb_membres_actifs` tombait à 0 partout du même coup, or c'est le chiffre de
tête de chaque carte de commission depuis #656. « 0 / 76 membres y siègent »
sur les huit commissions d'un groupe est une page fausse, qu'aucune légende ne
rattrape.

Le vrai défaut n'était pas la valeur, c'était l'**ancrage**. Une fiche
historique n'a pas de « maintenant », et lui en donner un — que ce soit 0 ou 85
— produit un chiffre qui ne décrit pas le groupe.
