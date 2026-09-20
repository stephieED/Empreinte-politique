import { Link } from 'react-router-dom';
import EnTeteSite from '../components/EnTeteSite';
import PiedDeSite, { CONTACT, LINKEDIN, X_COMPTE } from '../components/PiedDeSite';
import Baseline from '../components/Baseline';
import '../styles/shell.css';
import '../components/StaticPage.css';
import './AboutPage.css';

/* ── LA PAGE /a-propos (#1032) ────────────────────────────────────────────────
 *
 * DEUX PAGES, DEUX QUESTIONS — arbitré le 18/09/2026. Celle-ci dit ce que le
 * site est et qui l'édite ; `/methodologie` dit comment chaque fiche est faite,
 * liste par liste. Le manifeste vivait dans l'introduction de `/methodologie`,
 * qui porte désormais un renvoi : **le texte n'existe qu'à un seul endroit**.
 * C'est le défaut mesuré sur #1026 — la `meta description` et cette
 * introduction ne disaient déjà pas la même chose. `/methodologie` garde ses
 * quinze sections et les dix ancres profondes que les fiches appellent.
 *
 * LE MANIFESTE EST DANS LE BANDEAU D'ENCRE, retenu sur maquette entre trois
 * formes : la coque standard des pages statiques le réduisait au chapeau de
 * `/methodologie`, un grand texte sans bannière ne disait plus où l'on est. Le
 * bandeau lui donne le poids d'une déclaration et lie la page à l'accueil, dont
 * il reprend les cotes et la baseline (#1026) — puces en accent, le seul fond
 * où le jaune signal passe le contraste (16,01:1, DESIGN_SYSTEM §2).
 *
 * LE TEXTE EST CELUI DE LA PROPRIÉTAIRE, du 18/09/2026, découpé en paragraphes
 * pour la lecture et sans un mot changé. Il ne promet rien de plus que
 * `/methodologie` : « relus par une personne » couvre les rapprochements que la
 * fiche signale (#977).
 *
 * CE QUE LA PAGE NE PORTE PAS, ET POURQUOI. Un texte long a été proposé le
 * 18/09/2026, avec trois listes — ce que le site refuse de publier, les données
 * et fonctionnalités, les sources intégrées. Elles redisaient `/methodologie`
 * (« Ce que vous ne trouverez pas ici ») et `/sources`, deux pages tenues à
 * jour et testées : c'est la duplication que la structure A venait de
 * supprimer. Cette page garde donc ce qui n'existe nulle part ailleurs — la
 * mission, l'indépendance, le but non lucratif, le code public — et renvoie
 * pour le reste. Trois affirmations de ce texte étaient par ailleurs fausses et
 * ne sont pas publiées : « sans intervention humaine » (le rattachement d'un
 * mandat est une relecture humaine datée, #977), « Sénat : scrutins » (son
 * open data n'en porte aucun, #885) et le Journal officiel présenté comme
 * collecté (il est cité, #860).
 *
 * LA PRÉSENTATION EST LA SIENNE, ET ELLE SIGNE « STÉPHIE E. ». Le patronyme
 * n'est pas publié : c'est ce qui permet aux mentions légales de garder leur
 * formulation — « édité à titre non professionnel et non commercial par une
 * personne physique », l'identité tenue à la disposition de l'hébergeur au titre
 * de l'article 6-III de la LCEN. Le compléter ici mettrait les deux pages en
 * contradiction, et un test le refuse.
 */

/* LE LIEN VERS LE DÉPÔT EST AUSSI L'OFFRE DE SOURCE que l'AGPL-3.0 attend d'un
 * service en réseau (sa section 13) : le lecteur qui utilise le site doit
 * pouvoir atteindre le code de la version qu'il utilise. « Open source » est
 * exact depuis que le dépôt porte son fichier `LICENSE` — avant, le dépôt était
 * seulement public, c'est-à-dire visible et tous droits réservés. */
const DEPOT = 'https://github.com/stephieED/Empreinte-politique-src';

