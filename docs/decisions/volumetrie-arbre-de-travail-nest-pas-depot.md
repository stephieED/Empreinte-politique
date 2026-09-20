<a id="volumetrie-arbre-de-travail-nest-pas-depot"></a>
# Volumétrie : l'arbre de travail n'est pas le dépôt, et la photo n'est pas le coût (2026-08-19)

`2026-08-19`

> **En bref** — l'arbre de travail n'est pas le dépôt, et une photo instantanée n'est pas un coût.

`audit_volumetrie_profils.py` comparait un total d'**arbre de travail** aux
seuils GitHub, qui portent sur le **dépôt** — ce qu'on clone, donc l'historique
compressé. L'écart n'est pas marginal : les profils JSON se déltifient
remarquablement bien.

| | arbre de travail | historique sur disque | facteur |
| --- | --- | --- | --- |
| `raw_data/profiles` | 1 490 Mo | 143 Mo | × 10,4 |
| `pivot_data/profiles` | 1 527 Mo | 109 Mo | × 14,0 |
| dépôt entier | 3 017 Mo de profils | **347 Mo** d'objets atteignables | |

`.git` pèse 670 Mo. Le cadrage de #429 annonçait donc une urgence **d'un ordre
de grandeur au-dessus du réel**, et l'erreur venait de l'outil de mesure
lui-même — pas d'une approximation de rédaction.

## Le vrai compteur : le coût par run

La photo ne grandit qu'avec le nombre de profils. L'**historique**, lui, grandit
à chaque run, définitivement. Le dernier commit de données (`a125e9e`, 209
profils) a ajouté **49,5 Mo** — 23,5 Mo pour le brut, 25,9 Mo pour le pivot.

À 752 profils, un run coûterait environ 180 Mo. En partant des 670 Mo actuels,
le seuil des 5 Go serait atteint après une vingtaine de runs à pleine échelle,
soit quelques semaines de runs quotidiens. **Aucune optimisation de la photo n'y
répond seule** : c'est le caractère récurrent qui décide, et c'est ce que le
rapport dit désormais en toutes lettres.

## Un second piège, corrigé là où on lit le chiffre

`--cible` compte des **fichiers**, pas des profils : `octets_total` est divisé
par le nombre de fichiers scannés. Passer deux répertoires avec
`--facteur-duplication 1.0` projette donc 752 *fichiers*, soit ~376 profils —
ni l'état actuel, ni le scénario d'un seul répertoire. Le bon usage est **un
seul répertoire**, avec le facteur en paramètre.

Je m'y suis fait prendre le 19/08 en mesurant pour #434, et l'invocation citée
dans #429 avait la même forme. Le rapport porte maintenant l'avertissement, à
l'endroit exact où on lit le chiffre — pas seulement dans une docstring que
personne ne relit au moment de conclure.

## Ce qui n'a pas changé

La mesure d'arbre de travail est **conservée** : un checkout de 10 Go est
pénible même si le dépôt tient dans 700 Mo. Les deux chiffres sont rendus côte
à côte, avec ce que chacun signifie — plutôt que de remplacer une mesure
trompeuse par une autre.

`--sans-historique-git` permet de sauter la mesure hors dépôt ou sur un très
gros dépôt, au prix explicite de perdre la seule mesure comparable aux seuils.

