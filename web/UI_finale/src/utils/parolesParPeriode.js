/* ── « Ce qu'il a dit », par période politique (#328) ─────────────────────────
 *
 * La section publiait trois compteurs et un paragraphe de méthode : combien
 * d'interventions, de quelle nature, et sous quel régime la source publie la
 * qualité de l'orateur. Elle disait COMMENT ON SAIT, et jamais CE QUI A ÉTÉ
 * DIT — alors que le corpus porte 16 188 verbatims du compte rendu intégral
 * pour 21 725 interventions collectées (10 des 27 candidats déclarés, commit
 * de données `fdb37a4c`).
 *
 * Ce module ne contient que du calcul. Il ne réécrit AUCUN repère qui vive
 * ailleurs : le banc et le gouvernement en place sont lus par
 * `bancALaDate`/`gouvernementALaDate` de `votesParPeriode.js` — les deux
 * sections découpent le temps de la même façon parce qu'elles appellent la
 * même fonction, pas parce qu'elles se ressemblent.
 *
 * ── LE SUJET NE SE LIT PAS AU MÊME NIVEAU SELON LE TYPE ────────────────────
 *
 * L'Assemblée écrit son ordre du jour en CHEMIN — « racine > étape > article »
 * — et la grammaire de ce chemin change avec le type d'intervention :
 *
 *   question au gouvernement  « Questions au Gouvernement > Réforme des retraites »
 *   examen d'un texte         « Projet de loi de finances pour 2023 > Première partie > Après l'article 3 »
 *
 * Sur la première, le sujet est la FEUILLE et la racine n'est que le créneau de
 * séance ; sur la seconde, le sujet est la RACINE et la feuille est une étape
 * de procédure. Prendre partout le même bout donne, d'un côté, UNE seule valeur
 * pour 3 660 questions ; de l'autre, « Suspension et reprise de la séance »
 * (921), « Discussion générale » (756), « Après l'article 2 (suite) » (293).
 *
 * Mesuré sur les interventions des candidats déclarés, commit `fdb37a4c` :
 *
 *   type                    intitulés   racines   feuilles
 *   question au gouvernement    3 660        74        756
 *   débat en séance             8 321       384        410
 *   examen d'un texte           4 453       105        328
 *   motion de censure             401         2          6
 *
 * Choisir le niveau par type, c'est LIRE la structure que la source pose. Ce
 * n'est pas rapprocher deux libellés voisins, qui reste proscrit
 * (`docs/decisions/regrouper-nest-pas-joindre-639.md`) : deux racines
 * différentes ne se rejoignent jamais, et « Motion de censure » et « Motions de
 * censure » restent deux entrées.
 *
 * ── CE QUE CE MODULE REFUSE DE CALCULER ────────────────────────────────────
 *
 * - `format` (« réaction courte » / « prise de parole développée »), pourtant
 *   présent et non nul sur 16 242 lignes : c'est NOTRE déduction, un seuil de 50 mots posé
 *   dans `src/parse_syceron.py`, jamais un fait du compte rendu. Le publier
 *   ferait passer un choix d'implémentation pour une donnée.
 * - une densité par jour de séance : un creux s'y lirait comme une absence
 *   individuelle, que la source ne publie pas et nous jamais (§2 règle 3).
 * - un total de carrière : comme pour les votes, une intervention depuis le
 *   banc du gouvernement et une intervention depuis les bancs ne se comptent
 *   pas dans la même unité.
 */
import { bancALaDate, gouvernementALaDate } from './votesParPeriode';

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

/* Deux formats de date coexistent dans le corpus : l'ISO du compte rendu et le
 * `JJ/MM/AAAA` des questions écrites. Une date qui n'entre dans aucun des deux
 * ne devient pas une date approchée — l'intervention sort du découpage et le
 * dit dans la couverture (§2 règle 5). */
const DATE_ISO = /^\d{4}-\d{2}-\d{2}$/;
const DATE_JJMMAAAA = /^(\d{2})\/(\d{2})\/(\d{4})$/;

export function dateISO(brute) {
  if (typeof brute !== 'string') return null;
  if (DATE_ISO.test(brute)) return brute;
  const m = DATE_JJMMAAAA.exec(brute);
  return m ? `${m[3]}-${m[2]}-${m[1]}` : null;
}

/* ── La qualification d'une intervention ────────────────────────────────────
 *
 * Six faits, chacun de sa source, aucun deviné. Une clé qu'on ne peut pas
 * résoudre reste `null` et le dit à l'affichage.
 */
