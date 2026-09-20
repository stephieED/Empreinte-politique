<a id="reproductibilite-mandats-sans-estampille-839"></a>
# 280 des 406 mandats sans estampille sont portés par un référentiel vivant, et aucun n'est introuvable (#839, lot B) (2026-09-12)

`2026-09-12`

> **En bref** — `src/audit_mandats_reproductibles.py` juge, **sans réseau**, chacune des 406 entrées `mandats[]` sans `categorie_source` comptées au lot A, contre **deux** référentiels — AMO30 (`.cache/acteurs_historique_an/`) et le bloc `mandat_europeen` du profil brut, parce qu'AMO30 ne porte pas les organes du Parlement européen et déclarerait les 21 entrées européennes introuvables, donc retirables ; résultat sur `origin/main` au 12/09/2026 : **186** même organe et période recouvrante, **78** libellé approché, **3** même organe autre période, **13** organe européen — soit **280 reproduites** — **113** dont la période est couverte par un mandat sourcé sans que l'organe soit retrouvé, **13** sans aucune date, **0 introuvable, 0 acteur non résolu, 0 référentiel vide** ; **le mot « non reproductible » employé le 12/09 était faux** et cette mesure le remplace ; **calibrage sur le témoin recollecté** `jean-luc-melenchon`, dont la réponse est connue par la collecte : 15 établies, 4 à relire (dont ses 3 faits portés sous un autre nom et son mandat de sénateur), 5 sans date — le classement ne rend **aucun** verdict favorable de plus que ce que la collecte montre ; deux défauts d'appariement trouvés par ce calibrage et corrigés : l'**apostrophe typographique** (`_normalize_label` la garde, donc son retrait de préfixe ne reconnaissait pas « Mission d’information sur … ») et les **suffixes de référentiel** (« … de la francophonie a.p.f »), traités par une seconde passe **par inclusion de mots significatifs**, seuil **3** mesuré, `_normalize_label` de #387 laissé intact puisqu'il sert une purge ; **aucun retrait ne se déduit de ce lot** — `sans_date`, `acteur_non_resolu` et `referentiel_indisponible` sont des déclarations, pas des jugements (§2 règle 5, #241) ; 14 tests sur fixtures.

## 1. La question, reformulée pour être décidable

Le lot A compte 406 entrées sans `categorie_source`. Le champ absent dit
« personne n'a établi cette catégorie » (#718), et rien de plus.

Le 12/09/2026, un rapport à la propriétaire a écrit « ces mandats ne sont pas
reproductibles ». **C'était faux** : la mesure portait sur les libellés à
l'intérieur du profil, pas sur un référentiel. Deux choses étaient confondues :

| Ce qui était mesuré | Ce qui était dit |
| --- | --- |
| l'entrée ne revient pas telle quelle | le fait n'est plus disponible |

La première est vraie de presque toutes — l'AN nomme l'organe autrement que
l'ancienne source. Seule la seconde justifierait de parler de perte.

## 2. Deux référentiels, et pourquoi jamais un seul

**AMO30** porte les organes de l'Assemblée, et le lot A a montré que **21 des
406 entrées sont des organes du Parlement européen** (2 profils). Les juger sur
AMO30 seul les aurait déclarées introuvables — le verdict qui autorise un
retrait. Le second référentiel est le bloc `mandat_europeen` du profil brut.

Le libellé « Mandat de député européen » n'y est ajouté **que si le profil porte
un volet européen** : sinon un profil strictement français verrait une entrée de
ce nom déclarée reproduite.

Les deux lectures sont **hors réseau** : AMO30 vient du cache, l'européen du
brut. Vérifié le 12/09/2026 — 36 mandats rendus pour `PA2150` en quelques
secondes.

## 3. Le calibrage, avant de croire un seul chiffre

Le témoin `jean-luc-melenchon` a été recollecté à blanc : la réponse est connue
par la collecte, pas par l'appariement. Le classement rend :

| Verdict | Entrées |
| --- | ---: |
| reproduit — même organe, période recouvrante | 12 |
| reproduit — libellé approché | 3 |
| période couverte par un mandat sourcé, organe absent | 4 |
| aucune date | 5 |

