<a id="amendements-index-budget-ci-cache-granularite"></a>
# Spike : budget CI pour un job dédié `extract-amendements-an` et granularité de cache (#249) (2026-08-13)

`2026-08-13`

> **En bref** — spike : budget CI d'un job dédié amendements, et granularité de cache tranchée.

**Contexte** : sous-issue 1/6 du plan d'architecture #248, en préparation
d'un futur job dédié qui construirait les 3 index de législature (17/16/15)
sans condition (indépendamment de la liste de candidats traitée par
`extract-an`/`extract-roster-groupes`), pour pré-chauffer le cache partagé
`.cache/amendements_an/`. Spike sans code : mesurer un budget de timeout
réaliste et trancher la granularité de clé de cache, avant la conception du
job lui-même (sous-issue 3, hors périmètre ici).

**Mesures effectuées** :

1. Tailles exactes (vérifiées en direct, requêtes `Range` sur l'origine,
   13/08 11:31 UTC — affinent les approximations « 283-618 Mo » déjà
   présentes dans `docs/sources/an-opendata.md`) :
   ```
   $ curl -sS --http1.1 -D - -o /dev/null -r 0-4194303 \
     https://data.assemblee-nationale.fr/static/openData/repository/<leg>/loi/<segment>/<fichier>
   ```
   | Législature | Content-Range total | ~MiB | Cache CDN |
   |---|---|---|---|
   | 17 | 296 735 207 o | 283,0 | `Cacheable: force cache` (rafraîchi quotidiennement, cf. `docs/sources/an-opendata.md`) |
   | 16 | 363 306 362 o | 346,5 | `Not cacheable: too big` (confirmé, cohérent avec [[amendements-retry-blocage-legislature]]) |
   | 15 | 648 539 281 o | 618,6 | `Not cacheable: too big` |

   Total des 3 archives : 1 308 580 850 o (≈ 1,22 Gio). Le support des
   requêtes `Range` (206 + `Content-Range`) est reconfirmé sur les 3 URLs,
   cohérent avec la vérification du 13/08 07:29 UTC déjà consignée dans
   [[amendements-range-download-legislature-isolation]].

2. Reproduction, depuis l'environnement d'exécution de ce spike (bac à sable
   Claude Code — **pas** un runner GitHub Actions, chemin réseau différent
   via une passerelle egress restreinte), du comportement de retry par
   segment de `_download_amendements_zip` (script autonome réutilisant les
   mêmes constantes — `AMENDEMENTS_DOWNLOAD_CHUNK_BYTES`,
   `AMENDEMENTS_DOWNLOAD_MAX_ATTEMPTS`, `AMENDEMENTS_DOWNLOAD_BACKOFF_SECONDS`,
   `AMENDEMENTS_DOWNLOAD_READ_TIMEOUT_SECONDS` — et la même logique de
   segment/retry/`Content-Range`). Deux essais indépendants sur la
   législature 17 ont chacun atteint un échec définitif après 3 tentatives
   (`IncompleteRead`), en 20 à 68 s — bien en-deçà du plafond théorique de
   370 s (3 × 120 s de timeout de lecture + 2 × 5 s de backoff), signe que
   les échecs observés ici sont des coupures de connexion rapides plutôt que
   des blocages. Fait notable : les deux essais échouent au même offset
   cumulé exact (33 554 432 o = 32 Mio), ce qui pointe vers un plafond
   propre à la passerelle réseau du bac à sable plutôt qu'un phénomène de
   l'origine AN — **ces essais ne sont donc pas utilisés comme mesure de
   débit de référence** ; ils servent uniquement à revalider le support
   `Range`/`Content-Range` et le comportement de retry par segment sur les
   URLs réelles.
3. Aucun téléchargement complet et propre des 3 archives n'a pu être obtenu
   depuis cet environnement (plafond ci-dessus), et les logs bruts d'un run
   GitHub Actions réel n'ont pas pu être récupérés depuis ce spike (l'hôte de
   stockage des logs, `*.blob.core.windows.net`, n'est pas dans la liste
   d'autorisation réseau de cet environnement). Le budget proposé ci-dessous
   s'appuie donc principalement sur des mesures de production **déjà
   consignées dans ce fichier**, réutilisées ici comme la mesure réelle la
   plus fiable disponible :
   - Run #30 (13/08, `https://github.com/stephieED/Empreinte-politique-src/actions/runs/31685914622`) :
     un blocage réel (pas une coupure rapide) sur une législature amendements
     a consommé **6 min 48 s** avant préemption du runner — cf.
     [[amendements-failed-legislature-marker-inter-jobs]]. Cohérent avec le
     plafond théorique par législature (3 tentatives × 120 s de lecture +
     2 × 5 s de backoff = 370 s ≈ 6 min 10 s, marge de préemption/latence
     réseau incluse).
   - [[amendements-retry-blocage-legislature]] : la législature 17 (servie
     depuis le cache CDN) « se charge rapidement » en conditions saines ; les
     législatures 16/15 (toujours servies depuis l'origine, non
     cacheables) sont les seules concernées par les `IncompleteRead`
     observés en production.

