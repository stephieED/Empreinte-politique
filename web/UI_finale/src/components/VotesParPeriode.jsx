/* ── « Ce qu'il a voté », par période politique (#328) ────────────────────────
 *
 * Le composant ne calcule rien qui soit un fait : les périodes, les matières,
 * l'échelle et la couverture arrivent déjà construites par
 * `utils/votesParPeriode.js`. Il ne décide ici que ce qui est montré à l'écran
 * — quelle période, quels filtres, quelle matière sélectionnée.
 *
 * Maquette validée le 08/09/2026 (artefact « Depuis quel banc il a voté »).
 */
import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { LIBELLE_SORT_TEXTE, VOTE_STYLE, formatNumber, pageDuJeuDeDonnees } from '../utils/lecture';
import { MATIERE_NON_ETABLIE as NON_ETABLIE, NATURES_UE } from '../utils/profilCandidat';
import { teinteThemeUe } from '../utils/matiere';
import { libellePosition, MATIERE_NON_ETABLIE } from '../utils/profilCandidat';
import {
  LIBELLE_ORIGINE,
  LIBELLE_POSITION,
  ORIGINE_GOUVERNEMENT,
  ORIGINE_PARLEMENT,
  POSITIONS_ORDONNEES,
  REPERE_NON_PUBLIE,
  matieresDePeriode,
} from '../utils/votesParPeriode';
import NavigationPeriodes from './NavigationPeriodes';
import './VotesParPeriode.css';

const jour = (d) => (d ? `${d.slice(8, 10)}/${d.slice(5, 7)}/${d.slice(0, 4)}` : '');
const mois = (d) => (d ? `${d.slice(0, 4)}/${d.slice(5, 7)}` : '');

/* Le titre d'une période nomme CE QU'ON SAIT, et rien d'autre. Les deux repères
 * ne sont pas toujours publiés ensemble : avant 2017 le corpus n'a aucune fiche
 * de gouvernement, depuis 2024 l'Assemblée ne déclare plus le banc. Un titre
 * qui compléterait le repère manquant par celui de la période voisine
 * inventerait un fait (§2 règle 5). */
function titreDePeriode(periode) {
  if (periode.cumul) return 'Toutes les périodes';
  if (!periode.banc && !periode.gouvernement) return REPERE_NON_PUBLIE;
  // Le repère manquant est NOMMÉ, pas escamoté : un titre qui n'écrit que le
  // gouvernement laisse croire que le banc n'existait pas, alors qu'il n'est
  // pas publié — ce sont deux faits différents (§2 règle 5).
  const banc = periode.banc ? libellePosition(periode.banc) : 'banc non publié';
  const gouvernement = periode.gouvernement
    ? `gouvernement ${periode.gouvernement}`
    : 'gouvernement non publié';
  return `${banc} · ${gouvernement}`.replace(/^./, (c) => c.toUpperCase());
}

function libelleCourtDePeriode(periode) {
  if (periode.libelle) return periode.groupes?.length ? periode.groupes.join(', ') : periode.libelle;
  const banc = periode.banc ? libellePosition(periode.banc) : 'banc non publié';
  return periode.gouvernement ? `${banc} · ${periode.gouvernement}` : banc;
}

/* ── La barre divergente d'une matière ──────────────────────────────────────
 *
 * Contre à gauche de l'axe, abstention puis pour à droite. Dans chaque
 * position, la part du GOUVERNEMENT est posée CONTRE L'AXE, toujours, pour
 * qu'elle se compare d'une ligne à l'autre sans que l'œil ait à la chercher.
 *
 * L'origine se dit par la FORME, pas par la couleur : aplat pour le
 * gouvernement, voile de la même teinte plus filet à pleine saturation pour le
 * Parlement. La teinte n'est jamais altérée, donc la position se lit toujours à
 * pleine saturation ; et le filet tient sur un segment d'un seul texte, là où
 * une rayure n'aurait plus la place d'une diagonale.
 */
function segments(ligne, portee) {
  const px = (x) => (x / portee) * 50;
  const out = [];
  const pousse = (cote, position, origine, n, decalage) => {
    if (!n) return decalage;
    const couleur = VOTE_STYLE[position]?.color ?? null;
    out.push({
      cle: `${cote}-${position}-${origine}`,
      origine,
      style: {
        '--pc': couleur,
        backgroundColor: couleur,
        width: `${px(n)}%`,
        ...(cote === 'gauche'
          ? { right: `${50 + px(decalage)}%` }
          : { left: `${50 + px(decalage)}%` }),
      },
    });
    return decalage + n;
  };

  let gauche = pousse('gauche', 'contre', ORIGINE_GOUVERNEMENT, ligne.contre.gouvernement, 0);
  pousse('gauche', 'contre', ORIGINE_PARLEMENT, ligne.contre.parlement, gauche);

  let droite = 0;
  for (const position of ['abstention', 'pour']) {
    droite = pousse('droite', position, ORIGINE_GOUVERNEMENT, ligne[position].gouvernement, droite);
    droite = pousse('droite', position, ORIGINE_PARLEMENT, ligne[position].parlement, droite);
  }
  return out;
}

