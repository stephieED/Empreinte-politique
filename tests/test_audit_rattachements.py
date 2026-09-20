"""Un taux de rattachement se publie avec sa population, et ne bloque jamais.

Ce module mesure ce que le dépôt a dû ÉTABLIR lui-même : aucun de ces liens
n'est donné par la source. Il se distingue d'`audit_integrite_referentielle` sur
un point que ces tests verrouillent — celui-là vérifie une propriété **binaire**
(une clé résout, ou c'est un bug, et ça bloque), celui-ci un **taux**, dont la
valeur basse est le plus souvent le silence de la source.

Les mélanger ferait lire les silences comme des fautes, et diluerait les fautes
dans un tableau de taux.

CE QUE CES GARDE-FOUS PROTÈGENT SURTOUT : qu'un taux ne soit jamais publié seul.
Le MÊME rattachement vaut 4 % ou 61 % selon le dénominateur — 714 scrutins sur
17 762 publiés, mais 423 sur les 697 textes en dernière lecture. Un taux sans sa
population est une erreur, pas une approximation (AGENTS.md §9).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "tests"))

import audit_pipeline  # noqa: E402
from audit_rattachements import audit_rattachements  # noqa: E402


@pytest.fixture
def corpus(tmp_path: Path) -> Path:
    """Un corpus minuscule, écrit à la main — aucun test ne lit le corpus vivant (#473)."""
    pivot = tmp_path / "pivot_data"
    (pivot / "amendements").mkdir(parents=True)
    (pivot / "profiles").mkdir()
    (pivot / "amendements" / "17.json").write_text(
        json.dumps({
            "legislature": "17",
            "textes": {
                "T1": {"dossier_id": "D1", "titre": "Un texte"},
                "T2": {"dossier_id": None, "titre": "Sans dossier"},
            },
            "amendements": {
                "a1": {"texte_vise": "T1"},
                "a2": {"texte_vise": "T2"},
                "a3": {"texte_vise": "INCONNU"},
                "a4": {"texte_vise": None},
            },
        }),
        encoding="utf-8",
    )
    (pivot / "commissions_dossiers.json").write_text(
        json.dumps({"commissions": {"D1": {"sigle": "Lois"}}}), encoding="utf-8"
    )
    (pivot / "scrutins_dossiers.json").write_text(
        json.dumps({"scrutins": {"an:17:1": "D1"}, "dossiers": {"D1": {"statut": "adopte"}}}),
        encoding="utf-8",
    )
    (pivot / "scrutins.json").write_text(
        json.dumps({"scrutins": [{"id": "an:17:1"}, {"id": "an:17:2"}, {"id": "an:17:3"}]}),
        encoding="utf-8",
    )
    (pivot / "profiles" / "x.pivot.json").write_text(
        json.dumps({"textes_portes": [
            {"dossier_id": "D1"},
            {"dossier_id": "D9"},
            {"dossier_id": None},
        ]}),
        encoding="utf-8",
    )
    return pivot


def _par_cle(rapport: dict) -> dict:
    return {j["cle"]: j for j in rapport["jointures"]}


# ---------------------------------------------------------------------------
# 1. Ce que chaque jointure mesure
# ---------------------------------------------------------------------------

def test_les_deux_crans_de_l_index_amendements_sont_mesures_separement(corpus):
    """Un amendement peut viser un texte non nommé ; un texte nommé peut n'avoir
    aucun dossier. Les fondre masquerait celui des deux qui décroche."""
    j = _par_cle(audit_rattachements(corpus))
    assert (j["amendement_vers_texte_vise.17"]["resolus"],
            j["amendement_vers_texte_vise.17"]["total"]) == (2, 4)
    assert (j["texte_vise_vers_dossier.17"]["resolus"],
            j["texte_vise_vers_dossier.17"]["total"]) == (1, 2)


def test_le_dossier_amende_est_confronte_a_la_table_des_commissions(corpus):
    j = _par_cle(audit_rattachements(corpus))
    assert (j["dossier_amende_vers_commission"]["resolus"],
            j["dossier_amende_vers_commission"]["total"]) == (1, 1)


def test_le_scrutin_est_confronte_a_la_table_des_dossiers(corpus):
    j = _par_cle(audit_rattachements(corpus))["scrutin_vers_dossier"]
    assert (j["resolus"], j["total"]) == (1, 3)


def test_le_texte_porte_est_mesure_sur_deux_crans(corpus):
    """Porter un `dossier_id` et résoudre une commission sont deux choses."""
    j = _par_cle(audit_rattachements(corpus))
    assert (j["texte_porte_vers_dossier"]["resolus"],
            j["texte_porte_vers_dossier"]["total"]) == (2, 3)
    assert (j["texte_porte_vers_commission"]["resolus"],
            j["texte_porte_vers_commission"]["total"]) == (1, 3)


# ---------------------------------------------------------------------------
# 2. Un taux ne se publie jamais seul
# ---------------------------------------------------------------------------

def test_chaque_jointure_porte_ses_deux_termes_et_sa_population(corpus):
    """§2 règle 7 : numérateur ET dénominateur. §9 : la population est nommée."""
    for j in audit_rattachements(corpus)["jointures"]:
        assert isinstance(j["resolus"], int) and isinstance(j["total"], int)
        assert j["resolus"] <= j["total"], f"{j['cle']} : plus de résolus que de total"
        assert j["population"] and j["population"].strip(), (
            f"{j['cle']} publie un taux sans nommer sa population"
        )


def test_le_taux_est_nul_quand_le_denominateur_l_est(tmp_path):
    """Zéro sur zéro n'est pas 100 % — c'est rien du tout."""
    (tmp_path / "amendements").mkdir(parents=True)
    (tmp_path / "amendements" / "17.json").write_text(
        json.dumps({"legislature": "17", "textes": {}, "amendements": {}}), encoding="utf-8"
    )
    j = _par_cle(audit_rattachements(tmp_path))
    assert j["amendement_vers_texte_vise.17"]["taux"] is None


# ---------------------------------------------------------------------------
# 3. Rapporter n'est pas bloquer
# ---------------------------------------------------------------------------

def test_le_module_se_declare_non_bloquant(corpus):
    """Un taux bas est le plus souvent le silence de la source, pas une faute."""
    assert audit_rattachements(corpus)["bloquant"] is False


def test_un_fichier_absent_est_nomme_et_ne_leve_rien(tmp_path):
    """Un corpus vide rend un rapport, jamais une exception : l'absence se
    déclare (§2 règle 5)."""
    rapport = audit_rattachements(tmp_path)
    assert rapport["jointures"] == []
    assert "pivot_data/commissions_dossiers.json" in rapport["fichiers_absents"]
    assert "pivot_data/scrutins_dossiers.json" in rapport["fichiers_absents"]


def test_un_json_illisible_ne_fait_pas_echouer_l_audit(tmp_path):
    (tmp_path / "commissions_dossiers.json").write_text("{ pas du json", encoding="utf-8")
    assert "pivot_data/commissions_dossiers.json" in audit_rattachements(tmp_path)["fichiers_absents"]


# ---------------------------------------------------------------------------
# 4. Le rendu, et ce qu'il doit dire au lecteur
# ---------------------------------------------------------------------------

def test_le_rendu_nomme_la_population_de_chaque_taux(corpus):
    md = audit_pipeline._md_section_rattachements(audit_rattachements(corpus))
    assert "Population" in md
    assert "amendements publiés, législature 17" in md
    assert "2 / 4" in md, "le couple numérateur/dénominateur n'est pas affiché"


def test_le_rendu_dit_qu_il_ne_bloque_pas_et_renvoie_a_l_integrite(corpus):
    """Sans ça, un taux de 4 % se lit comme une alarme."""
    md = audit_pipeline._md_section_rattachements(audit_rattachements(corpus))
    assert "ne bloque jamais" in md
    assert "audit_integrite_referentielle" in md


def test_la_section_est_dans_le_rapport_assemble():
    """Un module qui n'est pas rendu n'est mesuré par personne."""
    source = (RACINE / "src" / "audit_pipeline.py").read_text(encoding="utf-8")
    assert "audit_rattachements.audit_rattachements(profiles_dir.parent)" in source, (
        "le CLI ne mesure plus les rattachements, ou ne les fait plus lire le "
        "dossier pointé par --profiles-dir : il lirait le corpus vivant (§3b)"
    )
    assert '_md_section_rattachements(rapport.get("audit_rattachements")' in source


def test_build_report_ne_lit_jamais_le_corpus_vivant(corpus):
    """Il ASSEMBLE, il ne calcule pas — c'est son contrat, et c'est §3b.

    Le calculer dedans faisait scanner 509 744 amendements à chacun des trois
    appels de `test_audit_pipeline.py` : la suite passait de 60 s à 185 s, et
    aucun test ne doit lire le corpus vivant.
    """
    from test_audit_pipeline import (  # réutilise les stubs déjà écrits
        _rapport_gouvernements,
        _rapport_groupes,
        _rapport_profils,
    )

    appels = []
    import audit_rattachements as ar

    original = ar.audit_rattachements
    ar.audit_rattachements = lambda *a, **k: appels.append(1) or {}
    try:
        rapport = audit_pipeline.build_report(
            _rapport_profils(), _rapport_groupes(), _rapport_gouvernements()
        )
    finally:
        ar.audit_rattachements = original
    assert appels == [], "`build_report` a calculé les rattachements lui-même"
    assert rapport["audit_rattachements"] == {}


def test_la_section_passee_en_argument_est_rendue_telle_quelle(corpus):
    from test_audit_pipeline import (
        _rapport_gouvernements,
        _rapport_groupes,
        _rapport_profils,
    )

    mesure = audit_rattachements(corpus)
    rapport = audit_pipeline.build_report(
        _rapport_profils(), _rapport_groupes(), _rapport_gouvernements(), mesure
    )
    assert rapport["audit_rattachements"] is mesure
