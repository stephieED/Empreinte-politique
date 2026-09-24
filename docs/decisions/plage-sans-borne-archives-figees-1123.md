<a id="plage-sans-borne-archives-figees-1123"></a>
# Les archives figées se demandent en plage sans borne, la législature en cours garde ses segments (#1123) (2026-09-24)

`2026-09-24`

> **En bref** — Le téléchargeur bornait chaque plage à 32 Mo. La source d'amendements coupe **chaque** réponse, mais ce qu'elle délivre avant de couper va de 0 à 211 Mo : le segment bornait donc le bon cas, et chaque segment suivant était un nouveau tirage. Les archives **figées** passent en `bytes=<offset>-` ; la 17e garde le segment borné, faute de mesure sur son chemin.

## Constat

24/09/2026, depuis un poste, sur `Amendements_XV.json.zip` (648 Mo). Toutes les
réponses finissent en erreur de flux HTTP/2 (`curl` 92), à n'importe quel
décalage. Ce n'est **ni un débit trop faible ni un mur** — les deux lectures
qu'on avait faites jusque-là :

| Décalage demandé | Tentatives | Octets obtenus |
| --- | --- | --- |
| 0 | 3 | 6,2 Mo |
| 4 Mio | 3 | 53,8 Mo |
| 16 Mio | 5 | 247,4 Mo, dont **211,7 en une seule réponse** |
| 34 Mio | 3 | 15,2 Mo |
| 64 Mio | 10 | 80,6 Mo, dont 6 tentatives à zéro |

Sur 46 plages **sans borne** : 577 Mo cumulés, **12,6 Mo par tentative**.
L'archive entière est venue en 89 minutes, **352 tentatives dont 6
productives** — le fichier tient en six réponses chanceuses. Le job de CI, en
segments bornés, plafonnait à 35 Mo en 1 300 s.

## Décision

`chunk_bytes = 0` demande une plage sans borne, et
`AMENDEMENTS_DOWNLOAD_CHUNK_BYTES_FIGEES` la câble sur les deux chemins qui
tirent une archive close : la passe de CI (`construire_un_contenu_fige`) et
l'outil local (`build_amendements_index_figees.py --download`).

Deux effets se cumulaient, et c'est leur somme qui coûtait :

1. une réponse qui aurait délivré 200 Mo était **tronquée à 32** ;
2. chaque segment suivant était une **nouvelle requête**, donc un nouveau
   tirage qui peut rendre zéro.

Une plage ouverte tronquée se traite exactement comme un segment tronqué :
`_telecharger_flux` écrit au fil de l'eau, la reprise repart de l'octet
réellement obtenu, et le principe de #443 — ne jamais jeter un préfixe valide —
est inchangé.

## Ce que cela ne contredit pas

#443 a mesuré que « 8 Kio échouent autant que 32 Mio », et cette décision ne
revient pas dessus : cette phrase porte sur les **échecs**, celle-ci sur le
**rendement quand ça passe**. Les deux sont vraies, et c'est pourquoi la taille
de segment restait un mauvais levier tant qu'on la lisait comme un remède aux
états 2 et 3.

## La 17e ne change pas, et c'est un choix

La législature en cours passe par le même téléchargeur, dans un job qui n'a pas
le même budget, et son archive n'a **jamais** posé ce problème. Lui changer sa
forme de requête sur la foi d'une mesure faite ailleurs serait un pari, pas une
décision. `AMENDEMENTS_DOWNLOAD_CHUNK_BYTES` reste son défaut, et un test le
tient.

## Ce qui n'est pas mesuré, et qu'il ne faut pas lire comme acquis

**Les 12,6 Mo par tentative viennent d'un poste, pas d'un runner GitHub.** Le
chemin réseau n'est pas le même, et rien ne dit que la source se comporte de
façon identique vu d'Azure. Le premier run qui reconstruira une archive figée
sera la vraie mesure ; d'ici là, ce lot améliore une probabilité, il ne garantit
rien.

## Ce que cela ne règle pas

La **conservation du préfixe entre deux runs** reste ouverte, avec ses trois
obstacles nommés dans le `ROADMAP.md` — l'archive partielle supprimée dans un
`finally`, le `Post Run actions/cache` sauté précisément quand l'étape échoue,
et la clé hebdomadaire jamais réécrite. Un run qui n'aboutit pas repart de zéro.
