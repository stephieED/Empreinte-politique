<a id="rattachement-au-dossier-interventions-et-scrutins-639"></a>

# Rattacher une intervention ou un scrutin à son dossier : les deux volets restants sont écartés, mesure à l'appui (#639) (2026-09-01)

`2026-09-01`

> **En bref** — instruction, pas implémentation : #639 portait quatre matières, deux sont livrées et revérifiées ici (`textes_portes[]` **472 / 472**, table `textes` des index d'amendements à 6 · 777 · 444 · 565 entrées), les deux autres sont **écartées avec leur condition de réouverture** ; **interventions** — 0 des **652 703** entrées publiées des 481 profils porte un `dossier_id`, et le balayage **exhaustif** des 1 206 comptes rendus Syceron en cache (605 XVIe + 601 XVIIe, jamais un échantillon de 40) rend **0** occurrence de `DLR5L`, `PRJLANR5`, `PIONANR5`, `PNREANR5` ou `ODJ`, la seule référence structurée étant l'uid de la réunion ; la route `seance_ref` **existe** (12 629 `reunionRef` + 10 328 `odjRef` sur les 10 967 dossiers des trois archives, 87,2 % rattachés à un seul dossier) mais son plafond honnête est **631 / 652 703 = 0,097 %** — 8 283 entrées portent une référence de séance (les 636 461 entrées `roster_groupe` n'en portent aucune, `_reduire_au_theme` la retire avec les champs lourds, #657), 7 484 tombent sur une séance qu'un dossier référence, et **une séance ne traite pas un dossier** : 345 des 568 séances citées (60,7 %) portent plusieurs points d'ordre du jour, où siègent **6 742 des 8 283** entrées (81,4 %) ; `bibard` est écarté deux fois — c'est un fragment d'affichage (`' (n[[o]]\xa02915 rectifié)'`, vide ou blanc sur 4 786 / 23 145 points de la XVIe) et le numéro seul n'identifie pas un document (1,9 à 3,1 % des couples *(législature, numéro)* en désignent plusieurs) ; **scrutins** — 0 des 17 748 publiés porte un `texte_lie_id` et les 66 motions de censure ont toutes **le motif déclaré, aucune le lien** ; le lien inverse remesuré rend **706 / 17 748 (3,98 %)** et non 715 ni 760 (710 `voteRef` distincts, 558 dossiers, **0 / 792** en XIVe ; le « 34 676 dossiers » cité était le nombre d'**entrées** des archives, la population étant 10 967), `dossierRef` n'est **pas remesurable hors ligne** (les archives brutes XV-XVII ne sont pas sur disque, `_parse_scrutins_zip` n'en garde qu'une projection — trou déclaré, aucun appel réseau) mais la borne de mars 2026 est **corroborée indirectement** : 2 606 des 17 748 scrutins publiés sont datés du 01/03/2026 ou après, à deux unités des 2 608 mesurés porteurs du champ ; l'union des deux routes sourcées plafonne à **3 234 / 17 748 (18,2 %)** et laisse **14 514 (81,8 %)** sans rattachement, dont **792 / 792 (100 %) de la XIVe**, sur un corpus qui court du 03/07/2012 au 21/07/2026 ; **le coût n'est pas l'obstacle** — +2,42 Mio sur `scrutins.json` (9,75 → 12,17) et +36,3 Mio sur les 481 socles pour 1 312 951 votes, contre un plus gros fichier versionné à 48,1 Mio et des seuils de `garde_fou_blobs` à 50 / 80 —, l'obstacle est éditorial ; **une borne déclarée ne suffit pas** parce que le vide est la règle et non une frange, parce que `LISTES_COUVERTES` indexe cinq **listes** et pas des champs (la borne `votes` « couvert depuis 2012-06-20 » est vraie : ce qui manque est un champ du vote), et parce que le lecteur lit la page d'une loi, pas l'en-tête d'un fichier — la vue « votes groupés par loi » est donc **impraticable par clé sourcée** et n'en a pas besoin, `regrouper-nest-pas-joindre-639` l'ayant déjà servie à 99,4 % par regroupement d'intitulés ; le remède de #639 « un cache sans le champ est refusé » **ne se transpose pas** à `dossier_id`, absent par nature des archives XIV-XVI, où il rejetterait les trois index figés à perpétuité ; conditions de réouverture écrites et conjointes des deux côtés, et trois trous nommés (le champ sur les archives XV-XVII, `vp/reunions/Agenda.json.zip` toujours non vérifié, le rendement d'une recollecte).

