/*
 * VALIDER UN JSON-LD CONTRE LE VOCABULAIRE DE SCHEMA.ORG (#1008).
 *
 * Mesuré le 18/09/2026 : le validateur de Google refuse les requêtes au-delà
 * d'une trentaine — 34 sur 34 bloquées, même espacées de six secondes. Le
 * critère de fin de #1008 demande pourtant que CHAQUE fiche soit vérifiée. Ce
 * module le fait sans Google : il télécharge le vocabulaire publié par
 * schema.org et vérifie que chaque `@type` existe et que chaque propriété
 * appartient à son type.
 *
 * LE PIÈGE, PAYÉ LE 18/09/2026 : une première passe a rendu 420 anomalies,
 * toutes fausses. Elles venaient du PATRON `Role` de schema.org — un rôle daté
 * porte la propriété par laquelle il est rattaché (`Person.memberOf` →
 * `OrganizationRole.memberOf` → `Organization`), ce que `domainIncludes` ne
 * peut pas exprimer. Un `Role` accepte donc toute propriété connue, et c'est
 * la règle du vocabulaire, pas une tolérance de confort.
 *
 * Ce qu'il ne fait pas : dire si un type donne droit à un affichage enrichi
 * dans Google — ça, seul l'outil de Google le dit, et `Person` n'y donne pas
 * droit de toute façon.
 */
const VOCABULAIRE = 'https://schema.org/version/latest/schemaorg-current-https.jsonld';

const liste = (x) => (x === undefined || x === null ? [] : [].concat(x));
const nom = (ref) => String(ref['@id'] || ref).split(':').pop();

export async function chargerVocabulaire(url = VOCABULAIRE) {
  const reponse = await fetch(url);
  if (!reponse.ok) throw new Error(`vocabulaire schema.org : HTTP ${reponse.status}`);
  return construireVocabulaire(await reponse.json());
}

export function construireVocabulaire(document) {
  const types = new Map();
  const proprietes = new Map();
  for (const terme of document['@graph'] || []) {
    const t = liste(terme['@type']);
    if (t.includes('rdfs:Class')) types.set(nom(terme), liste(terme['rdfs:subClassOf']).map(nom));
    if (t.includes('rdf:Property')) proprietes.set(nom(terme), liste(terme['schema:domainIncludes']).map(nom));
  }
  return { types, proprietes };
}

function ancetres(types, type, vus = new Set()) {
  if (vus.has(type) || !types.has(type)) return vus;
  vus.add(type);
  for (const parent of types.get(type)) ancetres(types, parent, vus);
  return vus;
}

/* Rend la liste des anomalies — vide quand l'objet est conforme. */
export function anomalies(vocabulaire, objet, chemin = '') {
  const trouvees = [];
  const type = objet['@type'];
  if (!vocabulaire.types.has(type)) return [`${chemin || '/'} : type inconnu de schema.org — ${type}`];
  const permis = ancetres(vocabulaire.types, type);
  const estRole = permis.has('Role');
  for (const [cle, valeur] of Object.entries(objet)) {
    if (cle.startsWith('@')) continue;
    const domaine = vocabulaire.proprietes.get(cle);
    if (!domaine) {
      trouvees.push(`${chemin}/${cle} : propriété inconnue de schema.org`);
      continue;
    }
    if (domaine.length && !domaine.some((d) => permis.has(d)) && !estRole) {
      trouvees.push(`${chemin}/${cle} : hors du domaine de ${type}`);
    }
    for (const v of liste(valeur)) {
      if (v && typeof v === 'object') trouvees.push(...anomalies(vocabulaire, v, `${chemin}/${cle}`));
    }
  }
  return trouvees;
}
