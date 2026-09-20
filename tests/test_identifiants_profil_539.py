"""L'`id` est le slug, et les identifiants de source sont publiés à côté (#539).

#487 avait retiré le préfixe `nosdeputes:`/`europarl:` de l'`id` parce qu'il
était **instable** — il dérivait de la chambre qui avait répondu ce jour-là.
Mais l'information qu'il portait, « d'où vient cette personne », était vraie ;
elle était simplement rangée dans l'identité au lieu d'être nommée. #539 la
range dans `identifiants`, et régularise les 20 `id` que #487 n'avait pas
réécrits (19 sénateurs en `nosdeputes:<slug>`, `jordan-bardella` en
`europarl:131580`).

Ce que ces tests tiennent :

  1. le bloc porte **toujours ses quatre clés**, `null` compris — une clé
     absente laisserait choisir entre « pas d'identifiant » et « le producteur
     n'y a pas pensé » ;
  2. `identifiants.hatvp` est la **recopie** d'`identite.uri_hatvp`, et rien
     d'autre ne peut s'y glisser — en particulier pas le marqueur XML brut
     d'AMO30 que **186 des 476 profils publiés** portent dans ce champ ;
  3. l'`id` d'un profil européen **suit son slug**, ce qui rend la
     régularisation de `jordan-bardella` durable au lieu de tenir un run ;
  4. la fusion ne fait **jamais** régresser un identifiant vers `null`.

Aucune lecture de `pivot_data/` ni de `raw_data/profiles/` : ces tests tournent
en CI, où le corpus est absent du disque (#473).
"""

import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from merge_profile import merge_pivot_profile  # noqa: E402
from normalize_europarl import normalize_europarl  # noqa: E402
from normalize_profil import normalize_profil  # noqa: E402
from schema_pivot import (  # noqa: E402
    KNOWN_IDENTIFIANTS,
    ORDRE_IDENTIFIANTS,
    identifiants_vides,
    make_empty_profil,
    poser_identifiant,
    valider_identifiants,
    validate_profil,
)

#: Le marqueur `xsi:nil` d'AMO30, tel qu'il arrive dans `identite.uri_hatvp`
#: après conversion XML→JSON. Ce n'est pas une hypothèse : 186 des 476 profils
#: publiés le portaient au 27/08/2026, contre 279 vraies URI et 11 champs vides
#: — **191 sur 481** à la re-mesure du 29/08. La mesure de « 465 profils avec
#: `uri_hatvp` » qui circulait comptait les marqueurs comme renseignés.
#:
#: Le défaut a été fermé **à l'extraction** par #556 (`_champ_identite_an`), qui
#: a aussi trouvé le marqueur dans `profession` et `lieu_naissance`. Les tests de
#: ce fichier restent : ils tiennent le comportement du normaliseur face à une
#: valeur fautive, qui est ce qui protège le corpus tant qu'un profil non
#: régénéré porte encore l'ancienne.
NIL_AMO30 = {"@xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance", "@xsi:nil": "true"}


def _brut(**identite) -> dict:
    """Profil brut minimal au format `candidate_profile.build_profile()`."""
    champs = {
        "nom_complet": "Marie Martin",
        "groupe_sigle": "SOC",
        "url_an_ou_senat": "https://www2.assemblee-nationale.fr/deputes/fiche/OMC_PA123456",
    }
    champs.update(identite)
    return {
        "slug": "marie-martin",
        "chambre": "deputes",
        "source": "https://data.assemblee-nationale.fr/",
        "identite": champs,
        "mandats": [],
        "votes": [],
        "interventions": [],
        "amendements": [],
        "dossiers_legislatifs": [],
        "meta": {"genere_le": "2026-08-28T12:00:00+0000", "synchro_sources": {}},
    }


def _brut_ue() -> dict:
    return {
        "identifiant_pe": 131580,
        "nom_complet": "Jordan BARDELLA",
        "url_source": "https://www.europarl.europa.eu/meps/fr/131580",
        "mandats_europeens": [],
        "meta": {"genere_le": "2026-08-28T12:00:00+0000"},
    }


# ---------------------------------------------------------------------------
# 1. Le bloc porte toujours ses quatre clés
# ---------------------------------------------------------------------------

def test_un_profil_vide_porte_les_quatre_cles_a_null():
    """`null` dit « aucun identifiant connu ». Une clé absente ne dit rien."""
    assert make_empty_profil("x", "X")["identifiants"] == {
        "an": None, "senat": None, "europarl": None, "hatvp": None
    }


