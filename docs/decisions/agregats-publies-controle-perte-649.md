<a id="agregats-publies-controle-perte-649"></a>
# Les agrégats publiés entrent dans le contrôle de perte, et l'ordre de grandeur reste hors contrat (#649) (2026-08-31)

`2026-08-31`

> **En bref** — `amendements_agreges` et `comptages.par_statut` n'étaient regardés par aucune collection d'`audit_diff_profils` : le run `33351244845` a divisé par 5 à 32 le compteur principal de cinq fiches publiées et le commit `3c8e1f0c` est passé sans une ligne ; ils deviennent des **scalaires surveillés** — disparition et passage à `null` bloquent, la baisse de valeur est relevée — et il n'y a **pas** de quatrième catégorie bloquante sur l'ordre de grandeur, parce que la chute juste de `3c8e1f0c` (× 0,03 à × 0,21) est plus forte que la chute défectueuse d'`a125e9e` (× 0,00 à × 0,64) sur chacune des fiches et qu'aucun seuil de ratio ne les sépare ; rejeu sur les 65 transitions committées : 4 constats nouveaux, tous des pertes réelles, zéro faux positif.

## Le constat

`audit_diff_profils.py` protège les listes et quelques scalaires d'identité. Il
ne regardait **aucun** des chiffres qu'une fiche affiche en gros :

| Fiche | Clé publiée | Contenu | Surveillée avant #649 |
| --- | --- | --- | --- |
| groupe | `amendements_agreges` | 6 compteurs + `taux_adoption` + `par_type_deposant` | non |
| gouvernement | `comptages.par_statut` | 9 compteurs, dont `adopte_49_3` | non |

Le run `33351244845` du 31/08/2026 en a donné le cas réel. La correction de
[[amendements-distincts-et-signatures-643]] a divisé par 5 à 32 le compteur principal
de cinq fiches publiées, et le commit automatique `3c8e1f0c` **est passé sans
qu'aucun contrôle ne bloque ni ne signale** :

| Fiche | `par_type_deposant.depute.nb_amendements` avant | après | Facteur |
| --- | ---: | ---: | ---: |
| `AN:RN` | 1 175 535 | 37 093 | ÷ 31,7 |
| `AN:LFI` | 2 600 765 | 131 202 | ÷ 19,8 |
| `AN:SOC` | 618 368 | 54 186 | ÷ 11,4 |
| `AN:LR` | 923 446 | 156 899 | ÷ 5,9 |
| `AN:REN` | 654 775 | 132 128 | ÷ 5,0 |

Cette chute-là était voulue. Ce que le run établit, c'est qu'une chute **non
voulue** de la même ampleur passerait exactement pareil.

## Ce que corrige cette décision, et ce qu'elle refuse de corriger

[[perimetre-controle-perte]] écartait déjà ces trois blocs, en une ligne : « des
compteurs dérivés, qui bougent légitimement dans les deux sens **et dont les
listes amont sont déjà surveillées** ». La seconde moitié de ce motif est
fausse, et la mesure le montre.

Sur le run `a125e9e` — celui de [[controle-de-perte-avant-commit]] et
[[perimetre-controle-perte]] eux-mêmes — la fiche `AN:LFI-16` perd ses 11 561
amendements (→ **0**) et son `taux_adoption` passe de `0.0476` à **`null`**,
pendant que `membres` (3), `cohesion_votes` (1 996) et `mandats_agreges` (50)
restent identiques à l'entrée près. **Aucune liste amont ne bouge sur cette
fiche.** Le contrôle bloquait bien ce run-là, mais sur SOC-16 et REN-16 ; sur
LFI-16 il n'avait rien à dire.

La première moitié du motif, elle, tient — et c'est elle qui décide du régime.

## La décision

**Les agrégats deviennent des scalaires surveillés, pas des listes stables.**
Autrement dit : leur **disparition** et leur passage à `null` bloquent ; la
**baisse de leur valeur** est relevée sans bloquer.

