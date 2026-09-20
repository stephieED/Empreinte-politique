"""Rattachement d'un amendement à son dossier législatif (issue #639, rang 3).

DEUX DÉFAUTS, UN SEUL LOT.

1. **La clé sourcée était écrasée avant d'être écrite.**
   `candidate_profile.fetch_amendements_officiels` résolvait le `texte_vise`
   d'un amendement — l'uid du document AN amendé, `PRJLANR5L15B1088` — en titre
   du dossier, puis **remplaçait le code par le titre** dans l'enregistrement
   brut. Mesuré le 31/08/2026 sur `pivot_data/amendements/` : 293 582 des
   484 132 amendements publiés (60,6 %) ne portent plus qu'un libellé, sans
   aucune clé. La perte est infligée par le pipeline, pas subie de la source.

2. **La brique qui joint le texte au dossier n'avait jamais été ouverte.**
   `json/document/*.json` des archives de dossiers porte `dossierRef` sur
   21 936 de ses 21 937 uid distincts (0 divergence entre les trois archives).
   `docs/sources/an-opendata.md` les décrivait comme « sans rapport, à filtrer »
   depuis le spike #207.

CE QUE CES TESTS VERROUILLENT. Que la jointure se fasse d'uid à uid et jamais
par libellé (AGENTS.md §2 règle 2) ; qu'un texte non résolu reste sans dossier
et se compte (§2 règle 5) ; qu'une table vide n'efface pas un rattachement déjà
publié ; et que le `dossier_id` vive **une fois par texte** et non une fois par
amendement — l'encodage est un choix mesuré, pas un détail (0,10 Mio contre
5,7 Mio sur les quatre fichiers d'index).

FIXTURES. Réductions verbatim de l'archive réelle
`.../17/loi/dossiers_legislatifs/Dossiers_Legislatifs.json.zip`
(`tests/fixtures/dossiers_an/`) : un document et son dossier, plus le seul
document des trois archives dépourvu de `dossierRef` — un texte supprimé, qui
ne porte que son `dateSuppression`. Aucune valeur n'est inventée (leçon de
#510).
"""

import json
import sys
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import textes_dossiers_an  # noqa: E402
from amendements_index import (  # noqa: E402
    AmendementsIndex,
    charger,
    ecrire,
    merge_amendements_index,
    resoudre_textes,
)
from candidate_profile import fetch_amendements_officiels  # noqa: E402
from schema_pivot import validate_amendements_index  # noqa: E402
from textes_dossiers_an import charger_table, construire_table  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures" / "dossiers_an"

#: Un texte réellement amendé et son dossier, verbatim.
TEXTE = "PIONANR5L17BTC0699"
DOSSIER = "DLR5L17N50879"
TITRE = "Pour plus de sport et moins de sucre"

#: Le seul document des trois archives sans `dossierRef` : un texte supprimé.
TEXTE_SUPPRIME = "PIONANR5L17BTC2806"

#: Réduction verbatim d'une entrée de `raw_data/amendements_an_figes/15/` :
#: `texte_vise` y est bien le code source, jamais un libellé.
AMENDEMENT_FIGE = {
    "uid": "AMANR5L15PO757134B1088P0D1N000396",
    "texte_vise": "PRJLANR5L15B1088",
    "sort": "retiré",
    "base_juridique_irrecevabilite": None,
    "premier_signataire": "an:PA942",
    "co_signataires": ["an:PA642868"],
    "type_deposant": "depute",
    "date": "2018-08-09",
    "numero": "396",
    "source_url": None,
}


@pytest.fixture(autouse=True)
def _purge_memo():
    textes_dossiers_an.vider_memo()
    yield
    textes_dossiers_an.vider_memo()


def _archive(chemin: Path, entrees: list[tuple[str, str]]) -> Path:
    """Reconstruit une archive au format AN à partir des fixtures verbatim."""
    with zipfile.ZipFile(chemin, "w") as zf:
        for arcname, fichier in entrees:
            zf.writestr(arcname, (FIXTURES / fichier).read_bytes())
    return chemin


def _archive_17(tmp_path: Path, nom: str = "dossiers.zip") -> Path:
    return _archive(tmp_path / nom, [
        (f"json/document/{TEXTE}.json", f"document_{TEXTE}.json"),
        (f"json/document/{TEXTE_SUPPRIME}.json", f"document_{TEXTE_SUPPRIME}.json"),
        (f"json/dossierParlementaire/{DOSSIER}.json", f"dossier_{DOSSIER}.json"),
    ])


