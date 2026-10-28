import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useLargeur } from '../../hooks/useLargeur';
import BulleSurvol, { cibleDans } from './BulleSurvol';

/* ── Législatures et gouvernements depuis 2012, en ligne de métro (#1329) ─────
 *
 * Arbitrée sur maquette le 22/10/2026 (https://claude.ai/artifact/77vSvbZkMBFuyorgwBYtV2),
 * après une frise à l'échelle du temps où Barnier (trois mois) ou Philippe I (un
 * mois) n'avaient pas la place d'écrire leur nom.
 *
 * DEUX VOIES PARALLÈLES : l'Assemblée en prune, le gouvernement en rouille. Une
 * station par Premier ministre. Une traverse fine passe d'une législature à la
 * suivante, en pointillé noir quand elle a fini par une dissolution. La station
 * d'aujourd'hui est jaune.
 *
 * L'ÉCHELLE : une législature prend une largeur moitié selon sa durée, moitié
 * selon son nombre de Premiers ministres. À durée seule, les trois de la XVIIe
 * n'auraient pas eu la place ; à nombre seul, la XVIIe (deux ans) paraissait
 * aussi longue que la XIVe (cinq). Les durées exactes sont sur les fiches.
 *
 * SUR TÉLÉPHONE, la même ligne descend, le plus récent en haut.
 *
 * UN PREMIER MINISTRE À PLUSIEURS GOUVERNEMENTS (23/10/2026) : son nœud ouvre,
 * au clic, le choix entre ses gouvernements (I, II) et leurs dates, en mois et
 * année : l'année seule écrirait « 2012 – 2012 » pour Ayrault I. Un nœud qui ne
 * menait nulle part donnait l'impression d'un bouton en panne ; le menu a
 * remplacé les pastilles I / II posées sous le nom. Au clic et non au survol :
 * un menu de survol se referme quand la souris le rejoint, et n'existe pas sur
 * téléphone.
 *
 * LA BULLE DE SURVOL (23/10/2026) : sur une législature, ses dates et le groupe
 * que l'Assemblée déclare majoritaire, s'il existe ; sur un gouvernement, ses
 * dates ; puis, en gris, ce que le lecteur trouvera en cliquant. Un Premier
 * ministre à plusieurs gouvernements n'en a pas : son menu donne les dates.
 *
 * Un Premier ministre est rangé dans la législature où il a gouverné le plus
 * longtemps (Attal : XVIe ; Borne : XVIe ; Philippe : XVe). */

const ETROIT = 520;
const jour = (s) => new Date(`${s}T00:00:00Z`).getTime();
const annee = (s) => s.slice(0, 4);
/* Mois et année dans le menu : courts, et alignés d'une ligne à l'autre. */
const date = (s) => `${s.slice(5, 7)}/${s.slice(0, 4)}`;
const periode = (g) => (g.fin ? `${date(g.debut)} – ${date(g.fin)}` : `depuis ${date(g.debut)}`);
const LARGEUR_MENU = 188;
const bulleLegislature = (l) => ({
  lignes: [
    l.fin ? `${date(l.debut)} – ${date(l.fin)}` : `Depuis ${date(l.debut)}`,
    ...(l.groupeMajoritaire ? [`Groupe majoritaire : ${l.groupeMajoritaire}`] : []),
  ],
  note: l.fin ? 'Qui siégeait, et ce que l’Assemblée a voté' : 'Qui siège, et ce que l’Assemblée vote',
});
const bulleGouvernement = (g) => ({
  lignes: [g.fin ? `${date(g.debut)} – ${date(g.fin)}` : `Depuis ${date(g.debut)}`],
  note: g.fin ? 'Qui le composait, et ce qu’il a fait adopter' : 'Qui le compose, et ce qu’il fait adopter',
});

