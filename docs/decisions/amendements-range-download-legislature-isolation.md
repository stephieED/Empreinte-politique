<a id="amendements-range-download-legislature-isolation"></a>
# Téléchargement par plages (Range) + isolation par législature pour les amendements officiels (#241) (2026-08-13)

`2026-08-13`

> **En bref** — téléchargement par plages (Range) et isolation par législature.

**Contexte** : #239 (voir [[amendements-retry-blocage-legislature]] ci-dessous)
a corrigé le blocage CI en mémorisant en mémoire process qu'une législature a
définitivement échoué pour le run courant, et en réduisant le timeout de
lecture par tentative (600s → 120s). Correctif suffisant pour le symptôme CI,
mais qui a pour effet secondaire d'abandonner purement et simplement la
collecte de la législature en échec pour tout le run — `amendements[]` est un
champ central du schéma pivot (§4 AGENTS.md), et les législatures 15/16
couvrent une fenêtre (2012-2022) où un profil type de candidat·e 2027 a une
probabilité non négligeable d'avoir siégé (déjà visible sur Guedj, Le Pen).
Deux défauts distincts identifiés : (1) `fetch_amendements_officiels` n'a pas
de `try/except` par législature dans sa boucle sur `AN_AMENDEMENTS_PATH` — la
première à échouer (généralement la légis 16, chroniquement instable)
interrompt l'appel entier, avant même de tenter la légis 15 ; un échec sur la
16 fait donc perdre une légis 17 pourtant récupérée avec succès. (2) le
téléchargement est un flux HTTP continu unique : une coupure `IncompleteRead`
en cours de flux (déjà observée à des points variables, 9 à 40 Mo lus sur des
flux de 300-620 Mo) jette tout le travail déjà fait et force à tout
redémarrer à zéro. Vérifié en direct (13/08 07:29 UTC) que le CDN devant
`data.assemblee-nationale.fr` supporte fonctionnellement les requêtes par
plage (`Range: bytes=...` → HTTP 206 + `Content-Range`), pas seulement
annoncé via l'en-tête.

**Décision** :
1. `_download_amendements_zip` remplace le flux continu par un découpage en
   segments de `AMENDEMENTS_DOWNLOAD_CHUNK_BYTES` (32 Mo) via l'en-tête
   `Range`, écrits séquentiellement dans le fichier local. Chaque segment est
   retenté indépendamment avec le backoff existant de #225
   (`AMENDEMENTS_DOWNLOAD_MAX_ATTEMPTS`/`BACKOFF_SECONDS`, désormais appliqués
   par segment plutôt qu'au fichier entier) : une coupure mi-flux ne force
   plus qu'un nouvel appel pour le seul segment concerné. Taille finale
   validée contre le total déduit de `Content-Range` (pas de requête `HEAD`
   séparée : le premier `GET` par plage la fournit déjà). Repli sur un
   téléchargement classique en un seul segment si le serveur ignore l'en-tête
   Range (réponse 200 au lieu de 206).
2. `fetch_amendements_officiels` encapsule désormais chaque appel à
   `_build_acteur_amendement_index(legislature)` dans un `try/except
   AmendementsIndexError` par itération de la boucle sur
   `AN_AMENDEMENTS_PATH` : les législatures réussies sont conservées même si
   une autre échoue définitivement, et un warning
   `WARNING_PREFIX_AMENDEMENTS_INDISPONIBLES` précisant la législature
   concernée est ajouté par échec (paramètre `warnings` optionnel, propagé
   depuis `build_profile`) au lieu d'un échec binaire global propagé par
   exception.
3. Le cache d'échec inter-candidats de #239
   (`_amendements_failed_legislatures`) est conservé tel quel comme filet de
   sécurité : il ne s'active désormais qu'après épuisement des tentatives
   *par segment*, pour le cas d'une archive réellement indisponible plutôt
   qu'une simple coupure mi-flux.

**Complété depuis** : ce découpage suppose que le `Range` fonctionne. Quand il
ne rend plus rien — mode de défaillance observé les 18 et 19/08/2026 —, réduire
la taille de segment ne sert à rien et le repli à ajouter est le GET séquentiel.
Voir [[telechargement-an-trois-modes-defaillance]] (#443), qui étend le principe
de cette entrée du segment au flux, et corrige au passage le
`b"".join(resp.iter_content(...))` qui jetait ici les octets déjà reçus quand la
coupure survenait en cours de segment.

**Alternative rejetée** : persister le fichier partiel + les offsets déjà
confirmés sur disque pour permettre une reprise *entre processus* (pas
seulement entre tentatives au sein d'un même appel). Écartée pour ce
correctif — gain marginal (l'essentiel du bénéfice vient déjà de la reprise
intra-tentative par segment) face à la complexité ajoutée (état de reprise à
invalider si l'archive distante change entre deux runs) ; à réévaluer
séparément si des coupures en tout début de flux devenaient fréquentes en
pratique.

