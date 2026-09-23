/*
 * LE BANDEAU ET LE PIED DU SITE, SUR LES PAGES STATIQUES (#1029).
 *
 * Un instantané est une page statique de `public/rapports/` : GitHub Pages la
 * sert telle quelle, l'application React ne la route pas. Elle portait donc un
 * bandeau à elle — la marque en gras et deux liens — et, pour l'instantané du
 * 23/09, aucun pied. Un lecteur qui arrive par un lien LinkedIn tombait sur une
 * page qui ne ressemblait pas au site, sans le contact, sans les mentions
 * légales et sans le bandeau « en construction » que toutes les autres pages
 * portent.
 *
 * LE MARKUP EST RECOPIÉ, LE STYLE EST RECOPIÉ, ET C'EST LE DÉFAUT DU PROCÉDÉ :
 * `EnTeteSite.jsx`, `NavigationSite.jsx` et `PiedDeSite.jsx` sont du JSX, ils ne
 * s'exécutent pas hors de l'application. Deux gardes tiennent la copie :
 * `tests/test_chrome_instantanes_1029.py` compare les entrées de la barre, les
 * liens du pied, l'adresse de contact et la baseline avec leurs définitions
 * React, et `test_rapports_publies.py` refuse une page dont le chrome a dérivé
 * de ce fichier. Une entrée ajoutée à la barre du site fait donc rougir la
 * suite tant qu'elle n'est pas ici.
 *
 * LE CHROME SUIT LE SITE, LE CONTENU RESTE GELÉ. « Un instantané n'est jamais
 * mis à jour » vaut pour ses faits, pas pour le menu qui l'entoure : un lien
 * mort dans le pied d'une page de septembre ne rend pas cette page plus fidèle.
 * Le chrome vit donc entre des marqueurs (`<!--chrome:…-->`), et
 * `node scripts/index-rapports.mjs` le réécrit dans toutes les pages du
 * dossier.
 *
 * LE MENU ÉTROIT EST UN `<details>`, pas un bouton : sous 720 px la barre du
 * site replie ses liens derrière « Menu », et une page statique n'a pas de
 * React pour tenir cet état. `<details>` le tient sans une ligne de script.
 *
 * LES LIENS SONT ABSOLUS. La page est faite pour être partagée, et elle se
 * relit parfois hors du site — depuis le dépôt, depuis une copie. Un lien
 * racine y mènerait au disque.
 */

/** L'origine du site publié. Les pages statiques n'ont pas de base relative. */
export const SITE = 'https://empreinte-politique.fr';

/** Les pages de la barre, dans l'ordre de `NavigationSite.jsx`. */
export const PAGES = [
  { libelle: 'Explorateur', vers: '/candidats' },
  { libelle: 'Méthodologie', vers: '/methodologie' },
  { libelle: 'Sources', vers: '/sources' },
  { libelle: 'Articles', vers: '/rapports' },
  { libelle: 'FAQ', vers: '/faq' },
];

/** La colonne « Le site » du pied, dans l'ordre de `PiedDeSite.jsx`. */
export const PIED_PAGES = [
  { libelle: 'À propos', vers: '/a-propos' },
  { libelle: 'Sources', vers: '/sources' },
  { libelle: 'Méthodologie', vers: '/methodologie' },
  { libelle: 'Mentions légales', vers: '/mentions-legales' },
];

export const CONTACT = 'contact@empreinte-politique.fr';
export const LINKEDIN = 'https://www.linkedin.com/company/empreinte-politique';
export const X_COMPTE = 'https://x.com/EmpreintePol';

/** Les quatre mentions de `Baseline.jsx`. L'espace avant le % est insécable. */
export const BASELINE = ['100\u00a0% automatisé', '100\u00a0% sourcé', '0 score', '0 filtre'];

/* Le filigrane de `shell.css`, recopié tel quel : seize ellipses concentriques
   posées en bas à gauche, à 5,5 % d'opacité. */
