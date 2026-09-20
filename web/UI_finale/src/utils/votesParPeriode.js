/* ── Ce qu'il a voté : les positions rangées par période politique (#328) ─────
 *
 * Un décompte « 598 pour, 457 contre, 105 abstentions » sur une carrière entière
 * ne dit rien, parce qu'un même vote n'a pas le même sens selon d'où il est
 * émis : depuis la majorité, voter contre n'arrive presque jamais ; depuis
 * l'opposition, c'est le vote POUR qui se remarque. La section découpe donc les
 * positions en PÉRIODES POLITIQUES — une nouvelle dès que le banc ou le
 * gouvernement change — et ne totalise jamais par-dessus.
 *
 * Ce module ne contient que du calcul. Il ne connaît ni React ni CSS, et il
 * n'écrit AUCUNE règle qui vive déjà ailleurs : le repli sur la dernière lecture
 * et la sélection des votes sur l'ensemble d'un texte restent dans
 * `utils/lecture.js` (#711), la commission saisie au fond reste lue dans
 * `pivot_data/commissions_dossiers.json` (#328), le statut du dossier et le
 * 49.3 restent lus dans `pivot_data/scrutins_dossiers.json` (#758).
 *
 * TROIS REPÈRES, ET AUCUN N'EST DÉDUIT (§2 règles 2, 5 et 6).
 *
 *   - le BANC vient de `mandats[].position_dans_hemicycle`, que
 *     `validate_profil()` refuse sans `source_url` ;
 *   - le GOUVERNEMENT vient des dates du manifeste, elles-mêmes issues des
 *     fiches de gouvernement ;
 *   - l'ORIGINE du texte est lue dans l'intitulé officiel du scrutin, qui nomme
 *     lui-même la catégorie juridique — « projet de loi » ou « proposition ».
 *
 * Les deux premiers se COMPLÈTENT, et c'est la raison d'être du découpage :
 * de 2012 à 2017 l'Assemblée publie le banc mais aucune fiche de gouvernement
 * n'existe dans le corpus ; depuis 2024 c'est l'inverse. Mesuré sur les 1 160
 * positions de dernière lecture des 13 candidats déclarés, commit de données
 * `ac86c6e0` : le banc seul en couvre 719, le gouvernement seul 916, et le banc
 * OU le gouvernement les couvre 1 160 — aucune position ne reste sans repère.
 * Édouard Philippe et Xavier Bertrand n'ont QUE le banc (74 et 59 votes, aucun
 * gouvernement au corpus avant 2017) ; Marine Le Pen n'a le banc que sur 24 de
 * ses 132 positions, et le gouvernement sur les 132.
 * Une période sans aucun des deux existerait pourtant, et elle serait DÉCLARÉE
 * (`REPERE_NON_PUBLIE`), jamais rangée sous un repère voisin.
 */
import { estProcedure49_3, normalizeLabel, titreDuTexteVote } from './lecture';
import { MATIERE_NON_ETABLIE } from './profilCandidat';

export const ORIGINE_GOUVERNEMENT = 'gouvernement';
export const ORIGINE_PARLEMENT = 'parlement';

/* L'ordre de la figure, et le seul : contre à gauche de l'axe, abstention puis
 * pour à droite. Les colonnes de la liste et les boutons de filtre le suivent —
 * trois endroits, un seul ordre, parce qu'une colonne doit se retrouver sous la
 * portion de barre dont elle vient. */
export const POSITIONS_ORDONNEES = ['contre', 'abstention', 'pour'];

export const LIBELLE_POSITION = {
  contre: 'Contre',
  abstention: 'Abstention',
  pour: 'Pour',
};

export const LIBELLE_ORIGINE = {
  [ORIGINE_GOUVERNEMENT]: 'Gouvernement',
  [ORIGINE_PARLEMENT]: 'Parlement',
};

export const REPERE_NON_PUBLIE = 'Repère non publié';
export const ORIGINE_NON_ETABLIE = 'Origine non établie';

