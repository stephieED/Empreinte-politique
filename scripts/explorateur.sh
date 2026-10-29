#!/usr/bin/env bash
# explorateur.sh — pivot_data et raw_data en tableaux reliés, dans le navigateur.
#
#   scripts/explorateur.sh                     reconstruit si les données ont changé, puis ouvre
#   scripts/explorateur.sh --construire        reconstruit, même à jour, sans ouvrir
#   scripts/explorateur.sh --sans-reconstruire ouvre la base existante telle quelle
#
# LECTURE SEULE du dépôt. La base (plusieurs Go) et l'environnement de Datasette
# vivent sous .cache/explorateur/, ignoré par git. Le serveur n'écoute que sur
# cette machine (127.0.0.1) et s'arrête avec Ctrl+C.
# → src/explorateur_donnees.py, docs/commandes.md
set -euo pipefail

DEPOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOSSIER="$DEPOT/.cache/explorateur"
BASE="$DOSSIER/donnees.db"
VENV="$DOSSIER/venv"
PORT="${PORT:-8001}"
MODE="ouvrir"

case "${1:-}" in
  "") ;;
  --construire) MODE="construire" ;;
  --sans-reconstruire) MODE="sans-reconstruire" ;;
  -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
  *) echo "Option inconnue : $1 (voir --help)" >&2; exit 1 ;;
esac

mkdir -p "$DOSSIER"

# Par défaut, seulement si le commit lu a changé ; --construire force.
case "$MODE" in
  ouvrir) python3 "$DEPOT/src/explorateur_donnees.py" --depot "$DEPOT" --base "$BASE" --si-perimee ;;
  construire) python3 "$DEPOT/src/explorateur_donnees.py" --depot "$DEPOT" --base "$BASE" ;;
esac
[ "$MODE" = "construire" ] && exit 0

if [ ! -f "$BASE" ]; then
  echo "Aucune base : lancer d'abord sans --sans-reconstruire." >&2
  exit 1
fi

if [ ! -x "$VENV/bin/datasette" ]; then
  echo "Installation de Datasette dans $VENV (une seule fois)…"
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install -q -r "$DEPOT/scripts/explorateur/requirements.txt"
fi

URL="http://127.0.0.1:$PORT/donnees"
( for _ in $(seq 1 60); do
    if curl -s -o /dev/null "http://127.0.0.1:$PORT/"; then
      command -v xdg-open >/dev/null && xdg-open "$URL" >/dev/null 2>&1 || true
      echo "Explorateur ouvert : $URL  (Ctrl+C pour l'arrêter)"
      break
    fi
    sleep 1
  done ) &

exec "$VENV/bin/datasette" serve "$BASE" \
  --metadata "$DEPOT/scripts/explorateur/metadata.json" \
  --plugins-dir "$DEPOT/scripts/explorateur/plugins" \
  --host 127.0.0.1 --port "$PORT" \
  --setting default_page_size 50 --setting facet_time_limit_ms 3000 \
  --setting sql_time_limit_ms 10000
