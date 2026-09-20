"""Le roster brut ne se refetche pas : il transite (#518, second incident).

## Ce que ces tests protègent

#519 a ramené de 9 à **2** les fetchs de la même liste dans un run :
`prepare-roster-matrix` (→ artifact `roster-candidats`) et
`generate_group_profiles.py`, qui refetche pour son propre compte. C'est le
second qui a tué le run `32750929942`.

Ce n'est pas qu'une requête de trop, et le coût n'est pas l'argument principal :

- **fragilité** — les 5 groupes AN partagent la clé `('deputes','16')`, donc
  **un** fetch raté vaut 5 échecs, un step rouge et un commit skippé pour
  ~452 profils de candidats parfaitement collectés ;
- **correction** — la fiche de groupe publiée décrivait une composition lue
  ~7 min APRÈS celle qui a servi à collecter les profils. Une entrée ou une
  sortie de groupe entre les deux, et la composition publiée diverge du corpus
  collecté, **sans qu'aucune étape n'échoue**. Exactement le défaut que #518 a
  fermé pour le roster de candidats, laissé ouvert pour le roster brut.

Le repli par fetch est verrouillé lui aussi, et sa **granularité** avec : une
clé manquante retombe sur le fetch, un fichier illisible aussi — mais jamais en
silence, sans quoi le transit pourrait cesser de fonctionner sans que rien ne
le signale.
"""

import json
import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import generate_group_profiles
from generate_group_profiles import generate_all
from generate_roster_candidats import main as roster_main
from group_roster import (
    charger_rosters_bruts,
    cle_roster_texte,
    ecrire_rosters_bruts,
)

#: Ce fichier de tests lit la configuration committée nommée ci-dessous.
#: Le garde-fou de `conftest.py` refuse tout `.json` de `raw_data/` qu'un
#: test n'a pas déclaré (#791), et n'accepte la déclaration que si le chemin
#: est dans le `sparse-checkout` de `tests.yml` — sinon le test ne tournerait
#: qu'en local, sur ce qu'un run y a laissé.
pytestmark = pytest.mark.lit_reference_committee("raw_data/groupes_reels.json")


_MEMBRES_AN = [
    {"slug": "alice", "nom": "Alice", "groupe_sigle": "LR", "mandat_debut": "2022-06-22", "mandat_fin": None},
    {"slug": "bob", "nom": "Bob", "groupe_sigle": "SOC", "mandat_debut": "2022-06-22", "mandat_fin": None},
]

_GROUPE_AN = {
    "roster_chambre": "deputes", "groupe_id": "AN:LR", "groupe_sigle": "LR",
    "groupe_nom": "Les Républicains", "chambre": "AN", "legislature": "16",
    "fichier": "groupe-AN-LR-16.json",
}
_GROUPE_SENAT = {
    "roster_chambre": "senateurs", "groupe_id": "Senat:LR", "groupe_sigle": "LR",
    "groupe_nom": "Les Républicains", "chambre": "Senat", "legislature": None,
    "fichier": "groupe-Senat-LR.json",
}


@pytest.fixture(autouse=True)
def index_partages_absents(monkeypatch, tmp_path_factory):
    """Même précaution que test_generate_group_profiles.py (#473) : les chemins
    d'index sont des valeurs par défaut de paramètre, donc insensibles à un
    monkeypatch de la globale — sans ça, ces tests liraient les ~66 Mo du
    corpus vivant sans qu'une seule assertion n'en dépende."""
    from amendements_index import charger as charger_amendements_reel
    from scrutins_index import charger as charger_scrutins_reel

    absent = tmp_path_factory.mktemp("index-absents")
    monkeypatch.setattr(
        "generate_group_profiles.charger_scrutins",
        lambda _chemin: charger_scrutins_reel(absent / "scrutins.json"),
    )
    monkeypatch.setattr(
        "generate_group_profiles.charger_amendements",
        lambda _dossier, **kwargs: charger_amendements_reel(absent / "amendements", **kwargs),
    )


def _config(tmp_path, groupes):
    chemin = tmp_path / "groupes.json"
    chemin.write_text(json.dumps({"groupes": groupes}), encoding="utf-8")
    return chemin


# ---------------------------------------------------------------------------
# Le format de transit
# ---------------------------------------------------------------------------

def test_aller_retour_conserve_les_cles_et_la_matiere(tmp_path):
    """Aucune projection au passage : le consommateur doit appliquer
    `filter_roster_by_sigle` à la MÊME matière que le producteur, sans quoi le
    transit réintroduirait une divergence au lieu de la fermer."""
    chemin = tmp_path / "rosters_bruts.json"
    origine = {("deputes", "16"): _MEMBRES_AN, ("senateurs", None): [{"slug": "carla"}]}

    assert ecrire_rosters_bruts(chemin, origine) == 2
    assert charger_rosters_bruts(chemin) == origine


