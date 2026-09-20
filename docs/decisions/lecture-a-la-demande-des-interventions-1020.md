<a id="lecture-a-la-demande-des-interventions-1020"></a>
# Un bloc que la projection retire se lit à la demande, il ne revient pas dans la liste (#1020) (2026-09-18)

`2026-09-18`

> **En bref** — `tags_thematiques_agreges` a été publié `[]` sur les **17
> fiches** de gouvernement, et `comptages.membres_avec_interventions` à `0`,
> pendant un run entier : l'agrégation lisait `profil["interventions"]` sur des
> profils **projetés** sur cinq blocs (#635), qui ne le portent pas. Le bloc est
> désormais lu **à la demande, une personne à la fois**, jamais rapatrié dans la
> liste. Mesuré après correctif : **5 726 étiquettes, 291 membres porteurs sur
> les 17 fiches, 13,5 s, 0,22 Gio de RSS**.

## Contexte

#1020 a livré `agreger_tags_thematiques`, et sa fonction est juste : appelée à
la main sur des profils entiers, elle rend ce qu'elle doit. Elle n'a rien rendu
en production, parce que le pipeline ne lui a jamais donné d'interventions.

`generate_gouvernement_profiles.generate_all` charge les profils par
`load_profils_from_dir`, qui les **projette** sur
`BLOCS_LUS_COMPOSITION = ("id", "nom", "identite", "mandats", "sources")`. La
projection existe pour une raison mesurée : garder les profils entiers coûtait
2,4 à 2,7 Gio sous un plafond de 2,0 (#635,
[`audit-599-projection-blocs-lus-628`](./audit-599-projection-blocs-lus-628.md)).
`interventions` n'y est pas, `profil.get("interventions")` rend `None`, et
l'agrégat sort vide — **sans un mot**, puisqu'une liste vide est une réponse
valide.

## Ce qui a empêché de le voir

`tests/test_agregat_parole_gouvernement_1020.py` fabrique ses profils, avec
leurs `interventions` dedans, et les passe **directement** à
`agreger_tags_thematiques`. Il prouve l'agrégation ; il ne traverse jamais le
chargement. **Un test qui contourne le chemin réel ne prouve rien de ce
chemin** — la même leçon que les fixtures inventées de #997.

## Décision

**Le bloc se lit à la demande, et le contrat le dit.**

1. `gouvernement_roster.charger_profils_et_chemins` rend, en une passe, les
   profils projetés **et** `{id: chemin}`. L'index est bâti sur l'`id` que le
   document porte, pas sur le nom du fichier : la convention slug = nom de
   fichier (#487) reste une convention, pas un contrat de lecture.
2. `gouvernement_roster.lecteur_interventions(chemins)` rend
   `lire(membre_id) -> interventions[]`. Le document entier est local à
   l'appel et meurt à son retour, exactement comme `_lire_profil_projete`.
3. `agreger_tags_thematiques(fenetres, lire_interventions)` ne reçoit **plus
   de profils**. Un appelant doit dire d'où vient la matière ; il ne peut plus
   passer, sans le savoir, des profils qui n'en portent pas.
4. `build_gouvernement_profile(..., lire_interventions=None)` : `None` veut
   dire « personne ne peut lire les interventions ». L'agrégat n'est alors
   **pas calculé**, `membres_avec_interventions` vaut `null` — jamais `0`, qui
   affirmerait qu'aucun membre n'a parlé (§2 règle 5) — et un warning le dit.

## Pourquoi pas ajouter `interventions` à `BLOCS_LUS_COMPOSITION`

C'est l'option évidente, et c'est celle qui ramène le mur de #635. Mesuré le
18/09/2026 sur 35 profils échantillonnés (1 sur 40 des 1 383 publiés) :

| Bloc | Part du volume |
| --- | ---: |
| `amendements` | 57,2 % |
| **`interventions`** | **38,1 %** |
| `votes` | 6,9 % |
| `mandats` | 1,7 % |
| tout le reste | < 1 % |

Soit ~560 Mo de JSON extrapolés aux 1 478,9 Mo du corpus, × 4 en objets
Python. La projection retenait 2,0 % du volume ; l'y remettre en retiendrait
40 %.

## Pourquoi pas une passe unique sur le corpus

L'autre forme possible : relire tous les profils une fois, en agrégeant au fil
de la lecture pour les 17 gouvernements à la fois. Elle suppose de connaître
toutes les fenêtres **avant** la lecture, donc de construire les rosters en
amont, donc de couper `build_gouvernement_profile` en deux.

Elle est aussi **plus chère**, ce qui a tranché : une passe complète coûte
1 478,9 Mo à 61 Mo/s ≈ 24 s, là où la lecture à la demande n'ouvre que ce dont
elle a besoin — **650 lectures pour 311 personnes distinctes**, une personne
étant relue autant de fois qu'elle a servi dans plusieurs gouvernements, soit
~700 Mo ≈ 11 s. Mesuré sur le chemin réel : **13,5 s** pour les 17 fiches,
**0,22 Gio de RSS** au plus haut.

## Ce que ça publie

| Gouvernement | Étiquettes | Membres porteurs / distincts |
| --- | ---: | ---: |
| Borne | 1 738 | 50 / 55 |
| Lecornu II | 1 257 | 39 / 39 |
| Bayrou | 942 | 36 / 36 |
| Attal | 741 | 34 / 35 |
| Castex | 684 | 43 / 43 |
| Barnier | 303 | 39 / 42 |
| Philippe II | 61 | 50 / 50 |
| **Les 10 autres** | **0** | **0** |

**Les zéros ne sont pas un défaut, et le dénominateur les rend lisibles.** Les
interventions collectées commencent le **28/06/2017** — début de la XVe
législature. Les neuf gouvernements antérieurs à Philippe II, Philippe I
compris (18/05 → 19/06/2017, clos neuf jours avant la première entrée du
corpus), n'ont rien à agréger. Lecornu I (10/09 → 10/10/2025) est le cas le
plus net : ses 19 membres portent 2 516 interventions entre août et novembre
2025 et **aucune dans sa fenêtre**, l'Assemblée n'ayant pas siégé — un zéro
mesuré, pas un trou de collecte.

## Garde

`tests/test_generate_gouvernement_profiles.py` écrit des profils **sur
disque**, les fait lire par `generate_all`, et vérifie que la fiche produite
porte ses étiquettes et écarte ce qui tombe hors de la fenêtre du membre. Les
deux cas échouent sur le code d'avant (vérifié en le restaurant), ce qui est la
seule preuve qui compte pour un test de non-régression.

## Alternative rejetée

**Publier `tags_thematiques_agreges: []` et `membres_avec_interventions: 0`
quand aucun lecteur n'est fourni.** C'est exactement l'état qui a été publié :
un zéro qui se lit « aucun membre n'a pris la parole » là où la mesure n'a pas
eu lieu. L'absence de mesure est désormais `null` plus un warning (§2 règle 5).
