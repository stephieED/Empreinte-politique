<a id="index-scrutins-europeens-901"></a>
# L'index des scrutins européens publie les effectifs, jamais le sort (#901) (2026-09-14)

`2026-09-14`

> **En bref** — #901 demandait un `scrutin_id` pour les 11 013 votes européens, au motif qu'« une entrée retombe sur `scrutin_non_resolu`, qui ne porte ni `type_vote` ni `texte` ». **Remesuré le 14/09/2026 : elle porte les deux.** `nature` et `titre` sont renseignés à **100 %**, `reference_dossier` à **96 %**, et `_porte_sur_ensemble` existait déjà dans le normaliseur. Ce qui manquait vraiment est ailleurs, et aucun profil ne peut le porter seul : le scrutin **vu d'ensemble** — pour, contre, abstention, ventilés par groupe politique. La source les publie sur **44 556 des 44 648 scrutins** (99,8 %). `pivot_data/scrutins_europeens.json` indexe les **5 571** scrutins que les 7 profils européens citent, pour **3,8 Mo**.

## 1. Ce que l'issue décrivait, et ce que la mesure a trouvé

| Champ de `scrutin_non_resolu` | Renseigné | L'issue disait |
| --- | ---: | --- |
| `nature` — 27 valeurs, « vote unique », « ensemble du texte »… | **100 %** | « ni `type_vote` » |
| `titre` | **100 %** | « ni `texte` » |
| `reference_dossier` | 96 % | — |
| `numero_scrutin`, `date`, `source_url` | **100 %** | — |

Deuxième fois dans ce lot : le **point 2** avait le même diagnostic, et la même correction — `amendement_non_resolu` porte `texte_vise` et `numero` à 100 %. Un bloc nommé « non résolu » se lit comme vide ; il ne l'est pas. Ce qui manque, dans les deux cas, est un **lecteur**, pas une collecte.

## 2. Ce que l'index ajoute, et la règle qui l'encadre

Les effectifs par scrutin, et leur ventilation par groupe. C'est ce qui permet de juxtaposer, **sur un scrutin sourcé**, la position d'un député et la position majoritaire de son groupe — un fait publiable que `AGENTS.md` §2 règle 7 autorise nommément.

La même règle dit l'interdit, et il est proche : **jamais un compte**. « A voté contre son groupe 47 fois » est l'indice individuel mesuré contre une moyenne de groupe, réservé au rapport interne. L'index publie donc des effectifs **par scrutin**, jamais un cumul par personne — et il ne porte aucune liste nominative.

## 3. Trois refus, et chacun a sa raison

**Le sort n'est pas déduit.** Conclure « adopté » de `pour > contre` serait une inférence : le Parlement européen vote aussi à la majorité qualifiée des membres qui le composent, et le dump ne dit pas quelle règle s'appliquait. Un sort déduit d'une comparaison aurait l'air d'un fait sourcé sans en être un (§2 règle 5). `totaux` le remplace.

**Une position absente ne vaut pas zéro.** « La source n'a pas publié ce décompte » et « personne n'a voté ainsi » ne sont pas la même chose : la clé est absente.

**Un code de position inconnu n'est rangé nulle part.** Les trois que la source emploie sont nommés ; une quatrième apparaîtrait sous son propre nom plutôt que d'être glissée dans l'une des trois.

## 4. L'identifiant, et les deux formes du `voteid`

`pe:<voteid>`. Le `voteid` vient de la source et le préfixe dit l'institution — c'est ce que [#431](amendements-cle-uid.md) refusait de faire **sous `an:`** : ranger un scrutin européen dans un espace de noms qui annonce l'Assemblée.

Le `voteid` a deux formes, et elles sont reprises telles quelles : sur les 5 571 cités, **4 855** sont des entiers (`7649`) et **716** des chaînes composites (`'2017-06-01 00:00:00-1.'`), espaces et point final compris. Normaliser la seconde produirait une clé que la source ne connaît pas, et la jointure depuis un profil se fait de toute façon sur `numero_scrutin`. L'unicité est vérifiée — **5 571 identifiants distincts sur 5 571** — et un test la gèle.

Ces deux formes ont d'ailleurs cassé le tri au premier essai : comparer un entier à une chaîne lève. La clé de tri passe par `str`, et un test le retient — un ordre instable ferait bouger l'index sans que rien n'ait bougé.

## 5. Le périmètre : ce que le corpus cite

**5 571 scrutins**, pas 44 648. L'index suit le corpus, il ne le précède pas : indexer tout le dump ferait porter au dépôt huit fois le poids utile. Même choix que `pivot_data/scrutins.json` côté Assemblée, qui pèse 9,8 Mo pour 17 748 scrutins.

Un scrutin cité mais absent du dump ne produit **aucune entrée** : il est compté et dit, jamais fabriqué. Et un dump indisponible **lève** au lieu de rendre un index vide, qui se lirait comme « aucun scrutin européen » — la confusion de #510.

## 6. Ce que ce lot ne fait pas

**Il ne renseigne pas `scrutin_id` dans les profils.** Les 11 013 votes gardent `scrutin_id: null` et leur `scrutin_non_resolu` : y écrire `pe:<voteid>` changerait le contrat de `scrutins_index.decomposer_id`, qui refuse tout ce qui ne commence pas par `an:`, et toucherait la fusion de 11 013 entrées. La jointure se fait sur `numero_scrutin`, qui est déjà publié des deux côtés. C'est un lot à part, s'il est jamais demandé.
