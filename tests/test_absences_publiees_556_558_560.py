"""Trois absences publiées comme des faits (#556, #558, #560).

Le lot réunit trois défauts de **même forme** : une absence produite par une
décision, une frontière de source ou un marqueur XML était publiée comme un
fait. C'est le contresens que #539 existe pour empêcher.

Ce que ces tests tiennent, dans l'ordre d'importance :

  1. **#556 — un marqueur d'absence n'est jamais une valeur.** Le marqueur
     `xsi:nil` d'AMO30 est ramené à `null` **à l'extraction**, sur tout champ
     d'identité et pas seulement sur celui qui a été mesuré. Et il ne doit
     jamais atteindre une fonction qui *interpole* : là, il devient une chaîne
     qu'aucun contrôle de type ne rattrape plus ;
  2. **#556 — `validate_profil` SIGNALE la divergence au lieu de la
     neutraliser.** C'est le point du lot : la contrainte existait déjà et se
     taisait, parce qu'elle ne se déclenchait que si les deux champs étaient
     renseignés — or le second était `null`, précisément parce que le premier
     était fautif ;
  3. **#558 — une décision non déclarée retombe sur « couvert ».** Un profil
     dont le groupe est gelé publie `non_collecte`/`par_decision` sur ses cinq
     listes, avec une preuve LUE dans la config, jamais « couvert » ;
  4. **#558 — la population ne se lit ni sur `chambre` ni sur la provenance.**
     Les 20 sénateurs publient `chambre: "AN"`, et l'un d'eux est
     `candidat_declare`. L'appartenance se lit au groupe ;
  5. **#560 — une frontière de source n'est pas une avarie.** Un profil dont
     tous les mandats précèdent la XVe publie `hors_couverture` sur ses
     interventions, jamais `panne` : aucun run ne comblera ce silence ;
  6. **#560 — un zéro constaté est publiable.** Les archives qui répondent et
     ne portent rien rendent `couvert`, pas `non_collecte`.

Aucune lecture de `pivot_data/` ni de `raw_data/profiles/` (#473) : les fiches
de groupe des tests d'appartenance sont écrites dans un `tmp_path`.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import candidate_profile as cp  # noqa: E402
import couverture_profil as cv  # noqa: E402
import groupes_config as gc  # noqa: E402
import schema_groupe as sg  # noqa: E402
from schema_pivot import (  # noqa: E402
    CAUSE_PANNE,
    CAUSE_PAR_DECISION,
    ETAT_COUVERT,
    ETAT_HORS_COUVERTURE,
    ETAT_NON_COLLECTE,
    LISTES_COUVERTES,
    make_empty_profil,
    valider_couverture,
    validate_profil,
)

LE_JOUR = "2026-08-29"

#: Le marqueur, tel que le convertisseur XML → JSON d'AMO30 le rend.
MARQUEUR = {
    "@xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "@xsi:nil": "true",
}

#: Sa forme interpolée — celle qui a atteint 28 profils publiés via
#: `_format_lieu_naissance`, et qu'aucun `isinstance(..., str)` ne rattrape.
MARQUEUR_INTERPOLE = (
    "{'@xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance', "
    "'@xsi:nil': 'true'}"
)


def _profil(
    *,
    provenance="candidat_declare",
    warnings=(),
    mandats=(),
    slug="marie-martin",
) -> dict:
    profil = make_empty_profil(slug, "Marie Martin", provenance=provenance)
    profil["meta"]["warnings"] = list(warnings)
    profil["mandats"] = [dict(m) for m in mandats]
    return profil


def _mandat(debut, fin=None):
    return {"label": "Mandat parlementaire", "categorie": "mandat_electif",
            "debut": debut, "fin": fin}


def _etats(couverture, liste):
    return [e["etat"] for e in couverture[liste]]


# ---------------------------------------------------------------------------
# 1. #556 — un marqueur d'absence n'est jamais une valeur
# ---------------------------------------------------------------------------

def test_le_marqueur_nil_est_ramene_a_none_a_la_lecture():
    """La règle, sur la fonction qui la porte. Un marqueur n'est pas une donnée
    manquante *déguisée* : c'est une donnée manquante (AGENTS.md §2.5)."""
    assert cp._champ_identite_an(MARQUEUR) is None
    assert cp._champ_identite_an("https://www.hatvp.fr/x") == "https://www.hatvp.fr/x"
    assert cp._champ_identite_an("") is None
    assert cp._champ_identite_an(None) is None


