<a id="extrait-amendements-par-candidat-1273"></a>

# La fiche de candidat lit un extrait de l'index des amendements, écrit à la construction (#1273) (2026-10-09)

`2026-10-09`

> **En bref** — Une fiche de candidat qui a siégé à l'Assemblée restait blanche une dizaine de secondes : elle téléchargeait l'index entier des amendements de chaque législature. `sync-data` écrit désormais `profiles/<slug>.amendements.json`, les seules entrées que le profil référence et les textes qu'elles visent ; la fiche lit ce fichier, et l'index entier seulement s'il manque.

## Le contexte

Mesuré le 09/10/2026 sur le site en ligne (déployé à 6 h 38, heure de Paris),
Firefox 157 sans interface, machine de la propriétaire, candidats déclarés :

| Fiche | Contenu affiché à | Décompressé |
| --- | ---: | ---: |
| François Ruffin (trois chargements) | 10,6 s · 14,0 s · 11,7 s | 203,0 Mo |
| Jean-Luc Mélenchon (un chargement) | 10,3 s | non relevé |
| Bruno Retailleau, sans mandat à l'Assemblée (un chargement) | 3,9 s | 22,1 Mo |

Sur les 203 Mo de François Ruffin, 162 sont les index des XVe, XVIe et XVIIe
législatures : 587 667 amendements, dont son profil référence 48 786 (5 400
comme auteur principal, 43 386 comme cosignataire), soit 8 %. Le réseau n'est
pas le poste principal — 6,8 Mo transférés en trois secondes ; c'est la lecture
du JSON par le navigateur. `CandidateProfilePage.jsx` n'affiche rien tant que
tout n'est pas chargé.

## La décision

- `extraitDesAmendements` (`web/UI_finale/src/utils/extraitAmendements.js`)
  rend, pour une législature, les entrées référencées et leurs textes visés,
  dans la forme même de l'index. La jointure de `pivotAdapter.js` ne change pas.
- `sync-data.mjs` écrit un fichier par candidat déclaré qui référence au moins
  un amendement de l'Assemblée, à côté du vocabulaire de #1029.
- `loadAmendementsPour` (`src/data/index.js`) lit l'extrait. S'il manque, elle
  charge l'index entier comme avant : une fiche lente plutôt qu'une fiche sans
  amendements.
- Les index entiers restent copiés dans le site : la figure d'exécution et les
  fiches de groupe n'en dépendent pas, mais le repli ci-dessus oui.

Toutes les signatures sont gardées, cosignatures comprises : la fiche les joint
toutes, et n'en retenir qu'une partie changerait ce qu'elle publie.

## Les alternatives écartées

- **Afficher la fiche par étapes** : traite l'attente perçue, pas la cause, et
  demande à chaque section un état « en cours ». Reste possible ensuite.
- **Un indicateur de chargement seul** : la page n'est plus blanche, elle reste
  aussi lente.

## Ce qui n'est pas couvert

Les fiches de groupe et de gouvernement, non mesurées. Aucun téléphone. Le
« Profil introuvable » vu une fois sur cinq chargements, cause non établie.
