"""#689 — un projet de loi porté au nom du Gouvernement n'est pas une
production personnelle.

`textes_portes[]` publiait sous un unique `role: "auteur"` deux actes de nature
différente : la proposition de loi qu'un·e parlementaire dépose, et le projet de
loi qu'un membre du Gouvernement porte au nom de l'exécutif. Mesuré sur
`origin/main` le 01/09/2026 : **316 des 472 entrées publiées** sont des projets
de loi, dont **282 des 283 d'`edouard-philippe`**, toutes déposées pendant qu'il
était Premier ministre.

Ce que ces tests verrouillent, dans l'ordre du défaut :

1. **Le discriminant ne vient pas du libellé.** Le dossier CETA d'Édouard
   Philippe s'intitule « Accord économique et commercial global (CETA)… » : un
   filtre « commence par *Projet de loi* » n'en voit rien. Sa nature se lit dans
   le document déposé (`PRJLANR5L15B0868`).
2. **Un seul endroit lit l'archive** : `_origine`, dont dépendent les fiches de
   gouvernement, dérive de `nature_texte_depose` et rend le même verdict.
3. **La qualification traverse la fusion additive.** Sans
   `backfill_dossier_nature`, l'entrée ancienne gagne et le brut n'acquiert
   jamais le champ — le trou de #639 et de #492, au même endroit.
4. **Le rôle publié est dérivé, et ne peut pas contredire la nature.**

FIXTURES. Réductions verbatim des archives réelles
`.../{15,17}/loi/dossiers_legislatifs/…` (`tests/fixtures/dossiers_an/`), copiées
octet pour octet depuis le zip AN. Aucune valeur n'est inventée (leçon de #510).
"""

import json
import re
import sys
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import candidate_profile  # noqa: E402
import gouvernement_textes  # noqa: E402
from gouvernement_textes import nature_texte_depose  # noqa: E402
from merge_profile import backfill_dossier_nature, merge_raw_profile  # noqa: E402
from normalize_profil import _normalize_texte_porte  # noqa: E402
from schema_pivot import (  # noqa: E402
    KNOWN_NATURES_TEXTE,
    KNOWN_ROLES_TEXTE,
    ROLE_INITIATEUR_PAR_NATURE,
    make_empty_profil,
    validate_profil,
)

FIXTURES = Path(__file__).parent / "fixtures" / "dossiers_an"

#: Le dossier de l'issue : CETA, initié par Édouard Philippe (`PA345619`) le
#: 19/06/2019, alors qu'il était Premier ministre et sans mandat électif.
#: Document déposé : `PRJLANR5L15B0868`. Titre SANS préfixe de nature.
CETA = "DLR5L15N37607"
CETA_TITRE = ("Accord économique et commercial global (CETA) et accord de "
              "partenariat stratégique entre l'UE et le Canada")
PHILIPPE = "PA345619"

#: Une proposition de loi (document `PIONANR5L17B0558`).
PION = "DLR5L17N50879"

#: Une proposition de résolution art. 34-1 (document `PNRE…`).
PNRE = "DLR5L15N44127"

#: Le PLF 2027 : AUCUN acte de dépôt résolvable, donc repli sur
#: `procedureParlementaire.code == "3"` (« Projet de loi de finances »).
SANS_DOCUMENT = "DLR5L17N54629"


def _dossier(uid: str) -> dict:
    charge = json.loads((FIXTURES / f"dossier_{uid}.json").read_text(encoding="utf-8"))
    return charge["dossierParlementaire"]


# ---------------------------------------------------------------------------
# 1. La nature vient du document déposé, jamais du libellé
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("uid, attendu", [
    (CETA, "projet_de_loi"),
    (PION, "proposition_de_loi"),
    (PNRE, "proposition_de_resolution"),
    (SANS_DOCUMENT, "projet_de_loi"),
])
def test_la_nature_se_lit_dans_le_document_depose(uid, attendu):
    """`PRJL` / `PION` / `PNRE`, préfixe de l'uid du document du premier acte de
    dépôt — le type encodé par l'AN elle-même. Le repli sur
    `procedureParlementaire` ne sert qu'aux dossiers sans document résolvable."""
    assert nature_texte_depose(_dossier(uid)) == attendu
    assert nature_texte_depose(_dossier(uid)) in KNOWN_NATURES_TEXTE


def test_le_libelle_ne_dit_pas_la_nature():
    """Le piège de #689, sur le dossier qui l'a révélé : un discriminant tiré du
    libellé manque 283 des 304 textes portés hors mandat électif. Une clé dérivée
    d'un libellé rouille, et se tait en rouillant (#672)."""
    dossier = _dossier(CETA)
    titre = (dossier.get("titreDossier") or {}).get("titre")
    assert titre == CETA_TITRE
    assert not titre.lower().startswith("projet de loi")
    assert nature_texte_depose(dossier) == "projet_de_loi"


