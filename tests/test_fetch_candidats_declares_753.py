"""`fetch_candidats_declares.py` — la liste des déclarés, et ce qu'elle n'écrit pas (#753).

La fixture `wikipedia_candidatures_2027.html` est une **capture réelle**, réduite
aux lignes qui portent une forme distincte, pas un HTML écrit à la main : les
quatre lignes de candidat gardées sont celles qui ont cassé une extraction naïve
(Arthaud a un article et un lien de parti, Selma Labib n'a **pas** d'article donc
son premier lien est celui du parti, Benoît Mathieu n'a ni article ni clé de tri
et porte son âge en texte nu, Fabien Roussel traîne trois appels de note). Elle
garde aussi le titre « Candidats pressentis » et une de ses lignes, parce que la
borne de fin de section est la moitié du travail.

C'est la leçon de #726 : *une fixture qui décrit le monde tel que le code
l'imagine ne peut pas révéler que le monde a bougé*.
"""

import json
from pathlib import Path

import pytest
import requests

import fetch_candidats_declares as fcd

#: Ce fichier de tests lit la configuration committée nommée ci-dessous.
#: Le garde-fou de `conftest.py` refuse tout `.json` de `raw_data/` qu'un
#: test n'a pas déclaré (#791), et n'accepte la déclaration que si le chemin
#: est dans le `sparse-checkout` de `tests.yml` — sinon le test ne tournerait
#: qu'en local, sur ce qu'un run y a laissé.
pytestmark = pytest.mark.lit_reference_committee("raw_data/candidats.json")

FIXTURE = Path(__file__).parent / "fixtures" / "wikipedia_candidatures_2027.html"


@pytest.fixture
def html() -> str:
    return FIXTURE.read_text(encoding="utf-8")


@pytest.fixture
def fichier_candidats(tmp_path: Path) -> Path:
    document = {
        "_meta": {
            "statuts_possibles": ["declare", "pressenti", "officiel"],
            "derniere_verification": "2026-07-18",
        },
        "candidats": [
            {
                "nom": "Nathalie Arthaud",
                "slug": "nathalie-arthaud",
                "parti": "Lutte Ouvrière (LO)",
                "famille_politique": "extrême gauche",
                "statut": "declare",
                "date_declaration": "2025-12",
                "source": "https://example.invalid/arthaud",
                "notes": "4e candidature consécutive.",
            },
            {
                "nom": "Jordan BARDELLA",
                "slug": "jordan-bardella",
                "parti": "Rassemblement National (RN)",
                "famille_politique": "extrême droite",
                "statut": "pressenti",
                "date_declaration": None,
                "source": "https://example.invalid/bardella",
                "notes": None,
            },
        ],
    }
    chemin = tmp_path / "candidats.json"
    chemin.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return chemin


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------


def test_extrait_les_declares_et_sarrete_au_titre_de_niveau_2(html):
    """La section des déclarés, ses primaires comprises — et rien de « pressentis »."""
    declares, _ = fcd.extraire_declares(html)
    noms = [c.nom for c in declares]

    assert noms == [
        "Nathalie Arthaud",
        "Selma Labib",
        "Benoît Mathieu",
        "Fabien Roussel",
        "Marine Tondelier",
    ]
    assert "François Baroin" not in noms, "un pressenti ne doit jamais entrer"


def test_le_nom_vient_du_texte_et_non_du_premier_lien(html):
    """Deux déclarés n'ont pas d'article : leur premier lien est celui du parti.

    Une extraction par lien publiait « Nouveau Parti anticapitaliste » comme nom
    de candidate — c'est la ligne Selma Labib.
    """
    par_nom = {c.nom: c for c in fcd.extraire_declares(html)[0]}

    assert par_nom["Selma Labib"].parti == "NPA – Révolutionnaires"
    assert par_nom["Selma Labib"].url is None
    assert par_nom["Benoît Mathieu"].parti == "Sans étiquette"
    assert par_nom["Benoît Mathieu"].url is None


def test_les_parasites_de_cellule_sont_retires(html):
    """Clé de tri, âge et appels de note ne doivent pas entrer dans le nom."""
    par_nom = {c.nom: c for c in fcd.extraire_declares(html)[0]}

    # {{TriNom}} rend « Arthaud, Nathalie » en span caché devant le nom.
    assert par_nom["Nathalie Arthaud"].parti == "Lutte ouvrière"
    assert par_nom["Nathalie Arthaud"].url == "https://fr.wikipedia.org/wiki/Nathalie_Arthaud"
    # Fabien Roussel porte trois <sup class="reference"> entre le nom et l'âge.
    assert "63" not in par_nom["Fabien Roussel"].nom
    assert par_nom["Fabien Roussel"].parti == "Parti communiste français"


