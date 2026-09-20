<a id="amendements-legislatures-figees"></a>
# Index amendements des législatures 15/16 : construction manuelle hors CI, committée (2026-08-13)

`2026-08-13`

> **En bref** — construits hors CI, committés, jamais re-téléchargés.

**Contexte** : le job CI dédié `extract-amendements-an` ([[amendements-index-job-dedie-ci]],
#251) a échoué sur son tout premier run réel pour les législatures 15 et 16 —
`IncompleteRead` répété dès le premier segment de `Amendements_XV.json.zip`
(648 Mo) et `Amendements.json.zip`/16 (363 Mo), les 3 tentatives
(`AMENDEMENTS_DOWNLOAD_MAX_ATTEMPTS`) épuisées à chaque fois (voir logs du run
GitHub Actions #31705965678, job `extract-amendements-an`). La quality gate
section 3d ([[amendements-index-quality-gate-fraicheur]], #254) rapportait
alors, à raison, les deux comme « jamais construit ». Reproduit hors CI :
un téléchargement manuel (`curl --http1.1`, retries, resume `-C -`, budget
1h+) rencontre le même type de coupure (`HTTP/2 stream ... PROTOCOL_ERROR`
puis, en HTTP/1.1, `transfer closed with N bytes remaining to read`) —
confirme que la cause est le CDN d'`data.assemblee-nationale.fr` lui-même sur
ces deux grosses archives, pas une contrainte spécifique aux runners GitHub
Actions.

Ces deux législatures sont closes : leurs dossiers législatifs ne seront plus
jamais amendés, et l'en-tête `Last-Modified` des archives le confirme
(`2022-06-09` pour la 15e, `2024-06-28` pour la 16e — probablement une
dernière correction éditoriale AN, pas une évolution de fond). Retenter à
chaque run CI un téléchargement de 350-650 Mo pour une donnée figée n'a donc
aucune valeur — contrairement à la législature 17 (en cours), dont l'archive
évolue et doit rester reconstruite en continu par le job CI existant.

**Décision** :
1. `AN_AMENDEMENTS_LEGISLATURES_FIGEES = frozenset({"15", "16"})`
   (`candidate_profile.py`), et un nouveau script one-shot
   `src/build_amendements_index_figees.py --legislature {15,16} (--zip <archive
   locale> | --download)` qui réutilise le parsing existant
   (`_parse_amendements_zip`, extrait de `_download_and_build_amendement_index`)
   sur une archive amendements AN, soit déjà téléchargée manuellement
   (patience/retries hors budget CI, cas d'origine documenté ci-dessous), soit
   téléchargée par le script lui-même via `--download` (réutilise
   `_download_amendements_zip` — mêmes segments HTTP Range + retries que le
   job CI réseau — dans `.cache/amendements_an/<legislature>/`, gitignoré,
   jamais committé).
2. `_download_and_build_amendement_index` court-circuite tout accès réseau
   pour ces deux législatures : `_load_frozen_amendement_index` lit le
   fallback committé et le matérialise dans le cache disque standard
   (`.cache/amendements_an/<legislature>/`), au même format qu'une
   construction réseau réussie — transparent pour `fetch_amendements_officiels`
   et pour `check_quality_gate.py`.
3. Section 3d du quality gate : nouvel état **figé** (distinct de
   jamais-construit/périmé/frais), déclenché quand la législature est dans
   `_AMENDEMENTS_LEGISLATURES_FIGEES` *et* que `fraicheur.json` porte
   `figee: true`. Aucune notion de péremption ne s'applique — pas de
   warning, jamais, même après `--amendements-staleness-days`.

**Révision (2026-08-13, après inspection de la release `amendements-figes-v1`)** :
le point 1 ci-dessus committait initialement `index_par_acteur.json` tel que
produit par `_parse_amendements_zip` — un enregistrement complet par
signataire (auteur + chaque cosignataire), chacun portant sa propre copie
intégrale de l'amendement (dont `co_signataires`). Un premier build réel de la
législature 16 a mesuré ce fichier à **3,86 Go décompressés** (63,7 Mo une
fois gzippé) — l'inverse de l'affirmation « plusieurs ordres de grandeur plus
petit » ci-dessous, et surtout largement au-delà de la limite GitHub de
100 Mo par blob une fois décompressé, rendant un `git add` direct
structurellement impossible (pas seulement indésirable). La législature 15
(archive source plus grosse) aurait vraisemblablement heurté la même limite,
y compris compressée (marge insuffisante par simple extrapolation du ratio
observé sur la 16).

> **Révisé le 18/08/2026** — la clé de déduplication décrite ci-dessous
> (`numero`) était fausse : elle écrasait 74,9 % des amendements et en
> attribuait 40,5 % au mauvais texte. Le store est désormais keyé par l'`uid`
> AN et les index figés ont été reconstruits ; voir
> [[amendements-cle-uid]]. Le reste de cette entrée (pourquoi dédupliquer,
> pourquoi gzip, pourquoi hors CI) reste valable.

Plutôt que de committer le `.json.gz` compressé tel quel (alternative
initialement envisagée, pariant sur le ratio de compression ~60:1 pour rester
sous 100 Mo — non garanti pour la 15e), le format committé a été revu pour
dédupliquer la donnée à la source : `_aggregate_amendements_index` (nouveau,
`candidate_profile.py`) sépare l'index brut en `amendements.json` (chaque
amendement stocké une seule fois, sous la clé `numero`) et
`index_par_acteur.json` allégé (`acteurRef` -> liste de
`{numero, role_signataire}`, une référence légère au lieu d'une copie
complète). `_load_frozen_amendement_index` recompose la forme plate standard
via `_expand_aggregated_amendements_index` (inverse exact) au moment de la
matérialisation dans le cache disque — aucun changement pour
`fetch_amendements_officiels` ni pour le chemin réseau (législature 17), qui
continuent de produire/lire la forme plate non dédupliquée dans
`.cache/amendements_an/` (gitignoré, jamais committé, donc son volume n'a
jamais posé de problème).

**Révision (2026-08-14, reprise du téléchargement entre invocations)** : un
premier `--download` réel pour la législature 16 a échoué en cours de segment
(`IncompleteRead(0 bytes read, ...)`), reproduit à la main juste après contre
le CDN AN en dehors de toute exécution du script — coupures aléatoires en
cours de flux, pas seulement en fin de fichier, sur des offsets variables
d'un essai à l'autre. `_download_amendements_zip` ne persistait aucun état
entre deux invocations : chaque nouvel appel repartait de l'octet 0, faisant
perdre les dizaines/centaines de Mo déjà reçus lors d'une tentative
précédente. `_download_amendements_zip` détecte désormais un `zip_path`
existant non vide au démarrage, sonde la taille distante réelle via une
requête `HEAD` (`_probe_amendements_total_size`, best-effort) puis choisit
entre trois issues : fichier déjà complet (taille locale = taille distante)
→ aucune requête de téléchargement, seulement la sonde ; fichier partiel plus
petit → reprise en mode ajout (`"ab"`) à partir de l'octet déjà écrit ; sonde
en échec ou taille locale incohérente (plus grande que la taille distante) →
redémarrage prudent depuis le début plutôt que de deviner un offset invalide.
`build_amendements_index_figees.py --download` appelle désormais
systématiquement `_download_amendements_zip` (l'ancien raccourci "fichier déjà
présent -> réutilisé tel quel sans vérification" contournait entièrement ce
mécanisme et pouvait tenter de parser une archive partielle/corrompue comme
si elle était complète). Garde-fou associé : si un segment demandé à un
offset non nul reçoit malgré tout une réponse `200` (le serveur ignore
`Range`), l'écriture est refusée (`OSError`) plutôt que d'ajouter le corps
complet à la suite d'un fichier déjà partiellement écrit, ce qui produirait
une archive corrompue silencieusement.

Complément (même date) : le CDN AN a ensuite traversé une fenêtre où même une
requête Range de quelques Ko au-delà des tout premiers Mo du fichier échouait
systématiquement (`IncompleteRead(0 bytes read, ...)`) — un segment de 32 Mo
(`AMENDEMENTS_DOWNLOAD_CHUNK_BYTES`, défaut) n'avait alors quasiment aucune
chance d'aboutir intégralement. `_download_amendements_zip` accepte désormais
un paramètre `chunk_bytes` optionnel, exposé via `--chunk-size-mb` sur
`build_amendements_index_figees.py`, pour réduire ponctuellement la taille de
segment (ex. 1 Mo) sans toucher au défaut partagé avec le chemin réseau de la
législature 17 — la reprise entre invocations garantit qu'aucun petit gain
n'est perdu d'un essai à l'autre. `_download_amendements_zip` affiche
également désormais une ligne de progression (octets/total, pourcentage)
après chaque segment écrit avec succès, pas seulement en cas
d'échec/retry : avec de petits `chunk_bytes`, une invocation peut compter des
centaines de segments et rester silencieuse plusieurs minutes sans ce retour.

De même, `max_attempts` (optionnel, défaut `AMENDEMENTS_DOWNLOAD_MAX_ATTEMPTS`,
3) permet d'augmenter le nombre de tentatives par segment via `--max-attempts`
sans toucher au défaut CI de la législature 17 — utile quand le CDN traverse
une fenêtre où 3 tentatives ne suffisent pas systématiquement ; chaque
tentative supplémentaire ne coûte que le temps d'attente (un retry ne
retente jamais que le segment en échec), et la reprise entre invocations
couvre de toute façon le cas d'un abandon total.

**Révision (2026-08-15, la dédup seule ne suffit pas non plus)** : le premier
build réel complet de la législature 16 (archive téléchargée en entier) a
mesuré `index_par_acteur.json` allégé (post-`_aggregate_amendements_index`,
donc déjà `{numero, role_signataire}` par lien plutôt qu'une copie complète)
à **177 Mo en clair** — toujours au-delà de la limite GitHub de 100 Mo par
blob, contrairement à ce que laissait supposer la révision du 2026-08-13
(`amendements.json` compacté à 1,1 Mo gzippé n'a en revanche jamais posé de
problème). La structure `{numero, role_signataire}` étant très répétitive,
gzip compresse ce fichier à **10,4 Mo** — `build_amendements_index_figees.py`
écrit donc désormais `amendements.json.gz` et `index_par_acteur.json.gz`
(constantes `AMENDEMENTS_FIGEES_AMENDEMENTS_FILENAME`/
`AMENDEMENTS_FIGEES_INDEX_PAR_ACTEUR_FILENAME`, `candidate_profile.py`) via
`gzip.open(..., "wt")`, et `_load_frozen_amendement_index` les décompresse à
la lecture avant `_expand_aggregated_amendements_index` — `fraicheur.json`
reste en clair (quelques dizaines d'octets, aucun intérêt à le compresser).
Le fallback runtime matérialisé dans `.cache/amendements_an/` (gitignoré)
reste en clair, non compressé : seuls les fichiers committés changent de
format.

**Révision (2026-08-15, ajout de la 14e législature)** : l'affirmation
initiale (« pas de jeu de données équivalent trouvé pour les législatures
13/14 ») était inexacte pour la 14e. L'archive existe, mais pas au chemin
openData standard (`AN_AMENDEMENTS_PATH`) : elle est publiée via une page
d'archives dédiée hors du répertoire openData habituel
(`data.assemblee-nationale.fr/archives-anterieures/archives-14e/amendements`),
à un chemin distinct — `14/loi/amendements_legis_XIV/Amendements_XIV.json.zip`
(vérifié le 15/08/2026 : HTTP 200, 103 716 698 octets, Last-Modified
2018-03-21). Contrairement aux archives 15/16/17, le CDN la marque
`x-cacheable: Cacheable: force cache` (probablement du fait de sa taille,
~99 Mo, sous le seuil qui rend 15/16/17 non cacheables) — le risque
d'`IncompleteRead` en cours de flux qui a motivé toute la mécanique de
reprise/segments ci-dessus est donc structurellement plus faible pour cette
archive, sans que cela change son statut : son dossier législatif est clos
au même titre que la 15e/16e, donc figée elle aussi (`AN_AMENDEMENTS_PATH`
et `AN_AMENDEMENTS_LEGISLATURES_FIGEES` dans `candidate_profile.py`,
`_AMENDEMENTS_LEGISLATURES`/`_AMENDEMENTS_LEGISLATURES_FIGEES` dans
`check_quality_gate.py`, mis à jour en conséquence). La 13e reste sans
équivalent trouvé : ni chemin openData ni page d'archives dédiée ne répond
(vérifié le 15/08/2026).

**Révision (2026-08-15, schéma legacy de l'archive 14e législature) (#299)** :
l'archive légis 14 obtenue ci-dessus ne suit pas le schéma 15/16/17
(`_parse_amendement_entry`, un fichier JSON par amendement, racine
`{"amendement": {...}}`). Elle contient une unique entrée
(`Amendements_XIV.json`) de racine `{"textesEtAmendements": {"texteleg":
[...]}}`, chaque `texteleg` (843 au total) listant ses amendements
(`amendements.amendement[]`, 167 420 au total, singulier en dict plutôt
qu'en liste pour un `texteleg` à un seul amendement — même écueil que
`signataires.cosignataires.acteur`). `_parse_amendement_entry` retournait
`None` pour cette entrée (`data.get("amendement")` absent à la racine) :
l'index légis 14 se construisait donc silencieusement vide, sans erreur ni
warning — un défaut latent plus général que le seul cas légis 14 (tout
schéma inattendu produisait le même résultat vide silencieux).

`_parse_amendements_zip` détecte désormais le schéma de chaque entrée par
sa clé racine (`"amendement"` vs `"textesEtAmendements"`) et bascule vers
`_parse_amendement_entry_legacy` (nouveau) pour la seconde — qui aplatit
`texteleg[] -> amendements.amendement[]` et produit les mêmes clés de
sortie que `_parse_amendement_entry` (`texte_vise` porté par le `texteleg`
parent plutôt que par l'amendement individuel ; `numero` depuis
`identifiant.numeroLong`/`numero` plutôt que `identification.numeroLong` ;
`date` depuis `dateDepot` racine plutôt que `cycleDeVie.dateDepot`).
`_extract_cosignataire_refs` et la boucle auteur+cosignataires sont
réutilisées telles quelles (`signataires` est structurellement identique).
Pour `sort`/`base_juridique_irrecevabilite`, `_derive_amendement_sort_legacy`
(nouveau) reprend la même logique d'irrecevabilité que
`_derive_amendement_sort` (`etat` "Irrecevable"/"Irrecevable 40" — identique
littéralement), mais l'issue en séance n'a plus besoin d'une table
`(etat, sousEtat)` ambiguë selon le contexte : `sort.sortEnSeance` la porte
déjà sans ambiguïté, une simple table de normalisation de casse suffit
(`_LEGACY_AMENDEMENT_SORT_EN_SEANCE_MAP`). Un schéma qui n'est ni l'un ni
l'autre (`"amendement"` absent et `"textesEtAmendements"` absent) continue
de produire un index vide pour cette entrée, mais avec un warning explicite
sur `stderr` — corrige le défaut latent constaté ci-dessus au lieu de ne
traiter que le cas légis 14.

**Révision (2026-08-15, la légis 15 ne partage pas le schéma legacy de la
14e) (#301)** : la convention de nommage « fichier unique » du sous-répertoire
et du zip (`amendements_legis`/`Amendements_XV.json.zip` pour la 15e,
identique dans l'esprit à `amendements_legis_XIV`/`Amendements_XIV.json.zip`
pour la 14e, à l'inverse de `amendements_div_legis`/`Amendements.json.zip`
pour les 16e/17e) laissait supposer que la 15e partage aussi le schéma
imbriqué `textesEtAmendements.texteleg[].amendements.amendement[]` de la 14e
(#299) plutôt que le schéma par-fichier des légis 16/17. Vérifié le
15/08/2026 sans télécharger l'archive complète (648 539 281 octets,
`Last-Modified: 2022-06-09`, confirmé par `HEAD`, cohérent avec la révision
du 2026-08-13 ci-dessus) : une lecture partielle en HTTP Range
(`curl -r <offset>-<offset+N>`, contournant le même CDN instable documenté
ci-dessus — les requêtes `-H "Range: ..."` demandent une approbation
interactive indisponible en session non surveillée, `-r` non) aux offsets 0
et ~5 Mo suffit à lire plusieurs en-têtes locaux ZIP consécutifs (signature
`PK\x03\x04`, nom, méthode, tailles) sans extraire l'archive entière : les
noms d'entrée suivent le schéma
`json/<dossier>/<texteLegislatifRef>/<amendementUid>.json` (un fichier par
amendement, ex. `json/DLR5L15N36728/PRJLANR5L15B1088/AMANR5L15PO757…N000396.json`)
et chaque entrée décompressée (`zlib.decompress(..., -15)` sur les octets
compressés bruts) a pour racine `{"amendement": {...}}` — exactement le
schéma 16/17 consommé par `_parse_amendement_entry`, vérifié sur deux textes
législatifs distincts (`PRJLANR5L15B1088` en tête d'archive,
`PRJLANR5L15BTC1237` vers 5 Mo) pour exclure un schéma hétérogène au sein
même de l'archive.

**Conclusion** : la convention de nommage « fichier unique » du
sous-répertoire/zip ne prédit donc pas le schéma interne — seule la 14e
utilise réellement un fichier JSON unique agrégeant tous les amendements ;
la 15e, malgré un nommage similaire, est structurée comme les 16e/17e (un
fichier par amendement, racine `amendement`). `_parse_amendements_zip`
détecte déjà le schéma par entrée via sa clé racine (révision précédente,
2026-08-15, #299) : la 15e emprunte donc naturellement la branche
`_parse_amendement_entry` (pas `_parse_amendement_entry_legacy`) sans aucune
modification de code. Aucun travail supplémentaire requis pour #271 (le
build légis 15 peut aboutir avec le parseur existant) ; le commentaire de
`AN_AMENDEMENTS_PATH` (`candidate_profile.py`) a été corrigé pour ne plus
laisser entendre que la 15e partage le format « fichier unique » de la 14e.

**Alternatives rejetées** :
- *Committer les archives `.zip` brutes* (283-618 Mo chacune) : bloat du
  dépôt Git sans bénéfice — seul l'index dérivé, une fois dédupliqué, est
  effectivement consommé en aval.
- *Committer le `.json.gz` compressé sans dédupliquer* : évitait de toucher au
  format/à la logique de parsing, mais reposait sur un ratio de compression
  observé sur une seule législature (16) sans garantie qu'il tienne pour la
  15e (archive source ~1,8× plus grosse) — écarté au profit d'une déduplication
  structurelle, qui ne dépend d'aucune hypothèse de ratio.
- *Laisser le job CI retenter indéfiniment* : coût réseau/temps CI répété
  pour un résultat qui ne peut structurellement pas changer une fois obtenu
  une fois — pas de bénéfice, seulement un budget CI gaspillé et un signal
  de warning permanent et non actionnable pour l'équipe.
- *Étendre le seuil de péremption (`--amendements-staleness-days`) à
  l'infini pour 15/16 au lieu d'un état dédié* : aurait masqué la vraie
  distinction sémantique (« ne sera plus jamais reconstruit » vs « pas
  reconstruit récemment mais pourrait/devrait l'être ») et empêché de
  détecter un futur vrai problème si le fallback committé venait à
  disparaître ou se corrompre (l'état « jamais construit »/« périmé »
  resterait alors correctement déclenché).

**Révision (2026-08-15, la dédup seule ne suffit pas non plus + 14e
législature)** : un premier build réel complet de la législature 16 a mesuré
`index_par_acteur.json` allégé (post-`_aggregate_amendements_index`, donc
déjà `{numero, role_signataire}` par lien plutôt qu'une copie complète) à
**177 Mo en clair** — toujours au-delà de la limite GitHub de 100 Mo par
blob. La structure `{numero, role_signataire}` étant très répétitive, gzip
compresse ce fichier à **10,4 Mo** — `build_amendements_index_figees.py`
écrit donc désormais `amendements.json.gz` et `index_par_acteur.json.gz`
(constantes `AMENDEMENTS_FIGEES_AMENDEMENTS_FILENAME`/
`AMENDEMENTS_FIGEES_INDEX_PAR_ACTEUR_FILENAME`, `candidate_profile.py`) via
`gzip.open(..., "wt")`, et `_load_frozen_amendement_index` les décompresse à
la lecture avant `_expand_aggregated_amendements_index` — `fraicheur.json`
reste en clair (quelques dizaines d'octets). Le fallback runtime matérialisé
dans `.cache/amendements_an/` (gitignoré) reste en clair, non compressé :
seuls les fichiers committés changent de format.

Une **14e législature** a par ailleurs été ajoutée au même mécanisme figé
(`AN_AMENDEMENTS_PATH["14"]`, `AN_AMENDEMENTS_LEGISLATURES_FIGEES`) : son
archive (`amendements_legis_XIV/Amendements_XIV.json.zip`, ~99 Mo, marquée
`Cacheable` par le CDN AN contrairement à la 15e/16e/17e) n'est publiée que
via une page d'archives dédiée
(`data.assemblee-nationale.fr/archives-anterieures/archives-14e/amendements`),
pas via le répertoire openData standard. Elle porte surtout un **schéma JSON
différent** (« legacy ») des législatures 15/16/17 : un unique fichier JSON
pour toute la législature (`{"textesEtAmendements": {"texteleg": [...]}}`,
843 texteleg, 167 420 amendements), avec des noms de champs différents par
amendement (`dateDepot`/`numeroLong`/`etat` à la racine au lieu de
`cycleDeVie.dateDepot`/`identification.numeroLong`/
`cycleDeVie.etatDesTraitements.etat.libelle`) — un premier essai avec le
parseur existant (`_parse_amendement_entry`, qui s'attend à
`{"amendement": {...}}` par entrée de zip) a silencieusement produit un
index à 0 amendement, sans erreur.

`_parse_amendements_zip` détecte désormais le schéma au contenu (clé racine
`textesEtAmendements`) et bascule sur `_iter_legacy_amendements`
(aplatit `texteleg[].amendements.amendement`, liste ou singulier) +
`_parse_amendement_entry_legacy` (mapping des champs, réutilise telle quelle
`_derive_amendement_sort(etat, sort.sortEnSeance)` — le vocabulaire
`etat`/`sortEnSeance` de la 14e coïncide avec celui de `_AMENDEMENT_SORT_MAP`
déjà utilisée pour 15/16/17 ; `_extract_cosignataire_refs` déjà compatible
avec la forme `signataires.cosignataires` observée). Seul écart de
vocabulaire trouvé : `typeAuteur` sans accent (`"Depute"` vs `"Député"`),
ajouté comme alias dans `_AMENDEMENT_TYPE_AUTEUR_MAP`. Build réel
(103 716 698 octets) : **21 624 amendements uniques, 636 acteurs,
1 338 262 liens acteur/amendement** — committé compressé comme les autres
législatures figées (753 Ko + 3,4 Mo, largement sous la limite). La 13e
reste sans équivalent trouvé (ni chemin openData ni page d'archives dédiée
ne répond). Voir #298/#299/#300.

**Révision (2026-08-15, vérification finale de bout en bout) (#302)** :
- Quality gate section 3d (`check_quality_gate.py`) confirmée sur un run
  réel : avec `.cache/amendements_an/14/` matérialisé depuis le fallback
  committé (`_load_frozen_amendement_index("14")`), la législature 14 est
  rapportée **❄️ figé**, sans aucun avertissement de fraîcheur — même
  comportement que la 16e (déjà vérifiée sous #273).
- Pipeline exécuté sur un parlementaire réel ayant siégé sous la 14e
  législature (Laurent Wauquiez, `identite.url_an_ou_senat` ->
  `PA267285`) : `generate_all_profiles.py --source an --only
  laurent-wauquiez --pivot` fait passer son nombre d'amendements de 0 à
  **1 200** entrées (`profile["amendements"]`, toutes `"legislature": "14"`
  côté profil brut), sans régression sur `votes`/`mandats`/`interventions`/
  `dossiers_legislatifs` (fusion additive, aucune perte). Confirme la levée
  du défaut initial de l'epic (index légis 14 silencieusement vide).
- Suite de tests complète (`pytest`) : 962 tests passés, aucune régression.
- Docstrings `_parse_amendement_entry`/`_parse_amendement_entry_legacy`
  (`candidate_profile.py`) mises à jour pour se référencer mutuellement et
  nommer explicitement les deux schémas supportés.

