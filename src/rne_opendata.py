#!/usr/bin/env python3
"""Les mandats locaux, lus au Répertoire national des élus (#922).

Les fiches ne portaient **aucun mandat local** — ni maire, ni conseiller
municipal, départemental ou régional — alors que plus de la moitié des candidats
déclarés en exercent un. Nos trois sources (AN, Sénat, Parlement européen) ne
couvrent que le versant parlementaire.

## Ce que ce module lit, et ce qu'il refuse

Deux jeux, tous deux sous **Licence Ouverte 2.0**, tous deux interrogeables par
`tabular-api.data.gouv.fr` — soit ~160 requêtes par run contre 76 Mo de
téléchargement :

- le **RNE** pour les mandats **en cours** ;
- les **sortants 2020-2026** pour la mandature précédente.

Il refuse les trois fichiers du RNE qui portent des mandats **déjà collectés
ailleurs** — députés, sénateurs, représentants au Parlement européen. Les lire
publierait deux fois le même mandat, avec deux dates de début potentiellement
différentes, et rien ne dirait laquelle fait foi.

## La borne, et pourquoi elle est à 2020

Rien avant 2020 n'est intégré (`BORNE_COUVERTURE`). Deux raisons **distinctes**,
et une seule est réversible : les jeux complets de 2014 et de 2020 ne déclarent
aucune licence (§7 interdit de collecter ce qu'on ne peut pas attribuer), et les
seuls jeux de 2014 sous Licence Ouverte ne couvrent que le **premier tour**.

Une absence avant cette borne ne se tait pas : elle se déclare.
La décision qui la fixe porte le numéro #922 et vit sous `docs/decisions/`.

## Les trois pièges, tous payés en mesurant

1. **`responsible` n'est pas `type`** — l'équivalent ici est que le patronyme
   seul ne veut rien dire : 400 « MATHIEU » chez les conseillers municipaux, 148
   « VERDIER », 93 « LALANNE ». Avec le prénom : 0, 1 et 0.
2. **Les diacritiques sont incohérents dans la source** : « Edouard » sans accent
   et « Jérôme » avec, dans le même fichier. Apparier sur le prénom tel qu'écrit
   rendait Édouard Philippe **sans aucun mandat**, alors qu'il est maire du
   Havre — et l'échec est entièrement silencieux. D'où `aplatir()`.
3. **Le même mandat est publié dans deux fichiers** : un maire figure chez les
   conseillers municipaux avec la fonction « Maire », *et* chez les maires. La
   clé de déduplication est `(commune, date de début)`, jamais le fichier.

Usage :

    from rne_opendata import mandats_locaux
    mandats = mandats_locaux(appel, "PHILIPPE", "Édouard", "1970-11-28")
"""

from __future__ import annotations

import unicodedata
from typing import Any, Callable, Iterable, Optional

#: Le catalogue, qui résout les identifiants de ressource. Le `rid` **change à
#: chaque publication trimestrielle** — l'URL d'un fichier porte sa date
#: (`20260811-155100`). Le coder en dur ferait collecter un corpus figé au jour
#: où quelqu'un l'a copié, sans que rien ne le dise.
URL_CATALOGUE = "https://www.data.gouv.fr/api/1/datasets/{slug}/"

#: L'API tabulaire, qui filtre côté serveur par colonne.
URL_TABULAIRE = "https://tabular-api.data.gouv.fr/api/resources/{rid}/data/"

DATASET_RNE = "repertoire-national-des-elus-1"
DATASET_SORTANTS = (
    "elections-municipales-2026-maires-et-conseillers-municipaux-sortants")

#: La couverture commence ici. Voir le docstring du module.
BORNE_COUVERTURE = "2020"

#: Les fichiers du RNE que ce module lit, et la catégorie qu'ils décrivent.
#: Neuf fichiers : s'arrêter aux deux premiers aurait conclu « aucun mandat »
#: pour Marine Tondelier, que seul le fichier **régional** porte.
FICHIERS_LOCAUX: dict[str, str] = {
    "elus-conseillers-municipaux-cm": "conseil_municipal",
    "elus-maires-mai": "mairie",
    "elus-conseillers-darrondissements-ca": "conseil_arrondissement",
    "elus-conseillers-communautaires-epci": "conseil_communautaire",
    "elus-conseillers-departementaux-cd": "conseil_departemental",
    "elus-conseillers-regionaux-cr": "conseil_regional",
    "elus-membres-assemblee-ma": "assemblee_territoriale",
    "elus-conseillers-des-francais-de-letranger-consfde": "conseil_francais_etranger",
    "elus-assemblee-des-francais-de-letranger-afe": "assemblee_francais_etranger",
}

