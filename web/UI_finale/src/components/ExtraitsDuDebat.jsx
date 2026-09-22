import { Fragment, useEffect, useState } from 'react';
import { extraitsDuDebat } from '../utils/extraits';
import { segmentsSurlignes } from '../utils/filtreIntitule';
import { formatNumber } from '../utils/lecture';
import './ExtraitsDuDebat.css';

/* ── Ce qui a été dit, dans un débat ouvert (#1029) ───────────────────────────
 *
 * Les extraits d'un débat, du plus récent au plus ancien : la date, les 280
 * premiers caractères du propos, et le lien vers la prise de parole à son
 * ancre sur la page de séance de l'AN (#1087) — le texte entier est là. Un
 * extrait coupé finit par « … » : c'est l'affichage qui l'ajoute, le verbatim
 * publié n'en porte pas.
 *
 * Aucun compte par personne (§2 règles 1 et 7) : rien n'est additionné par nom.
 */
const jour = (iso) => (iso ? `${iso.slice(8, 10)}/${iso.slice(5, 7)}/${iso.slice(0, 4)}` : '');
const MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'];
const jourLong = (iso) => {
  if (!iso) return '';
  const j = Number(iso.slice(8, 10));
  return `${j === 1 ? '1er' : j} ${MOIS[Number(iso.slice(5, 7)) - 1]} ${iso.slice(0, 4)}`;
};

/** Le paquet d'extraits d'un débat : `undefined` pendant le chargement, `null`
 *  s'il manque. `cle` nomme le paquet — le chargement ne se refait que si elle
 *  change ; `null` : rien à charger. */
export function usePaquetExtraits(cle, charger) {
  const [etat, setEtat] = useState({ cle: null, paquet: undefined });
  useEffect(() => {
    if (!cle) return undefined;
    let vivant = true;
    Promise.resolve(charger()).then((p) => { if (vivant) setEtat({ cle, paquet: p ?? null }); });
    return () => { vivant = false; };
    // `charger` change à chaque rendu ; `cle` nomme ce qu’il charge.
  }, [cle]);
  return etat.cle === cle ? etat.paquet : undefined;
}

/** Les propos d'UN membre dans un débat — forme A, retenue sur maquette le
 *  22/09/2026 : chaque propos daté, en citation, avec « Lire la suite au
 *  compte rendu » ; les séances sans propos rapporté (collecte au thème seul)
 *  réunies en pastilles datées, une par séance, chacune vers son compte rendu. */
export function ProposDuMembre({ extraits, mots = [], saisie = '', parPage = 5 }) {
  const [montres, setMontres] = useState(parPage);
  const cites = extraits.filter((e) => e.texte);
  const seances = [];
  for (const e of extraits) {
    if (e.texte || seances.some((x) => x.date === e.date)) continue;
    seances.push(e);
  }
  seances.sort((a, b) => a.date.localeCompare(b.date));
  if (!cites.length && !seances.length) return null;
  return (
    <div className="xd-propos">
      {cites.slice(0, montres).map((e) => (
        <div className="xd-cite" key={e.id || e.date}>
          <span className="xd-date">{jour(e.date)}</span>
          <div className="xd-cite-corps">
            <p className="xd-texte xd-texte--nu">
              {mots.length
                ? segmentsSurlignes(e.texte, saisie).map((s, k) => (s.marque
                  ? <mark className="xd-mot" key={k}>{s.texte}</mark>
                  : <Fragment key={k}>{s.texte}</Fragment>))
                : e.texte}
              {e.tronque && ' …'}
            </p>
            {e.url && (
              <a className="xd-source" href={e.url} target="_blank" rel="noreferrer">
                Lire la suite au compte rendu ↗
              </a>
            )}
          </div>
        </div>
      ))}
      {cites.length > montres && (
        <button className="xd-plus" type="button" onClick={() => setMontres((n) => n + parPage)}>
          Afficher les {formatNumber(Math.min(parPage, cites.length - montres))} suivants
          {' '}({formatNumber(cites.length - montres)} restants)
        </button>
      )}
      {seances.length > 0 && (
        <div className="xd-seances">
          <span className="xd-muet">
            Propos non rapportés : cette parole est collectée au thème seul. Chaque séance mène au compte rendu.
          </span>
          <div>
            {seances.map((e) => (
              e.url
                ? <a className="xd-chip" href={e.url} key={e.date} target="_blank" rel="noreferrer">{jour(e.date)} ↗</a>
                : <span className="xd-chip" key={e.date}>{jour(e.date)}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/** Le débat ouvert de la fiche de groupe, en forme A comme la fiche de
 *  gouvernement : chaque député à gauche, ses propos datés à droite. Arbitré le
 *  22/09/2026 (option A) : l'orateur est NOMMÉ, jamais compté — la colonne de
 *  gauche ne porte ni nombre de prises de parole ni rang, seulement le nom et
 *  les dates. Les députés se suivent du plus récent au plus ancien propos. */
export function ProposParOrateur({ charger, cle, sujet, nomDe, mots = [], saisie = '', debut = null, parIntitule = false }) {
  const paquet = usePaquetExtraits(cle, charger);
  if (paquet === undefined) return <p className="xd-attente">Chargement des prises de parole…</p>;
  const extraits = extraitsDuDebat(paquet?.[sujet], { mots, debut, parIntitule });
  if (!extraits.length) return <p className="xd-attente">Aucune prise de parole détaillée pour ce débat{debut ? ' sur la période' : ''}.</p>;
  const parOrateur = new Map();
  for (const e of extraits) {
    const liste = parOrateur.get(e.orateur) || [];
    liste.push(e);
    parOrateur.set(e.orateur, liste);
  }
  const orateurs = [...parOrateur.entries()]
    .map(([orateur, liste]) => ({ orateur, liste, premiere: liste.at(-1).date, derniere: liste[0].date }))
    .sort((a, b) => b.derniere.localeCompare(a.derniere) || String(nomDe(a.orateur)).localeCompare(String(nomDe(b.orateur)), 'fr'));
  return (
    <div className="xd-orateurs">
      {orateurs.map((o) => (
        <div className="xd-membre" key={o.orateur}>
          <div className="xd-membre-tete">
            <span className="xd-membre-nom">{nomDe(o.orateur)}</span>
            <span className="xd-date">
              {o.premiere === o.derniere ? jourLong(o.premiere) : `du ${jourLong(o.premiere)} au ${jourLong(o.derniere)}`}
            </span>
          </div>
          <ProposDuMembre extraits={o.liste} mots={mots} saisie={saisie} />
        </div>
      ))}
    </div>
  );
}
