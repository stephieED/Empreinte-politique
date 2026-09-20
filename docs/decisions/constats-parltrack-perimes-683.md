# Un constat « aucune donnée » ne survit pas à l'arrivée de données (#683, lot 3)

`2026-09-09`

> **En bref** — trouvé en répondant à « la nouvelle pipeline ne va rien écraser ? » **avant** de lancer un run réel, et deux défauts auraient publié des affirmations fausses sans rien faire rougir : `unir_warnings` garde un message de l'ancien écrivain dont la famille n'est pas représentée par le nouveau — et un run qui **trouve** des données n'émet rien dans la famille « aucune donnée », si bien que `jordan-bardella` aurait publié « ParlTrack : aucune donnée trouvée pour le député européen 131580 » **à côté de 1 926 votes, 525 amendements et 255 interventions** ; et les deux constats de couverture du lot 2, qui portent des **compteurs**, n'avaient pas été déclarés dans `FAMILLES_WARNINGS` — vérifié : **12 000 et 18 709 publiés côte à côte** sur le même profil, exactement ce que cette table existe pour prévenir ; d'où `retirer_constats_parltrack_perimes`, sur le patron de `clean_stale_interventions` — une entrée écrite sous un régime révolu se retire **sur preuve** (une entrée portant `institution: "parlement_europeen"`) et non sur le succès d'un appel, qui ne survivrait pas au run suivant (#484) —, appelée en **toute fin** de `merge_pivot_profile` parce qu'appelée plus tôt elle jugerait sur un corpus incomplet, et **se levant d'elle-même** puisque l'enrichissement republie le constat dès qu'il ne trouve plus rien ; **écarté** : faire émettre un message positif dans la même famille pour chasser l'ancien — un avertissement qui annonce que tout va bien n'a pas de destinataire, et ferait de `meta.warnings` un journal de succès alors qu'il est le véhicule de « donnée manquante = donnée manquante ». **Quatrième fois de la journée** qu'un contrôle d'effet trouve ce qu'une suite verte laisse passer. Suite complète à 4 346, 0 échec.

## Contexte

Trouvé en répondant à une question de la propriétaire — « la nouvelle pipeline
ne va rien écraser d'important ? » — avant de lancer un run réel. La réponse
était oui pour l'écrasement, non pour le reste : deux défauts auraient publié
des affirmations fausses dès le premier run, et aucun n'aurait fait rougir quoi
que ce soit.

## Le premier défaut : le constat périmé survit

`unir_warnings` (#600) garde un avertissement de l'ancien écrivain **dont la
famille n'est pas représentée par le nouveau**. C'est ce qui protège un constat
que le run du jour n'a pas eu l'occasion de refaire, et c'est correct.

Mais un run qui **trouve** des données n'émet aucun message dans la famille
« aucune donnée » — il n'a rien à y dire. L'ancien survit donc, intact.

Mesuré avant correction, par simulation de la fusion : le profil de
`jordan-bardella` aurait publié

> ParlTrack : aucune donnée trouvée pour le député européen (identifiant
> ParlTrack 131580) dans les dumps publiés sur parltrack.org/dumps.

à côté de **1 926 votes, 525 amendements et 255 interventions** du Parlement
européen. Le constat était vrai le jour où il a été écrit ; il devient faux le
jour où la lecture est réparée, et **rien ne l'aurait retiré**.

## Le second : mes deux avertissements neufs n'étaient pas des familles

`FAMILLES_WARNINGS` existe parce que plusieurs messages portent des **compteurs**
calculés sur le profil qui les émet. Les deux constats de couverture ajoutés au
lot 2 en portent — « 18 709 scrutin(s) », « 179 explication(s) » — et je ne les
avais pas déclarés.

Vérifié : deux fusions successives publiaient **12 000 et 18 709 côte à côte**,
sur le même profil, pour la même liste. C'est exactement ce que cette table
existe pour prévenir, et l'oubli le reproduisait.

## Décision

### 1. Les deux constats entrent dans `FAMILLES_WARNINGS`

Rien de plus : la table faisait déjà le travail, il fallait l'y inscrire.

### 2. Une reprise, sur preuve, à la fin de la fusion

`retirer_constats_parltrack_perimes` suit le patron de
`clean_stale_interventions` et `clean_stale_textes_portes` : **une entrée écrite
sous un régime révolu ne se corrige pas en changeant la règle de fusion, elle se
retire sur preuve.**

La preuve est le corpus lui-même — une entrée portant
`institution: "parlement_europeen"` dans l'une des quatre listes — et **non le
succès d'un appel**, qui ne survivrait pas au run suivant. C'est la même
distinction qu'au #484 : ce qui compte est ce que le profil porte, pas ce qu'un
appel a rendu.

Elle est appelée **en toute fin** de `merge_pivot_profile`, après les quatre
listes : appelée plus tôt, elle jugerait sur un corpus incomplet.

**La reprise se lève d'elle-même.** Si la source cesse de porter cette personne,
l'enrichissement republie le constat au run suivant : l'absence redevenue vraie
se redit (§2 règle 5). Aucune date de retrait à prévoir.

## Ce que ces deux défauts ont en commun

Ni l'un ni l'autre n'aurait fait échouer un run. Le premier publiait une phrase
fausse sous le nom d'une personne ; le second publiait deux comptes dont un
faux. Les 4 343 tests du lot 2 étaient verts, et le portail rendait 0.

C'est la quatrième fois de la journée qu'un contrôle d'effet trouve ce qu'une
suite verte laisse passer — et cette fois, ce qui l'a déclenché est une question
de la propriétaire, pas une mesure planifiée.

## Alternative écartée

**Faire émettre à l'enrichissement un message positif dans la même famille**
(« ParlTrack : 1 926 votes trouvés »), qui aurait chassé l'ancien par le
mécanisme d'union existant, sans reprise. Écarté pour deux raisons : le message
n'a aucun destinataire — un lecteur n'a que faire d'un avertissement qui annonce
que tout va bien —, et il ferait de `meta.warnings` un journal de succès, alors
que le champ est le véhicule de « donnée manquante = donnée manquante »
(§2 règle 5).
