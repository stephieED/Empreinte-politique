"""La frise de /couverture : des segments pleins, et le Sénat comme institution.

Deux changements du 15/09/2026, tenus ici parce qu'ils sont tous deux des
ARBITRAGES et non des détails d'écriture.

1. UN SEGMENT PAR RAIL, de la première à la dernière donnée. Il y en avait un
   par mois porteur, les mois consécutifs fusionnés. Les blancs entre eux ne
   parlaient pas de la source mais des mois où aucun candidat déclaré n'était en
   fonction là — 73 pour les textes portés de l'Assemblée — et sur une page qui
   s'appelle « Ce que le dépôt porte, et depuis quand », ils se lisaient comme
   des lacunes de collecte.

2. LE SÉNAT EST UNE INSTITUTION, avec ses cinq listes. Il portait un rail unique
   en jaune et le compte « 7 · 2 candidats » : les sept mandats électifs seuls,
   les 126 organes n'étant comptés nulle part.

Le jaune disparaît de la page avec lui, et c'est le point le plus facile à
défaire de bonne foi : voir `test_le_jaune_ne_revient_pas_sans_sa_raison`.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
UI = RACINE / "web" / "UI_finale"
GENERATEUR = UI / "scripts" / "couverture-corpus.mjs"
FRISE = UI / "src" / "components" / "FriseCouverture.jsx"
FRISE_CSS = UI / "src" / "components" / "FriseCouverture.css"


@pytest.fixture(scope="module")
def frise() -> str:
    return FRISE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def generateur() -> str:
    return GENERATEUR.read_text(encoding="utf-8")


# ── Le segment ──────────────────────────────────────────────────────────────


def test_le_generateur_rend_deux_dates_et_non_des_tranches(generateur: str) -> None:
    assert "export function etendue(" in generateur
    assert "tranchesMensuelles" not in generateur, (
        "les tranches mensuelles répondaient à « quand nos gens étaient en "
        "fonction », pas à « depuis quand la source est lue »"
    )
    assert generateur.count("etendue: etendue(") == 2, (
        "les deux constructeurs — couche et apport — portent l'étendue"
    )


def test_un_champ_sans_aucune_date_ne_porte_pas_de_segment() -> None:
    """Un champ à zéro rendrait un segment de largeur nulle : un trait fantôme.

    Le corpus en porte : `avec un lien vers la source` vaut 0 sur les 168 711
    amendements de l'Assemblée.
    """
    if shutil.which("node") is None:
        pytest.skip("node absent")
    script = f"""
    const {{ etendue }} = await import({json.dumps(GENERATEUR.as_uri())});
    console.log(JSON.stringify({{
      vide: etendue([]),
      nuls: etendue([null, undefined, '']),
      une: etendue(['2019-03-14']),
      plusieurs: etendue(['2021-05-02', '2019-03-14', '2024-11-30']),
    }}));
    """
    res = subprocess.run(["node", "--input-type=module", "-e", script],
                         capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    out = json.loads(res.stdout.strip().splitlines()[-1])
    assert out["vide"] is None
    assert out["nuls"] is None
    assert out["une"] == ["2019-03-01", "2019-03-28"]
    assert out["plusieurs"] == ["2019-03-01", "2024-11-28"]


def test_un_segment_qui_commence_avant_l_axe_est_marque(frise: str, ) -> None:
    """Le Sénat porte un mandat depuis octobre 1986, `AXE_DEBUT` vaut 2000.

    Un bord arrondi collé au zéro dirait « commence en 2000 » — l'erreur exacte
    que #940 a corrigée sur la borne de l'Assemblée, à l'envers.
    """
    assert "fc-seg--tronque" in frise
    assert "< AXE_DEBUT" in frise, "la troncature se déduit de l'axe, jamais d'une date en dur"
    css = FRISE_CSS.read_text(encoding="utf-8")
    assert ".fc-seg--tronque" in css
    assert "border-top-left-radius: 0" in css, "le bord sectionné perd son arrondi"


# ── Le Sénat ────────────────────────────────────────────────────────────────


def test_le_senat_est_une_institution_avec_ses_cinq_listes(generateur: str) -> None:
    assert "cle: 'Senat'" in generateur
    assert "estMandatSenatorial" in generateur
    assert "TITRE_LISTE" in generateur, (
        "une liste vide doit être NOMMÉE comme les autres, sinon le lecteur ne "
        "sait pas ce qui manque"
    )


def test_les_quatre_listes_senatoriales_sont_non_publiees_et_non_pas_non_collectees(
    generateur: str,
) -> None:
    """La distinction que cette frise existe pour porter.

    `src/senat_opendata.py` lit 24 des 93 tables de l'export : aucune ne porte
    de scrutin, de compte rendu, d'amendement ni de texte. Les trois tables
    refusées à l'entrée sont de la présence et des procurations (§2 règle 3) —
    elles ne nourrissent aucune de nos cinq listes. Le jaune dirait « nous ne
    l'avons pas fait » : un fait faux sur nous.
    """
    bloc = generateur[generateur.index("cle: 'Senat'"):]
    assert "nonPublie:" in bloc
    assert "93 tables" in bloc or "93" in bloc, "la raison est écrite, pas supposée"


def test_le_senat_quitte_le_bloc_des_lignes_sans_activite(frise: str) -> None:
    sans = re.search(r"const SANS_ACTIVITE = \[(.*?)\];", frise, re.DOTALL)
    assert sans, "SANS_ACTIVITE a disparu ou changé de forme"
    assert "Senat" not in sans.group(1)
    assert "local" in sans.group(1), "les mandats locaux gardent leur ligne unique : ils ne sont pas une institution (#922)"


# ── Le jaune ────────────────────────────────────────────────────────────────


def test_le_jaune_ne_revient_pas_sans_sa_raison(frise: str) -> None:
    """La clé « Données non collectées » est retirée de la LÉGENDE, pas du CSS.

    Elle n'illustrait plus aucune ligne : une légende décrit ce qui est à
    l'écran. La règle, elle, tient toujours — un trou de NOTRE fait se dit en
    jaune. Le style reste disponible pour le jour où le premier cas réapparaît.
    """
    legende = frise[frise.index("fc-legende"):]
    assert "fc-cle--nonc" not in legende, (
        "aucune ligne n'emploie le jaune : une clé sans occurrence se lit comme "
        "un élément qu'on n'a pas su trouver"
    )
    assert "fc-cle--hors" in legende
    css = FRISE_CSS.read_text(encoding="utf-8")
    assert ".fc-cle--nonc" in css, "le style reste, la règle aussi"
    assert ".fc-noncollecte" in css


def test_la_cle_des_donnees_collectees_montre_les_quatre_teintes() -> None:
    css = FRISE_CSS.read_text(encoding="utf-8")
    cle = css[css.index(".fc-cle--collecte"):]
    cle = cle[:cle.index("}")]
    for teinte in ("--fc-an", "--fc-gouv", "--fc-pe", "--fc-senat", "--fc-local"):
        assert teinte in cle, f"{teinte} manque à la clé : elle montre ce qui est à l'écran"


def test_la_sarcelle_du_senat_est_retenue_avec_sa_mesure() -> None:
    """Elle est à 67° du bleu de l'Union, sous le seuil de 72° de DESIGN_SYSTEM §2.

    Retenue malgré ce critère, sur la mesure qui compte pour un lecteur : sous
    daltonisme, Europe/Sénat est la paire LA PLUS séparée des six. Le commentaire
    porte la mesure pour qu'une session future ne la retire pas au nom du seul
    seuil, sans savoir qu'il a été pesé.
    """
    css = FRISE_CSS.read_text(encoding="utf-8")
    assert "--fc-senat: #169E9E" in css
    assert "67°" in css, "l'écart au seuil est écrit, pas tu"
    assert "daltonisme" in css, "la mesure qui a emporté la décision est écrite"
