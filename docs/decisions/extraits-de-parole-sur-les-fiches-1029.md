<a id="extraits-de-parole-sur-les-fiches-1029"></a>

# Ce qui a été dit, sur les fiches de gouvernement et de groupe (#1029) (2026-09-22)

`2026-09-22`

> **En bref** — le cas « carburant » de #1029 doit montrer **ce qui s'est dit**, pas seulement qui a parlé. Backend publie l'extrait de 280 caractères des membres de roster et de gouvernement (#1086) et l'ancre de chaque prise de parole (#1087). L'interface les montre **dans un débat ouvert**, sur les fiches de gouvernement et de groupe, et **le filtre par mot cherche aussi dans les extraits**. Arbitré le 22/09/2026 (option A) : sur la fiche de groupe, l'extrait **nomme le député et la date de sa séance**, lu un débat à la fois, **jamais compté par personne**. Les extraits d'un maillon pèseraient ~20 Mo (RN, XVIIe, ~146 000 interventions à thème par an pour les rosters de groupe) : le build écrit donc un **index** (le vocabulaire des extraits de chaque débat, sur toute la période, 12 et 6 mois) que le filtre charge au premier mot, et **16 paquets** d'extraits dont un seul se charge quand un débat s'ouvre. Poids mesuré **avant** le run qui apporte les textes : 39,9 Mo pour les lignées, 6,9 Mo pour les gouvernements — à remesurer ensuite. Sur la fiche candidat, le lien de chaque intervention mène désormais à la prise de parole, à son ancre.

## Le contexte

La fiche de gouvernement disait qui avait parlé, sur quel débat, à quelles
séances ; la fiche de groupe, combien de membres. Ni l'une ni l'autre ne disait
ce qui avait été dit : la parole des rosters était collectée au thème seul
(#657). Backend a répondu au besoin de #1029 (voie 3) par un extrait de 280
caractères et une ancre vers la page de séance de l'AN.

## La décision

- **Une règle, `src/utils/extraits.js`**, lue par le build et le navigateur :
  le lien de séance et la coupe à 280 caractères reprennent
  `schema_pivot.url_seance_an` et `schema_pivot.extrait_de_texte` — un test
  compare les deux sur les mêmes entrées. Un membre dont la parole est collectée
  en entier (un candidat déclaré devenu ministre) est coupé à la même longueur.
- **Le débat ouvert** montre ses extraits du plus récent au plus ancien :
  orateur, date, propos, lien vers le compte rendu. Sous une période, ceux de la
  fenêtre ; sous un mot que l'intitulé ne porte pas, ceux qui le portent.
- **Le filtre par mot** garde un débat quand son intitulé porte le mot, ou quand
  le vocabulaire de ses extraits le porte, dans la période cochée. Le débat dit
  lequel des deux (`parIntitule`).
- **Sur la fiche de groupe, l'orateur est nommé** (option A) : une citation
  sourcée est un fait, comme la position d'un membre sur un scrutin (§2 règle
  7). Rien n'est additionné par personne.

## Les limites

- Le filtre ne voit que **les 280 premiers caractères** : un mot prononcé plus
  loin lui échappe. Le lien mène au texte entier.
- Le vocabulaire est celui du **débat**, pas de chaque extrait : sous plusieurs
  mots, un débat peut rester parce que deux extraits différents les portent ;
  le débat ouvert ne montre alors que les extraits qui les portent tous.
- Une entrée pas encore recollectée reste au thème seul : elle apparaît avec son
  orateur, sa date et son lien, sans propos.

## Les alternatives écartées

- **Les extraits dans la projection de la fiche** : ~20 Mo pour un maillon,
  téléchargés à chaque visite.
- **Un index par extrait** (mot → extraits) : exact sous plusieurs mots, mais
  plusieurs fois le poids du vocabulaire par débat.
- **Des extraits anonymes sur la fiche de groupe** : le lien vers la séance
  nomme l'orateur de toute façon.
