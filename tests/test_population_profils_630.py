"""Les deux populations de `pivot_data/profiles/` sont portées par les outils (#630).

Ce que ce fichier verrouille, et ce qu'il ne verrouille pas.

**Verrouillé** : le rendu de `src/population_profils.py`, et le fait que chaque
compte de profils affiché par les quatre outils de mesure porte sa ventilation.
Les fonctions de rapport sont appelées pour de vrai, sur des fixtures écrites
dans `tmp_path` — jamais sur `pivot_data/`, qu'aucun test ne lit (#473).

**Non verrouillé, et c'est écrit plutôt que présumé** : un compte de profils
*ajouté* demain sans passer par `Ventilation`. Le détecter demanderait de
reconnaître « un compte de profils » dans une f-string quelconque ; un tel
garde-fou crierait sur les compteurs qui n'en sont pas (`Entrées : 481`,
`len(rows_mixtes)`) et finirait désactivé. Le raisonnement est dans
`docs/decisions/populations-profils-portees-par-les-outils-630.md`.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from audit_collecte_vs_publie import auditer, generate_markdown_report as md_collecte  # noqa: E402
from audit_pivot_dataset import (  # noqa: E402
    build_report,
    generate_markdown_report as md_pivot,
)
from audit_volumetrie_profils import (  # noqa: E402
    analyser_repertoires,
    compute_volumetrie,
    generate_markdown_report as md_volumetrie,
)
from correspondance_acteurs_an import SCHEMA_VERSION as SCHEMA_VERSION_CORRESPONDANCE  # noqa: E402
from check_quality_gate import (  # noqa: E402
    _report_amendements_coverage,
    _report_correspondance_acteurs,
    _report_coverage,
    _report_low_interventions,
)
from population_profils import (  # noqa: E402
    CANDIDAT_DECLARE,
    ROSTER_GROUPE,
    Ventilation,
    lire_provenances,
    provenance_du_profil,
    ventiler,
    ventiler_chemins,
    ventiler_repertoire,
)

#: La ventilation telle qu'elle doit apparaître pour 1 candidat déclaré et
#: 2 membres de roster. Écrite une fois : si la forme change, elle change ici,
#: et tous les rendus la suivent — c'est tout l'intérêt du module partagé.
DETAIL_1_2 = "(1 candidats · 2 membres de roster)"


# ---------------------------------------------------------------------------
# Fixtures — un corpus minuscule, mais des deux populations
# ---------------------------------------------------------------------------

def _pivot(slug: str, provenance: str | None, **champs) -> dict:
    profil = {
        "id": slug,
        "nom": slug.replace("-", " ").title(),
        "chambre": "AN",
        "chambres": ["AN"],
        "identite": {"nom_complet": slug.replace("-", " ").title()},
        "mandats": [],
        "votes": [],
        "textes_portes": [],
        "amendements": [],
        "interventions": [],
        "tags_thematiques": [],
        "sources": [],
        "meta": {"warnings": []},
    }
    profil.update(champs)
    if provenance is not None:
        profil["meta"]["provenance"] = provenance
    return profil


def _ecrire_corpus(repertoire: Path) -> list[dict]:
    """1 candidat déclaré, 2 membres de roster — la proportion réelle en petit."""
    repertoire.mkdir(parents=True, exist_ok=True)
    profils = [
        _pivot("candidate-declaree", CANDIDAT_DECLARE),
        _pivot("membre-roster-1", ROSTER_GROUPE),
        _pivot("membre-roster-2", ROSTER_GROUPE),
    ]
    for profil in profils:
        (repertoire / f"{profil['id']}.pivot.json").write_text(
            json.dumps(profil), encoding="utf-8"
        )
    return profils


# ---------------------------------------------------------------------------
# Le module partagé
# ---------------------------------------------------------------------------

def test_la_forme_affichee_est_celle_que_l_issue_demande():
    ventilation = Ventilation(candidats_declares=13, membres_roster=468)
    assert ventilation.total == 481
    assert ventilation.ligne("Profils publiés") == (
        "Profils publiés : 481   (13 candidats · 468 membres de roster)"
    )
    assert ventilation.cellule_markdown() == (
        "481 (13 candidats · 468 membres de roster)"
    )


def test_le_total_est_la_somme_des_postes_illisibles_compris():
    """« 481 » et « 13 + 468 » ne peuvent pas diverger en silence : un fichier
    illisible reste dans le total, sous son propre poste (AGENTS.md §2 règle 5)."""
    ventilation = Ventilation(candidats_declares=13, membres_roster=467, illisibles=1)
    assert ventilation.total == 481
    assert "1 illisibles" in ventilation.detail()


def test_une_provenance_absente_vaut_candidat_declare():
    """Rétro-compatibilité de `docs/decisions/provenance-pivot.md`, la même que
    celle de `validate_profil()`."""
    assert provenance_du_profil({"meta": {}}) == CANDIDAT_DECLARE
    assert provenance_du_profil({}) == CANDIDAT_DECLARE
    assert provenance_du_profil(None) == CANDIDAT_DECLARE
    assert ventiler([{"meta": {}}]).candidats_declares == 1


def test_une_provenance_inconnue_a_son_propre_poste():
    """Elle n'est rangée d'office dans aucun des deux camps : une valeur qu'on ne
    sait pas lire n'est pas une valeur qu'on peut supposer."""
    ventilation = ventiler([_pivot("x", "source_inventee")])
    assert (ventilation.candidats_declares, ventilation.membres_roster) == (0, 0)
    assert ventilation.provenance_autre == 1
    assert "1 provenance inconnue" in ventilation.detail()


def test_un_fichier_cache_n_est_pas_un_profil(tmp_path):
    """`Path.glob` rend les dotfiles, contrairement au module `glob` :
    `.generation_checkpoint.json` a déjà été lu comme un profil (#518)."""
    _ecrire_corpus(tmp_path)
    (tmp_path / ".generation_checkpoint.pivot.json").write_text("{}", encoding="utf-8")

    assert ventiler_repertoire(tmp_path).total == 3


def test_un_pivot_illisible_est_compte_sans_etre_ventile(tmp_path):
    _ecrire_corpus(tmp_path)
    (tmp_path / "casse.pivot.json").write_text("{ pas du JSON", encoding="utf-8")

    ventilation = ventiler_repertoire(tmp_path)
    assert (ventilation.total, ventilation.illisibles) == (4, 1)


def test_un_profil_brut_n_est_jamais_compte_comme_candidat_declare(tmp_path):
    """`raw_data/profiles/<slug>.json` ne porte pas `meta.provenance` : lui
    appliquer le repli rétro-compatible inventerait autant de candidats déclarés
    qu'il y a de fichiers. La règle de #189 vaut pour un pivot d'avant #189."""
    brut = tmp_path / "quelqu-un.json"
    brut.write_text(json.dumps({"slug": "quelqu-un", "meta": {"warnings": []}}), encoding="utf-8")
    pivot = tmp_path / "quelqu-un.pivot.json"
    pivot.write_text(json.dumps(_pivot("quelqu-un", ROSTER_GROUPE)), encoding="utf-8")

    ventilation, hors_pivot = ventiler_chemins([brut, pivot])

    assert ventilation.candidats_declares == 0
    assert ventilation.membres_roster == 1
    assert hors_pivot == [brut]


def test_lire_provenances_rend_le_slug_sans_le_suffixe(tmp_path):
    _ecrire_corpus(tmp_path)
    provenances, illisibles = lire_provenances(tmp_path)

    assert provenances == {
        "candidate-declaree": CANDIDAT_DECLARE,
        "membre-roster-1": ROSTER_GROUPE,
        "membre-roster-2": ROSTER_GROUPE,
    }
    assert illisibles == []


# ---------------------------------------------------------------------------
# check_quality_gate — les quatre sections qui affichent un compte de profils
# ---------------------------------------------------------------------------

def _candidats_json(tmp_path: Path, slugs: list[str]) -> Path:
    chemin = tmp_path / "candidats.json"
    chemin.write_text(json.dumps({"candidats": [
        {"slug": slug, "nom": slug.title(), "parti": "—", "statut": "declare"}
        for slug in slugs
    ]}), encoding="utf-8")
    return chemin


def test_gate_section2_ventile_les_profils_generes(tmp_path):
    profils_dir = tmp_path / "profiles"
    _ecrire_corpus(profils_dir)
    candidats = _candidats_json(tmp_path, ["candidate-declaree"])

    console, md = _report_coverage(candidats, profils_dir)

    assert f"Profils générés : 3   {DETAIL_1_2}" in console
    assert f"| ✅ Profils générés | 3 {DETAIL_1_2} |" in md


def test_gate_section2_ne_crie_plus_sur_les_membres_de_roster(tmp_path):
    """Le défaut mesuré le 30/08/2026 : 468 membres de roster nommés un par un
    sous « Fichiers sans correspondance dans candidats.json », soit 468 lignes
    de fausse alerte sur les 1 054 du rapport. Un membre de roster hors
    `candidats.json` est la normale — c'est la raison pour laquelle il existe.
    """
    profils_dir = tmp_path / "profiles"
    _ecrire_corpus(profils_dir)
    candidats = _candidats_json(tmp_path, ["candidate-declaree"])

    console, md = _report_coverage(candidats, profils_dir)

    assert "membre-roster-1" not in console
    assert "membre-roster-2" not in console
    assert "Inattendus" not in console
    assert "2 profil(s) hors candidats.json (2 membres de roster)" in console


def test_gate_section2_signale_encore_un_candidat_declare_hors_liste(tmp_path):
    """Le contre-témoin : ce qui reste « inattendu » est un profil qui se DIT
    candidat déclaré sans figurer dans la liste éditoriale. Sans lui, le test
    précédent pourrait passer parce que la section ne signale plus rien."""
    profils_dir = tmp_path / "profiles"
    _ecrire_corpus(profils_dir)
    candidats = _candidats_json(tmp_path, [])

    console, md = _report_coverage(candidats, profils_dir)

    assert "Inattendus : 1" in console
    assert "candidate-declaree" in console
    assert "membre-roster-1" not in console


def test_gate_section3_ventile_les_profils_analyses(tmp_path):
    profils_dir = tmp_path / "profiles"
    _ecrire_corpus(profils_dir)
    candidats = _candidats_json(tmp_path, ["candidate-declaree"])

    console, md, provenances = _report_low_interventions(profils_dir, candidats, 10)

    assert f"Profils analysés : 3   {DETAIL_1_2}" in console
    assert f"| ⚠️ Profils analysés | 3 {DETAIL_1_2} |" in md
    # La §3 est la seule section qui charge le corpus : c'est elle qui rend la
    # provenance aux §2 et §5b, qui ne lisent que des noms de fichiers.
    assert provenances["membre-roster-1"] == ROSTER_GROUPE


def test_gate_section3c_ventile_les_profils_an_avec_identite(tmp_path):
    profils_dir = tmp_path / "profiles"
    _ecrire_corpus(profils_dir)

    soft, regression, console, md = _report_amendements_coverage(profils_dir)

    assert f"Profils AN avec identité : 3   {DETAIL_1_2}" in console
    assert f"| ⚠️ Profils AN avec identité | 3 {DETAIL_1_2} |" in md
    # Le signal global porte lui aussi sa population.
    assert regression is not None and f"aucun profil AN sur 3 {DETAIL_1_2}" in regression


def test_gate_section5b_ventile_les_profils_publies(tmp_path):
    """« Profils publiés : 481 » est le compte que tout le monde recopie."""
    profils_dir = tmp_path / "profiles"
    _ecrire_corpus(profils_dir)
    table = tmp_path / "correspondance.json"
    table.write_text(json.dumps({
        "schema_version": SCHEMA_VERSION_CORRESPONDANCE,
        "genere_le": "2026-08-30T00:00:00+0000",
        "source_referentiel": "https://data.assemblee-nationale.fr/",
        "correspondances": {
            slug: {
                "acteur_ref": f"PA{rang}",
                "etat_civil": {"nom_complet": slug.replace("-", " ").title()},
                "ecart": None,
                "motif": None,
                "preuve": f"https://www2.assemblee-nationale.fr/deputes/fiche/OMC_PA{rang}",
                "verifie_le": "2026-08-30",
            }
            for rang, slug in enumerate(
                ("candidate-declaree", "membre-roster-1", "membre-roster-2"), start=1
            )
        },
    }), encoding="utf-8")

    hard, console, md = _report_correspondance_acteurs(profils_dir, table)

    assert not hard
    assert f"Profils publiés : 3   {DETAIL_1_2}" in console
    assert f"| Profils publiés | 3 {DETAIL_1_2} |" in md


def test_gate_section5b_ventile_sans_qu_on_lui_passe_la_provenance(tmp_path):
    """Le partage depuis la §3 optimise, il ne conditionne pas : appelée seule,
    la section relit la provenance plutôt que de rendre un rapport amputé."""
    profils_dir = tmp_path / "profiles"
    _ecrire_corpus(profils_dir)
    candidats = _candidats_json(tmp_path, ["candidate-declaree"])

    console_partage, _ = _report_coverage(
        candidats, profils_dir, {"membre-roster-1": ROSTER_GROUPE,
                                 "membre-roster-2": ROSTER_GROUPE,
                                 "candidate-declaree": CANDIDAT_DECLARE},
    )
    console_seule, _ = _report_coverage(candidats, profils_dir)

    assert console_partage == console_seule
    assert DETAIL_1_2 in console_seule


# ---------------------------------------------------------------------------
# Les trois audits
# ---------------------------------------------------------------------------

def test_audit_pivot_dataset_affiche_la_ventilation_qu_il_calculait_deja(tmp_path):
    """25 occurrences de `provenance` et une table de répartition — mais deux
    sections plus bas que le total. Le total la porte désormais lui-même."""
    profils = _ecrire_corpus(tmp_path)

    rapport = build_report(profils, [])
    md = md_pivot(rapport)

    assert rapport["meta"]["ventilation_provenance"]["roster_groupe"] == 2
    assert f"3 {DETAIL_1_2} profil(s) analysé(s)" in md
    assert f"Total profils : 3 {DETAIL_1_2}" in md
    # La table de répartition d'origine reste : elle n'est pas remplacée, elle
    # cesse seulement d'être le seul endroit qui porte l'information.
    assert "### Répartition par provenance" in md


def test_audit_pivot_dataset_ventile_les_profils_sans_activite(tmp_path):
    """« 24 / 481 » ne dit pas si le trou est sur les 13 fiches publiées ou sur
    les 468 membres de roster, et les deux appellent des suites différentes."""
    profils = _ecrire_corpus(tmp_path)

    md = md_pivot(build_report(profils, []))

    assert f"3 {DETAIL_1_2} sur 3 {DETAIL_1_2} profil(s)." in md


def test_audit_collecte_vs_publie_ventile_la_population_rapprochee(tmp_path):
    raw_dir = tmp_path / "raw"
    pivot_dir = tmp_path / "pivot"
    profils = _ecrire_corpus(pivot_dir)
    raw_dir.mkdir()
    for profil in profils:
        (raw_dir / f"{profil['id']}.json").write_text(
            json.dumps({"slug": profil["id"], "meta": {"warnings": []}}), encoding="utf-8"
        )

    rapport = auditer(raw_dir, pivot_dir)
    md = md_collecte(rapport)

    assert rapport["nb_profils_compares"] == 3
    assert rapport["ventilation_provenance"]["roster_groupe"] == 2
    assert f"Population : **3 profil(s)** {DETAIL_1_2}" in md


def test_audit_volumetrie_ventile_les_pivots_et_nomme_les_bruts(tmp_path):
    """Deux répertoires, deux natures : le pivot se ventile, le brut se nomme."""
    pivot_dir = tmp_path / "pivot"
    raw_dir = tmp_path / "raw"
    _ecrire_corpus(pivot_dir)
    raw_dir.mkdir()
    (raw_dir / "quelqu-un.json").write_text(
        json.dumps({"slug": "quelqu-un", "meta": {"warnings": []}}), encoding="utf-8"
    )

    mesures, erreurs, exact = analyser_repertoires([pivot_dir, raw_dir], echantillon=0)
    md = md_volumetrie({
        "volumetrie": compute_volumetrie(mesures, exact),
        "leviers": [],
    })

    assert exact["nb_profils_sans_provenance"] == 1
    assert f"**4 profils** ({DETAIL_1_2[1:-1]} · 1 profils bruts, sans meta.provenance)" in md
