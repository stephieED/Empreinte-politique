"""Liste dédupliquée des scrutins, partagée entre profils et groupes (#432).

Un scrutin est identique pour tous ses votants : son méta était recopié dans
chacun des profils l'ayant voté, jusqu'à 74 fois. Mesuré sur les données
committées : 398 085 paires (membre, vote) pour 17 422 scrutins distincts, et
179,8 Mo de votes ramenés à 17,9 Mo de mapping + 8,1 Mo d'index (−85,5 %).

Les tests ci-dessous portent sur les trois propriétés qui rendent cette
normalisation sûre : la résolution reste globale au corpus, la fusion de deux
index est additive (un run partiel ne doit pas faire disparaître des scrutins
que des mappings référencent), et rien n'est jamais résolu par défaut.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scrutins_index import (
    CHAMPS_SCRUTIN,
    SCHEMA_VERSION,
    ScrutinsIndex,
    charger,
    cle_scrutin,
    construire_index,
    decomposer_id,
    ecrire,
    iter_votes_du_repertoire,
    merge_scrutins_index,
    rafraichir,
)
from scrutins_legislature import LegislatureIrresoluble


def _vote(numero="4084", date="2024-06-07", legislature="16", **extra):
    base = {
        "numero_scrutin": numero, "date": date, "legislature": legislature,
        "position": "pour", "titre": "PLF", "sort": "adopté",
        "url_source": "https://an/16/scrutins/4084",
    }
    base.update(extra)
    return base


# ── Identifiants ─────────────────────────────────────────────────────────────

def test_cle_scrutin_porte_la_legislature():
    """Le numéro repart à 1 à chaque législature : un identifiant qui ne la
    porterait pas confondrait deux scrutins sans rapport (AGENTS.md §5)."""
    assert cle_scrutin("16", "4084") == "an:16:4084"
    assert cle_scrutin("17", "4084") != cle_scrutin("16", "4084")


@pytest.mark.parametrize("valeur", ["", "an:16", "16:4084", "an::4084", "an:16:", "an:16:4084:x", None, 42])
def test_decomposer_id_refuse_une_forme_non_reconnue(valeur):
    """Un identifiant mal formé ne doit pas se faire deviner."""
    assert decomposer_id(valeur) == (None, None)


def test_decomposer_id_est_l_inverse_de_cle_scrutin():
    assert decomposer_id(cle_scrutin("16", "4084")) == ("16", "4084")


# ── Construction ─────────────────────────────────────────────────────────────

def test_construire_index_deduplique_les_occurrences():
    index, echecs = construire_index([_vote(), _vote(), _vote()])

    assert echecs == []
    assert len(index) == 1
    assert index.get("an:16:4084")["texte"] == "PLF"


def test_construire_index_lit_les_deux_schemas_de_champs():
    """Le brut nomme `titre`/`url_source` ce que le pivot nomme
    `texte`/`source_url` : accepter les deux permet de reconstruire l'index
    depuis l'un comme depuis l'autre, donc de comparer avant/après."""
    index, _ = construire_index([
        {"numero_scrutin": "1", "date": "2026-01-05", "legislature": "17",
         "texte": "Depuis un pivot", "source_url": "https://x"},
    ])
    scrutin = index.get("an:17:1")
    assert scrutin["texte"] == "Depuis un pivot"
    assert scrutin["source_url"] == "https://x"


def test_construire_index_complete_les_champs_manquants_sans_ecraser():
    """Les 7 champs communs sont identiques sur les 398 085 paires mesurées,
    mais une collecte partielle peut laisser un champ null chez l'un et
    renseigné chez l'autre : on complète, on n'écrase pas."""
    index, _ = construire_index([
        _vote(sort=None, titre="PLF"),
        _vote(sort="adopté", titre="Titre concurrent"),
    ])
    scrutin = index.get("an:16:4084")
    assert scrutin["sort"] == "adopté"       # complété
    assert scrutin["texte"] == "PLF"         # première valeur non nulle conservée


def test_construire_index_resout_par_jumeau_a_travers_le_corpus():
    """La résolution est globale : un profil est soit entièrement sur l'ancien
    chemin de collecte, soit sur le nouveau, donc le jumeau étiqueté vit
    toujours dans un autre fichier."""
    index, echecs = construire_index([
        _vote(legislature=None),   # profil « ancien »
        _vote(legislature="16"),   # profil « récent »
    ])

    assert echecs == []
    assert index.get("an:16:4084")["legislature_provenance"] == "collectee"


def test_construire_index_trace_une_derivation_calendaire():
    index, _ = construire_index([_vote(numero="632", date="2022-11-25", legislature=None)])
    assert index.get("an:16:632")["legislature_provenance"] == "derivee_du_calendrier"


def test_construire_index_strict_leve_sur_un_scrutin_irresoluble():
    """Un index amputé produirait des profils dont une partie des votes ne
    référence rien, sans que rien ne le signale."""
    with pytest.raises(LegislatureIrresoluble):
        construire_index([_vote(date="2024-07-01", legislature=None)])


def test_construire_index_non_strict_rend_les_echecs_et_omet_le_scrutin():
    index, echecs = construire_index(
        [_vote(date="2024-07-01", legislature=None), _vote()], strict=False,
    )
    assert len(echecs) == 1
    assert len(index) == 1          # le résoluble est là, l'autre est absent
    assert index.get("an:16:4084") is not None


def test_construire_index_signale_un_jumeau_contradictoire():
    """Deux étiquettes pour le même `(numero, date)` : aucune raison d'en
    préférer une, donc échec plutôt que choix arbitraire."""
    with pytest.raises(LegislatureIrresoluble):
        construire_index([_vote(legislature="16"), _vote(legislature="17")])


def test_construire_index_ignore_une_entree_non_dict():
    index, _ = construire_index([_vote(), "pas un vote", None])
    assert len(index) == 1


# ── Résolution d'un vote vers son scrutin ────────────────────────────────────

def test_identifiant_de_vote_resout_sans_legislature():
    """C'est tout l'intérêt de l'index côté normalisation : le vote qui n'a pas
    de législature retrouve la sienne."""
    index, _ = construire_index([_vote(legislature="16"), _vote(legislature=None)])
    assert index.identifiant_de_vote({"numero_scrutin": "4084", "date": "2024-06-07"}) == "an:16:4084"


def test_identifiant_de_vote_accepte_un_numero_non_str():
    index, _ = construire_index([_vote()])
    assert index.identifiant_de_vote({"numero_scrutin": 4084, "date": "2024-06-07"}) == "an:16:4084"


def test_identifiant_de_vote_rend_none_sur_un_scrutin_inconnu():
    index, _ = construire_index([_vote()])
    assert index.identifiant_de_vote({"numero_scrutin": "9999", "date": "2024-06-07"}) is None


def test_get_sur_identifiant_inconnu_rend_none_plutot_que_de_lever():
    """Un profil peut référencer un scrutin qu'un index partiel ne connaît pas :
    aux appelants d'en faire une donnée manquante, jamais une valeur inventée."""
    index, _ = construire_index([_vote()])
    assert index.get("an:17:1") is None
    assert index.get(None) is None


