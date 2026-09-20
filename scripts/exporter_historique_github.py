#!/usr/bin/env python3
"""Exporte les issues et pull requests GitHub en fichiers Markdown versionnés.

**Pourquoi ce script existe.** La mémoire de ce projet vit dans des fichiers —
330 décisions sous `docs/decisions/`. Les issues sont le dernier endroit où
elle ne vivait pas : un arbitrage rendu dans un commentaire n'existe nulle part
ailleurs, et il disparaît avec le dépôt qui le porte.

**Les dates sont tronquées au JOUR.** C'est la convention du projet : les 330
décisions sont datées `2026-09-18`, jamais à l'heure. La chronologie porte le
sens, l'heure n'en porte aucun.

Usage :
    python3 scripts/exporter_historique_github.py --depot stephieED/X --out docs/historique
    python3 scripts/exporter_historique_github.py --numero 997      # un seul, pour voir
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any, Optional

#: Repérés pour être SIGNALÉS, jamais retirés en silence : une heure citée dans
#: le texte d'une issue est du contenu rédigé, pas une métadonnée.
MOTIF_HEURE = re.compile(r"\b\d{1,2} ?h ?\d{2}\b|\b\d{1,2}:\d{2}\b|\b\d{1,2} ?h\b")


def _gh(chemin: str) -> Any:
    sortie = subprocess.run(
        ["gh", "api", chemin, "--paginate"], capture_output=True, text=True)
    if sortie.returncode != 0:
        raise RuntimeError(f"gh api {chemin} : {sortie.stderr.strip()[:200]}")
    texte = sortie.stdout.strip()
    if not texte:
        return []
    # `--paginate` concatène des tableaux JSON : `][` entre deux pages.
    return json.loads(texte.replace("][", ","))


def _jour(horodatage: Optional[str]) -> str:
    """`2026-09-18T15:29:47Z` → `2026-09-18`. L'heure ne sort jamais d'ici."""
    return (horodatage or "")[:10]


def _slug(titre: str, longueur: int = 60) -> str:
    sans_accent = unicodedata.normalize("NFKD", titre or "")
    sans_accent = "".join(c for c in sans_accent if not unicodedata.combining(c))
    mots = re.sub(r"[^a-zA-Z0-9]+", "-", sans_accent).strip("-").lower()
    return mots[:longueur].rstrip("-") or "sans-titre"


def rendre(objet: dict[str, Any], commentaires: list[dict[str, Any]]) -> str:
    est_pr = "pull_request" in objet
    etat = objet.get("state")
    if est_pr and objet.get("pull_request", {}).get("merged_at"):
        ligne_etat = f"fusionnée le {_jour(objet['pull_request']['merged_at'])}"
    elif etat == "closed":
        ligne_etat = f"fermée le {_jour(objet.get('closed_at'))}"
    else:
        ligne_etat = "ouverte"

    labels = ", ".join(l["name"] for l in objet.get("labels") or []) or "—"
    lignes = [
        f"# #{objet['number']} — {objet.get('title') or ''}",
        "",
        f"- **Type** : {'pull request' if est_pr else 'issue'}",
        f"- **État** : {ligne_etat}",
        f"- **Ouverte le** : {_jour(objet.get('created_at'))}",
        f"- **Auteur** : {(objet.get('user') or {}).get('login', '—')}",
        f"- **Labels** : {labels}",
        "",
        (objet.get("body") or "_Sans description._").strip(),
    ]
    for c in commentaires:
        lignes += [
            "",
            "---",
            "",
            f"## Commentaire — {_jour(c.get('created_at'))}, "
            f"{(c.get('user') or {}).get('login', '—')}",
            "",
            (c.get("body") or "").strip(),
        ]
    return "\n".join(lignes).rstrip() + "\n"


def exporter(depot: str, sortie: Path, numeros: Optional[list[int]] = None) -> dict[str, Any]:
    sortie.mkdir(parents=True, exist_ok=True)
    if numeros:
        objets = [_gh(f"repos/{depot}/issues/{n}") for n in numeros]
    else:
        objets = _gh(f"repos/{depot}/issues?state=all&per_page=100")
    rapport = {"ecrits": 0, "heures_en_clair": []}
    for objet in objets:
        if not isinstance(objet, dict) or "number" not in objet:
            continue
        commentaires = _gh(f"repos/{depot}/issues/{objet['number']}/comments?per_page=100") \
            if objet.get("comments") else []
        texte = rendre(objet, commentaires if isinstance(commentaires, list) else [])
        chemin = sortie / f"{objet['number']:04d}-{_slug(objet.get('title') or '')}.md"
        chemin.write_text(texte, encoding="utf-8")
        rapport["ecrits"] += 1
        for trouve in MOTIF_HEURE.findall(texte):
            rapport["heures_en_clair"].append((objet["number"], trouve))
    return rapport


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--depot", default="stephieED/Empreinte-politique-src")
    parser.add_argument("--out", type=Path, default=Path("docs/historique"))
    parser.add_argument("--numero", type=int, action="append",
                        help="n'exporte que ces numéros — pour voir le rendu avant le lot")
    args = parser.parse_args(argv)

    rapport = exporter(args.depot, args.out, args.numero)
    print(f"{rapport['ecrits']} fichier(s) écrits dans {args.out}")
    if rapport["heures_en_clair"]:
        print(f"\n[!] {len(rapport['heures_en_clair'])} heure(s) citée(s) DANS LE TEXTE — "
              "à relire avant publication :")
        for numero, extrait in rapport["heures_en_clair"][:40]:
            print(f"    #{numero} : {extrait}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
