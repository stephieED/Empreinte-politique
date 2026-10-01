"""Une fiche sans donnée ne répète pas six fois la même absence.

ARBITRÉ LE 01/10/2026, sur quatre rendus comparés de la fiche d'Anasse Kazib —
candidat déclaré sans aucun mandat, zéro entrée au pivot.

Mesuré avant : six sections, 2 725 px, dont 996 px de cartes « Rien à afficher »
réparties sur quatre sections, et 608 px pour « Ce qu'on n'a pas pu lire » — le
seul bloc qui dise la cause, liste par liste, avec sa borne. Il était en dernier.

CE N'EST PAS UN MASQUAGE, et c'est ce qui le rend compatible avec §2 règle 5 :
l'absence reste déclarée, à l'endroit où elle s'explique. La section vide tient
en une ligne qui y renvoie.
"""
from __future__ import annotations

from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "web" / "UI_finale" / "src"
FICHE = SRC / "components" / "CandidateProfile.jsx"
LECTURE = SRC / "components" / "Lecture.jsx"
LIGNEE = SRC / "components" / "LigneeProfile.jsx"
ECARTS = SRC / "components" / "EcartsGroupe.jsx"


def test_les_vides_de_la_fiche_candidat_renvoient_tous_au_meme_endroit() -> None:
    """Un « Pourquoi → » qui mène tantôt en bas de page, tantôt sur une autre
    page, c'est le lecteur qui paie. Les quatre renvoient à la section 6."""
    fiche = FICHE.read_text(encoding="utf-8")
    assert fiche.count('compacte renvoi="#section-6"') == 4, (
        "les quatre listes vides de la fiche candidat doivent renvoyer à « Ce qu'on "
        "n'a pas pu lire »"
    )
    assert 'Rien à comparer' in ECARTS.read_text(encoding="utf-8")
    assert 'href="#section-6"' in ECARTS.read_text(encoding="utf-8")


def test_une_liste_jamais_interrogee_ne_dit_pas_qu_on_a_cherche() -> None:
    """« Aucune donnée TROUVÉE » affirme une recherche.

    Sur une liste `non_collecte`, cette recherche n'a pas eu lieu : le dire
    publierait un résultat là où il n'y a pas eu de mesure (§2 règle 5, et le
    commentaire d'`EMPTY_LIST_CAUSES` qui l'écrit déjà pour la carte pleine).
    """
    lecture = LECTURE.read_text(encoding="utf-8")
    assert "non_collecte: 'Liste non interrogée.'" in lecture
    assert "defaut: 'Aucune donnée trouvée.'" in lecture


def test_une_section_vide_ne_porte_plus_sa_regle_de_lecture() -> None:
    """Rien à montrer, donc rien à expliquer — sa consigne du 01/10/2026.

    Le pied et le critère accompagnent des figures ; sous une mention d'absence,
    ils sont deux lignes de commentaire pour une ligne de contenu.
    """
    fiche = FICHE.read_text(encoding="utf-8")
    assert "c.fonctions.blocs.length === 0 ? null : (" in fiche, "le pied de la section 1"
    assert "critere={c.ecarts.bande.length" in fiche, "le critère de la section 4"
    assert "critere={c.interventions.total" in fiche, "le critère de la section 5"
    assert "{!sectionVide && (" in fiche, (
        "le renvoi de méthodologie de la section 2"
    )


def test_la_carte_des_amendements_disparait_quand_la_section_entiere_est_vide() -> None:
    """Deux mentions pour un même vide, dont une en carte pleine.

    Sur une fiche sans donnée, la ligne des textes dit déjà l'absence et renvoie à
    sa cause ; la carte des amendements la redisait juste en dessous, avec son
    titre et son fond. Elle disparaît — mais SEULEMENT quand la section entière ne
    porte rien.

    ELLE RESTE DÈS QUE L'AUTRE VERSANT PORTE QUELQUE CHOSE. Son titre dit alors de
    quel parlement il s'agit, sans quoi « aucun amendement » se lirait comme un
    vide de collecte quand le Parlement d'à côté en porte des milliers — c'est la
    raison écrite dans le composant, et elle ne tombe pas avec ce lot.
    """
    fiche = FICHE.read_text(encoding="utf-8")
    assert "const sectionVide = textes.total === 0 && europe.total === 0 && !amdt.totalAuteur" in fiche
    assert "{sectionVide ? null : amdt.totalAuteur === 0 ? (" in fiche
    # `amdt.totalAuteur === 0` ne paraît QU'UNE FOIS : une garde de #901 découpe
    # le fichier sur cette expression, et la répéter coupait sa tranche ailleurs.
    assert fiche.count("amdt.totalAuteur === 0") == 1
    assert "est l’auteur" in fiche, "le titre du versant vide ne doit pas disparaître avec la carte"


def test_la_cause_des_ecarts_est_dite_en_section_six() -> None:
    """Les écarts ne sont pas une liste collectée — ni borne, ni compte —, donc
    pas une sixième ligne du tableau. Ils ont leur mention, et elle porte la
    nuance sans laquelle le vide se lirait « il n'a jamais divergé »."""
    fiche = FICHE.read_text(encoding="utf-8")
    assert "cp-couv-ecarts" in fiche
    assert "ecartsSansFiche={!c.ecarts.fiches.length}" in fiche
    assert "ne dit pas qu’elle n’a jamais divergé" in fiche


def test_la_fiche_de_lignee_garde_la_carte_pleine() -> None:
    """La répétition qui a motivé la forme courte n'existe pas là-bas : la
    décision porte sur la fiche candidat, et elle ne déborde pas."""
    lignee = LIGNEE.read_text(encoding="utf-8")
    assert "ListeVide" in lignee
    assert "compacte" not in lignee