#: Ce que ce module refuse **à l'entrée**, et la raison — même geste que
#: `senat_opendata.TABLES_REFUSEES`. Ces trois fichiers portent des mandats que
#: nos sources institutionnelles collectent déjà, avec leur propre datation :
#: les lire publierait le même mandat deux fois, sans que rien ne dise laquelle
#: des deux dates fait foi.
FICHIERS_REFUSES: dict[str, str] = {
    "elus-deputes-dep": "collecté par l'open data de l'Assemblée nationale",
    "elus-senateurs-sen": "collecté par data.senat.fr depuis #885",
    "elus-representants-Parlement-européen-rpe": (
        "collecté par l'Open Data Portal du Parlement européen"),
}

#: La colonne qui porte le nom, et celle qui porte le prénom.
COL_NOM = "Nom de l'élu"
COL_PRENOM = "Prénom de l'élu"
COL_NAISSANCE = "Date de naissance"
COL_DEBUT_MANDAT = "Date de début du mandat"
COL_DEBUT_FONCTION = "Date de début de la fonction"
COL_FONCTION = "Libellé de la fonction"

#: Les colonnes de lieu, par ordre de précision décroissante. Un fichier
#: départemental ne porte pas de commune, un régional ne porte ni l'un ni
#: l'autre : prendre la première renseignée est le seul moyen de nommer le
#: ressort d'un mandat sans supposer lequel.
COLS_LIEU = (
    "Libellé de la commune",
    "Libellé de l'EPCI",
    "Libellé du département",
    "Libellé de la région",
    "Libellé de la collectivité à statut particulier",
)


class RneIndisponible(RuntimeError):
    """Le catalogue ou l'API tabulaire n'a rien rendu d'exploitable.

    Levée plutôt que de rendre une liste vide : une liste vide se publierait
    comme « cette personne n'a aucun mandat local », qui est un constat sur la
    personne et non sur la panne (§2 règle 5, la confusion de #510).
    """


def aplatir(valeur: Optional[str]) -> str:
    """Le texte sans diacritiques ni casse, pour comparer deux orthographes.

    La source est **incohérente** : « Edouard » sans accent et « Jérôme » avec,
    dans le même fichier. Comparer les chaînes telles quelles rate
    silencieusement — mesuré le 14/09/2026, Édouard Philippe ressortait sans
    aucun mandat alors qu'il est maire du Havre.

    Sert à **comparer**, jamais à publier : ce qui est publié reste le verbatim
    de la source.
    """
    if not valeur:
        return ""
    sans_accent = "".join(
        c for c in unicodedata.normalize("NFD", valeur)
        if unicodedata.category(c) != "Mn")
    return sans_accent.upper().replace("-", " ").strip()


def lieu_de(ligne: dict[str, Any]) -> Optional[str]:
    """Le ressort du mandat, à la maille la plus fine que la ligne porte."""
    for colonne in COLS_LIEU:
        valeur = (ligne.get(colonne) or "").strip()
        if valeur:
            return valeur
    return None


def concerne(ligne: dict[str, Any], nom: str, prenom: str) -> bool:
    """Cette ligne décrit-elle bien la personne cherchée ?

    Le filtrage côté serveur porte sur les chaînes exactes ; ce contrôle-ci
    rattrape les diacritiques, et il est **obligatoire** quand l'interrogation
    s'est faite par date de naissance : quatre personnes sont nées le
    28/11/1970 dans tout le RNE, une seule s'appelle Philippe.
    """
    return (aplatir(ligne.get(COL_NOM)) == aplatir(nom)
            and aplatir(ligne.get(COL_PRENOM)) == aplatir(prenom))


def cle_de_mandat(ligne: dict[str, Any]) -> tuple:
    """`(lieu, date de début)` — la clé qui dédoublonne deux fichiers.

    Un maire est publié **deux fois** : chez les conseillers municipaux avec la
    fonction « Maire », et chez les maires. C'est le même mandat. Se clé sur le
    fichier d'origine en publierait deux.
    """
    return (aplatir(lieu_de(ligne)), ligne.get(COL_DEBUT_MANDAT))


