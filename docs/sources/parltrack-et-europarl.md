# ParlTrack et `data.europarl.europa.eu` — les deux sources du versant européen

> **Statut : les deux sont collectées.** `data.europarl.europa.eu` porte l'identité et les
> mandats (job `extract-ue-officiel`) ; les dumps ParlTrack portent l'activité — votes,
> amendements, dossiers, interventions (job `extract-parltrack`). Ce fichier décrit ce que
> les **fournisseurs** publient, et dérive avec eux, non avec notre code.
>
> Il n'existait pas avant le 14/09/2026, et c'est ce qui a coûté le plus cher sur ce versant :
> le format des dumps a été supposé pendant toute la vie du module.

## Producteurs et licences

| Source | Producteur | Licence | Contrainte |
| --- | --- | --- | --- |
| `parltrack.org/dumps` | ParlTrack (association) | **ODbL v1.0** | **partage à l'identique** si un jeu dérivé est republié |
| `data.europarl.europa.eu` | Parlement européen | **CC BY 4.0** | attribution |

La page Copyright de parltrack.org ne donne l'ODbL que pour les **dumps JSON**. Le CC BY-SA 3.0
qu'on y lit couvre le HTML des pages, que ce pipeline ne télécharge jamais. `AGENTS.md` §7
portait « CC0 / ODbL (mixed) » jusqu'à ce que [`licences`](../decisions/licences.md) le
vérifie en direct — et `src/mep_profile.py` a inscrit « CC0 » quatre lots de plus, jusqu'à
[#909](../decisions/licence-jamais-en-dur-909.md).

Le portail `data.europarl.europa.eu` est sous **CC BY 4.0** : décision du Bureau du Parlement
européen du 16/12/2024, [EUR-Lex C/2025/341](https://eur-lex.europa.eu/eli/C/2025/341/oj),
article 4, et champ `info.license` de la documentation OpenAPI de l'API. Toutes nos requêtes
européennes vont à ce portail. `www.europarl.europa.eu` n'est **jamais interrogé** : il est
derrière un pare-feu anti-robot, et on n'y écrit que des liens. Son avis juridique
(« © Union européenne – Source : Parlement européen ») ne vaudrait que si l'on reproduisait
son contenu. Cette ligne a porté « EP Legal Notice » jusqu'à
[#983](../decisions/licence-parlement-europeen-cc-by-983.md).

## Le format des dumps, et l'incident qu'il a causé

**Un dump n'est pas du NDJSON.** C'est **un seul tableau JSON**, un objet par ligne, le
séparateur en **tête** : la première ligne commence par `[`, les suivantes par `,`, la dernière
est `]` seule. La page https://parltrack.org/dumps le dit en toutes lettres.

Le module les a lus comme du NDJSON pendant toute sa vie. `json.loads` échouait sur chaque
ligne, et l'échec partait dans un `except JSONDecodeError: continue`. Mesuré le 09/09/2026 :
les index faisaient **2 octets** — `{}` — en face de 182 Mio de dumps, et les 7 candidats
déclarés à mandat européen publiaient « aucune donnée trouvée » **sur eux**
([`lecture-dumps-parltrack-683`](../decisions/lecture-dumps-parltrack-683.md)).

C'est pour ce genre de dérive que ce fichier existe : un format de fournisseur qui change, ou
qu'on a mal lu, ne se voit pas dans notre code.

## Les huit dumps, et les cinq que nous lisons

| Dump | Lu ? | Ce qu'il porte |
| --- | --- | --- |
| `ep_votes.json.zst` | oui | **44 648** scrutins nominatifs en séance |
| `ep_dossiers.json.zst` | oui | **23 885** dossiers législatifs |
| `ep_amendments.json.zst` | oui | amendements en commission |
| `ep_plenary_amendments.json.zst` | oui | amendements en séance |
| `ep_mep_activities.json.zst` | oui | interventions, questions, rapports, résolutions |
| `ep_meps` | non | doublon du portail officiel, d'où l'identité est déjà tirée |
| `ep_com_votes` | non | **89 scrutins en tout** |
| `ep_comagendas` | non | ne nomme personne |

## Ce que chaque dump porte vraiment — mesuré le 13-14/09/2026

### `ep_votes` — les scrutins

| Champ | Couverture | Ce qu'il donne |
| --- | ---: | --- |
| `voteid` | **100 %** | l'identifiant de scrutin |
| `ts`, `title`, `url` | **100 %** | date, intitulé, procès-verbal officiel |
| `doc` | 87,2 % | le document voté — `A6-0034/2004` |
| `epref` | 87,1 % | la référence de dossier — `2004/0234(CNS)` |
| `votes` | **99,8 %** | les effectifs pour / contre / abstention, **ventilés par groupe** |

**`voteid` a deux formes**, et elles cassent un tri naïf : **4 855** entiers (`7649`) et **716**
chaînes composites (`'2017-06-01 00:00:00-1.'`), espaces et point final compris, sur les 5 571
scrutins que le corpus cite. Comparer un entier à une chaîne lève.

### `ep_dossiers` — les dossiers

`procedure.reference` est renseigné à **100 %** ; `procedure.stage_reached` sur **20 442 des
23 885** dossiers (**85,6 %**), pour **16 valeurs** distinctes.

**Le piège des commissions.** Une entrée de `committees[]` porte deux champs qui semblent dire
la même chose :

| Champ | Renseigné | Verdict |
| --- | ---: | --- |
| `responsible: true` | 521 / 18 242 — **2,9 %** | inutilisable |
| **`type`** | **97 %** | c'est lui qu'il faut lire |

`type` vaut `Responsible Committee`, `Committee Opinion`, `Former Responsible Committee`,
`Joint Responsible Committee`… S'être fié au premier aurait rendu une commission au fond pour
**1,2 %** des dossiers au lieu de **97,7 %**.

Et quand la saisine est **conjointe**, `committee` et `committee_full` sont des **listes**, pas
des chaînes — 36 des 402 entrées au fond de notre population.

**La matière : `procedure.subject`, sous deux formes.** Classification OEIL du dossier,
renseignée sur **389 / 389** dossiers que nos profils citent, y compris les 40 résolutions
d'actualité (`RSP`) — qu'aucune commission au fond ne couvre, puisqu'une RSP n'est jamais
renvoyée en commission. Forme courante : un dict `{"6.20.03": "Bilateral economic…"}` (387
dossiers) ; forme rare : une **liste de chaînes** où code et libellé sont collés,
`"6.20.03 Bilateral economic…"` (2 dossiers). Lire la seule première perd les autres sans
erreur. Code hiérarchique, 238 valeurs sur ce corpus : pas un vocabulaire fermé. Mesuré le
16/09/2026 (#901).

**Le premier niveau — la famille — n'a de libellé que sur une minorité de dossiers.** Un
dossier porte d'ordinaire ses seuls codes profonds (`6.40.10`) ; le code d'une famille
(`6`) n'apparaît, avec son libellé, que sur **437** occurrences des 23 885 dossiers du dump
(mesuré le 17/09/2026 sur le dump du 17/08). Il faut donc le lire sur **tout** le dump. Trois
formes : une clé de dict seule (`"4": "Economic, social and territorial cohesion"`), une
chaîne de liste qui colle code et libellé (`"3 Community policies"`), et des fiches anciennes
qui n'ont que `meta.created`, pas `meta.updated`. **Le libellé a changé avec le temps** :
« Internal market, SLIM » (2013) puis « Internal market, single market » (2026). Libellés en
**anglais** seulement ; le site OEIL en français répond `307` à une requête simple.

### `ep_mep_activities` — les activités

Une entrée `REPORT` porte `dossiers[]`, la référence de procédure visée, sur **144 des 146**
entrées d'un échantillon de 300 MEP. C'est ce qui permet de résoudre le stade d'un texte porté
qui ne vient pas d'une saisine comme rapporteur.

### `ep_amendments` — les amendements

`id` (`PE529.899-1`), `reference` (`2014/2021(INI)`), `peid`, `date`, `committee`, `seq`, `src`
sont renseignés à **100 %**. **Aucun champ ne porte le `sort`** d'un amendement — c'est le seul
manque réel de ce versant, et il n'est comblé par rien.

## Ce que la clé `reference` permet

Le même identifiant `2014/2021(INI)` circule dans les trois dumps : `procedure.reference` côté
dossiers, `epref` côté votes, `reference` côté amendements, `dossiers[]` côté activités. C'est
lui qui rend l'ensemble rattachable, et c'est la clé des deux index de
[`index-scrutins-europeens-901`](../decisions/index-scrutins-europeens-901.md) et
[`index-dossiers-europeens-901`](../decisions/index-dossiers-europeens-901.md).

## Deux dates qui ne veulent pas dire ce qu'on croit

**44 dates d'amendement sont impossibles** — année 0302, année 2068 — sur les 20 937 mesurés le
09/09/2026. Elles sont publiées `null` avec leur valeur brute à côté, jamais corrigées en
silence.

**La datation ParlTrack au 22/11/2016** touche les interventions et textes européens : c'est le
jour de republication du dump, pas celui de la séance. Suivi par #858, non résolu.

## `data.europarl.europa.eu/api/v2/documents/{id}` — ce que la réponse porte, et comment elle se refuse

Mesuré le 16/09/2026 (#901), sur 20 documents `doceo` tirés au hasard parmi les résolutions
sans dossier, puis confirmé sur `RC-9-2024-0227` :

| Champ | Présent | Ce qu'il porte |
| --- | --- | --- |
| `data.title_dcterms` | 20 / 20 | le titre en **22 à 23 langues** — `fr` sur 20, `en` sur 19. C'est la version officielle, pas une traduction |
| `data.is_about` | 20 / 20 | 2 à 9 URI **EuroVoc** (`http://eurovoc.europa.eu/2155`) ; les libellés se résolvent ailleurs (`docs/sources/eurovoc.md`) |
| `data.isAboutSubjectMatter` | 0 / 20 | codes lisibles (`PESC`…), seulement sur les documents récents : inutilisable comme axe |

**`data` arrive en objet OU en liste d'un élément** : les deux se rencontrent. Un lecteur qui n'en
connaît qu'une forme rend `None` sur l'autre sans erreur.

**Le site public `www.europarl.europa.eu/doceo/…` ne se lit pas** : `HTTP 202`, zéro octet, défi
anti-robot, pour une adresse vraie comme pour une inventée (#827). Tout passe par le portail.

**Le portail ne refuse pas toujours poliment.** En #827, au-delà du débit toléré, il répondait
`HTTP 429` + `Retry-After: 60`. Le 16/09/2026, après une trentaine de requêtes de mesure
enchaînées en quelques minutes, `/documents/{id}` est devenu **muet** — 30 s puis timeout,
trois essais —, alors que `/api/v2/` et `/meps` répondaient encore depuis la même machine, et
que la même URL servie depuis un autre réseau rendait 200. Diagnostic : une limitation qui
visait **notre adresse, sur cette ressource**. Deux conséquences dans le code : un disjoncteur
après cinq silences (`MAX_ECHECS_CONSECUTIFS`), et aucune mesure en boucle depuis la machine
de développement — vérifier un document isolé passe par un autre réseau.

## Ce que ces sources ne portent pas

- **Le `sort` d'un amendement** — aucun champ, dans aucun dump.
- **Le sort d'un dossier** — `procedure` porte l'avancement, pas l'issue. `sort_non_resolu`
  vaut `source_sans_sort` sur tous les textes portés européens.
- **Un rang entre les stades** : les 16 valeurs de `stage_reached` décrivent des **états**, pas
  des degrés. « Procedure completed » et « Awaiting committee decision » ne s'ordonnent pas, et
  « Procedure completed » recouvre l'adoption comme l'échec — « Procedure rejected » est une
  procédure achevée elle aussi.
