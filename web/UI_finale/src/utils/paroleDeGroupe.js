/*
 * LA PAROLE D'UN GROUPE, COMPTÉE — débat par débat, membre par membre.
 *
 * Arrêté sur maquette le 02/10/2026 (`docs/decisions/revue-ux-de-la-fiche-de-groupe.md`) :
 * « Sur quoi ils ont pris la parole » ne compte plus seulement les membres
 * intervenus dans un débat, mais leurs PRISES DE PAROLE — une barre par débat,
 * un segment par membre, large comme ce qu'il y a dit de fois.
 *
 * Comme `carresTextes.js`, ce module ne rend rien : il range. La projection de
 * build (`scripts/vue-lignee.mjs`) et le composant l'importent tous les deux.
 *
 * CE QUI N'EST PAS LA PAROLE DU GROUPE, et que la propriétaire en retire :
 *
 *   - LA PRÉSIDENCE DE SÉANCE. « La parole est à… » est la conduite de la
 *     séance, pas une intervention : 20 788 des 39 581 prises de parole comptées
 *     à Ensemble pour la République en XVIIe législature. Le compte rendu la
 *     marque par le libellé de l'orateur, publié sous `role_seance` (#1169).
 *   - LA PAROLE PRONONCÉE COMME MEMBRE DU GOUVERNEMENT. Un député nommé ministre
 *     reste membre de son groupe un mois ; il y parle alors pour le
 *     gouvernement. La règle est celle de la fiche candidat
 *     (`fonctionGouvernementale.js`).
 *
 * Elles sont RETIRÉES, pas mises à part derrière une pastille.
 *
 * TANT QUE LE CORPUS NE PORTE PAS `role_seance`, LA FIGURE NE SE DESSINE PAS.
 * Le champ arrive par un run de collecte ; d'ici là rien ne distingue la
 * présidence, et publier le volume ferait passer la conduite de la séance pour
 * la parole du groupe. `rolesPublies` dit si le corpus lu au build le porte :
 * la fiche garde sa figure d'avant tant qu'il est faux.
 */
import { estFonctionGouvernementale } from './fonctionGouvernementale.js';
import { TYPES_INTERVENTION } from './profilCandidat.js';

export const ROLE_PRESIDENCE = 'presidence';

/** Les natures de la fiche candidat, dans le même ordre et sous les mêmes mots. */
export const NATURES_DE_PAROLE = TYPES_INTERVENTION.map((t) => t.label);
const RANG_NATURE = new Map(TYPES_INTERVENTION.flatMap((t, k) => t.cles.map((cle) => [cle, k])));

/** Le rang de la nature d'une intervention, ou -1 quand la fiche ne la nomme pas. */
export function natureDeParole(typeDetail) {
  return RANG_NATURE.get(typeDetail) ?? -1;
}

/** Vrai si l'intervention porte le champ qui permet de reconnaître la présidence. */
export function porteUnRoleDeSeance(intervention) {
  return Boolean(intervention) && Object.hasOwn(intervention, 'role_seance');
}

/** Vrai si la prise de parole compte pour le groupe. */
export function estParoleDuGroupe(intervention) {
  if (intervention?.role_seance === ROLE_PRESIDENCE) return false;
  return !estFonctionGouvernementale(intervention?.fonction);
}

/**
 * Les prises de parole d'un groupe, comptées.
 *
 * `entrees` : `[{ sujet, orateur, nature }]`, une par prise de parole retenue.
 * Rend `{ debats: [intitulé], comptes: [[débat, orateur, nature, n]] }` — les
 * débats par ordre alphabétique, pour qu'un build redonne le même fichier.
 */
export function agregerParoles(entrees) {
  const debats = [...new Set((entrees || []).map((e) => e.sujet))].sort((a, b) => a.localeCompare(b, 'fr'));
  const rang = new Map(debats.map((d, k) => [d, k]));
  const comptes = new Map();
  for (const e of entrees || []) {
    const cle = `${rang.get(e.sujet)}|${e.orateur}|${e.nature}`;
    comptes.set(cle, (comptes.get(cle) || 0) + 1);
  }
  return {
    debats,
    comptes: [...comptes].map(([cle, n]) => [...cle.split('|').map(Number), n])
      .sort((a, b) => a[0] - b[0] || a[1] - b[1] || a[2] - b[2]),
  };
}

/**
 * Ce que la figure montre sous une sélection de natures (`null` ou vide : toutes).
 *
 * Les débats sont RANGÉS PAR NOMBRE DE PRISES DE PAROLE (arbitrage du
 * 02/10/2026), puis par nombre de membres, puis par intitulé ; les segments
 * d'une barre du plus grand au plus petit. `parNature` compte TOUT le groupe,
 * hors sélection : c'est le nombre écrit sur chaque pastille.
 */
export function debatsSousSelection(paroles, natures = null, limite = 10) {
  const retenues = natures && natures.size ? natures : null;
  const parNature = NATURES_DE_PAROLE.map(() => 0);
  const parDebat = new Map();
  for (const [d, orateur, nature, n] of paroles?.comptes || []) {
    if (nature >= 0) parNature[nature] += n;
    if (retenues && !retenues.has(nature)) continue;
    const membres = parDebat.get(d) || new Map();
    membres.set(orateur, (membres.get(orateur) || 0) + n);
    parDebat.set(d, membres);
  }
  const lignes = [...parDebat].map(([d, membres]) => ({
    label: paroles.debats[d],
    membres: membres.size,
    paroles: [...membres.values()].reduce((a, b) => a + b, 0),
    segments: [...membres].sort((a, b) => b[1] - a[1] || a[0] - b[0]),
  })).sort((a, b) => b.paroles - a.paroles || b.membres - a.membres || a.label.localeCompare(b.label, 'fr'));
  return {
    parNature,
    total: lignes.reduce((a, l) => a + l.paroles, 0),
    nDebats: lignes.length,
    lignes: limite ? lignes.slice(0, limite) : lignes,
  };
}
