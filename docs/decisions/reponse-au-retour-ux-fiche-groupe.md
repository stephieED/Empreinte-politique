<a id="reponse-au-retour-ux-fiche-groupe"></a>

# La réponse au retour d'ergonomie sur la fiche de groupe : ce qui a été décidé, constat par constat (2026-10-04)

`2026-10-04`

> **En bref** — Le retour d'ergonomie du 02/10/2026
> ([`retour-ux-sur-les-fiches-groupe`](retour-ux-sur-les-fiches-groupe.md))
> portait sept constats et trois recommandations. La propriétaire a arbitré
> toute la fiche sur maquette le 02/10, puis l'a relue sur la page servie les
> 03 et 04/10. **Cinq constats ont une réponse livrée, un l'est en partie, un a
> reçu une autre réponse que celle du retour.** Des trois recommandations,
> **aucune n'a été suivie telle quelle** : deux touchaient une règle
> éditoriale, la troisième a été montrée et écartée. Ouverte sur ses plis, la
> fiche d'Ensemble pour la République passe de **15 007 à 8 450 px** au plus ;
> repliée, de **6 572 à 5 906 px**. Une règle est sortie du travail et vaut
> pour le volet gouvernement : **la maquette arbitre la forme, la page servie
> arbitre le vrai** — c'est en relisant la page qu'une section affichant 0 a
> révélé 969 prises de parole jetées avant le compte.

## Pourquoi ce fichier existe

Le fichier du retour dit ce que le retour demandait et ce que la mesure en
confirmait. Il se terminait par « Tout reste ouvert ».
[`revue-ux-de-la-fiche-de-groupe`](revue-ux-de-la-fiche-de-groupe.md) dit ce
qui a été retenu **section par section**, avec les formes écartées et les
mesures. Celui-ci fait le chemin inverse : il reprend le retour **constat par
constat** et dit ce que chacun est devenu, comme
[`reponse-au-retour-ux-fiche-candidat`](reponse-au-retour-ux-fiche-candidat.md)
l'a fait pour le premier volet. Il ne redit pas les formes ni la palette : il y
renvoie.

## La réponse, constat par constat

| # | Constat du retour | Réponse | État |
| --- | --- | --- | --- |
| 1 | L'« explosion verticale » : 448 noms dépliés sur plus de huit pages | La liste s'ouvre **un groupe à la fois, un seul rang ouvert**. Le plus grand rang, La République en Marche (343 personnes), ajoute 2 544 px, contre 7 583 pour la liste entière | Fait |
| 2 | Ni recherche, ni tri, ni pagination dans la liste dépliée | Le découpage par groupe tient lieu de pagination. **Le champ de recherche a été maquetté, montré, puis écarté par la propriétaire** | Répondu autrement |
| 3 | La hauteur varie à l'extrême selon l'effectif | Un rang ouvert ajoute de 146 px (Écologie Démocratie Solidarité, 17 personnes) à 2 544 px. L'écart reste de 1 à 17 : il suit toujours l'effectif | Fait, en partie |
| 4 | Le diagramme en rubans de « Ce qu'ils ont proposé » | Remplacé par **un carré par texte, une ligne par rôle**, et une barre d'amendements découpée par texte. La section passe de 1 559–1 622 px à 1 128–1 204 px sur les trois fiches | Fait |
| 5 | « Avec qui ils votent » affiche des « pourcentages de proximité (51 %, 50 %) » | Le fait cité était faux — c'étaient des nombres de textes communs — et la lecture fausse était le constat. **Un carré par texte commun** ; la base reste écrite, en petit | Fait |
| 6 | Une accumulation de réserves | **Huit bulles** ancrées aux titres remplacent les phrases sous les titres, les pieds et les renvois | Fait |
| 7 | Sur Écologie Démocratie Solidarité, « Sur quoi ils ont pris la parole » affiche un bloc vide | La section affiche **953 prises de parole**, dont 872 sous « Intitulé non publié ». Le vide venait de deux défauts, l'un dans l'interface, l'autre dans les données. Voir plus bas | Fait côté interface ; côté données, #1189 |

