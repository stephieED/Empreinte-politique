# Les mandats de député disent quand la personne a siégé (#1412) (2026-11-02)

`2026-11-02`

> **En bref** — corrige `mandats-electifs-liste-complete-640` sur deux de ses décisions. Un mandat de député est publié par **enregistrement AMO30**, et non plus recollé par siège : un passage au gouvernement le coupe en deux périodes. Le début est la date de l'élection pour un mandat ouvert par une élection, et la date d'entrée en fonction pour une reprise ou une suppléance. Dans la fusion, un mandat de député estampillé « an » est remplacé par les périodes neuves qui recouvrent la sienne : c'est la seule exception nommée à la fusion additive des mandats. Mesuré le 02/11/2026 : 328 des 1 677 profils à mandat de député voient leurs périodes redatées, dont 6 candidats déclarés.

## Contexte mesuré

Le lot 2 de #1248 relit les mandats de député sur la page « fonctions » de l'Assemblée (`/dyn/deputes/<PA>/fonctions` et `?archive=oui`). Essayé le 02/11/2026 sur les 18 candidats déclarés qui ont été députés, il a trouvé que le corpus publiait :

| Erreur | Cas |
| --- | --- |
| un passage au gouvernement compté comme mandat de député | Cazeneuve et Batho (XIVe), Becht (XVIe), Bertrand (XIIIe) — Cazeneuve député de 2012 à 2017, ministre puis Premier ministre pendant ce temps |
| un suppléant daté du jour de l'élection | Philippe (XIIIe, daté du 20/06/2007 pour un siège pris le 23/03/2012), Guedj (XIIIe, XIVe) |
| un mandat en double, sous deux libellés | Brun, XVIIe |
| un mandat manquant | Bertrand, XIIe (2002-2004) |

Sur tout le corpus, contre l'archive AMO30 du 02/11/2026 : 330 des 1 801 profils à identifiant de député ont au moins une période qui ne commence pas à une élection, ou un siège en plusieurs enregistrements ; 115 ont un mandat interrompu par le gouvernement.

## Ce que #640 avait décidé, et pourquoi c'était faux

- **Décision 1** recollait les enregistrements d'un siège sur `(legislature, dateDebut)`. Or `dateDebut` est la date de l'**élection** : les trois enregistrements de 13e législature de Bertrand la portent tous (2007-06-20), même les deux qui commencent en 2009 et en 2012. Le recollage rendait l'enveloppe.
- **Décision 2** choisissait `dateDebut` plutôt que `datePriseFonction`, parce que l'autre date aurait dédoublé les 457 entrées déjà publiées. C'était un choix de fusion, pas de justesse, et il était juste pour les élections seulement.
- L'**alternative écartée** (distinguer interruption et fin) renvoyait à « lire `datePriseFonction` segment par segment », « à instruire séparément ». Rien n'avait été instruit.

AMO30 donne pourtant la réponse dans chaque enregistrement : `election.causeMandat` dit pourquoi la période commence, `mandature.datePriseFonction` quand. Les causes, sur les 3 316 enregistrements des 1 801 profils : 2 868 « élections générales », 73 élections partielles, 167 remplacements d'un député nommé au gouvernement, 113 reprises après le gouvernement, 62 remplacements pour incompatibilité, 21 de député décédé, 12 de député en mission.

## Décision

| | Avant (#640) | Depuis #1412 |
| --- | --- | --- |
| unité publiée | un siège : enregistrements recollés sur `(legislature, dateDebut)` | un enregistrement AMO30 |
| début, mandat ouvert par une élection | `dateDebut` (élection) | inchangé |
| début, reprise ou suppléance | `dateDebut` (l'élection, parfois des années avant) | `datePriseFonction` |
| fusion | additive : l'enveloppe restait | un mandat de député « an » recouvert par une période neuve est remplacé |

Le choix de la date d'élection pour les mandats ouverts par une élection est conservé. Le changer aurait déplacé de trois jours les 2 868 périodes d'élections générales sans rien corriger. La page de l'Assemblée donne les deux (« Élu le 19 juin 2022 – Mandat du 22 juin 2022 »).

**Le remplacement dans la fusion** (`merge_profile.mandats_deputes_conserves`, aux deux étages) ne retire un mandat publié que si une période neuve recouvre la sienne. Une collecte sans mandat de député ne retire rien, et une collecte partielle ne retire que ce qu'elle recouvre. Les mandats non estampillés (#718), sénatoriaux, européens et les autres catégories ne sont jamais touchés. C'est aussi ce qui fait disparaître les doublons au libellé périmé que #640 (décision 3) décrivait.

`NOM_INDEX_IDENTITE` passe en `v6` : l'index d'identité d'avant rendrait les anciennes enveloppes.

## Ce que ça change à l'écran et dans les agrégats

- La frise de 6 candidats déclarés change : Cazeneuve, Batho, Becht, Bertrand (interruptions), Philippe, Guedj (suppléances). Le doublon de Brun disparaît.
- **La cohésion des groupes** : les fenêtres d'éligibilité d'un membre (`group_profile._member_eligibility_intervals`) viennent de ses mandats de député. Un membre au gouvernement n'est plus compté sur les scrutins de cette période. Les dénominateurs publiés peuvent baisser, ce qui est plus juste ; l'effet n'est pas mesuré.
- **Le premier run qui applique la correction perd des entrées sur une liste surveillée** : 3 profils (Brun, Alix Fruchon, Éric Gérard) passent d'un mandat de plus à un de moins, les doublons. Le contrôle de perte bloque le commit : ce run se lance avec `allow_declared_losses`.

## Alternatives écartées

- **Comparer le lot 2 de #1248 sur l'enveloppe** (première et dernière date de chaque législature) : le contrôle aurait passé, et les erreurs seraient restées publiées.
- **Un run `overwrite`** pour réécrire les profils sans fusion : il perdrait tout ce que la fusion additive garde d'une source retirée, et le contrôle de perte le bloquerait de toute façon.
- **Renseigner `suspendu_pour_fonction_gouvernementale`** : inutile pour dire ce que la frise doit montrer, puisque l'interruption est maintenant une absence de période. Le champ reste `null`.

## Non vérifié, et ce qui reste

- **Le mandat manquant de Bertrand (XIIe, 2002-2004)** n'est pas dans AMO30 lui-même : l'archive du 02/11/2026 ne porte aucun enregistrement de 12e législature pour `PA267080`. C'est un fait que l'open data omet ; la correction n'y peut rien.
- **Une phrase publiée est fausse** : la fiche candidat affiche « La source ne dit pas si un mandat s'est interrompu quand cette personne est entrée au gouvernement » (`profilCandidat.js`, clé `suspension`). La source le dit, et le profil le montre désormais. À retirer ou reformuler côté interface, avec la propriétaire.
- L'effet sur les ratios de cohésion publiés n'est pas mesuré.
