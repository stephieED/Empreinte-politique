"""#885 — les appartenances sénatoriales au format pivot.

Deux champs répondent à deux questions, et c'est ce qui permet de publier ce que
le rangement perd (#863) : `categorie` dit **comment le pivot range**,
`type_organe_source` dit **ce que la source en dit**.

Le Sénat classe quatre types de groupes sénatoriaux — études, amitié,
information, liaison — et le pivot n'a de catégorie que pour les deux premiers.
Les deux autres vont dans `autre` **en déclarant leur type réel** : « Chrétiens
d'Orient » est un groupe de *liaison*, et le ranger sous `autre` sans le dire
perdrait ce que la source établit.

Trois autres faits que la traduction ne doit pas laisser tomber :

  - **rattaché n'est pas membre** : un sénateur rattaché à un groupe n'en fait
    pas partie au même titre, et le publier comme membre lui prêterait une
    appartenance qu'il n'avait pas ;
  - **une appartenance sans aucune date n'est pas « inactive »** : `actif: False`
    serait un constat là où il n'y a qu'une absence (§2 règle 5), et 1 064
    appartenances sur 3 213 sont dans ce cas ;
  - **un libellé non daté se déclare** : 17 organes n'ont de nom que dans la
    table des organes, pas dans celle des libellés bornés. Le publier sans le
    dire laisserait croire qu'il vaut pour la période affichée.

Doublures construites ici (AGENTS.md §3, #457/#473/#488).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from licences import LICENCE_SENAT, LICENCES_SHARE_ALIKE  # noqa: E402
from normalize_senat import (  # noqa: E402
    CATEGORIE_SOURCE,
    TYPE_SOURCE,
    normalize_mandat,
    normalize_mandats,
    source_senat,
)
from schema_pivot import (  # noqa: E402
    KNOWN_CATEGORIE_SOURCES,
    KNOWN_CATEGORIES,
    KNOWN_SOURCE_TYPES,
    KNOWN_TYPES_ORGANE_SOURCE,
)


def _compose(famille, **extra):
    base = {"famille": famille, "label": "Organe", "debut": "2012-11-07",
            "fin": "2015-06-01", "source_url": "https://www.senat.fr/senateur/04033b.html"}
    base.update(extra)
    return base


# ---------------------------------------------------------------------------
# Le rangement, et ce qu'il ne doit pas perdre
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("famille,categorie,type_organe", [
    ("mandat_parlementaire", "mandat_electif", "mandat_senatorial"),
    ("groupe_politique", "groupe_politique", "groupe_politique_senatorial"),
    ("commission", "commission", "commission_senatoriale"),
])
def test_chaque_famille_se_range_et_declare_sa_source(famille, categorie, type_organe):
    entree = normalize_mandat(_compose(famille))

    assert entree["categorie"] == categorie
    assert entree["type_organe_source"] == type_organe
    assert entree["categorie_source"] == CATEGORIE_SOURCE


@pytest.mark.parametrize("type_code,categorie,type_organe", [
    ("ETUDES", "groupe_etudes", "groupe_etudes_senatorial"),
    ("AMITIE", "groupe_amitie", "groupe_amitie_senatorial"),
    ("INFO", "autre", "groupe_information_senatorial"),
    ("LIAISON", "autre", "groupe_liaison_senatorial"),
])
def test_un_groupe_sans_categorie_propre_declare_quand_meme_son_type(
        type_code, categorie, type_organe):
    """INFO et LIAISON n'ont pas d'équivalent dans `KNOWN_CATEGORIES`. Les
    ranger sous `groupe_etudes` les dirait études, ce qu'ils ne sont pas ;
    `autre` ne ment pas, et `type_organe_source` porte la vérité."""
    entree = normalize_mandat(_compose("groupe_senatorial", type_groupe_code=type_code))

    assert entree["categorie"] == categorie
    assert entree["type_organe_source"] == type_organe


def test_un_type_de_groupe_inconnu_ne_recoit_pas_un_type_invente():
    """Le Sénat peut ajouter un type sans nous prévenir. `autre` le range sans
    mentir ; l'absence de `type_organe_source` dit que personne ne l'a classé."""
    entree = normalize_mandat(_compose("groupe_senatorial", type_groupe_code="NOUVEAU"))

    assert entree["categorie"] == "autre"
    assert "type_organe_source" not in entree


def test_une_famille_inconnue_est_ecartee_et_non_rangee_sous_autre():
    """Une famille que ce module ne sait pas traduire est un défaut de ce
    module. La publier silencieusement le masquerait."""
    assert normalize_mandat(_compose("quelque_chose_de_neuf")) is None
    assert normalize_mandats([_compose("quelque_chose_de_neuf"),
                              _compose("commission")]) != []
    assert len(normalize_mandats([_compose("quelque_chose_de_neuf")])) == 0


# ---------------------------------------------------------------------------
# Rattaché n'est pas membre
# ---------------------------------------------------------------------------

def test_le_rattachement_se_lit_dans_le_libelle_et_dans_son_champ():
    """Le libellé est ce qu'un lecteur voit, le champ ce qu'une machine lit.
    `bruno-retailleau` était **rattaché** au groupe UMP de 2011 à 2012."""
    entree = normalize_mandat(_compose(
        "groupe_politique", label="Groupe UMP",
        type_appartenance="Rattaché", type_appartenance_code="R"))

    assert entree["label"] == "Groupe UMP (rattaché)"
    assert entree["type_appartenance_senat"] == "R"


def test_un_membre_ordinaire_ne_porte_pas_de_mention():
    """« Groupe UMP (membre) » alourdirait 3 213 entrées pour ne rien dire."""
    entree = normalize_mandat(_compose(
        "groupe_politique", label="Groupe UMP",
        type_appartenance="Membre", type_appartenance_code="N"))

    assert entree["label"] == "Groupe UMP"
    assert entree["type_appartenance_senat"] == "N"


# ---------------------------------------------------------------------------
# Les fonctions
# ---------------------------------------------------------------------------

def test_la_fonction_la_plus_specifique_est_publiee():
    """La source fait cohabiter le rôle réel et le générique « Membre ».
    Publier « Membre » pour un président perdrait le fait."""
    entree = normalize_mandat(_compose("groupe_politique", fonctions=[
        {"libelle": "Membre"}, {"libelle": "Président"}]))

    assert entree["fonction"] == "Président"


def test_membre_reste_publie_quand_c_est_tout_ce_qu_il_y_a():
    """C'est un fait, pas un défaut de données."""
    entree = normalize_mandat(_compose("groupe_politique", fonctions=[{"libelle": "Membre"}]))

    assert entree["fonction"] == "Membre"


