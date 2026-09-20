<a id="plage-dates-groupes"></a>
# Tableau croisé des plages temporelles par groupe (#318, sous-issue 2/6 de #316) (2026-08-15)

`2026-08-15`

> **En bref** — tableau croisé des plages temporelles par groupe.

**Contexte** : `audit_groupe_dataset.py` avait un tableau croisé des
*volumes* par groupe (`compute_tableau_croise_groupes`, #174) mais rien
sur la *période* couverte. #316 demande le symétrique pour les trois
types de profil (candidat, groupe, gouvernement) ; cette sous-issue
traite le groupe.

**Décision — format `dates_invalides`** : la sous-issue 1 (candidats,
`audit_pivot_dataset.py`) n'existait pas encore au moment de ce chantier,
donc pas de convention à réutiliser telle quelle. Retenu pour
`compute_plage_dates_groupes` : chaque ligne porte une cellule
`{"min":..., "max":...} | null` pour `cohesion_votes` (calculée sur les
dates valides uniquement, jamais une date par défaut — AGENTS.md §2.5),
et une liste séparée `dates_invalides` (`{groupe_id, champ, valeur}`)
recense chaque date ignorée pour traçabilité, plutôt qu'un simple
compteur global. Les sous-issues 1 et 4 (candidat, gouvernement)
devraient suivre la même forme pour rester cohérentes entre les trois
audits.

**Décision — `amendements_agreges` toujours `null`** : `schema_groupe.py`
n'agrège aucune date au niveau du bloc `amendements_agreges` (seulement
des compteurs). Cellule `null`, documentée explicitement dans le rapport
Markdown (« N/A (non applicable) » + note) comme limite structurelle du
schéma actuel — pas une donnée manquante à corriger dans ce chantier
(ajouter une date à `amendements_agreges` est listé dans le Hors périmètre
de #316).

