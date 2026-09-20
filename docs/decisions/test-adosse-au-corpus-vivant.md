<a id="test-adosse-au-corpus-vivant"></a>
# Un test d'acceptation adossé au corpus vivant rougit quand la donnée s'améliore (#457) (2026-08-20)

`2026-08-20`

> **En bref** — un test d'acceptation adossé au corpus vivant rougit quand la donnée s'améliore : fixtures figées.

Les vérifications d'acceptation de #209 (`tests/test_gouvernement_roster.py`)
lisaient `pivot_data/profiles/` directement, pour confronter
`build_gouvernement_roster` à de vrais profils plutôt qu'à des cas fabriqués.
L'intention était bonne ; le montage, non. Deux d'entre elles étaient rouges sur
`main`, et **aucune ne signalait une régression de code** :

- `charlotte-parmentier-lecocq` : le test assenait `portefeuille is None` pour la
  période Bayrou. Le portefeuille a fini par être renseigné dans le corpus. Le
  test échouait donc **parce qu'une lacune de données avait été comblée** — il
  avait figé l'absence en invariant.
- `david-amiel` : le test attendait 1 membre, en obtenait 2, parce que l'intéressé
  a changé de portefeuille sans changer de gouvernement.

**La leçon** : un test unitaire adossé à un corpus vivant n'a que deux issues, et
les deux sont mauvaises. Ou bien il fige une valeur, et il rougit à la première
mise à jour — y compris, comme ici, une mise à jour qui *améliore* la donnée, et
le signal est alors exactement inversé : rouge veut dire « ça va mieux ». Ou bien
il s'assouplit jusqu'à ne vérifier que la forme, et il cesse de contrôler ce pour
quoi il avait été écrit. Mesurer la couverture du corpus réel est le travail du
quality gate (`check_quality_gate.py` §5), qui est fait pour ça : il mesure un
niveau et le compare à un seuil, sans prétendre qu'une valeur est immuable.

D'où des **fixtures figées** sous `tests/fixtures/gouvernement_roster/` (modèle
`tests/fixtures/audit_pivot/`) : de vrais profils, réduits aux seuls champs que
`gouvernement_roster` lit (`id`, `nom`, `identite.source_url`, `mandats[]`) et
aux catégories `fonction_gouvernementale` / `mandat_electif` — 3 à 6 Ko au lieu
de 0,3 à 0,5 Mo. Chacune consigne sa provenance dans `meta.fixture` (fichier
source, ref, date d'extraction : §2.2), pour qu'on sache toujours de quel état du
corpus elle est le témoin. `mandat_electif` y est gardé bien qu'inerte pour ce
module, afin que le filtrage par catégorie porte réellement sur quelque chose.

## Le corollaire, qui dépasse les tests : `membres[]` dénombre des entrées, pas des personnes

Le cas `david-amiel` posait une vraie question éditoriale — un ministre qui change
de portefeuille sans changer de gouvernement doit-il compter deux fois ? — en
opposant §2.2 (traçabilité : deux fonctions distinctes sur deux périodes
distinctes, les fondre effacerait un fait vérifiable) à §2.7 (un dénominateur
publié doit être juste).

Elle se tranche par une vérification, pas par un arbitrage : **aucun effectif
n'est publié aujourd'hui**. `comptages.par_statut` dénombre des textes de loi, et
`web/UI_finale/src/components/GovernmentProfile.jsx` liste les membres sans en
donner le total (`members.length` n'y sert qu'au test de liste vide). Deux entrées
factuelles distinctes sont donc conformes à §2.2, et §2.7 n'est pas en cause :
rien n'expose de dénominateur faux.

Mais le décalage, lui, est bien réel et **systémique** — mesuré sur les 10
gouvernements publiés : 116 entrées pour 95 personnes, dont 7 gouvernements
concernés.

| gouvernement | entrées | personnes | écart |
| --- | --- | --- | --- |
| BORNE | 31 | 23 | 8 |
| BAYROU | 12 | 9 | 3 |
| CASTEX | 14 | 12 | 2 |
| FILLON_2 | 5 | 2 | 3 |
| FILLON_3 | 3 | 1 | 2 |
| LECORNU_II | 12 | 10 | 2 |
| PHILIPPE_2 | 9 | 8 | 1 |

Le risque est **différé, pas absent** : la première vue qui affichera « N
ministres » annoncera 31 pour Borne au lieu de 23, sans que rien ne l'avertisse.
La déduplication est à faire au moment de l'affichage, par `membre_id` — pas dans
`membres[]`, dont la granularité par période est ce qui porte l'information.
Même principe qu'en [[mandat-electif-perdu-fausse-le-denominateur]] : la
structure de `mandats[]` décide de ce qu'un décompte veut dire, et un
dénominateur faux se publie sans avertissement.

`src/audit_gouvernement_dataset.py` (`compute_taux_portefeuille_renseigne`) n'est
pas concerné : il rapporte des entrées à des entrées — c'est un taux
d'attribution par entrée, ce qu'il doit être —, et ce rapport d'audit n'est pas
publié.

---
