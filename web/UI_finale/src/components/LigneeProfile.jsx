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
 * Les règles de forme (DESIGN_SYSTEM §6 bis) y sont appliquées. Depuis la
 * revue d'ergonomie du 02/10/2026, ce qui dit comment lire une section est
 * dans la BULLE de son titre, comme sur la fiche candidat : une phrase, une
 * note, « Lire la méthode ». Les phrases sous les titres, les pieds et les
 * renvois sont partis — `docs/decisions/revue-ux-de-la-fiche-de-groupe.md`.
 */
import { createContext, useContext, useMemo, useRef, useState } from 'react';
import { Condition, EtiquetteFiltre, PeriodeContext } from './Recherche';
import { Link } from 'react-router-dom';
import '../styles/shell.css';
import './LigneeProfile.css';
import { ProposParOrateur, usePaquetExtraits } from './ExtraitsDuDebat';
import { getPaquetExtraitsMaillon, getParolesMaillon } from '../data';
import { NATURES_DE_PAROLE, debatsSousSelection } from '../utils/paroleDeGroupe';
import { paquetDe } from '../utils/extraits';
import { SUJET_NON_PUBLIE } from '../utils/sujetIntervention.js';
import { motsDuFiltre } from '../utils/filtreIntitule';
import NavigationPeriodes from './NavigationPeriodes';
import InfoBulle from './InfoBulle';
import { useReplieAuClicDehors } from '../hooks/useReplieAuClicDehors';
import { ListeVide } from './Lecture';
import { LAST_READING_LABEL, formatNumber, styleForPosition, pageDuJeuDeDonnees } from '../utils/lecture';
import { MAILLON_A_DES_RESULTATS } from '../utils/filtreLignee';
import { cumulerTypes, LISTES_SIGNALEES, motifDePosture, ORDRE_PASSAGES, PASSAGES, QUALITES_TEXTE, textesDesQualites } from '../utils/lignee';
import { ListeCascade } from './CascadeTextes';
import { CarresTextes } from './CarresTextes';
import { MATIERE_NON_ETABLIE, textesPortes } from '../utils/profilCandidat';
import { teinteCommission } from '../utils/commissions';

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
/* `filtreActif` : un mot OU une période (#1074) — la fiche se comporte alors de
 * la même façon, et c'est lui que les conditions lisent, jamais le mot seul. */
const Filtre = createContext({ mot: '', filtreActif: false, index: null, avecTete: true, avecPied: true });
function Etiquette() {
  const { mot } = useContext(Filtre);
  return <EtiquetteFiltre mot={mot} />;
}
function VideFiltre({ quoi, critere }) {
  const { mot } = useContext(Filtre);
  return <p className="cp-filtre-vide">{quoi}<Condition critere={critere} mot={mot} />.</p>;
}
/* LES TEXTES DES BULLES, tels que la propriétaire les a arrêtés le 02/10/2026,
 * un par un, sur maquette. La phrase dit ce que la section montre et ce qui la
 * range ; la note aide à ne pas mal lire la figure. Les recopier dans
 * `tests/test_revue_ergonomie_fiche_groupe.py` est voulu : une reformulation
 * « pour améliorer » doit échouer.
 *
 * « En bref » : la note finit par « en comparant leurs membres » depuis que
 * le run calcule le rattachement (#1168, lot 3).
 *
 * « Sur quoi ils ont pris la parole » a DEUX ÉTATS. Sa figure et sa bulle
 * arrêtées comptent des prises de parole, d'où l'on retire la présidence de
 * séance — ce que seul le champ `role_seance` permet (#1169). Tant que le
 * corpus construit ne le porte pas, la section garde sa figure d'avant, avec
 * sa phrase, son pied et son renvoi ; dès qu'il le porte, elle prend la
 * nouvelle (`utils/paroleDeGroupe.js`). */
const LIRE_LA_METHODE = 'Lire la méthode →';
/* S'ajoute à la note d'« En bref » quand le groupe de la législature en cours
 * porte « Posture non déclarée » — la phrase de la fiche de gouvernement, mot
 * pour mot (propriétaire, 04/10/2026). */
