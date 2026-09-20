<a id="consommateurs-chambres-migres"></a>
# Les consommateurs de `chambre` migrés vers `chambres`, et le garde-fou qui datera son retrait (#494) (2026-08-20)

`2026-08-20`

> **En bref** — les consommateurs de `chambre` migrés vers `chambres`, avec le garde-fou qui datera le retrait du scalaire.

Sous-issue **E** de l'épic **#486**, après #493 (D, PR #504) qui a créé la liste
dérivée `chambres` et l'a fait coexister avec le scalaire « le temps de
reprendre les consommateurs un par un ».

Ne corrige pas #484 (constat plus bas, sans correction), ne touche pas à l'UI
(#495) ni à `.github/workflows/generate-data.yml` (#505). Aucune collecte
relancée, aucun fichier de `pivot_data/` ni de `raw_data/` modifié.

## Quatre `chambre` portent le même nom, et le recensement les confondait

C'est le point qui a fait échouer le recensement de l'épic sur trois emplacements
sur seize. Le dépôt en compte quatre :

| Ce dont on parle | Où | Valeurs |
| --- | --- | --- |
| la **chambre du profil pivot** | `chambre` / `chambres` | `AN`, `Senat`, `PE`, `mairie` |
| la **chambre de collecte** | profil *brut* (`raw_data/profiles`) | `deputes`, `senateurs` |
| la chambre d'un **mandat électif** (#492) | `mandats[].chambre` | `AN`, `Senat`, `PE`, `mairie` |
| la chambre d'un **groupe** ou d'un texte | `schema_groupe` | `AN`, `Senat` |

Trois corrections au recensement de #494, relevées en le refaisant à l'AST sur
`07e9147` :

- **`group_profile.py` n'a aucun consommateur du champ profil.** Les trois
  emplacements listés (l. 1364, 1373, 1443) sont `roster_chambre`, l'argument CLI
  `--roster-chambre` qui vaut `deputes`/`senateurs` : la chambre de collecte. Ses
  deux vraies lectures de `chambre` portent sur un **profil de groupe**
  (`profil_groupe.get("chambre")`), et une troisième sur un **mandat**.
- **`merge_profile._prefer_non_empty` n'est pas « aux deux niveaux de fusion »
  du champ profil.** `merge_raw_profile` (l. 266) fusionne le profil **brut** :
  sa `chambre` vaut `deputes`/`senateurs`. Un seul des deux niveaux est concerné.
- **`check_quality_gate` a deux filtres de population, pas un.** L'issue nommait
  `population_an` deux fois (l. ~350 et ~444) ; l. 444 est en réalité
  `_report_low_syceron_coverage`, un **second** filtre `chambre in ("AN",
  "deputes")`, et `population_an` est l. ~648. Les deux ont migré.

Et un consommateur qu'aucun des deux recensements ne voyait, parce qu'ils ne
regardaient que `src/*.py` : **`web/UI_finale/src/data/pivotAdapter.js`** lit
`pivot.chambre` pour fabriquer le libellé de profession de repli
(`chambreLabel` — « Député », « Ancien(ne) sénateur »). Sur un profil bicaméral
il n'en affiche qu'une : c'est littéralement la question éditoriale qui a ouvert
l'épic. Sa migration appartient à #495 (F).

## Une porte unique de lecture, et pourquoi elle a un repli

`schema_pivot.lire_chambres(profil)` est le seul lecteur du champ. Elle rend la
liste si `chambres` est présente, sinon `[chambre]` — en tolérant la valeur de
collecte (`deputes` → `AN`), tolérance que `check_quality_gate` portait depuis
toujours dans `chambre in ("AN", "deputes")` et qu'une migration naïve aurait
perdue en silence.

**Le repli n'est pas une commodité.** Mesuré sur `07e9147` le 20/08/2026 :
`chambres` est produite par #493, mais **0 des 209 profils publiés ne la porte** —
elle n'apparaîtra qu'après un run complet. Un consommateur qui lirait `chambres`
sans repli verrait une liste vide sur tout le corpus : `population_an` passerait
de **207 à 0**, et le signal de régression qu'elle porte s'éteindrait sur le
corpus même qu'il surveille. Sans repli, la coexistence que #493 a conçue pour
permettre une migration progressive n'aurait servi à rien.

Ce repli-là a une fin écrite, contrairement à ceux de #431 et #432 : il est une
branche unique, dans une fonction unique, et disparaît avec le scalaire.

## Ce qui a migré, et ce qui ne devait pas

| Emplacement | Décision |
| --- | --- |
| `check_quality_gate._report_amendements_coverage` — `population_an` | **migré** — `"AN" in lire_chambres(...)` |
| `check_quality_gate._report_low_syceron_coverage` — filtre AN | **migré** |
| `check_quality_gate._report_low_interventions` — colonne Chambre | **migré** — affiche `AN+PE` |
| `audit_pivot_dataset.compute_repartition_chambre` | **migré** — n'est plus une partition |
| `audit_pivot_dataset.compute_coherence_chambre_sources` | **migré** — contrôle chaque chambre |
| `audit_pivot_dataset.compute_tableau_croise_candidats` | **migré** — la ligne porte la liste |
| `audit_pivot_dataset.compute_plage_dates_candidats` | **migré** — idem |
| `merge_profile.merge_pivot_profile` (l. 447) | **inchangé** — `appliquer_chambres` réécrit les deux champs juste après : ce `_prefer_non_empty` n'alimente plus que le **repli** de la fabrique |
| `merge_profile.merge_raw_profile` (l. 266) | **inchangé** — profil brut, chambre de collecte |
| `normalize_nosdeputes` / `normalize_europarl` / `mep_profile` | **inchangés** — producteurs du repli, pas consommateurs |
| `candidate_profile`, `generate_all_profiles` | **inchangés** — chambre de collecte et chambre de mandat |
| `group_profile`, `generate_group_profiles`, `generate_roster_candidats`, `audit_groupe_dataset`, `schema_groupe`, `check_quality_gate._report_groupes` | **inchangés** — chambre d'un groupe |
| `web/UI_finale/src/data/pivotAdapter.js` | **hors périmètre** — #495 |

## L'effet mesuré sur `population_an` : zéro, et c'est le point

Simulation **en lecture seule** sur les **209 profils publiés** de `07e9147`
(aucune écriture, aucune collecte). « Publié » = le corpus tel qu'il est ;
« projeté » = ce que la même dérivation donnerait après une régénération qui
estampille les mandats européens, jamais un état constaté.

| Mesure, sur les 209 profils publiés | Scalaire (avant) | `chambres` (après), publié | `chambres`, projeté |
| --- | ---: | ---: | ---: |
| `population_an` (§3c) | **207** | **207** | **207** |
| assiette du filtre Syceron | **207** | **207** | **207** |
| profils contrôlés par `MAPPING_CHAMBRE_SOURCES` | 209 | 209 | 209 |
| incohérences `chambre(s)` / `sources[].type` | 0 | 0 | 0 |
| attributions de la répartition par chambre | 209 | 209 | **216** |

**L'assiette ne bouge pas, et il faut le dire ainsi plutôt que d'annoncer une
amélioration.** Ce que la migration change est une **propriété**, pas un
nombre : `"AN" in chambres` ne peut plus perdre quelqu'un qui a aussi siégé au
Sénat, là où le scalaire le perdait dès que l'autre chambre l'emportait. Le
nombre ne bougera que quand les mandats porteront leur chambre.

Le cas qui l'établit, et qui coupe court à toute lecture optimiste :
**`jean-luc-melenchon` ne revient pas dans `population_an`**. Son scalaire vaut
`Senat`, ses 5 `mandat_electif` sont tous à `chambre: null` (comme les 228 du
corpus), donc `lire_chambres` rend `["Senat"]` — aussi faux que le scalaire.
Et il en sortirait de toute façon par sa seconde condition : son `identite` est
vide, ce qui est l'autre moitié de #484. La migration n'y peut rien ; seule une
recollecte le peut.

La seule ligne qui bouge est la répartition par chambre, et seulement en
projection : `PE` passerait de 1 à 8 profils, parce que 7 profils bicaméraux
AN+PE ou Senat+PE cesseraient d'être publiés sous une seule chambre. **La somme
dépasse alors le nombre de profils** — 216 pour 209 — ce que
`total_attributions` publie explicitement à côté de `total_profils` : un
dénominateur se publie avec ce qu'il dénombre (§2.7).

*Corroboration* : la distribution projetée ici — `["AN"]` × 201, `["AN","PE"]` ×
6, `["Senat","PE"]` × 1, `["PE"]` × 1 — retombe exactement sur celle que #493
avait mesurée en rejouant le pipeline sur `b2c34f4`, par un chemin indépendant.

## Les 18 sénateurs publiés `AN` : ni corrigés, ni dégradés

#493 avait relevé que le scalaire est faux sur **au moins 20 profils**, pas
deux : aux cas Retailleau et Mélenchon s'ajoutent 18 sénateurs publiés
`chambre: "AN"`. Vérifié ici sur `07e9147` : ce sont exactement les **18 profils
sans aucun `mandat_electif`** (`gerard-larcher` compris), et le compte est le
même des deux côtés.

Sous cette migration, `lire_chambres` leur rend `["AN"]` — le repli, faute de
mandat qui dise autre chose. **Aucun consommateur ne s'en trouve dégradé** :
ils restent dans `population_an` et dans le contrôle chambre/sources exactement
comme avant. Mais aucun ne s'en trouve corrigé non plus, et une recollecte de
mandats n'y suffira pas : ils n'en ont aucun. Leur correction relève de la
collecte (tracée dans `ROADMAP.md`), pas du schéma.

## `_prefer_non_empty` sur `chambre` : la collance survit, contenue et déclarée

Constat, **sans correction** — #484 reste ouverte et n'est pas réduite par cette
issue.

`merge_pivot_profile` fait toujours `_prefer_non_empty(new.chambre, old.chambre)`
(l. 447), puis `appliquer_chambres` recalcule les deux champs en prenant ce
scalaire pour **repli** (l. ~468). Or `deriver_chambres` ajoute *toujours* le
repli — c'est la règle que #493 a retenue après deux simulations, parce que
retirer une chambre observée est une suppression. Donc **une chambre fausse qui
a survécu à une collecte muette survit dans `chambres`**. La bascule des
consommateurs vers un champ dérivé ne ferme pas la moitié « collante » de #484.

Deux choses changent tout de même, et ce sont celles qui comptent :

1. la chambre collante ne peut plus **évincer** une chambre que les mandats
   attestent — le scalaire remplaçait, la liste s'ajoute ;
2. elle est **déclarée** non corroborée, donc distinguable d'une chambre étayée.

La collance passe ainsi de *silencieuse et exclusive* à *déclarée et additive*.
C'est moins que sa correction, et il ne faut pas prendre l'un pour l'autre.

## `chambre` n'est pas retiré ici, et le garde-fou dit pourquoi

Aucune des deux conditions de retrait écrites par #493 n'est remplie :

1. **les consommateurs** — le pipeline a fini de migrer, mais
   `pivotAdapter.chambreLabel` lit encore le scalaire, et l'UI est le périmètre
   de #495 ;
2. **le champ n'a plus rien de propre à dire** — vérifié sur `07e9147` :
   **0 des 209 profils publiés porte le warning `chambres du profil non
   corroborée`**, non parce que la corroboration serait acquise mais parce
   qu'aucun ne porte encore `chambres`. Le « 208 sur 209 » de #493 est une
   projection, pas une mesure du corpus publié.

Et un retrait aujourd'hui serait bloquant par lui-même : `chambre` est un
scalaire surveillé par `audit_diff_profils`, et 209 régressions renseigné →
absent abandonneraient le commit — la raison même pour laquelle #493 avait
écarté la liste vide.

**`tests/test_garde_fou_chambre.py`** rend le reste mécanique. Il énumère par
l'AST tout usage de la clé `"chambre"` dans `src/*.py`, et par motif d'accès
tout `<expr>.chambre` sous `web/UI_finale`, puis exige que chaque emplacement
soit **déclaré avec sa catégorie** — profil, collecte, mandat, groupe, fabrique,
repli. Un emplacement neuf casse le test, et son auteur doit dire de quelle
`chambre` il parle : c'est précisément la distinction que le recensement de
l'épic n'avait pas faite.

`test_condition_1_de_retrait_etat_global` **échouera** le jour où #495 aura
migré le dernier consommateur, en disant que la condition 1 est remplie. Un test
qui échoue pour annoncer une fin, plutôt qu'une note dans un journal : c'est la
différence entre un transitoire qui se termine et les replis de #431/#432, qui
ne se sont jamais terminés.

## Tests

`tests/test_consommateurs_chambres.py` (23) et `tests/test_garde_fou_chambre.py`
(7), sur **fixtures figées** — aucune lecture de `pivot_data/` ni de
`raw_data/profiles/`, aucun accès réseau (#473).

