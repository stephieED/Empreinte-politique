#!/usr/bin/env python3
"""L'explorateur des données : `pivot_data/` et `raw_data/` en tableaux reliés.

Une base SQLite que Datasette affiche dans le navigateur, en local
(`scripts/explorateur.sh`). Demandé par la propriétaire le 29/10/2026 pour
naviguer d'une entrée à l'autre sans lire le JSON à la main.

**Lecture seule.** Le module lit le dépôt et écrit une seule chose : la base,
sous `.cache/explorateur/` (ignoré par git), jamais committée ni publiée. C'est
une **photo** : elle porte le commit lu (`_construction`), et la commande la
reconstruit quand il a changé.

## La forme

- Un document (profil, groupe, lignée, gouvernement, fichier de `raw_data`) est
  une ligne de sa table racine : ses champs simples sont des colonnes, un objet
  imbriqué est aplati en colonnes préfixées (`identite_date_naissance`).
- **Chaque liste d'objets devient une table fille** (`profils__mandats`),
  dont chaque ligne pointe vers son parent (`_parent`). Une liste dans une liste
  fait une table petite-fille. Les identifiants connus (`scrutin_id`,
  `membre_id`, `groupe_id`, `lignee_id`) deviennent des liens.
- Les tables du brut sont préfixées `brut_` ; un profil brut et son profil
  pivot se renvoient l'un à l'autre.
- `documents` porte le document entier, affiché en arborescence repliable,
  pour les candidats déclarés, les membres des gouvernements, les groupes, les
  lignées, les gouvernements et les petits fichiers de `raw_data`.

## Ce qui n'est pas chargé, pour la taille

Les votes et les amendements des membres des groupes (`roster_groupe`) : 13,7
millions de lignes au pivot le 29/10/2026, pour une base qui passerait de
quelques Go à plusieurs dizaines. Chaque profil le dit (`votes__non_charge`).

Usage :

    python3 src/explorateur_donnees.py --base .cache/explorateur/donnees.db
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Iterable, Optional

RACINE = Path(__file__).resolve().parents[1]
BASE_PAR_DEFAUT = RACINE / ".cache" / "explorateur" / "donnees.db"

#: Provenance dont les listes les plus lourdes ne sont pas chargées.
PROVENANCE_ALLEGEE = "roster_groupe"
LISTES_NON_CHARGEES = ("votes", "amendements", "amendements_partitionnes")
#: Le document entier n'est gardé que pour ces provenances (2 Go de roster sinon).
PROVENANCES_DOCUMENT = ("candidat_declare", "roster_gouvernement")

RACINES = {"profils": "id", "groupes": "groupe_id", "lignees": "lignee_id",
           "gouvernements": "gouvernement_id", "scrutins": "id", "documents": "cle",
           "brut_profils": "slug"}
#: Une colonne de ce nom, dans n'importe quelle table, est un lien.
CIBLES = {"scrutin_id": ("scrutins", "id"), "membre_id": ("profils", "id"),
          "groupe_id": ("groupes", "groupe_id"), "lignee_id": ("lignees", "lignee_id")}
LOT = 20000
#: Au-delà, un dictionnaire devient une table fille plutôt que des colonnes.
CLES_MAX_EN_COLONNES = 50


class Base:
    """Les tables, créées au premier lot avec leurs liens, élargies ensuite."""

    def __init__(self, chemin: Path):
        self.cx = sqlite3.connect(chemin)
        self.cx.executescript("PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF;")
        self.colonnes: dict[str, list[str]] = {}
        # SQLite compare les noms de colonnes sans la casse : deux clés du JSON
        # qui ne diffèrent que par elle (mesuré le 29/10/2026 sur un agrégat de
        # mandats) recevraient le même nom. Chaque clé a son nom de colonne.
        self.noms: dict[str, dict[str, str]] = {}
        self.cles: dict[str, str] = {}
        self.tampons: dict[str, list[dict[str, Any]]] = {}
        self.liens: dict[str, list[tuple[str, str, str]]] = {}

    def ajouter(self, table: str, ligne: dict[str, Any], cle: str, liens=()) -> None:
        self.cles[table] = cle
        if liens:
            self.liens.setdefault(table, list(liens))
        self.tampons.setdefault(table, []).append(ligne)
        if len(self.tampons[table]) >= LOT:
            self.vider(table)

    def vider(self, table: Optional[str] = None) -> None:
        for nom in [table] if table else list(self.tampons):
            lignes = self.tampons.get(nom) or []
            if not lignes:
                continue
            cles = list(dict.fromkeys(k for l in lignes for k in l))
            correspondance = self.noms.setdefault(nom, {})
            if nom not in self.colonnes:
                self._creer(nom, [self._nommer(nom, k) for k in cles])
            for k in cles:
                if k not in correspondance:
                    colonne = self._nommer(nom, k)
                    self.cx.execute(f'ALTER TABLE {_q(nom)} ADD COLUMN {_q(colonne)}')
                    self.colonnes[nom].append(colonne)
            inverse = {c: k for k, c in correspondance.items()}
            cols = self.colonnes[nom]
            noms_sql = ", ".join(_q(c) for c in cols)
            marques = ", ".join("?" for _ in cols)
            requete = f'INSERT OR REPLACE INTO {_q(nom)} ({noms_sql}) VALUES ({marques})'
            self.cx.executemany(requete, ([_valeur(l.get(inverse.get(c, c))) for c in cols] for l in lignes))
            self.tampons[nom] = []

    def _nommer(self, table: str, cle: str) -> str:
        """Le nom de colonne d'une clé, unique sans tenir compte de la casse."""
        correspondance = self.noms.setdefault(table, {})
        if cle in correspondance:
            return correspondance[cle]
        pris = {c.lower() for c in correspondance.values()}
        colonne, n = cle, 2
        while colonne.lower() in pris:
            colonne, n = f"{cle} ({n})", n + 1
        correspondance[cle] = colonne
        return colonne

    def _creer(self, nom: str, noms: list[str]) -> None:
        # Les liens se posent À LA CRÉATION : les ajouter ensuite recopie chaque
        # table une fois par lien (plus de 40 min mesurées le 29/10/2026).
        cle = self.cles[nom]
        cols = [cle] + [c for c in noms if c != cle]
        liens = list(self.liens.get(nom, []))
        if "__" in nom:
            parent = nom.rsplit("__", 1)[0]
            liens.append(("_parent", parent, RACINES.get(parent, "_id")))
        for col, (cible, cle_cible) in CIBLES.items():
            if col in cols and RACINES.get(nom) != col:
                liens.append((col, cible, cle_cible))
        definition = [f'{_q(cle)} TEXT PRIMARY KEY'] + [_q(c) for c in cols[1:]]
        definition += [f'FOREIGN KEY({_q(c)}) REFERENCES {_q(t)}({_q(k)})' for c, t, k in liens
                       if c in cols]
        self.cx.execute(f'CREATE TABLE {_q(nom)} ({", ".join(definition)})')
        self.colonnes[nom] = cols

    def indexer(self) -> None:
        for nom, cols in self.colonnes.items():
            for c in cols:
                if c == "_parent" or c in CIBLES or c in ("profil", "brut"):
                    self.cx.execute(f'CREATE INDEX IF NOT EXISTS {_q("ix_" + nom + "_" + c)} ON {_q(nom)}({_q(c)})')

    def fermer(self) -> None:
        self.vider()
        self.indexer()
        self.cx.commit()
        self.cx.close()


