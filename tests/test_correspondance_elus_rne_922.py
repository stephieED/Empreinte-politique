"""#922 — la table relue qui apparie un candidat déclaré à un élu du RNE.

Le RNE n'expose aucun identifiant de personne. La clé praticable est
`(nom, prénom, date de naissance)` : elle résout **17 des 32 candidats
déclarés** sans relecture. Les 15 autres n'ont pas de date de naissance dans le
corpus, et apparier au nom seul a déjà produit un faux positif en instruisant
#885 — trois mandats sénatoriaux d'un homonyme mosellan attribués à
`jean-louis-masson`.

D'où cette table, sur le patron de `mandats_anterieurs.json` (#860) et de la
correspondance slug ↔ acteur AN (#525) : committée, relue, chaque ligne portant
ce qui a servi à trancher.

**Le contrat de relevé est celui de #860** : un candidat présent a été relu, son
verdict est complet ; un candidat ABSENT n'a pas été relu, et sa fiche doit le
dire. Absent n'est pas « aucun mandat » (`AGENTS.md` §2 règle 5).
"""

import json
import re
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

TABLE = RACINE / "raw_data" / "correspondance_elus_rne.json"
VERDICTS = {"confirme", "ecarte", "aucun_mandat_trouve"}

#: Ce fichier LIT une configuration committée, et le déclare (#791). Le garde-fou
#: de `conftest.py` n'accepte cette déclaration que si le chemin est couvert par
#: le `sparse-checkout` de `tests.yml` — sans quoi la CI ne le télécharge pas et
#: le test ne tourne qu'en local, sur ce qu'un run a laissé.
#:
#: C'est exactement ce qui est arrivé : la suite passait dans le worktree, qui
#: porte tout le dépôt, et la CI de la PR #939 tombait en `FileNotFoundError`.
pytestmark = pytest.mark.lit_reference_committee("raw_data/correspondance_elus_rne.json")


@pytest.fixture
def table():
    """Portée `function`, et c'est délibéré.

    Le garde-fou de `conftest.py` qui surveille les lectures de `raw_data/` est
    une fixture `autouse` de portée **function**. Une fixture de portée `module`
    s'exécute AVANT lui — le fichier était donc lu hors surveillance, et le
    marqueur `lit_reference_committee` ci-dessus n'était jamais consulté :
    une déclaration décorative. Mesuré le 15/09/2026, en retirant le marqueur :
    les 14 tests passaient quand même.

    Relire 8 Kio quatorze fois ne coûte rien ; une déclaration qui ne mord pas,
    si.
    """
    return json.loads(TABLE.read_text(encoding="utf-8"))


def test_la_table_existe_et_porte_ses_deux_blocs(table):
    assert set(table) == {"_meta", "candidats"}
    assert table["candidats"], "une table vide ne relit rien"


def test_le_meta_dit_le_contrat_de_releve(table):
    """Sans cette phrase, une absence se lirait comme « aucun mandat »."""
    meta = table["_meta"]
    for clef in ("description", "pourquoi", "releve", "fichiers_interroges", "licence"):
        assert meta.get(clef), f"_meta.{clef} manquant"
    assert "n'a PAS été relu" in meta["releve"]


def test_les_neuf_fichiers_locaux_sont_nommes(table):
    """Un verdict ne vaut que pour les fichiers effectivement interrogés."""
    fichiers = table["_meta"]["fichiers_interroges"]

    assert len(fichiers) == 9
    assert "elus-conseillers-municipaux-cm" in fichiers
    assert "elus-conseillers-regionaux-cr" in fichiers, (
        "c'est le fichier régional qui porte marine-tondelier : l'oublier "
        "aurait conclu « aucun mandat »")


@pytest.mark.parametrize("slug", ["david-lisnard", "karim-bouamrane",
                                  "fabien-verdier", "marine-tondelier"])
def test_chaque_appariement_confirme_porte_sa_cle_et_sa_preuve(table, slug):
    e = table["candidats"][slug]

    assert e["appariement"] == "confirme"
    for clef in ("nom", "prenom", "date_naissance"):
        assert e["rne"].get(clef), f"rne.{clef} manquant"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", e["rne"]["date_naissance"])
    assert e["preuve"].get("source", "").startswith("https://")
    assert e["preuve"].get("fait_verifie")
    assert e["etabli_par"] == "relecture_humaine"


