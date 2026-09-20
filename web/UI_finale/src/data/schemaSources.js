/* ── Le schéma des sources : ce que chacune apporte, et où cela se lit (#951) ──
 *
 * Retenu le 16/09/2026 sur maquette, entre un flux, une matrice et un schéma des
 * croisements : le flux est le seul qui répond à la fois à « d'où » et à « pour
 * quoi ».
 *
 * CHAQUE SOURCE DU SCHÉMA RENVOIE À SA CARTE (`config`), et un test vérifie les
 * deux sens : une source ajoutée à `sources.config.js` sans place dans le schéma
 * ferait mentir la figure, et l'inverse une carte manquante sous la figure.
 *
 * Ce qui est écrit ici vient de `docs/data-architecture.md` (« Les sources »),
 * du bloc `rafraichir-candidats` de `docs/workflow-generate-data.md` et
 * d'AGENTS.md §7. Aucun chiffre : une figure qui compte vieillit au run suivant.
 *
 * `url` : la page que le pavé ouvre, dans un nouvel onglet (demandé le
 * 16/09/2026). La page d'accueil du jeu de données, jamais un fichier.
 *
 * NOSDÉPUTÉS ET NOSSÉNATEURS NE SONT PLUS DANS LE SCHÉMA (16/09/2026). Mesuré par
 * Backend sur `origin/main` `dc80a10cb`, parcours récursif de `pivot_data/` :
 * aucune valeur publiée par le site n'en dérive, et aucun `licence_donnees` ne
 * cite Regards Citoyens. Quatre fichiers sénatoriaux gelés en dérivent encore
 * dans le dépôt, que le site ne publie pas : leur retrait est un lot backend.
 *
 * `statut` : `a-venir` (pas encore publiée ; dates de la loi, pas d'une
 * annonce), `collectee` (interrogée à chaque run), `citee` (relue à la main,
 * jamais interrogée). `teinte` : l'institution que la source sert, dans les
 * teintes de la frise ; `candidat` pour les deux sources qui disent QUI est
 * candidat et ne servent aucune institution.
 */

export const SOURCES_SCHEMA = [
  // EN TÊTE, et À VENIR : elle remplacera Wikipédia, qui la précède donc sur la
  // même donnée. Sa place dit que la suivante est temporaire (16/09/2026).
  { id: 'cc', nom: 'Conseil constitutionnel', teinte: 'candidat', statut: 'a-venir', config: 'conseil-constitutionnel',
    url: 'https://www.conseil-constitutionnel.fr/' },
  { id: 'wp', nom: 'Wikipédia', teinte: 'candidat', statut: 'collectee', config: 'wikipedia-fr',
    url: 'https://fr.wikipedia.org/wiki/Candidatures_%C3%A0_l%27%C3%A9lection_pr%C3%A9sidentielle_fran%C3%A7aise_de_2027' },
  { id: 'wd', nom: 'Wikidata', teinte: 'candidat', statut: 'collectee', config: 'wikidata',
    url: 'https://www.wikidata.org/wiki/Property:P4123' },
  { id: 'an', nom: 'Assemblée nationale', teinte: 'an', statut: 'collectee', config: 'assemblee-nationale-opendata',
    url: 'https://data.assemblee-nationale.fr/' },
  { id: 'sen', nom: 'Sénat', teinte: 'senat', statut: 'collectee', config: 'senat-opendata',
    url: 'https://data.senat.fr/' },
  { id: 'syc', nom: 'Sycomore', teinte: 'an', statut: 'citee', config: 'sycomore',
    url: 'https://www2.assemblee-nationale.fr/sycomore/recherche' },
  { id: 'jo', nom: 'Journal officiel', teinte: 'gouv', statut: 'citee', config: 'journal-officiel',
    url: 'https://www.legifrance.gouv.fr/' },
  { id: 'pe', nom: 'Parlement européen', teinte: 'pe', statut: 'collectee', config: 'parlement-europeen-opendata',
    url: 'https://data.europarl.europa.eu/' },
  { id: 'pt', nom: 'ParlTrack', teinte: 'pe', statut: 'collectee', config: 'parltrack',
    url: 'https://parltrack.org/' },
  { id: 'ev', nom: 'EuroVoc', teinte: 'pe', statut: 'collectee', config: 'eurovoc',
    url: 'https://op.europa.eu/fr/web/eu-vocabularies/dataset/-/resource?uri=http://publications.europa.eu/resource/dataset/eurovoc' },
  { id: 'rne', nom: 'Répertoire national des élus', teinte: 'local', statut: 'collectee', config: 'repertoire-national-des-elus',
    url: 'https://www.data.gouv.fr/datasets/repertoire-national-des-elus-1' },
];

// L'ordre des lignes est celui des sources qu'elles reçoivent : il limite les
// croisements de courbes, il ne classe rien.
export const DONNEES_SCHEMA = [
  { id: 'candidats', nom: 'La liste des candidats déclarés', de: ['cc', 'wp'] },
  { id: 'identifiant', nom: 'Leur identifiant à l’Assemblée', de: ['wd'] },
  { id: 'deputes', nom: 'Identité, mandats de député', de: ['an'] },
  { id: 'activite', nom: 'Votes, amendements, textes, paroles', de: ['an'] },
  { id: 'gouvernement', nom: 'Fonctions gouvernementales', de: ['an', 'jo'] },
  { id: 'senat', nom: 'Mandats au Sénat', de: ['sen'] },
  { id: 'anterieurs', nom: 'Mandats antérieurs à 2002', de: ['syc', 'jo'] },
  { id: 'europeen', nom: 'Mandat européen', de: ['pe'] },
  { id: 'activite-ue', nom: 'Activité européenne, titres français', de: ['pt', 'pe'] },
  { id: 'matieres', nom: 'Noms des matières européennes', de: ['ev'] },
  { id: 'locaux', nom: 'Mandats locaux, depuis 2020', de: ['rne'] },
];

export const FICHES_SCHEMA = [
  { id: 'candidat', nom: 'Fiche candidat', de: DONNEES_SCHEMA.map((d) => d.id), ligne: 4 },
  { id: 'groupe', nom: 'Fiche de groupe', de: ['deputes', 'activite'], ligne: 7 },
  { id: 'gouv', nom: 'Fiche de gouvernement', de: ['gouvernement', 'activite'], ligne: 9 },
];
