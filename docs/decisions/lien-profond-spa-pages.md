# Un lien profond démarre l'application, pas la page d'erreur de GitHub, 07/09/2026

`2026-09-07`

> **En bref** — mesuré en production au commit déployé `df5a9ba5` : `/` répondait **200**, `/candidats` et `/candidats/<slug>` répondaient **404**, et `/404.html` aussi ; l'application route côté client (`BrowserRouter`) quand Pages sert des **fichiers** et n'a **aucune règle de réécriture**, si bien que le site n'était navigable qu'en partant de la racine — un favori, un lien partagé, une entrée d'historique ou un simple **F5 sur une fiche** tombaient sur la page d'erreur de GitHub ; `dist/404.html` reçoit donc le contenu de `dist/index.html`, seul mécanisme disponible, et la copie est faite par le **build** (`scripts/spa-fallback.mjs`) et non par `deploy-pages.yml`, parce que le workflow ne fait que téléverser `dist/` et qu'un `dist/` publié autrement doit porter le même repli ; le repli **échoue bruyamment** si `index.html` manque ; **ce qui reste assumé** : le statut HTTP demeure **404** sur un lien profond — le lecteur voit la bonne page, un robot voit une erreur —, le corriger demandant un hébergement qui réécrit ou un routage par fragment qui abîmerait les URL ; défaut **ancien et sans rapport avec le lot du jour**, apparu avec le déploiement Pages et vu seulement parce qu'une fiche a été rafraîchie. 5 tests, trois mutations vérifiées échouantes, et le repli éprouvé contre un serveur reproduisant Pages.

Ancres : `spa-fallback.mjs`, `deploy-pages.yml`, `BrowserRouter`.

## Contexte

Mesuré en production le 07/09/2026 sur `https://empreinte-politique.fr`, au
commit déployé `df5a9ba5` :

| URL | réponse |
| --- | --- |
| `/` | 200 |
| `/candidats` | **404** |
| `/candidats/gabriel-attal` | **404** |
| `/404.html` | **404** |

L'application route côté client (`BrowserRouter`, `src/main.jsx`). GitHub Pages
sert des **fichiers** : il ne connaît que `/index.html` et répond 404 à tout
chemin qui n'est pas un fichier réel. Le site n'était donc navigable qu'en
partant de la racine et en cliquant — un favori, un lien partagé, une entrée
d'historique, ou simplement **F5 sur une fiche candidat** tombaient sur la page
d'erreur de GitHub.

Le défaut est ancien et n'avait rien à voir avec le lot du jour : il est apparu
avec le déploiement Pages, pas avec la section « Ce qu'il a proposé ». Il s'est
vu ce jour-là parce que la propriétaire a rafraîchi une fiche pour y chercher
des corrections fraîchement fusionnées.

## Décision

`dist/404.html` reçoit le contenu de `dist/index.html`. Pages sert `404.html`
pour tout chemin inconnu ; l'application démarre donc, lit l'URL et affiche la
bonne page. **C'est le seul mécanisme disponible** — Pages n'a aucune règle de
réécriture.

**La copie est faite par le BUILD, pas par le workflow.** `npm run build`
enchaîne `sync-data`, `vite build` puis `scripts/spa-fallback.mjs`. Mettre la
copie dans `deploy-pages.yml` la lierait à un seul chemin de publication, alors
que le workflow ne fait que téléverser `dist/` : c'est au build de rendre
`dist/` complet. Un `dist/` construit à la main et publié autrement porte le
même repli.

**Le repli échoue bruyamment** si `dist/index.html` manque : un repli
silencieusement absent redonne le défaut sans rien dire.

## Ce qui reste, et qui est assumé

**Le statut HTTP demeure 404 sur un lien profond.** Le lecteur voit la bonne
page, un robot voit une erreur. Le corriger demanderait un hébergement capable
de réécrire, ou un routage par fragment (`/#/candidats/…`) qui abîmerait les
URL — deux choix plus lourds que le défaut qu'ils réparent, sur un site qui
n'est pas encore indexé.

## Vérification

Le repli a été éprouvé contre un serveur reproduisant Pages — le fichier s'il
existe, sinon `404.html` avec le statut 404. `/candidats/gabriel-attal` y rend
la fiche complète : cascade, chute, et la ligne 49.3.

## Alternative écartée

**`HashRouter`.** Elle supprime le problème à la racine — `/#/candidats/…` est
toujours servi par `index.html` — mais change toutes les URL publiques du site
pour une forme datée, et casserait tout lien déjà partagé. Le repli `404.html`
laisse les URL propres.
