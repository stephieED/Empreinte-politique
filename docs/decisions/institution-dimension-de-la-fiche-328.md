# L'institution est une dimension de la fiche, pas une section — 10/09/2026 (#328)

`2026-09-10`

> **En bref** — quatre institutions lues dans les six sections de la fiche ; la chambre voyage sur le rôle et seul l'affichage la lit, le banc reste intact pour ses quinze consommateurs.

## Contexte

Le corpus a cessé d'être français. Sur les **30 fiches publiées** au commit de
données `b0a142cc` : 16 personnes ont siégé à l'Assemblée, 8 ont exercé une
fonction gouvernementale, **6 ont siégé au Parlement européen**, 2 au Sénat, et
11 n'ont aucune des quatre. Le matériau européen représente **11 013 votes**,
5 329 interventions, 405 textes portés et 7 303 amendements.

Pour trois de ces six — Glucksmann, Philippot, Massard — l'européen n'est pas un
complément : c'est **tout** leur mandat parlementaire.

## Décision

L'institution est une **dimension à l'intérieur des six sections**, jamais une
septième section ni un encadré à part. La trame ne bouge pas : ce qui change,
c'est que chaque acte dit de quel hémicycle il vient.

Une section européenne distincte aurait obligé à trancher, sur la fiche de
Glucksmann, laquelle des deux est la fiche : la française vide, ou l'européenne
pleine. La dimension ne pose jamais la question.

**Quatre institutions**, et elles ne sont pas de même nature dans les données :
`AN`, `Senat` et `PE` sont des valeurs de `chambres` (`KNOWN_CHAMBRES`), le
gouvernement est une **catégorie de mandat** (`fonction_gouvernementale`). C'est
cohérent : on ne siège pas au gouvernement, et un ministre ne vote pas.

## Le banc et la chambre, séparés

`institution` dit le **banc** — `parlement`, `gouvernement`, `mission` — et
quinze endroits du code en dépendent : la comparaison au groupe, les périodes
politiques, les limites de couverture. Le scinder en cinq aurait demandé de les
relire un par un.

La **chambre** voyage donc à côté, sur le rôle, et seul l'affichage la lit :
`pisteDuRole()` en tire `parlement`, `senat` ou `pe`. Les consommateurs du banc
sont inchangés.

## Ce que ça a corrigé, et qui était faux à l'écran

| Fiche | Colonnes avant | Colonnes après |
| --- | --- | --- |
| Glucksmann | À l'Assemblée | Au Parlement européen |
| Mélenchon | À l'Assemblée | À l'Assemblée · Au Sénat · Au Parlement européen |
| Retailleau | À l'Assemblée · Au gouvernement | Au Sénat · Au gouvernement |

Glucksmann n'a jamais siégé à l'Assemblée ; la colonne y portait ses 4 mandats en
commission européens. Retailleau est sénateur depuis 2004 et n'a aucun mandat de
député — son `AN` vient du **repli** de `deriver_chambres()`, la chambre de
collecte, « toujours ajoutée, jamais étayée par un mandat » (#486) —, et la
colonne y portait ses 35 textes.

De même, la limite « la qualification du groupe n'est pas déclarée **par
l'Assemblée** sur N de ses M mandats parlementaires » comptait chez Mélenchon
**cinq** mandats, dont deux européens, un sénatorial et un non estampillé.
L'Assemblée ne dit rien d'un mandat européen, et n'a pas à en dire (§2 règle 2).

## Une institution présente sans activité s'affiche avec son motif

Le Sénat de Mélenchon et de Retailleau est un siège **réel** dont aucune activité
n'est collectée (#528). Taire la colonne dirait « il n'a rien fait » ; l'afficher
vide avec sa cause dit « nous ne collectons pas », et c'est le seul des deux qui
soit vrai (§2 règle 5). Arbitrage de la propriétaire, 10/09/2026.

## Ce que la trame ne peut pas remplir

**La §4 « Où il s'est écarté des siens » restera vide à l'européen.** Les 23
fiches de groupe servies sont 21 AN et 2 Sénat, aucune européenne, et le profil
de Glucksmann ne porte aucun mandat `groupe_politique` : son groupe au Parlement
européen n'est pas dans les données. La section reste présente et vide, avec son
motif — comme le Sénat.

## Alternative écartée

Scinder `INSTITUTION_PARLEMENT` en trois constantes. Écartée : quinze
consommateurs à relire pour un besoin qui est d'affichage, et chacun d'eux aurait
dû redire « les trois chambres » là où il dit « le banc ».
