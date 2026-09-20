# Volumétrie des profils et leviers d'allègement

Population : **752 profils**, **8 093.1 Mo** au total — mesuré sur tous les fichiers.

Ratios (compact, gzip, poids par champ) calculés sur **60 profils** échantillonnés à intervalle régulier sur la distribution des tailles.

| Indicateur | Valeur |
| --- | --- |
| Profil médian | 5.6 Mo |
| Profil moyen | 10.8 Mo |
| Profil le plus lourd | 51.7 Mo (`patrick-hetzel.json`) |

## Projection

À **752 profils**, facteur de duplication `raw`/`pivot` = 1.0 :

- **7.9 Go** de données versionnées ;
- seuil de push GitHub (2.0 Go) : **dépassé** ;
- seuil de dépôt recommandé (5.0 Go) : **dépassé** ;
- seuil atteint vers **475 profils**.

> Population **complète** (752 profils pour une cible de 752) : le total est mesuré, pas extrapolé.

## Leviers, tous sans perte d'information

| Levier | Gain | Part | Remarque |
| --- | --- | --- | --- |
| Fichiers gzippés (.json.gz) | 7 878.3 Mo | **97.3 %** | blob binaire : git ne peut plus déltifier, mesurer l'effet sur .git |
| Externaliser `amendements` hors du profil | 4 775.0 Mo | **59.0 %** | la donnée reste disponible dans un index dédié (modèle #392) |
| Externaliser `amendements:co_signataires` hors du profil | 3 564.7 Mo | **44.0 %** | la donnée reste disponible dans un index dédié (modèle #392) |
| JSON compact (sans indentation) | 2 809.0 Mo | **34.7 %** | aucune décision éditoriale, aucun champ touché |
| Externaliser `votes` hors du profil | 501.9 Mo | **6.2 %** | la donnée reste disponible dans un index dédié (modèle #392) |
| Externaliser `interventions` hors du profil | 0.0 Mo | **0.0 %** | la donnée reste disponible dans un index dédié (modèle #392) |

> Aucun levier listé ici ne supprime de donnée : ils la compressent ou la déplacent hors du fichier de profil. C'est délibéré — l'UI n'est pas définitive, et la refonte analytics (#324) aura besoin de champs que l'interface actuelle n'exploite pas encore (#429).