export function qualifierInterventions(interventions, { roles = [], gouvernements = [] } = {}) {
  return (interventions || []).map((i) => {
    const date = dateISO(i?.date);
    const banc = bancALaDate(roles, date);
    const gouvernement = gouvernementALaDate(gouvernements, date);
    return {
      id: i?.intervention_id ?? null,
      date,
      type: i?.type_detail ?? null,
      chemin: cheminDuPoint(i),
      sujet: sujetDeIntervention(i),
      // La qualité vient du compte rendu, qui ne la publie que pour une
      // fonction particulière — ministre, rapporteur. Son absence n'est pas
      // « il parlait comme député » : c'est un silence de la source.
      fonction: i?.fonction ?? null,
      verbatim: i?.texte ?? null,
      sourceUrl: i?.source_url ?? null,
      // Régime de collecte déclaré (#657) : la date, la nature et le thème, et
      // rien d'autre. Un verbatim absent n'y est pas un silence de la personne.
      themeSeul: i?.collecte === 'theme_seul',
      banc: banc?.position ?? null,
      groupe: banc?.groupe ?? null,
      gouvernementId: gouvernement?.id ?? null,
      gouvernement: gouvernement?.nom ?? null,
    };
  });
}

/* ── La qualité : à quel titre la personne a parlé (#328) ───────────────────
 *
 * Une carrière traverse des bancs, et on n'y parle pas du même endroit. La
 * section les mélangeait sous un seul titre, et les rangeait toutes par
 * GOUVERNEMENT FRANÇAIS — y compris les interventions européennes. Mesuré le
 * 13/09/2026 : les 128 interventions de Raphaël Glucksmann au Parlement
 * européen se répartissaient sur quatre gouvernements français, dont une seule
 * sous « gouvernement Attal ». Le cadre ne disait rien, et il le disait avec
 * assurance (§2 règle 2).
 *
 * Trois qualités, jamais devinées : la fonction publiée par le compte rendu
 * pour le gouvernement, le marqueur d'institution pour l'Europe, et le reste à
 * l'Assemblée. Mesuré sur les 17 fiches qui portent des interventions : 13
 * n'ont qu'une qualité, 4 en ont deux, aucune n'en a trois.
 */
export const QUALITE_AN = 'AN';
export const QUALITE_GOUVERNEMENT = 'GOUV';
export const QUALITE_PE = 'PE';

const FONCTION_GOUVERNEMENTALE = /ministre|secrétaire d'état|premier ministre/i;

export const LIBELLE_QUALITE = {
  [QUALITE_AN]: 'En qualité de député(e)',
  [QUALITE_GOUVERNEMENT]: 'En qualité de membre du gouvernement',
  [QUALITE_PE]: 'En qualité de député(e) européen(ne)',
};

/** L'ordre est celui de la frise — le banc français d'abord, l'Europe ensuite —
 *  pour que deux fiches se comparent. */
export const ORDRE_QUALITES = [QUALITE_AN, QUALITE_GOUVERNEMENT, QUALITE_PE];

export function qualiteDeParole(intervention) {
  const fonction = intervention?.fonction;
  if (fonction && FONCTION_GOUVERNEMENTALE.test(fonction)) return QUALITE_GOUVERNEMENT;
  if ((intervention?.source?.institution ?? null) === 'parlement_europeen') return QUALITE_PE;
  return QUALITE_AN;
}

/* ── Le découpage ───────────────────────────────────────────────────────────
 *
 * Une nouvelle période dès que le couple (banc, gouvernement) change — le même
 * critère que « Ce qu'il a voté », et pour la même raison : une intervention
 * n'a pas le même sens selon d'où elle est portée. Les interventions sont
 * triées par date d'abord ; le corpus ne garantit aucun ordre, et une période
 * se refermerait puis se rouvrirait sur le même couple.
 */
export function clePeriodeParole(intervention) {
  return `${intervention.banc ?? ''}|${intervention.gouvernementId ?? ''}`;
}

export function periodesDeParole(qualifiees) {
  const triees = [...(qualifiees || [])]
    .filter((i) => i.date)
    .sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0));

  const periodes = [];
  for (const i of triees) {
    const cle = clePeriodeParole(i);
    const courante = periodes[periodes.length - 1];
    if (!courante || courante.cle !== cle) {
      periodes.push({
        cle,
        banc: i.banc,
        gouvernementId: i.gouvernementId,
        gouvernement: i.gouvernement,
        debut: i.date,
        fin: i.date,
        interventions: [i],
      });
      continue;
    }
    courante.fin = i.date;
    courante.interventions.push(i);
  }
  return periodes.map((p) => ({
    ...p,
    groupes: [...new Set(p.interventions.map((i) => i.groupe).filter(Boolean))],
    // Aucun des deux repères : la période le DIT, elle n'est jamais rattachée à
    // la période voisine (§2 règle 5).
    sansRepere: !p.banc && !p.gouvernementId,
  }));
}

