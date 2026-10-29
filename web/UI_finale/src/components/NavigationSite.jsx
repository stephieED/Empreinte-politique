import { useEffect, useRef, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import BandeauArticles from './BandeauArticles';
import './NavigationSite.css';

/* ── La barre des pages du site (#951) ────────────────────────────────────────
 *
 * Six liens, dans le style discret retenu le 16/09/2026 : gris, la page
 * courante en encre soulignée de jaune. Le jaune est un TRAIT sous le mot,
 * jamais la couleur du texte — 1,05:1 sur le fond clair (DESIGN_SYSTEM §2).
 *
 * « NOUS SOUTENIR » A REJOINT LA BARRE LE 19/10/2026 (#1033), au même style
 * que les autres : dans le seul pied de page, la propriétaire l'a jugé trop
 * caché. Pas de bouton jaune — le jaune y marque la page courante.
 *
 * Sous 720 px les six liens ne tiennent plus à côté du logo et de la loupe :
 * ils passent dans un menu.
 *
 * « ARTICLES » OUVRE UN BANDEAU SOUS CELUI DU SITE (#1329, arbitré sur
 * maquette le 26/10/2026) : les articles en cartes, et « Tous les articles → »
 * vers l'index, une page statique servie telle quelle par GitHub Pages (#1029)
 * — d'où un `<a href>` et jamais un `<Link>`, qui ferait démarrer le routeur
 * sur une adresse qu'il ne connaît pas. Le bouton n'est jamais « courant ».
 *
 * « EXPLORATEUR » A QUITTÉ LE MENU, PARTOUT (29/10/2026, #1372). Il menait à
 * `/candidats`, le complément lié à 2027, et non au cœur du site ; son nom ne
 * disait pas où il menait. Il avait déjà quitté l'accueil (30/09) et cédé sa
 * place sur les fiches (#1025, #1329). On va aux fiches par l'accueil — le
 * logo y ramène, ses portes y mènent — et on en change par le fil d'Ariane.
 *
 * SUR UNE FICHE, LA RECHERCHE OUVRE LA BARRE, là où était l'onglet : la fiche
 * la pose quand elle filtre, et rien sinon. Elle n'entre pas dans le menu
 * replié : elle est à côté de « Menu », pas dedans.
 */
const PAGES = [
  // « Articles » juste après la recherche (demandé le 26/10/2026, #1329).
  { libelle: 'Articles', vers: '/rapports', racines: [], bandeau: true },
  { libelle: 'Méthodologie', vers: '/methodologie', racines: ['/methodologie'] },
  { libelle: 'Sources', vers: '/sources', racines: ['/sources'] },
  { libelle: 'FAQ', vers: '/faq', racines: ['/faq'] },
  { libelle: 'Nous soutenir', vers: '/nous-soutenir', racines: ['/nous-soutenir'] },
];

const estCourante = (page, pathname) =>
  page.racines.some((r) => pathname === r || pathname.startsWith(`${r}/`));

export default function NavigationSite({ outilExplorateur = null }) {
  const { pathname } = useLocation();
  const [menuOuvert, setMenuOuvert] = useState(false);
  const [articlesOuverts, setArticlesOuverts] = useState(false);
  const menuRef = useRef(null);
  // Le bouton qui a ouvert le bandeau : Échap lui rend le focus (#1329).
  const ouvreurArticles = useRef(null);

  useEffect(() => {
    setMenuOuvert(false);
    setArticlesOuverts(false);
  }, [pathname]);

  /* Le bandeau se referme à Échap et au clic hors de lui — hors du bouton
     aussi, qui le referme lui-même. */
  useEffect(() => {
    if (!articlesOuverts) return undefined;
    const surClic = (e) => {
      if (!e.target.closest?.('.bandeau-articles, .nav-site-articles')) setArticlesOuverts(false);
    };
    const surTouche = (e) => {
      if (e.key !== 'Escape') return;
      setArticlesOuverts(false);
      ouvreurArticles.current?.focus();
    };
    document.addEventListener('mousedown', surClic);
    document.addEventListener('keydown', surTouche);
    return () => {
      document.removeEventListener('mousedown', surClic);
      document.removeEventListener('keydown', surTouche);
    };
  }, [articlesOuverts]);

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
      if (page.bandeau) {
        return (
          <button
            aria-controls="bandeau-articles"
            aria-expanded={articlesOuverts}
            className={`${className} nav-site-articles`}
            key={page.libelle}
            onClick={(e) => {
              /* Depuis le menu replié, le bouton disparaît avec le menu : le
                 focus reviendra au bouton « Menu ». */
              ouvreurArticles.current = className === 'nav-site-lien'
                ? e.currentTarget
                : menuRef.current?.querySelector('.nav-site-menu-bouton');
              setMenuOuvert(false);
              setArticlesOuverts((v) => !v);
            }}
            type="button"
          >
            {page.libelle}
            <svg aria-hidden="true" className="nav-site-articles-chevron" height="7" viewBox="0 0 10 7" width="10">
              <path d="M1 1.5L5 5.5L9 1.5" fill="none" stroke="currentColor" strokeLinecap="round" strokeWidth="1.8" />
            </svg>
          </button>
        );
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
        {outilExplorateur && <span className="nav-site-outil">{outilExplorateur}</span>}
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
      <BandeauArticles id="bandeau-articles" ouvert={articlesOuverts} />
    </>
  );
}
