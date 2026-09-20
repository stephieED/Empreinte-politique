"""#890 — le marqueur d'une source dont plus aucune donnée n'est publiée quitte
les profils de député, et seulement eux.

§7 écrit que `meta.licence_donnees` est un champ **dérivé** dont la condition de
retrait « court d'elle-même » : la clause ODbL quitte un profil le jour où ce
profil cesse de porter quoi que ce soit de Regards Citoyens. Mesuré le
13/09/2026 par un parcours récursif des deux couches, **clés de dict
comprises**, la condition était remplie sur les 1 196 profils publiés — et seul
le marqueur la retenait.

Ce que ces tests verrouillent, c'est autant le retrait que **son périmètre** :
les 21 profils qui touchent le Sénat gardent le marqueur, parce que `raw_data`
porte encore leurs URL et que leur sort est celui de #885. Un lot qui les
emporterait retirerait l'attribution **avant** d'avoir une source pour la
remplacer.

Toutes les doublures sont des répertoires `tmp_path` : aucun test ne lit
`raw_data/profiles/` ni `pivot_data/profiles/`, ni ne touche le réseau
(AGENTS.md §3, #457/#473/#488).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from licences import (  # noqa: E402
    LICENCE_AN,
    LICENCE_REGARDS_CITOYENS,
)
from purge_marqueur_regards_citoyens import (  # noqa: E402
    est_dans_le_perimetre,
    main as purge_main,
    purger,
    purger_brut,
)


def _profil_pivot(chambres, types, licence=None):
    return {
        "slug": "doublure",
        "chambres": list(chambres),
        "sources": [{"type": t, "url": f"https://example.test/{t}", "synchro_le": None}
                    for t in types],
        "meta": {"licence_donnees": licence or "", "provenance": "roster_groupe"},
        "mandats": [],
        "interventions": [],
    }


def _corpus(tmp_path, profils):
    """`profils` : `{slug: (pivot, brut | None)}`."""
    pivot_dir = tmp_path / "pivot"
    raw_dir = tmp_path / "raw"
    pivot_dir.mkdir(exist_ok=True)
    raw_dir.mkdir(exist_ok=True)
    for slug, (pivot, brut) in profils.items():
        (pivot_dir / f"{slug}.pivot.json").write_text(
            json.dumps(pivot, ensure_ascii=False), encoding="utf-8")
        if brut is not None:
            (raw_dir / f"{slug}.json").write_text(
                json.dumps(brut, ensure_ascii=False), encoding="utf-8")
    return pivot_dir, raw_dir


def _brut(journal):
    return {"slug": "doublure", "meta": {"synchro_sources": dict(journal)}, "mandats": []}


# ---------------------------------------------------------------------------
# Le périmètre — ce que le lot refuse de toucher
# ---------------------------------------------------------------------------

def test_un_profil_de_depute_est_dans_le_perimetre():
    assert est_dans_le_perimetre(_profil_pivot(["AN"], ["nosdeputes", "assemblee_nationale"]))


def test_un_profil_qui_touche_le_senat_garde_son_marqueur():
    """`bruno-retailleau` et `jean-luc-melenchon` : leur marqueur couvre une
    carrière sénatoriale, et son sort est celui de #885."""
    assert not est_dans_le_perimetre(
        _profil_pivot(["AN", "Senat"], ["nosdeputes", "nossenateurs"]))


def test_un_profil_sans_aucune_chambre_est_hors_perimetre():
    """Les 19 membres de roster sénatorial ne publient aucune chambre, leur
    collecte étant suspendue (#528). Une liste vide n'est pas « pas le Sénat »,
    c'est « on ne sait pas » — §2 règle 5 interdit de lire une absence comme un
    constat, et `raw_data` porte encore leur URL `nosdeputes.fr`."""
    assert not est_dans_le_perimetre(_profil_pivot([], ["nosdeputes"]))


def test_un_profil_sans_marqueur_n_est_pas_touche():
    assert not est_dans_le_perimetre(_profil_pivot(["AN"], ["assemblee_nationale"]))


# ---------------------------------------------------------------------------
# Le retrait, aux deux couches
# ---------------------------------------------------------------------------

