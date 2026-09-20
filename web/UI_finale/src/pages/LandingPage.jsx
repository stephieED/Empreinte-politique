import EnTeteSite from '../components/EnTeteSite';
import PiedDeSite from '../components/PiedDeSite';
import Hero from '../components/landing/Hero';
import CandidatsDeclares from '../components/landing/CandidatsDeclares';
import '../styles/shell.css';
import '../components/landing/landing.css';

// L'ACCUEIL, FORME C (#951, arbitrée le 16/09/2026) : le Hero sans ses boutons,
// puis les candidats déclarés en accès direct. Les autres blocs ont leur page :
// « Comment ça marche » et « Ce que vous ne trouverez pas ici » ouvrent
// /methodologie, les questions fréquentes sont sur /faq, les sources et ce que le
// dépôt porte sur /sources. La barre des pages du site les relie.
//
// Écartées sur maquette : le Hero seul, avec ses trois boutons ; le Hero et
// quatre cartes, une par page de la barre, qui la dupliquaient.
export default function LandingPage() {
  return (
    <div className="app-shell">
      <div className="landing-page">
        <EnTeteSite />
        <main className="landing-main">
          <Hero />
          <CandidatsDeclares />
        </main>
        <PiedDeSite />
      </div>
    </div>
  );
}
