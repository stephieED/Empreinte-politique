<a id="libelles-senat-colonne-complete-912"></a>
# Le libellé d'un organe sénatorial se lit sur la colonne complète, pas sur l'abrégée (#912) (2026-09-13)

`2026-09-13`

> **En bref** — neuf des 133 appartenances sénatoriales publiées (2 candidats déclarés) s'affichaient coupées, cassées ou sans nom : **3** libellés tronqués à 60 caractères pile (`…audiovisuelle et à la télévisi`), **1** portant un octet cp1252 non converti, **5** absents. Une seule cause pour les deux premiers : `libcom` était lu sur `evelib`, l'abrégé. La table en porte quatre, et **420 de ses 571 lignes** portent un abrégé différent du libellé complet — `Culture` contre `commission de la culture, de l'éducation, de la communication et du sport`. Le découpage sur renommage de #885 fonctionnait ; il publiait trois fois le même mot. C'est le piège des colonnes `eve*` déjà payé sur `orgext`, jamais appliqué à `libcom`. Après correction, sur `bruno-retailleau` : **0** tronqué, **0** cassé, **0** sans nom.

## 1. Quatre colonnes, quatre contenus

| Colonne | Rempli | Long. max | Ce que c'est |
| --- | ---: | ---: | --- |
| `evelic` | 462 / 571 | 60 | le **code** — `AFCL` |
| `evelib` | 570 / 571 | 119 | l'**abrégé** — `Culture` |
| `evelil` | 462 / 571 | 352 | le complet, **en majuscules**, vide sur 109 lignes |
| **`libcomlilmin`** | **568 / 571** | 384 | **le complet, en casse normalisée** |

L'ordre retenu est `libcomlilmin` → `evelib` → `evelil` : le complet d'abord, l'abrégé en repli pour les 3 lignes qu'il est seul à porter, les majuscules en dernier recours. Aucune ligne ne reste sans nom.

**`evelil` ne suffisait pas**, et c'est ce qui rend le choix non évident : les trois libellés tronqués ont `evelil` **vide**. Se replier sur la colonne longue en majuscules les aurait laissés coupés.

## 2. Ce que ça change sur une fiche

| Période | Avant | Après |
| --- | --- | --- |
| 08/10/2014 → 01/10/2023 | `Affaires culturelles` | Commission des affaires culturelles |
| 04/10/2023 → 17/01/2024 | `Culture` | Commission de la culture, de l'éducation et de la communication |
| depuis le 18/01/2024 | `Culture` | Commission de la culture, de l'éducation, de la communication **et du sport** |

Le renommage du 12/12/2023 que #885 §3a donnait comme l'argument central de la réouverture — celui que le référentiel de l'Assemblée est incapable de dater — **était dans la source et n'atteignait pas le corpus**.

## 3. Le mojibake, et pourquoi `errors="replace"` ne le voit pas

**61 des 755 lignes de `com`** portent un caractère de la zone C1 : `U+0092` pour l'apostrophe typographique, `U+009C` pour `œ`. Aucune autre table utile n'en porte.

La source a encodé en UTF-8 des octets cp1252 **comme s'ils étaient du latin-1**. `0x92` est ainsi devenu la séquence `\xc2\x92` — de l'UTF-8 **valide**, qui décode en un caractère de contrôle. Notre lecture n'a donc aucune erreur à signaler, et le caractère ressort tel quel dans le libellé publié.

`senat_opendata.reparer_mojibake` remappe les **26** positions que cp1252 définit dans cette zone, à la lecture, pour toutes les tables. Les cinq positions que cp1252 laisse indéfinies ne sont **pas** devinées : les remplacer par l'apostrophe la plus probable produirait un texte qui a l'air juste (§2 règle 5).

## 4. Ce que ce lot ne fait pas

**Les cinq libellés absents ne sont pas comblés par une invention** — ils se sont résolus d'eux-mêmes une fois la bonne colonne lue, y compris l'étrange `Aucune (Président du Sénat)`, qui est ce que la source dit. Un organe sans ligne de libellé continuerait de sortir `libelle_non_resolu`, et c'est le bon comportement.

**Les agrégats ne sont pas recomptés ici.** Les libellés abrégés remontent aussi dans les fiches de gouvernement, de parti et de lignée ; l'effet du changement sur elles se mesure au run suivant, pas dans ce fichier.

## 5. Ce que l'incident dit des tests

Les **77 tests sénat passaient**. Aucun ne gelait la colonne lue : ils vérifiaient que le découpage produisait trois périodes, jamais que les trois portaient trois noms différents. Une fixture qui fournit son propre libellé ne peut pas révéler que la production en lit un autre — c'est la leçon de [`audit-champs-deplaces-726`](audit-champs-deplaces-726.md), appliquée à un autre étage.

D'où un test qui lit le **code** : il capture les colonnes que `composer_mandats` passe pour `libcom` et refuse que l'abrégé repasse devant.
