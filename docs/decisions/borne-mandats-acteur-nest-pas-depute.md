<a id="borne-mandats-acteur-nest-pas-depute"></a>
# « Acteur » n'est pas « député » : la preuve de couverture publiée affirmait plus que la mesure (2026-09-12)

`2026-09-12`

> **En bref** — la preuve de couverture des mandats, publiée sur **2 337 entrées** du corpus, disait « AMO30 ne rattache **aucun acteur** à un mandat antérieur à la XIIe — 3 117 acteurs, plus ancien `mandat_debut` d'acteur 2002-06-19 » ; **c'est faux du fichier** : le plus ancien mandat qu'il porte est du **02/10/1980** (un groupe du Sénat), et 192 mandats `SENAT`, 123 `COMSENAT`, 75 `GROUPESENAT` commencent avant le 19/06/2002 ; **la mesure juste porte sur les mandats de député** — le plus ancien `ASSEMBLEE` est bien du 19/06/2002 ; la cause est un mot : **« acteur » n'est pas « député »**, et sur les 3 117 acteurs du référentiel, **2 122** ont siégé à l'Assemblée, **905 sont des sénateurs qui n'y ont jamais siégé**, 90 n'ont qu'une fonction gouvernementale ; la phrase publiée dit désormais « aucun **mandat de député** antérieur à la XIIe », avec sa mesure refaite le 12/09/2026 ; relevé par la propriétaire, qui a trouvé l'URL du jeu de données et s'est étonnée que son nom annonce la **XIe** ; le commentaire du code avait vu une partie du défaut — il notait des « mandats d'ORGANES » remontant à 1998 — mais la formulation publiée avait perdu la distinction, et la date elle-même était trop récente de dix-huit ans.

## 1. Ce qui était publié

> « l'Assemblée nationale publie l'état civil et les mandats de ses élu·es depuis la XIe législature (juin 1997), mais son référentiel historique AMO30 **ne rattache aucun acteur à un mandat antérieur à la XIIe** — mesuré le 28/08/2026 : 3 117 acteurs, plus ancien `mandat_debut` d'acteur 2002-06-19 (XIIe) »

## 2. Ce que l'archive contient, mesuré le 12/09/2026

| Type d'organe | Mandat le plus ancien |
| --- | --- |
| `GROUPESENAT` | **1980-10-02** |
| `SENAT` | 1998-10-01 |
| `COMSENAT`, `DELEGSENAT`, `HCJ`, `CJR` | 2001 |
| **`ASSEMBLEE`** | **2002-06-19** |

Et la population du référentiel :

| Acteurs | Nombre |
| --- | ---: |
| ayant siégé à l'Assemblée | 2 122 |
| **sénateurs, jamais députés** | **905** |
| fonction gouvernementale seulement | 90 |

## 3. La correction

> « … mais son référentiel historique AMO30 ne rattache **aucun mandat de député** antérieur à la XIIe — mesuré le 12/09/2026 : 3 117 acteurs, dont 2 122 ayant siégé à l'Assemblée ; plus ancien mandat de député 2002-06-19 (XIIe), les organes du Sénat que le référentiel porte remontant à 1980 et restant hors périmètre (#528) »

La borne **ne change pas** : nos fiches ne remontent toujours pas avant le 19/06/2002. Ce qui change, c'est que la phrase cesse d'affirmer sur le fichier ce qui n'est vrai que d'une partie de son contenu.

## 4. Ce que l'incident apprend

**Le commentaire du code avait vu le défaut à moitié.** Il notait « des mandats d'ORGANES remontent au 09/07/1998 », donc l'écart était connu — mais la phrase *publiée*, elle, avait gardé le mot « acteur », et personne ne relisait les deux ensemble. Un commentaire juste ne protège pas d'un texte faux : ce qui est publié doit porter sa propre mesure.

**Et la mesure de 1998 était elle-même trop récente** : le plus ancien mandat du fichier est de 1980. Elle avait dû être faite sur un sous-ensemble — les organes, sans les groupes du Sénat.

## 5. Ce que ça ouvre

Les mandats sénatoriaux qu'AMO30 publie sur nos profils — **291 entrées sur 33 profils** — sont l'objet de #878 : les publier quand c'est l'AN qui les source, sans jamais interroger le Sénat.
