"""Destinataire déclaré d'un avertissement de profil (#642).

`meta.warnings[]` mélangeait deux registres sous un seul champ. Mesuré le
31/08/2026 sur le corpus publié : **52 des 481 profils portent 115
avertissements**, dont 80 s'adressent à nous (compteurs de migration #492/#493,
fraîcheur de `synchro_sources`, pannes de cache) et 35 au lecteur (« votes
introuvables », « mandats introuvables », « aucun mandat français connu »).
Rien ne les partitionnait, donc l'interface ne pouvait ni tout publier — de la
plomberie sur une page publique — ni rien publier — elle perdait les
explications que le lecteur attend. Elle ne publiait rien.

Ce module déclare le destinataire **par avertissement, à l'endroit qui l'écrit**,
et jamais par une table indexée sur le préfixe du message. Ce choix n'est pas
esthétique : `WARNING_PREFIX_VOTES_INTROUVABLES` couvre à la fois un **constat**
(« aucune correspondance officielle Assemblée nationale ») et une **panne**
(« index des scrutins indisponible »), qui ne s'adressent pas à la même
personne. Une table par préfixe reproduirait #484 à l'identique — c'est la
leçon que `couverture_profil.MOTIFS_PANNE` a déjà dû tirer, en s'indexant par
motif plutôt que par préfixe.

Trois pièces, et rien d'autre :

- `DESTINATAIRES_AVERTISSEMENT` — le vocabulaire **fermé**, deux valeurs. Il
  n'y a pas de troisième valeur « mixte » : un avertissement qui s'adresse aux
  deux s'écrit **deux fois**, dans les termes de chaque destinataire (c'est ce
  que fait `normalize_parltrack_dumps` depuis ce lot).
- `avertissement()` — la fabrique. Elle rend une **chaîne** (`Avertissement`
  hérite de `str`), pour que les quelque 60 consommateurs qui font
  `startswith`, `in`, `==` ou `json.dump` sur `meta.warnings[]` continuent de
  fonctionner sans être touchés. Le typage voyage sur l'instance, le long des
  listes, de l'union (#600) et des filtres d'extinction.
- `deriver_avertissements()` — la publication. Elle écrit
  `meta.avertissements[]`, jumeau **typé et aligné** de `meta.warnings[]`, une
  entrée par avertissement, dans le même ordre. C'est un champ **dérivé**, au
  même titre que `chambres` (#493), `licence_donnees` (#530) et
  `provenance_champs` (#603) : recalculé après toute mutation, jamais fusionné.

Le typage porté par l'instance ne survit pas à un aller-retour JSON — un profil
brut relu par la passe pivot ne rend que des `str`. C'est pour cela que
`deriver_avertissements` **relit le bloc déjà présent** dans le même `meta` :
la correspondance s'y fait sur le message **exact**, jamais sur un préfixe. Un
message qu'aucune des deux voies ne type est publié
`{"destinataire": null}` — déclaré inconnu, jamais rangé par défaut d'un côté
(AGENTS.md §2 règle 5, et le même geste que `provenance_champs` pour une source
inconnue).
"""

from __future__ import annotations

from typing import Any, Optional

#: L'avertissement explique au lecteur ce qu'il voit — une liste vide, un bloc
#: absent — et nomme sa source ou sa borne (AGENTS.md §2 règle 2).
DESTINATAIRE_LECTEUR = "lecteur"

#: L'avertissement rend compte de l'état du pipeline à ceux qui le maintiennent :
#: compteur de migration, panne de cache, numéro d'issue, nom de fonction.
DESTINATAIRE_INTERNE = "interne"

#: Vocabulaire fermé, validé par `schema_pivot.valider_avertissements`. Deux
#: valeurs, et il faut résister à en ajouter une troisième : « mixte » rendrait
#: à l'interface le tri qu'elle n'a pas su faire, avec un nom de plus.
DESTINATAIRES_AVERTISSEMENT: frozenset[str] = frozenset({
    DESTINATAIRE_LECTEUR,
    DESTINATAIRE_INTERNE,
})


