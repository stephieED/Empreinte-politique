<a id="collecte-vide-necrase-jamais"></a>
# Une collecte vide n'écrase jamais une collecte non vide (#465) (2026-08-20)

`2026-08-20`

> **En bref** — sous `--no-merge`, un champ revenu vide ne remplace jamais un champ non vide — par champ, jamais par profil.

En mode écrasement (`--no-merge`), la fusion additive ne protège plus rien. Or
une **sous-collecte** peut échouer sans que le profil écrit n'ait l'air anormal :
identité introuvable, endpoint en panne, archive indisponible. Le profil part
alors avec un champ simplement vide, et il remplace le bon.

## Ce que ça a coûté

Run `32302557156` du 19/08/2026, lancé en écrasement pour propager une
correction :

| profil | perte | ce que portait le profil écrit |
| --- | --- | --- |
| `jean-luc-melenchon` | 18 721 amendements, 1 016 votes, 33 textes | « aucun mandat français connu — identité introuvable » |
| `bruno-retailleau` | 36 textes portés | « votes introuvables » |
| `marine-le-pen` | 23 textes portés | **aucun avertissement** |

Le troisième cas est le plus instructif. Ses amendements (13 991) et ses votes
(1 813) sont **intacts** : seuls ses textes portés sont tombés à zéro, et rien
dans le profil ne le signalait. Un garde-fou conditionné à la présence d'un
avertissement ne l'aurait pas vu. Un garde-fou raisonnant sur le profil entier
non plus.

## Ce que le diagnostic initial avait manqué

J'avais d'abord attribué ces pertes à la publication d'un job **annulé** — quatre
shards l'avaient été — et au `if: always()` de l'étape de publication. C'était
faux, et vérifiable : le profil de Mélenchon a été écrit à 21:13:30, **deux
minutes après le lancement**, bien avant l'annulation de son job. Celui de Le Pen
ne portait aucune trace d'interruption.

L'annulation n'est pas la cause. La cause est qu'un `[]` non mesuré a la même
forme qu'un `[]` constaté, et que `--no-merge` ne fait pas la différence.

## La règle, et elle existait déjà ailleurs

> Une collecte **vide** ne remplace jamais une collecte **non vide**. Champ par
> champ, pas profil par profil.

Ce n'est pas une invention : #427 l'a énoncée pour les gouvernements, et le code
le dit noir sur blanc — *« distinguer "zéro dossier constaté" de "collecte
incomplète" ; sans elle, l'appelant écraserait des profils avec un `textes: []`
qui n'a jamais été mesuré »*. Les profils étaient le seul endroit à ne pas
l'appliquer.

## Ce que la règle ne bloque pas

**Une correction de clé aboutit toujours.** #440 a remplacé 2 018 amendements par
944 — une baisse de plus de moitié, parfaitement légitime, et non bloquée :
944 n'est pas zéro. Seul le passage à **zéro** est refusé. C'est ce qui distingue
ce garde-fou d'une demi-fusion, laquelle rendrait toute correction impossible et
recréerait le défaut de [[publication-scopee-artifacts]].

Et le champ est traité **isolément** : Le Pen aurait gardé ses 23 textes portés
tout en voyant ses amendements écrasés normalement.

## Levée explicite, préservation jamais silencieuse

`--autoriser-collecte-vide` permet de vider délibérément un champ. Sans lui, la
préservation est **imprimée** : « collecte vide sur *champ* — entrées existantes
PRÉSERVÉES malgré `--no-merge` ». Une préservation muette serait un autre défaut :
on croirait la collecte réussie.

## Deux couches, pas une

| | quand | attrape |
| --- | --- | --- |
| ce garde-fou | à l'écriture du profil | la collecte ratée, avant qu'elle ne touche le disque |
| [[controle-de-perte-avant-commit]] (#461) | avant le commit | le reste — baisse partielle, profil disparu |

La première empêche le dégât, la seconde le rattrape s'il passe quand même.
Aucune ne remplace l'autre : une baisse de 2 035 à 5 votes n'est pas un vide, et
seul le contrôle de perte la verrait.

## Ce que ça ne corrige pas

Le `if: always()` de l'étape de publication reste en place, et c'est désormais un
choix : puisque la destruction ne vient pas de là, le publier reste utile — un
job préempté en fin de course garde son travail. La question de savoir si un
artifact de job annulé doit être marqué comme partiel se pose toujours, mais
elle ne porte plus l'urgence qu'on lui prêtait.