function total(part) {
  return part.gouvernement + part.parlement;
}

function BlocPeriode({ periode, portee, garde, matiere, onMatiere, ue = false }) {
  const lignes = matieresDePeriode(periode, garde);

  if (!lignes.length) {
    return (
      <p className="vp-vide">
        Aucun texte ne répond aux filtres retenus sur cette période. Les filtres retirent de la
        masse ; ils ne redimensionnent rien.
      </p>
    );
  }

  return (
    <>
      <div className="vp-tete">
        <h3 className="vp-titre">{periode.libelle ?? titreDePeriode(periode)}</h3>
        <span className="vp-quand">
          {mois(periode.debut)} → {mois(periode.fin)}
          {periode.groupes.length ? ` · ${periode.groupes.join(', ')}` : ''}
        </span>
      </div>

      <div className="vp-barres">
        {lignes.map((l) => (
          <div className="vp-ligne" key={l.matiere}>
            <div className="vp-nom">
              {l.matiere}
              <em>
                {total(l.contre)} contre · {total(l.pour)} pour
                {total(l.abstention) ? ` · ${total(l.abstention)} abst.` : ''}
              </em>
            </div>
            <button
              type="button"
              className={`vp-piste${matiere === l.matiere ? ' vp-piste--active' : ''}`}
              onClick={() => onMatiere(matiere === l.matiere ? null : l.matiere)}
              aria-pressed={matiere === l.matiere}
              aria-label={`${l.matiere} : ${total(l.contre)} contre, ${total(l.abstention)} abstention, ${total(l.pour)} pour`}
            >
              <span className="vp-axe" />
              {segments(l, portee).map((s) => (
                <span
                  key={s.cle}
                  className={`vp-seg vp-seg--${s.origine}`}
                  style={s.style}
                />
              ))}
            </button>
            <div className="vp-tot">{formatNumber(l.n)}</div>
          </div>
        ))}
      </div>

      <p className="vp-echelle">
        <span>← {formatNumber(portee)} textes</span>
        {/* Sous un mot du filtre, la figure n'a qu'une période, le cumul ; côté
            européen, il n'y a jamais de période — mais l'échelle reste commune
            aux filtres, qui retirent de la masse sans redimensionner. */}
        <span className="vp-echelle-mid">
          {periode.cumul ? '' : ue ? 'même échelle quel que soit le filtre' : 'même échelle pour toutes les périodes'}
        </span>
        <span>{formatNumber(portee)} textes →</span>
      </p>
    </>
  );
}

/* ── Les trois colonnes ─────────────────────────────────────────────────────
 *
 * Une colonne par position, dans l'ordre de la figure. Sans matière
 * sélectionnée, elles montrent toute la période courante : un panneau qui
 * attend un clic pour dire quelque chose laisse un tiers de la page vide tant
 * qu'on n'a pas deviné le geste.
 */
