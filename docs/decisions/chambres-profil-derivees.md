<a id="chambres-profil-derivees"></a>
# `chambres` au niveau profil : une liste dérivée, et `chambre` qui n'en est plus que le premier élément (#493) (2026-08-20)

`2026-08-20`

> **En bref** — un champ dérivé se recalcule, il ne se fusionne pas ; le repli est déclaré par profil.

Sous-issue **D** de l'épic **#486**, après #487 (A), #488 (B) et #492 (C). Ne
migre aucun consommateur (#494, sous-issue E), ne corrige pas le profil de
Mélenchon (#484), ne touche pas à l'UI (#495). Aucune collecte relancée, aucun
fichier de `pivot_data/` ni de `raw_data/` modifié.

## Le défaut

`schema_pivot` publiait `chambre` — un scalaire, une chambre par personne, et
une donnée **collectée** : la chambre du site qui avait répondu le premier
(#488). Une carrière sur deux chambres n'y tenait pas, et le scalaire était faux
dans les deux sens : `bruno-retailleau` publié `AN` alors qu'il siège au Sénat
depuis 2004, `jean-luc-melenchon` publié `Senat` alors qu'il a été député
2017-2022.

Mesuré ici, la faute est plus large que les deux cas de l'épic. Sur les 209
profils publiés de `b2c34f4`, **18 profils sont des sénateurs publiés
`chambre: "AN"`** — les 15 membres de `groupe-Senat-LR` et les 5 de
`groupe-Senat-SER` présents dans le corpus, `gerard-larcher` compris. Leur profil
brut porte `chambre: "deputes"` et leur `sources[].type` vaut `nosdeputes` :
`nosdeputes.fr` a répondu pour eux (les délégations internationales de l'AN
recensent aussi des sénateurs), et l'erreur est **cohérente avec elle-même**.
C'est pourquoi `audit_pivot_dataset.compute_coherence_chambre_sources` ne la voit
pas : elle compare la chambre aux types de sources, et les deux viennent du même
malentendu. Ces 18 profils sont exactement ceux qui n'ont **aucun**
`mandat_electif` collecté — donc ceux qu'aucune recollecte de mandats ne
corrigera.

## L'option « dériver du mandat en cours » est mesurément mauvaise

Mesuré sur les 209 profils publiés de `b2c34f4` :

| Résultat de la dérivation par le mandat en cours | Profils |
| --- | ---: |
| aucun mandat électif en cours → `chambre` deviendrait `null` | **114** |
| un seul mandat en cours → dérivation nette | 95 |
| plusieurs mandats en cours → ambigu | 0 |

**55 % du corpus perdrait sa chambre**, dont `edouard-philippe` et
`jean-luc-melenchon` parmi les 8 `candidat_declare`. Et deux consommateurs
utilisent ce champ pour **sélectionner une population**, pas pour informer :
`check_quality_gate` §3c (`chambre in ("AN", "deputes")`) verrait son assiette
passer de 207 à 95, et `audit_pivot_dataset.MAPPING_CHAMBRE_SOURCES`, qui fait
`continue` sur un `null`, cesserait de contrôler 114 profils. Elle remplacerait
surtout un fait faux par un autre : la carrière de député de Retailleau
disparaîtrait comme disparaissent aujourd'hui les années sénatoriales de
Mélenchon.

## La décision : `chambres`, liste dérivée — et `chambre` = `chambres[0]`

`schema_pivot.deriver_chambres()` est désormais la **seule fabrique** des deux
champs. `chambres` est la liste des chambres de `KNOWN_CHAMBRES`, dans l'ordre de
`ORDRE_CHAMBRES` (`AN`, `Senat`, `PE`, `mairie`), et `chambre` en est le premier
élément — `validate_profil` refuse toute divergence.

Une **liste**, pas une chaîne concaténée : `chambre in ("AN", "deputes")` renvoie
`False` sur `"AN; Senat"` **sans lever d'erreur**, là où `"AN" in chambres` est
explicite et testable. Des valeurs de `KNOWN_CHAMBRES`, pas des rôles : « Député »
et « Sénateur » appartiennent au mandat, qui les porte déjà ; le niveau profil n'a
besoin que de l'énumération, et c'est ce qui la rend vérifiable par le validateur.

`AN` avant `Senat` dans `ORDRE_CHAMBRES` reprend la convention déjà documentée
par #488 (« le premier de `CHAMBRES` l'emporte quand les deux répondent ») : c'est
ce qui garantit qu'aucun scalaire publié ne change de valeur du seul fait que la
dérivation remplace la collecte.

## Ce qui a rendu la condition non négociable satisfiable

`chambre` **cesse d'être une donnée autonome**. Deux champs dérivés de la même
fabrique ne peuvent pas se contredire ; un champ collecté à côté d'un champ dérivé
garderait le mensonge à côté de la vérité en ajoutant la question « lequel
croire ». L'invariant est vérifié à trois endroits : la fabrique, le validateur,
et une simulation en lecture seule sur les 209 profils (0 profil en erreur).

## Le repli s'ajoute, il ne se substitue jamais — et deux mesures l'ont imposé

Aujourd'hui, **les 228 `mandat_electif` publiés sont tous à `chambre: null`**
(#492 estampille à la collecte ; rien n'a été recollecté depuis). Une dérivation
strictement fondée sur les mandats donnerait donc `chambres: []` et
`chambre: null` sur les 209 profils — ce qui ne rend pas seulement le champ
inutilisable pendant la transition : `chambre` est un **scalaire surveillé** par
`audit_diff_profils`, et 209 régressions renseigné → `null` **abandonnent le
commit**. L'option « liste vide » ne survit donc pas à un seul run.

`chambres` intègre par conséquent la **chambre de collecte** — quel jeu de
données a répondu. Deux formulations plus restrictives ont été essayées et
corrigées par la simulation, pour la même raison à chaque fois : *retirer une
chambre observée est une suppression*, ce que le pipeline ne fait jamais.

| Règle du repli | Effet mesuré sur les 209 profils de `b2c34f4` |
| --- | --- |
| « seulement si aucun mandat n'est estampillé » | **7 profils basculent de `AN`/`Senat` vers `PE`** (`marine-le-pen`, `damien-abad`, `jean-luc-melenchon`, `philippe-juvin`, `constance-le-grip`, `anne-sophie-frigout`, `yannick-vaugrenard`) : leurs mandats européens sont estampillés `PE` par `normalize_europarl`, leurs mandats AN restent à `null`. Une députée publiée députée européenne. |
| « seulement tant que la couverture des mandats est incomplète » | **1 profil bascule** : `yannick-vaugrenard`, dont le seul `mandat_electif` collecté est européen. Tous ses électifs étant estampillés, la couverture passait pour complète — et son `AN` disparaissait, le sortant de `population_an`. |
| **« toujours ajoutée »** (retenue) | **0 divergence** sur les 209 profils, dans les deux chemins du pipeline. |

La leçon du second cas mérite d'être écrite : **la complétude de `mandats[]`
n'est pas celle d'une carrière.** Un profil peut n'avoir aucun `mandat_electif`
français collecté sans avoir cessé de siéger — c'est le cas des 18 sénateurs
ci-dessus. `ChambresDerivees.corroboree` dit donc seulement « chaque chambre
publiée est étayée par un mandat estampillé », jamais « voici toute la carrière ».

## Pourquoi ce repli n'est pas trompeur, et à quelle condition il cesse de l'être

Le repli est **utilisable, pas vérifié**. Ce qui l'empêche d'être trompeur n'est
pas son exactitude — il est faux sur au moins 20 profils mesurés — c'est qu'il est
**déclaré** : un warning `chambres du profil non corroborée` nomme, dans le profil
lui-même, les chambres qu'aucun mandat n'étaye et le nombre de mandats électifs
encore sans chambre (§2.5). Un consommateur migré tôt (#494) peut donc distinguer
une liste que les mandats étayent entièrement d'une liste où la chambre de
collecte figure sur sa seule parole, et
`audit_pivot_dataset.compute_agregation_warnings` en donne le décompte de corpus.

Entre les deux options que l'issue posait, la liste vide est la plus honnête
*prise isolément* et le repli est le plus utilisable ; **le repli déclaré est le
moins trompeur des deux**, et la nuance est le mot « déclaré ». La liste vide
n'aurait rien affirmé de faux, mais elle aurait supprimé une donnée observée sur
209 profils, cassé le contrôle de perte, et privé #494 de tout jalon mesurable.
Un repli **non** déclaré, lui, aurait été plus trompeur que la liste vide : il
aurait rebaptisé l'ancien scalaire d'un nom qui promet une carrière.

Mesuré après changement, sur les 209 profils : 208 portent le warning de
non-corroboration, 1 ne le porte pas (`jordan-bardella`, dont tous les
`mandat_electif` sont européens et estampillés).

## Condition de retrait de `chambre` — écrite maintenant, parce que sinon

Le dépôt porte déjà des transitoires devenus permanents : les replis de lecture de
#431 et #432 sont encore là. Celui-ci a donc un critère de fin, et il est
mesurable sans jugement :

> **`chambre` est retiré du schéma quand les deux conditions sont vraies :**
>
> 1. **les consommateurs ont migré** — les emplacements recensés par #486 lisent
>    `chambres`, et le garde-fou de #494 le vérifie. Écrit depuis :
>    `tests/test_garde_fou_chambre.py`, voir [[consommateurs-chambres-migres]].
>    Le pipeline a migré ; il reste `pivotAdapter.chambreLabel` dans l'UI (#495).
> 2. **le champ n'a plus rien de propre à dire** — le warning
>    `chambres du profil non corroborée` est absent de tout le corpus, c'est-à-dire
>    que chaque chambre publiée est étayée par un `mandat_electif` estampillé.
>    **208 profils sur 209** est une *projection* : sur le corpus publié à
>    `07e9147`, aucun profil ne porte encore ni `chambres` ni ce warning (0/209),
>    faute de régénération.
>
> Au retrait, `chambres` entre dans `REQUIRED_TOP_LEVEL_KEYS` — elle en est
> volontairement absente pendant la coexistence, les 209 profils publiés ne la
> portant pas encore, et les déclarer invalides ne dirait rien de vrai sur eux.
>
> La condition 2 seule ne suffit pas (un consommateur non migré casserait), la
> condition 1 seule non plus (`chambres` deviendrait la seule source d'une
> information encore non corroborée, sans que rien ne le dise).

Le coût de la redondance en attendant est négligeable : une vingtaine d'octets par
profil, ~15 Ko à 752 profils, contre ~370 Mo projetés pour `pivot_data/profiles`.

## Un champ dérivé se recalcule, il ne se fusionne pas

C'est le symétrique du piège que #492 a rencontré sur `backfill_mandat_chambre`.
`merge_lists_by_key` est additif : `merged["mandats"]` est un **surensemble** des
mandats de l'ancien profil comme du neuf. Un `chambres` fusionné —
`_prefer_non_empty`, ou une union de listes — décrirait donc un ensemble de
mandats qui n'existe dans aucun des deux. `schema_pivot.appliquer_chambres()`
repose les deux champs **après** toute mutation de `mandats[]`, et il y en a trois :

- `merge_profile.merge_pivot_profile`, après la fusion additive et le backfill ;
- `generate_all_profiles`, aux **deux** endroits où il verse les mandats européens
  dans le pivot AN/Sénat par un `mandats.extend(...)` — sans ce recalcul, un profil
  AN + PE publierait `chambres: ["AN"]` et effacerait le mandat européen, soit
  exactement le défaut de #486 reconduit dans le champ censé le corriger ;
- `normalize_nosdeputes` / `normalize_europarl` / `mep_profile`, à la construction.

Le warning de non-corroboration suit la même règle et dans les **deux** sens : la
fusion le retire quand elle est devenue fausse (des mandats estampillés sont
revenus), et l'**ajoute** quand elle est devenue vraie. Sans ce second sens, la
seule chose qui empêche `chambres` d'être trompeuse disparaîtrait précisément sur
les profils mixtes — ceux de la migration : un run qui recollecte proprement un
mandat pendant que la fusion en conserve un ancien non estampillé produit un
profil neuf sans warning et un profil fusionné qui le mérite.

## Preuve qu'aucun dénominateur publié ne change

Simulation **en lecture seule** rejouant en mémoire les deux chemins de
`generate_all_profiles._process_candidate` sur les 209 profils de `b2c34f4`
(`--no-merge`, et fusion additive avec le pivot publié) :

| Mesure, sur les 209 profils publiés | Publié | `--no-merge` | Fusion additive |
| --- | ---: | ---: | ---: |
| divergences du scalaire `chambre` | — | **0** | **0** |
| `check_quality_gate` §3c `population_an` | 207 | **207** | **207** |
| profils contrôlés par `MAPPING_CHAMBRE_SOURCES` | 209 | **209** | **209** |
| incohérences `chambre` / `sources[].type` | 0 | — | **0** |
| `audit_diff_profils.comparer` : bloquant | — | **non** | **non** |
| profils en erreur sur `chambre == chambres[0]` | — | **0** | **0** |

`chambres` dérivée, sur les mêmes 209 : `["AN"]` × 201, `["AN", "PE"]` × 6,
`["Senat", "PE"]` × 1, `["PE"]` × 1. Les 7 profils bicaméraux AN+PE ou Senat+PE
sont exactement ceux qu'un scalaire ne pouvait pas représenter.

Deux constats **non causés par #493** apparaissent dans la même simulation et sont
signalés ici pour qu'on ne les lui impute pas : 208 changements de valeur du
scalaire `id` (`nosdeputes:<slug>` → `<slug>`), qui sont l'effet de #487 pas
encore rejoué sur le corpus, et non bloquants par construction ; et 4 pertes du
scalaire `parti` qui n'existaient que parce que la première version de la
simulation ne repassait pas `parti` au normaliseur — artefact de mesure, corrigé.

## Ce que #493 ne fait pas

- **La valeur reste à venir.** La structure est en place ; `chambres` ne dira la
  carrière qu'après un run complet, quand les 228 `mandat_electif` publiés auront
  été recollectés et estampillés. L'ordre est délibéré : la structure d'abord, la
  valeur ensuite.
- **Les 18 sénateurs publiés `AN` ne sont pas corrigés.** Aucun mandat électif
  n'est collecté pour eux, donc rien ne peut les étayer — et #488 réserve la
  collecte bicamérale aux 8 `candidat_declare`. Ils portent désormais le warning
  qui le dit, ce qui les rend visibles ; les corriger relève de la collecte, pas
  du schéma.
- **Aucun consommateur n'est migré** : c'est #494, et c'est précisément ce que la
  coexistence permet de faire un par un.

