"""#642 — un destinataire déclaré par avertissement, fermé, obligatoire, validé.

Aucun test ici ne lit `pivot_data/` ni `raw_data/profiles/` et aucun ne sort sur
le réseau (AGENTS.md §3b) : les chiffres du corpus vivent dans
`docs/decisions/destinataire-avertissements-642.md`, pas dans une assertion.
"""

import ast
import copy
import json
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
SRC = RACINE / "src"
sys.path.insert(0, str(SRC))

from avertissements import (  # noqa: E402
    AVERTISSEMENTS_HERITES,
    PREFIXES_HERITES,
    DESTINATAIRE_INTERNE,
    DESTINATAIRE_LECTEUR,
    DESTINATAIRES_AVERTISSEMENT,
    Avertissement,
    avertissement,
    deriver_avertissements,
    destinataire_de,
    unir_tables_avertissements,
)
from merge_profile import (  # noqa: E402
    FAMILLES_WARNINGS,
    _PREFIXE_PARLTRACK_AUCUNE_DONNEE,
    _PREFIXE_PARLTRACK_DIAGNOSTIC,
    REGLES_META,
    fusionner_meta,
    merge_pivot_profile,
)
from candidate_profile import WARNING_PREFIX_VOTES_INTROUVABLES  # noqa: E402
from normalize_parltrack_dumps import (  # noqa: E402
    WARNING_PREFIX_PARLTRACK_AUCUNE_DONNEE,
    WARNING_PREFIX_PARLTRACK_DIAGNOSTIC,
)
from schema_pivot import valider_avertissements  # noqa: E402


# ---------------------------------------------------------------------------
# Le vocabulaire : fermé, deux valeurs, pas de troisième
# ---------------------------------------------------------------------------

def test_le_vocabulaire_est_ferme_et_compte_exactement_deux_valeurs():
    """Un avertissement qui s'adresse aux deux s'écrit deux fois.

    Une valeur « mixte » rendrait à l'interface le tri qu'elle n'a pas su
    faire, avec un nom de plus — c'est le point de l'issue.
    """
    assert DESTINATAIRES_AVERTISSEMENT == {DESTINATAIRE_LECTEUR, DESTINATAIRE_INTERNE}
    assert len(DESTINATAIRES_AVERTISSEMENT) == 2


def test_la_fabrique_refuse_un_destinataire_hors_nomenclature():
    with pytest.raises(ValueError, match="destinataire d'avertissement inconnu"):
        avertissement("un message", "mixte")


def test_la_fabrique_n_a_pas_de_destinataire_par_defaut():
    """Un site d'écriture qui ne sait pas à qui il parle doit le décider."""
    with pytest.raises(TypeError):
        avertissement("un message")  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Le typage voyage sans rien casser
# ---------------------------------------------------------------------------

def test_un_avertissement_typé_reste_une_chaine_pour_tous_les_consommateurs():
    a = avertissement(
        f"{WARNING_PREFIX_VOTES_INTROUVABLES} : rien.", DESTINATAIRE_LECTEUR
    )
    assert isinstance(a, str)
    assert a.startswith(WARNING_PREFIX_VOTES_INTROUVABLES)
    assert a == f"{WARNING_PREFIX_VOTES_INTROUVABLES} : rien."
    assert json.loads(json.dumps([a])) == [f"{WARNING_PREFIX_VOTES_INTROUVABLES} : rien."]


def test_une_copie_profonde_ne_perd_pas_le_destinataire():
    """Sans `__deepcopy__`, la perte serait silencieuse — la régression même
    que ce lot existe pour éviter."""
    a = avertissement("un message", DESTINATAIRE_INTERNE)
    assert destinataire_de(copy.deepcopy(a)) == DESTINATAIRE_INTERNE
    assert destinataire_de(copy.copy(a)) == DESTINATAIRE_INTERNE
    profil = copy.deepcopy({"meta": {"warnings": [a]}})
    assert destinataire_de(profil["meta"]["warnings"][0]) == DESTINATAIRE_INTERNE


