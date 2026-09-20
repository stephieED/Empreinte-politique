"""Une source lente n'annule plus le commit, et son échec se lit (#518).

## Ce que ces tests protègent

Run `32750929942` (24/08/2026) : 22 jobs verts, et `merge-and-pivot` tombé sur
`Générer les profils de groupe parlementaire réel`. Un fetch de roster en
timeout, les 5 groupes AN comptés en échec — ils partagent la clé
`('deputes','16')` —, `exit 1`, donc `Quality gate`, les trois garde-fous,
`Committer et pousser` et le déploiement **skippés**.

Or **aucune fiche de groupe n'avait été touchée** : les 7 fiches committées
étaient intactes sur le disque. Faire tomber tout le job a privé le run du
commit des ~452 profils de candidats et des profils de parti, qui eux étaient
corrects. C'est mot pour mot l'argument déjà écrit dans `generate-data.yml`
pour le step gouvernement (#427) : refuser qu'une donnée **non écrite** annule
la publication d'une donnée **écrite**.

Deux moitiés, et il faut les deux :

- le code de sortie **distingue** « roster indisponible » (2, rien d'écrit) de
  « une génération a planté » (1, un vrai défaut) — sans quoi le
  `continue-on-error` du step couvrirait aussi les vrais défauts ;
- l'échec **se lit** : le run n'exposait que `Process completed with exit
  code 1`, ce qui a obligé à rejouer le script localement pour savoir quelle clé
  de fetch était tombée. L'annotation nomme la clé ET les fiches non
  régénérées.

Aucune tolérance n'est ajoutée : la section 4 du quality gate continue de
hard-failer sur une fiche de groupe absente ou invalide.
"""

import json
import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import generate_group_profiles
from generate_group_profiles import (
    EXIT_ROSTER_INDISPONIBLE,
    ResultatGeneration,
    generate_all,
    main as group_profiles_main,
)

#: Ce fichier de tests lit la configuration committée nommée ci-dessous.
#: Le garde-fou de `conftest.py` refuse tout `.json` de `raw_data/` qu'un
#: test n'a pas déclaré (#791), et n'accepte la déclaration que si le chemin
#: est dans le `sparse-checkout` de `tests.yml` — sinon le test ne tournerait
#: qu'en local, sur ce qu'un run y a laissé.
pytestmark = pytest.mark.lit_reference_committee("raw_data/groupes_reels.json")


_GROUPE_AN = {
    "roster_chambre": "deputes", "groupe_id": "AN:LR", "groupe_sigle": "LR",
    "groupe_nom": "Les Républicains", "chambre": "AN", "legislature": "16",
    "fichier": "groupe-AN-LR-16.json",
}
_GROUPE_AN_SOC = {
    "roster_chambre": "deputes", "groupe_id": "AN:SOC", "groupe_sigle": "SOC",
    "groupe_nom": "Socialistes", "chambre": "AN", "legislature": "16",
    "fichier": "groupe-AN-SOC-16.json",
}
_GROUPE_SENAT = {
    "roster_chambre": "senateurs", "groupe_id": "Senat:LR", "groupe_sigle": "LR",
    "groupe_nom": "Les Républicains", "chambre": "Senat", "legislature": None,
    "fichier": "groupe-Senat-LR.json",
}
_MEMBRES = [{"slug": "alice", "nom": "Alice", "groupe_sigle": "LR",
             "mandat_debut": "2022-06-22", "mandat_fin": None}]


@pytest.fixture(autouse=True)
def index_partages_absents(monkeypatch, tmp_path_factory):
    """Voir test_generate_group_profiles.py (#473) : sans ça, ces tests liraient
    les ~66 Mo d'index du corpus vivant pour rien."""
    from amendements_index import charger as charger_amendements_reel
    from scrutins_index import charger as charger_scrutins_reel

    absent = tmp_path_factory.mktemp("index-absents")
    monkeypatch.setattr(
        "generate_group_profiles.charger_scrutins",
        lambda _chemin: charger_scrutins_reel(absent / "scrutins.json"),
    )
    monkeypatch.setattr(
        "generate_group_profiles.charger_amendements",
        lambda _dossier, **kwargs: charger_amendements_reel(absent / "amendements", **kwargs),
    )


