# Le `texte_vise` fautif se reprend depuis l'archive figée, pas par une fusion plus permissive (#696, 01/09/2026)

`2026-09-01`

> **En bref** — **2 500 des 484 132 amendements publiés** de `pivot_data/amendements/` portent dans `texte_vise` un **intitulé** au lieu de l'uid du document AN, tous en XVe législature et pour 5 intitulés distincts (2 458 « Système universel de retraite ») : #639 avait corrigé la collecte, mais l'index est fusionné additivement et `merge_amendements_index` laisse gagner « la nouvelle valeur si elle est renseignée » — un intitulé **est** renseigné, donc l'entrée gardait le sien à chaque reconstruction ; **quatrième occurrence** de la famille nommée par `AGENTS.md` §3a (#492, #639, #641) et **même remède** : un report nommé, jamais une fusion plus permissive ; le cadrage était même optimiste — la fusion ne conserve pas seulement le défaut, elle le **réintroduit** (`an:AMANR5L15PO59051B4857P0D1N000045` est porté avec son uid par **trois** profils bruts et publié avec l'intitulé du quatrième, parce que `jean-luc-melenchon.json` passe après eux dans l'ordre des fichiers), et les 13 399 paires fautives du corpus brut vivent **dans un seul profil**, le sien ; `amendements_index.backfill_texte_vise` relit donc la valeur dans `raw_data/amendements_an_figes/<legislature>/`, **jamais** reconstruite depuis le titre ni appariée par libellé (le préfixe du document — `PRJL`/`PION`/`PNRE`/`RAPP` — n'est pas dans l'uid de l'amendement, le déduire serait l'inventer), strictement monotone, **sans toucher la clé de fusion** (l'élargir est le défaut de #668) et **avant** `resoudre_textes` pour que la réparation gagne son dossier dans le même run ; le critère est la **grammaire** de l'uid AN (`est_uid_texte`), mesurée sur 2 387 valeurs distinctes publiées (2 382 acceptées, 5 refusées = exactement les 5 intitulés) et sur 2 086 valeurs distinctes des trois archives figées (2 086 acceptées, 0 refusée) — le critère « ne contient pas d'espace » de l'issue rend le **même verdict** sur les deux populations, **aucun contre-exemple**, mais la grammaire est plus stricte et « Bioéthique » est un titre de dossier réel ; câblé sur les **deux** chemins d'appel parce que la CI ne passe jamais par `build_amendements_index_pivot.py` (piège de #657) ; ce qu'il ne répare pas est compté et nommé — une législature sans archive figée (la XVIIe, cas **vide** aujourd'hui) et un amendement absent de l'archive (**zéro** : les 2 500 sont toutes réparables) —, la couche brute gardant son intitulé puisque le report se rejoue à chaque construction ; l'archive est lue **par projection** (280 Mio de RSS contre 610 en chargement direct, mesuré) et jamais ouverte pour une législature sans entrée fautive ; le run à venir doit faire passer `jean-luc-melenchon` de **23 dossiers / 2 499 dépôts sans dossier** à **25 / 0**.

## Contexte

#639 a corrigé la **collecte** : `fetch_amendements_officiels` résolvait le
`texte_vise` d'un amendement — l'uid du document AN amendé, `PRJLANR5L15B2623` —
en titre du dossier, puis **remplaçait le code par le titre** dans
l'enregistrement brut. Elle ne le fait plus.

La correction n'a jamais atteint l'index publié. `pivot_data/amendements/` est
reconstruit à chaque run puis **fusionné additivement** avec le précédent, et
`merge_amendements_index` laisse gagner « la nouvelle valeur si elle est
renseignée ». Un intitulé **est** renseigné.

### Ce qui est mesuré, le 01/09/2026, sur `origin/main` à `f635cb60`

| Population | Mesure |
| --- | ---: |
| amendements publiés, `pivot_data/amendements/{14,15,16,17}.json` | 484 132 |
| dont `texte_vise` n'est pas un uid de document AN | **2 500** |
| … tous en XVe législature, pour 5 intitulés distincts | 2 458 « Système universel de retraite », puis 20, 14, 6, 2 |
| valeurs de `texte_vise` distinctes publiées | 2 387 (2 382 uid + 5 intitulés) |
| paires amendement × signataire, 481 profils bruts | 6 091 732 |
| dont `texte_vise` est un intitulé | 13 399 |
| profils bruts porteurs d'au moins un intitulé | **1** — `jean-luc-melenchon` |
| uid d'amendement qu'**aucun** profil brut ne porte avec sa forme d'uid | 2 499 |

Et ce que ça coûte à la lecture, sur les dépôts **comme auteur principal**
(`role_signataire == "auteur_principal"`, index et table `textes` publiés) :

| Profil | Dépôts | Dossiers résolus | Sans dossier | dont cause = intitulé |
| --- | ---: | ---: | ---: | ---: |
| `jean-luc-melenchon` | 2 831 | 23 | **2 499 (88 %)** | 2 499 |
| `laurent-wauquiez` | 584 | 14 | 258 | 0 |
| `jerome-guedj` | 2 429 | 25 | 24 | 0 |
| `marine-le-pen` | 690 | 83 | 5 | 0 |

