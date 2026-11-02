"""Relecture à la source du stade et des dates des textes portés (#1248, lot 4).

Les pages sont des extraits verbatim de pages de dossier législatif de
l'Assemblée, relevées le 02/11/2026 : la frise des étapes (budget de la
Sécurité sociale 2026, une loi promulguée, une résolution adoptée
définitivement) et la phrase de dépôt d'un texte seulement déposé.
"""

import datetime as dt
import json
from pathlib import Path

import pytest

import relecture_textes_source as rt

FIXTURES = Path(__file__).parent / "fixtures" / "relecture_textes"


def _page(nom):
    return (FIXTURES / f"{nom}.html").read_text(encoding="utf-8")


def _publication(**champs):
    base = {"slug": "x", "stade": "depose", "sort": "depose", "date_min": None, "date_max": None}
    return rt.Publication(**{**base, **champs})


# ── La lecture de la page ────────────────────────────────────────────────────

def test_la_frise_du_budget_de_la_securite_sociale():
    c = rt.lire_chronologie(_page("dossier_plfss_2026"))
    assert c.depot == "2025-10-14"
    assert c.promulgation == "2025-12-30"
    assert max(c.dates) == "2025-12-30"
    assert not c.adopte_definitivement


def test_un_texte_seulement_depose_se_lit_dans_sa_phrase():
    c = rt.lire_chronologie(_page("dossier_depose"))
    assert (c.depot, c.dates, c.promulgation) == ("2026-07-23", ["2026-07-23"], None)


def test_l_adoption_definitive_se_lit():
    assert rt.lire_chronologie(_page("dossier_adopte_definitivement")).adopte_definitivement


def test_une_page_sans_rien_de_lisible_est_illisible():
    with pytest.raises(rt.PageIllisible):
        rt.lire_chronologie("<html><body>Maintenance</body></html>")


# ── Les quatre règles ───────────────────────────────────────────────────────

def test_un_rapporteur_nomme_avant_le_depot_n_est_pas_un_ecart():
    """Le budget de la Sécurité sociale 2026 : `date_min` au 02/07/2025, pour un
    dépôt au 14/10/2025. `date_min` est le premier acte du dossier, pas le dépôt."""
    c = rt.lire_chronologie(_page("dossier_plfss_2026"))
    publication = _publication(stade="promulgue", sort="adopte", date_min="2025-07-02", date_max="2025-12-30")
    assert rt.comparer(c, publication) == []


def test_un_debut_posterieur_au_depot_est_un_ecart():
    c = rt.lire_chronologie(_page("dossier_depose"))
    ecarts = rt.comparer(c, _publication(date_min="2026-08-01", date_max="2026-08-01"))
    assert [e["regle"] for e in ecarts] == ["dépôt"]


def test_une_etape_plus_recente_que_notre_derniere_date_est_un_ecart():
    c = rt.lire_chronologie(_page("dossier_plfss_2026"))
    ecarts = rt.comparer(c, _publication(stade="promulgue", sort="adopte",
                                          date_min="2025-10-14", date_max="2025-12-18"))
    assert [e["regle"] for e in ecarts] == ["fraîcheur"]


def test_une_etape_plus_recente_que_nos_dossiers_n_est_pas_un_ecart():
    """Le projet de loi constitutionnelle sur la Corse : deuxième lecture
    commencée le 28/10/2026, dossiers à jour au 26/10. Pas encore relue."""
    c = rt.Chronologie(depot="2026-04-27", dates=["2026-04-27", "2026-06-24", "2026-10-28"],
                       promulgation=None, adopte_definitivement=False)
    publication = _publication(stade="discute_seance", sort="navette_en_cours",
                               date_min="2026-04-27", date_max="2026-10-21")
    assert rt.comparer(c, publication, dossiers_a_jour_au="2026-10-26") == []
    assert [e["regle"] for e in rt.comparer(c, publication)] == ["fraîcheur"]


def test_une_promulgation_que_nous_ne_publions_pas_est_un_ecart():
    c = rt.lire_chronologie(_page("dossier_promulgue"))
    ecarts = rt.comparer(c, _publication(stade="adopte", sort="adopte",
                                          date_min="2024-04-12", date_max="2025-02-17"))
    assert [e["regle"] for e in ecarts] == ["promulgation"]


def test_une_promulgation_que_la_page_n_a_pas_est_un_ecart():
    c = rt.lire_chronologie(_page("dossier_depose"))
    ecarts = rt.comparer(c, _publication(stade="promulgue", date_min="2026-07-23", date_max="2026-07-23"))
    assert [e["regle"] for e in ecarts] == ["promulgation"]


