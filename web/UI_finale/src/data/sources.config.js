// Config partagée des sources de données, factuelle et pure (pas de JSX).
// Reprise telle quelle depuis AGENTS.md §7 (Sources and licenses) et README.md
// (Source taxonomy, Coverage limits, Data freshness). Ne pas arrondir/inventer
// une cadence ou une licence : toute mise à jour de ces valeurs doit d'abord
// passer par AGENTS.md / README.md, puis être répercutée ici.
// Consommée par la section "Sources & fraîcheur" et par les tooltips de licence
// de la landing page — ne jamais hardcoder ces informations dans un composant.
//
// Ce tableau liste les sources dont le site publie des données, pas seulement
// celles qu'il interroge encore. NosDéputés/NosSénateurs y reste : elle n'est
// plus collectée, mais des champs publiés en dérivent, et l'attribution ODbL
// leur est due tant qu'ils sont là (#530).

export const sourcesConfig = [
  // À VENIR (#951). La liste officielle des candidats n'est pas encore publiée :
  // Wikipédia la remplace jusque-là. Les deux dates sont celles de la loi, jamais
  // une annonce : aucune n'a été faite au 16/09/2026, et le site dédié n'existe
  // pas encore. `aVenir` la retire du compte des sources de l'accueil.
  {
    id: 'conseil-constitutionnel',
    aVenir: true,
    nom: 'Conseil constitutionnel',
    type: 'À venir — site dédié à l’élection de 2027, non ouvert au 16/09/2026',
    contenuCouvert:
      "La liste officielle des candidats à l'élection présidentielle, et les parrainages validés. Elle remplacera Wikipédia pour dire qui est candidat.",
    cadenceMiseAJour:
      "À venir. Selon l'article 3 de la loi du 6 novembre 1962 : les parrainages sont rendus publics au moins deux fois par semaine, à mesure qu'ils arrivent et jusqu'au 12 mars 2027 à 18 h ; la liste des candidats est publiée au plus tard le 26 mars 2027, pour un premier tour le 18 avril 2027.",
    licence: 'Non connue à ce jour',
    implication: "Les conditions de réutilisation seront vérifiées à l'ouverture du site.",
    perimetre: ['Suivi candidat'],
    couverturePeriode: null,
  },
  {
    id: 'assemblee-nationale-opendata',
    nom: 'data.assemblee-nationale.fr',
    type: 'Dumps ZIP (open data)',
    contenuCouvert:
      "Seule source de l'activité parlementaire française : identité et mandats des députés, composition des groupes, votes officiels, amendements, dossiers législatifs, questions (questions.assemblee-nationale.fr) et débats en séance (Syceron). Le Sénat publie ses appartenances (data.senat.fr), jamais son activité en séance.",
    cadenceMiseAJour: 'Quotidienne.',
    licence: 'Licence Ouverte / Open Licence (Etalab)',
    implication: 'Réutilisation libre sous réserve de mention de la source (attribution uniquement, pas de partage à l\'identique).',
    perimetre: ['AN'],
    couverturePeriode:
      "Votes officiels disponibles pour les législatures 14 à 17, selon les dumps existants. Le jeu de données du Sénat n'en contient aucun : ses fiches ne portent ni vote ni prise de parole.",
  },
  {
    id: 'senat-opendata',
    nom: 'data.senat.fr',
    type: 'Open data (export PostgreSQL, extraits CSV)',
    contenuCouvert:
      "Les appartenances des sénateurs : mandats avec leur motif de début et de fin, groupes politiques, commissions, délégations, groupes d'études, d'amitié et de liaison, organismes extra-parlementaires. Chaque organe est nommé tel qu'il s'appelait à la date du mandat, et un mandat qui traverse un changement de nom est publié en deux périodes.",
    cadenceMiseAJour: 'Quotidienne.',
    licence: 'Licence Ouverte / Open Licence (Sénat)',
    implication: "Réutilisation libre sous réserve de mention de la source (attribution uniquement, pas de partage à l'identique).",
    perimetre: ['Senat'],
    couverturePeriode:
      "L'activité en séance n'est pas publiée : ce jeu de données ne contient ni scrutins ni comptes rendus de débats. Les fiches ne portent donc aucun vote et aucune prise de parole au Sénat. Les taux de présence que la source publie ne sont pas collectés — un taux de présence individuel n'est jamais publié ici.",
  },
  {
    id: 'parltrack',
    nom: 'Parltrack',
    type: 'Dumps LZMA (JSON)',
    contenuCouvert: 'Mandats, votes et activité des eurodéputés au Parlement européen.',
    cadenceMiseAJour: 'Hebdomadaire (environ).',
    licence: 'ODbL v1.0',
    implication:
      "Réutilisation possible, mais toute republication sous forme de jeu de données téléchargeable doit être partagée sous la même licence (share-alike).",
    perimetre: ['PE'],
    couverturePeriode: null,
  },
  {
    id: 'parlement-europeen-opendata',
    nom: 'Parlement européen Open Data',
    type: 'API REST + pages MEP',
    contenuCouvert:
      'Les mandats des député·es européen·nes, et l’existence et le titre français des documents européens (data.europarl.europa.eu).',
    cadenceMiseAJour: 'En direct (récupérées à chaque exécution, pas de cache hebdomadaire).',
    // UN SEUL LIBELLÉ, CC BY 4.0 (#983) : décision du Bureau du 16/12/2024, art. 4,
    // et la licence que l'API du portail déclare. www.europarl.europa.eu n'est
    // jamais interrogé, seulement lié.
    licence: 'CC BY 4.0',
    implication: 'Réutilisation libre sous réserve de mention de la source (attribution uniquement).',
    perimetre: ['PE'],
    couverturePeriode: null,
  },
  {
    id: 'eurovoc',
    nom: 'EuroVoc (Office des publications de l’Union européenne)',
    type: 'SPARQL',
    contenuCouvert:
      "Les noms français des matières européennes, quand le Parlement européen n'en donne que l'identifiant. Rien n'est classé ici : un identifiant sans nom est déclaré, jamais inventé.",
    cadenceMiseAJour: 'À chaque exécution.',
    licence: 'CC BY 4.0',
    implication: "Réutilisation libre sous réserve d'attribution et d'indication des modifications.",
    perimetre: ['PE'],
    couverturePeriode: null,
  },
  {
    id: 'repertoire-national-des-elus',
    nom: 'Répertoire national des élus (data.gouv.fr)',
    type: 'API tabulaire data.gouv.fr',
    contenuCouvert:
      "Les mandats locaux des candidats déclarés : conseils municipaux, mairies, conseils départementaux, régionaux et communautaires.",
    cadenceMiseAJour: 'À chaque exécution.',
    licence: 'Licence Ouverte 2.0 (Etalab)',
    implication: 'Réutilisation libre sous réserve de mention de la source (attribution uniquement).',
    perimetre: ['Local'],
    couverturePeriode:
      "Publiés à partir de 2020 seulement : avant cette date, l'absence d'un mandat local ne dit rien.",
  },
  // CITÉES, PAS COLLECTÉES (#860). Les mandats nationaux antérieurs à ce que
  // publie l'open data de l'Assemblée sont relus à la main, un par un, et
  // portés par les fiches avec leur lien (`mandats_anterieurs`). Aucun
  // collecteur n'interroge ces deux sites.
  {
    id: 'sycomore',
    nom: 'Sycomore (Assemblée nationale)',
    type: 'Fiches consultées, relues à la main',
    contenuCouvert:
      "Mandats de député antérieurs au 19 juin 2002, que l'open data de l'Assemblée ne rattache pas : fonction et dates, citées mandat par mandat avec un lien vers la fiche du député.",
    cadenceMiseAJour:
      "Aucune collecte : table relue une fois (raw_data/mandats_anterieurs.json), complétée quand un candidat se déclare.",
    licence: 'Tous droits réservés (Assemblée nationale) — faits cités',
    implication:
      "Seuls des faits — une fonction, deux dates — sont repris, chacun avec son lien ; aucun contenu du site n'est reproduit.",
    perimetre: ['AN'],
    couverturePeriode: null,
  },
  {
    id: 'journal-officiel',
    nom: 'Journal officiel (Légifrance)',
    type: 'Décrets consultés, relus à la main',
    contenuCouvert:
      "Fonctions gouvernementales antérieures à celles que publie l'open data de l'Assemblée : décrets relatifs à la composition du Gouvernement, cités fonction par fonction.",
    cadenceMiseAJour:
      "Aucune collecte : table relue une fois (raw_data/mandats_anterieurs.json), complétée quand un candidat se déclare.",
    licence: 'Licence Ouverte 2.0 (Etalab)',
    implication: 'Réutilisation libre sous réserve de mention de la source (attribution uniquement).',
    perimetre: ['Gouvernement'],
    couverturePeriode: null,
  },
  // WIKIPÉDIA ET WIKIDATA disent QUI est candidat, rien d'autre (AGENTS.md §7,
  // job `rafraichir-candidats`). Leurs textes disaient « suivi biographique
  // complémentaire » et « citations verbatim » : faux, corrigés le 16/09/2026.
  {
    id: 'wikipedia-fr',
    nom: 'Wikipédia',
    type: 'API MediaWiki REST',
    contenuCouvert:
      "La liste des candidats déclarés, lue dans l'article « Candidatures à l'élection présidentielle française de 2027 ». Seuls des faits en sont repris — un nom, une étiquette de parti —, jamais de texte.",
    cadenceMiseAJour: 'À chaque exécution.',
    licence: 'CC BY-SA 4.0',
    implication: "Seuls des faits sont repris, sans reproduction du texte de l'article.",
    perimetre: ['Suivi candidat'],
    couverturePeriode: null,
  },
  {
    id: 'wikidata',
    nom: 'Wikidata',
    type: 'SPARQL',
    contenuCouvert:
      "L'identifiant de chaque candidat déclaré à l'Assemblée nationale (propriété P4123), qui relie sa candidature à sa fiche.",
    cadenceMiseAJour: 'À chaque exécution.',
    licence: 'CC0 1.0',
    implication: 'Domaine public : aucune restriction de réutilisation.',
    perimetre: ['Suivi candidat'],
    couverturePeriode: null,
  },
];

export default sourcesConfig;
