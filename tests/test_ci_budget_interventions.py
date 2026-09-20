"""Garde-fou #498 : le timeout du job, le budget de la collecte et le message de
temps mur doivent rester d'accord entre eux.

Contexte. `timeout-minutes: 5` sur `extract-an` était justifié par des durées
mesurées « 1m18s-2m10s » — toutes relevées dans le mode par défaut, celui qui
lève `--skip-interventions`. Employé avec `collect_interventions=true`, ce
timeout tuait le shard : 4 shards sur 8 du run 32302557156, puis 8 sur 8 du
run 32379928098 — ce dernier n'a collecté aucun profil AN. Le correctif tient
en deux valeurs couplées, écrites à deux endroits différents du même fichier :

- `timeout-minutes` d'`extract-an`, conditionnel au mode ;
- `--budget-interventions-secondes` du step d'extraction, qui borne la collecte
  *à l'intérieur* du process pour que le timeout de job ne soit plus le
  mécanisme d'arrêt normal.

Découplées, elles reproduisent exactement le défaut d'origine : un budget plus
grand que ce que le timeout laisse réellement à l'extraction, et le shard meurt
à nouveau sans rien écrire. D'où ce test.

Les assertions ne sont pas que textuelles : le fragment de bash du step est
réellement exécuté dans les deux modes, parce que c'est un garde-fou débranché
— écrit mais jamais déclenché — qui est à l'origine de #460.

#546 a ajouté la troisième valeur qui manquait au contrat : le budget est
vérifié ENTRE deux unités de collecte, donc le timeout doit couvrir le budget
PLUS l'unité en vol au moment où il expire. Sans elle, la paire (9 min, 240 s)
passait ce test alors qu'elle provisionnait 575 s pour 540 s disponibles.

Volontairement sans PyYAML (absent de `requirements.txt`), comme
`test_ci_cache_paths.py` et `test_ci_garde_fou_interventions.py`.
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"

# Provision de préambule de job : `actions/checkout`, `setup-python`, `pip
# install`, restauration des deux caches, téléchargement de l'artifact
# d'amendements. Mesurée entre 30 s et 193 s sur les 32 shards `extract-an`
# des runs 32233766814, 32288588518, 32302557156 et 32379928098, et entre
# 146 s et 197 s sur les 8 shards du run 33110395663 (27/08) — c'est ce que
# le `timeout-minutes` couvre en plus de la collecte, et ce que le budget
# interne, lui, ne couvre pas. La population n'a pas bougé, le maximum non
# plus : 197 s. #546 ramène la provision de 240 s à 200 s, au plus près du
# maximum mesuré, parce que les 40 s de confort étaient prises sur la marge
# qui manquait ailleurs (voir DEPASSEMENT_UNITE_EN_VOL_SECONDES).
PREAMBULE_PROVISIONNE_SECONDES = 200

# Préambule du process Python (avant la première unité d'interventions) plus
# écriture du profil, deux postes que le budget interne ne compte pas : mesurés
# 5-6 s et 3-4 s sur les 7 shards porteurs du run 33110395663. Provision 15 s.
HORS_BUDGET_DU_PROCESS_SECONDES = 15

# CE QUE #546 A AJOUTÉ, ET QUI MANQUAIT. Le budget est vérifié ENTRE deux
# unités, jamais au milieu de l'une : quand il expire, l'unité en vol va à son
# terme. Le `timeout-minutes` doit donc couvrir le budget PLUS cette unité.
# L'omettre est ce qui rendait la paire (9 min, 240 s) incohérente — 575 s de
# somme provisionnée pour 540 s disponibles — alors que le test ci-dessous la
# déclarait bonne.
#
# Quelle unité ? Pas une législature Syceron : elles sont engagées à l'horloge
# 41-63 s (mesuré sur les 7 shards porteurs de 33110395663), très en deçà de
# tout budget de cet ordre, donc jamais celle qui dépasse. C'est une législature
# de questions officielles, mesurée 5-104 s — max jean-luc-melenchon,
# législature 15, run 33110395663. Provision 120 s.
DEPASSEMENT_UNITE_EN_VOL_SECONDES = 120


def _yaml() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def _timeouts_extract_an() -> tuple[int, int]:
    """`(minutes sans interventions, minutes avec)` lus sur le `timeout-minutes`
    d'`extract-an`."""
    texte = _yaml()
    bloc = re.search(r"^  extract-an:\n(.*?)(?=\n  [a-z][a-z0-9-]*:\n)", texte, flags=re.S | re.M)
    assert bloc, "Job `extract-an` introuvable dans generate-data.yml."
    motif = re.search(
        r"^    timeout-minutes:\s*\$\{\{\s*inputs\.collect_interventions\s*&&\s*(\d+)\s*\|\|\s*(\d+)\s*\}\}",
        bloc.group(1),
        flags=re.M,
    )
    assert motif, (
        "Le `timeout-minutes` d'extract-an n'est plus conditionnel à "
        "`inputs.collect_interventions`. Une valeur unique ne peut pas couvrir les "
        "deux modes : c'est le défaut que #498 corrige (extraction mesurée à "
        "8-18 s sans interventions, 59-286 s avec)."
    )
    avec, sans = int(motif.group(1)), int(motif.group(2))
    return sans, avec


