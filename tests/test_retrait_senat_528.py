"""Garde-fou #528 : le Sénat ne rentre pas par la fenêtre.

Le Sénat est sorti du périmètre du produit par une **décision éditoriale**
(`docs/decisions/retrait-senat-528.md`). Une décision éditoriale ne se
défait pas en rajoutant une clé dans un dict : elle se reprend explicitement,
datée, en satisfaisant les trois conditions écrites au §7 de cette section.

Ce fichier est le verrou qui l'impose. Il ne teste pas un comportement de
collecte — il n'y a plus rien à collecter — mais l'**absence** des trois portes
d'entrée, et la **présence** des trois refus bruyants qui les remplacent. C'est
la même mécanique que les deux tests retournés de #526/#527 sur
`AN_ROSTER_ACTIF` : un verrou qu'on supprime le jour où il se déclenche n'a
jamais rien gardé.

Ce qui reste EXPRESSÉMENT en place, et que ce fichier vérifie aussi :

- les 2 entrées Sénat de `raw_data/groupes_reels.json`, toujours
  `extraction_suspendue` — les retirer supprimerait deux fichiers publiés, ce
  que `audit_diff_profils` bloque (#460/#470) ;
- leur `condition_reprise`, qui doit renvoyer à la décision éditoriale et **pas**
  à un état de source : un certificat renouvelé sur `archive.nossenateurs.fr` ne
  rouvre plus rien.

Volontairement sans PyYAML (absent de `requirements.txt`), comme les autres
gardes-fous de workflow de ce dépôt.
"""

import json
import re
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"
GROUPES = RACINE / "raw_data" / "groupes_reels.json"

sys.path.insert(0, str(RACINE / "src"))

import candidate_profile
import generate_all_profiles
import group_roster

#: Ce fichier de tests lit la configuration committée nommée ci-dessous.
#: Le garde-fou de `conftest.py` refuse tout `.json` de `raw_data/` qu'un
#: test n'a pas déclaré (#791), et n'accepte la déclaration que si le chemin
#: est dans le `sparse-checkout` de `tests.yml` — sinon le test ne tournerait
#: qu'en local, sur ce qu'un run y a laissé.
pytestmark = pytest.mark.lit_reference_committee("raw_data/groupes_reels.json")

#: L'ancre de la décision. Un refus qui ne la cite pas oblige son lecteur à
#: deviner s'il regarde une panne ou un choix.
ANCRE = "retrait-senat-528"


# ---------------------------------------------------------------------------
# Les trois portes d'entrée sont fermées
# ---------------------------------------------------------------------------

def test_senateurs_nest_plus_une_chambre_collectee():
    """La porte la plus basse. Elle s'appelait `BASE_URLS` (la table des
    domaines NosDéputés par chambre) jusqu'à #529, qui l'a remplacée par
    `CHAMBRES_COLLECTEES` — plus aucune URL de plateforme n'est interrogée, mais
    le garde-fou de chambre, lui, reste : tant qu'une entrée `senateurs` y
    figure, tout le chemin de collecte redevient atteignable."""
    assert not hasattr(candidate_profile, "BASE_URLS"), (
        "`BASE_URLS` est de retour : c'est la table des domaines NosDéputés, "
        "retirée par #529."
    )
    assert set(candidate_profile.CHAMBRES_COLLECTEES) == {"deputes"}, (
        candidate_profile.CHAMBRES_COLLECTEES
    )


def test_chambres_ne_contient_que_l_assemblee():
    assert generate_all_profiles.CHAMBRES == ["deputes"]


def test_source_senat_nest_plus_une_valeur():
    assert "senat" not in generate_all_profiles.SOURCE_VALUES
    assert set(generate_all_profiles.SOURCE_VALUES) == {"an", "ue", "all"}


