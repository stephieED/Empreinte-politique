#!/usr/bin/env python3
"""
test_purge_textes_portes_roster_747.py — La purge du résidu `textes_portes` des
profils de roster, et le critère qui ne se transpose pas d'un étage à l'autre
(#747).

49 entrées ont survécu un mois sur 15 profils de roster dont la collecte
déclare, dans le fichier lui-même, ne pas demander cette liste
(`meta.collecte_ecartee`, #539). Résidu d'avant #357, que la fusion additive
conserve indéfiniment — la liste neuve est **vide**, pas incomplète — et
qu'aucun run ne rafraîchira, la collecte de cette liste étant coupée en dur sur
ce job.

Ce que ces tests verrouillent :

- la purge passe les DEUX étages, la leçon de #729/#730 ;
- **le critère, lui, ne les traverse pas** : `meta.provenance` est un champ du
  pivot, le brut ne le porte pas, et `meta.collecte_ecartee` seul ne
  discrimine rien — un candidat déclaré est aussi un membre de roster, dont le
  job réécrit le `meta`. Le critère brut seul aurait purgé 71 dossiers sur 4
  fiches candidats publiées. C'est le test le plus important du fichier ;
- la cible est la liste **vide**, jamais la clé retirée ;
- `validate_profil()` refuse désormais `sort: null` sans `sort_non_resolu` —
  l'invariant que le schéma promettait sans l'imposer.

Aucun test ne lit `pivot_data/`, `raw_data/profiles/` ni le réseau.
"""

from pathlib import Path
import importlib.util
import json
import sys

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from schema_pivot import validate_profil  # noqa: E402


