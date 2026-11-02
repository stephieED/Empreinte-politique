"""#1412 — les périodes de mandat de député disent quand la personne a siégé.

Relu sur la page « fonctions » de l'Assemblée (#1248, lot 2), le corpus
publiait Bernard Cazeneuve député de 2012 à 2017 pendant qu'il était ministre,
et Édouard Philippe député dès 2007 pour un siège de suppléant pris en 2012.
`tests/fixtures/amo30_periodes_1412.zip` est un extrait **octet pour octet**
de l'archive AMO30 du 02/11/2026 (ces deux acteurs), pour la raison de #510 :
une fixture inventée répondrait à la question par construction.
"""

import json
import zipfile
from pathlib import Path

import candidate_profile
import merge_profile
from candidate_profile import _periodes_mandats_assemblee
from merge_profile import mandats_deputes_conserves

ARCHIVE = Path(__file__).resolve().parent / "fixtures" / "amo30_periodes_1412.zip"


def _mandats_de(acteur_ref):
    with zipfile.ZipFile(ARCHIVE) as zf:
        acteur = json.loads(zf.read(f"json/acteur/{acteur_ref}.json"))["acteur"]
    mandats = (acteur.get("mandats") or {}).get("mandat")
    return mandats if isinstance(mandats, list) else [mandats]


def _periodes(acteur_ref, legislature):
    return sorted(
        (p["debut"], p["fin"])
        for p in _periodes_mandats_assemblee(_mandats_de(acteur_ref), {})
        if p["legislature"] == legislature
    )


# ── La reconstruction ───────────────────────────────────────────────────────

def test_le_passage_au_gouvernement_n_est_plus_un_mandat_de_depute():
    """Cazeneuve, XIVe : député un mois, ministre puis Premier ministre, de
    nouveau député les quatre derniers jours — ce que dit la page."""
    assert _periodes("PA785", "14") == [
        ("2012-06-20", "2012-07-21"),
        ("2017-06-16", "2017-06-20"),
    ]


def test_un_suppleant_est_date_de_son_entree_en_fonction():
    """Philippe, XIIIe : « Élu le 20 juin 2007 - Mandat du 23 mars 2012
    (remplacement d'un député décédé) »."""
    assert _periodes("PA345619", "13") == [("2012-03-23", "2012-06-19")]


def test_un_mandat_ouvert_par_une_election_garde_la_date_de_l_election():
    """La convention de #640 ne bouge pas pour les élections : la changer aurait
    déplacé de trois jours les 2 868 périodes d'élections générales."""
    assert _periodes("PA345619", "14") == [("2012-06-20", "2017-06-15")]


def test_une_cause_absente_se_lit_comme_une_election():
    mandat = {"typeOrgane": "ASSEMBLEE", "legislature": "17", "dateDebut": "2024-07-07",
              "dateFin": None, "mandature": {"datePriseFonction": "2024-07-08"}}
    assert candidate_profile._debut_de_periode(mandat) == "2024-07-07"


def test_une_reprise_sans_date_de_prise_de_fonction_garde_l_election():
    mandat = {"election": {"causeMandat": "reprise de l'exercice du mandat d'un ancien membre du Gouvernement"},
              "dateDebut": "2012-06-20", "mandature": {}}
    assert candidate_profile._debut_de_periode(mandat) == "2012-06-20"


# ── La fusion : l'ancienne enveloppe ne survit pas aux périodes justes ─────

def _depute(debut, fin, label="Mandat parlementaire (SRC)", source="an"):
    return {"categorie": "mandat_electif", "categorie_source": source,
            "label": label, "debut": debut, "fin": fin}


def test_l_enveloppe_publiee_est_retiree_quand_la_collecte_la_redate():
    ancienne = _depute("2012-06-20", "2017-06-20")
    neufs = [_depute("2012-06-20", "2012-07-21"), _depute("2017-06-16", "2017-06-20")]
    assert mandats_deputes_conserves([ancienne], neufs) == []


def test_le_doublon_au_libelle_perime_disparait():
    """Brun, XVIIe : la même période sous deux groupes."""
    perime = _depute("2024-07-07", None, "Mandat parlementaire (Socialistes et apparentés)")
    neuf = _depute("2024-07-07", None, "Mandat parlementaire (Non inscrit)")
    assert mandats_deputes_conserves([perime, neuf], [neuf]) == []


def test_une_collecte_sans_mandat_de_depute_ne_retire_rien():
    anciens = [_depute("2012-06-20", "2017-06-20")]
    assert mandats_deputes_conserves(anciens, []) == anciens
    assert mandats_deputes_conserves(anciens, None) == anciens


def test_un_mandat_que_la_collecte_ne_recouvre_pas_reste():
    """Le repli sur le seul mandat courant ne retire pas un mandat passé."""
    passe = _depute("2017-06-18", "2022-06-21")
    courant = _depute("2024-07-07", None)
    assert mandats_deputes_conserves([passe, courant], [courant]) == [passe]


def test_les_autres_mandats_ne_sont_jamais_touches():
    nosdeputes = _depute("2012-06-20", "2017-06-20", source=None)
    commission = {"categorie": "commission", "categorie_source": "an",
                  "debut": "2012-06-20", "fin": "2017-06-20"}
    senat = _depute("2012-06-20", "2017-06-20", source="senat")
    anciens = [nosdeputes, commission, senat]
    assert mandats_deputes_conserves(anciens, [_depute("2012-06-20", "2012-07-21")]) == anciens


def test_les_deux_etages_de_la_fusion_appliquent_le_retrait():
    """Le profil brut et le profil publié : oublier l'un laisserait l'enveloppe
    revenir par l'autre (#729)."""
    def depute(debut, fin):
        return {**_depute(debut, fin), "fonction": None, "type": "mandat"}

    ancien = {"id": "bernard-cazeneuve", "nom": "Bernard Cazeneuve",
              "mandats": [depute("2012-06-20", "2017-06-20")]}
    neuf = {"id": "bernard-cazeneuve", "nom": "Bernard Cazeneuve",
            "mandats": [depute("2012-06-20", "2012-07-21"), depute("2017-06-16", "2017-06-20")]}
    for fusion in (merge_profile.merge_raw_profile, merge_profile.merge_pivot_profile):
        periodes = sorted((m["debut"], m["fin"]) for m in fusion(ancien, neuf)["mandats"])
        assert periodes == [("2012-06-20", "2012-07-21"), ("2017-06-16", "2017-06-20")], fusion.__name__


def test_la_categorie_source_recopiee_est_celle_de_la_collecte():
    assert merge_profile._CATEGORIE_SOURCE_AN == candidate_profile.CATEGORIE_SOURCE_AN
