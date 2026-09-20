#!/usr/bin/env python3
"""
test_entree_derivee_correspondance_715.py — Une entrée dérivée gèle un slug
fabriqué, et n'ouvre la porte à rien d'autre (#715).

Ce que ces tests protègent, c'est une frontière, pas une fonctionnalité. #708 a
ouvert une porte d'entrée : un membre de roster sans correspondance relue reçoit
`slugify(état civil AMO30)`. La §5b du portail exigeait ensuite une entrée de
table pour publier — et le constructeur ne pouvait rien proposer, puisqu'il part
des profils **déjà publiés**. La passe dérivée comble ce trou-là **et aucun
autre** : elle n'écrit que pour un slug que le roster du run déclare fabriqué,
elle ne réécrit jamais une entrée relue, et elle refuse dès que le profil publié
ne corrobore pas l'acteur déclaré.

Aucun test ne lit `pivot_data/`, `raw_data/profiles/` ni le réseau (AGENTS.md
§3b) : tout est monté en `tmp_path`, et la table de référence est la fixture
extraite de #525.
"""

from pathlib import Path
import json
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import build_correspondance_acteurs_an as builder  # noqa: E402
import check_quality_gate as gate  # noqa: E402
import correspondance_acteurs_an as corr  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "correspondance_acteurs_an_extrait.json"


@pytest.fixture(autouse=True)
def _memo_propre():
    corr.vider_memo()
    yield
    corr.vider_memo()


def _table(tmp_path, correspondances):
    document = {
        "schema_version": corr.SCHEMA_VERSION,
        "genere_le": "2026-08-26T00:00:00+0000",
        "source_referentiel": "https://data.assemblee-nationale.fr/",
        "correspondances": correspondances,
    }
    chemin = tmp_path / "table.json"
    chemin.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    return chemin


def _entree_relue(acteur_ref="PA1"):
    return {
        "identifiants": {"an": acteur_ref, "senat": None, "europarl": None, "hatvp": None},
        "etat_civil": {"nom_complet": "Témoin Relu"},
        "ecart": None,
        "motif": None,
        "preuve": f"https://www2.assemblee-nationale.fr/deputes/fiche/OMC_{acteur_ref}",
        "verifie_le": "2026-08-26",
    }


def _rosters_bruts(tmp_path, membres, nom="rosters_bruts.json"):
    chemin = tmp_path / nom
    chemin.write_text(
        json.dumps({"rosters": {"deputes:17": membres}}, ensure_ascii=False),
        encoding="utf-8",
    )
    return chemin


