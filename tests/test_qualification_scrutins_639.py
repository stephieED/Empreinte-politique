"""Qualification sourcée des scrutins (issue #639, rang 1).

`_parse_scrutins_zip` ne retenait que `numero`, `date`, `titre`, `sort` et
`legislature`. `typeVote` et `demandeur` étaient lus puis jetés, alors que la
source les renseigne : relevé du 31/08/2026 sur les quatre archives réelles,
`typeVote` est présent sur **18 311 / 18 311** scrutins bruts et
`demandeur.texte` sur 18 226.

Conséquence mesurée sur `pivot_data/scrutins.json` avant ce lot : `type_vote`
valait « vote_texte » sur les **17 748** scrutins publiés et `type_scrutin` y
était `null` sur les 17 748. Les **66 motions de censure** (14e : 4, 15e : 5,
16e : 34, 17e : 23) étaient donc publiées sous le même type que les votes sur
un texte, et l'invariant d'AGENTS.md §5 était vacuement satisfait.

FIXTURES. Six scrutins réels, réduits **verbatim** depuis les archives
`data.assemblee-nationale.fr` (`tests/fixtures/scrutins_an/`) : seules les
listes nominatives sont tronquées à un votant et `miseAuPoint` retirée ; aucune
valeur n'est inventée. C'est la leçon de #510 — les deux fixtures inventées de
l'époque avaient laissé la panne armée sous une suite verte. Ils couvrent les
deux conditionnements d'archive (14e monolithique, 17e un fichier par scrutin),
les quatre codes publiés (SPO, SPS, SAT, MOC) et les deux formes de
`demandeur.texte` (renseigné et nul).
"""

import gzip
import json
import sys
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import candidate_profile  # noqa: E402
from candidate_profile import (  # noqa: E402
    SCRUTINS_CACHE_INDEX_PAR_ACTEUR_DIRNAME,
    SCRUTINS_CACHE_SCRUTINS_FILENAME,
    SCRUTINS_FIGES_INDEX_PAR_ACTEUR_FILENAME,
    SCRUTINS_FIGES_SCRUTINS_FILENAME,
    _load_frozen_scrutins_index,
    _parse_scrutins_zip,
    _scrutins_cache_present,
    _scrutins_store_qualifie,
)
from schema_pivot import (  # noqa: E402
    KNOWN_TYPES_SCRUTIN,
    KNOWN_TYPES_VOTE,
    SCRUTINS_SCHEMA_VERSION,
    validate_scrutins_index,
)
import scrutins_index  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures" / "scrutins_an"

# Réductions verbatim, par conditionnement d'archive.
SCRUTINS_14E = ("VTANR5L14V1", "VTANR5L14V2", "VTANR5L14V292")      # SAT, SPO, MOC
SCRUTINS_17E = ("VTANR5L17V842", "VTANR5L17V2657", "VTANR5L17V4241")  # MOC, SPO, SPS


@pytest.fixture(autouse=True)
def _purge_memo_store_scrutins():
    candidate_profile._clear_scrutins_store_memo()
    yield
    candidate_profile._clear_scrutins_store_memo()


def _brut(uid: str) -> dict:
    return json.loads((FIXTURES / f"{uid}.json").read_text(encoding="utf-8"))


def _zip_par_fichier(tmp_path, uids, nom="Scrutins.json.zip"):
    """Conditionnement 15/16/17 : un fichier JSON par scrutin."""
    chemin = tmp_path / nom
    with zipfile.ZipFile(chemin, "w") as zf:
        for uid in uids:
            zf.writestr(f"json/{uid}.json", json.dumps({"scrutin": _brut(uid)}))
    return chemin


def _zip_monolithique(tmp_path, uids, nom="Scrutins_XIV.json.zip"):
    """Conditionnement de la 14e : un seul JSON `scrutins.scrutin[]`."""
    chemin = tmp_path / nom
    with zipfile.ZipFile(chemin, "w") as zf:
        zf.writestr(
            "Scrutins_XIV.json",
            json.dumps({"scrutins": {"scrutin": [_brut(uid) for uid in uids]}}),
        )
    return chemin


# ---------------------------------------------------------------------------
# La qualification survit aux DEUX conditionnements d'archive
# ---------------------------------------------------------------------------

