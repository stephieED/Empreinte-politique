<a id="mandats-agreges-famille-1"></a>
# `mandats_agreges` : agrégation catégorielle sur `mandats[]`, famille 1 (#361, sous-issue de #349) (2026-08-16)

`2026-08-16`

> **En bref** — `mandats_agreges` : agrégation catégorielle sur `mandats[]`, première famille.

**Contexte** : #349 (agrégats de groupe) prévoyait une famille d'agrégats
génériques sur `mandats[]` (commissions, groupes d'amitié, mandats
extra-parlementaires…). Design proposé et validé sur #349 avant
implémentation (voir historique de commentaires) : bloc dédié
`mandats_agreges` plutôt qu'une structure générique `attributs_agreges:
[{champ, type_agregation, résultat}]` — cohérent avec le style déjà en
place (`cohesion_votes`, `amendements_agreges` sont déjà des blocs nommés,
pas une structure générique unique) et plus simple à consommer côté UI. Le
caractère « générique » demandé porte sur le *mécanisme de calcul* (une
seule fonction `group_profile._aggregate_mandats` paramétrée par
`MANDATS_AGREGES_CATEGORIES`), pas sur la forme de sortie.

**Périmètre v1** : `MANDATS_AGREGES_CATEGORIES = ("commission",
"groupe_amitie", "extra_parlementaire")`. Exclus explicitement (pas
oubliés) : `mandat_electif` (définit déjà l'appartenance au groupe —
l'agréger serait circulaire), `groupe_politique` (redondant avec
`groupe_id`/`periode` dans un profil déjà scopé à un seul groupe),
`fonction_gouvernementale` (recoupe
`mandats[].suspendu_pour_fonction_gouvernementale`, AGENTS.md §5 — mérite
sa propre décision), `autre` (filet de secours quasi jamais peuplé,
`candidate_profile.py`).

**Éligibilité temporelle** : réutilise `_member_eligibility_intervals`
(intervalles de mandat électif du membre, déjà utilisés pour
`cohesion_votes`) + nouvelle `_intervals_overlap` : un mandat catégoriel
compte pour le groupe si sa période `[debut, fin]` chevauche au moins un
intervalle de mandat électif (bornes `None` non bornées). Inclusion
binaire, pas de pondération à la durée de chevauchement — cohérent avec les
comptages simples déjà utilisés ailleurs dans ce module. Membre sans mandat
électif renseigné → éligible par défaut (même approche conservatrice que
`_is_eligible_at`).

**Doublon `(categorie, label)` par membre** (ex. réélu·e à la même
commission sur deux périodes) : une seule entrée retenue par
`_select_mandat_entree_unique`, priorité à `actif=true`, sinon la plus
récente par date de fin — même esprit que le tie-break déjà documenté pour
`position_majoritaire` en cas d'égalité (`_compute_cohesion_votes`).

**`poids_relatif`** : `nb_membres / len(profils)`, où `profils` est la
couverture *disponible* (même dénominateur que `tags_thematiques_agreges`),
jamais `meta.couverture_roster.roster_total` — point soulevé en revue de
conception pour rester cohérent avec la règle éditoriale 7 (`AGENTS.md`
§2). `nb_membres_actifs` requiert à la fois le mandat actif *et*
l'appartenance au groupe active aujourd'hui (`membres[].actif`, dérivé de
`_derive_membre_entry`), pas seulement l'un des deux.

**Impact `mandats[]` plus riche à venir** (#351/#352/#353, nouvelles
catégories côté source AN officielle — missions d'information, commissions
d'enquête, délégations, groupes d'études, CMP…) : non bloquant pour cette
implémentation, le schéma `mandats_agreges` ne change pas de forme selon la
source ; `MANDATS_AGREGES_CATEGORIES` pourra être revisité séparément.

