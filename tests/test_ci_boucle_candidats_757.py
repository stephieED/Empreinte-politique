"""La boucle du périmètre : liste → slug → correspondance → collecte (#757).

Ce que ces tests tiennent n'est pas la forme du YAML, c'est **l'ordre** et les
**conditions** dont dépend la boucle. Chacun correspond à une manière connue de
la casser sans qu'aucune étape n'échoue :

- rafraîchir la liste APRÈS que la matrice a été construite : le run collecterait
  le périmètre d'hier tout en committant celui d'aujourd'hui ;
- pousser la liste depuis le job de tête : `merge-and-pivot` annulerait le commit
  (`GENERATION_CODE_CHANGED_DURING_RUN`, #390/#413) ;
- écrire les correspondances APRÈS le portail : la §5b bloquerait sur des
  entrées que l'étape suivante allait écrire ;
- oublier `candidats.json` dans le `git add` : les slugs seraient refabriqués à
  chaque run, donc jamais gelés — la panne que #715 a corrigée pour la table.
"""

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"


def _bloc_job(nom: str) -> str:
    """Le texte d'un seul job. Même analyseur que `test_ci_roster_unique_par_run`.

    PyYAML n'est pas une dépendance du dépôt et ne le devient pas pour un test :
    le workflow se lit en texte, comme partout ailleurs dans la suite.
    """
    texte = WORKFLOW.read_text(encoding="utf-8")
    debut = re.search(rf"^  {re.escape(nom)}:\s*$", texte, flags=re.MULTILINE)
    assert debut, f"job `{nom}` absent de {WORKFLOW.name}"
    suite = re.search(r"^  [a-z][a-z0-9-]*:\s*$", texte[debut.end():], flags=re.MULTILINE)
    return texte[debut.end(): debut.end() + suite.start()] if suite else texte[debut.end():]


def _sans_commentaires(bloc: str) -> str:
    """Les rationales de ce dépôt citent les commandes qu'elles expliquent."""
    return "\n".join(l for l in bloc.split("\n") if not l.lstrip().startswith("#"))


def _steps(bloc: str) -> list[str]:
    code = _sans_commentaires(bloc)
    decoupe = re.split(r"^      - (?=name:|uses:|run:|id:)", code, flags=re.MULTILINE)
    return [s for s in decoupe[1:] if s.strip()]


def _indice(job: str, aiguille: str) -> int:
    steps = _steps(_bloc_job(job))
    for i, step in enumerate(steps):
        if aiguille in step:
            return i
    raise AssertionError(f"étape introuvable dans {job} : {aiguille!r}")


# ---------------------------------------------------------------------------
# Le job de tête
# ---------------------------------------------------------------------------


def test_le_job_de_rafraichissement_na_aucun_needs():
    """Il doit démarrer au premier étage : c'est lui qui dimensionne la matrice."""
    entete = _bloc_job("rafraichir-candidats").split("steps:")[0]
    assert "needs:" not in _sans_commentaires(entete)


def test_il_ne_porte_pas_continue_on_error():
    """`continue-on-error` rendrait vert un échec ; le repli est dans le shell."""
    entete = _bloc_job("rafraichir-candidats").split("steps:")[0]
    assert "continue-on-error" not in _sans_commentaires(entete)


def test_le_repli_garde_la_liste_committee_et_le_dit():
    """Une source injoignable ne doit jamais produire une liste vide (#511)."""
    bloc = _sans_commentaires(_bloc_job("rafraichir-candidats"))
    assert "CANDIDATS_SOURCE_INJOIGNABLE" in bloc
    assert '"$code" -eq 1' in bloc
    # Le fichier de résolutions est écrit VIDE, pas laissé absent : la passe
    # hors ligne doit distinguer « rien à ajouter » de « fichier manquant ».
    assert "resolutions-candidats-v1" in bloc


