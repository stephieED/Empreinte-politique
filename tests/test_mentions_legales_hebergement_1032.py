"""L'hébergeur des mentions légales (#1032).

La section « Hébergement » disait « À préciser » : elle datait d'avant le choix
d'un hébergement. Or le site est servi par **GitHub Pages** depuis que
`.github/workflows/deploy-pages.yml` existe — la propriétaire a d'abord nommé
Gandi, qui est le **bureau d'enregistrement du nom de domaine**, pas
l'hébergeur au sens de l'article 6-III de la LCEN.

Ce que ces garde-fous protègent :

1. **L'hébergeur nommé est celui qui sert le site.** Si le déploiement quitte
   GitHub Pages, ce test échoue et la page doit suivre : c'est le seul lien
   mécanique entre le workflow de déploiement et la page légale.
2. **Les adresses ne se réinventent pas.** Celle de GitHub vient de sa
   déclaration de confidentialité, celle de Gandi de l'enregistrement RDAP du
   domaine chez l'AFNIC. Le test vérifie qu'elles sont là, pas qu'elles sont
   vraies — cela se refait à la source le jour où l'une bouge.
"""

from __future__ import annotations

from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
LEGAL = RACINE / "web" / "UI_finale" / "src" / "pages" / "LegalNoticePage.jsx"
DEPLOIEMENT = RACINE / ".github" / "workflows" / "deploy-pages.yml"


def test_l_hebergeur_nomme_est_celui_qui_sert_le_site() -> None:
    """GitHub Pages sert le site : c'est GitHub, Inc. que la page doit nommer."""
    assert DEPLOIEMENT.exists(), "le déploiement Pages est ce qui fonde la mention"
    deploiement = DEPLOIEMENT.read_text(encoding="utf-8")
    assert "actions/deploy-pages" in deploiement or "pages" in deploiement.lower()
    legal = LEGAL.read_text(encoding="utf-8")
    assert "GitHub, Inc." in legal
    assert "GitHub Pages" in legal
    assert "88 Colin P. Kelly Jr. Street" in legal


def test_le_registrar_n_est_pas_presente_comme_l_hebergeur() -> None:
    """Gandi enregistre le domaine ; il n'héberge pas le site."""
    legal = LEGAL.read_text(encoding="utf-8")
    hebergement = legal.split("heading: 'Hébergement'")[1].split("heading:")[0]
    assert "hébergé par" in hebergement
    avant_gandi = hebergement.split("Gandi")[0]
    assert "hébergé par" in avant_gandi, "la phrase d'hébergement précède celle du domaine"
    assert "enregistré auprès de" in hebergement
    assert "63-65 boulevard Masséna" in hebergement


def test_la_section_ne_dit_plus_a_preciser() -> None:
    """Elle l'a dit tant qu'aucun hébergement n'était choisi ; ce n'est plus vrai."""
    hebergement = (
        LEGAL.read_text(encoding="utf-8").split("heading: 'Hébergement'")[1].split("heading:")[0]
    )
    assert "À préciser" not in hebergement
