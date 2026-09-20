"""Une candidature déclinée n'a plus de fiche dans l'interface (#761).

#760 l'a sortie du périmètre de **collecte** ; ses données ont donc cessé d'être
rafraîchies pendant que sa fiche restait en ligne — le pire des deux états. Ce
lot la sort de l'**interface**.

Le test qui compte est celui de **parité** : `STATUTS_MASQUES` (JS) et
`STATUTS_GELES` (Python) disent la même chose, et rien dans le langage ne les
oblige à rester d'accord. Même patron que la table de sorts de #743, le premier
test du dépôt à confronter un `frozenset` Python à une table JS.
"""

import re
from pathlib import Path

import pytest

import perimetre_candidats as perimetre

RACINE = Path(__file__).resolve().parents[1]
SYNC = RACINE / "web" / "UI_finale" / "scripts" / "sync-data.mjs"


def _sans_commentaires(source: str) -> str:
    """Les commentaires de ce script citent le code qu'ils expliquent."""
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"(?<!:)//[^\n]*", "", source)


@pytest.fixture(scope="module")
def source() -> str:
    return SYNC.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def code(source) -> str:
    return _sans_commentaires(source)


def _statuts_masques_js(source: str) -> set[str]:
    bloc = re.search(r"STATUTS_MASQUES = new Set\(\[(.*?)\]\)", source, re.DOTALL)
    assert bloc, "`STATUTS_MASQUES` n'est plus déclaré dans sync-data.mjs"
    return set(re.findall(r"'([a-z0-9_]+)'", bloc.group(1)))


# ---------------------------------------------------------------------------
# La parité, qui est le sujet
# ---------------------------------------------------------------------------


def test_les_deux_langages_masquent_le_meme_ensemble(code):
    """« Ne plus collecter » et « ne plus afficher » disent la même chose ici.

    Les séparer devra être une décision écrite : un statut collecté mais masqué,
    ou l'inverse, est concevable — il n'est simplement pas décidé aujourd'hui.
    """
    assert _statuts_masques_js(code) == set(perimetre.STATUTS_GELES)


def test_lensemble_masque_nest_pas_vide(code):
    """Un ensemble vidé par mégarde republierait toutes les fiches déclinées
    sans qu'aucun test ne rougisse."""
    assert _statuts_masques_js(code) == {"decline"}


# ---------------------------------------------------------------------------
# Ce que le script en fait
# ---------------------------------------------------------------------------


def test_le_manifeste_exclut_les_statuts_masques(code):
    bloc = re.search(r"const manifestCandidates = candidats\s*\n\s*\.filter\(([^\n]*)\)", code)
    assert bloc, "le filtre du manifeste a changé de forme"
    assert "estMasque" in bloc.group(1), (
        "le manifeste ne filtre plus sur le statut : les fiches déclinées "
        "reviendraient dans l'onglet Candidats"
    )


def test_le_profil_masque_nest_pas_copie(code):
    assert "slugsMasques" in code
    bloc = re.search(r"for \(const file of profileFiles\) \{(.*?)\n\}", code, re.DOTALL)
    assert bloc, "la boucle de copie des profils a changé de forme"
    assert "slugsMasques.has" in bloc.group(1)


def test_un_profil_masque_laisse_par_une_execution_precedente_est_supprime(code):
    """Le script ne nettoie pas son dossier de sortie.

    Sans cette suppression, la fiche masquée resterait servie à son URL par le
    fichier qu'une exécution antérieure y avait copié — masquée du manifeste, et
    pourtant atteignable.
    """
    bloc = re.search(r"for \(const file of profileFiles\) \{(.*?)\n\}", code, re.DOTALL)
    assert "rmSync" in bloc.group(1)
    assert "existsSync" in bloc.group(1)


def test_les_slugs_disponibles_excluent_les_masques(code):
    """`availableSlugs` sert au filtre du manifeste ET au rattachement aux
    groupes : un masqué qui y resterait se verrait recoller des `groupIds`."""
    bloc = re.search(r"const availableSlugs = new Set\((.*?)\);", code, re.DOTALL)
    assert bloc, "`availableSlugs` a changé de forme"
    assert "slugsMasques" in bloc.group(1)


def test_les_fiches_masquees_sont_nommees_et_pas_seulement_comptees(code):
    """Une fiche retirée doit se distinguer d'une fiche qu'on a oublié de
    produire (#510)."""
    assert "fiche(s) masquée(s)" in code
    assert "[...slugsMasques].join" in code


# ---------------------------------------------------------------------------
# Ce que masquer ne fait pas
# ---------------------------------------------------------------------------


def test_le_script_ne_supprime_jamais_dans_pivot_data(code):
    """Masquer une fiche ne touche pas au corpus publié (#460/#470).

    Le `rmSync` du script ne vise que le dossier de SORTIE ; s'il visait
    `pivotProfilesDir`, il supprimerait un fichier publié — une disparition
    qu'`audit_diff_profils` bloque, découverte au commit plutôt qu'ici.
    """
    for appel in re.findall(r"rmSync\(([^)]*)\)", code):
        assert "pivotProfiles" not in appel and "pivot_data" not in appel, (
            f"rmSync vise le corpus publié : {appel}"
        )
    assert "rmSync(cible)" in code


def test_les_fiches_de_groupe_ne_passent_pas_par_cette_liste(code):
    """Masquer la fiche de CANDIDAT ne retire personne d'un agrégat de groupe :
    les fiches de groupe sont bâties sur leur propre `membres[]`."""
    bloc = re.search(r"for \(const membre of groupe\.membres \|\| \[\]\) \{(.*?)\n  \}", code, re.DOTALL)
    assert bloc, "le rattachement aux groupes a changé de forme"
    assert "slugsMasques" not in bloc.group(1), (
        "le masquage ne doit pas s'appliquer à la composition d'un groupe"
    )
