"""Tests de `src/audit_sediment.py` (#839, lot A).

Ce script **compte, il ne juge pas** : les tests portent donc sur ce qui se
compte et sur ce qui, délibérément, ne se compte pas — une couche qui ne porte
pas le champ n'a pas « zéro entrée », et une couche sans `meta.provenance` n'est
pas ventilée (#630 : le brut rendrait « 1 181 candidats », ce qui est
faux).

Aucun test ne lit le corpus réel : les fixtures décrivent les **deux** couches,
parce que le brut et le pivot ne nomment pas les mêmes clés — c'est exactement
ce qu'un jeu d'essai d'une seule couche laisserait passer (#726).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from audit_sediment import (  # noqa: E402
    FAMILLES,
    TYPES_SOURCE_RETIRES,
    auditer_profil,
    auditer_repertoire,
)


def _profil_pivot(**champs):
    base = {"meta": {"provenance": "candidat_declare"}, "mandats": [], "interventions": [], "sources": []}
    base.update(champs)
    return base


def _compte(profil, cle):
    return len(auditer_profil(profil)[cle])


# ---------------------------------------------------------------------------
# Les signatures, une par famille
# ---------------------------------------------------------------------------

def test_un_identifiant_entier_est_compte_dans_les_deux_couches():
    """Le pivot nomme la clé `intervention_id`, le brut `id`."""
    assert _compte(_profil_pivot(interventions=[{"intervention_id": 249506}]), "interventions_id_entier") == 1
    assert _compte(_profil_pivot(interventions=[{"id": 249506}]), "interventions_id_entier") == 1
    assert _compte(_profil_pivot(interventions=[{"intervention_id": "syceron_X_000160"}]), "interventions_id_entier") == 0


def test_l_url_de_la_source_retiree_se_lit_aussi_sous_la_cle_du_brut():
    """Le pivot publie `source_url`, le brut garde `url` : ne lire que l'un des
    deux rendait 0 sur une couche qui en porte 511."""
    pivot = _profil_pivot(interventions=[{"intervention_id": 1, "source_url": "https://www.nosdeputes.fr/16/seance/1"}])
    brut = _profil_pivot(interventions=[{"id": 1, "url": "https://www.nosdeputes.fr//api/document/Intervention/1/json"}])
    assert _compte(pivot, "interventions_url_source_retiree") == 1
    assert _compte(brut, "interventions_url_source_retiree") == 1


def test_un_mandat_sans_categorie_source_est_compte_sans_etre_accuse():
    """#718 : l'absence dit « personne n'a établi cette catégorie ». L'audit la
    compte, il ne la qualifie pas."""
    profil = _profil_pivot(mandats=[
        {"label": "Commission des affaires étrangères", "categorie": "commission"},
        {"label": "Commission des lois", "categorie": "commission", "categorie_source": "an"},
    ])
    assert _compte(profil, "mandats_sans_categorie_source") == 1


def test_un_mandat_actif_sans_aucune_date_est_compte_a_part():
    """La fiche publie une appartenance en cours que rien ne date ; le coût de
    son arbitrage n'est pas celui des autres."""
    profil = _profil_pivot(mandats=[
        {"label": "Vidéos", "categorie": "commission", "actif": True, "debut": None, "fin": None},
        {"label": "Commission des lois", "categorie": "commission", "actif": True, "debut": "2022-06-29", "fin": None},
    ])
    assert _compte(profil, "mandats_actifs_sans_dates") == 1


def test_les_types_de_source_retires_sont_derives_des_licences():
    """Jamais recopiés : le jour où un type change de licence, l'audit suit."""
    assert TYPES_SOURCE_RETIRES == frozenset({"nosdeputes", "nossenateurs"})
    profil = _profil_pivot(sources=[{"type": "nosdeputes"}, {"type": "assemblee_nationale"}])
    assert _compte(profil, "sources_retirees") == 1


