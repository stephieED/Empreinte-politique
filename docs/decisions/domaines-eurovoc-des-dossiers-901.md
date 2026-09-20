<a id="domaines-eurovoc-des-dossiers-901"></a>
# Un dossier européen reçoit ses domaines EuroVoc de son texte adopté (#901) (2026-09-17)

`2026-09-17`

> **En bref** — Les amendements et les votes européens se rattachent à un
> **dossier**, et EuroVoc n'est attaché qu'à des **documents**. Pour que leur axe
> de couleur soit celui du sankey des textes, chaque dossier de
> `dossiers_europeens.json` (v4) reçoit les domaines de son document de séance,
> **texte adopté d'abord**. Essai sur les 367 dossiers amendés : 292 couverts,
> 75 % des amendements. Pour les ~4 700 dossiers votés, un plafond de 1 500
> requêtes nouvelles par run, et un cache cumulé : arbitré le 17/09/2026 (option A).

## Le besoin

Arbitrage de la propriétaire, 17/09/2026 : « les catégories doivent être en
cohérence entre le sankey des textes et les amendements ». Le sankey range les
textes portés par domaine EuroVoc. Les amendements et les votes n'avaient que les
familles OEIL.

## Ce que la source publie, et ce qu'elle ne publie pas

- **Ni le dump ParlTrack** (0 des 23 885 dossiers ne mentionne EuroVoc), **ni la
  fiche « procédure » du portail** (sondée : aucun champ `is_about`) ne classent
  un dossier.
- **Le portail classe des documents**, et pas tous. Essai du 17/09/2026 sur les
  367 dossiers amendés par les candidats déclarés, 438 requêtes, 0 refus :

| Document qui porte les concepts | Dossiers |
| --- | ---: |
| Texte adopté (`TA-…`) | 281 |
| Rapport de commission (`A-…`) | 11 |
| Aucun document classé (surtout avant 2016) | 53 |
| Absent du dump (trop récent) | 12 |
| Texte adopté inexistant ou non classé | 7 |
| Aucun document de séance | 3 |

**5 507 des 7 303 amendements** tombent dans un dossier couvert. Un dossier
touche **5,2 domaines** en moyenne (jusqu'à 13).

## Décision

1. **`documents_de_seance`** lit les références de séance dans `docs[]` et
   `events[]` du dump (`T8-0286/2018` → `TA-8-2018-0286`, `RC-B9-…` → `RC-9-…`) et
   les ordonne : texte adopté, puis proposition de résolution, puis rapport. Deux
   documents essayés au plus par dossier.
2. **`domaines = [{code, libelle, concepts}]`**, triés par nombre de concepts,
   avec `domaines_document`, le document qui les porte. Le poids est un fait de la
   source. **Aucun domaine n'est « le » domaine du dossier** : choisir une couleur
   est une lecture, qui appartient à l'interface, sur maquette.
3. **Plafond de 1 500 requêtes nouvelles par run**, les dossiers **amendés
   d'abord**. Le cache `.cache/europarl` répond sans compter et se cumule d'un run
   à l'autre : la couverture des votes monte run après run.
4. **Cinq motifs d'absence**, qui ne se confondent pas : `aucun_document_de_seance`,
   `documents_non_classes`, `question_non_posee`, `eurovoc_injoignable`,
   `domaine_eurovoc_introuvable`.
5. **Licence** : l'entête nomme désormais ParlTrack, le portail du Parlement et
   EuroVoc.

## Alternatives rejetées

- **Tout interroger d'un coup** (~5 600 requêtes) : un premier run rallongé
  d'environ 1 h 30, exposé à la limite de débit du portail.
- **Les dossiers amendés seulement** : les votes restaient sans EuroVoc.
- **Le rapport de commission d'abord** : 11 dossiers classés sur 367.
- **Réunir les concepts de tous les documents du dossier** : davantage de
  requêtes, et un mélange de documents qui ne disent pas la même chose (un avis,
  une résolution).

## Vérification

- Tests sur le **vrai** `ResolveurDocuments`, avec la réponse réelle du portail
  pour `TA-8-2018-0286`, le dossier `2010/0310M(NLE)` tel que le dump le décrit, et
  les domaines que SPARQL rend pour ses 8 concepts.
- Sur les vraies données, cache de l'essai hors ligne : **292** dossiers amendés
  avec domaines, comme l'essai. Index de 3,8 Mo.
