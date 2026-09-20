# L'européen entre dans les listes que la fiche a déjà (#683, lot 2)

`2026-09-09`

> **En bref** — trois formes maquettées sur les données réelles de Bardella, la propriétaire tranche **« A enrichi »** : **pas de bloc européen parallèle**, un seul jeu de listes et chaque entrée qui sait d'où elle vient ; **six des sept natures européennes entraient déjà sans un champ de plus** (votes en `scrutin_id: null` + `scrutin_non_resolu` comme les amendements de #431, résolutions en `textes_portes` avec un rôle existant **apparié à `nature_texte`** (#689), interventions et questions en `interventions[]` où l'Assemblée range déjà les siennes), la septième — les **explications de vote**, seule matière où la personne dit elle-même pourquoi elle a voté — recevant un `type_detail` neuf ; **ce qui se publie est la position sur l'ensemble du texte** et rien d'autre, transposition de #711 — Bardella compte **607 scrutins sur le seul dossier `2018/0216(COD)`** et 93 % des intitulés sont procéduraux —, vérifié par la mesure : **1 007 de ses 1 137 dossiers ont exactement un vote retenu**, les pires cas étant des décharges où le Parlement vote réellement deux fois ; les écartés sont **comptés et déclarés** (§2 règle 5, #511) ; **le vocabulaire fermé des natures a dû devenir bilingue** — au passage à la XIe législature la source change de langue ET de tiret, la première version rendait **0 vote retenu sur 2024-2026** (5 012 scrutins pour Bardella) et **aucun test ne pouvait le voir**, toutes les fixtures étant au format d'avant : c'est la **borne de couverture** arrêtée au 19/10/2023 sur une personne siégeant toujours qui l'a révélé, troisième contrôle d'effet de la journée à trouver ce qu'une suite verte laissait passer ; **la couverture dit désormais quelle borne porte sur quelle part** — sans quoi 1 926 votes européens se publiaient sous « l'Assemblée nationale ne publie pas de scrutins avant la XIVe », preuve vraie portant sur rien (§2 règle 2) — l'institution étant lue **sur l'entrée** et la portée **mesurée sur les entrées**, jamais recopiée d'une page de source qui vieillit (#484) ; `COLLECTE_SANS_VERBATIM_SOURCE` ajoutée parce que « la source n'en publie pas » n'est pas « notre run ne l'a pas demandé » (#657) ; et **l'enrichissement remonte avant la dérivation de la couverture**, qui le suivait — un profil européen publiait sa couverture calculée avant l'arrivée de ses 525 amendements, et le chemin de collecte normal n'enrichissait pas du tout. Effet mesuré, schéma validé sur les 7 : **12 939 votes sur un texte**, 4 584 interventions, 397 textes portés. **Le chiffre de 375 annoncé en maquette est corrigé à 1 926** pour Bardella. Pas de fiche de groupe européenne, pas de wiring du périmètre (5 min 45 par run, mesurées). Suite complète à 4 343, 0 échec.

## Contexte

