"""La seconde déclaration lisait un champ que le corpus ne porte pas (#788).

#781 a posé la seconde déclaration à la place du pivot en écrivant qu'elle
devait être **symétrique** de celle de l'écriture du brut. Elle ne l'était pas :

| Place | Ce qu'elle passait |
| --- | --- |
| écriture du brut | `nom`, venu de `raw_data/candidats.json` |
| normalisation pivot | `profile.get("nom")`, sur le profil **brut** |

**Aucun profil brut ne porte de champ `nom`** — le nom y vit sous
`identite.nom_complet`. La branche rendait donc `False` à tous les coups, et la
seconde déclaration n'a jamais pu être vraie : le run `34264027824` a écrit les
cinq profils bruts, aucun pivot, sur un fichier de résolutions correct.

**Pourquoi les tests de #781 ne l'ont pas vu, et ce que ceux-ci font
différemment.** Ils lisent le *source* — ils vérifient que la fonction cite
`declare_hors_an_par_identifiant`, jamais qu'elle publie quoi que ce soit. Un
test de source ne peut pas voir qu'un champ lu n'existe pas. Ceux-ci **font
tourner** la fonction, sur un brut à la **forme du corpus** : pas de `nom`, un
`identite.nom_complet`. C'est la leçon de #726 — *une fixture décrivant le monde
tel que le code l'imagine ne peut pas révéler que le monde a bougé.*
"""

import json
import re
import sys
from pathlib import Path

import pytest

@pytest.fixture(autouse=True)
def _cache_amo30_isole(tmp_path_factory, monkeypatch):
    """Le cache AMO30 de ce fichier est un répertoire jetable, jamais celui du poste (#767).

    `nb_acteurs_referentiel_charge()` lit `ACTEURS_HISTORIQUE_CACHE_DIR /
    index_identite…`, un chemin **relatif au répertoire courant**. Sur une
    machine où une collecte a tourné, ces tests constataient donc le référentiel
    réel : « jamais élu·e à l'Assemblée » devenait dérivable, et douze d'entre
    eux basculaient. Verts en CI — dont le checkout est vide — et rouges chez la
    propriétaire, au moment précis où elle vérifie qu'elle n'a rien cassé.

    Le garde-fou de #721 le **diagnostiquait** déjà (`CacheDuPosteLuDansUnTest`)
    sans le corriger : il montre qui n'applique pas l'idiome, il ne l'applique
    pas à leur place.

    Le mémo de module est vidé aux deux bouts : rempli par un test voisin, il
    rendrait le vrai référentiel sans jamais rouvrir un fichier — donc sans que
    le garde-fou puisse le voir. C'est un `dict` partagé, pas un `lru_cache` :
    il se vide en place.
    """
    import candidate_profile

    candidate_profile._ACTEURS_HISTORIQUE_INDEX_MEMO.clear()
    monkeypatch.setattr(
        candidate_profile,
        "ACTEURS_HISTORIQUE_CACHE_DIR",
        tmp_path_factory.mktemp("cache_amo30_absent"),
    )
    yield
    candidate_profile._ACTEURS_HISTORIQUE_INDEX_MEMO.clear()

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

import generate_all_profiles as generate  # noqa: E402
import perimetre_candidats as perimetre  # noqa: E402

#: Ce fichier de tests lit la configuration committée nommée ci-dessous.
#: Le garde-fou de `conftest.py` refuse tout `.json` de `raw_data/` qu'un
#: test n'a pas déclaré (#791), et n'accepte la déclaration que si le chemin
#: est dans le `sparse-checkout` de `tests.yml` — sinon le test ne tournerait
#: qu'en local, sur ce qu'un run y a laissé.
pytestmark = pytest.mark.lit_reference_committee("raw_data/groupes_reels.json")


@pytest.fixture(autouse=True)
def _memo_propre():
    perimetre.vider_memo_resolutions()
    yield
    perimetre.vider_memo_resolutions()


@pytest.fixture(autouse=True)
def _table_neutre(monkeypatch):
    """Aucune entrée de correspondance : la SECONDE déclaration, seule.

    Sans ce neutre, ces tests lisaient `raw_data/correspondance_acteurs_an.json`
    — le corpus vivant, ce que la règle de #473 interdit. Ils sont passés le
    jour de leur écriture et ont échoué le lendemain, quand le run
    `34278343461` a écrit l'entrée sourcée d'Asselineau : la PREMIÈRE
    déclaration suffisait alors, et trois tests censés vérifier la seconde
    passaient sans elle.

    Ils sont même restés **verts en CI**, dont le sparse-checkout ne
    matérialise pas ce fichier : vert là-bas, rouge ici, pour la même raison
    que #721 — un test qui lit l'état d'un poste ne teste pas ce qu'il croit.
    """
    monkeypatch.setattr(generate, "_entree_correspondance", lambda slug: None)


