"""Tests du contrôle d'intégrité référentielle de `pivot_data/` (#485).

#432 a normalisé les votes et #431 les amendements : le détail a quitté les
profils pour un index partagé, et les profils n'en gardent qu'une **clé**. La
donnée est passée d'un état auto-suffisant à un état **référentiel**, et rien ne
vérifiait qu'une clé publiée résolve.

Ce n'était pas un défaut constaté : mesuré sur `01ffa7f`, 1 347 451 références
résolvent toutes, dans les deux sens. Ces tests verrouillent la propriété avant
qu'elle ne casse, et le contrôle qui la mesure.

**Pourquoi ce contrôle ne pouvait pas rejoindre `audit_diff_profils`** :
celui-ci compare un **avant** et un **après**. Il verrait une chute du nombre
d'entrées d'un index, mais pas une rupture de correspondance entre deux couches
du **même** état — deux couches régénérées de façon cohérente-mais-fausse lui
paraîtraient irréprochables. C'est une invariance dans un état donné, pas une
variation dans le temps, et
`test_le_controle_de_perte_ne_voit_pas_ce_que_celui_ci_voit` en fait la
démonstration plutôt que de l'affirmer.

Les fixtures sont **figées** (`tests/fixtures/integrite_referentielle/`,
provenance dans `meta.fixture` / `meta_fixture`, sur le modèle de
`tests/fixtures/audit_diff_pertes_reelles/`) : aucun test ne lit le corpus
vivant, absent du disque en CI (#473). Les clés y sont réelles, extraites du
corpus — une clé inventée ne prouverait rien d'une convention de clé.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from audit_integrite_referentielle import (  # noqa: E402
    INDEX_AMENDEMENTS,
    INDEX_SCRUTINS,
    MOTIFS_BLOQUANTS,
    RENVOIS,
    Index,
    auditer,
    charger_index_amendements,
    charger_index_scrutins,
    generate_markdown_report,
    main,
    verifier_document,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "integrite_referentielle"


def corpus(tmp_path: Path, *variantes: str) -> Path:
    """Assemble un `pivot_data/` : le corpus sain, puis les variantes superposées.

    Les variantes ne portent QUE le fichier qui diffère. Dupliquer l'index dans
    chacune ferait diverger sept copies au premier changement de schéma, et une
    fixture qu'on ne peut plus relire est une donnée inventée.
    """
    racine = tmp_path / "pivot_data"
    shutil.copytree(FIXTURES / "sain", racine)
    for variante in variantes:
        source = FIXTURES / variante
        assert source.is_dir(), f"variante inconnue : {variante}"
        shutil.copytree(source, racine, dirs_exist_ok=True)
    return racine


def motifs(rapport: dict) -> dict:
    return rapport["constats_par_motif"]


# ---------------------------------------------------------------------------
# Les fixtures elles-mêmes
# ---------------------------------------------------------------------------

def test_les_fixtures_declarent_leur_provenance():
    """Une fixture sans provenance est une donnée inventée dans six mois."""
    fichiers = sorted(FIXTURES.rglob("*.json"))
    assert len(fichiers) == 13
    ref_du_depot = None
    for chemin in fichiers:
        doc = json.loads(chemin.read_text(encoding="utf-8"))
        fixture = doc.get("meta_fixture") or doc["meta"]["fixture"]
        assert fixture["source"].startswith("pivot_data/"), chemin
        assert len(fixture["ref"]) == 40, chemin
        assert fixture["reduction"], chemin
        ref_du_depot = ref_du_depot or fixture["ref"]
        assert fixture["ref"] == ref_du_depot, (
            f"{chemin} vient d'une autre ref : les variantes ne seraient plus "
            "comparables au corpus sain.")


def test_les_cles_des_fixtures_sont_reelles():
    """Une clé inventée ne prouverait rien d'une convention de clé.

    Les identifiants viennent du corpus ; seules les clés **cassées** des
    variantes sont fabriquées, et elles le sont pour être introuvables.
    """
    profil = json.loads(
        (FIXTURES / "sain" / "profiles" / "jean-luc-melenchon.pivot.json").read_bytes())
    assert profil["votes"][0]["scrutin_id"].startswith("an:")
    assert profil["amendements"][0]["amendement_id"].startswith("an:AMANR5L")


# ---------------------------------------------------------------------------
# Le corpus sain — l'état mesuré le 20/08/2026
# ---------------------------------------------------------------------------

def test_un_corpus_sain_ne_bloque_pas(tmp_path):
    rapport = auditer(corpus(tmp_path))
    assert rapport["bloquant"] is False
    assert rapport["nb_bloquants"] == 0
    assert motifs(rapport) == {}


def test_les_trois_renvois_sont_comptes(tmp_path):
    """Les trois seuls champs de `pivot_data/` qui portent une clé d'index.

    `partis/` et `gouvernements/` n'en portent aucun — mesuré sur le corpus, ce
    sont des compteurs, pas des références.
    """
    rapport = auditer(corpus(tmp_path))
    assert set(rapport["references"]) == {
        "votes[].scrutin_id",
        "amendements[].amendement_id",
        "cohesion_votes[].scrutin_id",
    }
    assert all(n > 0 for n in rapport["references"].values())
    assert rapport["total_references"] == sum(rapport["references"].values())


def test_toutes_les_entrees_d_index_sont_referencees(tmp_path):
    """0 entrée orpheline dans le sens inverse, comme sur le corpus réel.

    Ce n'est pas une coïncidence : les deux index sont **construits depuis** les
    profils bruts, donc toute entrée vient d'un profil.
    """
    rapport = auditer(corpus(tmp_path))
    for nom in (INDEX_SCRUTINS, INDEX_AMENDEMENTS):
        assert rapport["index"][nom]["jamais_referencees"] == 0, nom
        assert rapport["index"][nom]["present"] is True


# ---------------------------------------------------------------------------
# Une clé orpheline côté profil, une côté groupe
# ---------------------------------------------------------------------------

def test_une_cle_orpheline_dans_un_profil_bloque(tmp_path):
    """Un vote publié sans objet : la clé est là, le scrutin n'existe pas."""
    rapport = auditer(corpus(tmp_path, "orpheline_profil"))
    assert rapport["bloquant"] is True
    assert motifs(rapport) == {"orpheline": 1}
    assert rapport["constats_par_champ"]["votes[].scrutin_id"] == 1