const NOTE_MAJORITE_NON_DITE = 'L’Assemblée nationale ne dit quel groupe est majoritaire qu’une fois la législature achevée.';
const BULLES = {
  enBref: {
    phrase: 'L’histoire du groupe à l’Assemblée : ses noms, ses effectifs, sa position face au gouvernement.',
    note: 'Note : D’une législature à la suivante, l’Assemblée ne dit pas quel groupe succède à quel autre. Empreinte politique établit ce lien en comparant leurs membres.',
    liens: [{ libelle: LIRE_LA_METHODE, vers: '/methodologie#lignee' }],
  },
  quiSontIls: {
    phrase: 'L’évolution de la composition du groupe d’une législature à la suivante et sous chacun de ses noms successifs.',
    note: 'Note : Sont comptés tous les députés passés par le groupe pendant la législature, même brièvement.',
    liens: [{ libelle: LIRE_LA_METHODE, vers: '/methodologie#lignee' }],
  },
  textes: {
    phrase: 'Les textes de loi portés par des membres du groupe, comme auteurs ou comme rapporteurs, à l’étape qu’ils ont atteinte.',
    note: 'Note : Seuls les textes examinés en commission sont affichés. Un texte arrêté à une étape n’est pas nécessairement rejeté.',
    liens: [{ libelle: LIRE_LA_METHODE, vers: '/methodologie#depots' }],
  },
  amendements: {
    phrase: 'Les amendements des membres du groupe, par matière et par texte amendé.',
    note: 'Note : Le nombre d’amendements seul peut tromper. Chaque segment d’une barre est un texte amendé ; sa largeur est le nombre d’amendements déposés sur ce texte.',
    liens: [{ libelle: LIRE_LA_METHODE, vers: '/methodologie#depots' }],
  },
  paroles: {
    phrase: 'Les prises de parole des membres du groupe à l’Assemblée, par législature, par nature et par débat.',
    note: 'Note : Une prise de parole peut tenir en quelques mots.',
    liens: [{ libelle: LIRE_LA_METHODE, vers: '/methodologie#paroles' }],
  },
  vote: {
    phrase: 'Les scrutins où le groupe a voté d’une seule voix, et ceux où ses membres se sont partagés, par législature.',
    note: 'Note : « Quorum atteint » : au moins la moitié des membres du groupe a voté. « D’une seule voix » : toutes les positions exprimées vont dans le même sens.',
    liens: [{ libelle: LIRE_LA_METHODE, vers: '/methodologie#cohesion' }],
  },
  avecQui: {
    phrase: 'La position du groupe comparée à celle de chaque autre groupe, texte par texte, par législature.',
    note: 'Note : Voter dans le même sens n’est pas s’entendre : deux groupes peuvent rejeter un texte pour des raisons opposées. « Nuance » : l’un des deux groupes s’est abstenu.',
    liens: [{ libelle: LIRE_LA_METHODE, vers: '/methodologie#convergences' }],
  },
  couverture: {
    phrase: 'Les limites de cette fiche : ce que les sources ne disent pas sur ces groupes.',
    note: 'Note : Une information absente de cette fiche n’a pas été trouvée dans les sources. Cela ne veut pas dire qu’il ne s’est rien passé.',
    liens: [
      { libelle: 'Sources et couvertures →', vers: '/sources#frise' },
      { libelle: LIRE_LA_METHODE, vers: '/methodologie#couverture' },
    ],
  },
};

/* LA BULLE EST À CÔTÉ DU TITRE, PAS DEDANS — la règle de la fiche candidat :
 * dans le `h2`, son bouton entrerait dans le nom que la section annonce à un
 * lecteur d'écran. Une section qui porte une bulle n'écrit plus de critère ;
 * `critere`, `pied` et `renvoi` restent pour la seule section qui n'a pas
 * encore la sienne. */
function Section({ numero, titre, bulle = null, critere, pied, renvoi, children }) {
  const { avecTete, avecPied } = useContext(Filtre);
  return (
    <section className="lp-section" data-section={avecTete ? titre : undefined} id={avecTete ? `section-${numero}` : undefined} style={avecTete ? undefined : { marginTop: 18 }}>
      {avecTete && (
        <>
          <div className="lp-section-bande">
            <span className="lp-section-numero">{numero}</span>
            <span className="lp-section-trait" />
          </div>
          <div className="lp-section-tete ib-ancre">
            <h2 className="lp-section-titre"><span>{titre}</span></h2>
            {bulle && <InfoBulle sujet={titre} {...bulle} />}
          </div>
          {critere && !bulle && <p className="lp-section-critere">{critere}</p>}
        </>
      )}
      <div className="lp-section-corps">{children}</div>
      {avecPied && pied && <p className="lp-section-pied">{pied}</p>}
      {avecPied && renvoi && (
        <p className="lp-methodo">
          <Link to={`/methodologie#${renvoi.ancre}`}>{renvoi.texte}</Link>
        </p>
      )}
    </section>
  );
}

/* Un pli : une poignée, et ce qu'elle déplie. Comme sur la fiche candidat,
 * c'est un `details` dont l'état est tenu ici, pour qu'un clic ailleurs le
 * replie (`useReplieAuClicDehors`, arrêté pour les fiches de groupe le
 * 02/10/2026). `force` : sous un mot recherché, le pli est déplié d'office et
 * ne se replie pas — c'est la recherche qui l'a ouvert, pas le lecteur. */
