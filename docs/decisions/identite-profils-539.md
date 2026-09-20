<a id="identite-profils-539"></a>
# Comment naît l'identité d'un profil, et où vont les identifiants de source (#539) (2026-08-28)

`2026-08-28`

> **En bref** — comment naît l'identité d'un profil, et pourquoi les identifiants de source ne vivent plus dans l'`id`.

La question de l'issue était « comment naît un identifiant ». La réponse a été
cadrée par une mesure qui contredisait sa prémisse : **le slug n'était déjà
plus l'`id`.**

## Le constat qui a forcé le cadrage

| Forme de l'`id` | Profils |
| --- | ---: |
| `<slug>` — l'`id` vaut le nom de fichier | 456 |
| `nosdeputes:<slug>` | **19** |
| `europarl:131580` | **1** |

Vingt profils sur 476 portaient encore, dans leur identité, le nom d'une source.
Dix-neuf nomment une plateforme **retirée du pipeline par #529** ; le
vingtième, `jordan-bardella`, nomme le Parlement européen. #487 avait posé la
règle et migré ce qu'un run réécrit ; ces vingt-là ne sont plus régénérés —
les 19 sénateurs n'ont plus de source depuis #528, et Bardella repartait à
chaque run avec `europarl:131580` parce que `generate_all_profiles` appelait
`normalize_europarl` **sans lui passer le slug**.

Le contournement existait déjà, non écrit, à deux endroits :
`web/UI_finale/scripts/sync-data.mjs:106` et `src/group_profile.py:1400` font
tous deux `split(':')` pour retrouver le slug.

## La règle

**`id` == nom de fichier, sans préfixe de source, pour les 476.** L'identifiant
de source part dans un bloc `identifiants` où il est **nommé**, au lieu d'être
concaténé dans une identité.

Coût mesuré, et il est faible : `audit_diff_profils` classe `id` en
**scalaire**, où seule la régression renseigné → `null` bloque. Le contrôle
rejoué sur le corpus migré rend **20 changements de valeur d'un scalaire, non
bloquants, et rien d'autre** — 0 perte, 0 évolution sur les listes, sur les
cinq collections.

