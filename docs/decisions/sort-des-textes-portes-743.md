<a id="sort-des-textes-portes-743"></a>
# Un texte porté dit ce qu'il est devenu, et son sort ne se déduit jamais de son stade (#743) (2026-09-06)

`2026-09-06`

> **En bref** — `textes_portes[]` publiait dix champs dont **aucun ne disait ce qu'était devenu le texte** (ni rejeté, ni retiré, ni en navette), `stade_procedural` encodant une **progression** dont l'absence du cran suivant est un fait de la source à sa date et jamais une issue ; ce n'était pas un manque de source — les fiches de gouvernement le publient **depuis #184** (725 textes) et `schema_gouvernement.py` avait écrit que ce concept « n'existe pas encore côté pivot individuel » —, et la source est instruite depuis le spike #207 : le statut vit dans **`statutConclusion.fam_code`**, non dans `codeActe` ; d'où `textes_portes[].sort`, vocabulaire fermé lu **par la même fonction que les gouvernements** (`_determine_statut`, qui ne dépend pas de l'origine du dossier), accompagné quand il est `null` d'un `sort_non_resolu.motif` à trois valeurs **qui ne se réparent pas au même endroit** — `sans_decision` (état légitime), `fam_code_inconnu` (table à étendre), `archives_indisponibles` (panne du run) —, le schéma refusant la contradiction et le motif inventé, et `sort_49_3` n'étant **pas** republié puisque `adopte_49_3` le porte déjà ; mesuré sur les **472 entrées** : `navette_en_cours` 238 · `adopte` 127 · `adopte_cmp` 59 · `promulgue` 20 · **`rejete` 13** · **`retire` 8** · `adopte_49_3` 7, **0 sans sort**, et **464/464** dossiers retrouvés sans un seul `fam_code` inconnu ; **septième occurrence** de la famille #492/#639/#641/#696/#710/#718 pour le report nommé — mais **la moitié du câblage aurait été du code mort** : posé d'abord aux deux étages sur la leçon de #729/#730, la mutation a montré que décâbler le report **brut** fait échouer un test et le **pivot** aucun, parce que `merge_dossier_records` fait gagner l'entrée **neuve** là où `merge_lists_by_key` fait gagner l'ancienne — report pivot **retiré**, et la leçon écrite : **une règle générale ne dispense pas de vérifier qu'elle s'applique ici** ; le lot ne dérive jamais le sort du stade (4 tests sur 4 stades), ne touche pas la vue, et rien n'est publié avant un run. 27 tests, trois mutations vérifiées échouantes plus une quatrième restée verte — celle qui a fait retirer du code. Suite complète à 3 840, 0 échec.

## 1. Le constat

`textes_portes[]` publiait dix champs — `titre`, `dossier_id`, `role`,
`nature_texte`, `type_rapport`, `stade_procedural`, `date_min`, `date_max`,
`legislature`, `source_url` — dont **aucun ne disait ce qu'était devenu le
texte**. Ni rejeté, ni retiré, ni encore en navette.

`stade_procedural` encode une **progression** : `depose` → `examine_commission`
→ `inscrit_ordre_jour` → `discute_seance` → `adopte` → `promulgue`, dont un
dossier ne porte que le cran le plus avancé atteint. L'absence du cran suivant
est un fait de la source **à sa date**, jamais une issue. « Discuté en séance et
pas adopté » ne permet pas d'écrire « rejeté » (§2 règles 2 et 5).

## 2. Ce n'était pas un manque de source, et le dépôt le savait déjà

Les fiches de gouvernement publient ce sort **depuis #184** — 725 textes, tous
qualifiés. Et `schema_gouvernement.py` avait écrit d'avance pourquoi le champ
vivait là et pas ailleurs :

> `KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL` est définie ici, pas dans
> `schema_pivot.py` : ce concept d'« issue » d'un dossier (résultat final)
> **n'existe pas encore côté pivot individuel**, et est distinct de
> `KNOWN_STADES_PROCEDURAUX`, qui encode une progression procédurale, pas une
> issue.

Le « pas encore » est ce que ce lot comble.

La source, elle, est instruite depuis le spike #207 (`docs/sources/an-opendata.md`,
14/08/2026, comptage exhaustif sur 3 044 dossiers) : le statut est porté par
**`statutConclusion.fam_code`**, et **non** par `codeActe` — une hypothèse déjà
écartée là-bas, et que la session UI a reproposée de bonne foi.

## 3. La décision

