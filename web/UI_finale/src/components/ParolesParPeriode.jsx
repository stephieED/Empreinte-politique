/* ── « Ce qu'il a dit », par période politique (#328) ─────────────────────────
 *
 * Le composant ne calcule aucun fait : les périodes, les sujets, les plafonds
 * et la couverture arrivent construits par `utils/parolesParPeriode.js`. Il ne
 * décide ici que ce qui est montré — quelle période, quelles natures, quel
 * sujet, et si le détail est ouvert.
 *
 * Maquette validée le 09/09/2026 (artefact « Ce qu'il a dit, en trois
 * formes »), forme A. Trois entrées croisées, de la plus large à la plus fine :
 *
 *   période politique  →  nature de l'intervention  →  sujet  →  le détail
 *
 * DEUX ÉCHELLES, ET C'EST VOULU. Les COMPTEURS suivent la sélection : ils
 * disent « combien reste-t-il sous ce filtre », donc ils sont le dénominateur
 * de ce qu'on lit et jamais un palmarès (§2 règle 7). Les BARRES gardent le
 * plafond de la fiche, parce qu'elles servent à comparer deux périodes entre
 * elles — un filtre retire de la masse, il ne redimensionne pas. Sur « toutes
 * les périodes », le plafond change et le libellé le dit : une barre
 * d'ensemble ne se compare pas à une barre de période.
 *
 * LE DÉTAIL EST FERMÉ TANT QU'AUCUN SUJET N'EST CHOISI. Ouvrir 3 963
 * interventions d'emblée, c'est publier un mur où le lecteur ne cherche rien —
 * et la première phrase visible deviendrait, de fait, une phrase mise en avant,
 * ce qu'aucune règle ne nous autorise à faire (§2 règle 1).
 */
import { Fragment, useMemo, useState } from 'react';
import { segmentsSurlignes } from '../utils/filtreIntitule';
import { Link } from 'react-router-dom';
import { PAGE_JEU_DE_DONNEES_DEBATS, formatNumber, lienDocumentaire } from '../utils/lecture';
import { libellePosition, TYPES_INTERVENTION } from '../utils/profilCandidat';
import { SUJET_NON_PUBLIE, sujetsDuLot } from '../utils/parolesParPeriode';
import NavigationPeriodes from './NavigationPeriodes';
import './ParolesParPeriode.css';

const jour = (d) => (d ? `${d.slice(8, 10)}/${d.slice(5, 7)}/${d.slice(0, 4)}` : '');
const mois = (d) => (d ? `${d.slice(0, 4)}/${d.slice(5, 7)}` : '');

/* La classe d'une qualité est ÉCRITE, jamais dérivée : `toLowerCase` est
   interdit dans ce composant (#639) parce qu'il ouvre la porte au
   rapprochement de deux libellés voisins. La règle vaut aussi pour une clé
   technique — on ne garde pas un outil en promettant de ne pas s'en servir. */
const CLASSE_QUALITE = {
  AN: 'pp-qualite--an',
  GOUV: 'pp-qualite--gouv',
  PE: 'pp-qualite--pe',
};

const SUJETS_REPLIES = 10;
const PAS_DE_FIL = 25;

/* Le titre nomme CE QU'ON SAIT. Un repère non publié est écrit, jamais escamoté
 * ni comblé par la période voisine — mêmes formules que « Ce qu'il a voté ». */
function titreDePeriode(periode) {
  if (!periode.banc && !periode.gouvernement) return 'Repère non publié';
  const banc = periode.banc ? libellePosition(periode.banc) : 'banc non publié';
  const gouvernement = periode.gouvernement
    ? `gouvernement ${periode.gouvernement}`
    : 'gouvernement non publié';
  return `${banc} · ${gouvernement}`.replace(/^./, (c) => c.toUpperCase());
}

function libelleCourtDePeriode(periode) {
  const banc = periode.banc ? libellePosition(periode.banc) : 'banc non publié';
  return periode.gouvernement ? `${banc} · ${periode.gouvernement}` : banc;
}

/* Les natures, dans le vocabulaire que la fiche emploie déjà — une seule table
 * de libellés pour ce champ, ici comme dans « En bref ». Un type que la table
 * ne connaît pas garde sa clé brute : un libellé inventé serait pire. */
