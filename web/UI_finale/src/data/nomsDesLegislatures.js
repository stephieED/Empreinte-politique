/* Le nom d'une législature, « XVIe législature ».
 *
 * Module SANS IMPORT, comme `adressesParDefaut.js` : `scripts/pages-par-adresse.mjs`
 * le lit sous Node au build pour écrire le titre des pages servies sans
 * JavaScript (#1314). Une seule écriture du nom, pour la fiche et pour les
 * moteurs de recherche. */
export const ROMAINS = { 14: 'XIVe', 15: 'XVe', 16: 'XVIe', 17: 'XVIIe' };
export const nomDeLegislature = (id) => `${ROMAINS[Number(id)] || `${id}e`} législature`;
