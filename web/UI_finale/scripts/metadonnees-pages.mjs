/*
 * LE TITRE ET LA DESCRIPTION DE CHAQUE PAGE (#969, forme C).
 *
 * Arbitrés le 17/09/2026 sur maquette, entre trois formes, sur six pages
 * réelles : « l'élection en tête » — le nom et « présidentielle 2027 » dans le
 * titre, le contenu dans la description.
 *
 * LE TEXTE SUIT CE QUE LA FICHE CONTIENT, jamais un gabarit fixe : « mandats,
 * votes et textes » était faux pour 13 des 30 candidats déclarés publiés, qui
 * n'ont aucun vote dans les données (mesuré le 17/09/2026). Une donnée absente
 * n'est pas annoncée (§2 règle 5).
 *
 * Ce que ces textes ne portent JAMAIS : un nombre de votes, qui se lirait comme
 * une assiduité (§2 règle 3) ; un accord de genre (« candidature », pas
 * « candidat ») ; une position déclarée (§2 règle 8).
 */

export const MARQUE = 'Empreinte politique';
const SOURCE = 'Chaque fait renvoie à sa source officielle, sans note ni classement.';

/* Les institutions, dans l'ordre où la fiche les présente. */
export const PREPOSITION = { AN: "à l'Assemblée nationale", Senat: 'au Sénat', PE: 'au Parlement européen' };

/* Pages fixes : le titre est celui que la page affiche. Seule la méthode a une
 * description propre ; les autres gardent celle du site. */
export const PAGES_FIXES_META = {
  /* /a-propos porte une description propre, comme la méthode : c'est la page qui
     dit ce que le site est et qui l'édite (#1032), et l'aperçu d'un lien vers
     elle ne doit pas être celui du site entier. */
  'a-propos': {
    titre: `À propos — ${MARQUE}`,
    description:
      "Ce que ce site fait, et qui l'édite : un projet indépendant qui publie ce que les institutions publient, collecté par un programme, sans note ni classement.",
  },
  methodologie: {
    titre: `Méthode éditoriale — ${MARQUE}`,
    description: "Ce que le site publie, ce qu'il refuse de publier, et pourquoi : des faits sourcés, sans note ni classement.",
  },
  sources: { titre: `Sources — ${MARQUE}` },
  faq: { titre: `Questions fréquentes — ${MARQUE}` },
  'mentions-legales': { titre: `Mentions légales — ${MARQUE}` },
};

function enumerer(elements) {
  if (elements.length <= 1) return elements.join('');
  return `${elements.slice(0, -1).join(', ')} et ${elements.at(-1)}`;
}

function annee(date) {
  return typeof date === 'string' && /^\d{4}/.test(date) ? date.slice(0, 4) : null;
}

/* Valeurs de `KNOWN_CHAMBRES` (`src/schema_pivot.py`) qui ne sont pas une
 * assemblée : la description dit « mandats », sans nommer de lieu. Un test
 * échoue si le schéma gagne une valeur que ce module ne connaît pas. */
export const CHAMBRES_SANS_LIBELLE = ['mairie'];

export function metaCandidat(entree, profil) {
  const chambres = (profil.chambres || []).filter((c) => c in PREPOSITION);
  const inconnues = (profil.chambres || []).filter((c) => !(c in PREPOSITION) && !CHAMBRES_SANS_LIBELLE.includes(c));
  if (inconnues.length) throw new Error(`${entree.slug} : chambre sans libellé — ${inconnues.join(', ')}`);

  const mandats = profil.mandats || [];
  const contenus = [];
  if (mandats.length) {
    const locauxSeuls = !chambres.length && mandats.some((m) => m.categorie === 'mandat_local');
    contenus.push(locauxSeuls ? 'mandats locaux' : 'mandats');
  }
  if ((profil.votes || []).length) contenus.push('votes');
  if ((profil.textes_portes || []).length) contenus.push('textes');

  let quoi = enumerer(contenus);
  if (quoi && chambres.length) quoi += ` ${enumerer(chambres.map((c) => PREPOSITION[c]))}`;
  quoi = quoi ? quoi[0].toUpperCase() + quoi.slice(1) : '';

  const tete = [quoi, entree.parti].filter(Boolean).join(' · ');
  /* « Debout ! » : pas de point après une ponctuation finale. */
  const phrase = tete && !/[.!?]$/.test(tete) ? `${tete}.` : tete;
  return {
    titre: `${entree.nom}, présidentielle 2027 — parcours politique sourcé`,
    description: phrase ? `${phrase} ${SOURCE}` : SOURCE,
  };
}

/* `lignee` : la projection de `dist/data/lignees/<id>.json` (id, nom, chambre, periode). */
export function metaLignee(lignee) {
  const ou = PREPOSITION[lignee.chambre];
  if (!ou) throw new Error(`${lignee.id} : chambre sans libellé — ${lignee.chambre}`);
  const debut = annee(lignee.periode?.debut);
  const fin = annee(lignee.periode?.fin);
  let quand = null;
  if (debut && !lignee.periode?.fin) quand = `Depuis ${debut}.`;
  else if (debut && fin) quand = debut === fin ? `En ${debut}.` : `De ${debut} à ${fin}.`;
  return {
    titre: `Groupe ${lignee.nom} ${ou} — membres, votes, amendements`,
    description: [quand, SOURCE].filter(Boolean).join(' '),
  };
}

export function metaGouvernement(entree) {
  const debut = annee(entree.debut);
  const fin = annee(entree.fin);
  let quand = null;
  if (debut && entree.actif) quand = `depuis ${debut}`;
  else if (debut && fin) quand = debut === fin ? debut : `${debut}-${fin}`;
  return {
    titre: `${entree.nom}${quand ? ` (${quand})` : ''} — membres et textes`,
    description: SOURCE,
  };
}

function attribut(texte) {
  return texte.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

/* Chaque balise est REMPLACÉE, jamais ajoutée : un `index.html` qui perd l'une
 * d'elles fait échouer le build plutôt que de publier deux titres. */
const BALISES = [
  [/<title>[^<]*<\/title>/, (m) => `<title>${attribut(m.titre)}</title>`],
  [/<meta name="description" content="[^"]*" \/>/, (m) => `<meta name="description" content="${attribut(m.description)}" />`],
  [/<meta property="og:url" content="[^"]*" \/>/, (m) => `<meta property="og:url" content="${attribut(m.url)}" />`],
  [/<meta property="og:title" content="[^"]*" \/>/, (m) => `<meta property="og:title" content="${attribut(m.titre)}" />`],
  [/<meta property="og:description" content="[^"]*" \/>/, (m) => `<meta property="og:description" content="${attribut(m.description)}" />`],
  [/<meta name="twitter:title" content="[^"]*" \/>/, (m) => `<meta name="twitter:title" content="${attribut(m.titre)}" />`],
  [/<meta name="twitter:description" content="[^"]*" \/>/, (m) => `<meta name="twitter:description" content="${attribut(m.description)}" />`],
];

/* `meta.description` absente : celle du gabarit reste. */
export function appliquerMeta(gabarit, meta) {
  let html = gabarit;
  for (const [motif, balise] of BALISES) {
    const trouvees = html.match(new RegExp(motif.source, 'g')) || [];
    if (trouvees.length !== 1) throw new Error(`index.html porte ${trouvees.length} fois ${motif.source} — attendu 1`);
    if (motif.source.includes('description') && !meta.description) continue;
    html = html.replace(motif, balise(meta));
  }
  return html.replace('</head>', `  <link rel="canonical" href="${attribut(meta.url)}" />\n  </head>`);
}
