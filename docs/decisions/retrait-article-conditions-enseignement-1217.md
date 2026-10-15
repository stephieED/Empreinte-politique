<a id="retrait-article-conditions-enseignement-1217"></a>

# L'article « Les conditions d'enseignement » est retiré, et son remplaçant change de titre (#1217) (2026-10-14)

`2026-10-14`

> **En bref** — Deux articles sur le même sujet étaient en ligne : « Les conditions d'enseignement, de l'école au lycée » (`2026-10-04-conditions-d-enseignement.html`), première version, et « L'éducation à l'Assemblée, avant et pendant la mobilisation lycéenne » (`2026-10-09-education-a-l-assemblee.html`), qui l'a entièrement revue. La propriétaire a demandé le 14/10/2026 le retrait de la première, et un nouveau titre pour la seconde : « L'éducation dans les débats de l'Assemblée, avant et pendant la mobilisation lycéenne ».

## Le contexte

La règle des articles veut qu'un instantané ne soit jamais mis à jour, et qu'un
sujet repris reçoive une nouvelle page à une nouvelle adresse (`AGENTS.md` §1).
Elle a été suivie : la version revue a sa propre adresse. Mais l'ancienne est
restée publiée, et l'index des articles listait les deux. Ce n'étaient pas deux
instantanés de dates différentes sur un même sujet : la seconde remplace la
première, qui n'avait plus de raison d'être lue.

## La décision

- La page `web/UI_finale/public/rapports/2026-10-04-conditions-d-enseignement.html`
  est supprimée ; l'index (`public/rapports.html`) est régénéré par
  `scripts/index-rapports.mjs` et le `sitemap.xml`, construit depuis le même
  dossier, la perd au déploiement suivant.
- **Ce retrait est un cas, pas une règle** : un sujet repris à une autre date
  garde ses deux instantanés quand chacun mesure son instant. Ici la seconde
  page a remplacé la première.
- Les décisions qui décrivent l'ancien article
  (`instantane-compte-des-personnes-1217`,
  `instantane-enseignement-orientation-apres-le-bac-1217`) restent telles
  quelles : elles disent pourquoi il était fait ainsi.

- **Le titre de l'article restant change**, à la demande de la propriétaire :
  « L'éducation à l'Assemblée » pouvait se lire « éduquer l'Assemblée », sur le
  modèle de « l'éducation à la santé ». Retenu parmi quatre propositions :
  « L'éducation dans les débats de l'Assemblée, avant et pendant la
  mobilisation lycéenne ». Le titre de la page, son `<h1>` et l'index changent ;
  **l'adresse ne change pas**, pour qu'un lien déjà partagé réponde toujours.
  C'est une retouche de libellé, pas une mise à jour de l'instantané : ses
  données et sa date ne bougent pas.

## Ce qui reste ouvert

L'ancienne adresse ne répond plus : un lien partagé vers elle tombe sur la page
d'erreur du site. Aucune redirection n'est posée — un fichier de
redirection dans `public/rapports/` serait lu comme un article par l'index.

## L'alternative écartée

Garder l'ancienne page, hors de l'index : elle resterait lisible par son
adresse et dans les moteurs de recherche, avec un contenu que la version revue
corrige.
