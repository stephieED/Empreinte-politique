<a id="index-de-mots-des-amendements-1029"></a>
# Trouver les amendements d'un sujet : l'article visé et un index de mots de l'exposé (#1029) (2026-09-22)

`2026-09-22`

> **En bref** — Un amendement ne portait que son dossier, dont l'intitulé nomme le véhicule (« projet de loi de finances ») et jamais le sujet : « carburant » rendait 0. L'archive AN porte l'article visé et l'exposé sommaire. On publie l'article sur l'index, et un index de mots de l'exposé ENTIER pour toutes les législatures ; l'exposé se lit chez l'AN. 624 amendements de la XVIIe sur le carburant ou la TICPE, trouvables.

## Le besoin

Remonté par l'interface (#1029, rapport « carburant ») : retrouver les
amendements dont l'objet est le carburant, avec leur sort, leur article visé et
le groupe de leur premier signataire — sur **tout** l'index, pas les seuls
candidats. Arbitré le 22/09/2026 : toutes les législatures, avec les réductions
de coût ci-dessous.

## Chemin de l'arbitrage

| Proposé | Poids | Sort |
| --- | ---: | --- |
| Extrait de 280 caractères de l'exposé | ≈ 25 à 140 Mo | écarté : ne permet pas de TROUVER (l'interface) |
| Exposé entier | ≈ 100 Mo pour la XVIIe seule | écarté |
| Index de mots, toutes législatures, première forme | estimé 80 Mo, mesuré 120 Mo | remplacé |
| **Index de mots, formes fusionnées, seuil 3 %, identifiants sans préfixe** | **93,0 Mo, 29,4 Mo compressés** | **retenu** |

L'écart entre 80 et 120 Mo : la liste des identifiants et des articles, que
l'estimation ne comptait pas, pèse un quart du fichier. Les optimisations ont
été mesurées une à une sur les quatre archives, puis arbitrées ensemble :

| Variante | Mots | Renvois | Brut | Compressé | « carbur* / TICPE », XVIIe |
| --- | ---: | ---: | ---: | ---: | ---: |
| Première forme (seuil 5 %) | 203 392 | 31,6 M | 120,3 Mo | 38,9 Mo | 624 |
| **Retenue** | 148 448 | 23,1 M | 93,0 Mo | 29,4 Mo | **624** |
| Mot rattaché s'il revient 2 fois (écartée) | — | ÷ 7 | — | — | 182 |
| Seuil à 2 % (écartée) | — | −27 % | — | — | 624, mais « taxe », « recettes », « investissement » perdus |

## Décision

1. `amendements_contenu.py` lit dans l'archive, pour chaque amendement,
   `division.titre` + `avant_A_Apres` (l'article visé, verbatim) et les mots de
   `exposeSommaire` : HTML retiré, minuscules, sans accents, ≥ 4 lettres. Les
   deux formes d'archive (un fichier par amendement ; le JSON unique de la XIVe).
2. Un fichier par législature, `pivot_data/amendements/<lég>.contenu.json` :
   `ids` triés **sans le préfixe commun** (`prefixe_ids`, `AMANR5L17`),
   `articles` alignés, `mots` → renvois (positions dans `ids`) en écarts base 36.
   Trois temps : les mots de plus de 5 % des amendements sont écartés ; les
   autres sont **ramenés à leur forme de base** quand elle existe dans l'index
   (`forme_indexee` : `carburants` → `carburant`, `fiscaux` → `fiscal` ; jamais
   une forme devinée) ; les formes de plus de **3 %** sont écartées à leur tour.
   La règle est publiée dans le fichier (`fusion_des_formes`, `seuil_frequence`).
   **Pour chercher**, un lecteur normalise le mot comme un exposé, le ramène à
   sa forme indexée contre les clés de `mots`, puis décode ses renvois.
3. `article` est posé sur chaque amendement de `<lég>.json` : les fiches n'ont
   pas à charger l'index de mots pour l'afficher.
4. **Rien n'est rangé sous un thème** : la présence d'un mot dans l'exposé est un
   fait de la source (§2 règle 8).

## Chaîne

- XVIIe : construite avec son index dans `extract-amendements-an`, transportée
  par l'artifact existant, publiée par `merge-and-pivot`. Aucun changement de
  workflow.
- XIVe à XVIe : construites **une par run** tant qu'elles ne sont pas publiées,
  puis relues dans le fichier publié. Jamais réécrites ensuite
  (`ecrire_index_json`, #1075).

## Mesuré (22/09/2026, depuis un poste)

| Lég. | Amendements | Mots indexés | `contenu` | `<lég>.json` avant → après | Temps / mémoire |
| --- | ---: | ---: | ---: | --- | --- |
| XIV | 167 420 | 32 836 | 19,4 Mo | 23,8 → 26,9 Mo | 55 s / 2,6 Go |
| XV | 311 934 | 44 211 | 37,0 Mo | 69,6 → 78,5 Mo | 134 s / 2,7 Go |
| XVI | 163 789 | 36 337 | 19,8 Mo | 37,3 → 42,1 Mo | 71 s / 1,5 Go |
| XVII | 124 929 | 35 064 | 16,8 Mo | 28,8 → 32,7 Mo | 63 s / 1,4 Go |

Article posé sur 685 492 des 685 495 amendements de l'index. Chaîne complète
sur trois profils réels : 33 668 / 33 668 articles posés, +230 Mo de mémoire
dans le constructeur de l'index.

## Ce qui suit

- **`15.json` approche la limite** de 100 Mo par fichier de GitHub : 78,5 Mo.
- **L'interface** : `sync-data.mjs` copie tout `*.json` non-cosignatures de
  `pivot_data/amendements/` dans le site — ces 93 Mo y seraient servis sans
  être lus tant qu'elle ne les exclut ou ne les charge pas à la demande.
- Le groupe du premier signataire à la date de l'amendement se joint sur les
  appartenances publiées, côté interface.
