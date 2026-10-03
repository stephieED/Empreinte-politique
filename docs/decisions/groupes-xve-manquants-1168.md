# Trois groupes de la XVe n'avaient pas de fiche, et aucune décision ne l'avait voulu (#1168)

`2026-10-02`

> **En bref** — l'audit de filiation (#1168) listait sept organes de groupe de la XVe sans entrée dans `config/groupes_reels.json`. Ce sont **trois groupes** : le groupe **UDI** (cinq organes successifs, `LC` → `UDI-AGIR` → `UDI-I` → `UDI-A-I` → `UDI_I`, 43 personnes), **Libertés et Territoires** (`LT`, 25) et **Agir ensemble** (`AGIR-E`, 23) — **75 personnes distinctes**, dont **57** ont déjà une entrée dans la table des acteurs et **18** sont à collecter par le run. Aucune décision ne les avait écartés : les XVIe et XVIIe étaient complètes (10 groupes sur 10, 11 sur 11), la XVe en comptait 8 sur 11. **Arbitré par la propriétaire le 02/10/2026 : on les ajoute.** Trois entrées, trois lignées d'un seul maillon, **aucun lien `succede_a`** — les filiations `LT → LIOT` et `AGIR-E → Horizons`, refusées le 11/09, le restent, et l'audit les mesure toujours sous le seuil. Les fiches paraissent au prochain run ; d'ici là le portail de qualité compte trois fichiers manquants.

## Le constat

Mesuré le 02/10/2026 sur l'archive AMO30 publiée ce jour (02:34), hors
non-inscrits :

| Législature | Groupes de l'Assemblée | Avec entrée | Sans |
| --- | ---: | ---: | ---: |
| XVIIe | 11 | 11 | 0 |
| XVIe | 10 | 10 | 0 |
| XVe | 11 | 8 | **3** |

Un groupe renommé reçoit un nouvel organe : les sept organes sans entrée sont
trois groupes. Le dépôt ne parlait d'eux qu'à propos de **filiation** — deux
liens refusés le 11/09 (`historique-noms-et-filiations-815`) — jamais de leur
publication. L'absence n'était pas un choix écrit.

## Ce qui est déclaré

| Sigle publié | Organes AN | Période | Personnes | Déjà dans la table des acteurs | Position déclarée par l'AN |
| --- | --- | --- | ---: | ---: | --- |
| `UDI` | `LC`, `UDI-AGIR`, `UDI-I`, `UDI-A-I`, `UDI_I` | 27/06/2017 → 21/06/2022 | 43 | 28 | `divergente` |
| `LT` | `LT` | 18/10/2018 → 21/06/2022 | 25 | 22 | `opposition` |
| `AGIR` | `AGIR-E` | 27/05/2020 → 21/06/2022 | 23 | 19 | `minoritaire` |

Chaque groupe reçoit sa lignée — `AN:LIGNEE:UDI`, `AN:LIGNEE:LT`,
`AN:LIGNEE:AGIR` —, d'un seul maillon, comme `EDS`.

**Le groupe UDI est une union de cinq organes**, le motif `SOC`/`SOC-A` et
`MODEM`/`DEM`. Les dates se suivent au jour près, et le recouvrement d'un organe
au suivant le confirme :

| D'un organe au suivant | Personnes communes | Sur le plus petit des deux |
| --- | ---: | ---: |
| `LC` → `UDI-AGIR` | 35 | 35 |
| `UDI-AGIR` → `UDI-I` | 28 | 28 |
| `UDI-I` → `UDI-A-I` | 28 | 28 |
| `UDI-A-I` → `UDI_I` | 27 | 28 |

**Sa position est `divergente`, et ce n'est pas un choix** : l'Assemblée déclare
`Opposition` sur quatre organes et `Minoritaire` sur `UDI-A-I`. La règle de #686
ne replie jamais deux déclarations contraires sur l'une des deux.

**Agir ensemble est un groupe à part**, né le 27/05/2020 : 10 de ses 23 membres
viennent d'`UDI-A-I`, fermé l'avant-veille — une scission, pas un renommage.

## Les noms publiés

`groupe_sigle` suit l'usage du dépôt, qui simplifie le sigle de l'Assemblée
(`REN` pour `RE`, `LFI` pour `LFI-NUPES`) : `UDI`, `LT`, `AGIR`. `AGIR` plutôt
qu'`AGIR-E` : le sigle entre dans un nom de fichier dont le tiret est le
séparateur (`groupe-AN-AGIR-15.json`).

`groupe_nom` et `lignee_nom` reprennent le **dernier** libellé de l'Assemblée,
comme les douze lignées déjà déclarées : « UDI et Indépendants », « Libertés et
Territoires », « Agir ensemble ».

**L'identifiant de lignée est l'adresse d'une page (#836) : il ne bougera plus
une fois publié.** Les trois sigles, les trois noms et les trois identifiants ont
été montrés à la propriétaire et **validés par elle le 02/10/2026**, avant tout
run. Non vérifié : qu'un tiret dans un sigle casserait réellement quelque chose —
il a été évité par prudence, pas sur mesure.

## Ce que ça ne change pas

Aucun `succede_a`. L'audit, rejoué sur la table complétée, rend toujours
**17 liens retrouvés sur 17 et aucun écart**, et place les nouveaux groupes sous
le seuil :

| Couple | Personnes communes | Sur le plus petit des deux |
| --- | ---: | ---: |
| `UDI-15` → `LIOT-16` | 8 | 22 |
| `LT-15` → `LIOT-16` | 7 | 22 |
| `AGIR-15` → `HOR-16` | 6 | 23 |

Il ne liste plus **aucun** organe sans entrée : un groupe que l'Assemblée
ouvrirait désormais apparaît seul dans cette rubrique.

## Ce qui reste, et qui demande un run

- Les trois fiches de groupe et les trois fiches de lignée n'existent pas encore.
  `check_quality_gate.py` les compte en erreur dure (« fichier manquant »)
  jusqu'au run qui les produit — mesuré : 3 échecs durs, et rien d'autre.
- 18 personnes n'ont pas de profil : le roster leur fabrique un slug (#527,
  #708), la collecte suit.
- `effectif_publie` reste `null` jusqu'à la parution.

## Alternative écartée

**Déclarer ces absences comme voulues**, pour faire taire l'audit. C'était la
première proposition de la session, fondée sur une affirmation non vérifiée —
« c'est voulu ». La question de la propriétaire (« on n'est pas censé collecter
tous les groupes ? ») a fait chercher la décision : il n'y en avait pas.
