"""Le slug d'un candidat se fabrique quand un identifiant le porte (#757).

#753 faisait entrer tout déclaré neuf avec `slug: null`, et sans slug il n'y a
pas de shard `extract-an` : le périmètre n'avançait que lorsqu'une main y
pensait. Ces tests couvrent la porte qui s'ouvre — et surtout les trois cas où
elle reste fermée, parce qu'un slug fabriqué sans corroboration ferait publier
un profil que la §5b refuserait ensuite.
"""

import json
from pathlib import Path

import pytest

import fetch_candidats_declares as fcd
import identifiants_wikidata as iw

FIXTURE = Path(__file__).parent / "fixtures" / "wikipedia_candidatures_2027.html"


def _candidat(nom, url=None):
    return fcd.CandidatDeclare(nom=nom, parti="Un parti", url=url)


def _resolution(nom, issue, acteur_ref=None):
    return iw.Resolution(
        nom=nom,
        issue=issue,
        acteur_ref=acteur_ref,
        qid="Q1",
        preuve="https://www.wikidata.org/wiki/Q1",
    )


# ---------------------------------------------------------------------------
# Attribution
# ---------------------------------------------------------------------------


def test_un_acteur_resolu_donne_un_slug():
    absents = [_candidat("Fabien Roussel")]
    resolutions = {"Fabien Roussel": _resolution("Fabien Roussel", iw.Issue.ACTEUR, "PA720692")}

    slugs, refus = fcd.attribuer_slugs(absents, resolutions, {})

    assert slugs == {"Fabien Roussel": "fabien-roussel"}
    assert refus == []


def test_un_hors_an_recoit_aussi_son_slug():
    """Il n'a rien à collecter, mais sa fiche existe et son entrée est écrivable."""
    absents = [_candidat("François Asselineau")]
    resolutions = {"François Asselineau": _resolution("François Asselineau", iw.Issue.HORS_AN)}

    slugs, refus = fcd.attribuer_slugs(absents, resolutions, {})

    assert slugs == {"François Asselineau": "francois-asselineau"}


def test_un_identifiant_indetermine_ne_donne_aucun_slug():
    """Sans corroboration possible hors ligne, un slug bloquerait le run entier."""
    absents = [_candidat("Selma Labib")]
    resolutions = {"Selma Labib": _resolution("Selma Labib", iw.Issue.INDETERMINE)}

    slugs, refus = fcd.attribuer_slugs(absents, resolutions, {})

    assert slugs == {}
    assert refus and refus[0].startswith(fcd.MOTIF_IDENTIFIANT_INDETERMINE)
    assert "Selma Labib" in refus[0]


def test_une_resolution_absente_vaut_indetermine():
    slugs, refus = fcd.attribuer_slugs([_candidat("Inconnu")], {}, {})
    assert slugs == {} and refus[0].startswith(fcd.MOTIF_IDENTIFIANT_INDETERMINE)


# ---------------------------------------------------------------------------
# Collisions : c'est l'acteur qui tranche, jamais le nom
# ---------------------------------------------------------------------------


def test_un_slug_deja_porte_par_la_meme_personne_est_repris():
    """Ruffin, Brun et Faure sont déjà collectés comme membres de roster.

    Leur slug existe, il est le leur, et le reprendre est ce qui fait basculer
    leur `meta.provenance` sans rien collecter de neuf.
    """
    absents = [_candidat("François Ruffin")]
    resolutions = {"François Ruffin": _resolution("François Ruffin", iw.Issue.ACTEUR, "PA722142")}

    slugs, refus = fcd.attribuer_slugs(absents, resolutions, {"francois-ruffin": "PA722142"})

    assert slugs == {"François Ruffin": "francois-ruffin"}
    assert refus == []


def test_un_slug_porte_par_quelqu_un_d_autre_est_refuse():
    """Le cas `alexandra-martin` de #525 : deux personnes, un seul slug visé."""
    absents = [_candidat("Alexandra Martin")]
    resolutions = {"Alexandra Martin": _resolution("Alexandra Martin", iw.Issue.ACTEUR, "PA999")}

    slugs, refus = fcd.attribuer_slugs(absents, resolutions, {"alexandra-martin": "PA111"})

    assert slugs == {}
    assert refus[0].startswith(fcd.MOTIF_SLUG_DEJA_PRIS)
    assert "PA111" in refus[0] and "PA999" in refus[0]


