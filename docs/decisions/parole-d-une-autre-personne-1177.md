<a id="parole-d-une-autre-personne-1177"></a>
# Une prise de parole dont le libellé nomme une autre personne n'est pas attribuée (#1177) (2026-10-07)

`2026-10-07`

> **En bref** — l'Assemblée rattache parfois la parole d'un invité au député qui a demandé le débat : le 08/01/2026, « M. Jean-Marc Cantais, policier, lanceur d'alerte » et « Mme Assa Traoré » portent l'identifiant d'Audrey Abadie-Amiel aux deux endroits où la source écrit l'orateur. Rien ne se contredisait dans les identifiants, seul le nom trahissait l'erreur, et le nom n'était pas lu. Arbitrage de la propriétaire, 07/10/2026 : une telle parole n'est pas attribuée. **98** prises de parole sont retirées de **60** fiches, dont trois de Gabriel Attal.

## 1. Comment une parole était attribuée

Par l'identifiant que l'Assemblée écrit elle-même, à deux endroits du paragraphe :
`<orateur><id>` et l'attribut `id_acteur` (#510). Quand ils se contredisent, la source
refuse l'attribution (2 625 paragraphes). Le libellé (« M. Jean-Marc Cantais ») n'était
comparé à rien.

## 2. La mesure

Sur les trois archives (XVe et XVIe en cache, XVIIe téléchargée le 07/10/2026), en
comparant le libellé de chaque paragraphe attribué au nom de l'acteur dans le
référentiel AMO30 :

| | XVe | XVIe | XVIIe |
| --- | ---: | ---: | ---: |
| Libellés de personne qui concordent | 412 779 | 214 451 | 189 854 |
| Libellés qui nomment une autre personne | 34 | 48 | 16 |

Une première règle, plus large, en comptait plus de 5 000 : elle refusait les noms
d'une lettre (Cédric O, Delphine O) et les noms d'usage changés (« Christine
Cloarec », devenue Christine Le Nabour ; « Benjamin Lucas », Lucas-Lundy). La règle
retenue les garde.

## 3. La décision

1. **`libelle_designe_une_autre_personne`** : seul un libellé de personne est
   comparé (« M./Mme Prénom Nom ») — ni une fonction (« M. le président »), ni un
   collectif ; il concorde dès qu'il contient un mot du nom OU du prénom de l'acteur.
2. **À la collecte** : `_normaliser_orateur_id_syceron` refuse, motif
   `libelle_d_une_autre_personne`, quand le référentiel est chargé ; sans lui, rien
   n'est vérifié et le compteur le dit. `SYCERON_VERSION_INDEX` passe à
   `1177-libelle`.
3. **Sur les fiches déjà publiées** : un retrait nommé, après la fusion, depuis la
   liste committée `config/paroles_d_une_autre_personne.json` (98 paragraphes, par
   `id_syceron`). Une parole n'est retirée que de la fiche à laquelle la source
   l'avait rattachée.
4. **Rien n'est réattribué.** La parole de Jean-Marc Cantais ne va à personne :
   attribuer sur un nom serait ce que §2 règle 2 interdit.

## 4. L'effet, simulé

Sur les 1 402 profils du privé (07/10/2026) : **98** prises de parole retirées, de
**60** profils — Audrey Abadie-Amiel 10, Antoine Armand 5, Antoine Savignat 4,
Félicie Gérard 4, Gabriel Attal 3, Yaël Braun-Pivet 3… Les fiches de groupe et de
gouvernement se recomposent d'elles-mêmes.

## 5. Ce que cela exige du run

`interventions` est une liste stable du contrôle de perte : 60 profils baissent, le run
**bloque**. Il se lance avec `allow_declared_losses=true` après un run sans la case
dont le rapport ne montre que ces pertes — idéalement le même que celui de #1011, pour
ne payer qu'une fois les deux runs.

## 6. Ce qui n'est pas dans ce lot

- **La liste se régénère à la main** (`src/paroles_d_une_autre_personne.py`) quand une
  archive s'enrichit ; la collecte refuse déjà les nouveaux cas, mais une parole déjà
  publiée qui ne serait pas dans la liste resterait.
- **Le constat 2** de #1177 (34 orateurs contre 26) : l'écart semble venir des extraits
  que l'interface construit. Non confirmé.
