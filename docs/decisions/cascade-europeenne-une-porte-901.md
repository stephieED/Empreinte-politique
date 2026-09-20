<a id="cascade-europeenne-une-porte-901"></a>
# La cascade des textes portés passe au versant européen : une porte, et la nomenclature de la source (#901) (2026-09-16)

`2026-09-16`

> **En bref** — les **694 textes portés européens** des six fiches à mandat européen n'atteignaient pas l'écran : `STADES_PUBLIES` est un **ordre** — un texte est publié s'il a atteint au moins l'examen en commission — et aucune des seize valeurs `ue_` n'y a de rang. Raphaël Glucksmann affichait « **0 publiés** » en portant 23 textes, dont 9 à un stade que la source publie. La section 2 gagne donc un **commutateur** *Au niveau français · Au niveau européen*, et le versant européen reprend **la même figure** avec **un seul palier** : les seize stades décrivent des états, pas des degrés — « procédure achevée » recouvre l'adoption comme l'échec, et « procédure rejetée » est une procédure achevée elle aussi. Les **628** propositions de résolution que la source ne rattache à aucun dossier restent **dans** la figure, en branche basse nommée. Forme arbitrée par la propriétaire le 16/09/2026 sur maquette, sur données réelles.

## 1. Le défaut, mesuré

Sur le corpus du 15/09/2026, après le run `34980741069` :

| Fiche | Textes européens | À un stade publié | Ce que la fiche affichait |
| --- | ---: | ---: | --- |
| Florian Philippot | 502 | 2 | « 0 publiés · 0 promulgué » |
| Marine Le Pen | 115 | 10 | idem |
| Emmanuel Maurel | 45 | 37 | « 45 autres textes portés dont la source ne publie pas le stade », rangés avec ses textes **français** |
| Raphaël Glucksmann | 23 | 9 | « 0 publiés · 0 promulgué » |
| Jean-Luc Mélenchon | 8 | 8 | idem |
| Lydie Massard | 1 | 0 | idem |
| **total** | **694** | **66** | |

Deux défauts distincts, et le second était invisible : les textes européens étaient **comptés dans le total français**, donc dans `ecartes`. Les 45 de Maurel se lisaient comme 45 textes de l'Assemblée restés au dépôt.

## 2. La figure : un palier, et pas une échelle

La mise en page française cumule — `atteint[i]` est la somme des arrêts au-delà de `i` — parce qu'un texte promulgué a forcément été adopté, discuté, examiné. **Les seize valeurs européennes ne s'ordonnent pas.** `docs/sources/parltrack-et-europarl.md` le dit de la source elle-même : ce sont des **états**, et « Procedure completed » recouvre l'adoption comme l'échec.

D'où `disposerCascadeUE` : les matières à gauche, **une barre par issue** à droite, aucun flux ne traversant une autre. Même forme de retour que sa voisine, donc **le même composant, le même clic, les mêmes teintes** — et la même hauteur, pour que le commutateur ne fasse pas sauter la page.

**Les branches basses sont nommées, et il y en a trois possibles.** Un texte sans stade porte toujours son motif (`deux-fabriques-textes-portes-europeens-901`) :

| Motif | Ce qu'il dit | Corpus |
| --- | --- | ---: |
| `activite_sans_dossier` | l'activité ne vise aucun dossier : il n'y a rien à interroger | **628** |
| `source_sans_stade` | le dossier est connu, la source se tait sur son stade | 0 |
| `stade_source_inconnu` | la source publie un libellé que notre table ignore | 0 |

Les deux derniers sont des compteurs-témoins. Les confondre ferait compter comme une lacune de la source ce qui est une propriété de l'activité (§2 règle 5).

## 3. La matière est la commission saisie au fond — et elle manque presque partout

Même champ qu'au niveau français, autre index : `pivot_data/dossiers_europeens.json`, résolu sur `reference_dossier`. Mesuré le 16/09/2026 :

| | |
| --- | ---: |
| textes européens ne citant **aucun** dossier | **628** |
| textes citant une référence | 66 (**43** références distinctes) |
| références présentes dans l'index | **9 sur 43** |
| textes effectivement teintés | **12 sur 694** |

L'index a été construit pour les références que les **amendements** visent (#901) ; celles des textes portés n'y sont pas. **Besoin remonté au pipeline** : y ajouter les 34 manquantes. Même alors, le plafond reste 66 sur 694 — une résolution individuelle ne vise aucun dossier, et rien ne le remplacera. La matière n'est jamais déduite de l'intitulé (§2 règle 2).