def _profil(profiles_dir, slug, acteur_ref, **identite):
    profiles_dir.mkdir(exist_ok=True)
    bloc = {"civilite": None, "date_naissance": None, "uri_hatvp": None, "source_url": None}
    bloc.update(identite)
    (profiles_dir / f"{slug}.pivot.json").write_text(
        json.dumps(
            {
                "id": slug,
                "nom": identite.get("nom_complet", "Élue Neuve"),
                "identifiants": {"an": acteur_ref, "senat": None, "europarl": None, "hatvp": None},
                "identite": bloc,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def _membre(slug, acteur_ref, origine="fabrique"):
    return {"slug": slug, "acteur_ref": acteur_ref, "slug_origine": origine, "nom": "Élue Neuve"}


# --------------------------------------------------------------------------
# 1. Le schéma : `origine` est fermée, et son défaut est un fait daté
# --------------------------------------------------------------------------

def test_une_entree_sans_origine_est_lue_relue(tmp_path):
    """Les 481 entrées committées avant ce lot n'ont pas la clé, et ne
    pouvaient venir que de la passe relue de #525 : la porte de fabrication
    n'existait pas."""
    chemin = _table(tmp_path, {"temoin": _entree_relue()})
    assert corr.charger_correspondance(chemin)["temoin"]["origine"] == "relue"


def test_une_origine_inconnue_est_refusee(tmp_path):
    entree = dict(_entree_relue(), origine="automatique")
    chemin = _table(tmp_path, {"temoin": entree})
    with pytest.raises(corr.CorrespondanceInvalide, match="origine inconnue"):
        corr.charger_correspondance(chemin)


def test_une_entree_derivee_ne_peut_pas_porter_decart(tmp_path):
    """Un écart est le produit d'un arbitrage. Le porter tout en se déclarant
    non relue serait une entrée qui se contredit."""
    entree = dict(
        _entree_relue(),
        origine="derivee",
        ecart="nom_divergent",
        motif="nom d'usage",
    )
    chemin = _table(tmp_path, {"temoin": entree})
    with pytest.raises(corr.CorrespondanceInvalide, match="un écart s'arbitre"):
        corr.charger_correspondance(chemin)


def test_la_fixture_porte_un_temoin_derive():
    """Une fixture qui ne décrirait que le cas relu ne dirait rien du nouveau
    régime — le piège de `syceron_minimal.xml` (#510)."""
    table = corr.charger_correspondance(FIXTURE)
    derivees = [s for s, e in table.items() if e["origine"] == "derivee"]
    assert derivees == ["elue-derivee"]
    assert table["adrien-quatennens"]["origine"] == "relue"


# --------------------------------------------------------------------------
# 2. Qui est déclaré fabriqué, et par quoi
# --------------------------------------------------------------------------

def test_seul_slug_origine_fabrique_est_retenu(tmp_path):
    chemin = _rosters_bruts(
        tmp_path,
        [_membre("elue-neuve", "PA800001"), _membre("deja-relue", "PA1", origine="table")],
    )
    assert builder.slugs_fabriques(chemin) == {"elue-neuve": "PA800001"}


def test_un_slug_fabrique_sur_deux_acteurs_est_refuse(tmp_path):
    """Le roster se contredirait, et rien ne dirait lequel croire."""
    chemin = tmp_path / "rosters_bruts.json"
    chemin.write_text(
        json.dumps(
            {
                "rosters": {
                    "deputes:16": [_membre("elue-neuve", "PA800001")],
                    "deputes:17": [_membre("elue-neuve", "PA800002")],
                }
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(SystemExit, match="déclaré sur deux acteurs"):
        builder.slugs_fabriques(chemin)


# --------------------------------------------------------------------------
# 3. Ce que la passe écrit — et les trois filtres qui l'en empêchent
# --------------------------------------------------------------------------

def test_lentree_derivee_est_ecrite_et_relit_valide(tmp_path):
    profils = tmp_path / "pivots"
    _profil(
        profils,
        "elue-neuve",
        "PA800001",
        nom_complet="Élue Neuve",
        civilite="Mme",
        date_naissance="1980-01-02",
    )
    entrees, refus = builder.entrees_derivees(
        profils, {"elue-neuve": "PA800001"}, {}, "2026-09-02"
    )
    assert refus == []
    assert set(entrees) == {"elue-neuve"}

    ecrite = entrees["elue-neuve"]
    assert ecrite["origine"] == "derivee"
    assert ecrite["identifiants"]["an"] == "PA800001"
    assert ecrite["preuve"].endswith("OMC_PA800001")
    assert ecrite["etat_civil"]["date_naissance"] == "1980-01-02"
    # `prenom`/`nom` séparés n'existent que dans la fiche AMO30, que cette
    # passe ne lit pas : `null` dit « non porté », pas « sans prénom ».
    assert ecrite["etat_civil"]["prenom"] is None

    chemin = _table(tmp_path, {"elue-neuve": ecrite})
    assert corr.charger_correspondance(chemin)["elue-neuve"]["acteur_ref"] == "PA800001"


def test_une_entree_existante_nest_jamais_reecrite(tmp_path):
    """La table passe devant la fabrication (#708 §3) : c'est ce qui empêche un
    changement de nom d'usage de déplacer l'identifiant d'une personne déjà
    collectée."""
    profils = tmp_path / "pivots"
    _profil(profils, "deja-relue", "PA999")
    entrees, refus = builder.entrees_derivees(
        profils,
        {"deja-relue": "PA800001"},
        {"deja-relue": _entree_relue("PA999")},
        "2026-09-02",
    )
    assert entrees == {} and refus == []


def test_un_slug_publie_non_declare_fabrique_ne_recoit_rien(tmp_path):
    """Le garde-fou contre le tampon : #525 §6 interdit toujours de combler une
    correspondance depuis `identite.source_url`."""
    profils = tmp_path / "pivots"
    _profil(profils, "slug-herite", "PA800001")
    entrees, refus = builder.entrees_derivees(profils, {}, {}, "2026-09-02")
    assert entrees == {} and refus == []


def test_un_slug_fabrique_sans_profil_publie_ne_recoit_rien(tmp_path):
    """La §5b ne bloque que sur les profils publiés ; poser l'entrée d'avance
    serait un tampon sur quelqu'un que le run n'a pas collecté."""
    profils = tmp_path / "pivots"
    profils.mkdir()
    entrees, refus = builder.entrees_derivees(
        profils, {"elue-neuve": "PA800001"}, {}, "2026-09-02"
    )
    assert entrees == {} and refus == []


def test_un_desaccord_dacteur_refuse_et_nomme(tmp_path):
    """Le profil décrirait un acteur et le slug en désignerait un autre — le
    défaut de clé collante de #540, sur le seul identifiant du dépôt."""
    profils = tmp_path / "pivots"
    _profil(profils, "elue-neuve", "PA999999")
    entrees, refus = builder.entrees_derivees(
        profils, {"elue-neuve": "PA800001"}, {}, "2026-09-02"
    )
    assert entrees == {}
    assert len(refus) == 1
    assert "elue-neuve" in refus[0] and "PA800001" in refus[0] and "PA999999" in refus[0]


def test_un_profil_sans_identifiant_an_refuse(tmp_path):
    profils = tmp_path / "pivots"
    _profil(profils, "elue-neuve", None)
    entrees, refus = builder.entrees_derivees(
        profils, {"elue-neuve": "PA800001"}, {}, "2026-09-02"
    )
    assert entrees == {}
    assert "aucun identifiant AN" in refus[0]


def test_lacteur_est_relu_dans_lurl_de_fiche_a_defaut_didentifiants(tmp_path):
    """`normalize_profil` tire lui-même `identifiants.an` de cette URL quand la
    table est muette : même fait, même source, pas une seconde autorité."""
    profils = tmp_path / "pivots"
    _profil(
        profils,
        "elue-neuve",
        None,
        source_url="https://www2.assemblee-nationale.fr/deputes/fiche/OMC_PA800001",
    )
    entrees, refus = builder.entrees_derivees(
        profils, {"elue-neuve": "PA800001"}, {}, "2026-09-02"
    )
    assert refus == [] and set(entrees) == {"elue-neuve"}


# --------------------------------------------------------------------------
# 4. La commande : additive, silencieuse quand il n'y a rien à faire
# --------------------------------------------------------------------------

def _lancer(tmp_path, sortie, rosters, profils):
    args = builder._build_arg_parser().parse_args(
        [
            "--completer-derivees",
            "--rosters-bruts",
            str(rosters),
            "--profiles-dir",
            str(profils),
            "--sortie",
            str(sortie),
            "--verifie-le",
            "2026-09-02",
        ]
    )
    return builder.completer_derivees(args)


def test_la_commande_ajoute_sans_toucher_aux_entrees_relues(tmp_path):
    sortie = _table(tmp_path, {"deja-relue": _entree_relue("PA999")})
    avant = json.loads(sortie.read_text(encoding="utf-8"))
    profils = tmp_path / "pivots"
    _profil(profils, "elue-neuve", "PA800001")
    rosters = _rosters_bruts(tmp_path, [_membre("elue-neuve", "PA800001")])

    assert _lancer(tmp_path, sortie, rosters, profils) == 0

    apres = json.loads(sortie.read_text(encoding="utf-8"))
    assert set(apres["correspondances"]) == {"deja-relue", "elue-neuve"}
    # Reconduite **verbatim** : ni `acteur_ref` ajouté en doublon
    # d'`identifiants.an`, ni `origine` posée sur du travail relu.
    assert apres["correspondances"]["deja-relue"] == avant["correspondances"]["deja-relue"]
    assert apres["correspondances"]["elue-neuve"]["origine"] == "derivee"
    corr.vider_memo()
    assert len(corr.charger_correspondance(sortie)) == 2


def test_la_commande_ne_reecrit_rien_quand_il_ny_a_rien_a_ajouter(tmp_path):
    """`genere_le` bougerait à chaque run et le step de commit verrait un
    changement là où il n'y en a pas."""
    sortie = _table(tmp_path, {"deja-relue": _entree_relue("PA999")})
    avant = sortie.read_bytes()
    profils = tmp_path / "pivots"
    _profil(profils, "deja-relue", "PA999")
    rosters = _rosters_bruts(tmp_path, [_membre("deja-relue", "PA999", origine="table")])

    assert _lancer(tmp_path, sortie, rosters, profils) == 0
    assert sortie.read_bytes() == avant


def test_un_refus_sort_en_echec(tmp_path):
    sortie = _table(tmp_path, {"deja-relue": _entree_relue("PA999")})
    profils = tmp_path / "pivots"
    _profil(profils, "elue-neuve", "PA999999")
    rosters = _rosters_bruts(tmp_path, [_membre("elue-neuve", "PA800001")])
    assert _lancer(tmp_path, sortie, rosters, profils) == 1


def test_la_commande_exige_les_rosters_bruts(tmp_path, capsys):
    args = builder._build_arg_parser().parse_args(["--completer-derivees"])
    assert builder.completer_derivees(args) == 2
    assert "--rosters-bruts" in capsys.readouterr().err


def test_la_commande_ne_repart_pas_dune_table_illisible(tmp_path, capsys):
    """Additive veut dire additive : sur une table absente elle ne reconstruit
    pas un artefact relu à partir de rien."""
    rosters = _rosters_bruts(tmp_path, [_membre("elue-neuve", "PA800001")])
    profils = tmp_path / "pivots"
    _profil(profils, "elue-neuve", "PA800001")
    assert _lancer(tmp_path, tmp_path / "absente.json", rosters, profils) == 2
    assert "illisible" in capsys.readouterr().err


# --------------------------------------------------------------------------
# 5. Le portail : couvert, mais compté
# --------------------------------------------------------------------------

def _profils_publies(tmp_path, slugs):
    repertoire = tmp_path / "publies"
    repertoire.mkdir()
    for slug in slugs:
        (repertoire / f"{slug}.pivot.json").write_text("{}", encoding="utf-8")
    return repertoire


def test_une_entree_derivee_couvre_le_commit(tmp_path):
    repertoire = _profils_publies(tmp_path, ["elue-derivee"])
    durs, console, _ = gate._report_correspondance_acteurs(repertoire, FIXTURE)
    assert durs == []
    assert "Tout profil publié porte sa correspondance relue" in console


def test_le_portail_publie_la_file_dattente_de_relecture(tmp_path):
    """#708 §8 nommait la file sans la rendre visible ; une file qu'on ne voit
    pas ne se résorbe pas."""
    repertoire = _profils_publies(tmp_path, ["elue-derivee"])
    _, console, md = gate._report_correspondance_acteurs(repertoire, FIXTURE)
    assert "en attente de relecture : 1" in console
    assert "| Dont dérivées, en attente de relecture (#715) | 1 |" in md


def test_le_portail_nomme_encore_le_slug_non_couvert(tmp_path):
    """La passe dérivée n'assouplit pas la §5b : elle lui donne de quoi être
    satisfaite, elle ne la contourne pas."""
    repertoire = _profils_publies(tmp_path, ["elue-derivee", "jamais-vue"])
    durs, _, _ = gate._report_correspondance_acteurs(repertoire, FIXTURE)
    assert len(durs) == 1 and "jamais-vue" in durs[0]
    assert "--completer-derivees" in durs[0]
