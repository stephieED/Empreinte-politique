"""#901 — l'index des dossiers européens : un code de procédure devient un titre.

Un amendement européen publie son `texte_vise` — `"2021/0136(COD)"` — sur 100 %
des 7 303 entrées, et `pivotAdapter.js` le lit déjà. Ce qui manquait n'était ni
une collecte ni une lecture : `resolveDossier` cherche la référence dans l'index
**français**, ne l'y trouve pas, et la fiche affiche « 590 amendements · 0
dossiers ». Un code de procédure sans titre attaché ne dit rien à un lecteur.

Cet index est ce référentiel, et rien d'autre : référence → titre, type, stade.
"""

import json
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from dossiers_europeens import (
    matieres,
    matieres_non_resolu,  # noqa: E402
    SCHEMA_VERSION,
    DumpDossiersIndisponible,
    construire,
    document,
    identifiant,
    references_visees,
)


def _dossier(reference, stage="Procedure completed", **procedure):
    proc = {"reference": reference, "title": "Un intitulé législatif",
            "type": "COD - Ordinary legislative procedure"}
    if stage is not None:
        proc["stage_reached"] = stage
    proc.update(procedure)
    return {"procedure": proc, "meta": {"source": f"https://oeil.europarl.europa.eu/{reference}"}}


def _dump(tmp_path, dossiers):
    """Un dump `.zst` au format ParlTrack : un tableau JSON, séparateur en tête."""
    import zstandard as zstd
    chemin = tmp_path / "ep_dossiers.json.zst"
    lignes = [("[" if r == 0 else ",") + json.dumps(d, ensure_ascii=False)
              for r, d in enumerate(dossiers)]
    lignes.append("]")
    chemin.write_bytes(zstd.ZstdCompressor().compress("\n".join(lignes).encode("utf-8")))
    return chemin


def _profil(*references):
    return {"amendements": [
        {"amendement_id": None, "role_signataire": "auteur_principal",
         "amendement_non_resolu": {"institution": "parlement_europeen", "texte_vise": r}}
        for r in references
    ]}


# --------------------------------------------------------------------------
# Le périmètre : ce que les amendements visent
# --------------------------------------------------------------------------

def test_les_references_sont_lues_dans_amendement_non_resolu(tmp_path):
    """`amendement_id` reste `null` pour un amendement européen, et c'est voulu
    (#431) : la référence vit dans le bloc non résolu."""
    (tmp_path / "a.pivot.json").write_text(
        json.dumps(_profil("2021/0136(COD)", "2017/2070(INI)")), encoding="utf-8")
    (tmp_path / "b.pivot.json").write_text(
        json.dumps(_profil("2021/0136(COD)")), encoding="utf-8")

    assert references_visees(tmp_path) == {"2021/0136(COD)", "2017/2070(INI)"}


def test_les_references_sont_aussi_lues_dans_les_textes_portes(tmp_path):
    """La seconde source, et celle qui manquait (#901, 16/09/2026).

    Un `textes_portes[]` européen publie `reference_dossier`, et l'index ne la
    lisait pas : 34 références citées par une fiche — 54 occurrences — ne
    résolvaient nulle part. Les 10 dossiers `RSP` qui y figuraient déjà y
    étaient entrés par la bande, parce qu'un amendement les visait.
    """
    (tmp_path / "a.pivot.json").write_text(json.dumps({
        "textes_portes": [
            {"institution": "parlement_europeen", "reference_dossier": "2024/2698(RSP)"},
            {"institution": "parlement_europeen", "reference_dossier": "2015/2652(RSP)"},
        ],
    }), encoding="utf-8")

    assert references_visees(tmp_path) == {"2024/2698(RSP)", "2015/2652(RSP)"}


