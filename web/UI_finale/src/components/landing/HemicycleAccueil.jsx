import { useRef, useState } from 'react';
import BulleSurvol, { cibleDans } from './BulleSurvol';
import { useNavigate } from 'react-router-dom';
import { formatNumber } from '../../utils/lecture';

/* ── L'Assemblée aujourd'hui, par groupe (#1329) ──────────────────────────────
 *
 * Un secteur par groupe, d'épaisseur constante et d'angle proportionnel à ses
 * députés, de la gauche vers la droite comme dans l'hémicycle (siège médian) ;
 * les non-inscrits en gris clair au bout. Deux tons d'encre alternés séparent
 * deux groupes voisins : aucune couleur de position, la XVIIe n'en publie pas.
 *
 * Chaque groupe est nommé (22/10/2026, « que toutes les étiquettes soient
 * visibles ») : dans son secteur s'il compte au moins 40 députés, sinon juste
 * dehors, relié par un trait court. Survoler un groupe éteint les autres ;
 * cliquer ouvre sa fiche. Aucun classement : l'ordre est celui des sièges.
 *
 * La bulle de survol (23/10/2026) donne le nom complet et le nombre de
 * députés, que l'hémicycle n'écrit pas, puis ce que la fiche montre. */

const CX = 150, CY = 146, R0 = 78, R1 = 128, ECART = 0.012, DEDANS = 40;
const pt = (r, a) => [CX + r * Math.cos(a), CY - r * Math.sin(a)];
function secteur(a0, a1) {
  const [x0, y0] = pt(R1, a0), [x1, y1] = pt(R1, a1), [x2, y2] = pt(R0, a1), [x3, y3] = pt(R0, a0);
  return `M${x0},${y0} A${R1},${R1} 0 0 1 ${x1},${y1} L${x2},${y2} A${R0},${R0} 0 0 0 ${x3},${y3} Z`;
}

export default function HemicycleAccueil({ groupes }) {
  const navigate = useNavigate();
  const [survol, setSurvol] = useState(null);
  const [bulle, setBulle] = useState(null);
  const cadre = useRef(null);
  const total = groupes.reduce((n, g) => n + (g.membres || 0), 0);
  let a = Math.PI;
  const secteurs = groupes.map((g, i) => {
    const da = (Math.PI * (g.membres || 0)) / total;
    const s = { ...g, i, a0: a - ECART / 2, a1: a - da + ECART / 2, m: a - da / 2 };
    a -= da;
    return s;
  });
  return (
    <div className="ha-cadre" ref={cadre}>
    <svg className="ha" viewBox="-36 -24 372 184" role="img" aria-label={`L’Assemblée aujourd’hui : ${formatNumber(total)} députés`} onMouseLeave={() => setSurvol(null)}>
      {secteurs.map((s) => {
        const c = Math.cos(s.m);
        const aller = () => s.lien && navigate(s.lien);
        const ouvrir = (e) => {
          setSurvol(s.i);
          setBulle({
            lignes: [`${s.nom} · ${formatNumber(s.membres)} députés`],
            note: s.lien ? 'Ses députés, et comment ils ont voté' : null,
            cible: cibleDans(e.currentTarget, cadre.current),
          });
        };
        return (
          <g
            key={s.sigle}
            className={`ha-g${s.lien ? ' ha-g--lien' : ''}`}
            style={{ opacity: survol != null && survol !== s.i ? 0.25 : 1 }}
            onMouseEnter={ouvrir}
            onMouseLeave={() => setBulle(null)}
            onFocus={ouvrir}
            onBlur={() => { setBulle(null); setSurvol(null); }}
            onClick={aller}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); aller(); } }}
            role={s.lien ? 'link' : undefined}
            tabIndex={s.lien ? 0 : undefined}
            aria-label={`${s.nom} : ${formatNumber(s.membres)} députés`}
          >
            <path d={secteur(s.a0, s.a1)} className={s.ni ? 'ha-s ha-s--ni' : s.i % 2 ? 'ha-s ha-s--b' : 'ha-s'} />
            {s.membres >= DEDANS && !s.ni ? (
              <text x={pt((R0 + R1) / 2, s.m)[0]} y={pt((R0 + R1) / 2, s.m)[1] + 3.5} textAnchor="middle" className="ha-sigle ha-sigle--dedans">{s.sigle}</text>
            ) : (
              <>
                <line x1={pt(R1 + 2, s.m)[0]} y1={pt(R1 + 2, s.m)[1]} x2={pt(R1 + 10, s.m)[0]} y2={pt(R1 + 10, s.m)[1]} className="ha-trait" />
                <text x={pt(R1 + 13, s.m)[0]} y={pt(R1 + 13, s.m)[1] + 3.5} textAnchor={c < -0.2 ? 'end' : c > 0.2 ? 'start' : 'middle'} className="ha-sigle">{s.sigle}</text>
              </>
            )}
          </g>
        );
      })}
      <text x={CX} y={CY - 16} textAnchor="middle" className="ha-total">{formatNumber(total)}</text>
      <text x={CX} y={CY} textAnchor="middle" className="ha-sous">députés</text>
    </svg>
    <BulleSurvol bulle={bulle} />
    </div>
  );
}
