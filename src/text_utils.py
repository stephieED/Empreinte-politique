#!/usr/bin/env python3
"""
text_utils.py — Petits utilitaires de texte partagés entre les modules de génération.
"""

import re
import unicodedata


def slugify(text: str) -> str:
    """Dérive un identifiant slug (ex. "les-republicains-lr") à partir d'un libellé."""
    decomposed = unicodedata.normalize("NFKD", text)
    ascii_only = "".join(c for c in decomposed if not unicodedata.combining(c))
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", ascii_only.lower())).strip("-")
