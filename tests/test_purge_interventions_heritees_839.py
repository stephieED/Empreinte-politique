"""Tests de `src/purge_interventions_heritees.py` (#839).

Arbitrage retenu : **prudence**, comme #387. Une intervention héritée de l'ère
NosDéputés n'est retirée que si sa jumelle Syceron est **présente dans le même
profil**, le même jour, au texte contenu ou identique. Sans jumelle, elle est
conservée : un faux négatif laisse un doublon visible (bénin), un faux positif
supprime une prise de parole (irréversible hors git).

Les fixtures décrivent les deux couches (`id` au brut, `intervention_id` au
pivot) et les formes de date qui coexistent réellement dans le corpus — un test
qui ne servirait qu'une seule forme vérifierait un monde que le corpus n'a pas
(#726).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from purge_interventions_heritees import (  # noqa: E402
    _normalize_date,
    _normalize_texte,
    est_heritee,
    purge_profil,
)


def _nosdeputes(identifiant, date, texte):
    return {
        "id": identifiant,
        "date": date,
        "texte": texte,
        "source_url": f"https://www.nosdeputes.fr/16/seance/1247#inter_{identifiant}",
    }


def _syceron(suffixe, date, texte):
    return {"intervention_id": f"syceron_CRSANR5L16S2023O1N091_{suffixe}", "date": date, "texte": texte}


# ---------------------------------------------------------------------------
# Signature d'une entrée héritée
# ---------------------------------------------------------------------------

def test_identifiant_entier_est_la_signature_nosdeputes():
    """Aucune source vivante ne rend d'identifiant entier : Syceron, les
    questions officielles et le Parlement européen rendent tous une chaîne
    préfixée."""
    assert est_heritee({"id": 249506})
    assert est_heritee({"intervention_id": 2360})
    assert not est_heritee({"intervention_id": "syceron_CRSANR5L16S2023O1N091_000160"})
    assert not est_heritee({"intervention_id": "question_QANR5L15QOSD1118"})
    assert not est_heritee({"intervention_id": "europarl_A9-0100-2021"})
    assert not est_heritee({"intervention_id": None})


def test_un_booleen_n_est_pas_un_identifiant():
    """`True` est un `int` en Python : sans garde, une valeur aberrante serait
    lue comme une entrée héritée et l'entrée disparaîtrait."""
    assert not est_heritee({"intervention_id": True})


# ---------------------------------------------------------------------------
# Réduction du texte et de la date
# ---------------------------------------------------------------------------

def test_le_texte_se_compare_hors_balises_et_ponctuation():
    """NosDéputés sert du HTML, Syceron du texte nu : sans cette réduction,
    aucune jumelle ne se rapproche."""
    assert _normalize_texte("<p>C&#039;est vrai !</p>") == _normalize_texte("C’est vrai !")


def test_les_deux_formes_de_date_du_corpus_s_accordent():
    """`30/06/2020` (questions officielles) et `2020-06-30` (Syceron) désignent
    le même jour ; les comparer bruts ferait conclure « aucune intervention ce
    jour-là »."""
    assert _normalize_date("30/06/2020") == _normalize_date("2020-06-30")


# ---------------------------------------------------------------------------
# purge_profil — le cœur de l'arbitrage
# ---------------------------------------------------------------------------

def test_retire_le_doublon_quand_la_jumelle_syceron_est_presente():
    profil = {"interventions": [
        _nosdeputes(249506, "2023-05-02", "<p>Les Mahorais ont manifesté pour les soutenir !</p>"),
        _syceron("000160", "2023-05-02", "Les Mahorais ont manifesté pour les soutenir !"),
    ]}
    profil, retires = purge_profil(profil)
    assert [_id(e) for e in retires] == [249506]
    assert len(profil["interventions"]) == 1
    assert not est_heritee(profil["interventions"][0])


def test_conserve_l_entree_sans_jumelle():
    """Les 19 entrées que Syceron ne rend pas — Congrès de 2018, réunions de
    commission, interpellations attribuées ailleurs — restent publiées tant que
    l'arbitrage éditorial n'a pas tranché."""
    profil = {"interventions": [
        _nosdeputes(305964, "2018-07-09", "<p>Malgré la mélodie des discours habiles…</p>"),
        _syceron("000012", "2018-07-09", "Tout autre chose, dite le même jour."),
    ]}
    profil, retires = purge_profil(profil)
    assert retires == []
    assert len(profil["interventions"]) == 2


