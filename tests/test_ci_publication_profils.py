"""Garde-fou #450 : un artifact d'extraction ne contient QUE ce que son job a écrit.

Contexte. Chaque job d'extraction commence par un `actions/checkout` :
`raw_data/profiles/` y contient les profils committés, dont la quasi-totalité
que ce job ne touchera jamais. Tant que l'upload prenait ce répertoire pour
`path:`, chaque artifact publiait la tranche fraîche du job **et** une copie
périmée de tous les autres profils. Deux dégâts distincts, mesurés sur le run
32277443716 (19/08/2026, sha 698a882) :

- `merge_raw_dirs` fusionnant additivement, une version fraîche et une version
  périmée du même profil donnaient leur UNION : `--no-merge` faisait son travail
  dans le job d'extraction et se faisait défaire à la fusion. Sur
  `antoine-armand`, 3 335 amendements = 1 289 périmés + 2 046 corrigés. Aucune
  correction de clé ne pouvait aboutir, et le volume enflait de 107 000 entrées
  par run — un amendement compté deux fois fausse les dénominateurs publiés
  (AGENTS.md §2.7).
- `merge-multiple` aplatit les 8 artifacts du roster dans un seul dossier : à
  nom de fichier égal, un seul survit. Les 8 shards publiant chacun les 752
  profils, ils entraient en collision partout, et seuls les 28 profils du
  shard 6 ont atteint le commit — le travail réseau des 7 autres shards a été
  écrasé sans le moindre signal.

La correction ne se règle pas par un arbitrage à la fusion : elle rétablit une
propriété structurelle, *un artifact = la contribution d'un job*. Des jobs qui
ne publient que leur propre tranche produisent des jeux de fichiers disjoints —
plus de baseline périmée à réinjecter, plus de nom en collision à départager.

Ces tests portent sur le workflow parce que c'est là que la propriété se perd :
elle ne laisse aucune trace dans le code Python, et sa disparition serait
silencieuse — le pipeline continuerait de produire des profils, simplement
faux et de plus en plus gros.

Volontairement sans PyYAML (absent de requirements.txt), comme
`test_ci_cache_paths.py`.
"""

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"
ACTION_PUBLICATION = RACINE / ".github" / "actions" / "publish-written-profiles" / "action.yml"

# Jobs d'extraction qui écrivent des profils bruts et les publient.
# `extract-senat` en faisait partie jusqu'à #528, qui l'a retiré avec le Sénat
# (docs/decisions/retrait-senat-528.md). Un job d'extraction ajouté
# ici doit publier via l'action dédiée, pas tout `raw_data/profiles/` (#450).
JOBS_EXTRACTION = (
    "extract-an",
    "extract-ue-officiel",
    "extract-roster-groupes",
)


def _blocs_par_job() -> dict[str, str]:
    """`{job: texte de sa définition}`. Découpe sur les en-têtes de job (2
    espaces d'indentation), seul niveau où le workflow est structurellement
    régulier."""
    texte = WORKFLOW.read_text(encoding="utf-8")
    blocs: dict[str, str] = {}
    job = None
    lignes: list[str] = []
    for ligne in texte.split("\n"):
        entete = re.match(r"^  ([a-z][a-z0-9-]*):\s*$", ligne)
        if entete:
            if job:
                blocs[job] = "\n".join(lignes)
            job = entete.group(1)
            lignes = []
        elif job:
            lignes.append(ligne)
    if job:
        blocs[job] = "\n".join(lignes)
    return blocs


def _lignes_de_code(bloc: str) -> str:
    """Bloc débarrassé de ses commentaires : les rationales de ce dépôt citent
    abondamment `raw_data/profiles/`, et un test qui les lirait comme du
    workflow serait un faux positif permanent."""
    return "\n".join(l for l in bloc.split("\n") if not l.lstrip().startswith("#"))


def test_les_jobs_attendus_existent_toujours():
    """Garde-fou du garde-fou : un job renommé ferait passer tous les tests
    ci-dessous en n'inspectant plus rien."""
    blocs = _blocs_par_job()
    manquants = [j for j in JOBS_EXTRACTION if j not in blocs]
    assert not manquants, f"Jobs absents de {WORKFLOW.name} : {manquants}"


def test_aucun_job_ne_publie_le_repertoire_des_profils():
    """Le cœur de #450. `path: raw_data/profiles/` republie la baseline
    committée du checkout, que ce job n'a pas produite."""
    for job, bloc in _blocs_par_job().items():
        code = _lignes_de_code(bloc)
        fautifs = re.findall(r"^\s*path:\s*(raw_data/profiles/?)\s*$", code, flags=re.MULTILINE)
        assert not fautifs, (
            f"Le job `{job}` publie {fautifs[0]} : l'artifact contiendrait la baseline "
            "committée récupérée par son checkout, en plus de sa propre tranche. "
            "Passer par ./.github/actions/publish-written-profiles (#450)."
        )


