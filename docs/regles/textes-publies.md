<!-- Ajouté le 07/10/2026 à la demande de la propriétaire. Ces règles ne
viennent pas d'`AGENTS.md` : elles vivaient dans les notes d'une session et ne
se transmettaient à aucune autre. `AGENTS.md` en garde la ligne d'index, sous
le renvoi « AGENTS.md §3g ». -->

# §3g — Les textes publiés sur le site

### 3g. Published site text

**Ces règles ne valent que pour ce que le lecteur du site voit à l'écran.**
Rien d'autre n'est concerné, et les appliquer ailleurs serait une erreur.

| Concerné | Non concerné |
| --- | --- |
| les pages de `web/UI_finale` : accueil, méthodologie, sources, FAQ, à propos, mentions légales | la documentation du dépôt (`docs/`, `README.md`, `AGENTS.md`, `ROADMAP.md`) |
| les fiches : titres de section, libellés, bulles, notes, légendes de figure | les commentaires de code, les messages de commit, les noms de champs et de fichiers |
| les articles de `web/UI_finale/public/rapports/` et leur index | les issues, les PR et leurs commentaires |
| | les réponses à la propriétaire, régies par `AGENTS.md` §9 |
| | les libellés du formulaire de lancement d'un run, qu'elle seule lit |

Dans la colonne de droite, le vocabulaire du dépôt est le bon : « pivot »,
« run », « roster » y sont des termes exacts, et les remplacer par des
périphrases rendrait la documentation moins précise.

**Les règles éditoriales d'`AGENTS.md` §2 passent devant celles-ci.** Elles
disent ce qui peut être publié ; ce fichier dit comment l'écrire.

- **Écrire pour quelqu'un qui n'a pas participé au développement.** Aucun mot
  du dépôt dans un texte publié : pivot, run, roster, pipeline, workflow,
  backfill, et de même champ, fusion, agrégat ou collecte quand ils désignent
  notre fabrication et non la chose dont parle le lecteur. Le mot juste est
  celui de l'institution — séance, scrutin, amendement, groupe — ou celui de
  tous les jours.
- **Reprendre une phrase déjà publiée ne la rend pas lisible.** Sept bulles
  recopiaient la méthodologie mot pour mot ; elles ont été jugées « illisibles
  pour quelqu'un qui n'a pas participé au développement du code »
  (01/10/2026).
- **Un texte d'aide dit d'abord ce que la section présente, puis ses points
  critiques**, en phrases courtes. Une bulle qui ne décrit qu'un élément de la
  section ne suffit pas.
- **Une note aide le lecteur à ne pas mal lire la figure.** Elle définit un
  terme affiché, dit ce qu'une marque représente, ou nomme la conclusion à ne
  pas tirer. Elle ne justifie pas ce qu'on a choisi de ne pas faire, et elle
  n'énonce pas une règle de calcul.
- **Pas de notice sous une figure.** Si une figure a besoin d'un texte pour se
  lire, c'est la figure qu'on reprend ; l'explication de méthode va sur la page
  de méthodologie, avec un renvoi.
- **Un titre décrit, il ne commente pas.** Il dit la période, l'objet ou la
  nature de ce qui suit, jamais son effet ni ce qu'il faut en penser (§2
  règle 1).
- **Entre groupes, rien qui se lise comme un classement** : ni tri par nombre,
  ni compteur dans un titre. Ordre alphabétique ou place dans l'hémicycle ; un
  ratio garde son numérateur et son dénominateur (§2 règle 7).
- **Un seul nom par objet sur une même page.** Un article ne s'appelle pas tour
  à tour « rapport » et « panorama ».
  → `docs/decisions/article-de-type-instantane-1029.md`
- **Le texte se montre rendu avant d'être écrit dans le code**, sur la vraie
  page ou sur une maquette, jamais en source (`AGENTS.md` §11).

**Ce que la garde tient, et ce qu'elle ne tient pas.**
`tests/test_textes_publies.py` refuse six mots sans ambiguïté — pivot, roster,
run, pipeline, workflow, backfill — dans le texte visible des pages, de
l'accueil, des deux fichiers de configuration qui portent du texte publié et
des articles. Elle ne lit pas les composants des fiches, et elle ne peut pas
juger « champ », « fusion » ou « collecte », qui sont aussi des mots courants :
pour ceux-là, et pour toutes les autres règles, il n'y a que la relecture.