Toute vue qui regroupe les amendements par loi — le chantier de la fiche
candidat, #328 — reposait donc, pour Mélenchon, sur **12 %** de ses dépôts.

### La fusion ne conservait pas seulement le défaut : elle le réintroduisait

Les 2 500 entrées fautives de l'index ne correspondent pas aux 2 499 uid que le
corpus brut ne porte qu'en intitulé. **Il y en a une de trop**, et elle dit ce
que le cadrage de l'issue ne disait pas :
`an:AMANR5L15PO59051B4857P0D1N000045` est porté **avec son uid** par trois
profils bruts (`benedicte-taurine`, `caroline-fiat`, `francois-ruffin`) et avec
l'intitulé par un quatrième — et c'est l'intitulé qui est publié, parce que
`construire_index` retient la dernière valeur renseignée vue et que
`jean-luc-melenchon.json` passe après les trois autres dans l'ordre des fichiers.

Le défaut n'est donc pas seulement historique : il peut **contaminer une entrée
saine** à chaque run, et son verdict dépend de l'ordre alphabétique des slugs.

### Quatrième occurrence de la même famille

AGENTS.md §3a la nomme depuis #641 : *un champ corrigé n'atteint jamais une
entrée déjà collectée tout seul, et le remède est un report nommé, jamais une
fusion plus permissive* — #492 (`mandats[].chambre`), #639 (`type_scrutin`),
#641 (`identite.profession`). Les trois avaient passé la suite entière : le test
qui manquait couvrait la **transition**, pas les étapes.

## Décision

