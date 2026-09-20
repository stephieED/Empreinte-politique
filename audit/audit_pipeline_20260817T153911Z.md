# Rapport d'audit pipeline (profils + groupes + gouvernements)

Généré le 2026-08-17T15:39:11.570374+00:00. Seuil de péremption des sources : 30 jour(s).

Outil manuel de qualité interne, distinct de `check_quality_gate.py` (seul gate bloquant en CI) : usage manuel uniquement, jamais appelé par la CI. Compile les rapports `audit_pivot_dataset.py`, `audit_groupe_dataset.py` et `audit_gouvernement_dataset.py` sans nouvelle logique de calcul métier, ni score ni classement.

## Vue d'ensemble

| Indicateur | Valeur |
| --- | --- |
| Profils audités | 68 |
| Groupes audités | 7 |
| Gouvernements audités | 10 |
| Erreurs de lecture (profils + groupes + gouvernements) | 0 |
| Warnings (profils + groupes + gouvernements) | 671 |

### Warnings agrégés (profils + groupes + gouvernements)

| Type | Fréquence | Profils concernés | Groupes concernés | Gouvernements concernés |
| --- | --- | --- | --- | --- |
| ParlTrack | 2 | europarl:131580, nossenateurs:jean-luc-melenchon | — | — |
| amendements indisponibles (législature 15) | 39 | nosdeputes:annie-vidal, nosdeputes:beatrice-piron, nosdeputes:benjamin-haddad, nosdeputes:benoit-mournet, nosdeputes:bruno-studer, nosdeputes:caroline-abadie, nosdeputes:charlotte-parmentier-lecocq, nosdeputes:david-amiel, nosdeputes:david-valence, nosdeputes:dominique-da-silva, nosdeputes:dominique-faure, nosdeputes:emilie-chandler, nosdeputes:emmanuel-pellerin, nosdeputes:eric-poulliat, nosdeputes:fadila-khattabi, nosdeputes:frederic-descrozaille, nosdeputes:guillaume-vuilletet, nosdeputes:jean-marc-zulesi, nosdeputes:jean-michel-jacques, nosdeputes:jean-philippe-ardouin, nosdeputes:laurence-maillart-mehaignerie, nosdeputes:ludovic-mendes, nosdeputes:marjolaine-meynier-millefert, nosdeputes:olivier-dussopt, nosdeputes:olivier-veran, nosdeputes:pascale-boyer, nosdeputes:patrick-vignal, nosdeputes:philippe-dunoyer, nosdeputes:pierre-cazeneuve, nosdeputes:pieyre-alexandre-anglade, nosdeputes:sophie-errante, nosdeputes:sophie-panonacle, nosdeputes:stella-dupont, nosdeputes:stephane-mazars, nosdeputes:thomas-cazenave, nosdeputes:thomas-rudigoz, nosdeputes:xavier-roseren, nosdeputes:yael-braun-pivet, nosdeputes:yannick-chenevard | — | — |
| amendements indisponibles (législature 16) | 39 | nosdeputes:annie-vidal, nosdeputes:beatrice-piron, nosdeputes:benjamin-haddad, nosdeputes:benoit-mournet, nosdeputes:bruno-studer, nosdeputes:caroline-abadie, nosdeputes:charlotte-parmentier-lecocq, nosdeputes:david-amiel, nosdeputes:david-valence, nosdeputes:dominique-da-silva, nosdeputes:dominique-faure, nosdeputes:emilie-chandler, nosdeputes:emmanuel-pellerin, nosdeputes:eric-poulliat, nosdeputes:fadila-khattabi, nosdeputes:frederic-descrozaille, nosdeputes:guillaume-vuilletet, nosdeputes:jean-marc-zulesi, nosdeputes:jean-michel-jacques, nosdeputes:jean-philippe-ardouin, nosdeputes:laurence-maillart-mehaignerie, nosdeputes:ludovic-mendes, nosdeputes:marjolaine-meynier-millefert, nosdeputes:olivier-dussopt, nosdeputes:olivier-veran, nosdeputes:pascale-boyer, nosdeputes:patrick-vignal, nosdeputes:philippe-dunoyer, nosdeputes:pierre-cazeneuve, nosdeputes:pieyre-alexandre-anglade, nosdeputes:sophie-errante, nosdeputes:sophie-panonacle, nosdeputes:stella-dupont, nosdeputes:stephane-mazars, nosdeputes:thomas-cazenave, nosdeputes:thomas-rudigoz, nosdeputes:xavier-roseren, nosdeputes:yael-braun-pivet, nosdeputes:yannick-chenevard | — | — |
| amendements indisponibles (législature 17) | 39 | nosdeputes:annie-vidal, nosdeputes:beatrice-piron, nosdeputes:benjamin-haddad, nosdeputes:benoit-mournet, nosdeputes:bruno-studer, nosdeputes:caroline-abadie, nosdeputes:charlotte-parmentier-lecocq, nosdeputes:david-amiel, nosdeputes:david-valence, nosdeputes:dominique-da-silva, nosdeputes:dominique-faure, nosdeputes:emilie-chandler, nosdeputes:emmanuel-pellerin, nosdeputes:eric-poulliat, nosdeputes:fadila-khattabi, nosdeputes:frederic-descrozaille, nosdeputes:guillaume-vuilletet, nosdeputes:jean-marc-zulesi, nosdeputes:jean-michel-jacques, nosdeputes:jean-philippe-ardouin, nosdeputes:laurence-maillart-mehaignerie, nosdeputes:ludovic-mendes, nosdeputes:marjolaine-meynier-millefert, nosdeputes:olivier-dussopt, nosdeputes:olivier-veran, nosdeputes:pascale-boyer, nosdeputes:patrick-vignal, nosdeputes:philippe-dunoyer, nosdeputes:pierre-cazeneuve, nosdeputes:pieyre-alexandre-anglade, nosdeputes:sophie-errante, nosdeputes:sophie-panonacle, nosdeputes:stella-dupont, nosdeputes:stephane-mazars, nosdeputes:thomas-cazenave, nosdeputes:thomas-rudigoz, nosdeputes:xavier-roseren, nosdeputes:yael-braun-pivet, nosdeputes:yannick-chenevard | — | — |
| aucun mandat français connu (candidat non référencé sur NosDéputés/NosSénateurs, ou identité introuvable) | 2 | nosdeputes:marine-le-pen, nossenateurs:jean-luc-melenchon | — | — |
| couverture_roster_senat | 2 | — | Senat:LR, Senat:SER | — |
| fraicheur_donnees | 7 | — | AN:LFI, AN:LR, AN:REN, AN:RN, AN:SOC, Senat:LR, Senat:SER | — |
| gouvernement_profile | 45 | — | — | gouvernement:ATTAL, gouvernement:BARNIER, gouvernement:BAYROU, gouvernement:LECORNU_II |
| gouvernement_textes | 473 | — | — | gouvernement:ATTAL, gouvernement:BARNIER, gouvernement:BAYROU, gouvernement:BORNE, gouvernement:CASTEX, gouvernement:FILLON_2, gouvernement:FILLON_3, gouvernement:LECORNU_II, gouvernement:PHILIPPE, gouvernement:PHILIPPE_2 |
| synchro_sources.nosdeputes | 20 | nosdeputes:anne-genetet, nosdeputes:carole-grandjean, nosdeputes:celine-calvez, nosdeputes:christine-decodts, nosdeputes:christine-le-nabour, nosdeputes:christophe-marion, nosdeputes:corinne-vignon, nosdeputes:danielle-brulebois, nosdeputes:francoise-buffet, nosdeputes:jean-rene-cazeneuve, nosdeputes:jean-terlier, nosdeputes:marie-guevenoux, nosdeputes:marie-pierre-rixain, nosdeputes:maud-bregeon, nosdeputes:michel-lauzzana, nosdeputes:nicole-le-peih, nosdeputes:pascal-lavergne, nosdeputes:quentin-bataillon, nosdeputes:sandra-marsaud, nosdeputes:veronique-riotton | — | — |
| votes introuvables | 3 | nosdeputes:edouard-philippe, nosdeputes:laurent-wauquiez, nossenateurs:bruno-retailleau | — | — |

