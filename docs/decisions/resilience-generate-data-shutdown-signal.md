<a id="resilience-generate-data-shutdown-signal"></a>
# Résilience de `generate-data.yml` face aux `shutdown signal` runner : continue-on-error généralisé, watchdog réseau, retry générique sur `_get_payload`, retry `retry-generate-data.yml` non-régressif, et appels NosDéputés morts pour les députés (dossiers, votes) (2026-08-16)

`2026-08-16`

<a id="dossiers-legislatifs-nosdeputes-vs-an-officiel"></a><a id="get-payload-retry"></a><a id="dossiers-legislatifs-nosdeputes-vs-an-officiel"></a><a id="get-payload-retry"></a>

> **En bref** — continue-on-error généralisé, watchdog réseau, retry générique, appels NosDéputés morts retirés.

**Contexte** : investigation déclenchée par des échecs répétés d'`extract-an`
et `extract-roster-groupes`, tous avec la même signature `shutdown signal`
déjà documentée ([[retry-generate-data-preemption]], #217/#221/#228) —
observée systématiquement juste après le print `-> Dossiers législatifs :
...` (`fetch_dossiers`, `candidate_profile.py`), sur des candidats et
législatures différents d'un run à l'autre.

**Décision 1 — `continue-on-error: true` sur `extract-an`/`extract-senat`/
`extract-ue-officiel`** : avant ce changement, ces 3 jobs n'avaient pas
`continue-on-error`, contrairement à `extract-parltrack`/
`extract-amendements-an`/`extract-roster-groupes`. Un échec de l'un des 3
faisait donc sauter `extract-roster-groupes` **et** `merge-and-pivot` en
entier (`needs:` bloquant), alors que la fusion additive de
`merge_profile.py::merge_raw_dirs` gère déjà nativement un répertoire source
absent. Étendu le même pattern aux 3 jobs restants, et rendu les
téléchargements d'artifacts AN/Sénat/UE dans `merge-and-pivot` optionnels
(`continue-on-error: true`) pour le même motif (un job ayant échoué avant son
étape `Upload artifact` peut laisser l'artifact totalement absent, pas
seulement vide). Résultat vérifié sur un run réel : `extract-an` et
`extract-roster-groupes` en échec, `merge-and-pivot` a quand même tourné et
réussi.

**Décision 2 — watchdog mur (`_get_with_watchdog`,
`candidate_profile.py`)** : `_get_payload` (chokepoint de `fetch_identity`/
`fetch_votes`/`fetch_dossiers`/`fetch_activity_synthesis`) n'utilisait que
`timeout=` de `requests`, qui ne couvre pas la résolution DNS
(`getaddrinfo`) sur toutes les plateformes. Ajout d'un timeout mur
indépendant : la requête tourne dans un thread démon, abandonné après
`TIMEOUT + 10s` quoi qu'il arrive. **Vérifié insuffisant en pratique** : un
run réel a rejoué exactement la même signature `shutdown signal` après ce
correctif (commit confirmé via `headSha` du run), le blocage se produisant
apparemment au niveau du runner entier (aucun thread, pas même celui du
watchdog, n'a pu s'exécuter pour lever l'exception) — cohérent avec une
préemption infra GitHub, pas un bug applicatif. Le watchdog reste une
amélioration défensive légitime (protège contre un DNS/connect réellement
bloqué en cas normal), mais n'était pas la cause du symptôme observé.

**Décision 3 — fix de `retry-generate-data.yml` (reconstruction des
inputs)** : avec le logging de debug activé sur ce dépôt, le log brut d'un
step contenant plusieurs `${{ }}` contient aussi le texte du template GitHub
Actions non résolu (ex. littéralement `--workers {3}`, émis par
`##[debug]Evaluating format(...)`) en plus de la ligne `Run ...` réellement
résolue. `grep -oP -- '--workers \K\S+' | head -1` capturait ce placeholder
au lieu de la vraie valeur — régression constatée sur un run réel :
`workers="{3}"` transmis tel quel au `workflow_dispatch` de relance, faisant
planter `extract-senat`/`extract-ue-officiel` avec `invalid int value:
'{3}'`. Fix : ancrage des motifs sur la ligne de commande finale et
restriction aux caractères attendus (`[0-9]+`, `true|false`) — la valeur
placeholder ne matche alors plus du tout, peu importe sa position dans le
log. Découvert au passage : la détection d'`extract_interventions` était
structurellement toujours fausse (`grep -q -- '--skip-interventions'`
matchait le texte source du script, toujours présent que la condition soit
vraie ou non) ; corrigé en lisant directement la valeur substituée dans la
condition `[[ "<valeur>" != "true" ]]`. Chaque extraction est aussi passée en
`|| true` : sous `set -e`/`pipefail`, un motif non trouvé faisait avant
avorter tout le step (donc perdre les valeurs suivantes, correctement
extractibles) plutôt que de ne dégrader que la valeur en cause vers son
défaut.

<a id="dossiers-legislatifs-nosdeputes-vs-an-officiel"></a>
**Décision 4 — suppression de l'appel NosDéputés pour les dossiers
législatifs des députés** : en creusant pourquoi `fetch_dossiers` (étape 3 de
`build_profile`) était justement le point qui pendait dans tous les runs
observés, découverte que pour `chambre == "deputes"`, son résultat
(`dossiers_payload`, étape 8) est de toute façon **écrasé** juste après par
l'étape 8bis (`fetch_textes_portes_officiels`, source officielle AN via
`ensure_dossiers_zip_downloaded`/`gouvernement_textes.py`, déjà en place et
donnant un résultat propre à chaque élu — voir le commentaire déjà présent
avant ce jour à l'étape 8bis : « Remplace la liste NosDéputés [...], qui
n'est pas propre à l'élu »). L'appel réseau à `nosdeputes.fr/.../dossiers/
nom/json` pour les députés ne servait donc plus à rien depuis que 8bis existe
— juste un risque de blocage gratuit. Décision : ne plus appeler
`fetch_dossiers_for_legislatures` du tout quand `chambre == "deputes"`
(`candidate_profile.py`, étape 3), sans ajouter de retry ni de bascule vers
un téléchargement direct du zip AN pour ce cas — le zip AN est déjà consommé
par 8bis, un deuxième chemin d'accès au même jeu de données officiel aurait
été redondant. Pour `chambre == "senateurs"`, l'appel est conservé
inchangé : aucun remplacement officiel n'est branché pour cette chambre
(l'archive NosSénateurs reste la seule source), donc la question d'un retry
dédié y reste ouverte et distincte — non traitée ici, ce chantier n'ayant mis
en évidence aucun blocage côté sénateurs dans les runs examinés.

**Vérification post-Décision 4** : un run réel avec ce correctif déployé
(`headSha` confirmé) a de nouveau échoué avec la même signature `shutdown
signal` — mais cette fois bloqué sur l'appel suivant dans la séquence
(`-> Synthèse d'activité : .../synthese/data/json`, `fetch_activity_synthesis`,
aucun remplaçant officiel branché pour ce point), pas sur les dossiers.
Confirme ce qu'on avait déjà déduit du watchdog (Décision 2) : le blocage
n'est pas propre à une URL précise, c'est un gel du runner GitHub lui-même à
peu près au même moment dans le job (~1-2 min), quel que soit l'appel réseau
en cours à cet instant — retirer un appel donné ne fait donc que déplacer le
point de blocage, pas disparaître le symptôme. Seul `continue-on-error`
(Décision 1) protège réellement le run dans son ensemble contre ce mode de
défaillance ; les Décisions 4/5 (ce chantier et le suivant) restent
justifiées pour leur propre mérite (suppression d'appels réseau prouvés
morts/inutiles), pas comme correctif du `shutdown signal`.

