/*
 * LES TEXTES PORTÉS, UN CARRÉ PAR TEXTE — le rangement, et rien d'autre.
 *
 * Arrêté le 01/10/2026 pour la fiche candidat, versant français : la cascade
 * en rubans répondait « combien franchissent chaque porte », et le lecteur
 * cherche « quels textes, et jusqu'où ». Un carré est UN texte, rangé à
 * l'étape la plus avancée qu'il a atteinte, teinté par sa commission.
 *
 * Comme `cascadeTextes.js`, ce module ne rend rien : il range. Le composant
 * dessine, et le rangement se vérifie hors navigateur.
 *
 * CE QUE LA FIGURE NE DIT TOUJOURS PAS. Une colonne est une ÉTAPE ATTEINTE,
 * jamais un sort : le texte resté « discuté en séance » n'y est ni repoussé ni
 * abandonné — le corpus n'enregistre aucun acte au-delà (§2 règle 5). Le sort,
 * quand la source le publie, se lit au survol et dans la liste, à côté de
 * l'étape et jamais à sa place.
 *
 * LE VERSANT EUROPÉEN N'EST PAS ICI. Ses seize stades ne s'ordonnent pas
 * (#901) : quatre colonnes « dans l'ordre de la procédure » y publieraient un
 * avancement que la source n'établit pas. Il a sa propre grille depuis le
 * 02/10/2026 — une ligne par thème, une colonne par étape présente, sans
 * ordre entre elles (`carresThemesUe.js`).
 */
import { ORDRE_DES_FAMILLES, familleDeCommission, teinteDeLaFamille } from './commissions.js';
import { LIBELLE_SORT_TEXTE } from './lecture.js';

/* QUATRE COLONNES, TOUJOURS LES QUATRE. Une colonne à zéro reste affichée :
 * « 0 adopté » est un fait de la fiche, et une colonne absente ferait lire
 * « promulgué » comme l'étape qui suit « discuté en séance ».
 *
 * `inscrit_ordre_jour` se range avec « examiné en commission » : le texte a
 * passé la commission et n'a pas été discuté. Lui ouvrir une cinquième colonne
 * la laisserait vide sur presque toutes les fiches.
 *
 * Le libellé s'accorde au nombre — « 1 promulgué », « 3 discutés en séance » —
 * et zéro prend le singulier, comme partout ailleurs sur la fiche. */
export const ETAPES_DES_CARRES = [
  {
    cle: 'commission',
    stades: ['examine_commission', 'inscrit_ordre_jour'],
    un: 'examiné en commission',
    plusieurs: 'examinés en commission',
  },
  { cle: 'seance', stades: ['discute_seance'], un: 'discuté en séance', plusieurs: 'discutés en séance' },
  { cle: 'adopte', stades: ['adopte'], un: 'adopté', plusieurs: 'adoptés' },
  { cle: 'promulgue', stades: ['promulgue'], un: 'promulgué', plusieurs: 'promulgués' },
];

/* Ce qu'on lit d'un texte, en une ligne : commission · étape · sort · année.
 * La commission est celle du DOSSIER, en toutes lettres — c'est elle qui nomme
 * ce que la teinte ne fait que rappeler, et une commission spéciale y garde
 * son nom, que la légende regroupe. Un sort absent se dit absent : aucun sort
 * par défaut (§2 règle 5). */
export function faitDuTexte(texte) {
  return [
    texte.matiere,
    texte.stade,
    texte.sortCle ? LIBELLE_SORT_TEXTE[texte.sortCle] || texte.sortCle : 'Sort non résolu',
    texte.an,
  ].filter(Boolean).join(' · ');
}

