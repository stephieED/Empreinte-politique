<a id="chambre-par-mandat-electif"></a>
# La chambre est un fait du mandat, pas du profil : `mandats[].chambre` estampillée à la collecte (#492) (2026-08-20)

`2026-08-20`

> **En bref** — la chambre est un fait du mandat, estampillé à la collecte, pas une propriété du profil.

Sous-issue C de l'épic **#486**, après #488 (sous-issue B). Ne touche pas à
`chambre` au niveau profil (sous-issue D, `needs-human`), ne corrige pas le
profil de Mélenchon (#484), n'ajoute aucun mandat à aucun profil.

## Le défaut

Les `mandat_electif` ne portaient **aucun marqueur de chambre**. Les libellés
publiés sont « Mandat parlementaire (Les Républicains) », « Mandat parlementaire
(Renaissance) » — identiques qu'on siège au Palais-Bourbon ou au Luxembourg.
Seuls les mandats européens étaient explicites (« Mandat de député européen »,
14 occurrences). L'information n'était pas seulement non affichée : elle n'était
pas portée, et l'UI (sous-issue F) n'aurait eu aucun moyen de distinguer les deux
expériences parlementaires d'un candidat.

## La méthode suggérée par l'issue ne tient pas, et la mesure le dit

#492 proposait de dériver la chambre du `source_url` — « les fiches AN portent
`assemblee-nationale.fr`, les sénatoriales `archive.nossenateurs.fr` » — en
signalant que le champ était « à `None` sur plusieurs mandats ». Mesuré sur
`f5a828b`, sur les **228 `mandat_electif` des 209 profils publiés** :

| `source_url` sur un `mandat_electif` | Mandats |
| --- | ---: |
| absent | **214** |
| présent, `www.europarl.europa.eu` | **14** |
| présent, `assemblee-nationale.fr` | **0** |
| présent, `archive.nossenateurs.fr` | **0** |

Le champ n'est pas « souvent vide » : il est **systématiquement** vide sur les
mandats AN et Sénat, et systématiquement rempli sur les seuls mandats européens.
`candidate_profile._extract_mandats` ne l'a jamais renseigné sur un mandat
électif. La méthode proposée aurait donc pu établir exactement la distinction
qu'on n'a pas besoin d'établir (le PE se lit déjà dans le libellé) et aucune de
celle qu'on cherche. Pour situer, la couverture de `source_url` par catégorie sur
les 16 853 mandats du corpus : `groupe_politique` 398/398 (le champ y est
obligatoire, règle 6), `fonction_gouvernementale` 107/319, `autre` 88/174,
`commission` 75/5 285, `mandat_electif` 14/228, toutes les autres 0.

## Ce qui a été fait : estampiller à la collecte

`candidate_profile.build_profile(chambre, slug)` **sait** de quel jeu de données
vient le mandat qu'il fabrique — c'est son paramètre. La chambre est donc écrite
sur le mandat au moment où il est construit, dans le vocabulaire brut
(`deputes` / `senateurs`), et traduite en nomenclature pivot (`AN` / `Senat` /
`PE`) par `normalize_nosdeputes` / `normalize_europarl`.

Sémantique exacte du champ, et elle compte : **la chambre dont le jeu de données
a rendu ce mandat**. C'est un fait de collecte traçable (§2.2), pas une
qualification juridique déduite. Le profil de Retailleau reste un contre-exemple
utile : son unique `mandat_electif` débute le 2004-09-26 — la date du
renouvellement sénatorial — et reste ouvert, tout en venant de
`www.nosdeputes.fr`. #492 ne tranche pas ce cas ; elle le rend **visible sur le
mandat** au lieu de le laisser au seul niveau profil.

## La chambre est lue sur le mandat, jamais sur le profil

Le raccourci tentant — reprendre `raw_profile["chambre"]` pour tous les mandats
du profil — est faux, et le corpus le prouve. La fusion additive
(`merge_profile.merge_lists_by_key`) accumule dans un même profil des mandats
collectés lors de runs différents, donc sous des chambres potentiellement
différentes. Mesuré sur `f5a828b` : le profil brut de `jean-luc-melenchon` porte
`chambre: "senateurs"` et **trois** `mandat_electif`, dont deux manifestement AN
(2017-2022, groupe LFI). Reprendre la chambre du profil aurait estampillé
« Sénat » deux mandats de l'Assemblée — un fait faux de plus, exactement ce que
l'épic #486 reproche au champ de niveau profil.

C'est aussi ce qui distingue ce champ de `chambre` au niveau profil : dériver la
chambre d'**une personne** de « quel site a répondu » est faux, parce qu'une
carrière n'est pas réductible à une chambre ; dériver la chambre d'**un mandat**
du jeu de données qui l'a rendu est exact, parce que ce mandat vient de là.

## Correction au diagnostic : les deux chambres se rencontrent déjà, dans la CI

#488 note qu'elle « ne fusionne pas les deux profils bruts », et #492 en déduit
qu'aucun profil ne porte de mandats des deux chambres. C'est vrai de
`build_profile_any_chambre` ; **c'est faux du pipeline**. `generate-data.yml`
lance deux passes scopées — `extract-an` (`--source an`) et `extract-senat`
(`--source senat`) — dont les profils bruts se retrouvent dans
`merge_profile.merge_raw_dirs`, additivement, pour le **même slug**. Un candidat
présent des deux côtés y accumule donc déjà les `mandat_electif` des deux
chambres dans un seul `mandats[]`. C'est la trace qu'on lit sur
`jean-luc-melenchon` : profil brut `senateurs`, trois `mandat_electif`, dont deux
AN. Le ROADMAP note déjà cette voie pour le scalaire `chambre` (« artifact merge
order », sous-issue D) ; elle vaut aussi pour les mandats.

Deux conséquences. L'estampille sert **dès le prochain run complet** : les
mandats AN et Sénat d'un même candidat arriveront dans le même profil, chacun
portant sa chambre — ce dont l'UI (sous-issue F) a besoin, sans travail de fusion
supplémentaire. Et le filtre d'éligibilité par chambre n'est pas une précaution
théorique : c'est le garde-fou de cette voie-là.

## Le `null`, et pourquoi un seul warning par profil

Un mandat collecté avant #492 ne porte pas d'estampille, et sa chambre **n'est
pas reconstituable a posteriori** : ni par `source_url` (mesuré nul ci-dessus),
ni par la chambre du profil (démonstration ci-dessus). Il est publié à `null`,
jamais à une valeur par défaut (§2.5).

Le warning est **agrégé par profil**, pas émis par mandat, et il porte le compte.
Ce cas n'est ni celui de #474 — les 92 parlementaires en mission sont écartés
**sans** warning, parce que leur exclusion est le comportement attendu et
permanent — ni tout à fait celui de #488, où chaque échec de chambre est une
panne et mérite sa ligne. Ici le `null` est déterministe, uniforme et
**transitoire** : le compte est précisément la mesure qui dira quand la migration
est terminée. Un warning par mandat produirait 214 occurrences sur 189 profils
là où `audit_pivot_dataset.compute_agregation_warnings`, qui agrège par préfixe,
n'en montrerait de toute façon qu'une ligne.

## Le report à la fusion, sans lequel le champ ne se remplirait jamais

`merge_lists_by_key` est additif pur : l'entrée ancienne gagne, et la clé d'un
mandat (`categorie`, `fonction`, `label`, `debut`) ne contient pas la chambre. La
version neuve, estampillée, porte donc la **même clé** que l'ancienne et serait
écartée à chaque régénération : le champ resterait à `null` pour toujours en
fusion additive, et ne se remplirait qu'en `cold_start` / `--no-merge`.

`merge_profile.backfill_mandat_chambre`, appelée aux deux niveaux de fusion
(brut et pivot), reporte donc la chambre d'un mandat neuf sur l'entrée ancienne
de même clé. Le report est strictement croissant en information : il ne remplit
qu'un champ **absent ou nul**, n'écrase jamais une chambre déjà déterminée, ne
touche aucun autre champ, ne réordonne ni ne duplique rien, et reconstruit
l'entrée au lieu de muter l'objet de l'appelant. Il est **volontairement limité à
`chambre`** : généraliser le report ferait de la fusion additive une fusion par
champ, ce qu'elle n'est pas.

*Alternative écartée* : mettre la chambre dans la clé de fusion. Elle
dédoublerait chaque mandat déjà connu au premier run estampillé — un mandat en
double, c'est un `debut_dans_groupe` faux et un `mandats_agreges` gonflé.

## Le risque de dénominateur (§2.7) : corrigé ici, sans effet aujourd'hui

`group_profile._member_eligibility_intervals` retenait **tous** les
`mandat_electif` sans distinction de chambre, et `_is_eligible_at` renvoyait
`True` dès qu'une date tombait dans n'importe lequel — une union. Un mandat
sénatorial ne peut pas chevaucher un mandat AN (incompatibilité
constitutionnelle), donc dans le cas général l'union est inoffensive ; le cas
dangereux est le **changement de chambre en cours de législature**, qui prolonge
la fenêtre d'éligibilité au-delà du départ de l'Assemblée et compte le membre
absent sur des scrutins qu'il ne pouvait plus voter.

Le filtre est écrit ici parce que #492 le rend écrivable pour la première fois :
avant, aucun mandat ne portait de chambre. `_mandats_electifs(mandats, chambre)`
restreint à la chambre du groupe, et la chambre est passée depuis
`build_groupe_profile` à `_derive_membre_entry`, `_compute_cohesion_votes`,
`_aggregate_mandats` et `compute_ecarts_cohesion_internes`.

Deux règles qui font tout l'écart entre corriger et casser :

- **un mandat à `chambre: null` est conservé.** L'écarter réduirait un
  dénominateur publié sur la foi d'une donnée absente — l'erreur exactement
  symétrique de celle qu'on corrige. Conséquence directe et mesurée : sur le
  corpus d'aujourd'hui, où les 214 `mandat_electif` AN/Sénat sont tous à `null`,
  **ce filtre ne change aucun dénominateur publié**. La correction entre en
  vigueur au fil de la collecte, mandat par mandat, jamais d'un coup ;
- **« aucun mandat électif » et « des mandats électifs, mais aucun dans cette
  chambre » ne sont pas la même chose.** Le premier reste `None` → éligible par
  défaut (absence d'information, comportement historique). Le second renvoie `[]`
  → jamais éligible : ce n'est pas une absence d'information, c'est
  l'information que ce membre ne siège pas dans cette chambre.

**Mesuré vs projeté.** L'exposition réelle au défaut est **nulle aujourd'hui**,
et le dénominateur d'un groupe est borné à sa seule législature — ce n'est pas
une fraction des 17 535 scrutins de l'index. Mesuré sur `f5a828b`, sur les 7
profils de groupe publiés :

| Groupe | `cohesion_votes` | Candidats déclarés parmi les membres |
| --- | ---: | --- |
| `AN-REN-16` | 4 099 | `gabriel-attal` |
| `AN-RN-16` | 3 405 | `marine-le-pen` |
| `AN-LR-16` | 2 232 | — |
| `AN-LFI-16` | 1 996 | — |
| `AN-SOC-16` | 814 | `jerome-guedj` |
| `Senat-LR` | **0** | `bruno-retailleau` |
| `Senat-SER` | **0** | — |

Deux raisons indépendantes, chacune suffisante : les trois candidats siégeant
dans un groupe à dénominateur réel viennent tous d'un profil brut
`chambre: "deputes"` (le seul profil brut `senateurs` du corpus est
`jean-luc-melenchon`, qui n'est membre d'aucun groupe publié) ; et le seul
bicaméral, `bruno-retailleau`, est dans un groupe à `cohesion_votes: 0` —
aucun jeu de données Sénat structuré n'étant exploitable (§ *Senate votes,
amendments, sponsored texts*). Ce qui est corrigé ici est donc une **exposition
future**, celle qu'ouvrirait toute publication de mandats des deux chambres sur
un même profil.

*Repli écarté, vérifié plutôt que supposé* : filtrer sur les mandats
`groupe_politique` au lieu de la chambre. Ils existent sur **188 des 209
profils**, 398 mandats — dont **0 sans date de fin**. Ils ne couvrent donc pas la
législature en cours et ne peuvent pas servir de fenêtre d'éligibilité.

## Ce que ça change sur le corpus, mesuré à vide

Aucune régénération n'a été lancée ; les chiffres ci-dessous viennent d'une
simulation en lecture seule sur `f5a828b` (normalisation des 209 profils bruts
committés, fusion avec les pivots publiés, en mémoire).

- **0** des 209 pivots publiés devient invalide avec la nouvelle règle de schéma ;
- après une passe `--pivot-only` (aucun appel réseau) : 228 `mandat_electif`, dont
  **14 estampillés `PE`** (le chemin européen est immédiatement déterminé) et
  **214 à `null`**, portés par **189 profils** qui reçoivent chacun **un** warning ;
- les 214 restants s'estampillent à leur prochaine collecte réelle, via le report
  de fusion.

## Périmètre

Le champ n'est écrit que sur les `mandat_electif`. La chambre d'une commission ou
d'un groupe d'amitié est un fait réel, mais non publié en v1 : l'inventer sur
16 625 mandats pour l'homogénéité du dictionnaire serait la même faute, en plus
volumineux.

Aucun mandat n'est fusionné entre chambres par ce changement : un profil de
candidat bicaméral continue de ne publier que les mandats de la chambre retenue
par #488. Publier les deux suppose de trancher `chambre` au niveau profil — c'est
la sous-issue D (#493, `needs-human`), et #492 ne la préempte pas.