**Aucun fichier n'est renommé.** La régularisation porte sur le champ, jamais
sur un nom de fichier : renommer un fichier publié est une suppression, que le
même contrôle bloque (#460/#470).

L'identifiant opaque interne (`EP-000042`) a été écarté : il imposerait deux
clés dans toutes les jointures sans fermer la question côté interface, où le
permalien reste le slug.

## Les `membre_id` sont dans la même passe, ou dans aucune

`group_profile.py:286` recopie `membre_id` depuis l'`id` du profil : les deux
décrivent la même identité. Réécrire les `id` sans réécrire les `membre_id`
laisserait les fiches de groupe pointer sur des identités qui n'existent plus.

Mesuré : **19 `membre_id` préfixés, dans 2 fichiers** —
`groupe-Senat-LR.json` (14) et `groupe-Senat-SER.json` (5). Bardella n'est
membre d'aucun groupe publié, d'où 19 et non 20. La réécriture est **invisible**
au contrôle de perte : `membre_id` vit à l'intérieur d'une entrée de `membres[]`,
et le contrôle ne compare d'une liste que sa cardinalité.

## Le bloc `identifiants`

Quatre référentiels, quatre clés **toujours présentes**, toutes nullables. Une
clé absente laisserait un lecteur choisir entre « pas d'identifiant » et « le
producteur n'y a pas pensé » ; `null` dit la première chose et rien d'autre
(§2.5). Le bloc entier absent = profil publié avant ce lot.

| Clé | Source | Renseignée (sur 476) |
| --- | --- | ---: |
| `an` | `raw_data/correspondance_acteurs_an.json`, table committée et relue (#525) | **475** |
| `senat` | aucun référentiel établi depuis #528 | **0**, et c'est un fait déclaré |
| `europarl` | `mandat_europeen.identifiant_pe` | **12** |
| `hatvp` | recopie d'`identite.uri_hatvp` | **279** |

`uri_hatvp` **reste** dans `identite` : l'interface le lit là-bas, et le retirer
casserait des lecteurs pour un gain nul. Les deux valeurs sortent de la même
fabrique (`normalize_profil`) et `validate_profil` refuse qu'elles divergent.

**Le `PA` cesse d'être ré-résolu par correspondance de nom à chaque run : il est
publié.** C'est la moitié utile du bloc — la table le porte déjà, prouvé et
relu, et chaque consommateur le redérivait.

## La mesure qu'on n'attendait pas : 186 `uri_hatvp` qui n'en sont pas

En recopiant le champ, on a dû le regarder.

| Contenu de `identite.uri_hatvp` | Profils |
| --- | ---: |
| Une vraie URI `https://www.hatvp.fr/...` | **279** |
| `{"@xmlns:xsi": "...", "@xsi:nil": "true"}` — le marqueur XML brut d'AMO30 | **186** |
| Vide ou `identite` absente | 11 |

La mesure de « 465 profils portent `uri_hatvp` » qui circulait comptait les 186
comme renseignés. Ce sont des profils **sans déclaration HATVP**, dont le `null`
d'AMO30 a traversé la conversion XML→JSON sans être lu.

*(Re-mesure du 29/08/2026, sur 481 profils : **285** vraies URI, **191**
marqueurs, **0** `null`, 5 profils sans bloc `identite`. La nature du défaut n'a
pas changé, sa population a grandi. Il a été corrigé **à l'extraction** par
#556 — voir [#marqueur-nil-identite-556](absences-publiees-comme-faits-556-558-560.md#marqueur-nil-identite-556) —, qui a
aussi trouvé que le marqueur touchait `profession` et `lieu_naissance`, et que
la contrainte de `validate_profil` censée signaler la divergence la
**neutralisait**.)*

Deux décisions, et la seconde est celle qui coûte :

1. **`identifiants.hatvp` ne reçoit que les 279 vraies URI.** Un identifiant qui
   ne mène nulle part ne vaut pas mieux qu'une absence, il vaut moins (§2.2).
   `poser_identifiant` **lève** sur une valeur non-chaîne plutôt que de la
   sérialiser : un `str(valeur)` obligeant aurait publié cet objet comme
   identifiant HATVP sur 186 profils, et le schéma ne l'aurait pas rattrapé
   puisque la valeur serait devenue une chaîne.
2. **`identite.uri_hatvp` n'est pas réparé ici.** Le défaut est dans
   l'extraction d'identité, en amont, et sa correction réécrira 186 profils
   publiés — un lot à part, avec sa propre mesure avant/après. Ce lot le
   contourne et le nomme ; il ne le masque pas.

## La collision : suffixe numérique figé

`alexandra-martin` / `alexandra-martin-1`, la règle de fait, désormais écrite.
Le suffixe est attribué à la **première publication**, n'est jamais réattribué —
même si le profil qui le précède disparaît — et n'est **pas re-dérivable** depuis
l'état civil : il est committé dans la table, jamais recalculé.

La désambiguïsation par territoire a été écartée malgré son usage par l'AN
elle-même (« Alexandra Martin (Alpes-Maritimes) ») : une circonscription change
d'un mandat à l'autre, l'identifiant ne serait pas immuable.

## La fabrication vaut à la première publication SEULEMENT

| Mesure sur les 476 profils | Valeur |
| --- | ---: |
| Collisions si le slug est dérivé de l'état civil AN | **0** |
| Slugs publiés divergeant de `slugify(état civil)` | **7** — exactement les 7 `ecart` de la table |
| Slugs déjà suffixés | 1 (`alexandra-martin-1`) |

Conséquence : **la règle de fabrication ne doit jamais être rejouée sur un profil
publié.** Re-dériver depuis l'état civil renommerait ces 7 fichiers, et un
renommage est une suppression bloquante. Le suffixe numérique est une politique
**pour l'avenir** ; sur le corpus d'aujourd'hui elle ne se déclenche pas, et
c'est ce qui la rend sûre à poser maintenant.

## Les cinq candidats invisibles, et les trois cercles qui les enfermaient

Cinq candidats déclarés sur treize portaient `slug: null` dans
`raw_data/candidats.json` — Arthaud, Tondelier, Royal, Bertrand, Lisnard. La
règle qui produisait ce `null` était écrite dans le fichier lui-même : « slug =
identifiant nosdeputes.fr/nossenateurs.fr quand le candidat y est référencé,
sinon null ». Elle date d'avant #529, et depuis, elle ne décrit plus rien.

Ce `null` les enfermait à trois endroits, dont deux que l'issue n'avait pas
nommés :

| Où | Ce qui les écartait |
| --- | --- |
| `generate-data.yml:238` (`prepare-an-matrix`) | `if c.get("slug")` — **le vrai cercle fermé** : pas de slug, pas de shard, donc jamais de collecte |
| `web/UI_finale/scripts/sync-data.mjs:75` | `c.slug &&` dans le filtre du manifeste |
| `generate_all_profiles._select_existants` (#445) | ne retient que les candidats dont le profil brut existe **déjà** — mais il n'agit que sous `--refresh-existing`, donc il n'était pas la cause |

La règle de fabrication, elle, **existait déjà en code** et n'a jamais été le
blocage : `generate_all_profiles.py:301` définit
`_effective_slug(c) = c["slug"] or slugify(c["nom"])`. Elle n'était utilisée
qu'en lecture.

Les cinq slugs sont donc **fabriqués une fois et committés** dans
`candidats.json`, avec la règle réécrite à côté d'eux. `c.slug &&` est retiré du
manifeste : il ne filtrait plus rien de vrai, il perpétuait une prémisse fausse.
Le libellé du garde-fou qualité — « non générables via NosDéputés/NosSénateurs »
— devient « identité non fabriquée », et il affiche désormais **0 sur 13**.

## Deux candidats, deux régimes, et ce que la collecte rend vraiment

Royal et Bertrand ont un acteur AN ; les trois autres n'en ont pas.

| Candidat | Acteur AMO30 | Mandat AN | Ce que la collecte peut rendre |
| --- | --- | --- | --- |
| Ségolène Royal | `PA2650` | clos le 19/06/2007 (XII<sup>e</sup>) | **11 mandats**, 0 vote, 0 amendement — les archives de scrutins et d'amendements commencent à la XIV<sup>e</sup> |
| Xavier Bertrand | `PA267080` | clos le 12/01/2016 (XIV<sup>e</sup>) | mandats **et** une part d'activité parlementaire : son dernier mandat tombe dans la plus ancienne législature couverte |
| Arthaud, Tondelier, Lisnard | aucun | aucun | rien à collecter — et c'est un **fait vérifié**, pas une collecte manquée |

Les 0 de Ségolène Royal sont **mesurés** (collecte rejouée en local sur le cache
AMO30 le 28/08/2026), et ils ne sont pas la même chose : ses mandats sont un
zéro d'archive, pas un zéro de carrière. C'est exactement ce que le bloc
`couverture` publie — voir
[#couverture-listes-539](couverture-listes-539.md).

## Un profil écrit depuis `candidats.json` seul, et sa condition

`process_candidat` n'écrivait rien sans identité française ni mandat européen.
Une branche est ajoutée, et sa condition est le point qui compte : elle se
déclenche sur une **absence déclarée** dans la table (`ecart: "hors_an"`, avec
motif et preuve relus), **jamais** sur une absence de résultat. Un référentiel
en panne rend exactement le même vide, et écrire un squelette dessus serait le
défaut de #484 reconduit. Une panne déclarée (`WARNING_PREFIX_CHAMBRE_EN_ECHEC`)
écarte donc la branche.

Sans elle, ces trois-là auraient existé dans une liste et disparu au clic.

## La table devient multi-sources

`raw_data/correspondance_acteurs_an.json` passe en
`correspondance-acteurs-an-v2` : chaque entrée porte un bloc `identifiants`
(`an` / `senat` / `europarl` / `hatvp`) au lieu du seul `acteur_ref`. C'est elle
qui alimente le bloc publié, donc les deux nomenclatures sont **la même**,
importée de `schema_pivot` et pas recopiée.

Trois propriétés conservées, une étendue :

- l'**absence déclarée** garde son patron — `acteur_ref: null` **et**
  `ecart: "hors_an"` **et** un motif écrit. Un trou muet est ce qui a produit
  #510 et #501 ;
- `acteur_ref` reste **lu** comme l'ancien nom du champ `an`, et reste **exposé**
  par le chargeur : une table est un artefact relu, et refuser de relire ce
  qu'on a écrit hier transformerait un renommage de clé en perte de
  correspondances vérifiées à la main (même arbitrage que `KNOWN_SOURCE_TYPES`).
  Les deux écritures ensemble sont acceptées **si et seulement si** elles disent
  la même chose ;
- l'**unicité** d'un identifiant sur deux slugs devient une vérification par
  référentiel (`an`, `senat`, `europarl`), et plus seulement pour l'AN. Mesuré à
  0 sur les 481 entrées. `hatvp` en est exclu : c'est une URI de déclaration,
  pas une clé d'identité.

La table passe de 476 à **481 entrées** : Royal, Bertrand, et les trois
non-parlementaires en déclaration `hors_an`. Le garde-fou de couverture ne
bloque que dans un sens — un profil **publié** sans entrée. Cinq entrées sans
profil publié sont signalées, non bloquantes.

## Ce qui reste ouvert

- **Deux pages sur cinq restent à écrire.** Arthaud, Tondelier et Lisnard ont la
  leur : leur profil est entièrement déterministe hors ligne — le contenu sourcé
  de `candidats.json`, plus une absence déclarée. Royal et Bertrand non : leurs
  listes ont besoin des index d'amendements et de scrutins que seule la CI
  construit, et les produire ici publierait des `non_collecte — panne` qui
  décriraient un cache local, pas le corpus. Le lot livre ce qui les rend
  productibles — slug, shard, branche, couverture — et le prochain run les
  écrit. Le garde-fou qualité les nomme en attendant (« Manquants : 2 »), sans
  bloquer.
- **Les 186 `uri_hatvp` au format XML nil**, corrigés à la publication, pas à la
  source.
- **Le rendu des états de couverture** appartient au lot #324/#328, bloqué par
  #326.

---

