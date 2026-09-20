<a id="cache-du-poste-hors-des-tests-721"></a>
# Six tests lisaient le cache du poste : la CI était verte parce que la machine est vide (#721) (2026-09-03)

`2026-09-03`

> **En bref** — six tests rendaient **688** interventions là où leur fixture en attendait **1** : ils patchaient le **constructeur** (`_build_acteur_interventions_syceron_index`) mais pas `_read_cached_interventions_syceron_acteur`, qui **lit le cache avant de construire**, et les **onze** constantes de cache du dépôt valent `Path(".cache") / …`, donc un chemin **relatif au répertoire courant** — la racine du dépôt en local, le piège que `AGENTS.md` §3b nomme déjà ; **la CI est verte parce que son checkout partiel ne pose pas `.cache/`**, pas parce que le test est juste, et ils passaient en local depuis #719 parce que le cache du poste est périmé donc rejeté — deux raisons accidentelles, aucune bonne, et c'est ce qui a mis la puce à l'oreille (six tests devenus verts sans qu'on les touche) ; **rediriger les constantes a été essayé, mesuré et écarté** : dix tests cassent, ceux qui isolent déjà leur cache par `monkeypatch.chdir(tmp_path)` et écrivent sous un `.cache` relatif — une constante rendue absolue leur retire l'isolation et les envoie sur le réseau, où la coupure de #473 les arrête —, l'idiome existant étant bon, ce qui manquait était de **voir** ceux qui ne l'appliquent pas ; d'où un garde-fou dans `conftest.py` sur le patron de #473 : `builtins.open` filtré, toute ouverture sous le `.cache` **du dépôt** lève en nommant le fichier et en disant quoi faire, avec le test grossier sur la chaîne d'abord (`resolve()` à chaque ouverture coûterait cher pour un cas rarissime), `bytes` et descripteurs traités, et un `.cache` sous `tmp_path` qui ne déclenche rien ; le littéral `.cache` s'est fait prendre par `test_ci_perimetre_sparse_checkout`, d'où `_NOMMES_POUR_ETRE_REFUSES` — une exemption **explicite** plutôt qu'un chemin construit autrement qui aurait esquivé le relevé et masqué le garde-fou —, verrouillée par un test parce que le jour où `.cache` entrerait dans le sparse-checkout les tests liraient le cache du **runner** ; la propriété dont tout dépend (**les constantes restent relatives**, sans quoi `chdir` n'isole plus) est testée sur les 7 modules qui en portent, avec un **compteur-témoin** contre le trou muet de #510 ; limites déclarées — le garde-fou ne couvre que `open()` (un `Path.is_dir()` seul passerait, accepté : une existence lue ne sert pas de données fausses) et ne dit rien des écritures. 11 tests, deux mutations vérifiées échouantes, suite complète à 3 694, 0 échec.

## 1. Le défaut

Six tests échouaient **en local et pas en CI**, en rendant **688** interventions
là où leur fixture en attendait **1** :

- `tests/test_candidate_profile.py` — `test_fetch_interventions_syceron_maps_actor_to_candidate_interventions`,
  `test_fetch_interventions_syceron_aggregates_multiple_legislatures` ;
- `tests/test_budget_interventions.py` — ses quatre tests.

Ils lisaient le **cache Syceron du poste** au lieu de leur fixture.

## 2. Le mécanisme

Les tests patchent le **constructeur** :

```python
with patch("candidate_profile._build_acteur_interventions_syceron_index", return_value=index):
    result = fetch_interventions_syceron(...)
```

Mais `fetch_interventions_syceron` appelle `_interventions_syceron_acteur`, qui
**lit le cache avant de construire** :

```python
entrees = _read_cached_interventions_syceron_acteur(legislature, acteur_ref, ...)
if entrees is not None:
    return entrees          # le constructeur patché n'est jamais appelé
```

Et les **onze** constantes de cache du dépôt valent `Path(".cache") / …` —
`syceron_debates.py:42` pour celle-ci —, donc un chemin **relatif au répertoire
courant**, qui est la racine du dépôt quand pytest tourne en local. C'est le
piège que `AGENTS.md` §3b nomme déjà : *« Watch CLI/function defaults pointing
into the repo. »*

**Pourquoi la CI est verte** : `tests.yml` fait un checkout partiel, `.cache/`
n'est pas versionné, le répertoire est absent — la lecture rend `None` et le
patch s'applique. Le test ne passe pas parce qu'il est juste, il passe parce que
la machine est vide.

**Et pourquoi ils passaient en local depuis #719** : ce lot refuse un index
Syceron sans `sujet_code_grammaire`, et le cache du poste est antérieur, donc
rejeté. Deux raisons accidentelles, aucune bonne — c'est même ce qui a mis la
puce à l'oreille : six tests devenus verts sans qu'on les touche.