def test_deux_neufs_qui_visent_le_meme_slug_ne_le_partagent_pas():
    absents = [_candidat("Jean Dupont"), _candidat("Jean Dupont ")]
    resolutions = {
        "Jean Dupont": _resolution("Jean Dupont", iw.Issue.ACTEUR, "PA1"),
        "Jean Dupont ": _resolution("Jean Dupont ", iw.Issue.ACTEUR, "PA2"),
    }

    slugs, refus = fcd.attribuer_slugs(absents, resolutions, {})

    assert len(slugs) == 1
    assert refus and refus[0].startswith(fcd.MOTIF_SLUG_DEJA_PRIS)


# ---------------------------------------------------------------------------
# Écriture : combler un trou n'est pas réécrire une valeur
# ---------------------------------------------------------------------------


def test_un_slug_null_existant_est_comble_et_les_autres_ne_bougent_pas():
    document = {
        "_meta": {},
        "candidats": [
            {"nom": "Déjà Publié", "slug": "deja-publie", "statut": "declare", "notes": "intacte"},
            {"nom": "En Attente", "slug": None, "statut": "declare", "notes": "à relire"},
        ],
    }

    apres = fcd.appliquer(document, [], "2026-09-07", {"En Attente": "en-attente"})

    assert apres["candidats"][0] == document["candidats"][0], "entrée publiée intacte"
    assert apres["candidats"][1]["slug"] == "en-attente"
    # Le comblement ne réécrit rien d'autre de l'entrée.
    assert apres["candidats"][1]["notes"] == "à relire"


def test_un_slug_deja_pose_nest_jamais_remplace():
    document = {
        "_meta": {},
        "candidats": [{"nom": "Publié", "slug": "ancien-slug", "statut": "declare"}],
    }

    apres = fcd.appliquer(document, [], "2026-09-07", {"Publié": "nouveau-slug"})

    assert apres["candidats"][0]["slug"] == "ancien-slug"


def test_les_notes_disent_par_quelle_porte_lentree_est_passee():
    avec = fcd.nouvelle_entree(_candidat("Avec Slug"), "2026-09-07", "avec-slug")
    sans = fcd.nouvelle_entree(_candidat("Sans Slug"), "2026-09-07", None)

    assert "identifiant externe" in avec["notes"]
    assert "Sans slug" in sans["notes"] and sans["slug"] is None


# ---------------------------------------------------------------------------
# Une panne d'identifiants n'écrit rien
# ---------------------------------------------------------------------------


@pytest.fixture
def fichier(tmp_path: Path) -> Path:
    chemin = tmp_path / "candidats.json"
    chemin.write_text(
        json.dumps(
            {
                "_meta": {"statuts_possibles": ["declare"], "derniere_verification": "2026-01-01"},
                "candidats": [
                    {
                        "nom": "Nathalie Arthaud",
                        "slug": "nathalie-arthaud",
                        "parti": "LO",
                        "famille_politique": None,
                        "statut": "declare",
                        "date_declaration": None,
                        "source": None,
                        "notes": None,
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return chemin


def test_une_panne_de_resolution_nécrit_rien(fichier, monkeypatch):
    """Le patron de #511, appliqué à l'identifiant au lieu de la liste."""
    avant = fichier.read_text(encoding="utf-8")

    def _panne(*_a, **_k):
        raise iw.ResolutionIndisponible("Read timed out")

    monkeypatch.setattr(fcd.iw, "resoudre", _panne)
    code = fcd.main(
        [
            "--candidats", str(fichier),
            "--html", str(FIXTURE),
            "--ecrire",
            "--resoudre-identifiants",
        ]
    )

    assert code == fcd.EXIT_COLLECTE_INCOMPLETE
    assert fichier.read_text(encoding="utf-8") == avant


def test_les_resolutions_sont_ecrites_pour_la_passe_hors_ligne(fichier, tmp_path, monkeypatch):
    sortie = tmp_path / "resolutions.json"

    def _resoudre(candidats, session=None):
        return {c["nom"]: _resolution(c["nom"], iw.Issue.ACTEUR, "PA1") for c in candidats}

    monkeypatch.setattr(fcd.iw, "resoudre", _resoudre)
    fcd.main(
        [
            "--candidats", str(fichier),
            "--html", str(FIXTURE),
            "--ecrire",
            "--resolutions-out", str(sortie),
        ]
    )

    document = json.loads(sortie.read_text(encoding="utf-8"))
    assert document["schema_version"] == "resolutions-candidats-v1"
    assert document["resolutions"]


def test_sans_le_drapeau_le_comportement_de_753_est_inchange(fichier):
    """`slug: null` reste le défaut : la boucle est explicite, jamais subie."""
    fcd.main(["--candidats", str(fichier), "--html", str(FIXTURE), "--ecrire"])
    apres = json.loads(fichier.read_text(encoding="utf-8"))

    neufs = [c for c in apres["candidats"] if c["nom"] != "Nathalie Arthaud"]
    assert neufs and all(c["slug"] is None for c in neufs)