def test_une_declaration_en_primaire_est_marquee_sans_changer_de_statut(html):
    """Le drapeau `primaire` sert la note de relecture, pas le statut."""
    par_nom = {c.nom: c for c in fcd.extraire_declares(html)[0]}

    assert par_nom["Marine Tondelier"].primaire is True
    assert par_nom["Nathalie Arthaud"].primaire is False
    assert fcd.nouvelle_entree(par_nom["Marine Tondelier"], "2026-09-07")["statut"] == "declare"


def test_les_en_tetes_de_colonnes_ne_sont_pas_des_anomalies(html):
    """Une ligne qui n'a que des `th` est un en-tête, pas une ligne illisible.

    Elles étaient signalées quatre fois par run ; un avertissement qu'on apprend
    à ignorer est un avertissement perdu.
    """
    _, anomalies = fcd.extraire_declares(html)
    assert anomalies == []


# ---------------------------------------------------------------------------
# Rien n'est écrit sur une collecte en échec (#511)
# ---------------------------------------------------------------------------


def test_section_introuvable_leve_et_nomme_larticle():
    with pytest.raises(fcd.CollecteIncomplete) as leve:
        fcd.extraire_declares("<div class='mw-heading mw-heading2'><h2>Sondages</h2></div>")
    assert fcd.ANOMALIE_SECTION in str(leve.value)


def test_section_presente_mais_vide_leve():
    """Le filet de dernier recours : le titre est là, la forme du tableau a changé."""
    vide = (
        "<div class='mw-heading mw-heading2'><h2>Candidats déclarés</h2></div>"
        "<table class='wikitable'><tr><th>Candidat</th></tr></table>"
    )
    with pytest.raises(fcd.CollecteIncomplete) as leve:
        fcd.extraire_declares(vide)
    assert fcd.ANOMALIE_VIDE in str(leve.value)


def test_le_fichier_nest_pas_touche_quand_la_collecte_echoue(fichier_candidats, monkeypatch):
    """Le patron de #511 : une collecte vide n'est pas un résultat."""
    avant = fichier_candidats.read_text(encoding="utf-8")

    def _echec(*_args, **_kwargs):
        raise requests.RequestException("Read timed out")

    monkeypatch.setattr(fcd.requests, "get", _echec)
    code = fcd.main(["--candidats", str(fichier_candidats), "--ecrire"])

    assert code == fcd.EXIT_COLLECTE_INCOMPLETE
    assert fichier_candidats.read_text(encoding="utf-8") == avant


def test_lexception_reseau_voyage_jusquau_message(monkeypatch):
    """« en échec » ne dit pas s'il faut relancer ou corriger le code (#524)."""

    def _echec(*_args, **_kwargs):
        raise requests.RequestException("HTTP 500")

    monkeypatch.setattr(fcd.requests, "get", _echec)
    with pytest.raises(fcd.CollecteIncomplete) as leve:
        fcd.telecharger_html()
    assert "HTTP 500" in str(leve.value)


def test_une_erreur_dapi_est_une_collecte_incomplete(monkeypatch):
    class _Reponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"error": {"info": "The page you specified doesn't exist."}}

    monkeypatch.setattr(fcd.requests, "get", lambda *a, **k: _Reponse())
    with pytest.raises(fcd.CollecteIncomplete) as leve:
        fcd.telecharger_html()
    assert "doesn't exist" in str(leve.value)


# ---------------------------------------------------------------------------
# Comparaison
# ---------------------------------------------------------------------------


def test_comparer_dans_les_deux_sens(html, fichier_candidats):
    declares, _ = fcd.extraire_declares(html)
    locaux = json.loads(fichier_candidats.read_text(encoding="utf-8"))["candidats"]

    ecarts = fcd.comparer(declares, locaux)

    assert [c.nom for c in ecarts.absents_du_fichier] == [
        "Selma Labib",
        "Benoît Mathieu",
        "Fabien Roussel",
        "Marine Tondelier",
    ]
    assert [e["nom"] for e in ecarts.plus_declares] == ["Jordan BARDELLA"]
    assert ecarts.communs == ["Nathalie Arthaud"]


def test_la_casse_et_les_accents_ne_font_pas_deux_personnes():
    """« Jordan BARDELLA » et « Jordan Bardella » sont la même entrée."""
    assert fcd.cle_nom("Jordan BARDELLA") == fcd.cle_nom("Jordan Bardella")
    assert fcd.cle_nom("Édouard Philippe") == fcd.cle_nom("Edouard PHILIPPE")


