<a id="rapport-et-panorama-mots-permis-1217"></a>

# « Rapport » et « panorama » restent des mots : la garde vise le nom que la page se donne (#1217) (2026-10-12)

`2026-10-12`

> **En bref** — La décision du 23/09/2026 (`article-de-type-instantane-1029`) a été écrite, puis testée, plus strictement que la propriétaire ne l'entendait : « "rapport" et "panorama" ne sont plus des mots publiés ». Le 12/10/2026 le test a bloqué le titre d'une figure et le titre d'un texte de l'Assemblée. Tranché par la propriétaire le 12/10/2026 : **ce qu'elle voulait, c'est qu'une page ne se donne pas trois noms ; aucun mot n'est interdit.** La garde refuse désormais « ce rapport », « ce panorama », et laisse passer tout autre emploi.

## Le contexte

`tests/test_rapports_publies.py` relisait le texte visible de chaque page de
`web/UI_finale/public/rapports/` et refusait toute occurrence de « rapport » ou
de « panorama ».

Mesuré le 12/10/2026 sur la page `2026-10-09-education-a-l-assemblee.html`, la
première à le rencontrer — deux occurrences, aucune ne nomme l'article :

| Mot trouvé | Où | Ce que c'est |
| --- | --- | --- |
| « Panorama » | titre d'une figure : « Panorama des textes déposés par les groupes parlementaires » | un titre choisi par la propriétaire le 09/10/2026 |
| « rapports » | infobulle d'un texte déposé : « Retrouver la confiance et l'équilibre dans les rapports locatifs » | le titre que l'Assemblée donne à un texte |

Le second cas ne pouvait pas se corriger sans réécrire un titre de la source
(§2 règle 2).

## La décision

Les mots de la propriétaire, le 12/10/2026 : « c'est un article. Un article à
ranger dans les rapports. Ce que j'ai dit la dernière fois, c'était pour
expliquer le fait que le post en question était à la fois un instantané et un
rapport. Mais il ne s'agissait pas d'appliquer une règle aussi stricte ! »

- **Aucun mot n'est interdit dans une page.** Ni « rapport », ni « panorama ».
- **Ce qui reste vrai de la décision du 23/09** : l'objet publié se dit
  « article », son type « instantané », et une page ne se désigne pas de
  plusieurs façons (`docs/regles/textes-publies.md` : « un seul nom par objet
  sur une même page »).
- **La garde est resserrée sur ce cas** : elle refuse la page qui se désigne
  elle-même — « ce rapport », « ce panorama », « le présent rapport » — et rien
  d'autre. Un second test tient les deux phrases qui l'ont fait resserrer et
  les deux qu'elle doit encore refuser.

Cette décision **corrige** la ligne « "rapport" et "panorama" ne sont plus des
mots publiés » de `article-de-type-instantane-1029.md`, qui n'est pas éditée en
place.

## L'alternative écartée

**Renommer la figure** (« Cartographie des textes déposés… ») pour satisfaire le
test : proposé par l'agent, écarté. Cela laissait le second cas sans issue, et
pliait un titre choisi à une règle que personne n'avait voulue.

## Ce qui n'est pas vérifié

La garde ne reconnaît qu'un déterminant suivi du mot. Une page qui écrirait
« Rapport sur les carburants » en titre principal ne serait pas arrêtée : c'est
la relecture à l'écran qui la rattrape, pas ce test.
