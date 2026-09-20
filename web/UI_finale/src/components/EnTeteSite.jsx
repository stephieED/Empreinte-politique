import Brand from './Brand';
import NavigationSite from './NavigationSite';
import './EnTeteSite.css';

/* ── La rangée du logo, collée en haut (#951) ─────────────────────────────────
 *
 * Le logo à gauche, les pages du site à droite. Une seule rangée pour
 * l'explorateur et l'accueil, pour qu'elle ne diverge pas d'une page à l'autre.
 *
 * SA HAUTEUR NE CHANGE JAMAIS AU DÉFILEMENT : c'est ce qui rend le défilement
 * stable (voir ExplorerLayout.jsx). Elle se lit dans `--entete-hauteur`, que les
 * enfants — le panneau des listes — reprennent pour se poser dessous.
 *
 * `children` s'ajoute après les liens : l'explorateur y met son tiroir.
 * `navProps` passe à la barre des pages : l'explorateur y pose l'outil qui
 * remplace l'onglet courant (#1025).
 */
export default function EnTeteSite({ children, ref, navProps = null }) {
  return (
    <header className="entete-site" ref={ref}>
      <Brand />
      <div className="entete-site-actions">
        <NavigationSite {...(navProps || {})} />
        {children}
      </div>
    </header>
  );
}
