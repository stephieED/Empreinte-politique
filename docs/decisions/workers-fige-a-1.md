<a id="workers-fige-a-1"></a>
# `workers` retire du formulaire : un bouton qui ne pouvait que nuire (2026-08-20)

`2026-08-20`

> **En bref** — `workers` retiré du formulaire : un paramètre documenté comme nuisible reste un piège.

`workflow_dispatch` exposait un input `workers` dont la description disait
elle-meme, depuis #467 : « MAINTENU A 1 PAR #467, et desormais sur une mesure :
augmenter cette valeur RALENTIT l'extraction ».

Un parametre qu'on documente comme nuisible reste un piege. Dans un formulaire
`workflow_dispatch`, « workers » se lit comme un levier d'optimisation ; sa
valeur par defaut ne protege que celui qui n'y touche pas.

## Ce que la mesure de #467 etablit

| | `workers=1` | `workers=4` |
| --- | ---: | ---: |
| avant #467 | 74,1 s | **94,6 s** (+28 %) |
| apres #467 | 9,8 s | **13,8 s** (+41 %) |

La charge est du parsing JSON sous GIL, serialise de surcroit par les verrous
par legislature : quatre threads se disputent le meme interpreteur. Le RSS de
pointe monte en prime (1 281 -> 1 374 Mo en local), sur un job deja expose a
l'OOM (#377).

## Pourquoi le figer plutot que le decouper

L'input etait **partage par trois charges de natures differentes** — le chemin
AN et le roster (CPU, parsing sous GIL), `extract-senat`, et `extract-ue-officiel`.
C'est ce qui rendait la question insoluble : impossible de le figer sans perdre
le levier sur les deux autres, impossible de l'ouvrir sans degrader l'AN.

Le decoupage a ete envisage puis ecarte : la description de l'input notait que
le Senat est « reellement borne par NosDeputes », c'est-a-dire par la source et
non par le CPU. Y ajouter des workers ne le rendrait pas plus rapide — cela le
rendrait moins courtois envers une source publique, ce que le projet refuse par
ailleurs (la temporisation de politesse de #467). Le levier ne servait donc
nulle part.

`extract-senat` a ete chronometre a **4,6 min pour un timeout de 90** : aucune
urgence ne justifie de rouvrir la question.

## Ce qui change

L'input disparait du formulaire ; les **cinq** sites qui le lisaient passent a
`--workers 1` en dur (`extract-senat`, `extract-ue-officiel`, le shard roster,
et les deux invocations de `merge-and-pivot`). Le flag `--workers` de
`generate_all_profiles.py` **reste** : il garde son utilite en local, et rien
n'indique qu'il faille amputer la CLI parce que la CI n'en veut plus.

**A rouvrir si** la duree d'`extract-senat` ou d'`extract-ue-officiel` devenait
dimensionnante — auquel cas ce serait un input propre a ces jobs, pas un input
partage avec un chemin que le parallelisme degrade.

