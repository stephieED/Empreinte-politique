"""Les faits d'une fiche sont lisibles sans JavaScript (#969).

Mesuré en production le 17/09/2026 après #1002 : le corps d'une fiche servie
contenait **0 caractère**. Les robots des modèles de langage n'exécutent en
général pas le JavaScript : ils ne lisaient que le titre et la description.

`scripts/bloc-sans-js.mjs` écrit dans le conteneur de l'application les faits
déjà publiés. Arbitré sur maquette le 17/09/2026, sur cinq fiches réelles.

FIXTURES. Entrées copiées du corpus le 17/09/2026 : le mandat local d'Hénin-
Beaumont, TERMINÉ (`actif` faux) et SANS date de fin, est le cas qui fait la
règle — la période se lit sur `actif`.

CE QU'ILS NE COUVRENT PAS : le remplacement du bloc par React. Vérifié hors
dépôt dans Firefox sur `dist/` servi comme Pages, JavaScript activé puis coupé :
un seul `<h1>`, 705 caractères de texte sans JavaScript contre 20 831 avec.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale"
MODULE = UI / "scripts" / "bloc-sans-js.mjs"

MELENCHON = {
    "mandats": [
        {"categorie": "mandat_electif", "label": "Mandat de député européen", "debut": "2014-07-01", "fin": "2017-06-18", "actif": False, "source_url": "https://www.europarl.europa.eu/meps/fr/96742"},
        {"categorie": "mandat_electif", "label": "Mandat de sénateur", "debut": "1986-10-02", "fin": "1995-10-01", "actif": False, "source_url": "https://www.senat.fr/senateur/86039k.html"},
        {"categorie": "commission", "label": "Commission des affaires étrangères", "debut": "2017-06-29", "fin": None, "actif": False, "source_url": None},
    ],
}
TONDELIER = {
    "mandats": [
        {"categorie": "mandat_local", "label": "Hénin-Beaumont", "debut": "2020-05-18", "fin": None, "actif": False, "source_url": "https://www.data.gouv.fr/datasets/elections-municipales-2026-maires-et-conseillers-municipaux-sortants"},
        {"categorie": "mandat_local", "label": "Hauts-De-France", "debut": "2021-07-02", "fin": None, "actif": True, "source_url": "https://www.data.gouv.fr/datasets/repertoire-national-des-elus-1"},
    ],
}
LIGNEE = {
    "id": "AN-SOC", "nom": "Socialistes", "chambre": "AN", "cumul": 96,
    "periode": {"debut": "2017-06-27", "fin": None},
    "maillons": [{"nom": "Nouvelle Gauche", "legislature": "15"}, {"nom": "Socialistes et apparentés", "legislature": "16"}],
}
GOUVERNEMENT = {
    "nom": "Gouvernement Lecornu II",
    "periode": {"debut": "2025-10-13", "fin": None, "actif": True},
    "membres": [
        {"nom": "Amélie de Montchalin", "portefeuille": "Ministère de l'action et des comptes publics", "debut": "2025-10-13", "fin": "2026-02-21", "actif": False},
        {"nom": "Annie Genevard", "portefeuille": "Ministère de l'agriculture", "debut": "2025-10-13", "fin": None, "actif": True},
    ],
}


def _node(corps: str) -> str:
    if shutil.which("node") is None:
        pytest.skip("node absent")
    script = f"import * as B from {json.dumps(MODULE.as_uri())};\n{corps}"
    res = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    return res.stdout


@pytest.fixture(scope="module")
def blocs() -> dict:
    donnees = json.dumps({"m": MELENCHON, "t": TONDELIER, "l": LIGNEE, "g": GOUVERNEMENT}, ensure_ascii=False)
    sortie = _node(
        f"const D = {donnees};\n"
        "console.log(JSON.stringify({\n"
        "  melenchon: B.blocCandidat({nom: 'Jean-Luc Mélenchon', parti: 'La France Insoumise (LFI)'}, D.m, '2026-09-17'),\n"
        "  tondelier: B.blocCandidat({nom: 'Marine Tondelier', parti: 'Les Écologistes'}, D.t, '2026-09-17'),\n"
        "  sans: B.blocCandidat({nom: 'Nathalie Arthaud', parti: 'Lutte Ouvrière (LO)'}, {mandats: []}, '2026-09-17'),\n"
        "  lignee: B.blocLignee(D.l, '2026-09-17'),\n"
        "  gouvernement: B.blocGouvernement(D.g, '2026-09-17'),\n"
        "}));"
    )
    return json.loads(sortie)


def test_un_mandat_termine_sans_date_de_fin_n_est_jamais_dit_en_cours(blocs):
    """#922/#966 : `fin` peut manquer sur un mandat clos — `actif` fait foi."""
    bloc = blocs["tondelier"]
    assert "Hénin-Beaumont — à partir du 18/05/2020, terminé — date de fin non publiée" in bloc
    assert "Hauts-De-France — depuis le 02/07/2021" in bloc


