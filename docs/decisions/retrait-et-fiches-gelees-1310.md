# Un retrait écrit dans la fusion n'atteint pas une fiche gelée (#1310) (2026-10-23)

`2026-10-23`

> **En bref** — le correctif de #1310 (retrait des sources mal typées, source des mandats locaux) s'applique à la fusion et au versement des mandats locaux. Une fiche gelée — candidature retirée, hors de tout shard depuis #760, qu'aucun roster ne reprend — ne passe par aucun des deux : après le run du 22/10/2026, `fabien-verdier` et `lydie-massard` gardaient le défaut. Elles ont été corrigées par un commit de données sur le public (`6c6a83a3ad`, 23/10/2026), avec les fonctions mêmes du pipeline. Arbitré le 23/10/2026 (« A »). Un retrait futur butera sur le même cas : il se vérifie sur les fiches gelées, et se corrige une fois dans leurs fichiers.

## Contexte

Mesuré le 22-23/10/2026 sur `public/main` après le run du 22/10 :

| Candidats `statut: decline` | Fiches |
| --- | ---: |
| recollectés quand même, comme anciens députés, par un roster de l'Assemblée | 6 (Guedj, Royal, Wauquiez, Brun, Faure, Maurel) |
| gelés, sans aucun run depuis | 3 : `jordan-bardella` (06/09), `lydie-massard` (25/09), `fabien-verdier` (12/10) |
| … qui portaient un défaut de #1310 | 2 : Verdier (le lien Wikipédia typé `assemblee_nationale`, donc la licence de l'Assemblée, et 3 mandats locaux sans source `rne`) ; Massard (1 mandat local sans source `rne`) |

Ces fiches sont masquées sur le site (#761) : le défaut ne vivait que dans les
fichiers du dépôt public.

## Décision

**Corriger une fois les fichiers des fiches gelées**, aux couches où l'erreur est
publiée, avec les fonctions du pipeline (`merge_profile.est_source_mal_typee`,
`generate_all_profiles.source_rne`, `licences.appliquer_licence_donnees`) et non
à la main. Seuls `sources` et `meta.licence_donnees` du pivot ont changé ; la
couche brute n'avait rien à retirer. Le commit a été écrit sur le public, puis
rapatrié (`9c6a7427a1`). La même correction avait été ouverte en PR sur le privé
(#1339), à la demande de la propriétaire, puis fusionnée.

**La règle pour un retrait futur** (`docs/regles/fusion-et-index.md`) : un
retrait nommé dans la fusion se vérifie aussi sur les fiches que le périmètre
gèle (`perimetre_candidats.STATUTS_GELES`) et qu'aucun roster ne reprend.

## Alternatives écartées

- **Faire passer les fiches gelées par les corrections à chaque run**, sans rien
  collecter : un lot de code pour trois fiches, dont une seule défaillante par
  cas mesuré. À reconsidérer si un retrait touche de nouveau des fiches gelées.
- **Ne rien faire, la fiche étant masquée** : une licence fausse restait dans un
  fichier publié et réutilisable.

## Non vérifié

- Qu'aucun retrait antérieur à #1310 n'ait laissé de trace sur ces trois fiches :
  seuls les deux défauts de #1310 ont été mesurés.
