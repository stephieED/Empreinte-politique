import './landing.css';

// Contenu éditorial : reformulation positive des règles éditoriales
// non-négociables (AGENTS.md §2 et §6) — jamais un aveu de manque.
const ITEMS = [
  {
    title: 'Aucun score, aucune note',
    detail:
      "Chaque fait parlementaire est décrit pour ce qu'il est, jamais ramené à un chiffre unique ou à une appréciation.",
  },
  {
    title: 'Aucun classement entre candidats',
    detail:
      "Les chiffres se lisent côte à côte, avec leur contexte — jamais ordonnés du meilleur au pire.",
  },
  {
    title: "Aucun taux individuel d'assiduité ou de présence",
    detail:
      "Un scrutin manqué ne décrit ni le travail parlementaire d'un candidat ni ses motifs — cette donnée n'est jamais publiée à l'échelle individuelle.",
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
