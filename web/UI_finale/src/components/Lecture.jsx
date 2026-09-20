/*
 * Fondations de lecture — la forme des six règles (issue #326).
 *
 * Les règles elles-mêmes sont dans `utils/lecture.js` : ce fichier ne décide
 * rien, il rend. Les lots 2, 3 et 4 consomment ces primitives ; ils n'en
 * écrivent pas de seconde version.
 */
import './Lecture.css';
import {
  READING_LEVELS,
  emptyListMessage,
  formatNumber,
  ratio,
  sourceBadge,
  styleForPosition,
  truncation,
} from '../utils/lecture';

/*
 * Une position exprimée porte sa couleur ; `non_votant` et toute valeur
 * inconnue portent un contour tireté et aucune teinte — c'est ce qui empêche
 * les valeurs de se lire comme un dégradé du meilleur au pire.
 */
export function PositionVote({ position }) {
  const style = styleForPosition(position);

  if (!style.label) return null;

  return (
    <span
      className={`lec-position${style.outlined ? ' lec-position--contour' : ''}`}
      style={style.color ? { color: style.color } : undefined}
    >
      <span
        className="lec-position-dot"
        style={style.color ? { background: style.color } : undefined}
      />
      {style.label}
    </span>
  );
}

/*
 * Jamais un pourcentage seul. Le dénominateur est nommé dans la phrase, pas
 * seulement compté.
 */
export function Ratio({ numerator, denominator, denominatorLabel, caveat }) {
  const r = ratio(numerator, denominator, denominatorLabel);

  if (!r.available) {
    return (
      <p className="lec-ratio lec-ratio--nd">
        <span className="lec-ratio-nd">N/D</span>
        <span className="lec-ratio-den">{denominatorLabel}</span>
      </p>
    );
  }

  return (
    <div className="lec-ratio">
      <p className="lec-ratio-line">
        <span className="lec-ratio-num">{formatNumber(r.numerator)}</span>
        <span className="lec-ratio-den">
          sur {formatNumber(r.denominator)} {denominatorLabel}
        </span>
      </p>
      {caveat && <p className="lec-caveat">{caveat}</p>}
    </div>
  );
}

/*
 * Une liste coupée annonce sa règle de coupe à côté du nombre coupé, ou elle
 * n'est pas coupée.
 */
export function Troncature({ shown, total, rule }) {
  const t = truncation(shown, total, rule);
  if (!t.truncated) return null;
  return <p className="lec-troncature">{t.text}</p>;
}

/*
 * Le vide dit pourquoi. La cause est celle du bloc `couverture` du profil, et
 * `motif` est la phrase que le pipeline a écrite pour ce profil-là.
 */
export function ListeVide({ cause, motif, source }) {
  const m = emptyListMessage(cause, motif);

  return (
    <div className={`lec-vide${m.known ? '' : ' lec-vide--inconnue'}`}>
      <p className="lec-vide-titre">{m.titre}</p>
      <p className="lec-vide-message">{m.message}</p>
      {source && <p className="lec-vide-source">{source}</p>}
    </div>
  );
}

/*
 * « Lien de source non publié » parle de nous ; « non vérifié » ferait porter
 * le doute sur la donnée. Voir `utils/lecture.js`.
 */
export function BadgeSource({ url }) {
  const badge = sourceBadge(url);

  if (!badge.verified) {
    return <span className="lec-badge lec-badge--absent">{badge.label}</span>;
  }

  return (
    <a className="lec-badge lec-badge--verifie" href={badge.href} rel="noreferrer" target="_blank">
      <span aria-hidden="true" className="lec-badge-tick">
        ✓
      </span>
      {badge.label}
    </a>
  );
}

/*
 * Les trois mêmes niveaux sur les trois types de profil.
 */
export function NiveauxLecture({ actif, onChange }) {
  return (
    <div className="lec-niveaux" role="tablist">
      {READING_LEVELS.map((niveau) => (
        <button
          aria-selected={niveau.id === actif}
          className={`lec-niveau${niveau.id === actif ? ' lec-niveau--actif' : ''}`}
          key={niveau.id}
          onClick={() => onChange?.(niveau.id)}
          role="tab"
          type="button"
        >
          {niveau.label}
          <span className="lec-niveau-duree">{niveau.duree}</span>
        </button>
      ))}
    </div>
  );
}

