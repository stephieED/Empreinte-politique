import { useEffect, useMemo, useRef, useState } from 'react';
import { useReplieAuClicDehors } from '../hooks/useReplieAuClicDehors';
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
 * UNE BARRE PAR MINISTÈRE depuis le 04/10/2026 : le diagramme de flux et ses
 * deux rangées de filtres sont partis (`docs/decisions/revue-ux-de-la-fiche-de-gouvernement.md`).
 */

const MUET = 'le titre ne le dit pas';
/* Douze ministères, puis les autres à ouvrir : la liste entière en compte trente
   sur Borne. */
const LIGNES_AFFICHEES = 12;
const LOIS = '\u0000lois';
const LIES = 'lies';
const MUETS = 'muets';
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
  const [ouvert, setOuvert] = useState(null);
  // La part de la barre retenue : `null` pour tout le ministère, sinon l'un
  // de ses deux segments — `LIES` ou `MUETS`.
  const [part, setPart] = useState(null);
  const [tout, setTout] = useState(false);
  // Ce qui s'ouvre au clic se replie au clic ailleurs, comme sur les autres fiches.
  const racine = useRef(null);
  useReplieAuClicDehors(racine, ouvert !== null, () => { setOuvert(null); setPart(null); });

  useEffect(() => {
    let vivant = true;
    setDonnees(null);
    setErreur(false);
    setOuvert(null);
    setPart(null);
    setTout(false);
    getActesDuGouvernement(id)
      .then((d) => { if (vivant) setDonnees(d); })
      .catch(() => { if (vivant) setErreur(true); });
    return () => { vivant = false; };
  }, [id]);

  /* UNE BARRE PAR MINISTÈRE, À L'ENCRE (revue d'ergonomie du 04/10/2026, forme A).
   *
   * La section portait un diagramme de flux : cinq ministères en couleur, les
   * autres fondus dans un bloc gris, et à droite deux cases dont l'une, « le
   * titre ne le dit pas », recevait 94 % des actes de Borne — elle a été lue
   * comme « une catégorie par défaut qui écrase la répartition ». Chaque
   * ministère a désormais sa ligne ; la part sombre de sa barre est celle des
   * actes dont le titre cite une loi, le fond clair est « le titre ne le dit
   * pas ».
   *
   * PLUS DE COULEUR PAR MINISTÈRE. Les cinq teintes suivaient le RANG, pas le
   * ministère : le premier était toujours bleu, d'une fiche à l'autre. Une
   * couleur qui ne dit rien se retire (arbitrage de la propriétaire). Elle
   * reviendra si les projets de loi portent un jour leur ministre : la source
   * le publie, la collecte ne le lit pas encore. */
  const lignes = useMemo(() => {
    if (!donnees) return [];
    const par = new Map(Object.keys(donnees.ministeres || {}).map((m) => [m, { nom: m, n: 0, lies: 0 }]));
    (donnees.cellules || []).forEach((c) => {
      const l = par.get(c.m) || { nom: c.m, n: 0, lies: 0 };
      l.n += c.n;
      if (c.l !== MUET) l.lies += c.n;
      par.set(c.m, l);
    });
    return [...par.values()].filter((l) => l.n > 0).sort((x, y) => y.n - x.n || x.nom.localeCompare(y.nom, 'fr'));
  }, [donnees]);

  if (erreur) {
    return <p className="adg-vide">Les actes du Journal officiel n’ont pas pu être chargés.</p>;
  }
  if (!donnees) {
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

  const max = Math.max(1, ...lignes.map((l) => l.n));
  const visibles = tout ? lignes : lignes.slice(0, LIGNES_AFFICHEES);
  const reste = lignes.slice(LIGNES_AFFICHEES);
  const lois = donnees.lois || [];
  const loisDu = (m) => lois.filter((l) => (l.actes || []).some((a) => a.m === m));
  /* LE LIBELLÉ OUVRE TOUT LE MINISTÈRE, UN SEGMENT SA SEULE PART — le geste
     des prises de parole : le sujet entier, ou un membre. Un second clic sur
     ce qui est déjà retenu referme. */
  const basculer = (cle, laPart = null) => {
    const meme = ouvert === cle && part === laPart;
    setOuvert(meme ? null : cle);
    setPart(meme ? null : laPart);
  };

  return (
    <div className="adg" ref={racine}>
      <ol className="adg-entonnoir">
        <li><b>{nombre(donnees.tot)}</b><span>actes parus au Journal officiel</span></li>
        <li className="adg-ecartes">
          <b>− {nombre(donnees.personnes)}</b>
          <span>actes relevant du fonctionnement interne de l’État</span>
        </li>
        <li className="adg-reste"><b>{nombre(donnees.total)}</b><span>actes qui touchent au droit</span></li>
      </ol>

      <div className="adg-barres">
        <div className="adg-ligne adg-ligne--tete">
          <span />
          <span />
          <span className="adg-n">actes</span>
          <span className="adg-n">liés à une loi</span>
        </div>
        {visibles.map((l) => {
          const choisi = ouvert === l.nom;
          const muets = l.n - l.lies;
          const cellules = (donnees.cellules || []).filter((c) => c.m === l.nom
            && (part === null || (part === LIES ? c.l !== MUET : c.l === MUET)));
          return (
            <div key={l.nom}>
              <div className="adg-ligne">
                <button aria-expanded={choisi && part === null} className="adg-lib adg-lib--cliquable" onClick={() => basculer(l.nom)} title={l.nom} type="button">
                  {l.nom}
                </button>
                <span className="adg-rail">
                  <span className="adg-barre" style={{ width: `${((100 * l.n) / max).toFixed(2)}%` }}>
                    {l.lies > 0 && (
                      <button
                        aria-label={`${l.nom} — ${nombre(l.lies)} actes dont le titre cite une loi`}
                        aria-pressed={choisi && part === LIES}
                        className={`adg-part adg-part--lie${choisi && part === LIES ? ' adg-part--choisie' : ''}`}
                        onClick={() => basculer(l.nom, LIES)}
                        style={{ flex: `${l.lies} 1 0` }}
                        type="button"
                      />
                    )}
                    {muets > 0 && (
                      <button
                        aria-label={`${l.nom} — ${nombre(muets)} actes, le titre ne le dit pas`}
                        aria-pressed={choisi && part === MUETS}
                        className={`adg-part adg-part--muet${choisi && part === MUETS ? ' adg-part--choisie' : ''}`}
                        onClick={() => basculer(l.nom, MUETS)}
                        style={{ flex: `${muets} 1 0` }}
                        type="button"
                      />
                    )}
                  </span>
                </span>
                <span className="adg-n">{nombre(l.n)}</span>
                <span className="adg-n adg-n--fort">{nombre(l.lies)}</span>
              </div>
              {choisi && (
                <div className="adg-deroule">
                  {part !== MUETS && loisDu(l.nom).length > 0 && <Lois lois={loisDu(l.nom)} ministere={l.nom} />}
                  <Actes cellules={cellules} exemples={donnees.exemples} />
                </div>
              )}
            </div>
          );
        })}
        {reste.length > 0 && (
          <button className="adg-plus" onClick={() => setTout((v) => !v)} type="button">
            {tout
              ? 'Replier les ministères'
              : `▸ ${reste.length} autre${reste.length > 1 ? 's' : ''} ministère${reste.length > 1 ? 's' : ''} — ${nombre(reste.reduce((t, l) => t + l.n, 0))} actes, dont ${nombre(reste.reduce((t, l) => t + l.lies, 0))} liés à une loi`}
          </button>
        )}
      </div>

      {/* La légende dit les deux parts d'une barre. « Le titre ne le dit pas »
          n'est pas « sans loi » : l'absence de mention ne dit rien de l'acte
          (§2 règle 5), et le raisonnement est en méthodologie. */}
      <p className="adg-legende">
        <i aria-hidden="true" className="adg-cle adg-cle--lie" />actes dont le titre cite une loi
        <i aria-hidden="true" className="adg-cle adg-cle--muet" />le titre ne le dit pas
        <span className="adg-legende-limite">« Le titre ne le dit pas » ne veut pas dire « sans loi ».</span>
      </p>

      {lois.length > 0 && (
        <div>
          <button aria-expanded={ouvert === LOIS} className="adg-plus" onClick={() => basculer(LOIS)} type="button">
            {ouvert === LOIS ? '▾' : '▸'} {nombre(lois.length)} loi{lois.length > 1 ? 's' : ''} citée{lois.length > 1 ? 's' : ''} dans le titre d’un acte
          </button>
          {ouvert === LOIS && <Lois lois={lois} ministere={null} />}
        </div>
      )}
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
        {/* La limite se dit là où le nombre se lit : « délai 12 ans » se lirait
            comme douze ans d'inaction. */}
        {' '}Le délai est celui du premier acte <i>de cette période</i> : une loi ancienne a pu en recevoir avant.
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

function Actes({ cellules, exemples }) {
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
        <Acte key={`${a.i}-${a.d}`} acte={a} />
      ))}
    </div>
  );
}

function Acte({ acte }) {
  return (
    <div className="adg-acte">
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
