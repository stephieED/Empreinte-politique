"""Tests de `scripts/audit_fusion_blocs_599.py` (lot 0 de l'épic #598).

Un audit qui compte mal est pire qu'aucun audit : il publie un chiffre. Ces
tests éprouvent donc ses **détecteurs**, pas son formatage — chacun construit un
corpus minuscule dont la réponse attendue est connue, et vérifie que l'audit la
rend.

Trois pièges sont éprouvés nommément, parce que les trois ont déjà produit une
mesure fausse dans ce dépôt :

1. le marqueur `xsi:nil` compté comme une valeur renseignée (#539/#556) ;
2. les profils dont l'absence d'identité AN est **attendue** comptés dans le
   défaut (#539) ;
3. une population non nommée — ici, `nosdeputes` compté comme une source périmée
   alors que #529 ne l'écrit plus.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

_RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_RACINE / "src"))
sys.path.insert(0, str(_RACINE / "scripts"))

from audit_fusion_blocs_599 import (  # noqa: E402
    BLOCS_BRUT_LUS,
    BLOCS_PIVOT_LUS,
    HORS_DEFAUT,
    LISTES_PARLEMENTAIRES,
    charger_corpus,
    construire_rapport,
    identite_du_chemin_minimal,
    mesurer_identite,
    mesurer_synchro,
    mesurer_warnings,
    nombre_d_entrees,
    porte_des_donnees_parlementaires,
    projeter_pivot,
    projeter_socle,
    rendre_markdown,
    valeur_de_fond,
)

MARQUEUR_NIL = {
    "@xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "@xsi:nil": "true",
}


def _identite_minimale(nom: str = "Jean Test", parti: str = "Parti") -> dict:
    """La forme exacte de `generate_all_profiles.build_minimal_profile`."""
    return {
        "nom_complet": nom,
        "groupe_sigle": None,
        "groupe_nom": parti,
        "profession": None,
        "date_naissance": None,
        "num_circo": None,
        "nb_mandats": None,
        "url_an_ou_senat": None,
    }


def _identite_an() -> dict:
    """La forme de l'écrivain AN : dix clés, `lieu_naissance` et `uri_hatvp`
    comprises."""
    return {
        "nom_complet": "Jean Test",
        "groupe_sigle": "LFI",
        "groupe_nom": "La France insoumise",
        "profession": "Professeur",
        "date_naissance": "1951-08-19",
        "lieu_naissance": "Tanger",
        "num_circo": 4,
        "nb_mandats": 3,
        "uri_hatvp": "https://www.hatvp.fr/fiche/jean-test",
        "url_an_ou_senat": "https://www2.assemblee-nationale.fr/deputes/fiche/OMC_PA1234",
    }


# ---------------------------------------------------------------------------
# Les prédicats de base
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "valeur",
    [None, "", [], {}, MARQUEUR_NIL, "{'@xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance', '@xsi:nil': 'true'}"],
)
def test_valeur_de_fond_refuse_toutes_les_formes_d_absence(valeur):
    """Le marqueur XML d'AMO30 n'est pas une valeur.

    C'est la mesure fausse de #539 — « 465 profils portent `uri_hatvp` » quand
    186 portaient le marqueur. Un audit qui le recompte referait l'erreur.
    """
    assert valeur_de_fond(valeur) is None


def test_valeur_de_fond_garde_une_vraie_valeur():
    assert valeur_de_fond("Tanger") == "Tanger"
    assert (
        valeur_de_fond(
            "Chauny ({'@xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',"
            " '@xsi:nil': 'true'})"
        )
        == "Chauny"
    )


def test_valeur_de_fond_garde_un_zero_mesure():
    """`nb_mandats: 0` et `num_circo: 0` sont des valeurs, pas des absences.

    C'est §2.5 lue dans l'autre sens : si l'audit les traitait comme vides, il
    déclarerait « champ perdu » sur un champ correctement publié, et le lot
    suivant irait le « réparer » en republiant l'ancienne valeur.
    """
    assert valeur_de_fond(0) == 0


def test_identite_du_chemin_minimal_reconnait_le_squelette():
    assert identite_du_chemin_minimal(_identite_minimale()) is True


def test_identite_du_chemin_minimal_refuse_une_identite_an():
    assert identite_du_chemin_minimal(_identite_an()) is False


def test_identite_du_chemin_minimal_refuse_une_collecte_an_en_echec():
    """Une identité AN entièrement vide n'est PAS le squelette minimal.

    Elle a dix clés, pas huit : la distinction tient à la forme autant qu'au
    fond, sinon l'audit confondrait deux défauts différents et attribuerait à
    #484 des profils dont la collecte AN a simplement échoué.
    """
    vide = {champ: None for champ in _identite_an()}
    assert identite_du_chemin_minimal(vide) is False


def test_identite_du_chemin_minimal_refuse_un_squelette_enrichi():
    """Huit clés mais une profession : ce bloc a appris quelque chose d'une
    source, il n'est plus celui du chemin minimal."""
    enrichi = _identite_minimale() | {"profession": "Professeur"}
    assert identite_du_chemin_minimal(enrichi) is False


