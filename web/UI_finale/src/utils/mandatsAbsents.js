/* ── LES MANDATS QUE LA SOURCE DEVRAIT PORTER, ET NE PORTE PAS (#859) ────────
 *
 * `mandats_absents_de_la_source` est une table relue à la main, comme
 * `mandats_anterieurs` (#860) : une ligne par mandat, chacune sur sa source
 * primaire. Ce qui les sépare est leur date. Les mandats antérieurs précèdent
 * le 19 juin 2002, date où commence le fichier de l'Assemblée ; ceux-ci la
 * SUIVENT, et manquent quand même — le fichier ne porte aucun gouvernement
 * avant le 17 mai 2007, et il lui arrive d'omettre un mandat de député.
 *
 * ILS ONT LEUR LIGNE À EUX, parce que la phrase des mandats antérieurs —
 * « exercés avant le 19 juin 2002 » — serait fausse pour eux. Arbitré par la
 * propriétaire le 07/10/2026 : même section (« Ce qu'on n'a pas pu lire »),
 * même forme, une phrase qui dit leurs propres dates.
 *
 * Une fiche NON RELUE (`null`) ne produit aucune ligne, pour la raison écrite
 * sous les mandats antérieurs : elle parlerait de notre travail, pas de cette
 * personne.
 *
 * Ce module n'importe rien : `tests/test_mention_mandats_absents_859.py`
 * l'exécute sur les lignes copiées de `config/mandats_anterieurs.json`.
 *
 * → `docs/decisions/mandats-absents-de-la-source-859.md`
 */

const MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'];

const jour = (iso) => {
  const j = Number(iso.slice(8, 10));
  return `${j === 1 ? '1er' : j} ${MOIS[Number(iso.slice(5, 7)) - 1]} ${iso.slice(0, 4)}`;
};

export const CLE_MANDATS_ABSENTS = 'mandats-absents-de-la-source';

export function limiteMandatsAbsents(absents) {
  const lignes = Array.isArray(absents) ? absents : [];
  if (!lignes.length) return null;

  const n = lignes.length;
  const pluriel = n > 1;
  const parInstitution = lignes.reduce((acc, m) => {
    acc[m.institution] = (acc[m.institution] || 0) + 1;
    return acc;
  }, {});
  const detail = [
    parInstitution.assemblee_nationale ? `${parInstitution.assemblee_nationale} à l’Assemblée` : null,
    parInstitution.gouvernement ? `${parInstitution.gouvernement} au gouvernement` : null,
  ].filter(Boolean);

  /* Les dates ne s'écrivent que si TOUTES les lignes les portent : une borne
   * calculée sur une partie des mandats daterait à tort les autres (§2 règle 5). */
  const debuts = lignes.map((m) => m.debut).filter(Boolean).sort();
  const fins = lignes.map((m) => m.fin).filter(Boolean).sort();
  const dates = debuts.length === n && fins.length === n
    ? ` entre le ${jour(debuts[0])} et le ${jour(fins[n - 1])}`
    : '';

  return {
    cle: CLE_MANDATS_ABSENTS,
    titre: 'Mandats absents de la source',
    texte:
      `${n} mandat${pluriel ? 's' : ''} exercé${pluriel ? 's' : ''}${dates}`
      + (detail.length > 1 ? ` — ${detail.join(', ')} —` : '')
      + ` ${pluriel ? 'sont cités' : 'est cité'} depuis ${pluriel ? 'leur' : 'sa'} source primaire. `
      + 'Aucune activité n’y est collectée.',
  };
}