### Erreurs de lecture agrégées

Aucune erreur de lecture.

---

# Rapport d'audit du jeu de données pivot

Généré le 2026-08-17T15:39:11.570374+00:00. 68 profil(s) analysé(s), 0 erreur(s) de lecture. Seuil de péremption des sources : 30 jour(s).

Ce rapport est un outil de qualité interne : il présente des indicateurs bruts, sans jugement de valeur ni classement.

## Volumétrie

Total profils : 68

### Répartition par chambre

| Chambre | Profils |
| --- | --- |
| AN | 65 |
| PE | 1 |
| Senat | 2 |
| mairie | 0 |
| null | 0 |

### Répartition par provenance (`meta.provenance`)

| Provenance | Profils |
| --- | --- |
| candidat_declare | 8 |
| roster_groupe | 60 |
| null | 0 |

### Distribution des listes métier (par profil)

| Champ | Min | Max | Médiane | Moyenne | % profils à 0 |
| --- | --- | --- | --- | --- | --- |
| votes | 0 | 2642 | 1085.5 | 1047.75 | 5.88 |
| textes_portes | 0 | 12 | 0.0 | 1.22 | 72.06 |
| amendements | 0 | 10763 | 0.0 | 1797.81 | 60.29 |
| interventions | 0 | 395 | 0.0 | 11.6 | 91.18 |

### Sources déclarées

| Moyenne de sources par profil | % profils à une seule source |
| --- | --- |
| 1.99 | 5.88 |

## Tableau croisé des volumes par candidat

