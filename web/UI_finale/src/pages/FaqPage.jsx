import StaticPage from '../components/StaticPage';
import { QUESTIONS } from '../components/landing/Faq';
import '../components/landing/landing.css';

/* LA PAGE /faq (#951). Les questions de l'accueil, dans la coque des pages
 * statiques. Forme retenue le 16/09/2026 sur maquette, entre trois : l'accordéon
 * de l'accueil — les questions se lisent d'un coup d'œil, la première est
 * ouverte pour montrer qu'une réponse se déplie.
 *
 * Les questions ne sont écrites qu'une fois, dans `landing/Faq.jsx` : l'accueil
 * les porte encore tant que sa forme C n'est pas posée. */
export default function FaqPage() {
  const sections = [
    {
      id: 'questions',
      body: (
        <div className="landing-faq-list">
          {QUESTIONS.map(({ question, answer }, i) => (
            <details className="landing-faq-item" key={question} open={i === 0}>
              <summary>{question}</summary>
              <p>{answer}</p>
            </details>
          ))}
        </div>
      ),
    },
  ];
  return <StaticPage eyebrow="Empreinte politique" title="Questions fréquentes" sections={sections} />;
}
