# Les mandats antérieurs à la couverture de l'Assemblée entrent par une table relue (#860)

`2026-09-11`

> **En bref** — une fiche de candidat ne savait pas dire qu'une carrière commence avant le **19/06/2002**, premier jour des données de l'Assemblée : le seul critère calculable, « premier mandat lu », s'est trompé sur 3 des 5 cas. **Mesuré** : parmi les 16 candidats déclarés qui ont un acteur AN, **5** ont un mandat national antérieur — Royal, Mélenchon, Retailleau, Cazeneuve, Dupont-Aignan —, pour **13 lignes** dont 11 dans le périmètre (6 mandats de député, 5 fonctions gouvernementales) et 2 mandats de sénateur hors périmètre (#528). Arbitrage de la propriétaire, 11/09/2026 : **une table committée et relue**, `raw_data/mandats_anterieurs.json`, sur le modèle de la correspondance slug ↔ acteur (#525) — une source primaire par ligne, **Sycomore** pour un député, un **décret au Journal officiel** pour une fonction gouvernementale ; chaque fait a été relu sur sa source avant d'être écrit, et la seule fin introuvable (1993) est publiée `null` avec son motif. **Wikidata a servi à découvrir, pas à publier** : les 4 fonctions ministérielles de Royal y manquent, deux dates y diffèrent de Sycomore, et `P4123` y est stocké **sans** le préfixe `PA` — la première mesure est revenue vide pour cette seule raison. Le champ `mandats_anterieurs` est **dérivé** : reposé à chaque écriture du pivot, jamais fusionné, sur les seuls candidats déclarés ; **relu ≠ non relu** — 5 fiches relues, **27 publiées `null` + `non_relu`**, absent n'étant pas « aucun ». Suite complète à **4 533**, 0 échec.

## La mesure

Wikidata `P39` pour les 16 candidats déclarés à acteur AN, fonctions commencées
avant le 19/06/2002, puis **chaque ligne relue sur sa source primaire** :

| Candidat | Relu sur | Lignes portées |
| --- | --- | --- |
| Ségolène Royal | Sycomore 6174 ; décrets du 02/04/1992, 04/06/1997, 27/03/2000, 27/03/2001, 06/05/2002 | 3 députée, 4 ministre |
| Jean-Luc Mélenchon | décrets du 27/03/2000 et 06/05/2002 | 1 ministre délégué — les 2 mandats de sénateur **non portés** (#528) |
| Bruno Retailleau | Sycomore 6689 | 1 député |
| Bernard Cazeneuve | Sycomore 1562 | 1 député |
| Nicolas Dupont-Aignan | Sycomore 2721 | 1 député |

Le corpus ne porte **aucun** mandat de député antérieur au 19/06/2002, vérifié sur
les cinq profils : ceux de la XIe législature (1997-2002) y manquent aussi.

**La fin de 1993.** Aucun décret de cessation des fonctions du gouvernement
Bérégovoy n'a été trouvé sur Légifrance ; le décret de composition du 02/04/1992
n'y rend que son titre, et la fonction de Royal est attestée par sa signature
« Le ministre de l'environnement » du décret n° 92-396. La ligne porte donc
`fin: null` et `fin_non_resolue.motif = "source_primaire_non_trouvee"`.

**Comment Légifrance a été lu.** Le site refuse les requêtes directes (contrôle
anti-robot) ; les décrets ont été lus par une récupération web qui résume la page.
C'est une lecture indirecte, déclarée comme telle.

## La décision

- `raw_data/mandats_anterieurs.json` : `slug → lignes`, relue, datée ; chaque ligne
  `institution`, `libelle`, `debut`, `fin`, `source_url` (primaire), éventuellement
  `legislature`, `source_fin_url`, `fin_non_resolue` ;
- `mandats_anterieurs.charger_table` refuse une ligne sans source, une fin nulle
  sans motif, une ligne qui se termine **dans** la couverture — un trou après la
  borne est un autre défaut (#859) —, une institution hors du frozenset ;
- `appliquer_mandats_anterieurs` repose le champ à l'écriture de chaque pivot,
  **avant** la comparaison de #343, pour qu'une fiche inchangée garde ses
  horodatages ; `validate_profil` le tient s'il est présent.

## La table ne se met pas à jour seule — le rappel est posé là où l'on passe

Un candidat ajouté par `rafraichir-candidats` paraît `non_relu` sur sa fiche : ce
n'est pas silencieux, mais rien n'invitait à le relire. Question de la
propriétaire, 11/09/2026. Le rappel est donc écrit **aux deux endroits par où passe
forcément qui touche à la liste** :

- la **note de l'entrée neuve** dans `raw_data/candidats.json`, que
  `fetch_candidats_declares.nouvelle_entree` compose déjà (« À relire — slug,
  famille politique… ») et qui gagne `RAPPEL_MANDATS_ANTERIEURS`, avec ou sans slug ;
- la **règle de domaine** `docs/regles/roster-et-sources.md`, chargée quand on
  touche aux candidats.

Les deux entrées déjà présentes sans relecture (Mlekuz, Mikolajczak) ne sont pas
réécrites : une entrée existante ne se modifie jamais (#753) ; #847 les suit.

**Écarté** : un signal non bloquant du portail listant les candidats non relus à
chaque run — 27 lignes identiques d'un run à l'autre, un avertissement qu'on
apprend à ne plus lire.

## Écarté

| Option | Pourquoi |
| --- | --- |
| Collecte automatique (Sycomore, Légifrance, Wikidata) | trois sources hors §7 à maintenir, pour 11 lignes et 5 personnes |
| Wikidata seul | source secondaire (§2 règle 2), incomplète, dates décalées |

## Limites déclarées

- **27 candidats déclarés ne sont pas relus**, dont 11 à acteur AN pour lesquels
  Wikidata ne montre aucun mandat national antérieur, et 16 sans acteur AN. Leur
  fiche le dit ; les relire est la suite.
- **Le Sénat** : l'ajouter à `KNOWN_INSTITUTIONS_ANTERIEURES` est la reprise de #528.
- **Les mentions légales** : Sycomore et le Journal officiel sont désormais
  **cités** par des fiches. `AGENTS.md` §7, `sources.config.js` et
  `LegalNoticePage.jsx` doivent dire la même chose ; les deux derniers sont côté
  interface.
