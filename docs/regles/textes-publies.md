<!-- Ajouté le 07/10/2026 à la demande de la propriétaire. Ces règles ne
viennent pas d'`AGENTS.md` : elles vivaient dans les notes d'une session et ne
se transmettaient à aucune autre. `AGENTS.md` en garde la ligne d'index, sous
le renvoi « AGENTS.md §3g ». -->

# §3g — Les textes publiés sur le site

### 3g. Published site text

**Ces règles s'appliquent particulièrement pour les sessions UI et COM.**
`AGENTS.md` §11 importe ce fichier : Claude Code le charge au démarrage de
chaque session, avant tout texte proposé pour le site.

**Avant de proposer le moindre texte pour le site, charge la skill
`textes-du-site`** (`.claude/skills/textes-du-site/`). Ce fichier dit ce qui
est permis ; la skill dit comment l'écrire, d'après les corrections de la
propriétaire, et chaque correction nouvelle s'y ajoute.

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

- **Le lecteur ne sait rien du projet.** « Un lecteur qui arrive sur la page ne
  sait probablement rien du projet. Il ne faut pas qu'il soit perdu au premier
  regard » (22/10/2026, accueil #1329). Chaque texte se relit avec ses yeux à
  lui, pas avec ceux de qui connaît les fiches.
- **Avant d'écrire, savoir ce que le lecteur doit comprendre.** Un encadré, une
  bulle ou une légende dont le but n'est pas dit se réécrit sans fin : sept
  formes ont été refusées le 08/10/2026 avant que l'intention soit énoncée (« que
  le lecteur puisse comprendre la représentativité de la Commission »). La
  question se pose d'abord ; le texte vient ensuite.
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
- **Les tics d'un modèle de langage se corrigent avant de proposer un texte.**
  Un lecteur du fil r/developpeurs a écrit, le 30/10/2026 : « rendu encore plus
  compliqué par l'IA qui pond du texte pour expliquer le texte qui expliquait le
  texte d'avant […] je prendrai comme argent comptant une infographie de ce
  genre sur lemonde.fr, mais pas la même infographie présentée sur un site
  inconnu (qui en plus a des tournures de LLM dans ses textes) ». Deux
  relectures extérieures (GPT et Gemini, 30/10/2026) ont relevé ces tournures
  sur tout le site. Ce sont celles de l'agent qui rédige, et elles entament la
  confiance avant qu'un seul chiffre soit lu. Avant de proposer un texte, le
  relire contre ce tableau ; un texte qui porte l'un de ces tics se réécrit
  d'abord.

  | Tic | Relevé sur le site | À la place |
  | --- | --- | --- |
  | La négation d'abord : « X n'est pas Y », « ne veut pas dire », « ce n'est pas X, c'est Y », « et non X », « X, pas Y » | « Une fonction longue n'est pas une fonction plus importante » ; une vingtaine dans la méthodologie | dire ce qui est. Une négation ne reste que si elle empêche une mauvaise lecture précise (« un texte arrêté n'est pas rejeté »), une fois, là où la figure la demande |
  | Le tiret long d'incise (« — ») | 26 dans la méthodologie, 10 dans les mentions légales | une virgule, une parenthèse, ou deux phrases |
  | La phrase-chute, le miroir, l'aphorisme | « un vote absent ne dit rien, un vote attribué à tort affirme… » ; « cinq notes sont un classement » ; « faire passer une ignorance pour un fait » ; le titre « Trois vides, trois causes » | le fait, dit sans effet |
  | Le deux-points qui annonce une révélation | « Les limites de cette fiche : … » ; « Deux étapes, deux sources : … » | une phrase directe |
  | Les énumérations par trois ou quatre, « ni… ni… ni » | « ni total, ni rang, ni comparaison entre personnes » | ce qui est nécessaire, pas le rythme |
  | Les mots d'insistance | réellement, simplement, pleinement, elle-même, « pour ce qu'il est » ; « jamais » 24 fois dans la méthodologie | les retirer |
  | Le gras à répétition | 50 passages en gras dans la méthodologie, 24 dans les mentions légales | les noms et les chiffres qui portent la phrase, pas plus |
  | La phrase qui s'annonce | « Cette page dit comment chaque fiche est faite… » ; « Cet article montre… » | commencer par le contenu |
  | La justification de fabrication à l'écran | « Écrire « membre » partout ferait lire une distinction… » ; « choisir les faits qui arrangent serait pire… » ; « Nous préférons ce manque… » | la méthodologie, ou rien (voir « Une note aide le lecteur à ne pas mal lire la figure ») |
  | La formule de communication | « s'inscrit dans une logique de lutte contre », « Focus sur », « l'univers retenu » | le mot de tous les jours |
  | La redite d'une page à l'autre | « ni note ni classement » ou « aucun taux de présence » redits à six ou sept endroits | un endroit ; ailleurs, un lien |
  | Plusieurs voix | « mon temps libre », « nous » et « Empreinte politique » sur des pages voisines | une voix par page |
  | La promesse plus large que le fait | « 100 % automatisé », « aucun fait n'est écrit ni corrigé à la main », « et la fiche le dit », alors que des mandats sont relus à la main et qu'aucune fiche ne le dit | n'écrire une promesse qu'après avoir vérifié qu'elle est vraie partout |

  Les chiffres de la colonne du milieu sont ceux des rapports (30/10/2026),
  comptés sur le code source. `tests/test_textes_publies.py` tient un cliquet
  sur les deux tics qui se comptent sans lire, le tiret long et la négation
  (« n'est pas », « ne veut pas dire ») : leur nombre ne peut que baisser.
  Tout le reste ne se voit qu'à la relecture.
- **Du concret, pas de quantificateur flou.** « La plupart », « compte
  surtout » font lire une formule « fumeuse » ou « alambiquée » (ses mots,
  22/10/2026, sur l'explication de la filiation des groupes). On dit le chiffre,
  le seuil, l'exemple.
- **Reprendre une phrase déjà publiée ne la rend pas lisible.** Sept bulles
  recopiaient la méthodologie mot pour mot ; elles ont été jugées « illisibles
  pour quelqu'un qui n'a pas participé au développement du code »
  (01/10/2026).
- **Un texte d'aide dit d'abord ce que la section présente, puis ses points
  critiques**, en phrases courtes. Une bulle qui ne décrit qu'un élément de la
  section ne suffit pas : « Il faut quelque chose qui va expliquer la fonction
  générale de cette section » (01/10/2026).
- **« En bref » dit ce que l'objet est, jamais son activité.** La carrière d'une
  personne, l'effectif des maillons d'une lignée, la composition d'un
  gouvernement dans le temps ; l'activité vit dans les sections suivantes. Trois
  formes refusées sur la fiche de gouvernement (#330) avançaient l'activité.
- **Rien qui redise l'écran.** Une bulle, une note ou un libellé n'ajoute pas ce
  que la figure montre déjà : le sigle et le nombre d'un groupe écrits sur
  l'hémicycle ne se répètent pas dans sa bulle.
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
- **Un article se vérifie au téléphone avant d'être publié**, pas seulement à
  l'ordinateur. À 390 et à 360 px : la page ne déborde pas de l'écran, aucune
  figure ni aucun tableau ne défile de côté, aucun texte ne rend sous 13 px
  (SVG compris : taille × échelle d'affichage), les cibles se touchent au doigt
  (24 px). Une figure trop large se redessine à la largeur — cadre resserré,
  version réservée au téléphone, tableau en lignes —, elle ne se réduit pas
  jusqu'à l'illisible. Les règles vivent dans un bloc
  `@media (max-width: 720px)` de l'article ; à 1 280 px, rien ne change.
  `tests/test_articles_au_telephone_1372.py` refuse un article sans bloc
  téléphone ; le reste ne se voit qu'à l'écran.
  → `docs/decisions/articles-au-telephone-1372.md`
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
- **Ses formulations se reprennent mot pour mot.** Quand la propriétaire donne
  les mots d'un titre ou d'un libellé, on les applique tels quels ; on ne
  corrige que l'accord ou la ponctuation, en le disant. Une objection de fond
  se dit en une phrase, à côté de sa version, jamais à la place (« Je ne
  comprends pas pourquoi tu t'es autant écarté de ma proposition », 09/10/2026).

**Ce que la garde tient, et ce qu'elle ne tient pas.**
`tests/test_textes_publies.py` refuse six mots sans ambiguïté — pivot, roster,
run, pipeline, workflow, backfill — dans le texte visible des pages, de
l'accueil, des deux fichiers de configuration qui portent du texte publié et
des articles. Elle ne lit pas les composants des fiches, et elle ne peut pas
juger « champ », « fusion » ou « collecte », qui sont aussi des mots courants,
ni le jargon technique et la longueur des phrases :
pour ceux-là, et pour toutes les autres règles, il n'y a que la relecture.
