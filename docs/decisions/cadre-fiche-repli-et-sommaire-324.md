<a id="cadre-fiche-repli-et-sommaire-324"></a>

# L'en-tête rend 301 px, et un sommaire prend la marge que personne n'occupait (#324) (2026-09-08)

`2026-09-08`

> **En bref** — l'en-tête restait collé **en entier** : marque plus trois barres, **357 px identiques sur tous les supports** (45 % de la hauteur d'un 1 280 × 800, 42 % d'un mobile), pour une fiche de **7 968 px** — neuf écrans avec un demi-écran utile ; au-delà de 180 px de défilement l'en-tête se réduit à **56 px**, soit **301 px rendus au contenu sur les cinq supports, mobile compris** (contenu au premier écran 371 → 672 px en 1 280 × 800) ; l'ordre des listes devient **candidats, groupes, gouvernements** — une fiche s'atteint par un nom ; un **sommaire de sections à gauche** tient en place, marque la section lue et sert de raccourci — à gauche parce qu'un sommaire s'y lit *avant* le contenu, et il **lit la page** (`[data-section]`) au lieu de recevoir une liste, donc il sert les trois types de fiche et accueille une section neuve sans rien savoir d'elle, l'ancre venant du **numéro** et jamais du titre (qui change avec la voix du texte) ; **le seuil de 1 440 px est une mesure, pas un goût** — la question « comment ça rend sur l'ordinateur de monsieur tout le monde » a changé la réponse : Statcounter France août 2026, 1 440 px couvre **39 % du parc de bureau nommé et 21 % de toutes les visites** contre 13 % à 1 600 px, et **un seuil à 1 600 px aurait exclu les écrans 1 600 × 900 eux-mêmes**, dont la fenêtre fait 1 585 px — frontière posée en pensant à des écrans, réglée sur des fenêtres ; le sommaire **ne coûte rien au contenu**, qui reste à 1 100 px partout ; **trois défauts trouvés en mesurant** — le sommaire restait vide (monté avant la fiche, dont les données arrivent en réseau : `MutationObserver`), retirer son `<nav>` faisait glisser le contenu dans sa colonne de 204 px, et surtout **vérifier un attribut n'est pas vérifier son effet** : une mesure lisait `element.hidden` et déclarait les barres masquées alors que `display: flex` l'emporte sur le `[hidden]` du navigateur — seule la capture l'a montré ; **alternative écartée** : le repli seul, sans sommaire, qui règle le vrai problème mais laisse une page de neuf écrans sans repère alors que le sommaire ne coûte rien. 12 tests neufs, suite complète à 4 147, 0 échec.

## Le contexte, mesuré

Mesuré le 08/09/2026 sur la fiche de Jérôme Guedj, build de production :

| Support | En-tête collant | de la hauteur | Marges latérales |
| --- | ---: | ---: | ---: |
| 1920 × 1080 | 357 px | 33 % | 43 % |
| 1440 × 900 | 357 px | 40 % | 24 % |
| **1280 × 800** | 357 px | **45 %** | 14 % |
| 834 × 1112 | 357 px | 32 % | 0 % |
| **390 × 844** | 357 px | **42 %** | 0 % |

357 px de marque et de barres de sélection, **identiques sur tous les
supports** — un en-tête qui ne s'adapte à rien. Et la fiche fait **7 968 px** sur
ordinateur, **12 122 px** sur mobile : neuf écrans parcourus avec un demi-écran
utile, sans rien qui dise où l'on en est.

## La décision

### 1. Les barres défilent, une barre compacte prend le relais

Au-delà de 180 px de défilement, l'en-tête se réduit à **56 px** : la marque, et
un bouton qui ramène les listes. **357 → 56, soit 301 px rendus au contenu.**

C'est la moitié de la réforme qui vaut **pour tout le monde** — les cinq
supports, mobile compris. Sur un 1 280 × 800, le contenu visible au premier
écran passe de 371 à 672 px.

Les listes rappelées se collent sous la barre compacte : on vient de les
demander, elles doivent rester sous la main. Elles se referment d'elles-mêmes
quand on remonte, et quand on change de fiche.

### 2. L'ordre des listes : candidats, groupes, gouvernements

