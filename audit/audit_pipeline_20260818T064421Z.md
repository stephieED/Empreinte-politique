# Rapport d'audit pipeline (profils + groupes + gouvernements)

Généré le 2026-08-18T06:44:21.242642+00:00. Seuil de péremption des sources : 30 jour(s).

Outil manuel de qualité interne, distinct de `check_quality_gate.py` (seul gate bloquant en CI) : usage manuel uniquement, jamais appelé par la CI. Compile les rapports `audit_pivot_dataset.py`, `audit_groupe_dataset.py` et `audit_gouvernement_dataset.py` sans nouvelle logique de calcul métier, ni score ni classement.

## Vue d'ensemble

| Indicateur | Valeur |
| --- | --- |
| Profils audités | 129 |
| Groupes audités | 7 |
| Gouvernements audités | 10 |
| Erreurs de lecture (profils + groupes + gouvernements) | 0 |
| Warnings (profils + groupes + gouvernements) | 202 |

### Warnings agrégés (profils + groupes + gouvernements)

| Type | Fréquence | Profils concernés | Groupes concernés | Gouvernements concernés |
| --- | --- | --- | --- | --- |
| ParlTrack | 2 | europarl:131580, nosdeputes:jean-luc-melenchon | — | — |
| amendements indisponibles | 2 | nosdeputes:rene-pilato, nosdeputes:rodrigo-arenas | — | — |
| amendements indisponibles (législature 15) | 24 | nosdeputes:annie-vidal, nosdeputes:beatrice-piron, nosdeputes:benjamin-haddad, nosdeputes:benoit-mournet, nosdeputes:bruno-studer, nosdeputes:charlotte-parmentier-lecocq, nosdeputes:david-amiel, nosdeputes:david-valence, nosdeputes:dominique-da-silva, nosdeputes:dominique-faure, nosdeputes:emmanuel-pellerin, nosdeputes:guillaume-vuilletet, nosdeputes:jean-marc-zulesi, nosdeputes:jean-michel-jacques, nosdeputes:ludovic-mendes, nosdeputes:marjolaine-meynier-millefert, nosdeputes:olivier-dussopt, nosdeputes:pascale-boyer, nosdeputes:patrick-vignal, nosdeputes:philippe-dunoyer, nosdeputes:pierre-cazeneuve, nosdeputes:pieyre-alexandre-anglade, nosdeputes:sophie-panonacle, nosdeputes:yannick-chenevard | — | — |
| amendements indisponibles (législature 16) | 24 | nosdeputes:annie-vidal, nosdeputes:beatrice-piron, nosdeputes:benjamin-haddad, nosdeputes:benoit-mournet, nosdeputes:bruno-studer, nosdeputes:charlotte-parmentier-lecocq, nosdeputes:david-amiel, nosdeputes:david-valence, nosdeputes:dominique-da-silva, nosdeputes:dominique-faure, nosdeputes:emmanuel-pellerin, nosdeputes:guillaume-vuilletet, nosdeputes:jean-marc-zulesi, nosdeputes:jean-michel-jacques, nosdeputes:ludovic-mendes, nosdeputes:marjolaine-meynier-millefert, nosdeputes:olivier-dussopt, nosdeputes:pascale-boyer, nosdeputes:patrick-vignal, nosdeputes:philippe-dunoyer, nosdeputes:pierre-cazeneuve, nosdeputes:pieyre-alexandre-anglade, nosdeputes:sophie-panonacle, nosdeputes:yannick-chenevard | — | — |
| amendements indisponibles (législature 17) | 32 | nosdeputes:annie-vidal, nosdeputes:beatrice-piron, nosdeputes:benjamin-haddad, nosdeputes:benoit-mournet, nosdeputes:bruno-studer, nosdeputes:catherine-belrhiti, nosdeputes:catherine-procaccia, nosdeputes:charlotte-parmentier-lecocq, nosdeputes:david-amiel, nosdeputes:david-valence, nosdeputes:dominique-da-silva, nosdeputes:dominique-faure, nosdeputes:emmanuel-pellerin, nosdeputes:eric-dolige, nosdeputes:evelyne-renaud-garabedian, nosdeputes:guillaume-vuilletet, nosdeputes:hussein-bourgi, nosdeputes:jean-marc-zulesi, nosdeputes:jean-michel-jacques, nosdeputes:jean-pierre-bansard, nosdeputes:joel-bigot, nosdeputes:ludovic-mendes, nosdeputes:marjolaine-meynier-millefert, nosdeputes:olivier-dussopt, nosdeputes:pascale-boyer, nosdeputes:patrick-vignal, nosdeputes:philippe-dunoyer, nosdeputes:pierre-cazeneuve, nosdeputes:pieyre-alexandre-anglade, nosdeputes:sophie-panonacle, nosdeputes:viviane-malet, nosdeputes:yannick-chenevard | — | — |
| couverture_roster_senat | 2 | — | Senat:LR, Senat:SER | — |
| fraicheur_donnees | 7 | — | AN:LFI, AN:LR, AN:REN, AN:RN, AN:SOC, Senat:LR, Senat:SER | — |
| mandats introuvables | 9 | nosdeputes:charles-guene, nosdeputes:eric-dolige, nosdeputes:evelyne-renaud-garabedian, nosdeputes:jean-jacques-panunzi, nosdeputes:jean-pierre-bansard, nosdeputes:jean-raymond-hugonet, nosdeputes:marie-christine-chauvin, nosdeputes:thierry-cozic, nosdeputes:viviane-malet | — | — |
| synchro_sources.nosdeputes | 80 | nosdeputes:anne-genetet, nosdeputes:anne-sophie-frigout, nosdeputes:antoine-villedieu, nosdeputes:benjamin-dirx, nosdeputes:brigitte-klinkert, nosdeputes:bruno-bilde, nosdeputes:carole-grandjean, nosdeputes:catherine-belrhiti, nosdeputes:catherine-deroche, nosdeputes:catherine-dumas, nosdeputes:catherine-procaccia, nosdeputes:celine-calvez, nosdeputes:charles-guene, nosdeputes:christine-decodts, nosdeputes:christine-le-nabour, nosdeputes:christophe-bentz, nosdeputes:christophe-marion, nosdeputes:claude-raynal, nosdeputes:corinne-vignon, nosdeputes:danielle-brulebois, nosdeputes:dominique-de-legge, nosdeputes:eric-dolige, nosdeputes:evelyne-renaud-garabedian, nosdeputes:fabien-di-filippo, nosdeputes:florent-boudie, nosdeputes:franck-riester, nosdeputes:francois-cormier-bouligeon, nosdeputes:francoise-buffet, nosdeputes:gerard-larcher, nosdeputes:gilles-le-gendre, nosdeputes:graziella-melchior, nosdeputes:hadrien-ghomi, nosdeputes:herve-berville, nosdeputes:hussein-bourgi, nosdeputes:jean-carles-grelier, nosdeputes:jean-francois-lovisolo, nosdeputes:jean-francois-rousset, nosdeputes:jean-jacques-panunzi, nosdeputes:jean-luc-bourgeaux, nosdeputes:jean-pierre-bansard, nosdeputes:jean-pierre-vigier, nosdeputes:jean-raymond-hugonet, nosdeputes:jean-rene-cazeneuve, nosdeputes:jean-terlier, nosdeputes:joel-bigot, nosdeputes:julie-delpech, nosdeputes:julien-odoul, nosdeputes:julien-rancoule, nosdeputes:karl-olive, nosdeputes:lionel-vuibert, nosdeputes:lysiane-metayer, nosdeputes:marie-christine-chauvin, nosdeputes:marie-guevenoux, nosdeputes:marie-pierre-rixain, nosdeputes:martine-etienne, nosdeputes:mathieu-lefevre, nosdeputes:maud-bregeon, nosdeputes:maxime-minot, nosdeputes:michael-taverne, nosdeputes:michel-lauzzana, nosdeputes:mikaele-seo, nosdeputes:nicole-le-peih, nosdeputes:pascal-lavergne, nosdeputes:philippe-juvin, nosdeputes:prisca-thevenot, nosdeputes:quentin-bataillon, nosdeputes:rene-pilato, nosdeputes:rodrigo-arenas, nosdeputes:roland-lescure, nosdeputes:sandra-marsaud, nosdeputes:sandrine-le-feur, nosdeputes:stephane-travert, nosdeputes:stephanie-rist, nosdeputes:thierry-cozic, nosdeputes:thomas-gassilloud, nosdeputes:veronique-riotton, nosdeputes:vincent-rolland, nosdeputes:viviane-malet, nosdeputes:yannick-haury, nosdeputes:yannick-vaugrenard | — | — |
| votes introuvables | 20 | nosdeputes:bruno-retailleau, nosdeputes:catherine-belrhiti, nosdeputes:catherine-deroche, nosdeputes:catherine-dumas, nosdeputes:catherine-procaccia, nosdeputes:charles-guene, nosdeputes:claude-raynal, nosdeputes:dominique-de-legge, nosdeputes:eric-dolige, nosdeputes:evelyne-renaud-garabedian, nosdeputes:gerard-larcher, nosdeputes:hussein-bourgi, nosdeputes:jean-jacques-panunzi, nosdeputes:jean-pierre-bansard, nosdeputes:jean-raymond-hugonet, nosdeputes:joel-bigot, nosdeputes:marie-christine-chauvin, nosdeputes:thierry-cozic, nosdeputes:viviane-malet, nosdeputes:yannick-vaugrenard | — | — |

