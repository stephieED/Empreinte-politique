<a id="push-donnees-cle-de-deploiement-508"></a>
# Rétablir le check requis sans bloquer le bot : le push de données passe par une clé de déploiement (#508) (2026-08-27)

`2026-08-27`

> **En bref** — le push de données passe par une clé de déploiement, seul moyen de rétablir un check requis sans bloquer le bot.

Le check requis `Suite complète` a été ajouté au ruleset `20260729_ruleset` le
20/08/2026, puis **retiré le soir même** parce qu'il avait fait rejeter le push
du bot de génération. Depuis, le dépôt tourne **sans aucun check bloquant** : le
job `tests.yml` rougit sur les PR, mais rien n'empêche de fusionner par-dessus.
Cette entrée consigne pourquoi la solution évidente est fermée sur un dépôt
personnel, ce qui a été retenu à la place, et ce que ce choix coûte.

## 1. Le diagnostic n'a plus à être « établi par élimination » : le serveur l'avait nommé

#508 présentait sa cause comme déduite d'une chronologie. Elle est en réalité
**écrite en toutes lettres dans le log du run 32398799010**, trois lignes
au-dessus de la conclusion que le workflow en tirait :

```
remote: error: GH013: Repository rule violations found for refs/heads/main.
remote: - Required status check "Suite complète" is expected.
 ! [remote rejected] main -> main (push declined due to repository rule violations)
```

L'API confirme le reste sans laisser de place au doute — l'historique du
ruleset (`GET /repos/{o}/{r}/rulesets/{id}/history/{version_id}`) donne l'état
exact à chaque version :

| Version | Horodatage | `rules` |
|---|---|---|
| 44755531 | 29/07 11:06 | `deletion`, `non_fast_forward` |
| 47092235 | **20/08 16:30** | + `required_status_checks` (« Suite complète », `integration_id` 15368) |
| 47092515 | 20/08 16:32 | + `pull_request`, `strict_required_status_checks_policy: true` |
| 47092963 | 20/08 16:37 | − `pull_request`, `strict` repassé à `false` |
| 47118877 | **20/08 20:46** | − `required_status_checks` (état actuel) |

Deux corrections à la chronologie de l'issue, mineures mais consignées parce que
c'est le genre d'écart qui fait rouvrir un dossier : le check a été ajouté à
**16:30**, pas à 16:37 (16:37 est le retrait de la règle `pull_request` ajoutée
cinq minutes plus tôt), et le retrait final est horodaté **20:46 heure locale**.

**Le mécanisme, lui, tient exactement comme décrit** : un ruleset applique ses
`required_status_checks` aux **pushs directs**, pas seulement aux PR. Ce job
pousse sur `main` sans PR — aucun check n'est attaché au commit qu'il fabrique,
donc aucun check ne *peut* passer avant le push. La règle n'est pas dure à
satisfaire pour lui, elle est **insatisfiable**. Reboucler ne sert à rien, et
c'est bien ce qu'on a observé : trois tentatives, trois fois la même erreur.

## 2. Pourquoi l'app GitHub Actions ne peut pas être l'acteur de contournement (la question à ne pas rouvrir)

L'entrée de `bypass_actors` qu'on voudrait écrire est refusée par l'API :

```
Actor GitHub Actions integration must be part of the ruleset source or owner organization
```

C'est **structurel, pas un bug de l'API**. Un acteur de type `Integration` doit
appartenir à la source du ruleset ou à l'**organisation** propriétaire. Ce dépôt
est possédé par un compte **utilisateur** (`owner.type == "User"`, vérifié) : il
n'y a pas d'organisation propriétaire, donc pas d'app éligible. C'est aussi
pourquoi l'entrée n'apparaît pas dans *Add bypass* côté interface — l'interface
ne cache pas une option disponible, elle reflète une contrainte réelle.

**Condition de réouverture, et une seule** : si le dépôt migre un jour vers une
organisation, l'app GitHub Actions (id 15368) devient un acteur de contournement
légitime, et tout ce qui suit — clé de déploiement, secret, push SSH — peut être
retiré. Tant que le dépôt est personnel, il n'y a rien à réessayer ici.

## 3. Les options, et pourquoi la clé de déploiement