/* ── Règle : l'origine se lit dans l'intitulé, elle ne se rapproche pas ──────
 *
 * L'Assemblée écrit elle-même la catégorie juridique en tête de l'intitulé du
 * scrutin : « projet de loi » désigne un texte du gouvernement, « proposition
 * de loi » ou « proposition de résolution » un texte du Parlement. Ce n'est
 * donc PAS un rapprochement de chaînes entre deux corpus — ce que
 * `docs/decisions/regrouper-nest-pas-joindre-639.md` proscrit — mais la lecture
 * d'un mot que la source pose.
 *
 * Le motif est ANCRÉ EN TÊTE, après les seuls articles initiaux, jamais cherché
 * en sous-chaîne : « ... modifiant la proposition de loi ... » ne dit rien de
 * l'origine du texte voté.
 *
 * Mesuré au commit de données `ac86c6e0`, sur les scrutins de l'index :
 *   925 votes sur l'ensemble d'un texte : 425 gouvernement, 500 Parlement, 0 non établi
 *   697 dernières lectures              : 279 gouvernement, 418 Parlement, 0 non établi
 *
 * Le troisième état reste néanmoins dans le code et dans l'affichage. Une
 * couverture de 100 % à une date n'est pas une garantie de schéma : le jour où
 * un intitulé n'entre dans aucun des deux motifs, la page doit dire « origine
 * non établie » et surtout pas ranger le texte au Parlement par défaut
 * (§2 règle 5).
 */
const ARTICLE_INITIAL = /^(?:l'|la |le |les |de la |de l'|de |du |des )+/;
const PROJET_DE_LOI = /^projet de loi\b/;
const PROPOSITION = /^proposition\b/;

export function origineDuScrutin(scrutin) {
  const titre = normalizeLabel(titreDuTexteVote(scrutin?.texte)).replace(ARTICLE_INITIAL, '');
  if (PROJET_DE_LOI.test(titre)) return ORIGINE_GOUVERNEMENT;
  if (PROPOSITION.test(titre)) return ORIGINE_PARLEMENT;
  return null;
}

/* ── Les deux repères, lus à la date du vote ────────────────────────────────
 *
 * `rolesParlementaires` est la liste que `rolesDuParcours` a déjà construite :
 * elle porte `position` (le banc déclaré) et `detail` (le sigle du groupe). On
 * ne la recalcule pas ici — la fiche porterait deux lectures du même mandat.
 */
export function bancALaDate(rolesParlementaires, date) {
  if (!date) return null;
  const r = (rolesParlementaires || []).find((x) => x.debut <= date && date <= x.fin && x.position);
  return r ? { position: r.position, groupe: r.detail ?? null } : null;
}

/* Le nom court d'un gouvernement : « Gouvernement Borne » se lit « Borne » dans
 * un titre qui écrit déjà le mot. Le nom complet reste celui de la source. */
const PREFIXE_GOUVERNEMENT = /^gouvernement\s+/i;

export function nomCourtDeGouvernement(nom) {
  return (nom || '').replace(PREFIXE_GOUVERNEMENT, '').trim() || null;
}

export function gouvernementALaDate(gouvernements, date) {
  if (!date) return null;
  const g = (gouvernements || []).find(
    (x) => x.debut && x.debut <= date && (!x.fin || date <= x.fin),
  );
  return g ? { id: g.id, nom: nomCourtDeGouvernement(g.nom) } : null;
}

/* ── La qualification d'un vote retenu ──────────────────────────────────────
 *
 * Sept faits, chacun de sa source, aucun deviné. Une clé qu'on ne peut pas
 * résoudre reste `null` et le dit dans l'affichage — jamais un défaut, jamais
 * un zéro (§2 règle 5).
 */
export function qualifierVotes(
  retenus,
  { roles = [], gouvernements = [], scrutinsDossiers = null, commissionDuDossier = () => null } = {},
) {
  const parScrutin = scrutinsDossiers?.scrutins || null;
  const parDossier = scrutinsDossiers?.dossiers || null;

  return (retenus || []).map((v) => {
    const scrutin = v.scrutin || {};
    const date = v.date ?? scrutin.date ?? null;
    const banc = bancALaDate(roles, date);
    const gouvernement = gouvernementALaDate(gouvernements, date);
    const dossierId = (parScrutin && v.scrutin_id && parScrutin[v.scrutin_id]) || null;
    const dossier = (parDossier && dossierId && parDossier[dossierId]) || null;
    const commission = commissionDuDossier(dossierId);

    return {
      scrutinId: v.scrutin_id ?? scrutin.id ?? null,
      position: v.position,
      date,
      titre: titreDuTexteVote(scrutin.texte) || scrutin.texte || null,
      sourceUrl: scrutin.source_url ?? null,
      // La matière est la commission saisie au fond du DOSSIER, jamais déduite
      // d'un intitulé — ce serait une classification construite ici.
      matiere: commission?.sigle ?? null,
      origine: origineDuScrutin(scrutin),
      banc: banc?.position ?? null,
      groupe: banc?.groupe ?? null,
      gouvernementId: gouvernement?.id ?? null,
      gouvernement: gouvernement?.nom ?? null,
      dossierId,
      statutTexte: dossier?.statut ?? null,
      procedure49_3: estProcedure49_3(dossier?.statut ?? null),
    };
  });
}

