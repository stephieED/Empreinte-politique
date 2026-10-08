<a id="garde-connait-le-retrait-1177"></a>
# La garde « collecté = publié » soustrait le retrait des paroles d'une autre personne (#1177) (2026-10-08)

`2026-10-08`

> **En bref** — le run à pertes déclarées `37738655769` (08/10/2026) a franchi le contrôle de perte, puis bloqué à la garde « collecté = publié » (#545) : **60 profils, 98 prises de parole** collectées et publiées nulle part. C'est exactement le retrait de #1177. Il s'applique au pivot après la fusion, et le brut garde ces paragraphes, parce qu'il dit ce que la source a rendu. Arbitrage de la propriétaire, 08/10 (option A) : le retrait devient une **réduction nommée** de la relation `interventions`, sur le modèle de #888. La garde rejoue `retirer_paroles_d_une_autre_personne` sur les interventions du brut et sur l'acteur publié par le pivot. Le seuil reste 0.

## 1. La mesure

Rejoué sur les 60 profils réels (bruts et pivots du public `5555443e8`, pivot après retrait simulé, 98 retirées) :

| Version de la garde | Déficits |
| --- | ---: |
| `origin/main` avant ce lot | **60**, le blocage du run |
| avec la réduction | **0** |

Les votes européens publiés deux fois (#1011) ne déclenchent pas la garde : le pivot en publie plus que le brut, car le matériau européen n'a pas de contrepartie brute (#683).

## 2. La décision

- `REDUCTION_PAROLES_D_UNE_AUTRE_PERSONNE` sur la relation `interventions`. Elle **rejoue** la fonction du retrait et ne réimplémente pas son critère. L'acteur est lu dans le pivot, parce que c'est là que le retrait le lit.
- `Reduction.compter` reçoit désormais aussi le répertoire pivot. La réduction de #888 l'ignore.
- **Règle pour la suite** (`docs/regles/gardes-avant-commit.md`) : un retrait nommé appliqué au pivot après la fusion se déclare comme réduction **dans le même lot**. #1249 ne l'a pas fait, et ce sont trois runs qui l'ont révélé.

## 3. Alternatives écartées

- **Relancer avec `allow_publication_gaps=true`** : ce run passait, mais le suivant rebloquait, puisque le brut garde ces paragraphes.
- **Retirer aussi les paragraphes du brut** : le brut est la couche fidèle à la source, et la source les attribue bel et bien à ces députés. La retoucher effacerait la trace de ce que la source a publié.
