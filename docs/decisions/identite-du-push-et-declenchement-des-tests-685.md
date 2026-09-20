<a id="identite-du-push-et-declenchement-des-tests-685"></a>
# L'identité du push décide si un workflow voit le commit de données — et depuis quinze commits, aucun ne le voit (#685) (2026-09-01)

`2026-09-01`

> **En bref** — `AGENTS.md` §3b promettait, au titre de #508, qu'« a deploy-key push emits a `push` event, so `tests.yml` really runs on data commits » : mesuré au 01/09/2026, **0 des 15** commits de données arrivés sur `main` depuis le premier run de `tests.yml` (20/08) ne porte de run de la suite, **11** d'entre eux postérieurs à #508, alors que le workflow a bien tourné en `push` sur tous les autres commits de `main` (124 runs) — ce n'est donc pas un incident mais l'état permanent ; la cause est prouvée par quatre mesures convergentes et par le journal du job `99566091830`, où `actions/checkout` pose `git remote add origin https://github.com/…` puis un `AUTHORIZATION: basic ***` au lieu du `git@github.com:` qu'il poserait si `ssh-key` était renseignée — le dépôt n'a **aucune** clé de déploiement (`GET /repos/{o}/{r}/keys` rend `[]`), le secret `DATA_PUSH_SSH_KEY` ne figure pas parmi ses 4 secrets, et le ruleset n'a ni `required_status_checks` ni acteur `DeployKey` : les **trois gestes manuels** de #508 §7 n'ont jamais été posés, la décision s'étant pourtant réservée (« tant qu'il n'a pas poussé, cette entrée décrit une intention ») avant que `AGENTS.md` ne promeuve l'intention en fait ; ce qui a rendu quinze commits invisibles n'est pas le repli vers le `GITHUB_TOKEN` — documenté et voulu — mais qu'il soit **muet**, le « rejet bruyant » de #508 ne parlant que sur un `GH013`, lequel suppose le check requis jamais rétabli, si bien que **chaque omission rend l'autre invisible** ; `merge-and-pivot` gagne donc un step qui **mesure** `git remote get-url origin` après un push abouti — le fait, là où `secrets.DATA_PUSH_SSH_KEY != ''` ne dirait que l'intention — et nomme la **conséquence** (« `tests.yml` ne tournera pas sur ce commit ») sur les deux canaux qui se relisent, annotation `::warning::` et résumé du job, **sans bloquer** puisque les trois gestes vivent hors du dépôt et qu'échouer priverait le site de ses données fraîches ; `tests/test_ci_signal_identite_push_685.py` **exécute** le fragment de shell extrait du workflow dans un dépôt local sous `tmp_path`, une fois en `https://` et une fois en `git@` (un signal qui crie ou se tait dans les deux cas n'apprend rien), garde un cas échouant si quelqu'un rendait le signal bloquant en passant, et un autre si `tests.yml` gagnait un `paths:` qui donnerait au commit de données une seconde raison de n'être pas couvert ; §3b cesse d'affirmer la garantie et dit qu'elle ne revient qu'avec #508 §7, **jamais en réécrivant la ligne** ; non établi et nommé : ce que les quinze commits non testés auraient révélé, et le comportement sous clé de déploiement, jamais observé dans ce dépôt.

## 1. Le constat, et ce qu'il n'est pas

Le commit de données `245511b4` (31/08/2026) ne porte aucun run de `tests.yml`.
Le dépôt le savait possible et affirmait le contraire : `AGENTS.md` §3b, au titre
de [[push-donnees-cle-de-deploiement-508]], écrivait

> **A deploy-key push emits a `push` event, so `tests.yml` really runs on data commits.**

Ce n'est pas un incident. Sur les **15** commits de données arrivés sur `main`
depuis que `tests.yml` existe — son premier run est du 20/08/2026 —, **aucun**
ne porte de run de la suite, quel que soit l'événement :