def test_un_avertissement_herite_est_reconnu_par_la_table_qui_le_publie():
    """Les formulations d'avant vivent dans `avertissements.py`, qui leur donne
    un destinataire (#642) : les recopier ici en ferait une seconde vérité."""
    from avertissements import AVERTISSEMENTS_HERITES
    message = next(iter(AVERTISSEMENTS_HERITES))
    assert _compte(_profil_pivot(meta={"provenance": "candidat_declare", "avertissements": [message]}),
                   "avertissements_herites") == 1
    assert _compte(_profil_pivot(meta={"provenance": "candidat_declare", "avertissements": ["tout va bien"]}),
                   "avertissements_herites") == 0


def test_une_preuve_de_couverture_citant_la_source_est_comptee():
    profil = _profil_pivot(couverture={"mandats": [
        {"etat": "couvert", "preuve": "synchronisé depuis www.nosdeputes.fr"},
        {"etat": "couvert", "preuve": "AMO30, mesuré le 28/08/2026"},
    ]})
    assert _compte(profil, "preuves_couverture") == 1


# ---------------------------------------------------------------------------
# Ce que l'audit refuse de dire
# ---------------------------------------------------------------------------

def test_un_champ_absent_de_la_couche_n_est_pas_zero(tmp_path):
    """`sources[]` et `couverture` n'existent pas au brut : y afficher `0` se
    lirait comme un constat sur le sédiment (§2 règle 5)."""
    (tmp_path / "x.json").write_text(json.dumps({"mandats": [], "interventions": []}), encoding="utf-8")
    _, _, _, cles_vues, _ = auditer_repertoire(tmp_path)
    familles = {f.cle: f for f in FAMILLES}
    assert not any(cle in cles_vues for cle in familles["sources_retirees"].cles_lues)
    assert any(cle in cles_vues for cle in familles["mandats_sans_categorie_source"].cles_lues)


def test_une_couche_sans_provenance_n_est_pas_ventilee(tmp_path):
    """Sans `meta.provenance`, tout profil compterait comme candidat déclaré :
    le brut rendrait « 1 181 candidats », faux (#630)."""
    (tmp_path / "a.json").write_text(json.dumps({"mandats": []}), encoding="utf-8")
    _, _, _, _, provenance_portee = auditer_repertoire(tmp_path)
    assert provenance_portee is False

    (tmp_path / "b.json").write_text(
        json.dumps({"meta": {"provenance": "roster_groupe"}, "mandats": []}), encoding="utf-8")
    _, population, _, _, provenance_portee = auditer_repertoire(tmp_path)
    assert provenance_portee is True
    assert population.total == 2


def test_un_fichier_illisible_reste_dans_le_total(tmp_path):
    """Il compte sous son propre poste : « lu » et « ventilé » ne doivent pas
    diverger en silence."""
    (tmp_path / "casse.json").write_text("{ pas du json", encoding="utf-8")
    _, population, illisibles, _, _ = auditer_repertoire(tmp_path)
    assert len(illisibles) == 1
    assert population.total == 1


def test_les_cosignatures_ne_sont_jamais_ouvertes(tmp_path):
    """222 Mio de RSS pour un fichier qu'aucune famille ne concerne."""
    (tmp_path / "x.cosignatures.json").write_text(json.dumps({"mandats": [{"label": "X"}]}), encoding="utf-8")
    _, population, _, _, _ = auditer_repertoire(tmp_path)
    assert population.total == 0


def test_l_audit_ne_modifie_aucun_profil(tmp_path):
    """Le lot A compte ; les retraits sont le lot D."""
    chemin = tmp_path / "x.json"
    contenu = json.dumps({"meta": {"provenance": "candidat_declare"},
                          "interventions": [{"intervention_id": 249506}], "mandats": []})
    chemin.write_text(contenu, encoding="utf-8")
    auditer_repertoire(tmp_path)
    assert chemin.read_text(encoding="utf-8") == contenu
