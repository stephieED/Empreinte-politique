# Volumétrie des profils et leviers d'allègement

Échantillon : **379 profils**, **2 282.4 Mo** au total.

| Indicateur | Valeur |
| --- | --- |
| Profil médian | 6.0 Mo |
| Profil moyen | 6.0 Mo |
| Profil le plus lourd | 29.7 Mo (`marine-le-pen.json`) |

## Projection

À **752 profils**, facteur de duplication `raw`/`pivot` = 1.0 :

- **4.42 Go** de données versionnées ;
- seuil de push GitHub (2.0 Go) : **dépassé** ;
- seuil de dépôt recommandé (5.0 Go) : respecté ;
- seuil atteint vers **850 profils**.

> La projection suppose l'échantillon représentatif. S'il ne porte que des profils déjà générés, il est **biaisé vers les figures de premier plan** (gros déposants d'amendements) et surestime probablement le total.

## Leviers, tous sans perte d'information

| Levier | Gain | Part | Remarque |
| --- | --- | --- | --- |
| Fichiers gzippés (.json.gz) | 2 202.1 Mo | **96.5 %** | blob binaire : git ne peut plus déltifier, mesurer l'effet sur .git |
| Externaliser `amendements` hors du profil | 1 243.6 Mo | **54.5 %** | la donnée reste disponible dans un index dédié (modèle #392) |
| Externaliser `amendements:co_signataires` hors du profil | 963.7 Mo | **42.2 %** | la donnée reste disponible dans un index dédié (modèle #392) |
| JSON compact (sans indentation) | 773.8 Mo | **33.9 %** | aucune décision éditoriale, aucun champ touché |
| Externaliser `votes` hors du profil | 248.6 Mo | **10.9 %** | la donnée reste disponible dans un index dédié (modèle #392) |
| Externaliser `interventions` hors du profil | 9.6 Mo | **0.4 %** | la donnée reste disponible dans un index dédié (modèle #392) |

> Aucun levier listé ici ne supprime de donnée : ils la compressent ou la déplacent hors du fichier de profil. C'est délibéré — l'UI n'est pas définitive, et la refonte analytics (#324) aura besoin de champs que l'interface actuelle n'exploite pas encore (#429).