def test_une_adoption_definitive_avec_un_sort_non_resolu_est_un_ecart():
    """La résolution sur les allocations chômage des frontaliers : la page dit
    « adopté définitivement », nous publions un `sort` nul (`fam_code_inconnu`)."""
    c = rt.lire_chronologie(_page("dossier_adopte_definitivement"))
    publication = _publication(stade="discute_seance", sort=None, date_min="2025-10-01", date_max="2026-03-16")
    assert [e["regle"] for e in rt.comparer(c, publication)] == ["adoption définitive"]
    assert rt.comparer(c, _publication(stade="discute_seance", sort="adopte",
                                       date_min="2025-10-01", date_max="2026-03-16")) == []


# ── Le corpus, le tirage, le bout à bout ────────────────────────────────────

def _profils(tmp_path):
    textes = {
        "a": [{"dossier_id": "DLR5L17N1", "source_url": "https://www.assemblee-nationale.fr/dyn/17/dossiers/un",
               "stade_procedural": "depose", "sort": "depose", "date_min": "2026-10-20", "date_max": "2026-10-20"},
              {"dossier_id": None, "source_url": "https://oeil.secure.europarl.europa.eu/x"}],
        "b": [{"dossier_id": "DLR5L17N1", "source_url": "https://www.assemblee-nationale.fr/dyn/17/dossiers/un",
               "stade_procedural": "depose", "sort": "depose", "date_min": "2026-10-20", "date_max": "2026-10-20"}],
    }
    for slug, liste in textes.items():
        (tmp_path / f"{slug}.pivot.json").write_text(json.dumps({"id": slug, "textes_portes": liste}))
    return sorted(tmp_path.glob("*.pivot.json"))


def test_un_dossier_rassemble_ses_publications_et_ecarte_les_textes_europeens(tmp_path):
    [dossier] = rt.dossiers_publies(_profils(tmp_path))
    assert dossier.dossier_id == "DLR5L17N1"
    assert [p.slug for p in dossier.publications] == ["a", "b"]


def test_sept_recents_puis_trois_sur_tout_le_corpus():
    dossiers = ([rt.Dossier(f"DLR5L17N{i}", "u", "2026-10-20") for i in range(30)]
                + [rt.Dossier(f"DLR5L15N{i}", "u", "2019-01-01") for i in range(300)])
    tirage = rt.tirer(dossiers, dt.date(2026, 11, 2), graine=1)
    assert len(tirage) == 10 and all(d.date_max == "2026-10-20" for d in tirage[:7])
    assert [d.dossier_id for d in rt.tirer(list(reversed(dossiers)), dt.date(2026, 11, 2), graine=1)] == \
        [d.dossier_id for d in tirage]


def test_bout_a_bout_et_page_injoignable(tmp_path):
    [dossier] = rt.dossiers_publies(_profils(tmp_path))
    dossier.publications = [_publication(slug="a", date_min="2026-07-23", date_max="2026-07-23")]
    [res] = rt.relire([dossier], obtenir=lambda _u: _page("dossier_depose"), delai=0)
    assert (res.non_verifie, res.publications, res.concordantes, res.ecarts) == (None, 1, 1, [])

    def panne(_url):
        raise ConnectionError("délai dépassé")

    [res] = rt.relire([dossier], obtenir=panne, delai=0)
    assert res.non_verifie.startswith("page injoignable") and res.ecarts == []
    _texte, resume = rt.rapport([res], graine=1)
    assert resume["dossiers_non_verifies"] == 1 and resume["ecarts"] == 0


def test_la_date_des_dossiers_se_lit_dans_le_fichier_de_fraicheur(tmp_path):
    chemin = tmp_path / "fraicheur_sources.json"
    chemin.write_text(json.dumps({"familles": {"an.dossiers": {"a_jour_au": "2026-10-26"}}}))
    assert rt.a_jour_au(chemin) == "2026-10-26"
    assert rt.a_jour_au(tmp_path / "absent.json") is None


# ── Le branchement dans le run ──────────────────────────────────────────────

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "generate-data.yml"


def _step(nom):
    texte = WORKFLOW.read_text(encoding="utf-8")
    debut = texte.index(f"      - name: {nom}\n")
    fin = texte.find("\n      - ", debut + 1)
    return texte[debut:fin]


def test_le_controle_tourne_dans_le_run_sans_bloquer():
    step = _step("Textes portés relus à la source (signalement)")
    assert "src/relecture_textes_source.py" in step
    assert "continue-on-error: true" in step and "github.run_id" in step


def test_le_run_ne_ferme_jamais_l_issue_des_textes():
    step = _step("Textes portés en écart avec la source — issue de suivi")
    assert "gh issue close" not in step
    assert "steps.commit.outputs.pushed == 'true'" in step
    assert "['ecarts']" in step
