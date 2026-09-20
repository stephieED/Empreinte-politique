"""Garde-fou #550 : le cache AN se restaure sur la complétude ATTENDUE et se
sauvegarde sur la complétude ATTEINTE.

Le mécanisme, mesuré. Le 27/08/2026 au run `33100214165`, deux archives Syceron
(15e, 16e) et deux archives de questions (14e, 15e) sont tombées en
`IncompleteRead`. Les gardes de #505/#510 ont refusé de mettre ces index en
cache, et le shard a sauvegardé son entrée sous
`public-data-cache-an-2026-W35-interv` — 114 481 867 o ne contenant, côté
interventions, que la 17e législature de débats et les 16e/17e de questions.
Deux heures plus tard, le run `33110395663` a fait un *exact key hit* dessus :
« Cache hit occurred on the primary key public-data-cache-an-2026-W35-interv,
not saving cache » (20:02:40, job 98652271090). Chacun des 7 shards porteurs a
reconstruit les index des 15e et 16e — 113 à 219 s, 40 à 60 % de l'horloge de
collecte — pour les jeter à la fin de son job.

Trois propriétés doivent tenir ensemble, et aucune ne suffit seule :

1. **La clé porte la complétude.** Sans elle, une entrée partielle occupe la
   clé d'une entrée complète et rien ne peut plus la remplacer de la semaine —
   les entrées de cache GitHub sont immuables.
2. **La sauvegarde est explicite.** `actions/cache` combiné ne connaît qu'une
   clé, et saute sa sauvegarde sur *exact key hit* : il ne peut ni restaurer
   sur une clé (l'attendue) ni écrire sur une autre (l'atteinte).
3. **Les deux steps déclarent le MÊME `path`.** La *version* d'une entrée de
   cache est un hachage du `path` : deux listes différentes donnent deux
   entrées qui ne se voient pas, et la sauvegarde deviendrait invisible à la
   restauration — sans aucun message.

Volontairement sans PyYAML (absent de `requirements.txt`), comme
`test_ci_cache_paths.py` et `test_ci_cache_producteur_ecrivain.py` : le
workflow est lu comme du texte.
"""

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"
MODULE_EMPREINTE = RACINE / "src" / "cache_an_empreinte.py"


def _job_extract_an() -> str:
    texte = WORKFLOW.read_text(encoding="utf-8")
    bloc = re.search(r"^  extract-an:\n(.*?)(?=\n  [a-z][a-z0-9-]*:\n)", texte, flags=re.S | re.M)
    assert bloc, "Job `extract-an` introuvable dans generate-data.yml."
    return bloc.group(1)


def _steps() -> list[str]:
    """Les steps du job, dans l'ordre, texte brut."""
    morceaux = re.split(r"\n(?=      - (?:uses|name):)", "\n" + _job_extract_an())
    return [m for m in morceaux if m.strip().startswith("- ")]


def _step_contenant(motif: str) -> str:
    trouves = [s for s in _steps() if motif in s]
    assert len(trouves) == 1, f"{len(trouves)} step(s) contiennent « {motif} » (attendu : 1)."
    return trouves[0]


def _lignes_du_bloc(step: str, champ: str) -> tuple[str, list[str]]:
    """`(valeur sur la ligne du champ, lignes plus indentées qui la prolongent)`.

    Écrit à la main plutôt qu'en une expression régulière : `if: >-` et
    `path: |` sont des scalaires de bloc YAML, et une regex gourmande avale la
    suite du fichier — commentaires du step suivant compris. C'est
    l'indentation, et elle seule, qui borne le bloc.
    """
    lignes = step.split("\n")
    for i, ligne in enumerate(lignes):
        motif = re.match(rf"^(\s*){re.escape(champ)}:\s*(.*)$", ligne)
        if not motif:
            continue
        indentation = len(motif.group(1))
        suite = []
        for suivante in lignes[i + 1:]:
            if not suivante.strip():
                break
            if len(suivante) - len(suivante.lstrip()) <= indentation:
                break
            suite.append(suivante.strip())
        return motif.group(2).strip(), suite
    raise AssertionError(f"champ `{champ}:` absent du step :\n{step}")


def _valeur(step: str, champ: str) -> str:
    """La valeur d'un champ, scalaire de bloc replié en une ligne."""
    tete, suite = _lignes_du_bloc(step, champ)
    if tete in ("|", ">", ">-", "|-"):
        return " ".join(suite)
    return tete


