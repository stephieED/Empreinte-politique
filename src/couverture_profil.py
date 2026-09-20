#!/usr/bin/env python3
"""
couverture_profil.py — Pourquoi une liste d'un profil est vide (#539).

Fabrique unique du bloc `couverture` du schéma pivot. Le vocabulaire (les
quatre états, les **trois** causes depuis #562, les cinq listes) vit dans
`schema_pivot` avec le reste du contrat de structure ; ce module porte les
**bornes mesurées** et la **dérivation**.

## Les décisions qui gouvernent ce module

Trois, et le module n'en a jamais cité aucune — les numéros d'issue ci-dessous
ne disent pas où lire. La liste complète et à jour :
`docs/decisions-par-module.md`.

- `docs/decisions/couverture-listes-539.md` — les quatre états, la `cause`
  obligatoire sur `non_collecte` et interdite ailleurs, les cinq listes, et la
  décision 4 : `couverture` est **remplacée**, jamais fusionnée additivement.
- `docs/decisions/defaut-collecte-vs-panne-562.md` — `MOTIFS_PANNE` contre
  `MOTIFS_DEFAUT_COLLECTE` : une source en bonne santé et un code cassé ne se
  publient pas de la même façon, et la preuve d'un défaut se construit
  (`_preuve_defaut_collecte`), elle ne se recopie pas d'un message d'exception.
- `docs/decisions/absences-publiees-comme-faits-556-558-560.md` — pourquoi
  `DECISIONS_PIPELINE` doit connaître toute décision de pipeline (#558), pourquoi
  `MOTIFS_JAMAIS_PANNE` retire l'avarie d'une frontière de source (#560), et ce
  que `legislatures_du_profil` a le droit de dériver de la carrière.

## Le défaut qu'il retire

Une liste vide ne dit rien par elle-même. Mesuré sur les 476 profils publiés au
27/08/2026, le vide est même la norme : `interventions` 469/476,
`tags_thematiques` 469/476, `textes_portes` 454/476, `amendements` 120/476,
`votes` 21/476, `mandats` 9/476. Ces vides recouvrent quatre situations qui
n'ont rien à voir entre elles — un zéro constaté, un fait sur la personne, une
source qui ne couvre pas la période, et une collecte qui n'a pas eu lieu — et
l'interface n'avait aucun moyen de les distinguer.

Le cas le plus nombreux est celui qu'aucun modèle à trois états n'exprimait :
`generate-data.yml` appliquait `--skip-interventions --skip-dossiers-legislatifs`
**en dur** au job roster, « indépendamment des inputs » (#357). 469 profils sur
476 n'avaient donc pas d'interventions parce que **nous avions choisi de ne pas
les collecter**. Le dire « non collecté » tout court, à côté des vraies pannes,
ferait dire au produit « nous n'avons pas réussi » — le contresens exact que
#539 combat. D'où la `cause`, obligatoire sur `non_collecte` et interdite
ailleurs.

**#657 a retourné la moitié « interventions » de ce constat**, et le repli par
provenance avec (voir l'étape 0 de `deriver`) : le job les collecte désormais,
réduites au thème, quand `collect_interventions` est coché. Publier
`non_collecte`/`par_decision` sur une liste PLEINE, sous une preuve nommant un
drapeau que le run n'a pas passé, serait le même contresens à l'envers.

## La règle qui gouverne tout le module

**La condition porte sur la santé de la source, jamais sur l'absence de
résultat.** C'est ce qui a manqué à #484 : un échec réseau a produit un vide, et
le vide a été traité comme une donnée — `jean-luc-melenchon` a basculé au Sénat.

Conséquence directe, et contre-intuitive : `WARNING_PREFIX_VOTES_INTROUVABLES`
n'est **pas** un signal de panne. Le même préfixe couvre deux faits opposés dans
`candidate_profile` — « index des scrutins indisponible » (une panne, l. 1208)
et « aucune correspondance officielle AN n'a été trouvée » (un constat, l. 4766).
Seuls les **motifs** de `MOTIFS_PANNE` ci-dessous, qui nomment une source qui
n'a pas répondu, font basculer une liste en `non_collecte`/`panne`.

Corollaire ajouté par #562 : une source en bonne santé et un code cassé sont eux
aussi deux faits différents. `'<' not supported between instances of 'dict' and
'str'` a été publié comme **preuve de panne** sur 99 profils sur 481, alors
qu'aucune source n'était en défaut. `MOTIFS_DEFAUT_COLLECTE` sépare ce cas, et
sa preuve n'est jamais recopiée d'un message d'exception : elle est construite.

Corollaire ajouté par #558 : une décision de pipeline dont la table n'a pas
d'entrée n'est pas une décision **absente**, c'est une décision publiée comme un
**fait**. `DECISIONS_PIPELINE` ne connaissait que les deux drapeaux de #357 ; le
gel d'un groupe (`extraction_suspendue`, #516) n'y figurait pas, donc les 20
membres des deux fiches `groupe-Senat-*` retombaient sur le défaut — « couvert »,
borné par le référentiel — alors que rien n'avait été demandé à aucune source
pour eux. « Couvert depuis 2002, zéro mandat » se lit « cette personne n'a pas
de mandat », et c'est faux.

Corollaire ajouté par #560 : une **frontière de source** n'est pas une avarie.
Publier `panne` là où nos archives ne remontent simplement pas assez loin fait
porter à la donnée un défaut qui n'existe pas, et laisse croire qu'un prochain
run comblera le silence. Voir l'étape 1ter de `deriver`.

## La forme à deux entrées, et pourquoi elle est la forme générale

Chaque liste collectée porte **deux** entrées : ce que la source couvre, et ce
qu'elle ne couvre pas. Elle ne dépend d'aucune connaissance de la carrière de la
personne — donc elle est publiable pour les 9 profils dont les cinq listes sont
déjà vides et dont `mandats` est vide aussi (`eric-dolige`, `charles-guene`,
`thierry-cozic`…), où toute dérivation par mandats serait muette.

#560 ajoute une dérivation qui, elle, LIT la carrière (`legislatures_du_profil`)
— mais elle ne remplace pas la forme générale, elle s'y ajoute **sous
condition** : elle ne s'arme que si les mandats du profil sont connus et datés,
et se tait sinon. La forme à deux entrées reste donc le cas par défaut, y
compris pour les neuf profils ci-dessus.

Elle dit exactement ce qui est vrai : « dans la fenêtre couverte, le compte
publié est ce que la source contient ; avant, nous ne couvrons pas ». Le mandat
de XIIe législature de Ségolène Royal tombe dans la seconde entrée, et c'est
tout ce que le produit a le droit d'en dire.

Un cinquième état `partielle` — celui de `couverture_dossiers.py` (#399) — n'est
volontairement pas repris : deux entrées disent la même chose **plus** l'endroit
où passe la frontière.

## Ce que le module ne fait pas

Il ne dérive **jamais** « jamais élu·e » pour le Sénat ni pour le Parlement
européen : aucun référentiel dont la complétude soit prouvable n'existe pour ces
chambres. Ces deux faits restent exclusivement humains — voir
`etablir_fait_hors_an`.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Iterable, NamedTuple, Optional

from groupes_config import CLE_SUSPENSION, libelle_groupe
from population_profils import PROVENANCES_ROSTER
from schema_pivot import (
    CAUSE_DEFAUT_COLLECTE,
    CAUSE_PANNE,
    CAUSE_PAR_DECISION,
    ETAT_COUVERT,
    ETAT_FAIT_ETABLI,
    ETAT_HORS_COUVERTURE,
    ETAT_NON_COLLECTE,
    LISTES_COUVERTES,
    valider_couverture,
)
from scrutins_legislature import LEGISLATURES_AN

# ---------------------------------------------------------------------------
# Calendrier
# ---------------------------------------------------------------------------

# Ouverture de chaque législature, de la XIe à la XVIIe. Les quatre dernières
# ne sont PAS recopiées : elles sont vérifiées contre `LEGISLATURES_AN`
# (`scrutins_legislature`, la table qui résout la législature d'un scrutin) par
# `_verifier_calendrier()`, appelée à l'import. Deux copies d'une même borne
# divergent en silence — c'est l'argument qui a fait écarter le patron de #399
# côté UI (`GOVERNMENT_TEXTS_COVERAGE_START` dupliquant la constante Python).
#
# Les trois plus anciennes n'ont pas d'autre porteur dans le dépôt : le
# calendrier de `scrutins_legislature` s'arrête à la XIVe parce que c'est la
# borne des archives de scrutins, et l'étendre là-bas changerait la résolution
# d'un scrutin (une date de 2005 y résoudrait au lieu d'échouer). Elles vivent
# donc ici, où elles ne servent qu'à borner une couverture.
CALENDRIER_LEGISLATURES: dict[int, tuple[str, Optional[str]]] = {
    11: ("1997-06-12", "2002-06-18"),
    12: ("2002-06-19", "2007-06-19"),
    13: ("2007-06-20", "2012-06-19"),
    14: ("2012-06-20", "2017-06-20"),
    15: ("2017-06-21", "2022-06-21"),
    16: ("2022-06-22", "2024-06-09"),
    17: ("2024-07-18", None),
}


def _verifier_calendrier() -> None:
    """Refuse une divergence avec `LEGISLATURES_AN` plutôt que de la subir."""
    for legislature, bornes in LEGISLATURES_AN.items():
        ici = CALENDRIER_LEGISLATURES.get(int(legislature))
        if ici is None:
            raise ValueError(
                f"législature {legislature} connue de scrutins_legislature mais "
                "absente de CALENDRIER_LEGISLATURES : les deux tables doivent "
                "couvrir au moins le même intervalle."
            )
        if ici != bornes:
            raise ValueError(
                f"législature {legislature} : CALENDRIER_LEGISLATURES dit {ici}, "
                f"scrutins_legislature.LEGISLATURES_AN dit {bornes}. Une borne "
                "d'archive ne peut pas avoir deux valeurs."
            )


_verifier_calendrier()


# ---------------------------------------------------------------------------
# Bornes réelles de chaque source
# ---------------------------------------------------------------------------

class Borne(NamedTuple):
    """Ce qu'une source couvre, et la preuve de cette borne.

    La `preuve` se lit dans cet ordre, et l'ordre est le correctif de #560 :
    **d'abord ce que la source publie, ensuite la constante du dépôt**.

    Avant, une preuve disait « `candidate_profile.AN_SCRUTINS_LEGISLATURES = 17,
    16, 15, 14` — 17 748 scrutins ingérés ». Elle décrivait donc **notre
    ingestion**, ce qui se lit comme un choix de notre part, révisable au
    prochain run. La phrase juste est « l'Assemblée nationale ne publie pas de
    scrutins avant la XIVe » : une limite de la source, que rien de ce que nous
    ferons ne déplacera.

    Pour une page comme celle de Ségolène Royal, la différence n'est pas
    cosmétique — l'une suggère qu'on pourrait collecter davantage, l'autre dit
    qu'on ne le pourra jamais. Et AGENTS.md §2.2 demande qu'un fait renvoie à sa
    source primaire : une constante du code n'est la source que de notre
    configuration. Elle reste nommée, en second, comme **trace
    d'implémentation** — c'est elle qui rend l'entrée vérifiable en relecture, et
    c'est sur elle que porte
    `test_couverture_profil_539.test_la_borne_publiee_suit_la_constante_qui_la_porte`.
    """

    #: Législatures réellement ingérées, croissantes.
    legislatures: tuple[int, ...]
    #: Ce que la source PUBLIE, vérifié à la source, avec la date de vérification.
    limite_source: str
    #: La constante du dépôt qui porte la borne, et sa mesure.
    constante: str

    @property
    def preuve(self) -> str:
        """La limite de la source d'abord, la constante du dépôt ensuite."""
        return f"{self.limite_source} — borne portée par {self.constante}"

    @property
    def debut(self) -> str:
        """Ouverture de la plus ancienne législature ingérée."""
        return CALENDRIER_LEGISLATURES[self.legislatures[0]][0]

    @property
    def veille(self) -> str:
        """Veille de `debut` : la fin de ce que la source **ne** couvre pas."""
        return (date.fromisoformat(self.debut) - timedelta(days=1)).isoformat()