def test_une_chaine_nue_n_est_pas_interne_par_defaut():
    assert destinataire_de("un message sans origine") is None


# ---------------------------------------------------------------------------
# `meta.avertissements` : aligné, complet, jamais muet
# ---------------------------------------------------------------------------

def test_le_jumeau_est_aligne_entree_par_entree_dans_le_meme_ordre():
    meta = {"warnings": [
        avertissement("premier", DESTINATAIRE_LECTEUR),
        avertissement("second", DESTINATAIRE_INTERNE),
    ]}
    deriver_avertissements(meta)
    assert meta["avertissements"] == [
        {"message": "premier", "destinataire": "lecteur"},
        {"message": "second", "destinataire": "interne"},
    ]
    assert valider_avertissements(meta["avertissements"], meta["warnings"]) == []


def test_aucun_avertissement_n_est_perdu_au_typage():
    """Le garde-fou de l'issue : `audit_diff_profils` ne surveille pas
    `meta.warnings`, donc rien d'autre ne bloquerait une disparition."""
    warnings = [f"message {i}" for i in range(7)]
    meta = {"warnings": list(warnings)}
    deriver_avertissements(meta)
    assert [e["message"] for e in meta["avertissements"]] == warnings


def test_un_message_que_personne_n_a_type_est_publie_a_null_jamais_omis():
    meta = {"warnings": ["une chaîne relue du disque"]}
    deriver_avertissements(meta)
    entree = meta["avertissements"][0]
    assert entree == {"message": "une chaîne relue du disque", "destinataire": None}
    assert "destinataire" in entree


def test_le_bloc_est_ecrit_meme_vide():
    """Sa présence dit « passé par le lot, rien à déclarer » ; son absence dit
    « profil antérieur »."""
    meta = {"warnings": []}
    deriver_avertissements(meta)
    assert meta["avertissements"] == []


def test_le_bloc_deja_publie_retype_une_chaine_relue_du_disque():
    """C'est le pont de l'aller-retour JSON entre le profil brut et le pivot."""
    meta = {
        "warnings": ["un constat"],
        "avertissements": [{"message": "un constat", "destinataire": "lecteur"}],
    }
    deriver_avertissements(meta)
    assert meta["avertissements"] == [
        {"message": "un constat", "destinataire": "lecteur"}
    ]


def test_la_table_des_avertissements_herites_type_ce_qu_aucun_code_n_ecrit_plus():
    message = next(iter(AVERTISSEMENTS_HERITES))
    meta = {"warnings": [message]}
    deriver_avertissements(meta)
    assert meta["avertissements"][0]["destinataire"] == AVERTISSEMENTS_HERITES[message]


def test_le_prefixe_herite_type_l_ancien_message_parltrack():
    """Le seul préfixe hérité, et il ne recouvre qu'un énoncé — c'est la
    condition pour déroger au message entier."""
    ancien = (
        "ParlTrack: aucune donnée trouvée pour le MEP ID 96742. "
        "Vérifier la disponibilité des dumps ou la validité du MEP ID."
    )
    meta = {"warnings": [ancien]}
    deriver_avertissements(meta)
    assert meta["avertissements"][0]["destinataire"] == "lecteur"


def test_aucun_prefixe_herite_ne_recouvre_deux_registres():
    """`votes introuvables` couvre un constat ET une panne : un préfixe pareil
    n'a pas sa place ici, et c'est pourquoi la table principale est indexée sur
    le message entier (#484)."""
    assert len(PREFIXES_HERITES) == 1
    for prefixe, _ in PREFIXES_HERITES:
        assert not prefixe.startswith(WARNING_PREFIX_VOTES_INTROUVABLES)


def test_la_table_des_herites_est_indexee_sur_le_message_entier():
    """Jamais sur un préfixe : `votes introuvables` couvre un constat ET une
    panne, qui ne s'adressent pas à la même personne (#484)."""
    for message in AVERTISSEMENTS_HERITES:
        meta = {"warnings": [message + " suite inattendue"]}
        deriver_avertissements(meta)
        assert meta["avertissements"][0]["destinataire"] is None


