#!/usr/bin/env python3
"""
correspondance_acteurs_an.py — La correspondance slug ↔ acteur AN est un
artefact committé, pas une heuristique rejouée à chaque run (#525).

## Ce que la table résout

Les **slugs NosDéputés sont les identifiants de profil** du dépôt :
`pivot_data/profiles/<slug>.pivot.json`, et `id` du schéma pivot (#487).
AMO30 — le référentiel historique des acteurs de l'Assemblée nationale — ne
publie ni le slug ni aucun identifiant externe : il rend un `PA######` et de
l'état civil. Sortir de NosDéputés comme source de vérité (épic « une seule
source AN ») suppose donc une correspondance, et cette correspondance doit
être **relue et prouvée**, pas recalculée.

Le slug reste l'`id`. Un `acteur_ref` est une **correspondance**, jamais un
renommage : renommer un fichier publié est une suppression, et
`audit_diff_profils` la bloque (#460/#470).

## Pourquoi un fichier committé plutôt que la correspondance par nom

`candidate_profile._resolve_acteur_ref_par_slug` sait déjà rapprocher un slug
d'un acteur par son nom normalisé, et **refuse l'homonymie** plutôt que
d'attribuer au hasard. Mesuré sur les 476 profils publiés et les 3 119 acteurs
de l'archive AMO30 : **466 résolus, 10 non résolus**.

Les 10 restants ne sont pas un défaut d'algorithme, ce sont des faits d'état
civil que rien dans les données ne permet de deviner :

| Slug | Écart | `acteur_ref` |
| --- | --- | --- |
| `alexandra-martin` | homonymie réelle — l'AN désambiguïse par département : « Alexandra Martin (Alpes-Maritimes) » | `PA793342` |
| `alexandra-martin-1` | homonymie réelle — « Alexandra Martin (Gironde) » | `PA793944` |
| `christelle-d-intorni` | apostrophe — le slug la remplace par un tiret | `PA793322` |
| `christelle-petex-levet` | nom divergent — AN : « Christelle Petex » | `PA721442` |
| `claire-pitollat` | nom divergent — AN : « Claire Colomb-Pitollat » | `PA718910` |
| `emmanuel-tache-de-la-pagerie` | nom divergent — AN : « Emmanuel Taché » | `PA793382` |
| `guillaume-gouffier-cha` | changement de nom — AN : « Guillaume Gouffier Valente » | `PA721296` |
| `jordan-bardella` | **hors AN** : député européen, aucun acteur AMO30 | `null` |
| `loic-prud-homme` | apostrophe — « Loïc Prud'homme » | `PA719578` |
| `sabrina-agresti-roubache` | nom divergent — AN : « Sabrina Roubache » | `PA793278` |

Une heuristique qui rattraperait ces dix cas rattraperait aussi, sans le dire,
des rapprochements faux : « Alexandra Martin » a deux acteurs, et aucune règle
de normalisation ne dit lequel est le bon. La preuve est ce qui tranche, et
une preuve ne se recalcule pas — elle se relit.

## Un trou est déclaré, jamais absent

Un slug sans acteur AN (`jordan-bardella`, député européen) porte
`acteur_ref: null` **et** `ecart: "hors_an"` **et** un `motif`. Il n'est pas
absent de la table. Un trou muet est ce qui a produit #510 (Syceron publiait
l'id nu, l'index restait vide sans que rien n'échoue) et #501 : AGENTS.md §2
règle 5 — donnée manquante veut dire donnée manquante, jamais une valeur par
défaut, et ici jamais un slug reconstruit à la volée.

## Ce que la table ne fait pas

Elle ne remplace pas la correspondance par nom : elle passe **devant**. Un
slug absent de la table retombe sur `_build_acteur_nom_index`, qui garde son
refus d'homonymie. Supprimer ce recours rendrait impossible la collecte de
tout profil neuf — le roster grossit à chaque run, et un membre nouvellement
élu n'a par construction aucune entrée tant que personne n'a relu la sienne.
Ce qui échoue bruyamment, c'est le **contrôle de couverture** sur le corpus
**publié** (`slugs_non_couverts`, branché en échec dur dans
`check_quality_gate.py`) : un profil publié sans entrée nomme son slug et
bloque le commit.

## Deux régimes d'entrée, et ce n'est pas une tolérance (#715)

`origine` sépare ce que la table fait pour deux populations qui n'ont rien en
commun :

- **`relue`** — les 481 slugs hérités de NosDéputés. Le slug venait d'ailleurs,
  l'acteur AN était à *découvrir* dans AMO30, et la découverte se prouve. C'est
  tout ce qui précède.
- **`derivee`** — un membre de roster dont le slug a été **fabriqué depuis
  l'acteur** (`slugify(état civil AMO30)`, #708). Il n'y a aucun rapprochement
  à prouver : le slug ne pouvait pas désigner quelqu'un d'autre, il est sorti
  de cet acteur-là. L'entrée n'enregistre pas une preuve, elle **gèle**
  l'identifiant — c'est le seul service que la table rend encore à cette
  population, et il est réel : sans entrée, un changement de nom d'usage
  déplacerait le slug au run suivant (#487, #668).

Ce que ça n'assouplit pas : #525 §6 interdit de **combler** une entrée relue
depuis `identite.source_url`, et ce refus tient entier. Un slug publié qui
n'est pas déclaré fabriqué par le roster du run ne reçoit rien, et la §5b du
portail bloque toujours son commit.

Rationale complet et condition de retrait :
`docs/decisions/correspondance-acteurs-an-525.md`,
`docs/decisions/entree-derivee-correspondance-715.md`.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any, Iterable, Optional
import json
import re

from schema_pivot import KNOWN_IDENTIFIANTS, ORDRE_IDENTIFIANTS

#: Version de schéma du fichier. Un fichier d'une autre version est refusé
#: bruyamment plutôt que lu au mieux : la table est un artefact relu, pas un
#: cache.
SCHEMA_VERSION = "correspondance-acteurs-an-v2"

#: Référentiels dont la table porte l'identifiant (#539). Même nomenclature que
#: `schema_pivot.KNOWN_IDENTIFIANTS`, et **importée** de là : la table est ce qui
#: alimente le bloc `identifiants` du pivot, deux listes auraient divergé.
#:
#: `senat` est présent et vaudra `null` partout tant qu'aucun référentiel
#: sénatorial n'est établi (#528). C'est un trou **déclaré**, pas une colonne
#: oubliée : la même règle que l'`acteur_ref` de Bardella, appliquée à une
#: source entière.
IDENTIFIANTS_CONNUS = KNOWN_IDENTIFIANTS

#: Forme attendue de chaque identifiant, reprise du schéma pivot mot pour mot.
_FORMES = {
    "an": re.compile(r"^PA\d+$"),
    "senat": None,
    "europarl": re.compile(r"^\d+$"),
    "hatvp": re.compile(r"^https?://"),
}

#: Emplacement committé de la table. Fichier de configuration, au même titre
#: que `raw_data/groupes_reels.json` — jamais sous `raw_data/profiles/`.
CHEMIN_PAR_DEFAUT = Path("raw_data") / "correspondance_acteurs_an.json"

#: Natures d'écart admises entre le slug NosDéputés et l'état civil AMO30.
#: Fermé comme les `KNOWN_*` du schéma pivot : on étend le frozenset, on ne le
#: contourne pas.
ECARTS_CONNUS = frozenset({
    "apostrophe",        # le slug remplace l'apostrophe par un tiret
    "nom_divergent",     # nom d'usage, changement de nom, particule absente
    "homonymie",         # plusieurs acteurs AN portent ce nom
    "hors_an",           # la personne n'a jamais eu d'acteur AN
})

#: Comment l'entrée est arrivée dans la table. Fermé, comme `ECARTS_CONNUS`.
#:
#: - `relue` — le rapprochement entre un slug **préexistant** et un acteur AN a
#:   été arbitré : c'est le régime de #525, celui des 476 slugs hérités de
#:   NosDéputés, qu'il fallait *découvrir* dans AMO30.
#: - `derivee` — le slug a été **fabriqué depuis** l'acteur
#:   (`slugify(état civil AMO30)`, #708), donc il n'y a aucun rapprochement à
#:   prouver : l'entrée ne fait qu'enregistrer une dérivation déjà faite. Ce
#:   qu'elle apporte n'est pas une preuve, c'est le **gel** de l'identifiant —
#:   sans elle, un changement de nom d'usage déplacerait le slug au run suivant
#:   et publierait la même personne deux fois (#487, #668).
#: - `sourcee` — le rapprochement est porté par un **identifiant externe**
#:   (Wikidata `P4123`, #757), pas par un arbitrage humain et pas par une
#:   dérivation. Régime des candidats déclarés : leur slug vient de
#:   `slugify(nom)`, un nom saisi dans un fichier éditorial, donc l'entrée
#:   établit bien quelque chose — contrairement à `derivee` — mais ce quelque
#:   chose est **sourcé et daté**, pas relu. La `preuve` est l'URL de l'élément,
#:   et l'entrée n'est écrite que si le profil publié la corrobore.
ORIGINES_CORRESPONDANCE = frozenset({"relue", "derivee", "sourcee"})

#: Origine d'une entrée qui n'en déclare pas. Ce n'est pas un défaut choisi par
#: commodité : une entrée écrite **avant** ce lot ne peut venir que de la passe
#: relue de #525 — la porte de fabrication n'existait pas. La clé reste donc
#: facultative en lecture, et le constructeur l'écrit sur toutes les entrées
#: qu'il produit. Condition de retrait du défaut : le jour où plus aucune entrée
#: committée n'est dépourvue de la clé, l'exiger devient gratuit.
ORIGINE_PAR_DEFAUT = "relue"

_ACTEUR_REF = re.compile(r"^PA\d+$")
#: Même alphabet que `slugify()` : `[a-z0-9-]`, jamais un point en tête
#: (#518 — un `.generation_checkpoint` lu comme un slug a coûté un commit).
_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class CorrespondanceInvalide(ValueError):
    """Le fichier de correspondance est illisible ou viole un invariant.

    Jamais rattrapée en silence : une table dégradée attribuerait des votes au
    mauvais acteur, ce qui est pire que pas de table du tout.
    """


class CorrespondanceIntrouvable(LookupError):
    """Aucune entrée pour ce slug, en mode strict.

    Le message **nomme le slug** : c'est tout l'objet du lot 2 — une résolution
    non trouvée échoue bruyamment, elle n'invente pas un identifiant.
    """


# Mémoïsation par **chemin**, jamais par nom logique : les tests règlent leur
# propre fichier par cas, et un mémo global ferait fuiter la table d'un test
# dans le suivant (le piège qui a fait revenir #377, AGENTS.md §5).
_MEMO: dict[str, dict[str, Any]] = {}


def vider_memo() -> None:
    """Oublie les tables déjà chargées. Utile aux tests, sans effet ailleurs."""
    _MEMO.clear()


def _exiger(condition: bool, message: str) -> None:
    if not condition:
        raise CorrespondanceInvalide(message)


def _lire_identifiants(slug: str, entree: dict[str, Any]) -> dict[str, Optional[str]]:
    """Bloc `identifiants` complet d'une entrée, quelle que soit son écriture.

    La table est **multi-sources** depuis #539 : elle porte l'identifiant de
    chaque référentiel où la personne existe, et c'est elle qui alimente le bloc
    `identifiants` du profil pivot.

    Deux écritures sont lues, et c'est délibéré :

    - `identifiants: {"an": "PA1567", …}` — la forme v2 ;
    - `acteur_ref: "PA1567"` — la forme v1, **la même donnée sous son ancien
      nom**. Continuer à la lire n'est pas de la complaisance : une table est un
      artefact relu, et refuser de relire ce qu'on a écrit hier transformerait
      un renommage de clé en perte de correspondances vérifiées à la main
      (même arbitrage que `KNOWN_SOURCE_TYPES` dans `schema_pivot`).

    Les deux ensemble sont acceptées **si et seulement si** elles disent la même
    chose : deux valeurs divergentes seraient une table qui se contredit, et
    rien ne dirait laquelle croire.
    """
    identifiants = entree.get("identifiants")
    _exiger(
        identifiants is None or isinstance(identifiants, dict),
        f"{slug} : identifiants doit être un objet, reçu {type(identifiants).__name__}",
    )
    identifiants = dict(identifiants or {})

    inconnus = sorted(set(identifiants) - IDENTIFIANTS_CONNUS)
    _exiger(
        not inconnus,
        f"{slug} : référentiels inconnus dans identifiants {inconnus!r} "
        f"(connus : {sorted(IDENTIFIANTS_CONNUS)})",
    )

    if "acteur_ref" in entree:
        ancien = entree.get("acteur_ref")
        if "an" in identifiants:
            _exiger(
                identifiants["an"] == ancien,
                f"{slug} : identifiants.an ({identifiants['an']!r}) contredit "
                f"acteur_ref ({ancien!r}) — la même correspondance ne peut pas "
                "avoir deux valeurs.",
            )
        identifiants["an"] = ancien

    complet: dict[str, Optional[str]] = {}
    for cle in ORDRE_IDENTIFIANTS:
        valeur = identifiants.get(cle)
        _exiger(
            valeur is None or isinstance(valeur, str),
            f"{slug} : identifiants.{cle} doit être une chaîne ou null, "
            f"reçu {type(valeur).__name__}",
        )
        forme = _FORMES[cle]
        # Le message nomme l'ANCIENNE clé pour l'AN : `acteur_ref` est le nom
        # sous lequel la table s'écrit encore, et c'est ce nom-là qu'un
        # opérateur cherchera dans le fichier.
        nom_lisible = "identifiants.an (acteur_ref)" if cle == "an" else f"identifiants.{cle}"
        _exiger(
            valeur is None or forme is None or bool(forme.match(valeur)),
            f"{slug} : {nom_lisible} ne respecte pas la forme attendue "
            f"({forme.pattern if forme else ''}) : {valeur!r}",
        )
        complet[cle] = valeur
    return complet


def _valider_entree(slug: str, entree: Any) -> dict[str, Any]:
    """Valide une entrée et la renvoie normalisée (tous les champs présents).

    Chaque règle correspond à une manière connue de rendre la table
    trompeuse ; aucune n'est cosmétique.
    """
    _exiger(isinstance(entree, dict), f"entrée non-objet pour le slug {slug!r}")
    _exiger(bool(_SLUG.match(slug)), f"slug invalide : {slug!r}")

    identifiants = _lire_identifiants(slug, entree)
    acteur_ref = identifiants["an"]
    _exiger(
        acteur_ref is None or (isinstance(acteur_ref, str) and bool(_ACTEUR_REF.match(acteur_ref))),
        f"{slug} : l'identifiant AN doit valoir null ou 'PA<chiffres>', reçu {acteur_ref!r}",
    )

    ecart = entree.get("ecart")
    _exiger(
        ecart is None or ecart in ECARTS_CONNUS,
        f"{slug} : ecart inconnu {ecart!r} (attendus : {sorted(ECARTS_CONNUS)})",
    )

    # Un acteur absent est un fait déclaré, jamais un champ oublié — et
    # réciproquement, `hors_an` avec un acteur_ref serait une contradiction.
    _exiger(
        (acteur_ref is None) == (ecart == "hors_an"),
        f"{slug} : acteur_ref null et ecart 'hors_an' vont ensemble "
        f"(acteur_ref={acteur_ref!r}, ecart={ecart!r})",
    )

    motif = entree.get("motif")
    _exiger(
        ecart is None or (isinstance(motif, str) and motif.strip()),
        f"{slug} : un écart '{ecart}' exige un motif écrit",
    )

    origine = entree.get("origine", ORIGINE_PAR_DEFAUT)
    _exiger(
        origine in ORIGINES_CORRESPONDANCE,
        f"{slug} : origine inconnue {origine!r} "
        f"(attendues : {sorted(ORIGINES_CORRESPONDANCE)})",
    )
    # Un écart est le résultat d'un arbitrage : personne ne l'a écrit en
    # dérivant un slug depuis l'acteur qui le porte. Les deux ensemble
    # décriraient une entrée qui prétend n'avoir pas été relue tout en portant
    # le produit d'une relecture.
    _exiger(
        origine != "derivee" or ecart is None,
        f"{slug} : une entrée dérivée ne porte pas d'écart "
        f"(ecart={ecart!r}) — un écart s'arbitre, il ne se dérive pas",
    )

    preuve = entree.get("preuve")
    _exiger(
        isinstance(preuve, str) and preuve.startswith("http"),
        f"{slug} : preuve absente ou non-URL ({preuve!r}) — une entrée sans "
        "preuve n'est pas relisible",
    )

    verifie_le = entree.get("verifie_le")
    _exiger(isinstance(verifie_le, str), f"{slug} : verifie_le absent")
    try:
        date.fromisoformat(verifie_le)
    except ValueError as exc:
        raise CorrespondanceInvalide(f"{slug} : verifie_le invalide ({verifie_le!r})") from exc

    etat_civil = entree.get("etat_civil")
    _exiger(isinstance(etat_civil, dict), f"{slug} : etat_civil absent")

    return {
        # `acteur_ref` reste exposé, et vaut TOUJOURS `identifiants["an"]` : il
        # est l'ancien nom du même champ, et une centaine d'appels le lisent.
        # Le dériver ici, dans la seule fabrique d'entrée normalisée, garantit
        # que les deux ne peuvent pas diverger côté lecteur (#539).
        "acteur_ref": acteur_ref,
        "identifiants": identifiants,
        "etat_civil": etat_civil,
        "ecart": ecart,
        "motif": motif,
        "preuve": preuve,
        "verifie_le": verifie_le,
        "origine": origine,
    }


def charger_correspondance(chemin: Optional[Path] = None) -> dict[str, dict[str, Any]]:
    """Charge et valide la table ; renvoie `{slug: entrée}`.

    Mémoïsé par chemin absolu. Lève `CorrespondanceInvalide` sur un fichier
    absent, illisible, d'une autre version de schéma, ou violant un invariant.
    """
    chemin = Path(chemin) if chemin is not None else CHEMIN_PAR_DEFAUT
    cle = str(chemin.resolve())
    memoise = _MEMO.get(cle)
    if memoise is not None:
        return memoise

    try:
        with open(chemin, encoding="utf-8") as f:
            document = json.load(f)
    except FileNotFoundError as exc:
        raise CorrespondanceInvalide(
            f"Table de correspondance absente : {chemin}. Elle est committée "
            "(#525) ; un run qui ne la trouve pas lit un dépôt incomplet."
        ) from exc
    except json.JSONDecodeError as exc:
        raise CorrespondanceInvalide(f"Table de correspondance illisible ({chemin}) : {exc}") from exc

    _exiger(isinstance(document, dict), f"{chemin} : racine non-objet")
    version = document.get("schema_version")
    _exiger(
        version == SCHEMA_VERSION,
        f"{chemin} : schema_version {version!r}, attendu {SCHEMA_VERSION!r}",
    )
    brut = document.get("correspondances")
    _exiger(isinstance(brut, dict), f"{chemin} : clé 'correspondances' absente ou non-objet")

    table: dict[str, dict[str, Any]] = {}
    # Unicité par référentiel, pas seulement pour l'AN (#539) : deux slugs sur
    # un même identifiant, ce serait deux profils publiés pour une seule
    # personne — un doublon que rien d'autre ne relèverait. Mesuré à 0 sur les
    # 476 profils publiés, pour les quatre référentiels.
    # `hatvp` en est exclu : c'est une URI de déclaration, pas une clé
    # d'identité, et rien ne garantit qu'un couple ne partage pas une page.
    par_identifiant: dict[str, dict[str, str]] = {
        cle: {} for cle in ("an", "senat", "europarl")
    }
    for slug, entree in brut.items():
        valide = _valider_entree(slug, entree)
        for cle, deja_vus in par_identifiant.items():
            valeur = valide["identifiants"][cle]
            if valeur is None:
                continue
            _exiger(
                valeur not in deja_vus,
                f"l'identifiant {cle}={valeur} est attribué à deux slugs : "
                f"{deja_vus.get(valeur)} et {slug}",
            )
            deja_vus[valeur] = slug
        table[slug] = valide

    _MEMO[cle] = table
    return table


def resoudre_acteur_ref(
    slug: str,
    chemin: Optional[Path] = None,
    *,
    strict: bool = False,
) -> Optional[str]:
    """Résout un slug en `acteur_ref` AN depuis la table committée.

    - entrée présente avec un acteur → l'`acteur_ref` ;
    - entrée présente **déclarée hors AN** → `None`, sans exception : c'est un
      fait vérifié, pas une absence ;
    - slug absent de la table → `None`, ou `CorrespondanceIntrouvable`
      **nommant le slug** si `strict=True`.

    `strict=True` est le mode des chaînes qui n'ont pas le droit de deviner
    (un roster dérivé d'AMO30 doit savoir quel profil il alimente) ;
    `strict=False` laisse l'appelant enchaîner sur la correspondance par nom.
    """
    table = charger_correspondance(chemin)
    entree = table.get(slug)
    if entree is None:
        if strict:
            raise CorrespondanceIntrouvable(
                f"Aucune correspondance slug ↔ acteur AN pour {slug!r} dans "
                f"{chemin or CHEMIN_PAR_DEFAUT}. Ajoute l'entrée avec sa preuve "
                "(#525) — un acteur_ref n'est jamais reconstruit à la volée."
            )
        return None
    return entree["acteur_ref"]


def resoudre_identifiants(
    slug: str, chemin: Optional[Path] = None
) -> dict[str, Optional[str]]:
    """Bloc `identifiants` complet du slug (#539), toutes clés à `null` si absent.

    C'est ce que le pivot publie : le `PA` cesse d'être ré-résolu par
    correspondance de nom à chaque run, il est lu ici et écrit là-bas. Un slug
    absent de la table rend quatre `null` — « aucun identifiant connu », jamais
    une valeur reconstruite à la volée (AGENTS.md §2 règle 5).
    """
    entree = charger_correspondance(chemin).get(slug)
    if entree is None:
        return {cle: None for cle in ORDRE_IDENTIFIANTS}
    return dict(entree["identifiants"])


def est_declare_hors_an(slug: str, chemin: Optional[Path] = None) -> bool:
    """Vrai si le slug est **déclaré** sans acteur AN (et non simplement absent)."""
    entree = charger_correspondance(chemin).get(slug)
    return entree is not None and entree["ecart"] == "hors_an"


def slugs_non_couverts(slugs: Iterable[str], chemin: Optional[Path] = None) -> list[str]:
    """Slugs publiés qui n'ont aucune entrée dans la table, triés.

    Le contrôle de couverture du lot 2 : c'est lui que `check_quality_gate.py`
    transforme en échec dur, en nommant chaque slug.
    """
    table = charger_correspondance(chemin)
    return sorted({slug for slug in slugs if slug not in table})
