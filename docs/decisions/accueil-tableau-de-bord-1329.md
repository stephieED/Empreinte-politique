<a id="accueil-tableau-de-bord-1329"></a>

# L'accueil montre un croisement au lieu d'annoncer un procédé : frise des législatures et des gouvernements, Assemblée par groupe (#1329) (2026-10-23)

`2026-10-23`

> **En bref** — le site se présente comme un tableau de bord de la vie parlementaire et gouvernementale, et non comme un agrégateur : sa valeur est de **relier et donner à voir** des objets que les sources publient séparément. L'accueil, arbitré sur maquette le 22/10/2026 (version 24) puis ajusté le 23/10, le **montre** : sous la carte héro, une tuile **« Législatures et gouvernements · depuis 2012 »** en ligne de métro (deux voies, Assemblée et gouvernement, une station par Premier ministre, la dissolution en pointillé, aujourd'hui en jaune ; largeur d'une législature = ½ durée + ½ nombre de Premiers ministres ; verticale sur téléphone, le plus récent en haut) et une tuile **« L'Assemblée aujourd'hui par groupe »** (un secteur par groupe dans l'ordre des sièges, les 12 groupes nommés). « Le concept » (sources → collecte → empreinte) est retiré de la carte héro, dont les textes ne changent pas ; le **carrousel des analyses** y prend place, l'**événement des candidats en première diapositive jusqu'au 01/06/2027**, et sa tuile disparaît. La carte héro a **la hauteur de la diapositive la plus courte** et ne bouge pas au défilement : les plus hautes perdent d'abord des lignes de description, puis de titre. **Un Premier ministre à plusieurs gouvernements ouvre au clic le choix entre eux** (mois/année), à la place des pastilles I / II. **Au survol**, une bulle dit le fait propre à l'élément puis ce que la fiche montre : pour une législature ses dates et le groupe **que l'Assemblée déclare majoritaire** (rien pour la XVIIe, qui n'en déclare aucun), pour un gouvernement ses dates, pour un groupe son nom complet et ses députés. Le premier écran tient sous 800 px à 1 440 × 900 (bas des tuiles à 669 px).

## Contexte

L'ancien accueil présentait des portes (candidats, groupes, gouvernements) et
un procédé (« Le concept »). Le lecteur « ne sait probablement rien du projet. Il
ne faut pas qu'il soit perdu au premier regard » (propriétaire, 22/10/2026) : le
premier écran doit à la fois donner envie de cliquer et faire comprendre ce
qu'est le site. Une vue qui croise législatures et gouvernements le fait sans
texte de plus.

## Décision

- Les deux tuiles lisent le manifeste : `mode_fin`, les groupes rangés par siège
  médian et `groupe_majoritaire` par législature (écrits par
  `scripts/sync-data.mjs` depuis `legislatures.json` et les positions politiques
  des fiches de groupe). Tant qu'aucune législature n'est au manifeste, l'accueil
  garde les anciennes portes (`CommencerAExplorer`).
- Le groupe majoritaire est celui que l'Assemblée **déclare** (`position_politique
  = majorite`), sous son nom au jour de référence ; il n'est jamais déduit d'un
  décompte de sièges : à la date de référence, aucun groupe n'a 289 députés.
- Aucun classement (§2 règle 1) : les groupes sont dans l'ordre des sièges.
- L'analyse sur les violences sexuelles et sexistes prend le titre « Les
  violences sexuelles et sexistes dans les débats de l'Assemblée » : « à
  l'Assemblée » se lisait comme des violences commises dans l'Assemblée. Seul le
  titre change ; les données de l'article restent celles du 13/10/2026.

## Alternatives écartées

Les portes illustrées d'une miniature de leur fiche ; les variantes A/B/C/G/H/I/J ;
une frise à l'échelle exacte du temps, noms en escalier (« brouillon ») ; une case
par Premier ministre ; les législatures en accolades « pilule » ; un espacement par
le seul nombre de Premiers ministres (« problème d'échelle trop flagrant ») ;
groupes et candidats intégrés à la frise ; un menu de gouvernements ouvert au
survol, qui se referme quand la souris le rejoint et n'existe pas sur téléphone ;
une carte héro à la hauteur de la plus haute diapositive, qui laissait un vide sous
les plus courtes.