const FILIGRANE = "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='1600' height='1000'%3E%3Cg fill='none' stroke='rgb(20,21,26)' stroke-width='1.5' opacity='0.055'%3E%3Cellipse cx='150' cy='1000' rx='100' ry='92'/%3E%3Cellipse cx='150' cy='1000' rx='200' ry='184'/%3E%3Cellipse cx='150' cy='1000' rx='300' ry='276'/%3E%3Cellipse cx='150' cy='1000' rx='400' ry='368'/%3E%3Cellipse cx='150' cy='1000' rx='500' ry='460'/%3E%3Cellipse cx='150' cy='1000' rx='600' ry='552'/%3E%3Cellipse cx='150' cy='1000' rx='700' ry='644'/%3E%3Cellipse cx='150' cy='1000' rx='800' ry='736'/%3E%3Cellipse cx='150' cy='1000' rx='900' ry='828'/%3E%3Cellipse cx='150' cy='1000' rx='1000' ry='920'/%3E%3Cellipse cx='150' cy='1000' rx='1100' ry='1012'/%3E%3Cellipse cx='150' cy='1000' rx='1200' ry='1104'/%3E%3Cellipse cx='150' cy='1000' rx='1300' ry='1196'/%3E%3Cellipse cx='150' cy='1000' rx='1400' ry='1288'/%3E%3Cellipse cx='150' cy='1000' rx='1500' ry='1380'/%3E%3Cellipse cx='150' cy='1000' rx='1600' ry='1472'/%3E%3C/g%3E%3C/svg%3E\")";

/* Les valeurs viennent de ConstructionBanner.css, Brand.css, EnTeteSite.css,
   NavigationSite.css, PiedDeSite.css et Baseline.css. Trois écarts, tous dus au
   fait qu'il n'y a pas de React ici :
   — le menu étroit est un `<details>`, donc son `summary` remplace le bouton ;
   — le pied prend `--faible` là où le site prend `--muted` : c'est la même
     valeur (#8b8794), les pages d'instantané nomment ce gris autrement ;
   — le bouton du menu prend `--border-fort`, le `--border-strong` du site. */
