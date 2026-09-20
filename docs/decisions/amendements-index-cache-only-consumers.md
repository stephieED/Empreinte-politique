<a id="amendements-index-cache-only-consumers"></a>
# Bascule d'`extract-an`/`extract-roster-groupes` vers la lecture cache-only des amendements (#252) (2026-08-13)

`2026-08-13`

> **En bref** — `extract-an` et `extract-roster-groupes` lisent les amendements en cache seul.

**Contexte** : sous-issue 4/6 du plan d'architecture #248, bloquée par #250
([[amendements-index-cache-only-split]]) et #251
([[amendements-index-job-dedie-ci]]). C'est ce changement qui élimine
réellement le problème documenté par #239/#245/#246 (coût réseau payé
indépendamment par chaque job) : les deux sous-issues précédentes ont préparé
le terrain (fonction cache-only isolée, job dédié qui pré-chauffe le cache)
sans changer le comportement observable des appelants.

**Décision** :
1. `fetch_amendements_officiels` (`src/candidate_profile.py`) appelle
   désormais `_read_cached_amendement_index` directement, pour chaque
   législature de `AN_AMENDEMENTS_PATH` — plus d'appel à
   `_build_acteur_amendement_index` (supprimée, devenue un pur orchestrateur
   mort une fois ce dernier appelant retiré) ni, par transitivité, à
   `_download_and_build_amendement_index` depuis ce chemin. Une législature
   absente du cache produit le warning `WARNING_PREFIX_AMENDEMENTS_INDISPONIBLES`
   existant (par législature, cf. #241/#242) au lieu d'un
   `AmendementsIndexError` intercepté — `_read_cached_amendement_index` ne
   lève jamais, elle retourne `None`.
2. `_download_and_build_amendement_index` reste inchangée et devient le seul
   point d'entrée réseau restant pour les amendements officiels, désormais
   appelée exclusivement par le job dédié `extract-amendements-an`
   (`src/build_amendements_index.py`, #251).
3. `.github/workflows/generate-data.yml` : un step `download-artifact` pour
   `amendements-index-an` (`continue-on-error: true`) doit être ajouté sur
   `extract-an` et `extract-roster-groupes`, avant leur étape d'extraction —
   en cas d'échec (artifact pas encore prêt, course sans `needs:` documentée
   dans le job `extract-amendements-an` ; ou job en échec), ces deux jobs
   s'appuient sur ce que la restauration du cache partagé `public-data-cache-an-*`
   contient déjà. **Non appliqué dans le commit associé à cette entrée** : les
   permissions de l'app GitHub utilisée par l'agent ne permettent pas de
   pousser une modification sous `.github/workflows/` — un reviewer humain
   doit appliquer ce step manuellement (voir le commentaire de la PR pour le
   YAML exact).

**Tests** : `test_fetch_amendements_officiels_never_triggers_network_when_cache_absent`
(aucun appel réseau mocké quand le cache est absent pour toutes les
législatures) et `test_fetch_amendements_officiels_returns_cached_amendements_when_index_present`
(comportement inchangé quand le cache est présent) — `tests/test_candidate_profile.py`.
Les tests existants ciblant l'ex-`_build_acteur_amendement_index` (retry,
cache d'échec mémoire/disque, isolation par législature) sont retargetés vers
`_download_and_build_amendement_index`, seule fonction restante à exercer
cette logique.

*Alternative rejetée* : garder `_build_acteur_amendement_index` comme
fonction utilitaire inutilisée « au cas où » — rejeté, code mort non justifié
une fois son unique appelant retiré (sa documentation la présentait
explicitement comme le point d'entrée réservé à `fetch_amendements_officiels`).

