"""Garde-fou #511 : le contrôle « collecté mais non publié » reste branché, au bon endroit.

Un contrôle correct placé trop tôt est un contrôle faux. Entre la passe pivot
des candidats déclarés et la passe pivot roster-driven, **tout membre de roster
est légitimement sans pivot** : y brancher ce contrôle signalerait 543 écarts
sur un run parfaitement sain. C'est ce que ces tests verrouillent, autant que la
présence de l'appel.

Ils verrouillent aussi le **cloisonnement des trois tolérances** :
`allow_declared_losses` (#460/#470) et `allow_broken_references` (#485) ne
doivent pas désarmer celle-ci — #470 a documenté le piège inverse.

Volontairement sans PyYAML (absent de requirements.txt), comme les autres
gardes-fous de workflow de ce dépôt.
"""

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"
SCRIPT = "src/audit_collecte_non_publiee.py"


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


#: Ancré sur le NOM du step et pas sur l'appel : `--tolerer-non-publies` est
#: posé quelques lignes AVANT, dans le tableau `TOLERANCE`.
NOM_STEP = "- name: Collecté mais non publié"


def _step_du_controle(code: str) -> str:
    debut = code.find(NOM_STEP)
    assert debut >= 0, f"step `{NOM_STEP}` absent du job"
    bloc = code[debut:]
    suivant = bloc.find("- name:", 1)
    step = bloc[:suivant] if suivant > 0 else bloc
    assert SCRIPT in step, "le step ne lance plus le contrôle"
    return step


def test_le_controle_est_appele_dans_merge_and_pivot():
    code = _sans_commentaires(_bloc_job("merge-and-pivot"))
    assert SCRIPT in code, (
        "Le contrôle « collecté mais non publié » n'est plus appelé : une passe "
        "pivot qui itère sur moins que ce que le run a collecté redeviendrait "
        "invisible, et le run se conclurait en succès (#511)."
    )


def test_le_controle_precede_le_commit():
    """Après le commit, il ne protégerait plus rien."""
    code = _sans_commentaires(_bloc_job("merge-and-pivot"))
    rang_controle = code.find(SCRIPT)
    rang_commit = code.find("git commit")
    assert rang_controle >= 0 and rang_commit >= 0
    assert rang_controle < rang_commit


def test_le_controle_suit_les_deux_passes_de_normalisation_pivot():
    """LE test d'emplacement.

    `merge_profile.py --dirs` remplit `raw_data/profiles`, puis DEUX passes
    `generate_all_profiles.py --pivot-only` écrivent les pivots : celle de
    `raw_data/candidats.json`, puis celle de `raw_data/roster_candidats.json`.
    Entre les deux, chaque membre de roster est sans pivot pour une raison
    parfaitement légitime — le contrôle y signalerait un écart qui n'existe pas
    encore.
    """
    code = _sans_commentaires(_bloc_job("merge-and-pivot"))
    rang_controle = code.find(SCRIPT)
    assert rang_controle > 0

    rang_fusion = code.find("src/merge_profile.py")
    assert 0 <= rang_fusion < rang_controle, (
        "la fusion des profils bruts doit précéder le rapprochement : sinon "
        "`raw_data/profiles` n'a pas encore reçu les profils du run.")

    passes_pivot = [m.start() for m in re.finditer(r"--pivot-only", code)]
    assert len(passes_pivot) >= 2, (
        "les deux passes pivot attendues (candidats déclarés, puis roster) ne "
        "sont plus toutes les deux dans le job.")
    assert max(passes_pivot) < rang_controle, (
        "le contrôle s'exécute avant la dernière passe pivot : il signalerait "
        "comme non publié tout membre de roster que cette passe est justement "
        "en train de publier (#511).")

    rang_roster = code.find("--candidats raw_data/roster_candidats.json")
    assert 0 <= rang_roster < rang_controle, (
        "la passe pivot roster-driven doit précéder le contrôle.")


