"""`chambres` au niveau profil : une liste dérivée, et `chambre` qui en découle (#493).

Sous-issue **D** de l'épic **#486**, elle-même appuyée sur **#492** (la chambre
portée par chaque `mandat_electif`).

Ce que ces tests verrouillent, dans l'ordre de ce qui pourrait casser :

1. **`chambre` n'est plus une donnée autonome.** Elle vaut `chambres[0]` et
   `validate_profil` refuse toute divergence. C'est la condition non négociable
   de la coexistence : un champ collecté à côté d'un champ dérivé garderait le
   mensonge à côté de la vérité, en ajoutant la question « lequel croire ».
2. **Le repli s'ajoute, il ne se substitue pas.** Deux simulations en lecture
   seule sur les 209 profils publiés de `b2c34f4` ont corrigé ce point, et pour
   la même raison à chaque fois : retirer une chambre observée est une
   suppression, ce que le pipeline ne fait jamais. Les deux cas mesurés sont
   rejoués ici sur fixtures figées (`test_le_repli_ne_disparait_pas_*`).
3. **`chambres` se recalcule après la fusion, il ne se fusionne pas.**
   `merge_lists_by_key` est additif : `merged["mandats"]` est un surensemble de
   l'ancien comme du neuf, donc un `chambres` fusionné décrirait un ensemble de
   mandats qui n'existe nulle part. Symétrique du piège que #492 a rencontré sur
   `backfill_mandat_chambre`.
4. **Le repli est déclaré.** `chambres` peut contenir une chambre que rien
   n'étaye — celle de la collecte. Le warning est ce qui sépare « utilisable »
   de « trompeur », et son décompte est la mesure de la migration.

Aucune lecture du corpus vivant (`pivot_data/`, `raw_data/profiles/`) : ces
tests tournent en CI, où le corpus est absent du disque (#473).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from merge_profile import merge_pivot_profile  # noqa: E402
from normalize_europarl import normalize_europarl  # noqa: E402
from normalize_profil import (  # noqa: E402
    WARNING_PREFIX_CHAMBRE_MANDAT_NON_RESOLUE,
    WARNING_PREFIX_CHAMBRES_NON_CORROBOREE,
    normalize_profil,
)
from schema_pivot import (  # noqa: E402
    KNOWN_CHAMBRES,
    ORDRE_CHAMBRES,
    appliquer_chambres,
    deriver_chambres,
    make_empty_profil,
    validate_profil,
)


# ---------------------------------------------------------------------------
# Fixtures figées, minimales
# ---------------------------------------------------------------------------

def _mandat_electif(chambre=None, label="Mandat parlementaire (Socialistes)", debut="2022-06-22"):
    """Mandat électif au format pivot. `chambre=None` = collecté avant #492."""
    return {
        "label": label,
        "categorie": "mandat_electif",
        "fonction": "membre",
        "debut": debut,
        "fin": None,
        "actif": True,
        "chambre": chambre,
    }


def _brut(chambre="deputes", mandats=None):
    """Profil brut minimal, format `candidate_profile.build_profile()`."""
    return {
        "slug": "marie-martin",
        "chambre": chambre,
        "source": "https://www.nosdeputes.fr/marie-martin",
        "identite": {"nom_complet": "Marie Martin", "groupe_nom": "Socialistes"},
        "mandats": mandats if mandats is not None else [],
        "votes": [],
        "interventions": [],
        "amendements": [],
        "dossiers_legislatifs": [],
        "meta": {
            "genere_le": "2026-08-20T12:00:00+0000",
            "synchro_sources": {"nosdeputes": "2026-08-20T12:00:00+0000"},
        },
    }


def _mandat_brut(chambre=None, label="Mandat parlementaire (Socialistes)", debut="2022-06-22"):
    mandat = {
        "categorie": "mandat_electif",
        "type": "mandat",
        "label": label,
        "debut": debut,
        "fin": None,
        "actif": True,
    }
    if chambre is not None:
        mandat["chambre"] = chambre
    return mandat


