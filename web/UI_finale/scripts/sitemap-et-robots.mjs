/*
 * LE SITEMAP ET LE ROBOTS.TXT (#969).
 *
 * Mesuré en production le 17/09/2026 : les deux fichiers étaient absents, et
 * l'adresse `/sitemap.xml` répondait 404 — un moteur de recherche n'avait
 * aucune liste des pages à explorer.
 *
 * LE SITEMAP LISTE LES 57 PAGES PUBLIÉES, PAS LES 33 REDIRECTIONS. Arbitré le
 * 17/09/2026 : une redirection n'a rien à indexer, et sa balise `canonical`
 * dit déjà où aller. Les y mettre ferait explorer un tiers d'adresses sans
 * contenu propre.
 *
 * `lastmod` est LA DATE DE LA DONNÉE, pas celle du build : `meta.genere_le`
 * d'un profil, la date de la projection d'une lignée. Un build qui ne change
 * rien ne doit pas annoncer 57 pages modifiées. Les pages fixes et l'accueil,
 * qui ne viennent d'aucune donnée, portent la date du build.
 *
 * AUCUN ROBOT N'EST EXCLU, ceux des modèles de langage compris (GPTBot,
 * ClaudeBot, PerplexityBot) : c'est ce que le lot cherche, la propriétaire l'a
 * demandé explicitement. Pas de `changefreq` ni de `priority` — Google les
 * ignore depuis des années, et ils seraient deux affirmations de plus à tenir.
 */

function ech(texte) {
  return String(texte).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

/* `entrees` : [{ chemin, lastmod }], chemin sans barre initiale ('' = accueil). */
export function sitemap(domaine, entrees) {
  const urls = [...entrees]
    .sort((a, b) => a.chemin.localeCompare(b.chemin))
    .map(({ chemin, lastmod }) => {
      const jour = /^\d{4}-\d{2}-\d{2}/.test(lastmod || '') ? lastmod.slice(0, 10) : null;
      return `  <url>\n    <loc>https://${ech(domaine)}/${ech(chemin)}</loc>\n`
        + (jour ? `    <lastmod>${jour}</lastmod>\n` : '')
        + '  </url>';
    });
  return '<?xml version="1.0" encoding="UTF-8"?>\n'
    + '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + `${urls.join('\n')}\n</urlset>\n`;
}

export function robots(domaine) {
  return [
    '# Toutes les pages publiées sont listées dans le sitemap ci-dessous.',
    "# Aucun robot n'est exclu, y compris ceux des modèles de langage.",
    '',
    'User-agent: *',
    'Allow: /',
    '',
    `Sitemap: https://${domaine}/sitemap.xml`,
    '',
  ].join('\n');
}
