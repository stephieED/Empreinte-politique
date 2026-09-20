"""Un module lourdement gouverné ne peut plus ne citer aucune décision.

`docs/technical_decisions.md` va des décisions vers le code. Rien n'allait du
**code vers ses décisions**, sauf renvoi écrit à la main dans le module — donc
inégalement posé, et re-troué à chaque module créé. Mesuré le 30/08/2026 :
`src/merge_profile.py` citait **zéro** décision alors que 39 nomment une de ses
fonctions, et c'est exactement le module de l'épic #598, dont personne n'avait
relu la politique de fusion pendant des mois.

`scripts/generer_decisions_par_module.py` retourne le lien et écrit
`docs/decisions-par-module.md`. Ce fichier-ci tient les deux propriétés sans
lesquelles cette table redeviendrait de la décoration :

1. **elle est générée** — un fichier committé qui a dérivé du dépôt fait échouer
   la suite, faute de quoi une table périmée serait pire que pas de table ;
2. **le trou ne peut plus se creuser au-delà du seuil** — un module qu'au moins
   `SEUIL_MODULE_TROUE` décisions gouvernent, et qui n'en cite aucune, échoue.

## Le seuil, et pourquoi 5

Il ne protège pas contre « une décision non citée » : il protège contre **la
forme #598**, un module dont la politique n'a plus aucune porte d'entrée depuis
le code. Trois chiffres l'ont fixé, mesurés sur les 168 décisions et les
62 modules de `src/` retenus (les 3 passes `migrer_*` sont écartées) :

| | |
| --- | --- |
| les deux cas qui ont coûté quelque chose | `merge_profile` 39, `group_profile` 15 |
| le pire trou restant après la pose des blocs de renvois | **3** (`budget_collecte`) |
| modules troués à 1 ou 2 décisions | **14 sur 15** |

En dessous de 5, le test crierait sur quatorze modules dont la gouvernance tient
en deux lignes qu'un `git grep` retrouve — et *un garde-fou qui crie pour rien
finit désactivé* (`docs/decisions/hook-diagnostic-sparse-checkout.md`). Au-dessus,
il laisserait passer `group_profile` à 15, c'est-à-dire le second cas réel.

5 laisse **deux décisions de marge** au pire module restant : la suite ne
rougira pas sur la prochaine décision écrite, mais elle rougira avant qu'un
module ne redevienne opaque. Le correctif attendu est un bloc de trois renvois
en tête du module, pas une exemption.

## Ce que ce test ne fait pas

Il ne vérifie pas que les décisions citées sont **les bonnes** — aucun test ne
peut le faire. `tests/test_index_decisions.py` vérifie qu'elles existent ; le
choix des deux ou trois qui comptent reste un acte de lecture.
"""

import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "scripts"))

import generer_decisions_par_module as generateur  # noqa: E402

#: Au-delà, un module qui ne cite aucune décision fait échouer la suite.
#: Le docstring ci-dessus porte les trois mesures qui l'ont fixé.
SEUIL_MODULE_TROUE = 5


@pytest.fixture(scope="module")
def analyse():
    return generateur.analyser()


def test_le_corpus_analyse_nest_pas_vide(analyse):
    """Garde-fou du garde-fou : `docs/` ou `src/` hors du sparse-checkout de
    `tests.yml` rendrait tous les autres tests de ce fichier vrais par vacuité,
    en CI seulement — le piège que `tests/conftest.py` diagnostique."""
    assert len(analyse) > 50, (
        f"{len(analyse)} module(s) trouvé(s) sous src/ — le répertoire est absent "
        "ou vide.")
    gouvernes = sum(1 for fiche in analyse.values() if fiche["gouvernent"])
    assert gouvernes > 20, (
        f"{gouvernes} module(s) gouverné(s) par au moins une décision. Soit "
        "docs/decisions/ est absent du disque, soit le critère ne reconnaît plus "
        "rien — dans les deux cas le seuil ci-dessous ne protège plus personne.")


def test_la_table_inversee_est_a_jour(analyse):
    """Générée, jamais tenue à la main : une table manuelle diverge."""
    attendu = generateur.rendre(analyse)
    assert generateur.SORTIE.exists(), (
        f"{generateur.SORTIE.relative_to(RACINE)} est absent — le générer avec "
        "`python3 scripts/generer_decisions_par_module.py`.")
    assert generateur.SORTIE.read_text(encoding="utf-8") == attendu, (
        f"{generateur.SORTIE.relative_to(RACINE)} a dérivé du dépôt. Ce fichier "
        "est généré : relancer `python3 scripts/generer_decisions_par_module.py` "
        "plutôt que de l'éditer.")


def test_aucun_module_lourdement_gouverne_ne_cite_zero_decision(analyse):
    troues = {
        nom: len(fiche["gouvernent"])
        for nom, fiche in analyse.items()
        if not fiche["cite"] and len(fiche["gouvernent"]) >= SEUIL_MODULE_TROUE
    }
    detail = "\n  ".join(
        f"src/{nom}.py — {compte} décisions le gouvernent, il n'en cite aucune"
        for nom, compte in sorted(troues.items(), key=lambda kv: (-kv[1], kv[0])))
    assert not troues, (
        f"un module qu'au moins {SEUIL_MODULE_TROUE} décisions gouvernent doit "
        "porter, en tête, un bloc nommant les deux ou trois qui comptent — pas la "
        "liste entière, qui ne se lit pas :\n  " + detail +
        "\n\nLesquelles retenir : `docs/decisions-par-module.md`, section du module.")


def test_le_critere_gouverne_distingue_le_fichier_du_symbole(tmp_path):
    """Le cœur du critère, éprouvé sur un corpus minuscule.

    Sans ce test, un `symboles_nommes` qui ne reconnaîtrait plus rien rendrait
    les deux tests ci-dessus verts par vacuité — et un `symboles_nommes` qui
    reconnaîtrait tout les rendrait ininterprétables.
    """
    module = tmp_path / "fusion_bidon.py"
    module.write_text(
        "SEUIL_BIDON = 3\n"
        "def fusionner_les_blocs(a, b):\n"
        "    def interne_bidon():\n"
        "        return None\n"
        "    return a\n",
        encoding="utf-8")
    symboles = generateur.symboles_de_tete(module)
    assert symboles == {"SEUIL_BIDON", "fusionner_les_blocs"}, (
        "seuls les symboles de tête comptent — pas les fonctions imbriquées, pas "
        "le module lui-même")

    index = {s: {"fusion_bidon"} for s in symboles}

    def nommes(texte):
        return generateur.symboles_nommes(texte, "fusion_bidon", symboles, index)

    assert nommes("La règle vit dans `fusion_bidon.py`, et rien d'autre.") == set(), (
        "nommer le fichier n'est pas nommer un contrat : c'est une mention")
    assert nommes("`fusion_bidon.fusionner_les_blocs` compose clé par clé.") == {
        "fusionner_les_blocs"}, "la forme qualifiée gouverne"
    assert nommes("Le repli passe par `SEUIL_BIDON`.") == {"SEUIL_BIDON"}, (
        "la forme nue entre dos d'accent gouverne, le symbole étant unique")
    assert nommes("On fusionner_les_blocs sans accent, en prose.") == set(), (
        "hors dos d'accent, la forme nue est une coïncidence de prose")

    partage = {s: {"fusion_bidon", "autre_module"} for s in symboles}
    assert generateur.symboles_nommes(
        "Le repli passe par `SEUIL_BIDON`.", "fusion_bidon", symboles, partage) == set(), (
        "un symbole défini dans deux modules ne désigne personne sous sa forme nue")
