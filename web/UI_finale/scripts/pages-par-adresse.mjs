/*
 * UN FICHIER PAR ADRESSE PUBLIÉE, POUR QU'ELLE RÉPONDE 200 (#969).
 *
 * `spa-fallback.mjs` (#756) fait démarrer l'application sur tout lien profond,
 * mais par `404.html` : le lecteur voit la page, un moteur de recherche voit
 * une erreur et n'indexe rien. Mesuré en production le 17/09/2026 : `/`
 * répondait 200, `/sources`, `/faq`, `/candidats/jean-luc-melenchon`… 404.
 *
 * GitHub Pages n'a pas de règle de réécriture, mais il sert un FICHIER RÉEL
 * en 200. Ce script écrit donc, dans `dist/`, une copie de `index.html` par
 * adresse que l'interface publie. L'application y démarre exactement comme
 * depuis la racine.
 *
 * `<adresse>.html`, JAMAIS `<adresse>/index.html` : Pages sert `x.html` à
 * l'adresse `/x` en 200, alors qu'un dossier `x/` répond 301 vers `/x/` — une
 * redirection sur chaque fiche, et une seconde forme d'adresse. Relevé sur un
 * site Pages le 17/09/2026.
 *
 * CE QUI EST PUBLIÉ se lit dans `dist/data/manifest.json`, jamais en dur : les
 * candidats du manifeste (les déclinées en sont déjà exclues, #761), les
 * lignées de groupe, les gouvernements. Une fiche absente du manifeste n'a pas
 * de fichier : elle garde le repli 404, qui est le bon statut pour elle.
 *
 * LES ADRESSES QUI REDIRIGENT (`/candidats`, `/couverture`, une ancienne fiche
 * de législature `/groupes/AN-SOC-17`…) reçoivent aussi leur fichier, avec une
 * balise `canonical` vers l'adresse d'arrivée : un lien déjà partagé répond
 * 200 et désigne la page à indexer, sans que la même fiche soit indexée deux
 * fois. L'application fait la redirection elle-même, ancre comprise.
 *
 * CHAQUE PAGE PORTE SON TITRE ET SA DESCRIPTION, balises `og:` et `twitter:`
 * comprises, et une balise `canonical` vers sa propre adresse (une recherche
 * `?mot=` n'est pas une autre page). Le texte vit dans `metadonnees-pages.mjs`.
 *
 * Le script ÉCHOUE plutôt que d'omettre en silence : un identifiant qu'on ne
 * peut pas écrire en nom de fichier, une redirection vers une page qui
 * n'existe pas, une collision de noms.
 */
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  DEFAULT_CANDIDATE_ID,
  DEFAULT_GOVERNMENT_ID,
  DEFAULT_GROUP_ID,
} from '../src/data/adressesParDefaut.js';
import {
  PAGES_FIXES_META,
  appliquerMeta,
  metaCandidat,
  metaGouvernement,
  metaLignee,
} from './metadonnees-pages.mjs';
import { avecBloc, blocCandidat, blocGouvernement, blocLignee } from './bloc-sans-js.mjs';
import { robots, sitemap } from './sitemap-et-robots.mjs';
import {
  baliseJsonld,
  jsonldAccueil,
  jsonldCandidat,
  jsonldGouvernement,
  jsonldLignee,
} from './donnees-structurees.mjs';

const racineUI = dirname(dirname(fileURLToPath(import.meta.url)));
const dist = join(racineUI, 'dist');

function echouer(message) {
  console.error(`pages-par-adresse : ${message}`);
  process.exit(1);
}

/* Les pages fixes de `src/App.jsx`. Recopiées ici faute de pouvoir lire du
 * JSX sous Node : `tests/test_pages_par_adresse_969.py` échoue si une route
 * de l'application manque à cette liste. */
export const PAGES_FIXES = ['a-propos', 'methodologie', 'sources', 'faq', 'mentions-legales'];

/* Les redirections de `src/App.jsx`, adresse → adresse d'arrivée. */
export const REDIRECTIONS_FIXES = {
  candidats: `candidats/${DEFAULT_CANDIDATE_ID}`,
  groupes: `groupes/${DEFAULT_GROUP_ID}`,
  gouvernements: `gouvernements/${DEFAULT_GOVERNMENT_ID}`,
  couverture: 'sources',
};

