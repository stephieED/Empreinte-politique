/*
 * L'ORDRE DU JOUR DES SÉANCES, mis en agenda (#1354, forme B « agenda mural »
 * retenue le 26/10/2026 ; maquette https://claude.ai/artifact/Jvp4qhqXJjErdnHLbwiCWh).
 *
 * Le fichier vient de Backend, un par législature (`ordre_du_jour/<n>.json`) :
 * des jours, chacun avec ses séances et ses points. Un point de discussion
 * porte un dossier — celui que la source donne, ou celui d'un autre point du
 * même ordre du jour au même intitulé. Ici, on ne fait que lire : la commission
 * vient de `commissions_dossiers.json`, la couleur de `commissions.js`, la même
 * table que sur les autres fiches.
 *
 * TROIS ABSENCES QUI NE SE CONFONDENT PAS (§2 règle 5) : un jour sans séance,
 * un jour dont l'ordre du jour n'est pas encore fixé (législature en cours,
 * après le dernier jour publié), un point dont le texte n'est pas retrouvé
 * (« Matière non établie »).
 */
import { MATIERE_NON_ETABLIE } from './profilCandidat.js';
import { ORDRE_DES_FAMILLES, familleDeCommission, teinteDeLaFamille } from './commissions.js';
import { contientLesMots } from './filtreIntitule.js';

export const MOIS = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
  'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'];
const JOURS = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche'];
const INITIALES = ['L', 'M', 'M', 'J', 'V', 'S', 'D'];

/* Les points qui ne portent pas sur un texte : on les nomme, sans couleur. */
export const GENRES = {
  questions_gouvernement: 'Questions au Gouvernement',
  questions_orales: 'Questions orales',
  debat: 'Débat',
  declaration: 'Déclaration du Gouvernement',
  session: 'Ouverture ou clôture de session',
  autre: 'Autre point',
};

const iso = (t) => new Date(t).toISOString().slice(0, 10);
const utc = (s) => { const [a, m, j] = s.split('-').map(Number); return Date.UTC(a, m - 1, j); };
const joursem = (t) => (new Date(t).getUTCDay() + 6) % 7;
/* Le numéro de semaine ISO 8601, celui des calendriers français : la semaine 1
 * est celle qui contient le premier jeudi de l'année. */
function semaineIso(s) {
  const t = utc(s);
  const jeudi = t + (3 - joursem(t)) * 86400000;
  const an = new Date(jeudi).getUTCFullYear();
  return 1 + Math.floor((jeudi - Date.UTC(an, 0, 1)) / (7 * 86400000));
}

export function dateLongue(s) {
  const t = utc(s), d = new Date(t);
  const j = d.getUTCDate();
  return `${JOURS[joursem(t)]} ${j === 1 ? '1er' : j} ${MOIS[d.getUTCMonth()].toLowerCase()} ${d.getUTCFullYear()}`;
}

/* L'intitulé d'un point dont le dossier est inconnu, sans la mécanique de la
 * séance (« Suite de la discussion, en deuxième lecture, de la… »). */
