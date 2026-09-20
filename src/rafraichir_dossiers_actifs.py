#!/usr/bin/env python3
"""rafraichir_dossiers_actifs.py — Reprend les archives de dossiers encore vivantes (#762).

POURQUOI CE SCRIPT. `.cache/dossiers_an` est mis en cache en CI sous une clé
HEBDOMADAIRE doublée d'un `restore-keys` de préfixe. Au changement de semaine,
la clé exacte manque, le préfixe restaure le répertoire de la semaine
précédente, et `ensure_dossiers_zip_downloaded` — qui court-circuite sur
`zip_path.is_file()` — ne retélécharge rien. Le répertoire inchangé est ensuite
resauvegardé sous la clé neuve : **la rotation se désamorce elle-même**. C'est
la forme de #749, appliquée aux dossiers.

Le workflow appelle donc ce script quand la clé exacte de la semaine n'a PAS
été touchée (`cache-hit != 'true'`), et seulement là : dans la semaine, le
cache est légitime et rien n'est repris.

CE QU'IL NE FAIT PAS : reprendre les législatures dissoutes. Elles ne
produisent plus d'acte, et les retélécharger coûterait 23 Mo par semaine pour
un contenu identique. La liste des vivantes est dérivée dans
`couverture_dossiers.AN_DOSSIERS_LEGISLATURES_ACTIVES`.

Cinq consommateurs dérivent de ces archives : `commissions_dossiers.json`,
le `statut` des textes de gouvernement (#184), `scrutins_dossiers.json` (#758),
`textes_dossiers_an.py` et `candidate_profile.py`.

Usage :
    python3 src/rafraichir_dossiers_actifs.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from couverture_dossiers import (  # noqa: E402
    AN_DOSSIERS_LEGISLATURES_ACTIVES,
    AN_DOSSIERS_LEGISLATURES_FIGEES,
)
from gouvernement_textes import rafraichir_dossiers_actifs  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    del argv  # aucun argument : le script fait une chose
    attendues = sorted(AN_DOSSIERS_LEGISLATURES_ACTIVES)
    figees = sorted(AN_DOSSIERS_LEGISLATURES_FIGEES)
    print(f"-> Reprise des archives de dossiers encore vivantes : {attendues}")
    print(f"   (législatures figées, jamais reprises : {figees})")

    reprises = rafraichir_dossiers_actifs()

    manquantes = [leg for leg in attendues if leg not in reprises]
    if reprises:
        print(f"  ✓ {len(reprises)} archive(s) reprise(s) : {reprises}")
    if manquantes:
        # Non bloquant : la donnée déjà en cache reste exploitable, et un
        # rafraîchissement raté ne doit pas coûter le run (§2 règle 5 — on
        # nomme l'absence au lieu de la taire).
        print(
            f"  [!] {len(manquantes)} archive(s) non reprise(s) : {manquantes}. "
            "Le run continue sur la version en cache, qui peut être périmée."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
