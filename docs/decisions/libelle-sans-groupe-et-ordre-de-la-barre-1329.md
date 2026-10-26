<a id="libelle-sans-groupe-et-ordre-de-la-barre-1329"></a>

# « Sans groupe connu à l'Assemblée », et « Articles » juste après la recherche (#1329) (2026-10-26)

`2026-10-26`

> **En bref** — Deux arbitrages rendus après la fusion de `fil-d-ariane-a-la-place-du-tiroir-1329`, qui les complète sans être réécrite. **Le dernier intitulé de la liste des candidats « Par groupe »**, dans le menu du fil d'Ariane d'une fiche de candidat, est « Sans groupe connu à l'Assemblée », et non « Autres candidats » comme l'écrit la décision du fil d'Ariane. **« Articles » vient juste après la recherche** dans la barre du site, avant « Méthodologie » ; la barre des articles publiés suit le même ordre.

## « Sans groupe connu à l'Assemblée »

L'intitulé ferme la liste « Par groupe » : il réunit les candidats qui n'ont été
membres d'aucun groupe de l'Assemblée publié sur le site, donc depuis la XIVe.
Mesuré le 26/10/2026 sur le manifeste construit des données du 22/10 : 23 des
34 candidats du manifeste, dont des sénateurs, des députés européens, un député
non inscrit et des candidats sans mandat parlementaire.

| Forme | Sort |
| --- | --- |
| « Autres candidats » | première version, livrée dans #1347 ; ne disait pas pourquoi la majorité de la liste était à part |
| « Sans groupe à l'Assemblée depuis 2012 », « Sans groupe à l'Assemblée » | proposées, non retenues |
| « Sans groupe connu » | formulation de la propriétaire, appliquée mot pour mot |
| **« Sans groupe connu à l'Assemblée »** | **retenue** (« ok avec ta correction ») : le groupe d'un sénateur ou d'un député européen est souvent connu, et sa fiche l'affiche ; sans la précision, « connu » se lisait « nous ne savons pas » |

Livré dans #1348. Le texte vit dans `web/UI_finale/src/components/FilDAriane.jsx`.

## « Articles » juste après la recherche

Demandé le 26/10/2026 : « peux-tu mettre article entre la barre recherche et
méthodo ? ». L'ordre de la barre devient Explorateur (ou la recherche, sur une
fiche), Articles, Méthodologie, Sources, FAQ, Nous soutenir, sur toutes les pages
(`NavigationSite.jsx`). La barre des articles publiés le reprend
(`scripts/chrome-instantane.mjs`, appliqué par `index-rapports.mjs`) : « le chrome
suit le site, le contenu reste gelé », et seuls les liens de navigation des
quatre articles ont bougé. `tests/test_barre_navigation_951.py` et
`tests/test_chrome_instantanes_1029.py` tiennent les deux ordres ensemble.

Livré dans #1347.