# ---------------------------------------------------------------------------
# La validation : fermée, obligatoire, alignée
# ---------------------------------------------------------------------------

def test_validation_refuse_un_destinataire_hors_nomenclature():
    erreurs = valider_avertissements(
        [{"message": "m", "destinataire": "mixte"}], ["m"]
    )
    assert any("destinataire non reconnu" in e for e in erreurs)


def test_validation_refuse_une_entree_sans_cle_destinataire():
    """`null` dit « inconnu » ; l'omission ne dit rien. C'est le « si et
    seulement si » de `couverture[].cause` (#539)."""
    erreurs = valider_avertissements([{"message": "m"}], ["m"])
    assert any("ne déclare pas de destinataire" in e for e in erreurs)


def test_validation_accepte_un_destinataire_null():
    assert valider_avertissements([{"message": "m", "destinataire": None}], ["m"]) == []


def test_validation_refuse_une_cle_hors_nomenclature():
    erreurs = valider_avertissements(
        [{"message": "m", "destinataire": None, "niveau": "grave"}], ["m"]
    )
    assert any("hors nomenclature" in e for e in erreurs)


def test_validation_refuse_un_jumeau_desaligne():
    erreurs = valider_avertissements(
        [{"message": "m", "destinataire": "interne"}], ["m", "n"]
    )
    assert any("aligné sur `meta.warnings`" in e for e in erreurs)


def test_validation_refuse_un_message_qui_ne_reprend_pas_le_warning():
    erreurs = valider_avertissements(
        [{"message": "autre chose", "destinataire": "interne"}], ["m"]
    )
    assert any("ne reprend pas" in e for e in erreurs)


def test_le_bloc_absent_est_tolere_sur_les_profils_deja_publies():
    """481 profils publiés portent des avertissements sans destinataire.
    Un schéma qui n'accepte plus ce qu'il a écrit hier est une perte."""
    from schema_pivot import make_empty_profil, validate_profil

    profil = make_empty_profil("un-slug", "Un Nom", "AN")
    profil["meta"].pop("avertissements")
    profil["meta"]["warnings"] = ["un avertissement d'avant le lot"]
    assert not [e for e in validate_profil(profil) if "avertissement" in e]


# ---------------------------------------------------------------------------
# La fusion (#600) : le typage survit à l'union, et s'éteint avec le message
# ---------------------------------------------------------------------------

def test_meta_avertissements_a_une_regle_nommee_dans_regles_meta():
    """#600 refuse qu'une clé de `meta` soit prise au hasard."""
    assert "avertissements" in REGLES_META


def _pivot(warnings, avertissements=None):
    meta = {"schema_version": "1", "warnings": list(warnings)}
    if avertissements is not None:
        meta["avertissements"] = avertissements
    return {
        "id": "un-slug", "nom": "Un Nom", "chambre": "AN", "sources": [],
        "mandats": [], "votes": [], "textes_portes": [], "interventions": [],
        "amendements": [], "tags_thematiques": [], "meta": meta,
    }


def test_un_avertissement_ramene_de_l_ancien_profil_garde_son_destinataire():
    """Sans l'union des tables, il reparaîtrait sans destinataire : la fusion
    ne conserve du côté non retenu que la chaîne."""
    ancien = _pivot(
        ["constat de l'ancien écrivain"],
        [{"message": "constat de l'ancien écrivain", "destinataire": "lecteur"}],
    )
    neuf = _pivot([avertissement("constat du nouvel écrivain", DESTINATAIRE_INTERNE)])
    fusionne = merge_pivot_profile(ancien, neuf)
    par_message = {
        e["message"]: e["destinataire"] for e in fusionne["meta"]["avertissements"]
    }
    assert par_message["constat de l'ancien écrivain"] == "lecteur"
    assert par_message["constat du nouvel écrivain"] == "interne"