### Erreurs de lecture agrégées

Aucune erreur de lecture.

---

# Rapport d'audit du jeu de données pivot

Généré le 2026-08-18T06:44:21.242642+00:00. 129 profil(s) analysé(s), 0 erreur(s) de lecture. Seuil de péremption des sources : 30 jour(s).

Ce rapport est un outil de qualité interne : il présente des indicateurs bruts, sans jugement de valeur ni classement.

## Volumétrie

Total profils : 129

### Répartition par chambre

| Chambre | Profils |
| --- | --- |
| AN | 127 |
| PE | 1 |
| Senat | 1 |
| mairie | 0 |
| null | 0 |

### Répartition par provenance (`meta.provenance`)

| Provenance | Profils |
| --- | --- |
| candidat_declare | 8 |
| roster_groupe | 121 |
| null | 0 |

## Tableau croisé des volumes par candidat

Candidats déclarés uniquement (`meta.provenance` = `candidat_declare`).

| id | Nom | Chambre | Votes | Textes portés | Amendements | Interventions |
| --- | --- | --- | --- | --- | --- | --- |
| nosdeputes:bruno-retailleau | Bruno Retailleau | AN | 0 | 36 | 0 | 0 |
| nosdeputes:gabriel-attal | Gabriel Attal | AN | 2035 | 34 | 1074 | 5 |
| nosdeputes:jean-luc-melenchon | Jean-Luc Mélenchon | AN | 1016 | 0 | 11043 | 15 |
| europarl:131580 | Jordan BARDELLA | PE | 0 | 0 | 0 | 0 |
| nosdeputes:jerome-guedj | Jérôme Guedj | AN | 2906 | 5 | 13477 | 395 |
| nosdeputes:laurent-wauquiez | Laurent Wauquiez | AN | 826 | 9 | 1949 | 22 |
| nosdeputes:marine-le-pen | Marine Le Pen | AN | 1813 | 23 | 13094 | 302 |
| nosdeputes:edouard-philippe | Édouard Philippe | AN | 141 | 283 | 749 | 50 |

### Membres de groupe non candidats (agrégé par groupe)

121 profil(s) issus des rosters de groupes (`meta.provenance` = `roster_groupe`) : volumes agrégés, sans détail par membre.