# Une entrée par liste métier. Chaque `constante` NOMME la constante du dépôt qui
# porte la borne : c'est ce qui rend l'entrée relisible, et ce qui fait tomber le
# test `test_couverture_profil.py` le jour où une archive est ajoutée sans que la
# couverture publiée le dise.
#
# Les `limite_source` ont été vérifiées le 28/08/2026 sur le portail open data de
# l'Assemblée nationale (#560) : la page « archives antérieures » ne liste que la
# XVe et la XIVe, et celle de la XIVe porte amendements, dossiers, scrutins,
# questions et agendas — **pas de comptes rendus de séance**. Interrogée
# explicitement sur les XIIe et XIIIe : aucun jeu de données. Seuls l'état civil
# et les mandats remontent plus loin, à la XIe (juin 1997) — c'est l'exception qui
# explique qu'un profil publie légitimement 11 mandats et zéro vote.
BORNES: dict[str, Borne] = {
    # AMO30 est un référentiel HISTORIQUE, pas un roster : sa borne n'est pas
    # celle des autres. Et **« acteur » n'y veut pas dire « député »** — mesuré
    # le 12/09/2026 sur `.cache/acteurs_historique_an/` : 3 117 acteurs, dont
    # **2 122** ont siégé à l'Assemblée, **905 sont des sénateurs qui n'y ont
    # jamais siégé**, et 90 n'ont qu'une fonction gouvernementale.
    #
    # La distinction n'est pas de forme : le fichier porte des mandats bien
    # antérieurs à 2002, mais ce sont des organes du **Sénat** — le plus ancien
    # est un groupe du Sénat du **02/10/1980**, et 192 mandats `SENAT`, 123
    # `COMSENAT`, 75 `GROUPESENAT` commencent avant le 19/06/2002. Le plus ancien
    # mandat `ASSEMBLEE`, lui, est bien du **19/06/2002**, l'ouverture de la XIIe.
    #
    # La phrase publiée disait « aucun acteur à un mandat antérieur à la XIIe » :
    # juste dans son esprit, fausse dans sa lettre, sur un texte que le lecteur
    # voit (2 337 entrées de couverture). Elle dit désormais ce que la mesure
    # établit : aucun mandat **de député**. La borne prouvable reste la XIIe, pas
    # la XIe que nomme l'URL de l'archive — c'est la condition C1, sans laquelle
    # la phrase publiable n'est pas « jamais élue » mais « jamais élue depuis la
    # XIIe ».
    "mandats": Borne(
        legislatures=(12, 13, 14, 15, 16, 17),
        limite_source=(
            "l'Assemblée nationale publie l'état civil et les mandats de ses "
            "élu·es depuis la XIe législature (juin 1997), mais son référentiel "
            "historique AMO30 ne rattache aucun mandat de député antérieur à "
            "la XIIe"
        ),
        constante=(
            "AMO30 (référentiel historique des acteurs AN) — mesuré le 12/09/2026 : "
            "3 117 acteurs, dont 2 122 ayant siégé à l'Assemblée ; plus ancien "
            "mandat de député 2002-06-19 (XIIe), les organes du Sénat que le "
            "référentiel porte remontant à 1980 et restant hors périmètre (#528)"
        ),
    ),
    "votes": Borne(
        legislatures=(14, 15, 16, 17),
        limite_source=(
            "l'Assemblée nationale ne publie pas de scrutins avant la XIVe "
            "législature — vérifié le 28/08/2026 sur data.assemblee-nationale.fr, "
            "dont la page d'archives ne remonte pas au-delà"
        ),
        constante=(
            "candidate_profile.AN_SCRUTINS_LEGISLATURES = 17, 16, 15, 14 — "
            "17 748 scrutins ingérés (792 / 4 417 / 4 105 / 8 434)"
        ),
    ),
    "amendements": Borne(
        legislatures=(14, 15, 16, 17),
        limite_source=(
            "l'Assemblée nationale ne publie pas d'amendements avant la XIVe "
            "législature — vérifié le 28/08/2026 sur data.assemblee-nationale.fr, "
            "dont la page d'archives ne remonte pas au-delà"
        ),
        constante=(
            "candidate_profile.AN_AMENDEMENTS_PATH = 14, 15, 16, 17 — un shard "
            "pivot_data/amendements/<legislature>.json par législature ingérée"
        ),
    ),
    "textes_portes": Borne(
        legislatures=(14, 15, 16, 17),
        limite_source=(
            "l'Assemblée nationale ne publie pas d'archive de dossiers avant la "
            "XIVe : les index 12 et 13 répondent 404, revérifié le 18/09/2026. "
            "La XIVe est ingérée depuis #1019 — sa structure est monolithique, "
            "non incompatible, ce que la rédaction précédente affirmait à tort"
        ),
        constante=(
            "couverture_dossiers.AN_DOSSIERS_ARCHIVES = XIV, XV, XVI, XVII"
        ),
    ),
    "interventions": Borne(
        legislatures=(15, 16, 17),
        limite_source=(
            "l'Assemblée nationale ne publie pas de comptes rendus de séance "
            "(Syceron) avant la XVe législature — vérifié le 28/08/2026 sur "
            "data.assemblee-nationale.fr : la page d'archives de la XIVe porte "
            "amendements, dossiers, scrutins, questions et agendas, mais aucun "
            "compte rendu"
        ),
        constante="syceron_debates.SYCERON_AVAILABLE_LEGISLATURES = {15, 16, 17}",
    ),
}

