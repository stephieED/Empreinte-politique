<a id="gouvernement-textes-fam-codes-manquants"></a>
# `gouvernement_textes` : 3 `fam_code` manquants excluaient 42 % des textes ; `adopte_cmp` ajouté à la nomenclature (#397) (2026-08-18)

`2026-08-18`

> **En bref** — 3 `fam_code` manquants excluaient 42 % des textes ; `adopte_cmp` ajouté à la nomenclature.

**Contexte** : la revue de l'audit `audit_pipeline_20260817T153911Z` a montré
518 warnings sur les profils de gouvernement, dont **473 du seul type
`gouvernement_textes`**. Dépliés, ils provenaient de **3 `fam_code` distincts
seulement**, absents de `_FAM_CODE_STATUT_MAP`.

Le comportement en place était correct au regard d'AGENTS.md §2.5 — un code
inconnu donne `statut = None`, jamais un statut par défaut — mais
`gouvernement_profile.py` exclut alors le dossier de `textes[]`. Résultat :
**45 dossiers exclus contre 61 retenus, soit 42 % des textes gouvernementaux
absents du jeu de données**, dont le *Projet de loi de finances pour 2025*.

**Sens des trois codes, relevé dans le dataset source** (`statutConclusion.libelle`
du dump AN), donc sans interprétation de notre part :

| `fam_code` | Libellé AN | Décision |
| --- | --- | --- |
| `TSORTF03` | « adopté sans modification » | `adopte` |
| `TSORTF18` | « adopté, dans les conditions prévues à l'art. 45 al. 3 » | `adopte_cmp` (nouveau) |
| `TSORTF05` | « modifié » | `navette_en_cours` |

**Arbitrage sur `TSORTF18` (décision humaine, option B retenue)** : l'issue est
une adoption, mais par une voie procédurale distincte — approbation du texte
élaboré en commission mixte paritaire, sur demande du Gouvernement. Deux
options étaient ouvertes : fondre dans `adopte`, ou créer un statut dédié. Le
statut dédié `adopte_cmp` a été retenu, par symétrie explicite avec le
traitement du 49.3 en #208 : le fait procédural n'est jamais fusionné avec
l'issue du vote (AGENTS.md §2.4). `sort_49_3` reste `False` — `adopte_cmp`
n'est pas un statut 49.3, et le validateur refuse la combinaison
`adopte_cmp` + `sort_49_3 = True`. Il n'y a pas de cumul possible : si le
Gouvernement engage sa responsabilité sur le texte de CMP, la décision de
séance la plus récente porte `TSORTF06`/`TSORTF24`, pas `TSORTF18`.

**`TSORTF05` réaligne un test sur sa propre intention** :
`test_derniere_decision_de_seance_chronologique_prevaut_sur_une_decision_anterieure`
décrivait dans sa docstring un dossier « toujours en navette », mais assertait
`statut is None` — parce que le code ne savait pas encore l'exprimer. La
docstring du module anticipait déjà ce cas sans l'avoir encodé.

**Résultat mesuré après régénération des 10 gouvernements** :

| Indicateur | Avant | Après |
| --- | --- | --- |
| Textes retenus | 61 | **104** |
| Warnings gouvernement | 518 | **2** |
| `adopte` | 20 | 43 |
| `adopte_cmp` | — | 16 |
| `navette_en_cours` | 36 | 40 |

Les 2 warnings restants relèvent d'une autre cause (`chambre_depot_initial`
indéterminée sur `DLR5L17N50840` et `DLR5L17N53195`).

**La nomenclature reste fermée.** L'élargissement du mapping ne l'affaiblit
pas : un `fam_code` réellement inconnu produit toujours `statut = None` et un
warning. Un test dédié le vérifie, précisément parce qu'un tel élargissement
est le moment où cette protection risque d'être perdue de vue.

**Propagation** : `make_empty_comptages_statuts()` dérive de
`KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL`, donc `adopte_cmp` s'est propagé sans
modification supplémentaire côté schéma et audit. En revanche, **trois jeux de
fixtures de tests énuméraient les statuts en dur** et sont devenus invalides —
ils dérivent désormais de la nomenclature. Seule l'UI
(`web/UI_finale/src/data/pivotAdapter.js`) exige une entrée manuelle, pour
l'ordre d'affichage et les libellés : « adopté (texte de CMP) ».

**Suites** : #400 (ingérer les archives `/15/` et `/16/`, qui débloqueront
Borne et Castex, aujourd'hui à 0), #399 (bruit d'audit — ce sont ces 473
warnings qui avaient masqué le présent défaut), #398 (`premier_ministre` et
`portefeuille`).

---

