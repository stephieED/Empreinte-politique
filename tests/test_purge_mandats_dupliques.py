"""Tests de `src/purge_mandats_dupliques.py` (#387, sous-issue de l'épic
taxonomie #382).

Arbitrage retenu : **prudence**. Une entrée héritée n'est retirée que si son
doublon AN est démontré — même organe (libellé normalisé) ET période
recouvrante. Toute incertitude conserve l'entrée : un faux négatif laisse un
doublon visible (bénin), un faux positif supprimerait un mandat réel
(irréversible hors git).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from purge_mandats_dupliques import (
    _normalize_label,
    _periodes_se_chevauchent,
    purge_profil,
)


def _mandat(categorie, label, debut=None, fin=None):
    return {"categorie": categorie, "label": label, "debut": debut, "fin": fin}


# ---------------------------------------------------------------------------
# _normalize_label — appariement inter-référentiels
# ---------------------------------------------------------------------------

def test_normalize_label_retire_le_prefixe_de_nature():
    """L'AN nomme l'organe par son seul thème, NosDéputés préfixe la nature :
    c'est l'obstacle central identifié en #387."""
    assert _normalize_label("Groupe d'études trufficulture") == _normalize_label("Trufficulture")
    assert _normalize_label("Mission d'information sur la ressource en eau") == _normalize_label("La ressource en eau")
    assert _normalize_label("Commission d'enquête sur le montage juridique") == _normalize_label("Le montage juridique")


def test_normalize_label_neutralise_casse_et_accents():
    assert _normalize_label("Économie SOCIALE et solidaire") == _normalize_label("economie sociale et solidaire")


def test_normalize_label_ne_rapproche_pas_des_organes_distincts():
    """Garde-fou : la normalisation ne doit pas fusionner deux organes
    réellement différents — ce serait un faux positif, donc une perte."""
    assert _normalize_label("Groupe d'études montagne") != _normalize_label("Groupe d'études pastoralisme")
    assert _normalize_label("Commission des affaires étrangères") != _normalize_label("Commission des affaires sociales")


def test_normalize_label_valeur_non_textuelle():
    assert _normalize_label(None) == ""
    assert _normalize_label(42) == ""


# ---------------------------------------------------------------------------
# _periodes_se_chevauchent
# ---------------------------------------------------------------------------

def test_periodes_se_chevauchent_cas_nominal():
    assert _periodes_se_chevauchent("2023-10-31", "2024-06-09", "2023-10-03", "2024-06-09")


def test_periodes_disjointes_ne_se_chevauchent_pas():
    """Deux périodes distinctes du même organe (entrée/sortie/remplacement) :
    l'entrée héritée couvre un temps que l'AN ne couvre pas, la retirer
    effacerait une donnée réelle."""
    assert not _periodes_se_chevauchent("2024-04-12", "2024-06-09", "2024-03-28", "2024-04-09")


def test_periodes_bornes_absentes_traitees_comme_ouvertes():
    """Une borne absente est ouverte (mandat en cours), jamais remplacée par
    la date du jour (AGENTS.md §2.5)."""
    assert _periodes_se_chevauchent("2023-01-01", None, "2024-01-01", None)
    assert _periodes_se_chevauchent(None, None, "2020-01-01", "2020-02-01")


# ---------------------------------------------------------------------------
# purge_profil — règle complète
# ---------------------------------------------------------------------------

def test_purge_retire_le_doublon_avere():
    """Même organe, période recouvrante, catégorie couverte par l'AN."""
    profil = {"mandats": [
        _mandat("commission", "Groupe d'études trufficulture", "2022-10-01", "2024-06-09"),
        _mandat("groupe_etudes", "Trufficulture", "2022-09-15", "2024-06-09"),
    ]}
    mandats_an = [_mandat("groupe_etudes", "Trufficulture", "2022-09-15", "2024-06-09")]

    _, retires = purge_profil(profil, mandats_an)

    assert len(retires) == 1
    assert retires[0]["label"] == "Groupe d'études trufficulture"
    assert [m["label"] for m in profil["mandats"]] == ["Trufficulture"]


