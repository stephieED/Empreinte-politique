"""Le bouton « Partager cette fiche » (#1033).

Arbitré sur maquette entre sept formes : la forme E, le 21/10/2026, une pastille
qui flotte en bas à droite des trois fiches. Au téléphone, le menu de partage du
téléphone ; à l'ordinateur, un menu LinkedIn, X, copier le lien.

Ce que ces garde-fous protègent :

1. **Les trois fiches le portent** — candidat, lignée de groupe, gouvernement —,
   et la pastille flotte, sous la rangée collée du haut, sans perdre son
   libellé pour les lecteurs d'écran.
2. **Seule l'adresse est partagée** (§2 règle 1) : aucun texte pré-écrit, qui
   qualifierait la personne ou le groupe.
3. **Rien de LinkedIn ni de X ne s'exécute** : leurs adresses de partage nues,
   sans script.
4. **L'adresse est celle du site publié**, pas celle du navigateur — un partage
   depuis une copie locale ou de prévisualisation enverrait sinon une adresse
   que personne ne peut ouvrir.

CE QU'ILS NE COUVRENT PAS : aucun composant React n'est rendu ici. La pastille a
été jouée sur les trois fiches le 21/10/2026 à 1 280 px — menu ouvert, lien
copié, sans erreur console — et à 390 px sans défilement horizontal. Le menu de
partage du téléphone n'a pas pu être joué : le navigateur de test n'en a pas.
"""

from __future__ import annotations

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
COMPOSANTS = RACINE / "web" / "UI_finale" / "src" / "components"
BOUTON = COMPOSANTS / "PartagerFiche.jsx"


def sans_commentaires(source: str) -> str:
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    source = re.sub(r"\{/\*.*?\*/\}", "", source, flags=re.DOTALL)
    return re.sub(r"(?<!:)//[^\n]*", "", source)


def test_les_trois_fiches_portent_le_bouton() -> None:
    for fiche in ("CandidateProfile.jsx", "LigneeProfile.jsx", "GovernmentProfile.jsx"):
        source = sans_commentaires((COMPOSANTS / fiche).read_text(encoding="utf-8"))
        assert "import PartagerFiche from './PartagerFiche';" in source, fiche
        assert "<PartagerFiche />" in source, f"{fiche} ne porte plus le bouton de partage"


def test_seule_l_adresse_est_partagee() -> None:
    source = sans_commentaires(BOUTON.read_text(encoding="utf-8"))
    assert "navigator.share({ url: adresse })" in source, "le partage du téléphone ne porte que l'adresse"
    assert "text:" not in source and "title:" not in source
    assert "&text=" not in source and "?text=" not in source


def test_rien_de_linkedin_ni_de_x_ne_s_execute() -> None:
    source = sans_commentaires(BOUTON.read_text(encoding="utf-8"))
    assert "<script" not in source and "<iframe" not in source
    assert "linkedin.com/sharing/share-offsite/?url=" in source
    assert "x.com/intent/post?url=" in source


def test_l_adresse_est_celle_du_site_publie() -> None:
    source = sans_commentaires(BOUTON.read_text(encoding="utf-8"))
    assert "export const SITE = 'https://empreinte-politique.fr';" in source
    assert "window.location.href" not in source and "location.origin" not in source


def test_le_telephone_se_reconnait_au_doigt() -> None:
    """Plusieurs navigateurs d'ordinateur exposent `navigator.share` : la
    maquette validée y montre le menu du site, pas celui du système."""
    source = sans_commentaires(BOUTON.read_text(encoding="utf-8"))
    assert "(pointer: coarse)" in source


def test_la_pastille_flotte_et_garde_son_libelle() -> None:
    source = sans_commentaires(BOUTON.read_text(encoding="utf-8"))
    assert 'aria-label="Partager cette fiche"' in source, "l'icône seule doit garder son nom"
    css = (COMPOSANTS / "PartagerFiche.css").read_text(encoding="utf-8")
    assert "position: fixed;" in css
    # Sous la rangée collée du haut (EnTeteSite.css, z-index 5) et son tiroir.
    assert "z-index: 4;" in css
    assert "z-index: 5;" in (COMPOSANTS / "EnTeteSite.css").read_text(encoding="utf-8")
