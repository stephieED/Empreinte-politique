/*
 * LA TEINTE D'UNE MATIÈRE — et pourquoi il a fallu ouvrir une palette.
 *
 * `DESIGN_SYSTEM.md` §5 écrivait « aucune couleur n'était libre » : le jaune
 * signal est pris par la sélection, l'action et le badge de source, le vert et
 * le rouge par les positions de vote, le bleu et le bronze par les institutions
 * de la frise. C'était vrai du besoin d'alors — MARQUER UNE LIGNE dans une
 * liste, ce que la fiche résout par un filet d'encre sans teinte.
 *
 * Une figure qui distingue N MATIÈRES est un besoin différent, et il n'a pas de
 * solution sans teinte : une rampe d'encre placerait les matières sur une
 * échelle, ce que §2 règle 1 interdit. La palette ci-dessous est donc
 * CATÉGORIELLE et sans ordre — aucune teinte n'y est « meilleure », l'ordre
 * d'attribution suit le volume et rien d'autre.
 *
 * Elle vient de Paul Tol (qualitative « muted »), choisie pour rester
 * distinguable sous les trois formes de daltonisme les plus fréquentes, et
 * elle ne recouvre aucune des teintes déjà attribuées : ni le jaune signal, ni
 * le vert/rouge de vote, ni le bleu/bronze des institutions.
 *
 * LE GRIS N'EST PAS UNE COULEUR DE LA PALETTE. Il est réservé à « matière non
 * établie », qui n'est pas une matière de plus mais une absence de donnée
 * (§2 règle 5) — la distinguer par la teinte la rangerait parmi les autres.
 */
import { MATIERE_NON_ETABLIE } from './profilCandidat.js';

export const PALETTE_MATIERE = [
  '#332288', '#88ccee', '#44aa99', '#999933', '#cc6677',
  '#aa4499', '#882255', '#6699cc', '#661100', '#117733',
  '#ddcc77', '#4477aa', '#ee8866', '#77aadd',
];

export const GRIS_SANS_MATIERE = '#c4c0b9';

export function teinteMatiere(matiere, rang) {
  if (matiere === MATIERE_NON_ETABLIE) return GRIS_SANS_MATIERE;
  return PALETTE_MATIERE[rang % PALETTE_MATIERE.length];
}

/* LA TEINTE D'UN THÈME EUROPÉEN SUIT LE THÈME, PAS SON RANG (#901).
 *
 * Les thèmes européens forment un référentiel fermé : 21 domaines EuroVoc
 * (niveau 1 du thésaurus) et 8 familles OEIL, dans l'ordre des codes publiés
 * par la source. La teinte se lit dans cet ordre, donc un thème garde la même
 * couleur d'une figure à l'autre et d'une fiche à l'autre — ce que le rang ne
 * permet pas. La palette compte 14 teintes pour 29 thèmes : deux thèmes en
 * partagent donc une, ce qui était déjà le cas avec le rang.
 */
export const ORDRE_THEMES_UE = [
  'Vie politique', 'Relations internationales', 'Union européenne', 'Droit', 'Économie',
  'Échanges économiques et commerciaux', 'Finances', 'Questions sociales',
  'Éducation et communication', 'Sciences', 'Entreprise et concurrence', 'Emploi et travail',
  'Transports', 'Environnement', 'Agriculture, sylviculture et pêche', 'Agro-alimentaire',
  'Production, technologie et recherche', 'Énergie', 'Industrie', 'Géographie',
  'Organisations internationales',
  'European citizenship', 'Internal market, single market', 'Community policies',
  'Economic, social and territorial cohesion', 'Economic and monetary system',
  'External relations of the Union', 'Area of freedom, security and justice',
  'State and evolution of the Union',
];

export function teinteThemeUe(theme, rangDeSecours = 0) {
  if (theme === MATIERE_NON_ETABLIE) return GRIS_SANS_MATIERE;
  const i = ORDRE_THEMES_UE.indexOf(theme);
  return PALETTE_MATIERE[(i >= 0 ? i : rangDeSecours) % PALETTE_MATIERE.length];
}
