/* ── La recherche sur une fiche (#979) ───────────────────────────────────────
 *
 * La barre, l'étiquette posée en tête de chaque figure et la note d'une section
 * où le mot ne trouve rien. Une seule définition pour la fiche candidat et la
 * fiche de groupe : les arbitrages du 17/09/2026 — « Rechercher sur cette
 * page », « Contenant « … » », jamais « Non collecté » sous un mot — valent
 * pour les deux. */
import './Recherche.css';

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
  return (
    <p className="cp-filtre-etiquette">
      Contenant <mark>« {mot} »</mark>
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
