<a id="amendements-retry-blocage-legislature"></a>
# Le retry avec backoff des amendements (#225) transforme un échec instantané en blocage de plusieurs minutes par candidat (#239) (2026-08-13)

`2026-08-13`

> **En bref** — un retry avec backoff transforme un échec instantané en blocage de plusieurs minutes par candidat.

**Contexte** : #185 a diagnostiqué que la collecte des amendements officiels
(`fetch_amendements_officiels`/`_build_acteur_amendement_index`) échouait
silencieusement (`return {}` avalé) sur les trois archives AN Open Data
concernées ; #199 a corrigé cela en levant `AmendementsIndexError` au lieu
d'avaler l'échec. #220/#225 ont ensuite ajouté un retry avec backoff
(`AMENDEMENTS_DOWNLOAD_MAX_ATTEMPTS = 3`, `AMENDEMENTS_DOWNLOAD_BACKOFF_SECONDS
= 5`, timeout de lecture de 600s par tentative) pour absorber les
`IncompleteRead` déjà observés sur ces téléchargements volumineux (voir
[[concurrence-ci-roster]] pour un premier facteur aggravant, le double
téléchargement parallèle extract-an/extract-roster-groupes, déjà mitigé).

**Constat (#239)** : depuis le merge de #225 (2026-08-12T13:02Z), 100 % des
runs de `generate-data.yml` échouent avec la signature « runner shutdown
signal » / exit 143 sur `extract-an` — contre un mélange sain de succès/échecs
auparavant. Chronométrage des logs bruts : sur le dernier succès connu
(07/08, avant #199/#225), les 3 tentatives de téléchargement d'archives
échouaient en moins d'1 ms au total (un seul essai, `IncompleteRead` immédiat,
enchaînement direct au candidat suivant). Depuis #225, le même point du
pipeline (transition candidat 1 → candidat 2, où `fetch_amendements_officiels`
s'exécute) présente un écart silencieux de 3m46s à 8m18s selon les runs — un
job dont le budget total tourne alors autour de 5 à 12 minutes avant que le
runner ne reçoive le signal d'arrêt. Cause : un échec définitif de
téléchargement n'est toujours pas persisté sur le cache disque (seul un index
entièrement construit y est écrit), donc **chaque candidat suivant ayant
besoin de la même législature répète le cycle complet de 3 tentatives ×
600s de timeout depuis zéro**, sans mémoire inter-candidats qu'une
législature est cassée pour ce run.

**Législature spécifiquement en cause** : la 16ᵉ législature
(`amendements_div_legis/Amendements.json.zip`). Vérifié en direct le
13/08 06:53 UTC :
```
$ curl -sI https://data.assemblee-nationale.fr/static/openData/repository/16/loi/amendements_div_legis/Amendements.json.zip
content-length: 363306362
x-cacheable: Not cacheable: too big
```
— le CDN devant `data.assemblee-nationale.fr` refuse de mettre ce fichier en
cache (trop volumineux), donc chaque tentative frappe l'origine sans cache.
`IncompleteRead` observé en échec direct dans les logs de production à trois
reprises (07/08, 12/08 08:45, et implicitement sur tous les runs suivants) —
toujours sur cette même législature 16. La 15ᵉ (`amendements_legis/
Amendements_XV.json.zip`, 618 Mo, également hors cache CDN par sa taille)
n'a pas été observée en échec direct dans les runs examinés : la boucle sur
`AN_AMENDEMENTS_PATH` s'interrompt dès que la législature 16 lève une
exception, avant même de l'atteindre — elle reste donc une candidate
plausible au même défaut, non confirmée faute d'avoir été atteinte. La 17ᵉ
(législature active, dataset rafraîchi quotidiennement, généralement < 300 Mo)
est en revanche régulièrement servie depuis le cache CDN
(`x-cacheable: Matched cache`) et se charge rapidement, y compris en cache-hit
sur le disque local (`.cache/amendements_an/17/`) — elle n'est pas mise en
cause ici.

**Décision (implémentée, PR #240)** : (1) mémoriser en mémoire process (pas
sur disque, `_amendements_failed_legislatures`) qu'une législature a
définitivement échoué pour le run courant, pour que seul le premier candidat
qui la rencontre paie le cycle de retry complet — les suivants lèvent
immédiatement sans nouvel appel réseau ; (2) réduire le budget temps par
tentative (`AMENDEMENTS_DOWNLOAD_READ_TIMEOUT_SECONDS`, 600s → 120s) plutôt
que de le laisser à 3×600s dans le pire cas. Ceci recadre potentiellement une
partie du narratif « préemption infra aléatoire, hors de notre contrôle »
retenu par [[verification-billing-actions]] et [[ci-cd]] : au moins cette
occurrence précise avait une cause déterministe et corrigible côté code.
Correctif suffisant pour le symptôme CI mais qui abandonne toujours la
collecte de la législature en échec pour tout le run — étendu par #241 (voir
[[amendements-range-download-legislature-isolation]] ci-dessus), qui
remplace l'abandon par un téléchargement par plages et une isolation par
législature.

