<a id="roster-unique-par-run-518"></a>
# Un seul roster par run, une reprise sur ce qui est retentable, et des échecs qu'on peut lire (#518) (2026-08-24)

`2026-08-24`

> **En bref** — le roster transite par artifact ; reprise seulement sur ce qui est retentable.

**Ce qui est réparé ici n'est pas la panne d'une source : c'est le fait qu'un
run puisse mourir neuf fois sur la même requête, et qu'on ne puisse pas dire
après coup ce qu'il a refusé de publier.**

## 1. Ce qui s'est passé le 24/08/2026

Le run [`32738726729`](https://github.com/stephieED/Empreinte-politique-src/actions/runs/32738726729)
est le premier lancé après la fusion de #517 (suspension des deux groupes
Sénat). Il n'a **pas committé** : le job `merge-and-pivot` est allé jusqu'à son
dernier garde-fou avant commit et s'y est arrêté.

| Fait | Détail |
| --- | --- |
| Shards roster | **4 échecs sur 8** (1, 4, 5, 7), tous sur `Construction de la liste roster-driven` |
| `merge-and-pivot` | tous les steps verts jusqu'à **`Collecté mais non publié (avant commit)`** (#511), en échec |
| Conséquence | `Committer et pousser` et `Déclencher le déploiement` **skippés** — aucune donnée perdue, rien de publié |
| Retry automatique | **pas de relance**, à raison : la signature n'est ni une préemption runner ni #390 (`retry-generate-data.yml`) |

Deux constats, et ils sont indépendants.

**a. Les 4 shards morts ne sont pas la panne de #516.** Le Sénat étant
suspendu, la seule clé de fetch qui reste est `('deputes', '16')`, servie par
`www.nosdeputes.fr`. Elle a répondu normalement aux 4 autres shards, lancés
dans la même minute (`max-parallel: 4`). Rien de déterministe : 4 échecs et
4 succès sur la **même URL**. C'est la signature d'un aléa transitoire — et
`fetch_full_roster` faisait **un seul essai**, timeout 15 s, aucun backoff, là
où `candidate_profile._get_payload` en fait trois depuis longtemps pour les
appels par candidat. Un hoquet de 15 s tuait donc un job entier, pas un membre,
parce que ce fetch est le premier pas de `generate_roster_candidats.py` et que
#511 refuse — à raison — d'écrire un roster sur une collecte incomplète.

**b. Le garde-fou de #511 a bloqué le commit, et on ne peut pas dire sur qui.**
C'est le point qui a orienté cette issue. Ce que le run a laissé derrière lui :

- l'annotation `::error::COLLECTE_NON_PUBLIEE …` du step, qui **ne nomme
  personne** (le message est constant) ;
- `Process completed with exit code 1` dans l'onglet du job ;
- le rapport qui, lui, nomme les slugs — dans `$GITHUB_STEP_SUMMARY` et dans
  l'artifact `collecte-non-publiee`. Ni l'un ni l'autre n'apparaît dans la
  liste des annotations, et l'artifact expire.

**Ce qui a été écarté par la mesure, et non par raisonnement** : les
**20 profils orphelins** de l'incident de #511 (`68bc094`, 20/08) sont toujours
dans `main` — 229 profils bruts pour 209 pivots. L'hypothèse « ce sont eux qui
bloquent chaque run depuis » est fausse : rejouées sur l'arbre committé, les
deux passes `--pivot-only` (candidats déclarés, puis roster) les publient
toutes les vingt — `audit_collecte_non_publiee` rend **0**. Les 20 sont bien
membres du groupe `REN` de la 16ᵉ législature, donc dans le roster que la
seconde passe construit. Ils se répareront au prochain run qui ira au bout.

Restent, comme population possible des non-publiés, les profils **arrivés
pendant ce run** par les artifacts — et c'est ce qui désigne le défaut
structurel du §2.

## 2. Neuf rosters là où le run n'en a qu'un

`raw_data/roster_candidats.json` était reconstruit par **chacune des 9
invocations** d'un run : les 8 shards `extract-roster-groupes`, puis
`merge-and-pivot`. Neuf fetchs de la même liste de 618 parlementaires, à des
instants différents. Deux défauts, dont le second n'est pas un défaut de coût :

