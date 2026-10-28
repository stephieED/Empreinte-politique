<a id="telephone-lot-3-formes-1372"></a>

# Au téléphone, huit composants redessinés : le lot 3 (#1372, 2026-10-28)

`2026-10-28`

> **En bref** — Sous 720 px, huit composants des fiches et de l'accueil prennent la forme arbitrée le 28/10/2026 sur maquettes : grille d'années pour la navigation de période, tableaux à colonnes écrits sous leur barre, étagères côte à côte, bande des scrutins en carrés, grille « en chiffres » sans défilement, nombres des commissions sous la barre, deux hémicycles au cadre resserré. Plus aucune de ces figures ne défile de côté. Aucun mot nouveau à l'écran. L'ordinateur ne change pas.

## Le problème

Le lot 1 (`telephone-une-section-par-ecran-1372`) a mis une section par écran ; il a laissé aux figures leur dessin d'ordinateur, réduit ou défilant de côté. À 390 px : la navigation de période perdait l'année de ses petites périodes ; les tableaux à colonnes cassaient leur en-tête sur trois lignes, et la barre des actes par ministère avait sauté ; la bibliothèque des textes et la grille « Ce que cette personne a engagé, en chiffres » ne montraient qu'un tiers d'elles-mêmes ; la bande des scrutins défilait ; les segments des barres de commission perdaient leurs nombres (« Défense » : 19 affichés sur 23) ; les sigles des hémicycles tombaient sous 11 px.

## Ce qui est décidé

| Composant | Forme | Ce qu'elle fait | Maquette (privée) |
| --- | --- | --- | --- |
| Navigation de période (`NavigationPeriodes.jsx`) | **C** | Une case égale par période : l'année, son volume dessous ; une rangée jusqu'à cinq, des rangées équilibrées au-delà. Case courante à l'encre, trait jaune. Plus de flèches ni de cartes ; les touches ← → marchent toujours. Une période à 0 reste, « 0 » en italique | https://claude.ai/artifact/NN1UCdQCm7vKG3uB7ZyPYX |
| Tableaux à colonnes — amendements par matière (candidat, groupe), actes par ministère, prises de parole par débat (gouvernement, groupe) | **B** | Plus d'en-tête. L'intitulé entier, la barre sur toute la largeur, puis « **2 564** amendements · **2** textes distincts » : les mots de l'en-tête, accordés au singulier pour 1 (`ChiffresDeLigne.jsx`). Les actes retrouvent leur barre | https://claude.ai/artifact/75wT8JKPGbN5py2Zur23yZ |
| Étagères des textes (législature) | **C** | Trois meubles côte à côte en colonnes égales, la commission en titre au-dessus de ses trois étagères ; les livres gardent leur taille et passent à la ligne | https://claude.ai/artifact/P6FoA8gREx3Gm4xnTUbj1o |
| Bande « Où il a voté autrement que son groupe » | **A** | Un carré de 15 px par scrutin, dans l'ordre. Fond : position majoritaire du groupe. Encoche noire de 4 px : des membres n'ont pas suivi. Cadre d'encre et point de sa couleur : sa position divergente. Mêmes infobulles ; la légende redessine ses clés sans changer ses mots | https://claude.ai/artifact/X9fAPbkb5KB4zM9ihUT9du |
| « Ce que cette personne a engagé, en chiffres » | **C** | Une colonne égale par institution ouverte, la case de coin retirée, l'intitulé de rang en titre au-dessus de ses cellules. Les puces gardent leur rôle | https://claude.ai/artifact/6BeA7WuxrxzCazrb5V7WTK |
| Barres de « Le travail des commissions » | **B** | Plus aucun nombre dans les segments ; sous la barre, une pastille de 10 px de la couleur du segment et son nombre, pour chaque étape non nulle, dans l'ordre de la légende | https://claude.ai/artifact/Txt7n8xLM9YW2eHgLZrdcG |
| Hémicycle « Qui siège » | **D1** | `viewBox` calculé sur ce qui est dessiné (sièges, arcs, étiquettes posées) : sigles ≈ 13,5 px rendus, toujours des liens. Nombre écarté du sigle (`dy` 42 → 56). Un sigle posé sans effectif le reçoit quand il a la place — « NI » compris —, sans qu'aucun sigle disparaisse. La légende « Non-inscrits », quand elle est seule, est retirée | https://claude.ai/artifact/FcE3q2ppYFnt53wdwzfr1V |
| Hémicycle de l'accueil | D1 | Cadre resserré sur l'arc et ses sigles ; la taille des sigles, en unités de la figure, est choisie pour rendre 13 px (calcul repris jusqu'à stabilité, puisqu'elle élargit le cadre) | https://claude.ai/artifact/6WjubKRgEJ5uCBdE2NY7f5 |

