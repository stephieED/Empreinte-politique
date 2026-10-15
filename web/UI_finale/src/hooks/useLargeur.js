import { useEffect, useLayoutEffect, useRef, useState } from 'react';

/* ── La largeur réelle d'un bloc, et l'écran étroit (#867) ────────────────────
 *
 * Une figure SVG dessinée sur un `viewBox` de 1 000 unités se réduit au tiers
 * sur un téléphone : son texte de 11 px y tombe à 3 ou 4 px (mesuré le
 * 15/10/2026 à 360 px). Sous 720 px, les « En bref » se redessinent donc à la
 * largeur MESURÉE de leur carte, une unité pour un pixel. `0` tant que la
 * mesure n'est pas faite : la figure garde alors son dessin large.
 *
 * Le seuil est celui des feuilles de style (`max-width: 720px`), pour qu'une
 * figure et sa mise en page basculent ensemble. */
export const REQUETE_ETROIT = '(max-width: 720px)';

export function useLargeur() {
  const ref = useRef(null);
  const [largeur, setLargeur] = useState(0);
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el || typeof ResizeObserver === 'undefined') return undefined;
    const obs = new ResizeObserver((entrees) => {
      setLargeur(Math.round(entrees[0].contentRect.width));
    });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);
  return [ref, largeur];
}

export function useEcranEtroit() {
  const lire = () => typeof window !== 'undefined' && Boolean(window.matchMedia?.(REQUETE_ETROIT).matches);
  const [etroit, setEtroit] = useState(lire);
  useEffect(() => {
    const requete = window.matchMedia?.(REQUETE_ETROIT);
    if (!requete) return undefined;
    const suivre = () => setEtroit(requete.matches);
    requete.addEventListener('change', suivre);
    return () => requete.removeEventListener('change', suivre);
  }, []);
  return etroit;
}