def test_qualification_conservee_conditionnement_monolithique_14e(tmp_path):
    """14e législature : JSON monolithique. Les trois codes qu'elle porte
    (SAT, SPO, MOC) doivent ressortir qualifiés."""
    scrutins, _ = _parse_scrutins_zip(_zip_monolithique(tmp_path, SCRUTINS_14E), "14")

    assert scrutins["VTANR5L14V1"]["type_scrutin"] == "tribune"
    assert scrutins["VTANR5L14V1"]["type_vote"] == "vote_texte"
    assert scrutins["VTANR5L14V2"]["type_scrutin"] == "public_ordinaire"
    assert scrutins["VTANR5L14V2"]["type_vote"] == "vote_texte"
    assert scrutins["VTANR5L14V292"]["type_scrutin"] == "motion_censure"
    assert scrutins["VTANR5L14V292"]["type_vote"] == "motion_censure"
    assert scrutins["VTANR5L14V292"]["demandeur"] == "Conférence des présidents"


def test_qualification_conservee_conditionnement_par_fichier_17e(tmp_path):
    """15/16/17e : un fichier par scrutin. Le correctif doit valoir pour ce
    conditionnement aussi — les deux branches de `_iter_scrutins_bruts`
    convergeaient vers la même projection à cinq champs."""
    scrutins, _ = _parse_scrutins_zip(_zip_par_fichier(tmp_path, SCRUTINS_17E), "17")

    assert scrutins["VTANR5L17V842"]["type_vote"] == "motion_censure"
    assert scrutins["VTANR5L17V2657"]["type_scrutin"] == "public_ordinaire"
    assert scrutins["VTANR5L17V4241"]["type_scrutin"] == "solennel"
    assert scrutins["VTANR5L17V2657"]["demandeur"] == 'Présidente du groupe "Rassemblement National"'


def test_demandeur_nul_reste_nul(tmp_path):
    """`demandeur` est toujours un objet, mais son `texte` est nul sur 85 des
    18 311 scrutins bruts — dont la motion de censure du 19/02/2025 servant de
    fixture. Un `null` reste un `null` (AGENTS.md §2 règle 5)."""
    scrutins, _ = _parse_scrutins_zip(_zip_par_fichier(tmp_path, ("VTANR5L17V842",)), "17")

    assert scrutins["VTANR5L17V842"]["demandeur"] is None


# ---------------------------------------------------------------------------
# Aucun type deviné
# ---------------------------------------------------------------------------

def test_code_typevote_inconnu_reste_sans_qualification(tmp_path):
    """Un code que la table ne connaît pas ne doit pas être rangé dans SPO,
    qui est pourtant 97,5 % des scrutins publiés (AGENTS.md §2 règle 5)."""
    brut = _brut("VTANR5L17V2657")
    brut["typeVote"]["codeTypeVote"] = "XXX"
    chemin = tmp_path / "Scrutins.json.zip"
    with zipfile.ZipFile(chemin, "w") as zf:
        zf.writestr("json/x.json", json.dumps({"scrutin": brut}))

    scrutins, _ = _parse_scrutins_zip(chemin, "17")

    assert scrutins["VTANR5L17V2657"]["type_scrutin"] is None
    assert scrutins["VTANR5L17V2657"]["type_vote"] is None


def test_typevote_absent_reste_sans_qualification(tmp_path):
    """Un scrutin sans bloc `typeVote` reste non qualifié, et n'interrompt pas
    le parsing."""
    brut = _brut("VTANR5L17V2657")
    del brut["typeVote"]
    chemin = tmp_path / "Scrutins.json.zip"
    with zipfile.ZipFile(chemin, "w") as zf:
        zf.writestr("json/x.json", json.dumps({"scrutin": brut}))

    scrutins, index = _parse_scrutins_zip(chemin, "17")

    assert scrutins["VTANR5L17V2657"]["type_scrutin"] is None
    assert scrutins["VTANR5L17V2657"]["type_vote"] is None
    assert index, "Le scrutin reste indexé : seule sa qualification manque"