| id | Nom | Chambre | Votes | Textes portés | Amendements | Interventions |
| --- | --- | --- | --- | --- | --- | --- |
| nosdeputes:anne-genetet | Anne Genetet | AN | 1595 | 0 | 3671 | 0 |
| nosdeputes:annie-vidal | Annie Vidal | AN | 1422 | 2 | 0 | 0 |
| nosdeputes:benjamin-haddad | Benjamin Haddad | AN | 1163 | 0 | 0 | 0 |
| nosdeputes:benoit-mournet | Benoit Mournet | AN | 1445 | 0 | 0 | 0 |
| nossenateurs:bruno-retailleau | Bruno Retailleau | Senat | 0 | 12 | 0 | 0 |
| nosdeputes:bruno-studer | Bruno Studer | AN | 1327 | 0 | 0 | 0 |
| nosdeputes:beatrice-piron | Béatrice Piron | AN | 1921 | 0 | 0 | 0 |
| nosdeputes:carole-grandjean | Carole Grandjean | AN | 9 | 0 | 3034 | 0 |
| nosdeputes:caroline-abadie | Caroline Abadie | AN | 1402 | 0 | 0 | 0 |
| nosdeputes:charlotte-parmentier-lecocq | Charlotte Parmentier-Lecocq | AN | 1205 | 1 | 0 | 0 |
| nosdeputes:christine-decodts | Christine Decodts | AN | 1846 | 0 | 2085 | 0 |
| nosdeputes:christine-le-nabour | Christine Le Nabour | AN | 2178 | 0 | 4487 | 0 |
| nosdeputes:christophe-marion | Christophe Marion | AN | 1885 | 0 | 3833 | 0 |
| nosdeputes:corinne-vignon | Corinne Vignon | AN | 1434 | 0 | 4601 | 0 |
| nosdeputes:celine-calvez | Céline Calvez | AN | 1144 | 0 | 4245 | 0 |
| nosdeputes:damien-abad | Damien Abad | AN | 257 | 0 | 10474 | 0 |
| nosdeputes:danielle-brulebois | Danielle Brulebois | AN | 1829 | 0 | 9462 | 0 |
| nosdeputes:david-amiel | David Amiel | AN | 1594 | 4 | 0 | 0 |
| nosdeputes:david-valence | David Valence | AN | 2281 | 0 | 0 | 0 |
| nosdeputes:dominique-da-silva | Dominique Da Silva | AN | 1547 | 0 | 0 | 0 |
| nosdeputes:dominique-faure | Dominique Faure | AN | 1 | 0 | 0 | 0 |
| nosdeputes:emmanuel-pellerin | Emmanuel Pellerin | AN | 2642 | 0 | 0 | 0 |
| nosdeputes:fadila-khattabi | Fadila Khattabi | AN | 820 | 0 | 0 | 0 |
| nosdeputes:francoise-buffet | Françoise Buffet | AN | 1420 | 0 | 2159 | 0 |
| nosdeputes:frederic-descrozaille | Frédéric Descrozaille | AN | 1242 | 0 | 0 | 0 |
| nosdeputes:gabriel-attal | Gabriel Attal | AN | 269 | 12 | 826 | 5 |
| nosdeputes:guillaume-vuilletet | Guillaume Vuilletet | AN | 522 | 0 | 0 | 0 |
| nosdeputes:jean-terlier | Jean Terlier | AN | 1260 | 0 | 4744 | 0 |
| nossenateurs:jean-luc-melenchon | Jean-Luc Mélenchon | Senat | 1016 | 0 | 10763 | 15 |
| nosdeputes:jean-marc-zulesi | Jean-Marc Zulesi | AN | 1195 | 0 | 0 | 0 |
| nosdeputes:jean-michel-jacques | Jean-Michel Jacques | AN | 777 | 2 | 0 | 0 |
| nosdeputes:jean-philippe-ardouin | Jean-Philippe Ardouin | AN | 959 | 0 | 0 | 0 |
| nosdeputes:jean-rene-cazeneuve | Jean-René Cazeneuve | AN | 1778 | 0 | 5532 | 0 |
| europarl:131580 | Jordan BARDELLA | PE | 0 | 0 | 0 | 0 |
| nosdeputes:jerome-guedj | Jérôme Guedj | AN | 814 | 1 | 8993 | 395 |
| nosdeputes:laurence-maillart-mehaignerie | Laurence Maillart-Méhaignerie | AN | 773 | 0 | 0 | 0 |
| nosdeputes:laurent-wauquiez | Laurent Wauquiez | AN | 0 | 9 | 1949 | 22 |
| nosdeputes:ludovic-mendes | Ludovic Mendes | AN | 591 | 6 | 0 | 0 |
| nosdeputes:marie-guevenoux | Marie Guévenoux | AN | 740 | 0 | 2639 | 0 |
| nosdeputes:marie-pierre-rixain | Marie-Pierre Rixain | AN | 282 | 0 | 3918 | 0 |
| nosdeputes:marine-le-pen | Marine Le Pen | AN | 558 | 0 | 8999 | 302 |
| nosdeputes:marjolaine-meynier-millefert | Marjolaine Meynier-Millefert | AN | 1420 | 0 | 0 | 0 |
| nosdeputes:maud-bregeon | Maud Bregeon | AN | 758 | 0 | 1419 | 0 |
| nosdeputes:michel-lauzzana | Michel Lauzzana | AN | 1264 | 0 | 4206 | 0 |
| nosdeputes:nicole-le-peih | Nicole Le Peih | AN | 1561 | 0 | 4860 | 0 |
| nosdeputes:olivier-dussopt | Olivier Dussopt | AN | 26 | 1 | 0 | 0 |
| nosdeputes:olivier-veran | Olivier Véran | AN | 18 | 0 | 0 | 0 |
| nosdeputes:pascal-lavergne | Pascal Lavergne | AN | 1510 | 0 | 2143 | 0 |
| nosdeputes:pascale-boyer | Pascale Boyer | AN | 1407 | 0 | 0 | 0 |
| nosdeputes:patrick-vignal | Patrick Vignal | AN | 265 | 0 | 0 | 0 |
| nosdeputes:philippe-dunoyer | Philippe Dunoyer | AN | 1355 | 0 | 0 | 0 |
| nosdeputes:pierre-cazeneuve | Pierre Cazeneuve | AN | 1759 | 6 | 0 | 0 |
| nosdeputes:pieyre-alexandre-anglade | Pieyre-Alexandre Anglade | AN | 833 | 0 | 0 | 0 |
| nosdeputes:quentin-bataillon | Quentin Bataillon | AN | 1105 | 0 | 1042 | 0 |
| nosdeputes:sandra-marsaud | Sandra Marsaud | AN | 1233 | 0 | 4968 | 0 |
| nosdeputes:sophie-errante | Sophie Errante | AN | 602 | 1 | 0 | 0 |
| nosdeputes:sophie-panonacle | Sophie Panonacle | AN | 812 | 3 | 0 | 0 |
| nosdeputes:stella-dupont | Stella Dupont | AN | 1061 | 1 | 0 | 0 |
| nosdeputes:stephane-mazars | Stéphane Mazars | AN | 882 | 6 | 0 | 0 |
| nosdeputes:thomas-cazenave | Thomas Cazenave | AN | 734 | 7 | 0 | 0 |
| nosdeputes:thomas-rudigoz | Thomas Rudigoz | AN | 1066 | 0 | 0 | 0 |
| nosdeputes:veronique-riotton | Véronique Riotton | AN | 1026 | 0 | 6450 | 0 |
| nosdeputes:xavier-roseren | Xavier Roseren | AN | 1044 | 2 | 0 | 0 |
| nosdeputes:yannick-chenevard | Yannick Chenevard | AN | 1363 | 3 | 0 | 0 |
| nosdeputes:yael-braun-pivet | Yaël Braun-Pivet | AN | 356 | 4 | 0 | 0 |
| nosdeputes:edouard-philippe | Édouard Philippe | AN | 0 | 0 | 749 | 50 |
| nosdeputes:emilie-chandler | Émilie Chandler | AN | 1811 | 0 | 0 | 0 |
| nosdeputes:eric-poulliat | Éric Poulliat | AN | 833 | 0 | 0 | 0 |

## Plages temporelles par candidat

