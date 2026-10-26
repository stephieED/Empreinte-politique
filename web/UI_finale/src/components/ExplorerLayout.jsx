import { Outlet, useLocation, useSearchParams } from 'react-router-dom';
import { useEffect, useRef, useState } from 'react';
import EnTeteSite from './EnTeteSite';
import SommaireSections from './SommaireSections';
import { BarreFiltre } from './Recherche';
import '../styles/shell.css';
import PiedDeSite from './PiedDeSite';
import './ExplorerLayout.css';

/* ── Le cadre de la page (#324, refait par #951, #1025, puis #1329) ──────────
 *
 * UN SEUL ENDROIT POUR CHOISIR SA FICHE, ET C'EST LE FIL D'ARIANE (#1329).
 * #1025 avait réuni les listes dans un tiroir du bandeau ; arbitré sur maquette
 * le 26/10/2026, le fil d'Ariane de chaque fiche le remplace (`FilDAriane.jsx`).
 * La règle de #1025 tient — un seul endroit —, c'est l'endroit qui change : il
 * est sur la fiche, à côté de ce qu'on lit, et non derrière un bouton.
 *
 * L'ONGLET « EXPLORATEUR » NE REVIENT PAS SUR UNE FICHE. Il y était la page
 * courante et son clic menait à la fiche par défaut, ce que #1025 avait relevé.
 * La recherche prend sa place ; sur une page qui ne filtre pas (`/candidats`,
 * la page de choix), il n'y a rien.
 *
 * LA RECHERCHE RESTE SEULE DANS LE BANDEAU, et seulement là où elle filtre.
 * Le mot vit dans l'adresse (`?mot=carburant`) et c'est la page qui le lit :
 * déplacer le champ ne touche pas à la mécanique du filtre (#979). Le champ ne
 * tient pas à côté des liens sous 1 024 px de large : il y devient une loupe,
 * qui ouvre le même champ sous le bandeau — un seul élément dans la barre,
 * comme l'outil de #1025 au téléphone.
 *
 * LA PÉRIODE (#1074) a quitté le bandeau avec le tiroir : ses deux cases sont au
 * bout du fil d'Ariane, sur les fiches qui portent des dates.
 *
 * PLUS RIEN NE LIT LE DÉFILEMENT (#951, #1025) : ni écouteur, ni repère, ni
 * `IntersectionObserver`.
 */

/** Les fiches qui lisent `?mot=` — les trois de #979, et la législature depuis #1329. */
const FICHES_FILTRABLES = ['/candidats', '/groupes', '/gouvernements', '/legislatures'];

export default function ExplorerLayout() {
  const [loupeOuverte, setLoupeOuverte] = useState(false);
  const loupe = useRef(null);
  const { pathname } = useLocation();

  /* LE MOT VIT DANS L'ADRESSE (#979) : `?mot=finances` se recharge, se partage
   * et revient avec le bouton précédent. `replace` : chaque lettre tapée n'est
   * pas une page de l'historique. */
  const [params, setParams] = useSearchParams();
  const mot = params.get('mot') ?? '';
  const changerMot = (valeur) => {
    setParams((p) => {
      const suivant = new URLSearchParams(p);
      if (valeur) suivant.set('mot', valeur);
      else suivant.delete('mot');
      return suivant;
    }, { replace: true });
  };
  // Une FICHE filtre ; `/candidats` seul, la page de choix, n'a rien à filtrer.
  const filtrable = FICHES_FILTRABLES.some((racine) => pathname.startsWith(`${racine}/`));

  // Changer de fiche referme la loupe ; taper un mot la laisse ouverte.
  useEffect(() => {
    setLoupeOuverte(false);
  }, [pathname]);

  useEffect(() => {
    if (!loupeOuverte) return undefined;
    const surTouche = (e) => {
      if (e.key !== 'Escape') return;
      setLoupeOuverte(false);
      // Le focus revient à la loupe, comme à l'« i » d'une bulle.
      loupe.current?.focus();
    };
    document.addEventListener('keydown', surTouche);
    return () => document.removeEventListener('keydown', surTouche);
  }, [loupeOuverte]);

  /* Rendu UNE SEULE FOIS, à la place de l'onglet « Explorateur ». Le champ au
     large, la loupe à l'étroit : deux mises en page d'un même élément. */
  const outil = filtrable ? (
    <span className="explorer-recherche">
      <span className="explorer-recherche-champ">
        <BarreFiltre onSaisie={changerMot} saisie={mot} />
      </span>
      <button
        aria-controls="explorer-loupe"
        aria-expanded={loupeOuverte}
        aria-label={loupeOuverte ? 'Fermer la recherche' : 'Chercher sur cette fiche'}
        className={`explorer-loupe${mot ? ' explorer-loupe--active' : ''}`}
        onClick={() => setLoupeOuverte((v) => !v)}
        ref={loupe}
        type="button"
      >
        {loupeOuverte ? <span aria-hidden="true">×</span> : (
          <svg aria-hidden="true" height="17" viewBox="0 0 16 16" width="17">
            <circle cx="7" cy="7" fill="none" r="5" stroke="currentColor" strokeWidth="1.7" />
            <path d="M11 11l3.5 3.5" stroke="currentColor" strokeLinecap="round" strokeWidth="1.7" />
          </svg>
        )}
      </button>
    </span>
  ) : null;

  return (
    <div className="app-shell">
      <div className="explorer-main">
        <EnTeteSite navProps={{ outilExplorateur: outil }}>
          {filtrable && (
            <div className="explorer-loupe-panneau" hidden={!loupeOuverte} id="explorer-loupe">
              {loupeOuverte && <BarreFiltre id="cp-filtre-mot-loupe" onSaisie={changerMot} saisie={mot} />}
            </div>
          )}
        </EnTeteSite>

        <div className="explorer-corps">
          <SommaireSections />
          <div className="explorer-profile-zone">
            <Outlet />
          </div>
        </div>

        <PiedDeSite />
      </div>
    </div>
  );
}
