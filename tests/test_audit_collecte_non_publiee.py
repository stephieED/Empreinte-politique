"""#511 — un profil collecté et publié nulle part doit être signalé et bloquer.

Le run `32405297873` (20/08/2026) s'est conclu en **succès** après avoir écrit
un roster de 0 candidat : la passe pivot roster a itéré sur le vide et le commit
`68bc094` porte 229 profils bruts pour 209 pivots. Les 20 membres collectés par
ce run — jusqu'à 3 536 votes et 124 mandats chacun — ne sont publiés nulle part,
et **aucun des deux garde-fous existants ne pouvait le voir** :

  - `audit_diff_profils` (#460/#470) compare un avant et un après. Rien n'a été
    *perdu* : les deux compteurs montent, seule la correspondance manque ;
  - `audit_integrite_referentielle` (#485) vérifie que les clés publiées
    résolvent. Ce qui n'a jamais été publié ne porte aucune clé.

Toutes les doublures ici sont des répertoires `tmp_path` : aucun test ne lit
`raw_data/profiles/` ni `pivot_data/profiles/`, ni ne touche le réseau
(AGENTS.md §3, #457/#473/#488).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from audit_collecte_non_publiee import (  # noqa: E402
    PLAFOND_EXEMPLES,
    SEUIL_NON_PUBLIES,
    auditer,
    generate_markdown_report,
    main as audit_main,
)


def _corpus(tmp_path, bruts, pivots):
    """Deux répertoires de doublures, remplis de fichiers au contenu indifférent.

    Le contenu EST indifférent : le contrôle ne parse aucun profil, il compare
    deux listes de noms de fichiers. Le corpus réel pèse 1 642 Mo de bruts.
    """
    raw_dir = tmp_path / "raw"
    pivot_dir = tmp_path / "pivot"
    raw_dir.mkdir()
    pivot_dir.mkdir()
    for slug in bruts:
        (raw_dir / f"{slug}.json").write_text("{}", encoding="utf-8")
    for slug in pivots:
        (pivot_dir / f"{slug}.pivot.json").write_text("{}", encoding="utf-8")
    return raw_dir, pivot_dir


# ---------------------------------------------------------------------------
# Le cas nominal
# ---------------------------------------------------------------------------

def test_corpus_sain_ne_bloque_pas(tmp_path):
    raw_dir, pivot_dir = _corpus(tmp_path, ["alice", "bob"], ["alice", "bob"])

    rapport = auditer(raw_dir, pivot_dir)

    assert rapport["nb_bruts"] == 2
    assert rapport["nb_pivots"] == 2
    assert rapport["nb_non_publies"] == 0
    assert rapport["bloquant"] is False


def test_le_seuil_par_defaut_est_zero():
    """Mesuré, pas arrondi : 0 écart sur les 12 commits de run du 16 au
    20/08/2026, pendant que le corpus passait de 48 à 209 profils."""
    assert SEUIL_NON_PUBLIES == 0


# ---------------------------------------------------------------------------
# L'incident
# ---------------------------------------------------------------------------

def test_un_profil_collecte_sans_pivot_bloque(tmp_path):
    raw_dir, pivot_dir = _corpus(tmp_path, ["alice", "bob"], ["alice"])

    rapport = auditer(raw_dir, pivot_dir)

    assert rapport["nb_non_publies"] == 1
    assert rapport["non_publies"] == ["bob"]
    assert rapport["bloquant"] is True


def test_l_incident_du_run_32405297873_est_rejoue(tmp_path):
    """229 bruts, 209 pivots — les 20 membres roster collectés et non publiés.

    Le contrôle ne connaît pas la cause (roster vide) : il constate l'écart, ce
    qui est précisément ce qui manquait — la cause était visible dans les logs
    du run, mais rien ne la rapprochait du corpus.
    """
    membres = [f"membre-{i:03d}" for i in range(20)]
    publies = [f"publie-{i:03d}" for i in range(209)]
    raw_dir, pivot_dir = _corpus(tmp_path, publies + membres, publies)

    rapport = auditer(raw_dir, pivot_dir)

    assert (rapport["nb_bruts"], rapport["nb_pivots"]) == (229, 209)
    assert rapport["nb_non_publies"] == 20
    assert rapport["bloquant"] is True
    assert set(rapport["non_publies"]) == set(membres)


def test_le_rapport_nomme_les_slugs_non_publies(tmp_path):
    """Un constat non actionnable ne sert à rien : c'est le critère de #485,
    repris ici — nommer ce qu'il faut aller republier."""
    raw_dir, pivot_dir = _corpus(tmp_path, ["alice", "bob"], ["alice"])

    markdown = generate_markdown_report(auditer(raw_dir, pivot_dir))

    assert "`bob`" in markdown
    assert "Collectés mais non publiés" in markdown


