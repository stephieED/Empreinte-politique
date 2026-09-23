<a id="chrome-du-site-sur-les-instantanes-1029"></a>

# Le bandeau et le pied du site sur les pages d'instantané (#1029) (2026-09-23)

`2026-09-23`

> **En bref** — Un instantané est une page statique servie hors de l'application React : il portait donc un bandeau à lui — la marque et deux liens — et, pour celui du 23/09, aucun pied. Un lecteur arrivé par un lien LinkedIn tombait sur une page qui ne ressemblait pas au site, sans le contact, sans les mentions légales, sans le bandeau « en construction » que toutes les autres pages portent, et sans l'attribution due aux sources (§2 règle 2). Arbitré le 23/09/2026 : les pages statiques reprennent le **vrai** bandeau (avis d'état, logo, barre des pages, menu replié sous 720 px) et le **vrai** pied (marque, baseline, pages du site, adresse de contact, LinkedIn et X). Le markup et le style sont **recopiés** dans `web/UI_finale/scripts/chrome-instantane.mjs`, faute de pouvoir exécuter du JSX hors de l'application ; `tests/test_chrome_instantanes_1029.py` compare la copie aux composants React, et `tests/test_rapports_publies.py` refuse une page dont le chrome a dérivé du module. **Le chrome suit le site, le contenu reste gelé** : les trois blocs vivent entre marqueurs et `node scripts/index-rapports.mjs` les réécrit dans toutes les pages du dossier.

## Le contexte

`docs/decisions/instantanes-publies-1029.md` a posé la page statique et son
index. Le bandeau de ces pages était provisoire : « Empreinte politique · Les
instantanés », en gras, sur une ligne. L'instantané du 23 septembre n'avait, lui,
aucun pied — donc ni adresse de contact, ni mentions légales, ni attribution des
sources, alors que c'est la page que la communication envoie en premier.

Trois choses manquaient, et chacune pour une raison différente :

- **l'avis « en construction »** est sur toutes les pages du site depuis #556 ;
  un lecteur qui arrive par un lien direct doit savoir que des données manquent
  avant de conclure d'une liste vide. Un instantané est un lien direct ;
- **l'attribution** est due tant que les faits sont publiés (§2 règle 2, §7) ;
- **le contact et les mentions légales** ne vivent que dans le pied.

## La décision

Un module unique, `web/UI_finale/scripts/chrome-instantane.mjs`, porte les trois
blocs : le style, le bandeau, le pied. Il est importé par
`scripts/index-rapports.mjs`, qui construit l'index et réécrit le chrome de
chaque instantané du dossier.

**Le markup est recopié, et c'est le défaut assumé du procédé.**
`EnTeteSite.jsx`, `NavigationSite.jsx`, `PiedDeSite.jsx`, `Brand.jsx`,
`Baseline.jsx` et `ConstructionBanner.jsx` sont du JSX : ils ne s'exécutent pas
hors de l'application, et une page statique ne charge pas React pour afficher un
menu. Ce qui est tenu par un test, ce n'est pas le style — une couleur qui dérive
se voit à l'écran — mais **ce qui ne se voit jamais depuis la page** : les
entrées de la barre, les liens du pied, l'adresse de contact, les deux comptes,
les quatre mentions de la baseline, et la phrase du bandeau d'état. Une page
ajoutée à la barre du site fait donc rougir la suite tant qu'elle n'est pas ici.

**Le chrome suit le site, le contenu reste gelé.** « Un instantané n'est jamais
mis à jour » vaut pour ses faits, pas pour le menu qui l'entoure : un lien mort
dans le pied d'une page de septembre ne la rend pas plus fidèle à sa date. Les
trois blocs vivent donc entre marqueurs (`<!--chrome:bandeau-->`,
`<!--chrome:pied-->`, et `/*chrome:style*/` **en commentaire CSS** parce qu'il
est dans le `<style>` de la page), et une page qui n'en porte pas est refusée :
un instantané sans bandeau ni pied n'est pas une page du site.

Deux conséquences, mineures et voulues :

- **le menu étroit est un `<details>`**, pas un bouton — sous 720 px la barre
  replie ses liens, et une page statique n'a pas de React pour tenir cet état ;
- **les pages d'instantané perdent leur thème sombre.** Elles en avaient un, le
  site n'en a pas (`src/index.css` fixe `color-scheme: light`), et le lockup de
  la marque n'existe qu'en version claire : sur fond sombre, le logo du bandeau
  disparaissait. Une page du site s'affiche comme le site.

## Le sitemap

Une page qui répond 200 et vers laquelle rien d'indexé ne pointe n'est trouvée
par personne. `pages-par-adresse.mjs` n'écrit aucune des pages d'instantané — Vite
les recopie depuis `public/rapports/` —, donc elles ne passaient pas non plus par
son sitemap : elles étaient absentes des 66 adresses publiées. `index-rapports.mjs`
expose `entreesDeSitemap()`, que le build concatène aux pages publiées : l'index
`/rapports` et une entrée par instantané, avec pour `lastmod` la date des DONNÉES
— celle que porte le nom du fichier, puisqu'un instantané ne bouge plus après sa
publication. Chaque page déclare aussi sa `canonical`, comme les autres pages
publiées depuis #969.

## Deux mesures que ce lot a dû faire

**Pages tranche la collision fichier / dossier en faveur du fichier.**
`dist/rapports.html` voisine `dist/rapports/`, et
`docs/decisions/pages-par-adresse-969.md` laissait l'ordre de priorité « à
mesurer après déploiement » — si Pages préférait le dossier, le bouton
« Instantanés » aurait répondu 301 puis 404. Mesuré en production le 23/09/2026
sur `/candidats`, `/groupes` et `/gouvernements`, qui portent la même collision
depuis #969 : les trois répondent **200 avec le contenu de `x.html`**. Le point
ouvert de #969 est donc tranché, par la mesure et non par un choix.

**Le serveur de développement, lui, ne le fait pas.** Une adresse sans extension
tombe dans le repli SPA, React n'a pas de route `/rapports`, et l'écran reste
blanc — vu en cliquant sur « Instantanés » depuis l'accueil servi en local. Un
middleware de `vite.config.js`, en `apply: 'serve'` donc absent du build, résout
`/x` en `public/x.html` quand le fichier existe : le développement se comporte
comme la production, sur cette page comme sur `/faq`.

## L'alternative écartée

**Générer le chrome depuis les composants React** — rendre `EnTeteSite` et
`PiedDeSite` en HTML à la construction, avec `react-dom/server`. C'est la seule
façon de supprimer la copie, et elle a été écartée : elle impose de charger
l'application et ses styles dans un script de génération pour deux blocs de
markup, elle rendrait un `<Link>` de routeur en `<a href>` qu'il faudrait
réécrire de toute façon, et elle ne couvre ni le `<details>` du menu ni les
adresses absolues. Le coût de la copie est borné par les gardes ; celui de la
génération serait permanent.

**Ne rien mettre du tout, et laisser la page nue**, comme un document partagé.
Écarté : l'attribution est due, le contact est la seule chose qu'on vient
chercher dans un pied, et l'avis « en construction » vaut surtout sur la page
qu'un lien extérieur ouvre en premier.