| id | Nom | Chambre | Votes | Textes portés | Amendements | Interventions |
| --- | --- | --- | --- | --- | --- | --- |
| nosdeputes:anne-genetet | Anne Genetet | AN | 2022-07-11 → 2024-05-28 | — | 2017-07-21 → 2026-07-10 | — |
| nosdeputes:annie-vidal | Annie Vidal | AN | 2022-07-11 → 2024-06-07 | 2025-03-11 → 2026-05-26 | — | — |
| nosdeputes:benjamin-haddad | Benjamin Haddad | AN | 2022-07-11 → 2024-06-05 | — | — | — |
| nosdeputes:benoit-mournet | Benoit Mournet | AN | 2022-07-11 → 2024-06-06 | — | — | — |
| nossenateurs:bruno-retailleau | Bruno Retailleau | Senat | — | 2010-12-14 → 2026-05-06 | — | — |
| nosdeputes:bruno-studer | Bruno Studer | AN | 2022-07-12 → 2024-06-05 | — | — | — |
| nosdeputes:beatrice-piron | Béatrice Piron | AN | 2022-07-11 → 2024-06-07 | — | — | — |
| nosdeputes:carole-grandjean | Carole Grandjean | AN | 2022-07-11 → 2024-03-12 | — | 2017-07-07 → 2024-03-21 | — |
| nosdeputes:caroline-abadie | Caroline Abadie | AN | 2022-07-11 → 2024-05-30 | — | — | — |
| nosdeputes:charlotte-parmentier-lecocq | Charlotte Parmentier-Lecocq | AN | 2022-07-11 → 2024-06-07 | 2020-12-23 → 2025-02-19 | — | — |
| nosdeputes:christine-decodts | Christine Decodts | AN | 2022-07-11 → 2024-06-05 | — | 2022-07-09 → 2024-06-07 | — |
| nosdeputes:christine-le-nabour | Christine Le Nabour | AN | 2022-07-11 → 2024-06-05 | — | 2017-07-07 → 2026-07-10 | — |
| nosdeputes:christophe-marion | Christophe Marion | AN | 2022-07-11 → 2024-06-07 | — | 2022-07-09 → 2026-07-10 | — |
| nosdeputes:corinne-vignon | Corinne Vignon | AN | 2022-07-11 → 2024-06-06 | — | 2017-07-07 → 2026-07-10 | — |
| nosdeputes:celine-calvez | Céline Calvez | AN | 2022-07-11 → 2024-06-07 | — | 2017-07-21 → 2026-07-10 | — |
| nosdeputes:damien-abad | Damien Abad | AN | 2022-07-25 → 2024-05-28 | — | 2012-07-12 → 2024-05-28 | — |
| nosdeputes:danielle-brulebois | Danielle Brulebois | AN | 2022-07-12 → 2024-06-06 | — | 2017-07-11 → 2026-07-10 | — |
| nosdeputes:david-amiel | David Amiel | AN | 2022-07-12 → 2024-06-06 | 2024-07-20 → 2026-06-29 | — | — |
| nosdeputes:david-valence | David Valence | AN | 2022-07-11 → 2024-06-06 | — | — | — |
| nosdeputes:dominique-da-silva | Dominique Da Silva | AN | 2022-07-13 → 2024-06-05 | — | — | — |
| nosdeputes:dominique-faure | Dominique Faure | AN | 2022-07-11 → 2022-07-11 | — | — | — |
| nosdeputes:emmanuel-pellerin | Emmanuel Pellerin | AN | 2022-07-12 → 2024-06-07 | — | — | — |
| nosdeputes:fadila-khattabi | Fadila Khattabi | AN | 2022-07-11 → 2023-07-19 | — | — | — |
| nosdeputes:francoise-buffet | Françoise Buffet | AN | 2022-07-11 → 2024-06-05 | — | 2022-07-09 → 2026-07-15 | — |
| nosdeputes:frederic-descrozaille | Frédéric Descrozaille | AN | 2022-07-11 → 2024-06-05 | — | — | — |
| nosdeputes:gabriel-attal | Gabriel Attal | AN | 2017-07-04 → 2022-07-11 | 2023-12-13 → 2026-05-26 | 2017-10-05 → 2026-07-10 | — |
| nosdeputes:guillaume-vuilletet | Guillaume Vuilletet | AN | 2022-07-12 → 2024-05-28 | — | — | — |
| nosdeputes:jean-terlier | Jean Terlier | AN | 2022-07-11 → 2024-06-05 | — | 2017-07-21 → 2026-07-10 | — |
| nossenateurs:jean-luc-melenchon | Jean-Luc Mélenchon | Senat | 2017-07-04 → 2022-01-13 | — | 2017-07-11 → 2022-02-03 | — |
| nosdeputes:jean-marc-zulesi | Jean-Marc Zulesi | AN | 2022-07-11 → 2024-06-05 | — | — | — |
| nosdeputes:jean-michel-jacques | Jean-Michel Jacques | AN | 2022-07-12 → 2024-05-28 | 2022-12-14 → 2025-09-30 | — | — |
| nosdeputes:jean-philippe-ardouin | Jean-Philippe Ardouin | AN | 2022-07-12 → 2024-06-05 | — | — | — |
| nosdeputes:jean-rene-cazeneuve | Jean-René Cazeneuve | AN | 2022-07-11 → 2024-05-30 | — | 2017-07-21 → 2026-07-16 | — |
| europarl:131580 | Jordan BARDELLA | PE | — | — | — | — |
| nosdeputes:jerome-guedj | Jérôme Guedj | AN | 2022-07-11 → 2024-06-07 | 2025-10-23 → 2025-12-10 | 2012-07-12 → 2026-07-10 | 2022-07-11 → 2026-07-07 |
| nosdeputes:laurence-maillart-mehaignerie | Laurence Maillart-Méhaignerie | AN | 2022-07-11 → 2024-06-07 | — | — | — |
| nosdeputes:laurent-wauquiez | Laurent Wauquiez | AN | — | 2024-10-15 → 2026-02-03 | 2012-07-12 → 2026-07-10 | 2025-07-22 → 2026-04-21 |
| nosdeputes:ludovic-mendes | Ludovic Mendes | AN | 2022-07-11 → 2024-06-05 | 2024-10-02 → 2025-05-13 | — | — |
| nosdeputes:marie-guevenoux | Marie Guévenoux | AN | 2022-07-11 → 2024-02-06 | — | 2017-07-21 → 2024-05-31 | — |
| nosdeputes:marie-pierre-rixain | Marie-Pierre Rixain | AN | 2022-07-12 → 2024-06-07 | — | 2017-07-21 → 2026-07-15 | — |
| nosdeputes:marine-le-pen | Marine Le Pen | AN | 2022-07-11 → 2024-06-03 | — | 2017-07-21 → 2026-07-16 | 2022-07-06 → 2025-12-30 |
| nosdeputes:marjolaine-meynier-millefert | Marjolaine Meynier-Millefert | AN | 2022-07-11 → 2024-06-05 | — | — | — |
| nosdeputes:maud-bregeon | Maud Bregeon | AN | 2022-07-11 → 2024-05-29 | — | 2022-07-09 → 2026-07-10 | — |
| nosdeputes:michel-lauzzana | Michel Lauzzana | AN | 2022-07-12 → 2024-06-06 | — | 2017-07-21 → 2026-07-10 | — |
| nosdeputes:nicole-le-peih | Nicole Le Peih | AN | 2022-07-11 → 2024-05-30 | — | 2017-07-21 → 2026-07-10 | — |
| nosdeputes:olivier-dussopt | Olivier Dussopt | AN | 2022-07-11 → 2024-06-05 | 2013-09-10 → 2024-07-23 | — | — |
| nosdeputes:olivier-veran | Olivier Véran | AN | 2022-07-11 → 2024-05-28 | — | — | — |
| nosdeputes:pascal-lavergne | Pascal Lavergne | AN | 2022-07-11 → 2024-06-05 | — | 2017-07-21 → 2024-06-08 | — |
| nosdeputes:pascale-boyer | Pascale Boyer | AN | 2022-07-11 → 2024-06-05 | — | — | — |
| nosdeputes:patrick-vignal | Patrick Vignal | AN | 2022-07-20 → 2024-06-06 | — | — | — |
| nosdeputes:philippe-dunoyer | Philippe Dunoyer | AN | 2022-07-11 → 2024-05-28 | — | — | — |
| nosdeputes:pierre-cazeneuve | Pierre Cazeneuve | AN | 2022-07-11 → 2024-06-05 | 2024-10-29 → 2026-07-23 | — | — |
| nosdeputes:pieyre-alexandre-anglade | Pieyre-Alexandre Anglade | AN | 2022-07-12 → 2024-05-28 | — | — | — |
| nosdeputes:quentin-bataillon | Quentin Bataillon | AN | 2022-07-11 → 2024-06-05 | — | 2022-07-09 → 2024-05-23 | — |
| nosdeputes:sandra-marsaud | Sandra Marsaud | AN | 2022-07-11 → 2024-06-07 | — | 2017-07-11 → 2026-07-10 | — |
| nosdeputes:sophie-errante | Sophie Errante | AN | 2022-07-11 → 2024-06-07 | 2025-06-18 → 2026-06-24 | — | — |
| nosdeputes:sophie-panonacle | Sophie Panonacle | AN | 2022-07-11 → 2024-06-06 | 2024-10-15 → 2025-01-21 | — | — |
| nosdeputes:stella-dupont | Stella Dupont | AN | 2022-07-11 → 2024-06-07 | 2025-02-04 → 2025-02-04 | — | — |
| nosdeputes:stephane-mazars | Stéphane Mazars | AN | 2022-07-11 → 2024-06-06 | 2012-10-16 → 2026-03-27 | — | — |
| nosdeputes:thomas-cazenave | Thomas Cazenave | AN | 2022-07-11 → 2023-07-20 | 2024-07-19 → 2026-07-23 | — | — |
| nosdeputes:thomas-rudigoz | Thomas Rudigoz | AN | 2022-07-11 → 2024-06-06 | — | — | — |
| nosdeputes:veronique-riotton | Véronique Riotton | AN | 2022-07-11 → 2024-06-06 | — | 2017-07-11 → 2026-07-10 | — |
| nosdeputes:xavier-roseren | Xavier Roseren | AN | 2022-07-11 → 2024-06-04 | 2025-04-03 → 2026-07-24 | — | — |
| nosdeputes:yannick-chenevard | Yannick Chenevard | AN | 2022-07-12 → 2024-05-29 | 2024-07-20 → 2026-08-06 | — | — |
| nosdeputes:yael-braun-pivet | Yaël Braun-Pivet | AN | 2022-07-11 → 2024-06-07 | 2024-07-18 → 2026-07-08 | — | — |
| nosdeputes:edouard-philippe | Édouard Philippe | AN | — | — | 2012-07-12 → 2017-02-02 | 2017-08-09 → 2019-12-10 |
| nosdeputes:emilie-chandler | Émilie Chandler | AN | 2022-07-11 → 2024-06-07 | — | — | — |
| nosdeputes:eric-poulliat | Éric Poulliat | AN | 2022-07-12 → 2024-06-05 | — | — | — |

