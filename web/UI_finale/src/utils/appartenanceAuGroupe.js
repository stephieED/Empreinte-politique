/* ── UN VOTE NE SE COMPARE QU'AU GROUPE DU JOUR (#1159) ──────────────────────
 *
 * Une fiche de groupe couvre toute une législature ; une personne peut l'avoir
 * quittée en cours de route. Sans la date, ses votes d'après étaient comparés à
 * un groupe dont elle n'était plus membre, et un même scrutin à deux groupes :
 * Delphine Batho, sortie du groupe socialiste en mai 2018, y était comparée
 * jusqu'en 2022 ; Olivier Becht, passé de l'UDI à Agir en mai 2020, aux deux.
 * Un « écart » avec un groupe dont on n'est pas membre est un fait faux.
 *
 * Les périodes sont celles que la fiche de groupe publie pour ce membre
 * (`membres[].periodes`, sinon `debut_dans_groupe` / `fin_dans_groupe`).
 * `null` — membre inconnu de l'appelant, ou aucune date publiée — ne filtre
 * rien : on ne sait pas, et on ne retire pas ce qu'on ne sait pas dater.
 * Entre deux groupes, il n'y a rien à comparer, et la section ne compare rien.
 *
 * Ce module n'importe rien : `tests/test_ecarts_au_groupe_du_jour_1159.py`
 * l'exécute.
 */
export function periodesDansLeGroupe(fiche, membreId) {
  if (!membreId) return null;
  const membre = (fiche.membres || []).find((m) => m.membre_id === membreId);
  if (!membre) return null;
  const periodes = (membre.periodes?.length ? membre.periodes
    : [{ debut: membre.debut_dans_groupe, fin: membre.fin_dans_groupe }]).filter((p) => p.debut);
  return periodes.length ? periodes : null;
}

export function etaitMembreLe(periodes, date) {
  if (!periodes) return true;
  const jour = typeof date === 'string' ? date.slice(0, 10) : null;
  if (!jour) return false;
  return periodes.some((p) => jour >= p.debut && (!p.fin || jour <= p.fin));
}
