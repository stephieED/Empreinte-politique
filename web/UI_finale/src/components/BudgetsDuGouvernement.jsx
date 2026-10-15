import { useRef, useState } from 'react';
import './BudgetsDuGouvernement.css';
import {
  cascadeDesBudgets,
  colonnesDeLaSecuriteSociale,
  colonnesDuBudget,
  listeDesAnnees,
} from '../utils/budgetsGouvernement';

/* ── LES BUDGETS QUE CE GOUVERNEMENT A FAIT VOTER (#1053) ─────────────────────
 *
 * Arbitré en maquette avec la propriétaire le 13/10/2026, version 68 :
 * https://claude.ai/artifact/8qozzLMHSUccspo5d9aL6R
 *
 * DEUX CARTES. Le budget de l'État : ce qu'il reçoit et ce qu'il dépense, en
 * deux colonnes à la même échelle, et à leur droite la cascade des recettes et
 * des dépenses année par année, qui mène au solde. Puis la sécurité sociale,
 * dans les mêmes deux colonnes. Les formes écartées en maquette — schémas de
 * flux, carrés, listes de barres, courbes mensuelles — ne reviennent pas.
 *
 * SEULS LES MONTANTS ENCAISSÉS ET DÉPENSÉS. Aucun montant voté n'est repris :
 * la maquette les montrait, ils ont été retirés le 13/10/2026.
 *
 * Le calcul vit dans `utils/budgetsGouvernement.js` ; ce composant dessine.
 */

/* Deux nuances alternées par côté (demandé le 14/10/2026) : le bleu des
   recettes et l'orange des dépenses, ceux de la cascade. La nuance ne dit rien
   d'un poste, elle le sépare de son voisin. */
const NUANCES = {
  recoit: ['#2f5d93', '#5f8fc8'],
  depense: ['#d0652a', '#f0995c'],
};
const ENCRE = '#17141f';
const GRIS = '#8b8794';
const GRIS_CLAIR = '#b5b3af';
const VIDE = '#e7e4df';
/* La cascade : bleu pour les recettes, orange pour les dépenses (jeu D, retenu
   le 14/10/2026 parmi cinq ; lisible sous daltonisme). */
const CASCADE_RECETTES = '#3b6ea8';
const CASCADE_DEPENSES = '#e07b39';

const milliards = (euros) => `${(euros / 1e9).toLocaleString('fr-FR', {
  minimumFractionDigits: 1, maximumFractionDigits: 1,
})} Md€`.replace('-', '−');
const nombre = (euros) => (Math.abs(euros) / 1e9).toLocaleString('fr-FR', {
  minimumFractionDigits: 1, maximumFractionDigits: 1,
});

function teinteDe(ligne, cote, rang) {
  if (ligne.vide) return VIDE;
  if (ligne.gris) return GRIS;
  if (ligne.pale) return GRIS_CLAIR;
  return NUANCES[cote][rang % 2];
}

/* « En milliards d'euros » ou « Pour 100 € » : la même figure, d'autres nombres. */
function Bascule({ sur100, onChange, libelle100 }) {
  return (
    <div aria-label="Unité des montants" className="adg-filtres" role="group">
      <button aria-pressed={!sur100} className={`adg-bouton${sur100 ? '' : ' adg-bouton--actif'}`}
        onClick={() => onChange(false)} type="button">
        En milliards d’euros
      </button>
      <button aria-pressed={sur100} className={`adg-bouton${sur100 ? ' adg-bouton--actif' : ''}`}
        onClick={() => onChange(true)} type="button">
        {libelle100}
      </button>
    </div>
  );
}

/* ── Deux colonnes empilées, à la même échelle ─────────────────────────────── */

/* L'écart entre deux lignes d'étiquettes. */
const ECART = 14;

/* Place des étiquettes sans chevauchement, chacune au plus près de sa cible
   `vise` : les étiquettes trop proches forment un groupe centré sur la moyenne
   de leurs cibles, et deux groupes qui se touchent fusionnent. Écrit `ty`. */
