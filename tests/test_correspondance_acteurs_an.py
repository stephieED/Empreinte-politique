"""La correspondance slug ↔ acteur AN est un artefact relu, pas une heuristique (#525).

Ces tests tiennent trois choses :

  1. les **10 cas durs** — ceux que la correspondance par nom ne résout pas —
     sont nommés un par un, avec leur verdict attendu (résolu / homonymie
     tranchée / hors AN). Mesuré sur les 476 profils publiés et les 3 119
     acteurs d'AMO30 : **466 résolus, 10 non résolus** ;
  2. une résolution non trouvée **échoue en nommant le slug**, et un slug sans
     acteur AN est **déclaré** (`jordan-bardella`) et non absent ;
  3. le quality gate refuse le commit d'un profil publié sans correspondance,
     en le nommant.

Tout tourne sur `tests/fixtures/correspondance_acteurs_an_extrait.json`,
extraite de la table réelle : aucun accès à AMO30, aucune lecture de
`pivot_data/` ni de `raw_data/profiles/` (AGENTS.md §3). La fixture porte les
10 cas durs **et** deux témoins résolus par la seule correspondance de nom —
une fixture qui ne décrirait que l'exception ne dirait rien du cas courant,
le piège de `syceron_minimal.xml` (#510).
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import correspondance_acteurs_an as corr  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "correspondance_acteurs_an_extrait.json"


@pytest.fixture(autouse=True)
def _memo_propre():
    """La mémoïsation est par chemin, mais deux tests peuvent réécrire le même
    fichier temporaire : on repart d'une table vide à chaque cas."""
    corr.vider_memo()
    yield
    corr.vider_memo()


def _table_temporaire(tmp_path, correspondances, **entetes):
    document = {
        "schema_version": corr.SCHEMA_VERSION,
        "genere_le": "2026-08-26T00:00:00+0000",
        "source_referentiel": "https://data.assemblee-nationale.fr/",
        "correspondances": correspondances,
    }
    document.update(entetes)
    chemin = tmp_path / "table.json"
    chemin.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    return chemin


def _entree(**champs):
    base = {
        "acteur_ref": "PA1",
        "etat_civil": {"nom_complet": "Témoin"},
        "ecart": None,
        "motif": None,
        "preuve": "https://www2.assemblee-nationale.fr/deputes/fiche/OMC_PA1",
        "verifie_le": "2026-08-26",
    }
    base.update(champs)
    return base


# --------------------------------------------------------------------------
# 1. Les 10 cas durs, chacun nommé, avec son verdict
# --------------------------------------------------------------------------

#: (slug, acteur_ref attendu, écart attendu). Ce sont les 10 slugs sur 476 que
#: `_resolve_acteur_ref_par_slug` laisse non résolus — les seuls que la table
#: existe pour trancher.
CAS_DURS = [
    # Homonymie réelle : deux députées en exercice. L'AN ne les distingue que
    # par le département inscrit dans l'état civil, ce qu'aucune normalisation
    # de slug ne peut deviner.
    ("alexandra-martin", "PA793342", "homonymie"),
    ("alexandra-martin-1", "PA793944", "homonymie"),
    # Apostrophe : le slug la remplace par un tiret, la normalisation par un
    # espace ; la clé du référentiel garde l'apostrophe.
    ("christelle-d-intorni", "PA793322", "apostrophe"),
    ("loic-prud-homme", "PA719578", "apostrophe"),
    # Nom d'usage / particule : l'état civil AN et le slug NosDéputés divergent.
    ("christelle-petex-levet", "PA721442", "nom_divergent"),
    ("claire-pitollat", "PA718910", "nom_divergent"),
    ("emmanuel-tache-de-la-pagerie", "PA793382", "nom_divergent"),
    ("sabrina-agresti-roubache", "PA793278", "nom_divergent"),
    # Changement de nom en cours de carrière : l'uid AMO30 n'a pas bougé, la
    # correspondance par nom ne retombe plus sur ses pieds.
    ("guillaume-gouffier-cha", "PA721296", "nom_divergent"),
    # Hors AN : député européen, aucun acteur AMO30. Déclaré, pas absent.
    ("jordan-bardella", None, "hors_an"),
]


