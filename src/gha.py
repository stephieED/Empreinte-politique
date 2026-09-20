#!/usr/bin/env python3
"""
gha.py — Annotations GitHub Actions, un seul endroit (#518).

## Pourquoi ce module existe

Un échec qui ne vit que dans les 1 200 lignes de log d'un step n'est pas un
échec **déclaré** : l'onglet de résumé du job n'en garde que
`Process completed with exit code 1`, et le log lui-même n'est plus lisible
sans le télécharger. Les annotations `::error::`/`::warning::` sont le seul
canal qui survit à la fermeture d'un run — c'est là que se lit, six mois plus
tard, *ce que* le run a refusé de faire.

Le dépôt avait déjà trois implémentations privées et identiques de ces trois
lignes (`generate_all_profiles._annoter_github`,
`budget_collecte.annoncer_troncature`, `check_quality_gate._gha_annotation`).
#518 en ajoutait deux ; à cinq copies, la question n'est plus de savoir si
elles divergeront. Les trois existantes ne sont pas migrées ici — elles sont
couvertes par leurs propres tests et n'ont rien demandé — mais ce module est
désormais leur destination.

## Ce que ce module ne fait PAS

Il n'écrit pas dans `$GITHUB_STEP_SUMMARY` (voir
`check_quality_gate._write_step_summary`) : le résumé porte des **rapports**
Markdown de plusieurs dizaines de lignes, l'annotation porte **une phrase**
qui doit rester lisible dans une liste. Les deux canaux sont complémentaires,
et un run mort a besoin des deux.
"""

from __future__ import annotations

import os
import sys

#: Niveaux acceptés par GitHub Actions. `debug` est volontairement absent : il
#: n'apparaît que sur un run relancé en mode debug, donc jamais quand on en a
#: besoin.
NIVEAUX = ("error", "warning", "notice")


def actif() -> bool:
    """Vrai dans un runner GitHub Actions, faux partout ailleurs.

    Lu à CHAQUE appel et non figé au chargement du module : les tests règlent
    `GITHUB_ACTIONS` par `monkeypatch.setenv`, après l'import.
    """
    return os.getenv("GITHUB_ACTIONS") == "true"


def annoter(niveau: str, message: str) -> None:
    """Émet une annotation GitHub Actions ; sans effet hors CI.

    Le message est aplati sur une ligne : une commande de workflow s'arrête au
    premier saut de ligne, si bien qu'un message multi-lignes non aplati publie
    sa première ligne en annotation et déverse le reste en texte brut.

    Écrit sur **stdout** : GitHub ne lit les commandes de workflow que là. Un
    `::error::` envoyé sur stderr — le flux naturel des messages d'anomalie de
    ce dépôt — s'affiche dans le log et ne crée aucune annotation.
    """
    if niveau not in NIVEAUX:
        raise ValueError(f"Niveau d'annotation inconnu : {niveau!r}. Attendus : {NIVEAUX}.")
    if not actif():
        return
    propre = message.replace("\n", " ").replace("\r", "")
    print(f"::{niveau}::{propre}", file=sys.stdout, flush=True)
