# Un code de nomenclature n'est pas une profession, et « sans activité professionnelle » n'en est pas une (#641) (2026-08-31)

`2026-08-31`

> **En bref** — 8 des 457 profils qui renseignent `identite.profession` publiaient un code brut `(nn) - ` ; le préfixe est retiré (3 profils) et l'énoncé d'une absence passe à `null` (5 profils), sur un critère en deux parties — la famille du code 8x **et** le libellé de la source — parce que la famille seule nullerait « Elève, étudiant » ; le filtre existe aux deux étages parce que la fusion ne fait jamais régresser un scalaire vers `null`, donc la collecte corrigée seule laisserait les cinq libellés en place indéfiniment.

Mesuré le 31/08/2026 sur les 481 profils publiés : **8 des 457** qui renseignent
`identite.profession` publiaient un code de nomenclature brut, préfixé
`(nn) - `. Le champ est **affiché** — `pivotAdapter.js` le rend comme qualité
sous le nom du profil.

C'est l'idiome de [#absences-publiees-comme-faits-556-558-560](absences-publiees-comme-faits-556-558-560.md) :
une valeur technique de la source recopiée là où une valeur métier était
attendue, et qui passe le seul contrôle existant — « chaîne non vide ».

## Deux cas sous un même motif

| Forme publiée | Profils | Ce que c'est |
| --- | ---: | --- |
| `(33) - Cadre de la fonction publique` | **3** | un libellé bon, précédé de bruit |
| `(85) - Personne diverse sans activité professionnelle de moins de 60 ans…` | **5** | **l'énoncé d'une absence de profession**, publié comme une profession |

Le second est le vrai sujet. La valeur restante n'est pas une profession : c'est
la phrase par laquelle la source dit qu'il n'y en a pas. Elle devient `null`, et
la page dit « profession non renseignée » (AGENTS.md §2 règle 5). Aucune
profession de remplacement n'est inventée.

## Décision 1 — le critère de l'absence est le **code**, corroboré par le libellé

Deux parties, et les deux sont nécessaires :

- **la famille du code** — `8x`, « personnes sans activité professionnelle »
  dans la nomenclature socioprofessionnelle. C'est la structure, pas les mots ;
- **le libellé de la source elle-même**, qui doit contenir « sans activité
  professionnelle ».

La famille seule nullerait `"(84) - Elève, étudiant"`, qui nomme une situation
et non une absence. Le libellé seul s'appuierait sur des mots là où la
nomenclature offre une structure — ce que
[#syceron-archives-verifiees-parseur-510](syceron-archives-verifiees-parseur-510.md)
reproche déjà au lexical.

Ce que le critère **ne** fait pas : décréter la liste des codes d'absence à
partir d'une nomenclature qu'on n'a pas sous la main. Seul le **85** apparaît
dans l'archive au 31/08/2026 ; la règle attrape ses voisins le jour où ils
apparaissent, sans qu'aucun code non observé n'ait été affirmé.

## Décision 2 — deux lecteurs, et le second n'est pas une redondance

| Où | Fonction | Ce qu'il répare |
| --- | --- | --- |
| `src/candidate_profile.py` | `_profession_an` | la collecte : plus jamais de code écrit dans `raw_data/` |
| `src/normalize_profil.py` | `_profession_publiable` | la publication : les **cinq** profils déjà collectés |

Le second est indispensable, et c'est mesurable :
`merge_profile` prend la nouvelle valeur d'un scalaire **seulement si elle est
renseignée, et ne régresse jamais vers `null`**
([#collecte-vide-necrase-jamais](collecte-vide-necrase-jamais.md)). Une collecte
corrigée qui rend `None` laisserait donc les cinq libellés du code 85 en place
**indéfiniment**. Les trois profils au préfixe seul, eux, se réparent par la
collecte : la nouvelle valeur est renseignée, elle gagne. C'est exactement
l'argument de `_uri_hatvp_publiable` (#539) — ce qui est corrigé à la
normalisation, c'est ce qui est **publié**.

Le critère est donc recopié dans les deux modules plutôt qu'importé, comme
`_ACTEUR_REF_DANS_URL` : `normalize_profil` est volontairement découplé de la
collecte. Ce qui empêche les deux copies de diverger n'est pas le texte mais un
test qui les compare forme par forme.

## Ce que la mesure a répondu à la place d'une règle générale

La consigne de #556 est de **filtrer à la lecture, pas champ par champ** — le
convertisseur XML ne connaît pas le nom du champ, donc aucun n'est à l'abri du
marqueur `xsi:nil`. Le préfixe `(nn) - ` n'a pas cette propriété, et c'est
vérifié plutôt que supposé : parcours de **tous** les champs de
`json/acteur/*.json` sur les 3 117 acteurs de l'archive AMO30,
**128 occurrences du motif, toutes sur `acteur.profession.libelleCourant`,
zéro ailleurs**. Le marqueur `xsi:nil` vient du convertisseur ; ce préfixe-ci
vient d'une **nomenclature**, qui n'existe que pour ce champ. Le lecteur est
donc celui de la profession — et il décide sur le **code**, jamais sur le nom du
champ.

## Effet mesuré

| | Profils |
| --- | ---: |
| Profils publiant une profession | 457 / 481 |
| Professions corrigées | **8** |
| … préfixe retiré, libellé conservé | 3 |
| … passées à `null` | **5** |

Les cinq gardent leur bloc `identite` (date et lieu de naissance, circonscription,
URI HATVP) : `identite` est un scalaire surveillé par `audit_diff_profils`, et
aucun ne disparaît. `identite.profession` ne l'est pas — la régression est
signalée, pas bloquante.

## Alternative écartée — publier l'absence comme une couverture

`couverture` dit **pourquoi une liste métier est vide**, par liste ; la
profession est un champ scalaire, pas une liste. Et `meta.provenance_champs`
(#603) dit d'où vient un champ, pas ce qu'il vaut. Publier « la source déclare
une absence de profession » demanderait un troisième mécanisme pour une
information que personne n'a demandée ; `null` et une phrase de couverture à
l'écran suffisent, comme l'issue le tranche.
