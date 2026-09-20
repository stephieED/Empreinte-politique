# Rapport d'audit pipeline (profils + groupes + gouvernements)

Généré le 2026-08-18T06:35:07.166275+00:00. Seuil de péremption des sources : 30 jour(s).

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

Généré le 2026-08-18T06:35:07.166275+00:00. 129 profil(s) analysé(s), 0 erreur(s) de lecture. Seuil de péremption des sources : 30 jour(s).

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

### Distribution des listes métier (par profil)

| Champ | Min | Max | Médiane | Moyenne | % profils à 0 |
| --- | --- | --- | --- | --- | --- |
| votes | 0 | 5697 | 1026 | 1133.53 | 16.28 |
| textes_portes | 0 | 283 | 0 | 3.4 | 83.72 |
| amendements | 0 | 13477 | 2004 | 2634.68 | 37.21 |
| interventions | 0 | 395 | 0 | 6.12 | 95.35 |

### Sources déclarées

| Moyenne de sources par profil | % profils à une seule source |
| --- | --- |
| 1.91 | 14.73 |

## Tableau croisé des volumes par candidat

| id | Nom | Chambre | Votes | Textes portés | Amendements | Interventions |
| --- | --- | --- | --- | --- | --- | --- |
| nosdeputes:anne-genetet | Anne Genetet | AN | 1595 | 0 | 3103 | 0 |
| nosdeputes:anne-sophie-frigout | Anne-Sophie Frigout | AN | 427 | 0 | 1779 | 0 |
| nosdeputes:annie-vidal | Annie Vidal | AN | 1422 | 2 | 0 | 0 |
| nosdeputes:antoine-villedieu | Antoine Villedieu | AN | 1041 | 0 | 5778 | 0 |
| nosdeputes:benjamin-dirx | Benjamin Dirx | AN | 2382 | 0 | 3288 | 0 |
| nosdeputes:benjamin-haddad | Benjamin Haddad | AN | 1163 | 0 | 0 | 0 |
| nosdeputes:benoit-mournet | Benoit Mournet | AN | 1445 | 0 | 0 | 0 |
| nosdeputes:brigitte-klinkert | Brigitte Klinkert | AN | 3395 | 0 | 2366 | 0 |
| nosdeputes:bruno-bilde | Bruno Bilde | AN | 702 | 0 | 6383 | 0 |
| nosdeputes:bruno-retailleau | Bruno Retailleau | AN | 0 | 36 | 0 | 0 |
| nosdeputes:bruno-studer | Bruno Studer | AN | 1327 | 0 | 0 | 0 |
| nosdeputes:beatrice-piron | Béatrice Piron | AN | 1921 | 0 | 0 | 0 |
| nosdeputes:carole-grandjean | Carole Grandjean | AN | 9 | 0 | 2404 | 0 |
| nosdeputes:caroline-abadie | Caroline Abadie | AN | 1402 | 0 | 2391 | 0 |
| nosdeputes:catherine-belrhiti | Catherine Belrhiti | AN | 0 | 0 | 0 | 0 |
| nosdeputes:catherine-deroche | Catherine Deroche | AN | 0 | 0 | 0 | 0 |
| nosdeputes:catherine-dumas | Catherine Dumas | AN | 0 | 0 | 0 | 0 |
| nosdeputes:catherine-procaccia | Catherine Procaccia | AN | 0 | 0 | 0 | 0 |
| nosdeputes:charles-guene | Charles Guené | AN | 0 | 0 | 0 | 0 |
| nosdeputes:charlotte-parmentier-lecocq | Charlotte Parmentier-Lecocq | AN | 1205 | 1 | 0 | 0 |
| nosdeputes:christine-decodts | Christine Decodts | AN | 1846 | 0 | 1858 | 0 |
| nosdeputes:christine-le-nabour | Christine Le Nabour | AN | 2178 | 0 | 3618 | 0 |
| nosdeputes:christophe-bentz | Christophe Bentz | AN | 2480 | 0 | 10149 | 0 |
| nosdeputes:christophe-marion | Christophe Marion | AN | 1885 | 0 | 3375 | 0 |
| nosdeputes:claude-raynal | Claude Raynal | AN | 0 | 0 | 0 | 0 |
| nosdeputes:corinne-vignon | Corinne Vignon | AN | 1434 | 0 | 3851 | 0 |
| nosdeputes:celine-calvez | Céline Calvez | AN | 1144 | 0 | 3552 | 0 |
| nosdeputes:damien-abad | Damien Abad | AN | 257 | 0 | 10474 | 0 |
| nosdeputes:danielle-brulebois | Danielle Brulebois | AN | 1829 | 0 | 7740 | 0 |
| nosdeputes:david-amiel | David Amiel | AN | 1594 | 4 | 0 | 0 |
| nosdeputes:david-valence | David Valence | AN | 2281 | 0 | 0 | 0 |
| nosdeputes:dominique-da-silva | Dominique Da Silva | AN | 1547 | 0 | 0 | 0 |
| nosdeputes:dominique-faure | Dominique Faure | AN | 1 | 0 | 0 | 0 |
| nosdeputes:dominique-de-legge | Dominique de Legge | AN | 0 | 0 | 0 | 0 |
| nosdeputes:emmanuel-pellerin | Emmanuel Pellerin | AN | 2642 | 0 | 0 | 0 |
| nosdeputes:emmanuel-tache-de-la-pagerie | Emmanuel Taché de la Pagerie | AN | 832 | 0 | 5861 | 0 |
| nosdeputes:fabien-di-filippo | Fabien Di Filippo | AN | 630 | 0 | 6880 | 0 |
| nosdeputes:fadila-khattabi | Fadila Khattabi | AN | 820 | 0 | 2527 | 0 |
| nosdeputes:florent-boudie | Florent Boudié | AN | 853 | 0 | 4359 | 0 |
| nosdeputes:franck-riester | Franck Riester | AN | 938 | 0 | 3371 | 0 |
| nosdeputes:francois-cormier-bouligeon | François Cormier-Bouligeon | AN | 923 | 0 | 3188 | 0 |
| nosdeputes:francoise-buffet | Françoise Buffet | AN | 1420 | 0 | 1769 | 0 |
| nosdeputes:frederic-descrozaille | Frédéric Descrozaille | AN | 1242 | 0 | 2425 | 0 |
| nosdeputes:gabriel-attal | Gabriel Attal | AN | 2035 | 34 | 1074 | 5 |
| nosdeputes:gilles-le-gendre | Gilles Le Gendre | AN | 2585 | 0 | 2907 | 0 |
| nosdeputes:graziella-melchior | Graziella Melchior | AN | 1345 | 0 | 3698 | 0 |
| nosdeputes:guillaume-vuilletet | Guillaume Vuilletet | AN | 522 | 0 | 0 | 0 |
| nosdeputes:gerard-larcher | Gérard Larcher | AN | 0 | 0 | 0 | 0 |
| nosdeputes:hadrien-ghomi | Hadrien Ghomi | AN | 1135 | 0 | 1898 | 0 |
| nosdeputes:herve-berville | Hervé Berville | AN | 2446 | 0 | 2297 | 0 |
| nosdeputes:hussein-bourgi | Hussein Bourgi | AN | 0 | 0 | 0 | 0 |
| nosdeputes:jean-terlier | Jean Terlier | AN | 1260 | 0 | 3979 | 0 |
| nosdeputes:jean-carles-grelier | Jean-Carles Grelier | AN | 253 | 0 | 3961 | 0 |
| nosdeputes:jean-francois-lovisolo | Jean-François Lovisolo | AN | 973 | 0 | 1270 | 0 |
| nosdeputes:jean-francois-rousset | Jean-François Rousset | AN | 5697 | 0 | 3050 | 0 |
| nosdeputes:jean-jacques-panunzi | Jean-Jacques Panunzi | AN | 0 | 0 | 0 | 0 |
| nosdeputes:jean-luc-bourgeaux | Jean-Luc Bourgeaux | AN | 768 | 0 | 8476 | 0 |
| nosdeputes:jean-luc-melenchon | Jean-Luc Mélenchon | AN | 1016 | 0 | 11043 | 15 |
| nosdeputes:jean-marc-zulesi | Jean-Marc Zulesi | AN | 1195 | 0 | 0 | 0 |
| nosdeputes:jean-michel-jacques | Jean-Michel Jacques | AN | 777 | 2 | 0 | 0 |
| nosdeputes:jean-philippe-ardouin | Jean-Philippe Ardouin | AN | 959 | 0 | 3910 | 0 |
| nosdeputes:jean-pierre-bansard | Jean-Pierre Bansard | AN | 0 | 0 | 0 | 0 |
| nosdeputes:jean-pierre-vigier | Jean-Pierre Vigier | AN | 728 | 0 | 11300 | 0 |
| nosdeputes:jean-raymond-hugonet | Jean-Raymond Hugonet | AN | 0 | 0 | 0 | 0 |
| nosdeputes:jean-rene-cazeneuve | Jean-René Cazeneuve | AN | 1778 | 0 | 4692 | 0 |
| europarl:131580 | Jordan BARDELLA | PE | 0 | 0 | 0 | 0 |
| nosdeputes:joel-bigot | Joël Bigot | AN | 0 | 0 | 0 | 0 |
| nosdeputes:julie-delpech | Julie Delpech | AN | 3001 | 0 | 2810 | 0 |
| nosdeputes:julien-odoul | Julien Odoul | AN | 645 | 0 | 9058 | 0 |
| nosdeputes:julien-rancoule | Julien Rancoule | AN | 1638 | 0 | 5240 | 0 |
| nosdeputes:jerome-guedj | Jérôme Guedj | AN | 2906 | 5 | 13477 | 395 |
| nosdeputes:karl-olive | Karl Olive | AN | 727 | 0 | 1825 | 0 |
| nosdeputes:laurence-maillart-mehaignerie | Laurence Maillart-Méhaignerie | AN | 773 | 0 | 2772 | 0 |
| nosdeputes:laurent-wauquiez | Laurent Wauquiez | AN | 826 | 9 | 1949 | 22 |
| nosdeputes:lionel-vuibert | Lionel Vuibert | AN | 2560 | 0 | 2404 | 0 |
| nosdeputes:ludovic-mendes | Ludovic Mendes | AN | 591 | 6 | 0 | 0 |
| nosdeputes:lysiane-metayer | Lysiane Métayer | AN | 1575 | 0 | 2031 | 0 |
| nosdeputes:marie-guevenoux | Marie Guévenoux | AN | 740 | 0 | 2247 | 0 |
| nosdeputes:marie-christine-chauvin | Marie-Christine Chauvin | AN | 0 | 0 | 0 | 0 |
| nosdeputes:marie-pierre-rixain | Marie-Pierre Rixain | AN | 282 | 0 | 3247 | 0 |
| nosdeputes:marine-le-pen | Marine Le Pen | AN | 1813 | 23 | 13094 | 302 |
| nosdeputes:marjolaine-meynier-millefert | Marjolaine Meynier-Millefert | AN | 1420 | 0 | 0 | 0 |
| nosdeputes:martine-etienne | Martine Etienne | AN | 1102 | 0 | 11561 | 0 |
| nosdeputes:mathieu-lefevre | Mathieu Lefèvre | AN | 3473 | 0 | 2269 | 0 |
| nosdeputes:maud-bregeon | Maud Bregeon | AN | 758 | 0 | 1131 | 0 |
| nosdeputes:maxime-minot | Maxime Minot | AN | 1250 | 0 | 4813 | 0 |
| nosdeputes:michael-taverne | Michaël Taverne | AN | 1009 | 0 | 5215 | 0 |
| nosdeputes:michel-lauzzana | Michel Lauzzana | AN | 1264 | 0 | 3483 | 0 |
| nosdeputes:mikaele-seo | Mikaele Seo | AN | 985 | 0 | 1696 | 0 |
| nosdeputes:nicole-le-peih | Nicole Le Peih | AN | 1561 | 0 | 3958 | 0 |
| nosdeputes:olivier-dussopt | Olivier Dussopt | AN | 26 | 1 | 0 | 0 |
| nosdeputes:olivier-veran | Olivier Véran | AN | 18 | 0 | 2174 | 0 |
| nosdeputes:pascal-lavergne | Pascal Lavergne | AN | 1510 | 0 | 1859 | 0 |
| nosdeputes:pascale-boyer | Pascale Boyer | AN | 1407 | 0 | 0 | 0 |
| nosdeputes:patrick-vignal | Patrick Vignal | AN | 265 | 0 | 0 | 0 |
| nosdeputes:philippe-dunoyer | Philippe Dunoyer | AN | 1355 | 0 | 0 | 0 |
| nosdeputes:philippe-juvin | Philippe Juvin | AN | 698 | 0 | 4959 | 0 |
| nosdeputes:pierre-cazeneuve | Pierre Cazeneuve | AN | 1759 | 6 | 0 | 0 |
| nosdeputes:pieyre-alexandre-anglade | Pieyre-Alexandre Anglade | AN | 833 | 0 | 0 | 0 |
| nosdeputes:prisca-thevenot | Prisca Thevenot | AN | 3962 | 0 | 1775 | 0 |
| nosdeputes:quentin-bataillon | Quentin Bataillon | AN | 1105 | 0 | 901 | 0 |
| nosdeputes:rene-pilato | René Pilato | AN | 1136 | 0 | 0 | 0 |
| nosdeputes:rodrigo-arenas | Rodrigo Arenas | AN | 564 | 0 | 0 | 0 |
| nosdeputes:roland-lescure | Roland Lescure | AN | 2498 | 0 | 2645 | 0 |
| nosdeputes:sandra-marsaud | Sandra Marsaud | AN | 1233 | 0 | 4264 | 0 |
| nosdeputes:sandrine-le-feur | Sandrine Le Feur | AN | 3812 | 0 | 6029 | 0 |
| nosdeputes:sophie-errante | Sophie Errante | AN | 602 | 1 | 2766 | 0 |
| nosdeputes:sophie-panonacle | Sophie Panonacle | AN | 812 | 3 | 0 | 0 |
| nosdeputes:stella-dupont | Stella Dupont | AN | 1061 | 1 | 5063 | 0 |
| nossenateurs:stephane-mazars | Stéphane Mazars | Senat | 882 | 6 | 0 | 0 |
| nosdeputes:stephane-travert | Stéphane Travert | AN | 3480 | 0 | 7186 | 0 |
| nosdeputes:stephanie-rist | Stéphanie Rist | AN | 1048 | 0 | 3559 | 0 |
| nosdeputes:thierry-cozic | Thierry Cozic | AN | 0 | 0 | 0 | 0 |
| nosdeputes:thomas-cazenave | Thomas Cazenave | AN | 734 | 7 | 1090 | 0 |
| nosdeputes:thomas-gassilloud | Thomas Gassilloud | AN | 1682 | 0 | 2639 | 0 |
| nosdeputes:thomas-rudigoz | Thomas Rudigoz | AN | 1066 | 0 | 3187 | 0 |
| nosdeputes:vincent-rolland | Vincent Rolland | AN | 298 | 0 | 6392 | 0 |
| nosdeputes:viviane-malet | Viviane Malet | AN | 0 | 0 | 0 | 0 |
| nosdeputes:veronique-riotton | Véronique Riotton | AN | 1026 | 0 | 5583 | 0 |
| nosdeputes:xavier-roseren | Xavier Roseren | AN | 1044 | 2 | 4006 | 0 |
| nosdeputes:yannick-chenevard | Yannick Chenevard | AN | 1363 | 3 | 0 | 0 |
| nosdeputes:yannick-haury | Yannick Haury | AN | 1223 | 0 | 6652 | 0 |
| nosdeputes:yannick-vaugrenard | Yannick Vaugrenard | AN | 0 | 0 | 0 | 0 |
| nosdeputes:yael-braun-pivet | Yaël Braun-Pivet | AN | 356 | 4 | 2004 | 0 |
| nosdeputes:edouard-philippe | Édouard Philippe | AN | 141 | 283 | 749 | 50 |
| nosdeputes:emilie-chandler | Émilie Chandler | AN | 1811 | 0 | 1435 | 0 |
| nosdeputes:eric-dolige | Éric Doligé | AN | 0 | 0 | 0 | 0 |
| nosdeputes:eric-poulliat | Éric Poulliat | AN | 833 | 0 | 2633 | 0 |
| nosdeputes:evelyne-renaud-garabedian | Évelyne Renaud-Garabedian | AN | 0 | 0 | 0 | 0 |