function Colonnes({ votes, positions, matiere, onIsoler, onToutAfficher, ue = false }) {
  const colonnes = POSITIONS_ORDONNEES.filter((p) => positions.has(p));
  const seule = colonnes.length === 1;

  return (
    <div className="vp-liste">
      <div className="vp-liste-tete">
        <span className="vp-liste-quoi">
          {matiere || 'Toutes les matières'} — {formatNumber(votes.length)} texte
          {votes.length > 1 ? 's' : ''}
        </span>
        {matiere && (
          <button type="button" className="vp-raz" onClick={onToutAfficher}>
            Toute la période
          </button>
        )}
      </div>

      <div className="vp-colonnes" style={{ '--n': colonnes.length }}>
        {colonnes.map((p) => {
          const dans = votes.filter((v) => v.position === p);
          return (
            <div key={p} style={{ '--pc': VOTE_STYLE[p]?.color ?? null }}>
              <button
                type="button"
                className="vp-col-tete"
                onClick={() => onIsoler(p)}
                aria-pressed={seule}
                title={
                  seule
                    ? 'Réafficher les trois positions'
                    : `N'afficher que les votes ${LIBELLE_POSITION[p].toLowerCase()}`
                }
              >
                <span className="vp-col-quoi">{LIBELLE_POSITION[p]}</span>
                <span className="vp-col-n">{formatNumber(dans.length)}</span>
              </button>
              {dans.length ? (
                <ul>
                  {dans.map((v) => (
                    <li key={v.scrutinId}>
                      <span className="vp-li-t">
                        {v.sourceUrl ? (
                          <a href={pageDuJeuDeDonnees(v.sourceUrl)} target="_blank" rel="noreferrer">
                            {v.titre}
                          </a>
                        ) : (
                          v.titre
                        )}
                      </span>
                      <span className="vp-li-f">
                        {jour(v.date)} · {v.matiere || MATIERE_NON_ETABLIE.toLowerCase()} ·{' '}
                        {ue ? v.meta : (LIBELLE_SORT_TEXTE[v.statutTexte] ?? 'sort non établi')}
                        {v.procedure49_3 && <b className="vp-49-3">49.3</b>}
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="vp-col-vide">aucun texte</p>
              )}
            </div>
          );
        })}
      </div>

      {/* Une seule voix sur toute la fiche : « cliquez ». Le tutoiement de
          l'invite des textes portés et le vouvoiement d'ici cohabitaient sur la
          même page (#328). */}
      <p className="vp-aide">Cliquez une barre, ou un en-tête de colonne.</p>
    </div>
  );
}

/* `etiquette` (#979) : le rappel du mot du filtre, en tête de la carte.
 * `ue` (#901) : le versant européen — ni période, ni origine de texte. */
export default function VotesParPeriode({ periodes, portee, reperes, regle, etiquette = null, ue = false }) {
  const [index, setIndex] = useState(0);
  const [positions, setPositions] = useState(() => new Set(POSITIONS_ORDONNEES));
  const [origine, setOrigine] = useState(null);
  const [matiere, setMatiere] = useState(null);
  // Le filtre par nature des textes votés au Parlement européen (#901).
  const [nature, setNature] = useState('tous');

  const periode = periodes[Math.min(index, periodes.length - 1)];
  const LIBELLE_NATURE_VOTE = { sans_dossier: 'Sans dossier' };
  const naturesPresentes = ue
    ? NATURES_UE.filter((n) => (periode?.votes || []).some((v) => v.natureCle === n.cle))
    : [];
  const filtreNature = naturesPresentes.length > 1;

  const garde = useMemo(
    () => (v) =>
      positions.has(v.position)
      && (nature === 'tous' || v.natureCle === nature)
      && (!origine || (v.origine === ORIGINE_GOUVERNEMENT ? ORIGINE_GOUVERNEMENT : ORIGINE_PARLEMENT) === origine),
    [positions, origine, nature],
  );

  const visibles = useMemo(
    () =>
      (periode?.votes || [])
        .filter(garde)
        .filter((v) => !matiere || (v.matiere || MATIERE_NON_ETABLIE) === matiere)
        .slice()
        .reverse(),
    [periode, garde, matiere],
  );

  if (!periode) return null;

  const basculerPosition = (p) => {
    setPositions((s) => {
      const n = new Set(s);
      // La dernière position cochée refuse d'être décochée : un graphique vide
      // n'apprend rien et se lirait comme une absence de données.
      if (n.has(p)) {
        if (n.size > 1) n.delete(p);
      } else n.add(p);
      return n;
    });
    setMatiere(null);
  };

  const isoler = (p) => {
    setPositions((s) =>
      s.size === 1 && s.has(p) ? new Set(POSITIONS_ORDONNEES) : new Set([p]),
    );
    setMatiere(null);
  };

  const compteOrigine = (o) =>
    (periode.votes || []).filter(
      (v) =>
        positions.has(v.position)
        && (!o || (v.origine === ORIGINE_GOUVERNEMENT ? ORIGINE_GOUVERNEMENT : ORIGINE_PARLEMENT) === o),
    ).length;

  /* UNE SEULE CARTE, DU DÉNOMINATEUR À LA FIGURE. La règle de repli et la
   * navigation entre périodes flottaient AU-DESSUS du cadre blanc, comme deux
   * bandeaux détachés de ce qu'ils qualifient — alors qu'ils ne disent rien
   * d'autre que : voici de quoi cette figure est tirée, et quelle période elle
   * montre. Elles entrent donc dans la carte, dans cet ordre. */
  return (
    <div className="vp">
      <div className="cp-carte cp-bloc vp-carte">
        {etiquette}
        {regle && <p className="vp-regle">{regle}</p>}
        {filtreNature && (
          <div className="cp-natures" role="group" aria-label="Nature des textes votés">
            {[{ cle: 'tous', libelle: 'Toutes natures', total: new Set((periode.votes || []).map((v) => v.scrutinId)).size }]
              .concat(naturesPresentes.map((n) => ({
                ...n,
                libelle: LIBELLE_NATURE_VOTE[n.cle] || n.libelle,
                total: new Set((periode.votes || []).filter((v) => v.natureCle === n.cle).map((v) => v.scrutinId)).size,
              })))
              .map((n) => (
                <button
                  aria-pressed={nature === n.cle}
                  className="cp-nature"
                  key={n.cle}
                  onClick={() => { setNature(n.cle); setMatiere(null); }}
                  type="button"
                >
                  {n.libelle} <b className="cp-num">{formatNumber(n.total)}</b>
                </button>
              ))}
          </div>
        )}
        {/* Aucune navigation côté européen : il n'y a pas de période (#901), et
            aucune sous un mot du filtre, où la figure est le cumul (#979). */}
        {!periode.cumul && !ue && (
        <NavigationPeriodes
          periodes={periodes}
          index={Math.min(index, periodes.length - 1)}
          onIndex={(i) => {
            setIndex(i);
            setMatiere(null);
          }}
          poids={(p) => p.votes.length}
          libelle={libelleCourtDePeriode}
          unite="textes"
          uniteSingulier="texte"
        />
        )}
        <BlocPeriode
          ue={ue}
          periode={periode}
          portee={portee}
          garde={garde}
          matiere={matiere}
          onMatiere={setMatiere}
        />
      </div>

      <div className="vp-filtres">
        <span className="vp-filtres-quoi">Position</span>
        {POSITIONS_ORDONNEES.map((p) => (
          <button
            type="button"
            key={p}
            className="vp-chip vp-chip--position"
            style={{ '--pc': VOTE_STYLE[p]?.color ?? null }}
            aria-pressed={positions.has(p)}
            onClick={() => basculerPosition(p)}
          >
            <i />
            {LIBELLE_POSITION[p]}{' '}
            <span className="vp-chip-n">
              {formatNumber(new Set((periode.votes || []).filter((v) => v.position === p).map((v) => v.scrutinId)).size)}
            </span>
          </button>
        ))}
        {!ue && <span className="vp-sep" />}
        {!ue && <span className="vp-filtres-quoi">Origine</span>}
        {!ue && [null, ORIGINE_PARLEMENT, ORIGINE_GOUVERNEMENT].map((o) => (
          <button
            type="button"
            key={o ?? 'tous'}
            className={`vp-chip${o ? ` vp-chip--${o}` : ''}`}
            aria-pressed={origine === o}
            onClick={() => {
              setOrigine(o);
              setMatiere(null);
            }}
          >
            {o && <i />}
            {o ? LIBELLE_ORIGINE[o] : 'Tous'}{' '}
            <span className="vp-chip-n">{formatNumber(compteOrigine(o))}</span>
          </button>
        ))}
      </div>

      <p className="vp-methodo">
        <Link to="/methodologie#votes">
          Comment ces votes sont retenus, rattachés et qualifiés
        </Link>
      </p>

      <Colonnes
        ue={ue}
        votes={visibles}
        positions={positions}
        matiere={matiere}
        onIsoler={isoler}
        onToutAfficher={() => setMatiere(null)}
      />

      {/* La section publie ses propres trous. Sans cette ligne, une matière
          absente sur 449 des 1 160 positions se lirait comme « ces textes n'ont
          pas de commission saisie au fond » (§2 règles 5 et 7).
          LE CHIFFRE RESTE ICI, LE POURQUOI PART À LA MÉTHODOLOGIE : la mesure
          ne vaut que de cette personne et n'a de sens que sous sa figure ;
          l'explication du rattachement est la même sur les 30 fiches, et un
          paragraphe recopié trente fois se lit zéro fois. */}
      {reperes && ue && (
        <p className="cp-note vp-couverture">
          <b>Ce que cette figure ne sait pas.</b> Sur ses {formatNumber(reperes.total)} textes votés
          au Parlement européen, {formatNumber(reperes.total - reperes.matiere)} ne portent aucun
          thème — la source ne les rattache à aucun dossier — et{' '}
          {formatNumber(reperes.positions - reperes.total)} position
          {reperes.positions - reperes.total > 1 ? 's' : ''} portent sur un scrutin antérieur du
          même texte, que le dernier vote retenu remplace.
        </p>
      )}
      {reperes && !ue && (
        <p className="cp-note vp-couverture">
          <b>Ce que cette figure ne sait pas.</b> Sur ses {formatNumber(reperes.total)} positions
          de dernière lecture, {formatNumber(reperes.total - reperes.matiere)} ne disent pas quelle
          commission a examiné le texte — elles restent en « matière non établie » — et{' '}
          {formatNumber(reperes.total - reperes.statut)} ne portent pas le sort final de leur
          texte.{' '}
          <Link to="/methodologie#votes">Pourquoi ce rattachement n’aboutit pas toujours</Link>.
        </p>
      )}
    </div>
  );
}