def _q(nom: str) -> str:
    """Un identifiant SQL entre guillemets, ses guillemets doublés : des clés du
    corpus en portent (« rapporteur sur "la fiscalité des hébergements
    touristiques" », groupe UMP-14)."""
    return '"' + nom.replace('"', '""') + '"'


def _valeur(v: Any) -> Any:
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False)
    return v


def _simple(v: Any) -> bool:
    return v is None or isinstance(v, (str, int, float, bool))


def aplatir(base: Base, objet: dict[str, Any], table: str, ligne: dict[str, Any],
            prefixe: str, ident: str, exclus: Iterable[str] = ()) -> None:
    """Remplit `ligne` des champs de `objet` ; envoie chaque liste d'objets en table fille."""
    for cle, valeur in objet.items():
        nom = f"{prefixe}{cle}"
        if cle in exclus:
            ligne[f"{nom}__non_charge"] = (len(valeur) if isinstance(valeur, (list, dict)) else None)
        elif _simple(valeur):
            ligne[nom] = valeur
        elif isinstance(valeur, dict):
            if (len(valeur) > 12 and all(isinstance(v, dict) for v in valeur.values())) \
                    or len(valeur) > CLES_MAX_EN_COLONNES:
                # Un dictionnaire indexé (par identifiant) : une table fille, la
                # clé en colonne. Au-delà de 50 clés, quelle que soit la forme des
                # valeurs (`lois_jorf.json` : 8 820 clés, des listes), sinon
                # chaque clé deviendrait une colonne (SQLite en refuse au-delà de 2 000).
                fille = f"{table}__{nom}"
                for rang, (k, v) in enumerate(valeur.items(), 1):
                    enfant = {"_id": f"{ident}/{nom}/{k}", "_parent": ident, "_cle": k, "_rang": rang}
                    if isinstance(v, dict):
                        aplatir(base, v, fille, enfant, "", enfant["_id"])
                    else:
                        enfant["valeur"] = v
                    base.ajouter(fille, enfant, "_id")
                ligne[f"{nom}__nb"] = len(valeur)
            else:
                aplatir(base, valeur, table, ligne, f"{nom}_", ident)
        elif isinstance(valeur, list):
            if valeur and all(isinstance(v, dict) for v in valeur):
                fille = f"{table}__{nom}"
                for rang, v in enumerate(valeur, 1):
                    enfant = {"_id": f"{ident}/{nom}/{rang}", "_parent": ident, "_rang": rang}
                    aplatir(base, v, fille, enfant, "", enfant["_id"])
                    base.ajouter(fille, enfant, "_id")
                ligne[f"{nom}__nb"] = len(valeur)
            else:
                ligne[nom] = json.dumps(valeur, ensure_ascii=False) if valeur else None