def _dirs(tmp_path):
    (tmp_path / "profiles").mkdir(exist_ok=True)
    (tmp_path / "groupes").mkdir(exist_ok=True)
    return tmp_path / "profiles", tmp_path / "groupes"


def _fetch_ko(monkeypatch, exc=None):
    monkeypatch.setattr(
        "generate_group_profiles.fetch_full_roster",
        lambda *a, **k: (_ for _ in ()).throw(exc or requests.Timeout("Read timed out")),
    )


def _fetch_ok(monkeypatch):
    monkeypatch.setattr(
        "generate_group_profiles.fetch_full_roster",
        lambda *a, **k: list(_MEMBRES),
    )


def _annotations(capsys, niveau="error"):
    return [l for l in capsys.readouterr().out.splitlines() if l.startswith(f"::{niveau}::")]


# ---------------------------------------------------------------------------
# Le code de sortie distingue les deux échecs
# ---------------------------------------------------------------------------

def test_roster_indisponible_sort_en_2(tmp_path, monkeypatch):
    """LE test de ce fichier. 1 ferait skipper le commit d'un run dont les
    profils de candidats sont corrects, pour une fiche qu'on n'a pas touchée."""
    _fetch_ko(monkeypatch)
    profiles_dir, out_dir = _dirs(tmp_path)

    resultat = generate_all([_GROUPE_AN, _GROUPE_AN_SOC], profiles_dir=profiles_dir, out_dir=out_dir)

    assert resultat.code_sortie() == EXIT_ROSTER_INDISPONIBLE
    assert resultat.echecs == 2  # les deux groupes partagent la clé tombée
    assert resultat.echecs_generation == []
    assert list(out_dir.iterdir()) == []


def test_une_generation_qui_plante_sort_en_1(tmp_path, monkeypatch):
    """Un vrai défaut de code doit rester un `exit 1` : `continue-on-error` sur
    le step le laisse passer, mais l'annotation et le step rouge le nomment, et
    la section 4 du quality gate hard-faile sur la fiche manquante."""
    _fetch_ok(monkeypatch)
    monkeypatch.setattr(
        "generate_group_profiles.generate_groupe_profile_from_roster",
        lambda **kwargs: (_ for _ in ()).throw(KeyError("champ absent")),
    )
    profiles_dir, out_dir = _dirs(tmp_path)

    resultat = generate_all([_GROUPE_AN], profiles_dir=profiles_dir, out_dir=out_dir)

    assert resultat.code_sortie() == 1
    assert resultat.echecs_generation == ["AN:LR"]


def test_un_melange_des_deux_sort_en_1(tmp_path, monkeypatch):
    """Le vrai défaut l'emporte : rendre 2 ferait passer un plantage de code
    pour un aléa de source, et le `continue-on-error` le couvrirait en silence."""
    resultat = ResultatGeneration(
        echecs_generation=["AN:LR"],
        cles_indisponibles=[("senateurs", None)],
        groupes_sautes={("senateurs", None): ["Senat:LR"]},
    )
    assert resultat.code_sortie() == 1
    assert resultat.echecs == 2


def test_tout_va_bien_sort_en_0(tmp_path, monkeypatch):
    _fetch_ok(monkeypatch)
    profiles_dir, out_dir = _dirs(tmp_path)
    resultat = generate_all([_GROUPE_AN], profiles_dir=profiles_dir, out_dir=out_dir)
    assert resultat.code_sortie() == 0


