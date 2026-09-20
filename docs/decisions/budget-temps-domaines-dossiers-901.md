<a id="budget-temps-domaines-dossiers-901"></a>
# La passe des domaines EuroVoc des dossiers a fait annuler un run : son budget est désormais en temps (#901) (2026-09-17)

`2026-09-17`

> **En bref** — Le premier run portant `domaines-eurovoc-des-dossiers-901`
> (`35231390627`) a consommé ses 1 500 requêtes au portail en **88 minutes**,
> et non en 25 comme estimé. `merge-and-pivot` a dépassé ses 120 minutes, a été
> annulé, et n'a rien commité : ni le corpus, ni le cache des 1 501 réponses. La
> passe est désormais bornée par une **durée** (20 min), et le cache du portail
> est **sauvegardé juste après l'étape**, même si la suite échoue.

## Ce qui s'est passé

Run `35231390627`, étape « Générer l'index des dossiers européens » :
16 h 18 → 18 h 46 (heure de Paris), soit 88 minutes, pour 1 501 requêtes —
**3,5 s par requête**. L'essai du matin, depuis un poste, tournait à 0,9 s.
Compteurs : 301 dossiers avec domaines, 599 `documents_non_classes`, 3 739
`question_non_posee`, 3 `aucun_document_de_seance`.

Le job a atteint `timeout-minutes: 120` et a été annulé à 18 h 53. Le post-job
`actions/cache` évalue `success()` : faux, donc **aucune sauvegarde**. Le run
suivant aurait refait les mêmes 1 501 requêtes, et dépassé de la même façon.

Deux erreurs de conception de `domaines-eurovoc-des-dossiers-901`, et elles sont
à moi : une estimation de débit tirée d'une mesure locale, et un cache supposé
cumulé sans vérifier qu'il survivait à un échec.

## Décision

1. **`--budget-secondes`, défaut 1 200** : au-delà, la passe cesse d'interroger le
   portail (le cache répond encore) et les dossiers restants portent
   `question_non_posee`. Le plafond en requêtes (1 500) reste une borne haute. Au
   débit mesuré, 20 minutes valent ~340 requêtes : les dossiers amendés d'abord,
   puis les votés, run après run.
2. **Step « Sauvegarder le cache du portail européen »**, en `if: always()`, juste
   après l'index des dossiers, sous la clé
   `public-data-cache-europarl-documents-v3-<run_id>-dossiers`. Le préfixe de
   restauration existant la retrouve ; quand le run réussit, la sauvegarde du
   post-job, plus récente, l'emporte.

## Alternatives rejetées

- **Baisser le plafond en requêtes** : un débit ne se prévoit pas ; c'est
  exactement ce qui a échoué.
- **Relever `timeout-minutes`** : le job porte déjà tout le pivot ; l'allonger pour
  une passe réseau ferait payer au corpus chaque ralentissement du portail.
- **Sortir la passe dans un job à part** : plus propre, mais un chantier de
  workflow disproportionné pour ce correctif.
