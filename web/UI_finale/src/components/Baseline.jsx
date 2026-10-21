import './Baseline.css';

/* ── LA BASELINE (#1026) ──────────────────────────────────────────────────────
 *
 * « 100 % automatisé • 100 % sourcé • 0 score • 0 filtre ». La promesse était
 * écrite là où elle ne se lit pas : dans le `<title>`, dans la `meta
 * description` et dans l'introduction de /methodologie. Elle se lit maintenant
 * aux deux endroits où un lecteur arrive — le bandeau de l'accueil et le pied
 * de page, sous la marque, sur toutes les pages.
 *
 * PAS DANS L'EN-TÊTE COLLÉ : arbitré le 18/09/2026. Une phrase répétée en haut
 * de chaque écran devient du décor, et la rangée est à hauteur fixe (#968).
 *
 * QUATRE MENTIONS, UNE SEULE DÉFINITION. Elles sont ici, pas recopiées dans
 * deux composants : une promesse écrite deux fois est une promesse qui
 * divergera. Les séparateurs sont décoratifs — un lecteur d'écran lit les
 * quatre mentions, pas les puces.
 *
 * CE QUE CHAQUE MOT ENGAGE (§2) : « automatisé » porte sur la COLLECTE et la
 * mise en forme, ce que /methodologie détaille — aucun fait n'est écrit ni
 * altéré à la main. « 0 score, 0 filtre » énonce les règles 1 et 8 : ni note,
 * ni classement, et aucune sélection éditoriale de ce qui est publié. Le
 * filtre par intitulé de la fiche (#979) est un outil de lecture du visiteur,
 * qui ne retire rien du corpus publié.
 */
/* L'espace avant le % est insécable : « 100 » et « % » ne se séparent pas en
 * fin de ligne, et le pied de page passe sur deux lignes sous 900 px. */
export const BASELINE = ['100\u00a0% automatisé', '100\u00a0% sourcé', '0 score', '0 filtre'];

/* LES TUILES (bandeau d'À propos, forme C arbitrée le 21/10/2026) : la même
 * devise, le chiffre en grand et son mot dessous. Le chiffre est ce qui précède
 * le dernier mot : « 100 % » / « automatisé », « 0 » / « score ». */
const enTuile = (mention) => {
  const i = mention.lastIndexOf(' ');
  return { chiffre: mention.slice(0, i), mot: mention.slice(i + 1) };
};

export default function Baseline({ className = '', tuiles = false }) {
  if (tuiles) {
    return (
      <ul className={`baseline-tuiles${className ? ` ${className}` : ''}`}>
        {BASELINE.map((mention) => {
          const { chiffre, mot } = enTuile(mention);
          return (
            <li className="baseline-tuile" key={mention}>
              <b>{chiffre}</b> {mot}
            </li>
          );
        })}
      </ul>
    );
  }
  return (
    <p className={`baseline${className ? ` ${className}` : ''}`}>
      {BASELINE.map((mention, i) => (
        <span className="baseline-mention" key={mention}>
          {i > 0 && (
            <span aria-hidden="true" className="baseline-puce">
              •
            </span>
          )}
          {mention}
        </span>
      ))}
    </p>
  );
}