### Dates ignorées (invalides ou non parseables)

| Champ | Dates ignorées |
| --- | --- |
| interventions | 6 |

## Complétude

### Taux de remplissage

| Champ | Renseignés | Total | Taux (%) |
| --- | --- | --- | --- |
| parti | 8 | 68 | 11.76 |
| groupe | 68 | 68 | 100.0 |
| tags_thematiques | 3 | 68 | 4.41 |
| mandats | 68 | 68 | 100.0 |

### Profils sans activité (aucun vote, amendement ni intervention)

2 / 68 profil(s).

### Présence des métadonnées

| Critère | Profils en défaut (sur 68) |
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
| nosdeputes:carole-grandjean | sources[0].synchro_le |  | format_invalide |
| nosdeputes:celine-calvez | sources[0].synchro_le |  | format_invalide |
| nosdeputes:christine-decodts | sources[0].synchro_le |  | format_invalide |
| nosdeputes:christine-le-nabour | sources[0].synchro_le |  | format_invalide |
| nosdeputes:christophe-marion | sources[0].synchro_le |  | format_invalide |
| nosdeputes:corinne-vignon | sources[0].synchro_le |  | format_invalide |
| nosdeputes:danielle-brulebois | sources[0].synchro_le |  | format_invalide |
| nosdeputes:francoise-buffet | sources[0].synchro_le |  | format_invalide |
| nosdeputes:jean-rene-cazeneuve | sources[0].synchro_le |  | format_invalide |
| nosdeputes:jean-terlier | sources[0].synchro_le |  | format_invalide |
| nosdeputes:marie-guevenoux | sources[0].synchro_le |  | format_invalide |
| nosdeputes:marie-pierre-rixain | sources[0].synchro_le |  | format_invalide |
| nosdeputes:maud-bregeon | sources[0].synchro_le |  | format_invalide |
| nosdeputes:michel-lauzzana | sources[0].synchro_le |  | format_invalide |
| nosdeputes:nicole-le-peih | sources[0].synchro_le |  | format_invalide |
| nosdeputes:pascal-lavergne | sources[0].synchro_le |  | format_invalide |
| nosdeputes:quentin-bataillon | sources[0].synchro_le |  | format_invalide |
| nosdeputes:sandra-marsaud | sources[0].synchro_le |  | format_invalide |
| nosdeputes:veronique-riotton | sources[0].synchro_le |  | format_invalide |

