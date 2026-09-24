<a id="etalement-disque-index-de-mots-1121"></a>
# L'index de mots des amendements s'étale sur disque, et la fabrique de référence reste (#1121) (2026-09-24)

`2026-09-24`

> **En bref** — Construire l'index de mots d'une législature tenait toute l'archive en mémoire : 3,9 Go sur la XVe, et un essai tué par le noyau à 2,87 Go. `document_depuis_archive` fait le même document par seaux temporaires — **315 Mo de pic**, pour 157 s au lieu de 131. `document` reste, et un test compare les deux sur une archive.

## Constat

24/09/2026. Le contenu de la XVe (311 934 amendements) ne se construit pas sur
une machine de 7,8 Go dont un navigateur occupe 2,7 : le noyau tue le processus
à **2,87 Go**. Relancé après libération manuelle de la mémoire, il aboutit, pic
mesuré **~3,9 Go**.

Une construction qui n'aboutit que si la machine est par ailleurs au repos
n'est pas une construction : c'est une chance. La CI ne l'offre jamais, et
`extract-amendements-an` enchaîne les législatures closes dans un même job de
30 minutes.

La cause est `lire_archive`, qui rend `{uid: (article, mots)}` pour **tous** les
amendements à la fois — des centaines de milliers d'ensembles de chaînes.

## Décision

`document_depuis_archive` construit le même document **sans jamais tenir
l'archive**, par le remède que le dépôt applique déjà aux actes du Journal
officiel (`actes_reglementaires.Moisson`) : des seaux temporaires.

Trois passes, et ce qui reste en mémoire est nommé à chaque fois :

1. **Lire l'archive une fois.** On garde les uid et leur article — les seuls
   faits qu'on ne peut pas recalculer — et un simple COMPTE par mot. Les mots
   de chaque exposé partent sur disque, une ligne par amendement.
2. **Arrêter le vocabulaire**, puis relire ces lignes pour ranger chaque
   `(forme indexée, position)` dans l'un des `NB_SEAUX` seaux.
3. **Regrouper seau par seau.** Un seau tient seul en mémoire, et les positions
   d'une forme sont toutes dans le même : c'est ce que `hash_seau` garantit.

**L'ordre des deux premières passes n'est pas un détail d'implémentation.** La
fusion des formes (`fiscaux` → `fiscal`) n'a le droit de rapprocher deux mots
que si la forme de base existe dans le vocabulaire — donc le vocabulaire entier
doit être arrêté avant qu'un seul couple parte en seau. C'est ce qui interdit
de tout faire en une passe, et c'est la différence avec les actes, où le seau
d'un article se connaît dès sa lecture.

### Mesuré, sur les deux archives disponibles

| | XVe | XVIe |
| --- | --- | --- |
| Amendements | 311 934 | 163 789 |
| Pic mémoire, en mémoire | ~3,9 Go | non mesuré |
| Pic mémoire, par seaux | **315 Mo** | **197 Mo** |
| Durée | 157 s (contre 131) | 83 s |
| Document produit | **identique**, `genere_le` excepté | **identique** |

Douze fois moins de mémoire pour 20 % de temps en plus. La XVe s'est construite
avec 2,3 Go de disponible, ce qui était impossible la veille.

## `document` reste, et c'est délibéré

La fabrique en mémoire n'est pas remplacée : elle devient la **référence**.
Elle est courte, elle se lit d'un trait, et
`test_les_deux_fabriques_rendent_le_meme_document` construit une archive puis
compare les deux sorties. Sans elle, l'étalement n'aurait rien contre quoi se
vérifier — et un écart entre les deux ferait dépendre le corpus publié de la
façon dont il a été construit, ce qui est exactement ce qu'on refuse.

`ecrire_contenu_cache` (la CI) et la ligne de commande empruntent l'étalement.

## Au passage : `hash_seau` et `NB_SEAUX` ne sont plus définis deux fois

Ils existaient dans `actes_reglementaires`, et les redéfinir ici les aurait
rendus **ambigus** pour `scripts/generer_decisions_par_module.py`, qui laisse
tomber de sa table tout symbole défini dans plusieurs modules de `src/` : une
décision qui les nommerait aurait été silencieusement amputée. Ils sont donc
définis ici, et `actes_reglementaires` — qui importait déjà de ce module — les
importe. Aucune décision ne les nommait au moment du changement ; c'est le
genre de piège qui ne se voit qu'une fois posé.

## Alternative écartée : borner la mémoire par un découpage de l'archive

Construire par tranches de N amendements, puis fusionner les documents. Refusé
pour la même raison qui impose l'ordre des passes : les seuils de fréquence et
la fusion des formes se calculent sur **toute** la législature. Une tranche ne
sait pas si un mot est trop fréquent, ni si sa forme de base existe ailleurs —
et une fusion de documents partiels redonnerait un résultat qui dépend du
découpage.
