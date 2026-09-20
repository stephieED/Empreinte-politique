<a id="cache-amendements-existence-nest-pas-conformite"></a>
# L'existence d'un cache n'est pas la preuve de son contenu — et #447 n'avait pas de seconde cause (2026-08-19)

`2026-08-19`

> **En bref** — l'existence d'un répertoire de cache ne prouve rien de son contenu : vérifier aussi le format de clé.

## Ce que #447 soupçonnait, et ce que la mesure dit

Le dernier commentaire de #447 (19/08 18:58Z) concluait que la couverture `uid`
partielle était **reproduite à la génération**, et donc qu'une seconde cause
subsistait dans le chemin de code d'`extract-an`, à côté de
[[publication-scopee-artifacts]]. L'argument : les 6 candidats déclarés sont
rigoureusement inchangés entre `698a882` et l'état committé après le run
`32277443716`, alors que les 8 jobs `extract-an` ont tourné avec succès.

**Cet argument ne conclut pas.** Sous fusion additive, « inchangé » est
exactement ce qu'on observe quand la version fraîche est un **sous-ensemble** de
la version committée : l'union d'un sous-ensemble et de son sur-ensemble est le
sur-ensemble. Une sortie fraîche à 100 % d'`uid` et un profil committé mixte
produisent donc le même « aucun changement » qu'une sortie mixte.

Le run suivant tranche. `32288588518` (sha `36d51e8`, donc avec #451/#452/#453,
succès le 19/08 à 19:34Z, données committées en `a125e9e`) a régénéré ces mêmes
profils, cette fois sans le défaut de publication de #450 :

| slug | avant (`698a882`) | après (`a125e9e`) |
| --- | --- | --- |
| gabriel-attal | 2 018 / 944 uid | **944 / 944** |
| jean-luc-melenchon | 38 175 / 18 721 uid | **18 721 / 18 721** |
| edouard-philippe | 2 715 / 1 966 uid | **1 966 / 1 966** |
| laurent-wauquiez | 5 482 / 3 533 uid | **3 533 / 3 533** |
| marine-le-pen | 27 085 / 13 991 uid | **13 991 / 13 991** |
| jerome-guedj | 27 812 / 14 335 uid | **14 335 / 14 335** |

Et la mesure décisive n'est pas le compte, c'est l'**identité d'ensemble** :
comparés entrée par entrée (JSON canonique), les amendements d'après sont
**exactement** le sous-ensemble portant un `uid` d'avant — 0 entrée ajoutée, 0
entrée perdue, sur les 6 profils et 53 490 entrées. La sortie d'`extract-an`
était donc déjà à 100 % au run précédent. Corpus committé à `a125e9e` : **179
profils AN à 100 %, 0 mixte, 0 à 0 %, 791 831 amendements tous porteurs d'un
`uid`**.

**#447 n'avait pas de seconde cause.** Sa cause était entièrement le `path:`
d'upload de [[publication-scopee-artifacts]], et #451 l'a refermée. La leçon
n'est pas dans le code mais dans l'inférence : *sous fusion additive, l'absence
de différence n'est pas une observation sur la version fraîche.* Le contrôle qui
l'aurait dit tout de suite existe déjà — `src/audit_diff_profils.py`, qui compare
par profil et par champ au lieu de comparer des totaux.

## Ce que l'enquête a trouvé à la place : deux impasses silencieuses

Aucune des deux n'a causé #447. Les deux sont mesurées, et les deux sont du même
mode d'échec que [[signal-uid-partiel]] : un zéro qui ne se signale pas.

**1. Un cache figé au format hérité n'est ni reconstruit, ni lu.**
`amendements_index_deja_figee()` vérifiait la *présence* (`amendements.json` +
répertoire de tranches + `fraicheur.json` portant `figee: true`) et jamais le
*format*. Un cache matérialisé avant la correction de clé du 18/08
([[amendements-cle-uid]]) est donc déclaré « déjà figé », et
`build_amendements_index.py` le saute — pendant que
`_read_cached_amendements_acteur` le **refuse** à la lecture, précisément parce
qu'il est hérité. Ni reconstruit, ni lu : la législature perd la **totalité** de
ses amendements, et le seul signe est un warning soft « index en cache absent ».

Mesuré le 19/08/2026 sur le cache local, sans réseau — les trois législatures
figées étaient simultanément dans les deux états :

| législature | `amendements_index_deja_figee` | `_read_cached_amendements_acteur` |
| --- | --- | --- |
| 14 | `True` | `None` (index refusé) |
| 15 | `True` | `None` (index refusé) |
| 16 | `True` | `None` (index refusé) |

