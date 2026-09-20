#!/usr/bin/env python3
"""#659 — la civilité et la nomenclature PCS de l'INSEE atteignent le pivot.

Deux champs qu'AMO30 renseigne et que le pipeline traversait sans rien en
garder : `etatCivil.ident.civ`, lu par l'index d'identité depuis #556 et perdu à
l'assemblage du profil brut, et `profession.socProcINSEE`, jamais lu du tout.

Ces tests tournent sur `tests/fixtures/amo30_civilite_pcs_659.zip`, une
**réduction verbatim** de
`AMO30_tous_acteurs_tous_mandats_tous_organes_historique.json.zip` — huit fiches
acteur copiées octet pour octet, aucune écrite à la main. La raison est celle de
`docs/decisions/syceron-archives-verifiees-parseur-510.md` : la question qui
ouvre l'issue est factuelle — *que publie réellement la source, et sous quelle
forme ?* —, et une fixture inventée y répondrait par construction.

Les huit acteurs portent chacun un cas que la propagation devait traiter :

| Acteur | Ce qu'il porte |
| --- | --- |
| `PA1198` (Laurence Dumont) | `Mme` + famille « Cadres et professions intellectuelles supérieures », catégorie à **double espace** dans la source |
| `PA1037` (Robert del Picchia) | `M.` + le marqueur `xsi:nil` **aux deux niveaux** : non classé |
| `PA1019` (Isabelle Debré) | famille « Sans profession déclarée », qui est une VALEUR de la nomenclature — pas un `nil` |
| `PA794778` (Sandra Regol) | `libelleCourant` = `"(85) - Personne diverse sans activité professionnelle…"`, que #641 refuse de publier, pendant que la nomenclature dit « Sans profession déclarée » |
| `PA1308` (Jean-Jacques Filleul) | « Professions **I**ntermédiaires » |
| `PA335612` (Jean-Paul Lecoq) | « Professions **i**ntermédiaires » — la variante typographique |
| `PA1062` (Patrick Delnatte) | « Artisans, commerçants **et** chefs d'entreprise » |
| `PA1327` (Nicolas Forissier) | « Artisans, commerçants, chefs d'entreprise**s** » — l'autre variante |

Aucun test ici ne lit `pivot_data/` ni `raw_data/profiles/`, et aucun ne sort
sur le réseau : la fixture est copiée dans le cache disque, que
`_ensure_acteurs_historique_zip_downloaded` trouve déjà rempli (AGENTS.md §3b).
"""

import json
import shutil
import sys
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import candidate_profile  # noqa: E402
import schema_pivot  # noqa: E402
from candidate_profile import (  # noqa: E402
    _build_acteur_identite_index,
    _profession_an,
    _socproc_insee_an,
    build_profile,
)
from normalize_profil import normalize_profil  # noqa: E402
from schema_pivot import (  # noqa: E402
    CHAMPS_IDENTITE_TEXTE_LIBRE,
    make_empty_profil,
    validate_profil,
)

ARCHIVE = Path(__file__).resolve().parent / "fixtures" / "amo30_civilite_pcs_659.zip"

#: Le marqueur d'absence que le convertisseur XML → JSON d'AMO30 rend pour tout
#: élément déclaré vide (#556). Recopié tel quel de la fixture.
MARQUEUR_NIL = {
    "@xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "@xsi:nil": "true",
}


@pytest.fixture
def cache_amo30(tmp_path):
    """Le cache disque, garni de la réduction verbatim : aucun téléchargement."""
    shutil.copy(ARCHIVE, tmp_path / "acteurs_historique.zip")
    with patch("candidate_profile.ACTEURS_HISTORIQUE_CACHE_DIR", tmp_path):
        yield tmp_path


def _acteur(acteur_ref: str) -> dict:
    with zipfile.ZipFile(ARCHIVE) as zf:
        return json.loads(zf.read(f"json/acteur/{acteur_ref}.json"))["acteur"]


# ---------------------------------------------------------------------------
# 1. Le verdict factuel : ce que la source publie vraiment
# ---------------------------------------------------------------------------