def normaliser(
    ligne: dict[str, Any],
    categorie_lieu: str,
    en_cours: bool,
    constate_le: Optional[str],
    source_url: str,
) -> dict[str, Any]:
    """Une ligne du RNE devient un mandat pivot.

    ## `fin` est TOUJOURS nulle, et ce n'est pas un trou

    Aucun des deux jeux ne publie de date de fin : ils portent
    `Date de début du mandat` et `Date de début de la fonction`, jamais l'autre
    borne. On obtient donc une suite de **débuts datés** et d'**états constatés
    à une date**. « Maire du Havre depuis le 28/06/2020, constaté le
    27/02/2026 » est sourçable ; « jusqu'en mars 2026 » serait une inférence
    (§2 règle 5).

    D'où `fin: null` **avec** `fin_non_resolue`, qui nomme la cause et porte la
    date de constat — le patron de `sort_non_resolu` (#747) : ni les deux, ni
    aucun des deux.

    `actif` dit lequel des deux jeux a rendu la ligne, jamais une déduction :
    le RNE ne publie que des mandats en cours, le fichier des sortants que des
    mandats clos.
    """
    fonction = (ligne.get(COL_FONCTION) or "").strip() or None
    mandat: dict[str, Any] = {
        "label": lieu_de(ligne) or "",
        "categorie": "mandat_local",
        "categorie_source": "rne",
        "type_organe_source": categorie_lieu,
        "fonction": fonction,
        "debut": ligne.get(COL_DEBUT_MANDAT) or None,
        "fin": None,
        "actif": bool(en_cours),
        "source_url": source_url,
        "fin_non_resolue": {
            "motif": "source_sans_date_de_fin",
            "constate_le": constate_le,
        },
    }
    debut_fonction = ligne.get(COL_DEBUT_FONCTION) or None
    if fonction and debut_fonction and debut_fonction != mandat["debut"]:
        # Un maire est d'abord élu conseiller, puis désigné maire quelques jours
        # plus tard : deux dates, deux faits. Les confondre ferait commencer une
        # fonction avant sa désignation.
        mandat["debut_fonction"] = debut_fonction
    return mandat


def resoudre_ressources(appel: Callable[[str], Any], slug: str) -> dict[str, str]:
    """`{titre de fichier: rid}` pour un jeu du catalogue.

    Le `rid` change à chaque publication : il se résout, il ne se code pas.
    """
    catalogue = appel(URL_CATALOGUE.format(slug=slug))
    ressources = (catalogue or {}).get("resources") or []
    resolues = {}
    for ressource in ressources:
        titre = (ressource.get("title") or "").replace(".csv", "")
        rid = ressource.get("id")
        if titre and rid:
            resolues[titre] = rid
    if not resolues:
        raise RneIndisponible(
            f"{slug} : le catalogue ne rend aucune ressource exploitable.")
    return resolues


#: Lignes par page de l'API tabulaire. Une page ne suffit pas toujours : mesuré le
#: 16/09/2026, la date de naissance de Delphine Batho est partagée par 49 élus du
#: fichier des conseillers municipaux sortants — à une ligne du plafond.
TAILLE_PAGE = 50

#: Au-delà, on cesse de suivre les pages : une date de naissance partagée par
#: plus de 1 000 élus n'existe pas, et une boucle sans fin sur une API ne se
#: rattrape pas.
PAGES_MAX = 20


def dates_de_naissance_interrogees(date_naissance: str) -> tuple[str, ...]:
    """La date telle qu'elle est, et la même un siècle plus tard (#922).

    LE FICHIER DES SORTANTS PUBLIE DES NAISSANCES AU XXIᵉ SIÈCLE. Il donnait
    l'année sur deux chiffres (« 02/02/69 ») ; convertie en ISO, une année basse
    a pris le mauvais siècle. Mesuré le 16/09/2026 à la source :

      David Lisnard     né 1969-02-02  publié 2069-02-02
      Édouard Philippe né 1970-11-28  publié 2070-11-28
      Gabriel Attal    né 1989-03-16  publié 1989-03-16 (correct)

    Interrogée sur la seule date exacte, la source ne rendait rien, et le mandat
    clos disparaissait sans erreur : **5 mandats 2020-2026** sur les candidats
    déclarés (Lisnard, Philippe, Roussel, Bouamrane, Bertrand). Les 4 mandats clos
    que le corpus portait étaient tous ceux de candidats nés après 1980 — la
    signature exacte du défaut.

    Le seuil de bascule n'est **pas deviné** : les deux formes sont toujours
    demandées. Aucun élu ne peut être né après 2050, donc la forme décalée ne
    peut désigner qu'une date corrompue, et `concerne()` vérifie le nom et le
    prénom sur chaque ligne dans les deux cas.
    """
    annee, reste = date_naissance[:4], date_naissance[4:]
    if not annee.isdigit():
        return (date_naissance,)
    return (date_naissance, f"{int(annee) + 100}{reste}")