def test_le_profil_et_la_cle_sont_nommes(tmp_path):
    """Sans les deux, le constat n'est pas actionnable — critère de #485."""
    rapport = auditer(corpus(tmp_path, "orpheline_profil"))
    (exemple,) = rapport["exemples"]
    assert exemple["fichier"] == "jean-luc-melenchon.pivot.json"
    assert exemple["cle"] == "an:16:99999"
    assert exemple["couche"] == "profiles"
    assert exemple["champ"] == "votes[].scrutin_id"


def test_une_cle_orpheline_dans_un_groupe_bloque(tmp_path):
    """La couche où une rupture produit un DÉNOMINATEUR FAUX (AGENTS.md §2.7).

    C'est le mécanisme de la perte SOC-16 : le ratio garde son dénominateur et
    compte un scrutin dont plus personne ne peut dire lequel c'est. Une fiche
    incomplète se voit ; un ratio faux se publie.
    """
    rapport = auditer(corpus(tmp_path, "orpheline_groupe"))
    assert rapport["bloquant"] is True
    assert motifs(rapport) == {"orpheline": 1}
    (exemple,) = rapport["exemples"]
    assert exemple["couche"] == "groupes"
    assert exemple["fichier"] == "groupe-AN-SOC-16.json"
    assert exemple["cle"] == "an:16:99998"
    assert exemple["champ"] == "cohesion_votes[].scrutin_id"


def test_les_deux_couches_bloquent_ensemble(tmp_path):
    rapport = auditer(corpus(tmp_path, "orpheline_profil", "orpheline_groupe"))
    assert rapport["nb_bloquants"] == 2
    assert {e["couche"] for e in rapport["exemples"]} == {"profiles", "groupes"}


# ---------------------------------------------------------------------------
# Les amendements — l'index shardé, plus exposé à une publication partielle
# ---------------------------------------------------------------------------

def test_un_amendement_orphelin_bloque(tmp_path):
    """Le shard existe, la clé n'y est pas : une orpheline vraie."""
    rapport = auditer(corpus(tmp_path, "amendement_orphelin"))
    assert motifs(rapport) == {"orpheline": 1}
    (exemple,) = rapport["exemples"]
    assert exemple["champ"] == "amendements[].amendement_id"
    assert exemple["detail"] is None


