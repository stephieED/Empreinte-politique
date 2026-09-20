<a id="purge-mandats-nosdeputes-718"></a>
# 331 mandats écrits par NosDéputés étaient encore publiés, sans le nom de leur source (#718) (2026-09-17)

`2026-09-17`

> **En bref** — #976 a conclu qu'aucun champ publié ne dérivait plus de
> NosDéputés, en cherchant le nom de la source dans les données. **331 entrées de
> mandat** en venaient pourtant, sur 32 profils, sans le porter. Elles rangeaient
> en `commission` des groupes politiques et des missions, ou doublaient un mandat
> de l'AN avec une fin fausse. Arbitré le 17/09/2026 : toutes purgées, aux deux
> couches.

## D'où elles viennent

Retrouvé dans l'historique git. La première collecte (29/07/2026, commit
`0a404f752`) interrogeait NosDéputés : les profils de `jerome-guedj`,
`edouard-philippe`, `marine-le-pen` et `jean-luc-melenchon` y ont pour source
`nosdeputes.fr`, et portent déjà ces entrées à l'identique. `_extract_mandats`
rangeait alors en dur en `commission` toutes les `responsabilites` et
`historique_responsabilites` de l'API, quelle que soit la nature de l'organe, et
écrivait un « Mandat parlementaire (groupe) » par législature.

Quand l'AN est devenue la source (#369, #529), ses mandats sont arrivés **à côté** :
la fusion additive garde l'ancien, et la clé brute contient `type`, que
NosDéputés écrivait en minuscules (`membre`) et AMO30 capitalise (`Membre`).

## Ce qui a été mesuré

Sur `origin/main` `186375320`, au pivot, les 1 177 profils lus un par un :

| Population | Entrées | Profils |
| --- | ---: | ---: |
| 32 `candidat_declare` | 57 | 6 |
| 1 145 `roster_groupe` | 274 | 26 |
| **total** | **331** | **32** |

Par catégorie : `commission` 296, `mandat_electif` 33, `groupe_amitie` 1,
`extra_parlementaire` 1. Mêmes chiffres au brut.

Sur les 32 candidats déclarés, 28 des 57 doublaient un mandat que l'AN établit
dans le même profil (même organe, même date de début). NosDéputés relayait les
dates de l'AN, mais fermait une période le jour où la suivante commence, ou la
laissait `null`. Une fin `null` publiait un mandat **encore en cours** :
Jean-Luc Mélenchon membre actif de la commission des affaires étrangères depuis
le 14/01/2022, Marine Le Pen depuis le 30/06/2022.

Les autres n'avaient pas d'équivalent établi : groupes politiques rangés en
`commission` (`Députés Non Inscrits`, `Renaissance`, `La France Insoumise`…),
missions, groupes de travail, commissions d'enquête.

## Décision

1. **Signature** (`src/purge_mandats_nosdeputes.py`) : une entrée de `mandats[]`
   sans `categorie_source`, dont la fonction (`type` au brut, `fonction` au pivot)
   commence par une minuscule. Toute source vivante écrit `categorie_source`
   (#718) ; NosDéputés écrivait ses fonctions en minuscules.
2. **Les deux conditions ensemble.** Quatre entrées sans estampille ont une
   fonction capitalisée (deux `Gouvernement`, deux missions de 2026) : elles ne
   sont pas de NosDéputés et restent. Le « Mandat parlementaire » que l'AN produit
   aujourd'hui a `type: "mandat"`, mais il est estampillé : il reste.
3. **Toutes purgées**, y compris celles sans équivalent établi : arbitré le
   17/09/2026. Appliqué aux deux couches (#729), 331 entrées chacune. Seul
   `mandats` change ; `chambres` est recomposé et ne bouge sur aucun profil ; aucun
   profil ne perd son dernier mandat électif. Une seconde passe ne retire rien.
4. **`AGENTS.md` §7** dit de nouveau vrai : aucun champ publié ne dérive plus de
   NosDéputés, mesuré le 17/09/2026. Les fiches de groupe et de lignée se
   recomposent au run suivant.

## Alternatives rejetées

- **Ne purger que les doublons d'un mandat AN** (première version de cette PR,
  28 entrées sur 4 candidats). Elle laissait 303 entrées NosDéputés publiées, et
  l'attribution ODbL due.
- **Filtrer à l'affichage sur `categorie_source`.** Le corpus aurait continué de
  publier une donnée d'une source retirée, et les fiches de groupe l'auraient
  agrégée.
- **Relancer `purge_mandats_dupliques.py` (#387).** Il rend 0 : il protège toute
  entrée dont l'identité `(categorie, label, debut)` est celle d'un mandat AN.

## Ce que ça coûte

Des appartenances réelles que l'AN ne sert pas sous ce nom disparaissent : un
passage de cinq jours chez les non-inscrits, un groupe de travail, une mission.
Elles n'étaient pas sourcées par une source vivante, et le lecteur ne pouvait pas
les distinguer d'un mandat établi.

## Leçon

Chercher le nom d'une source dans les données ne prouve pas son absence : une
entrée peut n'en porter aucune trace. La signature se cherche dans la **forme**
de ce que la source écrivait.
