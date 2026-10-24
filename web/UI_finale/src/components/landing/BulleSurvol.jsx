import { useLayoutEffect, useRef, useState } from 'react';

/* ── La bulle de survol des tuiles de l'accueil (#1329, validée le 23/10/2026) ──
 *
 * Au survol d'une législature, d'un gouvernement ou d'un groupe, elle dit en
 * premier le fait propre à l'élément (ses dates, le groupe que l'Assemblée
 * déclare majoritaire), puis, en gris, ce que le lecteur trouvera en cliquant.
 * Rien de ce que la tuile écrit déjà.
 *
 * Elle se pose au-dessus de l'élément survolé, centrée sur lui, sans sortir de
 * son conteneur ; s'il n'y a pas la place au-dessus, elle passe dessous.
 *
 * `cible` : { haut, bas, centre } en pixels dans le conteneur, mesurés sur
 * l'élément survolé ; `lignes` : le texte, la dernière étant `note`. */
export function cibleDans(el, conteneur) {
  const r = el.getBoundingClientRect(), c = conteneur.getBoundingClientRect();
  return { haut: r.top - c.top, bas: r.bottom - c.top, centre: r.left - c.left + r.width / 2, largeur: c.width, ecran: -c.top };
}

export default function BulleSurvol({ bulle }) {
  const ref = useRef(null);
  const [pos, setPos] = useState(null);
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el || !bulle) { setPos(null); return; }
    const { haut, bas, centre, largeur, ecran } = bulle.cible;
    const l = el.offsetWidth, h = el.offsetHeight;
    const gauche = Math.max(0, Math.min(largeur - l, centre - l / 2));
    const dessus = haut - h - 8;
    setPos({ left: gauche, top: dessus >= ecran ? dessus : bas + 8 });
  }, [bulle]);
  if (!bulle) return null;
  return (
    <div className="bulle-survol" ref={ref} role="tooltip" style={pos ? { left: pos.left, top: pos.top } : { visibility: 'hidden', left: 0, top: 0 }}>
      {bulle.lignes.map((t) => <div key={t}>{t}</div>)}
      {bulle.note && <div className="bulle-survol-note">{bulle.note}</div>}
    </div>
  );
}