def test_lartifact_porte_la_liste_ET_les_resolutions():
    """Séparés, un run collecterait d'après l'une sans pouvoir écrire l'autre."""
    bloc = _sans_commentaires(_bloc_job("rafraichir-candidats"))
    assert bloc.count("upload-artifact") == 1
    assert "raw_data/candidats.json" in bloc
    assert "raw_data/resolutions_candidats.json" in bloc
    assert "if-no-files-found: error" in bloc


def test_la_resolution_reseau_na_lieu_que_dans_ce_job():
    """La passe qui écrit les correspondances est hors ligne (#524, #715)."""
    texte = _sans_commentaires(WORKFLOW.read_text(encoding="utf-8"))
    assert texte.count("--resoudre-identifiants") == 1
    assert "--resoudre-identifiants" in _sans_commentaires(_bloc_job("rafraichir-candidats"))


# ---------------------------------------------------------------------------
# La matrice lit la liste du jour
# ---------------------------------------------------------------------------


def test_la_matrice_attend_le_rafraichissement():
    entete = _sans_commentaires(_bloc_job("prepare-an-matrix").split("steps:")[0])
    assert "needs: rafraichir-candidats" in entete


def test_la_matrice_tourne_meme_si_le_rafraichissement_echoue():
    """Le périmètre d'hier vaut mieux qu'un run sans aucun candidat (#412 §2.1)."""
    entete = _sans_commentaires(_bloc_job("prepare-an-matrix").split("steps:")[0])
    assert "!cancelled()" in entete.replace(" ", "")


def test_la_matrice_telecharge_la_liste_avant_de_lire_les_slugs():
    assert _indice("prepare-an-matrix", "candidats-a-jour") < _indice(
        "prepare-an-matrix", "Slugs résolvables"
    ), "la matrice lirait la liste committée"


def test_un_artifact_absent_est_nomme_et_non_avale():
    bloc = _sans_commentaires(_bloc_job("prepare-an-matrix"))
    assert "CANDIDATS_ARTIFACT_ABSENT" in bloc


# ---------------------------------------------------------------------------
# Le commit, et l'ordre des passes
# ---------------------------------------------------------------------------


def test_la_passe_sourcee_precede_le_portail():
    """Sinon la §5b bloquerait sur des entrées que l'étape suivante allait écrire."""
    assert _indice("merge-and-pivot", "entrées sourcées") < _indice(
        "merge-and-pivot", "Quality gate"
    )


def test_la_passe_sourcee_suit_les_deux_passes_pivot():
    """Elle ne peut corroborer qu'un profil déjà publié (#715 §5, filtre 2)."""
    assert _indice("merge-and-pivot", "--pivot-only") < _indice(
        "merge-and-pivot", "entrées sourcées"
    )


def test_la_passe_sourcee_est_conditionnee_au_fichier_de_resolutions():
    """Pas de résolutions, pas de slug fabriqué, donc rien à écrire."""
    steps = _steps(_bloc_job("merge-and-pivot"))
    step = next(s for s in steps if "entrées sourcées" in s)
    assert "hashFiles" in step and "resolutions_candidats.json" in step


def test_la_liste_du_jour_entre_dans_le_commit():
    """Sans elle, les slugs seraient refabriqués à chaque run, donc jamais gelés."""
    texte = WORKFLOW.read_text(encoding="utf-8")
    ligne = next(l for l in texte.splitlines() if l.strip().startswith("git add raw_data/"))
    assert "raw_data/candidats.json" in ligne


def test_les_resolutions_ne_sont_pas_committees():
    """Intermédiaire de run, comme `rosters_bruts.json` : il bougerait à chaque fois."""
    texte = WORKFLOW.read_text(encoding="utf-8")
    ajouts = [l for l in texte.splitlines() if l.strip().startswith("git add ")]
    assert not any("resolutions_candidats" in l for l in ajouts)


def test_merge_and_pivot_normalise_la_liste_du_run():
    """Deux lectures de la même liste à deux moments divergent (#518)."""
    assert _indice("merge-and-pivot", "candidats-a-jour") < _indice(
        "merge-and-pivot", "--pivot-only"
    )


