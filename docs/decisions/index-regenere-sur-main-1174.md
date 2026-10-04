<a id="index-regenere-sur-main-1174"></a>
# Les deux index générés ne sont plus committés par les PR : `main` les régénère après la fusion (#1174) (2026-10-04)

`2026-10-04`

> **En bref** — #840 avait rendu l'index des décisions généré et conclu que le conflit devenait « structurellement impossible ». **C'est faux** : chaque PR committait encore le fichier, trié du plus récent au plus ancien, et le 02/10/2026 une seule fusion a mis **les quatre PR ouvertes** en conflit sur lui. Désormais une PR n'y touche plus : `.github/workflows/index-decisions.yml` régénère `docs/technical_decisions.md` et `docs/decisions-par-module.md` sur `main`, et `tests.yml` refuse une PR qui les modifie.

## 1. Le constat

`docs/decisions/index-decisions-genere-840.md` a supprimé l'**écriture à la
main**. Il n'a pas supprimé la cause du conflit : le fichier généré restait
committé par chaque PR, et deux décisions du même jour s'insèrent à la même
ligne, en tête.

Mesuré le 02/10/2026 à 19:05 (heure de Paris) : la fusion de la PR #1165 a mis
en conflit les quatre PR alors ouvertes — #1169, #1170, #1171, #1173 — sur le
seul `docs/technical_decisions.md`. Aucune ne recouvrait l'autre.
`docs/decisions-par-module.md` a conflicté trois fois le 23/09/2026.

Ce que #840 avait réellement gagné : la résolution se fait en régénérant, plus à
la main. Elle restait à refaire sur **chaque** PR ouverte après **chaque** fusion.

## 2. La décision

Arbitrée par la propriétaire le 04/10/2026, entre trois options.

1. **`.github/workflows/index-decisions.yml`** se déclenche sur un push vers
   `main` qui touche `docs/decisions/`, `src/*.py`, l'un des deux générateurs ou
   l'une des deux sorties. Il régénère les deux index et les committe, eux seuls.
2. **Une PR ne committe plus ces deux fichiers.** `tests.yml` lit la liste des
   fichiers de la PR par l'API — son checkout est partiel et sans historique —
   et échoue si l'un des deux y figure, en donnant la commande qui les remet à
   l'état de `main`.
3. **Les tests tiennent la sortie du générateur, plus le fichier du disque.**
   `test_lindex_et_le_repertoire_disent_la_meme_chose` et
   `test_lindex_conserve_toutes_les_ancres_dorigine` lisent `generer()`. Les
   deux tests de dérive (`test_lindex_committe_est_celui_que_le_script_produit`,
   `test_la_table_inversee_est_a_jour`) disparaissent : sur une branche qui
   ajoute une décision, la dérive est maintenant l'état normal.

Trois choix dans le workflow, chacun pour une raison :

| Choix | Raison |
| --- | --- |
| Il lit la tête de `main`, pas le commit de l'événement | deux fusions rapprochées lancent deux exécutions ; la seconde doit voir la première |
| Si `main` a bougé avant le push, il repart de la tête et régénère (trois essais) | un fichier généré ne se rebase pas, il se refait |
| Il ne tourne pas sur le dépôt public | le public reçoit le code par publication, index compris |

## 3. Ce que cela coûte, et ce qui n'est pas vérifié

- **Un commit automatique sur le `main` privé** après chaque fusion qui change
  un index. Un `main` local est donc en retard d'un commit après une telle
  fusion.
- **Ce commit ne déclenche aucun workflow** : il est poussé avec le jeton
  d'Actions. La suite ne tourne pas dessus ; il ne touche que deux fichiers
  qu'aucun test ne lit plus.
- **Entre la fusion et le commit de l'automate, l'index de `main` est en
  retard.** Un run de données qui épingle `main` dans cet intervalle publie un
  index auquel il manque la dernière décision, jusqu'au run suivant.
- **Une PR ouverte avant ce lot et qui a déjà committé un index** échoue sur le
  nouveau contrôle tant qu'elle ne l'a pas remis à l'état de `main`.
- **Non vérifié à l'écriture** : le workflow n'a pas été exécuté. Les droits ont
  été lus (jeton d'Actions en écriture par défaut, aucune protection sur `main`),
  pas éprouvés. Sa première exécution est la fusion de ce lot.

## 4. Alternatives rejetées

**Ne plus versionner l'index.** Les liens `docs/technical_decisions.md#<ancre>`
écrits dans des commentaires d'issues, hors du dépôt, ne mèneraient plus nulle
part — c'est ce que `test_lindex_conserve_toutes_les_ancres_dorigine` protège.

**Laisser tel quel.** Une régénération par PR ouverte après chaque fusion, à la
charge de chaque session, quand plusieurs travaillent en parallèle.

**Une stratégie de fusion dans `.gitattributes`.** Écartée par #840, non
remesurée ici.
