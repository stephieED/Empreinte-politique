<a id="parole-de-groupe-par-appartenance-et-fenetre-1073"></a>
# La parole d'un groupe est celle tenue pendant l'appartenance, comptée sur 6 et 12 mois (#1073) (2026-09-22)

`2026-09-22`

> **En bref** — L'interface demandait, pour chaque débat d'un groupe, le nombre de membres intervenus sur 6 mois, 12 mois et toute la période. La mesure a montré que le compte publié incluait la parole de membres partis ou pas encore arrivés — 7 308 interventions sur EPR-17. Arbitré le 22/09/2026 : seule compte la parole tenue pendant l'appartenance, sur les trois fenêtres.

## Le besoin

Remonté par la session interface (#1073) : la fiche de groupe reçoit un filtre
à durées fixes, arbitré le 22/09/2026. `tags_thematiques_agreges` ne portait
aucune date.

## Ce que la mesure a trouvé

Le prototype sans filtre reproduisait exactement les 1 126 débats de RN-17. Mais
un membre comptait pour **toute la législature**, alors que sa fiche publie ses
dates d'appartenance :

| Fiche | Interventions hors appartenance | Débats, avant → après |
| --- | ---: | --- |
| EPR-17 | 7 308 | 1 953 → 1 840 |
| DR-17 | 3 302 | 1 218 → 1 028 |
| HOR-17 | 1 001 | 836 → 715 |
| RN-17 | 971 | 1 126 → 1 118 |
| REN-16 | 15 555 | 2 163 → 1 899 |

Cas réel : Christine Engrand quitte le RN le 19/11/2024 et prend la parole le
01/04/2025 et le 17/02/2026 — comptée pour le RN. Sur RN-17, 956 des 971
entrées sont des interventions de Marine Le Pen au Parlement européen,
antérieures au groupe : elles ne portent aucune étiquette (voir `_tags_du_membre`),
elles ne changent aucun compte, elles sont seulement déclarées.

## Décision

Arbitrage de la propriétaire, option A : le filtre d'appartenance vaut pour les
trois fenêtres.

1. `_interventions_retenues` garde la législature de la fiche (#825), puis la
   parole datée **dans** les périodes d'appartenance (`periodes_d_appartenance`).
2. Une appartenance non datée garde toute la législature (§2 règle 5), comptée
   en avertissement. Une intervention sans date compte sur la période, jamais
   dans une fenêtre.
3. `fenetres_parole` : bornes comptées depuis `date_reference.date`, jamais
   avant `periode.debut`, et `nb_membres`, le dénominateur (§2 règle 7).
4. `nb_membres_porteurs_par_fenetre` : membres **distincts** par fenêtre.
5. La lignée applique le même filtre, sur l'union des périodes d'un membre dans
   les maillons d'une même législature.
6. La projection d'un membre (`CLES_LUES_PAR_ENTREE`) garde désormais `date`.

## Alternatives rejetées

- **Filtrer les seules fenêtres** (option B) : « toute la période » restait
  fausse sur EPR, et incohérente avec les deux autres.
- **Des comptes par mois** : des membres distincts ne s'additionnent pas d'un
  mois à l'autre.
- **Des dates par membre** : un relevé d'activité individuel dans un fichier
  public, sur des profils de roster qui ne sont pas des fiches publiées (§2
  règles 3 et 7).

## Poids

Mesuré sur les 11 fiches de la XVIIe : l'agrégat passe de 60–230 Ko à
99–371 Ko par fiche (JSON indenté). Côté interface, deux entiers par débat dans
`lignees/<id>.debats.json` : 22 694 débats sur toutes les fiches, soit 88 à
132 Ko de plus (estimé, sur ~1,0 Mo mesuré le 17/09/2026).

## Ce que ce lot ne fait pas

La parole du **gouvernement** (`gouvernements/<id>.paroles.json`), ajoutée à
#1073 par l'interface le 22/09/2026, est un lot à part : sa fiche nomme déjà
chaque ministre, et la demande y est une date par tour de parole.
