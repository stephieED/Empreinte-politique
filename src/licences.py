#!/usr/bin/env python3
"""
licences.py — Les licences des sources, et celle qu'un document publié DÉRIVE.

Source de vérité unique des libellés de licence côté pipeline (#530, lot 6 de
l'épic « une seule source AN » #523). Les mentions destinées au lecteur vivent
dans `AGENTS.md` §7, `web/UI_finale/src/data/sources.config.js` et
`web/UI_finale/src/pages/LegalNoticePage.jsx` ; les constantes ci-dessous en
sont la contrepartie machine, et elles doivent dire la même chose.

## Ce que le lot 6 change, et ce qu'il ne change pas

Depuis #528 (Sénat hors périmètre) et #529 (retrait du collecteur NosDéputés),
**plus une seule requête** ne part vers Regards Citoyens : tout ce que le
pipeline collecte encore côté français vient de `data.assemblee-nationale.fr`,
sous **Licence Ouverte / Open Licence (Etalab)** — attribution, pas de partage à
l'identique.

Ce n'est pas la même chose que « le corpus est sous Licence Ouverte », et c'est
le piège que ce module existe pour éviter :

- **ParlTrack reste sous ODbL v1.0**, avec sa clause de partage à l'identique,
  pour le versant européen. La source est vivante dans le pipeline
  (`normalize_parltrack_dumps`) ;
- **le corpus publié contient encore des champs dérivés de NosDéputés /
  NosSénateurs**, et la fusion additive les conserve. Mesuré sur les 476 profils
  de `pivot_data/profiles/` au commit `74c77c2` — c'est-à-dire APRÈS le premier
  run complet post-#529 : **475 profils** portent une entrée `sources[]` de type
  `nosdeputes` (474) ou `nossenateurs` (2), et **511 interventions publiées**
  sur 5 profils portent un `source_url` sur `www.nosdeputes.fr`. L'attribution
  ODbL leur reste **due** (AGENTS.md §2 règle 2).

`merge_profile._merge_pivot_sources` fusionne `sources[]` par `type` en gardant
la synchro la plus récente : une entrée `nosdeputes` déjà publiée n'est donc pas
remplacée par la collecte AN, elle **coexiste** avec elle. Une mention
d'attribution figée dans une constante se serait donc trompée dans les deux sens
à la fois : trop permissive sur les profils qui gardent du RC, trop restrictive
sur ceux qui n'en ont plus.

## D'où la règle : `meta.licence_donnees` est un champ DÉRIVÉ

Il se **recalcule** à partir de `sources[]` après chaque étape qui la modifie —
normalisation, greffe d'un mandat européen, enrichissement ParlTrack, fusion —
au lieu de se propager depuis le profil brut. C'est le patron de #493 pour
`chambres` : *un champ dérivé ne se fusionne pas, il se recalcule après la
fusion de ce dont il dérive.*

**Sa condition de retrait est écrite, et elle s'exécute toute seule** : le jour
où un profil ne portera plus ni source ni intervention Regards Citoyens, la
clause ODbL disparaîtra de SON `licence_donnees` sans qu'aucune décision
supplémentaire soit nécessaire. C'est le contraire d'un transitoire qui devient
permanent faute de critère écrit (AGENTS.md).

Ce qui n'est **pas** un signal de dérivation, et pourquoi :

- `mandats[].chambre == "Senat"` (2 mandats, `jean-luc-melenchon` et
  `bruno-retailleau`, #528 §3) : les deux profils portent déjà une entrée
  `sources[].type == "nossenateurs"`, le signal serait redondant ;
- `tags_thematiques[]`, dérivés de `interventions[].mots_cles` scrapés
  (#529 §3) : les 6 profils qui en portent portent aussi une source RC. Un
  troisième signal n'aurait rien ajouté qu'une chance de plus de diverger.

## Les trois décisions à lire avant de toucher ce module

Cinq le gouvernent (`docs/decisions-par-module.md`) ; ces trois-là suffisent à
ne pas se tromper :

- `docs/decisions/licence-lot-6-530.md` — pourquoi `meta.licence_donnees` est
  **dérivé** et non constant. C'est la fondation de tout ce fichier.
- `docs/decisions/licence-jamais-en-dur-909.md` — le corollaire, et son
  garde-fou : **aucun autre module** n'écrit ce champ à la main. Un constructeur
  de profil l'a fait pendant quatre lots en annonçant du CC0 pour de l'ODbL.
- `docs/decisions/retrait-marqueur-regards-citoyens-deputes-890.md` — quand un
  marqueur de source cesse d'être une traçabilité : la clause ODbL s'en va avec
  la donnée qui la justifiait, jamais avant.

Usage :
    from licences import LICENCE_AN, appliquer_licence_donnees
    appliquer_licence_donnees(profil_pivot)   # écrit meta.licence_donnees
"""

