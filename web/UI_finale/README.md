# UI finale — Empreinte politique

Interface de production de l'explorateur **Empreinte politique** (React 19 + Vite 8).

Elle consomme exclusivement les fichiers du dossier `pivot_data/` produits par le pipeline Python, et ne contient aucune logique d'extraction ni de normalisation.

Les règles qui gouvernent ce qu'elle a le droit d'afficher vivent dans `AGENTS.md` — §2 pour l'éditorial, §6 pour ce qui est public et ce qui ne l'est pas. Les règles de forme vivent dans `DESIGN_SYSTEM.md`, à côté de ce fichier. Ce README dit **où sont les choses**, pas pourquoi elles sont ainsi.

---

## Stack

| Rôle | Outil |
|---|---|
| Framework UI | React 19 |
| Bundler / dev server | Vite 8 |
| Routing | React Router v7 (SPA, BrowserRouter) |
| Graphiques | D3 (`d3-sankey` pour la cascade des textes) |
| Linter | Oxlint |
| Typage | JSDoc uniquement (pas de TypeScript) |

---

## Lancer l'application

```bash
# Depuis la racine du dépôt
cd web/UI_finale
npm install

# Dev (synchronise les données puis lance Vite)
npm run dev

# Build de production (sync + vite build + fallback SPA)
npm run build

# Prévisualiser le build
npm run preview
```

Le serveur de développement écoute sur `$PORT` si la variable est définie, sinon sur `5173`.
Plusieurs sessions peuvent travailler en parallèle sur ce dépôt, chacune depuis son propre
worktree : `PORT=5201 npm run dev` évite alors de disputer le port par défaut à une autre.

Après toute régénération de `pivot_data/`, relancer `npm run sync-data` (≈ 70 s) : le serveur
de dev sert `public/data/`, **jamais** `pivot_data/`. Sans resynchronisation on lit le corpus
d'avant, et on conclut faux.

---

## Synchronisation des données

`scripts/sync-data.mjs` s'exécute automatiquement avant `dev` et avant `build`, et peut se
lancer seul (`npm run sync-data`). Il copie ou projette, dans cet ordre :