def _ue_brut(debut="2014-07-01", fin="2019-07-01"):
    """Bloc `mandat_europeen` minimal, format `candidate_profile_ue`."""
    return {
        "identifiant_pe": "12345",
        "nom_complet": "Marie Martin",
        "url_source": "https://www.europarl.europa.eu/meps/fr/12345",
        "mandats_europeens": [
            {
                "type": "EU_INSTITUTION",
                "organisation_nom": "Parlement européen",
                "role_label": "Députée au Parlement européen",
                "debut": debut,
                "fin": fin,
                "actif": fin is None,
            }
        ],
        "meta": {"genere_le": "2026-08-20T12:00:00+0000"},
    }


def _warnings_chambres(pivot):
    return [
        w for w in pivot["meta"]["warnings"]
        if w.startswith(WARNING_PREFIX_CHAMBRES_NON_CORROBOREE)
    ]


def _warnings_mandat_sans_chambre(pivot):
    return [
        w for w in pivot["meta"]["warnings"]
        if w.startswith(WARNING_PREFIX_CHAMBRE_MANDAT_NON_RESOLUE)
    ]


# ---------------------------------------------------------------------------
# 1. deriver_chambres — la fabrique unique
# ---------------------------------------------------------------------------

def test_les_chambres_viennent_des_mandats_estampilles():
    d = deriver_chambres(
        [_mandat_electif("Senat", debut="2004-09-26"), _mandat_electif("AN", debut="2017-06-21")]
    )
    assert d.chambres == ["AN", "Senat"]
    assert d.corroboree is True
    assert d.chambres_non_corroborees == []


def test_une_carriere_sur_deux_chambres_nen_efface_aucune():
    """Le défaut d'origine de l'épic #486 : le scalaire n'en publiait qu'une."""
    d = deriver_chambres(
        [_mandat_electif("AN", debut="1994-01-01"), _mandat_electif("Senat", debut="2004-09-26")]
    )
    assert "AN" in d.chambres and "Senat" in d.chambres


def test_la_liste_est_dans_lordre_canonique_pas_celui_des_mandats():
    """L'ordre suit ORDRE_CHAMBRES, pas l'ordre des mandats — que la fusion
    additive fait varier d'un run à l'autre."""
    a = deriver_chambres([_mandat_electif("PE"), _mandat_electif("AN"), _mandat_electif("Senat")])
    b = deriver_chambres([_mandat_electif("Senat"), _mandat_electif("AN"), _mandat_electif("PE")])
    assert a.chambres == b.chambres == ["AN", "Senat", "PE"]


def test_la_liste_ne_porte_aucun_doublon():
    d = deriver_chambres([_mandat_electif("AN"), _mandat_electif("AN"), _mandat_electif("AN")])
    assert d.chambres == ["AN"]


def test_seuls_les_mandats_electifs_sont_lus():
    """Une commission ou un groupe politique ne fait pas siéger dans une chambre."""
    d = deriver_chambres([
        {"categorie": "commission", "chambre": "Senat", "label": "Finances"},
        {"categorie": "groupe_politique", "chambre": "PE", "label": "S&D"},
        _mandat_electif("AN"),
    ])
    assert d.chambres == ["AN"]


def test_aucun_libelle_nest_interprete():
    """« Mandat de député européen » ne fabrique pas un `PE` : #492 a écarté la
    déduction par le texte, et la rouvrir ici remettrait une chaîne collectée au
    cœur d'un champ fermé."""
    d = deriver_chambres([_mandat_electif(None, label="Mandat de député européen")])
    assert d.chambres == []


def test_une_chambre_hors_nomenclature_ne_passe_pas_en_contrebande():
    d = deriver_chambres([_mandat_electif("deputes"), _mandat_electif("senateurs")])
    assert d.chambres == []
    assert all(c in KNOWN_CHAMBRES for c in ORDRE_CHAMBRES)


def test_le_scalaire_est_toujours_le_premier_element():
    for mandats in ([], [_mandat_electif("Senat")], [_mandat_electif("PE"), _mandat_electif("AN")]):
        d = deriver_chambres(mandats)
        assert d.chambre == (d.chambres[0] if d.chambres else None)


