<a id="collecte-vs-publie-545"></a>
# Ce que la normalisation a le droit de faire : la table de relations collecté → publié (#545) (2026-08-28)

`2026-08-28`

> **En bref** — chaque liste déclare les chemins bruts dont elle somme les longueurs ; seuil 0.

Quatre garde-fous tournent maintenant avant le commit de `merge-and-pivot`.
Le quatrième — `src/audit_collecte_vs_publie.py` — ne surveille pas une
nouvelle donnée : il surveille l'**espace entre** les trois autres.

| Garde-fou | Compare | Pourquoi il n'a pas vu #540 |
| --- | --- | --- |
| `audit_diff_profils` (#460/#470) | deux états **publiés dans le temps** | la publication a *augmenté* (0 → 891) : ce n'est pas une perte |
| `audit_collecte_non_publiee` (#511) | deux listes de **noms de fichiers** | raisonne sur des profils ; les sept porteurs avaient tous un pivot |
| `audit_integrite_referentielle` (#485) | une clé et son **index** | ne compte rien : 891 clés qui résolvent lui valent autant que 16 242 |
| `audit_collecte_vs_publie` (#545) | deux **étages du pipeline dans le même run**, liste par liste | — |

Aucun des trois premiers n'était en défaut. C'est pourquoi le run
`33100214165` (27/08/2026) a conclu vert avec **7 767 interventions collectées
et 891 publiées**, et que le commit est parti. Le défaut n'a été vu qu'à la
relecture manuelle.

## Le piège : un compteur naïf crie à tort sur deux champs sur cinq

Un `assert len(brut) == len(pivot)` par champ de même nom produirait, sur le
corpus régénéré de `3104e37` (run `33110395663`, 476 profils), deux faux
positifs et zéro information supplémentaire. La table encode donc, pour chaque
liste **publiée**, les chemins du **brut** dont elle est la somme.

| Liste publiée | Doit égaler, dans le brut | Nature | Justification mesurée |
| --- | --- | --- | --- |
| `votes` | `votes` | égalité | `normalize_profil.py:446` mappe un pour un ; la clé de fusion pivot (`_pivot_vote_key`) est le `scrutin_id`, aussi distinctive que la clé brute. **1 312 828 = 1 312 828**, 0 profil en écart |
| `amendements` | `amendements` | égalité | `normalize_profil.py:449`, un pour un. La liste la plus volumineuse du corpus, donc celle où un effondrement de clé coûterait le plus. **3 074 378 = 3 074 378**, 0 profil en écart |
| `interventions` | `interventions` | égalité | `normalize_profil.py:448`, un pour un — **la relation que #540 violait**, non pas à la normalisation mais à la fusion. **16 242 = 16 242**, 0 profil en écart |
| `textes_portes` | `dossiers_legislatifs` | **renommage** | `normalize_profil.py:447` verse l'un dans l'autre. Comparer les champs de même nom rendrait **−472 et +472** pour zéro défaut. **472 = 472**, 0 profil en écart |
| `mandats` | `mandats` **+** `mandat_europeen.mandats_europeens` | **enrichissement attribué** | `generate_all_profiles.py:779` et `:989` versent les mandats européens dans `mandats[]` du pivot ; le brut les range à part. **40 432 = 40 154 + 278**, et l'égalité tient **profil par profil sur les 476**, sans exception |

Le cinquième point est celui qui change la nature du contrôle. L'issue
proposait un « enrichissement **borné** » — une marge tolérée sur `mandats`.
La mesure a montré mieux : l'écart n'est pas une marge, c'est une **seconde
liste collectée**, que le brut range ailleurs. Les douze profils concernés —
`marine-le-pen` +40, `joelle-melin` +36, `constance-le-grip` +30,
`philippe-juvin` +26, `helene-laporte` +26, `manuel-bompard` +23 en tête — ont
tous un écart pivot−brut **exactement** égal à leur nombre de mandats
européens. Déclarer la source plutôt qu'une marge permet de garder le **seuil à
0 sur les cinq relations**, sans aucune tolérance arbitraire.

Une note de cadrage de #545 attribuait ce +278 à des mandats « dérivés des
organes AN ». La mesure ne l'étaie pas : la totalité de l'écart s'explique par
`mandat_europeen.mandats_europeens`, sur les 476 profils et sur **deux** états
du corpus (`deb28a7` et `3104e37`).

## Seuil 0, mesuré sur deux états

Population : les 476 profils de `3104e37`, soit **2 380 couples (profil,
relation)**. **0 déficit et 0 excédent.** Ce n'est pas une valeur basse, c'est
une invariance, et elle tient sur les cinq relations à la fois.

Rejoué sur `deb28a7` — l'état d'avant le correctif de #540, mêmes 476 profils,
matérialisé en lecture seule hors de l'arbre de travail — le contrôle **sort en
erreur** et nomme les profils :

```
[!] gabriel-attal — interventions : 3351 collectée(s), 17 publiée(s) (-3334)
[!] marine-le-pen — interventions : 2247 collectée(s), 384 publiée(s) (-1863)
[!] jerome-guedj — interventions : 1083 collectée(s), 396 publiée(s) (-687)
[!] laurent-wauquiez — interventions : 535 collectée(s), 23 publiée(s) (-512)
[!] bruno-retailleau — interventions : 486 collectée(s), 6 publiée(s) (-480)
[!] 5 couple(s) (profil, liste) publient moins que ce que la collecte a rendu,
    soit 6876 entrée(s) collectée(s) et publiée(s) nulle part (seuil : 0).
```

Les deux autres porteurs d'interventions de cet état — `jean-luc-melenchon`
(15) et `edouard-philippe` (50) — avaient un pivot égal à leur brut : ils ne
sont **pas** nommés, et c'est correct. Les quatre autres relations sont vertes
sur `deb28a7` comme sur `3104e37`.

La double démonstration est le point : le garde-fou attrape ce qu'il prétend
attraper, et laisse passer ce qu'il doit laisser passer.

## Ce qui bloque, ce qui est rapporté

**Bloque — le déficit** : une liste publiée qui porte moins que la somme de ses
sources collectées. C'est #540, et c'est la seule forme de « collecté puis
jamais publié » qu'un compteur peut établir. Bloque aussi un profil
**illisible** : un fichier qu'on n'a pas pu lire n'est pas un profil à 0 entrée,
c'est un rapprochement qui n'a pas eu lieu (AGENTS.md §2.5).

**Rapporté sans bloquer — l'excédent.** Même arbitrage qu'`audit_diff_profils`
sur les changements de valeur — *faux négatif assumé, faux positif refusé* :
la fusion pivot est additive (AGENTS.md §3), donc un pivot conserve légitimement
les entrées d'un run précédent que la collecte du jour n'a pas rendues ;
`purge_mandats_dupliques.py --apply` retire des entrées du **brut seul** ; et un
excédent ne perd rien — la donnée publiée est là. Mesuré : **0 excédent** sur
les 2 380 couples. La catégorie est vide aujourd'hui et reste un compteur de
dérive, comme « publiés sans brut » de #511.

**Rapporté sans bloquer — une liste collectée sans relation déclarée.** C'est
le cas de la prochaine source branchée : elle ne doit pas rester muette, mais
elle ne doit pas non plus annuler un commit au motif que personne n'a encore
écrit sa relation. Annotation `warning` qui la nomme (#518). Mesuré : 0 sur les
deux états — les cinq listes du brut sont toutes couvertes.

**Hors périmètre, et nommé comme tel** : un brut sans pivot (c'est #511, qui
bloque déjà dessus — le compter en déficit de 100 % décrirait un autre défaut),
les champs pivot **dérivés** qui n'ont aucune source collectée (`chambres` de
#493, `tags_thematiques`, `sources`), le **contenu** des entrées, et les couches
agrégées.

## Dimensionnement : lire 4,3 Go sans matérialiser un profil

C'est la difficulté propre à ce contrôle, et ce qui le distingue de #511 : il
faut **ouvrir** les profils bruts, là où « collecté mais non publié » se
contente de comparer deux listes de noms de fichiers. Or un `json.load`
ordinaire du plus gros profil (`veronique-louwagie.json`, 28,6 Mo, 36 154
amendements) coûte **186,3 Mio** — presque tout le plafond de 236 Mio acté par
#460, pour un seul fichier, dans un script dont la mort annulerait la
publication.

`json.load(..., object_pairs_hook=...)`, avec un crochet qui ne retient que les
clés de la table et rend `None` pour tout objet sans clé utile. Le décodeur
construit bien une liste de 36 154 éléments, mais de 36 154 `None` : les chaînes
de chaque amendement sont libérées dès l'objet refermé. Le crochet garde en
outre les paires du **dernier** objet lu — un décodeur récursif referme
l'objet le plus extérieur en dernier, donc ce sont celles de la racine, et c'est
ainsi qu'on connaît les listes de premier niveau que la table ne déclare pas.

| Mesure (`/usr/bin/time`) | Temps | RSS max |
| --- | ---: | ---: |
| `json.load` ordinaire, plus gros profil (médiane de 3) | 0,62 s | 186,3 Mio |
| Le même avec le crochet (médiane de 3) | 0,38 s | **96,0 Mio** |
| Corpus entier : 476 bruts (4,3 Go) + 476 pivots (360 Mo) | 58,7 s | **158,2 Mio** |

Sous les 236 Mio, et processus séparé des trois autres contrôles : le pic du
job reste celui du plus coûteux. La RSS ne dépend plus du nombre d'entrées d'un
profil, seulement du texte du plus gros fichier.

## Quatrième tolérance, cloisonnée

`allow_publication_gaps` (« BREAK GLASS ») n'est désarmée par aucune des trois
autres et n'en désarme aucune. #470 a documenté le piège : rendre bloquant un
contrôle grossier force l'opérateur à relancer avec une tolérance, qui désarme
du même coup les contrôles précis. Les quatre marques de gravité des libellés
restent distinctes — GitHub affiche la description et masque le nom de l'input,
donc la gravité doit se lire dans le texte lui-même. Verrouillé par
`tests/test_ci_collecte_vs_publie.py`.

## Ce que ce lot n'établit pas

- **Aucun run CI n'a encore exécuté ce contrôle.** Les deux démonstrations
  ci-dessus sont des exécutions locales sur les corpus de `3104e37` et de
  `deb28a7` ; le coût en runner reste à mesurer.
- Les relations sont établies sur **deux** états du corpus, pas sur son
  historique. Un `cold_start` ou un `overwrite_profiles` n'a pas été rejoué.
- L'excédent n'a **jamais** été observé : son caractère légitime est déduit du
  code de fusion (AGENTS.md §3), pas d'une mesure. C'est la raison pour laquelle
  il est rapporté et non bloquant — bloquer sur un cas jamais vu serait poser un
  seuil sans mesure.

---

