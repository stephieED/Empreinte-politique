"""Le gris clair n'est jamais une couleur de texte sur un fond clair (22/10/2026).

La propriétaire, devant « Ce qu'on n'a pas pu lire » et le pied de page : « ce
gris très clair ne doit plus être utilisé en couleur de police sur un fond clair
(blanc, gris, etc.) ». `--muted` valait #8b8794, soit 3,25:1 sur le fond, sous
le seuil AA de 4,5:1 ; des titres écrivaient en #b6b1bd, 1,94:1.

Ce que la garde tient : le contraste de `--muted` sur le fond et sur une carte,
et l'absence de ces deux gris comme `color` dans les feuilles de style. Le gris
reste permis en remplissage (la case « abstention », un trait, une barre) : la
garde ne regarde que `color`, et `fill` des textes SVG qui lisent `--muted`.
→ web/UI_finale/DESIGN_SYSTEM.md, table de contraste
"""
from __future__ import annotations

import re
from pathlib import Path

UI = Path(__file__).resolve().parents[1] / "web" / "UI_finale"
SRC = UI / "src"
GRIS_RETIRES = ("#8b8794", "#b6b1bd")


def _luminance(hexa: str) -> float:
    h = hexa.lstrip("#")
    canaux = [int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in canaux]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def _contraste(a: str, b: str) -> float:
    la, lb = _luminance(a), _luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def _jeton(nom: str, css: str) -> str:
    m = re.search(rf"{re.escape(nom)}\s*:\s*(#[0-9a-fA-F]{{6}})\s*;", css)
    assert m, f"{nom} introuvable dans index.css"
    return m.group(1)


def test_le_texte_secondaire_passe_le_seuil_aa() -> None:
    css = (SRC / "index.css").read_text(encoding="utf-8")
    muted = _jeton("--muted", css)
    for fond in (_jeton("--bg", css), _jeton("--card", css)):
        assert _contraste(muted, fond) >= 4.5, f"--muted {muted} sur {fond} : {_contraste(muted, fond):.2f}:1"


def test_aucune_feuille_n_ecrit_en_gris_clair() -> None:
    fautes = []
    motif = re.compile(r"(?<![-\w])(?:color|fill)\s*:\s*(?:var\(--[\w-]+,\s*)?(#[0-9a-fA-F]{6})", re.I)
    for fichier in sorted(SRC.rglob("*.css")):
        texte = re.sub(r"/\*.*?\*/", "", fichier.read_text(encoding="utf-8"), flags=re.S)
        for n, ligne in enumerate(texte.splitlines(), 1):
            for valeur in motif.findall(ligne):
                if valeur.lower() in GRIS_RETIRES and "background" not in ligne:
                    fautes.append(f"{fichier.relative_to(SRC)}:{n} {ligne.strip()}")
    assert not fautes, "gris clair en couleur de texte :\n" + "\n".join(fautes)
