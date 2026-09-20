"""L'archive vivante se reprend au changement de semaine, les mortes jamais (#762).

`.cache/dossiers_an` porte une clé HEBDOMADAIRE doublée d'un `restore-keys` de
préfixe. Au changement de semaine, la clé exacte manque, le préfixe restaure le
répertoire de la semaine précédente, et `ensure_dossiers_zip_downloaded` — qui
court-circuite sur `zip_path.is_file()` — ne retélécharge rien. Le répertoire
inchangé repart ensuite sous la clé neuve : **la rotation se désamorce
elle-même**. C'est #749, appliqué aux dossiers.

CE QUE CES GARDE-FOUS PROTÈGENT, ET DANS LES DEUX SENS. Qu'on reprenne bien
l'archive vivante — sinon cinq consommateurs travaillent sur une donnée qui
vieillit en silence. Et qu'on ne reprenne **pas** les mortes : une législature
dissoute ne produit plus d'acte, et les 23 Mo hebdomadaires que coûterait leur
reprise n'achèteraient rien. Les deux erreurs sont faciles, et la seconde est
invisible — elle ne casse rien, elle gaspille.

CE QU'ILS NE COUVRENT PAS : aucun téléchargement n'est fait, et la CI n'est pas
exécutée. La cohérence de chaque étape avec le bloc de cache qu'elle suit est
vérifiée sur le YAML, pas sur un run.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))

from couverture_dossiers import (  # noqa: E402
    AN_DOSSIERS_ARCHIVES,
    AN_DOSSIERS_LEGISLATURES_ACTIVES,
    AN_DOSSIERS_LEGISLATURES_FIGEES,
)

WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"
SCRIPT = "src/rafraichir_dossiers_actifs.py"


@pytest.fixture(scope="module")
def workflow() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. Quelles archives sont vivantes — dérivé, jamais tenu en double
# ---------------------------------------------------------------------------

def test_les_actives_sont_la_difference_et_ne_se_recopient_pas():
    """Une liste tenue en double se désaligne au premier changement.

    À l'ouverture de la 18e, la seule édition est d'ajouter 17 aux figées ; les
    actives suivent toutes seules.
    """
    assert AN_DOSSIERS_LEGISLATURES_ACTIVES == (
        frozenset(AN_DOSSIERS_ARCHIVES) - AN_DOSSIERS_LEGISLATURES_FIGEES
    )


def test_la_seule_archive_vivante_est_la_dix_septieme():
    """Les 14e, 15e et 16e sont dissoutes : leurs archives ne changeront plus.

    La 14e est entrée avec #1019 — dissoute depuis 2017, elle naît figée."""
    assert AN_DOSSIERS_LEGISLATURES_ACTIVES == frozenset({17})
    assert AN_DOSSIERS_LEGISLATURES_FIGEES == frozenset({14, 15, 16})


def test_aucune_legislature_n_est_a_la_fois_figee_et_active():
    assert not (AN_DOSSIERS_LEGISLATURES_ACTIVES & AN_DOSSIERS_LEGISLATURES_FIGEES)


def test_les_figees_sont_bien_des_archives_declarees():
    """Geler une législature absente du dictionnaire ne gèlerait rien."""
    assert AN_DOSSIERS_LEGISLATURES_FIGEES <= frozenset(AN_DOSSIERS_ARCHIVES)


# ---------------------------------------------------------------------------
# 2. La reprise ne touche que les vivantes, et force vraiment
# ---------------------------------------------------------------------------

def test_la_reprise_force_le_telechargement_des_seules_vivantes(monkeypatch):
    """Sans `force_download=True`, l'appel court-circuite sur `is_file()` et
    ne reprend rien — c'est tout le défaut qu'on corrige."""
    import gouvernement_textes as gt

    appels: list[tuple[int, bool]] = []

    def faux(legislature, *, force_download=False):
        appels.append((legislature, force_download))
        return Path(f"/tmp/dossiers_{legislature}.zip")

    monkeypatch.setattr(gt, "ensure_dossiers_zip_downloaded", faux)
    reprises = gt.rafraichir_dossiers_actifs()

    assert [leg for leg, _ in appels] == sorted(AN_DOSSIERS_LEGISLATURES_ACTIVES)
    assert all(force for _, force in appels), (
        "une archive a été demandée sans `force_download` : elle serait servie "
        "depuis le cache, et la reprise n'aurait servi à rien"
    )
    assert reprises == sorted(AN_DOSSIERS_LEGISLATURES_ACTIVES)


