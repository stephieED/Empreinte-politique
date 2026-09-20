"""#555 — la clé hebdomadaire du cache AN ne périme rien, et doit le faire.

Pourquoi ce fichier existe. Quatrième reprise de la même famille : une clé de
cache qui ne décrit pas ce qu'elle protège.

| Forme | Issue | Ce que la clé ignorait |
| --- | --- | --- |
| 1re | #424 | les répertoires réellement couverts |
| 2e | #505 | le mode d'extraction (`-interv`) |
| 3e | #550 | la complétude du contenu indexé |
| 4e | #555 | **l'ÂGE du contenu restauré** |

Les trois premières mettaient la dimension manquante DANS la clé. Celle-ci ne
le peut pas : la semaine y est déjà, et c'est la *restauration* qui la
contourne. La dernière ligne des `restore-keys` est un préfixe nu,
`public-data-cache-an-`, sans borne de semaine.

MESURÉ, run `32738726729` du 24/08/2026 (lundi, première exécution de W35),
shard `jean-luc-melenchon`, job `97468417763` :

    14:28:54  Cache restored from key: public-data-cache-an-2026-W34
    14:28:58  Extraction AN — début
    14:29:09  Elapsed (wall clock) time: 0:10.12   ← aucune archive rouverte
    14:29:12  Cache saved with key: public-data-cache-an-2026-W35

Dix-huit secondes pour blanchir le contenu du 20/08 sous la clé du 24/08. Aucun
constructeur d'index ne regarde l'âge de ce qu'il trouve — vérifié ici même par
`test_aucun_constructeur_d_index_an_ne_regarde_l_age_du_cache`, sur le VRAI
code : c'est cette absence qui fait de la clé hebdomadaire le seul mécanisme de
fraîcheur, et donc du préfixe nu un contournement total.

Ce que ce fichier impose n'est pas la correction mais **sa règle** : le contenu
qui vieillit périme, celui qui ne vieillit pas reste. La frontière est la
clôture de la législature, dérivée des constantes du code — jamais recopiée.

Aucun réseau, aucun corpus : les caches sont fabriqués dans `tmp_path`.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

import cache_an_fraicheur as fr
import candidate_profile as cp

SEMAINE = "2026-W35"
SEMAINE_PRECEDENTE = "2026-W34"


# ---------------------------------------------------------------------------
# La semaine se lit dans la clé restaurée — le marqueur de fraîcheur existe déjà
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "cle, attendue",
    [
        # Les quatre formes réellement observées dans les caches du dépôt le
        # 28/08/2026 (`gh cache list`).
        ("public-data-cache-an-2026-W35", "2026-W35"),
        ("public-data-cache-an-2026-W35-interv", "2026-W35"),
        ("public-data-cache-an-2026-W35-interv-syc17-q16.17", "2026-W35"),
        ("public-data-cache-an-2026-W35-interv-syc15.16.17-q14.15.16.17", "2026-W35"),
        ("public-data-cache-an-2026-W34", "2026-W34"),
    ],
)
def test_la_semaine_se_lit_sur_toutes_les_formes_de_cle(cle, attendue):
    """La clé porte déjà sa semaine : c'est le marqueur de fraîcheur, et il n'a
    rien coûté au `path:` du step de cache — qu'un fichier sentinelle aurait
    modifié, changeant la *version* de l'entrée et faisant perdre une semaine
    de cache rien qu'à déployer la correction."""
    assert fr.semaine_de_la_cle(cle) == attendue


@pytest.mark.parametrize(
    "cle",
    ["", None, "   ", "public-data-cache-dossiers-2026-W34", "public-data-cache-an-", "n'importe"],
)
def test_une_cle_illisible_ne_rend_aucune_semaine(cle):
    assert fr.semaine_de_la_cle(cle) is None


def test_le_prefixe_du_module_est_celui_des_cles_du_depot():
    """Garde-fou du garde-fou : si le préfixe changeait ici seul, toute clé
    deviendrait illisible, donc toute semaine suspecte, donc une péremption
    hebdomadaire — coûteuse et silencieuse."""
    assert fr.PREFIXE_CLE_AN == "public-data-cache-an-"


# ---------------------------------------------------------------------------
# Le verdict
# ---------------------------------------------------------------------------


def test_une_entree_de_la_semaine_precedente_est_perimee():
    """LE cas du 24/08, reconstruit à l'identique."""
    verdict = fr.evaluer(SEMAINE, f"public-data-cache-an-{SEMAINE_PRECEDENTE}")
    assert verdict.etat == fr.PERIME
    assert verdict.perimee
    assert verdict.semaine_restauree == SEMAINE_PRECEDENTE
    assert verdict.niveau() == "warning"
    assert SEMAINE_PRECEDENTE in verdict.message()