def test_amo30_porte_la_civilite_de_chaque_acteur():
    """La civilité vient de l'état civil, et de nulle part ailleurs.

    Mesure du 31/08/2026 sur l'archive entière : **3 117 fiches sur 3 117**
    renseignent `etatCivil.ident.civ`, avec deux valeurs — « M. » 2 106 et
    « Mme » 1 011. Aucune fiche ne porte le marqueur `xsi:nil` sur ce champ.
    """
    with zipfile.ZipFile(ARCHIVE) as zf:
        refs = [Path(n).stem for n in zf.namelist() if n.startswith("json/acteur/")]
    civilites = {r: _acteur(r)["etatCivil"]["ident"]["civ"] for r in refs}
    assert set(civilites.values()) == {"M.", "Mme"}
    assert civilites["PA1198"] == "Mme"
    assert civilites["PA1037"] == "M."


def test_amo30_porte_les_deux_niveaux_de_la_nomenclature_insee():
    """`socProcINSEE` a exactement deux clés, et la source les remplit toutes
    les deux ou aucune.

    Mesure du 31/08/2026 : les 3 117 fiches portent le bloc, avec les mêmes deux
    clés ; 2 177 portent un couple de libellés (70 %), 940 portent le marqueur
    aux **deux** niveaux à la fois. Aucune n'en renseigne un sans l'autre — ce
    qui est ce qui autorise à publier `null` des deux côtés ensemble.
    """
    assert set(_acteur("PA1198")["profession"]["socProcINSEE"]) == {
        "famSocPro",
        "catSocPro",
    }
    classe = _acteur("PA1198")["profession"]["socProcINSEE"]
    assert classe["famSocPro"] == "Cadres et professions intellectuelles supérieures"

    non_classe = _acteur("PA1037")["profession"]["socProcINSEE"]
    assert non_classe["famSocPro"] == MARQUEUR_NIL
    assert non_classe["catSocPro"] == MARQUEUR_NIL


def test_les_variantes_typographiques_sont_dans_la_source():
    """Deux libellés d'une même famille, et la source écrit les deux.

    Mesure du 31/08/2026 : « Professions Intermédiaires » 107 fiches et
    « Professions intermédiaires » 58 ; « Artisans, commerçants et chefs
    d'entreprise » 125 et « Artisans, commerçants, chefs d'entreprises » 47.
    Le fait est ici pour que personne n'ait à le redécouvrir en agrégeant.
    """
    famille = lambda ref: _acteur(ref)["profession"]["socProcINSEE"]["famSocPro"]
    assert famille("PA1308") == "Professions Intermédiaires"
    assert famille("PA335612") == "Professions intermédiaires"
    assert famille("PA1062") == "Artisans, commerçants et chefs d'entreprise"
    assert famille("PA1327") == "Artisans, commerçants, chefs d'entreprises"


# ---------------------------------------------------------------------------
# 2. La lecture : le marqueur ne survit pas, la nomenclature oui
# ---------------------------------------------------------------------------

def test_le_marqueur_nil_est_lu_comme_une_absence_aux_deux_niveaux():
    assert _socproc_insee_an(_acteur("PA1037")["profession"]) == (None, None)


def test_un_bloc_socproc_absent_ne_fabrique_rien():
    """Une fiche sans le bloc rend `(None, None)`, pas une exception ni un
    libellé par défaut (§2 règle 5)."""
    assert _socproc_insee_an({}) == (None, None)
    assert _socproc_insee_an(None) == (None, None)
    assert _socproc_insee_an({"socProcINSEE": "Employés"}) == (None, None)


def test_non_classe_et_sans_profession_declaree_restent_deux_faits_distincts():
    """La réserve n°1 de l'issue, verrouillée sur deux acteurs réels.

    940 fiches sur 3 117 ne sont pas classées ; 85 le sont dans la famille
    « Sans profession déclarée », qui est une valeur de la nomenclature. Les
    confondre publierait « cette personne n'a pas déclaré de profession » là où
    la source dit seulement qu'elle ne l'a pas classée — le contresens exact de
    #556.
    """
    assert _socproc_insee_an(_acteur("PA1037")["profession"])[0] is None
    assert (
        _socproc_insee_an(_acteur("PA1019")["profession"])[0]
        == "Sans profession déclarée"
    )


