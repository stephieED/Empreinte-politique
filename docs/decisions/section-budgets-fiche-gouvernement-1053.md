<a id="section-budgets-fiche-gouvernement-1053"></a>

# La fiche de gouvernement montre les budgets qu'il a fait voter, en deux colonnes et une cascade (#1053) (2026-10-14)

`2026-10-14`

> **En bref** — Une sixième section, « Les budgets que ce gouvernement a fait voter », sur les huit fiches de gouvernement qui ont fait voter au moins une loi de finances. Pour l'État : ce qu'il reçoit et ce qu'il dépense par mission, en deux colonnes à la même échelle que l'emprunt égalise, et la cascade des recettes et des dépenses année par année jusqu'au solde. Pour la sécurité sociale : les mêmes deux colonnes. `sync-data` découpe `pivot_data/budgets_gouvernements.json` en un fichier par gouvernement ; sans ce fichier, la section ne s'affiche nulle part.

## Le contexte

La donnée vient de Backend (sa décision sur #1053, sur la branche
`backend/budget-fiche-gouvernement-1053`, pas encore fusionnée le 14/10/2026) :
une année revient au gouvernement sous lequel sa loi de finances initiale a été
promulguée, et seuls les montants encaissés et dépensés sont repris. La forme a
été arrêtée en maquette avec la propriétaire le 13/10/2026, version 68
(https://claude.ai/artifact/8qozzLMHSUccspo5d9aL6R) ; la section la reprend, ses
formes écartées comprises comme écartées : schémas de flux, carrés, listes de
barres, courbes mensuelles, montants votés.

## La décision

- **La section n'existe que pour un gouvernement qui a fait voter un budget.**
  Neuf fiches sur dix-sept n'en ont pas ; « Ce qu'on n'a pas pu lire » garde la
  dernière place, numérotée 07 ou 06.
- **Les deux colonnes ont la même hauteur, et c'est une égalité comptable** :
  ce que l'État dépense de plus qu'il ne reçoit est ce qu'il emprunte.
  « Emprunt » complète la colonne de gauche, hachuré ; le solde, lui, est dans
  la cascade.
- **Dix lignes, puis « Autres ».** Les dix missions les plus élevées et les deux
  reversements, puis « Autres missions (n) » et « Non réparti par mission,
  comptes à part » — les dégrèvements d'impôts locaux et le solde négatif des
  comptes tenus à part. Pour la sécurité sociale, dix régimes puis « Autres
  régimes (n) » et les frais de gestion.
- **Une année que la figure ne peut pas prendre est nommée, jamais additionnée
  à moitié** (§2 règle 5) : sans ses missions — avant 2023, ou l'exercice en
  cours — elle reste dans la cascade, mais sort des deux colonnes, et une phrase
  le dit. De même pour une année sans comptes sociaux.
- **« Pour 100 € » arrondit au plus fort reste**, de sorte que chaque colonne
  fasse son total ; le total écrit en tête est la somme des lignes affichées.
- **En 2024, la source donne les trois cotisations sur une seule ligne** :
  sans la ligne des salariés, elle ne dit plus « employeurs », et la figure
  écrit « Cotisations non séparées (2024) ».
- **Retouches de la relecture à l'écran du 14/10/2026**, à ne pas rouvrir :
  la cascade n'a que deux barres par année, recettes et dépenses, le reversé
  aux collectivités et à l'Union européenne fondu dans les dépenses (son
  détail reste au survol) ; son encadré ne porte plus le solde cumulé ; bleu
  pour les recettes, orange pour les dépenses, choisi parmi cinq jeux, et
  repris dans les deux colonnes en **deux nuances proches alternées**, qui
  séparent deux postes voisins sans rien dire d'eux ; « Autres missions » est
  en couleur, « Autres régimes » et les frais de gestion restent gris.
- **Une bulle au survol et au toucher**, sur la barre comme sur son libellé :
  le montant du poste, puis ce qui le compose — les programmes d'une mission
  (champ `programmes` livré par Backend le 14/10/2026), les missions ou les
  régimes regroupés sous « Autres ».
- **Les étiquettes de blocs fins s'écartent autour de leur groupe**, et un trait
  coudé relie celle qui ne peut pas rester en face de son bloc.
- **Le calcul est dans `utils/budgetsGouvernement.js`**, sans import, testé par
  `node` ; le composant dessine.

## Ce qui reste ouvert

- La bulle reprend le texte de la maquette, que la propriétaire n'a pas relu, et
  n'a pas de lien « Lire la méthode » : la méthodologie n'a pas encore d'entrée
  pour la section.
- Le bleu et l'orange n'ont pas été mesurés contre les couleurs déjà prises
  par le site (DESIGN_SYSTEM) ; le bleu est proche de celui du Parlement
  européen.
- La source ne publie aucune recette venue de l'Union européenne, quand elle
  isole la contribution qui lui est versée : la méthodologie devra le dire.
- Les tests portent sur des exercices écrits à la main, dans la forme du
  fichier : il n'est pas encore sur `main`.

## L'alternative écartée

Lire `budgets_gouvernements.json` entier depuis la fiche : 51 ko pour en
afficher une entrée. Le découpage par gouvernement suit celui des actes
(`<id>.actes.json`), et le manifeste dit d'avance quelles fiches ont la section.