def test_l_ordre_des_cles_couvre_exactement_la_nomenclature():
    """Sans quoi un référentiel ajouté à l'un et pas à l'autre serait publié
    dans un ordre instable, ou pas publié du tout."""
    assert set(ORDRE_IDENTIFIANTS) == KNOWN_IDENTIFIANTS
    assert len(ORDRE_IDENTIFIANTS) == len(KNOWN_IDENTIFIANTS)


def test_un_bloc_incomplet_est_refuse_en_nommant_ce_qui_manque():
    erreurs = valider_identifiants({"an": "PA1", "hatvp": None})
    assert erreurs and "senat" in erreurs[0] and "europarl" in erreurs[0]


def test_un_referentiel_inconnu_est_refuse():
    bloc = identifiants_vides() | {"wikidata": "Q42"}
    assert any("wikidata" in e for e in valider_identifiants(bloc))


@pytest.mark.parametrize("cle, valeur", [
    ("an", "847629"),                    # l'id Syceron nu, le défaut de #510
    ("an", "nosdeputes:marie-martin"),   # l'ancien préfixe, s'il revenait par là
    ("europarl", "europarl:131580"),
    ("hatvp", "hatvp.fr/pages/x"),
])
def test_une_forme_invalide_est_refusee(cle, valeur):
    bloc = identifiants_vides() | {cle: valeur}
    assert any(cle in e and "forme" in e for e in valider_identifiants(bloc))


# ---------------------------------------------------------------------------
# 2. `poser_identifiant` : la seule fabrique, et elle ne régresse jamais
# ---------------------------------------------------------------------------

def test_poser_un_identifiant_null_n_efface_pas_le_precedent():
    """Un profil AN + PE passe par deux normaliseurs ; le second ne doit pas
    effacer ce que le premier a établi."""
    profil = make_empty_profil("x", "X")
    poser_identifiant(profil, "an", "PA1567")
    poser_identifiant(profil, "an", None)
    poser_identifiant(profil, "an", "   ")
    assert profil["identifiants"]["an"] == "PA1567"


def test_poser_un_identifiant_hors_nomenclature_leve():
    with pytest.raises(ValueError, match="senat_ancien|référentiel connu"):
        poser_identifiant(make_empty_profil("x", "X"), "senat_ancien", "S1")


def test_poser_une_valeur_non_chaine_leve_plutot_que_de_la_serialiser():
    """**Le garde-fou des 186.** Un `str(valeur)` obligeant aurait publié le
    marqueur XML d'AMO30 comme identifiant HATVP sur 186 profils — et le schéma
    ne l'aurait pas rattrapé, puisque la valeur serait devenue une chaîne."""
    with pytest.raises(TypeError, match="uri_hatvp|chaîne"):
        poser_identifiant(make_empty_profil("x", "X"), "hatvp", NIL_AMO30)


# ---------------------------------------------------------------------------
# 3. La normalisation FR : `an` publié, `hatvp` recopié
# ---------------------------------------------------------------------------

def test_l_acteur_ref_de_la_table_est_publie_tel_quel():
    """« Le `PA` cesse d'être ré-résolu par correspondance de nom à chaque run :
    il est publié. »"""
    pivot = normalize_profil(_brut(), acteur_ref="PA1567")
    assert pivot["identifiants"]["an"] == "PA1567"


def test_sans_table_l_acteur_ref_est_relu_dans_l_url_de_fiche_deja_collectee():
    """Même fait, même source. Ne rien écrire quand on le connaît serait une
    donnée perdue, pas une donnée manquante."""
    assert normalize_profil(_brut())["identifiants"]["an"] == "PA123456"


def test_une_url_sans_acteur_ref_ne_produit_aucun_identifiant_invente():
    pivot = normalize_profil(_brut(url_an_ou_senat="https://www.assemblee-nationale.fr/"))
    assert pivot["identifiants"]["an"] is None


def test_la_table_prime_sur_l_url_collectee():
    """La table est relue et prouvée ; l'URL est un sous-produit de collecte."""
    pivot = normalize_profil(_brut(), acteur_ref="PA999")
    assert pivot["identifiants"]["an"] == "PA999"