| Groupe | Profils | Champ | Min | Max | Médiane | Moyenne |
| --- | --- | --- | --- | --- | --- | --- |
| Droite Républicaine | 5 | votes | 298 | 768 | 698 | 624.4 |
| Droite Républicaine | 5 | textes_portes | 0 | 0 | 0 | 0 |
| Droite Républicaine | 5 | amendements | 4959 | 11300 | 6880 | 7601.4 |
| Droite Républicaine | 5 | interventions | 0 | 0 | 0 | 0 |
| Ensemble pour la République | 21 | votes | 282 | 1885 | 1233 | 1164.52 |
| Ensemble pour la République | 21 | textes_portes | 0 | 7 | 0 | 0.52 |
| Ensemble pour la République | 21 | amendements | 1090 | 7740 | 3552 | 3497.62 |
| Ensemble pour la République | 21 | interventions | 0 | 0 | 0 | 0 |
| Horizons & Indépendants | 2 | votes | 1044 | 2178 | 1611.0 | 1611 |
| Horizons & Indépendants | 2 | textes_portes | 0 | 2 | 1.0 | 1 |
| Horizons & Indépendants | 2 | amendements | 3618 | 4006 | 3812.0 | 3812 |
| Horizons & Indépendants | 2 | interventions | 0 | 0 | 0.0 | 0 |
| La France insoumise - Nouveau Front Populaire | 2 | votes | 564 | 1136 | 850.0 | 850 |
| La France insoumise - Nouveau Front Populaire | 2 | textes_portes | 0 | 0 | 0.0 | 0 |
| La France insoumise - Nouveau Front Populaire | 2 | amendements | 0 | 0 | 0.0 | 0 |
| La France insoumise - Nouveau Front Populaire | 2 | interventions | 0 | 0 | 0.0 | 0 |
| La France insoumise - Nouvelle Union Populaire écologique et sociale | 1 | votes | 1102 | 1102 | 1102 | 1102 |
| La France insoumise - Nouvelle Union Populaire écologique et sociale | 1 | textes_portes | 0 | 0 | 0 | 0 |
| La France insoumise - Nouvelle Union Populaire écologique et sociale | 1 | amendements | 11561 | 11561 | 11561 | 11561 |
| La France insoumise - Nouvelle Union Populaire écologique et sociale | 1 | interventions | 0 | 0 | 0 | 0 |
| Les Démocrates | 1 | votes | 253 | 253 | 253 | 253 |
| Les Démocrates | 1 | textes_portes | 0 | 0 | 0 | 0 |
| Les Démocrates | 1 | amendements | 3961 | 3961 | 3961 | 3961 |
| Les Démocrates | 1 | interventions | 0 | 0 | 0 | 0 |
| Les Républicains | 1 | votes | 1250 | 1250 | 1250 | 1250 |
| Les Républicains | 1 | textes_portes | 0 | 0 | 0 | 0 |
| Les Républicains | 1 | amendements | 4813 | 4813 | 4813 | 4813 |
| Les Républicains | 1 | interventions | 0 | 0 | 0 | 0 |
| Non inscrit | 2 | votes | 602 | 1061 | 831.5 | 831.5 |
| Non inscrit | 2 | textes_portes | 1 | 1 | 1.0 | 1 |
| Non inscrit | 2 | amendements | 2766 | 5063 | 3914.5 | 3914.5 |
| Non inscrit | 2 | interventions | 0 | 0 | 0.0 | 0 |
| REN | 12 | votes | 1 | 2642 | 1385.0 | 1420.33 |
| REN | 12 | textes_portes | 0 | 6 | 0.0 | 1.08 |
| REN | 12 | amendements | 0 | 0 | 0.0 | 0 |
| REN | 12 | interventions | 0 | 0 | 0.0 | 0 |
| RN | 1 | votes | 832 | 832 | 832 | 832 |
| RN | 1 | textes_portes | 0 | 0 | 0 | 0 |
| RN | 1 | amendements | 5861 | 5861 | 5861 | 5861 |
| RN | 1 | interventions | 0 | 0 | 0 | 0 |
| Rassemblement Démocratique et Social européen | 1 | votes | 882 | 882 | 882 | 882 |
| Rassemblement Démocratique et Social européen | 1 | textes_portes | 6 | 6 | 6 | 6 |
| Rassemblement Démocratique et Social européen | 1 | amendements | 0 | 0 | 0 | 0 |
| Rassemblement Démocratique et Social européen | 1 | interventions | 0 | 0 | 0 | 0 |
| Rassemblement National | 7 | votes | 427 | 2480 | 1009 | 1134.57 |
| Rassemblement National | 7 | textes_portes | 0 | 0 | 0 | 0 |
| Rassemblement National | 7 | amendements | 1779 | 10149 | 5778 | 6228.86 |
| Rassemblement National | 7 | interventions | 0 | 0 | 0 | 0 |
| Renaissance | 27 | votes | 9 | 1921 | 959 | 971.11 |
| Renaissance | 27 | textes_portes | 0 | 6 | 0 | 0.56 |
| Renaissance | 27 | amendements | 0 | 10474 | 1435 | 1599.89 |
| Renaissance | 27 | interventions | 0 | 0 | 0 | 0 |
| null | 38 | votes | 0 | 5697 | 469.0 | 1257.95 |
| null | 38 | textes_portes | 0 | 0 | 0.0 | 0 |
| null | 38 | amendements | 0 | 7186 | 635.0 | 1541.66 |
| null | 38 | interventions | 0 | 0 | 0.0 | 0 |
| Ensemble | 121 | votes | 0 | 5697 | 1041 | 1136.27 |
| Ensemble | 121 | textes_portes | 0 | 7 | 0 | 0.4 |
| Ensemble | 121 | amendements | 0 | 11561 | 2031 | 2466.84 |
| Ensemble | 121 | interventions | 0 | 0 | 0 | 0 |

## Plages temporelles par candidat

Candidats déclarés uniquement (`meta.provenance` = `candidat_declare`).

| id | Nom | Chambre | Votes | Textes portés | Amendements | Interventions |
| --- | --- | --- | --- | --- | --- | --- |
| nosdeputes:bruno-retailleau | Bruno Retailleau | AN | — | 2010-12-14 → 2026-05-06 | — | — |
| nosdeputes:gabriel-attal | Gabriel Attal | AN | 2017-07-04 → 2026-07-21 | 2017-11-21 → 2026-05-26 | 2017-10-05 → 2026-07-10 | — |
| nosdeputes:jean-luc-melenchon | Jean-Luc Mélenchon | AN | 2017-07-04 → 2022-01-13 | — | 2017-07-11 → 2022-02-03 | — |
| europarl:131580 | Jordan BARDELLA | PE | — | — | — | — |
| nosdeputes:jerome-guedj | Jérôme Guedj | AN | 2012-10-09 → 2026-07-21 | 2022-09-15 → 2025-12-10 | 2012-07-12 → 2026-07-10 | 2022-07-11 → 2026-07-07 |
| nosdeputes:laurent-wauquiez | Laurent Wauquiez | AN | 2012-07-03 → 2026-07-21 | 2024-10-15 → 2026-02-03 | 2012-07-12 → 2026-07-10 | 2025-07-22 → 2026-04-21 |
| nosdeputes:marine-le-pen | Marine Le Pen | AN | 2017-07-04 → 2026-07-21 | 2017-10-13 → 2024-01-25 | 2017-07-21 → 2026-07-16 | 2022-07-06 → 2025-12-30 |
| nosdeputes:edouard-philippe | Édouard Philippe | AN | 2012-07-03 → 2016-11-22 | 2017-06-14 → 2024-03-21 | 2012-07-12 → 2017-02-02 | 2017-08-09 → 2019-12-10 |

### Membres de groupe non candidats (agrégé par groupe)

121 profil(s) issus des rosters de groupes (`meta.provenance` = `roster_groupe`) : plage englobante du groupe, sans détail par membre.

