<a id="web-v3-ui"></a>
# Interfacer web/UI_finale (CONTRECHAMP) aux données réelles (2026-08-08)

`2026-08-08`

> **En bref** — `web/UI_finale` câblé aux données réelles, à la place des mocks.

**Contexte** : `web/UI_finale` (React/Vite) était câblé sur des données mock
(`candidates.json`/`groups.json`/`mockGenerator.js`) bien plus riches en volume
que les données réelles disponibles : `pivot_data/` ne couvrait alors que 8
candidats (présidentiables 2027 aussi élus, ceux ayant un `slug` dans
`raw_data/candidats.json`) et 7 groupes parlementaires réels (5 AN + 2 Sénat).

**Mise à jour (#187, roster-driven)** : ce chiffre de 8 candidats était une
limite de l'extraction éditoriale-uniquement, résolue par l'extraction
roster-driven (`generate_roster_candidats.py`, #188/#190/#191, voir
[[provenance-pivot]]) qui couvre tou·te·s les membres réels des groupes
configurés, pas seulement les candidats déclarés. Le nombre de 7 groupes reste
en revanche une limite assumée du périmètre : `pivot_data/groupes/` ne couvre
que les groupes listés dans `raw_data/groupes_reels.json`, pas l'ensemble des
groupes parlementaires existants (voir "Coverage limits" dans `README.md`).
La couverture individuelle réelle au sein de ces 7 groupes dépend d'un run à
pleine échelle qui n'avait pas encore eu lieu en CI au moment de cette mise à
jour — chiffres et suivi dans [[seuil-couverture-groupe]].

**Décision** : remplacer intégralement le mock. `web/UI_finale/scripts/sync-data.mjs`
copie `pivot_data/profiles/`, `pivot_data/groupes/` et `raw_data/candidats.json`
vers `public/data/` (généré, gitignoré) et produit `public/data/manifest.json`
(roster candidats/groupes + rattachement candidat→groupe réel via
`membres[].membre_id`), car Vite ne sert pas de fichiers hors du dossier
projet. `src/data/pivotAdapter.js` porte vers React la logique déjà validée
dans `web/old/v3/js` (ancienneté de mandat, dédoublonnage des responsabilités,
classification majorité/opposition/gouvernement par `position_dans_hemicycle`
+ `source_url`, classification thématique par mots-clés) plutôt que de la
dupliquer en Python : cette logique est un pur calcul d'affichage, sans
publication de nouvelle donnée, donc pas de raison de la sortir du pipeline
web. *Alternative rejetée* : script Python générant des JSON pré-calculés —
aurait dupliqué une logique déjà écrite et éprouvée en JS pour v3.

**Périmètre restreint assumé** : `web/UI_finale` affiche désormais uniquement
Candidats + Groupes parlementaires réels (alignement sur l'ancien `web/old/v3`,
pas d'onglet Partis). Plusieurs groupes réels ont 0 ou 1 profil individuel
disponible localement (`profils_disponibles` très inférieur à `roster_total`)
: les composants affichent un état "aucune donnée" explicite plutôt qu'un
graphique à 0 silencieux, conformément à la règle 5 (une donnée manquante
n'est jamais un 0 par défaut).

**Mise à jour (#213, onglet Gouvernement)** : `web/UI_finale` ajoute un troisième
onglet, Gouvernement, sur le modèle exact de Groupes (`GovernmentsBar`/
`GovernmentProfile`/`GovernmentProfilePage`, `buildGovernmentView` dans
`pivotAdapter.js`) — `sync-data.mjs` copie désormais aussi `pivot_data/gouvernements/`
vers `public/data/gouvernements/`. Point d'attention spécifique retenu de
`schema_gouvernement.py` (règle AGENTS.md §2.1) : `comptages.par_statut` est rendu
comme une liste de badges texte (nombres bruts, statuts à 0 omis), jamais comme une
jauge, un donut ou un pourcentage — contrairement au donut de couverture de
`GroupProfile` (qui mesure la complétude des données collectées, pas un score). Même
pattern "aucune donnée" que les groupes à faible couverture pour `textes[]` vide
(gouvernements récents) et `membres[].portefeuille` manquant.

