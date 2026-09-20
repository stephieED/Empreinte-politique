# Une classe qui décide d'un fond ne se pose que sur un fond (#328) — 04/09/2026

`2026-09-04`

> **En bref** — trois défauts de couleur vivaient en production dans « En bref », trouvés **à l'écran** par la propriétaire alors que la suite était verte à **3 735 tests** : aucun ne regardait une couleur ; tous les trois viennent du **même geste**, une classe qui décide d'un `background` posée sur autre chose qu'un fond — les `<em>` de légende portaient la classe du **segment de barre**, donc `var(--parl)` (#3f5166) passait derrière un texte `var(--muted)` (#8b8794), soit **1,9:1** là où AA demande 4,5:1, et « 15 promulgué » était illisible ; les cinq pastilles prenaient `background: currentColor`, c'est-à-dire la couleur du **texte**, donc **toutes la même** — une légende qui n'identifie plus rien ; et `.cp-gc-tete-col--gouvernement ~ * .cp-gc-part--promulgue` partait de l'en-tête pour descendre sur **tous ses frères**, si bien que la barre « 2 promulgué » de la colonne **À l'Assemblée** était brune, quatrième effet compris : seul `promulgue` basculant, la colonne du gouvernement affichait une **barre à deux familles** ; d'où une teinte **déclarée une fois** sur la classe du stade (`--teinte`) et **lue deux fois**, en fond par le segment et en pastille par la légende, le libellé gardant `--muted` ; la **famille** (`--t1`…`--t5`) vient de la **colonne**, portée par la cellule elle-même (`piste={c}`) et non déduite du voisinage — **aucune couleur ne se décide par voisinage dans une grille**, où l'ordre du DOM ne dit rien de la colonne rendue ; la rampe **monte** sur les cinq stades de `STADES_PUBLIES`, là où elle descendait puis remontait (`inscrit_ordre_jour` plus clair que `examine_commission`) avec **deux stades voisins de valeur identique** (`discute_seance` = `examine_commission` = `--parl-line`), et ce n'est **pas une échelle de valeur** : un texte promulgué n'est pas « mieux » qu'un texte en commission (§2 règle 1), c'est l'ordre que la source publie ; limites déclarées — **le contraste n'est pas mesuré par un test**, les cinq tests ajoutés lisent le code exécuté et vérifient les rôles, et le bloc sombre de `.cp-gc` **ne s'applique jamais** (`index.css` déclare `color-scheme: light`, rendu vérifié **au pixel près identique** sous préférence système claire et sombre) mais reste en place, verrouillé par un test existant. 5 tests, cinq mutations vérifiées échouantes, suite complète à 3 754, 0 échec.

Trois défauts de couleur ont vécu en production dans « En bref », le bloc de
tête de la fiche candidat. Ils ont été trouvés **à l'écran**, par la
propriétaire, sur le site déployé. La suite était verte à **3 735 tests** ce
jour-là : aucun ne regardait une couleur.

## 1. Ce qui était faux, et pourquoi c'était le même geste

Les cinq stades d'un texte porté (`examine_commission`, `inscrit_ordre_jour`,
`discute_seance`, `adopte`, `promulgue`) coloraient les segments d'une barre.
Une seule classe par stade, et elle posait un `background`.