def test_les_deux_sources_se_reunissent(tmp_path):
    """Un amendement et un texte porté qui visent le même dossier : une entrée."""
    profil = _profil("2021/0136(COD)")
    profil["textes_portes"] = [
        {"institution": "parlement_europeen", "reference_dossier": "2021/0136(COD)"},
        {"institution": "parlement_europeen", "reference_dossier": "2024/2698(RSP)"},
    ]
    (tmp_path / "a.pivot.json").write_text(json.dumps(profil), encoding="utf-8")

    assert references_visees(tmp_path) == {"2021/0136(COD)", "2024/2698(RSP)"}


#: Copiés de `raphael-glucksmann` (`origin/main` `789537af5`) : un vote européen
#: qui cite son dossier, un qui ne le cite pas, et un vote de l'Assemblée
#: (`gabriel-attal`), qui n'a pas de bloc non résolu.
VOTE_PE_AVEC_DOSSIER = {"scrutin_id": None, "position": "pour", "scrutin_non_resolu": {"institution": "parlement_europeen", "titre": "RC-B9-0006/2019 - Résolution", "nature": "resolution", "reference_dossier": "2019/2730(RSP)", "date": "2019-07-18", "numero_scrutin": 108532, "source_url": "http://www.europarl.europa.eu/RegData/seance_pleniere/proces_verbal/2019/07-18/liste_presence/P9_PV(2019)07-18(RCV)_XC.xml"}}
VOTE_PE_SANS_DOSSIER = {"scrutin_id": None, "position": "pour", "scrutin_non_resolu": {"institution": "parlement_europeen", "titre": "RC-B9-0006/2019 - Résolution 18/07/2019 11:30:30.000", "nature": "resolution", "reference_dossier": None, "date": "2019-07-18", "numero_scrutin": "2019-07-18 00:00:00-9.", "source_url": "http://www.europarl.europa.eu/RegData/seance_pleniere/proces_verbal/2019/07-18/liste_presence/P9_PV(2019)07-18(RCV)_XC.xml"}}
VOTE_AN = {"scrutin_id": "an:15:1", "position": "pour"}


def test_les_references_sont_aussi_lues_dans_les_votes(tmp_path):
    """La troisième source (17/09/2026) : 4 630 références citées par les votes
    européens, dont 296 seulement étaient dans l'index."""
    (tmp_path / "raphael-glucksmann.pivot.json").write_text(json.dumps({
        "votes": [VOTE_PE_AVEC_DOSSIER, VOTE_PE_SANS_DOSSIER, VOTE_AN],
    }), encoding="utf-8")

    assert references_visees(tmp_path) == {"2019/2730(RSP)"}


def test_les_trois_sources_se_reunissent(tmp_path):
    profil = _profil("2021/0136(COD)")
    profil["textes_portes"] = [{"institution": "parlement_europeen", "reference_dossier": "2024/2698(RSP)"}]
    profil["votes"] = [VOTE_PE_AVEC_DOSSIER, {**VOTE_PE_AVEC_DOSSIER, "scrutin_non_resolu": {
        **VOTE_PE_AVEC_DOSSIER["scrutin_non_resolu"], "reference_dossier": "2021/0136(COD)"}}]
    (tmp_path / "a.pivot.json").write_text(json.dumps(profil), encoding="utf-8")

    assert references_visees(tmp_path) == {"2021/0136(COD)", "2024/2698(RSP)", "2019/2730(RSP)"}


def test_un_texte_porte_francais_n_entre_pas_dans_le_perimetre(tmp_path):
    """`institution` sépare les deux corpus, ici comme pour les amendements."""
    (tmp_path / "x.pivot.json").write_text(json.dumps({"textes_portes": [
        {"institution": None, "reference_dossier": "DLR5L17N47389"},
        {"institution": "parlement_europeen", "reference_dossier": None},
        {"institution": "parlement_europeen"},
    ]}), encoding="utf-8")

    assert references_visees(tmp_path) == set()