# ---------------------------------------------------------------------------
# La table : d'uid à uid, jamais par libellé
# ---------------------------------------------------------------------------

def test_la_table_joint_le_document_a_son_dossier(tmp_path):
    """`document.dossierRef` est la seule clé sourcée qui rattache un texte
    déposé à son dossier. Le titre l'accompagne pour que le libellé lisible ne
    soit pas perdu — il vivait recopié dans chaque `texte_vise`."""
    table = construire_table([(17, _archive_17(tmp_path))])

    assert table[TEXTE] == {"dossier_id": DOSSIER, "titre": TITRE}


def test_un_document_sans_dossier_declare_na_pas_dentree(tmp_path):
    """Le texte supprimé ne porte que son `dateSuppression` : il ne se voit pas
    attribuer un dossier par défaut (AGENTS.md §2 règle 5)."""
    table = construire_table([(17, _archive_17(tmp_path))])

    assert TEXTE_SUPPRIME not in table


def test_un_document_dans_deux_archives_est_lu_une_fois(tmp_path):
    """Les documents traînent d'une archive à l'autre. L'arbitrage est celui de
    `iter_dossiers_bruts` — législature la plus élevée — et il ne dépend pas de
    l'ordre d'appel. 0 divergence de `dossierRef` mesurée sur les 21 937 uid."""
    ancienne = _archive_17(tmp_path, "dossiers_16.zip")
    recente = _archive_17(tmp_path, "dossiers.zip")

    table = construire_table([(16, ancienne), (17, recente)])
    inverse = construire_table([(17, recente), (16, ancienne)])

    assert table == inverse == {TEXTE: {"dossier_id": DOSSIER, "titre": TITRE}}


def test_archives_absentes_rendent_une_table_vide_sans_lever(tmp_path):
    """Une archive illisible n'interrompt pas la construction : l'appelant en
    fait une absence de rattachement comptée, jamais une exception."""
    (tmp_path / "vide.zip").write_bytes(b"pas un zip")

    assert construire_table([(17, tmp_path / "vide.zip")]) == {}


def test_charger_table_sans_telechargement_ne_touche_pas_au_reseau(tmp_path):
    """Sans cache et sans autorisation de télécharger, la table est vide — et
    silencieuse côté réseau, ce que `tests/conftest.py` vérifie de son côté."""
    assert charger_table(cache_dir=tmp_path, telecharger=False) == {}


def test_le_cache_disque_est_keye_sur_son_chemin(tmp_path):
    """Le mémo en process est keyé sur le **chemin** du cache, jamais sur un nom
    logique : les tests remplacent le répertoire par cas, et un mémo global
    ferait fuir la table d'un cas dans le suivant (le piège de #377)."""
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    (a / textes_dossiers_an.NOM_CACHE).write_text(
        json.dumps({TEXTE: {"dossier_id": DOSSIER, "titre": TITRE}}), encoding="utf-8"
    )

    assert charger_table(cache_dir=a, telecharger=False)[TEXTE]["dossier_id"] == DOSSIER
    assert charger_table(cache_dir=b, telecharger=False) == {}


# ---------------------------------------------------------------------------
# La résolution : ce qui est rattaché, et ce qui se compte
# ---------------------------------------------------------------------------

def _index_deux_amendements() -> AmendementsIndex:
    """Un amendement portant son code source, un autre portant un libellé —
    l'état réel du corpus publié, 39,4 % contre 60,6 %."""
    return AmendementsIndex({
        "an:AMANR5L17PO0B1P0D1N1": {"texte_vise": TEXTE, "sort": "adopte"},
        "an:AMANR5L17PO0B1P0D1N2": {"texte_vise": "Pour plus de sport et moins de sucre"},
    })


def test_seul_le_code_source_est_rattache(tmp_path):
    """Le second amendement porte **exactement** le titre du dossier du premier.
    Le rapprocher serait une clé dérivée d'une chaîne : exclu, même à
    l'identique (AGENTS.md §2 règle 2)."""
    index = _index_deux_amendements()
    table = construire_table([(17, _archive_17(tmp_path))])

    comptes = resoudre_textes(index, table)

    assert index.dossier_de(index.get("an:AMANR5L17PO0B1P0D1N1")) == DOSSIER
    assert index.dossier_de(index.get("an:AMANR5L17PO0B1P0D1N2")) is None
    assert comptes == {
        "textes_resolus": 1,
        "textes_sans_dossier": 1,
        "amendements_rattaches": 1,
        "amendements_sans_dossier": 1,
    }