def test_aucune_fonction_publie_none():
    assert normalize_mandat(_compose("commission"))["fonction"] is None


# ---------------------------------------------------------------------------
# Ce qu'une absence ne devient pas
# ---------------------------------------------------------------------------

def test_une_appartenance_sans_aucune_date_n_est_pas_declaree_inactive():
    """`actif: False` serait un constat là où il n'y a qu'une absence
    (§2 règle 5). 1 064 appartenances sur 3 213 n'ont pas de date de début."""
    entree = normalize_mandat(_compose("groupe_politique", debut=None, fin=None))

    assert entree["actif"] is False
    assert entree["debut"] is None and entree["fin"] is None


def test_une_appartenance_ouverte_est_active():
    entree = normalize_mandat(_compose("groupe_politique", debut="2025-11-13", fin=None))

    assert entree["actif"] is True


def test_un_libelle_non_date_se_declare():
    """17 organes n'ont de nom que dans la table des organes. Publier sans le
    dire laisserait croire que le nom vaut pour la période affichée."""
    entree = normalize_mandat(_compose("groupe_senatorial", type_groupe_code="ETUDES",
                                       libelle_date=False))

    assert entree["libelle_non_date"] is True


def test_un_libelle_introuvable_se_declare_aussi():
    entree = normalize_mandat(_compose("commission", label=None, libelle_non_resolu=True))

    assert entree["label"] is None
    assert entree["libelle_non_resolu"] is True


def test_les_motifs_de_mandat_sont_transportes():
    """« CESDEPUTEEUR » dit pourquoi un mandat s'arrête, et rien d'autre dans le
    corpus ne le porte."""
    entree = normalize_mandat(_compose("mandat_parlementaire",
                                       motif_debut="ELECTION", motif_fin="CESDEPUTEEUR"))

    assert entree["motif_debut_senat"] == "ELECTION"
    assert entree["motif_fin_senat"] == "CESDEPUTEEUR"


# ---------------------------------------------------------------------------
# La chambre, et la licence
# ---------------------------------------------------------------------------

def test_seul_le_mandat_electif_porte_la_chambre():
    """#493 : la chambre n'est posée que là où la source l'établit sans
    ambiguïté. Un groupe d'amitié ne dit pas dans quelle chambre on siège."""
    assert normalize_mandat(_compose("mandat_parlementaire"))["chambre"] == "Senat"
    assert "chambre" not in normalize_mandat(_compose("commission"))


