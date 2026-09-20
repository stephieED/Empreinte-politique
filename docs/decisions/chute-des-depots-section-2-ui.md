# La chute des dépôts remplace la barre par législature (§ « Ce qu'il a proposé »), 06/09/2026

`2026-09-06`

> **En bref** — la barre segmentée **par sort**, une ligne par législature, répondait « combien et de quelle issue » et **rien sur le quand ni sur quoi** ; une **chute** — escalier cumulatif, une marche par **année civile** découpée par **matière**, barre de total qui repart du sol — la remplace, avec un bouton qui échange **amendements déposés** et **dossiers amendés** et un clic qui ouvre les dossiers de la matière, ceux dont **au moins un amendement a été adopté** marqués ; trois contraintes écrites sous la figure : **l'axe est le calendrier** (une année vide garde sa place, sa graduation et son palier — sept chez Laurent Wauquiez, huit chez Jérôme Guedj), **un escalier est additif** donc **aucune hauteur minimale** (1 dépôt sur 2 831 fait 0,15 px, et c'est le **palier** tracé au cumul exact qui garantit qu'aucune année ne disparaît), et **le domaine est l'union des deux mesures** jamais recalculé — fixé, il **montre** que **258 des 584 dépôts** de Laurent Wauquiez ne sont rattachés à aucun dossier ; une carte **« N amendements adoptés »** ouvre la rangée des blocs, **compte seul et rien en face**, porté sur **tous** les dépôts (la somme par dossier en perdrait **6** chez Jérôme Guedj et **25** chez Laurent Wauquiez) ; coût assumé : la série année × matière est accumulée dans la **passe unique** de `joinAmendements`, générateur qui ne se relit pas (#377, #431), et le lot **ouvre une palette catégorielle** que `DESIGN_SYSTEM.md` disait close — vrai du besoin d'alors (*marquer une ligne*), faux de celui-ci (*distinguer N matières*), sans solution sans teinte puisqu'une rampe d'encre les mettrait sur une échelle (§2 règle 1) ; **aucun rapport entre les deux mesures** (§6), le **gris** réservé à « matière non établie » qui est une absence et non une catégorie (§2 règle 5), et **aucune librairie de graphiques ajoutée** — le SVG est écrit à la main.

Ancres : `agregerAmendements`, `anneesPleines`, `MATIERE_NON_ETABLIE`, `teinteMatiere`,
`PALETTE_MATIERE`, `Chute`, `Propositions`.

## Contexte

La section « Ce qu'il a proposé » montrait les dépôts d'amendements en une barre
segmentée **par sort**, une ligne par législature. Elle répondait « combien, et
de quelle issue », et rien d'autre : ni **quand** les dépôts sont arrivés, ni
**sur quelle matière**. Or la dispersion est le fait que le total cache — 2 831
dépôts de Jean-Luc Mélenchon dont **2 625 en 2020**, deux mois de bataille sur
les retraites, contre 690 de Marine Le Pen étalés sur 57 mois.

Le sujet a été instruit en maquette (artifact « Trois formes pour ce qu'il a
proposé »), forme après forme : nuage, aires empilées, trellis, waterfall.

## Décision

Une **chute** — un escalier cumulatif — remplace la barre par législature.
Une marche par **année civile**, découpée par **matière**, une barre de total qui
repart du sol. Un bouton échange deux mesures : **amendements déposés** et
**dossiers amendés**. Cliquer une marche ou une entrée de la légende ouvre la
liste des dossiers de cette matière, avec ceux dont **au moins un amendement a
été adopté**.

Trois contraintes décident du reste, et elles sont écrites sous la figure :

- **L'axe est le calendrier.** Une année sans dépôt garde sa place, sa
  graduation et son palier. « Il n'a rien déposé en 2019 » n'est pas « 2019
  n'existe pas » — sept années vides chez Laurent Wauquiez, huit chez Jérôme
  Guedj.
- **Un escalier est additif**, donc aucune hauteur minimale n'est appliquée : le
  haut d'une marche est le bas de la suivante, et forcer une petite marche à se
  voir fausserait le cumul (1 dépôt sur 2 831 fait 0,15 px). C'est le **palier**,
  tracé à la hauteur exacte du cumul, qui garantit qu'aucune année ne disparaît.
  Aucun seuil n'est appliqué nulle part.
- **Le domaine est l'union des deux mesures**, jamais recalculé à la bascule :
  les dépôts de Laurent Wauquiez commencent en 2012, ses dossiers datés en 2024.
  Un axe qui bouge cesse d'être comparable — et fixé, il **montre** l'écart :
  258 de ses 584 dépôts ne sont rattachés à aucun dossier, et ces années-là
  restent vides en « dossiers amendés ».

Une carte **« N amendements adoptés »** ouvre la rangée des blocs, avant les
écartés au titre des articles 40 et 45. Elle porte un compte, rien en face :
un seul amendement adopté suffit à dire que le dépôt a produit un effet, et le
mettre en regard d'un nombre de rejets referait le bilan comptable que #328
avait déjà retiré. **Le compte porte sur tous les dépôts**, y compris ceux
qu'aucun dossier ne rattache : la somme par dossier en perdrait 6 chez Jérôme
Guedj et 25 chez Laurent Wauquiez.

## Ce que la décision a coûté, et ce qu'elle refuse

**Une passe unique.** `joinAmendements` est un générateur pour une raison
mesurée (#377, #431) : il ne se relit pas. La série année × matière est donc
accumulée **dans la même boucle** que les autres agrégats, jamais par une
seconde passe qui reconstruirait la forme plate que #431 supprime.

**Une palette catégorielle, et l'amendement de la charte qu'elle impose.**
`DESIGN_SYSTEM.md` §5 écrivait « aucune couleur n'était libre ». C'était vrai du
besoin d'alors — *marquer une ligne* dans une liste, que la fiche résout par un
filet d'encre sans teinte. Distinguer **N matières** est un besoin différent et
sans solution sans teinte : une rampe d'encre placerait les matières sur une
échelle, ce que §2 règle 1 interdit. La palette retenue (Paul Tol, qualitative
« muted ») est **sans ordre**, ne recouvre aucune teinte déjà attribuée — ni le
jaune signal, ni le vert/rouge de vote, ni le bleu/bronze des institutions — et
réserve le **gris** à « matière non établie », qui n'est pas une matière de plus
mais une absence de donnée (§2 règle 5).

**Aucun rapport entre les deux mesures.** 2 831 dépôts sur 25 dossiers ne
produit aucun ratio publiable (§6) : les deux nombres se lisent côte à côte, et
le bouton les échange au lieu de les diviser.

**Le sort d'un texte n'entre pas ici.** `textes_portes[].sort` arrive par #743,
et il ne se dérive jamais du stade : cette section ne l'utilise pas.

## Alternative écartée

**L'aire empilée par année**, essayée en maquette : elle répond « combien au
total, cette année-là » et **cache qui fait le volume** — une matière qui
explose pousse toutes les autres vers le haut, et l'œil lit une pile, pas une
série. Le trellis (une bande par matière) la corrigeait mais imposait un
arbitrage d'échelle insoluble : commune, un mois à 1 427 aplatit sept bandes sur
huit ; par bande, les hauteurs ne se comparent plus. La chute ne pose pas cette
question, parce qu'elle ne compare pas des matières entre elles — elle montre
comment le total s'est construit.

**Une librairie de graphiques** n'a pas été ajoutée. La figure est du SVG écrit
à la main : le poids et la licence d'une dépendance de rendu sont une décision à
part, et la géométrie d'un escalier empilé ne la justifie pas.
