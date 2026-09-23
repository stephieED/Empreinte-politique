/*
 * L'INDEX DES ARTICLES, CONSTRUIT DEPUIS LE DOSSIER (#1029).
 *
 * Un article est une page STATIQUE de `public/rapports/`, servie telle
 * quelle par GitHub Pages : son adresse répond 200 sans dépendre du repli de
 * routage, et elle ne bouge plus une fois partagée.
 *
 * L'index, lui, était écrit à la main — et un index écrit à la main oublie un
 * fichier le jour où on est pressé. Il se construit donc ICI, en lisant le
 * dossier : le nom du fichier donne la date des DONNÉES, son `<title>` le
 * sujet, sa `<meta name="description">` la phrase de présentation, sa
 * `<meta name="article:periode">` la période couverte et sa
 * `<meta name="article:type">` son type — « Instantané » pour ceux qui
 * mesurent un instant. LE TYPE N'EST PAS DEVINÉ : une page qui n'en déclare
 * pas n'en affiche pas (§2 règle 5), parce que d'autres types viendront.
 *
 * Écrit dans `public/`, pas dans `dist/` : la page est donc servie en
 * développement comme en production, et sa version committée se relit dans la
 * revue. `tests/test_rapports_publies.py` refuse une version périmée.
 */
import { readdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { SITE, STYLE_CHROME, appliquerLeChrome, bandeau, piedDeSite } from './chrome-instantane.mjs';

const ici = path.dirname(fileURLToPath(import.meta.url));
const racine = path.resolve(ici, '..');
export const DOSSIER = path.join(racine, 'public', 'rapports');
export const INDEX = path.join(racine, 'public', 'rapports.html');

const MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'];
const enClair = (iso) => `${Number(iso.slice(8, 10))} ${MOIS[Number(iso.slice(5, 7)) - 1]} ${iso.slice(0, 4)}`;
const lire = (source, motif) => (source.match(motif) || [null, null])[1];

/** Les instantanés du dossier, du plus récent au plus ancien. */
export function instantanes(dossier = DOSSIER) {
  return readdirSync(dossier)
    .filter((f) => /^\d{4}-\d{2}-\d{2}-[a-z0-9-]+\.html$/.test(f))
    .sort()
    .reverse()
    .map((fichier) => {
      const source = readFileSync(path.join(dossier, fichier), 'utf-8');
      const titre = (lire(source, /<title>(.*?)<\/title>/s) || '').split('·')[0].split('—')[0].trim();
      if (!titre) throw new Error(`${fichier} n'a pas de <title> lisible.`);
      const description = lire(source, /<meta name="description" content="(.*?)">/s);
      if (!description) throw new Error(`${fichier} n'a pas de <meta name="description">.`);
      const periode = lire(source, /<meta name="article:periode" content="(.*?)">/s);
      const type = lire(source, /<meta name="article:type" content="(.*?)">/s);
      return { fichier, titre, description, periode, type, date: fichier.slice(0, 10) };
    });
}

const echappe = (t) => t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

export function page(liste) {
  const lignes = liste.map((i) => `      <li>
        <a href="/rapports/${i.fichier}">${echappe(i.titre)}</a>
        <span class="quand">${i.type ? `${echappe(i.type)} · d` : 'D'}onnées au ${enClair(i.date)}${i.periode ? ` · ${echappe(i.periode)}` : ''}</span>
        <p>${echappe(i.description)}</p>
      </li>`).join('\n');
  return `<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Les articles · Empreinte politique</title>
<meta name="description" content="Les articles d'Empreinte politique : ce que les fiches du site disent d'un sujet, à une date donnée, chaque fait lié à sa source.">
<link rel="canonical" href="${SITE}/rapports">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap">
<style>
:root {
  color-scheme: light;
  --bg:#f7f6f4; --card:#ffffff; --ink:#17141f; --muted:#6e6a78; --faible:#8b8794;
  --border:#eae7e2; --border-fort:#ddd9d2; --accent:#dfff00;
}
body { margin:0; background:var(--bg); color:var(--ink); font-family:Manrope,'Segoe UI',system-ui,sans-serif; font-size:16px; line-height:1.6; -webkit-font-smoothing:antialiased; }
.page { max-width:760px; margin:0 auto; padding-block:48px 64px; padding-inline:20px; display:flex; flex-direction:column; gap:32px; }
h1 { margin:0; font-size:clamp(30px,5vw,44px); font-weight:800; letter-spacing:-0.025em; line-height:1.08; text-wrap:balance; }
.eyebrow { margin:0; font-size:11.5px; font-weight:700; letter-spacing:0.11em; text-transform:uppercase; color:var(--faible); }
.chapeau { margin:0; font-size:17.5px; color:var(--muted); max-width:66ch; }
ul.liste { list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:14px; }
ul.liste li { background:var(--card); border:1px solid var(--border); border-radius:14px; padding:18px 20px; display:flex; flex-direction:column; gap:6px; }
ul.liste a { font-size:18px; font-weight:800; color:var(--ink); text-decoration:none; }
ul.liste a:hover { text-decoration:underline; }
ul.liste .quand { font-size:12.5px; color:var(--faible); font-variant-numeric:tabular-nums; }
ul.liste p { margin:0; font-size:14.5px; color:var(--muted); }
.note { margin:0; font-size:13.5px; color:var(--muted); }
.note a { color:inherit; }
/*chrome:style*/
${STYLE_CHROME}
/*/chrome:style*/
</style>
</head>
<body>
<!--chrome:bandeau-->
${bandeau('/rapports')}
<!--/chrome:bandeau-->
<div class="page">
  <div>
    <p class="eyebrow">Empreinte politique</p>
    <h1>Les articles</h1>
  </div>
  <p class="chapeau">Ce que les fiches du site disent d'un sujet, au jour des données qui l'ont produit. Chaque fait y est lié à sa source — un compte rendu de séance, un dossier législatif, un texte au Journal officiel.</p>
  <ul class="liste">
${lignes}
  </ul>
  <p class="note">Un instantané est un article qui mesure un instant : il dit l'état du corpus à sa date, et n'est jamais mis à jour. Un sujet repris plus tard donne un nouvel instantané, à une nouvelle adresse.</p>
  <p class="note">Données publiques de l'Assemblée nationale et du Journal officiel · <a href="/sources">Les sources</a> · <a href="/methodologie">La méthodologie</a></p>
</div>
<!--chrome:pied-->
${piedDeSite()}
<!--/chrome:pied-->
</body>
</html>
`;
}

/**
 * Réécrit le bandeau et le pied de chaque instantané depuis
 * `chrome-instantane.mjs`. Le contenu ne bouge pas : seuls les trois blocs
 * entre marqueurs sont remplacés. Rend la liste des fichiers modifiés.
 */
export function rafraichirLeChrome(dossier = DOSSIER, { ecrire = true } = {}) {
  return instantanes(dossier)
    .map(({ fichier }) => {
      const chemin = path.join(dossier, fichier);
      const avant = readFileSync(chemin, 'utf-8');
      const apres = appliquerLeChrome(avant, { courante: '/rapports' });
      if (avant === apres) return null;
      if (ecrire) writeFileSync(chemin, apres);
      return fichier;
    })
    .filter(Boolean);
}

/**
 * Les instantanés pour le `sitemap.xml` : l'index, puis une entrée par page.
 * `lastmod` est la date des DONNÉES, celle que porte le nom du fichier — un
 * instantané ne bouge plus après sa publication (#1029).
 *
 * Ces pages sont servies telles quelles : `pages-par-adresse.mjs` n'en écrit
 * aucune, il se contente de les LISTER. Sans cela, aucun moteur n'a de chemin
 * vers elles — rien d'indexé ne pointe dessus.
 */
export function entreesDeSitemap(dossier = DOSSIER) {
  const liste = instantanes(dossier);
  if (!liste.length) return [];
  return [
    { chemin: 'rapports', lastmod: liste[0].date },
    ...liste.map((i) => ({ chemin: `rapports/${i.fichier}`, lastmod: i.date })),
  ];
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const touches = rafraichirLeChrome();
  const liste = instantanes();
  writeFileSync(INDEX, page(liste));
  console.log(`index-rapports : ${liste.length} article(s) → public/rapports.html`);
  if (touches.length) console.log(`chrome rafraîchi : ${touches.join(', ')}`);
}