def test_une_nature_inconnue_reste_nulle():
    """Un dossier sans document de dépôt ET dont le code de procédure n'est pas
    univoque n'est pas rangé d'office : `None`, jamais une valeur par défaut
    (AGENTS.md §2 règle 5)."""
    dossier = _dossier(SANS_DOCUMENT)
    dossier["procedureParlementaire"] = {"code": "5", "libelle": "Projet ou proposition"}
    assert nature_texte_depose(dossier) is None
    assert nature_texte_depose({"actesLegislatifs": None}) is None


# ---------------------------------------------------------------------------
# 2. Un seul endroit lit l'archive : `_origine` en dérive
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("uid, attendu", [
    (CETA, "gouvernemental"),
    (PION, "parlementaire"),
    (PNRE, None),
])
def test_l_origine_des_fiches_de_gouvernement_est_inchangee(uid, attendu):
    """#435/#400 lisaient déjà ce champ pour les fiches de gouvernement.
    `_origine` en dérive désormais au lieu de le relire : deux lectures du même
    champ auraient fini par diverger. Verdict identique sur les 10 674 dossiers
    des trois archives (relevé du 01/09/2026)."""
    assert gouvernement_textes._origine(_dossier(uid)) == attendu


# ---------------------------------------------------------------------------
# 3. La collecte écrit la nature — et le cache ne peut pas la contourner
# ---------------------------------------------------------------------------

def _archive(chemin: Path, uids: list[str]) -> Path:
    with zipfile.ZipFile(chemin, "w") as zf:
        for uid in uids:
            zf.writestr(
                f"json/dossierParlementaire/{uid}.json",
                (FIXTURES / f"dossier_{uid}.json").read_bytes(),
            )
    return chemin


def test_l_index_des_textes_portes_porte_la_nature(tmp_path):
    """`_build_acteur_textes_portes_index` lit la MÊME archive que les fiches de
    gouvernement : l'information n'était pas perdue à la source, elle était jetée
    à la collecte."""
    archive = _archive(tmp_path / "dossiers_15.zip", [CETA, PNRE])
    with patch("candidate_profile.DOSSIERS_CACHE_DIR", tmp_path / "cache"), \
         patch("candidate_profile.ensure_dossiers_zips_downloaded",
               return_value=[(15, archive)]):
        index = candidate_profile._build_acteur_textes_portes_index()

    entree = next(t for t in index[PHILIPPE] if t["id"] == CETA)
    assert entree["role"] == "auteur", "le rôle brut reste celui de la source"
    assert entree["nature_texte"] == "projet_de_loi"


def test_le_cache_disque_change_de_version():
    """Un index construit avant #689 ne porte pas `nature_texte` : le relire
    republierait « auteur » sur les 316 projets de loi du corpus sans qu'aucune
    étape n'échoue. L'existence d'un cache n'est pas la preuve de sa conformité
    (même règle que pour les amendements #440 et les scrutins #639).

    **`_v4` depuis #997**, et la démonstration a été faite en vrai : le run
    35324142500 portait le correctif du stade et a republié les 21
    `examine_commission` de Marine Le Pen **à l'identique**, parce que
    `.cache/dossiers_an` restaure l'index de la semaine précédente
    (`restore-keys: public-data-cache-dossiers-`). Le `stade` est calculé par
    `_collect_acteur_roles` **au moment de construire l'index**, donc il y est
    figé.

    **`_v5` depuis #1019** : l'archive XIV entre dans la couverture, donc
    l'index gagne 3 402 dossiers. Quatrième incrément, même règle — un cache
    porte le code ET les sources qui l'ont écrit.

    Aucune version antérieure ne doit subsister dans le source.
    """
    source = Path(candidate_profile.__file__).read_text(encoding="utf-8")
    assert "index_acteur_textes_v5.json" in source
    for perimee in ("v4", "v3", "v2"):
        assert f"index_acteur_textes_{perimee}.json" not in source


# ---------------------------------------------------------------------------
# 4. La qualification traverse la fusion additive
# ---------------------------------------------------------------------------

def _dossier_brut(uid: str, **extra) -> dict:
    """Réduction verbatim d'une entrée `dossiers_legislatifs[]` publiée."""
    base = {
        "id": uid,
        "titre": CETA_TITRE,
        "role": "auteur",
        "type_rapport": None,
        "stade_procedural": "adopte",
        "date_min": "2019-06-19",
        "date_max": "2024-03-21",
        "legislature": "15",
        "source_url": "https://www.assemblee-nationale.fr/dyn/15/dossiers/"
                      "aecg_partenariat_strategique_ue-canada",
    }
    base.update(extra)
    return base


