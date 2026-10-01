<a id="retour-ux-sur-les-fiches-candidat"></a>

# Le retour d'ergonomie sur les fiches candidat : ce qu'il tranche, et ce qu'il ne peut pas trancher (2026-10-01)

`2026-10-01`

> **En bref** — Un retour extérieur sur l'ergonomie des fiches candidat, remis à
> la propriétaire le 01/10/2026, a ouvert la revue des trois types de fiche. Il
> porte quatre constats et trois « arbitrages prioritaires ».
> **Deux de ces trois heurtaient des règles déjà posées** — masquer les blocs
> vides, et reléguer les avertissements dans une modale. Le premier a pourtant
> raison sur le fond, et c'est la propriétaire qui a montré par où : l'absence
> est **déjà** déclarée dans « Ce qu'on n'a pas pu lire », donc la répéter six
> fois est une redondance, pas une garantie. Ce fichier consigne le retour, ce
> que la mesure en confirme ou en infirme, l'arbitrage rendu, et **ce qui reste
> ouvert avec son interdit**.

## Pourquoi ce fichier existe

Le retour est la **matière de départ** d'un chantier qui durera plusieurs lots.
Sans trace, chacun de ses points se représentera comme une idée neuve — et deux
d'entre eux appellent une réponse qui contredit `AGENTS.md` §2. Un retour
d'ergonomie transmis sans ses limites se lit comme une liste de corrections à
appliquer.

## Ce que le retour dit

| # | Constat | Vérifié ? |
| --- | --- | --- |
| 1 | « Le syndrome de la page vide à 2 700 px » — scroller sur une fiche qui ne porte que des « Rien à afficher ». *« Sur un candidat sans mandat, la fiche devrait faire 400 px »* | **Oui.** Anasse Kazib : 6 sections, **2 725 px**, dont **996 px** de cartes d'absence sur quatre sections, et **608 px** pour « Ce qu'on n'a pas pu lire » — le seul bloc qui dise la cause, **en dernier** |
| 2 | La surcharge cognitive de la fiche François Ruffin, « le bruit des données » | **Oui pour la mesure** : 7 644 px repliée, 8 534 dépliée. Le jugement sur la saturation n'est pas mesurable |
| 3 | Les poignées de dépliage rallongent la page sans ancrage visuel | **Oui** : +890 px au clic sur Ruffin. L'effet sur le repérage n'a pas été mesuré |
| 4 | Le Sankey des textes portés est illisible pour le grand public, et une barre courte en fin de flux « induit visuellement une notion d'échec » | **Non mesuré.** Le risque est sérieux et touche §2 règle 1 |
| 5 | Une profusion de « disclaimers » donne un ton méta-justificatif | **Oui** : `CandidateProfile.jsx` déclare **33 emplacements** de texte explicatif — 14 pieds de section, 11 critères, 8 renvois. Tous ne s'affichent pas ensemble |
| 6 | La fiche candidat reste un « super-CV » ultra-détaillé, ce qui neutralise le recentrage sur les institutions | **Non mesurable.** C'est une question de positionnement, pas de forme |

## Les trois « arbitrages prioritaires », et ce qui s'y oppose

| Proposition | Verdict |
| --- | --- |
| **Masquer les blocs vides** au lieu d'afficher « Rien à signaler » | **Écarté sous cette forme, retenu sous une autre.** Masquer rend l'absence invisible : le lecteur ne distingue plus « rien collecté » de « rien à montrer », ce que §2 règle 5 refuse. Mais le retour a raison sur le fond — voir l'arbitrage ci-dessous |
| **Simplifier ou doubler les dataviz complexes** | **Ouvert.** Rien ne s'y oppose, et le risque nommé est réel |
| **Regrouper méthodologie et limites dans une modale ou une page dédiée** | **Écarté.** La méthodologie a déjà absorbé les explications, et six notices ont été retirées une à une sous les figures. Une modale éloigne la limite du fait qu'elle qualifie (§2 règle 2) et tient mal sur mobile. La **condensation**, elle, reste ouverte |

## L'arbitrage rendu : déclarer une fois, là où ça s'explique

**Ce n'est pas la ligne éditoriale qui bloquait, c'est ma lecture d'elle.** La
propriétaire l'a posé ainsi : « *les absences sont déclarées dans « Ce qu'on n'a
pas pu lire ». Donc il ne s'agit pas de rendre invisible mais de concentrer
l'information là où elle doit être tout en évitant les redondances* ».

