import { datesDesFamilles } from '../utils/sourcesDesBulles';

/* « À JOUR AU » (#1389) : la dernière relecture réussie de chaque famille de
 * données, écrite par chaque run dans `pivot_data/fraicheur_sources.json` et
 * copiée par `scripts/sync-data.mjs`. Un seul fichier pour tout le site : il
 * se charge une fois. Absent ou illisible, les bulles n'ont pas de pied — on
 * n'invente pas de date (§2 règle 5). */
let promesse = null;
/** Le fichier tel quel, ou `null` s'il manque. */
export function getFraicheur() {
  if (!promesse) {
    promesse = fetch('/data/fraicheur_sources.json')
      .then((r) => (r.ok ? r.json() : null), () => null);
  }
  return promesse;
}

export function getDatesDesFamilles() {
  return getFraicheur().then((f) => datesDesFamilles(f), () => ({}));
}
