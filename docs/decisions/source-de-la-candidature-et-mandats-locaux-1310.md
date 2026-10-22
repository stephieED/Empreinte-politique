<a id="source-de-la-candidature-et-mandats-locaux-1310"></a>
# L'attestation d'une candidature n'est pas une source de données, et les mandats locaux déclarent la leur (#1310, 2026-10-22)

`2026-10-22`

> **En bref** — 20 des 43 fiches de candidats déclarés publiaient la licence de l'Assemblée nationale sur la foi d'un article de presse ou d'une page Wikipédia, rangés dans `sources[]` sous le type `assemblee_nationale`. Une entrée de ce type pointe désormais vers l'Assemblée ou n'est pas écrite, et la fusion retire celles qui sont publiées. En corrigeant, un second trou : les mandats locaux (#922) n'avaient aucune entrée `sources[]`, donc aucune licence ; ils portent maintenant `rne` et la Licence Ouverte 2.0 de data.gouv.fr.

## Contexte mesuré

Sur `public/main` `85f898a614` (22/10/2026), les entrées `sources[]` de type
`assemblee_nationale` de tous les profils, par hôte de leur URL :

| Population | `www2.assemblee-nationale.fr` | presse | `fr.wikipedia.org` |
| --- | ---: | ---: | ---: |
| `candidat_declare` (43) | 19 | 17 | 3 |
| `roster_groupe` | 1 170 | 0 | 0 |
| `roster_gouvernement` | 202 | 0 | 0 |

Les 20 entrées hors de l'Assemblée sont le champ `source` de
`raw_data/candidats.json`, recopié par `build_minimal_profile` puis typé par
`normalize_profil` (`_SOURCE_TYPE_PROFIL_FR`) quel qu'il soit. 18 fiches de
candidats portent des mandats locaux (`categorie_source == "rne"`) ; aucune
n'avait d'entrée `sources[]` pour eux.

Rejoué le 22/10/2026 sur les 43 fiches (normalisation du profil brut publié,
versement des mandats locaux, fusion avec la fiche publiée) :

| Après le correctif | Fiches |
| --- | ---: |
| entrée `assemblee_nationale` hors de l'Assemblée | **0** (20 avant) |
| aucune donnée collectée : `sources: []`, `licence_donnees: ""` | 14 |
| mandats locaux seuls : la licence du RNE remplace celle de l'Assemblée | 6 |
| fiches qui gagnent la licence du RNE à côté des leurs | 12 |

## Décision

- **`normalize_profil`** n'écrit une entrée `assemblee_nationale` que pour une URL
  servie par l'Assemblée (`licences.est_url_assemblee` : `assemblee-nationale.fr`
  et ses sous-domaines). L'attestation d'une candidature n'entre pas dans
  `sources[]` : elle est déjà citée sur `/sources#candidats` (#1298), et
  Wikipédia ne doit atteindre aucun `sources[]` (AGENTS.md §7).
- **Le retrait est écrit** : `merge_profile.est_source_mal_typee` écarte, des deux
  côtés de la fusion, une entrée `assemblee_nationale` dont l'URL dément le type.
  Sans lui, l'union par type de `_merge_pivot_sources` garderait l'entrée publiée
  indéfiniment.
- **Les mandats locaux déclarent leur source** : `_verser_mandats_locaux` ajoute
  `{type: "rne", url, synchro_le}` quand il verse au moins un mandat — un bloc
  « relu, aucun mandat » publie sa couverture, pas une source. `rne` entre dans
  `KNOWN_SOURCE_TYPES`, et `licences.LICENCE_RNE` dans les licences dues.
- **Un profil minimal n'annonce plus la licence de l'Assemblée** dans sa couche
  brute : la licence y est composée, et sans source elle est vide.

## Alternative écartée

**Un type de source « presse ».** L'article atteste un fait — la candidature —
qui n'est pas une donnée collectée, et il n'a pas de licence ouverte à
revendiquer : un type de plus aurait fait publier une attribution vide de sens, ou
une licence inventée.

**Garder l'Assemblée comme licence par défaut d'une fiche vide.** C'est
exactement le défaut : une licence affichée doit être due par une donnée
publiée.

## Ce qui n'a pas été vérifié

- **Le rendu des 14 fiches sans licence** : `CandidateProfile.jsx` (`cp-pied`)
  affiche `meta.licence_donnees`. Ce qu'il fait d'une chaîne vide est à voir côté
  interface.
- La couche brute des profils minimaux déjà publiés garde son ancienne
  `meta.licence_donnees` tant que la fusion brute préfère une valeur non vide ;
  elle n'est lue par aucune publication, le pivot recompose la sienne.
- Une correction de code n'atteint le corpus qu'au run suivant.