def test_le_marqueur_part_des_deux_couches(tmp_path):
    """Retiré d'une seule couche, il redescendrait au run suivant : c'est la
    leçon de #729, et la raison pour laquelle ce script ouvre le brut."""
    pivot_dir, raw_dir = _corpus(tmp_path, {
        "gabriel-attal": (
            _profil_pivot(["AN"], ["nosdeputes", "assemblee_nationale"],
                          licence=LICENCE_REGARDS_CITOYENS),
            _brut({"assemblee_nationale": "2026-09-12T15:51:07+0000", "nosdeputes": None}),
        ),
    })

    rapport = purger(pivot_dir, raw_dir, appliquer=True)

    assert rapport["nb_profils_touches"] == 1
    assert rapport["nb_entrees_sources_retirees"] == 1
    assert rapport["nb_cles_journal_retirees"] == 1
    pivot = json.loads((pivot_dir / "gabriel-attal.pivot.json").read_text())
    assert [s["type"] for s in pivot["sources"]] == ["assemblee_nationale"]
    brut = json.loads((raw_dir / "gabriel-attal.json").read_text())
    assert "nosdeputes" not in brut["meta"]["synchro_sources"]
    assert "assemblee_nationale" in brut["meta"]["synchro_sources"]


def test_la_licence_est_recomposee_et_non_reecrite(tmp_path):
    """§4 : un champ dérivé se recompose après l'étape qui le déplace. La chaîne
    vient de `licences.py`, jamais d'un littéral de ce module (§7)."""
    pivot_dir, raw_dir = _corpus(tmp_path, {
        "gabriel-attal": (
            _profil_pivot(["AN"], ["nosdeputes", "assemblee_nationale"],
                          licence=f"{LICENCE_AN} + {LICENCE_REGARDS_CITOYENS}"),
            _brut({"nosdeputes": None}),
        ),
    })

    rapport = purger(pivot_dir, raw_dir, appliquer=True)

    profil = rapport["profils"][0]
    assert LICENCE_REGARDS_CITOYENS in profil["licence_avant"]
    assert LICENCE_REGARDS_CITOYENS not in profil["licence_apres"]
    assert profil["licence_apres"] == LICENCE_AN
    pivot = json.loads((pivot_dir / "gabriel-attal.pivot.json").read_text())
    assert pivot["meta"]["licence_donnees"] == LICENCE_AN


def test_la_simulation_n_ecrit_rien(tmp_path):
    """Sans `--apply`, le relevé est complet et le disque intact : un retrait se
    lit avant de s'appliquer."""
    pivot_dir, raw_dir = _corpus(tmp_path, {
        "gabriel-attal": (
            _profil_pivot(["AN"], ["nosdeputes"], licence=LICENCE_REGARDS_CITOYENS),
            _brut({"nosdeputes": None}),
        ),
    })
    avant_pivot = (pivot_dir / "gabriel-attal.pivot.json").read_text()
    avant_brut = (raw_dir / "gabriel-attal.json").read_text()

    rapport = purger(pivot_dir, raw_dir)

    assert rapport["applique"] is False
    assert rapport["nb_profils_touches"] == 1
    assert (pivot_dir / "gabriel-attal.pivot.json").read_text() == avant_pivot
    assert (raw_dir / "gabriel-attal.json").read_text() == avant_brut


def test_les_profils_hors_perimetre_sont_comptes_et_nommes(tmp_path):
    """Un lot partiel doit dire ce qu'il laisse, sinon « 454 retirés » se lit
    comme « il n'en reste plus »."""
    pivot_dir, raw_dir = _corpus(tmp_path, {
        "gabriel-attal": (_profil_pivot(["AN"], ["nosdeputes"]), _brut({"nosdeputes": None})),
        "bruno-retailleau": (_profil_pivot(["AN", "Senat"], ["nosdeputes", "nossenateurs"]),
                             _brut({"nosdeputes": None})),
        "gerard-larcher": (_profil_pivot([], ["nosdeputes"]), _brut({"nosdeputes": None})),
    })

    rapport = purger(pivot_dir, raw_dir, appliquer=True)

    assert rapport["nb_profils_touches"] == 1
    assert rapport["nb_hors_perimetre"] == 2
    assert sorted(rapport["hors_perimetre"]) == ["bruno-retailleau", "gerard-larcher"]
    garde = json.loads((pivot_dir / "bruno-retailleau.pivot.json").read_text())
    assert {s["type"] for s in garde["sources"]} == {"nosdeputes", "nossenateurs"}


# ---------------------------------------------------------------------------
# Ce qui ne doit pas bouger
# ---------------------------------------------------------------------------