def _cle(d: dict):
    return (d.get("legislature"), d.get("id"))


def test_le_report_remplit_le_champ_absent():
    ancien = [_dossier_brut(CETA)]
    neuf = [_dossier_brut(CETA, nature_texte="projet_de_loi")]
    (resultat,) = backfill_dossier_nature(ancien, neuf, _cle)
    assert resultat["nature_texte"] == "projet_de_loi"


def test_le_report_n_ecrase_rien_et_ne_cree_rien():
    """Strictement croissant en information : ne touche aucun autre champ, ne
    crée aucune entrée, n'écrase pas une nature déjà posée."""
    ancien = [_dossier_brut(CETA, nature_texte="proposition_de_loi", stade_procedural="depose")]
    neuf = [_dossier_brut(CETA, nature_texte="projet_de_loi"),
            _dossier_brut("DLR5L15N00000", nature_texte="projet_de_loi")]
    resultat = backfill_dossier_nature(ancien, neuf, _cle)
    assert len(resultat) == 1
    assert resultat[0]["nature_texte"] == "proposition_de_loi"
    assert resultat[0]["stade_procedural"] == "depose"


def test_la_fusion_du_brut_requalifie_une_entree_deja_collectee():
    """Le maillon où la qualification se perdrait. `merge_raw_profile` fusionne
    `dossiers_legislatifs[]` en additif pur : sans le report, l'entrée ancienne
    gagne et le brut n'acquiert JAMAIS `nature_texte` — donc les 316 projets de
    loi du corpus resteraient publiés sous `role: "auteur"` indéfiniment, sans
    qu'aucune étape n'échoue (#639 et #492, même trou)."""
    ancien = {"dossiers_legislatifs": [_dossier_brut(CETA)]}
    neuf = {"dossiers_legislatifs": [_dossier_brut(CETA, nature_texte="projet_de_loi")]}
    fusionne = merge_raw_profile(ancien, neuf)
    assert [d["nature_texte"] for d in fusionne["dossiers_legislatifs"]] == ["projet_de_loi"]


def test_une_collecte_sans_nature_ne_regresse_pas_une_entree_qualifiee():
    """Une régénération qui ne rend plus le dossier laisse la nature acquise en
    place : la fusion additive ne fait jamais régresser un scalaire vers `null`
    (#641)."""
    ancien = {"dossiers_legislatifs": [_dossier_brut(CETA, nature_texte="projet_de_loi")]}
    neuf = {"dossiers_legislatifs": []}
    fusionne = merge_raw_profile(ancien, neuf)
    assert fusionne["dossiers_legislatifs"][0]["nature_texte"] == "projet_de_loi"


# ---------------------------------------------------------------------------
# 5. Le rôle publié est dérivé de la nature
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("nature, role_attendu", [
    ("projet_de_loi", "initiateur_projet_de_loi"),
    ("proposition_de_loi", "auteur_proposition_de_loi"),
    ("proposition_de_resolution", "auteur_proposition_de_resolution"),
])
def test_le_role_publie_derive_de_la_nature(nature, role_attendu):
    publie = _normalize_texte_porte(_dossier_brut(CETA, nature_texte=nature))
    assert publie["role"] == role_attendu
    assert publie["nature_texte"] == nature
    assert role_attendu in KNOWN_ROLES_TEXTE


def test_sans_nature_le_role_reste_auteur():
    """Les 5 entrées d'initiateur publiées dont la source n'établit pas la nature (missions
    d'information, commissions d'enquête, déclaration du Gouvernement), et les
    entrées collectées avant #689 : ce qu'on ne sait pas ne s'écrit pas comme
    autre chose (AGENTS.md §2 règle 5). Une passe `--pivot-only` ne peut donc
    pas requalifier tout le corpus sans qu'une archive ait été relue."""
    assert _normalize_texte_porte(_dossier_brut(CETA))["role"] == "auteur"
    assert _normalize_texte_porte(_dossier_brut(CETA))["nature_texte"] is None
    assert _normalize_texte_porte(_dossier_brut(CETA, nature_texte="invention"))["role"] == "auteur"