Le contrôle ajouté lit **une** tranche (~285 Ko), jamais l'index entier : la
contrainte qui a fait naître cette fonction — ne pas recharger plusieurs Go en
clair, sous peine d'OOM ([[amendements-legislatures-figees]]) — reste tenue. Un
refus coûte au pire un retéléchargement ; l'accepter coûte une législature
entière, silencieusement.

**2. Un répertoire de tranches à moitié écrit ressemble à un cache complet.**
`_write_cached_amendements_agreges` promettait dans sa propre docstring qu'« une
écriture interrompue laisse un cache traité comme absent, jamais un cache
incohérent ». Le code ne le tenait pas : il faisait `rmtree` puis `mkdir` puis
remplissait **en place**, donc pendant toute la boucle le répertoire existait à
moitié rempli. Or `index_dir.is_dir()` suffit à `_download_and_build_amendement_index`
pour conclure au cache-hit — il n'est alors jamais reconstruit — et chaque acteur
dont la tranche manque encore est lu comme « aucun amendement » (liste vide) au
lieu de « index indisponible » (`None`). C'est exactement la distinction dont
dépend le warning de `fetch_amendements_officiels`.

Le cas est atteignable, pas théorique : le step `Upload artifact amendements AN`
de `generate-data.yml` est en `if: always()`, donc un job interrompu publie
l'état partiel du disque, que les jobs consommateurs téléchargent ensuite.

Les tranches sont désormais écrites dans un répertoire temporaire, publié d'un
seul `os.replace`. C'est cette propriété — et elle seule — qui rend légitime le
contrôle sur une **tranche unique** de `_cache_amendements_au_format_uid`, dont
#447 demandait s'il constituait un défaut latent : l'échantillon unique est
correct **si** un répertoire qui existe est toujours complet, ce qui n'était pas
garanti. Réponse : le défaut n'était pas dans la garde, il était dans l'écriture
qu'elle présuppose.

**Alternative écartée** : contrôler *toutes* les tranches au lieu d'une. 650
fichiers relus à chaque décision de cache-hit, pour un invariant que l'écriture
peut garantir gratuitement — on paierait à chaque lecture le prix d'un défaut
d'écriture.

**Alternative écartée** : un fichier-marqueur « complet » écrit en dernier dans
le répertoire. Il faudrait le contrôler partout où le répertoire est jugé
valide, et rien n'empêcherait un lecteur futur d'oublier. Le `os.replace` rend
l'état incohérent **inobservable** au lieu de le rendre détectable.

## Un angle mort du signal de #447 lui-même

La §3c du quality gate — le signal ajouté par #452 pour surveiller précisément
ce défaut — ne regardait que les profils de `chambre` `AN`/`deputes` **avec
identité**. Or un profil peut cesser d'être compté sans cesser d'être publié :
au 19/08/2026, `jean-luc-melenchon` porte **18 721 amendements AN publiés** et
est sorti du champ de la section en passant à `chambre: "Senat"` avec `identite`
vide. Soit **2,3 % du corpus invisibles au signal même qui doit les surveiller**,
sur l'un des profils que #447 cite nommément — et s'il était revenu mixte, la
§3c n'aurait rien dit.

La §3c distingue donc désormais deux populations. Les compteurs « candidats AN »
et le signal de régression « `amendements[]` vide partout » gardent la
population dont on **attend** des amendements ; la mesure de couverture `uid`,
elle, porte sur tout profil qui en **publie**, quelle que soit sa `chambre`. Un
profil hors population AN n'entre dans le décompte que s'il a des amendements,
il ne peut donc jamais éteindre le signal de régression.

L'apport hors population AN est affiché sur sa propre ligne plutôt que fondu
dans les compteurs « candidats AN » — chaque nombre garde ainsi un sens unique.
Rendu sur le corpus de `a125e9e` : 207 candidats AN avec identité, dont 179 avec
amendements, **plus 1 profil hors population portant 18 721 amendements**, pour
810 552 amendements mesurés (791 831 avant) tous porteurs d'un `uid`.

*La §3c suit les amendements, pas la fiche.* Un dénominateur publié dépend de ce
qui est publié, pas de ce qui est classé (AGENTS.md §2.7).

## Reste ouvert

`_write_cached_scrutins` a la même forme d'écriture non atomique que son
homologue amendements (`rmtree` + `mkdir` + remplissage en place, autour de
`_scrutins_shard_path_acteur`). Aucune garde de format n'en dépend et rien ne
l'a signalé en pratique ; ce n'est **pas** corrigé ici, délibérément, pour ne pas
toucher au chemin des votes dans la foulée de [[normalisation-votes]]. Noté pour
que le prochain passage ne le redécouvre pas.

---