| Groupe | Profils | Votes | Textes portés | Amendements | Interventions |
| --- | --- | --- | --- | --- | --- |
| Droite Républicaine | 5 | 2022-07-11 → 2024-06-07 | — | 2012-07-12 → 2026-07-10 | — |
| Ensemble pour la République | 21 | 2022-07-11 → 2024-06-07 | 2024-07-18 → 2026-07-23 | 2012-07-12 → 2026-07-16 | — |
| Horizons & Indépendants | 2 | 2022-07-11 → 2024-06-05 | 2025-04-03 → 2026-07-24 | 2017-07-07 → 2026-07-16 | — |
| La France insoumise - Nouveau Front Populaire | 2 | 2022-07-11 → 2024-06-07 | — | — | — |
| La France insoumise - Nouvelle Union Populaire écologique et sociale | 1 | 2022-07-11 → 2024-06-03 | — | 2022-07-05 → 2024-06-07 | — |
| Les Démocrates | 1 | 2022-07-12 → 2024-05-14 | — | 2017-07-21 → 2024-06-01 | — |
| Les Républicains | 1 | 2022-07-11 → 2024-06-05 | — | 2017-07-21 → 2024-06-07 | — |
| Non inscrit | 2 | 2022-07-11 → 2024-06-07 | 2025-02-04 → 2026-06-24 | 2012-07-12 → 2026-07-10 | — |
| REN | 12 | 2022-07-11 → 2024-06-07 | 2022-12-14 → 2026-08-06 | — | — |
| RN | 1 | 2022-07-11 → 2024-06-04 | — | 2022-07-09 → 2024-06-08 | — |
| Rassemblement Démocratique et Social européen | 1 | 2022-07-11 → 2024-06-06 | 2012-10-16 → 2026-03-27 | — | — |
| Rassemblement National | 7 | 2022-07-11 → 2024-06-07 | — | 2017-07-21 → 2026-07-16 | — |
| Renaissance | 27 | 2022-07-11 → 2024-06-07 | 2013-09-10 → 2026-06-29 | 2012-07-12 → 2024-06-08 | — |
| null | 38 | 2012-07-03 → 2026-07-21 | — | 2012-07-12 → 2026-07-15 | — |
| Ensemble | 121 | 2012-07-03 → 2026-07-21 | 2012-10-16 → 2026-08-06 | 2012-07-12 → 2026-07-16 | — |

### Dates ignorées (invalides ou non parseables)

| Champ | Dates ignorées |
| --- | --- |
| interventions | 6 |

## Complétude

### Taux de remplissage

| Champ | Renseignés | Total | Taux (%) |
| --- | --- | --- | --- |
| parti | 8 | 129 | 6.2 |
| groupe | 91 | 129 | 70.54 |
| tags_thematiques | 3 | 129 | 2.33 |
| mandats | 120 | 129 | 93.02 |

### Profils sans activité (aucun vote, amendement ni intervention)

21 / 129 profil(s).

### Présence des métadonnées

| Critère | Profils en défaut (sur 129) |
| --- | --- |
| meta absente | 0 |
| licence_donnees manquante | 0 |
| genere_le manquant | 0 |

## Cohérence

### Doublons d'`id`

Aucun doublon détecté.

### Divergence `schema_version` / `meta.schema_version`

Aucune divergence détectée.

### Dates de traçabilité invalides ou futures

| id | Champ | Valeur | Erreur |
| --- | --- | --- | --- |
| nosdeputes:anne-genetet | sources[0].synchro_le |  | format_invalide |
| nosdeputes:anne-sophie-frigout | sources[0].synchro_le |  | format_invalide |
| nosdeputes:antoine-villedieu | sources[0].synchro_le |  | format_invalide |
| nosdeputes:benjamin-dirx | sources[0].synchro_le |  | format_invalide |
| nosdeputes:brigitte-klinkert | sources[0].synchro_le |  | format_invalide |
| nosdeputes:bruno-bilde | sources[0].synchro_le |  | format_invalide |
| nosdeputes:carole-grandjean | sources[0].synchro_le |  | format_invalide |
| nosdeputes:catherine-belrhiti | sources[0].synchro_le |  | format_invalide |
| nosdeputes:catherine-deroche | sources[0].synchro_le |  | format_invalide |
| nosdeputes:catherine-dumas | sources[0].synchro_le |  | format_invalide |
| nosdeputes:catherine-procaccia | sources[0].synchro_le |  | format_invalide |
| nosdeputes:celine-calvez | sources[0].synchro_le |  | format_invalide |
| nosdeputes:charles-guene | sources[0].synchro_le |  | format_invalide |
| nosdeputes:christine-decodts | sources[0].synchro_le |  | format_invalide |
| nosdeputes:christine-le-nabour | sources[0].synchro_le |  | format_invalide |
| nosdeputes:christophe-bentz | sources[0].synchro_le |  | format_invalide |
| nosdeputes:christophe-marion | sources[0].synchro_le |  | format_invalide |
| nosdeputes:claude-raynal | sources[0].synchro_le |  | format_invalide |
| nosdeputes:corinne-vignon | sources[0].synchro_le |  | format_invalide |
| nosdeputes:danielle-brulebois | sources[0].synchro_le |  | format_invalide |
| nosdeputes:dominique-de-legge | sources[0].synchro_le |  | format_invalide |
| nosdeputes:eric-dolige | sources[0].synchro_le |  | format_invalide |
| nosdeputes:evelyne-renaud-garabedian | sources[0].synchro_le |  | format_invalide |
| nosdeputes:fabien-di-filippo | sources[0].synchro_le |  | format_invalide |
| nosdeputes:florent-boudie | sources[0].synchro_le |  | format_invalide |
| nosdeputes:franck-riester | sources[0].synchro_le |  | format_invalide |
| nosdeputes:francois-cormier-bouligeon | sources[0].synchro_le |  | format_invalide |
| nosdeputes:francoise-buffet | sources[0].synchro_le |  | format_invalide |
| nosdeputes:gerard-larcher | sources[0].synchro_le |  | format_invalide |
| nosdeputes:gilles-le-gendre | sources[0].synchro_le |  | format_invalide |
| nosdeputes:graziella-melchior | sources[0].synchro_le |  | format_invalide |
| nosdeputes:hadrien-ghomi | sources[0].synchro_le |  | format_invalide |
| nosdeputes:herve-berville | sources[0].synchro_le |  | format_invalide |
| nosdeputes:hussein-bourgi | sources[0].synchro_le |  | format_invalide |
| nosdeputes:jean-carles-grelier | sources[0].synchro_le |  | format_invalide |
| nosdeputes:jean-francois-lovisolo | sources[0].synchro_le |  | format_invalide |
| nosdeputes:jean-francois-rousset | sources[0].synchro_le |  | format_invalide |
| nosdeputes:jean-jacques-panunzi | sources[0].synchro_le |  | format_invalide |
| nosdeputes:jean-luc-bourgeaux | sources[0].synchro_le |  | format_invalide |
| nosdeputes:jean-pierre-bansard | sources[0].synchro_le |  | format_invalide |
| nosdeputes:jean-pierre-vigier | sources[0].synchro_le |  | format_invalide |
| nosdeputes:jean-raymond-hugonet | sources[0].synchro_le |  | format_invalide |
| nosdeputes:jean-rene-cazeneuve | sources[0].synchro_le |  | format_invalide |
| nosdeputes:jean-terlier | sources[0].synchro_le |  | format_invalide |
| nosdeputes:joel-bigot | sources[0].synchro_le |  | format_invalide |
| nosdeputes:julie-delpech | sources[0].synchro_le |  | format_invalide |
| nosdeputes:julien-odoul | sources[0].synchro_le |  | format_invalide |
| nosdeputes:julien-rancoule | sources[0].synchro_le |  | format_invalide |
| nosdeputes:karl-olive | sources[0].synchro_le |  | format_invalide |
| nosdeputes:lionel-vuibert | sources[0].synchro_le |  | format_invalide |
| nosdeputes:lysiane-metayer | sources[0].synchro_le |  | format_invalide |
| nosdeputes:marie-christine-chauvin | sources[0].synchro_le |  | format_invalide |
| nosdeputes:marie-guevenoux | sources[0].synchro_le |  | format_invalide |
| nosdeputes:marie-pierre-rixain | sources[0].synchro_le |  | format_invalide |
| nosdeputes:martine-etienne | sources[0].synchro_le |  | format_invalide |
| nosdeputes:mathieu-lefevre | sources[0].synchro_le |  | format_invalide |
| nosdeputes:maud-bregeon | sources[0].synchro_le |  | format_invalide |
| nosdeputes:maxime-minot | sources[0].synchro_le |  | format_invalide |
| nosdeputes:michael-taverne | sources[0].synchro_le |  | format_invalide |
| nosdeputes:michel-lauzzana | sources[0].synchro_le |  | format_invalide |
| nosdeputes:mikaele-seo | sources[0].synchro_le |  | format_invalide |
| nosdeputes:nicole-le-peih | sources[0].synchro_le |  | format_invalide |
| nosdeputes:pascal-lavergne | sources[0].synchro_le |  | format_invalide |
| nosdeputes:philippe-juvin | sources[0].synchro_le |  | format_invalide |
| nosdeputes:prisca-thevenot | sources[0].synchro_le |  | format_invalide |
| nosdeputes:quentin-bataillon | sources[0].synchro_le |  | format_invalide |
| nosdeputes:rene-pilato | sources[0].synchro_le |  | format_invalide |
| nosdeputes:rodrigo-arenas | sources[0].synchro_le |  | format_invalide |
| nosdeputes:roland-lescure | sources[0].synchro_le |  | format_invalide |
| nosdeputes:sandra-marsaud | sources[0].synchro_le |  | format_invalide |
| nosdeputes:sandrine-le-feur | sources[0].synchro_le |  | format_invalide |
| nosdeputes:stephane-travert | sources[0].synchro_le |  | format_invalide |
| nosdeputes:stephanie-rist | sources[0].synchro_le |  | format_invalide |
| nosdeputes:thierry-cozic | sources[0].synchro_le |  | format_invalide |
| nosdeputes:thomas-gassilloud | sources[0].synchro_le |  | format_invalide |
| nosdeputes:veronique-riotton | sources[0].synchro_le |  | format_invalide |
| nosdeputes:vincent-rolland | sources[0].synchro_le |  | format_invalide |
| nosdeputes:viviane-malet | sources[0].synchro_le |  | format_invalide |
| nosdeputes:yannick-haury | sources[0].synchro_le |  | format_invalide |
| nosdeputes:yannick-vaugrenard | sources[0].synchro_le |  | format_invalide |

