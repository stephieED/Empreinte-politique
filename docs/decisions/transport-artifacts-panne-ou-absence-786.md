# Une panne de transport n'est pas une source absente (#786)

`2026-09-08`

> **En bref** — le run `34241352524` est **vert et n'a collecté personne** : ses quatre téléchargements d'artifacts sont partis dans la même seconde et ont tous reçu un **403 « secondary rate limit »** sur `ListArtifacts`, que `download-artifact` déclare *non-retryable* ; `continue-on-error: true` a fait le reste et la fusion a écrit **0 profil** là où le run d'avant, même code, en écrivait **636** — les **40** artifacts AN et **8** artifacts roster étaient pourtant publiés et non expirés, dont les cinq candidats qu'attendait #775 ; **aucun garde-fou ne pouvait le voir**, ils mesurent tous la collecte APRÈS la fusion et sans profil brut il n'y a ni perte à constater (#460) ni collecté-non-publié à signaler (#511) — un vert **par absence**, le motif que #484 nomme déjà : *une panne rend le même vide qu'une absence* ; un step de contrôle s'insère donc **entre les téléchargements et la fusion**, seul point du run à tenir les deux termes — l'**inventaire** de ce que les jobs ont publié et le **disque** — et trois issues en sortent : rien de publié → silence (le repli de #412 §2.1 tient), publié et arrivé → rien à dire, publié et vide → **panne**, rattrapée par `gh run download` puis bloquante ; le rattrapage emprunte volontairement l'**autre chemin** (`gh` passe par l'API REST quand l'action interroge `results-receiver`, celui qui a rendu le 403), recolle à plat ce que `gh` range par sous-répertoire, et retente trois fois — la limite qui a produit l'incident a duré **moins de trois secondes** ; **deux asymétries assumées** : `parltrack-dumps` est rattrapé mais jamais bloquant (repli déclaré, portail §5), et un inventaire illisible **n'échoue pas** — « je ne peux pas vérifier » n'est pas « il n'y a rien » (§2 règle 5), d'où un `inventaire()` qui rend `None` et non une liste vide ; les quatre `continue-on-error` **restent**, ce lot ne les remplace pas, il sépare la source muette de la collecte perdue ; **alternative écartée** : retirer les `continue-on-error`, qui rendrait bloquante toute source n'ayant rien produit — ce que #412 §2.1 refuse — et un `retry` sur l'action, qui rejouerait la requête que la limite vient de refuser. 15 tests neufs, suite complète à 4 162, 0 échec.

## Contexte

Le run `34241352524` est **vert et n'a collecté personne**. Sa fusion a écrit
`0 profil(s)` là où le run précédent, sur le même code et à moins d'une heure
d'écart, en écrivait `636`.

Les quatre téléchargements d'artifacts d'extraction de `merge-and-pivot` sont
partis dans la même seconde et ont tous reçu la même réponse sur
`ListArtifacts` :

```
[Response] - 403
"You have exceeded a secondary rate limit. Please wait a few minutes..."
##[error]Unable to download artifact(s): Received non-retryable error
```

15:52:27.9 (AN), 15:52:28.4 (UE), 15:52:29.0 (ParlTrack), 15:52:29.4 (roster).
Le cinquième téléchargement du job, `candidats-a-jour`, a réussi à 15:52:30.4 :
la limite aura duré **moins de trois secondes**, et elle a suffi.
`download-artifact` ne rejoue pas un 403 — il le déclare *non-retryable* — et
les quatre steps portent `continue-on-error: true`, posé exprès pour qu'une
source en échec ne bloque pas les autres. `merge_raw_dirs` a donc vu quatre
répertoires vides et dit ce qu'il dit toujours devant un dossier absent.

Les artifacts, eux, étaient là : l'API du run en liste **40** `raw-profiles-an-*`
et **8** `raw-profiles-roster-groupes-*`, non expirés, dont les cinq candidats
que #775 attendait. Une heure treize de collecte, jetée entre le producteur et
le consommateur.

| Run | Transport | Fusion |
| --- | --- | --- |
| `34233153883` | 30 artifacts AN + 7 roster téléchargés | **636** profils écrits |
| `34241352524` | 4 × 403 secondary rate limit | **0** profil écrit |

## Pourquoi aucun garde-fou n'a rougi

