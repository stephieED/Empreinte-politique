"""L'`id` d'un profil pivot est le slug, et ne dérive d'aucune collecte (#487).

Sous-issue A de l'épic #486. Le préfixe `nosdeputes:` / `nossenateurs:` n'a pas
été retiré parce qu'il était redondant — il l'était, la provenance est consignée
trois fois ailleurs (`sources[].type`, `identite.source_url`, `meta.provenance`)
— mais parce qu'il était **instable** : il dérivait de `chambre`, c'est-à-dire du
site qui avait répondu ce jour-là. Entre `25f7bc7` et `01ffa7f`, sur des
carrières inchangées, `jean-luc-melenchon` est passé à `nossenateurs` et
`stephane-mazars` à `nosdeputes` — deux bascules en sens opposés.

D'où la forme des tests ci-dessous. Vérifier `id == slug` sur un cas nominal
serait faible : un préfixe stable passerait ce test aussi. Ce qui empêche la
réintroduction du défaut est de vérifier que l'`id` **ne dépend d'aucune donnée
de collecte** — on fait donc varier tout ce que la collecte produit, un champ à
la fois, et l'`id` ne doit pas bouger.

Aucune lecture du corpus vivant (`pivot_data/`, `raw_data/profiles/`) : ces
tests tournent en CI, où le corpus est absent du disque (#473).
"""

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from audit_diff_profils import (  # noqa: E402
    COLLECTION_GOUVERNEMENTS,
    COLLECTION_PROFILS,
    comparer,
    relever,
)
from gouvernement_roster import build_gouvernement_roster  # noqa: E402
from merge_profile import merge_pivot_profile  # noqa: E402
from normalize_europarl import normalize_europarl  # noqa: E402
from normalize_profil import normalize_profil  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures figées, minimales : le même élu, collecté d'un côté puis de l'autre
# ---------------------------------------------------------------------------

def _brut(chambre: str = "deputes") -> dict:
    """Profil brut minimal au format `candidate_profile.build_profile()`.

    `chambre` est ici le paramètre de collecte NosDéputés/NosSénateurs
    (`"deputes"` / `"senateurs"`), pas la chambre pivot : c'est exactement le
    champ dont le préfixe dérivait.
    """
    domaine = "nosdeputes" if chambre == "deputes" else "nossenateurs"
    return {
        "slug": "marie-martin",
        "chambre": chambre,
        "source": f"https://www.{domaine}.fr/marie-martin",
        "identite": {
            "nom_complet": "Marie Martin",
            "groupe_sigle": "SOC",
            "groupe_nom": "Socialistes",
            "url_an_ou_senat": "https://www.assemblee-nationale.fr/dyn/deputes/PA123456",
        },
        "mandats": [
            {
                "categorie": "mandat_electif",
                "type": "mandat",
                "label": "Mandat parlementaire (Socialistes)",
                "debut": "2004-09-26",
                "fin": None,
                "actif": True,
            }
        ],
        "votes": [],
        "interventions": [],
        "amendements": [],
        "dossiers_legislatifs": [],
        "meta": {"genere_le": "2026-08-20T12:00:00+0000", "synchro_sources": {}},
    }


def _brut_ue() -> dict:
    """Bloc `mandat_europeen` minimal, format `build_profile_ue()`.

    Modelé sur celui de `jordan-bardella`, le seul profil du corpus dont l'`id`
    ne dérivait pas de son slug (`europarl:131580`).
    """
    return {
        "identifiant_pe": 131580,
        "nom_complet": "Jordan BARDELLA",
        "url_source": "https://www.europarl.europa.eu/meps/fr/131580",
        "mandats_europeens": [
            {
                "type": "EU_INSTITUTION",
                "organisation_nom": "Parlement européen",
                "role_label": "Député",
                "debut": "2019-07-02",
                "fin": None,
                "actif": True,
            }
        ],
        "meta": {"genere_le": "2026-08-20T12:00:00+0000"},
    }


# ---------------------------------------------------------------------------
# 1. L'`id` est le slug
# ---------------------------------------------------------------------------

def test_id_vaut_le_slug_sans_prefixe():
    assert normalize_profil(_brut())["id"] == "marie-martin"


def test_id_identique_quelle_que_soit_la_chambre_qui_a_repondu():
    """Le fait n°2 de #487, transformé en garde-fou.

    Le même élu, collecté côté Assemblée puis côté Sénat, portait deux `id`
    différents. Il n'en porte plus qu'un.
    """
    assert (normalize_profil(_brut("deputes"))["id"]
            == normalize_profil(_brut("senateurs"))["id"]
            == "marie-martin")


