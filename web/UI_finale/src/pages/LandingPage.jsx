import EnTeteSite from '../components/EnTeteSite';
import PiedDeSite from '../components/PiedDeSite';
import Hero from '../components/landing/Hero';
import CommencerAExplorer from '../components/landing/CommencerAExplorer';
import '../styles/shell.css';
import '../components/landing/landing.css';

// L'ACCUEIL, REFONDU LE 30/09/2026 : le Hero sans ses boutons, puis l'entrée en
// deux temps — deux portes permanentes (groupes, gouvernements) et les candidats
// dans un encart borné par l'élection. La forme C de #951 ouvrait sur la grille
// des 31 candidats ; le recadrage éditorial du 30/09 en fait un volet ponctuel.
// → `docs/decisions/accueil-deux-portes-et-le-concept-en-mots-cles.md`
//
// Ce qui suit décrit la forme C, conservé parce qu'il dit où sont parties les
// autres sections : Les autres blocs ont leur page :
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
          <CommencerAExplorer />
        </main>
        <PiedDeSite />
      </div>
    </div>
  );
}
