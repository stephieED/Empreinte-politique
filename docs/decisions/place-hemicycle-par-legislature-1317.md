# La place d'un député dans l'hémicycle se lit dans l'archive de sa législature (#1317)

`2026-10-21`

> **En bref** — chaque mandat de député (`mandat_electif`, chambre `AN`) publie `place_hemicycle` : `{numero, source_url, etat_au}`, le numéro de siège lu dans l'archive AMO30 **de la législature du mandat** — `repository/15` et `repository/16` figées pour les XVe et XVIe, la courante pour la XVIIe. Jamais l'archive courante sur un mandat clos : elle y recopie le siège actuel de son titulaire (sur les 633 mandats XVIe, 323 changés et 202 vidés). `null` avec un motif fermé sinon, XIVe comprise. Reporté sur les mandats déjà publiés, aux deux étages.

## Contexte

#1314 dessine un hémicycle de 577 sièges, groupes dans l'ordre où ils siègent.
Un ordre gauche-droite inventé serait un placement politique sans source. Il
faut le siège de chaque député, par législature, sourcé — rosters compris.

La source porte `mandature.placeHemicycle` sur chaque mandat
`typeOrgane == "ASSEMBLEE"` d'AMO30 : **une valeur par mandat, sans date** —
la place à la date de l'archive. `_build_acteur_identite_index` ne lisait que
celle du mandat courant, et le champ n'atteignait pas le pivot.

Mesuré le 21/10/2026, hors dépôt puis avec le code du lot, sur trois
archives (courante téléchargée le 19/10/2026), population = mandats de député
de la législature (élus et remplaçants), tous acteurs d'AMO30, comptés dans
l'archive de leur législature :

| Législature | Archive | `last-modified` | Mandats avec une place | Places distinctes |
| --- | --- | --- | ---: | ---: |
| XVIIe | `repository/17` (courante) | republiée chaque nuit | 596 / 683 | 574 |
| XVIe | `repository/16` | 28/06/2024 | 591 / 633 | 577 |
| XVe | `repository/15` | 09/06/2022 | 579 / 675 | 567 |
| XIVe | `repository/14` → 404 | — | — | — |

**Le piège.** Dans l'archive courante, un mandat d'une législature close ne
porte une place que si son titulaire siège en XVIIe, et c'est alors son siège
actuel : sur les 633 mandats XVIe, 100 identiques à l'archive figée, **323
changés, 202 vidés**, 8 remplis depuis. Florent Boudié (`PA606507`) porte
`251` sur ses mandats XIVe, XVe et XVIe dans la courante ; l'archive XVe dit
`448`, l'archive XVIe `354`, et son mandat XVIIe n'a pas de place.

Les profils publient un mandat par siège (`(legislature, dateDebut)`, #640) :
575 / 656 sièges XVIIe avec une place, 581 / 623 XVIe, 572 / 666 XVe. L'archive
XVe est figée avant la fin de la législature (21/06/2022) : 13 enregistrements
XVe de la courante n'y sont pas, dont 9 segments d'un siège qu'elle porte et
**4 sièges** qu'elle ne porte pas du tout (remplaçants entrés après le
09/06/2022).

## Décision