def test_un_appariement_ecarte_nomme_la_ligne_et_le_motif(table):
    """Écarter sans dire quoi laisserait le prochain run reproposer la même."""
    e = table["candidats"]["nathalie-arthaud"]

    assert e["appariement"] == "ecarte"
    assert e["motif"] == "homonyme"
    assert e["ligne_ecartee"]["commune"] == "Limey-Remenauville"
    assert e["preuve"]["fait_verifie"]


def test_une_absence_non_corroboree_se_distingue_d_une_absence_verifiee(table):
    """Deux silences qui n'ont pas la même valeur (§2 règle 5).

    Quatre candidats ont une page Wikipédia où aucun mandat local ne figure :
    l'absence est corroborée. Deux n'ont aucune page : elle ne l'est pas, et la
    table doit le dire plutôt que de les publier pareil.
    """
    corrobores = ["francois-asselineau", "sylvain-durif", "anasse-kazib", "francis-lalanne"]
    non_corrobores = ["selma-labib", "benoit-mathieu"]

    for slug in corrobores:
        e = table["candidats"][slug]
        assert e["appariement"] == "aucun_mandat_trouve"
        assert "corroboration" not in e
        assert "wikipedia.org" in e["preuve"]["source"]

    for slug in non_corrobores:
        e = table["candidats"][slug]
        assert e["appariement"] == "aucun_mandat_trouve"
        assert e["corroboration"] == "absente"
        assert e.get("note"), "dire pourquoi ce silence vaut moins"


def test_tout_verdict_appartient_au_vocabulaire_ferme(table):
    """Comme les `KNOWN_*` du schéma (§4) : on étend délibérément, jamais par
    effet de bord."""
    for slug, e in table["candidats"].items():
        assert e.get("appariement") in VERDICTS, slug


def test_chaque_ligne_est_datee_et_attribuee(table):
    for slug, e in table["candidats"].items():
        assert e.get("etabli_par") == "relecture_humaine", slug
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", e.get("verifie_le", "")), slug


def test_les_slugs_sont_en_kebab_case(table):
    for slug in table["candidats"]:
        assert re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug), slug


def test_la_date_de_naissance_du_rne_ne_sert_pas_a_apparier(table):
    """La distinction que l'issue appelait « circulaire ».

    Une ligne `confirme` porte la date de naissance telle que le RNE l'écrit,
    pour RETROUVER les lignes de la personne au run suivant sans dépendre de
    l'orthographe. Ce n'est pas elle qui établit l'appariement — c'est la
    relecture, sur la commune et une source primaire. Le `_meta` doit le dire,
    sinon la table sera relue un jour comme une source de dates de naissance.
    """
    meta = table["_meta"]["la_date_de_naissance_ici_n_est_pas_circulaire"]

    assert "ne doit jamais être reversée dans `identite.date_naissance`" in meta


def test_le_piege_des_diacritiques_est_consigne(table):
    """« Edouard » sans accent et « Jérôme » avec, dans le même fichier.

    Mesuré le 14/09/2026 : apparier sur le prénom tel qu'écrit rendait Édouard
    Philippe SANS AUCUN MANDAT, alors qu'il est maire du Havre. L'échec est
    silencieux — d'où la trace dans la table.
    """
    assert "SILENCIEUSEMENT" in table["_meta"]["diacritiques"]


def test_la_borne_de_couverture_est_declaree(table):
    """#922, arbitré le 15/09/2026 : rien avant 2020, et l'absence se DIT.

    Une fiche ne doit jamais laisser lire « cette personne n'avait pas de mandat
    local avant 2020 ». Nathalie Arthaud a été conseillère municipale de
    Vaulx-en-Velin, élue en 2008, et aucun jeu accessible ne le porte : publier
    sans rien dire en ferait une personne sans parcours local (§2 règle 5).
    """
    meta = table["_meta"]

    assert meta["borne_couverture"] == "2020"
    assert "nous ne pouvons pas le savoir" in meta["borne"]


def test_les_deux_raisons_d_ecarter_les_paliers_anterieurs_sont_distinguees(table):
    """L'une peut tomber, l'autre non — les confondre ferait rouvrir la mauvaise.

    Licence non établie (jeux complets 2014 et 2020) : réparable par le
    producteur. Couverture au premier tour seul (jeux 2014 sous Licence
    Ouverte) : définitive, le jeu ne changera plus.
    """
    borne = table["_meta"]["borne"]

    assert "aucune licence" in borne
    assert "premier tour" in borne
    assert "La première raison tomberait" in borne
