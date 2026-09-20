"""Garde-fou #501 : aucun chemin de collecte ne peut plus diverger en silence
sur les interventions.

Contexte. Trois jobs de `generate-data.yml` lançaient `generate_all_profiles.py`
sur le réseau, et pendant des mois ils se sont comportés de trois façons
différentes face au même input `collect_interventions`, sans que rien ne le
signale :

- `extract-an` obéissait à l'input (`INTERV_FLAG`) ;
- `extract-roster-groupes` levait `--skip-interventions` en dur (#357) ;
- `extract-senat` collectait **toujours**, quel que soit le réglage — aucun
  flag, aucune lecture de l'input. Le run 32379928098 y a passé 74 minutes.

Aucun de ces trois comportements n'est illégitime en soi ; ce qui manquait,
c'est qu'ils soient *déclarés*. Une divergence lisible se discute, une
divergence tacite se découvre au bout de 74 minutes de runner.

Ce que ce fichier impose : **toute** invocation de `generate_all_profiles.py`
dans le workflow tombe dans exactement un mode explicite, et l'inventaire des
modes est écrit ici. Ajouter un chemin de collecte sans se prononcer sur les
interventions fait échouer `test_l_inventaire_est_a_jour` — le mode doit être
choisi et inscrit, pas hérité par défaut.

**#528 — `extract-senat` n'existe plus.** Le job qui a motivé cette issue a été
retiré avec le Sénat (docs/decisions/retrait-senat-528.md). Son entrée
d'inventaire et les quatre tests portant sur SON `timeout-minutes` et SON budget
sont partis avec lui ; l'inventaire lui-même reste armé, et c'est ce qui compte —
c'est la forme, pas ce job-là, qui empêche la prochaine divergence tacite.

Volontairement sans PyYAML (absent de `requirements.txt`), comme
`test_ci_budget_interventions.py` et `test_ci_cache_paths.py`.
"""

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"

# Provision de préambule d'un job (checkout, bootstrap-extraction, restauration
# du cache). Mesurée entre 6 s et 170 s sur les 15 derniers runs portant un
# `extract-senat` (14/08 → 20/08/2026). Même provision que `extract-an`, dont
# la mesure max est 193 s : c'est ce que `timeout-minutes` couvre EN PLUS de la
# collecte, et l'oublier est l'erreur d'origine de #498.
PREAMBULE_PROVISIONNE_SECONDES = 240

# Les quatre modes possibles face à `collect_interventions`.
MODE_INPUT = "piloté par collect_interventions"
MODE_JAMAIS = "--skip-interventions en dur"
MODE_SANS_CHAMBRE_FR = "--source ue : aucune chambre française, donc aucune intervention"
MODE_PIVOT = "--pivot-only : aucun appel réseau"
# #657 : une cinquième valeur, et pas un alias de MODE_INPUT. Le job roster obéit
# désormais au même input qu'extract-an, mais il ne collecte PAS la même chose —
# `--interventions-theme-seul` prend les débats sans leur verbatim et laisse les
# questions officielles. Les confondre laisserait passer, sans un test rouge, le
# jour où le job roster bascule en collecte complète (413 Mio au lieu de 103).
MODE_INPUT_THEME = "piloté par collect_interventions, réduit au thème (#657)"

# L'INVENTAIRE. Une entrée par invocation de `generate_all_profiles.py` dans
# generate-data.yml, clé `(job, rang dans le job)`.
#
# Toute nouvelle invocation doit être ajoutée ici avec son mode — c'est le
# point du garde-fou : le mode devient une décision écrite, pas un défaut.
INVENTAIRE = {
    ("extract-an", 0): MODE_INPUT,
    ("extract-ue-officiel", 0): MODE_SANS_CHAMBRE_FR,
    # #657 : les interventions ne sont plus écartées en dur. Le motif de #357
    # (« aucun agrégat ne les consomme ») était faux — `tags_thematiques`, et
    # donc `tags_thematiques_agreges` de chaque fiche de groupe, en dérive
    # intégralement. Elles sont collectées RÉDUITES AU THÈME, sous le même input
    # qu'extract-an, qui construit l'index dont ce job dépend.
    ("extract-roster-groupes", 0): MODE_INPUT_THEME,
    ("merge-and-pivot", 0): MODE_PIVOT,
    ("merge-and-pivot", 1): MODE_PIVOT,
}

# Jetons attendus dans la description de l'input pour chaque job qui ignore le
# réglage, OU qui lui obéit autrement que les autres (#657). Un job dont le
# comportement diverge de la lecture naïve de l'input doit être nommé là où
# l'opérateur lit cet input, pas seulement dans un commentaire YAML.
#
# `extract-roster-groupes` a changé de côté sans changer d'exigence : il
# n'ignore plus le réglage, il en fait une collecte RÉDUITE. Un opérateur qui
# coche la case doit lire, sur la case, que le roster n'en tire que le thème.
JETON_DESCRIPTION = {
    "extract-roster-groupes": "theme",
}


