import { useEffect, useRef, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import './NavigationSite.css';

/* ── La barre des pages du site (#951) ────────────────────────────────────────
 *
 * Quatre liens, dans le style discret retenu le 16/09/2026 : gris, la page
 * courante en encre soulignée de jaune. Le jaune est un TRAIT sous le mot,
 * jamais la couleur du texte — 1,05:1 sur le fond clair (DESIGN_SYSTEM §2).
 *
 * Sous 720 px les quatre liens ne tiennent plus à côté du logo et du tiroir :
 * ils passent dans un menu.
 *
 * L'ONGLET DE LA PAGE COURANTE PEUT CÉDER SA PLACE À UN OUTIL (#1025).
 * L'explorateur y pose son tiroir : sur une fiche, « Explorateur » était déjà
 * la page courante, et son clic renvoyait à la fiche par défaut. Le lien reste
 * partout ailleurs, où il sert. C'est un remplacement, jamais un ajout : la
 * barre porte quatre entrées, pas cinq.
 */
const PAGES = [
  { libelle: 'Explorateur', vers: '/candidats', racines: ['/candidats', '/groupes', '/gouvernements'] },
  { libelle: 'Méthodologie', vers: '/methodologie', racines: ['/methodologie'] },
  { libelle: 'Sources', vers: '/sources', racines: ['/sources'] },
  { libelle: 'FAQ', vers: '/faq', racines: ['/faq'] },
];

const estCourante = (page, pathname) =>
  page.racines.some((r) => pathname === r || pathname.startsWith(`${r}/`));

export default function NavigationSite({ outilExplorateur = null }) {
  const { pathname } = useLocation();
  const [menuOuvert, setMenuOuvert] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    setMenuOuvert(false);
  }, [pathname]);

  useEffect(() => {
    if (!menuOuvert) return undefined;
    const surClic = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setMenuOuvert(false);
    };
    const surTouche = (e) => {
      if (e.key === 'Escape') setMenuOuvert(false);
    };
    document.addEventListener('mousedown', surClic);
    document.addEventListener('keydown', surTouche);
    return () => {
      document.removeEventListener('mousedown', surClic);
      document.removeEventListener('keydown', surTouche);
    };
  }, [menuOuvert]);

  const liens = (className) =>
    PAGES.map((page) => {
      const courante = estCourante(page, pathname);
      // L'outil prend la place du lien dans la barre ; dans le menu replié, il
      // n'y a rien à mettre — le bouton est à côté de « Menu », pas dedans.
      if (outilExplorateur && page.libelle === 'Explorateur' && courante) {
        return className === 'nav-site-lien'
          ? <span key={page.libelle} className="nav-site-outil">{outilExplorateur}</span>
          : null;
      }
      return (
        <Link
          key={page.libelle}
          to={page.vers}
          className={`${className}${courante ? ` ${className}--courante` : ''}`}
          aria-current={courante ? 'page' : undefined}
        >
          {page.libelle}
        </Link>
      );
    });

  return (
    <>
      <nav className="nav-site" aria-label="Pages du site">
        {liens('nav-site-lien')}
      </nav>
      <div className="nav-site-menu" ref={menuRef}>
        <button
          type="button"
          className="nav-site-menu-bouton"
          aria-expanded={menuOuvert}
          aria-controls="nav-site-menu-liste"
          onClick={() => setMenuOuvert((v) => !v)}
        >
          <span className="nav-site-menu-icone" aria-hidden="true" />
          Menu
        </button>
        <nav
          id="nav-site-menu-liste"
          className="nav-site-menu-liste"
          aria-label="Pages du site"
          hidden={!menuOuvert}
        >
          {liens('nav-site-menu-lien')}
        </nav>
      </div>
    </>
  );
}
