/*
 * La fiche d'une LIGNÉE de groupe parlementaire — la page de groupe de #329,
 * depuis la décision du 10/09/2026 : une fiche par lignée (#836), pas par
 * législature.
 *
 * Construite en maquette avec la propriétaire le 11/09/2026 (artifact
 * edb442eb, seize versions annotées) ; ce qui a été tranché, avec ses mesures,
 * est dans `docs/decisions/fiche-de-lignee-ui-329.md`.
 *
 * Ce composant REND. Tout ce qu'il affiche arrive déjà calculé dans la
 * projection de build (`scripts/vue-lignee.mjs`), par les règles de
 * `utils/groupe.js` et `utils/lignee.js` — les mêmes que ce fichier importe
 * pour ses libellés. Aucun nombre n'est recalculé ici.
 *
 * Les sept règles de forme (DESIGN_SYSTEM §6 bis) y sont appliquées : un
 * critère court sous le titre, la limite en pied de section, le raisonnement en
 * méthodologie derrière un renvoi — jamais un paragraphe sur la fiche.
 */
import { createContext, useContext, useMemo, useState } from 'react';
import { EtiquetteFiltre, MOT } from './Recherche';
import { Link } from 'react-router-dom';
import '../styles/shell.css';
import './LigneeProfile.css';
import NavigationPeriodes from './NavigationPeriodes';
import { ListeVide } from './Lecture';
import { LAST_READING_LABEL, formatNumber, styleForPosition, pageDuJeuDeDonnees } from '../utils/lecture';
import { MAILLON_A_DES_RESULTATS } from '../utils/filtreLignee';
import { cumulerTypes, LISTES_SIGNALEES, motifDePosture, ORDRE_PASSAGES, PASSAGES, QUALITES_TEXTE, textesDesQualites } from '../utils/lignee';
import { Cascade, ListeCascade } from './CascadeTextes';
import { MATIERE_NON_ETABLIE, textesPortes } from '../utils/profilCandidat';
import { GRIS_SANS_MATIERE, PALETTE_MATIERE } from '../utils/matiere';

const MOIS = [
  'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
  'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre',
];
const jour = (iso) => {
  if (!iso) return null;
  const [a, m, j] = String(iso).split('-');
  return j ? `${Number(j)} ${MOIS[Number(m) - 1]} ${a}` : a;
};
const court = (iso) => {
  if (!iso) return '';
  const [a, m, j] = String(iso).split('-');
  return `${j}/${m}/${a}`;
};
const ROMAIN = { 14: 'XIV', 15: 'XV', 16: 'XVI', 17: 'XVII' };
const legislature = (l) => (l && ROMAIN[l] ? `${ROMAIN[l]}e` : '');
const nomDuMaillon = (m) => [m.sigle, legislature(m.legislature)].filter(Boolean).join(' · ');
const periodeDuMaillon = (m) => (m.periode.fin
  ? `${court(m.periode.debut)} → ${court(m.periode.fin)}`
  : `depuis le ${court(m.periode.debut)}`);

/* L'intitulé EST le lien vers la source (relecture du 11/09/2026) : plus de
 * badge « Source » sous chaque ligne. Sans URL publiée, l'intitulé reste du
 * texte et le dit — « lien de source non publié » parle de NOUS, jamais de la
 * donnée (DESIGN_SYSTEM §5). */
function LienSource({ url, children }) {
  if (!url) {
    return (
      <>
        <span>{children}</span> <small className="lp-sans-lien">lien de source non publié</small>
      </>
    );
  }
  /* Une archive ne s'ouvre pas, elle se télécharge : le lien mène alors à la
     PAGE du jeu de données, qui porte le téléchargement (#330). */
  return (
    <a className="lp-lien" href={pageDuJeuDeDonnees(url)} rel="noreferrer" target="_blank">
      {children}
    </a>
  );
}

/* Un en-tête de section, la grammaire de la fiche candidat : numéro, titre
 * surligné, critère court ; la limite et le renvoi en pied, APRÈS le contenu.
 * `id` et `data-section` servent `SommaireSections`, qui lit la page.
 * `renvoi` mène à une ancre de la méthodologie ; une section qui pose deux
 * questions distinctes en porte deux, sous `renvois` (DESIGN_SYSTEM §7). */
/* ── La recherche sur la fiche (#979) ────────────────────────────────────────
 *
 * Sous un mot, la page lit une lignée RÉDUITE (`filtrerLignee`) et chaque
 * section EMPILE les groupes de la lignée où le mot trouve quelque chose, du
 * plus récent au plus ancien, sans flèches — la recherche couvre toute la
 * lignée (forme B, arbitrée le 17/09/2026). Le contexte dit à une section quel
 * maillon elle rend, et si elle porte le titre (premier de la pile) et le pied
 * (dernier). « En bref » et « Qui sont-ils » se retirent ; « Ce qu'on n'a pas pu
 * lire » ne change pas. */
const Filtre = createContext({ mot: '', index: null, avecTete: true, avecPied: true });
function Etiquette() {
  const { mot } = useContext(Filtre);
  return mot ? <EtiquetteFiltre mot={mot} /> : null;
}
function VideFiltre({ children }) {
  const { mot } = useContext(Filtre);
  return <p className="cp-filtre-vide">{children} {MOT(mot)}.</p>;
}
function Section({ numero, titre, critere, pied, renvoi, renvois, children }) {
  const { avecTete, avecPied } = useContext(Filtre);
  if (!avecTete || !avecPied) {
    return (
      <section className="lp-section" data-section={avecTete ? titre : undefined} id={avecTete ? `section-${numero}` : undefined} style={avecTete ? undefined : { marginTop: 18 }}>
        {avecTete && (<><div className="lp-section-bande"><span className="lp-section-numero">{numero}</span><span className="lp-section-trait" /></div>
        <h2 className="lp-section-titre"><span>{titre}</span></h2>{critere && <p className="lp-section-critere">{critere}</p>}</>)}
        <div className="lp-section-corps">{children}</div>
        {avecPied && pied && <p className="lp-section-pied">{pied}</p>}
        {avecPied && renvoi && <p className="lp-methodo"><Link to={`/methodologie#${renvoi.ancre}`}>{renvoi.texte}</Link></p>}
      </section>
    );
  }
  return (
    <section className="lp-section" data-section={titre} id={`section-${numero}`}>
      <div className="lp-section-bande">
        <span className="lp-section-numero">{numero}</span>
        <span className="lp-section-trait" />
      </div>
      <h2 className="lp-section-titre"><span>{titre}</span></h2>
      {critere && <p className="lp-section-critere">{critere}</p>}
      <div className="lp-section-corps">{children}</div>
      {pied && <p className="lp-section-pied">{pied}</p>}
      {renvoi && (
        <p className="lp-methodo">
          <Link to={`/methodologie#${renvoi.ancre}`}>{renvoi.texte}</Link>
        </p>
      )}
      {renvois && (
        <p className="lp-methodo">
          {renvois.map((r, i) => (
            <span key={r.vers}>
              {i > 0 && ' · '}
              <Link to={r.vers}>{r.texte}</Link>
            </span>
          ))}
        </p>
      )}
    </section>
  );
}

/* La posture en pilule, là où elle change le sens d'un chiffre : la bordure
 * reprend le motif de la frise, jamais une teinte de jugement. */
function Posture({ posture }) {
  return <span className={`lp-posture lp-posture--${motifDePosture(posture)}`}>{posture.label}</span>;
}

