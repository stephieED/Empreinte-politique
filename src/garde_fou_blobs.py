#!/usr/bin/env python3
"""garde_fou_blobs.py — Le plus gros fichier versionné : garde-fou surveillé,
avec conduite à tenir (#580, arbitrage du 29/08/2026).

Pourquoi ce module existe
-------------------------
Le critère de sortie de l'épic volumétrie #429 portait quatre clauses. La
quatrième — « aucun blob au-dessus de 50 Mo » — **n'était pas un critère** : un
critère s'atteint, celui-là se déclenche. Il a été franchi le jour même de son
écriture, et l'avertissement que GitHub émet au push
(`remote: warning: File ... is 56.00 MB; this is larger than GitHub's
recommended maximum file size of 50.00 MB`) **est passé inaperçu — parce que
rien ne disait quoi en faire.**

Ce module est la réponse aux deux moitiés du problème :

  1. il **mesure** le plus gros fichier des répertoires versionnés, à chaque
     run, dans le quality gate qui décide du commit ;
  2. il **imprime la conduite à tenir** avec le constat, au lieu de laisser un
     chiffre seul dont personne ne sait s'il appelle une action.

Les trois seuils, et pourquoi ceux-là
-------------------------------------
=========================  ==========  ==========================================
Seuil                      Effet       Ce qu'il protège
=========================  ==========  ==========================================
50 Mio                     **avertit** le seuil recommandé par GitHub, celui de
                                       l'avertissement au push. C'est un signal
                                       de tendance, pas une urgence : huit
                                       fichiers le franchissaient au 29/08/2026.
80 Mio                     **bloque**  la marge de manœuvre. Bloquer ici laisse
                                       20 Mio avant le refus, c'est-à-dire le
                                       temps de découper — pas de découvrir le
                                       problème au moment où le push échoue.
100 Mio                    (GitHub)    la limite **dure** : le push est refusé,
                                       et un blob déjà committé ne se retire
                                       plus sans réécrire l'historique.
=========================  ==========  ==========================================

Pourquoi PAS « relever le seuil » quand il se déclenche
--------------------------------------------------------
Mesuré le 29/08/2026 sur `raw_data/profiles` : **8** fichiers au-dessus de
50 Mo, **54** au-dessus de 45. Quarante-six fichiers sont massés entre 45 et 50
— les mêmes députés cosignant les mêmes amendements, donc ils franchissent la
ligne **en bloc** à chaque correction de collecte. Le seuil ne surplombe pas une
queue de distribution : il est planté au milieu d'une falaise. Le porter à
60 Mo achèterait un cycle de correction, pas davantage.

C'est pour cela que la conduite à tenir ci-dessous ne comporte pas l'option
« relever le seuil », et que l'option qu'elle porte — partitionner sur un champ
déjà présent — est celle qui a fait passer le plus gros profil de 56,0 à
23,4 Mo sans supprimer un octet.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional

_MIO = 1024 * 1024

#: Seuil recommandé par GitHub, et seuil de son avertissement au push.
SEUIL_AVERTISSEMENT_OCTETS = 50 * _MIO

#: Seuil bloquant du quality gate. Volontairement **sous** la limite dure : un
#: contrôle qui n'alerte qu'à 100 Mio alerte au moment où il est trop tard, le
#: blob étant alors déjà écrit dans un commit.
SEUIL_BLOQUANT_OCTETS = 80 * _MIO

#: Limite dure de GitHub : au-delà, le push est **refusé**.
LIMITE_DURE_OCTETS = 100 * _MIO

#: Répertoires versionnés qui portent du volume. `pivot_data/amendements`
#: y figure parce que son index `15.json` a été, jusqu'au 28/08/2026, le plus
#: gros blob du dépôt — le garde-fou ne surveille pas que les profils bruts.
REPERTOIRES_SURVEILLES: tuple[str, ...] = (
    "raw_data/profiles",
    "pivot_data/profiles",
    "pivot_data/amendements",
    "pivot_data/groupes",
    "pivot_data/gouvernements",
)

#: Ancre de la décision, citée dans chaque message : un contrôle qui dit
#: « trop gros » sans dire où lire la suite reproduit le défaut qu'il corrige.
REF_DECISION = "docs/decisions/partition-profils-legislature-580.md#garde-fou-blob-580"

CONDUITE_A_TENIR: tuple[str, ...] = (
    "Identifier le champ qui pèse : `python3 src/audit_volumetrie_profils.py "
    "--profils-bruts-dir raw_data/profiles --echantillon 1` nomme le fichier le "
    "plus lourd et le poids de chacun de ses champs.",
    "Partitionner sur un champ DÉJÀ PRÉSENT, comme #580 l'a fait pour "
    "`amendements` sur `legislature` (56,0 → 23,4 Mo). Jamais dénormaliser, "
    "jamais dédupliquer, jamais rogner un champ : `raw_data/` est la couche "
    "source-near, et le principe de l'épic #429 est « normaliser, jamais "
    "supprimer ».",
    "Si le fichier est déjà partitionné, découper plus fin (par texte, par "
    "session) — la partition existante donne le motif à suivre.",
    "NE PAS relever le seuil. Mesuré le 29/08/2026 : 8 fichiers au-dessus de "
    "50 Mo mais 54 au-dessus de 45 — le seuil est planté dans une falaise, le "
    "relever achète un cycle de correction et rien de plus.",
    "NE PAS supprimer de données pour passer sous le seuil : ce serait "
    "échanger une limite d'hébergement contre une perte de collecte.",
    f"Le pourquoi, et la mesure qui l'appuie : {REF_DECISION}.",
)


@dataclass(frozen=True)
class Blob:
    """Un fichier versionné et son poids."""

    chemin: str
    octets: int

    @property
    def mo(self) -> float:
        return self.octets / _MIO


def _mo(octets: int) -> str:
    return f"{octets / _MIO:.2f} Mo"


def inventorier(
    repertoires: Iterable[Path], *, plancher_octets: int = 0
) -> list[Blob]:
    """Tous les fichiers des répertoires donnés, du plus lourd au plus léger.

    `rglob` et non `glob` : depuis #580 un profil brut a des tranches un niveau
    plus bas, et c'est précisément là que vivent désormais les plus gros
    fichiers. Un répertoire absent est ignoré silencieusement — le garde-fou
    n'a pas à décider si un répertoire manquant est une anomalie ; d'autres
    contrôles le font, et bruyamment.
    """
    blobs: list[Blob] = []
    for repertoire in repertoires:
        repertoire = Path(repertoire)
        if not repertoire.is_dir():
            continue
        for chemin in repertoire.rglob("*"):
            try:
                if not chemin.is_file():
                    continue
                taille = chemin.stat().st_size
            except OSError:
                continue
            if taille >= plancher_octets:
                blobs.append(Blob(str(chemin), taille))
    blobs.sort(key=lambda b: (-b.octets, b.chemin))
    return blobs


def evaluer(
    repertoires: Iterable[Path],
    *,
    seuil_avertissement: int = SEUIL_AVERTISSEMENT_OCTETS,
    seuil_bloquant: int = SEUIL_BLOQUANT_OCTETS,
) -> dict[str, Any]:
    """Constat sur le plus gros blob. Fonction quasi pure (elle lit `stat`).

    Rend un dict sérialisable — jamais un simple booléen : ce qui a manqué en
    #429, ce n'est pas un verdict, c'est de savoir **quel fichier**, **de
    combien**, et **quoi faire**.
    """
    if seuil_avertissement > seuil_bloquant:
        raise ValueError(
            "seuil d'avertissement au-dessus du seuil bloquant : le garde-fou "
            "bloquerait avant d'avertir."
        )
    blobs = inventorier(repertoires, plancher_octets=seuil_avertissement)
    au_dessus_avert = [b for b in blobs if b.octets >= seuil_avertissement]
    au_dessus_bloquant = [b for b in blobs if b.octets >= seuil_bloquant]
    plus_gros: Optional[Blob] = blobs[0] if blobs else None

    return {
        "seuil_avertissement": seuil_avertissement,
        "seuil_bloquant": seuil_bloquant,
        "limite_dure": LIMITE_DURE_OCTETS,
        "plus_gros": {"chemin": plus_gros.chemin, "octets": plus_gros.octets}
        if plus_gros
        else None,
        "nb_au_dessus_avertissement": len(au_dessus_avert),
        "nb_au_dessus_bloquant": len(au_dessus_bloquant),
        "au_dessus_avertissement": [
            {"chemin": b.chemin, "octets": b.octets} for b in au_dessus_avert[:20]
        ],
        "au_dessus_bloquant": [
            {"chemin": b.chemin, "octets": b.octets} for b in au_dessus_bloquant[:20]
        ],
        "bloquant": bool(au_dessus_bloquant),
    }


def rapport(constat: dict[str, Any]) -> tuple[list[str], list[str], str, str]:
    """(erreurs, avertissements, console, markdown).

    `erreurs` non vide ⇒ le quality gate doit bloquer le commit.
    """
    erreurs: list[str] = []
    avertissements: list[str] = []

    seuil_a = constat["seuil_avertissement"]
    seuil_b = constat["seuil_bloquant"]
    plus_gros = constat.get("plus_gros")

    lignes_console = ["", "─" * 69, "§7 — GARDE-FOU : taille du plus gros fichier versionné", "─" * 69]
    lignes_md = [
        "",
        "### 🧱 §7 — Garde-fou : taille du plus gros fichier versionné",
        "",
        f"Seuils : avertissement **{_mo(seuil_a)}** · blocage **{_mo(seuil_b)}** · "
        f"limite dure GitHub **{_mo(constat['limite_dure'])}** (push refusé).",
        "",
    ]

    if plus_gros is None:
        lignes_console.append(
            f"  ✓ Aucun fichier au-dessus de {_mo(seuil_a)}."
        )
        lignes_md.append(f"✅ Aucun fichier au-dessus de {_mo(seuil_a)}.")
        return erreurs, avertissements, "\n".join(lignes_console), "\n".join(lignes_md)

    lignes_console.append(
        f"  Plus gros fichier : {plus_gros['chemin']} — {_mo(plus_gros['octets'])}"
    )

    for entree in constat["au_dessus_bloquant"]:
        erreurs.append(
            f"{entree['chemin']} pèse {_mo(entree['octets'])} — au-dessus du seuil "
            f"bloquant de {_mo(seuil_b)}, et à {_mo(constat['limite_dure'] - entree['octets'])} "
            f"du refus de push."
        )
    bloquants = {e["chemin"] for e in constat["au_dessus_bloquant"]}
    for entree in constat["au_dessus_avertissement"]:
        if entree["chemin"] in bloquants:
            continue
        avertissements.append(
            f"{entree['chemin']} pèse {_mo(entree['octets'])} — au-dessus du seuil "
            f"recommandé par GitHub ({_mo(seuil_a)})."
        )

    nb_a = constat["nb_au_dessus_avertissement"]
    nb_b = constat["nb_au_dessus_bloquant"]
    if nb_b:
        lignes_console.append(
            f"  ✗ {nb_b} fichier(s) ≥ {_mo(seuil_b)} — COMMIT BLOQUÉ."
        )
        lignes_md.append(f"❌ **{nb_b} fichier(s) ≥ {_mo(seuil_b)} — commit bloqué.**")
    elif nb_a:
        lignes_console.append(
            f"  ⚠ {nb_a} fichier(s) ≥ {_mo(seuil_a)} — non bloquant, à traiter."
        )
        lignes_md.append(f"⚠️ **{nb_a} fichier(s) ≥ {_mo(seuil_a)}** — non bloquant, à traiter.")
    else:
        lignes_console.append(f"  ✓ Aucun fichier au-dessus de {_mo(seuil_a)}.")
        lignes_md.append(f"✅ Aucun fichier au-dessus de {_mo(seuil_a)}.")

    entrees = constat["au_dessus_bloquant"] or constat["au_dessus_avertissement"]
    if entrees:
        lignes_md += ["", "| Fichier | Poids |", "| --- | ---: |"]
        for entree in entrees:
            lignes_console.append(f"     - {entree['chemin']} : {_mo(entree['octets'])}")
            lignes_md.append(f"| `{entree['chemin']}` | {_mo(entree['octets'])} |")

    if nb_a or nb_b:
        lignes_console += ["", "  CONDUITE À TENIR :"]
        lignes_md += ["", "**Conduite à tenir**", ""]
        for i, etape in enumerate(CONDUITE_A_TENIR, start=1):
            lignes_console.append(f"    {i}. {etape}")
            lignes_md.append(f"{i}. {etape}")

    return erreurs, avertissements, "\n".join(lignes_console), "\n".join(lignes_md)
