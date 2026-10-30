"""Les bulles de la fiche de législature (#1314, 23/10/2026).

Écrites ou reprises mot pour mot par la propriétaire, rendues dans leur bulle
sur la fiche avant d'être codées. Elles sont recopiées ici : une reformulation
« pour améliorer » doit échouer.
"""
from pathlib import Path

FICHE = Path(__file__).resolve().parents[1] / "web" / "UI_finale" / "src" / "components" / "LegislatureProfile.jsx"

TEXTES = [
    "La législature en quelques faits.",
    "Note : Chiffres arrêtés au dernier jour de la législature. Sont comptées les lois votées par l’Assemblée de cette législature, puis promulguées.",
    "Note : Chiffres arrêtés à la date de la dernière mise à jour des données. Sont comptées les lois votées par l’Assemblée de cette législature, puis promulguées.",
    "Les groupes de l’Assemblée et leur position : majoritaire, minoritaire ou d’opposition.",
    "Note : Situation au dernier jour de la législature.",
    "Note : Situation à la date de la dernière mise à jour des données. L’Assemblée ne publie pas les positions pour la législature en cours.",
    # « À l'ordre du jour » (#1354), validée le 26/10/2026.
    "Les sujets discutés en séance publique, jour par jour.",
    "Note : Un jour sans barre n’a pas eu de séance publique. En pointillé, l’ordre du jour n’est pas encore fixé.",
    "Note : Un jour sans barre n’a pas eu de séance publique.",
    "Les textes votés par l’Assemblée pendant la législature, selon leur auteur, leur commission et leur sort.",
    "Note : Un texte adopté n’est pas forcément devenu une loi. Une résolution, par exemple, ne le devient jamais.",
    "Les textes confiés à chaque commission pendant la législature, et leur avancée.",
    "Note : Un texte jamais examiné n’a pas été rejeté. Il n’a jamais été mis à l’ordre du jour. Le nuage reprend les mots les plus fréquents dans les titres des textes.",
    "Les limites de cette fiche : ce que les sources ne disent pas sur cette législature.",
    "Note : Une information absente n’a pas été trouvée dans les sources. Elle a pu exister quand même.",
]


def test_les_bulles_sont_celles_validees() -> None:
    source = FICHE.read_text(encoding="utf-8")
    manquantes = [t for t in TEXTES if t not in source]
    assert not manquantes, "bulle reformulée ou retirée :\n" + "\n".join(manquantes)


def test_chaque_section_porte_sa_bulle() -> None:
    source = FICHE.read_text(encoding="utf-8")
    for cle in ("enBref", "sieges", "ordreDuJour", "textes", "commissions", "limites"):
        assert f"bulle={{BULLES.{cle}(" in source, f"la section « {cle} » n'a plus sa bulle"
