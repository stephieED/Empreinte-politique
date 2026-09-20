<a id="cle-fusion-interventions-540"></a>
# Une URL de source n'est pas un identifiant : la clé de fusion des interventions (#540) (2026-08-27)

`2026-08-27`

> **En bref** — la clé devient l'identifiant de la prise de parole, pas son URL.

**Mesure de référence.** Prise le 27/08/2026 sur `HEAD` = `74c77c2`, en
rejouant la normalisation et la fusion pivot sur les profils **bruts et pivot
committés** — pas sur une régénération, pas sur une estimation :

| Profil | Collecté (brut) | Publié (pivot) | Clé actuelle | Composite `(source_url, date, sujet, texte[:80])` | Clé retenue |
| --- | ---: | ---: | ---: | ---: | ---: |
| gabriel-attal | 3 351 | 17 | 17 | 3 127 | **3 351** |
| marine-le-pen | 2 247 | 384 | 384 | 2 240 | **2 247** |
| jerome-guedj | 1 083 | 396 | 396 | 1 077 | **1 083** |
| laurent-wauquiez | 535 | 23 | 23 | 533 | **535** |
| bruno-retailleau | 486 | 6 | 6 | 458 | **486** |
| edouard-philippe | 50 | 50 | 50 | 50 | **50** |
| jean-luc-melenchon | 15 | 15 | 15 | 15 | **15** |
| **TOTAL (7 profils porteurs sur 476)** | **7 767** | **891** | **891** | **7 500** | **7 767** |

Les 469 autres profils publiés ont une liste `interventions[]` vide des deux
côtés : ils n'entrent dans aucune colonne. Le corpus publié est bien à
**891 interventions sur 476 profils**, et la colonne « clé actuelle » le
reproduit à l'unité — c'est le contrôle qui établit que la mesure rejoue le
chemin réel et pas une approximation.

## Le défaut

`merge_profile._pivot_intervention_key` valait :

```python
return i.get("source_url") or (i.get("date"), i.get("sujet"), (i.get("texte") or "")[:50])
```

Le `or` court-circuite. Le repli discriminant existait — le triplet
date/sujet/texte — mais il n'était **jamais atteint** dès que `source_url`
était renseignée, c'est-à-dire toujours (0 entrée sans `source_url` sur les
891 publiées). La clé avait été écrite pour NosDéputés, qui publiait un
permalien `#inter_<hash>` par intervention. Syceron ne publie pas de
permalien : la seule URL qu'il expose est celle de **l'archive de la
législature**, la même pour ses 3 336 entrées chez gabriel-attal.

`merge_lists_by_key` est purement additif et ne peut donc rien perdre — mais
il n'ajoute que les clés inédites. Aucun garde-fou n'avait à réagir :
`audit_diff_profils` surveille les pertes et le pivot avait *augmenté*
(804 → 891) ; `audit_collecte_non_publiee` raisonne sur des profils, pas sur
le contenu de leurs listes.

