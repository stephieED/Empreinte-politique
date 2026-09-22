/* ── La recherche sur une fiche (#979) ───────────────────────────────────────
 *
 * La barre, l'étiquette posée en tête de chaque figure et la note d'une section
 * où le mot ne trouve rien. Une seule définition pour la fiche candidat et la
 * fiche de groupe : les arbitrages du 17/09/2026 — « Rechercher sur cette
 * page », « Contenant « … » », jamais « Non collecté » sous un mot — valent
 * pour les deux. */
import { createContext, useContext } from 'react';
import { libelleDebut } from '../utils/filtrePeriode';
import './Recherche.css';

/* LA PÉRIODE CHOISIE (#1074), fournie par la page : la date de début de la
 * fenêtre, ou null. L'étiquette et les messages vides la lisent, pour qu'une
 * capture ne circule jamais sans sa fenêtre. */
export const PeriodeContext = createContext(null);

/** Un filtre est actif dès qu'un mot OU une période l'est : la fiche se
 *  comporte alors de la même façon — sections des mandats retirées, vides dits
 *  comme ceux du filtre et jamais comme ceux d'une collecte (§2 règle 5). */
export function useFiltreActif(mot) {
  const debut = useContext(PeriodeContext);
  return Boolean(mot) || Boolean(debut);
}

/** La condition d'un vide, en toutes lettres : « dont l'intitulé contient
 *  « … » », « depuis le … », ou les deux. Le nom de la liste reste au message. */
export function Condition({ critere, mot }) {
  const debut = useContext(PeriodeContext);
  return (
    <>
      {mot && <> {critere} {MOT(mot)}</>}
      {debut && <> {libelleDebut(debut)}</>}
    </>
  );
}

export function BarreFiltre({ saisie, onSaisie }) {
  return (
    <div className="cp-filtre" role="search">
      <svg aria-hidden="true" height="16" viewBox="0 0 16 16" width="16">
        <circle cx="7" cy="7" fill="none" r="5" stroke="currentColor" strokeWidth="1.6" />
        <path d="M11 11l3.5 3.5" stroke="currentColor" strokeLinecap="round" strokeWidth="1.6" />
      </svg>
      <input
        aria-label="Rechercher sur cette page"
        autoComplete="off"
        id="cp-filtre-mot"
        onChange={(e) => onSaisie(e.target.value)}
        placeholder="Rechercher sur cette page"
        type="search"
        value={saisie}
      />
      {saisie && (
        <button className="cp-filtre-raz" onClick={() => onSaisie('')} type="button">
          Effacer
        </button>
      )}
    </div>
  );
}

export function EtiquetteFiltre({ mot }) {
  const debut = useContext(PeriodeContext);
  if (!mot && !debut) return null;
  return (
    <p className="cp-filtre-etiquette">
      {mot && <>Contenant <mark>« {mot} »</mark></>}
      {mot && debut && <span className="cp-filtre-sep"> · </span>}
      {debut && <span className="cp-filtre-periode">{libelleDebut(debut)}</span>}
    </p>
  );
}

export function VideDuFiltre({ mot, children, tete = null }) {
  return (
    <div className="cp-carte">
      <EtiquetteFiltre mot={mot} />
      {tete}
      <p className="cp-note cp-filtre-vide">{children}</p>
    </div>
  );
}

export const MOT = (mot) => <mark className="cp-filtre-mot">« {mot} »</mark>;
