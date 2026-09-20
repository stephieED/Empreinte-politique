"""#885 — un refus qui affirme « aucune source de remplacement établie » doit
cesser de l'affirmer le jour où il y en a une.

`tests/test_retrait_senat_528.py` gèle les trois refus eux-mêmes : ils sont
toujours là, et ils doivent le rester tant que rien n'est câblé derrière. Ce
fichier gèle l'autre moitié, celle que #528 ne pouvait pas prévoir — **ce que
les refus disent**.

Trois d'entre eux portaient, dans leur message ou leur commentaire, la phrase
« aucune source de remplacement établie ». C'était vrai le 24/08/2026 et faux
depuis le 13/09 : `data.senat.fr` est mesurée, sous Licence Ouverte, et porte
l'historique daté des appartenances (#885). Un refus qui continue de dire le
contraire **referme le sujet tout seul** — le lecteur suivant lit « il n'y a
rien », et n'ouvre pas la décision qui dit qu'il y a quelque chose. C'est le
mode de défaillance de #886, appliqué non plus à une page publiée mais à un
message d'erreur.

**Ce que ces tests ne demandent pas** : que les refus s'ouvrent. Ils restent
fermés, et c'est délibéré — une chambre acceptée sans collecte derrière rend un
profil vide qui passe pour un constat (#501, #510), et une valeur `--source`
acceptée et servie par rien redonne le job vert sans profil que #528 a fermé.
L'ordre est imposé : le collecteur d'abord, l'ouverture ensuite.
"""

import re
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

import candidate_profile  # noqa: E402
import generate_all_profiles  # noqa: E402
import group_roster  # noqa: E402

#: L'ancre de la décision qui établit la source. Un refus qui ne la cite pas
#: laisse son lecteur conclure qu'il n'y en a pas.
ANCRE_885 = "reouverture-partielle-senat-885"

#: L'ancre du retrait, que ces refus doivent continuer de citer : ils gardent
#: toujours quelque chose, et c'est lui qui dit quoi.
ANCRE_528 = "retrait-senat-528"

#: La phrase devenue fausse, sous les formes qu'elle a prises. Cherchée sans
#: accents ni casse : deux des trois emplacements sont écrits sans accents.
PHRASE_PERIMEE = re.compile(
    r"aucune\s+source\s+de\s+remplacement[^.]*?(?:n'est|nest)\s+etablie|"
    r"aucune\s+source\s+de\s+remplacement\s+etablie",
    re.IGNORECASE,
)


def _sans_accents(texte: str) -> str:
    for accentue, nu in (("é", "e"), ("è", "e"), ("ê", "e"), ("à", "a"), ("ô", "o")):
        texte = texte.replace(accentue, nu)
    return texte


# ---------------------------------------------------------------------------
# Les messages d'erreur
# ---------------------------------------------------------------------------

def test_le_refus_de_build_profile_nomme_la_source_etablie():
    """Le refus reste, et il dit désormais les deux choses : ce qui est fermé,
    et que la source existe."""
    with pytest.raises(ValueError) as echec:
        candidate_profile.build_profile("senateurs", "bruno-retailleau")
    message = str(echec.value)

    assert ANCRE_528 in message, message
    assert ANCRE_885 in message, message
    assert not PHRASE_PERIMEE.search(_sans_accents(message)), message


def test_le_refus_du_roster_dit_que_la_nouvelle_source_ne_passe_pas_par_lui():
    """Celui-ci garde le chemin **NosSénateurs**, qui ne rouvre pas (#885 §5.2).
    Son message doit dire que la source de remplacement existe **et** qu'elle
    emprunte une autre voie — sinon le lecteur suivant lève ce refus-ci en
    croyant appliquer #885, et rouvre `archive.nossenateurs.fr`."""
    with pytest.raises(ValueError) as echec:
        group_roster.fetch_full_roster("senateurs")
    message = str(echec.value)

    assert ANCRE_528 in message, message
    assert ANCRE_885 in message, message
    assert not PHRASE_PERIMEE.search(_sans_accents(message)), message
    assert "ne passe" in message.lower() or "voie distincte" in message.lower(), message


# ---------------------------------------------------------------------------
# Les commentaires de code, qui se lisent avant les messages
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("module", [
    "candidate_profile.py",
    "group_roster.py",
    "generate_all_profiles.py",
])
def test_aucun_module_n_affirme_plus_qu_il_n_y_a_pas_de_source(module):
    """La phrase vivait aussi en commentaire, au-dessus de `CHAMBRES_COLLECTEES`
    — l'endroit exact où un agent la lit avant de décider de ne rien faire."""
    texte = _sans_accents((RACINE / "src" / module).read_text(encoding="utf-8"))

    trouve = PHRASE_PERIMEE.search(texte)
    assert not trouve, (
        f"{module} affirme encore qu'aucune source de remplacement n'est établie : "
        f"« {texte[max(0, trouve.start() - 60):trouve.end() + 60]} ». "
        f"data.senat.fr l'est depuis #885."
    )


def test_les_trois_refus_citent_la_decision_qui_etablit_la_source():
    """Un commentaire qui requalifie sans renvoyer laisse le lecteur avec une
    affirmation nouvelle et aucune preuve."""
    for module in ("candidate_profile.py", "group_roster.py", "generate_all_profiles.py"):
        texte = (RACINE / "src" / module).read_text(encoding="utf-8")
        assert "#885" in texte, f"{module} ne cite pas #885"


# ---------------------------------------------------------------------------
# Ce qui ne s'ouvre pas — l'ordre est imposé
# ---------------------------------------------------------------------------

def test_la_chambre_reste_fermee_tant_que_rien_ne_la_sert():
    """Requalifier n'est pas ouvrir. Une chambre acceptée sans collecte derrière
    rend un profil vide qui passe pour un constat (#501, #510)."""
    assert candidate_profile.CHAMBRES_COLLECTEES == ("deputes",)


def test_source_senat_reste_refusee_tant_que_rien_ne_la_sert():
    """Une valeur `--source` acceptée et servie par rien redonne le job vert
    sans profil que #528 a fermé. Le collecteur d'abord, cette ligne ensuite."""
    assert "senat" not in generate_all_profiles.SOURCE_VALUES
