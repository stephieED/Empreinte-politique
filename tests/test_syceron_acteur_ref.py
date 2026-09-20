"""Résolution de l'identifiant d'orateur Syceron en acteurRef AN (#510).

L'archive Syceron publie l'identifiant d'orateur **nu** (`<orateur><id>847629
</id>`), et `_parse_syceron_intervention_entry` lui appliquait
`re.fullmatch(r"PA\\d+")`. L'index de la source *primaire* des interventions se
construisait donc vide depuis toujours : 0 des 789 interventions publiées à
`f1fff09` venaient de Syceron, et le repli NosDéputés comblait le silence.

**Le 27/08/2026, la résolution est devenue le comportement et le repli a été
retiré** : Syceron est la seule source du chemin interventions, et une collecte
vide reste vide, déclarée dans `meta.warnings[]`. Le drapeau
`--activer-interventions-syceron` n'existe plus — il est refusé bruyamment.

Ces tests travaillent sur des RÉDUCTIONS de l'archive réelle — les deux fixtures
précédentes décrivaient un schéma que l'Assemblée nationale ne publie pas, et
c'est précisément ce qui a rendu le défaut invisible aux tests. Elles sont
retirées.

La forme de l'identifiant est vérifiée sur les **trois** législatures collectées
depuis le 26/08/2026 (archives complètes téléchargées, `content-length` vérifié) :
`forme_inattendue` est à 0 sur chacune, et `id_acteur == "PA" + <orateur><id>`
sur 1 232 692 des 1 235 317 paragraphes qui portent les deux.

Aucun réseau, aucune lecture de `raw_data/` ni de `pivot_data/` : les comptes
rendus servis à `iter_syceron_xml_files` viennent des fixtures.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import candidate_profile as cp
from parse_syceron import parse_syceron_xml

FIXTURES = Path(__file__).resolve().parent / "fixtures"
FIXTURE = FIXTURES / "syceron_reel_leg17.xml"
FIXTURE_ATTRIBUTION_REFUSEE = FIXTURES / "syceron_reel_leg17_attribution_refusee.xml"


# --------------------------------------------------------------------------
# 1. La forme publiée par la source
# --------------------------------------------------------------------------

def test_larchive_publie_lidentifiant_nu_et_le_prefixe_cote_a_cote():
    """`id_acteur="PA847629"` et `<orateur><id>847629</id>` sur le MÊME paragraphe.

    C'est la preuve que le préfixage n'est pas une inférence : la source écrit
    elle-même les deux formes. Mesuré sur les 601 comptes rendus de la 17e :
    `id_acteur == "PA" + orateur/id` sur 289 701 des 289 702 paragraphes qui
    portent les deux.
    """
    brut = FIXTURE.read_text(encoding="utf-8")
    assert "<id>847629</id>" in brut
    assert 'id_acteur="PA847629"' in brut
    assert "<id>PA847629</id>" not in brut

    interventions = parse_syceron_xml(FIXTURE.read_bytes())["interventions"]
    ids = {i.get("orateur_id_source") for i in interventions}
    assert "847629" in ids, "le parseur rend l'identifiant nu, tel que publié"
    assert not any((i or "").startswith("PA") for i in ids if i), (
        "aucun identifiant d'orateur n'est publié préfixé dans l'archive réelle"
    )


# --------------------------------------------------------------------------
# 2. La normalisation, cas par cas
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "valeur, attendu, motif",
    [
        ("847629", "PA847629", "identifiant_nu_prefixe"),
        ("795310", "PA795310", "identifiant_nu_prefixe"),
        ("PA847629", "PA847629", "prefixe_deja_present"),
        # Orateur collectif anonyme (« Un député du groupe LFI-NFP ») : 7 580
        # occurrences sur les trois archives. `PA0` n'existe pas — l'indexer
        # fabriquerait un acteur.
        ("0", None, "orateur_collectif_anonyme"),
        ("000", None, "orateur_collectif_anonyme"),
        # Pseudo-acteur de rôle, hors référentiel AN (977 occurrences). L'archive
        # écrit `id_acteur="PA-125799"` : syntaxiquement formé, ne résout rien.
        ("-125799", None, "pseudo_acteur_hors_referentiel"),
        # Paragraphe sans orateur : didascalie, applaudissements.
        (None, None, "absent"),
        ("", None, "absent"),
        ("   ", None, "absent"),
        (42, None, "absent"),
        # Compteur-témoin : à 0 mesuré sur les TROIS législatures. Non nul, il dit
        # que la forme de l'identifiant a de nouveau bougé sous le code.
        ("PA12A", None, "forme_inattendue"),
        ("acteur/PA123", None, "forme_inattendue"),
    ],
)
def test_normalisation_orateur_id(valeur, attendu, motif):
    assert cp._normaliser_orateur_id_syceron(valeur) == (attendu, motif)


def test_le_prefixage_ne_fabrique_jamais_un_acteur_a_partir_de_zero():
    """`0` ne doit jamais devenir `PA0` — c'est un orateur collectif, pas une personne."""
    ref, _ = cp._normaliser_orateur_id_syceron("0")
    assert ref is None
    assert ref != "PA0"


