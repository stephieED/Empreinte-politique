<a id="cloisonnement-branche-roster-524"></a>
<a id="roster-suspension-totale-code-2"></a>
# Cloisonnement de la branche roster, et le code 2 « suspension totale » (#524) (2026-08-26)

`2026-08-26`

> **En bref** — une panne de source coûte la branche roster, jamais le commit.

**Ce lot ne répare pas la source. Il répare les trois amplificateurs qui
transformaient une panne de source en run entièrement perdu.**

## 1. Ce qui s'est passé

Run [`32876863499`](https://github.com/stephieED/Empreinte-politique-src/actions/runs/32876863499) :
3 jobs rouges (`prepare-roster-matrix`, `extract-roster-groupes (shard 0)`,
`merge-and-pivot`), la même annotation dans les trois :

> `ROSTER — récupération du roster (deputes, législature=16) en échec : la
> composition de ses groupes est INCONNUE, pas vide.`

Ce n'est pas #518 qui rejoue : les trois steps échouent en **8 s** — 3 tentatives
plus 2 s et 4 s de backoff, sur des réponses reçues en **0,4 s**. Pas un
timeout : un **500 immédiat et déterministe** de
`www.nosdeputes.fr/deputes/json`. Diagnostic complet : #522.

Et surtout : `merge-and-pivot` avait **terminé** l'étape 12 (fusion des bruts)
et l'étape 13 (`Normalisation pivot + enrichissement ParlTrack`, **165 s,
verte**) avant de mourir au step 15, `Repli — construction de la liste
roster-driven`. Tout ce travail a été jeté.

## 2. A — l'exception voyage jusqu'à l'annotation

`fetch_rosters_bruts` affichait l'exception sur `stderr` puis **la jetait**
(`rosters_bruts[key] = None`), et `anomalies_roster` reconstruisait son message
à partir de la **seule clé**. L'annotation `::error::` ajoutée par #518 — dont
c'était pourtant tout l'objet — disait donc « en échec » : jamais `HTTP 500`,
jamais `SSLError`, jamais `Read timed out`. Il a fallu sonder l'endpoint à la
main pour retrouver ce que le run savait déjà.

`fetch_rosters_bruts` rend désormais `(rosters_bruts, echecs)`, et l'anomalie
nomme sa cause :

> `… en échec (HTTPError: 500 Server Error: … for url: …) : la composition de
> ses groupes est INCONNUE, pas vide.`

Le message est aplati sur une ligne et borné à 200 caractères
(`resume_exception`) : la destination est une annotation, lue dans une liste.
Une clé sans exception connue garde le message d'origine — on n'invente pas une
cause (AGENTS.md §2 règle 5). Non-régression sur les trois familles réellement
observées : `HTTPError` 500, `SSLError`, `Timeout`
(`tests/test_roster_cause_echec.py`).

## 3. B — la branche roster ne coûte plus le commit des candidats déclarés

C'est **exactement** l'arbitrage que #518 avait écrit 70 lignes plus bas pour
`generate_group_profiles.py` — « refuser qu'une donnée NON écrite annule la
publication d'une donnée écrite » — et jamais appliqué au repli roster juste
au-dessus. Le step de repli de `merge-and-pivot` tolère désormais, **dans le
shell et sur le code** :

| Code | Sens | Écrit quelque chose ? |
| --- | --- | --- |
| `1` | roster INCOMPLET (fetch tombé, groupe à 0 membre, roster vide) — #511 | non |
| `2` | extraction de **tous** les groupes suspendue — #516/#524 | non |
| autre (127, 137/OOM…) | ce n'est pas un code documenté | repropagé, step rouge |

Puis `Normalisation pivot roster-driven` est conditionné à
`hashFiles('raw_data/roster_candidats.json') != ''` — sur **l'existence du
fichier**, pas sur le succès d'un step : le roster peut manquer par plusieurs
routes (artifact absent, repli sauté, `prepare-roster-matrix` skippé), et il
n'est pas committé, donc sans lui la passe échouerait de toute façon, sur un
message parlant de fichier introuvable plutôt que de branche roster fermée.

**Pas de `continue-on-error: true`**, pour la raison déjà écrite au step
groupes : il avalerait aussi ce qui n'est pas un code de sortie documenté, et
un job mort pour une autre cause passerait pour une source indisponible.

