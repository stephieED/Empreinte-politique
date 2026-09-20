<a id="cache-amendements-forme-dedupliquee"></a>
# Cache amendements stocké et lu sous forme dédupliquée (#377) (2026-08-17)

`2026-08-17`

> **En bref** — le cache amendements est stocké et relu sous forme dédupliquée : correctif de l'OOM.

**Contexte** : correctif de l'OOM diagnostiqué dans
[[oom-lecture-amendements-par-candidat]]. Le mécanisme de déduplication
existait déjà (`_aggregate_amendements_index`, écrit pour committer les
législatures figées sous la limite GitHub de 100 Mo par blob) mais était
défait juste avant l'usage qui posait problème : `_load_frozen_amendement_index`
appelait `_expand_aggregated_amendements_index` pour matérialiser le cache
sous forme plate, « pour que le reste du pipeline n'ait pas à distinguer les
deux origines ». C'est ce compromis qui coûtait un facteur ~21.

**Décision** : le cache disque (`AMENDEMENTS_CACHE_DIR/<legislature>/`)
stocke désormais la MEME forme dédupliquée que le fallback committé, en clair
plutôt que gzippée — `amendements.json` (chaque amendement une fois, clé
`numero`) + `index_par_acteur.json` (acteurRef -> `[{numero,
role_signataire}]`). Plus aucune expansion vers la forme plate n'a lieu :
- Lecture : `_read_cached_amendements_agreges` (le couple) et
  `_read_cached_amendements_acteur(legislature, acteur_ref)` qui ne
  matérialise que les entrées de CET acteur. Remplace
  `_read_cached_amendement_index`, qui renvoyait l'index entier expansé.
- Écriture : `_write_cached_amendements_agreges`, partagée par le chemin
  réseau (`_download_and_build_amendement_index`, qui agrège désormais avant
  d'écrire) et le fallback figé.
- `_expand_aggregated_amendements_index` n'est plus utilisée en production
  (conservée : inverse exact, utile aux tests de round-trip).

**Migration automatique** : les deux fichiers sont exigés ensemble pour
qu'un cache soit valide. Un cache écrit avant #377 n'a qu'un
`index_par_acteur.json` plat — il est donc indiscernable d'un cache absent
(`_read_cached_amendements_acteur` renvoie `None`, `amendements_index_deja_figee`
renvoie `False`, section 3d du quality gate rapporte « jamais construit »),
ce qui force sa reconstruction au format compact au lieu de sa relecture en
mémoire. L'écriture écrase le fichier plat au passage, libérant les Go qu'il
occupait. Le rapport du quality gate a été aligné sur ce même verdict, sinon
il aurait annoncé « construit » un index que la collecte ignore.

**Mesures (machine locale, 7,6 Gio de RAM)** :

| Indicateur | Avant | Après |
|---|---|---|
| Cache disque (législatures 14+15+16, hors zips) | 7,9 Go | **480 Mo** |
| Législature 16 seule | 4,67 Go | 211 Mo |
| Pic RSS, 7 candidats × 3 législatures | 6,83 Go (**OOM**) | **1,40 Go** |

**Effet fonctionnel, au-delà de la mémoire** : la collecte d'amendements
fonctionne à nouveau. Avant ce correctif, l'audit rapportait 97,92 % des
profils à 0 amendement (seul Wauquiez en avait) — conséquence directe des
OOM qui tuaient le job avant collecte. Après : Mélenchon 18 721, Guedj
9 516, Le Pen 9 917, Wauquiez 2 702, Philippe 1 966, Attal 343 (vérifié via
`fetch_amendements_officiels` sur le cache migré). À rapprocher de #265
(« Zero amendments according to audit »), qui pourrait se refermer en
grande partie de lui-même sur un prochain run complet.

**Reste ouvert** :
- La législature 17 (active, non figée) n'a toujours pas d'index : son
  téléchargement échoue en `IncompleteRead` côté CDN AN, problème réseau
  distinct et préexistant ([[amendements-legislatures-figees]]).
- Coût CPU : ~8,6 s par candidat pour relire les 3 index compacts (480 Mo de
  JSON reparsés à chaque candidat). Acceptable au volume actuel, mais à
  reconsidérer avant un run à pleine échelle (#376) — une mémoïsation reste
  écartée pour l'instant (l'expansion Python des `{numero, role_signataire}`
  fait passer 480 Mo de JSON à ~3-4 Go résidents si les 3 législatures sont
  gardées simultanément, cf. le pic de 1,40 Go pour une seule à la fois).
- Le pic mémoire lors de la *construction* initiale (chemin réseau :
  `_parse_amendements_zip` produit la forme plate avant agrégation) n'est
  pas traité ici — il ne concerne que le job CI dédié, sur la seule
  législature 17.

**Tests** : `_read_cached_amendements_acteur` (résolution des références,
acteur inconnu → `[]` vs cache absent → `None`, référence orpheline ignorée,
cache hérité plat traité comme absent, cache corrompu), migration du fallback
figé sans expansion, `amendements_index_deja_figee` sur cache hérité, et
alignement du rapport 3d du quality gate. Suite complète : 1148/1148.