### Cohérence `chambre` / types de `sources[]`

Aucune incohérence détectée.

## Fraîcheur

### Ancienneté des sources par type (jours écoulés depuis `synchro_le`)

| Type de source | Nombre de sources | Min | Max | Médiane | Moyenne |
| --- | --- | --- | --- | --- | --- |
| assemblee_nationale | 64 | 0 | 4 | 3.0 | 2.12 |
| europarl | 4 | 0 | 1 | 0.0 | 0.25 |
| nosdeputes | 45 | 2 | 11 | 4 | 4.13 |
| nossenateurs | 2 | 0 | 0 | 0.0 | 0 |

### Profils périmés (toutes sources > 30 jours)

Aucun profil périmé.

## Warnings

Total : 144

| Type | Fréquence | Profils concernés |
| --- | --- | --- |
| ParlTrack | 2 | europarl:131580, nossenateurs:jean-luc-melenchon |
| amendements indisponibles (législature 15) | 39 | nosdeputes:annie-vidal, nosdeputes:beatrice-piron, nosdeputes:benjamin-haddad, nosdeputes:benoit-mournet, nosdeputes:bruno-studer, nosdeputes:caroline-abadie, nosdeputes:charlotte-parmentier-lecocq, nosdeputes:david-amiel, nosdeputes:david-valence, nosdeputes:dominique-da-silva, nosdeputes:dominique-faure, nosdeputes:emilie-chandler, nosdeputes:emmanuel-pellerin, nosdeputes:eric-poulliat, nosdeputes:fadila-khattabi, nosdeputes:frederic-descrozaille, nosdeputes:guillaume-vuilletet, nosdeputes:jean-marc-zulesi, nosdeputes:jean-michel-jacques, nosdeputes:jean-philippe-ardouin, nosdeputes:laurence-maillart-mehaignerie, nosdeputes:ludovic-mendes, nosdeputes:marjolaine-meynier-millefert, nosdeputes:olivier-dussopt, nosdeputes:olivier-veran, nosdeputes:pascale-boyer, nosdeputes:patrick-vignal, nosdeputes:philippe-dunoyer, nosdeputes:pierre-cazeneuve, nosdeputes:pieyre-alexandre-anglade, nosdeputes:sophie-errante, nosdeputes:sophie-panonacle, nosdeputes:stella-dupont, nosdeputes:stephane-mazars, nosdeputes:thomas-cazenave, nosdeputes:thomas-rudigoz, nosdeputes:xavier-roseren, nosdeputes:yael-braun-pivet, nosdeputes:yannick-chenevard |
| amendements indisponibles (législature 16) | 39 | nosdeputes:annie-vidal, nosdeputes:beatrice-piron, nosdeputes:benjamin-haddad, nosdeputes:benoit-mournet, nosdeputes:bruno-studer, nosdeputes:caroline-abadie, nosdeputes:charlotte-parmentier-lecocq, nosdeputes:david-amiel, nosdeputes:david-valence, nosdeputes:dominique-da-silva, nosdeputes:dominique-faure, nosdeputes:emilie-chandler, nosdeputes:emmanuel-pellerin, nosdeputes:eric-poulliat, nosdeputes:fadila-khattabi, nosdeputes:frederic-descrozaille, nosdeputes:guillaume-vuilletet, nosdeputes:jean-marc-zulesi, nosdeputes:jean-michel-jacques, nosdeputes:jean-philippe-ardouin, nosdeputes:laurence-maillart-mehaignerie, nosdeputes:ludovic-mendes, nosdeputes:marjolaine-meynier-millefert, nosdeputes:olivier-dussopt, nosdeputes:olivier-veran, nosdeputes:pascale-boyer, nosdeputes:patrick-vignal, nosdeputes:philippe-dunoyer, nosdeputes:pierre-cazeneuve, nosdeputes:pieyre-alexandre-anglade, nosdeputes:sophie-errante, nosdeputes:sophie-panonacle, nosdeputes:stella-dupont, nosdeputes:stephane-mazars, nosdeputes:thomas-cazenave, nosdeputes:thomas-rudigoz, nosdeputes:xavier-roseren, nosdeputes:yael-braun-pivet, nosdeputes:yannick-chenevard |
| amendements indisponibles (législature 17) | 39 | nosdeputes:annie-vidal, nosdeputes:beatrice-piron, nosdeputes:benjamin-haddad, nosdeputes:benoit-mournet, nosdeputes:bruno-studer, nosdeputes:caroline-abadie, nosdeputes:charlotte-parmentier-lecocq, nosdeputes:david-amiel, nosdeputes:david-valence, nosdeputes:dominique-da-silva, nosdeputes:dominique-faure, nosdeputes:emilie-chandler, nosdeputes:emmanuel-pellerin, nosdeputes:eric-poulliat, nosdeputes:fadila-khattabi, nosdeputes:frederic-descrozaille, nosdeputes:guillaume-vuilletet, nosdeputes:jean-marc-zulesi, nosdeputes:jean-michel-jacques, nosdeputes:jean-philippe-ardouin, nosdeputes:laurence-maillart-mehaignerie, nosdeputes:ludovic-mendes, nosdeputes:marjolaine-meynier-millefert, nosdeputes:olivier-dussopt, nosdeputes:olivier-veran, nosdeputes:pascale-boyer, nosdeputes:patrick-vignal, nosdeputes:philippe-dunoyer, nosdeputes:pierre-cazeneuve, nosdeputes:pieyre-alexandre-anglade, nosdeputes:sophie-errante, nosdeputes:sophie-panonacle, nosdeputes:stella-dupont, nosdeputes:stephane-mazars, nosdeputes:thomas-cazenave, nosdeputes:thomas-rudigoz, nosdeputes:xavier-roseren, nosdeputes:yael-braun-pivet, nosdeputes:yannick-chenevard |
| aucun mandat français connu (candidat non référencé sur NosDéputés/NosSénateurs, ou identité introuvable) | 2 | nosdeputes:marine-le-pen, nossenateurs:jean-luc-melenchon |
| synchro_sources.nosdeputes | 20 | nosdeputes:anne-genetet, nosdeputes:carole-grandjean, nosdeputes:celine-calvez, nosdeputes:christine-decodts, nosdeputes:christine-le-nabour, nosdeputes:christophe-marion, nosdeputes:corinne-vignon, nosdeputes:danielle-brulebois, nosdeputes:francoise-buffet, nosdeputes:jean-rene-cazeneuve, nosdeputes:jean-terlier, nosdeputes:marie-guevenoux, nosdeputes:marie-pierre-rixain, nosdeputes:maud-bregeon, nosdeputes:michel-lauzzana, nosdeputes:nicole-le-peih, nosdeputes:pascal-lavergne, nosdeputes:quentin-bataillon, nosdeputes:sandra-marsaud, nosdeputes:veronique-riotton |
| votes introuvables | 3 | nosdeputes:edouard-philippe, nosdeputes:laurent-wauquiez, nossenateurs:bruno-retailleau |

