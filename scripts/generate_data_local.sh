#!/usr/bin/env bash
# Équivalent local de .github/workflows/generate-data.yml (workflow_dispatch),
# sans passer par GitHub Actions — utile pour contourner les gels runner
# ("shutdown signal") en générant le jeu de données complet sur sa propre
# machine. Reproduit l'ordre et les commandes exactes des jobs CI ; diffère
# uniquement là où l'orchestration GH Actions (artifacts, matrix par candidat)
# n'a pas d'équivalent utile en local :
#   - extract-an tourne ici sur TOUS les candidats en une fois (pas de matrix
#     par candidat : inutile hors CI, où son seul but est d'isoler la perte
#     en cas de gel runner).
#   - Pas d'étape merge_profile.py --dirs : chaque source écrit déjà
#     directement dans raw_data/profiles/ (fusion additive native de
#     generate_all_profiles.py), il n'y a rien à re-fusionner depuis des
#     artifacts séparés puisque tout tourne sur le même filesystem.
#   - Aucun commit/push automatique (dernière étape du job merge-and-pivot) :
#     vérifier le résultat, puis committer/pousser manuellement si satisfait.
#
# Chaque étape a le même comportement "continue-on-error" que son job CI
# correspondant (voir commentaires) : un échec n'interrompt pas le reste.
#
# Options d'entrée, mêmes défauts que workflow_dispatch dans generate-data.yml :
#   EXISTING_PROFILES=leave-as-is|refresh|overwrite
#                                     (défaut: refresh — recollecte l'existant
#                                      en FUSIONNANT ; overwrite pose
#                                      --no-merge, cf. #578)
#   ADD_UNCOVERED_MEMBERS=true|false
#                                     (défaut: true — écrit un premier profil
#                                      pour les membres qui n'en ont pas ;
#                                      axe 2 du formulaire, cf. #578/#590)
#   COLD_START=false|true             (défaut: false — purge les caches de
#                                      téléchargement, rien d'autre)
#   THRESHOLD=<n>                     (défaut: 3)
#   WORKERS=<n>                       (défaut: 1 — séquentiel, cf. retour
#                                      d'expérience utilisatrice sur la
#                                      parallélisation, docs/technical_decisions.md)
#   EXTRACT_INTERVENTIONS=false|true  (défaut: false)
#   ROSTER_EXTRACTION_LIMIT=<n>       (défaut: 0 = pas de plafond)
#   BACKGROUND=true|false             (défaut: true — se relance soi-même via
#                                      nohup et rend la main immédiatement ;
#                                      false = tourne au premier plan, logs
#                                      affichés en direct dans le terminal)
#
# Logs : toujours écrits dans logs/generate_data_local_<horodatage>.log
# (dossier créé si absent, git-ignoré comme .cache/) — en plus de la sortie
# terminal si BACKGROUND=false, à la place si BACKGROUND=true (nohup).
#
# Exemple : WORKERS=4 ROSTER_EXTRACTION_LIMIT=0 ./scripts/generate_data_local.sh
# Suivre la progression d'un run en arrière-plan : tail -f logs/generate_data_local_*.log
# Arrêter un run en arrière-plan : kill <PID affiché au lancement>

set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

mkdir -p logs

# Relance auto en arrière-plan (nohup) sauf si déjà relancé (_GDL_CHILD, garde
# anti-récursion) ou BACKGROUND=false explicite (mode premier plan / debug).
if [ "${BACKGROUND:-true}" = "true" ] && [ -z "${_GDL_CHILD:-}" ]; then
  LOG_FILE="logs/generate_data_local_$(date -u +%Y%m%dT%H%M%SZ).log"
  echo "Lancement en arrière-plan — logs : $LOG_FILE"
  # < /dev/null explicite : un stdin hérité fermé/invalide (terminal non
  # interactif, panneau IDE...) fait échouer bash au relancement ("error
  # reading input file: Bad file descriptor") — nohup ne redirige stdin que
  # s'il détecte un terminal, donc ne suffit pas seul dans ce cas.
  _GDL_CHILD=1 nohup "$0" "$@" < /dev/null > "$LOG_FILE" 2>&1 &
  BG_PID=$!
  disown
  echo "PID : $BG_PID"
  echo "Suivre : tail -f $LOG_FILE"
  echo "Arrêter : kill $BG_PID"
  exit 0
fi

