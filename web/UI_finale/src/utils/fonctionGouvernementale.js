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
 *
 * `fonction` EST DU TEXTE LIBRE DE LA SOURCE, et la règle se complète depuis
 * les valeurs RÉELLES, jamais depuis des exemples (#1206). Relevées le
 * 04/10/2026 sur les 231 194 prises de parole qui portent le champ, 1 402
 * profils, 529 valeurs distinctes : trois mots en reconnaissaient 244 et en
 * manquaient trois familles —
 *   « garde des sceaux », écrit SANS « ministre de la justice » sur 9 140
 *   prises de parole de quatre personnes, qui passaient pour une parole de
 *   député ;
 *   « secrétaire d’Etat », sans accent sur la capitale, une fois ;
 *   « haut-commissaire », 79 prises de parole d'une personne, toutes datées
 *   pendant sa période au gouvernement d'après la source — retenu par la
 *   propriétaire le 04/10/2026. Le féminin n'existe pas dans le relevé : il
 *   n'est pas deviné, il s'ajoutera le jour où la source l'écrira.
 * Aucune valeur reconnue n'est un faux positif : ni « ancien ministre », ni
 * fonction parlementaire.
 */
export const FONCTION_GOUVERNEMENTALE = /ministre|secrétaire d['’][ée]tat|garde des sceaux|haut-commissaire/i;

export function estFonctionGouvernementale(fonction) {
  return Boolean(fonction) && FONCTION_GOUVERNEMENTALE.test(fonction);
}
