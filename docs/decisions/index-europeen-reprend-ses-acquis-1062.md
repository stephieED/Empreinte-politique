<a id="index-europeen-reprend-ses-acquis-1062"></a>
# L'index européen relit ce qu'il a publié : le cache n'est pas une mémoire (#1062) (2026-09-21)

`2026-09-21`

> **En bref** — 996 dossiers sont repassés de « le portail a répondu » à « jamais demandé » parce qu'un cache de CI est parti vide ; l'index reprend désormais ses acquis depuis le fichier publié.

**Contexte** : la passe des domaines EuroVoc de `dossiers_europeens.py`
interroge le portail du Parlement sous un budget de 20 minutes par run, et la
couverture est censée monter d'un run à l'autre. Ce que la passe apprend vit
dans `ResolveurDocuments`, dont le cache est un **cache de CI**
(`public-data-cache-europarl-documents-v3-*`). Le fichier publié, lui, ne sert
qu'à être lu par l'interface.

**Mesuré le 21/09/2026**, premier run sur le dépôt public, dont le cache est
parti vide :

| `pivot_data/dossiers_europeens.json` | Avant (ancien dépôt) | Après le run |
| --- | ---: | ---: |
| avec domaines | 378 | 408 |
| `documents_non_classes` — le portail a répondu, il ne classe rien | **1 493** | **497** |
| `question_non_posee` — nous n'avons jamais demandé | 2 768 | **3 734** |

Le run a fait son travail — 685 requêtes en 21 minutes, 1,85 s l'une — et la
fiche est malgré tout **plus pauvre** qu'avant : ~1 000 dossiers ont perdu un
verdict acquis. **Aucune garde ne pouvait le voir** : les deux états sont des
absences licites (§2 règle 5), et le contrôle de perte compare des
cardinalités, pas des motifs.

**Décision : le fichier publié est la mémoire durable, le cache n'est qu'un
raccourci.** `reprendre_acquis()` relit l'index publié et remplit ce que le run
a laissé en `question_non_posee`.

Ce qui se reprend, et ce qui ne se reprend pas :

| État publié | Repris ? | Pourquoi |
| --- | --- | --- |
| `domaines` non vides | oui, **si le document qui les porte est encore cité** | le dump bouge ; republier un domaine tiré d'un document que le dossier ne cite plus serait une affirmation que la source ne porte pas (§2 règle 2) |
| `documents_non_classes` | oui | c'est une **réponse** du portail |
| `domaine_eurovoc_introuvable` | oui | les concepts sont connus, le domaine manque : un fait établi |
| `eurovoc_injoignable` | **non** | une panne n'est pas une réponse |
| `question_non_posee` | **non** | c'est l'ignorance elle-même |

**Rien n'est figé.** La reprise ne remplit que ce que le run n'a pas demandé :
un verdict obtenu maintenant l'emporte toujours. Le budget du run suivant
réinterroge donc ce qui a été repris, et la fraîcheur gagne.

**Effet mesuré sur le corpus réel**, en appliquant la reprise à l'état publié
ce matin avec l'index de l'ancien dépôt comme mémoire : **475 dossiers avec
domaines** (contre 408), **1 499** `documents_non_classes` (contre 497),
**2 665** `question_non_posee` (contre 3 734). 1 069 entrées retrouvent un
verdict, et l'état dépasse celui d'avant la bascule.

**Alternative écartée : committer le cache du portail** sous `raw_data/`. Il
porte les mêmes faits sous une autre forme, et il faudrait alors le tenir à
jour, l'arbitrer dans les gardes d'avant-commit et le publier — pour ne rien
apprendre de plus que ce que le fichier publié contient déjà.

**Alternative écartée : élargir le contrôle de perte aux motifs.** Il verrait
le recul, mais après coup et en bloquant le commit, là où la cause est qu'une
information acquise n'était lue nulle part. Compter mieux n'aurait pas rendu
les 996 verdicts.

**Ce que ce lot ne fait pas** : sortir la passe des domaines du chemin critique
de `merge-and-pivot`, où elle pèse 21,5 des 52,5 minutes. La question reste
ouverte — et elle se pose mieux une fois que chaque run capitalise au lieu de
recommencer.
