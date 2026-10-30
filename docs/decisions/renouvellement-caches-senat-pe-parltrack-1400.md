# Les caches Sénat, Parlement européen et ParlTrack se renouvellent à chaque période (#1400) (2026-10-30)

`2026-10-30`

> **En bref** — les trois caches de la fiche candidat lisent désormais `cache-hit`, comme celui des amendements depuis #749 : quand la clé exacte de la période (le jour pour le Sénat, la semaine pour les deux autres) n'existait pas, le job retélécharge sa source avant de collecter. Avant, le repli par préfixe restaurait l'entrée précédente, le code sautait le téléchargement dès que le fichier existait, et les sept familles de ces sources sont restées au 20/09/2026 pendant six semaines. Le préfixe de repli reste. Les deux clés hebdomadaires passent en `-v2-` pour que le correctif prenne dès son premier run.

## Contexte mesuré

Le premier fichier de fraîcheur complet (run public `40970208263`, 29/10 23 h 01 → 30/10 1 h 34, voir `premier-fichier-de-fraicheur-1389`) date du **20/09/2026** les sept familles des trois sources, et les quatorze autres du 26/10 au 30/10. Le journal du même run dit pourquoi :

| Job | Ce qu'il écrit | Ce que fait le code |
| --- | --- | --- |
| `extract-parltrack` | « Dump ep_votes.json.zst en cache (âge : 39 j) », de même pour les quatre autres dumps | `ensure_dump` rend le fichier dès qu'il existe |
| `extract-senat` | « Export déjà en cache, téléchargement sauté. » | le step saute si `export_sens.sql` n'est pas vide |
| `extract-ue-officiel` | rien | `fetch_all_meps_by_country` rend `meps_FR.json` dès qu'il existe ; `organisations.json` ne fait que s'allonger |

C'est le défaut de #749 (amendements) et de #555 (Assemblée), sur trois caches qu'aucun des deux n'avait couverts : la clé change, le repli par préfixe sert l'entrée précédente, et le job la resauvegarde sous la clé neuve sans l'avoir renouvelée. `docs/regles/ci.md` le disait déjà (#1127) : la clé périme le **nom** d'une entrée, jamais son **contenu**.

## Décision

Le mécanisme de #749, sur les trois jobs. Le step de cache reçoit un `id` ; `outputs.cache-hit` vaut `'true'` seulement quand la clé exacte a été restaurée, jamais sur un repli.

| Job | `id` | Ce qui est renouvelé quand `cache-hit` n'est pas `'true'` |
| --- | --- | --- |
| `extract-senat` | `cache_senat` | l'export est retéléchargé ; il n'est réutilisé que si la clé du jour a été restaurée |
| `extract-ue-officiel` | `cache_ue` | `meps_FR.json` et `organisations.json` sont retirés avant l'extraction, qui les relit |
| `extract-parltrack` | `cache_parltrack` | les cinq dumps sont retéléchargés (`force_download`) |

Les fichiers retirés du côté européen sont exactement les témoins de `pe.mandats` dans `src/fraicheur_sources.py` (`TEMOINS_PE_MANDATS`) : le relevé prend le plus ancien des deux, et un témoin oublié garderait la famille à sa vieille date. Le test compare les deux listes.

**Les clés hebdomadaires passent en `public-data-cache-ue-v2-<semaine>` et `public-data-cache-parltrack-v2-<semaine>`.** La clé de la semaine du correctif (W44) existait déjà, écrite par l'ancien code avec le contenu du 20/09 : elle aurait été restaurée exactement, et rien ne se serait renouvelé avant le lundi suivant. Le suffixe la fait manquer une fois. Le préfixe de repli, inchangé, reconnaît les deux formes. La clé du Sénat, au jour, n'en a pas besoin.

**Un téléchargement raté fait échouer le job**, comme avant. Pour ParlTrack, l'ancien dump reste sur le disque (`download_with_watchdog` écrit dans un `.part`), mais le job échoue : la fusion retombe sur les données publiées, et le fichier de fraîcheur dit « en échec » au lieu de redater un vieux fichier. L'entrée n'est pas sauvegardée, donc le run suivant réessaie.

## Alternatives écartées

- **Retirer le préfixe de repli.** Il garde le cache chaud quand la source est indisponible au premier run d'une période. Le retirer règlerait la fraîcheur en supprimant ce repli ; `cache-hit` donne la même fraîcheur sans rien retirer.
- **Une péremption par l'âge des fichiers** (`mtime`). Elle aurait pris effet dès le premier run sans changer de clé, mais elle se combine mal avec `actions/cache`, qui ne sauvegarde jamais sur une clé exacte : un fichier qui dépasse son âge en milieu de période serait retéléchargé à chaque run jusqu'à la suivante, sans jamais être resauvegardé.
- **Le module de #555** (`cache_an_fraicheur.py`, qui lit `cache-matched-key`). Il existe pour ne périmer qu'une partie du cache (les législatures vivantes). Ici tout le contenu vieillit : `cache-hit` suffit.

## Non vérifié

- La fréquence réelle de publication de chaque source : le Sénat régénère son export chaque nuit (#885) ; celle des dumps ParlTrack et de la liste des députés européens n'a pas été mesurée. La semaine reste le pas des deux clés hebdomadaires.
- Le coût en temps du premier run : les cinq dumps ParlTrack pesaient 232 Mio (#683), sous le budget de 900 s par dump et les 30 minutes du job, mais le temps de téléchargement depuis le runner n'a pas été remesuré.
- Le correctif atteint le corpus au premier run qui l'exécute, et le fichier de fraîcheur le dira : les sept familles doivent passer à la date de ce run.
