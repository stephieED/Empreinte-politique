# Un filtre de publication posé avant la fusion ne filtre rien (#641, réouverture) (2026-08-31)

`2026-08-31`

> **En bref** — le lot #641 avait bien vu que « la fusion ne fait jamais régresser un scalaire vers `null` » et en avait tiré un second filtre, mais posé sur le bloc que la **normalisation produit** et non sur celui qui part au fichier : le run `33395056902` a donc nettoyé les 3 professions à préfixe parasite — valeur neuve renseignée, elle gagne — et republié les **5** libellés du code 85 — valeur neuve `None`, `_composer_identite` rend la main à l'ancienne (#601) ; `filtrer_identite_publiee` s'applique désormais **après** la composition, sur les deux chemins de `merge_pivot_profile`, via une table nommée champ par champ (`FILTRES_PUBLICATION_IDENTITE`) parce qu'`identite` porte cinq libellés recopiés d'AMO30 et qu'un filtre général inventerait la sémantique des quatre autres ; effet re-mesuré sur les 481 profils publiés — **5** passent à `null`, 472 inchangés, 4 sans le champ —, la provenance du champ disparaît avec la valeur (#603), et **aucun `allow_declared_losses` n'est requis** : `audit_diff_profils` réduit `identite` à `"<renseigné>"` et ne compare que la présence du bloc, qui reste présent ; filtrer le bloc ancien **avant** la composition est écarté — cela peut faire basculer `bloc_sans_fond` et désarmer la réserve de #597 sur `nom_complet`/`groupe_nom` ; les 3 réussites et les 5 échecs passaient tous la suite, le test manquant portait sur la transition, pas sur les étapes.

[#profession-code-nomenclature-641](profession-code-nomenclature-641.md) a livré
deux filtres — un à la collecte (`candidate_profile._profession_an`), un à la
publication (`normalize_profil._profession_publiable`) — et son propre motif
disait pourquoi le second devait exister :

> le filtre existe aux deux étages parce que **la fusion ne fait jamais
> régresser un scalaire vers `null`** — donc la collecte corrigée seule
> laisserait les cinq libellés en place indéfiniment.

Le raisonnement était juste. Le placement, non. Vérifié sur le run
`33395056902` (commit de données `c5ee19ac`, relu à `4dda4d52`) :

| Volet | Valeur neuve | Résultat publié |
| --- | --- | --- |
| préfixe parasite, **3** profils | `"Cadre de la fonction publique"` | **nettoyé** |
| énoncé d'absence, **5** profils | `None` | **inchangé** — le code 85 republié |

## Ce qui sépare les deux volets

`_profession_publiable` s'applique au bloc que **la normalisation produit**. Or
le bloc **publié** n'est pas celui-là : c'est celui que `_composer_identite`
compose avec le pivot déjà en place, et sa première règle (#601) est qu'« une
absence n'écrase jamais une valeur connue ».

```
brut → _profession_an → None → _profession_publiable(None) → None
                                                              ↓
                        _composer_identite(ancien="(85) - …", neuf=None)
                                                              ↓
                                                    publié : "(85) - …"
```

Une valeur neuve **renseignée** gagne : d'où les 3 profils réparés. Une valeur
neuve **nulle** rend la main à l'ancienne : d'où les 5 qui ne l'étaient pas. Le
filtre n'a jamais vu la valeur qui partait au fichier.

## Décision — le filtre de publication s'applique au bloc composé

`merge_profile.FILTRES_PUBLICATION_IDENTITE` nomme, champ par champ, ce qui doit
traverser un filtre avant d'être écrit ; `filtrer_identite_publiee` l'applique
**après** `_composer_identite`, sur les deux chemins de `merge_pivot_profile`
(profil déjà publié, et premier pivot).

Trois propriétés, dans l'ordre où elles comptent :

1. **C'est la seule position d'où le filtre voit la valeur réellement
   publiée**, d'où qu'elle vienne. Filtrer l'un des deux côtés laisse l'autre
   passer — c'est exactement le défaut qu'on répare.
2. **Strictement décroissant en information** : le filtre ne peut que ramener
   un champ à `None`. Il n'ajoute aucune clé et n'invente aucune profession de
   remplacement (§2 règle 5). Mesuré sur les 481 profils publiés : **5**
   passent à `null`, **472** sont inchangés, **4** ne portent pas le champ.
3. **Pivot seulement.** `raw_data/` est source-proche (AGENTS.md §3) et le
   libellé y est authentique — c'est sa publication *comme profession* qui ne
   l'est pas. Le profil brut le garde, et c'est ce qui rendrait un changement
   d'avis relisible.

La table est nommée champ par champ, jamais générale : `identite` porte cinq
libellés recopiés d'AMO30 (`CHAMPS_IDENTITE_TEXTE_LIBRE`), et un filtre
s'appliquant à tous inventerait la sémantique des quatre autres.

## Effet de bord voulu : la provenance suit la valeur

`deriver_provenance_champs` n'écrit pas d'entrée pour un champ nul. Les cinq
profils perdent donc aussi leur `meta.provenance_champs.identite.profession` —
une provenance laissée seule serait la preuve d'un fait qui n'est plus publié
(#603).

## Ce que le contrôle de perte en dit — mesuré, pas supposé

Aucune déclaration `allow_declared_losses` n'est requise. `identite` est un
scalaire surveillé d'`audit_diff_profils`, mais `_valeur_scalaire` réduit tout
dict à `"<renseigné>"` : seule la **présence** du bloc est comparée, jamais son
contenu, et le bloc reste présent (les cinq profils gardent `nom_complet`,
`date_naissance`…). `meta.provenance_champs` n'est surveillé par aucune
collection. Le contrôle ne bloquera donc pas — et il ne l'aurait pas rattrapé
non plus.

## Alternative écartée — filtrer le bloc ancien à l'entrée de la composition

Elle répare le même cas et coûte un risque en plus : `_composer_identite`
calcule `reserve = bloc_sans_fond(neuf) and not bloc_sans_fond(ancien)`, la
réserve de #597 qui empêche un bloc pauvre d'écraser `nom_complet`/`groupe_nom`.
Nuller `profession` **avant** ce calcul peut faire basculer un ancien bloc de
« a du fond » à « sans fond », donc désarmer la réserve sur des champs qui n'ont
rien à voir. Filtrer après la composition ne touche à aucun verdict.

## Le test qui manquait

Les 3 corrections réussies et les 5 échouées passaient **toute** la suite : rien
ne testait la transition. `tests/test_profession_nomenclature_641.py` éprouve
désormais `merge_pivot_profile` sur un pivot publié portant le code 85 — la
seule étape où le défaut existait.
