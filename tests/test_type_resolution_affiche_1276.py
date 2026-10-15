"""Le type d'une résolution remplace la mention générique (#1276).

Arbitré le 15/10/2026 sur la fiche de Jean-Luc Mélenchon : variante A — le type
lu par la collecte (`type_resolution`) prend la place de « Résolution (prise de
position ou demande procédurale) » sur la ligne grise de la liste, et ouvre la
bulle des carrés. Aucun compte ne change, et une demande de commission
d'enquête n'est pas montrée à part. Exécuté, pas lu.
"""

from __future__ import annotations

import ast
import json
import shutil
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
UTILS = RACINE / "web" / "UI_finale" / "src" / "utils"


def _executer(script: str) -> object:
    if shutil.which("node") is None:
        pytest.skip("node absent")
    entete = "".join(
        f"const {nom} = await import({json.dumps((UTILS / fichier).as_uri())});\n"
        for nom, fichier in (("p", "profilCandidat.js"), ("c", "carresTextes.js"), ("l", "lignee.js"))
    )
    res = subprocess.run(["node", "--input-type=module", "-e", entete + script],
                         capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout.strip().splitlines()[-1])


def _types_du_schema() -> set[str]:
    arbre = ast.parse((RACINE / "src" / "schema_pivot.py").read_text(encoding="utf-8"))
    for noeud in ast.walk(arbre):
        if isinstance(noeud, ast.AnnAssign) and getattr(noeud.target, "id", "") == "KNOWN_TYPES_RESOLUTION":
            return {e.value for e in noeud.value.args[0].elts}
    raise AssertionError("KNOWN_TYPES_RESOLUTION introuvable dans schema_pivot.py")


def test_chaque_type_du_schema_a_son_libelle():
    """Un type ajouté au schéma sans libellé s'afficherait en clé technique."""
    libelles = _executer("console.log(JSON.stringify(Object.keys(p.LIBELLE_TYPE_RESOLUTION)));")
    assert set(libelles) == _types_du_schema()


def test_le_type_remplace_la_mention_generique_et_son_absence_la_garde():
    """Un type non lu garde la mention actuelle, jamais une valeur par défaut
    (§2 règle 5)."""
    out = _executer("""
      const r = 'auteur_proposition_de_resolution';
      console.log(JSON.stringify([
        p.libelleRoleTexte({ role: r, type_resolution: 'creation_commission_d_enquete' }),
        p.libelleRoleTexte({ role: r, type_resolution: null, type_resolution_non_resolu: { motif: 'document_absent' } }),
        p.libelleRoleTexte({ role: 'auteur_proposition_de_loi', type_resolution: null }),
      ]));
    """)
    assert out == [
        "Demande de commission d’enquête",
        "Résolution (prise de position ou demande procédurale)",
        "Proposition de loi issue d'un(e) parlementaire",
    ]


def test_la_bulle_ouvre_sur_le_type():
    out = _executer("""
      console.log(JSON.stringify([
        c.faitDuTexte({ typeResolution: 'Demande de commission d’enquête', matiere: 'Matière non établie',
                        stade: 'examiné en commission', sortCle: null, an: '2018' }),
        c.faitDuTexte({ typeResolution: null, matiere: 'Lois', stade: 'adopté', sortCle: null, an: '2020' }),
      ]));
    """)
    assert out[0].startswith("Demande de commission d’enquête · Matière non établie")
    assert out[1].startswith("Lois · adopté")


def test_la_fiche_de_groupe_recoit_le_type():
    """Les textes d'une lignée sont recopiés par `textesDuMaillon` : sans le
    champ, la fiche de groupe resterait sur la mention générique."""
    out = _executer("""
      const t = l.textesDuMaillon([{ dossier_id: 'dossier-1', role: 'auteur_proposition_de_resolution',
        titre: 'Prédation des capacités productives françaises par les fonds spéculatifs',
        nature_texte: 'proposition_de_resolution', type_resolution: 'creation_commission_d_enquete',
        stade_procedural: 'examine_commission' }]);
      console.log(JSON.stringify(t.map((x) => x.type_resolution)));
    """)
    assert out == ["creation_commission_d_enquete"]
