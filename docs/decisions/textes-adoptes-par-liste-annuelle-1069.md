<a id="textes-adoptes-par-liste-annuelle-1069"></a>
# Les textes adoptés se lisent par liste annuelle, plus un par un (#1069) (2026-09-21)

`2026-09-21`

> **En bref** — Le portail du Parlement publie la liste des textes adoptés d'une année, `is_about` compris : 38 pages remplacent des milliers de requêtes unitaires. Passe réelle, cache vide, budget du job de réchauffage : **2 396** dossiers avec domaines, contre **424** publiés. La file unitaire passe désormais des plus récents aux plus anciens.

## Le constat

La passe des domaines EuroVoc demandait les documents **un par un** — 0,6 s de
pause imposée, ~1,85 s par requête en CI, ~650 réponses par run — et sa file
était triée par référence **croissante** : après les dossiers amendés, elle
commençait par `1992/…`. Or le portail ne classe presque pas ces dossiers-là.

| Run du 21/09/2026 | Requêtes | Nouveaux « avec domaines » | Nouveaux « non classés » |
| --- | ---: | ---: | ---: |
| `f7518f71b` (19h) | 613 | 7 | 297 |
| `35648745220` (23h16) | 637 | 9 | 310 |

735 des 794 dossiers `documents_non_classes` du premier point étaient antérieurs
à 2014. Au rythme observé, la file se vidait en une douzaine de runs pour
n'apporter presque aucun domaine.

## Ce que le portail publie aussi

`/api/v2/adopted-texts?year=…` rend, par pages, tous les textes adoptés d'une
année avec leurs concepts. Mesuré depuis un poste (détail et limites :
`docs/sources/parltrack-et-europarl.md`) : 2014 → 2026, 5 196 textes dont 3 989
classés, 35 pages en 9 minutes ; `is_about` identique à la requête unitaire sur
10 textes sur 10.

## Décision

1. **`ResolveurDocuments.precharger_textes_adoptes(annees)`** écrit chaque
   texte listé au cache comme une réponse unitaire — `concepts: []` quand il
   n'est pas classé, ce qui est une réponse et non une ignorance.
2. **Seules les années d'un texte adopté encore inconnu du cache** sont
   demandées : une fois la liste passée, un run ne relit que l'année en cours.
3. **La liste partage le budget en temps, pas le plafond** : le plafond borne
   les requêtes unitaires, et une page en vaut deux cents.
4. **Un texte absent de la liste n'est rien écrit.** L'absence vaut
   inexistence pour la 7e législature (404 à l'unité aussi), mais la liste de
   l'année en cours peut retarder sur la publication : en déduire une
   inexistence publierait ce que la source n'a pas dit (§2 règle 5). La passe
   unitaire garde ces documents, et les rapports et propositions de résolution.
5. **La file unitaire va des plus récents aux plus anciens**, après les
   dossiers amendés.
6. `merge-and-pivot` ne change pas : budget et plafond à zéro, il ne liste
   rien et lit le cache chaud du job `rechauffer-le-portail-europeen`.

## Mesuré avant de publier

Passe réelle depuis un poste, le 21/09/2026, cache **vide**, sans reprise de
l'index publié, `--budget-secondes 1080` comme le job de réchauffage, sur les
4 642 dossiers de l'index :

| | Publié (run `35648745220`) | Passe #1069 |
| --- | ---: | ---: |
| avec domaines | 424 | **2 396** |
| `documents_non_classes` | 1 104 | 241 |
| `question_non_posee` | 3 111 | 2 002 |
| requêtes unitaires | 637 | 348, plus 38 pages de liste |
| durée | 1 113 s | 1 133 s (19 min 26 au total, dump compris) |

Les 2 002 restants sont surtout des textes antérieurs à 2014, que la liste ne
porte pas : la file unitaire les atteint en dernier, et ils finiront
majoritairement `documents_non_classes`, comme les 735 déjà mesurés.

**Ce débit est celui d'un poste.** Un débit local ne vaut pas en CI : le
premier run dira combien de pages tiennent dans le budget, et le budget, qui
est en temps, borne la passe quoi qu'il arrive.

## Alternatives rejetées

- **Ne plus interroger les dossiers d'avant 2014** : une borne écrite par nous,
  là où l'ordre des plus récents d'abord obtient le même effet sans rien
  exclure.
- **Abandonner EuroVoc sur les dossiers** au profit des seules familles OEIL :
  la cohérence avec l'axe des textes portés, arbitrée le 17/09/2026, était
  perdue.
- **Allonger le budget** : la file se vidait plus vite, sur des dossiers que le
  portail ne classe pas.
