"""#1137 (piste annexe) — la matrice roster n'est bornée que dans les modes où
un shard va chercher quelque chose chez l'Assemblée nationale.

Le raisonnement, en une phrase
------------------------------
#467 a ouvert `extract-roster-groupes` à `max-parallel: 4` et a écrit, noir sur
blanc, pourquoi pas 8 : « en cold_start=true les steps de cache sont sautés et
chaque shard retélécharge ~40 Mo d'archives AN ». L'argument est juste — et il
ne parle que de ce mode-là. Il était pourtant appliqué à **tous** les runs.
C'est la même forme de défaut qu'au `max-parallel` d'`extract-an`
(tests/test_ci_max_parallel_cle_chaude_1137.py) : un argument exact, appliqué
au-delà du cas qu'il décrit.

Hors de ces modes, les 8 shards restaurent la même entrée immuable de 21 Mo
chez GitHub et ne demandent **rien** à `data.assemblee-nationale.fr`.

Ce que ces tests tiennent
-------------------------
La borne est une **prudence réseau**, pas un plafond de concurrence : elle doit
donc suivre les modes qui déclenchent du téléchargement, et rien d'autre. Si un
troisième mode de ce genre apparaît un jour — un input qui fait télécharger un
shard —, c'est ici qu'on verra qu'il n'a pas été ajouté à la condition.
"""

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"

# Le nombre de tranches que `prepare-roster-matrix` construit. Ouvrir
# `max-parallel` au-delà ne servirait à rien : il n'y a pas plus de shards.
ROSTER_SHARDS = 8

# Les modes où un shard roster télécharge chez l'AN, donc où la rafale se borne.
MODES_BORNES = ("cold_start", "collect_dossiers_legislatifs")


def _yaml() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def _max_parallel(job: str) -> str:
    texte = _yaml()
    debut = re.search(rf"^  {re.escape(job)}:\s*$", texte, re.MULTILINE)
    assert debut, f"Job `{job}` introuvable."
    suite = re.search(r"^  [a-z][a-z0-9-]*:\s*$", texte[debut.end():], re.MULTILINE)
    bloc = texte[debut.end(): debut.end() + suite.start()] if suite else texte[debut.end():]
    trouve = re.search(r"\n      max-parallel: (.+)\n", bloc)
    assert trouve, f"`{job}` n'a plus de `max-parallel:`."
    return trouve.group(1).strip()


def test_le_nombre_de_shards_roster_est_bien_celui_qu_on_croit():
    """Garde-fou du garde-fou : la borne haute testée plus bas n'a de sens que
    si `prepare-roster-matrix` construit toujours ce nombre de tranches."""
    assert re.search(rf'\n          ROSTER_SHARDS: "{ROSTER_SHARDS}"\n', _yaml()), (
        f"ROSTER_SHARDS n'est plus {ROSTER_SHARDS} : le `max-parallel` de la "
        "matrice roster doit être relu avec lui — l'ouvrir au-delà du nombre de "
        "shards ne fait rien, rester en dessous laisse une vague de plus."
    )


def test_la_matrice_roster_tourne_en_une_seule_vague_hors_des_modes_reseau():
    expression = _max_parallel("extract-roster-groupes")
    trouve = re.search(r"&&\s*(\d+)\s*\|\|\s*(\d+)", expression)
    assert trouve, (
        f"`max-parallel: {expression}` n'est plus conditionnel. Si la borne de "
        "#467 est redevenue permanente, c'est une décision à écrire : elle "
        "coûte ~10 min de chemin critique à chaque run (mesuré sur le run "
        "36153601970, 1 306 s de temps mur en deux vagues)."
    )
    borne, ouvert = int(trouve.group(1)), int(trouve.group(2))
    assert ouvert == ROSTER_SHARDS, (
        f"Hors des modes réseau, la matrice tourne à {ouvert} pour "
        f"{ROSTER_SHARDS} shards : il reste une vague qui ne sert à rien."
    )
    assert borne == 4, (
        f"La borne des modes réseau est {borne} et non 4 : c'est la valeur que "
        "#467 a mesurée (~40 Mo d'archives AN par shard en cold_start), et la "
        "changer demande une nouvelle mesure, pas une estimation."
    )


def test_la_borne_suit_exactement_les_modes_qui_telechargent():
    """La borne est une prudence réseau. Elle doit se déclencher sur les modes
    où un shard va chercher chez l'AN — et sur ceux-là seulement, sinon elle
    redevient le plafond permanent que #467 n'a jamais voulu."""
    expression = _max_parallel("extract-roster-groupes")
    cites = set(re.findall(r"inputs\.(\w+)", expression))
    assert cites == set(MODES_BORNES), (
        f"La condition porte sur {sorted(cites)} au lieu de "
        f"{sorted(MODES_BORNES)}.\n"
        "- un mode en trop borne des runs qui ne téléchargent rien ;\n"
        "- un mode manquant lâche 8 shards sur data.assemblee-nationale.fr, "
        "dont ce dépôt a déjà documenté trois modes de défaillance (#443)."
    )


def test_les_deux_matrices_ne_partagent_plus_une_cadence_en_dur():
    """Les deux `max-parallel` du workflow sont désormais des expressions, et
    chacune a sa propre raison de l'être : `extract-an` regarde l'état du cache
    (la chaîne de réchauffement sert-elle ?), le roster regarde le mode (un
    shard va-t-il télécharger ?). Une valeur en dur qui réapparaîtrait est le
    signe qu'une des deux raisons a été perdue en route."""
    for job in ("extract-an", "extract-roster-groupes"):
        expression = _max_parallel(job)
        assert expression.startswith("${{"), (
            f"`{job}` est revenu à une cadence fixe (`{expression}`) : les deux "
            "matrices se règlent sur ce que le run rencontre, pas sur une "
            "constante (#1137)."
        )
