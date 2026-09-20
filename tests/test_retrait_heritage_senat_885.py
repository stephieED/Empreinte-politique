"""#885 point 5 — ce que la collecte sénatoriale remplace, et quand.

Deux retraits, deux causes, **deux moments**. Les confondre est le défaut que
ces tests empêchent.

1. **Une entrée `sources[]` qui ment sur sa provenance.** `jean-luc-melenchon`
   portait un `sources[]` de type `nossenateurs` dont l'URL était un **article
   de LCP** — le lien de `raw_data/candidats.json` qui atteste sa **candidature**,
   pas une source de données parlementaires. Une fusion ancienne l'a rangé là et
   la fusion additive l'y gardait (#729). Défaut **autonome**, corrigé
   immédiatement : il ne dépend d'aucune collecte.

   Effet mesuré : le profil perd l'ODbL **Regards Citoyens**, qu'il ne devait
   pas, et garde l'ODbL **ParlTrack**, qu'il doit. La clause de partage à
   l'identique ne bouge pas.

2. **Des mandats que le Sénat remplace.** Ceux-là **n'ont pas été retirés** :
   retirer avant que la publication sénatoriale soit branchée viderait la fiche
   de `bruno-retailleau` de son mandat parlementaire, et un corpus qui perd un
   fait en attendant son remplaçant publie un trou. La fonction rend donc une
   liste vide tant qu'aucun remplaçant n'est là — le garde-fou est dans le
   critère, pas dans la vigilance de l'appelant.

Doublures construites ici (AGENTS.md §3, #457/#473/#488).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from retrait_heritage_senat import (  # noqa: E402
    TYPES_REGARDS_CITOYENS,
    mandats_electifs_remplaces,
    retirer_sources_menteuses,
    source_ment_sur_sa_provenance,
)


def _mandat(categorie="mandat_electif", source=None, chambre=None):
    entree = {"categorie": categorie, "label": "Mandat parlementaire",
              "debut": "2004-09-26", "fin": None}
    if source:
        entree["categorie_source"] = source
    if chambre:
        entree["chambre"] = chambre
    return entree


# ---------------------------------------------------------------------------
# La provenance qui ment
# ---------------------------------------------------------------------------

def test_une_url_de_presse_sous_un_type_regards_citoyens_est_un_mensonge():
    """Le cas réel : un article de LCP rangé sous `nossenateurs`."""
    source = {"type": "nossenateurs",
              "url": "https://lcp.fr/actualites/presidentielle-2027-la-liste-des-candidats"}

    assert source_ment_sur_sa_provenance(source)


def test_une_vraie_url_regards_citoyens_est_laissee_en_paix():
    """`bruno-retailleau` porte `archive.nossenateurs.fr`, qui est exact. Son
    sort est celui de #885, pas celui d'un défaut."""
    source = {"type": "nossenateurs", "url": "https://archive.nossenateurs.fr/bruno-retailleau"}

    assert not source_ment_sur_sa_provenance(source)


def test_une_entree_sans_url_n_est_pas_jugee():
    """Elle ne dit rien, et une absence n'est pas un mensonge (§2 règle 5)."""
    assert not source_ment_sur_sa_provenance({"type": "nossenateurs", "url": None})
    assert not source_ment_sur_sa_provenance({"type": "nossenateurs"})
    assert not source_ment_sur_sa_provenance({"type": "nossenateurs", "url": "   "})


def test_les_autres_types_ne_sont_pas_concernes():
    """Ce module juge une prétention, pas une URL : une source `assemblee_nationale`
    ne prétend rien sur Regards Citoyens."""
    assert not source_ment_sur_sa_provenance({"type": "assemblee_nationale",
                                              "url": "https://lcp.fr/actualites/x"})
    assert TYPES_REGARDS_CITOYENS == frozenset({"nosdeputes", "nossenateurs"})


def test_le_retrait_rend_ce_qui_est_parti():
    """Un retrait muet ne se vérifie pas."""
    profil = {"sources": [
        {"type": "assemblee_nationale", "url": "https://data.assemblee-nationale.fr/"},
        {"type": "nossenateurs", "url": "https://lcp.fr/actualites/x"},
    ]}

    retirees = retirer_sources_menteuses(profil)

    assert [s["url"] for s in retirees] == ["https://lcp.fr/actualites/x"]
    assert [s["type"] for s in profil["sources"]] == ["assemblee_nationale"]


def test_le_retrait_ne_recompose_pas_la_licence_lui_meme():
    """§7 : `meta.licence_donnees` est dérivé, et sa fabrique est
    `licences.appliquer_licence_donnees`. Un module qui la réécrirait au passage
    en ferait un second référentiel."""
    profil = {"sources": [{"type": "nossenateurs", "url": "https://lcp.fr/x"}],
              "meta": {"licence_donnees": "inchangée"}}

    retirer_sources_menteuses(profil)

    assert profil["meta"]["licence_donnees"] == "inchangée"


