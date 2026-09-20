<a id="position-politique-groupes-686"></a>
# La position politique d'un groupe est celle que l'Assemblée déclare, lue dans une table committée (#686) (2026-09-01)

`2026-09-01`

> **En bref** — l'AN qualifie **elle-même** ses groupes (`organe.positionPolitique` sur les organes `GP` d'AMO30 : **40 des 63** organes, `Opposition` 24, `Minoritaire` 11, `Majoritaire` 5), le pipeline le lisait déjà pour les profils individuels (`mandats[].position_dans_hemicycle`, #354) et **nulle part pour les 7 fiches de groupe**, alors que la posture commande la lecture de tous leurs compteurs ; les fiches gagnent `position_politique` — `position`, `source_url` **obligatoire même sur `non_declaree`** (miroir de §2 règle 6), `verifie_le`, et `organes[]` qui publie **chaque organe** avec la chaîne source verbatim —, branché par la **table committée** `correspondance_sigles_an` et jamais par ressemblance de sigle : nos fiches disent `REN` et `LFI`, le référentiel dit `RE` et `LFI-NUPES`, et l'appariement direct rendait `None` sur **deux fiches sur cinq, dont la seule majoritaire du corpus** ; `non_declaree` est une **valeur publiée** distincte d'un champ absent — les **14 groupes de la XVIIe** sont dans ce cas, l'AN ne qualifiant qu'une législature achevée, et rien n'est jamais déduit d'un comportement de vote (§2 règle 1) ; `Minoritaire` reste une **catégorie vide**, `DEM` et `HOR` étant déclarés tels en XVIe sans avoir de fiche, et les replier serait un acte éditorial ; **deux organes successifs qui divergent se publient `divergente`**, jamais repliés sur le dernier (qui déciderait laquelle des deux moitiés de la législature définit le groupe, en silence) ni sur `null` (déjà pris par `non_declaree`) — mesuré nul aujourd'hui, les deux organes `SOC` de la XVIe s'accordant, et publié quand même ; le schéma exige que `position` soit **exactement** le résumé de `organes[]`, ce qui fait d'une posture inventée une erreur de schéma ; garde-fou **§4b du portail de qualité, seuil 0** sur le patron du §5b (#525) — fiche AN publiée sans entrée, table invalide, ou position publiée contredisant la table ; le champ reste **optionnel** (#653/#558) et les 5 fiches AN ne le porteront qu'après un run réel, ce que le §4b imprime comme compteur de migration ; `VERSION_INDEX_GP` passe en `v2` parce qu'un index `v1` restauré du cache CI ferait mesurer « aucun groupe qualifié » sur une archive qui en qualifie 40 (#510) ; `POSITION_POLITIQUE_AN_VERS_PIVOT` devient canonique dans `schema_pivot` et la table des sigles passe d'`an_roster` à `groupes_config` (précédent #558) ; **aucun taux, classement ni moyenne par posture** — la posture explique des chiffres, elle ne les corrige pas.

## 1. Le problème

L'Assemblée nationale qualifie **elle-même** chacun de ses groupes politiques —
`Majoritaire`, `Opposition`, `Minoritaire` — dans `organe.positionPolitique` du
référentiel AMO30, sur les organes `codeType == "GP"`. Ce n'est pas une
qualification que ce dépôt produirait : c'est la sienne.

Le pipeline la lisait déjà, et l'écrivait sur les **profils individuels**
(`mandats[].position_dans_hemicycle`, avec `source_url` sur 100 % des cas,
#354). Elle était **absente des 7 fiches de groupe** : zéro occurrence de
`positionPolitique`, `position_dans_hemicycle`, `majoritaire` ou `minoritaire`
dans `pivot_data/groupes/*.json`.

Ce n'est pas un champ décoratif : **la posture commande la lecture d'une fiche
de groupe**. Sans elle, « le groupe majoritaire fait adopter 30 686 amendements,
ce groupe d'opposition 9 386 » se lit comme une différence de compétence ; avec
elle, comme la définition d'une majorité.

## 2. Ce que l'archive dit, mesuré le 01/09/2026

Sur `.cache/acteurs_historique_an/acteurs_historique.zip` (13,6 Mo), et
reproduit dans les tests sur la réduction verbatim
`tests/fixtures/amo30_gp_leg16_17.zip` :

| Législature | Organes `GP` | Qualifiés |
| --- | ---: | ---: |
| 12 | 5 | 0 |
| 13 · 14 · 15 · 16 | 5 · 10 · 17 · 12 | 4 · 9 · 16 · 11 |
| **17 — en cours** | **14** | **0** |
| **total** | **63** | **40** |

Valeurs distinctes : `Opposition` 24, `Minoritaire` 11, `Majoritaire` 5, absente
23. Les cinq fiches publiées (toutes en XVIe) :

| Fiche | Sigle publié | Sigle(s) AN | Organe(s) | Déclaration AN | Publié |
| --- | --- | --- | --- | --- | --- |
| `groupe-AN-REN-16` | `REN` | `RE` | `PO800538` | Majoritaire | `majorite` |
| `groupe-AN-SOC-16` | `SOC` | `SOC`, `SOC-A` | `PO800496`, `PO830170` | Opposition, Opposition | `opposition` |
| `groupe-AN-RN-16` | `RN` | `RN` | `PO800520` | Opposition | `opposition` |
| `groupe-AN-LFI-16` | `LFI` | `LFI-NUPES` | `PO800490` | Opposition | `opposition` |
| `groupe-AN-LR-16` | `LR` | `LR` | `PO800508` | Opposition | `opposition` |

## 3. Trois obstacles, et ce que le lot en fait

### a. L'appariement par sigle échoue en silence sur deux fiches sur cinq

Nos fiches publient `REN` et `LFI` ; le référentiel dit `RE` et `LFI-NUPES`. Un
appariement direct rend `None` pour ces deux-là — **dont la seule fiche
majoritaire du corpus**, c'est-à-dire précisément celle qui porte le contraste.

Rien n'est inventé ici : la table `correspondance_sigles_an` de
`raw_data/groupes_reels.json` existe et est committée depuis #526, et sa propre
description énonce la règle — « Committée et relue, jamais devinée : `RE` ne se
déduit pas de `REN`, ni `DR` de `LR`. » Chaque entrée gagne un bloc
`position_politique_an` : la position résumée, les organes **avec la chaîne
source verbatim**, et une date de relecture.

`groupes_config.position_politique_publiee(sigle, législature)` compose ce que
la fiche publie ; `generate_group_profiles.py` l'appelle pour toute entrée dont
la `chambre` est `AN`. **Aucune archive n'est lue au moment de générer** : un
job qui produit des fiches de groupe n'a pas à télécharger 13,6 Mo, et une
valeur relue et datée vaut mieux qu'une valeur remesurée à chaque run (même
arbitrage qu'en #526 §6).

### b. Aucun groupe de la XVIIe n'a de position déclarée

`non_declaree` est une **valeur publiée**, distincte d'un champ absent. L'AN ne
qualifie ses groupes qu'une fois la législature achevée : les 14 groupes de la
XVIIe sont dans ce cas, et cinq d'entre eux ont déjà une entrée de table. Elle
n'est **jamais** déduite d'un comportement de vote, ce qui serait exactement le
jugement que ce dépôt refuse de porter (AGENTS.md §2 règle 1).

Un champ **absent** dit « non renseigné » — c'est le cas des 2 fiches
`groupe-Senat-*` (AMO30 ne qualifie que les organes de l'Assemblée) et, jusqu'au
prochain run réel, des 5 fiches AN publiées avant ce lot.

### c. Aucun groupe minoritaire n'a de fiche

`DEM` et `HOR` sont déclarés `Minoritaire` en XVIe ; ni l'un ni l'autre n'est
publié. La troisième posture existe donc dans le référentiel et pas dans le
corpus. Elle reste dans le vocabulaire, comme **catégorie vide** : la replier
sur `majorite` ou `opposition` serait un acte éditorial.

## 4. La décision : deux organes successifs qui divergent se publient `divergente`

`SOC` a `sigles_an: ["SOC", "SOC-A"]` — deux organes successifs dans la même
législature (`PO800496` du 28/06/2022 au 18/10/2023, puis `PO830170` jusqu'au
09/06/2024). Les deux sont `Opposition` aujourd'hui ; **rien ne le garantit
demain**, et #526 a déjà rencontré la même forme sur les rosters (`AD` → `UDR` →
`UDDPLR` en XVIIe).

Ce que fait le code :

1. **`organes[]` publie chaque organe**, dans l'ordre de succession, avec son
   `sigle_an`, son uid, la chaîne source verbatim et sa traduction. Rien n'est
   replié : c'est l'union de #526, appliquée à une qualification plutôt qu'à
   une composition.
2. **`position` est le résumé dérivé** de ces déclarations
   (`schema_groupe.resumer_position_politique`) : la valeur commune si les
   organes qui déclarent s'accordent, `non_declaree` si aucun ne déclare,
   **`divergente`** s'ils se contredisent.
3. Un organe muet **ne fait pas taire** un organe qui déclare : muet n'est pas
   contradiction, et le détail reste lisible dans `organes[]`.

**Alternative écartée : retenir le dernier organe.** C'est le repli qui vient
spontanément — « le groupe est ce qu'il est devenu ». Il décide laquelle des
deux moitiés de la législature définit le groupe, sur une fiche dont tous les
autres compteurs couvrent la législature entière ; et il le décide en silence,
puisque le résultat est indiscernable d'un groupe à organe unique. Retenir « la
plus longue période » a le même défaut avec une arithmétique en plus.

**Alternative écartée : `null` en cas de divergence.** Elle confondrait « les
organes se contredisent » avec « la source n'a rien déclaré », qui est déjà
`non_declaree`. Deux constats distincts ne partagent pas une valeur.

Le cas est **mesuré nul aujourd'hui** — et publié quand même, parce qu'un cas
non prévu se replie toujours sur le premier organe venu.

## 5. Le champ publié

```json
"position_politique": {
  "position": "majorite",
  "source_url": "https://data.assemblee-nationale.fr/…/AMO30_…json.zip",
  "verifie_le": "2026-09-01",
  "organes": [
    {"organe_an": "PO800538", "sigle_an": "RE",
     "valeur_source": "Majoritaire", "position": "majorite"}
  ]
}
```

`POSITIONS_POLITIQUES_GROUPE` : `majorite`, `minoritaire`, `opposition`,
`non_declaree`, `divergente`. Les trois premières sont celles du référentiel,
traduites par `schema_pivot.POSITION_POLITIQUE_AN_VERS_PIVOT` — **la même table
que les profils individuels**, désormais canonique dans `schema_pivot` : deux
tables jumelles auraient dérivé le jour où l'AN ajoute une valeur.

Quatre invariants de schéma, dont le dernier est le seul qui compte vraiment :

1. `position` appartient au vocabulaire fermé ;
2. `source_url` est **obligatoire dès que le bloc est présent**, y compris sur
   `non_declaree` — un constat d'absence nomme sa source comme un constat de
   présence. Miroir de la règle 6 d'AGENTS.md §2, qui l'exige déjà de
   `mandats[].position_dans_hemicycle` ;
3. `verifie_le` est obligatoire — une qualification non datée ne se relit pas ;
4. **`position` est exactement le résumé de `organes[]`.** Publier une posture
   que les déclarations de la source ne portent pas devient une erreur de
   schéma, et non un choix d'implémentation.

Le bloc est **optionnel**, comme `date_reference` (#653) et
`couverture_roster.etat` (#558) : les 7 fiches publiées avant ce lot ne le
portent pas, et les déclarer invalides ferait échouer le portail de qualité sur
du publié qui ne sera pas régénéré.

## 6. Le garde-fou : §4b du portail de qualité, seuil 0

Patron du §5b (#525) pour `correspondance_acteurs_an.json`, et pour la même
raison : une correspondance manquante ne se manifeste pas comme une erreur, elle
se manifeste comme une posture absente sur la fiche où elle comptait le plus.

**Échec dur** :

- une fiche AN publiée dont le couple `(groupe_sigle, législature)` n'a pas
  d'entrée dans la table — le message nomme le couple ;
- une table absente, illisible, ou violant un invariant : entrée sans
  `position_politique_an`, position hors vocabulaire, organe absent de
  `organes_an` (le fil-piège de #526), traduction que `valeur_source` ne porte
  pas, résumé que les organes ne donnent pas ;
- une fiche qui publie une position **différente** de celle que la table
  committe : la fiche est régénérée depuis la table à chaque run, donc un écart
  veut dire qu'une qualification publiée n'est plus adossée à sa preuve relue.

**Ne bloque pas** : une fiche AN publiée **sans** le champ (les 5 d'aujourd'hui
— c'est le compteur de migration, imprimé, et il tombe à 0 au premier run) ; une
fiche non-AN ; une entrée de table sans fiche publiée (les 5 groupes de la
XVIIe : un périmètre, pas un écart, #526 §4). Et la table n'est **réclamée que
s'il existe au moins une fiche AN publiée** : un contrôle sans objet ne bloque
pas un commit.

## 7. Le fil-piège, et ce qu'il dira

`python3 src/an_roster.py --positions` compare, entrée par entrée, la
qualification **committée** à celle que l'archive **déclare**. Il n'écrit rien :
une table qui se réécrirait sur mesure ne serait plus une table relue (#526).
Écart mesuré au 01/09/2026 : **0 sur 10**.

Le jour où la XVIIe s'achèvera, ses 14 groupes passeront de « non qualifié » à
une valeur, et c'est ce rapport — plus
`tests/test_position_politique_groupes_686.py::test_la_table_committee_dit_ce_que_larchive_dit`
— qui le dira.

`VERSION_INDEX_GP` passe à `an-roster-gp-v2`. Le suffixe n'est pas cosmétique :
`.cache/acteurs_historique_an/` traverse les jobs par la clé de cache CI, et un
index `v1` — qui ne porte pas `position_politique` — relu « au mieux » ferait
mesurer « aucun groupe n'est qualifié » sur une archive qui en qualifie 40. La
forme exacte du trou muet de #510.

## 8. Ce que le lot ne fait pas, et pourquoi

**Aucun taux, aucun classement, aucune moyenne par posture.** La posture
*explique* des chiffres, elle ne les *corrige* pas : un « taux d'adoption ajusté
pour l'opposition » fabriquerait un score en trois étapes de plus (AGENTS.md §2
règle 1), et §6 interdit déjà tout taux d'adoption tous déposants confondus.

**La valeur n'est dans aucune fiche publiée à ce jour.** Le champ, sa
correspondance et son garde-fou sont en place ; les cinq fiches AN ne le
porteront qu'après un run réel de `generate_group_profiles.py`. Le §4b l'imprime
comme compteur de migration plutôt que de le taire.

## 9. Effet de bord : où vit la table des sigles

`CLE_CORRESPONDANCE_SIGLES`, `CorrespondanceSiglesInvalide`,
`charger_correspondance_sigles` et `entree_correspondance` **passent de
`an_roster` à `groupes_config`**, réexportés depuis `an_roster` pour les
appelants historiques. C'est le précédent de #558 (`CHEMIN_CONFIG_GROUPES`)
appliqué au reste : `raw_data/groupes_reels.json` a maintenant quatre lecteurs,
et trois d'entre eux — la génération des fiches, le portail de qualité, la
config des groupes — n'ont aucune raison de dépendre du dérivateur de roster AN.
Un seul chargeur, une seule validation : deux auraient divergé.