| Collection | Ce qui entre | Régime |
| --- | --- | --- |
| groupes | `amendements_agreges` (présence du bloc) | scalaire — bloque sur `null` |
| groupes | `amendements_agreges.nb_amendements` | scalaire |
| groupes | `amendements_agreges.taux_adoption` | scalaire |
| groupes | `amendements_agreges.par_type_deposant.depute.nb_amendements` | scalaire |
| groupes | `amendements_agreges.par_type_deposant` | liste stable — `len()`, 4 catégories |
| gouvernements | `comptages` (présence du bloc) | scalaire |
| gouvernements | `comptages.par_statut` (présence du bloc) | scalaire |
| gouvernements | `comptages.par_statut.adopte_49_3` | scalaire |
| gouvernements | `comptages.par_statut.rejete_49_3` | scalaire |

Chaque inclusion a sa mesure, et chaque exclusion son motif :

| Écarté | Motif |
| --- | --- |
| `nb_adoptes`, `nb_rejetes`, `nb_irrecevables`, `nb_retires_ou_tombes`, `nb_sort_non_renseigne`, `nb_sort_non_reconnu`, `nb_sans_identifiant` | Même fabrique que `nb_amendements` (`schema_groupe.make_empty_amendements_stats`) : ils ne peuvent pas disparaître seuls. Aucun événement de plus, seulement des lignes de rapport. |
| `amendements_agreges.signatures` (#643) | Un seul état commité au 31/08/2026, celui de son apparition. Surveiller un champ dont la seule transition observée est sa naissance serait une intuition, pas une mesure. |
| `effectif.actuel`, `min_historique`, `max_historique` | Motif inchangé depuis #470 : un compte de membres actifs baisse légitimement quand un élu quitte le groupe (REN-16 50 → 77 dans l'autre sens, même run). |
| Les 7 autres statuts de `par_statut`, et la **valeur** des 9 | `validate_profil_gouvernement` compare les clés à `KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL` et fait échouer la porte de qualité sur une clé manquante : second verrou sur le même événement, l'argument qui écarte déjà `chambres` côté profils. Et une baisse par statut est la contrepartie **normale** d'une requalification — le run `720110d2` a déplacé 27 textes de `BORNE` vers `adopte_cmp` et 19 vers `promulgue` en une passe. La perte réelle serait que `textes` rétrécisse, et `textes` est déjà une liste stable bloquante. |
| `cohesion_votes[].membres_eligibles` | La **valeur** d'une entrée de liste, jamais comparée par cet outil ; il a bougé de 4,8 à 30,9 en moyenne sur `AN:SOC` au même run. Nommé désormais dans le « hors périmètre » du rapport plutôt que tu. |

`comptages` mérite un mot de plus : la clé figure dans
`REQUIRED_TOP_LEVEL_KEYS`, mais `validate_profil_gouvernement` accepte
`comptages: null` **sans un mot** — la clé est là, les neuf compteurs publiés
ont disparu. C'est la seule des quatre entrées « présence de bloc » qui ferme
un trou que rien d'autre ne couvre.

## Un compteur à zéro n'est pas une absence de compteur

Rien à changer : `_resume_scalaire` rend `0` et `False` tels quels et ne teste
que `is None`. La conséquence est double, et les deux moitiés comptent :

- `nb_amendements` 11 561 → **0** est un **changement de valeur**, relevé, non
  bloquant — un groupe qui n'a rien déposé a bien zéro amendement (§2 règle 5) ;
- `rejete_49_3` **0 → `null`** est en revanche une **régression bloquante** :
  zéro est une mesure, l'absence n'en est pas une.

## La troisième question : pas de quatrième catégorie bloquante

Le contrôle bloque sur trois constats — un fichier disparu, une baisse de liste
stable, un scalaire surveillé passant de renseigné à `null`. Une chute de × 20
sur un compteur n'entre dans aucun. Fallait-il un quatrième ?

**Non**, et la raison est une mesure, pas une prudence. Les deux seules chutes
d'ordre de grandeur du corpus se rangent dans le mauvais sens :

| Run | Nature | Facteurs observés |
| --- | --- | --- |
| `a125e9e` | **défaut réel** (#460 / #470) | `AN:LFI-16` × 0,00 · `AN:SOC-16` × 0,52 · `AN:LR-16` × 0,64 |
| `3c8e1f0c` | **correction juste** (#643) | les cinq fiches entre × 0,03 et × 0,21 |

La chute légitime est **plus forte que la chute défectueuse sur chacune des
fiches**. Aucun seuil de ratio ne les sépare : réglé pour attraper `a125e9e`
(× 0,64) il aurait bloqué `3c8e1f0c`, c'est-à-dire le run qui corrigeait le
défaut. Il aurait fallu cocher `allow_declared_losses`, une tolérance de corpus
qui désarme du même coup les contrôles précis par profil — l'échange que ce
fichier refuse déjà pour les index partagés.

Ce qui change n'est donc pas le blocage, c'est le **silence** : la chute de
× 20 apparaît désormais comme un changement de valeur, trois lignes par fiche,
à charge de relecture humaine.

## Ce que le correctif attrape, mesuré sur tout l'historique

Rejeu de `comparer()` sur les **39 transitions committées** de
`pivot_data/groupes` et les **26** de `pivot_data/gouvernements`, avec les
champs de #649 isolés :

| Transition | Fiche | Constat nouveau | Verdict |
| --- | --- | --- | --- |
| `51d6d4c3` → `98111f75` (03/08) | `AN:SOC-16` | `taux_adoption` 0.1991 → `null`, `nb_amendements` 437 → 0 | perte réelle — `membres` (1) et `cohesion_votes` (814) inchangés |
| `3d0ec252` → `d9cbca67` (06/08) | `AN:REN-16`, `AN:RN-16`, `AN:SOC-16` | `taux_adoption` → `null` sur trois fiches, compteurs → 0 | perte réelle — mêmes listes inchangées |
| `0fb4369f` → `a125e9e0` (19/08) | `AN:LFI-16` | `taux_adoption` 0.0476 → `null` | perte réelle — celle que #470 n'a pas vue |
| `be960bce` → `3c8e1f0c` (31/08) | 5 fiches | 15 changements de valeur | **non bloquant**, comme voulu |
| les 35 autres transitions de groupes | — | aucun | — |
| les 26 transitions de gouvernements | — | aucun | — |

**Quatre constats bloquants nouveaux sur 65 transitions, tous des pertes
réelles, zéro faux positif.** Le prochain run reste committable sans tolérance
tant qu'un agrégat ne s'effondre pas à `null`.

Une réserve, écrite parce qu'elle est le seul faux positif possible : le jour
où un groupe cesse **légitimement** de porter des amendements, son
`taux_adoption` passera à `null` et il faudra le déclarer une fois via
`allow_declared_losses`. C'est le bon coût — « zéro amendement publié pour un
groupe qui en portait 132 960 » est exactement ce qu'un humain doit confirmer.
Aucune occurrence en 39 transitions.

## Alternative écartée

**Un seuil de ratio bloquant (× 0,5, × 0,1…).** Écarté par la mesure ci-dessus :
il n'existe pas de seuil qui attrape `a125e9e` sans attraper `3c8e1f0c`. Un
seuil qui se déclenche sur trois runs de correction de clé en trois semaines
(#440, #643, et la reprise d'`a125e9e`) est une tolérance qu'on coche par
habitude, et une tolérance cochée par habitude ne protège plus de rien.

## Ce qui reste vrai

`allow_declared_losses` ne désarme pas le contrôle : il déclare une perte
connue (AGENTS.md §3c), et sa tolérance reste cloisonnée de celles des trois
autres gardes pré-commit.
