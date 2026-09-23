<a id="article-de-type-instantane-1029"></a>

# Un article, de type « instantané » (#1029) (2026-09-23)

`2026-09-23`

> **En bref** — La page publiée le 23/09/2026 se nommait elle-même de trois façons : « Instantanés » dans la barre du site et dans l'index, « ce rapport » dans un titre de section, « ce panorama » dans le chapeau. Tranché par la propriétaire le 23/09/2026 : **ce qui est produit est un article, et « instantané » est son type** — « on mesure un instant ». Le texte publié dit donc **article** pour l'objet et **instantané** pour ce qu'il mesure : l'onglet du site s'appelle **« Articles »**, l'index **« Les articles »**, et chaque entrée porte son type. « rapport » et « panorama » disparaissent des pages. L'adresse `/rapports`, le dossier, le script et les tests gardent leur nom : ce sont des identifiants, pas des mots lus. `tests/test_rapports_publies.py` refuse une page dont le TEXTE VISIBLE nomme son objet autrement. **Deux points de `docs/decisions/instantanes-publies-1029.md` sont remplacés** : l'onglet ne s'appelle plus « Instantanés », et la méta `instantane:periode` devient `article:periode`, à côté de `article:type`.

## Le contexte

Trois mots pour un objet, sur la même page, tous écrits de bonne foi à quelques
heures d'intervalle : le titre de la section venait du premier jet, le chapeau
d'une relecture, la barre du site de la décision qui a créé le dossier
(`docs/decisions/instantanes-publies-1029.md`). Aucun n'était faux ; ensemble
ils empêchaient de savoir comment la chose s'appelle.

Deux mots étaient en lice pour l'objet, « instantané » et « article », et la
propriétaire les a réconciliés plutôt que choisis : ce ne sont pas deux noms
concurrents, ce sont **deux niveaux**. L'article est le format — une page qu'on
lit, qu'on partage, qui porte un titre et un chapeau. L'instantané est le type
de mesure : un état du corpus à une date, jamais mis à jour.

## La décision

- **Le texte publié dit « article »** pour l'objet : « Ce que cet article ne dit
  pas », « cet article liste les interventions ».
- **Le type est nommé là où il se lit** : le sur-titre porte « Empreinte
  politique · instantané · données du 23 septembre 2026 », et l'index le définit
  une fois — « un instantané est un article qui mesure un instant : il dit
  l'état du corpus à sa date, et n'est jamais mis à jour ».
- **« rapport » et « panorama » ne sont plus des mots publiés.** Un test relit le
  TEXTE VISIBLE de chaque page — balises retirées — et refuse le nom seul ; il
  laisse passer « rien n'est rapporté à un possible », qui est une phrase de la
  page et non un nom.
- **L'onglet du site s'appelle « Articles »**, et la page qu'il ouvre
  « Les articles ». Un bouton et sa destination doivent dire la même chose ;
  « Articles » d'un côté et « Les instantanés » de l'autre aurait recréé, entre
  deux écrans, l'écart que cette décision ferme dans une page.
- **Chaque entrée de l'index porte son type**, lu dans la page :
  « Instantané · données au 23 septembre 2026 · période du 23 mars au
  23 septembre 2026 ». Le type vient d'une `<meta name="article:type">` et
  **n'est jamais deviné** : une page qui n'en déclare pas n'en affiche pas
  (§2 règle 5). Un défaut « Instantané » aurait étiqueté d'office le premier
  article d'un autre type.
- **Les identifiants ne bougent pas** : `/rapports`, `public/rapports/`,
  `index-rapports.mjs`, `test_rapports_publies.py`. Une adresse n'est pas un mot
  lu, et la renommer casserait un lien déjà partagé pour un gain nul. La méta,
  elle, change de préfixe — `instantane:periode` devient `article:periode` —
  parce qu'elle décrit le format et qu'aucun consommateur extérieur ne la lit.

Ce que la décision ouvre, sans le trancher : **le type laisse la place à
d'autres**. Un article qui suivrait un sujet sur plusieurs mois ne serait pas un
instantané, et il n'aurait pas à se nommer ainsi pour vivre dans le même
dossier. Rien n'est construit pour cela aujourd'hui — l'index ne porte pas de
type, il liste des pages.

## L'alternative écartée

**Renommer l'adresse en `/articles`.** Elle aurait dit la même chose que le
texte, et le coût était nul le jour même — rien n'était encore en ligne. Écarté
parce que le gain l'est aussi : personne ne lit une adresse pour savoir ce
qu'est une page, et le dossier `rapports/` est le seul endroit où le mot
survit, hors de toute phrase.

**Garder « rapport » et renoncer à « instantané ».** C'était le mot du premier
jet, et il a l'avantage d'être compris sans explication. Écarté : « rapport »
dit qu'on a rédigé un avis sur un sujet, là où la page extrait et date. Le mot
porte exactement la promesse que la ligne éditoriale refuse (§2 règle 1).