@pytest.mark.parametrize(
    "valeur, id_acteur, attendu, motif",
    [
        # Concordance : la source confirme le préfixage (1 232 692 paragraphes).
        ("847629", "PA847629", "PA847629", "identifiant_nu_prefixe"),
        # `id_acteur` absent : rien à contredire, le préfixage s'applique.
        ("847629", None, "PA847629", "identifiant_nu_prefixe"),
        ("847629", "", "PA847629", "identifiant_nu_prefixe"),
        # La source REFUSE l'attribution (2 625 paragraphes sur les trois
        # archives, dont 2 524 avec un `<nom>` citant deux orateurs).
        ("335612", "PA0", None, "attribution_refusee_par_la_source"),
        ("267306", "PA0", None, "attribution_refusee_par_la_source"),
        ("923", "PA720746", None, "attribution_refusee_par_la_source"),
        # Le refus ne s'applique qu'aux formes autrement résolubles : un orateur
        # collectif reste un orateur collectif, quel que soit `id_acteur`.
        ("0", "PA0", None, "orateur_collectif_anonyme"),
        ("-125799", "PA-125799", None, "pseudo_acteur_hors_referentiel"),
    ],
)
def test_lattribution_contredite_par_la_source_nest_jamais_forcee(valeur, id_acteur, attendu, motif):
    """La source porte `id_acteur` à côté de l'identifiant nu : quand les deux se
    contredisent, retenir l'identifiant présent fabriquerait une prise de parole
    (§2 règle 2). Même arbitrage que sur les orateurs multiples."""
    assert cp._normaliser_orateur_id_syceron(valeur, id_acteur) == (attendu, motif)


def test_lattribution_refusee_est_lue_sur_larchive_reelle():
    """Bout en bout sur la réduction verbatim du seul cas de la 17e législature."""
    parsed = parse_syceron_xml(FIXTURE_ATTRIBUTION_REFUSEE.read_bytes())
    inter = parsed["interventions"][0]
    assert (inter["orateur_id_source"], inter["orateur_id_acteur"]) == ("335612", "PA0")
    assert cp._normaliser_orateur_id_syceron(
        inter["orateur_id_source"], inter["orateur_id_acteur"]
    ) == (None, "attribution_refusee_par_la_source")


# --------------------------------------------------------------------------
# 3. L'index : plus de mode, et une tranche par acteur
# --------------------------------------------------------------------------

