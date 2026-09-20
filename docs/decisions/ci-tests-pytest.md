<a id="ci-tests-pytest"></a>
# Un job CI exécute la suite de tests : audit préalable et arbitrages (#473) (2026-08-20)

`2026-08-20`

> **En bref** — aucun test ne lit le corpus vivant ni le réseau ; le sparse-checkout le rend structurel.

Aucun workflow n'exécutait les 1 632 tests. `grep -rln pytest .github/workflows/`
ne renvoyait que `claude.yml`, et uniquement dans `--allowed-tools` — une
autorisation donnée à l'agent de revue, pas un job. La suite n'était verte que si
quelqu'un la lançait en local. C'est la cause racine de #457 : deux tests
d'acceptation cassaient depuis une mise à jour du corpus, découverts par hasard.

Le workflow est `.github/workflows/tests.yml`. Ce qui suit consigne l'audit qui
l'a rendu défendable, puis chacun des arbitrages qu'il fallait trancher.

## L'audit d'abord : un job qui rougit au gré des données est un job qu'on apprend à ignorer

La condition nécessaire posée par #473 — aucun test ne doit dépendre du corpus
vivant ni écrire dedans — a été **mesurée, pas supposée**. Un plugin pytest
jetable a instrumenté `io.open`, `builtins.open`, `os.open`, `socket.connect`,
`socket.create_connection` et `socket.getaddrinfo` sur la totalité de la suite,
en attribuant chaque accès au test qui l'avait déclenché.

C'est cette méthode qui compte, plus que les chiffres : **un `grep` ne voit pas
ces dépendances.** Les tests fautifs ne nommaient aucun chemin ; ils appelaient
une CLI ou une fonction dont une *valeur par défaut* pointait dans le dépôt.
C'est déjà le piège qui avait fait écrire un test dans `pivot_data/`, et c'est le
même en lecture. Le relevé initial :

| | Constat |
|---|---|
| **Écritures** dans `pivot_data/` ou `raw_data/` | **0 test** — confirmé aussi par un `git status` propre après un run complet. Le piège d'écriture était déjà refermé. |
| **Lectures du corpus vivant** | **10 tests**, dont **9 invisibles au `grep`** |
| **Lectures de config déclarative** | 5 tests, délibérées, conservées (voir plus bas) |
| **Sorties réseau réelles** | **1 test**, vers un site tiers |

Les dix lectures du corpus, et leur traitement :

- **`tests/test_audit_pivot_dataset.py`, 4 tests.** Ils surchargeaient
  `--input-dir` vers les fixtures mais pas `--scrutins` ni `--amendements`, dont
  les défauts argparse valent `pivot_data/scrutins.json` et
  `pivot_data/amendements/`. Ils lisaient donc ~66 Mo du corpus vivant sans
  qu'une seule assertion n'en dépende. Corrigé par une fixture `autouse` qui
  réécrit les deux globales : le parser étant reconstruit à chaque appel de
  `main()`, la surcharge couvre aussi les tests à venir.
- **`tests/test_generate_group_profiles.py`, 5 tests.** Même piège, variante plus
  retorse : `generate_all()` reçoit ces chemins en **valeur par défaut de
  paramètre**, liée à la définition — un monkeypatch de la globale du module n'y
  peut rien. Corrigé en substituant les chargeurs, appliqués à un chemin absent :
  ils rendent alors un index vide *du bon type*, en s'appuyant sur leur contrat
  documenté (« index vide si le fichier est absent ») plutôt que sur un faux.
- **`tests/test_gouvernement_profile.py`, 1 test.**
  `test_build_profile_real_pivot_gabriel_attal` lisait
  `pivot_data/profiles/gabriel-attal.pivot.json` : exactement le défaut de #457,
  dans un fichier que #472 n'avait pas traité parce que l'échec ne s'y était pas
  manifesté. Rebranché sur la fixture figée déjà produite par #472. **Le
  diagnostic de #473 était donc incomplet sur ce point** — il annonçait le
  découplage comme acquis ; il l'était pour le fichier où le symptôme était
  apparu, pas pour le module voisin.

Restent **5 tests** qui lisent `raw_data/groupes_reels.json` et
`raw_data/gouvernements_reels.json`. **Ils sont conservés, délibérément** : ces
deux fichiers ne sont pas du corpus mais de la **config déclarative éditée à la
main**. La frontière est vérifiable, pas déclarative — le `git add` de
`generate-data.yml` liste `raw_data/profiles`, `pivot_data/profiles`,
`pivot_data/partis`, `pivot_data/groupes`, `pivot_data/gouvernements`,
`pivot_data/scrutins.json` et `pivot_data/amendements`, et **aucun des deux
fichiers de config**. Le bot ne peut pas les changer ; seule une personne le
peut, et c'est précisément à ce moment-là qu'on veut savoir si la config reste
valide. Les figer en fixtures ne testerait plus que la copie.

