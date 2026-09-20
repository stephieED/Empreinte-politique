<a id="fusion-additive-et-libelle-corrige-912"></a>
# Un libellé corrigé ne remplace pas l'ancien, il s'ajoute — et le dernier marqueur part enfin (#908, suite de #912) (2026-09-14)

`2026-09-14`

> **En bref** — [#912](libelles-senat-colonne-complete-912.md) a corrigé la colonne lue : `Culture` est devenu « Commission de la culture, de l'éducation, de la communication et du sport ». Le run du 13/09/2026 a publié **les deux**. La fusion des profils est additive, le libellé fait partie de la clé d'une appartenance, et un nom corrigé crée donc une entrée neuve au lieu d'en remplacer une. Mesuré sur le commit de données `d2a56641a` : **126 entrées sénatoriales sur `bruno-retailleau` pour 101 collectées**, 40 pour 32 sur `jean-luc-melenchon` — **33 doublons à l'écran**. Ce lot les retire, puis retire les 8 appartenances héritées de NosSénateurs et le marqueur lui-même. Après : **une** trace subsiste dans `profiles/`, et c'est une phrase.

## 1. Corriger une production ne corrige pas ce qu'elle a déjà produit

C'est la leçon, et elle vaut au-delà des libellés : **un correctif de normalisation a besoin d'un retrait nommé pour atteindre le corpus**. La fusion additive protège contre la perte (une collecte vide n'écrase jamais — `collecte-vide-necrase-jamais`), et c'est la même propriété qui fait survivre une forme périmée à côté de sa version corrigée.

Le contrôle de perte ne pouvait pas le voir : il compte ce qui **disparaît**, et ici rien ne disparaissait — 33 entrées étaient apparues.

## 2. Le critère, et l'erreur qu'il a failli commettre

Le bloc `mandat_senatorial` du brut porte ce que la collecte a rendu au dernier run. Les deux couches se contrôlent l'une l'autre (#729), et aucun export n'a besoin d'être retéléchargé.

Mais **le brut ne se compare pas au pivot tel quel**. `normalize_senat` transforme le libellé : « Groupe UMP » y devient « Groupe UMP (rattaché) ». La première version du critère désignait donc comme orpheline l'appartenance de `bruno-retailleau` au groupe UMP en 2011-2012 — **un fait que la source publie**. Le brut est passé par `normalize_mandats` avant comparaison, ce qui reproduit exactement ce que la chaîne publie.

Vérification que le critère porte dans les deux sens : après normalisation, **aucune** entrée attendue n'est absente du pivot. 101 contre 101, 32 contre 32. Un écart d'un seul côté distingue « le pivot en porte trop » de « les deux divergent ».

## 3. La garde du marqueur se fonde sur la mesure, pas sur l'estampille

La première garde refusait de retirer le marqueur tant qu'une appartenance **non estampillée** subsistait. Elle bloquait `jean-luc-melenchon` sur **18 entrées** qui sont des mandats de **député** — « Commission des affaires étrangères », 2017-2022. Une `categorie_source` absente veut dire « personne n'a établi cette catégorie » (#718), jamais « cela vient de NosDéputés ».

La garde reprend donc la mesure de [#890](retrait-marqueur-regards-citoyens-deputes-890.md) : un parcours **récursif**, **clés de dict comprises**, de ce que le document porte réellement. La même que celle qui a servi à compter — pour que la décision et le constat ne divergent pas.

Deux familles de champs en sont exclues, et pas pour la même raison :

| Champ | Pourquoi il ne compte pas |
| --- | --- |
| `sources`, `synchro_sources` | ils **sont** le marqueur — les compter le ferait se retenir lui-même |
| `couverture` | champ **dérivé**, recomposé à chaque run, dont les `preuve` sont des **phrases qui décrivent** la collecte |

## 4. Le résultat, mesuré

| | Avant | Après |
| --- | ---: | ---: |
| Entrées sénatoriales, `bruno-retailleau` | 126 | **101** |
| Entrées sénatoriales, `jean-luc-melenchon` | 40 | **32** |
| Appartenances héritées de NosSénateurs | 8 | **0** |
| Traces Regards Citoyens dans `profiles/`, deux couches | 11 | **1** |

La dernière est la phrase de `couverture[].preuve` de `bruno-retailleau`, qui raconte un certificat TLS expiré sur `archive.nossenateurs.fr`. Elle se recompose au run suivant.

`meta.licence_donnees` est **recomposé**, jamais réécrit : la clause ODbL de Regards Citoyens quitte le corpus, celle de **ParlTrack** reste due sur `jean-luc-melenchon` — source vivante, et c'est exactement la condition de retrait que `AGENTS.md` §7 annonçait comme s'exécutant d'elle-même.

## 5. Ce qui reste, et n'est pas de ce lot

Les **agrégats** portent encore 6 entrées `sources[]` de type Regards Citoyens — 4 sur les gouvernements, 2 sur les partis. Ils se recomposent depuis les profils au run suivant, et les réécrire ici ferait de ce script une seconde fabrique.

La phrase de `couverture` de `bruno-retailleau` est par ailleurs **devenue fausse** : elle affirme que « le Sénat est sorti du périmètre éditorial du produit », ce que #885 a cessé d'être vrai. Même famille que [`mesure-publiee-devenue-fausse-886`](mesure-publiee-devenue-fausse-886.md), et c'est un texte publié — donc un arbitrage, pas un correctif d'agent.
