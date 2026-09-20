#!/usr/bin/env python3
"""
normalize_senat.py — Les appartenances sénatoriales au format pivot (#885).

Ce module traduit ce que `senat_mandats.composer_mandats` rend — du
**source-near**, calqué sur les tables du Sénat — en entrées de `mandats[]`
conformes à `schema_pivot`. Même place que `normalize_europarl` pour le
Parlement européen, et mêmes contraintes : vocabulaire fermé, champ dérivé
recomposé, absence publiée absente.

Deux champs, deux questions
----------------------------
`categorie` répond à « **comment le pivot range** cette appartenance », et ses
valeurs sont celles de `KNOWN_CATEGORIES`. `type_organe_source` répond à « **ce
que la source en dit** », et c'est lui qui porte ce que le rangement perd
(#863).

La distinction fait tout le travail sur les groupes sénatoriaux. Le Sénat en
classe quatre types — études, amitié, information, liaison — et le pivot n'a de
catégorie que pour les deux premiers. Les deux autres sont rangés `autre` **et
déclarent leur type réel** : « Chrétiens d'Orient » est un groupe de *liaison*,
et le publier sous `autre` sans le dire perdrait ce que la source établit.

Ce que ce module ne décide pas
-------------------------------
**Le nom de l'organe.** Il arrive déjà daté et découpé sur les renommages :
c'est le travail de `senat_mandats`, et le refaire ici produirait deux
référentiels du même fait. Une entrée dont le libellé n'est pas daté arrive avec
`libelle_date: False`, et ce module le transporte en `libelle_non_date` plutôt
que de le laisser tomber — un nom non daté publié comme daté serait une
affirmation que la source ne porte pas (§2 règle 2).

**La chambre.** `deriver_chambres()` en est la seule fabrique depuis #493 ; ce
module se contente de poser `chambre: "Senat"` sur les mandats électifs, qui est
le seul endroit où la source l'établit sans ambiguïté.

**La licence.** `appliquer_licence_donnees` la recompose depuis `sources[]`
après coup (#530). Le label lui-même vit dans `src/licences.py`, jamais en dur
ici.
"""

from __future__ import annotations

from typing import Any, Optional

from licences import LICENCE_SENAT
from population_profils import CANDIDAT_DECLARE

#: **Les populations dont les mandats sénatoriaux sont publiés.** Un seul
#: élément, et c'est une décision de périmètre mesurée, pas une timidité.
#:
#: `pivot_data/profiles/` porte deux populations (#630). Les **candidats
#: déclarés** ont une fiche que le site publie ; les **membres de roster** sont
#: collectés pour nourrir les agrégats de groupe, et `group_profile` ne lit
#: d'eux que `nom`, `mandats`, `votes`, `interventions`, `amendements`.
#:
#: Mesuré le 13/09/2026 sur les 36 profils appariés à un matricule sénatorial :
#:
#: | population | ce que le lot verserait | ce qu'ils publient déjà |
#: | --- | ---: | ---: |
#: | 2 candidats déclarés | **+120** | 94 |
#: | 34 membres de roster | **+1 674** | 1 575 |
#:
#: Le lot **doublerait** les mandats des membres de roster, et 890 des 1 674
#: entrées seraient des groupes d'amitié et d'études. Aucune vue ne les affiche :
#: elles n'iraient que dans `mandats_agreges`, un agrégat que **#853 conteste
#: déjà** — « il compte la carrière des membres, pas leur passage dans le
#: groupe ». Doubler le volume d'un champ dont on sait qu'il compte la mauvaise
#: chose n'est pas un gain.
#:
#: Rien n'est perdu pour autant : `senat_mandats.composer_mandats` compose les
#: 36 sans distinction, et c'est **l'écriture** qui se limite. Servir les rosters
#: un jour ne demandera pas de recoder, seulement d'élargir cette constante.
POPULATIONS_PUBLIEES: frozenset[str] = frozenset({CANDIDAT_DECLARE})