@pytest.mark.parametrize("role_brut", ["rapporteur", "co-rapporteur", None])
def test_les_roles_de_rapport_traversent_inchanges(role_brut):
    """Rapporter un projet de loi est une fonction parlementaire ordinaire : ce
    n'est pas porter le texte au nom du Gouvernement."""
    publie = _normalize_texte_porte(
        _dossier_brut(CETA, role=role_brut, nature_texte="projet_de_loi")
    )
    assert publie["role"] == role_brut
    assert publie["nature_texte"] == "projet_de_loi"


# ---------------------------------------------------------------------------
# 6. Les deux champs ne peuvent pas se contredire
# ---------------------------------------------------------------------------

def _profil_avec_texte(**texte) -> dict:
    profil = make_empty_profil("edouard-philippe", "Édouard Philippe")
    profil["textes_portes"] = [{
        "titre": CETA_TITRE, "dossier_id": CETA, "type_rapport": None,
        "stade_procedural": "adopte", "sort": "adopte", "date_min": "2019-06-19",
        "date_max": "2024-03-21", "legislature": "15", "source_url": None,
        **texte,
    }]
    return profil


def test_un_role_coherent_avec_sa_nature_est_valide():
    for nature, role in ROLE_INITIATEUR_PAR_NATURE.items():
        assert validate_profil(_profil_avec_texte(role=role, nature_texte=nature)) == []
    assert validate_profil(_profil_avec_texte(role="auteur", nature_texte=None)) == []
    assert validate_profil(_profil_avec_texte(role="rapporteur", nature_texte="projet_de_loi")) == []


def test_un_role_qui_contredit_sa_nature_est_refuse():
    """Deux champs qui disent la même chose ne valent que s'ils ne peuvent pas
    se contredire — même invariant que `chambre` / `chambres[0]` (#493). Sans
    lui, la redondance serait une seconde vérité à côté de la première."""
    erreurs = validate_profil(
        _profil_avec_texte(role="auteur_proposition_de_loi", nature_texte="projet_de_loi")
    )
    assert any("contredit" in e for e in erreurs), erreurs

    erreurs = validate_profil(_profil_avec_texte(role="auteur", nature_texte="projet_de_loi"))
    assert any("contredit" in e for e in erreurs), erreurs


def test_une_nature_hors_nomenclature_est_refusee():
    erreurs = validate_profil(_profil_avec_texte(role="auteur", nature_texte="loi"))
    assert any("nature_texte non reconnue" in e for e in erreurs), erreurs


# ---------------------------------------------------------------------------
# 7. Le garde-fou mesure la donnée PUBLIÉE, pas les tests
# ---------------------------------------------------------------------------

def _ecrire_pivot(repertoire: Path, slug: str, provenance: str, textes: list[dict]) -> None:
    profil = make_empty_profil(slug, slug)
    profil["meta"]["provenance"] = provenance
    profil["textes_portes"] = textes
    (repertoire / f"{slug}.pivot.json").write_text(
        json.dumps(profil, ensure_ascii=False), encoding="utf-8"
    )


def test_la_section_5c_compte_ce_qui_est_qualifie_et_ce_qui_attend(tmp_path):
    """Un correctif qui ne se vérifie que dans les tests ne dit rien de ce que
    le site montre. La §5c lit le corpus publié, nomme la population de chaque
    chiffre (#630) et reste SOFT : la qualification n'atteint un profil qu'au
    run réel qui le recollecte, et bloquer le commit interdirait les runs censés
    la propager (#447, cause #450)."""
    from check_quality_gate import _report_qualification_textes_portes

    _ecrire_pivot(tmp_path, "edouard-philippe", "candidat_declare", [
        {"titre": CETA_TITRE, "dossier_id": CETA, "role": "initiateur_projet_de_loi",
         "nature_texte": "projet_de_loi", "type_rapport": None,
         "stade_procedural": "adopte", "date_min": None, "date_max": None,
         "legislature": "15", "source_url": None},
        {"titre": "Sans nature", "dossier_id": "DLR5L15N00001", "role": "auteur",
         "nature_texte": None, "type_rapport": None, "stade_procedural": "depose",
         "date_min": None, "date_max": None, "legislature": "15", "source_url": None},
    ])
    _ecrire_pivot(tmp_path, "un-membre-de-roster", "roster_groupe", [
        {"titre": "Rapport", "dossier_id": "DLR5L17N00002", "role": "rapporteur",
         "nature_texte": "proposition_de_loi", "type_rapport": None,
         "stade_procedural": "adopte", "date_min": None, "date_max": None,
         "legislature": "17", "source_url": None},
    ])

    soft, console, markdown = _report_qualification_textes_portes(tmp_path)

    assert "Entrées publiées : 3" in console
    assert "Projets de loi portés au nom du Gouvernement : 1" in console
    assert "Initiateurs sans nature établie : 1" in console
    assert "edouard-philippe : 1/2" in console
    assert "1 candidats" in markdown, "la population de chaque chiffre est nommée"
    assert len(soft) == 1