## Plages temporelles par candidat

| id | Nom | Chambre | Votes | Textes portés | Amendements | Interventions |
| --- | --- | --- | --- | --- | --- | --- |
| nosdeputes:anne-genetet | Anne Genetet | AN | 2022-07-11 → 2024-05-28 | — | 2017-07-21 → 2026-07-10 | — |
| nosdeputes:anne-sophie-frigout | Anne-Sophie Frigout | AN | 2022-07-11 → 2022-12-01 | — | 2022-07-15 → 2024-05-23 | — |
| nosdeputes:annie-vidal | Annie Vidal | AN | 2022-07-11 → 2024-06-07 | 2025-03-11 → 2026-05-26 | — | — |
| nosdeputes:antoine-villedieu | Antoine Villedieu | AN | 2022-07-11 → 2024-06-06 | — | 2022-07-15 → 2024-06-08 | — |
| nosdeputes:benjamin-dirx | Benjamin Dirx | AN | 2017-07-04 → 2026-07-21 | — | 2017-07-17 → 2026-07-10 | — |
| nosdeputes:benjamin-haddad | Benjamin Haddad | AN | 2022-07-11 → 2024-06-05 | — | — | — |
| nosdeputes:benoit-mournet | Benoit Mournet | AN | 2022-07-11 → 2024-06-06 | — | — | — |
| nosdeputes:brigitte-klinkert | Brigitte Klinkert | AN | 2022-07-11 → 2026-07-21 | — | 2022-07-09 → 2026-07-10 | — |
| nosdeputes:bruno-bilde | Bruno Bilde | AN | 2022-07-12 → 2024-06-04 | — | 2017-07-21 → 2024-06-08 | — |
| nosdeputes:bruno-retailleau | Bruno Retailleau | AN | — | 2010-12-14 → 2026-05-06 | — | — |
| nosdeputes:bruno-studer | Bruno Studer | AN | 2022-07-12 → 2024-06-05 | — | — | — |
| nosdeputes:beatrice-piron | Béatrice Piron | AN | 2022-07-11 → 2024-06-07 | — | — | — |
| nosdeputes:carole-grandjean | Carole Grandjean | AN | 2022-07-11 → 2024-03-12 | — | 2017-07-07 → 2024-03-21 | — |
| nosdeputes:caroline-abadie | Caroline Abadie | AN | 2022-07-11 → 2024-05-30 | — | 2017-07-21 → 2024-05-31 | — |
| nosdeputes:catherine-belrhiti | Catherine Belrhiti | AN | — | — | — | — |
| nosdeputes:catherine-deroche | Catherine Deroche | AN | — | — | — | — |
| nosdeputes:catherine-dumas | Catherine Dumas | AN | — | — | — | — |
| nosdeputes:catherine-procaccia | Catherine Procaccia | AN | — | — | — | — |
| nosdeputes:charles-guene | Charles Guené | AN | — | — | — | — |
| nosdeputes:charlotte-parmentier-lecocq | Charlotte Parmentier-Lecocq | AN | 2022-07-11 → 2024-06-07 | 2020-12-23 → 2025-02-19 | — | — |
| nosdeputes:christine-decodts | Christine Decodts | AN | 2022-07-11 → 2024-06-05 | — | 2022-07-09 → 2024-06-07 | — |
| nosdeputes:christine-le-nabour | Christine Le Nabour | AN | 2022-07-11 → 2024-06-05 | — | 2017-07-07 → 2026-07-10 | — |
| nosdeputes:christophe-bentz | Christophe Bentz | AN | 2022-07-11 → 2024-06-07 | — | 2022-07-09 → 2026-07-16 | — |
| nosdeputes:christophe-marion | Christophe Marion | AN | 2022-07-11 → 2024-06-07 | — | 2022-07-09 → 2026-07-10 | — |
| nosdeputes:claude-raynal | Claude Raynal | AN | — | — | — | — |
| nosdeputes:corinne-vignon | Corinne Vignon | AN | 2022-07-11 → 2024-06-06 | — | 2017-07-07 → 2026-07-10 | — |
| nosdeputes:celine-calvez | Céline Calvez | AN | 2022-07-11 → 2024-06-07 | — | 2017-07-21 → 2026-07-10 | — |
| nosdeputes:damien-abad | Damien Abad | AN | 2022-07-25 → 2024-05-28 | — | 2012-07-12 → 2024-05-28 | — |
| nosdeputes:danielle-brulebois | Danielle Brulebois | AN | 2022-07-12 → 2024-06-06 | — | 2017-07-11 → 2026-07-10 | — |
| nosdeputes:david-amiel | David Amiel | AN | 2022-07-12 → 2024-06-06 | 2024-07-20 → 2026-06-29 | — | — |
| nosdeputes:david-valence | David Valence | AN | 2022-07-11 → 2024-06-06 | — | — | — |
| nosdeputes:dominique-da-silva | Dominique Da Silva | AN | 2022-07-13 → 2024-06-05 | — | — | — |
| nosdeputes:dominique-faure | Dominique Faure | AN | 2022-07-11 → 2022-07-11 | — | — | — |
| nosdeputes:dominique-de-legge | Dominique de Legge | AN | — | — | — | — |
| nosdeputes:emmanuel-pellerin | Emmanuel Pellerin | AN | 2022-07-12 → 2024-06-07 | — | — | — |
| nosdeputes:emmanuel-tache-de-la-pagerie | Emmanuel Taché de la Pagerie | AN | 2022-07-11 → 2024-06-04 | — | 2022-07-09 → 2024-06-08 | — |
| nosdeputes:fabien-di-filippo | Fabien Di Filippo | AN | 2022-07-12 → 2024-06-06 | — | 2017-07-17 → 2026-07-10 | — |
| nosdeputes:fadila-khattabi | Fadila Khattabi | AN | 2022-07-11 → 2023-07-19 | — | 2017-07-07 → 2024-05-21 | — |
| nosdeputes:florent-boudie | Florent Boudié | AN | 2022-07-11 → 2024-06-04 | — | 2012-07-12 → 2024-05-31 | — |
| nosdeputes:franck-riester | Franck Riester | AN | 2012-07-03 → 2026-04-14 | — | 2012-07-12 → 2026-07-10 | — |
| nosdeputes:francois-cormier-bouligeon | François Cormier-Bouligeon | AN | 2022-07-12 → 2024-06-07 | — | 2017-07-21 → 2024-05-28 | — |
| nosdeputes:francoise-buffet | Françoise Buffet | AN | 2022-07-11 → 2024-06-05 | — | 2022-07-09 → 2026-07-15 | — |
| nosdeputes:frederic-descrozaille | Frédéric Descrozaille | AN | 2022-07-11 → 2024-06-05 | — | 2017-07-21 → 2024-06-08 | — |
| nosdeputes:gabriel-attal | Gabriel Attal | AN | 2017-07-04 → 2026-07-21 | 2017-11-21 → 2026-05-26 | 2017-10-05 → 2026-07-10 | — |
| nosdeputes:gilles-le-gendre | Gilles Le Gendre | AN | 2017-07-04 → 2024-06-07 | — | 2017-07-21 → 2024-06-01 | — |
| nosdeputes:graziella-melchior | Graziella Melchior | AN | 2022-07-12 → 2024-05-29 | — | 2017-07-21 → 2024-05-23 | — |
| nosdeputes:guillaume-vuilletet | Guillaume Vuilletet | AN | 2022-07-12 → 2024-05-28 | — | — | — |
| nosdeputes:gerard-larcher | Gérard Larcher | AN | — | — | — | — |
| nosdeputes:hadrien-ghomi | Hadrien Ghomi | AN | 2022-07-11 → 2024-06-07 | — | 2022-07-09 → 2024-05-28 | — |
| nosdeputes:herve-berville | Hervé Berville | AN | 2017-07-04 → 2026-07-21 | — | 2017-07-21 → 2026-07-10 | — |
| nosdeputes:hussein-bourgi | Hussein Bourgi | AN | — | — | — | — |
| nosdeputes:jean-terlier | Jean Terlier | AN | 2022-07-11 → 2024-06-05 | — | 2017-07-21 → 2026-07-10 | — |
| nosdeputes:jean-carles-grelier | Jean-Carles Grelier | AN | 2022-07-12 → 2024-05-14 | — | 2017-07-21 → 2024-06-01 | — |
| nosdeputes:jean-francois-lovisolo | Jean-François Lovisolo | AN | 2022-07-11 → 2024-06-05 | — | 2022-07-09 → 2024-06-07 | — |
| nosdeputes:jean-francois-rousset | Jean-François Rousset | AN | 2022-07-11 → 2026-07-21 | — | 2022-07-09 → 2026-07-10 | — |
| nosdeputes:jean-jacques-panunzi | Jean-Jacques Panunzi | AN | — | — | — | — |
| nosdeputes:jean-luc-bourgeaux | Jean-Luc Bourgeaux | AN | 2022-07-12 → 2024-06-05 | — | 2017-07-07 → 2024-06-08 | — |
| nosdeputes:jean-luc-melenchon | Jean-Luc Mélenchon | AN | 2017-07-04 → 2022-01-13 | — | 2017-07-11 → 2022-02-03 | — |
| nosdeputes:jean-marc-zulesi | Jean-Marc Zulesi | AN | 2022-07-11 → 2024-06-05 | — | — | — |
| nosdeputes:jean-michel-jacques | Jean-Michel Jacques | AN | 2022-07-12 → 2024-05-28 | 2022-12-14 → 2025-09-30 | — | — |
| nosdeputes:jean-philippe-ardouin | Jean-Philippe Ardouin | AN | 2022-07-12 → 2024-06-05 | — | 2017-07-21 → 2024-06-01 | — |
| nosdeputes:jean-pierre-bansard | Jean-Pierre Bansard | AN | — | — | — | — |
| nosdeputes:jean-pierre-vigier | Jean-Pierre Vigier | AN | 2022-07-11 → 2024-06-04 | — | 2012-07-12 → 2024-06-08 | — |
| nosdeputes:jean-raymond-hugonet | Jean-Raymond Hugonet | AN | — | — | — | — |
| nosdeputes:jean-rene-cazeneuve | Jean-René Cazeneuve | AN | 2022-07-11 → 2024-05-30 | — | 2017-07-21 → 2026-07-16 | — |
| europarl:131580 | Jordan BARDELLA | PE | — | — | — | — |
| nosdeputes:joel-bigot | Joël Bigot | AN | — | — | — | — |
| nosdeputes:julie-delpech | Julie Delpech | AN | 2022-07-11 → 2026-07-21 | — | 2022-07-09 → 2026-07-10 | — |
| nosdeputes:julien-odoul | Julien Odoul | AN | 2022-07-11 → 2024-06-06 | — | 2022-07-15 → 2026-07-16 | — |
| nosdeputes:julien-rancoule | Julien Rancoule | AN | 2022-07-11 → 2024-06-06 | — | 2022-07-15 → 2024-06-08 | — |
| nosdeputes:jerome-guedj | Jérôme Guedj | AN | 2012-10-09 → 2026-07-21 | 2022-09-15 → 2025-12-10 | 2012-07-12 → 2026-07-10 | 2022-07-11 → 2026-07-07 |
| nosdeputes:karl-olive | Karl Olive | AN | 2022-07-11 → 2024-06-04 | — | 2022-07-09 → 2026-07-10 | — |
| nosdeputes:laurence-maillart-mehaignerie | Laurence Maillart-Méhaignerie | AN | 2022-07-11 → 2024-06-07 | — | 2017-07-11 → 2024-06-07 | — |
| nosdeputes:laurent-wauquiez | Laurent Wauquiez | AN | 2012-07-03 → 2026-07-21 | 2024-10-15 → 2026-02-03 | 2012-07-12 → 2026-07-10 | 2025-07-22 → 2026-04-21 |
| nosdeputes:lionel-vuibert | Lionel Vuibert | AN | 2022-07-11 → 2026-07-21 | — | 2022-07-09 → 2026-07-10 | — |
| nosdeputes:ludovic-mendes | Ludovic Mendes | AN | 2022-07-11 → 2024-06-05 | 2024-10-02 → 2025-05-13 | — | — |
| nosdeputes:lysiane-metayer | Lysiane Métayer | AN | 2022-07-11 → 2024-06-07 | — | 2022-07-09 → 2024-05-28 | — |
| nosdeputes:marie-guevenoux | Marie Guévenoux | AN | 2022-07-11 → 2024-02-06 | — | 2017-07-21 → 2024-05-31 | — |
| nosdeputes:marie-christine-chauvin | Marie-Christine Chauvin | AN | — | — | — | — |
| nosdeputes:marie-pierre-rixain | Marie-Pierre Rixain | AN | 2022-07-12 → 2024-06-07 | — | 2017-07-21 → 2026-07-15 | — |
| nosdeputes:marine-le-pen | Marine Le Pen | AN | 2017-07-04 → 2026-07-21 | 2017-10-13 → 2024-01-25 | 2017-07-21 → 2026-07-16 | 2022-07-06 → 2025-12-30 |
| nosdeputes:marjolaine-meynier-millefert | Marjolaine Meynier-Millefert | AN | 2022-07-11 → 2024-06-05 | — | — | — |
| nosdeputes:martine-etienne | Martine Etienne | AN | 2022-07-11 → 2024-06-03 | — | 2022-07-05 → 2024-06-07 | — |
| nosdeputes:mathieu-lefevre | Mathieu Lefèvre | AN | 2022-07-11 → 2025-11-12 | — | 2022-07-09 → 2026-07-10 | — |
| nosdeputes:maud-bregeon | Maud Bregeon | AN | 2022-07-11 → 2024-05-29 | — | 2022-07-09 → 2026-07-10 | — |
| nosdeputes:maxime-minot | Maxime Minot | AN | 2022-07-11 → 2024-06-05 | — | 2017-07-21 → 2024-06-07 | — |
| nosdeputes:michael-taverne | Michaël Taverne | AN | 2022-07-12 → 2024-06-06 | — | 2022-07-15 → 2024-06-08 | — |
| nosdeputes:michel-lauzzana | Michel Lauzzana | AN | 2022-07-12 → 2024-06-06 | — | 2017-07-21 → 2026-07-10 | — |
| nosdeputes:mikaele-seo | Mikaele Seo | AN | 2022-07-21 → 2026-07-21 | — | 2022-07-09 → 2026-07-10 | — |
| nosdeputes:nicole-le-peih | Nicole Le Peih | AN | 2022-07-11 → 2024-05-30 | — | 2017-07-21 → 2026-07-10 | — |
| nosdeputes:olivier-dussopt | Olivier Dussopt | AN | 2022-07-11 → 2024-06-05 | 2013-09-10 → 2024-07-23 | — | — |
| nosdeputes:olivier-veran | Olivier Véran | AN | 2022-07-11 → 2024-05-28 | — | 2012-07-12 → 2024-05-22 | — |
| nosdeputes:pascal-lavergne | Pascal Lavergne | AN | 2022-07-11 → 2024-06-05 | — | 2017-07-21 → 2024-06-08 | — |
| nosdeputes:pascale-boyer | Pascale Boyer | AN | 2022-07-11 → 2024-06-05 | — | — | — |
| nosdeputes:patrick-vignal | Patrick Vignal | AN | 2022-07-20 → 2024-06-06 | — | — | — |
| nosdeputes:philippe-dunoyer | Philippe Dunoyer | AN | 2022-07-11 → 2024-05-28 | — | — | — |
| nosdeputes:philippe-juvin | Philippe Juvin | AN | 2022-07-11 → 2024-06-07 | — | 2022-07-09 → 2026-07-10 | — |
| nosdeputes:pierre-cazeneuve | Pierre Cazeneuve | AN | 2022-07-11 → 2024-06-05 | 2024-10-29 → 2026-07-23 | — | — |
| nosdeputes:pieyre-alexandre-anglade | Pieyre-Alexandre Anglade | AN | 2022-07-12 → 2024-05-28 | — | — | — |
| nosdeputes:prisca-thevenot | Prisca Thevenot | AN | 2022-07-11 → 2026-07-21 | — | 2022-07-09 → 2026-07-10 | — |
| nosdeputes:quentin-bataillon | Quentin Bataillon | AN | 2022-07-11 → 2024-06-05 | — | 2022-07-09 → 2024-05-23 | — |
| nosdeputes:rene-pilato | René Pilato | AN | 2023-02-06 → 2024-06-07 | — | — | — |
| nosdeputes:rodrigo-arenas | Rodrigo Arenas | AN | 2022-07-11 → 2024-06-03 | — | — | — |
| nosdeputes:roland-lescure | Roland Lescure | AN | 2017-07-04 → 2025-11-12 | — | 2017-07-21 → 2026-07-10 | — |
| nosdeputes:sandra-marsaud | Sandra Marsaud | AN | 2022-07-11 → 2024-06-07 | — | 2017-07-11 → 2026-07-10 | — |
| nosdeputes:sandrine-le-feur | Sandrine Le Feur | AN | 2017-07-04 → 2026-07-21 | — | 2017-07-11 → 2026-07-10 | — |
| nosdeputes:sophie-errante | Sophie Errante | AN | 2022-07-11 → 2024-06-07 | 2025-06-18 → 2026-06-24 | 2012-07-12 → 2026-07-01 | — |
| nosdeputes:sophie-panonacle | Sophie Panonacle | AN | 2022-07-11 → 2024-06-06 | 2024-10-15 → 2025-01-21 | — | — |
| nosdeputes:stella-dupont | Stella Dupont | AN | 2022-07-11 → 2024-06-07 | 2025-02-04 → 2025-02-04 | 2017-07-17 → 2026-07-10 | — |
| nossenateurs:stephane-mazars | Stéphane Mazars | Senat | 2022-07-11 → 2024-06-06 | 2012-10-16 → 2026-03-27 | — | — |
| nosdeputes:stephane-travert | Stéphane Travert | AN | 2012-07-03 → 2026-07-21 | — | 2012-07-12 → 2026-07-15 | — |
| nosdeputes:stephanie-rist | Stéphanie Rist | AN | 2022-07-11 → 2024-06-07 | — | 2017-07-21 → 2026-07-10 | — |
| nosdeputes:thierry-cozic | Thierry Cozic | AN | — | — | — | — |
| nosdeputes:thomas-cazenave | Thomas Cazenave | AN | 2022-07-11 → 2023-07-20 | 2024-07-19 → 2026-07-23 | 2022-07-09 → 2026-07-10 | — |
| nosdeputes:thomas-gassilloud | Thomas Gassilloud | AN | 2017-07-04 → 2026-07-21 | — | 2017-07-21 → 2026-07-10 | — |
| nosdeputes:thomas-rudigoz | Thomas Rudigoz | AN | 2022-07-11 → 2024-06-06 | — | 2017-07-21 → 2024-05-31 | — |
| nosdeputes:vincent-rolland | Vincent Rolland | AN | 2022-07-11 → 2024-06-04 | — | 2017-07-07 → 2024-06-08 | — |
| nosdeputes:viviane-malet | Viviane Malet | AN | — | — | — | — |
| nosdeputes:veronique-riotton | Véronique Riotton | AN | 2022-07-11 → 2024-06-06 | — | 2017-07-11 → 2026-07-10 | — |
| nosdeputes:xavier-roseren | Xavier Roseren | AN | 2022-07-11 → 2024-06-04 | 2025-04-03 → 2026-07-24 | 2017-07-21 → 2026-07-16 | — |
| nosdeputes:yannick-chenevard | Yannick Chenevard | AN | 2022-07-12 → 2024-05-29 | 2024-07-20 → 2026-08-06 | — | — |
| nosdeputes:yannick-haury | Yannick Haury | AN | 2017-07-04 → 2024-06-04 | — | 2017-07-11 → 2024-06-07 | — |
| nosdeputes:yannick-vaugrenard | Yannick Vaugrenard | AN | — | — | — | — |
| nosdeputes:yael-braun-pivet | Yaël Braun-Pivet | AN | 2022-07-11 → 2024-06-07 | 2024-07-18 → 2026-07-08 | 2017-07-17 → 2026-07-10 | — |
| nosdeputes:edouard-philippe | Édouard Philippe | AN | 2012-07-03 → 2016-11-22 | 2017-06-14 → 2024-03-21 | 2012-07-12 → 2017-02-02 | 2017-08-09 → 2019-12-10 |
| nosdeputes:emilie-chandler | Émilie Chandler | AN | 2022-07-11 → 2024-06-07 | — | 2022-07-05 → 2024-05-31 | — |
| nosdeputes:eric-dolige | Éric Doligé | AN | — | — | — | — |
| nosdeputes:eric-poulliat | Éric Poulliat | AN | 2022-07-12 → 2024-06-05 | — | 2017-07-21 → 2024-05-31 | — |
| nosdeputes:evelyne-renaud-garabedian | Évelyne Renaud-Garabedian | AN | — | — | — | — |

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

Généré le 2026-08-18T06:35:07.166275+00:00. 7 groupe(s) analysé(s), 0 erreur(s) de lecture. Seuil de péremption des sources : 30 jour(s).

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

Généré le 2026-08-18T06:35:07.166275+00:00. 10 gouvernement(s) analysé(s), 0 erreur(s) de lecture. Seuil de péremption des sources : 30 jour(s).

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