def test_purge_conserve_une_periode_distincte_du_meme_organe():
    """Libellé identique mais période disjointe : ce n'est pas un doublon."""
    profil = {"mandats": [
        _mandat("commission", "Commission des affaires étrangères", "2024-04-12", "2024-06-09"),
    ]}
    mandats_an = [_mandat("commission", "Commission des affaires étrangères", "2024-03-28", "2024-04-09")]

    _, retires = purge_profil(profil, mandats_an)

    assert retires == []
    assert len(profil["mandats"]) == 1


def test_purge_conserve_une_entree_sans_equivalent_an():
    """Mandat réel que l'AN n'expose pas (typeOrgane hors périmètre, ou profil
    partiellement couvert) : conservé — c'est tout le principe de prudence."""
    profil = {"mandats": [
        _mandat("commission", "Commission mixte paritaire sur le PLF", "2023-01-01", "2023-02-01"),
    ]}
    mandats_an = [_mandat("commission", "Commission des finances", "2022-07-01", None)]

    _, retires = purge_profil(profil, mandats_an)

    assert retires == []


def test_purge_ne_retire_jamais_une_entree_an_elle_meme():
    """Une entrée identique à l'extraction AN courante est l'originale."""
    an = _mandat("groupe_etudes", "Trufficulture", "2022-09-15", "2024-06-09")
    profil = {"mandats": [dict(an)]}

    _, retires = purge_profil(profil, [an])

    assert retires == []


def test_purge_ignore_les_categories_hors_perimetre_an():
    """`mandat_electif`/`groupe_politique` ne sont pas couverts par ce mapping :
    jamais candidats à la purge, même si un libellé coïncidait."""
    profil = {"mandats": [
        _mandat("mandat_electif", "Trufficulture", "2022-09-15", "2024-06-09"),
        _mandat("groupe_politique", "Trufficulture", "2022-09-15", "2024-06-09"),
    ]}
    mandats_an = [_mandat("groupe_etudes", "Trufficulture", "2022-09-15", "2024-06-09")]

    _, retires = purge_profil(profil, mandats_an)

    assert retires == []


def test_purge_ne_retire_rien_si_l_equivalent_an_n_est_pas_dans_le_profil():
    """Défaut détecté à la mise au point, et raison d'être de ce test.

    Un profil pas encore régénéré avec le mapping élargi (#384) contient les
    entrées héritées mais PAS encore leurs équivalents AN. Comparer à
    l'extraction AN fraîche (qui, elle, connaît l'organe) ferait disparaître
    l'organe du profil au lieu de le dédoublonner — mesuré : 18 organes
    distincts perdus sur `benjamin-haddad`. La comparaison doit porter sur ce
    qui est présent dans le profil."""
    profil = {"mandats": [
        _mandat("commission", "Groupe d'études trufficulture", "2022-10-01", "2024-06-09"),
    ]}
    # L'AN connaît bien cet organe, mais l'entrée n'est pas (encore) dans le profil.
    mandats_an = [_mandat("groupe_etudes", "Trufficulture", "2022-09-15", "2024-06-09")]

    _, retires = purge_profil(profil, mandats_an)

    assert retires == [], "Sans équivalent présent dans le profil, rien ne doit être retiré"
    assert len(profil["mandats"]) == 1


def test_purge_est_idempotente():
    """Une seconde exécution ne retire plus rien."""
    profil = {"mandats": [
        _mandat("commission", "Groupe d'études trufficulture", "2022-10-01", "2024-06-09"),
        _mandat("groupe_etudes", "Trufficulture", "2022-09-15", "2024-06-09"),
    ]}
    mandats_an = [_mandat("groupe_etudes", "Trufficulture", "2022-09-15", "2024-06-09")]

    profil, premiers = purge_profil(profil, mandats_an)
    profil, seconds = purge_profil(profil, mandats_an)

    assert len(premiers) == 1
    assert seconds == []


def test_purge_sur_extraction_an_vide_ne_retire_rien():
    """Jamais de purge sur une absence : une extraction vide est
    indiscernable d'un échec transitoire (résilience #241)."""
    profil = {"mandats": [
        _mandat("commission", "Groupe d'études trufficulture", "2022-10-01", "2024-06-09"),
    ]}

    _, retires = purge_profil(profil, [])

    assert retires == []
    assert len(profil["mandats"]) == 1