Le dépôt connaissait déjà ce mode de défaillance : la docstring de
`_pivot_vote_key` (#432) le décrit mot pour mot pour les votes non résolus —
« les traiter tous comme la même clé `None` les fusionnerait en un seul, une
perte silencieuse ». Ici la clé collante n'est pas `None` mais une URL, donc
plus difficile à repérer : elle *ressemble* à un identifiant.

## La décision : propager l'identifiant, pas élargir la clé

`normalize_profil._normalize_intervention` écrit désormais
`interventions[].intervention_id`, propagé **verbatim** depuis l'`id` du profil
brut. `_pivot_intervention_key` en fait sa clé, avec `source_url` puis le
contenu en replis pour les entrées écrites avant ce lot.

Trois raisons, dans cet ordre :

**1. C'est la même identité que celle de la fusion brute.** `_intervention_key`
(`merge_profile:142`) repose sur `(id, url)` depuis toujours et n'a jamais
souffert du défaut — c'est précisément pourquoi les 7 767 entrées sont
*collectées* et seulement 891 *publiées*. Les deux étages disent maintenant la
même chose de ce qu'est une intervention. Tant qu'ils divergent, le pivot peut
publier autre chose que ce que la collecte a rendu sans que rien ne le dise.

**2. La clé composite proposée par l'issue est lossy, et le chiffre le dit.**
Elle rend 7 500 entrées au lieu de 7 767 : elle en absorbe **267 réelles**.
L'issue supposait qu'il s'agissait de doublons d'archive — la vérification dit
le contraire. Chez gabriel-attal, « Même avis, pour les mêmes raisons. » est
prononcé **13 fois dans la même séance du 08/11/2022**, sur 13 amendements
successifs ; « Même avis. » 9 fois le 03/11/2023. Ce sont 13 et 9 prises de
parole distinctes, que seul le rang du paragraphe dans le compte rendu sépare.
Les fusionner aurait été la perte silencieuse qu'on corrigeait, en plus petit.

**3. Une clé qui dépend du texte n'est pas stable.** Le compte rendu Syceron
porte un `etat_compte_rendu` et un `version_compte_rendu` : il est révisé. Une
correction typographique dans un paragraphe ferait revenir la même intervention
comme une entrée neuve, indéfiniment.

**Ce que la décision ne prétend pas.** `id` vaut
`syceron_<uid du compte rendu>_<rang du paragraphe>` : le `uid` vient de la
source, le rang est **positionnel**. Il est donc stable tant que le compte
rendu n'est pas re-paginé, pas au-delà. Ce n'est pas une régression : c'est
exactement la garantie qu'offre déjà la fusion brute, et l'aligner dessus ne
crée aucun risque nouveau. Syceron expose par ailleurs un `<paragraphe>` avec
ses propres attributs, que `parse_syceron` n'extrait pas aujourd'hui ; s'il
porte un identifiant publié par la source, le remplacer serait un progrès —
hors périmètre de ce lot, qui n'aurait pas pu le faire sans recollecter les
trois archives.

## La reprise des 891 entrées déjà publiées

C'est le point qui a demandé le plus d'attention. Les entrées publiées avant ce
lot n'ont **pas** d'`intervention_id` : leur clé reste leur `source_url`. Leur
renormalisation en a un. Sans reprise, la fusion additive publierait **les
deux** — l'ancienne sous sa clé d'URL, la neuve sous sa clé d'identifiant — et
le corpus se dédoublerait au lieu de se compléter.

`merge_profile.clean_stale_interventions`, sur le patron de
`clean_stale_textes_portes` (#431), écarte une entrée **sans**
`intervention_id` quand au moins une entrée **avec** `intervention_id` porte la
même `source_url`. Elle est alors, par construction, l'une de ces entrées-là :
la même intervention renormalisée pour un permalien (une entrée par URL), ou
l'unique rescapée de l'effondrement pour une URL d'archive — la première entrée
collectée de cette archive, que la liste neuve contient aussi. La reprise ne
peut donc rien perdre : sans entrée identifiée sur cette `source_url` (collecte
en échec, archive indisponible, législature non recollectée), rien n'est
écarté et l'ancienne entrée reste publiée. Vérifié sur les 476 profils : **0
entrée publiée non représentée après correctif**.

**Aucune passe de migration n'est nécessaire.** `generate_all_profiles`
normalise le profil **brut fusionné** puis le fusionne au pivot publié : les
7 767 entrées vivent déjà dans `raw_data/profiles/`, committées. Un
`--pivot-only` sur le corpus committé suffit à les publier, sans réseau et sans
recollecte. Le correctif seul récupère donc les 891 écrasées, au prochain run.

## Idempotence

Le piège de toute clé composite sur du texte tronqué. La clé retenue est une
fonction de l'identifiant seul : refusionner un profil avec lui-même n'ajoute
rien, et `clean_stale_interventions` appliquée deux fois rend le même résultat
(au second passage il ne reste plus d'entrée sans identifiant à reprendre).
Vérifié sur les 476 profils — **0 profil non idempotent** — et tenu par
`tests/test_interventions_cle_fusion_540.py`.

## Les autres clés pivot ne sont pas exposées

Auditées avec ce lot : `_pivot_vote_key` (`scrutin_id`, repli sur
`("non_resolu", numero, date)`), `_pivot_mandat_key` (tuple composite),
`_pivot_amendement_key` (`an:<uid>`, identifiant réellement unique) et
`_pivot_texte_key` (composite, indépendante de `role`). Aucune ne traite un
champ potentiellement non unique comme un identifiant. Le défaut est isolé aux
interventions.

## Ce qui reste ouvert

Le garde-fou « collecté vs publié » **au niveau des listes** demandé par #540
n'est pas dans ce lot. Aucun contrôle ne compare aujourd'hui ce que la collecte
a rendu à ce que la publication porte, champ par champ : c'est l'angle mort
exact dans lequel ce défaut a vécu, et il manquera à la prochaine source. Il
mérite son propre lot — il touche `audit_diff_profils` et
`audit_collecte_non_publiee`, dont aucun n'est en défaut ici. Le raisonnement
qui a laissé cet angle mort ouvert est daté et cité dans
[#syceron-actif-510](syceron-actif-510.md), section « Ce qui est mesuré, et ce
qui ne l'est pas » : la prédiction « le contrôle de perte verra une hausse, pas
une perte, donc il ne bloquera pas » était juste, et sa conséquence — plus rien
n'attrape alors un effondrement de clé — n'avait pas été tirée.