#639 demandait de propager un identifiant de dossier législatif sur **quatre**
matières. Deux sont livrées et vérifiées le 01/09/2026 sur `pivot_data/` au SHA
`8c4e705c` : `textes_portes[]` porte son `dossier_id` sur **472 des 472 entrées
publiées** des 481 profils, et la table `textes` des index d'amendements est
renseignée (6 · 777 · 444 · 565 entrées pour les législatures 14 · 15 · 16 · 17).
Les deux autres — **les interventions** et **les scrutins** — ne le sont pas.

Ce fichier dit si elles *peuvent* l'être. **Le verdict est négatif sur les deux**,
et il est écrit ici plutôt que laissé implicite pour que l'instruction ne soit pas
repayée : « on a regardé, et non, pour ces raisons » vaut autant qu'une décision.
Chaque volet porte sa **condition de réouverture** — un écart sans condition
devient définitif par omission, ou se rouvre au premier prétexte.

## Comment lire les chiffres

Toutes les mesures ci-dessous ont été **refaites** le 01/09/2026, sans aucun appel
réseau, sur : les 481 profils pivots (468 `roster_groupe`, 13 `candidat_declare`),
`pivot_data/scrutins.json`, les 481 socles bruts (880 Mo), les trois archives
`Dossiers_Legislatifs` en cache (10 967 dossiers parlementaires, 23 709 documents),
les **1 206** comptes rendus Syceron en cache (605 en XVIe, 601 en XVIIe), et
l'archive brute des scrutins de la XIVe — la seule conservée sur disque.

**Ce qui n'a pas pu être remesuré est dit à sa place**, jamais recopié en silence.

## Volet A — les interventions

### Le constat de départ se reproduit, et il se précise

| Population | Mesure |
| --- | ---: |
| Interventions publiées (481 profils) | **652 703** |
| dont un `dossier_id` non nul | **0** |
| dont un bloc `seance` avec `ref` | **8 283** (1,27 %) |
| dont un `dossier.point_ordre_du_jour` (texte libre) | 15 234 |

