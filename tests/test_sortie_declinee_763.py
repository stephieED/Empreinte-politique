"""Le script pose `decline` quand la source nomme la cause (#763).

Trois lots consommaient `decline` — le périmètre de collecte (#760), le masquage
de la fiche (#761), le rapport de #753 — et **aucun ne le posait** : les deux
valeurs du fichier avaient été écrites à la main. Trois consommateurs
automatiques d'une valeur que seule une main pouvait produire.

Ce que ces tests tiennent est la **frontière** : « figure sous *Candidats
pressentis ayant décliné* » est un fait lu et s'écrit ; « ne figure plus parmi
les déclarés » est une absence, ne dit ni retrait ni renommage, et ne change
rien.

La fixture porte les deux sections de sortie, réduites aux trois puces qui
comptent : Clémentine Autain (retirée), Wauquiez et Bardella (déclinés).
"""

import json
from pathlib import Path

import pytest

import fetch_candidats_declares as fcd

FIXTURE = Path(__file__).parent / "fixtures" / "wikipedia_candidatures_2027.html"


@pytest.fixture
def html() -> str:
    return FIXTURE.read_text(encoding="utf-8")


def _entree(nom, statut="declare", slug=None):
    return {
        "nom": nom,
        "slug": slug or nom.lower().replace(" ", "-"),
        "parti": "Un parti",
        "famille_politique": None,
        "statut": statut,
        "date_declaration": None,
        "source": None,
        "notes": "note d'origine",
    }


# ---------------------------------------------------------------------------
# Lire les sections de sortie
# ---------------------------------------------------------------------------


def test_les_deux_sections_de_sortie_sont_lues(html):
    sorties = fcd.extraire_sorties(html)

    assert set(sorties) == {"clementine autain", "laurent wauquiez", "jordan bardella"}
    assert sorties["clementine autain"][0] == "Candidatures retirées"
    assert sorties["laurent wauquiez"][0] == "Candidats pressentis ayant décliné"


def test_la_personne_est_le_premier_lien_de_sa_puce(html):
    """Le reste de la puce lie son parti, son mandat, et souvent le candidat
    qu'elle soutient désormais — un lien pris au hasard nommerait l'un d'eux."""
    sorties = fcd.extraire_sorties(html)
    assert sorties["laurent wauquiez"][1] == "https://fr.wikipedia.org/wiki/Laurent_Wauquiez"


def test_une_section_absente_ne_propose_rien():
    """L'article peut cesser de porter une section — plus aucun retrait à
    recenser. L'absence de preuve n'est pas une preuve d'absence."""
    assert fcd.extraire_sorties("<p>rien du tout</p>") == {}


def test_la_lecture_des_declares_nest_pas_perturbee(html):
    """Les sections de sortie sont après les déclarés : la borne de fin tient."""
    declares, _ = fcd.extraire_declares(html)
    noms = {c.nom for c in declares}
    assert "Clémentine Autain" not in noms
    assert "Laurent Wauquiez" not in noms


# ---------------------------------------------------------------------------
# Les trois garde-fous
# ---------------------------------------------------------------------------


def test_une_entree_nommee_par_une_sortie_transitionne(html):
    sorties = fcd.extraire_sorties(html)
    locaux = [_entree("Laurent Wauquiez"), _entree("Jordan Bardella", "pressenti")]

    transitions = fcd.transitions_de_sortie(locaux, sorties)

    assert {e["nom"] for e, _, _ in transitions} == {"Laurent Wauquiez", "Jordan Bardella"}


def test_on_ne_cree_jamais_une_entree_depuis_une_sortie(html):
    """Publier quelqu'un pour dire qu'il renonce serait absurde.

    Clémentine Autain est dans la section des retirées et pas dans notre
    fichier : elle ne doit produire aucune transition, donc aucune entrée.
    """
    sorties = fcd.extraire_sorties(html)
    transitions = fcd.transitions_de_sortie([_entree("Quelqu'un d'Autre")], sorties)
    assert transitions == []


