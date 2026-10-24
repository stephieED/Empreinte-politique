/*
 * LA FICHE D'UNE LÉGISLATURE (#1314), arbitrée en maquette avec la propriétaire
 * du dépôt les 21 et 22/10/2026.
 * Maquette de référence : https://claude.ai/artifact/BHyLiaMR5m1TwbsfHFgVFV
 *
 * Le pendant parlementaire de la fiche de gouvernement : ce que l'Assemblée a
 * fait pendant UNE législature, sans jamais la mettre à côté d'une autre — les
 * législatures n'ont pas la même durée, et juxtaposer leurs volumes classerait
 * (AGENTS.md §2 règle 1).
 *
 *   01 « En bref »           — la durée réelle contre le mandat prévu, les
 *      gouvernements posés dessus, cinq chiffres.
 *   02 « Qui siégeait »      — l'hémicycle, les groupes dans l'ordre où ils
 *      siégeaient (place publiée par l'Assemblée, #1317), un arc par position
 *      déclarée.
 *   03 « Les textes de la législature » — la bibliothèque : un meuble par sort,
 *      une étagère par domaine, un livre par texte ; les textes passés par un
 *      vote solennel sont des livres plus épais, en tête d'étagère.
 *   04 « Le travail des commissions » — une barre par commission, découpée par
 *      étape, et un nuage des mots des titres que la barre filtre.
 *   05 « Ce qu'on n'a pas pu lire ».
 *
 * Écartés en maquette, à ne pas reproposer : les tailles par nombre
 * d'amendements (« pas comparable d'une loi à l'autre »), la date de la loi
 * comme figure (« n'apporte rien »), le meuble des textes déposés, les
 * mots-clés calculés sur les couvertures (abandonnés le 21/10).
 */
import { Fragment, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { formatNumber } from '../utils/lecture';
import { useEcranEtroit } from '../hooks/useLargeur';
import {
  ETAPES, ORIGINES, SANS_ORIGINE, SORTS, motsDesTitres,
} from '../utils/legislature';
import InfoBulle from './InfoBulle';
import NuageDeMots from './NuageDeMots';
import './GovernmentProfile.css';
import './LegislatureProfile.css';

const MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin',
  'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'];
function jour(iso) {
  if (!iso) return '';
  const [a, m, j] = iso.slice(0, 10).split('-').map(Number);
  return `${j === 1 ? '1er' : j} ${MOIS[m - 1]} ${a}`;
}
/* « 1 an 11 mois 12 jours », arbitré le 21/10 : la durée ne s'écrit pas en jours. */
function dureeEnClair(debut, fin) {
  if (!debut || !fin) return [];
  const A = new Date(`${debut}T12:00`), B = new Date(`${fin}T12:00`);
  let a = B.getFullYear() - A.getFullYear(), m = B.getMonth() - A.getMonth(), j = B.getDate() - A.getDate();
  if (j < 0) { m -= 1; j += new Date(B.getFullYear(), B.getMonth(), 0).getDate(); }
  if (m < 0) { a -= 1; m += 12; }
  const p = (n, s, pl) => (n ? `${n} ${n > 1 ? pl : s}` : null);
  return [p(a, 'an', 'ans'), p(m, 'mois', 'mois'), p(j, 'jour', 'jours')].filter(Boolean);
}
const couleurOrigine = (d) => (d.origine ? ORIGINES[d.origine].couleur : SANS_ORIGINE.couleur);

/* LES BULLES DES CINQ SECTIONS (23/10/2026) : textes écrits ou repris mot pour
 * mot par la propriétaire, rendus dans leur bulle avant d'être codés, et
 * recopiés dans `tests/test_bulles_fiche_legislature.py`. Une législature en
 * cours dit la date de sa dernière mise à jour au lieu de son dernier jour.
 * Chacune renvoie à sa section de la méthodologie (famille « Fiche de
 * législature », rédigée par la propriétaire le 23/10/2026). */