function TeteDePeriode({ maillon, avecPosture = true }) {
  return (
    <div className="lp-periode-tete">
      <h3>
        <span>
          {maillon.nom}
          {maillon.legislature ? ` · ${legislature(maillon.legislature)} législature` : ''}
        </span>
        {avecPosture && <Posture posture={maillon.posture} />}
      </h3>
      <span className="lp-periode-dates">{periodeDuMaillon(maillon)}</span>
    </div>
  );
}

/* Une section qui se lit maillon par maillon : la navigation par période de la
 * fiche candidat, la même, avec son rail proportionnel au poids de CETTE
 * section. Une lignée d'un seul maillon n'a rien à naviguer. */
function useMaillon(lignee) {
  const force = useContext(Filtre).index;
  const [index, setIndex] = useState(lignee.maillons.length - 1);
  if (force != null) return [lignee.maillons[force], force, () => {}];
  return [lignee.maillons[index], index, setIndex];
}

function Navigation({ lignee, index, onIndex, poids, unite, uniteSingulier }) {
  const force = useContext(Filtre).index;
  const periodes = useMemo(
    () => lignee.maillons.map((m) => ({ ...m, cle: m.id, debut: m.periode.debut, fin: m.periode.fin })),
    [lignee],
  );
  if (periodes.length < 2 || force != null) return null;
  return (
    <NavigationPeriodes
      index={index}
      libelle={nomDuMaillon}
      onIndex={onIndex}
      periodes={periodes}
      poids={poids}
      unite={unite}
      uniteSingulier={uniteSingulier}
    />
  );
}

/* Un maillon dont la fiche ne porte pas cette liste le DIT, avec la cause que
 * la fiche déclare — le Sénat, hors périmètre depuis #528 —, jamais un zéro. */
function Vide({ maillon }) {
  const c = maillon.couverture || {};
  return <ListeVide cause={c.causeListeVide ?? 'non_collecte'} motif={c.motifListeVide ?? c.phrase} />;
}

/* ── En bref : l'effectif dans le temps ───────────────────────────────────────
 *
 * Teinte = l'Assemblée, motif = la posture du maillon (retenu le 11/09/2026),
 * hauteur = le nombre de membres ce jour-là, recompté depuis les appartenances
 * — il retombe sur l'effectif publié à la date de référence de chaque fiche. */
const LARGEUR = 1000;
const MARGE = { g: 34, d: 14, h: 34, b: 24 };

function DefsMotifs() {
  return (
    <defs>
      <pattern height="10" id="lp-m-diagonales" patternUnits="userSpaceOnUse" width="10">
        <rect fill="var(--parl)" height="10" width="10" />
        <path d="M-2,2 l4,-4 M0,10 l10,-10 M8,12 l4,-4" stroke="rgba(255,255,255,.55)" strokeWidth="3.5" />
      </pattern>
      <pattern height="3" id="lp-m-points" patternUnits="userSpaceOnUse" width="3">
        <rect fill="var(--card)" height="3" width="3" />
        <circle cx="1.5" cy="1.5" fill="var(--parl)" r="0.75" />
      </pattern>
    </defs>
  );
}

const REMPLISSAGE = {
  plein: 'var(--parl)',
  diagonales: 'url(#lp-m-diagonales)',
  mauve: 'var(--parl-mauve)',
  points: 'url(#lp-m-points)',
  absente: 'var(--card)',
};
// L'encre d'une étiquette posée dans une bande suit la valeur de la bande.
const ENCRE = { plein: '#fff', diagonales: '#fff', mauve: 'var(--ink)', points: 'var(--ink)', absente: 'var(--ink)' };

function Pave({ motif }) {
  return (
    <svg aria-hidden="true" className="lp-pave" viewBox="0 0 34 17">
      <rect fill={REMPLISSAGE[motif]} height="17" stroke={motif === 'absente' ? 'var(--muted)' : 'none'} strokeDasharray="3 2" width="34" />
    </svg>
  );
}