def test_un_avertissement_eteint_par_les_donnees_perd_aussi_son_entree():
    """L'extinction de #600 doit rester vraie du jumeau : une entrée typée sans
    avertissement publié serait un orphelin, et la validation la refuse."""
    ancien = _pivot([f"{WARNING_PREFIX_VOTES_INTROUVABLES} : rien trouvé."])
    neuf = _pivot([])
    neuf["votes"] = [{"scrutin_id": "an:leg16:1", "position": "pour"}]
    fusionne = merge_pivot_profile(ancien, neuf)
    meta = fusionne["meta"]
    assert not any(
        w.startswith(WARNING_PREFIX_VOTES_INTROUVABLES) for w in meta["warnings"]
    )
    assert not any(
        e["message"].startswith(WARNING_PREFIX_VOTES_INTROUVABLES)
        for e in meta["avertissements"]
    )
    assert valider_avertissements(meta["avertissements"], meta["warnings"]) == []


def test_le_jumeau_reste_aligne_apres_fusion():
    ancien = _pivot(["un message de l'ancien"])
    neuf = _pivot([avertissement("un message du neuf", DESTINATAIRE_INTERNE)])
    fusionne = merge_pivot_profile(ancien, neuf)
    meta = fusionne["meta"]
    assert valider_avertissements(meta["avertissements"], meta["warnings"]) == []


def test_la_regle_de_fusion_deduplique_sur_le_message():
    unis = unir_tables_avertissements(
        [{"message": "m", "destinataire": "interne"}],
        [{"message": "m", "destinataire": "lecteur"},
         {"message": "n", "destinataire": "lecteur"}],
    )
    assert unis == [
        {"message": "m", "destinataire": "interne"},
        {"message": "n", "destinataire": "lecteur"},
    ]


def test_fusionner_meta_ne_perd_pas_la_table_de_l_ecrivain_non_retenu():
    fusionne = fusionner_meta(
        {"warnings": ["ancien"],
         "avertissements": [{"message": "ancien", "destinataire": "lecteur"}]},
        {"warnings": ["neuf"],
         "avertissements": [{"message": "neuf", "destinataire": "interne"}]},
    )
    messages = {e["message"] for e in fusionne["avertissements"]}
    assert messages == {"ancien", "neuf"}


# ---------------------------------------------------------------------------
# ParlTrack : l'avertissement qui s'écrit deux fois
# ---------------------------------------------------------------------------

def test_les_deux_familles_parltrack_ne_sont_pas_prefixe_l_une_de_l_autre():
    """Sans quoi l'union par famille (#600) n'en publierait qu'une, et le lot
    aurait retiré un avertissement au lieu d'en typer deux."""
    a, b = WARNING_PREFIX_PARLTRACK_AUCUNE_DONNEE, WARNING_PREFIX_PARLTRACK_DIAGNOSTIC
    assert not a.startswith(b)
    assert not b.startswith(a)
    assert a in FAMILLES_WARNINGS
    assert b in FAMILLES_WARNINGS


def test_la_recopie_des_prefixes_parltrack_dans_merge_profile_na_pas_diverge():
    """`merge_profile` recopie les deux préfixes plutôt que de les importer :
    il est chargé par le portail de qualité et par tous les audits, et
    `normalize_parltrack_dumps` tire `zstandard` avec lui. C'est le prix de la
    recopie, et ce test est la façon dont on le paie."""
    assert _PREFIXE_PARLTRACK_AUCUNE_DONNEE == WARNING_PREFIX_PARLTRACK_AUCUNE_DONNEE
    assert _PREFIXE_PARLTRACK_DIAGNOSTIC == WARNING_PREFIX_PARLTRACK_DIAGNOSTIC


def test_la_famille_lecteur_couvre_le_message_publie_avant_le_lot():
    """L'ancienne forme est rangée dans la même famille que la nouvelle : elle
    est remplacée, pas conservée à côté."""
    ancien_message = (
        "ParlTrack: aucune donnée trouvée pour le MEP ID 96742. "
        "Vérifier la disponibilité des dumps ou la validité du MEP ID."
    )
    assert ancien_message.startswith(WARNING_PREFIX_PARLTRACK_AUCUNE_DONNEE)