def test_la_provenance_reste_lisible_dans_sources():
    """Retirer le préfixe ne perd rien : `sources[].type` porte toujours la
    provenance, et lui la décrit *vraiment* — c'est celle d'UNE source, pas
    l'identité de la personne (AGENTS.md §2.2).

    Elle valait `nosdeputes`/`nossenateurs` selon la chambre qui avait répondu
    (`_SOURCE_TYPE_MAP`). Depuis #529 il n'y a plus qu'une provenance possible
    pour un profil FR, et c'est justement ce que ce test doit constater : la
    chambre ne décide plus de la source, parce qu'il n'y a plus de choix.
    """
    assert normalize_profil(_brut("deputes"))["sources"][0]["type"] == "assemblee_nationale"
    assert normalize_profil(_brut("senateurs"))["sources"][0]["type"] == "assemblee_nationale"


# ---------------------------------------------------------------------------
# 2. Le garde-fou de fond : aucune dépendance à une donnée de collecte
# ---------------------------------------------------------------------------

# Valeurs de substitution couvrant les formes qu'une collecte peut rendre :
# manquant, vide, et une valeur plausible mais différente — dont les deux
# chambres, par lesquelles le défaut est arrivé.
_VARIANTES = (None, "", [], {}, 0, "senateurs", "deputes", "valeur-inattendue")


def test_l_id_ne_depend_d_aucune_donnee_de_collecte():
    """Le test qui empêche la réintroduction du défaut.

    `id == slug` sur un cas nominal ne dit rien : un préfixe **stable** le
    passerait. Ce qu'on interdit ici est la *dépendance* — faire varier
    n'importe quel champ collecté ne doit pas déplacer l'`id` d'un caractère.

    Les variantes qui font échouer la normalisation entière sont ignorées : ce
    test porte sur l'`id` d'un profil produit, pas sur la robustesse de
    `normalize_profil` à une entrée aberrante.
    """
    # La dépendance est vérifiée AVANT `id == slug` : c'est elle le sujet, et
    # c'est elle qui doit nommer la panne si le défaut revient. Un préfixe
    # stable réintroduit passerait la seconde assertion mais pas la première.
    reference = normalize_profil(_brut())["id"]

    champs_collectes = [c for c in _brut() if c != "slug"]
    assert "chambre" in champs_collectes, (
        "le champ par lequel l'instabilité est arrivée doit rester couvert"
    )

    testes = 0
    for champ in champs_collectes:
        for variante in _VARIANTES:
            brut = copy.deepcopy(_brut())
            brut[champ] = variante
            try:
                obtenu = normalize_profil(brut)["id"]
            except (AttributeError, TypeError):
                continue
            testes += 1
            assert obtenu == reference, (
                f"l'`id` a suivi le champ collecté {champ!r} "
                f"({variante!r} → {obtenu!r}) : il redevient instable"
            )
        brut = copy.deepcopy(_brut())
        del brut[champ]
        assert normalize_profil(brut)["id"] == reference, (
            f"l'`id` a suivi l'absence du champ collecté {champ!r}"
        )
        testes += 1

    assert testes >= len(champs_collectes), "aucune variante n'a été exercée"
    # …et, une fois l'indépendance établie, l'`id` est bien le slug.
    assert reference == "marie-martin"


def test_seul_le_slug_deplace_l_id():
    """Contrepartie du test précédent : le slug, lui, doit bien porter l'`id`.

    Sans quoi « ne dépend de rien » se satisferait d'une constante.
    """
    brut = _brut()
    brut["slug"] = "un-autre-slug"
    assert normalize_profil(brut)["id"] == "un-autre-slug"


# ---------------------------------------------------------------------------
# 3. Le cas européen (le seul `id` du corpus qui ne dérivait pas de son slug)
# ---------------------------------------------------------------------------

def test_normalize_europarl_prend_le_slug_quand_il_l_a():
    pivot = normalize_europarl(_brut_ue(), slug="jordan-bardella")
    assert pivot["id"] == "jordan-bardella"


