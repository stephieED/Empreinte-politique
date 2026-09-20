#!/usr/bin/env python3
"""
generer_index_decisions.py — Produit `docs/technical_decisions.md` depuis les
fichiers de `docs/decisions/` (#840).

Pourquoi cet index est généré
-----------------------------
Il était maintenu à la main, et **tous les lots y écrivaient au même endroit** :
une ligne insérée en tête, à chaque décision. Deux branches parallèles
conflictaient donc systématiquement — quatre rebases en une heure le 10/09/2026,
sur des lots qui ne se recouvraient pas.

Chaque lot n'écrit plus que **son propre fichier de décision**, que personne
d'autre ne touche. Le conflit devient structurellement impossible ; il n'est
plus seulement rare.

Ce que chaque décision doit porter
----------------------------------
    # Le titre de la décision (#issue)

    `2026-09-10`

    <a id="ancienne-ancre"></a><a id="autre-ancre"></a>   (facultatif)

    > **En bref** — le résumé qui devient la ligne d'index.

- Le **titre** est le `#` de niveau 1.
- La **date** est la ligne suivante, entre accents graves. `en continu` pour une
  décision permanente.
- Les **alias** sont de vraies ancres HTML, et ne servent qu'aux décisions dont
  une ancre historique diffère du nom de fichier : des centaines de liens `technical_decisions.md#<ancre>`
  existent hors du dépôt, dans des commentaires d'issues non réécrivables. Une
  ancre ne se renomme ni ne se supprime.
- Le **résumé** est la citation `> **En bref** — …`, sur une seule ligne. C'est
  lui qui devient la ligne d'index, et il est lu **aussi** par qui ouvre le
  fichier : la lecture chronologique du projet a de la valeur en soi.

Usage
-----
    python3 scripts/generer_index_decisions.py            # écrit l'index
    python3 scripts/generer_index_decisions.py --verifier # ne rien écrire, sortie 1 si dérive
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
DOSSIER = RACINE / "docs" / "decisions"
INDEX = RACINE / "docs" / "technical_decisions.md"

SEPARATEUR = "\n---\n\n"

RE_TITRE = re.compile(r"^#\s+(.+?)\s*$", re.M)
#: Le suffixe de date que porte le titre de 230 décisions — `(2026-08-29)`,
#: `— 10/09/2026`, `, 06/09/2026`. Il double la ligne de date placée juste en
#: dessous, et l'index ne l'a jamais repris. Retiré à la composition, jamais
#: dans le fichier : le titre reste ce que son auteur a écrit.
RE_DATE_EN_SUFFIXE = re.compile(
    r"\s*(?:\(\d{4}-\d{2}-\d{2}\)|[—,]\s*\d{1,2}/\d{1,2}/\d{4}|—\s*\d{4}-\d{2}-\d{2})"
    r"(?=\s*(?:\([^)]*#[^)]*\))?\s*$)"
)


def titre_d_index(titre_h1: str) -> str:
    """Le titre tel que l'index le porte : sans le suffixe de date."""
    return RE_DATE_EN_SUFFIXE.sub("", titre_h1).strip()
RE_DATE = re.compile(r"^`([^`]+)`\s*$", re.M)
RE_ANCRE = re.compile(r'<a id="([^"]+)"></a>')
RE_RESUME = re.compile(r"^>\s*\*\*En bref\*\*\s*—\s*(.+?)\s*$", re.M)


class DecisionIncomplete(ValueError):
    """Une décision à qui il manque de quoi produire sa ligne d'index."""


def lire_decision(chemin: Path) -> dict[str, object]:
    """Les métadonnées d'index d'une décision. Lève si l'une manque.

    Refuser plutôt que de produire une ligne partielle : un index qui perd
    silencieusement le résumé d'une décision est exactement ce que ce lot
    remplace.
    """
    contenu = chemin.read_text(encoding="utf-8")
    tete = contenu[: contenu.find("\n## ") if "\n## " in contenu else len(contenu)]

    m_titre = RE_TITRE.search(contenu)
    if not m_titre:
        raise DecisionIncomplete(f"{chemin.name} : pas de titre de niveau 1.")
    m_date = RE_DATE.search(tete)
    if not m_date:
        raise DecisionIncomplete(
            f"{chemin.name} : pas de date. Attendu une ligne `AAAA-MM-JJ` "
            "sous le titre."
        )
    m_resume = RE_RESUME.search(tete)
    if not m_resume:
        raise DecisionIncomplete(
            f"{chemin.name} : pas de résumé. Attendu une ligne "
            "`> **En bref** — …` sous la date."
        )
    # Les alias sont de VRAIES ancres dans le fichier, pas une déclaration à
    # part : un lien `decisions/<nom>.md#<alias>` doit atterrir quelque part.
    alias = list(dict.fromkeys(
        a for a in RE_ANCRE.findall(tete) if a != chemin.stem
    ))
    return {
        "fichier": chemin.name,
        # Le nom de fichier d'abord — c'est l'ancre canonique — puis les
        # alias historiques, dans l'ordre où l'index les portait.
        "ancres": [chemin.stem] + alias,
        "date": m_date.group(1),
        "titre": titre_d_index(m_titre.group(1)),
        "resume": m_resume.group(1),
    }


def _cle_de_tri(d: dict[str, object]) -> tuple:
    """Antéchronologique. `en continu` n'est pas une date : elle ferme la liste."""
    date = str(d["date"])
    # Rang 1 pour une vraie date, 0 sinon : après `reverse=True`, les dates
    # sortent en tête, de la plus récente à la plus ancienne, et `en continu`
    # ferme la liste — la place qu'elle occupe dans l'index depuis l'origine.
    return (1 if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date) else 0, date)


def composer(decisions: list[dict[str, object]]) -> str:
    lignes = []
    for d in sorted(decisions, key=_cle_de_tri, reverse=True):
        ancres = "".join(f'<a id="{a}"></a>' for a in d["ancres"])
        lignes.append(
            f"- `{d['date']}` {ancres}[{d['titre']}](decisions/{d['fichier']}) — {d['resume']}"
        )
    return "\n".join(lignes) + "\n"


def entete() -> str:
    """L'en-tête, conservé tel quel : il explique la manœuvre à qui écrit."""
    return INDEX.read_text(encoding="utf-8").split(SEPARATEUR)[0] + SEPARATEUR


def generer() -> str:
    erreurs: list[str] = []
    decisions = []
    for chemin in sorted(DOSSIER.glob("*.md")):
        try:
            decisions.append(lire_decision(chemin))
        except DecisionIncomplete as exc:
            erreurs.append(str(exc))
    if erreurs:
        raise DecisionIncomplete("\n".join(erreurs))
    return entete() + composer(decisions)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verifier", action="store_true",
                        help="ne rien écrire ; sortie 1 si l'index a dérivé")
    args = parser.parse_args(argv)

    try:
        attendu = generer()
    except DecisionIncomplete as exc:
        print(f"[!] index non généré :\n{exc}", file=sys.stderr)
        return 2

    if args.verifier:
        if INDEX.read_text(encoding="utf-8") == attendu:
            print(f"{INDEX.relative_to(RACINE)} est à jour.")
            return 0
        print(f"[!] {INDEX.relative_to(RACINE)} a dérivé. "
              "Relancer sans --verifier.", file=sys.stderr)
        return 1

    INDEX.write_text(attendu, encoding="utf-8")
    print(f"{INDEX.relative_to(RACINE)} écrit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