def test_la_section_5c_se_tait_quand_tout_est_qualifie(tmp_path):
    """Sa condition de retrait est écrite, et elle se mesure : 0 initiateur sans
    nature sur le corpus publié."""
    from check_quality_gate import _report_qualification_textes_portes

    _ecrire_pivot(tmp_path, "un-candidat", "candidat_declare", [
        {"titre": "PPL", "dossier_id": "DLR5L17N00003", "role": "auteur_proposition_de_loi",
         "nature_texte": "proposition_de_loi", "type_rapport": None,
         "stade_procedural": "adopte", "date_min": None, "date_max": None,
         "legislature": "17", "source_url": None},
    ])
    soft, console, _ = _report_qualification_textes_portes(tmp_path)
    assert soft == []
    assert "✓ Initiateurs sans nature établie : 0" in console


# ---------------------------------------------------------------------------
# 5. Le libellé affiché nomme l'initiative, et couvre tout le vocabulaire
# ---------------------------------------------------------------------------

_PROFIL_CANDIDAT_JS = Path("web/UI_finale/src/utils/profilCandidat.js")


def _libelles_role_texte() -> dict[str, str]:
    """Table `LIBELLE_ROLE_TEXTE` du module d'interface, lue depuis le code
    exécuté. Le dépôt n'a pas de harnais de test JS (`package.json` ne déclare
    que `dev`, `build`, `lint`, `sync-data`) : ce garde-fou est donc en Python,
    et il lit le fichier plutôt que de recopier ses valeurs."""
    source = _PROFIL_CANDIDAT_JS.read_text(encoding="utf-8")
    debut = source.index("export const LIBELLE_ROLE_TEXTE = {")
    corps = source[debut : source.index("\n};", debut)]
    # Les commentaires portent des exemples de clés (« initiateur_projet_de_loi »)
    # qu'un relevé naïf compterait comme des entrées.
    corps = "\n".join(l for l in corps.splitlines() if not l.lstrip().startswith("//"))
    return dict(
        re.findall(r"^\s*'?([\w-]+)'?:\s*\n?\s*['\"](.+?)['\"],", corps, re.MULTILINE)
    )


def test_chaque_role_publie_a_un_libelle():
    """Sans libellé, la fiche afficherait la clé technique telle quelle dès le
    premier run qualifié — `LIBELLE_ROLE_TEXTE[t.role] || t.role`. Le
    commentaire du module l'affirmait, rien ne le vérifiait."""
    from schema_pivot import KNOWN_ROLES_TEXTE

    libelles = _libelles_role_texte()
    manquants = sorted(KNOWN_ROLES_TEXTE - set(libelles))
    assert not manquants, f"rôles publiés sans libellé d'interface : {manquants}"
    orphelins = sorted(set(libelles) - KNOWN_ROLES_TEXTE)
    assert not orphelins, f"libellés pour des rôles hors vocabulaire : {orphelins}"


def test_le_libelle_nomme_l_initiative_pas_la_chambre():
    """« Issue de l'Assemblée nationale » aurait été faux 157 fois sur 391 :
    122 des 313 projets de loi des 13 candidats ont été déposés au
    Sénat sans cesser d'être des textes du gouvernement, et 35 des 78
    propositions sont sénatoriales. Ce que le libellé nomme, c'est l'article 39
    — qui est à l'initiative du texte — jamais la chambre de dépôt."""
    libelles = _libelles_role_texte()

    assert libelles["initiateur_projet_de_loi"] == (
        "Projet de loi à l'initiative du gouvernement"
    )
    assert libelles["auteur_proposition_de_loi"] == (
        "Proposition de loi issue d'un(e) parlementaire"
    )
    for role in ("initiateur_projet_de_loi", "auteur_proposition_de_loi"):
        assert "Assemblée" not in libelles[role] and "Sénat" not in libelles[role]


def test_le_libelle_de_resolution_ne_dit_pas_decision():
    """Une résolution ne crée aucune règle, et le libellé doit le dire sans
    affirmer d'aboutissement : 2 des 26 résolutions publiées seulement portent
    le stade `adopte`, et un texte déposé sans être voté n'a rien décidé
    (AGENTS.md §2 règle 5). La parenthèse énumère donc les deux procédures que
    la source distingue elle-même, sans trancher laquelle s'applique."""
    libelle = _libelles_role_texte()["auteur_proposition_de_resolution"]

    assert libelle == "Résolution (prise de position ou demande procédurale)"
    assert "décision" not in libelle