def _lire(chemin: Path) -> Any:
    with open(chemin, encoding="utf-8") as f:
        return json.load(f)


def _document(base: Base, cle: str, type_: str, fichier: str, doc: Any) -> None:
    base.ajouter("documents", {"cle": cle, "type": type_, "fichier": fichier,
                               "document": json.dumps(doc, ensure_ascii=False)}, "cle")


def construire(depot: Path, chemin_base: Path) -> dict[str, Any]:
    """Construit la base dans un fichier temporaire, puis la met en place d'un coup."""
    debut = time.time()
    chemin_base.parent.mkdir(parents=True, exist_ok=True)
    provisoire = chemin_base.with_name(chemin_base.name + ".construction")
    provisoire.unlink(missing_ok=True)
    base = Base(provisoire)
    pivot, brut = depot / "pivot_data", depot / "raw_data"

    provenances: dict[str, str] = {}
    for chemin in sorted((pivot / "profiles").glob("*.pivot.json")):
        doc = _lire(chemin)
        provenance = (doc.get("meta") or {}).get("provenance") or ""
        provenances[doc["id"]] = provenance
        fichier = f"pivot_data/profiles/{chemin.name}"
        ligne = {"id": doc["id"], "_fichier": fichier, "brut": doc["id"]}
        aplatir(base, doc, "profils", ligne, "", doc["id"],
                LISTES_NON_CHARGEES if provenance == PROVENANCE_ALLEGEE else ())
        base.ajouter("profils", ligne, "id", liens=[("brut", "brut_profils", "slug")])
        if provenance in PROVENANCES_DOCUMENT:
            _document(base, f"profil:{doc['id']}", "profil", fichier, doc)

    for dossier, cle in (("groupes", "groupe_id"), ("lignees", "lignee_id"),
                         ("gouvernements", "gouvernement_id")):
        for chemin in sorted((pivot / dossier).glob("*.json")):
            doc = _lire(chemin)
            fichier = f"pivot_data/{dossier}/{chemin.name}"
            ligne = {"_fichier": fichier}
            aplatir(base, doc, dossier, ligne, "", doc[cle])
            base.ajouter(dossier, ligne, cle)
            _document(base, f"{dossier}:{doc[cle]}", dossier, fichier, doc)

    if (pivot / "scrutins.json").is_file():
        for s in _lire(pivot / "scrutins.json").get("scrutins") or []:
            ligne: dict[str, Any] = {}
            aplatir(base, s, "scrutins", ligne, "", s["id"])
            base.ajouter("scrutins", ligne, "id")

    for chemin in sorted((brut / "profiles").glob("*.json")):
        doc = _lire(chemin)
        slug = doc.get("slug") or chemin.stem
        provenance = provenances.get(slug, "")
        allege = provenance == PROVENANCE_ALLEGEE
        fichier = f"raw_data/profiles/{chemin.name}"
        ligne = {"slug": slug, "_fichier": fichier, "profil": slug}
        aplatir(base, doc, "brut_profils", ligne, "", slug, LISTES_NON_CHARGEES if allege else ())
        base.ajouter("brut_profils", ligne, "slug", liens=[("profil", "profils", "id")])
        if allege:
            continue
        # Les tranches d'amendements (#580), rattachées au profil brut.
        for tranche in sorted((brut / "profiles" / slug).glob("*.json")):
            contenu = _lire(tranche)
            for rang, amendement in enumerate(contenu.get("amendements") or [], 1):
                enfant = {"_id": f"{slug}/{tranche.stem}/{rang}", "_parent": slug,
                          "_legislature": tranche.stem, "_rang": rang}
                aplatir(base, amendement, "brut_profils__amendements", enfant, "", enfant["_id"])
                base.ajouter("brut_profils__amendements", enfant, "_id")
        if provenance in PROVENANCES_DOCUMENT:
            _document(base, f"brut:{slug}", "brut_profil", fichier, doc)

    for chemin in sorted(brut.glob("*.json")):
        doc = _lire(chemin)
        table = f"brut_{chemin.stem}"
        fichier = f"raw_data/{chemin.name}"
        ligne = {"_id": chemin.stem, "_fichier": fichier}
        if isinstance(doc, dict):
            aplatir(base, doc, table, ligne, "", chemin.stem)
        base.ajouter(table, ligne, "_id")
        _document(base, f"brut:{chemin.stem}", "brut_fichier", fichier, doc)

    commit = _commit(depot)
    base.ajouter("_construction", {"_id": "construction", "commit": commit,
                                   "construite_le": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                                   "duree_s": round(time.time() - debut)}, "_id")
    base.fermer()
    os.replace(provisoire, chemin_base)
    return {"commit": commit, "duree_s": round(time.time() - debut), "taille_mo": round(chemin_base.stat().st_size / 1e6)}


