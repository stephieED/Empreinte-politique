"""Relecture à la source des positions de vote publiées (#1248).

La page de scrutin est un extrait copié des pages réelles de l'Assemblée
(scrutins 8700 et 3305, relevés le 30/10/2026), pas une page imaginée : c'est
sur la vraie page que la première version comptait comme « non nommé » un
votant dont le nom n'est pas un lien.
"""

import datetime as dt
from pathlib import Path

import pytest

import relecture_votes_source as rv

EXTRAIT = Path(__file__).parent / "fixtures" / "relecture_votes" / "scrutin_extrait.html"


@pytest.fixture(scope="module")
def page():
    return rv.lire_page(EXTRAIT.read_text(encoding="utf-8"))


# ── La lecture de la page ────────────────────────────────────────────────────

def test_les_quatre_listes_sont_lues(page):
    assert {p for p, _ in page.values()} == {"pour", "contre", "abstention", "non_votant"}
    assert page["PA721158"] == ("contre", "M. Pieyre-Alexandre Anglade")
    assert page["PA721908"] == ("non_votant", "Mme Yaël Braun-Pivet")


def test_un_votant_sans_lien_est_nomme(page):
    """Scrutin 3305 : Manon Bouquin est écrite en texte, sans lien vers sa fiche."""
    assert page["PA841131"] == ("pour", "Mme Manon Bouquin")


def test_la_lecture_s_arrete_aux_mises_au_point(page):
    """Ce qu'un député dit avoir voulu voter n'est pas le vote enregistré."""
    assert "PA999999" not in page


def test_un_intitule_inconnu_rend_la_page_illisible():
    html = EXTRAIT.read_text(encoding="utf-8").replace(">Contre</span>", ">Contre (délégation)</span>")
    with pytest.raises(rv.PageIllisible, match="intitulé"):
        rv.lire_page(html)


def test_une_page_sans_votant_est_illisible():
    with pytest.raises(rv.PageIllisible, match="aucun votant"):
        rv.lire_page("<html><body>Maintenance</body></html>")


# ── Le tirage : 7 récents, 3 sur tout le corpus (arbitré le 30/10/2026) ──────

def _scrutins(nb_recents, nb_anciens):
    recents = [{"id": f"an:17:{i}", "date": "2026-10-20", "source_url": f"u{i}"} for i in range(nb_recents)]
    anciens = [{"id": f"an:15:{i}", "date": "2019-01-01", "source_url": f"v{i}"} for i in range(nb_anciens)]
    return recents + anciens


def test_sept_recents_puis_trois_sur_tout_le_corpus():
    tirage = rv.tirer(_scrutins(50, 500), dt.date(2026, 10, 30), graine=1)
    assert len(tirage) == 10
    assert all(s["date"] == "2026-10-20" for s in tirage[:7])
    assert len({s["id"] for s in tirage}) == 10


def test_moins_de_sept_recents_le_reste_vient_du_corpus():
    tirage = rv.tirer(_scrutins(2, 500), dt.date(2026, 10, 30), graine=1)
    assert len(tirage) == 10
    assert sum(s["date"] == "2026-10-20" for s in tirage) >= 2


def test_le_tirage_se_rejoue_a_l_identique():
    a = rv.tirer(_scrutins(50, 500), dt.date(2026, 10, 30), graine=42)
    b = rv.tirer(list(reversed(_scrutins(50, 500))), dt.date(2026, 10, 30), graine=42)
    assert [s["id"] for s in a] == [s["id"] for s in b]


def test_un_scrutin_sans_adresse_n_est_pas_tire():
    scrutins = _scrutins(0, 5) + [{"id": "an:17:x", "date": "2026-10-20", "source_url": None}]
    assert "an:17:x" not in {s["id"] for s in rv.tirer(scrutins, dt.date(2026, 10, 30), graine=1)}


# ── La comparaison, personne par personne ───────────────────────────────────