def test_un_profil_sans_source_ne_bouge_pas():
    profil = {"sources": []}

    assert retirer_sources_menteuses(profil) == []
    assert profil["sources"] == []


# ---------------------------------------------------------------------------
# Le retrait qui attend son remplaçant
# ---------------------------------------------------------------------------

def test_aucun_mandat_n_est_propose_tant_que_rien_ne_le_remplace():
    """C'est le garde-fou du point 5. Retirer « Mandat parlementaire (Les
    Républicains) » avant que les 4 mandats sénatoriaux datés soient publiés
    viderait la fiche."""
    profil = {"mandats": [_mandat()]}

    assert mandats_electifs_remplaces(profil) == []


def test_le_mandat_herite_est_propose_une_fois_le_remplacant_publie():
    """Le remplaçant se reconnaît à son estampille **et** à sa chambre : un
    mandat `an` estampillé ne remplace pas un mandat sénatorial."""
    profil = {"mandats": [
        _mandat(),
        _mandat(source="senat", chambre="Senat"),
    ]}

    proposes = mandats_electifs_remplaces(profil)

    assert len(proposes) == 1
    assert "categorie_source" not in proposes[0]


def test_un_remplacant_d_une_autre_chambre_ne_declenche_rien():
    """Un mandat de député estampillé `an` ne remplace pas un mandat de
    sénateur, et le prendre pour tel retirerait un fait sans contrepartie."""
    profil = {"mandats": [_mandat(), _mandat(source="an", chambre="AN")]}

    assert mandats_electifs_remplaces(profil) == []


def test_seuls_les_mandats_electifs_sont_concernes():
    """Les 8 autres entrées sans estampille de `bruno-retailleau` — commissions,
    groupes d'études, extra-parlementaires — ne sont **pas** du périmètre : le
    « doublon hérité » fait 2 entrées, pas 9 (#878)."""
    profil = {"mandats": [
        _mandat(categorie="commission"),
        _mandat(categorie="groupe_amitie"),
        _mandat(source="senat", chambre="Senat"),
    ]}

    assert mandats_electifs_remplaces(profil) == []


# ---------------------------------------------------------------------------
# La moitié qu'on oublie : le brut
# ---------------------------------------------------------------------------

def test_le_retrait_au_brut_lit_le_bloc_senatorial_du_brut():
    """Le point 5 dit « aux deux couches » (#729), et la raison est mécanique :
    `audit_collecte_vs_publie` compare le brut au pivot, seuil 0. Retirer d'un
    seul côté produit un déficit qui **bloque le commit** — mesuré, 2 couples et
    2 entrées, avant que ce retrait n'existe.

    Le remplaçant se lit dans le brut lui-même : faire dépendre le brut du pivot
    inverserait le sens de la chaîne."""
    from retrait_heritage_senat import mandats_bruts_remplaces

    brut = {
        "mandats": [_mandat(), _mandat(categorie="commission")],
        "mandat_senatorial": {"mandats_senatoriaux": [
            {"famille": "mandat_parlementaire", "debut": "2004-10-01", "fin": "2014-09-30"},
        ]},
    }

    proposes = mandats_bruts_remplaces(brut)

    assert len(proposes) == 1
    assert proposes[0]["categorie"] == "mandat_electif"


def test_sans_bloc_senatorial_le_brut_ne_perd_rien():
    """Même garde qu'au pivot : pas de remplaçant, pas de retrait."""
    from retrait_heritage_senat import mandats_bruts_remplaces

    assert mandats_bruts_remplaces({"mandats": [_mandat()]}) == []
    assert mandats_bruts_remplaces({"mandats": [_mandat()],
                                    "mandat_senatorial": {"mandats_senatoriaux": []}}) == []


def test_un_mandat_de_depute_n_est_pas_remplace_par_un_mandat_de_senateur():
    """Le cas réel : `jean-luc-melenchon` publie un mandat de député
    21/06/2017 → 21/06/2022, non estampillé. Ses mandats de sénateur s'arrêtent
    en 2010. Sans la condition de recouvrement, il était proposé au retrait — et
    l'appliquer aurait effacé un mandat de député.

    C'est ce qui fait que le compte est **2 et non 3** (#878)."""
    profil = {"mandats": [
        {"categorie": "mandat_electif", "label": "Mandat parlementaire (LFI)",
         "debut": "2017-06-21", "fin": "2022-06-21"},
        {"categorie": "mandat_electif", "label": "Mandat de sénateur",
         "debut": "2004-10-01", "fin": "2010-01-07",
         "categorie_source": "senat", "chambre": "Senat"},
    ]}

    assert mandats_electifs_remplaces(profil) == []
