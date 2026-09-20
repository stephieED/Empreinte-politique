<a id="titres-par-page-969"></a>

# Chaque page porte son titre et sa description, écrits depuis ce que la fiche contient (#969) (2026-09-17)

`2026-09-17`

> **En bref** — arbitré le 17/09/2026 sur maquette, entre trois formes sur six pages réelles : **forme C, « l'élection en tête »** — « Jean-Luc Mélenchon, présidentielle 2027 — parcours politique sourcé ». La forme proposée par l'issue (« mandats, votes et textes » en titre) aurait été **fausse pour 13 des 30 candidats déclarés publiés**, sans aucun vote dans les données : le titre est donc le même pour toutes les fiches, et **la description suit ce que la fiche contient** — mandats, votes, textes, présents ou non, et les institutions où la personne a siégé (`chambres`), « mandats locaux » quand il n'y en a aucune. Groupes : « Groupe Socialistes à l'Assemblée nationale — membres, votes, amendements », période en description ; gouvernements : « Gouvernement Lecornu II (depuis 2025) — membres et textes ». Écrits au build par `scripts/metadonnees-pages.mjs` dans `<title>`, `description`, `og:` et `twitter:`, avec une `canonical` vers l'adresse elle-même ; une balise absente d'`index.html` **arrête le build**. Jamais de nombre de votes (§2 règle 3), jamais d'accord de genre (« candidature »). L'onglet suit la navigation : `TitreDeLaPage.jsx` relit le titre dans le fichier de l'adresse, sans le réécrire. Mesuré en production après #999 : `/candidats`, fichier `candidats.html` et dossier `candidats/` à la fois, répond **200** — Pages sert le fichier. 13 tests sur entrées copiées du corpus, trois mutations vérifiées échouantes.

Ancres : `metadonnees-pages.mjs`, `pages-par-adresse.mjs`, `TitreDeLaPage.jsx`.

## Contexte

#999 a donné un fichier, donc un statut 200, à chaque adresse publiée ; toutes
portaient encore le même titre, « Empreinte politique ». La maquette comparait
trois formes : A (ce que la fiche contient, en titre), B (le nom seul), C
(l'élection en tête). La mesure qui a écarté A : 13 des 30 fiches de candidats
déclarés n'ont aucun vote dans les données publiées le 17/09/2026.

## Décision

| Page | Titre | Description |
| --- | --- | --- |
| Accueil | Présidentielle 2027 : les parcours politiques des candidats, sourcés | Mandats, votes et textes des candidats déclarés… (dans `index.html`) |
| Candidat | `<nom>`, présidentielle 2027 — parcours politique sourcé | ce que la fiche contient · étiquette. Phrase de source |
| Groupe | Groupe `<nom>` à l'Assemblée nationale — membres, votes, amendements | Depuis `<année>` / De … à … / En …. Phrase de source |
| Gouvernement | `<nom>` (`<période>`) — membres et textes | phrase de source |
| Méthode, Sources, FAQ, Mentions légales | `<titre affiché>` — Empreinte politique | la méthode a la sienne ; les autres gardent celle du site |

**Le texte est relu dans les données, jamais supposé.** Une fiche sans mandat
(Nathalie Arthaud) ne porte que son étiquette : la description ne promet
rien que la fiche n'affiche.

**L'onglet suit la navigation.** Une navigation dans l'application ne recharge
pas la page : le titre de la première adresse ouverte serait resté. Le
composant relit le `<title>` du fichier de l'adresse affichée — une seule
rédaction, celle du build. Une adresse sans fichier garde le titre en place.

## Alternatives écartées

- **A, le contenu en titre** : faux pour 13 fiches sur 30, ou variable d'une
  fiche à l'autre, et coupé dans les résultats au-delà d'environ 60 caractères.
- **B, le nom seul** : toujours vrai, mais sans le mot que les recherches
  portent sur un candidat, « 2027 ».
- **Recalculer le titre dans l'application** : deux rédactions du même texte,
  qui divergeraient.