## Erreurs de lecture

Aucune erreur de lecture.

---

# Rapport d'audit du jeu de données groupes

Généré le 2026-08-17T15:39:11.570374+00:00. 7 groupe(s) analysé(s), 0 erreur(s) de lecture. Seuil de péremption des sources : 30 jour(s).

Ce rapport est un outil de qualité interne : il présente des indicateurs bruts, sans jugement de valeur ni classement.

## Volumétrie

### Effectifs (`effectif.actuel` / `min_historique` / `max_historique`)

| Champ | Groupes renseignés | Min | Max | Médiane | Moyenne |
| --- | --- | --- | --- | --- | --- |
| actuel | 7 | 0 | 15 | 1 | 2.57 |
| min_historique | 0 |  |  |  |  |
| max_historique | 0 |  |  |  |  |

### Cohésion de vote (nombre de scrutins recensés par groupe)

| Min | Max | Médiane | Moyenne | % groupes à 0 |
| --- | --- | --- | --- | --- |
| 0 | 4102 | 0 | 782 | 57.14 |

### Amendements agrégés (tous types de déposants confondus)

| Compteur | Min | Max | Médiane | Moyenne |
| --- | --- | --- | --- | --- |
| nb_amendements | 0 | 90798 | 0 | 15541.43 |
| nb_adoptes | 0 | 17285 | 0 | 2609.71 |
| nb_rejetes | 0 | 23187 | 0 | 4132.43 |
| nb_irrecevables | 0 | 13552 | 0 | 2354.43 |
| nb_retires_ou_tombes | 0 | 24275 | 0 | 3975 |

### Amendements agrégés par type de déposant

#### commission_rapporteur

| Compteur | Min | Max | Médiane | Moyenne |
| --- | --- | --- | --- | --- |
| nb_amendements | 0 | 2271 | 0 | 352.43 |
| nb_adoptes | 0 | 1410 | 0 | 209 |
| nb_rejetes | 0 | 255 | 0 | 45.43 |
| nb_irrecevables | 0 | 23 | 0 | 4.14 |
| nb_retires_ou_tombes | 0 | 390 | 0 | 61.29 |

#### depute

| Compteur | Min | Max | Médiane | Moyenne |
| --- | --- | --- | --- | --- |
| nb_amendements | 0 | 88527 | 0 | 15189 |
| nb_adoptes | 0 | 15875 | 0 | 2400.71 |
| nb_rejetes | 0 | 22932 | 0 | 4087 |
| nb_irrecevables | 0 | 13529 | 0 | 2350.29 |
| nb_retires_ou_tombes | 0 | 23885 | 0 | 3913.71 |

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
| AN:LFI | La France insoumise - NUPES | AN | 0 | 0 | 0 | 0 |
| AN:LR | Les Républicains | AN | 0 | 0 | 0 | 0 |
| Senat:LR | Les Républicains | Senat | 1 | 0 | 0 | 0 |
| AN:RN | Rassemblement National | AN | 1 | 558 | 318 | 8999 |
| AN:REN | Renaissance | AN | 61 | 4102 | 0 | 90798 |
| Senat:SER | Socialiste, Écologiste et Républicain | Senat | 0 | 0 | 0 | 0 |
| AN:SOC | Socialistes et apparentés | AN | 1 | 814 | 179 | 8993 |

## Tableau croisé des plages temporelles par groupe

Complète (sans le remplacer) le tableau croisé des volumes ci-dessus : pour chaque groupe, la période couverte par les dates disponibles (min → max), plutôt que le nombre d'entrées.

| groupe_id | Nom | Chambre | Cohésion de vote (min → max) | Amendements agrégés |
| --- | --- | --- | --- | --- |
| AN:LFI | La France insoumise - NUPES | AN | N/D | N/A (non applicable) |
| AN:LR | Les Républicains | AN | N/D | N/A (non applicable) |
| Senat:LR | Les Républicains | Senat | N/D | N/A (non applicable) |
| AN:RN | Rassemblement National | AN | 2022-07-11 → 2024-06-03 | N/A (non applicable) |
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

