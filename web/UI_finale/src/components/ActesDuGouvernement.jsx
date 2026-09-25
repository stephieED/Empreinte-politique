import { useEffect, useMemo, useState } from 'react';
import { getActesDuGouvernement } from '../data';
import './ActesDuGouvernement.css';

/* ── CE QUE L'EXÉCUTIF A FAIT ENTRER EN VIGUEUR (#1029 voie 1) ────────────────
 *
 * Arbitré en maquette avec la propriétaire les 24 et 25/09/2026 :
 * https://claude.ai/artifact/GXrJZv1umqSGbEgQgwrc4r
 *
 * CE QUE LA SECTION MONTRE, et dans cet ordre : combien d'actes ont paru
 * pendant le gouvernement, combien sont des actes de personne — donc retirés —,
 * puis, sur ce qui touche au droit, quel ministère signe et ce que le TITRE
 * déclare d'une loi. Deux filtres règlent à la fois le flux et le détail.
 *
 * TROIS CHOSES QU'AUCUNE FORMULE D'ICI NE DOIT LAISSER CROIRE.
 *
 *   « Le titre ne le dit pas » N'EST PAS « sans loi ». La qualification
 *   structurée de Légifrance n'est plus posée — un acte sur toute l'année de
 *   Lecornu II la porte — et son absence ne dit rien de l'acte (§2 règle 5).
 *   → `docs/decisions/part-d-application-non-publiable-1029.md`
 *
 *   Le DÉLAI d'une loi est celui de son premier acte DE CETTE PÉRIODE, jamais
 *   « du premier acte jamais pris » : une loi ancienne a pu en recevoir avant.
 *
 *   Les actes qui nomment une loi se CONCENTRENT. Sur Lecornu II, 308 des 395
 *   nomment la même — la loi de financement de la sécurité sociale pour 2007,
 *   par des arrêtés fixant la liste des praticiens autorisés à exercer. Lire
 *   « 395 actes appliquent une loi » comme 395 mesures serait faux, et la
 *   section le dit en clair.
 *
 * DESSINÉ À LA MAIN, sans librairie : deux colonnes, une douzaine de rubans.
 * Charger ECharts pour cela pèserait plus que toute la fiche.
 */

const LIE = 'lié à une loi';
const MUET = 'le titre ne le dit pas';
const AUTRES = 'Autres ministères';
/* Cinq teintes, et pas six : à huit, deux paires tombent sous le seuil de
   séparation, y compris en vision normale (validateur de palette, 25/09/2026).
   Le sixième bloc n'est donc pas une couleur de plus, c'est un regroupement. */
const PALETTE = ['#2B5EA8', '#C2621B', '#8A45A3', '#1F7A4D', '#C0459B'];
const GRIS = '#9A958D';
const TOP = 5;

const nombre = (n) => (n ?? 0).toLocaleString('fr-FR');
const enJours = (n) => {
  if (n === undefined || n === null) return '';
  if (n < 90) return `${n} jours`;
  const mois = Math.round(n / 30.44);
  return mois < 24 ? `${mois} mois` : `${(n / 365.25).toFixed(1).replace('.', ',')} ans`;
};
const enClair = (iso) => (iso ? iso.split('-').reverse().join('/') : '');