assert set(BORNES) == set(LISTES_COUVERTES), (
    "chaque liste métier porte sa borne : BORNES et LISTES_COUVERTES ne peuvent "
    "pas diverger."
)


# ---------------------------------------------------------------------------
# Décisions de pipeline
# ---------------------------------------------------------------------------

#: Nom de la décision « le groupe parlementaire de ce profil est gelé » (#558).
#: Elle est à part des deux autres : sa portée est **les cinq listes**, et sa
#: preuve n'est pas connue de ce module — elle est lue dans le bloc
#: `extraction_suspendue` du groupe (voir `GroupeSuspendu`).
DECISION_GROUPE_SUSPENDU = "groupe_suspendu"

#: Décision de pipeline → (listes métier qu'elle écarte, preuve).
#: La preuve d'une décision est la DÉCISION, pas une URL : elle nomme le drapeau
#: et l'issue qui l'a posé.
#:
#: Le second membre était une liste **unique** jusqu'à #558 ; il est devenu un
#: tuple parce qu'une décision peut parfaitement écarter les cinq listes d'un
#: coup. La forme précédente n'était pas seulement étroite : elle rendait
#: `groupe_suspendu` inexprimable, et une décision inexprimable retombe sur le
#: défaut — « couvert ». C'est ce qu'ont publié 20 profils de sénateurs, sur des
#: listes vides que le gel de leur groupe explique entièrement.
DECISIONS_PIPELINE: dict[str, tuple[tuple[str, ...], str]] = {
    "skip_interventions": (
        ("interventions",),
        # #657 : le drapeau n'est plus posé EN DUR — il suit `collect_interventions`,
        # et quand il est levé la collecte est réduite au thème. La preuve dit
        # donc ce qui est vrai du run qui a écrit le profil, sans affirmer une
        # politique permanente que le workflow ne porte plus.
        "--skip-interventions appliqué au job extract-roster-groupes par le run "
        "qui a produit ce profil (#357 ; depuis #657 le drapeau suit l'input "
        "collect_interventions au lieu d'être posé en dur)",
    ),
    "skip_dossiers_legislatifs": (
        ("textes_portes",),
        "generate-data.yml:1641 — --skip-dossiers-legislatifs appliqué en dur au "
        "job extract-roster-groupes, indépendamment des inputs (#357)",
    ),
    DECISION_GROUPE_SUSPENDU: (
        tuple(LISTES_COUVERTES),
        "groupes_config.CLE_SUSPENSION — l'extraction du groupe parlementaire de "
        "ce profil est suspendue (#516), et le Sénat est hors périmètre éditorial "
        "depuis #528 : aucune des cinq listes n'a été demandée à une source",
    ),
}

