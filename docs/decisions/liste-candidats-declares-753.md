# La liste des candidats se collecte, et un déclaré entre sans slug (#753)

`2026-09-07`

> **En bref** — `raw_data/candidats.json` décide de **qui reçoit une fiche** (il dimensionne la matrice `extract-an` et porte la première passe pivot) et il était tenu à la main, `derniere_verification` à **51 jours** ; mesuré le 07/09/2026 : **30 déclarés** en ligne (19 au tableau principal, 11 en primaire) contre **13** chez nous, donc **19 absents** et **2 entrées périmées** — Wauquiez (`declare`) et Bardella (`pressenti`) sont tous deux sous « Candidats pressentis ayant décliné » ; le garde-fou censé le voir, `fetch_wikipedia_candidates.py`, n'était appelé par **aucun workflow**, n'avait **aucun test**, rendait 13 « candidats » dont **aucun n'était une personne** (« nationalité française », « droits civiques ») et **sortait en 0 sur un échec réseau total** — le patron de #511 ; trois défauts indépendants : mauvais article (la liste vit dans « Candidatures à… », l'article de l'élection ne fait que la transclure), regex de titre attrapant « **Conditions de candidature** », et requête Wikidata imposant une classe d'élection (`Q869519`) que `Q111594692` ne porte pas ; le remplaçant lit le **HTML rendu** parce que les primaires sont transcluses (`{{#section-h:}}`) et qu'un wikitext perd Mélenchon, Tondelier, Guedj et Royal — quatre personnes déjà publiées —, lit le nom dans le **texte** de la cellule et jamais dans son premier lien (Selma Labib et Benoît Mathieu n'ont pas d'article, leur premier lien est celui du **parti**), et retire trois parasites d'empilement `<br>` (clé de tri `{{TriNom}}`, `datasortkey`, `sup.reference`) ; **trois anomalies bloquent l'écriture** (page illisible, section introuvable, zéro candidat) et aucune n'est un seuil, une ligne illisible étant comptée et nommée comme `ROSTER_SANS_SLUG` (#527) tandis qu'un en-tête de colonnes se reconnaît à sa **structure** (que des `th`) et non à son libellé ; le point qui décide de tout : un nouveau candidat entre avec **`slug: null`**, ce qui le tient hors de `prepare-an-matrix` donc hors publication donc hors du hard fail §5b (#525) — **le blocage de #715 était un défaut et il est réparé** (`70626a02`, 02/09/2026, a bien committé les 160 profils et leurs entrées `origine: derivee`), mais son correctif est **borné à sa population** : `slugs_fabriques()` ne lit que `rosters_bruts.json`, or `groupes_reels.json` ne configure que **5 groupes par législature** (ni Écologistes, ni GDR, ni LIOT, ni MoDem, ni Horizons), d'où **3** des 19 déjà collectés comme membres de roster et **16** qu'aucune passe dérivée ne rattraperait — et l'étendre serait **faux**, le slug d'un candidat sortant de `slugify(nom)` et non de son acteur, donc un **rapprochement** à relire (#525, #715 §2) ; une entrée qui n'est plus déclarée est **signalée, jamais modifiée** (la section lue ne distingue pas un retrait d'un déplacement) ; Wikidata sort du dispositif (`P3602` rend **1** personne sur 30) et l'adaptateur officiel n'est pas écrit — `data.gouv.fr` rend **0** jeu 2027, le CC publie 2017 et 2022 sous `other-pd` et la liste passera par trois régimes (déclaratif → parrainages → officiel) ; **`decline` entre dans `statuts_possibles`** — le fichier n'avait aucune valeur pour dire qu'une candidature est abandonnée, d'où 51 jours de `declare` faux —, l'entrée étant **conservée** (son slug est publié, #460/#470) et la valeur n'étant **jamais posée par le script** ; coût **nul aujourd'hui** (19 entrées sans slug, `prepare-an-matrix` en retient toujours 13 ; référence : run `34053322456`, 13 shards, **606 s cumulés**, 27 à 69 s, moyenne 46,6 s) et **dissymétrique demain** : 3 des 19 sont déjà collectés comme membres de roster (Ruffin, Brun, Faure — le slug ne fait que basculer `provenance`), 16 sont à collecter de zéro, soit +19 shards **en série** (`max-parallel: 1`, seuil d'avertissement de 16 franchi) ≈ **+15 min** de chemin critique, plafond dur 19 × 5 min = **+95 min** ; côté dépôt (9,0 Go de `raw_data/profiles`, pack git **2,95 Gio**, médiane roster **10,8 Mo**), les bornes sont **0 à ~173 Mo bruts** selon combien des 16 ont une carrière AN — ce que dira la table de correspondance, et ce lot charge un peu plus **#678** et **#691** ; effet de bord **déclaré et non corrigé** : `parti_profile.py` créera 19 fiches de parti à `nb_candidats_avec_pivot: 0`. 24 tests sur une capture réelle réduite aux quatre formes qui cassent une extraction naïve, dont trois qui confrontent le fichier réel à sa propre liste de statuts.

## Contexte

`raw_data/candidats.json` décide de **qui reçoit une fiche** : il dimensionne la
matrice `extract-an` (un shard par candidat à slug résolvable) et porte la
première passe pivot de `merge-and-pivot`. Il était tenu **à la main**, et sa
`_meta.derniere_verification` valait `2026-07-18` — **51 jours** au 07/09/2026.

Mesuré ce jour-là contre l'article Wikipédia des candidatures :

| Population | Nombre |
| --- | --- |
| « Candidats déclarés », tableau principal | **19** |
| Déclarés dans le cadre d'une primaire (gauche unitaire, PS, autres) | **11** |
| `raw_data/candidats.json` | **13**, dont **11** communs |
| **Déclarés absents de notre fichier** | **19** |
| **Entrées de notre fichier qui ne sont plus déclarées** | **2** |

Les deux entrées périmées sont sourcées : **Laurent Wauquiez** (`statut:
declare`) et **Jordan Bardella** (`statut: pressenti`) figurent tous deux sous
« Candidats pressentis ayant décliné », le premier en soutien à Bruno
Retailleau, le second à Marine Le Pen.

### Le garde-fou existait, et il ne gardait rien

`src/fetch_wikipedia_candidates.py` (356 lignes) n'était appelé par **aucun
workflow**, n'avait **aucun test** ni fichier de décision. Exécuté le
07/09/2026, il rapportait 13 « candidats », dont **aucun n'était une personne** :
« nationalité française », « droits civiques », « parrainages », « Conseil
constitutionnel ». Trois défauts indépendants, tous vérifiés :

1. **il visait le mauvais article.** La liste ne vit pas dans « Élection
   présidentielle française de 2027 », qui ne fait que la transclure, mais dans
   « Candidatures à l'élection présidentielle française de 2027 » ;
2. **sa regex de titre attrapait « Conditions de candidature »** — un titre qui
   contient « candidat » — et en ramassait les puces ;
3. **sa requête Wikidata ne pouvait pas aboutir** : elle imposait
   `?election wdt:P31 wd:Q869519`, quand l'élément de l'élection 2027
   (`Q111594692`) porte `Q890055` et `Q114775014`.

Et **il sortait en 0 sur un échec réseau total**, en affichant « ✓ Aucun nouveau
candidat détecté en ligne » : une collecte vide rendue comme un résultat, le
patron exact de #511.

## Décision

Un script neuf, `src/fetch_candidats_declares.py`, qui **collecte les déclarés
et écrit** `raw_data/candidats.json`. L'ancien est retiré.

### Le périmètre : tout candidat déclaré, sans filtre

« A déclaré sa candidature » est un fait, sourçable ligne à ligne. Tout autre
critère — notoriété, score attendu, taille du parti — reviendrait à arbitrer qui
mérite une fiche, ce que la §2 règle 1 interdit. Les sous-sections de primaire
sont dedans : la source en fait des sous-sections de « Candidats déclarés ».

### Le HTML rendu, et non le wikitext

Les primaires sont **transcluses** (`{{#section-h:}}`) depuis d'autres articles.
Lire le wikitext du seul article dédié perd Mélenchon, Tondelier, Guedj et
Royal — quatre personnes que nous publions déjà. `action=parse&prop=text`
développe les transclusions ; c'est la seule raison pour laquelle ce script
parle HTML.

### Le nom se lit dans le texte de la cellule, jamais dans son premier lien

Deux déclarés n'ont pas d'article Wikipédia — **Selma Labib**, **Benoît
Mathieu** — et leur premier lien est donc celui du parti. Une extraction par
lien publie « Nouveau Parti anticapitaliste » comme nom de candidate. La cellule
d'en-tête est un empilement `<br>` (nom, âge, parti) dont trois parasites sont
retirés avant lecture : la clé de tri de `{{TriNom}}`
(`<span style="display:none">`), l'âge (`<span class="datasortkey">`) et les
appels de note (`<sup class="reference">`, trois sur la seule ligne Fabien
Roussel).

### Trois anomalies bloquent l'écriture, aucune n'est un seuil

Le patron de `generate_roster_candidats.py`, pour la raison de #511 :

1. **la page n'a pas pu être lue** — réseau, HTTP, JSON illisible, erreur d'API.
   L'exception voyage jusqu'au message (#524) : « en échec » ne dit pas s'il faut
   relancer ou corriger le code ;
2. **la section « Candidats déclarés » est introuvable** — un titre qui bouge ne
   doit pas se lire comme une liste vide ;
3. **zéro candidat extrait** alors que la section existe.

Une ligne dont le nom ne se laisse pas lire ne bloque **pas** : elle est comptée
et nommée (`CANDIDATS_LIGNE_ILLISIBLE`), comme `ROSTER_SANS_SLUG` le fait des
membres sans slug (#527). Une ligne **d'en-tête de colonnes** n'en est pas une :
elle se reconnaît à sa structure (que des `th`, aucun `td`) et non à son libellé,
ce qui évite quatre avertissements par run — un avertissement qu'on apprend à
ignorer est un avertissement perdu.

### Un nouveau candidat entre avec `slug: null`

C'est le point qui décide de tout le reste. Fabriquer le slug ferait entrer le
candidat dans la matrice `extract-an`, donc dans la collecte, donc dans la
publication — et la **§5b du portail qualité est un hard fail à seuil 0** sur
tout profil publié sans correspondance slug ↔ acteur AN relue (#525).

**Ce blocage a déjà été levé une fois, et pas pour cette population.** #715 a
traité l'incident du run `33613535746` — 160 profils collectés, commit refusé —
et ses profils **ont bien été committés** après correctif : `70626a02`, le
02/09/2026, ajoute 160 profils pivot et les 160 entrées `origine: derivee` que
porte la table aujourd'hui (641 entrées, dont 481 sans clé `origine`, d'avant le
lot). L'incident était un défaut, il est réparé, et il ne doit pas servir
d'épouvantail.

Le correctif est **borné à sa population**, et de deux façons.
`build_correspondance_acteurs_an.slugs_fabriques()` lit
`raw_data/rosters_bruts.json` et rien d'autre, et le step de CI est conditionné
à `hashFiles('raw_data/rosters_bruts.json')`. Or `raw_data/groupes_reels.json`
ne configure que **cinq groupes par législature** — REN/EPR, SOC, RN, LFI,
LR/DR : ni Écologistes, ni GDR, ni LIOT, ni MoDem, ni Horizons. C'est pourquoi
**3** des 19 entrées neuves ont déjà un profil (Ruffin, Brun, Faure, membres de
roster) et **16** n'en ont aucun : aucune des seize n'entrerait dans la passe
dérivée, et chacune bloquerait la §5b.

Et ce n'est pas qu'une affaire d'implémentation : **l'étendre serait faux.**
#715 §2 tranche que l'entrée dérivée n'établit rien parce que le slug d'un
membre de roster **sort de son acteur AMO30**. Le slug d'un candidat, lui, sort
de `slugify(nom)` — un nom tapé à la main dans un fichier éditorial. Établir
quel `PA######` lui correspond reste un **rapprochement**, c'est-à-dire
exactement ce que #525 exige de relire.

`slug: null` est exactement l'inverse : `prepare-an-matrix` ne retient que les
slugs résolvables, donc pas de shard, pas de collecte, pas de publication, pas
de §5b. La relectrice mint le slug **quand** elle a vérifié la correspondance.
L'état d'attente n'est pas une invention de ce lot : c'est la sémantique que le
pipeline porte déjà.

`famille_politique` et `date_declaration` restent `null` : le tableau des
déclarés ne les porte pas, et une absence se publie en absence (§2 règle 5).

### Une entrée qui n'est plus déclarée est signalée, jamais modifiée

Le script lit la **section des déclarés**. Il ne peut donc pas distinguer un
retrait d'une candidature déclinée ni d'un simple déplacement de section :
trancher à sa place serait inventer une cause. Il annote (`::warning::`), il
n'écrit pas. Et il ne supprime jamais — un `slug` publié est immuable
(#460/#470).

### `decline` entre dans `statuts_possibles`, et l'entrée est conservée

Wauquiez et Bardella avaient décliné, et le fichier n'avait **aucune valeur pour
le dire** : `statuts_possibles` ne portait que `declare`, `pressenti` et
`officiel`. Ils sont donc restés `declare` et `pressenti` pendant 51 jours,
c'est-à-dire faux.

`decline` nomme une candidature explicitement abandonnée par une personne que
nous portions comme déclarée ou pressentie. **L'entrée est conservée, jamais
supprimée** : son slug est publié, et retirer un fichier publié est une
disparition qu'`audit_diff_profils` bloque (#460/#470). Le champ reste
descriptif — où en est la candidature — et jamais un jugement sur elle
(§2 règle 1).

**Le script ne pose jamais cette valeur.** Il ne lit que la section des
déclarés, où l'absence d'une personne ne distingue pas un retrait d'un
déplacement de section : il signale, un humain tranche avec sa source. C'est la
même frontière que partout ailleurs dans le dépôt — une cause non résolue se
déclare, elle ne se devine pas (§2 règle 5).

Conséquence à connaître : `generate_all_profiles` dérive
`meta.provenance = "candidat_declare"` de **tout** statut autre que
`roster_groupe`. Une entrée `decline` reste donc un profil publié, et sa fiche
reste en ligne. Si elle ne doit plus l'être, c'est une décision éditoriale
distincte, et elle n'est pas prise ici.

Une contrainte que rien ne tenait devient un test :
`test_tout_statut_publie_est_dans_statuts_possibles` confronte le fichier à sa
propre liste de valeurs, ce que personne ne faisait.

## Le coût, mesuré

**Aujourd'hui, il est nul.** Les 19 entrées neuves sont sans slug :
`prepare-an-matrix` en retient toujours **13**, et le run du 06/09/2026
(`34053322456`) reste la référence — 13 shards, **606 s cumulés**, de 27 s
(Bardella) à 69 s (Mélenchon), moyenne **46,6 s**.

**Le coût arrive quand les slugs seront écrits**, un par un, et il est
dissymétrique :

| | Nombre | Ce que ça coûte |
| --- | --- | --- |
| Déjà collectés comme membres de roster (Ruffin, Brun, Faure) | **3** | **rien de neuf** — le profil brut est déjà versionné ; le slug ne fait que basculer `meta.provenance` |
| À collecter de zéro | **16** | un shard `extract-an` chacun, et un profil brut de plus |

**CI.** `extract-an` est en `max-parallel: 1` : les shards s'exécutent **en
série**, et chacun paie ses propres frais fixes de `actions/checkout`. À 32
shards, `prepare-an-matrix` franchit son seuil d'avertissement de 16 (#498).
Dans le régime observé, +19 shards ≈ **+15 min** de chemin critique ; le
plafond dur est 19 × `timeout-minutes: 5` = **+95 min** (et le double si
`collect_interventions` est coché, le timeout passant à 10). Les 606 s mesurés
le sont sur un `existing_profiles=refresh` de profils **déjà collectés** : une
première collecte est plus chère, et c'est précisément ce qu'un slug neuf
déclenche.

**Dépôt.** L'arbre porte **9,0 Go** de `raw_data/profiles` et 947 Mo de
`pivot_data/profiles`, pour un pack git de **2,95 Gio**. Les 13 candidats
déclarés pèsent 92,3 Mo bruts (Le Pen 25,6 ; cinq à 0, faute de mandat AN) ; les
628 membres de roster, 9 470,9 Mo, **médiane 10,8 Mo**, p90 34,5, max 61,3.

Le coût des 16 dépend donc entièrement de **combien ont une carrière à
l'Assemblée**, ce que dira la table de correspondance au moment où elle sera
écrite — c'est la même relecture humaine qui débloque le slug. Les bornes :
**0 Mo** si aucun n'est passé par l'AN (le cas des cinq déclarés déjà à zéro),
**~173 Mo bruts** si les seize l'étaient tous, à la médiane du roster. Le pivot
en représente 10 à 30 % selon la part d'amendements.

Deux issues ouvertes portent ce terrain et ce lot les charge un peu plus :
**#678** (le poids total du dépôt n'est surveillé par personne) et **#691** (les
tranches d'amendements recopient 4,58 Gio déjà versionnés en 38 Mo pour les
législatures 14/15/16). Tant que #691 n'a pas atterri, chaque nouveau profil à
carrière AN paie cette duplication.

## Ce que la décision ne fait pas

**Wikidata sort du dispositif.** Corrigée de sa classe d'élection, la requête
`?p wdt:P3602 wd:Q111594692` rend **1** personne (Clara Egger), absente de notre
fichier : la propriété n'est pas peuplée pour 2027. Une source qui rend 1 sur 30
n'est pas une source de repli, c'est un faux témoin.

**La liste officielle n'existe pas encore, et ce lot ne la prépare pas.** Le
Conseil constitutionnel est seul compétent et n'émet rien avant l'ouverture du
recueil des présentations. `data.gouv.fr` rendait **0** jeu de données
« présidentielle 2027 » au 07/09/2026 ; le CC y publie bien 2017 et 2022
(organisation « Conseil constitutionnel », licence `other-pd`, JSON/CSV/XLSX,
rafraîchis 2×/semaine pendant le recueil), puis la décision « PDR » arrêtant la
liste au JO — précédent 2022 : décision n° 2022-187 PDR du 7 mars 2022. La liste
passe donc par **trois régimes** — déclaratif (aujourd'hui), parrainages
(~janv-févr 2027), officiel (~mars 2027) — et `statut` porte déjà les trois
valeurs. Écrire aujourd'hui l'adaptateur officiel serait écrire contre une forme
que personne n'a vue : c'est ce que #726 nomme *une fixture qui décrit le monde
tel que le code l'imagine*.

**Le script n'est branché dans aucun workflow.** Il s'exécute à la main, et
`--echouer-si-ecart` existe pour le jour où un job le lancera en tête de run.
Le brancher demande d'abord de trancher où la mise à jour est **commitée** : le
garde-fou `GENERATION_CODE_CHANGED_DURING_RUN` de `merge-and-pivot` annule le
commit si `raw_data/*.json` a bougé sur la branche pendant le run.

**Un effet de bord est déclaré et non corrigé** : `parti_profile.py` groupe
**toutes** les entrées de `candidats.json` par leur champ `parti` et écrit un
`pivot_data/partis/parti-<slug>.json` par label. Les 19 entrées neuves y
créeront donc des fiches de parti à `nb_candidats_avec_pivot: 0` — un compteur
déclaré, sur une sortie qu'aucun onglet de `web/UI_finale` n'affiche.

## Alternative écartée

**Réparer `fetch_wikipedia_candidates.py`.** Les trois défauts sont
indépendants et touchent la cible, l'extraction et la requête — c'est-à-dire
tout le fichier sauf son CLI. Et son contrat change : il promettait de **ne
jamais écrire**, ce que sa ligne de `docs/commandes.md` disait en gras. Garder
le nom d'un script qui fait l'inverse de ce qui est écrit de lui coûte plus
qu'un fichier neuf.

**Fabriquer le slug à l'entrée, comme #708 le fait pour les membres de
roster.** Là-bas, la passe dérivée de #715 rattrape le slug fabriqué dans le
même run et le commit passe — c'est mesuré, `70626a02` a committé les 160.
Ici, aucune des 16 entrées à collecter n'est dans un roster configuré, donc
aucune n'est rattrapée ; et l'y rattraper serait faire dire à une entrée dérivée
ce qu'elle ne dit pas, puisque le slug d'un candidat ne sort pas de son acteur.
