#!/usr/bin/env python3
"""
group_roster.py — Récupère la composition réelle d'un groupe parlementaire.

Contrairement à raw_data/candidats.json (liste éditoriale des candidats déclarés
à l'élection présidentielle, voir parti_profile.py), ce module rend la VRAIE
liste des membres d'un groupe parlementaire (ex. tou·te·s les député·es LR
d'une législature), à utiliser ensuite avec group_profile.py — depuis l'open
data de l'Assemblée.

## Ce module ne parle plus à NosDéputés (#529, lot 5)

Il ne reste ici **aucun appel réseau propre**. `fetch_full_roster` délègue à
`an_roster.fetch_full_roster_an`, qui dérive la composition d'AMO30 — même
source que les scrutins et les amendements, Licence Ouverte au lieu d'ODbL, et
une législature qui est une donnée du référentiel plutôt qu'un sous-domaine à
connaître d'avance (AGENTS §7, #526/#527).

Sont partis avec la plateforme : `_BASE_URL_BY_LEGISLATURE_AN` (la table
domaine → législature, qui s'arrêtait à la 16e faute que NosDéputés y ait
jamais été étendu), `_base_url_for`, `_LIST_ENDPOINT`,
`fetch_full_roster_nosdeputes`, et **toute la machinerie de reprise qui
l'entourait** — `_erreur_retentable`, `_STATUTS_5XX_RETENTABLES`,
`_ROSTER_MAX_ATTEMPTS`, `_ROSTER_RETRY_BACKOFF_SECONDS`, `_ROSTER_TIMEOUT`.
Elle avait été écrite (#518, #524) pour un endpoint de 814 Ko généré à la volée
dont « aucune réponse en moins de 10 s » avait été mesurée sur 24 appels, puis
qui a servi un **500 déterministe** trois runs durant. Sur une archive lue
depuis `.cache/acteurs_historique_an/`, elle n'a plus d'objet : le
téléchargement de l'archive AMO30 a ses propres reprises, dans
`candidate_profile._ensure_acteurs_historique_zip_downloaded`.

Ce qui n'a PAS bougé, et c'est le point : le **contrat de sortie**.
`filter_roster_by_sigle` s'applique inchangé, le transit des rosters bruts par
artifact (#518) aussi, et `ERREURS_ROSTER` reste la liste unique de ce qu'un
appel peut lever — c'est elle qui fait d'une archive absente un « roster
indisponible » nommé (`exit 2`, fiches publiées intactes) plutôt qu'une trace
de pile qui coûte le commit du run.

Voir docs/decisions/retrait-nosdeputes-529.md.

## Le Sénat n'est plus une chambre servie ici (#528)

Toute chambre autre que `deputes` **lève**, en nommant la décision. Les deux
entrées Sénat de `raw_data/groupes_reels.json` restent `extraction_suspendue`
— leurs fiches publiées ne bougent pas — et ce chemin n'est atteint que si
quelqu'un lève cette suspension : il doit alors échouer bruyamment plutôt que
rendre un roster vide. Voir docs/decisions/retrait-senat-528.md.

Usage (depuis la racine du dépôt) :
    python src/group_roster.py --chambre deputes --sigle LR --legislature 16
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

import requests

import an_roster

# ── Transit du roster BRUT par artifact (#518, second incident) ──────────────
# Il restait DEUX fetchs de la même liste par run après #519 :
# `prepare-roster-matrix` (→ artifact `roster-candidats`) et
# `generate_group_profiles.py`, qui refetche pour son propre compte. Le second
# n'est pas qu'une requête de trop : la fiche de groupe publiée est bâtie sur
# une composition lue ~7 min après celle qui a servi à la collecte des profils.
# Une entrée/sortie de groupe entre les deux, et la composition publiée diverge
# du corpus collecté — exactement le défaut de correction de #518, sans qu'une
# seule étape n'échoue.
#
# Le format est un dict {clé texte → membres bruts}, tel que rendu par
# `fetch_full_roster` : aucune projection, pour que le consommateur applique
# `filter_roster_by_sigle` sur la MÊME matière que le producteur.

#: Séparateur de la clé texte. `None` (législature non applicable) se
#: sérialise en chaîne vide — jamais en `"None"` ni en `"courante"`, qui
#: seraient des valeurs de législature possibles au relire.
_SEPARATEUR_CLE = ":"


def cle_roster_texte(chambre: str, legislature: Optional[str]) -> str:
    """Clé JSON d'un roster brut : `"deputes:16"`, `"deputes:"`."""
    return f"{chambre}{_SEPARATEUR_CLE}{legislature or ''}"