## 3. Le remède écarté, et pourquoi

**Rediriger les constantes** vers un répertoire jetable, par une fixture
`autouse` qui les balaye dans `sys.modules`. Essayé, mesuré, écarté : **dix
tests cassent**, ceux de `test_syceron_acteur_ref.py` et de
`test_index_interventions_cache_partiel.py`, qui isolent déjà leur cache par
`monkeypatch.chdir(tmp_path)` puis écrivent sous `.cache/` **relatif**. Une
constante rendue absolue leur retire cette isolation, et ils partent chercher
l'archive sur le réseau — où la coupure de #473 les arrête.

L'idiome existant est bon. Ce qui manquait n'était pas une redirection, c'était
de **voir** les tests qui ne l'appliquent pas.

## 4. La décision

Un garde-fou dans `tests/conftest.py`, sur le patron de la coupure réseau de
#473 : `builtins.open` est filtré, et toute ouverture sous le `.cache` **du
dépôt** lève `CacheDuPosteLuDansUnTest` en **nommant le fichier** et en disant
quoi faire.

Trois détails qui ne sont pas des détails :

- **Le test grossier sur la chaîne vient d'abord.** `resolve()` à chaque
  ouverture de fichier coûterait cher pour un cas qui ne se produit presque
  jamais ; `".cache" not in texte` élimine tout le reste avant.
- **`bytes` et descripteurs sont traités.** `open()` accepte les deux ; les
  ignorer laisserait un trou silencieux, et un trou silencieux est ce qu'on
  corrige ici.
- **Un `.cache` sous un `tmp_path` ne déclenche rien**, sinon le garde-fou
  casserait précisément les dix tests qui font ce qu'il faut.

Les six tests reçoivent ensuite l'isolation qui leur manquait — le même
`monkeypatch.chdir(tmp_path)` que leurs voisins.

## 5. `.cache` est nommé pour être refusé, jamais lu

`tests/test_ci_perimetre_sparse_checkout.py` relève les littéraux de chemin
ancrés à la racine et exige qu'ils soient dans le sparse-checkout de `tests.yml`.
Le nouveau littéral `.cache` s'y est fait prendre — et l'y ajouter serait le
contraire de ce qu'on veut : **la CI doit continuer de ne pas l'avoir**.

D'où `_NOMMES_POUR_ETRE_REFUSES`, une exemption **explicite** plutôt que la
construction du chemin autrement, qui aurait esquivé le relevé et masqué le
garde-fou. Elle est verrouillée par un test : le jour où `.cache` entrerait dans
le sparse-checkout, les tests liraient de nouveau un cache réel — celui du
runner — et le garde-fou deviendrait un mensonge.

## 6. La propriété dont tout dépend, et elle est testée

`monkeypatch.chdir(tmp_path)` n'isole que parce que les constantes sont
**relatives**. Une seule rendue absolue laisserait `chdir` sans effet, et le
garde-fou serait alors le seul filet : le test échouerait au lieu de servir sa
fixture. `test_les_constantes_de_cache_sont_toutes_relatives` le vérifie sur les
sept modules qui en portent, avec un **compteur-témoin** — si le balayage cessait
de rien trouver, le test passerait pour de bonnes raisons apparentes et de
mauvaises vraies, le trou muet de #510.

## 7. Ce que ça ne fait pas

- **Le garde-fou ne couvre que `open()`.** Un test qui se contenterait de
  `Path.is_dir()` sur le cache du poste sans jamais rien ouvrir passerait au
  travers. C'est accepté : une existence lue sans lecture ne sert pas de données
  fausses, et couvrir tout `os.stat` coûterait plus que ce que ça rapporte.
- **Il ne dit rien des écritures.** Aucun test connu n'écrit sous le `.cache` du
  dépôt, et rien ne le vérifie aujourd'hui.
- **Il ne voit pas un module importé après la fixture.** Sans objet ici : le
  garde-fou filtre `open`, pas des constantes ; c'était la limite du remède
  écarté au §3.

## 8. Vérification

`tests/test_cache_du_poste_721.py` — 11 tests, dont le garde-fou piloté **sans
faire échouer la suite** (le filtre est appelé directement, comme
`test_hook_diagnostic_sparse_checkout.py` le fait pour son propre hook) : *un
diagnostic qui cesse de parler sans le dire est pire que pas de diagnostic.*

Deux mutations vérifiées échouantes :

| Mutation | Effet |
| --- | --- |
| Le filtre neutralisé (`if False:`) | `test_ouvrir_le_cache_du_poste_leve_en_nommant_le_fichier` échoue |
| L'isolation retirée d'un des six tests | 4 tests de `test_budget_interventions` échouent, en nommant le cache |

Suite complète : **3 694 tests, 0 échec**.
