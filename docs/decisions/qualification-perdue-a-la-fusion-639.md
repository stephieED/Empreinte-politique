# La qualification d'un scrutin se perdait entre la collecte et le profil brut (#639, rang 1) (2026-08-31)

`2026-08-31`

> **En bref** — le rang 1 avait traité les deux bouts qu'il possédait, parseur d'archives et index figés (qui portent bien la qualification : 1 354, 4 417 et 4 105 scrutins pour les XIVe, XVe et XVIe, dont 4, 5 et **34** motions de censure), et le run `33395056902` a pourtant publié `type_scrutin: null` et `demandeur: null` sur les **17 748** scrutins et `type_vote: "vote_texte"` sur les 17 748 — les 66 motions de censure invisibles dans la seule couche que `web/` lit ; deux maillons, tous deux dans une transition — `merge_raw_profile` fusionne `votes[]` en additif pur, l'entrée ancienne gagne et sa clé `(numero_scrutin, date)` ne contient aucun champ neuf, donc les 1 016 / 1 016 votes bruts de `jean-luc-melenchon` restaient à sept clés run après run (le trou exact de #492 sur `mandats[].chambre`, documenté à l'époque comme une particularité de la chambre) ; et `_valeur_scrutin` repliait `type_vote` sur « vote_texte », ce que `construire_index` ne complète jamais ensuite, donc la première occurrence non qualifiée d'un scrutin verrouillait un fait faux (§2 règle 4) ; `backfill_vote_qualification` reporte les trois champs nommés **sans toucher la clé** — vérifié, 1 016 clés identiques avant/après, 1 016 entrées après fusion, 1 016 mappings sur la branche principale de `_pivot_vote_key` —, le défaut `vote_texte` disparaît de l'index et de `scrutin_non_resolu`, et `merge_scrutins_index` conserve la valeur publiée plutôt que de régresser ; rejeu sur données réelles : 0 → 1 016 `type_scrutin`, 0 → 1 010 `demandeur`, 0 → **5** motions pour la XVe, 17 748 scrutins inchangés, 0 erreur de validation ; la couverture se remplit profil par profil et non d'un coup — lire les index figés directement est écarté, l'index pivot ne doit porter que des scrutins qu'un profil référence et la XVIIe n'a pas d'index figé ; la suite était verte des deux côtés, le bout en bout s'arrêtant au profil brut écrit pour la PREMIÈRE fois.

Le rang 1 de #639 a fait entrer `type_scrutin`, `type_vote` et `demandeur` dans
le parseur d'archives et dans les trois index figés. Le run `33395056902` a
quand même publié `pivot_data/scrutins.json` avec **`type_scrutin: null` sur les
17 748 scrutins**, `demandeur: null` sur les 17 748, et `type_vote: "vote_texte"`
sur les 17 748 — donc les **66 motions de censure** invisibles dans la seule
couche que `web/` lit.

Relevé à `4dda4d52`, aux trois étages :

| Étage | État |
| --- | --- |
| Index figés 14 / 15 / 16 | **portent la qualification** — 1 354, 4 417, 4 105 scrutins ; 4, 5 et **34** motions de censure |
| `votes[]` de `jean-luc-melenchon`, profil **brut** | 1 016 / 1 016 sans `type_scrutin` — sept clés : `date`, `legislature`, `numero_scrutin`, `position`, `sort`, `titre`, `url_source` |
| `pivot_data/scrutins.json` | `type_scrutin` `null` × 17 748 |

## Deux maillons, tous deux dans une transition

**Le premier est la fusion additive.** `candidate_profile` recopie bien les
trois champs dans le vote qu'il écrit (`abf5f9dc`, présent dans le commit du
run). Mais `merge_raw_profile` fusionne `votes[]` par `merge_lists_by_key` :
additif pur, **l'entrée ancienne gagne**, et sa clé `(numero_scrutin, date)` ne
contient aucun des champs neufs. Le vote régénéré, qualifié, était écarté à
chaque run. Le profil brut ne pouvait donc jamais acquérir la qualification — et
`build_scrutins_index.py`, dont la docstring dit qu'il lit les profils bruts, ne
pouvait que publier `null`.

C'est exactement le trou que #492 avait déjà rencontré sur
`mandats[].chambre`, et pour lequel `backfill_mandat_chambre` avait été écrit.
Personne n'a fait le rapprochement : le report était documenté comme une
particularité de la chambre, pas comme la conséquence générale de « old entry
wins ».

**Le second est un défaut de valeur.** `scrutins_index._valeur_scrutin` repliait
`type_vote` sur `"vote_texte"`, héritage d'avant la qualification sourcée. Or
`construire_index` ne complète une occurrence suivante que sur un champ resté
`None` : la **première** occurrence non qualifiée d'un scrutin verrouillait le
repli, et aucune occurrence qualifiée ne pouvait plus le corriger. Une motion de
censure votée par un profil régénéré **et** par un profil qui ne l'est pas
serait restée publiée sous le type d'un vote sur texte — un fait faux, et une
règle 4 vidée de son sens.

