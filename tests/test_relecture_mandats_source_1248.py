"""Relecture à la source des mandats de député publiés (#1248, lot 2).

Les pages sont des extraits verbatim de la page « fonctions » de l'Assemblée
(Yaël Braun-Pivet et Bernard Cazeneuve, relevées le 02/11/2026) : la section
« Mandat », telle que le site l'écrit.
"""

from pathlib import Path

import pytest

import relecture_mandats_source as rm

FIXTURES = Path(__file__).parent / "fixtures" / "relecture_mandats"


def _page(nom):
    return (FIXTURES / nom).read_text(encoding="utf-8")


# ── La lecture de la page ────────────────────────────────────────────────────

def test_les_periodes_d_une_deputee_en_cours_de_mandat():
    """Mandat en cours sur la page courante, mandats passés sur l'archive ; la
    ligne de présidence de l'Assemblée n'est pas une période de mandat."""
    periodes = rm.lire_periodes([_page("braun_pivet_courant.html"), _page("braun_pivet_archive.html")])
    assert periodes == {
        ("2024-07-07", None),
        ("2022-06-19", "2024-06-09"),
        ("2017-06-18", "2022-06-20"),
    }


def test_une_reprise_se_date_de_l_entree_en_fonction():
    """Cazeneuve, XIVe : député un mois, puis de nouveau les quatre derniers
    jours ; la XIe (1997) est avant la borne d'AMO30 et n'est pas lue."""
    periodes = rm.lire_periodes([_page("cazeneuve_archive.html")])
    assert periodes == {
        ("2012-06-20", "2012-07-21"),
        ("2017-06-16", "2017-06-20"),
        ("2007-06-20", "2012-06-16"),
    }


def test_un_mois_inconnu_rend_la_page_illisible():
    html = _page("cazeneuve_archive.html").replace("Réélu le 20 juin 2012", "Réélu le 20 juinet 2012")
    with pytest.raises(rm.PageIllisible):
        rm.lire_periodes([html])


# ── Le tirage : 1 candidat, 3 de la XVIIe, 1 des précédentes ────────────────

def _depute(slug, provenance, periodes):
    return rm.Depute(slug=slug, acteur=f"PA{len(slug)}", provenance=provenance, periodes=set(periodes))


def _population():
    candidats = [_depute(f"candidat-{i}", "candidat_declare", [("2017-06-18", "2022-06-21")]) for i in range(5)]
    xviie = [_depute(f"xviie-{i}", "roster_groupe", [("2024-07-07", None)]) for i in range(20)]
    anciens = [_depute(f"ancien-{i}", "roster_groupe", [("2012-06-20", "2017-06-20")]) for i in range(20)]
    return candidats + xviie + anciens


def test_le_tirage_suit_l_arbitrage():
    tirage = rm.tirer(_population(), graine=1)
    groupes = [g for g, _ in tirage]
    assert groupes == ["candidat déclaré"] + ["XVIIe législature"] * 3 + ["législatures précédentes"]
    assert all(d.siege_dans_la_xviie for g, d in tirage if g == "XVIIe législature")
    assert not any(d.siege_dans_la_xviie for g, d in tirage if g == "législatures précédentes")


def test_un_candidat_tire_ne_l_est_pas_deux_fois():
    candidat = _depute("candidat-xviie", "candidat_declare", [("2024-07-07", None)])
    tirage = rm.tirer([candidat] + [_depute(f"x-{i}", "roster_groupe", [("2024-07-07", None)]) for i in range(3)], graine=1)
    assert [d.slug for _, d in tirage].count("candidat-xviie") == 1


def test_le_tirage_se_rejoue_a_l_identique():
    a = [d.slug for _, d in rm.tirer(_population(), graine=42)]
    b = [d.slug for _, d in rm.tirer(list(reversed(_population())), graine=42)]
    assert a == b