def _cle_roster_depuis_texte(cle: str) -> tuple[str, Optional[str]]:
    chambre, _, legislature = cle.partition(_SEPARATEUR_CLE)
    return (chambre, legislature or None)


def ecrire_rosters_bruts(
    chemin: Path,
    rosters_bruts: dict[tuple[str, Optional[str]], Optional[list[dict[str, Any]]]],
) -> int:
    """Sérialise les rosters bruts RÉUSSIS ; retourne le nombre de clés écrites.

    Une clé en échec (`None`) n'est pas écrite : un fetch raté ne doit pas
    devenir une liste vide chez le consommateur (AGENTS.md §2 règle 5) — son
    absence le fait retomber sur son propre fetch, ce qui est le mode dégradé
    voulu, pas une composition de 0 membre.
    """
    charge = {
        cle_roster_texte(chambre, legislature): membres
        for (chambre, legislature), membres in rosters_bruts.items()
        if membres is not None
    }
    chemin.parent.mkdir(parents=True, exist_ok=True)
    # Compact : 814 Ko par clé, et personne ne lit ce fichier à l'œil (#433).
    chemin.write_text(
        json.dumps({"rosters": charge}, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    return len(charge)


def charger_rosters_bruts(chemin: Path) -> dict[tuple[str, Optional[str]], list[dict[str, Any]]]:
    """Relit un fichier écrit par `ecrire_rosters_bruts`.

    Raises:
        OSError: fichier absent ou illisible.
        ValueError: JSON invalide, ou structure inattendue — jamais un dict
            vide par défaut : « fichier corrompu » et « aucun roster » n'ont
            pas la même conséquence chez l'appelant.
    """
    charge = json.loads(chemin.read_text(encoding="utf-8"))
    rosters = charge.get("rosters")
    if not isinstance(rosters, dict):
        raise ValueError(f"{chemin} : clé `rosters` absente ou de type inattendu.")
    resultat: dict[tuple[str, Optional[str]], list[dict[str, Any]]] = {}
    for cle, membres in rosters.items():
        if not isinstance(membres, list):
            raise ValueError(f"{chemin} : roster {cle!r} n'est pas une liste.")
        resultat[_cle_roster_depuis_texte(cle)] = membres
    return resultat


# `_erreur_retentable`, `_base_url_for` et `_member_matches_legislature` ont été
# RETIRÉS. Les deux premiers par #529 (voir l'en-tête du module) : ils
# décrivaient la politique de reprise et le choix de domaine d'un endpoint
# NosDéputés qui n'est plus appelé. Le troisième par #528 : il n'existait que
# pour le Sénat, dont `archive.nossenateurs.fr` servait un domaine d'archive
# unique, sans sous-domaine par période, ce qui obligeait à filtrer les membres
# côté client sur `mandat_fin`. L'Assemblée n'en a jamais eu besoin — sa
# législature est une donnée du référentiel AMO30 (#526).


#: Tout ce qu'un appel à `fetch_full_roster` peut légitimement lever, quelle
#: que soit la source (#527). Les deux consommateurs interceptaient
#: `(ValueError, requests.RequestException)` — la forme des échecs NosDéputés.
#: `an_roster` lève `RosterAnIndisponible` / `RosterAnInactif`, qui héritent de
#: `RuntimeError` : sans cette liste, une archive AMO30 absente ne serait plus
#: un « roster indisponible » nommé et annoté (#518/#524) mais une trace de pile
#: qui tue le job — c'est-à-dire un `exit 1` là où #518 a payé pour obtenir un
#: `exit 2`. `CorrespondanceSiglesInvalide` et `CorrespondanceInvalide` héritent
#: déjà de `ValueError` et sont couvertes par elle.
ERREURS_ROSTER: tuple[type[BaseException], ...] = (
    ValueError,
    requests.RequestException,
    an_roster.RosterAnIndisponible,
    an_roster.RosterAnInactif,
)


def fetch_full_roster(
    chambre: str,
    legislature: Optional[str] = None,
    session: Optional[requests.Session] = None,
) -> list[dict[str, Any]]:
    """Le roster brut d'une (chambre, législature) — **AMO30, et rien d'autre**.

    Seul endroit du dépôt qui choisit la source d'un roster. Depuis #529 il n'y
    a plus de choix à faire : la lecture NosDéputés vers laquelle #527
    aiguillait encore le Sénat et le repli du drapeau est retirée. Ce qui reste
    de l'aiguillage est le **refus**, et il est explicite dans les deux cas :

    - une chambre autre que `deputes` lève en nommant #528 — les deux groupes
      Sénat de `groupes_reels.json` restent suspendus, et ce chemin n'est
      atteint que si quelqu'un lève cette suspension ;
    - `an_roster.AN_ROSTER_ACTIF` baissé lève `RosterAnInactif` (dans
      `an_roster`), et ne rend **jamais** une liste vide. Le drapeau n'est plus
      un aiguillage vers une autre source, c'est un interrupteur : baissé, il
      n'y a plus de roster du tout, bruyamment. Sa condition de retrait est
      écrite dans docs/decisions/roster-an-derive-amo30-526.md §9.

    `session` n'a plus aucun effet : aucune requête HTTP ne part d'ici.
    Conservée dans la signature parce que trois appelants la passent encore et
    qu'un paramètre retiré d'une signature publique est un `TypeError` chez eux
    — elle est ignorée, et c'est sans conséquence puisque l'archive AMO30 est
    téléchargée et mise en cache par `candidate_profile`.

    La table sigle publié → sigle AN est lue dans son fichier committé,
    `raw_data/groupes_reels.json` (`an_roster.CHEMIN_CONFIG_GROUPES`), et non
    dans le `--config` de l'appelant : un groupe absent de la table échoue en
    **nommant** le couple `(sigle, législature)` plutôt que de rendre un roster
    vide (#526 §3b).

    Raises:
        Tout ce que liste `ERREURS_ROSTER`.
    """
    del session  # cf. docstring : conservée pour les appelants, sans effet.
    if chambre != "deputes":
        raise ValueError(
            f"Chambre {chambre!r} hors périmètre. Seule valeur servie : 'deputes'. "
            "Le Sénat a été retiré par #528 (archive.nossenateurs.fr ne sert plus "
            "de certificat valide) ; les 2 groupes Sénat restent suspendus, voir "
            "docs/decisions/retrait-senat-528.md. #885 établit une source de "
            "remplacement — data.senat.fr — mais elle ne passe PAS par ici : ce "
            "refus garde le chemin NosSénateurs, qui ne rouvre pas. Un roster "
            "sénatorial viendra d'une voie distincte ; voir "
            "docs/decisions/reouverture-partielle-senat-885.md."
        )
    return an_roster.fetch_full_roster_an(legislature)


def filter_roster_by_sigle(
    raw_members: list[dict[str, Any]],
    chambre: str,
    groupe_sigle: str,
) -> list[dict[str, Any]]:
    """Filtre une liste de membres bruts (issue de `fetch_full_roster`) par sigle de groupe.

    `chambre` n'est plus lue depuis #528 (le filtre temporel qu'elle pilotait
    était propre au Sénat) : elle reste dans la signature parce que c'est la
    clé de lecture des appelants, et qu'une chambre qui disparaît de la
    signature d'un filtre est une information perdue le jour où il y en a deux.
    """
    roster: list[dict[str, Any]] = []
    for member in raw_members:
        if member.get("groupe_sigle") != groupe_sigle:
            continue

        mandat_fin = member.get("mandat_fin")
        roster.append({
            "slug": member.get("slug"),
            # D'où vient ce slug (#708) : `table` = correspondance relue
            # (#525), `fabrique` = `slugify(état civil AMO30)`, la porte
            # d'entrée d'un membre que personne n'a encore collecté. `None`
            # quand la source ne le déclare pas — l'absence dit « personne ne
            # l'a déclaré », jamais « relu » (AGENTS §2 règle 5). Le champ
            # traverse le filtre parce que `generate_roster_candidats` doit
            # pouvoir COMPTER ce qui entre par cette porte : un membre entré
            # sans qu'aucune relecture ne l'ait vu ne doit pas être
            # indiscernable d'un membre relu.
            "slug_origine": member.get("slug_origine"),
            "nom": member.get("nom"),
            "groupe_sigle": member.get("groupe_sigle"),
            "mandat_debut": member.get("mandat_debut"),
            "mandat_fin": mandat_fin,
            # #809 — LES DEUX BORNES SONT UNE ENVELOPPE, ET LE DÉTAIL DOIT
            # TRAVERSER AVEC ELLES. `mandat_debut`/`mandat_fin` recollent en un
            # intervalle des appartenances qui en comptent plusieurs : 33
            # membres de 8 fiches étaient dits dans leur groupe pendant qu'ils
            # étaient au gouvernement, jusqu'à 1 110 jours masqués.
            #
            # Ce filtre est une projection par clés, et #809 l'avait manqué :
            # le champ était produit par `an_roster`, lu par
            # `appartenances_depuis_roster` et publié par la fiche, mais **jeté
            # ici**, au milieu. Le run 34538350163 a régénéré les 23 fiches
            # sans qu'aucune ne porte `periodes[]`. C'est la règle de
            # `docs/regles/fusion-et-index.md` : un champ ajouté n'atteint pas
            # tout seul un consommateur qui recopie les entrées à la main.
            "mandat_periodes": member.get("mandat_periodes"),
            "actif": not mandat_fin,
            # `acteur_ref` (le `PA######` d'AMO30) traverse le filtre depuis
            # #529 : c'est ce qui permet à `generate_roster_candidats` de
            # donner à chaque entrée de roster une `source` qui pointe vers la
            # fiche AN du membre. L'ancienne source était
            # `<domaine NosDéputés>/<slug>`, dérivée de la législature, et le
            # membre brut n'avait alors pas d'identifiant externe à porter.
            # `None` si la source n'en fournit pas : jamais inventé (règle 5).
            "acteur_ref": member.get("acteur_ref"),
        })
    return roster


def fetch_group_roster(
    chambre: str,
    groupe_sigle: str,
    legislature: Optional[str] = None,
    session: Optional[requests.Session] = None,
) -> list[dict[str, Any]]:
    """Récupère la liste des membres réels d'un groupe parlementaire.

    Args:
        chambre: "deputes" (seule chambre servie depuis #528).
        groupe_sigle: sigle exact du groupe tel que fourni par l'API
                      (ex. "LR", "RN", "SOC" — voir champ `groupe_sigle` des
                      entrées renvoyées par /deputes/json).
        legislature: législature AN (ex. "16") ; détermine le sous-domaine
                     interrogé. None = domaine courant.
        session: session requests à réutiliser (optionnel, pour les tests).

    Returns:
        Liste de dicts {slug, nom, groupe_sigle, mandat_debut, mandat_fin, actif}
        pour chaque membre dont `groupe_sigle` correspond exactement.

    Raises:
        ValueError: chambre ou législature inconnue.
        requests.RequestException: échec réseau (non intercepté, remonté tel quel).

    Note : pour construire plusieurs groupes de la même chambre/législature,
    préférer `fetch_full_roster` + `filter_roster_by_sigle` pour éviter de
    refaire le même appel réseau à chaque sigle.

    Passe par `fetch_full_roster`, donc par l'aiguillage de #527 : sur
    `deputes`, ce que rend cette fonction vient d'AMO30, pas de NosDéputés.
    Une commodité de mise au point qui lirait une autre source que le pipeline
    serait un piège — c'est pour la ligne de commande qu'on regarde un roster.
    """
    raw_members = fetch_full_roster(chambre, legislature=legislature, session=session)
    return filter_roster_by_sigle(raw_members, chambre, groupe_sigle)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Récupère la composition réelle d'un groupe parlementaire "
        "(AMO30 pour l'Assemblée depuis #527 ; le Sénat est hors périmètre depuis #528).",
    )
    parser.add_argument(
        "--chambre",
        choices=["deputes"],
        required=True,
        help="Seule valeur : deputes. Le Sénat est hors périmètre depuis #528.",
    )
    parser.add_argument("--sigle", required=True, metavar="SIGLE", help='Ex. "LR", "RN", "SOC".')
    parser.add_argument("--legislature", default=None, metavar="N", help='Législature AN, ex. "16".')
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    try:
        roster = fetch_group_roster(
            chambre=args.chambre,
            groupe_sigle=args.sigle,
            legislature=args.legislature,
        )
    except ERREURS_ROSTER as exc:
        print(f"[!] {exc}", file=sys.stderr)
        return 1

    print(f"→ {len(roster)} membre(s) trouvé(s) pour le groupe {args.sigle!r}.", file=sys.stderr)
    print(json.dumps(roster, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