export function ecarter(items, ecart, plancher = -Infinity) {
  const groupes = [];
  items.forEach((it) => {
    groupes.push({ items: [it], somme: it.vise });
    for (;;) {
      const g = groupes[groupes.length - 1];
      g.debut = Math.max(plancher, g.somme / g.items.length - ((g.items.length - 1) * ecart) / 2);
      const p = groupes[groupes.length - 2];
      if (!p || p.debut + p.items.length * ecart <= g.debut) break;
      p.items.push(...g.items);
      p.somme += g.somme;
      groupes.pop();
    }
  });
  groupes.forEach((g) => g.items.forEach((it, k) => { it.ty = g.debut + k * ecart; }));
}

function Colonne({ lignes, x, gauche, titre, total, echelle, haut, largeur, motif, sur100, centre, montrer }) {
  const ordre = [...lignes].sort((a, b) => (b.hachure || b.vide ? 1 : 0) - (a.hachure || a.vide ? 1 : 0));
  const complement = ordre.find((l) => l.hachure || l.vide);
  const elements = [];
  let yTitre = null;
  const ancre = gauche ? 'end' : 'start';
  const xTexte = gauche ? x - 10 : x + largeur + 10;
  // La colonne la plus courte est complétée en haut : son total s'écrit à sa
  // vraie hauteur, sur un trait.
  if (complement) {
    const yBas = haut + complement.montant * echelle;
    const court = complement.montant * echelle < 34;
    yTitre = court ? yBas + 15 : yBas - 6;
    elements.push(
      <line key="trait" stroke={ENCRE} strokeWidth={1.2} x1={gauche ? x - 150 : x}
        x2={gauche ? x + largeur : x + largeur + 150} y1={yBas} y2={yBas} />,
      <text className="bdg-col-titre" key="titre" textAnchor={ancre} x={xTexte} y={yTitre}>
        {`${titre} · ${total}`}
      </text>,
    );
  } else if (centre) {
    elements.push(
      <text className="bdg-col-titre" key="titre" textAnchor="middle" x={x + largeur / 2} y={16}>{titre}</text>,
      <text className="bdg-col-total" key="total" textAnchor="middle" x={x + largeur / 2} y={31}>{total}</text>,
    );
  } else {
    elements.push(
      <text className="bdg-col-titre" key="titre" textAnchor={gauche ? 'end' : 'start'} x={gauche ? x + largeur : x} y={16}>{titre}</text>,
      <text className="bdg-col-total" key="total" textAnchor={gauche ? 'end' : 'start'} x={gauche ? x + largeur : x} y={31}>{total}</text>,
    );
  }
  // Chaque étiquette vise le milieu de son bloc. Quand des blocs fins se
  // suivent, leurs étiquettes s'écartent AUTOUR de leur groupe — vers le haut
  // comme vers le bas —, au lieu d'être toutes repoussées vers le bas : sinon
  // les dernières finissent loin de leur bloc.
  const blocs = [];
  let y = haut;
  ordre.forEach((l) => {
    const h = l.montant * echelle;
    blocs.push({ l, y, h, vise: y + h / 2 + 4 });
    y += h;
  });
  const enCompl = blocs.filter((b) => b.l === complement);
  const autres = blocs.filter((b) => b.l !== complement);
  enCompl.forEach((b) => { b.ty = b.h < 34 && yTitre !== null ? b.y + b.h / 2 + 1 : b.vise; });
  // Sous le titre posé sur le trait, la place est prise : la première
  // étiquette ne remonte pas au-dessus.
  const plancher = complement && yTitre !== null ? yTitre + 15 : -Infinity;
  ecarter(autres, ECART, plancher);
  let rang = 0;
  blocs.forEach(({ l, y: yb, h, ty, vise }) => {
    const teinte = l.hachure ? `url(#${motif})` : teinteDe(l, gauche ? 'recoit' : 'depense', rang);
    // Un poste trop fin pour se voir ne compte pas dans l'alternance : sinon ses
    // deux voisins prendraient la même nuance et se confondraient.
    if (!l.hachure && !l.gris && !l.pale && !l.vide && h >= 3) rang += 1;
    const valeur = sur100 ? (l.euros < 1 ? 'moins de 1 €' : `${l.euros} €`) : milliards(l.montant);
    // Une étiquette déplacée est reliée à son bloc par un trait coudé.
    const decalee = Math.abs(ty - vise) > 3;
    const xBord = gauche ? x : x + largeur;
    const xCoude = gauche ? x - 6 : x + largeur + 6;
    // La barre et son libellé ouvrent la même bulle, au survol comme au toucher.
    const ouvrir = (e) => montrer(l, e);
    elements.push(
      <g className="bdg-poste" key={`p-${l.nom}`} onClick={ouvrir} onMouseLeave={() => montrer(null)} onMouseMove={ouvrir}>
        <rect fill={teinte} height={Math.max(h - 2, 1)} rx={2} width={largeur} x={x} y={yb + 1} />
        {decalee && (
          <polyline className="bdg-renvoi" fill="none"
            points={`${xBord},${vise - 4} ${xCoude},${vise - 4} ${xTexte + (gauche ? 4 : -4)},${ty - 4}`} />
        )}
        <text className="bdg-ligne" textAnchor={ancre} x={xTexte} y={ty}>
          <tspan>{`${l.nom} `}</tspan>
          <tspan className="bdg-valeur">{valeur}</tspan>
        </text>
      </g>,
    );
  });
  return elements;
}