def _toutes_les_pages(appel: Callable[[str], Any], url: str) -> list[dict[str, Any]]:
    """Toutes les lignes d'une requête, page après page (#922).

    Le module ne lisait que la première page : une personne en 51ᵉ position
    était perdue en silence. On suit `links.next` tant que le serveur en donne
    une, jusqu'à `PAGES_MAX`.
    """
    lignes: list[dict[str, Any]] = []
    suivante: Optional[str] = url
    for _ in range(PAGES_MAX):
        if not suivante:
            break
        reponse = appel(suivante) or {}
        lignes.extend(l for l in (reponse.get("data") or []) if isinstance(l, dict))
        suivante = (reponse.get("links") or {}).get("next")
    return lignes


def lignes_de(
    appel: Callable[[str], Any],
    rid: str,
    nom: str,
    prenom: str,
    date_naissance: Optional[str],
) -> list[dict[str, Any]]:
    """Les lignes d'un fichier qui décrivent cette personne.

    **Deux clés d'interrogation, et la première est la bonne quand on l'a.**
    Interroger par date de naissance contourne d'un coup le problème des
    diacritiques. À défaut, on interroge par nom — le patronyme, moins souvent
    accentué que le prénom — et on filtre le prénom en mémoire.

    La date est demandée sous DEUX formes : voir
    `dates_de_naissance_interrogees`, et le siècle que le fichier des sortants a
    ajouté aux naissances.

    Dans tous les cas, `concerne()` tranche : le filtrage serveur ne suffit
    jamais seul.
    """
    base = URL_TABULAIRE.format(rid=rid)
    if date_naissance:
        filtres = [f"{COL_NAISSANCE}__exact={d}"
                   for d in dates_de_naissance_interrogees(date_naissance)]
    else:
        filtres = [f"{COL_NOM}__exact={aplatir(nom)}"]
    lignes: list[dict[str, Any]] = []
    for filtre in filtres:
        lignes.extend(_toutes_les_pages(appel, f"{base}?{filtre}&page_size={TAILLE_PAGE}"))
    return [l for l in lignes if concerne(l, nom, prenom)]


def mandats_locaux(
    appel: Callable[[str], Any],
    nom: str,
    prenom: str,
    date_naissance: Optional[str] = None,
    constate_le: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Tous les mandats locaux d'une personne, dédoublonnés.

    Args:
        appel: fonction qui rend le JSON d'une URL. Injectée pour que la
            collecte soit testable sans réseau, et pour qu'un seul endroit
            porte les en-têtes et le cache.
        nom, prenom: l'état civil tel que NOUS l'écrivons. La comparaison est
            faite sans diacritiques (`aplatir`).
        date_naissance: quand le corpus la porte, c'est la clé. Les candidats
            déclarés qui n'en ont pas passent par la table relue
            `raw_data/correspondance_elus_rne.json` (#922).
        constate_le: la date d'état du jeu des sortants, reportée telle quelle
            dans `fin_non_resolue`.

    Returns:
        Une liste de mandats pivot, **triée** par date de début puis par lieu —
        un ordre instable ferait bouger un profil sans que rien n'ait bougé.
    """
    trouves: dict[tuple, dict[str, Any]] = {}
    for slug, en_cours in ((DATASET_RNE, True), (DATASET_SORTANTS, False)):
        ressources = resoudre_ressources(appel, slug)
        for titre, rid in ressources.items():
            if titre in FICHIERS_REFUSES:
                continue
            categorie = FICHIERS_LOCAUX.get(titre)
            if categorie is None and slug == DATASET_RNE:
                # Un fichier que le RNE ajouterait sans qu'on l'ait classé : il
                # est ignoré, mais il ne l'est pas en silence — le classer est
                # un geste, pas un défaut de configuration.
                continue
            if categorie is None:
                categorie = "conseil_municipal"
            for ligne in lignes_de(appel, rid, nom, prenom, date_naissance):
                mandat = normaliser(
                    ligne, categorie, en_cours, constate_le,
                    f"https://www.data.gouv.fr/datasets/{slug}")
                cle = cle_de_mandat(ligne)
                # Le premier gagne : le RNE (mandats en cours) est interrogé
                # avant les sortants, donc un mandat encore exercé n'est jamais
                # rétrogradé en mandat clos par son jumeau de l'autre fichier.
                trouves.setdefault(cle, mandat)
    return sorted(
        trouves.values(),
        key=lambda m: (m.get("debut") or "", m.get("label") or ""))