def _charger_script():
    chemin = RACINE / "scripts" / "purger_textes_portes_roster_747.py"
    spec = importlib.util.spec_from_file_location("purge_747", chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PURGE = _charger_script()


def _entree(dossier_id="DLR5L17N51672"):
    return {
        "titre": "Soins palliatifs et d'accompagnement",
        "dossier_id": dossier_id,
        "role": "auteur",
        "nature_texte": None,
        "type_rapport": None,
        "stade_procedural": "promulgue",
        "sort": None,
        "sort_non_resolu": None,
        "date_min": "2025-03-11",
        "date_max": "2026-05-26",
        "legislature": "17",
        "source_url": "https://www.assemblee-nationale.fr/dyn/17/dossiers/x",
    }


def _ecrire_profil(racine, slug, provenance, ecartee, entrees):
    pivot = racine / "pivot_data" / "profiles"
    brut = racine / "raw_data" / "profiles"
    pivot.mkdir(parents=True, exist_ok=True)
    brut.mkdir(parents=True, exist_ok=True)
    (pivot / f"{slug}.pivot.json").write_text(json.dumps({
        "id": slug,
        "nom": slug,
        "textes_portes": list(entrees),
        "meta": {"provenance": provenance, "collecte_ecartee": list(ecartee)},
    }, ensure_ascii=False), encoding="utf-8")
    # Le brut ne porte PAS `provenance` — c'est tout le sujet.
    (brut / f"{slug}.json").write_text(json.dumps({
        "id": slug,
        "dossiers_legislatifs": list(entrees),
        "meta": {"collecte_ecartee": list(ecartee)},
    }, ensure_ascii=False), encoding="utf-8")


def _lire(racine, slug):
    pivot = json.loads((racine / "pivot_data" / "profiles" / f"{slug}.pivot.json")
                       .read_text(encoding="utf-8"))
    brut = json.loads((racine / "raw_data" / "profiles" / f"{slug}.json")
                      .read_text(encoding="utf-8"))
    return pivot, brut


def test_la_purge_passe_les_deux_etages(tmp_path):
    _ecrire_profil(tmp_path, "annie-vidal", "roster_groupe",
                   ["interventions", "textes_portes"], [_entree(), _entree("DLR5L17N52958")])

    rapport = PURGE.purger(tmp_path, ecrire=True)

    assert rapport["pivot"] == {"fichiers": 1, "entrees": 2}
    assert rapport["brut"] == {"fichiers": 1, "entrees": 2}
    pivot, brut = _lire(tmp_path, "annie-vidal")
    assert pivot["textes_portes"] == []
    assert brut["dossiers_legislatifs"] == []


def test_la_cible_est_la_liste_vide_jamais_la_cle_retiree(tmp_path):
    """`[]` dit « rien à publier » ; une clé absente dirait « jamais collecté ».

    C'est la forme que portent déjà les 613 autres membres de roster.
    """
    _ecrire_profil(tmp_path, "annie-vidal", "roster_groupe",
                   ["textes_portes"], [_entree()])

    PURGE.purger(tmp_path, ecrire=True)

    pivot, brut = _lire(tmp_path, "annie-vidal")
    assert "textes_portes" in pivot
    assert "dossiers_legislatifs" in brut


def test_un_candidat_declare_n_est_jamais_purge_meme_si_son_brut_declare_la_liste_ecartee(tmp_path):
    """Le test qui compte : le critère du brut, seul, détruirait du publié.

    Un candidat déclaré est aussi un membre de roster ; le job roster réécrit
    son `meta`, donc son brut porte `collecte_ecartee: ["textes_portes"]` alors
    que ses `textes_portes` viennent d'`extract-an`, pleinement qualifiés.
    Mesuré sur le corpus du 06/09/2026 : 71 dossiers sur 4 fiches publiées
    (gabriel-attal 34, marine-le-pen 23, laurent-wauquiez 9, jerome-guedj 5).
    """
    qualifie = {**_entree(), "sort": "rejete", "nature_texte": "projet_de_loi",
                "sort_non_resolu": None}
    _ecrire_profil(tmp_path, "gabriel-attal", "candidat_declare",
                   ["interventions", "textes_portes"], [qualifie])

    rapport = PURGE.purger(tmp_path, ecrire=True)

    assert rapport["pivot"]["entrees"] == 0
    assert rapport["brut"]["entrees"] == 0
    pivot, brut = _lire(tmp_path, "gabriel-attal")
    assert pivot["textes_portes"] == [qualifie]
    assert brut["dossiers_legislatifs"] == [qualifie]


def test_un_roster_qui_ne_declare_rien_d_ecarte_est_laisse_en_l_etat(tmp_path):
    """Le critère est la contradiction déclarée, pas la provenance seule.

    Un profil de roster collecté un jour en mode plein, et qui le dit, porte
    une liste dont personne n'a écrit qu'elle n'avait pas été demandée : la
    purger serait une perte non déclarée.
    """
    _ecrire_profil(tmp_path, "quelqu-un", "roster_groupe", ["interventions"], [_entree()])

    rapport = PURGE.purger(tmp_path, ecrire=True)

    assert rapport["pivot"]["entrees"] == 0
    pivot, _ = _lire(tmp_path, "quelqu-un")
    assert len(pivot["textes_portes"]) == 1


def test_la_purge_est_idempotente(tmp_path):
    """La fusion étant additive sur une liste neuve vide, un passage suffit."""
    _ecrire_profil(tmp_path, "annie-vidal", "roster_groupe",
                   ["textes_portes"], [_entree()])

    PURGE.purger(tmp_path, ecrire=True)
    second = PURGE.purger(tmp_path, ecrire=True)

    assert second["pivot"]["entrees"] == 0
    assert second["brut"]["entrees"] == 0


def test_dry_run_n_ecrit_rien(tmp_path):
    _ecrire_profil(tmp_path, "annie-vidal", "roster_groupe",
                   ["textes_portes"], [_entree()])

    rapport = PURGE.purger(tmp_path, ecrire=False)

    assert rapport["pivot"]["entrees"] == 1
    pivot, brut = _lire(tmp_path, "annie-vidal")
    assert len(pivot["textes_portes"]) == 1
    assert len(brut["dossiers_legislatifs"]) == 1


def _profil_minimal(entree):
    return {"id": "x", "nom": "X", "textes_portes": [entree]}


def test_validate_profil_refuse_un_sort_nul_sans_motif():
    """L'invariant que `schema_pivot` promettait sans l'imposer (#747)."""
    erreurs = validate_profil(_profil_minimal(_entree()))

    assert any("sans sort_non_resolu" in e for e in erreurs), erreurs


def test_validate_profil_accepte_un_sort_nul_qui_nomme_sa_cause():
    entree = {**_entree(), "sort_non_resolu": {"motif": "sans_decision"}}

    erreurs = validate_profil(_profil_minimal(entree))

    assert not [e for e in erreurs if "sort" in e], erreurs
