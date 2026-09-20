# La couverture se remplace à la maille où #539 la publie, et un cas non tranchable se déclare (#602) (2026-08-30)

`2026-08-30`

> **En bref** — le remplacement descend du bloc à la liste métier (2 858 entrées sur 3 800 étaient perdues face à un écrivain partiel, sur les 481 profils publiés) ; à date et rang d'interrogation égaux, la divergence se déclare au lieu de se choisir sur l'ordre des jobs.

Lot 3 de l'épic #598. `couverture` était pris **en bloc** —
`_prefer_non_empty(new, old)` — sur un modèle que
[#couverture-listes-539](couverture-listes-539.md) a organisé **par liste
métier**.

## La mesure

Corpus committé au 30/08/2026 : **481 profils pivot publiés**, tous porteurs
d'un bloc `couverture` complet sur les cinq listes de #539, **3 800 entrées**.

Rejoué sur ce corpus, face à un écrivain qui ne décrit qu'une liste (`votes`) :

| Règle | Entrées conservées sur les 3 800 | Profils perdant au moins une liste, sur 481 |
| --- | ---: | ---: |
| avant — le bloc au dernier écrivain qui en a un | 942 | **481** |
| après — remplacement par liste | **3 800** | **0** |

## Ce que la décision ne change pas

**`couverture` reste remplacée, jamais unie additivement** (#539, décision 4).
Une entrée de couverture décrit **le run**, pas la personne : l'unir aux
anciennes ferait survivre indéfiniment un `couvert` à côté d'un `non_collecte`
d'aujourd'hui — la panne masquée par son propre historique. Le remplacement
descend d'un cran, du bloc à la liste ; il ne devient pas une union.

**L'unité échangée est le jeu d'entrées entier d'une liste**, jamais une entrée
recomposée. C'est ce qui fait que la `cause` et la `portee` suivent l'état
auquel elles se rapportent : la forme générale de #539 est à deux entrées
(`couvert` sur la fenêtre couverte, `hors_couverture` avant), et prendre l'état
d'un écrivain avec la portée de l'autre publierait une frontière que personne
n'a constatée.

## La règle, en quatre temps

`merge_profile.fusionner_couverture`. Chaque temps porte sur la donnée, jamais
sur l'ordre des jobs de `generate-data.yml` — qui est un détail de la CI.

| # | Règle | Ce qu'elle empêche |
| --- | --- | --- |
| 1 | Une liste dont un écrivain ne dit rien garde ce que l'autre en dit | Le défaut du lot : quatre listes effacées par un écrivain qui en décrit une |
| 2 | Le constat le plus récent l'emporte (`constate_le`) | Qu'un `couvert` d'hier, recopié d'un profil committé, enterre la panne de ce matin — le piège de #539 décision 4 |
| 3 | À date égale, l'écrivain qui a **interrogé la source** l'emporte sur celui qui ne l'a pas fait | Que `--dirs an ue roster` décide entre le `couvert` du job AN et le `non_collecte`/`par_decision` du job roster, qui porte `--skip-interventions` en dur (#357) |
| 4 | À date et rang égaux, contenus différents : **non tranchable** | Qu'un cas que rien ne départage se choisisse en silence |

Le rang du temps 3 lit ce que l'écrivain a **demandé** à la source, pas ce qu'il
y a trouvé — c'est la règle qui gouverne tout `couverture_profil` (« la
condition porte sur la santé de la source, jamais sur l'absence de résultat »),
relue au moment de la fusion :

| Rang | États | Ce que l'écrivain a fait |
| ---: | --- | --- |
| 3 | `couvert`, `fait_etabli` | la source a répondu |
| 2 | `hors_couverture` | la source ne couvre pas : frontière connue |
| 1 | `non_collecte` / `panne`, `non_collecte` / `defaut_collecte` | demandé, échoué — les deux causes se valent **ici**, l'ordre de [#defaut-collecte-vs-panne-562](defaut-collecte-vs-panne-562.md) départage la cause, pas l'interrogation |
| 0 | `non_collecte` / `par_decision` | rien n'a été demandé |

## Le cas non tranchable : conservé et déclaré

Deux écrivains, le même jour, au même rang, avec des contenus différents. Aucune
règle sur la donnée ne les départage.

**La couverture déjà publiée est conservée** — ne rien changer est le seul geste
qui ne prétende pas avoir tranché — **et la divergence est déclarée** dans
`meta.warnings[]`, sous la famille `couverture divergente non tranchée`. Le
message nomme les listes concernées.

Il est **recalculé à chaque fusion** et s'éteint quand la divergence disparaît,
même patron que le warning de non-corroboration de `chambres` (#493) : ramené de
l'ancien profil par l'union de [#union-warnings-extinction-600](union-warnings-extinction-600.md),
il décrirait un constat que la fusion courante ne retrouve pas. Il a sa famille
dans `FAMILLES_WARNINGS` parce qu'il porte une énumération, donc un compteur :
sans elle, deux fusions successives publieraient deux énumérations côte à côte,
dont une périmée.

## L'alternative écartée : trancher la divergence par une priorité d'états

Ordonner les quatre états et publier le plus haut, ou le plus réservé.

Écartée pour la raison qui a fait écrire #562 : **un ordre inventé produit une
imputation**. Publier le plus réservé ferait dire « non collecté » à côté d'une
liste pleine ; publier le plus affirmatif ferait taire une panne constatée le
même jour. Dans les deux cas le produit choisirait un coupable sans avoir la
mesure qui le désigne — et le ferait en silence, ce qui est le défaut que ce lot
retire, pas celui qu'il ajoute.

## Ce que ça ne change pas non plus

Une **clé hors nomenclature** survit à la fusion. La faire disparaître rendrait
`schema_pivot.valider_couverture` muet sur elle : le bloc passerait pour
conforme parce que la fusion l'a nettoyé.

L'ordre des listes du bloc fusionné suit `LISTES_COUVERTES`, pour que git ne
voie une différence que là où le contenu a bougé.