# Deux axes disjoints, mêmes noms et mêmes défauts qu'en CI (#578).
# `FRESH_RUN` reste accepté comme alias historique de `COLD_START`.
EXISTING_PROFILES="${EXISTING_PROFILES:-refresh}"
ADD_UNCOVERED_MEMBERS="${ADD_UNCOVERED_MEMBERS:-true}"
COLD_START="${COLD_START:-${FRESH_RUN:-false}}"
THRESHOLD="${THRESHOLD:-3}"
WORKERS="${WORKERS:-1}"
EXTRACT_INTERVENTIONS="${EXTRACT_INTERVENTIONS:-false}"
ROSTER_EXTRACTION_LIMIT="${ROSTER_EXTRACTION_LIMIT:-0}"

case "$EXISTING_PROFILES" in
  leave-as-is|refresh|overwrite) ;;
  *) echo "[!] EXISTING_PROFILES=$EXISTING_PROFILES inconnu (leave-as-is|refresh|overwrite)." >&2; exit 2 ;;
esac
case "$ADD_UNCOVERED_MEMBERS" in
  true|false) ;;
  *) echo "[!] ADD_UNCOVERED_MEMBERS=$ADD_UNCOVERED_MEMBERS inconnu (true|false)." >&2; exit 2 ;;
esac

