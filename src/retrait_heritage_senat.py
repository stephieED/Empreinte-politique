#!/usr/bin/env python3
"""
retrait_heritage_senat.py — Ce que la collecte sénatoriale remplace (#885, point 5).

Deux retraits, et ils n'ont ni la même cause ni le même moment
---------------------------------------------------------------
**Une entrée `sources[]` qui ment sur sa provenance.** `jean-luc-melenchon`
porte un `sources[]` de type `nossenateurs` dont l'URL est un **article de
LCP** — `lcp.fr/actualites/presidentielle-2027-la-liste-des-candidats…`. Elle
vient de `raw_data/candidats.json`, où ce lien atteste que l'intéressé est
**candidat déclaré** ; ce n'est pas une source de données parlementaires, et
encore moins Regards Citoyens. Une fusion ancienne l'a rangée là, et la fusion
additive l'y garde (#729).

Le défaut est autonome : il ne dépend d'aucune collecte, et il se corrige
**maintenant**. Un profil qui déclare une provenance qu'il n'a pas fausse la
traçabilité (§2 règle 2) et, ici, la licence qu'il en tire (§7).

**Des mandats que le Sénat remplace.** `bruno-retailleau` publie « Mandat
parlementaire (Les Républicains) » depuis le 26/09/2004, **sans fin** ;
`jean-luc-melenchon` le sien de 2004 à 2010. La source sénatoriale en donne
respectivement **4** et **3**, bornés, avec leurs motifs.

Celui-là **ne se fait pas avant** que la publication sénatoriale soit branchée :
retirer d'abord viderait la fiche de Retailleau de son mandat parlementaire, et
un corpus qui perd un fait en attendant son remplaçant publie un trou.

Ce que le retrait ne touche pas
--------------------------------
Les **8 autres** entrées sans `categorie_source` de `bruno-retailleau` — des
commissions, groupes d'études et organismes extra-parlementaires, tous sans
date. C'est la mesure de #878 qui tient : le « doublon hérité » fait **2
entrées, pas 9**.

Leur raison a changé, elle. #878 disait « 2, parce que seules 2 ont un
équivalent chez l'Assemblée ». Aujourd'hui les 9 en ont un — **sénatorial**. Ce
qui rend les 7 autres retirables un jour, c'est qu'on les remplace, pas qu'elles
soient fausses ; et ce jour-là, c'est un appariement entrée par entrée qu'il
faudra, pas un retrait en bloc.
"""

from __future__ import annotations

from typing import Any, Optional

from licences import MOTIFS_URL_REGARDS_CITOYENS
from normalize_senat import CATEGORIE_SOURCE, normalize_mandats
from senat_opendata import periodes_se_recouvrent

#: Les types de source qui **prétendent** venir de Regards Citoyens. Une entrée
#: de ce type dont l'URL n'en vient pas est une provenance fausse.
TYPES_REGARDS_CITOYENS = frozenset({"nosdeputes", "nossenateurs"})


def _cle_appartenance(mandat: dict[str, Any]) -> tuple[Any, ...]:
    """Ce qui identifie une appartenance sénatoriale publiée.

    Le libellé en fait partie — c'est ce qui rend le retrait ci-dessous
    nécessaire, et c'est aussi ce qui le rend sûr : deux entrées de même période
    et de même catégorie sous deux noms différents sont deux entrées distinctes
    pour la fusion, donc deux lignes à l'écran.
    """
    return (mandat.get("label"), mandat.get("debut"),
            mandat.get("fin"), mandat.get("categorie"))