def test_hatvp_est_recopie_et_identite_le_garde():
    """`uri_hatvp` reste dans `identite` pour ne pas casser les lecteurs."""
    uri = "https://www.hatvp.fr/pages_nominatives/martin-marie"
    pivot = normalize_profil(_brut(uri_hatvp=uri))
    assert pivot["identifiants"]["hatvp"] == uri
    assert pivot["identite"]["uri_hatvp"] == uri


def test_le_marqueur_xml_d_amo30_ne_devient_jamais_un_identifiant():
    """186 profils sur 476. Un identifiant qui ne mène nulle part ne vaut pas
    mieux qu'une absence, il vaut moins (AGENTS.md §2 règles 2 et 5)."""
    pivot = normalize_profil(_brut(uri_hatvp=NIL_AMO30))
    assert pivot["identifiants"]["hatvp"] is None
    # …et le champ d'origine n'est PAS réparé ici : c'est un défaut de la
    # collecte d'identité, en amont, dont la correction réécrira 186 profils
    # publiés. Ce lot le contourne, il ne le masque pas.
    assert pivot["identite"]["uri_hatvp"] == NIL_AMO30


def test_un_hatvp_publie_qui_contredit_l_identite_est_refuse_par_le_schema():
    """Deux valeurs différentes voudraient dire qu'une des deux est fausse,
    sans dire laquelle."""
    pivot = normalize_profil(_brut(uri_hatvp="https://www.hatvp.fr/a"))
    pivot["identifiants"]["hatvp"] = "https://www.hatvp.fr/b"
    assert any("contredit" in e for e in validate_profil(pivot))


# ---------------------------------------------------------------------------
# 4. La branche européenne : l'`id` suit le slug, l'identifiant PE est nommé
# ---------------------------------------------------------------------------

def test_l_identifiant_pe_est_publie_dans_identifiants():
    pivot = normalize_europarl(_brut_ue(), slug="jordan-bardella")
    assert pivot["id"] == "jordan-bardella"
    assert pivot["identifiants"]["europarl"] == "131580"


def test_sans_slug_l_id_garde_l_identifiant_de_source_mais_le_publie_aussi():
    """Le repli de #487 est conservé — un identifiant de source explicite vaut
    mieux qu'un slug inventé depuis un nom collecté — mais il n'est plus la
    seule trace de l'identifiant PE."""
    pivot = normalize_europarl(_brut_ue())
    assert pivot["id"] == "europarl:131580"
    assert pivot["identifiants"]["europarl"] == "131580"


# ---------------------------------------------------------------------------
# 5. La fusion : clé par clé, jamais une régression vers null
# ---------------------------------------------------------------------------

def test_la_fusion_conserve_un_identifiant_que_le_nouveau_run_n_a_pas_resolu():
    """Une passe `--source an` ne rend pas l'`europarl`. Fusionner le bloc
    entier par `_prefer_non_empty` le perdrait."""
    ancien = normalize_profil(_brut(), acteur_ref="PA1567")
    ancien["identifiants"]["europarl"] = "131580"
    nouveau = normalize_profil(_brut(), acteur_ref="PA1567")

    fusionne = merge_pivot_profile(ancien, nouveau)
    assert fusionne["identifiants"] == {
        "an": "PA1567", "senat": None, "europarl": "131580", "hatvp": None
    }


def test_la_fusion_laisse_une_valeur_neuve_corriger_l_ancienne():
    ancien = normalize_profil(_brut(), acteur_ref="PA1")
    nouveau = normalize_profil(_brut(), acteur_ref="PA2")
    assert merge_pivot_profile(ancien, nouveau)["identifiants"]["an"] == "PA2"


def test_la_fusion_n_invente_pas_de_bloc_sur_un_profil_qui_n_en_a_pas():
    """Les 476 profils publiés avant #539 n'en portent pas : la fusion ne doit
    pas leur en fabriquer un vide, qui se lirait « aucun identifiant connu »."""
    ancien = normalize_profil(_brut())
    ancien.pop("identifiants")
    nouveau = copy.deepcopy(ancien)
    assert "identifiants" not in merge_pivot_profile(ancien, nouveau)


# ---------------------------------------------------------------------------
# 6. Rétro-compatibilité : un profil sans le bloc reste valide
# ---------------------------------------------------------------------------

def test_un_profil_sans_bloc_identifiants_reste_valide():
    """Même précédent que `chambres` (#493) : les déclarer invalides ne dirait
    rien de vrai sur eux."""
    pivot = normalize_profil(_brut())
    pivot.pop("identifiants")
    assert validate_profil(pivot) == []