def test_un_amendement_francais_n_entre_pas_dans_le_perimetre(tmp_path):
    (tmp_path / "x.pivot.json").write_text(json.dumps({"amendements": [
        {"amendement_id": "an:17:1", "amendement_non_resolu": None},
        {"amendement_non_resolu": {"institution": "assemblee_nationale",
                                   "texte_vise": "DLR5L17N47389"}},
    ]}), encoding="utf-8")

    assert references_visees(tmp_path) == set()


def test_seuls_les_dossiers_vises_entrent_dans_l_index(tmp_path):
    """367 références servies, pas les 23 885 dossiers du dump."""
    chemin = _dump(tmp_path, [_dossier("A"), _dossier("B"), _dossier("C")])

    entrees = construire({"B"}, dump_path=chemin)

    assert [e["reference"] for e in entrees] == ["B"]


def test_une_reference_absente_du_dump_ne_produit_aucune_entree(tmp_path):
    """12 des 367, toutes de 2024-2025 : le dump des dossiers est plus ancien
    que celui des amendements. Absence datée, déclarée par l'appelant, jamais
    comblée (§2 règle 5)."""
    entrees = construire({"2025/2084(INI)"}, dump_path=_dump(tmp_path, [_dossier("A")]))

    assert entrees == []


def test_un_dossier_publie_deux_fois_n_entre_qu_une_fois(tmp_path):
    chemin = _dump(tmp_path, [_dossier("A", title="Premier"), _dossier("A", title="Second")])

    entrees = construire({"A"}, dump_path=chemin)

    assert len(entrees) == 1


def test_sans_reference_l_index_est_vide_sans_lire_le_dump():
    assert construire(set()) == []


def test_un_dump_indisponible_leve_au_lieu_de_rendre_un_index_vide(monkeypatch):
    import dossiers_europeens

    monkeypatch.setattr(dossiers_europeens, "ensure_dump", lambda *a, **k: None)

    with pytest.raises(DumpDossiersIndisponible):
        dossiers_europeens.construire({"2021/0136(COD)"})


# --------------------------------------------------------------------------
# Ce que l'entrée porte
# --------------------------------------------------------------------------

def test_l_entree_porte_le_titre_le_type_et_le_stade(tmp_path):
    entrees = construire({"2017/2070(INI)"}, dump_path=_dump(tmp_path, [
        _dossier("2017/2070(INI)", title="Implementation of the common commercial policy",
                 type="INI - Own-initiative procedure")]))

    assert entrees[0]["id"] == "pe-dossier:2017/2070(INI)"
    assert entrees[0]["titre"] == "Implementation of the common commercial policy"
    assert entrees[0]["type_procedure"] == "INI - Own-initiative procedure"
    assert entrees[0]["stade_procedural"] == "ue_procedure_achevee"


def test_le_stade_passe_par_la_table_de_textes_portes(tmp_path):
    """Une seule fabrique de cette correspondance : la recopier ici ferait
    diverger deux tables le jour où la source ajoute une valeur."""
    from normalize_parltrack_dumps import STADE_UE_PAR_LIBELLE_SOURCE

    entrees = construire({"A"}, dump_path=_dump(tmp_path, [
        _dossier("A", stage="Awaiting Parliament 2nd reading")]))

    assert entrees[0]["stade_procedural"] == (
        STADE_UE_PAR_LIBELLE_SOURCE["Awaiting Parliament 2nd reading"])


def test_un_dossier_sans_stade_porte_son_motif(tmp_path):
    entrees = construire({"A"}, dump_path=_dump(tmp_path, [_dossier("A", stage=None)]))

    assert entrees[0]["stade_procedural"] is None
    assert entrees[0]["stade_procedural_non_resolu"] == {"motif": "source_sans_stade"}


def test_un_stade_inconnu_conserve_le_libelle_recu(tmp_path):
    entrees = construire({"A"}, dump_path=_dump(tmp_path, [
        _dossier("A", stage="Awaiting alien invasion")]))

    assert entrees[0]["stade_procedural"] is None
    assert entrees[0]["stade_procedural_non_resolu"]["valeur_source"] == "Awaiting alien invasion"


