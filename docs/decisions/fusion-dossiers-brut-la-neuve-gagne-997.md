<a id="fusion-dossiers-brut-la-neuve-gagne-997"></a>
# Un dossier déjà collecté n'apprenait plus rien : au brut aussi, la neuve gagne (#997) (2026-09-18)

`2026-09-18`

> **En bref** — Le correctif de stade de #997 a traversé **quatre runs** sans
> atteindre le corpus. Ni le cache, ni l'index, ni les quatre chemins muets
> n'étaient en cause : `merge_raw_profile` fusionnait `dossiers_legislatifs[]`
> en **additif pur**, donc l'entrée ancienne était conservée inchangée et la
> neuve ignorée. Elle se fusionne désormais par `merge_dossier_records`, comme
> au pivot. Mesuré sur Édouard Philippe : **118 transitions
> `examine_commission` → `depose`**, et `examine_commission` tombe de 127 à 9.

## Ce que le run du 18/09 a éliminé

Le run 35361424164, lancé avec `collect_dossiers_legislatifs=true`, portait les
traces de #1023. Elles disent :

    [textes portés] index reconstruit depuis 4 archive(s) : 2143 acteurs.

L'index **est** reconstruit, avec les quatre archives de #1019. Les quatre
sorties muettes sont hors de cause. Et le corpus a bien bougé — +466 textes
portés sur un échantillon de 198 profils — mais **uniquement par des entrées
nouvelles** : 0 transition de stade sur les entrées déjà présentes, 0 entrée
disparue.

## La cause

`merge_raw_profile` fusionnait cette liste par `merge_lists_by_key`, dont le
contrat est explicite : « les entrées de `old_list` sont toutes conservées
**inchangées** ; seules les entrées de `new_list` dont la clé n'apparaît pas
déjà sont ajoutées ». Un dossier déjà collecté ne pouvait donc plus rien
apprendre d'une régénération.

Le pivot, lui, fusionne par `merge_dossier_records` — la neuve gagne — et le
commentaire de #743 le dit. Mais il **normalise depuis le brut** : il recevait
la vieille valeur et n'avait rien à écraser. Les deux étages étaient d'accord,
sur une donnée périmée. C'est ce qui rendait la mesure « brut ET pivot
inchangés » si convaincante, et si trompeuse.

Deux reports nommés existaient déjà au même endroit, pour le même défaut sur
d'autres champs : `backfill_dossier_nature` (#689, `nature_texte`) et
`backfill_sort_texte_porte` (#743, `sort`). Sa docstring l'écrivait mot pour
mot — « les anciens gagnent » — un an avant #997. **Aucun pour `stade`.**

## La mesure qui autorise le remplacement

`merge_dossier_records` remplace l'entrée **entière**. Il fallait donc vérifier
qu'une collecte neuve ne rend pas moins que ce qui est publié — sans quoi le
correctif aurait perdu de l'information. Mesuré le 18/09/2026, collecte réelle
(quatre archives téléchargées) contre le brut publié d'Édouard Philippe :

| | |
| --- | ---: |
| Dossiers au brut publié | 290 |
| Dossiers rendus par la collecte | 290 |
| Clés communes | **290** |
| Champs qui seraient perdus | **aucun** |
| `stade_procedural` changé | **118** |
| `sort` changé | 104 |

Toutes les transitions de stade vont dans le même sens :
`examine_commission → depose`, 118 fois. Ses `examine_commission` passent de
**127 à 9** — le chiffre qu'une reconstruction locale annonçait, et que le
corpus refusait de publier.

## Décision

**Au brut comme au pivot, la neuve gagne** sur collision de `_dossier_key`.

Ce que cela ne change pas :

1. **Un dossier que la collecte ne rend plus reste publié tel quel.** Une
   absence n'est pas une correction (§2 règle 5).
2. **Une collecte vide ne remplace rien** : `CHAMPS_PROTEGES_DU_VIDE` couvre
   `dossiers_legislatifs` en amont.
3. **#689 et #743 restent en place.** Sur le chemin nominal ils n'ont plus rien
   à faire — la neuve porte déjà sa nature et son sort — mais les retirer est
   un autre lot, avec sa propre mesure.

## Ce que le prochain run publiera

Le seuil §6 est un filtre **d'interface** (`STADES_PUBLIES` dans
`web/UI_finale/src/utils/profilCandidat.js`), pas de collecte : le pivot garde
toutes ses entrées, avec le bon stade. **Aucune cardinalité ne baisse, donc le
contrôle de perte ne bloquera pas** et `allow_declared_losses` n'est pas requis.

Ce qui change est ce que la page **affiche** : les textes redescendus à
`depose` passent sous le seuil et sortent de la section. C'est l'effet voulu de
#997 — un texte seulement déposé cessait d'être publié « en navette ». Quels
stades la fiche publie reste un arbitrage d'interface, non rendu.

## Garde

`tests/test_merge_profile.py` : un stade corrigé atteint le profil brut, un
dossier que la collecte ne rend plus reste publié, une collecte vide ne
remplace rien. Les deux premiers échouent sur le code d'avant, vérifié en le
restaurant.

**Rien ne verrouillait l'ancienne politique** : la suite entière passait avant
ce changement comme après. Un comportement que personne ne teste est un
comportement que personne ne défend — c'est ce qui a permis à quatre runs de
se convaincre que le correctif était ailleurs.

## Alternative rejetée

**Un troisième backfill, `backfill_stade_texte_porte`.** Il aurait corrigé ce
champ-ci et laissé le suivant se reperdre. Un backfill est par contrat
« strictement croissant en information » : il ne remplit qu'un champ absent.
Ici le stade est **présent et faux**, ce qui n'est pas le même travail. Trois
contournements au même endroit disent que c'est la politique de fusion qui est
en cause, pas le champ.