@pytest.mark.parametrize("slug, acteur_ref, ecart", CAS_DURS, ids=[c[0] for c in CAS_DURS])
def test_chaque_cas_dur_porte_son_verdict(slug, acteur_ref, ecart):
    table = corr.charger_correspondance(FIXTURE)
    assert slug in table, f"{slug} absent de la table : le cas dur n'est plus couvert"
    assert table[slug]["acteur_ref"] == acteur_ref
    assert table[slug]["ecart"] == ecart
    assert corr.resoudre_acteur_ref(slug, FIXTURE) == acteur_ref


@pytest.mark.parametrize("slug, _ref, _ecart", CAS_DURS, ids=[c[0] for c in CAS_DURS])
def test_chaque_cas_dur_porte_sa_preuve_et_son_motif(slug, _ref, _ecart):
    """Un cas dur sans preuve relue serait la même heuristique, déplacée d'un cran."""
    entree = corr.charger_correspondance(FIXTURE)[slug]
    assert entree["preuve"].startswith("http")
    assert entree["motif"] and entree["motif"].strip()
    assert entree["verifie_le"] == "2026-08-26"


def test_lhomonymie_est_tranchee_vers_deux_acteurs_distincts():
    """Le point de l'arbitrage : deux slugs, deux personnes, deux `PA`.

    Les rapprocher du même acteur publierait deux profils pour une personne et
    en laisserait une sans données — sans qu'aucun compteur ne bouge.
    """
    table = corr.charger_correspondance(FIXTURE)
    une = table["alexandra-martin"]
    autre = table["alexandra-martin-1"]
    assert une["acteur_ref"] != autre["acteur_ref"]
    assert une["etat_civil"]["date_naissance"] != autre["etat_civil"]["date_naissance"]
    # L'AN désambiguïse par le département, dans l'état civil lui-même.
    assert "Alpes-Maritimes" in une["etat_civil"]["nom_complet"]
    assert "Gironde" in autre["etat_civil"]["nom_complet"]


def test_les_temoins_resolus_par_le_nom_sont_aussi_dans_la_table():
    """La table couvre les 476, pas seulement les 10 : les entrées sans écart
    portent `ecart: null` et `motif: null`, et restent prouvées."""
    table = corr.charger_correspondance(FIXTURE)
    temoin = table["adrien-quatennens"]
    assert temoin["ecart"] is None
    assert temoin["motif"] is None
    assert temoin["acteur_ref"] == "PA720422"
    assert temoin["preuve"].endswith("OMC_PA720422")


def test_melenchon_est_couvert_malgre_une_identite_pivot_vide():
    """`jean-luc-melenchon` est publié sans `identite` : son `acteur_ref` ne se
    lit dans aucun `source_url`. Il est dans la table quand même — c'est
    exactement ce qu'un artefact relu apporte sur une heuristique."""
    assert corr.resoudre_acteur_ref("jean-luc-melenchon", FIXTURE) == "PA2150"


# --------------------------------------------------------------------------
# 2. Échec bruyant, et trou déclaré
# --------------------------------------------------------------------------

def test_un_slug_absent_echoue_en_le_nommant():
    with pytest.raises(corr.CorrespondanceIntrouvable) as exc:
        corr.resoudre_acteur_ref("depute-jamais-vu", FIXTURE, strict=True)
    assert "depute-jamais-vu" in str(exc.value)


def test_un_slug_absent_ne_leve_pas_hors_mode_strict():
    """Le mode non strict est celui de la collecte : un membre de roster
    nouvellement élu n'a par construction aucune entrée relue, et doit pouvoir
    retomber sur la correspondance par nom."""
    assert corr.resoudre_acteur_ref("depute-jamais-vu", FIXTURE) is None


