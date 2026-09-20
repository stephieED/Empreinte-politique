# La trame du profil candidat : l'institution est une colonne, jamais un chapitre (#328)

`2026-09-01`

> **En bref** — quatrième lot de #324 : la fiche des **13 candidats déclarés** (les 468 `roster_groupe` n'en ont pas) passe de quatre KPI et trois onglets à **sept emplacements identiques pour les treize**, dont l'ordre est chronologique et jamais hiérarchique, et où **aucun total n'additionne deux natures d'acte** ; les règles vivent dans `web/UI_finale/src/utils/profilCandidat.js`, qui **consomme** `styleForPosition`/`emptyListMessage`/`sourceBadge`/`isWholeTextVote`/`WHOLE_TEXT_VOTE_BOUND` du lot 1 et de #672 sans en réécrire une ; **l'issue se trompait sur son propre obstacle** — `positionPolitique` EST collectée, sous le nom `position_dans_hemicycle` sur les mandats `groupe_politique`, avec le `source_url` qu'exige §2 règle 6 (mesuré sur les 541 mandats des 13 : 14 `opposition`, 7 `majorite`, 17 `gouvernement`, 503 nuls, `minoritaire` sur aucun), donc la frise porte vraiment la position déclarée, collée au chiffre qu'elle explique (Jérôme Guedj : **24 déposés / 6 adoptés** en majorité XIVe, **1 968 / 67** en opposition XVIe, **437 / 87** en XVIIe sans position publiée — l'Assemblée n'en déclare aucune pour la législature en cours) ; une **seule** bande, une ligne par rôle rangée par date, teinte = institution et motif = position, aucune étiquette dans la bande (des repères numérotés, repliés sur deux niveaux sous 3,4 % d'écart) ; `siegesElectifs` replie les enregistrements en sièges sur leur date de FIN (**5 → 4** chez Guedj, **5 → 3** chez Attal) sans rien supprimer et le déclare ; le bilan de gouvernement sort de « ce qu'il a proposé » — la place contredisait sa propre phrase — et devient une section d'**ensembles** (Attal : Philippe II 282 textes dont 1 par 49.3, Castex 195/0, Borne 111/**6**, Attal 25/0), les 49.3 **hors** de la répartition colorée (§2 règle 4) ; trois régimes de qualité d'orateur au lieu de deux, parce que 35 / 3 933 chez Jean-Luc Mélenchon n'est ni 3 555 / 3 963 ni 0 / 2 702 ; la direction des questions au gouvernement se déclare par ligne (Guedj **0 / 215** ministérielles — il les a posées ; Attal **723 / 743** — il y a répondu, deux conditions conjointes donnant le même 723) ; l'axe des votes devient **continu** avec trois situations (`gouvernement`, `hors_mandat`, `en_mandat`), parce qu'un axe troué efface les années de gouvernement et qu'un `0` nu publierait le taux de présence qu'interdit §2 règle 3 — et la barre Pour/Contre/Abstention d'Attal, que la maquette suspendait, publie ses **150 votes réels sur l'ensemble d'un texte** (140/7/3) À CÔTÉ du fait établi ; les écarts avec le groupe restent **scrutin par scrutin, jamais totalisés**, avec le nombre de scrutins communs publié (Guedj **814 communs, 2 écarts** ; Attal **1** commun — la maquette annonçait 0 — et 0 écart) ; la voix du texte suit `identite.civilite` (9 / 13 renseignées) et n'invente aucun genre quand elle manque ; effet de bord : `chambreLabel(pivot.chambre)` disparaît, **la condition 1 de retrait du scalaire `chambre` est remplie** et `test_condition_1_de_retrait_etat_global` passe en assertion positive comme sa propre docstring l'annonçait ; le faisceau de la maquette est refait par **comptage d'un champ de la source** au lieu d'un thème écrit à la main (§2 règle 8), avec son seuil de concentration publié (90 %, soit 6 / 34 dossiers pour 2 206 / 2 429 amendements chez Guedj) ; **§2 règle 7 et §6 rangent l'écart individu/groupe en interne seulement, la trame le publie** : la contradiction est nommée et laissée à arbitrage, la section étant retirable d'un bloc.