export function rangerEnCarres(cascade) {
  const stades = cascade?.stades || [];
  const rangFamille = new Map(ORDRE_DES_FAMILLES.map((f, i) => [f, i]));
  const carres = (cascade?.textes || []).map((texte, index) => {
    const famille = familleDeCommission(texte.matiere);
    return { index, texte, famille, teinte: teinteDeLaFamille(famille) };
  });
  /* Dans une colonne, les carrés d'une même commission se touchent : l'ordre
   * est celui de la légende, puis l'année la plus récente d'abord. Ce n'est pas
   * un classement — c'est ce qui permet de compter une teinte d'un coup d'œil. */
  const ordre = (a, b) => rangFamille.get(a.famille) - rangFamille.get(b.famille)
    || String(b.texte.an || '').localeCompare(String(a.texte.an || ''))
    || a.texte.titre.localeCompare(b.texte.titre, 'fr');

  const colonnes = ETAPES_DES_CARRES.map((etape) => {
    const dedans = carres.filter((c) => etape.stades.includes(c.texte.stadeCle)).sort(ordre);
    /* La sélection d'une colonne reste un INTERVALLE de crans de la cascade —
     * le modèle de `textesDeLaSelection`. Les crans vifs d'une étape sont
     * contigus dans `cascade.stades`, qui suit l'ordre de `STADES_PUBLIES`. */
    const crans = etape.stades.map((s) => stades.indexOf(s)).filter((i) => i >= 0);
    return {
      cle: etape.cle,
      n: dedans.length,
      libelle: dedans.length > 1 ? etape.plusieurs : etape.un,
      lo: crans.length ? Math.min(...crans) : null,
      hi: crans.length ? Math.max(...crans) : null,
      carres: dedans,
    };
  });

  // Seules les familles PRÉSENTES : une légende de dix entrées pour trois
  // teintes dessinées ferait chercher sept couleurs qui ne sont pas là.
  const legende = ORDRE_DES_FAMILLES
    .filter((f) => carres.some((c) => c.famille === f))
    .map((f) => ({
      famille: f,
      teinte: teinteDeLaFamille(f),
      n: carres.filter((c) => c.famille === f).length,
    }));

  return { colonnes, legende, total: carres.length };
}

/* ── LA SÉLECTION ────────────────────────────────────────────────────────────
 *
 * Trois gestes, un seul état — celui de la cascade, étendu de deux clés :
 *
 *   un carré       { texte: index }            ce texte seul
 *   une étape      { matiere: null, lo, hi }   l'intervalle de crans, inchangé
 *   une commission { famille, lo: 0, hi: fin } tous ses textes, toutes étapes
 *
 * `famille`, et non `matiere` : la légende regroupe les commissions spéciales,
 * qui sont autant de matières distinctes. Le 49.3 garde sa sélection à lui
 * (`{ procedure493: true }`), qui filtre la liste et laisse la figure intacte.
 *
 * `intitule` voyage avec la sélection : la liste nomme ce qu'on a cliqué avec
 * les mots de la figure, sans réapprendre son vocabulaire.
 */
export function selectionDuCarre(carre) {
  return { texte: carre.index, intitule: '' };
}

export function selectionDeLEtape(colonne) {
  return { matiere: null, lo: colonne.lo, hi: colonne.hi, intitule: colonne.libelle };
}

export function selectionDeLaFamille(cascade, famille) {
  return {
    famille,
    lo: 0,
    hi: Math.max(0, (cascade?.stades || []).length - 1),
    intitule: famille,
  };
}

export function memeSelection(a, b) {
  if (!a || !b) return false;
  return (a.texte ?? null) === (b.texte ?? null)
    && (a.famille ?? null) === (b.famille ?? null)
    && (a.matiere ?? null) === (b.matiere ?? null)
    && (a.lo ?? null) === (b.lo ?? null)
    && (a.hi ?? null) === (b.hi ?? null)
    && Boolean(a.procedure493) === Boolean(b.procedure493);
}

/* Ce que la sélection laisse allumé. Sans sélection, tout ; sous un 49.3, tout
 * aussi — c'est le comportement de la cascade, gardé tel quel : la pastille
 * filtre la liste, où chaque texte répond de lui-même. */
export function carreEclaire(selection, carre, cascade) {
  if (!selection || selection.procedure493) return true;
  if (selection.texte != null) return selection.texte === carre.index;
  if (selection.famille && selection.famille !== carre.famille) return false;
  if (selection.matiere && selection.matiere !== carre.texte.matiere) return false;
  const rang = (cascade?.stades || []).indexOf(carre.texte.stadeCle);
  return rang >= selection.lo && rang <= selection.hi;
}