## Décision 1 — `backfill_vote_qualification`, report nommé sur les votes anciens

Trois champs, nommés (`CHAMPS_QUALIFICATION_VOTE`), reportés sur l'entrée
ancienne de même clé quand elle ne les porte pas. Strictement croissant en
information : ne remplit qu'un champ absent ou vide, n'écrase rien, ne touche
aucun autre champ, ne réordonne rien, ne crée aucune entrée.

**La clé de fusion ne bouge pas**, et c'est le garde-fou de #668 : `_vote_key`
reste `(numero_scrutin, date)`, `_pivot_vote_key` reste `scrutin_id`. Élargir la
clé pour y faire entrer les champs neufs aurait republié chaque vote deux fois —
le défaut mesuré sur `textes_portes`, 468 doublons sur 940 entrées. Vérifié :
sur les 1 016 votes de `jean-luc-melenchon`, l'ensemble des clés est identique
avant et après, la fusion rend 1 016 entrées, et les 1 016 mappings pivot sont
sur la branche principale de `_pivot_vote_key`.

`backfill_vote_qualification` et `backfill_mandat_chambre` sont deux jumeaux
qui **ne partagent pas leur mécanique**, et c'est délibéré :
`tests/test_garde_fou_chambre.py` inventorie tout usage de la clé `"chambre"`
par la fonction qui l'écrit, et un champ passé en tuple d'appel à un helper
générique disparaît de cet inventaire — le garde-fou de #494 cesserait de voir
l'endroit où la chambre d'un mandat est posée. Vingt lignes en double coûtent
moins qu'un inventaire qui ment.

## Décision 2 — `type_vote` n'a plus de valeur par défaut

`_valeur_scrutin` rend ce que le vote dit, et `null` sinon (§2 règle 5). Un
scrutin que personne ne qualifie sort `null` de la construction ;
`merge_scrutins_index` conserve alors la valeur déjà publiée plutôt que de
régresser, donc **aucune valeur ne disparaît de l'index en ligne**. Même retrait
sur `scrutin_non_resolu.type_vote` de `normalize_profil` : cet enregistrement
est le vote tel que la source l'a dit, et c'est le seul vote que le pipeline n'a
pas su rattacher — y affirmer un type serait le pire endroit pour le faire.

## Effet mesuré, et ce qu'il faut en attendre

Rejeu de la chaîne complète sur données réelles — profil brut publié de
`jean-luc-melenchon`, index figé de la XVe, fusion, construction, fusion avec
l'index publié :

| Mesure | Avant | Après |
| --- | ---: | ---: |
| Votes bruts du profil | 1 016 | 1 016 (aucun doublon) |
| `type_scrutin` renseigné | 0 | 1 016 |
| `demandeur` renseigné | 0 | 1 010 |
| Motions de censure identifiées | 0 | **5** (le compte attendu de la XVe) |
| `scrutins.json` après fusion | 17 748 | 17 748, dont 1 016 qualifiés |
| Erreurs de `validate_scrutins_index` | — | 0 |

**La couverture se remplit profil par profil.** Un seul profil régénéré qualifie
les scrutins qu'il a votés ; les 17 748 ne le seront qu'après un run complet. Ce
n'est pas une réserve sur le correctif, c'est la forme de la donnée : un scrutin
n'entre dans l'index que par le vote de quelqu'un.

## Ce que le contrôle de perte en dit

`audit_diff_profils` ne surveille sur `scrutins.json` que la **longueur** de
`scrutins`, en liste signalée non bloquante. Elle est inchangée. Aucun
`allow_declared_losses` n'est requis, et le contrôle n'aurait de toute façon pas
vu le défaut : il compare des comptes, et le compte était juste.

## Le test qui manquait

`test_la_qualification_traverse_larchive_jusquau_profil_brut` allait de
l'archive au profil brut **écrit pour la première fois**, et s'arrêtait là. La
suite entière était verte pendant que le run republiait `null`. Le bout en bout
comporte désormais l'étape qui manquait : un profil brut **déjà publié**,
collecté avant #639, que la régénération doit requalifier.

## Alternative écartée — construire l'index pivot depuis les index figés

Ils portent la qualification, et la lire là aurait qualifié les 17 748 d'un
coup. Écartée : `pivot_data/scrutins.json` ne doit contenir que des scrutins
qu'un profil publié référence, sinon l'index grossit de scrutins que personne ne
vote et `audit_integrite_referentielle` perd son sens de dénombrement. Et la
XVIIe n'a pas d'index figé — la source de vérité serait double.
