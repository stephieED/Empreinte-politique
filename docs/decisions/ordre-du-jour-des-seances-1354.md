# L'ordre du jour des séances publiques, un fichier par législature (#1354) (2026-10-26)

`2026-10-26`

> **En bref** — la fiche de législature (#1314) dessine un agenda des sujets discutés en séance, jour par jour, à la couleur de la commission saisie (forme B, arbitrée le 26/10/2026). `src/ordre_du_jour_an.py` publie `pivot_data/ordre_du_jour/<n>.json` pour les XVe-XVIIe, depuis l'archive Agenda que le dépôt téléchargeait déjà : chaque séance (états « Supprimé » et « Annulé » compris) et ses points, avec les dossiers que la source leur donne. Un point sans dossier reçoit celui d'un autre point de la même archive au même intitulé, **dans toute la législature et seulement si cet intitulé ne mène qu'à un dossier** — arbitré le 26/10/2026 (option C) —, publié à part (`dossier_retrouve`), jamais mêlé à ceux de la source. Mesuré sur les séances confirmées : XVIIe 967 points au dossier de la source, 1 032 retrouvés, 38 ambigus, 486 sans dossier.

## Contexte

L'archive Agenda (`vp/reunions/Agenda*.json.zip`) publie, pour chaque séance
publique, son ordre du jour point par point. `articles_votes.py` (#1264) la
téléchargeait pour un seul usage : savoir quels dossiers une séance a discutés.
Rien n'en était publié.

La source ne donne le dossier que sur une partie des points (mesures dans
`docs/sources/an-opendata.md`, « Agenda / meetings ») : la « Suite de la
discussion » presque jamais, et beaucoup de premières « Discussion » non plus.
Sans dossier, un point ne peut pas prendre la couleur de sa commission.

## Décision

1. **Un fichier par législature**, `pivot_data/ordre_du_jour/<n>.json` :
   `{schema_version, legislature, genere_le, licence_donnees, source_url, seances}`.
   Une séance : `{uid, date, debut, fin, etat, session_ref, compte_rendu_ref,
   points}`, dans l'ordre de son début. Un point : `{uid, objet, type, etat,
   procedure, nature, dossiers, dossier_retrouve, dossier_non_resolu}`, dans
   l'ordre de la source. Les champs sont ceux de la source, renommés en
   `snake_case`.
2. **Une séance publique de l'Assemblée** est une réunion `seance_type` dont
   l'uid commence par `RUAN` : les séances du Sénat et du Congrès, les réunions
   de commission sont écartées. **Une séance supprimée ou annulée garde son
   état** au lieu de disparaître (§2 règle 5).
3. **Le dossier d'un point**, trois cas exclusifs :
   - `dossiers` : ceux que la source pose (`dossiersLegislatifsRefs`), verbatim ;
   - `dossier_retrouve` : `{dossier_ref, par: "meme_intitule_dans_la_legislature",
     point_source}`. L'intitulé est réduit au texte qu'il nomme
     (`cle_d_intitule` : la mention de la discussion, les parenthèses et la
     navette sont retirées) ; le dossier est celui des points de la même
     archive qui portent cette clé, s'il n'y en a qu'un. `point_source` est le
     plus proche dans le temps ;
   - `dossier_non_resolu.motif` : `point_hors_texte` (questions, débats,
     session : aucun texte nommé), `intitule_sans_dossier`,
     `intitule_a_plusieurs_dossiers` (qui nomme alors les dossiers).
4. **La portée du regroupement est la législature** (option C, arbitrée le
   26/10/2026, sur un exemple : la PPL « débits de boisson en zone rurale »,
   discutée le 10/03 puis les 31/03 et 01/04/2025, ne porte son dossier que sur
   la première séance).
5. **Aucune durée et aucune présence** ne sont publiées (§2 règle 3) : `debut` et
   `fin` sont les bornes que la source annonce pour la séance.
6. **Dans le job `extract-articles-votes`**, une étape de plus, en `always()`, et
   un artifact à part (`ordre-du-jour`). Il n'y a pas de nouveau job ; le
   workflow change.

## Mesures (26/10/2026, archives du jour, séances confirmées)

| Points | XVe | XVIe | XVIIe |
| --- | ---: | ---: | ---: |
| dossier de la source | 2 265 | 857 | 967 |
| dossier retrouvé par l'intitulé | 973 | 616 | 1 032 |
| intitulé à plusieurs dossiers | 35 | 55 | 38 |
| intitulé sans dossier | 210 | 212 | 486 |
| point hors texte | 616 | 257 | 340 |

Avant l'arbitrage, la portée a été mesurée à trois niveaux (XVe / XVIe / XVIIe) :
la même séance 125 / 43 / 143, le même jour 482 / 266 / 447, la législature
973 / 616 / 1 032. Pour la législature, 92 % des points retrouvés le sont à
moins de 60 jours du point qui donne le dossier ; 16 le sont à plus d'un an
(7 en XVe, 9 en XVIIe). Le cas qu'il faut craindre existe : le PLFSS 2025 a deux
dossiers (le texte tombé avec la censure de décembre 2024, puis celui redéposé),
et la règle le laisse sans dossier.

Fichiers : 3,6 Mo (XVe), 1,6 Mo (XVIe), 2,3 Mo (XVIIe), 6 s pour les trois.

**Le point laissé ouvert par l'issue**, les dossiers absents de
`pivot_data/commissions_dossiers.json` (généré le 19/10/2026) : 190 points de la
XVIIe, sur 59 dossiers, 150 en XVIe, 206 en XVe. En XVIIe, ce sont tous des
propositions de résolution (100, dont les créations de commission d'enquête),
des résolutions de l'article 34-1 de la Constitution (66) et des motions de
censure (24). La table des commissions ne couvre que les dossiers renvoyés à une
commission au fond ; ces points n'ont pas cette couleur, et c'est un fait. Ce
n'est pas une donnée qui manque à l'ordre du jour.

## Alternatives écartées

- **Joindre un point à un dossier de l'archive des dossiers législatifs par son
  titre** : deux sources, aucune clé. Interdit (`regrouper-nest-pas-joindre-639`).
- **Les portées A (la séance) et B (le jour)** : sûres, mais elles laissent sans
  couleur les suites de débat étalées sur plusieurs semaines.
- **Un seul fichier pour les trois législatures** : 7,5 Mo lus par une fiche qui
  n'en montre qu'une.
- **Écarter les séances supprimées** : l'interface doit distinguer un jour sans
  séance d'un jour dont la séance a été retirée.

## Non vérifié

- Le premier run en CI : le temps de l'étape (6 s en local) et l'écriture des
  trois fichiers par l'artifact.
- Ce que le point « en commission » d'une séance (`procedure` « législation en
  commission ») change à la lecture : publié tel quel, sans interprétation.
