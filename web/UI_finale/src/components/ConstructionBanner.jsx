import { useState } from 'react';
import { Link } from 'react-router-dom';
import './ConstructionBanner.css';

/**
 * Bandeau « en construction », sur TOUTES les pages.
 *
 * Le site est public et le pipeline évolue quotidiennement : des données
 * manquent, et certaines absences portent encore une explication imprécise
 * (#556, #558, #560). Un lecteur qui arrive par un lien direct sur une page de
 * profil doit le savoir avant de conclure d'une liste vide.
 *
 * Volontairement NON refermable : un bandeau qu'on ferme disparaît pour toute
 * la visite, y compris sur les pages de profil — là où il compte le plus.
 *
 * Couleur : encre sur gris (--notice). Le bandeau était cyan, hors palette ;
 * la propriétaire l'a ramené à un gris le 02/10/2026. Le jaune signal reste
 * exclu — la charte le réserve à la sélection, l'action et la source vérifiée,
 * « jamais pour indiquer un jugement » (DESIGN_SYSTEM.md §1 et §2).
 *
 * AU TÉLÉPHONE, UNE LIGNE (#1372, base A′ du 28/10/2026) : le bandeau prenait
 * 145 px, un sixième du premier écran, sur chaque page. Sous 720 px il tient
 * sur une ligne, coupée par « … » ; « En construction. » est un bouton qui le
 * déplie. Il n'est toujours pas refermable : replié, il reste là, et son texte
 * est inchangé.
 */
export default function ConstructionBanner() {
  const [deplie, setDeplie] = useState(false);
  return (
    <aside
      aria-label="État du projet"
      className={`construction-banner${deplie ? ' construction-banner--deplie' : ''}`}
      role="note"
    >
      <p className="construction-banner__text">
        <button
          aria-expanded={deplie}
          className="construction-banner__deplier"
          onClick={() => setDeplie((v) => !v)}
          type="button"
        >
          <strong>En construction.</strong>
        </button>{' '}
        Des données peuvent manquer, et certaines absences sont encore mal expliquées.
      </p>
      <Link className="construction-banner__link" to="/methodologie">
        Méthodologie
      </Link>
    </aside>
  );
}
