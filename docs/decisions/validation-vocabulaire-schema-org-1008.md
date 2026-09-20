<a id="validation-vocabulaire-schema-org-1008"></a>

# Le balisage se valide contre le vocabulaire de schema.org, pas contre la disponibilité de Google (#1008) (2026-09-18)

`2026-09-18`

> **En bref** — le critère de fin de #1008 demandait que **chaque** fiche soit vérifiée par un validateur. Mesuré le 18/09/2026 : celui de Google (`validator.schema.org`) refuse au-delà d'une trentaine de requêtes — 35 pages validées à 0 erreur, puis **34 sur 34 bloquées**, même espacées de six secondes, avec une redirection vers sa page « sorry ». Un critère de fin qui dépend d'un service qui rationne n'est pas rejouable : `scripts/vocabulaire-schema-org.mjs` télécharge le **vocabulaire que schema.org publie** (1,5 Mo, 3 256 termes) et vérifie que chaque `@type` existe et que chaque propriété appartient à son type ou à l'un de ses parents. Branché sur `verifier-referencement.mjs`, il a rendu **0 anomalie sur les 60 objets JSON-LD des 64 pages en ligne**. **Le piège, payé le même jour** : une première passe a rendu **420 anomalies, toutes fausses**, venues du patron `Role` — un rôle daté **porte la propriété par laquelle il est rattaché** (`Person.memberOf` → `OrganizationRole.memberOf` → `Organization`), ce que `domainIncludes` ne peut pas exprimer ; un `Role` accepte donc toute propriété connue. Un vocabulaire indisponible **ne fait pas échouer** le contrôle du site : il se dit, et `--sans-vocabulaire` saute l'étape. 8 tests, deux mutations vérifiées échouantes.

Ancres : `vocabulaire-schema-org.mjs`, `verifier-referencement.mjs`.

## Contexte

#1008 a posé le balisage. Sa vérification reposait sur deux outils en ligne :
l'outil de résultats enrichis de Google, qui ne prend qu'une adresse à la fois,
et son validateur `validator.schema.org`. Le second a tenu 35 pages, puis a
rationné — et un critère de fin qu'on ne peut pas rejouer ne tient personne.

## Décision

| Ce qui est vérifié | Comment |
| --- | --- |
| Le type existe | il est dans le vocabulaire publié par schema.org |
| La propriété existe | idem |
| La propriété appartient au type | `domainIncludes`, en remontant les classes parentes |
| Un `Role` porte la propriété qui l'attache | exception explicite, c'est la règle du vocabulaire |

Ce que ce contrôle **ne dit pas** : si un type donne droit à un affichage
enrichi dans Google. Seul l'outil de Google le dit, et `Person` n'y donne pas
droit de toute façon — ce n'est pas ce que le lot cherchait.

## Alternative écartée

**Espacer les requêtes vers le validateur de Google.** Essayé : six secondes
entre deux appels n'ont rien changé, 34 sur 34 refusées. Le blocage porte sur la
séquence, pas sur la cadence.
