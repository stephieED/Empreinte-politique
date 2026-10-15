"""Au téléphone, la fiche candidat ne glisse plus de côté (#867).

Mesuré le 15/10/2026 à 360 et 400 px (Playwright, Firefox) : deux textes en
`white-space: nowrap` élargissaient tout le document — les totaux d'une carte
(419 px pour Mélenchon, 440 pour Guedj) et le nom d'une commission longue dans
« Ce qu'il a voté » (365 px). Corrigés, les 31 fiches de candidats tiennent dans
360 px. Ce test tient les deux règles ; il ne remplace pas une mesure du rendu.
"""

from __future__ import annotations

import re
from pathlib import Path

COMPOSANTS = Path(__file__).resolve().parent.parent / "web" / "UI_finale" / "src" / "components"


def _blocs_etroits(css: str) -> str:
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
    blocs = []
    for m in re.finditer(r"@media \(max-width: 720px\) \{", css):
        i, profondeur = m.end(), 1
        while profondeur:
            profondeur += {"{": 1, "}": -1}.get(css[i], 0)
            i += 1
        blocs.append(css[m.end():i])
    return "\n".join(blocs)


def _regle(css: str, selecteur: str) -> str:
    m = re.search(re.escape(selecteur) + r"\s*\{([^}]*)\}", css)
    assert m, f"{selecteur} absent des règles sous 720 px"
    return m.group(1)


def test_les_totaux_d_une_carte_passent_sous_le_titre():
    etroit = _blocs_etroits((COMPOSANTS / "CandidateProfile.css").read_text(encoding="utf-8"))
    assert "minmax(0, 1fr)" in _regle(etroit, ".cp-gouv-tete")
    assert "white-space: normal" in _regle(etroit, ".cp-gouv-periode")


def test_le_nom_d_une_commission_va_a_la_ligne():
    etroit = _blocs_etroits((COMPOSANTS / "VotesParPeriode.css").read_text(encoding="utf-8"))
    assert "white-space: normal" in _regle(etroit, ".vp-nom")


# ---------------------------------------------------------------------------
# Les figures redessinées pour le téléphone (formes arbitrées le 15/10/2026)
# ---------------------------------------------------------------------------

SRC = COMPOSANTS.parent


def _code(chemin: Path) -> str:
    source = chemin.read_text(encoding="utf-8")
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"(?<!:)//[^\n]*", "", source)


def test_le_seuil_des_figures_est_celui_des_feuilles():
    """Une figure et sa mise en page basculent ensemble, à 720 px."""
    assert "(max-width: 720px)" in (SRC / "hooks" / "useLargeur.js").read_text(encoding="utf-8")


def test_la_frise_du_parcours_descend_au_telephone():
    """Forme B : à 360 px, la frise horizontale superposait ses années."""
    code = _code(COMPOSANTS / "CandidateProfile.jsx")
    assert "function FriseVerticale(" in code
    assert "etroit ? <FriseVerticale" in code, "la frise large reste celle de l'ordinateur"
    assert "r.ligne * FV.colonne" in code, "les colonnes reprennent le rangement de la frise large"
    assert ".cp-fv-libelle" in (COMPOSANTS / "CandidateProfile.css").read_text(encoding="utf-8")


def test_les_en_bref_se_redessinent_a_la_largeur_mesuree():
    """Forme A : une unité pour un pixel, au lieu de mille unités réduites au tiers."""
    gouv = _code(COMPOSANTS / "GovernmentProfile.jsx")
    assert "const L = aLaLargeur ? largeur : 1000;" in gouv
    lignee = _code(COMPOSANTS / "LigneeProfile.jsx")
    assert "const L = aLaLargeur ? largeur : LARGEUR;" in lignee
    i = lignee.index("function Frise(")
    corps = lignee[i:lignee.index("function QuiSontIls", i)]
    assert "LARGEUR - " not in corps and "* LARGEUR" not in corps, "plus aucun calcul sur la largeur fixe"


def test_le_titre_d_un_debat_prend_sa_ligne():
    """Forme B : « projet de loi de finances… » ne disait plus l'année."""
    gouv = _blocs_etroits((COMPOSANTS / "GovernmentProfile.css").read_text(encoding="utf-8"))
    assert "grid-column: 1 / -1" in _regle(gouv, ".gvp-mr .gvp-mr-lib")
    assert "display: none" in _regle(gouv, ".gvp-mr--tete > :first-child"), "l'en-tête était décalé d'une colonne"
    lignee = _blocs_etroits((COMPOSANTS / "LigneeProfile.css").read_text(encoding="utf-8"))
    assert "white-space: normal" in _regle(lignee, ".lp-mat .lp-mr-lib")
    assert "display: block" in _regle(lignee, ".lp-mat .lp-mr-rail")
    assert 'className="lp-mat lp-mat--debats"' in (COMPOSANTS / "LigneeProfile.jsx").read_text(encoding="utf-8")


def test_les_amendements_par_matiere_gardent_leur_barre():
    """Forme A : la règle des débats vaut aussi pour le tableau des amendements,
    dont les barres disparaissaient toutes sous 720 px (13 sur 13 chez LR)."""
    jsx = (COMPOSANTS / "LigneeProfile.jsx").read_text(encoding="utf-8")
    assert '<div className="lp-mat">' in jsx, "le tableau des amendements n'est plus un .lp-mat"
    lignee = _blocs_etroits((COMPOSANTS / "LigneeProfile.css").read_text(encoding="utf-8"))
    assert ".lp-mat--debats .lp-mr-rail" not in lignee, "la barre ne doit plus être réservée aux débats"
