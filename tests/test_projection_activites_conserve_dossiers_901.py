"""#901 — le stade d'un texte porté européen traverse la PROJECTION, pas que la fabrique.

Le run `34853965676` (14/09/2026) a publié **12 stades sur 383**, exactement
comme le run d'avant : le correctif de la seconde fabrique n'avait rien changé
au corpus. Les 371 entrées issues des activités sortaient toutes en
`activite_sans_dossier` — **371 sur 371, soit 100 %**.

La cause n'était dans aucune des deux fabriques. `_make_texte_porte_activite`
lit `entree["dossiers"]`, mais `entree` ne vient pas du dump : elle vient de
`build_activities_index`, qui projetait chaque entrée sur six clés — `titre`,
`date`, `reference`, `source_url`, `legislature`, `texte` — et jetait
`dossiers`. Le champ était détruit **une étape avant** l'endroit qu'on corrigeait.

## Pourquoi les tests d'alors ne pouvaient pas le voir

Ils appelaient `_reference_dossier_activite` sur une entrée **fabriquée par le
test**, portant `dossiers`. Ils vérifiaient donc que la fonction sait lire un
champ que la chaîne réelle ne lui remet jamais. C'est le défaut nommé dans
`AGENTS.md` (§Références, #726) : *une fixture décrivant le monde comme le code
l'imagine ne peut pas révéler que le monde a bougé.*

D'où la forme de ce fichier : **aucune entrée n'est fabriquée à la main au
milieu de la chaîne**. On part d'un dump, on passe par l'index, et on regarde ce
qui sort à l'autre bout.

## Ce que la source porte

Mesuré le 14/09/2026 sur les 4 585 fiches du dump `ep_mep_activities`
(population : toutes les fiches MEP du dump, pas les 7 candidats déclarés à
identifiant européen) : `REPORT` 9 593 / 9 935 (96,6 %), `MOTION`
44 684 / 60 362 (74,0 %), `COMPARL` 542 / 4 937 (11,0 %), `IMOTION` 1 / 3 862.

Une absence reste donc fréquente et légitime : `activite_sans_dossier` ne doit
pas disparaître, il doit cesser d'être unanime.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "tests"))

from normalize_parltrack_dumps import (  # noqa: E402
    _make_texte_porte_activite,
    _reference_dossier_activite,
)
from parltrack_dumps import (  # noqa: E402
    VERSION_SCHEMA_INDEX,
    build_activities_index,
)

#: Le format publié par ParlTrack n'est pas un tableau JSON ordinaire, et
#: `_write_zst_file` est « cette fonction, et elle seule, qui empêche la suite de
#: repasser verte sur un format que la source n'utilise pas ». La recopier ici
#: annulerait cette garantie le jour où le format bouge.
from test_parltrack_dumps import _write_zst_file  # noqa: E402

REFERENCE = "2022/2852(RSP)"


@pytest.fixture
def index_depuis_un_dump(tmp_path):
    """L'index tel que la chaîne réelle le produit, sans entrée écrite à la main."""
    dump = tmp_path / "ep_mep_activities.json.zst"
    _write_zst_file(dump, [{
        "mep_id": 131580,
        "REPORT": [{
            "date": "2022-10-04T00:00:00",
            "title": "Report on the situation of X",
            "reference": "A9-0240/2022",
            "url": "https://www.europarl.europa.eu/doceo/document/A-9-2022-0240_FR.html",
            "term": 9,
            "dossiers": [REFERENCE],
        }],
        "MOTION": [{
            "date": "2021-03-09T00:00:00",
            "title": "Motion for a resolution sans dossier visé",
            "reference": "B9-0160/2021",
            "term": 9,
        }],
    }])
    with patch("parltrack_dumps.ensure_dump", return_value=dump), \
         patch("parltrack_dumps.PARLTRACK_CACHE_DIR", tmp_path):
        yield build_activities_index(perimetre=frozenset({131580}))


def test_la_projection_conserve_la_reference_de_procedure(index_depuis_un_dump):
    """C'est la ligne exacte qui manquait : `dossiers` était jeté à l'indexation."""
    rapport = index_depuis_un_dump[131580]["rapport"][0]

    assert rapport["dossiers"] == [REFERENCE]


def test_la_reference_du_document_et_celle_du_dossier_ne_se_confondent_pas(
    index_depuis_un_dump,
):
    """`reference` est le DOCUMENT (`A9-0240/2022`), `dossiers` la PROCÉDURE.

    Se rabattre sur `reference` faute de `dossiers` interrogerait l'index des
    stades avec une clé qu'il n'a jamais — et rendrait `stade_source_inconnu`
    sur tout le corpus, ce qui se lirait comme un défaut de la source.
    """
    rapport = index_depuis_un_dump[131580]["rapport"][0]

    assert rapport["reference"] == "A9-0240/2022"
    assert rapport["dossiers"] == [REFERENCE]


def test_le_stade_traverse_toute_la_chaine(index_depuis_un_dump):
    """Du dump au texte porté publié — le seul test qui aurait attrapé #923."""
    rapport = index_depuis_un_dump[131580]["rapport"][0]

    assert _reference_dossier_activite(rapport) == REFERENCE

    texte = _make_texte_porte_activite(
        "rapport", rapport, {REFERENCE: "Procedure completed"}
    )

    assert texte["reference_dossier"] == REFERENCE
    assert texte["stade_procedural"] == "ue_procedure_achevee"
    assert "stade_procedural_non_resolu" not in texte


def test_une_activite_sans_dossier_reste_une_absence_declaree(index_depuis_un_dump):
    """74 % des `MOTION` en portent un : les 26 % restants sont un fait, pas un bug.

    Le motif doit rester atteignable. Ce qui était faux, c'est qu'il était
    **unanime** ; §2 règle 5 exige qu'une absence soit déclarée, pas qu'elle
    disparaisse.
    """
    motion = index_depuis_un_dump[131580]["proposition_de_resolution"][0]

    assert motion["dossiers"] is None

    texte = _make_texte_porte_activite("proposition_de_resolution", motion, {})

    assert texte["stade_procedural"] is None
    assert texte["stade_procedural_non_resolu"] == {"motif": "activite_sans_dossier"}


def test_la_version_de_schema_a_ete_incrementee():
    """Sans elle, le correctif n'atteint aucun run.

    `build_activities_index` relit l'index caché tant que sa date dépasse celle
    du dump, et le cache CI `public-data-cache-parltrack-<semaine>` restaure les
    deux. Le dump n'étant pas retéléchargé, l'index amputé aurait resservi une
    semaine entière : code juste, corpus inchangé. L'empreinte de schéma est
    portée par le NOM du fichier précisément pour faire rater ce cache.
    """
    assert VERSION_SCHEMA_INDEX >= 3
