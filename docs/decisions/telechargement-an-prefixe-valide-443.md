# Téléchargement AN : trois modes de défaillance, un seul principe — ne jamais jeter un préfixe valide (#443) (2026-08-19)

`2026-08-19`

> **En bref** — trois modes de défaillance du téléchargement AN, un seul principe : ne jamais jeter un préfixe valide.

**Contexte** : `data.assemblee-nationale.fr` ne tombe pas en panne, il **change
de mode de défaillance**, et assez vite pour qu'une mesure de quelques minutes
induise en erreur. Relevé le 18/08/2026 sur `Amendements_XV.json.zip` (648 Mo),
puis reconfirmé le 19/08 avant d'écrire une ligne de code :

| État | `Range` | GET séquentiel | Repli utile |
| --- | --- | --- | --- |
| 1 | fonctionne | — | reprise par segments — l'existant ([[amendements-range-download-legislature-isolation]], #241) |
| 2 | 0 octet à toutes les tailles (8 Kio à 32 Mio) | délivre | GET séquentiel, conservé comme préfixe |
| 3 | 0 octet | coupe à 13-25 Mo | **aucun** — seule l'attente fonctionne |

Le serveur annonce `Accept-Ranges: bytes` et un `Content-Length` correct dans
les trois états : **aucune sonde `HEAD` ne les distingue**, seul le transfert
lui-même le peut. C'est pourquoi l'arbitrage se fait en cours de
téléchargement et non par configuration.

