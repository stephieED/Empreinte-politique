<a id="six-emplacements-fiche-candidat-328"></a>

# La fiche candidat passe à six emplacements, et ce qu'il a voté remonte avant ce qu'il a dit (#328) (2026-09-08)

`2026-09-08`

> **En bref** — trois arbitrages de la propriétaire, et ce qu'ils coûtent : **« les gouvernements dont il a été membre » est retiré** (avec le composant, `buildGouvernements`, `loadGouvernements`, le titre dans les trois voix, la fonction `Barre` et **26 règles CSS**) — la fiche d'un ancien ministre ne télécharge plus ses fiches de gouvernement, jusqu'à quatre chez Attal, et le bilan collectif n'est pas dépublié pour autant, les pages `/gouvernements/:id` le portent ; **l'ordre rapproche les trois emplacements d'actes législatifs** — proposer, voter, s'écarter — et renvoie la parole après eux, sans rien changer au principe de la trame (une suite d'actes, jamais une hiérarchie) ; **« ce qu'il a voté » ne garde que la figure validée sur maquette**, l'axe des années et la note « un membre du gouvernement ne vote pas » partant ensemble — leur raison d'être était de protéger un `0` d'être lu comme une absence individuelle (§2 règle 3), ce qui n'a de sens que sur un axe **continu**, et la vue par période n'affiche aucune période sans vote, donc plus aucun zéro à mal lire ; **ce qui ne part pas** est la moitié qui compte — les quatre branches de vide (quatre causes qu'aucune figure ne remplace), les dénominateurs du repli (§2 règle 7) et les deux phrases de règle, que #711 veut **à côté du chiffre** et dont `test_derniere_lecture_711.py` garde la présence ; elles passent seulement **sous** la figure, trois blocs de texte avant un graphique faisant lire la légende à la place du fait ; **alternative écartée** : garder l'axe des années sous la vue par période — deux axes sur la même population avec deux métriques différentes, quand un lecteur suppose qu'ils comptent la même chose ; **aucun test ne gardait les figures retirées** (zéro occurrence de `parAnnee`, `cp-annee` ou de leurs libellés dans `tests/`), et les 20 classes CSS mortes ont été établies en confrontant chaque nom aux `.jsx`, gabarits `cp-annee--${…}` compris — `cp-gouv-tete/-nom/-periode` survivent, « ce qu'il a proposé » les réutilise, le préfixe ne suffisait pas à décider ; `trame-profil-candidat-328` décrit toujours sept emplacements et **n'est pas modifiée** : une décision se remplace, elle ne se réécrit pas. Suite complète à 4 099, 0 échec.

## Le contexte

[`trame-profil-candidat-328`](trame-profil-candidat-328.md) a posé **sept
emplacements** identiques pour les treize candidats déclarés, dans un ordre
« chronologique et jamais hiérarchique ». Deux d'entre eux ne tiennent plus,
et la vue des votes livrée par
[`votes-par-periode-politique-328`](votes-par-periode-politique-328.md) a rendu
deux figures redondantes.

Ce sont des arbitrages de la propriétaire, rendus le 08/09/2026. Cette décision
consigne ce qu'ils coûtent, ce qu'ils ne coûtent pas, et ce qui a dû être vérifié
avant de couper.

## La décision

### 1. « Les gouvernements dont il a été membre » est retiré

L'emplacement 2 disparaît de la fiche. Avec lui partent le composant
`Gouvernements`, `buildGouvernements` dans l'adaptateur, `loadGouvernements`
dans le chargeur, le titre `voix.titres.gouvernements` dans les trois voix, la
fonction `Barre` et **26 règles CSS** devenues sans emploi.

**Ce que le retrait gagne, mesuré :** la fiche d'un ancien membre du
gouvernement ne télécharge plus ses fiches de gouvernement — jusqu'à quatre
fichiers pour Gabriel Attal. Les autres candidats n'en téléchargeaient aucune,
donc le gain est ciblé, pas général.

**Ce qu'il coûte :** la fiche ne publie plus le bilan collectif des
gouvernements dont la personne fut membre. Ce bilan n'est ni perdu ni
dépublié — les pages `/gouvernements/:id` le portent en entier, et « Les
fonctions exercées » nomme toujours la fonction et sa durée.

### 2. Ce qu'il a **voté** et ses **écarts** passent avant ce qu'il a **dit**

L'ordre devient : les fonctions exercées · ce qu'il a proposé · **ce qu'il a
voté · où il s'est écarté des siens** · ce qu'il a dit · ce qu'on n'a pas pu
lire.

L'ordre reste ce que la trame d'origine exigeait — **une suite d'actes, pas une
hiérarchie de valeur**. Il rapproche simplement les trois emplacements qui
portent des actes législatifs (proposer, voter, s'écarter) et renvoie la parole
après eux.

### 3. « Ce qu'il a voté » ne garde que la figure validée sur maquette

Deux figures partent, et il faut dire ce qu'elles portaient.

**L'axe des années** — une barre par année civile, avec trois situations
(`gouvernement`, `hors_mandat`, `en_mandat`). Il existait pour qu'un `0` ne se
lise pas comme une absence individuelle, ce qu'interdit §2 règle 3. **Cette
protection n'a de sens que sur un axe CONTINU** : elle a été construite parce
que l'axe affichait toutes les années, y compris celles sans vote. La vue par
période n'affiche que les périodes où la personne a voté — il n'y a plus de zéro
à l'écran, donc plus rien à mal lire.

**La note « un membre du gouvernement ne vote pas »** — corollaire du même axe :
elle nommait les années creuses. Le fait lui-même reste porté par « Les
fonctions exercées » et par la frise d'« En bref ».

**Ce qui NE part pas**, et c'est la moitié qui compte :

| Élément | Pourquoi il reste |
| --- | --- |
| Les quatre branches de vide | Elles distinguent quatre causes — index illisible, aucun vote sur l'ensemble, aucune dernière lecture, aucune date exploitable — qu'aucune figure ne remplace (§2 règle 5) |
| Les dénominateurs du repli (`cp-regles`) | « 168 textes tirés de 221 votes sur l'ensemble, parmi 2 906 positions » : un ratio sans son dénominateur n'est pas vérifiable (§2 règle 7) |
| `LAST_READING_RULE.phrase` et `WHOLE_TEXT_VOTE_BOUND.phrase` | #711 les veut **à côté du chiffre**, pas seulement dans la méthodologie — la garde de `test_derniere_lecture_711.py` échoue sinon |

Les deux phrases passent **sous** la figure et non plus au-dessus : trois blocs
de texte avant un graphique font lire la légende à la place du fait.

## L'alternative écartée

**Garder l'axe des années sous la vue par période.** Il aurait donné une
lecture calendaire que le découpage en périodes ne donne pas — les périodes sont
proportionnelles au nombre de textes, pas à la durée. Écartée parce que les deux
axes auraient affiché la même population sous deux métriques différentes, et
qu'un lecteur qui compare deux figures du même bloc suppose qu'elles comptent la
même chose. Le rail de la vue par période porte déjà les dates.

## Ce qui a été vérifié avant de couper

- **Aucun test ne gardait les deux figures retirées.** Recherché sur
  `parAnnee`, `cp-annee`, « voter était impossible », « Un membre du
  gouvernement » : zéro occurrence dans `tests/`. Leur retrait n'a donc été
  arrêté par rien — raison de plus pour écrire ici ce qu'elles protégeaient.
- **Les classes CSS retirées le sont vraiment.** Chaque nom de classe de
  `CandidateProfile.css` a été confronté à l'ensemble des `.jsx`, y compris les
  noms construits par gabarit (`cp-annee--${situation}`). 20 classes mortes,
  26 règles retirées, ~185 lignes.
- **`cp-gouv-tete` / `-nom` / `-periode` survivent** : « ce qu'il a proposé » les
  réutilise. Le préfixe ne suffisait pas à décider.
- **Suite complète à 4 099, 0 échec**, dans un worktree propre.

## Ce qui reste ouvert

`docs/decisions/trame-profil-candidat-328.md` §1 décrit toujours sept
emplacements. Il n'est **pas modifié** : une décision ne se réécrit pas, elle se
remplace (AGENTS.md §8). C'est ce fichier-ci qui fait foi sur le nombre et
l'ordre des emplacements depuis le 08/09/2026.
