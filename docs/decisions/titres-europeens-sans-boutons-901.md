<a id="titres-europeens-sans-boutons-901"></a>
# Un titre européen perd ses boutons de téléchargement, et rien d'autre (#901) (2026-09-15)

`2026-09-15`

> **En bref** — ParlTrack ne lit aucune base du Parlement européen : il recopie
> la page, et ramasse avec le titre les boutons « PDF (268 KB) DOC (71 KB) ».
> 68,7 % des titres d'activités portées du dump en portent. On les retire **à
> l'entrée du corpus**, parce qu'un libellé de bouton n'est pas un fait sur le
> texte. On ne touche ni aux intitulés dédoublés ni aux espaces manquants : les
> réparer serait reconstruire.

## Contexte

L'interface a signalé le 14/09/2026 que **314 des 383** titres de textes portés
européens portaient du balisage, et a refusé de maquetter le panneau européen
dessus : « une maquette sur des titres illisibles ferait valider une forme qui ne
tiendra pas sur les titres corrigés ». Elle a explicitement demandé de **ne pas**
nettoyer par expression régulière côté affichage — ce qui masquerait le défaut
sans le corriger — et de dire, si la source ne publie que la page, que c'est une
limite.

## Ce que la mesure a établi

La pollution n'est **pas** produite chez nous. `build_activities_index` recopiait
`entree["title"]` tel quel ; c'est le dump qui la porte.

Mesuré le 15/09/2026 sur `ep_mep_activities` — 27 576 des 40 146 titres
d'activités portées (**68,7 %**), et 7 des 13 types d'activité :

| Type | Titres pollués |
| --- | ---: |
| `MINT` | 91,4 % |
| `REPORT` | 88,9 % |
| `IMOTION` | 86,6 % |
| `REPORT-SHADOW` | 80,7 % |
| `MOTION` | 71,5 % |
| `WQ` (questions écrites) | 68,1 % |
| `OQ` (questions orales) | 63,5 % |
| `CRE`, `WEXP`, `COMPARL`, `COMPARL-SHADOW`, `WDECL` | 0 % |

Les espaces manquants aux jointures — « RESOLUTIONpursuant », « Procedureon » —
signent la concaténation de nœuds HTML : c'est la preuve que le titre est
assemblé depuis une page, pas lu dans un champ. **La source ne publie aucun
champ titre propre.**

## Décision

1. **La queue de boutons est retirée à la projection**
   (`titre_sans_boutons`, appelée dans `build_activities_index`), donc une seule
   fois, à l'entrée du corpus. La faire plus loin laisserait chaque consommateur
   réinventer sa règle — et l'interface a raison de refuser de porter ça.

2. **La règle est étroite** : un type de fichier, une taille chiffrée, une
   unité. Un titre qui parle de PDF sans cette forme n'est pas touché.

3. **`VERSION_SCHEMA_INDEX` passe de 3 à 4.** Troisième fois en deux jours que
   cette constante sauve un correctif : sans elle, le cache
   `public-data-cache-parltrack-<semaine>` resservirait l'index déjà bâti, avec
   ses titres pollués, pendant une semaine entière.

4. **Rien d'autre n'est corrigé.** Ni les intitulés répétés deux fois d'affilée,
   ni les espaces manquants. Aucune règle ne les distingue d'un titre
   légitimement redondant ou d'un mot composé, et les réparer produirait un
   intitulé que personne n'a écrit. C'est la limite, et elle est déclarée.

## Pourquoi c'est compatible avec §2 règle 2

La règle interdit de publier un fait qui ne remonte pas à une source primaire.
Retirer « PDF (235 KB) » **n'ôte aucun fait** : ce n'est pas une information sur
le texte, c'est le libellé d'un bouton de la page. Le `source_url` publié mène
toujours à cette page, où le lecteur retrouve titre *et* boutons.

La frontière est là, et elle est nette : **on retire ce que la page affiche
autour du texte, jamais ce qu'elle dit du texte.**

## Ce que la règle fait vraiment, mesuré

737 498 titres du dump : **85 952 modifiés (11,7 %)**, **0** perdant plus de 40
caractères, **0** gardant un « PDF ( » résiduel.

**1 035 deviennent vides** — ils n'étaient *que* des boutons. Le nettoyage n'y
détruit rien : il révèle une absence que le faux titre masquait (§2 règle 5).
Aucun n'est dans notre population : sur les 383 textes portés européens publiés,
314 sont nettoyés et **zéro** ne devient vide.

## Alternative rejetée

**Nettoyer à l'affichage.** C'est ce que l'interface a refusé, et elle a raison :
le corpus continuerait de porter un faux titre, chaque consommateur écrirait sa
propre règle, et les deux autres défauts resteraient invisibles au lieu d'être
déclarés. Un défaut masqué à un endroit est un défaut qui réapparaît ailleurs.
