# Volumétrie des profils et leviers d'allègement

Population : **752 profils**, **491.4 Mo** au total — mesuré sur tous les fichiers.

Ratios (compact, gzip, poids par champ) calculés sur **60 profils** échantillonnés à intervalle régulier sur la distribution des tailles.

| Indicateur | Valeur |
| --- | --- |
| Profil médian | 0.5 Mo |
| Profil moyen | 0.7 Mo |
| Profil le plus lourd | 3.7 Mo (`yael-braun-pivet.json`) |

## Projection

À **752 profils**, facteur de duplication `raw`/`pivot` = 1.0 :

- **0.48 Go** de données versionnées ;
- seuil de push GitHub (2.0 Go) : respecté ;
- seuil de dépôt recommandé (5.0 Go) : respecté ;
- seuil atteint vers **7835 profils**.

> Population **complète** (752 profils pour une cible de 752) : le total est mesuré, pas extrapolé.

## Leviers, tous sans perte d'information

| Levier | Gain | Part | Remarque |
| --- | --- | --- | --- |
| Externaliser `votes` hors du profil | 483.8 Mo | **98.4 %** | la donnée reste disponible dans un index dédié (modèle #392) |
| Fichiers gzippés (.json.gz) | 459.7 Mo | **93.5 %** | blob binaire : git ne peut plus déltifier, mesurer l'effet sur .git |
| Externaliser `amendements` hors du profil | 0.0 Mo | **0.0 %** | la donnée reste disponible dans un index dédié (modèle #392) |
| Externaliser `interventions` hors du profil | 0.0 Mo | **0.0 %** | la donnée reste disponible dans un index dédié (modèle #392) |
| JSON compact (sans indentation) | 0.0 Mo | **0.0 %** | aucune décision éditoriale, aucun champ touché |
| Externaliser `amendements:co_signataires` hors du profil | 0.0 Mo | **0.0 %** | la donnée reste disponible dans un index dédié (modèle #392) |

> Aucun levier listé ici ne supprime de donnée : ils la compressent ou la déplacent hors du fichier de profil. C'est délibéré — l'UI n'est pas définitive, et la refonte analytics (#324) aura besoin de champs que l'interface actuelle n'exploite pas encore (#429).
