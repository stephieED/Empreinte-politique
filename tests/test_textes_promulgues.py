"""Les textes promulgués, et leur matière — `pivot_data/textes_promulgues.json`.

Besoin remonté par l'interface le 23/09/2026 : mettre en regard, sur une fiche de
gouvernement, les textes promulgués et les actes parus au Journal officiel. Ni
les `textes[]` d'une fiche (ceux qu'un membre a initiés : **1** promulgué sur la
fenêtre de LECORNU_II) ni l'union des `textes_portes` des profils (**13** sur la
même fenêtre, soit « ce que nos rosters portent ») ne sont cette population.

FIXTURES. Réductions **verbatim** de deux dossiers promulgués de l'archive réelle
de la XVIIe : `DLR5L17N52781` (proposition de loi, déposée à l'Assemblée) et
`DLR5L17N53940` (projet de loi, déposé au Sénat). Les sous-objets de la source
sont recopiés intacts, seuls les actes hors sujet ont été retirés.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))

import textes_promulgues as tp  # noqa: E402

FIXTURES = RACINE / "tests" / "fixtures" / "dossiers_promulgues"
PROPOSITION = "DLR5L17N52781"
PROJET_SENAT = "DLR5L17N53940"

COMMISSION = {
    "organe_ref": "PO420120", "sigle": "Affaires sociales",
    "nom": "Commission des affaires sociales", "type": "COMPER",
}


def _dossier(uid: str) -> dict:
    return json.loads((FIXTURES / f"dossier_{uid}.json").read_text(encoding="utf-8"))["dossierParlementaire"]


def test_une_proposition_promulguee_porte_sa_date_son_numero_et_sa_nature():
    ligne = tp.entree(_dossier(PROPOSITION), COMMISSION)

    assert ligne["date_promulgation"].startswith("20")
    assert ligne["numero_loi"], "le numéro de loi vient de `codeLoi`, pas de l'intitulé"
    assert ligne["nature_procedure"] == "Proposition de loi ordinaire"
    assert ligne["titre"]
    assert ligne["commission"]["sigle"] == "Affaires sociales"
    assert ligne["chambre_premiere_lecture"] == "assemblee_nationale"


def test_un_texte_depose_au_senat_le_dit():
    """Tout dossier promulgué porte les DEUX dépôts — 607 sur 607 —, le second
    étant la transmission : c'est la date qui départage, jamais la présence."""
    ligne = tp.entree(_dossier(PROJET_SENAT), None)

    assert ligne["nature_procedure"] == "Projet de loi ordinaire"
    assert ligne["chambre_premiere_lecture"] == "senat"


def test_une_commission_absente_reste_une_absence():
    """La commission donne la matière de la ligne ; devinée depuis l'intitulé,
    elle serait une matière fausse (§2 règle 8)."""
    ligne = tp.entree(_dossier(PROJET_SENAT), None)

    assert ligne["commission"] is None
    assert "titre" in ligne, "le reste de la ligne est publié quand même"


def test_un_dossier_sans_promulgation_n_entre_pas():
    dossier = _dossier(PROPOSITION)
    actes = dossier["actesLegislatifs"]["acteLegislatif"]
    dossier["actesLegislatifs"]["acteLegislatif"] = [
        a for a in actes if a["codeActe"] != tp.CODE_PROMULGATION
    ]

    assert tp.entree(dossier, COMMISSION) is None


def test_la_chambre_reste_nulle_quand_rien_ne_la_departage():
    """Deux dépôts au même jour ne disent pas l'origine : `null` plutôt qu'un
    choix arbitraire (§2 règle 5)."""
    dossier = _dossier(PROPOSITION)
    for acte in dossier["actesLegislatifs"]["acteLegislatif"]:
        if acte["codeActe"] in tp.CHAMBRE_PAR_DEPOT:
            acte["dateActe"] = "2026-01-01T00:00:00.000+01:00"

    assert tp.chambre_premiere_lecture(dossier) is None


def test_la_table_ne_garde_que_les_dossiers_promulgues():
    archives = []  # `iter_dossiers_bruts` est contourné : on passe les dossiers à la main
    dossiers = [(17, _dossier(PROPOSITION)), (17, _dossier(PROJET_SENAT))]
    table = {}
    for _leg, dossier in dossiers:
        ligne = tp.entree(dossier, None)
        if ligne is not None:
            table[dossier["uid"]] = ligne

    assert set(table) == {PROPOSITION, PROJET_SENAT}
    assert tp.construire_table(archives, {}) == {}, "sans archive, table vide, jamais une erreur"


def test_la_fusion_est_additive_et_une_collecte_vide_n_ecrase_rien(tmp_path, monkeypatch):
    # Le cache des archives est isolé : sans ça, ce test lirait celui du poste et
    # passerait ou échouerait selon ce qu'une collecte locale y a laissé (#721).
    monkeypatch.chdir(tmp_path)
    chemin = tmp_path / "textes_promulgues.json"
    publie = {"schema_version": tp.SCHEMA_VERSION, "genere_le": "2026-09-23T10:00:00+0200",
              "licence_donnees": "x", "textes": {PROPOSITION: {"titre": "déjà publié"}}}
    chemin.write_text(json.dumps(publie), encoding="utf-8")

    assert tp.main(["--out", str(chemin), "--commissions", str(tmp_path / "absent.json")]) == 0

    garde = json.loads(chemin.read_text(encoding="utf-8"))["textes"]
    assert PROPOSITION in garde, "un run sans archive conserve ce qui est publié (§3a)"


def test_les_commissions_se_lisent_dans_le_fichier_publie(tmp_path):
    chemin = tmp_path / "commissions_dossiers.json"
    chemin.write_text(json.dumps({"commissions": {PROPOSITION: COMMISSION}}), encoding="utf-8")

    assert tp.charger_commissions(chemin)[PROPOSITION]["sigle"] == "Affaires sociales"
    assert tp.charger_commissions(tmp_path / "absent.json") == {}


def test_l_identifiant_jorftext_vient_de_la_table_des_lois():
    """Les archives de l'Assemblée ne publient pas cet identifiant, et le NOR
    manque sur 412 des 1 015 textes : la jointure passe par le numéro de loi."""
    dossier = _dossier(PROPOSITION)
    numero = tp.promulgation(dossier)["codeLoi"]
    table = {numero: [["JORFTEXT000000279082", "2026-01-01"],
                      ["JORFTEXT000000465327", "2026-01-10"]]}

    ligne = tp.entree(dossier, None, table)

    assert ligne["jorftext"] == "JORFTEXT000000279082", "la publication d'origine d'abord"
    assert ligne["jorftext_autres"] == ["JORFTEXT000000465327"], "le rectificatif est dit"


def test_sans_table_l_identifiant_reste_une_absence():
    ligne = tp.entree(_dossier(PROPOSITION), None, {})

    assert ligne["jorftext"] is None and ligne["jorftext_autres"] is None