export function intituleCourt(objet) {
  let s = (objet || '').replace(/\s+/g, ' ').trim();
  for (let k = 0; k < 3; k += 1) {
    s = s.replace(/^(Éventuellement,?|Suite de la discussion,?|Discussion,?|sous réserve de son dépôt,?|Vote solennel sur|Explications de vote[^:]*? sur)\s*/i, '')
      .replace(/^(en (première|deuxième|nouvelle|troisième) lecture|sur le rapport de la commission mixte paritaire|en lecture définitive),?\s*/i, '')
      .replace(/^(de la |du |des |de l'|de l’)/, '')
      .trim();
  }
  return s ? s[0].toUpperCase() + s.slice(1) : '';
}

/** Les points d'un jour, prêts à lire : titre, famille de commission, couleur. */
function lirePoints(points, { titres, commissions }) {
  return points.map((p) => {
    if (p.genre !== 'texte') {
      // Un débat ou une déclaration a un sujet, qui se lit ; les questions, non.
      const genre = GENRES[p.genre] || GENRES.autre;
      const sujet = p.genre === 'debat' || p.genre === 'declaration' ? intituleCourt(p.intitule) : '';
      return { texte: false, titre: sujet || genre, genre, n: p.n || 1 };
    }
    const famille = p.dossier ? familleDeCommission(commissions[p.dossier]?.sigle) : MATIERE_NON_ETABLIE;
    return {
      texte: true,
      titre: (p.dossier && titres[p.dossier]) || intituleCourt(p.intitule),
      famille, couleur: teinteDeLaFamille(famille), solennel: Boolean(p.solennel), n: p.n || 1,
    };
  });
}

/**
 * La vue de l'agenda. `fichier` est le JSON de Backend ; `periode` les bornes
 * de la législature ; `mots` le filtre de la recherche ; `depuis` la fenêtre
 * de période (législature en cours seulement).
 */
export function vueOrdreDuJour(fichier, { titres = {}, commissions = {}, periode = {}, aujourdhui, mots = [], depuis = null } = {}) {
  if (!fichier?.jours?.length) return null;
  const parDate = new Map();
  let dernier = '';
  for (const j of fichier.jours) {
    let points = lirePoints(j.points || [], { titres, commissions });
    if (mots.length) points = points.filter((p) => contientLesMots(p.titre, mots));
    if (depuis && j.date < depuis) points = [];
    parDate.set(j.date, { seances: j.seances, points });
    if (j.date > dernier) dernier = j.date;
  }
  const debut = periode.debut || fichier.jours[0].date;
  const fin = periode.fin || null;
  const enCours = !fin;
  const borne = fin || dernier;
  const annees = [];
  for (let a = Number(debut.slice(0, 4)); a <= Number(borne.slice(0, 4)); a += 1) annees.push(a);
  const familles = new Set();
  let sansTexte = false;
  for (const { points } of parDate.values()) {
    for (const p of points) { if (p.texte) familles.add(p.famille); else sansTexte = true; }
  }

  function jourDe(t) {
    const date = iso(t), w = joursem(t);
    const j = parDate.get(date);
    return {
      date, num: String(new Date(t).getUTCDate()).padStart(2, '0'), initiale: INITIALES[w], weekend: w >= 5,
      hors: date < debut || (fin != null && date > fin),
      aVenir: date > aujourdhui,
      nonFixe: enCours && !j && date > dernier,
      seances: j?.seances ?? 0, points: j?.points ?? [],
    };
  }
  function joursDuMois(a, m) {
    const jours = [];
    for (let t = Date.UTC(a, m, 1); new Date(t).getUTCMonth() === m; t += 86400000) jours.push(jourDe(t));
    return jours;
  }
  function annee(a) {
    return MOIS.map((nom, m) => ({ nom, jours: joursDuMois(a, m) }));
  }

  /* LA VUE SEMAINES EST UN CALENDRIER MURAL (26/10/2026, sur une capture de la
   * propriétaire) : douze mois, chacun en lignes de semaines numérotées et en
   * colonnes du lundi au dimanche. Un cumul par semaine, essayé d'abord, a été
   * refusé : « Ce n'est pas à ça que ressemblent les agendas par semaine ». */
  function calendrier(a) {
    return annee(a).map(({ nom, jours }) => {
      const semainesDuMois = [];
      let ligne = null;
      for (const j of jours) {
        const w = joursem(utc(j.date));
        if (!ligne || w === 0) {
          const lundi = utc(j.date) - w * 86400000;
          ligne = { numero: semaineIso(j.date), lundi: iso(lundi), jours: Array(7).fill(null) };
          semainesDuMois.push(ligne);
        }
        ligne.jours[w] = j;
      }
      return { nom, semaines: semainesDuMois };
    });
  }

  /* UNE SEMAINE OU UN MOIS SÉLECTIONNÉ (26/10/2026) : le détail cumule ses
   * jours de séance — chaque texte une fois, avec le nombre de jours où il a été
   * discuté dans la période. Les textes d'abord, puis questions et débats. */
  function detailDePeriode(type, cle) {
    const dates = [];
    let titre;
    if (type === 'semaine') {
      const t0 = utc(cle);
      for (let k = 0; k < 7; k += 1) dates.push(iso(t0 + k * 86400000));
      const d0 = new Date(t0), d6 = new Date(t0 + 6 * 86400000);
      const j0 = d0.getUTCDate(), j6 = d6.getUTCDate();
      const m0 = MOIS[d0.getUTCMonth()].toLowerCase(), m6 = MOIS[d6.getUTCMonth()].toLowerCase();
      titre = `Semaine ${semaineIso(cle)} · du ${j0 === 1 ? '1er' : j0}${m0 !== m6 ? ` ${m0}` : ''} au ${j6 === 1 ? '1er' : j6} ${m6} ${d6.getUTCFullYear()}`;
    } else {
      const [a, m] = cle.split('-').map(Number);
      for (let t = Date.UTC(a, m - 1, 1); new Date(t).getUTCMonth() === m - 1; t += 86400000) dates.push(iso(t));
      titre = `${MOIS[m - 1]} ${a}`;
    }
    const entrees = new Map();
    let jours = 0, aVenir = true;
    for (const d of dates) {
      const j = parDate.get(d);
      if (!j || !j.points.length) continue;
      jours += 1;
      if (d <= aujourdhui) aVenir = false;
      for (const p of j.points) {
        const k = `${p.texte ? 't' : 'g'}:${p.titre}`;
        const e = entrees.get(k) || { ...p, jours: 0, solennel: false };
        e.jours += 1; e.solennel = e.solennel || p.solennel;
        entrees.set(k, e);
      }
    }
    const points = [...entrees.values()];
    return { type, cle, titre, jours, aVenir: jours > 0 && aVenir, points: [...points.filter((p) => p.texte), ...points.filter((p) => !p.texte)] };
  }

  /* L'année ouverte par défaut : celle du dernier jour de séance passé. Le jour
   * détaillé : ce même jour. */
  const passes = [...parDate.keys()].filter((d) => d <= aujourdhui && parDate.get(d).points.length).sort();
  const dernierPasse = passes[passes.length - 1] || null;
  return {
    annees,
    annee,
    calendrier,
    detailDePeriode,
    parDate,
    anneeParDefaut: dernierPasse ? Number(dernierPasse.slice(0, 4)) : annees[annees.length - 1],
    jourParDefaut: (a) => [...passes].reverse().find((d) => d.startsWith(String(a))) || null,
    legende: [
      ...ORDRE_DES_FAMILLES.filter((f) => familles.has(f)).map((f) => ({ libelle: f, couleur: teinteDeLaFamille(f) })),
    ],
    sansTexte,
    enCours,
  };
}