def test_les_exemples_sont_plafonnes_mais_le_total_est_exact(tmp_path):
    """543 lignes identiques ne s'utilisent pas ; le total, si."""
    membres = [f"membre-{i:03d}" for i in range(543)]
    raw_dir, pivot_dir = _corpus(tmp_path, membres, [])

    rapport = auditer(raw_dir, pivot_dir)

    assert rapport["nb_non_publies"] == 543
    assert len(rapport["non_publies"]) == PLAFOND_EXEMPLES
    assert len(rapport["non_publies_complets"]) == 543
    assert "et 523 autre(s)" in generate_markdown_report(rapport)


# ---------------------------------------------------------------------------
# Ce qui est rapporté sans bloquer, et ce qui l'est à tort
# ---------------------------------------------------------------------------

def test_un_pivot_sans_brut_est_rapporte_sans_bloquer(tmp_path):
    """Rien ne supprime un pivot dont le brut aurait été retiré du dépôt :
    compteur de dérive, jamais un verdict (même raisonnement que les entrées
    d'index jamais référencées de #485)."""
    raw_dir, pivot_dir = _corpus(tmp_path, ["alice"], ["alice", "fantome"])

    rapport = auditer(raw_dir, pivot_dir)

    assert rapport["nb_publies_sans_brut"] == 1
    assert rapport["publies_sans_brut"] == ["fantome"]
    assert rapport["bloquant"] is False


def test_un_repertoire_absent_ne_rend_pas_un_rapport_vert(tmp_path):
    """« Rien à comparer » n'est pas « rien à signaler » — c'est exactement la
    faute que ce contrôle traque (AGENTS.md §2 règle 5)."""
    rapport = auditer(tmp_path / "absent", tmp_path / "aussi-absent")

    assert rapport["repertoire_brut_absent"] is True
    assert rapport["repertoire_pivot_absent"] is True
    assert rapport["bloquant"] is True


def test_un_pivot_egare_dans_le_repertoire_brut_n_est_pas_compte_comme_brut(tmp_path):
    """`.pivot.json` se termine aussi par `.json` : dépouiller au mauvais
    suffixe inventerait un slug `bob.pivot` éternellement non publié."""
    raw_dir, pivot_dir = _corpus(tmp_path, ["alice"], ["alice"])
    (raw_dir / "bob.pivot.json").write_text("{}", encoding="utf-8")

    rapport = auditer(raw_dir, pivot_dir)

    assert rapport["nb_bruts"] == 1
    assert rapport["bloquant"] is False


def test_les_fichiers_non_json_sont_ignores(tmp_path):
    raw_dir, pivot_dir = _corpus(tmp_path, ["alice"], ["alice"])
    (raw_dir / "README.md").write_text("x", encoding="utf-8")
    (raw_dir / "sous-repertoire").mkdir()

    assert auditer(raw_dir, pivot_dir)["nb_bruts"] == 1


