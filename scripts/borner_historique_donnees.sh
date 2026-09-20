#!/usr/bin/env bash
#
# borner_historique_donnees.sh — option D de #434 : borner l'historique DE
# DONNÉES plutôt que son contenu.
#
# Ce script NE POUSSE JAMAIS et NE MODIFIE JAMAIS `main`. Il mesure, ou il
# prépare une ref locale que l'humaine inspectera puis poussera elle-même. La
# réécriture d'historique est irréversible pour tous les clones existants :
# c'est une décision, pas une étape de script.
#
#   --mesurer   (défaut)  clone le dépôt dans un répertoire temporaire, y
#                         applique la coupure, repacke, et rend le gain RÉEL.
#                         Ne touche à rien.
#   --preparer            écrit `refs/heads/main-borne` et le tag de sauvegarde
#                         `archive/pre-borne-<date>` dans le dépôt courant,
#                         puis affiche les commandes de push à exécuter à la
#                         main. `main` reste intacte.
#
#   --fenetre N           nombre de commits de données conservés (défaut : 30).
#
# ── Ce que la mesure a établi ────────────────────────────────────────────────
#
#   Deux campagnes, et c'est leur ÉCART qui compte. La seconde a été faite pour
#   #551, parce que l'hypothèse de calibrage de la première avait cessé d'être
#   vraie — voir plus bas.
#
#                                        20/08/2026     28/08/2026
#                                        (0466957,      (dc3ba83,
#                                        209 profils,   479 profils,
#                                        23 c. données) 28 c. données)
#     dépôt après `gc --prune=now` ....   284 Mo         434 Mo
#     `.git` sur disque, avant repack .   853 Mo         (non relevé)
#     taille annoncée par l'API GitHub    395 Mo         (non relevé)
#
#   Le dépôt « pèse » plusieurs chiffres différents, et un seul compte pour les
#   seuils : celui d'après repack. Les 569 Mo d'écart local et les 111 Mo
#   d'écart côté GitHub relevés le 20/08 étaient des objets DEVENUS
#   INACCESSIBLES par des rebases et des pushs forcés — pas de l'historique.
#
#   ⚠ IL Y A DEUX TABLES, ET ELLES RÉPONDENT À DEUX QUESTIONS DIFFÉRENTES.
#   Les confondre est l'erreur que #551 a failli commettre.
#
#   ── (a) RÉTROSPECTIVE : « que gagnerais-je à resserrer AUJOURD'HUI ? » ──
#
#   Mesurée le 28/08/2026 sur un miroir de `dc3ba83` ramené à la SEULE ref
#   `main`, gc --prune=now compris ; 28 commits de données, donc « 28 » =
#   historique complet :
#
#     fenêtre :    0    1    2    3    4    6    8   10   12   15   20   24   27   28
#     dépôt   :  180  194  208  219  225  312  364  394  405  430  430  433  433  434  Mo
#
#   Réponse : presque rien avant 6. Passer de 28 à 15 économise 4 Mo (1 %), à
#   10 en économise 40 (9 %), et il faut descendre à 4 pour en économiser 209
#   (48 %).
#
#   MAIS CETTE TABLE NE FONDE AUCUNE POLITIQUE. Elle sature par le bas
#   uniquement parce que sa QUEUE est faite de commits écrits en phase de
#   développement, quand le corpus faisait 8 à 48 profils. Ce n'est pas une
#   propriété de la fenêtre, c'est une trace de l'histoire du projet — et ces
#   commits-là ne reviendront pas. Le coût d'un commit de données, en packs
#   isolés (`pack-objects` sur `rev-list --objects <c> --not <c>^`) :
#
#                                                médiane  moyenne   min   max
#     14 plus anciens (01→17/08,   8→48 profils)     1,6      1,5   0,2   2,6  Mo
#     14 plus récents (18→27/08, 129→476 profils)   29,3     34,6   0,1  78,6  Mo
#
#   (La table du 20/08, elle, saturait par le HAUT — queue ET tête bon marché.
#   D'où le « borner à 30 ne retire RIEN » qui figurait ici. C'était vrai ;
#   ça ne le sera plus.)
#
#   ── (b) PROSPECTIVE : « quel PLATEAU la fenêtre pose-t-elle ? » ──────────
#
#   C'est celle-ci qui fonde une politique. En régime permanent, les N commits
#   de la fenêtre coûtent tous le même prix : la courbe devient LINÉAIRE,
#   socle + N × coût marginal, et la fenêtre est le SEUL mécanisme qui borne
#   la croissance.
#
#   Coût marginal RÉEL d'un commit conservé, mesuré le 28/08/2026 en empilant
#   les arbres du plus récent vers le plus ancien et en repackant à chaque
#   étape — le seul bloc en régime de production (476 → 481 profils) :
#
#     socle : arbre complet à f5e20b6 (481 profils) ..... 153,6 Mo
#     + e87490c ......................................... + 9,9 Mo
#     + 74c77c2 ......................................... +15,1 Mo
#     + bf063f2 ......................................... +15,3 Mo
#     + de23b62 (729 fichiers) .......................... +15,2 Mo
#
#   Soit 10 à 15 Mo par commit — et NON les 22 à 79 Mo des packs isolés, qui
#   ne peuvent pas se déltifier contre les arbres voisins et surestiment d'un
#   facteur 2 à 5. Projeter sur eux DOUBLERAIT le plateau.
#
#   Ce qui compte est le contenu RÉELLEMENT nouveau, pas le nombre de fichiers
#   réécrits. Deux vérifications : `de23b62` réécrit 729 fichiers — tout le
#   corpus — et ne coûte que 15,2 Mo ; `e4d71cf`, l'une des deux propagations
#   `--no-merge` que #434 disait « structurellement exceptionnelles » et qui
#   pèse 47 Mo en pack isolé, ne coûte que 7,7 Mo en marginal. Une propagation
#   ne crée pas de contenu, elle le recopie, et git le sait.
#
#   Le marginal suit la taille du corpus, un peu moins que proportionnellement :
#   7,7 Mo à 209 profils, 11,5 à 229, ~15,2 à 476 — le corpus fait × 2,28, le
#   marginal × 1,97. C'est ce qui autorise l'extrapolation ci-dessous.
#
#   Plateau posé par la fenêtre (socle 180 Mo + N × marginal) :
#
#     fenêtre :          4    10    15    20    30
#     bas     (10,4) : 222   284   336   388   492  Mo
#     central (14,4) : 238   324   396   468   612  Mo
#     haut    (16,0) : 244   340   420   500   660  Mo
#
#   À 30, le plateau vaut donc 490 à 660 Mo à 479 profils : marge × 3,3 contre
#   les 2 Go du critère de sortie de #429, là où le dépôt d'aujourd'hui est
#   à × 4,7. Extrapolé à 752 membres (facteur 1,58 de #429), 780 à 1 040 Mo,
#   soit × 2,0 à × 2,6. C'est LÀ que le choix de la fenêtre se joue.
#
#   Et le défaut de 30 ne vient PAS d'un budget en octets : #434 l'a tiré d'une
#   règle de latence — « cadence de pointe × période sans surveillance »,
#   4 commits/jour × 7 jours = 28, arrondi à 30 — pour qu'une semaine d'absence
#   reste réparable. La règle est intacte ; c'est son PRIX qui a changé, et il
#   ne se lit que sur la table (b).
#
#   Le besoin forensique, lui, s'exprime en JOURS : les 42 SHA de commits cités
#   dans les .md suivis et les corps d'issues s'étalent du 12 au 28/08/2026,
#   seize jours. La fenêtre, elle, se compte en COMMITS. Le facteur de
#   conversion est la cadence — c'est-à-dire exactement la règle de #434.
#
#   L'arbitrage (valeur, unité, déclenchement, destination de l'archive) est
#   ouvert et n'est PAS rendu ici :
#   voir docs/decisions/fenetre-recalibrage-551.md.
#
# ── Trois pièges, tous rencontrés en mesurant ────────────────────────────────
#
#   1. `git replace --graft` NE SUFFIT PAS. `main` porte des commits de merge
#      dont le second parent plonge avant la coupure : greffer un seul commit
#      laisse l'ancien historique atteignable par un autre chemin. Mesuré :
#      677 commits avant, 677 après la greffe. D'où le rejeu explicite
#      ci-dessous, qui remappe TOUS les parents.
#
#   2. Les index bitmap sont calculés sur le graphe NON greffé, et rev-list les
#      utilise en priorité. Sans `-c pack.useBitmaps=false`, une mesure de
#      vérification rend le résultat d'AVANT la coupure sans le signaler.
#
#   3. Les autres refs ré-épinglent l'ancien historique. Au 20/08/2026 le dépôt
#      local porte 18 refs et GitHub 3 branches + 1 tag. Une branche oubliée
#      garde atteignable tout ce que la coupure prétendait retirer, et le gain
#      est nul sans que rien ne le dise.
#
# ── Ce que l'opération ne rend PAS ───────────────────────────────────────────
#
#   Un push forcé ne libère rien tant qu'un `gc` n'a pas tourné, et côté GitHub
#   on ne peut pas en déclencher un. Mesuré sur un dépôt nu local :
#
#     serveur, historique complet, gc fait ............ 284 Mo
#     après push forcé d'une fenêtre à 3 (169 Mo) ..... 284 Mo  ← INCHANGÉ
#     après `gc --prune=now` .......................... 169 Mo
#
#   Sur GitHub, seule la deuxième ligne est atteignable par nos moyens. La
#   troisième dépend du ramasse-miettes de GitHub, dont la date n'est ni
#   annoncée ni déclenchable.
#
#   MAIS il faut séparer deux choses, et la mesure les sépare nettement. Depuis
#   le MÊME serveur non ramassé, un clone passé par le protocole git :
#
#     serveur sur disque, sans gc ..................... 284 Mo
#     clone frais depuis ce serveur ................... 218 Mo  ← déjà borné
#
#   `upload-pack` reconstruit le pack à partir des seuls objets ATTEIGNABLES.
#   Donc : le coût pour les consommateurs — clone, checkout CI, temps de
#   fetch — tombe IMMÉDIATEMENT après le push forcé, sans attendre aucun gc.
#   Ce qui reste haut, c'est l'empreinte disque côté GitHub et le `size`
#   annoncé par l'API. Mesuré le 20/08/2026 : 284 Mo atteignables contre
#   395 Mo annoncés, soit 111 Mo (39 %) de résidus des rebases et pushs forcés
#   de la journée, toujours pas ramassés.
#
#   (Attention en vérifiant : `git clone` sur un CHEMIN local copie le
#   répertoire d'objets tel quel, résidus compris, et rend donc 284 Mo. Il faut
#   `--no-local` ou une URL `file://` pour mesurer ce que sert vraiment un
#   serveur.)
#
set -euo pipefail