# ---------------------------------------------------------------------------
# Le périmètre : geler la collecte d'une candidature déclinée (#760)
# ---------------------------------------------------------------------------


def test_la_matrice_utilise_le_predicat_partage():
    """Une seule définition du périmètre, jamais deux.

    Le filtre `if c.get("slug")` vivait en dur dans le YAML ; recopié, il aurait
    divergé du jour où `generate_all_profiles` a appliqué le même gel.
    """
    bloc = _sans_commentaires(_bloc_job("prepare-an-matrix"))
    assert "from perimetre_candidats import" in bloc
    assert "slugs_a_collecter" in bloc
    assert 'if c.get("slug")' not in bloc, "le filtre en dur a été réintroduit"


def test_le_module_du_perimetre_est_dans_la_liste_blanche():
    """Un chemin lu mais absent du sparse-checkout ne fait pas échouer le
    checkout : il rend un fichier absent, et la collecte se replie en silence."""
    bloc = _bloc_job("prepare-an-matrix")
    assert "src/perimetre_candidats.py" in bloc


def test_le_gel_est_nomme_la_ou_le_perimetre_est_calcule():
    """Un trou muet se lit comme un constat (#510, #501)."""
    bloc = _sans_commentaires(_bloc_job("prepare-an-matrix"))
    assert "CANDIDAT_GELE" in bloc
    assert "slugs_geles" in bloc


def test_le_job_de_tete_verifie_que_les_resolutions_existent():
    """Échouer ICI nomme la cause ; échouer trois jobs plus loin la cache (#771).

    Le run `34160985529` a perdu 1 h 18 de collecte parce qu'un fichier absent
    s'est propagé en silence : artifact incomplet, `hashFiles()` vide, passe
    hors ligne sautée, portail qui refuse. Le job de tête refuse désormais de
    publier un artifact amputé.
    """
    bloc = _sans_commentaires(_bloc_job("rafraichir-candidats"))
    assert "CANDIDATS_RESOLUTIONS_ABSENTES" in bloc
    assert "! -f raw_data/resolutions_candidats.json" in bloc


def test_le_gel_nest_annote_quune_fois_par_run():
    """`prepare-an-matrix` annote ; `generate_all_profiles` se contente
    d'imprimer.

    Le run `34160985529` a produit 60 avertissements `CANDIDAT_GELE` — deux
    candidats × trente shards. Un avertissement répété trente fois est un
    avertissement qu'on filtre.
    """
    src = (RACINE / "src" / "generate_all_profiles.py").read_text(encoding="utf-8")
    bloc = re.search(r"geles = perimetre\.slugs_geles\(candidats\)(.*?)\n    if args\.only",
                     src, re.DOTALL)
    assert bloc, "le bloc de gel a changé de forme"
    assert "_annoter_github" not in bloc.group(1), (
        "le gel ne doit pas être annoté depuis un shard : la matrice le fait déjà"
    )


def test_le_shard_recoit_les_resolutions_du_run():
    """Sans elles, un candidat déclaré sans mandat AN par un identifiant externe
    ne reçoit aucun profil — et sans profil, pas d'entrée de table (#775).

    L'artifact porte aussi `candidats.json` du jour : le shard lisait jusqu'ici
    la liste COMMITTÉE, donc celle d'hier.
    """
    bloc = _sans_commentaires(_bloc_job("extract-an"))
    assert "candidats-a-jour" in bloc
    telechargement = _indice("extract-an", "candidats-a-jour")
    extraction = _indice("extract-an", "Extraction AN")
    assert telechargement < extraction, "le shard collecterait avant d'avoir les résolutions"


def test_le_telechargement_des_resolutions_ne_fait_pas_echouer_le_shard():
    """Son absence rend le comportement d'avant, à l'identique — pas une panne."""
    steps = _steps(_bloc_job("extract-an"))
    step = next(s for s in steps if "candidats-a-jour" in s)
    assert "continue-on-error: true" in step
