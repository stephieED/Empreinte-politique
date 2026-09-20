"""Le run de test : même workflow, périmètre réduit, jamais de commit (#792).

Ce que ces tests tiennent, ce n'est pas la commodité — c'est ce qui rendrait le
mode **trompeur** :

- un mode qui commiterait publierait un corpus qu'on sait partiel ;
- un slug introuvable qui disparaîtrait en silence ferait lire « rien à
  collecter » là où il faut lire « tu as mal tapé » (patron de #510) ;
- un mode qui divergerait du mode réel — autre code, autre ordre — ne prouverait
  rien de ce qu'on lui demande de prouver, et c'est le seul reproche qu'on ne
  pourrait pas rattraper après coup.
"""

import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

import perimetre_candidats as perimetre  # noqa: E402

WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"


# ---------------------------------------------------------------------------
# La saisie
# ---------------------------------------------------------------------------


def test_la_saisie_tolere_les_formes_courantes():
    """Une liste se colle depuis un log aussi souvent qu'elle se tape."""
    attendu = ["marine-le-pen", "gabriel-attal"]
    for saisie in (
        "marine-le-pen,gabriel-attal",
        " marine-le-pen , gabriel-attal ",
        "marine-le-pen;gabriel-attal",
        "marine-le-pen\ngabriel-attal",
    ):
        assert perimetre.slugs_demandes(saisie) == attendu, saisie


def test_une_saisie_vide_ne_declenche_rien():
    for vide in ("", "   ", ",,", None, 0):
        assert perimetre.slugs_demandes(vide) == []
        assert perimetre.est_run_de_test(vide) is False


def test_un_seul_slug_suffit_a_desarmer_le_commit():
    """Un champ, trois effets. Deux cases séparées autoriseraient « périmètre
    réduit ET commit », c'est-à-dire publier un corpus connu comme partiel."""
    assert perimetre.est_run_de_test("marine-le-pen") is True


# ---------------------------------------------------------------------------
# La restriction
# ---------------------------------------------------------------------------


def test_le_perimetre_intact_quand_rien_nest_demande():
    slugs = ["a", "b", "c"]
    assert perimetre.restreindre_au_test(slugs, "") == (slugs, [])


def test_les_retenus_gardent_lordre_du_perimetre():
    """Un run de test doit se comporter comme un run ordinaire amputé, pas comme
    une liste rejouée dans un autre ordre."""
    retenus, _ = perimetre.restreindre_au_test(["a", "b", "c"], "c,a")
    assert retenus == ["a", "c"]


def test_un_slug_hors_perimetre_est_rendu_pour_etre_nomme():
    """Mal tapé, sans slug résolvable, ou gelé (#760) : les trois se ressemblent
    sur une intersection, et aucun ne doit disparaître en silence."""
    retenus, introuvables = perimetre.restreindre_au_test(["a", "b"], "a, marine-lepen")
    assert retenus == ["a"]
    assert introuvables == ["marine-lepen"]


def test_un_gel_prime_sur_une_demande_de_test():
    """`slugs_a_collecter` a déjà retiré les gelés : les redemander ne les
    ramène pas. Le gel est un périmètre, pas une préférence."""
    candidats = [
        {"slug": "actif", "statut": "declare"},
        {"slug": "retire", "statut": "decline"},
    ]
    perimetre_du_run = perimetre.slugs_a_collecter(candidats)
    retenus, introuvables = perimetre.restreindre_au_test(perimetre_du_run, "retire")
    assert retenus == []
    assert introuvables == ["retire"]


# ---------------------------------------------------------------------------
# Sa place dans le workflow
# ---------------------------------------------------------------------------


def _texte() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def _sans_commentaires(bloc: str) -> str:
    return "\n".join(l for l in bloc.split("\n") if not l.lstrip().startswith("#"))


def test_le_champ_est_le_premier_du_formulaire():
    """Un mode se lit avant les réglages qu'il modifie."""
    entrees = re.search(r"^    inputs:\n(.*?)^jobs:", _texte(), re.MULTILINE | re.DOTALL)
    assert entrees, "bloc `inputs:` introuvable"
    noms = re.findall(r"^      ([a-z_]+):$", entrees.group(1), re.MULTILINE)
    assert noms[0] == "test_slugs", f"premier champ attendu `test_slugs`, trouvé `{noms[0]}`"