export const STYLE_CHROME = `
:root { --notice:#00e5ff; }
body {
  background-color: var(--bg);
  background-image: ${FILIGRANE};
  background-repeat: no-repeat;
  background-size: cover;
  background-position: left bottom;
}
.construction-banner { display:flex; flex-wrap:wrap; align-items:baseline; justify-content:center; gap:0.5rem 1rem; padding:0.875rem 1.25rem; background:var(--notice); color:#17141f; font-size:0.9375rem; line-height:1.45; text-align:center; }
.construction-banner__text { margin:0; max-width:78ch; }
.construction-banner__link { color:#17141f; font-weight:600; text-underline-offset:0.25em; white-space:nowrap; }
.construction-banner__link:hover, .construction-banner__link:focus-visible { text-decoration-thickness:2px; }
@media (max-width:34rem) { .construction-banner { text-align:left; justify-content:flex-start; } }

.entete-site { --entete-hauteur:80px; position:sticky; top:0; z-index:5; height:var(--entete-hauteur); display:flex; align-items:center; gap:16px; padding-right:40px; background:var(--bg); border-bottom:1px solid var(--border); }
.entete-site-actions { margin-left:auto; display:flex; align-items:center; gap:22px; }
.brand { display:flex; align-items:center; padding-inline:40px; height:80px; text-decoration:none; transition:opacity 0.15s; flex:none; }
.brand:hover, .brand:focus-visible { opacity:0.75; }
.brand-lockup { display:block; height:58px; width:auto; }
.brand-symbol { display:none; height:40px; width:40px; }

.nav-site { display:flex; align-items:center; gap:22px; }
.nav-site-lien { font-size:13px; font-weight:600; color:var(--faible); text-decoration:none; padding:4px 0; white-space:nowrap; }
.nav-site-lien:hover { color:var(--ink); }
.nav-site-lien--courante { color:var(--ink); font-weight:800; box-shadow:inset 0 -3px 0 var(--accent); }
.nav-site-lien:focus-visible, .nav-site-menu-lien:focus-visible, .nav-site-menu-bouton:focus-visible { outline:2px solid var(--ink); outline-offset:2px; }
.nav-site-menu { position:relative; display:none; }
.nav-site-menu-bouton { display:inline-flex; align-items:center; gap:8px; font:inherit; font-size:12.5px; font-weight:600; border:1px solid var(--border-fort); background:var(--card); color:var(--ink); border-radius:999px; padding:5px 12px; cursor:pointer; white-space:nowrap; list-style:none; }
.nav-site-menu-bouton::-webkit-details-marker { display:none; }
.nav-site-menu-bouton:hover { border-color:var(--faible); }
.nav-site-menu-icone { position:relative; width:13px; height:9px; border-top:2px solid currentColor; border-bottom:2px solid currentColor; box-sizing:border-box; }
.nav-site-menu-icone::after { content:''; position:absolute; left:0; right:0; top:1.5px; border-top:2px solid currentColor; }
.nav-site-menu-liste { position:absolute; right:0; top:calc(100% + 8px); z-index:10; min-width:200px; display:flex; flex-direction:column; padding:8px; background:var(--card); border:1px solid var(--border); border-radius:14px; box-shadow:0 10px 30px rgba(23,20,31,0.14); }
.nav-site-menu-lien { padding:10px 12px; border-radius:10px; font-size:14px; font-weight:700; color:var(--ink); text-decoration:none; }
.nav-site-menu-lien:hover { background:var(--bg); }
.nav-site-menu-lien--courante, .nav-site-menu-lien--courante:hover { background:var(--accent); color:#17141f; }
@media (max-width:720px) {
  .entete-site { padding-right:16px; gap:8px; }
  .entete-site-actions { gap:8px; }
  .nav-site { display:none; }
  .nav-site-menu { display:block; }
}
@media (max-width:480px) {
  .entete-site { --entete-hauteur:56px; }
  .brand { height:56px; padding-inline:16px; }
  .brand-lockup { display:none; }
  .brand-symbol { display:block; }
}

.pds { display:grid; line-height:1.4; grid-template-columns:1.4fr 1fr auto; gap:26px 40px; align-items:start; width:100%; max-width:1600px; margin:0 auto; padding:26px 40px 30px; border-top:1px solid var(--border); font-size:13px; color:var(--faible); }
.pds-marque { line-height:1.55; }
.pds-marque b { display:block; font-size:13px; font-weight:800; letter-spacing:0.06em; text-transform:uppercase; color:var(--ink); margin-bottom:6px; }
.pds-colonne { display:flex; flex-direction:column; align-items:flex-start; gap:7px; }
.pds-titre { font-size:10.5px; font-weight:800; letter-spacing:0.11em; text-transform:uppercase; color:#b6b1bd; margin-bottom:2px; }
.pds a { color:var(--faible); text-decoration:none; }
.pds a:hover, .pds a:focus-visible { color:var(--ink); text-decoration:underline; }
.pds a:focus-visible { outline:2px solid var(--ink); outline-offset:3px; border-radius:2px; }
.pds-comptes { display:flex; gap:4px; margin-top:1px; }
.pds-icone { display:inline-flex; align-items:center; justify-content:center; width:30px; height:30px; border-radius:4px; transition:background 0.12s ease, color 0.12s ease; }
.pds-icone svg { width:16px; height:16px; display:block; }
.pds-icone:hover, .pds-icone:focus-visible { background:#f2f0ed; color:var(--ink); text-decoration:none; }
.pds-icone:focus-visible { outline-offset:1px; }
.baseline { margin:0; display:flex; flex-wrap:wrap; font-variant-numeric:tabular-nums; }
.baseline-mention { white-space:nowrap; }
.baseline-puce { padding:0 6px; color:var(--faible); }
.baseline--pied { font-size:13px; font-weight:600; color:var(--faible); }
@media (max-width:760px) { .pds { grid-template-columns:1fr; gap:22px; padding:24px 20px 28px; } }
@media (prefers-reduced-motion:reduce) { .pds-icone { transition:none; } }
`.trim();

const lien = (page, classe, courante) =>
  `<a href="${SITE}${page.vers}" class="${classe}${page.vers === courante ? ` ${classe}--courante` : ''}"${
    page.vers === courante ? ' aria-current="page"' : ''
  }>${page.libelle}</a>`;

/**
 * Le bandeau : l'avis « en construction », puis la rangée du logo et la barre
 * des pages. `courante` est l'adresse de la page rendue (`/rapports` sur
 * l'index), soulignée de jaune comme dans l'application.
 */
export function bandeau(courante = null) {
  const barre = PAGES.map((p) => lien(p, 'nav-site-lien', courante)).join('\n      ');
  const menu = PAGES.map((p) => lien(p, 'nav-site-menu-lien', courante)).join('\n      ');
  return `<aside class="construction-banner" role="note" aria-label="État du projet">
  <p class="construction-banner__text"><strong>En construction.</strong> Ce site est publié pendant son développement. Ce qui s'affiche est sourcé et vérifiable, mais des données peuvent manquer, et certaines absences sont encore mal expliquées.</p>
  <a class="construction-banner__link" href="${SITE}/methodologie">Méthodologie</a>
</aside>
<header class="entete-site">
  <a class="brand" href="${SITE}/" aria-label="Empreinte politique — retour à l'accueil">
    <img src="${SITE}/brand/empreinte-lockup-light.svg" alt="" class="brand-lockup">
    <img src="${SITE}/brand/empreinte-symbol-light.svg" alt="" class="brand-symbol">
  </a>
  <div class="entete-site-actions">
    <nav class="nav-site" aria-label="Pages du site">
      ${barre}
    </nav>
    <details class="nav-site-menu">
      <summary class="nav-site-menu-bouton"><span class="nav-site-menu-icone" aria-hidden="true"></span>Menu</summary>
      <nav class="nav-site-menu-liste" aria-label="Pages du site">
      ${menu}
      </nav>
    </details>
  </div>
</header>`;
}

