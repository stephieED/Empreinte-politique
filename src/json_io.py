#!/usr/bin/env python3
"""
json_io.py — Écriture JSON des profils : compact pour les profils individuels,
indenté pour les documents relus à la main (#433, sous-issue de l'épic
volumétrie #429).

Mesuré sur les 752 profils du roster complet (`audit_volumetrie_profils.py`) :
8 093 Mo sur disque pour 5 263 Mo de contenu réel — **2 830 Mo, 35 %, ne sont
que de l'indentation**. C'est le seul levier de #429 qui ne touche aucun champ,
aucun schéma et aucun consommateur : tout le pipeline relit ses fichiers par
`json.load()`, jamais ligne à ligne.

Contrepartie assumée
--------------------
Un profil compact n'est plus lisible en diff git : chaque profil modifié
apparaît comme une seule ligne changée. Cet avantage était déjà perdu en
pratique — le commit de données du 2026-08-18 affichait 16,6 millions de lignes
modifiées sur 239 fichiers, un diff que personne ne lit.

D'où le partage :
  - **compact** — `raw_data/profiles/` et `pivot_data/profiles/` (le volume),
    et `pivot_data/lignees/` depuis #836 ;
  - **indenté** — `pivot_data/groupes`, `pivot_data/gouvernements`,
    `pivot_data/partis`, les rosters, les rapports d'audit et les checkpoints :
    9,8 Mo au total à l'écriture de cette note, effectivement relus à la main
    lors des audits.

Le critère est « relu à la main », jamais le voisinage de répertoire (#836)
--------------------------------------------------------------------------
Une fiche de LIGNÉE est l'union de ses maillons : `AN:LIGNEE:REN` pèse **11,5
Mo** indentée, dont 5,0 Mo de `cohesion_votes` et 2,7 Mo de `mandats_agreges`
— 53 Mo pour les dix, contre 36 en compact. Personne n'ouvre un document de
11 Mo, et son diff est « une seule ligne changée » dans les deux formats : la
contrepartie assumée ci-dessus est déjà payée, l'économie de 32 %, elle, ne
l'est pas. La ranger avec `pivot_data/groupes` parce qu'elle en est voisine
appliquerait la LISTE au lieu du CRITÈRE.

À relire : les 9,8 Mo cités plus haut datent de #433. `pivot_data/groupes` en
pèse 64 à lui seul depuis que 23 fiches y sont publiées, et le jour où ces
fiches cesseront elles aussi d'être ouvertes à la main, c'est le même
raisonnement qui s'appliquera — mesure à l'appui, pas par analogie.

Le format n'est jamais porteur de sens : `preserve_stable_freshness_timestamps`
et les comparaisons de contenu de #343 travaillent sur la structure déjà
désérialisée (`_pivot_content_fingerprint` re-sérialise avec `sort_keys=True`),
donc « contenu identique » reste détecté indépendamment de l'indentation.
"""

from pathlib import Path
from typing import Any, Callable, Optional
import json
import re

# Pas d'espace après `,` ni `:` — les valeurs par défaut de `json.dumps` en
# ajoutent un, soit ~1 octet par champ sur des profils qui en portent des
# centaines de milliers.
SEPARATEURS_COMPACTS = (",", ":")


def dumps_profil_json(document: Any) -> str:
    """Sérialise un profil individuel en JSON compact.

    `ensure_ascii=False` : les accents restent en UTF-8 réel plutôt qu'en
    `\\uXXXX`, qui coûterait 6 octets par caractère accentué — sur des profils
    en français, l'échappement annulerait une part du gain.
    """
    return json.dumps(document, ensure_ascii=False, separators=SEPARATEURS_COMPACTS)


def ecrire_profil_json(chemin: Path, document: Any) -> None:
    """Écrit un profil individuel (brut ou pivot) en JSON compact.

    Crée le répertoire parent au besoin : les appelants le faisaient déjà
    séparément, l'opération est idempotente et rend l'helper sûr à appeler
    depuis n'importe quel générateur.
    """
    chemin = Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(dumps_profil_json(document), encoding="utf-8")


#: `genere_le` d'un index, lu dans son entête sans désérialiser le fichier :
#: `pivot_data/amendements/15.json` pèse 70 Mo, et le charger pour y lire une
#: date coûterait plusieurs centaines de Mo de mémoire au job qui l'écrit.
_GENERE_LE = re.compile(rb'"genere_le"\s*:\s*("(?:[^"\\]|\\.)*"|null)')
#: L'entête de tous les index publiés tient dans ces octets : `genere_le` y
#: est la deuxième ou troisième clé.
_TAILLE_ENTETE = 4096


def ecrire_index_json(
    chemin: Path,
    document: dict[str, Any],
    serialiser: Callable[[Any], str] = dumps_profil_json,
) -> bool:
    """Écrit un index partagé, **sauf si seul son `genere_le` changerait** (#1075).

    Mesuré sur le commit du run `35648745220` (21/09/2026) : sur les 18 fichiers
    de `pivot_data/` modifiés hors profils, **13 ne changeaient que par
    `genere_le`** — les huit fichiers d'amendements, législatures closes
    comprises, les index de scrutins, `documents_europeens.json`,
    `commissions_dossiers.json`. Chaque run republiait ~70 Mo pour une date.

    Le document est sérialisé avec l'ancien `genere_le` ; s'il est alors
    identique **octet pour octet** au fichier en place, rien n'est écrit, et
    `genere_le` garde la date du dernier changement réel. Le même
    `serialiser` que l'écriture sert à la comparaison : un changement de format
    compte comme un changement. Même contrat que
    `merge_profile.preserve_stable_freshness_timestamps` (#343) pour les
    profils.

    Rend `True` si le fichier a été écrit.
    """
    chemin = Path(chemin)
    texte = serialiser(document)
    try:
        ancien = chemin.read_bytes()
    except OSError:
        ancien = None
    if ancien is not None and "genere_le" in document:
        m = _GENERE_LE.search(ancien[:_TAILLE_ENTETE])
        if m:
            candidat = serialiser({**document, "genere_le": json.loads(m.group(1))})
            if candidat.encode("utf-8") == ancien:
                return False
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(texte, encoding="utf-8")
    return True


def dumps_indente(document: Any) -> str:
    """La forme indentée des index relus à la main (`json.dump(…, indent=2)`)."""
    return json.dumps(document, ensure_ascii=False, indent=2)


def dumps_ligne(document: Any) -> str:
    """Forme compacte suivie d'un saut de ligne, celle des index européens."""
    return dumps_profil_json(document) + "\n"