class Avertissement(str):
    """Un message d'avertissement qui sait à qui il s'adresse.

    Hérite de `str` **exprès** : `meta.warnings[]` reste une liste de chaînes,
    sur le fil comme en mémoire. Les 61 sites d'écriture et l'ensemble des
    consommateurs (`_prune_stale_warnings`, `unir_warnings`,
    `couverture_profil`, `audit_pivot_dataset`, le portail de qualité) n'ont
    rien à changer, et aucun texte publié ne bouge — la contrainte que #600
    s'était déjà donnée.

    `__reduce__` et `__deepcopy__` sont explicites : sans eux, une copie
    profonde d'un profil perdrait le destinataire **en silence**, ce qui est
    exactement la régression invisible que ce lot existe pour éviter.
    """

    __slots__ = ("destinataire",)

    def __new__(cls, message: str, destinataire: Optional[str]) -> "Avertissement":
        if destinataire is not None and destinataire not in DESTINATAIRES_AVERTISSEMENT:
            raise ValueError(
                f"destinataire d'avertissement inconnu : {destinataire!r}. "
                f"Valeurs connues : {sorted(DESTINATAIRES_AVERTISSEMENT)}."
            )
        instance = super().__new__(cls, message)
        instance.destinataire = destinataire
        return instance

    def __reduce__(self):
        return (Avertissement, (str(self), self.destinataire))

    def __copy__(self) -> "Avertissement":
        return Avertissement(str(self), self.destinataire)

    def __deepcopy__(self, memo: dict) -> "Avertissement":
        return Avertissement(str(self), self.destinataire)


def avertissement(message: str, destinataire: str) -> Avertissement:
    """Fabrique unique d'un avertissement typé.

    `destinataire` est **obligatoire** : il n'y a pas de valeur par défaut, et
    c'est le point du lot. Un site d'écriture qui ne sait pas à qui il parle
    doit le décider, pas hériter d'un choix pris ailleurs.
    """
    if destinataire not in DESTINATAIRES_AVERTISSEMENT:
        raise ValueError(
            f"destinataire d'avertissement inconnu : {destinataire!r}. "
            f"Valeurs connues : {sorted(DESTINATAIRES_AVERTISSEMENT)}."
        )
    return Avertissement(message, destinataire)


def destinataire_de(entree: Any) -> Optional[str]:
    """Le destinataire d'un avertissement, ou `None` s'il n'en déclare pas.

    Accepte les deux formes qui circulent : l'instance `Avertissement` (en
    mémoire) et l'entrée `{"message", "destinataire"}` de `meta.avertissements`
    (sur le fil). Une chaîne nue rend `None` — ce n'est pas « interne par
    défaut », c'est « personne ne l'a déclaré ».
    """
    if isinstance(entree, Avertissement):
        return entree.destinataire
    if isinstance(entree, dict):
        valeur = entree.get("destinataire")
        return valeur if valeur in DESTINATAIRES_AVERTISSEMENT else None
    return None


#: Avertissements que **plus aucun code n'écrit** mais que le corpus publié
#: porte encore, avec leur destinataire. Table fermée, indexée sur le message
#: **entier** — jamais sur un préfixe, pour la raison donnée en tête de module.
#:
#: C'est un **pont vers le corpus déjà publié**, du même genre que
#: `couverture_profil.MOTIFS_JAMAIS_PANNE`, et pas une seconde façon de typer.
#: **Quatre entrées, 49 des 115 avertissements publiés au 31/08/2026**, toutes
#: écrites avant #529 par un code qui nommait encore NosDéputés. Sans cette
#: table, ces 49-là seraient publiés sans destinataire — c'est-à-dire invisibles
#: à l'interface, l'état exact que #642 corrige.
#:
#: Trois d'entre elles sont d'anciennes formulations de familles encore
#: vivantes : la fusion par famille (#600) finira par les remplacer à la
#: prochaine collecte du profil. La quatrième, `synchro_sources.nosdeputes`,
#: n'est plus écrite du tout — son adaptateur est parti avec la source — et la
#: fusion additive la reconduit indéfiniment depuis les profils bruts committés.
#:
#: Condition de retrait, écrite pour qu'elle ne devienne pas permanente par
#: omission : chaque entrée part le jour où aucun profil publié ne porte plus
#: son message. Le compte se lit avec `audit_pivot_dataset` (agrégation des
#: warnings par type).
AVERTISSEMENTS_HERITES: dict[str, str] = {
    # 19 profils — l'adaptateur ne l'écrit plus depuis #529, mais la phrase
    # publiée dit la même chose que celle d'aujourd'hui, au lecteur.
    "votes introuvables : aucune correspondance officielle Assemblée nationale "
    "n'a été trouvée pour ce parlementaire/cette législature (NosDéputés.fr non "
    "interrogé pour les votes, endpoint en panne systématique — voir "
    "fetch_votes_officiels).": DESTINATAIRE_LECTEUR,
    # 9 profils — idem, ancienne formulation de « mandats introuvables ».
    "mandats introuvables : aucun mandat/responsabilité trouvé "
    "(NosDéputés/NosSénateurs et référentiel officiel Assemblée nationale "
    "confondus).": DESTINATAIRE_LECTEUR,
    # 19 profils — plus aucun code ne l'écrit, et rien ne le réécrira.
    "synchro_sources.nosdeputes : aucune synchro réussie enregistrée dans le "
    "profil source.": DESTINATAIRE_INTERNE,
}

