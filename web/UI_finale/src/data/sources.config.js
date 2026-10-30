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
    type: 'À venir — data.gouv.fr pour les parrainages, Journal officiel pour la liste',
    contenuCouvert:
      "Les parrainages validés, puis la liste officielle des candidats. Elle remplacera la liste tenue à la main pour dire qui est candidat. Les parrainages seront publiés sur data.gouv.fr, la liste par une décision au Journal officiel.",
    cadenceMiseAJour:
      "À venir. Article 3 de la loi du 6 novembre 1962 : les parrainages sont publiés au moins deux fois par semaine jusqu'au 12 mars 2027 à 18 h ; la liste des candidats, au plus tard le 26 mars 2027.",
    licence: 'Licence Ouverte 2.0 (Etalab) pour la décision ; other-pd pour les parrainages',
    implication: "Elle sera publiée comme les actes du Journal officiel. La forme 2027 n'est pas connue : data.gouv.fr ne publiait aucun jeu 2027 au 07/09/2026, et rien ne dit que 2027 reprendra celle de 2022.",
    perimetre: ['Suivi candidat'],
    couverturePeriode: null,
  },
  {
    id: 'assemblee-nationale-opendata',
    nom: 'data.assemblee-nationale.fr',
    type: 'Fichiers téléchargeables (ZIP)',
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
    type: 'Fichiers téléchargeables (base PostgreSQL, tableurs CSV)',
    contenuCouvert:
      "Les appartenances des sénateurs : mandats avec leur motif de début et de fin, groupes politiques, commissions, délégations, groupes d'études, d'amitié et de liaison, organismes extra-parlementaires. Chaque organe est nommé tel qu'il s'appelait à la date du mandat, et un mandat qui traverse un changement de nom est publié en deux périodes.",
    cadenceMiseAJour: 'Quotidienne.',
    licence: 'Licence Ouverte / Open Licence (Sénat)',
    implication: "Réutilisation libre sous réserve de mention de la source (attribution uniquement, pas de partage à l'identique).",
    perimetre: ['Senat'],
    couverturePeriode:
      "L'activité en séance n'est pas publiée : ce jeu de données ne contient ni scrutins ni comptes rendus de débats. Les fiches ne portent donc aucun vote et aucune prise de parole au Sénat. Les taux de présence publiés par le Sénat ne sont pas repris.",
  },
  {
    id: 'parltrack',
    nom: 'Parltrack',
    type: 'Fichiers téléchargeables (JSON compressé)',
    contenuCouvert: 'Mandats, votes et activité des eurodéputés au Parlement européen.',
    cadenceMiseAJour: 'Hebdomadaire (environ).',
    licence: 'ODbL v1.0',
    implication:
      "Réutilisation possible, mais toute republication sous forme de fichier téléchargeable doit reprendre la même licence (share-alike).",
    perimetre: ['PE'],
    couverturePeriode: null,
  },
  {
    id: 'parlement-europeen-opendata',
    nom: 'Parlement européen Open Data',
    type: 'Interrogation en ligne',
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
    type: 'Interrogation en ligne',
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
    type: 'Interrogation en ligne',
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
      "Aucune collecte automatique : mandats relus une fois à la main, complétés quand un candidat se déclare.",
    licence: 'Tous droits réservés (Assemblée nationale) — faits cités',
    implication:
      "Seuls des faits — une fonction, deux dates — sont repris, chacun avec son lien ; aucun contenu du site n'est reproduit.",
    perimetre: ['AN'],
    couverturePeriode: null,
  },
  // CITÉE, PAS OUVERTE (#1326). Les places de la XIVe ne sont dans aucun jeu
  // de données ouvert : elles viennent d'un fichier du site de l'Assemblée,
  // sous ses conditions (« Info site »), comme Sycomore. AGENTS.md §7.
  {
    id: 'places-hemicycle-xive',
    nom: "Places de l'hémicycle, XIVe législature (Assemblée nationale)",
    type: "Fichier publié sur le site de l'Assemblée",
    contenuCouvert:
      "Le siège de chaque député de la XIVe législature (2012-2017), au 20 juin 2017. Les données en libre accès de l'Assemblée ne le donnent pas pour cette législature.",
    cadenceMiseAJour: 'Aucune : la XIVe législature est close.',
    licence: "Conditions du site de l'Assemblée nationale : reproduction gratuite, sans usage commercial",
    implication: 'Seul le numéro de siège est repris, avec un lien vers le fichier.',
    perimetre: ['AN'],
    couverturePeriode: null,
  },
  {
    id: 'journal-officiel',
    nom: 'Journal officiel (Légifrance)',
    type: 'Actes collectés ; décrets de nomination relus à la main',
    contenuCouvert:
      'Tous les décrets, arrêtés et ordonnances parus depuis 2007. Pour les fonctions gouvernementales plus anciennes, les décrets de nomination sont cités un à un, après relecture.',
    cadenceMiseAJour:
      'À chaque mise à jour des données pour les actes. Les décrets relus à la main ne sont complétés que lorsqu’un candidat se déclare.',
    licence: 'Licence Ouverte 2.0 (Etalab)',
    implication: 'Réutilisation libre sous réserve de mention de la source (attribution uniquement).',
    perimetre: ['Gouvernement'],
    couverturePeriode: 'Les actes commencent au 1er janvier 2007.',
  },
  // WIKIPÉDIA ET WIKIDATA disent QUI est candidat, rien d'autre (AGENTS.md §7,
  // job `rafraichir-candidats`). Leurs textes disaient « suivi biographique
  // complémentaire » et « citations verbatim » : faux, corrigés le 16/09/2026.
  {
    id: 'wikipedia-fr',
    nom: 'Wikipédia',
    type: 'Interrogation en ligne',
    contenuCouvert:
      "La liste des candidats déclarés, lue dans l'article « Candidatures à l'élection présidentielle française de 2027 ». Seuls des faits sont repris, comme un nom ou une étiquette de parti, jamais de texte.",
    cadenceMiseAJour: 'À chaque exécution.',
    licence: 'CC BY-SA 4.0',
    implication: "Seuls des faits sont repris, sans reproduction du texte de l'article.",
    perimetre: ['Suivi candidat'],
    couverturePeriode: null,
  },
  {
    id: 'wikidata',
    nom: 'Wikidata',
    type: 'Interrogation en ligne',
    contenuCouvert:
      "Le numéro de chaque candidat déclaré à l'Assemblée nationale (P4123), qui relie sa candidature à sa fiche.",
    cadenceMiseAJour: 'À chaque exécution.',
    licence: 'CC0 1.0',
    implication: 'Domaine public : aucune restriction de réutilisation.',
    perimetre: ['Suivi candidat'],
    couverturePeriode: null,
  },
];

export default sourcesConfig;