from typing import Any

#: Open data de l'Assemblée nationale — la **seule** source française collectée
#: depuis #529. Attribution obligatoire, PAS de partage à l'identique.
#: https://data.assemblee-nationale.fr/licence-ouverte-open-licence
LICENCE_AN = "Licence Ouverte / Open Licence (Etalab) — data.assemblee-nationale.fr"

#: #885 — le Sénat publie sous **Licence Ouverte** (`fr-lo` dans l'API
#: data.gouv), attribution seule, sans partage à l'identique. Elle est donc
#: **plus permissive que l'ODbL** de Regards Citoyens : un profil qui cesse de
#: porter du Regards Citoyens et gagne du Sénat sort de la clause share-alike,
#: il n'y entre pas.
LICENCE_SENAT = "Licence Ouverte / Open Licence (Sénat) — data.senat.fr"

#: NosDéputés.fr / NosSénateurs.fr (Regards Citoyens). **Plus collectée**
#: (#528, #529), mais toujours due aux champs déjà publiés qui en dérivent.
#: https://opendatacommons.org/licenses/odbl/1-0/
LICENCE_REGARDS_CITOYENS = (
    "ODbL v1.0 (NosDéputés.fr / NosSénateurs.fr — Regards Citoyens, "
    "à partir de l'Assemblée nationale / Sénat / JO)"
)

#: Portail Open Data du Parlement européen. Attribution.
LICENCE_EUROPARL = (
    "CC BY 4.0 (Parlement européen, Open Data Portal - data.europarl.europa.eu)"
)

#: Dumps JSON ParlTrack. **Le partage à l'identique reste ici**, et c'est la
#: raison pour laquelle « le corpus est sous Licence Ouverte » serait faux.
#: https://opendatacommons.org/licenses/odbl/1-0/
LICENCE_PARLTRACK = "ODbL v1.0 (ParlTrack — https://parltrack.org/dumps)"

#: Les licences qui portent une clause de partage à l'identique. Sert aux
#: consommateurs qui doivent savoir si un jeu de données dérivé est
#: republiable sous simple attribution (AGENTS.md §7).
LICENCES_SHARE_ALIKE = frozenset({LICENCE_REGARDS_CITOYENS, LICENCE_PARLTRACK})

#: `sources[].type` (valeurs de `schema_pivot.KNOWN_SOURCE_TYPES`) → licence.
#: Un type absent de cette table n'ajoute aucune clause : mieux vaut une
#: mention incomplète et visible qu'une licence inventée pour une source
#: qu'on n'a pas qualifiée.
LICENCE_PAR_TYPE_SOURCE: dict[str, str] = {
    "assemblee_nationale": LICENCE_AN,
    "senat": LICENCE_SENAT,
    "nosdeputes": LICENCE_REGARDS_CITOYENS,
    "nossenateurs": LICENCE_REGARDS_CITOYENS,
    "europarl": LICENCE_EUROPARL,
    "parltrack": LICENCE_PARLTRACK,
}