/* ── Les paroles, rangées par qualité ───────────────────────────────────────
 *
 * Une qualité française se découpe en périodes politiques, comme avant. La
 * qualité EUROPÉENNE, non : une législature européenne ne suit pas les
 * gouvernements français, et les y ranger produisait le « gouvernement Attal »
 * de Glucksmann. Elle rend donc UNE période, non datée, que la vue sait
 * reconnaître à `sansDecoupage` — et la sélection des périodes disparaît.
 *
 * Elle rend une période plutôt que rien parce que tout le reste de la vue —
 * natures, sujets, fil — travaille sur des périodes : lui faire deux chemins
 * aurait dupliqué ce que le découpage seul distingue.
 */
export function parolesParQualite(interventions, { roles = [], gouvernements = [] } = {}) {
  const parQualite = new Map();
  for (const i of interventions || []) {
    const q = qualiteDeParole(i);
    if (!parQualite.has(q)) parQualite.set(q, []);
    parQualite.get(q).push(i);
  }

  return ORDRE_QUALITES.filter((q) => parQualite.has(q)).map((q) => {
    const lot = parQualite.get(q);
    const qualifiees = qualifierInterventions(lot, { roles, gouvernements });
    if (q !== QUALITE_PE) {
      return { qualite: q, libelle: LIBELLE_QUALITE[q], total: lot.length, periodes: periodesDeParole(qualifiees) };
    }
    const datees = qualifiees.filter((i) => i.date).sort((a, b) => (a.date < b.date ? -1 : 1));
    return {
      qualite: q,
      libelle: LIBELLE_QUALITE[q],
      total: lot.length,
      periodes: datees.length ? [{
        cle: 'pe',
        banc: null,
        gouvernementId: null,
        gouvernement: null,
        debut: datees[0].date,
        fin: datees[datees.length - 1].date,
        interventions: datees,
        groupes: [],
        sansRepere: true,
        sansDecoupage: true,
      }] : [],
    };
  }).filter((b) => b.periodes.length);
}

/* ── Les sujets d'un lot ────────────────────────────────────────────────────
 *
 * Un sujet non publié n'est pas le plus petit des sujets : il garde son rang
 * par effectif mais porte son propre libellé, et reste sélectionnable — c'est
 * un lot d'interventions comme un autre, dont on ne connaît pas l'intitulé.
 */
export function sujetsDuLot(interventions) {
  const compte = new Map();
  for (const i of interventions || []) {
    const cle = i.sujet || SUJET_NON_PUBLIE;
    compte.set(cle, (compte.get(cle) || 0) + 1);
  }
  return [...compte.entries()]
    .map(([sujet, n]) => ({ sujet, n }))
    .sort((a, b) => b.n - a.n || a.sujet.localeCompare(b.sujet, 'fr'));
}

/* ── Les deux plafonds, et pourquoi il en faut deux ─────────────────────────
 *
 * Sur UNE période, l'échelle est celle du plus gros couple (période, sujet) de
 * la fiche : une barre se compare alors d'une période à l'autre, et un filtre
 * retire de la masse sans redimensionner — la règle posée sur « Ce qu'il a
 * voté ».
 *
 * Sur TOUTES les périodes à la fois, ce plafond serait dépassé par le premier
 * sujet cumulé. L'échelle devient donc celle de l'ensemble, et l'affichage
 * l'écrit : une barre d'ensemble ne se compare pas à une barre de période. Une
 * échelle qui changerait sans le dire serait le vrai défaut.
 */
export function plafondParPeriode(periodes) {
  let max = 0;
  for (const p of periodes || []) {
    for (const s of sujetsDuLot(p.interventions)) if (s.n > max) max = s.n;
  }
  return max || 1;
}

export function plafondToutesPeriodes(periodes) {
  const toutes = (periodes || []).flatMap((p) => p.interventions);
  const sujets = sujetsDuLot(toutes);
  return sujets.length ? sujets[0].n : 1;
}

/* ── Ce que la section sait de ses propres trous ────────────────────────────
 *
 * Publié, jamais laissé à la soustraction du lecteur (§2 règles 5 et 7). Trois
 * candidats sur les dix qui ont des interventions — Ruffin, Faure, Brun,
 * 5 483 lignes — relèvent du régime `theme_seul` : aucun verbatim, aucune
 * qualité, aucun intitulé sur 3 760 d'entre elles. Ce n'est pas une donnée
 * manquante à combler, c'est un régime de collecte nommé par le pipeline.
 */
export function couvertureDesParoles(qualifiees) {
  const liste = qualifiees || [];
  return {
    total: liste.length,
    datees: liste.filter((i) => i.date).length,
    sujet: liste.filter((i) => i.sujet).length,
    verbatim: liste.filter((i) => i.verbatim).length,
    fonction: liste.filter((i) => i.fonction).length,
    themeSeul: liste.filter((i) => i.themeSeul).length,
  };
}