Le saut est **sûr et déjà surveillé**, pas décrété : si le fetch roster échoue,
les shards n'ont rien collecté non plus (ils meurent au même endroit), donc il
n'existe aucun profil « collecté mais non publié » à produire. Et si cette
hypothèse devenait fausse un jour, `audit_collecte_non_publiee.py` (#511/#518)
reste armé au step 26 et bloquerait le commit en nommant les slugs. **Le
garde-fou de #511 n'est pas contourné — il est ce qui rend le saut légitime.**

## 4. C — « tous les groupes suspendus » est une décision, pas une anomalie

`generate_roster_candidats.main()` sortait en **1** quand toutes les entrées de
`groupes_reels.json` portaient `extraction_suspendue`. Or suspendre les 5
entrées AN — comme les 2 entrées Sénat le sont depuis #516 — suspendrait **les
7** : le remède documenté d'une source en panne **reproduisait donc l'échec
qu'il était censé éteindre**. Et `--autoriser-roster-incomplet` n'est câblé sur
aucun input, délibérément (#511). Conséquence : il n'existait **aucun** moyen
d'obtenir un run vert pendant que NosDéputés répondait 500.

Ce cas rend désormais `EXIT_ROSTER_INDISPONIBLE = 2` — même valeur et même
sémantique que `generate_group_profiles.EXIT_ROSTER_INDISPONIBLE` et
`generate_gouvernement_profiles.EXIT_COLLECTE_INCOMPLETE` (#427) —, toléré par
les **trois** appelants du workflow, qui sautent alors la branche roster.
L'annonce est une annotation `warning` et non `error` : un run qui saute une
branche délibérément suspendue n'a pas de défaut à signaler, mais l'onglet de
résumé doit dire *pourquoi* il ne publie aucun profil de roster, sans quoi la
suspension devient invisible au bout de deux runs.

**Ce que le code 2 ne dit jamais : « écris un roster vide ».** Ce chemin
n'écrit rien du tout, ce qui reste exactement l'interdit de #511. Une config
illisible ou sans groupes garde le code 1 : sans cette séparation, le `if:` des
appelants sauterait la branche roster sur une erreur de dépôt.

Côté producteur, l'artifact `roster-candidats` est publié **sous condition**
(`steps.roster.outputs.ecrit == 'true'`) et garde `if-no-files-found: error`.
Les deux vont ensemble : sans le `if:`, il faudrait relâcher `error` en
`ignore`, et les consommateurs téléchargeraient alors un artifact **vide** avec
succès — « roster absent » deviendrait « roster de 0 candidat », c'est-à-dire
l'incident de #511. Un artifact **absent**, lui, les fait tomber sur leur repli.

## 5. E — un 500 de nosdeputes.fr n'est pas un aléa

`group_roster._erreur_retentable` classait tout 5xx comme transitoire. Or
l'en-tête du module documente depuis toujours que `/groupe/<SIGLE>/json`
« renvoie **systématiquement** une erreur HTTP 500 » : sur cette plateforme, un
500 est une **signature de panne applicative**, pas un hoquet. Les 3 tentatives
ne changeaient pas le verdict, elles ne faisaient que retarder le message qui le
nomme — même raisonnement que la ligne `SSLError` de #518, dont la suspension
d'extraction de #516 dépend.

`_STATUTS_5XX_RETENTABLES = {502, 503, 504}` : ceux-là viennent d'un frontal ou
d'un backend momentanément indisponible, et un second essai y change quelque
chose. Impact faible en temps (6 s), mais la ligne devait être requalifiée en
même temps que A — c'est elle qui décide si l'on relance ou si l'on suspend.

## 6. Condition de retrait

Ce cloisonnement n'est **pas** transitoire et n'a pas à être retiré : « une
donnée non écrite n'annule pas la publication d'une donnée écrite » est la même
règle qu'aux steps groupes (#518) et gouvernement (#427). Ce qui est
transitoire, c'est ce qui l'a rendu urgent.

Deux choses, distinctes, à rouvrir :

- la **suspension** des entrées AN de `groupes_reels.json` (hors périmètre de
  #524 : c'est la suite de C, pas C). À poser seulement si la panne dure, avec
  `depuis`/`motif`/`references`/`condition_reprise` que la gate de #516 exige en
  dur, `condition_reprise` étant un `GET https://www.nosdeputes.fr/deputes/json`
  en **200**. À lever dès que cette condition est remplie ;
- la **requalification du 500** (§5) : à revoir si `nosdeputes.fr` se met un jour
  à servir des 500 réellement transitoires. Le signal serait un run où une
  seconde tentative aboutit — aucun n'a été observé.

Le cloisonnement, lui, reste : il ne masque rien qu'un audit ne mesure, et il
mesure ce qu'il saute.

Guarded by `tests/test_roster_cause_echec.py`,
`tests/test_ci_cloisonnement_branche_roster.py`,
`tests/test_roster_reprise_reseau.py`, `tests/test_groupes_suspendus.py`.

