<a id="reperes-de-la-fiche-candidat-1142"></a>

# Ce que la fiche candidat nomme, et où se situe sa voix (#1142) (2026-09-25)

`2026-09-25`

> **En bref** — Cinq défauts relevés sur la fiche d'Emmanuel Maurel, qui n'a
> **aucun mandat de catégorie `fonction_gouvernementale`** et dont la fiche disait
> « Au gouvernement » à deux endroits. Un était un bug de rangement, deux étaient
> des mots, un était une décision déjà prise et jamais appliquée, et le dernier
> ajoute un repère qui manquait. Les trois arbitrages ont été rendus sur maquette
> le 25/09/2026.

## Une racine commune : la fiche prêtait une institution

Deux sections attribuaient un banc gouvernemental à qui n'en a jamais occupé, et
pour deux raisons différentes — l'une de calcul, l'autre de vocabulaire.

**Le rangement.** La liste ouverte au clic sur la cascade des textes portés
filtrait ses colonnes sur `t.projetDeLoi`, c'est-à-dire la **nature** du texte. Un
**rapporteur** d'un projet de loi s'y retrouvait « Au gouvernement » : c'est le
contresens exact que #689 avait corrigé dans l'autre sens. Mesuré : **18 des
1 098 textes portés des 34 candidats publiés**, dont les deux « Projet de loi de
finances » (2025 et 2026), promulgués, dont Maurel est co-rapporteur. Le
commentaire du code décrivait déjà le bon comportement pendant que le code
appelait l'autre fonction. `institutionDuTexte` lit `role` d'abord.

**Une quatrième colonne, et non un repli.** 6 des 1 098 textes n'ont aucune
attribution sourcée. Les fondre dans « À l'Assemblée » inventerait une initiative
personnelle (§2 règle 5) ; les taire les ferait disparaître de la liste. Ils
prennent donc leur colonne, au gris des métadonnées et **jamais à une quatrième
teinte** — une teinte les rangerait à côté des trois institutions, alors qu'ils
disent précisément qu'on ne sait pas.

**Le vocabulaire.** Le filtre de « Ce qu'il a voté » nomme l'**origine du texte
voté**, et son calcul est juste ; ce sont ses deux mots — « Gouvernement »,
« Parlement » — qui se lisaient comme un banc occupé. Ils deviennent **« Texte du
gouvernement »** et **« Texte du Parlement »**.

## Le titre dit de quelle majorité il parle

« Les scrutins où il n'est pas du côté majoritaire » se lit comme la majorité de
l'**Assemblée**, ce qui serait un fait politique tout autre. La section compare sa
position à celle de **son groupe**. Retenu : **« Les scrutins où il n'a pas voté
comme la majorité de son groupe »** — le verbe reprend le mot que la légende
emploie déjà, « membres qui n'ont pas suivi ».

Deux formulations écartées : « n'est pas du côté de la majorité de son groupe »
garde une nuance d'alliance là où il s'agit d'un vote, et « sa position diffère de
celle de son groupe » efface qu'il s'agit d'un vote nominatif.

## Le repère porte la teinte de son vote — et c'est un arbitrage

La barre de chaque scrutin portait la répartition du groupe sans dire **où il
est**. Un repère s'y pose, au centre de la part qu'il a rejointe.

**Il porte la couleur de son vote, et cette décision a été prise contre
l'argument inverse.** La lecture proposée le voulait en encre, au motif que le
vert, le rouge et le gris sont pris par les positions et qu'une quatrième teinte
fabriquerait un jugement. La propriétaire a tranché l'autre sens : la couleur
**relie** le repère à la position écrite juste à gauche, et elle n'ajoute aucune
teinte puisqu'elle en reprend une. **Ne pas « corriger » vers l'encre.**

Il est donc de la même couleur que le segment sous lui, et deux choses l'en
détachent, aucune décorative : il **déborde** la barre en haut et en bas, et il
porte un **anneau de la couleur du fond**. Vérifié au rendu sur les trois teintes.

Deux gardes de calcul : le centre se compte **absents compris**, parce que la
barre les montre — les retirer du dénominateur décalerait le repère de tout ce que
leur segment occupe ; et **aucun repère n'est posé quand la part est vide**, un
repère au hasard disant une position qu'il n'a pas prise (§2 règle 5).

## Une prise de parole se cite, et se cite pareil partout

Rien ne séparait la parole rapportée du texte de la fiche. Les guillemets
français — avec leurs espaces fines insécables — encadrent désormais **tout
verbatim**, sur les trois fiches qui en publient : le candidat
(`ParolesParPeriode`), la lignée et le gouvernement (tous deux par
`ExtraitsDuDebat`). Demandé le 25/09/2026, « et ça devrait être le cas partout ».

**La convention vit dans `src/utils/extraits.js`**, pas dans chaque composant :
recopiée trois fois, elle divergerait au premier ajustement.

**L'élision est dans les guillemets, jamais après.** 29,1 % des 1 210 607
extraits publiés sont marqués `texte_tronque` : la collecte s'arrête à 280
caractères. Refermer les guillemets sans élision donnerait une citation complète
là où le propos continue (§2 règle 5). Sur la fiche candidat, `texteTronque`
était **calculé et rendu nulle part** — un extrait coupé s'y terminait sans le
moindre signe.

**Elle s'écrit `[…]` et non `…`**, arbitré sur maquette le 25/09/2026. Une seule
raison décide : **le locuteur suspend lui-même sa phrase.** 1 072 des 352 564
extraits tronqués finissent déjà sur des points de suspension, et des points nus
s'y collent sans que rien ne dise lequel est de lui — « pour assurer une
production nationale… … ». Les crochets disent que la marque est de **nous**.

Deux raisons de moindre poids suivent : **73,7 %** des extraits tronqués
finissent sur un point, où « trois articles. … » se lit comme une coquille et
« trois articles. […] » non ; et les crochets sont la convention française de
l'omission dans une citation, ce qui vaut mieux qu'une invention maison sur une
page qui publie de la parole rapportée. Les 26,0 % coupés sur un mot se lisent
correctement dans les deux formes — ils ne décidaient rien.

**Ce n'est pas une préférence de goût, et le test le dit** : revenir à `…`
rouvrirait la confusion avec la suspension du locuteur.

Une limite mesurée et laissée telle quelle : **1,3 % des extraits** (15 470) se
terminent sans ponctuation finale alors qu'ils ne sont pas marqués tronqués. Le
relevé montre qu'il s'agit de transcriptions qui finissent ainsi, pas d'une
coupe silencieuse ; rien n'est ajouté sur leur foi.

## Ce qui n'a pas été fait, et pourquoi

**Un bouton « toutes les périodes » dans « Ce qu'il a voté »** a été demandé puis
mis de côté le 25/09 : il contredit
[`votes-par-periode-politique-328`](votes-par-periode-politique-328.md) — « aucun
total de carrière, aucun taux : ce serait le score que §2 règle 1 interdit » — et
[`paroles-par-periode-328`](paroles-par-periode-328.md), qui dit explicitement que
cette section ne prend pas `avecTout`. Le cumul reste donc l'exception ouverte par
#979, sous un mot du filtre seulement.

**L'ouverture sur la période la plus récente n'est pas une nouveauté** :
`paroles-par-periode-328` l'écrivait déjà pour les deux sections. « Ce qu'il a
voté » ouvrait sur l'index 0 — le mandat le plus ancien — et ne l'avait jamais
appliquée.