def test_les_valeurs_produites_appartiennent_au_vocabulaire_ferme():
    """Toute valeur de la table doit être déclarée dans les frozensets du
    schéma : c'est la règle « étendre le frozenset, jamais le contourner »
    (AGENTS.md §4)."""
    for type_scrutin, type_vote in candidate_profile._SCRUTINS_TYPE_PAR_CODE.values():
        assert type_scrutin in KNOWN_TYPES_SCRUTIN
        assert type_vote in KNOWN_TYPES_VOTE


def test_le_congres_reste_ecarte_et_nest_pas_dans_la_table():
    """SSG (« scrutin solennel du Congrès ») n'est PAS dans la table : la seule
    occurrence des quatre archives porte un uid de Congrès et est écartée en
    amont. L'y inscrire laisserait croire que le Congrès est publié."""
    assert "SSG" not in candidate_profile._SCRUTINS_TYPE_PAR_CODE


# ---------------------------------------------------------------------------
# L'existence d'un cache n'est pas la preuve de ce qu'il contient
# ---------------------------------------------------------------------------

def _ecrire_cache(racine, legislature, store):
    cache = racine / legislature
    (cache / SCRUTINS_CACHE_INDEX_PAR_ACTEUR_DIRNAME).mkdir(parents=True, exist_ok=True)
    (cache / SCRUTINS_CACHE_SCRUTINS_FILENAME).write_text(json.dumps(store), encoding="utf-8")


STORE_AVANT_639 = {
    "VTANR5L16V1": {"numero": "1", "date": "2023-01-01", "titre": "T", "sort": None, "legislature": "16"}
}
STORE_APRES_639 = {
    "VTANR5L16V1": {**STORE_AVANT_639["VTANR5L16V1"],
                    "type_scrutin": "public_ordinaire", "type_vote": "vote_texte", "demandeur": None}
}


def test_cache_anterieur_a_639_est_traite_comme_absent(tmp_path):
    """Un cache présent mais écrit sous la projection à cinq champs
    republierait 17 748 scrutins sans qualification, sans que rien ne le dise
    (AGENTS.md §5 : « un répertoire qui existe n'est pas la preuve de ce qu'il
    contient »)."""
    _ecrire_cache(tmp_path, "16", STORE_AVANT_639)
    with patch("candidate_profile.SCRUTINS_CACHE_DIR", tmp_path):
        assert _scrutins_cache_present("16") is False

    _ecrire_cache(tmp_path, "16", STORE_APRES_639)
    with patch("candidate_profile.SCRUTINS_CACHE_DIR", tmp_path):
        assert _scrutins_cache_present("16") is True


def test_store_qualifie_teste_la_cle_pas_la_valeur():
    """`type_scrutin` peut légitimement valoir `None` (code inconnu) : exiger
    une valeur refuserait un cache correct."""
    assert _scrutins_store_qualifie({"u": {"numero": "1", "type_scrutin": None}}) is True
    assert _scrutins_store_qualifie({"u": {"numero": "1"}}) is False
    assert _scrutins_store_qualifie({}) is False


def test_index_fige_anterieur_a_639_est_refuse_et_le_dit(tmp_path, capsys):
    """Accepter un index figé non qualifié laisserait les législatures 14, 15
    et 16 publier 43 motions de censure étiquetées `vote_texte` jusqu'à ce que
    quelqu'un pense à relancer `build_scrutins_index_figes.py`."""
    figes = tmp_path / "figes"
    (figes / "16").mkdir(parents=True)
    with gzip.open(figes / "16" / SCRUTINS_FIGES_SCRUTINS_FILENAME, "wt", encoding="utf-8") as f:
        json.dump(STORE_AVANT_639, f)
    with gzip.open(figes / "16" / SCRUTINS_FIGES_INDEX_PAR_ACTEUR_FILENAME, "wt", encoding="utf-8") as f:
        json.dump({"PA1": [["VTANR5L16V1", "pour"]]}, f)

    with (
        patch("candidate_profile.AN_SCRUTINS_FIGES_DIR", figes),
        patch("candidate_profile.SCRUTINS_CACHE_DIR", tmp_path / "cache"),
    ):
        assert _load_frozen_scrutins_index("16") is False

    sortie = capsys.readouterr().out
    assert "build_scrutins_index_figes.py" in sortie, "Le refus doit nommer la remédiation"


# ---------------------------------------------------------------------------
# Motion de censure : la clé absente est DÉCLARÉE, jamais inventée
# ---------------------------------------------------------------------------