def _bloc_path(step: str) -> list[str]:
    tete, suite = _lignes_du_bloc(step, "path")
    assert tete == "|", f"`path:` n'est pas un bloc littéral dans :\n{step}"
    return suite


# ---------------------------------------------------------------------------
# Garde-fou du garde-fou
# ---------------------------------------------------------------------------


def test_le_job_est_lisible():
    """Si le découpage ne trouve plus les steps, tous les tests ci-dessous
    passeraient pour une mauvaise raison (leçon de #460)."""
    steps = _steps()
    assert len(steps) >= 10, f"{len(steps)} step(s) trouvés dans extract-an"


# ---------------------------------------------------------------------------
# 1. La clé porte la complétude
# ---------------------------------------------------------------------------


def test_la_cle_de_restauration_porte_la_completude_attendue():
    """Le mode y était depuis #505 ; c'est la complétude qui manquait."""
    cle = _valeur(_step_contenant("actions/cache/restore@v5\n        id: cache_an"), "key")
    assert "inputs.collect_interventions" in cle, (
        "La clé AN ne porte plus le mode : un run en mode interventions "
        "referait un exact key hit sur une entrée sans interventions (#505)."
    )
    assert "steps.empreinte_attendue.outputs.empreinte" in cle, (
        "La clé de restauration ne porte plus la complétude attendue : une "
        "entrée partielle redeviendrait indiscernable d'une entrée complète "
        "(#550)."
    )


def test_la_cle_de_sauvegarde_porte_la_completude_atteinte():
    """Sauvegarder sous la clé ATTENDUE serait le défaut de #550 à l'identique :
    un shard qui n'a pu indexer que deux législatures sur trois écrirait une
    entrée que la clé déclare complète."""
    cle = _valeur(_step_contenant("actions/cache/save@v5"), "key")
    assert "steps.empreinte_obtenue.outputs.empreinte" in cle
    assert "steps.empreinte_attendue.outputs.empreinte" not in cle, (
        "La sauvegarde écrit la complétude ATTENDUE au lieu de l'ATTEINTE : "
        "c'est exactement l'entrée mensongère que #550 corrige."
    )
    assert "inputs.collect_interventions" in cle


def test_les_deux_empreintes_viennent_du_meme_module():
    """Deux calculs distincts dériveraient l'un de l'autre sans que rien ne le
    dise. Un seul module, deux drapeaux."""
    assert MODULE_EMPREINTE.is_file(), "src/cache_an_empreinte.py a disparu"
    job = _job_extract_an()
    assert "python3 src/cache_an_empreinte.py --attendue" in job
    assert "python3 src/cache_an_empreinte.py --disque" in job


def test_les_globes_du_workflow_sont_ceux_que_l_empreinte_sonde():
    """L'empreinte doit décrire EXACTEMENT ce que l'entrée contiendra. Si le
    `path:` capture un fichier que l'empreinte ne regarde pas — ou l'inverse —
    la clé recommence à mentir sur son contenu, autrement."""
    import cache_an_empreinte as emp

    chemins = _bloc_path(_step_contenant("actions/cache/save@v5"))
    assert emp.GLOBE_QUESTIONS in chemins, (
        f"le `path:` du cache AN ne contient plus {emp.GLOBE_QUESTIONS} ; "
        f"il déclare {chemins}."
    )
    assert emp.GLOBE_SYCERON in chemins, (
        f"le `path:` du cache AN ne contient plus {emp.GLOBE_SYCERON} ; "
        f"il déclare {chemins}."
    )


# ---------------------------------------------------------------------------
# 2. La sauvegarde est explicite, et conditionnée
# ---------------------------------------------------------------------------


def test_le_cache_an_est_en_restore_puis_save_explicites():
    """Un `actions/cache` combiné ne sait pas restaurer sur une clé et écrire
    sur une autre : il saute sa sauvegarde dès l'exact key hit."""
    job = _job_extract_an()
    assert "actions/cache/save@v5" in job, (
        "La sauvegarde explicite du cache AN a disparu : plus rien ne peut "
        "remplacer une entrée partielle de la semaine (#550)."
    )
    restore = _step_contenant("actions/cache/restore@v5\n        id: cache_an")
    assert "id: cache_an" in restore, "le step de restauration doit rester adressable"