#: Les avertissements hérités qui portent un identifiant variable, donc un
#: **préfixe** et non un message entier. Il n'y en a qu'un, et c'est le message
#: ParlTrack d'avant le dédoublement de #642 : il porte le `MEP ID`.
#:
#: Déroger ici au message entier est sûr **parce que ce préfixe-là ne recouvre
#: qu'un énoncé** — contrairement à `votes introuvables`, qui recouvre un
#: constat ET une panne, et c'est pourquoi la table au-dessus est indexée sur le
#: message. Un préfixe n'entre ici que si l'on peut dire à qui s'adresse *tout*
#: ce qu'il recouvre.
PREFIXES_HERITES: tuple[tuple[str, str], ...] = (
    # 2 profils — l'ancienne phrase mêlait le constat et la consigne de
    # vérification ; c'est sa moitié lecteur qui la résume.
    ("ParlTrack: aucune donnée trouvée pour le MEP ID", DESTINATAIRE_LECTEUR),
)


def _destinataire_herite(message: str) -> Optional[str]:
    """Le destinataire d'un avertissement publié avant #642, ou `None`."""
    direct = AVERTISSEMENTS_HERITES.get(message)
    if direct is not None:
        return direct
    for prefixe, destinataire in PREFIXES_HERITES:
        if message.startswith(prefixe):
            return destinataire
    return None


def _table_deja_publiee(meta: dict[str, Any]) -> dict[str, str]:
    """Message exact → destinataire, lu du bloc `avertissements` déjà présent.

    C'est le pont qui fait survivre le typage à l'aller-retour JSON entre le
    profil brut et la passe pivot, et à la fusion additive. La clé est le
    message **entier** : un préfixe ne dirait pas la même chose (voir l'en-tête
    du module).
    """
    table: dict[str, str] = {}
    for entree in meta.get("avertissements") or ():
        if not isinstance(entree, dict):
            continue
        message = entree.get("message")
        destinataire = entree.get("destinataire")
        if isinstance(message, str) and destinataire in DESTINATAIRES_AVERTISSEMENT:
            table[message] = destinataire
    return table


def deriver_avertissements(meta: Any) -> None:
    """Recompose `meta.avertissements[]` à partir de `meta.warnings[]`.

    À appeler **après toute mutation de `meta.warnings`**, comme
    `appliquer_chambres` après une mutation de `mandats[]` : c'est un champ
    dérivé, jamais fusionné. Le bloc est écrit même vide — sa présence est ce
    qui distingue « ce profil est passé par #642 et n'a rien à dire » de « ce
    profil est antérieur au lot ».

    Ne touche ni à `meta.warnings` ni aux textes : l'ordre et les chaînes sont
    ceux de `warnings`, à l'identique, et `valider_avertissements` le vérifie.
    """
    if not isinstance(meta, dict):
        return
    warnings = meta.get("warnings")
    if not isinstance(warnings, list):
        return
    deja_publie = _table_deja_publiee(meta)
    meta["avertissements"] = [
        {
            "message": str(w),
            "destinataire": (
                destinataire_de(w)
                or deja_publie.get(str(w))
                or _destinataire_herite(str(w))
            ),
        }
        for w in warnings
    ]


def unir_tables_avertissements(new_value: Any, old_value: Any) -> Any:
    """Union des deux tables de destinataires, le nouvel écrivain gagnant.

    Règle `meta.avertissements` de `merge_profile.REGLES_META`. Elle ne décide
    pas ce qui est publié — `deriver_avertissements` réaligne le bloc sur les
    `warnings` fusionnés juste après — mais elle **conserve le typage de
    l'écrivain que la fusion n'a pas retenu**, sans quoi un avertissement
    ramené de l'ancien profil par `unir_warnings` reparaîtrait sans
    destinataire.
    """
    entrees: list[dict[str, Any]] = []
    vus: set[str] = set()
    for source in (new_value, old_value):
        if not isinstance(source, list):
            continue
        for entree in source:
            if not isinstance(entree, dict):
                continue
            message = entree.get("message")
            if not isinstance(message, str) or message in vus:
                continue
            vus.add(message)
            entrees.append({
                "message": message,
                "destinataire": destinataire_de(entree),
            })
    return entrees
