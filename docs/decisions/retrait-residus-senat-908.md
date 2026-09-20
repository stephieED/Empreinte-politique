<a id="retrait-residus-senat-908"></a>
# Le dernier marqueur Regards Citoyens part quand il ne couvre plus rien, et pas avant (#908) (2026-09-13)

`2026-09-13`

> **En bref** — [#890](retrait-marqueur-regards-citoyens-deputes-890.md) a retiré le marqueur `nosdeputes` / `nossenateurs` des profils de député et s'est arrêté aux deux qui touchent le Sénat : leur marqueur couvrait une carrière que rien d'autre ne portait. #885 a branché `data.senat.fr`, la carrière est publiée — 133 appartenances datées — et la condition que #890 posait est remplie. Mesuré le 13/09/2026 sur `origin/main` `0a919cb67`, par un parcours **récursif des deux couches, clés de dict comprises** : **11 traces** subsistent dans `profiles/`, sur 2 profils. Ce lot les retire, mais **entrée par entrée** : une table de 8 lignes écrite à la main, et une garde qui refuse le retrait du marqueur tant qu'une appartenance héritée subsiste.

## 1. Ce qui restait, ventilé par chemin de champ

| Chemin | Occ. | Couche | Nature |
| --- | ---: | --- | --- |
| `sources[].type` | 2 | pivot | la donnée |
| `sources[].url` | 2 | pivot | la donnée |
| `meta.synchro_sources.nosdeputes` | 2 | brut | une **clé**, pas une valeur |
| `couverture.*[].preuve` | 5 | pivot | une **phrase** qui décrit la source |

La ventilation par chemin n'est pas de la présentation : c'est elle qui montre la **nature** de ce qui reste, et c'est la nature qui décide. Les 5 `preuve` sont des phrases dérivées par `couverture_profil.deriver` — elles se recomposent, et les lister sous le même intitulé que la donnée a déjà coûté un lot. La clé brute ne se voit d'aucun parcours de **valeurs** : c'est le piège payé quatre fois en instruisant #885.

## 2. Une table écrite à la main, et non une règle de similarité

Une fois [#912](libelles-senat-colonne-complete-912.md) corrigé, **6 des 8** appartenances héritées s'apparient à l'identique. Une heuristique de similarité les prendrait aussi. Les deux dernières ne divergent pas dans le même sens :

| Hérité de NosSénateurs | Publié par le Sénat | Écart |
| --- | --- | --- |
| `Groupe Chrétiens d'Orient` | `Chrétiens d'Orient` | un mot **de plus** |
| `Groupe d'études Agriculture et alimentation` | `Groupe d'études Agriculture, élevage et alimentation` | un mot **de moins** |

Une règle assez souple pour les deux accepterait aussi `Groupe d'études Élevage`, qui est un organe **distinct**. C'est la faute de #878 dans l'autre sens, et la raison pour laquelle #908 écrivait « pas de remplacement en bloc ».

Chaque ligne a donc été vérifiée contre l'export : pour les deux libellés qui ne coïncident pas, la source ne porte **qu'un seul** organe candidat — `orgcod=919` pour l'agriculture, et un unique groupe de **liaison** « Chrétiens d'Orient », dont le remplacement corrige au passage la catégorie que l'entrée héritée donnait (`groupe_amitie`).

## 3. La garde, et le défaut qu'elle a révélé

Le marqueur ne part **que** si plus aucune appartenance non estampillée ne subsiste sur le profil. Tant qu'il en reste une, l'attribution ODbL est due (§2 règle 2) et l'entrée `sources[]` reste.

La première version de l'appariement proposait **17 mandats de député** de `jean-luc-melenchon` au retrait — « Commission des affaires étrangères », 2017-2022, Assemblée nationale. La cause est mécanique et vaut d'être écrite : `table.get(label)` rend `None` pour un libellé **absent de la table**, et cinq appartenances sénatoriales sont publiées **sans nom** (`libelle_non_resolu`, §2 règle 5). `None` était donc dans l'ensemble des libellés publiés, et `None in publies` valait vrai pour tout libellé inconnu.

C'est la même famille que le défaut corrigé sur `mandats_electifs_remplaces` en instruisant #885 : **un critère de retrait trop large efface un fait**. Deux fois sur le même module, par deux chemins différents.

## 4. L'ordre d'exécution, et pourquoi il n'est pas libre

Le script s'arrête aujourd'hui à **7 des 8** entrées. La huitième — « Commission de la culture, de l'éducation et de la communication » — attend son remplaçant : le corpus publie encore `Culture`, et #912 n'a pas encore régénéré.

Ce n'est pas une limite, c'est la garde qui fonctionne. La séquence est donc **contrainte** : corriger la colonne, régénérer, retirer. Retirer d'abord publierait un trou, et c'est précisément ce que #890 avait refusé de faire.

## 5. Ce que le script ne touche pas

Les **agrégats** — groupes, lignées, partis, gouvernements. Ils se recomposent au run suivant à partir des profils, et les réécrire ici ferait du script une seconde fabrique. Même partage que #890.