def test_une_legislature_absente_ne_se_confond_pas_avec_une_legislature_nommee():
    """`None` se sérialise en chaîne VIDE. `"None"` ou `"courante"` seraient des
    valeurs de législature possibles au relire — la clé Sénat et une 17e
    baptisée « courante » se retrouveraient dans le même seau."""
    assert cle_roster_texte("senateurs", None) == "senateurs:"
    assert cle_roster_texte("deputes", "16") == "deputes:16"
    assert cle_roster_texte("senateurs", None) != cle_roster_texte("senateurs", "courante")


def test_une_cle_en_echec_n_est_jamais_ecrite(tmp_path):
    """LE test de cette section.

    Un fetch raté (`None`) écrit en liste vide deviendrait, chez le
    consommateur, une composition de **0 membre** mesurée — la forme même de
    l'incident de #511. Son absence le fait retomber sur son propre fetch,
    ce qui est le mode dégradé voulu.
    """
    chemin = tmp_path / "rosters_bruts.json"
    assert ecrire_rosters_bruts(chemin, {("deputes", "16"): None}) == 0
    assert charger_rosters_bruts(chemin) == {}


def test_un_fichier_corrompu_leve_au_lieu_de_rendre_un_dict_vide(tmp_path):
    """« Fichier illisible » et « aucun roster » n'ont pas la même conséquence
    chez l'appelant : le premier doit refetcher, le second non."""
    chemin = tmp_path / "rosters_bruts.json"
    chemin.write_text(json.dumps({"rosters": ["pas", "un", "dict"]}), encoding="utf-8")
    with pytest.raises(ValueError):
        charger_rosters_bruts(chemin)

    chemin.write_text(json.dumps({"rosters": {"deputes:16": "pas une liste"}}), encoding="utf-8")
    with pytest.raises(ValueError):
        charger_rosters_bruts(chemin)


# ---------------------------------------------------------------------------
# Le producteur : generate_roster_candidats.py --rosters-bruts-out
# ---------------------------------------------------------------------------

def test_le_producteur_publie_le_roster_brut_avec_le_roster_de_candidats(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "generate_roster_candidats.fetch_full_roster",
        lambda *a, **k: list(_MEMBRES_AN),
    )
    bruts = tmp_path / "rosters_bruts.json"

    rc = roster_main([
        "--config", str(_config(tmp_path, [_GROUPE_AN])),
        "--out", str(tmp_path / "roster.json"),
        "--rosters-bruts-out", str(bruts),
    ])

    assert rc == 0
    assert charger_rosters_bruts(bruts) == {("deputes", "16"): _MEMBRES_AN}


def test_le_roster_brut_n_est_pas_ecrit_quand_le_roster_de_candidats_ne_l_est_pas(tmp_path, monkeypatch):
    """LE test de cette section.

    Les deux fichiers décrivent la même collecte, à la même seconde. Publier le
    brut malgré les anomalies rendrait au consommateur une composition de groupe
    qui n'est pas celle du corpus collecté — le défaut même que ce transit ferme
    (#511 pour la règle, #518 pour la conséquence).
    """
    monkeypatch.setattr(
        "generate_roster_candidats.fetch_full_roster",
        lambda *a, **k: (_ for _ in ()).throw(requests.Timeout("Read timed out")),
    )
    bruts = tmp_path / "rosters_bruts.json"

    rc = roster_main([
        "--config", str(_config(tmp_path, [_GROUPE_AN])),
        "--out", str(tmp_path / "roster.json"),
        "--rosters-bruts-out", str(bruts),
    ])

    assert rc == 1
    assert not bruts.exists()


def test_le_producteur_n_ecrit_rien_sans_le_drapeau(tmp_path, monkeypatch):
    """Non écrit par défaut : seul le run CI en a besoin, et un travail local ne
    doit pas salir l'arbre (même raison que `_manifest/`, #450)."""
    monkeypatch.setattr(
        "generate_roster_candidats.fetch_full_roster",
        lambda *a, **k: list(_MEMBRES_AN),
    )
    roster_main([
        "--config", str(_config(tmp_path, [_GROUPE_AN])),
        "--out", str(tmp_path / "roster.json"),
    ])
    assert not (tmp_path / "rosters_bruts.json").exists()


# ---------------------------------------------------------------------------
# Le consommateur : generate_group_profiles.py --rosters-bruts
# ---------------------------------------------------------------------------

def _sans_reseau(monkeypatch, appels):
    def interdit(chambre, legislature=None, session=None):
        appels.append((chambre, legislature))
        return list(_MEMBRES_AN)

    monkeypatch.setattr("generate_group_profiles.fetch_full_roster", interdit)