**Décision 5 — même traitement pour les votes NosDéputés des députés** :
`fetch_votes_officiels` (AN, déjà préféré à l'étape 6) documente déjà dans
son propre docstring que « l'endpoint /votes de NosDéputés.fr est en panne
(HTTP 500 systématique, testé sur tous les domaines et législatures
disponibles) ». Constat confirmé empiriquement dans tous les logs de ce
chantier : `fetch_votes` (étape 1, jusqu'à 8 requêtes — 4 domaines × 2
formats) échoue systématiquement en HTTP 500 ou format non pris en charge,
pour les députés. Conséquence : `votes_raw` y est *garanti* vide, rendant la
branche de repli « `else`: utiliser `votes_raw` » (étape 6) strictement
inatteignable pour cette chambre — plus net encore que pour les dossiers
(pas de simple écrasement après coup, mais une branche de code déjà morte en
pratique). Décision : ne plus appeler `fetch_votes` du tout quand `chambre
== "deputes"` (`candidate_profile.py`, étape 1), même limite que la Décision
4 (aucun effet sur le `shutdown signal` lui-même — voir vérification
ci-dessus). Message de warning (`WARNING_PREFIX_VOTES_INTROUVABLES`) ajusté
en conséquence pour ne plus mentionner une « erreur serveur » qui, pour les
députés, ne se produit plus puisque l'appel n'est plus fait. Pour
`chambre == "senateurs"`, l'appel est conservé inchangé — aucune preuve
équivalente que l'archive NosSénateurs soit cassée, et c'est la seule source
de votes pour cette chambre.

<a id="get-payload-retry"></a>
**Décision 6 — retry léger généralisé dans `_get_payload`** : suite à la
vérification post-Décision 4 ci-dessus (le point de blocage se déplace d'un
appel à l'autre — après le retrait de `fetch_dossiers_for_legislatures`,
`fetch_activity_synthesis` a hérité du `shutdown signal` sur un run réel),
question posée de retenter spécifiquement `fetch_activity_synthesis`.
Écartée : ce point n'est pas la cause, seulement le prochain appel en vol au
moment du gel — un retry câblé sur cette seule fonction n'aurait fait que
redéplacer le symptôme vers l'appel suivant (interventions), et n'aide de
toute façon pas contre un vrai gel du runner (Décision 2 : même un thread de
watchdog totalement indépendant n'arrive pas à s'exécuter dans ce cas).
Généralisé à la place : 3 tentatives max avec backoff fixe 1,5s, ajoutées
directement dans `_get_payload` (le chokepoint déjà partagé par identité/
votes/synthèse/dossiers-Sénat, entre autres). Un seul point d'ajout plutôt
qu'un retry dupliqué par fonction appelante — couvre aussi la demande de
retry Sénat de l'issue #340 (dossiers/votes) sans changement supplémentaire.
Ne retente que les échecs transitoires (5xx, `requests.RequestException`, y
compris le `Timeout` levé par le watchdog) — jamais `_TERMINAL_FAILURE`
(4xx, format non exploitable, JSON malformé), qui reste un échec déterministe
à usage unique. **Effet de bord sur les tests** : plusieurs tests
`build_profile(...)` ne mockaient pas `fetch_activity_synthesis`/
`fetch_all_intervention_results_from_domains`, s'appuyant sur un appel réseau
réel qui échouait vite en sandbox — le retry l'a fait échouer 3× plus
lentement (un test est passé de <1s à 22s). Corrigé en ajoutant les mocks
manquants plutôt qu'en réduisant le retry : plus correct de toute façon (un
test unitaire ne devrait pas dépendre d'un comportement réseau réel, retry ou
pas).

