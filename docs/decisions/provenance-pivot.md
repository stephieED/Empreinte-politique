<a id="provenance-pivot"></a>
# Provenance des profils pivot : candidat_declare vs roster_groupe (2026-08-10)

`2026-08-10`

> **En bref** — `meta.provenance` distingue `candidat_declare` de `roster_groupe`.

**Contexte** : #188 introduit `generate_roster_candidats.py`, qui produit une
liste de "candidats" alternative à `raw_data/candidats.json`, pilotée par la
composition réelle des groupes parlementaires (`statut: "roster_groupe"`) plutôt
que par la liste éditoriale des candidats déclarés à la présidentielle. Une fois
les deux sources utilisées pour générer des pivots (`generate_all_profiles.py`),
un même `slug` peut être régénéré par les deux : un membre de groupe extrait via
le roster peut aussi être un candidat déclaré déjà enrichi manuellement (`parti`
notamment, renseigné depuis `candidats.json`).

**Décision** : ajouter `meta.provenance` (`"candidat_declare"` | `"roster_groupe"`,
voir `schema_pivot.KNOWN_PROVENANCES`) au schéma pivot, propagé par
`normalize_nosdeputes()`/`normalize_europarl()` et renseigné par
`generate_all_profiles.py` selon `candidat["statut"]`. Règle de fusion dans
`merge_profile.merge_pivot_profile()` : un profil déjà `"candidat_declare"` n'est
jamais rétrogradé vers `"roster_groupe"` par une régénération roster-driven du
même slug — la valeur éditoriale de vérité (`candidats.json`) prime toujours sur
l'extraction automatique par roster. Les autres champs éditoriaux (`parti`, etc.)
sont déjà protégés par la stratégie `_prefer_non_empty` existante, car
`generate_roster_candidats.py` ne renseigne jamais ces champs (valeur `None`).
Rétro-compatibilité : un pivot existant sans `meta.provenance` (généré avant
cette décision) reste valide et est traité comme `"candidat_declare"` par défaut
par `validate_profil()` et la politique de fusion — pas de migration nécessaire.

*Alternative rejetée* : marquer la provenance au niveau du fichier `candidats.json`
uniquement (sans persister l'info dans le pivot) — rejeté car le pivot est la
seule couche lue par les agrégations groupes/partis et par `web/` ; sans champ
dédié dans le pivot lui-même, aucune politique de fusion protectrice n'aurait été
possible lors d'une régénération croisée des deux sources.

