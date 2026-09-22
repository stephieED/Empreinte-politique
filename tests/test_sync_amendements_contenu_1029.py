"""Le site ne sert, des amendements, que l'index `<lég>.json` (#1029 voie 2).

Backend ajoute `pivot_data/amendements/<lég>.contenu.json` — l'index de mots des
exposés, 93 Mo pour les quatre législatures. Le filtre de `sync-data`
excluait les seuls `.cosignatures.json` : il aurait recopié ce fichier dans le
site sans qu'aucune vue le lise. La liste se construit désormais par le nom.
"""

from __future__ import annotations

import re
from pathlib import Path

SYNC = Path(__file__).resolve().parent.parent / "web" / "UI_finale" / "scripts" / "sync-data.mjs"


def _motif() -> re.Pattern[str]:
    source = SYNC.read_text(encoding="utf-8")
    m = re.search(r"const INDEX_AMENDEMENTS = /(.+?)/;", source)
    assert m, "la liste des fichiers copiés se construit par un motif nommé"
    assert "INDEX_AMENDEMENTS.test(f)" in source
    return re.compile(m.group(1).replace("\\\\", "\\"))


def test_seul_l_index_par_legislature_est_copie() -> None:
    motif = _motif()
    copies = [f for f in ("14.json", "17.json", "17.cosignatures.json", "17.contenu.json", "17.json.tmp")
              if motif.fullmatch(f)]
    assert copies == ["14.json", "17.json"]
