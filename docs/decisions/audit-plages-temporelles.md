<a id="audit-plages-temporelles"></a>
# Épic #316 — tableaux croisés des plages temporelles (#317/#318/#320/#321) : bilan et décisions transverses (2026-08-15)

`2026-08-15`

> **En bref** — tableaux croisés des plages temporelles : bilan de l'épic et décisions transverses.

**Contexte** : #316 fait suite à #174 (« Amélioration de la pipeline audit »,
clos), qui avait ajouté le tableau croisé des **volumes** par candidat
(`compute_tableau_croise_candidats`). Ce tableau répond à « combien
d'éléments ? » mais pas à « sur quelle période ? » — un profil avec 800
votes peut couvrir 2007-2025 ou seulement les 6 derniers mois sans que le
rapport ne le distingue. Distinct de la fraîcheur déjà auditée
(`sources[].synchro_le`, quand la donnée a été *collectée*) : la plage
temporelle porte sur la date des *faits* eux-mêmes (`votes[].date`,
`membres[].debut/fin`, etc.), pas sur leur date de collecte. #316 a décliné
ce besoin en 6 sous-issues sur les trois types de profil (candidat, groupe,
gouvernement) ; cette entrée clôt l'épic et documente les décisions
transverses qui ne rentraient dans le périmètre fichiers d'aucune
sous-issue individuelle.

**Pourquoi une plage temporelle en plus du volume** : un tableau de volume
seul ne distingue pas un profil réellement complet (couverture longue) d'un
profil récemment initialisé mais déjà actif (couverture courte, volume
comparable après quelques mois) — seule la comparaison min/max face à la
période institutionnelle attendue (législature, mandat) permet ce diagnostic
en un coup d'œil. Implémenté en parité sur les trois types de profil plutôt
que sur le seul candidat (déjà couvert par le tableau de volumes historique),
pour que l'audit gouvernement — jusqu'ici totalement absent — ne devienne pas
le seul angle mort restant.

**Pourquoi `amendements_agreges` (groupe) n'a pas de colonne plage
temporelle** : `schema_groupe.py` n'agrège que des compteurs sous
`amendements_agreges` (`nb_amendements`, `nb_adoptes`, `nb_rejetes`,
`nb_irrecevables`, `nb_retires_ou_tombes`, `taux_adoption`,
`par_type_deposant`) — aucun champ date n'existe au niveau de ce bloc
agrégé. `compute_plage_dates_groupes` retourne donc `null` pour cette
cellule, documenté dans le rapport Markdown comme limite structurelle du
schéma actuel (voir [[plage-dates-groupes]]), pas une donnée manquante que
ce chantier aurait dû corriger — ajouter cette date impliquerait un
changement de schéma (`schema_groupe.py`), explicitement mis hors périmètre
par #316 dès sa rédaction.

**Pourquoi `audit_gouvernement_dataset.py` a été construit avec parité
complète plutôt qu'un script minimal** : avant #316, aucun audit
n'existait pour `pivot_data/gouvernements/` — `check_quality_gate.py`
(#212) valide la structure des profils de gouvernement, mais sans rapport
de qualité dédié équivalent à `audit_pivot_dataset.py`/`audit_groupe_dataset.py`.
Un script minimal ne portant que `compute_plage_dates_gouvernements` aurait
répondu à la lettre du tableau croisé demandé, mais aurait laissé
`audit_gouvernement_dataset.py` structurellement asymétrique par rapport aux
deux scripts jumeaux — notamment sans agrégation de `meta.warnings[]`
(nécessaire à `audit_pipeline.py::compute_vue_ensemble` pour agréger les
warnings des trois types de profil, voir [[audit-pipeline-gouvernement]]) ni
volumétrie/complétude/cohérence/fraîcheur comparables. Décision prise lors
de la préparation de l'épic (actée dans le corps de #316 avant même la
sous-issue #319) : construire `audit_gouvernement_dataset.py` sur le même
modèle complet que `audit_groupe_dataset.py` dès #319/#320 (sous-issues 3
et 4/6), pour que la vue d'ensemble compilée par `audit_pipeline.py` (#321)
traite les trois types de profil de façon strictement symétrique — jamais
une vue d'ensemble à 0 gouvernement audité par construction.

**Hors périmètre, noté pour la trace long-terme** :
- `interventions[].date_reponse` (délai de réponse aux questions
  parlementaires officielles) reste hors du tableau des plages temporelles
  de `audit_pivot_dataset.py`, qui se limite au champ `date` de chaque
  entrée (`compute_plage_dates_candidats`/`_plage_dates_champ_simple`) —
  déjà acté dans le corps de #316 (« Hors périmètre »), repris ici pour ne
  pas se perdre au fil des sous-issues individuelles. Un futur besoin
  éditorial sur le délai de réponse serait un chantier séparé.
- Toute alerte/warning basée sur un seuil de plage temporelle (ex. « profil
  ne couvre pas la législature en cours ») : cette épic ajoute l'indicateur
  brut (min/max), jamais de logique de détection d'anomalie dessus. Ajouté
  à `ROADMAP.md`.
- Ajout d'un champ date à `amendements_agreges` (`schema_groupe.py`) pour
  combler le gap noté ci-dessus — changement de schéma, hors périmètre.
  Ajouté à `ROADMAP.md`.
- `check_quality_gate.py` (gate bloquant en CI) : cette épic ne touche que
  l'outil d'audit manuel (`audit_pipeline.py`), jamais appelé par la CI.