@pytest.fixture
def cache_syceron(tmp_path, monkeypatch):
    """Sert la fixture réelle à `iter_syceron_xml_files` depuis un cache temporaire."""
    monkeypatch.chdir(tmp_path)
    xml_dir = tmp_path / ".cache" / "syceron_an" / "17" / "xml" / "compteRendu"
    xml_dir.mkdir(parents=True)
    (xml_dir / "CRSANR5L17S2025O1N053.xml").write_bytes(FIXTURE.read_bytes())
    return tmp_path / ".cache" / "syceron_an" / "17"


@pytest.fixture(autouse=True)
def memo_process_vierge():
    """Vide le mémo des index non publiés entre deux cas.

    Il est clé par CHEMIN de cache (AGENTS.md : jamais par nom logique), donc
    deux `tmp_path` ne peuvent pas se marcher dessus ; on le vide quand même,
    pour que l'ordre des tests ne puisse jamais porter de sens.
    """
    cp._SYCERON_INDEX_NON_PUBLIE.clear()
    yield
    cp._SYCERON_INDEX_NON_PUBLIE.clear()


def test_lindex_se_remplit_sans_drapeau(cache_syceron, capsys):
    """La résolution des identifiants nus n'est plus conditionnelle (#510).

    Elle l'a été le temps d'une décision d'opérateur — un mode où l'index se
    construisait vide à partir de 380 Mo d'archive lisible. Ce mode n'existe
    plus : il ne rendait pas « moins » d'interventions, il en rendait zéro.
    """
    index = cp._build_acteur_interventions_syceron_index("17")

    assert "PA847629" in index
    assert "PA0" not in index
    assert "PA-125799" not in index
    assert all(entree["orateur_id_source"].startswith("PA") for v in index.values() for entree in v)

    # Le parcours des <point> imbriqués est corrigé depuis le 26/08/2026 :
    # PA795310 ne parle que dans le <point nivpoint="2"> de la fixture, et il est
    # désormais indexé. Le parcours d'origine ne voyait que 180 755 des 1 444 564
    # paragraphes des trois archives (12,5 %).
    assert "PA795310" in index, (
        "les <point> imbriqués doivent être parcourus (défaut nº1 de #510)"
    )

    sortie = capsys.readouterr().out
    assert "identifiant_nu_prefixe=" in sortie
    assert "orateur_collectif_anonyme=" in sortie
    assert "pseudo_acteur_hors_referentiel=" in sortie


def test_le_drapeau_dactivation_est_refuse_bruyamment(capsys):
    """`--activer-interventions-syceron` a été retiré : le refus doit NOMMER la
    décision. Un `unrecognized arguments` laisserait croire à une option inconnue
    — ou pire, à une collecte Syceron désactivée."""
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--activer-interventions-syceron", action=cp.RefusDrapeauInterventionsSyceron
    )
    with pytest.raises(SystemExit):
        parser.parse_args(["--activer-interventions-syceron"])
    assert "#510" in capsys.readouterr().err


def test_les_entrees_indexees_portent_leur_sujet(cache_syceron):
    """Second défaut de #510 : `sujet` sortait à `None` sur 100 % des entrées.

    Syceron REMPLACE la liste d'interventions dont `tags_thematiques` est dérivé
    (`normalize_profil` lit `theme_officiel`, qui vaut `sujet`) : publier un
    ordre de grandeur d'interventions sans thème, à la place de 789 qui en
    portent, serait une régression sur un champ publié.
    """
    index = cp._build_acteur_interventions_syceron_index("17")

    entrees = [e for v in index.values() for e in v]
    assert entrees
    assert any(e["sujet"] for e in entrees)
    assert {e["sujet"] for e in entrees} == {
        "Questions au Gouvernement",
        "Accès à l’enseignement supérieur",
    }


def test_lattribution_refusee_est_comptee_dans_lindex(cache_syceron, capsys):
    """Le refus de la source se compte comme les autres rejets, jamais en silence."""
    xml_dir = cache_syceron / "xml" / "compteRendu"
    for f in xml_dir.glob("*.xml"):
        f.unlink()
    xml_dir.joinpath("refusee.xml").write_bytes(FIXTURE_ATTRIBUTION_REFUSEE.read_bytes())

    index = cp._build_acteur_interventions_syceron_index("17")

    assert index == {}, "l'unique paragraphe est une attribution refusée par la source"
    sortie = capsys.readouterr().out
    assert "attribution_refusee_par_la_source=1" in sortie