const LIRE_LA_METHODE = 'Lire la méthode →';
const BULLES = {
  enBref: (enCours) => ({
    phrase: 'La législature en quelques faits.',
    note: enCours
      ? 'Note : Chiffres arrêtés à la date de la dernière mise à jour des données. Sont comptées les lois votées par l’Assemblée de cette législature, puis promulguées.'
      : 'Note : Chiffres arrêtés au dernier jour de la législature. Sont comptées les lois votées par l’Assemblée de cette législature, puis promulguées.',
    liens: [{ libelle: LIRE_LA_METHODE, vers: '/methodologie#leg-bref' }],
  }),
  sieges: (enCours) => ({
    phrase: 'La composition de l’Assemblée, groupe par groupe, et leur position : majorité, minoritaire ou opposition.',
    note: enCours
      ? 'Note : Situation à la date de la dernière mise à jour des données. L’Assemblée ne publie pas les positions pour la législature en cours.'
      : 'Note : Situation au dernier jour de la législature.',
    liens: [{ libelle: LIRE_LA_METHODE, vers: '/methodologie#leg-sieges' }],
  }),
  textes: () => ({
    phrase: 'Les textes votés par l’Assemblée pendant la législature, selon leur auteur, leur commission et leur sort.',
    note: 'Note : Un texte adopté n’est pas forcément devenu une loi. Une résolution, par exemple, ne le devient jamais.',
    liens: [{ libelle: LIRE_LA_METHODE, vers: '/methodologie#leg-textes' }],
  }),
  commissions: () => ({
    phrase: 'Les textes confiés à chaque commission pendant la législature, et leur avancée.',
    note: 'Note : Un texte jamais examiné n’est pas un texte rejeté : il n’a simplement jamais été mis à l’ordre du jour. Le nuage reprend les mots les plus fréquents dans les titres des textes.',
    liens: [{ libelle: LIRE_LA_METHODE, vers: '/methodologie#leg-commissions' }],
  }),
  limites: () => ({
    phrase: 'Les limites de cette fiche : ce que les sources ne disent pas sur cette législature.',
    note: 'Note : Une information absente de cette fiche n’a pas été trouvée dans les sources. Cela ne veut pas dire qu’il ne s’est rien passé.',
    liens: [{ libelle: LIRE_LA_METHODE, vers: '/methodologie#couverture' }],
  }),
};

function Section({ numero, titre, id, bulle = null, children }) {
  return (
    <section className="gvp-section" data-section={titre} id={id}>
      <div className="gvp-section-tete">
        <span className="gvp-section-numero">{numero}</span>
        <span className="gvp-section-trait" />
      </div>
      <div className="gvp-section-titre-rang ib-ancre">
        <h2 className="gvp-section-titre"><span>{titre}</span></h2>
        {bulle && <InfoBulle sujet={titre} {...bulle} />}
      </div>
      {children}
    </section>
  );
}

/* ── 01 En bref ──────────────────────────────────────────────────────────── */

/* Les gouvernements de la frise se rangent sur autant de rangées qu'il le faut
 * pour que deux noms ne se chevauchent pas (XVIIe : Barnier et Lecornu I ne
 * durent que quelques mois). Mesuré à l'écran, refait quand la largeur change. */
const RANG = 40;
function useRangees(cles) {
  const ref = useRef(null);
  const [rangs, setRangs] = useState([]);
  useLayoutEffect(() => {
    const zone = ref.current;
    if (!zone) return undefined;
    const ranger = () => {
      const g = zone.getBoundingClientRect().left, fins = [];
      setRangs([...zone.children].map((e) => {
        const r = e.getBoundingClientRect();
        let k = 0;
        while (fins[k] != null && fins[k] > r.left - g - 6) k += 1;
        /* une étiquette alignée à droite occupe la place à gauche de son repère */
        fins[k] = r.right - g;
        return k;
      }));
    };
    ranger();
    if (typeof ResizeObserver === 'undefined') return undefined;
    const ro = new ResizeObserver(ranger);
    ro.observe(zone);
    return () => ro.disconnect();
  }, [cles]);
  return [ref, rangs];
}

