<a id="tags-singulier-et-pluriel-1042"></a>
# Un singulier et un pluriel sont le même sujet : la clé groupe, la source publie (#1042) (2026-09-20)

`2026-09-20`

> **En bref** — « motion de censure » et « motions de censure » arrivaient en
> **première et deuxième ligne** de la fiche du gouvernement Borne, avec 19 et
> 12 porteurs. Les étiquettes se regroupent désormais sur une clé au **pluriel
> simple**, et la forme publiée reste **celle que la source écrit** — jamais la
> clé, qui n'a parfois jamais été écrite.

## Contexte

Signalé par la session « UI gouv » le 20/09/2026, à la demande de la
propriétaire, et remesuré côté backend. `deriver_tags_thematiques` rangeait un
thème en `theme.strip().lower()` : deux `theme_officiel` distincts dans le
compte rendu font deux étiquettes, et l'Assemblée écrit tantôt l'un, tantôt
l'autre.

| Collection | Fiches | Étiquettes | Groupes singulier/pluriel |
| --- | --- | ---: | ---: |
| `pivot_data/gouvernements/` | 17 | 5 726 | **10**, sur 4 fiches |
| `pivot_data/lignees/` | 12 | 21 681 | **48**, sur 11 fiches |

C'est **peu et très visible** : ces étiquettes-là sont fréquentes, donc elles
remontent en tête. Récurrents : *motion / motions de censure*, *rappel /
rappels au règlement*, *pénurie / pénuries de médicaments*, *fermeture /
fermetures de classes*, *narcotrafic / narcotrafics*.

## Décision

**La clé regroupe, la source publie.**

1. `cle_tag_thematique` retire le `s` final de chaque mot de plus de trois
   lettres. Volontairement naïve : elle ne rapproche que ce qu'un `s` sépare.
2. `forme_publiee` rend la forme **la plus fréquente** parmi celles observées,
   l'ordre alphabétique départageant une égalité — déterministe, donc deux
   profils traités séparément publient la même.
3. Les **trois** consommateurs groupent sur cette clé :
   `deriver_tags_thematiques`, `group_profile.aggregate_tags_thematiques`,
   `gouvernement_profile.agreger_tags_thematiques`. Corriger la seule fabrique
   n'aurait rien changé aux fiches : chaque agrégat compte de son côté, et deux
   membres écrivant deux formes auraient toujours fait deux lignes.

## La mesure qui décide de la forme publiée

Sur un profil publié sur quatre : **4 025 clés, 10 à plusieurs formes**. Et
parmi ces 10, **4 ont une forme normalisée que la source n'écrit jamais** :

| Clé | Formes observées |
| --- | --- |
| `pénurie de médicament` | « pénurie de médicaments » (7), « pénuries de médicaments » (1) |
| `fermeture de classe` | « fermetures de classes » (11), « fermeture de classes » (2) |

Publier la clé fabriquerait un intitulé que personne n'a écrit — exactement ce
que §2 règle 2 interdit. La forme publiée est donc toujours une forme de la
source.

## Ce que ça change au corpus

Recalculé sur 346 profils (1 sur 4) : **15 672 étiquettes → 15 607**, soit
**−65** sur 61 profils. `tags_thematiques` étant un champ **dérivé**, recalculé
à chaque fusion (#710), le corpus suivra au prochain run sans retrait nommé.

## Ce que le seuil ne protège pas, et pourquoi c'est sans conséquence

« gaz » reste intact ; « sens » rend « sen » et « ours » rend « our ». La clé
ne sert qu'à **regrouper** : il faudrait qu'un « sen » existe par ailleurs pour
que deux sujets se confondent. Sur les 4 025 clés mesurées, les 10 groupes
formés sont tous des variantes singulier/pluriel du même intitulé.

## Alternatives rejetées

**La lemmatisation** et **une table d'alias**. Les deux décideraient que deux
intitulés publiés par la source n'en font qu'un — une normalisation
éditoriale, qui n'a pas été demandée, et qui ferait de la table l'endroit où
l'on arbitre ce qu'est un sujet. Le pluriel simple, lui, se vérifie à l'œil sur
chaque groupe formé.

**Fusionner côté interface**, ce que la session « UI gouv » s'est refusée à
faire, pour la même raison : ce n'est pas à l'affichage de décider que deux
intitulés publiés n'en font qu'un.
