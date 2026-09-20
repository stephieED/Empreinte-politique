import { Fragment } from 'react';
import Baseline from '../Baseline';
import { SOURCE_BADGE_VERIFIED } from '../../utils/lecture';
import './landing.css';

function CheckIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
      <path d="M2.5 9.5L9 3" stroke="#14151A" strokeWidth="1.8" strokeLinecap="round" />
      <path d="M5.7 4.8l1.4 1.4" stroke="#14151A" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

function ArrowIcon() {
  return (
    <svg
      className="hero-pipeline-arrow"
      width="18"
      height="12"
      viewBox="0 0 18 12"
      fill="none"
      aria-hidden="true"
    >
      <path
        d="M0 6h15M10 1l5 5-5 5"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

// Exemple fictif : aucune donnée candidate réelle (AGENTS.md §2).
const PIPELINE_STEPS = [
  {
    key: 'donnee-brute',
    label: 'Donnée brute',
    content: <code className="hero-pipeline-sample">{'{ vote: "pour", texte: "PJL exemple" }'}</code>,
  },
  {
    key: 'fait-source',
    /* « Vérifié » disait que nous contrôlons la donnée. Nous ne la contrôlons
       pas : nous la publions avec le lien vers la source qui la porte (#328). */
    label: 'Fait sourcé',
    content: (
      <span className="hero-pipeline-verified">
        <CheckIcon /> {SOURCE_BADGE_VERIFIED}
      </span>
    ),
  },
  {
    key: 'fiche-candidat',
    label: 'Profil',
    content: (
      <span className="hero-pipeline-card">
        <span className="hero-pipeline-avatar" aria-hidden="true" />
        Prénom Nom (exemple)
      </span>
    ),
  },
];

// Hero (#143) : promesse factuelle + micro-animation du pipeline donnée brute
// → fait vérifié → fiche candidat. Ses trois boutons (« Voir un profil
// candidat / de groupe / de gouvernement ») sont retirés par la forme C de #951 :
// ils menaient à une fiche prise par défaut, et la liste des candidats qui suit
// le Hero donne le choix dès l'arrivée.
export default function Hero() {
  return (
    <section className="landing-section landing-hero" aria-label="Présentation">
      <h1>L'explorateur neutre et sourcé des parcours politiques pour la présidentielle 2027.</h1>
      {/* LA BASELINE (#1026) remplace la sous-ligne « Des faits sourcés, sans
          note ni classement — à consulter par candidat, par groupe ou par
          gouvernement » : elle disait deux des trois traits, et la liste des
          candidats juste dessous dit déjà par où entrer. */}
      <Baseline className="baseline--bandeau" />

      <div className="hero-pipeline">
        <p className="hero-pipeline-caption">Le concept</p>
        <div className="hero-pipeline-steps">
          {PIPELINE_STEPS.map((step, index) => (
            <Fragment key={step.key}>
              <div className="hero-pipeline-step" style={{ animationDelay: `${index * 2}s` }}>
                <span className="hero-pipeline-marker" aria-hidden="true" />
                <span className="hero-pipeline-label">{step.label}</span>
                {step.content}
              </div>
              {index < PIPELINE_STEPS.length - 1 && <ArrowIcon />}
            </Fragment>
          ))}
        </div>
      </div>

    </section>
  );
}
