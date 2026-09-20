<a id="budget-execution-pleine-echelle-467"></a>
# Budget d'exécution à pleine échelle : 630 min annoncées, 55 mesurées (#467) (2026-08-20)

`2026-08-20`

> **En bref** — et un cache disque évite un re-téléchargement, jamais un re-parse.

L'en-tête de `generate-data.yml` portait un budget de **210 min** en
configuration par défaut et **630 min (10 h 30)** en run complet. Ce chiffre
n'a jamais été confronté à un run. Il l'est ici : le run complet
`32288588518` du 19/08/2026 a duré **54,9 min**. Facteur d'écart : **×11,5**.

## 1. Pourquoi 630 était faux : une charge fixe multipliée par le nombre de shards

Le calcul sommait les `timeout-minutes`. Pour la matrice roster il écrivait
`S × 60`, soit 480 min à S=8. Or ces 8 shards se partagent une charge
**fixe** — sharder ne crée pas de travail, il le divise. Le timeout de 60 min
couvrait ~712 membres ; un shard en contient ~94. Écrire `8 × 60` supposait
5 696 membres à traiter, sur un roster de 752.

Le timeout avait été dimensionné pour le job **non shardé** ([[budget-roster-mesure]],
#376) et n'a pas été relu quand #394 l'a découpé. C'est le mode de défaillance
d'une valeur qu'on additionne au lieu de la lire : chaque terme était juste,
la somme ne voulait rien dire.

**Correctif** : l'en-tête distingue désormais le **plafond autorisé** (somme
des timeouts, filet de sécurité, jamais atteint) du **temps mur**, mesuré et
seul à budgéter. Les timeouts eux-mêmes sont laissés en l'état : ils ne coûtent
rien tant qu'ils ne sont pas atteints, et les rabaisser aurait échangé un
chiffre faux contre un risque réel.

## 2. Où passe réellement le temps : ce n'est pas le calcul, c'est le checkout

Décomposition d'un shard roster, relevée dans le log du run `32288588518` :

| poste | shard 0 | shard 7 |
| --- | --- | --- |
| `actions/checkout` (fetch du dépôt) | 117 s | 93 s |
| **extraction (24 membres)** | **63 s** | **67 s** |
| tout le reste (setup-python, pip, cache, artifact, construction du roster, publication, upload, teardown) | 25 s | 34 s |
| **total du job** | **205 s** | **194 s** |

**Les deux tiers d'un shard sont des frais fixes, et la moitié est un
`git fetch`.** À `max-parallel: 1`, sharder ×8 payait donc ~17 min de temps mur
pour zéro travail utile. C'est le poste que ni `--workers` ni aucune
optimisation de code ne touche.

## 3. La répartition du temps par candidat : 0 requête réseau

Mesure demandée par l'issue, faite en rejouant **la population exacte** du
shard 0 (ses 24 membres, mêmes options : `--skip-interventions
--skip-dossiers-legislatifs --workers 1`), cache AN chaud, cache amendements au
format `uid` shardé (matérialisé hors ligne depuis
`raw_data/amendements_an_figes/`, législatures 14/15/16 — la 17e n'est pas figée
et aurait exigé le réseau), en instrumentant `requests` et `time.sleep`.
Temps mur total : **74,1 s**, RSS de pointe **1 266 Mo** (à comparer aux
1 596 Mo relevés en CI sur le même shard — les deux environnements se
correspondent).

| poste | part du temps mur |
| --- | --- |
| relecture d'index locaux (`_extract_mandats_officiels`, dont `fetch_organe` 43,4 s) | 68,9 % (51,0 s) |
| temporisations de courtoisie (`time.sleep`) | 27,7 % (20,5 s) |
| lecture des amendements (`fetch_amendements_officiels`) | 8,6 % (6,4 s) |
| **réseau** | **0,7 % (0,52 s) — 1 requête HTTP pour 24 candidats** |