def test_le_titre_n_est_pas_traduit(tmp_path):
    """Traduire un intitulé législatif produirait un titre que personne n'a
    écrit et qu'aucune source ne confirme (§2 règle 2)."""
    anglais = "Use of passenger name record (PNR) data for the prevention of terrorist offences"
    entrees = construire({"A"}, dump_path=_dump(tmp_path, [_dossier("A", title=anglais)]))

    assert entrees[0]["titre"] == anglais


def test_l_ordre_suit_la_reference(tmp_path):
    """Un ordre instable ferait bouger l'index sans que rien n'ait bougé."""
    chemin = _dump(tmp_path, [_dossier("2021/0136(COD)"), _dossier("2017/2070(INI)")])

    entrees = construire({"2021/0136(COD)", "2017/2070(INI)"}, dump_path=chemin)

    assert [e["reference"] for e in entrees] == ["2017/2070(INI)", "2021/0136(COD)"]


def test_l_entete_nomme_le_schema_et_la_licence_de_parltrack():
    """`licence_donnees` vient de `licences.py`, jamais écrit en dur (#909)."""
    entete = document([])

    assert entete["schema_version"] == SCHEMA_VERSION
    assert "ODbL" in entete["licence_donnees"] and "ParlTrack" in entete["licence_donnees"]
    assert entete["dossiers"] == []


def test_l_identifiant_ne_se_confond_pas_avec_celui_d_un_scrutin():
    """`pe:` nomme un scrutin, `pe-dossier:` un dossier. Deux espaces de noms
    distincts, comme `an:` l'est des deux."""
    from scrutins_europeens import identifiant as identifiant_scrutin

    assert identifiant("2021/0136(COD)") == "pe-dossier:2021/0136(COD)"
    assert not identifiant("X").startswith(identifiant_scrutin("X"))


# --------------------------------------------------------------------------
# La commission saisie au fond (#901, besoin remonté par l'interface)
# --------------------------------------------------------------------------

from dossiers_europeens import commissions_au_fond  # noqa: E402


def test_la_saisine_pour_avis_n_est_pas_une_saisine_au_fond():
    """« Committee Opinion » et ses variantes désignent une commission
    consultée, pas compétente. Les confondre publierait une compétence que la
    source sépare."""
    entrees = commissions_au_fond({"committees": [
        {"committee": "ENVI", "committee_full": "Environment", "type": "Committee Opinion"},
        {"committee": "JURI", "committee_full": "Legal Affairs", "type": "Responsible Committee"},
    ]})

    assert [e["sigle"] for e in entrees] == ["JURI"]


def test_une_saisine_conjointe_est_aplatie_en_une_entree_par_sigle():
    """La source met des LISTES dans `committee` et `committee_full` quand la
    saisine est conjointe — 36 des 402 entrées au fond de notre population.
    Publier une liste dans un champ scalaire obligerait chaque consommateur à
    gérer les deux formes."""
    entrees = commissions_au_fond({"committees": [{
        "committee": ["ECON", "JURI"],
        "committee_full": ["Economic and Monetary Affairs", "Legal Affairs"],
        "type": "Joint Responsible Committee"}]})

    assert entrees == [
        {"sigle": "ECON", "nom": "Economic and Monetary Affairs",
         "type_source": "Joint Responsible Committee", "statut": "au_fond_conjointe"},
        {"sigle": "JURI", "nom": "Legal Affairs",
         "type_source": "Joint Responsible Committee", "statut": "au_fond_conjointe"},
    ]


