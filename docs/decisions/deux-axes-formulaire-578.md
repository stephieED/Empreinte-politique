<a id="deux-axes-formulaire-578"></a>
# Un paramètre commandait ce qu'il ne nommait pas (#578) (2026-08-29)

`2026-08-29`

> **En bref** — le formulaire de lancement porte deux axes disjoints — ce qu'on fait des profils écrits, qui on collecte — plus le cache ; `roster_limit` ne commande plus de politique.

Trois défauts, une seule faute. `overwrite_profiles` commandait `--no-merge`
sans le nommer ; le rafraîchissement de l'existant dépendait de la présence de
`--limit` ; et `roster_limit=0` rafraîchissait **moins** que `20`. Le lot des
libellés (#577) avait buté dessus : ce ne sont pas les mots qui étaient faux,
c'est le découpage. Le formulaire répondait à **deux questions dans un seul
champ**.

## Les deux axes

**Axe 1 — `existing_profiles`** : ce qu'on fait des profils **déjà écrits**. Un
`type: choice`, pas un booléen, parce que les états sont trois.

| valeur | effet |
| --- | --- |
| `leave-as-is` | pas recollecté — un correctif de collecte ne l'atteint jamais |
| **`refresh`** *(défaut)* | recollecté et **FUSIONNÉ** — rien n'est perdu |
| `overwrite` | recollecté et **REMPLACÉ** (`--no-merge`) |

**Axe 2 — `roster_coverage`** : si on écrit un premier profil pour les membres
qui n'en ont pas. `current-members-only` ou `add-uncovered-members` (défaut).

> **Mise à jour (#590, 29/08/2026)** : ce champ est **renommé
> `add_uncovered_members`** et passe de menu à **case à cocher**, cochée par
> défaut — deux états n'ont jamais eu besoin d'un menu. `roster_coverage`,
> `current-members-only` et `add-uncovered-members` sont des noms **morts** ;
> `test_les_deux_axes_sont_deux_champs_distincts` échoue si `roster_coverage`
> réapparaît dans les inputs. Le découpage en deux axes, lui, est inchangé :
> lire ci-dessous « décoché » pour `current-members-only` et « coché » pour
> `add-uncovered-members`. État courant du formulaire :
> `docs/workflow-generate-data.md` §2, et `python3 scripts/rendu_formulaire.py`.

Les deux sont **disjoints**, donc les six combinaisons se demandent — dont
« recollecter l'existant **en fusionnant** ET ajouter les nouveaux », qu'aucun
réglage ne permettait d'obtenir avant. Traduction en drapeaux, dans le job
`extract-roster-groupes` :

| | `current-members-only` | `add-uncovered-members` |
| --- | --- | --- |
| `leave-as-is` | rien à faire (manifeste vide) | `--skip-existing` |
| `refresh` | `--refresh-existing` | *(aucun drapeau)* |
| `overwrite` | `--refresh-existing --no-merge` | `--no-merge` |

La case vide en haut à gauche est une **réponse, pas une panne** : on ne touche
pas à l'existant et on n'étend pas la couverture. Le step écrit un manifeste
vide et sort en 0 — « ce job n'a écrit aucun profil » plutôt que « le job a
échoué » ([[publication-scopee-artifacts]] : un manifeste absent est un
incident, un manifeste vide est un fait).

## Le défaut passe à `refresh`

Changement de comportement assumé. Sur #562, le code était juste pendant deux
runs et la donnée restait fausse, parce que le mode sûr n'était atteignable
qu'en le demandant explicitement. **Le mode le plus sûr doit être celui qu'on
obtient sans rien cocher.** Coût mesuré, sur les deux runs du 28/08/2026 :

| run | mode | durée |
| --- | --- | --- |
| `33185097538` | sans toucher à l'existant | 56 min |
| `33200210924` | en rafraîchissant les 481 profils | 66 min |

**Dix minutes.** Le temps d'un run est dominé par `extract-an` — treize shards
séquentiels de candidats — pas par le job roster.

## `roster_limit` : un plafond, et son défaut passe à 0

Il conflatait « combien de membres » et « faut-il étendre ». Avec l'axe 2
explicite, il ne reste qu'un **plafond de volume**, orthogonal aux six cases :
il les borne, il n'en déplace aucune (verrouillé par
`test_le_plafond_est_orthogonal_aux_deux_axes`).

Son défaut passe de **20 à 0** (pas de plafond), et c'est une conséquence du
point précédent, pas un goût. Le rollout progressif qu'il budgétait est
terminé — roster couvert à **452/452** — et un plafond de 20 ferait mentir le
défaut `refresh`, qui promet qu'un correctif de collecte atteint l'existant
**sans qu'on le demande** : avec 20, il faudrait ~23 runs pour propager une
correction à tout le roster. Les 66 minutes mesurées ci-dessus sont celles de ce
défaut-là.

## Le rafraîchissement ne dépend plus d'un plafond

C'est le même défaut un cran plus bas, dans `src/generate_all_profiles.py`.
L'exemption au saut de `--skip-existing` était posée par la **seule présence de
`--limit`** :

```python
if args.limit is not None and args.skip_existing:      # avant #578
    candidats, refresh_slugs = _select_candidats_couverture(...)
```

Sans `--limit`, la branche n'était pas empruntée, `refresh_slugs` restait vide,
et `process_candidat` sautait **chaque** profil existant. D'où le tableau qui
n'a aucune raison d'être :

| `roster_limit` | `--limit` passé ? | profils existants rafraîchis |
| --- | --- | --- |
| `20` | oui | les périmés, dans la limite du budget |
| `0` | non | **aucun** |

C'est ce qui a coûté le second run raté du 28/08/2026 : `roster_limit=0` avait
été choisi précisément pour tout régénérer.

**Trois populations, trois intentions nommées.** `--skip-existing` (les
non-couverts), `--refresh-existing` (l'existant), ni l'un ni l'autre (tout le
monde). `--skip-existing` devient **strict** : plus d'exemption implicite, donc
`refresh_slugs` disparaît — l'exemption s'exprime maintenant en ne posant pas le
drapeau. `_select_candidats_couverture` reste, mais ne répartit plus qu'un
budget.

**La péremption est une règle de priorité sous plafond, jamais une politique.**
Un correctif de code ne périme aucune date : le profil régénéré hier est
« frais » au sens de `compute_profils_perimes`, et c'est pourtant exactement
celui qu'un correctif doit atteindre. Sans plafond, `refresh` recollecte donc
**tout** l'existant, pas seulement le périmé.

## `cold_start` cesse de porter l'écrasement

`cold_start` n'est ni « qui » ni « comment écrire » : c'est **à quel point les
données sources doivent être fraîches**. Il levait aussi `--no-merge` et
supprimait `raw_data/profiles/*.json` — deux politiques d'écriture déguisées en
politique de fraîcheur (un profil effacé n'a plus rien à fusionner). Il ne fait
plus que `rm -rf .cache`.

Conséquence à écrire noir sur blanc : **écraser sans purger le cache est un cas
réel et courant** — on réécrit les profils à partir d'archives déjà
téléchargées, sur une source AN dont l'indisponibilité a déjà bloqué trois
chantiers (#440, dont [[telechargement-an-trois-modes-defaillance]] rappelle la
correction de clé). Et sa réciproque devient demandable pour la première fois :
repartir de sources fraîches **en fusionnant**.

Sans effet sur le corpus committé : depuis #450 chaque job ne publie que ce
qu'il a écrit, et `merge-and-pivot` refait son propre checkout.

## L'avertissement de `roster_refresh_existing` est SUPPRIMÉ

Il disait : *« refresh sans overwrite : les profils seront FUSIONNÉS, pas
écrasés. Une correction de clé laisserait les entrées erronées en place. »*

Il devait viser la **nature de la correction** — clé ou non. Il ne le peut pas :
**le workflow ne sait pas ce que le correctif corrige.** Il n'a ni le diff de
`src/`, ni l'intention de qui lance le run. Réécrire l'avertissement en
prétendant le contraire serait écrire un faux.

Ce qu'il faisait en pratique était l'inverse de son intention : il traitait le
mode le **plus sûr** comme suspect, sur le mode qui est désormais le **défaut**
— donc à chaque run — et poussait à prendre `--no-merge` sans en avoir besoin.
Un signal qui se déclenche sur le cas normal est celui qu'on apprend à ignorer,
mécanisme déjà constaté sur la §3 de la quality gate (#460).

Le step émet à la place une ligne de log **non annotée** nommant la combinaison
en vigueur et les drapeaux qu'elle produit. Le signal qui reste sur le mode
destructeur est celui de #460 — `overwrite` sans collecte d'interventions — qui
chiffre la perte sur la baseline committée au lieu de la supposer.

## Ce que ça ne change pas

La fusion additive reste le défaut de `merge_profile.py`. `overwrite` reste le
geste **rare**, réservé à une correction de clé (#440), où la fusion conserverait
les entrées fautives à côté des corrigées.

## Propagation à la relance automatique

`retry-generate-data.yml` reconstruit les inputs d'un run préempté en grepant
les logs. Les deux axes sont lus dans le bloc `env:` résolu du step
d'extraction roster (`EXISTING_PROFILES:`, `ROSTER_COVERAGE:` — devenu
`ADD_UNCOVERED:` avec le renommage de #590) — seule source
exacte : un `choice` n'a pas de step conditionnel qui trahirait sa valeur, et
l'axe 1 n'est pas déductible de `--no-merge` seul, `leave-as-is` et `refresh`
posant tous deux la fusion additive. Repli : `--no-merge` dans la commande
`extract-an` prouve au moins l'écrasement ; sinon on retombe sur `refresh`, le
mode sûr.

---

