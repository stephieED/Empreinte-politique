/* ── Ce qu'il a voté au Parlement européen (#901) ─────────────────────────────
 *
 * Les 11 013 positions de vote européennes des six candidats déclarés à mandat
 * européen étaient collectées et n'atteignaient pas l'écran : `scrutin_id` est
 * `null` sur TOUTES — l'index de l'Assemblée ne les résout pas, et c'est voulu
 * (`index-scrutins-europeens-901`). La fiche affichait donc « aucune n'est
 * rattachée à un scrutin identifié », ce qui décrivait notre index, pas la
 * source.
 *
 * LA JOINTURE EST AILLEURS : `scrutin_non_resolu` porte le NUMÉRO du scrutin et
 * sa DATE, et `pivot_data/scrutins_europeens.json` les publie tous les deux.
 * Les 11 013 positions retrouvent ainsi leur scrutin, sans exception (mesuré le
 * 17/09/2026).
 *
 * TROIS RÈGLES, ET AUCUNE N'EST DÉDUITE D'UN INTITULÉ (§2 règle 2) :
 *
 *   - UN TEXTE, UNE POSITION. Un texte est un DOSSIER (`reference_dossier`), à
 *     défaut le document voté, à défaut le scrutin lui-même ; la position
 *     retenue est celle du DERNIER scrutin — date la plus tardive, puis rang
 *     dans la séance. C'est le pendant européen de la dernière lecture retenue
 *     côté français (#711), qui ne s'applique pas ici : la nomenclature
 *     européenne ne publie pas de lecture.
 *   - LE THÈME vient du dossier, par la même cascade que le sankey des textes
 *     portés : ses domaines EuroVoc s'il en porte, sinon ses familles OEIL. Un
 *     texte compte sous CHACUN de ses thèmes — la figure est un diagramme en
 *     barres, ses lignes ne prétendent pas s'additionner (arbitré le
 *     17/09/2026) ; les effectifs des puces et des positions, eux, comptent des
 *     textes distincts.
 *   - AUCUN DÉCOUPAGE PAR PÉRIODE. Côté français, les votes se lisent par banc
 *     et par gouvernement en place : à Strasbourg il n'y a ni l'un ni l'autre,
 *     et la propriétaire a jugé ce filtre « hors propos » le 17/09/2026. La
 *     figure couvre tous les mandats européens, et nomme les groupes traversés.
 */
import { NATURES_UE, TYPE_GROUPE_EUROPEEN, libelleDomaine } from './profilCandidat.js';

const INSTITUTION = 'parlement_europeen';

/** Le code de procédure d'une référence de dossier : `2021/0136(COD)` → `COD`. */
export function codeProcedure(reference) {
  const m = /\(([A-Z]{3})\)\s*$/.exec(reference || '');
  return m ? m[1] : null;
}

/** La nature d'un texte voté, dans le vocabulaire des textes portés (#901).
 *  Une procédure hors des quatre natures — un accord, une décharge — n'en
 *  reçoit aucune : elle reste comptée dans « toutes natures », jamais rangée
 *  sous une nature qui ne serait pas la sienne. */
export function cleNatureDuVote(reference) {
  if (!reference) return 'sans_dossier';
  const code = codeProcedure(reference);
  return NATURES_UE.find((n) => n.procedures.includes(code))?.cle ?? null;
}

/* 716 des 5 571 scrutins portent un numéro mal formé — « 2017-06-01
 * 00:00:00-13. » au lieu de 13 (signalé à la collecte le 17/09/2026). Il reste
 * unique, donc la jointure tient ; seul l'ordre dans la séance se lit sur le
 * nombre final. */
export function rangDansLaSeance(numero) {
  if (typeof numero === 'number') return numero;
  const m = /(\d+)\.?\s*$/.exec(String(numero ?? ''));
  return m ? Number(m[1]) : -1;
}

/** Les positions européennes, une par texte : le dernier scrutin de chaque
 *  dossier. Rend aussi les deux dénominateurs — positions collectées, positions
 *  jointes — pour que la couverture se publie au lieu de se soustraire. */
