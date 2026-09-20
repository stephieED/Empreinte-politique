# Un taux de rattachement se publie avec sa population, et ne bloque jamais, 07/09/2026

`2026-09-07`

> **En bref** — le dépôt établit lui-même des liens qu'aucune source ne donne (amendement → texte visé → dossier → commission, scrutin → dossier #758, texte porté → commission), chacun mesuré **une fois** le jour de son écriture et plus jamais : un rattachement qui tomberait de 61 % à 12 % ne bougeait aucun compteur ; d'où une section « Rattachements reconstruits » dans `audit_pipeline`, **jamais bloquante** — et c'est ce qui la sépare d'`audit_integrite_referentielle`, qui vérifie une propriété **binaire** (une clé résout ou c'est un bug) sans aucun seuil, là où un taux bas est le plus souvent le **silence de la source** ; la **population est publiée avec le taux, toujours**, le même rattachement valant **4 %** sur les 17 762 scrutins et **61 %** sur les 697 textes en dernière lecture (§2 règle 7, §9) ; les **deux crans** de l'index des amendements sont mesurés séparément — viser un texte nommé, et ce texte porter un dossier — parce que les fondre masquerait celui qui décroche ; l'audit **ne recalcule pas** la population « sur l'ensemble d'un texte », que §6 pin à `lecture.js` (#711), et le déclare ; **ce que la première mesure fait sortir** : l'index de la **14e législature déclare 6 textes visés pour 578 référencés**, soit **122/61 036** amendements rattachés — 60 914 publiés sans titre ni dossier, trou antérieur au lot et jusqu'ici invisible, montré et non réparé ; **défaut de mon fait, corrigé et consigné** : le premier jet faisait calculer les rattachements par `build_report` — qui **assemble et ne recalcule rien** —, ce qui faisait scanner le **corpus vivant** aux trois appels de `test_audit_pipeline.py` (§3b) et portait la suite de 56 s à **185 s** ; le calcul appartient au CLI, et le dossier lu est dérivé de `--profiles-dir`. 14 tests, quatre mutations vérifiées échouantes.

Ancres : `audit_rattachements`, `audit_rattachements.py`,
`_md_section_rattachements`, `audit_integrite_referentielle`, `build_report`.

## Contexte

Le dépôt établit lui-même plusieurs liens qu'aucune source ne donne : un
amendement vers le texte qu'il vise, un texte vers son dossier, un dossier vers
sa commission saisie au fond, un scrutin vers le dossier qu'il tranche (#758).
Chacun a été mesuré **une fois**, le jour où il a été écrit, et plus jamais.

Rien ne les suivait. Un rattachement qui tombe de 61 % à 12 % au run suivant —
index tronqué, convention de clé changée, shard en échec — ne bougeait aucun
compteur.

## Décision

Une section « Rattachements reconstruits » dans `audit_pipeline`. Six familles,
douze lignes sur le corpus publié.

### Ce n'est pas `audit_integrite_referentielle`, et c'est délibéré

Celui-là vérifie une propriété **binaire** — une clé publiée résout, ou elle ne
résout pas — et il **bloque**. Une clé orpheline est un bug, il n'y a aucun
seuil à choisir, et c'est ce qui lui donne zéro faux positif.

Ici la propriété est un **taux**, et un taux bas n'est pas un bug. Un scrutin
sans dossier, c'est le silence de la source : l'Assemblée ne publie aucune
référence législative sur ses scrutins (0/18 311, #762). Ranger ces absences à
côté des références orphelines les ferait lire comme des fautes, et diluerait
les fautes dans un tableau de taux. **Cette section ne bloque donc jamais**, et
le rendu le dit au lecteur avant de lui montrer un chiffre bas.

### La population est publiée avec le taux, toujours

Le **même** rattachement vaut **4 %** ou **61 %** selon le dénominateur : 714
scrutins sur les 17 762 publiés, mais 423 sur les 697 textes en dernière
lecture. Chaque ligne porte donc `resolus`, `total` et le nom de la population —
jamais un pourcentage seul (§2 règle 7 ; §9 : un taux sans sa population est une
erreur, pas une approximation).

### Deux crans, jamais fondus

Un amendement peut viser un texte que l'index ne **nomme** pas ; un texte nommé
peut n'être rattaché à **aucun dossier**. Les mesurer ensemble masquerait celui
des deux qui décroche — et c'est exactement ce qui se serait produit ici.

### Ce que l'audit ne calcule pas

La population « votes sur l'ensemble d'un texte » est sélectionnée par
`isWholeTextVote` / `cleDuTexteVote`, et AGENTS.md §6 fixe que le repli et la
sélection vivent **uniquement** dans `web/UI_finale/src/utils/lecture.js`
(#711). La redire en Python en ferait une seconde source qui divergerait.
L'audit rapporte donc les populations qu'il peut nommer sans dupliquer cette
sélection, et **déclare** celle qu'il ne couvre pas — d'où la note portée par la
ligne `scrutin_vers_dossier`, qui explique que son taux bas est attendu.

## Un défaut de mon fait, corrigé et consigné

Le premier jet faisait calculer les rattachements **par `build_report`**, sans
argument. Deux règles cassées d'un coup :

- `build_report` **assemble et ne recalcule rien** — c'est écrit dans sa
  docstring depuis toujours ;
- les trois appels de `test_audit_pipeline.py` se sont mis à scanner le corpus
  vivant, ce qu'AGENTS.md §3b interdit. Le fichier est passé de **3,2 s à 50 s**,
  et la suite complète de 56 s à **185 s**.

Le calcul appartient au CLI, et le dossier lu est **dérivé de `--profiles-dir`** :
un CLI pointé sur des fixtures lit les fixtures. Deux tests le verrouillent —
`build_report` ne doit jamais appeler la mesure lui-même, et le call site doit
passer le dossier.

La leçon est celle que le dépôt écrit ailleurs : **un audit est un consommateur
comme un autre**, et le brancher au mauvais étage lui fait lire ce qu'il ne
devrait pas.

## Ce que la première mesure a fait sortir

| rattachement | population | résolus |
| --- | --- | ---: |
| amendement → texte visé | amendements, **lég. 14** | **122 / 61 036 — 0,2 %** |
| amendement → texte visé | amendements, lég. 15 | 208 591 / 209 488 |
| amendement → texte visé | amendements, lég. 16 | 137 160 / 137 205 |
| amendement → texte visé | amendements, lég. 17 | 101 874 / 102 015 |
| dossier amendé → commission | dossiers visés | 922 / 974 |
| scrutin → dossier | tous les scrutins | 714 / 17 762 |
| texte porté → dossier | textes portés | 423 / 423 |
| texte porté → commission | textes portés | 316 / 423 |

**L'index de la 14e législature déclare 6 textes visés pour 578 référencés** :
60 914 amendements y sont publiés sans titre de texte et sans dossier. Le trou
existait avant ce lot ; il était simplement invisible. Il n'est pas corrigé ici
— cet audit le montre, il ne le répare pas.

## Alternative écartée

**Verser ces taux dans `audit_integrite_referentielle`.** Elle aurait donné une
seule section à lire, mais forcé à choisir un seuil de blocage pour chaque
jointure — et un seuil est précisément ce que ce module n'a pas. Le premier
taux à 0,2 % aurait bloqué tous les runs sur un fait ancien et connu.
