"""Relecture à la source des signataires d'amendements publiés (#1248, lot 3).

Les pages sont des extraits verbatim du bloc « Déposé par » de deux pages
d'amendement de l'Assemblée, relevées le 02/11/2026 : un amendement de la XVIe
à sept cosignataires (Ugo Bernalicis), et un amendement de rapporteur de la
XVIIe (Bruno Fuchs, sans cosignataire).
"""

import datetime as dt
import json
from pathlib import Path

import pytest

import relecture_amendements_source as ra

FIXTURES = Path(__file__).parent / "fixtures" / "relecture_amendements"
UID_16 = "an:AMANR5L16PO791932B0760P0D1N002711"
#: Ce que l'index publié de la XVIe porte pour cet amendement, relevé le 02/11/2026.
COSIGNATAIRES_16 = ["an:PA795588", "an:PA795596", "an:PA342384", "an:PA719578",
                    "an:PA794130", "an:PA791824", "an:PA795136"]


def _page(nom):
    return (FIXTURES / nom).read_text(encoding="utf-8")


# ── La lecture de la page ────────────────────────────────────────────────────

def test_le_premier_signataire_puis_les_cosignataires_dans_l_ordre():
    premier, cosignataires = ra.lire_signataires(_page("amendement_16_0760_2711.html"))
    assert premier == "an:PA720430"
    assert cosignataires == COSIGNATAIRES_16


def test_un_amendement_de_rapporteur_sans_cosignataire():
    assert ra.lire_signataires(_page("amendement_17_rapporteur.html")) == ("an:PA722284", [])


def test_une_page_sans_bloc_depose_par_est_illisible():
    with pytest.raises(ra.PageIllisible, match="Déposé par"):
        ra.lire_signataires("<html><body>Maintenance</body></html>")


def test_les_liens_apres_le_bloc_ne_sont_pas_lus():
    html = _page("amendement_17_rapporteur.html") + '<a href="/dyn/deputes/PA999999">Un autre député</a>'
    assert ra.lire_signataires(html) == ("an:PA722284", [])


# ── Le tirage ────────────────────────────────────────────────────────────────

def _amendements():
    recents = [ra.Amendement(f"an:AMANR5L17X{i:04d}", "17", "2026-10-20", "an:PA1", []) for i in range(50)]
    anciens = [ra.Amendement(f"an:AMANR5L15X{i:04d}", "15", "2019-01-01", "an:PA2", []) for i in range(500)]
    return recents + anciens


def test_sept_recents_puis_trois_sur_tout_le_corpus():
    tirage = ra.tirer(_amendements(), dt.date(2026, 11, 2), graine=1)
    assert len(tirage) == 10 and len({a.uid for a in tirage}) == 10
    assert all(a.date == "2026-10-20" for a in tirage[:7])


def test_le_tirage_se_rejoue_a_l_identique():
    a = [x.uid for x in ra.tirer(_amendements(), dt.date(2026, 11, 2), graine=42)]
    b = [x.uid for x in ra.tirer(list(reversed(_amendements())), dt.date(2026, 11, 2), graine=42)]
    assert a == b


def test_la_xive_n_est_pas_tiree():
    """Sa page répond 404 quand on la demande par identifiant (02/11/2026)."""
    assert "14" not in ra.LEGISLATURES


# ── La comparaison : l'index et les profils ─────────────────────────────────

AMENDEMENT = ra.Amendement(UID_16, "16", "2023-01-23", "an:PA720430", COSIGNATAIRES_16)
SLUGS = {"an:PA720430": "ugo-bernalicis", "an:PA795588": "membre-a", "an:PA795596": "membre-b"}


def _roles(**surcharges):
    roles = {"ugo-bernalicis": {UID_16: "auteur_principal"},
             "membre-a": {UID_16: "cosignataire"},
             "membre-b": {UID_16: "cosignataire"}}
    roles.update(surcharges)
    return roles