def test_l_identifiant_pe_reste_tracable_hors_de_l_id():
    """§2.2 : retirer `131580` de l'`id` ne doit rien coûter en traçabilité.

    Sur le profil réel il apparaît 25 fois, dont 24 hors de l'`id` — la source
    EP et le `source_url` de chacun des 22 mandats européens. Ici la fixture est
    réduite, mais l'invariant est le même : la source reste atteignable.
    """
    pivot = normalize_europarl(_brut_ue(), slug="jordan-bardella")
    assert "131580" not in pivot["id"]
    assert pivot["sources"][0]["url"].endswith("/131580")
    assert all("131580" in m["source_url"] for m in pivot["mandats"])


def test_normalize_europarl_sans_slug_garde_l_identifiant_de_source():
    """Sans slug, pas de slug inventé.

    `ue_profile` n'en porte pas, et le seul qu'on pourrait en tirer viendrait de
    `nom_complet` — donc d'une donnée de collecte, exactement le défaut que
    cette issue retire. Un identifiant de source explicite vaut mieux.
    """
    assert normalize_europarl(_brut_ue())["id"] == "europarl:131580"


# ---------------------------------------------------------------------------
# 4. Migration du corpus : la nouvelle valeur l'emporte à la fusion
# ---------------------------------------------------------------------------

def test_la_fusion_laisse_le_nouvel_id_l_emporter():
    """Aucune réécriture manuelle de `pivot_data/`, aucune table de
    correspondance : une régénération suffit — à condition que la fusion
    additive ne réimpose pas l'ancien `id`.

    `merge_pivot_profile` part de `dict(new)` et ne rattrape jamais `id` : la
    valeur régénérée gagne, y compris contre un ancien préfixé.
    """
    ancien = normalize_profil(_brut())
    ancien["id"] = "nossenateurs:marie-martin"          # l'état committé
    nouveau = normalize_profil(_brut())             # ce que régénère le pipeline
    assert merge_pivot_profile(ancien, nouveau)["id"] == "marie-martin"


def test_la_fusion_ne_regresse_pas_vers_l_ancien_prefixe_dans_l_autre_sens():
    """Le contrôle inverse : un ancien non préfixé ne doit pas être réécrit
    par un nouveau préfixé venu d'un chemin resté en arrière."""
    ancien = normalize_profil(_brut())
    nouveau = normalize_profil(_brut())
    nouveau["id"] = "nosdeputes:marie-martin"
    # `merge_pivot_profile` fait gagner le nouveau : c'est le contrat, et c'est
    # ce qui rend la migration possible. Le test le fige pour qu'une inversion
    # de politique ne passe pas inaperçue.
    assert merge_pivot_profile(ancien, nouveau)["id"] == "nosdeputes:marie-martin"


# ---------------------------------------------------------------------------
# 5. La réserve de #487 : ce que le contrôle de perte fait de la réécriture
# ---------------------------------------------------------------------------

def _profil_pivot_pour_roster(id_: str) -> dict:
    """Pivot réduit aux champs que `build_gouvernement_roster` regarde."""
    return {
        "id": id_,
        "nom": "Marie Martin",
        "mandats": [
            {
                "categorie": "fonction_gouvernementale",
                "type": "mandat",
                "label": "Gouvernement (BAYROU)",
                "debut": "2024-12-24",
                "fin": None,
                "actif": True,
            }
        ],
    }


def test_le_membre_id_du_roster_suit_l_id_du_profil():
    """`gouvernement_roster` publie `membre_id: profil["id"]` : changer la
    convention réécrit `membres[]`. C'est le fait d'où part la réserve."""
    avant = build_gouvernement_roster(
        "BAYROU", "2024-12-23", None, [_profil_pivot_pour_roster("nosdeputes:marie-martin")])
    apres = build_gouvernement_roster(
        "BAYROU", "2024-12-23", None, [_profil_pivot_pour_roster("marie-martin")])
    assert [m["membre_id"] for m in avant] == ["nosdeputes:marie-martin"]
    assert [m["membre_id"] for m in apres] == ["marie-martin"]
    assert len(avant) == len(apres) == 1