function premiersMinistres(gouvernements, legislatures, aujourdhui) {
  const debut0 = legislatures.length ? jour(legislatures[0].debut) - 35 * 864e5 : 0;
  const retenus = gouvernements
    .filter((g) => g.debut && (g.fin ? jour(g.fin) : jour(aujourdhui)) >= debut0)
    .sort((a, b) => a.debut.localeCompare(b.debut));
  const pms = [];
  retenus.forEach((g) => {
    const nom = g.title.replace(/^Gouvernement\s+/, '');
    const m = nom.match(/^(.*?)\s+(I{1,3}|IV|V)$/);
    const pm = m ? m[1] : nom;
    const dernier = pms[pms.length - 1];
    const gv = { id: g.id, nom, numero: m ? m[2] : null, debut: g.debut, fin: g.fin };
    if (dernier && dernier.nom === pm) dernier.gouvernements.push(gv);
    else pms.push({ nom: pm, gouvernements: [gv] });
  });
  return pms.map((p) => {
    const d0 = p.gouvernements[0].debut, d1 = p.gouvernements[p.gouvernements.length - 1].fin;
    const a0 = annee(d0), a1 = d1 ? annee(d1) : null;
    const ans = !a1 ? `depuis ${a0}` : a0 === a1 ? a0 : `${a0}–${a1}`;
    // la législature où il a gouverné le plus longtemps
    let meilleure = 0, recouvre = -1;
    legislatures.forEach((l, k) => {
      const r = Math.min(d1 ? jour(d1) : jour(aujourdhui), l.fin ? jour(l.fin) : jour(aujourdhui)) - Math.max(jour(d0), jour(l.debut));
      if (r > recouvre) { recouvre = r; meilleure = k; }
    });
    return { ...p, ans, legislature: meilleure, actif: !d1 };
  });
}

