# Un scrutin plus récent que notre index n'est pas encore collecté, pas absent (#1248) (2026-11-05)

`2026-11-05`

> **En bref** — complète [la confrontation de l'archive et de l'index](scrutins-de-l-archive-contre-l-index-1248.md), sans la modifier. Un scrutin de l'archive absent de notre index n'est plus signalé s'il est **postérieur au dernier scrutin de l'index** et daté de moins de **3 jours** avant le contrôle (`DELAI_DE_COLLECTE_JOURS`) : il est compté « pas encore collecté ». Au-delà de ce délai, l'absence est signalée, pour qu'une collecte arrêtée ne se cache pas derrière la règle.

## Contexte

Le run 41932814357 a démarré le 05/11/2026 à 00 h 19 (heure de Paris). L'Assemblée a publié son archive des scrutins de la XVIIe à 00 h 26 (`last-modified: Wed, 04 Nov 2026 23:26:08 GMT`). La collecte a lu l'archive précédente, arrêtée au scrutin n° 9578 du 02/11. Le contrôle des effectifs, qui retélécharge l'archive en fin de run, a vu les scrutins suivants et en a signalé **119 absents de notre index** (#1441).

Aucun n'était perdu. Mesuré le 05/11/2026 sur l'archive de la XVIIe : 9 759 scrutins, dont 72 datés du 03/11 et 109 du 04/11, tous postérieurs au dernier de notre index (02/11). Le prochain run les collecte. La propriétaire a accepté la règle le 05/11/2026 (« Oui », sur la question « J'applique la même règle aux scrutins ? »).

## Décision

| Scrutin de l'archive absent de notre index | Ce que c'est |
| --- | --- |
| daté au plus tard du dernier scrutin de l'index | **absent** : signalé |
| plus récent que le dernier scrutin de l'index, daté de moins de 3 jours | **pas encore collecté** : relevé, pas signalé |
| plus récent que le dernier scrutin de l'index, daté de plus de 3 jours | **absent** : signalé |

C'est la règle du contrôle des lois promulguées, qui compte à part les lois « publiées après nos dossiers, pas encore relues » (`relecture_lois_promulguees`), avec en plus un délai : sans lui, une collecte arrêtée laisserait tous les scrutins suivants dans « pas encore collectés », indéfiniment.

La date de l'index est celle de son dernier scrutin, par législature (`dates_publiees`). Le délai se compte depuis le jour du contrôle (UTC).

Rejouée le 05/11/2026 sur l'archive du jour et l'index publié par ce run : 181 scrutins pas encore collectés, 0 absent.

## Alternative écartée

**Relire l'archive que la collecte a lue**, au lieu d'en retélécharger une. Elle vit dans le cache des jobs d'extraction, pas dans `merge-and-pivot` où le contrôle tourne : la transporter coûterait un artifact de plus pour un cas qui ne se produit que quand un run chevauche la publication de l'Assemblée.

## Ce qui n'a pas été vérifié

- L'heure à laquelle l'Assemblée publie son archive chaque nuit : une seule observation (00 h 26 le 05/11/2026).
- Le délai de 3 jours suppose que la collecte lit l'archive au moins une fois par jour. Un run sauté pendant plus de 3 jours ferait signaler des scrutins qui ne sont qu'en retard ; c'est voulu.
