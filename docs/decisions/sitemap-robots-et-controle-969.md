<a id="sitemap-robots-et-controle-969"></a>

# Un sitemap des pages publiées, un robots.txt qui n'exclut personne, et un contrôle qui rend la régression visible (#969) (2026-09-17)

`2026-09-17`

> **En bref** — dernière étape de #969, après #999 (statut 200), #1002 (titres) et #1003 (faits lisibles sans JavaScript). `sitemap.xml` et `robots.txt` étaient **absents** — `/sitemap.xml` répondait 404. Le build les écrit : **57 adresses**, celles des pages publiées, **jamais les 33 redirections** (arbitré le 17/09/2026 — une redirection n'a rien à indexer et sa `canonical` dit déjà où aller ; les lister ferait explorer un tiers d'adresses sans contenu propre). `lastmod` porte **la date de la donnée** (`meta.genere_le` d'un profil, `genereLe` d'une projection de lignée), pas celle du build : un build qui ne change rien n'annonce pas 57 pages modifiées ; une date absente n'en fabrique aucune. **Ni `changefreq` ni `priority`** : ignorés par Google, et deux affirmations de plus à tenir. `robots.txt` autorise **tout le monde**, robots des modèles de langage compris, et désigne le sitemap. Le **critère de fin** de l'issue est livré avec : `scripts/verifier-referencement.mjs` parcourt le sitemap d'un site servi et échoue sur un statut ≠ 200, un titre manquant, une `canonical` manquante, deux pages au même titre, ou une fiche redescendue sous 100 caractères lisibles sans JavaScript. Mesuré sur le build servi comme Pages : 57 adresses, 52 fiches, 57 en 200, 57 titres distincts, aucun défaut. 10 tests, commande documentée.

Ancres : `sitemap-et-robots.mjs`, `verifier-referencement.mjs`, `pages-par-adresse.mjs`.

## Décision

| Fichier | Contenu |
| --- | --- |
| `sitemap.xml` | les 57 pages publiées, avec `lastmod` = date de la donnée |
| `robots.txt` | `User-agent: *`, `Allow: /`, et la ligne `Sitemap:` |
| `scripts/verifier-referencement.mjs` | le contrôle, sur un site servi, documenté dans `docs/commandes.md` |

**Le contrôle interroge un site SERVI, jamais `dist/`.** Ce qui se mesure est ce
que le serveur répond : `vite preview` ne reproduit pas le comportement de
GitHub Pages, et c'est ce comportement qui a fait le défaut d'origine. Les
`loc` du sitemap portent le domaine de production : le script en garde le
chemin et le rapporte à la base donnée, sinon un contrôle local mesure le site
en ligne en croyant mesurer le build.

## Alternative écartée

**Lister aussi les redirections**, pour qu'un lien déjà partagé vers
`/couverture` soit exploré plus tôt. Elles répondent 200 depuis #999 et portent
leur `canonical` : un moteur les trouve par les liens du site, sans qu'un tiers
du budget d'exploration parte dans des adresses sans contenu propre.
