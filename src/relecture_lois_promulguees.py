#!/usr/bin/env python3
"""Confronter nos textes promulgués aux lois du Journal officiel (#1248, contrôle des totaux).

Pourquoi ce module existe
-------------------------
Les relectures de #1248 disent si ce que nous publions est juste ; les
contrôles de totaux, si nous avons tout. Celui-ci est le seul **croisement
indépendant de l'Assemblée** : la table des lois du Journal officiel
(`raw_data/lois_jorf.json`, tenue par `extract-actes-jo` depuis les livraisons
de la DILA) contre nos textes promulgués (`pivot_data/textes_promulgues.json`,
tirés des archives de dossiers de l'Assemblée). Ils se joignent par le numéro
de la loi, que les deux sources publient.

Les deux sens, et ce qui n'est pas signalé
------------------------------------------
| Constat | Traitement |
| --- | --- |
| loi du JO (depuis le 20/06/2012) absente de nos textes, **déclarée** absente de l'open data de l'AN (`config/lois_absentes_open_data_an.json`, #1424) | relevée, pas signalée : un trou de la source |
| la même, **publiée après** la date à laquelle nos dossiers sont à jour (`an.dossiers` du fichier de fraîcheur, #1389) | relevée, pas signalée : pas encore relue — les dossiers sont hebdomadaires |
| la même, autrement | **signalée** : une loi que notre collecte a perdue |
| un de nos textes promulgués dont le numéro manque à la table du JO | **signalé** |
| une loi déclarée absente que nous publions pourtant | **signalée** : la liste est à revoir |

Mesuré le 04/11/2026 (table du run du 03/11, textes du même run) : 1 091 lois
du JO depuis le 20/06/2012 — 1 019 publiées chez nous, 71 déclarées, 1 pas
encore relue —, 0 écart ; aucun des 1 019 numéros de nos textes ne manque à la
table. (1 020 textes pour 1 019 numéros : la loi 2017-1338 est portée par deux
uids de dossier, `DLR5L14N35824` et `DLR5L15N35824`.)

Une entrée manquante (table, textes) rend le contrôle « non vérifié », jamais
un écart (§2 règle 5). Rien ne bloque.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

#: Le début de la XIVe, la première législature dont nous publions les dossiers.
DEBUT_DU_CORPUS = "2012-06-20"


def _lire(chemin: Optional[Path]) -> Optional[Any]:
    if chemin is None or not Path(chemin).is_file():
        return None
    with open(chemin, encoding="utf-8") as f:
        return json.load(f)


def dossiers_a_jour_au(fraicheur: Optional[dict[str, Any]]) -> Optional[str]:
    if not isinstance(fraicheur, dict):
        return None
    familles = fraicheur.get("familles") or fraicheur
    return ((familles.get("an.dossiers") or {}).get("a_jour_au")) if isinstance(familles, dict) else None


@dataclass
class Bilan:
    non_verifie: Optional[str] = None
    lois_du_jo: int = 0
    textes_publies: int = 0
    declarees_absentes: list[str] = field(default_factory=list)
    pas_encore_relues: list[str] = field(default_factory=list)
    #: écarts signalés
    perdues: list[dict[str, str]] = field(default_factory=list)
    absentes_du_jo: list[dict[str, Any]] = field(default_factory=list)
    declarees_a_tort: list[str] = field(default_factory=list)

    @property
    def a_signaler(self) -> int:
        return len(self.perdues) + len(self.absentes_du_jo) + len(self.declarees_a_tort)


def controler(lois_jo: dict[str, list[list[str]]], textes: dict[str, dict[str, Any]],
              declarees: set[str], a_jour_au: Optional[str]) -> Bilan:
    bilan = Bilan()
    publies: dict[str, list[str]] = {}
    for uid, texte in textes.items():
        numero = texte.get("numero_loi")
        if numero:
            publies.setdefault(numero, []).append(uid)
    bilan.textes_publies = len(publies)
    for numero, publications in sorted(lois_jo.items()):
        if not publications:
            continue
        cid, publiee_le = publications[0][0], publications[0][1]
        if publiee_le < DEBUT_DU_CORPUS:
            continue
        bilan.lois_du_jo += 1
        if numero in publies:
            if numero in declarees:
                bilan.declarees_a_tort.append(numero)
            continue
        if numero in declarees:
            bilan.declarees_absentes.append(numero)
        elif a_jour_au and publiee_le > a_jour_au:
            bilan.pas_encore_relues.append(numero)
        else:
            bilan.perdues.append({"numero_loi": numero, "jorftext": cid, "publiee_au_jo_le": publiee_le})
    for numero, uids in sorted(publies.items()):
        if numero not in lois_jo:
            bilan.absentes_du_jo.append({"numero_loi": numero, "dossiers": sorted(uids)})
    return bilan


def rapport(bilan: Bilan, a_jour_au: Optional[str]) -> tuple[str, dict[str, Any]]:
    resume = {k: v for k, v in bilan.__dict__.items()}
    resume["a_signaler"] = bilan.a_signaler
    resume["dossiers_a_jour_au"] = a_jour_au
    if bilan.non_verifie:
        return f"Non vérifié : {bilan.non_verifie}.\n", resume
    lignes = [
        f"**{bilan.a_signaler}** écart(s) entre le Journal officiel et nos textes promulgués.",
        "",
        f"| Population | Nombre |",
        "| --- | ---: |",
        f"| Lois publiées au JO depuis le 20/06/2012 (lois et lois organiques) | {bilan.lois_du_jo} |",
        f"| … absentes de l'open data de l'AN, déclarées (#1424) | {len(bilan.declarees_absentes)} |",
        f"| … publiées après nos dossiers (à jour au {a_jour_au or '—'}), pas encore relues | {len(bilan.pas_encore_relues)} |",
        f"| … **absentes de nos textes promulgués** | **{len(bilan.perdues)}** |",
        f"| Nos textes promulgués (numéros distincts) | {bilan.textes_publies} |",
        f"| … **dont le numéro manque à la table du JO** | **{len(bilan.absentes_du_jo)}** |",
        f"| Lois déclarées absentes que nous publions pourtant | **{len(bilan.declarees_a_tort)}** |",
    ]
    if bilan.perdues:
        lignes += ["", "### Lois du Journal officiel absentes de nos textes promulgués", "",
                   "| Loi | JORFTEXT | Publiée au JO le |", "| --- | --- | --- |"]
        lignes += [f"| {e['numero_loi']} | {e['jorftext']} | {e['publiee_au_jo_le']} |" for e in bilan.perdues]
    if bilan.absentes_du_jo:
        lignes += ["", "### Nos textes promulgués absents de la table du Journal officiel", "",
                   "| Loi | Dossiers |", "| --- | --- |"]
        lignes += [f"| {e['numero_loi']} | {', '.join(e['dossiers'])} |" for e in bilan.absentes_du_jo]
    if bilan.declarees_a_tort:
        lignes += ["", "### Déclarées absentes de l'open data, mais publiées",
                   "", "À retirer de `config/lois_absentes_open_data_an.json` : " + ", ".join(bilan.declarees_a_tort)]
    return "\n".join(lignes) + "\n", resume


def main(argv: Optional[list[str]] = None) -> int:
    parseur = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parseur.add_argument("--lois-jorf", type=Path, default=Path("raw_data/lois_jorf.json"))
    parseur.add_argument("--textes-promulgues", type=Path, default=Path("pivot_data/textes_promulgues.json"))
    parseur.add_argument("--absentes", type=Path, default=Path("config/lois_absentes_open_data_an.json"))
    parseur.add_argument("--fraicheur", type=Path, default=Path("pivot_data/fraicheur_sources.json"))
    parseur.add_argument("--out", type=Path, required=True)
    parseur.add_argument("--out-json", type=Path, required=True)
    args = parseur.parse_args(argv)

    table, textes = _lire(args.lois_jorf), _lire(args.textes_promulgues)
    a_jour_au = dossiers_a_jour_au(_lire(args.fraicheur))
    if not isinstance(table, dict) or not isinstance(table.get("lois"), dict):
        bilan = Bilan(non_verifie=f"table du Journal officiel illisible ({args.lois_jorf})")
    elif not isinstance(textes, dict) or not isinstance(textes.get("textes"), dict):
        bilan = Bilan(non_verifie=f"textes promulgués illisibles ({args.textes_promulgues})")
    else:
        absentes = _lire(args.absentes) or {}
        declarees = {loi["numero_loi"] for loi in absentes.get("lois") or [] if loi.get("numero_loi")}
        bilan = controler(table["lois"], textes["textes"], declarees, a_jour_au)
    texte, resume = rapport(bilan, a_jour_au)
    resume["releve_le"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    args.out.write_text(texte, encoding="utf-8")
    args.out_json.write_text(json.dumps(resume, ensure_ascii=False, indent=2), encoding="utf-8")
    print(texte)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
