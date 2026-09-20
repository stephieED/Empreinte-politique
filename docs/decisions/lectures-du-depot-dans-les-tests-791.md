<a id="lectures-du-depot-dans-les-tests-791"></a>
# Un garde-fou posé sur `builtins.open` ne voit pas `pathlib` (#791) (2026-09-10)

`2026-09-10`

> **En bref** — `tests/conftest.py` refusait le cache du poste et le corpus publié, mais pas les `.json` de `raw_data/` qu’un run réécrit : trois tests du 08/09 sont passés au rouge **en local seulement** quand le run `34278343461` a écrit l’entrée d’Asselineau dans `correspondance_acteurs_an.json`, la CI ne matérialisant pas ce fichier ; **la piste de l’issue — étendre le filtre `builtins.open` — était insuffisante et la mesure le dit** : `Path.open()` appelle `io.open`, `builtins.open` en est une AUTRE référence, et sur les **144 tests** qui ouvraient un fichier du dépôt, **40** passaient par `builtins.open` contre **105** par `pathlib` — **le garde-fou de #721 avait donc le même trou depuis son écriture**, et un test le traversait en créant `.cache/amendements_an/17/` dans le dépôt pour y écrire. D’où trois portes coupées au lieu d’une ; ce qu’un run réécrit servi figé (`correspondance_acteurs_an.json` 64 ouvertures → **0**, `resolutions_candidats.json` 1 → **0**, le marqueur de cache 2 → **0**) ; et ce qui est une **configuration committée** — `groupes_reels.json`, `gouvernements_reels.json`, `candidats.json` — **déclaré** fichier par fichier (`pytest.mark.lit_reference_committee`, 18 fichiers de tests) plutôt que figé, parce que figer `test_repository_groupes_reels_json_is_valid` reviendrait à lui faire valider une copie. La déclaration n’est acceptée **que si le chemin est dans le `sparse-checkout`** : d’où l’entrée de `raw_data/candidats.json` (20 Kio) dans la liste blanche, cinq tests de validité qui se `skip`aient en CI et qui y tournent enfin — seul changement du lot dans `.github/workflows/`, réversible d’une ligne. Troisième mémo de module découvert à la mesure (le piège de #767) : `_MEMBRES_GROUPES_SUSPENDUS` est construit une fois par processus, si bien qu’un seul test lisait `groupes_reels.json` et onze consommaient sa lecture sans rouvrir de fichier — vidé aux deux bouts, le compte de lecteurs passe de 96 à **110**, le vrai chiffre. **41 tests** n’ouvrent plus aucun des trois fichiers disparus, **27** plus aucun fichier du dépôt ; aucun test supprimé ni désarmé. Suite complète 4 380 → **4 399 passés, 0 échec**.

## 1. Le défaut, et ce qu'il n'était pas

Trois tests écrits le 08/09 passaient. Le run `34278343461` a écrit dans la nuit
l'entrée sourcée d'Asselineau dans `raw_data/correspondance_acteurs_an.json`, et
ils ont échoué le lendemain **en local seulement** : le `sparse-checkout` de
`tests.yml` ne matérialise pas ce fichier, donc la CI ne l'a jamais lu. Vert en
CI pour une mauvaise raison, rouge chez la propriétaire.

L'issue proposait d'étendre `_NOMMES_POUR_ETRE_REFUSES`, c'est-à-dire le filtre
posé sur `builtins.open`. **Cette piste est insuffisante, et la mesure le dit.**

## 2. La mesure, avant d'agir

Suite complète (4 380 tests), `builtins.open`, `io.open` et `Path.open`
instrumentés simultanément, 10/09/2026 :

| Fichier du dépôt réellement ouvert | Ouvertures | Tests | Voie |
| --- | ---: | ---: | --- |
| `raw_data/groupes_reels.json` | 692 | 96 | `pathlib` |
| `raw_data/correspondance_acteurs_an.json` | 64 | 40 | `builtins.open` |
| `raw_data/candidats.json` | 10 | 5 | `pathlib` |
| `raw_data/gouvernements_reels.json` | 6 | 3 | `pathlib` |
| `.cache/amendements_an/17/failed_run_id` | 2 | 1 | `pathlib` |
| `raw_data/resolutions_candidats.json` | 1 | 1 | `builtins.open` |