def test_le_libelle_annonce_les_deux_effets():
    """Le champ dit ce qu'il restreint ET qu'il ne committe pas : la seconde
    moitié est celle qu'on ne peut pas deviner."""
    ligne = next(l for l in _texte().splitlines() if "Test run —" in l)
    assert "empty = full run" in ligne
    assert "never commits" in ligne


def test_la_matrice_passe_par_le_predicat_partage():
    """Une seule définition du périmètre de test, comme pour le gel (#760)."""
    texte = _sans_commentaires(_texte())
    assert "restreindre_au_test" in texte
    assert "TEST_SLUGS: ${{ inputs.test_slugs }}" in texte


def test_un_perimetre_de_test_entierement_vide_echoue_tot():
    """Échouer ICI nomme la cause ; laisser tourner une heure la cache (#771)."""
    texte = _sans_commentaires(_texte())
    assert "TEST_PERIMETRE_VIDE" in texte
    assert "TEST_SLUG_INTROUVABLE" in texte


def test_le_commit_est_conditionne_a_labsence_de_perimetre_de_test():
    """L'effet qui ne se rattrape pas : un run réduit ne publie rien."""
    texte = _texte()
    bloc = texte[texte.index("- name: Committer et pousser les données mises à jour"):][:400]
    assert "if: ${{ inputs.test_slugs == '' }}" in bloc, (
        "le step de commit doit refuser de tourner en run de test"
    )


def test_le_run_de_test_dit_quil_na_rien_committe():
    """Un run vert qui n'a rien publié doit le dire, sinon il se lit comme un
    run qui a publié (#786, le vert par absence)."""
    texte = _texte()
    assert "- name: Run de test — commit désarmé" in texte
    bloc = texte[texte.index("- name: Run de test — commit désarmé"):][:600]
    assert "if: ${{ inputs.test_slugs != '' }}" in bloc
    assert "RUN_DE_TEST" in bloc
    assert "GITHUB_STEP_SUMMARY" in bloc


def test_la_retention_ne_tourne_pas_en_run_de_test():
    """Elle taille l'historique du dépôt : hors sujet pour un essai."""
    texte = _texte()
    bloc = texte[texte.index("- name: Fenêtre de rétention de l'historique de données"):][:200]
    assert "inputs.test_slugs == ''" in bloc


def test_le_roster_est_plafonne_et_lannonce():
    """Sans plafond, un run « de test » collecterait quand même 625 membres."""
    texte = _sans_commentaires(_texte())
    assert 'TEST_ROSTER_LIMIT: "8"' in texte
    assert "RUN_DE_TEST — roster plafonné" in texte


def test_un_plafond_explicite_lemporte():
    """Le plafond automatique ne s'applique qu'à la valeur par défaut."""
    texte = _sans_commentaires(_texte())
    garde = 'if [[ -n "${TEST_SLUGS:-}" && ( -z "${ROSTER_LIMIT}" || "${ROSTER_LIMIT}" == "0" ) ]]'
    assert garde in texte, "un roster_limit demandé doit survivre au mode test"


# ---------------------------------------------------------------------------
# Le retry ne doit pas transformer un run de test en run qui commite
# ---------------------------------------------------------------------------


RETRY = RACINE / ".github" / "workflows" / "retry-generate-data.yml"


def test_le_retry_ne_relance_pas_un_run_de_test():
    """Le piège que ce mode ouvrait, et qui n'existait pas avant lui.

    Le retry reconstruit les inputs **depuis les logs** et ne saurait pas
    reconstruire `test_slugs` de façon sûre : une valeur perdue relancerait un
    run de test en run COMPLET, qui committerait.
    """
    texte = RETRY.read_text(encoding="utf-8")
    bloc = texte[texte.index("- name: Re-déclencher generate-data.yml"):][:600]
    assert "steps.inputs.outputs.run_de_test == 'false'" in bloc, (
        "la relance doit exiger un `false` EXPLICITE"
    )


def test_labsence_dinformation_ne_relance_pas():
    """Log illisible, job absent, valeur inattendue : on s'abstient.

    Un retry manqué se rattrape d'un clic ; un commit publié depuis un
    périmètre réduit ne se rattrape pas. D'où `== 'false'` et non `!= 'true'`.
    """
    texte = RETRY.read_text(encoding="utf-8")
    assert "run_de_test=inconnu" in texte
    assert "RETRY_ABANDONNE" in texte, (
        "un retry abandonné doit se dire : un silence se lit comme une absence de panne"
    )
