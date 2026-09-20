#!/usr/bin/env python3
"""Écrit le bloc `mandats_locaux` dans les profils bruts (#922).

Miroir de `collecte_senat.py` : un script d'entrée qui lit une source, compose
un bloc, et n'écrit **que** les profils du périmètre — en consignant lesquels
dans un manifeste (#450).

## Ce que le bloc déclare TOUJOURS, même vide

Une liste vide de mandats locaux ne dit pas pourquoi elle est vide, et les
raisons ne se valent pas. Le bloc porte donc `appariement`, en vocabulaire
fermé :

| Valeur | Ce que la fiche peut en dire |
| --- | --- |
| `date_naissance` | apparié par la clé sûre : nom, prénom et date de naissance |
| `table_relue` | apparié par relecture humaine, faute de date de naissance |
| `ecarte` | une ligne existait, un humain l'a rejetée — homonyme |
| `aucun_mandat_trouve` | relu, et la source n'en porte aucun |
| `non_relu` | **personne n'a encore regardé** — l'absence ne dit rien |

Les deux derniers se ressemblent et ne se confondent pas : `aucun_mandat_trouve`
est un constat, `non_relu` est un aveu. Publier l'un pour l'autre ferait dire à
une fiche « cette personne n'a pas de mandat local » alors que nous ne le savons
pas (§2 règle 5).

## La borne, reportée dans chaque bloc

`borne_couverture` vaut 2020, et voyage avec la donnée plutôt que de vivre
seulement dans un document : une fiche doit pouvoir dire, sans rien aller
chercher, que rien avant cette date n'a pu être vérifié.

Usage :

    python3 src/collecte_mandats_locaux.py --apply --manifest-out _manifest/locaux.txt
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Callable, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from json_io import ecrire_profil_json  # noqa: E402
from population_profils import provenance_du_profil  # noqa: E402
from rne_opendata import (  # noqa: E402
    BORNE_COUVERTURE,
    DATASET_RNE,
    RneIndisponible,
    mandats_locaux,
)

RACINE = Path(__file__).resolve().parents[1]
DEFAULT_RAW_DIR = RACINE / "raw_data" / "profiles"
DEFAULT_PIVOT_DIR = RACINE / "pivot_data" / "profiles"
DEFAULT_CANDIDATS = RACINE / "raw_data" / "candidats.json"
DEFAULT_TABLE = RACINE / "raw_data" / "correspondance_elus_rne.json"

#: La clé du bloc dans le profil brut.
CLE_BLOC = "mandats_locaux"

#: Les provenances dont ce script s'occupe. Un membre de roster n'a pas de fiche
#: publiée : lui collecter des mandats locaux coûterait ~750 × 9 requêtes pour
#: une donnée que rien n'affiche.
PERIMETRE = {"candidat_declare"}

#: Vocabulaire fermé d'`appariement`. Voir le docstring du module.
KNOWN_APPARIEMENTS = frozenset({
    "date_naissance", "table_relue", "ecarte", "aucun_mandat_trouve", "non_relu",
})

#: L'état du jeu des sortants, reporté dans `fin_non_resolue.constate_le`.
#: Il vient du nom du fichier publié (`mun2026-cm-sortants-20260227.csv`) et
#: n'est pas deviné : une date de constat inventée ferait dater un fait.
CONSTATE_LE_SORTANTS = "2026-02-27"


def _charger(chemin: Path) -> Optional[dict[str, Any]]:
    try:
        return json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def etat_civil(pivot: dict[str, Any]) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """`(nom, prénom, date de naissance)` d'un profil pivot.

    Le prénom n'a **pas** de champ à lui : il se lit dans `nom`, qui porte
    « Nathalie Arthaud ». Le premier mot est le prénom — convention du corpus,
    et la seule que `raw_data/candidats.json` respecte.
    """
    complet = (pivot.get("nom") or "").strip()
    if not complet:
        return None, None, None
    morceaux = complet.split()
    if len(morceaux) < 2:
        return complet, None, None
    prenom, nom = morceaux[0], " ".join(morceaux[1:])
    date = ((pivot.get("identite") or {}).get("date_naissance")) or None
    return nom, prenom, date


def cle_appariement(
    pivot: dict[str, Any], table: dict[str, Any], slug: str,
) -> tuple[str, Optional[tuple[str, str, Optional[str]]]]:
    """Comment apparier ce profil, et avec quelles valeurs.

    **Le corpus prime sur la table.** Si la date de naissance est publiée, elle
    tranche — une relecture reste valide, mais elle devient inutile, et deux
    sources qui se contrediraient en silence seraient pires que l'une des deux.
    C'est le cas qui se produit dès qu'un candidat relu est ensuite élu député.
    """
    nom, prenom, date = etat_civil(pivot)
    if not nom or not prenom:
        return "non_relu", None
    if date:
        return "date_naissance", (nom, prenom, date)

    entree = ((table.get("candidats") or {}).get(slug)) or None
    if entree is None:
        return "non_relu", None
    verdict = entree.get("appariement")
    if verdict == "confirme":
        rne = entree.get("rne") or {}
        return "table_relue", (
            rne.get("nom") or nom, rne.get("prenom") or prenom,
            rne.get("date_naissance"))
    if verdict in ("ecarte", "aucun_mandat_trouve"):
        return verdict, None
    return "non_relu", None


def composer_bloc(
    appariement: str,
    mandats: list[dict[str, Any]],
    synchro_le: str,
) -> dict[str, Any]:
    """Le bloc `mandats_locaux`, qui se lit même quand il est vide."""
    return {
        "source": f"https://www.data.gouv.fr/datasets/{DATASET_RNE}",
        "synchro_le": synchro_le,
        "borne_couverture": BORNE_COUVERTURE,
        "appariement": appariement,
        "mandats": mandats,
    }


def collecter(
    appel: Callable[[str], Any],
    raw_dir: Path = DEFAULT_RAW_DIR,
    pivot_dir: Path = DEFAULT_PIVOT_DIR,
    table_path: Path = DEFAULT_TABLE,
    *,
    appliquer: bool = False,
    synchro_le: Optional[str] = None,
    manifest_out: Optional[Path] = None,
) -> dict[str, Any]:
    """Écrit (ou simule) le bloc local des candidats déclarés.

    Comme `collecte_senat.collecter`, le manifeste ne consigne **que** les
    fichiers écrits par ce job : uploader `raw_data/profiles/` entier
    réinjecterait la baseline committée du checkout (#450).
    """
    table = _charger(table_path) or {}
    horodatage = synchro_le or time.strftime("%Y-%m-%dT%H:%M:%S%z")
    ecrits: list[dict[str, Any]] = []
    sans_brut: list[str] = []
    par_appariement: dict[str, int] = {}

    for chemin_pivot in sorted(pivot_dir.glob("*.pivot.json")):
        pivot = _charger(chemin_pivot)
        if pivot is None or provenance_du_profil(pivot) not in PERIMETRE:
            continue
        slug = chemin_pivot.name.replace(".pivot.json", "")
        appariement, cle = cle_appariement(pivot, table, slug)
        par_appariement[appariement] = par_appariement.get(appariement, 0) + 1

        mandats: list[dict[str, Any]] = []
        if cle is not None:
            nom, prenom, date = cle
            mandats = mandats_locaux(
                appel, nom, prenom, date, constate_le=CONSTATE_LE_SORTANTS)

        chemin_brut = raw_dir / f"{slug}.json"
        brut = _charger(chemin_brut)
        if brut is None:
            # Un profil du périmètre dont le brut manque n'est pas un profil
            # vide : c'est une collecte qui n'a pas eu lieu, et fabriquer un
            # socle ici écrirait une fiche sans identité (§2 règle 5).
            sans_brut.append(slug)
            continue
        brut[CLE_BLOC] = composer_bloc(appariement, mandats, horodatage)
        if appliquer:
            ecrire_profil_json(chemin_brut, brut)
        ecrits.append({"slug": slug, "appariement": appariement,
                       "mandats": len(mandats)})

    if manifest_out is not None and appliquer:
        manifest_out.parent.mkdir(parents=True, exist_ok=True)
        manifest_out.write_text(
            "".join(f"{e['slug']}.json\n" for e in ecrits), encoding="utf-8")

    return {
        "applique": appliquer,
        "nb_profils": len(ecrits),
        "nb_mandats": sum(e["mandats"] for e in ecrits),
        "par_appariement": par_appariement,
        "profils": ecrits,
        "nb_sans_brut": len(sans_brut),
        "sans_brut": sans_brut,
    }


def _appel_reseau(url: str) -> Any:
    """L'accès réseau, isolé ici — le reste du module est testable sans lui."""
    import urllib.parse
    import urllib.request

    decoupe = urllib.parse.urlsplit(url)
    query = urllib.parse.urlencode(
        urllib.parse.parse_qsl(decoupe.query, keep_blank_values=True))
    propre = urllib.parse.urlunsplit(
        (decoupe.scheme, decoupe.netloc, decoupe.path, query, ""))
    requete = urllib.request.Request(
        propre, headers={"User-Agent": "EmpreintePolitique/1.0 (+github.com/stephieED)"})
    with urllib.request.urlopen(requete, timeout=60) as reponse:
        return json.loads(reponse.read().decode("utf-8"))


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--pivot-dir", type=Path, default=DEFAULT_PIVOT_DIR)
    parser.add_argument("--table", type=Path, default=DEFAULT_TABLE)
    parser.add_argument("--apply", action="store_true",
                        help="écrit les profils ; sans lui, simule et compte")
    parser.add_argument("--manifest-out", type=Path,
                        help="les seuls fichiers écrits, un par ligne (#450)")
    args = parser.parse_args(argv)

    try:
        rapport = collecter(
            _appel_reseau, args.raw_dir, args.pivot_dir, args.table,
            appliquer=args.apply, manifest_out=args.manifest_out)
    except RneIndisponible as erreur:
        print(f"::error::RNE_INDISPONIBLE — {erreur}", file=sys.stderr)
        return 1

    print(f"{rapport['nb_profils']} profil(s), {rapport['nb_mandats']} mandat(s) local/locaux")
    for appariement, nombre in sorted(rapport["par_appariement"].items()):
        print(f"  {appariement:<22} {nombre}")
    if rapport["sans_brut"]:
        print(f"::warning::PROFILS_SANS_BRUT — {', '.join(rapport['sans_brut'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
