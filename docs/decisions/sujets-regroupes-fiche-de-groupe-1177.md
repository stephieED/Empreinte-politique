<a id="sujets-regroupes-fiche-de-groupe-1177"></a>

# La fiche de groupe regroupe ses sujets de parole avec la clé de l'agrégat (#1177) (2026-10-08)

`2026-10-08`

> **En bref** — L'Assemblée intitule la même séance « Motion de censure » et « Motions de censure ». L'agrégat des fiches de groupe range les deux sous une clé (`cle_tag_thematique`, #1042) ; la fiche de groupe lisait l'intitulé exact et montrait deux lignes. Arbitré par la propriétaire (option A, transmis par la session Backend le 08/10/2026) : **la figure et les extraits de la fiche de groupe regroupent avec la même clé**, et affichent la forme que l'agrégat publie. **La fiche candidat n'est pas concernée** : deux intitulés voisins y restent deux entrées (#639).

## Le contexte

Mesuré le 08/10/2026 sur `main` 1739b9c12, groupe EPR de la XVIIe, parole du
groupe (hors présidence de séance et hors parole tenue comme membre du
gouvernement) :

| | Lignes | Prises de parole | Membres |
| --- | --- | ---: | ---: |
| Avant | « motion de censure » | 226 | 21 |
| | « motions de censure » | 183 | 24 |
| Après | « motions de censure » | 409 | 33 |
| L'agrégat de la fiche | « motions de censure » | | 34 |

L'écart qui reste, 33 contre 34, vient de la population : l'agrégat compte toute
prise de parole, la figure écarte la présidence de séance et la parole
gouvernementale (arbitrage du 02/10/2026).

## La décision

- `cleTagThematique` (`web/UI_finale/src/utils/sujetsRegroupes.js`) est la copie
  de `cle_tag_thematique` ; `tests/test_sujets_regroupes_1177.py` exécute les
  deux sur les mêmes intitulés.
- La forme affichée est celle que l'agrégat publie ; pour un sujet qu'il ne
  porte pas, la plus fréquente parmi celles lues, l'ordre alphabétique
  départageant. Jamais la clé elle-même, que la source n'écrit pas toujours.
- « Intitulé non publié » ne se regroupe avec rien.

## L'alternative écartée

Publier dans l'agrégat la liste des formes regroupées : un champ de plus sur
toutes les fiches de groupe, pour un seul usage (écartée côté données, voir les
commentaires du 07/10 sur #1177).

## Ce qui reste

- **Deux règles coexistent.** La fiche candidat garde « Motion de censure » et
  « Motions de censure » comme deux entrées, par une garde écrite pour #639.
  Non arbitré : les aligner ou non.
- La fiche de gouvernement lit ses sujets par l'intitulé en minuscules, sans
  cette clé : non mesuré.
- Non vérifié à l'écran.
