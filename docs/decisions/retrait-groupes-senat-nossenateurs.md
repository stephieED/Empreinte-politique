<a id="retrait-groupes-senat-nossenateurs"></a>
# Les deux groupes du Sénat et leurs lignées sont retirés : ils dérivaient de NosSénateurs (2026-09-16)

`2026-09-16`

> **En bref** — `groupe-Senat-LR`, `groupe-Senat-SER` et leurs lignées étaient les
> **seules données de `pivot_data/`** encore issues de NosSénateurs. Gelés depuis
> #516, sortis de l'interface par #885, ils restaient versionnés dans le dépôt
> public, lus par personne. Leurs quatre fichiers et leurs entrées de
> `raw_data/groupes_reels.json` sont retirés dans le même commit. Arbitré par la
> propriétaire le 16/09/2026.

## Contexte

La session interface voulait retirer NosDéputés/NosSénateurs de la page `/sources`
et demandait, avant d'écrire qu'ils étaient partis, s'il restait des données qui
en dérivent.

Mesuré sur `origin/main` `dc80a10cb`, par un parcours récursif de tous les `.json`
de `pivot_data/`, clés et valeurs :

| Collection | Occurrences | Nature |
| --- | ---: | --- |
| `profiles/` (1 177 profils) | 0 | — |
| `gouvernements/` | 0 | — |
| `groupes/` | 30 fichiers | **texte seulement** : 29 `meta.warnings[]` disant que la composition « ne vient plus » de nosdeputes.fr, 1 `preuve` |
| `meta.licence_donnees` citant Regards Citoyens | 0 | — |

Aucune valeur ne portait la trace de la source. **Mais le code, lui, le disait** :
`src/group_profile.py` écrit que `groupe-Senat-LR` et `groupe-Senat-SER` « dérivent
de NosSénateurs ». Leurs deux lignées, régénérées à chaque run à partir d'eux, en
héritaient. `groupe-Senat-LR` portait `effectif.actuel = 1`, `sources: []` : une
valeur dont rien ne disait plus l'origine.

**Leçon de la mesure** : chercher le nom d'une source dans les données ne suffit
pas à conclure qu'aucune donnée n'en dérive. Une valeur ne porte pas toujours son
origine ; le code qui l'a produite, si.

## Décision

Retirer les quatre fichiers et les quatre entrées de configuration (deux groupes,
deux lignées) **dans le même commit**.

## L'arbitrage renversé, et pourquoi

#516 avait choisi de **suspendre sans retirer** : `extraction_suspendue` gardait les
entrées dans la configuration, parce qu'un fichier disparu fait avorter le commit
du run (#460/#470). « Une migration ne se paie pas en cassant ce qui est déjà
publié. »

Deux faits l'ont renversé :

1. **#885 a sorti ces fiches de l'interface** (`CHAMBRE_HORS_INTERFACE = 'Senat'`
   dans `sync-data.mjs`) : il n'y avait plus rien de publié à ne pas casser.
2. **Ce qui restait était une donnée dérivée d'une source retirée**, versionnée
   dans un dépôt public — exactement ce que la sortie de Regards Citoyens (#529,
   #530) cherchait à éteindre.

La raison technique de #516 ne tient plus non plus : les fichiers et leurs
entrées partent **ensemble**. Le run suivant part d'un état où ils n'existent
pas, ne les régénère pas, et ne voit donc aucune disparition.

## Vérifié

- Contrôle de perte (`audit_diff_profils.py --ref HEAD`) : **4 constats bloquants,
  exactement ces quatre fichiers**, et rien d'autre.
- Suite complète : les trois tests qui gelaient l'ancien arbitrage
  (`test_les_deux_entrees_senat_restent_dans_la_config`, et les deux textes de
  preuve de `test_ordre_preuve_suspension_885.py`) sont remplacés par un test qui
  tient le nouveau : aucune entrée `chambre == "Senat"` dans les groupes ni dans
  les lignées.

## Ce que ce retrait ne change pas

- **Les appartenances sénatoriales des candidats déclarés** (#885, `data.senat.fr`,
  Licence Ouverte) restent collectées et publiées : ce ne sont pas des fiches de
  groupe.
- **Les phrases** des 29 `meta.warnings[]` de groupes AN qui nomment nosdeputes.fr
  restent : elles disent que la donnée n'en vient **pas**.

## Alternative écartée

**Garder les fiches et écrire « aucune donnée publiée par le site n'en dérive ».**
Vrai pour le site, faux pour le dépôt. Et la réserve se serait relue comme une
imprécision le jour où quelqu'un aurait téléchargé `pivot_data/`.
