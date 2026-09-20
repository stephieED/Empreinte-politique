<a id="budgets-extract-an-perimes-546"></a>
# Le correctif de #540 validé en conditions réelles, et les deux budgets qu'il a périmés (#546) (2026-08-27)

`2026-08-27`

> **En bref** — le correctif de #540 validé en conditions réelles a périmé les deux budgets qui le bornaient.

Deux runs complets se sont succédé le 27/08, encadrant la fusion du correctif
de #540. C'est leur **écart** qui est instructif, pas chacun pris isolément.

| | `33100214165` (avant #540) | `33110395663` (après) |
| --- | --- | --- |
| Jobs | 22 verts, 52 min | 22 verts, 72 min |
| Interventions publiées | 891 | **16 242** |
| `extract-an`, durées | 2,3 → 6,7 min | 3,3 → **8,9 min** |
| Troncature de collecte | aucune | **1 profil** |

## Le correctif fait ce qu'il annonce

Vérifié profil par profil sur le corpus régénéré : **le pivot égale le brut**,
sur les sept profils porteurs, sans exception.

| Profil | Brut | Pivot |
| --- | ---: | ---: |
| gabriel-attal | 3 963 | 3 963 |
| jean-luc-melenchon | 3 933 | 3 933 |
| jerome-guedj | 2 702 | 2 702 |
| edouard-philippe | 2 376 | 2 376 |
| marine-le-pen | 2 247 | 2 247 |
| laurent-wauquiez | 535 | 535 |
| bruno-retailleau | 486 | 486 |
| **Total** | **16 242** | **16 242** |

C'était le risque propre à la reprise de #540 : les entrées déjà publiées n'ont
pas d'`intervention_id`, leur renormalisation en produit un, et une fusion
additive naïve les aurait **doublées**. L'égalité ci-dessus est la preuve que
`clean_stale_interventions` absorbe les anciennes au lieu de les empiler. Elle
n'avait été vérifiée qu'en simulation avant ce run.

**Un écart avec la prévision, non expliqué.** On attendait 7 767 interventions,
il y en a 16 242 — parce que la **collecte** a progressé entre les deux runs,
pas la publication : `jean-luc-melenchon` passe de 15 à 3 933 entrées brutes et
`edouard-philippe` de 50 à 2 376. Au premier run, ces deux profils portaient
`synchro_syceron = None` et Philippe un warning « aucune intervention Syceron
pour cet acteurRef ». Ce qui a changé entre les deux n'est pas établi. À
surveiller si le phénomène se répète : une résolution d'acteur qui échoue un
run sur deux serait un défaut, pas une amélioration.

## Le quatrième point de #510 devient mesurable

`pivot_data/profiles` : **376 Mo pour 476 profils**, médiane **0,5 Mo**, le plus
lourd à **7,1 Mo** (`jean-luc-melenchon`). À comparer aux 100,6 Mo du 20/08 :
la charge a plus que triplé. Elle reste loin des grandeurs que #429 protège —
le seuil GitHub porte sur le dépôt et le push, jamais sur l'arbre de travail.
`raw_data/profiles` pèse en revanche **4,3 Go**.

## Les deux budgets ne valent plus, et l'un perd déjà de la donnée

Le commentaire de `generate-data.yml:383-394` documente honnêtement d'où vient
le `timeout-minutes: 9` : « 240 s de préambule provisionné + les 240 s de
`--budget-interventions-secondes` + ~60 s de marge », mesuré sur les runs des
19 et 20/08. **Deux hypothèses de ce calibrage sont tombées depuis** :

- la **recherche NosDéputés** y pesait 90 s sur `jean-luc-melenchon`. Elle a été
  retirée par #529 ;
- **Syceron n'indexait rien** à l'époque — c'est le défaut de #510. Le poste
  « archives de débats » était mesuré à 22-55 s par législature pour **zéro
  intervention retenue**.

On a donc soustrait 90 s et ajouté un poste dont le coût réel n'a jamais été
mesuré. Que le total retombe à 8,9 min pour un plafond de 9 est une
**coïncidence**, pas un dimensionnement.

Et le second budget tronque déjà :

```
jerome-guedj — collecte d'interventions tronquée (budget de temps) :
budget de collecte d'interventions épuisé après 247 s (plafond 240 s)
— non collecté : 1 législature(s) de questions officielles
```

La perte est **déclarée**, exactement comme #514 l'a conçu : le dispositif
fonctionne. Mais elle est réelle, et le profil publié de Jérôme Guedj ne porte
pas les questions officielles d'une législature.

**Rien n'est corrigé ici** : aucun run n'a échoué, et re-dimensionner à l'aveugle
reproduirait la faute d'origine — un chiffre posé sur une mesure périmée. La
décomposition réelle d'un shard doit être mesurée d'abord. Suivi en #546.

> **Mesuré depuis**, et deux chiffres de cette entrée sont à corriger : les
> profils tronqués sont **deux** et non un (`jean-luc-melenchon` l'était aussi,
> à 332 s), et les durées des deux runs ne sont pas comparables — au run
> `33100214165` les archives Syceron des 15e et 16e législatures étaient
> injoignables. Voir
> [#budgets-extract-an-remesures-546](budgets-extract-an-remesures-546.md).

---

