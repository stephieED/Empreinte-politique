"""#1169 — distinguer la présidence de séance d'une prise de parole dans le débat.

Le besoin vient de la fiche de groupe : publier le VOLUME de parole par membre
sans compter la conduite de la séance comme la parole du groupe. Mesuré sur
Ensemble pour la République à la XVIIe, **13 797 des 39 581 prises de parole du
groupe — 35 % — sont de sa présidente d'Assemblée.**

## Pourquoi un champ, et pas `fonction`

Trois signaux existent dans Syceron, mesurés le 02/10/2026 sur 60 comptes rendus
de la XVIIe (33 924 paragraphes, parseur XML) :

| Signal | Couverture de la présidence |
| --- | --- |
| `<qualite>` (publié sous `fonction`) | **0 %** — vide sur les 3 667 paragraphes de présidence |
| l'attribut `roledebat="president"` | **41 %** (3 666 sur 8 970) |
| **le libellé de l'orateur** | **100 %** — 8 970 paragraphes, et un seul faux positif écarté par l'ancrage |

`fonction` dit bien ministre, rapporteur, rapporteur général — ce n'est pas un
champ vide, contrairement à ce que laissait croire un échantillon de 25 profils
de membres de roster sans rôle gouvernemental. Mais il ne dit **jamais** la
présidence, parce que la source ne la met pas là.

## Pourquoi un rôle dérivé, et pas `orateur_nom` verbatim

8,5 % des entrées d'index portent un libellé de présidence. Publier le libellé
partout coûterait **42 Mio** sur le corpus publié, contre **2,6 Mio** pour ce
champ seul — mesuré sur 101 946 entrées d'index. `_reduire_au_theme` compte déjà
ses octets à 90 près ; ce lot suit la même règle.

## Et pourquoi le report dans la fusion était indispensable

La fusion est additive : l'entrée ancienne gagne. Sans report, **aucune des
1 217 456 interventions publiées ne recevrait jamais ce champ** — exactement ce
qui s'est produit les 30/09, où deux runs ont collecté les interventions sans
ajouter une entrée ni remplir un champ.
"""

import json
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]

from merge_profile import (  # noqa: E402
    CHAMPS_FAITS_DE_SOURCE,
    reporter_faits_de_source,
    reporter_id_syceron,
)
from normalize_profil import _normalize_intervention  # noqa: E402
from schema_pivot import (  # noqa: E402
    KNOWN_ROLES_SEANCE,
    ROLE_SEANCE_PRESIDENCE,
    role_seance_depuis_orateur,
)
import candidate_profile as cp  # noqa: E402

#: Copiée verbatim de `raw_data/profiles/yael-braun-pivet.json` le 02/10/2026 —
#: une entrée RÉELLE, en régime « extrait », de la population qui a besoin de ce
#: champ. Une entrée inventée aurait porté les clés que le code attend ; celle-ci
#: porte celles que le corpus a. C'est la leçon de #726.
ENTREE_DU_CORPUS = {
    "id": "syceron_CRSANR5L17S2026E1N023_000420",
    "date": "2026-07-21",
    "type_detail": "debat",
    "sujet": "Protection des enfants",
    "sujet_code_grammaire": "TITRE_TEXTE_DISCUSSION",
    "session_ref": "SCR5A2026E1",
    "url": "https://data.assemblee-nationale.fr/static/openData/repository/17/vp/syceronbrut/syseron.xml.zip",
    "legislature": "17",
    "id_syceron": "4167357",
    "collecte": "extrait",
    "texte": "La parole est à Mme la présidente de la commission spéciale.",
    "texte_tronque": False,
}


# ---------------------------------------------------------------------------
# Le libellé, et ce qu'il ne doit pas attraper
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("libelle", [
    "M. le président", "Mme la présidente",
    "M. le vice-président", "Mme la vice-présidente",
    "  Mme la présidente  ", "MME LA PRÉSIDENTE",
])
def test_les_libelles_de_presidence_sont_reconnus(libelle):
    assert role_seance_depuis_orateur(libelle) == ROLE_SEANCE_PRESIDENCE


@pytest.mark.parametrize("libelle", [
    "M. Jean-Luc Mélenchon",
    "Mme Yaël Braun-Pivet",
    # LE faux positif à écarter, et il existe dans la source : un orateur qui
    # CITE la formule. Mesuré, un seul cas sur 60 comptes rendus — l'ancrage
    # des deux côtés suffit, et c'est pour ça qu'il est ancré.
    "La parole est à M. le président Marc Fesneau, pour un rappel au règlement",
    "M. le président de la commission des finances",
    "M. le ministre", "Mme la rapporteure",
    "", None, 42,
])
def test_ce_qui_n_est_pas_la_presidence_de_seance_est_ecarte(libelle):
    assert role_seance_depuis_orateur(libelle) is None


def test_le_vocabulaire_du_role_est_ferme():
    """Une valeur de plus se déclare, comme tout `KNOWN_*` (AGENTS.md §4)."""
    assert KNOWN_ROLES_SEANCE == frozenset({ROLE_SEANCE_PRESIDENCE})


# ---------------------------------------------------------------------------
# La collecte le pose, et la forme réduite le garde
# ---------------------------------------------------------------------------