`textes_portes[].sort`, vocabulaire fermé `KNOWN_SORTS_TEXTE_PORTE`, **lu par la
même fonction que les fiches de gouvernement** : `gouvernement_textes._determine_statut`
ne dépend pas de l'origine du dossier — c'est `parse_dossier_gouvernemental` qui
filtre l'origine **avant** de l'appeler. Même archive, même fonction, même
vocabulaire, exactement le patron de `nature_texte` (#689).

Quand le sort est `null`, l'entrée porte **`sort_non_resolu.motif`**, d'un
vocabulaire fermé de trois valeurs **qui ne se réparent pas au même endroit** :

| Motif | Ce que c'est | Se répare |
| --- | --- | --- |
| `sans_decision` | le dossier n'a pas atteint de décision de séance | **rien à réparer** — un état légitime |
| `fam_code_inconnu` | la source publie un code que la table ne connaît pas | en étendant la table |
| `archives_indisponibles` | l'archive n'a pas été fournie au run | une panne du run |

Les confondre ferait passer un **état normal** pour un défaut. Le schéma refuse
qu'une entrée porte les deux à la fois, et refuse un motif inventé.

**`sort_49_3` n'est pas republié** : `adopte_49_3` et `rejete_49_3` le portent
déjà, et le dupliquer ferait deux faits là où il n'y en a qu'un.

## 4. Ce que ça donne, mesuré

Rejoué sur les **472 entrées publiées** de `textes_portes[]`, archives en cache :

| Sort | Entrées |
| --- | ---: |
| `navette_en_cours` | 238 |
| `adopte` | 127 |
| `adopte_cmp` | 59 |
| `promulgue` | 20 |
| **`rejete`** | **13** |
| **`retire`** | **8** |
| `adopte_49_3` | 7 |
| **Sans sort** | **0** |

Sur les 464 `dossier_id` distincts : **464 / 464 retrouvés dans les archives, 0
`fam_code` inconnu, 0 warning**. Les trois motifs sont donc, aujourd'hui, des
**compteurs-témoins à zéro**.

## 5. Le report nommé — et la moitié qui aurait été du code mort

**Septième occurrence de la famille** #492 / #639 / #641 / #696 / #710 / #718 :
un champ ajouté au schéma n'atteint jamais une entrée déjà collectée tout seul.
`_dossier_key` ne contient pas le sort, donc l'entrée neuve qui le porte a la
même clé que l'ancienne et serait écartée à chaque régénération.

**Le report a d'abord été câblé aux deux étages, sur la leçon de #729/#730, et
la moitié était fausse.** La mutation l'a montré : décâbler le report du **brut**
fait échouer un test, le décâbler du **pivot** n'en fait échouer aucun.

La raison est que `textes_portes` ne se fusionne pas comme les autres listes :
`merge_dossier_records` fait gagner l'entrée **neuve** en cas de collision de
clé, là où `merge_lists_by_key` fait gagner l'ancienne. Le sort atteint donc le
pivot de lui-même.

Le report pivot a été **retiré**. Il aurait été du code mort justifié par un
raisonnement faux — la bonne règle appliquée à une liste qui n'y est pas
soumise. **Une règle générale ne dispense pas de vérifier qu'elle s'applique
ici.**

## 6. Ce que le lot ne fait pas

- **Il ne dérive jamais le sort du stade**, dans aucun sens, et quatre tests le
  vérifient sur quatre stades. « Non adopté » ne devient pas « rejeté ».
- **Il ne touche pas la vue.** La cascade procédurale de la fiche candidat
  emploie des formulations négatives — « non discuté en séance », « non
  adopté », « non promulgué » — et elles restent correctes : un sort collecté ne
  change rien au fait qu'un stade non atteint ne dit rien du sort.
- **Il ne modifie pas les fiches de gouvernement**, déjà servies par #184.
- **Rien n'est publié tant qu'un run n'a pas régénéré.** Les mesures ci-dessus
  viennent d'un rejeu hors dépôt.

## 7. Une duplication assumée, et verrouillée

`KNOWN_SORTS_TEXTE_PORTE` a les mêmes neuf valeurs que
`KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL`. Les deux schémas restent indépendants —
c'est une règle du dépôt —, mais ils lisent la même source par la même fonction
et ne peuvent pas diverger sans que ce soit une erreur. Un test l'affirme, donc
une divergence se verra au lieu de s'installer.

## 8. Vérification

`tests/test_sort_des_textes_portes_743.py` — 27 tests : les deux vocabulaires et
leur accord, le schéma qui refuse un sort inventé, un motif inventé, la
contradiction ; quatre stades qui ne fabriquent aucun sort ; le report et ses
invariants ; la clé de fusion inchangée ; et le test qui **documente pourquoi le
pivot n'a pas besoin de report**.

Trois mutations vérifiées échouantes : le report brut décâblé, la contradiction
autorisée par le schéma, le sort déduit du stade. Une quatrième — le report
pivot décâblé — **n'a fait échouer aucun test**, et c'est ce qui a fait retirer
ce report.

Suite complète : **3 840 tests, 0 échec**.
