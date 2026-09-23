<a id="textes-promulgues-population-du-parlement"></a>
# Les textes promulgués sont une population du Parlement, pas d'un gouvernement (2026-09-23)

`2026-09-23`

> **En bref** — L'interface voulait mettre en regard, sur une fiche de gouvernement, les textes promulgués et les actes parus au Journal officiel. Les deux populations lisibles disaient autre chose : ce qu'un membre du gouvernement a *initié* (1 texte sur la fenêtre de LECORNU_II), ou ce que nos rosters *portent* (13). On publie donc les **1 015 dossiers promulgués** des archives de l'Assemblée, pour eux-mêmes, et le rattachement à un gouvernement se fait par la date de promulgation.

## Constat

Remonté par la session interface le 23/09/2026. Sur la fenêtre de `LECORNU_II` :

| Population lisible | Textes promulgués comptés |
| --- | ---: |
| `textes[]` de la fiche de gouvernement — ceux qu'un membre a initiés | **1** |
| Union des `textes_portes` des profils collectés | **13** (8 propositions, 5 projets) |

Aucune des deux n'est « les textes promulgués » : la première est une mesure de
l'initiative, la seconde de notre couverture de collecte — et l'écart avec la
réalité n'est pas mesurable de l'intérieur du corpus.

## Décision

`pivot_data/textes_promulgues.json`, un enregistrement par dossier portant un
acte `PROM-PUB` dans les archives de dossiers de l'Assemblée. Mesuré le
23/09/2026 sur les quatre archives : **1 015 textes, de 2012 à 2026**, 0,47 Mo.

| Champ | Ce qu'il porte, et sa couverture |
| --- | --- |
| `date_promulgation` | la date de parution au JO de l'acte de promulgation — c'est **elle** qui range le texte dans la fenêtre d'un gouvernement |
| `numero_loi` | `codeLoi` de la source, 1 015 / 1 015 |
| `nor` | `referenceNOR`, **603 / 1 015** : l'archive de la XIVe ne le publie pas |
| `titre` | l'intitulé du dossier |
| `nature_procedure` | 336 propositions de loi ordinaires, 297 ratifications de traités, 273 projets de loi ordinaires, 56 textes organiques… |
| `commission` | la commission saisie au fond, recopiée de `commissions_dossiers.json` : 1 015 / 1 015 |
| `chambre_premiere_lecture` | 606 Assemblée, 409 Sénat |

**Une loi promulguée n'appartient à personne.** Le fichier ne l'attribue donc à
aucun gouvernement : c'est le lecteur qui la range par sa date. Attribuer par
l'initiative rejouerait le contresens mesuré sur les textes portés d'Édouard
Philippe, où 281 des 283 textes « portés » étaient ceux de son gouvernement.

**La chambre de première lecture est dérivée, et c'est déclaré** : tout dossier
promulgué porte un `AN1-DEPOT` **et** un `SN1-DEPOT` (607 sur 607 dans les trois
archives mesurées d'abord), le second étant la transmission. Le dépôt le plus
ancien dit l'origine ; deux dates égales ou absentes rendent `null`.

**La commission n'est jamais devinée.** Elle donne la matière — donc la couleur
d'une ligne à l'écran —, et une matière déduite de l'intitulé serait une matière
fausse (§2 règle 8). Absente, elle est publiée `null`.

## Ce que ce fichier ne porte pas

Aucun lien vers les décrets d'application. Mesuré le 23/09/2026 sur les 13 267
lois du fonds JORF : la source ne pose plus `typelien="APPLICATION"` depuis 2024
(0 des 50 lois de 2024, alors que 56 % d'entre elles sont citées par au moins un
acte). Une colonne à moitié vide se lirait comme un manquement de l'exécutif ;
le constat et sa règle de remesure vivent dans `docs/sources/jorf-dila.md`.

## Alternative rejetée

**Élargir les `textes[]` des fiches de gouvernement à tous les textes promulgués
de la période.** Le champ dit « ce que ce gouvernement a initié » ; y verser ce
que le Parlement promulgue changerait le sens d'un champ déjà publié, et deux
lecteurs liraient la même clé différemment selon la date du corpus.