1 / 7 groupe(s).

## Cohérence

### Validation du schéma (`validate_profil_groupe`)

Aucun groupe invalide détecté.

### Divergence `schema_version` / `meta.schema_version`

Aucune divergence détectée.

### Écart de couverture du roster

| groupe_id | Roster total | Profils disponibles | Écart | Taux de couverture (%) |
| --- | --- | --- | --- | --- |
| AN:LFI | 76 | 0 | 76 | 0.0 |
| AN:LR | 62 | 0 | 62 | 0.0 |
| AN:REN | 193 | 61 | 132 | 31.61 |
| AN:RN | 90 | 1 | 89 | 1.11 |
| AN:SOC | 31 | 1 | 30 | 3.23 |
| Senat:LR | 235 | 1 | 234 | 0.43 |
| Senat:SER | 65 | 0 | 65 | 0.0 |

### Doublons de `groupe_id`

Aucun doublon détecté.

## Fraîcheur

### Ancienneté des sources par type (jours écoulés depuis `synchro_le`)

| Type de source | Nombre de sources | Min | Max | Médiane | Moyenne |
| --- | --- | --- | --- | --- | --- |
| assemblee_nationale | 3 | 0 | 4 | 0 | 1.33 |
| europarl | 2 | 0 | 0 | 0.0 | 0 |
| nosdeputes | 43 | 3 | 11 | 4 | 4.02 |
| nossenateurs | 1 | 0 | 0 | 0 | 0 |

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

Généré le 2026-08-17T15:39:11.570374+00:00. 10 gouvernement(s) analysé(s), 0 erreur(s) de lecture. Seuil de péremption des sources : 30 jour(s).

Ce rapport est un outil de qualité interne : il présente des indicateurs bruts, sans jugement de valeur ni classement.

## Volumétrie

### Répartition par `periode.actif`

| Total | Actifs | Inactifs | Indéterminés |
| --- | --- | --- | --- |
| 10 | 1 | 9 | 0 |

### Distribution du nombre de `membres` / `textes` par gouvernement

| Champ | Min | Max | Médiane | Moyenne |
| --- | --- | --- | --- | --- |
| membres | 1 | 9 | 3.5 | 3.6 |
| textes | 0 | 45 | 0.0 | 6.1 |

### Comptages agrégés par statut de texte (`comptages.par_statut`)

| Statut | Total |
| --- | --- |
| adopte | 20 |
| adopte_49_3 | 2 |
| depose | 0 |
| navette_en_cours | 36 |
| rejete | 2 |
| rejete_49_3 | 0 |
| retire | 1 |

## Tableau croisé des plages temporelles par gouvernement

Pour chaque gouvernement, la période couverte par les dates disponibles (min → max) des mandats de ses membres et des textes qu'il a portés.

| gouvernement_id | Nom | Mandats membres (min → max) | Textes (min → max) |
| --- | --- | --- | --- |
| gouvernement:ATTAL | Gouvernement Attal | 2024-01-10 → 2024-09-05 | 2024-06-12 → 2025-10-22 |
| gouvernement:BARNIER | Gouvernement Barnier | 2024-09-22 → 2024-12-13 | 2024-10-10 → 2025-09-10 |
| gouvernement:BAYROU | Gouvernement Bayrou | 2024-12-24 → 2025-09-09 | 2025-01-08 → 2026-01-28 |
| gouvernement:BORNE | Gouvernement Borne | 2022-05-21 → 2024-01-09 | N/D |
| gouvernement:CASTEX | Gouvernement Castex | 2020-07-07 → 2022-05-16 | N/D |
| gouvernement:FILLON_2 | Gouvernement Fillon II | 2007-06-19 → 2010-11-13 | N/D |
| gouvernement:FILLON_3 | Gouvernement Fillon III | 2010-11-14 → 2012-05-10 | N/D |
| gouvernement:LECORNU_II | Gouvernement Lecornu II | 2025-10-13 → 2026-02-26 | 2025-10-14 → 2026-07-27 |
| gouvernement:PHILIPPE | Gouvernement Philippe I | 2017-05-18 → 2017-06-19 | N/D |
| gouvernement:PHILIPPE_2 | Gouvernement Philippe II | 2017-06-20 → 2020-07-06 | N/D |

> **`mandats_membres`** : calculée sur `membres[].debut`/`.fin`. Un `fin = null` signale un mandat en cours — exclu du calcul sans jamais être remplacé par la date du jour (AGENTS.md §2.5).

### Dates `membres[]`/`textes[]` invalides ignorées pour le calcul (0)

Aucune date invalide détectée.

## Complétude

### Présence d'un `premier_ministre` renseigné

| Renseignés | Total | Taux (%) |
| --- | --- | --- |
| 0 | 10 | 0.0 |

### Taux de `membres[].portefeuille` renseigné

| Renseignés | Total | Taux (%) |
| --- | --- | --- |
| 0 | 36 | 0.0 |

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
| assemblee_nationale | 7 | 0 | 3 | 0 | 1.29 |
| europarl | 1 | 0 | 0 | 0 | 0 |
| nosdeputes | 29 | 2 | 11 | 4 | 5.03 |
| nossenateurs | 2 | 0 | 0 | 0.0 | 0 |

### Gouvernements périmés (toutes sources > 30 jours)

Aucun gouvernement périmé.

## Warnings

Total : 518

| Type | Fréquence | Gouvernements concernés |
| --- | --- | --- |
| gouvernement_profile | 45 | gouvernement:ATTAL, gouvernement:BARNIER, gouvernement:BAYROU, gouvernement:LECORNU_II |
| gouvernement_textes | 473 | gouvernement:ATTAL, gouvernement:BARNIER, gouvernement:BAYROU, gouvernement:BORNE, gouvernement:CASTEX, gouvernement:FILLON_2, gouvernement:FILLON_3, gouvernement:LECORNU_II, gouvernement:PHILIPPE, gouvernement:PHILIPPE_2 |

## Erreurs de lecture

Aucune erreur de lecture.
