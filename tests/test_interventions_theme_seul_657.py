"""Collecte d'interventions RÉDUITE AU THÈME pour les membres de roster (#657).

Le défaut corrigé : `tags_thematiques` dérive intégralement d'`interventions[]`,
et les 468 membres de roster publiaient `interventions: []` — l'« empreinte
thématique » de chaque fiche de groupe était donc celle d'UNE personne (470
étiquettes sur `AN:RN` portées par Marine Le Pen, 382 sur `AN:SOC` par Jérôme
Guedj, zéro sur `AN:LFI` et `AN:LR`).

Le mode réduit collecte les débats Syceron SANS leur verbatim. Ce que ces tests
tiennent, dans l'ordre où ça peut casser :

1. la réduction ne coûte PAS UNE étiquette — `sujet` vient du titre de point,
   jamais du texte (mesuré sur la fixture réelle, pas supposé) ;
2. l'entrée réduite DÉCLARE qu'elle l'est, et `null` n'est pas la déclaration ;
3. les deux formes d'index ne se mélangent JAMAIS dans le cache — c'est #447
   (« un répertoire qui existe n'est pas la preuve de ce qu'il contient »)
   transposé au contenu d'une entrée ;
4. `couverture` cesse de dire `non_collecte`/`par_decision` sur une liste pleine ;
5. un candidat déclaré n'est jamais collecté en réduit — sa forme complète
   serait gelée par la fusion additive.

Fixtures : réductions VERBATIM de comptes rendus réels (#510), les mêmes que
`test_parse_syceron.py`. Aucun accès réseau, aucune lecture de `pivot_data/` ni
de `raw_data/profiles/`.
"""

