"""Aucun lien publié ne déclenche un téléchargement (#330, relevé du 20/09/2026).

L'Assemblée nationale publie les comptes rendus de séance et l'annuaire des
acteurs sous forme d'ARCHIVES : trois `syseron.xml.zip`, un par législature, et
`AMO30_…zip`. Ces adresses sont ce que `source_url` porte sur la plupart des
entrées, et la fiche candidat en faisait un badge « Source » par intervention.

Mesuré avant correction : **27 007 des 33 823 interventions** des 32 candidats
déclarés y menaient, et un clic lançait le téléchargement de 100 Mo — pour trois
fichiers distincts, répétés vingt-sept mille fois.

La règle : un lien par ligne ne subsiste que s'il mène à un DOCUMENT ; l'archive
est nommée une fois par section, et les légendes qui doivent rester des liens
mènent à la PAGE du jeu de données.

CE QUE CES GARDES NE COUVRENT PAS : elles lisent la source, elles ne rendent
aucun composant. L'absence de lien `.zip` a été vérifiée en navigateur sur six
pages — /sources, /couverture, /methodologie, une fiche de gouvernement, une
fiche candidat et une fiche de lignée.
"""

from __future__ import annotations

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SRC = RACINE / "web" / "UI_finale" / "src"
LECTURE = SRC / "utils" / "lecture.js"


def test_la_regle_vit_dans_utils_lecture():
    source = LECTURE.read_text(encoding="utf-8")
    for symbole in (
        "export function estArchiveTelechargeable",
        "export function lienDocumentaire",
        "export function pageDuJeuDeDonnees",
        "PAGE_JEU_DE_DONNEES_DEBATS",
        "PAGE_JEU_DE_DONNEES_ACTEURS",
    ):
        assert symbole in source, f"{symbole} a disparu"


def test_les_pages_du_jeu_de_donnees_ne_sont_pas_des_fichiers():
    source = LECTURE.read_text(encoding="utf-8")
    for constante in ("PAGE_JEU_DE_DONNEES_DEBATS", "PAGE_JEU_DE_DONNEES_ACTEURS"):
        url = re.search(rf"{constante} = '([^']+)'", source).group(1)
        assert url.startswith("https://data.assemblee-nationale.fr/"), url
        assert not url.endswith(".zip"), f"{constante} doit être une page, pas une archive"


def test_aucun_composant_ne_lie_une_url_de_source_sans_la_filtrer():
    """Un `href={…sourceUrl}` non filtré republierait l'archive."""
    fautifs = []
    for fichier in SRC.rglob("*.jsx"):
        texte = fichier.read_text(encoding="utf-8")
        for ligne in re.findall(r"href=\{[^}]*[Ss]ourceUrl[^}]*\}", texte):
            if "lienDocumentaire" in ligne or "pageDuJeuDeDonnees" in ligne:
                continue
            # Les dossiers et scrutins portent une URL de page, jamais d'archive.
            if "dossier" in ligne.lower() or "scrutin" in ligne.lower():
                continue
            fautifs.append(f"{fichier.name} :: {ligne}")
    assert not fautifs, (
        "ces liens publient l'adresse brute d'une source, qui peut être une archive :\n  "
        + "\n  ".join(fautifs)
    )
