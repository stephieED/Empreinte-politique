<a id="gouvernement-doc-cloture"></a>
# Documentation upkeep de clôture, vue Gouvernement (#214, plan #184) (2026-08-14)

`2026-08-14`

> **En bref** — passe documentaire de clôture de la vue Gouvernement, sans anticiper de fonctionnalité non livrée.

**Contexte** : #214 demandait une passe finale de mise à jour documentaire
une fois #207-#213 réellement mergées, sans anticiper de fonctionnalité non
livrée. Les PR #207-#213 avaient déjà fait leur propre upkeep `AGENTS.md §8`
au fil de l'eau ; cette entrée ne duplique pas ce contenu, elle le
consolide par renvoi :

1. **Rattachement des textes par `date_depot`** : décision et alternative
   rejetée (chaîne `AMO30`) déjà documentées in extenso —
   voir [[gouvernement-profile-rattachement]] (#211) et [[gouvernement-textes-statut]]
   (#210, section "Alternative rejetée").
2. **Gap couverture ministérielle (`portefeuille`)** : déjà documenté comme
   hors périmètre — voir [[hors-perimetre]] § "Ministerial function", repris
   dans `check_quality_gate.py` ([[quality-gate-gouvernements]]) et `ROADMAP.md`.
   Pas de nouvelle source identifiée depuis #212 ; toujours non résolu.
3. **Limite Sénat, confirmée spécifique à cette vue** : `gouvernement_textes.py`
   ne lit que le dump AN `Dossiers_Legislatifs.json.zip` — un texte dont le
   Sénat est la chambre de dépôt *primaire* n'est jamais vu (seuls les textes
   déposés à l'AN, y compris ceux transmis en 2e lecture au Sénat, entrent
   dans `textes[]`). C'est un cas particulier de la limite déjà actée en
   [[hors-perimetre]] § "Senate votes, amendments, sponsored texts" (aucun
   dataset Sénat structuré exploitable), reconfirmé ici pour la vue
   Gouvernement spécifiquement car `schema_gouvernement.py` expose
   `chambre_depot_initial` (`"AN"` ou `"Senat"`) et pourrait laisser croire à
   tort à une couverture bicamérale complète.

**Hors périmètre de cette entrée** : aucun changement de code ; voir la table
`AGENTS.md §8` appliquée dans la PR de #214 pour le détail fichier par
fichier. `docs/pipeline-gouvernement.md` (miroir de
`docs/data-architecture.md`) n'est pas créé ici : proposition
soumise à validation explicite (hors table d'upkeep existante), voir la PR.