def test_le_marqueur_n_atteint_jamais_une_fonction_qui_interpole():
    """**Le pire des trois champs, et la raison de la règle générale.**

    `_format_lieu_naissance` interpole ses arguments : un marqueur qui
    l'atteint ne ressort pas en `dict` repérable, mais en **chaîne**. 18
    profils publiés portaient un lieu de naissance intégralement fait de
    plomberie XML, et 10 autres une ville suivie d'un marqueur entre
    parenthèses. La garde vit dans la fonction, pas seulement chez l'appelant.
    """
    assert cp._format_lieu_naissance(MARQUEUR, MARQUEUR, MARQUEUR) is None
    assert cp._format_lieu_naissance("Chauny", MARQUEUR, None) == "Chauny"
    assert cp._format_lieu_naissance(MARQUEUR, "Aisne", None) == "Aisne"
    # Le cas nominal ne bouge pas.
    assert cp._format_lieu_naissance("Lille", "Nord", "France") == "Lille (Nord)"


def test_le_nom_complet_ne_peut_pas_devenir_du_xml():
    assert cp._format_nom_complet(MARQUEUR, MARQUEUR) is None
    assert cp._format_nom_complet(MARQUEUR, "Martin") == "Martin"
    assert cp._format_nom_complet("Marie", "Martin") == "Marie Martin"


def test_aucune_forme_interpolee_ne_subsiste_dans_un_lieu_de_naissance():
    """Le contrôle qui aurait vu le défaut : ce qui sort ne contient pas de
    namespace XML, quelle que soit la combinaison d'entrées."""
    for entrees in (
        (MARQUEUR, MARQUEUR, MARQUEUR),
        ("Vichy", MARQUEUR, MARQUEUR),
        (MARQUEUR, "Allier", "France"),
    ):
        rendu = cp._format_lieu_naissance(*entrees)
        assert rendu is None or "xsi" not in rendu


def test_un_contact_nil_ne_devient_pas_un_dict():
    """Un `mailto:` construit sur un dict est un lien mort. Le champ n'a jamais
    été mesuré au marqueur — c'est justement pourquoi il est gardé : le
    convertisseur ne connaît pas le nom du champ."""
    contact = cp._extract_contact([
        {"typeLibelle": "Mèl", "valElec": MARQUEUR},
        {"typeLibelle": "Twitter", "valElec": "@martin"},
    ])
    assert contact["email"] is None
    assert contact["twitter"] == "@martin"


def test_les_index_deriveS_d_amo30_sont_versionnes():
    """Un correctif sur ce qui est ÉCRIT dans un index reste sans effet tant que
    l'ancien fichier est relu — et il l'est, d'un run à l'autre, par le cache
    GitHub Actions (#550/#555). Le nom porte donc une version."""
    assert cp.NOM_INDEX_IDENTITE.endswith(".json")
    assert cp.NOM_INDEX_ORGANES.endswith(".json")
    assert cp.NOM_INDEX_IDENTITE != "index_identite.json"
    assert cp.NOM_INDEX_ORGANES != "index_organes.json"


# ---------------------------------------------------------------------------
# 2. #556 — `validate_profil` SIGNALE, il ne neutralise pas
# ---------------------------------------------------------------------------

def _profil_avec_uri(valeur, hatvp=None) -> dict:
    profil = make_empty_profil("marie-martin", "Marie Martin")
    profil["identite"] = {
        "profession": None, "date_naissance": None, "lieu_naissance": None,
        "num_circo": None, "uri_hatvp": valeur, "source_url": None,
    }
    profil["identifiants"] = {"an": None, "senat": None, "europarl": None,
                              "hatvp": hatvp}
    return profil


def test_le_marqueur_dans_uri_hatvp_est_signale_et_non_neutralise():
    """**Le cœur de #556.**

    La contrainte de recopie ne se déclenchait que si les DEUX champs étaient
    renseignés. `_uri_hatvp_publiable` ramenant le marqueur à `None`, le couple
    était (marqueur, `None`), le second falsy, la comparaison sautée : 191
    profils sur 481 passaient la validation en publiant un dict là où le schéma
    annonce un lien. La règle porte désormais sur la forme du champ lui-même.
    """
    erreurs = validate_profil(_profil_avec_uri(MARQUEUR))
    assert any("identite.uri_hatvp" in e for e in erreurs), erreurs
    assert any("xsi:nil" in e or "URI" in e for e in erreurs), erreurs