def test_une_entree_de_la_semaine_courante_est_fraiche():
    """Le témoin. Sans lui, tout serait déclaré périmé et la correction
    coûterait une réindexation à CHAQUE run au lieu d'une par semaine."""
    verdict = fr.evaluer(SEMAINE, f"public-data-cache-an-{SEMAINE}-interv-syc15.16.17-q14.15.16.17")
    assert verdict.etat == fr.FRAIS
    assert not verdict.perimee
    assert verdict.niveau() == "notice"


def test_un_cache_froid_ne_perime_rien():
    """Aucune entrée restaurée : il n'y a rien à supprimer, et déclarer un
    avertissement ici noierait le seul cas qui en mérite un."""
    verdict = fr.evaluer(SEMAINE, "")
    assert verdict.etat == fr.CACHE_FROID
    assert not verdict.perimee
    assert verdict.niveau() == "notice"


def test_une_cle_illisible_perime_par_precaution():
    """Le sens de l'erreur est CHOISI : une clé dont la semaine ne se lit pas
    ne peut pas être déclarée fraîche. Le coût est une réindexation de la
    législature en cours ; le silence coûterait la fraîcheur de toutes les
    suivantes."""
    verdict = fr.evaluer(SEMAINE, "public-data-cache-an-nouvelle-forme")
    assert verdict.etat == fr.INDECIDABLE
    assert verdict.perimee
    assert verdict.niveau() == "warning"


# ---------------------------------------------------------------------------
# Ce qui périme, et ce qui reste
# ---------------------------------------------------------------------------


def _poser_cache(racine: Path) -> None:
    """Un cache AN complet, dans la forme exacte que le `path:` du step de
    cache capture."""
    (racine / "acteurs_historique_an").mkdir(parents=True)
    (racine / "acteurs_historique_an" / "acteurs_historique.zip").write_bytes(b"PK")
    (racine / "acteurs_historique_an" / cp.NOM_INDEX_IDENTITE).write_text("{}", encoding="utf-8")
    for legislature in ("14", "15", "16", "17"):
        (racine / "scrutins_an" / legislature / "index_par_acteur").mkdir(parents=True)
        (racine / "questions_an" / legislature).mkdir(parents=True)
        (racine / "questions_an" / legislature / "index_par_acteur.json").write_text(
            "{}", encoding="utf-8"
        )
    for legislature in ("15", "16", "17"):
        (racine / "syceron_an" / legislature / "index_par_acteur").mkdir(parents=True)


def _chemins(racine: Path) -> list[str]:
    return [
        str(chemin.relative_to(racine))
        for chemin in fr.chemins_perissables(
            cache_acteurs=racine / "acteurs_historique_an",
            cache_scrutins=racine / "scrutins_an",
            cache_questions=racine / "questions_an",
            cache_syceron=racine / "syceron_an",
        )
    ]


def test_seules_les_legislatures_non_figees_perissent(tmp_path):
    """LE cœur de #555, et ce qui le distingue du retrait du préfixe nu : les
    15e et 16e législatures coûtent 147 s et 55 s à réindexer, la 17e 42 s
    (mesures #550). Périmer l'entrée en bloc chaque semaine paierait 244 s là
    où 42 s suffisent — et rouvrirait #424 par-dessus."""
    _poser_cache(tmp_path)
    assert _chemins(tmp_path) == [
        "acteurs_historique_an",
        "questions_an/17",
        "scrutins_an/17",
        "syceron_an/17",
    ]


def test_les_legislatures_figees_survivent_a_la_peremption(tmp_path):
    _poser_cache(tmp_path)
    fr.perimer(
        fr.chemins_perissables(
            cache_acteurs=tmp_path / "acteurs_historique_an",
            cache_scrutins=tmp_path / "scrutins_an",
            cache_questions=tmp_path / "questions_an",
            cache_syceron=tmp_path / "syceron_an",
        )
    )
    for legislature in ("15", "16"):
        assert (tmp_path / "syceron_an" / legislature / "index_par_acteur").is_dir()
        assert (tmp_path / "questions_an" / legislature / "index_par_acteur.json").is_file()
    assert not (tmp_path / "syceron_an" / "17").exists()
    assert not (tmp_path / "questions_an" / "17").exists()
    assert not (tmp_path / "acteurs_historique_an").exists()


def test_la_frontiere_est_derivee_des_constantes_du_code():
    """Recopiée, la liste deviendrait fausse à la clôture de la 17e ou à
    l'ouverture de la 18e : le cache se remettrait à périmer (ou à ne plus
    périmer) au mauvais endroit, sans que rien ne le dise. Même règle que
    l'empreinte de #550."""
    assert fr.legislatures_figees() == (
        frozenset(cp.AN_SCRUTINS_LEGISLATURES_FIGEES)
        & frozenset(cp.AN_AMENDEMENTS_LEGISLATURES_FIGEES)
    )


