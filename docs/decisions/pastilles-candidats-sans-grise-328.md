<a id="pastilles-candidats-sans-grise-328"></a>

# Les pastilles des candidats sans mandat ne sont plus grisées (#328) (2026-10-07)

`2026-10-07`

> **En bref** — `docs/decisions/barre-candidats-ordre-et-mandat-328.md` grisait la pastille d'un candidat sans mandat à l'Assemblée ni fonction gouvernementale, avec une infobulle qui l'expliquait. La propriétaire a demandé le 07/10/2026 de retirer ce grisé, sur la barre de sélection comme sur la liste de l'accueil. **Toutes les pastilles ont la même forme, et l'infobulle part avec le grisé.** Ce fichier **corrige** la décision d'origine sur ce seul point : l'ordre alphabétique fait à la source ne change pas.

## Le contexte

La décision du 09/09/2026 posait deux choses : l'ordre alphabétique, et le
grisé. Le grisé disait un fait sur ce que la fiche montre — ni vote, ni
intervention, ni amendement — et son infobulle l'écrivait. Mesure de la décision
d'origine, non refaite : 14 des 30 candidats du manifeste étaient grisés.

## La décision

- Demande de la propriétaire, le 07/10/2026 : « peux-tu enlever le grisé sur les
  pastilles des candidats sur la page d'accueil et sur le menu de sélection ? »
- `.cb-chip--sans-mandat` et ses trois règles de style sont retirées ;
  `CandidatesBar.jsx` et `CommencerAExplorer.jsx` ne distinguent plus les fiches
  sans mandat. PR #1241.
- **L'infobulle est retirée avec le grisé** (choix de l'agent, signalé à la
  propriétaire) : elle n'existait que pour l'expliquer, et serait apparue au
  survol de pastilles que rien ne distingue.
- Le manifeste des candidats garde `aSiegeOuGouverne`, que plus rien n'affiche.
- Ce que la fiche ne porte pas se lit sur la fiche, dans « Ce qu'on n'a pas pu
  lire ».

## Trouvé en route

Une ligne `.cb-chip.active` sans accolades, restée devant `.cb-skeleton`,
faisait de la règle des pastilles de chargement un sélecteur descendant qui ne
s'appliquait à rien. Retirée dans la même PR.

## Ce qui n'a pas été vérifié

Le rendu n'a pas été capturé à l'écran. La raison de la demande n'a pas été
donnée.