def test_porte_des_donnees_parlementaires():
    assert porte_des_donnees_parlementaires({"votes": [{"a": 1}]}) is True
    assert porte_des_donnees_parlementaires({"votes": [], "mandats": []}) is False


# ---------------------------------------------------------------------------
# Mesure 1 — identité
# ---------------------------------------------------------------------------

def test_mesure_1_compte_le_squelette_minimal_gagnant():
    """Le cas #484 : identité du chemin minimal, 1 016 votes dans le même
    fichier. L'écrivain qui n'avait rien a gagné sur celui qui avait tout."""
    bruts = {
        "jean-luc-melenchon": {
            "identite": _identite_minimale(),
            "votes": [{"numero_scrutin": 1}],
            "meta": {"warnings": []},
        }
    }
    mesure = mesurer_identite(bruts, {})
    constats = mesure["constats"]["brut_squelette_minimal"]
    assert [e["slug"] for e in constats] == ["jean-luc-melenchon"]
    assert mesure["nb_profils_touches"] == 1


def test_mesure_1_ne_compte_pas_un_squelette_sans_donnees_parlementaires():
    """Sans donnée collectée, le bloc pauvre n'a écrasé personne : il est le
    seul qui existe. Le compter gonflerait la mesure d'un défaut absent."""
    bruts = {"quelqu-un": {"identite": _identite_minimale(), "votes": [], "mandats": []}}
    assert mesurer_identite(bruts, {})["nb_profils_touches"] == 0


def test_mesure_1_compte_a_part_les_quatre_profils_attendus():
    """Les trois non-parlementaires de #539 et `jordan-bardella` ne sont jamais
    dans le défaut : leur identité nulle est un fait, pas une perte."""
    bruts = {
        slug: {"identite": _identite_minimale(), "mandats": [{"label": "m"}]}
        for slug in sorted(HORS_DEFAUT)
    }
    mesure = mesurer_identite(bruts, {})
    assert mesure["nb_profils_touches"] == 0
    assert mesure["hors_defaut_attendu"]["brut_squelette_minimal"] == sorted(HORS_DEFAUT)
    assert mesure["population_mesuree"] == 0


def test_mesure_1_repere_un_champ_pivot_null_que_le_brut_renseigne():
    bruts = {"depute": {"identite": _identite_an(), "votes": [{"n": 1}]}}
    pivots = {
        "depute": {
            "identite": {
                "profession": None,
                "date_naissance": "1951-08-19",
                "lieu_naissance": None,
                "num_circo": 4,
                "uri_hatvp": "https://www.hatvp.fr/fiche/jean-test",
                "source_url": "https://www2.assemblee-nationale.fr/",
            }
        }
    }
    perdus = mesurer_identite(bruts, pivots)["constats"]["pivot_champ_perdu"]
    assert perdus == [{"slug": "depute", "champs": ["lieu_naissance", "profession"]}]