| Option | Verdict |
|---|---|
| **App GitHub Actions en `bypass_actors`** | **Impossible** sur dépôt personnel (§2). |
| **Clé de déploiement en `bypass_actors`** | **Retenue.** `DeployKey` est un `actor_type` accepté, `actor_id: null`. Portée limitée à ce seul dépôt, pas d'expiration, pas de credential personnel. |
| **PAT à portée restreinte de l'administratrice** | Écartée. Fonctionne — `RepositoryRole/5` contourne déjà, aucune modification de `bypass_actors` ne serait même nécessaire — mais **expire** (une panne différée, silencieuse, qui reviendra), est adossée à une personne, et surtout **efface la traçabilité** : le push du bot apparaîtrait comme un push de `stephieED` dans les rule suites et le journal d'audit. La clé de déploiement laisse une identité distincte. |
| **App GitHub propriété de l'utilisatrice** | Écartée. Contournement plus étroit *en théorie* (un acteur nommé au lieu de « les clés de déploiement »), mais l'acceptation de l'API n'est pas établie — le message d'erreur de §2 parle d'organisation, pas d'app première partie — et le coût est réel : une app à créer et maintenir, deux secrets (app id + clé privée), un step de frappe de jeton. Beaucoup de pièces mobiles pour un gain marginal sur un dépôt qui compte **zéro clé de déploiement** aujourd'hui. |
| **Le bot ouvre une PR et l'auto-merge** | Écartée, et c'est un cul-de-sac, pas un arbitrage de goût : une PR créée avec le `GITHUB_TOKEN` **ne déclenche aucun workflow**. `tests.yml` ne tournerait jamais dessus, le check requis resterait `pending` pour toujours, et la PR ne pourrait pas fusionner. C'est le piège déjà consigné en [[ci-tests-pytest]] (arbitrage 1). Sortir de ce cul-de-sac demanderait… une autre identité de push. On revient au même point, en ayant ajouté une PR par run. |
| **Renoncer au check bloquant** | C'est l'état actuel, et c'est ce que #508 existe pour corriger. |

## 4. Le périmètre du contournement, dit honnêtement

`DeployKey` en `bypass_actors` **ne se resserre pas** :

- le `bypass_mode` ne peut valoir que `always` — la documentation REST précise
  que `pull_request` n'est **pas compatible** avec `DeployKey` (et `exempt`
  serait pire : il n'écrit même pas d'entrée d'audit) ;
- l'entrée vaut pour **toutes** les clés de déploiement du dépôt (`actor_id`
  est `null`), pas pour une clé nommée ;
- un contournement `always` contourne **toutes** les règles du ruleset, donc
  aussi `deletion` et `non_fast_forward`.

Ce qui rend ce périmètre acceptable ici, et qui doit rester vrai :

1. le dépôt a **zéro clé de déploiement** aujourd'hui (`GET /repos/{o}/{r}/keys`
   renvoie `[]`) ; celle qu'on ajoute est donc la seule, et « toutes les clés »
   veut dire « celle-ci » ;
2. sa clé privée ne vit que dans le secret Actions `DATA_PUSH_SSH_KEY`, lisible
   par les seuls workflows du dépôt ;
3. le seul job qui la reçoit est `merge-and-pivot`, et il ne fait qu'un
   `git push` en avance rapide — jamais de `--force`, jamais de suppression ;
4. **c'est un invariant à surveiller, pas un fait acquis** : ajouter une
   deuxième clé de déploiement au dépôt lui donne mécaniquement le droit de
   forcer et de supprimer `main`. Il n'existe pas de réglage GitHub qui
   l'empêche — seulement cette phrase.

À comparer avec l'existant plutôt qu'avec un idéal : `RepositoryRole/5`
(administrateur) figure **déjà** dans les `bypass_actors` avec `always`, et
contourne donc déjà tout. La clé de déploiement n'ouvre pas une brèche d'une
nature nouvelle ; elle ajoute un second porteur, sans expiration, dont les
pushs restent distinguables de ceux de l'administratrice.

## 5. Ce que change l'identité du push — mesuré, pas supposé

