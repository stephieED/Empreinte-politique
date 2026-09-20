"""`AGENTS.md` ne dénombre pas ce qu'un lot déplace.

La propriétaire l'a formulé le 15/09/2026 : « il y a beaucoup d'éléments dans
AGENTS.md qui sont des notes informationnelles alors que ce fichier ne doit être
que des instructions. Du coup c'est un peu chiant parce que le contenu dérive
alors que ça devrait être stable. »

La règle existait déjà — §8 dit « **never a count that a run or a lot moves** » —
mais elle ne s'appliquait pas au fichier lui-même. À la relecture, il annonçait
**trois comptages faux** :

- « the nine jobs » — le run en compte onze depuis #922 ;
- « the eight outputs of `pivot_data/` » — dix ;
- « the nine jobs one by one », le même défaut plus bas, dans les References.

## Pourquoi ce test ne cherche pas « les chiffres »

Un premier essai interdisait tout nombre écrit en lettres devant un pluriel. Il
refusait « the four pre-commit guards », « the two shared indexes », « the four
canonical labels » — des faits d'**architecture**, qui ne bougent que par une
décision délibérée, et dont le compte fait partie de l'instruction.

Un nombre n'est pas dangereux en soi. Il l'est quand il compte **ce qu'un lot
déplace sans y penser**, et qu'un autre fichier le dénombre déjà mieux :

| Ce qu'on dénombre | Qui le sait vraiment |
| --- | --- |
| les jobs du run | `.github/workflows/generate-data.yml`, régénéré avec eux |
| les sorties de `pivot_data/` | `docs/data-architecture.md`, et un `ls` |

Ces deux-là ont cassé trois fois en une semaine. Ce sont ceux que ce test
refuse — nommément, sans généraliser, parce qu'une garde qui crie à tort finit
désarmée.
"""

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
AGENTS = RACINE / "AGENTS.md"
WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"

NOMBRES = (
    "two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    "deux|trois|quatre|cinq|six|sept|huit|neuf|dix|onze|douze|"
    r"\d+"
)

#: « the nine jobs », « les huit sorties de pivot_data ».
DENOMBREMENTS_INTERDITS = {
    "les jobs du run": re.compile(
        rf"\b(?:the|les)\s+(?:{NOMBRES})\s+jobs\b", re.IGNORECASE),
    "les sorties de pivot_data": re.compile(
        rf"\b(?:the|les)\s+(?:{NOMBRES})\s+(?:outputs|sorties)\b", re.IGNORECASE),
}

#: Une empreinte de commit fige un état du dépôt dans un fichier de règles.
COMMIT = re.compile(r"`[0-9a-f]{7,40}`")


def _lignes_hors_code():
    dans_code = False
    for numero, ligne in enumerate(AGENTS.read_text(encoding="utf-8").split("\n"), 1):
        if ligne.lstrip().startswith("```"):
            dans_code = not dans_code
            continue
        if not dans_code:
            yield numero, ligne


def test_agents_ne_denombre_pas_ce_qu_un_lot_deplace():
    """Écrire la chose sans son compte, et renvoyer au fichier qui la dénombre."""
    fautes = []
    for numero, ligne in _lignes_hors_code():
        for quoi, motif in DENOMBREMENTS_INTERDITS.items():
            if motif.search(ligne):
                fautes.append((numero, quoi, ligne.strip()[:90]))

    assert not fautes, (
        "AGENTS.md dénombre ce qu'un lot déplace (§8 : « never a count that a "
        "run or a lot moves ») :\n"
        + "\n".join(f"  ligne {n} — {quoi} : {t}" for n, quoi, t in fautes)
        + "\n\nÉcrire la chose sans son compte : le fichier qui la dénombre est "
        "régénéré avec elle, celui-ci non.")


def test_agents_ne_cite_aucune_empreinte_de_commit():
    """Sa place est la décision qui l'a mesurée : elle porte sa date, et
    personne ne la lit comme l'état du jour."""
    fautes = [(n, l.strip()[:90]) for n, l in _lignes_hors_code() if COMMIT.search(l)]

    assert not fautes, (
        "AGENTS.md cite une empreinte de commit ; elle appartient à la décision "
        "qui l'a mesurée :\n" + "\n".join(f"  ligne {n} : {t}" for n, t in fautes))


def test_le_motif_attrape_ce_qui_a_casse_et_epargne_l_architecture():
    """La distinction que ce test encode, vérifiée sur les deux formes.

    Ce qui a cassé : un compte de jobs ou de sorties. Ce qui doit passer : un
    fait d'architecture dont le compte fait partie de l'instruction, et un fait
    passé daté, qui ne périmera jamais.
    """
    attrape = DENOMBREMENTS_INTERDITS["les jobs du run"].search
    sorties = DENOMBREMENTS_INTERDITS["les sorties de pivot_data"].search

    assert attrape("the nine jobs, caches, artifacts")
    assert attrape("what a run does — the nine jobs one by one")
    assert sorties("the eight outputs of `pivot_data/`")

    assert not attrape("what a run does — the jobs, caches, artifacts")
    assert not attrape("**§3c. The four pre-commit guards**")
    assert not sorties("the two shared indexes")
    assert not sorties("Three drifts in a single day, 29-30/08/2026")


def test_le_compte_reel_des_jobs_vit_dans_le_yaml_pas_ici():
    """Le fichier qui dénombre est celui qui change avec ce qu'il dénombre.

    Ce test ne vérifie pas un nombre — il vérifie qu'il y a bien une source de
    vérité ailleurs, pour que le renvoi d'`AGENTS.md` mène quelque part.
    """
    texte = WORKFLOW.read_text(encoding="utf-8")
    apres_jobs = texte.split("\njobs:", 1)[-1]
    jobs = re.findall(r"^  ([a-z][a-z0-9-]*):$", apres_jobs, re.MULTILINE)

    assert len(jobs) >= 2, "le workflow doit porter les jobs qu'AGENTS.md ne compte plus"
    assert "merge-and-pivot" in jobs