def test_un_index_sans_aucun_sujet_est_annonce(cache_syceron, capsys, monkeypatch):
    """Compteur-témoin du second défaut (§2.5).

    Un `sujet` vide partout est exactement l'état que #510 avait laissé —
    invisible parce que rien ne le disait. Mesuré aujourd'hui : 88,0 % des
    1 227 415 interventions indexables des trois archives portent un sujet.

    On simule ici le déplacement du vocabulaire de la source (`code_grammaire`),
    seule cause plausible d'un retour à 100 % de vides, plutôt que de fabriquer
    un compte rendu qui n'existe pas — c'est la fixture inventée qui a produit
    ce défaut.
    """
    import parse_syceron

    monkeypatch.setattr(parse_syceron, "_CODE_GRAMMAIRE_SUJET", frozenset())

    index = cp._build_acteur_interventions_syceron_index("17")

    assert index, "les orateurs restent résolus : c'est le sujet qui manque"
    assert all(not e["sujet"] for v in index.values() for e in v)
    sortie = capsys.readouterr().out
    assert "AUCUNE" in sortie
    assert "sujet" in sortie
    assert "#510" in sortie


def test_lindex_est_publie_en_tranches_par_acteur(cache_syceron):
    """La tranche par acteur est ce qui rend la source primaire tenable (#510).

    L'index plat était relu ENTIER à chaque candidat et pour chaque législature :
    1 664,8 Mio et 12,5 s mesurés sur les trois archives, contre le budget de
    240 s de #500. Il n'est plus écrit du tout — et les deux index plats hérités
    (dont celui de 2 octets du mode d'avant) sont supprimés à la publication.
    """
    for nom in cp.SYCERON_INDEX_FILENAMES_HERITES:
        (cache_syceron / nom).write_text("{}", encoding="utf-8")

    index = cp._build_acteur_interventions_syceron_index("17")

    tranche = cache_syceron / cp.SYCERON_INDEX_PAR_ACTEUR_DIRNAME / "PA847629.json"
    assert tranche.is_file()
    assert json.loads(tranche.read_text(encoding="utf-8")) == index["PA847629"]
    for nom in cp.SYCERON_INDEX_FILENAMES_HERITES:
        assert not (cache_syceron / nom).exists(), f"{nom} hérité doit être supprimé"


def test_larchive_nest_reparcourue_quune_fois_par_legislature(cache_syceron, monkeypatch):
    """Le second candidat ne doit plus toucher un seul compte rendu.

    C'est la propriété, pas le chiffre, qui est fixée ici : « un cache disque
    évite un re-téléchargement, jamais un re-parsing » (AGENTS.md), quatrième
    occurrence du même coût au même endroit après #392, #403 et #467.
    """
    parcours: list[str] = []
    vrai_iter = cp.iter_syceron_xml_files

    def compter(legislature, **kwargs):
        parcours.append(legislature)
        return vrai_iter(legislature, **kwargs)

    monkeypatch.setattr(cp, "iter_syceron_xml_files", compter)
    monkeypatch.setattr(cp, "SYCERON_AVAILABLE_LEGISLATURES", {"17"})

    url = "https://www.assemblee-nationale.fr/dyn/deputes/PA847629"
    premier = cp.fetch_interventions_syceron(url)
    second = cp.fetch_interventions_syceron(url)

    assert premier and second == premier
    assert parcours == ["17"], "le second candidat a reparcouru l'archive"