def test_la_nomenclature_dit_ce_que_le_texte_libre_ne_pouvait_pas_dire():
    """La réserve n°3, sur l'acteur qui porte les deux formes à la fois.

    `PA794778` publie en `libelleCourant` un code brut dont #641 a montré qu'il
    n'est pas une profession mais l'énoncé d'une absence : `_profession_an` le
    refuse, et le profil dit « profession non renseignée ». La nomenclature,
    elle, la classe — et c'est *elle* qui porte l'information, sans qu'on ait eu
    à la deviner dans une phrase.
    """
    profession = _acteur("PA794778")["profession"]
    assert profession["libelleCourant"].startswith("(85) - Personne diverse sans")
    assert _profession_an(profession["libelleCourant"]) is None
    assert _socproc_insee_an(profession) == (
        "Sans profession déclarée",
        "Sans profession déclarée",
    )


def test_les_libelles_sont_publies_verbatim_sans_rapprochement():
    """Aucune normalisation à la lecture : deux libellés distincts le restent.

    Regrouper est l'affaire de qui agrège (`group_profile.py`, hors de ce lot),
    et un regroupement purement typographique — casse et ponctuation, sur le
    modèle de `gouvernement_roster._normalise_fonction` — n'a pas sa place dans
    un fait individuel publié. Ce test échoue si la lecture se met à harmoniser.
    """
    assert _socproc_insee_an(_acteur("PA1308")["profession"])[0] == (
        "Professions Intermédiaires"
    )
    assert _socproc_insee_an(_acteur("PA335612")["profession"])[0] == (
        "Professions intermédiaires"
    )
    # Le double espace de la source survit lui aussi : il n'est pas à nous de
    # décider qu'il est de trop.
    assert "et  artistiques" in _socproc_insee_an(_acteur("PA1198")["profession"])[1]


# ---------------------------------------------------------------------------
# 3. L'index d'identité
# ---------------------------------------------------------------------------

def test_l_index_d_identite_porte_les_trois_champs(cache_amo30):
    index = _build_acteur_identite_index()
    assert index["PA1198"]["civilite"] == "Mme"
    assert index["PA1198"]["famille_socioprofessionnelle"] == (
        "Cadres et professions intellectuelles supérieures"
    )
    assert index["PA1037"]["civilite"] == "M."
    assert index["PA1037"]["famille_socioprofessionnelle"] is None
    assert index["PA1037"]["categorie_socioprofessionnelle"] is None


def test_l_index_versionne_ignore_le_fichier_de_la_version_precedente(cache_amo30):
    """Le contenu écrit change, donc le nom du fichier change (#556).

    Sans ce changement de nom, le cache disque — restauré d'un run à l'autre par
    le cache GitHub Actions (#550/#555) — rendrait l'index d'avant : les deux
    nouveaux champs seraient absents et le code qui les lit ne s'exécuterait
    jamais. C'est le piège exact que #556 a documenté en versionnant ces index.
    """
    (cache_amo30 / "index_identite_v3.json").write_text(
        json.dumps({"PA1198": {"nom_complet": "index périmé"}}), encoding="utf-8"
    )
    index = _build_acteur_identite_index()
    assert index["PA1198"]["nom_complet"] != "index périmé"
    assert "famille_socioprofessionnelle" in index["PA1198"]


# ---------------------------------------------------------------------------
# 4. Le profil brut, puis le pivot
# ---------------------------------------------------------------------------

def _build_profile_sans_reseau(identite_an, acteur_ref):
    with (
        patch("candidate_profile.time.sleep", return_value=None),
        patch("candidate_profile.fetch_identite_officielle_par_slug",
              return_value=(identite_an, acteur_ref)),
        patch("candidate_profile._extract_mandats_officiels", return_value=[]),
        patch("candidate_profile.fetch_positions_hemicycle_officielles", return_value=[]),
        patch("candidate_profile.fetch_votes_officiels", return_value=([], [])),
        patch("candidate_profile.fetch_amendements_officiels", return_value=[]),
        patch("candidate_profile.fetch_textes_portes_officiels", return_value=[]),
        patch("candidate_profile.fetch_interventions_syceron", return_value=[]),
        patch("candidate_profile.fetch_questions_officielles", return_value=[]),
    ):
        return build_profile("deputes", "laurence-dumont")


