# L'index des amendements n'écrit plus deux clés nulles sans objet (#1265, #580) (2026-11-05)

`2026-11-05`

> **En bref** — le run du 04/11/2026 a échoué au garde-fou de blob : avec les 25 non-inscrits (#1265), `pivot_data/amendements/15.json` passait à 80,73 Mio, au-dessus du seuil de 80. Le fichier publié omet désormais `base_juridique_irrecevabilite` et `source_url` quand ils valent `null`, et `amendements_index.charger()` les rétablit à `None`. Mesuré le 05/11/2026 sur les quatre fichiers de `main` : la XVe passe de 78,92 à 64,63 Mio, et les 755 467 amendements relus sont identiques à ceux d'avant l'écriture. `sort` et `date` restent publiés à `null`.

## Contexte

Le run 41876048393 (04/11/2026, épinglé à 18 h 16) a été le premier à collecter les profils des non-inscrits. Il a ajouté 6 879 amendements à la XVe (300 765 → 307 644) et le quality gate a refusé le commit : `15.json` pesait 80,73 Mio, au-dessus du seuil bloquant de `garde_fou_blobs` (80 Mio). Rien n'a été publié. La porte des non-inscrits a été refermée dans le code en attendant (#1439).

Deux options ont été présentées à la propriétaire le 05/11/2026 :

| Option | Gain sur la XVe | Coût |
| --- | --- | --- |
| A1 — découper la XVe par session | le fichier en trois ou quatre | l'interface charge `/data/amendements/${legislature}.json` (`web/UI_finale/src/data/index.js`) : le chemin change, `sync-data.mjs` et le validateur aussi |
| **A2 — ne plus écrire les clés nulles** | 14,98 Mo | aucun lecteur à changer |

Elle a répondu « A2 ».

## Mesure

Les clés à `null` des quatre fichiers, mesurées le 05/11/2026 sur `origin/main` (`051bee8aa0`) :

| Champ | Nul dans la XVe | Ce que `null` y dit |
| --- | --- | --- |
| `base_juridique_irrecevabilite` | 258 518 des 300 765 (9,57 Mo) | **sans objet** : les 42 247 amendements irrecevables de la XVe portent tous leur base, et `validate_amendements_index` l'exige |
| `source_url` | 300 765 des 300 765 (5,41 Mo) | rien : nul sur 100 % des 755 467 amendements des quatre fichiers |
| `sort` | 48 422 des 300 765 (0,58 Mo) | **non connu** |
| `date` | 4 des 300 765 | **non connu** |

## Décision

**Deux champs seulement** (`amendements_index.CHAMPS_OMIS_SI_NULS`) : ceux dont le `null` ne dit rien qu'une absence ne dise. `sort` et `date` nuls disent « non connu », et AGENTS.md §2 règle 5 veut qu'une donnée manquante soit écrite comme telle. Les omettre aurait gagné 0,58 Mo de plus.

**L'omission vit dans le fichier, pas en mémoire.** `ecrire()` écrit une copie de chaque entrée sans ces clés ; `charger()` les rétablit à `None`. Pour un lecteur Python, rien ne change : `get()` rend la même entrée qu'avant l'écriture (vérifié sur les 755 467 amendements). La fusion additive (`merge_amendements_index`) n'écrase déjà jamais par un `None`.

**Les lecteurs JavaScript lisaient déjà l'absence comme `null`** : `pivotAdapter.js` (`amendement.base_juridique_irrecevabilite ?? null`), `profilCandidat.js` (`if (a.base_juridique_irrecevabilite)`) ; aucun ne lit `source_url` de l'index. Aucun lecteur, Python ou JavaScript, n'accède à ces deux clés par indexation stricte.

**`schema_version` reste `amendements-v1`.** Un fichier où la clé est présente reste valide, et le fichier compagnon des cosignatures suit la même convention depuis #431 (un amendement sans cosignataire y est absent, `co_signataires()` rend `[]`).

**Ce n'est pas « rogner un champ » au sens du garde-fou** (`garde_fou_blobs.CONDUITE_A_TENIR`, `partition-profils-legislature-580.md`). Cette conduite protège le contenu de `raw_data/`, et aucune valeur ne disparaît ici : chaque clé omise valait `null`, et se relit `null`.

| Fichier | Avant (Mio) | Après (Mio) |
| --- | --- | --- |
| `14.json` | 39,69 | 32,03 |
| `15.json` | 78,92 | 64,63 |
| `16.json` | 42,11 | 34,91 |
| `17.json` | 37,70 | 31,06 |

Avec les 6 879 amendements des non-inscrits, la XVe devrait peser environ 66 Mio : sous le seuil bloquant, au-dessus de l'avertissement de 50 Mio.

## Alternative écartée

**Découper la XVe par session (A1).** C'est la conduite écrite du garde-fou pour un fichier déjà partitionné, et elle reste la suite si la XVe remonte vers 80 Mio. Elle n'a pas été retenue maintenant : elle change le chemin que l'interface charge, alors que 14,98 Mo de la XVe ne portaient aucune information.

**Omettre tous les `null`.** Écarté pour `sort` et `date` (règle 5, ci-dessus).

## Ce qui n'a pas été vérifié

- Le poids réel de la XVe avec les non-inscrits : il ne se mesurera qu'au premier run qui rouvre leur porte, après #1439.
- Pourquoi `source_url` n'est renseigné sur aucun amendement. Aucun lecteur de l'interface ne s'en sert, et elle ne construit pas non plus de lien vers l'amendement depuis son `uid` (recherché le 05/11/2026). Le champ est gardé dans `CHAMPS_AMENDEMENT` pour le jour où la collecte le remplirait.
- Le premier run après la fusion réécrit les quatre fichiers une fois (`ecrire_index_json` compare octet pour octet, et le format change), législatures closes comprises.
