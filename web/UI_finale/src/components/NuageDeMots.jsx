import { useEffect, useRef, useState } from 'react';
import cloud from 'd3-cloud';
import { useEcranEtroit } from '../hooks/useLargeur';

/* Le nuage des mots des titres (#1314), disposé par d3-cloud comme sur la
 * maquette arbitrée (22/10/2026). La taille d'un mot est le nombre de titres
 * où il apparaît, écrit à côté de lui ; l'échelle suit le filtre. La graine est
 * fixe : un même jeu de mots retombe toujours au même endroit. */
const graine = (s) => () => { s = (s * 16807) % 2147483647; return (s - 1) / 2147483646; };

export default function NuageDeMots({ mots, actif = null, onMot }) {
  const boite = useRef(null);
  const [largeur, setLargeur] = useState(0);
  const [rendu, setRendu] = useState(0);
  const [places, setPlaces] = useState([]);
  const etroit = useEcranEtroit();

  useEffect(() => {
    const el = boite.current;
    if (!el) return undefined;
    const mesurer = () => {
      setLargeur(Math.max(320, Math.round(el.clientWidth)));
      setRendu(el.clientWidth);
    };
    mesurer();
    const ro = new ResizeObserver(mesurer);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  /* AU TÉLÉPHONE (#1372, forme A du 28/10/2026), aucun nombre en exposant
   * sous 13 px RENDUS : le dessin fait au moins 320 unités, et se réduit
   * quand la boîte est plus étroite. */
  const plancherN = etroit && rendu > 0 ? 13 * (largeur / rendu) : 9;
  /* LES MOTS AUSSI (29/10/2026) : à 320 px d'écran, le plus petit mot dessiné
   * en 13 unités rendait 11,8 px. Il part du même plancher que les nombres, et
   * la hauteur du dessin grandit comme la surface des mots (le carré du
   * facteur), pour qu'ils trouvent autant de place qu'avant. */
  // Arrondi au-dessus : d3-cloud tronque la taille à l'entier (15,4 → 15, soit 12,7 px rendus).
  const plancherMot = etroit && rendu > 0 ? Math.max(13, Math.ceil(13 * (largeur / rendu))) : 13;
  const hauteur = Math.round(
    (mots.length >= 60 ? 440 : Math.max(220, Math.min(380, 120 + mots.length * 7))) * (plancherMot / 13) ** 2,
  );

  useEffect(() => {
    if (!largeur || !mots.length) { setPlaces([]); return undefined; }
    const n = mots.map(([, c]) => c);
    const mn = Math.min(...n), mx = Math.max(...n);
    const taille = (c) => (mx === mn ? Math.max(22, plancherMot) : plancherMot + ((c - mn) / (mx - mn)) * Math.min(42, 18 * (mx - mn)));
    let vivant = true;
    const disposition = cloud()
      .size([largeur, hauteur])
      .words(mots.map(([w, c]) => ({ w, c, text: `${w} ${c}`, size: taille(c) })))
      .padding(3)
      .rotate(0)
      .font('Manrope')
      .fontWeight(700)
      .fontSize((d) => d.size)
      .random(graine(7))
      .spiral('archimedean')
      .on('end', (ws) => { if (vivant) setPlaces(ws); });
    disposition.start();
    return () => { vivant = false; disposition.stop(); };
  }, [mots, largeur, hauteur, plancherMot]);

  return (
    <div className="lgp-mots" ref={boite}>
      {largeur > 0 && (
        <svg aria-label="Nuage des mots des titres" role="img" viewBox={`0 0 ${largeur} ${hauteur}`}>
          <g transform={`translate(${largeur / 2},${hauteur / 2})`}>
            {places.map((d) => (
              <text
                aria-pressed={actif === d.w}
                className={`lgp-mot${actif === d.w ? ' lgp-sel' : ''}`}
                key={d.w}
                onClick={() => onMot(d.w)}
                onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onMot(d.w); } }}
                role="button"
                style={{ fontSize: `${d.size}px` }}
                tabIndex={0}
                textAnchor="middle"
                transform={`translate(${d.x},${d.y})`}
              >
                {d.w}
                <tspan className="lgp-mot-n" dx="0.15em" dy="-0.45em" style={{ fontSize: `${Math.max(plancherN, d.size * 0.45)}px` }}>{d.c}</tspan>
              </text>
            ))}
          </g>
        </svg>
      )}
    </div>
  );
}