def test_le_profil_brut_transmet_les_trois_champs(cache_amo30):
    """Le défaut de départ : `civilite` était dans l'index et s'arrêtait là."""
    identite_an = _build_acteur_identite_index()["PA1198"]
    profil = _build_profile_sans_reseau(identite_an, "PA1198")
    assert profil["identite"]["civilite"] == "Mme"
    assert profil["identite"]["famille_socioprofessionnelle"] == (
        "Cadres et professions intellectuelles supérieures"
    )
    assert profil["identite"]["categorie_socioprofessionnelle"].startswith(
        "Cadres de la fonction publique"
    )


def test_le_pivot_publie_les_trois_champs(cache_amo30):
    identite_an = _build_acteur_identite_index()["PA1198"]
    brut = _build_profile_sans_reseau(identite_an, "PA1198")
    pivot = normalize_profil(brut)
    assert pivot["identite"]["civilite"] == "Mme"
    assert pivot["identite"]["famille_socioprofessionnelle"] == (
        "Cadres et professions intellectuelles supérieures"
    )
    assert validate_profil(pivot) == []


def test_un_acteur_non_classe_publie_null_et_garde_sa_civilite(cache_amo30):
    identite_an = _build_acteur_identite_index()["PA1037"]
    pivot = normalize_profil(_build_profile_sans_reseau(identite_an, "PA1037"))
    assert pivot["identite"]["civilite"] == "M."
    assert pivot["identite"]["famille_socioprofessionnelle"] is None
    assert pivot["identite"]["categorie_socioprofessionnelle"] is None


def test_un_profil_brut_d_avant_le_lot_ne_regresse_pas(cache_amo30):
    """Un profil collecté avant #659 n'a pas les clés : le pivot publie `null`,
    pas une exception ni une valeur inventée.

    Ce que la fusion en fait ensuite est écrit ailleurs et compte ici : un
    scalaire ne régresse jamais vers `null`
    (`docs/decisions/collecte-vide-necrase-jamais.md`). Une fois la valeur
    publiée, le silence d'une source ne la retire pas — c'est aussi pour ça que
    le marqueur doit être arrêté à la LECTURE et jamais publié une seule fois.
    """
    pivot = normalize_profil({
        "slug": "sans-civilite",
        "chambre": "deputes",
        "identite": {"profession": "Avocat", "date_naissance": "1951-08-19"},
    })
    assert pivot["identite"]["civilite"] is None
    assert pivot["identite"]["famille_socioprofessionnelle"] is None
    assert validate_profil(pivot) == []


# ---------------------------------------------------------------------------
# 5. Le contrôle de forme, côté publié
# ---------------------------------------------------------------------------

def test_validate_profil_refuse_le_marqueur_sur_chaque_champ_d_identite():
    """`audit_diff_profils` ne compare que la PRÉSENCE du bloc `identite` : une
    clé ajoutée, retirée ou changée ne déclenche rien (#649). Le seul contrôle
    qui puisse voir passer le marqueur est celui-ci."""
    for champ in CHAMPS_IDENTITE_TEXTE_LIBRE:
        profil = make_empty_profil("x", "X")
        profil["identite"] = {champ: MARQUEUR_NIL}
        erreurs = validate_profil(profil)
        assert any(f"identite.{champ}" in e for e in erreurs), champ


def test_les_trois_champs_du_lot_sont_sous_controle():
    assert {
        "civilite",
        "famille_socioprofessionnelle",
        "categorie_socioprofessionnelle",
    } <= set(CHAMPS_IDENTITE_TEXTE_LIBRE)


def test_le_schema_decrit_les_trois_champs():
    """AGENTS.md §4 et le schéma doivent dire la même chose que le code."""
    docstring = schema_pivot.__doc__ or ""
    for champ in (
        "civilite",
        "famille_socioprofessionnelle",
        "categorie_socioprofessionnelle",
    ):
        assert champ in docstring, champ