# La fenêtre vaut UN MOIS de données (#551, 28/08/2026) ; 30 en est la
# conversion à une cadence d'un run par jour, pas la décision. Tenue égale à
# `FENETRE_COMMITS_DONNEES` de src/audit_volumetrie_profils.py, qui porte le
# raisonnement complet, par tests/test_borner_historique_donnees.py.
FENETRE=30
MODE=mesurer
MOTIF="mise à jour automatique des données"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mesurer)  MODE=mesurer; shift ;;
    --preparer) MODE=preparer; shift ;;
    --fenetre)  FENETRE=$2; shift 2 ;;
    # L'en-tête entier, quelle que soit sa longueur : une plage de lignes en
    # dur se périme au premier ajout, et tronque l'aide sans le dire.
    -h|--help)  awk 'NR==1{next} /^#/{print; next} {exit}' "$0"; exit 0 ;;
    *) echo "[!] Option inconnue : $1" >&2; exit 2 ;;
  esac
done

RACINE=$(git rev-parse --show-toplevel)
cd "$RACINE"

# ── Rejeu : la coupure devient un commit racine portant l'arbre COMPLET, tous
# les commits postérieurs sont recréés à l'identique (mêmes arbres, mêmes
# blobs, mêmes auteurs, mêmes dates) avec leurs parents remappés.
_rejouer() {
  local depot=$1 cut=$2 sortie=$3
  local tmsg root tip
  tmsg=$(mktemp); trap 'rm -f "$tmsg"' RETURN
  cut=$(git -C "$depot" rev-parse "$cut")
  printf 'data: socle historique — squash de tout ce qui précède %s (#434)\n' \
         "$(git -C "$depot" rev-parse --short "$cut")" > "$tmsg"
  root=$(git -C "$depot" commit-tree "$cut^{tree}" -F "$tmsg")

  local -A carte=()
  carte[$cut]=$root
  local c p np parents
  for c in $(git -C "$depot" rev-list --reverse --topo-order main "^$cut"); do
    parents=""
    for p in $(git -C "$depot" rev-list --parents -n1 "$c" | cut -d' ' -f2-); do
      np=${carte[$p]:-$root}
      case " $parents " in *" -p $np "*) ;; *) parents="$parents -p $np";; esac
    done
    git -C "$depot" log -1 --format='%B' "$c" > "$tmsg"
    carte[$c]=$(
      GIT_AUTHOR_NAME=$(git -C "$depot" log -1 --format='%an' "$c") \
      GIT_AUTHOR_EMAIL=$(git -C "$depot" log -1 --format='%ae' "$c") \
      GIT_AUTHOR_DATE=$(git -C "$depot" log -1 --format='%aI' "$c") \
      GIT_COMMITTER_NAME=$(git -C "$depot" log -1 --format='%cn' "$c") \
      GIT_COMMITTER_EMAIL=$(git -C "$depot" log -1 --format='%ce' "$c") \
      GIT_COMMITTER_DATE=$(git -C "$depot" log -1 --format='%cI' "$c") \
      git -C "$depot" commit-tree "$c^{tree}" $parents -F "$tmsg"
    )
  done
  tip=${carte[$(git -C "$depot" rev-parse main)]}
  git -C "$depot" update-ref "$sortie" "$tip"
  echo "$tip"
}

