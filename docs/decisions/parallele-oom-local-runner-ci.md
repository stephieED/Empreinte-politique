<a id="parallele-oom-local-runner-ci"></a>
# Parallèle RAM entre l'exécution locale et les runners GitHub Actions hébergés, diagnostic ajouté (2026-08-17)

`2026-08-17`

> **En bref** — la RAM d'une exécution locale et celle d'un runner hébergé se comparent : le diagnostic vaut pour les deux.

**Contexte** : suite à [[oom-lecture-amendements-par-candidat]] (ci-dessous) —
plusieurs OOM réels confirmés en local (`journalctl -k`) sur `extract-an`/
`extract-roster-groupes`, cause identifiée précisément (rechargement complet
en mémoire de l'index amendements d'une législature, jusqu'à 4,35 Gio pour
la 16e, par candidat). Question posée : ce même mécanisme peut-il expliquer
(au moins une partie) des incidents `shutdown signal` observés en CI depuis
le 12/08 (#217 et suivants), jusqu'ici attribués à une « préemption infra
transitoire, indépendante » ?

**Constat — le parallèle est plausible et n'a jamais été testé** :
1. Les runners GitHub Actions hébergés standard (`ubuntu-latest`, 2 vCPU)
   ont **~7 Gio de RAM** — spec publiée et stable de longue date, le même
   ordre de grandeur que la machine locale où l'OOM a été confirmé
   (7,6 Gio). Charger la seule législature 16 (4,35 Gio mesurés) y est donc
   tout aussi risqué qu'en local.
2. Le code concerné (`fetch_amendements_officiels` →
   `_read_cached_amendement_index`) tourne à l'identique en CI, sans
   protection supplémentaire : `extract-an` est shardé par candidat (#344)
   mais un **seul** candidat suffit à charger la législature 16 en entier ;
   `extract-roster-groupes` n'est pas shardé du tout et traite plusieurs
   membres dans le même process — exposition au moins aussi importante
   qu'en local, voire supérieure une fois #376 (passage à pleine échelle)
   réalisé.
3. **Point décisif** : GitHub Actions n'expose jamais les diagnostics
   kernel (`journalctl -k`/`dmesg`) dans les logs de job. Si le runner
   hébergé se fait tuer par OOM, le seul symptôme visible côté logs serait
   `The runner has received a shutdown signal` — **exactement** la
   signature déjà chassée dans ce fichier depuis le 12/08
   ([[verification-billing-actions]], [[resilience-generate-data-shutdown-signal]]).
   La conclusion du 12/08 (« préemption infra, indépendante ») a écarté
   facturation/quota mais n'a jamais mesuré la mémoire réelle, faute
   d'accès — absence de preuve d'OOM dans les logs, pas preuve d'absence
   d'OOM.

**Nuance** : les deux incidents CI diagnostiqués précisément cette session
(runs #45/#47, voir [[resolution-an-prenom-compose-et-gel-runner-etape0]])
se sont produits à l'étape de résolution d'identité (avant la collecte
d'amendements dans `build_profile`), pas pendant `fetch_amendements_officiels`
— ce parallèle n'explique donc pas *ces* deux incidents précis. Mais
l'historique plus ancien du projet (#185/#199/#220/#225/#239/#241/#246,
classés « réseau uniquement » dans [[amendements-index-budget-ci-cache-granularite]])
n'a jamais pu être réévalué à la lumière de cette hypothèse, faute d'avoir
identifié à l'époque que la collecte d'amendements par candidat pouvait à
elle seule approcher la RAM totale d'un runner standard.

**Décision — ajout d'un diagnostic, pas de conclusion prématurée** :
plutôt que de réattribuer rétroactivement les incidents passés sans preuve,
deux steps de diagnostic ajoutés à `extract-an` et `extract-roster-groupes`
(`.github/workflows/generate-data.yml`), à évaluer sur le prochain run réel :
- `free -h` en tout début de job (avant toute charge) — confirme/infirme la
  RAM totale réellement disponible sur ce runner.
- `/usr/bin/time -v` autour de l'appel Python principal de chaque job — trace
  le pic de RSS atteint dans les logs, si le process Python se termine
  (normalement ou tué) sans que le runner entier ne disparaisse avec lui.

**Limite connue et acceptée** : si c'est bien le runner entier qui se fait
tuer par OOM (pas seulement le process Python), rien ne s'exécute après —
même angle mort déjà documenté que `if: always()` (#228). `/usr/bin/time -v`
ne capture donc que le cas où le process Python meurt seul (OOM ciblé sur lui,
ou `MemoryError` Python) sans emporter le runner — mais c'est déjà mieux que
l'absence totale de signal actuelle, et `free -h` seul confirme au moins la
RAM de départ sans dépendre de ce cas.

