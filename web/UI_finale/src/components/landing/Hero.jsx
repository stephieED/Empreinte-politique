import { Fragment } from 'react';
import { Link } from 'react-router-dom';
import Baseline from '../Baseline';
import './landing.css';

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

/* LES TROIS CASES SONT TROIS LISTES DE MÊME FORME (30/09/2026), et c'est la
 * forme qui fait la démonstration : d'où ça vient, ce qu'on en fait, ce que ça
 * contient. Elles portaient trois registres — un exemple de JSON, une pastille
 * jaune, un avatar et un nom fictif — pour une même rangée.
 *
 * « AGRÉGATION » ET NON « TRAITEMENT » : la contrainte posée est l'absence de
 * connotation de transformation. « Traitement » ne dit pas sur quoi il porte et
 * se lit comme une retouche du fond.
 *
 * « L'EMPREINTE » SUR LA TROISIÈME CASE (arbitré le 30/09/2026). Elle a dit
 * « Les parcours » d'abord, choisi parce que « parcours » était le mot du titre
 * six lignes plus haut. Ce titre a changé le même jour, si bien que la raison est
 * tombée avant la case. « L'empreinte » nomme ce que la collecte produit avec le
 * nom du site — et « parcours » ne figure plus nulle part sur l'accueil, ce qui
 * règle par les faits la question que le recadrage laissait ouverte sur ce mot.
 *
 * LA PASTILLE JAUNE EST RETIRÉE, et avec elle la dépendance à
 * `SOURCE_BADGE_VERIFIED` : ce libellé est partagé par toutes les fiches et vient
 * de #328. Le Hero ne parlant plus d'un fait particulier mais du procédé, il
 * cesse d'en dépendre.
 *
 * → `docs/decisions/accueil-deux-portes-et-le-concept-en-mots-cles.md` */
const PIPELINE_STEPS = [
  {
    key: 'sources',
    label: 'Sources officielles',
    mots: 'Assemblée nationale · Sénat · Parlement européen\u202f…',
    vers: '/sources',
    destination: 'Détails des sources',
  },
  {
    key: 'collecte',
    label: 'Collecte et agrégation',
    mots: 'Automatisé · Traçable · Reproductible · Open source',
    /* « Les principes » est une FAMILLE de sections dans `MethodologyPage.jsx`,
       pas une section : seules les sections portent un `id`. La première de la
       famille est `comment-ca-marche`. Une ancre inexistante déposerait le
       lecteur en haut de la page sans que rien ne le lui dise. */
    vers: '/methodologie#comment-ca-marche',
    destination: 'Détails de la méthodologie',
  },
  {
    key: 'empreinte',
    label: 'L’empreinte',
    mots: 'Mandats · Votes · Amendements · Prises de parole',
    vers: null,
    destination: null,
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
      <h1>Explorez l’action politique à partir des données officielles.</h1>
      {/* LA BASELINE (#1026) remplace la sous-ligne « Des faits sourcés, sans
          note ni classement — à consulter par candidat, par groupe ou par
          gouvernement » : elle disait deux des trois traits, et la liste des
          candidats juste dessous dit déjà par où entrer. */}
      <Baseline className="baseline--bandeau" />

      <div className="hero-pipeline">
        <p className="hero-pipeline-caption">Le concept</p>
        <div className="hero-pipeline-steps">
          {PIPELINE_STEPS.map((step, index) => {
            const contenu = (
              <>
                <span className="hero-pipeline-marker" aria-hidden="true" />
                <span className="hero-pipeline-label">{step.label}</span>
                <span className="hero-pipeline-mots">{step.mots}</span>
                {/* LA DESTINATION S'ANNONCE, au survol ET au clavier. Un `title`
                    natif serait lent, illisible au clavier et muet pour un
                    lecteur d'écran. Posée en absolu : dans le flux, elle
                    pousserait le contenu et ferait sauter la rangée. */}
                {step.destination && (
                  <span className="hero-pipeline-dest" aria-hidden="true">{step.destination} →</span>
                )}
              </>
            );
            return (
              <Fragment key={step.key}>
                {step.vers ? (
                  <Link className="hero-pipeline-step hero-pipeline-step--lien" to={step.vers}>
                    {contenu}
                  </Link>
                ) : (
                  <div className="hero-pipeline-step">{contenu}</div>
                )}
                {index < PIPELINE_STEPS.length - 1 && <ArrowIcon />}
              </Fragment>
            );
          })}
        </div>
      </div>

    </section>
  );
}
