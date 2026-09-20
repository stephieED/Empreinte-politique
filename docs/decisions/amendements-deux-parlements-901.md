<a id="amendements-deux-parlements-901"></a>

# Les amendements de la fiche se lisent par parlement, derrière un commutateur partagé (#901) (2026-09-17)

`2026-09-17`

> **En bref** — La carte des amendements mêlait les dépôts de l'Assemblée et
> ceux du Parlement européen sur un axe de commissions françaises : 2 615 des
> 2 944 dépôts d'Emmanuel Maurel tombaient dans « Matière non établie ». Les
> deux populations sont désormais séparées, l'axe européen est la commission
> saisie au fond du dossier (3 557 dépôts sur 3 690, 96 %), et un seul
> commutateur — dupliqué au-dessus de chaque figure, jamais dédoublé en deux
> états — règle le parlement de toute la section.

## Le constat

`amendements[]` porte deux populations que rien ne distingue à la lecture de la
carte : 172 244 dépôts et cosignatures résolus dans l'index partagé, et 7 303
dépôts européens que cet index ne connaît pas (candidats déclarés, mesuré le
17/09/2026). La figure trie par **commission**, et `commissions_dossiers.json`
est le référentiel de l'Assemblée : aucun dossier européen n'y figure.

Rendu, chez Emmanuel Maurel : « 2 944 amendements · 18 dossiers · 38 adoptés »,
et 2 615 lignes dans « Matière non établie ». Chez Florian Philippot, « 11
amendements · 0 dossiers », une seule ligne grise — alors que ses deux dossiers
européens nomment chacun leur commission. Le fait existe dans la source ; c'est
la figure qui ne pouvait pas le lire.

## La décision

**1. Deux populations, deux agrégats, jamais un total.** Le partage se lit dans
la donnée et non dans une heuristique : un dépôt français porte un
`amendement_id`, un dépôt européen porte `amendement_non_resolu.institution ==
"parlement_europeen"` et aucun `amendement_id` — sans un seul cas mixte sur les
179 547 entrées des candidats déclarés. `buildCandidateView` publie
`amendementsParVersant.{francais, europeens}`, chacun agrégé avec **son**
résolveur de commission.

**2. L'axe européen est la commission saisie au fond**, sous le nom que le
Parlement européen publie — en anglais, comme les familles OEIL de la cascade
(`axe-europeen-prorata-domaines-901`). 3 557 des 3 690 dépôts comme auteur
principal en portent une (96 %) ; une saisine conjointe ne vaut qu'à défaut
d'une saisine au fond. Ce que le dossier ne nomme pas reste « Matière non
établie » — 46 dépôts sur 2 609 chez Maurel —, jamais déduit d'un intitulé
(§2 règle 2).

**3. Un seul versant pour la section, commandé depuis deux endroits.** Le
commutateur est posé au-dessus des textes portés **et** au-dessus des
amendements ; les deux règlent le même état. Un lecteur qui change de parlement
au bas de la section n'a pas à remonter d'un écran, et les deux figures ne
peuvent pas se contredire. Changer de versant referme la matière choisie :
« Finances » et « Legal Affairs » ne vivent pas dans le même référentiel.

**4. Il porte les mots de « Ce qu'il a dit »** — « En qualité de député(e) » et
« En qualité de député(e) européen(ne) », leur pastille d'institution et leur
effectif après un point médian, depuis `LIBELLE_QUALITE`. La fiche comptait déjà
un commutateur qui distingue les deux parlements ; un second vocabulaire aurait
fait lire deux mécaniques là où il n'y en a qu'une. La puce n'est pas redéfinie :
une seule définition de l'objet, dans `ParolesParPeriode.css` (#672).

**5. Trois fiches sur dix-sept portent les deux parlements** (Maurel, Le Pen,
Mélenchon). Trois n'ont que l'européen (Glucksmann, Massard, Philippot) : aucun
commutateur, et le titre nomme le parlement. Un versant vide garde son titre et
son commutateur, faute de quoi « aucun amendement » se lirait comme un vide de
collecte quand l'autre versant en porte des milliers (§2 règle 5).

**6. La colonne des noms tient les intitulés européens.** Elle monte de 200 à
290 px et la barre voisine rend la place (1.2fr → 0.9fr) : « Environment,
Public Health and Food Safety » fait 41 signes là où « Finances » en fait 8, et
quatre noms sur dix-neuf étaient tronqués. La colonne ne s'élargit qu'autant que
son contenu le demande, donc le versant français ne bouge pas.

## Ce qui n'est pas fait, et pourquoi

**« Les grands chiffres » comptent toujours la population entière**, et y rangent
les dépôts européens sous « À l'Assemblée » — défaut antérieur à ce lot. Le
corriger demande de créer un point d'amendements dans la colonne du Parlement
européen, ce qui est un arbitrage de la trame de #328, pas une conséquence de
celui-ci. Retirer les dépôts européens de ce compte sans leur écrire leur point
les ferait simplement disparaître de la fiche.

**Sur mobile, les noms sont encore tronqués** : sous 720 px la figure passe à
quatre colonnes et l'intitulé prend `1fr`. Les faire passer à la ligne est une
retouche de la figure, à voir avec le lot mobile (#867), où le débordement
horizontal de « Les grands chiffres » reste ouvert.

## L'alternative écartée

**Un commutateur propre à chaque carte, avec deux états indépendants.** Il
permettait de lire les textes européens à côté des amendements français. Écarté :
la section publie deux populations d'un même mandat, et deux commutateurs voisins
réglés différemment se lisent comme un seul mal rafraîchi. La duplication retenue
garde l'ergonomie — commuter sans remonter — sans le second état.