const SEGMENT_SUR = /^[A-Za-z0-9][A-Za-z0-9._-]*$/;

function adresse(prefixe, id, origine) {
  if (typeof id !== 'string' || !SEGMENT_SUR.test(id)) {
    echouer(`identifiant ${JSON.stringify(id)} (${origine}) inutilisable comme nom de fichier — aucune page écrite.`);
  }
  return `${prefixe}/${id}`;
}

if (!existsSync(join(dist, 'index.html'))) echouer('dist/index.html est introuvable — le build a-t-il tourné ?');
const cheminManifeste = join(dist, 'data', 'manifest.json');
if (!existsSync(cheminManifeste)) echouer('dist/data/manifest.json est introuvable — sync-data a-t-il tourné ?');

const gabarit = readFileSync(join(dist, 'index.html'), 'utf-8');
const manifeste = JSON.parse(readFileSync(cheminManifeste, 'utf-8'));
const domaine = readFileSync(join(racineUI, 'public', 'CNAME'), 'utf-8').trim();
if (!gabarit.includes('</head>')) echouer('dist/index.html ne porte pas de </head>.');

const pages = {
  fixes: PAGES_FIXES,
  candidats: (manifeste.candidates || []).map((c) => adresse('candidats', c.slug, 'manifest.candidates')),
  groupes: (manifeste.lignees || []).map((l) => adresse('groupes', l.id, 'manifest.lignees')),
  gouvernements: (manifeste.gouvernements || []).map((g) => adresse('gouvernements', g.id, 'manifest.gouvernements')),
};
const publiees = new Set(Object.values(pages).flat());

/* Une fiche de législature d'avant #329 mène à sa lignée (GroupProfilePage). */
const redirections = { ...REDIRECTIONS_FIXES };
for (const g of manifeste.groupes || []) {
  if (!g.lignee) continue;
  const depuis = adresse('groupes', g.id, 'manifest.groupes');
  if (!publiees.has(depuis)) redirections[depuis] = `groupes/${g.lignee}`;
}

for (const [depuis, vers] of Object.entries(redirections)) {
  if (publiees.has(depuis)) echouer(`« /${depuis} » est à la fois une page et une redirection.`);
  if (!publiees.has(vers)) echouer(`« /${depuis} » redirige vers « /${vers} », qui n'est pas une page publiée.`);
}

function ecrire(chemin, contenu) {
  const cible = join(dist, `${chemin}.html`);
  if (existsSync(cible)) echouer(`dist/${chemin}.html existe déjà — collision avec un fichier du build.`);
  mkdirSync(dirname(cible), { recursive: true });
  writeFileSync(cible, contenu);
}

const cles = Object.keys(PAGES_FIXES_META).sort().join(', ');
if (cles !== [...PAGES_FIXES].sort().join(', ')) echouer(`les pages fixes n'ont pas toutes leur titre : ${cles}`);

/* Adresse → { titre, description } et, pour une fiche, le texte lisible sans
 * JavaScript (#969). Une erreur de texte arrête le build. */