def test_le_libelle_de_type_est_conserve_tel_quel():
    """Quatre états que la source distingue : saisine au fond, ancienne,
    conjointe, ancienne conjointe. Les fondre en un booléen perdrait le fait
    qu'une commission a été dessaisie."""
    entrees = commissions_au_fond({"committees": [
        {"committee": "LIBE", "committee_full": "Civil Liberties",
         "type": "Former Responsible Committee"}]})

    assert entrees[0]["type_source"] == "Former Responsible Committee"


def test_le_champ_lu_est_type_et_non_responsible():
    """LE piège : `responsible: true` n'est renseigné que sur 2,9 % des entrées,
    `type` sur 97 %. S'y fier rendait une commission au fond pour 1,2 % des
    dossiers au lieu de 97,7 %."""
    entrees = commissions_au_fond({"committees": [
        {"committee": "JURI", "committee_full": "Legal Affairs",
         "responsible": True, "type": "Committee Opinion"},
        {"committee": "ECON", "committee_full": "Economic Affairs",
         "responsible": None, "type": "Responsible Committee"},
    ]})

    assert [e["sigle"] for e in entrees] == ["ECON"]


def test_un_sigle_absent_ou_vide_ne_produit_aucune_entree():
    entrees = commissions_au_fond({"committees": [
        {"committee": [], "committee_full": [], "type": "Responsible Committee"},
        {"committee": None, "type": "Responsible Committee"},
        {"committee": "", "type": "Responsible Committee"},
    ]})

    assert entrees == []


def test_un_nom_manquant_laisse_le_sigle_publie():
    """Le sigle est ce que l'interface affiche ; l'absence du nom complet ne
    doit pas emporter le fait (§2 règle 5)."""
    entrees = commissions_au_fond({"committees": [
        {"committee": "JURI", "type": "Responsible Committee"}]})

    assert entrees == [{"sigle": "JURI", "nom": None,
                        "type_source": "Responsible Committee",
                        "statut": "au_fond"}]


def test_un_dossier_sans_commission_rend_une_liste_vide(tmp_path):
    """8 des 355 dossiers de l'index sont dans ce cas. Une liste vide dit
    « la source n'en publie aucune » ; l'absence de clé ferait croire à un
    champ oublié."""
    entrees = construire({"A"}, dump_path=_dump(tmp_path, [_dossier("A")]))

    assert entrees[0]["commissions_au_fond"] == []


# --------------------------------------------------------------------------
# Les trois questions que l'interface doit pouvoir poser sans inférence
# (arbitrage de la propriétaire, 14/09/2026)
#
# Les quatre libellés se DISTINGUENT, ils ne se fondent pas : écraser
# publierait comme compétente une commission dessaisie, et effacerait qu'une
# saisine est partagée — une compétence que la source n'établit pas
# (§2 règle 2). L'arbitrage tient à sa réversibilité : fondre plus tard à
# l'affichage reste possible, re-séparer ce qu'on a écrasé ne l'est pas.
#
# `type_source` garde le verbatim ; `statut` est ce verbatim LU, pour qu'aucun
# consommateur n'ait à reconnaître une chaîne anglaise pour savoir si la
# commission est compétente aujourd'hui.
# --------------------------------------------------------------------------

from dossiers_europeens import (
    matieres,
    matieres_non_resolu,  # noqa: E402
    KNOWN_STATUTS_COMMISSION_AU_FOND,
    commissions_au_fond_non_resolu,
)


def _au_fond(type_source, sigle="JURI"):
    return commissions_au_fond({"committees": [
        {"committee": sigle, "committee_full": "Legal Affairs", "type": type_source}]})


@pytest.mark.parametrize("type_source,statut", [
    ("Responsible Committee", "au_fond"),
    ("Joint Responsible Committee", "au_fond_conjointe"),
    ("Former Responsible Committee", "ancienne_au_fond"),
    ("Former Joint Committee Responsible", "ancienne_au_fond_conjointe"),
])
def test_chaque_libelle_de_la_source_a_son_statut(type_source, statut):
    """Les quatre libellés relevés le 14/09/2026 sur les 355 dossiers de l'index."""
    entree = _au_fond(type_source)[0]

    assert entree["statut"] == statut
    assert entree["type_source"] == type_source, "le verbatim ne se perd jamais"


