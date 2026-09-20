# Données UE — investigation des sources (2026-08-04)

`2026-08-04`

> **En bref** — trois pistes mesurées (ParlTrack, profils Europarl, HowTheyVote) sur le même échantillon de 3 candidats : les dumps ParlTrack sont la seule source qui attribue amendements et rapports à un député européen donné.

<a id="investigation-sources-ue"></a>

**Ce fichier n'est pas une doc de job.** C'est le rapport d'investigation qui a
tranché la source des données UE — trois pistes mesurées sur le même échantillon
de 3 candidats, un tableau comparatif, un verdict. Il vit sous `docs/decisions/`
depuis le 30/08/2026 pour cette raison : ce qu'il documente est un **choix**, pas
le fonctionnement d'`extract-ue-officiel` ni celui d'`extract-parltrack`. Ce que
ces deux jobs font aujourd'hui est décrit dans
[`docs/workflow-generate-data.md`](../workflow-generate-data.md) §1.

**Décision appliquée** : piste ParlTrack via dumps, implémentée dans
`src/parltrack_dumps.py` et `src/normalize_parltrack_dumps.py`. La §*Instructions
d'implémentation* et le prompt qui suivent sont conservés **tels qu'écrits le
04/08/2026** : ce sont les consignes d'origine, pas l'état du code. Ce que les
profils UE deviennent aujourd'hui est dans
[`docs/data-architecture.md`](../data-architecture.md).

## Contexte

Objectif: identifier une source exploitable pour récupérer l'activité parlementaire européenne par candidat (rapports/textes portés en tant que rapporteur, et si possible amendements), à partir d'un MEP ID déjà connu.

Contrainte de départ: l'API officielle EP `/plenary-documents` s'est révélée impraticable (pas de filtre auteur, corpus massif à scanner, rate limit contraignante).

Échantillon de test utilisé (3 candidats de la base):
- Jordan Bardella (MEP ID `131580`)
- Marine Le Pen (MEP ID `28210`)
- Jean-Luc Mélenchon (MEP ID `96742`)

---

## Résumé exécutif

- Piste 1 (ParlTrack via dumps): faisable, recommandée.
- Piste 2 (profils MEP officiels Europarl): non faisable dans nos conditions de run actuelles (WAF/challenge).
- Piste 3 (HowTheyVote): utile pour les votes, non adaptée pour rapports/amendements comme source principale.

---

## Piste 1 - ParlTrack

### 1) Format d'accès réel

Accès vérifié:
- Site: `https://parltrack.org/`
- Dumps: `https://parltrack.org/dumps`

Exemples testés (OK):
- `https://parltrack.org/dumps/ep_meps.json.zst`
- `https://parltrack.org/dumps/ep_dossiers.json.zst`
- `https://parltrack.org/dumps/ep_plenary_amendments.json.zst`
- `https://parltrack.org/dumps/ep_amendments.json.zst`

Remarque: la tentative de JSON direct sur page MEP (ex: `?format=json`) renvoie `{"STOP":"scraping!"}`. En pratique, le mode robuste est l'exploitation des dumps.

### 2) Couverture temporelle

Sur `ep_dossiers.json.zst`:
- plage observée: 1972 -> 2026
- 2024: 477 dossiers
- 2025: 120 dossiers
- 2026: 29 dossiers

Sur `ep_meps.json.zst` (candidats test):
- Jordan Bardella: termes `[9, 10]`, actif
- Marine Le Pen: termes `[6, 7, 8]`, non active
- Jean-Luc Mélenchon: termes `[7, 8]`, non actif

Conclusion: la législature actuelle (2024-2029, terme 10) est bien couverte.

### 3) Structure dossiers / rapporteurs

Dans les dossiers, `procedure.reference` + blocs `committees[]` avec `rapporteur` structuré.

Exemple concret:
- `procedure.reference`: `2014/0802(NLE)`
- `committees[].rapporteur[]` contient:
  - `name`
  - `mepref`
  - `group`, `abbr`, `date`

Important:
- `mepref` est majoritairement numérique (jointure facile avec MEP ID).
- présence minoritaire d'un ancien format hash hexadécimal (24 chars) sur des données historiques.

### 4) Structure amendements

Deux dumps dédiés, amendements individuels:
- `ep_plenary_amendments.json.zst`
- `ep_amendments.json.zst` (comités)

Exemple plénière:
- `id`: `A9-0052/2023-1`
- `reference`: `2020/2202(INI)`
- `meps`: `[124747]`
- `authors`, `location`, `date`

