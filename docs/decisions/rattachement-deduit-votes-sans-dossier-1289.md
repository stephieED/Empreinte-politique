<a id="rattachement-deduit-votes-sans-dossier-1289"></a>

# Un vote que l'Assemblée ne rattache pas reçoit son dossier par déduction, marquée (#1289) (2026-10-15)

`2026-10-15`

> **En bref** — Le lien vote → dossier se lit d'abord dans la source ; à défaut,
> il se déduit : le dossier qui inscrit une décision de l'Assemblée le jour du
> vote, sans vote sur l'ensemble attaché, sous un titre proche ; et ce qui reste,
> seulement, vient d'une table relue à la main. La déduction est marquée `provenance:
> deduit_date_et_titre` dans `pivot_data/scrutins_dossiers.json`. Exception
> arbitrée par la propriétaire à `regrouper-nest-pas-joindre-639`. Ce qui reste
> sans dossier et ressemble à un autre texte ouvre une issue de suivi, jamais un
> échec du run.

## Le contexte

L'interface regroupe les lectures d'un même texte pour n'afficher que la
dernière (#711). Sa première clé est le dossier ; à défaut, l'intitulé. Mesuré le
15/10/2026 :

| Population | Mesure |
| --- | --- |
| Votes sur l'ensemble d'un texte, XIVe à XVIIe | 934 |
| … qu'aucun dossier de la source ne nomme | **265** (XIVe 23, XVe 166, XVIe 46, XVIIe 30) |
| … dont le vote apparaît quelque part dans les archives de dossiers | 4 (3 ajoutés par la source depuis le dernier calcul ; 1, an:16:4052, rangé à tort par l'archive XVIe et corrigé dans l'archive XVIIe) |
| Textes affichés deux fois sur les fiches (chiffre de l'issue) | 21, sur 11 des 36 fiches de candidats déclarés |

**La cause est la source** : pour 261 votes, l'Assemblée ne pose le vote dans
aucun `actesLegislatifs[].voteRefs`. Ne plus afficher ces votes a été pesé et
écarté : environ 167 lois disparaîtraient des fiches (Immigration 2018 et 2023,
devoir de vigilance…), 457 des 3 246 positions des candidats déclarés — une
absence publiée comme un fait (§2 règle 5), pour corriger 21 doublons.

## La décision

**Une cascade, dans cet ordre** (`src/build_scrutins_dossiers.py`) :

1. le lien que l'Assemblée publie ;
2. la déduction (`src/rattachement_deduit.py`), pour les seuls votes sur
   l'ensemble que la source ne rattache pas. Retenue quand **un seul** dossier :
   - inscrit une décision de l'Assemblée en séance **le jour du vote** (CMP
     comprise) ;
   - dont aucun vote **sur l'ensemble** n'occupe déjà cette décision — un vote
     d'amendement ou de motion ne l'occupe pas : la source pose parfois la motion
     de rejet là où devrait être le vote (DLR5L16N47637, 15/11/2023) ;
   - dont le titre se retrouve pour moitié dans l'intitulé du vote, « organique »
     des deux côtés ou d'aucun ;
3. **en dernier**, `config/rattachements_scrutins_dossiers.json` — une ligne
   relue par la propriétaire, avec sa date et sa preuve, pour un vote que ni la
   source ni la déduction ne rattachent. Elle ne remplace jamais ni l'une ni
   l'autre (arbitrage du 15/10/2026) : une ligne qu'elles rendent inutile est
   ignorée, et le run la nomme pour qu'on la retire.

**La trace.** `scrutins_dossiers.json` gagne une table `provenance` : `table_relue`
ou `deduit_date_et_titre`. Absent de `provenance`, un rattachement est celui de
la source. Les déductions sont **recalculées à chaque run** qui a lu les
archives, jamais fusionnées : une déduction que la source rend inutile perd sa
marque. Un run sans archives garde celles d'avant.

**L'alerte.** `src/alerte_votes_sans_dossier.py` relève, après la cascade, les
paires de textes d'une même législature dont l'un au moins reste sans dossier et
dont les intitulés partagent la moitié de leurs mots. Une étape du run tient une
issue de suivi (étiquette `votes-sans-dossier`) sur le dépôt privé, comme celle
des fiches hors schéma (#1223) : ouverte, réécrite, commentée seulement quand la
liste change, fermée quand elle se vide. **Le run n'échoue jamais.** Une paire
jugée « textes différents » entre dans `textes_distincts` et n'est plus signalée.

### Mesure de la règle (15/10/2026)

Rejouée sur les 669 votes sur l'ensemble que la source rattache elle-même, en
libérant à chaque fois la seule décision de ce vote :

| Résultat | Votes |
| --- | --- |
| Bon dossier | 615 |
| Aucune proposition (zéro ou plusieurs candidats) | 53 |
| **Mauvais dossier** | **1** — an:14:594, transparence de la vie publique : lois organique et ordinaire jumelles, sous le même titre de dossier |

Sur les 265 votes sans dossier : **226 déduits**, puis **10** rattachés par la
table relue (validés par la propriétaire le 15/10/2026) ; 26 votes restent sans
dossier, et l'alerte ne relève **aucune paire** — la seule paire restante,
deux accords internationaux votés le même jour (an:15:4355, an:15:4356), est
inscrite dans `textes_distincts`. Sur les 31 votes de la
première relecture humaine, la déduction en rattache 27 au dossier proposé et
aucun ailleurs.

## Pourquoi c'est une exception à `regrouper-nest-pas-joindre-639`

Cette décision interdit de joindre deux objets sans identifiant posé par la
source. La propriétaire l'a assouplie le 15/10/2026, **pour ce seul cas**, à trois
conditions : le rattachement déduit est marqué, il ne remplace jamais celui de la
source, et une table relue à la main comble ce qui reste. Ce qui a pesé : le vote et le
dossier viennent de la **même** source ; la règle ne repose pas sur le titre seul
mais sur une décision inscrite le jour même ; son erreur est mesurée (1 sur 616
propositions). La décision du 31/08 reste entière partout ailleurs —
amendements, interventions, textes portés.

## Alternatives écartées

| Option | Pourquoi non |
| --- | --- |
| Ne plus afficher les votes sans dossier | 167 lois retirées des fiches pour 21 doublons ; une absence publiée comme un fait |
| Assouplir le regroupement par intitulé côté interface | Multiplie les fusions à tort, comme les deux lois de finances rectificatives de 2017 (an:15:246, an:15:345), deux dossiers distincts |
| Tout relire à la main | 265 votes ; la table relue ne sert qu'aux cas que la règle ne tranche pas |
| Une table relue qui l'emporte sur la source et la déduction | Écartée par la propriétaire : la table ne doit porter que les cas sans autre rattachement, en dernier recours |
| Échouer le run sur un doublon possible | Un défaut d'affichage ne vaut pas une journée de données perdue ; l'issue de suivi suffit |

## Ce qui reste

- **Un cas écarté à la relecture** : la déshérence des retraites
  supplémentaires (an:15:2445, an:15:3428) semblait être une loi à deux
  dossiers. Ce sont deux propositions distinctes : la n° 2516, rejetée le
  30/01/2020 (DLR5L15N38380), puis la n° 2782, déposée le 24/03/2020 et
  promulguée le 26/02/2021 (DLR5L15N39229), dont la chronologie ne porte aucun
  acte du 30/01/2020. Deux textes, deux lignes : rien à corriger.
