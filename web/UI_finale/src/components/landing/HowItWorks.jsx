import { useState } from 'react';
import sourcesConfig from '../../data/sources.config';
import './landing.css';

function IconSources() {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" focusable="false">
      <rect x="3" y="3" width="7" height="7" rx="1.5" fill="none" stroke="currentColor" strokeWidth="1.6" />
      <rect x="14" y="3" width="7" height="7" rx="1.5" fill="none" stroke="currentColor" strokeWidth="1.6" />
      <rect x="3" y="14" width="7" height="7" rx="1.5" fill="none" stroke="currentColor" strokeWidth="1.6" />
      <rect x="14" y="14" width="7" height="7" rx="1.5" fill="none" stroke="currentColor" strokeWidth="1.6" />
    </svg>
  );
}

function IconNormalize() {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" focusable="false">
      <path
        d="M4 4 L20 4 L14 12 L14 20 L10 20 L10 12 Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function IconTrace() {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" focusable="false">
      <rect x="2" y="9" width="9" height="6" rx="3" fill="none" stroke="currentColor" strokeWidth="1.6" />
      <rect x="13" y="9" width="9" height="6" rx="3" fill="none" stroke="currentColor" strokeWidth="1.6" />
      <line x1="9" y1="12" x2="15" y2="12" stroke="currentColor" strokeWidth="1.6" />
    </svg>
  );
}

const STEPS = [
  {
    id: 'sources',
    label: 'On part de sources ouvertes',
    // Une source à venir n'est pas encore une source (#951).
    stat: `${sourcesConfig.filter((s) => !s.aVenir).length} sources publiques`,
    detail:
      'Assemblée nationale, Sénat, Parlement européen, répertoire des élus : des données publiées par les institutions elles-mêmes, collectées automatiquement à chaque mise à jour.',
    Icon: IconSources,
  },
  {
    id: 'normalise',
    label: 'On rassemble les sources',
    stat: '1 format commun',
    detail:
      "Un programme range toutes les sources dans le même format. Quelques rapprochements, comme l'identité d'un candidat ou ses mandats d'avant 2002, sont relus par une personne et citent leur source.",
    Icon: IconNormalize,
  },
  {
    id: 'trace',
    label: 'On trace chaque fait à sa source',
    stat: 'Chaque fait → sa source',
    detail: "Un vote, un texte porté ou un mandat renvoie toujours au document officiel dont il provient.",
    Icon: IconTrace,
  },
];

export default function HowItWorks() {
  const [activeId, setActiveId] = useState(STEPS[0].id);
  const active = STEPS.find((step) => step.id === activeId) ?? STEPS[0];

  return (
    <section className="landing-section" aria-label="Comment ça marche">
      <h2>Comment ça marche</h2>
      <ol className="how-it-works-steps">
        {STEPS.map((step, index) => {
          const Icon = step.Icon;
          const isActive = step.id === activeId;
          return (
            <li key={step.id}>
              <button
                type="button"
                className={`how-it-works-step ${isActive ? 'active' : ''}`}
                aria-current={isActive ? 'step' : undefined}
                aria-describedby="how-it-works-detail"
                onClick={() => setActiveId(step.id)}
                onFocus={() => setActiveId(step.id)}
                onMouseEnter={() => setActiveId(step.id)}
              >
                <span className="how-it-works-step-number">{String(index + 1).padStart(2, '0')}</span>
                <span className="how-it-works-step-icon">
                  <Icon />
                </span>
                <span className="how-it-works-step-label">{step.label}</span>
                <span className="how-it-works-step-stat">{step.stat}</span>
              </button>
            </li>
          );
        })}
      </ol>
      {active.detail && (
        <p id="how-it-works-detail" className="how-it-works-detail" aria-live="polite">
          {active.detail}
        </p>
      )}
    </section>
  );
}
