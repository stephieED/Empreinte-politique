"""#885 — la preuve d'une suspension s'ouvre sur son motif, pas sur la panne.

La preuve publiée commençait par « extraction du groupe Senat:LR suspendue
depuis le 2026-08-24 ». Un lecteur y trouvait donc, en premier, un **incident
technique daté** — un certificat expiré en août — là où la vraie raison est que
`data.senat.fr` ne publie ni scrutin ni compte rendu.

L'ordre n'était pas de la présentation : c'est lui qui décidait de ce que la
phrase affirmait. La propriétaire l'a arbitré le 14/09/2026 sur trois
formulations rendues côte à côte, et a retenu celle qui fait passer la panne au
rang d'incident daté.

**Rien ne gelait cet ordre** : les 4 973 tests passaient avant et après
l'inversion. C'est ce silence que ce fichier ferme — le même motif écrit dans
l'autre sens redeviendrait faux sans qu'une seule assertion bouge.
"""

import json
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from couverture_profil import GroupeSuspendu, groupe_suspendu_depuis_config  # noqa: E402

CONFIG = RACINE / "raw_data" / "groupes_reels.json"


def _suspendus():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    return [g for g in config["groupes"] if "extraction_suspendue" in g]


def test_la_preuve_commence_par_le_motif():
    preuve = GroupeSuspendu(groupe_id="X:Y", depuis="2026-08-24",
                            motif="La source ne publie rien.").preuve

    assert preuve.startswith("La source ne publie rien.")
    assert "extraction du groupe X:Y suspendue depuis le 2026-08-24" in preuve


def test_sans_motif_la_decision_ouvre_quand_meme_la_phrase():
    """Une suspension mal documentée est déjà une erreur dure du quality gate ;
    ce n'est pas ici qu'on la redécouvre, et la preuve ne doit pas commencer
    par un tiret orphelin."""
    preuve = GroupeSuspendu(groupe_id="X:Y", depuis="2026-08-24").preuve

    assert preuve.startswith("extraction du groupe X:Y suspendue")


def test_l_identifiant_et_la_date_restent_publies():
    """Ils rattachent la phrase à une entrée de configuration vérifiable
    (§2 règle 2). L'arbitrage portait sur leur PLACE, pas sur leur retrait."""
    preuve = GroupeSuspendu(groupe_id="Senat:LR", depuis="2026-08-24",
                            motif="Motif.", references="#528").preuve

    assert "Senat:LR" in preuve
    assert "2026-08-24" in preuve
    assert "références : #528" in preuve


@pytest.mark.lit_reference_committee("raw_data/groupes_reels.json")
def test_aucune_suspension_publiee_n_annonce_le_senat_hors_perimetre():
    """L'affirmation que #885 a rendue fausse, gelée là où elle vivait.

    Le Sénat est rentré pour ses appartenances le 13/09/2026 : 133 entrées
    sénatoriales sont publiées sur 2 candidats déclarés. Une suspension qui
    annonce l'inverse décrit un périmètre qui n'existe plus.
    """
    fautifs = []
    for groupe in _suspendus():
        motif = groupe["extraction_suspendue"].get("motif") or ""
        if "sorti le Sénat du périmètre" in motif or "Sénat est sorti du périmètre" in motif:
            fautifs.append(groupe["groupe_id"])

    assert fautifs == [], (
        f"suspensions annonçant le Sénat hors périmètre : {fautifs}. "
        "Les deux entrées ont été reformulées le 14/09/2026, chacune arbitrée : "
        "Senat:LR ouvre sur l'absence de source, Senat:SER sur sa clôture de 2009.")


# Les deux tests qui gelaient le texte des preuves de Senat:LR et Senat:SER sont
# retirés avec les deux groupes (16/09/2026) : leurs entrées ne sont plus dans la
# configuration, et une preuve sans groupe ne se publie nulle part.
# → docs/decisions/retrait-groupes-senat-nossenateurs.md