def mandats_senatoriaux_orphelins(
    profil: dict[str, Any],
    brut: dict[str, Any],
) -> list[dict[str, Any]]:
    """Les appartenances sénatoriales publiées que la collecte ne produit plus.

    ## Pourquoi elles existent

    La fusion des profils est **additive** : une entrée dont le libellé change
    n'en remplace pas une, elle s'ajoute à côté. #912 a corrigé la colonne lue —
    `Culture` est devenu « Commission de la culture, de l'éducation, de la
    communication et du sport » — et le run du 13/09/2026 a donc publié les deux.
    Mesuré sur le commit de données `d2a56641a` : **126 entrées sénatoriales sur
    `bruno-retailleau` pour 101 collectées**, 40 pour 32 sur
    `jean-luc-melenchon`. Trente-trois doublons, à l'écran.

    ## Le critère, et pourquoi il passe par la normalisation

    Le bloc `mandat_senatorial` du brut porte ce que la collecte a rendu au
    dernier run : les deux couches se contrôlent l'une l'autre (#729), et aucun
    export n'a besoin d'être retéléchargé pour trancher.

    Mais **le brut ne se compare pas au pivot tel quel** : `normalize_senat`
    transforme le libellé — « Groupe UMP » y devient « Groupe UMP (rattaché) ».
    Comparer les deux directement désignait une entrée **légitime** comme
    orpheline. Le brut est donc passé par la normalisation avant comparaison,
    ce qui reproduit exactement ce que la chaîne publie.

    Vérification que le critère porte : sur les deux profils, **aucune** entrée
    normalisée n'est absente du pivot. La correspondance est exacte dans l'autre
    sens, ce qui distingue « le pivot en porte trop » de « les deux divergent ».

    Rend la liste sans rien retirer, comme les autres fonctions de ce module.
    """
    bloc = brut.get("mandat_senatorial") or {}
    collectes = bloc.get("mandats_senatoriaux")
    if not collectes:
        # Rien de collecté : on ne peut pas distinguer « plus produit » de
        # « pas encore collecté », et le second ne justifie aucun retrait.
        return []
    attendues = {_cle_appartenance(m) for m in normalize_mandats(collectes)}
    return [m for m in (profil.get("mandats") or [])
            if isinstance(m, dict)
            and m.get("categorie_source") == CATEGORIE_SOURCE
            and _cle_appartenance(m) not in attendues]


def source_ment_sur_sa_provenance(source: dict[str, Any]) -> bool:
    """True si l'entrée se dit Regards Citoyens et que son URL dit autre chose.

    Le critère est **l'URL**, pas notre opinion : `licences.MOTIFS_URL_REGARDS_CITOYENS`
    est le référentiel des domaines, et le recopier ici ferait de ce module un
    second référentiel (#530).

    Une entrée **sans URL** n'est pas jugée : elle ne dit rien, et une absence
    n'est pas un mensonge (§2 règle 5).
    """
    if source.get("type") not in TYPES_REGARDS_CITOYENS:
        return False
    url = source.get("url")
    if not isinstance(url, str) or not url.strip():
        return False
    return not any(motif in url.lower() for motif in MOTIFS_URL_REGARDS_CITOYENS)


def retirer_sources_menteuses(profil: dict[str, Any]) -> list[dict[str, Any]]:
    """Retire ces entrées de `sources[]` et rend celles qui sont parties.

    Ne recompose pas `meta.licence_donnees` : c'est un champ dérivé, et sa
    fabrique est `licences.appliquer_licence_donnees` (§7). L'appelant la lance
    après, comme après toute étape qui déplace `sources[]`.
    """
    sources = profil.get("sources") or []
    retirees = [s for s in sources if isinstance(s, dict) and source_ment_sur_sa_provenance(s)]
    if retirees:
        profil["sources"] = [s for s in sources if s not in retirees]
    return retirees