def test_sans_mandat_ni_repli_la_liste_est_vide_et_le_scalaire_nul():
    """Aucune valeur par défaut (§2.5) : rien à dériver, rien sur quoi se replier.

    Et rien à corroborer : une liste vide ne publie aucune chambre, donc aucune
    chambre non étayée (#486). La déclarer « non corroborée » faisait publier,
    sur 3 des 481 profils pivot du 30/08/2026 (`david-lisnard`,
    `marine-tondelier`, `nathalie-arthaud`), un warning dont la phrase même
    disait qu'il n'y avait rien à signaler.
    """
    d = deriver_chambres([], repli=None)
    assert d.chambres == [] and d.chambre is None
    assert d.corroboree is True
    assert d.chambres_non_corroborees == []


# ---------------------------------------------------------------------------
# 2. Le repli s'ajoute, il ne se substitue pas
# ---------------------------------------------------------------------------

def test_le_repli_comble_labsence_totale_de_mandat_estampille():
    """Les 201 profils `roster_groupe` du corpus de `b2c34f4` sont dans ce cas."""
    d = deriver_chambres([_mandat_electif(None)], repli="AN")
    assert d.chambres == ["AN"]
    assert d.corroboree is False
    assert d.chambres_non_corroborees == ["AN"]
    assert d.mandats_non_estampilles == 1


def test_le_repli_ne_disparait_pas_quand_un_mandat_europeen_est_estampille():
    """Cas mesuré sur `b2c34f4` : 6 profils AN portent un mandat européen
    estampillé `PE` par `normalize_europarl` et des mandats AN encore à `null`.
    Un repli « seulement si rien n'est estampillé » les publiait `PE` — une
    députée publiée députée européenne, et 5 d'entre eux sortis de
    `check_quality_gate.population_an`."""
    d = deriver_chambres([_mandat_electif(None), _mandat_electif("PE")], repli="AN")
    assert d.chambres == ["AN", "PE"]
    assert d.chambre == "AN"
    assert d.chambres_non_corroborees == ["AN"]


def test_le_repli_ne_disparait_pas_quand_tous_les_electifs_collectes_sont_europeens():
    """Cas mesuré sur `b2c34f4` : `yannick-vaugrenard`, dont le seul
    `mandat_electif` collecté est européen. Tous ses mandats électifs étant
    estampillés, un repli « seulement si la couverture est incomplète » tenait
    la carrière pour complète et effaçait son `AN`. La complétude de `mandats[]`
    n'est pas celle d'une carrière."""
    d = deriver_chambres([_mandat_electif("PE")], repli="AN")
    assert d.chambres == ["AN", "PE"]
    assert d.chambre == "AN"
    assert d.corroboree is False


def test_le_repli_deja_etaye_par_un_mandat_ne_cree_pas_de_doublon():
    d = deriver_chambres([_mandat_electif("AN")], repli="AN")
    assert d.chambres == ["AN"]
    assert d.corroboree is True
    assert d.chambres_non_corroborees == []


def test_un_repli_hors_nomenclature_est_ignore():
    """`normalize_profil` laisse passer une chambre brute non mappée ;
    elle est écartée ici, jamais publiée telle quelle."""
    assert deriver_chambres([], repli="deputes").chambres == []
    assert deriver_chambres([], repli="").chambres == []


