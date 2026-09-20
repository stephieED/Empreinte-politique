<a id="deux-versions-archive-amendements-1050"></a>
# Amendements AN : une seule connexion, une seule version (#1050) (2026-09-21)

`2026-09-21`

> **En bref** — l'AN sert deux versions de la même URL ; les segments passent désormais par une seule connexion et redemandent explicitement leur version, et une archive illisible ne sort plus de la boucle par législature.

**Contexte** : le 20/09/2026, le job `extract-amendements-an` du run
`35531938588` tombe à 21h23, quatre minutes après son départ, sur
`zlib.error: Error -3 while decompressing data: invalid distance too far back`,
levée par `_parse_amendements_zip`. Le log du téléchargement ne montre pourtant
aucune anomalie : `300382312/300382312 octets (100.0%)`, neuf segments écrits,
aucune reprise. L'archive fait exactement la taille annoncée et n'est pas
lisible.

**La mesure qui explique tout**, prise le 21/09 vers 00h50 sur
`…/17/loi/amendements_div_legis/Amendements.json.zip` — dix requêtes `HEAD`,
deux réponses différentes :

| | `content-length` | `last-modified` | `ETag` |
| --- | --- | --- | --- |
| 8 fois sur 10 | 300 382 312 | 20/09 20h22 | `"11e77868-65bee362fa5cb"` |
| 2 fois sur 10 | 300 418 979 | 20/09 22h21 | `"11e807a3-65befe27af972"` |

Une seule adresse IP, deux contenus. `_download_amendements_zip` ouvrait une
connexion par segment (chaque appel de `_telecharger_flux` passait par
`requests.get`, donc une session neuve) et ne regardait ni `ETag` ni
`If-Range` — ces deux chaînes n'existaient nulle part dans le module. Neuf
segments tirés au hasard entre deux backends produisent un fichier de la bonne
longueur assemblé à partir de deux archives. Aucune garde ne pouvait le voir :
la seule vérification de fin compare les octets écrits à la taille annoncée, et
les deux coïncident. C'est le seul des quatre modes de défaillance connus de
cette source qui ne se lit pas dans la taille.

**Décision, en deux gardes qui ne se remplacent pas.**

1. **Tous les segments sur une seule connexion** (`requests.Session` portée par
   `_download_amendements_zip`, passée à `_telecharger_flux`). Sept plages
   enchaînées sur une connexion keep-alive rendent la même `ETag`, là où dix
   requêtes séparées en rendent deux : l'affinité de connexion fait la
   différence entre une incohérence rare et une incohérence majoritaire. Sur
   huit segments et un partage mesuré à 80/20, une archive cohérente avait
   environ 17 % de chances de sortir.
2. **Chaque segment redemande sa version** : `If-Range: <ETag>` envoyée par
   `_tenter_segments_range`, et comparaison de l'`ETag` rendue avec celle
   épinglée au premier segment, **avant** que le moindre octet ne soit écrit.
   Une version qui change fait jeter le préfixe et redémarrer depuis zéro —
   à rebours du principe de [[telechargement-an-prefixe-valide-443]], et
   délibérément : un préfixe valide pour une archive que la source ne sert plus
   ne peut pas être complété. Au-delà de
   `AMENDEMENTS_DOWNLOAD_MAX_REDEMARRAGES_VERSION` (3), on échoue en disant que
   la source est **incohérente** (`SourceAmendementsIncoherenteError`) et non
   indisponible : elle délivre parfaitement, elle se contredit.

La garde 1 sans la garde 2 laisserait passer une republication en cours de
transfert ; la garde 2 sans la garde 1 ferait échouer la plupart des
téléchargements au lieu d'en corrompre quelques-uns. Les deux ont été
neutralisées une à une pour le vérifier : sans le contrôle d'`ETag`, le test
reproduit un fichier de la taille attendue mélangeant les deux versions ;
sans la session partagée, huit connexions s'ouvrent et le téléchargement
échoue.

**Second défaut, corrigé dans le même lot** : `zlib.error` n'était attrapée
nulle part. `_download_and_build_amendement_index` ne gardait le parsing que
par `except zipfile.BadZipFile`, et `build_amendements_index_figees.py` de
même — or une archive recollée **s'ouvre** normalement, son répertoire central
étant intact, et ne déraille qu'à la décompression d'un membre. L'erreur
sortait donc de la boucle par législature de `build_amendements_index.py`,
dont le contrat est « une législature perdue, jamais les autres ». Le run, lui,
survivait : le job porte `continue-on-error: true`, et c'est le plafond de
120 minutes de `merge-and-pivot` qui a eu sa peau deux heures plus tard, pour
une cause sans rapport.

**Alternative écartée : vérifier l'archive après assemblage** (`testzip()`, ou
une somme de contrôle sur le fichier complet). Elle détecte le même défaut,
mais après avoir payé 300 Mo de transfert et plusieurs minutes de
décompression, pour apprendre ce que l'`ETag` dit au deuxième segment. Elle ne
dit pas non plus **quoi faire** : sans identité de version, un redémarrage
retombe au hasard sur l'un ou l'autre backend.

**Écarté aussi : demander à l'AN de corriger.** Rien n'empêche de le signaler,
mais la collecte doit tenir avec la source telle qu'elle est — c'est la même
ligne que pour les trois modes de défaillance de #443.
