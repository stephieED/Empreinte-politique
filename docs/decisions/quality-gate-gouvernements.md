<a id="quality-gate-gouvernements"></a>
# `check_quality_gate.py` : section gouvernements (§5), couverture ministérielle proxy par `portefeuille` (#212) (2026-08-14)

`2026-08-14`

> **En bref** — section gouvernements du quality gate : couverture ministérielle approchée par `portefeuille`.

**Contexte** : #212 (plan #184) demandait d'intégrer les profils de
gouvernement au quality gate CI sur le modèle de la section groupes
existante (`_report_groupes`, §4) : hard fail sur structure cassée, soft
fail sur qualité dégradée. Contrairement à `_report_groupes`, `schema_gouvernement.py`
n'a pas de notion de `meta.couverture_roster` (roster_total/profils_disponibles) :
un gouvernement est agrégé localement à partir des profils pivot déjà présents,
sans fetch réseau dédié (`gouvernement_roster.py` n'interroge aucun roster
externe, voir [[gouvernement-roster-desambiguisation]]) — il n'y a donc pas de
dénominateur "effectif réel" à comparer aux `membres[]` obtenus.

**Décision** : `_report_gouvernements()` (miroir de `_report_groupes()`) retient
trois soft fails adaptés :
1. **Couverture ministérielle incomplète** — proxy sur `membres[].portefeuille`
   (nb de portefeuilles confirmés / nb de membres), pas sur un ratio
   roster/profils. Cette incomplétude est structurelle et documentée
   ([[hors-perimetre]] § "Ministerial function") : aucune source open-data
   n'identifie encore le portefeuille précis, donc ce warning se déclenche
   aujourd'hui sur la totalité des gouvernements réels — signal volontairement
   bruyant tant que la source manque, non bloquant (soft), utile pour
   constater automatiquement une future amélioration de couverture.
2. **`textes[]` vide alors que `periode.debut` est renseigné** — mirroir de
   "membres présents mais 0 cohesion_votes" côté groupes.
3. **Signaux réseau `IncompleteRead`** dans `meta.warnings`, propagés depuis
   `gouvernement_textes.py` (même logique que `_GROUPE_NETWORK_SIGNALS`, sans
   les motifs spécifiques roster qui n'ont pas d'équivalent gouvernemental).

Hard fails identiques à `_report_groupes` : fichier attendu manquant, JSON
invalide, `validate_profil_gouvernement()` en erreur — OR-é dans le code de
sortie final aux côtés de `grp_exit`. `pivot_data/gouvernements` ajouté au
scan `IncompleteRead` générique (`ir_dirs`, section 1). Nouveaux arguments
CLI `--gouvernements-dir` (défaut `pivot_data/gouvernements`) et
`--gouvernements-config` (défaut `raw_data/gouvernements_reels.json`), miroir
de `--groupes-dir`/`--groupes-config`. Rapport renuméroté en conséquence :
groupes reste §4, gouvernements §5, ParlTrack (optionnel) devient §6.

**Alternative rejetée** : réutiliser `min_members`/`min_coverage_pct` (seuils
de `_report_groupes`) tels quels pour la couverture ministérielle. Écartée
car ces seuils comparent à un roster réseau qui n'existe pas ici — le seul
dénominateur disponible localement est `len(membres)`, donc un seuil absolu
sur le nombre de membres n'aurait mesuré qu'une réalité déjà garantie par la
construction du roster (`gouvernement_roster.build_gouvernement_roster`), pas
une qualité de donnée dégradée.

Hors périmètre (comme demandé par #212) : pas de branchement dans
`generate-data.yml` (sous-issue #9), pas de nouvelle section dans
`audit_pivot_dataset.py`/`audit_groupe_dataset.py`.

