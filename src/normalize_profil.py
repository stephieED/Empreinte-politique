#!/usr/bin/env python3
"""
normalize_profil.py — Adaptateur profil brut FR → schéma pivot v1.

Convertit un profil JSON produit par `candidate_profile.py` vers le schéma
pivot commun défini dans `schema_pivot.py`. Pendant du `normalize_europarl.py`
pour la branche européenne.

## Il s'appelait `normalize_nosdeputes.py` (#529, lot 5)

Le nom datait du jour où le profil brut venait effectivement de NosDéputés.
Ce n'est plus vrai depuis longtemps, et plus du tout depuis #529 : l'identité,
les mandats, les votes, les amendements, les textes portés et les interventions
viennent tous de l'open data de l'Assemblée nationale. Ce module n'a jamais
connu la source, seulement la **forme** du profil brut — le renommer aligne son
nom sur ce qu'il fait, et sur ce que le diagramme d'AGENTS.md §3 décrit.

Ce qui a suivi le nom : `_SOURCE_TYPE_MAP` (chambre → `nosdeputes` /
`nossenateurs`) et l'URL NosDéputés qui servait de repli à `sources[].url`.
Ce qui ne l'a PAS suivi : la capacité à **relire** les profils déjà collectés,
qui portent encore `meta.synchro_sources.nosdeputes` — un adaptateur qui ne
saurait plus lire le corpus existant transformerait un renommage en perte de
données (AGENTS.md §2 règle 5).

Ce module est volontairement découplé de la collecte : il ne fait aucun
appel réseau et ne connaît pas le mécanisme de téléchargement.

## Les décisions à relire avant de toucher à une normalisation

La liste complète et à jour est dans `docs/decisions-par-module.md`. Ces
trois-là portent le contrat de ce module :

- `docs/decisions/collecte-vs-publie-545.md` — **ce que la normalisation a le
  droit de faire** : la table de relations collecté → publié, liste par liste
  (égalité, renommage `textes_portes` → `dossiers_legislatifs`, dérivation), et
  le garde-fou `audit_collecte_vs_publie` qui la tient. Toute relation nouvelle
  s'écrit là avant de s'écrire ici.
- `docs/decisions/cle-fusion-interventions-540.md` — pourquoi
  `_normalize_intervention` propage `intervention_id` **verbatim** depuis l'`id`
  du brut : sans identifiant, la fusion pivot repliait 7 767 interventions
  collectées sur 891 publiées, en silence.
- `docs/decisions/normalisation-amendements.md` — pourquoi
  `_normalize_amendement` ne recopie pas la liste des cosignataires par
  signataire, et pourquoi la clé d'un amendement est son `uid`, jamais son
  `numero`.

Usage :
    from normalize_profil import normalize_profil
    pivot = normalize_profil(raw_profile)

    # Enrichissement optionnel depuis candidats.json :
    pivot["parti"] = "La France Insoumise"
"""

import re
import time
from typing import Any, Optional

from schema_pivot import (
    CHAMBRE_COLLECTE_VERS_PIVOT,
    COLLECTE_THEME_SEUL,
    KNOWN_NATURES_TEXTE,
    ROLE_INITIATEUR_PAR_NATURE,
    SCHEMA_VERSION,
    appliquer_chambres,
    deriver_tags_thematiques,
    make_empty_profil,
    poser_identifiant,
)
from amendements_index import cle_amendement
from avertissements import (
    DESTINATAIRE_INTERNE,
    avertissement,
    deriver_avertissements,
)
from licences import appliquer_licence_donnees
from scrutins_index import ScrutinsIndex, cle_scrutin
from scrutins_legislature import legislature_du_calendrier

# Correspondance chambre (clé du profil brut) → valeur normalisée du pivot.
# Vit dans `schema_pivot` depuis #494 : `lire_chambres()` doit appliquer la même
# tolérance côté lecture, et deux tables auraient pu diverger sans que rien ne le
# dise. L'alias local garde les appels du module inchangés.
_CHAMBRE_MAP: dict[str, str] = CHAMBRE_COLLECTE_VERS_PIVOT

# Type de source du profil brut FR (`sources[].type`, valeur de
# `schema_pivot.KNOWN_SOURCE_TYPES`). Constante depuis #529, et non plus une
# table indexée par chambre : `_SOURCE_TYPE_MAP` faisait correspondre `deputes`
# → `nosdeputes` et `senateurs` → `nossenateurs`, deux plateformes dont plus
# aucune n'alimente la collecte. La chambre ne décide plus de la provenance,
# parce qu'il n'y a plus qu'une provenance.
#
# `nosdeputes` et `nossenateurs` restent des valeurs VALIDES du schéma : 476
# profils publiés en portent une, et les retirer de `KNOWN_SOURCE_TYPES` ferait
# refuser par `validate_profil()` le corpus qu'on vient de publier. Leur sort —
# comme celui des mentions d'attribution ODbL — est le lot 6, pas celui-ci.
_SOURCE_TYPE_PROFIL_FR = "assemblee_nationale"

# Repli d'URL de source quand le profil brut n'en porte pas. C'était
# `https://www.nosdeputes.fr/<slug>` — une URL de plateforme tierce inventée
# pour un profil dont aucune section ne venait d'elle. La racine de l'open data
# AN ne prétend pas identifier la personne : elle nomme le jeu de données, ce
# qui est exactement ce qu'on sait quand le slug n'a pas été résolu en acteur.
_URL_SOURCE_PAR_DEFAUT = "https://data.assemblee-nationale.fr/"

# Préfixe de warning publié dans `meta.warnings` (#492). Même convention que
# candidate_profile.WARNING_PREFIX_* : le texte avant le premier ':' est le
# *type* agrégé par audit_pivot_dataset.compute_agregation_warnings.
WARNING_PREFIX_CHAMBRE_MANDAT_NON_RESOLUE = "chambre de mandat électif non résolue"

