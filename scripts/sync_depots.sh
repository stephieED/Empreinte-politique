#!/usr/bin/env bash
# sync-depots.sh — les deux dépôts d'Empreinte politique, dans les deux sens.
#
#   Empreinte-politique-src  (privé)  le développement : code, issues, PR
#   Empreinte-politique      (public) la publication : code + données, et les runs
#
# Le privé écrit le CODE, le public produit les DONNÉES. Aucun des deux n'a
# raison sur tout, d'où les deux sens :
#
#   --recuperer-donnees   public → privé   les données régénérées par les runs
#   --publier-code        privé → public   le code, dans un commit de publication
#   --etat                ne touche à rien, dit où en sont les deux
#
# L'ORDRE COMPTE. `--publier-code` pousse un arbre entier : s'il part d'un privé dont
# les données sont périmées, il ÉCRASE les données fraîches du public. Récupérer les
# données d'abord, publier le code ensuite. `--tout` fait exactement ça.
#
# POURQUOI PAS `git push public main`. Les deux historiques n'ont aucun ancêtre
# commun — le public part d'un commit orphelin. Un push simple est refusé, et
# forcé il déverserait les ~1 800 commits du privé sur le dépôt public, avec
# leurs horodatages. Ce script construit donc un commit dont le CONTENU vient du
# privé et le PARENT est le dernier commit public : le public accumule un
# historique de publications, jamais celui du développement.

set -euo pipefail

# La racine du dépôt, déduite et jamais codée en dur : ce script est
# versionné, donc publié, et un chemin absolu y exposerait une arborescence
# personnelle en plus de ne marcher que sur une machine.
DEPOT="${DEPOT:-$(git rev-parse --show-toplevel 2>/dev/null || true)}"
[ -n "$DEPOT" ] || { printf '\033[31m%s\033[0m\n' "Hors d'un dépôt git : préciser DEPOT=<chemin>." >&2; exit 1; }
DONNEES=(pivot_data raw_data)

cd "$DEPOT"

rouge() { printf '\033[31m%s\033[0m\n' "$*" >&2; }
info()  { printf '  %s\n' "$*"; }

verifier_remotes() {
  git remote get-url origin >/dev/null 2>&1 || { rouge "remote 'origin' absent."; exit 1; }
  git remote get-url public >/dev/null 2>&1 || {
    rouge "remote 'public' absent. À ajouter une fois :"
    rouge "  git remote add public https://github.com/stephieED/Empreinte-politique.git"
    exit 1
  }
}

# Un run qui tourne va committer sur public/main : publier maintenant, c'est
# écrire sur une cible qui bouge, et récupérer les données, c'est copier un état à moitié
# écrit.
refuser_si_run_en_cours() {
  local n
  n=$(gh run list -R stephieED/Empreinte-politique --workflow=generate-data.yml \
        --status in_progress --json databaseId --jq 'length' 2>/dev/null || echo 0)
  [ "${n:-0}" = "0" ] || { rouge "Un run de données tourne sur le dépôt public. Attendre sa fin."; exit 1; }
}

etat() {
  git fetch --quiet origin && git fetch --quiet public
  info "privé  : $(git rev-parse --short origin/main)  $(git log -1 --format=%s origin/main | cut -c1-58)"
  info "public : $(git rev-parse --short public/main)  $(git log -1 --format=%s public/main | cut -c1-58)"
  if git diff --quiet origin/main public/main -- "${DONNEES[@]}"; then
    info "données : identiques"
  else
    info "données : DIFFÉRENTES — $(git diff --name-only origin/main public/main -- "${DONNEES[@]}" | wc -l) fichier(s)"
  fi
  local code
  code=$(git diff --name-only origin/main public/main -- . ':(exclude)pivot_data' ':(exclude)raw_data' | wc -l)
  [ "$code" = "0" ] && info "code    : identique" || info "code    : DIFFÉRENT — $code fichier(s)"
}

recuperer_donnees() {
  refuser_si_run_en_cours
  git fetch --quiet public
  [ -z "$(git status --porcelain)" ] || { rouge "Arbre de travail non propre. Committer ou ranger d'abord."; exit 1; }

  if git diff --quiet HEAD public/main -- "${DONNEES[@]}"; then
    info "Rien à récupérer : les données sont déjà identiques."
    return 0
  fi
  info "Récupération de ${DONNEES[*]} depuis le public…"
  git checkout public/main -- "${DONNEES[@]}"
  git commit --quiet -m "chore : données récupérées du dépôt public ($(git rev-parse --short public/main))

Régénérées par un run sur le dépôt public, reprises ici pour que le
développement porte sur le corpus réel."
  info "Fait : $(git rev-parse --short HEAD). Pousser vers le privé avec : git push origin main"
}

publier_code() {
  refuser_si_run_en_cours
  git fetch --quiet origin && git fetch --quiet public

  # Le contenu vient d'origin/main, jamais de l'arbre de travail : on ne publie
  # pas un fichier local oublié.
  local arbre parent version message commit
  arbre=$(git rev-parse origin/main^{tree})
  parent=$(git rev-parse public/main)

  if [ "$arbre" = "$(git rev-parse public/main^{tree})" ]; then
    info "Rien à publier : le contenu est déjà identique."
    return 0
  fi

  # Les données du privé écraseraient celles du public si elles sont plus
  # vieilles. C'est le sens de l'ordre récupérer-les-données → publier-le-code.
  if ! git diff --quiet origin/main public/main -- "${DONNEES[@]}"; then
    rouge "Les données diffèrent entre les deux dépôts."
    rouge "Publier maintenant écraserait celles du public. Lancer --recuperer-donnees d'abord,"
    rouge "pousser vers le privé, puis relancer --publier-code."
    exit 1
  fi

  version="${1:-}"
  [ -n "$version" ] || { rouge "Usage : $0 --publier-code <version>   (ex. v1.0.1)"; exit 1; }
  message="$version"$'\n\n'"Publication du code depuis le dépôt de développement."

  commit=$(git commit-tree "$arbre" -p "$parent" -m "$message")
  git push public "$commit:refs/heads/main"

  # Vérifier la RÉFÉRENCE, jamais le message de la commande qui précède.
  if [ "$(git ls-remote public refs/heads/main | cut -f1)" = "$commit" ]; then
    info "Publié : $commit"
  else
    rouge "Le push n'a pas abouti — la référence distante ne porte pas ce commit."
    exit 1
  fi
}

case "${1:-}" in
  --etat)               etat ;;
  --recuperer-donnees)  verifier_remotes; recuperer_donnees ;;
  --publier-code)       verifier_remotes; publier_code "${2:-}" ;;
  --tout)               verifier_remotes; recuperer_donnees; git push origin main; publier_code "${2:-}" ;;
  *)
    cat >&2 <<USAGE
Usage : $0 --etat | --recuperer-donnees | --publier-code <version> | --tout <version>

  --etat                     dit où en sont les deux dépôts, ne touche à rien
  --recuperer-donnees        public → privé : les données régénérées par les runs
  --publier-code <version>   privé → public : le code, en un commit de publication
  --tout <version>           récupérer les données, pousser vers le privé, publier le code

Refuse d'agir si un run de données tourne sur le dépôt public.
USAGE
    exit 1 ;;
esac