if [ -f .venv/bin/activate ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

export PYTHONUNBUFFERED=1

# Mode premier plan (BACKGROUND=false) : sortie dupliquée vers un fichier de
# log, en plus du terminal — même contrat "logs toujours sauvegardés" que le
# mode arrière-plan ci-dessus (qui, lui, redirige déjà tout via nohup).
if [ -z "${_GDL_CHILD:-}" ]; then
  LOG_FILE="logs/generate_data_local_$(date -u +%Y%m%dT%H%M%SZ).log"
  echo "Mode premier plan — logs également sauvegardés dans : $LOG_FILE"
  exec > >(tee -a "$LOG_FILE") 2>&1
fi

MERGE_FLAG=()
[ "$EXISTING_PROFILES" = "overwrite" ] && MERGE_FLAG=(--no-merge)

INTERV_FLAG=()
[ "$EXTRACT_INTERVENTIONS" != "true" ] && INTERV_FLAG=(--skip-interventions)
# `MAX_PAGES`/`--max-pages` ont été retirés avec la recherche d'interventions
# NosDéputés (#510) : elle n'alimentait que le repli, lui-même retiré.

if [ "$COLD_START" = "true" ]; then
  # Comme en CI (#578) : purge des CACHES DE TÉLÉCHARGEMENT, et rien d'autre.
  # Ce qu'on fait des profils déjà écrits est l'autre axe.
  echo "=== Purge des caches de téléchargement (cold_start) ==="
  rm -rf .cache
fi

echo "=== [1/6] extract-amendements-an : index amendements (17/16/15) ==="
python3 src/build_amendements_index.py || echo "[!] extract-amendements-an en échec (continue-on-error, comme en CI)"

echo "=== [2/6] extract-an : Assemblée nationale (tous les candidats) ==="
python3 src/generate_all_profiles.py --source an --workers "$WORKERS" "${MERGE_FLAG[@]}" "${INTERV_FLAG[@]}" \
  || echo "[!] extract-an en échec (continue-on-error, comme en CI)"

# L'étape « extract-senat » a été retirée par #528, en même temps que le job CI :
# le Sénat est sorti du périmètre du produit et `--source senat` n'existe plus.
# Voir docs/decisions/retrait-senat-528.md.

echo "=== [3/6] extract-ue-officiel : Parlement européen (Open Data Portal) ==="
python3 src/generate_all_profiles.py --source ue --workers "$WORKERS" "${MERGE_FLAG[@]}" \
  || echo "[!] extract-ue-officiel en échec (continue-on-error, comme en CI)"

echo "=== [4/6] extract-parltrack : dumps ParlTrack (.zst) ==="
# Fichier temporaire plutôt qu'un heredoc (python3 - <<EOF) : un heredoc lit
# depuis le flux du script lui-même, sensible aux mêmes soucis de descripteur
# de fichier hérité qu'expliqué ci-dessus sur le relancement nohup — un
# fichier réel sur disque n'en dépend pas du tout.
PARLTRACK_SCRIPT="$(mktemp -t generate_data_local_parltrack.XXXXXX.py)"
trap 'rm -f "$PARLTRACK_SCRIPT"' EXIT
cat > "$PARLTRACK_SCRIPT" <<'PYEOF'
import sys
sys.path.insert(0, "src")
from parltrack_dumps import ensure_dump, _DUMP_DOSSIERS, _DUMP_PLENARY_AMENDMENTS, _DUMP_COMMITTEE_AMENDMENTS
force = sys.argv[1] == "true"
ok = True
for dump in [_DUMP_DOSSIERS, _DUMP_PLENARY_AMENDMENTS, _DUMP_COMMITTEE_AMENDMENTS]:
    path = ensure_dump(dump, force_download=force)
    if path is None:
        print(f"[!] Échec téléchargement : {dump}", file=sys.stderr)
        ok = False
sys.exit(0 if ok else 1)
PYEOF
python3 "$PARLTRACK_SCRIPT" "$COLD_START" || echo "[!] extract-parltrack en échec (continue-on-error, comme en CI)"
rm -f "$PARLTRACK_SCRIPT"
trap - EXIT

echo "=== [5/6] extract-roster-groupes : membres de groupe (mode léger) ==="
# #511 : sortie non nulle sur une collecte incomplète (fetch en échec, groupe à
# 0 membre, roster vide). Ce script n'a pas `set -e` — sans ce test explicite,
# l'extraction ci-dessous repartirait sur un roster périmé ou absent, ce qui est
# exactement l'enchaînement qui a produit 229 profils bruts pour 209 pivots.
#
# Mais elle n'arrête plus le script (#524) : en CI, un shard roster rouge ne tue
# pas `merge-and-pivot`, et ce script doit refléter la même chose. Codes 1
# (roster incomplet, NON écrit) et 2 (extraction de tous les groupes suspendue)
# sautent la branche roster ; tout autre code reste un échec, pour ne pas
# avaler un plantage réel.
ROSTER_CODE=0
python3 src/generate_roster_candidats.py || ROSTER_CODE=$?
if [ "$ROSTER_CODE" != "0" ] && [ "$ROSTER_CODE" != "1" ] && [ "$ROSTER_CODE" != "2" ]; then
  echo "[!] generate_roster_candidats.py : code inattendu $ROSTER_CODE."
  exit "$ROSTER_CODE"
fi
if [ "$ROSTER_CODE" != "0" ]; then
  echo "[!] Roster non régénéré (code $ROSTER_CODE) — extraction roster sautée, le reste du pipeline continue (#524)."
else
LIMIT_FLAG=()
[ -n "$ROSTER_EXTRACTION_LIMIT" ] && [ "$ROSTER_EXTRACTION_LIMIT" != "0" ] && LIMIT_FLAG=(--limit "$ROSTER_EXTRACTION_LIMIT")
# Même table que le job roster de generate-data.yml (#578) : la population
# vient des deux axes, jamais de la présence d'un plafond.
POP_FLAG=()
SAUTER_ROSTER=false
if [ "$EXISTING_PROFILES" = "leave-as-is" ]; then
  if [ "$ADD_UNCOVERED_MEMBERS" != "true" ]; then
    SAUTER_ROSTER=true
  else
    POP_FLAG=(--skip-existing)
  fi
elif [ "$ADD_UNCOVERED_MEMBERS" != "true" ]; then
  POP_FLAG=(--refresh-existing)
fi
if [ "$SAUTER_ROSTER" = "true" ]; then
  echo "Aucun membre à traiter : EXISTING_PROFILES=leave-as-is et ADD_UNCOVERED_MEMBERS=false."
else
python3 src/generate_all_profiles.py \
  --candidats raw_data/roster_candidats.json \
  --workers "$WORKERS" \
  "${POP_FLAG[@]}" --resume \
  --skip-interventions --skip-dossiers-legislatifs \
  "${LIMIT_FLAG[@]}" "${MERGE_FLAG[@]}" \
  || echo "[!] extract-roster-groupes en échec (continue-on-error, comme en CI)"
fi
fi

echo "=== [6/6] merge-and-pivot : pivots, groupes, gouvernements, quality gate ==="

# --no-checkpoint comme en CI (#518) : une passe --pivot-only n'a rien à
# reprendre, et son point de sauvegarde s'écrirait dans raw_data/profiles/,
# où le garde-fou #511 le prendrait pour un profil brut sans pivot.
python3 src/generate_all_profiles.py \
  --pivot-only \
  --no-checkpoint \
  --enrich-parltrack \
  --parltrack-status-out parltrack-status.json \
  --workers "$WORKERS" \
  "${MERGE_FLAG[@]}"

# #511 : sans ce test, un roster non régénéré fait normaliser la passe suivante
# sur une liste périmée — ou, dans l'incident d'origine, sur une liste vide.
# `--rosters-bruts-out` reproduit ce que le run CI transite par l'artifact
# `roster-candidats` : le step groupes plus bas lit cette liste au lieu d'en
# refetcher une (#518).
#
# Le `exit 1` d'ici est tombé avec #524, et c'est le même arbitrage qu'en CI :
# la passe pivot des candidats déclarés vient de se terminer juste au-dessus,
# les fiches de parti et de groupe suivent, et une donnée NON écrite n'annule
# pas la publication d'une donnée écrite. Seule la branche roster est sautée.
ROSTER_PIVOT_CODE=0
python3 src/generate_roster_candidats.py \
  --rosters-bruts-out raw_data/rosters_bruts.json || ROSTER_PIVOT_CODE=$?
if [ "$ROSTER_PIVOT_CODE" != "0" ] && [ "$ROSTER_PIVOT_CODE" != "1" ] && [ "$ROSTER_PIVOT_CODE" != "2" ]; then
  echo "[!] generate_roster_candidats.py : code inattendu $ROSTER_PIVOT_CODE."
  exit "$ROSTER_PIVOT_CODE"
fi
if [ "$ROSTER_PIVOT_CODE" != "0" ]; then
  echo "[!] Roster non régénéré (code $ROSTER_PIVOT_CODE) — pivots roster non produits, le reste du pipeline continue (#524)."
else
python3 src/generate_all_profiles.py \
  --pivot-only \
  --no-checkpoint \
  --candidats raw_data/roster_candidats.json \
  --workers "$WORKERS" \
  "${MERGE_FLAG[@]}"
fi

python3 src/parti_profile.py \
  --candidats raw_data/candidats.json \
  --profiles-dir pivot_data/profiles \
  --out-dir pivot_data/partis

GROUPE_MERGE_FLAG=()
[ "$EXISTING_PROFILES" != "overwrite" ] && GROUPE_MERGE_FLAG=(--merge-existing)
# Même filtrage qu'en CI, et pour la même raison (#518) : le code 2 dit « roster
# indisponible, aucune fiche touchée » — le run continue. Tout autre code reste
# un échec. Ne pas remplacer par un `|| true`, qui avalerait aussi le code 1.
GROUPE_CODE=0
python3 src/generate_group_profiles.py \
  --config raw_data/groupes_reels.json \
  --profiles-dir pivot_data/profiles \
  --out-dir pivot_data/groupes \
  --rosters-bruts raw_data/rosters_bruts.json \
  --validate "${GROUPE_MERGE_FLAG[@]}" || GROUPE_CODE=$?
if [ "$GROUPE_CODE" -eq 2 ]; then
  echo "[!] Roster indisponible : aucune fiche de groupe régénérée, les versions existantes restent en place (#518)."
elif [ "$GROUPE_CODE" -ne 0 ]; then
  exit "$GROUPE_CODE"
fi

python3 src/generate_gouvernement_profiles.py \
  --config raw_data/gouvernements_reels.json \
  --profiles-dir pivot_data/profiles \
  --out-dir pivot_data/gouvernements \
  --validate

python3 src/check_quality_gate.py \
  --profiles-dir      pivot_data/profiles \
  --groupes-dir       pivot_data/groupes \
  --partis-dir        pivot_data/partis \
  --raw-dir           raw_data/profiles \
  --candidats         raw_data/candidats.json \
  --groupes-config    raw_data/groupes_reels.json \
  --gouvernements-dir    pivot_data/gouvernements \
  --gouvernements-config raw_data/gouvernements_reels.json \
  --threshold         "$THRESHOLD" \
  --low-interventions 10 \
  --groupe-min-members 1 \
  --parltrack-status-file parltrack-status.json

echo
echo "=== Terminé ==="
echo "Rien n'a été committé/poussé automatiquement (contrairement au job CI)."
echo "Vérifier 'git status' / 'git diff' sur raw_data/profiles, pivot_data/profiles,"
echo "pivot_data/partis, pivot_data/groupes, pivot_data/gouvernements, puis"
echo "committer/pousser manuellement si le résultat est satisfaisant."