def test_mesure_1_ne_signale_pas_un_marqueur_nil_comme_une_perte():
    """Le brut porte le marqueur, le pivot publie `null` : c'est exactement ce
    que #556 demande. Un audit qui l'appellerait une perte réclamerait la
    republication d'une absence comme si c'était une valeur (§2.5)."""
    brut_identite = _identite_an() | {"profession": MARQUEUR_NIL}
    bruts = {"depute": {"identite": brut_identite, "votes": [{"n": 1}]}}
    pivots = {
        "depute": {
            "identite": {
                "profession": None,
                "date_naissance": "1951-08-19",
                "lieu_naissance": "Tanger",
                "num_circo": 4,
                "uri_hatvp": "https://www.hatvp.fr/fiche/jean-test",
                "source_url": "https://x",
            }
        }
    }
    assert mesurer_identite(bruts, pivots)["constats"].get("pivot_champ_perdu") is None


def test_mesure_1_repere_uri_hatvp_null_avec_identifiant_renseigne():
    bruts = {"depute": {"identite": {"nom_complet": "X"}}}
    pivots = {
        "depute": {
            "identite": {"uri_hatvp": None, "source_url": "https://x"},
            "identifiants": {"hatvp": "https://www.hatvp.fr/fiche/x"},
        }
    }
    constats = mesurer_identite(bruts, pivots)["constats"]["hatvp_incoherent"]
    assert [e["slug"] for e in constats] == ["depute"]


def test_mesure_1_repere_un_pivot_sans_bloc_identite():
    bruts = {"depute": {"identite": _identite_an(), "votes": [{"n": 1}]}}
    pivots = {"depute": {"identite": None}}
    constats = mesurer_identite(bruts, pivots)["constats"]["pivot_identite_absente"]
    assert constats[0]["slug"] == "depute"
    assert "profession" in constats[0]["champs_connus_du_brut"]


# ---------------------------------------------------------------------------
# Mesure 2 — warnings
# ---------------------------------------------------------------------------

def test_mesure_2_compte_les_warnings_reduits_au_chemin_minimal():
    bruts = {
        "depute": {
            "votes": [{"n": 1}],
            "meta": {
                "genere_le": "2026-08-29T16:00:00+0000",
                "collecte_ecartee": [],
                "warnings": [
                    "aucun mandat français connu (slug absent du référentiel "
                    "Assemblée nationale, ou identité introuvable)"
                ],
            },
        }
    }
    mesure = mesurer_warnings(bruts, {}, "2026-08-29")
    assert [e["slug"] for e in mesure["constats"]["warnings_reduits_au_chemin_minimal"]] == ["depute"]


def test_mesure_2_ne_compte_pas_un_profil_qui_porte_aussi_d_autres_warnings():
    """Un `meta` qui porte le warning du chemin minimal **et** ceux de
    l'écrivain AN n'a rien perdu — c'est la cible de #600."""
    bruts = {
        "depute": {
            "votes": [{"n": 1}],
            "meta": {
                "genere_le": "2026-08-29T16:00:00+0000",
                "collecte_ecartee": [],
                "warnings": [
                    "aucun mandat français connu (…)",
                    "amendements indisponibles : …",
                ],
            },
        }
    }
    mesure = mesurer_warnings(bruts, {}, "2026-08-29")
    assert mesure["constats"].get("warnings_reduits_au_chemin_minimal") is None


def test_mesure_2_n_accuse_pas_les_profils_non_regeneres():
    """Dix-neuf sénateurs ne sont plus régénérés depuis #528 : leur `meta` est
    légitimement d'avant `collecte_ecartee` (#539). Les compter serait un
    chiffre juste sur la mauvaise population."""
    bruts = {
        "senateur": {
            "mandats": [{"label": "m"}],
            "meta": {"genere_le": "2026-08-19T10:00:00+0000", "warnings": []},
        }
    }
    mesure = mesurer_warnings(bruts, {}, "2026-08-29")
    assert mesure["constats"].get("collecte_ecartee_absente") is None
    assert mesure["non_regeneres_par_le_dernier_run"] == ["senateur"]


def test_mesure_2_accuse_un_meta_sans_collecte_ecartee_du_dernier_run():
    bruts = {
        "depute": {
            "votes": [{"n": 1}],
            "meta": {"genere_le": "2026-08-29T16:00:00+0000", "warnings": []},
        }
    }
    mesure = mesurer_warnings(bruts, {}, "2026-08-29")
    assert [e["slug"] for e in mesure["constats"]["collecte_ecartee_absente"]] == ["depute"]