(Les deux premiers postes se recouvrent partiellement : les sleeps de
`_fetch_ue` s'exécutent en parallèle de la collecte FR.)

**Une requête HTTP pour vingt-quatre candidats**, vers
`data.europarl.europa.eu` (la liste des eurodéputés, téléchargée une fois par
process). **Zéro requête vers NosDéputés, zéro vers data.assemblee-nationale.fr.**
Depuis #369 un député trouvé dans le référentiel historique AN ne déclenche
aucun appel NosDéputés ; depuis #392 ses amendements et depuis #403 ses votes
viennent d'index locaux. La collecte roster n'est plus une opération réseau.

## 4. Ce que ça change, poste par poste

### a. La relecture d'index : le vrai coût, et il était invisible

`fetch_organe` a été appelé **2 255 fois** pour ces 24 membres, et chaque appel
**rouvrait et reparsait** `.cache/acteurs_historique_an/index_organes.json`.
Les quatre index dérivés du zip AMO30 (identité, mandats, organes, positions
dans l'hémicycle) avaient un cache **disque** — qui évitait le
retéléchargement, jamais le reparsing.

C'est la troisième occurrence de la même pathologie au même endroit :
[[budget-roster-mesure]] (#376) l'avait trouvée sur les amendements (93 % du
coût par membre), #403 sur les scrutins. Elle survivait sur le référentiel des
acteurs.

**Correctif** : mémo intra-process, indexé par **chemin** d'index et non par
nom logique — chaque test patche `ACTEURS_HISTORIQUE_CACHE_DIR` vers son propre
`tmp_path`, et un mémo global leur ferait lire l'index du test précédent. C'est
exactement le piège qui avait fait reverter la mémoïsation de #377 ; une
fixture autouse purge en plus le mémo, ceinture et bretelles. L'objet rendu est
partagé, jamais copié (même règle que l'index amendements, AGENTS.md §5).

### b. La temporisation de courtoisie : conservée, mais envers une source réellement appelée

`time.sleep(0.5)  # on reste courtois avec l'API publique entre deux candidats`
datait de l'ère NosDéputés. Mesurée, elle représentait **12,0 s sur 74,1 s de
temps mur** — et une fois la relecture d'index supprimée, la moitié de ce qui
restait : du travail passé à ménager une source qu'on n'interrogeait pas.

**Correctif** : `_get_payload` — chokepoint **exclusif** de
NosDéputés/NosSénateurs, l'Open Data AN ne passant jamais par lui — incrémente
un compteur ; `process_candidat` ne temporise que si le compteur a bougé
pendant le traitement du candidat. Un sénateur, un député absent du référentiel
AN ou une passe avec interventions continuent d'appeler NosDéputés, donc de
temporiser. Même principe pour le `time.sleep(0.3)` du volet européen, qui ne
se paie plus que pour un mandat effectivement trouvé.

*Pourquoi un compteur global et non thread-local* : les appels partent de
sous-pools (`_fetch_fr`/`_fetch_ue`, recherche d'interventions multi-domaines),
donc d'autres threads que celui qui traite le candidat. Le global rend la
mesure **conservatrice** avec `--workers > 1` : on peut temporiser à cause d'un
autre candidat, jamais s'en dispenser à tort. Le sens de l'erreur est celui de
la courtoisie.

*Alternative écartée* : supprimer la temporisation. Elle reste due — la mesure
dit qu'elle était payée au mauvais moment, pas qu'elle est inutile.

### Résultat, sur la population exacte du shard 0

| | temps mur | par membre | RSS max |
| --- | --- | --- | --- |
| avant | 74,1 s | 3,09 s | 1 266 Mo |
| après | **9,8 s** | **0,41 s** | 1 287 Mo |

**−86,8 %**, sans dégradation mémoire (le mémo remplace une allocation
transitoire par membre par une allocation unique ; +21 Mo, soit +1,7 %).
Après correctif, le poste dominant n'est plus la relecture d'index mais la
lecture des amendements (5,7 s des 9,8 s), c'est-à-dire du travail utile.

**Projection en CI** — le même shard y coûtait 63,1 s pour 24 membres, soit
~1,9 s par membre : la mesure locale part d'une base ~1,6× plus lente, donc
transposer le rapport donne **≈ 0,5 s par membre** en retenant une marge pour
la 17e législature, absente du cache local. À pleine échelle (94 membres par
shard) l'extraction passerait de ~3,2 min à **~1 min**. Projection, pas mesure.

## 5. `max-parallel` : la condition de réouverture de #412 était remplie

[[concurrence-shards-extraction-412]] avait écrit sa propre condition :

> *À rouvrir si §3 se confirme et que le run complet devient la norme.*

§3 confirmée par [[cache-cle-amendements-separee]] (#424), run complet devenu la
norme au passage à pleine échelle. Les deux arguments qui restaient à #412 sont
tombés à la mesure — mais **pour la matrice roster seulement** :

- **Cache** : les shards roster ne se passent rien. Le `needs:` de ce job
  garantit que `public-data-cache-an-*` est déjà écrite par `extract-an` quand
  la matrice démarre. Log du run `32288588518` : `Cache hit occurred on the
  primary key public-data-cache-an-2026-W34, not saving cache` sur **tous** les
  shards roster, entrée de **21 Mo** restaurée en **1,1 s**. Chaque shard
  restaure la même entrée immuable. Sérialiser ne réchauffe rien.
- **Prudence réseau** : profil mesuré d'un shard = 2 requêtes NosDéputés
  (construction du roster) + 1 requête `data.europarl.europa.eu` + **0 par
  candidat**. Quatre shards simultanés, c'est 8 requêtes au lieu de 2, une fois
  par run.

**Décision : `max-parallel: 4` sur `extract-roster-groupes`.**

**`extract-an` reste à `max-parallel: 1`**, et l'asymétrie est le cœur de la
décision : ses shards **écrivent** réellement la clé de la semaine (le premier
sauvegarde, les suivants font un exact key hit) — la chaîne de réchauffement y
existe, c'est ce que #424 a réparé. Le job roster démarre derrière lui : sa clé
est déjà chaude. Le même `max-parallel: 1` recouvrait deux situations
différentes ; une seule le justifiait.

*Pourquoi 4 et non 8* : en `fresh_run=true` les steps de cache sont sautés et
chaque shard retélécharge ~40 Mo d'archives AN (acteurs historiques 13,6 Mo +
scrutins XVII 26,3 Mo, `content-length` relevé le 20/08/2026). 4 borne cette
rafale à la moitié pour ~3 min de temps mur en plus à pleine échelle. Ce dépôt
a déjà documenté trois modes de défaillance de l'AN (#443) ; on ne va pas les
provoquer pour trois minutes.

*Ce qui reste une projection* : `max-parallel` ne se teste pas en local. La
mesure porte sur le profil réseau et sur le comportement du cache ; le gain de
temps mur (~23 min → ~6 min à pleine échelle) est déduit des durées de shard
observées, pas observé.

## 6. Ce que le cache AN protège encore : deux répertoires sur quatre

L'issue demandait de chiffrer les quatre répertoires listés dans le `path:` du
job. Relevé le 20/08/2026 :

| répertoire | poids local | téléchargement évité | lu par le job roster ? |
| --- | --- | --- | --- |
| `.cache/scrutins_an` | 89 Mo | **26,3 Mo** (XVII seule — XIV/XV/XVI sont figées et committées) | oui |
| `.cache/acteurs_historique_an` | 35 Mo | **13,6 Mo** | oui |
| `.cache/syceron_an` | 39 Mo | — | **non** (`--skip-interventions`) |
| `.cache/questions_an` | non matérialisé | — | **non** (`--skip-interventions`) |

L'entrée de cache réellement restaurée par un shard roster pèse **21 Mo**
(`Cache Size: ~21 MB`, log du run) : elle ne contient donc, de fait, que ce que
`extract-an` a matérialisé.

Le job cache donc deux répertoires qu'il ne lit jamais. **Laissé en l'état** :
`tests/test_ci_cache_paths.py` exige que `extract-an` et
`extract-roster-groupes` cachent **exactement le même ensemble**, précisément
pour qu'aucun des deux ne re-télécharge ce que l'autre a persisté (#424).
Resserrer le `path:` du seul job roster casserait cette invariance pour
économiser une restauration de cache de 1,1 s. Le vrai chiffre est là :
**39,9 Mo** par shard en cas de cache froid, pas les 163 Mo que suggère la
taille sur disque.

## 7. Le troisième levier : découpage proportionnel, et pourquoi `TOTAL=1`

`prepare-roster-matrix` force 1 seul shard dès que `roster_extraction_limit`
est non nulle. C'était le seul endroit du fichier où une décision n'était pas
argumentée. Elle l'est maintenant, et la raison est **sémantique, pas de coût** :
dans `generate_all_profiles.main()`, `--shard` s'applique **avant** `--limit`,
donc la limite vaut par shard. `limite=100` sur 8 shards ne traiterait pas 100
candidats mais jusqu'à 800 — on demanderait un lot, on en obtiendrait huit.

*Alternative examinée et écartée* — découper quand même, en 8 tranches de
`limite/8`, pour paralléliser le rollout progressif :

- **Ce n'est pas un levier distinct de `max-parallel`** : il signifie
  exactement la même chose côté réseau, huit jobs roster simultanés frappant
  les mêmes sources. C'est une variante, pas une alternative.
- **Le lot cesse d'être exact.** La sélection progressive de #224 prend d'abord
  les non couverts, qui ne sont pas répartis uniformément (#445 : 24, 24, 28,
  27 couverts selon le shard). On demanderait 100 et on obtiendrait 70 ou 80,
  sans savoir lesquels à l'avance.
- **Le gain a fondu.** Un shard coûte ~130 s de frais fixes pour une extraction
  tombée à ~0,3 s par membre : découper un lot de 100 ferait payer huit fois
  ces frais fixes pour économiser ~1 min de temps mur.

Le nombre effectivement traité, lui, est **déjà** rapporté par
`_select_candidats_couverture` — `Sélection progressive + rafraîchissement : X/Y
candidat(s) retenu(s) (N non couvert(s), M périmé(s))` — par shard, dans le log
du job. Rien à ajouter de ce côté.

## 8. `--workers` : maintenu à 1, mais plus pour la raison écrite

Le second verrou de l'issue. Sa justification était la courtoisie ; celle-ci est
désormais portée par la temporisation conditionnelle, pas par la sérialisation.
Ce qui maintient 1 :

- **Le parallélisme inter-candidats ne fait pas gagner de temps ici : il en
  coûte.** Mesuré sur les 24 membres, cache amendements réel :

  | | `--workers 1` | `--workers 4` |
  | --- | --- | --- |
  | avant #467 | 74,1 s | **94,6 s** (+28 %) |
  | après #467 | 9,8 s | **13,8 s** (+41 %) |

  Dans les deux états. La charge est du parsing JSON sous GIL, sérialisé de
  surcroît par les verrous par législature (`_get_amendements_lock`,
  `_ACTEURS_*_LOCK`) : quatre threads ne font que se disputer le même
  interpréteur. Le mode dont l'input parle — « candidats traités
  simultanément » — décrit une charge réseau qui n'existe plus.
- **Le RSS de pointe monte** (1 281 → 1 374 Mo en local ; 1 596 Mo mesuré en CI
  à `--workers 1`), sur un job déjà exposé à l'OOM (#377). Payer de la mémoire
  pour perdre du temps serait un mauvais échange deux fois.
- **L'input est partagé** avec `extract-senat` et `merge-and-pivot`, et le
  Sénat, lui, est réellement borné par NosDéputés. L'augmenter changerait deux
  profils de charge à la fois — exactement ce que #412 refusait de faire.

## Limites assumées de cette mesure

- **Faite en local**, comme [[budget-roster-mesure]] et pour la même raison.
  Elle est ancrée sur un point CI réel — la population exacte du shard 0 et sa
  durée mesurée en CI (63,1 s) — mais le poste dominant est CPU/disque, pas
  réseau : la transposition porte sur un rapport, pas sur une valeur absolue.
- **Cache chaud.** Le cas froid (`fresh_run=true`) n'a pas été mesuré, seulement
  chiffré en volume (39,9 Mo par shard, `content-length` relevé à la source).
- **17e législature absente du cache amendements local.** Elle n'est pas figée,
  la matérialiser aurait exigé de retélécharger 676 Mo à l'AN. Les mesures
  couvrent donc 3 législatures sur 4 côté amendements — c'est ce qui justifie
  la marge prise dans la projection à 0,5 s par membre. Premier constat de
  cette limite : le cache local était au format plat hérité de #377, donc
  `fetch_amendements_officiels` y répondait « index absent » et la phase
  n'apparaissait pas du tout dans une première série de mesures. Une phase qui
  échoue proprement se lit comme une phase rapide.
- **`max-parallel` n'est pas testable en local.** Le gain de temps mur est
  déduit des durées de shard observées, pas observé.
- **`merge-and-pivot` à 752 profils reste l'inconnue.** 7,5 min mesurées à 209
  profils ; rien ne dit comment ce job se comporte à 752, et c'est désormais le
  poste le moins connu du budget. Le premier run complet réel tranchera.

---