| Période | Commits de données sur `main` | Portant un run de `tests.yml` |
|---|---|---|
| 20/08 → 26/08 (avant #508) | 4 | 0 |
| 27/08 → 31/08 (après #508, commit `6c8454c0`) | 11 | 0 |
| **Total** | **15** | **0** |

Mesure : les 288 SHA distincts couverts par les runs de `tests.yml` (workflow
`338539771`, toutes pages, tous événements) croisés avec
`git log --grep='mise à jour automatique des données'`. Aucun des 15 n'y figure.
`tests.yml` a bien tourné en `push` sur tous les autres commits de `main` — 124
runs `push` au 01/09 —, donc le workflow n'est ni cassé ni suspendu : il ne voit
tout simplement jamais passer les commits du bot.

## 2. La cause, prouvée

Elle n'est pas déduite d'une chronologie ; quatre mesures indépendantes la
donnent, et le journal d'un run la montre à l'exécution.

| Ce qui est vérifié | Appel | Résultat |
|---|---|---|
| Clés de déploiement du dépôt | `GET /repos/{o}/{r}/keys` | `[]` — **aucune** |
| Secrets Actions du dépôt | `GET /repos/{o}/{r}/actions/secrets` | 4 secrets : `ACTIONS_RUNNER_DEBUG`, `ACTIONS_STEP_DEBUG`, `CLAUDE_CODE_OAUTH_TOKEN`, `WORKFLOW_PAT` — **pas** `DATA_PUSH_SSH_KEY` |
| Règles du ruleset `20260729_ruleset` | `GET /repos/{o}/{r}/rulesets/19959954` | `deletion`, `non_fast_forward`. **Pas** de `required_status_checks` ; `bypass_actors` = `RepositoryRole/5` seul, **aucun** `DeployKey` |
| Identité réellement employée par le push | journal du job `99566091830` (run `33414042623`, qui a poussé `3fafa99e`) | `git remote add origin https://github.com/stephieED/Empreinte-politique-src` puis `git config --local http.https://github.com/.extraheader AUTHORIZATION: basic ***` |

La dernière ligne est la preuve, et pas un indice : `actions/checkout` pose
`git@github.com:` **si et seulement si** `ssh-key` est renseignée. Elle a posé
`https://` et un en-tête d'autorisation, donc `ssh-key` valait la chaîne vide,
donc le push est parti sous le `GITHUB_TOKEN`. Un push sous le `GITHUB_TOKEN`
n'émet **aucun** événement (protection anti-boucle des workflows) : pas
d'événement `push`, pas de run de `tests.yml`.

Autrement dit, les trois gestes manuels que
[[push-donnees-cle-de-deploiement-508]] §7 énumérait — poser la clé, renseigner
le secret, rétablir le check requis — **n'ont jamais été faits**. La décision
s'était pourtant réservée : « tant qu'il n'a pas poussé, cette entrée décrit une
intention ». C'est `AGENTS.md` §3b qui a promu l'intention en fait.

Correction mineure à l'issue, consignée parce que c'est le genre d'écart qui fait
rouvrir un dossier : le run `33414042623` a poussé `cf2d548..3fafa99`, donc
`3fafa99e` et non `245511b4`. Les deux commits sont dans les 15, la mesure ne
bouge pas.

## 3. Pourquoi personne ne l'a vu : les deux omissions se couvrent l'une l'autre

Le repli vers le `GITHUB_TOKEN` est **documenté et voulu** — un fork ou une
branche sans le secret doit continuer à fonctionner. Ce n'est donc pas le repli
le défaut ; c'est qu'il est **muet**.

#508 promettait un rejet bruyant sur secret absent. Ce rejet existe bien, mais il
ne se déclenche que sur un `GH013`, c'est-à-dire sur un **rejet par une règle du
dépôt** — lequel suppose le check requis `Suite complète`, qui est précisément le
troisième geste jamais posé. Résultat :

- pas de clé ⇒ push sous le token ⇒ pas d'événement ⇒ pas de suite de tests ;
- pas de check requis ⇒ le push **réussit** ⇒ le garde-fou ne parle pas.

Chaque omission rend l'autre invisible. Un dispositif qui n'aurait été qu'à
moitié posé aurait crié dès le premier run ; posé à zéro, il se tait.

## 4. La décision

**Trois choses, dont une seule est réparable depuis le dépôt.**

**a. Le signal.** `merge-and-pivot` gagne un step qui, après un push abouti,
**mesure** `git remote get-url origin` et dit ce que ça implique — annotation
`::warning::` sur le run **et** ligne dans le résumé du job, le seul des deux
canaux qui se relise après coup. Il **mesure ce qui s'est passé** plutôt que de
tester `secrets.DATA_PUSH_SSH_KEY != ''`, qui ne dirait que l'intention : un
secret renseigné mais refusé par le checkout passerait le test et échouerait
quand même à émettre l'événement.

Le message nomme la **conséquence** (« `tests.yml` ne tournera pas sur ce
commit ») et pas seulement le fait (« pas de clé de déploiement »). C'est
exactement la reconstruction qui n'a été faite par personne pendant quinze
commits.

**b. `AGENTS.md` §3b dit ce qui est vrai.** La ligne n'affirme plus une garantie ;
elle donne la mesure, nomme les trois gestes qui la rétabliraient, et précise que
la garantie revient avec eux et **jamais en réécrivant la ligne**. Laisser une
garantie fausse en place est le plus coûteux des trois états possibles : on s'y
fie, et un dépôt public dont le site est en ligne s'y fie pour de bon.

**c. Ce qui n'est pas dans ce dépôt, encore une fois.** Poser la clé, le secret
et le check requis reste hors de portée d'un run. Ce lot ne les pose pas ; il
fait en sorte que leur absence se voie à chaque run de données.

## 5. Pourquoi le signal ne bloque pas

Faire échouer `merge-and-pivot` sur un push non émetteur d'événement priverait le
site de ses données fraîches pour une configuration que seule la propriétaire du
dépôt peut poser — et le commit de données, lui, est légitime : il a passé la
quality gate et les quatre gardes-fous de pré-commit. Le rendre bloquant est un
**arbitrage** et non une correction ; `tests/test_ci_signal_identite_push_685.py`
comporte un cas qui échoue si quelqu'un le prend en passant, pour que la bascule
soit décidée et non subie.

## 6. Le verrou

`tests/test_ci_signal_identite_push_685.py` **exécute** le fragment de shell
extrait du workflow, dans un dépôt git local créé sous `tmp_path` (aucun accès
réseau, aucune lecture de `pivot_data/` ni `raw_data/profiles/` — `AGENTS.md`
§3b), une fois avec un `origin` en `https://` et une fois en `git@`. Les deux
moitiés comptent : un signal qui crie dans les deux cas n'apprend rien, un signal
muet dans les deux cas non plus.

C'est délibérément plus qu'un test de motif. Un garde-fou qui devient muet sans
le dire est pire que pas de garde-fou (`AGENTS.md` §3b, à propos du hook de
diagnostic) — et un test qui reconnaît un motif reste vert le jour où le motif
est là mais ne s'imprime plus. Le cas sur `tests.yml` complète le dispositif :
il échoue si le workflow gagnait un `paths:`/`paths-ignore:`, qui donnerait au
commit de données une **seconde** raison de ne pas être couvert et rendrait
l'annotation faussement affirmative.

## 7. Alternatives écartées

| Option | Verdict |
|---|---|
| **Vérifier après coup, par l'API, qu'un run de `tests.yml` existe pour le SHA poussé** | Écartée. Il faudrait attendre puis sonder — un run qui se met en file, un délai d'indexation, et le job devient long et intermittent. La mesure du distant est immédiate et déterministe. |
| **Tester `secrets.DATA_PUSH_SSH_KEY != ''`** | Écartée. Dit l'intention, pas l'exécution : une clé refusée par le checkout donnerait un signal vert sur un push muet. |
| **Rendre le signal bloquant** | Écartée pour l'instant, §5 — arbitrage de la propriétaire, pas correction d'agent. |
| **Retirer la phrase de `AGENTS.md` sans rien mesurer** | Écartée. Le dépôt aurait perdu la garantie *et* la trace de pourquoi elle ne tenait pas ; la prochaine session aurait réécrit la même phrase. |
| **Réparer le mécanisme depuis le dépôt** | Impossible : clé de déploiement, secret et ruleset sont trois objets GitHub, aucun versionné. C'est la réserve déjà posée par [[push-donnees-cle-de-deploiement-508]] §7 et [[ci-tests-pytest]]. |

## 8. Ce que ce lot n'établit pas

- **Ce que les quinze commits non testés auraient révélé.** La suite ne lit pas
  le corpus (#473) ; elle verrouille des invariants de structure, le périmètre du
  sparse-checkout, la cohérence des workflows et l'index des décisions. Rien ne
  dit qu'elle aurait rougi sur l'un d'eux — seulement que personne ne le sait.
- **Le comportement sous clé de déploiement**, jamais observé dans ce dépôt : la
  bascule `git@` du step est vérifiée par rejeu local, pas par un run réel. Le
  critère d'acceptation de #508 — « vérifié par un run réel » — reste ouvert, et
  ce lot le rend enfin visible plutôt que de le supposer tenu.
