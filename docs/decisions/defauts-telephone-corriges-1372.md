<a id="defauts-telephone-corriges-1372"></a>

# Cinq défauts relevés pendant le chantier téléphone, corrigés (#1372, 2026-10-29)

`2026-10-29`

> **En bref** — Les défauts relevés en route sur #1372 (commentaire du 29/10) sont corrigés sans changer un texte ni une forme : la durée de la XVIe n'est plus coupée, le nuage de mots et l'article « Éducation » n'ont plus de texte sous 13 px à 320 px, le « 23 juin » de l'article « Carburants » est au milieu de sa frise, et la frise des noms de l'ordinateur attend sa police avant de les ranger. Le sixième, « le menu ne mène à aucune fiche », était un choix du 30/09/2026 ; la propriétaire a décidé de retirer « Explorateur » du menu de toutes les pages.

## Ce qui est corrigé, et la mesure

Tout est vérifié dans Chromium le 29/10/2026, sur les données régénérées du jour.

| Défaut | Cause | Correction | Mesure après |
| --- | --- | --- | --- |
| Fiche de la XVIe : « 1 an 11 mois 18 jou » coupé dans la barre | la législature dissoute ne remplit que 40 % de la barre ; le texte était sur une ligne, coupé | la durée peut passer à la ligne (`.lgp-frise-plein`, deux lignes dans 34 px) | entière à 320, 390 et 1 280 px |
| Nuage de mots : mots à 11,8 px à 320 px | le dessin fait au moins 320 unités et se réduit ; seuls les nombres avaient un plancher | les mots partent du même plancher, arrondi à l'entier supérieur (d3-cloud tronque la taille) ; la hauteur du dessin grandit comme le carré du facteur | à 320 px, plus petit mot 13,5 px ; mots placés : 46, 32 et 31 (XVIe, XVe, XVIIe), contre 37, 26 et 27 avant ; 390 px et ordinateur inchangés |
| Article « Éducation » : textes SVG à 11,2 px à 320 px | quatre figures du téléphone n'avaient que 242 px | sous 360 px, marge de page 16 px et cadre de ces figures sans marge intérieure : 282 px | aucun texte sous 13 px à 320, 360 et 390 px ; rien ne déborde |
| Article « Carburants » : « 23 juin » décalé d'environ 5 % | trois dates réparties de bord à bord, de longueurs inégales | la date du milieu est posée à 50 % — le 23 juin est le 92e jour sur 184 | centre de la date = centre de la frise, à 1 280 et 390 px |
| Frise des noms (ordinateur) : empilement variable d'un chargement à l'autre | les noms étaient mesurés avant le chargement de la police | ils sont rangés de nouveau une fois la police prête, comme sur la frise du téléphone | 5 chargements, police ralentie : une seule disposition sur chacune des XVe, XVIe, XVIIe |

**Les deux articles sont des instantanés, qu'on ne met pas à jour.** Ces retouches s'en tiennent à la mise en page, sous la même condition que `articles-au-telephone-1372` : aucun texte ni aucun nombre ne change. `tests/test_instantanes_textes_geles_1372.py` le vérifie.

## Le menu : « Explorateur » retiré de toutes les pages

« Le menu du site ne mène à aucune fiche » n'était pas un défaut de code : à l'accueil, « Explorateur » était retiré volontairement depuis le 30/09/2026, les portes « Commencer l'exploration » y menant plus directement. La propriétaire a choisi le 29/10/2026 de le retirer **partout** : le lien menait à `/candidats`, le complément lié à 2027 et non le cœur du site, et son nom ne disait pas où il menait. On va aux fiches par l'accueil (le logo y ramène depuis toutes les pages), et on change de fiche par le fil d'Ariane. Sur une fiche, la recherche garde sa place en tête de la barre.

Coût accepté : depuis Méthodologie, Sources ou la FAQ, aller à une fiche demande un clic de plus.

## Ce qui n'est pas vérifié

- Au doigt, sur un vrai téléphone.
- La frise des noms avec une police réellement lente sur le réseau : l'essai l'a ralentie, mais seulement si elle vient de Google Fonts.
