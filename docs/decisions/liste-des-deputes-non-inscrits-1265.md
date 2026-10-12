# Les députés non inscrits sont publiés comme une liste, pas comme un groupe (#1265)

`2026-10-12`

> **En bref** — `raw_data/non_inscrits.json` porte, par législature depuis la XIVe, les députés qui n'appartiennent à aucun groupe, avec leurs périodes (forme de `membres[].periodes`). Lu dans l'organe `NI` d'AMO30 que le roster écarte. Pas destiné au site : il complète des articles, d'où `raw_data/`. Le transit d'ouverture est écarté et compté ; un passage court reste publié, sans seuil de durée ; ce n'est pas une fiche de groupe.

## Contexte

Le dépôt ne publie que des fiches de groupe. Un député hors de tout groupe à une
date donnée n'avait ni part ni siège dans les figures. Mesuré par la session
communication le 08/10/2026 pour l'article « violences sexuelles et sexistes » :
13 amendements de commission et 51 de séance ne se rattachaient à aucun groupe à
leur date de dépôt, et les hémicycles comptaient 558 députés — les membres des
onze groupes au 05/10 — au lieu de l'Assemblée entière.

La source existait : l'organe `GP` de sigle `NI` d'AMO30
(`an_roster.SIGLE_NON_INSCRIT`). Le roster et la dérivation des lignées
l'écartent volontairement, parce que les non-inscrits ne sont pas un groupe.

## Mesure

Archive AMO30 locale du 17/08/2026, mandats de l'organe `NI` :

| Législature | Mandats de transit d'ouverture | Personnes publiées | Périodes publiées | dont closes en 7 jours au plus | Personnes en cours | Personnes sans fiche |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| XIVe | 0 | 92 | 94 | 59 | 0 | 55 |
| XVe | 577 | 116 | 126 | 60 | 0 | 15 |
| XVIe | 576 | 39 | 39 | 25 | 0 | 2 |
| XVIIe | 577 | 94 | 98 | 81 | 10 | 3 |

« En cours » est vrai à la date de l'archive ; la page de l'Assemblée en listait
11 le 08/10/2026.

## Décision

**1. Un fichier à part, `raw_data/non_inscrits.json`, et non une fiche de
groupe.** Rien de ce qu'une fiche de groupe publie ne s'applique à un ensemble
qui n'en est pas un (cohésion, ratios, empreinte thématique — §2 règle 7 s'y
appliquerait à tort). Un bloc par législature dans un seul fichier de 96 Ko,
plutôt qu'un fichier par législature.

**Il n'est pas destiné au site.** Arbitré par la propriétaire le 12/10/2026 :
puisque ces profils ne s'agrègent pas, la liste ne servira qu'à compléter des
articles. Elle vit donc dans `raw_data/` et non dans `pivot_data/`, la seule
couche que le site lit — le rangement de `gouvernements_reels.json`, dérivé de
la même archive par le même job. `sync-data.mjs` copie une liste fermée de
fichiers et ne le prend pas. Le fichier reste produit par le run : un chiffre
d'article se rattache ainsi au commit de données d'un run, et se revérifie.

**2. Le transit d'ouverture est écarté, par la règle du roster.**
`an_roster.est_mandat_de_transit` : un mandat clos au plus tard le jour de
constitution des groupes est un passage administratif. Ce qui est écarté est
compté dans `transit_d_ouverture`, et l'entête dit qu'avant
`date_constitution_groupes` la liste ne dit pas qui était non inscrit.

**3. Un passage court reste publié.** 81 des 98 périodes de la XVIIe durent sept
jours au plus. Elles sont publiées telles que la source les donne : chacune est
datée, et le lecteur du fichier compte à la date qui l'intéresse.

**4. Les quatre législatures du corpus**, de la XIVe à la XVIIe : la source et la
règle sont les mêmes, et le coût est nul.

**5. `membre_id` vient de la table de correspondance, ou vaut `null`.** Jamais un
slug fabriqué : il désignerait une fiche qui n'existe pas. `acteur_ref` est la
clé, toujours présente.

**6. Rien n'est écrit sur une lecture en échec** (#511) : archive indisponible,
aucun organe `NI`, deux organes `NI` pour une législature, table de
correspondance absente, document non conforme. Le fichier committé reste.

## Ce que ce lot ne fait pas

- **Il ne collecte aucune fiche.** Trois personnes de la XVIIe n'ont pas de
  profil — Véronique Besse et Philippe Bonnecarrère, non inscrits depuis le
  19/07/2024, et Stéphane Chouin, un jour. Leurs votes et leurs amendements ne
  sont dans aucun profil. Les faire entrer dans la collecte est un autre lot :
  le roster n'a aujourd'hui que deux portes, le groupe et le gouvernement.
- **Il n'affiche rien, et n'a pas vocation à le faire.** Le fichier n'est lu
  par aucune page ; les articles le liront quand ils en auront besoin.
- **Le contrôle de perte ne le couvre pas.** Il compare des collections de
  fiches ; ce fichier est réécrit en entier à chaque run depuis la source.

## Alternatives écartées

- **Le ranger dans `pivot_data/`** (première rédaction de ce lot) : il y aurait
  été le seul fichier que le site ne lit pas.
- **Ne rien committer, un script lancé à la demande** : plus rien dans le
  workflow, mais le chiffre d'un article ne se rattacherait plus à un run.

- **Publier le transit d'ouverture, marqué comme tel** : le compte du 10 juillet
  2024 serait exact (577), mais chaque lecteur du fichier devrait savoir
  l'écarter, et le roster des groupes ne le publie pas non plus.
- **Un seuil de durée** : une liste courte, proche de l'idée qu'on se fait d'un
  non-inscrit, mais le seuil serait un jugement de notre part, sans fondement
  dans la source.
- **Une fiche `groupe-AN-NI-17`** : elle aurait reçu des compteurs de groupe, et
  l'audit de filiation (#1168) avait mesuré 34 liens proposés à tort quand `NI`
  est traité comme un groupe.
- **Un job de plus dans le workflow** : un second checkout pour 96 Ko. L'étape
  rejoint `extract-gouvernements`, qui lit la même archive.