function Frise({ lignee, aujourdhui }) {
  const [survol, setSurvol] = useState(null);
  const { maillons } = lignee;
  const derniere = maillons[maillons.length - 1];
  const debut = Date.parse(maillons[0].periode.debut);
  const fin = Date.parse(lignee.periode.fin && !derniere.periode.actif ? lignee.periode.fin : aujourdhui);
  const x = (iso) => MARGE.g + ((Date.parse(iso) - debut) / Math.max(1, fin - debut)) * (LARGEUR - MARGE.g - MARGE.d);
  // Un effectif ne se trace que s'il est DATÉ : les deux fiches Sénat gelées ne
  // portent que l'ancien compteur, rapporté à aucune date (#653).
  const trace = (m) => Boolean(m.serie?.length && m.effectif != null && m.dateReference);
  const avecEffectif = maillons.some(trace);
  // Sans effectif tracé, la frise se réduit à sa bande : une hauteur vide se
  // lirait comme un effectif nul.
  const HAUTEUR = avecEffectif ? 230 : 96;
  const max = Math.max(1, ...maillons.flatMap((m) => (m.serie || []).map((p) => p[1])));
  const y = (v) => HAUTEUR - MARGE.b - (v / (max * 1.12)) * (HAUTEUR - MARGE.b - MARGE.h);
  const pas = max > 200 ? 100 : max > 80 ? 50 : max > 30 ? 20 : 10;
  const graduations = [];
  for (let v = pas; v < max * 1.12; v += pas) graduations.push(v);
  const annees = [];
  for (let a = new Date(debut).getUTCFullYear() + 1; a <= new Date(fin).getUTCFullYear(); a += 1) annees.push(a);

  const bande = (m) => {
    const x0 = x(m.periode.debut);
    const x1 = x(m.periode.fin || aujourdhui);
    let d = `M${x0},${y(0)}`;
    let ligne = '';
    let niveau = 0;
    m.serie.forEach(([date, v], i) => {
      const xx = Math.max(x0, Math.min(x1, x(date)));
      d += `L${xx},${y(niveau)}L${xx},${y(v)}`;
      ligne += i === 0 ? `M${xx},${y(v)}` : `L${xx},${y(niveau)}L${xx},${y(v)}`;
      niveau = v;
    });
    d += `L${x1},${y(niveau)}L${x1},${y(0)}Z`;
    ligne += `L${x1},${y(niveau)}`;
    return { x0, x1, d, ligne, niveau };
  };

  const surDeplacement = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const px = ((e.clientX - rect.left) / rect.width) * LARGEUR;
    const t = new Date(debut + ((px - MARGE.g) / (LARGEUR - MARGE.g - MARGE.d)) * (fin - debut));
    const iso = t.toISOString().slice(0, 10);
    const m = maillons.find((mm) => mm.periode.debut <= iso && iso <= (mm.periode.fin || aujourdhui));
    let v = null;
    if (m) for (const [date, c] of m.serie || []) if (date <= iso) v = c;
    setSurvol({ px, iso, maillon: m ?? null, valeur: v });
  };

  const motifs = [...new Set(maillons.map((m) => motifDePosture(m.posture)))];
  const source = maillons.find((m) => m.posture?.sourceUrl)?.posture.sourceUrl ?? null;

  return (
    <div className="lp-carte lp-frise">
      <svg
        aria-label={`Effectif du groupe dans le temps, ${maillons.length} groupe${maillons.length > 1 ? 's' : ''} successif${maillons.length > 1 ? 's' : ''}`}
        onMouseLeave={() => setSurvol(null)}
        onMouseMove={avecEffectif ? surDeplacement : undefined}
        role="img"
        viewBox={`0 0 ${LARGEUR} ${HAUTEUR}`}
      >
        <DefsMotifs />
        {avecEffectif && graduations.map((v) => (
          <g key={v}>
            <line stroke="var(--border)" x1={MARGE.g} x2={LARGEUR - MARGE.d} y1={y(v)} y2={y(v)} />
            <text className="lp-axe" textAnchor="end" x={MARGE.g - 6} y={y(v) + 3.5}>{v}</text>
          </g>
        ))}
        <line stroke="var(--border-strong)" x1={MARGE.g} x2={LARGEUR - MARGE.d} y1={y(0)} y2={y(0)} />
        {maillons.map((m, i) => {
          const motif = motifDePosture(m.posture);
          const x0 = x(m.periode.debut);
          const repere = (
            <g>
              <line stroke="var(--border-strong)" x1={x0} x2={x0} y1={22} y2={y(0)} />
              <circle cx={x0} cy={12} fill="var(--card)" r={9} stroke="var(--ink)" strokeWidth={1.5} />
              <text className="lp-repere" textAnchor="middle" x={x0} y={15.5}>{i + 1}</text>
            </g>
          );
          if (!trace(m)) {
            const x1 = x(m.periode.fin || aujourdhui);
            return (
              <g key={m.id}>
                <rect fill="var(--card)" height={26} rx={3} stroke="var(--muted)" strokeDasharray="4 3" strokeWidth={1.5} width={Math.max(4, x1 - x0)} x={x0} y={y(0) - 26} />
                <text className="lp-bande-vide" x={x0 + 8} y={y(0) - 9}>Effectif non publié</text>
                {repere}
              </g>
            );
          }
          const b = bande(m);
          return (
            <g key={m.id}>
              <path d={b.d} fill={REMPLISSAGE[motif]} />
              <path d={b.ligne} fill="none" stroke="var(--ink)" strokeOpacity={0.55} strokeWidth={1.2} />
              <text className="lp-effectif" textAnchor="end" x={b.x1 - 3} y={y(m.effectif) - 7}>
                {formatNumber(m.effectif)}
              </text>
              {b.x1 - b.x0 > 54 && y(0) - y(b.niveau) > 22 && (
                <text className="lp-bande-nom" fill={ENCRE[motif]} x={b.x0 + 7} y={y(0) - 8}>{nomDuMaillon(m)}</text>
              )}
              {repere}
            </g>
          );
        })}
        {annees.map((a) => {
          const xx = x(`${a}-01-01`);
          return xx > MARGE.g && xx < LARGEUR - MARGE.d ? (
            <text className="lp-axe" key={a} textAnchor="middle" x={xx} y={HAUTEUR - 6}>{a}</text>
          ) : null;
        })}
        {survol && <line stroke="var(--ink)" x1={survol.px} x2={survol.px} y1={MARGE.h - 6} y2={y(0)} />}
      </svg>
      <p aria-live="polite" className="lp-frise-lecture">
        {survol
          ? survol.maillon
            ? <><b>{formatNumber(survol.valeur)}</b> membres le {jour(survol.iso)} · {nomDuMaillon(survol.maillon)}</>
            : <>{jour(survol.iso)} : entre deux législatures, aucun groupe</>
          : ' '}
      </p>
      <div className="lp-legende">
        {motifs.map((motif) => {
          const m = maillons.find((mm) => motifDePosture(mm.posture) === motif);
          return (
            <span className="lp-legende-item" key={motif}>
              <Pave motif={motif} />
              {m.posture.label}
            </span>
          );
        })}
        {source && (
          <span className="lp-legende-item">
            <LienSource url={source}>Selon l'Assemblée nationale</LienSource>
          </span>
        )}
      </div>
      {/* Du plus récent au plus ancien, de haut en bas (relecture du 11/09/2026) :
          le groupe d'aujourd'hui se lit d'abord. Chaque ligne garde le numéro de
          son repère sur la frise, qui court, elle, dans l'ordre du temps. */}
      <ol className="lp-maillons" reversed>
        {maillons.map((m, i) => [m, i]).reverse().map(([m, i]) => (
          <li className="lp-maillon" key={m.id}>
            <span className="lp-maillon-repere">{i + 1}</span>
            <span className="lp-maillon-dates">{periodeDuMaillon(m)}</span>
            <span className="lp-maillon-nom">
              <b>{m.nom}</b>
              {m.legislature ? ` · ${legislature(m.legislature)} législature` : ''} <Posture posture={m.posture} />
            </span>
            <span className="lp-maillon-effectif">
              {m.effectif != null && m.dateReference ? (
                <><b className="lp-num">{formatNumber(m.effectif)}</b> <small>membres au {court(m.dateReference)}</small></>
              ) : (
                <small>effectif non publié</small>
              )}
            </span>
          </li>
        ))}
      </ol>
    </div>
  );
}

/* ── § 1 — qui sont-ils : un point par personne ───────────────────────────────
 *
 * Forme B de la maquette, retenue le 11/09/2026 après cinq agrégats écartés la
 * veille. Chaque point est une personne, et dit d'où elle vient ; le survol
 * allume son chemin dans tous les groupes de la lignée. Trois comptes publiés
 * côte à côte, jamais un taux de renouvellement (§2 règle 1). */
