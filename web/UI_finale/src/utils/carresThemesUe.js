/*
 * LES TEXTES PORTÉS EUROPÉENS, UNE LIGNE PAR THÈME — le rangement, et rien
 * d'autre.
 *
 * Arbitré le 02/10/2026 sur maquette (forme D), pour la fiche candidat : la
 * cascade en rubans répondait « quelle part de quels thèmes va à quelle
 * issue », et il fallait cliquer pour apprendre « quels textes ». Ici un carré
 * EST un texte, posé dans la case (thème × étape) qui le concerne.
 *
 * UN TEXTE EST RÉPÉTÉ SUR CHACUN DE SES THÈMES, ET C'EST VOULU. Un texte porté
 * européen touche plusieurs domaines EuroVoc (`themesEuropeens`) ; lui en
 * choisir un écrasait les autres, ce que la propriétaire a refusé le
 * 17/09/2026. Le ruban le partageait au prorata — des « parts de texte » que
 * personne ne lit. La grille le dessine entier, une fois par ligne, et c'est
 * le survol qui dit la répétition : toutes les occurrences d'un texte
 * s'entourent ensemble (`CarresThemesUe.jsx`).
 *
 * DONC DEUX COMPTES, À NE JAMAIS CONFONDRE. `carres` est le nombre de carrés
 * dessinés ; `textes` le nombre de textes. L'en-tête d'une colonne compte des
 * TEXTES ENTIERS — additionner les carrés d'une colonne compterait trois fois
 * le texte à trois thèmes.
 *
 * AUCUN COMPTE PAR THÈME NE SORT D'ICI (arbitrage du 17/09/2026, voir
 * `themesEuropeens`) : le nombre de textes d'un thème sert à CLASSER les
 * lignes, et il n'est pas rendu — une ligne n'a rien à afficher que son nom.
 *
 * UNE COLONNE N'EST PAS UN ÉCHELON. Les stades européens ne s'ordonnent pas
 * (#901) : l'ordre des colonnes est celui du schéma, pour que deux fiches ne
 * les rangent pas différemment, et rien d'autre. Seules les étapes PRÉSENTES
 * ont une colonne — une colonne vide par stade de la nomenclature en ferait
 * seize, dont treize à zéro.
 */
import { MATIERE_NON_ETABLIE } from './profilCandidat.js';
import { teinteThemeUe } from './matiere.js';

/* Ce qu'on lit d'un texte, en une ligne : thèmes · étape · année. Tous ses
 * thèmes, dans l'ordre où la source les donne : c'est ici que le lecteur
 * apprend pourquoi le même carré est sur trois lignes. Aucun sort : la source
 * européenne n'en publie pas à côté du stade. */
export function faitDuTexteUe(texte) {
  return [
    (texte.themes || []).join(', '),
    texte.stade,
    texte.an,
  ].filter(Boolean).join(' · ');
}

