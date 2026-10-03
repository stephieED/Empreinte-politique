# Les groupes ajoutés par le run : depuis 2017, sous le dernier nom de l'Assemblée et son sigle tel quel (#1168)

`2026-10-03`

> **En bref** — trois points laissés ouverts par le plan de #1168, arbitrés par la propriétaire le 03/10/2026, et qui ne concernent que les groupes que le run ajoute seul. **La borne** : on ne remonte pas avant la XVe législature (2017) — `PREMIERE_LEGISLATURE = 15` reste la seule borne, alors que l'archive AMO30 porte les groupes depuis 2002. **Le nom** : un groupe ajouté par un run, renommé ensuite, prend le dernier nom de l'Assemblée ; la lignée qu'un run a ouverte prend le nom de son groupe le plus récent (`suivre_le_dernier_nom`). **Le sigle** : celui que l'Assemblée donne à la naissance du groupe, tel quel (`LFI-NUPES`, `UDI_I`), sans simplification. Les noms écrits à la main et les identifiants — donc l'adresse des pages — ne bougent jamais.

## Les trois arbitrages

| Point | Arbitré | Ce que le code fait |
| --- | --- | --- |
| Jusqu'où remonter | « on ne remonte pas avant 2017 » | `PREMIERE_LEGISLATURE = 15`, inchangé |
| Le nom d'un groupe renommé après son entrée | « on prend le dernier nom de l'assemblée » | `groupe_nom` suit le libellé du dernier organe ; `lignee_nom` d'une lignée ouverte par un run suit son groupe le plus récent |
| Le sigle d'un groupe ajouté | « on garde tel quel » | le premier sigle de l'Assemblée, à l'entrée, jamais simplifié |

## Ce qui suit le dernier nom, et ce qui ne le suit pas

| Objet | Suit le dernier nom ? |
| --- | --- |
| `groupe_nom` d'un groupe que seul un run a ajouté | **oui** |
| `lignee_nom` d'une lignée que seul un run a ouverte | **oui** — le nom de son groupe le plus récent |
| un nom porté par la table écrite à la main | non : un humain l'a choisi |
| `lignee_nom` d'une lignée écrite à la main, même si un run y ajoute un groupe | non |
| `groupe_id`, `lignee_id`, `fichier` | **jamais** : c'est l'adresse de la page (#836) |
| `groupe_sigle` | non : fixé à l'entrée, tel que l'Assemblée le donne |

La convention retenue pour la lignée est celle des quinze lignées écrites à la
main, nommées d'après leur groupe actuel (« Ensemble pour la République »,
« Droite Républicaine »).

## Comment on sait qu'un nom vient du run

`mettre_a_jour_table` pose `nomme_par: "run"` sur l'entrée de `groupes[]` et de
`lignees[]` qu'il crée, et sur rien d'autre. `suivre_le_dernier_nom` ne touche
que ces entrées-là. Ce n'est pas l'absence de la table écrite qui décide : un
groupe nommé à la main, puis retiré de la table écrite, revient de la table du
run précédente **avec le nom qu'un humain lui a donné** — un test le tient.

## Pourquoi le sigle ne suit pas, quand le nom suit

Le sigle entre dans l'identifiant et dans le nom de fichier ; le faire suivre
déplacerait l'adresse d'une page. Le nom, lui, n'est qu'affiché.

## Pourquoi pas avant 2017

La règle de la moitié n'a été éprouvée que sur les XVe, XVIe et XVIIe
législatures (19 paires d'organes, 16 liens), et le site ne publie rien
d'antérieur. Y remonter serait publier une filiation sur un corpus où la règle
n'a jamais été mesurée.

## Ce qui reste à la main

Tout nom ou sigle d'un groupe ajouté par le run peut être corrigé en l'ajoutant
à la table écrite à la main : elle a toujours raison sur ce qu'elle porte. Une
correction qui changerait l'identifiant d'une lignée déjà publiée est refusée
par la composition (#836).