function EnBref({ vue }) {
  const { periode, termePrevu, gouvernements, comptes } = vue;
  /* UNE LÉGISLATURE EN COURS (XVIIe, forme C arbitrée le 23/10/2026) : la frise
   * court jusqu'au terme légal, pleine jusqu'à aujourd'hui, marqué en jaune
   * comme la station d'aujourd'hui sur l'accueil ; la suite reste vide. */
  const enCours = !periode?.fin;
  const aujourdhui = new Date().toISOString().slice(0, 10);
  const fin = periode?.fin || (periode?.debut ? aujourdhui : null);
  const [zoneGov, rangs] = useRangees(gouvernements.map((g) => g.id).join('|'));
  const nRangs = Math.max(1, ...rangs.map((k) => k + 1));
  const terme = termePrevu?.date ?? null;
  const borne = terme && fin && terme > fin ? terme : fin;
  const part = (d) => (periode?.debut && borne ? ((Date.parse(d) - Date.parse(periode.debut)) / (Date.parse(borne) - Date.parse(periode.debut))) * 100 : 0);
  const duree = dureeEnClair(periode?.debut, fin);
  const annees = [];
  if (periode?.debut && borne) for (let a = Number(periode.debut.slice(0, 4)); a <= Number(borne.slice(0, 4)); a += 1) annees.push(a);
  const chiffres = [
    [gouvernements.length, gouvernements.length > 1 ? 'gouvernements' : 'gouvernement'],
    [vue.sieges, 'députés'],
    [comptes.lois, comptes.lois > 1 ? 'lois' : 'loi'],
    [comptes.solennels, 'votes solennels'],
    [comptes.article493, 'textes adoptés par 49.3, sans vote', 'proc'],
    [comptes.motions, 'motions de censure'],
  ].filter(([n]) => n != null);
  return (
    <Section id="section-bref" numero="01" titre="En bref" bulle={BULLES.enBref(enCours)}>
      <div className="gvp-carte lgp-bref">
        {periode?.debut && fin && (
          <div className="lgp-frise">
            <div className="lgp-frise-gov" ref={zoneGov} style={{ height: nRangs * RANG - 2 }}>
              {gouvernements.map((g, i) => {
                const d0 = g.debut < periode.debut ? periode.debut : g.debut;
                const d1 = !g.fin || g.fin > fin ? fin : g.fin;
                return (
                  <div className={`lgp-frise-g${part(d0) > 80 ? ' lgp-frise-g--droite' : ''}`} key={g.id} style={{ ...(part(d0) > 80 ? { right: `${100 - part(d0)}%` } : { left: `${part(d0)}%` }), top: (rangs[i] || 0) * RANG, height: (nRangs - (rangs[i] || 0)) * RANG - 2, zIndex: 1 + (rangs[i] || 0) }}>
                    <b>{g.title.replace(/^Gouvernement\s+/, '')}</b>
                    {dureeEnClair(d0, d1).join(' ')}
                  </div>
                );
              })}
            </div>
            <div className="lgp-frise-barre">
              <div className="lgp-frise-plein" style={{ width: `${part(fin)}%` }}>{duree.join(' ')}</div>
              {terme && terme > fin && (
                <>
                  <div className={`lgp-frise-coupe${enCours ? ' lgp-frise-coupe--auj' : ''}`} style={{ left: `calc(${part(fin)}% - ${enCours ? 2 : 1}px)` }} />
                  <div className="lgp-frise-reste" style={{ left: `${part(fin)}%` }}>
                    {!enCours && <>{vue.fin?.mode === 'dissolution' ? 'dissolution · ' : ''}le mandat devait courir jusqu’en {MOIS[Number(terme.slice(5, 7)) - 1]} {terme.slice(0, 4)}</>}
                  </div>
                </>
              )}
            </div>
            <div className={`lgp-frise-ax${enCours ? ' lgp-frise-ax--auj' : ''}`}>
              {annees.map((a, i) => (
                <span
                  key={a}
                  style={{
                    left: `${Math.max(0, Math.min(100, part(`${a}${periode.debut.slice(4)}`)))}%`,
                    ...(i === 0 ? { transform: 'none' } : i === annees.length - 1 ? { transform: 'translateX(-100%)' } : {}),
                  }}
                >{a}</span>
              ))}
              {enCours && <span className="lgp-frise-auj" style={{ left: `${part(fin)}%` }}>aujourd’hui</span>}
            </div>
          </div>
        )}
        <div className="lgp-chiffres">
          {chiffres.map(([n, libelle, proc]) => (
            <div className={`lgp-chiffre${proc ? ' lgp-chiffre--proc' : ''}`} key={libelle}>
              <b>{formatNumber(n)}</b>
              <span>{libelle}</span>
            </div>
          ))}
        </div>
      </div>
    </Section>
  );
}

/* ── 02 Qui siégeait ─────────────────────────────────────────────────────── */

const POSITIONS = {
  majorite: { libelle: 'Majorité', couleur: '#803060' },
  minoritaire: { libelle: 'Minoritaire', couleur: '#D9B3C8' },
  opposition: { libelle: 'Opposition', couleur: '#14151A' },
  non_inscrit: { libelle: 'Non-inscrits', couleur: '#B8B4AE' },
};
const HORS_GROUPE = '#E4E1DC';
/* SANS AUCUNE POSITION PUBLIÉE (XVIIe, arbitré le 23/10/2026, forme B) : les
 * groupes se distinguent par deux tons d'encre alternés, ceux de l'hémicycle de
 * l'accueil ; ni arc de position, ni couleur de position en légende, puisque
 * l'Assemblée n'en publie aucune. Les non-inscrits gardent leur gris. */
const TONS_SANS_POSITION = ['#3B3940', '#8B8794'];
const COLOREES = new Set(['majorite', 'minoritaire', 'opposition']);
const sansPosition = (groupes) => !groupes.some((g) => COLOREES.has(g.position));

/* SUR TÉLÉPHONE (23/10/2026), l'hémicycle se réduit au quart : ses sigles de 25
 * unités tombaient à 6 px. Ils grossissent et s'écartent des sièges ; le nombre
 * des groupes de moins de 30 députés et tout sigle qui chevaucherait son voisin
 * restent dans la bulle des sièges ; les arcs gardent leur couleur, sans
 * libellé, que la légende dit déjà. */