La sortie réseau, enfin :
`tests/test_candidate_profile.py::test_build_profile_no_syceron_for_senat`
appelait réellement `archive.nossenateurs.fr` sur deux législatures à
`TIMEOUT = 15 s`. Le test patchait tout ce qu'il croyait nécessaire, mais pas
`fetch_dossiers_for_legislatures`, la seule branche réservée à
`chambre != "deputes"` — donc la seule que ce test empruntait. Il coûtait **16 s
des 35 s** de la suite et aurait fait dépendre le job d'un site tiers.

**Résultat, mesuré après correction : 1 632 tests, 0 écriture, 0 lecture du
corpus vivant, 0 sortie réseau externe, et 35 s → 11 s.** La suite est
déterministe : elle ne peut plus rougir à cause d'une mise à jour de données.

## Arbitrage 1 — déclencheurs : `pull_request` **et** `push` sur `main`, sans `paths-ignore`

`pull_request` seul laisserait passer le cas qui nous concerne directement : deux
PR vertes séparément peuvent casser `main` une fois fusionnées l'une après
l'autre, par conflit sémantique et non textuel — que git ne voit pas. Le dépôt
vit dans ce régime, plusieurs branches ouvertes en parallèle sur le même code.
`push: [main]` est le filet, à 11 s le run.

**Pas de `paths-ignore`, ni pour les commits de données du bot, ni pour la
documentation.** Deux raisons, la seconde plus intéressante que la première :

1. **Le piège du check requis.** Un job filtré par `paths-ignore` n'est pas
   « réussi », il est *absent* — et un check requis absent laisse la PR
   indéfiniment `pending`. Une PR purement documentaire serait bloquée sans
   moyen de la débloquer autrement qu'en retirant l'exigence.
2. **Le commit de données est le canari.** Exclure les commits de
   `generate-data` reviendrait à inscrire dans le YAML l'hypothèse « les tests ne
   dépendent pas des données » — l'hypothèse même dont #473 existe parce que
   personne ne l'avait vérifiée. Tant qu'elle tient, ces runs sont verts et
   coûtent 11 s ; le jour où un test se recouple au corpus, c'est ce run-là qui
   le dit. Payer 11 s pour transformer une hypothèse en vérification continue est
   un bon prix. (Accessoirement, `generate-data.yml` est aujourd'hui en
   `workflow_dispatch` seul, son `schedule` étant commenté : ces commits sont
   rares.)

## Arbitrage 2 — matrice Python : une seule version, 3.12, et pas de matrice

Le plancher réel a été **mesuré sur le code**, pas choisi : aucune trace de
`match`, `tomllib`, `datetime.UTC`, `itertools.batched`, `except*`, `StrEnum`,
`typing.Self` ni de génériques PEP 695. Ce qu'on trouve, ce sont 53 annotations
`X | None` (PEP 604) évaluées à l'exécution — seuls 6 fichiers de `src/` ont
`from __future__ import annotations` — et `zip(..., strict=True)`. **Le plancher
est donc 3.10**, sans aucun usage de 3.11 ou 3.12.

Ce plancher est un fait mesuré, pas une promesse : rien dans le dépôt ne
s'engage sur une version (ni `pyproject.toml`, ni `setup.cfg`, ni
`python_requires` — le projet n'est pas un paquet distribué). Une matrice
3.10/3.11/3.12 multiplierait par trois le coût pour garantir un support que
personne ne réclame et qu'aucun utilisateur n'exerce.

Le job tourne donc sur **la version qui exécute la production**, en réutilisant
`./.github/actions/bootstrap-extraction` — dont `inputs.python-version` vaut
`'3.12'`. C'est le point décisif : la version n'a qu'une seule déclaration dans
tout le dépôt, et si quelqu'un l'y change, les tests le suivent sans qu'on ait à
y penser. Tester sur un interpréteur que la production n'utilise pas serait
tester autre chose. Le plancher 3.10 est consigné ici pour que l'élargissement
de la matrice, s'il devient utile, parte d'un chiffre plutôt que d'un pari.

## Arbitrage 3 — bloquant tout de suite, pas informatif

#473 penchait pour « informatif quelques semaines, le temps de vérifier la
stabilité ». Ce délai sert à se prémunir d'un job instable ; l'audit ci-dessus
montre qu'il n'y a rien à observer. Aucune écriture, aucune lecture du corpus
vivant, aucune sortie réseau, aucun `sleep` dépendant d'une horloge externe :
les seules sockets restantes sont des serveurs HTTP locaux (`127.0.0.1`) montés
par les tests eux-mêmes. Un job informatif, lui, a un coût certain — il apprend
à lire un rouge comme du bruit, et c'est exactement ce qui rendait #457
possible. Le job **échoue** donc dès maintenant si un test échoue.