def test_hors_an_est_declare_et_se_distingue_dun_slug_absent():
    """`None` des deux côtés, mais deux faits opposés : « vérifié sans acteur
    AN » et « jamais relu ». Un trou muet est ce qui a produit #510 et #501."""
    assert corr.resoudre_acteur_ref("jordan-bardella", FIXTURE) is None
    assert corr.resoudre_acteur_ref("jordan-bardella", FIXTURE, strict=True) is None
    assert corr.est_declare_hors_an("jordan-bardella", FIXTURE) is True
    assert corr.est_declare_hors_an("depute-jamais-vu", FIXTURE) is False


def test_hors_an_porte_un_motif_ecrit():
    entree = corr.charger_correspondance(FIXTURE)["jordan-bardella"]
    assert entree["acteur_ref"] is None
    assert "européen" in entree["motif"]
    assert entree["preuve"].startswith("https://www.europarl.europa.eu/")


def test_slugs_non_couverts_nomme_ce_qui_manque():
    manquants = corr.slugs_non_couverts(
        ["adrien-quatennens", "jordan-bardella", "zoe-inconnue", "abel-inconnu"], FIXTURE
    )
    assert manquants == ["abel-inconnu", "zoe-inconnue"]


# --------------------------------------------------------------------------
# 3. Ce que la validation refuse (chaque règle a coûté quelque chose ailleurs)
# --------------------------------------------------------------------------

def test_une_table_absente_echoue_en_nommant_le_fichier(tmp_path):
    with pytest.raises(corr.CorrespondanceInvalide) as exc:
        corr.charger_correspondance(tmp_path / "nulle-part.json")
    assert "nulle-part.json" in str(exc.value)


def test_une_autre_version_de_schema_est_refusee(tmp_path):
    chemin = _table_temporaire(tmp_path, {"a-b": _entree()}, schema_version="v0")
    with pytest.raises(corr.CorrespondanceInvalide, match="schema_version"):
        corr.charger_correspondance(chemin)


def test_deux_slugs_sur_le_meme_acteur_sont_refuses(tmp_path):
    """Deux profils publiés pour une seule personne — rien d'autre ne le verrait."""
    chemin = _table_temporaire(
        tmp_path, {"a-b": _entree(acteur_ref="PA42"), "c-d": _entree(acteur_ref="PA42")}
    )
    with pytest.raises(corr.CorrespondanceInvalide, match="PA42"):
        corr.charger_correspondance(chemin)


def test_un_ecart_sans_motif_est_refuse(tmp_path):
    chemin = _table_temporaire(tmp_path, {"a-b": _entree(ecart="apostrophe", motif=None)})
    with pytest.raises(corr.CorrespondanceInvalide, match="motif"):
        corr.charger_correspondance(chemin)


def test_un_ecart_inconnu_est_refuse(tmp_path):
    chemin = _table_temporaire(tmp_path, {"a-b": _entree(ecart="au-pif", motif="x")})
    with pytest.raises(corr.CorrespondanceInvalide, match="ecart inconnu"):
        corr.charger_correspondance(chemin)


def test_une_entree_sans_preuve_est_refusee(tmp_path):
    chemin = _table_temporaire(tmp_path, {"a-b": _entree(preuve=None)})
    with pytest.raises(corr.CorrespondanceInvalide, match="preuve"):
        corr.charger_correspondance(chemin)


def test_un_acteur_null_sans_declaration_hors_an_est_refuse(tmp_path):
    """L'absence d'acteur doit être un fait déclaré, jamais un champ oublié."""
    chemin = _table_temporaire(tmp_path, {"a-b": _entree(acteur_ref=None)})
    with pytest.raises(corr.CorrespondanceInvalide, match="hors_an"):
        corr.charger_correspondance(chemin)


def test_hors_an_avec_un_acteur_ref_est_refuse(tmp_path):
    chemin = _table_temporaire(
        tmp_path, {"a-b": _entree(acteur_ref="PA7", ecart="hors_an", motif="x")}
    )
    with pytest.raises(corr.CorrespondanceInvalide, match="hors_an"):
        corr.charger_correspondance(chemin)


def test_un_acteur_ref_mal_formé_est_refuse(tmp_path):
    chemin = _table_temporaire(tmp_path, {"a-b": _entree(acteur_ref="847629")})
    with pytest.raises(corr.CorrespondanceInvalide, match="acteur_ref"):
        corr.charger_correspondance(chemin)