def test_le_dossier_ne_vit_pas_dans_lamendement(tmp_path):
    """L'encodage est le choix du lot : une table de fichier, jamais un champ
    par amendement. 484 132 amendements ne visent que 2 248 textes distincts —
    recopier le `dossier_id` dans chacun coûte 5,7 Mio, la table 0,10."""
    index = _index_deux_amendements()
    resoudre_textes(index, construire_table([(17, _archive_17(tmp_path))]))

    for amendement in index.par_id.values():
        assert "dossier_id" not in amendement
        assert "titre" not in amendement


def test_une_table_vide_neface_pas_un_rattachement_publie():
    """Archives indisponibles : rien n'est ajouté, rien n'est retiré. C'est la
    règle « une collecte vide n'écrase jamais » appliquée à un index dérivé."""
    index = AmendementsIndex(
        {"an:AMANR5L17PO0B1P0D1N1": {"texte_vise": TEXTE}},
        textes={TEXTE: {"dossier_id": DOSSIER, "titre": TITRE}},
    )

    comptes = resoudre_textes(index, {})

    assert index.par_texte[TEXTE]["dossier_id"] == DOSSIER
    assert comptes["amendements_rattaches"] == 1
    assert comptes["textes_resolus"] == 0


def test_un_amendement_sans_texte_vise_reste_sans_dossier():
    index = AmendementsIndex({"an:AMANR5L17PO0B1P0D1N1": {"texte_vise": None}})

    comptes = resoudre_textes(index, {TEXTE: {"dossier_id": DOSSIER, "titre": TITRE}})

    assert comptes["amendements_sans_dossier"] == 1
    assert index.dossier_de({"texte_vise": None}) is None


# ---------------------------------------------------------------------------
# Écriture, relecture, fusion
# ---------------------------------------------------------------------------

def test_chaque_fichier_porte_les_seuls_textes_quil_vise(tmp_path):
    """Un fichier de législature doit se lire seul, sans embarquer les 21 936
    documents des archives."""
    index = AmendementsIndex(
        {
            "an:AMANR5L17PO0B1P0D1N1": {"texte_vise": TEXTE},
            "an:AMANR5L16PO0B1P0D1N1": {"texte_vise": "PIONANR5L16B0097"},
        },
        textes={
            TEXTE: {"dossier_id": DOSSIER, "titre": TITRE},
            "PIONANR5L16B0097": {"dossier_id": "DLR5L15N37420", "titre": None},
        },
    )

    ecrire(tmp_path, index)

    dix_sept = json.loads((tmp_path / "17.json").read_text(encoding="utf-8"))
    seize = json.loads((tmp_path / "16.json").read_text(encoding="utf-8"))
    assert set(dix_sept["textes"]) == {TEXTE}
    assert set(seize["textes"]) == {"PIONANR5L16B0097"}
    assert validate_amendements_index(dix_sept) == []


def test_la_table_survit_a_un_aller_retour_disque(tmp_path):
    index = AmendementsIndex(
        {"an:AMANR5L17PO0B1P0D1N1": {"texte_vise": TEXTE}},
        textes={TEXTE: {"dossier_id": DOSSIER, "titre": TITRE}},
    )
    ecrire(tmp_path, index)

    relu = charger(tmp_path)

    assert relu.dossier_de(relu.get("an:AMANR5L17PO0B1P0D1N1")) == DOSSIER
    assert relu.texte(TEXTE)["titre"] == TITRE


def test_un_index_sans_table_reste_lisible(tmp_path):
    """Les quatre fichiers publiés avant #639 n'ont pas de clé `textes` : les
    relire ne doit ni lever, ni inventer de rattachement."""
    (tmp_path / "17.json").write_text(json.dumps({
        "schema_version": "amendements-v1",
        "legislature": "17",
        "amendements": {"an:AMANR5L17PO0B1P0D1N1": {"texte_vise": TEXTE}},
    }), encoding="utf-8")

    relu = charger(tmp_path)

    assert relu.par_texte == {}
    assert relu.dossier_de(relu.get("an:AMANR5L17PO0B1P0D1N1")) is None


