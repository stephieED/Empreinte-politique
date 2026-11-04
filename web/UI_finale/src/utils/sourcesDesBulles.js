/* ── Le pied de source d'une bulle de section (#1389) ─────────────────────────
 *
 * Chaque bulle de section se termine par une ligne par source qui alimente la
 * section : le nom de la source, en lien vers elle, et « à jour au
 * JJ/MM/AAAA ». Forme B, retenue sur maquette par la propriétaire le
 * 29/10/2026.
 *
 * LE NOM EST CELUI DU SCHÉMA DE LA PAGE SOURCES (`SOURCES_SCHEMA`), à la lettre :
 * le lecteur reconnaît la source d'une page à l'autre, et un objet garde un seul
 * nom sur le site.
 *
 * LA DATE EST « À JOUR AU » (arbitré le 29/10/2026) : la dernière relecture
 * RÉUSSIE de chaque famille de données, lue dans `fraicheur_sources.json`
 * (`familles[…].a_jour_au`). Ce n'était pas `sources[].synchro_le` du profil,
 * affiché du 29/10 au 04/11 : ce champ dit quand la donnée a CHANGÉ, si bien
 * qu'un profil relu sans changement gardait une date ancienne. Une famille en
 * échec garde la date de sa dernière relecture réussie : c'est ce que « à jour
 * au » veut dire. Une famille sans date n'a pas de ligne : on n'invente pas de
 * date (§2 règle 5).
 *
 * UNE BULLE DÉCLARE SES FAMILLES (« an.votes »), ou une source entière (« an »)
 * pour toutes les familles de cette source que lit la fiche. Une source qui
 * alimente la section par plusieurs familles n'a qu'une ligne, à la date de la
 * plus ANCIENNE : la section n'est pas plus à jour que sa partie la moins
 * fraîche.
 *
 * UNE SOURCE ABSENTE DE LA FICHE N'A PAS DE LIGNE : le pied d'Attal ne nomme ni
 * le Sénat ni le Parlement européen, où il n'a pas siégé. La présence se lit
 * dans `sources[]` du profil, comme avant le 04/11.
 *
 * Une source citée sans être interrogée (Sycomore, les décrets de nomination
 * du Journal officiel) n'a pas de famille : elle n'a pas de ligne ici, et reste
 * nommée par la page Sources.
 */
import { SOURCES_SCHEMA } from '../data/schemaSources.js';

/* Les familles de `fraicheur_sources.json` par source du schéma (pour l'AN,
 * celles que lit la fiche candidat). Une bulle qui déclare une source entière
 * les reçoit toutes. */
export const FAMILLES_PAR_SOURCE = {
  an: ['an.mandats', 'an.gouvernements', 'an.votes', 'an.interventions', 'an.questions', 'an.dossiers', 'an.amendements'],
  sen: ['sen.mandats'],
  pe: ['pe.mandats', 'pe.documents'],
  pt: ['pt.textes', 'pt.amendements', 'pt.votes', 'pt.interventions'],
  rne: ['rne.mandats_locaux'],
  // Les budgets de la fiche de gouvernement : une famille par source, sans point.
  mef: ['budget_etat'],
  drees: ['drees'],
  unedic: ['unedic'],
};

/* Le `type` d'une entrée de `sources[]` du profil → l'identifiant du schéma. */
export const TYPE_VERS_SCHEMA = {
  assemblee_nationale: 'an',
  senat: 'sen',
  europarl: 'pe',
  parltrack: 'pt',
  rne: 'rne',
};

/** Les sources du schéma présentes dans `sources[]` du profil. */
export function sourcesDuProfil(sources) {
  return [...new Set((sources || []).map((s) => TYPE_VERS_SCHEMA[s?.type]).filter(Boolean))];
}

const ORDRE = SOURCES_SCHEMA.map((s) => s.id);
const PAR_ID = Object.fromEntries(SOURCES_SCHEMA.map((s) => [s.id, s]));

const FORMAT = new Intl.DateTimeFormat('fr-FR', {
  timeZone: 'UTC',
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
});

/* `a_jour_au` est une date sans heure (« 2026-11-03 ») : elle se lit telle
 * quelle, sans fuseau, pour ne pas glisser d'un jour. */