Le téléchargeur ne connaissait que l'état 1. Son unique repli — réduire
`AMENDEMENTS_DOWNLOAD_CHUNK_BYTES` — porte sur une dimension qui n'est pas en
cause dans les états 2 et 3 : des segments de 8 Kio y échouent autant que des
segments de 32 Mo. Le repli existant était donc inopérant précisément quand il
aurait fallu qu'il serve. Trois chantiers ont buté sur ce symptôme en deux
jours ([[cache-cle-amendements-separee]] #424,
[[gouvernement-textes-non-ecrasement]] #427, et la reconstruction des index
figés de #440, arrêtée plusieurs heures), à chaque fois traité comme de
l'instabilité subie.

**Mesures du 19/08/2026** (rappelées ici parce qu'elles corrigent deux
affirmations de l'issue) :

- La panne du `Range` dépend du **décalage**, pas du fichier : une plage à
  l'octet 0 ou à 4 Mio est servie normalement (206 + 8192 octets) pendant que
  la même plage à 64 Mio, 100 Mio et 300 Mio ne rend rien. Sonder le support du
  `Range` en tête de fichier conclurait donc à tort qu'il fonctionne — l'arbitrage
  doit porter sur le décalage courant, ce que fait naturellement la boucle.
- Ce n'est pas un artefact HTTP/2 : `curl --http1.1` échoue identiquement
  (`transfer closed with 8192 bytes remaining to read`). Inutile de chercher un
  remède du côté du protocole.
- Le GET séquentiel a rendu 58,7 Mo puis 17,2 Mo sur deux essais successifs :
  le point de coupure est aléatoire, et **inférieur au préfixe déjà obtenu une
  fois sur deux**. D'où l'obligation de comparer les longueurs avant d'adopter.

**Le principe** : *ne jamais jeter un préfixe valide, d'où qu'il vienne.* Un
`Range` partiel, un GET séquentiel interrompu et une reprise réussie produisent
tous des préfixes du **même** fichier : le plus long doit gagner, quelle que
soit sa provenance. C'est le principe de #241 appliqué un cran plus bas, au
flux plutôt qu'au segment.

**Décision** :

1. **Écriture au fil de l'eau** (`_telecharger_flux`). Le
   `b"".join(resp.iter_content(...))` matérialisait tout le segment avant de
   l'écrire : une coupure en cours propageait l'exception depuis `iter_content`
   et relançait le segment **depuis son offset de départ**, perdant tout ce qui
   avait été reçu. Sous un mode de défaillance où la coupure tombe à un point
   aléatoire, cela annulait l'essentiel de ce qui arrivait.
2. **Lecture sur `resp.raw`, pas `iter_content`.** Corollaire mesuré, et non
   prévu : écrire au fil de l'eau ne suffit pas, car `iter_content` jette
   lui-même le tampon partiel. Sur un corps tronqué à 40 000 octets pour
   100 000 annoncés, `iter_content(chunk_size=N)` rend **0 octet** dès
   N ≥ 64 Kio et 39 936 octets pour N = 1 Kio, là où `raw.read()` rend les
   40 000. En cause le tampon de décodage d'urllib3 : `read(amt,
   decode_content=True)` accumule jusqu'à `amt` octets avant de rendre, et
   `_raw_read` lève `IncompleteRead` sur la lecture *suivante* — celle qui rend
   zéro octet — ce qui jette le tampon. Le corps devant rester non décodé, la
   requête pose `Accept-Encoding: identity` et un `Content-Encoding` autre est
   refusé bruyamment plutôt qu'écrit tel quel.
3. **Repli GET séquentiel** (`_tenter_get_sequentiel`), déclenché quand les
   plages ne rendent **aucun** octet après épuisement des tentatives. Le flux
   est écrit dans un fichier voisin `.seq` et **adopté seulement s'il est plus
   long** que le préfixe déjà détenu. Adopter le fichier entier plutôt que d'en
   recoller la fin sur l'existant évite par construction tout raccord entre deux
   versions distinctes de l'archive distante.
4. **Arbitrage à l'exécution**, jamais par configuration : chaque cycle retente
   les plages au décalage courant, puis le séquentiel. Un `Range` redevenu
   opérant est donc repris immédiatement, en repartant du préfixe déjà obtenu.
5. **État 3 traité explicitement.** Quand un cycle complet ne rend pas un seul
   octet, on **attend** (`AMENDEMENTS_SOURCE_STALL_WAIT_SECONDS`, 30 s) au lieu
   de marteler, jusqu'à `AMENDEMENTS_SOURCE_STALL_MAX_CYCLES` (3), puis on lève
   `SourceAmendementsIndisponibleError` — dont le message dit que **la source
   est indisponible**, pas que le téléchargement a échoué. La distinction n'est
   pas cosmétique : elle change ce que fait la personne qui lit le log — dans un
   cas elle relance, dans l'autre elle attend ou passe par un index figé. Les
   deux bornes sont basses par défaut (budget CI) et exposées en CLI par
   `build_amendements_index_figees.py` (`--stall-cycles`,
   `--stall-wait-seconds`), car hors CI l'attente longue est le seul remède qui
   fonctionne.
6. **Une 4xx n'est pas une source indisponible.** Un 404/403 ne rend aucun
   octet lui non plus ; sans garde-fou il aurait été rapporté comme « source
   indisponible », envoyant attendre un rétablissement qui n'arriverait jamais.
   `_est_erreur_http_definitive` le fait remonter tel quel (4xx hors 408/429).
7. **Pas de troncature silencieuse.** Une réponse 200 n'est tenue pour le
   fichier entier que si le flux s'est achevé **sans erreur** ; sinon elle n'est
   qu'un préfixe de plus. L'ancien code posait `total_size = len(chunk)` sur
   toute réponse 200, ce qui aurait déclaré complète une archive tronquée. Le
   contrôle de taille finale est conservé.

**Alternative rejetée** : choisir le mode par configuration (une option
`--sequential`, ou un réglage déduit d'une sonde initiale). Le mode de
défaillance change en quelques minutes — j'ai moi-même conclu à tort que « la
taille de segment était la cause », sur la foi de six mesures prises dans une
fenêtre où le `Range` fonctionnait encore. Un réglage posé d'après un
diagnostic ponctuel serait faux la plupart du temps, et faux silencieusement.

**Vérification** : 11 tests contre un **vrai serveur HTTP local** simulant les
trois états (`tests/test_amendements_download_modes.py`) — pas des doubles de
`requests`, qui n'auraient prouvé que le chemin nominal : ce qui est en cause
est le comportement du transfert lui-même (corps tronqué par rapport au
`Content-Length` annoncé, connexion fermée en cours de flux), que seul un vrai
serveur reproduit. Les six protections ont été neutralisées une à une, chacune
fait échouer son test — y compris la restauration littérale du
`b"".join(iter_content(...))` d'origine. 1409 tests verts.

Vérifié aussi contre la source réelle : `Amendements_XIV.json.zip` téléchargée
intégralement (103 716 698 octets, archive zip valide) par le chemin nominal.

**Ce que ceci ne résout pas** — et il vaut mieux le dire que le laisser croire :

- Dans l'état 3, **aucun repli réseau ne fonctionne.** Le correctif ne peut
  qu'attendre plus intelligemment et échouer en le disant. Pire, le repli
  séquentiel redémarre à l'octet 0 (le `Range` étant mort, aucune reprise n'est
  possible) : son utilité décroît à mesure que le préfixe grandit, et sur une
  archive de 648 Mo dont les transferts séquentiels cassent vers 20-60 Mo, elle
  est nulle en pratique. Pour les artefacts **immuables** — index figés des
  législatures closes — la vraie réponse reste de ne pas avoir à les
  retélécharger ([[amendements-legislatures-figees]]).
- Le chemin CI supprime toujours l'archive partielle en cas d'échec (`try/finally`
  de #264), donc n'en tire aucun bénéfice de reprise d'un run à l'autre. Ce
  choix reposait sur une prémisse devenue fausse (« `_download_amendements_zip`
  réécrit toujours depuis zéro », vrai avant la reprise entre invocations de
  #241). Le corriger échange du volume de cache CI contre de la reprise : arbitrage
  à mesurer, noté dans `ROADMAP.md` plutôt que tranché ici en passant.

---
