"""#809 — le champ traverse-t-il TOUTE la chaîne, filtre compris ?

Le défaut que ces tests couvrent : `mandat_periodes` était produit par
`an_roster`, lu par `appartenances_depuis_roster` et publié par la fiche — mais
**jeté au milieu** par `filter_roster_by_sigle`, une projection par clés. Le run
`34538350163` a régénéré les 23 fiches de groupe sans qu'aucune ne porte
`periodes[]`.

Les tests de #809 ne l'ont pas vu parce qu'ils appelaient
`appartenances_depuis_roster` **directement**, en sautant le filtre : ils
décrivaient la chaîne telle que le lot l'imaginait, pas telle qu'elle est.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from group_profile import appartenances_depuis_roster  # noqa: E402
from group_roster import filter_roster_by_sigle  # noqa: E402


def _membre(slug, periodes=None, **extra):
    base = {
        "slug": slug, "nom": slug.title(), "groupe_sigle": "REN",
        "mandat_debut": "2022-06-29", "mandat_fin": "2024-06-09",
        "acteur_ref": f"PA{slug}",
    }
    if periodes is not None:
        base["mandat_periodes"] = periodes
    base.update(extra)
    return base


DUSSOPT = [
    {"debut": "2022-06-29", "fin": "2022-07-20"},
    {"debut": "2024-02-11", "fin": "2024-06-09"},
]


def test_le_filtre_laisse_passer_les_periodes():
    """LA régression du 11/09/2026 : le filtre recopiait les entrées à la main.

    Un champ ajouté n'atteint pas tout seul un consommateur qui projette par
    clés (`docs/regles/fusion-et-index.md`).
    """
    filtres = filter_roster_by_sigle([_membre("dussopt", DUSSOPT)], "AN", "REN")
    assert filtres[0]["mandat_periodes"] == DUSSOPT


def test_la_chaine_entiere_porte_les_periodes_jusqu_a_l_appartenance():
    """Roster → filtre → appartenances. Le test de #809 sautait le filtre."""
    filtres = filter_roster_by_sigle([_membre("dussopt", DUSSOPT)], "AN", "REN")
    appartenances = appartenances_depuis_roster(filtres)
    assert len(appartenances["dussopt"]["periodes"]) == 2


def test_un_roster_sans_periodes_traverse_sans_les_inventer():
    """Un roster d'avant #809 n'en porte pas : `None`, jamais une liste vide —
    « ce roster ne les portait pas » n'est pas « aucune période connue »
    (§2 règle 5)."""
    filtres = filter_roster_by_sigle([_membre("alice")], "AN", "REN")
    assert filtres[0]["mandat_periodes"] is None
    assert appartenances_depuis_roster(filtres)["alice"]["periodes"] is None


def test_le_filtre_ne_laisse_passer_que_le_groupe_demande():
    """Le garde-fou du garde-fou : le filtre filtre encore."""
    membres = [_membre("alice", DUSSOPT), _membre("bob", DUSSOPT, groupe_sigle="LFI")]
    filtres = filter_roster_by_sigle(membres, "AN", "REN")
    assert [m["slug"] for m in filtres] == ["alice"]