def test_le_statut_repond_aux_trois_questions_sans_lire_l_anglais():
    """Compétente aujourd'hui, partagée, ou dessaisie — sans reconnaître de chaîne."""
    en_vigueur = {"au_fond", "au_fond_conjointe"}

    assert _au_fond("Responsible Committee")[0]["statut"] in en_vigueur
    assert _au_fond("Joint Responsible Committee")[0]["statut"] in en_vigueur
    assert _au_fond("Former Responsible Committee")[0]["statut"] not in en_vigueur
    assert _au_fond("Former Joint Committee Responsible")[0]["statut"] not in en_vigueur


def test_une_dessaisie_ne_peut_pas_etre_prise_pour_la_competente():
    """La question 3 de l'interface : distinguer sans confusion possible."""
    entrees = commissions_au_fond({"committees": [
        {"committee": "LIBE", "committee_full": "Civil Liberties",
         "type": "Former Responsible Committee"},
        {"committee": "JURI", "committee_full": "Legal Affairs",
         "type": "Responsible Committee"},
    ]})

    competentes = [e["sigle"] for e in entrees if e["statut"] == "au_fond"]

    assert competentes == ["JURI"]
    assert len(entrees) == 2, "la dessaisie reste publiée, elle n'est pas filtrée"


def test_un_libelle_inconnu_n_est_ni_devine_ni_jete():
    """Vocabulaire fermé (`AGENTS.md` §4) : l'étendre est un geste délibéré.

    Le contenir est un fait de la source, le classer est notre affirmation. Un
    libellé que la table ne connaît pas sort `statut: None` avec sa valeur
    reçue — §2 règle 5.
    """
    entree = _au_fond("Provisionally Responsible Committee")[0]

    assert entree["statut"] is None
    assert entree["statut_non_resolu"] == {
        "motif": "libelle_inconnu", "valeur": "Provisionally Responsible Committee"}
    assert entree["sigle"] == "JURI", "l'entrée reste publiée"


def test_le_vocabulaire_des_statuts_est_ferme():
    assert KNOWN_STATUTS_COMMISSION_AU_FOND == {
        "au_fond", "au_fond_conjointe", "ancienne_au_fond", "ancienne_au_fond_conjointe"}


# --- absence à la source contre absence de lecture -------------------------

def test_aucune_commission_a_la_source_porte_son_motif():
    """8 des 355 : le dump ne porte aucune entrée au fond. Un fait, pas un trou."""
    dossier = {"committees": [
        {"committee": "ENVI", "committee_full": "Environment", "type": "Committee Opinion"}]}

    assert commissions_au_fond_non_resolu(dossier, []) == {
        "motif": "source_sans_commission_au_fond"}


def test_une_saisine_conjointe_sans_nom_ne_se_confond_pas_avec_une_absence():
    """6 des 355, et c'est le cas qu'une liste vide effaçait.

    La source AFFIRME une saisine conjointe et laisse `committee` à la liste
    vide. L'affirmation existe, son contenu manque : le lire comme « aucune
    commission au fond » perdrait le fait que deux commissions se la partagent.
    """
    dossier = {"committees": [
        {"committee": [], "committee_full": [], "type": "Joint Responsible Committee"},
        {"committee": [], "committee_full": [], "type": "Joint Responsible Committee"},
    ]}

    assert commissions_au_fond(dossier) == []
    assert commissions_au_fond_non_resolu(dossier, []) == {
        "motif": "saisine_conjointe_sans_commission_nommee"}


