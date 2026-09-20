# Un champ d'identité publié ne meurt plus sans un run à perte déclarée (#601) (2026-08-30)

`2026-08-30`

> **En bref** — composer champ par champ fait qu'une valeur survit au silence de sa source ; assumé et écrit, la péremption déclarée étant écartée faute de pouvoir distinguer « la source ne dit plus » de « la source dit non ».

Conséquence assumée de la composition champ par champ, et elle n'allait pas de soi.

## La règle qui la produit

`fusionner_identite` applique §2.5 au niveau du champ : **une absence n'écrase
jamais une valeur connue**. Un champ que le nouvel écrivain ne renseigne pas
garde la valeur de l'ancien.

C'est ce qui répare #484 — le squelette du chemin minimal ne peut plus vider une
identité collectée. C'est aussi ce qui donne au champ une durée de vie qui ne
dépend plus de la source.

## Ce que ça implique

Sous fusion additive, **un champ que la collecte ne rend plus garde sa valeur
indéfiniment**. Si l'Assemblée nationale retire la `profession` d'un député,
notre profil continue de la publier. Seul un run `--no-merge` l'efface, et c'en
est un à **perte déclarée** (`allow_declared_losses`), pas un run ordinaire.

Une donnée peut donc survivre à sa source.

## La décision

**Assumer, et l'écrire.** C'est ce fichier : sans lui, la permanence serait une
propriété émergente que personne n'a choisie — le pire des deux mondes.

## L'alternative écartée : une péremption déclarée

Faire expirer un champ que la collecte ne rend plus depuis N runs.

Écartée parce qu'elle demande de distinguer **« la source ne dit plus »** de
**« la source dit non »**, et qu'aucune de nos sources ne fait cette
distinction : AMO30 ne publie pas de retrait, il cesse de publier. Une
péremption trancherait donc à leur place, en publiant une absence là où nous
n'avons qu'un silence — exactement ce que §2.5 interdit, et le contresens que le
bloc `couverture` de #539 existe pour éviter.

Le compromis « faire expirer et le déclarer » n'a pas été retenu non plus : il
faudrait choisir un N, et rien ne le fonde. Un seuil non mesuré publié comme une
règle est le défaut que #551 a coûté cher à démonter.

## Ce que ça ne change pas

La règle inverse tient toujours : une valeur **non vide** qui arrive écrase
normalement, donc une correction de la source atterrit au prochain run. La
permanence ne concerne que le cas où la source **se tait**.
