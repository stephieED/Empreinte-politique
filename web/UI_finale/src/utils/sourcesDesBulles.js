/* ── Le pied de source d'une bulle de section (#1389, 29/10/2026) ─────────────
 *
 * Chaque bulle de section se termine par une ligne par source qui alimente la
 * section : le nom de la source, en lien vers elle, et « mis à jour le
 * JJ/MM/AAAA ». Forme B, retenue sur maquette par la propriétaire, avec ses
 * mots : « mis à jour », pas « consulté ».
 *
 * LE NOM EST CELUI DU SCHÉMA DE LA PAGE SOURCES (`SOURCES_SCHEMA`), à la lettre :
 * le lecteur reconnaît la source d'une page à l'autre, et un objet garde un seul
 * nom sur le site.
 *
 * LA DATE EST `sources[].synchro_le` DU PROFIL : le moment où la collecte a
 * relu cette source pour cette fiche. Ce n'est pas la date du dernier fait
 * publié par la source (un député qui n'a pas voté depuis un an a quand même
 * une fiche relue hier). Une source sans date lisible n'a pas de ligne : on
 * n'invente pas de date (§2 règle 5).
 *
 * Une source citée sans être interrogée (Sycomore, les décrets de nomination
 * du Journal officiel) n'a pas de date de relecture : elle n'a pas de ligne
 * ici, et reste nommée par la page Sources.
 */
import { SOURCES_SCHEMA } from '../data/schemaSources.js';

/* Le `type` d'une entrée de `sources[]` du profil → l'identifiant du schéma.
 * Un type absent d'ici n'a pas de ligne : il faudrait d'abord lui donner une
 * place dans le schéma de la page Sources. */
export const TYPE_VERS_SCHEMA = {
  assemblee_nationale: 'an',
  senat: 'sen',
  europarl: 'pe',
  parltrack: 'pt',
  rne: 'rne',
};

const ORDRE = SOURCES_SCHEMA.map((s) => s.id);
const PAR_ID = Object.fromEntries(SOURCES_SCHEMA.map((s) => [s.id, s]));

const FORMAT = new Intl.DateTimeFormat('fr-FR', {
  timeZone: 'Europe/Paris',
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
});

/* `synchro_le` arrive avec son fuseau (« +0000 ») ou sans (ParlTrack). Sans
 * fuseau, l'heure est celle du serveur de collecte, qui tourne en UTC. */
function instant(valeur) {
  if (typeof valeur !== 'string' || !valeur) return null;
  let v = valeur.replace(/([+-]\d{2})(\d{2})$/, '$1:$2');
  if (/T\d{2}:\d{2}(:\d{2}(\.\d+)?)?$/.test(v)) v += 'Z';
  const ms = Date.parse(v);
  return Number.isNaN(ms) ? null : ms;
}

/**
 * Les dates de relecture du profil, par source du schéma.
 * Deux entrées du même type : la plus ANCIENNE l'emporte, pour ne jamais
 * annoncer une fiche plus fraîche que sa partie la moins fraîche.
 *
 * @param {Array} sources  `sources[]` du profil pivot
 * @returns {Object} `{ [id du schéma]: ms }`
 */
export function datesDesSources(sources) {
  const dates = {};
  for (const s of sources || []) {
    const id = TYPE_VERS_SCHEMA[s?.type];
    const ms = instant(s?.synchro_le);
    if (!id || ms === null) continue;
    if (dates[id] === undefined || ms < dates[id]) dates[id] = ms;
  }
  return dates;
}

/**
 * Les lignes du pied d'une bulle, dans l'ordre du schéma de la page Sources.
 *
 * @param {Array} demandees  les sources de la section : un identifiant du
 *                           schéma, ou `{ id, url }` quand la section a une page
 *                           plus précise que l'accueil de la source
 * @param {Object} dates     le résultat de `datesDesSources`
 * @returns {Array} `[{ id, nom, url, date }]`, `date` en « JJ/MM/AAAA »
 */
export function lignesDeSources(demandees, dates) {
  if (!demandees?.length || !dates) return [];
  const urls = {};
  for (const d of demandees) {
    if (typeof d === 'string') urls[d] = urls[d] ?? null;
    else if (d?.id) urls[d.id] = d.url ?? null;
  }
  return ORDRE
    .filter((id) => id in urls && dates[id] !== undefined && PAR_ID[id])
    .map((id) => ({
      id,
      nom: PAR_ID[id].nom,
      url: urls[id] || PAR_ID[id].url,
      date: FORMAT.format(dates[id]),
    }));
}