def _yaml() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def _blocs_de_job() -> dict[str, str]:
    """`{nom de job: corps}` pour chaque job de `generate-data.yml`."""
    texte = _yaml()
    apres_jobs = texte.split("\njobs:\n", 1)
    assert len(apres_jobs) == 2, "Section `jobs:` introuvable dans generate-data.yml."
    corps = apres_jobs[1]
    debuts = [(m.start(), m.group(1)) for m in re.finditer(r"^  ([a-z][a-z0-9-]*):\n", corps, flags=re.M)]
    assert debuts, "Aucun job détecté."
    blocs = {}
    for i, (debut, nom) in enumerate(debuts):
        fin = debuts[i + 1][0] if i + 1 < len(debuts) else len(corps)
        blocs[nom] = corps[debut:fin]
    return blocs


def _invocations() -> dict[tuple[str, int], str]:
    """`{(job, rang): commande}` pour chaque appel à `generate_all_profiles.py`.

    Les continuations `\\` sont recollées : `extract-roster-groupes` et
    `merge-and-pivot` écrivent leur commande sur plusieurs lignes, et une
    recherche ligne à ligne y raterait `--skip-interventions`.
    """
    trouvees: dict[tuple[str, int], str] = {}
    for nom, bloc in _blocs_de_job().items():
        lignes = bloc.split("\n")
        recollees: list[str] = []
        tampon = ""
        for ligne in lignes:
            nue = ligne.strip()
            if nue.startswith("#"):
                continue
            if nue.endswith("\\"):
                tampon += nue[:-1].strip() + " "
                continue
            recollees.append((tampon + nue).strip())
            tampon = ""
        if tampon:
            recollees.append(tampon.strip())
        rang = 0
        for commande in recollees:
            if "generate_all_profiles.py" not in commande:
                continue
            trouvees[(nom, rang)] = commande
            rang += 1
    return trouvees


def _script_du_job(nom: str) -> str:
    """Tout le shell d'un job, commentaires compris : c'est là que vivent les
    assignations de `INTERV_FLAG`."""
    return _blocs_de_job()[nom]


def _mode_observe(job: str, commande: str) -> str:
    """Le mode réellement déclaré par une invocation, lu sur le YAML."""
    if "--pivot-only" in commande:
        return MODE_PIVOT
    if re.search(r"--source\s+ue\b", commande):
        return MODE_SANS_CHAMBRE_FR
    if "--skip-interventions" in commande:
        return MODE_JAMAIS
    motif_tableau = re.search(r'"\$\{([A-Z_]*INTERV[A-Z_]*)\[@\]\}"', commande)
    if motif_tableau:
        tableau = motif_tableau.group(1)
        script = _script_du_job(job)
        assignation = re.search(
            rf"inputs\.collect_interventions[^\n]*\)\s*&&\s*{tableau}=\(|"
            rf"{tableau}=\([^)]*\)[^\n]*inputs\.collect_interventions|"
            rf"inputs\.collect_interventions[^\n]*{tableau}=",
            script,
        )
        if not assignation:
            # #657 : l'input peut arriver par `env:` plutôt qu'en clair dans le
            # script — c'est le cas du job roster, dont
            # tests/test_ci_inputs_workflow.py EXÉCUTE le bloc de décision et
            # interdit donc toute expression `${{ }}` à l'intérieur. Le lien
            # input → tableau reste lisible, en deux sauts au lieu d'un.
            for var in re.findall(
                r"^\s*([A-Z_]+): \$\{\{ inputs\.collect_interventions \}\}", script, re.M
            ):
                if re.search(rf"\${var}\b[^\n]*{tableau}=|{tableau}=\([^)]*\)[^\n]*\${var}\b", script):
                    assignation = True
                    break
        if assignation:
            # #657 : la FORME de la collecte se lit sur le drapeau que le
            # tableau reçoit, pas sur l'input. Deux jobs peuvent obéir au même
            # réglage et ne pas collecter la même chose.
            if re.search(rf"{tableau}=\([^)]*--interventions-theme-seul", script):
                return MODE_INPUT_THEME
            return MODE_INPUT
    return "AUCUN MODE DÉCLARÉ"


# ---------------------------------------------------------------------------
# Le garde-fou : l'inventaire et le YAML disent la même chose
# ---------------------------------------------------------------------------