def test_la_sauvegarde_ne_reecrit_pas_la_cle_qu_elle_vient_de_restaurer():
    """Une entrée de cache GitHub est immuable : sauvegarder sous la clé
    restaurée ne peut qu'échouer, après avoir payé l'archivage. C'est le cas de
    tous les shards qui suivent celui qui a complété l'index."""
    condition = _valeur(_step_contenant("actions/cache/save@v5"), "if")
    assert "steps.cache_an.outputs.cache-matched-key" in condition, (
        "La sauvegarde ne compare plus la clé restaurée à celle qu'elle "
        "écrirait : chaque shard paierait un archivage pour un refus."
    )
    for morceau in (
        "public-data-cache-an-",
        "steps.week.outputs.week",
        "steps.empreinte_obtenue.outputs.empreinte",
        "inputs.collect_interventions",
        "-interv-",
    ):
        assert morceau in condition, (
            f"La condition de sauvegarde ne reconstruit plus la clé (« {morceau} » "
            "manquant) : elle comparerait la clé restaurée à autre chose que la "
            "clé écrite, et sauterait — ou referait — la sauvegarde à tort."
        )


def test_la_sauvegarde_refuse_une_empreinte_vide():
    """Le step d'empreinte en échec rendrait une sortie vide, et la clé
    s'écrirait `…-interv-` : de nouveau muette sur son contenu."""
    condition = _valeur(_step_contenant("actions/cache/save@v5"), "if")
    assert "steps.empreinte_obtenue.outputs.empreinte != ''" in condition


def test_la_sauvegarde_survit_a_une_extraction_tronquee():
    """Un shard tronqué par son budget a quand même construit des index, et ce
    sont eux que les suivants n'auront pas à reconstruire. `success()` les
    jetterait."""
    condition = _valeur(_step_contenant("actions/cache/save@v5"), "if")
    assert "!cancelled()" in condition and "success()" not in condition


def test_un_echec_de_sauvegarde_ne_fait_pas_echouer_le_shard():
    """Le profil est déjà écrit et uploadé quand ce step s'exécute : un cache
    qui ne s'archive pas ne doit pas transformer un shard livré en shard en
    échec."""
    assert "continue-on-error: true" in _step_contenant("actions/cache/save@v5")


# ---------------------------------------------------------------------------
# 3. Le `path` identique, et l'ordre des steps
# ---------------------------------------------------------------------------


def test_restauration_et_sauvegarde_declarent_le_meme_path():
    """LA propriété silencieuse. La *version* d'une entrée est un hachage du
    `path` : deux listes différentes donnent deux entrées qui ne se voient pas,
    et la sauvegarde deviendrait invisible à la restauration — sans aucun
    message d'erreur. C'est la même règle qui lie déjà `extract-an` et
    `extract-roster-groupes` (#505, `test_ci_cache_paths.py`)."""
    restore = _bloc_path(_step_contenant("actions/cache/restore@v5\n        id: cache_an"))
    save = _bloc_path(_step_contenant("actions/cache/save@v5"))
    assert restore == save, (
        f"Les `path:` du cache AN divergent.\n  restore : {restore}\n  save    : {save}\n"
        "Deux versions d'entrée distinctes : la sauvegarde ne serait jamais "
        "restaurée, et rien ne le signalerait."
    )


def test_la_sauvegarde_vient_apres_la_publication_du_profil():
    """L'archivage est le poste qui peut s'étirer (5,2 s mesurées le 27/08 pour
    114 Mo ; une entrée complète reste à mesurer) et le `timeout-minutes` du job
    le couvre. Placé avant la publication, il ferait perdre le PROFIL — le
    défaut de #498, où 12 shards tués ont tous publié « 0 profil(s) ». Placé
    après, il ne peut coûter qu'une entrée de cache."""
    steps = _steps()
    rang = {nom: i for i, s in enumerate(steps) for nom in ("save",) if "actions/cache/save@v5" in s}
    assert rang, "step de sauvegarde du cache AN introuvable"
    i_save = rang["save"]
    i_upload = next(i for i, s in enumerate(steps) if "actions/upload-artifact" in s)
    i_publie = next(i for i, s in enumerate(steps) if "publish-written-profiles" in s)
    assert i_save > i_upload > i_publie, (
        f"Ordre des steps : publication={i_publie}, upload={i_upload}, "
        f"sauvegarde={i_save}. La sauvegarde du cache doit venir en dernier."
    )