# ---------------------------------------------------------------------------
# Écriture
# ---------------------------------------------------------------------------


def test_lecriture_est_additive_et_ne_touche_aucune_entree_existante(html, fichier_candidats):
    declares, _ = fcd.extraire_declares(html)
    document = json.loads(fichier_candidats.read_text(encoding="utf-8"))
    avant = json.loads(json.dumps(document["candidats"]))

    ecarts = fcd.comparer(declares, document["candidats"])
    apres = fcd.appliquer(document, ecarts.absents_du_fichier, "2026-09-07")

    assert apres["candidats"][: len(avant)] == avant
    assert len(apres["candidats"]) == len(avant) + 4
    assert apres["_meta"]["derniere_verification"] == "2026-09-07"


def test_un_nouveau_candidat_entre_sans_slug(html):
    """Sans slug, pas de shard `extract-an`, donc pas de publication (portail §5b)."""
    declares, _ = fcd.extraire_declares(html)
    entree = fcd.nouvelle_entree(declares[1], "2026-09-07")

    assert entree["slug"] is None
    assert entree["statut"] == "declare"
    # Le tableau des déclarés ne porte ni l'un ni l'autre : une absence reste
    # une absence (§2 règle 5).
    assert entree["famille_politique"] is None
    assert entree["date_declaration"] is None
    assert "2026-09-07" in entree["notes"]


def test_une_sortie_SANS_cause_nommee_est_signalee_jamais_modifiee(
    fichier_candidats, capsys
):
    """L'invariant de #753, restreint par #763 à ce qui reste vrai.

    Une entrée que la source range sous « Candidatures retirées » ou
    « Candidats pressentis ayant décliné » transitionne désormais (#763) — c'est
    un fait lu. Celle qui disparaît des déclarés SANS qu'aucune section ne la
    nomme reste intouchée : déplacement, renommage, cause inconnue, et trancher
    à sa place serait inventer une cause (§2 règle 5).

    Jordan BARDELLA ne convient plus pour ce test : la fixture le nomme sous
    « ayant décliné ». On prend donc quelqu'un qu'aucune section ne mentionne.
    """
    document = json.loads(fichier_candidats.read_text(encoding="utf-8"))
    document["candidats"].append(
        {
            "nom": "Personne Sans Cause",
            "slug": "personne-sans-cause",
            "parti": "Un parti",
            "famille_politique": None,
            "statut": "declare",
            "date_declaration": None,
            "source": None,
            "notes": None,
        }
    )
    fichier_candidats.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    code = fcd.main(
        ["--candidats", str(fichier_candidats), "--html", str(FIXTURE), "--ecrire"]
    )
    apres = json.loads(fichier_candidats.read_text(encoding="utf-8"))
    sans_cause = [c for c in apres["candidats"] if c["nom"] == "Personne Sans Cause"][0]

    assert code == fcd.EXIT_OK
    assert sans_cause["statut"] == "declare", "le script ne tranche pas une cause absente"
    assert sans_cause["slug"] == "personne-sans-cause"
    assert "Personne Sans Cause" in capsys.readouterr().out


def test_sans_ecrire_le_fichier_ne_bouge_pas(fichier_candidats):
    avant = fichier_candidats.read_text(encoding="utf-8")
    code = fcd.main(["--candidats", str(fichier_candidats), "--html", str(FIXTURE)])

    assert code == fcd.EXIT_OK
    assert fichier_candidats.read_text(encoding="utf-8") == avant


def test_avec_ecrire_les_declares_manquants_entrent(fichier_candidats):
    fcd.main(["--candidats", str(fichier_candidats), "--html", str(FIXTURE), "--ecrire"])
    apres = json.loads(fichier_candidats.read_text(encoding="utf-8"))

    assert [c["nom"] for c in apres["candidats"]] == [
        "Nathalie Arthaud",
        "Jordan BARDELLA",
        "Selma Labib",
        "Benoît Mathieu",
        "Fabien Roussel",
        "Marine Tondelier",
    ]


def test_deux_passes_nadditionnent_pas_les_doublons(fichier_candidats):
    """Le script est idempotent : relancé, il ne recrée pas ce qu'il a écrit."""
    args = ["--candidats", str(fichier_candidats), "--html", str(FIXTURE), "--ecrire"]
    fcd.main(args)
    premier = json.loads(fichier_candidats.read_text(encoding="utf-8"))["candidats"]
    fcd.main(args)
    second = json.loads(fichier_candidats.read_text(encoding="utf-8"))["candidats"]

    assert [c["nom"] for c in premier] == [c["nom"] for c in second]


