<a id="filtre-par-intitule-fiche-candidat-979"></a>

# Un mot filtre la fiche candidat, et la fiche se recalcule sur ce qu'il porte (#979) (2026-09-17)

`2026-09-17`

> **En bref** — Une barre en tête de la fiche candidat filtre textes, votes,
> amendements et interventions par un mot de leur intitulé (et du verbatim, pour une intervention). Le filtre réduit le
> profil avant le calcul : figures et listes suivent ensemble. « En bref », les
> fonctions et la couverture se retirent, chaque figure porte le mot, les listes
> se déplient, et un mot sans résultat a son propre message.

## Contexte

#979 partait d'une recherche de NOMS. La propriétaire a précisé le 17/09/2026
qu'elle cherche des INTITULÉS, en deux temps : un filtre sur une fiche, puis une
recherche « quelle fiche porte ce mot ? ». Ce lot est le premier temps, sur la
fiche candidat seule ; les fiches de groupe et de gouvernement n'ont pas été
maquettées.

Tout ce qui suit a été tranché sur maquette, sur la fiche d'Emmanuel Maurel,
avec « finances », « énergie » et « numérique ».

## Décision

| Point | Retenu | Pourquoi |
| --- | --- | --- |
| Où | **Une seule barre, en tête de fiche** | Un champ par liste faisait retaper le mot trois fois |
| Les figures des sections 2 à 5 | **Recalculées** : le filtre réduit le profil pivot (`filtrerProfil`), puis la fiche est reconstruite par les règles habituelles | Une figure de toute la carrière au-dessus d'une liste filtrée montrait deux choses différentes |
| « En bref », « Les fonctions exercées », « Ce qu'on n'a pas pu lire » | **Retirées tant qu'un mot est tapé** | Recalculé sur « finances », « En bref » publiait « 259 amendements sur 4 dossiers ». Une section non filtrée entre des sections filtrées se lirait comme filtrée. La couverture recalculée décrirait les lacunes du filtre, pas celles de la collecte |
| Le rappel du mot | **Une étiquette en tête de chaque figure** (« Contenant « … » », la même partout) | Les totaux recalculés sont ce qui circule en capture d'écran ; une ligne sous le titre de section sort du cadre de la capture |
| Les listes | **Dépliées sans clic, sous un mot seulement** : textes portés, tous les dossiers amendés, interventions de toutes les périodes et de tous les sujets | Sans mot, Maurel compte 1 569 interventions et 2 944 amendements ; sous « finances », 225 et 4 dossiers |
| « Ce qu'il a voté » | **Cumule ses périodes sous un mot** (`periodeCumulee`) | Exception assumée à la règle qui refuse le cumul hors filtre (il reformerait un total de carrière) : la liste portait toutes les périodes, la figure une seule |
| Un mot sans résultat | **La section reste, avec un message du filtre** (`VideDuFiltre`) | Sans lui, la fiche affichait « Non collecté » et « La source ne publie pas cette période » : faux, la collecte n'est pas vide (§2 règle 5). Une section retirée se lirait comme une section qui n'existe pas pour la personne |
| La langue | **Sans casse ni accents, sans traduction.** Le message des amendements dit que les intitulés européens sont en anglais | 0 des 170 dossiers amendés européens de Maurel porte un intitulé français (détection approchée, 17/09/2026). Traduire serait publier un intitulé que la source n'a pas écrit (§2 règle 2) |
| La barre | **« Rechercher sur cette page »**, retenu par la propriétaire à la place de « Filtrer la fiche par un mot des intitulés » | Plus court, et le geste est connu |
| Les interventions | **Cherchées dans le sujet OU le verbatim**, le mot surligné dans le verbatim (`segmentsSurlignes`) | « Rechercher sur cette page » promet ce qui est sur la page. Sur le sujet seul, « nucléaire » ne trouvait aucune des 5 interventions de Maurel qui en parlent (1 569 interventions, 17/09/2026) |
| Le compte de résultats | **Pas de compteur à part** | Les figures recalculées portent déjà leurs totaux |

Les intitulés comparés sont ceux que la fiche affiche : `titreDuTexteVote` pour
un vote (l'intitulé de source pour un vote européen non rattaché), le dossier de
l'index par législature ou de `dossiers_europeens.json` pour un amendement,
`cheminDuPoint` et le verbatim pour une intervention. `mandats` n'est jamais filtré.

Le mot vit dans l'adresse (`?mot=`) ; le chargement se fait une fois
(`chargerSourcesCandidat`), le calcul à chaque mot (`vueCandidat`), sur la valeur
différée de la saisie. Mesuré en développement le 17/09/2026 : 109 à 307 ms (verbatims compris) par
recalcul sur Ruffin, Mélenchon, Faure et Maurel.

**Défaut corrigé en chemin.** Sous trois flux, la cascade des textes portés
n'est pas dessinée et annonce « la liste ci-dessous les porte tous » ; la liste
n'apparaissait qu'après un clic dans le diagramme absent. `cascadeDessinee` le
détecte, et la liste montre alors tous les textes — avec ou sans mot.

## Limite connue

Les votes européens non rattachés à un scrutin ne sont pas affichés sur la
fiche (3 598 chez Maurel), filtre ou pas. Le filtre les trouve sur leur
intitulé de source : le message « aucun vote affiché » en donne le nombre, il ne
les montre pas.

## Alternatives écartées

- **Filtrer les listes seulement, figures intactes** : la figure ne correspondait
  plus à la liste placée dessous.
- **Retirer toutes les figures sous un mot** (une liste de résultats par
  section) : recommandé par l'agent, écarté par la propriétaire au profit des
  figures recalculées.
- **Un champ par liste**, ou un champ en tête qui ne filtrerait que les votes
  de la période affichée.
- **Un sujet vide retiré et nommé sous la barre** : plus court, mais une section
  absente se lit comme une section qui n'existe pas.
- **Une étiquette par nature de recherche** (« Intitulés contenant » sur les
  figures, « Sujets ou propos contenant » sur les interventions) : plus précise,
  recommandée par l'agent ; la propriétaire a retenu un seul libellé partout.