#: Les appartenances non électives héritées de NosSénateurs, et l'organe
#: sénatorial qui les remplace — **une ligne par entrée, écrite à la main**
#: (#908).
#:
#: Pourquoi une table et non une heuristique. Six des huit s'apparient à
#: l'identique une fois #912 corrigé, et une règle de similarité les prendrait
#: aussi. Les deux dernières ne diffèrent pas dans le même sens : « Groupe
#: Chrétiens d'Orient » porte un mot **de plus** que le libellé du Sénat,
#: « Groupe d'études Agriculture et alimentation » un mot **de moins**. Une
#: règle assez souple pour les deux accepterait « Groupe d'études Élevage »,
#: qui est un organe **distinct** du Sénat. C'est la faute que #878 a commise
#: dans l'autre sens, et la raison pour laquelle #908 écrit « pas de
#: remplacement en bloc ».
#:
#: Chaque ligne a été vérifiée contre l'export : pour les deux libellés qui ne
#: coïncident pas, la source ne porte **qu'un seul** organe candidat.
APPARIEMENTS_HERITES: dict[str, str] = {
    # Identiques au libellé publié par le Sénat une fois `libcomlilmin` lu (#912).
    "Collège consultatif de la commission du fonds pour le développement de la vie associative":
        "Collège consultatif de la commission du fonds pour le développement de la vie associative",
    "Commission départementale de la coopération intercommunale":
        "Commission départementale de la coopération intercommunale",
    "Commission départementale de répartition des crédits de la dotation d'équipement des territoires ruraux":
        "Commission départementale de répartition des crédits de la dotation d'équipement des territoires ruraux",
    "Groupe d'information internationale sur le Haut-Karabagh":
        "Groupe d'information internationale sur le Haut-Karabagh",
    "Groupe d'études Statut, rôle et place des Français établis hors de France":
        "Groupe d'études Statut, rôle et place des Français établis hors de France",
    # #912 fait de celui-ci un exact : `evelib` publiait « Culture ».
    "Commission de la culture, de l'éducation et de la communication":
        "Commission de la culture, de l'éducation et de la communication",
    # Le Sénat nomme l'organe sans le mot « Groupe », et le range en groupe de
    # LIAISON — l'entrée héritée le rangeait en groupe d'amitié. Le
    # remplacement corrige donc aussi sa catégorie.
    "Groupe Chrétiens d'Orient": "Chrétiens d'Orient",
    # `orgcod=919`, seul organe sénatorial dont le nom porte « agriculture » ou
    # « alimentation ». « Groupe d'études Élevage » existe à côté : c'est un
    # autre organe, et il n'est pas concerné.
    "Groupe d'études Agriculture et alimentation":
        "Groupe d'études Agriculture, élevage et alimentation",
}


def _labels_publies(labels: Any) -> set[str]:
    """Les libellés sénatoriaux effectivement publiés — **`None` exclu**.

    Cinq appartenances sénatoriales sont publiées sans nom : leur organe n'a
    aucune ligne dans la table des libellés, et `decouper_sur_renommages` le
    déclare (`libelle_non_resolu`) plutôt que de l'inventer (§2 règle 5).

    Les garder ici serait une faute, et elle a été commise : `table.get(label)`
    rend `None` pour un libellé **absent de la table**, et `None in publies`
    était alors vrai. La fonction proposait au retrait **17 mandats de député**
    de `jean-luc-melenchon` — « Commission des affaires étrangères », 2017-2022,
    Assemblée nationale — au seul motif qu'ils n'étaient pas estampillés. Même
    famille que le défaut que le recouvrement de période a corrigé sur
    `mandats_electifs_remplaces` : **un critère trop large efface un fait**.
    """
    return {label for label in labels if isinstance(label, str) and label}


def _est_remplace(mandat: dict[str, Any], table: dict[str, str], publies: set[str]) -> bool:
    """True si ce mandat a une ligne dans la table ET que son remplaçant est publié."""
    remplacant = table.get(mandat.get("label"))
    return bool(remplacant) and remplacant in publies


def mandats_apparies_remplaces(
    profil: dict[str, Any],
    appariements: Optional[dict[str, str]] = None,
) -> list[dict[str, Any]]:
    """Les appartenances **non électives** héritées qu'un organe sénatorial remplace.

    Rend la liste sans rien retirer, comme `mandats_electifs_remplaces` : le
    retrait attend que le remplaçant soit publié.

    Trois conditions, et la troisième est celle qui empêche de publier un trou :

      - l'absence de `categorie_source` — personne n'a établi cette catégorie ;
      - une ligne dans `APPARIEMENTS_HERITES`, écrite et vérifiée à la main ;
      - **la présence effective du remplaçant** dans `mandats[]`, estampillé
        `senat`. Une table d'appariement dit ce qui *devrait* remplacer ; elle
        ne prouve pas que la collecte l'a publié. Sans ce contrôle, un lot qui
        renommerait l'organe côté source retirerait le fait hérité sans que
        rien ne prenne sa place.

    Les mandats électifs sont hors de ce périmètre : ils ont leur propre
    fonction, et leur critère est le **recouvrement de période**, pas le nom.
    """
    table = APPARIEMENTS_HERITES if appariements is None else appariements
    mandats = profil.get("mandats") or []
    publies = _labels_publies(m.get("label") for m in mandats
                              if isinstance(m, dict) and m.get("categorie_source") == "senat")
    return [m for m in mandats if isinstance(m, dict)
            and m.get("categorie") != "mandat_electif"
            and not m.get("categorie_source")
            and _est_remplace(m, table, publies)]