def _commit(depot: Path) -> Optional[str]:
    try:
        return subprocess.run(["git", "-C", str(depot), "rev-parse", "HEAD"], capture_output=True,
                              text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def commit_de_la_base(chemin_base: Path) -> Optional[str]:
    """Le commit que la base photographie, ou None si elle n'existe pas."""
    if not chemin_base.is_file():
        return None
    try:
        cx = sqlite3.connect(f"file:{chemin_base}?mode=ro", uri=True)
        ligne = cx.execute('SELECT "commit" FROM "_construction"').fetchone()
        cx.close()
        return ligne[0] if ligne else None
    except sqlite3.Error:
        return None


def main(argv: Optional[Iterable[str]] = None) -> int:
    analyseur = argparse.ArgumentParser(description=__doc__,
                                        formatter_class=argparse.RawDescriptionHelpFormatter)
    analyseur.add_argument("--depot", type=Path, default=RACINE)
    analyseur.add_argument("--base", type=Path, default=BASE_PAR_DEFAUT)
    analyseur.add_argument("--si-perimee", action="store_true",
                           help="ne reconstruit que si le commit du dépôt a changé")
    args = analyseur.parse_args(list(argv) if argv is not None else None)
    if args.si_perimee and commit_de_la_base(args.base) == _commit(args.depot) is not None:
        print(f"Base à jour ({commit_de_la_base(args.base)[:10]}) : rien à reconstruire.")
        return 0
    print("Construction de la base de l'explorateur (lecture seule du dépôt)…")
    rapport = construire(args.depot, args.base)
    print(f"Base construite : {rapport['taille_mo']} Mo en {rapport['duree_s']} s, "
          f"commit {str(rapport['commit'])[:10]}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