def _script_extraction() -> str:
    """Le shell du step « Extraction AN », tel que GitHub Actions l'exécutera."""
    texte = _yaml()
    motif = re.search(
        r"^      - name: Extraction AN\b.*?\n        run: \|\n(.*?)(?=\n      [-#])",
        texte,
        flags=re.S | re.M,
    )
    assert motif, "Step « Extraction AN » introuvable ou sans `run: |`."
    return "\n".join(ligne[10:] for ligne in motif.group(1).split("\n"))


def _budget_du_script() -> int:
    motif = re.search(r"--budget-interventions-secondes (\d+)", _script_extraction())
    assert motif, (
        "Le step d'extraction ne passe plus `--budget-interventions-secondes`. "
        "Sans budget interne, un shard tué par `timeout-minutes` ne publie AUCUN "
        "profil (constaté : « Publication : 0 profil(s) » sur les 12 shards tués "
        "des runs 32302557156 et 32379928098)."
    )
    return int(motif.group(1))


def _executer_script(collect_interventions: str) -> str:
    """Exécute le fragment de bash du step, sans la ligne d'extraction Python,
    et renvoie les flags calculés."""
    script = _script_extraction()
    lignes = [ligne for ligne in script.split("\n") if "generate_all_profiles.py" not in ligne]
    corps = "\n".join(lignes)
    corps = corps.replace("${{ inputs.collect_interventions }}", collect_interventions)
    corps = re.sub(r"\$\{\{[^}]*\}\}", "0", corps)
    corps += '\necho "BUDGET=${BUDGET_FLAG[*]-}"\necho "INTERV=${INTERV_FLAG[*]-}"\n'
    resultat = subprocess.run(
        ["bash", "-c", corps],
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin", "FRESH": "false", "OVERWRITE": "false"},
    )
    assert resultat.returncode == 0, resultat.stderr
    return resultat.stdout


# ---------------------------------------------------------------------------
# Le contrat entre les deux valeurs
# ---------------------------------------------------------------------------

def test_le_mode_interventions_a_un_timeout_plus_large():
    sans, avec = _timeouts_extract_an()
    assert avec > sans, (
        "Le mode interventions ajoute deux charges absentes du mode par défaut "
        "— archives de débats Syceron et archives de questions officielles ; la "
        "recherche NosDéputés qui en était une troisième est partie avec #529. "
        "Son timeout ne peut pas être inférieur ou égal."
    )


def test_le_budget_tient_dans_le_timeout_du_mode_ou_il_s_applique():
    """Le cœur du garde-fou. Le budget ne borne que la collecte ; le timeout
    borne le job entier — préambule, postes hors budget du process, et l'unité
    en vol au moment où le budget expire (#546)."""
    _, avec = _timeouts_extract_an()
    budget = _budget_du_script()
    plafond = avec * 60
    somme = (
        budget
        + PREAMBULE_PROVISIONNE_SECONDES
        + HORS_BUDGET_DU_PROCESS_SECONDES
        + DEPASSEMENT_UNITE_EN_VOL_SECONDES
    )
    assert somme <= plafond, (
        f"budget={budget} s + préambule provisionné={PREAMBULE_PROVISIONNE_SECONDES} s "
        f"+ hors budget du process={HORS_BUDGET_DU_PROCESS_SECONDES} s "
        f"+ unité en vol={DEPASSEMENT_UNITE_EN_VOL_SECONDES} s = {somme} s "
        f"dépasse le timeout du mode interventions ({avec} min = {plafond} s). "
        "Le shard serait de nouveau tué avant d'écrire son profil — exactement "
        "le défaut de #498."
    )