def test_le_motif_est_absent_des_qu_une_commission_est_nommee():
    """Même contrat que `sort_non_resolu` (#747) : ni les deux, ni aucun des deux."""
    dossier = {"committees": [
        {"committee": "JURI", "committee_full": "Legal Affairs",
         "type": "Responsible Committee"}]}
    publiees = commissions_au_fond(dossier)

    assert publiees
    assert commissions_au_fond_non_resolu(dossier, publiees) is None


def test_le_motif_atteint_le_dossier_publie(tmp_path):
    """De bout en bout : c'est `construire` qui doit le poser, pas le lecteur."""
    entrees = construire({"A"}, dump_path=_dump(tmp_path, [_dossier("A")]))

    assert entrees[0]["commissions_au_fond"] == []
    assert entrees[0]["commissions_au_fond_non_resolu"] == {
        "motif": "source_sans_commission_au_fond"}


# --------------------------------------------------------------------------
# Les matières OEIL — l'axe que la commission au fond ne couvre pas (#901)
# --------------------------------------------------------------------------

def test_la_matiere_est_lue_quand_la_source_donne_un_dict():
    """La forme courante : 387 des 389 dossiers visés."""
    assert matieres({"procedure": {"subject": {
        "7.10.06": "Asylum, refugees, displaced persons",
        "7.10.08": "Migration policy",
    }}}) == [
        {"code": "7.10.06", "libelle": "Asylum, refugees, displaced persons"},
        {"code": "7.10.08", "libelle": "Migration policy"},
    ]


def test_la_matiere_est_lue_quand_la_source_donne_une_liste():
    """L'autre forme, sur 2 dossiers : code et libellé COLLÉS dans une chaîne.

    Un lecteur qui ne connaîtrait que le dict perdrait ces deux-là sans erreur
    visible — c'est exactement le genre d'absence que personne ne mesure.
    """
    assert matieres({"procedure": {"subject": [
        "2.10.01 Customs union, tax and duty-free, Community transit",
        "6.20.03 Bilateral economic and trade agreements and relations",
    ]}}) == [
        {"code": "2.10.01", "libelle": "Customs union, tax and duty-free, Community transit"},
        {"code": "6.20.03", "libelle": "Bilateral economic and trade agreements and relations"},
    ]


def test_les_matieres_sont_triees_par_code():
    lu = matieres({"procedure": {"subject": {"8.20.01": "b", "3.30.06": "a"}}})
    assert [m["code"] for m in lu] == ["3.30.06", "8.20.01"]


def test_une_entree_sans_code_lisible_est_publiee_sans_code_plutot_que_perdue():
    lu = matieres({"procedure": {"subject": ["Politique inclassable"]}})
    assert lu == [{"code": "Politique inclassable", "libelle": None}]


def test_un_dossier_sans_matiere_dit_pourquoi():
    """Jamais une liste vide nue : une absence porte son motif (§2 règle 5)."""
    assert matieres({"procedure": {}}) == []
    assert matieres_non_resolu({"procedure": {}}, []) == {"motif": "source_sans_matiere"}
    assert matieres_non_resolu({}, [{"code": "6", "libelle": "x"}]) is None


def test_l_index_publie_les_matieres(tmp_path):
    """Le champ atteint l'entrée d'index, pas seulement la fonction."""
    (tmp_path / "a.pivot.json").write_text(json.dumps({"textes_portes": [
        {"institution": "parlement_europeen", "reference_dossier": "2015/2833(RSP)"},
    ]}), encoding="utf-8")
    dump = _dump(tmp_path, [{
        "procedure": {"reference": "2015/2833(RSP)", "title": "T",
                      "type": "RSP - Resolutions on topical subjects",
                      "stage_reached": "Procedure completed",
                      "subject": {"7.10.08": "Migration policy"}},
        "committees": [],
    }])
    entrees = construire(references_visees(tmp_path), dump_path=dump)
    assert entrees[0]["matieres"] == [{"code": "7.10.08", "libelle": "Migration policy"}]
    assert "matieres_non_resolu" not in entrees[0]