Exemple comité:
- `id`: `PE529.899-1`
- `reference`: `2014/2021(INI)`
- `committee`: `["AFET"]`
- `meps`: `[96739]`

Conclusion: les signataires sont disponibles au niveau individuel, avec identifiants MEP.

### 5) Fraîcheur / maintenance

D'après `/dumps` au moment de l'investigation:
- `ep_meps`, `ep_dossiers`, `ep_mep_activities`, `ep_plenary_amendments`: mis à jour `2026-07-24`
- `ep_amendments`: `2026-02-03`

Signal maintenance projet:
- dépôt `parltrack/parltrack` avec commits récents observés.

### 6) Licence

Licence données ParlTrack:
- ODbL v1.0 (annoncée sur la page dumps)

Conséquence:
- réutilisation possible, avec obligations ODbL (attribution + partage à l'identique sur la base dérivée quand applicable).

### 7) Test concret (3 candidats)

Rapporteur (dossiers):
- Jordan Bardella: 0
- Marine Le Pen: 0
- Jean-Luc Mélenchon: 0

Amendements (plénière + comité):
- Jordan Bardella: 15 + 510 = 525
- Marine Le Pen: 0 + 342 = 342
- Jean-Luc Mélenchon: 0 + 154 = 154

Taux de succès "rapporteur et/ou amendements": 3/3 (via amendements).

---

## Piste 2 - Profils officiels MEP (europarl.europa.eu)

### 1) Structure URL

Pattern prévisible testé:
- `https://www.europarl.europa.eu/meps/fr/{id}`
- variantes `/en/{id}` et `/en/{id}/{NOM}/home`

### 2) Faisabilité technique observée

Depuis l'environnement d'exécution (dev container), toutes les requêtes testées sur profils MEP retournent:
- HTTP `202`
- header `x-amzn-waf-action: challenge`
- body vide

Impact:
- impossible de vérifier de manière fiable les sections "Rapports/Avis/Propositions" et la présence d'amendements par scraping backend classique.
- le blocage est de type anti-bot/WAF, plus bloquant qu'une simple limite de débit.

### 3) Test concret (3 candidats)

- 3 URLs candidates testées
- 3/3 bloquées par challenge
- taux de succès extraction automatisée: 0/3

Conclusion: non faisable dans les conditions d'exécution actuelles.

---

## Piste 3 - HowTheyVote.eu (vérification rapide)

### 1) API / exports

Constaté:
- API publique: `https://howtheyvote.eu/api/` (OpenAPI)
- endpoints orientés votes/members (`/api/votes`, `/api/members/{id}`, etc.)
- export dataset annoncé via GitHub (`HowTheyVote/data`)

### 2) Couverture utile pour ce besoin

- produit centré votes (roll-call)
- pas d'API dédiée rapports/textes portés
- pas d'API dédiée amendements comme source de production principale

Conclusion: non adaptée pour le besoin ciblé (rapports + amendements par candidat).

---

## Tableau comparatif

| Piste | Verdict | Effort | Fiabilité observée (échantillon 3) | Risques | Recommandation |
|---|---|---|---|---|---|
| ParlTrack dumps | Faisable | Modéré | 3/3 (amendements), 0/3 (rapporteur sur cet échantillon) | Dépendance tierce, formats `mepref` mixtes historique, volume de dumps | À implémenter |
| Profils Europarl | Non faisable | Lourd | 0/3 (WAF challenge) | Anti-bot CloudFront, extraction non déterministe | À écarter pour maintenant |
| HowTheyVote | Non faisable (pour ce besoin) | Léger | N/A sur rapports/amendements | Couverture hors cible (votes) | À écarter pour ce cas d'usage |

---

## Décision proposée

Implémenter la piste ParlTrack via dumps.

Ne pas investir à ce stade sur le scraping des profils MEP officiels tant que la contrainte WAF n'est pas levée dans l'environnement d'exécution cible.

---

## Instructions d'implémentation pour un agent (ParlTrack via dumps)

Cette section sert de brief exécutable pour un agent de dev.

### Objectif produit

Ajouter un pipeline UE basé sur dumps ParlTrack pour alimenter:
- `textes_portes[]` quand un candidat est rapporteur (si trouvé),
- `amendements[]` signés par le candidat,
- sans casser les règles éditoriales du projet (AGENTS.md).

### Entrées

- `raw_data/candidats.json` (noms/slugs/partis)
- mapping candidat -> MEP ID (source actuelle: `find_mep_by_name` dans `src/candidate_profile_ue.py`)
- dumps ParlTrack:
  - `ep_meps.json.zst`
  - `ep_dossiers.json.zst`
  - `ep_plenary_amendments.json.zst`
  - `ep_amendments.json.zst`

### Sorties attendues

- enrichissement `raw_data/profiles/<slug>.json` sous `mandat_europeen` (ou bloc dédié UE)
- normalisation en pivot dans `pivot_data/profiles/<slug>.pivot.json`:
  - `textes_portes[]` (si rôle rapporteur détecté)
  - `amendements[]`
- aucun score/ranking, aucune valeur par défaut trompeuse

### Plan technique recommandé

1. Créer un module dédié `src/parltrack_dumps.py`
- téléchargement + cache `.cache/parltrack/`
- support `.zst`
- lecture streaming (pas de chargement complet RAM)
- extraction incrémentale

2. Construire des index légers
- index `mep_id -> amendements[]` depuis `ep_plenary_amendments` + `ep_amendments`
- index `mep_id -> dossiers_rapporteur[]` depuis `ep_dossiers` (`committees[].rapporteur[].mepref`)
- gérer double format `mepref` (int + ancien hash)

3. Résolution des IDs historiques
- priorité: `mepref` numérique (join direct)
- fallback historique: table de correspondance hash -> UserID construite depuis `ep_meps`/historique si possible
- si non résolvable: conserver en warning, ne pas inventer

4. Mapper vers le schéma pivot
- `textes_portes[]`: 1 entrée par dossier lié au rôle rapporteur
  - inclure référence procédure, titre, comité, type de rôle, date/source
- `amendements[]`: 1 entrée par amendement signé
  - inclure référence, id amendement, date, location, committee le cas échéant, source

5. Fusion additive
- respecter la logique de merge existante (`src/merge_profile.py`)
- jamais supprimer des données existantes lors d'une régénération partielle

6. Qualité et garde-fous
- tracer `meta.warnings[]` quand source partielle ou mapping ambigu
- ne pas convertir absence de données en `0`
- préserver validation schéma (`validate_profil()`)

### Contrats de test à ajouter

Créer tests unitaires ciblés:
- parsing streaming `.zst`
- extraction amendements pour `131580`, `28210`, `96742` (cas connus)
- cas `mepref` numérique et cas hash non résolu
- mapping vers pivot (`textes_portes`, `amendements`)
- non-régression merge additive

Fichiers tests suggérés:
- `tests/test_parltrack_dumps.py`
- `tests/test_normalize_parltrack_dumps.py`

### Commandes de validation

- tests ciblés:
  - `python -m pytest -q tests/test_parltrack_dumps.py tests/test_normalize_parltrack_dumps.py`
- suite complète:
  - `python -m pytest -q`

### Critères d'acceptation

- sur l'échantillon 3 candidats, au moins les amendements sont correctement récupérés
- schéma pivot valide
- aucune régression sur règles éditoriales AGENTS.md
- pipeline reproductible avec cache local et logs de fraîcheur

---

## Prompt prêt à l'emploi pour lancer un agent d'implémentation

```text
Tu implémentes la piste ParlTrack via dumps dans ce repo, sans toucher au front.

Contexte:
- Respect strict des règles AGENTS.md (pas de scoring, pas de valeurs par défaut trompeuses, traçabilité des sources).
- Source à utiliser: dumps ParlTrack (.zst) et pas scraping de pages MEP.
- Cibles de données: textes_portes (rôle rapporteur quand détecté) + amendements signés.

Travail demandé:
1) Créer un module src/parltrack_dumps.py avec:
   - téléchargement/cache des dumps
   - lecture streaming des .zst
   - extraction par mep_id
2) Intégrer ce module dans la génération de profils UE existante.
3) Mapper vers le schéma pivot v1 (textes_portes, amendements) avec source_url et dates.
4) Respecter la fusion additive existante.
5) Ajouter tests unitaires dédiés + fixtures minimales.
6) Exécuter tests ciblés puis suite complète et corriger erreurs liées aux changements.

Contraintes techniques:
- éviter le chargement RAM complet des dumps
- gérer mepref numérique et cas historiques hashés via fallback contrôlé
- si données ambiguës/non résolues: warning explicite, pas d'invention

Livrables:
- code + tests
- résumé des choix de mapping
- limites restantes et prochaines étapes
```

---

## Note terminologique

Le terme "parltract" utilisé dans la demande est interprété ici comme "ParlTrack".
