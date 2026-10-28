# Le déploiement du site ne récupère que ce que le build lit (#1370) (2026-10-28)

`2026-10-28`

> **En bref** — les deux déploiements du site du 27/10/2026 ont été arrêtés par leur limite de 10 minutes, et le site n'a pas été mis à jour. La récupération du dépôt (9,5 Go) en prenait 7 à 8 : #1370 a porté la limite à 20 minutes. Le 28/10, le build tracé par strace n'ouvre que `pivot_data/`, `raw_data/candidats.json` et `web/UI_finale/`. Le job `build` de `deploy-pages.yml` ne récupère plus que ces chemins (`sparse-checkout`, `filter: blob:none`) : 265 Mo téléchargés au lieu de 506, 4 min 50 au lieu de 8 min 48 en local, pour un `dist/` identique au fichier près.

## Contexte

| Déploiement | Récupération | Total du job `build` |
| --- | ---: | ---: |
| 26/10/2026, deux réussis | 6 min | ~8 min 30 |
| 27/10/2026, run `40551617669`, deux essais | 7 min, 8 min | > 10 min, arrêtés |
| 28/10/2026, run `40732737642`, limite à 20 min | 8 min 24 (7 min 24 de téléchargement, 1 min d'écriture) | 11 min 45 |

La récupération croît avec les données, et le build n'en lit qu'une partie.

## Ce qui a été mesuré (28/10/2026, commit public `da03cd9d73`)

`strace -f -e trace=openat,open` sur `npm run build`, dans un worktree complet :
2 346 fichiers du dépôt ouverts (2,7 Go), hors `node_modules/` et hors ce que
le build écrit (`dist/`, `public/data/`), tous sous :

| Chemin | Fichiers ouverts |
| --- | ---: |
| `pivot_data/` (17 entrées : profils, groupes, lignées, gouvernements, actes, amendements, ordre du jour, index) | 2 155 |
| `raw_data/candidats.json` | 1 |
| `web/UI_finale/` | 190 |

Rien sous `src/`, `config/`, `docs/`, `tests/`, ni dans le reste de
`raw_data/` (6,5 Go sur les 9,5 Go de l'arbre).

Sur la même connexion (locale, pas celle de GitHub), récupération du même commit à profondeur 1 :

| Récupération | Fichiers | Sur disque | Téléchargé | Durée |
| --- | ---: | ---: | ---: | ---: |
| complète | 6 382 | 9,5 Go | 506 Mo | 8 min 48 (434 s + 94 s d'écriture) |
| partielle, les trois chemins | 2 397 | 2,8 Go | 265 Mo | 4 min 50 |

Le `dist/` construit depuis la récupération partielle est identique à celui
construit depuis le dépôt complet : `diff -rq`, 0 ligne.

## Décision

Le job `build` de `deploy-pages.yml` passe à `actions/checkout` les motifs
`/*`, `!/*/`, `/pivot_data/`, `/raw_data/candidats.json`, `/web/UI_finale/`
(mode non-cône, pour pouvoir nommer un fichier), avec `filter: blob:none`.
Les fichiers à la racine restent récupérés, comme dans l'essai local.

**Un script de build qui lit un nouveau chemin du dépôt l'ajoute au
`sparse-checkout`.** Sinon le build échoue en CI, et seulement là.
`tests/test_deploy_pages_checkout_partiel.py` relève les
`path.join(repoRoot, '…')` des scripts de `web/UI_finale/scripts/` et refuse
un chemin non récupéré ; il refuse aussi toute autre remontée vers la racine.

## Alternatives écartées

- **Relever encore la limite de temps** : elle courrait derrière les données.
- **Récupérer `pivot_data/` en partie seulement** : le build en ouvre 2 155
  fichiers sur 2 186 ; le gain serait nul et la liste fragile.
- **Exclure `raw_data/` du dépôt public** : ce sont les données publiées ; ce
  n'est pas au déploiement du site d'en décider.

## Non vérifié

- La durée en CI : le gain mesuré en local (environ moitié) est une
  indication. Le premier déploiement après publication le dira.
- Le comportement de `filter: blob:none` sur les runners : les fichiers sont
  téléchargés au moment de l'écriture, en lots ; essayé en local avec git
  seulement, pas avec `actions/checkout`.