const MANIFESTE = [
  'Empreinte politique rassemble ce que les institutions publient sur les candidats à la présidentielle 2027 — mandats, votes, textes, prises de parole — et le donne à lire tel quel.',
  "Tout est collecté et mis en forme par un programme, à chaque mise à jour : aucun fait n'est écrit ni corrigé à la main. Ce que vous lisez est ce que la source publie, avec le lien pour le vérifier.",
  'Seuls quelques rapprochements sont relus par une personne, et la fiche le dit.',
  "Rien n'est noté, classé ni commenté.",
];

export default function AboutPage() {
  return (
    <div className="app-shell">
      <div className="static-page">
        <EnTeteSite />
        <main className="static-main apropos-main">
          <section className="apropos-bandeau" aria-labelledby="apropos-titre">
            <p className="apropos-eyebrow">À propos</p>
            <h1 id="apropos-titre">Ce que ce site fait, et qui l’édite.</h1>
            {MANIFESTE.map((phrase) => (
              <p key={phrase}>{phrase}</p>
            ))}
            <Baseline className="baseline--bandeau apropos-baseline" />
          </section>

          <div className="static-sections">
            <section className="static-card" id="qui">
              <h2>Qui édite ce site</h2>
              {/* « Qui édite ce site », et non « Qui sommes-nous » : un « nous »
                  pour une personne seule est la première chose qu'un lecteur
                  relève.

                  LA PREMIÈRE PHRASE EST CELLE DE LA PROPRIÉTAIRE, du 18/09/2026,
                  mot pour mot. Elle signe « Stéphie E. » : le nom complet n'est
                  pas publié, et les mentions légales peuvent donc garder leur
                  formulation — « une personne physique », l'identité tenue à la
                  disposition de l'hébergeur (LCEN, article 6-III). Ne pas y
                  ajouter le patronyme sans le lui demander.

                  « indépendant » n'est pas répété dans la phrase suivante : elle
                  dit de quoi le projet est indépendant, et c'est le fait. */}
              <p>
                Empreinte politique est un projet indépendant conçu et développé par Stéphie E.,
                ingénieure/analyste de données, passionnée par l’Open Data et la transparence
                démocratique.
              </p>
              <p>
                Projet à but non lucratif : aucune affiliation à un parti, à un candidat ou à une
                organisation ; aucun financement extérieur, aucune publicité. Les coûts sont portés
                sur fonds propres, et{' '}
                <a href={DEPOT} target="_blank" rel="noopener noreferrer">
                  le code est publié en open source, sous licence AGPL-3.0
                </a>
                .
              </p>
              <p>
                C’est un projet personnel, mené sur mon temps libre. Ni une rédaction, ni une
                entreprise : une personne, un programme, et des sources publiques.
              </p>
              {/* LA SEULE PHRASE DE LA PAGE QUI NE SOIT PAS UN FAIT SUR LE SITE :
                  elle dit pourquoi il existe, et c'est la voix de la propriétaire
                  (§2 — les règles tiennent l'outil, pas sa plume). */}
              <p>
                Il s’inscrit dans une logique de lutte contre la polarisation des débats et la
                désinformation : donner à lire les faits, avec de quoi les vérifier.
              </p>
              <p className="apropos-liens">
                <a href={`mailto:${CONTACT}`}>{CONTACT}</a>
                <span aria-hidden="true"> · </span>
                <a href={LINKEDIN} target="_blank" rel="noopener noreferrer">
                  LinkedIn
                </a>
                <span aria-hidden="true"> · </span>
                <a href={X_COMPTE} target="_blank" rel="noopener noreferrer">
                  X
                </a>
              </p>
            </section>

            <section className="static-card" id="comment">
              <h2>Comment les fiches sont faites</h2>
              <p>
                Le détail, liste par liste et figure par figure, est sur la page{' '}
                <Link to="/methodologie">méthodologie</Link> : ce que chaque chiffre mesure, ce
                qu’il ne mesure pas, et ce que le site refuse de publier. Les sources, elles, sont
                nommées une par une sur <Link to="/sources">la page des sources</Link>.
              </p>
            </section>
          </div>
        </main>
        <PiedDeSite />
      </div>
    </div>
  );
}
