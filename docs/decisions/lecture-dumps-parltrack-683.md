# Le lecteur des dumps ParlTrack n'avait jamais lu une ligne (#683, lot 1)

`2026-09-09`

> **En bref** — `iter_ndjson_zst` lisait en **NDJSON** des dumps que ParlTrack publie en **un seul tableau JSON, séparateur en tête de ligne** (`[{…}`, puis `,{…}`, puis `]`), format que la page /dumps décrit en toutes lettres depuis toujours ; `json.loads` échouait sur chaque ligne et l'échec partait dans un `except JSONDecodeError: continue`, si bien que **les 7 candidats déclarés à mandat européen publiaient « ParlTrack : aucune donnée trouvée » sur eux** — une panne présentée au lecteur comme un constat (§2 règle 5, patron de #484/#510) ; **la preuve dormait sur disque** — `.cache/parltrack/index_*.json` à **2 octets** (`{}`) en face de 182 Mio téléchargés à chaque run depuis un an — et **la suite était verte**, ses 27 fixtures étant écrites dans le format que le code imaginait (#726) ; d'où quatre choses et non une : `iter_dump_zst` au format publié, et surtout **`DumpParltrackIllisible`**, levée quand un dump porteur de lignes ne rend aucun enregistrement — le compteur porte sur les lignes et non sur la taille, un `[]` compressé pesant 12 octets non nuls, défaut trouvé par les tests du lot ; **un périmètre d'indexation obligatoire**, parce que réparer sans borner écrivait **2 675 293 entrées, ~0,5 Go** dans le cache téléversé à chaque run (le défaut ne s'en apercevait pas, l'index sortait vide donc gratuit), avec l'empreinte du périmètre **dans le nom du fichier** (#505) et `_perimetre()` qui rend l'**union** — jamais un index plus étroit que demandé (#510) ; **`role_signataire` cessé d'être `auteur_principal` pour tout le monde** — l'amendement `A9-0183/2023-18` de Bardella compte **30 signataires**, médiane 3, maximum 127 — et se lit désormais en trois cas, le quatrième restant **`null`** puisque l'ordre de `meps` ne reproduit celui d'`authors` que dans **91 %** des 1 257 735 amendements vérifiables ; **44 dates impossibles** (an 0302, an 2068) publiées `null` + `date_non_resolue` ; **deux dumps de plus** (`ep_votes`, `ep_mep_activities`, +58 Mio), liste centralisée dans `DUMPS_LUS` et lue par le YAML au lieu d'y être recopiée. Effet mesuré sur les dumps publiés, 78 s pour les sept : **7 828 amendements** et 12 textes portés, chiffres qui reproduisent exactement ceux de l'investigation du 04/08/2026 ; les deux nouveaux lecteurs rendent **100 017 positions de vote** en 36 s. **Deux chiffres annoncés le 09/09 sont corrigés** : la répartition des 21 356 signatures est de 7 828 déclarés / 13 528 roster, et non 10 013 / 11 343. Ne stocke ni votes ni activités — l'emplacement se décide après la maquette de fiche. Suite complète à 4 330, 0 échec.

## Contexte

Sept candidats déclarés ont un identifiant de député européen. Leur profil
publiait **zéro amendement, zéro texte porté**, et cet avertissement, destiné au
**lecteur** :

> ParlTrack : aucune donnée trouvée pour le député européen (identifiant
> ParlTrack 131580) dans les dumps publiés sur parltrack.org/dumps.

C'était faux, et c'était nous. `iter_ndjson_zst` lisait les dumps comme du
**NDJSON** — un objet JSON complet par ligne. ParlTrack publie **un seul tableau
JSON**, un objet par ligne, le séparateur en **tête** : la première ligne
commence par `[`, les suivantes par `,`, la dernière est `]`. `json.loads`
échouait donc sur chaque ligne, et l'échec partait dans un
`except json.JSONDecodeError: continue`.

La page https://parltrack.org/dumps le décrit en toutes lettres, et depuis
toujours :

> you can read the uncompressed JSON line-by-line, **strip of the first
> character** and process the rest of the line as JSON, you can stop processing
> if after stripping the first character an empty string remains, this means the
> end of the JSON stream.

**Ce qui l'a rendu invisible** : la panne ne pouvait pas rougir. Un dump
illisible rendait un index vide, un index vide rendait une liste vide, et une
liste vide se publiait comme un constat sur la personne — le patron exact de
#484 et #510. La preuve était sur disque et personne ne l'a regardée :
`.cache/parltrack/index_amendements_par_mep.json` et
`index_dossiers_rapporteur.json` faisaient **2 octets** — `{}` — en face de
182 Mio de dumps téléchargés à chaque run depuis un an.

**Et la suite de tests était verte.** Les 27 tests de `test_parltrack_dumps.py`
écrivaient leurs fixtures en NDJSON, c'est-à-dire dans le format que le code
imaginait. « Une fixture qui décrit le monde tel que le code l'imagine ne peut
pas révéler que le monde a bougé » (#726) — ici elle ne pouvait même pas révéler
qu'il n'avait jamais été ainsi.

## Décision

### 1. Lire le format publié, et refuser de rendre vide un dump plein

`iter_dump_zst` retire le premier caractère et s'arrête sur `]` — les deux
formes que la source décrit, `]` seul en fin de tableau et `[]` pour un dump
légitimement vide. Le `continue` sur ligne illisible est conservé : une ligne
tronquée ne doit pas perdre le dump entier.

Il ne suffit pas, et c'est le vrai correctif : **`DumpParltrackIllisible`** est
levée par `_lire_dump` quand un dump **porteur de lignes** ne rend **aucun**
enregistrement. C'est la seule chose qui sépare « ParlTrack ne connaît pas cette
personne » de « nous ne savons plus lire le fichier ». Le compteur porte sur les
lignes d'enregistrement et non sur la taille du fichier : un `[]` compressé pèse
12 octets non nuls, et une garde par la taille aurait fait échouer un dump vide
légitime — défaut trouvé par les tests du lot, pas par relecture.

### 2. Borner l'index à un périmètre, sinon le correctif coûte un demi-giga

Mesuré le 09/09/2026 sur les dumps publiés : indexer les amendements de **tous**
les eurodéputés produit **2 675 293 entrées**, soit **~0,5 Go de JSON** écrits
dans `.cache/parltrack/`, mis en cache par le workflow et téléversés en artifact
à chaque run. Le défaut d'origine ne s'en apercevait pas — l'index sortait vide,
donc gratuit.

Les indexeurs prennent donc un `perimetre`, et **le nom du fichier d'index porte
l'empreinte du périmètre** (même geste qu'au #505). Un index construit pour une
personne et relu pour sept rendrait six listes vides, et six listes vides se
lisent comme six constats (#510) : l'empreinte fait rater le cache au lieu de le
laisser mentir. Pour la même raison, `_perimetre(mep_id)` rend l'**union** du
périmètre défini et de la personne demandée — jamais un index plus étroit que ce
qu'on lui demande.

**Coût mesuré, et assumé pour l'instant** : sans `definir_perimetre_meps`, chaque
personne fait reconstruire son index, **49 s** — soit ~5 min 45 pour les sept,
contre **78 s** quand le périmètre est posé une fois. Le point d'accroche existe
(`definir_perimetre_meps`) mais rien ne l'appelle : le poser demanderait une
passe préalable sur `raw_data/profiles/` pour y lire les
`mandat_europeen.identifiant_pe`, ce que le lot de stockage fera à l'endroit où
il connaîtra les sept sans les relire.

### 3. Deux dumps de plus, et une seule définition de la liste

ParlTrack publie **huit** dumps ; ce module en lisait trois et en lit **cinq** :
`ep_votes` (scrutins nominatifs) et `ep_mep_activities` (interventions,
questions, explications de vote, propositions de résolution) entrent. +58 Mio sur
les 182 déjà téléchargés ; `extract-parltrack` garde très largement ses 30
minutes.

La liste vit dans le module (`DUMPS_LUS`) et le YAML la lit. Recopiée, elle
aurait divergé du jour où un sixième dump entre — et un dump absent ne fait pas
échouer la lecture, il rend un index vide.

Les trois autres restent dehors, chacun pour une raison mesurée : `ep_meps` fait
doublon avec le portail officiel du PE, d'où le pipeline tire déjà identité et
mandats ; `ep_com_votes` porte **89 scrutins en tout** ; `ep_comagendas` ne nomme
personne.

### 4. Le rôle de signataire se lit, il ne se suppose pas

Le module écrivait `auteur_principal` sur **chaque** amendement. C'est faux et
mesurablement : l'amendement `A9-0183/2023-18` de Jordan Bardella compte **30
signataires**, et la médiane sur nos profils européens est de **3**, le maximum
de **127**. Personne ne s'en apercevait — aucune entrée n'était produite.

`_role_signataire` tranche en trois cas et se tait dans un quatrième :

| Cas | Rôle |
| --- | --- |
| un seul signataire | `auteur_principal` — sans lire un nom |
| le nom en tête d'`authors` est le sien | `auteur_principal` |
| la source nomme quelqu'un d'autre en tête | `cosignataire` |
| `authors` absent ou illisible | **`null`** |

Le quatrième cas est le seul honnête. L'ordre de `meps` reproduit celui
d'`authors` dans **91 %** des 1 257 735 amendements vérifiables — trop pour
l'ignorer, beaucoup trop peu pour en faire une règle (8 270 discordants,
97 459 noms non résolus).

**Une phrase de la docstring était fausse et est corrigée** : « ParlTrack ne
fournit pas les cosignataires ». Chaque amendement porte la liste complète de ses
signataires (`meps`) et leurs noms dans l'ordre (`authors`) — c'est exactement ce
qui rend ce champ calculable.

### 5. Quarante-quatre dates impossibles

Sur les 20 937 amendements des profils européens, **44** portent une date que
rien ne peut expliquer : `PE650.371-2` est daté de l'an **0302**,
`PE640.014-47` de **2068**. Republiée telle quelle, elle range un amendement de
2020 dans un siècle qui n'existe pas ; corrigée en silence, elle invente. Elle
est donc publiée `null`, avec la valeur brute conservée à côté sous
`date_non_resolue: {motif, valeur_source}` — la forme que le dépôt emploie déjà
partout pour une clé qu'on ne sait pas résoudre (§2 règle 5).

Borne basse : **1979**, première élection du Parlement européen au suffrage
universel. Borne haute : l'année suivante, pour ne pas rejeter un dépôt
légitimement postérieur au dump.

### 6. Les bornes de fraîcheur sont des données, pas un détail d'exploitation

Les cinq dumps ne sont pas régénérés au même rythme, et l'écart est publiable :

| Dump | Dernière mise à jour | Ce qu'il borne |
| --- | --- | --- |
| `ep_dossiers`, `ep_plenary_amendments`, `ep_mep_activities` | 24/07/2026 | — |
| `ep_votes` | **28/03/2026** | dernier scrutin porté : **26/03/2026** |
| `ep_amendments` (commission) | **03/02/2026** | l'essentiel des amendements |

Ces bornes devront se retrouver dans `couverture.votes` et
`couverture.amendements` au lot de stockage. La propriétaire a tranché le
09/09/2026 : on les accepte et on les écrit, plutôt que d'ajouter HowTheyVote
pour la fenêtre récente — cette source ne publie que **2 421** scrutins à partir
du 18/07/2019, contre 44 648 depuis 2004, et aucun des sept n'est en exercice.

## Effet mesuré

Enrichissement réel des sept profils déclarés, sur les dumps publiés, périmètre
posé : **78 s**.

| Candidat | Amendements | dont auteur principal | dont cosignataire | Textes portés |
| --- | ---: | ---: | ---: | ---: |
| Emmanuel Maurel | 3 991 | 2 609 | 1 382 | 8 |
| Raphaël Glucksmann | 2 544 | 590 | 1 954 | 4 |
| Jordan Bardella | 525 | 163 | 362 | 0 |
| Marine Le Pen | 342 | 272 | 70 | 0 |
| Florian Philippot | 175 | 11 | 164 | 0 |
| Jean-Luc Mélenchon | 154 | 137 | 17 | 0 |
| Lydie Massard | 97 | 71 | 26 | 0 |

Ces chiffres reproduisent **exactement** ceux de
[`investigation-sources-ue`](investigation-sources-ue.md) du 04/08/2026 sur son
échantillon de trois (Bardella 15 + 510 = 525, Le Pen 342, Mélenchon 154) — ce
qui confirme que l'investigation avait bien lu les dumps, avec du code qui n'est
pas celui qui a été livré.

Les deux nouveaux lecteurs, mesurés sur les mêmes sept, **36 s** : **100 017**
positions de vote (Maurel 27 987, Glucksmann 21 817, Bardella 20 635, Le Pen
10 670, Philippot 8 470, Mélenchon 7 823, Massard 2 615), et côté activités
2 158 interventions en séance pour Mélenchon, 766 explications de vote pour
Philippot, 63 rapports pour Maurel.

**Deux chiffres annoncés à la propriétaire le 09/09 étaient faux et sont
corrigés ici** : la répartition des 21 356 signatures entre les deux populations.
Les 7 candidats déclarés en portent **7 828** et non 10 013 ; les 15 membres de
roster **13 528** et non 11 343. Le total et la décision de périmètre ne
changent pas.

## Ce que ce lot ne fait pas

- **Il ne stocke ni les votes ni les activités.** Les deux lecteurs existent et
  sont testés ; où ces données vivent dans le pivot, et sous quelle forme, se
  décide après que la propriétaire a vu une fiche — c'est l'étape 3 du plan
  arrêté le 09/09.
- **Il ne touche pas les 15 membres de roster** qui ont un identifiant européen.
  Le périmètre arrêté est celui des **7 candidats déclarés**. Leur cas est une
  décision de périmètre distincte, qui porte sur les agrégats de groupe.
- **Il ne pose pas les bornes de couverture** (§6 ci-dessus) : elles appartiennent
  au lot de stockage, avec `couverture_profil.deriver()`.
- **Il ne wire pas `definir_perimetre_meps`** : 5 min 45 par run, mesurées, contre
  une passe préalable sur `raw_data/profiles/` qui n'a pas sa place ici.

## Alternative écartée

**Réparer le lecteur sans la garde `DumpParltrackIllisible`.** C'est le correctif
d'une ligne, et il aurait suffi aujourd'hui. Il laisse intacte la seule chose qui
a permis à la panne de durer un an : rien, dans le pipeline, ne distinguait un
dump illisible d'un député sans activité. Le jour où ParlTrack change son format
— il l'a déjà fait, passant de `lzip` à `zstd` le 11/11/2024 —, les sept fiches
redeviendraient vides en silence, et l'avertissement au lecteur redirait « aucune
donnée trouvée » sur des gens qui ont déposé 7 828 amendements.
