# L'écriture marque les tranches closes, et le `nombre` vient de l'archive (#691, lot 3b)

`2026-09-09`

> **En bref** — **le lot qui cesse d'écrire** : `partitionner(profil, acteur_ref=…)` marque `derivee` toute tranche de législature close que l'archive couvre, elle sort du dictionnaire rendu et `ecrire_profil_brut` la supprime **par le nettoyage des « non attendus » qui existait déjà**, sans une ligne de plus ; sans `acteur_ref` rien n'est marqué et le comportement est celui d'avant à l'octet près — `generate_all_profiles` le transmet depuis la table relue, `merge_profile` depuis le manifeste déjà écrit (**la collecte amorce, la fusion reconduit**) ; **le `nombre` vient de l'archive**, arbitrage de la propriétaire : les deux comptes coïncident aujourd'hui (854 tranches sur 854) et le choix porte sur le jour de la divergence — le compte de la collecte ferait lever `recomposer` et rendrait le profil **illisible**, déplaçant l'erreur très loin de sa cause (#771, 1 h 18), quand l'archive laisse la lecture tenir et fait déclarer l'écart **là où il naît**, par `nombre_collecte` écrit **uniquement** en cas d'écart (un champ qui n'apparaît que quand ça ne va pas se remarque, #510) ; **l'ordre devient par blocs** dès qu'une tranche est dérivée — elle est relue dans celui de l'archive (16 915 positions sur 16 915 différentes) — et ça ne coûte rien de publié, aucun consommateur ne lisant l'ordre, tandis que l'aller-retour octet pour octet reste vrai pour tout profil **sans** tranche dérivée ; **mesuré sur `mathilde-panot`** : **59,6 → 28,2 Mo (−53 %)**, seule la tranche 17 subsiste, **54 559 amendements relus pour 54 559**, ensemble identique, et **aucun `nombre_collecte`** ; **un OOM killer en route** — `signatures()` chargeait aussi le store alors qu'elle n'a besoin que de l'index par acteur (10,5 Mo contre plusieurs centaines), les mémos sont désormais séparés par fichier, et le test qui prétendait le couvrir ne vérifiait que l'absence d'appel à `reconstruire_tranche` : **un test qui vérifie l'appel n'a rien dit du coût** ; le premier run sous cette forme supprimera **5,55 Go**, la XVIIe (3,64 Go) restant écrite faute d'archive. 12 tests neufs, suite complète à 4 235, 0 échec.

## Contexte

Les trois lots précédents ont établi, dans l'ordre : qu'une tranche de
législature close se reconstruit **exactement** depuis l'archive (120 profils,
568 771 amendements, zéro écart) ; que le lecteur sait en servir une ; que le
garde-fou « collecté = publié » sait la compter. **C'est ce lot qui cesse
d'écrire.**

## Décision

`partitionner(profil, *, acteur_ref=...)` marque `derivee` toute tranche dont la
législature est close et que l'archive couvre pour cet acteur. Elle sort du
dictionnaire rendu, donc `ecrire_profil_brut` la supprime — **par le nettoyage
des « non attendus » qui existait déjà**, sans une ligne de plus.

Sans `acteur_ref`, rien n'est marqué et le comportement est celui d'avant, à
l'octet près. Les deux appelants qui comptent le transmettent :
`generate_all_profiles` depuis la table relue, `merge_profile` depuis le
manifeste déjà écrit — **la collecte amorce, la fusion reconduit**.

## Le `nombre` vient de l'archive — arbitrage de la propriétaire

Les deux comptes coïncident aujourd'hui : 854 tranches sur 854 couvertes,
568 771 amendements sans écart. La question portait sur le jour où ils
divergeront.

| `nombre` = | Le jour de la divergence |
| --- | --- |
| la collecte | `recomposer` lève : le profil devient **illisible** |
| **l'archive** | la lecture tient ; l'écart se déclare à l'écriture |

L'archive, donc. Rendre un profil illisible parce que la collecte a trouvé autre
chose déplacerait l'erreur très loin de sa cause — le patron que #771 a payé
1 h 18. L'écart se déclare **là où il naît**, par `nombre_collecte`, écrit
**uniquement** en cas d'écart : un champ qui n'apparaît que quand quelque chose
ne va pas se remarque, quand un champ toujours présent et presque toujours égal
ne se lit plus (#510).

## L'ordre devient par blocs, et ça ne coûte rien de publié

Dès qu'une tranche est dérivée, l'ordre d'origine n'est plus restituable : la
tranche est relue dans celui de l'archive (mesuré sur `mathilde-panot/16.json` :
ensemble identique, **16 915 positions sur 16 915 différentes**). Le manifeste
porte alors un ordre **par blocs**, chaque tranche d'un seul tenant.

Ce que ça coûte : rien. Aucun consommateur ne lit l'ordre — `audit_diff_profils`
relève une liste par un **entier**, et le site trie ce qu'il affiche. Ce que ça
préserve : l'aller-retour identique octet pour octet reste vrai pour tout profil
**sans** tranche dérivée, le seul cas où il était testé et le seul où il a un
sens.

## Mesuré sur un profil réel

`mathilde-panot`, 54 559 amendements sur trois législatures :

| | Avant | Après |
| --- | ---: | ---: |
| Disque | 59,6 Mo | **28,2 Mo** (−53 %) |
| Tranches fichiers | 15, 16, 17 | **17 seule** |
| Amendements relus | 54 559 | **54 559**, ensemble identique |
| `nombre_collecte` | — | **aucun** : collecte et archive coïncident |

## Un OOM, et ce qu'il a corrigé

Le premier essai s'est fait **tuer par l'OOM killer** sur une machine à 7 Go :
`signatures()` chargeait aussi le store des amendements, alors qu'elle n'a besoin
que de l'index par acteur — 10,5 Mo contre plusieurs centaines en clair. Les
mémos sont désormais **séparés par fichier**, et deux tests le tiennent : compter
ne charge pas le store, reconstruire le charge.

Le test qui existait déjà — « compter n'ouvre pas le store » — vérifiait
seulement qu'aucun appel à `reconstruire_tranche` n'était fait. Il ne pouvait pas
voir le chargement réel, et il est passé au vert pendant que le process mourait.
**Un test qui vérifie l'appel n'a rien dit du coût.**

## Ce qui reste

Le premier run qui écrira sous cette forme supprimera les tranches closes du
corpus — **5,55 Go**. Rien à faire de plus : le nettoyage est celui de
`ecrire_profil_brut`, et l'archive porte déjà les données. Ce qu'il faudra
vérifier dans son log : le compte de profils écrits, l'absence de
`COLLECTE_NON_PUBLIEE`, et l'apparition d'un éventuel `nombre_collecte` au diff.

La XVIIe (3,64 Go) reste écrite : elle est vivante et n'a pas d'archive figée.