def test_un_horodatage_de_synchro_an_n_est_jamais_touche(tmp_path):
    """`normalize_profil:647` lit `assemblee_nationale` **puis** `nosdeputes` en
    repli. Les 11 profils dont la clé porte un horodatage réel ont tous
    `assemblee_nationale` renseigné : la branche de repli n'est jamais
    empruntée, et aucun `synchro_le` ne bouge."""
    pivot_dir, raw_dir = _corpus(tmp_path, {
        "loic-prud-homme": (
            _profil_pivot(["AN"], ["nosdeputes", "assemblee_nationale"]),
            _brut({"assemblee_nationale": "2026-09-12T15:45:11+0000",
                   "nosdeputes": "2026-08-24T21:44:22+0000"}),
        ),
    })

    purger(pivot_dir, raw_dir, appliquer=True)

    journal = json.loads((raw_dir / "loic-prud-homme.json").read_text())["meta"]["synchro_sources"]
    assert journal == {"assemblee_nationale": "2026-09-12T15:45:11+0000"}


def test_un_brut_sans_cle_de_journal_ne_bloque_pas(tmp_path):
    """Le pivot est retiré même quand le brut n'a rien à retirer : les deux
    couches sont traitées indépendamment, et une absence n'est pas une erreur."""
    pivot_dir, raw_dir = _corpus(tmp_path, {
        "gabriel-attal": (_profil_pivot(["AN"], ["nosdeputes"]),
                          _brut({"assemblee_nationale": None})),
    })

    rapport = purger(pivot_dir, raw_dir, appliquer=True)

    assert rapport["nb_entrees_sources_retirees"] == 1
    assert rapport["nb_cles_journal_retirees"] == 0


def test_un_brut_absent_est_declare_et_le_pivot_est_quand_meme_purge(tmp_path):
    pivot_dir, raw_dir = _corpus(tmp_path, {
        "gabriel-attal": (_profil_pivot(["AN"], ["nosdeputes"]), None),
    })

    rapport = purger(pivot_dir, raw_dir, appliquer=True)

    assert rapport["nb_brut_absent"] == 1
    assert rapport["nb_entrees_sources_retirees"] == 1


def test_un_pivot_illisible_est_declare_jamais_ignore(tmp_path):
    """Un profil illisible n'est pas « rien à retirer » : c'est un retrait qui
    n'a pas eu lieu (§2 règle 5)."""
    pivot_dir, raw_dir = _corpus(tmp_path, {})
    (pivot_dir / "casse.pivot.json").write_text("{ pas du json", encoding="utf-8")

    rapport = purger(pivot_dir, raw_dir)

    assert rapport["nb_illisibles"] == 1
    assert rapport["illisibles"] == ["casse"]


def test_un_fichier_de_service_n_est_pas_un_profil(tmp_path):
    """`Path.glob` rend les dotfiles, contrairement au module `glob` (#518)."""
    pivot_dir, raw_dir = _corpus(tmp_path, {
        "gabriel-attal": (_profil_pivot(["AN"], ["nosdeputes"]), _brut({"nosdeputes": None})),
    })
    (pivot_dir / ".progress.pivot.json").write_text('{"slug": "x"}', encoding="utf-8")

    rapport = purger(pivot_dir, raw_dir)

    assert rapport["nb_profils_touches"] == 1
    assert rapport["nb_illisibles"] == 0


def test_purger_brut_sur_un_meta_sans_journal():
    assert purger_brut({"meta": {}}) is False
    assert purger_brut({}) is False
    assert purger_brut({"meta": {"synchro_sources": {"assemblee_nationale": None}}}) is False


def test_only_ne_traite_qu_un_profil(tmp_path):
    pivot_dir, raw_dir = _corpus(tmp_path, {
        "gabriel-attal": (_profil_pivot(["AN"], ["nosdeputes"]), _brut({"nosdeputes": None})),
        "elisabeth-borne": (_profil_pivot(["AN"], ["nosdeputes"]), _brut({"nosdeputes": None})),
    })

    rapport = purger(pivot_dir, raw_dir, appliquer=True, seulement="gabriel-attal")

    assert rapport["nb_profils_touches"] == 1
    autre = json.loads((pivot_dir / "elisabeth-borne.pivot.json").read_text())
    assert [s["type"] for s in autre["sources"]] == ["nosdeputes"]


def test_main_rend_zero_et_annonce_le_mode(tmp_path, capsys):
    pivot_dir, raw_dir = _corpus(tmp_path, {
        "gabriel-attal": (_profil_pivot(["AN"], ["nosdeputes"]), _brut({"nosdeputes": None})),
    })

    code = purge_main(["--pivot-dir", str(pivot_dir), "--raw-dir", str(raw_dir)])

    assert code == 0
    sortie = capsys.readouterr().out
    assert "simulation" in sortie
    assert "1 profil(s) touché(s)" in sortie