def test_un_shard_absent_est_nomme_a_part(tmp_path):
    """Le remède n'est pas le même : publier un fichier, pas corriger des clés.

    C'est le scénario de publication partielle que #431 rend possible en
    shardant : un shard qui échoue rend orphelines toutes les références d'une
    législature d'un coup. Les rapporter une à une noierait la cause.
    """
    rapport = auditer(corpus(tmp_path, "shard_absent"))
    assert motifs(rapport) == {"shard_absent": 1}
    (exemple,) = rapport["exemples"]
    assert exemple["detail"] == "amendements/17.json"
    assert exemple["motif"] in MOTIFS_BLOQUANTS


def test_sans_amendements_ne_declare_pas_sain_ce_qu_il_n_a_pas_regarde(tmp_path):
    """`--sans-amendements` retire le renvoi du périmètre, il ne le blanchit pas.

    Le piège serait de filtrer les constats après coup : le rapport dirait alors
    « intégrité intacte » sur une couche non lue.
    """
    racine = corpus(tmp_path, "amendement_orphelin")
    complet = auditer(racine)
    partiel = auditer(racine, avec_amendements=False)
    assert complet["bloquant"] is True
    assert partiel["bloquant"] is False
    assert "amendements[].amendement_id" not in partiel["references"]
    assert partiel["avec_amendements"] is False
    assert "n'a pas été lu" in generate_markdown_report(partiel)


def test_les_cosignatures_ne_sont_jamais_ouvertes(tmp_path):
    """222 Mio de RSS pour le seul `15.cosignatures.json`, et aucun référent.

    Motif d'exclusion **négatif** : `*` traverse le point, donc un motif positif
    `[0-9]*.json` les attraperait et l'économie serait silencieusement annulée.
    """
    racine = corpus(tmp_path)
    piege = racine / "amendements" / "15.cosignatures.json"
    piege.write_text("{ ceci n'est pas du JSON", encoding="utf-8")
    index = charger_index_amendements(racine / "amendements")
    assert "15.cosignatures.json" not in index.entrees_par_fichier
    assert auditer(racine)["bloquant"] is False


# ---------------------------------------------------------------------------
# Clé absente : déclarée ou non, ce n'est pas le même fait
# ---------------------------------------------------------------------------

def test_une_cle_absente_avec_son_enregistrement_ne_bloque_pas(tmp_path):
    """Forme normale d'un amendement du PE, que ParlTrack livre sans uid AN.

    La donnée est conservée, rien n'est perdu ni inventé : c'est exactement le
    repli que §2.5 prescrit, pas une violation.
    """
    rapport = auditer(corpus(tmp_path, "non_resolue_declaree"))
    assert rapport["bloquant"] is False
    assert motifs(rapport) == {"non_resolue_declaree": 1}
    assert rapport["exemples"] == []


def test_une_cle_absente_sans_enregistrement_bloque(tmp_path):
    """`validate_profil()` l'interdit déjà : ni supprimé, ni doté d'une clé inventée."""
    rapport = auditer(corpus(tmp_path, "cle_absente_sans_declaration"))
    assert rapport["bloquant"] is True
    assert motifs(rapport) == {"cle_absente_sans_declaration": 1}


def test_un_groupe_ne_prevoit_aucune_absence_de_cle(tmp_path):
    """`cohesion_votes` est construit DEPUIS des scrutins résolus.

    Une entrée sans clé y serait un dénominateur publié sur un objet inconnu :
    aucun `declaration` n'est donc prévu, et un `null` bloque.
    """
    (renvoi,) = [r for r in RENVOIS if r.couche == "groupes"]
    assert renvoi.declaration is None
    racine = corpus(tmp_path)
    chemin = racine / "groupes" / "groupe-AN-SOC-16.json"
    doc = json.loads(chemin.read_bytes())
    doc["cohesion_votes"][0]["scrutin_id"] = None
    chemin.write_text(json.dumps(doc), encoding="utf-8")
    assert motifs(auditer(racine)) == {"cle_absente_sans_declaration": 1}


# ---------------------------------------------------------------------------
# Le sens inverse — instruit, et non bloquant
# ---------------------------------------------------------------------------

