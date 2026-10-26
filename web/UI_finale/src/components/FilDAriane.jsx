import { useEffect, useId, useMemo, useRef, useState } from 'react';
import { Link, useLocation, useSearchParams } from 'react-router-dom';
import { getCandidatesList, getGovernmentsList, getGroupsList, getLegislaturesList } from '../data';
import { PERIODES, periodeValide } from '../utils/filtrePeriode';
import './FilDAriane.css';

/* ── Le fil d'Ariane de chaque fiche, qui sert aussi à en changer (#1329) ─────
 *
 * IL REMPLACE LE TIROIR. #1025 voulait un seul endroit pour choisir sa fiche,
 * et c'était le tiroir « Chercher ou changer de fiche » du bandeau. Arbitré sur
 * maquette le 26/10/2026 (forme A) : cet endroit est désormais le fil d'Ariane
 * de la fiche. « Législature / XVe législature » devient cliquable ; le type
 * comme le nom ouvrent un menu à deux colonnes — les quatre types à gauche, les
 * fiches du type choisi à droite, la fiche courante cochée.
 *
 * LES CANDIDATS À PART (demandé le 26/10/2026). Sur une fiche de candidat, le
 * menu ne montre que les candidats : à gauche, deux affichages — l'ordre
 * alphabétique, ou par groupe, chaque groupe suivi de ses candidats —, à
 * droite la liste qu'ils donnent, sous un champ. Sur les autres fiches, il ne
 * les montre pas : le volet des candidats est borné à l'élection (AGENTS.md
 * §1), son entrée est la diapositive de l'accueil.
 *
 * L'ORDRE DES LISTES N'EST JAMAIS UN CLASSEMENT (AGENTS.md §2 règle 1) :
 * législatures et gouvernements du plus récent au plus ancien, groupes et
 * candidats dans l'ordre alphabétique — l'ordre où le manifeste les livre déjà,
 * qui n'est pas refait ici. Les candidats, une trentaine, ont un champ en tête.
 *
 * LA PÉRIODE SUIT LE FIL. Les cases « 6 derniers mois » et « 12 derniers mois »
 * (#1074) vivaient dans le tiroir ; elles s'alignent désormais au bout du fil,
 * sur les seules fiches qui portent les dates de ce qu'elles montrent. Elles
 * restent dans l'adresse (`?periode=6m`), exclusives comme avant.
 */

const TYPES = [
  { cle: 'candidats', libelle: 'Candidats', recherche: 'Chercher un candidat' },
  { cle: 'groupes', libelle: 'Groupes' },
  { cle: 'gouvernements', libelle: 'Gouvernements' },
  { cle: 'legislatures', libelle: 'Législatures' },
];

const annee = (iso) => (iso ? iso.slice(0, 4) : null);
/* « depuis 2024 », « 2022–2024 », « 2017 » : de quoi distinguer deux fiches du
 * même nom, rien de plus. */
function periodeEnAnnees(debut, fin) {
  const a0 = annee(debut);
  if (!a0) return null;
  if (!fin) return `depuis ${a0}`;
  const a1 = annee(fin);
  return a0 === a1 ? a0 : `${a0}–${a1}`;
}

/* Les quatre listes, ramenées à une forme : `{ id, nom, precision }`. Le
 * manifeste est déjà en mémoire après la première fiche : rien n'est retéléchargé. */
async function chargerLesListes() {
  const [candidats, groupes, gouvernements, legislatures] = await Promise.all([
    getCandidatesList(), getGroupsList(), getGovernmentsList(), getLegislaturesList(),
  ]);
  return {
    candidats: candidats.map((c) => ({ id: c.id, nom: c.nom, fiches: c.groupIds || [] })),
    groupes: groupes.map((g) => ({ id: g.id, nom: g.title, fiches: g.fiches || [] })),
    gouvernements: gouvernements.map((g) => ({ id: g.id, nom: g.title, precision: periodeEnAnnees(g.debut, g.fin) })),
    legislatures: legislatures.map((l) => ({ id: l.id, nom: l.title, precision: periodeEnAnnees(l.debut, l.fin) })),
  };
}

/* Les deux affichages de la liste des candidats. */
const AFFICHAGES = [
  { cle: 'alpha', libelle: 'Ordre alphabétique' },
  { cle: 'groupe', libelle: 'Par groupe' },
];

const normaliser = (s) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();

/** Les cases de période, au bout du fil. Elles écrivent l'adresse, comme le
 *  faisait le tiroir ; la page la lit. */