def test_un_mandat_non_estampille_nempeche_plus_la_corroboration_dune_liste_etayee():
    """La corroboration porte sur ce que `chambres` PUBLIE, pas sur la
    complétude de `mandats[]` (#486).

    Ici `AN` est étayée par un mandat estampillé : la liste publiée est
    entièrement fondée. Le mandat resté à `null` est un manque de collecte,
    déclaré par le warning de #492 — qui le nomme et le compte. Confondre les
    deux gageait le retrait d'un champ de niveau profil sur une complétude de
    niveau mandat que la fusion additive ne peut pas atteindre : sur les 481
    profils pivot publiés du 30/08/2026, **27** étaient dans ce cas exact, et
    leur warning se lisait « chambres du profil non corroborée : chambres=['AN'],
    dont aucune sans mandat électif estampillé pour l'étayer ».
    """
    d = deriver_chambres([_mandat_electif("AN"), _mandat_electif(None)], repli="AN")
    assert d.chambres == ["AN"]
    assert d.corroboree is True
    assert d.chambres_non_corroborees == []
    # Le fait n'est pas perdu : il reste compté, pour le warning de #492.
    assert d.mandats_non_estampilles == 1


# ---------------------------------------------------------------------------
# 3. validate_profil — les deux champs ne peuvent pas diverger
# ---------------------------------------------------------------------------

def _profil_valide(chambres, chambre):
    p = make_empty_profil("marie-martin", "Marie Martin")
    p["chambres"] = chambres
    p["chambre"] = chambre
    p["meta"]["licence_donnees"] = "ODbL"
    return p


def test_validate_accepte_un_couple_coherent():
    assert validate_profil(_profil_valide(["AN", "Senat"], "AN")) == []
    assert validate_profil(_profil_valide([], None)) == []


def test_validate_refuse_un_scalaire_qui_contredit_la_liste():
    errors = validate_profil(_profil_valide(["AN", "Senat"], "Senat"))
    assert any("contredit" in e for e in errors), errors


def test_validate_refuse_un_scalaire_renseigne_sur_une_liste_vide():
    errors = validate_profil(_profil_valide([], "AN"))
    assert any("contredit" in e for e in errors), errors


def test_validate_refuse_une_valeur_hors_nomenclature_dans_la_liste():
    errors = validate_profil(_profil_valide(["deputes"], "deputes"))
    assert any("non reconnues" in e for e in errors), errors


def test_validate_refuse_un_doublon():
    errors = validate_profil(_profil_valide(["AN", "AN"], "AN"))
    assert any("doublons" in e for e in errors), errors


def test_validate_refuse_un_ordre_non_canonique():
    errors = validate_profil(_profil_valide(["Senat", "AN"], "Senat"))
    assert any("ordre canonique" in e for e in errors), errors


def test_validate_refuse_une_liste_qui_nen_est_pas_une():
    errors = validate_profil(_profil_valide("AN", "AN"))
    assert any("doit être une liste" in e for e in errors), errors


def test_validate_ignore_un_profil_publie_avant_493():
    """`chambres` n'est pas dans REQUIRED_TOP_LEVEL_KEYS le temps de la
    coexistence : les 209 profils publiés de `b2c34f4` ne la portent pas, et les
    déclarer invalides ne dirait rien de vrai sur eux. La clé devient obligatoire
    quand `chambre` est retiré (#494)."""
    p = _profil_valide([], None)
    del p["chambres"]
    p["chambre"] = "AN"
    assert validate_profil(p) == []


# ---------------------------------------------------------------------------
# 4. Normalisation — les deux champs sortent de la même fabrique
# ---------------------------------------------------------------------------

def test_le_pivot_publie_les_deux_champs():
    pivot = normalize_profil(_brut(chambre="deputes", mandats=[_mandat_brut("deputes")]))
    assert pivot["chambres"] == ["AN"]
    assert pivot["chambre"] == "AN"
    assert validate_profil(pivot) == []


def test_le_pivot_ne_publie_plus_la_chambre_de_collecte_telle_quelle():
    """Un profil collecté côté `senateurs` mais dont le mandat électif est
    estampillé `AN` publie les deux — c'est le cas `jean-luc-melenchon` que #492
    a mesuré sur `f5a828b` (profil brut `senateurs`, mandats manifestement AN)."""
    pivot = normalize_profil(_brut(chambre="senateurs", mandats=[_mandat_brut("deputes")]))
    assert pivot["chambres"] == ["AN", "Senat"]
    assert pivot["chambre"] == "AN"