# Préfixe de warning publié dans `meta.warnings` (#493) quand `chambres` n'est
# pas entièrement étayée par les mandats : une chambre y figure au seul titre de
# la collecte, ou un `mandat_electif` reste sans chambre. Cette liste-là est
# utilisable, pas vérifiée, et ce warning est exactement ce qui l'empêche d'être
# trompeuse. Son décompte agrégé par
# `audit_pivot_dataset.compute_agregation_warnings` est la mesure de la
# migration : il tombe à zéro quand `chambre` peut être retiré.
WARNING_PREFIX_CHAMBRES_NON_CORROBOREE = "chambres du profil non corroborée"


def _first(*values: Any) -> Any:
    """Retourne la première valeur non-None parmi les arguments."""
    for v in values:
        if v is not None:
            return v
    return None


#: Identifiant d'acteur AN tel qu'il apparaît dans une URL de fiche
#: (`.../deputes/fiche/OMC_PA1567`). Même motif que
#: `candidate_profile._extract_acteur_ref`, recopié ici plutôt qu'importé :
#: `normalize_profil` est volontairement découplé de la collecte et n'a aucune
#: raison d'en tirer 4 900 lignes et ses dépendances réseau.
_ACTEUR_REF_DANS_URL = re.compile(r"PA\d+")


def _acteur_ref_de_l_url(url_an_ou_senat: Optional[str]) -> Optional[str]:
    """`PA######` lu dans une URL de fiche AN, `None` si elle n'en porte pas."""
    if not url_an_ou_senat:
        return None
    trouve = _ACTEUR_REF_DANS_URL.search(url_an_ou_senat)
    return trouve.group(0) if trouve else None


def _uri_hatvp_publiable(valeur: Any) -> Optional[str]:
    """URI HATVP réelle, ou `None` — et surtout jamais le marqueur XML d'AMO30.

    **Mesure de #539 sur les 476 profils publiés** : seuls **279** portent une
    vraie URI dans `identite.uri_hatvp`. **186** portent
    `{"@xmlns:xsi": "...", "@xsi:nil": "true"}` — le « pas de déclaration »
    d'AMO30, recopié tel quel depuis le XML converti au lieu d'être lu comme un
    `null` ; **11** sont vides. La mesure de 465 qui circulait comptait les 186
    comme renseignés.

    `identite.uri_hatvp` n'est PAS corrigé ici, et ce n'est pas un oubli : le
    défaut est dans l'**extraction** d'identité, en amont, et réparer dans la
    normalisation laisserait `raw_data/profiles` porter une valeur qui n'a jamais
    existé chez la source. Ce qui est corrigé ici, c'est ce qui est **publié** :
    un identifiant qui ne mène nulle part ne vaut pas mieux qu'une absence, il
    vaut moins (AGENTS.md §2 règles 2 et 5).

    **#556 a fermé l'amont** (`candidate_profile._champ_identite_an`), et la
    re-mesure du 29/08/2026 sur 481 profils dit 285 vraies URI, **191**
    marqueurs, 0 vides et 5 profils sans bloc `identite`. Elle a aussi trouvé
    deux autres champs au marqueur — `profession` (20) et `lieu_naissance` (28,
    en chaîne interpolée) —, ce qui a fait passer le correctif d'un champ à la
    règle de lecture. Cette fonction reste en place : elle protège le champ
    publié tant qu'un profil non régénéré porte encore l'ancienne valeur.
    """
    if isinstance(valeur, str) and valeur.startswith(("http://", "https://")):
        return valeur
    return None


#: Code de catégorie socioprofessionnelle en tête d'une profession AMO30 :
#: `"(33) - Cadre de la fonction publique"` (#641). Recopié depuis
#: `candidate_profile._PREFIXE_CODE_CSP_AN` plutôt qu'importé, comme
#: `_ACTEUR_REF_DANS_URL` : `normalize_profil` est volontairement découplé de la
#: collecte et n'a aucune raison d'en tirer 5 000 lignes et ses dépendances
#: réseau.
_PREFIXE_CODE_CSP_AN = re.compile(r"^\(\s*(\d+)\s*\)\s*-\s*")
_MARQUEUR_ABSENCE_PROFESSION = "sans activité professionnelle"


def _profession_publiable(valeur: Any) -> Optional[str]:
    """Profession réelle, ou `None` — jamais un code de nomenclature, jamais
    l'énoncé d'une absence de profession (#641).

    **Mesure du 31/08/2026 sur les 481 profils publiés** : 8 des 457 qui
    renseignent `identite.profession` publient un code brut. Trois portent
    `"(33) - Cadre de la fonction publique"` — le préfixe est du bruit, le
    libellé est bon. Cinq portent `"(85) - Personne diverse sans activité
    professionnelle de moins de 60 ans…"` : la valeur restante **n'est pas une
    profession**, c'est l'énoncé d'une absence, publié comme une profession sur
    une page consultable. Même idiome que #556, et il passe le seul contrôle
    existant — « chaîne non vide ».

    ## Pourquoi cette fonction existe EN PLUS de `candidate_profile._profession_an`

    Ce n'est pas une ceinture-bretelles, c'est la seule des deux qui répare les
    cinq profils déjà collectés. `merge_profile` prend la nouvelle valeur d'un
    scalaire **seulement si elle est renseignée, et ne régresse jamais vers
    `null`** (`docs/decisions/collecte-vide-necrase-jamais.md`) : une collecte
    corrigée qui rend `None` laisserait donc le libellé de la source en place,
    indéfiniment. Les trois profils au préfixe seul se réparent, eux, par la
    collecte — la nouvelle valeur est renseignée, elle gagne.

    C'est exactement l'argument de `_uri_hatvp_publiable` (#539) : ce qui est
    corrigé ici, c'est ce qui est **publié**.

    Le critère de l'absence est en deux parties, et les deux sont nécessaires :
    la **famille du code** (8x, « personnes sans activité professionnelle » dans
    la nomenclature) et le **libellé de la source elle-même**. La famille seule
    nullerait `"(84) - Elève, étudiant"`, qui nomme une situation et non une
    absence ; le libellé seul s'appuierait sur des mots là où la nomenclature
    offre une structure.
    """
    if not isinstance(valeur, str) or not valeur.strip():
        return None
    texte = valeur.strip()
    trouve = _PREFIXE_CODE_CSP_AN.match(texte)
    if trouve is None:
        return texte
    libelle = texte[trouve.end():].strip()
    if not libelle:
        return None
    if trouve.group(1).startswith("8") and _MARQUEUR_ABSENCE_PROFESSION in libelle.lower():
        return None
    return libelle


