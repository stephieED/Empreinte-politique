<a id="amendements-index-non-regression-fraicheur"></a>
# Non-régression sur échec de reconstruction d'un index amendements + indicateur de fraîcheur (#253) (2026-08-13)

`2026-08-13`

> **En bref** — un échec de reconstruction ne régresse pas l'index en place, et la fraîcheur devient un indicateur.

**Contexte** : sous-issue 5/6 du plan d'architecture #248, bloquée par #251
([[amendements-index-job-dedie-ci]]). Objectif : garantir qu'un échec
définitif de reconstruction d'une législature dans `_download_and_build_amendement_index`
(appelée par le job dédié `extract-amendements-an`, #251) ne peut jamais
effacer un `index_par_acteur.json` déjà en cache et fonctionnel.

**Constat** : `_download_and_build_amendement_index` (#250) n'ouvrait déjà
`index_path` en écriture qu'après succès complet du téléchargement et du
parsing — aucun chemin d'échec (`AmendementsIndexError`, raccourci
`_amendements_legislature_failed_this_run`) n'écrivait donc jamais sur un
index existant. Le seul cas où une reconstruction est réellement retentée
malgré un fichier déjà présent est un cache corrompu (`JSONDecodeError`) :
un index valide est utilisé tel quel sans nouvelle tentative (lecture en
tête de fonction). L'invariant demandé par #253 était donc déjà correct,
mais non testé explicitement ni observable par un consommateur externe.

**Décision** :
1. Tests de non-régression ajoutés (`tests/test_candidate_profile.py`) :
   succès (index remplacé), échec sur cache corrompu préexistant (fichier
   préservé à l'identique, byte pour byte), échec sans index préexistant
   (comportement inchangé, aucun fichier créé), et le raccourci
   inter-candidats/inter-jobs (`_amendements_legislature_failed_this_run`).
2. Indicateur de fraîcheur `fraicheur.json`, écrit par
   `_write_amendements_fraicheur` à côté de `index_par_acteur.json` :
   `{"derniere_construction_reussie": bool, "horodatage": str}`. Écrit à
   chaque tentative concernant un index existant ou nouvellement créé —
   succès (`reussi=True`) ou échec définitif sur un index préexistant
   conservé (`reussi=False`) ; jamais écrit si aucun index n'existe (rien à
   qualifier). Best-effort comme l'écriture de l'index lui-même (`OSError`
   avalée). Hors périmètre ici : exploitation par le quality gate
   (sous-issue 6 de #248).

*Alternative rejetée* : forcer un re-téléchargement inconditionnel à chaque
exécution du job dédié (bypasser la lecture cache-only en tête de fonction)
pour que la protection soit exercée à chaque run plutôt que seulement sur
cache corrompu — rejeté car hors périmètre de #253 (qui ne demande pas de
changer la politique de fraîcheur du cache, seulement de ne jamais régresser
sur échec) et parce que cela viderait de son sens le choix déjà tranché par
#250/#251 de ne retélécharger que si le cache est absent/corrompu.