**Réserve explicite, parce qu'elle n'est pas dans ce dépôt** : en faire un
*required check* qui bloque le bouton « merge » est un réglage de protection de
branche, dans les paramètres GitHub, qu'aucun fichier versionné ne porte. En
l'état, l'échec est visible et rouge sur la PR, mais n'empêche pas
mécaniquement la fusion tant que ce réglage n'est pas posé à la main.

## Arbitrage 4 — coût runner : la suite ne domine pas, le checkout le ferait

Chiffres mesurés en local (Python 3.12.3, la même version qu'en CI) :

| | Durée | Pic mémoire |
|---|---|---|
| Avant correctifs, à froid | 45,5 s | 285 Mio |
| Avant correctifs, à chaud | ~35 s | |
| **Après correctifs** | **11,2 s** | |

Et en CI, sur le premier run réel du job (`32361952284`, PR #478, commit
`efed279`, 20/08/2026 11:03 UTC) — **job complet en 24 s**, soit :

| Étape | Durée |
|---|---|
| `actions/checkout` (sparse + `blob:none`) | **2 s** |
| Garde « corpus hors du checkout » | < 1 s |
| `bootstrap-extraction` (setup-python + `pip install`) | 5 s |
| **pytest (1 639 tests)** | **12 s** |

Les 2 s de checkout sont à comparer aux **93–117 s** que #467 a mesurées pour un
checkout complet du même dépôt : la liste de chemins ci-dessous vaut un facteur
~50 sur ce poste.

La correction a supprimé les trois postes qui dominaient : 16 s d'appel réseau
réel, ~8 s de chargement d'index du corpus, et le reste en désérialisation. Ce
qui domine désormais est `tests/test_amendements_download_modes.py`, dont onze
teardowns attendent 0,5 s l'arrêt d'un serveur HTTP local — ~5,5 s, soit la
moitié de la suite. **Signalé, pas traité** : ces temporisations font partie du
scénario testé (les trois états de dégradation du téléchargement par Range), et
les raccourcir demande de retoucher le module, pas le test. À reprendre dans une
issue dédiée si le job devient un jour un point de contention.

Le vrai poste de coût est ailleurs : l'arbre de travail pèse **1,8 Gio**, dont
1,5 Gio de `raw_data/profiles/` et 240 Mio de `pivot_data/`. Un `checkout` complet
coûterait plusieurs fois la durée des tests — #467 vient de le mesurer sur ce
même dépôt : **93 à 117 s par shard** sur le run 32288588518, soit ~55 % du temps
d'un shard d'extraction (voir `#budget-execution-pleine-echelle-467`). Le job
fait donc un
**sparse-checkout** (`sparse-checkout-cone-mode: false`) doublé de
`filter: blob:none` — sans le filtre, git téléchargerait les blobs de tout
l'arbre avant de n'en matérialiser qu'une fraction.

La liste des chemins n'est pas une devinette : l'instrumentation a relevé
l'ensemble **exhaustif** des fichiers du dépôt que la suite touche hors `src/` et
`tests/` — trois fichiers sous `.github/`, les deux JSON de config, et cinq
fichiers sous `web/` lus par les tests `test_web_v3_*`.

Et ce n'est pas qu'une économie. **Ne pas poser le corpus sur le disque rend le
critère « aucun test ne lit `pivot_data/` » structurel au lieu d'audité une
fois.** Un test qui s'y recouplerait échoue sur un `FileNotFoundError` nommant
le chemin fautif, au lieu de passer en silence jusqu'à la prochaine mise à jour
du corpus — le scénario #457, précisément. Un step de garde vérifie d'ailleurs
que `pivot_data/` et `raw_data/profiles/` sont bien absents du checkout : si le
périmètre est élargi un jour, ce sera une décision, pas un effet de bord.

Le revers assumé : le checkout de CI diffère de celui d'un poste de
développement, et un test qui lirait un chemin non listé passerait en local et
échouerait en CI. C'est le sens de l'échange — cette divergence *est* le
garde-fou, et le message d'erreur nomme le chemin manquant.

## Arbitrage 5 — dépendances : `requirements-dev.txt`, pas un `pip install pytest` en dur

Le dépôt n'avait ni `requirements-dev.txt`, ni `pyproject.toml`, ni `setup.cfg` :
`requirements.txt` ne porte que les dépendances d'exécution, et la suite a besoin
de pytest en plus. Écrire `pip install -r requirements.txt pytest` dans le YAML
aurait mis une version de pytest hors de toute déclaration, libre de diverger de
celle des postes de développement sans que rien ne le signale.

D'où `requirements-dev.txt`, qui fait `-r requirements.txt` (une seule
déclaration des dépendances d'exécution) puis épingle `pytest==9.1.1` — la
version réellement installée dans `.venv/` et celle avec laquelle les durées
ci-dessus ont été mesurées, au `==` comme l'exige AGENTS.md §8. Le job le passe à
`bootstrap-extraction` via son `inputs.requirements`, sans dupliquer l'étape
`setup-python` + `pip install`.

---