def test_une_uri_hatvp_reelle_reste_valide():
    profil = _profil_avec_uri("https://www.hatvp.fr/x", hatvp="https://www.hatvp.fr/x")
    assert [e for e in validate_profil(profil) if "hatvp" in e] == []


def test_une_absence_declaree_se_publie_null_et_passe():
    assert [e for e in validate_profil(_profil_avec_uri(None)) if "hatvp" in e] == []


def test_une_uri_renseignee_et_un_identifiant_vide_sont_une_divergence():
    """L'autre moitié du couple : les deux champs sortent de la même fabrique,
    donc l'écart ne peut venir que d'une valeur jugée impubliable sans que le
    champ d'origine soit corrigé."""
    erreurs = validate_profil(_profil_avec_uri("https://www.hatvp.fr/x", hatvp=None))
    assert any("identifiants.hatvp est vide" in e for e in erreurs), erreurs


def test_une_uri_hatvp_qui_n_est_pas_une_uri_est_refusee():
    erreurs = validate_profil(_profil_avec_uri("pas une uri"))
    assert any("identite.uri_hatvp" in e for e in erreurs), erreurs


# ---------------------------------------------------------------------------
# 3. #558 — le gel d'un groupe est une décision, pas un « couvert »
# ---------------------------------------------------------------------------

SUSPENSION = {
    "depuis": "2026-08-24",
    "motif": "Certificat TLS expiré sur archive.nossenateurs.fr ; #528 a depuis "
             "sorti le Sénat du périmètre éditorial.",
    "references": ["#528", "#516"],
    "condition_reprise": "Réactivation du périmètre Sénat.",
}

GROUPE_SUSPENDU = {
    "groupe_id": "Senat:LR", "groupe_sigle": "LR", "chambre": "Senat",
    "roster_chambre": "senateurs", "fichier": "groupe-Senat-LR.json",
    "extraction_suspendue": SUSPENSION,
}

GROUPE_ACTIF = {
    "groupe_id": "AN:SOC", "groupe_sigle": "SOC", "chambre": "AN",
    "roster_chambre": "deputes", "fichier": "groupe-AN-SOC.json",
}


def test_la_decision_groupe_suspendu_existe_et_porte_les_cinq_listes():
    """Elle manquait, et une décision qui manque n'est pas une décision absente :
    c'est une décision publiée comme un fait."""
    listes, _ = cv.DECISIONS_PIPELINE[cv.DECISION_GROUPE_SUSPENDU]
    assert set(listes) == set(LISTES_COUVERTES)


def test_un_profil_de_groupe_gele_ne_publie_jamais_couvert():
    """`charles-guene` publiait « couvert depuis 2002, zéro mandat » — ce qui se
    lit « cette personne n'a pas de mandat ». C'est faux : l'extraction de son
    groupe est gelée depuis le 24/08/2026."""
    couverture = cv.deriver(
        _profil(provenance="roster_groupe"),
        constate_le=LE_JOUR,
        groupe_suspendu=cv.groupe_suspendu_depuis_config(GROUPE_SUSPENDU),
    )
    assert valider_couverture(couverture) == []
    for liste in LISTES_COUVERTES:
        assert _etats(couverture, liste) == [ETAT_NON_COLLECTE], liste
        assert couverture[liste][0]["cause"] == CAUSE_PAR_DECISION
        assert ETAT_COUVERT not in _etats(couverture, liste)


def test_la_preuve_du_gel_est_lue_dans_la_config_pas_codee_en_dur():
    """Une preuve recopiée à la main divergerait le jour où la suspension est
    levée. Les quatre champs exigés par `anomalies_suspension` existent pour
    être relus — c'est ici qu'ils le sont."""
    preuve = cv.deriver(
        _profil(),
        constate_le=LE_JOUR,
        groupe_suspendu=cv.groupe_suspendu_depuis_config(GROUPE_SUSPENDU),
    )["mandats"][0]["preuve"]
    assert "Senat:LR" in preuve
    assert SUSPENSION["depuis"] in preuve
    assert "archive.nossenateurs.fr" in preuve
    assert "#528" in preuve


