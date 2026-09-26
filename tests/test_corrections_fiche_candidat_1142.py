"""Trois corrections relevées sur la fiche d'Emmanuel Maurel (25/09/2026).

Elles ont une racine commune : **la fiche prêtait à une personne une
institution qu'elle n'a jamais exercée.** Emmanuel Maurel n'a aucun mandat de
catégorie `fonction_gouvernementale` — vérifiable sur son profil pivot — et sa
fiche montrait pourtant « Au gouvernement ».

Ces gardes sont au niveau de la SOURCE, comme les autres garde-fous de la fiche
(`test_pied_de_site_et_section_6_328.py`) : `profilCandidat.js` importe sans
extension, donc node ne le charge pas seul, et monter Vite dans la suite
coûterait plus cher que ce que la garde protège.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
SRC = RACINE / "web" / "UI_finale" / "src"


def _sans_commentaires(texte: str) -> str:
    sans_bloc = re.sub(r"/\*.*?\*/", "", texte, flags=re.S)
    return re.sub(r"^\s*//.*$", "", sans_bloc, flags=re.M)


@pytest.fixture(name="cascade")
def _cascade() -> str:
    return _sans_commentaires((SRC / "components" / "CascadeTextes.jsx").read_text(encoding="utf-8"))


@pytest.fixture(name="profil")
def _profil() -> str:
    return _sans_commentaires((SRC / "utils" / "profilCandidat.js").read_text(encoding="utf-8"))


@pytest.fixture(name="votes")
def _votes() -> str:
    return _sans_commentaires((SRC / "components" / "VotesParPeriode.jsx").read_text(encoding="utf-8"))


def test_la_colonne_suit_l_institution_sourcee_et_non_la_nature(cascade: str) -> None:
    """Un RAPPORTEUR d'un projet de loi n'est pas au gouvernement (#689).

    `estProjetDeLoi` répond à « de quelle nature est ce texte », jamais à « de
    quelle institution relève cette personne sur ce texte ». La colonne lisait
    la première : 18 des 1 098 textes portés des 34 candidats publiés étaient
    rangés à tort, dont les deux lois de finances dont Emmanuel Maurel est
    co-rapporteur.
    """
    assert "t.institution === INSTITUTION_GOUVERNEMENT" in cascade
    assert "t.projetDeLoi" not in cascade, (
        "la colonne est revenue à la nature du texte"
    )


def test_le_texte_de_cascade_porte_l_institution(profil: str) -> None:
    """Le commentaire disait `role`, le code lisait la nature : ils divergeaient."""
    assert "institution: institutionDuTexte(t)" in profil, (
        "les textes de la cascade ne portent plus l'attribution sourcée"
    )


def test_une_institution_non_etablie_prend_sa_colonne(cascade: str, profil: str) -> None:
    """6 des 1 098 textes n'ont aucune attribution sourcée.

    Les fondre dans « À l'Assemblée » inventerait une initiative personnelle
    (§2 règle 5) ; les taire les ferait disparaître de la liste ouverte au clic.
    """
    assert "INSTITUTION_NON_ETABLIE" in profil and "INSTITUTION_NON_ETABLIE" in cascade
    assert "'Institution non établie'" in profil
    assert "!t.institution" in cascade, "les textes sans attribution ne sont rangés nulle part"


def test_ce_qu_il_a_vote_ouvre_sur_la_periode_la_plus_recente(votes: str) -> None:
    """Deux sections voisines n'ouvrent pas sur deux bouts de carrière différents.

    « Ce qu'il a dit » ouvre sur `periodes.length - 1` ; « Ce qu'il a voté »
    ouvrait sur l'index 0, c'est-à-dire le mandat le plus ancien.
    """
    assert "useState(0)" not in votes, "la section revient à la période la plus ancienne"
    assert "periodes?.length || 1) - 1" in votes


@pytest.fixture(name="ecarts")
def _ecarts() -> str:
    return _sans_commentaires((SRC / "components" / "EcartsGroupe.jsx").read_text(encoding="utf-8"))


def test_le_filtre_nomme_l_origine_du_texte_et_non_un_banc() -> None:
    """« Gouvernement » seul se lisait comme une fonction exercée.

    Le filtre porte l'ORIGINE du texte voté — projet de loi contre proposition.
    Sur la fiche d'Emmanuel Maurel, deux boutons semblaient dire qu'il avait
    siégé au gouvernement. Arbitré le 25/09/2026, sur maquette.
    """
    src = (SRC / "utils" / "votesParPeriode.js").read_text(encoding="utf-8")
    assert "'Texte du gouvernement'" in src and "'Texte du Parlement'" in src
    assert "[ORIGINE_GOUVERNEMENT]: 'Gouvernement'" not in src


def test_le_titre_dit_de_quelle_majorite_il_parle(ecarts: str) -> None:
    """« Majoritaire » seul se lit comme la majorité de l'Assemblée.

    La section compare sa position à celle de SON GROUPE, et c'est un fait tout
    autre. Le verbe reprend le mot de la légende — « membres qui n'ont pas suivi ».
    """
    assert "n’a pas voté comme la majorité de son groupe" in ecarts
    assert "n’est pas du côté majoritaire" not in ecarts


def test_le_repere_porte_la_teinte_de_son_vote(ecarts: str) -> None:
    """Arbitré le 25/09/2026, CONTRE la lecture qui le voulait en encre.

    L'argument écarté était que les trois teintes sont prises par les positions
    de vote. La propriétaire a tranché : le repère porte la couleur du vote, ce
    qui le relie à la position écrite juste à gauche. Ne pas « corriger » vers
    l'encre — c'est une décision, pas un oubli.
    """
    assert "background: teinte(x.position)" in ecarts, (
        "le repère a perdu la teinte de son vote"
    )
    css = (SRC / "components" / "EcartsGroupe.css").read_text(encoding="utf-8")
    assert ".eg-rang-sien" in css
    assert "box-shadow: 0 0 0 1.5px var(--card" in css, (
        "sans anneau de la couleur du fond, le repère disparaît dans le segment "
        "de même teinte qu'il surmonte"
    )


def test_aucun_repere_quand_la_part_est_vide(ecarts: str) -> None:
    """Un repère posé au hasard dirait une position qu'il n'a pas prise (§2 règle 5)."""
    assert "centre === null ? null :" in ecarts


def test_le_centre_compte_les_absents_dans_le_denominateur(ecarts: str) -> None:
    """La barre MONTRE les absents : les retirer du dénominateur décalerait le
    repère de tout ce que leur segment occupe."""
    assert "+ (x.absents || 0)" in ecarts


# ── UNE PRISE DE PAROLE SE CITE, ET SE CITE PAREIL PARTOUT ──────────────────

def test_la_convention_de_citation_vit_a_un_seul_endroit() -> None:
    """Recopiée dans trois composants, elle divergerait au premier ajustement."""
    src = (SRC / "utils" / "extraits.js").read_text(encoding="utf-8")
    for nom in ("CITATION_OUVRE", "CITATION_FERME", "CITATION_ELISION"):
        assert f"export const {nom}" in src, f"{nom} n'est plus exporté"
    # Guillemets français + espaces fines insécables, jamais les guillemets droits.
    assert "'\\u00ab\\u202f'" in src and "'\\u202f\\u00bb'" in src
    # L'ÉLISION EST ENTRE CROCHETS (arbitré le 25/09/2026, sur maquette) : 1 072
    # des 352 564 extraits tronqués finissent déjà sur des points de suspension
    # DU LOCUTEUR, et « … » s'y colle sans qu'on sache lequel est de lui. Les
    # crochets disent que la marque est de nous. Ne pas revenir à « … ».
    assert "CITATION_ELISION = '[\\u2026]'" in src, (
        "l'élision est revenue aux points nus : elle se confond alors avec la "
        "suspension du locuteur"
    )


@pytest.mark.parametrize(
    "fichier",
    ["components/ParolesParPeriode.jsx", "components/ExtraitsDuDebat.jsx"],
)
def test_les_trois_fiches_citent_le_verbatim(fichier: str) -> None:
    """Candidat, lignée et gouvernement : rien ne séparait la parole rapportée
    du texte de la fiche. Demandé le 25/09/2026, « et ça devrait être le cas
    partout »."""
    src = _sans_commentaires((SRC / fichier).read_text(encoding="utf-8"))
    assert "CITATION_OUVRE" in src and "CITATION_FERME" in src


@pytest.mark.parametrize(
    "fichier,champ",
    [("components/ParolesParPeriode.jsx", "i.texteTronque"),
     ("components/ExtraitsDuDebat.jsx", "e.tronque")],
)
def test_un_extrait_coupe_ne_se_referme_pas_comme_un_propos_complet(fichier: str, champ: str) -> None:
    """29,1 % des 1 210 607 extraits publiés sont marqués tronqués.

    Refermer les guillemets sans élision donnerait une citation complète là où
    la collecte s'arrête à 280 caractères (§2 règle 5). Sur la fiche candidat,
    `texteTronque` était calculé et rendu NULLE PART avant cette correction.
    """
    src = _sans_commentaires((SRC / fichier).read_text(encoding="utf-8"))
    assert f"{champ} && ` ${{CITATION_ELISION}}`" in src
