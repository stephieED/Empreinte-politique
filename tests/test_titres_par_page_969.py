"""Le titre et la description de chaque page (#969, forme C).

Arbitrés le 17/09/2026 sur maquette entre trois formes : le nom et
« présidentielle 2027 » en titre, ce que la fiche contient en description.
Le texte suit les données : « mandats, votes et textes » aurait été faux pour
13 des 30 candidats déclarés publiés, sans aucun vote (mesuré le 17/09/2026).

FIXTURES. Entrées copiées du corpus le 17/09/2026 — `chambres`, un mandat, un
vote, un texte porté, tels qu'ils sont dans `pivot_data/profiles/` ; seule la
longueur des listes est réduite, ce que le texte lit est leur présence. La
projection de lignée et l'entrée de gouvernement sont celles du manifeste.

CE QU'ILS NE COUVRENT PAS : le titre de l'onglet pendant la navigation
(`TitreDeLaPage.jsx`) n'est pas rendu ici. Il a été vérifié hors dépôt dans
Firefox, sur `dist/` servi comme Pages : clic vers une lignée, vers la
méthodologie, redirections `/candidats`, `/couverture`, `/groupes/AN-SOC-17`.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale"
MODULE = UI / "scripts" / "metadonnees-pages.mjs"
INDEX = UI / "index.html"

SOURCE = "Chaque fait renvoie à sa source officielle, sans note ni classement."

PROFILS = {
    "jean-luc-melenchon": (
        {"slug": "jean-luc-melenchon", "nom": "Jean-Luc Mélenchon", "parti": "La France Insoumise (LFI)"},
        {
            "chambres": ["AN", "Senat", "PE"],
            "mandats": [{"label": "Mandat parlementaire (La France insoumise)", "categorie": "mandat_electif", "debut": "2017-06-18", "fin": "2022-06-21"}],
            "votes": [{"scrutin_id": None, "position": "abstention"}],
            "textes_portes": [{"titre": "Créer une adoption sociale ouvrant un partenariat social", "dossier_id": "DLR5L15N45748"}],
        },
    ),
    "marine-tondelier": (
        {"slug": "marine-tondelier", "nom": "Marine Tondelier", "parti": "Les Écologistes"},
        {"chambres": [], "mandats": [{"label": "Hénin-Beaumont", "categorie": "mandat_local", "debut": "2020-05-18", "fin": None}], "votes": [], "textes_portes": []},
    ),
    "segolene-royal": (
        {"slug": "segolene-royal", "nom": "Ségolène Royal", "parti": "Parti Socialiste (PS)"},
        {"chambres": ["AN"], "mandats": [{"label": "Mandat parlementaire (Socialiste)", "categorie": "mandat_electif", "debut": "2002-06-19", "fin": "2007-06-19"}], "votes": [], "textes_portes": []},
    ),
    "nathalie-arthaud": (
        {"slug": "nathalie-arthaud", "nom": "Nathalie Arthaud", "parti": "Lutte Ouvrière (LO)"},
        {"chambres": [], "mandats": [], "votes": [], "textes_portes": []},
    ),
    "francois-ruffin": (
        {"slug": "francois-ruffin", "nom": "François Ruffin", "parti": "Debout !"},
        {
            "chambres": ["AN"],
            "mandats": [{"label": "Mandat parlementaire (Écologiste et Social)", "categorie": "mandat_electif", "debut": "2024-07-07", "fin": None}],
            "votes": [{"scrutin_id": "an:15:1", "position": "contre"}],
            "textes_portes": [{"titre": "Supprimer les avantages à vie des anciens présidents de la République", "dossier_id": "DLR5L17N54713"}],
        },
    ),
}
LIGNEES = {
    "AN-SOC": {"id": "AN-SOC", "nom": "Socialistes", "chambre": "AN", "periode": {"debut": "2017-06-27", "fin": None}},
    "AN-EDS": {"id": "AN-EDS", "nom": "Écologie Démocratie Solidarité", "chambre": "AN", "periode": {"debut": "2020-05-20", "fin": "2020-10-16"}},
}
GOUVERNEMENTS = {
    "LECORNU_II": {"id": "LECORNU_II", "nom": "Gouvernement Lecornu II", "debut": "2025-10-13", "fin": None, "actif": True},
    "BORNE": {"id": "BORNE", "nom": "Gouvernement Borne", "debut": "2022-05-21", "fin": "2024-01-09", "actif": False},
    "PHILIPPE": {"id": "PHILIPPE", "nom": "Gouvernement Philippe I", "debut": "2017-05-18", "fin": "2017-06-19", "actif": False},
}


def _node(corps: str):
    if shutil.which("node") is None:
        pytest.skip("node absent")
    script = f"import * as M from {json.dumps(MODULE.as_uri())};\n{corps}"
    res = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=False)
    return res


@pytest.fixture(scope="module")
def textes() -> dict:
    donnees = json.dumps({"profils": PROFILS, "lignees": LIGNEES, "gouvernements": GOUVERNEMENTS}, ensure_ascii=False)
    res = _node(
        f"const D = {donnees};\n"
        "const out = {};\n"
        "for (const [k, [e, p]] of Object.entries(D.profils)) out[k] = M.metaCandidat(e, p);\n"
        "for (const [k, l] of Object.entries(D.lignees)) out[k] = M.metaLignee(l);\n"
        "for (const [k, g] of Object.entries(D.gouvernements)) out[k] = M.metaGouvernement(g);\n"
        "console.log(JSON.stringify(out));"
    )
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout)


def test_la_fiche_complete_porte_le_texte_de_la_maquette(textes):
    assert textes["jean-luc-melenchon"] == {
        "titre": "Jean-Luc Mélenchon, présidentielle 2027 — parcours politique sourcé",
        "description": "Mandats, votes et textes à l'Assemblée nationale, au Sénat et au Parlement européen"
        f" · La France Insoumise (LFI). {SOURCE}",
    }


def test_une_fiche_sans_vote_n_annonce_pas_de_vote(textes):
    assert textes["marine-tondelier"]["description"] == f"Mandats locaux · Les Écologistes. {SOURCE}"
    royal = textes["segolene-royal"]["description"]
    assert royal == f"Mandats à l'Assemblée nationale · Parti Socialiste (PS). {SOURCE}"
    assert "vote" not in royal and "texte" not in royal


def test_une_fiche_sans_mandat_ne_dit_que_l_etiquette(textes):
    assert textes["nathalie-arthaud"]["description"] == f"Lutte Ouvrière (LO). {SOURCE}"


def test_pas_de_point_apres_une_ponctuation_finale(textes):
    assert "Debout ! Chaque fait" in textes["francois-ruffin"]["description"]


def test_le_titre_est_le_meme_pour_toutes_les_fiches_candidat(textes):
    for slug, (entree, _) in PROFILS.items():
        assert textes[slug]["titre"] == f"{entree['nom']}, présidentielle 2027 — parcours politique sourcé"


def test_groupes_et_gouvernements(textes):
    assert textes["AN-SOC"] == {
        "titre": "Groupe Socialistes à l'Assemblée nationale — membres, votes, amendements",
        "description": f"Depuis 2017. {SOURCE}",
    }
    assert textes["AN-EDS"]["description"] == f"En 2020. {SOURCE}"
    assert textes["LECORNU_II"]["titre"] == "Gouvernement Lecornu II (depuis 2025) — membres et textes"
    assert textes["BORNE"]["titre"] == "Gouvernement Borne (2022-2024) — membres et textes"
    assert textes["PHILIPPE"]["titre"] == "Gouvernement Philippe I (2017) — membres et textes"


def test_aucun_texte_ne_porte_de_chiffre_de_votes(textes):
    """§2 règle 3 : un nombre de votes se lirait comme une assiduité."""
    for cle, meta in textes.items():
        if cle in GOUVERNEMENTS or cle in LIGNEES:
            continue
        assert not any(ch.isdigit() for ch in meta["description"].replace("2027", "")), (cle, meta)


def test_une_chambre_inconnue_arrete_le_build_plutot_que_de_disparaitre():
    res = _node(
        "try { M.metaCandidat({slug:'x', nom:'X'}, {chambres:['AN','Cese'], mandats:[], votes:[], textes_portes:[]});"
        " console.log('passe'); } catch (e) { console.log('erreur', e.message); }"
    )
    assert res.stdout.startswith("erreur") and "Cese" in res.stdout


def test_chaque_chambre_du_schema_est_connue_du_module():
    """Une valeur de `KNOWN_CHAMBRES` inconnue du module arrêterait le build du site."""
    from schema_pivot import KNOWN_CHAMBRES

    res = _node("console.log(JSON.stringify([...Object.keys(M.PREPOSITION), ...M.CHAMBRES_SANS_LIBELLE]));")
    assert res.returncode == 0, res.stderr
    connues = json.loads(res.stdout)
    assert KNOWN_CHAMBRES == set(connues), (KNOWN_CHAMBRES, connues)


def test_une_chambre_mairie_ne_bloque_pas_et_n_est_pas_nommee():
    res = _node(
        "console.log(JSON.stringify(M.metaCandidat({slug:'x', nom:'X', parti:'P'},"
        " {chambres:['mairie'], mandats:[{categorie:'mandat_electif'}], votes:[], textes_portes:[]})));"
    )
    assert res.returncode == 0, res.stderr
    assert json.loads(res.stdout)["description"].startswith("Mandats · P.")


def test_chaque_balise_du_vrai_index_html_est_remplacee_une_fois():
    gabarit = INDEX.read_text(encoding="utf-8")
    meta = {"titre": 'Nom "cité" & co', "description": "Une description", "url": "https://empreinte-politique.fr/faq"}
    res = _node(
        f"const html = M.appliquerMeta({json.dumps(gabarit)}, {json.dumps(meta)});\nconsole.log(html);"
    )
    assert res.returncode == 0, res.stderr
    html = res.stdout
    assert html.count("<title>") == 1 and "<title>Nom &quot;cité&quot; &amp; co</title>" in html
    assert html.count('content="Une description"') == 3
    assert html.count('rel="canonical"') == 1
    assert '<meta property="og:url" content="https://empreinte-politique.fr/faq" />' in html


def test_une_page_sans_description_propre_garde_celle_du_site():
    gabarit = INDEX.read_text(encoding="utf-8")
    res = _node(
        f"const html = M.appliquerMeta({json.dumps(gabarit)}, {{titre: 'Sources — Empreinte politique', url: 'https://e/sources'}});\n"
        "console.log(html);"
    )
    assert res.returncode == 0, res.stderr
    assert res.stdout.count("sans note ni classement.\" />") == 3


def test_une_balise_perdue_dans_index_html_arrete_le_build():
    gabarit = INDEX.read_text(encoding="utf-8").replace('<meta property="og:url"', '<meta property="og:adresse"')
    res = _node(
        f"try {{ M.appliquerMeta({json.dumps(gabarit)}, {{titre:'t', description:'d', url:'u'}}); console.log('passe'); }}"
        " catch (e) { console.log('erreur'); }"
    )
    assert res.stdout.strip() == "erreur"


def test_l_accueil_porte_le_texte_de_la_maquette():
    gabarit = INDEX.read_text(encoding="utf-8")
    assert "<title>Présidentielle 2027 : les parcours politiques des candidats, sourcés</title>" in gabarit
    assert gabarit.count(
        "Mandats, votes et textes des candidats déclarés, par candidat, par groupe ou par gouvernement. "
        "Des faits sourcés, sans note ni classement."
    ) == 3
    assert 'rel="canonical"' not in gabarit, "la canonical de l'accueil est posée au build, après 404.html"


def test_l_onglet_suit_la_navigation():
    app = (UI / "src" / "App.jsx").read_text(encoding="utf-8")
    assert "<TitreDeLaPage />" in app