def test_les_fetchs_senatoriaux_nont_plus_de_definition():
    """`fetch_votes` et `fetch_dossiers_for_legislatures` n'avaient plus
    d'appelant : côté députés, votes et textes portés viennent de l'open data
    AN. Les laisser vivantes aurait gardé un chemin réseau vers une source
    morte, prêt à être rebranché sans décision."""
    for nom in ("fetch_votes", "fetch_dossiers", "fetch_dossiers_for_legislatures"):  # noqa: E501
        assert not hasattr(candidate_profile, nom), (
            f"`candidate_profile.{nom}` est de retour : c'est un chemin de "
            f"collecte sénatorial. Voir docs/decisions/{ANCRE}.md."
        )


# ---------------------------------------------------------------------------
# Les trois refus sont bruyants, et nomment la décision
# ---------------------------------------------------------------------------

def test_build_profile_refuse_la_chambre_en_nommant_la_decision():
    """Le refus doit dire POURQUOI. Un `KeyError` sur `BASE_URLS`, ou un
    « chambre inconnue » générique, se lit comme une faute de frappe."""
    with pytest.raises(ValueError) as echec:
        candidate_profile.build_profile("senateurs", "bruno-retailleau")
    message = str(echec.value)
    assert "#528" in message, message
    assert ANCRE in message, message


def test_le_roster_refuse_la_chambre_avant_tout_travail():
    """Le refus vivait dans `group_roster._base_url_for`, retiré par #529 avec
    le reste du chemin NosDéputés. Il a remonté d'un cran, dans
    `fetch_full_roster` : c'est désormais le seul point d'entrée d'un roster,
    et il doit refuser en nommant la décision plutôt qu'en rendant une liste
    vide."""
    with pytest.raises(ValueError) as echec:
        group_roster.fetch_full_roster("senateurs")
    assert ANCRE in str(echec.value)


def test_le_refus_roster_est_un_roster_indisponible():
    """`ValueError` appartient à `ERREURS_ROSTER` : les appelants le traitent en
    « roster indisponible » (exit 2, fiches publiées intactes) et non en trace
    de pile qui coûte le commit du run (#518/#524)."""
    assert ValueError in group_roster.ERREURS_ROSTER


# ---------------------------------------------------------------------------
# Le job CI a disparu, et rien ne le rappelle en vie
# ---------------------------------------------------------------------------

def _workflow() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def _noms_de_jobs() -> list[str]:
    corps = _workflow().split("\njobs:\n", 1)
    assert len(corps) == 2, "Section `jobs:` introuvable dans generate-data.yml."
    return re.findall(r"^  ([a-z][a-z0-9-]*):\n", corps[1], flags=re.M)


def test_le_job_extract_senat_est_revenu_sur_une_autre_source():
    """**Gel retourné par #885**, et c'est le §8 de la décision qui le prévoit :
    « un verrou qu'on supprime le jour où il se déclenche n'a jamais rien gardé ».

    `extract-senat` existe de nouveau — mais il lit `data.senat.fr`, producteur
    Sénat sous Licence Ouverte, et **jamais** `archive.nossenateurs.fr`, dont le
    certificat reste expiré et dont l'archive reste morte pour le produit.

    Ce que ce test garde désormais : que le job ne retourne pas à l'ancienne
    source. C'est la seule chose que #528 protégeait vraiment."""
    contenu = WORKFLOW.read_text(encoding="utf-8")

    assert "extract-senat:" in contenu
    assert "data.senat.fr" in contenu
    # Le critère porte sur une URL **appelée**, pas sur le mot : le workflow
    # garde une ligne de commentaire qui explique le coût évité par #528, et
    # l'effacer perdrait la trace de la décision. Ce qui ne doit pas revenir,
    # c'est une requête.
    appels = [ligne for ligne in contenu.splitlines()
              if "nossenateurs" in ligne and not ligne.lstrip().startswith("#")]
    assert not appels, appels


def _ancien_test_le_job_extract_senat_nexiste_plus():
    jobs = _noms_de_jobs()
    assert "extract-senat" not in jobs, (
        "`extract-senat` est de retour dans generate-data.yml. Ce job tournait, "
        "échouait sur 8 candidats sur 8 et concluait vert : c'est le motif de "
        f"#501, #510 et #528. Voir docs/decisions/{ANCRE}.md."
    )
    assert jobs, "aucun job détecté — le découpage ne lit plus le workflow"