const TAILLES = {
  large: { sigle: 25, n: 22, dy: 23, ecart: 54, total: 44, sous: 24 },
  etroit: { sigle: 46, n: 38, dy: 42, ecart: 92, total: 68, sous: 36 },
};

function Hemicycle({ groupes, sieges, neutre = false }) {
  const etroit = useEcranEtroit();
  const T = etroit ? TAILLES.etroit : TAILLES.large;
  const total = sieges ?? groupes.reduce((s, g) => s + (g.effectif || 0), 0);
  const { points, sigles, arcs } = useMemo(() => {
    const R = 12, r0 = 180, r1 = 440, cx = 500, cy = 500;
    const rayons = [...Array(R)].map((_, i) => r0 + ((r1 - r0) * i) / (R - 1));
    const somme = rayons.reduce((s, r) => s + r, 0);
    const parRang = rayons.map((r) => Math.round((total * r) / somme));
    parRang[R - 1] += total - parRang.reduce((s, n) => s + n, 0);
    const places = [];
    rayons.forEach((r, i) => {
      const n = parRang[i];
      for (let k = 0; k < n; k += 1) {
        const a = Math.PI * (1 - k / Math.max(1, n - 1));
        places.push({ a, x: cx + r * Math.cos(a), y: cy - r * Math.sin(a) });
      }
    });
    places.sort((p, q) => q.a - p.a);
    const seq = [];
    let alterne = 0, ton = 0;
    groupes.forEach((g, gi) => {
      let c = POSITIONS[g.position]?.couleur || HORS_GROUPE;
      if (neutre && g.position !== 'non_inscrit') { c = TONS_SANS_POSITION[ton % 2]; ton += 1; }
      // Deux tons d'encre séparent les groupes d'opposition voisins (21/10).
      if (g.position === 'opposition') { c = alterne % 2 ? '#6E6A75' : '#14151A'; alterne += 1; }
      for (let i = 0; i < (g.effectif || 0); i += 1) seq.push({ c, g: gi, titre: g.nom });
    });
    while (seq.length < total) seq.push({ c: HORS_GROUPE, g: -1, titre: 'Hors groupe ou siège vacant' });
    const angle = (gi) => {
      const idx = seq.map((s, i) => (s.g === gi ? i : -1)).filter((i) => i >= 0);
      return idx.length ? { a0: Math.max(...idx.map((i) => places[i].a)), a1: Math.min(...idx.map((i) => places[i].a)), m: idx.reduce((s, i) => s + places[i].a, 0) / idx.length } : null;
    };
    const runs = [];
    groupes.forEach((g, gi) => {
      const an = angle(gi);
      if (!an) return;
      const dernier = runs[runs.length - 1];
      if (dernier && dernier.p === g.position) { dernier.a1 = an.a1; dernier.n += g.effectif || 0; } else runs.push({ p: g.position, a0: an.a0, a1: an.a1, n: g.effectif || 0 });
    });
    return {
      points: places.map((p, i) => ({ ...p, ...seq[i], r: ((r1 - r0) / (R - 1)) * 0.42 })),
      sigles: groupes.map((g, gi) => ({ s: g.sigle, nom: g.nom, n: g.effectif, a: angle(gi)?.m })).filter((s) => s.a != null),
      arcs: runs,
      geo: { cx, cy, r1 },
    };
  }, [groupes, total, neutre]);
  const cx = 500, cy = 500, r1 = 440;
  /* Les étiquettes posées ; sur téléphone, une étiquette qui chevaucherait la
   * précédente n'est pas posée. */
  const etiquettes = [];
  /* Les plus grands groupes se posent d'abord : en cas de chevauchement, c'est le
   * sigle du plus petit qui reste dans la bulle. L'ordre d'affichage reste celui
   * des sièges. */
  [...sigles].sort((a, b) => (etroit ? b.n - a.n : 0)).forEach((g) => {
    const x = cx + (r1 + T.ecart) * Math.cos(g.a), y = cy - (r1 + T.ecart) * Math.sin(g.a) - 8;
    const avecN = !(etroit && g.n < 30);
    const l = g.s.length * T.sigle * 0.64, h = T.sigle + (avecN ? T.dy : 0);
    const b = { x0: x - l / 2, x1: x + l / 2, y0: y - T.sigle, y1: y - T.sigle + h + 4 };
    if (etroit && etiquettes.some((e) => b.x0 < e.b.x1 && b.x1 > e.b.x0 && b.y0 < e.b.y1 && b.y1 > e.b.y0)) return;
    etiquettes.push({ ...g, x, y, avecN, b });
  });
  const arc = (r, a0, a1) => `M${(cx + r * Math.cos(a0)).toFixed(1)},${(cy - r * Math.sin(a0)).toFixed(1)} A${r},${r} 0 0 1 ${(cx + r * Math.cos(a1)).toFixed(1)},${(cy - r * Math.sin(a1)).toFixed(1)}`;
  return (
    <svg className="lgp-hemi" role="img" aria-label={`Hémicycle : ${total} députés`} viewBox="-250 -90 1500 630">
      {!neutre && arcs.map((u) => {
        const rr = r1 + (etroit ? 30 : 104), m = (u.a0 + u.a1) / 2, cm = Math.cos(m);
        const anc = cm < -0.25 ? 'end' : cm > 0.25 ? 'start' : 'middle';
        return (
          <Fragment key={`${u.p}-${u.a0}`}>
            <path d={arc(rr, u.a0 + 0.004, u.a1 - 0.004)} fill="none" stroke={POSITIONS[u.p]?.couleur || '#9A958D'} strokeWidth="7" />
            {!etroit && <text className="lgp-hemi-arc" dominantBaseline="middle" textAnchor={anc} x={cx + (rr + 14) * cm} y={cy - (rr + 14) * Math.sin(m)}>
              {`${POSITIONS[u.p]?.libelle || 'Position non publiée'} · ${u.n}`}
            </text>}
          </Fragment>
        );
      })}
      {points.map((p, i) => (
        <circle cx={p.x} cy={p.y} fill={p.c} key={i} r={p.r} stroke={p.g < 0 ? '#9A958D' : 'none'}>
          <title>{p.titre}</title>
        </circle>
      ))}
      {/* Le sigle porte son compte de députés, et son nom complet au survol : la
          liste sous la figure, qui les redisait, est retirée (22/10/2026). */}
      {etiquettes.map((s) => (
        <text className="lgp-hemi-sigle" key={s.s} style={{ fontSize: T.sigle }} textAnchor="middle" x={s.x} y={s.y}>
          <title>{`${s.nom} : ${formatNumber(s.n)} député${s.n > 1 ? 's' : ''}`}</title>
          {s.s}
          {s.avecN && <tspan className="lgp-hemi-sigle-n" dy={T.dy} style={{ fontSize: T.n }} x={s.x}>{formatNumber(s.n)}</tspan>}
        </text>
      ))}
      <text className="lgp-hemi-total" style={{ fontSize: T.total }} textAnchor="middle" x="500" y={etroit ? 455 : 470}>{total}</text>
      <text className="lgp-hemi-sous" style={{ fontSize: T.sous }} textAnchor="middle" x="500" y={etroit ? 500 : 504}>députés</text>
    </svg>
  );
}

