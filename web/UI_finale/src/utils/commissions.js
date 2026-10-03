/*
 * UNE COULEUR FIXE PAR COMMISSION PERMANENTE (arrêté le 01/10/2026).
 *
 * La teinte d'une matière suivait son RANG (`teinteMatiere`) : la commission la
 * plus fréquente prenait la première teinte. Or les deux cartes de la section
 * ne classent pas pareil — l'une compte des textes portés, l'autre des
 * amendements — et la même commission y changeait donc de couleur. Mesuré le
 * 01/10/2026 sur la fiche de François Ruffin : « Affaires sociales » indigo
 * sur les textes portés, bleu clair sur les amendements ; « Lois » bleu clair
 * en haut, olive en bas. Une couleur qui change de sens d'une carte à l'autre
 * ne s'apprend pas, et d'une fiche à l'autre encore moins.
 *
 * Les commissions permanentes de l'Assemblée sont HUIT, et c'est un référentiel
 * fermé : chacune reçoit sa teinte, la même dans les deux cartes de « Ce qu'il
 * a proposé » et sur toutes les fiches candidat. La clé est le `sigle` de
 * `pivot_data/commissions_dossiers.json`, celui que `commissionDuDossier` rend.
 *
 * LES DEUX GRIS NE SONT PAS DES TEINTES DE PLUS. Une commission spéciale est
 * créée pour un texte et disparaît avec lui : lui donner une couleur ouvrirait
 * une palette sans fin, et elles partagent donc UN gris — leur nom, lui, reste
 * entier sur la ligne et au survol. « Matière non établie » prend un gris plus
 * clair : ce n'est pas une matière mais une absence de donnée (§2 règle 5).
 *
 * LES TEINTES SE CALCULENT, ELLES NE S'ESTIMENT PAS (`DESIGN_SYSTEM.md` §2).
 * Parties de la palette « muted » de Paul Tol qu'employait `utils/matiere.js`,
 * elles ont été corrigées, chacune dans sa famille, jusqu'à passer
 * `validate_palette.js` sur fond blanc et TOUTES PAIRES — un carré a n'importe
 * quelle autre commission pour voisin. La mesure et le verdict sont dans
 * `docs/decisions/carres-des-textes-et-couleurs-des-commissions.md`.
 *
 * LA COULEUR NE PORTE JAMAIS SEULE L'IDENTITÉ : la légende nomme chaque teinte,
 * la ligne d'amendements écrit sa commission, le carré la dit au survol et dans
 * la liste. Et aucun texte ne prend la couleur d'une commission — encre et
 * gris seulement.
 *
 * La fiche de lignée et la fiche de gouvernement gardent `teinteMatiere` : ce
 * lot ne les couvre pas.
 */
import { MATIERE_NON_ETABLIE } from './profilCandidat.js';

export const TEINTE_COMMISSION_PERMANENTE = {
  'Affaires culturelles et éducation': '#f16675',
  'Affaires économiques': '#882255',
  'Affaires étrangères': '#463fa0',
  'Affaires sociales': '#259ce6',
  'Défense': '#137731',
  'Développement durable': '#ab47aa',
  'Finances': '#09a68b',
  'Lois': '#9d9201',
};

/* Le nom sous lequel la légende réunit les commissions spéciales. */
export const COMMISSIONS_SPECIALES = 'Commissions spéciales';

export const GRIS_COMMISSIONS_SPECIALES = '#6e6a72';
export const GRIS_MATIERE_NON_ETABLIE = '#b5b3af';

/* La FAMILLE d'une matière : elle-même si c'est une commission permanente,
 * « Commissions spéciales » sinon, et l'absence reste l'absence.
 *
 * « Sinon » est le référentiel tel que la source le publie : hors des huit
 * permanentes, `commissions_dossiers.json` ne porte que des commissions
 * spéciales (27 sigles au 28/09/2026, tous de la forme « Commission spéciale … »
 * ou « CS … »). Le jour où un autre organe est saisi au fond, il prendra ce
 * gris — sans teinte, donc sans se faire passer pour une des huit. */
export function familleDeCommission(matiere) {
  if (!matiere || matiere === MATIERE_NON_ETABLIE) return MATIERE_NON_ETABLIE;
  return Object.hasOwn(TEINTE_COMMISSION_PERMANENTE, matiere) ? matiere : COMMISSIONS_SPECIALES;
}

export function teinteDeLaFamille(famille) {
  if (famille === MATIERE_NON_ETABLIE) return GRIS_MATIERE_NON_ETABLIE;
  return TEINTE_COMMISSION_PERMANENTE[famille] || GRIS_COMMISSIONS_SPECIALES;
}

export function teinteCommission(matiere) {
  return teinteDeLaFamille(familleDeCommission(matiere));
}

/* L'ordre de la légende : alphabétique, puis les deux gris. Aucun volume n'y
 * entre — un ordre par volume changerait d'une fiche à l'autre, et c'est
 * précisément ce que la couleur fixe retire. */
export const ORDRE_DES_FAMILLES = [
  ...Object.keys(TEINTE_COMMISSION_PERMANENTE).sort((a, b) => a.localeCompare(b, 'fr')),
  COMMISSIONS_SPECIALES,
  MATIERE_NON_ETABLIE,
];