#: Politique appliquée à tout profil d'une provenance de `PROVENANCES_ROSTER`
#: — `roster_groupe`, et `roster_gouvernement` depuis #996 lot 3 : le job qui
#: les produit porte les deux drapeaux **en dur**, donc la décision se lit sur la
#: provenance seule, sans avoir à rejouer le run. C'est ce qui rend la couverture
#: dérivable sur les profils déjà publiés, dont les plus anciens ne portent
#: aucune trace des drapeaux du run qui les a écrits.
#:
#: `groupe_suspendu` n'y est **pas**, et c'est délibéré : la provenance ne
#: recouvre pas la population. Sur les 20 membres des deux fiches
#: `groupe-Senat-*`, 19 sont `roster_groupe` et le vingtième — `bruno-retailleau`,
#: le plus visible des vingt — est `candidat_declare`. Un correctif branché sur
#: la provenance seule l'aurait manqué. L'appartenance se lit donc au groupe, pas
#: au profil : voir `groupes_config.index_membres_de_groupes_suspendus`.
DECISIONS_ROSTER: tuple[str, ...] = ("skip_interventions", "skip_dossiers_legislatifs")


class GroupeSuspendu(NamedTuple):
    """Le gel d'extraction d'un groupe, tel que sa config le documente (#558).

    La preuve est **lue** dans `raw_data/groupes_reels.json`, jamais codée en
    dur ici : les quatre champs de `groupes_config.CHAMPS_SUSPENSION_REQUIS` sont
    exigés justement pour qu'une suspension soit relisible, et une preuve qui les
    recopierait à la main divergerait le jour où la suspension est levée.
    """

    #: `groupe_id` de la config (ex. `"Senat:LR"`).
    groupe_id: str
    #: Date de la suspension (`extraction_suspendue.depuis`).
    depuis: Optional[str] = None
    #: Motif écrit (`extraction_suspendue.motif`).
    motif: Optional[str] = None
    #: Références (`extraction_suspendue.references`), déjà mises en forme.
    references: Optional[str] = None

    @property
    def preuve(self) -> str:
        """Preuve publiable : le motif d'abord, puis la décision et sa date.

        ## Pourquoi le motif passe en tête (#885)

        La preuve s'ouvrait sur « extraction du groupe Senat:LR suspendue depuis
        le 2026-08-24 ». Un lecteur y trouvait donc, en premier, un **incident
        technique daté** — un certificat expiré en août — là où la vraie raison
        est que `data.senat.fr` ne publie ni scrutin ni compte rendu. La panne
        n'est pas la cause : elle est un épisode d'une décision éditoriale qui
        la précède (#528) et qu'un lot ultérieur a rouverte à moitié (#885).

        L'ordre n'est pas de la présentation. C'est lui qui décidait de ce que
        la phrase affirmait, et c'est à ce titre que la propriétaire l'a
        arbitré le 14/09/2026, sur trois formulations rendues côte à côte.

        Le `groupe_id` et la date restent publiés — ils rattachent la phrase à
        une entrée de configuration vérifiable (§2 règle 2) — mais **après** ce
        qu'ils expliquent.
        """
        morceaux = []
        if self.motif:
            morceaux.append(str(self.motif))
        morceaux.append(
            f"extraction du groupe {self.groupe_id} suspendue"
            + (f" depuis le {self.depuis}" if self.depuis else "")
        )
        if self.references:
            morceaux.append(f"références : {self.references}")
        return (
            " — ".join(morceaux)
            + ". Aucune des cinq listes n'a été demandée à une source pour ce "
            "profil : ce vide est une décision, pas un constat."
        )


def groupe_suspendu_depuis_config(groupe: dict[str, Any]) -> GroupeSuspendu:
    """Construit un `GroupeSuspendu` depuis une entrée de `groupes_reels.json`.

    Tolérante par construction : une suspension mal documentée est déjà une
    erreur dure du quality gate (`groupes_config.anomalies_suspension`), et ce
    n'est pas ici qu'on la redécouvre. Ce qui manque manque, et la preuve le dit
    en creux plutôt que d'inventer.
    """
    bloc = groupe.get(CLE_SUSPENSION)
    bloc = bloc if isinstance(bloc, dict) else {}
    references = bloc.get("references") or []
    if isinstance(references, str):
        references = [references]
    return GroupeSuspendu(
        groupe_id=libelle_groupe(groupe),
        depuis=bloc.get("depuis") or None,
        motif=bloc.get("motif") or None,
        references=", ".join(str(r) for r in references) or None,
    )


# ---------------------------------------------------------------------------
# Pannes
# ---------------------------------------------------------------------------

#: Motifs de `meta.warnings[]` qui nomment une SOURCE QUI N'A PAS RÉPONDU, et la
#: liste qu'ils condamnent. Fermé, et volontairement étroit : le critère est la
#: santé de la source, jamais l'absence de résultat.
#:
#: Ce qui n'y est PAS, et pourquoi :
#: - « mandats introuvables : aucun mandat trouvé dans le référentiel officiel »
#:   (`candidate_profile:4679`) est un **constat** de l'AN, pas une panne ;
#: - « votes introuvables : aucune correspondance officielle AN n'a été trouvée »
#:   (`:4766`) aussi — alors que « votes introuvables (législature N) : index des
#:   scrutins indisponible » (`:1208`), sous le **même préfixe**, est une panne.
#:   C'est pourquoi la table est indexée par motif et non par préfixe : traiter
#:   le préfixe comme un signal produirait #484 à l'identique, en publiant
#:   « jamais élu » sur une panne réseau.
#:
#: `interventions syceron indisponibles` y reste, et c'est correct depuis #560 :
#: le préfixe a été SCINDÉ, et seule la branche `except` l'écrit désormais. Le
#: constat qui le portait aussi a son propre préfixe — mais le corpus déjà
#: committé porte encore l'ancien message, d'où `MOTIFS_JAMAIS_PANNE` ci-dessous.
MOTIFS_PANNE: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("index des scrutins indisponible", ("votes",)),
    ("cache d'index des scrutins illisible", ("votes",)),
    ("amendements indisponibles", ("amendements",)),
    ("questions indisponibles", ("interventions",)),
    ("interventions syceron indisponibles", ("interventions",)),
    ("collecte d'interventions tronquée", ("interventions",)),
    ("collecte tronquée (budget de temps)", tuple(LISTES_COUVERTES)),
    ("textes portés officiels (Assemblée nationale) indisponibles", ("textes_portes",)),
    ("chambre en échec", tuple(LISTES_COUVERTES)),
)