# ---------------------------------------------------------------------------
# Normaliseurs de sections individuelles
# ---------------------------------------------------------------------------

def _normalize_vote(
    v: dict[str, Any], scrutins_index: Optional[ScrutinsIndex] = None
) -> dict[str, Any]:
    """Normalise un vote brut vers le **mapping** pivot (#432).

    Un scrutin est identique pour tous ses votants : son méta (`texte`, `date`,
    `sort`…) vit une seule fois dans `pivot_data/scrutins.json`, et le profil ne
    garde que ce qui est propre au membre. Mesuré : 179,8 → 18,0 Mo de mapping
    plus 8,7 Mo de liste partagée, soit −85 %.

    `groupe_au_moment_du_vote` n'est écrit que s'il est renseigné. Son absence
    signifie « non renseigné », exactement comme `null` — exception documentée
    à la convention « missing = null » d'AGENTS.md §4, et elle seule : le champ
    n'est aujourd'hui jamais peuplé (0 sur 398 085) et l'écrire quand même
    coûtait **12,1 Mo de `null`, soit 40 % du mapping**.

    Résolution de l'identifiant, dans cet ordre :

    1. **l'index** — il porte la résolution de corpus (jointure sur un jumeau
       étiqueté, `scrutins_legislature`), la seule qui voie au-delà du profil ;
    2. **la législature du vote lui-même**, quand il la porte ;
    3. **le calendrier des législatures**, dérivation locale et déterministe.

    Si rien ne résout, le vote n'est **ni supprimé ni doté d'une clé inventée** :
    il conserve son enregistrement complet sous `scrutin_non_resolu`, avec
    `scrutin_id` à `null`. Une donnée qu'on ne sait pas normaliser reste une
    donnée (AGENTS.md §2.5) — et elle est visible plutôt que muette.
    """
    numero = str(v["numero_scrutin"]) if v.get("numero_scrutin") is not None else None
    legislature = str(v["legislature"]) if v.get("legislature") is not None else None

    scrutin_id = scrutins_index.identifiant_de_vote(v) if scrutins_index is not None else None
    if scrutin_id is None and numero is not None:
        legislature_resolue = legislature or legislature_du_calendrier(v.get("date"))
        if legislature_resolue:
            scrutin_id = cle_scrutin(legislature_resolue, numero)

    vote: dict[str, Any] = {
        "scrutin_id": scrutin_id,
        "position": v.get("position") or None,
    }
    if v.get("groupe_au_moment_du_vote"):
        vote["groupe_au_moment_du_vote"] = v["groupe_au_moment_du_vote"]

    if scrutin_id is None:
        vote["scrutin_non_resolu"] = {
            "numero_scrutin": numero,
            "legislature": legislature,
            "date": v.get("date"),
            "texte": v.get("texte") or v.get("titre") or None,
            "sort": v.get("sort"),
            "type_scrutin": v.get("type_scrutin"),
            # Aucun défaut : l'enregistrement non résolu est le vote tel que la
            # source l'a dit (#639). « vote_texte » y aurait affirmé un type que
            # rien ne source, sur le seul vote que le pipeline n'a pas su
            # rattacher.
            "type_vote": v.get("type_vote"),
            "texte_lie_id": v.get("texte_lie_id"),
            "source_url": v.get("source_url") or v.get("url_source"),
        }
    return vote


def _normalize_mandat(m: dict[str, Any]) -> dict[str, Any]:
    """Normalise un mandat/responsabilité brut vers le format pivot.

    `chambre` (#492) n'est portée que par les `mandat_electif`, et **lue sur le
    mandat lui-même**, jamais sur `raw_profile["chambre"]`. La distinction n'est
    pas cosmétique : la fusion additive accumule dans un même profil des mandats
    collectés lors de runs différents, donc potentiellement sous des chambres
    différentes. Mesuré sur `f5a828b` : `jean-luc-melenchon` est un profil brut
    `chambre: "senateurs"` qui porte trois `mandat_electif`, dont deux
    manifestement AN (2017-2022, groupe LFI). Reprendre la chambre du profil
    aurait donc estampillé « Sénat » deux mandats de l'Assemblée — un fait faux
    de plus, exactement ce que l'épic #486 reproche au champ de niveau profil.
    Un mandat non estampillé (collecté avant #492) reste à `null` : la chambre
    d'un mandat déjà collecté n'est pas reconstituable a posteriori, et une
    valeur par défaut est interdite (AGENTS.md §2.5).
    """
    mandat = {
        "label": m.get("label") or None,
        "categorie": m.get("categorie") or None,
        # Dans le format brut, la fonction s'appelle "type" (héritage de l'API)
        "fonction": m.get("type") or "membre",
        "debut": m.get("debut"),
        "fin": m.get("fin"),
        "actif": bool(m.get("actif")),
        "source_url": m.get("source_url"),
        "position_dans_hemicycle": m.get("position_dans_hemicycle"),
        "mode_declenchement": m.get("mode_declenchement"),
        "suspendu_pour_fonction_gouvernementale": m.get("suspendu_pour_fonction_gouvernementale"),
    }
    if mandat["categorie"] == "mandat_electif":
        chambre_brute = m.get("chambre")
        mandat["chambre"] = _CHAMBRE_MAP.get(chambre_brute) if chambre_brute else None
    # #718 — `categorie_source` est une clé FACULTATIVE, et son absence est un
    # sens : « personne n'a établi cette catégorie ». La publier à `null` sur
    # les entrées héritées dirait la même chose sous la forme d'un constat, ce
    # que §2 règle 5 refuse — même arbitrage que `interventions[].collecte`
    # (#657), dont l'absence est aussi la forme pleine.
    source_categorie = m.get("categorie_source")
    if source_categorie:
        mandat["categorie_source"] = source_categorie
    return mandat


