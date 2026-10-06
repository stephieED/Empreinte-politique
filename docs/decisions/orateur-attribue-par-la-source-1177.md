<a id="orateur-attribue-par-la-source-1177"></a>
# La moitié de la parole de 2021 n'était pas indexée : un paragraphe sans identifiant d'orateur suit l'attribution de la source (#1177) (2026-10-05)

`2026-10-05`

> **En bref** — #1177 demandait si un plafond tronquait les profils à « exactement 1 999 prises de parole ». Il n'y en a pas : c'est une coïncidence. Mais la comparaison de l'archive au publié a montré que **71 520 paragraphes de la XVe, tous de 2021**, n'étaient pas indexés : ils nomment leur orateur et portent `id_acteur`, sans `<orateur><id>`, et le code les rangeait avec les didascalies. Arbitré par la propriétaire le 05/10/2026 : ils sont attribués par `id_acteur` quand le libellé est celui d'une personne. 71 505 entrées de plus à la XVe, pour 586 acteurs ; XVIe et XVIIe inchangées.

## 1. La question posée, et sa réponse

Trois profils publiaient exactement 1 999 prises de parole dans une législature.
Mesuré le 05/10/2026 contre les archives en cache :

| Profil | Législature | Publié | Dans l'archive |
| --- | --- | --- | --- |
| `charles-sitzenstuhl` | XVIIe | 1 999 | 1 999 |
| `stephanie-rist` | XVIIe | 2 000 (1 999 le 02/10) | 2 001 |
| `jean-michel-blanquer` | XVe | 1 999 | **2 160** |

Aucun plafond : le premier est exact, la deuxième a repris la parole depuis.
C'est le troisième qui a ouvert la piste.

## 2. Ce qui manquait

Les 161 prises de parole absentes de Jean-Michel Blanquer sont toutes de 2021.
Leur paragraphe porte `id_acteur="PA717157"` et `<nom>M. Jean-Michel
Blanquer</nom>`, mais pas `<orateur><id>`. `_normaliser_orateur_id_syceron`
rendait « absent » dès que cet identifiant manquait — le cas des didascalies.

Sur les trois archives, paragraphes sans `<orateur><id>` mais avec un
`id_acteur` de la forme d'un acteur :

| Législature | Paragraphes | dont orateur nommé |
| --- | --- | --- |
| XVe | 71 962, sur 499 comptes rendus | 71 520, **tous de 2021** |
| XVIe | 205 | 0 |
| XVIIe | 179 | 0 |

En 2021, la XVe compte 67 463 paragraphes indexés et 71 520 écartés ainsi : la
moitié de l'année. 27 350 sont la présidence de séance.

## 3. L'attribution est celle de la source, et elle se vérifie

Hors présidence, l'acteur de `id_acteur` porte le nom affiché sur **44 080 des
44 170** paragraphes (nom de famille du référentiel AMO30 retrouvé dans le
libellé). Les 90 écarts :

- 76 sont un nom d'usage qui a changé (« Gouffier-Cha » / « Gouffier Valente »,
  « Pitollat » / « Colomb-Pitollat ») : la même personne ;
- 14 sont des orateurs **collectifs** (« Un député du groupe LR », « Plusieurs
  députés du groupe LaREM ») que la source rattache au président de séance.

## 4. La décision

Arbitrée par la propriétaire le 05/10/2026.

Quand `<orateur><id>` manque, le paragraphe est attribué à `id_acteur` si, et
seulement si, cet attribut a la forme d'un acteur (`PA` suivi d'un entier non
nul) **et** que le libellé de l'orateur est celui d'une personne — il commence
par « M. » ou « Mme ». Motif compté : `attribue_par_id_acteur`.

Restent écartés : les orateurs collectifs, et les paragraphes sans libellé
(les 205 et 179 des XVIe et XVIIe) — rien n'y dit qui parle (§2 règle 2).

`SYCERON_VERSION_INDEX` change : l'index contient 71 505 entrées de plus.

## 5. L'effet, simulé sur les trois archives

| | XVe | XVIe | XVIIe |
| --- | --- | --- | --- |
| paragraphes attribués par `id_acteur` | 71 505 | 0 | 0 |
| acteurs concernés | 586 | — | — |
| identifiants d'entrée en double | 0 | 0 | 0 |

Les identifiants des entrées déjà publiées ne bougent pas : le rang d'un
paragraphe dans son compte rendu compte tous les paragraphes, attribués ou non.
Les entrées nouvelles s'ajoutent par la fusion additive, sans report.

**Simulé n'est pas mesuré.** Le corpus les reçoit après un run qui collecte les
interventions, et qui parvient à télécharger l'archive de la XVe (#1202).

## 6. Ce que #1177 portait d'autre, et qui reste ouvert

- « Motions de censure » : 34 membres dans l'agrégat d'un groupe, 26 dans les
  extraits. Non instruit ici.
- Deux prises de parole portant la fonction d'une personne auditionnée. Non
  instruit ici.

## 7. Ce que cela dit de nos mesures

Le chiffre « 1 232 692 des 1 235 317 paragraphes portant les deux
[identifiants] » qui justifiait le préfixage ne comptait, par construction, que
les paragraphes portant **les deux**. Ceux qui n'en portent qu'un n'étaient dans
aucun dénominateur. Une couverture se mesure contre l'archive, orateur par
orateur, pas contre ce que l'index a déjà retenu.
