<a id="preuve-de-couverture-reste-technique-1160"></a>
# La preuve d'une entrée de couverture peut citer un champ, une constante ou une issue (#1160) (2026-10-07)

`2026-10-07`

> **En bref** — les phrases de preuve de `couverture` sont écrites pour revérifier, pas pour être lues : sur les 1 402 profils publiés, 11 043 des 13 848 entrées citent un nom technique et 5 565 un numéro d'issue, pour 57 phrases différentes. Aucune vue ne les affiche depuis le 01/10/2026. Arbitrage de la propriétaire, 07/10/2026 : **elles restent en l'état** — noms de champ, de constante et numéros d'issue compris. Le texte lu à l'écran est celui de l'interface.

## Le constat

Mesuré le 07/10/2026 sur le privé `72be714b4`. Une preuve typique : « l'Assemblée
nationale ne publie pas de scrutins avant la XIVe législature — vérifié le
28/08/2026 … — borne portée par candidate_profile.AN_SCRUTINS_LEGISLATURES ».
L'ordre est voulu (`Borne.preuve`) : la limite de la source d'abord, la
constante du dépôt ensuite, pour qu'un lecteur du code public retrouve la borne.

La seule lecture de `preuve` dans `web/UI_finale` porte sur
`meta.couverture_roster` des fiches de groupe (`groupe.js`), pas sur la
couverture d'un profil.

## La décision

Option A : rien ne change. La preuve sert la traçabilité (§2 règle 2) d'un
fichier que l'on télécharge et que l'on réutilise ; elle n'est pas un texte
publié à l'écran, et `couverture_profil.py` n'a pas à écrire pour un lecteur.

## Écarté

| Option | Pourquoi |
| --- | --- |
| Retirer les seuls numéros d'issue | recommandation de l'agent — ils renvoient au dépôt privé, qu'un réutilisateur ne peut pas ouvrir ; écartée par l'arbitrage |
| Réécrire les 57 phrases en français courant | perd le renvoi vérifiable, et 57 textes à relire |
| Une phrase lisible et une référence technique dans un champ à part | changement de schéma sans lecteur |

## Ce qui en découle

Le jour où une vue affiche une preuve de couverture, le texte se montre et
s'arbitre avant d'être écrit (AGENTS.md §11) : c'est alors l'interface qui le
rédige, à partir de l'état et de la portée, pas en recopiant `preuve`.