Ils mesurent tous la collecte **après** la fusion. Sans profil brut, le contrôle
de perte ne voit aucune perte (#460/#470), celui de #511 n'a rien de
collecté-non-publié à signaler, et la §5b ne réclame d'entrée de correspondance
pour personne. Le run est vert **par absence** — le motif que #484 nomme déjà
ailleurs : *une panne rend le même vide qu'une absence*, et rien ne les
distingue quand on ne regarde que le résultat.

C'est aussi ce qui rend le défaut non déterministe. Rien dans le code ne dit
quand il frappera, et **un run vert ne prouve pas qu'il n'a pas frappé** : la
seule trace est un `##[error]` dans un step marqué `continue-on-error`, que rien
ne remonte.

## Décision

Un step de contrôle, `src/verifier_transport_artifacts.py`, s'insère **entre les
téléchargements et la fusion**. Il est le seul point du run à tenir les deux
termes de la comparaison :

- l'**inventaire** — ce que les jobs d'extraction ont publié, lisible par l'API
  du run ;
- le **disque** — ce qui est arrivé.

Trois issues, nommées séparément parce qu'elles se ressemblent sur le disque et
pas du tout dans les faits :

| Inventaire | Disque | Conduite |
| --- | --- | --- |
| rien de publié | vide | **silence** — une source qui n'a rien produit n'est pas une panne, et le repli de #412 §2.1 tient |
| publié | arrivé | rien à dire |
| publié | vide | **panne** — rattrapage par `gh run download`, puis échec |

Le rattrapage emprunte volontairement l'**autre chemin** : `gh` passe par l'API
REST du dépôt quand `download-artifact` interroge le service `results-receiver`,
et c'est ce dernier qui a rendu le 403. Deux chemins pour une même donnée, seule
redondance disponible ici. Trois tentatives, 20 s puis 60 s, parce que ce qu'on
attend n'est pas une panne durable mais une rafale.

`gh run download` range chaque artifact dans son propre sous-répertoire là où
l'action aplatit (`merge-multiple: true`) : le rattrapage recolle à plat, sans
quoi il réussirait sans servir à rien.

## Les deux asymétries, et leur raison

**`parltrack-dumps` est rattrapé, jamais bloquant.** Son repli est déclaré,
`--enrich-parltrack` sait tourner sans lui et le portail §5 le mesure. Bloquer
dessus ferait échouer un run pour une dégradation que le dépôt publie déjà.

**Un inventaire illisible n'échoue pas.** Si l'API refuse de répondre, ce module
ne sait pas ce que le run a publié — et « je ne peux pas vérifier » n'est pas
« il n'y a rien » (§2 règle 5, et le `indetermine` de #757). Il l'annonce
(`TRANSPORT_INVENTAIRE_INDISPONIBLE`) et rend la main : ce que le run fait
ensuite est ce qu'il faisait avant ce module, ni pire, ni fabriqué. C'est aussi
pourquoi `inventaire()` rend `None` et non une liste vide — le type porte la
distinction, et la confondre serait refaire le défaut qu'on corrige.

## Ce qui ne change pas

Les quatre `continue-on-error: true` **restent**. Ils sont la bonne conduite pour
une source qui n'a rien produit, et ce lot ne les remplace pas : il sépare ce cas
de celui où la collecte a eu lieu et n'arrive pas.

`candidats-a-jour` n'entre pas dans le contrôle : son absence a déjà un sens
publié — le run normalise le périmètre d'hier et `CANDIDATS_ARTIFACT_ABSENT` le
dit (#757).

Le jeton du run est pris par `github.token`, jamais par `secrets.GITHUB_TOKEN` :
ce job n'a droit qu'à **une** identité venue de `secrets.`, la clé de
déploiement qui pousse (#508), et un second nom sous ce préfixe rendrait le
ruleset ambigu. Le garde-fou de #508 compte les `secrets.` ; celui de ce lot
vérifie que `github.token` ne sert qu'à `GH_TOKEN` et jamais à un checkout.

## Alternative écartée

**Retirer les `continue-on-error` et laisser le step de téléchargement échouer.**
Le plus court, et faux : il rendrait bloquante toute source qui n'a rien produit,
donc ferait échouer un run entier parce qu'`extract-ue-officiel` a timeouté — ce
que #412 §2.1 a explicitement refusé. La distinction demandée n'est pas
« a échoué / a réussi » mais « a produit et n'arrive pas / n'a rien produit »,
et le step de téléchargement ne connaît pas le second terme.

**Un `retry` autour de l'action.** Rejouer `download-artifact` sur le même
chemin, c'est rejouer la requête qui vient d'être refusée par une limite de
débit. Le rattrapage n'a de valeur que parce qu'il change de chemin.
