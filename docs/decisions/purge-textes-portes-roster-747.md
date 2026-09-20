# Un profil de roster ne porte pas une liste que sa propre collecte déclare écartée — purge des 49 `textes_portes` résiduels (#747)

`2026-09-07`

> **En bref** — l'atterrissage de #743 a montré **49 entrées** portant `sort: null` **et** `sort_non_resolu: null`, une absence sans cause que §2 règle 5 refuse et que le schéma promettait sans l'imposer, `validate_profil()` ne s'armant que sur un motif **non nul** ; toutes de provenance `roster_groupe`, **0 sur les 13 fiches publiées**, et toutes issues d'une fenêtre de trois jours — les 15 profils porteurs sont **tous les 15** dans le snapshot du 16/08/2026 (48 profils), collectés en mode plein avant que `a9f24d66` (#357) ne pose `--skip-dossiers-legislatifs` **en dur** sur `extract-roster-groupes` ; la fusion additive les conservait parce que la liste neuve est **vide et non incomplète**, donc les reports nommés de #689 et #743 n'avaient **aucune clé** sur quoi se poser — d'où la co-localisation exacte qui a servi de preuve, les 44 dossiers sans sort étant un sous-ensemble strict des 49 sans `nature_texte` que le gate comptait déjà ; **purge et non réparation**, décision inversée en cours d'arbitrage : la première recommandation pesait la **valeur** des faits sans regarder **qui les tiendrait à jour**, or la collecte de cette liste est coupée en dur pour cette population et un `sort` réparé sur un dossier `navette_en_cours` deviendrait faux **en silence** ; rien n'est perdu du corpus (**9** des 44 dossiers publient déjà un `statut` résolu sur une fiche de gouvernement, **34** sont dans `commissions_dossiers.json`) et le poids ne plaidait rien (**20,3 Ko**) ; **commit dédié plutôt qu'`allow_declared_losses`**, qui désarmerait le contrôle de perte du run entier ; les deux étages purgés mais **le critère ne les traverse pas** — `provenance` est un champ du pivot, et `collecte_ecartee` seul ne discrimine rien puisqu'un candidat déclaré est aussi un membre de roster : le critère brut seul aurait supprimé **71 dossiers sur 4 fiches publiées** ; l'invariant devient un contrôle, et il a fait tomber un **second chemin vivant** — `normalize_parltrack_dumps` publiait une entrée sans sort **ni** motif, défaut latent qu'aucune mesure n'aurait vu —, d'où un quatrième motif **`source_sans_sort`** ; ce que le lot ne fait pas : l'avertissement #689 tombe de 34 à **4** et non à 0 (prévision fausse, corrigée — 3 candidats déclarés restants), et `audit_integrite_referentielle` ne couvre toujours pas `textes_portes[].dossier_id`. 8 tests, suite complète à 3 858, 0 échec.

## Contexte

Le run du 06/09/2026 (`34053322456`, commit de données `e6503c29`) a fait
atterrir #743 dans les données publiées : `sort` est renseigné sur **423 des
472** entrées `textes_portes[]`. Les **49** restantes portent `sort: null`
**et** `sort_non_resolu: null` — une absence sans cause déclarée, que
`AGENTS.md` §2 règle 5 refuse et que le commentaire de `src/schema_pivot.py`
promettait déjà (« `null` s'accompagne TOUJOURS de `sort_non_resolu` »).
`validate_profil()` ne l'attrapait pas : il ne contrôlait `sort_non_resolu` que
lorsqu'il était **non nul**, c'est-à-dire la moitié bruyante du couple.

Ces 49 entrées (44 dossiers distincts, 15 profils) sont **toutes** de
provenance `roster_groupe`, et **aucune** n'est sur une fiche publiée : 0 des
13 candidats déclarés.

### D'où elles viennent : une fenêtre de trois jours

Les 15 profils porteurs sont **tous les 15** présents dans le snapshot du
16/08/2026 07:55 UTC, quand le corpus comptait 48 profils. Ils ont été
collectés par `extract-roster-groupes` en **mode plein**. Le commit `a9f24d66`
(16/08 13:16 UTC, #357) a ensuite posé `--skip-dossiers-legislatifs` **en dur**
sur ce job. Depuis, aucun profil de roster écrit ne porte une seule entrée :
**613 des 628** membres de roster publient `textes_portes: []`, et 609
déclarent `meta.collecte_ecartee: ["textes_portes"]` (#539).

La fusion additive (« une collecte vide n'écrase jamais ») les conserve
indéfiniment. C'est le mécanisme exact du trou, et il n'est pas celui qu'on
suppose : la liste neuve est **vide**, pas incomplète. Les reports nommés de
#689 (`nature_texte`) et #743 (`sort`) ne se posent que sur une clé présente
dans la liste neuve — ils n'ont donc **rien** sur quoi se poser. D'où une
co-localisation exacte, qui a servi de preuve : les 44 dossiers sans `sort`
sont un sous-ensemble strict des 49 entrées sans `nature_texte` que
l'avertissement #689 comptait déjà, et dont il annonçait à tort qu'elles « se
résorbent au prochain run réel » — les runs du 04/09 et du 06/09 affichaient
tous deux exactement 34.

## Décision

**Purger, et non réparer.** Les 49 entrées sont retirées des **deux** étages ;
la cible est la **liste vide**, jamais la clé retirée — c'est la forme que
portent déjà les 613 autres membres de roster, et une clé absente dirait
« jamais collecté » là où `[]` dit « rien à publier ».

La première recommandation portée à l'arbitrage était l'inverse — réparer, au
motif que le `sort` de ces dossiers est déjà dérivé ailleurs dans le même run
et qu'une purge jetterait des faits sourcés. Elle raisonnait sur la **valeur**
des faits sans regarder **qui les tiendrait à jour** :

| | |
| --- | --- |
| Le fichier se contredit lui-même | Les 15 profils déclarent `meta.collecte_ecartee: ["textes_portes"]` — « cette liste n'a pas été demandée » — et la portent quand même |
| Personne ne les lit | `BLOCS_LUS_MEMBRE` exclut nommément `textes_portes` (`group_profile.py`) ; le manifeste web ne rend que les 13 candidats déclarés |
| **Rien ne les rafraîchirait** | La collecte de cette liste est coupée **en dur** sur ce job. Un `sort` réparé sur un dossier `navette_en_cours` — 215 entrées dans le corpus — deviendrait faux **en silence** à mesure que le texte avance |
| Rien n'est perdu du corpus | **9** des 44 dossiers sont déjà publiés avec un `statut` résolu sur une fiche de gouvernement, calculé par la même `_determine_statut()` ; **34** des 44 sont dans `commissions_dossiers.json` |

Le poids ne plaide rien : **20,3 Ko**. C'est la contradiction, pas l'espace
disque, qui décide.

La purge est **stable** : la fusion étant additive sur une liste neuve vide,
rien ne recrée ces entrées au run suivant. Un seul passage suffit, et le script
est idempotent.

### Un commit dédié, pas `allow_declared_losses`

Le drapeau existe pour déclarer une perte légitime (#460/#470), mais il
désarme le contrôle de perte pour le **run entier** — y compris les pertes
qu'on n'a pas vues venir. Le garde-fou ne tourne que dans `generate-data.yml` :
une purge portée par un commit dédié laisse le run suivant comparer à une base
**déjà purgée**, et il ne voit aucune perte. Le diff est relu une fois, dans une
PR, au lieu d'être couvert par un drapeau global.

### Le critère ne se transpose pas d'un étage à l'autre

Leçon de #729/#730 : une suppression qui ne passe qu'un étage se fait rejouer
par l'autre — `normalize_profil` dérive `textes_portes` de
`dossiers_legislatifs`, donc purger le seul pivot laisserait la prochaine passe
`--pivot-only` le réécrire. Mais **le critère, lui, ne traverse pas** :

- `meta.provenance` est un champ du **pivot** ; le brut ne le porte pas.
- `meta.collecte_ecartee`, que le brut porte bien, **ne discrimine rien ici** :
  un candidat déclaré est aussi un membre de roster, dont le job réécrit le
  `meta`. **4 des 13 candidats déclarés** publient
  `collecte_ecartee: ["textes_portes"]` tout en portant des `textes_portes`
  pleinement qualifiés, collectés par `extract-an`.

Le critère brut seul aurait donc supprimé **71 dossiers sur 4 fiches candidats
publiées** — gabriel-attal 34, marine-le-pen 23, laurent-wauquiez 9,
jerome-guedj 5. D'où la forme retenue : les slugs cibles sont établis **une
fois**, sur le pivot, seul étage qui sache de quelle population relève un
profil ; les deux étages sont ensuite purgés sur cette liste. **Un étage ne
redécide jamais seul de ce qu'il supprime.** C'est le test le plus important du
lot.

### L'invariant devient un contrôle, et il révèle un second chemin

`validate_profil()` refuse désormais `sort: null` sans `sort_non_resolu`.

Ce contrôle a immédiatement fait tomber un producteur vivant :
`normalize_parltrack_dumps._make_texte_porte` — le chemin européen — écrivait
une entrée qui ne disait **rien** du sort, ni le champ ni le motif. #743
n'avait instruit que le chemin AN, et le contrôle existant ne s'armait que sur
un motif **non nul** : le cas était invisible des deux côtés. Le dump ParlTrack
ne porte aucune issue de dossier — `get_dossiers_for_mep` indexe `reference`,
`titre`, `comite`, `role`, `date`, `source_url`, et rien d'autre. D'où un
quatrième motif, **`source_sans_sort`**, qui n'est ni un trou à combler
(`fam_code_inconnu`) ni une panne (`archives_indisponibles`) ni un état
légitime de la procédure (`sans_decision`), mais un fait de la source.

Le corpus ne portait aucune entrée de ce chemin au moment du lot (0 profil
enrichi au run du 06/09) : le défaut était **latent**, et c'est le contrôle qui
l'a sorti, pas une mesure.

## Ce que le lot ne fait pas

- **L'avertissement #689 tombe de 34 à 4, pas à 0.** La prévision portée à
  l'arbitrage disait 0 ; elle était fausse. Restent 4 entrées sans
  `nature_texte` sur **3 candidats déclarés** — jean-luc-melenchon 2/33,
  edouard-philippe 1/283, gabriel-attal 1/34 —, d'une autre cause, sur des
  fiches publiées. Et son message continue d'annoncer une résorption « au
  prochain run réel » que deux runs consécutifs ont démentie.
- **`audit_integrite_referentielle` ne couvre toujours pas
  `textes_portes[].dossier_id`.** Trois renvois sont contrôlés
  (`votes[].scrutin_id`, `amendements[].amendement_id`,
  `cohesion_votes[].scrutin_id`) ; aucune garde ne confronte le `sort` d'un
  profil au `statut` du même dossier sur une fiche de gouvernement, alors que
  **9 dossiers** publient les deux.

## Alternative écartée

**Réparer les 49 entrées** — reporter le `sort` depuis les archives déjà en
cache, sans un seul appel réseau. Écartée pour la raison qui a inversé la
recommandation initiale : la donnée réparée serait figée le jour du lot et
qu'aucun run ne la reprendrait, la collecte de cette liste étant coupée en dur
pour cette population. Un fait juste qui se périme en silence est pire qu'une
absence déclarée.

## Mesures

| | Avant | Après |
| --- | --- | --- |
| Entrées `textes_portes[]` publiées | 472 | 423 |
| Entrées sans `sort` | 49 | 0 |
| Entrées `sort: null` sans motif | 49 | 0 |
| Membres de roster portant la liste | 15 / 628 | 0 / 628 |
| Avertissement #689 « sans nature établie » | 34 | 4 |
| Profils pivot invalides | 0 | 0 |

Suite complète : 3 858 tests, 0 échec.