function CasesPeriode() {
  const [params, setParams] = useSearchParams();
  const periode = periodeValide(params.get('periode'));
  const changer = (valeur) => {
    setParams((p) => {
      const suivant = new URLSearchParams(p);
      if (valeur !== periode) suivant.set('periode', valeur);
      else suivant.delete('periode');
      return suivant;
    }, { replace: true });
  };
  return (
    <div className="periode fil-periode" role="group" aria-label="Période">
      {Object.entries(PERIODES).map(([cle, p]) => (
        <label className="periode-case" key={cle}>
          <input checked={periode === cle} id={`periode-${cle}`} onChange={() => changer(cle)} type="checkbox" />
          {p.libelle}
        </label>
      ))}
    </div>
  );
}

/**
 * @param {string} type     'candidats' | 'groupes' | 'gouvernements' | 'legislatures'
 * @param {string} libelle  Le premier maillon, tel que la fiche l'écrivait (« Gouvernement »).
 * @param {string} id       L'identifiant de la fiche courante, cochée dans sa liste.
 * @param {string} nom      Le second maillon.
 * @param {boolean} periode Les cases de période au bout du fil.
 * @param {boolean} ouvertAuDepart Le menu est ouvert à l'arrivée : la page des
 *                  candidats, qui n'a pas de fiche à montrer (`ChoixDuCandidatPage`).
 */