function QuiSiegeait({ vue }) {
  const { groupes } = vue;
  if (!groupes.length) return null;
  const total = vue.sieges ?? groupes.reduce((s, g) => s + (g.effectif || 0), 0);
  const hors = total - groupes.reduce((s, g) => s + (g.effectif || 0), 0);
  const neutre = sansPosition(groupes);
  /* Un groupe sans position publiée (XVe : 19 députés) est dessiné en gris clair ;
   * la légende le nomme avec les mots de son arc, sans quoi le gris ne se lit
   * pas — et sur téléphone l'arc n'a plus de libellé. */
  const sansPositionPubliee = groupes.some((g) => g.position !== 'non_inscrit' && !POSITIONS[g.position]);
  const legende = neutre
    ? (groupes.some((g) => g.position === 'non_inscrit') ? [POSITIONS.non_inscrit] : [])
    : [...Object.values(POSITIONS), ...(sansPositionPubliee ? [{ libelle: 'Position non publiée', couleur: HORS_GROUPE }] : [])];
  return (
    <Section id="section-sieges" numero="02" titre={vue.periode.fin ? 'Qui siégeait' : 'Qui siège'} bulle={BULLES.sieges(!vue.periode.fin)}>
      <div className="gvp-carte">
        <div className="lgp-legende">
          {legende.map((p) => <span key={p.libelle}><i style={{ background: p.couleur }} />{p.libelle}</span>)}
          {hors > 0 && <span><i style={{ background: HORS_GROUPE }} />Hors groupe ou siège vacant</span>}
        </div>
        <Hemicycle groupes={groupes} sieges={vue.sieges} neutre={neutre} />
      </div>
    </Section>
  );
}

/* ── 03 Les textes de la législature ─────────────────────────────────────── */

function qui(d) {
  const p = d.initiateurs[0];
  if (!p) return 'Initiateur non renseigné';
  const s = `${p.nom}, ${p.fonction}${p.groupe ? `, ${p.groupe}` : ''}`;
  const n = d.initiateurs.length - 1;
  return n > 0 ? `${s}, et ${n} autre${n > 1 ? 's' : ''}` : s;
}
function quand(d) {
  const t = [];
  if (d.depot) t.push(`déposé le ${jour(d.depot)}`);
  if (d.promulgation) t.push(`promulgué le ${jour(d.promulgation)}`);
  const s = t.join(' · ');
  return s ? s[0].toUpperCase() + s.slice(1) : '';
}

