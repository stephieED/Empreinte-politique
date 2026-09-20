<a id="audit-rapport-perimetre-candidats"></a>
# Rapport d'audit pivot : détail réservé aux candidats déclarés, indicateurs de distribution retirés (2026-08-18)

`2026-08-18`

> **En bref** — le détail du rapport d'audit est réservé aux candidats déclarés ; indicateurs de distribution retirés.

**Contexte** : le rapport Markdown de `audit_pivot_dataset.py` avait grossi
au rythme du jeu de données. Sur `pivot_data/profiles` (129 profils au
18/08/2026), les deux tableaux croisés par candidat (`#174` pour les
volumes, `#317` pour les plages temporelles) listaient **une ligne par
profil**, soit 258 lignes de détail dont 242 pour des profils de roster
(`meta.provenance == "roster_groupe"`, 121 profils) qui ne sont pas des
candidats : ils sont collectés pour la cohésion de groupe, jamais pour un
affichage individuel. Le rapport devenait illisible pour son unique usage —
repérer d'un coup d'œil un profil de candidat mal enrichi.

**Décision** :
- Les deux tableaux croisés ne détaillent plus que les **candidats déclarés**
  (`meta.provenance` absente ou `candidat_declare`, cf.
  [[provenance-pivot]] — helper `_est_candidat`). Les profils de roster sont
  restitués **agrégés par `groupe`** (min/max/médiane/moyenne pour les
  volumes, plage englobante pour les dates), plus une ligne « Ensemble » ;
  aucun `id` ni `nom` de membre non candidat n'apparaît dans l'agrégat, ce
  qu'un test verrouille. Un `groupe` absent est regroupé sous `"null"`,
  comme ailleurs dans le rapport.
- Deux indicateurs de volumétrie sont supprimés du rapport JSON **et**
  Markdown : « Distribution des listes métier (par profil) »
  (`compute_distribution_listes`) et « Sources déclarées »
  (`compute_nombre_sources` : moyenne de sources par profil, % de profils à
  une seule source). Sans distinction candidat/roster, leurs statistiques
  mélangeaient deux populations aux volumétries incomparables ; la
  ventilation par groupe des non-candidats couvre désormais le même besoin
  là où il a un sens. Leur logique min/max/médiane/moyenne survit dans le
  helper `_stats_volumes`, réutilisé par l'agrégat par groupe.

*Alternative rejetée* : filtrer les profils de roster hors du rapport
entièrement (ne rien afficher pour eux) — rejeté car un roster mal collecté
(votes à 0 sur tout un groupe) resterait invisible dans l'audit, alors que
c'est précisément un défaut de pipeline que ce rapport doit faire remonter.
L'agrégat par groupe garde ce signal sans le détail individuel.

*Alternative rejetée* : garder les deux indicateurs supprimés en les
ventilant par provenance — rejeté comme redondant avec l'agrégat par groupe
introduit ici, pour un rapport qu'on cherchait justement à alléger.