def test_une_entree_d_index_jamais_referencee_est_rapportee_sans_bloquer(tmp_path):
    """État LÉGITIME, pas une anomalie.

    La fusion des index est additive **par contrat** (AGENTS.md §3 : « a partial
    run must never drop ballots that other profiles' mappings still point at »).
    Cette additivité implique qu'une entrée survive à son référent — profil
    corrigé, membre sorti du corpus, tranche non retraitée. Bloquer dessus
    reviendrait à interdire la propriété de sûreté principale du pipeline.
    """
    rapport = auditer(corpus(tmp_path, "index_derive"))
    assert rapport["bloquant"] is False
    assert rapport["index"][INDEX_SCRUTINS]["jamais_referencees"] == 1
    assert "Compteur de dérive" in generate_markdown_report(rapport)


def test_une_cle_referencee_deux_fois_reste_resoluble():
    """Le relevé du sens inverse ne consomme pas les clés.

    Une suppression destructive dans `cles` aurait économisé un `set`, et rendu
    orpheline toute seconde référence à un même scrutin — ce qui est le cas
    normal : un scrutin est voté par des dizaines de membres.
    """
    index = Index(nom=INDEX_SCRUTINS, cles={"an:16:1"}, present=True)
    doc = {"votes": [{"scrutin_id": "an:16:1"}, {"scrutin_id": "an:16:1"}]}
    constats = verifier_document(doc, "x.json", "profiles",
                                 {INDEX_SCRUTINS: index,
                                  INDEX_AMENDEMENTS: Index(nom=INDEX_AMENDEMENTS)})
    assert constats == []
    assert index.jamais_referencees == 0


# ---------------------------------------------------------------------------
# Index entier absent — un seul diagnostic, pas 524 353
# ---------------------------------------------------------------------------

def test_un_index_absent_est_nomme_comme_tel(tmp_path):
    """« an uncommitted index leaves every mapping pointing at nothing, silently ».

    Le remède est de publier le fichier, pas de corriger des clés une à une :
    le motif est donc distinct de l'orpheline.
    """
    racine = corpus(tmp_path)
    (racine / "scrutins.json").unlink()
    rapport = auditer(racine)
    assert rapport["bloquant"] is True
    assert set(motifs(rapport)) == {"index_absent"}
    assert rapport["index"][INDEX_SCRUTINS]["present"] is False


def test_les_exemples_sont_plafonnes_mais_le_total_ne_l_est_pas(tmp_path):
    """Un index absent produirait des milliers de lignes identiques.

    Le total reste juste ; seuls les exemples nommés sont bornés.
    """
    racine = corpus(tmp_path)
    (racine / "scrutins.json").unlink()
    rapport = auditer(racine, plafond_exemples=2)
    assert len(rapport["exemples"]) == 2
    assert rapport["nb_bloquants"] > 2
    assert f"{rapport['nb_bloquants'] - 2} de plus" in generate_markdown_report(rapport)


def test_les_exemples_bloquants_ne_sont_pas_evinces_par_les_autres(tmp_path):
    """Un plafond partagé laisserait des clés légitimes chasser la seule fautive."""
    rapport = auditer(corpus(tmp_path, "non_resolue_declaree", "orpheline_profil"),
                      plafond_exemples=1)
    (exemple,) = rapport["exemples"]
    assert exemple["motif"] == "orpheline"


# ---------------------------------------------------------------------------
# Le cas que le contrôle de perte ne peut pas voir
# ---------------------------------------------------------------------------

def test_le_controle_de_perte_ne_voit_pas_ce_que_celui_ci_voit(tmp_path):
    """La démonstration, pas l'affirmation.

    On construit un « après » où profils et index sont régénérés de façon
    cohérente-mais-fausse : la convention de clé change des deux côtés, aucun
    compteur ne bouge, mais les profils, eux, gardent l'ancienne. Pour
    `audit_diff_profils`, les cardinalités sont identiques — il ne relève rien.
    Ce contrôle-ci relève chaque référence.
    """
    from audit_diff_profils import (COLLECTION_INDEX_SCRUTINS, COLLECTION_PROFILS,
                                    comparer, lire_collection_disque)

    avant = corpus(tmp_path / "avant")
    apres = corpus(tmp_path / "apres")
    chemin = apres / "scrutins.json"
    doc = json.loads(chemin.read_bytes())
    for scrutin in doc["scrutins"]:
        scrutin["id"] = scrutin["id"].replace("an:", "an-v2:")
    chemin.write_text(json.dumps(doc), encoding="utf-8")

    # Le contrôle de perte : mêmes cardinalités des deux côtés, rien à signaler.
    for collection, sous in ((COLLECTION_PROFILS, "profiles"),
                             (COLLECTION_INDEX_SCRUTINS, "")):
        rapport_perte = comparer(
            lire_collection_disque(avant / sous if sous else avant, collection),
            lire_collection_disque(apres / sous if sous else apres, collection),
            collection)
        assert rapport_perte["bloquant"] is False, collection.nom
        assert rapport_perte["pertes"] == [], collection.nom

    # Celui-ci : chaque référence de scrutin est devenue orpheline.
    rapport = auditer(apres)
    assert rapport["bloquant"] is True
    assert rapport["constats_par_champ"]["votes[].scrutin_id"] > 0
    assert rapport["constats_par_champ"]["cohesion_votes[].scrutin_id"] > 0
    assert rapport["constats_par_champ"]["amendements[].amendement_id"] == 0


