<a id="audit-champs-deplaces-726"></a>
# Un audit qui lit un champ déplacé ne se tait pas : il crie 62 000 fois (#726) (2026-09-03)

`2026-09-03`

> **En bref** — `audit_pipeline.py` rend **62 705 lignes** dont **99 % sont deux faux constats**, chacun venant d'un champ qu'une décision de schéma a déplacé ou tari sans que l'audit soit rouvert : `sources[].synchro_le` des entrées `nosdeputes`, que **#529** a cessé de collecter tout en les conservant pour la clause ODbL (464 lignes, 100 % du bloc — 464 des **1 115** entrées `sources[]` publiées), et `cohesion_votes[].date`, que **#432** a déplacé dans `pivot_data/scrutins.json` (61 596 lignes, 98 % du rapport — **pas une** des 61 596 entrées ne porte la clé, ce n'est pas un `null` mais une absence de champ) ; ce n'est pas cosmétique, le second bloc enterrait le fait que le **tableau des plages temporelles par groupe était vide par construction depuis #432** ; d'où un troisième code `non_renseigne` séparé de `format_invalide` — une valeur **non-chaîne** reste fautive, une absence ne l'est pas (§2 règle 5) — **agrégé** au rendu quand les deux autres restent énumérés, et une résolution de la date **là où elle vit** via `scrutins_index.charger()`, qui rend le tableau réel (XVIe 2022-07-11 → 2024-06-07, XVIIe 2024-10-08 → 2026-07-21, les 2 fiches Sénat gelées sans `cohesion_votes` à `N/D`) et fait que **les 61 596 dates se résolvent toutes** ; trois motifs fermés (`MOTIFS_DATE_NON_RESOLUE`) **comptés et jamais énumérés** parce que « le scrutin n'est pas dans l'index » et « sa date est illisible » ne se réparent pas au même endroit ; un index absent est un **trou déclaré** (`index_disponible: False`) et un index **vide vaut absent** — `charger()` en rend un sur un fichier introuvable, le croire disponible aurait fait passer « le fichier manquait » pour « ces groupes n'ont pas de scrutin », la panne de #510 ; le défaut de la fonction reste `None` et non un chemin du dépôt (§3b, sujet de #721), la CLI portant `--scrutins` ; mesuré **62 705 → 653 lignes**, rapport groupes **~61 700 → 191**, plages renseignées **0 → 10 sur 12** ; la règle qui reste : **un audit est un consommateur comme un autre et rien ne le prévient qu'un champ a bougé** — les tests fournissaient eux-mêmes un `date` dans l'entrée, donc ils vérifiaient que la fonction lisait un champ que le corpus ne porte pas, et une fixture qui décrit le monde tel que le code l'imagine ne peut pas révéler qu'il a changé (#510). 3 684 tests, 0 échec.

## 1. Le défaut

`audit_pipeline.py` lancé le 03/09/2026 sur le corpus publié (`7a1f8cd7`) rend
**62 705 lignes**, dont **~62 060 — 99 % — sont deux faux constats**. Ils ont la
même cause : l'audit lit un champ qu'une décision de schéma a depuis déplacé ou
tari, et personne ne l'a rouvert depuis.

| Section | Ce qu'elle lit | Invalidé par | Lignes |
| --- | --- | --- | ---: |
| Profils · « Dates de traçabilité invalides ou futures » | `sources[].synchro_le` des entrées `nosdeputes` | **#529** | **464** (100 % du bloc) |
| Groupes · « Plages temporelles par groupe » | `cohesion_votes[].date` | **#432** | **61 596** (98 % du rapport) |

Aucun n'est une régression : l'état est le même à `f635cb60`, `70626a02` et
`25895974`. Ce sont deux hypothèses vraies à l'écriture, fausses depuis, et
jamais relues.

**Ce n'est pas un défaut cosmétique.** Un bloc de 61 596 lignes ne se lit pas :
il enterre ce qui vaudrait d'être lu, et il a enterré le fait que le tableau des
plages temporelles par groupe était **vide par construction depuis #432**. C'est
l'inverse de ce qu'un audit existe pour faire.

## 2. `sources[].synchro_le` — la prémisse a vieilli

`audit_pivot_dataset._erreur_date` rendait `format_invalide` pour toute valeur
absente, et son docstring le justifiait explicitement :

> « ces deux champs sont générés par le pipeline lui-même (pas une donnée source
> potentiellement manquante), une valeur absente ou future y signale toujours une
> anomalie amont. »

**La prémisse était vraie et ne l'est plus.** Depuis #529, les entrées
`sources[].type == "nosdeputes"` sont **conservées sans être recollectées** —
c'est voulu, la clause ODbL en dépend (`AGENTS.md` §7). Rien ne peut plus leur
donner de date.

Mesuré sur les 641 profils publiés : **1 115 entrées `sources[]`**, dont **464
sans `synchro_le`, toutes de type `nosdeputes`** (10 entrées `nosdeputes` en
portent une, héritée). Un `null` y dit « non collecté », pas « format invalide » :
c'est la distinction de `AGENTS.md` §2 règle 5, appliquée à l'outil chargé de la
faire respecter.

**La décision** : un troisième code, `non_renseigne`, séparé de
`format_invalide` et de `date_future`. Une valeur **non-chaîne** (un entier dans
un champ de date) reste `format_invalide` — ce n'est pas une absence, c'est une
valeur d'un type que le champ n'admet pas.

Et le rendu suit la distinction : `non_renseigne` est **agrégé** — un compte par
champ —, les deux autres restent **énumérés**. 464 lignes identiques ne sont pas
de l'information ; le compte, lui, se lit, et il reste **visible**, ce qui est la
différence avec le fait de ne rien afficher.