#: Motifs qui INTERDISENT de lire un warning comme une panne, même quand il
#: porte par ailleurs un préfixe de `MOTIFS_PANNE` (#560).
#:
#: Une seule entrée, et elle est un **pont vers le corpus déjà publié**. Le
#: constat « les archives ont répondu, elles ne portent rien pour cet acteurRef »
#: a son propre préfixe depuis #560
#: (`WARNING_PREFIX_INTERVENTIONS_SYCERON_AUCUNE`) ; mais les 481 profils bruts
#: committés portent encore l'ancien message, écrit sous le préfixe de panne. La
#: passe pivot les relit à chaque run, et sans cette table elle republierait
#: « panne » sur un zéro constaté jusqu'à la prochaine collecte complète.
#:
#: Ce n'est pas un contournement du préfixe : c'est la reconnaissance d'une
#: phrase qui dit explicitement que la source A répondu. Le critère reste le
#: même — la santé de la source, jamais l'absence de résultat.
MOTIFS_JAMAIS_PANNE: tuple[str, ...] = (
    "aucune intervention syceron pour cet acteurref",
)

#: Motifs de `meta.warnings[]` qui nomment un défaut de CE DÉPÔT, et la liste
#: qu'ils condamnent (#562). Dérivés de `LISTES_COUVERTES` plutôt que recopiés :
#: deux expressions du même invariant divergent en silence.
#:
#: Ils sont volontairement HORS de `MOTIFS_PANNE` : la table au-dessus dit « la
#: source n'a pas répondu », et une anomalie de notre code n'a jamais rien dit
#: de la source. `candidate_profile._tracer_echec_collecte` écrit l'un ou
#: l'autre, jamais les deux pour une même exception.
MOTIFS_DEFAUT_COLLECTE: tuple[tuple[str, tuple[str, ...]], ...] = tuple(
    (f"défaut de collecte interne ({liste})", (liste,)) for liste in LISTES_COUVERTES
)

#: Nombre d'acteurs attendus dans AMO30 (condition C1). En **dessous** de ce
#: plancher, le référentiel n'est pas prouvé chargé et aucun « jamais élu·e » ne
#: peut en être dérivé : l'état retombe sur `non_collecte`/`panne`. Mesuré à
#: 3 117 le 28/08/2026 ; le plancher est délibérément plus bas, un référentiel
#: historique ne pouvant que croître, et délibérément non nul — c'est un
#: référentiel à moitié lu, pas un référentiel vide, qui produit #484.
ACTEURS_AN_PLANCHER = 3_000
ACTEURS_AN_MESURE = 3_117


class SanteReferentiel(NamedTuple):
    """État du référentiel AMO30 pour ce run (condition C1)."""

    #: Nombre d'acteurs effectivement lus, ou `None` si personne ne l'a mesuré.
    nb_acteurs: Optional[int] = None

    @property
    def prouve_charge(self) -> bool:
        return self.nb_acteurs is not None and self.nb_acteurs >= ACTEURS_AN_PLANCHER

    @property
    def preuve(self) -> str:
        if self.nb_acteurs is None:
            return "référentiel AMO30 non mesuré ce run"
        return (
            f"référentiel AMO30 : {self.nb_acteurs} acteurs lus "
            f"(plancher {ACTEURS_AN_PLANCHER}, mesure de référence {ACTEURS_AN_MESURE})"
        )


# ---------------------------------------------------------------------------
# Fait établi — « jamais élu·e à l'Assemblée nationale »
# ---------------------------------------------------------------------------

class FaitHorsAn(NamedTuple):
    """Verdict de `etablir_fait_hors_an`."""

    #: `True` = la personne n'a jamais été élue à l'AN dans la fenêtre couverte.
    etabli: bool
    #: `True` si le verdict vient d'une déclaration humaine (motif + preuve
    #: relus) plutôt que d'une dérivation. C5 : elle prime toujours.
    humain: bool
    #: Preuve publiable.
    preuve: str
    #: Renseigné quand rien ne peut être établi : la panne à publier à la place.
    panne: Optional[str] = None


def etablir_fait_hors_an(
    entree_correspondance: Optional[dict[str, Any]],
    sante: SanteReferentiel = SanteReferentiel(),
) -> Optional[FaitHorsAn]:
    """« Jamais élu·e à l'Assemblée nationale » — les cinq conditions, en code.

    Portée : **l'Assemblée nationale uniquement**. AMO30 est un référentiel
    historique dont la complétude est mesurable ; ni le Sénat ni le Parlement
    européen n'ont d'équivalent dont la complétude soit prouvable, donc « jamais
    élu·e au Sénat » reste exclusivement humain. Dériver sans référentiel
    rendrait un « fait établi » là où nous n'avons qu'une absence de couverture.

    - **C1** — le référentiel doit être *prouvé chargé* (`sante`). En dessous du
      plancher, on ne dérive rien : on rend une panne.
    - **C2** — l'appariement se fait sur l'état civil complet, jamais sur le nom
      seul. C'est le travail de `raw_data/correspondance_acteurs_an.json`, qui
      stocke `etat_civil` avec la correspondance ; ce module lit son verdict.
    - **C3** — pas de date de naissance ⇒ pas de dérivation. Le cas Bardella,
      dont la date est `null` dans la table : sans état civil, un humain déclare
      avec un motif, et c'est C5 qui répond.
    - **C4** — rien n'est figé : le verdict est recalculé à chaque appel, depuis
      la table et la santé du run. L'immuabilité porte sur l'identifiant, jamais
      sur le fait.
    - **C5** — une déclaration humaine (`ecart: "hors_an"` + motif + preuve)
      prime toujours, y compris sur un référentiel en panne.

    Returns:
        `None` si la question ne se pose pas (la personne A un acteur AN, ou
        aucune entrée ne la décrit) ; un `FaitHorsAn` sinon.
    """
    if not isinstance(entree_correspondance, dict):
        return None

    acteur_ref = entree_correspondance.get("acteur_ref")
    if acteur_ref:
        # La personne EST un acteur AN : la question ne se pose pas.
        return None

    # C5 — la déclaration humaine prime, et elle prime aussi sur une panne.
    if entree_correspondance.get("ecart") == "hors_an":
        motif = (entree_correspondance.get("motif") or "").strip()
        preuve = (entree_correspondance.get("preuve") or "").strip()
        verifie_le = entree_correspondance.get("verifie_le") or ""
        if motif and preuve:
            return FaitHorsAn(
                etabli=True,
                humain=True,
                preuve=(
                    "raw_data/correspondance_acteurs_an.json — absence déclarée "
                    f"(ecart 'hors_an', vérifiée le {verifie_le}) : {preuve}"
                ),
            )

    # C1 — sans référentiel prouvé chargé, aucune dérivation. Un référentiel
    # injoignable doit produire « non collecté — panne », jamais « jamais élu ».
    if not sante.prouve_charge:
        return FaitHorsAn(
            etabli=False,
            humain=False,
            preuve=sante.preuve,
            panne=(
                "référentiel AN non prouvé chargé, aucun fait négatif dérivable — "
                f"{sante.preuve}"
            ),
        )

    # C2/C3 — sans état civil complet (date de naissance comprise), pas de
    # dérivation : on retombe sur la déclaration humaine, qui n'existe pas ici.
    etat_civil = entree_correspondance.get("etat_civil") or {}
    if not (etat_civil.get("nom") and etat_civil.get("date_naissance")):
        return FaitHorsAn(
            etabli=False,
            humain=False,
            preuve="état civil incomplet (date de naissance absente)",
            panne=(
                "état civil incomplet dans la table de correspondance : sans date "
                "de naissance, aucun fait négatif n'est dérivable (condition C3)"
            ),
        )

    return FaitHorsAn(
        etabli=True,
        humain=False,
        preuve=(
            f"{sante.preuve} — aucun acteur AMO30 pour "
            f"{etat_civil.get('nom_complet') or etat_civil.get('nom')} "
            f"(né·e le {etat_civil.get('date_naissance')})"
        ),
    )


