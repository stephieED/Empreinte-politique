/*
 * La cascade des textes portés et la liste qu'on y ouvre — une figure, deux
 * fiches (#329). Elle vivait dans `CandidateProfile.jsx` ; la fiche de lignée
 * la reprend telle quelle (annotation de la propriétaire, 11/09/2026 : « le
 * gabarit candidat »). Une figure recopiée divergerait au premier correctif :
 * elle est donc sortie ici, et les deux fiches l'importent.
 *
 * Ses classes `cp-ter-*` restent dans `CandidateProfile.css`, importée ici :
 * elles sont la figure, pas la fiche.
 */
import { Fragment, useLayoutEffect, useMemo, useRef, useState } from 'react';
import './CandidateProfile.css';
import { teinteMatiere, teinteThemeUe } from '../utils/matiere';
import { croise, disposerCascade, textesDeLaSelection } from '../utils/cascadeTextes';
import { LIBELLE_SORT_TEXTE, MOTIF_SORT, estProcedure49_3, formatNumber } from '../utils/lecture';
import { LIBELLE_PISTE, LIBELLE_STADE } from '../utils/profilCandidat';

/*
 * LA CASCADE PROCÉDURALE — ce que sont devenus les textes qu'il a portés.
 *
 * Trois portes, six branches : de la commission on va en séance OU nulle part
 * ailleurs, de la séance à l'adoption OU nulle part ailleurs, de l'adoption à
 * la promulgation OU nulle part ailleurs. La mise en page et le vocabulaire
 * vivent dans `utils/cascadeTextes.js` — ici, on rend.
 *
 * LA LARGEUR EST MESURÉE, pas supposée. La chute voisine s'en passe : son
 * viewBox est fixe et le navigateur la met à l'échelle. La cascade ne le peut
 * pas — elle décide de la place de ses étiquettes, du mot long ou court, et de
 * la gouttière des matières d'après la largeur réelle. À viewBox fixe, un
 * téléphone recevrait la disposition d'un écran large, réduite au tiers.
 */
const ENCRE_ETAPE = ['#5b6b82', '#46566d', '#334458', '#17141f'];

function encreDeLEtape(i, fin) {
  if (!fin) return ENCRE_ETAPE[ENCRE_ETAPE.length - 1];
  return ENCRE_ETAPE[Math.round((i / fin) * (ENCRE_ETAPE.length - 1))];
}

function useLargeur() {
  const ref = useRef(null);
  const [largeur, setLargeur] = useState(0);
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return undefined;
    const obs = new ResizeObserver((entrees) => {
      setLargeur(Math.round(entrees[0].contentRect.width));
    });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);
  return [ref, largeur];
}

/* `rangs` (facultatif) : le rang de teinte de chaque matière, quand la page
 * porte une autre figure des mêmes matières et qu'une commission doit garder
 * sa couleur d'une figure à l'autre (fiche de lignée, #329). Une matière
 * absente de `rangs` prend les rangs suivants, dans l'ordre de la cascade. */
/* `disposer` (facultatif) : la mise en page à employer. Le versant européen a
 * la sienne — `disposerCascadeUE`, un seul palier, parce que les seize stades
 * européens ne s'ordonnent pas (#901). Le rendu, lui, ne change pas : c'est la
 * même figure, les mêmes teintes de matière, le même clic. */
