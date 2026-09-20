# Le sort d'un texte entre dans la fiche, à côté de son stade et jamais à sa place (#743 dans #328), 07/09/2026

`2026-09-07`

> **En bref** — la demande était de **remplacer les étiquettes du sankey** par `textes_portes[].sort`, publié depuis #747 (423 entrées, 423 avec un sort) ; la mesure l'a décalée : **aucune barre n'est homogène en sort** — celle « non adopté » d'Édouard Philippe porte 2 navette, **1 adopté via 49.3** et 1 retiré, la barre finale « promulgué » de Gabriel Attal porte 6 CMP, 5 adoptés, **4 adoptés via 49.3** et 3 promulgués —, une étiquette ne pouvant nommer un sort qu'en mentant sur les autres, parce que la cascade a le **stade** pour axe et que le sort est **orthogonal** ; confrontation complète sur les 423 : **un seul désaccord**, le 49.3 de Philippe, où la figure écrit « non adopté » sur un texte adopté sans vote ; d'où le sort **par la liste** — deux faits, deux places, la pastille gardant le stade —, ce qui fait lire la barre « non adopté » de Jean-Luc Mélenchon comme **4 rejetés, 1 retiré, 1 en navette** là où elle donnait six textes indistincts ; le **49.3 nommé à côté de la figure et jamais dedans** (5 textes sur 414, quatre fondus dans « promulgué »), en **fait procédural** et en compte seul (§2 règle 4, §6) ; une **sélection par sort ne voile rien**, un segment agrégeant matière × porte ; le vocabulaire **déménage dans `utils/lecture.js`** — mêmes 9 valeurs que `KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL`, `depose` et `rejete_49_3` déclarés bien qu'absents du corpus —, et un sort nul affiche son **motif**, jamais un défaut (§2 règle 5) ; premier test du dépôt qui compare **le frozenset Python au dictionnaire JS**.

Ancres : `LIBELLE_SORT_TEXTE`, `MOTIF_SORT`, `SORTS_PROCEDURE_49_3`,
`estProcedure49_3`, `cascadeDesTextes`, `textesDeLaSelection`, `croise`,
`ListeCascade`, `Cascade`, `KNOWN_SORTS_TEXTE_PORTE`,
`KNOWN_MOTIFS_SORT_NON_RESOLU`.

## Contexte

`textes_portes[].sort` est publié dans `pivot_data/` depuis #747 : **423
entrées, toutes portées par les 13 candidats déclarés, 423 avec un sort
renseigné, 0 nul**. La demande était de **remplacer les étiquettes du sankey**
par ce sort, pour qu'« adopté par 49.3 » apparaisse.

## La mesure qui a décalé la demande

Aucune barre de la cascade n'est homogène en sort. Sur les cinq candidats dont
la figure se dessine :

| barre | textes | sorts qui la composent |
| --- | ---: | --- |
| Philippe · « non discuté en séance » | 127 | 124 navette, 3 retirés |
| Philippe · « non adopté » | 4 | 2 navette, **1 adopté via 49.3**, 1 retiré |
| Attal · « non adopté » | 6 | 4 rejetés, 2 navette |
| Attal · barre finale « promulgué » | 18 | 6 CMP, 5 adoptés, **4 adoptés via 49.3**, 3 promulgués |
| Retailleau · « non promulgué » | 14 | 12 adoptés, 2 rejetés |

Une étiquette de barre ne peut donc nommer un sort qu'en mentant sur les
autres. La cause est structurelle : **la cascade a le STADE pour axe** — jusqu'où
le texte est allé — et le sort est **orthogonal** : ce qu'il est devenu. Un
texte adopté par 49.3 se range là où son stade le met.

Confrontation complète de la négation portée par la figure au sort publié, sur
les 423 entrées : **un seul désaccord**, et c'est le 49.3 d'Édouard Philippe —
la figure écrit « non adopté » là où la source dit adopté sans vote.

## Décision

**Le sort entre par la liste, pas par les étiquettes.** Chaque texte porte deux
faits distincts et deux places distinctes : la pastille de droite garde le
**stade** (rampe d'encre), la ligne du dessous donne le **sort**. Ce que ça
rend visible se mesure : la barre « non adopté » de Jean-Luc Mélenchon, six
textes indistincts jusqu'ici, se lit désormais **4 rejetés, 1 retiré, 1 encore
en navette**.

**Le 49.3 est nommé à côté de la figure, jamais dedans.** Cinq textes des 414
publiés ont été adoptés sans vote — quatre de Gabriel Attal fondus dans la
barre « promulgué », un d'Édouard Philippe dans une barre qui le contredisait.
Une ligne cliquable les compte et les nomme, en disant ce que c'est : un **fait
procédural**, jamais une position de vote (§2 règle 4). Un compte, jamais une
part (§6).

**Une sélection par sort ne voile pas la figure**, à la différence d'une
sélection par matière ou par cran. Un segment agrège (matière × porte) : les
cinq 49.3 y sont mêlés à des voisins qui n'en sont pas, et éteindre le segment
entier dirait « ces textes-là sont des 49.3 ». La sélection filtre donc la
liste, où chaque texte répond de lui-même.

**Le vocabulaire déménage dans `utils/lecture.js`.** Les neuf libellés vivaient
dans `data/pivotAdapter.js`, au service des seules fiches de gouvernement ; la
fiche candidat les lit maintenant aussi, et un vocabulaire écrit deux fois
divergera. Ce sont **les mêmes neuf valeurs** que
`KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL`, par construction — même fonction, même
source (`statutConclusion.fam_code`). `depose` et `rejete_49_3` ne sont portés
par aucun texte du corpus au commit `acd7f5b7` : ils sont déclarés quand même,
le vocabulaire étant celui du schéma et non celui des données du jour.

**Un sort absent affiche son motif**, jamais un sort par défaut (§2 règle 5).
Les quatre motifs de `KNOWN_MOTIFS_SORT_NON_RESOLU` ont leur libellé, bien
qu'aucun texte publié n'en porte aujourd'hui.

## Ce que les tests verrouillent, et une chose qu'ils font pour la première fois

`tests/test_sort_texte_porte_fiche_328.py` compare **le frozenset Python au
dictionnaire JavaScript** : un sort ajouté au schéma sans libellé, ou un
libellé qui décrit une valeur que la source ne produit pas, fait échouer la
suite. C'est le premier contrôle du dépôt qui tienne les deux langages sur le
même vocabulaire fermé.

## Alternative écartée

**Segmenter les barres par sort au lieu de la matière.** Elle rendrait le 49.3
visible dans la figure, mais au prix de la continuité de couleur par matière,
qui est ce que la cascade établit d'un bout à l'autre — et elle placerait sur
un même axe une progression et une issue, ce que la décision #743 interdit
explicitement.
