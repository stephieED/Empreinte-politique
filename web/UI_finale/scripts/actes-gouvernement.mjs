/*
 * CE QUE L'EXÉCUTIF A FAIT ENTRER EN VIGUEUR, PAR GOUVERNEMENT (#1029 voie 1).
 *
 * `pivot_data/actes_reglementaires/` porte 389 000 décrets, arrêtés et
 * ordonnances depuis 2007. La fiche de gouvernement n'en lisait aucun : ce
 * module en tire, pour la fenêtre de chaque gouvernement, la projection que
 * l'interface charge.
 *
 * TROIS RÈGLES, ET AUCUNE N'EST COSMÉTIQUE.
 *
 * 1. LES ACTES DE PERSONNE SORTENT, ET C'EST LE JOURNAL OFFICIEL QUI LE DIT.
 *    Le sommaire de chaque livraison range ses textes — « Mesures nominatives »
 *    contre « Textes généraux » —, et `rubrique_des_actes` (#1134) porte ce
 *    rangement, aligné sur `ids`. La rubrique décide ; le titre ne sert plus
 *    que de REPLI, là où le sommaire ne dit rien.
 *
 *    Pourquoi ce n'était pas suffisant par le titre : 308 arrêtés « fixant la
 *    liste des personnes autorisées à exercer la profession de médecin »
 *    nomment des gens un par un sans qu'aucune formule du filtre ne les
 *    attrape, et trois filtres par titre donnaient trois comptes — 308, 321,
 *    366. La rubrique n'est pas une devinette : sur la fenêtre de Lecornu II,
 *    elle classe en mesures nominatives la TOTALITÉ de ces arrêtés.
 *
 *    La couverture n'est pas uniforme et ne se lit pas comme une absence : de
 *    98 % en 2025 à 58 % en 2007 (mesuré le 25/09/2026 sur les 389 506 actes).
 *    Une rubrique absente n'est pas « acte général » (§2 règle 5) — c'est le
 *    repli par le titre qui tranche, et la fiche dit combien d'actes en
 *    dépendent.
 *
 * 2. LE LIEN À UNE LOI SE LIT DANS LE TITRE, PAS DANS `liens_lois`. La
 *    qualification structurée de Légifrance n'est plus posée : sur la même
 *    période, UN acte la porte. Mais 576 écrivent « portant application » dans
 *    leur titre et 395 y nomment la loi par son numéro. Le titre est donc la
 *    seule source utilisable — et il dit ce qu'il dit :
 *    « le titre ne le dit pas » N'EST PAS « sans loi ». L'absence de mention ne
 *    dit rien de l'acte (§2 règle 5), et aucune formule publiée ne doit le
 *    laisser croire.
 *    → `docs/decisions/part-d-application-non-publiable-1029.md`
 *
 * 3. UN ACTE A UN SEUL VERBE, dans l'ordre de `VERBES` : « modifiant l'arrêté
 *    portant création » est une modification. C'est une aide à la lecture, pas
 *    une catégorie officielle, et la fiche le dit.
 */

/** Le rangement du sommaire du JO qui sort un acte du compte. */
export const RUBRIQUE_PERSONNE = 'Mesures nominatives';

/**
 * Un acte concerne-t-il une personne ? La rubrique du Journal officiel tranche
 * quand elle existe ; sinon, et seulement sinon, le titre. `parLeTitre` dit
 * laquelle des deux a répondu, pour que la fiche puisse le publier.
 */
export function acteDePersonne(titre, rubrique) {
  if (rubrique) return { personne: rubrique.includes(RUBRIQUE_PERSONNE), parLeTitre: false };
  return { personne: PERSONNE.test(titre || ''), parLeTitre: true };
}

/** Ce qui concerne une personne et non le droit — le REPLI, quand le sommaire se tait. */
export const PERSONNE = /portant (nomination|cessation|mutation|délégation de signature|admission|promotion|radiation|désignation|inscription|maintien|renouvellement|titularisation|détachement|réintégration|affectation|avancement|reconduction|attribution de la médaille|élévation|nominations|naturalisation)|naturalisation, réintégration|perte de la nationalité|francisation de nom|composition du cabinet/i;

/** L'ordre compte : le premier qui accroche gagne. */
export const VERBES = [
  // ABROGER ET MODIFIER PASSENT AVANT CRÉER, et l'ordre est le fait : « modifiant
  // le décret portant création du machin » modifie, il ne crée pas. L'inverse
  // gonflait les créations de tout ce qui touche à un texte fondateur.
  ['abroger', /\babrogeant\b|portant abrogation|portant retrait|portant suppression/i],
  ['modifier', /\bmodifiant\b|portant modification|de modification/i],
  ['créer', /portant création|\binstituant\b|\bcréant\b|portant institution|portant ouverture/i],
  ['étendre ou approuver', /portant extension|\bhomologuant\b|portant approbation|\bapprouvant\b|portant publication/i],
  ['autoriser', /\bautorisant\b|portant autorisation|portant agrément|\bagréant\b/i],
  ['encadrer', /\bfixant\b|portant fixation|\brelatif(?:ve)?s? (?:à|au|aux)\b|portant règlement|portant organisation|\bdéfinissant\b/i],
];