def test_l_inventaire_est_a_jour():
    """Un quatrième chemin de collecte ne peut pas apparaître en silence."""
    observees = set(_invocations())
    inventoriees = set(INVENTAIRE)
    nouvelles = observees - inventoriees
    disparues = inventoriees - observees
    assert not nouvelles, (
        "Invocation(s) de generate_all_profiles.py absente(s) de l'INVENTAIRE : "
        f"{sorted(nouvelles)}. Décidez ce que ce chemin fait des interventions "
        "et inscrivez-le — c'est précisément la divergence tacite que #501 corrige "
        "(l'ex-job extract-senat a collecté hors de tout réglage pendant des mois)."
    )
    assert not disparues, (
        f"L'INVENTAIRE référence des invocations qui n'existent plus : {sorted(disparues)}."
    )


@pytest.mark.parametrize("cle", sorted(INVENTAIRE))
def test_chaque_invocation_declare_le_mode_inventorie(cle):
    invocations = _invocations()
    if cle not in invocations:
        pytest.skip("couvert par test_l_inventaire_est_a_jour")
    observe = _mode_observe(cle[0], invocations[cle])
    assert observe == INVENTAIRE[cle], (
        f"{cle[0]} (invocation n°{cle[1]}) : mode attendu « {INVENTAIRE[cle]} », "
        f"observé « {observe} ».\n  {invocations[cle]}"
    )


def test_aucune_invocation_reseau_ne_reste_muette():
    """La formulation directe du défaut de #501 : sur le chemin réseau, ne rien
    dire des interventions n'est pas un mode."""
    muettes = [
        cle for cle, commande in _invocations().items()
        if _mode_observe(cle[0], commande) == "AUCUN MODE DÉCLARÉ"
    ]
    assert not muettes, (
        f"Invocation(s) sans mode d'interventions déclaré : {sorted(muettes)}. "
        "Attendu : --skip-interventions, un tableau INTERV_* piloté par "
        "inputs.collect_interventions, --source ue ou --pivot-only."
    )


def test_la_description_de_l_input_nomme_les_jobs_qui_divergent():
    """Un job qui n'obéit pas à `collect_interventions` doit être nommé là où
    l'opérateur lit cet input. La description disait « Affects extract-an only —
    the roster job always skips them » alors qu'extract-senat collectait
    toujours : elle décrivait deux jobs sur trois. Ce job a été retiré (#528),
    la règle reste."""
    motif = re.search(r'^      collect_interventions:\n        description: "([^"]*)"', _yaml(), flags=re.M)
    assert motif, "Input `collect_interventions` introuvable ou description non littérale."
    description = motif.group(1)
    ignorants = {
        job for (job, _), mode in INVENTAIRE.items()
        if mode in (MODE_JAMAIS, MODE_INPUT_THEME)
    }
    manquants = [
        JETON_DESCRIPTION[job] for job in sorted(ignorants)
        if job in JETON_DESCRIPTION and JETON_DESCRIPTION[job].lower() not in description.lower()
    ]
    assert not manquants, (
        f"La description de collect_interventions ne nomme pas {manquants} alors que "
        f"ces jobs en divergent (ignoré, ou collecte réduite) : {sorted(ignorants)}."
        f"\n  « {description} »"
    )


# ---------------------------------------------------------------------------
# Le timeout d'extract-senat : bloc RETIRÉ par #528
#
# Quatre tests tenaient les valeurs de ce job : `timeout-minutes` >= préambule
# provisionné + collecte résiduelle projetée ; `timeout-minutes` <= 20 min (un
# plafond qu'on n'atteint jamais ne protège de rien — 90 min n'ont jamais coupé
# ce job) ; et pas de `--budget-interventions-secondes` sous
# `--skip-interventions`, qui serait un réglage mort.
#
# La dernière de ces règles n'est pas propre au Sénat, et elle reste vraie :
# `build_profile_any_chambre` neutralise le budget d'interventions sous
# `--skip-interventions` (#514). Elle est aujourd'hui sans job à surveiller —
# `extract-roster-groupes`, seul autre `MODE_JAMAIS`, n'en pose pas. Le jour où
# une invocation combine les deux, c'est ce test-là qu'il faut réécrire, avec
# les mesures de ce job-là. Voir docs/decisions/retrait-senat-528.md.
# ---------------------------------------------------------------------------


def test_aucun_mode_jamais_ne_pose_de_budget_d_interventions():
    """La seule des quatre règles ci-dessus qui ne dépendait pas du Sénat.

    `--budget-interventions-secondes` n'a de sens que sur un chemin qui
    collecte : `build_profile_any_chambre` le neutralise sous
    `--skip-interventions`. Le poser quand même serait un réglage mort, du genre
    qui fait croire à une protection — c'est exactement #514.
    """
    invocations = _invocations()
    fautifs = [
        cle for cle, mode in INVENTAIRE.items()
        if mode == MODE_JAMAIS
        and cle in invocations
        and "--budget-interventions-secondes" in invocations[cle]
    ]
    assert not fautifs, (
        f"{sorted(fautifs)} pose(nt) un budget d'interventions tout en levant "
        "--skip-interventions : le budget serait None par construction (#514)."
    )