const metas = new Map();
const blocs = new Map();
/* Adresse → balisage Schema.org (#1008). */
const jsonld = new Map();
/* Adresse → date de la donnée, pour le `lastmod` du sitemap. */
const datesDesDonnees = new Map();
const dateDuBuild = new Date().toISOString().slice(0, 10);
try {
  for (const chemin of PAGES_FIXES) metas.set(chemin, PAGES_FIXES_META[chemin]);
  for (const c of manifeste.candidates || []) {
    const profil = JSON.parse(readFileSync(join(dist, 'data', 'profiles', `${c.slug}.pivot.json`), 'utf-8'));
    metas.set(`candidats/${c.slug}`, metaCandidat(c, profil));
    blocs.set(`candidats/${c.slug}`, blocCandidat(c, profil, dateDuBuild));
    datesDesDonnees.set(`candidats/${c.slug}`, profil.meta?.genere_le || null);
    jsonld.set(`candidats/${c.slug}`, jsonldCandidat(c, profil, `https://${domaine}/candidats/${c.slug}`));
  }
  /* La période n'est pas au manifeste : elle se lit dans la vue de lignée. */
  for (const l of manifeste.lignees || []) {
    const vue = JSON.parse(readFileSync(join(dist, 'data', 'lignees', l.fichier), 'utf-8'));
    metas.set(`groupes/${l.id}`, metaLignee(vue));
    blocs.set(`groupes/${l.id}`, blocLignee(vue, dateDuBuild));
    datesDesDonnees.set(`groupes/${l.id}`, vue.genereLe || null);
    jsonld.set(`groupes/${l.id}`, jsonldLignee(vue, `https://${domaine}/groupes/${l.id}`));
  }
  for (const g of manifeste.gouvernements || []) {
    metas.set(`gouvernements/${g.id}`, metaGouvernement(g));
    const profil = JSON.parse(readFileSync(join(dist, 'data', 'gouvernements', g.fichier), 'utf-8'));
    blocs.set(`gouvernements/${g.id}`, blocGouvernement(profil, dateDuBuild));
    datesDesDonnees.set(`gouvernements/${g.id}`, profil.meta?.genere_le || null);
    jsonld.set(`gouvernements/${g.id}`, jsonldGouvernement(profil, `https://${domaine}/gouvernements/${g.id}`));
  }
} catch (erreur) {
  echouer(`texte d'une page impossible à écrire — ${erreur.message}`);
}

/* Le balisage vit dans le `<head>`, où les robots le lisent sans rendre la page. */
function avecJsonld(page, objet) {
  return page.replace('</head>', `  ${baliseJsonld(objet)}\n  </head>`);
}

/* L'accueil garde son texte (celui d'`index.html`) et reçoit sa canonical ici,
 * APRÈS la copie vers `404.html` : une page introuvable ne désigne pas l'accueil. */
const accueil = gabarit.replace('</head>', `  <link rel="canonical" href="https://${domaine}/" />\n  </head>`);
const descriptionDuSite = (gabarit.match(/<meta name="description" content="([^"]*)"/) || [])[1] || '';
writeFileSync(join(dist, 'index.html'), avecJsonld(accueil, jsonldAccueil(domaine, descriptionDuSite)));

for (const chemin of publiees) {
  try {
    let page = appliquerMeta(gabarit, { ...metas.get(chemin), url: `https://${domaine}/${chemin}` });
    if (jsonld.has(chemin)) page = avecJsonld(page, jsonld.get(chemin));
    ecrire(chemin, blocs.has(chemin) ? avecBloc(page, blocs.get(chemin)) : page);
  } catch (erreur) {
    echouer(`${chemin} : ${erreur.message}`);
  }
}
for (const [depuis, vers] of Object.entries(redirections)) {
  ecrire(depuis, gabarit.replace('</head>', `  <link rel="canonical" href="https://${domaine}/${vers}" />\n  </head>`));
}

/* Le sitemap ne liste QUE les pages publiées, jamais les redirections (#969). */
const entrees = [{ chemin: '', lastmod: dateDuBuild }]
  .concat([...publiees].map((chemin) => ({ chemin, lastmod: datesDesDonnees.get(chemin) || dateDuBuild })));
writeFileSync(join(dist, 'sitemap.xml'), sitemap(domaine, entrees));
writeFileSync(join(dist, 'robots.txt'), robots(domaine));

console.log(
  `pages-par-adresse : ${publiees.size + 1} pages publiées répondent 200 — l'accueil, `
  + `${pages.fixes.length} pages fixes, ${pages.candidats.length} fiches candidat (candidats du manifeste), `
  + `${pages.groupes.length} fiches de lignée, ${pages.gouvernements.length} fiches de gouvernement ; `
  + `${Object.keys(redirections).length} adresses de redirection, canonical vers leur arrivée ; `
  + `${blocs.size} fiches portent leurs faits en clair, lisibles sans JavaScript ; `
  + `sitemap.xml en liste ${entrees.length}, robots.txt le désigne ; `
  + `${jsonld.size + 1} pages portent leur balisage Schema.org.`,
);
