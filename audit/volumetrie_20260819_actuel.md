# Volumétrie des profils et leviers d'allègement

Population : **209 profils**, **1 527.0 Mo** au total — mesuré sur tous les fichiers.

Ratios (compact, gzip, poids par champ) calculés sur **60 profils** échantillonnés à intervalle régulier sur la distribution des tailles.

| Indicateur | Valeur |
| --- | --- |
| Profil médian | 8.1 Mo |
| Profil moyen | 7.3 Mo |
| Profil le plus lourd | 25.6 Mo (`christophe-bentz.pivot.json`) |

## Projection

À **752 profils**, facteur de duplication `raw`/`pivot` = 2.0 :

- **10.73 Go** de données versionnées ;
- seuil de push GitHub (2.0 Go) : **dépassé** ;
- seuil de dépôt recommandé (5.0 Go) : **dépassé** ;
- seuil atteint vers **350 profils**.

> La projection suppose la population représentative. Si elle ne porte que des profils déjà générés, elle peut être biaisée — les profils générés en premier ne sont pas forcément de poids médian.

## Leviers, tous sans perte d'information

| Levier | Gain | Part | Remarque |
| --- | --- | --- | --- |
| Fichiers gzippés (.json.gz) | 1 473.8 Mo | **96.5 %** | blob binaire : git ne peut plus déltifier, mesurer l'effet sur .git |
| Externaliser `amendements` hors du profil | 1 289.5 Mo | **84.4 %** | la donnée reste disponible dans un index dédié (modèle #392) |
| Externaliser `amendements:co_signataires` hors du profil | 1 040.6 Mo | **68.1 %** | la donnée reste disponible dans un index dédié (modèle #392) |
| Externaliser `votes` hors du profil | 232.6 Mo | **15.2 %** | la donnée reste disponible dans un index dédié (modèle #392) |
| Externaliser `interventions` hors du profil | 0.0 Mo | **0.0 %** | la donnée reste disponible dans un index dédié (modèle #392) |
| JSON compact (sans indentation) | 0.0 Mo | **0.0 %** | aucune décision éditoriale, aucun champ touché |

> Aucun levier listé ici ne supprime de donnée : ils la compressent ou la déplacent hors du fichier de profil. C'est délibéré — l'UI n'est pas définitive, et la refonte analytics (#324) aura besoin de champs que l'interface actuelle n'exploite pas encore (#429).