**Le nom complet, et en anglais.** La figure portait d'abord l'acronyme — `AFET`, `ITRE` — et la propriétaire a demandé le nom complet le 16/09/2026 : côté français, ce que la figure appelle « sigle » est un nom court **en français** (« Lois », « Affaires sociales ») et se lit ; côté européen c'est une abréviation opaque. Le nom reste **en anglais** parce que c'est ce que l'index publie — `Foreign Affairs` —, et le traduire écrirait un libellé que personne n'a publié : la même frontière que les titres de dossiers, eux non plus jamais traduits (`titres-europeens-sans-boutons-901`). Arbitré ainsi le 16/09/2026, l'anglais assumé plutôt qu'une traduction de notre main.

Le libellé officiel français existe pourtant, et **le corpus le porte déjà ailleurs** : les mandats européens des fiches publient **181 paires sigle → libellé**, « INTA » y valant « Commission du commerce international ». C'est le second besoin remonté au pipeline — le porter dans l'index des dossiers. La bascule sera alors une clé à changer, jamais une table à écrire dans l'interface, et un test refuse qu'un sigle de commission soit cité dans le code de la fiche.

La gouttière des noms s'ajuste en conséquence, plafonnée à 200 px : les 172 px de la figure française sont taillés pour « Affaires sociales », et **11 des 24 commissions européennes dépassent 25 signes** — « Environment, Public Health and Food Safety » en fait 42. Au-delà, ce sont les rubans qu'on écrase ; ce qui ne tient pas est coupé et reste entier dans l'infobulle.

## 4. Le seuil §6, écrit par exclusion

`STADES_UE_NON_PUBLIES = ['ue_phase_preparatoire_parlement']`, la même valeur que `src/schema_pivot.py`, et un test le vérifie contre le schéma. Écrire la règle dans l'autre sens — une liste de stades publiés — ferait disparaître en silence tout stade que la source ajouterait ensuite ; ici il arrive publié, ce qui est la conséquence voulue de l'arbitrage du 14/09/2026. Un texte que §6 ne publie pas est **compté et dit** sous la figure, jamais tu. Aucun n'est dans ce cas aujourd'hui.

## 5. Les seize libellés

Aucun stade n'était traduit : la fiche aurait affiché `ue_procedure_achevee` tel quel. Chaque libellé suit celui de la source, sans rien y ajouter — « achevée » n'est pas « adoptée », et un test refuse qu'un libellé européen promette une adoption, une promulgation ou un vote que le dump n'établit pas (`sort_non_resolu: source_sans_sort` sur les 694).

## 6. L'alternative écartée

Deux autres formes étaient maquettées sur les données réelles :

- **la porte seule**, les textes sans dossier comptés en une phrase sous la figure. Écartée : Florian Philippot aurait publié une figure de **2 textes** pour une fiche qui en porte 502. Un texte porté qui sort de la figure sort de la fiche.
- **un registre unique, le stade en étiquette**, l'absence de stade devenant une étiquette parmi les autres. Écartée : elle donne à une absence l'apparence d'un état.

## 7. Un test réécrit, et ce qu'il tenait

`test_la_cascade_lit_la_meme_table_de_commissions_que_la_chute` exigeait la **chaîne** `export function textesPortes(textes, commissionDuDossier` — la signature exacte, sur une ligne. Le troisième paramètre l'a passée sur plusieurs lignes et le test a rougi sans qu'aucune figure ait changé de table. Il vérifie désormais l'**intention** : le paramètre existe, et l'adaptateur passe le même résolveur aux deux figures. Deuxième fois en une semaine qu'un test de chaîne dérive pendant que le comportement tient.

## 8. Ce que ce lot ne fait pas

- **Les amendements européens** ne rejoignent pas encore leur dossier : « 590 amendements · 0 dossiers » reste affiché, alors que `texte_vise` est publié à 100 % et que l'index en résout 33 des 37 références de Glucksmann. Lot suivant.
- **Les votes européens** non plus : les 11 013 positions sont toutes des votes sur l'ensemble d'un texte, et `scrutins_europeens.json` en résout **1 977 sur 1 977** pour Glucksmann. La section reste vide en attendant l'arbitrage de la juxtaposition (`pas-d-ecarts-groupe-europeens-901` §4).
- **Les titres** : **314 des 694** portent encore « PDF (268 KB) DOC (71 KB) », alors que `titres-europeens-sans-boutons-901` a livré le nettoyage le 15/09. Le correctif n'a pas atteint le corpus — signalé au pipeline, non corrigé ici.

→ voisins : [`stade-procedural-europeen-901`](stade-procedural-europeen-901.md), [`index-dossiers-europeens-901`](index-dossiers-europeens-901.md), [`trois-saisines-au-fond-europeennes-901`](trois-saisines-au-fond-europeennes-901.md), [`pas-d-ecarts-groupe-europeens-901`](pas-d-ecarts-groupe-europeens-901.md)