def _vote_brut(numero, date, type_vote, type_scrutin, **extra):
    return {"numero_scrutin": numero, "date": date, "legislature": "17",
            "titre": "T", "sort": None, "position": "pour",
            "type_vote": type_vote, "type_scrutin": type_scrutin, **extra}


def test_motion_de_censure_publie_la_declaration_dabsence_de_texte_lie():
    """Le scrutin AN ne porte aucune référence législative (0 / 18 311 sur les
    quatre archives). Plutôt qu'inventer `texte_lie_id` ou taire son absence,
    l'index publie la déclaration — patron `*_non_resolu` du dépôt."""
    index, _ = scrutins_index.construire_index(
        [_vote_brut("842", "2025-02-19", "motion_censure", "motion_censure")]
    )
    scrutin = index.get("an:17:842")

    assert scrutin["texte_lie_id"] is None
    assert scrutin["texte_lie_non_resolu"]["motif"]
    assert validate_scrutins_index({
        "schema_version": SCRUTINS_SCHEMA_VERSION, "scrutins": index.liste(),
    }) == []


def test_un_vote_sur_texte_ne_porte_aucune_declaration():
    index, _ = scrutins_index.construire_index(
        [_vote_brut("2657", "2025-06-17", "vote_texte", "public_ordinaire")]
    )
    assert "texte_lie_non_resolu" not in index.get("an:17:2657")


def test_la_declaration_disparait_quand_le_texte_lie_est_resolu():
    """Champ dérivé, jamais fusionné : garder « non résolu » à côté d'une clé
    résolue serait un fait faux."""
    index, _ = scrutins_index.construire_index([
        _vote_brut("842", "2025-02-19", "motion_censure", "motion_censure",
                   texte_lie_id="DLR5L17N54083")
    ])
    assert "texte_lie_non_resolu" not in index.get("an:17:842")


def test_la_fusion_pose_la_declaration_sur_un_scrutin_requalifie():
    """Un scrutin publié avant #639 sous `vote_texte` et requalifié
    `motion_censure` par un run récent doit gagner sa déclaration à la fusion."""
    ancien = scrutins_index.ScrutinsIndex({
        "an:17:842": {"id": "an:17:842", "legislature": "17", "numero_scrutin": "842",
                      "legislature_provenance": "collectee", "type_vote": "vote_texte",
                      "type_scrutin": None, "texte_lie_id": None},
    })
    nouveau, _ = scrutins_index.construire_index(
        [_vote_brut("842", "2025-02-19", "motion_censure", "motion_censure")]
    )

    fusionne = scrutins_index.merge_scrutins_index(ancien, nouveau).get("an:17:842")

    assert fusionne["type_vote"] == "motion_censure"
    assert fusionne["texte_lie_non_resolu"]["motif"]


def test_validate_refuse_une_motion_sans_cle_ni_declaration():
    """La seconde branche ouverte par #639 exige une DÉCLARATION, pas rien :
    une motion muette reste une erreur de schéma."""
    erreurs = validate_scrutins_index({
        "schema_version": SCRUTINS_SCHEMA_VERSION,
        "scrutins": [{"id": "an:17:842", "legislature": "17", "numero_scrutin": "842",
                      "legislature_provenance": "collectee", "type_vote": "motion_censure"}],
    })
    assert any("texte_lie_non_resolu" in e for e in erreurs)


# ---------------------------------------------------------------------------
# La chaîne complète : archive -> cache -> profil brut -> index publié
# ---------------------------------------------------------------------------

