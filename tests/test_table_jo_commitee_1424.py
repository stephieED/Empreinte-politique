"""Ce que l'artifact `actes-jo` emporte est commité (#1424).

`extract-actes-jo` emporte les fichiers que son run a modifiés : les mois
d'actes réglementaires ET la table `raw_data/lois_jorf.json`. Le commit de
`merge-and-pivot` ne faisait `git add` que sur les actes : la table, écrite une
fois le 23/09/2026, repartait de là à chaque run, et une loi sortie de la
fenêtre relue (`MOIS_RELUS`) aurait perdu son identifiant au Journal officiel.
La garde porte sur la règle, pas sur ce seul fichier : un chemin ajouté à
l'artifact sans `git add` ferait échouer ce test.
"""

import re
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "generate-data.yml"


def _job(nom):
    """Le texte d'un job, de sa clé à la clé du job suivant (même idiome que les
    autres gardes du workflow : le YAML se lit comme du texte)."""
    texte = WORKFLOW.read_text(encoding="utf-8")
    debut = texte.index(f"\n  {nom}:\n")
    suivant = re.search(r"\n  [a-z][a-z0-9-]*:\n", texte[debut + 1:])
    return texte[debut: debut + 1 + suivant.start()] if suivant else texte[debut:]


def _chemins_emportes():
    commande = re.search(r"git status --porcelain --([^\\|\n]+)", _job("extract-actes-jo")).group(1)
    return commande.split()


def _chemins_commites():
    lignes = re.findall(r"^\s*(?:if .*then )?git add ([^\n;]+)", _job("merge-and-pivot"), re.M)
    return {chemin for ligne in lignes for chemin in ligne.split() if not chemin.startswith("-")}


def test_l_artifact_emporte_les_actes_et_la_table_des_lois():
    assert _chemins_emportes() == ["pivot_data/actes_reglementaires", "raw_data/lois_jorf.json"]


def test_chaque_chemin_emporte_est_commite():
    manquants = [c for c in _chemins_emportes() if c not in _chemins_commites()]
    assert manquants == [], f"emportés par actes-jo, jamais commités : {manquants}"
