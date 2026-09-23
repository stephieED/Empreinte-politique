import { existsSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const ici = path.dirname(fileURLToPath(import.meta.url))

/* ── LE SERVEUR DE DÉVELOPPEMENT RÉSOUT `/x` EN `x.html` (#1029) ──────────────
 *
 * GitHub Pages sert `x.html` quand on demande `/x` — c'est ce qui fait marcher
 * `/faq`, `/sources` et, depuis #1029, `/rapports`. Vite, lui, ne le fait pas :
 * une adresse sans extension tombe dans le repli SPA, React n'a pas de route
 * `/rapports`, et l'écran reste blanc. Mesuré le 23/09/2026, en cliquant sur
 * « Instantanés » depuis l'accueil servi en local.
 *
 * Ce middleware ne vaut QUE pour le développement : il réécrit la requête vers
 * le fichier de `public/` quand il existe. Rien n'est ajouté au build.
 *
 * La collision fichier/dossier — `rapports.html` à côté de `rapports/` — est
 * tranchée par Pages EN FAVEUR DU FICHIER : mesuré en production le 23/09/2026
 * sur `/candidats`, `/groupes` et `/gouvernements`, qui portent la même
 * collision depuis #969 et répondent 200 avec le contenu de `x.html`. Le
 * middleware fait donc pareil.
 */
function adressesSansExtension() {
  return {
    name: 'adresses-sans-extension',
    apply: 'serve',
    configureServer(serveur) {
      serveur.middlewares.use((req, _res, suite) => {
        const [chemin] = (req.url || '').split('?');
        if (chemin && !path.extname(chemin) && chemin !== '/') {
          const fichier = path.join(ici, 'public', `${chemin.replace(/\/$/, '')}.html`);
          if (existsSync(fichier)) req.url = `${chemin.replace(/\/$/, '')}.html`;
        }
        suite();
      });
    },
  };
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), adressesSansExtension()],
  server: {
    port: Number(process.env.PORT) || 5173,
    strictPort: false,
  },
})
