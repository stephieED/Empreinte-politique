"""Le périmètre de collecte : geler n'est ni supprimer, ni écarter en silence (#760).

`prepare-an-matrix` retenait tout candidat à slug résolvable, donc une
candidature déclinée gardait son shard. Ces tests tiennent les trois propriétés
qui font qu'un gel reste réversible et lisible :

- il **retire du périmètre**, il ne supprime rien ;
- un statut **inconnu** est collecté, jamais écarté — l'erreur coûteuse est
  d'amputer le périmètre en silence, pas de payer un shard de trop ;
- le gel est **nommé** là où le périmètre est calculé.
"""

import json
from pathlib import Path

import pytest

import perimetre_candidats as perimetre

#: Ce fichier de tests lit la configuration committée nommée ci-dessous.
#: Le garde-fou de `conftest.py` refuse tout `.json` de `raw_data/` qu'un
#: test n'a pas déclaré (#791), et n'accepte la déclaration que si le chemin
#: est dans le `sparse-checkout` de `tests.yml` — sinon le test ne tournerait
#: qu'en local, sur ce qu'un run y a laissé.
pytestmark = pytest.mark.lit_reference_committee("raw_data/candidats.json")


def _candidat(slug, statut="declare", nom="Quelqu'un"):
    return {"nom": nom, "slug": slug, "statut": statut}


# ---------------------------------------------------------------------------
# Le prédicat
# ---------------------------------------------------------------------------


def test_un_declare_est_collecte():
    assert perimetre.est_a_collecter(_candidat("jean-dupont")) is True


def test_un_decline_est_gele():
    assert perimetre.est_a_collecter(_candidat("laurent-wauquiez", "decline")) is False


def test_un_candidat_sans_slug_nest_pas_collectable():
    """Sans slug il n'y a pas de profil à écrire — la règle de #344, inchangée."""
    assert perimetre.est_a_collecter(_candidat(None)) is False
    assert perimetre.est_a_collecter(_candidat("")) is False


def test_un_statut_inconnu_est_collecte():
    """Le défaut penche vers collecter de trop, jamais vers écarter en silence.

    Une valeur de statut ajoutée ailleurs — un lot futur, un correctif éditorial —
    ne doit pas faire disparaître quelqu'un du périmètre sans que rien ne le
    dise. C'est le patron de #510.
    """
    assert perimetre.est_a_collecter(_candidat("x", "statut_invente_demain")) is True
    assert perimetre.est_a_collecter(_candidat("y", "pressenti")) is True
    assert perimetre.est_a_collecter(_candidat("z", "officiel")) is True


def test_seul_decline_est_gele_aujourdhui():
    """L'ensemble fermé est petit exprès : tout le reste est collecté."""
    assert perimetre.STATUTS_GELES == frozenset({"decline"})


# ---------------------------------------------------------------------------
# Les deux listes
# ---------------------------------------------------------------------------


def test_le_perimetre_garde_lordre_du_fichier():
    candidats = [
        _candidat("a"),
        _candidat("b", "decline"),
        _candidat("c"),
        _candidat(None),
    ]
    assert perimetre.slugs_a_collecter(candidats) == ["a", "c"]


def test_les_geles_sont_rendus_avec_leur_statut():
    """Rendu pour être imprimé : un périmètre réduit doit se distinguer d'un
    périmètre amputé."""
    candidats = [_candidat("a"), _candidat("b", "decline")]
    assert perimetre.slugs_geles(candidats) == [("b", "decline")]


def test_un_gele_sans_slug_nest_pas_nomme():
    """Il n'était pas dans le périmètre de toute façon : le nommer ferait croire
    qu'on vient de l'en retirer."""
    assert perimetre.slugs_geles([_candidat(None, "decline")]) == []


def test_une_entree_qui_nest_pas_un_objet_ne_casse_rien():
    assert perimetre.est_a_collecter("pas un dict") is False
    assert perimetre.slugs_a_collecter(["x", None, _candidat("a")]) == ["a"]


# ---------------------------------------------------------------------------
# Sur le corpus réel
# ---------------------------------------------------------------------------


def test_les_deux_candidatures_declinees_sortent_du_perimetre():
    source = Path("raw_data/candidats.json")
    if not source.exists():  # checkout partiel
        pytest.skip("raw_data/candidats.json absent de ce checkout")
    candidats = json.loads(source.read_text(encoding="utf-8"))["candidats"]

    geles = dict(perimetre.slugs_geles(candidats))
    collectes = perimetre.slugs_a_collecter(candidats)

    assert set(geles) == {"laurent-wauquiez", "jordan-bardella"}
    assert not set(geles) & set(collectes)
    # Le gel retire du périmètre ; il ne supprime pas l'entrée du fichier.
    assert all(any(c["nom"] and c["slug"] == slug for c in candidats) for slug in geles)


def test_le_gel_ne_retire_personne_du_fichier():
    """Geler retire du périmètre ; ça ne supprime pas l'entrée.

    Le pendant côté corpus — le profil pivot reste sur disque — n'est PAS
    vérifié ici : aucun test ne lit le corpus vivant (AGENTS.md §3b). Ce que le
    gel ne touche pas, il ne le touche pas *par construction* — ce module ne
    connaît que la liste éditoriale et n'a aucun accès à `pivot_data/`.
    """
    candidats = [_candidat("a"), _candidat("b", "decline")]
    avant = [dict(c) for c in candidats]

    perimetre.slugs_a_collecter(candidats)
    perimetre.slugs_geles(candidats)

    assert candidats == avant, "le prédicat ne doit rien muter"
