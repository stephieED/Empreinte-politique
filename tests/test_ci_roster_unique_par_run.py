"""Un seul roster par run, transité par artifact (#518).

## Ce qui est verrouillé, et pourquoi

Jusqu'à #518, `raw_data/roster_candidats.json` était reconstruit par chacune
des **9 invocations** d'un run : 8 shards `extract-roster-groupes` + le job
`merge-and-pivot`. Deux défauts distincts, et c'est le second qui rend ces
tests nécessaires :

- **fragilité** — 9 requêtes qui doivent toutes passer. Le run `32738726729`
  (24/08/2026) a perdu 4 shards sur 8 exactement là, pendant que les 4 autres
  obtenaient la même liste sans incident ;
- **correction** — rien ne garantissait que les 9 listes soient la même. Les
  shards se partagent le roster par position (`--shard i/N`) et
  `merge-and-pivot` normalise en pivot ce que **sa** liste contient. Deux
  listes qui divergent, et un membre collecté par un shard n'est présenté à
  aucune passe pivot : c'est le « collecté mais non publié » de #511, produit
  sans qu'aucune étape n'ait échoué.

Le repli par régénération est verrouillé lui aussi, et sa **condition** avec :
un repli inconditionnel rétablirait les 9 fetchs sans que rien ne le signale.

Volontairement sans PyYAML (absent de requirements.txt), comme les autres
gardes-fous de workflow de ce dépôt.
"""

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"
SCRIPT = "python3 src/generate_roster_candidats.py"
ARTIFACT = "roster-candidats"


def _bloc_job(nom: str) -> str:
    texte = WORKFLOW.read_text(encoding="utf-8")
    debut = re.search(rf"^  {re.escape(nom)}:\s*$", texte, flags=re.MULTILINE)
    assert debut, f"job `{nom}` absent de {WORKFLOW.name}"
    suite = re.search(r"^  [a-z][a-z0-9-]*:\s*$", texte[debut.end():], flags=re.MULTILINE)
    return texte[debut.end(): debut.end() + suite.start()] if suite else texte[debut.end():]


def _sans_commentaires(bloc: str) -> str:
    """Les rationales de ce dépôt citent abondamment les commandes qu'elles
    expliquent : les lire comme du workflow serait un faux positif permanent."""
    return "\n".join(l for l in bloc.split("\n") if not l.lstrip().startswith("#"))


def _steps(bloc: str) -> list[str]:
    """Découpe un job en steps, commentaires retirés."""
    code = _sans_commentaires(bloc)
    decoupe = re.split(r"^      - (?=name:|uses:|run:)", code, flags=re.MULTILINE)
    return [s for s in decoupe[1:] if s.strip()]


def _step_contenant(bloc: str, aiguille: str) -> str:
    trouves = [s for s in _steps(bloc) if aiguille in s]
    assert len(trouves) == 1, (
        f"{len(trouves)} step(s) contiennent {aiguille!r}, 1 attendu.")
    return trouves[0]


# ---------------------------------------------------------------------------
# Le producteur
# ---------------------------------------------------------------------------

def test_prepare_roster_matrix_construit_le_roster_et_le_publie():
    bloc = _sans_commentaires(_bloc_job("prepare-roster-matrix"))
    assert SCRIPT in bloc, (
        "Le roster du run n'est plus construit dans `prepare-roster-matrix` : "
        "chaque shard le reconstruirait pour lui-même (#518).")
    assert f"name: {ARTIFACT}" in bloc, "artifact `roster-candidats` non publié"
    assert "raw_data/roster_candidats.json" in bloc


def test_le_producteur_publie_aussi_le_roster_brut():
    """#519 avait ramené 9 fetchs à 2 ; il en restait un, celui de
    `generate_group_profiles.py`, et c'est lui qui a tué le run 32750929942.

    Le roster BRUT (avant filtrage par sigle) part dans le même artifact : la
    fiche de groupe cesse d'être bâtie sur une composition lue ~7 min après
    celle qui a servi à collecter les profils.
    """
    bloc = _sans_commentaires(_bloc_job("prepare-roster-matrix"))
    assert "--rosters-bruts-out raw_data/rosters_bruts.json" in bloc
    step = _step_contenant(_bloc_job("prepare-roster-matrix"), f"name: {ARTIFACT}")
    assert "raw_data/rosters_bruts.json" in step, (
        "le roster brut est produit mais pas publié : `merge-and-pivot` "
        "refetcherait (#518).")