**Décision 7 — deux incohérences relevées par relecture indépendante** (mêmes
fichiers, mêmes commits que ce chantier, non détectées avant relecture) :
1. Le fallback GHA `-f extract_interventions="${{ ... || 'true' }}"`
   (`retry-generate-data.yml`, step *« Re-déclencher generate-data.yml »*)
   divergeait du vrai défaut `workflow_dispatch` déclaré dans
   `generate-data.yml` (`default: false`) — contrairement aux 5 autres
   fallbacks de ce step (`fresh_run||'false'`, `threshold||'3'`,
   `workers||'1'`, `max_pages||'5'`, `roster_extraction_limit||'20'`), tous
   correctement alignés. La justification d'origine de #336
   ([[retry-generate-data-best-effort-non-bloquant]] ci-dessous — « valeur
   initiale du script best-effort avant détection de --skip-interventions »)
   est elle-même devenue caduque : la Décision 3 de ce jour a réécrit cette
   logique bash pour qu'elle retombe correctement sur `false`, donc même le
   script best-effort ne justifie plus le `'true'` du fallback GHA. Corrigé
   en `|| 'false'`.
2. Le commentaire de budget en tête de `generate-data.yml` (« Total mur
   (parallèle) ≈ 120 + 60 = 180 min ») ne comptait que `max(AN, Sénat, UE)`
   + `merge-and-pivot`, sans `extract-roster-groupes` — qui n'est *pas*
   parallèle aux 4 jobs d'extraction (`needs:` sur les 4, #222,
   [[concurrence-ci-roster]]) ni `extract-an` à `extract-amendements-an`
   (`needs:` direct). Chemin critique réel : `max(30+120, 90, 60, 30)` (phase
   parallèle, dominée par la chaîne amendements-an→AN) `+ 60` (roster,
   séquencé après) `+ 60` (merge-and-pivot, séquencé après roster) `= 270
   min`, pas 180. Commentaire manifestement écrit avant l'ajout du
   séquencement roster (#222) et jamais mis à jour depuis. Corrigé avec le
   détail des chaînes de dépendance, pour éviter qu'un futur ajout de job
   laisse à nouveau ce commentaire dériver silencieusement.