def _resolutions(tmp_path: Path, **issues) -> Path:
    chemin = tmp_path / "resolutions.json"
    chemin.write_text(
        json.dumps({"resolutions": {nom.replace("_", " "): {"issue": issue}
                                    for nom, issue in issues.items()}}),
        encoding="utf-8",
    )
    return chemin


def _brut_a_la_forme_du_corpus(nom_complet: str) -> dict:
    """Un profil brut tel que la collecte l'écrit — **sans champ `nom`**.

    C'est le seul point de ce fichier qui compte : la fixture ne décrit pas ce
    que le code attend, elle décrit ce que `raw_data/profiles/*.json` contient.
    """
    return {
        "slug": "francois-asselineau",
        "chambre": None,
        "source": "https://fr.wikipedia.org/wiki/Fran%C3%A7ois_Asselineau",
        "identite": {"nom_complet": nom_complet, "groupe_sigle": None},
        "mandats": [],
        "votes": [],
        "interventions": [],
        "meta": {"warnings": ["aucun mandat français connu"]},
    }


def _pivoter(profile, nom, resolutions):
    return generate._normaliser_en_pivot(
        profile,
        None,
        nom=nom,
        effective_slug="francois-asselineau",
        parti="UPR",
        provenance="candidat_declare",
        chambre=None,
        resolutions=str(resolutions),
        scrutins_index=None,
    )


# ---------------------------------------------------------------------------
# Le comportement, sur la forme réelle du corpus
# ---------------------------------------------------------------------------


def test_un_brut_sans_champ_nom_devient_un_pivot(tmp_path):
    """Le défaut, en une ligne : c'est ce cas qui rendait `None`."""
    resolutions = _resolutions(tmp_path, François_Asselineau="hors_an")
    pivot = _pivoter(
        _brut_a_la_forme_du_corpus("François Asselineau"),
        "François Asselineau",
        resolutions,
    )
    assert pivot is not None, (
        "un candidat déclaré sans mandat AN, déclaré tel par un identifiant "
        "externe, doit recevoir un pivot — sinon c'est un « collecté mais non "
        "publié » (#511)"
    )


def test_le_nom_ne_vient_pas_du_brut(tmp_path):
    """Même brut, même résolution, un nom d'appelant qui ne correspond pas.

    Contre-épreuve du test précédent : s'il passait en lisant le brut, celui-ci
    passerait aussi, et la paire ne dirait plus rien.
    """
    resolutions = _resolutions(tmp_path, François_Asselineau="hors_an")
    pivot = _pivoter(
        _brut_a_la_forme_du_corpus("François Asselineau"),
        "Quelqu'un d'autre",
        resolutions,
    )
    assert pivot is None


def test_indetermine_ne_publie_toujours_pas(tmp_path):
    """La garde de #757, vérifiée en exécution et non plus par une regex.

    « Wikidata ne décrit pas cette personne » et « Wikidata la décrit et ne lui
    connaît aucun mandat AN » sont deux affirmations différentes.
    """
    resolutions = _resolutions(tmp_path, Manolo_Mlekuz="indetermine")
    pivot = _pivoter(
        _brut_a_la_forme_du_corpus("Manolo Mlekuz"), "Manolo Mlekuz", resolutions
    )
    assert pivot is None


def test_un_fichier_de_resolutions_absent_ne_publie_pas(tmp_path):
    """L'absence de preuve n'est pas une preuve d'absence : le comportement
    d'avant s'applique, il ne se durcit pas."""
    pivot = _pivoter(
        _brut_a_la_forme_du_corpus("François Asselineau"),
        "François Asselineau",
        tmp_path / "jamais-ecrit.json",
    )
    assert pivot is None


# ---------------------------------------------------------------------------
# La symétrie, cette fois vérifiable
# ---------------------------------------------------------------------------


def _source_generate() -> str:
    """Le code seul : les rationales de ce dépôt citent ce qu'elles expliquent,
    et celle de #788 nomme le champ fautif mot pour mot."""
    texte = (RACINE / "src" / "generate_all_profiles.py").read_text(encoding="utf-8")
    return "\n".join(l for l in texte.split("\n") if not l.lstrip().startswith("#"))


def test_le_brut_nest_plus_interroge_sur_son_nom():
    """`profile.get("nom")` est le champ absent : il ne doit pas revenir."""
    src = _source_generate()
    assert 'profile.get("nom")' not in src, (
        "aucun profil brut ne porte de champ `nom` — le lire rend `None` sans "
        "que rien ne le dise (#788)"
    )


def test_les_deux_appelants_passent_le_nom_du_candidat():
    """La symétrie que #781 décrivait, désormais tenue par les appels."""
    src = _source_generate()
    appels = re.findall(
        r"pivot_profile = _normaliser_en_pivot\(\n(.*?)\n        \)", src, re.DOTALL
    )
    assert len(appels) == 2, f"deux appels attendus, {len(appels)} trouvés"
    for appel in appels:
        assert "nom=nom" in appel, (
            "un appel ne transmet pas le nom du candidat : la place du pivot "
            "retomberait sur un nom vide"
        )
