/* ── Les articles publiés, lus une fois (#1329) ──────────────────────────────
 *
 * `public/rapports.json` est écrit par `scripts/index-rapports.mjs` depuis le
 * dossier des articles, du plus récent au plus ancien. Trois lecteurs : le
 * carrousel de l'accueil, le bandeau « Articles » et les fiches de législature
 * et de gouvernement (« Articles sur cette période »). Un échec rend une liste
 * vide : un encart vide dirait qu'il manque quelque chose (§2 règle 5) là où
 * il n'y a simplement pas d'article.
 */

/* L'ÉVÉNEMENT DES CANDIDATS (#1329, arbitré le 22/10/2026) : la première
 * diapositive du carrousel et la première carte du bandeau, jusqu'à cette date. */
export const FIN_EVENEMENT_CANDIDATS = '2027-06-01';

const MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'];

/** « 13 octobre 2026 », « 1er mai 2026 ». */
export function dateEnClair(iso) {
  const jour = Number(iso.slice(8, 10));
  return `${jour === 1 ? '1er' : jour} ${MOIS[Number(iso.slice(5, 7)) - 1]} ${iso.slice(0, 4)}`;
}

let promesse = null;
export function getArticles() {
  if (!promesse) {
    promesse = fetch('/rapports.json')
      .then((r) => (r.ok ? r.json() : []), () => [])
      .then((l) => (Array.isArray(l) ? l : []), () => []);
  }
  return promesse;
}

/** Les articles dont la date tombe dans une période, bornes comprises ; une
 *  période ouverte court jusqu'à aujourd'hui. Un article publié ne se modifie
 *  pas : c'est la fiche qui renvoie à l'article, jamais l'inverse. */
export function articlesDeLaPeriode(articles, debut, fin) {
  if (!debut) return [];
  const borne = fin || new Date().toISOString().slice(0, 10);
  return (articles || []).filter((a) => a.date && a.date >= debut && a.date <= borne);
}
