import './landing.css';

// Contenu éditorial : reformulation positive des règles éditoriales
// non-négociables (AGENTS.md §2 et §6) — jamais un aveu de manque.
const ITEMS = [
  {
    title: 'Aucun score, aucune note',
    detail:
      'Chaque fait est présenté tel que la source le publie, sans chiffre unique ni appréciation.',
  },
  {
    title: 'Aucun classement entre candidats',
    detail:
      'Les chiffres sont présentés côte à côte, avec leur contexte. Aucun n’est classé.',
  },
  {
    title: "Aucun taux individuel d'assiduité ou de présence",
    detail:
      'Un scrutin manqué ne dit rien du travail d’un candidat ni de ses raisons. Le site ne publie donc aucun taux de présence individuel.',
  },
];

export default function WhatYouWontFind() {
  return (
    <section className="landing-section" aria-label="Ce que vous ne trouverez pas ici">
      <h2>Ce que vous ne trouverez pas ici</h2>
      <ul className="wontfind-list">
        {ITEMS.map((item) => (
          <li key={item.title}>
            <details className="wontfind-item">
              <summary className="wontfind-title">{item.title}</summary>
              <p className="wontfind-detail">{item.detail}</p>
            </details>
          </li>
        ))}
      </ul>
    </section>
  );
}