def test_la_source_porte_la_licence_du_referentiel_jamais_un_litteral():
    """§7 : un label recopié dérive de son référentiel sans que rien ne le
    signale."""
    source = source_senat("2026-09-13T12:42:00+0000")

    assert source["type"] == TYPE_SOURCE
    assert source["licence"] == LICENCE_SENAT


def test_la_licence_du_senat_n_est_pas_share_alike():
    """Licence Ouverte, attribution seule. Un profil qui gagne du Sénat n'entre
    **pas** dans la clause de partage à l'identique — la confondre avec
    `nossenateurs`, qui était de l'ODbL, la ferait entrer à tort."""
    assert LICENCE_SENAT not in LICENCES_SHARE_ALIKE


# ---------------------------------------------------------------------------
# Les vocabulaires fermés — étendus, jamais contournés
# ---------------------------------------------------------------------------

def test_les_valeurs_produites_sont_toutes_dans_les_vocabulaires_fermes():
    """§4 : on étend le `frozenset`, on ne le contourne pas."""
    assert TYPE_SOURCE in KNOWN_SOURCE_TYPES
    assert CATEGORIE_SOURCE in KNOWN_CATEGORIE_SOURCES
    for famille in ("mandat_parlementaire", "groupe_politique", "commission"):
        entree = normalize_mandat(_compose(famille))
        assert entree["categorie"] in KNOWN_CATEGORIES
        assert entree["type_organe_source"] in KNOWN_TYPES_ORGANE_SOURCE
    for type_code in ("ETUDES", "AMITIE", "INFO", "LIAISON"):
        entree = normalize_mandat(_compose("groupe_senatorial", type_groupe_code=type_code))
        assert entree["categorie"] in KNOWN_CATEGORIES
        assert entree["type_organe_source"] in KNOWN_TYPES_ORGANE_SOURCE


def test_senat_et_nossenateurs_restent_deux_types_distincts():
    """`nossenateurs` désignait un réutilisateur tiers sous ODbL ; `senat` est le
    producteur sous Licence Ouverte. Les confondre déplacerait la clause de
    partage à l'identique dans le mauvais sens."""
    assert {"senat", "nossenateurs"} <= KNOWN_SOURCE_TYPES
    assert TYPE_SOURCE != "nossenateurs"


# ---------------------------------------------------------------------------
# Le périmètre : qui reçoit ces mandats
# ---------------------------------------------------------------------------

def test_seuls_les_candidats_declares_recoivent_les_mandats_senatoriaux():
    """Mesuré sur les 36 profils appariés : le lot verserait **+120** entrées
    aux 2 candidats déclarés et **+1 674** aux 34 membres de roster, doublant
    les mandats de ces derniers.

    890 de ces 1 674 seraient des groupes d'amitié et d'études, qu'aucune vue
    n'affiche : ils n'iraient que dans `mandats_agreges`, un agrégat que #853
    conteste déjà. Doubler le volume d'un champ dont on sait qu'il compte la
    mauvaise chose n'est pas un gain."""
    from population_profils import CANDIDAT_DECLARE, ROSTER_GROUPE
    from normalize_senat import POPULATIONS_PUBLIEES, est_dans_le_perimetre

    assert POPULATIONS_PUBLIEES == frozenset({CANDIDAT_DECLARE})
    assert est_dans_le_perimetre(CANDIDAT_DECLARE)
    assert not est_dans_le_perimetre(ROSTER_GROUPE)


def test_une_provenance_inconnue_est_hors_perimetre():
    """Publier sur un profil dont on ne sait pas ce qu'il est reviendrait à
    décider à sa place (§2 règle 5)."""
    from normalize_senat import est_dans_le_perimetre

    assert not est_dans_le_perimetre(None)
    assert not est_dans_le_perimetre("population_future")


# ---------------------------------------------------------------------------
# Les organismes extra-parlementaires
# ---------------------------------------------------------------------------

def test_un_organisme_extra_parlementaire_se_range_et_dit_qui_a_designe():
    """L'Assemblée en publie 3 pour `bruno-retailleau`, **sans date**. Le Sénat
    en date 13, avec le rang et le désignateur — `SENCOMECON`, la commission des
    affaires économiques. Une désignation sans son désignateur perd ce qui en
    fait un fait institutionnel."""
    entree = normalize_mandat(_compose(
        "extra_parlementaire", label="Commission du dividende numérique",
        titulaire_ou_suppleant="TITULAIRE", designe_par="Commission des affaires économiques"))

    assert entree["categorie"] == "extra_parlementaire"
    assert entree["type_organe_source"] == "organisme_extra_parlementaire_senat"
    assert entree["label"] == "Commission du dividende numérique"