# ── La seule vérification qui prouve qu'aucun octet n'a été perdu : l'arbre du
# sommet doit être IDENTIQUE avant et après. Un arbre git est un hachage
# récursif de tout le contenu ; s'il coïncide, chaque fichier coïncide.
_verifier() {
  local depot=$1 avant=$2 apres=$3
  local ta tb
  ta=$(git -C "$depot" rev-parse "$avant^{tree}")
  tb=$(git -C "$depot" rev-parse "$apres^{tree}")
  if [[ "$ta" != "$tb" ]]; then
    echo "[!] ARBRE DIFFÉRENT ($ta != $tb) — ne rien pousser." >&2
    return 1
  fi
  echo "✓ Arbre du sommet identique ($ta) : aucun fichier n'a changé."
}

_coupure() {
  git -C "$1" log --format='%H' --grep="$MOTIF" main \
    | sed -n "$((FENETRE + 1))p"
}

case "$MODE" in

mesurer)
  TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
  echo "→ Clone de mesure dans $TMP (aucune écriture dans $RACINE)…"
  git clone --quiet --mirror --no-hardlinks "$RACINE" "$TMP/m.git"
  git -C "$TMP/m.git" -c pack.threads=4 gc --prune=now --quiet
  AVANT=$(du -sm "$TMP/m.git" | cut -f1)
  NB=$(git -C "$TMP/m.git" log --format='%H' --grep="$MOTIF" main | wc -l)
  echo "   commits de données : $NB — fenêtre demandée : $FENETRE"
  echo "   dépôt, historique complet, après repack : ${AVANT} Mo"

  CUT=$(_coupure "$TMP/m.git" || true)
  if [[ -z "$CUT" ]]; then
    echo "✓ Fenêtre NON contraignante ($NB ≤ $FENETRE) : rien à borner."
    echo "  Aucune réécriture d'historique n'est justifiée aujourd'hui."
    exit 0
  fi
  echo "   coupure : $(git -C "$TMP/m.git" rev-parse --short "$CUT")"
  NEW=$(_rejouer "$TMP/m.git" "$CUT" refs/heads/borne)
  _verifier "$TMP/m.git" main "$NEW"
  # Toutes les autres refs doivent tomber, sinon elles ré-épinglent l'ancien
  # historique et le gain mesuré serait faux (piège n° 3).
  git -C "$TMP/m.git" for-each-ref --format='%(refname)' \
    | grep -v '^refs/heads/borne$' | xargs -r -n1 git -C "$TMP/m.git" update-ref -d
  git -C "$TMP/m.git" reflog expire --all --expire=now
  git -C "$TMP/m.git" -c pack.threads=4 gc --prune=now --quiet
  APRES=$(du -sm "$TMP/m.git" | cut -f1)
  echo "   dépôt, historique borné à $FENETRE, après repack : ${APRES} Mo"
  echo "→ GAIN RÉEL : $((AVANT - APRES)) Mo ($(( (AVANT - APRES) * 100 / AVANT )) %)"
  echo "  (à ne pas confondre avec la somme des coûts par run, qui surestime :"
  echo "   au 28/08/2026, 506 Mo de packs isolés pour 254 Mo réellement ajoutés"
  echo "   au dépôt, soit un facteur 2,0 — voir l'en-tête de ce script.)"
  ;;

