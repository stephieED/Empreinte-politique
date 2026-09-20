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
 * Couleur : cyan signal (--notice) sur encre. La charte ne définit aucune
 * couleur d'alerte, et c'est ce qui rend ce choix sûr : le cyan n'appartient à
 * aucun autre élément de l'interface, donc le bandeau ne peut pas se lire
 * comme du contenu. Le jaune signal est exclu — la charte le réserve à la
 * sélection, l'action et la source vérifiée, « jamais pour indiquer un
 * jugement » (DESIGN_SYSTEM.md §1 et §2).
 */
export default function ConstructionBanner() {
  return (
    <aside className="construction-banner" role="note" aria-label="État du projet">
      <p className="construction-banner__text">
        <strong>En construction.</strong>{' '}
        Ce site est publié pendant son développement. Ce qui s'affiche est sourcé
        et vérifiable, mais des données peuvent manquer, et certaines absences
        sont encore mal expliquées.
      </p>
      <Link className="construction-banner__link" to="/methodologie">
        Méthodologie
      </Link>
    </aside>
  );
}