export function rangerParTheme(cascade) {
  const stades = cascade?.stades || [];
  const basses = new Set(cascade?.basses || []);
  const textes = cascade?.textes || [];

  /* LES STADES PUBLIÉS D'ABORD, LES MOTIFS D'ABSENCE ENSUITE. `cascade.stades`
   * les range dans l'autre sens (les branches basses au rang 0, pour la
   * cascade) : la colonne garde donc son RANG d'origine en `lo`/`hi`, et la
   * sélection d'une étape reste l'intervalle que `textesDeLaSelection` lit. */
  const colonnes = [
    ...stades.filter((st) => !basses.has(st)),
    ...stades.filter((st) => basses.has(st)),
  ].map((cle) => {
    const n = textes.filter((t) => t.stadeCle === cle).length;
    return {
      cle,
      n,
      libelle: cascade.libelles?.[cle] || cle,
      lo: stades.indexOf(cle),
      hi: stades.indexOf(cle),
      /* La largeur suit la RACINE du nombre de textes : une colonne de 250
       * textes à côté d'une colonne d'un seul prendrait sinon toute la figure,
       * et l'en-tête de la seconde ne tiendrait plus. */
      largeur: Math.max(1, Math.sqrt(n)),
    };
  }).filter((col) => col.n > 0);

  /* LES LIGNES, PAR NOMBRE DE TEXTES QUI TOUCHENT LE THÈME. À égalité, l'ordre
   * de `cascade.matieres` — le poids au prorata — départage, pour que deux
   * chargements de la même fiche rendent la même figure. « Matière non
   * établie » en dernier : ce n'est pas un thème de plus, c'est une absence
   * (§2 règle 5). */
  const touche = new Map();
  for (const t of textes) {
    for (const theme of t.themes || []) touche.set(theme, (touche.get(theme) || 0) + 1);
  }
  const rangConnu = new Map((cascade?.matieres || []).map((m, i) => [m, i]));
  const rang = (theme) => (rangConnu.has(theme) ? rangConnu.get(theme) : rangConnu.size);
  const themes = [...touche.keys()].sort(
    (a, b) => (a === MATIERE_NON_ETABLIE) - (b === MATIERE_NON_ETABLIE)
      || touche.get(b) - touche.get(a)
      || rang(a) - rang(b)
      || a.localeCompare(b, 'fr'),
  );

  let carres = 0;
  const lignes = themes.map((theme) => {
    const teinte = teinteThemeUe(theme);
    return {
      theme,
      teinte,
      /* Une case par colonne, dans le même ordre : la grille se dessine sans
       * rien recalculer. `index` est le rang du texte dans `cascade.textes` —
       * c'est lui qui relie les occurrences d'un même texte entre les lignes,
       * et lui que la sélection d'un carré porte. */
      cases: colonnes.map((col) => {
        const dedans = [];
        textes.forEach((texte, index) => {
          if (texte.stadeCle === col.cle && (texte.themes || []).includes(theme)) {
            dedans.push({ index, texte, theme, teinte });
          }
        });
        carres += dedans.length;
        return dedans;
      }),
    };
  });

  return { colonnes, lignes, carres, textes: textes.length };
}

/* ── LA SÉLECTION ────────────────────────────────────────────────────────────
 *
 * Les trois gestes des carrés français (`carresTextes.js`), sur le même état :
 *
 *   un carré  { texte: index }               ce texte, où qu'il soit dessiné
 *   une étape { matiere: null, lo, hi }      `selectionDeLEtape`, inchangée
 *   un thème  { matiere: thème, lo: 0, hi }  tous les textes qui le TOUCHENT
 *
 * `matiere`, et non `famille` : `textesDeLaSelection` lit `t.themes` quand la
 * sélection porte une matière, et rend donc un texte sous chacun de ses thèmes
 * (#901) — la règle existait pour le ruban, elle sert telle quelle.
 */
export function selectionDuTheme(cascade, theme) {
  return {
    matiere: theme,
    lo: 0,
    hi: Math.max(0, (cascade?.stades || []).length - 1),
    intitule: theme,
  };
}

/* Ce que la sélection laisse allumé.
 *
 * UN TEXTE CHOISI ALLUME TOUTES SES OCCURRENCES — c'est le même texte, et
 * n'en éclairer qu'une dirait qu'il y en a plusieurs. UN THÈME CHOISI N'ALLUME
 * QUE SA LIGNE : les textes qu'il ouvre sont aussi sur d'autres lignes, mais
 * les y éclairer ferait lire ces autres thèmes comme choisis. */
export function carreThemeEclaire(selection, carre, cascade) {
  if (!selection || selection.procedure493) return true;
  if (selection.texte != null) return selection.texte === carre.index;
  if (selection.matiere && selection.matiere !== carre.theme) return false;
  const rang = (cascade?.stades || []).indexOf(carre.texte.stadeCle);
  return rang >= selection.lo && rang <= selection.hi;
}