**Décision — budget de timeout proposé** : **30 minutes** pour le futur job
`extract-amendements-an`, calculé comme la somme du pire cas raisonnable
couvrant les deux scénarios demandés (le job doit tenir dans les deux) :
- 2 législatures en conditions saines : 5 min chacune (marge large — aucune
  mesure de débit soutenu fiable n'a pu être obtenue depuis cet
  environnement ; valeur volontairement prudente plutôt qu'optimiste) → 10 min.
- 1 législature en échec définitif après épuisement des tentatives (scénario
  dégradé demandé par l'issue) : 6 min 48 s mesurés en production
  (arrondis à 7 min).
- Overhead fixe (checkout, `setup-python`, `pip install`, parsing en mémoire
  des zips téléchargés avec succès — dizaines à centaines de milliers de
  fichiers JSON par archive, jamais extraits sur disque) : 3 min, cohérent
  avec l'overhead de démarrage observé sur les jobs `extract-*` existants
  (~10 s hors installation) mais avec marge pour le coût CPU du parsing zip.

Total ≈ 20 min ; **30 min** retenu pour une marge ×1,5 et pour rester un
nombre rond cohérent avec les autres jobs du fichier (`generate-data.yml` :
120/90/60/30 min). Valeur **provisoire**, comme déjà pratiqué pour le
timeout de `extract-roster-groupes` dans ce même workflow (60 min
« provisoire ») : à recalibrer sur le premier run réel du job dédié
(sous-issue 3), aucune mesure de débit GitHub Actions authentique n'ayant pu
être obtenue depuis ce spike.

**Décision — granularité de clé de cache** : réutiliser la clé
hebdomadaire existante `public-data-cache-an-<semaine ISO>`, **pas** de clé
quotidienne dédiée aux amendements. Justification :
1. Les jobs AN existants (`extract-an`, `extract-roster-groupes`) partagent
   déjà un seul répertoire `.cache` et une seule clé hebdomadaire pour
   plusieurs jeux de données également documentés comme rafraîchis
   quotidiennement côté AN Open Data (acteurs actifs, dossiers législatifs —
   cf. `docs/sources/an-opendata.md`), sans que cela ait posé de problème identifié
   dans l'historique de ce fichier. Une clé quotidienne spécifique aux
   amendements introduirait une incohérence de granularité au sein du même
   répertoire de cache sans bénéfice démontré.
2. `actions/cache` met en cache le répertoire `.cache` dans son ensemble : on
   ne peut pas donner une granularité différente à un seul sous-répertoire
   sans un `path` de cache séparé — changement de structure hors périmètre
   de ce spike (« pas d'implémentation »).
3. Seule la 17ᵉ législature est concernée par la mise à jour quotidienne ; les
   16ᵉ et 15ᵉ sont des législatures archivées dont les archives ne changeront
   plus jamais (`Last-Modified` observé : 2024-06-28 pour la 16ᵉ, 2022-06-09
   pour la 15ᵉ — vérifié en direct le 13/08). Une clé quotidienne
   multiplierait par ~7 la fréquence de re-téléchargement des 2/3 du volume
   (965 Mio sur 1,22 Gio) sans aucune justification de fraîcheur.
4. Une clé quotidienne multiplie aussi par ~7 le nombre d'entrées de cache
   distinctes sous le préfixe `public-data-cache-an-*` (partagé par tous les
   jeux AN, pas seulement les amendements), ce qui accélère la pression
   d'éviction LRU du cache GitHub Actions (limite globale par dépôt) — allant
   à l'encontre de l'objectif même du job dédié (pré-chauffer un cache
   durable).
5. Le produit (CV politiques factuels) ne porte aucune exigence de fraîcheur
   infra-hebdomadaire documentée dans `AGENTS.md` — une amende récente
   n'ayant pas encore atteint le cache n'est pas un défaut fonctionnel.

**Décision — `runs-on`** : pas de runner différent, `ubuntu-latest` standard
(cohérent avec les 5 autres jobs de `generate-data.yml`). Ces mêmes
téléchargements s'exécutent déjà aujourd'hui, sur ce runner standard, au sein
de `extract-an`/`extract-roster-groupes` (mémoire/bande passante suffisantes
en pratique) ; aucun incident de mémoire ou de CPU n'apparaît dans l'historique
d'incidents amendements de ce fichier (#185/#199/#220/#225/#239/#241/#246,
uniquement des incidents réseau). `_download_amendements_zip` écrit chaque
segment directement sur disque (jamais le zip entier en mémoire) et
`_build_acteur_amendement_index` ne lit qu'un membre du zip à la fois sans
extraction sur disque — empreinte mémoire déjà conçue pour rester modeste,
indépendamment du runner.

**Alternative rejetée** : mesurer le budget en déclenchant un run
`workflow_dispatch` réel et en lisant ses logs. Écartée pour ce spike — la
sous-issue 3 (hors périmètre ici) n'existe pas encore en tant que job
dédié isolable, et les jobs existants ne téléchargent les amendements que
paresseusement (au niveau candidat, avec cache), rendant une mesure isolée
du futur comportement « sans condition » impossible sans implémenter
d'abord le job — précisément ce que ce spike doit précéder.