def test_aucune_legislature_figee_n_est_jamais_reprise(monkeypatch):
    """23 Mo par semaine pour un contenu qui ne peut pas changer."""
    import gouvernement_textes as gt

    demandees: list[int] = []
    monkeypatch.setattr(
        gt, "ensure_dossiers_zip_downloaded",
        lambda leg, *, force_download=False: demandees.append(leg) or Path("/tmp/x.zip"),
    )
    gt.rafraichir_dossiers_actifs()
    assert not (set(demandees) & AN_DOSSIERS_LEGISLATURES_FIGEES)


def test_une_archive_qui_echoue_n_interrompt_pas_le_run(monkeypatch):
    """Un rafraîchissement raté vaut mieux qu'un run perdu : la donnée en
    cache reste exploitable, et l'absence est nommée par le script."""
    import gouvernement_textes as gt

    monkeypatch.setattr(
        gt, "ensure_dossiers_zip_downloaded",
        lambda leg, *, force_download=False: None,
    )
    assert gt.rafraichir_dossiers_actifs() == []


# ---------------------------------------------------------------------------
# 3. Le workflow : chaque étape suit SON cache et lit SON id
#
# Lu en TEXTE, comme `test_ci_push_regle_depot_508.py` : le dépôt n'a pas de
# dépendance YAML, et en ajouter une pour trois assertions serait cher.
# ---------------------------------------------------------------------------

def _blocs_de_cache(texte: str) -> list[str]:
    """Les blocs `actions/cache*` dont le `path` est le cache des dossiers."""
    blocs = []
    for m in re.finditer(r"^      - uses: actions/cache(?:/restore)?@v5\n", texte, re.M):
        suite = texte[m.end():]
        fin = re.search(r"^      - ", suite, re.M)
        bloc = suite[: fin.start()] if fin else suite
        if "path: .cache/dossiers_an" in bloc:
            blocs.append(bloc)
    return blocs


def _etapes_de_reprise(texte: str) -> list[str]:
    etapes = []
    for m in re.finditer(r"^      - name: Reprendre les archives de dossiers[^\n]*\n", texte, re.M):
        suite = texte[m.end():]
        fin = re.search(r"^      - ", suite, re.M)
        etapes.append(suite[: fin.start()] if fin else suite)
    return etapes


def test_chaque_cache_de_dossiers_est_suivi_d_une_reprise(workflow):
    """Un bloc de cache sans reprise, c'est une archive figée en silence."""
    caches = _blocs_de_cache(workflow)
    reprises = _etapes_de_reprise(workflow)
    assert caches, "plus aucun cache de dossiers dans le workflow"
    assert len(caches) == len(reprises), (
        f"{len(caches)} bloc(s) de cache de dossiers pour {len(reprises)} reprise(s)"
    )


def test_chaque_reprise_lit_le_cache_hit_de_SON_bloc(workflow):
    """Lire l'id d'un autre bloc rendrait la condition toujours vraie ou
    toujours fausse, sans que rien ne le signale."""
    caches = _blocs_de_cache(workflow)
    reprises = _etapes_de_reprise(workflow)
    identifiants = []
    for bloc in caches:
        trouve = re.search(r"^        id: (\S+)", bloc, re.M)
        assert trouve, "un bloc de cache des dossiers n'a pas d'`id` : son cache-hit est illisible"
        identifiants.append(trouve.group(1))
    assert len(set(identifiants)) == len(identifiants), (
        f"deux blocs partagent le même `id` : {identifiants}"
    )
    for identifiant, etape in zip(identifiants, reprises):
        assert f"steps.{identifiant}.outputs.cache-hit != 'true'" in etape, (
            f"la reprise qui suit `{identifiant}` ne lit pas le cache-hit de son propre bloc"
        )


def test_la_reprise_ne_tourne_pas_sur_un_demarrage_a_froid(workflow):
    """Le `rm -rf .cache` du cold start effacerait ce qu'elle vient de prendre.

    Défaut réel, trouvé en relisant l'ordre des étapes : dans `extract-an` et
    `extract-roster-groupes`, la purge SUIT la reprise.
    """
    for etape in _etapes_de_reprise(workflow):
        assert "!inputs.cold_start" in etape, (
            "la reprise tournerait sur un démarrage à froid, où le `rm -rf .cache` "
            "qui suit efface son téléchargement"
        )


def test_la_reprise_ne_fait_pas_echouer_le_run(workflow):
    for etape in _etapes_de_reprise(workflow):
        assert "continue-on-error: true" in etape, (
            "un rafraîchissement raté ferait échouer le run"
        )


def test_la_reprise_appelle_bien_le_script(workflow):
    for etape in _etapes_de_reprise(workflow):
        assert SCRIPT in etape
