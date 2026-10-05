<a id="teinte-par-ministere-fiche-gouvernement-1205"></a>

# Une teinte par ministère, la même sur la carte, les projets de loi et les actes de la fiche de gouvernement (#1205) (2026-10-04)

`2026-10-04`

> **En bref** — La propriétaire voulait un code commun entre les projets de
> loi et les actes au Journal officiel. Il attendait une donnée : le ministre
> qui présente un projet, publié le 04/10/2026 (#1204). **Forme A retenue sur
> maquette** : une teinte par ministère, la même sur sa carte de « Qui le
> composait », sur les carrés de ses projets de loi et sur sa barre d'actes.
> **Aucune table écrite à la main** : un libellé rejoint sa carte par la règle
> qui construit les cartes — 1 269 des 1 302 projets de loi des fiches s'y
> rattachent. **24 teintes**, attribuées d'après le premier mot du nom du
> ministère, pas d'après son rang. Les carrés de cette fiche ne portent plus la
> couleur de leur commission. La forme a été choisie **contre la
> recommandation de l'agent**, qui proposait un ministère désigné au clic, sans
> couleur.

## Le contexte

La revue du 04/10/2026 avait mis les actes à l'encre : les cinq teintes
d'avant suivaient le rang, pas le ministère
([`revue-ux-de-la-fiche-de-gouvernement`](revue-ux-de-la-fiche-de-gouvernement.md)).
La voie restait ouverte si les projets de loi portaient un jour leur ministre.
C'est fait : `textes[].initiateurs[].portefeuille`
([`ministres-presentant-un-projet-de-loi-1204`](ministres-presentant-un-projet-de-loi-1204.md)).

## Ce que la mesure dit

Sur les données construites depuis `main` (`94ad63118`), avec la règle des
cartes (`organigramme`, `rattachementDuPortefeuille`) :

| Mesure | Résultat |
| --- | --- |
| Projets de loi des 12 fiches qui en portent, rattachés à un ministère de la fiche | 1 269 sur 1 302 |
| Ministères par fiche (cartes de « Qui le composait »), sur les 17 fiches | de 15 à 64 |
| Ministères présents à la fois dans les projets de loi et dans les actes, sur ces 12 fiches | de 3 à 19 |
| Projets de la fiche Borne présentés par plusieurs ministères | 23 sur 111 |
| Actes de la fiche Borne rattachés à une carte | 16 316 sur 17 056 |

Les actes qui ne se rattachent pas sont surtout rangés par la source sous
« Ministère non précisé » et « Présidence de la République ».

## La décision

- **Une teinte par ministère, lue à trois endroits.** Le liseré de la carte
  sert de légende ; les carrés et la barre la reprennent
  (`web/UI_finale/src/utils/ministere.js`).
- **La teinte suit le nom, pas le rang.** Sa place dans la palette vient du
  premier mot du nom du ministère ; elle ne glisse à la place libre suivante
  que si un autre ministère de la même fiche l'occupe. Sur les 17 fiches,
  20 premiers mots sur 49 gardent toujours la même teinte : la stabilité d'un
  gouvernement à l'autre est fréquente, pas garantie.
- **24 teintes.** Calculées pour être le plus éloignées possible les unes des
  autres ; écart minimal entre deux : 12,1 (OKLab × 100), le seuil du
  `DESIGN_SYSTEM`. À 26, il tombait à 11,6.
- **Au-delà de 24 ministères**, ceux qui présentent un projet de loi sont
  servis d'abord ; les autres restent au neutre. Trois fiches sont dans ce
  cas : Ayrault I (35 cartes), Ayrault II (39), Fillon II (64).
- **Un projet présenté par plusieurs ministères est un carré coupé en bandes**,
  une par ministère ; aucun n'est choisi à la place des autres.
- **Gris** pour un projet qu'aucun ministère de la fiche ne présente ; la
  légende écrit « Aucun ministère nommé ».
- **Le Premier ministre n'a pas de teinte** : il signe tous les projets.
- **Les carrés se rangent par ministère** dans chaque colonne, et la légende
  des commissions laisse la place à celle des ministères, cliquable.

## Ce que cela défait

| Règle d'avant | Ce qu'elle devient |
| --- | --- |
| « Une couleur fixe par commission, sur les trois fiches » | Sur deux : la fiche de gouvernement colore par ministère. La commission se lit dans l'infobulle et dans la liste |
| Les actes à l'encre | À la teinte du ministère ; un ministère sans carte reste à l'encre |
| Le liseré des cartes au neutre | Le liseré gauche porte la teinte ; le reste de la carte est inchangé |

## Alternatives écartées

| Forme | Pourquoi |
| --- | --- |
| B — le ministère désigné au clic s'allume dans les trois sections, sans couleur | Recommandée par l'agent : elle tient à 64 ministères comme à 15 et garde la couleur des commissions. La propriétaire a retenu A |
| Une table ministère → commission | Refusée le 04/10/2026 : écrite à la main, sans source |
| Les teintes au rang | La première barre était toujours bleue, d'une fiche à l'autre |
| Ne colorer que le premier ministère d'un projet | Il en choisirait un à la place des autres |

## Ce qui n'a pas été vérifié

- La palette n'est validée qu'**entre ses teintes**, pas contre les couleurs
  déjà prises par le site (institutions, positions de vote). Elle porte un
  rouge et un vert francs ; la fiche de gouvernement n'affiche aucun vote.
- Seule la fiche Borne a été regardée à l'écran. Plusieurs violets y restent
  proches.
- Sur les trois fiches à plus de 24 ministères, des ministères d'actes restent
  au neutre : 16 sur Ayrault I, 3 sur Ayrault II, 8 sur Fillon II.
- La section des prises de parole n'a pas reçu la teinte : ses segments
  alternent deux encres, forme arbitrée le même jour.