| Source dans `pivot_data/` | Destination | Rôle |
|---|---|---|
| `scrutins.json` | `public/data/` | index partagé des scrutins (#432) — absent, tous les votes s'affichent vides |
| `amendements/` (métadonnées seules) | `public/data/amendements/` | index partagé (#431) ; les corps d'amendements ne sont **pas** copiés |
| `commissions_dossiers.json` | `public/data/` | commission saisie au fond, par dossier (#328) — c'est la « matière » |
| `scrutins_dossiers.json` | `public/data/` | scrutin → dossier, statut, 49.3 (#758) |
| `raw_data/candidats.json` | `public/data/candidats.json` | roster brut : nom, parti, statut |
| `profiles/*.pivot.json` | `public/data/profiles/` | les profils de **candidats déclarés** |
| `groupes/groupe-*.json` | `public/data/groupes/` | fiches de groupe par législature |
| `lignees/` | `public/data/lignees/` | une vue projetée par lignée (#329) |
| `gouvernements/` | `public/data/gouvernements/` | fiches de gouvernement |

Il génère ensuite `public/data/manifest.json`, l'index central à **quatre** entrées :
`{ candidates[], groupes[], lignees[], gouvernements[] }`.

Un retrait est décidé **au build** et **nommé** dans le journal — une page qui disparaît en
silence est une page qu'on croit encore publiée : **le Sénat**, dont les groupes ne seront
pas collectés (#885). Le filtre porte sur `chambre` et retire les deux objets ensemble, la
fiche de groupe et la lignée qui la porte ; les fichiers restent dans `pivot_data/`.

Le dossier `public/data/` n'est **pas versionné** ; il est entièrement généré à la volée.

---

## Structure de `src/`

Le dossier fait foi ; cette carte dit à quoi sert chaque étage.

```
src/
├── main.jsx                  # Point d'entrée React (StrictMode + BrowserRouter)
├── App.jsx                   # Déclaration des routes
├── index.css                 # Tokens CSS globaux (palette, typographie)
├── components/               # Composants d'affichage — ils ne calculent aucun fait
│   ├── ExplorerLayout        # Coque de l'explorateur : barres latérales + outlet
│   ├── Brand · EnTeteSite · NavigationSite · PiedDeSite · SommaireSections · ScrollRow · StaticPage
│   ├── CandidatesBar · GroupsBar · GovernmentsBar   # les trois onglets
│   ├── CandidateProfile      # Fiche candidat
│   ├── LigneeProfile         # Fiche d'une lignée de groupe (#329)
│   ├── GovernmentProfile     # Fiche de gouvernement
│   ├── VotesParPeriode       # « Ce qu'il a voté », par période politique (#328)
│   ├── ParolesParPeriode     # « Ce qu'il a dit », par qualité de parole (#328)
│   ├── EcartsGroupe          # « Ses divergences », scrutin par scrutin (#328)
│   ├── CascadeTextes         # Cascade des textes portés (d3-sankey)
│   ├── NavigationPeriodes    # Sélecteur de période, partagé par les sections
│   ├── FriseCouverture       # Frise de /couverture, par institution
│   ├── Lecture · ConstructionBanner · NotFoundProfile
│   └── landing/              # Hero et CandidatsDeclares (accueil, #951) ; HowItWorks,
│                             #   WhatYouWontFind (tête de /methodologie) ; Faq (questions de /faq)
├── pages/                    # Pages routées
│   ├── LandingPage           # L'accueil, hors explorateur
│   ├── CandidateProfilePage · GroupProfilePage · GovernmentProfilePage
│   └── MethodologyPage · CoveragePage · LegalNoticePage
├── context/
│   └── GroupFilterContext    # État global : groupe sélectionné (filtre candidats)
├── data/
│   ├── index.js              # API de fetch + défauts de route
│   └── pivotAdapter.js       # Pivot JSON → objets consommables ; APPELLE utils/,
│                             #   n'écrit pas de seconde version des règles
├── utils/                    # LES RÈGLES DE LECTURE — c'est ici que vivent les faits
│   ├── lecture.js            # Fondations communes ; isWholeTextVote, dernière lecture (#711)
│   ├── profilCandidat.js     # Règles propres à la fiche candidat ; STADES_PUBLIES
│   ├── votesParPeriode.js    # Découpage par (banc, gouvernement) ; échelle commune
│   ├── parolesParPeriode.js  # Qualité de parole (#328)
│   ├── ecartsGroupe.js       # Juxtaposition position / groupe, par scrutin (§2 règle 7)
│   ├── cascadeTextes.js      # Construction du Sankey des textes portés
│   ├── groupe.js · lignee.js # Fiches de groupe et de lignée
│   ├── matiere.js            # La palette des matières — une teinte, jamais une échelle
│   └── text.js               # Helpers texte (initiales, etc.)
├── hooks/
│   ├── useAsyncData.js       # Chargement async générique { data, loading, error }
│   └── useDragScroll.js      # Drag-scroll horizontal sur les barres
└── styles/
    └── shell.css             # CSS de la coque applicative
```

---

## Flux de données

```
manifest.json + profiles/ + groupes/ + lignees/ + gouvernements/ + les quatre index partagés
        │                                                          (public/data/)
        ▼
data/index.js         — fetch + cache ; getCandidateProfile() / getLigneeProfile()
        │                              / getGovernmentProfile() / loadCouverture()
        ▼
data/pivotAdapter.js  — buildCandidateView() / buildGovernmentView() ; la fiche de
        │               lignée lit la projection calculée au build
        ▼
utils/*.js            — les règles de lecture : sélection, découpage, ratios
        │
        ▼
useAsyncData()        — { data, loading, error }
        │
        ▼
CandidateProfile / LigneeProfile / GovernmentProfile   — affichage
```

`pivotAdapter.js` est le point de passage unique entre la donnée et l'écran. Les **règles**
vivent dans `utils/` et n'y sont jamais réécrites : une règle dupliquée est une règle qui
diverge.

---

## Routes

| URL | Composant | Description |
|---|---|---|
| `/` | `LandingPage` | L'accueil : ce que le dépôt porte, comment il est fait |
| `/candidats` | → redirect | Vers le candidat par défaut |
| `/candidats/:candidateId` | `CandidateProfilePage` | Fiche candidat |
| `/groupes` | → redirect | Vers la lignée par défaut |
| `/groupes/:groupId` | `GroupProfilePage` | Fiche de lignée ; un id de fiche par législature redirige vers sa lignée |
| `/gouvernements` | → redirect | Vers le gouvernement par défaut |
| `/gouvernements/:governmentId` | `GovernmentProfilePage` | Fiche de gouvernement |
| `/methodologie` | `MethodologyPage` | La méthode, les règles, ce qui n'est pas publié |
| `/sources` | `CoveragePage` | Les sources et ce que chacune apporte (#951), puis ce que le dépôt porte et depuis quand, pour tout le corpus (#328). `/couverture` y redirige |
| `/mentions-legales` | `LegalNoticePage` | Sources, licences, attribution |

Trois onglets dans l'explorateur — **Candidats · Groupes · Gouvernement** —, mais **dix
routes** : les trois pages statiques vivent hors de la coque.

---

## Règles éditoriales respectées dans l'UI

Les règles de `AGENTS.md §2` s'appliquent au code d'affichage. Les plus structurantes :

- Aucun taux de présence individuel n'est affiché (règle 3).
- Les 49.3 sont étiquetés comme fait procédural, sans position de vote (règle 4).
- Une donnée absente se dit absente, jamais `0` (règle 5) : un compte vide et un compte non
  publié sont deux affichages différents.
- Les ratios de groupe ne s'affichent qu'avec numérateur + dénominateur (règle 7).
- La position d'une personne se juxtapose à celle de son groupe **un scrutin à la fois**, et
  n'est **jamais comptée** : un compte de divergences est un indice individuel mesuré contre
  une moyenne de groupe, réservé au rapport interne (règle 7).
- Les tags thématiques sont des aides à la lecture, pas des positions déclarées (règle 8).

**Plusieurs tests du dépôt verrouillent des arbitrages, pas seulement du comportement.**
Quand l'un rougit, lire son nom et sa docstring avant de le modifier : il protège
peut-être une décision qu'on est en train de renverser sans le savoir. Exemples :
`tests/test_mention_mandats_anterieurs_860.py` (un mandat antérieur ne se lit qu'à un
endroit), `tests/test_qualite_de_parole_328.py`, et l'interdiction de `toLowerCase` dans
`ParolesParPeriode.jsx` (#639).

---

## Linter

```bash
npm run lint          # oxlint sur tout le projet
npx oxlint src scripts
```

Oxlint (Rust-based). Pas de configuration TypeScript — JSDoc uniquement.
