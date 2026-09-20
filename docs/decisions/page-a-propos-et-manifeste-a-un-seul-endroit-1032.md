<a id="page-a-propos-et-manifeste-a-un-seul-endroit-1032"></a>

# La page /a-propos, et le manifeste à un seul endroit (#1032) (2026-09-18)

`2026-09-18`

> **En bref** — la propriétaire a demandé une page « À propos » portant un manifeste et la présentation de l'éditrice. Le manifeste qu'elle a écrit était, **à trois mots près, l'introduction déjà publiée de `/methodologie`** (#977) — « corrigé » pour « altéré », « relus par une personne » pour « validés par un humain », « et la fiche le dit » pour « chacun cite sa source ». Publier les deux, c'était refaire le défaut que #1026 venait de mesurer : la `meta description` et cette introduction ne disaient déjà pas la même chose. **Structure A retenue** : `/a-propos` porte le manifeste et l'éditrice, `/methodologie` garde ses **quinze sections** et son introduction devient une phrase sur ce que cette page-là fait. Ce qui a écarté la fusion des deux pages est une mesure : `/methodologie` est citée par **26 liens internes**, dont **10 ancres profondes** appelées depuis les fiches (`#fonctions`, `#propose`, `#couverture`, `#ecarts`) — une redirection les aurait toutes fait rebondir. **Forme retenue sur maquette, entre trois** : le manifeste dans le **bandeau d'encre**, aux cotes de celui de l'accueil, avec la baseline de #1026 en pied de bandeau, puces en accent — le seul fond où le jaune signal passe le contraste (16,01:1). Écartées : la coque standard des pages statiques, qui réduisait le manifeste au chapeau de `/methodologie` ; un grand texte sans bannière, qui ne disait plus où l'on est. La section s'intitule **« Qui édite ce site »**, pas « Qui sommes-nous » : la page parle à la première personne du singulier. **La présentation est celle de la propriétaire, et elle signe « Stéphie E. »** : le patronyme n'est pas publié, ce qui laisse les mentions légales garder leur formulation — « édité à titre non professionnel et non commercial par une personne physique », l'identité tenue à la disposition de l'hébergeur (LCEN, article 6-III). La tension entre les deux pages tombe, et un test refuse que le patronyme soit ajouté ici. **Ce qui reste ouvert** : la place de la page dans le bandeau — elle est au pied de page, le bandeau restant à quatre onglets (#1025).

## Le contexte

Mesuré le 18/09/2026 sur `origin/main` (`8c4ce00f6`) :

| Ce qui existait | Volume |
| --- | ---: |
| `/methodologie` | 4 familles, **15 sections**, 570 lignes |
| Son introduction | 4 phrases — le manifeste |
| Liens internes vers `/methodologie` | **26** |
| Dont ancres profondes citées par les fiches | **10** |
| Présentation de l'éditrice | aucune |

Les mentions légales, elles, ne nomment personne à dessein : « édité à titre non
professionnel et non commercial par une personne physique », l'identité étant
tenue à la disposition de l'hébergeur au titre de l'article 6-III de la LCEN.

## La décision

### 1. Deux pages, deux questions

`/a-propos` dit **ce que le site est et qui l'édite**. `/methodologie` dit
**comment chaque fiche est faite**, liste par liste. Le manifeste quitte la
seconde pour la première, et l'introduction de `/methodologie` devient :

> Cette page dit comment chaque fiche est faite : ce que chaque chiffre mesure,
> ce qu'il ne mesure pas, et ce que le site refuse de publier.

Le texte n'existe donc qu'à un seul endroit. C'est la règle que ce lot ajoute,
et un test la tient.

### 2. Pourquoi la fusion a été écartée