### Cohérence `chambre` / types de `sources[]`

Aucune incohérence détectée.

## Fraîcheur

### Ancienneté des sources par type (jours écoulés depuis `synchro_le`)

| Type de source | Nombre de sources | Min | Max | Médiane | Moyenne |
| --- | --- | --- | --- | --- | --- |
| assemblee_nationale | 108 | 0 | 4 | 0.0 | 0.75 |
| europarl | 7 | 0 | 0 | 0 | 0 |
| nosdeputes | 48 | 0 | 11 | 3.5 | 3.88 |
| nossenateurs | 3 | 0 | 0 | 0 | 0 |

### Profils périmés (toutes sources > 30 jours)

Aucun profil périmé.

## Warnings

Total : 193

| Type | Fréquence | Profils concernés |
| --- | --- | --- |
| ParlTrack | 2 | europarl:131580, nosdeputes:jean-luc-melenchon |
| amendements indisponibles | 2 | nosdeputes:rene-pilato, nosdeputes:rodrigo-arenas |
| amendements indisponibles (législature 15) | 24 | nosdeputes:annie-vidal, nosdeputes:beatrice-piron, nosdeputes:benjamin-haddad, nosdeputes:benoit-mournet, nosdeputes:bruno-studer, nosdeputes:charlotte-parmentier-lecocq, nosdeputes:david-amiel, nosdeputes:david-valence, nosdeputes:dominique-da-silva, nosdeputes:dominique-faure, nosdeputes:emmanuel-pellerin, nosdeputes:guillaume-vuilletet, nosdeputes:jean-marc-zulesi, nosdeputes:jean-michel-jacques, nosdeputes:ludovic-mendes, nosdeputes:marjolaine-meynier-millefert, nosdeputes:olivier-dussopt, nosdeputes:pascale-boyer, nosdeputes:patrick-vignal, nosdeputes:philippe-dunoyer, nosdeputes:pierre-cazeneuve, nosdeputes:pieyre-alexandre-anglade, nosdeputes:sophie-panonacle, nosdeputes:yannick-chenevard |
| amendements indisponibles (législature 16) | 24 | nosdeputes:annie-vidal, nosdeputes:beatrice-piron, nosdeputes:benjamin-haddad, nosdeputes:benoit-mournet, nosdeputes:bruno-studer, nosdeputes:charlotte-parmentier-lecocq, nosdeputes:david-amiel, nosdeputes:david-valence, nosdeputes:dominique-da-silva, nosdeputes:dominique-faure, nosdeputes:emmanuel-pellerin, nosdeputes:guillaume-vuilletet, nosdeputes:jean-marc-zulesi, nosdeputes:jean-michel-jacques, nosdeputes:ludovic-mendes, nosdeputes:marjolaine-meynier-millefert, nosdeputes:olivier-dussopt, nosdeputes:pascale-boyer, nosdeputes:patrick-vignal, nosdeputes:philippe-dunoyer, nosdeputes:pierre-cazeneuve, nosdeputes:pieyre-alexandre-anglade, nosdeputes:sophie-panonacle, nosdeputes:yannick-chenevard |
| amendements indisponibles (législature 17) | 32 | nosdeputes:annie-vidal, nosdeputes:beatrice-piron, nosdeputes:benjamin-haddad, nosdeputes:benoit-mournet, nosdeputes:bruno-studer, nosdeputes:catherine-belrhiti, nosdeputes:catherine-procaccia, nosdeputes:charlotte-parmentier-lecocq, nosdeputes:david-amiel, nosdeputes:david-valence, nosdeputes:dominique-da-silva, nosdeputes:dominique-faure, nosdeputes:emmanuel-pellerin, nosdeputes:eric-dolige, nosdeputes:evelyne-renaud-garabedian, nosdeputes:guillaume-vuilletet, nosdeputes:hussein-bourgi, nosdeputes:jean-marc-zulesi, nosdeputes:jean-michel-jacques, nosdeputes:jean-pierre-bansard, nosdeputes:joel-bigot, nosdeputes:ludovic-mendes, nosdeputes:marjolaine-meynier-millefert, nosdeputes:olivier-dussopt, nosdeputes:pascale-boyer, nosdeputes:patrick-vignal, nosdeputes:philippe-dunoyer, nosdeputes:pierre-cazeneuve, nosdeputes:pieyre-alexandre-anglade, nosdeputes:sophie-panonacle, nosdeputes:viviane-malet, nosdeputes:yannick-chenevard |
| mandats introuvables | 9 | nosdeputes:charles-guene, nosdeputes:eric-dolige, nosdeputes:evelyne-renaud-garabedian, nosdeputes:jean-jacques-panunzi, nosdeputes:jean-pierre-bansard, nosdeputes:jean-raymond-hugonet, nosdeputes:marie-christine-chauvin, nosdeputes:thierry-cozic, nosdeputes:viviane-malet |
| synchro_sources.nosdeputes | 80 | nosdeputes:anne-genetet, nosdeputes:anne-sophie-frigout, nosdeputes:antoine-villedieu, nosdeputes:benjamin-dirx, nosdeputes:brigitte-klinkert, nosdeputes:bruno-bilde, nosdeputes:carole-grandjean, nosdeputes:catherine-belrhiti, nosdeputes:catherine-deroche, nosdeputes:catherine-dumas, nosdeputes:catherine-procaccia, nosdeputes:celine-calvez, nosdeputes:charles-guene, nosdeputes:christine-decodts, nosdeputes:christine-le-nabour, nosdeputes:christophe-bentz, nosdeputes:christophe-marion, nosdeputes:claude-raynal, nosdeputes:corinne-vignon, nosdeputes:danielle-brulebois, nosdeputes:dominique-de-legge, nosdeputes:eric-dolige, nosdeputes:evelyne-renaud-garabedian, nosdeputes:fabien-di-filippo, nosdeputes:florent-boudie, nosdeputes:franck-riester, nosdeputes:francois-cormier-bouligeon, nosdeputes:francoise-buffet, nosdeputes:gerard-larcher, nosdeputes:gilles-le-gendre, nosdeputes:graziella-melchior, nosdeputes:hadrien-ghomi, nosdeputes:herve-berville, nosdeputes:hussein-bourgi, nosdeputes:jean-carles-grelier, nosdeputes:jean-francois-lovisolo, nosdeputes:jean-francois-rousset, nosdeputes:jean-jacques-panunzi, nosdeputes:jean-luc-bourgeaux, nosdeputes:jean-pierre-bansard, nosdeputes:jean-pierre-vigier, nosdeputes:jean-raymond-hugonet, nosdeputes:jean-rene-cazeneuve, nosdeputes:jean-terlier, nosdeputes:joel-bigot, nosdeputes:julie-delpech, nosdeputes:julien-odoul, nosdeputes:julien-rancoule, nosdeputes:karl-olive, nosdeputes:lionel-vuibert, nosdeputes:lysiane-metayer, nosdeputes:marie-christine-chauvin, nosdeputes:marie-guevenoux, nosdeputes:marie-pierre-rixain, nosdeputes:martine-etienne, nosdeputes:mathieu-lefevre, nosdeputes:maud-bregeon, nosdeputes:maxime-minot, nosdeputes:michael-taverne, nosdeputes:michel-lauzzana, nosdeputes:mikaele-seo, nosdeputes:nicole-le-peih, nosdeputes:pascal-lavergne, nosdeputes:philippe-juvin, nosdeputes:prisca-thevenot, nosdeputes:quentin-bataillon, nosdeputes:rene-pilato, nosdeputes:rodrigo-arenas, nosdeputes:roland-lescure, nosdeputes:sandra-marsaud, nosdeputes:sandrine-le-feur, nosdeputes:stephane-travert, nosdeputes:stephanie-rist, nosdeputes:thierry-cozic, nosdeputes:thomas-gassilloud, nosdeputes:veronique-riotton, nosdeputes:vincent-rolland, nosdeputes:viviane-malet, nosdeputes:yannick-haury, nosdeputes:yannick-vaugrenard |
| votes introuvables | 20 | nosdeputes:bruno-retailleau, nosdeputes:catherine-belrhiti, nosdeputes:catherine-deroche, nosdeputes:catherine-dumas, nosdeputes:catherine-procaccia, nosdeputes:charles-guene, nosdeputes:claude-raynal, nosdeputes:dominique-de-legge, nosdeputes:eric-dolige, nosdeputes:evelyne-renaud-garabedian, nosdeputes:gerard-larcher, nosdeputes:hussein-bourgi, nosdeputes:jean-jacques-panunzi, nosdeputes:jean-pierre-bansard, nosdeputes:jean-raymond-hugonet, nosdeputes:joel-bigot, nosdeputes:marie-christine-chauvin, nosdeputes:thierry-cozic, nosdeputes:viviane-malet, nosdeputes:yannick-vaugrenard |