def test_chaque_job_d_extraction_consigne_ce_qu_il_ecrit():
    """Sans `--manifest-out`, l'étape de publication n'a rien à copier et
    l'artifact serait vide — panne muette, pas une erreur."""
    blocs = _blocs_par_job()
    for job in JOBS_EXTRACTION:
        code = _lignes_de_code(blocs[job])
        assert "generate_all_profiles.py" in code, (
            f"`{job}` n'appelle plus generate_all_profiles.py : revoir ce test."
        )
        assert "--manifest-out" in code, (
            f"Le job `{job}` écrit des profils sans `--manifest-out` : l'étape de "
            "publication ne saurait pas lesquels lui appartiennent (#450)."
        )


def test_chaque_job_d_extraction_publie_via_l_action_dediee():
    blocs = _blocs_par_job()
    for job in JOBS_EXTRACTION:
        code = _lignes_de_code(blocs[job])
        assert "./.github/actions/publish-written-profiles" in code, (
            f"Le job `{job}` n'appelle pas l'action de publication scopée (#450)."
        )
        assert "path: _publish/profiles/" in code, (
            f"Le job `{job}` n'uploade pas le staging rempli par cette action (#450)."
        )


def test_l_etape_de_publication_precede_l_upload():
    """Ordre inversé, le staging serait vide au moment de l'upload — et
    l'artifact partirait sans erreur."""
    blocs = _blocs_par_job()
    for job in JOBS_EXTRACTION:
        code = _lignes_de_code(blocs[job])
        rang_publication = code.find("publish-written-profiles")
        rang_upload = code.find("actions/upload-artifact")
        assert rang_publication >= 0, f"`{job}` n'a plus d'étape de publication (#450)."
        assert rang_upload >= 0, f"`{job}` n'uploade plus rien : revoir ce test."
        assert rang_publication < rang_upload, (
            f"Dans `{job}`, l'upload précède l'étape de publication : le staging "
            "serait encore vide (#450)."
        )


def test_la_publication_survit_a_une_preemption():
    """L'upload porte déjà `if: always()` (#228, préemptions fréquentes). Si
    l'étape de publication ne le portait pas, un job préempté publierait un
    artifact vide au lieu du préfixe qu'il avait écrit."""
    blocs = _blocs_par_job()
    for job in JOBS_EXTRACTION:
        steps = [b for b in _lignes_de_code(blocs[job]).split("      - name:")
                 if "publish-written-profiles" in b]
        assert steps, f"`{job}` n'a plus d'étape de publication (#450)."
        for bloc_step in steps:
            assert "if: always()" in bloc_step, (
                f"L'étape de publication de `{job}` n'a pas `if: always()` : un job "
                "préempté perdrait les profils déjà écrits (#450, #443)."
            )


def test_l_action_de_publication_ne_retombe_jamais_sur_le_repertoire_source():
    """Un repli « manifeste absent → publier raw_data/profiles/ » restaurerait
    exactement le bug : c'est le cas où le job n'a rien écrit, donc celui où il
    ne doit rien publier."""
    action = ACTION_PUBLICATION.read_text(encoding="utf-8")
    code = "\n".join(l for l in action.split("\n") if not l.lstrip().startswith("#"))
    assert 'exit 0' in code and 'Manifeste absent' in code, (
        "L'action doit sortir sans rien copier quand le manifeste est absent (#450)."
    )
    # Le seul usage de SOURCE_DIR autorisé est la lecture d'un nom listé au
    # manifeste, jamais une copie en masse.
    assert not re.search(r'cp\s+-[ra]|\$SOURCE_DIR"?/\*', code), (
        "L'action copie le répertoire source en masse : elle republierait la "
        "baseline périmée (#450)."
    )


def test_les_index_partages_sont_committes():
    """Un index qui n'est pas committé laisse les mappings pointer dans le vide.

    Depuis #432 (votes) et #431 (amendements), un profil pivot ne se lit plus
    seul : `pivot_data/scrutins.json` et `pivot_data/amendements/` portent le
    méta que les mappings référencent. Les oublier du `git add` ne casse rien de
    visible — le pipeline continue, les profils sont committés, et les vues se
    vident simplement sans erreur.
    """
    texte = WORKFLOW.read_text(encoding="utf-8")
    ligne = next(
        (l for l in texte.split("\n") if l.strip().startswith("git add ")), None
    )
    assert ligne is not None, "Aucun `git add` trouvé dans le workflow."
    for chemin in ("pivot_data/scrutins.json", "pivot_data/amendements"):
        assert chemin in ligne, (
            f"`{chemin}` absent du `git add` : l'index ne serait jamais committé "
            "et les mappings des profils pointeraient dans le vide."
        )