def test_le_point_de_sauvegarde_n_est_pas_un_profil(tmp_path):
    """Run `32773067295` (24/08/2026) : 22 jobs verts, commit annulé sur
    `Slug(s) : .generation_checkpoint`.

    `generate_all_profiles.py` écrit sa progression dans
    `raw_data/profiles/.generation_checkpoint.json` — un fichier de service,
    DANS le répertoire des profils bruts. Ce contrôle inventorie ce répertoire
    par nom de fichier : il l'a compté comme un brut, cherché son pivot, et
    annulé le commit de ~477 profils parfaitement collectés et publiés.

    Le filtre porte sur le point initial, pas sur ce nom précis : `slugify` ne
    produit que `[a-z0-9-]` puis `.strip("-")`, donc aucun slug ne peut
    commencer par un point. C'est une propriété du générateur de noms, pas une
    liste d'exceptions à tenir à jour.
    """
    raw_dir, pivot_dir = _corpus(tmp_path, ["alice", "bob"], ["alice", "bob"])
    (raw_dir / ".generation_checkpoint.json").write_text(
        '{"resultats": []}', encoding="utf-8")

    rapport = auditer(raw_dir, pivot_dir)

    assert rapport["nb_bruts"] == 2
    assert rapport["non_publies"] == []
    assert rapport["bloquant"] is False


def test_un_fichier_cache_du_repertoire_pivot_n_est_pas_un_pivot(tmp_path):
    """Symétrique du précédent : un fichier de service côté pivots deviendrait
    un « publié sans brut », c.-à-d. un compteur de dérive qui dérive tout
    seul."""
    raw_dir, pivot_dir = _corpus(tmp_path, ["alice"], ["alice"])
    (pivot_dir / ".etat.pivot.json").write_text("{}", encoding="utf-8")

    rapport = auditer(raw_dir, pivot_dir)

    assert rapport["nb_pivots"] == 1
    assert rapport["nb_publies_sans_brut"] == 0


# ---------------------------------------------------------------------------
# Le seuil, et la tolérance
# ---------------------------------------------------------------------------

def test_un_seuil_releve_laisse_passer(tmp_path):
    raw_dir, pivot_dir = _corpus(tmp_path, ["alice", "bob"], ["alice"])

    assert auditer(raw_dir, pivot_dir, seuil=1)["bloquant"] is False
    assert auditer(raw_dir, pivot_dir, seuil=0)["bloquant"] is True


def test_main_rend_1_sur_ecart_et_0_avec_la_tolerance(tmp_path, capsys):
    raw_dir, pivot_dir = _corpus(tmp_path, ["alice", "bob"], ["alice"])
    args = ["--raw-dir", str(raw_dir), "--pivot-dir", str(pivot_dir)]

    assert audit_main(args) == 1
    assert "bob" in capsys.readouterr().err

    assert audit_main(args + ["--tolerer-non-publies"]) == 0


def test_main_ecrit_les_deux_rapports(tmp_path):
    raw_dir, pivot_dir = _corpus(tmp_path, ["alice"], ["alice"])
    md = tmp_path / "rapport.md"
    js = tmp_path / "rapport.json"

    rc = audit_main(["--raw-dir", str(raw_dir), "--pivot-dir", str(pivot_dir),
                     "--out", str(md), "--out-json", str(js)])

    assert rc == 0
    assert "Collecté mais non publié" in md.read_text(encoding="utf-8")
    assert json.loads(js.read_text(encoding="utf-8"))["nb_bruts"] == 1


def test_les_trois_tolerances_restent_cloisonnees():
    """#470 a documenté le piège : un contrôle grossier rendu bloquant force
    l'opérateur à relancer avec la tolérance, ce qui désarme du même coup les
    contrôles précis. Les trois drapeaux doivent donc rester distincts."""
    from audit_collecte_non_publiee import _build_arg_parser

    options = {action.dest for action in _build_arg_parser()._actions}
    assert "tolerer_non_publies" in options
    assert "tolerer_pertes" not in options
    assert "tolerer_orphelins" not in options