function naturesDuLot(interventions) {
  const compte = new Map();
  for (const i of interventions) compte.set(i.type, (compte.get(i.type) || 0) + 1);

  const connus = new Set(TYPES_INTERVENTION.flatMap((t) => t.cles));
  const lignes = TYPES_INTERVENTION.map(({ cles, label }) => ({
    cle: cles.join('+'),
    cles,
    label,
    n: cles.reduce((s, c) => s + (compte.get(c) || 0), 0),
  }));
  for (const [cle] of compte) {
    if (!connus.has(cle)) lignes.push({ cle, cles: [cle], label: cle || 'Nature non publiée', n: compte.get(cle) });
  }
  return lignes.filter((l) => l.n > 0 || connus.has(l.cles[0]));
}

function Intervention({ i, mot = '' }) {
  return (
    <li className="pp-item">
      <div className="pp-quand">
        {jour(i.date)}
        <em>{i.libelleNature}</em>
      </div>
      <div className="pp-quoi">
        <p className="pp-chemin">
          {i.chemin ? (
            <>
              <b>{i.sujet}</b>
              {i.reste && <span className="pp-reste"> › {i.reste}</span>}
            </>
          ) : (
            <span className="pp-reste">{SUJET_NON_PUBLIE} par la source</span>
          )}
        </p>
        {/* La question au gouvernement dont ce tour fait partie (#1094) : le
            ministère interrogé et la page de la question, lus sur l'acte. */}
        {i.question && (
          <p className="pp-question">
            Question au gouvernement{i.question.ministere ? ` · ${i.question.ministere}` : ''}
            {i.question.lien && (
              <>
                {' · '}
                <a href={i.question.lien} target="_blank" rel="noreferrer">Voir la question ↗</a>
              </>
            )}
          </p>
        )}
        {i.fonction && (
          <p className="pp-qualite">
            prononcé comme <b>{i.fonction}</b>
          </p>
        )}
        {i.verbatim ? (
          <blockquote className="pp-verbatim">
            {mot
              ? segmentsSurlignes(i.verbatim, mot).map((s, k) => (s.marque
                ? <mark className="pp-mot" key={k}>{s.texte}</mark>
                : <Fragment key={k}>{s.texte}</Fragment>))
              : i.verbatim}
          </blockquote>
        ) : (
          <p className="pp-sans-verbatim">
            {i.themeSeul
              ? 'Collecte au thème seul : le verbatim n’a pas été rapporté. Ce n’est pas un silence de la personne.'
              : 'Le compte rendu ne porte pas de verbatim pour cette entrée.'}
          </p>
        )}
        {/* LE LIEN DE LA PRISE DE PAROLE (#1087) : la page de séance, à
            l'ancre de l'intervention — même libellé que sur les fiches de
            gouvernement et de groupe. Une question écrite garde sa page. */}
        {i.lien ? (
          <a className="pp-source" href={i.lien} target="_blank" rel="noreferrer">
            Lire au compte rendu ↗
          </a>
        ) : lienDocumentaire(i.sourceUrl) && (
          <a className="pp-source" href={lienDocumentaire(i.sourceUrl)} target="_blank" rel="noreferrer">
            Source · Assemblée nationale
          </a>
        )}
      </div>
    </li>
  );
}

/* `deplie` (#979) : un mot est tapé dans le filtre de la fiche. Toutes les
 * périodes sont montrées d'emblée, et le fil de tous les sujets s'affiche sans
 * qu'il faille en choisir un — la fiche réduite à ce mot se lit, elle ne se
 * fouille pas. Sans mot, rien ne change. `etiquette` : le rappel du mot, posé
 * en tête du cadre pour qu'une capture de la figure ne le perde pas. */