def test_seuls_les_mandats_de_depute_depuis_2002_sont_publies_a_comparer():
    profil = {"mandats": [
        {"categorie": "mandat_electif", "chambre": "AN", "debut": "2012-06-20", "fin": "2012-07-21"},
        {"categorie": "mandat_electif", "chambre": "AN", "debut": "1997-06-12", "fin": "2002-06-18"},
        {"categorie": "mandat_electif", "chambre": "Senat", "debut": "2014-10-01", "fin": None},
        {"categorie": "commission", "chambre": "AN", "debut": "2012-06-28", "fin": "2012-07-21"},
    ]}
    assert rm.periodes_publiees(profil) == {("2012-06-20", "2012-07-21")}


# ── La comparaison et les sources muettes ───────────────────────────────────

def test_l_enveloppe_d_avant_1412_est_un_ecart():
    """Ce que le premier essai a trouvé : un passage au gouvernement publié
    comme mandat de député."""
    page = rm.lire_periodes([_page("cazeneuve_archive.html")])
    publiees = {("2012-06-20", "2017-06-20"), ("2007-06-20", "2012-06-16")}
    concordantes, ecarts = rm.comparer(page, publiees)
    assert concordantes == 1
    assert {(tuple(e["page"]) if e["page"] else None, tuple(e["publie"]) if e["publie"] else None) for e in ecarts} == {
        (("2012-06-20", "2012-07-21"), None),
        (("2017-06-16", "2017-06-20"), None),
        (None, ("2012-06-20", "2017-06-20")),
    }


def _cazeneuve():
    return rm.Depute(slug="bernard-cazeneuve", acteur="PA785", provenance="candidat_declare",
                     periodes={("2012-06-20", "2012-07-21"), ("2017-06-16", "2017-06-20"),
                               ("2007-06-20", "2012-06-16")})


def test_un_ancien_depute_sans_page_courante_est_relu_sur_l_archive():
    pages = {rm.URL_FONCTIONS.format(acteur="PA785"): None,
             rm.URL_FONCTIONS.format(acteur="PA785") + "?archive=oui": _page("cazeneuve_archive.html")}
    [res] = rm.relire([("candidat déclaré", _cazeneuve())], obtenir=pages.get, delai=0)
    assert res.non_verifie is None and res.concordantes == 3 and res.ecarts == []


def test_une_page_injoignable_est_non_verifiee():
    def panne(_url):
        raise ConnectionError("délai dépassé")

    [res] = rm.relire([("candidat déclaré", _cazeneuve())], obtenir=panne, delai=0)
    assert res.non_verifie.startswith("page injoignable") and res.ecarts == []
    _texte, resume = rm.rapport([res], graine=1)
    assert resume["deputes_non_verifies"] == 1 and resume["periodes_en_ecart"] == 0


def test_une_page_sans_periode_est_non_verifiee():
    [res] = rm.relire([("candidat déclaré", _cazeneuve())], obtenir=lambda _u: "<html></html>", delai=0)
    assert res.non_verifie == "page illisible : aucune période de mandat lue"


# ── Le branchement dans le run ──────────────────────────────────────────────

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "generate-data.yml"


def _step(nom):
    texte = WORKFLOW.read_text(encoding="utf-8")
    debut = texte.index(f"      - name: {nom}\n")
    fin = texte.find("\n      - ", debut + 1)
    return texte[debut:fin]


def test_le_controle_tourne_dans_le_run_sans_bloquer():
    step = _step("Mandats relus à la source (signalement)")
    assert "src/relecture_mandats_source.py" in step
    assert "continue-on-error: true" in step
    assert "github.run_id" in step


def test_le_run_ne_ferme_jamais_l_issue_des_mandats():
    step = _step("Mandats en écart avec la source — issue de suivi")
    assert "gh issue close" not in step
    assert "steps.commit.outputs.pushed == 'true'" in step
    assert "periodes_en_ecart" in step