def test_la_forme_du_fichier_survit_a_un_aller_retour(tmp_path):
    """Un format qui churne rendrait le diff illisible — la seule chose à relire."""
    source = Path("raw_data/candidats.json")
    if not source.exists():  # sparse-checkout d'un job qui ne prend pas raw_data/
        pytest.skip("raw_data/candidats.json absent de ce checkout")
    brut = source.read_text(encoding="utf-8")
    copie = tmp_path / "candidats.json"

    fcd.ecrire(copie, json.loads(brut))

    avant, apres = brut.splitlines(), copie.read_text(encoding="utf-8").splitlines()
    touchees = sum(1 for ligne in apres if ligne not in avant)
    assert touchees <= 6, "l'aller-retour ne doit réécrire que le tableau compacté à la main"


def test_echouer_si_ecart_rend_le_code_3(fichier_candidats):
    code = fcd.main(
        ["--candidats", str(fichier_candidats), "--html", str(FIXTURE), "--echouer-si-ecart"]
    )
    assert code == fcd.EXIT_ECART


def test_sortie_json_porte_les_deux_sens(fichier_candidats, capsys):
    fcd.main(["--candidats", str(fichier_candidats), "--html", str(FIXTURE), "--json"])
    rendu = json.loads(capsys.readouterr().out)

    assert len(rendu["declares_en_ligne"]) == 5
    assert rendu["absents_du_fichier"] == [
        "Selma Labib",
        "Benoît Mathieu",
        "Fabien Roussel",
        "Marine Tondelier",
    ]
    assert rendu["plus_declares"] == ["Jordan BARDELLA"]
    assert rendu["ecrit"] is False


# ---------------------------------------------------------------------------
# Le fichier réel : la cohérence que rien ne contrôlait
# ---------------------------------------------------------------------------


def _corpus() -> dict:
    source = Path("raw_data/candidats.json")
    if not source.exists():  # checkout partiel d'un job qui ne prend pas raw_data/
        pytest.skip("raw_data/candidats.json absent de ce checkout")
    return json.loads(source.read_text(encoding="utf-8"))


def test_tout_statut_publie_est_dans_statuts_possibles():
    """`statuts_possibles` était une liste que personne ne confrontait au fichier.

    `decline` y est entré avec #753 : une candidature abandonnée n'avait aucune
    valeur pour se dire, et deux entrées ont porté `declare` / `pressenti`
    pendant 51 jours après avoir été déclinées.
    """
    document = _corpus()
    connus = set(document["_meta"]["statuts_possibles"])

    inconnus = {
        c["nom"]: c["statut"] for c in document["candidats"] if c["statut"] not in connus
    }
    assert inconnus == {}, f"statuts hors de statuts_possibles : {inconnus}"


def test_une_entree_sans_slug_ne_recoit_jamais_de_famille_ni_de_date_inventees():
    """Ce que la source ne porte pas reste `null` jusqu'à relecture (§2 règle 5)."""
    for candidat in _corpus()["candidats"]:
        if candidat["slug"] is not None:
            continue
        assert candidat["nom"], "une entrée sans slug doit au moins porter son nom"
        assert candidat["notes"], "une entrée non relue doit dire ce qui manque"


def test_aucun_doublon_de_nom_ni_de_slug():
    document = _corpus()
    cles = [fcd.cle_nom(c["nom"]) for c in document["candidats"]]
    slugs = [c["slug"] for c in document["candidats"] if c["slug"]]

    assert len(cles) == len(set(cles))
    assert len(slugs) == len(set(slugs))


def test_la_sortie_json_reste_lisible_en_CI(fichier_candidats, capsys, monkeypatch):
    """`gha.annoter` écrit sur STDOUT, et seulement quand `GITHUB_ACTIONS` vaut
    « true » — donc en CI et jamais en local.

    Sans ce test, la suite passait en local et échouait en CI : les annotations
    s'intercalaient avant le document et `json.loads` mourait sur le premier
    `::notice::`. C'est le patron de #726 — un banc qui décrit le monde tel que
    le code l'imagine ne peut pas révéler que le monde a bougé —, ici appliqué
    à l'environnement plutôt qu'aux données.
    """
    monkeypatch.setenv("GITHUB_ACTIONS", "true")

    fcd.main(["--candidats", str(fichier_candidats), "--html", str(FIXTURE), "--json"])

    sortie = capsys.readouterr().out
    assert "::" not in sortie, "une commande de workflow a été émise en mode --json"
    json.loads(sortie)  # ne doit pas lever
