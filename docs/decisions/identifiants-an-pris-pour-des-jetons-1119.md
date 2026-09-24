<a id="identifiants-an-pris-pour-des-jetons-1119"></a>
# Les identifiants d'amendements sont pris pour des jetons, et le chemin sort du scanner (#1119) (2026-09-24)

`2026-09-24`

> **En bref** — Le scanner de secrets de GitHub a ouvert cinq alertes « Atlassian API Token » sur des **identifiants d'amendements de l'Assemblée**. La cause est notre propre optimisation : `<lég>.contenu.json` publie l'uid amputé de son préfixe de législature, et les 24 caractères restants tombent dans le motif du jeton. Le corpus en contient 372 135. Le chemin est exclu du scanner, après avoir vérifié que rien d'autre ne peut se trouver dans ces fichiers.

## Constat

24/09/2026, dépôt public. Cinq alertes, quatre au commit de publication
`cb3269d0` (`v1.0.9`, qui ajoutait les contenus de la XVe et de la XVIe) et une
au commit de données `40104bb4` du 23/09 — le phénomène précède donc la
publication qui l'a rendu visible.

Les chaînes signalées sont des uid d'amendements. Relues à la colonne exacte
que l'API donne, elles sont **au milieu d'une suite consécutive** :

    …24P2D1N000131","PO419604B0324P2D1N000132","PO419604B0324P2D1N000133","PO419604B0324P2D1N000134"…

Aucun secret ne s'incrémente. Trois des cinq ont par ailleurs été retrouvées
telles quelles comme noms de fichiers dans les archives d'amendements de l'AN.

## La cause est une optimisation, pas une fuite

`pivot_data/amendements/<lég>.contenu.json` publie l'uid **sans** son préfixe
commun à la législature (`AMANR5L15`), que `uid_complet` recolle à la lecture :
6,6 Mo économisés sur les quatre fichiers. Ce qui reste fait exactement 24
caractères alphanumériques — le motif d'un ancien jeton d'API Atlassian. Avec
leur préfixe ils en feraient 33 et ne ressembleraient à rien.

L'échantillon de GitHub ne dit pas l'ampleur : **372 135 identifiants** du
corpus publié tombent dans ce motif, dont 173 793 pour la seule XVe. Chaque run
qui touche un `contenu.json` peut en rouvrir.

## Décision

Un `.github/secret_scanning.yml` exclut **ce seul chemin** :

    paths-ignore:
      - "pivot_data/amendements/*.contenu.json"

**Ce qui rend l'exclusion sûre a été mesuré avant d'être décidé**, et c'est le
point à ne pas re-litiger : la structure de ces fichiers est entièrement
contrainte. Sur les quatre législatures — 768 216 identifiants — zéro `ids`
hors du motif d'uid de l'AN, zéro clé de `mots` hors `[a-z]{4,}`, zéro renvoi
hors base 36, zéro `articles` mal formé. Un secret n'y entrerait pas sans
casser le schéma, et `amendements_contenu.document` ne fabrique rien d'autre.

`paths-ignore` porte sur l'analyse **et** sur la protection au push, ne ferme
pas les alertes déjà ouvertes — les cinq ont été traitées à la main, en
`false_positive` avec leur motif — et plafonne à 1 000 entrées pour 1 Mo.

## Alternative écartée : exclure tout `pivot_data/`

Le corpus entier est produit par machine depuis des sources publiques, et on
aurait pu l'exclure d'un trait. Refusé : `raw_data/` et le reste de
`pivot_data/` ne coûtent rien à analyser, et le jour où un jeton se glisse dans
un profil brut — ce qui n'est pas une hypothèse d'école, une clé d'API traîne
dans un environnement de collecte — on veut que le scanner le voie. Une
exclusion large achète un angle mort permanent contre un bruit ponctuel.

## Ce qui n'est délibérément pas exclu

Les actes réglementaires portent eux aussi des chaînes de 24 caractères :
`dihydroxydiphenylsulfone`, `dodecylbenzenesulfonique`, `hydroxybenzylphosphonate`
— des mots de chimie tirés des titres de décrets, rangés dans leur index de
mots. Aucun contrôle d'entropie ne les prend pour des jetons, et aucune alerte
ne les a jamais visés. Les exclure par précaution n'achèterait qu'un angle mort
de plus.