def test_aucun_needs_ne_reference_le_job_retire():
    """Un `needs:` orphelin ne fait pas échouer le workflow à la validation :
    GitHub *skippe* le job qui en dépend. C'est la forme de panne silencieuse
    que #412 §2.1 a payée."""
    jobs = set(_noms_de_jobs())
    orphelins = []
    for motif in re.finditer(r"^    needs:\s*\[([^\]]*)\]", _workflow(), flags=re.M):
        for besoin in (b.strip() for b in motif.group(1).split(",")):
            if besoin and besoin not in jobs:
                orphelins.append(besoin)
    assert not orphelins, f"`needs:` pointant sur des jobs inexistants : {sorted(set(orphelins))}"


def test_le_workflow_ne_collecte_le_senat_que_pour_ses_appartenances():
    """**Gel retourné par #885.** Le Sénat rentre pour ses appartenances, pas
    pour son activité : son jeu ne porte ni scrutins ni comptes rendus, et la
    condition 2 du §7 de #528 reste **déclarée non remplie**.

    Ce que ce test garde : que le workflow n'appelle pas `--source senat`, qui
    déclencherait la collecte d'activité de l'ancien chemin — celle que #528 a
    fermée et que #885 ne rouvre pas."""
    contenu = WORKFLOW.read_text(encoding="utf-8")

    assert "--source senat" not in contenu
    assert "collecte_senat.py" in contenu


def _ancien_test_le_workflow_ne_lance_plus_de_collecte_senatoriale():
    lignes = [
        ligne for ligne in _workflow().splitlines()
        if not ligne.lstrip().startswith("#")
    ]
    corps = "\n".join(lignes)
    for interdit in ("--source senat", "raw-profiles-senat", "_artifacts/senat",
                     "public-data-cache-senat"):
        assert interdit not in corps, (
            f"`{interdit}` est de retour dans generate-data.yml (hors commentaire). "
            f"Voir docs/decisions/{ANCRE}.md."
        )


# ---------------------------------------------------------------------------
# Les 2 groupes suspendus : suspendus, pas retirés, et pour la bonne raison
# ---------------------------------------------------------------------------

def _entrees_senat() -> list[dict]:
    groupes = json.loads(GROUPES.read_text(encoding="utf-8"))["groupes"]
    return [g for g in groupes if g.get("chambre") == "Senat"]


def test_les_entrees_senat_sont_retirees_de_la_config():
    """Suspendre n'est plus conserver : les deux groupes sont RETIRÉS (16/09/2026).

    #516 gardait Senat:LR et Senat:SER suspendus plutôt que retirés, parce qu'un
    fichier disparu fait avorter le commit (#460/#470). Deux faits ont renversé
    ce choix : ces fiches dérivent de NosSénateurs (`group_profile.py` le dit), et
    #885 les a sorties de l'interface — il ne restait qu'une donnée dérivée d'une
    source retirée, publiée dans le dépôt et lue par personne. La disparition n'avorte
    plus rien : les fichiers et leurs entrées sont retirés dans le même commit.
    → `docs/decisions/retrait-groupes-senat-nossenateurs.md`
    """
    config = json.loads(GROUPES.read_text(encoding="utf-8"))
    assert _entrees_senat() == []
    assert [l for l in config["lignees"] if l.get("chambre") == "Senat"] == []


def test_la_condition_de_reprise_est_editoriale_et_non_un_etat_de_source():
    """Le cœur de la décision. L'ancienne condition disait « un certificat
    valide sur archive.nossenateurs.fr » : un renouvellement de certificat
    aurait rouvert tout seul une collecte que le produit ne veut plus."""
    for groupe in _entrees_senat():
        reprise = groupe["extraction_suspendue"]["condition_reprise"]
        assert ANCRE in reprise, (
            f"{groupe['groupe_id']} : la condition de reprise ne renvoie pas à la "
            "décision écrite."
        )
        assert "#528" in groupe["extraction_suspendue"]["references"]