import argparse
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import candidate_profile as cp
import couverture_profil
import generate_all_profiles
import normalize_profil
from parse_syceron import parse_syceron_xml
from schema_pivot import (
    COLLECTE_THEME_SEUL,
    KNOWN_COLLECTES_INTERVENTION,
    make_empty_profil,
    validate_profil,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"
STRUCTURE = FIXTURES / "syceron_reel_leg17_structure.xml"
IMBRICATION = FIXTURES / "syceron_reel_leg17.xml"


# ---------------------------------------------------------------------------
# 1. Le parseur : ce que la réduction retire, et ce qu'elle ne retire pas
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fixture", [STRUCTURE, IMBRICATION])
def test_la_reduction_ne_coute_pas_une_seule_etiquette(fixture):
    """`sujet` et `type_detail` sortent IDENTIQUES sans le verbatim.

    C'est la propriété qui rend tout le lot possible : les deux champs viennent
    du titre de point (`_titre_point`), jamais de `_extract_texte`. Mesuré ici
    sur l'archive réduite, et à pleine échelle le 31/08/2026 — 287 789 entrées
    indexées pour la 17e et 305 862 pour la 16e dans les DEUX modes, au nombre
    près.
    """
    complet = parse_syceron_xml(fixture.read_bytes())
    reduit = parse_syceron_xml(fixture.read_bytes(), avec_texte=False)

    assert len(reduit["interventions"]) == len(complet["interventions"])
    assert [i["sujet"] for i in reduit["interventions"]] == [
        i["sujet"] for i in complet["interventions"]
    ]
    assert [i["type_detail"] for i in reduit["interventions"]] == [
        i["type_detail"] for i in complet["interventions"]
    ]
    assert [i["orateur_id_source"] for i in reduit["interventions"]] == [
        i["orateur_id_source"] for i in complet["interventions"]
    ]


def test_le_format_tombe_a_null_et_pas_a_reaction_courte():
    """`format` se déduit du nombre de MOTS du verbatim (`_infer_format`).

    Sans verbatim, « reaction_courte » serait un défaut déguisé en mesure, sur
    la totalité du corpus réduit — le contraire exact de la règle 5 d'AGENTS.md.
    """
    complet = parse_syceron_xml(STRUCTURE.read_bytes())
    reduit = parse_syceron_xml(STRUCTURE.read_bytes(), avec_texte=False)

    assert any(i["format"] == "prise_de_parole_developpee" for i in complet["interventions"])
    assert {i["format"] for i in reduit["interventions"]} == {None}
    assert {i["texte"] for i in reduit["interventions"]} == {None}


# ---------------------------------------------------------------------------
# 2. L'entrée réduite déclare qu'elle l'est
# ---------------------------------------------------------------------------

def _entree_brute_reduite() -> dict:
    """Une entrée d'index réduite, produite par le vrai chemin de collecte."""
    parsed = parse_syceron_xml(STRUCTURE.read_bytes(), avec_texte=False)
    for rang, intervention in enumerate(parsed["interventions"]):
        resultat = cp._parse_syceron_intervention_entry(
            intervention, "17", rang, theme_seul=True
        )
        if resultat is not None and intervention.get("sujet"):
            return resultat[1]
    pytest.fail("aucune entrée indexable avec sujet dans la fixture")


def test_l_entree_brute_reduite_porte_le_marqueur_et_pas_de_verbatim():
    entree = _entree_brute_reduite()
    assert entree["collecte"] == COLLECTE_THEME_SEUL
    # ABSENTES, pas nulles : `"texte": null` se lirait « cette prise de parole
    # n'a pas de verbatim », un fait sur la personne, là où le fait porte sur
    # le run.
    for absente in ("texte", "fonction", "format", "point_ordre_du_jour", "seance_ref"):
        assert absente not in entree, absente
    # Ce qui reste : la clé de fusion, la matière thématique, la traçabilité.
    assert entree["id"].startswith("syceron_")
    assert entree["sujet"]
    assert entree["url"].startswith("https://")
    assert entree["legislature"] == "17"


def test_l_url_d_archive_n_est_plus_recopiee_trois_fois():
    """L'entrée complète porte `source`, `source_url` ET `url` — la même URL.

    Trois chemins de normalisation historiques la lisent sous trois noms ; le
    mode réduit n'en garde que celui que `_normalize_intervention` lit
    réellement. Mesuré : 330 octets par entrée d'index, sur 593 651 entrées.
    """
    parsed = parse_syceron_xml(STRUCTURE.read_bytes())
    complete = cp._parse_syceron_intervention_entry(parsed["interventions"][0], "17", 0)
    assert complete is not None
    assert complete[1]["source"] == complete[1]["source_url"] == complete[1]["url"]

    reduite = _entree_brute_reduite()
    assert "source" not in reduite and "source_url" not in reduite


def test_l_entree_pivot_reduite_porte_le_theme_et_le_marqueur():
    pivot = normalize_profil._normalize_intervention(_entree_brute_reduite())
    assert pivot["collecte"] == COLLECTE_THEME_SEUL
    assert pivot["theme_officiel"]
    assert pivot["intervention_id"].startswith("syceron_")
    assert pivot["source"]["type"] == "syceron"
    assert pivot["source"]["legislature"] == "17"
    assert pivot["source_url"].startswith("https://")
    assert "texte" not in pivot and "sujet" not in pivot


def test_une_entree_complete_reste_complete():
    """La forme pleine ne bouge pas : `collecte` est ABSENT, pas `null`.

    Une clé toujours présente ferait de la forme complète une valeur parmi
    d'autres et rendrait les 16 242 entrées déjà publiées rétroactivement
    « non déclarées ».
    """
    parsed = parse_syceron_xml(STRUCTURE.read_bytes())
    complete = cp._parse_syceron_intervention_entry(parsed["interventions"][0], "17", 0)
    pivot = normalize_profil._normalize_intervention(complete[1])
    assert "collecte" not in pivot
    assert "texte" in pivot and "sujet" in pivot and "seance" in pivot


# ---------------------------------------------------------------------------
# 3. Le schéma : `collecte` est une valeur fermée
# ---------------------------------------------------------------------------

def _profil_avec(interventions: list[dict]) -> dict:
    profil = make_empty_profil("un-slug", "Un Nom")
    profil["interventions"] = interventions
    return profil


def test_le_schema_accepte_l_entree_reduite():
    pivot = normalize_profil._normalize_intervention(_entree_brute_reduite())
    assert validate_profil(_profil_avec([pivot])) == []


def test_le_schema_refuse_une_forme_de_collecte_inconnue():
    erreurs = validate_profil(_profil_avec([{"collecte": "resume_seul"}]))
    assert any("collecte" in e for e in erreurs)
    assert COLLECTE_THEME_SEUL in KNOWN_COLLECTES_INTERVENTION


# ---------------------------------------------------------------------------
# 4. Les tags : le point de tout le lot
# ---------------------------------------------------------------------------

def test_les_tags_thematiques_sortent_d_une_collecte_reduite():
    """De `interventions: []` / `tags_thematiques: []` à une liste peuplée.

    Mesuré à pleine échelle le 31/08/2026 : 448 des 468 membres de roster
    reçoivent au moins une intervention, et l'empreinte d'`AN:LFI` passe de 0 à
    1 981 étiquettes portées par 76 membres sur 76.
    """
    parsed = parse_syceron_xml(STRUCTURE.read_bytes(), avec_texte=False)
    brut = {
        "id": "un-slug",
        "identite": {"nom": "Un Nom"},
        "interventions": [
            entree[1]
            for rang, i in enumerate(parsed["interventions"])
            if (entree := cp._parse_syceron_intervention_entry(i, "17", rang, theme_seul=True))
        ],
        "meta": {"warnings": []},
    }
    assert brut["interventions"], "la fixture doit indexer au moins une entrée"

    pivot = normalize_profil.normalize_profil(brut)
    assert pivot["tags_thematiques"], "la collecte réduite doit peupler les tags"
    assert all(t == t.strip().lower() for t in pivot["tags_thematiques"])


# ---------------------------------------------------------------------------
# 5. Les deux formes d'index ne se mélangent jamais
# ---------------------------------------------------------------------------

def _cache(tmp_path: Path, monkeypatch) -> Path:
    monkeypatch.setattr(cp, "SYCERON_CACHE_DIR", tmp_path)
    monkeypatch.setattr(cp, "_SYCERON_INDEX_NON_PUBLIE", {})
    return tmp_path


def test_les_deux_index_vivent_dans_deux_repertoires(tmp_path, monkeypatch):
    racine = _cache(tmp_path, monkeypatch)
    cp._write_syceron_index_par_acteur("17", {"PA1": [{"id": "a", "texte": "long"}]})
    cp._write_syceron_index_par_acteur(
        "17", {"PA1": [{"id": "a", "collecte": COLLECTE_THEME_SEUL}]}, theme_seul=True
    )
    assert (racine / "17" / "index_par_acteur" / "PA1.json").is_file()
    assert (racine / "17" / "index_par_acteur_theme" / "PA1.json").is_file()


def test_le_mode_complet_ne_lit_jamais_l_index_reduit(tmp_path, monkeypatch):
    """Sinon un `texte` absent par DÉCISION se publierait comme un constat.

    C'est la moitié de #510 qui a survécu le plus longtemps : une source qui
    rend moins, sans que rien ne le dise.
    """
    _cache(tmp_path, monkeypatch)
    # La tranche porte `sujet_code_grammaire` : sans lui, #719 la refuserait
    # comme périmée et ce test passerait pour la mauvaise raison.
    cp._write_syceron_index_par_acteur(
        "17",
        {"PA1": [{"id": "a", "sujet_code_grammaire": None,
                  "collecte": COLLECTE_THEME_SEUL}]},
        theme_seul=True,
    )
    assert cp._read_cached_interventions_syceron_acteur("17", "PA1") is None


def test_le_mode_reduit_lit_l_index_complet_et_le_reduit(tmp_path, monkeypatch):
    """L'asymétrie qui évite de reconstruire l'index en CI.

    `extract-an` publie l'index complet avant que la matrice roster ne démarre
    (`needs:`) : le mode réduit le lit et jette les champs lourds, au lieu de
    reparcourir 344 + 324 Mo de XML dans chacun des 8 shards.
    """
    _cache(tmp_path, monkeypatch)
    cp._write_syceron_index_par_acteur(
        "17",
        {"PA1": [{"id": "a", "date": "2025-01-01", "sujet": "Un sujet",
                  "sujet_code_grammaire": "DISC_ARTICLES_1_1",
                  "session_ref": "S", "url": "https://x", "legislature": "17",
                  "texte": "un très long verbatim"}]},
    )
    entrees = cp._read_cached_interventions_syceron_acteur("17", "PA1", theme_seul=True)
    assert entrees == [{
        "id": "a", "date": "2025-01-01", "type_detail": None, "sujet": "Un sujet",
        # #710 — le code du point qui a fourni le sujet suit le sujet jusque dans
        # l'entrée réduite : sans lui, `backfill_sujet_seance` ne pourrait jamais
        # corriger un créneau de séance déjà publié sur un membre de roster, et le
        # mode « thème seul » serait le seul à ne pas guérir. La VALEUR est
        # vérifiée, pas seulement la clé : `_reduire_au_theme` la poserait à
        # `None` même sur un index qui ne la porte pas, et c'est justement ce que
        # #719 refuse en amont.
        "sujet_code_grammaire": "DISC_ARTICLES_1_1",
        "session_ref": "S", "url": "https://x", "legislature": "17",
        "collecte": COLLECTE_THEME_SEUL,
    }]


def test_le_memo_process_distingue_les_deux_formes(tmp_path, monkeypatch):
    """Sans ça, un index réduit non publié serait servi à un appelant qui a
    demandé le verbatim, pour le reste du process et sans un mot."""
    _cache(tmp_path, monkeypatch)
    assert cp._syceron_memo_key("17", True) != cp._syceron_memo_key("17", False)


# ---------------------------------------------------------------------------
# 6. `couverture` cesse de mentir sur une liste pleine
# ---------------------------------------------------------------------------

def _profil_roster(collecte_ecartee) -> dict:
    profil = make_empty_profil("un-membre", "Un Membre", provenance="roster_groupe")
    if collecte_ecartee is not None:
        profil["meta"]["collecte_ecartee"] = collecte_ecartee
    return profil


def test_un_membre_de_roster_qui_a_des_interventions_n_est_plus_non_collecte():
    couverture = couverture_profil.deriver(_profil_roster([]), constate_le="2026-08-31")
    etats = {e["etat"] for e in couverture["interventions"]}
    assert "non_collecte" not in etats, (
        "le repli par provenance publiait `non_collecte`/`par_decision` sur une "
        "liste pleine, sous une preuve nommant un drapeau que le run n'a pas passé"
    )


def test_un_run_qui_ecarte_encore_les_interventions_le_dit_toujours():
    couverture = couverture_profil.deriver(
        _profil_roster(["interventions", "textes_portes"]), constate_le="2026-08-31"
    )
    (entree,) = couverture["interventions"]
    assert entree["etat"] == "non_collecte"
    assert entree["cause"] == "par_decision"


def test_le_repli_par_provenance_survit_pour_les_profils_sans_declaration():
    """Les 19 profils `roster_groupe` publiés avant #539 ne portent aucune trace
    des drapeaux de leur run : eux seuls dépendent encore de la provenance."""
    couverture = couverture_profil.deriver(_profil_roster(None), constate_le="2026-08-31")
    (entree,) = couverture["interventions"]
    assert entree["etat"] == "non_collecte"
    assert entree["cause"] == "par_decision"
    assert "skip-interventions" in entree["preuve"]


# ---------------------------------------------------------------------------
# 7. Les deux refus : le drapeau mort, et le candidat déclaré
# ---------------------------------------------------------------------------

def test_theme_seul_et_skip_interventions_sont_refuses_ensemble():
    args = argparse.Namespace(
        interventions_theme_seul=True, skip_interventions=True,
        budget_interventions_secondes=0, pivot_only=False, budget_collecte_secondes=0,
    )
    with pytest.raises(SystemExit) as exc:
        generate_all_profiles.valider_budgets(args)
    assert "--interventions-theme-seul" in str(exc.value)


def test_la_liste_des_candidats_declares_est_lue_et_tolere_l_absence(tmp_path):
    fichier = tmp_path / "candidats.json"
    fichier.write_text(json.dumps({"candidats": [
        {"slug": "marine-le-pen"}, {"nom": "Sans slug"}, {"slug": ""},
    ]}), encoding="utf-8")
    assert generate_all_profiles.slugs_candidats_declares(str(fichier)) == frozenset(
        {"marine-le-pen"}
    )
    assert generate_all_profiles.slugs_candidats_declares(
        str(tmp_path / "absent.json")
    ) == frozenset()


def _args_roster(**overrides) -> argparse.Namespace:
    base = dict(
        source="an", pivot_only=False, skip_existing=False,
        skip_interventions=False, interventions_theme_seul=True,
        skip_dossiers_legislatifs=True, budget_interventions_secondes=0,
        budget_collecte_secondes=0, skip_ue=True, pivot=False, no_merge=False,
        enrich_parltrack=False, candidats_declares=frozenset({"marine-le-pen"}),
    )
    base.update(overrides)
    return argparse.Namespace(**base)


def _collecte_espionne(monkeypatch) -> list[dict]:
    """Remplace la collecte réseau et retient les drapeaux qu'elle a reçus."""
    recus: list[dict] = []

    def fausse_collecte(chambre, slug, **kwargs):
        recus.append(kwargs)
        return {
            "slug": slug, "chambre": chambre, "identite": None, "mandats": [],
            "votes": [], "interventions": [], "amendements": [],
            "dossiers_legislatifs": [], "votes_source": None, "source": None,
            "meta": {"warnings": [], "synchro_sources": {}},
        }

    monkeypatch.setattr("generate_all_profiles.build_profile", fausse_collecte)
    return recus


def test_le_mode_reduit_ne_touche_pas_un_candidat_declare(monkeypatch, tmp_path):
    """Un candidat déclaré qui siège dans un groupe est dans les DEUX listes.

    Le collecter en réduit ici gèlerait ses interventions à cette forme pour
    toujours — la fusion additive garde l'ANCIENNE entrée sur la même
    `intervention_id` —, et pourrait remplacer la forme complète déjà publiée si
    son artifact l'emporte au `merge-multiple` (#450). Le run l'écarte donc
    plutôt que de le réduire : c'est `extract-an` qui le collecte en entier.
    """
    recus = _collecte_espionne(monkeypatch)
    generate_all_profiles.process_candidat(
        {"nom": "Marine Le Pen", "slug": "marine-le-pen", "statut": "roster_groupe"},
        _args_roster(), tmp_path / "raw", tmp_path / "pivot",
    )
    assert recus and recus[0]["skip_interventions"] is True
    assert recus[0]["interventions_theme_seul"] is False


def test_un_membre_de_roster_ordinaire_est_bien_collecte_en_reduit(monkeypatch, tmp_path):
    recus = _collecte_espionne(monkeypatch)
    generate_all_profiles.process_candidat(
        {"nom": "Un Membre", "slug": "un-membre", "statut": "roster_groupe"},
        _args_roster(), tmp_path / "raw", tmp_path / "pivot",
    )
    assert recus and recus[0]["skip_interventions"] is False
    assert recus[0]["interventions_theme_seul"] is True


# ---------------------------------------------------------------------------
# 8. Les questions officielles : écartées, et ça ne coûte aucun thème
# ---------------------------------------------------------------------------

def test_une_question_officielle_ne_porte_aucun_theme():
    """Le motif de leur exclusion du mode réduit, vérifié plutôt qu'affirmé.

    Elles n'ont ni `seance_ref` ni `session_ref`, donc `theme_officiel` y est
    `None`, et leur `mots_cles` est vide par construction : elles ne rendent pas
    une seule étiquette. Elles sont en revanche le seul poste réseau du chemin
    interventions qui grandisse avec le nombre de membres.
    """
    question = {
        "id": "question_QANR5L17QE1234", "type_detail": "question",
        "sujet": "Un sujet de question", "mots_cles": [],
        "url": "https://questions.assemblee-nationale.fr/q17/17-1234QE.htm",
    }
    pivot = normalize_profil._normalize_intervention(question)
    assert pivot["theme_officiel"] is None
    assert pivot["mots_cles"] == []
