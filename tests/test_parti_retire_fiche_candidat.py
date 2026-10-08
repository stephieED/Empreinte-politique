"""Le parti d'un candidat n'est plus publié par l'interface (07/10/2026).

Décision de la propriétaire : le parti vient de `raw_data/candidats.json`, rempli
depuis le tableau Wikipédia des candidatures et jamais relu (#757, #1251). Il
sortait à quatre endroits : la ligne sous le nom, la version sans JavaScript, la
description de la page et les données structurées. Le groupe parlementaire,
sourcé, reste.

CE QUE CES TESTS NE COUVRENT PAS : ils lisent le code source, ils ne rendent pas
la fiche. Les trois scripts de construction ont leurs propres tests, qui les
exécutent (`test_bloc_sans_js_969`, `test_titres_par_page_969`,
`test_donnees_structurees_1008`).
"""
from __future__ import annotations

import re
from pathlib import Path

UI = Path(__file__).resolve().parent.parent / "web" / "UI_finale"


def _sans_commentaires(source: str) -> str:
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.S)
    return re.sub(r"^\s*//.*$", "", source, flags=re.M)


def test_la_fiche_ne_lit_plus_le_parti() -> None:
    fiche = _sans_commentaires((UI / "src" / "components" / "CandidateProfile.jsx").read_text(encoding="utf-8"))
    assert "c.parti" not in fiche


def test_le_manifeste_et_la_vue_ne_le_transportent_plus() -> None:
    for chemin in ("scripts/sync-data.mjs", "src/data/index.js"):
        source = _sans_commentaires((UI / chemin).read_text(encoding="utf-8"))
        assert "parti: c.parti" not in source, chemin
    vue = _sans_commentaires((UI / "src" / "data" / "pivotAdapter.js").read_text(encoding="utf-8"))
    assert not re.search(r"^\s*parti:", vue, flags=re.M), "la vue du candidat ne rend plus de champ `parti`"


def test_un_libelle_de_groupe_egal_au_parti_n_est_pas_affiche() -> None:
    """`pivot.groupe` recopie le parti quand la personne n'a pas de groupe.

    Mesuré le 07/10/2026 sur 13 des 35 profils de candidats : sans cette règle,
    la fiche écrirait « Groupe Lutte Ouvrière (LO) » et le parti resterait
    publié sous un autre nom.
    """
    vue = _sans_commentaires((UI / "src" / "data" / "pivotAdapter.js").read_text(encoding="utf-8"))
    assert "groupe: memeLibelle(pivot.groupe, pivot.parti) ? ''" in vue
