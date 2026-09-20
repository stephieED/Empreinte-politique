# Ce qu'un run de test coûte vraiment : 51 min, et pourquoi le mode ne peut pas faire mieux (#792)

`2026-09-09`

> **En bref** — le mode de #792 a été exercé pour la première fois (run `34323318020`) et a fait ce qu'il annonçait — **2 shards au lieu de 27**, roster à **1 shard** plafonné à 8, quatre garde-fous verts, **aucun commit** — mais il a duré **51 minutes** quand j'en avais annoncé « ~20-25 », chiffre **jamais mesuré** ; la cause est structurelle : **`merge-and-pivot` fait la moitié du run (25,8 min) et ne peut pas être réduit**, puisqu'il refait les deux passes pivot, les agrégats et les quatre contrôles sur **tout le corpus** — c'est précisément ce qu'un run de test vient exercer, le réduire supprimerait ce qu'on cherche à vérifier —, et quatre autres jobs (amendements AN 7,6 min, UE 7,5, ParlTrack 6,8, matrice roster 6,8) ne dépendent pas du périmètre des candidats ; **gain réel : 1 h 15 → 51 min, un tiers et non les trois quarts**, portant sur la moitié qui échoue vite — une matrice mal calculée ou un artifact qui n'arrive pas (#786) se voit en 25 min contre 55, un défaut *dans* la fusion coûte le même temps qu'avant ; ce que ça change n'est pas l'utilité du mode (il venait d'exercer le chemin d'écriture de #691 sans rien committer, juste avant le run qui supprime 5,55 Go) mais **ce qu'on peut lui demander : il n'y a pas de boucle courte dans ce pipeline**, et la seule qui le soit reste le test unitaire ; l'alternative « aval seul » de #792 reste écartée pour la seule raison qui tenait — elle n'aurait pas vu #786 —, son coût annoncé étant faux lui aussi.

## Contexte

Le mode de test de #792 a été exercé pour la première fois le 09/09/2026, run
[`34323318020`](https://github.com/stephieED/Empreinte-politique-src/actions/runs/34323318020),
sur `delphine-batho,gabriel-attal`. Il a fait ce qu'il annonçait — matrice
réduite à **2 shards** au lieu de 27, roster à **1 shard** plafonné à 8 membres,
quatre garde-fous verts, **aucun commit**.

**Il a duré 51 minutes.** J'avais annoncé « ~20-25 min » en ouvrant #792. Le
chiffre était faux, et il n'était pas mesuré.

## Ce que le mode réduit, et ce qu'il ne réduit pas

| Job | Réduit ? | Durée mesurée |
| --- | --- | ---: |
| `extract-an` | **oui** — 2 shards au lieu de 27 | ~2 min |
| `extract-roster-groupes` | **oui** — 1 shard au lieu de 8 | 15,9 min |
| `merge-and-pivot` | **non** | **25,8 min** |
| `extract-amendements-an` | non | 7,6 min |
| `extract-ue-officiel` | non | 7,5 min |
| `extract-parltrack` | non | 6,8 min |
| `prepare-roster-matrix` | non | 6,8 min |

**`merge-and-pivot` est la moitié du run, et il ne peut pas être réduit.** Il
refait les deux passes pivot, les agrégats de groupe, de parti et de
gouvernement, et les quatre contrôles d'avant-commit — sur **tout le corpus**,
pas sur le périmètre collecté. C'est précisément ce qu'un run de test vient
exercer : le réduire supprimerait ce qu'on cherche à vérifier.

Les quatre autres jobs ne dépendent pas du périmètre des candidats. Un shard de
roster reste long parce qu'il porte les frais fixes de checkout et de cache.

## Le gain réel

**1 h 15 → 51 min, soit un tiers.** Pas les trois quarts annoncés.

Ça reste un gain, et il porte sur la moitié qui échoue vite : un défaut
d'orchestration en amont de la fusion — une matrice mal calculée, un artifact qui
n'arrive pas (#786) — se voit dans les 25 premières minutes, contre 55 dans un
run complet. Un défaut *dans* la fusion, lui, coûte le même temps qu'avant.

## Ce que ça ne change pas, et ce que ça change

Le mode reste utile, et il vient de le prouver : il a exercé le nouveau chemin
d'écriture de #691 sur une dizaine de profils sans rien committer, juste avant
le run qui supprime 5,55 Go. C'est exactement l'usage pour lequel il a été
construit.

Ce que ça change, c'est ce qu'on peut lui demander : **il n'y a pas de boucle
courte dans ce pipeline.** Un défaut d'une ligne se paie 51 minutes, pas 20. La
seule boucle réellement courte reste le test unitaire — une demi-seconde — et
#788 en était un.

## Pourquoi une décision plutôt qu'une correction dans #792

Une décision se remplace, elle ne se réécrit pas. Et surtout : l'écart entre un
chiffre annoncé et un chiffre mesuré est un fait qui mérite sa trace. #792 a été
ouverte, argumentée et mergée sur une estimation que personne n'avait vérifiée —
y compris dans son tableau d'options, où « ~20 min » servait à départager deux
conceptions.

L'alternative écartée dans #792 — le mode « aval seul » — reste écartée, mais
pour la seule raison qui tenait : il n'aurait pas vu #786. Son coût annoncé,
« environ le même temps (~20 min) », était faux lui aussi ; il aurait en réalité
coûté les 25,8 min de `merge-and-pivot`, c'est-à-dire à peu près la moitié d'un
run de test, sans en voir le transport.