def test_le_gel_prime_sur_les_drapeaux_357_qui_n_expliquent_que_deux_listes():
    """Sur un profil `roster_groupe` d'un groupe gelé, les deux drapeaux de #357
    sont vrais aussi — mais ils n'expliquent que deux listes sur cinq. Le gel les
    englobe, et c'est lui que le lecteur doit trouver en preuve."""
    couverture = cv.deriver(
        _profil(provenance="roster_groupe"),
        constate_le=LE_JOUR,
        groupe_suspendu=cv.groupe_suspendu_depuis_config(GROUPE_SUSPENDU),
    )
    for liste in ("interventions", "textes_portes"):
        assert "Senat:LR" in couverture[liste][0]["preuve"], liste


def test_un_profil_de_groupe_gele_a_des_mandats_ne_bascule_pas_en_couvert():
    """Le gel ne dépend pas de ce que les listes contiennent : 11 des 20
    sénateurs ont des mandats, et publient pourtant sur des listes vides par
    ailleurs. La condition porte sur la décision, jamais sur le résultat."""
    couverture = cv.deriver(
        _profil(mandats=[_mandat("2017-06-21")]),
        constate_le=LE_JOUR,
        groupe_suspendu=cv.groupe_suspendu_depuis_config(GROUPE_SUSPENDU),
    )
    for liste in LISTES_COUVERTES:
        assert _etats(couverture, liste) == [ETAT_NON_COLLECTE], liste


def test_sans_gel_la_derivation_ne_change_pas():
    """Le garde-fou de non-régression : 461 profils sur 481 ne sont pas
    concernés, et rien ne doit bouger pour eux."""
    couverture = cv.deriver(_profil(mandats=[_mandat("2022-06-22")]),
                            constate_le=LE_JOUR)
    assert _etats(couverture, "votes") == [ETAT_COUVERT, ETAT_HORS_COUVERTURE]


# ---------------------------------------------------------------------------
# 4. #558 — l'appartenance se lit au GROUPE, pas sur `chambre` ni la provenance
# ---------------------------------------------------------------------------

def _ecrire_fiche(dossier: Path, fichier: str, membres: list[str]) -> None:
    (dossier / fichier).write_text(
        json.dumps({"membres": [{"membre_id": m} for m in membres]},
                   ensure_ascii=False),
        encoding="utf-8",
    )


def test_l_appartenance_se_lit_dans_la_fiche_publiee_du_groupe(tmp_path):
    """Un groupe suspendu n'est plus interrogé : sa composition n'existe plus
    que dans la fiche déjà publiée. C'est la source sur laquelle #558 a mesuré
    sa population, et la seule qui les rende tous les vingt."""
    _ecrire_fiche(tmp_path, "groupe-Senat-LR.json",
                  ["charles-guene", "bruno-retailleau"])
    _ecrire_fiche(tmp_path, "groupe-AN-SOC.json", ["jerome-guedj"])

    index = gc.index_membres_de_groupes_suspendus(
        [GROUPE_SUSPENDU, GROUPE_ACTIF], tmp_path
    )
    assert set(index) == {"charles-guene", "bruno-retailleau"}
    assert index["bruno-retailleau"]["groupe_id"] == "Senat:LR"


def test_le_membre_de_provenance_candidat_declare_n_est_pas_manque(tmp_path):
    """**Le piège mesuré.** 19 des 20 sont `roster_groupe` ; le vingtième —
    `bruno-retailleau`, le plus visible — est `candidat_declare`. Un correctif
    branché sur la provenance seule l'aurait manqué."""
    _ecrire_fiche(tmp_path, "groupe-Senat-LR.json", ["bruno-retailleau"])
    index = gc.index_membres_de_groupes_suspendus([GROUPE_SUSPENDU], tmp_path)

    couverture = cv.deriver(
        _profil(provenance="candidat_declare", slug="bruno-retailleau"),
        constate_le=LE_JOUR,
        groupe_suspendu=cv.groupe_suspendu_depuis_config(index["bruno-retailleau"]),
    )
    assert _etats(couverture, "mandats") == [ETAT_NON_COLLECTE]
    assert couverture["mandats"][0]["cause"] == CAUSE_PAR_DECISION


def test_une_fiche_absente_ne_fait_pas_echouer_l_index(tmp_path):
    """Ce module n'est pas le garde-fou du fichier publié — `audit_diff_profils`
    l'est déjà (#460/#470). Une fiche manquante rend zéro membre, pas une
    exception qui coûterait la génération d'un profil."""
    assert gc.index_membres_de_groupes_suspendus([GROUPE_SUSPENDU], tmp_path) == {}