export default function ParolesParPeriode({
  qualites, plafondPeriode, plafondEnsemble, couverture, deplie = false, etiquette = null, mot = '',
}) {
  /* LA QUALITÉ D'ABORD, LA PÉRIODE ENSUITE (#328).
   *
   * On ne parle pas du même endroit selon qu'on siège à Paris, qu'on gouverne
   * ou qu'on siège à Strasbourg — et les natures elles-mêmes ne se comparent
   * pas : l'explication de vote domine au Parlement européen (683 des 845 chez
   * Emmanuel Maurel), la réaction courte à l'Assemblée. Le sélecteur ne
   * s'affiche que si la fiche porte PLUSIEURS qualités : sur 17 fiches, 13
   * n'en ont qu'une, et lui en montrer une seule serait un dispositif vide. */
  const [qualite, setQualite] = useState(qualites[0]?.qualite ?? null);
  const bloc = qualites.find((q) => q.qualite === qualite) ?? qualites[0];
  const periodes = bloc?.periodes ?? [];
  /* Une législature européenne ne suit pas les gouvernements français : y
     ranger ces interventions produisait le « gouvernement Attal » de Raphaël
     Glucksmann. La sélection des périodes disparaît donc, et le dit. */
  const sansDecoupage = periodes.length === 1 && periodes[0].sansDecoupage;
  const [index, setIndex] = useState(deplie && !sansDecoupage ? null : periodes.length - 1);
  const [natures, setNatures] = useState(() => new Set());
  const [sujet, setSujet] = useState(null);
  const [tousSujets, setTousSujets] = useState(false);
  const [limite, setLimite] = useState(PAS_DE_FIL);

  const indexSur = Math.min(index ?? periodes.length - 1, periodes.length - 1);
  const tout = index === null;
  const lot = useMemo(
    () => (tout ? periodes.flatMap((p) => p.interventions) : periodes[indexSur].interventions),
    [periodes, indexSur, tout],
  );

  const parNature = useMemo(() => naturesDuLot(lot), [lot]);
  const clesRetenues = useMemo(() => {
    const s = new Set();
    for (const l of parNature) if (natures.has(l.cle)) for (const c of l.cles) s.add(c);
    return s;
  }, [parNature, natures]);

  const passeNature = (i) => clesRetenues.size === 0 || clesRetenues.has(i.type);

  /* Chaque facette est comptée sous la sélection de l'AUTRE. C'est ce qui fait
     du chiffre un dénominateur, et non un classement. */
  const naturesAffichees = useMemo(() => {
    const sousSujet = lot.filter((i) => !sujet || (i.sujet || SUJET_NON_PUBLIE) === sujet);
    return naturesDuLot(sousSujet)
      .map((l) => ({ ...l, actif: natures.has(l.cle) }))
      .sort((a, b) => b.n - a.n || a.label.localeCompare(b.label, 'fr'));
  }, [lot, sujet, natures]);

  const sujets = useMemo(() => sujetsDuLot(lot.filter(passeNature)), [lot, clesRetenues]);
  const plafond = tout ? plafondEnsemble : plafondPeriode;

  const visibles = useMemo(
    () =>
      lot
        .filter((i) => passeNature(i) && (sujet ? (i.sujet || SUJET_NON_PUBLIE) === sujet : deplie))
        .slice()
        .reverse(),
    [lot, clesRetenues, sujet, deplie],
  );

  const libelleNature = (type) =>
    TYPES_INTERVENTION.find((t) => t.cles.includes(type))?.label ?? type ?? 'Nature non publiée';

  const changerPeriode = (i) => {
    setIndex(i);
    setSujet(null);
    setTousSujets(false);
    setLimite(PAS_DE_FIL);
  };

  const basculerNature = (cle) => {
    setNatures((s) => {
      const n = new Set(s);
      if (n.has(cle)) n.delete(cle);
      else n.add(cle);
      return n;
    });
    setLimite(PAS_DE_FIL);
  };

  const periodeCourante = tout ? null : periodes[indexSur];
  const sujetsVus = tousSujets ? sujets : sujets.slice(0, SUJETS_REPLIES);

  return (
    <div className="pp">
      {qualites.length > 1 && (
        <div className="pp-qualites" role="group" aria-label="En quelle qualité">
          {qualites.map((q) => (
            <button
              className={`pp-qualite ${CLASSE_QUALITE[q.qualite]}`}
              key={q.qualite}
              type="button"
              aria-pressed={q.qualite === bloc.qualite}
              onClick={() => { setQualite(q.qualite); setIndex(null); }}
            >
              <i aria-hidden="true" />
              {q.libelle}
              <span>· {formatNumber(q.total)}</span>
            </button>
          ))}
        </div>
      )}

      {/* LA SÉLECTION DES PÉRIODES DISPARAÎT, SANS RIEN À LA PLACE.
          Une législature européenne ne suit pas les gouvernements français : y
          ranger ces interventions produisait le « gouvernement Attal » de
          Raphaël Glucksmann. Rien ne remplace le dispositif — ce n'est pas une
          liste vide à expliquer (§2 règle 5), ce sont toutes les interventions,
          simplement sans découpage. */}
      {!sansDecoupage && (
        <NavigationPeriodes
          periodes={periodes}
          index={index}
          onIndex={changerPeriode}
          poids={(p) => p.interventions.length}
          libelle={libelleCourtDePeriode}
          unite="interventions"
          uniteSingulier="intervention"
          avecTout
        />
      )}

      <div className="cp-carte cp-bloc pp-cadre">
        {etiquette}
        <div className="pp-tete">
          <h3 className="pp-titre">
            {tout ? 'Toutes les périodes' : titreDePeriode(periodeCourante)}
          </h3>
          <span className="pp-quand-periode">
            {tout
              ? `${mois(periodes[0].debut)} → ${mois(periodes[periodes.length - 1].fin)} · ${formatNumber(periodes.length)} périodes`
              : `${mois(periodeCourante.debut)} → ${mois(periodeCourante.fin)}${
                  periodeCourante.groupes.length ? ` · ${periodeCourante.groupes.join(', ')}` : ''
                }`}
          </span>
        </div>

        <div className="pp-facette">
          <span className="pp-facette-quoi">
            Nature <i>— {formatNumber(naturesAffichees.reduce((s, l) => s + l.n, 0))} sous la sélection</i>
          </span>
          <div className="pp-chips">
            {naturesAffichees.map((l) => (
              <button
                type="button"
                key={l.cle}
                className="pp-chip"
                aria-pressed={l.actif}
                disabled={l.n === 0}
                onClick={() => basculerNature(l.cle)}
              >
                {l.label} <span className="pp-chip-n">{formatNumber(l.n)}</span>
              </button>
            ))}
            {natures.size > 0 && (
              <button type="button" className="pp-raz" onClick={() => setNatures(new Set())}>
                Tout retirer
              </button>
            )}
          </div>
        </div>

        <div className="pp-facette">
          <span className="pp-facette-quoi">
            Sujet{' '}
            <i>
              — {formatNumber(sujets.length)} sous la sélection ·{' '}
              {tout
                ? 'échelle propre à l’ensemble, non comparable à celle d’une période'
                : 'échelle commune aux périodes'}
            </i>
          </span>
          {sujets.length ? (
            <ul className="pp-sujets">
              {sujetsVus.map((s) => (
                <li key={s.sujet} className={s.sujet === sujet ? 'pp-sujet--actif' : undefined}>
                  <button
                    type="button"
                    onClick={() => {
                      setSujet(s.sujet === sujet ? null : s.sujet);
                      setLimite(PAS_DE_FIL);
                    }}
                    aria-pressed={s.sujet === sujet}
                  >
                    <span className="pp-sujet-nom">{s.sujet}</span>
                    <span
                      className="pp-sujet-barre"
                      style={{ width: `${Math.max(1, (s.n / plafond) * 100)}%` }}
                    />
                  </button>
                  <span className="pp-sujet-n">{formatNumber(s.n)}</span>
                </li>
              ))}
              {sujets.length > SUJETS_REPLIES && (
                <li className="pp-sujets-plus">
                  <button type="button" onClick={() => setTousSujets((v) => !v)}>
                    {tousSujets
                      ? 'Réduire la liste'
                      : `Voir les ${formatNumber(sujets.length - SUJETS_REPLIES)} autres sujets`}
                  </button>
                </li>
              )}
            </ul>
          ) : (
            <p className="pp-vide">Aucun sujet publié sous cette sélection.</p>
          )}
        </div>
      </div>

      <div className="pp-fil">
        {!sujet && !deplie ? (
          <p className="pp-invite">
            <b>Choisissez un sujet</b> pour lire ce qui a été dit —{' '}
            {formatNumber(lot.filter(passeNature).length)} interventions sous la sélection.
          </p>
        ) : (
          <>
            <div className="pp-fil-tete">
              <span className="pp-fil-quoi">
                {sujet || 'Tous les sujets'} — {formatNumber(visibles.length)} intervention
                {visibles.length > 1 ? 's' : ''}
              </span>
              {sujet && (
                <button type="button" className="pp-raz" onClick={() => setSujet(null)}>
                  Toute la période
                </button>
              )}
            </div>
            {visibles.length ? (
              <ul className="pp-liste">
                {visibles.slice(0, limite).map((i) => (
                  <Intervention
                    mot={mot}
                    key={i.id ?? `${i.date}-${i.chemin}`}
                    i={{
                      ...i,
                      libelleNature: libelleNature(i.type),
                      reste: i.chemin
                        ? i.chemin
                            .split('>')
                            .map((s) => s.trim())
                            .filter((s) => s && s !== i.sujet)
                            .join(' › ')
                        : null,
                    }}
                  />
                ))}
              </ul>
            ) : (
              <p className="pp-vide">
                Aucune intervention sous ce croisement — le croisement est vide, pas le corpus.
              </p>
            )}
            {visibles.length > limite && (
              <button
                type="button"
                className="pp-plus"
                onClick={() => setLimite((n) => n + PAS_DE_FIL)}
              >
                Voir {formatNumber(Math.min(PAS_DE_FIL, visibles.length - limite))} interventions de
                plus — {formatNumber(visibles.length - limite)} restantes
              </button>
            )}
          </>
        )}
      </div>

      {/* LE CHIFFRE RESTE ICI, LE POURQUOI PART À LA MÉTHODOLOGIE. Ce que la
          source publie ou non de la qualité de l'orateur, ce qu'est une
          collecte réduite au thème : c'est vrai des 30 fiches, et le répéter
          sous chacune noyait la seule chose qui parle de cette personne — les
          quatre chiffres. */}
      <p className="cp-note pp-couverture">
        {/* CE QUI MANQUE, PAS CE QUI EST LÀ. « 3 951 portent l'intitulé » sur
            3 963 se lit comme une abondance : il faut soustraire de tête pour
            voir les 12 qui manquent, et c'est le trou que la phrase annonce. */}
        <b>Ce que cette figure ne sait pas.</b> Sur {formatNumber(couverture.total)} interventions :{' '}
        {formatNumber(couverture.total - couverture.sujet)} sans intitulé,{' '}
        {formatNumber(couverture.total - couverture.verbatim)} sans verbatim,{' '}
        {formatNumber(couverture.total - couverture.fonction)} sans la qualité de l’orateur.
        {couverture.themeSeul > 0 && (
          <>
            {' '}
            {formatNumber(couverture.themeSeul)} relèvent d’une collecte réduite au thème.
          </>
        )}
        {couverture.datees < couverture.total && (
          <>
            {' '}
            {formatNumber(couverture.total - couverture.datees)} ne portent pas de date exploitable
            et restent hors du découpage.
          </>
        )}{' '}
        <Link to="/methodologie#interventions">Ce que ces absences veulent dire</Link>.
      </p>

      {/* LA SOURCE EST NOMMÉE UNE FOIS, PAS À CHAQUE LIGNE. L'Assemblée publie
          les comptes rendus de séance en archive : un badge par intervention y
          menait, et cliquer lançait le téléchargement de 100 Mo. */}
      <p className="pp-archive">
        Les comptes rendus de séance sont publiés par l’Assemblée nationale sous forme d’archive.{' '}
        <a href={PAGE_JEU_DE_DONNEES_DEBATS} target="_blank" rel="noreferrer">
          La page du jeu de données
        </a>{' '}
        porte le lien de téléchargement.
      </p>

      <p className="pp-methodo">
        <Link to="/methodologie#interventions">
          Comment ces interventions sont collectées, datées et qualifiées
        </Link>
      </p>
    </div>
  );
}