export default function FriseMetro({ legislatures, gouvernements, aujourdhui }) {
  const [ref, largeur] = useLargeur();
  const navigate = useNavigate();
  const legs = useMemo(() => [...legislatures].sort((a, b) => a.debut.localeCompare(b.debut)), [legislatures]);
  const pms = useMemo(() => premiersMinistres(gouvernements, legs, aujourdhui), [gouvernements, legs, aujourdhui]);

  const aller = (vers) => (e) => { e.preventDefault(); navigate(vers); };
  const clavier = (vers) => (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); navigate(vers); } };
  const lien = (vers, titre) => ({ role: 'link', tabIndex: 0, className: 'fm-seg', onClick: aller(vers), onKeyDown: clavier(vers), 'aria-label': titre });

  /* La bulle de survol, posée dans le conteneur de la frise. */
  const [bulle, setBulle] = useState(null);
  const montrer = (contenu) => {
    const ouvrir = (e) => setBulle({ ...contenu, cible: cibleDans(e.currentTarget, ref.current) });
    const fermer = () => setBulle(null);
    return { onMouseEnter: ouvrir, onMouseLeave: fermer, onFocus: ouvrir, onBlur: fermer };
  };

  /* Le choix entre les gouvernements d'un même Premier ministre. */
  const [menu, setMenu] = useState(null);
  const menuRef = useRef(null);
  useEffect(() => {
    if (!menu) return undefined;
    const dehors = (e) => { if (!menuRef.current?.contains(e.target) && !e.target.closest?.('.fm-choix')) setMenu(null); };
    const echap = (e) => { if (e.key === 'Escape') setMenu(null); };
    document.addEventListener('mousedown', dehors);
    document.addEventListener('keydown', echap);
    return () => { document.removeEventListener('mousedown', dehors); document.removeEventListener('keydown', echap); };
  }, [menu]);
  const choix = (p, x, y) => {
    const ouvrir = (e) => { e.preventDefault(); setBulle(null); setMenu((m) => (m?.nom === p.nom ? null : { nom: p.nom, x, y })); };
    return {
      role: 'button', tabIndex: 0, className: 'fm-seg fm-choix', 'aria-haspopup': 'menu', 'aria-expanded': menu?.nom === p.nom,
      'aria-label': `${p.nom} : choisir un gouvernement`,
      onClick: ouvrir, onKeyDown: (e) => { if (e.key === 'Enter' || e.key === ' ') ouvrir(e); },
    };
  };
  const pmOuvert = menu && pms.find((p) => p.nom === menu.nom);
  /* Sur ordinateur, le menu s'ouvre au-dessus du nœud, pour rester dans le
   * premier écran ; sur téléphone, en dessous, la ligne descendant. */
  /* `decalage` : où tombe la pointe dans le menu ; centré par défaut. */
  const fenetre = (W, enHaut, decalage = LARGEUR_MENU / 2) => {
    if (!pmOuvert) return null;
    const gauche = Math.max(0, Math.min(W - LARGEUR_MENU, menu.x - decalage));
    return (
      <div
        className={`fm-menu ${enHaut ? 'fm-menu--haut' : 'fm-menu--bas'}`}
        ref={menuRef}
        role="menu"
        aria-label={`Gouvernements ${pmOuvert.nom}`}
        style={{
          left: gauche,
          width: LARGEUR_MENU,
          '--pointe': `${Math.max(14, Math.min(LARGEUR_MENU - 14, menu.x - gauche))}px`,
          ...(enHaut ? { bottom: `calc(100% - ${menu.y - 16}px)` } : { top: menu.y + 28 }),
        }}
      >
        {pmOuvert.gouvernements.map((g) => (
          <Link key={g.id} role="menuitem" className="fm-menu-l" to={`/gouvernements/${g.id}`} aria-label={`Gouvernement ${g.nom}, ${periode(g)}`} onClick={() => setMenu(null)}>
            <span className="fm-menu-n" aria-hidden="true">{g.numero}</span>
            <span className="fm-menu-d">{periode(g)}</span>
            <span className="fm-menu-f" aria-hidden="true">→</span>
          </Link>
        ))}
      </div>
    );
  };

  if (!legs.length || !pms.length) return <div className="fm" ref={ref} />;
  const W = largeur || 900;
  const nb = legs.map((_, k) => pms.filter((p) => p.legislature === k).length);
  const leg = legs.map((l, k) => ({
    ...l,
    nom: l.court,
    ans: l.fin ? `${annee(l.debut)}–${annee(l.fin)}` : `depuis ${annee(l.debut)}`,
    lien: `/legislatures/${l.id}`,
    dissolution: l.modeFin === 'dissolution' && k < legs.length - 1,
  }));

  if (W < ETROIT) {
    /* Téléphone : la ligne descend, le plus récent en haut. Les deux voies
     * sont décalées de 16 px depuis que les années passent à 13 px (#1372,
     * 28/10/2026) : « depuis 2024 », aligné à droite contre la voie des
     * législatures, sortait du cadre à gauche. Les années descendent de 2 px
     * sous le nom, passé à 14 px. */
    const n = pms.length, pas = 50, y0 = 22, Y = (i) => y0 + (n - 1 - i) * pas, xR = 128, xA = 90, H = y0 + (n - 1) * pas + 30;
    const premiere = (k) => pms.findIndex((p) => p.legislature === k);
    const derniere = (k) => n - 1 - [...pms].reverse().findIndex((p) => p.legislature === k);
    const bornesY = leg.map((_, k) => [
      derniere(k) === n - 1 ? Y(n - 1) - 16 : (Y(derniere(k)) + Y(derniere(k) + 1)) / 2,
      premiere(k) === 0 ? Y(0) + 16 : (Y(premiere(k)) + Y(premiere(k) - 1)) / 2,
    ]);
    return (
      <div className="fm" ref={ref}>
        <svg className="fm-v" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Législatures et gouvernements depuis 2012">
          {leg.map((l, k) => {
            const [h, b] = bornesY[k];
            const a = h + (k < leg.length - 1 ? 5 : 0), z = b - (k > 0 ? 5 : 0);
            return (
              <g key={l.id} {...lien(l.lien, `${l.title}, ${l.ans}`)} {...montrer(bulleLegislature(l))}>
                <rect x="0" y={a} width={xA + 8} height={z - a} fill="transparent" />
                <line className="fm-voie-a" x1={xA} x2={xA} y1={a} y2={z} />
                <text x={xA - 12} y={a + 16} textAnchor="end" className="fm-leg-nom">{l.nom}</text>
                <text x={xA - 12} y={a + 33} textAnchor="end" className="fm-ans">{l.ans}</text>
              </g>
            );
          })}
          {leg.slice(0, -1).map((l, k) => {
            const yb = (bornesY[k][0] + bornesY[k + 1][1]) / 2;
            return (
              <g key={`t${l.id}`}>
                <line className={l.dissolution ? 'fm-trav fm-trav--diss' : 'fm-trav'} x1={xA - 8} x2={xR + 8} y1={yb} y2={yb} />
                {l.dissolution && <text x={xA - 12} y={yb - 5} textAnchor="end" className="fm-diss">dissolution</text>}
              </g>
            );
          })}
          <line className="fm-voie-g" x1={xR} x2={xR} y1={Y(n - 1) - 14} y2={Y(0) + 14} />
          {pms.map((p, i) => {
            const y = Y(i), seul = p.gouvernements.length === 1;
            return (
              <g key={p.nom} {...(seul ? { ...lien(`/gouvernements/${p.gouvernements[0].id}`, `Gouvernement ${p.gouvernements[0].nom}, ${p.ans}`), ...montrer(bulleGouvernement(p.gouvernements[0])) } : choix(p, xR, y))}>
                <circle className={p.actif ? 'fm-station fm-station--auj' : 'fm-station'} cx={xR} cy={y} r="8" />
                <text x={xR + 20} y={y + 1} className="fm-pm-nom">{p.nom}</text>
                <text x={xR + 20} y={y + 18} className="fm-ans">{p.ans}</text>
              </g>
            );
          })}
        </svg>
        {fenetre(W, false, 24)}
        <BulleSurvol bulle={bulle} />
      </div>
    );
  }

  /* Ordinateur : la ligne se lit de gauche à droite. */
  const n = pms.length, m = 30, yA = 34, yR = 66, H = 116;
  const durees = leg.map((l) => (l.fin ? jour(l.fin) : jour(aujourdhui)) - jour(l.debut));
  const tot = durees.reduce((a, b) => a + b, 0);
  const bornes = [m];
  leg.forEach((_, k) => bornes.push(bornes[k] + (0.5 * nb[k] / n + 0.5 * durees[k] / tot) * (W - 2 * m)));
  const X = [];
  leg.forEach((_, k) => {
    const a = bornes[k], w = bornes[k + 1] - a, d = w / (2 * Math.max(1, nb[k]));
    const fin = k === leg.length - 1 ? w - 4 : w - d;
    for (let j = 0; j < nb[k]; j += 1) X.push(a + d + (nb[k] > 1 ? (j * (fin - d)) / (nb[k] - 1) : 0));
  });
  const etroit = X.map((x, i) => Math.min(i > 0 ? x - X[i - 1] : 1e9, i < n - 1 ? X[i + 1] - x : 1e9) < 60);
  return (
    <div className="fm" ref={ref}>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Législatures et gouvernements depuis 2012">
        {leg.map((l, k) => {
          const a = bornes[k] + (k ? 5 : 0), b = bornes[k + 1] - (k < leg.length - 1 ? 5 : 0);
          return (
            <g key={l.id} {...lien(l.lien, `${l.title}, ${l.ans}`)} {...montrer(bulleLegislature(l))}>
              <rect x={a} y={yA - 26} width={b - a} height="38" fill="transparent" />
              <line className="fm-voie-a" x1={a} x2={b} y1={yA} y2={yA} strokeLinecap={k === 0 || k === leg.length - 1 ? 'round' : 'butt'} />
              <text x={(a + b) / 2} y={yA - 12} textAnchor="middle" className="fm-leg-nom">
                {l.nom}{b - a > 150 && <tspan className="fm-ans" dx="7">{l.ans}</tspan>}
              </text>
            </g>
          );
        })}
        {leg.slice(0, -1).map((l, k) => (
          <g key={`t${l.id}`}>
            <line className={l.dissolution ? 'fm-trav fm-trav--diss' : 'fm-trav'} x1={bornes[k + 1]} x2={bornes[k + 1]} y1={yA - (l.dissolution ? 8 : 6)} y2={yR + 8} />
            {l.dissolution && <text x={bornes[k + 1]} y={yA - 12} textAnchor="middle" className="fm-diss">dissolution</text>}
          </g>
        ))}
        <line className="fm-voie-g" x1={bornes[0]} x2={bornes[bornes.length - 1]} y1={yR} y2={yR} />
        {pms.map((p, i) => {
          const x = X[i], seul = p.gouvernements.length === 1;
          return (
            <g key={p.nom} {...(seul ? { ...lien(`/gouvernements/${p.gouvernements[0].id}`, `Gouvernement ${p.gouvernements[0].nom}, ${p.ans}`), ...montrer(bulleGouvernement(p.gouvernements[0])) } : choix(p, x, yR))}>
              <circle className={p.actif ? 'fm-station fm-station--auj' : 'fm-station'} cx={x} cy={yR} r="8" />
              <text x={x} y={yR + 28} textAnchor="middle" className={etroit[i] ? 'fm-pm-nom fm-pm-nom--etroit' : 'fm-pm-nom'}>{p.nom}</text>
              <text x={x} y={yR + 42} textAnchor="middle" className={etroit[i] ? 'fm-ans fm-ans--etroit' : 'fm-ans'}>{p.ans}</text>
            </g>
          );
        })}
      </svg>
      {fenetre(W, true)}
      <BulleSurvol bulle={bulle} />
    </div>
  );
}
