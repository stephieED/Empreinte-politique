/* ── Trouver les amendements d'un sujet par les mots de leur exposé (#1029) ──
 *
 * Voie 2 de #1029. L'intitulé d'un amendement est celui de son DOSSIER, qui
 * nomme le véhicule (« projet de loi de finances ») et jamais le sujet :
 * « carburant » rendait 0 amendement. Backend publie, par législature, l'index
 * des mots de l'exposé sommaire (`pivot_data/amendements/<lég>.contenu.json`,
 * `src/amendements_contenu.py`, #1092) : 93 Mo pour quatre législatures, trop
 * pour une page. Le build en tire, par FICHE, le vocabulaire des seuls
 * amendements qu'elle porte ; ce module est la règle de lecture, la même au
 * build et à l'écran, et la même que `amendements_contenu.py` — un test
 * compare les deux.
 *
 * LIMITES, À DIRE :
 * - un mot de moins de 4 lettres n'est pas indexé (« TVA ») : il ne cherche que
 *   dans l'intitulé du dossier ;
 * - un mot présent dans plus de 3 % des amendements d'une législature n'est pas
 *   indexé (« amendement », « article ») ;
 * - l'index est celui des MOTS, pas du texte : deux mots tapés sont cherchés
 *   dans le même exposé, sans ordre ni proximité.
 */

export const LONGUEUR_MIN_MOT = 4;
export const FUSION_DES_FORMES = [['aux', 'al'], ['es', ''], ['s', ''], ['x', ''], ['e', '']];

/** Positions croissantes → écarts successifs en base 36, séparés par des virgules. */
export function encoder(positions) {
  let precedent = 0;
  return positions.map((p) => {
    const ecart = p - precedent;
    precedent = p;
    return ecart.toString(36);
  }).join(',');
}

/** L'inverse d'`encoder` — `amendements_contenu.decoder`. */
export function decoder(renvois) {
  const positions = [];
  let courant = 0;
  for (const morceau of renvois ? renvois.split(',') : []) {
    courant += parseInt(morceau, 36);
    positions.push(courant);
  }
  return positions;
}

/** Les mots cherchables d'une saisie, normalisés comme un exposé : minuscules,
 *  accents retirés, `[a-z]{4,}`. */
export function motsCherchables(saisie) {
  const texte = String(saisie ?? '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
  return [...new Set(texte.match(new RegExp(`[a-z]{${LONGUEUR_MIN_MOT},}`, 'g')) || [])];
}

/** La forme sous laquelle `mot` est indexé — `amendements_contenu.forme_indexee`. */
export function formeIndexee(mot, vocabulaire, fusion = FUSION_DES_FORMES) {
  for (const [terminaison, remplacement] of fusion) {
    if (!mot.endsWith(terminaison)) continue;
    const base = mot.slice(0, mot.length - terminaison.length) + remplacement;
    if (base.length >= LONGUEUR_MIN_MOT && base !== mot && vocabulaire.has(base)) {
      return formeIndexee(base, vocabulaire, fusion);
    }
  }
  return mot;
}

/**
 * Les uid des amendements dont l'exposé porte chacun des mots de la saisie —
 * l'uid AN (`AMANR5L17…`), sans le préfixe `an:` que le pivot lui ajoute.
 *
 * `vocabulaires` : `[{ prefixe, ids, mots }]`, un par législature. Un mot est
 * cherché comme le filtre de la fiche cherche un intitulé — par INCLUSION :
 * « carbur » trouve « carburant » et « biocarburant » —, après avoir été ramené
 * à sa forme indexée. Rend `null` quand la saisie n'a aucun mot cherchable
 * (tous de moins de 4 lettres) : on ne peut rien dire du contenu.
 */
export function amendementsQuiPortent(vocabulaires, saisie) {
  const mots = motsCherchables(saisie);
  if (!mots.length) return null;
  const retenus = new Set();
  for (const v of vocabulaires || []) {
    if (!v?.mots || !v.ids) continue;
    const cles = Object.keys(v.mots);
    const vocabulaire = new Set(cles);
    let positions = null;
    for (const mot of mots) {
      const forme = formeIndexee(mot, vocabulaire);
      const ici = new Set();
      for (const cle of cles) {
        if (cle.includes(forme)) for (const p of decoder(v.mots[cle])) ici.add(p);
      }
      positions = positions === null ? ici : new Set([...positions].filter((p) => ici.has(p)));
      if (!positions.size) break;
    }
    for (const p of positions || []) retenus.add(`${v.prefixe || ''}${v.ids[p]}`);
  }
  return retenus;
}

/**
 * Au build : le vocabulaire de chaque fiche, tiré d'un document de législature.
 *
 * `doc` : `<lég>.contenu.json` ; `fiches` : Map `clé de fiche` → Set d'uid.
 * Rend Map `clé` → `{ prefixe, ids, mots }`, où `ids` sont les uid de la fiche
 * présents dans le document (sans le préfixe, triés) et `mots` ses renvois,
 * renumérotés sur `ids`. Une seule passe sur les renvois de la législature.
 */
export function vocabulairesDesFiches(doc, fiches) {
  const prefixe = doc.prefixe_ids || '';
  const positionDe = new Map(doc.ids.map((id, p) => [id, p]));
  const locales = new Map();
  const parPosition = new Map();
  for (const [cle, uids] of fiches) {
    const ids = [...uids]
      .filter((u) => u.startsWith(prefixe) && positionDe.has(u.slice(prefixe.length)))
      .map((u) => u.slice(prefixe.length))
      .sort();
    locales.set(cle, { prefixe, ids, mots: {} });
    ids.forEach((id, locale) => {
      const p = positionDe.get(id);
      if (!parPosition.has(p)) parPosition.set(p, []);
      parPosition.get(p).push([cle, locale]);
    });
  }
  const postings = new Map([...locales.keys()].map((cle) => [cle, new Map()]));
  for (const [mot, renvois] of Object.entries(doc.mots || {})) {
    for (const p of decoder(renvois)) {
      for (const [cle, locale] of parPosition.get(p) || []) {
        const m = postings.get(cle);
        if (!m.has(mot)) m.set(mot, []);
        m.get(mot).push(locale);
      }
    }
  }
  for (const [cle, m] of postings) {
    const mots = locales.get(cle).mots;
    for (const [mot, liste] of [...m.entries()].sort((a, b) => a[0].localeCompare(b[0]))) {
      mots[mot] = encoder(liste.sort((a, b) => a - b));
    }
  }
  return locales;
}