def est_dans_le_perimetre(provenance: Optional[str]) -> bool:
    """Les mandats sénatoriaux de cette population sont-ils publiés ?

    Une provenance **inconnue** est hors périmètre : publier sur un profil dont
    on ne sait pas ce qu'il est reviendrait à décider à sa place, et §2 règle 5
    refuse de lire une absence comme un constat.
    """
    return provenance in POPULATIONS_PUBLIEES


#: Le type de source, au sens de `schema_pivot.KNOWN_SOURCE_TYPES`.
TYPE_SOURCE = "senat"

#: `mandats[].categorie_source` : qui a classé l'appartenance. « senat » dit que
#: c'est le Sénat lui-même, par ses tables de types — jamais nous.
CATEGORIE_SOURCE = "senat"

#: L'URL du jeu, pour `sources[]`. Le point d'entrée documenté, pas le fichier :
#: `docs/sources/senat-opendata.md` porte le détail des ressources.
URL_SOURCE = "https://data.senat.fr/"

#: Famille composée → catégorie pivot. Les groupes sénatoriaux n'y sont pas :
#: leur catégorie dépend de leur type, et `_CATEGORIE_GROUPE_SENATORIAL` la donne.
_CATEGORIE_PAR_FAMILLE: dict[str, str] = {
    "mandat_parlementaire": "mandat_electif",
    "groupe_politique": "groupe_politique",
    "commission": "commission",
    "extra_parlementaire": "extra_parlementaire",
}

#: Type de groupe sénatorial → catégorie pivot. **INFO et LIAISON n'ont pas
#: d'équivalent**, et c'est assumé : les ranger sous `groupe_etudes` les
#: dirait études, ce qu'ils ne sont pas. Ils vont dans `autre`, et
#: `type_organe_source` porte ce que le rangement perd (#863).
_CATEGORIE_GROUPE_SENATORIAL: dict[str, str] = {
    "ETUDES": "groupe_etudes",
    "AMITIE": "groupe_amitie",
    "INFO": "autre",
    "LIAISON": "autre",
}

#: Ce que la source dit de l'organe, dans le vocabulaire fermé de
#: `schema_pivot.KNOWN_TYPES_ORGANE_SOURCE`.
_TYPE_ORGANE_SOURCE: dict[str, str] = {
    "mandat_parlementaire": "mandat_senatorial",
    "groupe_politique": "groupe_politique_senatorial",
    "commission": "commission_senatoriale",
    "extra_parlementaire": "organisme_extra_parlementaire_senat",
}

_TYPE_ORGANE_GROUPE_SENATORIAL: dict[str, str] = {
    "ETUDES": "groupe_etudes_senatorial",
    "AMITIE": "groupe_amitie_senatorial",
    "INFO": "groupe_information_senatorial",
    "LIAISON": "groupe_liaison_senatorial",
}


def _fonction_publiable(mandat: dict[str, Any]) -> Optional[str]:
    """La fonction tenue, ou `None`.

    Plusieurs fonctions peuvent recouvrir une même période — la source distingue
    « Membre » du rôle réel, et les deux cohabitent. On publie **la plus
    spécifique**, c'est-à-dire la première qui ne soit pas le générique
    « Membre » ; sinon « Membre », qui est un fait lui aussi.
    """
    fonctions = [f.get("libelle") for f in (mandat.get("fonctions") or []) if f.get("libelle")]
    if not fonctions:
        return None
    specifiques = [f for f in fonctions if f.strip().lower() not in ("membre", "membres")]
    return specifiques[0] if specifiques else fonctions[0]


def _libelle_appartenance(mandat: dict[str, Any]) -> Optional[str]:
    """Le libellé, enrichi du type d'appartenance quand il en change le sens.

    « Rattaché » et « apparenté » ne sont pas « membre » : un sénateur rattaché
    à un groupe n'en fait pas partie au même titre, et le Sénat le publie
    distinctement. Le perdre publierait une appartenance que l'intéressé n'avait
    pas (§2 règle 2). Le type reste **aussi** dans son champ propre — le libellé
    est ce qu'un lecteur voit, le champ est ce qu'une machine lit.
    """
    label = mandat.get("label")
    type_app = mandat.get("type_appartenance")
    if label and type_app and type_app.strip().lower() not in ("membre",):
        return f"{label} ({type_app.strip().lower()})"
    return label


