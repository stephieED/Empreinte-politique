<a id="pourquoi-en-methodologie-328"></a>

# Le « pourquoi » descend en méthodologie, la fiche garde la limite (#328) (2026-09-09)

`2026-09-09`

> **En bref** — un audit de la **page rendue** (titres de textes et de commissions exclus, ce sont des libellés de source) a mesuré **1 772 mots de notre copie** sur `jerome-guedj`, dont six blocs au-dessus de DESIGN_SYSTEM §7 règle 2 — le critère de « Ce qu'il a voté » à **58 mots** en tête — et deux modes d'emploi qui ne s'accordaient même pas sur le vouvoiement ; arbitrage de la propriétaire : le raisonnement va en méthodologie, la fiche garde la limite et le lien, et **chaque section de la fiche a son ancre, une seule** (`fonctions`, `propose`, `votes`, `ecarts`, `interventions`, `couverture`) — « Textes portés » et « Amendements » étaient deux sections pour un seul emplacement et sont réunies sous « Ce qui est proposé » ; **le critère des votes perd la règle de dernière lecture**, publiée SOUS la figure là où #711 la veut, et c'est cette répétition qui le portait à 58 mots ; **les trois refus gardent leur phrase et perdent leur `pourquoi`** (71 mots), qui n'est pas recopié — les deux pages rendent le même `STATED_REFUSALS` ; **les preuves de borne ne bougent pas**, ce sont des preuves et non de la copie ; mesuré après : **1 562 mots, 210 de moins**, aucun bloc au-dessus de 27, et un test refuse un critère au-delà de 22 mots comme un renvoi vers une ancre inexistante ; **alternative écartée** — raccourcir sans créer d'ancres, deux fois moins de travail et le coût déplacé sur le lecteur, qui rouvre douze sections pour retrouver la règle. 8 tests neufs.

## Le contexte

`DESIGN_SYSTEM.md` §7 règle 2 dit : « Le texte explicatif est un aveu d'échec.
[…] une limite tient en deux mots, une explication en paragraphe. » Un audit de
la **page rendue** — pas des sources — l'a mesurée le 09/09/2026 sur
`jerome-guedj`, titres de textes et de commissions exclus parce que ce sont des
libellés de la source et non notre copie.

**1 772 mots de notre copie**, dont six blocs au-dessus de la limite :

| Endroit | Mots |
| --- | ---: |
| § « Ce qu'il a voté » · critère | **58** |
| § 6 · note « groupe majoritaire non déclaré » | 52 |
| § « Les fonctions exercées » · pied | 40 |
| § 6 · note « enregistrements pour sièges » | 36 |
| § « Où il s'est écarté » · critère | 32 |
| § « Ce qu'il a dit » · critère | 31 |

Plus deux modes d'emploi que la règle vise directement — « Cliquez une barre
pour ne garder qu'une matière… » et « Clique un ruban, une barre ou une
étiquette… » — qui ne s'accordaient même pas sur le vouvoiement.

## La décision

**Le raisonnement va dans la méthodologie ; la fiche garde la limite et le lien
vers le paragraphe.** Arbitrage de la propriétaire, 09/09/2026.

Pour que ce lien dépose le lecteur devant **sa** règle et non en haut d'une page
de douze sections, **chaque section de la fiche a son ancre, et une seule** :

| Section de la fiche | Ancre |
| --- | --- |
| Les fonctions exercées | `#fonctions` (section neuve) |
| Ce qu'il a proposé | `#propose` |
| Ce qu'il a voté | `#votes` |
| Où il s'est écarté des siens | `#ecarts` |
| Ce qu'il a dit | `#interventions` |
| Ce qu'on n'a pas pu lire | `#couverture` |

« Textes portés » et « Amendements » étaient **deux sections de méthodologie
pour un seul emplacement de fiche** : elles sont réunies sous « Ce qui est
proposé », chacune gardant son sous-titre. Une section que nul renvoi n'atteint
est une section que personne ne lit — et un test refuse désormais l'inverse : un
renvoi vers une ancre inexistante.

## Ce qui a bougé, et ce qui n'a pas bougé

- **Le critère des votes perd la règle de dernière lecture**, qui est publiée
  **sous** la figure, là où #711 la veut — à côté du chiffre. L'écrire aussi en
  tête faisait lire deux fois la même phrase, et c'est cette répétition qui
  portait le critère à 58 mots.
- **Les trois refus gardent leur phrase et perdent leur `pourquoi`** sur la
  fiche — 71 mots. Il n'est pas recopié dans la méthodologie : les deux pages
  rendent le **même** `STATED_REFUSALS`. Une phrase écrite deux fois est une
  phrase qui divergera (leçon de #711).
- **Les limites de `limitesDuProfil` disent un fait, plus sa raison.** « Le
  déduire d'un comportement de vote serait un jugement, pas une lecture » est
  une règle générale, pas un fait sur ce profil : elle passe sous
  `#couverture`.
- **Une seule voix** : « cliquez » partout.
- **Les preuves de borne ne bougent pas.** Les trois plus longues (57, 50 et
  41 mots) viennent de `couverture[].preuve`, produit par le pipeline : ce sont
  des preuves, pas de la copie. Les raccourcir serait affaiblir ce qu'elles
  établissent.

Mesuré après : **1 562 mots**, soit **210 de moins**, et aucun bloc de notre
copie au-dessus de 27 mots. Un test refuse un critère de section au-delà de 22
mots — c'est là que les phrases s'accumulent, parce que chacune paraît utile
isolément.

## L'alternative écartée

**Raccourcir sans créer d'ancres.** Deux fois moins de travail, et cela déplace
le coût sur le lecteur : un renvoi vers `/methodologie` sans fragment fait
rouvrir douze sections pour retrouver la règle qu'on vient de perdre de vue —
exactement le coût que la règle 2 cherche à éviter.