### Ce que la mesure dit, avant et après

Mesuré le 04/10/2026 sur l'application construite depuis `main`
(`fe44777a2`, PR #1192 et #1194 fusionnées), à 1 440 px de large.
Les valeurs « avant » sont celles du fichier du retour, mesurées le 02/10.

| Fiche | Repliée, avant | Repliée, après | Liste des personnes ouverte, avant | Le plus grand rang ouvert, après |
| --- | ---: | ---: | ---: | ---: |
| Ensemble pour la République (`AN-REN`) | 6 572 px | 5 906 px | 15 007 px | 8 450 px |
| Écologie Démocratie Solidarité (`AN-EDS`) | 5 545 px | 5 322 px | 6 826 px | 5 468 px |
| LIOT (`AN-LIOT`) | 6 352 px | 5 601 px | 7 819 px | 5 813 px |

Deux précisions sur ce tableau. Les valeurs « avant, ouverte » comptaient
aussi le pli « Lectures antérieures, amendements, articles et motions », qui
ajoute de 836 à 870 px et qui existe toujours : la colonne « après » n'ouvre
que le rang de personnes. Et Écologie Démocratie Solidarité **gagne moins que
les deux autres repliée**, parce que sa section de parole, vide le 02/10
(297 px), est désormais pleine (631 px).

| Section, fiche d'Ensemble pour la République repliée | Après |
| --- | ---: |
| En bref | 498 px |
| 1 · Qui sont-ils | 642 px |
| 2 · Sur quoi ils ont pris la parole | 712 px |
| 3 · Ce qu'ils ont proposé | 1 151 px |
| 4 · Ce qu'ils ont voté | 914 px |
| 5 · Avec qui ils votent | 950 px |
| 6 · Ce qu'on n'a pas pu lire | 92 px |
| **Fiche entière** | **5 906 px** |

Le détail « avant » par section n'a pas été relevé le 02/10 : seule la section
3 l'a été. Il ne se reconstitue pas.

## Les trois recommandations, et ce qu'elles sont devenues

| Recommandation du retour | Ce qui a été fait |
| --- | --- |
| Paginer la liste : 20 à 30 « membres clefs (présidents, porte-paroles, démissionnaires) », avec une recherche | **Ni membres clefs, ni recherche.** Choisir des membres clefs, c'est la fiche qui décide qui compte dans un groupe, et nommer des « démissionnaires » désigne des personnes par un comportement (`AGENTS.md` §2 règle 1). Les données ne portent d'ailleurs aucune fonction de groupe. La liste s'ouvre un groupe à la fois |
| Une hauteur maximale sur les plis, avec défilement interne | **Montrée sur maquette, écartée.** La fiche a pris la voie de la fiche candidat : ce qui s'ouvre au clic se replie au clic ailleurs |
| Dire d'emblée la part des votes « consensuels » qui « gonflent artificiellement » la proximité | **Écartée.** Rien n'établit que cette part se mesure, et « gonfler » est un jugement sur les votes. Ce qui a été corrigé, c'est la figure : elle n'affiche plus de nombre qui se lise comme un taux |

## Le constat 7 : un bloc vide qui cachait deux défauts

Le retour voyait un bloc vide sur Écologie Démocratie Solidarité. La page
l'expliquait elle-même : « Les membres du groupe sans profil publié manquent à
la collecte ». **Ce n'était pas la cause** : les 17 profils sont publiés. Relue sur la page servie le 04/10, une
fois la nouvelle figure allumée, la section affichait « 0 prise de parole ».
Mesuré : les 17 personnes du groupe portaient 969 interventions pendant la
période du groupe, toutes avec leur texte et leur nature, aucune avec un
intitulé de débat.

| Défaut | Où | Réponse |
| --- | --- | --- |
| Le build ne gardait que les interventions portant un thème, et jetait les autres avant de compter | interface | La règle du sujet est celle de la fiche candidat ; une intervention sans intitulé se compte dans sa nature et se range sous **« Intitulé non publié »** (PR #1192) |
| L'intitulé de séance était jeté à la normalisation pour toute la XVe d'avant avril 2021 | données | #1189, corrigé par la PR #1190 ; mesure de Backend : 489 024 des 631 579 entrées de la XVe |

La ligne « Intitulé non publié » **se compte et ne s'ouvre pas** : sur la XVe,
elle portait 82 080 des 87 367 prises de parole de La République en Marche, et
19,6 Mo à charger au clic. Elle redeviendra ouvrable si le correctif des
données la rend petite.

C'est la propriétaire qui a vu le vide, en relisant la page — « c'est normal
que la fiche de Ecologie Démocratie Solidarité soit vide ? » — et qui a refusé
l'explication par les données seules : « mais on affiche les prises de paroles
même si elles n'ont pas de nature ? non ? ». La figure avait été validée sur maquette et
vérifiée sur une seule fiche.

## Ce que la parole d'un groupe compte, et ne compte pas

Arbitré le 02/10 et précisé le 04/10. La règle vaut **pour la fiche de groupe
seulement** ; la fiche candidat ne retire rien et range la parole de ministre à
part.

| Parole | Sort | Les mots de la propriétaire |
| --- | --- | --- |
| Présidence de séance | Retirée, sans pastille | « ça ne fait pas partie des interventions du groupe » |
| Parole prononcée comme membre du gouvernement | Retirée, sans pastille | « il ne devrait pas y avoir de "membre du gouvernement" dans les interventions des groupes parlementaires » |
| Parole de rapporteur | Comptée | « non on garde le rapporteur » |
| Sans intitulé de débat | Comptée, rangée sous « Intitulé non publié » | « Vraiment, on se calle sur la fiche candidat » |

Le retrait s'applique à toute intervention, avec ou sans intitulé, avant tout
compte. Il dépend d'un champ que les données doivent porter : mesuré sur le
seul profil de Richard Ferrand, aucune de ses 132 interventions de 2017 n'est
marquée, contre 14 372 sur 15 206 de 2018 à 2022.

## Les huit bulles

Écrites ou recomposées par la propriétaire, rendues dans leur bulle avant
d'être retenues, et recopiées dans `tests/test_revue_ergonomie_fiche_groupe.py`.
Sept sont dans
[`revue-ux-de-la-fiche-de-groupe`](revue-ux-de-la-fiche-de-groupe.md) ; la
huitième est arrivée avec la figure des prises de parole.

| Emplacement | Phrase | Note |
| --- | --- | --- |
| 2 · Sur quoi ils ont pris la parole | Les prises de parole des membres du groupe à l'Assemblée, par législature, par nature et par débat. | Une prise de parole peut tenir en quelques mots. |

Deux libellés ont été alignés entre les fiches à cette occasion : la note
d'« En bref » finit par « en comparant leurs membres » depuis que le run
calcule le lien entre groupes
([`lien-etabli-par-comparaison-1168`](lien-etabli-par-comparaison-1168.md)), et
le lien vers la frise des sources s'appelle « Sources et couvertures → » sur la
fiche candidat comme sur la fiche de groupe.

## La page de méthodologie a suivi

Le retour ne la citait pas. Deux relectures transmises par la propriétaire l'ont fait, et les deux
parties qui décrivent les fiches ont été réécrites pour un lecteur qui n'a pas
travaillé sur le projet (PR #1192 pour la fiche candidat, #1194 pour la fiche
de groupe).

| Ce qui est parti | Ce qui le remplace |
| --- | --- |
| « le pivot », « le corpus », neuf noms de champs (`examine_commission`, `position_dans_hemicycle`…) | « la source », « nos données », le nom français de l'étape |
| « la cascade et la chute », « ruban », « la branche basse » | « Lire les textes derrière les figures » : un carré est un texte porté, une barre découpe les amendements d'une commission |
| « racine » et « feuille » du chemin de l'ordre du jour | « premier niveau » et « dernier niveau » |
| « quorum », « dénominateurs », « date de référence », « bande », « motif » | ce que le mot désigne, dit en clair |
| La section « Ordre des catégories » | Retirée : elle décrivait un onglet « Textes » que la fiche candidat n'a plus |

Les propositions de phrases de ces relectures n'ont pas été recopiées : deux
changeaient un fait. « Au moins 50 % » n'est pas « plus de la moitié », qui est
la règle ; et « taux d'accord » nommait un taux que la fiche ne publie pas.

## Ce qui a été décidé contre l'avis de l'agent, et ce qu'il a mal compris

Consigné parce que la suite repartira des mêmes réflexes.

| Sujet | Ce qui était proposé ou compris | Ce qui a été tranché |
| --- | --- | --- |
| Textes portés | Une forme à l'encre seule, qui dispensait de la palette | La couleur reste, comme côté candidat |
| Amendements | Une variante à largeurs exactes | La découpe de la fiche candidat telle quelle, en sachant que 28 textes sur 237 n'y ont aucun pixel |
| Palette | « Harmoniser » lu comme : toutes les palettes des trois fiches | **Les commissions seulement.** Les thèmes européens et les ministères ne sont pas concernés |
| Filtre de la parole | « Se caler sur la fiche candidat » lu comme : ne plus rien retirer | Le filtre reste sur la fiche de groupe ; c'est la règle du sujet qui se cale sur la fiche candidat |
| Extraits d'un débat | Nom en tête, date en colonne étroite | Nom en tête, date au-dessus de chaque propos : la grille d'avant ne laissait que 512 px au texte sur 932 |

## Ce qui reste ouvert

| Sujet | Où il en est |
| --- | --- |
| Treize des quinze fiches de lignée | Jamais regardées à l'écran : seules Ensemble pour la République et Écologie Démocratie Solidarité l'ont été (#1178) |
| La ligne « Intitulé non publié » | À remesurer après un run suivant #1190, puis à rendre ouvrable si elle est devenue petite (#1178) |
| Le constat 3, sur les grands effectifs | Le rang de La République en Marche fait encore 2 544 px |
| Le téléphone | Écarté de ce volet par la propriétaire ; #867 |
| Les agrégats bornés à la législature et non à la période du groupe | #1175 : sur Écologie Démocratie Solidarité, des scrutins de 2019, 2021 et 2022 figurent sur un groupe qui a existé de mai à octobre 2020 |
| Trois constats sur les prises de parole | #1177 |
| « 41 pages publiées », que le retour annonçait | Non retrouvé ; une hypothèse est notée dans `revue-ux-de-la-fiche-de-groupe`, pas un fait |
| Le volet gouvernement | À ouvrir sur le signal de la propriétaire, méthode à confirmer |

## Ce qui a servi, et ce que cela a coûté

La méthode du volet candidat a changé d'un cran : **toute la fiche a été
arbitrée sur maquette avant la première ligne de code**, parce que les
sections se répondent. Elle a tenu pour les formes. Elle n'a pas suffi pour le
vrai.

Cinq pièges payés, pour le volet gouvernement :

- **Une figure validée sur maquette se relit sur la page servie, sur plus d'une
  fiche.** Le vide d'Écologie Démocratie Solidarité n'a été vu ni sur la
  maquette, ni sur la simulation, ni sur la fiche d'Ensemble pour la
  République.
- **Une règle recopiée de la fiche candidat ne tient pas forcément à l'échelle
  d'un groupe.** La barre découpée écrase son plus gros segment dès 51
  segments ; et la règle du sujet, elle, n'avait pas été recopiée du tout.
- **Une cause devinée ne se transmet pas comme un fait.** Le bloc vide avait
  une cause consignée, fausse ; l'écart « motions de censure » aussi.
- **Un total se donne avec ce qu'il contient encore.** Les premiers totaux de
  la XVe comptaient la présidence de séance, que les données ne marquaient pas
  encore : 191 012 prises de parole pour La République en Marche, 87 367 une
  fois le champ arrivé.
- **Pendant une relecture, on modifie et on montre ; la suite complète et le
  push viennent une fois, à la fin.** Retirer une fin de phrase avait pris
  plusieurs minutes, pour des contrôles que personne n'attendait.
