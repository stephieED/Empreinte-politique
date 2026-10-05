<a id="cohesion-par-appartenance-1175"></a>
# Les votes d'un groupe sont ceux de ses membres du jour : la cohésion suit l'appartenance, comme la parole (#1175) (2026-10-05)

`2026-10-05`

> **En bref** — `cohesion_votes` comptait, pour chaque scrutin, toute personne passée par le groupe dans la législature et députée ce jour-là. Un membre parti, ou pas encore entré, pesait au dénominateur **et votait au nom du groupe** : le 21/11/2025, les 11 groupes de la XVIIe totalisaient 601 éligibles pour 577 sièges. Arbitré par la propriétaire le 05/10/2026 : la cohésion suit l'appartenance au groupe le jour du scrutin, règle déjà retenue pour la parole (#1073). Simulé sur les 31 fiches : 105 278 cases changent de dénominateur, 25 132 de voix, 1 756 de position majoritaire, et **7 126 cases disparaissent** — des scrutins tenus un jour où le groupe n'avait aucun membre.

## 1. Le constat

Signalé par la session de l'interface sur le scrutin `an:17:4241` (21/11/2025,
première partie du projet de loi de finances pour 2026), reproduit à
l'identique sur le privé `2140244c4` : la somme des `membres_eligibles` des 11
groupes de la XVIIe vaut **601** ; les membres présents dans chaque groupe ce
jour-là, d'après `membres[].periodes`, sont **566**.

`group_profile._compute_cohesion_votes` recevait tous les profils ayant appartenu
au groupe pendant la législature et testait `_member_eligibility_intervals` :
« en mandat électif dans cette chambre ce jour-là ».

## 2. Ce n'est pas qu'un dénominateur

L'issue laissait non vérifié « si des voix de non-membres sont comptées ».
Elles le sont. Scrutin `an:17:200` du 30/10/2024 : la fiche d'Ensemble pour la
République publie `pour: 1`. Cette voix est celle de Stella Dupont, membre du
groupe du 19/07/2024 au **03/10/2024**, députée non inscrite ensuite.

## 3. La décision

Arbitrée par la propriétaire le 05/10/2026, sur la question posée par #1175 :
« borne-t-on les votes d'un groupe à la période d'appartenance de chaque membre,
comme c'est déjà fait pour la parole ? » — oui.

1. `_compute_cohesion_votes` reçoit `appartenances`, la table
   `{id de profil: périodes}` que lit déjà `aggregate_tags_thematiques` (#1073).
   Un membre compte pour un scrutin — au dénominateur et par sa voix — si la
   date du scrutin tombe dans l'une de ses périodes, bornes incluses.
2. Un scrutin pour lequel aucun membre n'est éligible n'a pas d'entrée, comme
   avant : c'est ce qui retire les scrutins tenus hors de l'existence du groupe.
3. Une appartenance **non datée** garde le critère du mandat électif : on
   n'exclut personne sur une date qu'on n'a pas (§2 règle 5). Aucun membre des
   31 fiches n'est dans ce cas aujourd'hui.

## 4. L'effet, simulé sur les 31 fiches de groupe de l'Assemblée

Les deux calculs rejoués sur les profils du privé `2140244c4`. **L'ancien calcul
rejoué rend exactement les 31 fiches publiées** : la simulation mesure donc bien
la différence entre les deux règles.

| Cases (groupe × scrutin) | XVe | XVIe | XVIIe |
| --- | --- | --- | --- |
| publiées | 41 139 | 37 897 | 88 238 |
| après | 34 013 | 37 897 | 88 238 |
| **disparaissent** (aucun membre ce jour-là) | 7 126 | 0 | 0 |
| `membres_eligibles` baisse | 25 757 | 19 838 | 59 683 |
| `membres_eligibles` monte | 0 | 0 | 108 |
| les voix changent | 11 065 | 2 975 | 11 092 |
| `position_majoritaire` change | 1 449 | 110 | 197 |
| `quorum_atteint` passe à vrai | 180 | 292 | 1 009 |
| `quorum_atteint` passe à faux | 13 | 0 | 0 |

Les 7 126 cases perdues viennent de trois groupes nés ou dissous en cours de
législature : Agir ensemble (4 065 → 1 532), Écologie Démocratie Solidarité
(3 649 → 205), Libertés et Territoires (3 930 → 2 781).

Les 108 cases de la XVIIe où le dénominateur monte : des membres que
`membres[].periodes` range dans le groupe ce jour-là et que leurs mandats
électifs ne couvraient pas. Non instruit plus avant.

Témoin : `an:17:4241`, Ensemble pour la République, 103 éligibles et 29 absents
avant ; 91 éligibles et 17 absents après.

## 5. Ce que cela exige du run

`cohesion_votes` est une **liste stable** du contrôle de perte, sur les fiches de
groupe comme sur les fiches de lignée (`audit_diff_profils`). Le run qui porte ce
lot verra 7 126 entrées en moins sur trois fiches de groupe, et autant sur les
lignées qui les réunissent : il **bloquera**, à juste titre. Il se lance donc à
la main avec `allow_declared_losses=true`, après un run sans la case dont le
rapport de perte ne montre que ces pertes-là (`docs/regles/gardes-avant-commit.md`).

## 6. Ce qui n'est pas dans ce lot

- **Les amendements** d'un groupe restent bornés à la législature
  (`amendements_agreges`) : c'est l'autre moitié de #1175, à arbitrer à part.
- **La page de méthodologie** : elle parle de « membres éligibles » sans dire
  éligibles à quoi. Texte publié, à la session de l'interface et à la
  propriétaire.
- Les fiches de lignée ne sont pas simulées ; elles se recomposent des fiches de
  groupe.

**Simulé n'est pas mesuré** : à vérifier sur le corpus après le run.
