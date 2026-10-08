<a id="recherche-entre-fiches-abandonnee-979"></a>

# La recherche reste sur la fiche : la recherche entre fiches est abandonnée (#979) (2026-10-07)

`2026-10-07`

> **En bref** — #979 avait été découpée le 17/09/2026 en deux temps. Le premier — chercher un mot sur la fiche affichée — est livré sur les trois types de fiche. Le second — une recherche « quelle fiche porte des données sur ce mot ? », avec un index reliant un mot aux fiches — **est abandonné**, sur arbitrage de la propriétaire confirmé le 07/10/2026. **À ne pas reproposer.** Ce fichier consigne un abandon qui n'était écrit nulle part.

## Le contexte

| Temps | Ce que c'est | État |
| --- | --- | --- |
| 1 | filtrer la fiche affichée par un mot | livré : fiche candidat (#993, 17/09), fiche de groupe sur toute la lignée (#995, 17/09), fiche de gouvernement (#1040, 20/09) |
| 2 | chercher un mot sur tout le site, par un index mot → fiches | non commencé |

Les arbitrages du temps 1 sont dans
`docs/decisions/filtre-par-intitule-fiche-candidat-979.md` et
`docs/decisions/recherche-fiche-groupe-979.md`.

## La décision

Le 07/10/2026, à la proposition d'ouvrir le temps 2, la propriétaire : « on
n'avait pas arbitré qu'on ne ferait pas le temps 2 ? », puis « oui, ferme ».
Aucune trace écrite de cet arbitrage n'existait — ni dans l'issue, ni dans
`docs/decisions/`, ni au `ROADMAP.md`, ni dans les notes des sessions.

- Le temps 2 n'est pas fait, et #979 est fermée.
- L'entrée « Une recherche par mot-clé à l'intérieur d'une fiche » sort du
  `ROADMAP.md` : elle est livrée.

## Ce qui n'a pas été vérifié

La raison de l'abandon n'a pas été donnée. Le `ROADMAP.md` notait, avant la
livraison, qu'un moteur de recherche entre fiches « poserait un classement »
(§2 règle 1) : c'est une raison possible, pas la sienne.

Deux constats du 17/09, non revérifiés, sont dans le commentaire de fermeture de
#979.