def test_une_legislature_qui_se_clot_cesse_de_perir(tmp_path):
    """Le jour où la 17e est déclarée close des deux côtés, son index doit
    cesser d'être rebâti chaque semaine — sans qu'on touche à ce module."""
    _poser_cache(tmp_path)
    figees = frozenset({"14", "15", "16", "17"})
    with patch.object(cp, "AN_SCRUTINS_LEGISLATURES_FIGEES", figees), patch.object(
        cp, "AN_AMENDEMENTS_LEGISLATURES_FIGEES", figees
    ):
        assert _chemins(tmp_path) == ["acteurs_historique_an"]


def test_une_legislature_neuve_perit_sans_intervention(tmp_path):
    """Et le jour où la 18e s'ouvre, elle périme d'office : figée par défaut,
    elle vieillirait indéfiniment sous le préfixe nu."""
    _poser_cache(tmp_path)
    (tmp_path / "syceron_an" / "18" / "index_par_acteur").mkdir(parents=True)
    assert "syceron_an/18" in _chemins(tmp_path)


def test_les_repertoires_hors_forme_ne_sont_jamais_supprimes(tmp_path):
    """`.cache/syceron_an/<législature>` ne contient que des numéros. Un
    répertoire de travail qui s'y glisserait ne doit pas être emporté par une
    péremption — même règle que `_syceron_shard_path_acteur`, qui refuse ce
    qui est hors forme plutôt que de l'assainir approximativement."""
    _poser_cache(tmp_path)
    (tmp_path / "syceron_an" / "index_par_acteur.partiel").mkdir(parents=True)
    assert "syceron_an/index_par_acteur.partiel" not in _chemins(tmp_path)


def test_un_cache_absent_ne_fait_rien_echouer(tmp_path):
    """Le runner neuf : rien sur le disque, aucune erreur, une liste vide."""
    assert _chemins(tmp_path) == []
    assert fr.perimer([tmp_path / "absent"]) == []


# ---------------------------------------------------------------------------
# La jonction avec le VRAI code : pourquoi la semaine est le seul recours
# ---------------------------------------------------------------------------


def test_aucun_constructeur_d_index_an_ne_regarde_l_age_du_cache():
    """La prémisse de #555, éprouvée sur le code et non sur un commentaire.

    Les trois portes d'entrée du cache AN rendent leur contenu sur la seule
    EXISTENCE du fichier — `zip_path.is_file()`, `index_path.is_file()`,
    `index_dir.is_dir()`. Aucun `mtime`, aucun TTL, aucune date. C'est ce qui
    fait de la clé hebdomadaire le seul mécanisme de fraîcheur, donc du préfixe
    nu un contournement total.

    Le jour où l'un d'eux acquiert sa propre péremption, ce test tombe et la
    correction de #555 doit être relue : elle ferait double emploi.
    """
    import inspect

    sources = {
        nom: inspect.getsource(getattr(cp, nom))
        for nom in (
            "_ensure_acteurs_historique_zip_downloaded",
            "_build_acteur_questions_index",
            "_read_cached_interventions_syceron_acteur",
        )
    }
    for nom, source in sources.items():
        corps = source.split('"""')[-1]
        assert "mtime" not in corps and "time.time" not in corps, (
            f"{nom} regarde désormais l'âge de son cache : la clé hebdomadaire "
            "n'est plus le seul mécanisme de fraîcheur, et #555 est à relire."
        )


def test_la_peremption_laisse_le_disque_dans_un_etat_que_l_empreinte_550_sait_decrire(tmp_path):
    """#555 et #550 doivent rester solidaires : après une péremption, ce qui
    reste sur le disque est un cache PARTIEL, et l'empreinte de #550 doit le
    dire — sans quoi le job réécrirait une clé annonçant une complétude qu'il
    n'a pas."""
    import cache_an_empreinte as emp

    _poser_cache(tmp_path)
    for legislature in ("15", "16", "17"):
        (tmp_path / "syceron_an" / legislature / "index_par_acteur" / "PA1.json").write_text(
            "[]", encoding="utf-8"
        )

    avant = emp.empreinte(
        emp.legislatures_syceron_indexees(tmp_path / "syceron_an"),
        emp.legislatures_questions_indexees(tmp_path / "questions_an"),
    )
    assert avant == emp.empreinte_attendue()

    fr.perimer(
        fr.chemins_perissables(
            cache_acteurs=tmp_path / "acteurs_historique_an",
            cache_scrutins=tmp_path / "scrutins_an",
            cache_questions=tmp_path / "questions_an",
            cache_syceron=tmp_path / "syceron_an",
        )
    )
    apres = emp.empreinte(
        emp.legislatures_syceron_indexees(tmp_path / "syceron_an"),
        emp.legislatures_questions_indexees(tmp_path / "questions_an"),
    )
    assert apres == "syc15.16-q14.15.16"
    assert apres != emp.empreinte_attendue(), (
        "Après péremption, le disque ne porte plus la 17e législature : "
        "l'empreinte de #550 doit le dire, sinon la sauvegarde annoncerait une "
        "complétude qu'elle n'a pas."
    )


