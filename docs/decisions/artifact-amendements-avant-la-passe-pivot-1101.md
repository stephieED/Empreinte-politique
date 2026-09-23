<a id="artifact-amendements-avant-la-passe-pivot-1101"></a>
# L'artifact des amendements passe avant la génération pivot, et son absence se dit (#1101) (2026-09-22)

`2026-09-22`

> **En bref** — La voie 2 de #1029 n'a rien publié au premier run qui aurait dû le faire : l'étape qui télécharge `.cache/amendements_an` était placée juste avant son premier lecteur, le quality gate, et donc 11 minutes après le second, `publier_contenus`. Zéro contenu publié, zéro `article` posé, et aucune ligne pour le dire. L'étape remonte avant les deux passes pivot, un test verrouille l'ordre, et une législature sans contenu imprime le chemin cherché.

## Constat

Run `35767700159` du 22/09/2026, job `merge-and-pivot` :

| Étape | Heure (UTC) |
| --- | --- |
| Index pivot des amendements, 1re passe | 19:54:39 |
| Index pivot des amendements, 2e passe | 20:03:14 |
| « Download artifact amendements AN (optionnel) » | **20:14:54** |

`extract-amendements-an` avait construit la XVIIe (125 014 amendements, 35 064
mots) et téléversé son artifact. Dans les données publiées (`92c7b3db5`) :
aucun `pivot_data/amendements/*.contenu.json`, et **0 des 14 520 amendements**
de `philippe-brun` portant `article`.

L'étape avait été écrite pour le quality gate (§3d, la fraîcheur des index) et
placée juste avant lui. #1092 lui a ajouté un second lecteur, `publier_contenus`,
dans la génération pivot — sans déplacer l'étape.

## Décision

1. L'étape de téléchargement passe **avant la première passe pivot**, et reste
   `continue-on-error` : son absence est une dégradation, jamais un échec de job.
2. `publier_contenus` **imprime ce qu'elle n'a pas trouvé**, avec le chemin du
   cache et celui du fichier publié. Le défaut a vécu un run entier parce que le
   silence et le succès se ressemblaient.
3. `tests/test_ordre_artifact_amendements_1101.py` verrouille l'ordre du
   téléchargement et de ses trois lecteurs, et vérifie que le
   `continue-on-error` est toujours là. Vérifié par l'échec : replacé à son
   ancienne position, le test tombe sur les deux passes pivot.

## Deuxième cause, trouvée au run suivant : la CI n'appelle pas le script

Le run `35792678909` (23/09/2026, 00h29), avec l'étape remise dans le bon ordre,
a **encore** publié zéro contenu — et sans même la ligne « AUCUN » ajoutée
ci-dessus. `extract-amendements-an` avait pourtant construit deux contenus
(XVIIe : 125 057 amendements, 35 064 mots ; XIVe : 167 420 et 32 836).

La raison est écrite dans le code depuis #696 : **la CI n'appelle jamais
`build_amendements_index_pivot.py`**, elle passe par
`generate_all_profiles._rafraichir_index_amendements`. `publier_contenus` était
câblée dans le seul `main()` du script, donc sur un chemin que le run ne prend
pas. `articles` n'était pas passé non plus : aucun `article` posé sur l'index.

La fonction de la CI publie donc le contenu et pose l'article, et
`tests/test_ordre_artifact_amendements_1101.py` vérifie les **deux** chemins —
le même garde-fou que #696 s'était donné, pour le même piège.

## Ce que cet incident dit, au-delà du lot

**Un consommateur ajouté à un cache déplace le moment où ce cache doit exister
— et un chemin d'appel qui n'est pas celui de la CI ne publie rien.** Les deux
causes étaient dans le même lot, et la première masquait la seconde.
C'est la même famille que #726 (« un audit est un consommateur comme un autre, et
rien ne l'avertit qu'un champ a bougé ») : le lecteur neuf n'a pas de raison de
savoir pour qui l'étape avait été écrite.

## Alternative rejetée

**Relire le cache après le téléchargement, dans une seconde passe de
`build_amendements_index_pivot`** : deux constructions de l'index des 685 664
amendements pour un fichier de contenu, alors que déplacer une étape suffit.
