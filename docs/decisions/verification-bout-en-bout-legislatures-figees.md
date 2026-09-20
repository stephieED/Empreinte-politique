<a id="verification-bout-en-bout-legislatures-figees"></a>
# Vérification de bout en bout des législatures figées 15/16 (#273, clôture de l'epic #268) (2026-08-17)

`2026-08-17`

> **En bref** — vérification de bout en bout des législatures figées 15/16 : aucun changement de code nécessaire.

**Contexte** : sous-issue 5/5 de #268, débloquée une fois #269/#270/#271/#272
fermées. Vérification uniquement, aucun changement de code attendu — et
aucun n'a été nécessaire.

**Constat préalable, non prévu par l'issue** : la vérification n'a pu
aboutir qu'après la résolution de deux problèmes découverts entre-temps, qui
empêchaient toute collecte d'amendements et auraient fait conclure à tort à
un échec de l'epic #268 — [[cache-amendements-forme-dedupliquee]] (#377,
l'ancienne forme plate déclenchait l'OOM killer avant collecte) et
[[nettoyage-archive-brute-amendements]] (#264). Avant eux, l'audit
rapportait encore 97,92 % des profils à 0 amendement alors que les index
figés étaient déjà committés et corrects.

**Critère 1 — quality gate §3d** (run local réel, exit code 0) : les
législatures 14, 15 et 16 sont rapportées **❄️ figé (dossier clos, non
reconstruit)**, jamais **❌ jamais construit**. Seule la 17 est en « jamais
construit » — législature active, `IncompleteRead` répétés sur le CDN
`data.assemblee-nationale.fr`, problème réseau distinct et préexistant
([[amendements-legislatures-figees]]), explicitement hors périmètre.

**Critère 2 — non-régression du symptôme « zero amendments »** (profils
régénérés avec le pipeline réel, aucun appel réseau pour 14/15/16) :

| Profil | L14 | L15 | L16 | Total pivot |
|---|---|---|---|---|
| `damien-abad` | 2 896 | 5 989 | 1 589 | 10 474 |
| `jerome-guedj` | 288 | 0 | 5 827 | 6 115 |

Deux points élucidés au passage, tous deux préexistants et **non** des
pertes de données — consignés pour éviter qu'une future vérification ne les
prenne pour des régressions :
1. Le champ `legislature` n'existe pas dans le schéma pivot des
   `amendements[]` (contrairement à `textes_portes[]`, qui le porte) : la
   ventilation par législature ci-dessus provient des profils bruts, pas des
   pivots. Choix de conception de `schema_pivot.py`, jamais remis en cause.
2. L'index contient 9 217 *références* pour Guedj en L16 alors que son
   profil n'affiche que 5 827 amendements : ce sont 5 827 numéros distincts,
   dédupliqués par `merge_profile._amendement_key` sur `(numero,
   texte_vise, date)`. Un même amendement peut légitimement être référencé
   plusieurs fois pour un même élu (rôles de signature multiples).

**Critère 3** : #265 commentée pour signaler la résolution de la piste
légis 15/16 (fix 4 de son investigation), sans clore l'issue — ses fixes
1/2/3/5 restent ouverts, hors périmètre de #268.

**Reste attendu** : la section 3c (couverture amendements) affiche encore 39
avertissements « collecte en échec » — ce sont des warnings *hérités* dans
les pivots non régénérés depuis les runs cassés par l'OOM, pas un défaut
actuel du pipeline. Ils se purgent d'eux-mêmes à la régénération
(`merge_profile._prune_stale_warnings` retire ce warning dès qu'un profil
porte des amendements), ce que confirment les deux profils régénérés
ci-dessus : zéro warning amendements pour eux.

**Tests** : suites demandées par l'issue au vert (`test_candidate_profile.py`,
`test_quality_gate_amendements.py`, `test_build_amendements_index.py`, 182
tests) ; suite complète 1151/1151.

