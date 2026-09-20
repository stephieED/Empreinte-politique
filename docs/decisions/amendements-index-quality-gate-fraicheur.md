<a id="amendements-index-quality-gate-fraicheur"></a>
# Quality gate : distinguer un index amendements jamais construit d'un index périmé (#254) (2026-08-13)

`2026-08-13`

> **En bref** — le quality gate distingue un index jamais construit d'un index périmé.

**Contexte** : sous-issue 6/6 (dernière) du plan d'architecture #248, bloquée
par #251 ([[amendements-index-job-dedie-ci]]), #252
([[amendements-index-cache-only-consumers]]) et #253
([[amendements-index-non-regression-fraicheur]]). Clôture le fil ouvert par
#239 ([[amendements-retry-blocage-legislature]]) → #241/#242
([[amendements-range-download-legislature-isolation]]) → #245/#246
([[retry-generate-data-continue-on-error]], [[amendements-failed-legislature-marker-inter-jobs]])
→ cette issue : le quality gate n'exploitait jusqu'ici aucun des signaux déjà
construits par cette chaîne de correctifs (isolation par législature, job
dédié, indicateur de fraîcheur), alors que #253 avait explicitement laissé
« l'exploitation par le quality gate » hors périmètre pour cette sous-issue.

**Décision** :
1. Nouvelle section 3d dans `check_quality_gate.py`
   (`_report_amendements_freshness`) : pour chacune des 3 législatures de
   `AN_AMENDEMENTS_PATH` (dupliquées localement en `_AMENDEMENTS_LEGISLATURES`
   — même choix de découplage que `_AMENDEMENTS_INDISPONIBLES_PREFIX`
   existant, ce script n'importe jamais `candidate_profile.py`), lit
   `.cache/amendements_an/<legislature>/{index_par_acteur.json,fraicheur.json}`
   et distingue trois états : **jamais construit** (aucun
   `index_par_acteur.json` en cache), **périmé** (index présent mais
   `fraicheur.json` absent/illisible, ou `derniere_construction_reussie:
   false`, ou réussie il y a plus de `--amendements-staleness-days` jours) et
   **frais** (index présent, dernière tentative connue réussie et récente).
   Soft warning uniquement (n'empêche pas le commit), même traitement que le
   reste de la section 3c dont elle prolonge la numérotation.
2. **Limite assumée du signal « périmé »** : `fraicheur.json` (#253) ne
   conserve que l'issue de la *dernière tentative connue*, pas un historique —
   un échec écrase le `reussi`/`horodatage` d'un succès antérieur éventuel.
   Le quality gate ne peut donc pas calculer un véritable « nombre de jours
   sans reconstruction réussie » quand la dernière tentative a échoué ; dans
   ce cas (ainsi que fraîcheur absente/illisible), l'index est signalé périmé
   **immédiatement**, sans attendre le seuil en jours — seul le cas
   `reussi=true` applique réellement le seuil `--amendements-staleness-days`
   (défaut 7, aligné sur la granularité de cache hebdomadaire déjà tranchée
   par #249, voir
   [[amendements-index-budget-ci-cache-granularite]]). *Alternative rejetée* :
   ajouter un champ supplémentaire à `fraicheur.json` (ex. horodatage du
   dernier succès distinct de la dernière tentative) pour permettre un calcul
   exact dans tous les cas — explicitement hors périmètre de #254 (« Pas de
   nouveau mécanisme de détection au-delà du signal de péremption décrit
   ci-dessus ») : le gate consomme strictement le contrat déjà livré par
   #253, sans l'étendre.
3. Deux nouvelles options CLI : `--amendements-cache-dir` (défaut
   `.cache/amendements_an`) et `--amendements-staleness-days` (défaut 7, `0`
   désactive entièrement la section, même convention que
   `--low-syceron-coverage`).
4. `.github/workflows/generate-data.yml` (job `merge-and-pivot`, seul job qui
   exécute `check_quality_gate.py`) : ajout d'une étape `download-artifact`
   optionnelle (`continue-on-error: true`) pour `amendements-index-an` vers
   `.cache/amendements_an`, avant l'étape « Quality gate ». Nécessaire :
   contrairement à `extract-an`/`extract-roster-groupes` (qui ont déjà cette
   étape depuis #251/#252), `merge-and-pivot` ne restaurait jusqu'ici aucun
   contenu de `.cache/amendements_an` — sans cet ajout, la nouvelle section 3d
   aurait signalé les 3 législatures « jamais construites » à **chaque** run
   réel, quelle que soit leur fraîcheur réelle côté job dédié, rendant le
   signal inutilisable en production. Poussé directement dans ce commit —
   contrairement à #228/#230 (création d'un nouveau fichier sous
   `.github/workflows/`, bloquée par les permissions de l'app GitHub),
   modifier un fichier existant a fonctionné pour #237 ; à vérifier au
   prochain retour humain si ce n'est pas le cas ici.
5. `docs/sources/an-opendata.md` : **laissé inchangé** — ce fichier documente les
   points d'accès AN Open Data (URLs, tailles d'archives), jamais la structure
   du cache local ni le contrat `fraicheur.json` ; cette issue ne change ni
   l'un ni l'autre, seulement un nouveau consommateur d'un fichier déjà livré
   par #253.
6. `AGENTS.md` §3 (diagramme pipeline Mermaid) : **laissé inchangé** — ce
   diagramme représente le flux de transformation des données (raw_data →
   pivot_data → quality gate), pas les jobs CI individuels ; le job dédié
   `extract-amendements-an` lui-même (#251) n'y figure pas, pas plus que les
   autres jobs `extract-*`. Le texte de prose au-dessus du diagramme (§3,
   ligne « Quality gate ») est en revanche mis à jour pour mentionner le
   nouveau signal.

**Tests** : `tests/test_quality_gate_amendements.py` — cache absent (3×
« jamais construit »), index frais (aucun warning), reconstruction réussie
mais au-delà du seuil (périmé), dernière tentative en échec signalée
immédiatement quel que soit l'âge, index sans `fraicheur.json` traité comme
périmé plutôt que faux-frais, états mixtes sur les 3 législatures
simultanément, et le cas `--amendements-staleness-days 0` (aucun raccourci de
désactivation interne à `_report_amendements_freshness` — c'est `main()` qui
saute l'appel sur seuil nul, la fonction elle-même applique un seuil de 0
jour littéral si on l'appelle directement).

*Alternative rejetée* : hard fail sur index périmé/jamais construit plutôt que
soft warning — rejeté, l'issue #254 demande explicitement un traitement
cohérent avec les autres signaux de la section 3c (soft warning), une
législature d'amendements indisponible n'étant pas une régression de
structure au même titre qu'un fichier groupe cassé (section 4).

