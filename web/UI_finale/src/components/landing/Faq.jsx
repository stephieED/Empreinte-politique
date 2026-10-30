// Écrites une seule fois : la page /faq les lit ici (#951). L'accueil ne les
// porte plus depuis sa forme C.
export const QUESTIONS = [
  {
    question: 'Est-ce que c’est objectif ?',
    answer:
      'Le site ne donne ni note, ni classement, ni avis. Chaque fait (vote, mandat, texte porté, intervention) renvoie à sa source et à sa date de mise à jour. L’activité parlementaire est présentée telle qu’elle est publiée, sans commentaire.',
  },
  {
    question: 'D’où viennent les données ?',
    answer:
      'En France : les données que l’Assemblée nationale publie en libre accès (mandats, votes, textes, amendements, prises de parole) et celles du Sénat, qui ne contiennent que les appartenances. Les deux sont sous Licence Ouverte. Les mandats locaux viennent du Répertoire national des élus, à partir de 2020. Pour le Parlement européen : ses données en libre accès et les fichiers de ParlTrack (licence ODbL). Chaque fiche indique ses sources et sa date de mise à jour. Une donnée manquante est affichée comme manquante, jamais comme zéro.',
  },
  {
    question: 'Pourquoi pas de notation ?',
    answer:
      'Une note ou un classement résume, et cache autant qu’il montre. Le site présente les faits bruts (votes, textes portés, mandats) pour que chacun se fasse son propre jugement.',
  },
  {
    question: 'Pourquoi n’y a-t-il pas de taux de présence individuel ?',
    answer:
      'Un scrutin manqué ne dit rien du travail de la personne (commission, texte porté…) ni de ses raisons (absence justifiée…). Le site ne publie donc aucun taux individuel d’assiduité, de présence ou d’absence.',
  },
];