def test_conserve_quand_la_jumelle_est_un_autre_jour():
    """Le même texte un autre jour n'est pas la même prise de parole."""
    profil = {"interventions": [
        _nosdeputes(2360, "2022-07-11", "<p>C'est vrai !</p>"),
        _syceron("000004", "2022-07-12", "C’est vrai !"),
    ]}
    _, retires = purge_profil(profil)
    assert retires == []


def test_la_jumelle_peut_contenir_le_fragment_nosdeputes():
    """Le compte rendu définitif rend d'un bloc ce que NosDéputés coupait :
    l'inclusion vaut dans les deux sens."""
    profil = {"interventions": [
        _nosdeputes(29173, "2017-08-09", "<p>… de celui de la justice, …</p>"),
        _syceron("000200", "2017-08-09", "Il relève du ministère de l’intérieur comme de celui de la justice, et nul ne l’ignore."),
    ]}
    _, retires = purge_profil(profil)
    assert [_id(e) for e in retires] == [29173]


def test_une_entree_question_officielle_n_est_jamais_touchee():
    profil = {"interventions": [
        {"intervention_id": "question_QANR5L15QOSD1118", "date": "30/06/2020", "texte": "Mme Marine Le Pen attire l'attention…"},
    ]}
    profil, retires = purge_profil(profil)
    assert retires == []
    assert len(profil["interventions"]) == 1


def test_idempotent():
    """Une seconde exécution ne retire plus rien : la jumelle Syceron reste,
    l'entrée héritée est partie."""
    profil = {"interventions": [
        _nosdeputes(249506, "2023-05-02", "<p>Les Mahorais ont manifesté pour les soutenir !</p>"),
        _syceron("000160", "2023-05-02", "Les Mahorais ont manifesté pour les soutenir !"),
    ]}
    profil, premiers = purge_profil(profil)
    profil, seconds = purge_profil(profil)
    assert len(premiers) == 1 and seconds == []


def test_retirer_sans_jumelle_emporte_aussi_les_orphelines():
    """Arbitrage du 12/09/2026, adossé à la source : les 19 entrées sans jumelle
    ont été vérifiées une par une dans les archives de l'AN, qui ne les rattache
    à aucun mandat — `PA0` et identifiants négatifs portent tous
    `id_mandat="-1"`. Le drapeau reste explicite, et le défaut prudent."""
    profil = {"interventions": [
        _nosdeputes(305964, "2018-07-09", "<p>Un propos que Syceron ne rend pas.</p>"),
        _syceron("000012", "2018-07-09", "Tout autre chose, dite le même jour."),
    ]}
    _, prudent = purge_profil(json.loads(json.dumps(profil)))
    _, etendu = purge_profil(json.loads(json.dumps(profil)), retirer_sans_jumelle=True)
    assert prudent == []
    assert [_id(e) for e in etendu] == [305964]


def test_retirer_sans_jumelle_ne_touche_pas_les_entrees_vivantes():
    """Le drapeau élargit le retrait aux seules entrées héritées : une entrée
    Syceron ou une question officielle n'est jamais concernée."""
    profil = {"interventions": [
        _syceron("000160", "2023-05-02", "Un propos."),
        {"intervention_id": "question_QANR5L15QOSD1118", "date": "30/06/2020", "texte": "Une question."},
    ]}
    profil, retires = purge_profil(profil, retirer_sans_jumelle=True)
    assert retires == []
    assert len(profil["interventions"]) == 2


def test_un_profil_sans_interventions_ne_leve_pas():
    """Un profil de gouvernement ou un profil neuf n'a pas la clé ; la parcourir
    sans garde ferait tomber la purge sur un cas banal."""
    profil, retires = purge_profil({"slug": "x"})
    assert retires == [] and "interventions" not in profil


def test_une_entree_heritee_sans_texte_est_conservee():
    """Un texte vide rapprocherait n'importe quelle jumelle : §2 règle 5, une
    absence ne se comble pas."""
    profil = {"interventions": [
        _nosdeputes(1, "2023-05-02", None),
        _syceron("000160", "2023-05-02", "Un texte quelconque."),
    ]}
    _, retires = purge_profil(profil)
    assert retires == []


def _id(entree):
    return entree.get("intervention_id", entree.get("id"))