def test_mesure_2_liste_les_warnings_du_brut_absents_du_pivot():
    bruts = {"depute": {"meta": {"genere_le": "2026-08-29T00:00:00+0000", "warnings": ["a", "b"]}}}
    pivots = {"depute": {"meta": {"warnings": ["b", "c"]}}}
    mesure = mesurer_warnings(bruts, pivots, "2026-08-29")
    assert mesure["warnings_du_brut_non_publies_au_pivot"] == [
        {"slug": "depute", "warnings": ["a"]}
    ]


# ---------------------------------------------------------------------------
# Mesure 3 — synchro_sources
# ---------------------------------------------------------------------------

def test_mesure_3_separe_la_source_retiree_des_sources_encore_ecrites():
    """`nosdeputes` n'est plus écrit depuis #529 : sa vieille valeur est un
    reliquat exact. Le mélanger aux trois sources AN publierait un compteur de
    « défauts » dont la majorité n'en sont pas."""
    bruts = {
        "reliquat": {
            "meta": {
                "genere_le": "2026-08-29T16:00:00+0000",
                "synchro_sources": {
                    "nosdeputes": "2026-08-19T10:00:00+0000",
                    "assemblee_nationale": "2026-08-29T15:59:00+0000",
                },
                "warnings": [],
            }
        },
        "vraie-perte": {
            "meta": {
                "genere_le": "2026-08-29T16:00:00+0000",
                "synchro_sources": {"assemblee_nationale": "2026-08-19T18:00:00+0000"},
                "warnings": [],
            }
        },
    }
    mesure = mesurer_synchro(bruts)
    assert mesure["nb_anterieure_au_genere_le"] == 2
    assert mesure["dont_source_retiree_seulement"] == ["reliquat"]
    assert [e["slug"] for e in mesure["dont_source_encore_ecrite"]] == ["vraie-perte"]
    assert mesure["retard_max_jours_par_source"]["assemblee_nationale"] == pytest.approx(9.92, abs=0.02)


def test_mesure_3_ignore_l_ecart_intra_run():
    """Quelques minutes entre la synchro et le `genere_le` du même profil, c'est
    l'ordonnancement normal d'un run, pas une reprise."""
    bruts = {
        "normal": {
            "meta": {
                "genere_le": "2026-08-29T16:00:00+0000",
                "synchro_sources": {"assemblee_nationale": "2026-08-29T15:40:00+0000"},
                "warnings": [],
            }
        }
    }
    assert mesurer_synchro(bruts)["nb_anterieure_au_genere_le"] == 0


def test_mesure_3_repere_un_meta_sans_bloc_synchro():
    bruts = {
        "depute": {
            "votes": [{"n": 1}],
            "meta": {"genere_le": "2026-08-29T16:00:00+0000", "warnings": []},
        }
    }
    assert mesurer_synchro(bruts)["meta_sans_synchro_sources"] == ["depute"]


def test_mesure_3_ne_compte_pas_les_quatre_profils_attendus_sans_synchro():
    bruts = {
        slug: {"mandats": [{"label": "m"}], "meta": {"genere_le": "2026-08-29T16:00:00+0000"}}
        for slug in sorted(HORS_DEFAUT)
    }
    assert mesurer_synchro(bruts)["meta_sans_synchro_sources"] == []


# ---------------------------------------------------------------------------
# Bout en bout : lecture du corpus et rendu
# ---------------------------------------------------------------------------

