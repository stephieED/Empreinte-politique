/*
 * UNE FONCTION GOUVERNEMENTALE, reconnue dans ce que le compte rendu publie.
 *
 * La règle vivait dans `parolesParPeriode.js`, qui n'est importable que par
 * Vite. La projection de build en a besoin aussi — la parole prononcée comme
 * membre du gouvernement ne compte pas pour un groupe (`paroleDeGroupe.js`) —
 * et une règle recopiée divergerait au premier correctif : elle est ici, une
 * fois, pour les deux.
 *
 * Les deux apostrophes : le compte rendu écrit « secrétaire d’État » avec la
 * typographique, et la droite seule ne l'attrapait pas.
 */
export const FONCTION_GOUVERNEMENTALE = /ministre|secrétaire d['’]état|premier ministre/i;

export function estFonctionGouvernementale(fonction) {
  return Boolean(fonction) && FONCTION_GOUVERNEMENTALE.test(fonction);
}
