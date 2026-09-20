"""La population à résoudre est « ce que la table ne couvre pas » (#771).

Le run `34160985529` a collecté 1 h 18 et n'a rien committé. La chaîne :

    aucune entrée neuve → aucune résolution → aucun fichier écrit
      → l'artifact n'en portait qu'un → `hashFiles()` vide dans merge-and-pivot
        → passe hors ligne SKIPPÉE
          → §5b « Sans entrée : 8 »  et  bloc 2/4 « Manquants : 5 »
            → commit refusé

Deux gestes le referment, et chacun a son test ici : résoudre la **bonne
population**, et écrire le fichier **même vide** — parce que conditionner une
étape sur la PRÉSENCE d'un fichier transforme « rien à ajouter » en « ne fais
rien ».

C'est le défaut de #715 reproduit un cran plus loin, par le même geste : borner
une population à ce qu'on avait sous les yeux en l'écrivant.
"""

import json
from pathlib import Path

import pytest

import fetch_candidats_declares as fcd

FIXTURE = Path(__file__).parent / "fixtures" / "wikipedia_candidatures_2027.html"


def _entree(nom, slug=None, statut="declare"):
    return {"nom": nom, "slug": slug, "statut": statut, "source": None}


def _candidat(nom):
    return fcd.CandidatDeclare(nom=nom, parti="Un parti", url=None)


# ---------------------------------------------------------------------------
# Les trois familles
# ---------------------------------------------------------------------------


def test_un_declare_absent_du_fichier_est_resolu():
    a = fcd.a_resoudre_identifiants([_candidat("Neuf")], [], {}, "https://x.invalid")
    assert [x["nom"] for x in a] == ["Neuf"]


def test_une_entree_sans_slug_est_resolue():
    a = fcd.a_resoudre_identifiants([], [_entree("Sans Slug")], {}, "x")
    assert [x["nom"] for x in a] == ["Sans Slug"]


def test_une_entree_A_SLUG_mais_sans_entree_de_table_est_resolue():
    """La famille qui a coûté le run.

    Invisible au critère « neuf » : elle a un slug, elle n'est pas absente du
    fichier — et pourtant la passe hors ligne a besoin de sa résolution pour
    écrire son entrée.
    """
    a = fcd.a_resoudre_identifiants([], [_entree("Déjà Sluggé", "deja-slugge")], {}, "x")
    assert [x["nom"] for x in a] == ["Déjà Sluggé"]


def test_une_entree_couverte_par_la_table_nest_pas_resolue():
    """La table passe devant : la re-résoudre coûterait un appel réseau pour un
    résultat qu'on n'écrira pas."""
    table = {"couverte": {"acteur_ref": "PA1"}}
    a = fcd.a_resoudre_identifiants([], [_entree("Couverte", "couverte")], table, "x")
    assert a == []


def test_un_statut_non_declare_nest_pas_resolu():
    """Une candidature déclinée sort du périmètre (#760) : rien à collecter,
    donc rien à corroborer."""
    a = fcd.a_resoudre_identifiants([], [_entree("Déclinée", "declinee", "decline")], {}, "x")
    assert a == []


def test_aucun_doublon_entre_les_familles():
    """Un déclaré absent du fichier ET présent dans `locaux` ne part qu'une fois."""
    a = fcd.a_resoudre_identifiants(
        [_candidat("Doublon")], [_entree("Doublon", "doublon")], {}, "x"
    )
    assert [x["nom"] for x in a] == ["Doublon"]


def test_le_cas_exact_du_run_34160985529():
    """32 entrées, toutes à slug, aucune neuve — et pourtant 13 à résoudre.

    Avant le correctif, cette situation rendait une population VIDE : c'est
    l'état dans lequel `main` se trouvait au moment du run.
    """
    locaux = [_entree(f"Personne {i}", f"personne-{i}") for i in range(32)]
    table = {f"personne-{i}": {"acteur_ref": None} for i in range(19)}

    a = fcd.a_resoudre_identifiants([], locaux, table, "x")

    assert len(a) == 13


# ---------------------------------------------------------------------------
# Le fichier s'écrit même vide
# ---------------------------------------------------------------------------


#: Les cinq déclarés que porte la fixture. Le fichier de test les contient TOUS,
#: sinon il y aurait des absents à résoudre et le scénario ne serait plus
#: « rien à résoudre ».
DECLARES_DE_LA_FIXTURE = [
    ("Nathalie Arthaud", "nathalie-arthaud"),
    ("Selma Labib", "selma-labib"),
    ("Benoît Mathieu", "benoit-mathieu"),
    ("Fabien Roussel", "fabien-roussel"),
    ("Marine Tondelier", "marine-tondelier"),
]


@pytest.fixture
def fichier(tmp_path: Path) -> Path:
    chemin = tmp_path / "candidats.json"
    chemin.write_text(
        json.dumps(
            {
                "_meta": {"statuts_possibles": ["declare"]},
                "candidats": [
                    {
                        "nom": nom,
                        "slug": slug,
                        "parti": "Un parti",
                        "famille_politique": None,
                        "statut": "declare",
                        "date_declaration": None,
                        "source": None,
                        "notes": None,
                    }
                    for nom, slug in DECLARES_DE_LA_FIXTURE
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return chemin


def test_le_fichier_de_resolutions_est_ecrit_meme_sans_rien_a_resoudre(
    fichier, tmp_path, monkeypatch
):
    """Un fichier absent et un fichier vide ne disent pas la même chose.

    C'est le conditionnement sur la présence qui a sauté la passe hors ligne.
    """
    sortie = tmp_path / "resolutions.json"
    table = tmp_path / "table.json"
    # Tous couverts par la table : plus rien à résoudre, nulle part.
    table.write_text(
        json.dumps(
            {"correspondances": {slug: {"acteur_ref": None} for _, slug in DECLARES_DE_LA_FIXTURE}}
        ),
        encoding="utf-8",
    )

    def _jamais_appele(*_a, **_k):  # pragma: no cover
        raise AssertionError("rien à résoudre : la chaîne ne doit pas sortir sur le réseau")

    monkeypatch.setattr(fcd.iw, "resoudre", _jamais_appele)

    code = fcd.main(
        [
            "--candidats", str(fichier),
            "--html", str(FIXTURE),
            "--correspondance", str(table),
            "--resolutions-out", str(sortie),
        ]
    )

    assert code == fcd.EXIT_OK
    assert sortie.is_file(), "le fichier doit exister même quand il n'y a rien dedans"
    assert json.loads(sortie.read_text(encoding="utf-8"))["resolutions"] == {}
