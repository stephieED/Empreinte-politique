<a id="audit-pipeline-gouvernement"></a>
# `audit_pipeline.py` : intégration du rapport gouvernement (#321, sous-issue 5/6 de #316) (2026-08-15)

`2026-08-15`

> **En bref** — le rapport gouvernement entre dans `audit_pipeline.py`, à parité avec profils et groupes.

**Contexte** : `audit_pipeline.py` compilait jusqu'ici uniquement les audits
profils (`audit_pivot_dataset.py`) et groupes (`audit_groupe_dataset.py`,
#178). #321 étend la vue d'ensemble compilée à `audit_gouvernement_dataset.py`
(#319/#320), au même niveau de parité que les deux audits existants :
`compute_vue_ensemble`/`build_report` prennent désormais trois rapports en
entrée (`total_gouvernements_audites`, `erreurs_lecture.gouvernements`,
`warnings.par_type[...].gouvernement_ids`), un nouveau flag CLI
`--gouvernements-dir` (défaut `pivot_data/gouvernements`, même comportement
que `--profiles-dir`/`--groupes-dir` sur dossier absent : erreur explicite +
code de sortie 1, jamais de traceback), et une troisième section Markdown
compilée.

**Écart comblé — agrégation des warnings gouvernement** : contrairement à
`audit_pivot_dataset.py` et `audit_groupe_dataset.py`, `audit_gouvernement_dataset.py`
(#319/#320) n'avait jamais implémenté de `compute_agregation_warnings` sur
`meta.warnings[]` — l'epic #316 ne le listait pas explicitement dans
l'architecture cible de ces deux sous-issues, alors même que
`gouvernement_profile.py`/`gouvernement_textes.py` peuplent réellement ce
champ (ex. `gouvernement_profile` : dossier exclu de `textes[]`,
`gouvernement_textes` : statut/chambre de dépôt non déterminable). #321
demandait explicitement un compteur "warnings" gouvernement dans la vue
d'ensemble, ce qui n'était possible qu'en comblant ce trou plutôt qu'en le
contournant silencieusement (une vue d'ensemble à 0 warning gouvernement
aurait été trompeuse — vérifié sur les 10 gouvernements réels de
`raw_data/gouvernements_reels.json` : 518 warnings, types `gouvernement_profile`
et `gouvernement_textes`). Ajouté à `audit_gouvernement_dataset.py`
(`compute_agregation_warnings`, section `warnings` de `build_report`, section
Markdown `## Warnings`), en dehors de la liste "Fichiers concernés" de
l'issue mais strictement au même contrat que la fonction jumelle de
`audit_groupe_dataset.py` (`{"total_warnings": int, "par_type": {type:
{"frequence": int, "gouvernement_ids": [...]}}}`).

**Alternative rejetée** : dégrader silencieusement `compute_vue_ensemble` en
traitant l'absence de section `warnings` côté gouvernement comme "toujours
0" (`.get("warnings", {"total_warnings": 0, "par_type": {}})`), pour rester
strictement dans le périmètre fichiers de #321. Écartée : la donnée
`meta.warnings` existe réellement dans `pivot_data/gouvernements/*.json`
(vérifié en conditions réelles ci-dessus), donc masquer ce warning aurait
contredit le critère d'acceptation "Vue d'ensemble agrégée mise à jour avec
les compteurs gouvernement" et laissé un vrai signal de qualité invisible.

Pure composition inchangée côté `audit_pipeline.py` (AGENTS.md §2.1 : aucune
nouvelle logique de calcul métier n'y est introduite) ; le calcul réel des
warnings gouvernement vit dans `audit_gouvernement_dataset.py`, comme pour
les deux autres audits.