def test_le_repli_de_merge_and_pivot_produit_les_deux_fichiers():
    """Un repli qui n'écrirait que le roster de candidats laisserait le step
    groupes sans roster brut — donc en refetch, dans le job même où l'artifact
    a manqué, c'est-à-dire au pire moment."""
    step = _step_contenant(_bloc_job("merge-and-pivot"), SCRIPT)
    assert "--rosters-bruts-out raw_data/rosters_bruts.json" in step


def test_le_roster_brut_n_est_pas_committe():
    """Il est régénéré à chaque run et pèse ~814 Ko par clé : committé, il
    salirait l'arbre au `git rebase --autostash` du push et dériverait
    silencieusement (même piège que #413 §5)."""
    gitignore = (RACINE / ".gitignore").read_text(encoding="utf-8")
    assert "raw_data/rosters_bruts.json" in gitignore


def test_l_artifact_du_producteur_ne_peut_pas_etre_vide():
    """`if-no-files-found: ignore` publierait un artifact vide, que les
    consommateurs téléchargeraient avec succès — un roster absent deviendrait
    un roster de 0 candidat, c'est-à-dire l'incident de #511."""
    step = _step_contenant(_bloc_job("prepare-roster-matrix"), f"name: {ARTIFACT}")
    assert "if-no-files-found: error" in step


def test_le_producteur_installe_ses_dependances():
    """Le job ne faisait ni checkout ni pip install avant #518."""
    bloc = _sans_commentaires(_bloc_job("prepare-roster-matrix"))
    assert "actions/checkout" in bloc
    assert "pip install -r requirements.txt" in bloc


# ---------------------------------------------------------------------------
# Les consommateurs
# ---------------------------------------------------------------------------

def test_les_consommateurs_telechargent_le_roster_du_run():
    for job in ("extract-roster-groupes", "merge-and-pivot"):
        bloc = _sans_commentaires(_bloc_job(job))
        assert f"name: {ARTIFACT}" in bloc, (
            f"`{job}` ne télécharge plus le roster du run : il en reconstruirait "
            "un autre, et les deux peuvent différer (#518).")
        assert "actions/download-artifact" in bloc


def test_la_regeneration_reste_un_repli_conditionnel():
    """LE test de ce fichier.

    Sans la condition, on retombe sur 9 fetchs par run — et sans le repli, un
    `prepare-roster-matrix` en échec emporterait tout le run, à rebours de
    #412 §2.1.
    """
    for job in ("extract-roster-groupes", "merge-and-pivot"):
        step = _step_contenant(_bloc_job(job), SCRIPT)
        assert "if:" in step, (
            f"`{job}` reconstruit le roster inconditionnellement : l'artifact du "
            "run ne sert alors à rien (#518).")
        assert "roster_artifact.outcome == 'failure'" in step, (
            f"le repli de `{job}` n'est plus conditionné à l'ABSENCE de "
            "l'artifact.")


def test_le_telechargement_du_roster_ne_fait_pas_echouer_le_job():
    """Un artifact manquant est un mode dégradé documenté, pas une panne : le
    repli existe pour ça."""
    for job in ("extract-roster-groupes", "merge-and-pivot"):
        step = _step_contenant(_bloc_job(job), f"name: {ARTIFACT}")
        assert "continue-on-error: true" in step
        assert "id: roster_artifact" in step


def test_le_roster_est_disponible_avant_la_passe_pivot_roster():
    """Ordre des steps dans `merge-and-pivot` : télécharger (ou régénérer)
    APRÈS la passe pivot ne servirait à rien — elle aurait déjà itéré."""
    code = _sans_commentaires(_bloc_job("merge-and-pivot"))
    rang_telechargement = code.find(f"name: {ARTIFACT}")
    rang_repli = code.find(SCRIPT)
    rang_passe = code.find("--candidats raw_data/roster_candidats.json")
    assert 0 <= rang_telechargement < rang_passe
    assert 0 <= rang_repli < rang_passe


def test_les_shards_extraient_toujours_depuis_le_roster_du_run():
    """Le fichier consommé ne change pas de nom : c'est la seule chose que
    `--shard i/N` partitionne."""
    code = _sans_commentaires(_bloc_job("extract-roster-groupes"))
    assert "--candidats raw_data/roster_candidats.json" in code