def test_le_pivot_declare_une_liste_non_corroboree():
    pivot = normalize_profil(_brut(chambre="deputes", mandats=[_mandat_brut(None)]))
    assert pivot["chambres"] == ["AN"]
    warnings = _warnings_chambres(pivot)
    assert len(warnings) == 1
    assert "AN" in warnings[0]


def test_le_pivot_ne_declare_rien_quand_la_liste_est_corroboree():
    pivot = normalize_profil(_brut(chambre="deputes", mandats=[_mandat_brut("deputes")]))
    assert _warnings_chambres(pivot) == []


def test_un_seul_warning_par_profil_quel_que_soit_le_nombre_de_mandats():
    """Même règle que #492 : le cas est uniforme, c'est le compte de profils qui
    porte l'information. Un warning par mandat ferait 214 occurrences sur 207
    profils pour dire la même chose."""
    brut = _brut(chambre="deputes", mandats=[_mandat_brut(None) for _ in range(5)])
    assert len(_warnings_chambres(normalize_profil(brut))) == 1


def test_le_pivot_europeen_derive_pe_de_ses_mandats():
    pivot = normalize_europarl(_ue_brut())
    assert pivot["chambres"] == ["PE"]
    assert pivot["chambre"] == "PE"
    assert validate_profil(pivot) == []


# ---------------------------------------------------------------------------
# 5. appliquer_chambres — recalculer après toute mutation de mandats[]
# ---------------------------------------------------------------------------

def test_le_versement_des_mandats_europeens_ajoute_pe_a_la_liste():
    """Ce que fait `generate_all_profiles` : `mandats.extend(ue_pivot.mandats)`.
    Sans recalcul, le profil publierait `["AN"]` et effacerait le mandat
    européen — le défaut même que #486 reproche au scalaire, reconduit dans le
    champ censé le corriger."""
    pivot = normalize_profil(_brut(chambre="deputes", mandats=[_mandat_brut("deputes")]))
    ue_pivot = normalize_europarl(_ue_brut())
    pivot["mandats"].extend(ue_pivot["mandats"])
    appliquer_chambres(pivot)
    assert pivot["chambres"] == ["AN", "PE"]
    assert pivot["chambre"] == "AN"


def test_appliquer_chambres_est_idempotent():
    pivot = normalize_profil(_brut(chambre="deputes", mandats=[_mandat_brut(None)]))
    avant = (list(pivot["chambres"]), pivot["chambre"])
    appliquer_chambres(pivot)
    appliquer_chambres(pivot)
    assert (pivot["chambres"], pivot["chambre"]) == avant


def test_appliquer_chambres_ne_fait_jamais_regresser_le_scalaire_vers_null():
    """`chambre` est un scalaire **surveillé** par `audit_diff_profils` : un
    passage renseigné → `null` abandonne le commit. Le repli sur la valeur
    courante est ce qui l'en empêche."""
    pivot = make_empty_profil("marie-martin", "Marie Martin")
    pivot["chambre"] = "AN"
    appliquer_chambres(pivot)
    assert pivot["chambre"] == "AN"
    assert pivot["chambres"] == ["AN"]


# ---------------------------------------------------------------------------
# 6. Fusion — un champ dérivé se recalcule, il ne se fusionne pas
# ---------------------------------------------------------------------------

def test_la_fusion_recalcule_la_liste_sur_les_mandats_fusionnes():
    """`merge_lists_by_key` est additif : `merged["mandats"]` est un surensemble
    de l'ancien comme du neuf. Une liste fusionnée décrirait un ensemble de
    mandats qui n'existe dans aucun des deux profils."""
    ancien = normalize_profil(
        _brut(chambre="senateurs", mandats=[_mandat_brut("senateurs", label="Sénat", debut="2004-09-26")])
    )
    neuf = normalize_profil(
        _brut(chambre="deputes", mandats=[_mandat_brut("deputes", label="AN", debut="2017-06-21")])
    )
    fusionne = merge_pivot_profile(ancien, neuf)

    assert fusionne["chambres"] == ["AN", "Senat"]
    assert fusionne["chambre"] == "AN"
    assert validate_profil(fusionne) == []