## Erreurs de lecture

Aucune erreur de lecture.

---

# Rapport d'audit du jeu de données groupes

Généré le 2026-08-18T06:44:21.242642+00:00. 7 groupe(s) analysé(s), 0 erreur(s) de lecture. Seuil de péremption des sources : 30 jour(s).

Ce rapport est un outil de qualité interne : il présente des indicateurs bruts, sans jugement de valeur ni classement.

## Volumétrie

### Effectifs (`effectif.actuel` / `min_historique` / `max_historique`)

| Champ | Groupes renseignés | Min | Max | Médiane | Moyenne |
| --- | --- | --- | --- | --- | --- |
| actuel | 7 | 0 | 23 | 2 | 5.57 |
| min_historique | 0 |  |  |  |  |
| max_historique | 0 |  |  |  |  |

### Cohésion de vote (nombre de scrutins recensés par groupe)

| Min | Max | Médiane | Moyenne | % groupes à 0 |
| --- | --- | --- | --- | --- |
| 0 | 4102 | 1996 | 1792.71 | 28.57 |

### Amendements agrégés (tous types de déposants confondus)

| Compteur | Min | Max | Médiane | Moyenne |
| --- | --- | --- | --- | --- |
| nb_amendements | 0 | 195718 | 13477 | 46590.43 |
| nb_adoptes | 0 | 40149 | 677 | 6775.29 |
| nb_rejetes | 0 | 45982 | 4488 | 13229 |
| nb_irrecevables | 0 | 29592 | 2162 | 7596.43 |
| nb_retires_ou_tombes | 0 | 51479 | 2825 | 11139.71 |

### Amendements agrégés par type de déposant

#### commission_rapporteur

| Compteur | Min | Max | Médiane | Moyenne |
| --- | --- | --- | --- | --- |
| nb_amendements | 0 | 4779 | 203 | 959.29 |
| nb_adoptes | 0 | 2858 | 38 | 518.14 |
| nb_rejetes | 0 | 563 | 88 | 164.14 |
| nb_irrecevables | 0 | 60 | 8 | 13.86 |
| nb_retires_ou_tombes | 0 | 876 | 28 | 165 |

#### depute

