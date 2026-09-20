"""Le fichier des sortants publie des naissances au XXIᵉ siècle (#922).

Mesuré le 16/09/2026 à `tabular-api.data.gouv.fr`, fichier
`mun2026-cm-sortants-20260227` :

  David Lisnard     né 1969-02-02  publié 2069-02-02
  Édouard Philippe  né 1970-11-28  publié 2070-11-28
  Gabriel Attal     né 1989-03-16  publié 1989-03-16  (correct)

Le fichier donnait l'année sur deux chiffres ; convertie en ISO, une année basse
a pris le mauvais siècle. Interrogée sur la seule date exacte, la source ne
rendait rien, et 5 mandats 2020-2026 de candidats déclarés disparaissaient sans
erreur : Lisnard, Philippe, Roussel, Bouamrane, Bertrand.

POURQUOI LES TESTS EXISTANTS NE POUVAIENT PAS LE VOIR : leur faux serveur
(`_faux_appel` dans `test_rne_opendata_922.py`) IGNORE le filtre de la requête et
rend les mêmes lignes quelle que soit la date demandée. Il décrivait le serveur
comme le code l'imaginait (#726). Celui-ci applique le filtre et la pagination
comme le vrai, et les lignes sont celles relevées à la source.
"""
from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))

from rne_opendata import (  # noqa: E402
    COL_DEBUT_MANDAT,
    COL_FONCTION,
    COL_NAISSANCE,
    COL_NOM,
    COL_PRENOM,
    PAGES_MAX,
    dates_de_naissance_interrogees,
    lignes_de,
    mandats_locaux,
)

# Relevées à la source le 16/09/2026 — la date de naissance est celle PUBLIÉE.
LISNARD_SORTANT = {
    COL_NOM: "LISNARD", COL_PRENOM: "David", COL_NAISSANCE: "2069-02-02",
    COL_DEBUT_MANDAT: "2020-05-18", COL_FONCTION: "Maire",
    "Libellé de la commune": "Cannes",
}
ATTAL_SORTANT = {
    COL_NOM: "ATTAL", COL_PRENOM: "Gabriel", COL_NAISSANCE: "1989-03-16",
    COL_DEBUT_MANDAT: "2020-06-28", COL_FONCTION: None,
    "Libellé de la commune": "Vanves",
}


def _serveur(lignes_par_rid: dict[str, list[dict]]):
    """Un faux serveur tabulaire qui APPLIQUE le filtre `__exact` et pagine."""
    appels: list[str] = []

    def appel(url: str):
        appels.append(url)
        parties = urlsplit(url)
        rid = parties.path.split("/resources/")[1].split("/")[0]
        params = {k: v[0] for k, v in parse_qs(parties.query).items()}
        lignes = lignes_par_rid.get(rid, [])
        for cle, valeur in params.items():
            if cle.endswith("__exact"):
                colonne = cle[: -len("__exact")]
                lignes = [l for l in lignes if l.get(colonne) == valeur]
        page = int(params.get("page", 1))
        taille = int(params.get("page_size", 20))
        tranche = lignes[(page - 1) * taille: page * taille]
        suivante = None
        if page * taille < len(lignes):
            reste = "&".join(f"{k}={v}" for k, v in params.items() if k != "page")
            suivante = f"https://tabular-api.data.gouv.fr/api/resources/{rid}/data/?{reste}&page={page + 1}"
        return {"data": tranche, "links": {"next": suivante},
                "meta": {"page": page, "page_size": taille, "total": len(lignes)}}

    appel.appels = appels
    return appel


def test_la_date_exacte_seule_ne_trouve_pas_lisnard():
    """La prémisse du défaut, tenue : le serveur ne rend rien sur 1969-02-02."""
    appel = _serveur({"RID": [LISNARD_SORTANT]})
    brut = appel(
        "https://tabular-api.data.gouv.fr/api/resources/RID/data/"
        f"?{COL_NAISSANCE}__exact=1969-02-02&page_size=50")
    assert brut["data"] == []


def test_la_forme_decalee_retrouve_le_mandat_clos():
    appel = _serveur({"RID": [LISNARD_SORTANT]})
    assert lignes_de(appel, "RID", "LISNARD", "David", "1969-02-02") == [LISNARD_SORTANT]


def test_une_date_correcte_est_toujours_trouvee():
    appel = _serveur({"RID": [ATTAL_SORTANT]})
    assert lignes_de(appel, "RID", "ATTAL", "Gabriel", "1989-03-16") == [ATTAL_SORTANT]


def test_les_deux_formes_sont_toujours_demandees():
    """Le seuil de bascule n'est pas deviné : 1989 est correct, 1969 ne l'est
    pas, et rien ne dit où passe la frontière."""
    assert dates_de_naissance_interrogees("1969-02-02") == ("1969-02-02", "2069-02-02")
    assert dates_de_naissance_interrogees("1989-03-16") == ("1989-03-16", "2089-03-16")


def test_la_forme_decalee_ne_fait_pas_entrer_un_homonyme():
    """`concerne()` vérifie le nom sur chaque ligne, quelle que soit la forme."""
    autre = {**LISNARD_SORTANT, COL_NOM: "DUPONT", COL_PRENOM: "Jean"}
    appel = _serveur({"RID": [autre]})
    assert lignes_de(appel, "RID", "LISNARD", "David", "1969-02-02") == []


def test_une_personne_au_dela_de_la_premiere_page_n_est_pas_perdue():
    """Le module ne lisait que la première page. Mesuré le 16/09/2026 : une date
    de naissance partagée par 49 élus, à une ligne du plafond de 50."""
    voisins = [{**LISNARD_SORTANT, COL_NOM: f"ELU{i:03d}", COL_PRENOM: "X"}
               for i in range(120)]
    appel = _serveur({"RID": voisins + [LISNARD_SORTANT]})
    assert lignes_de(appel, "RID", "LISNARD", "David", "1969-02-02") == [LISNARD_SORTANT]


def test_la_pagination_a_une_fin():
    """Un serveur qui rendrait toujours une page suivante n'emballe pas la boucle."""
    appels = []

    def serveur_sans_fin(url):
        appels.append(url)
        return {"data": [], "links": {"next": url + "&x=1"}}

    lignes_de(serveur_sans_fin, "RID", "LISNARD", "David", "1969-02-02")
    assert len(appels) <= 2 * PAGES_MAX


def test_la_collecte_publie_le_mandat_clos_de_lisnard():
    """De bout en bout, avec les deux jeux, sur les lignes relevées à la source."""
    catalogue = {
        "repertoire-national-des-elus-1": {"resources": [
            {"title": "elus-maires-mai.csv", "id": "RID_MAI"}]},
        "elections-municipales-2026-maires": {"resources": [
            {"title": "mun2026-cm-sortants-20260227.csv", "id": "RID_SORT"}]},
    }
    en_cours = {**LISNARD_SORTANT, COL_NAISSANCE: "1969-02-02",
                COL_DEBUT_MANDAT: "2026-03-15"}
    tabulaire = _serveur({"RID_MAI": [en_cours], "RID_SORT": [LISNARD_SORTANT]})

    def appel(url):
        if "/api/1/datasets/" in url:
            return next((v for k, v in catalogue.items() if k in url), {})
        return tabulaire(url)

    mandats = mandats_locaux(appel, "LISNARD", "David", "1969-02-02",
                             constate_le="2026-02-27")
    assert [(m["label"], m["debut"], m["actif"]) for m in mandats] == [
        ("Cannes", "2020-05-18", False),
        ("Cannes", "2026-03-15", True),
    ]
