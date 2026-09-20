<a id="resolution-an-prenom-compose-et-gel-runner-etape0"></a>
# Bug de résolution AN pour les prénoms composés, et gel runner déplacé sur l'étape 0 (run #47) (2026-08-17)

`2026-08-17`

> **En bref** — bug de résolution AN sur les prénoms composés, et gel runner déplacé sur l'étape 0.

**Contexte** : run `#47` de `generate-data.yml`, premier run réel après
[[mandats-officiels-an-369]] (étape 4). Résultat inattendu : les échecs
`extract-an` persistent (6/7 députés), mais plus du tout au même endroit que
le run `#45` (avant étape 4, gel systématique sur `fetch_identity`
NosDéputés — 3ᵉ domaine).

**Constat 1 — le gel runner ("shutdown signal") a suivi le point d'appel
réseau, pas disparu** : sur `#47`, 6 candidats (Attal, Retailleau, Wauquiez,
Le Pen, Philippe, Guedj) gèlent immédiatement après le print `=== Nom ===`,
**avant même le premier appel nosdeputes.fr** — donc pendant l'étape 0
(résolution AN, `fetch_identite_officielle_par_slug` /
`_ensure_acteurs_historique_zip_downloaded`), pas pendant le fallback
NosDéputés. Confirme ce que documentait déjà le commentaire au-dessus de
`_get_payload` : un vrai gel runner (assez profond pour empêcher même le
thread démon du watchdog de s'exécuter) peut frapper n'importe quel point
d'I/O réseau du job, pas spécifiquement nosdeputes.fr. Réduire l'exposition
à nosdeputes.fr (#369) a donc déplacé le point de blocage sans traiter la
cause racine — aucune régression du travail #369/#370, seulement une preuve
que ce n'était pas ce qu'on pensait résoudre.

**Constat 2 — bug réel et distinct, corrigé ici** : le seul candidat à
atteindre nosdeputes.fr sur `#47` (Jean-Luc Mélenchon) y arrive parce que sa
résolution AN échoue silencieusement. Cause : `_normalize_search_query` ne
convertit pas les tirets en espaces — `nom_complet` "Jean-Luc Mélenchon" se
normalise en `"jean-luc melenchon"` (tiret interne conservé) alors que le
slug `"jean-luc-melenchon"` remplace **tous** ses tirets par des espaces
avant normalisation, donnant `"jean luc melenchon"` — les deux clés ne
matchent jamais. Bug latent depuis #355 (jamais détecté car jamais testé en
production contre un prénom composé jusqu'à ce que l'étape 4 rende ce chemin
réellement emprunté). Corrigé dans `_build_acteur_nom_index`
(`src/candidate_profile.py`) en appliquant le même `.replace("-", " ")` que
côté slug avant normalisation — `_normalize_search_query` elle-même n'est
pas touchée (partagée avec les requêtes de recherche NosDéputés/NosSénateurs,
où le tiret a un sens différent). Vérifié en local contre un téléchargement
frais du zip AN réel : les 6 candidats se résolvent tous correctement après
le fix (`jean-luc-melenchon -> PA2150`, etc.) — confirmant au passage que
leur échec de résolution AN sur `#47` n'était PAS dû à ce bug (eux se
résolvent très bien), seulement au gel runner du Constat 1.

**Constat 3 — le cache partagé `.cache` (915 Mio en prod) ralentit l'étape 0
pour rien** : chaque shard restaure/extrait l'intégralité de
`public-data-cache-an-*` avant même de savoir s'il en a besoin (40 à 90s de
restore+`tar --use-compress-program unzstd` observés sur `#47`, sur un budget
de 5 min/shard). [[amendements-index-budget-ci-cache-granularite]] (#249)
avait mesuré que les 3 archives amendements (17/16/15) pèsent à elles seules
**≈1,22 Gio**, l'essentiel du volume — alors que l'étape 0 (résolution
identité) n'a besoin que de `.cache/acteurs_an/`. Ce spike avait déjà noté
qu'un `path` de cache séparé par sous-répertoire serait nécessaire pour
changer cette granularité mais l'avait classé hors périmètre. Piste non
implémentée ici (changement structurel sur 3 jobs — `extract-an`,
`extract-roster-groupes`, `extract-amendements-an` — qui mérite sa propre
issue/revue plutôt qu'une édition à l'aveugle) : voir issue de suivi
associée.

**Non résolu** : le gel runner lui-même (Constat 1) reste un problème
d'infrastructure CI, pas applicatif — aucun retry/watchdog ne peut s'en
protéger. Scinder le cache (Constat 3) réduirait la fenêtre d'exposition sans
l'éliminer.

**Tests** : `test_fetch_identite_officielle_par_slug_resolves_hyphenated_prenom`
(nouveau, `tests/test_candidate_profile.py`) — reproduit le bug prénom
composé et vérifie la résolution correcte après fix. Suite complète :
1130/1130.