def test_charger_corpus_lit_un_profil_partitionne_et_ignore_les_fichiers_de_service(tmp_path):
    """La partition par législature (#580) et le checkpoint sont les deux
    pièges d'énumération. Un `json.load` direct sur le socle rendrait un profil
    sans amendements ; un `glob` naïf compterait `.generation_checkpoint.json`
    comme un profil et fausserait toutes les populations."""
    bruts = tmp_path / "raw"
    bruts.mkdir()
    (bruts / ".generation_checkpoint.json").write_text("{}", encoding="utf-8")
    socle = {
        "slug": "depute",
        "identite": _identite_an(),
        "votes": [{"numero_scrutin": 1}],
        "amendements_partitionnes": {
            "cle": "amendements",
            "total": 1,
            "tranches": [{"legislature": 16, "fichier": "16.json", "nb": 1}],
        },
        "meta": {"genere_le": "2026-08-29T16:00:00+0000", "warnings": []},
    }
    (bruts / "depute.json").write_text(json.dumps(socle), encoding="utf-8")
    (bruts / "depute").mkdir()
    (bruts / "depute" / "16.json").write_text(
        json.dumps({"amendements": [{"uid": "AMANR5L16PO1234B0001P1D1N1"}]}), encoding="utf-8"
    )

    pivots = tmp_path / "pivot"
    pivots.mkdir()
    (pivots / ".cache.pivot.json").write_text("{}", encoding="utf-8")
    (pivots / "depute.pivot.json").write_text(json.dumps({"id": "depute"}), encoding="utf-8")

    charges_bruts, charges_pivots, illisibles = charger_corpus(bruts, pivots)
    assert sorted(charges_bruts) == ["depute"]
    assert sorted(charges_pivots) == ["depute"]
    assert illisibles == []


def test_rapport_complet_est_serialisable_et_nomme_ses_populations(tmp_path):
    bruts = tmp_path / "raw"
    bruts.mkdir()
    (bruts / "depute.json").write_text(
        json.dumps({
            "identite": _identite_minimale(),
            "votes": [{"numero_scrutin": 1}],
            "meta": {
                "genere_le": "2026-08-29T16:00:00+0000",
                "synchro_sources": {"assemblee_nationale": "2026-08-19T18:00:00+0000"},
                "warnings": ["aucun mandat français connu (…)"],
            },
        }),
        encoding="utf-8",
    )
    pivots = tmp_path / "pivot"
    pivots.mkdir()
    (pivots / "depute.pivot.json").write_text(
        json.dumps({"identite": None, "meta": {"warnings": []}}), encoding="utf-8"
    )

    rapport = construire_rapport(bruts, pivots)
    json.dumps(rapport, ensure_ascii=False)  # ne doit pas lever

    assert rapport["mesure_1_identite"]["population_bruts"] == 1
    assert rapport["mesure_1_identite"]["profils_touches"] == ["depute"]
    assert rapport["mesure_2_warnings"]["profils_touches"] == ["depute"]
    assert rapport["mesure_3_synchro"]["nb_dont_source_encore_ecrite"] == 1

    markdown = rendre_markdown(rapport)
    assert "Population du défaut" in markdown
    assert "`depute`" in markdown


# ---------------------------------------------------------------------------
# Mémoire : le plafond est dans le test (#628)
# ---------------------------------------------------------------------------
#
# Cet audit a été livré « rejouable » par #599 et ne l'était pas : il rangeait
# chaque profil pivot **entier** dans un dictionnaire indexé par slug, soit
# 623 Mo de JSON désérialisés puis conservés. Mesuré sur le corpus committé du
# 30/08/2026 : le pic dépassait 2,5 Gio avant même le 235e des 481 pivots, pour
# un pic complet extrapolé à ~3,9 Gio (facteur de gonflement mesuré : × 4,2).
# Sur une machine à 7,6 Gio dont 4 disponibles et le swap saturé, le noyau le
# tuait — `exit 137`, aucun rapport.
#
# Le défaut est **latent** : il ne se voit que sur une machine chargée. C'est
# exactement ce qu'un test doit rattraper, sinon on ne le réapprend qu'en
# relançant l'outil le jour où on en a besoin.

#: Profils du corpus-fixture de mesure. Assez nombreux pour que le coût
#: **transitoire** d'un seul document (celui qu'on désérialise puis relâche)
#: soit un ordre de grandeur sous le plafond.
NB_PROFILS_FIXTURE = 24

#: Poids visé, par profil, des blocs que l'audit doit relâcher — côté pivot
#: (`amendements`, `interventions`, `couverture`) et côté brut (`votes`).
POIDS_LOURD_PIVOT = 2 * 1024 * 1024
POIDS_LOURD_BRUT = 1 * 1024 * 1024