def test_la_forme_reduite_garde_le_role():
    """C'est la forme des MEMBRES DE ROSTER, donc la population dont les fiches
    de groupe agrègent la parole. Sans cette clé ici, le lot ne sert à rien."""
    reduite = cp._reduire_au_theme({**ENTREE_DU_CORPUS, "role_seance": ROLE_SEANCE_PRESIDENCE})
    assert reduite["role_seance"] == ROLE_SEANCE_PRESIDENCE
    # et l'entrée du corpus, telle qu'elle est publiée aujourd'hui, n'en a pas
    assert "role_seance" not in cp._reduire_au_theme(ENTREE_DU_CORPUS)


def test_le_role_ne_se_pose_jamais_a_none():
    """Une clé à `None` ferait croire que le rôle a été mesuré et qu'il est
    absent. Ici il n'a pas été lu (§2 règle 5)."""
    assert "role_seance" not in _normalize_intervention(dict(ENTREE_DU_CORPUS))
    pivot = _normalize_intervention({**ENTREE_DU_CORPUS, "role_seance": ROLE_SEANCE_PRESIDENCE})
    assert pivot["role_seance"] == ROLE_SEANCE_PRESIDENCE


def test_le_pivot_le_publie_aussi_en_forme_complete():
    complete = dict(ENTREE_DU_CORPUS)
    complete.pop("collecte")
    complete["role_seance"] = ROLE_SEANCE_PRESIDENCE
    assert _normalize_intervention(complete)["role_seance"] == ROLE_SEANCE_PRESIDENCE


# ---------------------------------------------------------------------------
# Le report : il écrit là où rien n'était écrit, et nulle part ailleurs
# ---------------------------------------------------------------------------


def _cle(i):
    return i.get("id") or i.get("intervention_id")


def test_le_report_remplit_une_entree_publiee_sans_le_champ():
    """Le cas réel : 1 217 456 entrées publiées sans `role_seance`, qu'aucun run
    ne remplirait sans ce report."""
    publiee = [dict(ENTREE_DU_CORPUS)]
    neuve = [{**ENTREE_DU_CORPUS, "role_seance": ROLE_SEANCE_PRESIDENCE, "fonction": "ministre"}]
    resultat = reporter_faits_de_source(publiee, neuve, _cle)
    assert resultat[0]["role_seance"] == ROLE_SEANCE_PRESIDENCE
    assert resultat[0]["fonction"] == "ministre"
    # et il n'a touché à rien d'autre
    assert resultat[0]["texte"] == ENTREE_DU_CORPUS["texte"]
    assert resultat[0]["collecte"] == "extrait"


def test_le_report_n_ecrase_jamais_une_valeur_publiee():
    """`collecte-vide-necrase-jamais`, dans les deux sens : ni par du vide, ni
    par une autre valeur. Le report écrit là où rien n'était écrit."""
    publiee = [{**ENTREE_DU_CORPUS, "fonction": "rapporteur", "id_syceron": "4167357"}]
    neuve = [{**ENTREE_DU_CORPUS, "fonction": "ministre", "id_syceron": "9999999"}]
    resultat = reporter_faits_de_source(publiee, neuve, _cle)
    assert resultat[0]["fonction"] == "rapporteur"
    assert resultat[0]["id_syceron"] == "4167357"


def test_une_entree_neuve_vide_ne_retire_rien():
    publiee = [{**ENTREE_DU_CORPUS, "role_seance": ROLE_SEANCE_PRESIDENCE}]
    neuve = [{k: v for k, v in ENTREE_DU_CORPUS.items()}]
    assert reporter_faits_de_source(publiee, neuve, _cle)[0]["role_seance"] == ROLE_SEANCE_PRESIDENCE


def test_le_report_ne_relie_que_les_entrees_de_meme_cle():
    publiee = [dict(ENTREE_DU_CORPUS)]
    neuve = [{**ENTREE_DU_CORPUS, "id": "syceron_AUTRE_000001",
              "role_seance": ROLE_SEANCE_PRESIDENCE}]
    assert "role_seance" not in reporter_faits_de_source(publiee, neuve, _cle)[0]


def test_le_report_d_id_syceron_reste_un_cas_du_report_general():
    """#1087 nomme `reporter_id_syceron` et des tests l'exercent : il doit
    continuer à ne toucher QUE cette clé."""
    publiee = [{k: v for k, v in ENTREE_DU_CORPUS.items() if k != "id_syceron"}]
    neuve = [{**ENTREE_DU_CORPUS, "role_seance": ROLE_SEANCE_PRESIDENCE}]
    resultat = reporter_id_syceron(publiee, neuve, _cle)
    assert resultat[0]["id_syceron"] == "4167357"
    assert "role_seance" not in resultat[0]


def test_la_liste_des_faits_de_source_est_nommee_et_courte():
    """« Tous les champs absents » serait `collecte-vide-necrase-jamais` à
    l'envers : un champ que la collecte peut légitimement rendre vide se
    remplirait depuis un autre run. Chaque entrée de cette liste est un fait que
    la source porte sur le paragraphe et qu'aucune relecture ne corrige."""
    assert CHAMPS_FAITS_DE_SOURCE == ("id_syceron", "fonction", "role_seance")
    for interdit in ("texte", "collecte", "sujet", "theme_officiel",
                     "succede_a", "position_politique", "tags_thematiques"):
        assert interdit not in CHAMPS_FAITS_DE_SOURCE
