<a id="fonction-sur-la-forme-reduite-1200"></a>
# La qualité de l'orateur survit à la forme réduite : `fonction` pour les membres de groupe et de gouvernement (#1200) (2026-10-04)

`2026-10-04`

> **En bref** — `fonction` (« ministre », « rapporteur général ») était publiée sur la forme complète des candidats déclarés et sur **aucune des 1 197 491 prises de parole réduites** des membres de groupe et de gouvernement : la forme réduite ne la reprenait pas, ni à la collecte ni à la normalisation. La source la porte sur environ un paragraphe sur six. Elle est désormais gardée quand elle est lue, `SYCERON_VERSION_INDEX` passe à `1200`, et le corpus la reçoit par le report des faits de source après un run qui collecte les interventions.

## 1. Le constat

Signalé par la session qui dessine la fiche de groupe. La propriétaire a décidé
de retirer de la parole d'un groupe celle qu'un membre a prononcée comme membre
du gouvernement ; l'interface la reconnaît à `fonction`. Or :

Mesuré le 04/10/2026 (privé `5b421000c`), entrées Syceron des profils bruts,
jointes à leur entrée pivot :

| Population, forme | Entrées | avec `fonction` au brut | au pivot |
| --- | --- | --- | --- |
| candidats déclarés, complète | 27 631 | 6 782 | 6 782 |
| membres de groupe, extrait | 1 144 691 | 0 | 0 |
| membres de groupe, thème seul | 2 361 | 0 | 0 |
| membres de gouvernement, extrait | 50 438 | 0 | 0 |

Élisabeth Borne, Première ministre, publie 4 213 prises de parole sans une
seule qualité ; la fiche de gouvernement s'en remettait à la fenêtre de dates.

## 2. La cause

La source porte le champ. Parseur passé sur les archives en cache : une
`<qualite>` sur 50 526 des 318 848 paragraphes de la XVIIe, 58 362 des 333 988
de la XVIe — « ministre », « rapporteur », « rapporteur général », « garde des
sceaux ».

La forme réduite est un **second écrivain**, et il ne la reprenait pas :
`candidate_profile._reduire_au_theme` ne posait pas la clé au brut, et la
branche réduite de `normalize_profil._normalize_intervention` ne l'aurait pas
publiée. #1169 avait fait entrer `role_seance` dans cette forme et nommé
`fonction` dans `CHAMPS_FAITS_DE_SOURCE`, sans voir que la forme réduite ne
l'écrivait pas.

## 3. La décision

1. `_reduire_au_theme` garde `fonction`, **seulement quand la source la porte** :
   la clé est absente, jamais nulle (§2 règle 5), comme `role_seance`.
2. La branche réduite de `normalize_profil` la publie de même.
3. `SYCERON_VERSION_INDEX` passe à `1200` : le parseur n'a pas changé, mais ce
   que l'index réduit contient, si — c'est le cas que la règle de #1169 vise.
4. Les entrées déjà publiées la reçoivent par `reporter_faits_de_source`,
   inchangé : `fonction` y est nommée depuis #1169.

## 4. Ce que cela coûte, et ce qui n'est pas vérifié

- **Le poids** : 1,8 Mo pour tous les paragraphes de l'archive de la XVIIe,
  2,1 Mo pour la XVIe. C'est un majorant — seuls les paragraphes des profils
  publiés sont écrits — et la XVe n'a pas été mesurée.
- **Un run qui collecte les interventions**, et qui reconstruit l'index des
  trois législatures.
- **Non vérifié** : la couverture réelle sur les profils publiés, qui se mesure
  après le run.

## 5. Alternative rejetée

**Laisser l'interface déduire la fonction de la fenêtre du mandat
gouvernemental.** C'est ce que la fiche de gouvernement faisait faute de mieux.
Une fenêtre dit quand la personne était ministre, pas à quel titre elle a pris
la parole ce jour-là : un rapporteur général devenu ministre, un ministre
redevenu député dans la même législature, se lisent faux. Le compte rendu le
dit paragraphe par paragraphe ; on publie ce qu'il dit.