export default function FilDAriane({ type, libelle, id = null, nom = null, periode = false, ouvertAuDepart = false }) {
  const [ouvert, setOuvert] = useState(ouvertAuDepart);
  const [vu, setVu] = useState(type);
  const [listes, setListes] = useState(null);
  const [saisie, setSaisie] = useState('');
  const [affichage, setAffichage] = useState('alpha');
  const surUnCandidat = type === 'candidats';
  const types = surUnCandidat ? TYPES.filter((t) => t.cle === 'candidats') : TYPES.filter((t) => t.cle !== 'candidats');
  const racine = useRef(null);
  /* Le bouton qui a ouvert le menu : Échap lui rend le focus, comme la bulle
   * d'information (`InfoBulle.jsx`) — sans quoi le lecteur au clavier repart
   * du haut de la page. */
  const ouvreur = useRef(null);
  const menuId = useId();
  const { pathname } = useLocation();

  // Changer de page referme le menu — sauf à l'arrivée sur une page qui le
  // veut ouvert. L'adresse précédente est comparée, et non un drapeau de
  // premier rendu, que le double rendu de développement de React consomme.
  const adresseVue = useRef(pathname);
  useEffect(() => {
    if (adresseVue.current === pathname) return;
    adresseVue.current = pathname;
    setOuvert(false);
  }, [pathname]);

  useEffect(() => {
    if (!ouvert || listes) return undefined;
    let vivant = true;
    chargerLesListes().then((l) => vivant && setListes(l), () => vivant && setListes({}));
    return () => { vivant = false; };
  }, [ouvert, listes]);

  useEffect(() => {
    if (!ouvert) return undefined;
    const surClic = (e) => {
      if (racine.current && !racine.current.contains(e.target)) setOuvert(false);
    };
    const surTouche = (e) => {
      if (e.key !== 'Escape') return;
      setOuvert(false);
      ouvreur.current?.focus();
    };
    document.addEventListener('mousedown', surClic);
    document.addEventListener('keydown', surTouche);
    return () => {
      document.removeEventListener('mousedown', surClic);
      document.removeEventListener('keydown', surTouche);
    };
  }, [ouvert]);

  const ouvrir = (e) => {
    ouvreur.current = e.currentTarget;
    setVu(type);
    setSaisie('');
    setOuvert((o) => !o);
  };

  const typeVu = types.find((t) => t.cle === vu) || types[0];
  const objets = useMemo(() => {
    const liste = listes?.[typeVu.cle] || [];
    if (!typeVu.recherche || !saisie.trim()) return liste;
    const mot = normaliser(saisie.trim());
    return liste.filter((o) => normaliser(o.nom).includes(mot));
  }, [listes, typeVu, saisie]);
  /* PAR GROUPE (candidats seulement) : les groupes du site dont au moins un
   * candidat a été membre, dans l'ordre alphabétique — jamais rangés par leur
   * nombre de candidats (§2 règle 1) —, chacun suivi de ses candidats. Un
   * groupe se lit comme une lignée : « Socialistes » réunit les membres de
   * chacun de ses maillons. Un candidat passé par deux groupes figure sous les
   * deux ; ceux qui ne sont passés par aucun ferment la liste, sous « Sans
   * groupe connu à l'Assemblée » (arbitré le 26/10/2026) : leur groupe au
   * Sénat ou au Parlement européen, lui, est souvent connu. */
  const parGroupe = useMemo(() => {
    if (!surUnCandidat || affichage !== 'groupe' || !listes) return [];
    const blocs = (listes.groupes || [])
      .map((g) => {
        const fiches = new Set(g.fiches);
        return { id: g.id, nom: g.nom, candidats: objets.filter((c) => c.fiches.some((f) => fiches.has(f))) };
      })
      .filter((b) => b.candidats.length);
    const places = new Set(blocs.flatMap((b) => b.candidats.map((c) => c.id)));
    const autres = objets.filter((c) => !places.has(c.id));
    return autres.length ? [...blocs, { id: '_autres', nom: 'Sans groupe connu à l’Assemblée', candidats: autres }] : blocs;
  }, [surUnCandidat, affichage, listes, objets]);

  const ligne = (o, cle = o.id) => {
    const courant = typeVu.cle === type && String(o.id) === String(id);
    return (
      <li key={cle}>
        <Link
          aria-current={courant ? 'page' : undefined}
          className={`fil-objet${courant ? ' fil-objet--courant' : ''}`}
          to={`/${typeVu.cle}/${o.id}`}
        >
          <span>{o.nom}</span>
          {courant ? <span aria-hidden="true">✓</span> : o.precision && <small>{o.precision}</small>}
        </Link>
      </li>
    );
  };

  const chevron = <span aria-hidden="true" className="fil-chevron">▾</span>;

  return (
    <div className="fil-rangee">
      <nav aria-label="Fil d’Ariane" className="fil" ref={racine}>
        <button aria-controls={menuId} aria-expanded={ouvert} className="fil-bouton" onClick={ouvrir} type="button">
          {libelle}{chevron}
        </button>
        {nom && (
          <>
            <span aria-hidden="true" className="fil-sep">/</span>
            <button aria-controls={menuId} aria-expanded={ouvert} className="fil-bouton fil-bouton--courant" onClick={ouvrir} type="button">
              {nom}{chevron}
            </button>
          </>
        )}
        <div className="fil-menu" hidden={!ouvert} id={menuId}>
          {ouvert && (
            <>
              <ul className="fil-types">
                {surUnCandidat ? AFFICHAGES.map((a) => (
                  <li key={a.cle}>
                    <button
                      aria-pressed={a.cle === affichage}
                      className="fil-type"
                      onClick={() => setAffichage(a.cle)}
                      type="button"
                    >
                      {a.libelle}<span aria-hidden="true">›</span>
                    </button>
                  </li>
                )) : types.map((t) => (
                  <li key={t.cle}>
                    <button
                      aria-pressed={t.cle === vu}
                      className="fil-type"
                      onClick={() => { setVu(t.cle); setSaisie(''); }}
                      type="button"
                    >
                      {t.libelle}<span aria-hidden="true">›</span>
                    </button>
                  </li>
                ))}
              </ul>
              <div className="fil-objets">
                {typeVu.recherche && (
                  <label className="fil-recherche">
                    <svg aria-hidden="true" height="14" viewBox="0 0 16 16" width="14">
                      <circle cx="7" cy="7" fill="none" r="5" stroke="currentColor" strokeWidth="1.6" />
                      <path d="M11 11l3.5 3.5" stroke="currentColor" strokeLinecap="round" strokeWidth="1.6" />
                    </svg>
                    <input
                      aria-label={typeVu.recherche}
                      autoComplete="off"
                      onChange={(e) => setSaisie(e.target.value)}
                      placeholder={typeVu.recherche}
                      type="search"
                      value={saisie}
                    />
                  </label>
                )}
                {surUnCandidat && affichage === 'groupe' ? (
                  <ul className="fil-liste">
                    {parGroupe.map((g) => (
                      <li className="fil-bloc" key={g.id}>
                        <span className="fil-bloc-titre">{g.nom}</span>
                        <ul className="fil-liste">{g.candidats.map((c) => ligne(c, `${g.id}-${c.id}`))}</ul>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <ul className="fil-liste">{objets.map((o) => ligne(o))}</ul>
                )}
              </div>
            </>
          )}
        </div>
      </nav>
      {periode && <CasesPeriode />}
    </div>
  );
}