def test_la_qualification_traverse_larchive_jusquau_profil_brut(tmp_path):
    """Le champ le mieux parsé ne sert à rien s'il est jeté à l'étape
    suivante : c'est exactement ce qui est arrivé à `texte_vise` des
    amendements (#639, commentaire). On éprouve donc la chaîne entière sur la
    motion de censure du 19/02/2025, réduite verbatim."""
    archive = _zip_par_fichier(tmp_path, ("VTANR5L17V842",))
    with patch("candidate_profile.SCRUTINS_CACHE_DIR", tmp_path / "cache"):
        scrutins, index_acteur = _parse_scrutins_zip(archive, "17")
        candidate_profile._write_cached_scrutins("17", scrutins, index_acteur)
        acteur = next(iter(index_acteur))
        with (
            patch("candidate_profile.AN_SCRUTINS_LEGISLATURES", ("17",)),
            patch("candidate_profile.requests.get") as mock_get,
        ):
            votes, _ = candidate_profile.fetch_votes_officiels(
                f"https://www.assemblee-nationale.fr/dyn/deputes/{acteur}"
            )
    mock_get.assert_not_called()
    assert votes[0]["type_vote"] == "motion_censure"

    profil = _profil_brut_avec_votes(votes)
    vote_publie = profil["votes"][0]
    assert vote_publie["type_vote"] == "motion_censure"
    assert vote_publie["type_scrutin"] == "motion_censure"

    index, _ = scrutins_index.construire_index(profil["votes"])
    scrutin = index.get("an:17:842")
    assert scrutin["type_vote"] == "motion_censure"
    assert scrutin["texte_lie_non_resolu"]["motif"]
    assert validate_scrutins_index({
        "schema_version": SCRUTINS_SCHEMA_VERSION, "scrutins": index.liste(),
    }) == []


def _profil_brut_avec_votes(votes):
    """Profil brut construit sur des votes officiels déjà collectés — mêmes
    doublures que `tests/test_votes_multi_legislature.py`."""
    identite_an = {
        "nom_complet": "Jean Dupont", "mandat_debut": "2024-07-18", "mandat_fin": None,
        "groupe_sigle": "RE", "groupe_nom": "Renaissance",
    }
    with (
        patch("candidate_profile.time.sleep", return_value=None),
        patch("candidate_profile.fetch_interventions_syceron", return_value=[]),
        patch("candidate_profile.fetch_questions_officielles", return_value=[]),
        patch("candidate_profile.fetch_identite_officielle_par_slug",
              return_value=(identite_an, "PA123456")),
        patch("candidate_profile._extract_mandats_officiels", return_value=[]),
        patch("candidate_profile.fetch_positions_hemicycle_officielles", return_value=[]),
        patch("candidate_profile.fetch_textes_portes_officiels", return_value=[]),
        patch("candidate_profile.fetch_amendements_officiels", return_value=[]),
        patch("candidate_profile.fetch_votes_officiels", return_value=(votes, ["17"])),
    ):
        return candidate_profile.build_profile("deputes", "jean-dupont", skip_interventions=True)


# ---------------------------------------------------------------------------
# Le maillon intermédiaire : la fusion (#639, rang 1, réouverture du 31/08/2026)
# ---------------------------------------------------------------------------
#
# Le rang 1 avait traité les deux bouts qu'il possédait — le parseur d'archives
# et les index figés — et `candidate_profile` recopie bien les trois champs dans
# le vote qu'il écrit. Le run 33395056902 a pourtant republié
# `type_scrutin: null` sur les 17 748 scrutins, et 1 016 / 1 016 votes bruts de
# `jean-luc-melenchon` sans le champ (relevé à `4dda4d52`).
#
# Cause : `merge_raw_profile` fusionne `votes[]` en ADDITIF PUR — l'entrée
# ancienne gagne, et sa clé `(numero_scrutin, date)` ne contient pas les champs
# neufs. Le profil brut ne pouvait donc jamais les acquérir, et
# `build_scrutins_index.py`, qui le lit, ne pouvait que publier `null`.
#
# Rien n'avait échoué : chaque étape faisait ce qu'elle promet. C'est la
# transition qui perdait la donnée — le motif exact de #641, le même jour.

from merge_profile import (  # noqa: E402
    CHAMPS_QUALIFICATION_VOTE,
    _pivot_vote_key,
    _vote_key,
    backfill_vote_qualification,
    merge_raw_profile,
)

#: Le vote tel qu'il a été collecté AVANT #639 : sept clés, aucune
#: qualification. Forme relevée verbatim sur `raw_data/profiles` à `4dda4d52`.
VOTE_AVANT_639 = {
    "date": "2025-02-19", "titre": "la motion de censure", "position": "pour",
    "numero_scrutin": "842", "sort": "l'Assemblée nationale n'a pas adopté",
    "legislature": "17",
    "url_source": "https://www.assemblee-nationale.fr/dyn/17/scrutins/842",
}