Les 4 à relire sont ses 3 faits portés sous un autre nom (groupe FI, députés non
inscrits, mandat parlementaire) **et son mandat de sénateur**, le seul que rien
ne porte plus depuis #528. **Le classement ne déclare donc reproduit rien de
plus que ce que la collecte montre**, et laisse à la relecture ce que
l'appariement ne peut pas établir.

**Deux défauts d'appariement trouvés là, pas en relecture de code** :

1. **L'apostrophe typographique.** `_normalize_label` (#387) déplie les accents
   mais **garde les apostrophes** : son retrait de préfixe ne reconnaît pas
   « Mission d’information sur … », les deux libellés gardent alors chacun des
   mots que l'autre n'a pas, et aucune inclusion n'est possible. La mission
   covid de Mélenchon était manquée pour cette seule raison.
2. **Les suffixes de référentiel.** « Section française de l'Assemblée
   parlementaire de la francophonie » d'un côté, « … a.p.f » de l'autre.

D'où une **seconde passe, déclarée à part** : inclusion des **mots
significatifs** (mots vides retirés), dans les deux sens, avec un seuil de **3
mots** — deux mots rapprocheraient « Commission des transports » de
« Commission des transports et du tourisme », ce qu'un test verrouille.

**`_normalize_label` n'est pas modifié.** Il sert `purge_mandats_dupliques.py` :
l'élargir élargirait des retraits, et c'est exactement le faux positif que la
prudence de #387 existe pour éviter.

## 4. La mesure, sur les 406

| Verdict | Entrées | Profils |
| --- | ---: | --- |
| reproduit — même organe, période recouvrante | 186 | 40 (4 déclarés · 36 de roster) |
| reproduit — libellé approché, période recouvrante | 78 | 26 (3 · 23) |
| reproduit — même organe, autre période | 3 | 2 (1 · 1) |
| reproduit — organe du Parlement européen du profil | 13 | 1 (0 · 1) |
| **période couverte par un mandat sourcé, organe absent — à relire** | **113** | 34 (7 · 27) |
| **aucune date : rien à situer** | **13** | 2 (2 · 0) |
| introuvable | **0** | — |
| acteur non résolu / référentiel vide | **0** | — |

**280 sur 406 sont portées par un référentiel vivant.** Aucune n'est
introuvable : ce que l'appariement ne conclut pas, il le déclare à relire.

## 5. Ce que les 126 à relire contiennent

Trois familles portent les trois quarts du travail, et ce ne sont pas 126 cas
distincts :

| Famille | Entrées | Ce que c'est |
| --- | ---: | --- |
| `Mandat parlementaire (…)` en `mandat_electif` | 35 | le mandat est porté par une entrée sourcée dont le libellé cite le groupe autrement |
| `Députés Non Inscrits`, `Renaissance`, `Les Républicains` en `commission` | 47 | un **nom de groupe** publié comme une commission ; le fait est porté par `groupe_politique` |
| organes réels que le référentiel ne nomme pas ainsi | ~44 | missions flash, groupes de travail, Assemblée parlementaire franco-allemande, commissions extra-parlementaires, organes du Sénat |
| intitulés de navigation sans dates | 13 | `Amendements`, `Vidéos`, `Questions`, `Interventions`, `Loi ou de résolution` |

## 6. Ce que ce lot ne fait pas

**Aucun retrait, et aucune proposition de retrait.** `sans_date`,
`acteur_non_resolu` et `referentiel_indisponible` ne sont pas des jugements :
ils disent ce que la mesure n'a pas pu établir. Un lot de retrait qui s'appuie
sur l'un des trois retirerait sur une absence de mesure — ce que §2 règle 5
refuse, et ce que #241 a déjà payé.

Le périmètre du nettoyage (lot D) inclut `laurent-wauquiez`, dont la collecte
est gelée : arbitrage de la propriétaire du 12/09/2026, **le gel ne vaut que
pour la collecte en CI**.

## 7. L'alternative écartée

**Recollecter les 45 profils à blanc** pour juger par la collecte plutôt que par
appariement. C'est la mesure la plus sûre, et elle reste la référence — c'est
ainsi que ce lot est calibré. Mais 45 collectes, dont plusieurs à plus d'un Gio
de mémoire, coûtent des heures et se disputent les serveurs de l'Assemblée avec
les runs. L'appariement rend le même verdict sur le témoin, en quelques
secondes, et déclare ce qu'il ne sait pas.
