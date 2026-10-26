<a id="fil-d-ariane-a-la-place-du-tiroir-1329"></a>

# Le fil d'Ariane de chaque fiche remplace le tiroir, « Articles » ouvre un bandeau, et les fiches se relient (#1329) (2026-10-26)

`2026-10-26`

> **En bref** — Le site se présente comme un tableau de bord qui relie ce que les sources publient séparément (#1329), mais sa navigation rangeait les fiches par type dans un tiroir, « Chercher ou changer de fiche », et les fiches ne se reliaient presque pas : la fiche de législature ne menait ni à ses gouvernements ni à ses groupes, celle de gouvernement ni à sa législature ni à son groupe majoritaire, celle de groupe à aucune législature. Arbitré sur maquette les 23 et 26/10/2026 (https://claude.ai/artifact/RCG8KrCReJGWBUN4KxN37h) : **le fil d'Ariane de chaque fiche devient le seul endroit pour en changer** (forme A — le type comme le nom ouvrent un menu à deux colonnes, les quatre types à gauche, les fiches du type choisi à droite, la fiche courante cochée), à la place du tiroir ; **« Articles » ouvre un bandeau sombre sous celui du site**, dont la première carte est l'événement des candidats jusqu'au 01/06/2027 ; **les fiches se relient à l'endroit de leurs figures**. La règle de `un-seul-tiroir-pour-choisir-et-chercher-1025` — un seul endroit pour choisir sa fiche — tient ; c'est l'endroit qui change. La recherche reste seule dans le bandeau, et les cases de période vont au bout du fil.

## Ce qui a décidé

La propriétaire, le 26/10/2026, sur la maquette : « A » pour le fil d'Ariane (la
forme B, où le nom n'ouvre que ses voisins du même type, était recommandée et a
été écartée) ; « Le bandeau de l'article est bien » pour « Articles ». La
question « le fil d'Ariane remplace-t-il le tiroir ? » était tranchée par la
planche elle-même, intitulée « à la place du tiroir ».

## La décision

| Endroit | Ce qui change |
| --- | --- |
| Bandeau du site, sur une fiche | Le tiroir et son bouton disparaissent. La recherche (`?mot=`), « Chercher sur cette fiche », prend la place de l'onglet « Explorateur » sur les quatre fiches. Sous 1 024 px de large, le champ devient une loupe qui ouvre le même champ sous le bandeau |
| Recherche sur la fiche de législature | Nouvelle, demandée le 26/10/2026 (la maquette montrait le champ sur cette fiche). Les dossiers dont le titre ne porte pas le mot quittent la vue avant les sections : les textes et le travail des commissions se recalculent, chacun avec l'étiquette « Contenant « … » » ; « En bref », « Qui siégeait » et les articles se retirent ; « Ce qu'on n'a pas pu lire » reste. Un mot sans résultat laisse la section avec sa note |
| Fil d'Ariane (`FilDAriane.jsx`) | Ses deux maillons sont des boutons. Le menu : Groupes, Gouvernements, Législatures ; législatures et gouvernements du plus récent au plus ancien, groupes dans l'ordre alphabétique. Jamais un classement (§2 règle 1). **Les candidats à part** (demandé le 26/10/2026, après la relecture en local) : sur une fiche de candidat, le menu ne montre que les candidats : à gauche deux affichages, « Ordre alphabétique » et « Par groupe » ; à droite, sous « Chercher un candidat », la liste brute ou, par groupe, chaque groupe du site dont au moins un candidat a été membre — lu comme une lignée, dans l'ordre alphabétique — suivi de ses candidats, puis « Autres candidats ». Un candidat passé par deux groupes figure sous les deux. Sur les autres fiches, le menu ne les montre pas |
| Cases « 6 / 12 derniers mois » (#1074) | Elles quittent le tiroir pour le bout du fil d'Ariane, sur les trois fiches datées. Toujours exclusives, toujours dans l'adresse |
| « Articles » | Un bouton qui ouvre une bande `--dark` sous le bandeau, d'un bord à l'autre : l'événement des candidats (même vignette « Mai 2027 », mêmes mots, même date de fin que la première diapositive du carrousel de l'accueil), puis les articles en cartes, du plus récent au plus ancien, et « Tous les articles → » vers l'index. Au-delà de quatre cartes, la rangée défile de côté |
| Fiche de législature | Les noms des gouvernements de la frise mènent à leur fiche ; chaque sigle de l'hémicycle mène à son groupe, sauf les non-inscrits |
| Fiche de gouvernement | Une ligne « Législature » dans « En bref » ; le groupe déclaré majoritaire mène à sa fiche ; chaque barre de la frise des gouvernements mène à la sienne, le précédent et le suivant sont nommés au-dessus |
| Fiche de groupe | Chaque groupe de la lignée mène à la législature où il a siégé |
| Fiches de législature et de gouvernement | « Articles sur cette période », **en fin de fiche**, après « Ce qu'on n'a pas pu lire » : les articles dont la date tombe dans la période ; aucun, aucun encart. Un article publié ne se modifie pas : c'est la fiche qui y renvoie. Proposé dans la maquette sans avoir été arbitré, codé d'abord entre les sections 02 et 03 ; la propriétaire l'a placé en fin de fiche le 26/10/2026 (« A, en fin de fiche »), parce qu'une carte sans numéro coupait la suite des sections |

**`/candidats` n'a plus de fiche par défaut** (demandé le 26/10/2026, après la
relecture en local). L'adresse redirigeait vers la fiche de Jean-Luc Mélenchon,
un choix que rien ne justifiait, et c'est là que menait la carte « Mai 2027 »
du carrousel et du bandeau. Elle montre désormais le fil d'Ariane ouvert sur la
liste des candidats, et rien d'autre (`ChoixDuCandidatPage.jsx`). La page a son
fichier servi au build, sous le titre de la carte qui y mène ; `/groupes` et
`/gouvernements` gardent leur fiche par défaut.

Les quatre barres du tiroir (`CandidatesBar`, `GroupsBar`, `GovernmentsBar`,
`LegislaturesBar`) et le filtre des candidats par groupe qu'elles partageaient
(`GroupFilterContext`) sont supprimés. Les articles sont lus à un seul endroit,
`src/data/articles.js`, pour leurs trois lecteurs.

## Ce que l'implémentation a tranché seule

- **La place des cases de période**, que la maquette ne montrait pas : au bout
  du fil d'Ariane, plutôt que dans le bandeau, où elles ne tenaient pas avec le
  champ et les cinq liens à 1 280 px.
- **La loupe sous 1 024 px**, et non sous 720 px comme les liens : le champ de
  250 px ne tient pas à côté du logo et des liens entre les deux.

## Ce qui n'est pas fait

- Les liens de la fiche candidat vers ses gouvernements et ses législatures,
  proposés dans #1329 : la fiche les nomme sans les rattacher par un
  identifiant, et un rattachement par le nom est interdit
  (`regrouper-nest-pas-joindre-639`).
- Les pages lisibles sans JavaScript ne connaissent pas encore les législatures
  (#1314).

## Alternatives écartées

| Forme | Pourquoi |
| --- | --- |
| Garder le tiroir à côté du fil d'Ariane | Deux endroits pour choisir sa fiche : le défaut que #1025 avait corrigé |
| Fil d'Ariane forme B (le nom n'ouvre que ses voisins du même type) | Écartée par la propriétaire au profit de A |
| « Articles » en menu déroulant sous le bouton | « j'avais autre chose en tête » |
| Relier le bandeau au carrousel de l'accueil | Écarté le 26/10/2026 |