**Un report nommé, `amendements_index.backfill_texte_vise`, sur le patron de
`backfill_dossier_nature` (#689).** Il relit dans l'archive figée le
`texte_vise` des entrées qui n'en portent pas un, et ne touche rien d'autre.

1. **Sourcé.** La valeur de substitution vient de
   `raw_data/amendements_an_figes/<legislature>/amendements.json.gz`, keyée par
   l'uid de l'amendement. Jamais reconstruite depuis le titre, jamais appariée
   par libellé même exact (#639, §2 règle 2) — et pour cause : le préfixe du
   document (`PRJL`/`PION`/`PNRE`/`RAPP`) **n'est pas** dans l'uid de
   l'amendement, le déduire serait l'inventer. Les trois archives figées portent
   2 086 `texte_vise` distincts et **aucun n'est un intitulé** : la source avait
   raison tout du long.
2. **Strictement monotone.** Il ne touche qu'une entrée dont le `texte_vise`
   n'est pas un uid, ne substitue qu'une valeur qui en est un, n'écrase jamais
   un uid en place, ne vide rien, ne touche aucun autre champ, ne crée ni ne
   supprime aucune entrée, ne réordonne rien, et il est idempotent.
3. **La clé de fusion ne bouge pas.** `amendement_id` reste `an:<uid AN>`.
   L'élargir pour y porter le champ corrigé serait le défaut de #668 — 468
   doublons sur 940 entrées de `textes_portes`.
4. **Avant la résolution des dossiers, après la fusion.** Un `texte_vise` réparé
   doit gagner son dossier dans le **même** run ; et il faut passer après la
   fusion, puisque c'est elle qui peut réintroduire l'intitulé.
5. **Sur les deux chemins d'appel.** La CI ne passe **jamais** par
   `build_amendements_index_pivot.py` : elle appelle
   `generate_all_profiles._rafraichir_index_amendements`. Un report câblé sur le
   seul script n'aurait jamais atteint l'index publié — le piège de #657, « un
   consommateur que personne ne grep ». `tests/test_texte_vise_libelle_696.py`
   verrouille les deux.
6. **Actif par défaut, jamais derrière un interrupteur qu'on oublie de lever.**
   `--sans-report-texte-vise` existe pour une exécution sans archives figées, et
   il compte ce qu'il laisse. La CI n'a pas d'entrée de formulaire pour le
   désarmer.

### Le critère de détection, écrit et mesuré

`textes_vises_figes.est_uid_texte` reconnaît la **grammaire** de l'uid de
document AN : un préfixe capitalisé, l'infixe `ANR5L` que l'Assemblée écrit dans
chacun de ses identifiants, la législature, la série, le numéro
(`^[A-Z]{2,8}ANR5L\d{1,2}[A-Z]{0,4}\d+$`).

| Population | Acceptées | Refusées |
| --- | ---: | ---: |
| 2 387 `texte_vise` distincts publiés | 2 382 | **5** — exactement les 5 intitulés |
| 2 086 `texte_vise` distincts des trois archives figées | 2 086 | 0 |

L'issue proposait « un uid AN ne contient pas d'espace ». Mesuré sur ces deux
populations, les deux critères rendent **le même verdict**, et **aucun
contre-exemple n'a été trouvé** — ni un intitulé sans espace, ni un uid en
portant une. La grammaire est retenue parce qu'elle est strictement plus
stricte : un titre de dossier d'un seul mot passerait le critère de l'espace, et
« Bioéthique » est un titre de dossier réel de la XVe (#689). Les parties
variables du motif sont volontairement larges — le rôle du critère est de
reconnaître un identifiant, pas d'énumérer les quatre préfixes observés : un
préfixe inédit doit être accepté, pas requalifié en intitulé.

### Ce que le report ne peut pas réparer

- **Une législature sans archive figée.** La XVIIe est en cours ; elle n'en a
  pas. Le cas est aujourd'hui **vide** (0 des 96 893 amendements publiés de la
  XVIIe portent un intitulé), et il l'est par construction : la XVIIe est
  recollectée à chaque run, donc la correction de #639 l'a déjà traversée. Le
  report le **compte** (`legislatures_sans_source`) plutôt que de retomber sur
  une seconde source en silence — c'est ce silence qui a rendu #510 invisible.
- **Un amendement absent de l'archive, ou dont l'archive ne porte pas non plus
  d'uid.** Compté en `entrees_sans_source`, l'entrée garde son intitulé : un trou
  déclaré, jamais un trou creusé (§2 règle 5). **Sur le corpus d'aujourd'hui, ce
  compte est zéro : les 2 500 entrées fautives sont toutes réparables**, et elles
  se rattachent à 6 textes et 5 dossiers.
- **La couche brute.** `raw_data/profiles/jean-luc-melenchon` garde ses 13 399
  paires en intitulé : elle est source-near, elle n'est pas ce que `web/` lit, et
  la réécrire serait une réécriture de profil sans nouvelle collecte. Le report
  s'applique à **chaque** construction d'index, donc la couche publiée se répare
  et **se maintient réparée** sans que la couche brute change.

### Ce que le run à venir doit produire

Mesuré en rejouant `rafraichir` sur une copie de `pivot_data/amendements/15.json`
(aucun fichier du dépôt touché) : 2 500 corrigées, 0 sans source, 0 entrée
fautive restante, et `jean-luc-melenchon` passe de **23 dossiers / 2 499 dépôts
sans dossier** à **25 dossiers / 0 dépôt sans dossier**. Le contrôle de perte
(#460) n'y voit qu'un changement de valeur, non bloquant ; aucune entrée ne
disparaît, aucune liste ne rétrécit.

## Le coût, mesuré

L'archive figée de la XVe pèse 134 Mio décompressés pour 307 644
enregistrements. La charger telle quelle coûte **610 Mio de RSS** ; lue par
projection (`object_pairs_hook` qui ne retient d'un enregistrement que son
`texte_vise` et n'en garde que les uid demandés), **280 Mio et 1,9 s**. C'est la
règle de §3a : lire par projection, ne jamais garder un document.

Et l'archive d'une législature **sans entrée fautive n'est jamais ouverte** : le
report relève d'abord, lit ensuite. Sur un index sain, son coût est nul.

## Alternatives écartées

| Option | Pourquoi non |
| --- | --- |
| `--no-merge` | l'aide du script le réserve à un corpus **complet** ; reconstruire les 484 132 entrées pour en corriger 2 500 (0,5 %), et surtout : il ne corrigerait rien, puisque le profil brut porte lui aussi l'intitulé |
| Élargir la fusion (« l'uid gagne sur l'intitulé » dans `merge_amendements_index`) | c'est la fusion plus permissive que §3a interdit, et elle ne toucherait pas les entrées qu'aucun profil brut ne porte correctement — 2 499 des 2 500 |
| Corriger la couche brute | 7,8 Go réécrits pour un champ, sans collecte nouvelle ; `raw_data/` est source-near et n'est pas ce que `web/` lit |
| Rattacher l'intitulé au dossier par correspondance de titre | exactement ce que #639 interdit : une clé dérivée d'une chaîne, fausse le jour où deux dossiers partagent un intitulé |
| Reconstruire l'uid du document depuis l'uid de l'amendement (`…B2623…` → `…B2623`) | la série et le numéro y sont, **le préfixe non** : `PRJL`, `PION`, `PNRE` et `RAPP` sont tous possibles. Le choisir serait l'inventer |
| Élargir la clé de fusion pour y porter le `texte_vise` | le défaut de #668, verbatim |

## Où c'est

- `src/textes_vises_figes.py` — le critère (`est_uid_texte`) et le lecteur
  d'archive par projection (`lire_textes_vises`).
- `src/amendements_index.py` — `backfill_texte_vise`, appelé par `rafraichir`
  entre la fusion et `resoudre_textes`.
- `src/build_amendements_index_pivot.py` — le CLI et `--sans-report-texte-vise`.
- `src/generate_all_profiles.py` — `_rafraichir_index_amendements`, le chemin
  que la CI emprunte réellement.
- `tests/test_texte_vise_libelle_696.py` — 38 tests, sur la réduction
  **verbatim** `tests/fixtures/amendements_an_figes/15/amendements.json.gz`
  (4 enregistrements de l'archive réelle) et sur les 5 intitulés verbatim de
  l'index publié. Aucune valeur inventée (#510).
