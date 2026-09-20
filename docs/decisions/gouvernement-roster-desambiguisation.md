<a id="gouvernement-roster-desambiguisation"></a>
# `gouvernement_roster.py` : désambiguïsation par libellé exact + garde-fou de période, pas l'inverse (#209) (2026-08-14)

`2026-08-14`

> **En bref** — désambiguïsation par libellé exact puis garde-fou de période, jamais l'inverse.

**Contexte** : `mandats[].categorie == "fonction_gouvernementale"` (déjà peuplé
par `candidate_profile.py` depuis `AMO30_tous_acteurs_tous_mandats_tous_organes_historique.json.zip`,
voir [[hors-perimetre]] § "Ministerial function") porte un `label` du type
`"Gouvernement (<libelleAbrege>)"`, où `libelleAbrege` est le seul identifiant
que l'AN expose pour un gouvernement (ex. "BORNE", "LECORNU II") — ambigu en
cas de gouvernements homonymes lors d'un remaniement.

**Décision** : `raw_data/gouvernements_reels.json` (miroir éditorial de
`groupes_reels.json`) fixe manuellement `libelle_an` par gouvernement.
`gouvernement_roster.build_gouvernement_roster` sélectionne un mandat membre
d'abord par correspondance **exacte** de ce libellé, puis vérifie en second
lieu que la période du mandat chevauche celle du gouvernement (garde-fou
contre une anomalie de données, pas critère principal). Périodes de
`gouvernements_reels.json` dérivées des dates min/max réellement observées
sur les mandats `fonction_gouvernementale` déjà présents dans
`pivot_data/profiles/*.pivot.json` (zéro appel réseau, zéro date inventée).

**Alternative rejetée** : filtrer uniquement par chevauchement de période
(sans libellé). Rejeté parce que c'est précisément le chevauchement qui est
ambigu lors d'un remaniement rapproché (l'exemple donné dans l'issue #209 est
la distinction entre deux gouvernements homonymes successifs) — le libellé
exact est la seule donnée qui lève cette ambiguïté de façon fiable.

