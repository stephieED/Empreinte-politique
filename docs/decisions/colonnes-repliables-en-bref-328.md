# Les colonnes de « En bref » se replient, et le Sénat l'est d'entrée — 10/09/2026 (#328)

`2026-09-10`

> **En bref** — le repli d'une colonne par le lecteur n'est pas le retour des onglets : tout est ouvert au départ sauf le Sénat, on ne peut jamais tout replier, et une colonne repliée reste nommée par sa puce.

## Contexte

« En bref » apparie des colonnes : « des objets de même nature se font face ».
#328 avait écarté des **onglets par rôle** pour cela — « ils ne montrent jamais
les deux ensemble » — et `test_l_appariement_survit_a_l_ecran_etroit` interdisait
jusqu'au mot `useState` dans le composant.

Deux choses ont changé depuis. Les colonnes ne sont plus deux mais **jusqu'à
quatre** : Assemblée, Sénat, Parlement européen, gouvernement. Et deux des trente
fiches publiées portent un siège au Sénat dont **aucune activité n'est
collectée** (#528) : la colonne existe, elle est vraie, et elle ne contient que
des cellules vides.

## Décision

Le lecteur peut replier une colonne. Ce n'est pas le retour des onglets, et trois
propriétés l'en séparent :

1. **Tout est ouvert au départ**, sauf le Sénat, nommément.
2. **On ne peut jamais tout replier** : la dernière colonne ouverte ne se replie
   pas. Un tableau sans colonne n'est plus un tableau, c'est un gabarit.
3. **Une colonne repliée reste nommée** par sa puce, éteinte, au-dessus du
   tableau. Replier n'efface pas : le lecteur voit ce qu'il a rangé et le
   rouvre d'un clic.

Un onglet ne remplit aucune des trois — il choisit à la place du lecteur.

## Pourquoi le Sénat, et pourquoi pas les autres

Sa colonne ne porterait, sur les deux fiches concernées, que des cellules vides :
le Sénat est hors périmètre de collecte, donc ni vote, ni amendement, ni
intervention. La replier met en avant ce que la fiche sait dire ; la **retirer**
effacerait un siège réel, que Mélenchon a tenu de 2004 à 2010 et Retailleau
depuis 2004 (§2 règle 5). Elle s'ouvre donc quand elle est **seule** : sur une
fiche qui n'a que ce siège, replier par défaut donnerait une fiche vide.

## Alternative écartée

**Le rail** : la colonne repliée reste debout à sa place, réduite à une bande de
38 px portant son nom tourné. Elle a le mérite de ne jamais réordonner le
tableau, et la propriétaire la préférait — écartée sur son propre arbitrage :
« j'aime bien la version A, mais je ne suis pas sûre que ça plaira à tout le
monde ». Un nom vertical se lit moins vite, et quatre rails repliés occupent
150 px pour ne rien montrer.