def normalize_mandat(mandat: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Une appartenance composée → une entrée de `mandats[]`, ou `None`.

    Rend `None` pour une famille inconnue plutôt que de la ranger sous `autre` :
    une famille que ce module ne sait pas traduire est un défaut de ce module,
    et la publier silencieusement le masquerait.
    """
    famille = mandat.get("famille")
    if famille == "groupe_senatorial":
        type_code = mandat.get("type_groupe_code") or ""
        categorie = _CATEGORIE_GROUPE_SENATORIAL.get(type_code)
        type_organe = _TYPE_ORGANE_GROUPE_SENATORIAL.get(type_code)
        if categorie is None:
            # Un type que le Sénat ajouterait sans nous prévenir. `autre` le
            # range sans mentir, et l'absence de `type_organe_source` dit que
            # personne ne l'a classé — jamais un type inventé.
            categorie, type_organe = "autre", None
    elif famille in _CATEGORIE_PAR_FAMILLE:
        categorie = _CATEGORIE_PAR_FAMILLE[famille]
        type_organe = _TYPE_ORGANE_SOURCE.get(famille)
    else:
        return None

    entree: dict[str, Any] = {
        "label": _libelle_appartenance(mandat),
        "categorie": categorie,
        "categorie_source": CATEGORIE_SOURCE,
        "fonction": _fonction_publiable(mandat),
        "debut": mandat.get("debut"),
        "fin": mandat.get("fin"),
        # Une appartenance sans date de fin est en cours **si** elle a un début ;
        # sans aucune date, on ne sait pas, et `False` serait un constat (§2
        # règle 5). 1 064 appartenances sur 3 213 sont dans ce cas.
        "actif": bool(mandat.get("debut")) and not mandat.get("fin"),
        "source_url": mandat.get("source_url"),
    }
    if type_organe:
        entree["type_organe_source"] = type_organe
    if categorie == "mandat_electif":
        # #493 : la chambre n'est posée que là où la source l'établit sans
        # ambiguïté. Un groupe d'amitié ne dit pas dans quelle chambre on siège.
        entree["chambre"] = "Senat"
    if mandat.get("type_appartenance_code"):
        entree["type_appartenance_senat"] = mandat["type_appartenance_code"]
    for champ_source, champ_pivot in (("motif_debut", "motif_debut_senat"),
                                      ("motif_fin", "motif_fin_senat")):
        if mandat.get(champ_source):
            entree[champ_pivot] = mandat[champ_source]
    if mandat.get("libelle_date") is False:
        # Le nom existe, mais la source ne le borne pas : il vient de la table
        # des organes, pas de celle des libellés datés. Publier sans le dire
        # laisserait croire qu'il vaut pour la période affichée.
        entree["libelle_non_date"] = True
    if mandat.get("libelle_non_resolu"):
        entree["libelle_non_resolu"] = True
    return entree


def normalize_mandats(mandats: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Les appartenances traduites, dans l'ordre reçu, les inconnues écartées."""
    traduites = (normalize_mandat(m) for m in mandats)
    return [entree for entree in traduites if entree is not None]


def source_senat(synchro_le: Optional[str] = None) -> dict[str, Any]:
    """L'entrée `sources[]` du Sénat.

    La licence vient de `src/licences.py` et n'est **jamais** écrite en dur ici :
    §7 en fait un champ dérivé, et un label recopié dérive de son référentiel
    sans que rien ne le signale.
    """
    return {"type": TYPE_SOURCE, "url": URL_SOURCE, "synchro_le": synchro_le,
            "licence": LICENCE_SENAT}
