import { useEffect, useRef } from 'react';
import { useLocation, useNavigationType } from 'react-router-dom';
import { AVANCE_ANCRE as AVANCE_FICHE } from './RangeeSections';
import { AVANCE_ANCRE as AVANCE_PAGE } from './SommaireSections';

/* ── Le défilement au changement de page (#1448) ─────────────────────────────
 *
 * L'application change de page sans recharger, et le navigateur garde alors la
 * position de la page quittée : `/a-propos` défilée à 462 px ouvrait
 * `/mentions-legales` à 462 px. Ce composant fait ce qu'un vrai chargement
 * aurait fait :
 *
 * - une NOUVELLE page s'ouvre en haut ;
 * - une adresse à ancre (`/methodologie#couverture`) s'ouvre sur sa section, le
 *   titre sous la barre collée et non dessous ;
 * - « Précédent » et « Suivant » (POP) gardent la position que le navigateur
 *   rend de lui-même, sauf au premier chargement d'une adresse à ancre.
 *
 * Changer le mot cherché ou la période ne change pas de page : la position
 * reste.
 *
 * L'ANCRE SE SUIT PENDANT LE CHARGEMENT. La section demandée n'existe souvent
 * pas encore, et ce qui se charge au-dessus d'elle la pousse vers le bas : sur
 * `/sources#frise`, la liste des candidats, arrivée après la frise, la
 * repoussait de 2 191 px. La section est donc recalée à chaque changement de
 * la page, pendant quelques secondes, et le suivi s'arrête dès que le lecteur
 * fait défiler lui-même.
 *
 * Sous 720 px, une fiche montre une section à la fois : c'est
 * `GlissementSections` qui trouve la page de l'ancre, et ce composant le laisse
 * faire. */

const DUREE_SUIVI = 4000;
const GESTES = ['wheel', 'touchstart', 'keydown', 'mousedown'];

function avance(cible) {
  return cible.closest('.static-page') ? AVANCE_PAGE : AVANCE_FICHE;
}

function glissementActif() {
  return window.matchMedia('(max-width: 720px)').matches
    && Boolean(document.querySelector('.explorer-profile-zone'));
}

/** Recale la section `id` jusqu'à ce que la page se taise ou que le lecteur défile. */
function suivreAncre(id) {
  let fini = false;
  let attente = null;
  const recaler = () => {
    if (fini || glissementActif()) return;
    const cible = document.getElementById(id);
    // Une section cachée (onglet replié, page du glissement) n'a pas de place.
    if (!cible || !cible.getClientRects().length) return;
    const haut = cible.getBoundingClientRect().top + window.scrollY - avance(cible);
    if (Math.abs(window.scrollY - Math.max(0, haut)) > 1) window.scrollTo({ top: Math.max(0, haut) });
  };
  const planifier = () => {
    if (attente === null) attente = requestAnimationFrame(() => { attente = null; recaler(); });
  };
  const arreter = () => {
    if (fini) return;
    fini = true;
    observateur.disconnect();
    taille.disconnect();
    if (attente !== null) cancelAnimationFrame(attente);
    clearTimeout(minuterie);
    GESTES.forEach((g) => window.removeEventListener(g, arreter, true));
  };
  const observateur = new MutationObserver(planifier);
  observateur.observe(document.body, { childList: true, subtree: true });
  const taille = new ResizeObserver(planifier);
  taille.observe(document.body);
  GESTES.forEach((g) => window.addEventListener(g, arreter, { capture: true, passive: true }));
  const minuterie = setTimeout(arreter, DUREE_SUIVI);
  recaler();
  return arreter;
}

export default function SuiviDeNavigation() {
  const { key, pathname, search, hash } = useLocation();
  const type = useNavigationType();
  const avant = useRef({ pathname, search, hash });

  useEffect(() => {
    const precedent = avant.current;
    avant.current = { pathname, search, hash };
    // La première adresse du routeur porte la clé « default ».
    const auChargement = key === 'default';
    const changeDePage = precedent.pathname !== pathname;

    if (type === 'POP' && !auChargement) return undefined;
    if (hash.length > 1) {
      /* Taper un mot sur `/groupes/AN-SOC#section-3` change l'adresse sans
       * redemander la section : seul un changement de page ou d'ancre, ou un
       * nouveau clic sur le même lien (adresse identique), la suit. */
      const redemandee = auChargement || changeDePage || precedent.hash !== hash || precedent.search === search;
      return redemandee ? suivreAncre(decodeURIComponent(hash.slice(1))) : undefined;
    }
    if (changeDePage) window.scrollTo({ top: 0 });
    return undefined;
    // `key` change à chaque navigation, même vers l'adresse où l'on est déjà.
  }, [key, pathname, search, hash, type]);

  return null;
}