| Compteur | Min | Max | Médiane | Moyenne |
| --- | --- | --- | --- | --- |
| nb_amendements | 0 | 190939 | 13337 | 45631.14 |
| nb_adoptes | 0 | 37291 | 639 | 6257.14 |
| nb_rejetes | 0 | 45419 | 4400 | 13064.86 |
| nb_irrecevables | 0 | 29532 | 2157 | 7582.57 |
| nb_retires_ou_tombes | 0 | 50603 | 2797 | 10974.71 |

#### gouvernement

| Compteur | Min | Max | Médiane | Moyenne |
| --- | --- | --- | --- | --- |
| nb_amendements | 0 | 0 | 0 | 0 |
| nb_adoptes | 0 | 0 | 0 | 0 |
| nb_rejetes | 0 | 0 | 0 | 0 |
| nb_irrecevables | 0 | 0 | 0 | 0 |
| nb_retires_ou_tombes | 0 | 0 | 0 | 0 |

#### inconnu

| Compteur | Min | Max | Médiane | Moyenne |
| --- | --- | --- | --- | --- |
| nb_amendements | 0 | 0 | 0 | 0 |
| nb_adoptes | 0 | 0 | 0 | 0 |
| nb_rejetes | 0 | 0 | 0 | 0 |
| nb_irrecevables | 0 | 0 | 0 | 0 |
| nb_retires_ou_tombes | 0 | 0 | 0 | 0 |

## Tableau croisé des volumes par groupe

| groupe_id | Nom | Chambre | Membres | Cohésion de vote | Tags thématiques | Amendements |
| --- | --- | --- | --- | --- | --- | --- |
| AN:LFI | La France insoumise - NUPES | AN | 3 | 1996 | 0 | 11561 |
| AN:LR | Les Républicains | AN | 6 | 2232 | 0 | 42820 |
| Senat:LR | Les Républicains | Senat | 15 | 0 | 0 | 0 |
| AN:RN | Rassemblement National | AN | 9 | 3405 | 318 | 62557 |
| AN:REN | Renaissance | AN | 86 | 4102 | 0 | 195718 |
| Senat:SER | Socialiste, Écologiste et Républicain | Senat | 5 | 0 | 0 | 0 |
| AN:SOC | Socialistes et apparentés | AN | 1 | 814 | 179 | 13477 |

## Tableau croisé des plages temporelles par groupe

Complète (sans le remplacer) le tableau croisé des volumes ci-dessus : pour chaque groupe, la période couverte par les dates disponibles (min → max), plutôt que le nombre d'entrées.

| groupe_id | Nom | Chambre | Cohésion de vote (min → max) | Amendements agrégés |
| --- | --- | --- | --- | --- |
| AN:LFI | La France insoumise - NUPES | AN | 2022-07-11 → 2024-06-07 | N/A (non applicable) |
| AN:LR | Les Républicains | AN | 2022-07-11 → 2024-06-07 | N/A (non applicable) |
| Senat:LR | Les Républicains | Senat | N/D | N/A (non applicable) |
| AN:RN | Rassemblement National | AN | 2022-07-11 → 2024-06-07 | N/A (non applicable) |
| AN:REN | Renaissance | AN | 2017-11-09 → 2024-06-07 | N/A (non applicable) |
| Senat:SER | Socialiste, Écologiste et Républicain | Senat | N/D | N/A (non applicable) |
| AN:SOC | Socialistes et apparentés | AN | 2022-07-11 → 2024-06-07 | N/A (non applicable) |

> **`amendements_agreges`** : colonne marquée **N/A (non applicable)**, jamais une cellule vide silencieuse. `schema_groupe.py` ne stocke que des compteurs au niveau de l'agrégat (`nb_amendements`, `nb_adoptes`...), aucune date : c'est une limite structurelle du schéma actuel, pas une donnée manquante à corriger. Voir la section Hors périmètre de l'issue #316.

### Dates `cohesion_votes[].date` invalides ignorées pour le calcul (0)

Aucune date invalide détectée.

## Complétude

### Présence des tags thématiques agrégés

| Renseignés | Total | Taux (%) |
| --- | --- | --- |
| 2 | 7 | 28.57 |

### Groupes avec des membres mais sans `cohesion_votes`

2 / 7 groupe(s).

## Cohérence

### Validation du schéma (`validate_profil_groupe`)

Aucun groupe invalide détecté.

### Divergence `schema_version` / `meta.schema_version`

Aucune divergence détectée.

### Écart de couverture du roster

| groupe_id | Roster total | Profils disponibles | Écart | Taux de couverture (%) |
| --- | --- | --- | --- | --- |
| AN:LFI | 76 | 3 | 73 | 3.95 |
| AN:LR | 62 | 6 | 56 | 9.68 |
| AN:REN | 193 | 86 | 107 | 44.56 |
| AN:RN | 90 | 9 | 81 | 10.0 |
| AN:SOC | 31 | 1 | 30 | 3.23 |
| Senat:LR | 235 | 15 | 220 | 6.38 |
| Senat:SER | 65 | 5 | 60 | 7.69 |

### Doublons de `groupe_id`

Aucun doublon détecté.

## Fraîcheur

### Ancienneté des sources par type (jours écoulés depuis `synchro_le`)

| Type de source | Nombre de sources | Min | Max | Médiane | Moyenne |
| --- | --- | --- | --- | --- | --- |
| assemblee_nationale | 5 | 0 | 4 | 0 | 0.8 |
| europarl | 5 | 0 | 0 | 0 | 0 |
| nosdeputes | 45 | 0 | 11 | 4 | 3.84 |
| nossenateurs | 2 | 0 | 0 | 0.0 | 0 |

### Groupes périmés (toutes sources > 30 jours)

Aucun groupe périmé.

## Warnings

Total : 9

| Type | Fréquence | Groupes concernés |
| --- | --- | --- |
| couverture_roster_senat | 2 | Senat:LR, Senat:SER |
| fraicheur_donnees | 7 | AN:LFI, AN:LR, AN:REN, AN:RN, AN:SOC, Senat:LR, Senat:SER |

## Erreurs de lecture

Aucune erreur de lecture.

---

# Rapport d'audit du jeu de données gouvernements

Généré le 2026-08-18T06:44:21.242642+00:00. 10 gouvernement(s) analysé(s), 0 erreur(s) de lecture. Seuil de péremption des sources : 30 jour(s).

