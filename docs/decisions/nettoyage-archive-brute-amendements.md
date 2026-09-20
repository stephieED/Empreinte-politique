<a id="nettoyage-archive-brute-amendements"></a>
# Suppression de l'archive brute `amendements.zip` après construction de l'index (#264) (2026-08-17)

`2026-08-17`

> **En bref** — l'archive brute `amendements.zip` est supprimée après construction de l'index, succès comme échec.

**Contexte** : `_download_and_build_amendement_index` téléchargeait
`amendements.zip` (283-618 Mo selon la législature), le parsait, puis ne le
supprimait jamais — ni après succès, ni après échec. Constaté sur le run #32
de `generate-data.yml` : l'artifact `amendements-index-an` pesait 328 Mio
alors que l'index utile ne représente que quelques Mo, la quasi-totalité
étant le zip brut conservé sans raison.

**Décision** : `try`/`finally` autour du téléchargement et du parsing, avec
`zip_path.unlink(missing_ok=True)` en sortie — dans **tous** les cas (succès,
échec réseau, `BadZipFile`). Justification du nettoyage même en échec : le
fichier n'est jamais relu ensuite, ni par la lecture cache-only
(`_read_cached_amendements_acteur` ne lit que l'index), ni pour reprendre un
téléchargement entre deux tentatives (`_download_amendements_zip` réécrit
toujours depuis zéro, en `wb`) — un fichier partiel ou invalide n'a donc pas
plus d'utilité qu'une archive correctement parsée. Suppression best-effort
(`except OSError: pass`), comme l'écriture du cache elle-même : un échec de
nettoyage ne doit jamais masquer l'erreur métier en cours de propagation.

**Portée** : `index_path` n'est jamais touché par ce nettoyage — la
préservation d'un index existant en cas d'échec ([[amendements-index-quality-gate-fraicheur]],
#253) et le cache d'échec inter-jobs (#246) sont inchangés, ce que la suite
de tests existante vérifie toujours.

**Mesure** (cache local, après nettoyage des zips résiduels) : 1,6 Go →
480 Mo, soit **1,06 Go de zips morts** supprimés (99 + 619 + 347 Mo pour les
législatures 14/15/16). Ce gain se cumule avec celui de
[[cache-amendements-forme-dedupliquee]] : le cache amendements complet passe
de 7,9 Go (forme plate + zips) à 480 Mo.

**Hors périmètre** (repris tel quel de l'issue) : les autres archives zip du
dépôt (`dossiers.zip`, `acteurs.zip`, `syseron.xml.zip`...) ne sont pas
traitées ici — celles-ci sont, à l'inverse, réellement relues d'un run à
l'autre comme cache de contenu, la comparaison ne tient donc pas telle
quelle et mériterait sa propre évaluation.

**Tests** : succès → zip absent et index présent ; échec de téléchargement →
pas de fichier partiel résiduel ; `BadZipFile` → zip supprimé malgré
l'échec. Les 3 tests ont été vérifiés comme réellement discriminants (ils
échouent tous les 3 si l'on neutralise le `finally`). Suite complète :
1151/1151.