def test_les_passes_pivot_n_ecrivent_pas_de_point_de_sauvegarde():
    """La cause du run `32773067295` (24/08/2026), et pas seulement son symptôme.

    `generate_all_profiles.py` écrit sa progression dans
    `raw_data/profiles/.generation_checkpoint.json` sauf `--no-checkpoint` —
    dans le répertoire même que ce contrôle inventorie. Les deux passes
    `--pivot-only` de `merge-and-pivot` n'ont **rien à reprendre** (ni l'une ni
    l'autre ne porte `--resume`) : le fichier n'y servait qu'à faire échouer le
    contrôle, sur un run dont les 22 autres jobs étaient verts.

    Le contrôle écarte désormais les fichiers cachés, mais le point de
    sauvegarde reste lu par les six inventaires en `glob("*.json")` du dépôt —
    `pathlib` remonte les fichiers cachés, contrairement au module `glob`.
    """
    code = _sans_commentaires(_bloc_job("merge-and-pivot"))
    invocations = re.findall(
        r"python3 src/generate_all_profiles\.py(?:[^\n]*\\\n)*[^\n]*", code)
    passes_pivot = [i for i in invocations if "--pivot-only" in i]
    assert len(passes_pivot) >= 2, (
        "les deux passes pivot attendues ne sont plus dans le job.")
    for passe in passes_pivot:
        assert "--no-checkpoint" in passe, (
            "une passe --pivot-only sans --no-checkpoint écrit "
            "`raw_data/profiles/.generation_checkpoint.json`, que ce contrôle "
            "rencontre juste après (#518).")
        assert "--resume" not in passe, (
            "cette passe reprend une progression : --no-checkpoint la "
            "priverait de son point de reprise. Revoir le placement du "
            "fichier plutôt que de retirer le drapeau.")


def test_un_profil_non_publie_annule_le_commit():
    """Sans `exit 1`, le step afficherait le rapport et laisserait committer —
    c'est-à-dire exactement le run 32405297873, conclu en succès."""
    step = _step_du_controle(_sans_commentaires(_bloc_job("merge-and-pivot")))
    assert "exit 1" in step
    assert "COLLECTE_NON_PUBLIEE" in step, (
        "Le message d'erreur doit être repérable dans les logs : c'est ce qui "
        "distingue un échec diagnostiquable d'un job rouge."
    )


def test_le_controle_porte_sur_les_deux_repertoires_de_profils():
    step = _step_du_controle(_sans_commentaires(_bloc_job("merge-and-pivot")))
    assert "--raw-dir raw_data/profiles" in step
    assert "--pivot-dir pivot_data/profiles" in step


def test_la_tolerance_est_distincte_des_deux_autres():
    step = _step_du_controle(_sans_commentaires(_bloc_job("merge-and-pivot")))
    assert "--tolerer-non-publies" in step
    assert "--tolerer-pertes" not in step
    assert "--tolerer-orphelins" not in step
    assert "allow_declared_losses" not in step
    assert "allow_broken_references" not in step
    assert "inputs.allow_unpublished_profiles" in step


def test_la_tolerance_existe_et_est_desactivee_par_defaut():
    texte = WORKFLOW.read_text(encoding="utf-8")
    debut = texte.find("allow_unpublished_profiles:")
    assert debut > 0, "input `allow_unpublished_profiles` absent"
    bloc = texte[debut:][:1200]
    assert "default: false" in bloc
    # Même exigence qu'en #485 : GitHub affiche la description comme libellé du
    # champ et masque le nom de l'input. La gravité doit se lire dans le texte
    # lui-même, pas dans un renvoi vers un nom invisible à l'écran.
    assert "LAST RESORT" in bloc, (
        "Le libellé doit porter sa propre marque de gravité, distincte de "
        "« INTENDED REMOVAL » (#470) et de « EMERGENCY ONLY » (#485)."
    )


def test_le_rapport_est_joint_au_resume_de_job():
    """Un rapport qu'il faut aller télécharger n'est pas lu — et c'est en échec
    qu'on en a le plus besoin."""
    step = _step_du_controle(_sans_commentaires(_bloc_job("merge-and-pivot")))
    assert "GITHUB_STEP_SUMMARY" in step


def test_les_deux_autres_controles_restent_branches():
    """Les trois sont complémentaires, pas alternatifs : le contrôle de perte ne
    voit pas un profil jamais publié, l'intégrité référentielle non plus, et
    celui-ci ne voit ni une perte ni une clé orpheline."""
    code = _sans_commentaires(_bloc_job("merge-and-pivot"))
    assert "src/audit_diff_profils.py" in code
    assert "src/audit_integrite_referentielle.py" in code
