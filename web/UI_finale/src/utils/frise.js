/* ── La frise des noms, au téléphone (#1372, lot 3 suite, 28/10/2026) ──────────
 *
 * Deux frises partagent ce rangement : celle des gouvernements d'une
 * législature (forme F) et la fenêtre des gouvernements voisins sur la fiche de
 * gouvernement (forme C). Chaque nom part d'un trait vertical posé à sa date
 * de début, et descend jusqu'à la barre.
 *
 * Fonctions pures, sans DOM : la largeur de chaque nom est mesurée par le
 * composant (`FriseDesNoms.jsx`) et passée ici. Testées par
 * `tests/test_frise_des_noms_1372.py`. */

const CHIFFRE_ROMAIN = /^(.*?)\s+(I|II|III|IV|V|VI)$/;

/* « Lecornu II » → { premierMinistre: 'Lecornu', numero: 'II' }. Le nom du
 * Premier ministre est le nom sans le chiffre romain final. */
export function premierMinistre(nomCourt) {
  const m = String(nomCourt).trim().match(CHIFFRE_ROMAIN);
  return m ? { premierMinistre: m[1], numero: m[2] } : { premierMinistre: String(nomCourt).trim(), numero: null };
}

/* Les gouvernements CONSÉCUTIFS d'un même Premier ministre se réunissent sous
 * un seul nom (« Lecornu I et II »). Entrée : des gouvernements triés par date,
 * chacun `{ nom }` (nom sans « Gouvernement ») et ce qu'on veut y garder.
 * Sortie : des groupes `{ premierMinistre, membres: [{ ...gouvernement,
 * libelle }] }`, où `libelle` est le nom entier pour le premier membre et son
 * seul chiffre romain pour les suivants. Seul un gouvernement numéroté rejoint
 * le groupe qui le précède. */
export function reunirParPremierMinistre(gouvernements) {
  const groupes = [];
  for (const g of gouvernements) {
    const { premierMinistre: pm, numero } = premierMinistre(g.nom);
    const precedent = groupes[groupes.length - 1];
    if (precedent && numero && precedent.premierMinistre === pm) {
      precedent.membres.push({ ...g, libelle: numero });
    } else {
      groupes.push({ premierMinistre: pm, membres: [{ ...g, libelle: g.nom }] });
    }
  }
  return groupes;
}

/* Le mot qui précède le membre de rang `i` sur `n` : rien, « , », puis « et »
 * devant le dernier (« Fillon I, II et III »). */
export function liaison(i, n) {
  if (i === 0) return '';
  return i === n - 1 ? ' et ' : ', ';
}

const PERMUTATIONS_MAX = 7;

function permutations(xs) {
  if (xs.length <= 1) return [xs];
  return xs.flatMap((x, i) => permutations([...xs.slice(0, i), ...xs.slice(i + 1)]).map((p) => [x, ...p]));
}

/* Pose les noms dans l'ordre donné, chacun au niveau le plus bas permis.
 * Rend `null` si un nom ne trouve aucun niveau. */
function placer(ordre, { ecart, garde }) {
  const niveauxMax = Math.max(12, ordre.length);
  const places = [];
  for (const e of ordre) {
    const ok = (l) => places.every((o) => {
      // (a) deux noms d'un même niveau ne se touchent pas
      if (o.niveau === l && !(e.b + ecart <= o.a || e.a >= o.b + ecart)) return false;
      // (b) mon trait descend à travers les niveaux plus bas : il ne traverse aucun nom
      if (o.niveau < l && e.t1 >= o.a - garde && e.t0 <= o.b + garde) return false;
      // (c) le trait d'un nom plus haut ne traverse pas mon texte
      if (o.niveau > l && o.t1 >= e.a - garde && o.t0 <= e.b + garde) return false;
      return true;
    });
    let l = 0;
    while (l < niveauxMax && !ok(l)) l += 1;
    if (l >= niveauxMax) return null;
    places.push({ ...e, niveau: l });
  }
  return places;
}

