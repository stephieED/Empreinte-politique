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
- **Pas de jargon technique non plus, même hors du dépôt.** Un terme
  d'informaticien ou un anglicisme (« open data », « API », « dataset »,
  « export »), un nom de fichier ou une adresse écrite en toutes lettres ne
  parlent pas au grand public. On dit ce que c'est — « les données que
  l'Assemblée publie en libre accès », « un fichier du site de l'Assemblée » —
  et c'est le lien qui porte l'adresse. Relevé le 22/10/2026 sur le brouillon
  de la source des places de la XIVe, qui écrivait « l'open data de
  l'Assemblée » et `place.txt`. Le terme est déjà sur plusieurs pages : la
  règle vaut pour tout texte écrit ou repris, pas comme un nettoyage d'office.
- **Une phrase courte, une idée par phrase.** Une phrase qui enchaîne deux
  propositions par « et que », « alors que », un deux-points et une parenthèse
  se relit deux fois. Quand une explication demande une formule, c'est un
  tableau ou un exemple chiffré qui la porte, pas la phrase. Relevé le
  22/10/2026 : la règle de filiation des groupes écrite en une phrase (« si au
  moins 60 % des noms de ces deux listes réunies figurent sur les deux ») a été
  jugée illisible ; la version publiée tient en un tableau de trois colonnes et
  deux exemples (#1333).
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
- **Un texte se valide avec la propriétaire avant d'être écrit dans le code**
  (`AGENTS.md` §11). Le but est d'éviter de retoucher le code à chaque
  ajustement de formulation : on s'accorde d'abord, on code ensuite, une fois.
  La façon de le montrer dépend du texte. Une phrase à créer ou à corriger se
  propose directement dans la conversation. Quand la lecture dépend de
  l'endroit où le texte s'affiche — une mention sur une figure, une bulle, une
  légende, un libellé de formulaire —, on le montre en situation, sur une
  maquette ou sur la page en local. C'est souvent le cas, mais ce n'est pas un
  automatisme : écrire dans le code pour pouvoir montrer une phrase revient au
  défaut que la règle évite. Reformulé le 22/10/2026 : « jamais en source »
  avait fait coder deux textes avant tout accord.

**Ce que la garde tient, et ce qu'elle ne tient pas.**
`tests/test_textes_publies.py` refuse six mots sans ambiguïté — pivot, roster,
run, pipeline, workflow, backfill — dans le texte visible des pages, de
l'accueil, des deux fichiers de configuration qui portent du texte publié et
des articles. Elle ne lit pas les composants des fiches, et elle ne peut pas
juger « champ », « fusion » ou « collecte », qui sont aussi des mots courants,
ni le jargon technique et la longueur des phrases :
pour ceux-là, et pour toutes les autres règles, il n'y a que la relecture.