def test_la_fiche_sans_mandat_declare_la_limite_de_couverture(blocs):
    """La collecte des mandats locaux commence en 2020 (AGENTS.md §7)."""
    bloc = blocs["sans"]
    assert "La collecte des mandats locaux commence en 2020" in bloc
    assert "aucun mandat local" not in bloc.lower()


def test_seuls_les_mandats_et_fonctions_sont_publies(blocs):
    assert "Mandat de député européen — du 01/07/2014 au 18/06/2017" in blocs["melenchon"]
    assert "Commission des affaires" not in blocs["melenchon"], "une commission n'est pas un mandat publié ici"


def test_chaque_mandat_porte_sa_source_ou_dit_qu_elle_manque(blocs):
    assert '<a href="https://www.senat.fr/senateur/86039k.html">source</a>' in blocs["melenchon"]
    sortie = _node(
        "console.log(B.blocCandidat({nom:'X'}, {mandats:[{categorie:'mandat_electif', label:'M', debut:'2020-01-01',"
        " fin:'2021-01-01', actif:false, source_url:null}]}, '2026-09-17'));"
    )
    assert "source non publiée" in sortie


def test_aucun_compte_d_activite_ni_avertissement(blocs):
    """§2 règle 1 : un compte d'activité se lit comme un indicateur."""
    for cle in ("melenchon", "tondelier", "sans"):
        bas = blocs[cle].lower()
        for interdit in ("vote", "amendement", "intervention", "avertissement", "notable"):
            assert f"{interdit}s :" not in bas and f"{interdit} :" not in bas
        assert "avec javascript, les votes" in bas, "la phrase de pied nomme ce que JavaScript ajoute"


def test_le_groupe_et_le_gouvernement(blocs):
    assert "Groupe à l'Assemblée nationale · depuis le 27/06/2017 · 96 personnes y ont siégé" in blocs["lignee"]
    assert "Nouvelle Gauche — 15<sup>e</sup> législature" in blocs["lignee"]
    assert "depuis le 13/10/2025 · 2 membres" in blocs["gouvernement"]
    assert "Amélie de Montchalin — Ministère de l&#39;action et des comptes publics · du 13/10/2025 au 21/02/2026" in blocs["gouvernement"]


def test_la_date_du_build_est_ecrite(blocs):
    for bloc in blocs.values():
        assert "Faits publiés le 17/09/2026." in bloc


def test_le_bloc_vit_dans_le_conteneur_de_l_application():
    """Hors du conteneur, React ne le remplacerait pas : il resterait affiché."""
    sortie = _node(
        "console.log(B.avecBloc('<body><div id=\"root\"></div></body>', '<h1>Fiche</h1>'));"
    )
    assert sortie.strip() == '<body><div id="root"><h1>Fiche</h1></div></body>'
    absent = _node(
        "try { B.avecBloc('<body><div id=\"app\"></div></body>', 'x'); console.log('passe'); }"
        " catch (e) { console.log('erreur'); }"
    )
    assert absent.strip() == "erreur"


def test_le_conteneur_attendu_est_bien_celui_de_index_html():
    assert '<div id="root"></div>' in (UI / "index.html").read_text(encoding="utf-8")


def test_le_build_ecrit_les_blocs():
    script = (UI / "scripts" / "pages-par-adresse.mjs").read_text(encoding="utf-8")
    assert "bloc-sans-js.mjs" in script and "avecBloc(" in script