def _role_texte_porte(role_brut: Any, nature: Optional[str]) -> Optional[str]:
    """Dérive le rôle publié d'un texte porté à partir du rôle brut et de la
    nature du texte déposé (#689).

    **Le rôle publié est dérivé, jamais collecté.** Même patron que `chambres`
    (#493) et `meta.licence_donnees` (#530) : un champ dérivé se recalcule à
    chaque normalisation, il ne traverse pas la fusion. C'est aussi ce qui rend
    la reprise possible sans réécrire les profils à la main — la qualification
    arrive par le brut, la dérivation la publie.

    Ne touche QUE le rôle d'initiateur, celui que la source appelle
    `initiateur.acteurs.acteur[]` et que la collecte écrivait `"auteur"` sans
    distinction. `rapporteur` / `co-rapporteur` traversent inchangés : rapporter
    un projet de loi est une fonction parlementaire ordinaire, ce n'est pas
    porter le texte au nom du Gouvernement.

    Une nature absente laisse `"auteur"`, et c'est délibéré à deux titres. C'est
    le fait constaté pour les 5 entrées d'initiateur publiées dont la source
    n'établit pas la nature (missions d'information, commissions d'enquête,
    déclaration du Gouvernement) : ce qu'on ne sait pas ne s'écrit pas autrement
    (AGENTS.md §2 règle 5). Et c'est la seule valeur juste pour les entrées
    collectées avant #689, dont le brut ne porte pas encore `nature_texte` :
    inventer ici une qualification qu'aucune archive n'a rendue les ferait
    toutes basculer d'un coup sur une passe `--pivot-only`, sans qu'un seul
    octet de source ait été relu.
    """
    if role_brut != "auteur":
        return role_brut
    return ROLE_INITIATEUR_PAR_NATURE.get(nature, "auteur")


def _normalize_texte_porte(d: dict[str, Any]) -> dict[str, Any]:
    """Normalise un dossier législatif brut vers le format pivot `textes_portes`.

    Le rôle reste nul quand la source ne le fournit pas : aucune inférence
    n'est faite à partir du volume d'interventions. Il l'était systématiquement
    du temps où la liste venait de NosDéputés, qui ne distinguait pas auteur et
    rapporteur ; `fetch_textes_portes_officiels` (#400, seule source depuis
    #528) le renseigne, mais les entrées collectées avant lui traversent la
    fusion additive avec leur `role: null` — c'est ce que ce repli couvre.

    `nature_texte` (#689) est le fait sourcé — préfixe de l'uid du document
    déposé (`PRJL`/`PION`/`PNRE`), écrit au brut par
    `candidate_profile._build_acteur_textes_portes_index` — et `role` en dérive
    pour un initiateur (voir `_role_texte_porte`). Une entrée brute d'avant #689
    ne porte pas la clé : elle sort avec `nature_texte: null` et son `role`
    inchangé, jusqu'à ce qu'un run réel la requalifie via
    `merge_profile.backfill_dossier_nature`.

    `dossier_id` (#639) est l'identifiant du dossier législatif à l'Assemblée
    nationale, forme `DLR5L15N37607`. Il n'est **pas reconstruit** : le profil
    brut le porte déjà sous `dossiers_legislatifs[].id`, écrit par
    `candidate_profile._build_acteur_textes_portes_index` depuis le `uid` du
    dossier, et la normalisation le jetait — 472 / 472 entrées publiées, 464
    dossiers distincts, 22 profils (mesuré le 31/08/2026). C'est le seul
    identifiant sourcé qui rattache un texte porté à autre chose qu'un libellé
    en clair, et il porte **le même nom** que sur les fiches de gouvernement
    (`textes[].dossier_id`, 63 / 63 sur LECORNU_II) : les deux étages parlent
    la même langue, sinon le croisement retomberait sur le titre.
    """
    nature = d.get("nature_texte")
    if nature not in KNOWN_NATURES_TEXTE:
        nature = None
    return {
        "titre": d.get("titre") or None,
        "dossier_id": d.get("id") or None,
        "role": _role_texte_porte(d.get("role"), nature),
        "nature_texte": nature,
        "type_rapport": d.get("type_rapport"),
        "stade_procedural": d.get("stade_procedural"),
        # #743 — l'ISSUE du dossier, à côté de sa PROGRESSION et jamais à sa
        # place. Un sort absent s'accompagne toujours de son motif : les deux
        # traversent ensemble, sinon le pivot publierait une absence sans cause.
        "sort": d.get("sort"),
        "sort_non_resolu": d.get("sort_non_resolu"),
        "date_min": d.get("date_min"),
        "date_max": d.get("date_max"),
        "legislature": d.get("legislature"),
        # `source_url` D'ABORD (#639) : c'est la clé qu'écrit la collecte AN
        # depuis #400, et la seule que porte le corpus — 468 des 472 entrées
        # brutes committées, 0 pour `url_source`/`url_institution`. Ne lire que
        # ces deux-là publiait donc `source_url: null` sur 472 / 472 textes
        # portés, c'est-à-dire un fait publié sans sa source primaire
        # (AGENTS.md §2 règle 2). Les deux clés héritées de NosDéputés restent
        # lues : elles vivent encore dans des entrées collectées avant #529.
        "source_url": _first(
            d.get("source_url"), d.get("url_source"), d.get("url_institution")
        ),
    }


