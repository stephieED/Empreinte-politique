<a id="collecte-mandats-locaux-rne-922"></a>
# Collecter les mandats locaux : une catégorie à part, et une fin qu'on n'invente pas (#922) (2026-09-15)

`2026-09-15`

> **En bref** — `src/rne_opendata.py` lit les mandats locaux dans deux jeux sous
> Licence Ouverte 2.0, par l'API tabulaire plutôt que par 76 Mo de
> téléchargement. Trois choix portent le module : la catégorie est
> **`mandat_local`** et non `mandat_electif`, parce que ce dernier commande
> `chambres[]` ; la **date de fin est toujours nulle**, avec son motif, parce
> qu'aucun des deux jeux n'en publie ; et les trois fichiers de mandats déjà
> collectés ailleurs sont **refusés à l'entrée**.

## Contexte

Aucune fiche ne portait de mandat local. La source existe, son appariement est
réglé (table relue, #922) et sa borne est fixée à 2020
(#922, arbitrée le 15/09/2026). Restait la collecte.

## Trois choix, et pourquoi

### 1. `mandat_local`, jamais `mandat_electif`

`mandat_electif` n'est pas qu'une étiquette : `appliquer_chambres` en dérive
`chambres[]` et `chambre` (#493), et le schéma **compte les `mandat_electif`
sans chambre comme un défaut de collecte** (#492). Verser un conseiller régional
dans cette catégorie ferait sonner cette garde à tort, run après run — un conseil
régional n'est pas une chambre parlementaire et n'a pas vocation à entrer dans
`chambres[]`.

D'où une valeur neuve dans `KNOWN_CATEGORIES`, et `categorie_source: "rne"` dans
`KNOWN_CATEGORIE_SOURCES`. Les deux vocabulaires sont fermés : les étendre est un
geste, pas un effet de bord.

### 2. `fin: null`, toujours, avec sa cause

**Aucun des deux jeux ne publie de date de fin.** Ils portent `Date de début du
mandat` et `Date de début de la fonction`, jamais l'autre borne. On obtient une
suite de **débuts datés** et d'**états constatés à une date**.

« Maire du Havre depuis le 28/06/2020, constaté le 27/02/2026 » est sourçable ;
« jusqu'en mars 2026 » serait une inférence (§2 règle 5). D'où `fin: null`
**avec** `fin_non_resolue: {motif, constate_le}` — le patron de `sort_non_resolu`
(#747) : ni les deux, ni aucun des deux.

`actif` recopie **lequel des deux jeux** a rendu la ligne — le RNE ne publie que
des mandats en cours, les sortants que des mandats clos. Ce n'est pas une
déduction.

### 3. Les mandats déjà collectés ailleurs sont refusés à l'entrée

Le RNE porte aussi les députés, les sénateurs et les représentants au Parlement
européen. Nous les collectons déjà, avec leur propre datation. Les lire
publierait le même mandat **deux fois**, avec deux dates de début
potentiellement différentes, et rien ne dirait laquelle fait foi.

Le refus est **à la lecture**, comme `senat_opendata.TABLES_REFUSEES` : un filtre
à l'affichage laisserait la donnée dans `raw_data/`, où la fusion additive la
garderait indéfiniment (#729).

## Deux mécanismes que la mesure a imposés

**La déduplication se clé sur `(lieu, date de début)`, jamais sur le fichier.**
Un maire est publié deux fois — chez les conseillers municipaux avec la fonction
« Maire », et chez les maires. C'est le même mandat. Le RNE étant interrogé avant
les sortants, un mandat en cours n'est jamais rétrogradé par son jumeau clos.

**Les diacritiques se neutralisent pour comparer, jamais pour publier.** La
source écrit « Edouard » sans accent et « Jérôme » avec, dans le même fichier.
Comparer les chaînes telles quelles rate en silence : mesuré le 14/09/2026,
Édouard Philippe ressortait sans aucun mandat alors qu'il est maire du Havre.

## Vérifié contre la source, pas seulement contre des fixtures

Les tests n'ouvrent pas le réseau — la fonction d'appel est injectée. Mais une
fixture ne révèle pas que le monde a bougé (#726), donc le module a été exécuté
contre le vrai RNE le 15/09/2026 :

| Candidat | Résultat |
| --- | --- |
| Édouard Philippe | 2 mandats — maire du Havre, président de l'agglomération. L'appariement par date de naissance contourne l'accent |
| David Lisnard | 4 mandats, dont **un clos** (Cannes 2020, par les sortants) ; maire et conseiller municipal dédoublonnés en un seul |
| Marine Tondelier | Hénin-Beaumont clos, **conseil régional en cours** — celui que deux fichiers sur neuf auraient manqué |

## L'alternative rejetée

**Télécharger les CSV.** 76 Mo par run pour en utiliser quelques lignes, là où
l'API tabulaire filtre côté serveur : ~160 requêtes, une par (fichier, candidat).
C'est le même arbitrage que l'index des amendements (#639), en sens inverse —
là-bas le volume justifiait un cache, ici la sélectivité justifie l'API.

## Ce que ce lot ne fait pas

**Rien n'appelle encore ce module.** L'écriture dans les profils bruts et le job
CI restent à faire, sur le patron d'`extract-senat` (#885). `AGENTS.md` §7 garde
donc le RNE en « cité, pas encore collecté » jusque-là.