export default function ActesDuGouvernement({ id }) {
  const [donnees, setDonnees] = useState(null);
  const [erreur, setErreur] = useState(false);
  const [lien, setLien] = useState(null);
  const [ministere, setMinistere] = useState(null);

  useEffect(() => {
    let vivant = true;
    setDonnees(null);
    setErreur(false);
    getActesDuGouvernement(id)
      .then((d) => { if (vivant) setDonnees(d); })
      .catch(() => { if (vivant) setErreur(true); });
    return () => { vivant = false; };
  }, [id]);

  const modele = useMemo(() => {
    if (!donnees) return null;
    const mins = Object.keys(donnees.ministeres || {}).slice(0, TOP);
    const couleur = Object.fromEntries(mins.map((m, i) => [m, PALETTE[i]]));
    couleur[AUTRES] = GRIS;
    const theme = (m) => (couleur[m] && m !== AUTRES ? m : AUTRES);
    const cat = (l) => (l === MUET ? MUET : LIE);
    const retenu = (c) => (!lien || cat(c.l) === lien) && (!ministere || theme(c.m) === ministere);
    const compte = (f) => (donnees.cellules || []).reduce((s, c) => (f(c) ? s + c.n : s), 0);
    const flux = new Map();
    (donnees.cellules || []).forEach((c) => {
      if (!retenu(c)) return;
      const cle = `${theme(c.m)}|${cat(c.l)}`;
      flux.set(cle, (flux.get(cle) || 0) + c.n);
    });
    return { mins, couleur, theme, cat, retenu, compte, flux, ordre: [...mins, AUTRES] };
  }, [donnees, lien, ministere]);

  if (erreur) {
    return <p className="adg-vide">Les actes du Journal officiel n’ont pas pu être chargés.</p>;
  }
  if (!donnees || !modele) {
    return <p className="adg-vide">Chargement des actes parus au Journal officiel…</p>;
  }
  if (!donnees.total) {
    return (
      <p className="adg-vide">
        Aucun acte du Journal officiel n’est rattaché à la période de ce gouvernement — le fonds
        collecté commence au 1<sup>er</sup> janvier 2007.
      </p>
    );
  }

  const { couleur, theme, cat, retenu, compte, flux, ordre } = modele;
  const actes = (donnees.cellules || []).filter(retenu);
  const lois = (donnees.lois || []).filter(
    (l) => !ministere || (l.actes || []).some((a) => theme(a.m) === ministere),
  );

  return (
    <div className="adg">
      <ol className="adg-entonnoir">
        <li><b>{nombre(donnees.tot)}</b><span>actes parus au Journal officiel pendant ce gouvernement</span></li>
        <li>
          <b>− {nombre(donnees.personnes)}</b>
          <span>actes de personne, rangés là par le Journal officiel lui‑même</span>
          {donnees.personnesParTitre > 0 && (
            <span className="adg-repli">
              dont {nombre(donnees.personnesParTitre)} d’après leur titre, le sommaire ne les rangeant pas
            </span>
          )}
        </li>
        <li className="adg-reste"><b>{nombre(donnees.total)}</b><span>actes qui touchent au droit — ceux du diagramme</span></li>
      </ol>

      <Flux flux={flux} ordre={ordre} couleur={couleur} />

      <div className="adg-filtres">
        <span className="adg-filtre-titre">Ce que le titre déclare d’une loi</span>
        <Bouton actif={!lien} libelle="Tous" n={compte(() => true)} action={() => setLien(null)} />
        <Bouton actif={lien === LIE} libelle={LIE} couleur="#803060"
          n={compte((c) => cat(c.l) === LIE && (!ministere || theme(c.m) === ministere))}
          action={() => setLien(LIE)} />
        <Bouton actif={lien === MUET} libelle={MUET} couleur={GRIS}
          n={compte((c) => c.l === MUET && (!ministere || theme(c.m) === ministere))}
          action={() => setLien(MUET)} />
        <span className="adg-filtre-titre">Ministère</span>
        <Bouton actif={!ministere} libelle="Tous"
          n={compte((c) => !lien || cat(c.l) === lien)} action={() => setMinistere(null)} />
        {ordre.map((m) => (
          <Bouton key={m} actif={ministere === m} libelle={m} couleur={couleur[m]}
            n={compte((c) => theme(c.m) === m && (!lien || cat(c.l) === lien))}
            action={() => setMinistere(m)} />
        ))}
      </div>

      {lien === LIE ? (
        <Lois lois={lois} ministere={ministere} />
      ) : lien || ministere ? (
        <Actes cellules={actes} exemples={donnees.exemples} couleur={couleur} theme={theme} />
      ) : null}

      <p className="adg-note">
        Les familles sont lues dans les <b>titres</b>, une seule par acte — c’est une aide à la
        lecture, pas une catégorie officielle. <b>« Le titre ne le dit pas » ne veut pas dire
        « sans loi »</b> : Légifrance ne pose presque plus la qualification d’application, et son
        absence ne dit rien de l’acte. Le <b>délai</b> d’une loi est celui de son premier acte
        <i> de cette période</i> : une loi ancienne a pu en recevoir avant.
      </p>
    </div>
  );
}