def test_le_code_2_a_la_meme_valeur_que_celui_du_gouvernement():
    """Les deux steps posent le même `continue-on-error` pour la même raison
    (#427) : deux valeurs différentes inviteraient à les traiter différemment."""
    from generate_gouvernement_profiles import EXIT_COLLECTE_INCOMPLETE

    assert EXIT_ROSTER_INDISPONIBLE == EXIT_COLLECTE_INCOMPLETE == 2


def test_main_propage_le_code_2(tmp_path, monkeypatch):
    """Le code peut être juste dans `generate_all` et perdu dans `main`."""
    _fetch_ko(monkeypatch)
    profiles_dir, out_dir = _dirs(tmp_path)
    config = tmp_path / "groupes.json"
    config.write_text(json.dumps({"groupes": [_GROUPE_AN]}), encoding="utf-8")

    rc = group_profiles_main([
        "--config", str(config),
        "--profiles-dir", str(profiles_dir),
        "--out-dir", str(out_dir),
    ])

    assert rc == EXIT_ROSTER_INDISPONIBLE


def test_la_fiche_deja_publiee_reste_intacte(tmp_path, monkeypatch):
    """Le fondement du code 2 : rien n'est écrit, donc rien n'est perdu. Si la
    fiche committée bougeait, `continue-on-error` publierait une régression."""
    _fetch_ko(monkeypatch)
    profiles_dir, out_dir = _dirs(tmp_path)
    fiche = out_dir / "groupe-AN-LR-16.json"
    fiche.write_text('{"deja": "publiee"}', encoding="utf-8")

    generate_all([_GROUPE_AN], profiles_dir=profiles_dir, out_dir=out_dir)

    assert json.loads(fiche.read_text(encoding="utf-8")) == {"deja": "publiee"}


# ---------------------------------------------------------------------------
# L'échec se lit sans télécharger le log
# ---------------------------------------------------------------------------