function LigneTexte({ d }) {
  return (
    <li>
      <i className={d.article493 ? 'lgp-pastille-493' : undefined} style={d.article493 ? undefined : { background: couleurOrigine(d) }} />
      <span>
        <span className={d.solennel || d.article493 ? 'lgp-fort' : undefined}>
          {d.titre || 'Titre non publié'}
          {d.article493 && <b className="lgp-mention"> · adopté par 49.3</b>}
          {d.solennel && <b className="lgp-mention"> · vote solennel</b>}
        </span>
        <small className="lgp-qui">
          {qui(d)}{quand(d) ? ` · ${quand(d)}` : ''} · <a href={d.url} rel="noopener noreferrer" target="_blank">le dossier à l’Assemblée ›</a>
        </small>
      </span>
    </li>
  );
}

function Detail({ titre, sousTitre, onFermer, children }) {
  return (
    <div className="lgp-detail">
      <button aria-label="Fermer" className="lgp-fermer" onClick={onFermer} type="button">×</button>
      <h4>{titre}{sousTitre && <span>{sousTitre}</span>}</h4>
      {children}
    </div>
  );
}

function Bibliotheque({ vue }) {
  const [ouvert, setOuvert] = useState(null);
  const ordreOrigine = ['gouvernement', 'deputes', 'senateurs', null];
  /* LES COMMISSIONS SPÉCIALES TIENNENT UNE SEULE RANGÉE (23/10/2026) : chacune
   * n'examine qu'un ou deux textes, et une rangée par commission allongeait la
   * section de rangées presque vides. Même nom que dans « Le travail des
   * commissions ». */
  const tous = vue.dossiers.filter((d) => SORTS.some((s) => s.cle === d.sort));
  const nbSpeciales = new Set(tous.filter((d) => d.commissionSpeciale).map((d) => d.commission)).size;
  const textes = tous.map((d) => (d.commissionSpeciale ? { ...d, domaine: `Commissions spéciales (${nbSpeciales})` } : d));
  const domaines = [...new Set(textes.map((d) => d.domaine))]
    .sort((a, b) => (a === 'Domaine non renseigné') - (b === 'Domaine non renseigné') || a.localeCompare(b, 'fr'));
  const cellule = (dom, sort) => textes.filter((d) => d.domaine === dom && d.sort === sort)
    .sort((a, b) => (b.solennel - a.solennel) || ordreOrigine.indexOf(a.origine) - ordreOrigine.indexOf(b.origine));
  const basculer = (cle) => setOuvert((o) => (o?.cle === cle.cle ? null : cle));
  if (!textes.length) return null;
  return (
    <Section id="section-textes" numero="03" titre="Les textes de la législature" bulle={BULLES.textes()}>
      <div className="gvp-carte">
        <div className="lgp-legende">
          {Object.values(ORIGINES).map((o) => <span key={o.libelle}><i style={{ background: o.couleur }} />{o.libelle}</span>)}
          {textes.some((d) => !d.origine) && <span><i style={{ background: SANS_ORIGINE.couleur }} />{SANS_ORIGINE.libelle}</span>}
          <span><i className="lgp-hach" />adopté par 49.3, sans vote</span>
          <span className="lgp-leg-livres"><span aria-hidden="true" className="lgp-mini"><i /><i className="epais" /><i /></span>livre épais : passé par un vote solennel</span>
        </div>
        <div className="lgp-meubles-defile">
          <div className="lgp-meubles">
            <div />
            {SORTS.map((s) => (
              <div className="lgp-meuble-tete" key={s.cle}>{s.libelle}<b>{formatNumber(textes.filter((d) => d.sort === s.cle).length)}</b></div>
            ))}
            {domaines.map((dom) => (
              <Fragment key={dom}>
                <button className={`lgp-domaine${ouvert?.cle === `dom|${dom}` ? ' lgp-sel' : ''}`} onClick={() => basculer({ cle: `dom|${dom}`, dom })} type="button">{dom}</button>
                {SORTS.map((s) => {
                  const L = cellule(dom, s.cle);
                  return (
                    <div
                      className={`lgp-case${ouvert?.cle === `case|${dom}|${s.cle}` ? ' lgp-sel' : ''}`}
                      key={s.cle}
                      onClick={() => basculer({ cle: `case|${dom}|${s.cle}`, dom, sort: s.cle })}
                      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); basculer({ cle: `case|${dom}|${s.cle}`, dom, sort: s.cle }); } }}
                      role="button"
                      tabIndex={0}
                      title={`${dom} · ${s.libelle} · ${L.length}`}
                    >
                      {L.map((d) => (
                        <button
                          aria-label={d.titre || 'Titre non publié'}
                          className={`lgp-livre${d.solennel ? ' lgp-livre--epais' : ''}${ouvert?.cle === `livre|${d.id}` ? ' lgp-sel' : ''}`}
                          key={d.id}
                          onClick={(e) => { e.stopPropagation(); basculer({ cle: `livre|${d.id}`, dom, livre: d }); }}
                          style={{ background: d.article493 ? undefined : couleurOrigine(d) }}
                          title={d.titre || ''}
                          type="button"
                          {...(d.article493 ? { 'data-493': '' } : {})}
                        />
                      ))}
                    </div>
                  );
                })}
                {ouvert?.dom === dom && (
                  <div className="lgp-detail-rang">
                    <Detail
                      onFermer={() => setOuvert(null)}
                      sousTitre={ouvert.livre ? SORTS.find((s) => s.cle === ouvert.livre.sort)?.singulier
                        : ouvert.sort ? SORTS.find((s) => s.cle === ouvert.sort)?.libelle : null}
                      titre={dom}
                    >
                      {ouvert.livre && <ul className="lgp-liste lgp-liste--un"><LigneTexte d={ouvert.livre} /></ul>}
                      {ouvert.sort && <ul className="lgp-liste">{cellule(dom, ouvert.sort).map((d) => <LigneTexte d={d} key={d.id} />)}</ul>}
                      {!ouvert.livre && !ouvert.sort && SORTS.map((s) => {
                        const L = cellule(dom, s.cle);
                        return L.length ? (
                          <Fragment key={s.cle}>
                            <h5>{s.libelle} · {L.length}</h5>
                            <ul className="lgp-liste">{L.map((d) => <LigneTexte d={d} key={d.id} />)}</ul>
                          </Fragment>
                        ) : null;
                      })}
                    </Detail>
                  </div>
                )}
              </Fragment>
            ))}
          </div>
        </div>
      </div>
    </Section>
  );
}

