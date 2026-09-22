import { Outlet, useLocation, useSearchParams } from 'react-router-dom';
import { useEffect, useState } from 'react';
import EnTeteSite from './EnTeteSite';
import GroupsBar from './GroupsBar';
import GovernmentsBar from './GovernmentsBar';
import CandidatesBar from './CandidatesBar';
import SommaireSections from './SommaireSections';
import { BarreFiltre } from './Recherche';
import { PERIODES, periodeValide } from '../utils/filtrePeriode';
import { GroupFilterProvider } from '../context/GroupFilterContext';
import '../styles/shell.css';
import PiedDeSite from './PiedDeSite';
import './ExplorerLayout.css';

/* ── Le cadre de la page (#324, refait par #951, puis par #1025) ──────────────
 *
 * UN SEUL ENDROIT POUR CHOISIR SA FICHE, ET C'EST LE TIROIR. Les trois listes
 * vivaient à deux endroits : dépliées sous le bandeau à l'arrivée — 425 px, et
 * la fiche ne commençait qu'à 577 px du haut de la page — puis rappelées dans
 * un bouton du bandeau une fois ces listes passées au défilement. Une seule
 * reste, celle du bandeau, et la page commence par la fiche.
 *
 * LE TIROIR PREND LA PLACE DE L'ONGLET « EXPLORATEUR », il ne s'ajoute pas à
 * lui. Sur une fiche, cet onglet était déjà la page courante et son clic
 * renvoyait à `/candidats`, c'est-à-dire à la fiche par défaut : il déplaçait
 * le lecteur vers une fiche que personne n'avait demandée. Il reste un lien
 * partout où il sert encore — accueil, méthodologie, sources, FAQ.
 *
 * LA RECHERCHE EST DANS LE TIROIR, EN TÊTE. « Rechercher sur cette page »
 * (#979) vivait dans le corps de la fiche, sous le nom ; le mot, lui, vit dans
 * l'adresse (`?mot=carburant`) et c'est la page qui le lit. Monter le champ
 * dans le bandeau ne déplace donc qu'un champ : la mécanique du filtre n'est
 * pas touchée.
 *
 * LE CHAMP N'EXISTE QUE LÀ OÙ IL FILTRE. Les fiches candidat et de lignée
 * lisent `?mot=` ; la fiche de gouvernement ne le lit pas encore, et les pages
 * éditoriales n'ont pas de filtre du tout. Une barre qui ne filtre rien est du
 * mobilier : le tiroir se renomme alors « Changer de fiche ».
 *
 * PLUS RIEN NE LIT LE DÉFILEMENT. La mise en page ne changeait déjà plus au
 * défilement depuis #951, mais la VISIBILITÉ du bouton s'y réglait encore. Les
 * listes ayant quitté la page, le tiroir est là dès l'arrivée : ni écouteur de
 * défilement, ni repère, ni `IntersectionObserver` — dont #951 avait déjà
 * montré qu'il manquait les sauts directs (une ancre, un lien partagé).
 */

/** Les fiches qui lisent `?mot=` — les trois depuis #979. */
const FICHES_FILTRABLES = ['/candidats', '/groupes', '/gouvernements'];

/** Les fiches qui portent les dates de ce qu'elles montrent (#1074) — la fiche
 *  de groupe depuis que #1077 lui a donné ses fenêtres de parole. */
const FICHES_DATEES = ['/candidats', '/groupes', '/gouvernements'];

export default function ExplorerLayout() {
  const [tiroirOuvert, setTiroirOuvert] = useState(false);
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
  const filtrable = FICHES_FILTRABLES.some((racine) => pathname.startsWith(racine));

  /* LA PÉRIODE (#1074) : deux cases, « 6 derniers mois » et « 12 derniers mois ».
   * De vraies cases à cocher, arbitré le 22/09/2026 sur maquette — mais
   * EXCLUSIVES : cocher l'une décoche l'autre, décocher la case active revient
   * à tout montrer. Elle vit dans l'adresse (`?periode=6m`), comme le mot.
   *
   * Seulement là où elle filtre : les fiches qui portent les dates de ce
   * qu'elles montrent (`FICHES_DATEES`) — des cases qui ne filtrent rien
   * seraient du mobilier. */
  const periode = periodeValide(params.get('periode'));
  const periodeDisponible = FICHES_DATEES.some((racine) => pathname.startsWith(racine));
  const changerPeriode = (valeur) => {
    setParams((p) => {
      const suivant = new URLSearchParams(p);
      if (valeur !== periode) suivant.set('periode', valeur);
      else suivant.delete('periode');
      return suivant;
    }, { replace: true });
  };

  // Changer de fiche referme le tiroir : on vient de s'en servir. Taper un mot
  // ne change que la partie `?mot=` de l'adresse, et le laisse donc ouvert.
  useEffect(() => {
    setTiroirOuvert(false);
  }, [pathname]);

  useEffect(() => {
    if (!tiroirOuvert) return undefined;
    const surTouche = (e) => {
      if (e.key === 'Escape') setTiroirOuvert(false);
    };
    document.addEventListener('keydown', surTouche);
    return () => document.removeEventListener('keydown', surTouche);
  }, [tiroirOuvert]);

  const libelleFerme = filtrable ? 'Chercher ou changer de fiche' : 'Changer de fiche';

  /* Le bouton est rendu UNE SEULE FOIS, dans la barre des pages, à la place de
     l'onglet. Sous 720 px cette barre ne porte plus que lui (NavigationSite.css)
     et passe à droite du bouton « Menu » : un seul élément, deux mises en page,
     jamais deux boutons pour un même geste. */
  const outil = (
    <button
      type="button"
      className="explorer-outil"
      aria-expanded={tiroirOuvert}
      aria-controls="explorer-tiroir"
      onClick={() => setTiroirOuvert((v) => !v)}
    >
      {/* Le libellé long dit les deux gestes ; sous 720 px il ne tient pas —
          226 px mesurés sur 390 px de large — et se réduit à « Fiches ». */}
      <span className="explorer-outil-long">{tiroirOuvert ? 'Fermer' : libelleFerme}</span>
      <span className="explorer-outil-court">{tiroirOuvert ? 'Fermer' : 'Fiches'}</span>
      <svg className="explorer-outil-chevron" width="10" height="7" viewBox="0 0 10 7" aria-hidden="true">
        <path d="M1 1.5L5 5.5L9 1.5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      </svg>
    </button>
  );

  return (
    <GroupFilterProvider>
      <div className="app-shell">
        <div className="explorer-main">
          <EnTeteSite navProps={{ outilExplorateur: outil }}>
            <div id="explorer-tiroir" className="explorer-tiroir" hidden={!tiroirOuvert}>
              {tiroirOuvert && (
                <>
                  {filtrable && (
                    <div className="explorer-tiroir-recherche">
                      <p className="explorer-tiroir-titre">Sur cette page</p>
                      <BarreFiltre onSaisie={changerMot} saisie={mot} />
                      {periodeDisponible && (
                        <div className="periode" role="group" aria-label="Période">
                          {Object.entries(PERIODES).map(([cle, p]) => (
                            <label className="periode-case" key={cle}>
                              <input
                                checked={periode === cle}
                                id={`periode-${cle}`}
                                onChange={() => changerPeriode(cle)}
                                type="checkbox"
                              />
                              {p.libelle}
                            </label>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                  <p className="explorer-tiroir-titre">Changer de fiche</p>
                  <CandidatesBar />
                  <GroupsBar />
                  <GovernmentsBar />
                </>
              )}
            </div>
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
    </GroupFilterProvider>
  );
}
