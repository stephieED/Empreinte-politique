<a id="couverture-listes-539"></a>
# Ce qu'une liste vide veut dire : les quatre états de couverture (#539) (2026-08-28)

`2026-08-28`

> **En bref** — une liste vide recouvre quatre états sans rapport (couvert, non collecté, hors couverture, panne) : ils sont désormais nommés.

Second volet de [#identite-profils-539](identite-profils-539.md), qui réglait
l'identité. Celui-ci règle la question que l'issue posait derrière : **une liste
vide, ça veut dire quoi ?**

## La mesure qui déplace la question

Le vide n'est pas un cas limite de ce corpus. Il en est la norme.

| Liste | Profils où elle est vide (sur 476) |
| --- | ---: |
| `interventions` | **469** |
| `tags_thematiques` | 469 |
| `textes_portes` | 454 |
| `amendements` | 120 |
| `votes` | 21 |
| `mandats` | 9 |

Et sous ce vide, quatre situations sans rapport entre elles. Les 469
`interventions` vides ne sont ni un fait sur la personne, ni un trou de source,
ni une panne : `generate-data.yml:1553-1554` et `:1641` appliquent
`--skip-interventions --skip-dossiers-legislatifs` **en dur** au job roster,
« indépendamment des inputs » (#357). C'est **une décision de pipeline**, et
elle couvre 469 profils sur 476.

## Décision 1 — quatre états, la cause portée par `non_collecte`

| État | Ce qu'une liste vide veut dire |
| --- | --- |
| `couvert` | collecté, dans le périmètre de la source, **réellement zéro** — un fait publiable |
| `fait_etabli` | un fait sur la **personne** : « jamais élu·e à l'Assemblée nationale » |
| `hors_couverture` | la source ne couvre pas cette période. **Jamais** un fait sur la personne |
| `non_collecte` | rien ne peut être affirmé. Porte obligatoirement une `cause` |

La nomenclature n'est pas inventée : c'est celle déjà fermée pour les
gouvernements (`couverture_dossiers.py`, #399). `partielle` n'y est pas repris —
la portée l'exprime en **deux entrées**, qui disent en plus *où* passe la
frontière.

`couvert` est le complément sans lequel les trois autres ne suffisent pas :
c'est l'état où une liste vide **dit vrai**. Sans lui, une liste sans entrée
retombe dans « on ne sait pas », et le produit perd le zéro constaté — qui est
précisément ce qu'il existe pour donner. §2.5 interdit de confondre un zéro
mesuré avec une absence, pas de publier le premier.

`cause` ∈ { `panne`, `par_decision` }, **obligatoire si et seulement si**
`etat == "non_collecte"`, interdite ailleurs. *(Une troisième valeur,
`defaut_collecte`, a été ajoutée par #562 — voir
[#defaut-collecte-vs-panne-562](defaut-collecte-vs-panne-562.md) : ranger un
défaut de notre code sous `panne` impute une faute à la source.)* Le « si et seulement si » est ce
qui empêche la cause d'être omise en silence. La preuve d'une `par_decision`
**nomme la politique** — le drapeau et l'issue —, pas une URL : la preuve d'une
décision est la décision.

*(Amendement de #558 — voir
[#groupe-gele-couverture-558](absences-publiees-comme-faits-556-558-560.md#groupe-gele-couverture-558). Les seules
`par_decision` que cette section connaisse sont les deux drapeaux de #357. Le
**gel d'un groupe** (`extraction_suspendue`, #516) en est une troisième, et son
absence de `DECISIONS_PIPELINE` a fait publier « couvert » à 20 profils de
sénateurs sur des listes vides. Une décision qui manque à la table n'est pas une
décision absente : c'est une décision publiée comme un fait. Amendement de #560
sur l'ordre des tests : une **frontière de source** se décide AVANT la cause,
sans quoi `hors_couverture` et `non_collecte`/`panne` se confondent — ce qui
était le cas du chemin des interventions.)*

## Décision 2 — cinq listes métier, et la complétude obligatoire

`mandats`, `votes`, `textes_portes`, `interventions`, `amendements`. **Pas
`tags_thematiques`** : c'est une aide à la lecture dérivée des autres (§2.8),
sans source propre donc sans borne propre.

Chaque liste porte **au moins une entrée**. Aucun défaut implicite : « pas
d'entrée = couvert » réintroduirait l'ambiguïté qu'on retire et ferait porter à
l'interface une hypothèse qu'aucune mesure n'étaye.

Chaque entrée porte une `preuve` et un `constate_le`, tous deux obligatoires.
Une entrée sans preuve serait une affirmation sans source, ce qu'AGENTS.md §2.2
interdit partout ailleurs.

`portee` est facultative — `{"legislature": n}` ou `{"debut", "fin"}` ; absente,
l'entrée vaut pour tout le profil.

## La forme à deux entrées, et pourquoi elle est la forme générale

Une liste collectée porte ce que la source couvre **et** ce qu'elle ne couvre
pas :

```json
"votes": [
  {"etat": "couvert",         "portee": {"debut": "2012-06-20", "fin": null}, ...},
  {"etat": "hors_couverture", "portee": {"debut": null, "fin": "2012-06-19"}, ...}
]
```

Cette forme ne dépend d'**aucune connaissance de la carrière** de la personne.
C'est ce qui la rend publiable sur les 9 profils dont les cinq listes sont déjà
vides — `eric-dolige`, `charles-guene`, `thierry-cozic`, `jean-pierre-bansard`,
`marie-christine-chauvin`, `jean-raymond-hugonet`, `jean-jacques-panunzi`,
`evelyne-renaud-garabedian`, `viviane-malet` : tous sénateurs, tous
`roster_groupe`, sans source depuis #528, et dont `mandats` est vide aussi, donc
sur lesquels une dérivation par mandats serait muette.

Elle dit ce qui est vrai et rien de plus : dans la fenêtre couverte, le compte
publié est ce que la source contient ; avant, nous ne couvrons pas. Le mandat de
XII<sup>e</sup> législature de Ségolène Royal tombe dans la seconde entrée, et
c'est tout ce que le produit a le droit d'en dire.

## Les bornes, vérifiées dans le code et pas recopiées

| Liste | Constante qui porte la borne | Législatures | Borne basse |
| --- | --- | --- | --- |
| `mandats` | AMO30 (référentiel historique) | 12-17 | **2002-06-19** |
| `votes` | `candidate_profile.AN_SCRUTINS_LEGISLATURES` | 14-17 | 2012-06-20 |
| `amendements` | `candidate_profile.AN_AMENDEMENTS_PATH` | 14-17 | 2012-06-20 |
| `textes_portes` | `couverture_dossiers.AN_DOSSIERS_ARCHIVES` | 15-17 | 2017-06-21 |
| `interventions` | `syceron_debates.SYCERON_AVAILABLE_LEGISLATURES` | 15-17 | 2017-06-21 |

`tests/test_couverture_profil_539.py` compare chaque borne publiée à la
constante qu'elle prétend suivre : le jour où une archive est ajoutée sans que
la couverture le dise, c'est là que ça tombe, pas six mois plus tard dans
l'interface.

**La borne d'AMO30 était « à mesurer », elle est mesurée** (28/08/2026, sur
`.cache/acteurs_historique_an/`) : **3 117 acteurs**, plus ancien `mandat_debut`
d'acteur **2002-06-19** — l'ouverture de la XII<sup>e</sup> — pour 150 acteurs.
Des mandats d'*organes* remontent au 09/07/1998 (9 en 1998, 10 en 1999, 34 en
2001), mais aucun acteur n'y est rattaché sans mandat de la XII<sup>e</sup>. La
borne prouvable est donc la **XII<sup>e</sup>**, et non la XI<sup>e</sup> que
nomme l'URL de l'archive. C'est la condition C1 : sans cette mesure écrite avec
la règle, la phrase publiable n'est pas « jamais élue » mais « jamais élue
depuis la XII<sup>e</sup> législature ».

Le calendrier des législatures XI-XVII vit dans `couverture_profil` et est
**vérifié à l'import** contre `scrutins_legislature.LEGISLATURES_AN` sur les
quatre qu'elles ont en commun. Étendre `LEGISLATURES_AN` aurait été pire :
elle résout la législature d'un scrutin, et un scrutin daté de 2005 y résoudrait
au lieu d'échouer.

## Décision 3 — `fait_etabli` dérivable, sous cinq conditions

« Jamais élu·e à l'Assemblée nationale » est un fait négatif : publiable
seulement si le référentiel qui l'étaye est exhaustif sur un périmètre qu'on
sait nommer.

| # | Condition | Ce qu'elle empêche |
| --- | --- | --- |
| C1 | référentiel **prouvé chargé** — `nb_acteurs ≥ 3 000`, mesure de référence 3 117. En dessous, l'état retombe sur `non_collecte`/`panne` | Le scénario #484 exactement |
| C2 | appariement sur l'**état civil complet**, jamais sur le nom seul | L'homonymie, que `_resolve_acteur_ref_par_slug` refuse déjà de trancher au hasard |
| C3 | pas de date de naissance ⇒ **pas de dérivation** | Le cas Bardella, dont la date est `null` dans la table |
| C4 | recalculé **à chaque run** ; l'immuabilité porte sur l'identifiant, jamais sur le fait | Qu'un fait devenu faux survive parce qu'il a été figé un jour |
| C5 | une **déclaration humaine** (motif + preuve) prime toujours | Qu'un automatisme contredise un fait vérifié à la main |

**La règle qui gouverne tout le module : la condition porte sur la santé de la
source, jamais sur l'absence de résultat.**

Le contre-exemple est dans le code, et il est piégeux. Le préfixe
`WARNING_PREFIX_VOTES_INTROUVABLES` couvre **deux faits opposés** dans
`candidate_profile` : « index des scrutins indisponible » (l. 1208 — une panne)
et « aucune correspondance officielle AN n'a été trouvée » (l. 4766 — un
constat). Indexer la détection sur le préfixe aurait reproduit #484 à
l'identique. `MOTIFS_PANNE` est donc indexé sur le **motif**, et son contenu est
la liste, fermée, des textes qui nomment une source qui n'a pas répondu.

Symétriquement, les deux seuls profils portant « aucun mandat français connu »
sont `marine-le-pen` (`PA720614`, 56 mandats, 1 813 votes publiés) et
`jean-luc-melenchon` (`PA2150`, 86 mandats, 1 016 votes). Une dérivation
branchée sur ce signal de run aurait publié « jamais élue à l'Assemblée
nationale » sur Marine Le Pen.

**Limite de portée, posée d'emblée** : ces conditions ne sont réunies que pour
l'**Assemblée nationale**. Ni le Sénat ni le Parlement européen n'ont
d'équivalent dont la complétude soit prouvable ; « jamais élu·e au Sénat » reste
donc **exclusivement humain**. Dériver sans référentiel rendrait un « fait
établi » là où nous n'avons qu'une absence de couverture — le contresens même
que #539 combat.

## Décision 4 — la couverture n'est PAS fusionnée additivement

C'est le piège du lot, et la seule exception à la règle de `merge_profile`.

La fusion additive protège la donnée **collectée** : une entrée acquise ne
disparaît pas parce qu'un run l'a manquée. La couverture ne décrit pas la
personne, elle décrit **le run** — ce qu'on a demandé à la source ce jour-là, et
ce que cette source couvre. La fusionner ferait survivre indéfiniment un
`couvert` établi le jour où la collecte tournait, à côté d'un `non_collecte`
d'aujourd'hui : la panne masquée par son propre historique.

Elle est donc **remplacée** à chaque passe pivot. Nuance retenue :
`_prefer_non_empty` plutôt que la nouvelle valeur sèche, pour qu'un outil
autonome qui ne dérive pas de couverture n'efface pas celle du corpus.

La décision de collecte, elle, est **consignée par la collecte** —
`meta.collecte_ecartee` dans le profil brut, propagé au pivot. Sans elle, la
passe pivot de la CI (`--pivot-only`, sans drapeau, `generate-data.yml:1903`)
publierait « couvert » sur une liste que personne n'a demandée. La provenance
`roster_groupe` reste le repli pour les 469 profils déjà publiés, qui ne portent
pas cette trace : le job qui les produit porte les deux drapeaux en dur, donc la
politique se lit sur la provenance seule.

## Ce que le corpus dit une fois le bloc publié

479 profils, 2 395 couples (profil, liste), 3 754 entrées :

| État | Entrées |
| --- | ---: |
| `hors_couverture` | 1 359 |
| `couvert` | 1 339 |
| `non_collecte` / `par_decision` | **936** |
| `non_collecte` / `panne` | **100** |
| `fait_etabli` | 20 |

Et la mesure qui justifie le lot à elle seule : sur les **123 profils dont
`amendements` est vide, 99 le sont parce que la source a échoué** (warning
« amendements indisponibles » déclaré dans leur `meta`) et **24 sont un zéro
réellement mesuré**. Avant ce bloc, les deux étaient le même `[]`.

Coût mesuré : **1 974 octets par profil** pour `couverture` + `identifiants`,
**923,4 Kio pour 479 profils, soit 0,25 %** des 359,8 Mio de
`pivot_data/profiles`. Trois fois l'estimation de l'arbitrage (660 o), et la
différence est la `preuve` — qui est justement ce qui rend le bloc relisible.
La complétude ne coûte rien.

## Ce qui reste ouvert

- **Le rendu des quatre états** appartient au lot #324/#328, bloqué par #326. Ce
  lot modélise et publie la donnée ; il ne touche aucun composant React.
- **`fait_etabli` n'est aujourd'hui dérivé de personne** : les 20 entrées (4
  profils × 5 listes) viennent toutes de déclarations humaines (C5), et c'est
  correct — les quatre personnes concernées sont sans date de naissance dans la
  table, donc C3 interdirait la dérivation. La branche C1/C2 est écrite, testée,
  et attend un cas.
- **`non_collecte`/`panne` sur `amendements` (99 profils)** décrit un état du
  corpus publié, pas une fatalité : un run où `extract-amendements-an` réussit
  les fera basculer en `couvert`. C'est précisément ce que C4 attend d'un état
  recalculé à chaque run.
  **Démenti par #562** : `extract-amendements-an` n'était pas en cause, et
  aucun run n'aurait fait basculer ces 99 profils. Le warning
  « amendements indisponibles » qu'ils portaient était le texte d'un `TypeError`
  du dépôt, converti en indisponibilité de source par un `except Exception` nu —
  voir [#defaut-collecte-vs-panne-562](defaut-collecte-vs-panne-562.md). Le bloc
  `couverture` n'a pas produit ce défaut : il l'a rendu **lisible**, après des
  mois où il ne vivait que dans `meta.warnings`.

---