# ---------------------------------------------------------------------------
# 5. #558 — l'état de couverture d'un roster de groupe
# ---------------------------------------------------------------------------

def _fiche_groupe(couverture_roster: dict) -> dict:
    fiche = sg.make_empty_profil_groupe("Senat:LR", "LR", "Les Républicains",
                                        "Senat", None)
    fiche["meta"]["couverture_roster"] = couverture_roster
    return fiche


def test_hors_perimetre_exige_sa_preuve():
    """Dire qu'un groupe est hors périmètre sans dire par quelle décision est
    exactement le défaut que cet état existe pour corriger."""
    erreurs = sg.validate_profil_groupe(
        _fiche_groupe({"roster_total": 235, "profils_disponibles": 15,
                       "etat": sg.ETAT_ROSTER_HORS_PERIMETRE})
    )
    assert any("couverture_roster.preuve" in e for e in erreurs), erreurs


def test_hors_perimetre_avec_preuve_est_valide():
    erreurs = sg.validate_profil_groupe(
        _fiche_groupe({"roster_total": 235, "profils_disponibles": 15,
                       "etat": sg.ETAT_ROSTER_HORS_PERIMETRE,
                       "preuve": "extraction suspendue depuis 2026-08-24 (#516, #528)"})
    )
    assert [e for e in erreurs if "couverture_roster" in e] == []


def test_un_etat_inconnu_est_refuse():
    erreurs = sg.validate_profil_groupe(
        _fiche_groupe({"roster_total": 235, "profils_disponibles": 15,
                       "etat": "partiel"})
    )
    assert any("couverture_roster.etat" in e for e in erreurs), erreurs


def test_une_fiche_sans_etat_reste_valide():
    """Les fiches publiées avant ce lot n'en portent pas : les déclarer
    invalides ne dirait rien de vrai sur elles (même précédent que #539)."""
    erreurs = sg.validate_profil_groupe(
        _fiche_groupe({"roster_total": 62, "profils_disponibles": 60})
    )
    assert [e for e in erreurs if "couverture_roster" in e] == []


# ---------------------------------------------------------------------------
# 6. #560 — une frontière de source n'est pas une avarie
# ---------------------------------------------------------------------------

def test_tous_les_mandats_avant_la_xve_donnent_hors_couverture_sur_interventions():
    """**Le test que #560 demande.** Le mandat de Ségolène Royal relève de la
    XIIe et Syceron commence à la XVe : la `panne` était fausse **par
    construction**, pas seulement mal choisie. Aucun run ne comblera ce
    silence."""
    profil = _profil(
        mandats=[_mandat("2002-06-19", "2007-06-19"), _mandat("2014-04-03", "2017-05-17")],
        warnings=["interventions syceron indisponibles : ConnectionError"],
    )
    couverture = cv.deriver(profil, constate_le=LE_JOUR)

    assert _etats(couverture, "interventions") == [ETAT_HORS_COUVERTURE]
    assert couverture["interventions"][0].get("cause") is None
    assert valider_couverture(couverture) == []


def test_la_preuve_du_hors_couverture_nomme_la_limite_de_la_source():
    """« Voilà ce que nous avons ingéré » se lit comme un choix révisable ;
    « l'Assemblée nationale ne publie pas » dit qu'on ne le pourra jamais. La
    constante du dépôt reste nommée, en second, comme trace d'implémentation
    (AGENTS.md §2.2)."""
    preuve = cv.deriver(
        _profil(mandats=[_mandat("2002-06-19", "2007-06-19")]),
        constate_le=LE_JOUR,
    )["interventions"][0]["preuve"]

    assert "Assemblée nationale" in preuve
    assert "SYCERON_AVAILABLE_LEGISLATURES" in preuve
    assert preuve.index("Assemblée nationale") < preuve.index("SYCERON_AVAILABLE")
    assert "XIIe" in preuve  # les législatures du profil, nommées


def test_la_frontiere_prime_sur_une_panne_declaree():
    """Une panne survenue par ailleurs ne dit rien d'une liste qui n'a jamais pu
    être remplie. C'est le sens de « distinguer les deux cas AVANT de poser la
    cause »."""
    profil = _profil(
        mandats=[_mandat("2002-06-19", "2007-06-19")],
        warnings=["interventions syceron indisponibles : SSLError"],
    )
    assert _etats(cv.deriver(profil, constate_le=LE_JOUR), "interventions") == [
        ETAT_HORS_COUVERTURE
    ]