## 3. `cohesion_votes[].date` — le champ n'existe pas

`schema_groupe.py` le dit depuis #432, à la ligne 196 :

> `"scrutin_id": "an:16:4084",  # référence vers pivot_data/scrutins.json (#432).`
> `                             # `date`, `texte` et `sort` y vivent`

Mesuré : **61 596 entrées `cohesion_votes` sur les 12 fiches, et pas une ne porte
la clé `date`** — ce n'est pas un `null`, c'est une absence de champ.

**La décision** : résoudre la date **là où elle vit**. `_plage_cohesion_votes`
prend l'index partagé (`scrutins_index.charger()`), lit `scrutin_id` et en tire
la date. Le tableau redevient réel :

| Fiche | Cohésion de vote (min → max) |
| --- | --- |
| `AN:REN`, `AN:LR`, `AN:RN`, `AN:SOC`, `AN:LFI` (XVIe) | 2022-07-11 → 2024-06-07 |
| `AN:EPR`, `AN:DR`, `AN:LFI:17`, `AN:SOC:17` (XVIIe) | 2024-10-08 → 2026-07-21 |
| `AN:RN:17` | 2024-10-09 → 2026-07-21 |
| `Senat:LR`, `Senat:SER` | `N/D` — ces fiches gelées (#516) n'ont pas de `cohesion_votes` |

**Les 61 596 dates se résolvent toutes.** Le bloc d'erreurs qui les remplaçait
disparaît donc, et ce qui reste est un compte par motif, à zéro.

### Trois motifs fermés, comptés et jamais énumérés

`MOTIFS_DATE_NON_RESOLUE` : `scrutin_id_absent`, `scrutin_inconnu`,
`date_invalide`. Les distinguer n'est pas de la coquetterie — « le scrutin n'est
pas dans l'index » et « sa date est illisible » ne se réparent pas au même
endroit. Et ils sont **comptés**, jamais listés : ces entrées se comptent à
l'échelle du corpus de scrutins, pas à celle d'une anomalie. C'est la leçon du
défaut qu'on corrige ici.

### Un index absent est un trou déclaré

Sans index, toutes les cellules valent `None` — et `index_disponible: False` les
accompagne, pour qu'aucun lecteur ne lise ce `None` comme « ce groupe n'a pas de
scrutin » (§2 règle 5). Le rendu Markdown le dit en toutes lettres et nomme
l'option qui répare.

**Un index VIDE vaut un index absent**, et ce point a failli m'échapper :
`scrutins_index.charger()` rend un `ScrutinsIndex` vide sur un fichier
introuvable, jamais une exception. Le traiter comme disponible aurait fait passer
« le fichier manquait » pour « ces groupes n'ont pas de scrutin » — exactement la
panne de #510, un index qui ne résout rien et qu'on rend en silence. Le cas est
atteignable depuis la CLI, il est donc testé.

### Le défaut de la fonction reste `None`, pas un chemin du dépôt

`build_report(..., scrutins_index=None)` : la valeur par défaut d'une fonction
qui pointerait dans l'arbre est le piège de `AGENTS.md` §3b, et c'est le sujet de
#721 mesuré sur les tests. La CLI, elle, porte le chemin
(`--scrutins pivot_data/scrutins.json`), parce que c'est son rôle.

## 4. Ce que ça donne

| | Avant | Après |
| --- | ---: | ---: |
| `audit_pipeline.md` | **62 705 lignes** | **653** |
| Rapport groupes seul | ~61 700 | **191** |
| Plages temporelles par groupe | vides sur 12 / 12 | **10 / 12 renseignées** (les 2 gelées n'ont pas de `cohesion_votes`) |
| Dates de traçabilité « invalides » | 464 lignes | **0** — plus un compte agrégé de 464 `non_renseigne` |

## 5. La règle, parce que ce n'est pas la dernière fois

**Un audit est un consommateur comme un autre, et rien ne le prévient qu'un
champ a bougé.** Les deux cas d'ici sont séparés de leur décision par des mois,
et aucun test ne les a vus — parce qu'ils testaient l'audit contre ses propres
hypothèses, sur des fixtures écrites en même temps que lui. Les tests de
`compute_plage_dates_groupes` fournissaient un `date` dans l'entrée : ils
vérifiaient que la fonction lisait bien un champ que le corpus ne porte pas.

Une fixture qui décrit le monde tel que le code l'imagine ne peut pas révéler que
le monde a changé. C'est la leçon de #510 — « mesurer sur des réductions
verbatim de l'archive » — appliquée aux audits.

## 6. Ce que ce lot ne fait pas

- Il ne touche à aucune donnée : les deux audits sont des outils de lecture.
- Il ne traite pas les autres constats du run d'audit, tous légitimes :
  `premier_ministre` renseigné sur **5 / 10** gouvernements, **24 / 641** profils
  sans aucune activité, les 2 fiches Sénat gelées sans `cohesion_votes` (#516).
- Il ne traite pas #721 (des tests qui lisent le cache du poste), même si le
  §3b y est le même travers.

## 7. Vérification

`tests/test_audit_groupe_dataset.py` — les 6 tests de `compute_plage_dates_groupes`
sont **réécrits sur le contrat réel** (l'entrée porte un `scrutin_id`, la date
vient de l'index), et 4 sont ajoutés : la date de l'entrée est ignorée quand elle
existe, les trois motifs sont comptés, l'index absent est déclaré, l'index vide
vaut l'index absent.

`tests/test_audit_pivot_dataset.py` — le cas réel est ajouté (une entrée
`nosdeputes` conservée rend `non_renseigne`), et une valeur non-chaîne reste
`format_invalide`.

Suite complète : **3 684 tests, 0 échec**.