# ---------------------------------------------------------------------------
# Dérivation
# ---------------------------------------------------------------------------

def _entree(
    etat: str,
    preuve: str,
    constate_le: str,
    *,
    cause: Optional[str] = None,
    portee: Optional[dict[str, Any]] = None,
    source: Optional[str] = None,
) -> dict[str, Any]:
    """Une entrée de couverture, clés dans un ordre stable (git le lit).

    `source` (#683) nomme l'institution dont l'entrée décrit la couverture. Il
    est **facultatif et son absence signifie « Assemblée nationale »**, ce qui
    est le cas de 100 % des entrées écrites avant ce champ — l'écrire partout
    aurait été un backfill sans fait nouveau. Il n'est pas décoratif : c'est lui
    que `merge_profile._sources_couvertes` lit pour départager deux écrivains
    dont l'un a interrogé une source que l'autre n'a pas interrogée.
    """
    entree: dict[str, Any] = {"etat": etat}
    if cause is not None:
        entree["cause"] = cause
    if source is not None:
        entree["source"] = source
    if portee is not None:
        entree["portee"] = portee
    entree["preuve"] = preuve
    entree["constate_le"] = constate_le
    return entree


def _preuve_defaut_collecte(liste: str) -> str:
    """La preuve d'un défaut interne — **construite**, jamais recopiée.

    C'est la règle qui répare #562 à la racine : le message de l'exception reste
    dans `meta.warnings` (canal technique) et sur la sortie d'erreur du run, et
    n'entre JAMAIS dans `preuve`. Ce que le champ publie ici est le seul fait
    vrai et vérifiable : la collecte de cette liste n'a pas abouti, et la cause
    est chez nous. Un lecteur y trouve ce qu'il peut en faire — ne rien conclure
    de ce vide, et surtout rien conclure sur l'Assemblée nationale.
    """
    return (
        f"défaut de collecte interne du dépôt sur « {liste} » : la collecte n'a "
        "pas abouti pour une anomalie qui nous est propre, aucune source de "
        "l'Assemblée nationale n'est en cause. Le détail technique est consigné "
        "dans meta.warnings et au journal de run, pas dans ce champ (#562)."
    )


def _defauts_declares(warnings: Iterable[Any]) -> set[str]:
    """Listes condamnées par un défaut de collecte interne (#562).

    Renvoie les seules listes, pas les warnings : la preuve est construite
    (`_preuve_defaut_collecte`), justement pour qu'aucun texte d'exception ne
    puisse remonter jusqu'au champ publié.
    """
    defauts: set[str] = set()
    for warning in warnings or ():
        if not isinstance(warning, str):
            continue
        minuscule = warning.lower()
        for motif, listes in MOTIFS_DEFAUT_COLLECTE:
            if motif.lower() in minuscule:
                defauts.update(listes)
    return defauts


def _pannes_declarees(warnings: Iterable[Any]) -> dict[str, str]:
    """Listes condamnées par une panne, avec le warning qui l'établit.

    Seuls les motifs de `MOTIFS_PANNE` comptent : ils nomment une source qui
    n'a pas répondu. Une absence de résultat n'en est pas une.
    """
    pannes: dict[str, str] = {}
    for warning in warnings or ():
        if not isinstance(warning, str):
            continue
        minuscule = warning.lower()
        if any(motif in minuscule for motif in MOTIFS_JAMAIS_PANNE):
            continue
        for motif, listes in MOTIFS_PANNE:
            if motif.lower() not in minuscule:
                continue
            for liste in listes:
                pannes.setdefault(liste, warning)
    return pannes


# ---------------------------------------------------------------------------
# Les législatures d'un profil
# ---------------------------------------------------------------------------

def legislatures_du_profil(profil: dict[str, Any]) -> tuple[int, ...]:
    """Législatures que les mandats **publiés** du profil recouvrent.

    Rendue **vide quand rien n'est connu**, et c'est la moitié importante du
    contrat : un profil sans mandat daté ne dit rien de sa carrière, donc rien
    ne doit en être dérivé. C'est ce qui préserve la propriété que #539 avait
    obtenue — la couverture reste publiable pour les 9 profils dont `mandats`
    est vide, où toute dérivation par mandats serait muette.

    Un mandat sans `fin` est **en cours** : il court jusqu'à la dernière
    législature du calendrier. Un mandat dont la période déborde le calendrier
    est retenu pour les seules législatures qu'il recoupe réellement.
    """
    mandats = profil.get("mandats")
    if not isinstance(mandats, list):
        return ()

    trouvees: set[int] = set()
    for mandat in mandats:
        if not isinstance(mandat, dict):
            continue
        debut = mandat.get("debut")
        if not isinstance(debut, str) or not debut.strip():
            continue
        fin = mandat.get("fin")
        fin = fin if isinstance(fin, str) and fin.strip() else None
        for legislature, (ouverture, cloture) in CALENDRIER_LEGISLATURES.items():
            # Deux intervalles se recoupent si chacun commence avant que
            # l'autre ne finisse. `None` = pas de fin connue, donc ouvert.
            if cloture is not None and debut > cloture:
                continue
            if fin is not None and fin < ouverture:
                continue
            trouvees.add(legislature)
    return tuple(sorted(trouvees))