def test_la_fusion_est_additive_sur_les_textes():
    """Un run partiel ne voit qu'une partie des textes : effacer les autres
    laisserait des amendements publiés sans dossier alors qu'il était acquis
    (leçon de #450, transposée à la table)."""
    ancien = AmendementsIndex(
        {"an:AMANR5L17PO0B1P0D1N1": {"texte_vise": TEXTE}},
        textes={TEXTE: {"dossier_id": DOSSIER, "titre": TITRE}},
    )
    nouveau = AmendementsIndex(
        {"an:AMANR5L16PO0B1P0D1N1": {"texte_vise": "PIONANR5L16B0097"}},
        textes={"PIONANR5L16B0097": {"dossier_id": "DLR5L15N37420", "titre": None}},
    )

    fusionne = merge_amendements_index(ancien, nouveau)

    assert set(fusionne.par_texte) == {TEXTE, "PIONANR5L16B0097"}


def test_la_validation_refuse_une_entree_sans_dossier():
    """Un texte sans dossier résolu n'a pas d'entrée du tout : une entrée à
    `dossier_id: null` coûterait des octets pour ne rien dire de plus qu'une
    absence."""
    erreurs = validate_amendements_index({
        "schema_version": "amendements-v1",
        "legislature": "17",
        "textes": {TEXTE: {"titre": TITRE}},
        "amendements": {},
    })

    assert any("dossier_id" in e for e in erreurs)


# ---------------------------------------------------------------------------
# La collecte : le code source n'est plus écrasé
# ---------------------------------------------------------------------------

def test_la_collecte_conserve_le_code_source_du_texte():
    """LE défaut du rang 3. `fetch_amendements_officiels` remplaçait le code par
    le titre du dossier avant l'écriture du profil brut — 293 582 amendements
    publiés en sont restés sans clé."""
    def records(legislature, acteur_ref):
        return [dict(AMENDEMENT_FIGE)] if legislature == "15" else None

    with (
        patch("candidate_profile._read_cached_amendements_acteur", side_effect=records),
        patch("candidate_profile._extract_acteur_ref", return_value="PA942"),
    ):
        amendements = fetch_amendements_officiels(
            "https://www.assemblee-nationale.fr/dyn/deputes/PA942"
        )

    assert [a["texte_vise"] for a in amendements] == ["PRJLANR5L15B1088"]


def test_la_collecte_ne_construit_plus_dindex_de_titres():
    """L'index `code -> titre` a disparu avec son unique appelant : le garder
    aurait laissé l'écrasement à une ligne de distance."""
    import candidate_profile

    assert not hasattr(candidate_profile, "_build_texte_titre_index")


# ---------------------------------------------------------------------------
# Le chemin réellement exécuté en CI
# ---------------------------------------------------------------------------

def _args_index(tmp_path, *, sans_dossiers: bool):
    from types import SimpleNamespace

    return SimpleNamespace(
        skip_amendements_index=False,
        skip_dossiers_legislatifs=sans_dossiers,
        amendements=str(tmp_path),
        no_merge=True,
    )


def test_la_jointure_est_cablee_sur_le_chemin_execute_en_ci(tmp_path):
    """`.github/workflows/generate-data.yml` n'appelle **jamais**
    `build_amendements_index_pivot.py` : le job `merge-and-pivot` passe par
    `generate_all_profiles`. Ne câbler la jointure que dans le CLI l'aurait
    rendue inerte en production, sans qu'un test ne bronche."""
    import generate_all_profiles as gap

    table = {TEXTE: {"dossier_id": DOSSIER, "titre": TITRE}}
    with (
        patch.object(gap, "charger_table_textes", return_value=table) as charge,
        patch.object(gap, "rafraichir_amendements", return_value=AmendementsIndex()) as raf,
    ):
        gap._rafraichir_index_amendements(_args_index(tmp_path, sans_dossiers=False), tmp_path)

    charge.assert_called_once()
    assert raf.call_args.kwargs["table_textes"] == table


def test_un_run_qui_refuse_les_dossiers_ne_les_telecharge_pas_par_la_bande(tmp_path):
    """`--skip-dossiers-legislatifs` est le mode léger du job roster (#357) :
    la jointure ne doit pas y rouvrir les archives que le run refuse."""
    import generate_all_profiles as gap

    with (
        patch.object(gap, "charger_table_textes") as charge,
        patch.object(gap, "rafraichir_amendements", return_value=AmendementsIndex()) as raf,
    ):
        gap._rafraichir_index_amendements(_args_index(tmp_path, sans_dossiers=True), tmp_path)

    charge.assert_not_called()
    assert raf.call_args.kwargs["table_textes"] is None