def mandats_electifs_remplaces(
    profil: dict[str, Any],
    chambre_remplacante: str = "Senat",
) -> list[dict[str, Any]]:
    """Les mandats électifs **non estampillés** qu'une source datée remplace.

    Rend la liste sans rien retirer : ce retrait attend la publication, et une
    fonction qui retire ce qui n'a pas encore de remplaçant produit un trou.

    Trois conditions, et la troisième a été ajoutée après coup parce qu'elle
    manquait :

      - l'absence de `categorie_source` — « personne n'a établi cette
        catégorie » (#718) ;
      - la présence d'au moins un mandat **estampillé de la chambre
        remplaçante**, sans quoi rien n'est proposé — c'est ce qui empêche le
        retrait de s'exécuter avant la publication ;
      - **le recouvrement de période avec l'un de ces remplaçants.**

    Sans la troisième, la fonction proposait le mandat de **député** de
    `jean-luc-melenchon` (21/06/2017 → 21/06/2022) au seul motif qu'il n'était
    pas estampillé et qu'un mandat sénatorial existait ailleurs sur sa fiche.
    Ses mandats de sénateur s'arrêtent en 2010 : celui de 2017 n'est remplacé
    par rien, et le retirer aurait effacé un mandat de député. C'est aussi ce
    qui fait que le compte est **2 et non 3**, comme #878 l'avait mesuré.
    """
    mandats = profil.get("mandats") or []
    remplacants = [m for m in mandats if isinstance(m, dict)
                   and m.get("categorie_source")
                   and m.get("chambre") == chambre_remplacante
                   and m.get("categorie") == "mandat_electif"]
    if not remplacants:
        return []
    return [m for m in mandats if isinstance(m, dict)
            and m.get("categorie") == "mandat_electif"
            and not m.get("categorie_source")
            and any(periodes_se_recouvrent(m.get("debut"), m.get("fin"),
                                           r.get("debut"), r.get("fin"))
                    for r in remplacants)]


def mandats_bruts_apparies_remplaces(
    brut: dict[str, Any],
    appariements: Optional[dict[str, str]] = None,
) -> list[dict[str, Any]]:
    """`mandats_apparies_remplaces`, côté **brut** — la moitié qu'on oublie (#729).

    Le remplaçant se lit dans le bloc `mandat_senatorial` du brut lui-même, et
    non dans le pivot : les deux couches se contrôlent l'une l'autre, et faire
    dépendre le brut du pivot inverserait le sens de la chaîne.
    """
    table = APPARIEMENTS_HERITES if appariements is None else appariements
    bloc = brut.get("mandat_senatorial") or {}
    publies = _labels_publies(m.get("label") for m in (bloc.get("mandats_senatoriaux") or [])
                              if isinstance(m, dict))
    return [m for m in (brut.get("mandats") or [])
            if isinstance(m, dict)
            and m.get("categorie") != "mandat_electif"
            and not m.get("categorie_source")
            and _est_remplace(m, table, publies)]


def mandats_bruts_remplaces(brut: dict[str, Any]) -> list[dict[str, Any]]:
    """Les mêmes, côté **brut** — et c'est la moitié qu'on oublie.

    Le point 5 de #885 dit « aux deux couches » (#729), et la raison est
    mécanique : `audit_collecte_vs_publie` compare le brut au pivot, seuil 0.
    Retirer d'un seul côté produit un **déficit** qui bloque le commit — mesuré,
    2 couples et 2 entrées, avant que ce retrait n'existe.

    Le remplaçant se lit dans le bloc `mandat_senatorial` du brut lui-même, et
    non dans le pivot : les deux couches se contrôlent l'une l'autre, et faire
    dépendre le brut du pivot inverserait le sens de la chaîne.
    """
    bloc = brut.get("mandat_senatorial") or {}
    remplacants = [m for m in (bloc.get("mandats_senatoriaux") or [])
                   if isinstance(m, dict) and m.get("famille") == "mandat_parlementaire"]
    if not remplacants:
        return []
    return [m for m in (brut.get("mandats") or [])
            if isinstance(m, dict)
            and m.get("categorie") == "mandat_electif"
            and not m.get("categorie_source")
            and any(periodes_se_recouvrent(m.get("debut"), m.get("fin"),
                                           r.get("debut"), r.get("fin"))
                    for r in remplacants)]