# ---------------------------------------------------------------------------
# Robustesse de lecture
# ---------------------------------------------------------------------------

def test_un_index_illisible_ne_leve_pas(tmp_path):
    racine = corpus(tmp_path)
    (racine / "scrutins.json").write_text("{ pas du JSON", encoding="utf-8")
    assert auditer(racine)["index"][INDEX_SCRUTINS]["present"] is False


def test_un_document_illisible_bloque(tmp_path):
    """Un profil qu'on ne peut pas lire n'est pas un profil sans référence."""
    racine = corpus(tmp_path)
    (racine / "profiles" / "casse.pivot.json").write_text("{ nope", encoding="utf-8")
    rapport = auditer(racine)
    assert motifs(rapport) == {"document_illisible": 1}
    assert rapport["bloquant"] is True


def test_un_repertoire_absent_ne_leve_pas(tmp_path):
    racine = corpus(tmp_path)
    shutil.rmtree(racine / "groupes")
    rapport = auditer(racine)
    assert rapport["bloquant"] is False
    assert rapport["fichiers_lus"]["groupes"] == 0


def test_index_amendements_absent_en_entier(tmp_path):
    racine = corpus(tmp_path)
    shutil.rmtree(racine / "amendements")
    rapport = auditer(racine)
    assert rapport["index"][INDEX_AMENDEMENTS]["present"] is False
    assert set(motifs(rapport)) == {"index_absent"}


def test_charger_index_scrutins_sur_fichier_absent(tmp_path):
    index = charger_index_scrutins(tmp_path / "rien.json")
    assert index.present is False and index.cles == set()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_cli_sort_en_erreur_sur_une_orpheline(tmp_path, capsys):
    racine = corpus(tmp_path, "orpheline_profil")
    code = main(["--pivot-dir", str(racine), "--out", str(tmp_path / "r.md"),
                 "--out-json", str(tmp_path / "r.json")])
    assert code == 1
    erreurs = capsys.readouterr().err
    assert "jean-luc-melenchon.pivot.json" in erreurs
    assert "an:16:99999" in erreurs
    assert json.loads((tmp_path / "r.json").read_text())["bloquant"] is True


def test_cli_tolere_les_orphelins_sur_demande(tmp_path):
    racine = corpus(tmp_path, "orpheline_profil")
    assert main(["--pivot-dir", str(racine), "--tolerer-orphelins",
                 "--out", str(tmp_path / "r.md")]) == 0


def test_cli_sort_a_zero_sur_un_corpus_sain(tmp_path):
    assert main(["--pivot-dir", str(corpus(tmp_path)),
                 "--out", str(tmp_path / "r.md")]) == 0


def test_le_rapport_enonce_son_hors_perimetre(tmp_path):
    """Un périmètre qu'on ne dit pas se croit complet."""
    markdown = generate_markdown_report(auditer(corpus(tmp_path)))
    assert "Hors périmètre de ce contrôle" in markdown
    assert "cosignatures" in markdown
    assert "audit_diff_profils" in markdown


@pytest.mark.parametrize("argv", [[], ["--sans-amendements"]])
def test_le_script_s_execute_en_sous_processus(tmp_path, argv):
    """Il tourne en CI comme un script, pas comme un module importé."""
    racine = corpus(tmp_path, *(["orpheline_profil"] if not argv else []))
    proc = subprocess.run(
        [sys.executable, str(RACINE / "src" / "audit_integrite_referentielle.py"),
         "--pivot-dir", str(racine), *argv],
        capture_output=True, text=True)
    assert proc.returncode == (1 if not argv else 0), proc.stderr