#: Ordre de composition. Stable et indépendant de l'ordre de `sources[]`, qui
#: dépend lui de l'ordre de collecte : deux profils au même contenu doivent
#: publier la même chaîne, sinon `audit_diff_profils` verrait bouger un
#: scalaire que rien n'a fait bouger.
ORDRE_LICENCES: tuple[str, ...] = (
    LICENCE_AN,
    LICENCE_SENAT,
    LICENCE_REGARDS_CITOYENS,
    LICENCE_EUROPARL,
    LICENCE_PARLTRACK,
)

#: Séparateur de composition. Repris tel quel de `normalize_parltrack_dumps`,
#: qui composait déjà « <licence existante> + <licence ParlTrack> » avant ce
#: lot : le format publié ne change pas, seule sa fabrique est unifiée.
SEPARATEUR = " + "

#: Fragments d'URL qui trahissent un champ dérivé de Regards Citoyens même
#: quand `sources[]` ne le dit plus. **Public depuis #839** : l'audit du
#: sédiment les relit, et les recopier ailleurs ferait de ce module un
#: référentiel parmi d'autres (`tests/test_retrait_nosdeputes_529.py` n'admet
#: la mention que dans les emplacements qu'il nomme).
MOTIFS_URL_REGARDS_CITOYENS = ("nosdeputes.fr", "nossenateurs.fr")

_MOTIFS_URL_REGARDS_CITOYENS = MOTIFS_URL_REGARDS_CITOYENS


def _porte_une_intervention_regards_citoyens(profil: dict[str, Any]) -> bool:
    """True si au moins une intervention publiée pointe vers Regards Citoyens.

    511 interventions sur 5 profils au commit `74c77c2`. `interventions[]` est
    fusionnée de façon **additive** (`merge_profile.merge_pivot_profile`) : ces
    prises de parole restent publiées, avec leur `source_url`, tant que le
    profil n'est pas régénéré à froid.
    """
    for intervention in profil.get("interventions") or []:
        if not isinstance(intervention, dict):
            continue
        url = intervention.get("source_url") or ""
        if isinstance(url, str) and any(m in url for m in _MOTIFS_URL_REGARDS_CITOYENS):
            return True
    return False


def licences_du_profil(profil: dict[str, Any]) -> list[str]:
    """Les licences réellement dues par ce profil, dans l'ordre de composition.

    Args:
        profil: profil au format pivot v1 (`schema_pivot`). Seules `sources[]`
                et `interventions[]` sont lues.

    Returns:
        Liste sans doublon, ordonnée par `ORDRE_LICENCES`. Vide si le profil
        ne porte aucune source qualifiée — un profil sans source n'a aucune
        licence à revendiquer, et `audit_pivot_dataset` le signalera comme
        `licence_donnees_manquante`, ce qui est l'information juste.
    """
    dues: set[str] = set()
    for source in profil.get("sources") or []:
        if not isinstance(source, dict):
            continue
        licence = LICENCE_PAR_TYPE_SOURCE.get(source.get("type"))
        if licence:
            dues.add(licence)
    if _porte_une_intervention_regards_citoyens(profil):
        dues.add(LICENCE_REGARDS_CITOYENS)
    return [licence for licence in ORDRE_LICENCES if licence in dues]


def composer_licence_donnees(profil: dict[str, Any]) -> str:
    """Le texte de `meta.licence_donnees` pour ce profil. Ne l'écrit pas."""
    return SEPARATEUR.join(licences_du_profil(profil))


def appliquer_licence_donnees(profil: dict[str, Any]) -> str:
    """Recalcule et écrit `profil["meta"]["licence_donnees"]`.

    À appeler après **toute** étape qui modifie `sources[]` ou
    `interventions[]`. Ne crée pas `meta` s'il manque : un document sans `meta`
    n'est pas un pivot valide, et le lui fabriquer ici masquerait le défaut au
    lieu de le laisser à `validate_profil()`.

    Returns:
        La valeur écrite (chaîne vide si le profil n'a pas de `meta`).
    """
    meta = profil.get("meta")
    if not isinstance(meta, dict):
        return ""
    licence = composer_licence_donnees(profil)
    meta["licence_donnees"] = licence
    return licence