La section 6 énumère déjà les cinq listes collectées, chacune avec sa cause, sa
borne et son compte à zéro. Les quatre cartes qui la précédaient disaient donc
une quatrième fois ce qu'elle dit une fois, **et mieux**.

**Quatre formes ont été rendues sur la vraie fiche**, sans modifier une ligne de
code — CSS et DOM injectés dans la page servie, puis capturés :

| | | Hauteur |
| --- | --- | ---: |
| Actuel | six sections pleines, l'explication en dernier | 2 725 px |
| A | les sections vides quittent le corps, le sommaire les garde en grisé | 1 552 px |
| B | A, et l'explication remonte en tête | 1 552 px |
| **C — retenue** | **chaque section vide tombe à une ligne qui renvoie à la cause** | 2 109 px |

C est la moins radicale des trois, et c'est **ce qui l'a fait retenir** : les six
sections gardent leur place et leur ordre, l'absence reste dite à chacune, et
elle est dite une fois complètement, en section 6.

Ce que la forme publie, et pourquoi chaque mot :

- « **Aucune donnée trouvée. Pourquoi →** » — ses mots. Une première version
  disait « collectée » ; elle l'a corrigée après qu'il lui a été signalé que le
  mot déplaçait l'absence de la source vers nous.
- « **Liste non interrogée.** » pour la cause `non_collecte`, et c'est §2
  règle 5 : « trouvée » affirme une recherche, qui sur cette cause n'a pas eu
  lieu. Deux causes, deux phrases.
- « **Rien à comparer. Pourquoi →** » pour les écarts avec le groupe, quand
  aucune fiche de groupe n'est publiée.
- **Un seul « Pourquoi → », une seule destination** — la section 6. Qu'il mène
  tantôt en bas de page, tantôt sur une autre page, c'est le lecteur qui paie.
  C'est elle qui l'a rectifié : la méthodologie avait été proposée.
- **Les écarts ne sont pas une sixième ligne du tableau** : ni borne, ni compte,
  ce n'est pas une liste collectée. Leur cause a sa mention sous le tableau, et
  elle porte la nuance sans laquelle le vide se lirait « il n'a jamais divergé ».
- **Rien à montrer, donc rien à expliquer** : le pied et les critères d'une
  section vide tombent, ainsi que le renvoi de méthodologie de la section 2.

**Mesuré après, sur l'application construite** : Anasse Kazib passe de 2 725 à
**2 017 px** (−26 %), cinq mentions, aucune carte, zéro pied, zéro critère.
**François Ruffin ne bouge pas** : 7 650 px, ses deux pieds et ses deux critères
intacts. La fiche de lignée garde la carte pleine — la répétition qui a motivé la
forme courte n'existe pas là-bas.

## Ce qui reste ouvert, et ce qu'il ne faut PAS en faire

**Le Sankey des textes portés.** Le risque nommé est qu'une barre courte en fin
de flux se lise comme un échec, ce que §2 règle 1 refuse. **Ne pas le remplacer
par un taux** : l'adoption rapportée à un total est précisément ce que `AGENTS.md`
§6 interdit de publier. **Ne pas ajouter de notice** non plus : six ont déjà été
retirées, et un texte explicatif sous une figure est l'aveu que la figure a raté.

**Les 33 emplacements de texte explicatif.** La condensation est ouverte, le
regroupement en modale ne l'est pas. Chaque emplacement doit être jugé sur ce
qu'il empêche de mal lire, pas compté.

**Le scroll de Ruffin et l'ancrage au clic.** Non mesurés au-delà des hauteurs.
Un ancrage se juge au rendu, pas dans le code.

**La fiche candidat comme « super-CV ».** Seul point qui n'est pas une question
de forme : c'est le positionnement, et il appartient à la propriétaire. Le
recentrage éditorial du 30/09 ne dit rien du niveau de détail des fiches
candidat, seulement de leur place dans la hiérarchie du site.

## Ce qui a servi, et où le retrouver

Les quatre formes et le rendu implémenté : une galerie publiée, construite sur la
vraie fiche. Les trois types de fiche, repliés et dépliés, ont été capturés le
30/09 et vivent dans trois autres galeries — elles ont montré que **le même geste
de lecture est implémenté de trois façons**, ce qu'aucune lecture du code ne
donne.

**Capturer l'application demande Selenium** : le mode capture de Firefox n'attend
pas le chargement asynchrone et rend une page vide. C'est le piège qui a coûté
une session.