/** Le pied du site : la marque et sa baseline, les pages, le contact. */
export function piedDeSite() {
  const mentions = BASELINE.map(
    (m, i) => `<span class="baseline-mention">${i > 0 ? '<span aria-hidden="true" class="baseline-puce">•</span>' : ''}${m}</span>`,
  ).join('');
  const pages = PIED_PAGES.map((p) => `    <a href="${SITE}${p.vers}">${p.libelle}</a>`).join('\n');
  return `<footer class="pds">
  <div class="pds-marque">
    <b>Empreinte politique</b>
    <p class="baseline baseline--pied">${mentions}</p>
  </div>
  <nav class="pds-colonne" aria-label="Pages du site">
    <span class="pds-titre">Le site</span>
${pages}
  </nav>
  <div class="pds-colonne">
    <span class="pds-titre">Nous joindre</span>
    <a href="mailto:${CONTACT}">${CONTACT}</a>
    <div class="pds-comptes">
      <a class="pds-icone" href="${LINKEDIN}" target="_blank" rel="noopener noreferrer" aria-label="Empreinte politique sur LinkedIn"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false"><path d="M4.98 3.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5ZM3 9.5h4v11H3v-11Zm6.5 0h3.8v1.5h.05c.53-.95 1.83-1.95 3.77-1.95 4.03 0 4.78 2.5 4.78 5.76v5.69h-4v-5.05c0-1.2-.02-2.75-1.7-2.75-1.7 0-1.96 1.31-1.96 2.66v5.14h-4v-11Z"/></svg></a>
      <a class="pds-icone" href="${X_COMPTE}" target="_blank" rel="noopener noreferrer" aria-label="Empreinte politique sur X"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false"><path d="M17.6 3h3.1l-6.77 7.74L22 21h-6.2l-4.86-6.35L5.37 21H2.26l7.24-8.28L2 3h6.36l4.4 5.82L17.6 3Zm-1.09 16.1h1.72L7.57 4.8H5.72l10.79 14.3Z"/></svg></a>
    </div>
  </div>
</footer>`;
}

/* Les trois blocs réécrits dans une page. Le style est rendu en dernier dans le
   `<style>` de la page, pour que le chrome ne dépende pas de l'ordre des
   règles du contenu. */
const BLOCS = {
  style: () => STYLE_CHROME,
  bandeau: (courante) => bandeau(courante),
  pied: () => piedDeSite(),
};

/* Le bloc de style vit DANS le `<style>` de la page, donc ses marqueurs sont
   des commentaires CSS et non des commentaires HTML : `<!--chrome:style-->`
   placé là est lu par le moteur CSS comme un sélecteur, qui avale la règle
   suivante — le bandeau « en construction » a perdu son cyan de cette façon. */
const marqueurs = (nom) =>
  nom === 'style'
    ? [`/*chrome:${nom}*/`, `/*/chrome:${nom}*/`]
    : [`<!--chrome:${nom}-->`, `<!--/chrome:${nom}-->`];

/**
 * Réécrit les trois blocs de chrome d'une page entre leurs marqueurs. Une page
 * qui n'en porte pas est refusée : un instantané sans bandeau ni pied n'est pas
 * une page du site.
 */
export function appliquerLeChrome(html, { courante = null } = {}) {
  let sortie = html;
  for (const [nom, rendu] of Object.entries(BLOCS)) {
    const [ouvre, ferme] = marqueurs(nom);
    const debut = sortie.indexOf(ouvre);
    const fin = sortie.indexOf(ferme);
    if (debut === -1 || fin === -1 || fin < debut) {
      throw new Error(`marqueurs ${ouvre} … ${ferme} absents : la page ne porte pas le chrome du site`);
    }
    sortie = `${sortie.slice(0, debut + ouvre.length)}\n${rendu(courante)}\n${sortie.slice(fin)}`;
  }
  return sortie;
}