def _romain(legislature: int) -> str:
    """`14` → `"XIVe"`. Les preuves publiées nomment les législatures comme
    l'Assemblée les nomme, pas comme le code les indexe."""
    chiffres = (
        (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
    )
    reste, texte = legislature, ""
    for valeur, symbole in chiffres:
        while reste >= valeur:
            texte += symbole
            reste -= valeur
    return f"{texte}e"


#: #683 — L'INSTITUTION QUI A FOURNI UNE ENTRÉE, LUE SUR L'ENTRÉE ELLE-MÊME.
#:
#: Sans cela, un profil européen publiait ses 1 317 votes du Parlement européen
#: sous une couverture qui dit « l'Assemblée nationale ne publie pas de scrutins
#: avant la XIVe législature ». La borne était vraie et ne portait sur rien —
#: une preuve qui parle d'une source dont la liste ne vient pas est une preuve
#: fausse (§2 règle 2).
INSTITUTION_PE = "parlement_europeen"

#: Où l'institution se lit, liste par liste. Deux formes seulement, parce que le
#: schéma en a deux : sur l'entrée pour un texte porté, dans l'enregistrement
#: non résolu pour un vote ou un amendement (#431), dans `source` pour une
#: intervention.
_CHEMINS_INSTITUTION: dict[str, tuple[tuple[str, ...], ...]] = {
    "votes": (("scrutin_non_resolu", "institution"),),
    "amendements": (("amendement_non_resolu", "institution"),),
    "textes_portes": (("institution",),),
    "interventions": (("source", "institution"),),
}

#: Où la date se lit, dans le même ordre de préséance.
_CHEMINS_DATE: dict[str, tuple[tuple[str, ...], ...]] = {
    "votes": (("scrutin_non_resolu", "date"),),
    "amendements": (("amendement_non_resolu", "date"),),
    "textes_portes": (("date_min",), ("date_max",)),
    "interventions": (("date",),),
}


def _lire(entree: Any, chemin: tuple[str, ...]) -> Any:
    for cle in chemin:
        if not isinstance(entree, dict):
            return None
        entree = entree.get(cle)
    return entree


def bornes_europeennes(profil: dict[str, Any]) -> dict[str, tuple[str, str]]:
    """`liste → (première date, dernière date)` du matériau européen publié.

    **Mesurée sur les entrées, jamais recopiée d'une page de source.** La date
    de fraîcheur d'un dump ParlTrack vieillit dès qu'on l'écrit ; la dernière
    date effectivement portée par le corpus, elle, se recalcule à chaque run et
    dit la même chose sans pouvoir mentir — c'est la leçon des constats chiffrés
    recopiés (#484).
    """
    bornes: dict[str, tuple[str, str]] = {}
    for liste, chemins_institution in _CHEMINS_INSTITUTION.items():
        dates: list[str] = []
        for entree in profil.get(liste) or ():
            if not isinstance(entree, dict):
                continue
            if not any(_lire(entree, c) == INSTITUTION_PE for c in chemins_institution):
                continue
            for chemin in _CHEMINS_DATE[liste]:
                valeur = _lire(entree, chemin)
                if isinstance(valeur, str) and valeur:
                    dates.append(valeur)
        if dates:
            bornes[liste] = (min(dates), max(dates))
    return bornes


def _preuve_europeenne(liste: str, fin: str) -> str:
    """La preuve d'une couverture européenne — construite, jamais recopiée."""
    return (
        f"« {liste} » porte aussi du matériau du Parlement européen, collecté via les "
        f"dumps ParlTrack (parltrack.org/dumps, ODbL v1.0) et sourcé sur les documents "
        f"officiels d'europarl.europa.eu. La source ne publie rien au-delà du {fin} "
        f"dans ce corpus : ce qui suit cette date n'est pas absent, il n'est pas encore "
        f"paru chez elle."
    )


def deriver(
    profil: dict[str, Any],
    *,
    constate_le: Optional[str] = None,
    decisions: Optional[Iterable[str]] = None,
    fait_hors_an: Optional[FaitHorsAn] = None,
    groupe_suspendu: Optional[GroupeSuspendu] = None,
) -> dict[str, list[dict[str, Any]]]:
    """Construit le bloc `couverture` d'un profil pivot.

    Args:
        profil: le profil pivot, lu pour `meta.provenance`, `meta.warnings` et
            — depuis #560 — `mandats[]`, dont les dates disent quelles
            législatures la carrière recouvre.
        constate_le: date ISO du constat (défaut : aujourd'hui).
        decisions: drapeaux de `DECISIONS_PIPELINE` appliqués à CE run. `None`
            = déduit de la provenance : un profil `roster_groupe` vient du job
            qui porte les deux drapeaux en dur (#357).
        fait_hors_an: verdict d'`etablir_fait_hors_an`, ou `None` si la question
            ne se pose pas.
        groupe_suspendu: le gel d'extraction du groupe de ce profil (#558), ou
            `None`. Fourni par l'appelant, qui seul connaît l'appartenance —
            elle ne se lit ni sur la provenance ni sur `chambre`.

    Returns:
        `{liste: [entrée, ...]}`, complet sur les cinq listes métier.
    """
    constate_le = constate_le or date.today().isoformat()
    meta = profil.get("meta") if isinstance(profil.get("meta"), dict) else {}
    provenance = meta.get("provenance", "candidat_declare")

    if decisions is None:
        # #657 — LE REPLI PAR PROVENANCE NE VAUT QUE SANS DÉCLARATION DU RUN.
        #
        # `DECISIONS_ROSTER` a été écrit quand le job roster portait
        # `--skip-interventions` EN DUR : la provenance suffisait alors à dire ce
        # que le run avait fait, et c'est ce qui rend la couverture dérivable sur
        # les 19 profils publiés avant #539, qui ne portent aucune trace de leurs
        # drapeaux. Depuis #657 le job peut collecter les interventions (réduites
        # au thème) : le repli publierait alors `non_collecte`/`par_decision` sur
        # une liste PLEINE, sous une preuve qui nomme un drapeau que le run n'a
        # pas passé — le contresens exact que #539 combat, retourné.
        #
        # La condition porte sur la PRÉSENCE de la clé, pas sur son contenu :
        # `collecte_ecartee: []` est une déclaration (« ce run n'a rien écarté »),
        # son absence n'en est pas une. Mesuré au 31/08/2026 : 449 des 468
        # profils `roster_groupe` publiés portent la clé, 19 ne la portent pas.
        run_a_declare = isinstance(meta.get("collecte_ecartee"), list)
        # #996 lot 3 — `PROVENANCES_ROSTER` et non l'égalité à `roster_groupe` :
        # un membre de gouvernement est collecté par les mêmes shards, sous les
        # mêmes drapeaux réduits, donc le repli qui explique ses listes vides
        # est le même. L'égalité l'aurait laissé sans preuve de couverture.
        decisions = (
            DECISIONS_ROSTER
            if provenance in PROVENANCES_ROSTER and not run_a_declare
            else ()
        )
    decisions = tuple(decisions)
    if groupe_suspendu is not None and DECISION_GROUPE_SUSPENDU not in decisions:
        # EN TÊTE, pas à la suite : sur un profil `roster_groupe` d'un groupe
        # gelé, les deux drapeaux de #357 sont vrais aussi, mais ils n'expliquent
        # que deux listes sur cinq. Le gel les englobe, et c'est lui que le
        # lecteur doit trouver en preuve — sur les cinq.
        decisions = (DECISION_GROUPE_SUSPENDU,) + decisions
    ecartees: dict[str, str] = {}
    for drapeau in decisions:
        if drapeau not in DECISIONS_PIPELINE:
            continue
        listes, preuve = DECISIONS_PIPELINE[drapeau]
        # La preuve d'un gel de groupe est celle que le groupe DOCUMENTE : la
        # phrase générique de la table ne sert que si l'appelant n'a pas su
        # dire de quel groupe il s'agit.
        if drapeau == DECISION_GROUPE_SUSPENDU and groupe_suspendu is not None:
            preuve = groupe_suspendu.preuve
        for liste in listes:
            ecartees.setdefault(liste, preuve)
    # `meta.collecte_ecartee` (#539) est la trace écrite PAR LA COLLECTE des
    # listes qu'elle a délibérément sautées. Elle prime sur toute inférence :
    # la passe pivot de la CI est un `--pivot-only` sans drapeau, donc elle ne
    # sait rien du run qui a produit le brut — sauf ce que ce run a consigné.
    for liste in meta.get("collecte_ecartee") or ():
        if liste in LISTES_COUVERTES:
            ecartees.setdefault(
                liste,
                f"collecte écartée par le run qui a produit le profil brut "
                f"(meta.collecte_ecartee, #357) : {liste}",
            )
    pannes = _pannes_declarees(meta.get("warnings") or ())
    defauts = _defauts_declares(meta.get("warnings") or ())
    legislatures = set(legislatures_du_profil(profil))

    couverture: dict[str, list[dict[str, Any]]] = {}
    for liste in LISTES_COUVERTES:
        borne = BORNES[liste]

        # 1. Une décision de pipeline passe avant tout : rien n'a été demandé à
        #    la source, donc ni son périmètre ni sa santé ne disent quoi que ce
        #    soit sur cette liste.
        if liste in ecartees:
            couverture[liste] = [
                _entree(ETAT_NON_COLLECTE, ecartees[liste], constate_le,
                        cause=CAUSE_PAR_DECISION)
            ]
            continue

        # 1ter. Puis la FRONTIÈRE DE SOURCE, avant toute cause (#560).
        #
        #    Si aucune législature du profil n'intersecte ce que la source
        #    publie, il n'y a rien à collecter — et il n'y aura jamais rien. Une
        #    panne survenue par ailleurs ne dit rien de cette liste-là ; un
        #    défaut de notre code non plus. Le seul fait vrai est celui de notre
        #    couverture, et il a son état : `hors_couverture`.
        #
        #    C'est le correctif de fond de #560 : `segolene-royal` publiait
        #    `non_collecte`/`panne` sur ses interventions, sous une preuve qui
        #    avouait son ambiguïté (« identifiant absent des trois archives, OU
        #    archive indisponible »). Son mandat relève de la XIIe et Syceron
        #    commence à la XVe : la panne était fausse **par construction**, et
        #    elle laissait croire qu'un prochain run comblerait le silence.
        #
        #    La condition n'est armée que si `legislatures` est non vide : un
        #    profil dont les mandats sont inconnus ne permet aucune dérivation
        #    (voir `legislatures_du_profil`).
        if legislatures and not legislatures & set(borne.legislatures):
            couverture[liste] = [
                _entree(
                    ETAT_HORS_COUVERTURE,
                    f"{borne.preuve}. Les mandats publiés de ce profil relèvent "
                    f"des législatures "
                    f"{', '.join(_romain(n) for n in sorted(legislatures))} : "
                    "aucune n'est couverte par cette source, et aucun run ne "
                    "peut le changer.",
                    constate_le,
                    portee={"debut": None, "fin": borne.veille},
                )
            ]
            continue

        # 1bis. Puis un défaut de NOTRE code, AVANT la santé de la source
        #    (#562) : quand les deux sont signalés pour la même liste, celui
        #    dont nous sommes sûrs est le nôtre. Publier « panne » à sa place
        #    imputerait à l'Assemblée nationale une faute qui est la nôtre —
        #    c'est ce qu'ont fait 99 profils sur 481.
        if liste in defauts:
            couverture[liste] = [
                _entree(ETAT_NON_COLLECTE, _preuve_defaut_collecte(liste),
                        constate_le, cause=CAUSE_DEFAUT_COLLECTE)
            ]
            continue

        # 2. Puis la santé de la source. Jamais l'absence de résultat.
        if liste in pannes:
            couverture[liste] = [
                _entree(ETAT_NON_COLLECTE, pannes[liste], constate_le,
                        cause=CAUSE_PANNE)
            ]
            continue

        # 3. Un fait négatif non établissable est une panne, pas un fait.
        if fait_hors_an is not None and fait_hors_an.panne:
            couverture[liste] = [
                _entree(ETAT_NON_COLLECTE, fait_hors_an.panne, constate_le,
                        cause=CAUSE_PANNE)
            ]
            continue

        # 4. Le fait établi, borné par ce que le référentiel étaye : « jamais
        #    élue » n'est publiable que dans la fenêtre où AMO30 sait répondre.
        etat_dans_la_fenetre = ETAT_COUVERT
        preuve_dans_la_fenetre = borne.preuve
        if fait_hors_an is not None and fait_hors_an.etabli:
            etat_dans_la_fenetre = ETAT_FAIT_ETABLI
            preuve_dans_la_fenetre = fait_hors_an.preuve

        couverture[liste] = [
            _entree(
                etat_dans_la_fenetre,
                preuve_dans_la_fenetre,
                constate_le,
                portee={"debut": borne.debut, "fin": None},
            ),
            _entree(
                ETAT_HORS_COUVERTURE,
                borne.preuve,
                constate_le,
                portee={"debut": None, "fin": borne.veille},
            ),
        ]

    # #683 — LA PART EUROPÉENNE DIT SA PROPRE BORNE, à côté de celle de
    # l'Assemblée et jamais à sa place. Les deux institutions cohabitent dans
    # une même liste sans se totaliser (§6) ; leurs couvertures cohabitent de
    # la même façon, chacune avec sa portée.
    for liste, (debut, fin) in bornes_europeennes(profil).items():
        couverture.setdefault(liste, []).append(
            _entree(
                ETAT_COUVERT,
                _preuve_europeenne(liste, fin),
                constate_le,
                portee={"debut": debut, "fin": fin},
                source=INSTITUTION_PE,
            )
        )

    return couverture


def appliquer(
    profil: dict[str, Any],
    *,
    constate_le: Optional[str] = None,
    decisions: Optional[Iterable[str]] = None,
    fait_hors_an: Optional[FaitHorsAn] = None,
    groupe_suspendu: Optional[GroupeSuspendu] = None,
) -> dict[str, list[dict[str, Any]]]:
    """Écrit `profil["couverture"]` et le renvoie.

    Refuse bruyamment un bloc non conforme plutôt que de le publier : la
    fabrique se contrôle avec la même règle que le schéma, écrite une fois.
    """
    couverture = deriver(
        profil,
        constate_le=constate_le,
        decisions=decisions,
        fait_hors_an=fait_hors_an,
        groupe_suspendu=groupe_suspendu,
    )
    erreurs = valider_couverture(couverture)
    if erreurs:
        raise ValueError(
            "couverture dérivée non conforme au schéma pivot : "
            + " | ".join(erreurs)
        )
    profil["couverture"] = couverture
    return couverture
