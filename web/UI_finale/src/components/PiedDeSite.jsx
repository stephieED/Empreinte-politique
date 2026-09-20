import { Link } from 'react-router-dom';
import Baseline from './Baseline';
import './PiedDeSite.css';

/* LE PIED DU SITE — UN SEUL, RENDU PAR LES TROIS CARCASSES (#328).
 *
 * Il y en avait trois, et l'un des trois n'existait pas : `landing-footer`
 * portait les pages sans le contact, `explorer-footer` portait les deux, et les
 * pages statiques — méthodologie, mentions légales, couverture — n'avaient
 * aucun pied. Trois pieds pour un même site sont trois pieds qui divergent, et
 * une adresse de contact absente d'une page sur deux est une adresse qu'on
 * n'écrit pas.
 *
 * L'ADRESSE S'ÉCRIT EN ENTIER. C'est ce qui distingue ce rendu des trois autres
 * essayés : elle se copie, elle se retient, et elle ne demande ni survol ni
 * clic pour être lue. Le coût est mesuré et assumé — le pied passe de 66 à
 * 118 px, sur toutes les pages.
 *
 * LES DEUX COMPTES SONT DES ICÔNES, LES PAGES SONT DES MOTS. La forme dit la
 * nature du lien : un mot mène à une page du site, une icône ouvre autre chose.
 * Chaque icône garde son `aria-label` en toutes lettres et une cible de 30 px —
 * elle remplace le libellé À L'ÉCRAN, jamais pour un lecteur d'écran ni pour le
 * doigt.
 *
 * `rel="noopener"` partout où `target="_blank"` apparaît : un lien sortant
 * ouvert dans un onglet neuf ne doit pas garder la main sur celui-ci.
 *
 * IL PORTE LA BASELINE (#1026), sous la marque, et elle remplace les deux
 * lignes qui disaient la même chose à moitié — « Données publiques agrégées.
 * Aucun score, aucun classement. » La promesse est écrite une seule fois, dans
 * `Baseline.jsx`, et l'accueil lit la même.
 *
 * CE QUE LE PIED NE PORTE PAS : « aucun taux de présence individuel ». La règle
 * §2 n° 3 reste publiée — méthodologie, « Ce que vous ne trouverez pas ici » et
 * FAQ de l'accueil —, mais elle était répétée jusqu'à trois fois sur une même
 * fiche, deux d'entre elles à quelques pixels l'une de l'autre.
 */

export const CONTACT = 'contact@empreinte-politique.fr';
export const LINKEDIN = 'https://www.linkedin.com/company/empreinte-politique';
export const X_COMPTE = 'https://x.com/EmpreintePol';

function IconeLinkedIn() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false">
      <path d="M4.98 3.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5ZM3 9.5h4v11H3v-11Zm6.5 0h3.8v1.5h.05c.53-.95 1.83-1.95 3.77-1.95 4.03 0 4.78 2.5 4.78 5.76v5.69h-4v-5.05c0-1.2-.02-2.75-1.7-2.75-1.7 0-1.96 1.31-1.96 2.66v5.14h-4v-11Z" />
    </svg>
  );
}

function IconeX() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false">
      <path d="M17.6 3h3.1l-6.77 7.74L22 21h-6.2l-4.86-6.35L5.37 21H2.26l7.24-8.28L2 3h6.36l4.4 5.82L17.6 3Zm-1.09 16.1h1.72L7.57 4.8H5.72l10.79 14.3Z" />
    </svg>
  );
}

export default function PiedDeSite() {
  return (
    <footer className="pds">
      <div className="pds-marque">
        <b>Empreinte politique</b>
        <Baseline className="baseline--pied" />
      </div>

      <nav className="pds-colonne" aria-label="Pages du site">
        <span className="pds-titre">Le site</span>
        <Link to="/a-propos">À propos</Link>
        <Link to="/sources">Sources</Link>
        <Link to="/methodologie">Méthodologie</Link>
        <Link to="/mentions-legales">Mentions légales</Link>
      </nav>

      <div className="pds-colonne">
        <span className="pds-titre">Nous joindre</span>
        <a href={`mailto:${CONTACT}`}>{CONTACT}</a>
        <div className="pds-comptes">
          <a
            className="pds-icone"
            href={LINKEDIN}
            target="_blank"
            rel="noopener noreferrer"
            aria-label="Empreinte politique sur LinkedIn"
          >
            <IconeLinkedIn />
          </a>
          <a
            className="pds-icone"
            href={X_COMPTE}
            target="_blank"
            rel="noopener noreferrer"
            aria-label="Empreinte politique sur X"
          >
            <IconeX />
          </a>
        </div>
      </div>
    </footer>
  );
}