1. **`resoudre_place_hemicycle(acteur_ref, legislature, debut)`**
   (`candidate_profile.py`) lit l'index des places de la législature
   (`_build_index_places_hemicycle`) : `{acteurRef: {dateDebut: place}}` tiré
   de SON archive, les segments d'un même siège partageant leur `dateDebut`
   (aucune clé ne porte deux places dans les trois archives). Appelée dans
   `build_profile` pour chaque période de `mandats_assemblee` — le chemin des
   candidats déclarés **et** des rosters (`generate_all_profiles` →
   `build_profile`, rien n'y dépend de la provenance).
2. **La forme** : `{"numero": "354", "source_url": <archive lue>, "etat_au":
   "2024-06-28"}`, `numero` verbatim (zéros de tête compris : `"081"`).
   `etat_au` : pour une archive figée, l'en-tête `last-modified` relevé par
   HEAD le 21/10/2026, posé en constante (`ARCHIVES_AMO30_FIGEES`) — l'archive
   n'est plus republiée, le relire à chaque run ne dirait rien de plus ; pour
   la courante, la date (heure de Paris) du fichier en cache, c'est-à-dire de
   son téléchargement, que le cache GitHub Actions restaure telle quelle.
3. **`null` porte toujours `place_hemicycle_non_resolu.motif`**
   (`KNOWN_MOTIFS_PLACE_HEMICYCLE_NON_RESOLU`) :
   `legislature_sans_archive_figee` (XIVe et avant ; la place d'une autre
   archive n'est jamais empruntée — l'archive XVe n'en donne qu'à 120 des 691
   mandats XIVe) ; `archive_indisponible` (l'archive n'a pas été lue ce run —
   un fait sur le run, jamais un constat d'absence, §2 règle 5) ;
   `mandat_absent_de_l_archive` ; `source_sans_place`. Les deux derniers
   nomment l'archive lue et son `etat_au`.
4. **La clé est facultative et réservée aux mandats de député** :
   `validate_profil()` refuse la clé sur un autre mandat, un motif sans clé, un
   `null` sans motif connu, une place accompagnée d'un motif, une forme
   incomplète. `_normalize_mandat` la recopie sur les seuls `mandat_electif`
   de chambre `AN`.
5. **La fusion n'apporte pas le champ seule** — mesuré sur les quatre mandats
   de député de `florent-boudie` (profil de roster) publiés sur `public/main` :
   `_mandat_key` / `_pivot_mandat_key` ne le contiennent pas, l'entrée
   ancienne gagne. D'où `backfill_mandat_place_hemicycle`, câblé aux deux
   étages. **Une place résolue n'est jamais remise à `null`** ; elle n'est
   remplacée que par une place lue à un `etat_au` au moins aussi récent (le
   siège XVIIe change en cours de législature, la dernière lecture fait foi).
   `archive_indisponible` n'efface jamais un motif lu dans l'archive. Le test
   de transition part des blocs réels copiés dans
   `tests/fixtures/florent_boudie_mandats_1317.json`, et sa contre-épreuve
   échoue quand le report est neutralisé.
6. **Les archives figées** se téléchargent par `_ensure_archive_amo30_figee`
   (même mécanisme que l'archive courante : `.part` renommé au succès, budget
   mur de 120 s, plus deux reprises #1202 — deux essais de l'archive XVIe ont
   été coupés à 1,6 et 2,9 Mo le 21/10/2026), une fois par process en cas
   d'échec. Elles vivent sous `.cache/acteurs_historique_an/figees/` : même
   `path:` de cache, **workflow inchangé**, et la péremption hebdomadaire
   (#555) les épargne. Elles s'invalident par `cold_start` ou en renommant
   `SOUS_REPERTOIRE_AMO30_FIGEES` ; leur index se reconstruit quand
   `NOM_INDEX_PLACES_HEMICYCLE` change.

## Alternative écartée

**Lire la place dans l'archive courante**, la seule que le pipeline
téléchargeait. Écarté par la mesure : elle publierait sur 323 mandats XVIe le
siège XVIIe de leur titulaire et laisserait 202 autres sans place, un fait faux
présenté comme sourcé (§2 règle 2) — exactement l'ordre inventé que #1314
cherche à éviter.

**Relire `last-modified` à chaque run pour les archives figées.** Écarté : une
requête de plus pour une valeur qui ne bouge plus ; et en cas d'échec il
faudrait choisir entre une date inventée et pas de date. La constante porte sa
mesure et sa source.

## Non vérifié

- Le comportement sur le corpus entier : la transition est testée sur un
  profil réel (quatre mandats, quatre cas), pas après un run. Les décomptes par
  législature sur `public/main` attendus par l'issue ne se feront qu'après lui.
- Le temps réel des deux téléchargements sur un runner GitHub, et le
  comportement du premier jour : tant que l'entrée de cache restaurée a été
  écrite avant le lot, chaque shard du roster télécharge les deux archives.
- Un mandat de député publié hors de `build_profile` (héritage d'une source
  retirée) restera sans clé : aucun run ne le recollecte.