preparer)
  if [[ -n "$(git status --porcelain)" ]]; then
    echo "[!] Arbre de travail non propre. Refus." >&2; exit 1
  fi
  if [[ "$(git rev-parse --abbrev-ref HEAD)" != "main" ]]; then
    echo "[!] À exécuter depuis main. Refus." >&2; exit 1
  fi
  git fetch --quiet origin
  if [[ "$(git rev-parse main)" != "$(git rev-parse origin/main)" ]]; then
    echo "[!] main et origin/main divergent. Synchroniser d'abord. Refus." >&2; exit 1
  fi

  CUT=$(_coupure "$RACINE" || true)
  if [[ -z "$CUT" ]]; then
    echo "✓ Fenêtre non contraignante : rien à préparer."; exit 0
  fi

  TAG="archive/pre-borne-$(date +%Y%m%d%H%M)"
  git tag "$TAG" main
  NEW=$(_rejouer "$RACINE" "$CUT" refs/heads/main-borne)
  _verifier "$RACINE" main "$NEW"

  cat <<FIN

Préparé, RIEN n'a été poussé et « main » est intacte.

  sauvegarde locale  : $TAG  (= l'ancien main, à ne PAS pousser sur le même
                       dépôt : le tag garderait tout l'historique atteignable
                       et le gain serait nul)
  branche réécrite   : main-borne ($NEW)