Une fiche s'atteint par un **nom** ; les deux autres listes sont des entrées de
contexte, et elles descendent d'autant.

### 3. Un sommaire des sections, à gauche, au-delà de 1 440 px

Il tient en place pendant que la page défile, marque la section en cours de
lecture, et sert de raccourci. **À gauche** : un lecteur commence par la gauche,
et un sommaire s'y lit *avant* le contenu, comme une table des matières. À
droite, il devient une note de marge.

Il **lit la page** au lieu de recevoir une liste — `[data-section]` sur chaque
section — donc il sert les trois types de fiche sans qu'aucune ait à le
connaître, et une section ajoutée y apparaît d'elle-même. L'ancre est dérivée du
**numéro**, jamais du titre : un titre change avec la voix du texte (« ce qu'il »
/ « ce qu'elle »), un lien partagé ne doit pas.

## Le seuil de 1 440 px est une mesure, pas un goût

C'est la question que la propriétaire a posée, et elle a changé la réponse :
« comment ça va rendre sur l'ordinateur de monsieur tout le monde ? »

Parc France, Statcounter, août 2026. La fenêtre vaut l'écran moins la barre de
défilement (~15 px) — hypothèse **généreuse**, une fenêtre non maximisée est plus
étroite encore.

| Écran | du parc bureau | de toutes les visites | Fenêtre | Sommaire |
| --- | ---: | ---: | ---: | :---: |
| 1920 × 1080 | 25,0 % | 13,2 % | 1 905 px | oui |
| 1536 × 864 | 9,2 % | 4,9 % | 1 521 px | oui |
| 1600 × 900 | 4,8 % | 2,5 % | 1 585 px | oui |
| 1366 × 768 | 5,0 % | 2,7 % | 1 351 px | non |
| 1280 × 720 | 5,0 % | 2,7 % | 1 265 px | non |

Le bureau fait **52,98 %** des visites françaises, le mobile **44,59 %** : une
part de parc se convertit en part de visites en la multipliant par 0,53.

| Seuil | Couverture |
| --- | --- |
| 1 600 px | 25 % du bureau nommé · **13 % des visites** |
| **1 440 px — retenu** | 39 % · **21 % des visites** |
| 1 280 px | 44 % · 23 %, mais 30 px de marge restante |

**Un seuil à 1 600 px aurait exclu les écrans 1 600 × 900 eux-mêmes**, dont la
fenêtre fait 1 585 px : quinze pixels sous la barre. C'est une frontière qu'on
pose en pensant à des écrans et qui se règle sur des fenêtres.

**Le sommaire ne coûte rien au contenu** : il prend 204 px sur la marge, et le
contenu reste à 1 100 px, seuil franchi ou non.

Ce que ces chiffres disent du fond : **le sommaire reste un supplément pour un
cinquième des visites.** Ce qui compte est le repli de l'en-tête, qui vaut sur
100 % des supports.

## Deux défauts trouvés en mesurant, et ce qu'ils enseignent

**Le sommaire restait vide.** Il est monté *avant* la fiche, dont les données
arrivent en réseau : une lecture unique au montage ne trouvait rien, et le
sommaire ne se remplissait jamais. Corrigé par un `MutationObserver`.

**Vérifier un attribut n'est pas vérifier son effet.** La première mesure lisait
`element.hidden` et déclarait les barres masquées ; elles restaient à l'écran,
parce que `display: flex` l'emporte sur le `[hidden] { display: none }` de la
feuille de l'agent utilisateur. **Seule la capture l'a montré.** La mesure
vérifie désormais le `display` calculé.

Un troisième, corrigé pour la même raison : retirer le `<nav>` du DOM quand il
n'a rien à montrer faisait glisser le contenu dans la colonne de 204 px. Il est
donc toujours rendu, vide s'il le faut.

## L'alternative écartée

**Le cadre A seul** — repli de l'en-tête, sans sommaire. Il règle le vrai
problème, celui qui vaut sur tous les supports, et c'était ma recommandation
avant de mesurer le parc. Écarté parce qu'une page de neuf écrans sans aucun
repère de position reste une page où l'on se perd, et parce que le sommaire ne
coûte **rien** au contenu : il n'y avait pas de compromis à arbitrer, seulement
un seuil à poser au bon endroit.