**144 tests distincts. 40 atteignent un fichier par `builtins.open`, 105 par
`pathlib`** (un test par les deux voies).

`Path.open()` appelle `io.open` ; `builtins.open` est une **autre référence** à
la même fonction, et patcher l'une laisse l'autre intacte (CPython 3.12). Un
refus posé sur `builtins.open` seul n'aurait donc attrapé que 40 des 144.

**Corollaire : le garde-fou de #721 avait le même trou depuis le jour de son
écriture**, et un test le traversait.
`test_candidate_profile.py::test_download_and_build_amendement_index_disk_marker_from_different_run_is_ignored`
calculait le chemin de son marqueur **avant** de régler
`AMENDEMENTS_CACHE_DIR`, créait `.cache/amendements_an/17/` dans le dépôt et y
écrivait — par `Path.write_text`, donc par `io.open`, donc invisible.

## 3. Ce qui est décidé

### 3.1 Trois portes coupées, pas une

`tests/conftest.py` installe le même filtre sur `builtins.open`, `io.open` et
`pathlib.Path.open`, par `monkeypatch` (la restauration est donc garantie même
si le test lève). Le filtre refuse deux populations : le `.cache/` du dépôt
(#721) et les `.json` de `raw_data/` (#791), `raw_data/profiles/` excepté — il a
déjà son propre diagnostic, et le message à donner n'est pas le même.

### 3.2 Ce qu'un run réécrit est servi figé

`correspondance_acteurs_an.json` et `resolutions_candidats.json` sont réécrits à
chaque run et absents du `sparse-checkout`. Les défauts de module qui y menaient
sont réglés, pour toute la suite, sur des fixtures :
`tests/fixtures/correspondance_acteurs_an_extrait.json` (13 entrées, déjà
utilisée par quatre fichiers de tests) et
`tests/fixtures/resolutions_candidats_neutre.json`.

Aucun des 40 tests concernés ne demandait quoi que ce soit au contenu réel : ils
traversaient `charger_correspondance()` sur son chemin par défaut sans jamais
regarder ce qui en sortait.

**Un littéral recopié échappait au réglage** : `fetch_candidats_declares.py`
portait `default="raw_data/correspondance_acteurs_an.json"` en dur. Il lit
désormais `correspondance_acteurs_an.CHEMIN_PAR_DEFAUT`, seul endroit où
l'emplacement de la table se déclare.

### 3.3 Ce qui est une configuration committée est **déclaré**, jamais figé

`groupes_reels.json`, `gouvernements_reels.json` et `candidats.json` ne sont pas
réécrits par un run : ce sont des fichiers éditoriaux, et la suite porte des
tests **dont le sujet est leur validité** (`test_repository_groupes_reels_json_is_valid`,
les deux entrées Sénat de #528, la table des positions de #686). Les figer
reviendrait à valider une copie, c'est-à-dire à désarmer le test.

Ils restent donc lisibles, mais jamais par accident : **18 fichiers de tests**
portent `pytestmark = pytest.mark.lit_reference_committee("<chemin>")`, et le
garde-fou n'accepte la déclaration **que si le chemin est dans le
`sparse-checkout` de `tests.yml`**. C'est la condition qui manquait : un fichier
que la CI ne télécharge pas n'est lu qu'en local, sur ce qu'un run y a laissé —
#791 tel quel.

### 3.4 `raw_data/candidats.json` entre dans le `sparse-checkout`

Conséquence directe de la condition ci-dessus. Quatre tests de
`test_fetch_candidats_declares_753.py` et un de `test_perimetre_candidats_760.py`
portent sur la validité de ce fichier committé — aucun doublon de nom ni de
slug, tout statut publié connu, aucune famille inventée — et **se `pytest.skip`aient
en CI**, faute de fichier. Leur garantie ne tenait qu'en local.

Le fichier pèse 20 Kio. Un commit de données du bot passe désormais sous ces
assertions : c'est exactement le canari que l'absence de `paths-ignore` dans
`tests.yml` veut voir chanter. **C'est le seul changement de ce lot dans
`.github/workflows/`, et il est réversible d'une ligne.**

### 3.5 Le piège de #767, aux deux bouts

`correspondance_acteurs_an._MEMO` et `perimetre_candidats._MEMO_RESOLUTIONS`
sont des `dict` de module, pas des `lru_cache` : rien ne s'annule tout seul. Ils
sont vidés à l'entrée **et** à la sortie de la fixture.

Un troisième s'est révélé à la mesure : `generate_all_profiles._MEMBRES_GROUPES_SUSPENDUS`
est construit **une fois par processus**. Un seul test lisait réellement
`groupes_reels.json` et onze autres consommaient sa lecture *sans rouvrir de
fichier*, donc sans que le garde-fou puisse les voir. D'où
`vider_index_groupes_suspendus()`, appelée aux deux bouts — et le compte de
tests lecteurs de `groupes_reels.json` passe de **96 à 110**, ce qui est le vrai
chiffre.

## 4. Le témoin

`tests/test_raw_data_du_depot_791.py` (18 tests) vérifie que chaque garde-fou
mord **par les trois portes**, que le refus nomme le fichier et donne l'idiome,
qu'une déclaration hors liste blanche lève, et que les mémos sont vides à
l'entrée d'un test.

Il porte aussi une preuve de **restauration** : le filtre du test courant a
capturé la vraie fonction d'ouverture, pas le filtre du test précédent — sans
quoi les filtres s'empileraient d'un test à l'autre. Ce témoin a mordu pour de
vrai : sous le greffon de mesure, qui est lui-même une couche supplémentaire,
c'est le seul test de la suite qui échoue.

## 5. Résultat mesuré

| | Avant | Après |
| --- | ---: | ---: |
| Suite complète | 4 380 passés, 0 échec | **4 399 passés, 0 échec** |
| Fichiers du dépôt ouverts par la suite | 6 | **3** |
| Tests ouvrant un de ces fichiers | 144 | 118 |
| Ouvertures de `correspondance_acteurs_an.json` | 64 | **0** |
| Ouvertures de `resolutions_candidats.json` | 1 | **0** |
| Ouvertures de `.cache/amendements_an/17/failed_run_id` | 2 | **0** |

**41 tests** n'ouvrent plus aucun des trois fichiers disparus ; **27** n'ouvrent
plus aucun fichier du dépôt du tout. Les 117 autres n'ouvrent que des
configurations déclarées, toutes trois présentes dans le `sparse-checkout`,
donc lues à l'identique en CI et en local.

**Aucun test n'a été supprimé ni désarmé.** Un seul a été corrigé au fond
(le marqueur d'amendements de §2), parce qu'il écrivait dans le dépôt.

## 6. Alternatives écartées

- **Étendre le seul filtre `builtins.open`**, comme l'issue le proposait : 40
  des 144 tests attrapés, et le trou de #721 laissé ouvert. Mesuré, pas supposé.
- **Figer aussi `groupes_reels.json` et `gouvernements_reels.json`** : cela
  transforme `test_repository_..._is_valid` en validation d'une copie. Un test
  qu'on fige pour qu'il passe est un test qu'on retire.
- **Rediriger globalement les constantes de chemin vers un répertoire jetable** :
  déjà essayé en #721, et déjà écarté — cela casse les dix tests qui isolent par
  `monkeypatch.chdir(tmp_path)`.
- **Un relevé statique des littéraux à la place du garde-fou** :
  `test_ci_perimetre_sparse_checkout.py` le fait, et ne voit que les chemins
  écrits en dur. Les 103 lectures par `pathlib` passaient toutes par des
  **défauts de module**, qu'aucun littéral de test ne nomme.

## 7. Ce que ce lot ne fait pas

Un **paramètre par défaut** lié à la définition d'une fonction
(`declare_hors_an_par_identifiant(nom, chemin=RESOLUTIONS_PAR_DEFAUT)`) ne suit
pas le réglage de la constante : le régler ne le déplace pas. Ces cas ne sont
pas silencieux pour autant — le garde-fou les arrête, bruyamment, ce qui reste
le bon échec. Les appelants de production lisent la constante à l'appel.