/* LE RANGEMENT DES NOMS (forme F du 28/10/2026).
 *
 * `etiquettes` : `[{ x, largeur }]` en pixels — `x` est la position du trait
 * (la date de début), `largeur` celle du nom, trait et marge compris.
 * `largeurTotale` : la largeur de la frise.
 *
 * Un nom qui déborderait à droite s'écrit vers la gauche de son trait. Puis on
 * cherche le plus petit nombre de niveaux tel que (a) deux noms d'un même
 * niveau restent à `ecart` px l'un de l'autre, (b) le trait d'un nom ne
 * traverse jamais le texte d'un nom placé plus bas, (c) le texte d'un nom
 * n'est traversé par aucun trait d'un nom placé plus haut — en (b) et (c), le
 * trait (`trait` px de large) reste à `garde` px du texte : à 2 px, sur la
 * XVe, « 1 an 10 mois 9 jours » (Castex) se lisait collé au trait de Borne. Recherche
 * exhaustive sur les ordres de placement jusqu'à sept noms ; au-delà, placement
 * glouton, de droite à gauche puis de gauche à droite, le meilleur des deux.
 *
 * Rend `{ niveaux: [n par étiquette, 0 = contre la barre], aDroite: [bool],
 * nombre }`. Si aucun ordre ne tient (deux noms au même jour), chaque nom
 * prend son propre niveau, dans l'ordre : rien ne se chevauche. */
export function rangerEtiquettes(etiquettes, largeurTotale, { ecart = 4, garde = 4, trait = 2 } = {}) {
  const items = etiquettes.map((e, i) => {
    const aDroite = e.x + e.largeur > largeurTotale;
    // le trait (`trait` px) borde le nom : à gauche du texte, ou à sa droite
    return {
      i, aDroite, t: e.x,
      t0: aDroite ? e.x - trait : e.x, t1: aDroite ? e.x : e.x + trait,
      a: aDroite ? e.x - e.largeur : e.x, b: aDroite ? e.x : e.x + e.largeur,
    };
  });
  const aDroite = items.map((e) => e.aDroite);
  if (!items.length) return { niveaux: [], aDroite, nombre: 0 };
  const options = { ecart, garde };
  let meilleur = null;
  const essayer = (ordre) => {
    const places = placer(ordre, options);
    if (!places) return;
    const nombre = Math.max(...places.map((p) => p.niveau + 1));
    if (!meilleur || nombre < meilleur.nombre) meilleur = { nombre, places };
  };
  if (items.length <= PERMUTATIONS_MAX) permutations(items).forEach(essayer);
  else {
    essayer([...items].sort((u, v) => v.t - u.t));
    essayer([...items].sort((u, v) => u.t - v.t));
  }
  if (!meilleur) {
    return { niveaux: items.map((e) => e.i), aDroite, nombre: items.length };
  }
  const niveaux = Array.from({ length: items.length });
  meilleur.places.forEach((p) => { niveaux[p.i] = p.niveau; });
  return { niveaux, aDroite, nombre: meilleur.nombre };
}

/* LES ANNÉES QUI TIENNENT (fiche de groupe, forme C) : le plus petit pas parmi
 * 1, 2, 4, 5, 10 tel que deux années affichées soient séparées d'au moins deux
 * fois la largeur d'une année — la largeur d'une année de blanc entre deux. */
export function pasDesAnnees(pixelsParAn, largeurAnnee) {
  for (const pas of [1, 2, 4, 5, 10]) if (pas * pixelsParAn >= 2 * largeurAnnee) return pas;
  return 20;
}

/* LES ANNÉES D'UNE FENÊTRE (fiche de gouvernement, forme C) : une graduation
 * par 1er janvier, tant que les années se lisent sans se toucher. `xs` : la
 * position de chaque année en pixels. Chaque étiquette, centrée sur sa
 * position, est ramenée dans la largeur de la frise ; on prend une année sur
 * `pas` (le plus petit pas qui laisse `ecart` px entre deux années), puis on
 * écarte celle qu'un bord aurait poussée contre sa voisine. Rend les indices
 * gardés et le bord gauche de chacune. */
export function anneesLisibles(xs, largeurTotale, largeurAnnee, ecart = 8) {
  if (!xs.length) return [];
  const pasMin = Math.min(...xs.slice(1).map((x, i) => x - xs[i]), Infinity);
  const pas = Number.isFinite(pasMin) && pasMin > 0 ? Math.max(1, Math.ceil((largeurAnnee + ecart) / pasMin)) : 1;
  const gardees = [];
  let finPrecedente = -Infinity;
  xs.forEach((x, i) => {
    if (i % pas) return;
    const gauche = Math.max(0, Math.min(largeurTotale - largeurAnnee, x - largeurAnnee / 2));
    if (gauche < finPrecedente + ecart) return;
    gardees.push({ i, gauche });
    finPrecedente = gauche + largeurAnnee;
  });
  return gardees;
}