def test_un_mandat_qui_intersecte_la_borne_garde_la_forme_a_deux_entrees():
    """Édouard Philippe : sa fonction gouvernementale court jusqu'en 2020, donc
    elle recoupe la XVe. Sa page publie `couvert` + `hors_couverture` — la forme
    que l'issue demande — et le correctif ne doit pas la lui retirer."""
    profil = _profil(mandats=[_mandat("2012-06-20", "2017-06-15"),
                              _mandat("2017-06-20", "2020-07-06")])
    couverture = cv.deriver(profil, constate_le=LE_JOUR)
    assert _etats(couverture, "interventions") == [ETAT_COUVERT, ETAT_HORS_COUVERTURE]


def test_sans_mandat_date_aucune_derivation_par_les_legislatures():
    """La moitié importante du contrat : un profil sans mandat daté ne dit rien
    de sa carrière. Les 9 profils à `mandats: []` gardent la forme générale,
    exactement comme #539 l'avait obtenue."""
    assert cv.legislatures_du_profil(_profil()) == ()
    couverture = cv.deriver(_profil(), constate_le=LE_JOUR)
    assert _etats(couverture, "interventions") == [ETAT_COUVERT, ETAT_HORS_COUVERTURE]


@pytest.mark.parametrize("debut, fin, attendues", [
    ("2002-06-19", "2007-06-19", (12,)),
    ("2012-06-20", "2017-06-15", (14,)),
    # 2017-06-20 est le DERNIER jour de la XIVe : le mandat la touche.
    ("2017-06-20", "2020-07-06", (14, 15)),
    ("2024-07-18", None, (17,)),
    ("2002-06-19", None, (12, 13, 14, 15, 16, 17)),
])
def test_les_legislatures_d_un_mandat_sont_celles_qu_il_recoupe(debut, fin, attendues):
    assert cv.legislatures_du_profil(_profil(mandats=[_mandat(debut, fin)])) == attendues


# ---------------------------------------------------------------------------
# 7. #560 — un zéro constaté est publiable, et le préfixe est scindé
# ---------------------------------------------------------------------------

def test_les_deux_etats_ont_deux_prefixes_distincts():
    """Un préfixe ne doit plus recouvrir deux états. C'est la leçon déjà tirée
    pour `WARNING_PREFIX_VOTES_INTROUVABLES` pendant #539."""
    assert (
        cp.WARNING_PREFIX_INTERVENTIONS_SYCERON_AUCUNE
        != cp.WARNING_PREFIX_INTERVENTIONS_SYCERON_INDISPONIBLES
    )
    assert not cp.WARNING_PREFIX_INTERVENTIONS_SYCERON_AUCUNE.startswith(
        cp.WARNING_PREFIX_INTERVENTIONS_SYCERON_INDISPONIBLES
    )


def test_les_archives_qui_repondent_et_ne_portent_rien_rendent_couvert():
    """Un zéro constaté est publiable (AGENTS.md §2.5). Le nouveau préfixe ne
    condamne aucune liste."""
    profil = _profil(
        mandats=[_mandat("2022-06-22")],
        warnings=[
            f"{cp.WARNING_PREFIX_INTERVENTIONS_SYCERON_AUCUNE} : les archives "
            "Syceron ont répondu et ne portent aucune intervention pour cet "
            "acteurRef."
        ],
    )
    couverture = cv.deriver(profil, constate_le=LE_JOUR)
    assert _etats(couverture, "interventions") == [ETAT_COUVERT, ETAT_HORS_COUVERTURE]


def test_une_archive_injoignable_reste_une_panne():
    """Le pendant : la panne existe, et elle doit continuer de se dire. Le
    correctif retire une confusion, pas un signal."""
    profil = _profil(
        mandats=[_mandat("2022-06-22")],
        warnings=[
            f"{cp.WARNING_PREFIX_INTERVENTIONS_SYCERON_INDISPONIBLES} : "
            "ConnectionError sur l'archive de la 17e législature"
        ],
    )
    couverture = cv.deriver(profil, constate_le=LE_JOUR)
    assert _etats(couverture, "interventions") == [ETAT_NON_COLLECTE]
    assert couverture["interventions"][0]["cause"] == CAUSE_PANNE


