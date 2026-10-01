"""Les mots que ce projet s'est donnés ne paraissent pas dans l'interface.

« LIGNÉE » EST DE NOUS (fermé le 01/10/2026 par la propriétaire). Le concept —
l'histoire d'un groupe parlementaire qui change de nom d'une législature à
l'autre — est parfaitement connu ; c'est la TERMINOLOGIE qui est une invention
de ce dépôt, et une invention de ce dépôt n'a pas à être lue par le public.

Le mot avait été publié à huit endroits : le titre et trois passages de
`/methodologie`, la pastille « nouveau dans la … », le critère et l'état vide de
la fiche de groupe, et son renvoi vers la méthodologie.

CE QUI RESTE AUTORISÉ, et c'est volontaire : `lignee` sans accent — identifiants
(`lignee-AN-SOC`), noms de fichiers, de fonctions, de champs et d'ancres. Le
lecteur ne les voit pas, et les renommer serait un autre chantier. La garde ne
porte donc que sur la forme ACCENTUÉE, celle qui ne vit que dans du texte français.
"""
from __future__ import annotations

import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "web" / "UI_finale" / "src"

# « surlignée » contient la séquence sans être le mot : la lettre qui précède
# l'exclut. Même chose pour « alignée », « souligne »…
MOT = re.compile(r"(?<![a-zà-ÿ])lign[ée]es?(?![a-zà-ÿ])", re.IGNORECASE)


def _sans_commentaires(source: str) -> str:
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"(?<!:)//[^\n]*", "", source)


def test_le_mot_ligne_e_ne_parait_nulle_part_dans_l_interface() -> None:
    fautifs = []
    for fichier in sorted(SRC.rglob("*.js*")):
        for numero, ligne in enumerate(_sans_commentaires(fichier.read_text(encoding="utf-8")).split("\n"), 1):
            for trouve in MOT.finditer(ligne):
                if "é" in trouve.group(0) or "É" in trouve.group(0):
                    fautifs.append(f"{fichier.relative_to(SRC)}:{numero} — {ligne.strip()[:90]}")
    assert not fautifs, (
        "« lignée » est un mot de ce dépôt, pas un mot du lecteur :\n  " + "\n  ".join(fautifs)
    )
