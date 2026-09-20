import { Link } from 'react-router-dom';
import './Brand.css';

// Lockup complet "Empreinte politique" : sa légende ("politique") est vectorisée
// et devient illisible en dessous d'environ 50px de hauteur affichée. On le rend
// à 58px, plancher posé par `DESIGN_SYSTEM.md` §1. Symbole seul en dessous du
// breakpoint (en-tête étroit / mobile). Élément unique cliquable → accueil ;
// les images sont décoratives (alt=""), le lien porte le nom accessible.
//
// LA `viewBox` EST RESSERRÉE SUR LE DESSIN, et ce n'est pas cosmétique
// (15/09/2026). Le brand pack livre ses SVG sur une toile fixe — 1200 x 600
// pour le lockup — le dessin occupant 906 x 215 au centre. Rendue telle quelle
// à 58px de HAUTEUR DE TOILE, la légende ne fait plus que 21px : le plancher
// de 50px est franchi sans que rien ne le signale. La `viewBox` est donc posée
// sur la boîte réelle du dessin, plus 2 % de respiration — ratio 3,75, contre
// 3,77 pour le lockup précédent, donc la mise en page de l'en-tête ne bouge pas.
// Le dessin, lui, n'est pas touché.
export default function Brand() {
  return (
    <Link to="/" className="brand" aria-label="Empreinte politique — retour à l'accueil">
      <img
        src="/brand/empreinte-lockup-light.svg"
        alt=""
        className="brand-lockup"
      />
      <img src="/brand/empreinte-symbol-light.svg" alt="" className="brand-symbol" />
    </Link>
  );
}