CE TEXTE SE SAUTE. La répétition du 28/08/2026 (#569) l'a montré : les sept
étapes déroulées à la main, et une oubliée — la suppression du tag
\`amendements-figes-v1\`, qui ré-épinglait 386 commits. Pour le dérouler sans
en sauter, et en garder trace :

  scripts/executer_bornage_guide.sh --fenetre $FENETRE

Le runner impose l'ordre, refuse d'avancer sur une précondition en échec,
fait TAPER UNE PHRASE avant chaque geste irréversible, et tient un journal
(#576). Ce script-ci ne pousse toujours JAMAIS : c'est le runner qui porte les
gestes irréversibles, et cette frontière est un test.

À faire à la main si l'on n'utilise pas le runner, dans cet ordre — chaque
étape est un point de non-retour de plus :

  1. Vérifier qu'aucun run de données n'est en cours ni programmé :
       gh run list --workflow=generate-data.yml --limit 5
     Un push forcé qui croise un run fait committer ce run sur un historique
     qui n'existe plus.

  2. Archiver l'ancien historique AILLEURS, sinon les SHA cités dans
     docs/technical_decisions.md et dans les issues cessent de résoudre.
     Archive de référence : Software Heritage (#551, question 4), gratuit,
     public, sans plafond de taille annoncé, et où le SHA git EST
     l'identifiant — une citation y reste vérifiable par un tiers.

     a. Déclencher l'archivage (« Save Code Now ») :
          https://archive.softwareheritage.org/save/
        Ils archivent ce qui est atteignable AU MOMENT du passage : après la
        coupure, c'est perdu. Cet ordre n'est pas négociable.

     b. VÉRIFIER que les SHA cités résolvent — sans quoi l'archivage est un
        rituel (#551, question 4). Une commande, et non plus un geste (#568) :

          python3 src/verifier_archivage_swh.py --fenetre $FENETRE

        \`--fenetre\` N'EST PAS FACULTATIF ICI (#575). Sans elle, la commande
        vérifie TOUS les SHA cités au lieu des seuls que cette coupure
        perdrait : c'est un audit d'archive, pas un feu vert de coupure, et
        elle bloquerait presque à chaque fois — Software Heritage repasse tous
        les ~11 jours, donc tout commit fusionné depuis sa dernière visite
        paraît « manquant » sans rien risquer. Mesuré le 28/08/2026 sur le banc
        de #569, fenêtre 5 : 38 SHA cités, 28 perdus par la coupure et 10
        conservés — et un blocage sur un des 10 conservés.
        (\`--coupure <commit>\` si l'on préfère nommer le point rendu par
        l'étape 3 plutôt que le redériver d'une fenêtre.)

        Il extrait les SHA cités dans les .md suivis et les corps d'issues,
        ne garde que ceux qui résolvent en commit, restreint le périmètre aux
        ANCÊTRES de la coupure, les interroge un par un et NOMME les manquants
        avec l'endroit où chacun est cité. Il temporise sur le quota anonyme
        (120 requêtes/heure) en le disant. Et il interroge l'origine du dépôt
        SOUS LA MAIN — dérivée de \`git remote get-url origin\`, plus une valeur
        codée en dur : lancé sur un banc, il rendait jusqu'ici un verdict
        confiant sur l'archive du dépôt réel.

        Trois verdicts, à ne pas confondre — c'est tout son intérêt :
          VÉRIFIÉ (0)     visite \`full\`, tout résout. La coupure peut suivre.
          MANQUANTS (1)   vrai trou d'archive : des SHA atteignables depuis
                          une ref de l'origine n'y sont pas. Relancer 2a,
                          puis revérifier.
          INDÉTERMINÉ (2) visite non conclue, quota épuisé, ou réseau : on n'a
                          RIEN établi. Réessayer. Une visite en cours n'est
                          PAS un échec d'archivage, et la traiter comme tel
                          ferait renoncer à une coupure légitime.

        Il signale à part les « citations orphelines » : des SHA atteignables
        depuis aucune ref de l'origine, venus d'une branche de PR récrite.
        L'origine ne les a jamais servis, donc SWH n'a jamais pu les voir,
        et relancer 2a n'y changera rien. Ils sont déjà irrésolvables pour
        un tiers : la coupure ne leur fait rien perdre, c'est la citation
        qu'il faut corriger.

        Et à part également les CONSERVÉS PAR LA COUPURE : cités, non ancêtres
        du point de coupure, donc non interrogés — après l'opération le dépôt
        en reste la copie de référence. À ne pas lire comme « pas besoin
        d'archive » : ils tomberont sous une coupure FUTURE, et l'archive les
        couvrira d'ici là. C'est « pas pour cette coupure-ci ».

        \`--sans-issues\` si \`gh\` n'est pas authentifié ; \`--json <fichier>\`
        pour garder trace de ce qui a été constaté ce jour-là.

     c. Facultatif, pour le confort — un miroir local ADDITIF, qui rend une
        récupération immédiate là où le vault de SWH demande une cuisson :
          git push /chemin/vers/archive.git $TAG
        JAMAIS \`git remote update\` ni \`--prune\` dessus : un miroir qui se
        synchronise supprime exactement ce qu'on lui demandait de garder.
        Ce miroir n'est pas la sauvegarde — SWH l'est, et il survit au
        matériel. C'est un raccourci, pas une sécurité.

  3. Pousser la branche bornée :
       git push --force-with-lease origin main-borne:main

  4. Supprimer ou réécrire TOUTE autre branche distante, sinon elle
     ré-épingle l'ancien historique et le gain est nul :
       git ls-remote --heads origin

  5. Prévenir : tout clone existant doit être refait. Un « git pull » sur un
     clone existant recrée l'ancien historique et peut le repousser.

Retour en arrière — possible tant que l'étape 4 n'a pas été faite ET que
GitHub n'a pas ramassé les objets :
       git push --force origin $TAG^{commit}:main
Au-delà, le retour dépend d'un clone tiers encore à jour.
FIN
  ;;
esac