# ── Fusion additive ──────────────────────────────────────────────────────────

def test_merge_conserve_les_scrutins_absents_du_nouvel_index():
    """Le cœur du sujet : un run qui ne régénère qu'une tranche ne voit qu'une
    partie des scrutins. Écraser l'index laisserait les mappings des profils non
    retraités pointer dans le vide — la leçon de #450, au niveau de l'index."""
    ancien, _ = construire_index([_vote(numero="1"), _vote(numero="2")])
    nouveau, _ = construire_index([_vote(numero="2")])

    fusionne = merge_scrutins_index(ancien, nouveau)

    assert set(fusionne.par_id) == {"an:16:1", "an:16:2"}


def test_merge_prend_la_nouvelle_valeur_renseignee():
    ancien, _ = construire_index([_vote(sort=None)])
    nouveau, _ = construire_index([_vote(sort="rejeté")])
    assert merge_scrutins_index(ancien, nouveau).get("an:16:4084")["sort"] == "rejeté"


def test_merge_ne_regresse_jamais_vers_null():
    ancien, _ = construire_index([_vote(sort="adopté")])
    nouveau, _ = construire_index([_vote(sort=None)])
    assert merge_scrutins_index(ancien, nouveau).get("an:16:4084")["sort"] == "adopté"


# ── Écriture / lecture ───────────────────────────────────────────────────────

