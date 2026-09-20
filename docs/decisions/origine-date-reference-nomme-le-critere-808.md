# L'origine de la date de référence nomme le critère, plus un événement (#808)

`2026-09-10`

> **En bref** — `date_reference.origine` valait `cloture_legislature` dès que toutes les appartenances d'un groupe sont refermées : critère de **calcul** exact, étiquette **fausse** pour deux fiches sur douze, dissoutes en cours de législature — `NG-15` s'arrête au 11/09/2018 quand la XVe se clôt le 21/06/2022, **3 ans 9 mois** d'écart, `EDS-15` 1 an 8 mois ; un lecteur y lisait « effectif à la fin de la XVe » là où la donnée dit « effectif au dernier jour d'existence du groupe » — le chiffre juste, la phrase fausse (§2 règle 2), soit le défaut de #653 un cran plus bas. La valeur devient **`derniere_appartenance_close`**, et l'avertissement publié — qui est la part réellement lue — nomme désormais le cas au lieu d'annoncer une clôture. L'ancien nom reste **accepté en lecture et jamais écrit** : les 14 fiches qui le portent ne seront régénérées qu'au prochain run, et le portail échouerait entre-temps sur des fichiers que personne n'a touchés ; les 2 fiches Sénat **gelées** ne portent aucun `date_reference`, donc le cas d'un nom à garder pour toujours ne se présente pas. **Écarté** : scinder en deux valeurs selon que la dernière appartenance coïncide ou non avec la clôture — il faudrait la date de clôture de chaque législature, pour une nuance que la date publiée donne déjà. Suite complète à 4 426, 0 échec.

## Contexte

`date_reference.origine` est un vocabulaire fermé à deux valeurs (#653). L'une
d'elles nommait mal ce qu'elle désignait.

`cloture_legislature` était posée dès que **toutes les appartenances du groupe
sont refermées**, la date retenue étant la dernière `fin_dans_groupe`. C'est un
critère de **calcul**, et il est exact.

Mais l'étiquette annonçait un **événement**, et deux fiches publiées ne l'ont
jamais connu — dissoutes en cours de législature :

| Fiche | `date_reference.date` | Clôture réelle | Écart |
| --- | --- | --- | ---: |
| `groupe-AN-NG-15` | `2018-09-11` | `2022-06-21` | **3 ans 9 mois** |
| `groupe-AN-EDS-15` | `2020-10-16` | `2022-06-21` | 1 an 8 mois |

Les douze autres fiches à appartenances closes portent bien la date de clôture
de leur législature.

Un lecteur voyant `cloture_legislature` sur `NG-15` lisait « effectif à la fin
de la XVe » là où la donnée dit « effectif au dernier jour d'existence du
groupe ». **Le chiffre était juste, la phrase qui l'accompagnait ne l'était
pas** (§2 règle 2) — le défaut même de #653, un cran plus bas : là un compteur
disait « aujourd'hui » sans le dire, ici une étiquette disait un événement qui
n'avait pas eu lieu.

## La décision

`ORIGINE_DATE_REFERENCE_CLOTURE` vaut désormais **`derniere_appartenance_close`**.

**Écarté** : scinder en deux valeurs selon que la dernière appartenance coïncide
ou non avec la clôture de la législature. Il faudrait connaître la date de
clôture de chaque législature, et cela ajouterait un cas au vocabulaire fermé
pour une nuance que la date publiée donne déjà au lecteur.

**Écarté aussi** : ne rien changer et documenter. La valeur est publiée pour
être lue.

## L'ancien nom reste valide en lecture

`ORIGINE_DATE_REFERENCE_CLOTURE_HERITEE` garde `cloture_legislature` dans
`ORIGINES_DATE_REFERENCE`, **accepté et jamais écrit**.

Les 14 fiches qui le portent seront régénérées au prochain run, mais une fiche
publiée doit continuer de valider entre le déploiement du code et ce run —
sans quoi le portail de qualité échouerait sur des fichiers que personne n'a
touchés. `web/UI_finale/src/utils/groupe.js` fait de même et rend les deux sous
le même libellé.

**Les deux fiches Sénat gelées ne sont pas concernées** : vérifié, elles ne
portent aucun `date_reference`. Le cas qui aurait exigé de garder l'ancien nom
pour toujours — une fiche jamais régénérée le portant — ne se présente pas.

## L'avertissement de fiche disait la même chose, et il le disait à l'écran

Le texte publié dans `meta.warnings` affirmait « tous les comptes de cette fiche
se rapportent au …, clôture de la législature ». Il dit maintenant « jour de la
dernière appartenance close », et nomme le cas : *« qui n'est pas toujours la
clôture de la législature — `NG-15` s'arrête au 11/09/2018, la XVe au
21/06/2022 »*.

C'était le vrai enjeu : la valeur est technique, cette phrase est lue.

## Hors périmètre

L'enveloppe d'appartenance, instruite en #809 : `debut_dans_groupe` /
`fin_dans_groupe` recollent en un intervalle des périodes qui en comptent
plusieurs. Distinct — ici c'est le **nom** d'une date, là c'est la **forme**
d'une période.

Suite complète à 4 426, 0 échec.