def _vote_apres_639(**remplacements):
    """Le même vote, tel que `candidate_profile` l'écrit depuis #639."""
    return {**VOTE_AVANT_639, "type_scrutin": "motion_censure",
            "type_vote": "motion_censure",
            "demandeur": "Président du groupe La France insoumise",
            **remplacements}


def _profil_brut(votes):
    return {"slug": "un-depute", "chambre": "deputes", "nom": "Un Député",
            "identite": {"nom_complet": "Un Député"}, "mandats": [], "votes": votes,
            "dossiers_legislatifs": [], "interventions": [], "amendements": [],
            "meta": {"genere_le": "2026-08-31T13:00:00+0000"}}


def test_la_qualification_atteint_un_vote_deja_collecte():
    """Le maillon manquant, isolé : sans report, l'entrée ancienne gagne telle
    quelle et les trois champs n'entrent jamais dans le profil brut."""
    fusionne = merge_raw_profile(
        _profil_brut([dict(VOTE_AVANT_639)]), _profil_brut([_vote_apres_639()])
    )
    vote = fusionne["votes"][0]
    assert vote["type_scrutin"] == "motion_censure"
    assert vote["type_vote"] == "motion_censure"
    assert vote["demandeur"] == "Président du groupe La France insoumise"


def test_le_report_ne_change_pas_la_cle_de_fusion():
    """Le garde-fou de #668 : ajouter des champs à un vote ne doit toucher ni
    `_vote_key` ni `_pivot_vote_key`, sinon le même vote se republie deux fois
    (468 doublons sur 940 entrées de `textes_portes`)."""
    fusionne = merge_raw_profile(
        _profil_brut([dict(VOTE_AVANT_639)]), _profil_brut([_vote_apres_639()])
    )
    assert len(fusionne["votes"]) == 1
    assert _vote_key(fusionne["votes"][0]) == _vote_key(VOTE_AVANT_639)
    # Côté pivot, la clé est `scrutin_id` : la qualification n'y figure pas.
    mapping = {"scrutin_id": "an:17:842", "position": "pour"}
    assert _pivot_vote_key(mapping) == "an:17:842"


def test_le_report_necrase_jamais_une_qualification_deja_posee():
    """Strictement croissant en information — comme `backfill_mandat_chambre`."""
    ancien = _vote_apres_639(type_scrutin="solennel", type_vote="vote_texte",
                             demandeur="Conférence des présidents")
    fusionne = merge_raw_profile(_profil_brut([ancien]), _profil_brut([_vote_apres_639()]))
    vote = fusionne["votes"][0]
    assert (vote["type_scrutin"], vote["type_vote"], vote["demandeur"]) == (
        "solennel", "vote_texte", "Conférence des présidents"
    )


def test_le_report_ne_touche_aucun_autre_champ():
    """La fusion additive n'est pas une fusion champ par champ : seuls les trois
    champs nommés circulent."""
    ancien = {**VOTE_AVANT_639, "position": "abstention", "sort": "ancien sort"}
    fusionne = merge_raw_profile(
        _profil_brut([ancien]),
        _profil_brut([_vote_apres_639(position="pour", sort="nouveau sort")]),
    )
    vote = fusionne["votes"][0]
    assert vote["position"] == "abstention"
    assert vote["sort"] == "ancien sort"


def test_un_vote_neuf_reste_ajoute():
    """Le report ne remplace pas l'additivité, il la complète."""
    neuf = _vote_apres_639(numero_scrutin="843", date="2025-02-20")
    fusionne = merge_raw_profile(
        _profil_brut([dict(VOTE_AVANT_639)]), _profil_brut([_vote_apres_639(), neuf])
    )
    assert {v["numero_scrutin"] for v in fusionne["votes"]} == {"842", "843"}


def test_les_champs_reportes_sont_ceux_que_lindex_republie():
    """Reporter un champ que l'index de scrutins ne lit pas ne servirait à rien,
    et en oublier un le laisserait `null` pour toujours."""
    assert set(CHAMPS_QUALIFICATION_VOTE) <= set(scrutins_index.CHAMPS_SCRUTIN)
    assert set(CHAMPS_QUALIFICATION_VOTE) == {"type_scrutin", "type_vote", "demandeur"}