def test_ecrire_puis_charger_est_un_aller_retour_fidele(tmp_path):
    index, _ = construire_index([_vote(numero="1"), _vote(numero="2")])
    chemin = tmp_path / "scrutins.json"

    ecrire(chemin, index, genere_le="2026-08-19T12:00:00+0000")
    relu = charger(chemin)

    assert set(relu.par_id) == set(index.par_id)
    assert relu.get("an:16:1") == index.get("an:16:1")
    donnees = json.loads(chemin.read_text(encoding="utf-8"))
    assert donnees["schema_version"] == SCHEMA_VERSION
    assert donnees["genere_le"] == "2026-08-19T12:00:00+0000"


def test_ecrire_en_json_compact(tmp_path):
    """Même règle que les profils (#433) : l'indentation pesait 35 % du volume."""
    chemin = tmp_path / "scrutins.json"
    index, _ = construire_index([_vote()])
    ecrire(chemin, index)
    assert len(chemin.read_text(encoding="utf-8").splitlines()) == 1


def test_liste_est_triee_par_identifiant(tmp_path):
    """Ordre stable d'un run à l'autre : git ne doit voir que les vraies
    différences."""
    index, _ = construire_index([_vote(numero="9"), _vote(numero="1"), _vote(numero="5")])
    assert [s["id"] for s in index.liste()] == ["an:16:1", "an:16:5", "an:16:9"]


def test_charger_un_fichier_absent_rend_un_index_vide(tmp_path):
    assert len(charger(tmp_path / "jamais_ecrit.json")) == 0


def test_index_contient_tous_les_champs_du_scrutin():
    index, _ = construire_index([_vote()])
    scrutin = index.get("an:16:4084")
    for champ in CHAMPS_SCRUTIN:
        assert champ in scrutin, champ
    assert {"id", "legislature", "legislature_provenance", "numero_scrutin"} <= set(scrutin)


# ── Lecture en flux d'un répertoire ──────────────────────────────────────────

def _ecrire_profil(dossier, slug, votes):
    dossier.mkdir(parents=True, exist_ok=True)
    (dossier / f"{slug}.json").write_text(
        json.dumps({"slug": slug, "votes": votes}, ensure_ascii=False), encoding="utf-8"
    )


def test_iter_votes_lit_tous_les_profils(tmp_path):
    _ecrire_profil(tmp_path, "alice", [_vote(numero="1")])
    _ecrire_profil(tmp_path, "bob", [_vote(numero="2")])
    assert len(list(iter_votes_du_repertoire(tmp_path))) == 2


def test_iter_votes_ignore_un_profil_illisible(tmp_path, capsys):
    """Un fichier corrompu ne doit pas priver l'index de tous les autres."""
    _ecrire_profil(tmp_path, "alice", [_vote()])
    (tmp_path / "casse.json").write_text("{ pas du json", encoding="utf-8")

    assert len(list(iter_votes_du_repertoire(tmp_path))) == 1
    assert "Lecture impossible" in capsys.readouterr().out


def test_iter_votes_repertoire_absent_ne_plante_pas(tmp_path):
    assert list(iter_votes_du_repertoire(tmp_path / "absent")) == []


def test_rafraichir_fusionne_avec_l_index_existant(tmp_path):
    chemin = tmp_path / "scrutins.json"
    ecrire(chemin, construire_index([_vote(numero="1")])[0])

    profils = tmp_path / "profiles"
    _ecrire_profil(profils, "alice", [_vote(numero="2")])
    index, _ = rafraichir(profils, chemin)

    assert set(index.par_id) == {"an:16:1", "an:16:2"}
    assert set(charger(chemin).par_id) == {"an:16:1", "an:16:2"}


def test_rafraichir_sans_fusion_reconstruit_entierement(tmp_path):
    chemin = tmp_path / "scrutins.json"
    ecrire(chemin, construire_index([_vote(numero="1")])[0])

    profils = tmp_path / "profiles"
    _ecrire_profil(profils, "alice", [_vote(numero="2")])
    index, _ = rafraichir(profils, chemin, fusionner=False)

    assert set(index.par_id) == {"an:16:2"}
