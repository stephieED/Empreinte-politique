<a id="pages-par-adresse-969"></a>

# Chaque adresse publiée est un fichier réel, et répond 200 (#969) (2026-09-17)

`2026-09-17`

> **En bref** — mesuré en production le 17/09/2026 : `/` répondait **200**, et `/sources`, `/faq`, `/methodologie`, `/mentions-legales`, `/candidats/jean-luc-melenchon`, `/groupes` **404**, tous servis par le repli `404.html` de #756 — le lecteur voyait la page, un moteur de recherche une erreur, et rien n'était indexable. Pages n'a pas de règle de réécriture mais sert un **fichier réel** en 200 : `web/UI_finale/scripts/pages-par-adresse.mjs` écrit au build une copie de `index.html` **par adresse publiée**, lue dans `dist/data/manifest.json` — **57 pages** au build du 17/09/2026 (l'accueil, 4 pages fixes, les 30 candidats du manifeste, 12 lignées, 10 gouvernements) — et **33 adresses de redirection** (`/candidats`, `/groupes`, `/gouvernements`, `/couverture`, et les 29 fiches de législature d'avant #329) reçoivent le même fichier **avec une balise `canonical`** vers leur arrivée : un lien déjà partagé répond 200 sans que la fiche soit indexée deux fois. Fichiers **`<adresse>.html`**, jamais `<adresse>/index.html` : Pages répond **301** vers `/x/` pour un dossier, et sert `x.html` à `/x` en 200 (relevé sur deux sites Pages). **Rien n'est écrit pour une fiche absente du manifeste** : les candidatures déclinées (#761) et un identifiant inconnu gardent le repli, en 404, qui est leur bon statut. Les identifiants par défaut sortent dans `src/data/adressesParDefaut.js`, lu par l'application **et** par le script. `lang="fr"`. Le script **échoue** sur un identifiant inutilisable en nom de fichier, une redirection vers une page non publiée, une collision. ~310 Ko ajoutés au déploiement. 8 tests, trois mutations vérifiées échouantes.

Ancres : `pages-par-adresse.mjs`, `spa-fallback.mjs`, `adressesParDefaut.js`.

## Contexte

#756 a fait démarrer l'application sur tout lien profond en copiant
`index.html` dans `404.html`. Il présentait le statut 404 comme une limite
assumée, « sur un site qui n'est pas encore indexé ». #969 la remet en cause :
une page en 404 n'est pas indexée, et aucune autre action de référencement
(titre, description, sitemap) ne sert tant qu'elle le reste.

## Décision

Au build, après `vite build` et `spa-fallback.mjs`, un fichier par adresse :

| Adresse | Source | Fichier |
| --- | --- | --- |
| `/methodologie`, `/sources`, `/faq`, `/mentions-legales` | liste du script, tenue contre `App.jsx` par un test | copie de `index.html` |
| `/candidats/<slug>` | `manifest.candidates` | copie |
| `/groupes/<lignée>` | `manifest.lignees` | copie |
| `/gouvernements/<id>` | `manifest.gouvernements` | copie |
| `/candidats`, `/groupes`, `/gouvernements`, `/couverture`, `/groupes/<fiche de législature>` | redirections de l'application | copie + `canonical` vers l'arrivée |

L'application démarre dans chacun de ces fichiers exactement comme depuis la
racine : c'est elle qui lit l'adresse et redirige, ancre comprise.

## Ce qui ne se vérifie qu'en production

- `dist/` a été servi par un serveur imitant Pages (fichier exact, sinon
  `x.html`, sinon 301 pour un dossier, sinon `404.html` en 404) : toutes les
  adresses publiées en 200, `/candidats/jordan-bardella` et un identifiant
  inconnu en 404.
- **`/candidats`, `/groupes` et `/gouvernements` sont à la fois un fichier
  `x.html` et un dossier `x/`.** Aucun site Pages relevé ne portait cette
  collision : l'ordre de priorité de Pages entre les deux reste à mesurer après
  déploiement. Si Pages préfère le dossier, ces trois adresses répondent 301
  puis 404 — l'application s'affiche toujours, par le repli.

## Alternatives écartées

- **`<adresse>/index.html`**, proposé par l'issue : chaque fiche répondrait 301
  vers une adresse à barre finale, une seconde forme d'adresse pour chaque page.
- **Laisser les redirections en 404** : un lien déjà partagé vers `/couverture`
  ne transmettrait rien à `/sources`.
- **Lire les routes dans `App.jsx` depuis le script** : analyser du JSX sous
  Node au build est plus fragile qu'une liste courte tenue par un test.