function DeuxColonnes({ donnees, titres, sur100, geometrie, motif, centre, libelle }) {
  const { largeurTotale, xGauche, xDroite, largeur } = geometrie;
  const [survol, setSurvol] = useState(null);
  const boite = useRef(null);
  const montrer = (ligne, e) => {
    if (!ligne) { setSurvol(null); return; }
    const cadre = boite.current.getBoundingClientRect();
    setSurvol({ ligne, x: e.clientX - cadre.left, y: e.clientY - cadre.top, largeur: cadre.width });
  };
  const haut = 44;
  const hauteur = 440;
  const echelle = hauteur / donnees.total;
  const totalGauche = sur100 ? `${donnees.recuPour100} €` : milliards(donnees.recu);
  const totalDroite = sur100 ? `${donnees.versePour100} €` : milliards(donnees.verse);
  return (
    // La bulle se pose hors du cadre qui défile : elle n'y serait pas coupée.
    <div className="bdg-ancre" onMouseLeave={() => setSurvol(null)} ref={boite}>
      <div className="bdg-defile">
      <svg aria-label={libelle} className="bdg-colonnes-svg" height={haut + hauteur + 14} role="img"
        viewBox={`0 0 ${largeurTotale} ${haut + hauteur + 14}`} width={largeurTotale}>
        <defs>
          <pattern height={6} id={motif} patternTransform="rotate(45)" patternUnits="userSpaceOnUse" width={6}>
            <rect fill="#f2f0ed" height={6} width={6} />
            <rect fill={ENCRE} height={6} width={2.4} />
          </pattern>
        </defs>
        {Colonne({ centre, echelle, gauche: true, haut, largeur, lignes: donnees.recoit, montrer, motif, sur100,
          titre: titres[0], total: totalGauche, x: xGauche })}
        {Colonne({ centre, echelle, gauche: false, haut, largeur, lignes: donnees.depense, montrer, motif, sur100,
          titre: titres[1], total: totalDroite, x: xDroite })}
      </svg>
      </div>
      {survol && (
        <div className="bdg-bulle" role="status"
          style={{ left: Math.min(survol.x + 14, survol.largeur - 330), top: survol.y + 14 }}>
          <b>{survol.ligne.nom}</b>
          <span className="bdg-bulle-total">{milliards(survol.ligne.montant)}</span>
          {survol.ligne.detail?.length > 0 && (
            <ul>
              {survol.ligne.detail.map((d) => (
                <li key={d.nom}><span>{d.nom}</span><b>{milliards(d.montant)}</b></li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

/* ── La cascade, année par année ───────────────────────────────────────────── */

function Cascade({ exercices }) {
  const { annees } = cascadeDesBudgets(exercices);
  if (!annees.length) return null;
  const hauts = annees.map((a) => a.depart + a.recettes);
  const bas = annees.map((a) => a.niveau);
  // Échelle bornée à ±400 Md€ au moins : la même sur toutes les fiches tant
  // qu'aucune cascade ne la dépasse.
  const max = Math.max(400e9, Math.ceil(Math.max(...hauts) / 100e9) * 100e9);
  const min = Math.min(-400e9, Math.floor(Math.min(...bas) / 100e9) * 100e9);
  const X0 = 56;
  const PAS = 84;
  const BW = 30;
  const ESP = 6;
  const TOP = 14;
  const HG = ((max - min) / 1e9) * 0.3;
  const W = X0 + annees.length * PAS + 12;
  // Sous l'axe, la place des années, et d'une seconde ligne seulement si un
  // exercice en cours la demande (« janv.–août »).
  const H = TOP + HG + (annees.some((a) => a.periode) ? 41 : 27);
  const y = (v) => TOP + ((max - v) / (max - min)) * HG;
  const grille = [];
  for (let v = min; v <= max; v += 100e9) grille.push(v);

  const barre = (cle, x, v0, v1, teinte, montant, bulle) => {
    const yh = Math.min(y(v0), y(v1));
    const h = Math.max(Math.abs(y(v1) - y(v0)), 1);
    return [
      <rect fill={teinte} height={h} key={`${cle}-r`} rx={3} width={BW} x={x} y={yh}><title>{bulle}</title></rect>,
      h >= 15 && (
        <text className="bdg-casc-nombre" key={`${cle}-n`} pointerEvents="none" textAnchor="middle" x={x + BW / 2} y={yh + h / 2 + 4}>
          {nombre(montant)}
        </text>
      ),
    ];
  };

  return (
    /* La largeur de la cascade, mais jamais plus que sa carte (#867) : le
       cadre est en `content-box`, ses 14 px de marge et son filet s'ajoutent.
       Sur Philippe II (trois exercices, 320 px de dessin), la fiche
       débordait à 391 px pour un écran de 360 ; le dessin défile désormais
       dans son cadre (`.bdg-defile`), comme les colonnes. */
    <div className="bdg-cascade" style={{ maxWidth: `min(${Math.max(W, 230)}px, calc(100% - 30px))` }}>
      <p className="bdg-periode">
        <b>Solde du budget de l’État</b>
      </p>
      <div className="bdg-defile">
        <svg aria-label="Cascade des recettes, des dépenses et du solde du budget de l’État, année par année"
          height={H} role="img" viewBox={`0 0 ${W} ${H}`} width={W}>
          {grille.map((v) => (
            <g key={v}>
              <line stroke={v ? '#e7e4df' : ENCRE} strokeWidth={1} x1={X0} x2={W - 10} y1={y(v)} y2={y(v)} />
              <text className="bdg-casc-axe" textAnchor="end" x={X0 - 8} y={y(v) + 4}>
                {v ? `${v / 1e9} Md€`.replace('-', '−') : '0'}
              </text>
            </g>
          ))}
          {annees.map((a, i) => {
            const xa = X0 + i * PAS + 9;
            const xs = [xa, xa + BW + ESP];
            const s1 = a.depart + a.recettes;
            // Un seul bloc pour les dépenses et ce qui est reversé (demandé le
            // 14/10/2026) : il descend des recettes jusqu'au niveau de l'année.
            const sorties = s1 - a.niveau;
            const nom = a.periode ? `${a.annee}, ${a.periode}` : a.annee;
            return (
              <g key={a.annee}>
                <text className="bdg-casc-an" textAnchor="middle" x={xa + BW + ESP / 2} y={TOP + HG + 22}>{a.annee}</text>
                {a.periode && (
                  <text className="bdg-casc-axe" textAnchor="middle" x={xa + BW + ESP / 2} y={TOP + HG + 37}>{a.periode}</text>
                )}
                {barre('rec', xs[0], a.depart, s1, CASCADE_RECETTES, a.recettes, `Recettes ${nom} : ${milliards(a.recettes)}`)}
                {barre('dep', xs[1], s1, a.niveau, CASCADE_DEPENSES, sorties,
                  `Dépenses ${nom}, reversements compris : ${milliards(sorties)}\ndont dépenses du budget : ${milliards(a.depenses)}\ndont reversé aux collectivités et à l’Union européenne, comptes à part : ${milliards(-a.reste)}\nNiveau atteint : ${milliards(a.niveau)}`)}
                <line stroke="#c4c0b9" strokeWidth={1} x1={xs[0] + BW} x2={xs[1]} y1={y(s1)} y2={y(s1)} />
                {i < annees.length - 1 && (
                  <line stroke="#c4c0b9" strokeWidth={1} x1={xs[1] + BW} x2={xa + PAS} y1={y(a.niveau)} y2={y(a.niveau)} />
                )}
              </g>
            );
          })}
        </svg>
      </div>
      <div className="bdg-legende">
        <span><i style={{ background: CASCADE_RECETTES }} />recettes</span>
        <span><i style={{ background: CASCADE_DEPENSES }} />dépenses</span>
      </div>
    </div>
  );
}

/* Une année que la figure ne peut pas prendre est nommée, jamais tue (§2 règle 5). */
function NonPublie({ annees, quoi }) {
  if (!annees.length) return null;
  return <p className="bdg-nonpub">{`${quoi} non publiées pour ${listeDesAnnees(annees)}.`}</p>;
}

export default function BudgetsDuGouvernement({ exercices }) {
  const [etatSur100, setEtatSur100] = useState(true);
  const [secuSur100, setSecuSur100] = useState(true);
  const etat = colonnesDuBudget(exercices);
  const secu = colonnesDeLaSecuriteSociale(exercices);

  return (
    <>
      <div className="gvp-carte">
        <div className="bdg-rang">
          <h3 className="bdg-titre">Recettes et dépenses du budget de l’État</h3>
          <div className={`bdg-colonnes${etat.annees.length ? '' : ' bdg-colonnes--vide'}`}>
            {etat.annees.length > 0 && (
              <>
                <Bascule libelle100="Pour 100 € dépensés" onChange={setEtatSur100} sur100={etatSur100} />
                <DeuxColonnes donnees={etat} geometrie={{ largeurTotale: 700, xGauche: 250, xDroite: 338, largeur: 52 }}
                  libelle="Ce que l’État reçoit et ce qu’il dépense par mission, en deux colonnes" motif="bdg-hachure-etat"
                  sur100={etatSur100} titres={['Ce que l’État reçoit', 'Ce que l’État dépense']} />
              </>
            )}
            <NonPublie annees={etat.sansDetail} quoi="Dépenses par mission" />
          </div>
          <Cascade exercices={exercices} />
        </div>
      </div>

      <div className="gvp-carte">
        <h3 className="bdg-titre">Recettes et dépenses de la sécurité sociale</h3>
        {secu.annees.length > 0 && (
          <>
            <Bascule libelle100="Pour 100 €" onChange={setSecuSur100} sur100={secuSur100} />
            <DeuxColonnes centre donnees={secu} geometrie={{ largeurTotale: 940, xGauche: 300, xDroite: 490, largeur: 70 }}
              libelle="Ce que les caisses de sécurité sociale reçoivent et ce qu’elles versent, en deux colonnes"
              motif="bdg-hachure-secu" sur100={secuSur100} titres={['Ce que les caisses reçoivent', 'Ce qu’elles versent']} />
          </>
        )}
        <NonPublie annees={secu.sansDetail} quoi="Recettes et dépenses" />
      </div>
    </>
  );
}