def test_l_annotation_nomme_la_cle_de_roster_tombee(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    _fetch_ko(monkeypatch, requests.Timeout("Read timed out"))
    profiles_dir, out_dir = _dirs(tmp_path)

    generate_all([_GROUPE_AN], profiles_dir=profiles_dir, out_dir=out_dir)

    erreurs = _annotations(capsys)
    assert any("ROSTER_INDISPONIBLE" in e for e in erreurs), erreurs
    assert any("deputes" in e and "16" in e for e in erreurs), erreurs
    assert any("Read timed out" in e for e in erreurs), erreurs


def test_l_annotation_nomme_les_fiches_non_regenerees(tmp_path, monkeypatch, capsys):
    """Sans les `groupe_id`, l'annotation dit qu'un run a échoué, pas ce qu'il a
    renoncé à publier — exactement ce qui a obligé à rejouer le script
    localement pour diagnostiquer le run 32750929942."""
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    _fetch_ko(monkeypatch)
    profiles_dir, out_dir = _dirs(tmp_path)

    generate_all([_GROUPE_AN, _GROUPE_AN_SOC], profiles_dir=profiles_dir, out_dir=out_dir)

    erreurs = _annotations(capsys)
    recap = [e for e in erreurs if "non régénérée" in e]
    assert len(recap) == 1, erreurs
    assert "AN:LR" in recap[0] and "AN:SOC" in recap[0]
    assert "2 fiche(s)" in recap[0]


def test_une_cle_tombee_ne_produit_qu_une_annotation_de_cause(tmp_path, monkeypatch, capsys):
    """Cinq groupes AN partagent une clé : répéter la cause par groupe la
    noierait sous ses conséquences (même arbitrage que `anomalies_roster`)."""
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    _fetch_ko(monkeypatch)
    profiles_dir, out_dir = _dirs(tmp_path)

    generate_all([_GROUPE_AN, _GROUPE_AN_SOC], profiles_dir=profiles_dir, out_dir=out_dir)

    erreurs = _annotations(capsys)
    assert len([e for e in erreurs if "en échec après reprises" in e]) == 1, erreurs


def test_un_groupe_qui_plante_est_annote_nommement(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    _fetch_ok(monkeypatch)
    monkeypatch.setattr(
        "generate_group_profiles.generate_groupe_profile_from_roster",
        lambda **kwargs: (_ for _ in ()).throw(KeyError("champ absent")),
    )
    profiles_dir, out_dir = _dirs(tmp_path)

    generate_all([_GROUPE_AN], profiles_dir=profiles_dir, out_dir=out_dir)

    erreurs = _annotations(capsys)
    assert any("GROUPE_EN_ECHEC" in e and "AN:LR" in e for e in erreurs), erreurs


def test_aucune_annotation_hors_ci(tmp_path, monkeypatch, capsys):
    """Un script lancé à la main n'a aucune raison d'imprimer des commandes de
    workflow (même contrat que gha.annoter)."""
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    _fetch_ko(monkeypatch)
    profiles_dir, out_dir = _dirs(tmp_path)

    generate_all([_GROUPE_AN], profiles_dir=profiles_dir, out_dir=out_dir)

    assert _annotations(capsys) == []


def test_un_run_sans_echec_n_annote_rien(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    _fetch_ok(monkeypatch)
    profiles_dir, out_dir = _dirs(tmp_path)

    generate_all([_GROUPE_AN], profiles_dir=profiles_dir, out_dir=out_dir)

    assert _annotations(capsys) == []
    assert _annotations(capsys, "warning") == []


def test_un_groupe_suspendu_n_annote_rien(tmp_path, monkeypatch, capsys):
    """Une suspension est une décision écrite (#516), pas une panne : l'annoter
    en erreur ferait du bruit à chaque run et userait le canal."""
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    _fetch_ok(monkeypatch)
    profiles_dir, out_dir = _dirs(tmp_path)
    suspendu = dict(
        _GROUPE_SENAT,
        extraction_suspendue=True,
        depuis="2026-08-24",
        motif="Certificat TLS expiré",
        references=["#516"],
        condition_reprise="Certificat renouvelé",
    )

    resultat = generate_all([_GROUPE_AN, suspendu], profiles_dir=profiles_dir, out_dir=out_dir)

    assert _annotations(capsys) == []
    assert resultat.code_sortie() == 0


# ---------------------------------------------------------------------------
# Le step du workflow
# ---------------------------------------------------------------------------

RACINE = Path(__file__).resolve().parents[1]
WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"


def _step_groupes() -> str:
    texte = WORKFLOW.read_text(encoding="utf-8")
    debut = texte.index("      - name: Générer les profils de groupe parlementaire réel")
    fin = texte.index("      - name:", debut + 10)
    return "\n".join(
        l for l in texte[debut:fin].split("\n") if not l.lstrip().startswith("#")
    )


def test_le_step_groupes_tolere_le_code_2():
    """La moitié CI de ce fichier : sans ce filtrage, le code 2 ne change rien —
    le step reste rouge et `Committer et pousser` reste skippé."""
    step = _step_groupes()
    assert "|| CODE=$?" in step
    assert '"$CODE" -eq 2' in step
    assert "exit 0" in step


def test_le_step_groupes_ne_tolere_QUE_le_code_2():
    """LE test de cette section.

    Un `continue-on-error: true` avalerait aussi le code 1 — une génération de
    groupe qui plante réellement — et annulerait la distinction que le code 2
    vient d'introduire : on committerait une fiche périmée sans que rien ne
    bloque.
    """
    step = _step_groupes()
    assert "continue-on-error" not in step, (
        "`continue-on-error` sur ce step rend le code de sortie 2 inutile : "
        "tous les échecs deviennent tolérés (#518).")
    assert 'exit "$CODE"' in step, (
        "un code autre que 2 doit continuer de faire échouer le step.")


def test_le_step_groupes_consomme_le_roster_du_run():
    assert "--rosters-bruts raw_data/rosters_bruts.json" in _step_groupes()