`2026-09-01` — quatrième lot d'implémentation de #324, posé sur les fondations du
lot 1 (#326) et la sélection de vote de #672. Mesuré sur le dépôt au commit
`9c702c4b` et sur `pivot_data/` au commit de données `245511b4`.

## Contexte

Deux maquettes construites sur données réelles, puis sept itérations, ont produit
la trame arrêtée dans le dernier commentaire de #328
([artifact `e7b32a0c`](https://claude.ai/code/artifact/e7b32a0c-8cb4-4e1f-9dbf-adf92162a7a9)).
Ce lot la transpose en React dans `web/UI_finale`. La fiche qu'il remplace
comptait quatre KPI, trois onglets et douze votes tronqués en silence ; elle
n'affichait ni les 2 429 amendements déposés par Jérôme Guedj comme auteur
principal, ni ses 124 mandats (réduits à une puce), ni un seul de ses 814
scrutins communs avec la fiche de son groupe.

**Deux populations, et une seule a une page.** `meta.provenance ==
"candidat_declare"` marque les **13** profils que `web/` publie ; les **468**
`roster_groupe` alimentent les agrégats et ne sont ni une page ni un lien (#630).
Tous les chiffres de cette décision portent sur les 13.

## Décision

### 1. Sept emplacements, identiques pour les treize, dans le même ordre

Coup d'œil · le parcours · les gouvernements dont la personne a été membre · ce
qu'elle a proposé · ce qu'elle a dit · ce qu'elle a voté · où elle s'est écartée
des siens · ce qu'on n'a pas pu lire.

**Une trame uniformise les emplacements et leur ordre, jamais la quantité.**
Chaque emplacement est rempli à hauteur de ce que la donnée porte, et un
emplacement vide dit **pourquoi** il l'est, via `emptyListMessage` du lot 1 et le
bloc `couverture` du profil — qui distingue `couvert` (une mesure),
`hors_couverture` (la source), `non_collecte` (la collecte) et `fait_etabli` (la
personne).

**Aucun total n'additionne deux natures d'acte.** 49 amendements et 25 textes de
gouvernement ne font pas 74 ; c'est ce qui empêche la comparaison de virer au
classement (§2 règle 1).

### 2. Les règles vivent dans `src/utils/profilCandidat.js`, le composant rend

Même partage que `utils/lecture.js` (#326) et `utils/groupe.js` (#329).
`VOTE_STYLE`, `OUTCOME_COLOR`, `styleForPosition`, `emptyListMessage`,
`sourceBadge`, `formatNumber`, `normalizeLabel`, `isWholeTextVote` et
`WHOLE_TEXT_VOTE_BOUND` sont **importés**, jamais réécrits : c'est exactement la
duplication que le lot 1 a supprimée.

### 3. La position dans l'hémicycle est collectée — contrairement à ce que la trame supposait

L'issue affirme que « `positionPolitique` n'est collectée nulle part, ni dans les
profils ni dans les fiches de groupe », et en tire que **quatre des sept motifs
de la frise sont inaffichables**. C'est faux, et la correction change la fiche :
`candidate_profile.py` reporte `organe.positionPolitique` sur les mandats
`groupe_politique`, sous le nom `position_dans_hemicycle`, avec le `source_url`
du référentiel qu'exige §2 règle 6.

Mesuré sur les **541 mandats des 13 candidats déclarés** : 14 `opposition`,
7 `majorite`, 17 `gouvernement`, 503 non renseignés, **`minoritaire` sur aucun**.
Deux des quatre motifs parlementaires sont donc réellement portés par la donnée ;
`minoritaire` reste déclaré parce que le schéma le connaît
(`KNOWN_POSITIONS_HEMICYCLE`), et le retirer le ferait tomber en silence le jour
où l'un des treize rejoint un groupe minoritaire.

Ce que l'issue dit juste : la position **n'est pas publiée pour la législature en
cours**. Aucun mandat `groupe_politique` de la XVIIe n'en porte, sur aucun des
13. `null` n'est pas une quatrième position, c'est « l'Assemblée ne l'a pas
déclaré » — et le déduire d'un comportement de vote serait le jugement à ne pas
porter.

**La position accompagne le chiffre qu'elle explique, sur la même ligne.**
Jérôme Guedj : 24 amendements déposés et 6 adoptés comme député **majoritaire**
(XIVe, SRC), 1 968 déposés et 67 adoptés comme député d'**opposition** (XVIe,
SOC), 437 et 87 en XVIIe sans position déclarée. Sans la mention, le lecteur lit
une incompétence là où il y a une fonction.

### 4. Une seule frise, une ligne par rôle, rangée par date

Pas deux couloirs empilés : un couloir au-dessus d'un autre **est** une
hiérarchie, au sens littéral. `rolesDuParcours` produit une ligne par siège
électif, par portefeuille gouvernemental et par mission, triées par date de
début, quelle que soit l'institution. Le chevauchement — Gabriel Attal est élu
député 33 jours alors qu'il est ministre délégué — est résolu par un rangement
glouton, et **la légende dit que c'en est un**.

**La teinte porte l'institution, le motif porte la position.** Ardoise `#3F5166`
pour le Parlement, terre `#8A6B4C` pour le gouvernement, jaune signal `#DFFF00`
pour le chef du gouvernement (aplat, jamais du texte : contraste 1,05:1 sur fond
clair), contour terre tireté pour la mission. À l'intérieur du Parlement la
teinte ne change pas : la question « quelle couleur vaut mieux » ne se pose
jamais. Le vert et le rouge restent réservés aux positions de vote, et chaque
situation reste distinguable en niveaux de gris.

**La bande ne porte aucun texte.** Des repères numérotés la surmontent, repliés
sur un second niveau quand deux débuts sont à moins de 3,4 % l'un de l'autre ; la
liste dessous porte les mêmes numéros et les intitulés complets. Le motif est un
`::after` en `inset: 0`, ce qui est sans risque **parce que** la bande n'a pas
d'étiquette à recouvrir — c'est le défaut corrigé en chemin sur la maquette.

### 5. Un siège, pas un enregistrement

La fusion additive a conservé, pour un même siège, deux enregistrements : un
ancien sans `chambre`, un récent avec (#492/#640). Guedj porte **5
enregistrements pour 4 sièges**, Attal **5 pour 3**. `siegesElectifs` les
regroupe sur leur **date de fin** — deux mandats qui se chevauchent et s'arrêtent
le même jour sont le même siège — jamais sur la seule législature, ce que #640
interdit. Rien n'est supprimé, l'écart est **déclaré** en section 7.

### 6. Le bilan d'un gouvernement est une section à part, avant les actes personnels

La maquette d'août rangeait ce bloc dans « ce qu'il a proposé » tout en portant
la phrase « ces textes engagent le gouvernement, pas la personne » : la place
contredisait la phrase, et la place gagne. En **ensembles**, jamais en liste
attribuée — sauf pour le gouvernement dont la personne était le chef, où nommer
les textes n'attribue rien qu'elle n'ait signé.

Les quatre gouvernements de Gabriel Attal, vérifiés fiche par fiche : Philippe II
282 textes (1 par 49.3), Castex 195 (0), Borne 111 (**6**), Attal 25 (0).
**Les 49.3 sortent de la répartition colorée** : un texte adopté sans vote est un
fait de procédure, jamais une issue de scrutin (§2 règle 4). Ils sont un segment
hachuré sans teinte et une phrase en toutes lettres.

Un gouvernement sans texte rattaché (Fillon II et III, 0 texte chacun) le dit
comme un vide de collecte, pas comme un bilan.

### 7. Ce qui est publié, et ce qui est écarté avec sa raison

`textes_portes` en deçà de l'examen en commission n'est pas publié (§6), **et la
page dit combien sont écartés et pourquoi** : 3 des 5 textes de Guedj — 2 déposés
sans jamais être examinés, 1 sans stade procédural.

`sort: null` sur un amendement n'est pas un sort : il s'affiche « sort non
publié », sans teinte, jamais confondu avec « rejeté » (§2 règle 5). Mesuré chez
Guedj : 659 des 1 968 amendements de la XVIe.

Les irrecevabilités portent leur **règle**, pas un compte d'échecs : 246 au titre
de l'article 40, 161 au titre de l'article 45, chacune accompagnée de la phrase
qui dit ce que l'article interdit.

### 8. Deux régimes de qualité d'orateur, et un troisième état

`fonction` est publiée par la source sur 3 555 des 3 963 interventions d'Attal,
sur **0** des 2 702 de Guedj, et sur **35** des 3 933 de Jean-Luc Mélenchon. Deux
états auraient rangé Mélenchon avec Attal sur 0,9 % de couverture : la page
publie donc trois états — `source` (tout), `partiel` (les deux nombres, nommés),
`derive` (rien, et l'inférence est déclarée comme la nôtre).

**Un même champ recouvre deux actes opposés.** `question_gouvernement` compte les
questions posées et celles auxquelles un ministre répond : Guedj 215 dont **0**
avec une qualité ministérielle — il les a posées ; Attal 743 dont **723** — il y
a répondu. La détection exige **deux** conditions, la qualité publiée par la
source **et** une date tombant dans une période de gouvernement ; les deux règles
donnent 723 séparément, et les conjoindre empêche qu'un `fonction: "rapporteur"`
(204 chez Attal) compte un jour pour une qualité ministérielle.

### 9. L'axe des votes est continu, et chaque année dit sa situation

Un axe troué — 2018 puis 2022 chez Attal — laisse croire que les années
intermédiaires n'existent pas, alors qu'elles portent le fait le plus important
de sa fiche. Mais un `0` nu serait pire. Trois situations, jamais confondues :
`gouvernement` (voter était impossible), `hors_mandat` (aucun mandat cette
année-là — publier `0` sans le dire se lirait comme une absence, c'est-à-dire le
taux de présence qu'interdit §2 règle 3), `en_mandat` (un zéro mesuré).

**Aucun ratio de participation.** Un dénominateur « scrutins où la personne
aurait pu voter » est un taux d'assiduité individuel.

La maquette suspendait la barre Pour/Contre/Abstention chez Attal au motif qu'un
membre du gouvernement ne vote pas. Elle taisait ainsi **150 votes réels sur
l'ensemble d'un texte** (140 pour, 7 contre, 3 abstention). La page publie les
deux : les 150 votes, et le fait établi.

### 10. Les écarts, scrutin par scrutin, jamais totalisés

« A voté contre son groupe N fois » serait une note. La page publie la liste — sa
position et celle du groupe, côte à côte, sur un scrutin nommé, daté et sourcé —
et **jamais un total**. Restreint aux votes sur l'ensemble d'un texte : sur un
article ou un amendement, la position majoritaire d'un groupe se déplace pour des
raisons de négociation que le corpus ne porte pas.

Le nombre de scrutins **communs** est publié, sans quoi une section vide se lit
« il n'a jamais divergé » alors qu'elle dit « rien n'est comparable ». Guedj :
**814 communs, 2 écarts** (proposition de loi grand âge et autonomie,
19/03/2024 ; projet de loi d'orientation et de programmation de la justice,
18/07/2023 — contre, quand son groupe s'abstient).

### 11. La voix du texte suit la source, ou n'affirme rien

La trame écrit « ce qu'**il** a proposé ». Appliquée aux treize, la formule se
trompe sur quatre. `identite.civilite` vient d'AMO30 et n'est jamais inférée d'un
prénom (#659) : elle est renseignée sur **9 des 13** (`M.` ×7, `Mme` ×2).
Absente, la page n'invente pas de genre — elle écrit « ce que **cette personne** a
proposé ». Un vide reste un vide, y compris dans la grammaire.

## Ce que ce lot a fermé sans le chercher

**La condition 1 de retrait du scalaire `chambre` est remplie.**
`pivotAdapter.chambreLabel(pivot.chambre, actif)` était le dernier consommateur
du champ profil, côté pipeline comme côté interface, et
`tests/test_garde_fou_chambre.py::test_condition_1_de_retrait_etat_global`
annonçait dans sa docstring qu'il échouerait le jour de sa disparition. Il a
échoué. La fiche ne publie plus une chambre de profil mais **le rôle de chaque
siège**, lu sur `mandats[].chambre` (#492) : sur un profil bicaméral, les deux
chambres apparaissent, chacune à sa date. Le test est retourné en assertion
positive. Retirer le champ reste hors de ce lot : la condition 2 se lit sur un
run réel (l'avertissement « chambres du profil non corroborée » absent du
corpus), et le scalaire part alors avec la branche de repli de `lire_chambres()`.

## Alternatives écartées

| Écartée | Pourquoi |
| --- | --- |
| Reprendre le faisceau de la maquette tel quel (« 1 386 interventions sur la sécurité sociale, le grand âge ou la fin de vie ») | Ce thème n'existe dans aucun champ du corpus : l'agréger fabriquerait une catégorie éditoriale (§2 règle 8). Chaque trace est désormais **dérivée par comptage d'un champ de la source** — sujet le plus fréquent, concentration des dossiers, commission la plus fréquente. |
| Une concentration à `k` fixe (« 6 dossiers ») | Un `k` choisi par l'auteur présenté comme une mesure. La règle est publiée : le plus petit `k` atteignant **90 %** des dépôts. Elle redonne 6 / 34 dossiers pour 2 206 / 2 429 amendements chez Guedj. |
| Regrouper les sorts d'amendement en « adopté » et « sort non publié », comme la maquette le fait pour Guedj | La v2 reproche précisément à la v1 d'avoir « réduit les sept sorts à deux ». Les sept sont publiés, mesurés sur l'index partagé. |
| Ajouter un jeu de jetons de thème sombre | Le site est en thème clair déclaré (`index.css`, `color-scheme: light`). Le piège des trois états (`:root`, media query, `[data-theme]`) est propre au lecteur d'artifact et ne s'applique pas ici. |
| Monter un harnais de test JS | `package.json` n'expose que `dev`, `build`, `lint`. Hors lot, et nommé comme tel — les garde-fous restent `oxlint`, `vite build` et le rendu vérifié hors dépôt. |

## Ce qui reste ouvert

- **§2 règle 7 dit « les écarts individu/groupe sont un contrôle interne, jamais
  publics », et §6 les range en « interne seulement ».** La section 6 de la trame
  les publie, scrutin par scrutin et sans total. La règle et la trame se
  contredisent : l'arbitrage appartient à la propriétaire, et la section est
  écrite de façon à être retirable d'un bloc.
- `suspendu_pour_fonction_gouvernementale` n'est renseigné sur aucun mandat
  électif d'aucun des 13 : un mandat interrompu par une nomination reste
  indiscernable d'un mandat arrivé à terme. La page le **déclare**, calculé sur
  le profil affiché et non écrit en dur.
- `textes_portes` mêle projets et propositions de loi sous un même `role: auteur`
  (13 des 34 textes d'Attal) ; seul l'intitulé officiel les distingue, et la page
  le dit.
- Aucun runner JS : les mesures de cette décision ont été refaites en Python sur
  `pivot_data/` et en Node sur l'adaptateur, pas en test versionné.
