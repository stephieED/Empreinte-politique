<a id="telephone-lot-3-suite-1372"></a>

# Au téléphone, la fin du lot 3 : filtres, « En bref », budget, carrés, listes longues, pied de page (#1372, 2026-10-28)

`2026-10-28`

> **En bref** — Sous 720 px, les derniers composants de la revue du 28/10/2026 prennent la forme arbitrée le même jour sur maquettes : filtres en liste déroulante, frises « En bref » rangées sans chevauchement et réunies par Premier ministre, budget face à face resserré avec le solde en tête, carrés de 24 px rangés par couleur, nuage sans carte, quatre listes repliées, pied de page de 185 px. L'ordinateur ne change pas, sauf deux points voulus : la phrase d'aide des carrés (« Choisissez… ») et l'ordre de l'hémicycle dans « Avec qui ils votent ».

## Le problème

La revue téléphone du 28/10/2026 (92 constats) laissait, après le lot 3 (`telephone-lot-3-formes-1372`), des composants sans forme arrêtée : pastilles de filtre empilées sur 200 px, trois frises « En bref » illisibles (graduations à 10 px, escalier de cinq marches, gouvernements de 1 à 3 px), colonnes du budget larges de 700 à 940 px qui défilaient de côté, carrés de 16 px et légende centrée, nuage aux exposants de 9 px, quatre listes de 2 à 5 écrans, pied de page de 383 px répété sous chaque section.

## Ce qui est décidé

