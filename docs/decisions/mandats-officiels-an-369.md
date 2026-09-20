<a id="mandats-officiels-an-369"></a>
# Mandats commission/groupe_amitie/extra_parlementaire sourcés depuis l'AN, fetch_identity NosDéputés rendu conditionnel (#369, complet), watchdog générique sur tous les téléchargements zip (#370, complet) (2026-08-17)

`2026-08-17`

> **En bref** — mandats commission/groupe d'amitié/extra-parlementaire sourcés depuis l'AN ; watchdog générique sur tous les téléchargements zip.

**Contexte** : run `#44` de `generate-data.yml` — tous les shards `extract-an`
en échec, y compris les candidats non-députés (finissaient auparavant en
15-20s). Log de Bruno Retailleau : les 8 tentatives `fetch_identity`
(NosDéputés) se terminent normalement, puis silence total (~31s, aucun
print) avant `shutdown signal`. Diagnostic : `fetch_identite_officielle_par_slug`
(#355) est appelée sans condition juste après, et déclenche
`_ensure_acteurs_historique_zip_downloaded` — un `requests.get(...,
timeout=(TIMEOUT, 600), stream=True)` en un seul essai, **non protégé** par
le pattern watchdog déjà en place sur `_get_payload` (#340/[[get-payload-retry]]).
Cache disque partagé entre shards via la même clé GitHub Actions : le
premier shard à tenter ce téléchargement (Mélenchon) ayant lui-même échoué
avant de sauvegarder le cache, chaque shard suivant repartait à froid —
effet boule de neige expliquant l'échec de tous les shards, pas seulement
certains.

**Décision 1 — `download_with_watchdog` (#370, complet)** : généralisation
de `_get_with_watchdog` aux téléchargements de fichier — thread démon +
budget mur indépendant, écriture d'abord dans un fichier temporaire (`.part`)
renommé seulement en cas de succès complet (un thread abandonné continuant
d'écrire en arrière-plan ne corrompt jamais `dest_path`). Extrait dans un
module dédié `src/download_watchdog.py` (pas laissé dans `candidate_profile.py`) :
`gouvernement_textes.py` est déjà importé par `candidate_profile.py`, un
helper partagé y vivant aurait créé une dépendance circulaire. `headers`/
`timeout` passés en paramètre plutôt que codés en dur — chaque module garde
son réglage existant (`candidate_profile.py`/`gouvernement_textes.py`/
`syceron_debates.py` : défaut 120s ; `parltrack_dumps.py`/`mep_profile.py` :
900s, dumps de plusieurs centaines de Mo, budget mur dimensionné en
conséquence via `hard_timeout_seconds` explicite plutôt que le défaut).

Appliqué aux 6 points d'appel non protégés listés dans #370 :
`_ensure_acteurs_historique_zip_downloaded` (priorité #1, cause confirmée du
run #44), boucle questions officielles AN (`candidate_profile.py`),
`ensure_dossiers_zip_downloaded` (`gouvernement_textes.py` — simplifie au
passage : l'écriture atomique manuelle qui y existait déjà devient
redondante avec celle du helper), `_download_dump` (`parltrack_dumps.py` et
`mep_profile.py`, fonctions dupliquées à l'identique dans les deux fichiers),
`_download_syceron_zip` (`syceron_debates.py`).

Effet de bord découvert en testant : `unittest.mock.patch("module.requests.get",
...)` patche l'objet module `requests` partagé (`sys.modules`), pas une copie
par fichier — patcher `candidate_profile.requests.get` intercepte donc aussi
les appels faits depuis `download_watchdog.py`. Les 54 tests existants qui
patchaient déjà `candidate_profile.requests.get` pour les téléchargements
zip AN ont continué à passer sans modification.

**Décision 2 — mandats commission/groupe_amitie/extra_parlementaire sourcés
depuis l'AN (#369, partiel)** : `_build_acteur_identite_index()` lisait déjà
`acteur.mandats.mandat[]` en entier mais n'en extrayait que le mandat
`ASSEMBLEE` (circonscription/place hémicycle) — les mandats `COMPER`/`GA`/
`ORGEXTPARL` étaient lus puis jetés, sans passer par `_build_organe_index()`/
`fetch_organe()` (#353) pourtant déjà disponible pour les résoudre en noms
lisibles. Ajout de `_build_acteur_mandats_index()` (même zip déjà téléchargé
et parsé pour l'identité/les organes, aucun coût réseau supplémentaire) et
`_extract_mandats_officiels(acteur_ref)`, équivalents AN de `_extract_mandats`
(NosDéputés). Dans `build_profile`, étape 5 : quand l'acteur est résolu côté
AN, les mandats des 3 catégories partagées viennent désormais de l'AN
(NosDéputés ne complète que le mandat électif de base et les catégories non
couvertes) — évite un doublon du même organisme sous un libellé différent.

*Mapping* : `COMPER` → `commission`, `GA` → `groupe_amitie`,
`ORGEXTPARL` → `extra_parlementaire` (`_TYPE_ORGANE_TO_CATEGORIE`). Le reste
(`MISINFO`/`CNPE`/`DELEG`/`GE`/`GEVI`/`PARPOL`/`CMP`/`API`...) n'est pas
mappé — périmètre minimal-invasif, cohérent avec ce que #349/#361 excluent
déjà de l'agrégation de groupe.

**Décision 3 — étape 4, `fetch_identity` (NosDéputés) rendu réellement
conditionnel** : la résolution AN (`fetch_identite_officielle_par_slug`) est
déplacée en tout début de `build_profile` (nouvelle étape 0, avant l'ancienne
étape 1). `fetch_identity` n'est alors appelé que si `chambre != "deputes"`
(sénateurs, non couverts par l'AN) ou si l'AN n'a pas trouvé l'acteur
(`acteur_ref_an is None`, repli complet inchangé) — pour un député trouvé côté
AN, les 8 requêtes NosDéputés (identité) sont désormais entièrement évitées.
Cela nécessitait d'abord d'étendre `_build_acteur_identite_index()` (déjà fait
en préparation) pour qu'elle porte aussi `groupe_sigle`/`groupe_nom` (mandat
`GP` courant, résolu via `_build_organe_index()`), `mandat_debut`/`mandat_fin`
(bornes du mandat `ASSEMBLEE` courant) et `nb_mandats` (nombre de mandats
`ASSEMBLEE`) — sans ces champs, sauter NosDéputés aurait fait disparaître
silencieusement le groupe parlementaire déclaré et le mandat électif de base
pour chaque député résolu côté AN. Le nom de recherche d'interventions (étape
2) retombe sur `identite_an.get("nom_complet")` quand `identity_raw` n'a pas
été récupéré. L'entrée `mandat_electif` (jusqu'ici produite uniquement par
`_extract_mandats(parlementaire)`) est reconstruite depuis `identite_an`
quand NosDéputés n'est pas appelé, avec le même format que l'original
(`categorie`/`type`/`label`/`debut`/`fin`/`actif`).

`identity_base_url` reste `None` quand NosDéputés est sauté, plutôt que de
tenter de le reconstruire depuis la législature courante : `LEGISLATURE_BY_BASE_URL`
n'a pas d'entrée pour la législature 17 (courante), et les 3 usages restants
de `identity_base_url` (dossiers pour sénateurs, `profile["source"]` cosmétique,
`fetch_votes_officiels`) retombent déjà proprement sur `base_urls[0]` — c'est
le même chemin que le repli "candidat non trouvé" déjà en usage.

#369 est donc désormais complet, comme #370.

**Tests** : `download_with_watchdog` (`tests/test_download_watchdog.py`,
nouveau — abandon après budget mur, écriture `dest_path` seulement en cas de
succès, propagation d'une erreur réseau normale sans la transformer en
`TimeoutError`), `_build_acteur_mandats_index` (mapping typeOrgane, exclusion
`MISINFO`/`ASSEMBLEE`), `_extract_mandats_officiels` (résolution de label via
`fetch_organe`, acteur inconnu → liste vide), `_build_acteur_identite_index`
(résolution groupe politique + bornes de mandat), `build_profile` (préférence
AN sur les catégories partagées, mandat électif reconstruit depuis l'AN,
`fetch_identity` non appelé quand l'AN résout l'acteur, `fetch_identity`
toujours appelé en repli quand l'AN ne trouve rien). Suite complète : 1129/1129.
