<a id="votes-multi-legislature"></a>
# Votes : agrégation des législatures 14 à 17, index dédupliqué, 14/15/16 figées (#403) (2026-08-18)

`2026-08-18`

> **En bref** — 14/15/16 figées et committées.

**Contexte** : les votes ne couvraient qu'**une seule législature par profil**,
et en pratique toujours la 16e — 86 des 87 profils bruts, aucun en 17e. Le jeu
de données s'arrêtait donc en **juin 2024**, sur la législature en cours.
`fetch_votes_officiels()` prenait un `base_url` NosDéputés unique et le
convertissait en législature via `LEGISLATURE_BY_BASE_URL`. Depuis l'étape 4 de
#369, `identity_base_url` vaut `None` pour tout député résolu via l'AN : on
retombait systématiquement sur `base_urls[0]`, mappé en dur sur « 16 ». Double
défaut hérité de l'ère NosDéputés — mono-législature *par construction*, et un
mapping dont plus rien ne garantissait la pertinence.

**Décision** : `AN_SCRUTINS_LEGISLATURES = ("17", "16", "15", "14")` remplace le
mapping par domaine ; `fetch_votes_officiels(url_an_ou_senat, warnings)` agrège
les quatre législatures, chacune tentée indépendamment (une archive absente
n'interrompt plus les autres, même précaution qu'en #241 sur les amendements).
Le mapping domaine → législature n'est pas supprimé mais **déplacé dans
`group_roster.py`**, son seul utilisateur légitime restant : les rosters de
groupes sont bien servis par un domaine NosDéputés par législature (vérifié le
18/08/2026 : `www.nosdeputes.fr` sert toujours la 16e, 618 députés, mandats
2022-06-22 → 2024-06-09 — le site n'a pas été étendu à la 17e).

**Déduplication par `uid`, jamais par `numero`** — le point non évident. Le
numéro de scrutin AN **repart de 1 à chaque législature** : dédoublonner par
numéro effacerait des scrutins distincts. L'`uid` (`VTANR5L17V1000`) porte la
législature et est unique toutes législatures confondues. Le corollaire vaut
côté agrégats : `group_profile._compute_cohesion_votes` indexait par
`numero_scrutin` seul, ce qui aurait **fusionné les décomptes** du n° 1000 de la
16e et de celui de la 17e dès la première regénération. La cohésion (et le
rapport d'écarts internes) filtre donc désormais sur la législature du groupe —
un profil de groupe de la 16e ne peut plus se voir attribuer des scrutins de la
17e par ses membres réélus. Les votes sans `legislature` (collectés avant #403)
sont conservés par ce filtre : une donnée absente n'est pas une donnée
contradictoire (règle 5).

**Deux conditionnements d'archive**. La 14e est livrée en JSON **monolithique**
(`Scrutins_XIV.json`, `scrutins.scrutin[]`), les 15e/16e/17e en arborescence
`json/` d'un fichier par scrutin. Le conditionnement est détecté par la clé
racine, jamais par le nom de fichier. Même changement d'architecture AN qu'en
#400 sur les dossiers législatifs — mais ici, contrairement aux dossiers, les
données de la 14e sont bien présentes (1 354 scrutins) : seul le
conditionnement diffère, et l'indexeur qui n'attendait que `json/*.json` y
trouvait 0 acteur.

**Trois schémas de `decompteNominatif`, pas deux** (relevé exhaustif sur les
quatre archives) : pluriel `pours`/`contres` (15e, 17e, et 4 105 des 4 106
scrutins de la 16e), singulier `pour`/`contre` avec `abstentions`/`nonVotants`
au pluriel (toute la 14e), et tout au singulier pour un unique scrutin.
L'indexeur d'avant #403 n'acceptait que le pluriel : il perdait donc en silence
la totalité de la 14e — et un scrutin de la 16e.

**Scrutins du Congrès écartés**. Ce scrutin isolé est celui du **Congrès du
4 mars 2024** (constitutionnalisation de l'IVG, uid `VTCGR5L16V1`), présent dans
l'archive AN de la 16e. Il est volontairement exclu (`AN_SCRUTIN_UID_PREFIXE`) :
le Congrès est une assemblée distincte — d'où les 24 sénateurs apparaissant dans
sa ventilation nominative — et sa numérotation **repart de 1 en partageant
l'espace de numéros de l'AN**. Il porte le n° 1, déjà attribué à la motion de
censure du 11/07/2022. Le publier tel quel donnerait une source primaire fausse
(vérifié : `/dyn/16/scrutins/1` renvoie bien la motion de censure) et le
confondrait avec elle dans la cohésion de groupe. Le publier *correctement*
suppose un identifiant et une source propres au Congrès, hors périmètre de
#403 : noté au ROADMAP plutôt que bâclé ici. Une fois exclu, l'index de la 16e
retombe exactement sur les chiffres de référence de l'issue (617 acteurs,
602 911 votes nominatifs).

**Traçabilité par vote, plus par profil**. `votes_source` énumère désormais
*toutes* les législatures couvertes (« législatures 15, 16, 17 ») — le singulier
sur un profil qui en agrège trois rendrait la limite du jeu de données illisible
(AGENTS.md §2.8). Comme aucune législature ne vaut plus pour tous les votes d'un
profil, chaque vote porte sa propre source primaire
(`https://www.assemblee-nationale.fr/dyn/<legislature>/scrutins/<numero>`,
vérifiée sur les 14e/15e/17e) au lieu de la laisser déduire de `votes_source` —
ce que faisait `web/old/v3/js/utils.js` par expression régulière, et qui devient
faux dès que plusieurs législatures sont agrégées.

## Budget CI : mesuré avant généralisation, pas après

C'était le point dur de l'issue — ~994 Mo de cache décompressé pour les quatre
législatures, un ordre de grandeur au-dessus de #400 (46 Mo), sur un pipeline
qui a déjà connu **deux OOM** sur l'index des amendements (#377, #392). Mesure
préalable (méthode [[budget-roster-mesure]] #376), sur les archives réelles :

| Forme d'index | 14 | 15 | 16 | 17 | Total |
| --- | --- | --- | --- | --- | --- |
| Plate (une copie du méta par votant) | 29,5 Mo | 140,7 Mo | 189,4 Mo | 381,5 Mo | **741 Mo** |
| Dédupliquée (`scrutins.json` + réf. `[uid, position]`) | 3,0 Mo | 13,1 Mo | 16,7 Mo | 35,5 Mo | **68 Mo** |
| Dédupliquée, gzippée (forme committée) | 0,13 Mo | 1,14 Mo | 1,51 Mo | — | **2,8 Mo** |

Les deux remèdes qui avaient fonctionné sur les amendements sont donc repris
tels quels : **forme dédupliquée** (#377) — le méta du scrutin, titre compris,
stocké une fois au lieu d'être recopié pour chacun de ses ~150 votants, d'où le
facteur 11 ci-dessus, et un pic de construction ramené à **138 Mio de RSS** pour
la 17e (la plus lourde) — et **shardage par acteur** (#392) : une tranche
`index_par_acteur/PA1567.json` (~55 Ko) est lue par candidat au lieu des 132 à
357 Mo d'index complets, ce qui ramène le coût par candidat à **0,02 s** après
matérialisation du cache.

**Législatures 14/15/16 figées** (`AN_SCRUTINS_LEGISLATURES_FIGEES`,
`src/build_scrutins_index_figes.py`, sortie committée sous
`raw_data/scrutins_an_figes/`), même schéma que
[[amendements-legislatures-figees]] mais **pas pour la même raison** : les
archives de scrutins sont petites (0,7 à 26 Mo) et toutes marquées `Cacheable`
par le CDN AN, donc rien à voir avec les `IncompleteRead` chroniques des
archives d'amendements (283-618 Mo). Ce qui est évité ici, c'est un coût
**répété inutilement par chaque shard CI** pour trois législatures closes
(Last-Modified vérifié : 2018-03-21, 2022-06-09, 2024-06-28) dont l'index est
identique à l'octet près d'un run à l'autre. Le chemin réseau reste fonctionnel
si le fallback committé manque : le gel est une économie, jamais une dépendance.

**Résultat mesuré, cache froid** : 18,9 s et un seul téléchargement (26 Mo, la
17e) pour l'ensemble ; **80 Mo** de cache disque au lieu des 992 Mo qu'aurait
coûtés la généralisation naïve — soit moins que les 251 Mo du cache
mono-législature *actuel*. Le cache hérité (fichier unique, forme plate) est
indiscernable d'un cache absent pour le lecteur : il est reconstruit, jamais
relu en mémoire — c'est précisément la relecture qui avait déclenché l'OOM
killer en #377.

**Effet de la fusion additive sur l'existant** : `votes[]` suit la règle « ancienne
entrée gagne » (`merge_profile.merge_lists_by_key`, AGENTS.md §3), et la clé de
fusion reste `(numero_scrutin, date)` —
inchangée, donc les 92 344 votes déjà collectés se réconcilient bien avec leur
équivalent recollecté au lieu de se dédoubler (vérifié : aucune collision
`numero`+`date` à l'intérieur d'une législature, et les périodes de législature
ne se chevauchent pas). Contrepartie : ces entrées existantes **conservent leur
forme d'avant #403**, sans `legislature` ni `source_url`, jusqu'à un run
`fresh_run=true`. C'est précisément le cas que le filtre de cohésion traite en
conservant les votes sans législature. Aucun changement de politique de fusion
n'est fait ici : enrichir champ à champ une entrée existante serait un
changement de comportement pour tous les votes, hors périmètre de #403.

**Gain éditorial** : 92 344 → **246 196 votes** (×2,7), 0 → **55 profils** avec
des votes de la 17e. Vérifié sur les quatre profils témoins de l'issue
(`christophe-bentz` 2 480 → 7 401, `beatrice-piron` 1 921 → 6 413,
`christine-le-nabour` 2 178 → 6 048, `antoine-villedieu` 1 041 → 4 202).

**Alternative écartée** : basculer les votes en lecture *cache-only* avec un job
CI dédié, comme les amendements ([[amendements-index-job-dedie-ci]]). Justifié
là-bas par des archives de 283-618 Mo dont le téléchargement échouait ; ici, une
seule archive active de 26 Mo reste à charge du chemin paresseux, pour un job CI
et un artifact en moins.
