# Sur la fiche candidat, les mandats antérieurs sont une mention, et rien d'autre (#860)

`2026-09-12`

> **En bref** — la table relue de #860 était publiée sur les fiches depuis la reprise du 12/09/2026, et **aucune vue ne la lisait** : `sources.config.js` la déclarait comme source, `couverture-corpus.mjs` nommait les cinq fiches concernées sur l'accueil, et la fiche candidat elle-même l'ignorait. **Trois formes ont été maquettées sur les lignes réelles** de Ségolène Royal (7 lignes) et de Jean-Luc Mélenchon (1) — la frise du parcours étendue jusqu'au premier mandat, un liseré d'amont hors échelle à gauche de la frise, une liste datée sous la figure. **Arbitrage de la propriétaire, 12/09/2026 : les trois sont écartées**, et le fait entre par **une mention dans « ce qu'on n'a pas pu lire »**. La raison décide toute seule : un mandat antérieur est un **fait cité**, relu à la main sur Sycomore ou sur un décret au Journal officiel, et **aucune activité n'est collectée derrière lui** — ni vote, ni amendement, ni intervention. Le poser sur la frise ferait lire « couvert depuis 1988 » là où rien ne l'est (§2 règle 2). **Mesuré sur la forme A**, la plus tentante : la frise de Royal passait de 15 à **29 ans**, chaque mandat couvert perdant **48 %** de sa largeur pour afficher des segments dont on ne sait rien. Une fiche **non relue** ne produit aucune ligne : dire que la relecture n'a pas eu lieu parlerait de notre travail, pas de la personne affichée. Suite complète à **4 574**, 0 échec.

## Ce qui manquait, et où

La reprise `scripts/poser_mandats_anterieurs_860.py` avait posé le champ sur les
**32** profils de candidats déclarés — 5 relus, 27 `non_relu`. Mesuré le
12/09/2026, `mandats_anterieurs` n'était lu que par deux consommateurs, tous deux
hors de la fiche :

| Consommateur | Ce qu'il en fait |
| --- | --- |
| `src/data/sources.config.js` | déclare Sycomore et le Journal officiel comme sources citées |
| `web/UI_finale/scripts/couverture-corpus.mjs` | nomme, sur l'accueil, les fiches qui portent un mandat antérieur |

La fiche de Ségolène Royal affichait donc une frise commençant en 2002, quand la
table sait qu'elle est députée des Deux-Sèvres depuis le 13/06/1988.

## Les trois formes écartées, et ce qu'elles coûtaient

Maquettées sur les lignes réelles, jamais sur un exemple inventé.

| Forme | Ce qu'elle donnait | Ce qui l'a écartée |
| --- | --- | --- |
| **A** — la frise remonte jusqu'au premier mandat, zone tramée avant la borne | la carrière entière à l'échelle, d'un seul geste | 15 ans de frise deviennent 29 : **chaque mandat couvert perd 48 % de sa largeur** pour loger des segments sans activité derrière. Et une trame reste une nuance : rien n'oblige à la remarquer |
| **B** — un liseré d'amont hors échelle, à gauche, qui compte et déplie | le fait nommé là où le lecteur se demande « et avant ? » | ajoute une figure à une fiche qui en a déjà trop, pour un fait qui tient en une phrase |
| **C** — une liste datée sous la figure | aucune ambiguïté possible | duplique la section qui existe déjà pour ça |

**C et la mention retenue disent la même chose** ; la différence est l'endroit.
« Ce qu'on n'a pas pu lire » est la section qui parle des trous, et un mandat que
le corpus ne porte pas *est* un trou — pas une donnée de plus.

## La forme retenue

Une limite de parcours, au même rang que les trois qui existaient déjà — la
qualification de groupe non déclarée, l'entrée au gouvernement, les
enregistrements repliés. Deux cas rendus, vérifiés sur le serveur de
développement le 12/09/2026 :

```
[Mandats antérieurs]  7 mandats exercés avant le 19 juin 2002 — 3 à l'Assemblée,
                      4 au gouvernement — sont cités depuis leur source primaire.
                      Aucune activité n'y est collectée.

[Mandats antérieurs]  1 mandat exercé avant le 19 juin 2002 est cité depuis sa
                      source primaire. Aucune activité n'y est collectée.
```

Le détail par institution n'apparaît **que** s'il y en a deux : « 1 mandat — 1 au
gouvernement — » ne dit rien de plus que « 1 mandat ».

La seconde phrase n'est pas un ornement. Sans elle, la ligne se lit comme une
couverture de plus ; `tests/test_mention_mandats_anterieurs_860.py` la tient,
avec la traçabilité que §2 règle 2 exige.

## Ce que le test protège, et qu'aucun autre endroit n'écrit

`test_le_champ_n_est_lu_nulle_part_ailleurs_dans_la_fiche` parcourt `src/` et
refuse toute lecture de `mandats_anterieurs` hors de la limite et de la
déclaration de sources. C'est le seul endroit du dépôt où l'arbitrage est écrit
en code exécutable : une session suivante qui rebranche le champ sur la frise —
la forme A est la plus tentante, c'est la plus visuelle — fera rougir la suite.

## Ce que cette décision ne traite pas

- **Les 27 fiches non relues** ne disent rien. L'absence de relecture est un état
  de notre travail, pas un fait sur la personne ; #860 reste ouverte pour elles.
- **Le Sénat.** Mélenchon a été sénateur de 1986 à 2000 ; ces deux mandats ne
  sont pas dans la table, le Sénat étant hors périmètre (#528). Sa fiche mentionne
  donc sa seule fonction gouvernementale antérieure, et la frise commence
  toujours après ses quatorze ans au Sénat. Le dire demanderait une autre ligne,
  qui parlerait d'une source non collectée et non d'un mandat cité — c'est le
  sujet de `/couverture`, pas de la fiche.
- **La lisibilité au téléphone** de cette section, comme du reste de la fiche :
  le lot mobile (#867) est en pause.