PAGE = {
    "PA1": ("pour", "A"),
    "PA2": ("contre", "B"),
    "PA3": ("pour", "C"),        # profil, aucune position publiée
    "PA4": ("pour", "D"),        # aucun profil : non-inscrit
    "PA5": ("non_votant", "E"),  # profil, aucune position : l'archive ne le cite pas
}


def test_chaque_cas_a_son_verdict():
    publiees = {"PA1": "pour", "PA2": "pour", "PA6": "contre", "PA7": "absent"}
    concordants, hors, divergences, ecarts = rv.comparer(
        PAGE, publiees, {"PA1", "PA2", "PA3", "PA5", "PA6", "PA7"}
    )
    assert concordants == 1
    assert hors == ["D (PA4)"]
    assert [d["acteur"] for d in divergences] == ["PA5"]
    assert {(e["acteur"], e["page"], e["publie"]) for e in ecarts} == {
        ("PA2", "contre", "pour"),   # position différente
        ("PA3", "pour", None),       # position manquante chez nous
        ("PA6", None, "contre"),     # position que la page ne nomme pas
    }


def test_un_absent_publie_ne_se_compare_pas():
    """La page ne liste pas les absents (§2 règle 3) : rien à confronter."""
    _c, _h, _d, ecarts = rv.comparer({}, {"PA7": "absent", "PA8": "excuse"}, {"PA7", "PA8"})
    assert ecarts == []


def test_la_divergence_ne_vaut_que_pour_les_non_votants():
    """Un « pour » absent chez nous reste un écart, jamais une divergence."""
    _c, _h, divergences, ecarts = rv.comparer({"PA3": ("pour", "C")}, {}, {"PA3"})
    assert divergences == [] and len(ecarts) == 1


# ── Une source muette n'est pas un écart (§2 règle 5) ───────────────────────

def test_une_page_injoignable_est_non_verifiee():
    def panne(_url):
        raise ConnectionError("délai dépassé")

    tirage = [{"id": "an:17:1", "date": "2026-10-20", "source_url": "u"}]
    [res] = rv.relire(tirage, {}, set(), "2026-09-30", obtenir=panne, delai=0)
    assert res.non_verifie.startswith("page injoignable")
    assert res.ecarts == []
    texte, resume = rv.rapport([res], graine=1)
    assert resume["scrutins_non_verifies"] == 1 and resume["positions_en_ecart"] == 0


def test_le_rapport_compte_ce_qu_il_affiche(page):
    tirage = [{"id": "an:17:8700", "date": "2026-10-12", "source_url": "u"}]
    publiees = {"an:17:8700": {acteur: pos for acteur, (pos, _n) in page.items() if acteur != "PA721908"}}
    avec_profil = set(page)
    html = EXTRAIT.read_text(encoding="utf-8")
    [res] = rv.relire(tirage, publiees, avec_profil, "2026-09-30", obtenir=lambda _u: html, delai=0)
    texte, resume = rv.rapport([res], graine=7)
    assert resume["positions_concordantes"] == len(page) - 1
    assert resume["positions_en_ecart"] == 0
    assert resume["divergences_entre_sources"] == 1
    assert "Divergences entre sources" in texte and "graine 7" in texte


# ── Le branchement dans le run ──────────────────────────────────────────────

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "generate-data.yml"


def _step(nom: str) -> str:
    texte = WORKFLOW.read_text(encoding="utf-8")
    debut = texte.index(f"      - name: {nom}\n")
    fin = texte.find("\n      - ", debut + 1)
    return texte[debut:fin]


def test_le_controle_tourne_dans_le_run_sans_bloquer():
    step = _step("Votes relus à la source (signalement)")
    assert "src/relecture_votes_source.py" in step
    assert "continue-on-error: true" in step
    assert "github.run_id" in step, "la graine est le numéro du run"


def test_le_run_ne_ferme_jamais_l_issue_des_votes():
    """Un tirage sans écart ne dit rien des scrutins qu'il n'a pas tirés."""
    step = _step("Votes en écart avec la source — issue de suivi")
    assert "gh issue close" not in step
    assert "steps.commit.outputs.pushed == 'true'" in step
    assert "positions_en_ecart" in step
