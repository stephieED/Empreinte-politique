<a id="finances-sociales-par-bloc-1053"></a>

# Comptes sociaux : les ressources se lisent bloc par bloc, la source les relie (#1053) (2026-10-13)

`2026-10-13`

> **En bref** — La collecte ne lisait que deux des cinq feuilles d'opérations du
> classeur de la Drees. Les trois autres donnent, avec la deuxième, les ressources
> de chacun des quatre blocs qui composent l'ensemble : la source relie donc chaque
> ressource au bloc qui la reçoit. `src/finances_sociales.py` les lit toutes, et
> refuse le classeur si les blocs ne font plus l'ensemble.

## Contexte

La maquette de la vue des caisses sociales (#1053) montrait l'origine des
ressources pour l'ensemble, sans lien vers qui les reçoit. Question de la
propriétaire, le 13/10/2026 : pourquoi ne pas tracer les flux des cotisations vers
la Sécurité sociale, le chômage et le reste ? La réponse donnée d'abord — « les
fichiers ne donnent pas ce lien » — était **fausse** : elle décrivait les deux
feuilles lues, pas le classeur. Relu en entier, il porte une feuille d'opérations
par bloc de la comptabilité nationale.

Mesuré le 13/10/2026 sur les 20 lignes et les années 2020 à 2024 : pour chaque
ligne de ressources, la somme des quatre blocs vaut la ligne de l'ensemble. En
2023, les 281 881 M€ de cotisations d'employeurs se répartissent en 280 243 M€ aux
administrations de sécurité sociale, 1 073 M€ aux sociétés, 566 M€ aux
administrations publiques.

## Décision

1. **Les cinq feuilles d'opérations sont lues**, sous cinq champs de
   `protection_sociale.champs`, nommés comme le sommaire du classeur nomme les
   blocs. La forme du fichier ne change pas : `finances-sociales-v1` reste.
2. **Une garde de plus** : sur chaque année commune, le total des ressources des
   quatre blocs vaut celui de l'ensemble. Elle porte sur le total et non sur chaque
   ligne, parce que la source elle-même ne range pas les cotisations de l'année
   provisoire sur les mêmes lignes dans l'ensemble et dans les blocs.
3. **Aucun libellé de bloc n'est traduit ici.** « Caisses de sécurité sociale »,
   « mutuelles, assurances, entreprises » sont des mots de maquette, à arbitrer
   avec le texte publié.

## Ce que la source ne donne toujours pas

- Le bloc des administrations de sécurité sociale **n'est pas découpé** : ni la
  vieillesse, ni la maladie, ni la famille, ni le chômage n'y ont leurs ressources
  propres. Le fichier de l'Unédic nomme ses recettes autrement, et les recoller à
  ces lignes serait une lecture, pas un fait de la source (§2 règle 2).
- Les montants sont **hors transferts** : ce que l'État reverse aux caisses n'est
  pas un lien de ce fichier.
- Les blocs ne sont détaillés que **de 2020 à 2024**.

## Alternative écartée

Déduire le « reste » par soustraction, ensemble moins administrations de sécurité
sociale : inutile, les trois autres blocs sont publiés, et une soustraction aurait
caché l'exception de 2024.

## Ce que cet épisode dit de la méthode

Une phrase qui ferme une piste (« la source ne le donne pas ») s'est écrite sur
deux feuilles d'un classeur qui en a douze, et a été publiée dans la fiche de
source et dans la décision de la veille. Elle se remesure sur l'objet entier avant
de servir.