def test_un_index_vide_sur_une_archive_lisible_nest_jamais_mis_en_cache(cache_syceron, capsys):
    """§2.5 : le trou par lequel #510 est passé.

    La garde de #505 ne couvrait que « aucun fichier lisible ». Un `{}` construit
    à partir de 601 comptes rendus lus passait, lui, pour un résultat — une
    donnée manquante figée en zéro mesuré, propagée à tous les shards de la
    semaine par la clé de cache. Le repli NosDéputés étant retiré, plus rien ne
    comble ce silence : la garde compte double.
    """
    xml_dir = cache_syceron / "xml" / "compteRendu"
    for f in xml_dir.glob("*.xml"):
        f.unlink()
    # Un compte rendu lisible dont AUCUN orateur ne résout.
    xml_dir.joinpath("vide.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<compteRendu xmlns="http://schemas.assemblee-nationale.fr/referentiel">'
        "<uid>CR</uid><contenu><point><paragraphe><orateurs><orateur>"
        "<nom>Un député du groupe RN</nom><id>0</id></orateur></orateurs>"
        "<texte>Bravo !</texte></paragraphe></point></contenu></compteRendu>",
        encoding="utf-8",
    )

    index = cp._build_acteur_interventions_syceron_index("17")

    assert index == {}
    assert not (cache_syceron / cp.SYCERON_INDEX_PAR_ACTEUR_DIRNAME).exists()
    sortie = capsys.readouterr().out
    assert "NON mis en cache" in sortie
    assert "AUCUN acteur résolu" in sortie
    assert "repli NosDéputés a été retiré" in sortie


def test_fetch_interventions_syceron_resout_le_deputes_par_son_url(cache_syceron, monkeypatch):
    """Bout en bout : l'URL de fiche AN d'un député rend ses interventions."""
    # Seule la 17e est servie depuis le cache temporaire : les autres
    # législatures de SYCERON_AVAILABLE_LEGISLATURES déclencheraient un
    # téléchargement, que `tests/conftest.py` interdit (#473).
    monkeypatch.setattr(cp, "SYCERON_AVAILABLE_LEGISLATURES", {"17"})
    interventions = cp.fetch_interventions_syceron(
        "https://www.assemblee-nationale.fr/dyn/deputes/PA847629"
    )
    assert interventions
    assert {i["orateur_id_source"] for i in interventions} == {"PA847629"}
    assert all(i["legislature"] == "17" for i in interventions)


def test_le_sujet_est_desormais_lu_la_ou_la_source_le_publie():
    """Second défaut de #510, corrigé : `sujet` sortait à `None` sur 100 % des
    entrées parce que le parseur cherchait un `<titreStruct>` sous `<contenu>`,
    qui n'y existe pas (0 occurrence sur les 162 073 points des trois archives).

    Le titre vit dans `<point><texte>`. `sujet` est désormais renseigné sur
    **88,0 %** des 1 227 415 interventions indexables des trois archives — et le
    reste à `None` là où la source ne publie qu'un intitulé de procédure, ce qui
    est un résultat et non un défaut (§2 règles 5 et 8).
    """
    parsed = parse_syceron_xml(FIXTURE.read_bytes())
    assert any(i["sujet"] for i in parsed["interventions"])
    assert {i["type_detail"] for i in parsed["interventions"]} == {"question_gouvernement"}


def test_les_fixtures_inventees_restent_retirees():
    """Garde-fou de contexte : ne pas réintroduire le schéma inventé.

    `syceron_minimal.xml` et `syceron_missing_fields.xml` portaient des
    `<id>PA…</id>` et des `<titreStruct>` sous `<point>` : ni l'un ni l'autre
    n'existe dans l'archive. Le parseur a donc été validé contre sa propre
    hypothèse, et c'est la cause commune de #510 et de ses deux défauts de
    parseur. Elles sont retirées — les réintroduire, c'est réarmer la cause.
    """
    for nom in ("syceron_minimal.xml", "syceron_missing_fields.xml"):
        assert not (FIXTURE.parent / nom).exists(), (
            f"{nom} décrit un schéma inventé ; relire #510 avant de la réintroduire"
        )
