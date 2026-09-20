# L'union des avertissements peut ressusciter un démenti, et deux familles Syceron s'éteignent (#600) (2026-08-30)

`2026-08-30`

> **En bref** — unir les warnings des deux écrivains fait ressusciter les démentis ; une intervention Syceron publiée éteint les deux familles de #560, les questions ne comptant pas.

`merge_raw_profile` et `merge_pivot_profile` faisaient `merged = dict(new)` : le
bloc `meta` du **dernier écrivain** était pris entier, et les `warnings` de
l'autre source **disparaissaient purement**. Le lot #600 les unit.

Unir crée un risque symétrique : un avertissement qu'un autre écrivain a démenti
**ressuscite**.

## Ce que l'union fait apparaître

Un job qui n'obtient pas l'archive Syceron écrit sa panne. Sur un profil où
l'autre écrivain — ou la fusion additive — a rendu les interventions, cette
panne est **fausse au moment où elle est publiée**. Prendre le `meta` du dernier
écrivain la masquait par accident ; l'unir la rendrait visible et fausse.

## La décision

**Une intervention Syceron publiée éteint les deux avertissements de #560** :
`interventions syceron indisponibles` (une panne : l'archive n'a pas répondu) et
`aucune intervention syceron` (un zéro constaté : l'archive a répondu, rien pour
cet `acteurRef`). Une intervention publiée dément l'un comme l'autre.

C'est l'**extension** de `_defaut_collecte_dementi_par_les_donnees`, qui fait
déjà cela pour les votes, les mandats et les amendements — pas un second
mécanisme.

**0 profil concerné au 30/08/2026.** C'est un garde-fou de l'union, pas une
reprise de corpus : il existe pour que le prochain passage d'un job ne republie
pas un démenti.

### Le critère est « une intervention qui n'est PAS une question »

Et non « des interventions ». Les questions parlementaires viennent de l'open
data de l'Assemblée nationale, pas de Syceron — le repli NosDéputés est parti
avec #510. Les compter éteindrait un constat sur Syceron avec la preuve d'une
**autre source**.

C'est le symétrique exact du critère déjà appliqué à
`WARNING_PREFIX_QUESTIONS_INDISPONIBLES`, qui ne s'éteint que sur une
intervention de `type_detail == "question"`.

## Ce que la décision ne change pas

**Aucun texte d'avertissement publié ne change.** Les libellés restent
identiques au caractère près : c'est ce qui rend reconnaissables les profils
publiés avant ce lot. L'extinction porte sur le moment où un avertissement
cesse d'être publié, jamais sur ce qu'il dit.

## L'alternative écartée

Unir sans étendre l'extinction. Écartée parce qu'elle publierait une panne que
le fichier dément — une absence publiée comme un fait, ce que le lot
#556/#558/#560 vient précisément de retirer, et que §2.5 interdit.