#: Plancher de vraisemblance du corpus-fixture. Rétrécir les fixtures
#: rétrécirait le plafond avec elles, et le test finirait par passer sur un
#: corpus si petit qu'il ne prouverait plus rien. 40 Mio est la limite basse
#: sous laquelle ce test doit refuser de se prononcer.
PLANCHER_POIDS_RELACHE = 40 * 1024 * 1024

#: Ce que le processus enfant exécute : il mesure **son propre** pic mémoire
#: (`ru_maxrss`, sans dépendance externe) de part et d'autre de l'audit, et
#: rend la croissance. Un sous-processus est nécessaire : dans le processus
#: pytest, `ru_maxrss` porterait aussi le pic de tous les tests précédents.
_PILOTE = """\
import json, resource, sys
from pathlib import Path

depot, dossier_bruts, dossier_pivots = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, str(Path(depot) / "src"))
sys.path.insert(0, str(Path(depot) / "scripts"))
import audit_fusion_blocs_599 as audit

depart = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
rapport = audit.construire_rapport(Path(dossier_bruts), Path(dossier_pivots))
pic = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
print(json.dumps({
    "depart": depart,
    "pic": pic,
    "nb_bruts": rapport["mesure_1_identite"]["population_bruts"],
    "nb_pivots": rapport["mesure_1_identite"]["population_pivots"],
}))
"""


