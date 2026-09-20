<a id="oom-reconstruction-amendements-figees"></a>
# OOM lors de la relecture d'un index amendements figé déjà en cache (exécution locale) (2026-08-17)

`2026-08-17`

> **En bref** — OOM à la relecture d'un index figé déjà en cache, en exécution locale.

**Contexte** : exécution locale via `scripts/generate_data_local.sh`.
Symptôme rapporté : la section 3d de `check_quality_gate.py` signale la
législature 15 comme « jamais construit », alors qu'elle est bien dans
`AN_AMENDEMENTS_LEGISLATURES_FIGEES` et que le fallback committé
(`raw_data/amendements_an_figes/15/`) est complet.

**Diagnostic** (log complet relu, `logs/generate_data_local_*.log`) : le
process `python3 src/build_amendements_index.py` s'arrête net avec
`Processus arrêté` juste après avoir commencé la législature 16 — confirmé
via `journalctl -k` comme un **OOM kill** du noyau (`Out of memory: Killed
process ... python3 ... anon-rss:6061768kB` sur une machine à 7,6 Gio de
RAM). Même symptôme un peu plus tard sur `generate_all_profiles.py`, et sur
le process VS Code lui-même (`Killed process ... (code)`) — la fermeture de
fenêtre perçue par l'utilisatrice n'était pas volontaire, c'est le kernel qui
a tué VS Code par pression mémoire.

Cause : `_download_and_build_amendement_index` (candidate_profile.py), sur
cache-hit, `json.load()` **l'intégralité** de `index_par_acteur.json` — y
compris pour une législature figée déjà validée, où ce rechargement ne sert
qu'à re-confirmer une donnée qui, par construction, ne change plus jamais.
Pour la législature 16, ce fichier pèse **4,7 Gio en clair** (forme plate
non dédupliquée — voir [[amendements-legislatures-figees]] pour le choix de
committer sous forme compressée/dédupliquée puis de l'étendre localement) :
le charger en JSON pur Python consomme largement plus que sa taille sur
disque, jusqu'à épuiser la RAM disponible. `build_amendements_index.py`
itère les 4 législatures de `AN_AMENDEMENTS_PATH` dans l'ordre `17, 16, 15,
14` : le kill sur la 16 empêche donc la 15 d'être ne serait-ce que tentée à
chaque exécution — pas un incident isolé, un blocage systématique tant que
le cache de la 16 reste présent sur cette machine.

**Décision** : nouvelle fonction `amendements_index_deja_figee(legislature)`
(candidate_profile.py) — vérifie la présence de `index_par_acteur.json` +
`fraicheur.json["figee"] is True` en ne lisant **que** `fraicheur.json`
(quelques dizaines d'octets), sans jamais toucher au gros index.
`build_amendements_index.py` l'appelle en tête de boucle et saute
entièrement une législature déjà figée en cache, au lieu de la refaire
passer par `_download_and_build_amendement_index`. Mesuré après fix : pic
mémoire de la commande complète 42 Mio (contre ~6 Gio avant, OOM).

**Non touché** : `_download_and_build_amendement_index` elle-même garde son
comportement (cache-hit = relecture complète) — c'est le seul appelant
(`build_amendements_index.py`, confirmé par grep, seul point d'entrée réseau
amendements depuis #252) qui évite maintenant de l'invoquer inutilement pour
une législature figée, plutôt que de complexifier la fonction partagée.

**Tests** : 4 nouveaux tests unitaires pour `amendements_index_deja_figee`
(matérialisé+figé → True, législature active même si le cache y ressemble →
False, non matérialisé → False, JSON invalide dans `index_par_acteur.json`
n'affecte pas le résultat car jamais lu). `test_build_amendements_index.py` :
les 5 tests existants patchent désormais aussi
`amendements_index_deja_figee` (sinon ils dépendaient silencieusement de
l'état réel du cache disque de la machine qui les exécute) + 1 nouveau test
vérifiant qu'une législature figée est sautée sans appeler la fonction
lourde. Suite complète : 1143/1143.