/* ── Le découpage ───────────────────────────────────────────────────────────
 *
 * Une nouvelle période dès que le couple (banc, gouvernement) change. Les votes
 * sont triés par date d'abord : le corpus ne garantit aucun ordre, et une
 * période se refermerait puis se rouvrirait sur le même couple.
 */
export function clePeriode(vote) {
  return `${vote.banc ?? ''}|${vote.gouvernementId ?? ''}`;
}

export function periodesDeVote(votesQualifies) {
  const tries = [...(votesQualifies || [])]
    .filter((v) => v.date)
    .sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0));

  const periodes = [];
  for (const v of tries) {
    const cle = clePeriode(v);
    const courante = periodes[periodes.length - 1];
    if (!courante || courante.cle !== cle) {
      periodes.push({
        cle,
        banc: v.banc,
        gouvernementId: v.gouvernementId,
        gouvernement: v.gouvernement,
        debut: v.date,
        fin: v.date,
        votes: [v],
      });
      continue;
    }
    courante.fin = v.date;
    courante.votes.push(v);
  }
  return periodes.map((p) => ({
    ...p,
    groupes: [...new Set(p.votes.map((v) => v.groupe).filter(Boolean))],
    // Aucun des deux repères : la période le DIT. Elle n'est jamais rattachée à
    // la période voisine, ce qui inventerait un banc que la source ne publie pas.
    sansRepere: !p.banc && !p.gouvernementId,
  }));
}

/* ── Les lignes d'une période ───────────────────────────────────────────────
 *
 * Une ligne par matière, chaque position scindée par origine du texte. Les
 * matières sont ordonnées par effectif décroissant, « matière non établie »
 * toujours en dernier : c'est un vide déclaré, pas la plus petite des matières.
 */
function parts(votes, position) {
  const d = votes.filter((v) => v.position === position);
  return {
    gouvernement: d.filter((v) => v.origine === ORIGINE_GOUVERNEMENT).length,
    parlement: d.filter((v) => v.origine !== ORIGINE_GOUVERNEMENT).length,
  };
}

export function matieresDePeriode(periode, garde = () => true) {
  const dans = (periode?.votes || []).filter(garde);
  const compte = new Map();
  for (const v of dans) {
    const m = v.matiere || MATIERE_NON_ETABLIE;
    compte.set(m, (compte.get(m) || 0) + 1);
  }
  return [...compte.keys()]
    .sort((a, b) => {
      if (a === MATIERE_NON_ETABLIE) return 1;
      if (b === MATIERE_NON_ETABLIE) return -1;
      return compte.get(b) - compte.get(a) || (a < b ? -1 : 1);
    })
    .map((m) => {
      const d = dans.filter((v) => (v.matiere || MATIERE_NON_ETABLIE) === m);
      return {
        matiere: m,
        n: d.length,
        contre: parts(d, 'contre'),
        abstention: parts(d, 'abstention'),
        pour: parts(d, 'pour'),
      };
    });
}

/* ── Règle : UNE SEULE ÉCHELLE, calculée sur TOUS les votes ─────────────────
 *
 * L'échelle des barres se calcule sur la totalité des positions, filtres
 * compris, et ne bouge jamais. Recalculée à chaque filtre, elle ferait paraître
 * 2 textes parlementaires aussi larges que 37 gouvernementaux : cocher un
 * filtre n'apprendrait plus rien, et deux périodes ne se compareraient plus.
 * Un filtre RETIRE de la masse, il ne redimensionne pas.
 */
export function porteeCommune(periodes) {
  let portee = 1;
  for (const p of periodes || []) {
    for (const l of matieresDePeriode(p)) {
      const gauche = l.contre.gouvernement + l.contre.parlement;
      const droite =
        l.abstention.gouvernement + l.abstention.parlement + l.pour.gouvernement + l.pour.parlement;
      portee = Math.max(portee, gauche, droite);
    }
  }
  return portee;
}

/* Ce que la section publie d'elle-même : ses propres trous, comptés. Un
 * dénominateur sans numérateur se lirait comme une couverture complète. */
export function couvertureDesReperes(votesQualifies) {
  const liste = votesQualifies || [];
  return {
    total: liste.length,
    banc: liste.filter((v) => v.banc).length,
    gouvernement: liste.filter((v) => v.gouvernementId).length,
    unRepereAuMoins: liste.filter((v) => v.banc || v.gouvernementId).length,
    matiere: liste.filter((v) => v.matiere).length,
    origine: liste.filter((v) => v.origine).length,
    dossier: liste.filter((v) => v.dossierId).length,
    statut: liste.filter((v) => v.statutTexte).length,
    procedure49_3: liste.filter((v) => v.procedure49_3).length,
  };
}