function Bouton({ actif, libelle, n, couleur, action }) {
  return (
    <button type="button" className={`adg-bouton${actif ? ' adg-bouton--actif' : ''}`}
      aria-pressed={actif} onClick={action}>
      {couleur ? <i style={{ background: couleur }} aria-hidden="true" /> : null}
      {libelle}
      <b>{nombre(n)}</b>
    </button>
  );
}

/* Le flux, dessiné à la main : les sources empilées à gauche, les deux
   destinations à droite, un ruban par couple. La hauteur d'un ruban EST son
   nombre d'actes — une seule échelle, jamais deux. */
function Flux({ flux, ordre, couleur }) {
  const H = 420;
  const L = 900;
  const ECART = 6;
  const total = [...flux.values()].reduce((s, n) => s + n, 0);
  if (!total) return null;
  const sources = ordre
    .map((m) => ({ nom: m, n: [LIE, MUET].reduce((s, d) => s + (flux.get(`${m}|${d}`) || 0), 0) }))
    .filter((s) => s.n > 0);
  const cibles = [LIE, MUET]
    .map((d) => ({ nom: d, n: ordre.reduce((s, m) => s + (flux.get(`${m}|${d}`) || 0), 0) }))
    .filter((c) => c.n > 0);
  const utile = (cote) => H - ECART * Math.max(0, cote.length - 1);
  const poser = (liste) => {
    const echelle = utile(liste) / total;
    let y = 0;
    return liste.map((e) => {
      const h = Math.max(2, e.n * echelle);
      const bloc = { ...e, y, h };
      y += h + ECART;
      return bloc;
    });
  };
  const gauche = poser(sources);
  const droite = poser(cibles);
  const curseurG = Object.fromEntries(gauche.map((g) => [g.nom, g.y]));
  const curseurD = Object.fromEntries(droite.map((d) => [d.nom, d.y]));
  const echelle = Math.min(utile(sources), utile(cibles)) / total;
  const rubans = [];
  gauche.forEach((g) => {
    [LIE, MUET].forEach((d) => {
      const n = flux.get(`${g.nom}|${d}`) || 0;
      if (!n) return;
      const h = Math.max(1.2, n * echelle);
      const y1 = curseurG[g.nom];
      const y2 = curseurD[d];
      curseurG[g.nom] += h;
      curseurD[d] += h;
      const x1 = 236;
      const x2 = L - 330;
      const m = (x1 + x2) / 2;
      rubans.push({
        cle: `${g.nom}|${d}`,
        couleur: couleur[g.nom],
        d: `M${x1},${y1} C${m},${y1} ${m},${y2} ${x2},${y2} L${x2},${y2 + h} C${m},${y2 + h} ${m},${y1 + h} ${x1},${y1 + h} Z`,
      });
    });
  });
  return (
    <div className="adg-cadre">
      <svg className="adg-flux" viewBox={`0 0 ${L} ${H + 8}`} role="img"
        aria-label="Les actes par ministère, puis par ce que leur titre déclare d’une loi">
        {rubans.map((r) => (
          <path key={r.cle} d={r.d} fill={r.couleur} opacity="0.42" />
        ))}
        {gauche.map((g) => (
          <g key={g.nom}>
            <rect x="222" y={g.y} width="14" height={g.h} fill={couleur[g.nom]} rx="2" />
            <text x="214" y={g.y + g.h / 2 + 4} textAnchor="end" className="adg-etiquette">
              {g.nom}<tspan className="adg-compte" dx="6">{nombre(g.n)}</tspan>
            </text>
          </g>
        ))}
        {droite.map((c) => (
          <g key={c.nom}>
            <rect x={L - 330} y={c.y} width="14" height={c.h} fill={c.nom === LIE ? '#803060' : GRIS} rx="2" />
            <text x={L - 308} y={c.y + c.h / 2 + 4} className="adg-etiquette">
              {c.nom}<tspan className="adg-compte" dx="6">{nombre(c.n)}</tspan>
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}

function Lois({ lois, ministere }) {
  const [ouverte, setOuverte] = useState(null);
  const nommees = lois.filter((l) => l.titre).length;
  const propositions = lois.filter((l) => (l.nature || '').startsWith('Proposition')).length;
  const concentration = lois[0] && lois[0].n > 1 ? lois[0] : null;
  return (
    <div className="adg-detail">
      <h3>{ministere ? `Les lois appliquées · ${ministere}` : 'Les lois que ce gouvernement a mises en application'}</h3>
      <p className="adg-sous">
        {lois.length} lois nommées par un acte, dont {nommees} retrouvées dans les textes
        promulgués et {propositions} nées d’une proposition de loi.
        {concentration ? (
          <> À elle seule, la première en compte <b>{nombre(concentration.n)}</b> : les actes
            qui nomment une loi se concentrent sur quelques régimes.</>
        ) : null}
      </p>
      {lois.map((l) => (
        <details key={l.num} className="adg-loi" open={ouverte === l.num}
          onToggle={(e) => setOuverte(e.currentTarget.open ? l.num : (o) => (o === l.num ? null : o))}>
          <summary>
            <span className="adg-loi-titre">
              {l.titre || `Loi n° ${l.num} — hors du corpus des textes promulgués`}
            </span>
            <span className="adg-loi-meta">
              {(l.nature || '').startsWith('Proposition')
                ? <span className="adg-ppl">proposition de loi</span>
                : <span>{l.nature || '—'}</span>}
              <span><b>{nombre(l.n)}</b> acte{l.n > 1 ? 's' : ''}</span>
              {l.com ? <span>{l.com}</span> : null}
              {l.prom ? <span>promulguée le {enClair(l.prom)}</span> : null}
              {l.delai !== undefined ? <span>délai <b>{enJours(l.delai)}</b></span> : null}
            </span>
          </summary>
          <div className="adg-dedans">
            {(l.actes || []).map((a) => <Acte key={a.i} acte={a} />)}
            {l.n > (l.actes || []).length ? (
              <p className="adg-sous">{(l.actes || []).length} actes sur {nombre(l.n)}, du plus ancien au plus récent.</p>
            ) : null}
          </div>
        </details>
      ))}
    </div>
  );
}

function Actes({ cellules, exemples, couleur, theme }) {
  const total = cellules.reduce((s, c) => s + c.n, 0);
  const liste = cellules
    .flatMap((c) => (exemples[`${c.m}|${c.l}|${c.v}`] || []).map((a) => ({ ...a, v: c.v })))
    .sort((a, b) => (a.d < b.d ? -1 : 1))
    .slice(0, 12);
  if (!liste.length) return null;
  return (
    <div className="adg-detail">
      <h3>Les actes retenus</h3>
      <p className="adg-sous">
        {nombre(total)} actes · douze d’entre eux, du plus ancien au plus récent. L’ordre est
        celui des dates, aucun classement.
      </p>
      {liste.map((a) => (
        <Acte key={`${a.i}-${a.d}`} acte={a} couleur={couleur[theme(a.m)]} />
      ))}
    </div>
  );
}

function Acte({ acte, couleur }) {
  return (
    <div className="adg-acte" style={couleur ? { borderLeftColor: couleur } : undefined}>
      <p className="adg-acte-titre">{acte.t}</p>
      <p className="adg-acte-meta">
        {acte.m} · {enClair(acte.d)}
        {acte.v ? <> · <i>{acte.v}</i></> : null}
        {' · '}
        <a href={`https://www.legifrance.gouv.fr/jorf/id/JORFTEXT${acte.i}`}
          target="_blank" rel="noopener noreferrer">Lire sur Légifrance ↗</a>
      </p>
    </div>
  );
}
