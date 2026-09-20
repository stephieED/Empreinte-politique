<a id="doublons-textes-europeens-cle-doceo-901"></a>
# Un texte européen est identifié par son document, pas par son titre (#901) (2026-09-16)

`2026-09-16`

> **En bref** — 311 textes portés européens étaient publiés deux fois dans le
> même profil : Philippot 250 (502 affichés pour 252 réels), Le Pen 57,
> Mélenchon 4. Sans `dossier_id`, un texte européen était rangé sur le repli
> `(titre, date_min, legislature)` ; #938 a nettoyé les titres, et chaque texte est
> revenu comme une entrée neuve. `_pivot_texte_key` identifie désormais un texte
> européen par son **document `doceo`**, et une reprise nommée retire les 311
> copies déjà publiées.

## Contexte

Le défaut a été trouvé par accident, en mesurant autre chose : 314 entrées
européennes sans `titre_langue`, là où le champ venait d'être posé partout. Elles
étaient les **anciennes copies** de textes publiés deux fois.

Les 311 paires ne diffèrent que par deux champs :

| Champ | Copie ancienne | Copie récente |
| --- | --- | --- |
| `titre` | « …goods and services **PDF (181 KB) DOC (45 KB)** » | « …goods and services » |
| `titre_langue` | absent | `"en"` |

Le défaut précède les lots du 16/09 : il est présent sur `57783fca7`. Il a faussé
**tous** les dénombrements européens de la journée — « 694 textes portés »,
« 628 sans dossier » — qui comptaient les doublons. Les chiffres justes : **383**
textes distincts, dont **56** rattachés à un dossier.

## C'est exactement l'alternative que la clé avait écartée

La docstring de `_pivot_texte_key` (#668) rejetait « keyer toujours sur le
repli » pour une raison précise : *« une correction typographique du titre […]
republierait le dossier comme une entrée neuve »*. La règle tenait pour les textes
de l'Assemblée, qui ont un `dossier_id`. Elle ne protégeait pas les textes
européens, qui n'en ont pas et tombaient donc **tous** sur le repli. #938 a été
cette correction de titre.

## Décision

Entre `dossier_id` et le repli, une branche : pour une entrée
`institution == "parlement_europeen"` dont `source_url` désigne un document
`doceo`, la clé est `("doceo", "B-8-2017-0240")`.

- **Le schéma de l'URL n'est pas lu.** 625 `source_url` sont en `http://`, 56 en
  `https://` : une clé qui les distinguerait rejouerait la bascule de #668 le jour
  où la collecte changera de forme.
- **681 des 694 entrées** portent un document, et aucun n'est partagé par deux
  textes réellement différents d'un même profil.
- Les **13** entrées sans document (fiches OEIL, avis sans lien) gardent leur clé :
  rien ne change pour elles. Les textes de l'Assemblée non plus.

## Pourquoi pas `reference_dossier`

Elle existait déjà, et elle aurait été fausse. Elle désigne une **procédure**, et
plusieurs textes vivent dans la même : chez Emmanuel Maurel, l'avis « OPINION on
the role of EU development policy… » et la fiche du dossier dont il est
rapporteur partagent `2023/2031(INI)`. Une clé sur la référence en aurait
supprimé un — une perte silencieuse, de celles que le contrôle de perte ne voit
que comme une cardinalité.

## La reprise

La fusion additive ne retire jamais ce qui est publié, et le contrôle de perte
aurait bloqué le run qui tentait de le faire. `scripts/purger_doublons_textes_europeens_901.py`
réapplique `merge_dossier_records` avec la nouvelle clé — ce que la fusion fera
d'elle-même au prochain run, sans en inventer un second chemin.

Vérifié profil par profil : seul `textes_portes` change ; les 311 entrées retirées
portent **toutes** un titre sale ; 0 texte de l'Assemblée retiré. Un seul étage :
le brut ne porte aucune adresse `doceo` sur les trois profils.

La perte est **déclarée**, jamais contournée (§3c) : 311 entrées de moins sur une
liste stable, c'est exactement ce que `audit_diff_profils` doit bloquer tant que
personne ne l'a nommée.

## Ce que ce lot ne fait pas

**Trois titres restent sales, et ce ne sont pas des doublons** : chez Philippot
`B-8-2016-0621` et `B-8-2015-1183`, chez Le Pen `B-8-2016-0621`. Chacun est seul
sous sa clé — la collecte ne les rend plus, la fusion additive les conserve. Les
nettoyer est un autre geste que retirer une copie.

## La leçon, qui vaut au-delà de ce lot

Le lot du même jour sur le titre français (#960) avait été testé sur un titre
**inventé**, « …(A9-0227/2024) », qu'aucun des 694 titres réels ne ressemble, et
il n'a produit aucun titre français. Les tests de ce lot-ci sont écrits sur des
entrées **copiées du corpus** — les deux copies réelles de `B-8-2017-0240`, l'avis
et le dossier réels de Maurel —, et quatre d'entre eux échouent sur l'ancienne
clé.
