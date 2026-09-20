# Aucune filiation de la XVe pour LIOT et Horizons, et `historique_noms` sort des organes de l'Assemblée (#815)

`2026-09-11`

> **En bref** — les deux derniers morceaux de #815. **Les filiations de la XVe ne sont pas déclarées**, sur mesure : parmi les 22 membres de `LIOT-16`, **7** seulement viennent de `LT` (et 8 de la famille UDI) ; parmi les 36 d'`HOR-16`, **6** d'`AGIR-E`, contre **11** de `LAREM-15`. Les successions déjà déclarées sont toutes majoritaires et gardent le nom ou le sigle — LAREM-15 → REN-16 **58 %**, DEM-15 → DEM-16 **64 %**, LR-15 → LR-16 **75 %**, LR-16 → DR-17 **64 %** — ; LIOT et Horizons naissent de plusieurs groupes à la fois, et déclarer une succession à 32 % ou 17 % publierait une filiation que la composition ne porte pas (§2 règle 2). Arbitrage de la propriétaire, 11/09/2026 : **aucune**. **`historique_noms`**, vide sur toutes les fiches depuis l'origine et « laissé à renseigner manuellement », se remplit désormais **depuis les organes de l'Assemblée** : pour chaque fiche, ses organes successifs dans sa législature, avec sigle, libellé, bornes et `organe_an`. Mesuré sur AMO30, committé dans `correspondance_sigles_an[].historique_organes_an` — **29 entrées sur 29, 0 écart** avec les `organes_an` déjà committés — et recopié par l'étape groupe, qui ne lit aucune archive : le chemin de la position politique (#686). Trois fiches ont plus d'un organe : **SOC-16** (`SOC` → `SOC-A`), **DEM-15** (`MODEM` → `DEM`), **UDR-17** (`AD` → `UDR` → `UDDPLR`). Un test confronte chaque entrée des XVIe et XVIIe à la fixture d'archive, et la table refuse un historique qui ne nomme pas exactement `organes_an`. Suite complète à **4 520**, 0 échec.

## Les filiations, mesurées

| XVIe | Effectif | Venus de… |
| --- | ---: | --- |
| LIOT-16 | 22 | UDI (LC → UDI-AGIR → UDI-I → UDI-A-I → UDI_I) 8 · LT 7 · LAREM 2 · DEM 2 · LR 1 |
| HOR-16 | 36 | LAREM 11 · AGIR-E 6 · UDI 6 · LT 1 · DEM 1 |

Membres ayant siégé dans les deux groupes, archive AMO30 du 11/09/2026.

**Écarté** : `LT` → LIOT et `AGIR-E` → HOR, qui publieraient une succession
minoritaire en écartant, pour Horizons, son apport principal ; LIOT comme
**fusion** (`succede_a: [LT, UDI]`), qui ne couvrirait que 15 membres sur 22 et
exigerait de déclarer une chaîne de cinq organes UDI. LIOT et Horizons
commencent donc à la XVIe, comme UDR commence à la XVIIe.

## `historique_noms` : un fait publié, pas un jugement

Le champ décrivait des « renommages entre législatures », alors que la fiche est
une par groupe **et** par législature depuis #700 : ce qui se passe entre deux
législatures est `succede_a`. Ce qui reste à `historique_noms`, ce sont les
renommages **dans** la législature — l'Assemblée ferme un organe et en ouvre un
autre le lendemain. Elle publie chacun avec son libellé et ses bornes ; rien n'est
déduit.

**Pourquoi la table et pas l'archive** : l'étape groupe du run n'a pas l'archive
AMO30 sous la main — aucun cache ne la restaure dans `merge-and-pivot` —, et #686
a déjà tranché que ce qui se mesure sur l'archive se commit et se relit. Le prix
est la duplication de `organes_an` ; elle est **confrontée**, pas tolérée.

**Absent n'est pas vide** : une entrée sans `historique_organes_an` rend `None`,
et la fiche garde la liste vide que le schéma exige. Les deux fiches Sénat, gelées,
restent ainsi.

## Ce qui reste

Rien dans #815 : les identifiants de groupe (#815 lot 1), MoDem, Horizons, LIOT
(#846), UDR (#856), les filiations et `historique_noms` (ce lot). Les fiches
porteront leur historique au premier run après le merge.
