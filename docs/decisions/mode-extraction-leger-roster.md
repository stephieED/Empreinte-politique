<a id="mode-extraction-leger-roster"></a>
# Mode d'extraction léger pour `extract-roster-groupes` (#357, sous-issue 6/6 de #351) (2026-08-16)

`2026-08-16`

> **En bref** — mode d'extraction léger pour `extract-roster-groupes`, une fois l'identité résolue côté AN.

**Contexte** : une fois #355 en place (identité biographique des députés
résolue depuis l'AN, indépendante d'un appel réseau NosDéputés préalable),
un membre roster n'a quasiment plus besoin d'appeler nosdeputes.fr pour son
identité/mandats. `extract-roster-groupes` ne consomme, en aval, que
`identite`/`mandats`/`votes`/`amendements` (agrégats de groupe, #349,
`cohesion_votes`/`amendements_agreges`/`mandats_agreges`) — jamais
`dossiers_legislatifs`/`interventions`/`questions_officielles`.

**Décision** : nouveau paramètre `skip_dossiers_legislatifs` sur
`candidate_profile.build_profile()`, symétrique à `skip_interventions` déjà
existant (qui couvrait déjà interventions + questions officielles AN) — il
neutralise l'étape 3 (dossiers NosDéputés, sénateurs) et l'étape 8bis
(`fetch_textes_portes_officiels`, députés). Exposé côté CLI via
`--skip-dossiers-legislatifs` (`generate_all_profiles.py`), combiné à
`--skip-interventions` pour former le mode léger.

**Toujours actif pour ce job, pas un toggle** : contrairement à
`--skip-interventions` sur `extract-an` (piloté par l'input de workflow
`extract_interventions`, réglable par run), les deux flags sont désormais
appliqués *inconditionnellement* dans le step `extract-roster-groupes` de
`generate-data.yml` — l'énoncé de #357 demande de sauter ces champs
« entièrement », pas d'en faire une option : ils ne sont consommés par aucun
agrégat de groupe actuel ni prévu, quel que soit le run. Alternative
écartée : réutiliser `inputs.extract_interventions` pour piloter aussi
`--skip-dossiers-legislatifs` sur ce job — rejetée car elle aurait couplé un
choix de rollout `extract-an` (candidats déclarés, profils complets voulus)
à un choix structurel roster (champs jamais voulus), deux décisions
indépendantes.

**Effet de bord attendu, pas une régression** : les ~750+ profils
`roster_groupe` afficheront `nb_interventions == 0` dans la section « 3 ·
Candidats avec peu d'interventions » de `check_quality_gate.py` — déjà le
cas aujourd'hui pour la quasi-totalité d'entre eux (l'input
`extract_interventions` vaut `false` par défaut) ; ce warning reste un soft
warning (§6 `AGENTS.md`), jamais un hard fail.

> **Deux noms de ce paragraphe ont changé depuis (30/08/2026).** La section s'appelle désormais « Profils avec peu d'interventions » — elle portait sur les 481 profils et non sur les seuls candidats, et son ancien libellé enseignait la confusion que #630 corrige. Et l'input `extract_interventions` s'appelle `collect_interventions` : le nom cité ici n'existe plus dans `generate-data.yml`.
>
> Le raisonnement du paragraphe reste juste ; seuls ses deux renvois étaient morts.
