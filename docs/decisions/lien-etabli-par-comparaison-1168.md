# Un lien entre groupes se publie « établi par comparaison des membres », et seulement s'il est mesuré (#1168, lot 3)

`2026-10-03`

> **En bref** — arbitré par la propriétaire le 03/10/2026 (option A) : tous les liens entre groupes successifs se disent établis par Empreinte politique **en comparant les membres**, et la méthodologie le dit en une phrase. Pour que la valeur soit vraie à la lettre, la fiche ne la porte que pour un lien **mesuré** : la table du run écrit, pour chaque lien, `succede_a_mesures` (`{groupe_id, communs, base}`), et `succession_publiee` publie `etabli_par: comparaison_des_membres` quand cette mesure passe la règle — plus de la moitié du plus petit des deux groupes —, `relecture_humaine` sinon. Mesuré sur l'archive du 02/10/2026 : **16 liens mesurés sur 16, tous au-dessus du seuil**, le plus bas à 17 sur 31 (`SOC-15 → SOC-16`). Le décompte n'est **pas publié** : seule la règle l'est, dans la méthodologie. La table écrite à la main seule ne porte aucune mesure : tant que le workflow du lot 2c n'est pas publié sur le dépôt public, les fiches gardent `relecture_humaine`, qui reste exact. **Remplace le « vocabulaire fermé à une valeur » de `fiches-groupe-17e-legislature-700`.**

## Le problème

La page Méthodologie publiée disait : « Ce rattachement est une relecture
humaine, datée ». Chaque lien publié portait `etabli_par: relecture_humaine`.
Depuis le lot 2c, le run peut ajouter un groupe et son lien par le calcul : la
phrase et la valeur deviendraient fausses au premier groupe ajouté.

## Ce qui a été proposé, et ce qui est retenu

| Option | Données | Méthodologie |
| --- | --- | --- |
| **A — retenue** | tous les liens « par comparaison des membres » | une phrase, vraie pour tous les liens |
| B | les 16 liens actuels « relecture humaine », les futurs « comparaison » | deux cas à expliquer |
| C | rien ne change tant qu'aucun groupe n'est ajouté | fausse au premier groupe ajouté |

La phrase proposée pour la méthodologie, montrée à la propriétaire avant
d'être choisie :

> Ce rattachement est établi par Empreinte politique en comparant les membres :
> un groupe prend la suite d'un autre quand plus de la moitié du plus petit des
> deux se retrouve dans l'autre.

La page appartient à l'interface ; ce lot ne la modifie pas.

## Ce qui est décidé

**Deux valeurs, et la seconde se mérite.** `ETABLISSEMENTS_SUCCESSION` porte
`relecture_humaine` et `comparaison_des_membres`. La seconde n'est jamais écrite
à la main : `succession_publiee` la choisit lien par lien.

| Le lien | `etabli_par` publié |
| --- | --- |
| mesuré, et la mesure passe la règle | `comparaison_des_membres` |
| mesuré, sous le seuil | `relecture_humaine` — et la composition le signale `[non soutenu]`, sortie 1 |
| non mesuré (table écrite seule, un côté sans membre connu) | `relecture_humaine` |

**Tous les liens sont mesurés, y compris ceux écrits à la main.** Sinon
« comparaison des membres » reposerait sur ce que la table écrite prétend. La
mesure se fait à chaque mise à jour (`groupes_amo30.mesurer_liens`), sur les
groupes entiers — organes réunis.

**Un lien sous le seuil n'est pas retiré.** La règle ne défait pas ce qu'un
humain a écrit : elle refuse seulement de dire qu'elle l'a établi.

**La mesure ne va pas sur la fiche, et n'ira pas.** Elle vit dans la table du
run, où elle sert à choisir la valeur publiée. Arbitré par la propriétaire le
03/10/2026 : « on ne publiera que la règle dans la méthodo ». Le lecteur lit la
règle — plus de la moitié du plus petit des deux groupes —, jamais le décompte
d'un lien (« 17 sur 31 »), ce qui reste cohérent avec la méthodologie : aucun
taux de renouvellement n'est publié.

## Ce que cette décision remplace

`fiches-groupe-17e-legislature-700` (§3.2) fermait le vocabulaire à une valeur :
« il n'y en aura pas de seconde tant qu'aucune source ne publiera la
succession ». Ce qui tient toujours : aucune valeur ne prétend à une source —
les deux sont des affirmations de ce dépôt, et `source_url` reste interdit sur le
bloc. Ce qui change : une affirmation de ce dépôt peut venir d'une mesure, pas
seulement d'une relecture.

## Mesuré

Archive AMO30 du 02/10/2026, table écrite d'`origin/main` (31 entrées depuis
le lot 2b) : 16 liens, 16 mesurés, 16 au-dessus du seuil, le plus bas
`SOC-15 → SOC-16` à 17 sur 31. Sur l'archive réduite des tests : les liens
XVIe → XVIIe se publient `comparaison_des_membres`, les liens XVe → XVIe
`relecture_humaine` (leurs mandats n'y sont pas).

## Ce qui n'est pas encore vrai en production

- Le workflow du lot 2c (PR #1182) n'est pas publié sur le dépôt public : les
  runs lisent la table écrite seule, sans mesure, et les fiches gardent
  `relecture_humaine`. C'est exact, pas un défaut.
- La phrase de la méthodologie n'est pas écrite : elle attend la session de
  l'interface.

## Alternatives écartées

- **Écrire `comparaison_des_membres` sur tous les liens sans mesure.** Vrai
  aujourd'hui pour les 16, mais rien ne le garantirait demain pour un lien écrit
  à la main.
- **Retirer un lien sous le seuil.** Ce serait laisser la règle défaire une
  relecture humaine sans que personne l'ait décidé.
- **Fermer le vocabulaire à la seule valeur nouvelle.** Une fiche non régénérée
  porte encore l'ancienne, et le portail la refuserait.