def test_la_fusion_ne_perd_jamais_une_chambre_deja_publiee():
    """Un run qui ne recollecte qu'une chambre ne doit pas retirer l'autre."""
    ancien = normalize_profil(
        _brut(chambre="deputes", mandats=[_mandat_brut("deputes", label="AN", debut="2017-06-21")])
    )
    neuf = normalize_profil(_brut(chambre="senateurs", mandats=[]))
    fusionne = merge_pivot_profile(ancien, neuf)
    assert "AN" in fusionne["chambres"]


def test_la_fusion_profite_du_backfill_de_chambre_de_492():
    """`backfill_mandat_chambre` estampille après coup un mandat déjà connu : le
    profil doit gagner la chambre correspondante, et perdre son warning."""
    ancien = normalize_profil(_brut(chambre="deputes", mandats=[_mandat_brut(None)]))
    assert len(_warnings_chambres(ancien)) == 1

    neuf = normalize_profil(_brut(chambre="deputes", mandats=[_mandat_brut("deputes")]))
    fusionne = merge_pivot_profile(ancien, neuf)

    assert fusionne["chambres"] == ["AN"]
    assert _warnings_chambres(fusionne) == []


def test_la_fusion_confie_le_mandat_non_estampille_au_warning_de_492():
    """Un mandat fossile — conservé par la fusion, que la source ne rend plus —
    ne rend pas la liste publiée non fondée (#486).

    `AN` est étayée par le mandat neuf. Ce qui reste vrai, et doit rester dit,
    c'est qu'un `mandat_electif` n'a pas de chambre : c'est le warning de #492,
    et il est désormais le seul à le déclarer.
    """
    ancien = normalize_profil(
        _brut(chambre="deputes", mandats=[_mandat_brut(None, label="Ancien", debut="2012-06-20")])
    )
    neuf = normalize_profil(
        _brut(chambre="deputes", mandats=[_mandat_brut("deputes", label="Neuf", debut="2017-06-21")])
    )
    fusionne = merge_pivot_profile(ancien, neuf)
    assert _warnings_chambres(fusionne) == []
    assert len(_warnings_mandat_sans_chambre(fusionne)) == 1
    assert "1 mandat(s)" in _warnings_mandat_sans_chambre(fusionne)[0]


def test_la_fusion_nintroduit_aucune_divergence_entre_les_deux_champs():
    ancien = normalize_profil(_brut(chambre="senateurs", mandats=[_mandat_brut(None)]))
    neuf = normalize_profil(_brut(chambre="deputes", mandats=[_mandat_brut("deputes")]))
    fusionne = merge_pivot_profile(ancien, neuf)
    assert fusionne["chambre"] == fusionne["chambres"][0]
    assert validate_profil(fusionne) == []


def test_un_profil_ancien_sans_chambres_est_fusionnable():
    """Le corpus publié ne porte pas encore la clé : la fusion doit la produire
    sans rien casser, et sans faire régresser le scalaire."""
    ancien = normalize_profil(_brut(chambre="deputes", mandats=[_mandat_brut(None)]))
    del ancien["chambres"]
    neuf = normalize_profil(_brut(chambre="deputes", mandats=[_mandat_brut(None)]))
    fusionne = merge_pivot_profile(ancien, neuf)
    assert fusionne["chambres"] == ["AN"]
    assert fusionne["chambre"] == "AN"


def test_un_profil_malforme_ne_tue_pas_le_pipeline():
    """`deriver_chambres` tourne dans le pipeline, **avant** toute validation.
    Une `chambre` qui n'est pas une chaîne doit produire « non déterminée », pas
    un `TypeError` (`x in frozenset` lève sur une valeur non hashable) — un shard
    d'extraction qui meurt n'écrit aucun profil du tout (#498)."""
    d = deriver_chambres([{"categorie": "mandat_electif", "chambre": ["AN"]}], repli={"x": 1})
    assert d.chambres == []
    assert d.mandats_non_estampilles == 1