L'alternative était que `/a-propos` absorbe `/methodologie`, qui aurait
redirigé — comme `/couverture` → `/sources` (#951). Le coût est mesurable : 26
liens internes rebondiraient, et les 10 ancres profondes que les fiches
appellent devraient survivre à la redirection. Le gain aurait été une adresse de
moins ; le prix, une page unique mêlant une présentation personnelle et quinze
sections techniques.

### 3. Le manifeste dans le bandeau d'encre

Trois formes jouées dans l'application, capturées sur le texte réel :

| Forme | Ce qu'elle donnait | Verdict |
| --- | --- | --- |
| La coque standard des pages statiques | Le manifeste en introduction, sous la bannière | Écartée : il y a le poids d'un chapeau, celui-là même dont la structure A vient de le sortir |
| Un grand texte éditorial, sans bannière | Le manifeste porte la page | Écartée : seule page du site sans bannière, rien ne dit d'un coup d'œil où l'on est |
| **Le bandeau d'encre** | Le manifeste *dans* le bandeau, aux cotes de l'accueil, baseline en pied | **Retenue** : le poids d'une déclaration, et la page est liée à l'accueil par la même forme |

Quatre paragraphes est la limite sur ce fond : au-delà, la lecture en clair sur
sombre fatigue. Le surtitre ne reprend pas `--muted`, calibré pour le fond
clair ; il porte un gris qui rend 7,1:1 sur l'encre.

### 4. « Qui édite ce site », et « Stéphie E. »

Pas « Qui sommes-nous ». La page parle à la première personne du singulier — la
propriétaire écrit elle-même « mon temps libre » — et un « nous » pour une
personne seule est la première chose qu'un lecteur relève.

La première phrase est la sienne, mot pour mot :

> Empreinte politique est un projet indépendant conçu et développé par Stéphie
> E., ingénieure/analyste de données, passionnée par l'Open Data et la
> transparence démocratique.

**Elle signe d'une initiale, et c'est ce qui règle la question des mentions
légales.** Le patronyme n'étant pas publié, la page légale garde sa formulation
sans se contredire. Un test refuse l'ajout du patronyme ici : le faire sans le
demander mettrait les deux pages en désaccord.

Les phrases suivantes — ce dont le projet est indépendant, son statut, et la
raison pour laquelle il existe — sont rédigées d'après l'issue et d'après un
texte long proposé le 18/09/2026.

**Ce texte long n'est pas publié tel quel, et c'est un arbitrage.** Il portait
trois listes — ce que le site refuse de publier, les données et fonctionnalités,
les sources intégrées — qui redisaient `/methodologie` (« Ce que vous ne
trouverez pas ici ») et `/sources` : la duplication que la structure A venait de
supprimer. La page garde ce qui n'existe nulle part ailleurs — la mission, le
but non lucratif, le code public, la phrase sur la polarisation — et renvoie
pour le reste.

**Trois de ses affirmations étaient fausses, vérifiées dans le dépôt, et ne sont
pas publiées** :

| Ce que le texte disait | Ce que le dépôt dit |
| --- | --- |
| « sans intervention ni sélection éditoriale humaine » | `/methodologie` publie l'inverse : le rattachement d'un mandat à un groupe est « une relecture humaine, datée » (#977) |
| « Assemblée nationale **& Sénat** : scrutins officiels, dossiers et mandats » | L'open data du Sénat ne porte **ni scrutin ni prise de parole** ; depuis #885 on n'en collecte que les appartenances |
| « Journal officiel & Open Data gouvernemental » | Le JO est **cité, pas collecté** — un décret par fonction antérieure au corpus, relu à la main (#860) |

Trois sources collectées manquaient aussi à sa liste, et leur attribution est
due : le répertoire national des élus (#922), Wikipédia (la liste des candidats
déclarés, #753) et Wikidata (#757). Enfin « publié en open source » : le dépôt
est public, mais il ne porte **aucun fichier de licence** — la page dit donc
« le code est public », qui est exact.

### 5. La page est servie et référencée

`/a-propos` entre dans `PAGES_FIXES` (`scripts/pages-par-adresse.mjs`) : elle a
donc sa page servie sans JavaScript et sa ligne de sitemap (#969, #1008). Le
pied de page y mène, en tête de la colonne « Le site ». Le bandeau reste à
quatre onglets.

## Ce qui reste ouvert

1. **La place de `/a-propos` dans le bandeau** : une cinquième entrée resserre
   une rangée qui vient d'être arbitrée (#1025). Elle est au pied de page.
2. **La voix de la section** : la phrase de la propriétaire est à la troisième
   personne (« conçu et développé par Stéphie E. »), les deux suivantes à la
   première (« mon temps libre »). Assumé en l'état — la première présente, les
   autres parlent.

## Les garde-fous

`tests/test_a_propos_1032.py` : le manifeste n'est qu'à un seul endroit,
`/methodologie` dit désormais ce que sa page fait, **les ancres profondes citées
par les fiches mènent toutes à une section existante** (la mesure est faite sur
le code, pas sur une liste écrite à la main), la page est servie et référencée,
la section dit « Qui édite ce site » et non « nous », le bandeau porte la
baseline sur fond d'encre, et le surtitre ne garde pas le gris des pages
claires.