export const LOI_NOMMEE = /loi (?:organique )?n°\s*(\d{4}-\d+)/i;
export const DIT_APPLIQUER = /portant application|pris pour l'application|pris en application|en application de|application de l'article/i;

export const NOMME = 'nomme la loi';
export const APPLIQUE = "dit appliquer une loi";
export const MUET = 'le titre ne le dit pas';

export function verbeDe(titre) {
  for (const [nom, motif] of VERBES) if (motif.test(titre)) return nom;
  return 'autre';
}

export function lienDe(titre) {
  if (LOI_NOMMEE.test(titre)) return NOMME;
  if (DIT_APPLIQUER.test(titre)) return APPLIQUE;
  return MUET;
}

/** « Ministère de la transition écologique, … » → « Transition écologique ». */
export function ministereCourt(libelle) {
  return (libelle || 'Ministère non précisé')
    .replace(/^Ministère (?:de la |de l'|des |du |de )/, '')
    .split(',')[0].trim()
    .replace(/^./, (c) => c.toUpperCase());
}

const CAP_EXEMPLES = 8;
const CAP_ACTES_LOI = 6;

/**
 * Un accumulateur par gouvernement. `periodes` : [{id, debut, fin}] — une fin
 * absente vaut « encore en fonction ».
 */
export function accumulateurs(periodes) {
  return periodes.map((p) => ({
    id: p.id,
    debut: p.debut,
    fin: p.fin,
    tot: 0,
    personnes: 0,
    personnesParTitre: 0,
    sansRubrique: 0,
    cellules: new Map(),
    exemples: new Map(),
    ministeres: new Map(),
    lois: new Map(),
  }));
}

/** Range un acte dans chaque gouvernement dont la fenêtre le couvre. */
export function ranger(acc, acte) {
  const { date, titre, ministere, id, rubrique } = acte;
  if (!date) return;
  const { personne, parLeTitre } = acteDePersonne(titre, rubrique);
  for (const a of acc) {
    if (a.debut && date < a.debut) continue;
    if (a.fin && date > a.fin) continue;
    a.tot += 1;
    if (parLeTitre) a.sansRubrique += 1;
    if (personne) {
      a.personnes += 1;
      if (parLeTitre) a.personnesParTitre += 1;
      continue;
    }
    const m = ministereCourt(ministere);
    const v = verbeDe(titre);
    const l = lienDe(titre);
    const cle = `${m}|${l}|${v}`;
    a.cellules.set(cle, (a.cellules.get(cle) || 0) + 1);
    a.ministeres.set(m, (a.ministeres.get(m) || 0) + 1);
    const ex = a.exemples.get(cle) || [];
    if (ex.length < CAP_EXEMPLES) { ex.push({ d: date, t: titre.slice(0, 190), i: id, m }); a.exemples.set(cle, ex); }
    const loi = titre.match(LOI_NOMMEE);
    if (loi) {
      const num = loi[1];
      const suite = a.lois.get(num) || { num, n: 0, actes: [] };
      suite.n += 1;
      if (suite.actes.length < CAP_ACTES_LOI) suite.actes.push({ d: date, t: titre.slice(0, 190), i: id, m });
      a.lois.set(num, suite);
    }
  }
}

const JOUR = 86400000;

/** La projection publiée pour un gouvernement. `textes` : numéro de loi → texte promulgué. */
export function projection(a, textes = {}) {
  const lois = [...a.lois.values()].map((l) => {
    const t = textes[l.num];
    const e = { ...l, actes: l.actes.sort((x, y) => (x.d < y.d ? -1 : 1)) };
    if (t) {
      e.titre = t.titre || '';
      e.nature = t.nature_procedure || '';
      e.com = t.commission?.sigle || '';
      e.prom = t.date_promulgation || '';
      // Le délai est celui du PREMIER ACTE DE CETTE PÉRIODE, jamais « du premier
      // acte jamais pris » : une loi ancienne a pu en recevoir avant.
      if (e.prom && e.actes.length) {
        e.delai = Math.round((Date.parse(e.actes[0].d) - Date.parse(e.prom)) / JOUR);
      }
    }
    return e;
  }).sort((x, y) => y.n - x.n || (x.num < y.num ? -1 : 1));
  return {
    tot: a.tot,
    personnes: a.personnes,
    // Ce que le sommaire du JO n'a pas rangé, et que le titre a dû trancher :
    // deux absences ne se confondent jamais (§2 règle 5).
    personnesParTitre: a.personnesParTitre,
    sansRubrique: a.sansRubrique,
    total: a.tot - a.personnes,
    cellules: [...a.cellules.entries()].map(([cle, n]) => {
      const [m, l, v] = cle.split('|');
      return { m, l, v, n };
    }),
    exemples: Object.fromEntries(a.exemples),
    ministeres: Object.fromEntries([...a.ministeres.entries()].sort((x, y) => y[1] - x[1])),
    lois,
  };
}