def _normalize_intervention(i: dict[str, Any]) -> dict[str, Any]:
    """Normalise une intervention brute vers le format pivot.

    `intervention_id` propage **verbatim** l'`id` du profil brut (#540). C'est
    le seul discriminant d'une intervention, et jusqu'à #540 la normalisation
    l'abandonnait : l'entrée pivot n'avait plus que sa `source_url`, que la
    fusion additive traitait comme un identifiant. Pour une intervention
    Syceron, cette `source_url` est l'URL de **l'archive de la législature** —
    la même pour toutes : 3 351 entrées collectées pour gabriel-attal se
    réduisaient à 17 publiées. Voir `merge_profile._pivot_intervention_key`.

    **Deux formes en sortie depuis #657.** Une entrée brute portant
    `collecte == "theme_seul"` a été collectée sans son verbatim : elle rend une
    entrée pivot réduite, qui porte le même marqueur. Toute autre entrée rend la
    forme complète, inchangée. Ce qui distingue les deux n'est pas le contenu
    d'un champ mais la PRÉSENCE d'une déclaration : une entrée complète dont le
    `texte` est vide reste un constat sur la source.

    L'identifiant est repris tel quel, jamais reconstruit : `syceron_<uid du
    compte rendu>_<rang du paragraphe>` côté débats AN
    (`candidate_profile._parse_syceron_intervention_entry`), `question_<uid>`
    côté questions officielles, l'entier NosDéputés pour les interventions
    héritées d'avant #529. Il reste `None` si le brut n'en porte pas — une
    donnée absente reste absente (AGENTS.md §2), et la clé de fusion sait
    retomber sur la `source_url` puis sur le contenu.
    """
    # #657 — ENTRÉE RÉDUITE AU THÈME. Le brut porte `collecte: "theme_seul"`,
    # écrit par la collecte, seul étage qui sache ce que le run a demandé : la
    # passe pivot de la CI est un `--pivot-only` sans drapeau.
    #
    # Les champs absents ne sont PAS publiés à `null` : ils sont absents, et
    # `collecte` dit pourquoi. Un `"texte": null` se lirait « cette prise de
    # parole n'a pas de verbatim » — un fait sur la personne — là où le fait
    # porte sur le run (AGENTS.md §2 règle 5). Aucun consommateur n'indexe ces
    # clés en dur ; `validate_profil` n'en exige aucune.
    if i.get("collecte") == COLLECTE_THEME_SEUL:
        return {
            "intervention_id": i.get("id") if i.get("id") not in (None, "") else None,
            "date": _first(i.get("date"), i.get("created_at")),
            "type_detail": i.get("type_detail"),
            "theme_officiel": (
                i.get("sujet") if i.get("seance_ref") or i.get("session_ref") else None
            ),
            "source_url": _first(i.get("url_detail"), i.get("url")),
            # `source.url` reste `null` : la répéter ici doublerait 112 octets
            # par entrée pour la même URL d'archive. `source_id` aussi — l'uid
            # du compte rendu est le préfixe d'`intervention_id`.
            "source": {
                "type": "syceron",
                "url": None,
                "source_id": None,
                "legislature": i.get("legislature"),
            },
            "collecte": COLLECTE_THEME_SEUL,
        }

    result: dict[str, Any] = {
        "intervention_id": i.get("id") if i.get("id") not in (None, "") else None,
        "date": _first(i.get("date"), i.get("created_at")),
        "type_detail": i.get("type_detail"),
        "sujet": i.get("sujet"),
        "texte": i.get("texte"),
        "fonction": i.get("fonction"),
        "format": i.get("format"),
        "mots_cles": list(i.get("mots_cles") or []),
        "source_url": _first(i.get("url_detail"), i.get("url")),
        # Champs pivot officiels — renseignés depuis les données Syceron (débats AN)
        # quand disponibles, null sinon (interventions NosDéputés scraping).
        # La présence de seance_ref ou session_ref identifie une intervention Syceron.
        "theme_officiel": i.get("sujet") if i.get("seance_ref") or i.get("session_ref") else None,
        "seance": (
            {
                "ref": i.get("seance_ref"),
                "session_ref": i.get("session_ref"),
            }
            if i.get("seance_ref")
            else None
        ),
        "dossier": (
            {"point_ordre_du_jour": i.get("point_ordre_du_jour")}
            if i.get("point_ordre_du_jour")
            else None
        ),
        "source": (
            {
                "type": "syceron",
                "url": i.get("source_url") or i.get("url"),
                "source_id": i.get("source_id"),
                "legislature": i.get("legislature"),
            }
            if i.get("seance_ref") or i.get("session_ref")
            else None
        ),
    }
    # Champs supplémentaires pour les questions parlementaires officielles (type_detail == "question").
    if i.get("type_detail") == "question":
        result["sous_type"] = i.get("sous_type")      # "QE" | "QG" | "QOSD"
        result["ministere"] = i.get("ministere")       # ministère interrogé
        result["reponse"] = i.get("reponse")           # texte de la réponse (si disponible)
        result["date_reponse"] = i.get("date_reponse") # date JO de la réponse
    return result


def _normalize_amendement(a: dict[str, Any], own_id: str) -> dict[str, Any]:
    """Normalise un amendement brut vers le **mapping** pivot (#431).

    Un amendement est identique pour tous ses signataires : `texte_vise`,
    `sort`, `date`, `type_deposant`, `premier_signataire` et surtout
    `co_signataires` vivent une seule fois dans `pivot_data/amendements/`, et le
    profil ne garde que ce qui est propre au membre — son `role_signataire`.

    Mesuré sur les 209 profils committés : 810 552 paires (membre, amendement)
    pour 207 238 amendements distincts, et **77,7 M entrées de cosignatures pour
    4,96 M distinctes** (× 15,7). C'est cette recopie qui pèse 1 083,9 Mo.

    Un amendement sans `uid` n'a pas de clé — le `numero` repart à chaque texte
    ([[amendements-cle-uid]]) — et on ne lui en invente pas : il conserve son
    enregistrement complet sous `amendement_non_resolu`, avec `amendement_id` à
    `null`. Ni supprimé, ni deviné (AGENTS.md §2.5). Zéro cas sur les données
    actuelles, dont la couverture `uid` est de 100 %.
    """
    role_signataire = a.get("role_signataire")
    amendement_id = cle_amendement(a.get("uid"))

    amendement: dict[str, Any] = {
        "amendement_id": amendement_id,
        "role_signataire": role_signataire,
    }

    if amendement_id is None:
        premier_signataire = a.get("premier_signataire")
        # Compatibilité ascendante : pour les données historiques sans rôle
        # explicite, on conserve le comportement ancien (premier_signataire =
        # élu du profil). Ne vaut que pour l'enregistrement non résolu : la
        # liste partagée, elle, ne peut porter qu'une valeur indépendante du
        # lecteur (voir amendements_index._valeur_amendement).
        if role_signataire != "cosignataire":
            premier_signataire = own_id
        amendement["amendement_non_resolu"] = {
            "texte_vise": a.get("texte_vise"),
            "sort": a.get("sort"),
            "base_juridique_irrecevabilite": a.get("base_juridique_irrecevabilite"),
            "premier_signataire": premier_signataire,
            "co_signataires": list(a.get("co_signataires") or []),
            "type_deposant": a.get("type_deposant"),
            "date": a.get("date"),
            "numero": a.get("numero"),
            "source_url": a.get("source_url"),
        }
    return amendement