function Pli({ titre, force = false, children }) {
  const ref = useRef(null);
  const [ouvert, setOuvert] = useState(false);
  useReplieAuClicDehors(ref, ouvert && !force, () => setOuvert(false));
  return (
    <details className="lp-tous" onToggle={(e) => setOuvert(e.currentTarget.open)} open={ouvert || force} ref={ref}>
      <summary>{titre}</summary>
      {children}
    </details>
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
      sansPosition
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
  // La liste : un groupe à la fois, et un clic hors de la carte la replie.
  const carte = useRef(null);
  const [rang, setRang] = useState(null);
  useReplieAuClicDehors(carte, rang != null, () => setRang(null));
  const lus = lignee.couverture?.profils_lus;

  return (
    <Section
      bulle={BULLES.quiSontIls}
      numero="1"
      titre="Qui sont-ils"
    >
      <div className="lp-carte" ref={carte}>
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
        {/* CE QUI ÉTAIT LE PIED DE LA SECTION, et qui est un fait : les
            candidats déclarés passés par ces groupes, avec leur fiche. Le
            compte des profils ne s'écrit que s'il en manque — « 448 sur 448 »
            ne disait rien (DESIGN_SYSTEM §6 bis règle 1). */}
        {(candidats.length > 0 || (lus != null && lus < lignee.cumul)) && (
          <p className="lp-carte-faits">
            {candidats.length > 0 && (
              <span>
                Candidat{candidats.length > 1 ? 's' : ''} déclaré{candidats.length > 1 ? 's' : ''} :{' '}
                {candidats.map((p, i) => <span key={p.id}>{i > 0 ? ', ' : ''}{nom(p)}</span>)}
              </span>
            )}
            {lus != null && lus < lignee.cumul && (
              <span className="lp-num">{formatNumber(lus)} profils publiés sur {formatNumber(lignee.cumul)} personnes</span>
            )}
          </p>
        )}
        {/* LA LISTE, UN GROUPE À LA FOIS (forme C, retenue le 02/10/2026). Les
            noms étaient en colonnes, une par groupe, tous dépliés d'un coup :
            7 583 px pour les 448 personnes d'Ensemble pour la République. Un
            rang par groupe de la lignée, un seul ouvert ; une personne passée
            par trois groupes figure sous les trois, et c'est son chemin qui se
            lit. Le survol d'un nom allume ce chemin dans la grille, comme un
            point. Aucun champ de recherche, aucun « membre clef » : la fiche
            ne choisit pas qui compte (§2 règle 1). */}
        <div className="lp-rangs">
          {lignee.maillons.map((m, i) => {
            const ouvert = rang === i;
            return (
              <div className="lp-rang" data-ouvert={ouvert || undefined} key={m.id}>
                <button aria-expanded={ouvert} className="lp-rang-poignee" onClick={() => setRang(ouvert ? null : i)} type="button">
                  <span aria-hidden="true" className="lp-chevron">{ouvert ? '▾' : '▸'}</span>
                  <span className="lp-rang-nom">{nomDuMaillon(m)}</span>
                  <span className="lp-rang-n"><b className="lp-num">{formatNumber(m.presents.length)}</b> personnes</span>
                </button>
                {ouvert && (
                  <ul className="lp-rang-noms" onMouseLeave={() => setSurvol(null)}>
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
                )}
              </div>
            );
          })}
        </div>
      </div>
    </Section>
  );
}

/* ── § 2 — sur quoi ils ont pris la parole ─────────────────────────────────── */
function SurQuoiIlsParlent({ lignee }) {
  const [m, index, setIndex] = useMaillon(lignee);
  const { filtreActif, mot } = useContext(Filtre);
  const debut = useContext(PeriodeContext);
  // Un débat ouvert, par maillon : ce qui y a été dit (#1029).
  const [ouvert, setOuvert] = useState(null);
  const carte = useRef(null);
  useReplieAuClicDehors(carte, ouvert != null, () => setOuvert(null));
  const s = filtreActif ? m.sujets : { ...m.sujets, liste: m.sujets.liste.slice(0, 10) };
  /* LES PRISES DE PAROLE COMPTÉES (figure retenue le 02/10/2026) : chargées
   * avec la section, et dessinées seulement si le corpus construit porte le
   * rôle de séance — sans lui, la présidence passerait pour la parole du
   * groupe. Sous un mot ou une période, la section garde sa liste d'avant :
   * c'est elle que la recherche sait réduire. */
  const paroles = usePaquetExtraits(filtreActif ? null : `paroles:${m.id}`, () => getParolesMaillon(m.id));
  if (!filtreActif && paroles?.rolesPublies) {
    return (
      <Section bulle={BULLES.paroles} numero="2" titre="Sur quoi ils ont pris la parole">
        <Navigation index={index} lignee={lignee} onIndex={setIndex} poids={(p) => p.sujets.total} unite="débats" uniteSingulier="débat" />
        <ParolesComptees key={m.id} lignee={lignee} maillon={m} paroles={paroles} />
      </Section>
    );
  }
  return (
    <Section
      critere="Les débats où le plus de membres sont intervenus : des sujets, jamais des positions du groupe."
      numero="2"
      pied={filtreActif ? null : s.liste.length > 0
        ? `${s.liste.length} sur ${formatNumber(s.total)} débats · membres qui y sont intervenus, sur ${formatNumber(s.denominateur)} passés par le groupe`
        : null}
      renvoi={{ ancre: 'paroles', texte: 'D’où viennent ces intitulés' }}
      titre="Sur quoi ils ont pris la parole"
    >
      <Navigation index={index} lignee={lignee} onIndex={setIndex} poids={(p) => p.sujets.total} unite="débats" uniteSingulier="débat" />
      <div className="lp-carte" ref={carte}>
        <TeteDePeriode avecPosture={false} maillon={m} />
        <Etiquette />
        {s.liste.length === 0 && filtreActif ? <VideFiltre critere="dont l’intitulé contient" quoi="Aucun débat" /> : s.liste.length === 0 ? <Vide maillon={m} /> : s.liste.map((t) => {
          const choisi = ouvert === `${m.id}\u0000${t.label}`;
          return (
            <div className="lp-sujet-bloc" key={t.label}>
              <button
                aria-expanded={choisi}
                className="lp-sujet lp-sujet--bouton"
                onClick={() => setOuvert(choisi ? null : `${m.id}\u0000${t.label}`)}
                type="button"
              >
                <span className="lp-sujet-lib">
                  <span aria-hidden="true" className="lp-chevron">{choisi ? '▾' : '▸'}</span>
                  {t.label}
                  {/* Retenu par les propos seuls (#1029). */}
                  {t.parIntitule === false && <span className="lp-sujet-via"> · le mot est dans les propos</span>}
                </span>
                <span className="lp-sujet-n lp-num" title={t.porteursTexte}>
                  <b>{formatNumber(t.porteurs)}</b> <small>/ {formatNumber(t.denominateur)}</small>
                </span>
                <span className="lp-sujet-barre"><i style={{ width: `${((100 * t.porteurs) / Math.max(1, t.denominateur)).toFixed(1)}%` }} /></span>
              </button>
              {choisi && (
                <ProposParOrateur
                  charger={() => getPaquetExtraitsMaillon(m.id, paquetDe(t.label))}
                  cle={`${m.id}:${paquetDe(t.label)}`}
                  debut={debut}
                  mots={motsDuFiltre(mot)}
                  nomDe={(r) => lignee.personnes[r]?.nom ?? '—'}
                  parIntitule={t.parIntitule !== false}
                  saisie={mot}
                  sujet={t.label}
                />
              )}
            </div>
          );
        })}
      </div>
    </Section>
  );
}

/* LA BARRE DÉCOUPÉE PAR MEMBRE, AVEC LES PASTILLES DE NATURE (forme D, retenue
 * le 02/10/2026 sur une idée de la propriétaire : la barre des amendements de
 * la fiche candidat, où chaque segment est un membre). La longueur d'une barre
 * est le nombre de prises de parole dans le débat ; le nombre de segments, les
 * membres intervenus. Les débats sont rangés par nombre de prises de parole.
 *
 * LES SEGMENTS SE TOUCHENT, et deux encres alternent : avec le blanc et les
 * deux pixels au moins de la barre des amendements, 51 membres demandent plus
 * de place que la barre n'en a, et c'est le plus gros segment qui cède. Ici
 * chaque largeur reste exacte.
 *
 * Les pastilles sont celles de la fiche candidat, sous les mêmes mots. Aucune
 * pastille de rôle : la présidence de séance et la parole prononcée comme
 * membre du gouvernement sont retirées en amont, elles ne sont pas la parole
 * du groupe. Aucune nature cochée : toutes. */
function ParolesComptees({ lignee, maillon, paroles }) {
  const [natures, setNatures] = useState(() => new Set());
  const [ouvert, setOuvert] = useState(null);
  const [survol, setSurvol] = useState(null);
  const carte = useRef(null);
  useReplieAuClicDehors(carte, ouvert != null, () => setOuvert(null));
  const vue = useMemo(() => debatsSousSelection(paroles, natures), [paroles, natures]);
  const max = Math.max(1, ...vue.lignes.map((l) => l.paroles));
  const denominateur = maillon.sujets.denominateur;
  const basculer = (k) => {
    const suivantes = new Set(natures);
    if (suivantes.has(k)) suivantes.delete(k); else suivantes.add(k);
    setNatures(suivantes);
    setOuvert(null);
    setSurvol(null);
  };
  return (
    <div className="lp-carte" ref={carte}>
      <TeteDePeriode avecPosture={false} maillon={maillon} />
      <div className="lp-facette">
        <span className="lp-facette-quoi">Nature <i>— {formatNumber(vue.total)} prise{vue.total > 1 ? 's' : ''} de parole sous la sélection</i></span>
        <div className="lp-chips">
          {NATURES_DE_PAROLE.map((libelle, k) => (
            <button aria-pressed={natures.has(k)} className="lp-chip" disabled={!vue.parNature[k]} key={libelle} onClick={() => basculer(k)} type="button">
              {libelle} <span className="lp-chip-n lp-num">{formatNumber(vue.parNature[k])}</span>
            </button>
          ))}
        </div>
      </div>
      {vue.lignes.length === 0 ? (
        <p className="lp-rien">Aucune prise de parole de cette nature.</p>
      ) : (
        <>
          <span className="lp-facette-quoi">Débat <i>— {formatNumber(vue.lignes.length)} sur {formatNumber(vue.nDebats)} sous la sélection</i></span>
          <div className="lp-mat" onMouseLeave={() => setSurvol(null)}>
            <div className="lp-mr lp-mr--tete">
              <span />
              <span className="lp-mr-rail" />
              <span className="lp-mr-n">prises de parole</span>
              <span className="lp-mr-n">membres</span>
            </div>
            {vue.lignes.map((l) => {
              // « Intitulé non publié » s'ouvre comme les autres lignes (#1178) ;
              // l'italique dit seulement que ce libellé n'est pas un intitulé.
              const sansIntitule = l.label === SUJET_NON_PUBLIE;
              const choisi = ouvert === l.label;
              return (
                <div key={l.label}>
                  <button
                    aria-expanded={choisi}
                    className={`lp-mr lp-mr--cliquable${sansIntitule ? ' lp-mr--nd' : ''}`}
                    onClick={() => setOuvert(choisi ? null : l.label)}
                    type="button"
                  >
                    <span className="lp-mr-lib" title={l.label}>{l.label}</span>
                    <span className="lp-mr-rail">
                      <span className="lp-parole-segments" style={{ width: `${((100 * l.paroles) / max).toFixed(2)}%` }}>
                        {l.segments.map(([orateur, n]) => (
                          <b
                            className={survol?.orateur === orateur ? 'lp-parole-meme' : undefined}
                            key={orateur}
                            onMouseEnter={() => setSurvol({ orateur, n, total: l.paroles, debat: l.label })}
                            style={{ flex: `${n} 1 0` }}
                          />
                        ))}
                      </span>
                    </span>
                    <span className="lp-mr-n">{formatNumber(l.paroles)}</span>
                    <span className="lp-mr-n lp-mr-n--textes">{formatNumber(l.membres)} / {formatNumber(denominateur)}</span>
                  </button>
                  {choisi && (
                    <div className="lp-deroule">
                      <ProposParOrateur
                        charger={() => getPaquetExtraitsMaillon(maillon.id, paquetDe(l.label))}
                        cle={`${maillon.id}:${paquetDe(l.label)}`}
                        nomDe={(r) => lignee.personnes[r]?.nom ?? '—'}
                        parIntitule
                        sujet={l.label}
                      />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
          {/* Le membre survolé se nomme ici, et s'allume dans chaque débat. */}
          <p aria-live="polite" className="lp-chemin">
            {survol ? (
              <><b>{lignee.personnes[survol.orateur]?.nom ?? '—'}</b> · {formatNumber(survol.n)} prise{survol.n > 1 ? 's' : ''} de parole sur {formatNumber(survol.total)} dans « {survol.debat} »</>
            ) : ' '}
          </p>
        </>
      )}
    </div>
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

/* LES TEXTES QU'ILS ONT PORTÉS — un carré par texte, une ligne par rôle
 * (forme C, retenue le 02/10/2026). La figure est celle de la fiche candidat
 * (`CarresTextes.jsx`) et la règle la même (`textesPortes`,
 * utils/profilCandidat.js). Seule change la population : les dossiers portés
 * par les membres du groupe dans la législature, un dossier une fois
 * (`textesDuMaillon`, utils/lignee.js).
 *
 * LES DEUX RÔLES SE LISENT ENSEMBLE, SANS BOUTON. Les pilules « Comme
 * auteurs » / « Comme rapporteurs » filtraient la cascade ; elles sont devenues
 * les deux lignes de la figure. Un texte que le groupe porte aux deux titres
 * figure sur les deux — c'est le même carré, pas deux textes.
 *
 * Sous le seuil de l'examen en commission, rien n'est publié (AGENTS §6). */
function TextesPortes({ maillon }) {
  const { filtreActif } = useContext(Filtre);
  const [sel, setSel] = useState(null);
  const carte = useRef(null);
  useReplieAuClicDehors(carte, sel != null, () => setSel(null));
  const textes = useMemo(() => {
    if (!maillon.textes) return null;
    const retenus = textesDesQualites(maillon.textes, Object.keys(QUALITES_TEXTE));
    const parDossier = new Map(retenus.map((t) => [t.dossier_id, t.commission]));
    return textesPortes(retenus, (dossier) => parDossier.get(dossier) ?? null);
  }, [maillon]);
  /* Le rôle se lit sur le texte du maillon, pas sur celui de la cascade, qui
   * n'en garde qu'un : la clé est l'adresse du dossier, son titre à défaut. */
  const lignes = useMemo(() => {
    const roles = new Map((maillon.textes || []).map((t) => [t.source_url || t.titre, t.roles || {}]));
    return Object.keys(QUALITES_TEXTE)
      .filter((q) => (maillon.textes || []).some((t) => t.roles?.[q]))
      .map((q) => ({ cle: q, libelle: LIBELLES_QUALITE[q], porte: (texte) => Boolean(roles.get(texte.url || texte.titre)?.[q]) }));
  }, [maillon]);
  if (!textes) return null;
  if (filtreActif && !maillon.textes.length) {
    return <div className="lp-carte lp-textes"><Etiquette /><VideFiltre critere="dont l’intitulé contient" quoi="Aucun texte porté" /></div>;
  }
  return (
    <div className="lp-carte lp-textes" ref={carte}>
      <Etiquette />
      <div className="lp-mat-tete ib-ancre">
        <span className="lp-mat-titre">
          Les textes qu'ils ont portés
          <InfoBulle petite sujet="Les textes qu'ils ont portés" {...BULLES.textes} />
        </span>
        <span className="lp-mat-totaux lp-num">
          <b>{formatNumber(textes.publies.length)}</b> publiés · <b>{formatNumber(textes.promulgues)}</b>{' '}
          promulgué{textes.promulgues > 1 ? 's' : ''}
        </span>
      </div>
      {textes.cascade.total > 0 ? (
        <>
          <CarresTextes cascade={textes.cascade} lignes={lignes} onSelection={setSel} selection={sel} />
          {/* L'invitation est celle de la fiche candidat, validée le 01/10/2026 :
              celle de la liste par défaut parle encore de rubans. */}
          <ListeCascade
            cascade={textes.cascade}
            invite="Cliquez un carré, une étape ou une commission pour lire les textes."
            onRaz={sel ? () => setSel(null) : null}
            selection={sel ?? (filtreActif ? { matiere: null, lo: 0, hi: textes.cascade.stades.length - 1 } : null)}
          />
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

/* Les segments d'une ligne : le nombre d'amendements de chacun de ses textes,
 * du plus grand au plus petit — la règle de la fiche candidat. ILS NE SE
 * DÉCOUPENT QUE S'ILS FONT LE TOTAL : sinon la barre dirait une répartition
 * que la donnée ne porte pas, et elle reste d'un seul tenant (§2 règle 5). */
function segmentsParTexte(detail, total) {
  const parTexte = (detail || []).map((d) => d.amendements).sort((a, b) => b - a);
  return parTexte.length && parTexte.reduce((s, n) => s + n, 0) === total ? parTexte : null;
}

function BarreParTexte({ segments, teinte, part }) {
  const width = `${(part * 100).toFixed(1)}%`;
  if (!segments) return <i style={{ background: teinte, width }} />;
  return (
    <span className="lp-mr-segments" style={{ width }}>
      {segments.map((n, k) => (
        // L'index suffit : la liste est triée une fois et ne se réordonne pas.
        <b key={k} style={{ background: teinte, flex: `${n} 1 0` }} />
      ))}
    </span>
  );
}

function TextesAmendes({ detail }) {
  const [montres, setMontres] = useState(TEXTES_MONTRES);
  return (
    <div className="lp-deroule">
      {/* Ce que le pied de la section disait de cette liste, là où elle se lit. */}
      <p className="lp-deroule-ordre">Du plus récemment amendé au plus ancien</p>
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
  const { filtreActif } = useContext(Filtre);
  const [m, index, setIndex] = useMaillon(lignee);
  const types = Object.keys(TYPES_DEPOSANT).filter((t) => m.amendements.parType[t]);
  const [choisis, setChoisis] = useState(['depute']);
  const [ouverte, setOuverte] = useState(null);
  const actifs = types.filter((t) => choisis.includes(t));
  const selection = actifs.length ? actifs : types.slice(0, 1);
  const bloc = cumulerTypes(m.amendements.parType, selection);
  /* UNE COULEUR FIXE PAR COMMISSION (`utils/commissions.js`) : la même sur les
   * carrés des textes portés, juste au-dessus, et sur les trois types de fiche.
   * La teinte suivait le rang du volume dans le groupe (02/10/2026). */
  const carte = useRef(null);
  useReplieAuClicDehors(carte, ouverte != null, () => setOuverte(null));
  const basculer = (t) => {
    // Un bouton au moins reste sélectionné : une vue vide se lirait « aucun amendement ».
    const suivants = selection.includes(t) ? selection.filter((x) => x !== t) : [...selection, t];
    if (suivants.length) { setChoisis(suivants); setOuverte(null); }
  };
  const lignes = bloc ? bloc.lignes.filter((l) => l.amendements > 0) : [];
  const nd = bloc?.nonEtablie ?? null;
  const maxA = Math.max(1, ...lignes.map((l) => l.amendements), nd?.amendements ?? 0);

  return (
    <Section
      numero="3"
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
      {m.textes ? <TextesPortes key={m.id} maillon={m} /> : null}
      <div className="lp-carte" ref={carte}>
        <Etiquette />
        {m.amendementsHorsPeriode ? (
          /* La projection compte les amendements par dossier, sur toute la
             législature : les recompter dans une fenêtre serait inventer (#1074). */
          <p className="cp-note">Les amendements du groupe se comptent par dossier, sur toute la législature : la période ne s’y applique pas.</p>
        ) : !bloc && filtreActif ? <VideFiltre critere="dont l’intitulé contient" quoi="Aucun dossier amendé" /> : !bloc ? <Vide maillon={m} /> : (
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
            <div className="lp-mat-tete ib-ancre">
              {/* « Par matière », et non « Par commission saisie au fond » (#328).
                  L'expression est du jargon parlementaire : la propriétaire, qui
                  connaît ce corpus mieux que quiconque, a demandé ce qu'elle
                  voulait dire. « Matière » est le mot que le produit emploie
                  partout ailleurs, et que la page de méthodologie définit
                  désormais en français courant. Le terme officiel y survit une
                  fois, comme passerelle vers le vocabulaire de la source. */}
              <span className="lp-mat-titre">
                Par matière
                <InfoBulle petite sujet="Les amendements, par matière" {...BULLES.amendements} />
              </span>
              <span className="lp-mat-totaux lp-num">
                <b>{formatNumber(bloc.amendements)}</b> amendements · <b>{formatNumber(bloc.dossiers)}</b> dossiers ·{' '}
                <b>{formatNumber(bloc.adoptes)}</b> adoptés
              </span>
            </div>
            {/* Une absence de donnée se déclare, là où le compte se lit (§2
                règle 5) : c'était une incise du pied de section. */}
            {m.amendements.sansType > 0 && !filtreActif && (
              <p className="lp-carte-faits lp-num">{formatNumber(m.amendements.sansType)} amendements sans type de déposant publié ne figurent pas ici</p>
            )}
            <div className="lp-mat">
              {/* Les cases vides d'en-tête portent la classe des barres qu'elles
                  surplombent : sous 720 px les barres disparaissent, et une case
                  restée décalait toute la ligne d'une colonne. */}
              <div className="lp-mr lp-mr--tete">
                <span />
                <span className="lp-mr-rail" />
                <span className="lp-mr-n">amendements</span>
                <span className="lp-mr-n">textes distincts</span>
              </div>
              {/* LA BARRE DÉCOUPÉE PAR TEXTE (forme A, 02/10/2026) : un segment
                  par texte amendé, large comme le nombre d'amendements déposés
                  dessus — la figure de la fiche candidat. La colonne « ratio
                  par texte » est partie avec elle : la découpe montre ce que le
                  ratio résumait. Mesuré sur Ensemble pour la République,
                  XVIIe : 28 textes sur 237 n'y ont aucun pixel, la propriétaire
                  l'a retenue en le sachant ; le nombre de textes reste écrit
                  au bout de la ligne. */}
              {lignes.map((l) => {
                const ouvert = ouverte === l.commission || filtreActif;
                return (
                  <div key={l.commission}>
                    <button
                      aria-expanded={ouvert}
                      className="lp-mr lp-mr--cliquable"
                      onClick={() => setOuverte(ouvert ? null : l.commission)}
                      type="button"
                    >
                      <span className="lp-mr-lib" title={l.commission}>{l.commission}</span>
                      <span className="lp-mr-rail">
                        <BarreParTexte part={l.amendements / maxA} segments={segmentsParTexte(l.detail, l.amendements)} teinte={teinteCommission(l.commission)} />
                      </span>
                      <span className="lp-mr-n">{formatNumber(l.amendements)}</span>
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
                    <span className="lp-mr-rail">
                      <BarreParTexte part={nd.amendements / maxA} segments={segmentsParTexte(nd.detail, nd.amendements)} teinte={teinteCommission(MATIERE_NON_ETABLIE)} />
                    </span>
                    <span className="lp-mr-n">{formatNumber(nd.amendements)}</span>
                    <span className="lp-mr-n lp-mr-n--textes">{nd.textes ? formatNumber(nd.textes) : '—'}</span>
                  </button>
                  {(ouverte === MATIERE_NON_ETABLIE || filtreActif) && nd.detail.length > 0 && <TextesAmendes detail={nd.detail} />}
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
  const { filtreActif } = useContext(Filtre);
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
  const liste = filtre || !filtreActif
    ? (m.partageListes?.[filtre || 'partages'] || [])
    : [...(m.partageListes?.partages || []), ...(m.partageListes?.une_seule_voix || [])];
  const dernieres = liste.filter(([id]) => m.scrutins[id]?.derniere);
  const reste = liste.filter(([id]) => !m.scrutins[id]?.derniere);
  const basculer = (cle) => { setFiltre(filtre === cle ? null : cle); setMontres(SCRUTINS_MONTRES); };

  return (
    <Section
      bulle={BULLES.vote}
      numero="4"
      titre="Ce qu'ils ont voté"
    >
      <Navigation
        index={index}
        lignee={lignee}
        onIndex={(i) => { setIndex(i); setFiltre(null); setMontres(SCRUTINS_MONTRES); }}
        poids={(x) => (filtreActif ? x.quorum.mesurables : x.quorum.agreges)}
        unite="scrutins"
        uniteSingulier="scrutin"
      />
      <div className="lp-carte">
        <Etiquette />
        <TeteDePeriode maillon={m} />
        {q.agreges && filtreActif && !q.mesurables ? <VideFiltre critere="dont l’intitulé contient" quoi="Aucun scrutin" /> : !q.agreges ? <Vide maillon={m} /> : (
          <>
            <p className="lp-sous">
              Sur les {formatNumber(q.mesurables)} scrutins où le quorum du groupe est atteint{filtreActif ? '' : `, sur ${formatNumber(q.agreges)}`}
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
              {filtre ? PARTS[filtre].titre : filtreActif ? 'Tous les scrutins' : 'Les plus partagés'} <span className="lp-sous-regle">· {LAST_READING_LABEL}</span>
            </p>
            {dernieres.length === 0 ? (
              <p className="lp-rien">Aucune dernière lecture d'un texte dans cette part.</p>
            ) : dernieres.slice(0, filtreActif ? undefined : montres).map(([id, po, co, ab]) => (
              <Scrutin abstention={ab} contre={co} id={id} key={id} pour={po} scrutins={m.scrutins} />
            ))}
            {!filtreActif && dernieres.length > montres && (
              <button className="lp-plus" onClick={() => setMontres(montres + 20)} type="button">
                et {formatNumber(dernieres.length - montres)} autres textes
              </button>
            )}
            {reste.length > 0 && (
              <Pli force={filtreActif} titre={`Lectures antérieures, amendements, articles et motions — ${formatNumber(reste.length)} scrutins`}>
                <Repli entrees={reste} scrutins={m.scrutins} />
              </Pli>
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
 * groupe mène à SA lignée.
 *
 * UN CARRÉ PAR TEXTE (forme B, retenue le 02/10/2026). La ligne portait une
 * barre et, à droite, le nombre de textes communs en gros : un relecteur
 * attentif y a lu « 51 % de proximité » là où la figure disait 9 textes dans
 * le même sens sur 51. Le nombre le plus visible n'était pas celui qui répond
 * au titre (DESIGN_SYSTEM §6 bis règle 8). La base ne s'écrit plus en gros :
 * elle se compte, un carré par texte commun, et reste écrite en petit au bout
 * des trois comptes — un ratio de groupe garde son dénominateur (§2 règle 7).
 *
 * Le survol d'un carré allume le même texte chez chaque groupe et le nomme
 * sous la figure ; le clic déroule les textes de sa part, comme avant. */
const NATURES = [
  { cle: 'meme_sens', classe: 'lp-part--une' },
  { cle: 'nuance', classe: 'lp-part--nuance' },
  { cle: 'oppose', classe: 'lp-part--oppose' },
];
const LIBELLES_NATURE = { meme_sens: 'même sens', nuance: 'nuance', oppose: 'sens opposé' };

function AvecQuiIlsVotent({ lignee }) {
  const { filtreActif } = useContext(Filtre);
  const [m, index, setIndex] = useMaillon(lignee);
  const [ouvert, setOuvert] = useState(null);
  const [survol, setSurvol] = useState(null);
  const carte = useRef(null);
  useReplieAuClicDehors(carte, ouvert != null, () => setOuvert(null));
  const lignes = (m.convergences || []).filter((a) => a.communs > 0);
  const basculer = (sigle, nature) => setOuvert(ouvert?.sigle === sigle && ouvert.nature === nature ? null : { sigle, nature });
  /* Le texte survolé, et la position de chaque groupe sur lui : lu dans les
   * listes déjà servies, rien n'est recalculé. */
  const survole = useMemo(() => {
    if (survol == null) return null;
    let sienne = null;
    const autres = [];
    for (const a of lignes) {
      for (const n of NATURES) {
        const entree = (a.scrutins[n.cle] || []).find(([id]) => id === survol);
        if (entree) { sienne = entree[1]; autres.push([a.sigle, entree[2]]); }
      }
    }
    return { scrutin: m.scrutins[survol] || {}, sienne, autres };
  }, [survol, lignes, m]);
  const pastille = (position) => {
    const st = styleForPosition(position);
    return <span className="lp-pos" style={{ background: st.color || undefined }}>{st.label}</span>;
  };

  return (
    <Section
      bulle={BULLES.avecQui}
      numero="5"
      titre="Avec qui ils votent"
    >
      <Navigation
        index={index}
        lignee={lignee}
        onIndex={(i) => { setIndex(i); setOuvert(null); setSurvol(null); }}
        poids={(x) => (x.convergences || []).reduce((a, c) => a + c.communs, 0)}
        unite="textes comparés"
        uniteSingulier="texte comparé"
      />
      <div className="lp-carte" ref={carte}>
        <Etiquette />
        <TeteDePeriode maillon={m} />
        {m.convergences && filtreActif && lignes.length === 0 ? <VideFiltre critere="dont l’intitulé contient" quoi="Aucun texte comparé" /> : !m.convergences ? <Vide maillon={m} /> : lignes.length === 0 ? (
          <p className="lp-rien">Aucun texte en dernière lecture où ce groupe et un autre atteignent tous deux leur quorum.</p>
        ) : (
          <>
            <div className="lp-natures">
              {NATURES.map((n) => (
                <span key={n.cle}><i className={`lp-part lp-carre ${n.classe}`} />{n.cle === 'nuance' ? 'nuance — abstention face à pour ou contre' : LIBELLES_NATURE[n.cle]}</span>
              ))}
            </div>
            <div onMouseLeave={() => setSurvol(null)}>
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
                      <div className="lp-accord-carres">
                        {NATURES.flatMap((n) => (a.scrutins[n.cle] || []).map(([id]) => (
                          <button
                            aria-label={`${m.scrutins[id]?.texte || 'Intitulé non publié'} — ${LIBELLES_NATURE[n.cle]}`}
                            className={`lp-part lp-carre ${n.classe}${survol === id ? ' lp-carre--meme' : ''}`}
                            key={id}
                            onBlur={() => setSurvol(null)}
                            onClick={() => basculer(a.sigle, n.cle)}
                            onFocus={() => setSurvol(id)}
                            onMouseEnter={() => setSurvol(id)}
                            type="button"
                          />
                        )))}
                      </div>
                      <div className="lp-accord-pied">
                        <div className="lp-accord-cles">
                          {NATURES.map((n) => (
                            <button aria-pressed={actif === n.cle} key={n.cle} onClick={() => basculer(a.sigle, n.cle)} type="button">
                              {LIBELLES_NATURE[n.cle]} <b className="lp-num">{formatNumber(valeurs[n.cle] || 0)}</b>
                            </button>
                          ))}
                          {a.autres > 0 && <span>autres <b className="lp-num">{formatNumber(a.autres)}</b></span>}
                        </div>
                        <span className="lp-accord-base lp-num">{formatNumber(a.communs)} texte{a.communs > 1 ? 's' : ''} commun{a.communs > 1 ? 's' : ''}</span>
                      </div>
                    </div>
                    {actif && <TextesCompares autre={a.sigle} entrees={a.scrutins[actif] || []} moi={m.sigle} scrutins={m.scrutins} />}
                    {!actif && filtreActif && <TextesCompares autre={a.sigle} entrees={NATURES.flatMap((n) => a.scrutins[n.cle] || []).concat(a.scrutins.autres || [])} moi={m.sigle} scrutins={m.scrutins} />}
                  </div>
                );
              })}
            </div>
            {/* Le texte survolé se nomme ici, avec la position de chaque groupe.
                La ligne garde sa hauteur au repos : rien ne saute sous le
                curseur (le motif de « Qui sont-ils »). */}
            <p aria-live="polite" className="lp-texte-survole">
              {survole ? (
                <>
                  <b className="lp-num">{court(survole.scrutin.date)}</b> · <b>{survole.scrutin.texte || 'Intitulé non publié'}</b>
                  <br />
                  {m.sigle} {pastille(survole.sienne)}
                  {survole.autres.map(([sigle, position]) => <span key={sigle}> · {sigle} {pastille(position)}</span>)}
                </>
              ) : ' '}
            </p>
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
      bulle={BULLES.couverture}
      numero="6"
      titre="Ce qu’on n’a pas pu lire"
    >
      {total === 0 ? (
        <p className="lp-rien">Aucun signalement propre aux fiches de ce groupe.</p>
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
  const debut = useContext(PeriodeContext);
  const filtreActif = Boolean(mot) || Boolean(debut);
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


      {!filtreActif && (
      <section className="lp-section lp-section--bref" data-section="En bref" id="section-bref">
        <div className="lp-section-tete ib-ancre">
          <h2 className="lp-section-titre"><span>En bref</span></h2>
          <InfoBulle
            sujet="En bref"
            {...BULLES.enBref}
            note={lignee.maillons.some((m) => !m.periode.fin && m.posture?.valeur === 'non_declaree')
              ? `${BULLES.enBref.note} ${NOTE_MAJORITE_NON_DITE}`
              : BULLES.enBref.note}
          />
        </div>
        <Frise aujourdhui={aujourdhui} lignee={lignee} />
      </section>
      )}

      <Filtre.Provider value={{ mot, filtreActif, index: null, avecTete: true, avecPied: true }}>
        {!filtreActif && <QuiSontIls lignee={lignee} />}
        {filtreActif ? (
          <>
            <EnPile Composant={SurQuoiIlsParlent} cle="parole" lignee={lignee} />
            <EnPile Composant={CeQuIlsOntPropose} cle="propose" lignee={lignee} />
            <EnPile Composant={CeQuIlsOntVote} cle="vote" lignee={lignee} />
            <EnPile Composant={AvecQuiIlsVotent} cle="avec" lignee={lignee} />
          </>
        ) : (
          <>
            <SurQuoiIlsParlent key={`p-${mot}-${debut}`} lignee={lignee} />
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