def test_le_consommateur_ne_fetche_plus_rien_quand_la_cle_est_fournie(tmp_path, monkeypatch):
    """LE test de ce fichier : c'est ce fetch-là qui a tué le run 32750929942."""
    appels = []
    _sans_reseau(monkeypatch, appels)
    bruts = tmp_path / "rosters_bruts.json"
    ecrire_rosters_bruts(bruts, {("deputes", "16"): _MEMBRES_AN})
    (tmp_path / "profiles").mkdir()
    out_dir = tmp_path / "groupes"
    out_dir.mkdir()

    resultat = generate_all(
        [_GROUPE_AN],
        profiles_dir=tmp_path / "profiles",
        out_dir=out_dir,
        rosters_bruts_path=bruts,
    )

    assert appels == []
    assert resultat.echecs == 0
    assert (out_dir / "groupe-AN-LR-16.json").exists()


def test_la_composition_publiee_est_celle_du_fichier_pas_celle_du_reseau(tmp_path, monkeypatch):
    """Le fetch rendrait `alice` (LR) ; le roster du run n'a que `zoe`. Si la
    fiche portait `alice`, le transit ne servirait à rien — c'est précisément la
    divergence de composition qu'il ferme."""
    appels = []
    _sans_reseau(monkeypatch, appels)
    bruts = tmp_path / "rosters_bruts.json"
    ecrire_rosters_bruts(bruts, {("deputes", "16"): [
        {"slug": "zoe", "nom": "Zoé", "groupe_sigle": "LR", "mandat_debut": "2022-06-22", "mandat_fin": None},
    ]})
    (tmp_path / "profiles").mkdir()
    out_dir = tmp_path / "groupes"
    out_dir.mkdir()

    generate_all(
        [_GROUPE_AN],
        profiles_dir=tmp_path / "profiles",
        out_dir=out_dir,
        rosters_bruts_path=bruts,
    )

    fiche = json.loads((out_dir / "groupe-AN-LR-16.json").read_text(encoding="utf-8"))
    couverture = fiche["meta"]["couverture_roster"]
    assert couverture["roster_total"] == 1
    assert appels == []


def test_une_cle_absente_du_fichier_retombe_sur_le_fetch(tmp_path, monkeypatch):
    """Granularité du repli : par clé, pas par fichier. Le Sénat suspendu (#516)
    n'est plus dans le roster du run, l'AN oui — le second ne doit pas payer
    pour l'absence du premier."""
    appels = []
    _sans_reseau(monkeypatch, appels)
    bruts = tmp_path / "rosters_bruts.json"
    ecrire_rosters_bruts(bruts, {("deputes", "16"): _MEMBRES_AN})
    (tmp_path / "profiles").mkdir()
    out_dir = tmp_path / "groupes"
    out_dir.mkdir()

    generate_all(
        [_GROUPE_AN, _GROUPE_SENAT],
        profiles_dir=tmp_path / "profiles",
        out_dir=out_dir,
        rosters_bruts_path=bruts,
    )

    assert appels == [("senateurs", None)]


def test_un_fichier_illisible_refetche_mais_jamais_en_silence(tmp_path, monkeypatch, capsys):
    """Un transit qui cesse de fonctionner sans rien dire redevient deux fetchs
    à des instants différents, c'est-à-dire le défaut de départ."""
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    appels = []
    _sans_reseau(monkeypatch, appels)
    bruts = tmp_path / "rosters_bruts.json"
    bruts.write_text("{ pas du json", encoding="utf-8")
    (tmp_path / "profiles").mkdir()
    out_dir = tmp_path / "groupes"
    out_dir.mkdir()

    generate_all(
        [_GROUPE_AN],
        profiles_dir=tmp_path / "profiles",
        out_dir=out_dir,
        rosters_bruts_path=bruts,
    )

    assert appels == [("deputes", "16")]
    annotations = [l for l in capsys.readouterr().out.splitlines() if l.startswith("::warning::")]
    assert any("ROSTER_BRUT" in a for a in annotations), annotations


def test_sans_le_drapeau_le_comportement_est_celui_d_avant(tmp_path, monkeypatch):
    """Un appel local sans roster du run fetche, comme toujours."""
    appels = []
    _sans_reseau(monkeypatch, appels)
    (tmp_path / "profiles").mkdir()
    out_dir = tmp_path / "groupes"
    out_dir.mkdir()

    generate_all([_GROUPE_AN], profiles_dir=tmp_path / "profiles", out_dir=out_dir)

    assert appels == [("deputes", "16")]


def test_le_drapeau_cli_est_cable_sur_generate_all(tmp_path, monkeypatch):
    """`--rosters-bruts` peut exister et n'être branché sur rien."""
    vus = {}
    monkeypatch.setattr(
        generate_group_profiles,
        "generate_all",
        lambda *a, **k: vus.update(k) or generate_group_profiles.ResultatGeneration([], [], {}),
    )
    generate_group_profiles.main([
        "--config", str(_config(tmp_path, [_GROUPE_AN])),
        "--profiles-dir", str(tmp_path / "profiles"),
        "--out-dir", str(tmp_path / "groupes"),
        "--rosters-bruts", str(tmp_path / "rosters_bruts.json"),
    ])
    assert vus["rosters_bruts_path"] == tmp_path / "rosters_bruts.json"