def test_l_enrichissement_parltrack_ecrit_les_deux_avertissements(monkeypatch):
    import normalize_parltrack_dumps as npd

    monkeypatch.setattr(npd, "get_dossiers_for_mep", lambda *a, **k: [])
    monkeypatch.setattr(npd, "get_amendments_for_mep", lambda *a, **k: [])
    # #683 : deux lectures de plus, muettes ici — le cas testé est « la source
    # ne connaît personne », et il exige que TOUTES les listes soient vides.
    monkeypatch.setattr(npd, "get_votes_for_mep", lambda *a, **k: [])
    monkeypatch.setattr(npd, "get_activities_for_mep", lambda *a, **k: {})
    profil = {"sources": [], "textes_portes": [], "amendements": [],
              "votes": [], "interventions": [], "meta": {}}
    npd.enrich_pivot_with_parltrack(profil, 96742)

    par_destinataire = {
        e["destinataire"] for e in profil["meta"]["avertissements"]
    }
    assert par_destinataire == {"lecteur", "interne"}
    assert len(profil["meta"]["warnings"]) == 2


# ---------------------------------------------------------------------------
# Le verrou : aucun site d'écriture ne peut revenir à une chaîne nue
# ---------------------------------------------------------------------------

#: Les modules qui écrivent dans le `meta.warnings` d'un PROFIL (les fiches de
#: groupe, de gouvernement et de parti ont leurs propres schémas, hors de ce
#: lot). Le test lit le code **exécuté**, jamais les commentaires — même geste
#: que `tests/test_retrait_nosdeputes_529.py`.
MODULES_DU_CHEMIN_PROFIL = (
    "candidate_profile.py",
    "generate_all_profiles.py",
    "mep_profile.py",
    "merge_profile.py",
    "normalize_parltrack_dumps.py",
    "normalize_profil.py",
)


def _appels_append_sur_warnings(chemin: Path):
    """Les `…warnings.append(x)` du module, avec leur argument."""
    arbre = ast.parse(chemin.read_text(encoding="utf-8"))
    for noeud in ast.walk(arbre):
        if not isinstance(noeud, ast.Call):
            continue
        fonction = noeud.func
        if not (isinstance(fonction, ast.Attribute) and fonction.attr == "append"):
            continue
        cible = ast.unparse(fonction.value)
        if "warnings" not in cible or not noeud.args:
            continue
        yield noeud.lineno, cible, noeud.args[0]


def test_aucun_site_d_ecriture_n_appose_une_chaine_nue():
    """Le champ est obligatoire *à l'écriture*, pas seulement au schéma.

    Une régression ici serait invisible : le message serait publié, valide, et
    sans destinataire — donc invisible à l'interface, qui est exactement l'état
    que #642 corrige.
    """
    nus: list[str] = []
    for nom in MODULES_DU_CHEMIN_PROFIL:
        chemin = SRC / nom
        for ligne, cible, arg in _appels_append_sur_warnings(chemin):
            if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name):
                if arg.func.id == "avertissement":
                    continue
            if isinstance(arg, ast.Name):
                # Une variable déjà typée en amont (cas du warning à compteur de
                # #492, fabriqué avant le test qui décide de l'ajouter).
                continue
            nus.append(f"{nom}:{ligne} — {cible}.append({ast.unparse(arg)[:60]})")
    assert not nus, (
        "Ces sites ajoutent un avertissement sans destinataire déclaré ; la "
        "fabrique est `avertissements.avertissement(message, destinataire)` "
        f"(#642) :\n  " + "\n  ".join(nus)
    )


def test_chaque_module_du_chemin_profil_derive_le_jumeau():
    """Un module qui écrit des avertissements et n'appelle jamais
    `deriver_avertissements` publierait des chaînes sans bloc typé."""
    muets = [
        nom for nom in MODULES_DU_CHEMIN_PROFIL
        if "deriver_avertissements(" not in (SRC / nom).read_text(encoding="utf-8")
    ]
    assert not muets, (
        f"Ces modules écrivent des avertissements sans jamais recomposer "
        f"`meta.avertissements` : {muets}"
    )