def test_un_statut_officiel_ne_bascule_pas(html):
    """Il viendra du Conseil constitutionnel, et un article encyclopédique ne
    renverse pas un acte publié au Journal officiel."""
    sorties = fcd.extraire_sorties(html)
    transitions = fcd.transitions_de_sortie([_entree("Laurent Wauquiez", "officiel")], sorties)
    assert transitions == []


def test_une_entree_deja_declinee_nest_pas_reecrite(html):
    """Sinon chaque run ferait bouger le fichier sans rien dire de neuf."""
    sorties = fcd.extraire_sorties(html)
    transitions = fcd.transitions_de_sortie([_entree("Laurent Wauquiez", "decline")], sorties)
    assert transitions == []


# ---------------------------------------------------------------------------
# Ce que l'écriture pose
# ---------------------------------------------------------------------------


def test_la_note_cite_la_section_a_la_lettre():
    """Vérifiable dans l'article : c'est le titre, pas sa paraphrase."""
    note = fcd.note_de_sortie(
        "Candidats pressentis ayant décliné", "declare", "2026-09-07", "https://ex.invalid/x"
    )
    assert "« Candidats pressentis ayant décliné »" in note
    assert "de declare à decline" in note
    assert "2026-09-07" in note
    assert "https://ex.invalid/x" in note


def test_lecriture_change_le_statut_et_la_note_et_rien_dautre(html):
    sorties = fcd.extraire_sorties(html)
    document = {"_meta": {}, "candidats": [_entree("Laurent Wauquiez")]}

    apres = fcd.appliquer(document, [], "2026-09-07", None, sorties)
    entree = apres["candidats"][0]

    assert entree["statut"] == "decline"
    assert entree["notes"] != "note d'origine"
    # Le slug publié est immuable (#460/#470), le reste de l'entrée intact.
    assert entree["slug"] == "laurent-wauquiez"
    assert entree["parti"] == "Un parti"


def test_sans_section_de_sortie_rien_ne_bouge(html):
    """Le régime de #753, préservé : une absence ne change rien."""
    document = {"_meta": {}, "candidats": [_entree("Quelqu'un Qui Disparait")]}
    avant = json.loads(json.dumps(document))

    apres = fcd.appliquer(document, [], "2026-09-07", None, fcd.extraire_sorties(html))

    assert apres["candidats"] == avant["candidats"]


# ---------------------------------------------------------------------------
# De bout en bout
# ---------------------------------------------------------------------------


@pytest.fixture
def fichier(tmp_path: Path) -> Path:
    chemin = tmp_path / "candidats.json"
    chemin.write_text(
        json.dumps(
            {
                "_meta": {"statuts_possibles": ["declare", "pressenti", "decline", "officiel"]},
                "candidats": [_entree("Laurent Wauquiez"), _entree("Nathalie Arthaud")],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return chemin


def test_main_pose_le_statut_et_le_rapporte(fichier, capsys):
    code = fcd.main(["--candidats", str(fichier), "--html", str(FIXTURE), "--ecrire"])
    apres = {c["nom"]: c for c in json.loads(fichier.read_text(encoding="utf-8"))["candidats"]}

    assert code == fcd.EXIT_OK
    assert apres["Laurent Wauquiez"]["statut"] == "decline"
    assert apres["Nathalie Arthaud"]["statut"] == "declare"
    assert "SORTIES NOMMÉES PAR LA SOURCE" in capsys.readouterr().out


def test_sans_ecrire_le_statut_ne_bouge_pas(fichier):
    avant = fichier.read_text(encoding="utf-8")
    fcd.main(["--candidats", str(fichier), "--html", str(FIXTURE)])
    assert fichier.read_text(encoding="utf-8") == avant


def test_une_sortie_nommee_nest_pas_signalee_comme_a_relire(fichier, capsys):
    """Le `warning` reste pour ce qui demande une relecture : une disparition
    dont aucune section ne dit la cause."""
    fcd.main(["--candidats", str(fichier), "--html", str(FIXTURE), "--ecrire"])
    sortie = capsys.readouterr().out
    assert "ENTRÉES QUI NE SONT PLUS DÉCLARÉES" not in sortie
