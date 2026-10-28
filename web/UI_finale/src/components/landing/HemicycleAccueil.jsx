import { useState } from 'react';
import BulleSurvol, { cibleDans } from './BulleSurvol';
import { useNavigate } from 'react-router-dom';
import { formatNumber } from '../../utils/lecture';
import { useEcranEtroit, useLargeur } from '../../hooks/useLargeur';

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

/* AU TÉLÉPHONE, LE CADRE SERRE LA FIGURE (#1372, 28/10/2026, principe D1 de la
 * fiche de législature). Le `viewBox` large réserve des marges que le téléphone
 * paie en taille : les sigles y tombaient sous 10 px. Le cadre est calculé sur
 * l'arc et les étiquettes posées, et la taille des sigles — en unités de la
 * figure — est choisie pour qu'ils rendent 13 px : comme elle élargit le cadre,
 * le calcul est repris jusqu'à ce qu'il ne bouge plus. La largeur d'un sigle
 * est estimée (0,66 em par signe, en gras), d'où une marge. */
const PX_SIGLE = 13, EM = 0.66, MARGE = 4;
function cadreSerre(secteurs, largeur) {
  let f = 9.5, boite = null;
  for (let k = 0; k < 4; k += 1) {
    let x0 = CX - R1, x1 = CX + R1, y0 = CY - R1, y1 = CY + 0.3 * f;
    secteurs.forEach((s) => {
      if (s.membres >= DEDANS && !s.ni) return;
      const [lx, ly] = pt(R1 + 13, s.m), c = Math.cos(s.m), w = s.sigle.length * f * EM;
      const g = c < -0.2 ? lx - w : c > 0.2 ? lx : lx - w / 2;
      x0 = Math.min(x0, g); x1 = Math.max(x1, g + w);
      y0 = Math.min(y0, ly + 0.37 * f - 0.75 * f); y1 = Math.max(y1, ly + 0.37 * f + 0.25 * f);
    });
    boite = [x0 - MARGE, y0 - MARGE, x1 - x0 + 2 * MARGE, y1 - y0 + 2 * MARGE];
    f = (PX_SIGLE * boite[2]) / largeur;
  }
  return { viewBox: boite.map((v) => v.toFixed(1)).join(' '), f };
}

export default function HemicycleAccueil({ groupes }) {
  const navigate = useNavigate();
  const [survol, setSurvol] = useState(null);
  const [bulle, setBulle] = useState(null);
  const [cadre, largeur] = useLargeur();
  const etroit = useEcranEtroit();
  const total = groupes.reduce((n, g) => n + (g.membres || 0), 0);
  let a = Math.PI;
  const secteurs = groupes.map((g, i) => {
    const da = (Math.PI * (g.membres || 0)) / total;
    const s = { ...g, i, a0: a - ECART / 2, a1: a - da + ECART / 2, m: a - da / 2 };
    a -= da;
    return s;
  });
  const serre = etroit && largeur > 0 ? cadreSerre(secteurs, largeur) : null;
  // Sur ordinateur, les tailles restent celles de la feuille de style.
  const taille = serre ? { fontSize: serre.f } : undefined;
  const dyTexte = serre ? 0.37 * serre.f : 3.5;
  return (
    <div className="ha-cadre" ref={cadre}>
    <svg className="ha" viewBox={serre ? serre.viewBox : '-36 -24 372 184'} role="img" aria-label={`L’Assemblée aujourd’hui : ${formatNumber(total)} députés`} onMouseLeave={() => setSurvol(null)}>
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
              <text x={pt((R0 + R1) / 2, s.m)[0]} y={pt((R0 + R1) / 2, s.m)[1] + dyTexte} textAnchor="middle" className="ha-sigle ha-sigle--dedans" style={taille}>{s.sigle}</text>
            ) : (
              <>
                <line x1={pt(R1 + 2, s.m)[0]} y1={pt(R1 + 2, s.m)[1]} x2={pt(R1 + 10, s.m)[0]} y2={pt(R1 + 10, s.m)[1]} className="ha-trait" />
                <text x={pt(R1 + 13, s.m)[0]} y={pt(R1 + 13, s.m)[1] + dyTexte} textAnchor={c < -0.2 ? 'end' : c > 0.2 ? 'start' : 'middle'} className="ha-sigle" style={taille}>{s.sigle}</text>
              </>
            )}
          </g>
        );
      })}
      <text x={CX} y={CY - 16} textAnchor="middle" className="ha-total">{formatNumber(total)}</text>
      <text x={CX} y={CY} textAnchor="middle" className="ha-sous" style={taille}>députés</text>
    </svg>
    <BulleSurvol bulle={bulle} />
    </div>
  );
}
