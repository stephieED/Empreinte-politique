<a id="telechargement-repris-apres-coupure-1202"></a>
# Un téléchargement coupé se reprend là où il s'est arrêté : l'archive Syceron de la XVe ne reste plus hors des correctifs (#1202) (2026-10-04)

`2026-10-04`

> **En bref** — le run du 04/10/2026 lancé pour porter #1197 a corrigé la XVIe et la XVIIe et **laissé la XVe intacte** : le téléchargement de son archive (149 Mo) a été rompu dans les dix jobs lus, après 2 à 40 Mo. `download_with_watchdog` reprend désormais un transfert coupé par `Range`, sur demande de l'appelant ; Syceron le demande. Éprouvé sur le serveur de l'Assemblée : deux coupures, archive identique à l'octet près.

## 1. Le constat

Run public `37200491118`, `collect_interventions=true`, `SYCERON_VERSION_INDEX`
passé à `1197` : l'index devait être reconstruit pour les trois législatures.

| Prises de parole Syceron avec intitulé, profils publiés | XVe | XVIe | XVIIe |
| --- | --- | --- | --- |
| Avant le run | 534 297 | 285 946 | 256 668 |
| Après le run | 534 297 | 304 440 | 289 046 |

Journal des dix jobs lus (huit shards du roster, deux candidats déclarés), tous
identiques : « Débats Syceron législature 15 indisponibles : Connection broken:
IncompleteRead(… bytes read, … more expected) », entre 2,3 et 40,7 Mo lus sur
148 954 869 octets. Au run manuel du 03/10 (`37133139751`), la même archive
avait dépassé le budget mur de 120 s.

## 2. Pourquoi cela se répète

Le cache d'Actions garde l'**index**, pas l'archive. Chaque changement de
`SYCERON_VERSION_INDEX` — trois en trois jours : #1169, #1197, #1200 — oblige
donc chaque job à retélécharger l'archive, et un transfert rompu était perdu en
entier. La règle de #1169 (« tout changement de ce que l'index contient
incrémente sa version ») est juste ; elle rendait seulement visible un
téléchargement qui ne tenait pas.

## 3. La décision

`download_with_watchdog` reçoit `reprises`, **à `0` par défaut** — les cinq
autres appelants ne changent pas :

- une rupture en cours de transfert (`ChunkedEncodingError`, `ConnectionError`,
  `ReadTimeout`) relance la requête avec `Range: bytes=<déjà écrit>-` et ajoute
  au fichier temporaire ;
- si le serveur ignore `Range` (réponse `200`) ou reprend ailleurs que demandé,
  le fichier repart de zéro : ajouter un fichier entier à un début de fichier
  publierait une archive corrompue ;
- la taille finale est comparée à celle que le serveur a annoncée : un fichier
  incomplet n'atteint jamais `dest_path` ;
- une erreur HTTP n'est pas une coupure, elle n'est pas reprise ;
- **le budget mur couvre tous les essais** : reprendre ne rallonge pas un job.

`syceron_debates` demande `SYCERON_REPRISES_TELECHARGEMENT = 8`.

## 4. Ce qui est éprouvé, et ce qui ne l'est pas

- **Éprouvé sur le vrai serveur**, depuis un poste personnel, le 04/10/2026 :
  archive de la XVe, deux ruptures provoquées, requêtes `bytes=2097152-` puis
  `bytes=23068672-`, 148 954 869 octets en 43 s, **empreinte SHA-256 identique**
  à celle de l'archive déjà en cache. Le serveur annonce `accept-ranges: bytes`
  et `last-modified: 09 Jun 2022`.
- **Non éprouvé** : en CI. La cause des ruptures côté serveur n'est pas connue,
  et rien ne dit qu'une reprise ne sera pas rompue à son tour. Le budget mur de
  120 s n'est pas relevé : s'il est dépassé au prochain run, c'est une seconde
  mesure, à traiter à part.

## 5. Alternatives rejetées

**Mettre l'archive de la XVe dans le cache d'Actions.** Elle est figée depuis
2022 et s'y prêterait ; mais 149 Mo par législature s'ajoutent à un cache déjà
compté (#1127), et cela ne répare pas le téléchargement, seulement sa fréquence.
À rouvrir si la reprise ne suffit pas.

**Relever le budget mur.** Les dix échecs du 04/10 sont des ruptures, pas des
dépassements : un budget plus long n'en aurait sauvé aucun.