export function votesEuropeensRetenus(votes, scrutinsParNumero) {
  const parTexte = new Map();
  let total = 0;
  let joints = 0;
  for (const v of votes || []) {
    const n = v.scrutin_non_resolu;
    if (n?.institution !== INSTITUTION) continue;
    total += 1;
    const scrutin = scrutinsParNumero?.[n.numero_scrutin];
    // La DATE fait partie de la clé : un numéro seul ne garantit pas le scrutin.
    if (!scrutin || scrutin.date !== n.date) continue;
    joints += 1;
    const cle = n.reference_dossier || scrutin.document || scrutin.id;
    const courant = parTexte.get(cle);
    const plusTard = !courant
      || scrutin.date > courant.scrutin.date
      || (scrutin.date === courant.scrutin.date
        && rangDansLaSeance(scrutin.numero_scrutin) > rangDansLaSeance(courant.scrutin.numero_scrutin));
    if (plusTard) {
      parTexte.set(cle, { position: v.position, scrutin, reference: n.reference_dossier || null });
    }
  }
  return { total, joints, retenus: [...parTexte.values()] };
}

function siegesEuropeens(mandats) {
  return (mandats || [])
    .filter((m) => m.categorie === 'mandat_electif' && m.categorie_source === 'europarl' && m.debut)
    .map((m) => ({ debut: m.debut, fin: m.fin || '9999-12-31' }))
    .sort((a, b) => (a.debut < b.debut ? -1 : 1));
}

/** Le groupe politique européen à une date, lu dans les mandats — jamais
 *  reconstruit depuis l'intitulé d'un scrutin. */
function groupeALaDate(mandats, date) {
  const g = (mandats || []).find(
    (m) => m.type_organe_source === TYPE_GROUPE_EUROPEEN
      && m.sigle_organe
      && m.debut <= date
      && date <= (m.fin || '9999-12-31'),
  );
  return g?.sigle_organe ?? null;
}

/** Les thèmes d'un dossier : les domaines EuroVoc, sinon les familles OEIL.
 *  La couverture EuroVoc monte d'un run à l'autre (151 dossiers sur 4 642 au
 *  17/09/2026) : un dossier que la collecte n'a pas encore interrogé n'est pas
 *  un dossier sans thème, sa famille le range. */
export function themesDuDossier(dossier) {
  const domaines = (dossier?.domaines || []).map((d) => libelleDomaine(d.libelle));
  if (domaines.length) return domaines;
  return (dossier?.familles || []).map((f) => f.libelle);
}

/** La figure : une seule période, un rang par thème, et les textes eux-mêmes.
 *  La forme rendue est celle de « Ce qu'il a voté » côté français — même
 *  composant, mêmes couleurs de position. */
export function figureVotesEuropeens(retenus, mandats, dossierEuropeen = () => null, positions = 0) {
  const sieges = siegesEuropeens(mandats);
  const textes = retenus
    .map(({ position, scrutin, reference }) => {
      const date = scrutin.date;
      const dossier = reference ? dossierEuropeen(reference) : null;
      const themes = themesDuDossier(dossier);
      return {
        scrutinId: scrutin.id,
        position,
        date,
        titre: dossier?.titre || scrutin.texte,
        sourceUrl: scrutin.source_url ?? null,
        themes,
        matiere: themes[0] ?? null,
        // La fiche ne publie pas d'origine de texte au Parlement européen : il
        // n'y a pas de projet de loi du gouvernement à Strasbourg.
        origine: null,
        groupe: groupeALaDate(mandats, date),
        siege: sieges.find((m) => m.debut <= date && date <= m.fin) || null,
        dossierId: reference,
        natureCle: cleNatureDuVote(reference),
        statutTexte: null,
        procedure49_3: false,
        reference: reference || null,
      };
    })
    .sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0));

  // Un texte se range sous chacun de ses thèmes : la figure en barres duplique
  // la ligne, jamais le texte — la liste et les effectifs restent sur
  // `scrutinId`.
  const etales = textes.flatMap((t) => (t.themes.length
    ? t.themes.map((theme) => ({ ...t, matiere: theme }))
    : [{ ...t, matiere: null }]));

  const periodes = etales.length
    ? [{
      cle: 'ue',
      debut: textes[0].date,
      fin: textes[textes.length - 1].date,
      votes: etales,
      groupes: [...new Set(textes.map((t) => t.groupe).filter(Boolean))],
      libelle: 'Au Parlement européen',
      sansRepere: false,
    }]
    : [];

  return {
    periodes,
    textes: textes.length,
    // Ce que la figure ne sait pas, publié plutôt que laissé à la soustraction
    // (§2 règles 5 et 7).
    /* CE QUE LE REPLI RETIRE SE DIT. Sur Emmanuel Maurel, 3 598 positions
     * donnent 3 175 textes : les 423 autres portent sur un scrutin antérieur du
     * même texte. Laissé à la soustraction, l'écart se lirait comme une perte
     * (§2 règles 5 et 7). */
    reperes: {
      total: textes.length,
      positions,
      matiere: textes.filter((t) => t.themes.length).length,
    },
  };
}
