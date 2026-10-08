"""Quatre textes faux ou bruts de la fiche candidat (#1161).

Relevés à l'écran pendant la revue d'ergonomie du 01/10/2026, remesurés le
08/10/2026 sur `main` 98327b0c0 :

1. le type `explication_de_vote` du Parlement européen sortait sous son nom
   technique (5 fiches de candidats : Maurel 683, Philippot 768, Mélenchon 49,
   Le Pen 65, Glucksmann 48) ;
2. « aucune fiche n'est publiée pour les groupes où cette personne a siégé »
   s'affichait pour une personne sans aucun mandat (Anasse Kazib) ;
3. « votes non publiés : 19840 scrutin(s)… » : n'est plus adressé au lecteur
   (arbitré le 02/10/2026 — il dit un choix, pas un manque) ;
4. « 48 des 48 explication(s) de vote… » : réécrit (arbitré le 02/10/2026).

Les messages ci-dessous sont COPIÉS du corpus, pas construits.

CE QUE CES TESTS NE COUVRENT PAS : la fiche n'est pas rendue. Les lignes de la
section 6 sont exécutées sur des fiches entières par
`tests/test_section_6_liste_de_manques.py`.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

UI = Path(__file__).resolve().parent.parent / "web" / "UI_finale" / "src"
MODULE = UI / "utils" / "profilCandidat.js"

#: `meta.avertissements[].message`, destinataire « lecteur », copiés le 08/10/2026.
MESSAGES = {
    "raphael-glucksmann": "Parlement européen — explications de vote : 48 des 48 explication(s) de vote sont publiées sans lien vers le document officiel (48 dont l'intitulé ne cite aucun document). Leur texte reste sourcé : ParlTrack transcrit l'annexe officielle de la séance.",
    "emmanuel-maurel": "Parlement européen — explications de vote : 46 des 683 explication(s) de vote sont publiées sans lien vers le document officiel (26 dont l'intitulé ne cite aucun document, 20 dont le document cité est introuvable au Parlement). Leur texte reste sourcé : ParlTrack transcrit l'annexe officielle de la séance.",
    "jean-luc-melenchon": "Parlement européen — explications de vote : 1 des 49 explication(s) de vote sont publiées sans lien vers le document officiel (1 dont l'intitulé ne cite aucun document). Leur texte reste sourcé : ParlTrack transcrit l'annexe officielle de la séance.",
    "marine-le-pen": "Parlement européen — explications de vote : 65 explication(s) de vote sont publiées sans lien vers le document officiel : la source en transcrit le texte sans en donner l'adresse.",
    "jordan-bardella": "ParlTrack: aucune donnée trouvée pour le député européen (identifiant ParlTrack 131580) dans les dumps publiés sur parltrack.org/dumps.",
}


def _node(expression: str):
    if shutil.which("node") is None:
        pytest.skip("node absent")
    script = "const m = await import(%r);\nprocess.stdout.write(JSON.stringify(%s));" % (MODULE.as_uri(), expression)
    res = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout)


def test_le_type_europeen_porte_le_libelle_des_explications_de_vote() -> None:
    types = _node("m.TYPES_INTERVENTION")
    ligne = next(t for t in types if t["label"] == "Explications de vote")
    assert set(ligne["cles"]) == {"explication_vote", "explication_de_vote"}


def test_les_explications_sans_lien_sont_reecrites() -> None:
    lus = _node("Object.fromEntries(Object.entries(%s).map(([k, v]) => [k, m.explicationsSansLien(v)]))" % json.dumps(MESSAGES))
    fin = "sans lien vers le document officiel."
    assert lus["raphael-glucksmann"] == {
        "titre": "Explications de vote au Parlement européen",
        "texte": f"Ses 48 explications de vote sont publiées {fin}",
    }
    assert lus["marine-le-pen"]["texte"] == f"Ses 65 explications de vote sont publiées {fin}"
    assert lus["emmanuel-maurel"]["texte"] == f"46 de ses 683 explications de vote sont publiées {fin}"
    assert lus["jean-luc-melenchon"]["texte"] == f"1 de ses 49 explications de vote est publiée {fin}"
    for texte in (v["texte"] for v in lus.values() if v):
        assert "(s)" not in texte and "ParlTrack" not in texte and "(" not in texte


def test_un_message_inconnu_n_est_pas_escamote() -> None:
    """Ce qu'on n'a pas su lire reste affiché tel quel, il ne disparaît pas."""
    assert _node("m.explicationsSansLien(%s)" % json.dumps(MESSAGES["jordan-bardella"])) is None


def test_la_mention_des_ecarts_suppose_un_mandat() -> None:
    fiche = (UI / "components" / "CandidateProfile.jsx").read_text(encoding="utf-8")
    assert "ecartsSansFiche={!c.ecarts.fiches.length && !c.ceQuiManque.phrase}" in fiche