export function Cascade({ cascade, selection, onSelection, rangs = null, disposer = disposerCascade, ue = false }) {
  const [ref, largeur] = useLargeur();
  const rang = useMemo(() => {
    if (!rangs) return new Map((cascade.matieres || []).map((m, i) => [m, i]));
    const r = new Map(rangs);
    for (const m of cascade.matieres || []) if (!r.has(m)) r.set(m, r.size);
    return r;
  }, [cascade.matieres, rangs]);
  const teinteDe = useMemo(
    () => (m) => (ue ? teinteThemeUe(m, rang.get(m) ?? 0) : teinteMatiere(m, rang.get(m) ?? 0)),
    [rang],
  );
  const vue = useMemo(
    () => (largeur ? disposer(cascade, largeur, teinteDe) : null),
    [cascade, disposer, largeur, teinteDe],
  );

  const choisir = (matiere, lo, hi) => {
    const memeChose = selection
      && selection.matiere === matiere && selection.lo === lo && selection.hi === hi;
    onSelection(memeChose ? null : { matiere, lo, hi });
  };

  return (
    <div className="cp-ter" ref={ref}>
      {vue === null ? (
        <p className="cp-note cp-ter-vide">
          {cascade.total <= 1
            ? 'Un seul texte publié : une cascade n’aurait qu’un ruban, et la liste ci-dessous le dit mieux.'
            : 'Trop peu de textes pour un diagramme de flux — la liste ci-dessous les porte tous.'}
        </p>
      ) : (
        <svg
          aria-label="Cascade procédurale des textes portés : à chaque étape, ce qui franchit et ce dont le corpus n’enregistre aucun acte au-delà"
          className="cp-ter-svg"
          role="img"
          viewBox={`0 ${vue.y0.toFixed(1)} ${vue.W} ${vue.H}`}
        >
          {vue.rubans.map((r) => (
            <path
              className={croise(selection, r.matiere, r.lo, r.hi) ? '' : 'cp-ter-voile'}
              d={r.d}
              fill="none"
              key={r.cle}
              onClick={() => choisir(r.matiere, r.lo, r.hi)}
              stroke={r.couleur}
              strokeOpacity={r.sortie ? 0.62 : 0.85}
              strokeWidth={r.epaisseur.toFixed(1)}
            >
              <title>{r.titre}</title>
            </path>
          ))}
          {vue.barres.map((b) => (
            <rect
              className={[
                b.couleur ? 'cp-ter-matiere' : (b.sortie ? 'cp-ter-issue' : 'cp-ter-encre'),
                croise(selection, b.matiere, b.lo, b.hi) ? '' : 'cp-ter-voile',
              ].filter(Boolean).join(' ')}
              fill={b.couleur || (b.sortie ? undefined : encreDeLEtape(b.etape, vue.fin))}
              height={b.h.toFixed(1)}
              key={b.cle}
              onClick={() => choisir(b.matiere, b.lo, b.hi)}
              rx={b.rx || 0}
              width={b.w.toFixed(1)}
              x={b.x.toFixed(1)}
              y={b.y.toFixed(1)}
            >
              <title>{b.titre}</title>
            </rect>
          ))}
          {vue.chiffres.map((c) => (
            <Fragment key={c.cle}>
              <text
                className="cp-ter-etape cp-ter-etape--issue"
                onClick={() => choisir(null, c.lo, c.hi)}
                x={c.x.toFixed(1)}
                y={c.y.toFixed(1)}
              >
                <tspan className="cp-ter-n">{formatNumber(c.nombre)}</tspan> {c.haut}
              </text>
              <text
                className="cp-ter-etape cp-ter-etape--issue"
                onClick={() => choisir(null, c.lo, c.hi)}
                x={c.xRetrait.toFixed(1)}
                y={c.yRetrait.toFixed(1)}
              >
                {c.bas}
              </text>
            </Fragment>
          ))}
          {/* Jamais voilée : l'étiquette porte la lecture, et c'est par elle
              qu'on sélectionne une étape toutes matières confondues. */}
          {vue.etiquettes.map((e) => (
            <text
              className={`cp-ter-etape${e.finie ? ' cp-ter-etape--fin' : ''}${e.sortie ? ' cp-ter-etape--issue' : ''}`}
              key={e.cle}
              onClick={() => choisir(null, e.lo, e.hi)}
              x={e.x.toFixed(1)}
              y={e.y.toFixed(1)}
            >
              <tspan className="cp-ter-n">{formatNumber(e.total)}</tspan> {e.lib}
            </text>
          ))}
          {vue.nomsMatiere.map((n) => (
            <Fragment key={n.cle}>
              {n.tirant && <path className="cp-ter-tirant" d={n.tirant} />}
              <text className="cp-ter-nom" x={n.x.toFixed(1)} y={n.y.toFixed(1)}>
                {n.court}
                <title>{n.nom}</title>
              </text>
            </Fragment>
          ))}
        </svg>
      )}

      <div className="cp-cles">
        {vue?.etroit && vue.matieres.map((m) => (
          <button
            aria-pressed={selection?.matiere === m}
            className="cp-cle cp-cle--cliquable"
            key={m}
            onClick={() => choisir(m, 0, vue.fin)}
            type="button"
          >
            <i style={{ background: teinteDe(m) }} />
            {m}
          </button>
        ))}
      </div>
      {/* LE 49.3 EST DIT ICI PARCE QUE LA FIGURE NE PEUT PAS LE PORTER.
          Son axe est le STADE — jusqu'où le texte est allé — et un texte adopté
          par engagement de responsabilité s'y range comme les autres : quatre
          de Gabriel Attal se fondent dans la barre « promulgué », un d'Édouard
          Philippe tombe dans une barre « non adopté » qui le contredit. Le fait
          est donc nommé à côté de la figure, jamais dedans, et jamais compté
          comme une adoption ordinaire (§2 règle 4). */}
      {cascade.procedure493 > 0 && (
        <p className="cp-ter-493">
          <button
            aria-pressed={Boolean(selection?.procedure493)}
            className="cp-ter-493-bouton"
            onClick={() => onSelection(selection?.procedure493 ? null : { procedure493: true })}
            type="button"
          >
            <span className="cp-ter-493-marque">49.3</span>
            <b>{formatNumber(cascade.procedure493)}</b> de ces textes
            {cascade.procedure493 > 1 ? ' ont été adoptés' : ' a été adopté'} sans vote
            <span className="cp-ter-493-quoi">(fait procédural)</span>
          </button>
        </p>
      )}
    </div>
  );
}