function jour(valeur) {
  if (typeof valeur !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(valeur)) return null;
  const ms = Date.parse(`${valeur}T00:00:00Z`);
  return Number.isNaN(ms) ? null : ms;
}

/* Les familles dont le nom ne commence pas par l'identifiant du schéma. */
const SOURCE_DE_FAMILLE = { budget_etat: 'mef', drees: 'drees', unedic: 'unedic' };

/**
 * L'état de chaque source de la page Sources (#1389, forme A du 04/11/2026),
 * toutes ses familles réunies : `aJourAu`, la plus ancienne dernière relecture
 * réussie, et `enEchecDepuis`, le plus ancien début d'échec, ou `null`. Une
 * source dont aucune famille n'a de date n'est pas dans le résultat : on
 * n'invente pas de date (§2 règle 5).
 *
 * @param {Object} fraicheur  le contenu de `fraicheur_sources.json`
 * @returns {Object} `{ [id du schéma]: { aJourAu, enEchecDepuis } }`, dates « AAAA-MM-JJ »
 */
export function etatDesSources(fraicheur) {
  const etats = {};
  const jourValide = (v) => (jour(v) === null ? null : v);
  for (const [famille, f] of Object.entries(fraicheur?.familles || {})) {
    const id = SOURCE_DE_FAMILLE[famille] || famille.split('.')[0];
    const aJourAu = jourValide(f?.a_jour_au);
    const echec = f?.etat === 'en_echec' ? jourValide(f?.en_echec_depuis) : null;
    const e = etats[id] || { aJourAu: null, enEchecDepuis: null };
    if (aJourAu && (!e.aJourAu || aJourAu < e.aJourAu)) e.aJourAu = aJourAu;
    if (echec && (!e.enEchecDepuis || echec < e.enEchecDepuis)) e.enEchecDepuis = echec;
    etats[id] = e;
  }
  for (const id of Object.keys(etats)) if (!etats[id].aJourAu) delete etats[id];
  return etats;
}

/**
 * Les dates « à jour au » de chaque famille.
 *
 * @param {Object} fraicheur  le contenu de `fraicheur_sources.json`
 * @returns {Object} `{ [famille]: ms }`, sans les familles sans date
 */
export function datesDesFamilles(fraicheur) {
  const dates = {};
  for (const [famille, f] of Object.entries(fraicheur?.familles || {})) {
    const ms = jour(f?.a_jour_au);
    if (ms !== null) dates[famille] = ms;
  }
  return dates;
}

/**
 * Les lignes du pied d'une bulle, dans l'ordre du schéma de la page Sources.
 *
 * @param {Array} demandees  ce qui alimente la section : une famille
 *                           (« an.votes »), une source entière (« an »), ou
 *                           `{ id, url }` quand la section a une page plus
 *                           précise que l'accueil de la source (`id` étant une
 *                           famille ou une source)
 * @param {Object} dates     le résultat de `datesDesFamilles`
 * @param {Array} presentes  les sources de la fiche (`sourcesDuProfil`) ;
 *                           absent, aucune n'est retirée
 * @returns {Array} `[{ id, nom, url, date }]`, `date` en « JJ/MM/AAAA »
 */
export function lignesDeSources(demandees, dates, presentes = null) {
  if (!demandees?.length || !dates) return [];
  const familles = {};
  const urls = {};
  for (const d of demandees) {
    const cle = typeof d === 'string' ? d : d?.id;
    if (!cle) continue;
    const source = cle.split('.')[0];
    familles[source] = familles[source] || new Set();
    for (const f of cle.includes('.') ? [cle] : FAMILLES_PAR_SOURCE[source] || []) familles[source].add(f);
    if (typeof d !== 'string' && d.url) urls[source] = d.url;
  }
  return ORDRE
    .filter((id) => familles[id] && PAR_ID[id] && (!presentes || presentes.includes(id)))
    .map((id) => {
      const connues = [...familles[id]].map((f) => dates[f]).filter((ms) => ms !== undefined);
      return connues.length ? { id, ms: Math.min(...connues) } : null;
    })
    .filter(Boolean)
    .map(({ id, ms }) => ({
      id,
      nom: PAR_ID[id].nom,
      url: urls[id] || PAR_ID[id].url,
      date: FORMAT.format(ms),
    }));
}