def _liste_lourde(octets_vises: int, gabarit: dict) -> list:
    """Une liste métier pesant environ `octets_vises` une fois sérialisée.

    Les entrées sont **petites**, et c'est le point : depuis #431 et #432 un
    `amendements[]` ou un `votes[]` publié est un mapping à deux clés. C'est
    cette forme-là qui gonfle d'un facteur 3 à 10 en objets Python (× 4,2
    mesuré sur le corpus committé) — chaque dict, chaque clé, chaque chaîne
    porte son en-tête. Une fixture bâtie sur de longues chaînes ne gonflerait
    que d'environ × 1,5 et le garde-fou ne séparerait plus grand-chose.
    """
    (cle_id, _), = [(k, v) for k, v in gabarit.items() if k.endswith("_id")]
    unite = len(json.dumps(gabarit, ensure_ascii=False)) + 1
    return [
        dict(gabarit, **{cle_id: f"{gabarit[cle_id]}{i:07d}"})
        for i in range(max(1, octets_vises // unite))
    ]


def _corpus_de_mesure(tmp_path: Path) -> tuple[Path, Path, int]:
    """Écrit un corpus-fixture dont les blocs lourds dominent le poids.

    Rend les deux répertoires et le **poids sur disque des blocs que l'audit
    doit relâcher** — c'est de ce poids, et non d'une observation, que le
    plafond est déduit.
    """
    bruts = tmp_path / "raw_profiles"
    pivots = tmp_path / "pivot_profiles"
    bruts.mkdir()
    pivots.mkdir()

    lourd_pivot = _liste_lourde(
        POIDS_LOURD_PIVOT // 2,
        {"amendement_id": "an:AMANR5L16PO0000B0000P0D0N", "role_signataire": "cosignataire"},
    )
    lourd_brut = _liste_lourde(
        POIDS_LOURD_BRUT, {"scrutin_id": "an:16:", "position": "pour"},
    )
    poids_relache = NB_PROFILS_FIXTURE * (
        2 * len(json.dumps(lourd_pivot, ensure_ascii=False))
        + len(json.dumps(lourd_brut, ensure_ascii=False))
    )

    for i in range(NB_PROFILS_FIXTURE):
        slug = f"depute-{i:03d}"
        socle = {
            "identite": _identite_an(),
            "meta": {
                "genere_le": "2026-08-30T11:00:00+0000",
                "collecte_ecartee": [],
                "warnings": [],
                "synchro_sources": {"assemblee_nationale": "2026-08-30T10:59:00+0000"},
            },
            "votes": lourd_brut,
            "mandats": [{"label": "Députée"}],
        }
        pivot = {
            "id": slug,
            "identite": _identite_an(),
            "identifiants": {"hatvp": "https://www.hatvp.fr/fiche/jean-test"},
            "meta": {"warnings": [], "provenance": "roster_groupe"},
            "amendements": lourd_pivot,
            "interventions": lourd_pivot,
            "couverture": {"amendements": {"motif": None}},
        }
        (bruts / f"{slug}.json").write_text(
            json.dumps(socle, ensure_ascii=False), encoding="utf-8")
        (pivots / f"{slug}.pivot.json").write_text(
            json.dumps(pivot, ensure_ascii=False), encoding="utf-8")

    return bruts, pivots, poids_relache


def test_la_projection_ne_retient_aucun_bloc_que_les_mesures_n_ouvrent_pas(tmp_path):
    """Le fond du défaut : un document lu n'est jamais un document gardé.

    Le pic mémoire dépend de la machine ; **ce que la projection retient** n'en
    dépend pas. C'est donc ici que l'invariant est verrouillé, et le test de
    plafond qui suit ne fait que confirmer qu'il a l'effet annoncé.
    """
    bruts_dir = tmp_path / "raw"
    pivots_dir = tmp_path / "pivot"
    bruts_dir.mkdir()
    pivots_dir.mkdir()
    (bruts_dir / "depute.json").write_text(
        json.dumps({
            "identite": _identite_an(),
            "meta": {"genere_le": "2026-08-30T11:00:00+0000", "warnings": []},
            "votes": [{"n": 1}, {"n": 2}, {"n": 3}],
            "interventions": [],
            "sources": [{"type": "assemblee_nationale"}],
        }),
        encoding="utf-8",
    )
    (pivots_dir / "depute.pivot.json").write_text(
        json.dumps({
            "id": "depute",
            "identite": _identite_an(),
            "identifiants": {"hatvp": "https://www.hatvp.fr/fiche/jean-test"},
            "meta": {"warnings": []},
            "amendements": [{"amendement_id": "an:X"}],
            "votes": [{"scrutin_id": "s1"}],
            "interventions": [{"titre": "t"}],
            "couverture": {"amendements": {"motif": None}},
        }),
        encoding="utf-8",
    )

    charges_bruts, charges_pivots, illisibles = charger_corpus(bruts_dir, pivots_dir)
    assert illisibles == []

    pivot = charges_pivots["depute"]
    assert sorted(pivot) == sorted(BLOCS_PIVOT_LUS)
    for bloc in ("amendements", "votes", "interventions", "couverture"):
        assert bloc not in pivot

    brut = charges_bruts["depute"]
    assert sorted(brut) == sorted(set(BLOCS_BRUT_LUS) | {"votes", "interventions"})
    assert brut["votes"] == 3, "des listes brutes on ne garde que le cardinal"
    assert brut["interventions"] == 0
    assert "sources" not in brut, "aucun bloc qu'aucune mesure n'ouvre"


def test_les_mesures_lisent_le_meme_chiffre_sur_la_liste_et_sur_son_cardinal():
    """La projection ne peut pas changer un chiffre : les mesures ne lisent des
    listes métier que leur présence et leur taille, et `nombre_d_entrees` rend
    la même valeur des deux formes."""
    entier = {"identite": _identite_an(), "votes": [{"n": 1}, {"n": 2}]}
    projete = projeter_socle(entier)
    assert projete["votes"] == 2
    assert porte_des_donnees_parlementaires(entier) is True
    assert porte_des_donnees_parlementaires(projete) is True
    assert nombre_d_entrees(entier["votes"]) == nombre_d_entrees(projete["votes"])

    vide = projeter_socle({"votes": [], "mandats": []})
    assert porte_des_donnees_parlementaires(vide) is False
    assert set(LISTES_PARLEMENTAIRES) >= set(vide)

    assert projeter_pivot({"identite": {"a": 1}, "amendements": [1, 2]}) == {
        "identite": {"a": 1}
    }


@pytest.mark.skipif(
    sys.platform.startswith("win"), reason="`resource` est POSIX")
def test_le_pic_memoire_de_l_audit_reste_sous_le_plafond_declare(tmp_path):
    """L'audit ne doit pas croître de plus que le poids **sur disque** des blocs
    qu'il est censé relâcher.

    D'où vient le plafond
    ---------------------
    Il n'est pas relevé sur une exécution puis arrondi — ce serait un plafond
    qui ne protège de rien, puisqu'il suivrait la dérive qu'il doit signaler.
    C'est une **règle** : la croissance mémoire de l'audit doit rester sous le
    poids en octets, sur disque, des blocs qu'il lit et ne doit pas garder
    (`amendements`, `interventions`, `couverture` côté pivot, `votes` côté
    brut). Le raisonnement tient en une ligne : la désérialisation JSON ne
    **réduit** jamais — une liste de petits dictionnaires occupe 3 à 10 fois le
    texte qui la décrit (× 4,2 mesuré sur le corpus committé). Donc si l'audit
    croît de moins que ce texte, il ne peut pas le détenir. Au-dessus, il en
    garde quelque chose.

    Pourquoi une mesure sur fixtures vaut quelque chose
    --------------------------------------------------
    La CI ne télécharge pas le corpus : `pivot_data` est hors de la liste
    blanche du sparse-checkout de `tests.yml`, et un garde-fou (#473) échoue
    s'il réapparaît. Le plafond ne peut donc pas porter sur les 623 Mo réels.

    Mais le défaut de #628 n'est pas un défaut de **volume**, c'est un défaut de
    **rétention** — et la rétention ne dépend pas de l'échelle : un chargeur qui
    range les documents entiers dans un dictionnaire les range à toutes les
    tailles. Le corpus-fixture est bâti pour que ce comportement-là soit
    impossible à manquer : ses blocs lourds font l'essentiel de son poids, et
    les retenir dépasserait le plafond à lui seul, plusieurs fois. Ce que ce
    test certifie est donc la **propriété** — aucun document n'est conservé —
    et non le pic sur le corpus réel, qui est mesuré ailleurs et consigné dans
    `docs/decisions/audit-599-projection-blocs-lus-628.md` (113 Mio).

    Ce que le test ne prouve pas
    ----------------------------
    Ni la vitesse, ni le pic absolu sur le vrai corpus, ni la mémoire consommée
    par le reste de la suite. `ru_maxrss` est un maximum historique du
    processus : mesuré dans le processus pytest il porterait le pic de tous les
    tests déjà passés, d'où le sous-processus.
    """
    bruts, pivots, poids_relache = _corpus_de_mesure(tmp_path)
    assert poids_relache >= PLANCHER_POIDS_RELACHE, (
        f"corpus-fixture trop léger ({poids_relache / 1024**2:.0f} Mio de blocs "
        f"à relâcher) : sous ce plancher le plafond qu'il déduit ne prouve plus "
        f"rien. Regonfler les fixtures, jamais desserrer le plancher.")

    pilote = tmp_path / "pilote_mesure.py"
    pilote.write_text(_PILOTE, encoding="utf-8")
    acheve = subprocess.run(
        [sys.executable, str(pilote), str(_RACINE), str(bruts), str(pivots)],
        capture_output=True, text=True, timeout=300,
    )
    assert acheve.returncode == 0, (
        f"l'audit n'a pas rendu son rapport (code {acheve.returncode}) — un 137 "
        f"est un OOM, le défaut même de #628 :\n{acheve.stderr[-2000:]}")
    mesure = json.loads(acheve.stdout.strip().splitlines()[-1])

    assert mesure["nb_bruts"] == NB_PROFILS_FIXTURE
    assert mesure["nb_pivots"] == NB_PROFILS_FIXTURE

    # `ru_maxrss` est en Kio sous Linux, en octets sous macOS.
    facteur = 1 if sys.platform == "darwin" else 1024
    croissance = (mesure["pic"] - mesure["depart"]) * facteur
    assert croissance < poids_relache, (
        f"l'audit a grossi de {croissance / 1024**2:.1f} Mio en lisant "
        f"{NB_PROFILS_FIXTURE} profils dont {poids_relache / 1024**2:.0f} Mio de "
        f"blocs qu'il ne doit pas garder. Au-dessus de ce plafond il en retient "
        f"une partie : c'est le défaut de #628, qui faisait tuer l'audit par "
        f"l'OOM sur le corpus réel (623 Mo, pic ~3,9 Gio, exit 137).")