| Défaut | Ce qu'on voyait | Cause |
| --- | --- | --- |
| La légende illisible | « 15 promulgué » en gris sur brun plein, « 2 adopté » en gris sur bleu foncé | Les `<em>` de la légende portaient **la classe du segment**, donc son `background`. `var(--parl)` (#3f5166) derrière `var(--muted)` (#8b8794) : **1,9:1**, quand AA demande 4,5:1 |
| Les pastilles toutes grises | Cinq pastilles identiques devant cinq libellés différents | `background: currentColor` — la couleur du **texte**, qui est la même pour toutes |
| Une barre brune à l'Assemblée | « 2 promulgué », colonne « À l'Assemblée », en couleur du gouvernement | `.cp-gc-tete-col--gouvernement ~ * .cp-gc-part--promulgue` : le sélecteur part de l'en-tête et descend sur **tous ses frères**. Dans la grille, les cellules du parlement viennent après cet en-tête |

Un quatrième, plus discret, tenait au même endroit : seul `promulgue` basculait
au brun. Les quatre autres stades restaient bleus dans la colonne du
gouvernement, qui affichait donc **une barre à deux familles**.

## 2. La décision : une teinte déclarée une fois, lue deux fois

La classe du stade ne peint plus rien. Elle **déclare** `--teinte`, et deux
lecteurs s'en servent :

- le segment de barre la prend en **fond** (`.cp-gc-part`) ;
- la pastille de la légende la prend en **pastille** (`em::before`).

Le libellé de la légende garde `var(--muted)` : c'est la pastille qui identifie
le segment, jamais la couleur du texte.

## 3. La famille de teintes vient de la colonne, portée par la cellule

`.cp-gc-cell` déclare `--t1`…`--t5` dans la famille bleue, et
`.cp-gc-cell--gouvernement` les redéclare **toutes les cinq** dans la famille
brune. La cellule reçoit sa colonne du composant (`piste={c}`), elle ne la
déduit plus de sa position : **aucune couleur ne se décide par voisinage dans
une grille**, où l'ordre du DOM ne dit rien de la colonne rendue.

## 4. Cinq stades, cinq degrés, et la rampe monte

La rampe d'avant descendait puis remontait — `examine_commission` valait
`--parl-line`, `inscrit_ordre_jour` le plus clair `--parl-pale` — et deux stades
voisins partageaient exactement la même valeur : `discute_seance` reprenait
`--parl-line`. Deux segments voisins de la même couleur ne se distinguent pas.

`--t1` à `--t5` suivent l'ordre de `STADES_PUBLIES`, du plus clair au plus
saturé. **Ce n'est pas une échelle de valeur** : un texte promulgué n'est pas
« mieux » qu'un texte en commission (§2 règle 1). C'est l'ordre que la source
publie, et la rampe le rend lisible sans le noter.

## Alternative écartée

| Écartée | Pourquoi |
| --- | --- |
| Donner au libellé de légende la couleur du stade | `--gouv` (#8a6b4c) sur blanc vaut 4,6:1 : AA passe de justesse à 12 px, et cinq libellés de cinq couleurs se scannent moins bien qu'un texte homogène. La pastille suffit à identifier |
| Neutraliser le fond sur les `<em>` (`background: none`) | Aurait laissé en place la classe qui ment sur son rôle. Le prochain usage l'aurait reposée ailleurs |
| Corriger le sélecteur de frères en `~ .cp-gc-cell--gouvernement` | La grille ne garantit aucun ordre entre colonnes ; la seule source sûre de la colonne est le composant qui la rend |

## Ce qui n'est pas vérifié

- **Le contraste n'est pas mesuré par un test.** Les cinq tests ajoutés à
  `tests/test_grands_chiffres_328.py` lisent le code exécuté et vérifient les
  rôles — quelle classe pose un fond, quelle famille vient d'où, que la rampe
  monte. **Cinq mutations ont été vérifiées échouantes.** Un rapport de
  contraste, lui, demanderait un harnais que le dépôt n'a pas.
- Le rendu a été relu **à l'écran**, sur `gabriel-attal`, la fiche entière rendue
  par les composants de l'application avec les deux plis ouverts. Pas sur les
  treize.
- **Le bloc sombre de `.cp-gc` ne s'applique jamais** et n'a pas été retiré :
  `index.css` déclare `color-scheme: light`, que Firefox honore pour
  `prefers-color-scheme`. Vérifié par capture : le rendu est **au pixel près
  identique** sous préférence système claire et sombre. C'est du code mort, mais
  `test_le_bloc_a_ses_deux_themes` le verrouille délibérément, et le retirer
  dépasse ce lot.
