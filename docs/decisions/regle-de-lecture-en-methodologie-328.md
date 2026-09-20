<a id="regle-de-lecture-en-methodologie-328"></a>

# La règle de lecture quitte la fiche pour la méthodologie, parce qu'elle est désormais appliquée (#328) (2026-09-10)

`2026-09-10`

> **En bref** — relue à l'écran, la section « ce qu'il a voté » portait **quatre énoncés de règle avant la moindre figure**, dont la dernière lecture écrite **deux fois** — en étiquette du chiffre et en phrase entière sous la figure. #711 avait exigé cette phrase sur la fiche parce que la méthodologie **annonçait** une règle que rien n'appliquait ; depuis #711 c'est le **code** qui l'applique (`isWholeTextVote` et le repli sur la date, dans `utils/lecture.js`), et une promesse non tenue ne peut plus réapparaître en silence — il faudrait retirer l'implémentation, et les tests qui la gardent échoueraient. **#711 est donc renversé sur la place de sa phrase, jamais sur son fond** : restent sur la fiche `LAST_READING_LABEL` — sans elle le lecteur compare des textes à des votes — et le renvoi vers `/methodologie#votes` posé sous la figure ; le raisonnement vit là où il s'argumente. C'est `DESIGN_SYSTEM` §7 règle 2 appliquée : l'étiquette est les deux mots, la phrase était le paragraphe. **Écarté** : une phrase courte de remplacement, qui ne dirait rien que l'étiquette ne dise et rouvrirait ce que le lot ferme. Trois tests suivent, chacun disant pourquoi.

## Le contexte

`docs/decisions/derniere-lecture-retenue-711.md` a corrigé un défaut précis :
la page de méthodologie **annonçait** la règle de la dernière lecture — « pour
un même texte, seule la lecture la plus avancée connue est conservée » — alors
que **rien ne l'appliquait**. Une règle annoncée sans être appliquée est pire
que pas de règle du tout : elle donne au lecteur une garantie qui n'existe pas.

#711 a donc fait deux choses, et une seule était le correctif : il a
**implémenté** la règle — `isWholeTextVote` et le repli sur la dernière lecture
vivent dans `web/UI_finale/src/utils/lecture.js`, la date ordonne, sur le corpus
entier des scrutins — et il a exigé que sa **phrase** soit publiée sur la fiche,
à côté du chiffre, pas seulement en méthodologie.

Trois tests figeaient cette seconde exigence :
`test_derniere_lecture_711.py::test_le_libelle_affiche_dit_la_regle_a_cote_du_chiffre`,
`test_pourquoi_en_methodologie_328.py::test_le_critere_des_votes_ne_redit_plus_la_regle_de_derniere_lecture`
et `test_votes_par_periode_328.py::test_seul_le_pourquoi_des_deux_regles_part_dans_la_methodologie`.

## Le constat, à l'écran

Relue sur la page servie le 10/09/2026, la section « ce qu'il a voté » portait
**quatre** énoncés de règle avant la moindre figure :

| Où | Quoi |
| --- | --- |
| Critère de section | « Une position par texte, rangée par période politique. Aucun taux de participation n'est publié. » |
| Bandeau, ligne 1 | « 111 textes — dernière lecture retenue pour chaque texte » |
| Bandeau, ligne 2 | « tirés de 150 votes sur l'ensemble d'un texte, parmi 2 035 positions » |
| Sous la figure | `LAST_READING_RULE.phrase` + `WHOLE_TEXT_VOTE_BOUND.phrase` — deux phrases entières |

La règle de la dernière lecture y était écrite **deux fois** : en étiquette du
chiffre, et en phrase sous la figure. Le « taux de participation » du critère
est déjà refusé en méthodologie et dans le pied du site.

## La décision

**Sur la fiche restent l'étiquette du chiffre et le renvoi.**
`LAST_READING_LABEL` — « dernière lecture retenue pour chaque texte » — accompagne
le nombre de textes, parce que sans elle le lecteur compare des textes à des
votes. Le renvoi vers `/methodologie#votes` est posé sous la figure. Le
raisonnement complet — quatre lectures d'un même texte, un code de scrutin qui
ne sépare pas l'ensemble de l'article — vit en méthodologie, où il s'argumente.

**Ce qui rend ce déplacement possible, et qui n'était pas vrai en #711 : la
règle est appliquée.** L'incident que #711 corrigeait était une méthodologie qui
promettait ce que le code ne faisait pas. Depuis #711, c'est le **code** qui
applique la règle, et `test_derniere_lecture_711.py` le vérifie sur la
fonction, pas sur une phrase. Une promesse non tenue ne peut plus réapparaître
en silence : il faudrait retirer l'implémentation, et les tests qui la gardent
échoueraient.

Autrement dit, #711 est renversé sur **la place de sa phrase**, jamais sur
**son fond**. La distinction est celle de `DESIGN_SYSTEM` §7 règle 2 : « une
limite tient en deux mots, une explication en paragraphe ». L'étiquette est les
deux mots ; la phrase était le paragraphe.

## L'alternative écartée

**Garder une phrase courte sur la fiche**, du genre « une position par texte,
sa dernière lecture ». Elle ne dit rien que l'étiquette ne dise déjà, et elle
rouvre exactement ce que ce lot ferme : une section qui énonce ses règles avant
de montrer son fait. Mesuré sur la page rendue, les quatre énoncés ci-dessus
occupaient la hauteur d'écran qui précède la figure — le lecteur lisait la
consigne à la place du fait.

## Ce qui reste garanti par les tests

- le chiffre affiché porte `LAST_READING_LABEL` ;
- il est bâti sur `votes.textes`, les textes retenus, jamais sur les votes ;
- le raisonnement est publié en méthodologie (`LAST_READING_RULE`,
  `WHOLE_TEXT_VOTE_BOUND`) ;
- le renvoi vers `/methodologie#votes` est posé sous la figure ;
- aucun `.pourquoi` n'est rendu sur la fiche.
