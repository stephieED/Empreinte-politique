# Une lignée n'est pas la somme de ses maillons (#836)

`2026-09-11`

> **En bref** — l'interface ne publiera qu'**une fiche par lignée** de groupe parlementaire (décision de la propriétaire, 10/09/2026), et cette fiche n'existait nulle part : ce lot en pose le schéma et la composition. **Elle ne s'obtient pas en additionnant les maillons** — mesuré sur la lignée socialiste `NG:15 → SOC:15 → SOC:16 → SOC:17`, la somme donne **170 membres** pour **96** personnes et **20 524** scrutins de cohésion pour **16 420**, les maillons n'étant pas disjoints ; et les `amendements_agreges` ne se dédoublonnent **pas du tout** au niveau des fiches, un amendement cosigné comptant une fois dans chaque maillon sans que rien ne dise que c'est le même — d'où un **recalcul** depuis `profiles[].amendements`, législature par législature pour ne pas rouvrir le défaut que #821 et #825 viennent de fermer. Trois régimes, donc : ce qui s'**unit** sur une clé (membres sur `membre_id`, cohésion sur `scrutin_id`, mandats sur `(categorie, label)`), ce qui se **recalcule**, et ce qui ne s'agrège **pas** — `position_politique` est publiée par législature par l'Assemblée (#686) et les réunir produirait un jugement que personne n'a porté (§2 règle 1), donc chaque maillon garde la sienne. L'ordre des maillons se lit sur `succede_a`, jamais sur les dates, et un cycle est **refusé** plutôt que parcouru. L'identifiant de lignée est **déclaré** et non dérivé : par la racine il changerait le jour où un maillon antérieur est ajouté — MoDem, Horizons, LIOT et UDR restent à déclarer (#815) —, par le maillon le plus récent il changerait à chaque législature, et un identifiant qu'une collecte déplace casse les liens du site. Les fiches vivent dans `pivot_data/lignees/`, à part des maillons : le contrôle de perte raisonne par collection, et deux types de documents dans un même répertoire est le défaut que #630 a payé. **Ce lot ne livre pas le script de génération ni le câblage CI** — la brique est là, mesurée sur la lignée socialiste réelle, et ce qui l'appelle reste à écrire.

## Le besoin, et ce qui le rendait impossible

La barre de sélection de l'interface affichait **20 boutons**, dont trois
« Socialistes et apparentés » que rien ne distinguait. La propriétaire a
tranché le 10/09/2026 : **une fiche par lignée**, et le bouton mène à la
lignée, pas à sa fiche la plus récente.

Cette fiche n'existait nulle part, et elle ne pouvait pas exister avant #821 et
#825 : tant que chaque maillon comptait la carrière entière de ses membres, les
maillons se recouvraient et toute addition comptait les mêmes entrées deux ou
trois fois. Ces deux lots sont dans les données depuis le run du 10/09.

## Trois régimes, et c'est toute la difficulté

Mesuré sur `NG:15 → SOC:15 → SOC:16 → SOC:17`, corpus du 11/09/2026 :

| Champ | Somme des maillons | La lignée | Régime |
| --- | ---: | ---: | --- |
| `membres` | 170 | **96** | union sur `membre_id` |
| `cohesion_votes` | 20 524 | **16 420** | union sur `scrutin_id` |
| `mandats_agreges` | 2 924 | **984** | fusion sur `(categorie, label)` |
| `sources` | 263 | **133** | union sur `(type, url)` |
| `tags_thematiques_agreges` | 2 447 | **1 947** | **recalcul** depuis les profils |
| `amendements_agreges` | 88 709 | — | **recalcul** depuis les profils |

Les deux premiers chiffres avaient été mesurés indépendamment par la session UI
avant ce lot. Les retrouver **à l'unité près** par un autre chemin est la seule
vérification qui vaille ici.

## Ce qui ne s'agrège pas, et pourquoi c'est une règle et non un manque

`position_politique` est publiée **par législature** par l'Assemblée (#686) :
elle qualifie un organe, pas une lignée. Un groupe peut être qualifié autrement
d'une législature à l'autre ; écraser ces qualifications en une seule serait
produire un jugement que personne n'a porté — ce que §2 règle 1 interdit.
Chaque maillon garde la sienne, recopiée dans `maillons[]`.

`effectif` et `periode` sont des plages par fiche pour la même raison. La lignée
porte sa propre `periode` — première borne, dernière borne, `None` l'emportant
sur une fin — et un `effectif.cumul_historique` qui est le **cardinal de
l'union**, jamais une somme.

## L'ordre vient de `succede_a`, jamais des dates

Une fiche peut ne porter aucune `periode.debut` quand aucune de ses
appartenances n'est datée ; la chaîne, elle, est toujours déclarée. Un **cycle**
est refusé plutôt que parcouru : mieux vaut une lignée manquante qu'une lignée
qui boucle en silence.

## L'identifiant est déclaré

`lignee_id` vient de `raw_data/groupes_reels.json`, comme `succede_a`. Les deux
dérivations possibles bougent : **par la racine**, l'identifiant change le jour
où un maillon antérieur est déclaré — et c'est prévu, #815 en a quatre en
attente ; **par le maillon le plus récent**, il change à chaque législature. Un
identifiant qu'une collecte peut déplacer est un identifiant qui casse les liens
du site.

C'est cohérent avec ce que le dépôt dit déjà de `succede_a` : une relecture
humaine datée, pas un champ de l'AN — « l'Assemblée ouvre et ferme des organes,
elle ne les chaîne pas » (#700).

## Un répertoire à part

`pivot_data/lignees/`, et non `pivot_data/groupes/`. Le contrôle de perte
raisonne par collection, et deux types de documents dans un même répertoire est
exactement le défaut que #630 a payé sur `pivot_data/profiles/` : « 481 files,
one directory, one naming pattern — a glob returns 481 ».

## `amendements_index` n'est pas optionnel en pratique

Une entrée d'`amendements[]` ne porte qu'un `amendement_id` depuis #431 ; son
`sort` et son `type_deposant` vivent dans l'index partagé. Sans index, le compte
sort à **0** — vérifié. Ne pas le passer est un mode de test, pas un mode de
production, et la docstring le dit.

## Ce que ce lot NE livre PAS

**Le script de génération et le câblage CI.** La brique est posée et mesurée sur
la lignée socialiste réelle ; ce qui l'appelle — un exécutable, son entrée dans
le workflow, sa collection dans le contrôle de perte, son bloc au portail
qualité — reste à écrire. Les fiches ne sont donc **pas encore produites**.

**Les `lignee_id` dans `raw_data/groupes_reels.json`.** Dix lignées à déclarer,
une relecture humaine qui se fait à la main.

Suite complète à 4 474, 0 échec.
