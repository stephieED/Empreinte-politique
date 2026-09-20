<a id="retrait-fetch-activity-synthesis"></a>
# Retrait de `fetch_activity_synthesis` (#356) (2026-08-16)

`2026-08-16`

> **En bref** — `fetch_activity_synthesis` retiré : plus rien n'en dépendait.

**Contexte** : sous-issue 5/6 de #351, une fois `fetch_identity` basculé sur
l'AN pour l'identité (bio) (#355, [[bascule-identite-an-primaire]]).
L'énoncé demandait de réévaluer si `fetch_activity_synthesis` (endpoint
NosDéputés `/synthese/data/json`) apporte encore une donnée non couverte
ailleurs et publiable, et de le retirer purement et simplement si rien n'en
dépend — plutôt que d'investir dans sa mise en cache comme envisagé
initialement (voir la mention `fetch_activity_synthesis` dans la décision
Résilience du 2026-08-16 : ce point d'appel a hérité du `shutdown signal`
runner lors d'une vérification post-Décision 4, sans qu'un retry ciblé ne
soit retenu).

**Constat** : `synthese_activite` (nom, `groupe_sigle`, profession,
`nb_mandats`, `url_an_ou_senat`) était stocké dans le profil brut mais
**jamais lu par `normalize_nosdeputes.py`** — aucun de ces champs n'atteint
`pivot_data/`. Ce n'était donc pas une donnée publiée mise en cache
manquante, mais un appel réseau et un champ de profil brut entièrement
morts : les champs qu'il portait sont soit déjà couverts (`profession` via
`fetch_identity`, mandats/groupe via NosDéputés `identite`), soit hors
périmètre éditorial (taux de présence agrégé, règle 3, §2 d'AGENTS.md), soit
sans consommateur.

**Décision : retrait complet**, pas de mise en cache. Supprimé :
`fetch_activity_synthesis` et son appel dans `build_profile`
(`candidate_profile.py`), le champ `synthese_activite` du profil brut
(structure par défaut dans `build_profile`/`build_minimal_profile`), et sa
fusion additive dans `merge_raw_profile` (`merge_profile.py`). Aucun impact
sur le schéma pivot (`schema_pivot.py`) : ce champ n'y a jamais existé.