Le lot 1 (#807) a réparé la lecture des dumps ParlTrack : les amendements et les
dossiers de rapporteur arrivent. Restaient dehors les votes, les interventions,
les questions, les propositions de résolution et les explications de vote — lus
et testés, mais rangés nulle part.

Trois formes ont été maquettées sur les données réelles de Jordan Bardella et
arbitrées par la propriétaire le 09/09/2026 : **deux registres appariés, enrichis**.
Sa formulation dit l'essentiel — « construit de façon à mapper les profils pivot
des candidats, auxquels s'ajoutent les données supplémentaires de ParlTrack ».
Autrement dit : **pas de bloc européen parallèle**. Un seul jeu de listes, chaque
entrée sachant d'où elle vient, et la vue qui les sépare à l'affichage.

Elle a également tranché qu'il n'y aura **pas de fiche de groupe européenne**.
Le périmètre reste les **7 candidats déclarés** à identifiant européen ; les 15
membres de roster qui en ont un ne servaient qu'aux agrégats de groupe.

## Décision

### 1. Chaque nature européenne va dans la liste qui la porte déjà

| Matière ParlTrack | Liste pivot | Ce qui la rend admissible |
| --- | --- | --- |
| Votes sur l'ensemble d'un texte | `votes[]` | `scrutin_id: null` + `scrutin_non_resolu`, la forme que le schéma prévoit pour un scrutin non rattachable |
| Amendements | `amendements[]` | déjà fait au lot 1 (#431) |
| Dossiers de rapporteur, rapports, avis | `textes_portes[]`, rôle `rapporteur` | rôle existant |
| Propositions de résolution | `textes_portes[]`, rôle `auteur_proposition_de_resolution` | rôle existant, **apparié à `nature_texte`** (#689) |
| Interventions en séance | `interventions[]`, `type_detail: "debat"` | — |
| Questions écrites et orales | `interventions[]`, `type_detail: "question"` | l'Assemblée y range déjà les siennes, avec `sous_type` |
| Explications de vote | `interventions[]`, `type_detail: "explication_de_vote"` | **le seul ajout** |

Rien de neuf sauf la dernière ligne : le schéma savait déjà tout accueillir.

### 2. Ce qui se publie, et ce qui se compte

Un député européen vote des centaines de fois sur un même texte : Bardella
compte **607 scrutins sur le seul dossier `2018/0216(COD)`**, dont 271 pour, 247
contre et 89 abstentions. Et **93 %** des intitulés sont procéduraux (« Am 1 »,
« § 13 », « Mardi - demande du groupe GUE/NGL »).

Seule la position sur **l'ensemble du texte** est publiée — la transposition
exacte de « un texte, une position » (#711). Vérifié sur Bardella : **1 007 de
ses 1 137 dossiers ont exactement un vote retenu**, 120 en ont deux, et les
quatre pires cas sont des décharges budgétaires, où le Parlement vote
réellement une `Décision` et une `Résolution` séparées, parfois deux fois.

Les scrutins écartés sont **comptés et déclarés** dans un avertissement destiné
au lecteur : une position d'amendement n'est pas une position absente (§2
règle 5, #511).

### 3. Le vocabulaire des natures est fermé, et il est bilingue

`NATURES_VOTE_SUR_ENSEMBLE` relève les natures sur les 44 648 scrutins du dump.
**Le seul signal disponible est l'intitulé** — le dump ne porte aucun drapeau —
et c'est une fragilité qu'il faut nommer.

**Elle s'est manifestée immédiatement.** Au passage à la XIe législature
(juillet 2024), la source change deux choses à la fois : elle écrit en
**anglais** et sépare par un **tiret demi-cadratin** au lieu du trait d'union.
La première version de la sélection ne connaissait ni l'un ni l'autre et rendait
**0 vote retenu sur 2024, 2025 et 2026** — 5 012 scrutins pour le seul Bardella.

Aucun test ne pouvait le voir : toutes les fixtures étaient écrites dans le
format d'avant. Ce qui l'a révélé est la **borne de couverture**, qui s'arrêtait
au 19/10/2023 sur une personne siégeant toujours. C'est la troisième fois de la
journée qu'un contrôle d'effet trouve ce qu'une suite verte laissait passer.

### 4. La couverture dit quelle borne s'applique à quelle part

Sans cela, Bardella publiait ses 1 926 votes du Parlement européen sous une
couverture disant « l'Assemblée nationale ne publie pas de scrutins avant la XIVe
législature ». La borne était vraie et ne portait sur rien : **une preuve qui
parle d'une source dont la liste ne vient pas est une preuve fausse** (§2 règle 2).

`couverture_profil.bornes_europeennes` lit l'institution **sur l'entrée
elle-même** — `institution: "parlement_europeen"`, posée dans
`scrutin_non_resolu`, `amendement_non_resolu`, `interventions[].source` et sur
l'entrée de `textes_portes` — et ajoute une entrée par liste, avec sa portée.

**La portée est mesurée sur les entrées, jamais recopiée d'une page de source.**
La date de fraîcheur d'un dump vieillit dès qu'on l'écrit ; la dernière date
effectivement portée par le corpus se recalcule à chaque run et dit la même
chose sans pouvoir mentir (#484). Mesuré : `2019-07-18 → 2026-03-26` pour les
votes de Bardella, ce qui restitue exactement la borne du dump `ep_votes`.

### 5. Les explications de vote entrent sans leur lien, et le disent

C'est la seule matière du corpus européen où la personne dit elle-même pourquoi
elle a voté ainsi — en français, datée, rattachée à un texte. Et **aucune ne
porte de lien** vers le document officiel : 0 sur 190 chez Bardella, la
référence n'est dans l'intitulé qu'1 fois sur 190, et le titre ne correspond
exactement à un dossier que dans 30 % des cas.

La propriétaire a tranché le 09/09 : on les publie, avec la limite écrite. Le
texte **est** sourcé — ParlTrack transcrit l'annexe officielle de la séance — ;
c'est le lien profond qui manque, et il se déclare plutôt qu'il ne se devine.

### 6. Une valeur de collecte de plus, parce que deux absences ne se confondent pas

Le Parlement européen ne publie **aucun** verbatim de séance : titre, date, lien
vers le document, rien de plus. `COLLECTE_SANS_VERBATIM_SOURCE` dit « il n'existe
pas chez la source » là où `theme_seul` dit « notre run ne l'a pas demandé »
(#657). Les confondre rangerait sous une décision de collecte ce que la source ne
publie pas. Les explications de vote, elles, ne portent aucune marque : leur
forme est complète.

### 7. L'enrichissement remonte avant la dérivation de la couverture

Il vivait chez l'appelant, et deux choses en découlaient. La couverture est
dérivée sur les listes « arrêtées » : un profil européen publiait donc
`couverture.amendements` calculée **avant** l'arrivée de ses 525 amendements.
Et le chemin de collecte normal n'enrichissait pas du tout — seul `--pivot-only`
le faisait, si bien que les deux chemins ne produisaient pas le même pivot.

La couverture est un champ dérivé (§4) : la seule façon de garantir qu'elle voit
tout est que rien ne change les listes après elle.

## Effet mesuré

Sur les dumps publiés, les 7 candidats déclarés, schéma validé pour chacun :

| Candidat | Votes sur un texte | Écartés | Interventions | Textes portés | Borne PE des votes |
| --- | ---: | ---: | ---: | ---: | --- |
| Emmanuel Maurel | 3 598 | 24 389 | 845 | 45 | 2014-07-16 → 2024-04-25 |
| Marine Le Pen | 2 092 | 8 578 | 956 | 58 | 2004-09-15 → 2017-05-17 |
| Raphaël Glucksmann | 1 977 | 19 840 | 128 | 23 | 2019-07-18 → 2026-03-11 |
| Jordan Bardella | 1 926 | 18 709 | 255 | 14 | 2019-07-18 → 2026-03-26 |
| Jean-Luc Mélenchon | 1 570 | 6 253 | 1 803 | 4 | 2009-11-25 → 2017-03-16 |
| Florian Philippot | 1 454 | 7 016 | 1 585 | 252 | 2014-07-17 → 2019-04-18 |
| Lydie Massard | 322 | 2 293 | 12 | 1 | 2023-10-17 → 2024-04-25 |

**Un chiffre annoncé à la propriétaire est corrigé ici** : la maquette du 09/09
annonçait **375** votes publiables pour Bardella. C'était la mesure d'un motif
étroit, écrit avant le relevé du vocabulaire ; le compte réel est **1 926**.

## Ce que ce lot ne fait pas

- **Il ne wire toujours pas `definir_perimetre_meps`** : 49 s par personne
  mesurées, ~5 min 45 par run pour les sept, contre 78 s périmètre posé. La
  table de correspondance ne porte que **12** identifiants européens et il en
  manque 4 des 7 — s'en servir donnerait un périmètre partiel pour un gain
  partiel. Le poser demande une passe préalable sur `raw_data/profiles/`.
- **Il ne rend pas les titres français.** Le Parlement européen publie ses
  intitulés en anglais : 1 sur 190 porte un accent français.
- **Il ne touche pas la vue.** Les listes portent désormais leur institution ;
  les séparer à l'écran est le lot suivant.

## Alternative écartée

**Un bloc `activite_europeenne` parallèle aux listes françaises.** C'est la
forme A de la maquette prise au pied de la lettre, et elle a l'avantage évident
de rendre le cumul impossible par construction. Elle a été écartée par la
propriétaire, et la mesure lui donne raison : le schéma accueillait déjà six des
sept natures européennes sans un champ de plus. Un bloc parallèle aurait
dupliqué `votes`, `amendements`, `textes_portes` et `interventions` — quatre
listes, leurs clés de fusion, leurs contrôles de perte, leurs entrées de
couverture — pour ranger ailleurs ce qui a la même forme. Ce qui doit rester
séparé n'est pas le stockage, c'est le **dénominateur** : deux natures ne
partagent jamais un total (règle de forme 4), et c'est la vue qui l'applique.
