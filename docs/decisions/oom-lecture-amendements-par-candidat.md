<a id="oom-lecture-amendements-par-candidat"></a>
# OOM persistant : lecture per-candidat de l'index amendements, tentative de mémoïsation revertée (2026-08-17)

`2026-08-17`

> **En bref** — OOM par relecture de l'index amendements à chaque candidat ; mémoïsation tentée puis revertée (fuite entre tests).

**Contexte** : après [[oom-reconstruction-amendements-figees]] (ci-dessous),
`build_amendements_index.py` ne rechargeait plus les index déjà figés — mais
l'OOM a persisté sur un run local suivant (`extract-an` puis
`extract-roster-groupes` tués par le kernel, confirmé `journalctl -k`,
anon-rss 4,2 à 5,7 Gio). Cause différente : `fetch_amendements_officiels`
(appelée une fois par candidat) boucle sur les 4 législatures de
`AN_AMENDEMENTS_PATH` et appelle `_read_cached_amendement_index` à chaque
fois — cette fonction, elle, n'a **jamais** été protégée par la correction
précédente (qui ne touchait que `build_amendements_index.py`) : elle
recharge le fichier disque en JSON pur Python à **chaque candidat**, pas
seulement au démarrage du job.

**Tentative #1 (revertée)** : `@lru_cache(maxsize=None)` sur
`_read_cached_amendement_index`, pour ne lire chaque législature qu'une
seule fois par process. Mesuré après coup : tailles réelles sur disque des 3
index figés — `14` 1,46 Gio, `15` 2,04 Gio, `16` 4,35 Gio (`ls -la
.cache/amendements_an/*/index_par_acteur.json`), soit **7,85 Gio cumulés**
rien qu'en JSON brut sur disque (davantage une fois désérialisé en objets
Python — mesuré ~6,8 Gio de RSS rien que pour boucler sur 7 candidats
factices touchant les 4 législatures). Un cache non borné garde les 3
simultanément résidents pour le reste du run — sur une machine à 7,6 Gio de
RAM totale, c'est **pire** que le comportement d'origine (un seul index à la
fois, libéré entre deux candidats, jamais plus d'~4,35 Gio transitoire).
Confirmé par de nouveaux kills OOM survenus *après* application du fix.
**Reverté** : `_read_cached_amendement_index` reste sans mémoïsation.

**Non résolu** : le comportement d'origine (rechargement complet à chaque
candidat) reste risqué sur une machine dont la RAM est du même ordre de
grandeur que la plus grosse législature figée (16 : 4,35 Gio) — chaque appel
pour cette législature s'approche dangereusement du plafond physique, avec
ou sans mémoïsation. Le correctif réel nécessite d'éviter de matérialiser
l'index entier d'une législature pour n'en lire qu'un seul acteur (ex.
restructurer le cache disque en un fichier par acteurRef plutôt qu'un seul
gros `index_par_acteur.json` par législature) — changement de format
cascadant (écriture réseau, fallback figé, quality gate section 3d, script
CI dédié), hors périmètre d'une correction ponctuelle. Voir l'issue de suivi
associée pour le chantier complet.

**Différence CI vs local** : ce risque est spécifique à une exécution locale
« tout-en-un-process » (`scripts/generate_data_local.sh`, qui traite tous
les candidats dans le même process Python) — en CI, `extract-an` est déjà
shardé en matrix par candidat (#344), donc chaque shard ne charge chaque
législature qu'une fois avant que le runner (et sa mémoire) ne soit
recyclé ; `extract-roster-groupes`, lui, n'est pas shardé et reste exposé au
même risque une fois le volume de candidats augmenté (voir #376).

**Tests** : le test de mémoïsation ajouté puis reverté a été retiré avec le
code qu'il testait (`tests/test_candidate_profile.py`). Suite complète :
1143/1143.

