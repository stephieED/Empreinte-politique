<a id="lecture-europeenne-themes-et-votes-901"></a>

# Le versant européen se lit comme le français : mêmes thèmes, mêmes couleurs, et les votes enfin affichés (#901) (2026-09-17)

`2026-09-17`

> **En bref** — Les 11 013 positions de vote au Parlement européen des six
> candidats déclarés à mandat européen étaient collectées et n'atteignaient pas
> l'écran : la fiche affirmait qu'« aucune n'est rattachée à un scrutin
> identifié », ce qui décrivait notre index et non la source. Elles se joignent
> toutes par **numéro + date** à `pivot_data/scrutins_europeens.json`, et se
> lisent maintenant dans le gabarit français. Les trois figures européennes —
> sankey des textes portés, carte des amendements, figure des votes — partagent
> **la même cascade de thèmes** (domaines EuroVoc du dossier, sinon familles
> OEIL) et **la même couleur par thème**, la teinte suivant le thème et non son
> rang.

## Le constat

Mesuré le 17/09/2026 sur le commit de données `760f1bffe` :

| Fait | Mesure |
| --- | --- |
| Positions de vote européennes des 6 fiches concernées | 11 013, dont **0 avec un `scrutin_id`** — par contrat (`index-scrutins-europeens-901`) |
| Positions que le numéro + la date rattachent à un scrutin | **11 013 sur 11 013** |
| Textes votés retenus après repli sur le dernier scrutin | 3 175 (Maurel), 1 921 (Le Pen), 1 830 (Glucksmann), 1 451 (Mélenchon), 1 247 (Philippot), 309 (Massard) |
| Axe « commission saisie au fond » sur ces textes | **2 à 11 %** seulement — l'index ne portait les commissions que des 389 dossiers cités par les textes portés |
| Dossiers européens dans l'index depuis #992 | 4 642, tous avec leurs familles OEIL ; 151 avec leurs domaines EuroVoc |

## La décision

**1. Un texte, une position.** Un texte est un dossier (`reference_dossier`), à
défaut le document voté, à défaut le scrutin. La position retenue est celle du
**dernier scrutin** : date la plus tardive, puis rang dans la séance. C'est le
pendant européen de la dernière lecture retenue (#711), que la nomenclature
européenne ne permet pas d'appliquer telle quelle — elle ne publie pas de
lecture.

**2. Les mêmes thèmes partout, par la même cascade.** Arbitrage de la
propriétaire : « les catégories doivent être en cohérence entre le sankey des
textes et les amendements ». Le thème d'un dossier est donc celui de ses
domaines EuroVoc, à défaut celui de ses familles OEIL — exactement la cascade du
sankey (`axe-europeen-prorata-domaines-901`). L'axe « commission saisie au
fond », retenu pour les amendements le matin du 17/09
(`amendements-deux-parlements-901`), est abandonné, et la règle qui le lisait est
retirée du module : une règle sans lecteur se périme sans que rien ne le signale.

**3. Un objet compte sous chacun de ses thèmes.** Un dépôt ou un texte voté dont
le dossier porte quatre thèmes apparaît sur quatre lignes. Les lignes ne
s'additionnent donc pas au total annoncé, et c'est assumé : « ce n'est pas grave
s'il n'y a pas unicité des amendements distribués sur les différentes catégories
de thème au format bar chart » — un diagramme en barres ne se lit pas comme un
tout réparti, contrairement au sankey, où le prorata reste la règle. **Les
effectifs, eux, comptent des objets distincts** : les puces de nature comptent
des dépôts et des textes, jamais les copies par thème. Sans cette séparation,
« Législatif » affichait 3 371 dépôts pour 1 552.

**4. Une couverture progressive n'est pas une absence.** 4 455 des 4 642 dossiers
portent `domaines_non_resolu.motif == "question_non_posee"` : la collecte
interroge le portail par paquets, environ 200 dossiers par run. Ce n'est pas
« ce dossier n'a pas de thème » : la famille OEIL le range en attendant, et les
figures se francisent d'un run à l'autre sans nouveau lot (§2 règle 5).

**5. La teinte suit le thème, pas son rang.** Le référentiel est fermé — 21
domaines EuroVoc et 8 familles OEIL — et `ORDRE_THEMES_UE` fixe l'ordre des
teintes. « Community policies » est donc de la même couleur dans le sankey et
dans la carte des amendements, et d'une fiche à l'autre. La palette compte 14
teintes pour 29 thèmes : deux thèmes en partagent une, ce qui était déjà vrai du
rang, en plus d'être instable. Dans la figure des votes, la couleur dit la
position (contre, abstention, pour) : le thème y est nommé, pas teinté.

**6. Aucun découpage par période côté européen, aucune origine de texte.** Les
votes français se lisent par banc et par gouvernement en place ; à Strasbourg il
n'y a ni l'un ni l'autre, et la propriétaire a jugé ce filtre « hors propos ». La
figure couvre tous les mandats européens et nomme les groupes traversés. Le
filtre « Origine : Parlement / Gouvernement » disparaît de même : il n'y a pas de
projet de loi du gouvernement au Parlement européen.

**7. Les grands chiffres cessent de ranger l'européen sous l'Assemblée.** La
cellule « Amendements » de la colonne française comptait tous les dépôts mais
seulement les dossiers de l'AN — « 2 944 amendements sur 18 dossiers législatifs »
chez Maurel, dont 2 609 européens. Chaque parlement a désormais sa cellule ; côté
européen le mot « législatif » n'est pas repris, 105 des 170 dossiers amendés par
Maurel étant des rapports d'initiative. La cellule « Textes portés » du Parlement
européen, elle, était **toujours vide** : elle lisait une liste qui ne contient
plus que les textes français depuis que la cascade européenne existe.

**8. La phrase qui déclarait ces votes hors de portée est retirée.** Elle disait
vrai tant que rien ne les rattachait ; elle est fausse depuis ce lot, et la
branche qui la portait est devenue inatteignable.

## Ce qui n'est pas fait, et pourquoi

- **Les intitulés de scrutin restent bruts** quand l'index ne connaît pas le
  titre du dossier : « A8-0299/2018 - Bart Staes - Résolution 24/10/2018
  13:09:53.000 ». Nettoyer cette chaîne serait déduire un titre d'un intitulé.
- **Le sort du texte n'est pas affiché** côté européen : l'index des scrutins ne
  le porte pas.
- **« Où il s'est écarté des siens » ne couvre pas l'européen**
  (`pas-d-ecarts-groupe-europeens-901`), alors que `scrutins_europeens.json`
  publie les positions par groupe. C'est un lot à part, et l'écart individuel
  contre la majorité du groupe se publie un scrutin à la fois, jamais compté
  (§2 règle 7).
- **716 des 5 571 scrutins portent un `numero_scrutin` mal formé** (« 2017-06-01
  00:00:00-13. »). Signalé à la collecte le 17/09 ; l'interface s'en accommode en
  relisant le nombre final pour l'ordre dans la séance, la jointure n'en dépend
  pas.

## L'alternative écartée

**Garder la commission saisie au fond comme axe européen.** C'était l'axe
français, et il rendait les deux versants comparables. Écarté deux fois : sur les
votes, il ne plaçait que 2 à 11 % des textes ; sur les amendements, il faisait
parler deux figures d'une même fiche dans deux vocabulaires. La cohérence
demandée porte sur les CATÉGORIES, pas sur la mécanique.