Le corpus se sépare en deux, et c'est décisif : les **636 461** entrées des 468
profils `roster_groupe` portent `collecte: "theme_seul"` (#657) et **aucun bloc
`seance`** — `_reduire_au_theme` retire `seance_ref` avec les autres champs
lourds, ce que sa docstring dit mot pour mot. La route « séance » ne peut donc
atteindre, aujourd'hui, que les **16 242** entrées des 13 candidats déclarés, dont
8 283 portent une référence de séance.

### Syceron ne publie aucune référence de dossier — balayage exhaustif

Les 1 206 comptes rendus **entiers** du cache, et non un échantillon de 40 :

| Chaîne cherchée | XVIe (605 CR) | XVIIe (601 CR) |
| --- | ---: | ---: |
| `DLR5L` (dossier) | **0** | **0** |
| `PRJLANR5` / `PIONANR5` / `PNREANR5` (document) | **0** | **0** |
| `ODJ…` (ordre du jour) | **0** | **0** |
| `RU[AS]NR5L…` (réunion) | 604 | 601 |

Une seule référence structurée par compte rendu, et c'est l'uid de la **réunion**.
Les balises `<point>` et `<texte>` ne portent aucun attribut de référence : leurs
attributs sont `nivpoint`, `valeur_ptsodj`, `code_grammaire`, `sommaire`,
`bibard`, `art`, `adt`, `ssadt`, `structure`, `orateur`.

### `seance_ref` ouvre bien une route sourcée — son plafond est 0,097 %

C'est la piste que le lot devait instruire, et elle **existe** : les dossiers
référencent leurs réunions. Sur les trois archives en cache, 12 629 occurrences de
`reunionRef` et 10 328 de `odjRef` donnent **15 907 références de réunion
distinctes**, dont 13 875 (87,2 %) rattachées à un seul dossier.

Jointe au corpus publié :

| Étape | Interventions publiées | Part des 652 703 |
| --- | ---: | ---: |
| portent un `seance.ref` | 8 283 | 1,27 % |
| … dont la séance est référencée par au moins un dossier | 7 484 | 1,15 % |
| … dont **un seul** dossier référence la séance | 4 554 | 0,70 % |
| … dont la séance ne porte **qu'un** point d'ordre du jour | 1 541 | 0,24 % |
| **… les deux conditions à la fois** | **631** | **0,097 %** |

Les deux dernières lignes sont le cœur du verdict, et la seconde ne figurait dans
aucune instruction précédente. **Une séance ne traite pas un dossier.** Sur les
568 séances que le corpus publié cite, **345 (60,7 %) portent plusieurs points
d'ordre du jour distincts** — jusqu'à 22 — et **6 742 des 8 283** interventions
concernées (81,4 %) sont assises sur une de ces séances. Rattacher une
intervention à un dossier parce que sa séance y touche imputerait à ce dossier des
prises de parole que la source range elle-même sous un autre point de la même
séance : une affirmation qu'aucune source ne fait (§2 règle 2).

Le plafond honnête de la route est donc **631 interventions publiées sur 652 703**.

### L'attribut `bibard` est écarté deux fois

C'est le seul autre porteur possible, au niveau du point. Il est écarté sur deux
motifs indépendants :

1. **Sa forme est un fragment d'affichage**, pas une clé :
   `' (n[[o]]\xa01364)'`, avec balisage `[[o]]`, espace insécable et suffixes en
   texte libre (`' (n[[o]]\xa02915 rectifié)'`). Il est vide ou blanc sur
   4 786 des 23 145 `<point>` de la XVIe et 6 496 des 22 021 de la XVIIe. En
   extraire le numéro, c'est analyser un libellé — le garde-fou explicite de #639,
   et ce que #672 a coûté.
2. **Le numéro seul n'identifie pas un document.** Mesuré sur les documents des
   trois archives, le couple *(législature, numéro)* est ambigu sur 157 des 5 050
   couples de la XVe (3,1 %), 80 des 2 997 de la XVIe (2,7 %) et 66 des 3 508 de
   la XVIIe (1,9 %) — `PRJLANR5L15B3583`, `ETDIANR5L15B3583` et `AVCEANR5L15B3583`
   partagent le numéro 3583, et le préfixe de type n'est pas dans `bibard`.

### Verdict — volet A

**Écarté.** L'Assemblée ne publie, à ce jour, aucune référence de dossier au
niveau d'une intervention ni au niveau d'un point d'ordre du jour ; la seule route
sourcée passe par la séance, elle plafonne à **631 des 652 703 interventions
publiées (0,097 %)**, et elle est ambiguë sur 81,4 % des interventions qu'elle
touche.

**Condition de réouverture — les deux, conjointes :**

1. l'Assemblée publie une référence **au niveau du point**, portant un uid de
   document ou de dossier. Critère mesurable, hors ligne, sur le cache Syceron :
   la chaîne `DLR5L`, `PRJLANR5`, `PIONANR5` ou `PNREANR5` apparaît dans au moins
   un compte rendu. Aujourd'hui : **0 sur 1 206**. Le jeu
   `.../{leg}/vp/reunions/Agenda.json.zip` reste le seul autre endroit possible,
   et il reste **non vérifié** (voir `hors-perimetre.md`, § *Agenda / committee
   meetings dataset*) ;
2. **et** le corpus publié porte une référence de séance sur davantage que les
   8 283 entrées d'aujourd'hui — c'est-à-dire que la forme réduite de #657
   s'élargit, ou que les 468 profils `roster_groupe` sont recollectés en forme
   pleine.

La conjonction est le point important : la première condition **seule** ne
plafonne plus à 0,097 % mais à 1,27 %, et la seconde seule ne lève pas
l'ambiguïté de la séance. Élargir la forme réduite pour ce seul motif est refusé
ici : cela coûte une recollecte complète des 468 profils, et la fusion additive
garde l'entrée *ancienne*, donc les 636 461 entrées déjà publiées n'y gagneraient
rien sans un report nommé (le trou de #492, #639 et #641, trois fois au même
endroit).

## Volet B — les scrutins

### Ce que le corpus publié porte

| Population | Mesure |
| --- | ---: |
| Scrutins publiés (`pivot_data/scrutins.json`) | **17 748** |
| avec un `texte_lie_id` | **0** |
| motions de censure (`type_vote`) | 66 |
| … dont un `texte_lie_id` | **0** |
| … dont un `texte_lie_non_resolu` **avec motif déclaré** | **66** |

Précision utile : les 66 motions n'ont pas « un lien **ou** un motif », elles ont
toutes **le motif**, aucune le lien. Et le fichier porte quatre clés —
`schema_version`, `genere_le`, `licence_donnees`, `scrutins` : **aucun bloc de
couverture**, ce que `regrouper-nest-pas-joindre-639.md` avait déjà relevé et qui
reste vrai.

### Les trois routes, et laquelle se remesure hors ligne

| Route | Mesure du 01/09/2026 | Remesurée ici ? |
| --- | ---: | --- |
| `objet.dossierLegislatif.dossierRef` | — | **non**, voir ci-dessous |
| Lien inverse dossier → scrutin (`voteRefs.voteRef`) | **706 / 17 748** (3,98 %) | **oui** |
| Reconnaissance par intitulé | 17 634 / 17 748 (99,4 %, #639) | non — et **interdite comme solution** |

**`dossierRef` n'est pas remesurable sur ce poste.** Les archives brutes de
scrutins des XVe, XVIe et XVIIe ne sont pas sur disque : `_parse_scrutins_zip` ne
conserve qu'une projection (`numero`, `date`, `titre`, `sort`, `legislature`, plus
`type_scrutin`, `type_vote`, `demandeur` depuis #639), et les index figés
committés portent la même. Les vérifier exigerait de retélécharger
`{leg}/loi/scrutins/Scrutins.json.zip` : **aucun appel réseau n'a été fait**, et
le trou est déclaré ici plutôt que comblé par recopie.

Ce qui a pu être vérifié, et qui l'a été :

- **la XIVe**, seule archive brute conservée : `objet` ne porte que `libelle` et
  `referenceLegislative`, cette dernière **nulle sur 1 354 / 1 354** ; la chaîne
  `dossierRef` apparaît **0 fois** dans l'archive entière, et `DLR5L` **0 fois**
  également. La clé n'y figure pas — mesure reproduite, pas recopiée ;
- **une corroboration indirecte, indépendante et hors ligne**, de la borne de mars
  2026 : les scrutins publiés datés du 01/03/2026 ou après sont **2 606 sur
  17 748 (14,7 %)**, à deux unités des 2 608 scrutins bruts de la XVIIe que la
  propriétaire a mesurés porteurs d'un `dossierRef`. Deux populations différentes,
  deux méthodes différentes, un même ordre de grandeur : la borne tient.

**Le lien inverse ne reproduit ni 715 ni 760.** Mesuré ici sur les 10 967 dossiers
des trois archives : 771 nœuds `voteRefs`, **710 `voteRef` distincts** (dont 3 du
Sénat), 707 convertibles en identifiant AN publié, **706 retrouvés parmi les
17 748 scrutins publiés**, portés par **558 dossiers**, 13 référencés par deux
dossiers. Répartition : **0 / 792** en XIVe, 251 / 4 417 en XVe, 205 / 4 105 en
XVIe, 250 / 8 434 en XVIIe. Le « 34 676 » cité comme dénombrement de dossiers est
en réalité le nombre d'**entrées** des trois archives (documents compris) ; la
population des dossiers est 10 967.

### Le coût n'est pas l'obstacle, et il faut le dire

| Poste | Mesure |
| --- | ---: |
| `pivot_data/scrutins.json` avec un `dossier_id` par scrutin | 9,75 → **12,17 Mio** (+2,42) |
| Report du champ dans chaque vote de profil brut (1 312 951 votes, 481 socles) | **+36,3 Mio** sur 880 Mo |
| Plus gros fichier versionné aujourd'hui | **48,1 Mio** (`pivot_data/amendements/15.json`) |
| Seuils de `src/garde_fou_blobs.py` | avertit 50 Mio · **échoue 80 Mio** |

Aucun des deux postes ne déplace le plus gros fichier versionné, et `scrutins.json`
resterait quatre fois sous le seuil d'alerte. Le transit par le profil brut n'est
pas optionnel : `build_scrutins_index.py` construit l'index pivot **depuis les
profils bruts** et ne lit jamais le cache de scrutins — c'est exactement le maillon
où #639 avait perdu `type_scrutin`.

Le coût réseau, lui, est **borné et connu** : les législatures 14, 15 et 16 sont
figées (`raw_data/scrutins_an_figes/`, 3,3 Mio gzippés), et la XVIIe est
retéléchargée à chaque run de toute façon. Mais un piège s'y cache et mérite d'être
nommé : le remède de #639 — « un cache qui ne porte pas la qualification est
refusé, jamais relu » — **ne se transpose pas** à `dossier_id`. Le champ n'existe
pas dans les archives des XIVe, XVe et XVIe ; un refus indexé sur sa présence
rejetterait les trois index figés **à perpétuité**, et rebâtir ces trois index
n'achèterait rien.

### Le faux vide : mesuré, et il n'est pas au bord du corpus

C'est la question que ce lot devait trancher. Les deux routes sourcées réunies, au
mieux :

| | Scrutins publiés | Part |
| --- | ---: | ---: |
| A. lien inverse (mesuré) | 706 | 3,98 % |
| B. fenêtre ≥ 2026-03-01 (proxy de `dossierRef`) | 2 606 | 14,68 % |
| A ∩ B | 78 | — |
| **A ∪ B** | **3 234** | **18,22 %** |
| **Sans aucun rattachement sourcé** | **14 514** | **81,78 %** |

Et sa forme par période, qui est le contresens lui-même :

| Législature | Sans rattachement | Part de la législature |
| --- | ---: | ---: |
| XIVe | 792 / 792 | **100 %** |
| XVe | 4 166 / 4 417 | 94,3 % |
| XVIe | 3 900 / 4 105 | 95,0 % |
| XVIIe | 5 656 / 8 434 | 67,1 % |

Le corpus publié s'étend du 03/07/2012 au 21/07/2026. **Le rattachement n'existe
que sur les cinq derniers mois.** Une vue « les votes de cette loi » afficherait
donc, pour toute loi antérieure à mars 2026 — c'est-à-dire quatorze années sur
quatorze —, « aucun vote rattaché », mot pour mot ce qu'elle afficherait pour une
loi sur laquelle personne n'a voté. C'est ce que §2 règle 5 interdit.

### Une borne déclarée ne suffit pas, et voici pourquoi

La parade normale serait une borne datée sur le modèle du bloc `couverture`. Elle
ne suffit pas, pour deux raisons mesurées et une raison de structure :

1. **Le vide n'est pas une frange, c'est la règle** : 81,8 % du corpus, et 100 %
   d'une législature entière. Une borne qualifie une exception ; ici elle
   qualifierait le cas général.
2. **`couverture` est indexé sur cinq listes métier, pas sur des champs**
   (`LISTES_COUVERTES` : `mandats`, `votes`, `textes_portes`, `interventions`,
   `amendements`). La borne existante sur `votes` dit « couvert depuis le
   20/06/2012 », et elle est **vraie** : les votes sont bien collectés depuis
   2012. Ce qui manque depuis 2026 n'est pas le vote, c'est **un champ du vote**.
   Déclarer cela demande un objet que le schéma n'a pas.
3. **Le lecteur ne lit pas l'en-tête d'un fichier, il lit la page d'une loi.**
   Une borne posée sur `scrutins.json` est honnête au niveau du fichier et muette
   à l'endroit où le contresens se produit.

**Donc : la vue est impraticable par clé sourcée tant que les anciennes
législatures ne sont pas couvertes — et elle n'en a pas besoin.**
`regrouper-nest-pas-joindre-639.md` a déjà tranché que regrouper des scrutins
entre eux **par leur propre intitulé** est légitime, atteint 99,4 % et se déclare.
Publier en plus un `dossier_id` sur 18 % des scrutins ne rendrait pas la vue
possible : elle produirait un **troisième** défaut, une page où certaines lois
portent un lien sourcé et les autres un simple regroupement, sans que rien ne dise
au lecteur laquelle il regarde.

### Verdict — volet B

**Différé, et le report est reconduit avec sa mesure**, non par reconduction
tacite. Le rang 4 de #639 reste différé pour la raison déjà écrite, à laquelle ce
lot ajoute trois faits : la couverture réunie plafonne à 18,2 %, le vide est de
100 % sur une législature entière, et le coût volumétrique n'est **pas**
l'obstacle — l'obstacle est éditorial.

**Condition de réouverture — les trois, conjointes :**

1. l'Assemblée renseigne `objet.dossierLegislatif.dossierRef` sur une législature
   **close** avant 2026. Critère mesurable sur l'archive : aujourd'hui **0** sur
   la XIVe (vérifié ici), et 0 sur les XVe et XVIe (mesure de la propriétaire,
   non reproduite faute d'archive sur disque) ;
2. **et** le taux de rattachement cesse d'être disjoint par période — aujourd'hui
   0 % · 5,7 % · 5,0 % · 30,9 % sur quatre législatures. Aucun seuil n'est posé
   ici : la clause est qualitative parce qu'un seuil inventé serait un arbitrage
   éditorial déguisé en mesure, ce que #649 a déjà tranché sur le contrôle de
   perte ;
3. **et** `pivot_data/scrutins.json` sait porter une borne de couverture **au
   niveau du champ**, lue par la vue à l'endroit où elle rend une loi — pas
   seulement posée dans l'en-tête du fichier.

Le lien inverse (706 scrutins) est disponible **aujourd'hui**, sans un octet
téléchargé. Il n'est pas publié séparément, et c'est délibéré : seul, il produit
le même faux vide sous une forme pire (0 % sur la XIVe, ~5 % sur les XVe et XVIe),
pour 4 % de couverture.

## L'alternative écartée

| Alternative | Écartée parce que |
| --- | --- |
| Une clé tirée de l'intitulé du scrutin (99,4 %) | Une clé dérivée d'un libellé n'est pas une clé sourcée (§2 règle 2). Garde-fou explicite de #639, coût payé par #672. Reste une **mesure de faisabilité** |
| Le numéro extrait de `bibard` pour les interventions | Même motif, plus une ambiguïté propre : 1,9 à 3,1 % des couples *(législature, numéro)* désignent plusieurs documents |
| Rattacher une intervention au dossier de sa séance | 81,4 % des interventions concernées siègent dans une séance à plusieurs points d'ordre du jour : ce serait imputer à un dossier des paroles que la source range ailleurs |
| Publier `dossier_id` sur les scrutins derrière une simple borne datée | Le vide couvre 81,8 % du corpus et 100 % d'une législature ; `couverture` ne sait pas déclarer un champ, seulement une liste ; et la borne ne parle pas à l'endroit où le contresens se produit |
| Élargir la forme réduite de #657 pour garder `seance_ref` | Coûte une recollecte des 468 profils `roster_groupe` et achète 0,097 % du corpus — et sans report nommé, la fusion additive garderait de toute façon les entrées anciennes |

## Ce qui n'est pas mesuré, et le dit

- **`objet.dossierLegislatif.dossierRef` sur les archives brutes des XVe, XVIe et
  XVIIe** : non reproduit ici, archives absentes du disque, aucun appel réseau.
  La ligne « B » du tableau d'union est un **proxy daté**, pas la mesure du champ.
- **`.../{leg}/vp/reunions/Agenda.json.zip`** : toujours pas en cache, toujours pas
  vérifié — c'est le seul endroit où une clé point-d'ordre-du-jour → dossier peut
  encore se trouver.
- **Ce que rendrait une recollecte** des scrutins : projeté depuis la mesure de la
  propriétaire, jamais mesuré ici.

## Ce que cette décision ne remet pas en cause

Les deux volets livrés, revérifiés ici : `textes_portes[]` à **472 / 472**, et la
table `textes` des quatre index d'amendements. Et
`regrouper-nest-pas-joindre-639.md` reste la règle de ce qu'une vue peut afficher
aujourd'hui : regrouper est permis, joindre exige une clé.
