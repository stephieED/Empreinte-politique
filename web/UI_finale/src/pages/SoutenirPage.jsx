import EnTeteSite from '../components/EnTeteSite';
import PiedDeSite, { CONTACT } from '../components/PiedDeSite';
import SommaireSections from '../components/SommaireSections';
import { DEPOT } from './AboutPage';
import '../styles/shell.css';
import '../components/StaticPage.css';
import './AboutPage.css';
import './SoutenirPage.css';

/* ── LA PAGE /nous-soutenir (#1033) ───────────────────────────────────────────
 *
 * Trois façons d'aider : le don, le code, le partage. Arbitré le 19/10/2026 sur
 * maquette, entre trois formes : la FORME A, le bandeau d'encre de `/a-propos`
 * avec le don dedans — c'est le seul fond où le jaune signal peut porter un
 * bouton (16,01:1 ; 1,05:1 sur fond clair, DESIGN_SYSTEM §2). Le code et le
 * partage suivent en deux cartes.
 *
 * LE DON EST UN LIEN, JAMAIS UN WIDGET. Le bouton mène à la page Ko-fi de la
 * propriétaire, et rien de Ko-fi n'est chargé ici : ni script, ni cadre, ni
 * cookie. Le site reste le seul à s'exécuter chez le lecteur, et les mentions
 * légales n'ont pas de section « cookies et tiers » à ouvrir. La barre
 * d'objectif de Ko-fi reste sur Ko-fi pour la même raison.
 * → docs/decisions/nous-soutenir-don-par-lien-1033.md
 *
 * LES TEXTES SONT CEUX DE LA PROPRIÉTAIRE, validés le 19/10/2026. La mention de
 * transparence a perdu sa parenthèse fiscale : aucune déclaration n'avait
 * encore eu lieu, et le lecteur n'en a pas besoin pour donner.
 *
 * LE PARTAGE NE FABRIQUE AUCUN MESSAGE (§2 règle 1) : les deux liens portent
 * l'adresse du site, et rien d'autre. Ce sont les adresses de partage nues de
 * LinkedIn et de X, sans leur SDK.
 */

/* L'adresse de la page Ko-fi, donnée par la propriétaire le 19/10/2026. Son
   bouton officiel charge une image depuis les serveurs de Ko-fi : seule l'adresse
   est reprise, pour que rien de Ko-fi ne se charge ici. Une adresse provisoire
   fait échouer `tests/test_nous_soutenir_1033.py`. */
export const KOFI = 'https://ko-fi.com/T0B72934R2';

const MENTION =
  "Empreinte Politique est un projet indépendant mené sur mon temps libre. Vos contributions permettent de couvrir les coûts d'hébergement et de serveurs.";

const SITE = 'https://empreinte-politique.fr/';
const PARTAGE_LINKEDIN = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(SITE)}`;
const PARTAGE_X = `https://x.com/intent/post?url=${encodeURIComponent(SITE)}`;

export default function SoutenirPage() {
  return (
    <div className="app-shell">
      <div className="static-page">
        <EnTeteSite />
        <main className="static-main apropos-main">
          <section className="apropos-bandeau" aria-labelledby="soutenir-titre">
            <p className="apropos-eyebrow">Nous soutenir</p>
            <h1 id="soutenir-titre">Soutenir Empreinte politique.</h1>
            <p>{MENTION}</p>
            <p className="soutenir-action">
              <a className="soutenir-bouton" href={KOFI} target="_blank" rel="noopener noreferrer">
                Faire un don sur Ko-fi
                <span aria-hidden="true"> ↗</span>
              </a>
            </p>
            <p className="soutenir-sous">Paiement en ligne via Ko-fi, sans création de compte.</p>
          </section>

          <SommaireSections libelle="Sections de cette page" />

          <div className="static-sections">
            <section className="static-card" id="code" data-section="Signaler une erreur, améliorer le code">
              <h2>Signaler une erreur, améliorer le code</h2>
              <p>
                Une donnée vous semble fausse, ou une méthode discutable : écrivez à{' '}
                <a href={`mailto:${CONTACT}`}>{CONTACT}</a>.
              </p>
              <p>
                Le code du site est public. Vous pouvez y signaler un défaut ou proposer une
                correction, sur{' '}
                <a href={DEPOT} target="_blank" rel="noopener noreferrer">
                  GitHub
                </a>
                .
              </p>
            </section>

            <section className="static-card" id="partager" data-section="Faire connaître le site">
              <h2>Faire connaître le site</h2>
              <p>Le plus simple est de partager le site, ou une fiche, autour de vous.</p>
              <p className="soutenir-partage">
                <a className="soutenir-lien" href={PARTAGE_LINKEDIN} target="_blank" rel="noopener noreferrer">
                  Partager sur LinkedIn
                </a>
                <a className="soutenir-lien" href={PARTAGE_X} target="_blank" rel="noopener noreferrer">
                  Partager sur X
                </a>
              </p>
            </section>
          </div>
        </main>
        <PiedDeSite />
      </div>
    </div>
  );
}