/* `ordonnee` : vrai quand les stades forment une ÉCHELLE. « examiné en
 * commission, et non discuté en séance » n'a de sens que là ; sur le versant
 * européen, une issue ne se lit pas par rapport à la suivante — il n'y a pas de
 * suivante. La liste nomme alors l'issue, et rien d'autre. */
export function ListeCascade({ cascade, selection, onRaz, ordonnee = true }) {
  const sel = useMemo(() => textesDeLaSelection(cascade, selection), [cascade, selection]);
  const colonnes = useMemo(() => [
    /* Un texte européen se range sous « Au Parlement européen », jamais sous
       « À l'Assemblée » (#901). */
    { cle: 'pe', textes: sel.filter((t) => t.europeen) },
    { cle: 'parlement', textes: sel.filter((t) => !t.projetDeLoi && !t.europeen) },
    { cle: 'gouvernement', textes: sel.filter((t) => t.projetDeLoi) },
  ].filter((c) => c.textes.length > 0), [sel]);
  if (!selection) {
    return (
      <p className="cp-note cp-ter-invite">
        Cliquez un ruban, une barre ou une étiquette pour lire ce qui la compose.
      </p>
    );
  }
  const fin = cascade.stades.length - 1;
  const nomDe = (i) => cascade.libelles?.[cascade.stades[i]]
    || LIBELLE_STADE[cascade.stades[i]] || cascade.stades[i];
  const ou = selection.procedure493
    ? 'adoptés sans vote, par engagement de responsabilité'
    : !ordonnee
    ? (selection.lo === selection.hi ? nomDe(selection.lo) : 'tous stades')
    : selection.lo === selection.hi
    ? (selection.lo === fin ? nomDe(fin) : `${nomDe(selection.lo)}, et non ${nomDe(selection.lo + 1)}`)
    : (selection.lo === 0 ? 'publiés' : `${nomDe(selection.lo)} ou au-delà`);
  return (
    <div className="cp-ter-liste">
      <div className="cp-ter-liste-tete">
        <span className="cp-ter-liste-quoi">
          {selection.procedure493 ? 'Article 49.3' : selection.matiere || 'toutes matières'} ·{' '}
          {ou} — {formatNumber(sel.length)} texte
          {sel.length > 1 ? 's' : ''}
        </span>
        {/* Sans `onRaz`, la liste montre déjà tout : un « Tout afficher » n'y
            ferait rien (diagramme non dessiné, filtre de la fiche — #979). */}
        {onRaz && <button className="cp-chute-raz" onClick={onRaz} type="button">Tout afficher</button>}
      </div>
      {/* DEUX COLONNES, PARCE QUE CE SONT DEUX QUALITÉS.
          Un projet de loi est signé comme MINISTRE, une proposition déposée
          comme PARLEMENTAIRE : la liste les mêlait, et une phrase sous la
          figure — « 31 de ses 34 textes portés sont des projets de loi » —
          disait en toutes lettres ce que la liste aurait dû montrer. `role` les
          sépare à la source (#689), les teintes sont celles de « ce que cette
          personne a engagé, en chiffres », et rien n'est additionné.

          UNE SEULE COLONNE QUAND LA SÉLECTION N'A QU'UNE QUALITÉ : une colonne
          vide se lirait comme une lacune de collecte, quand c'est l'expérience
          qui n'existe pas (§2 règle 5). */}
      <div className={`cp-ter-cols ${colonnes.length > 1 ? 'cp-ter-cols--deux' : ''}`}>
        {colonnes.map((col) => (
          <div className={`cp-gc-tete-col cp-gc-tete-col--${col.cle}`} key={`t-${col.cle}`}>
            <span className="cp-gc-bandeau" />
            <span className="cp-gc-col-nom">
              <i />
              {LIBELLE_PISTE[col.cle]}
              <b className="cp-ter-col-nb cp-num">{formatNumber(col.textes.length)}</b>
            </span>
          </div>
        ))}
        {colonnes.map((col) => (
          <ul key={`l-${col.cle}`}>
            {col.textes.map((t) => (
              <li key={`${t.titre}-${t.stadeCle}`}>
                <span className="cp-ter-titre">
                  {t.url
                    ? <a href={t.url} rel="noreferrer" target="_blank">{t.titre}</a>
                    : t.titre}
                </span>
                <span
                  className="cp-ter-pastille"
                  style={{
                    '--pastille': ordonnee
                      ? encreDeLEtape(cascade.stades.indexOf(t.stadeCle), fin)
                      : encreDeLEtape(fin, fin),
                  }}
                >
                  {t.stade}
                </span>
                <span className="cp-ter-fait">
                  {t.themes ? t.themes.join(', ') : t.matiere}{t.an ? ` · ${t.an}` : ''}{t.role ? ` · ${t.role}` : ''}
                </span>
            {/* LE SORT À CÔTÉ DU STADE, JAMAIS À SA PLACE. La pastille du haut
                dit jusqu'où le texte est allé, celle-ci ce qu'il est devenu, et
                l'un ne se déduit pas de l'autre : « discuté en séance et pas
                adopté » ne veut pas dire « rejeté ». Un sort absent affiche son
                MOTIF, jamais un sort par défaut (§2 règle 5). */}
                <span className={`cp-ter-sort${estProcedure49_3(t.sortCle) ? ' cp-ter-sort--493' : ''}`}>
                  {t.sortCle
                    ? LIBELLE_SORT_TEXTE[t.sortCle] || t.sortCle
                    : `Sort non résolu${t.sortMotif ? ` — ${MOTIF_SORT[t.sortMotif] || t.sortMotif}` : ''}`}
                </span>
              </li>
            ))}
          </ul>
        ))}
      </div>
    </div>
  );
}