- **fragilité** — neuf requêtes qui doivent **toutes** passer pour qu'un run
  aboutisse, sur une source qui a déjà fait tomber trois runs (#516) ;
- **correction** — rien ne garantissait que les neuf listes soient la **même**.
  Les shards se partagent le roster **par position** (`--shard i/N`, modulo), et
  `merge-and-pivot` normalise en pivot ce que **sa** liste contient. Deux listes
  qui divergent, et un membre collecté par un shard n'est présenté à aucune
  passe pivot : c'est exactement le « collecté mais non publié » de #511,
  produit **sans qu'aucune étape n'échoue**.

Le roster est donc construit **une fois**, par `prepare-roster-matrix` — le job
qui décide déjà du découpage, ce qui en fait le seul endroit où les deux
décisions (quelle liste, combien de tranches) sont prises ensemble — et
transité par l'artifact `roster-candidats`.

**Le repli est conservé, et conditionné.** Chaque consommateur régénère le
roster **si et seulement si** l'artifact manque
(`steps.roster_artifact.outcome == 'failure'`), avec un `::warning::` qui dit
que sa liste peut différer des autres. Sans la condition, on rétablit les neuf
fetchs sans que rien ne le signale ; sans le repli, un `prepare-roster-matrix`
préempté emporterait tout le run, à rebours de #412 §2.1. `if-no-files-found:
error` côté producteur ferme le troisième cas : un artifact **vide**
téléchargé avec succès ferait d'un roster absent un roster de 0 candidat,
c'est-à-dire l'incident de #511.

## 3. Retenter ce qui peut rendre autre chose, et rien d'autre

`fetch_full_roster` reprend désormais jusqu'à 3 tentatives (2 s puis 4 s
d'attente) sur **timeout, erreur de connexion, 5xx** — et sur rien d'autre.

La ligne de partage compte plus que le nombre de tentatives. Un `SSLError`
(certificat expiré : le cas Sénat de #516) et un 4xx sont des **verdicts
déterministes** : les retenter ferait payer trois fois le même échec et
retarderait d'autant le message qui nomme la panne — or c'est précisément sur
la vitesse de ce message que #516 s'est appuyé pour décider d'une suspension.
Piège au passage, verrouillé par un test : `requests.exceptions.SSLError`
**hérite de `ConnectionError`**, si bien qu'un `isinstance` posé dans le
mauvais ordre classerait un certificat expiré comme transitoire.

Coût du chemin nominal : **zéro** (aucune tentative supplémentaire quand la
première réussit). Coût du pire cas : 6 s d'attente, sur un job qui en dure
~200.

**Écarté — un retry générique dans un `Session` monté avec `urllib3.Retry`.**
Il aurait couvert les 5xx et les erreurs de connexion sans code, mais aussi
sans la distinction ci-dessus : `urllib3` ne sait pas qu'un certificat expiré
ne se retente pas, et `fetch_full_roster` accepte une `session` fournie par
l'appelant, qu'on n'a pas à reconfigurer dans son dos.

## 4. Un échec qui ne se lit pas n'est pas un échec déclaré

Les deux garde-fous qui ont tué des runs cette semaine émettent désormais des
**annotations** GitHub Actions :

| Script | Annotation |
| --- | --- |
| `generate_roster_candidats.py` | une `::error::` **par anomalie** (clé de fetch en échec, groupe à 0 membre, roster vide), plus le `ROSTER_INCOMPLET` final. `--autoriser-roster-incomplet` la dégrade en `::warning::` — le run continue, donc plus rien d'autre ne dirait que ce qu'il publie a été mesuré partiellement |
| `audit_collecte_non_publiee.py` | une `::error::` unique qui **nomme les slugs**, plafonnée par `PLAFOND_EXEMPLES` comme le rapport Markdown (543 annotations identiques noieraient l'onglet au lieu de le renseigner) |

Trois copies privées et identiques de ces trois lignes existaient déjà
(`generate_all_profiles._annoter_github`, `budget_collecte.annoncer_troncature`,
`check_quality_gate._gha_annotation`). #518 en ajoutait deux : à cinq, la
question n'est plus de savoir si elles divergeront. D'où `src/gha.py`, un
module d'une fonction. **Les trois existantes ne sont pas migrées** — elles
sont couvertes par leurs propres tests et n'ont rien demandé ; ce module est
leur destination, pas un chantier de réécriture ouvert par cette issue.

Deux détails qui sont le fond du sujet, et pas de la forme :

- l'annotation part sur **stdout**. GitHub ne lit les commandes de workflow que
  là, alors que ce dépôt imprime ses anomalies sur `stderr` : un `::error::`
  posté sur `stderr` s'affiche dans le log et **ne crée aucune annotation** ;
- le message est **aplati** sur une ligne. Une commande de workflow s'arrête au
  premier saut de ligne — non aplatie, elle publierait sa première ligne et
  déverserait le reste en texte brut.

## 5. Ce que cette issue ne fait pas

- **Elle ne répare pas les 20 orphelins de `68bc094`.** Ils se réparent d'un
  run qui va au bout (mesuré au §1), et les publier à la main court-circuiterait
  la passe pivot qui est censée les produire.
- **Elle n'ajoute aucune tolérance.** `allow_unpublished_profiles` existe déjà
  et reste à `false` : le remède d'un écart collecté/publié est de le
  comprendre, pas de le tolérer (#470).
- **Elle ne touche pas au budget de `extract-roster-groupes`**
  (`--budget-collecte-secondes 0`, #514) ni à l'ordre de traitement
  d'`extract-senat` : deux items de `ROADMAP.md` qui n'ont pas de rapport avec
  ce run.

Verrouillé par `tests/test_roster_reprise_reseau.py` (9 tests),
`tests/test_annotations_gha.py` (12) et
`tests/test_ci_roster_unique_par_run.py` (8). Suite complète : 2 070 tests.

---