def test_l_ancien_message_du_corpus_publie_n_est_plus_lu_comme_une_panne():
    """Le pont vers le corpus déjà committé : les 481 profils bruts portent
    encore le constat sous le préfixe de panne, et la passe pivot les relit à
    chaque run. Sans cette reconnaissance, « panne » serait republié sur un zéro
    constaté jusqu'à la prochaine collecte complète."""
    profil = _profil(
        mandats=[_mandat("2022-06-22")],
        warnings=[
            "interventions syceron indisponibles : aucune intervention Syceron "
            "pour cet acteurRef (identifiant absent des trois archives, ou "
            "archive indisponible)."
        ],
    )
    couverture = cv.deriver(profil, constate_le=LE_JOUR)
    assert _etats(couverture, "interventions") == [ETAT_COUVERT, ETAT_HORS_COUVERTURE]


# ---------------------------------------------------------------------------
# 8. La passe de migration : ce qu'elle répare, et ce qu'elle refuse de faire
# ---------------------------------------------------------------------------

import migrer_absences_publiees_556_558_560 as mig  # noqa: E402


def test_l_objet_marqueur_redevient_null():
    assert mig.est_marqueur_nil(MARQUEUR) is True
    assert mig.est_marqueur_nil({"@xsi:nil": "false"}) is False
    assert mig.est_marqueur_nil("Lille") is False
    assert mig.nettoyer_valeur(MARQUEUR) is None


def test_la_forme_interpolee_se_repare_par_motif_et_garde_la_vraie_donnee():
    """La ville reste, le complément absent part. C'est le complément qui est
    nil, pas la ville — retirer les deux perdrait une donnée collectée."""
    assert mig.nettoyer_valeur(f"Chauny ({MARQUEUR_INTERPOLE})") == "Chauny"
    assert mig.nettoyer_valeur(f"{MARQUEUR_INTERPOLE} ({MARQUEUR_INTERPOLE})") is None
    assert mig.nettoyer_valeur("Lille (Nord)") == "Lille (Nord)"
    assert mig.nettoyer_valeur(None) is None


def test_le_bloc_identite_entier_est_parcouru_pas_seulement_les_trois_mesures():
    """Le convertisseur XML ne connaît pas le nom du champ, donc la règle de
    réparation ne doit pas le connaître non plus."""
    profil = {"identite": {"uri_hatvp": MARQUEUR, "profession": MARQUEUR,
                           "lieu_naissance": f"Vichy ({MARQUEUR_INTERPOLE})",
                           "num_circo": MARQUEUR, "date_naissance": "1952-04-06"}}
    changes = mig._nettoyer_identite(profil)

    assert set(changes) == {"uri_hatvp", "profession", "lieu_naissance", "num_circo"}
    assert profil["identite"]["uri_hatvp"] is None
    assert profil["identite"]["lieu_naissance"] == "Vichy"
    assert profil["identite"]["date_naissance"] == "1952-04-06"


def test_la_migration_refuse_de_tourner_sans_referentiel_prouve_charge(
    tmp_path, monkeypatch
):
    """**Le garde-fou du script.**

    Sans AMO30 mesuré, `etablir_fait_hors_an` rend une panne (condition C1,
    #484), et les 4 profils qui publient « jamais élu·e à l'Assemblée
    nationale » basculeraient en « nous n'avons pas réussi à collecter » — le
    contresens que ce lot corrige, produit par le script qui le corrige.

    ## Pourquoi ce test DIT son monde au lieu d'en hériter (#767)

    Le cache AMO30 se lit à `Path(".cache") / …`, **relatif au répertoire
    courant**. Sans `chdir`, ce test constatait celui du poste : vert sur une
    machine vierge et sur la CI, rouge dès qu'une collecte locale avait tourné —
    c'est-à-dire au moment précis où on vérifie qu'on n'a rien cassé.

    `monkeypatch.chdir(tmp_path)` est l'idiome que dix autres tests appliquent
    déjà, et que `conftest` nomme : le garde-fou de #721 **diagnostique** la
    lecture du cache du poste, il ne la redirige pas. Sans ce `chdir`, il levait
    ici `CacheDuPosteLuDansUnTest` — c'est-à-dire qu'il faisait exactement son
    travail.
    """
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as echec:
        mig.migrer_pivots(tmp_path, {}, {}, constate_le=LE_JOUR, ecrire=False)
    assert "fait_etabli" in str(echec.value)