| Composant | Forme | Ce qu'elle fait | Maquette (privée) |
| --- | --- | --- | --- |
| Filtres en pastilles (`FiltreDeroulant.jsx`) | **B**, libellés **V2** | Une boîte par filtre ; rien de choisi : « Toutes » (nature, position), « Tous » (origine) ; choix faits : leurs libellés à la suite. La liste s'ouvre dans le flux, cases à cocher (bouton radio pour un choix unique), choix à 0 retirés. Logique de sélection inchangée | https://claude.ai/artifact/4116cceFYCsgHxfR8Zhk5s |
| « En bref » du groupe | **C** | Effectifs dans la figure seulement, sans axe vertical ; années à 13 px, celles qui tiennent ; la liste garde dates, nom et posture (sur sa ligne) | https://claude.ai/artifact/LuhYMisaRg7jv6ZNZNLMkT |
| « En bref » de la législature | **F** | Axe arrêté à aujourd'hui. Noms rangés au plus petit nombre de niveaux sans qu'aucun trait ne traverse un nom (`rangerEtiquettes`, `utils/frise.js`). Gouvernements consécutifs d'un même Premier ministre réunis : « Lecornu I et II », chaque partie menant à sa fiche, durée cumulée calculée sur les dates ; encoche blanche au remaniement | https://claude.ai/artifact/255rFpK9o9LraHtJtUgCpj |
| « En bref » du gouvernement | **C** | La frise depuis 2007 devient une fenêtre de cinq ou six gouvernements autour de celui de la fiche, même composant (`FriseDesNoms.jsx`) ; la ligne des voisins disparaît | https://claude.ai/artifact/MT8drXyRuTpHVbQbD8qRVN |
| Budget (section close, `section-budgets-fiche-gouvernement-1053`) | **B′** | Mise en page seule : colonnes face à face resserrées, libellés à 13 px sur deux ou trois lignes, figure ×1,3, trait de rappel ; le solde en tête du bloc de l'État, sur toute la largeur, redessiné à cette largeur | https://claude.ai/artifact/WqWmZ2f2rwmWhCY3Ur3VmU |
| Carrés des textes | **B** | Carrés de 24 px (21 px en quatre colonnes) ; légende alignée à gauche, une entrée par ligne de 30 px ; carrés regroupés par couleur dans chaque étape | https://claude.ai/artifact/CnEwSoQK1nZh8KDuZjGhgW |
| Phrase d'aide des carrés, tous écrans | **V1** | « Choisissez un carré, une étape ou un ministère (une commission) pour lire les textes. » | — |
| Nuage de mots | **A** | Carte intérieure retirée, pleine largeur, exposants ≥ 13 px | https://claude.ai/artifact/8XryiVyW6JnzSoq2C1dDZC |
| Les fonctions exercées | **A** | Commissions de l'Assemblée ouvertes, les autres familles repliées sur titre et nombre | https://claude.ai/artifact/CZKS86oc5KS4voRy3t2SaX |
| Qui le composait | **C** | Cartes gardées, six, puis « Voir les 14 autres ministères » (nombre calculé) | idem |
| Avec qui ils votent | **B** + ordre | Barre à trois parts au lieu des carrés ; **ordre de l'hémicycle sur tous les écrans** (siège médian, `ordreDeLHemicycle`), au lieu d'un tri par nombre qui se lisait comme un classement (`docs/regles/textes-publies.md`) | idem |
| Les plus partagés | **A** | Trois cartes, les autres dans « et N autres textes » | idem |
| Pied de page du site | **A′** | Titres retirés, liens à la suite (32 px), adresse remplacée par une enveloppe (« Écrire à Empreinte politique » pour les lecteurs d'écran), trois pictogrammes alignés à droite ; 383 → environ 175 px | https://claude.ai/artifact/Lk9ZutgQaKuG7GQyKLZD8d |
| Frise de l'accueil | plancher | Textes à 13-14 px (règle du lot 1), voies décalées de 16 px pour que rien ne sorte à gauche | — |

## Ce qui a été tranché en codant

- **La durée cumulée** se calcule sur les dates : « Lecornu I et II » dure 1 an 1 mois 18 jours, et non 17 jours comme la maquette, qui additionnait deux textes.
- **Trois gouvernements d'un même Premier ministre** s'écrivent « Fillon I, II et III », sur le modèle validé « Lecornu I et II ».
- **Le solde à trois exercices** (Philippe II) : les barres font environ 34 px ; un nombre de 13 px y est écrit debout plutôt que de disparaître.
- **La phrase d'aide européenne** de la fiche candidat suit la V1 : « Choisissez un carré, une étape ou un thème pour lire les textes. » La phrase des rubans (`CascadeTextes.jsx`, « Cliquez un ruban… ») n'est pas touchée.
- **Les six ministères affichés** sont les six premiers de l'ordre de l'ordinateur (Premier ministre, puis ministères dans l'ordre de la composition), et non ceux de l'ancien empilement au téléphone que montrait la maquette.
- **Un groupe sans place dans l'hémicycle** (dissous avant la date de référence) vient à la fin, par sigle.
- **Le filtre de nature des votes européens** (fiche de Raphaël Glucksmann) passe aussi en liste ; sans intitulé au-dessus, sa boîte garde le texte de la pastille actuelle, « Toutes natures ».

## Écarté

Les autres formes de chaque maquette : A et C des filtres ; A et B des « En bref » du groupe ; A à E de la législature ; A et B du gouvernement ; A et C du budget (colonnes l'une sous l'autre ; une colonne à la fois) ; A et C des carrés ; C du nuage (liste à barres) ; B des fonctions (tout replié) ; A et B de « Qui le composait » ; A de « Avec qui ils votent » (lignes repliées) ; B des plus partagés ; A et C du pied de page.

## Ce qui n'est pas vérifié

- Au doigt, sur un vrai téléphone : seulement Chromium à 390 × 844 (Playwright, `is_mobile`), et 360 px pour le pied de page.
- La largeur entre 521 et 720 px n'a pas été capturée composant par composant.
- La frise de législature place parfois ses noms avant le chargement de la police à l'ordinateur (défaut antérieur, vu sur les XVIIe et XVe) : les comparaisons au pixel à 1 280 px en sont bruitées.

## Hors de ce lot

- La page de méthodologie dit encore que les groupes de « Avec qui ils votent » sont « rangés d'abord par le nombre de textes comparés » : texte à revoir avec la propriétaire.
- À 390 px, la durée de la XVIe est coupée dans sa barre (« 1 an 11 mois 18 jou »), à cause de la partie dissoute : défaut antérieur.
- L'accueil au téléphone : maquette demandée le 28/10/2026, une fois ce lot livré.