def test_une_date_de_verification_invalide_est_refusee(tmp_path):
    chemin = _table_temporaire(tmp_path, {"a-b": _entree(verifie_le="hier")})
    with pytest.raises(corr.CorrespondanceInvalide, match="verifie_le"):
        corr.charger_correspondance(chemin)


def test_un_slug_commencant_par_un_point_est_refuse(tmp_path):
    """`Path.glob` renvoie les dotfiles : `.generation_checkpoint` a déjà été
    lu comme un profil et a coûté le commit de 476 profils corrects (#518)."""
    chemin = _table_temporaire(tmp_path, {".generation_checkpoint": _entree()})
    with pytest.raises(corr.CorrespondanceInvalide, match="slug invalide"):
        corr.charger_correspondance(chemin)


def test_le_memo_est_keye_par_chemin(tmp_path):
    """Deux tables chargées dans le même processus ne se contaminent pas — le
    piège qui a fait revenir #377 (AGENTS.md §5)."""
    une = _table_temporaire(tmp_path, {"a-b": _entree(acteur_ref="PA1")})
    autre_dir = tmp_path / "autre"
    autre_dir.mkdir()
    autre = _table_temporaire(autre_dir, {"a-b": _entree(acteur_ref="PA2")})
    assert corr.resoudre_acteur_ref("a-b", une) == "PA1"
    assert corr.resoudre_acteur_ref("a-b", autre) == "PA2"
    assert corr.resoudre_acteur_ref("a-b", une) == "PA1"


# --------------------------------------------------------------------------
# 4. La table passe devant la correspondance par nom
# --------------------------------------------------------------------------

import candidate_profile as cp  # noqa: E402
import check_quality_gate as gate  # noqa: E402


@pytest.fixture
def _table_par_defaut(monkeypatch):
    """Branche la fixture comme table par défaut du processus."""
    monkeypatch.setattr(corr, "CHEMIN_PAR_DEFAUT", FIXTURE)
    monkeypatch.setattr(cp, "_CORRESPONDANCE_INDISPONIBLE_SIGNALEE", False)


def test_la_table_prime_sur_la_correspondance_par_nom(monkeypatch, _table_par_defaut):
    """Une table relue n'est pas un repli : elle tranche avant l'heuristique."""
    monkeypatch.setattr(cp, "_build_acteur_nom_index", lambda: {"loic prud homme": ["PA666"]})
    assert cp._resolve_acteur_ref_par_slug("loic-prud-homme") == "PA719578"


def test_un_hors_an_declare_ne_retombe_pas_sur_le_nom(monkeypatch, _table_par_defaut):
    """Le cas qui distingue une table d'un cache : `jordan-bardella` est vérifié
    sans acteur AN. Même si l'index de noms proposait un acteur, la déclaration
    l'emporte — sinon un député européen se verrait attribuer des votes AN."""
    monkeypatch.setattr(cp, "_build_acteur_nom_index", lambda: {"jordan bardella": ["PA999"]})
    assert cp._resolve_acteur_ref_par_slug("jordan-bardella") is None


def test_un_slug_absent_de_la_table_retombe_sur_le_nom(monkeypatch, _table_par_defaut):
    """Le roster grossit à chaque run : un élu neuf n'a aucune entrée relue et
    doit rester collectable."""
    monkeypatch.setattr(cp, "_build_acteur_nom_index", lambda: {"elue neuve": ["PA1234"]})
    assert cp._resolve_acteur_ref_par_slug("elue-neuve") == "PA1234"


def test_lhomonymie_reste_refusee_par_le_repli(monkeypatch, _table_par_defaut):
    monkeypatch.setattr(cp, "_build_acteur_nom_index", lambda: {"deux fois": ["PA1", "PA2"]})
    assert cp._resolve_acteur_ref_par_slug("deux-fois") is None


