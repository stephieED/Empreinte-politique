<a id="amendements-index-cache-only-split"></a>
# Séparer téléchargement/construction et lecture cache-only dans `_build_acteur_amendement_index` (#250) (2026-08-13)

`2026-08-13`

> **En bref** — téléchargement/construction et lecture cache-only séparés en deux points d'entrée.

**Contexte** : sous-issue 2/6 du plan d'architecture #248, bloquée par
[[amendements-index-budget-ci-cache-granularite]] (#249, granularité de cache
tranchée : clé hebdomadaire existante, `.cache/amendements_an/<legislature>/
index_par_acteur.json`). Préparation nécessaire avant de pouvoir déplacer la
partie réseau dans un job dédié (sous-issue 3) sans changer le comportement
des appelants existants dans cette sous-issue.

**Décision** : `_build_acteur_amendement_index` (`src/candidate_profile.py`)
scindée en deux fonctions :
1. `_read_cached_amendement_index(legislature)` — lecture seule de
   `index_par_acteur.json` s'il existe ; retourne `None` (pas `{}`, pour
   rester distinguable d'un index vide légitime déjà mis en cache) si absent
   ou corrompu. Ne déclenche jamais d'appel réseau.
2. `_download_and_build_amendement_index(legislature)` — reprend telle quelle
   la logique réseau précédemment inline (téléchargement par plages #241,
   cache d'échec mémoire+disque #239/#246, écriture de
   `index_par_acteur.json`), y compris son propre double-check du cache en
   tête (sous le même verrou par législature) pour rester thread-safe.

`_build_acteur_amendement_index` (nom conservé, seul point d'entrée utilisé
par `fetch_amendements_officiels`) devient un simple orchestrateur : essaie
`_read_cached_amendement_index`, puis retombe sur
`_download_and_build_amendement_index` si absent — comportement observable
strictement inchangé (tous les tests existants sur le téléchargement/retry/
cache d'échec/isolation par législature passent sans modification de leurs
assertions). La bascule réelle vers "jamais de téléchargement depuis ces
jobs" reste hors périmètre de cette sous-issue (sous-issue 4).

**Granularité du verrou** : les deux nouvelles fonctions acquièrent chacune
séparément `_get_amendements_lock(legislature)` (verrou non réentrant)
plutôt qu'un unique verrou tenu sur toute la section critique comme avant le
découpage. Un thread peut donc en théorie observer un cache absent via
`_read_cached_amendement_index` puis, pendant l'appel séparé à
`_download_and_build_amendement_index`, retomber sur son propre double-check
de cache (qui retrouvera le fichier si un autre thread l'a entre-temps
écrit) — pas de régression : le pire cas est un aller-retour disque
supplémentaire, jamais un téléchargement dupliqué ni une corruption.

*Alternative rejetée* : faire porter le fallback réseau par
`_read_cached_amendement_index` elle-même (une seule fonction avec un
paramètre `allow_download`) — rejeté car cela va à l'encontre de l'objectif
explicite de l'issue (deux responsabilités testables indépendamment, la
fonction cache-only devant être *structurellement* incapable de déclencher
un appel réseau, pas seulement par défaut).

