<a id="intitule-des-lois-de-finances-1197"></a>
# Le titre d'une loi de finances est un intitulé de séance : le parseur lit `APPEL_PLF_1_20` (#1197) (2026-10-04)

`2026-10-04`

> **En bref** — les prises de parole des débats budgétaires étaient publiées sans intitulé : dans l'archive Syceron, le titre « Projet de loi de finances pour 2025 » porte `APPEL_PLF_1_20`, que le parseur ne lisait pas. **111 839 paragraphes à la XVe, 20 588 à la XVIe, 35 877 à la XVIIe** gagnent un sujet, aucun n'en change. Le code entre dans `_CODE_GRAMMAIRE_SUJET`, et `SYCERON_VERSION_INDEX` passe à `1197` : le corpus ne le reçoit qu'après un run qui collecte les interventions.

## 1. Le constat

Signalé par la session qui dessine la fiche de groupe : LIOT à la XVIIe publie
1 628 prises de parole sans intitulé sur 4 926 (hors présidence de séance), là
où les autres groupes sont entre 3 % et 13 %.

Mesuré le 04/10/2026 sur les profils publiés (privé `b76cc8d54`) : 1 432 de ces
1 628 sont de Charles de Courson, rapporteur général du budget, toutes datées
d'octobre-novembre 2024 et 2025 — la discussion des projets de loi de finances.

## 2. La cause

Un projet de loi de finances n'est pas titré comme les autres textes. Compte
rendu `CRSANR5L17S2025O1N044`, séance du 08/11/2024 :

| Niveau | `code_grammaire` | Titre |
| --- | --- | --- |
| 1 | `APPEL_PLF_1_20` | Projet de loi de finances pour 2025 |
| 2 | `APPEL_PLF_1_30` | Première partie (suite) |
| 3 | `DISC_ARTICLES_2_4` | Article 32 |

`parse_syceron._CODE_GRAMMAIRE_SUJET` ne contenait que `TITRE_TEXTE_DISCUSSION`
et les trois codes de questions. Il avait été établi sur les codes les plus
fréquents de la XVIIe, où celui-ci n'ouvre que 59 points.

## 3. La mesure, sur les trois archives

Parseur passé deux fois sur chaque compte rendu en cache, avec et sans le code,
**tous orateurs confondus** — ce sont des paragraphes d'archive, pas des entrées
de profils publiés :

| Législature | Points `APPEL_PLF_1_20` | Paragraphes | avec sujet, avant | avec sujet, après | Sujets modifiés |
| --- | --- | --- | --- | --- | --- |
| XVe | 229 | 783 386 | 671 177 | 783 016 | 0 |
| XVIe | 40 | 333 988 | 313 255 | 333 843 | 0 |
| XVIIe | 59 | 318 848 | 282 771 | 318 648 | 0 |

Les 328 titres nomment tous un texte budgétaire : loi de finances, loi de
finances rectificative, loi de finances de fin de gestion. Quatre portent
« (suite) » dans le titre même, et deux une faute de la source (« Projet de loi
finances pour 2024 », « Projet de loi de finances 2022 ») : ils sont publiés
tels que la source les écrit (§2 règle 2). `type_detail` ne change sur aucune
entrée.

Le PLFSS n'est pas concerné : il est titré sous `TITRE_TEXTE_DISCUSSION`.

## 4. La décision

1. `APPEL_PLF_1_20` entre dans `_CODE_GRAMMAIRE_SUJET`. Les niveaux inférieurs
   (`APPEL_PLF_1_30`, `PLF_PARTIES_*`, `PLF_1_1`, `PLF_3_1`) restent dehors : ils
   nomment une partie ou une mission, pas le texte.
2. `SYCERON_VERSION_INDEX` passe à `1197`, dans le même lot, comme la règle de
   #1169 l'exige : le parseur écrit autre chose dans `sujet` et
   `sujet_code_grammaire`, et un index en cache serait relu tel quel.
3. Les entrées déjà publiées reçoivent le titre par `backfill_sujet_seance`
   (#710), inchangé : elles portent la clé de preuve `sujet_code_grammaire`.

## 5. Ce que cela coûte, et ce qui n'est pas vérifié

- **Un run qui collecte les interventions** (`collect_interventions=true`) :
  l'index des trois législatures est reconstruit. Un run par défaut ne change
  rien au corpus.
- **Si l'archive de la XVe ne répond pas** — c'est arrivé au run manuel du
  03/10/2026 — ses entrées ne sont pas relues et gardent leur absence de sujet
  jusqu'au run suivant.
- `tags_thematiques` gagne les titres des lois de finances, variantes
  « (suite) » comprises.
- **Non mesuré** : le nombre d'entrées de profils publiés concernées. Les
  chiffres ci-dessus comptent les paragraphes de l'archive.

## 6. Alternative rejetée

**Reconnaître le titre par son niveau** (tout point de niveau 1 titré).
`FIN_SEAN_1_2`, « Ordre du jour de la prochaine séance », est de niveau 1 lui
aussi : le critère resterait une liste, tournée à l'envers. Le code est le
vocabulaire contrôlé de la source ; on l'étend, on ne le contourne pas.
