<a id="rattachement-des-membres-par-organe-996"></a>
# La fiche rattache ses membres par `organe_ref`, plus par un libellé comparé entre deux sources (#996, lot 4) (2026-09-18)

`2026-09-18`

> **En bref** — `gouvernement_roster.py` retenait un membre en comparant
> `mandats[].label` à `"Gouvernement (<libelle_an>)"` : **une jointure de
> chaînes entre deux sources différentes**, l'endpoint « positions dans
> l'hémicycle » d'un côté, les organes AMO30 de l'autre. Le roster de #996
> lot 2 porte `organe_ref` ; c'est lui qui tranche désormais l'appartenance.
> Mesuré sur les 17 fiches : **16 identiques, +2 sur Borne, 0 perdu**. Le
> libellé garde un rôle, un seul — départager les mandats *d'une même
> personne*. Et `comptages.membres_distincts` dit enfin ce que `membres[]`
> compte.

## Contexte

Lot 4 de #996. Le run du 18/09 a collecté les 205 profils manquants, et les 650
personnes recensées sur les 17 fiches sont désormais toutes rattachées — écart
`+0`. La raison d'être du lot n'est donc pas de rattacher plus, mais de
rattacher **autrement**.

**Le défaut n'est pas l'ambiguïté des libellés.** Les 17 sont distincts, AMO30
les numérote (`FILLON 1/2/3`, `PHILIPPE`/`PHILIPPE 2`, `LECORNU`/`LECORNU II`).
Il est que les deux chaînes comparées ne viennent pas du même endroit :

| Côté | Source |
| --- | --- |
| `raw_data/gouvernements_reels.json` → `libelle_an` | AMO30, `organe.libelleAbrege` (`gouvernements_amo30.py`) |
| `mandats[].label` du profil | endpoint « positions dans l'hémicycle », `groupe_sigle` (`candidate_profile.py`) |

Elles s'accordent au 18/09/2026. Rien ne l'impose, et une divergence ferait
disparaître des membres **sans qu'aucune étape n'échoue** — la forme du trou
muet de #510.

## Décision

**Le roster dit QUI, la période de l'organe dit QUAND, le libellé départage les
mandats d'une même personne.**

1. `slugs_du_gouvernement(membres_roster, organe_ref)` rend les slugs que le
   roster déclare sur cet organe. `None` — jamais un ensemble vide — quand le
   roster manque : un ensemble vide dirait « aucun membre » et viderait la
   fiche (§2 règle 5).
2. Un profil que le roster ne nomme pas n'est plus examiné.
3. **Le repli par libellé est conservé**, et seulement pour un run sans
   artifact de roster : une fiche produite par la voie fragile vaut mieux que
   pas de fiche (même arbitrage que #427). `charger_membres_roster` dit sur
   `stderr` laquelle des deux voies a servi.
4. `comptages.membres_distincts` est publié à côté de `membres_recenses`.

## Les deux pièges, trouvés en mesurant et non en lisant

Les deux premières versions de ce lot passaient toute la suite et **corrompaient
les fiches**. Elles n'ont été prises que par la comparaison des deux voies sur
le corpus réel, gouvernement par gouvernement.

**1. Une période d'appartenance non bornée avale le gouvernement suivant.**
AMO30 publie pour Amélie de Montchalin **deux** périodes `BAYROU`, dont une
`2024-12-24 → None`. Utiliser les dates du roster comme garde temporel lui
attribuait ses 4 entrées Lecornu sur la fiche Bayrou. C'est la période de
l'**organe** qui fait foi : elle, est bornée par le référentiel.

**2. Deux gouvernements qui se touchent d'un jour se volent leurs mandats.**
`FILLON 1` finit le 2007-06-18, `FILLON 2` commence le 2007-06-18. Le
chevauchement de période ne peut pas les séparer — ils se chevauchent
réellement. Sans le libellé pour départager les mandats *d'une même personne*,
Fillon II récupérait **19** entrées de Fillon I et Valls II **27** de Valls.

D'où le rôle résiduel du libellé, qui n'est **pas** celui que ce lot retire :
il ne décide plus de l'appartenance — c'était là qu'un libellé divergent faisait
disparaître quelqu'un — il trie les mandats d'une personne déjà retenue, tous
issus du même endpoint, donc cohérents entre eux.

## Mesuré, les deux voies sur les 17 fiches

| | Par libellé | Par `organe_ref` |
| --- | ---: | ---: |
| Entrées `membres[]`, total | 768 | **770** |
| Fiches identiques | — | 16 / 17 |
| Entrées perdues | — | **0** |

Le seul écart est Borne, `+2` : **Damien Abad et Yaël Braun-Pivet** portent un
mandat d'appartenance libellé `"Gouvernement"`, **sans parenthèses** — la source
n'a pas donné de sigle. L'égalité stricte le jetait. Le roster déclare la
personne membre, la période de l'organe le confirme, et les deux entrées sont
publiées sans portefeuille (aucun mandat `MINISTERE` ne chevauche ces fenêtres).

`membres_recenses` ne bouge pas : ce sont deux périodes de plus, pas deux
personnes.

## `membres[]` ne compte pas des personnes, et la fiche le dit maintenant

Mesuré le 18/09/2026 : **770 entrées pour 650 personnes** sur les 17 fiches, et
Fillon II à lui seul 89 entrées pour 52 personnes. `membres[]` porte une entrée
par **période** — un ministre qui change de portefeuille en cours de
gouvernement en a plusieurs (#398) — tandis que `membres_recenses` compte des
personnes.

Les deux nombres étaient donc posés côte à côte sur la fiche sans que rien ne
dise qu'ils portent sur des populations différentes : « 89 des 52 membres
recensés » est ce qu'un lecteur en tirait. `comptages.membres_distincts` est le
numérateur qui se rapproche du recensement, et il reste un entier — jamais un
taux (§2 règle 7).

## Alternative rejetée

**Ajouter `organe_ref` aux `mandats[]` du profil**, puis joindre dessus des deux
côtés. Plus propre en théorie, et utile au-delà des gouvernements. Rejeté pour
ce lot : c'est un changement de schéma qui n'atteint le corpus qu'après un run
de régénération complet, pour un défaut que le roster — déjà produit, déjà dans
le run — referme sans rien changer au pivot.

**Se passer du libellé entièrement.** Mesuré ci-dessus : +46 entrées fausses sur
deux fiches. La période seule ne sépare pas deux gouvernements qui se touchent.