def test_utiliser_table_false_court_circuite_la_table(monkeypatch, _table_par_defaut):
    """Ce dont `build_correspondance_acteurs_an.py` a besoin : construire la
    table sans la relire."""
    monkeypatch.setattr(cp, "_build_acteur_nom_index", lambda: {"loic prud homme": ["PA666"]})
    assert cp._resolve_acteur_ref_par_slug("loic-prud-homme", utiliser_table=False) == "PA666"


def test_une_table_absente_est_un_repli_declare(monkeypatch, tmp_path, capsys):
    """Absente, la table ne fait pas échouer la collecte — mais elle le dit. Le
    contrôle dur de couverture appartient au gate, pas au chemin de collecte
    (même ligne que le repli déclaré de #493)."""
    monkeypatch.setattr(corr, "CHEMIN_PAR_DEFAUT", tmp_path / "absente.json")
    monkeypatch.setattr(cp, "_CORRESPONDANCE_INDISPONIBLE_SIGNALEE", False)
    monkeypatch.setattr(cp, "_build_acteur_nom_index", lambda: {"loic prud homme": ["PA666"]})
    assert cp._resolve_acteur_ref_par_slug("loic-prud-homme") == "PA666"
    sortie = capsys.readouterr().out
    assert "absente.json" in sortie
    assert "Repli sur la correspondance par nom" in sortie


# --------------------------------------------------------------------------
# 5. Le quality gate bloque le commit, en nommant le slug
# --------------------------------------------------------------------------

def _profils(tmp_path, slugs, avec_checkpoint=False):
    repertoire = tmp_path / "pivots"
    repertoire.mkdir()
    for slug in slugs:
        (repertoire / f"{slug}.pivot.json").write_text("{}", encoding="utf-8")
    if avec_checkpoint:
        (repertoire / ".generation_checkpoint.pivot.json").write_text("{}", encoding="utf-8")
    return repertoire


def test_le_gate_passe_quand_tout_profil_publie_est_couvert(tmp_path):
    repertoire = _profils(tmp_path, ["adrien-quatennens", "jordan-bardella"])
    durs, console, _ = gate._report_correspondance_acteurs(repertoire, FIXTURE)
    assert durs == []
    assert "Tout profil publié porte sa correspondance relue" in console


def test_le_gate_bloque_et_nomme_le_slug_non_couvert(tmp_path):
    repertoire = _profils(tmp_path, ["adrien-quatennens", "elue-neuve"])
    durs, console, md = gate._report_correspondance_acteurs(repertoire, FIXTURE)
    assert len(durs) == 1
    assert "elue-neuve" in durs[0]
    assert "elue-neuve" in console and "elue-neuve" in md


def test_le_gate_compte_le_hors_an_comme_couvert(tmp_path):
    """Un trou déclaré n'est pas un trou (AGENTS.md §2 règle 5)."""
    repertoire = _profils(tmp_path, ["jordan-bardella"])
    durs, console, _ = gate._report_correspondance_acteurs(repertoire, FIXTURE)
    assert durs == []
    assert "Sans acteur AN (déclaré) : 1" in console


def test_le_gate_ignore_les_dotfiles(tmp_path):
    """`.generation_checkpoint.json` lu comme un profil a coûté un commit (#518)."""
    repertoire = _profils(tmp_path, ["adrien-quatennens"], avec_checkpoint=True)
    durs, _, _ = gate._report_correspondance_acteurs(repertoire, FIXTURE)
    assert durs == []


def test_une_entree_sans_profil_publie_ne_bloque_pas(tmp_path):
    """La table a le droit de survivre à un profil retiré du corpus, comme un
    index partagé survit à son référent (#485)."""
    repertoire = _profils(tmp_path, ["adrien-quatennens"])
    durs, console, _ = gate._report_correspondance_acteurs(repertoire, FIXTURE)
    assert durs == []
    assert "entrée(s) sans profil publié" in console


def test_le_gate_bloque_sur_une_table_illisible(tmp_path):
    repertoire = _profils(tmp_path, ["adrien-quatennens"])
    durs, _, _ = gate._report_correspondance_acteurs(repertoire, tmp_path / "absente.json")
    assert len(durs) == 1
    assert "absente.json" in durs[0]
