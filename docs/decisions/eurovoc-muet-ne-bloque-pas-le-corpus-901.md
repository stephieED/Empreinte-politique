<a id="eurovoc-muet-ne-bloque-pas-le-corpus-901"></a>
# Un délai dépassé chez EuroVoc a coûté toute la publication d'un run (#901) (2026-09-17)

`2026-09-17`

> **En bref** — Le run `35194727922` a échoué parce que le point SPARQL de
> l'Office des publications a dépassé **une fois** son délai de 60 s, sur la
> requête des domaines ajoutée par #988 : aucune donnée n'a été commitée, profils
> compris. Chaque requête SPARQL est désormais réessayée deux fois. Et si les
> **domaines** restent muets, l'index est publié avec l'absence déclarée
> (`eurovoc_injoignable`) au lieu de faire échouer le run.

## Ce qui s'est passé

Run `35194727922`, étape « Générer l'index des documents européens », 10 h 40
(heure de Paris) : `requests.exceptions.ReadTimeout` sur `publications.europa.eu`,
levé dans `resoudre_domaines`, converti en `LibellesEurovocIndisponibles`, qui a
fait échouer l'étape puis le job `merge-and-pivot`. La requête des libellés, juste
avant, avait répondu.

Rejouée depuis une autre machine une heure plus tard, la même requête répondait
en **0,1 à 0,4 s**, par lots de 100 comme par lots de 25. La panne était
passagère.

Deux défauts de conception de #988, et ils sont à moi :

1. **Aucun nouvel essai.** Une seule requête lente suffisait.
2. **Un axe de couleur pouvait bloquer tout le corpus.** J'avais recopié pour les
   domaines la règle des libellés — lever plutôt que publier — sans me demander si
   la raison valait aussi pour eux. Elle ne vaut pas : un code nu est illisible,
   une matière sans domaine se lit.

## Décision

1. **`_interroger_sparql`** réessaie deux fois, après 5 puis 20 s, sur un délai
   dépassé, une coupure, un `429` ou une erreur `5xx`. Un `400` n'est pas réessayé.
2. **Les libellés** : après les essais, l'étape échoue toujours. Inchangé.
3. **Les domaines** : après les essais, `construire` publie l'index. Chaque
   matière porte `domaine: null`, chaque document déclare
   `domaines_non_resolu = {motif: "eurovoc_injoignable", codes}`. Le motif
   distingue « la question n'a pas pu être posée » de « le thésaurus ne rend pas
   de domaine » (`domaine_eurovoc_introuvable`), comme `portail_non_interroge` et
   `source_sans_concept` le font déjà pour les concepts.

## Alternatives rejetées

- **Allonger le délai** au-delà de 60 s : il ne couvre pas une coupure ni un
  `503`, et une requête qui répond en 0,4 s n'a pas besoin de plus.
- **Faire échouer seulement l'index des documents** et laisser le reste du run se
  poursuivre : l'étape est dans `merge-and-pivot`, dont l'échec empêche le commit
  de tout le corpus. Changer l'enchaînement des jobs pour un index est
  disproportionné.

## Vérification

`tests/test_eurovoc_reessais_901.py` : le faux serveur lève la même exception
que `requests` a levée en CI. Trois des cinq tests **échouent sur l'ancien code**
(nouvel essai après un délai dépassé, nouvel essai après un `503`, domaines muets
déclarés) ; les deux autres fixent ce qui ne devait pas changer (un `400` non
réessayé, des libellés muets qui font toujours échouer).
