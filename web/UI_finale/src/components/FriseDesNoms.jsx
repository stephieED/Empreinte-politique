import { useLayoutEffect, useRef, useState } from 'react';
import { rangerEtiquettes } from '../utils/frise';
import './FriseDesNoms.css';

/* LES NOMS AU-DESSUS D'UNE FRISE, AU TÉLÉPHONE (#1372, lot 3 suite, formes
 * arbitrées le 28/10/2026) : la frise des gouvernements d'une législature
 * (forme F, un nom et sa durée) et la fenêtre des gouvernements voisins sur la
 * fiche de gouvernement (forme C, un nom par ligne). Chaque nom part d'un trait
 * vertical à sa date de début ; le rangement en niveaux est
 * `rangerEtiquettes` (`utils/frise.js`), sur les largeurs MESURÉES à l'écran,
 * refait quand la largeur change ou que la police arrive.
 *
 * `noms` : `[{ cle, x (0 à 100), contenu, sous, courant }]`.
 * `hauteurNiveau` : 38 px pour deux lignes, 22 px pour une. */
export default function FriseDesNoms({ noms, hauteurNiveau, uneLigne = false }) {
  const zone = useRef(null);
  const [rang, setRang] = useState(null);
  const cles = noms.map((n) => `${n.cle}@${n.x.toFixed(3)}`).join('|');

  useLayoutEffect(() => {
    const el = zone.current;
    if (!el) return undefined;
    let vivant = true;
    let derniere = -1;
    const ranger = (force = false) => {
      if (!vivant) return;
      const W = el.clientWidth;
      if (!W || (!force && W === derniere)) return;
      derniere = W;
      const etiquettes = [...el.children].map((c, i) => ({
        x: (noms[i].x / 100) * W,
        largeur: Math.ceil(c.getBoundingClientRect().width),
      }));
      const r = rangerEtiquettes(etiquettes, W);
      setRang((avant) => (avant && JSON.stringify(avant) === JSON.stringify(r) ? avant : r));
    };
    ranger(true);
    document.fonts?.ready?.then(() => ranger(true));
    if (typeof ResizeObserver === 'undefined') return () => { vivant = false; };
    const ro = new ResizeObserver(() => ranger());
    ro.observe(el);
    return () => { vivant = false; ro.disconnect(); };
    // `cles` résume `noms` : les positions et l'identité des noms.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cles]);

  const N = rang ? Math.max(1, rang.nombre) : 1;
  const H = N * hauteurNiveau;
  return (
    <div className={`frn${uneLigne ? ' frn--une-ligne' : ''}`} ref={zone} style={{ height: H }}>
      {noms.map((n, i) => {
        const niveau = rang ? rang.niveaux[i] : 0;
        const aDroite = rang ? rang.aDroite[i] : false;
        const haut = (N - 1 - niveau) * hauteurNiveau;
        return (
          <div
            className={`frn-nom${aDroite ? ' frn-nom--droite' : ''}${n.courant ? ' frn-nom--courant' : ''}`}
            key={n.cle}
            style={{
              ...(aDroite ? { right: `${100 - n.x}%` } : { left: `${n.x}%` }),
              top: haut,
              height: H - haut,
              visibility: rang ? undefined : 'hidden',
            }}
          >
            <span className="frn-l1">{n.contenu}</span>
            {n.sous && <span className="frn-l2">{n.sous}</span>}
          </div>
        );
      })}
    </div>
  );
}