Couverture des textes portés : **législatures XV–XVII (dossiers déposés à partir du 2017-06-21)** — au-delà de cette borne, un `textes[]` vide est une absence de source, pas un zéro constaté (#399).

Ce rapport est un outil de qualité interne : il présente des indicateurs bruts, sans jugement de valeur ni classement.

## Volumétrie

### Répartition par `periode.actif`

| Total | Actifs | Inactifs | Indéterminés |
| --- | --- | --- | --- |
| 10 | 1 | 9 | 0 |

### Distribution du nombre de `membres` / `textes` par gouvernement

| Champ | Min | Max | Médiane | Moyenne |
| --- | --- | --- | --- | --- |
| membres | 1 | 16 | 5.0 | 5.7 |
| textes | 0 | 282 | 30.0 | 72.5 |

### Comptages agrégés par statut de texte (`comptages.par_statut`)

| Statut | Total |
| --- | --- |
| adopte | 188 |
| adopte_49_3 | 9 |
| adopte_cmp | 111 |
| depose | 0 |
| navette_en_cours | 335 |
| promulgue | 67 |
| rejete | 9 |
| rejete_49_3 | 0 |
| retire | 6 |

## Couverture des textes portés

Archives de dossiers ingérées : **législatures XV–XVII (dossiers déposés à partir du 2017-06-21)**.

Un gouvernement dont la période est antérieure à cette borne n'a pas « zéro texte porté » : la source ne le couvre pas. Les deux cas sont distingués ci-dessous et ne doivent jamais être confondus (AGENTS.md §2.5). `Textes = N/D` signale un champ `textes` absent ou `null`, jamais transformé en `0`.

Couverte : 6 · partielle : 1 · hors couverture : 3 · indéterminée : 0

| gouvernement_id | Nom | Période | Couverture source | Textes |
| --- | --- | --- | --- | --- |
| gouvernement:ATTAL | Gouvernement Attal | 2024-01-10 → 2024-09-05 | couverte | 25 |
| gouvernement:BARNIER | Gouvernement Barnier | 2024-09-28 → 2024-12-13 | couverte | 13 |
| gouvernement:BAYROU | Gouvernement Bayrou | 2024-12-24 → 2025-09-09 | couverte | 35 |
| gouvernement:BORNE | Gouvernement Borne | 2022-05-21 → 2024-01-09 | couverte | 111 |
| gouvernement:CASTEX | Gouvernement Castex | 2020-07-07 → 2022-05-16 | couverte | 195 |
| gouvernement:FILLON_2 | Gouvernement Fillon II | 2007-06-19 → 2010-11-13 | hors couverture | 0 |
| gouvernement:FILLON_3 | Gouvernement Fillon III | 2010-11-14 → 2012-05-10 | hors couverture | 0 |
| gouvernement:LECORNU_II | Gouvernement Lecornu II | 2025-10-13 → en cours | couverte | 63 |
| gouvernement:PHILIPPE | Gouvernement Philippe I | 2017-05-18 → 2017-06-19 | hors couverture | 1 |
| gouvernement:PHILIPPE_2 | Gouvernement Philippe II | 2017-06-20 → 2020-07-06 | partielle | 282 |

### Sans texte, dans la couverture (0)

Zéro réellement constaté : la source couvre la période et n'y rattache aucun texte — anomalie à instruire.

Aucun gouvernement sans texte dans la couverture.

### Sans texte, hors couverture (2)

Absence de source, pas un fait mesuré : aucune conclusion ne peut en être tirée, et rien ne doit être publié comme un zéro.

| gouvernement_id |
| --- |
| gouvernement:FILLON_2 |
| gouvernement:FILLON_3 |

## Tableau croisé des plages temporelles par gouvernement

Pour chaque gouvernement, la période couverte par les dates disponibles (min → max) des mandats de ses membres et des textes qu'il a portés.

| gouvernement_id | Nom | Mandats membres (min → max) | Textes (min → max) |
| --- | --- | --- | --- |
| gouvernement:ATTAL | Gouvernement Attal | 2024-01-10 → 2024-09-05 | 2024-01-17 → 2026-05-26 |
| gouvernement:BARNIER | Gouvernement Barnier | 2024-09-22 → 2024-12-13 | 2024-10-01 → 2026-01-29 |
| gouvernement:BAYROU | Gouvernement Bayrou | 2024-12-24 → 2025-09-09 | 2025-01-08 → 2026-07-01 |
| gouvernement:BORNE | Gouvernement Borne | 2022-05-21 → 2024-01-09 | 2022-06-01 → 2025-09-30 |
| gouvernement:CASTEX | Gouvernement Castex | 2020-07-07 → 2022-05-16 | 2020-07-07 → 2023-06-02 |
| gouvernement:FILLON_2 | Gouvernement Fillon II | 2007-06-19 → 2010-11-13 | N/D (hors couverture) |
| gouvernement:FILLON_3 | Gouvernement Fillon III | 2010-11-14 → 2012-05-10 | N/D (hors couverture) |
| gouvernement:LECORNU_II | Gouvernement Lecornu II | 2025-10-13 → 2026-02-26 | 2025-10-14 → 2026-09-16 |
| gouvernement:PHILIPPE | Gouvernement Philippe I | 2017-05-18 → 2017-06-19 | 2017-06-14 → 2017-09-15 |
| gouvernement:PHILIPPE_2 | Gouvernement Philippe II | 2017-06-20 → 2020-07-06 | 2017-06-22 → 2024-03-21 |

> **`Textes`** : un `N/D (hors couverture)` signale une période hors du périmètre des archives ingérées, pas une absence de texte constatée — voir la section « Couverture des textes portés ».

> **`mandats_membres`** : calculée sur `membres[].debut`/`.fin`. Un `fin = null` signale un mandat en cours — exclu du calcul sans jamais être remplacé par la date du jour (AGENTS.md §2.5).

### Dates `membres[]`/`textes[]` invalides ignorées pour le calcul (0)

Aucune date invalide détectée.

## Complétude

### Présence d'un `premier_ministre` renseigné

| Renseignés | Total | Taux (%) |
| --- | --- | --- |
| 3 | 10 | 30.0 |

### Taux de `membres[].portefeuille` renseigné

| Renseignés | Total | Taux (%) |
| --- | --- | --- |
| 40 | 57 | 70.18 |

### Présence d'un bloc `meta` renseigné

| Renseignés | Total | Taux (%) |
| --- | --- | --- |
| 10 | 10 | 100.0 |

## Cohérence

### Validation du schéma (`validate_profil_gouvernement`)

Aucun gouvernement invalide détecté.

### Divergence `schema_version` / `meta.schema_version`

Aucune divergence détectée.

### Doublons de `gouvernement_id`

Aucun doublon détecté.

## Fraîcheur

### Ancienneté des sources par type (jours écoulés depuis `synchro_le`)

| Type de source | Nombre de sources | Min | Max | Médiane | Moyenne |
| --- | --- | --- | --- | --- | --- |
| assemblee_nationale | 10 | 0 | 3 | 0.0 | 0.9 |
| europarl | 1 | 0 | 0 | 0 | 0 |
| nosdeputes | 31 | 0 | 11 | 4 | 4.71 |
| nossenateurs | 2 | 0 | 0 | 0.0 | 0 |

### Gouvernements périmés (toutes sources > 30 jours)

Aucun gouvernement périmé.

## Warnings

Total : 0

Aucun warning.

## Erreurs de lecture

Aucune erreur de lecture.