Tout vit sous `@media (max-width: 720px)`, ou derrière `useEcranEtroit()` quand la structure change (navigation de période, hémicycles). Au-delà de 720 px, les pages entières des cinq fiches vérifiées et de l'accueil sont identiques au pixel, à 1 280 et à 721 px (captures comparées le 28/10/2026).

## Ce qui a été tranché en codant

- **Les en-têtes des étagères** empilent le libellé et son total (« PROMULGUÉS / 139 ») : sur une ligne, le total de la première étagère était coupé dans la maquette.
- **Le sigle qui gagne son nombre** : la maquette ajoutait l'effectif à « NI » seul. Les sigles se posent d'abord comme avant (nombre à partir de 30 députés, sigle retiré s'il chevauche) ; puis tout sigle posé sans nombre le reçoit s'il a la place. Ce second temps ne retire aucun sigle : un premier essai qui posait chaque sigle avec son nombre d'abord faisait disparaître « FI » de la XVe. Mesuré le 28/10/2026 : mêmes sigles affichés que sur `main` pour les XIVe à XVIIe ; gagnent leur nombre « NI » (XVIe, XVIIe), « UDI », « GDR » (XIVe) et « FI » (XVe) ; « SOC » et « AGIR » (XVe), « ECOLO » (XVIe) restent sans.
- **La clé « ses positions divergentes »** dessine un point neutre (gris) : sa couleur varie avec la position. L'ancienne clé employait `--contre`, défini nulle part — son cercle était vide.
- **« 1 / 39 membre »** : l'unité s'accorde au numérateur.

## Écarté

Les autres formes de chaque maquette : A et B pour la période (rail élargi avec flèches ; liste déroulante), A et C pour les tableaux (colonnes resserrées ; nombre principal seul), A et B pour les étagères, B et C pour la bande, A et B pour la grille, A et C pour les commissions, A à D2 pour l'hémicycle (D2 : le nombre à côté du sigle).

## Ce qui n'est pas vérifié

- Au doigt, sur un vrai téléphone : seulement Chromium à 390 × 844 (Playwright, `is_mobile`).
- La bande des scrutins sur une carrière à plusieurs centaines de scrutins : vue sur la fiche de Jean-Luc Mélenchon (89).
- Le chevauchement des sigles reste estimé (0,64 em par signe). Mesuré par `getBBox` sur les XIVe à XVIIe : deux paires se touchent (« DEM »/« AGIR » en XVe, « SOC »/« ECOLO » en XVIe), les mêmes que sur `main`.
- La largeur des sigles de l'accueil est estimée (0,66 em par signe) ; une police de repli plus large pourrait les approcher du bord.

## Hors de ce lot

Restent à maquetter (commentaire de #1372 du 28/10/2026) : les filtres en pastilles (forme B retenue, libellés nouveaux à valider), « En bref » du groupe, de la législature et du gouvernement, le budget, les carrés des textes, le nuage de mots, la frise de l'accueil, les listes longues, le pied de page.