def test_la_reecriture_des_membre_id_n_est_pas_bloquante():
    """**Le verdict de la réserve non levée de #487.**

    Craint : que la réécriture des 113 `membre_id` des 10 fichiers de
    gouvernement soit lue comme une régression massive, et que la correction
    bloque elle-même le commit qu'elle doit produire.

    Mesuré, ici comme sur le corpus : elle est **invisible** au contrôle.
    `membre_id` vit à l'intérieur d'une entrée de `membres[]`, et le contrôle ne
    compare d'une liste que sa **cardinalité** — que la réécriture ne touche
    pas. Les scalaires surveillés d'un gouvernement sont `gouvernement_id`,
    `nom`, `premier_ministre` et `periode.debut` ; `membre_id` n'en est pas.
    """
    def _gouvernement(prefixe: str) -> dict:
        return {
            "gouvernement_id": "gouvernement:BAYROU",
            "nom": "Gouvernement Bayrou",
            "premier_ministre": {"membre_id": f"{prefixe}francois-bayrou"},
            "periode": {"debut": "2024-12-23", "fin": None},
            "membres": [
                {"membre_id": f"{prefixe}marie-martin", "portefeuille": None},
                {"membre_id": f"{prefixe}jean-dupont", "portefeuille": None},
            ],
            "textes": [],
            "sources": [],
        }

    avant = {"g.json": relever(_gouvernement("nosdeputes:"), COLLECTION_GOUVERNEMENTS)}
    apres = {"g.json": relever(_gouvernement(""), COLLECTION_GOUVERNEMENTS)}
    rapport = comparer(avant, apres, COLLECTION_GOUVERNEMENTS)

    assert rapport["bloquant"] is False
    assert rapport["pertes_sur_champs_stables"] == []
    assert rapport["pertes_scalaires"] == []
    # Rien du tout, pas même un signalement : le contrôle ne voit pas la valeur
    # des entrées d'une liste.
    assert rapport["evolutions_scalaires"] == []
    assert rapport["pertes"] == []


def test_le_changement_d_id_d_un_profil_est_signale_mais_non_bloquant():
    """Côté profils, l'`id` **est** un scalaire surveillé — le changement se
    voit donc, et c'est voulu : il figure au rapport, sous le régime que #470 a
    retenu pour les changements de valeur (relevés, non bloquants). Seule une
    régression `renseigné → null` bloque.
    """
    def _profil(id_: str) -> dict:
        return {"id": id_, "nom": "Marie Martin", "chambre": "AN",
                "votes": [], "mandats": [], "sources": []}

    avant = {"marie-martin.pivot.json": relever(_profil("nossenateurs:marie-martin"),
                                                COLLECTION_PROFILS)}
    apres = {"marie-martin.pivot.json": relever(_profil("marie-martin"),
                                                COLLECTION_PROFILS)}
    rapport = comparer(avant, apres, COLLECTION_PROFILS)

    assert rapport["bloquant"] is False
    assert rapport["pertes_scalaires"] == []
    assert rapport["evolutions_scalaires"] == [{
        "fichier": "marie-martin.pivot.json", "champ": "id",
        "avant": "nossenateurs:marie-martin", "apres": "marie-martin",
    }]


def test_un_id_qui_disparait_reste_bloquant():
    """Le corollaire : si la nouvelle convention faisait disparaître l'`id`
    au lieu de le raccourcir, le contrôle bloquerait. Ce test dit que le
    garde-fou n'a pas été désarmé au passage."""
    def _profil(id_) -> dict:
        return {"id": id_, "nom": "Marie Martin", "votes": [], "mandats": []}

    rapport = comparer(
        {"x.json": relever(_profil("nosdeputes:marie-martin"), COLLECTION_PROFILS)},
        {"x.json": relever(_profil(None), COLLECTION_PROFILS)},
        COLLECTION_PROFILS,
    )
    assert rapport["bloquant"] is True
    assert [p["champ"] for p in rapport["pertes_scalaires"]] == ["id"]


# ---------------------------------------------------------------------------
# 6. Le seul lecteur du préfixe reste compatible
# ---------------------------------------------------------------------------

def test_le_seul_lecteur_du_prefixe_accepte_un_id_sans_prefixe():
    """`group_profile` (l. 1295, `--merge-existing`) est le seul endroit du
    dépôt qui lise le préfixe — et il le **retire** pour récupérer le slug.
    Un `id` déjà sans préfixe le traverse inchangé, dans les deux sens : rien à
    migrer de ce côté.
    """
    def _slug_depuis_membre_id(membre_id: str) -> str:
        # Recopie exacte de src/group_profile.py:1295.
        return membre_id.split(":", 1)[1] if ":" in membre_id else membre_id

    assert _slug_depuis_membre_id("nosdeputes:marie-martin") == "marie-martin"
    assert _slug_depuis_membre_id("nossenateurs:marie-martin") == "marie-martin"
    assert _slug_depuis_membre_id("marie-martin") == "marie-martin"
