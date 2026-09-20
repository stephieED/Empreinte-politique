// Écrites une seule fois : la page /faq les lit ici (#951). L'accueil ne les
// porte plus depuis sa forme C.
export const QUESTIONS = [
  {
    question: 'Est-ce que c’est objectif ?',
    answer:
      'Empreinte politique n’attribue ni note, ni classement, ni avis. Chaque fait affiché — vote, mandat, texte porté, intervention — est relié à sa source primaire et à sa date de synchronisation. L’outil donne à lire l’activité parlementaire telle qu’elle est publiée, sans la commenter.',
  },
  {
    question: 'D’où viennent les données ?',
    answer:
      'De sources publiques, et d’abord des institutions elles-mêmes. Côté français : l’open data de l’Assemblée nationale (mandats, votes, textes, amendements, prises de parole) et celui du Sénat, dont le jeu de données ne porte que les appartenances, sans votes ni débats ; tous deux sous Licence Ouverte. Les mandats locaux viennent du Répertoire national des élus, à partir de 2020. Côté européen : l’open data du Parlement européen et les dumps ParlTrack (ODbL). Wikidata relie chaque candidat à sa fiche de l’Assemblée, et les mandats antérieurs à 2002 sont cités depuis Sycomore et le Journal officiel. La liste des candidats déclarés vient de Wikipédia, en attendant la liste officielle que publiera le Conseil constitutionnel. Chaque profil indique ses sources et sa date de dernière synchronisation ; une donnée manquante est affichée comme manquante, jamais remplacée par un zéro.',
  },
  {
    question: 'Pourquoi pas de notation ?',
    answer:
      'Une note ou un classement résume — et masque autant qu’il éclaire. Empreinte politique montre les faits bruts (votes, textes portés, mandats) pour que chacun se forme son propre jugement, plutôt que de le préformer à sa place.',
  },
  {
    question: 'Pourquoi n’y a-t-il pas de taux de présence individuel ?',
    answer:
      'Un scrutin manqué ne décrit ni le travail parlementaire ni ses motifs (commission, texte porté, absence justifiée…). Empreinte politique ne publie donc aucun taux individuel d’assiduité, de présence ou d’absence.',
  },
];