# ---------------------------------------------------------------------------
# Fonction principale
# ---------------------------------------------------------------------------

def normalize_profil(
    raw_profile: dict[str, Any],
    parti: Optional[str] = None,
    provenance: str = "candidat_declare",
    scrutins_index: Optional[ScrutinsIndex] = None,
    acteur_ref: Optional[str] = None,
) -> dict[str, Any]:
    """Convertit un profil brut FR vers le schéma pivot v1.

    Args:
        raw_profile: dict produit par candidate_profile.build_profile().
        parti: parti politique de l'élu (optionnel ; peut être passé depuis
               candidats.json car aucune source institutionnelle ne le publie).
        scrutins_index: index partagé des scrutins (#432). Porte la résolution
               de corpus de la législature — la seule qui voie au-delà du
               profil courant. Facultatif : sans lui, chaque vote se résout sur
               sa propre législature puis sur le calendrier, ce qui suffit pour
               un profil isolé mais ne peut pas exploiter un jumeau étiqueté
               vivant dans un autre fichier.
        provenance: "candidat_declare" (défaut) ou "roster_groupe" — voir
                    schema_pivot.KNOWN_PROVENANCES. Propagé tel quel vers
                    meta.provenance du profil pivot.
        acteur_ref: identifiant d'acteur AN (`PA######`) issu de la table
               committée `raw_data/correspondance_acteurs_an.json` (#525, #539).
               Publié tel quel dans `identifiants.an`. Absent, il est relu dans
               l'URL de fiche AN du profil brut — même fait, même source. C'est
               ce qui fait que le `PA` cesse d'être ré-résolu par correspondance
               de nom à chaque run : il est publié.

    Returns:
        Profil pivot dict conforme au schéma v1.
    """
    slug = raw_profile.get("slug") or ""
    chambre_raw = raw_profile.get("chambre") or ""
    # `chambre_collecte` (#493) : la chambre dont le jeu de données a répondu.
    # Elle n'est plus publiée telle quelle — elle devient le **repli** de
    # `deriver_chambres()`, qui l'ajoute toujours à `chambres` sans jamais la
    # substituer à ce que disent les mandats ni la laisser les évincer.
    # `_CHAMBRE_MAP.get(x, x or None)` laisse passer une chambre brute non mappée
    # telle quelle : elle est écartée par `deriver_chambres`, qui n'accepte comme
    # repli qu'une valeur de KNOWN_CHAMBRES.
    chambre_collecte = _CHAMBRE_MAP.get(chambre_raw, chambre_raw or None)
    source_type = _SOURCE_TYPE_PROFIL_FR

    identite = raw_profile.get("identite") or {}
    nom = identite.get("nom_complet") or slug.replace("-", " ").title()

    # Timestamp de synchro depuis le méta du profil brut (ou maintenant si absent).
    #
    # Trois clés lues dans cet ordre, et l'ordre est le sujet (#529) :
    # `assemblee_nationale` (ce que la collecte écrit aujourd'hui), puis
    # `nosdeputes` (ce que portent les profils bruts collectés avant ce lot,
    # que la fusion additive conserve indéfiniment), puis `genere_le`. Sauter
    # la seconde ferait reculer `sources[].synchro_le` de tout profil non
    # recollecté vers son `genere_le` — un horodatage de fraîcheur qui régresse
    # sans qu'aucune donnée n'ait bougé.
    meta_raw = raw_profile.get("meta") or {}
    synchro_sources = meta_raw.get("synchro_sources") or {}
    synchro_le = synchro_sources.get("assemblee_nationale") or synchro_sources.get("nosdeputes")
    if not synchro_le:
        synchro_le = meta_raw.get("genere_le") or time.strftime("%Y-%m-%dT%H:%M:%S%z")
    # --- Profil pivot de base ---
    # L'`id` est le slug, SANS préfixe de provenance (#487, épic #486). Le slug
    # est une donnée d'entrée — le nom du fichier du profil, fixé par
    # `raw_data/candidats.json` ou par le roster —, jamais un résultat de
    # collecte. Le préfixe `nosdeputes:`/`nossenateurs:` dérivait au contraire
    # de la chambre qui avait répondu ce jour-là : entre `25f7bc7` et
    # `01ffa7f`, `jean-luc-melenchon` est passé à `nossenateurs` et
    # `stephane-mazars` à `nosdeputes` — deux bascules en sens opposés, sur des
    # carrières inchangées. Un identifiant que la météo du réseau fait varier
    # n'en est pas un.
    # `source_type` reste utilisé plus bas pour `sources[].type`, où il décrit
    # bien la provenance d'UNE source : c'est vrai, stable, et à sa place.
    profil: dict[str, Any] = make_empty_profil(slug, nom, provenance=provenance)
    # `chambre` n'est plus posée ici (#493) : elle est dérivée plus bas, une fois
    # `mandats[]` normalisé, par `deriver_chambres()` — la seule fabrique du
    # couple `chambres`/`chambre`. `chambre_collecte` n'est plus qu'une entrée de
    # cette dérivation (le repli), plus un champ publié directement.
    profil["parti"] = parti
    profil["groupe"] = identite.get("groupe_nom") or identite.get("groupe_sigle")

    # --- Sources ---
    source_url = raw_profile.get("source") or _URL_SOURCE_PAR_DEFAUT
    sources: list[dict[str, Any]] = [
        {
            "type": source_type,
            "url": source_url,
            "synchro_le": synchro_le,
        }
    ]
    votes_source = raw_profile.get("votes_source")
    if votes_source and "assemblee-nationale" in (votes_source or "").lower():
        an_synchro = (meta_raw.get("synchro_sources") or {}).get("assemblee_nationale") or synchro_le
        sources.append({
            "type": "assemblee_nationale",
            "url": "https://data.assemblee-nationale.fr/",
            "synchro_le": an_synchro,
        })
    profil["sources"] = sources

    # --- Identité (profession/naissance/HATVP) : uniquement si au moins un champ
    # est renseigné, sinon on laisse `identite` à None (valeur par défaut). ---
    identite_champs = {
        # #641 : le code de nomenclature est retiré et l'énoncé d'une absence de
        # profession devient `null` — la fusion ne régressant jamais un scalaire
        # vers `null`, c'est ici, et pas à la collecte, que les cinq profils
        # concernés cessent de publier « Personne diverse sans activité
        # professionnelle » comme une profession.
        "profession": _profession_publiable(identite.get("profession")),
        # #659 — la civilité déclarée par l'état civil d'AMO30, et rien d'autre.
        # Elle n'est JAMAIS dérivée d'un prénom : sans `etatCivil.ident.civ`,
        # c'est `null` (AGENTS.md §2 règle 5). Le champ était lu par l'index
        # d'identité depuis #556 et s'arrêtait au collecteur.
        "civilite": identite.get("civilite"),
        # #659 — les deux niveaux de la nomenclature PCS de l'INSEE, tels que
        # l'Assemblée nationale les applique. Publiés verbatim : c'est la
        # source qui classe. `null` quand elle ne classe pas — le marqueur
        # `xsi:nil` d'AMO30 est filtré à la LECTURE (#556), et « non classé »
        # reste distinct de la famille « Sans profession déclarée », qui est,
        # elle, une valeur de la nomenclature.
        "famille_socioprofessionnelle": identite.get("famille_socioprofessionnelle"),
        "categorie_socioprofessionnelle": identite.get("categorie_socioprofessionnelle"),
        "date_naissance": identite.get("date_naissance"),
        "lieu_naissance": identite.get("lieu_naissance"),
        "num_circo": identite.get("num_circo"),
        "uri_hatvp": identite.get("uri_hatvp"),
        "source_url": identite.get("url_an_ou_senat") or source_url,
    }
    if any(v for k, v in identite_champs.items() if k != "source_url"):
        profil["identite"] = identite_champs

    # --- Identifiants de source (#539) --------------------------------------
    #
    # Le préfixe `nosdeputes:` de l'`id` a été retiré par #487 parce qu'il était
    # instable, mais ce qu'il portait — « d'où vient cette personne » — était une
    # vraie information, simplement rangée au mauvais endroit. Elle vit ici,
    # nommée par référentiel.
    #
    # `an` vient de la table committée quand l'appelant l'a résolue (#525) : le
    # `PA` cesse d'être ré-résolu par correspondance de nom à chaque run, il est
    # publié. À défaut, il est relu dans l'URL de fiche AN déjà collectée —
    # c'est le même fait, à la même source, et ne rien écrire quand on le
    # connaît serait une donnée perdue, pas une donnée manquante.
    #
    # `hatvp` est la RECOPIE de `identite.uri_hatvp`, qui reste en place et que
    # l'interface lit là-bas. Une seule fabrique écrit les deux, donc ils ne
    # peuvent pas diverger. Le compte réel est **285 profils sur 481** au
    # 29/08/2026 : la mesure de 465 qui a circulé comptait les 191 marqueurs
    # `xsi:nil` comme des présences (#556).
    poser_identifiant(profil, "an", acteur_ref or _acteur_ref_de_l_url(
        identite.get("url_an_ou_senat")))
    poser_identifiant(profil, "hatvp", _uri_hatvp_publiable(identite_champs["uri_hatvp"]))

    # --- Sections principales ---
    profil["mandats"] = [_normalize_mandat(m) for m in (raw_profile.get("mandats") or [])]
    profil["votes"] = [_normalize_vote(v, scrutins_index) for v in (raw_profile.get("votes") or [])]
    profil["textes_portes"] = [_normalize_texte_porte(d) for d in (raw_profile.get("dossiers_legislatifs") or [])]
    profil["interventions"] = [_normalize_intervention(i) for i in (raw_profile.get("interventions") or [])]
    profil["amendements"] = [_normalize_amendement(a, profil["id"]) for a in (raw_profile.get("amendements") or [])]

    # --- chambres / chambre (#493) ---
    # Dérivées ici, APRÈS `mandats[]`, et pas avant : les deux champs sortent de
    # la même fabrique et ne peuvent donc pas se contredire. C'est la condition
    # non négociable de leur coexistence — un champ collecté à côté d'un champ
    # dérivé garderait le mensonge à côté de la vérité, en ajoutant la question
    # « lequel croire ».
    profil["chambre"] = chambre_collecte     # repli, consommé par appliquer_chambres
    derivation_chambres = appliquer_chambres(profil)

    # --- Tags thématiques : DÉRIVÉS des interventions, par la fabrique unique
    # `schema_pivot.deriver_tags_thematiques` (#710). Le raisonnement — pourquoi
    # `theme_officiel` prime et pourquoi le repli `mots_cles` survit à #529 — vit
    # dans sa docstring, avec `merge_pivot_profile` qui la rappelle après la
    # fusion : un champ dérivé se recalcule, il ne se fusionne pas.
    profil["tags_thematiques"] = deriver_tags_thematiques(profil.get("interventions"))

    # --- Métadonnées ---
    # `licence_donnees` est DÉRIVÉ de `sources[]`, plus propagé depuis le profil
    # brut (#530, lot 6). Le profil brut portait une constante — « ODbL (Regards
    # Citoyens, à partir de l'Assemblée nationale / Sénat / JO) » — qui décrivait
    # la collecte d'avant #369 et ne décrit plus rien depuis #529 : la collecte
    # française est intégralement sous Licence Ouverte. La propager reviendrait à
    # publier une attribution que le contenu du profil dément, dans un sens comme
    # dans l'autre (voir `licences`).
    appliquer_licence_donnees(profil)
    profil["meta"]["warnings"] = list(meta_raw.get("warnings") or [])

    # #539 — la décision de collecte suit le profil jusqu'au pivot. Écrite
    # seulement si le brut la porte : un profil brut d'avant ce lot n'a rien
    # décidé qu'on sache, et une liste vide écrite ici vaudrait « rien n'a été
    # écarté », ce qui est une affirmation, pas une absence (§2.5).
    # #657 : la FORME de la collecte d'interventions, quand elle n'était pas
    # pleine. Recopiée telle quelle — c'est une déclaration du run qui a produit
    # le brut, pas une dérivation.
    collecte_reduite = meta_raw.get("collecte_reduite")
    if isinstance(collecte_reduite, dict) and collecte_reduite:
        profil["meta"]["collecte_reduite"] = dict(collecte_reduite)

    collecte_ecartee = meta_raw.get("collecte_ecartee")
    if isinstance(collecte_ecartee, list):
        profil["meta"]["collecte_ecartee"] = [
            liste for liste in collecte_ecartee if isinstance(liste, str)
        ]

    # Propagation des avertissements de synchro depuis le profil brut.
    #
    # La clé surveillée est `assemblee_nationale` depuis #529, plus
    # `nosdeputes`. L'ancienne était `None` sur presque tout le corpus depuis
    # #369 — un député résolu dans le référentiel AN ne déclenchait aucun appel
    # NosDéputés, donc aucune synchro à horodater : le warning décrivait le
    # fonctionnement normal, ce qui est la définition d'un warning qui ne dit
    # plus rien. `assemblee_nationale`, lui, est renseigné dès que l'identité
    # est trouvée : à `None`, il signale une vraie absence de collecte.
    synchro_sources = meta_raw.get("synchro_sources") or {}
    if synchro_sources.get("assemblee_nationale") is None:
        profil["meta"]["warnings"].append(avertissement(
            "synchro_sources.assemblee_nationale : aucune synchro réussie "
            "enregistrée dans le profil source.",
            # Fraîcheur de collecte : le lecteur n'en fait rien, nous si (#642).
            DESTINATAIRE_INTERNE,
        ))

    # Mandats électifs dont la chambre n'est pas résolue (#492) : `null` publié,
    # jamais une valeur par défaut (§2.5). **Un seul warning par profil**, et non
    # un par mandat : le cas est uniforme et déterministe (un mandat collecté
    # avant #492 n'a pas d'estampille, et n'en aura une qu'à sa prochaine
    # collecte), et `audit_pivot_dataset.compute_agregation_warnings` agrège par
    # préfixe — un warning par mandat ferait 214 occurrences sur 207 profils
    # (mesuré sur `f5a828b`) là où une par profil dit exactement la même chose.
    # Ce n'est pas le cas de #474 (les 92 parlementaires en mission sont écartés
    # sans warning parce que leur exclusion est le comportement attendu et
    # permanent) : ici le `null` est un manque transitoire, et le compte est
    # précisément la mesure qui dit quand la migration est terminée.
    n_sans_chambre = sum(
        1 for m in profil["mandats"]
        if m.get("categorie") == "mandat_electif" and not m.get("chambre")
    )
    if n_sans_chambre:
        profil["meta"]["warnings"].append(avertissement(
            f"{WARNING_PREFIX_CHAMBRE_MANDAT_NON_RESOLUE} : {n_sans_chambre} mandat(s) "
            "électif(s) sans chambre déterminée, publiés à null (#492). La chambre est "
            "estampillée à la collecte ; un mandat conservé par la fusion additive et "
            "collecté avant #492 n'en porte pas, et elle n'est pas reconstituable a "
            "posteriori — ni depuis `source_url` (jamais renseignée sur un mandat électif "
            "AN/Sénat), ni depuis la chambre du profil (la fusion additive y accumule des "
            "mandats des deux chambres).",
            # Compteur de migration de #492 : il mesure ce que la fusion
            # additive n'a pas encore rattrapé. C'est notre thermomètre (#642).
            DESTINATAIRE_INTERNE,
        ))

    # `chambres` non corroborée (#493) : déclarée, jamais muette. C'est ce qui
    # sépare « utilisable » de « trompeur » — un consommateur migré tôt (#494)
    # peut distinguer une liste que les mandats étayent entièrement d'une liste
    # où la chambre de collecte figure sur sa seule parole. Un warning par
    # profil, comme celui de #492 et pour la même raison : le cas est uniforme,
    # et c'est le compte de profils qui est l'information utile.
    if not derivation_chambres.corroboree:
        profil["meta"]["warnings"].append(avertissement(
            f"{WARNING_PREFIX_CHAMBRES_NON_CORROBOREE} : "
            f"chambres={derivation_chambres.chambres}, dont "
            f"{derivation_chambres.chambres_non_corroborees} sans mandat "
            "électif estampillé pour l'étayer (#493). Une chambre non corroborée est "
            "celle de la collecte : elle dit quel jeu de données a répondu, pas où la "
            "personne a siégé — l'épic #486 a mesuré qu'elle peut être fausse dans les "
            "deux sens.",
            # Compteur de migration de #493, qu'AGENTS.md §3d désigne comme tel :
            # « une chambre non corroborée » n'est pas une phrase de page
            # publique, c'est une mesure de notre avancement (#642).
            DESTINATAIRE_INTERNE,
        ))

    # #642 : le jumeau typé, recomposé après la dernière mutation de
    # `meta.warnings` — champ dérivé, comme `chambres` et `licence_donnees`.
    deriver_avertissements(profil["meta"])

    return profil
