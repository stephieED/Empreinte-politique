<a id="description-accueil-apres-recadrage"></a>

# Le titre et la description de l'accueil suivent le recadrage du 30/09 (2026-10-15)

`2026-10-15`

> **En bref** — le texte que montrent les moteurs et les aperçus de lien pour l'accueil disait encore le site d'avant le recadrage (`coeur-permanent-groupes-et-gouvernements`) : « Présidentielle 2027 : les parcours politiques des candidats, sourcés », et une description qui ne parlait que des candidats déclarés. Constaté par la propriétaire dans un résultat Google le 15/10/2026, et remplacé, sur trois formulations montrées, par sa **forme C** : titre « Empreinte politique : l'action politique, sourcée », description « Mandats, votes et textes des groupes parlementaires, des gouvernements et des candidats à 2027, tirés des données officielles. Sans note ni classement. » Le nom du site entre dans le titre ; les groupes et les gouvernements, cœur permanent, passent avant les candidats, complément borné à une élection.

Ancres : `index.html`, `pages-par-adresse.mjs`, `manifest.webmanifest`.

## Contexte

`index.html` porte le titre et la description de l'accueil dans `<title>`,
`description`, `og:` et `twitter:` ; `scripts/pages-par-adresse.mjs` les
remplace pour chaque autre adresse publiée, et une page sans description propre
garde celle de l'accueil, qui nourrit aussi les données structurées de
l'accueil (#969). Le recadrage du 30/09/2026 n'y avait pas touché.

## Décision

| | Avant | Après |
| --- | --- | --- |
| Titre | Présidentielle 2027 : les parcours politiques des candidats, sourcés | Empreinte politique : l'action politique, sourcée |
| Description | Mandats, votes et textes des candidats déclarés, par candidat, par groupe ou par gouvernement. Des faits sourcés, sans note ni classement. | Mandats, votes et textes des groupes parlementaires, des gouvernements et des candidats à 2027, tirés des données officielles. Sans note ni classement. |

La même description remplace celle de l'application installable
(`manifest.webmanifest`), qui disait encore « les parcours politiques par
candidat, par groupe ou par gouvernement ».

Le titre tient sous les 60 signes qu'un moteur affiche, la description sous 155.
Les titres par page de #969 ne changent pas : une fiche de candidat reste titrée
sur l'élection, ce qu'elle est.

## Alternatives écartées

- « Empreinte politique : groupes, gouvernements, candidats », avec une
  description qui datait la couverture « depuis 2012 » ;
- « L'action des députés et des gouvernements depuis 2012 », sans le nom du
  site ni les candidats.