def test_le_budget_ne_descend_pas_sous_les_horloges_de_collecte_mesurees():
    """L'autre versant de l'arbitrage. Réduire le budget rend la paire trivialement
    cohérente, au prix de troncatures : il ne doit pas passer sous les horloges de
    collecte déjà mesurées sur des profils qui allaient au bout.

    Horloges du run 33110395663 (27/08), 7 shards porteurs, en secondes :
    166 (laurent-wauquiez), 200 (gabriel-attal), 208 (edouard-philippe),
    208 (bruno-retailleau), 244 (marine-le-pen), 247* (jerome-guedj),
    332* (jean-luc-melenchon) — * = tronqué par le budget de 240 s alors en place.
    Descendre sous 244 s retirerait marine-le-pen du lot des profils complets.
    """
    assert _budget_du_script() >= 244, (
        "Le budget passe sous l'horloge de collecte de marine-le-pen (244 s, run "
        "33110395663) : un profil qui sortait complet sortirait tronqué. La "
        "troncature est déclarée (#514), pas gratuite."
    )


def test_le_timeout_ne_derive_pas_vers_le_blocage_de_20_minutes():
    """La borne haute a une raison : un shard bloqué immobilise tout le matrix
    séquentiel (`max-parallel: 1`) derrière lui — 20+ min constatées le 16/08 sur
    `jerome-guedj`. Élargir le timeout au-delà de 10 min rouvrirait ce risque."""
    sans, avec = _timeouts_extract_an()
    assert sans <= 5
    assert avec <= 10


def test_le_message_de_temps_mur_annonce_le_timeout_du_mode_courant():
    """Annoncer 5 min par shard pendant qu'un run en consomme 9 rendrait cet
    avertissement faux au moment précis où il sert."""
    texte = _yaml()
    motif = re.search(
        r"AN_TIMEOUT_MINUTES:\s*\$\{\{\s*inputs\.collect_interventions\s*&&\s*(\d+)\s*\|\|\s*(\d+)\s*\}\}",
        texte,
    )
    assert motif, (
        "`prepare-an-matrix` n'expose plus AN_TIMEOUT_MINUTES : son avertissement "
        "de temps mur retomberait sur une valeur en dur, désolidarisée du timeout "
        "réel d'extract-an."
    )
    sans, avec = _timeouts_extract_an()
    assert (int(motif.group(1)), int(motif.group(2))) == (avec, sans)
    assert "COUNT * 5" not in texte, (
        "Le calcul du temps mur multiplie encore par une constante 5 : il doit "
        "utiliser AN_TIMEOUT_MINUTES."
    )


# ---------------------------------------------------------------------------
# Le flag est réellement posé, et réellement accepté
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "collect_interventions, budget_attendu, interv_attendu",
    [("true", True, False), ("false", False, True)],
)
def test_le_flag_suit_le_mode(collect_interventions, budget_attendu, interv_attendu):
    sortie = _executer_script(collect_interventions)
    budget_pose = "--budget-interventions-secondes" in sortie.split("BUDGET=")[1].split("\n")[0]
    skip_pose = "--skip-interventions" in sortie.split("INTERV=")[1].split("\n")[0]
    assert budget_pose is budget_attendu, sortie
    assert skip_pose is interv_attendu, sortie


def test_le_flag_existe_vraiment_cote_python():
    """Un flag inconnu ferait échouer argparse *après* le checkout et le pip
    install, c'est-à-dire 2 à 3 min de runner par shard pour rien."""
    aide = subprocess.run(
        [sys.executable, str(RACINE / "src" / "generate_all_profiles.py"), "--help"],
        capture_output=True,
        text=True,
        cwd=RACINE,
    )
    assert aide.returncode == 0, aide.stderr
    assert "--budget-interventions-secondes" in aide.stdout
