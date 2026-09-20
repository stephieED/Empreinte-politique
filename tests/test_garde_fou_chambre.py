"""Garde-fou de la **condition de retrait** du scalaire `chambre` (#494).

Sous-issue **E** de l'épic **#486**, après #493 (D, PR #504) qui a créé
`chambres` — la liste dérivée — et l'a fait coexister avec `chambre`, le
scalaire, « le temps de reprendre les consommateurs un par un ».

#493 a écrit la condition de retrait dans
`docs/decisions/chambres-profil-derivees.md` :

> 1. **les consommateurs ont migré** — et le garde-fou de #494 le vérifie ;
> 2. **le champ n'a plus rien de propre à dire** — le warning
>    `chambres du profil non corroborée` est absent de tout le corpus.

**Ce fichier est la condition 1.** Il ne peut pas être la condition 2 : celle-ci
porte sur le corpus vivant, absent du disque en CI (§3, #473), et se mesure par
`audit_pivot_dataset.compute_agregation_warnings` sur un run réel.

Pourquoi un garde-fou statique plutôt qu'une note dans un journal : le dépôt
porte déjà des transitoires devenus permanents — les replis de lecture de #431
et #432 sont encore là, des mois après. Une coexistence sans critère mécanique
devient définitive par défaut, jamais par décision.

## Comment il s'y prend

Il énumère **tout** endroit où la clé `"chambre"` est lue ou écrite, dans le
pipeline Python (`src/*.py`, par l'AST) comme dans l'interface
(`web/UI_finale`, par le motif d'accès à la propriété), et exige que chacun soit
**déclaré** ci-dessous avec sa catégorie. C'est la déclaration qui fait le
travail : un emplacement neuf casse le test, et son auteur doit dire *de quelle
`chambre` il parle* — celle d'un profil, d'un mandat, d'un groupe, ou la chambre
de collecte. Le recensement de #486 confondait les quatre, et c'est ce qui l'a
rendu faux sur trois points (voir `docs/technical_decisions.md`).

Le retrait devient alors trivialement décidable : quand plus aucun emplacement
n'est de catégorie `CONSOMMATEUR_PROFIL`, la condition 1 est remplie.
`test_condition_1_de_retrait` en donne l'état à chaque run, sans jugement.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
SRC = RACINE / "src"
UI = RACINE / "web" / "UI_finale"

# --- Catégories -------------------------------------------------------------
#
# Quatre `chambre` différentes vivent dans ce dépôt sous le même nom. Les
# distinguer n'est pas cosmétique : migrer la mauvaise casserait quelque chose
# de sans rapport, et le recensement de l'épic mélangeait déjà les quatre.

#: `chambre` du **profil pivot** — le champ que #493 a rendu dérivé et que #494
#: migre. Tout emplacement de cette catégorie retarde le retrait du scalaire.
CONSOMMATEUR_PROFIL = "consommateur du champ profil"

#: La fabrique elle-même (`deriver_chambres` / `appliquer_chambres`), son
#: validateur et le gabarit du schéma. Ne disparaît qu'avec le champ.
FABRIQUE = "fabrique / validation du champ profil"

#: Le **repli** passé à la fabrique : la chambre de collecte, reprise telle
#: quelle pour ne pas supprimer une donnée observée (#493). Disparaît avec le
#: scalaire, puisque c'est lui.
REPLI = "repli de la fabrique"

#: Le **repli de lecture** de `schema_pivot.lire_chambres()`, porte unique des
#: consommateurs (#494) : la seule branche qui lit encore le scalaire pour le
#: compte d'un tiers. Elle existe parce qu'aucun des 209 profils publiés ne
#: porte encore `chambres` (mesuré sur `07e9147`, 0/209) ; c'est la ligne à
#: supprimer le jour du retrait, et il n'y en a qu'une.
REPLI_DE_LECTURE = "repli de lecture de lire_chambres()"

#: `chambre` du profil **brut** (`raw_data/profiles`), qui vaut `"deputes"` ou
#: `"senateurs"` : *quel jeu de données a répondu*, pas où siège la personne.
#: Sans rapport avec le champ pivot — ne migre pas.
COLLECTE = "chambre de collecte (profil brut)"

#: `chambre` d'un **groupe parlementaire** (`schema_groupe`), ou d'un texte.
#: Sans rapport avec le champ pivot — ne migre pas.
GROUPE = "chambre d'un groupe / d'un texte"

#: `chambre` portée par un **mandat électif** depuis #492. C'est la source dont
#: `chambres` dérive — elle ne migre pas, elle est ce vers quoi on migre.
MANDAT = "chambre d'un mandat électif (#492)"


# --- Emplacements déclarés, côté pipeline -----------------------------------
#
# Clé : (module, fonction englobante). Une fonction peut porter plusieurs
# emplacements ; ils partagent alors une catégorie, sauf mention `+`.

SITES_PYTHON: dict[tuple[str, str], str] = {
    # -- La fabrique et sa validation ---------------------------------------
    ("schema_pivot.py", "deriver_chambres"): MANDAT,
    ("schema_pivot.py", "appliquer_chambres"): FABRIQUE,
    ("schema_pivot.py", "validate_profil"): FABRIQUE,
    ("schema_pivot.py", "make_empty_profil"): FABRIQUE,
    ("schema_pivot.py", "lire_chambres"): REPLI_DE_LECTURE,
    # -- Les producteurs du repli, à la construction du pivot ---------------
    ("normalize_profil.py", "_normalize_mandat"): MANDAT,
    ("normalize_profil.py", "normalize_profil"): REPLI,
    ("normalize_europarl.py", "normalize_europarl"): REPLI,
    # #885 — la chambre d'un mandat électif sénatorial. Posée là et nulle part
    # ailleurs : le Sénat est la seule source qui l'établisse sans ambiguïté
    # pour ses propres mandats, et un groupe d'amitié ne dit pas où l'on siège.
    ("normalize_senat.py", "normalize_mandat"): MANDAT,
    # #885 — LIT la `chambre` d'un mandat pour savoir si un mandat sénatorial
    # daté remplace un mandat hérité. Un remplaçant d'une autre chambre n'en est
    # pas un, et le confondre retirerait un fait sans contrepartie.
    ("retrait_heritage_senat.py", "mandats_electifs_remplaces"): MANDAT,
    ("mep_profile.py", "normalize_parltrack"): REPLI,
    # -- La fusion ----------------------------------------------------------
    # `merge_pivot_profile` réécrit les deux champs par `appliquer_chambres`
    # juste après : son `_prefer_non_empty` n'alimente plus que le repli.
    ("merge_profile.py", "merge_pivot_profile"): REPLI,
    # `merge_raw_profile` fusionne le profil **brut** : sa `chambre` vaut
    # "deputes"/"senateurs". Le recensement de #494 la comptait comme l'un des
    # « deux niveaux de fusion » du champ profil — elle n'en est pas un.
    ("merge_profile.py", "merge_raw_profile"): COLLECTE,
    ("merge_profile.py", "backfill_mandat_chambre"): MANDAT,
    # -- La collecte --------------------------------------------------------
    # `candidate_profile._extract_mandats` portait l'estampille de chambre sur
    # le mandat électif tiré d'un profil brut NosDéputés ; il est parti avec la
    # source (#529). Le mandat électif est désormais reconstruit dans
    # `build_profile` depuis `identite_an`, qui l'estampille au même endroit
    # que le reste de la collecte — d'où un emplacement en moins, pas une
    # estampille en moins.
    ("candidate_profile.py", "build_profile"): COLLECTE,
    ("generate_all_profiles.py", "build_minimal_profile"): COLLECTE,
    ("generate_all_profiles.py", "process_candidat"): COLLECTE,
    ("generate_all_profiles.py", "main"): COLLECTE,
    # -- Les groupes --------------------------------------------------------
    ("schema_groupe.py", "make_empty_profil_groupe"): GROUPE,
    ("schema_groupe.py", "validate_profil_groupe"): GROUPE,
    # #836 — la fiche de LIGNÉE porte la chambre de ses maillons, pour la même
    # raison qu'une fiche de groupe : c'est la chambre de l'organe, jamais le
    # scalaire d'un profil que #494 retire.
    ("schema_lignee.py", "make_empty_profil_lignee"): GROUPE,
    # La chambre y est aussi ce qui apparie un groupe à sa lignée : une
    # fiche `Senat:LR` et une lignée `AN:LIGNEE:LR` ne se rencontrent
    # jamais, et c'est le contrôle qui le dit plutôt qu'un préfixe qu'on
    # espère bien écrit.
    ("groupes_config.py", "charger_lignees"): GROUPE,
    ("generate_lignee_profiles.py", "generer_une_lignee"): GROUPE,
    ("group_profile.py", "_mandats_electifs"): MANDAT,
    ("group_profile.py", "generate_groupe_profile_from_roster"): GROUPE,
    ("group_profile.py", "main"): GROUPE,
    ("generate_group_profiles.py", "generate_all"): GROUPE,
    # #511 a scindé `build_roster_candidats` : l'aplatissement (et donc la
    # lecture de la `chambre` du groupe) a migré dans la variante qui compte
    # aussi les membres par groupe, et le libellé d'anomalie s'en sert pour
    # distinguer les deux `LR` (`AN:LR` et `Senat:LR`).
    ("generate_roster_candidats.py", "build_roster_candidats_detaille"): GROUPE,
    # #516 a sorti le libellé de `generate_roster_candidats._libelle_groupe`
    # (qui n'en est plus qu'un alias) vers le module de config partagé : les
    # trois consommateurs de `groupes_reels.json` nomment un groupe pareil.
    ("groupes_config.py", "libelle_groupe"): GROUPE,
    ("check_quality_gate.py", "_report_groupes"): GROUPE,
    # #686 : la §4b ne réclame une position politique déclarée qu'aux fiches de
    # l'Assemblée. AMO30 ne qualifie que ses propres organes, et exiger la
    # donnée d'une fiche sénatoriale serait en exiger une qui n'existe pas.
    ("check_quality_gate.py", "_report_position_politique"): GROUPE,
    ("audit_groupe_dataset.py", "compute_tableau_croise_groupes"): GROUPE,
    ("audit_groupe_dataset.py", "compute_plage_dates_groupes"): GROUPE,
    ("audit_groupe_dataset.py", "_md_section_tableau_croise_groupes"): GROUPE,
    ("audit_groupe_dataset.py", "_md_section_plage_dates_groupes"): GROUPE,
}

# --- Emplacements déclarés, côté interface ----------------------------------
#
# Clé : (fichier relatif à web/UI_finale, expression du receveur). L'expression
# est un ancrage plus stable qu'un numéro de ligne et dit à elle seule de quelle
# `chambre` il s'agit.

SITES_UI: dict[tuple[str, str], str] = {
    ("scripts/sync-data.mjs", "groupe"): GROUPE,
    # #329 : la projection de comparaison regroupe par (chambre, législature).
    # C'est le champ du SCHÉMA DE GROUPE — `schema_groupe.py` —, pas le scalaire
    # `chambre` d'un profil pivot que #493 met en retrait : une comparaison ne
    # traverse ni chambre ni législature, et la clé le dit.
    ("scripts/comparaison-groupes.mjs", "groupe"): GROUPE,
    # #329 : `buildGroupView` est parti avec la fiche par législature ; la page
    # de groupe lit désormais une PROJECTION de lignée, écrite au build.
    # `amendements-lignees.mjs` n'y retient que les maillons de l'Assemblée —
    # l'index des amendements ne couvre pas le Sénat (#528).
    ("scripts/amendements-lignees.mjs", "groupe"): GROUPE,
    # La chambre d'une LIGNÉE (`schema_lignee.py`), recopiée au manifeste, à la
    # projection, et lue par la page pour écrire « Assemblée nationale » ou
    # « Sénat » dans son sourcil.
    ("scripts/sync-data.mjs", "lignee"): GROUPE,
    ("scripts/vue-lignee.mjs", "lignee"): GROUPE,
    ("src/components/LigneeProfile.jsx", "lignee"): GROUPE,
    # #969 : le titre d'une fiche de lignée nomme sa chambre, lue sur la projection.
    ("scripts/metadonnees-pages.mjs", "lignee"): GROUPE,
    # #969 : le bloc lisible sans JavaScript nomme la chambre de la lignée.
    ("scripts/bloc-sans-js.mjs", "vue"): GROUPE,
    # #1008 : le balisage Schema.org nomme l'organisation d'une lignée, et celle
    # d'un mandat — lue SUR LE MANDAT, comme la fiche candidat.
    ("scripts/donnees-structurees.mjs", "vue"): GROUPE,
    ("scripts/donnees-structurees.mjs", "mandat"): MANDAT,
    ("src/components/GovernmentProfile.jsx", "texte"): GROUPE,
    # #328 : la fiche candidat lit la chambre SUR LE MANDAT, jamais sur le
    # profil. `siegesElectifs` regroupe les enregistrements en sièges et
    # `rolesDuParcours` en tire le rôle affiché (« Député(e) », « Sénateur(rice) »).
    # C'est la source dont `chambres` dérive — elle ne migre pas, elle est ce
    # vers quoi on migre.
    ("src/utils/profilCandidat.js", "m"): MANDAT,
    # La projection de couverture (/couverture) lit elle aussi la chambre SUR LE
    # MANDAT : c'est ce qui tient le Sénat et le Parlement européen hors de la
    # piste « Assemblée nationale » de la frise, et leur donne leur propre ligne
    # — mandat publié, activité non collectée (#528).
    ("scripts/couverture-corpus.mjs", "m"): MANDAT,
    ("src/utils/profilCandidat.js", "existant"): MANDAT,
    ("src/utils/profilCandidat.js", "siege"): MANDAT,
    # #328 : la chambre voyage sur le RÔLE de la frise, à côté du banc, et
    # `pisteDuRole` la lit pour donner sa piste — donc sa teinte et sa colonne —
    # à un siège européen ou sénatorial. Elle vient de `siegesElectifs`, c'est-à-dire
    # du mandat : c'est la même donnée, transportée d'un cran, jamais le scalaire
    # `chambre` du profil que #493 met en retrait.
    ("src/utils/profilCandidat.js", "role"): MANDAT,
    # #815 : la barre grise les deux fiches du Sénat — collecte suspendue depuis
    # le 24/08/2026, Sénat hors périmètre éditorial. La chambre lue est celle du
    # SCHÉMA DE GROUPE, portée par le manifeste, jamais le scalaire d'un profil
    # pivot : une pastille de groupe ne connaît aucun profil.
    ("src/components/GroupsBar.jsx", "group"): GROUPE,
    # #329 : une entrée par LIGNÉE DÉCLARÉE, lue au manifeste — le chaînage de
    # `succede_a` refait ici (l'accès `tete`) est parti. La chambre sert à
    # griser les deux lignées du Sénat dans la barre.
    ("src/data/index.js", "l"): GROUPE,
    # Les sigles des sièges se lisent sur les fiches de groupe de l'Assemblée
    # du manifeste (`avecSiglesDeSiege`, maquette « En bref » du 11/09/2026).
    ("src/data/index.js", "g"): GROUPE,
}

# Le dernier consommateur du champ profil de l'interface — `chambreLabel(
# pivot.chambre, actif)`, qui fabriquait le libellé de profession de repli
# (« Député », « Ancien(ne) sénateur ») — a disparu avec la refonte de la fiche
# candidat (#328) : elle ne publie plus une chambre de profil mais le rôle de
# CHAQUE siège, tiré de `mandats[].chambre`. Sur un profil bicaméral, les deux
# chambres apparaissent donc, chacune à sa place et à sa date, ce qui était
# exactement la question éditoriale posée par l'épic.


# --- Scanners ---------------------------------------------------------------


def _fonction_englobante(arbre: ast.AST) -> dict[int, str]:
    """`id(nœud)` -> nom de la fonction qui le contient (`<module>` sinon)."""
    proprietaire: dict[int, str] = {}

    def descendre(noeud: ast.AST, fonction: str) -> None:
        for enfant in ast.iter_child_nodes(noeud):
            courante = fonction
            if isinstance(enfant, (ast.FunctionDef, ast.AsyncFunctionDef)):
                courante = enfant.name
            proprietaire[id(enfant)] = courante
            descendre(enfant, courante)

    descendre(arbre, "<module>")
    return proprietaire


def _scanner_python() -> dict[tuple[str, str], list[int]]:
    """Tout usage de la clé `"chambre"` dans `src/*.py`, par (module, fonction).

    Trois formes sont reconnues, et ce sont les trois par lesquelles un
    dictionnaire JSON se lit ou s'écrit en Python : `x.get("chambre")`,
    `x["chambre"]` (lecture comme écriture) et la clé d'un littéral `{...}`.
    """
    trouves: dict[tuple[str, str], list[int]] = {}

    for chemin in sorted(SRC.glob("*.py")):
        arbre = ast.parse(chemin.read_text(encoding="utf-8"))
        proprietaire = _fonction_englobante(arbre)

        def noter(noeud: ast.AST, ligne: int) -> None:
            cle = (chemin.name, proprietaire.get(id(noeud), "<module>"))
            trouves.setdefault(cle, []).append(ligne)

        for noeud in ast.walk(arbre):
            if (
                isinstance(noeud, ast.Call)
                and isinstance(noeud.func, ast.Attribute)
                and noeud.func.attr == "get"
                and noeud.args
                and isinstance(noeud.args[0], ast.Constant)
                and noeud.args[0].value == "chambre"
            ):
                noter(noeud, noeud.lineno)
            elif (
                isinstance(noeud, ast.Subscript)
                and isinstance(noeud.slice, ast.Constant)
                and noeud.slice.value == "chambre"
            ):
                noter(noeud, noeud.lineno)
            elif isinstance(noeud, ast.Dict):
                for cle_litterale in noeud.keys:
                    if (
                        isinstance(cle_litterale, ast.Constant)
                        and cle_litterale.value == "chambre"
                    ):
                        noter(noeud, cle_litterale.lineno)

    return trouves


#: `\bchambre\b` et non `chambre` : sans la frontière de mot, `chambre_depot_initial`
#: (la chambre de dépôt d'un texte, champ distinct) serait comptée comme un accès
#: à `chambre`.
_MOTIF_UI = re.compile(r"([A-Za-z_$][\w$]*(?:\??\.[A-Za-z_$][\w$]*)*)\.chambre\b")
_SUFFIXES_UI = frozenset({".js", ".jsx", ".mjs", ".ts", ".tsx"})
_REPERTOIRES_IGNORES_UI = frozenset({"node_modules", "dist", "build"})


def _scanner_ui() -> dict[tuple[str, str], list[int]]:
    """Tout accès `<expr>.chambre` sous `web/UI_finale`, par (fichier, receveur).

    `web/old/` est hors périmètre : ce sont des générations archivées de
    l'interface (AGENTS.md §1), qui ne lisent plus le pivot.
    """
    trouves: dict[tuple[str, str], list[int]] = {}
    if not UI.exists():
        return trouves

    for chemin in sorted(UI.rglob("*")):
        if not chemin.is_file() or chemin.suffix not in _SUFFIXES_UI:
            continue
        if _REPERTOIRES_IGNORES_UI.intersection(chemin.parts):
            continue
        relatif = chemin.relative_to(UI).as_posix()
        for numero, ligne in enumerate(
            chemin.read_text(encoding="utf-8").splitlines(), 1
        ):
            for occurrence in _MOTIF_UI.finditer(ligne):
                trouves.setdefault((relatif, occurrence.group(1)), []).append(numero)

    return trouves


def _formatter(emplacements: dict[tuple[str, str], list[int]]) -> str:
    return "\n".join(
        f"  - {a} :: {b} (ligne(s) {', '.join(str(n) for n in lignes)})"
        for (a, b), lignes in sorted(emplacements.items())
    )


# --- Le garde-fou -----------------------------------------------------------


def test_tout_emplacement_du_scalaire_chambre_est_declare_python():
    """Aucun usage de `"chambre"` dans `src/` qui ne soit catégorisé ci-dessus.

    Un emplacement neuf casse ce test : son auteur doit dire de quelle `chambre`
    il parle. C'est le seul mécanisme qui empêche un consommateur de se rajouter
    en silence pendant la coexistence — et donc qui empêche la coexistence de
    devenir définitive.
    """
    trouves = _scanner_python()

    inconnus = {cle: lignes for cle, lignes in trouves.items() if cle not in SITES_PYTHON}
    assert not inconnus, (
        "Emplacement(s) de la clé `chambre` non déclaré(s) dans SITES_PYTHON :\n"
        + _formatter(inconnus)
        + "\n\nAjoute chacun avec sa catégorie. S'il lit la `chambre` d'un PROFIL "
        "pivot, migre-le vers `schema_pivot.lire_chambres()` plutôt que de le "
        "déclarer CONSOMMATEUR_PROFIL : le scalaire est en cours de retrait (#494)."
    )


def test_aucun_emplacement_declare_n_a_disparu_python():
    """La liste ne survit pas à ce qu'elle décrit.

    Une déclaration qui reste après la disparition de son emplacement redevient
    du commentaire, et la prochaine lecture y croira.
    """
    trouves = _scanner_python()

    disparus = {cle: SITES_PYTHON[cle] for cle in SITES_PYTHON if cle not in trouves}
    assert not disparus, (
        "Emplacement(s) déclaré(s) dans SITES_PYTHON mais introuvable(s) — "
        "retire-les :\n"
        + "\n".join(f"  - {a} :: {b} ({categorie})" for (a, b), categorie in sorted(disparus.items()))
    )


def test_tout_acces_chambre_de_l_interface_est_declare():
    """Même règle côté `web/UI_finale`.

    Le recensement de #486 puis de #494 ne couvrait que `src/*.py`. L'interface
    lit pourtant le pivot, et c'est là que se trouve le dernier consommateur du
    scalaire — voir SITES_UI.
    """
    trouves = _scanner_ui()

    inconnus = {cle: lignes for cle, lignes in trouves.items() if cle not in SITES_UI}
    assert not inconnus, (
        "Accès `.chambre` non déclaré(s) dans SITES_UI :\n" + _formatter(inconnus)
    )

    disparus = {cle: SITES_UI[cle] for cle in SITES_UI if cle not in trouves}
    assert not disparus, (
        "Accès déclaré(s) dans SITES_UI mais introuvable(s) — retire-les :\n"
        + "\n".join(f"  - {a} :: {b} ({categorie})" for (a, b), categorie in sorted(disparus.items()))
    )


def test_condition_1_de_retrait_pipeline_python():
    """**Le pipeline a fini de migrer** : plus un seul consommateur du profil.

    C'est la moitié atteignable de la condition 1 par #494. Elle est vraie
    depuis cette issue : `check_quality_gate` (2 filtres de population) et
    `audit_pivot_dataset` (4 indicateurs) lisent `chambres` via
    `schema_pivot.lire_chambres()`.
    """
    restants = {
        cle: categorie
        for cle, categorie in SITES_PYTHON.items()
        if categorie == CONSOMMATEUR_PROFIL
    }
    assert not restants, (
        "Consommateur(s) du champ profil restant(s) dans src/ :\n"
        + "\n".join(f"  - {a} :: {b}" for a, b in sorted(restants))
        + "\n\nMigre-les vers `schema_pivot.lire_chambres()`."
    )


def test_condition_1_de_retrait_etat_global():
    """**Condition 1 remplie** : plus aucun consommateur du champ profil.

    Le test disait, jusqu'au 01/09/2026, l'inverse — il attendait exactement un
    consommateur, `pivotAdapter.chambreLabel`, et sa docstring annonçait qu'il
    échouerait le jour où celui-ci disparaîtrait. Il a échoué, et c'était le
    signal prévu : la refonte de la fiche candidat (#328) a supprimé le libellé
    de profession de repli, seule chose qui lisait encore `pivot.chambre`.

    Un test qui échoue pour dire « c'est fini » plutôt qu'une note dans un
    journal : c'est la différence entre un transitoire qui se termine et les
    replis de #431/#432, qui ne se sont jamais terminés.

    **Ce qui reste avant de retirer le scalaire** — hors périmètre de #328,
    parce qu'aucune de ces deux étapes ne se vérifie côté interface : la
    condition 2 se lit sur un run réel (l'avertissement « chambres du profil non
    corroborée » absent du corpus), puis le champ et la branche de repli de
    `lire_chambres()` partent ensemble.
    """
    restants = sorted(
        cle for cle, categorie in {**SITES_PYTHON, **SITES_UI}.items()
        if categorie == CONSOMMATEUR_PROFIL
    )

    assert restants == [], (
        "Un consommateur du champ profil est réapparu :\n"
        + "\n".join(f"  - {a} :: {b}" for a, b in restants)
        + "\n\nLa condition 1 de retrait de `chambre` était remplie "
        "(docs/decisions/chambres-profil-derivees.md) ; lis la chambre sur "
        "`mandats[].chambre` (#492) ou via `schema_pivot.lire_chambres()`, "
        "jamais sur le scalaire du profil."
    )


@pytest.mark.parametrize(
    "module, symboles",
    [
        ("check_quality_gate", ("lire_chambres",)),
        ("audit_pivot_dataset", ("lire_chambres",)),
    ],
)
def test_les_consommateurs_migres_passent_par_la_porte_unique(module, symboles):
    """Les deux modules migrés importent bien le lecteur canonique.

    Sans cette vérification, un consommateur pourrait « migrer » vers
    `profil.get("chambres")` en direct et rouvrir la question que
    `lire_chambres()` ferme : que vaut la lecture sur les 209 profils publiés
    qui ne portent pas encore `chambres` ?
    """
    importe = __import__(module)
    for symbole in symboles:
        assert hasattr(importe, symbole), (
            f"{module} n'importe pas {symbole} de schema_pivot."
        )
