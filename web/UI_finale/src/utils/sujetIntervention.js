/*
 * LE SUJET D'UNE INTERVENTION — la règle de la fiche candidat, dans un module
 * que le build peut importer (les scripts de build exigent des imports avec
 * extension, ce que `parolesParPeriode.js` ne tient pas).
 *
 * La fiche de groupe la lit depuis le 04/10/2026 : elle ne gardait que
 * `theme_officiel` et JETAIT toute intervention sans thème — 969 prises de
 * parole d'Écologie Démocratie Solidarité, toutes écartées, et une section qui
 * affichait 0. Une intervention sans intitulé reste une prise de parole : elle
 * se compte dans sa nature et se range sous « Intitulé non publié » (§2 règle 5).
 */
/** Les types dont le sujet est la FEUILLE du chemin, et non sa racine. */
export const SUJET_EN_FEUILLE = new Set([
  'question_gouvernement',
  'question',
  'question_orale',
]);

export const SUJET_NON_PUBLIE = 'Intitulé non publié';
export const SEPARATEUR_CHEMIN = '>';

/* Le chemin brut, dans l'ordre où la collecte le rend disponible. Les trois
 * champs ne se contredisent pas : `point_ordre_du_jour` est le chemin complet,
 * `theme_officiel` le porte quand la collecte s'est arrêtée au thème (#657), et
 * `sujet` est la feuille déjà isolée par le parseur. */
export function cheminDuPoint(intervention) {
  const i = intervention || {};
  return i.dossier?.point_ordre_du_jour || i.theme_officiel || i.sujet || null;
}

export function segmentsDuChemin(chemin) {
  return (chemin || '')
    .split(SEPARATEUR_CHEMIN)
    .map((s) => s.trim())
    .filter(Boolean);
}

/** Le sujet d'une intervention : la feuille ou la racine, selon son type. */
export function sujetDeIntervention(intervention) {
  const segments = segmentsDuChemin(cheminDuPoint(intervention));
  if (!segments.length) return null;
  return SUJET_EN_FEUILLE.has(intervention?.type_detail)
    ? segments[segments.length - 1]
    : segments[0];
}