#508 demandait explicitement de vérifier ce point « dans un sens **ou dans
l'autre** ». Le sens est : **un push sous clé de déploiement émet un événement
`push`**, là où le `GITHUB_TOKEN` n'en émet aucun. Deux conséquences.

**`deploy-pages.yml` se déclenchera deux fois par commit de données** — une fois
par ses `paths:` (`pivot_data/**`), une fois par le `gh workflow run` explicite
de #416. Les deux runs sont sérialisés par la concurrence `pages`
(`cancel-in-progress: false`) : le second republie un contenu identique, ou est
annulé comme run en attente supplanté. **Le déclenchement explicite est
conservé**, et ce n'est pas de la prudence gratuite : il est le seul des deux
qui ne dépende pas de l'identité qui pousse. Le supprimer inscrirait dans le
workflow l'hypothèse « le push émettra toujours un événement » — le jour où le
secret manque ou est révoqué, `actions/checkout` retombe sur le `GITHUB_TOKEN`,
et le site cesserait **silencieusement** de se mettre à jour. C'est très
exactement la panne que #416 a corrigée. Un run de publication en trop coûte une
minute ; une donnée fraîche jamais publiée ne se voit pas.

**`tests.yml` tournera enfin sur les commits de données.** Et c'est ici que la
mesure a rapporté quelque chose d'inattendu : [[ci-tests-pytest]] justifie
l'absence de `paths-ignore` par « le commit de données est le canari » — or ce
canari **ne chantait pas**. Le commit `74c77c2` (27/08, run 33100214165) ne
porte aucun run de `tests.yml`, et le dernier run `push` sur `main` remonte au
merge `94e2716`. La raison est la même protection anti-boucle : pas d'événement
`push`, donc pas de run. L'argument était juste, le dispositif était inerte
depuis le premier jour. AGENTS.md affirmait de son côté que la suite tourne
« sur chaque push vers `main` » ; cette phrase devient vraie avec ce lot. Coût :
24 s de runner par run de données.

## 6. Le workflow ne se trompe plus de cause

Le 20/08, ce step a imprimé :

```
##[error]Push toujours rejeté après 3 tentatives, rebases réussis — concurrence soutenue sur main.
```

trois lignes sous un `remote:` qui nommait la règle. Le diagnostic publié
contredisait la donnée affichée juste au-dessus — et c'est ce diagnostic-là qui
a été lu en premier. La boucle de push distingue donc désormais **trois** issues
au lieu de deux : conflit de rebase, concurrence soutenue, et **rejet par une
règle de dépôt**. Ce troisième cas sort de la boucle immédiatement (un ruleset
ne cède pas au rebase ; reboucler ne fait que répéter l'erreur) et son message
nomme la piste utile — secret absent, ou clé non inscrite dans les
`bypass_actors`.

Détail d'implémentation qui vaut d'être écrit, parce qu'il est le piège
classique : la sortie du push est redirigée vers un fichier puis relue, et le
code de retour est testé sur `$?`. Un `if git push | tee log` testerait le
statut de `tee`, toujours nul — le rejet passerait pour un succès.

## 7. Ce qui n'est pas dans ce dépôt

Comme la réserve déjà posée en [[ci-tests-pytest]] (arbitrage 3) : **aucun
fichier versionné ne porte le ruleset ni les secrets.** Ce lot rend le push du
bot compatible avec un check requis ; il ne pose pas le check. Trois gestes
manuels restent nécessaires, dans cet ordre — la clé d'abord, la règle en
dernier, faute de quoi on reproduit le 20/08 :

1. générer une paire de clés, poser la publique en **Settings → Deploy keys**
   avec *Allow write access*, et la privée dans le secret Actions
   `DATA_PUSH_SSH_KEY` ;
2. ajouter `{"actor_type": "DeployKey", "actor_id": null, "bypass_mode": "always"}`
   aux `bypass_actors` du ruleset ;
3. **puis seulement** rétablir la règle `required_status_checks` sur
   « Suite complète ».

Le critère d'acceptation de #508 — « vérifié par un run réel, pas par la lecture
de la configuration » — porte sur le premier run de `generate-data.yml` qui
suivra ces trois gestes. Tant qu'il n'a pas poussé, cette entrée décrit une
intention.