def test_un_vote_sans_qualification_ne_reporte_rien():
    ancien = [dict(VOTE_AVANT_639)]
    assert backfill_vote_qualification(ancien, [dict(VOTE_AVANT_639)], _vote_key) == ancien


# --- Le second maillon : le défaut `vote_texte` de l'index ------------------

def test_type_vote_na_plus_de_defaut_dans_lindex():
    """`_valeur_scrutin` repliait `type_vote` sur « vote_texte ». Comme
    `construire_index` ne complète une occurrence suivante que sur un champ resté
    `None`, la PREMIÈRE occurrence non qualifiée d'un scrutin verrouillait le
    repli : une motion de censure votée par un profil régénéré et par un profil
    qui ne l'est pas serait restée publiée sous le type d'un vote sur texte."""
    index, _ = scrutins_index.construire_index([
        # Le votant non régénéré arrive en premier.
        {**VOTE_AVANT_639, "position": "contre"},
        _vote_apres_639(),
    ])
    scrutin = index.get("an:17:842")
    assert scrutin["type_vote"] == "motion_censure"
    assert scrutin["type_scrutin"] == "motion_censure"
    assert scrutin["texte_lie_non_resolu"]["motif"]


def test_un_scrutin_que_personne_ne_qualifie_sort_null():
    """Et non « vote_texte » : la source ne l'a pas dit (§2 règle 5). La valeur
    déjà publiée est conservée par `merge_scrutins_index`, jamais régressée."""
    index, _ = scrutins_index.construire_index([{**VOTE_AVANT_639, "position": "pour"}])
    assert index.get("an:17:842")["type_vote"] is None

    publie = scrutins_index.ScrutinsIndex({"an:17:842": {
        "id": "an:17:842", "legislature": "17", "numero_scrutin": "842",
        "legislature_provenance": "collectee", "date": "2025-02-19",
        "texte": "la motion de censure", "sort": None, "type_scrutin": None,
        "type_vote": "vote_texte", "texte_lie_id": None, "source_url": None,
    }})
    fusion = scrutins_index.merge_scrutins_index(publie, index)
    assert fusion.get("an:17:842")["type_vote"] == "vote_texte"


def test_la_qualification_traverse_la_fusion_jusqua_lindex_publie(tmp_path):
    """La chaîne ENTIÈRE, sur la motion de censure du 19/02/2025 réduite
    verbatim, avec l'étape qui manquait : un profil brut DÉJÀ PUBLIÉ, collecté
    avant #639, que la régénération doit requalifier."""
    archive = _zip_par_fichier(tmp_path, ("VTANR5L17V842",))
    with patch("candidate_profile.SCRUTINS_CACHE_DIR", tmp_path / "cache"):
        scrutins, index_acteur = _parse_scrutins_zip(archive, "17")
        candidate_profile._write_cached_scrutins("17", scrutins, index_acteur)
        acteur = next(iter(index_acteur))
        with (
            patch("candidate_profile.AN_SCRUTINS_LEGISLATURES", ("17",)),
            patch("candidate_profile.requests.get") as mock_get,
        ):
            votes, _ = candidate_profile.fetch_votes_officiels(
                f"https://www.assemblee-nationale.fr/dyn/deputes/{acteur}"
            )
    mock_get.assert_not_called()

    neuf = _profil_brut_avec_votes(votes)
    # Le profil déjà publié : les mêmes votes, sans les trois champs.
    deja_publie = {**neuf, "votes": [
        {c: v[c] for c in v if c not in CHAMPS_QUALIFICATION_VOTE} for v in neuf["votes"]
    ]}
    assert all("type_vote" not in v for v in deja_publie["votes"])

    fusionne = merge_raw_profile(deja_publie, neuf)
    assert len(fusionne["votes"]) == len(deja_publie["votes"])
    assert fusionne["votes"][0]["type_vote"] == "motion_censure"

    index, _ = scrutins_index.construire_index(fusionne["votes"])
    scrutin = index.get("an:17:842")
    assert scrutin["type_vote"] == "motion_censure"
    assert scrutin["type_scrutin"] == "motion_censure"
    assert validate_scrutins_index({
        "schema_version": SCRUTINS_SCHEMA_VERSION, "scrutins": index.liste(),
    }) == []
