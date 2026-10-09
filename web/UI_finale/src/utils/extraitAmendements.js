/**
 * L'extrait de l'index des amendements qu'UNE fiche de candidat lit (#1273).
 *
 * La fiche téléchargeait l'index entier de chaque législature où la personne a
 * déposé : mesuré le 09/10/2026 sur François Ruffin, 587 667 amendements et
 * 162 Mo de JSON lus par le navigateur pour 48 786 référencés, et une page
 * blanche de 10 à 14 secondes. `sync-data` écrit désormais, par candidat, les
 * seules entrées que son profil référence et les textes qu'elles visent.
 *
 * Même forme que l'index (`{ amendements, textes }`), pour que la jointure de
 * `pivotAdapter.js` lise l'un ou l'autre sans le savoir. Une entrée absente de
 * l'index reste absente de l'extrait : la vue en fait une donnée manquante,
 * comme avant (§2 règle 5).
 *
 * Module sans import : `sync-data` le lit au build et les tests l'exécutent
 * sous Node.
 */
export function extraitDesAmendements(index, ids) {
  const amendements = {};
  const textes = {};
  for (const id of ids) {
    const amendement = index?.amendements?.[id];
    if (!amendement) continue;
    amendements[id] = amendement;
    const vise = amendement.texte_vise;
    if (vise && index.textes?.[vise] && !textes[vise]) textes[vise] = index.textes[vise];
  }
  return { amendements, textes };
}