def test_tout_concorde():
    concordants, hors, ecarts = ra.comparer(AMENDEMENT, "an:PA720430", COSIGNATAIRES_16, SLUGS, _roles())
    assert (concordants, len(hors), ecarts) == (3, 5, [])


def test_un_cosignataire_absent_de_l_index_est_un_ecart():
    amendement = ra.Amendement(UID_16, "16", None, "an:PA720430", COSIGNATAIRES_16[:-1])
    _c, _h, ecarts = ra.comparer(amendement, "an:PA720430", COSIGNATAIRES_16, SLUGS, _roles())
    assert [e["quoi"] for e in ecarts] == ["cosignataire absent de l'index"]


def test_un_premier_signataire_different_est_un_ecart():
    amendement = ra.Amendement(UID_16, "16", None, "an:PA795588", COSIGNATAIRES_16)
    _c, _h, ecarts = ra.comparer(amendement, "an:PA720430", COSIGNATAIRES_16, SLUGS, _roles())
    assert "premier signataire" in [e["quoi"] for e in ecarts]


def test_un_profil_sans_l_amendement_ou_avec_un_autre_role_est_un_ecart():
    _c, _h, ecarts = ra.comparer(AMENDEMENT, "an:PA720430", COSIGNATAIRES_16, SLUGS,
                                 _roles(**{"membre-a": {}, "membre-b": {UID_16: "auteur_principal"}}))
    assert [(e["quoi"], e["publie"]) for e in ecarts] == [
        ("rôle sur le profil", None), ("rôle sur le profil", "auteur_principal")]


def test_un_profil_qui_porte_l_amendement_sans_etre_nomme_est_un_ecart():
    slugs = {**SLUGS, "an:PA1": "intrus"}
    _c, _h, ecarts = ra.comparer(AMENDEMENT, "an:PA720430", COSIGNATAIRES_16, slugs,
                                 _roles(intrus={UID_16: "cosignataire"}))
    assert [e["quoi"] for e in ecarts] == ["profil qui porte l'amendement sans que la page le nomme"]


# ── Bout à bout, et les sources muettes ─────────────────────────────────────

def _profils(tmp_path):
    for slug, roles in _roles().items():
        amendements = [{"amendement_id": uid, "role_signataire": role} for uid, role in roles.items()]
        (tmp_path / f"{slug}.pivot.json").write_text(json.dumps({"id": slug, "amendements": amendements}))
    return tmp_path


def test_bout_a_bout_sur_la_page_relevee(tmp_path):
    [res] = ra.relire([AMENDEMENT], SLUGS, _profils(tmp_path),
                      obtenir=lambda _u: _page("amendement_16_0760_2711.html"), delai=0)
    assert res.non_verifie is None and res.signataires == 8 and res.concordants == 3 and res.ecarts == []
    _texte, resume = ra.rapport([res], graine=1)
    assert resume["signatures_concordantes"] == 3 and resume["ecarts"] == 0


def test_une_page_injoignable_est_non_verifiee(tmp_path):
    def panne(_url):
        raise ConnectionError("délai dépassé")

    [res] = ra.relire([AMENDEMENT], SLUGS, _profils(tmp_path), obtenir=panne, delai=0)
    assert res.non_verifie.startswith("page injoignable") and res.ecarts == []


# ── Le branchement dans le run ──────────────────────────────────────────────

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "generate-data.yml"


def _step(nom):
    texte = WORKFLOW.read_text(encoding="utf-8")
    debut = texte.index(f"      - name: {nom}\n")
    fin = texte.find("\n      - ", debut + 1)
    return texte[debut:fin]


def test_le_controle_tourne_dans_le_run_sans_bloquer():
    step = _step("Amendements relus à la source (signalement)")
    assert "src/relecture_amendements_source.py" in step
    assert "continue-on-error: true" in step and "github.run_id" in step


def test_le_run_ne_ferme_jamais_l_issue_des_amendements():
    step = _step("Amendements en écart avec la source — issue de suivi")
    assert "gh issue close" not in step
    assert "steps.commit.outputs.pushed == 'true'" in step
    assert "['ecarts']" in step