# ---------------------------------------------------------------------------
# La ligne de commande, telle que le workflow l'appelle
# ---------------------------------------------------------------------------


def test_la_cli_ne_perime_rien_sans_le_drapeau(tmp_path, monkeypatch, capsys):
    """L'asymétrie producteur/consommateur : le job roster restaure la même clé
    mais ne sauvegarde rien (#505). Y périmer ferait retélécharger ~40 Mo par
    chacun de ses 8 shards sans rien persister en retour — #424 recréé."""
    _poser_cache(tmp_path)
    monkeypatch.setattr(cp, "ACTEURS_HISTORIQUE_CACHE_DIR", tmp_path / "acteurs_historique_an")
    monkeypatch.setattr(cp, "SCRUTINS_CACHE_DIR", tmp_path / "scrutins_an")
    monkeypatch.setattr(cp, "QUESTIONS_CACHE_DIR", tmp_path / "questions_an")
    monkeypatch.setattr(cp, "SYCERON_CACHE_DIR", tmp_path / "syceron_an")

    code = fr.main(
        ["--semaine", SEMAINE, "--cle-restauree", f"public-data-cache-an-{SEMAINE_PRECEDENTE}"]
    )
    assert code == 0
    assert (tmp_path / "syceron_an" / "17" / "index_par_acteur").is_dir()
    assert SEMAINE_PRECEDENTE in capsys.readouterr().out


def test_la_cli_perime_avec_le_drapeau(tmp_path, monkeypatch, capsys):
    _poser_cache(tmp_path)
    monkeypatch.setattr(cp, "ACTEURS_HISTORIQUE_CACHE_DIR", tmp_path / "acteurs_historique_an")
    monkeypatch.setattr(cp, "SCRUTINS_CACHE_DIR", tmp_path / "scrutins_an")
    monkeypatch.setattr(cp, "QUESTIONS_CACHE_DIR", tmp_path / "questions_an")
    monkeypatch.setattr(cp, "SYCERON_CACHE_DIR", tmp_path / "syceron_an")

    code = fr.main(
        [
            "--semaine",
            SEMAINE,
            "--cle-restauree",
            f"public-data-cache-an-{SEMAINE_PRECEDENTE}",
            "--perimer",
        ]
    )
    assert code == 0
    assert not (tmp_path / "syceron_an" / "17").exists()
    assert (tmp_path / "syceron_an" / "16" / "index_par_acteur").is_dir()
    sortie = capsys.readouterr().out
    assert "Périmé" in sortie


def test_la_cli_emet_une_annotation_github(tmp_path, monkeypatch, capsys):
    """Un phénomène qui ne vit que dans 1 200 lignes de log n'est pas déclaré
    (#518) : le `::warning::` est le seul canal qui survit à la fermeture d'un
    run, et c'est là qu'on lira, six mois plus tard, quelle semaine a servi."""
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setattr(cp, "ACTEURS_HISTORIQUE_CACHE_DIR", tmp_path / "absent")
    monkeypatch.setattr(cp, "SCRUTINS_CACHE_DIR", tmp_path / "absent")
    monkeypatch.setattr(cp, "QUESTIONS_CACHE_DIR", tmp_path / "absent")
    monkeypatch.setattr(cp, "SYCERON_CACHE_DIR", tmp_path / "absent")

    fr.main(
        ["--semaine", SEMAINE, "--cle-restauree", f"public-data-cache-an-{SEMAINE_PRECEDENTE}"]
    )
    assert "::warning::" in capsys.readouterr().out


def test_la_cli_reste_silencieuse_sur_un_cache_frais(tmp_path, monkeypatch, capsys):
    """Un avertissement à chaque run noierait le seul cas qui en mérite un."""
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setattr(cp, "ACTEURS_HISTORIQUE_CACHE_DIR", tmp_path / "absent")
    monkeypatch.setattr(cp, "SCRUTINS_CACHE_DIR", tmp_path / "absent")
    monkeypatch.setattr(cp, "QUESTIONS_CACHE_DIR", tmp_path / "absent")
    monkeypatch.setattr(cp, "SYCERON_CACHE_DIR", tmp_path / "absent")

    fr.main(["--semaine", SEMAINE, "--cle-restauree", f"public-data-cache-an-{SEMAINE}", "--perimer"])
    sortie = capsys.readouterr().out
    assert "::warning::" not in sortie
    assert "::notice::" in sortie