function QuiSontIls({ lignee }) {
  const [survol, setSurvol] = useState(null);
  const chemins = useMemo(() => {
    const c = lignee.personnes.map(() => []);
    lignee.maillons.forEach((m, i) => { for (const [r] of m.presents) c[r].push(i); });
    return c;
  }, [lignee]);
  const colonnes = Math.max(...lignee.maillons.map((m) => m.presents.length)) > 150 ? 20 : 12;
  const candidats = lignee.personnes.filter((p) => p.candidat);
  const nom = (p) => (p.candidat ? <Link to={`/candidats/${p.id}`}>{p.nom}</Link> : p.nom);

  return (
    <Section
      critere="Chaque personne passée par l'un des groupes de la lignée, et le chemin qu'elle y a fait."
      numero="1"
      pied={(
        <>
          {formatNumber(lignee.couverture?.profils_lus)} profils publiés sur {formatNumber(lignee.cumul)} personnes
          {candidats.length > 0 && (
            <> · candidat{candidats.length > 1 ? 's' : ''} déclaré{candidats.length > 1 ? 's' : ''} :{' '}
              {candidats.map((p, i) => <span key={p.id}>{i > 0 ? ', ' : ''}{nom(p)}</span>)}
            </>
          )}
        </>
      )}
      renvoi={{ ancre: 'lignee', texte: 'Comment les groupes d’une lignée sont reliés' }}
      titre="Qui sont-ils"
    >
      <div className="lp-carte">
        <div className="lp-cles">
          {ORDRE_PASSAGES.map((cle) => (
            <span key={cle}><i className={`lp-point lp-point--${cle}`} />{PASSAGES[cle].label}</span>
          ))}
        </div>
        <div className="lp-blocs" onMouseLeave={() => setSurvol(null)}>
          {lignee.maillons.map((m, i) => (
            <div className="lp-bloc" key={m.id}>
              <p className="lp-bloc-tete">
                {nomDuMaillon(m)}
                <b className="lp-num">{formatNumber(m.presents.length)} <small>personnes</small></b>
              </p>
              <div className="lp-grille" style={{ gridTemplateColumns: `repeat(${colonnes}, 10px)` }}>
                {m.presents.map(([r, passage]) => (
                  <button
                    aria-label={`${lignee.personnes[r].nom} — ${PASSAGES[passage].label}`}
                    className={`lp-point lp-point--${passage}${survol === r ? ' lp-point--eclaire' : ''}`}
                    key={r}
                    onBlur={() => setSurvol(null)}
                    onFocus={() => setSurvol(r)}
                    onMouseEnter={() => setSurvol(r)}
                    type="button"
                  />
                ))}
              </div>
              <p className="lp-bloc-comptes">
                {i > 0 && <span><b>{formatNumber(m.comptes.prec)}</b> {PASSAGES.prec.compte}</span>}
                {m.comptes.retour > 0 && <span><b>{formatNumber(m.comptes.retour)}</b> {PASSAGES.retour.compte}</span>}
                <span><b>{formatNumber(m.comptes.nouveau)}</b> {i === 0 ? 'au départ' : PASSAGES.nouveau.compte}</span>
              </p>
            </div>
          ))}
        </div>
        <p aria-live="polite" className="lp-chemin">
          {survol != null
            ? <><b>{lignee.personnes[survol].nom}</b> · {chemins[survol].map((i) => nomDuMaillon(lignee.maillons[i])).join(' → ')}</>
            : ' '}
        </p>
        {/* Les noms en colonnes, UNE PAR GROUPE de la lignée (relecture du
            11/09/2026), dans l'ordre des points : une personne passée par trois
            groupes figure dans trois colonnes, et c'est le chemin qui se lit.
            Le survol d'un nom allume son chemin dans la grille, comme un point. */}
        <details className="lp-tous">
          <summary>Les {formatNumber(lignee.personnes.length)} personnes</summary>
          <div className="lp-tous-colonnes" onMouseLeave={() => setSurvol(null)}>
            {lignee.maillons.map((m) => (
              <div className="lp-tous-colonne" key={m.id}>
                <p className="lp-bloc-tete">
                  {nomDuMaillon(m)} <small>· {formatNumber(m.presents.length)}</small>
                </p>
                <ul>
                  {m.presents.map(([r, passage]) => (
                    <li
                      className={survol === r ? 'lp-tous-actif' : undefined}
                      key={r}
                      onMouseEnter={() => setSurvol(r)}
                    >
                      <i aria-hidden="true" className={`lp-point lp-point--${passage}`} />
                      {nom(lignee.personnes[r])}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </details>
      </div>
    </Section>
  );
}

/* ── § 2 — sur quoi ils ont pris la parole ─────────────────────────────────── */
function SurQuoiIlsParlent({ lignee }) {
  const [m, index, setIndex] = useMaillon(lignee);
  const { mot } = useContext(Filtre);
  const s = mot ? m.sujets : { ...m.sujets, liste: m.sujets.liste.slice(0, 10) };
  return (
    <Section
      critere="Les débats où le plus de membres sont intervenus : des sujets, jamais des positions du groupe."
      numero="2"
      pied={mot ? null : s.liste.length > 0
        ? `${s.liste.length} sur ${formatNumber(s.total)} débats · membres qui y sont intervenus, sur ${formatNumber(s.denominateur)} passés par le groupe`
        : null}
      renvoi={{ ancre: 'paroles', texte: 'D’où viennent ces intitulés' }}
      titre="Sur quoi ils ont pris la parole"
    >
      <Navigation index={index} lignee={lignee} onIndex={setIndex} poids={(p) => p.sujets.total} unite="débats" uniteSingulier="débat" />
      <div className="lp-carte">
        <TeteDePeriode avecPosture={false} maillon={m} />
        <Etiquette />
        {s.liste.length === 0 && mot ? <VideFiltre>Aucun débat dont l’intitulé contient</VideFiltre> : s.liste.length === 0 ? <Vide maillon={m} /> : s.liste.map((t) => (
          <div className="lp-sujet" key={t.label}>
            <span className="lp-sujet-lib">{t.label}</span>
            <span className="lp-sujet-n lp-num" title={t.porteursTexte}>
              <b>{formatNumber(t.porteurs)}</b> <small>/ {formatNumber(t.denominateur)}</small>
            </span>
            <span className="lp-sujet-barre"><i style={{ width: `${((100 * t.porteurs) / Math.max(1, t.denominateur)).toFixed(1)}%` }} /></span>
          </div>
        ))}
      </div>
    </Section>
  );
}

/* ── § 3 — ce qu'ils ont proposé ───────────────────────────────────────────────
 *
 * Le gabarit « amendements par matière » de la fiche candidat (relecture du
 * 11/09/2026) : la commission saisie au fond, le ratio par texte au milieu, les
 * textes distincts au bout. Au clic, les textes, du plus récemment amendé au
 * plus ancien, avec le sort du texte quand la source le publie.
 *
 * LES DEUX TYPES DE DÉPOSANT SE SÉLECTIONNENT ENSEMBLE (relecture du
 * 11/09/2026) : un type seul se lit seul ; les deux, et chaque compte porte sur
 * les deux catégories réunies — les amendements s'additionnent, les textes se
 * réunissent sur leur dossier (`cumulerTypes`, `utils/lignee.js`). Aucun taux
 * d'adoption n'en sort (`AGENTS.md` §6). Les boutons sont des pilules de filtre
 * multi-état, pas des onglets : le DESIGN_SYSTEM §5 réserve le jaune plein à
 * l'onglet exclusif, et ne confond jamais les deux. */
const TYPES_DEPOSANT = {
  depute: 'Comme députés',
  commission_rapporteur: 'Comme rapporteurs de commission',
};
const LIBELLES_QUALITE = {
  auteur: 'Comme auteurs',
  rapporteur: 'Comme rapporteurs',
};

/* LES TEXTES QU'ILS ONT PORTÉS — la cascade de la fiche candidat, la même
 * figure importée (`CascadeTextes.jsx`) et la même règle (`textesPortes`,
 * utils/profilCandidat.js). Seule change la population : les dossiers portés
 * par les membres du groupe dans la législature, un dossier une fois
 * (`textesDuMaillon`, utils/lignee.js). Les deux qualités se sélectionnent
 * ensemble, comme les types de déposant des amendements. Sous le seuil de
 * l'examen en commission, rien n'est publié (AGENTS §6). */
function TextesPortes({ maillon, rangs }) {
  const { mot } = useContext(Filtre);
  const [qualites, setQualites] = useState(Object.keys(QUALITES_TEXTE));
  const [sel, setSel] = useState(null);
  const textes = useMemo(() => {
    if (!maillon.textes) return null;
    const retenus = textesDesQualites(maillon.textes, qualites);
    const parDossier = new Map(retenus.map((t) => [t.dossier_id, t.commission]));
    return textesPortes(retenus, (dossier) => parDossier.get(dossier) ?? null);
  }, [maillon, qualites]);
  if (!textes) return null;
  if (mot && !maillon.textes.length) {
    return <div className="lp-carte lp-textes"><Etiquette /><VideFiltre>Aucun texte porté dont l’intitulé contient</VideFiltre></div>;
  }
  const presentes = Object.keys(QUALITES_TEXTE).filter((q) => maillon.textes.some((t) => t.roles?.[q]));
  const basculer = (q) => {
    // Une qualité au moins reste retenue : une cascade vide se lirait « aucun texte ».
    const suivantes = qualites.includes(q) ? qualites.filter((x) => x !== q) : [...qualites, q];
    if (suivantes.length) { setQualites(suivantes); setSel(null); }
  };
  return (
    <div className="lp-carte lp-textes">
      <Etiquette />
      <div className="lp-mat-tete">
        <span className="lp-mat-titre">Les textes qu'ils ont portés</span>
        <span className="lp-mat-totaux lp-num">
          <b>{formatNumber(textes.publies.length)}</b> publiés · <b>{formatNumber(textes.promulgues)}</b>{' '}
          promulgué{textes.promulgues > 1 ? 's' : ''}
        </span>
      </div>
      {presentes.length > 1 && (
        <div aria-label="Qualités retenues" className="lp-onglets" role="group">
          {presentes.map((q) => (
            <button
              aria-pressed={qualites.includes(q)}
              className="lp-filtre"
              key={q}
              onClick={() => basculer(q)}
              type="button"
            >
              {LIBELLES_QUALITE[q]}
            </button>
          ))}
        </div>
      )}
      {textes.cascade.total > 0 ? (
        <>
          <Cascade cascade={textes.cascade} onSelection={setSel} rangs={rangs} selection={sel} />
          <ListeCascade cascade={textes.cascade} onRaz={sel ? () => setSel(null) : null} selection={sel ?? (mot ? { matiere: null, lo: 0, hi: textes.cascade.stades.length - 1 } : null)} />
        </>
      ) : (
        <p className="lp-rien">Aucun de ces textes n'a atteint l'examen en commission.</p>
      )}
    </div>
  );
}
const STATUTS_TEXTE = {
  promulgue: 'promulgué',
  adopte: 'adopté',
  adopte_cmp: 'adopté en CMP',
  navette_en_cours: 'en navette',
  rejete: 'rejeté',
  adopte_49_3: 'adopté sans vote — 49.3',
};
const TEXTES_MONTRES = 12;

function TextesAmendes({ detail }) {
  const [montres, setMontres] = useState(TEXTES_MONTRES);
  return (
    <div className="lp-deroule">
      {detail.slice(0, montres).map((d) => (
        <div className="lp-deroule-ligne" key={d.dossier}>
          <span className="lp-deroule-date lp-num">{court(d.dernier)}</span>
          <span className="lp-deroule-titre">
            <LienSource url={d.sourceUrl}>{d.titre || 'Titre du dossier non publié'}</LienSource>
            {d.statut ? (
              <span className={`lp-statut${d.statut === 'adopte_49_3' ? ' lp-statut--493' : ''}`}>
                {STATUTS_TEXTE[d.statut] || d.statut}
              </span>
            ) : (
              <span className="lp-statut lp-statut--absent">sort du texte non publié</span>
            )}
          </span>
          <span className="lp-deroule-n lp-num">
            <b>{formatNumber(d.amendements)}</b> amdt · <b>{formatNumber(d.adoptes)}</b> adopté{d.adoptes > 1 ? 's' : ''}
          </span>
        </div>
      ))}
      {detail.length > montres && (
        <button className="lp-plus" onClick={() => setMontres(montres + 30)} type="button">
          et {formatNumber(detail.length - montres)} autres textes
        </button>
      )}
    </div>
  );
}

function CeQuIlsOntPropose({ lignee }) {
  const { mot } = useContext(Filtre);
  const [m, index, setIndex] = useMaillon(lignee);
  const types = Object.keys(TYPES_DEPOSANT).filter((t) => m.amendements.parType[t]);
  const [choisis, setChoisis] = useState(['depute']);
  const [ouverte, setOuverte] = useState(null);
  const actifs = types.filter((t) => choisis.includes(t));
  const selection = actifs.length ? actifs : types.slice(0, 1);
  const bloc = cumulerTypes(m.amendements.parType, selection);
  /* UNE TEINTE PAR COMMISSION POUR TOUTE LA SECTION : le rang suit le volume
   * d'amendements du maillon, tous types réunis, et ne bouge ni avec les
   * boutons ni d'une figure à l'autre — la cascade des textes et les barres
   * d'amendements colorient pareil (DESIGN_SYSTEM : la couleur suit l'entité,
   * jamais son rang dans une sélection). */
  const rangs = useMemo(() => {
    const tous = cumulerTypes(m.amendements.parType, Object.keys(m.amendements.parType));
    return new Map((tous?.lignes || []).filter((l) => l.amendements > 0).map((l, i) => [l.commission, i]));
  }, [m]);
  const basculer = (t) => {
    // Un bouton au moins reste sélectionné : une vue vide se lirait « aucun amendement ».
    const suivants = selection.includes(t) ? selection.filter((x) => x !== t) : [...selection, t];
    if (suivants.length) { setChoisis(suivants); setOuverte(null); }
  };
  const lignes = bloc ? bloc.lignes.filter((l) => l.amendements > 0) : [];
  const nd = bloc?.nonEtablie ?? null;
  const maxA = Math.max(1, ...lignes.map((l) => l.amendements), nd?.amendements ?? 0);
  const maxD = Math.max(1, ...lignes.map((l) => (l.textes ? l.amendements / l.textes : 0)));
  const limites = [];
  if (m.amendements.distincts) limites.push(`${formatNumber(m.amendements.distincts)} amendements distincts en tout`);
  if (m.amendements.sansType && !mot) limites.push(`dont ${formatNumber(m.amendements.sansType)} sans type de déposant publié`);
  if (lignes.length) limites.push('textes rangés du plus récemment amendé au plus ancien');

  return (
    <Section
      critere="Textes et amendements distincts : cosigné par vingt membres, un texte ou un amendement compte une fois."
      numero="3"
      pied={limites.join(' · ') || null}
      renvoi={{ ancre: 'depots', texte: 'Quels textes et quels amendements sont retenus, et pourquoi aucun taux d’adoption' }}
      titre="Ce qu'ils ont proposé"
    >
      <Navigation
        index={index}
        lignee={lignee}
        onIndex={(i) => { setIndex(i); setOuverte(null); }}
        poids={(p) => p.amendements.distincts || 0}
        unite="amendements"
        uniteSingulier="amendement"
      />
      <TeteDePeriode maillon={m} />
      {m.textes ? <TextesPortes key={m.id} maillon={m} rangs={rangs} /> : null}
      <div className="lp-carte">
        <Etiquette />
        {!bloc && mot ? <VideFiltre>Aucun dossier amendé dont l’intitulé contient</VideFiltre> : !bloc ? <Vide maillon={m} /> : (
          <>
            {types.length > 1 && (
              <div aria-label="Types de déposant retenus" className="lp-onglets" role="group">
                {types.map((t) => (
                  <button
                    aria-pressed={selection.includes(t)}
                    className="lp-filtre"
                    key={t}
                    onClick={() => basculer(t)}
                    type="button"
                  >
                    {TYPES_DEPOSANT[t]}
                  </button>
                ))}
              </div>
            )}
            <div className="lp-mat-tete">
              {/* « Par matière », et non « Par commission saisie au fond » (#328).
                  L'expression est du jargon parlementaire : la propriétaire, qui
                  connaît ce corpus mieux que quiconque, a demandé ce qu'elle
                  voulait dire. « Matière » est le mot que le produit emploie
                  partout ailleurs, et que la page de méthodologie définit
                  désormais en français courant. Le terme officiel y survit une
                  fois, comme passerelle vers le vocabulaire de la source. */}
              <span className="lp-mat-titre">Par matière</span>
              <span className="lp-mat-totaux lp-num">
                <b>{formatNumber(bloc.amendements)}</b> amendements · <b>{formatNumber(bloc.dossiers)}</b> dossiers ·{' '}
                <b>{formatNumber(bloc.adoptes)}</b> adoptés
              </span>
            </div>
            <div className="lp-mat">
              {/* Les cases vides d'en-tête portent la classe des barres qu'elles
                  surplombent : sous 720 px les barres disparaissent, et une case
                  restée décalait toute la ligne d'une colonne. */}
              <div className="lp-mr lp-mr--tete">
                <span />
                <span className="lp-mr-rail" />
                <span className="lp-mr-n">amendements</span>
                <span className="lp-mr-n">ratio par texte</span>
                <span className="lp-mr-rail" />
                <span className="lp-mr-n">textes distincts</span>
              </div>
              {lignes.map((l, r) => {
                const densite = l.textes ? l.amendements / l.textes : null;
                const teinte = PALETTE_MATIERE[(rangs.get(l.commission) ?? r) % PALETTE_MATIERE.length];
                const ouvert = ouverte === l.commission || Boolean(mot);
                return (
                  <div key={l.commission}>
                    <button
                      aria-expanded={ouvert}
                      className="lp-mr lp-mr--cliquable"
                      onClick={() => setOuverte(ouvert ? null : l.commission)}
                      type="button"
                    >
                      <span className="lp-mr-lib" title={l.commission}>{l.commission}</span>
                      <span className="lp-mr-rail"><i style={{ background: teinte, width: `${((100 * l.amendements) / maxA).toFixed(1)}%` }} /></span>
                      <span className="lp-mr-n">{formatNumber(l.amendements)}</span>
                      <span className="lp-mr-n">{densite == null ? '—' : formatNumber(Math.round(densite))}</span>
                      <span className="lp-mr-rail">
                        {densite != null && <i style={{ background: teinte, opacity: 0.5, width: `${((100 * densite) / maxD).toFixed(1)}%` }} />}
                      </span>
                      <span className="lp-mr-n lp-mr-n--textes">{formatNumber(l.textes)}</span>
                    </button>
                    {ouvert && <TextesAmendes detail={l.detail} />}
                  </div>
                );
              })}
              {nd && nd.amendements > 0 && (
                <div>
                  <button
                    aria-expanded={ouverte === MATIERE_NON_ETABLIE}
                    className="lp-mr lp-mr--cliquable lp-mr--nd"
                    onClick={() => setOuverte(ouverte === MATIERE_NON_ETABLIE ? null : MATIERE_NON_ETABLIE)}
                    type="button"
                  >
                    <span className="lp-mr-lib">{MATIERE_NON_ETABLIE}</span>
                    <span className="lp-mr-rail"><i style={{ background: GRIS_SANS_MATIERE, width: `${((100 * nd.amendements) / maxA).toFixed(1)}%` }} /></span>
                    <span className="lp-mr-n">{formatNumber(nd.amendements)}</span>
                    <span className="lp-mr-n">—</span>
                    <span className="lp-mr-rail" />
                    <span className="lp-mr-n lp-mr-n--textes">{nd.textes ? formatNumber(nd.textes) : '—'}</span>
                  </button>
                  {(ouverte === MATIERE_NON_ETABLIE || mot) && nd.detail.length > 0 && <TextesAmendes detail={nd.detail} />}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </Section>
  );
}

/* ── § 4 — ce qu'ils ont voté ─────────────────────────────────────────────────
 *
 * Un groupe ne vote pas : ses membres votent. Le quorum ouvre la section, au
 * rang d'un sous-titre (relecture du 11/09/2026) ; la barre en trois parts
 * filtre la liste au clic. En tête, la DERNIÈRE lecture de chaque texte (#711) ;
 * le reste — lectures antérieures, amendements, articles, motions — replié. */
const PARTS = {
  une_seule_voix: { lib: "d'une seule voix", classe: 'lp-part--une', titre: "D'une seule voix — les plus récents" },
  abstention: { lib: "partagés entre une position et l'abstention", classe: 'lp-part--nuance', titre: "Entre une position et l'abstention — les plus partagés" },
  pour_et_contre: { lib: 'avec des voix pour et des voix contre', classe: 'lp-part--oppose', titre: 'Pour et contre — les plus partagés' },
};
const SCRUTINS_MONTRES = 6;
const POSITIONS = ['pour', 'contre', 'abstention'];

function Scrutin({ id, pour, contre, abstention, scrutins }) {
  const s = scrutins[id] || {};
  const voix = { pour, contre, abstention };
  const exprimees = POSITIONS.filter((p) => voix[p] > 0);
  const total = exprimees.reduce((a, p) => a + voix[p], 0);
  return (
    <div className="lp-scrutin">
      <div>
        <p className="lp-scrutin-texte" title={s.texte || undefined}>
          <LienSource url={s.sourceUrl}>{s.texte || 'Intitulé non publié'}</LienSource>
        </p>
        <p className="lp-scrutin-date lp-num">{court(s.date)}</p>
      </div>
      <div>
        <div aria-label={exprimees.map((p) => `${voix[p]} ${p}`).join(', ')} className="lp-repartition" role="img">
          {exprimees.map((p) => (
            <i key={p} style={{ flex: `${voix[p]} 1 0`, background: styleForPosition(p).color }}>{voix[p]}</i>
          ))}
        </div>
        <p className="lp-repartition-leg">
          {exprimees.map((p) => `${voix[p]} ${styleForPosition(p).label.toLowerCase()}`).join(' · ')} — {total} voix exprimées
        </p>
      </div>
    </div>
  );
}

function CeQuIlsOntVote({ lignee }) {
  const { mot } = useContext(Filtre);
  const [m, index, setIndex] = useMaillon(lignee);
  const [filtre, setFiltre] = useState(null);
  const [montres, setMontres] = useState(SCRUTINS_MONTRES);
  const q = m.quorum;
  const p = m.partage;
  const valeurs = {
    une_seule_voix: p.uneSeuleVoix,
    abstention: p.partages - p.pourEtContre,
    pour_et_contre: p.pourEtContre,
  };
  /* Sous un mot, la liste est DÉPLIÉE sur toutes les parts (#979) : les votes
   * d'une seule voix n'y apparaissaient qu'au clic sur leur segment. */
  const liste = filtre || !mot
    ? (m.partageListes?.[filtre || 'partages'] || [])
    : [...(m.partageListes?.partages || []), ...(m.partageListes?.une_seule_voix || [])];
  const dernieres = liste.filter(([id]) => m.scrutins[id]?.derniere);
  const reste = liste.filter(([id]) => !m.scrutins[id]?.derniere);
  const basculer = (cle) => { setFiltre(filtre === cle ? null : cle); setMontres(SCRUTINS_MONTRES); };

  return (
    <Section
      critere="Un groupe ne vote pas : ses membres votent. Mesuré là où la moitié d'entre eux a voté."
      numero="4"
      pied={q.agreges ? 'Positions exprimées seulement · les absences ne sont jamais comptées' : null}
      renvoi={{ ancre: 'cohesion', texte: 'Pourquoi aucun indice de cohésion' }}
      titre="Ce qu'ils ont voté"
    >
      <Navigation
        index={index}
        lignee={lignee}
        onIndex={(i) => { setIndex(i); setFiltre(null); setMontres(SCRUTINS_MONTRES); }}
        poids={(x) => (mot ? x.quorum.mesurables : x.quorum.agreges)}
        unite="scrutins"
        uniteSingulier="scrutin"
      />
      <div className="lp-carte">
        <Etiquette />
        <TeteDePeriode maillon={m} />
        {q.agreges && mot && !q.mesurables ? <VideFiltre>Aucun scrutin dont l’intitulé contient</VideFiltre> : !q.agreges ? <Vide maillon={m} /> : (
          <>
            <p className="lp-sous">
              Sur les {formatNumber(q.mesurables)} scrutins où le quorum du groupe est atteint{mot ? '' : `, sur ${formatNumber(q.agreges)}`}
            </p>
            <div aria-label="Filtrer la liste par part" className="lp-trois" role="group">
              {Object.entries(PARTS).map(([cle, part]) => (
                <button
                  aria-label={`${valeurs[cle]} ${part.lib}`}
                  aria-pressed={filtre === cle}
                  className={`lp-part ${part.classe}`}
                  key={cle}
                  onClick={() => basculer(cle)}
                  style={{ flex: `${valeurs[cle]} 1 0` }}
                  type="button"
                />
              ))}
            </div>
            <div className="lp-trois-cles">
              {Object.entries(PARTS).map(([cle, part]) => (
                <button aria-pressed={filtre === cle} key={cle} onClick={() => basculer(cle)} type="button">
                  <i className={`lp-part ${part.classe}`} /><b className="lp-num">{formatNumber(valeurs[cle])}</b> {part.lib}
                </button>
              ))}
            </div>
            <p className="lp-sous">
              {filtre ? PARTS[filtre].titre : mot ? 'Tous les scrutins' : 'Les plus partagés'} <span className="lp-sous-regle">· {LAST_READING_LABEL}</span>
            </p>
            {dernieres.length === 0 ? (
              <p className="lp-rien">Aucune dernière lecture d'un texte dans cette part.</p>
            ) : dernieres.slice(0, mot ? undefined : montres).map(([id, po, co, ab]) => (
              <Scrutin abstention={ab} contre={co} id={id} key={id} pour={po} scrutins={m.scrutins} />
            ))}
            {!mot && dernieres.length > montres && (
              <button className="lp-plus" onClick={() => setMontres(montres + 20)} type="button">
                et {formatNumber(dernieres.length - montres)} autres textes
              </button>
            )}
            {reste.length > 0 && (
              <details className="lp-tous" open={Boolean(mot)}>
                <summary>Lectures antérieures, amendements, articles et motions — {formatNumber(reste.length)} scrutins</summary>
                <Repli entrees={reste} scrutins={m.scrutins} />
              </details>
            )}
          </>
        )}
      </div>
    </Section>
  );
}

function Repli({ entrees, scrutins }) {
  const [montres, setMontres] = useState(10);
  return (
    <>
      {entrees.slice(0, montres).map(([id, po, co, ab]) => (
        <Scrutin abstention={ab} contre={co} id={id} key={id} pour={po} scrutins={scrutins} />
      ))}
      {entrees.length > montres && (
        <button className="lp-plus" onClick={() => setMontres(montres + 30)} type="button">
          et {formatNumber(entrees.length - montres)} autres
        </button>
      )}
    </>
  );
}

/* ── § 5 — avec qui ils votent ────────────────────────────────────────────────
 *
 * Position majoritaire du groupe face à celle de chaque autre, sur la DERNIÈRE
 * lecture de chaque texte (relecture du 11/09/2026), là où les deux atteignent
 * leur quorum. Rangés par nombre de textes communs, puis — à base égale
 * seulement — par votes dans le même sens (relecture du 11/09/2026). Chaque
 * groupe mène à SA lignée ; chaque segment déroule ses textes. */
const NATURES = [
  { cle: 'meme_sens', classe: 'lp-part--une' },
  { cle: 'nuance', classe: 'lp-part--nuance' },
  { cle: 'oppose', classe: 'lp-part--oppose' },
];
const LIBELLES_NATURE = { meme_sens: 'même sens', nuance: 'nuance', oppose: 'sens opposé' };

function AvecQuiIlsVotent({ lignee }) {
  const { mot } = useContext(Filtre);
  const [m, index, setIndex] = useMaillon(lignee);
  const [ouvert, setOuvert] = useState(null);
  const lignes = (m.convergences || []).filter((a) => a.communs > 0);
  /* UNE SEULE ÉCHELLE pour toutes les lignes (relecture du 11/09/2026) : la
   * barre la plus longue est le groupe qui partage le plus de textes, et les
   * autres raccourcissent d'autant. Ramener chaque barre à toute la largeur
   * faisait lire 48 et 58 textes communs comme la même base — une barre
   * « normalisée à effet visuel », ce que le DESIGN_SYSTEM §5 interdit. */
  const communsMax = Math.max(1, ...lignes.map((a) => a.communs));
  const basculer = (sigle, nature) => setOuvert(ouvert?.sigle === sigle && ouvert.nature === nature ? null : { sigle, nature });

  return (
    <Section
      critere="Position du groupe face à celle de chaque autre, sur la dernière lecture de chaque texte, quorum atteint des deux côtés."
      numero="5"
      pied={lignes.length ? `${LAST_READING_LABEL} · rangés par nombre de textes communs, puis de votes dans le même sens` : null}
      renvoi={{ ancre: 'convergences', texte: 'Voter dans le même sens n’est pas s’entendre' }}
      titre="Avec qui ils votent"
    >
      <Navigation
        index={index}
        lignee={lignee}
        onIndex={(i) => { setIndex(i); setOuvert(null); }}
        poids={(x) => (x.convergences || []).reduce((a, c) => a + c.communs, 0)}
        unite="textes comparés"
        uniteSingulier="texte comparé"
      />
      <div className="lp-carte">
        <Etiquette />
        <TeteDePeriode maillon={m} />
        {m.convergences && mot && lignes.length === 0 ? <VideFiltre>Aucun texte comparé dont l’intitulé contient</VideFiltre> : !m.convergences ? <Vide maillon={m} /> : lignes.length === 0 ? (
          <p className="lp-rien">Aucun texte en dernière lecture où ce groupe et un autre atteignent tous deux leur quorum.</p>
        ) : (
          <>
            <div className="lp-natures">
              {NATURES.map((n) => (
                <span key={n.cle}><i className={`lp-part ${n.classe}`} />{n.cle === 'nuance' ? 'nuance — abstention face à pour ou contre' : LIBELLES_NATURE[n.cle]}</span>
              ))}
            </div>
            {lignes.map((a) => {
              const valeurs = Object.fromEntries(a.natures.map((n) => [n.cle, n.valeur]));
              const actif = ouvert?.sigle === a.sigle ? ouvert.nature : null;
              return (
                <div className="lp-accord" key={a.sigle}>
                  <span className="lp-accord-sigle">
                    {a.lignee ? <Link className="lp-lien" to={`/groupes/${a.lignee}`}>{a.sigle}</Link> : a.sigle}
                    <small>{a.ligneeNom || a.nom}</small>
                  </span>
                  <div>
                    <div className="lp-accord-barre" style={{ width: `${((100 * a.communs) / communsMax).toFixed(1)}%` }}>
                      {NATURES.map((n) => (
                        <button
                          aria-label={`${valeurs[n.cle] || 0} ${LIBELLES_NATURE[n.cle]}`}
                          aria-pressed={actif === n.cle}
                          className={`lp-part ${n.classe}`}
                          key={n.cle}
                          onClick={() => basculer(a.sigle, n.cle)}
                          style={{ flex: `${valeurs[n.cle] || 0} 1 0` }}
                          type="button"
                        />
                      ))}
                    </div>
                    <div className="lp-accord-cles">
                      {NATURES.map((n) => (
                        <button aria-pressed={actif === n.cle} key={n.cle} onClick={() => basculer(a.sigle, n.cle)} type="button">
                          {LIBELLES_NATURE[n.cle]} <b className="lp-num">{formatNumber(valeurs[n.cle] || 0)}</b>
                        </button>
                      ))}
                      {a.autres > 0 && <span>autres <b className="lp-num">{formatNumber(a.autres)}</b></span>}
                    </div>
                  </div>
                  <span className="lp-accord-n">
                    <b className="lp-num">{formatNumber(a.communs)}</b>
                    <small>textes communs</small>
                  </span>
                  {actif && <TextesCompares autre={a.sigle} entrees={a.scrutins[actif] || []} moi={m.sigle} scrutins={m.scrutins} />}
                  {!actif && mot && <TextesCompares autre={a.sigle} entrees={NATURES.flatMap((n) => a.scrutins[n.cle] || []).concat(a.scrutins.autres || [])} moi={m.sigle} scrutins={m.scrutins} />}
                </div>
              );
            })}
          </>
        )}
      </div>
    </Section>
  );
}

function TextesCompares({ entrees, scrutins, moi, autre }) {
  const [montres, setMontres] = useState(15);
  const pastille = (position) => {
    const st = styleForPosition(position);
    return <span className="lp-pos" style={{ background: st.color || undefined }}>{st.label}</span>;
  };
  return (
    <div className="lp-deroule lp-deroule--large">
      {entrees.slice(0, montres).map(([id, sienne, lautre]) => {
        const s = scrutins[id] || {};
        return (
          <div className="lp-deroule-ligne" key={id}>
            <span className="lp-deroule-date lp-num">{court(s.date)}</span>
            <span className="lp-deroule-titre"><LienSource url={s.sourceUrl}>{s.texte || 'Intitulé non publié'}</LienSource></span>
            <span className="lp-deroule-n">{moi} {pastille(sienne)} · {autre} {pastille(lautre)}</span>
          </div>
        );
      })}
      {entrees.length > montres && (
        <button className="lp-plus" onClick={() => setMontres(montres + 30)} type="button">
          et {formatNumber(entrees.length - montres)} autres textes
        </button>
      )}
    </div>
  );
}

/* ── § 6 — ce qu'on n'a pas pu lire ──────────────────────────────────────────
 *
 * La même section que la fiche candidat, et le même partage (#328) : ce qui
 * est vrai de tout le corpus — les bornes de source, les textes portés non
 * collectés pour les membres, la carrière écartée des agrégats — est dit UNE
 * fois, sur `/couverture` et sous `/methodologie#couverture`. Une limite de
 * source écrite sous le nom d'un groupe se lirait comme une limite de ce
 * groupe. Ne reste ici que ce que CHAQUE fiche signale d'elle-même, rangé par
 * liste dans l'ordre des sections, maillon par maillon du plus récent au plus
 * ancien — comme la liste de « En bref ».
 *
 * Une lignée sans signalement le dit en une ligne : une section absente se
 * lirait comme un oubli. */
function CeQuOnNaPasPuLire({ lignee }) {
  const parListe = Object.keys(LISTES_SIGNALEES)
    .map((cle) => ({
      cle,
      lignes: [...lignee.maillons].reverse().flatMap((m) => (m.signalements || [])
        .filter((s) => s.liste === cle)
        .map((s) => ({ maillon: m, texte: s.texte }))),
    }))
    .filter((l) => l.lignes.length);
  const total = parListe.reduce((n, l) => n + l.lignes.length, 0);

  return (
    <Section
      critere="Les limites propres aux fiches de ces groupes, liste par liste."
      numero="6"
      renvois={[
        { vers: '/sources#frise', texte: 'Ce que le dépôt porte, et depuis quand' },
        { vers: '/methodologie#couverture', texte: 'Pourquoi ces limites se déclarent au lieu de se combler' },
      ]}
      titre="Ce qu’on n’a pas pu lire"
    >
      {total === 0 ? (
        <p className="lp-rien">Aucun signalement propre aux fiches de cette lignée.</p>
      ) : (
        <div className="lp-carte">
          <div className="lp-mat-tete">
            <span className="lp-mat-titre">Ce que la collecte signale</span>
            <span className="lp-mat-totaux lp-num">
              {formatNumber(total)} signalement{total > 1 ? 's' : ''}
            </span>
          </div>
          <dl className="lp-signal">
            {parListe.map((l) => (
              <div className="lp-signal-rang" key={l.cle}>
                <dt style={{ '--lignes': l.lignes.length }}>{LISTES_SIGNALEES[l.cle]}</dt>
                {l.lignes.map(({ maillon, texte }) => (
                  <dd key={`${maillon.id}-${texte}`}>
                    {lignee.maillons.length > 1 && <b>{nomDuMaillon(maillon)}</b>}
                    {texte}
                  </dd>
                ))}
              </div>
            ))}
          </dl>
        </div>
      )}
    </Section>
  );
}

/* Une section par groupe de la lignée qui a des résultats ; tous vides, le plus
 * récent seul, qui dit que le mot ne trouve rien. */
function EnPile({ lignee, cle, Composant }) {
  const ctx = useContext(Filtre);
  const n = lignee.maillons.length;
  let rangs = lignee.maillons.map((_, i) => i).reverse().filter((i) => MAILLON_A_DES_RESULTATS[cle](lignee.maillons[i]));
  if (!rangs.length) rangs = [n - 1];
  return rangs.map((i, k) => (
    <Filtre.Provider key={i} value={{ ...ctx, index: i, avecTete: k === 0, avecPied: k === rangs.length - 1 }}>
      <Composant lignee={lignee} />
    </Filtre.Provider>
  ));
}
export default function LigneeProfile({ lignee, mot = '' }) {
  const aujourdhui = lignee.genereLe || new Date().toISOString().slice(0, 10);
  const noms = [];
  for (const m of lignee.maillons) if (!noms.includes(m.nom)) noms.push(m.nom);
  const chambre = lignee.chambre === 'AN' ? 'Assemblée nationale' : 'Sénat';
  const depuis = lignee.periode.fin && !lignee.maillons[lignee.maillons.length - 1].periode.actif
    ? `du ${jour(lignee.periode.debut)} au ${jour(lignee.periode.fin)}`
    : `depuis le ${jour(lignee.periode.debut)}`;

  return (
    <main className="lp-main">
      <div className="lp-fil">
        Groupes / <strong>{lignee.nom}</strong>
      </div>
      <header className="lp-entete">
        <p className="lp-sourcil">Groupe parlementaire · {chambre}</p>
        <h1>{lignee.nom}</h1>
        <p className="lp-qui">{noms.join(' → ')} · {depuis}</p>
      </header>


      {!mot && (
      <section className="lp-section lp-section--bref" data-section="En bref" id="section-bref">
        <h2 className="lp-section-titre"><span>En bref</span></h2>
        <Frise aujourdhui={aujourdhui} lignee={lignee} />
      </section>
      )}

      <Filtre.Provider value={{ mot, index: null, avecTete: true, avecPied: true }}>
        {!mot && <QuiSontIls lignee={lignee} />}
        {mot ? (
          <>
            <EnPile Composant={SurQuoiIlsParlent} cle="parole" lignee={lignee} />
            <EnPile Composant={CeQuIlsOntPropose} cle="propose" lignee={lignee} />
            <EnPile Composant={CeQuIlsOntVote} cle="vote" lignee={lignee} />
            <EnPile Composant={AvecQuiIlsVotent} cle="avec" lignee={lignee} />
          </>
        ) : (
          <>
            <SurQuoiIlsParlent key={`p-${mot}`} lignee={lignee} />
            <CeQuIlsOntPropose key={`r-${mot}`} lignee={lignee} />
            <CeQuIlsOntVote key={`v-${mot}`} lignee={lignee} />
            <AvecQuiIlsVotent key={`a-${mot}`} lignee={lignee} />
          </>
        )}
      </Filtre.Provider>
      <CeQuOnNaPasPuLire lignee={lignee} />

      <footer className="lp-pied">
        <span>
          {lignee.genereLe ? `Fiche générée le ${jour(lignee.genereLe)}. ` : null}
          Aucun score, aucun classement, aucun taux de présence.
        </span>
        {lignee.licence && <span>{lignee.licence}</span>}
      </footer>
    </main>
  );
}
