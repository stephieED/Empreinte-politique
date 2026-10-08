<a id="parti-retire-de-la-fiche-candidat"></a>

# Le parti d'un candidat n'est plus publié par l'interface (#1251) (2026-10-07)

`2026-10-07`

> **En bref** — Le parti affiché sous le nom d'un candidat vient de `raw_data/candidats.json`, rempli depuis le tableau Wikipédia des candidatures et que personne n'a relu (`docs/decisions/boucle-perimetre-candidats-757.md`, « Le prix, assumé » ; #1251). La propriétaire a décidé le 07/10/2026 de le retirer de la fiche. **Il sortait à quatre endroits, et les quatre sont retirés** : la ligne sous le nom, la version de la fiche lisible sans JavaScript, la description de la page, les données structurées. Le groupe parlementaire, sourcé, reste. **Un libellé de groupe égal au parti n'est plus affiché non plus** : pour une personne sans groupe, le pivot recopie le parti dans `groupe`.

## Le contexte

Mesuré le 07/10/2026 sur `main` 1739b9c12, sur les 35 profils de candidats du
fichier qui ont un profil publié :

| Mesure | Valeur |
| --- | --- |
| Profils dont `parti` est renseigné | 35 sur 35 |
| Profils dont `groupe` est exactement le parti | 13 sur 35 |

Les 13 sont des personnes sans groupe parlementaire : Nathalie Arthaud, Marine
Tondelier, David Lisnard, François Asselineau, Karim Bouamrane, Sylvain Durif,
Anasse Kazib, Selma Labib, Francis Lalanne, Benoît Mathieu, Fabien Verdier,
Éric Zemmour, Mira Markovic. Leur fiche écrivait « Groupe Lutte Ouvrière (LO) »
ou « Groupe Sans étiquette ».

## La décision

- **Le parti n'est plus lu par l'interface** : ni `CandidateProfile.jsx`, ni
  `bloc-sans-js.mjs`, ni `metadonnees-pages.mjs`, ni `donnees-structurees.mjs`.
  Le manifeste des candidats ne le transporte plus.
- **Un libellé de groupe égal au parti ne s'affiche pas** (`memeLibelle`, dans
  `pivotAdapter.js`). La comparaison lit `pivot.parti`, qui reste dans le profil.
- **La ligne sous le nom se réduit** à « profession · Groupe X. Né le… », et à
  « profession. Né le… » pour une personne sans groupe.

## L'alternative écartée

Retirer la seule ligne sous le nom. Le parti serait resté dans la description
reprise par les moteurs de recherche et dans les aperçus de lien, pour la même
raison qu'on le retirait de la fiche.

## Ce qui reste, hors de ce lot

- **Les données portent toujours le parti**, et `groupe` le recopie pour 13
  profils : c'est la couche de données, pas l'interface. Le fichier de profil
  servi au navigateur les contient.
- `famillePolitique`, issu du même fichier, est toujours écrit dans le
  manifeste des candidats ; aucun écran ne le lit.
- Non vérifié à l'écran : la fiche n'a pas été capturée.