/* ── 04 Le travail des commissions ───────────────────────────────────────── */

const SEUIL_NUAGE = 10; // arbitré le 22/10 : sous 10 textes, la liste remplace le nuage

function ListeParEtape({ textes }) {
  return (
    <div className="lgp-par-etape">
      {[...ETAPES].reverse().map((e) => {
        const G = textes.filter((d) => d.etape === e.cle);
        return G.length ? (
          <div key={e.cle}>
            <h6>{e.pluriel} · {G.length}</h6>
            <ul className="lgp-liste-courte">
              {G.map((d) => (
                <li key={d.id}>
                  <a href={d.url} rel="noopener noreferrer" target="_blank">{d.titre || 'Titre non publié'}</a>
                  {d.depot && <small>Déposé le {jour(d.depot)}</small>}
                </li>
              ))}
            </ul>
          </div>
        ) : null;
      })}
    </div>
  );
}

function Commissions({ vue }) {
  const { dossiers, transversaux } = useMemo(() => motsDesTitres(vue.dossiers.filter((d) => d.commission && d.legislature === String(vue.id))), [vue]);
  const [filtre, setFiltre] = useState(null);
  const [mot, setMot] = useState(null);
  /* Mémorisé : le nuage ne se redispose que si le filtre change, pas à chaque mot cliqué. */
  const { T, mots, enListe } = useMemo(() => {
    const T = filtre ? dossiers.filter((d) => filtre.cs.includes(d.commission) && (!filtre.etape || d.etape === filtre.etape)) : dossiers;
    const ecartes = filtre ? new Set() : transversaux;
    const compte = new Map();
    T.forEach((d) => d.mots.forEach((w) => { if (!ecartes.has(w)) compte.set(w, (compte.get(w) || 0) + 1); }));
    const maxMot = Math.max(0, ...compte.values());
    let mots = [...compte].sort((a, b) => b[1] - a[1]);
    mots = T.length >= 30 ? mots.filter(([, n]) => n >= 2).slice(0, filtre ? 70 : 90) : mots.slice(0, 70);
    return { T, mots, enListe: T.length < SEUIL_NUAGE || maxMot < 2 };
  }, [dossiers, transversaux, filtre]);
  if (!dossiers.length) return null;
  const permanentes = [...new Set(dossiers.filter((d) => !d.commissionSpeciale).map((d) => d.commission))].sort((a, b) => a.localeCompare(b, 'fr'));
  const speciales = [...new Set(dossiers.filter((d) => d.commissionSpeciale).map((d) => d.commission))];
  const rangs = [
    ...permanentes.map((c) => ({ libelle: c, cs: [c] })),
    ...(speciales.length ? [{ libelle: `Commissions spéciales (${speciales.length})`, cs: speciales }] : []),
  ].map((r) => {
    const T = dossiers.filter((d) => r.cs.includes(d.commission));
    return { ...r, n: T.length, par: Object.fromEntries(ETAPES.map((e) => [e.cle, T.filter((d) => d.etape === e.cle).length])) };
  });
  const max = Math.max(...rangs.map((r) => r.n));
  const choisir = (f) => {
    setMot(null);
    setFiltre((cur) => (cur && f && cur.libelle === f.libelle && cur.etape === f.etape ? null : f));
  };
  const etapeLib = (k) => ETAPES.find((e) => e.cle === k)?.pluriel;
  return (
    <Section id="section-commissions" numero="04" titre="Le travail des commissions" bulle={BULLES.commissions()}>
      <div className="gvp-carte">
        <div className="lgp-legende">
          {ETAPES.map((e) => <span key={e.cle}><i style={{ background: e.couleur }} />{e.libelle}</span>)}
        </div>
        <div className="lgp-b1">
          {rangs.map((r) => (
            <div className={`lgp-b1-rang${filtre?.libelle === r.libelle ? ' lgp-sel' : ''}`} key={r.libelle}>
              <button className="lgp-b1-nom" onClick={() => choisir({ libelle: r.libelle, cs: r.cs, etape: null })} type="button">{r.libelle}</button>
              <span className="lgp-b1-barre">
                <span className="lgp-b1-in" style={{ width: `${((r.n / max) * 100).toFixed(1)}%` }}>
                  {ETAPES.map((e) => (r.par[e.cle] ? (
                    <button
                      className={`lgp-b1-seg${filtre?.libelle === r.libelle && filtre?.etape === e.cle ? ' lgp-sel' : ''}`}
                      key={e.cle}
                      onClick={() => choisir({ libelle: r.libelle, cs: r.cs, etape: e.cle })}
                      style={{ flex: r.par[e.cle], background: e.couleur, color: e.cle === 'jamais' ? '#14151A' : '#fff' }}
                      title={`${e.libelle} : ${r.par[e.cle]}`}
                      type="button"
                    >
                      {r.par[e.cle] >= 8 ? r.par[e.cle] : ''}
                    </button>
                  ) : null))}
                </span>
                <b>{formatNumber(r.n)}</b>
              </span>
            </div>
          ))}
        </div>
        <div className="lgp-nuage">
          <h4>
            {filtre ? filtre.libelle : 'Tous les textes renvoyés aux commissions'}
            <span>{filtre?.etape ? `${etapeLib(filtre.etape)} · ` : ''}{formatNumber(T.length)} texte{T.length > 1 ? 's' : ''}</span>
            {filtre && <button className="lgp-tout" onClick={() => choisir(null)} type="button">Tous les textes ›</button>}
          </h4>
          {enListe ? <ListeParEtape textes={T} /> : (
            <>
              <NuageDeMots actif={mot} mots={mots} onMot={(w) => setMot((m) => (m === w ? null : w))} />
              {mot && (
                <div className="lgp-nuage-textes">
                  <h5>Le mot « {mot} » · {T.filter((d) => d.mots.includes(mot)).length} textes</h5>
                  <ListeParEtape textes={T.filter((d) => d.mots.includes(mot))} />
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </Section>
  );
}

/* ── 05 Ce qu'on n'a pas pu lire ─────────────────────────────────────────── */

function CeQuOnNaPasPuLire() {
  const lignes = [
    ['Le Sénat', 'Seule l’Assemblée nationale est couverte.'],
    ['Les commissions', 'Les comptes rendus, les auditions et les rapports d’information ne sont pas lus.'],
    ['Les missions d’information', 'Leur rattachement à une commission est en cours de collecte.'],
  ];
  return (
    <Section id="section-limites" numero="05" titre="Ce qu’on n’a pas pu lire" bulle={BULLES.limites()}>
      <div className="gvp-carte">
        <dl className="gvp-limites">
          {lignes.map(([quoi, texte]) => (
            <div className="gvp-limite" key={quoi}><dt>{quoi}</dt><dd>{texte}</dd></div>
          ))}
        </dl>
      </div>
    </Section>
  );
}

/* ── La fiche ────────────────────────────────────────────────────────────── */

export default function LegislatureProfile({ vue }) {
  const { periode } = vue;
  return (
    <main className="gvp-main">
      <div className="gvp-breadcrumb">Législature / <strong>{vue.nom}</strong></div>
      <header className="gvp-entete">
        <h1>{vue.nom}</h1>
        {periode?.debut && (
          <p className="gvp-qui">
            {periode.fin ? `Du ${jour(periode.debut)} au ${jour(periode.fin)}` : `Depuis le ${jour(periode.debut)}`}
            {vue.fin?.mode === 'dissolution' ? ' · close par la dissolution' : ''}
          </p>
        )}
      </header>
      <EnBref vue={vue} />
      <QuiSiegeait vue={vue} />
      <Bibliotheque vue={vue} />
      <Commissions vue={vue} />
      <CeQuOnNaPasPuLire />
    </main>
  );
}
