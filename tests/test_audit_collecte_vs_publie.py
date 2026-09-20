"""#545 — une liste publiée qui porte moins que ce que la collecte a rendu doit
être nommée et bloquer.

Le run `33100214165` (27/08/2026) s'est conclu en **succès** avec 7 767
interventions collectées et 891 publiées : la clé de fusion pivot prenait l'URL
d'archive Syceron pour un identifiant (#540), et écrasait tout un débat sur une
entrée. **Aucun des trois garde-fous armés avant commit ne pouvait le voir** :

  - `audit_diff_profils` (#460/#470) surveille les *pertes* entre une référence
    git et le disque. La publication a *augmenté* — 0 → 891 — donc rien à voir ;
  - `audit_collecte_non_publiee` (#511) raisonne sur des **profils** : les sept
    porteurs avaient tous un pivot ;
  - `audit_integrite_referentielle` (#485) ne **compte** rien : les 891 clés
    résolvaient toutes.

Ces tests verrouillent autant la détection que **la table de relations** —
c'est elle qui distingue ce contrôle d'un `assert len(raw) == len(pivot)` qui
crierait à tort sur `dossiers_legislatifs` → `textes_portes` (un renommage) et
sur `mandats` (un enrichissement attribué).

Toutes les doublures ici sont des répertoires `tmp_path` : aucun test ne lit
`raw_data/profiles/` ni `pivot_data/profiles/`, ni ne touche le réseau
(AGENTS.md §3, #457/#473/#488).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from audit_collecte_vs_publie import (  # noqa: E402
    CHAMPS_PIVOT_DERIVES,
    PLAFOND_EXEMPLES,
    RELATIONS,
    SEUIL_DEFICIT,
    auditer,
    compter_listes,
    generate_markdown_report,
    main as audit_main,
)


def _corpus(tmp_path, profils):
    """Deux répertoires de doublures.

    `profils` : `{slug: (dict brut, dict pivot | None)}`. Un pivot `None` écrit
    le brut seul — le cas que #511 traite et que celui-ci ne doit pas doubler.
    """
    raw_dir = tmp_path / "raw"
    pivot_dir = tmp_path / "pivot"
    raw_dir.mkdir(exist_ok=True)
    pivot_dir.mkdir(exist_ok=True)
    for slug, (brut, pivot) in profils.items():
        (raw_dir / f"{slug}.json").write_text(
            json.dumps(brut, ensure_ascii=False), encoding="utf-8")
        if pivot is not None:
            (pivot_dir / f"{slug}.pivot.json").write_text(
                json.dumps(pivot, ensure_ascii=False), encoding="utf-8")
    return raw_dir, pivot_dir


def _entrees(n):
    """`n` entrées de liste, au contenu indifférent : ce contrôle compte."""
    return [{"i": i} for i in range(n)]


# ---------------------------------------------------------------------------
# Le cas nominal
# ---------------------------------------------------------------------------

def test_un_corpus_ou_tout_est_publie_ne_bloque_pas(tmp_path):
    raw_dir, pivot_dir = _corpus(tmp_path, {
        "alice": (
            {"votes": _entrees(3), "amendements": _entrees(5),
             "interventions": _entrees(2), "dossiers_legislatifs": _entrees(1),
             "mandats": _entrees(4)},
            {"votes": _entrees(3), "amendements": _entrees(5),
             "interventions": _entrees(2), "textes_portes": _entrees(1),
             "mandats": _entrees(4)},
        ),
    })

    rapport = auditer(raw_dir, pivot_dir)

    assert rapport["nb_profils_compares"] == 1
    assert rapport["nb_deficits"] == 0
    assert rapport["nb_excedents"] == 0
    assert rapport["bloquant"] is False


def test_le_seuil_par_defaut_est_zero():
    """Mesuré, pas arrondi : 0 déficit et 0 excédent sur les 2 380 couples
    (profil, relation) des 476 profils de `3104e37` — et les quatre relations
    hors interventions tiennent aussi sur `deb28a7`, l'état d'avant #540."""
    assert SEUIL_DEFICIT == 0


# ---------------------------------------------------------------------------
# L'incident #540
# ---------------------------------------------------------------------------

def test_une_liste_publiee_en_deficit_bloque_et_nomme_le_profil(tmp_path):
    """Le cas exact de `gabriel-attal` sur `deb28a7` : 3 351 collectées, 17
    publiées. #518 a imposé que le contrôle NOMME : « Process completed with
    exit code 1 » ne dit rien."""
    raw_dir, pivot_dir = _corpus(tmp_path, {
        "gabriel-attal": ({"interventions": _entrees(3351)},
                          {"interventions": _entrees(17)}),
        "sans-defaut": ({"interventions": _entrees(10)},
                        {"interventions": _entrees(10)}),
    })

    rapport = auditer(raw_dir, pivot_dir)

    assert rapport["bloquant"] is True
    assert rapport["nb_deficits"] == 1
    ecart = rapport["deficits"][0]
    assert ecart["slug"] == "gabriel-attal"
    assert ecart["champ_pivot"] == "interventions"
    assert (ecart["collecte"], ecart["publie"], ecart["delta"]) == (3351, 17, -3334)


def test_les_plus_gros_ecarts_sont_nommes_en_premier(tmp_path):
    """Le plafond d'exemples ne sert à rien s'il montre les écarts d'une entrée
    pendant qu'un profil en perd 3 334."""
    profils = {f"minus-{i}": ({"interventions": _entrees(2)},
                              {"interventions": _entrees(1)})
               for i in range(PLAFOND_EXEMPLES + 5)}
    profils["gabriel-attal"] = ({"interventions": _entrees(3351)},
                                {"interventions": _entrees(17)})
    raw_dir, pivot_dir = _corpus(tmp_path, profils)

    rapport = auditer(raw_dir, pivot_dir)

    assert rapport["deficits"][0]["slug"] == "gabriel-attal"
    assert len(rapport["deficits"]) == PLAFOND_EXEMPLES
    assert rapport["nb_deficits"] == PLAFOND_EXEMPLES + 6


def test_un_effondrement_de_cle_est_vu_meme_quand_la_publication_augmente(tmp_path):
    """Ce que le contrôle de perte (#460/#470) ne peut pas voir.

    Entre deux runs, la publication passe de 0 à 891 : une **hausse**. Le
    contrôle de perte ne bloque pas — à raison, rien n'a été perdu. Ici, seul
    compte l'écart avec ce que la collecte a rendu dans le MÊME run.
    """
    raw_dir, pivot_dir = _corpus(tmp_path, {
        "porteur": ({"interventions": _entrees(7767)},
                    {"interventions": _entrees(891)}),
    })

    rapport = auditer(raw_dir, pivot_dir)

    assert rapport["bloquant"] is True
    assert rapport["deficits"][0]["delta"] == -6876


# ---------------------------------------------------------------------------
# La table de relations — le cœur du contrôle
# ---------------------------------------------------------------------------

def test_le_renommage_ne_produit_aucun_faux_positif(tmp_path):
    """`dossiers_legislatifs` (brut) → `textes_portes` (pivot).

    Comparer les champs de même nom rendrait −472 sur l'un ET +472 sur l'autre :
    deux faux positifs pour zéro défaut. Mesuré sur les 476 profils de
    `3104e37` : 472 des deux côtés.
    """
    raw_dir, pivot_dir = _corpus(tmp_path, {
        "alice": ({"dossiers_legislatifs": _entrees(472)},
                  {"textes_portes": _entrees(472)}),
    })

    rapport = auditer(raw_dir, pivot_dir)

    assert rapport["nb_deficits"] == 0
    assert rapport["nb_excedents"] == 0
    assert rapport["bloquant"] is False


def test_le_renommage_reste_surveille(tmp_path):
    """Un renommage déclaré n'est pas un champ désarmé : si `textes_portes`
    s'effondre, le déficit doit sortir."""
    raw_dir, pivot_dir = _corpus(tmp_path, {
        "alice": ({"dossiers_legislatifs": _entrees(472)},
                  {"textes_portes": _entrees(3)}),
    })

    rapport = auditer(raw_dir, pivot_dir)

    assert rapport["bloquant"] is True
    assert rapport["deficits"][0]["champ_pivot"] == "textes_portes"
    assert rapport["deficits"][0]["delta"] == -469


def test_l_enrichissement_europeen_est_attribue_et_non_tolere(tmp_path):
    """`mandats` du pivot = `mandats` + `mandat_europeen.mandats_europeens` du brut.

    `generate_all_profiles.py:779` et `:989` versent les mandats européens dans
    `mandats[]` du pivot ; le brut les range à part. Mesuré sur les 476 profils
    de `3104e37` : l'écart pivot−brut égale **exactement** ce compte, profil par
    profil, sans exception (40 432 = 40 154 + 278). D'où une somme de sources,
    et pas une marge de tolérance.
    """
    raw_dir, pivot_dir = _corpus(tmp_path, {
        "manuel-bompard": (
            {"mandats": _entrees(39),
             "mandat_europeen": {"mandats_europeens": _entrees(23)}},
            {"mandats": _entrees(62)},
        ),
    })

    rapport = auditer(raw_dir, pivot_dir)

    assert rapport["nb_deficits"] == 0
    assert rapport["nb_excedents"] == 0
    relation = next(r for r in rapport["relations"] if r["champ_pivot"] == "mandats")
    assert relation["collecte"] == 62
    assert relation["publie"] == 62
    assert relation["nature"] == "enrichissement attribué"


def test_l_apport_europeen_manquant_est_un_deficit(tmp_path):
    """La contrepartie : si les mandats européens ne sont PAS versés dans le
    pivot, l'écart est un déficit — pas une marge absorbée en silence."""
    raw_dir, pivot_dir = _corpus(tmp_path, {
        "manuel-bompard": (
            {"mandats": _entrees(39),
             "mandat_europeen": {"mandats_europeens": _entrees(23)}},
            {"mandats": _entrees(39)},
        ),
    })

    rapport = auditer(raw_dir, pivot_dir)

    assert rapport["bloquant"] is True
    assert rapport["deficits"][0]["delta"] == -23
    assert "mandat_europeen.mandats_europeens" in rapport["deficits"][0]["sources"]


def test_la_table_declare_une_relation_par_liste_publiee():
    """Une liste publiée ne peut pas avoir deux relations : la seconde
    masquerait la première."""
    champs = [r.champ_pivot for r in RELATIONS]
    assert len(champs) == len(set(champs))
    assert set(champs) == {"votes", "amendements", "interventions",
                           "textes_portes", "mandats"}


def test_chaque_relation_porte_sa_justification():
    """Une relation sans justification est une règle qu'on ne peut pas
    contester — donc pas une règle mesurée (AGENTS.md §2.2)."""
    for relation in RELATIONS:
        assert relation.justification.strip(), relation.champ_pivot
        assert relation.sources, relation.champ_pivot


def test_les_champs_pivot_derives_ne_recoupent_pas_la_table():
    """`chambres`, `tags_thematiques`, `sources` n'ont aucune source collectée.
    Les nommer à part est ce qui rend leur absence de la table un choix
    documenté et non un oubli."""
    assert not (set(CHAMPS_PIVOT_DERIVES) & {r.champ_pivot for r in RELATIONS})


# ---------------------------------------------------------------------------
# L'excédent : rapporté, jamais bloquant
# ---------------------------------------------------------------------------

def test_un_excedent_est_rapporte_sans_bloquer(tmp_path):
    """La fusion pivot est additive (AGENTS.md §3) : un pivot garde les entrées
    d'un run précédent que la collecte du jour n'a pas rendues. Faux négatif
    assumé, faux positif refusé — le même arbitrage qu'`audit_diff_profils` sur
    les changements de valeur."""
    raw_dir, pivot_dir = _corpus(tmp_path, {
        "alice": ({"votes": _entrees(3)}, {"votes": _entrees(10)}),
    })

    rapport = auditer(raw_dir, pivot_dir)

    assert rapport["bloquant"] is False
    assert rapport["nb_excedents"] == 1
    assert rapport["excedents"][0]["delta"] == 7
    assert "Excédents" in generate_markdown_report(rapport)


# ---------------------------------------------------------------------------
# La prochaine source branchée
# ---------------------------------------------------------------------------

def test_une_liste_collectee_sans_relation_est_nommee_sans_bloquer(tmp_path):
    """« Il manquera à la prochaine source branchée » (#545).

    Une liste du brut qui ne figure dans aucune relation ne doit pas rester
    muette — mais elle ne doit pas non plus annuler un commit au motif qu'une
    relation reste à écrire.
    """
    raw_dir, pivot_dir = _corpus(tmp_path, {
        "alice": ({"votes": _entrees(2), "questions_ecrites": _entrees(9)},
                  {"votes": _entrees(2)}),
    })

    rapport = auditer(raw_dir, pivot_dir)

    assert rapport["bloquant"] is False
    assert rapport["champs_bruts_non_declares"] == ["questions_ecrites"]
    assert rapport["nb_profils_champs_non_declares"] == 1
    assert "questions_ecrites" in generate_markdown_report(rapport)


# ---------------------------------------------------------------------------
# Périmètre : ce que ce contrôle ne double pas
# ---------------------------------------------------------------------------

def test_un_brut_sans_pivot_n_est_pas_compte_en_deficit(tmp_path):
    """C'est le périmètre de #511, qui bloque déjà dessus. Le rapporter ici en
    déficit de 100 % décrirait un autre défaut que le nôtre."""
    raw_dir, pivot_dir = _corpus(tmp_path, {
        "publie": ({"votes": _entrees(3)}, {"votes": _entrees(3)}),
        "jamais-publie": ({"votes": _entrees(3536)}, None),
    })

    rapport = auditer(raw_dir, pivot_dir)

    assert rapport["nb_sans_pivot"] == 1
    assert rapport["sans_pivot"] == ["jamais-publie"]
    assert rapport["nb_deficits"] == 0
    assert rapport["nb_profils_compares"] == 1
    assert rapport["bloquant"] is False


def test_un_fichier_de_service_n_est_pas_un_profil(tmp_path):
    """`raw_data/profiles/.generation_checkpoint.json` a fait échouer le run
    `32773067295` sur le contrôle voisin (#518). Un slug ne peut pas commencer
    par un point : la propriété du générateur de noms, pas une liste
    d'exceptions à tenir."""
    raw_dir, pivot_dir = _corpus(tmp_path, {
        "alice": ({"votes": _entrees(1)}, {"votes": _entrees(1)}),
    })
    (raw_dir / ".generation_checkpoint.json").write_text("{}", encoding="utf-8")

    rapport = auditer(raw_dir, pivot_dir)

    assert rapport["nb_profils_compares"] == 1
    assert rapport["nb_sans_pivot"] == 0
    assert rapport["bloquant"] is False


# ---------------------------------------------------------------------------
# Un contrôle qui n'a rien lu n'est pas un contrôle vert
# ---------------------------------------------------------------------------

def test_le_repertoire_brut_absent_bloque(tmp_path):
    pivot_dir = tmp_path / "pivot"
    pivot_dir.mkdir()

    rapport = auditer(tmp_path / "absent", pivot_dir)

    assert rapport["repertoire_brut_absent"] is True
    assert rapport["bloquant"] is True
    assert "n'est pas un rapprochement vert" in generate_markdown_report(rapport)


def test_le_repertoire_pivot_absent_bloque(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    rapport = auditer(raw_dir, tmp_path / "absent")

    assert rapport["repertoire_pivot_absent"] is True
    assert rapport["bloquant"] is True


def test_un_profil_illisible_bloque(tmp_path):
    """Un profil qu'on n'a pas pu lire n'est pas un profil à 0 entrée : c'est un
    rapprochement qui n'a pas eu lieu (AGENTS.md §2.5). Le taire rendrait vert
    exactement ce que ce contrôle traque."""
    raw_dir, pivot_dir = _corpus(tmp_path, {
        "alice": ({"votes": _entrees(1)}, {"votes": _entrees(1)}),
        "casse": ({"votes": _entrees(1)}, {"votes": _entrees(1)}),
    })
    (raw_dir / "casse.json").write_text("{ceci n'est pas du JSON", encoding="utf-8")

    rapport = auditer(raw_dir, pivot_dir)

    assert rapport["nb_illisibles"] == 1
    assert rapport["illisibles"] == ["casse"]
    assert rapport["bloquant"] is True


def test_un_corpus_vide_ne_passe_pas_pour_un_corpus_sain(tmp_path):
    """Zéro profil rapproché n'est pas « rien à signaler » : c'est un contrôle
    qui n'a rien lu, et le rapport doit le dire."""
    raw_dir, pivot_dir = _corpus(tmp_path, {})

    rapport = auditer(raw_dir, pivot_dir)

    assert rapport["nb_profils_compares"] == 0
    assert "n'a rien lu" in generate_markdown_report(rapport)


# ---------------------------------------------------------------------------
# Lecture à mémoire bornée
# ---------------------------------------------------------------------------

def test_le_comptage_ne_lit_que_le_premier_niveau(tmp_path):
    """Le crochet de décodage retient les clés de la table **partout** dans le
    document — la navigation, elle, part de la racine. Une entrée de `mandats`
    qui porterait sa propre liste `votes` ne doit pas changer le compte des
    votes du profil."""
    chemin = tmp_path / "piege.json"
    chemin.write_text(json.dumps({
        "votes": _entrees(3),
        "mandats": [{"votes": _entrees(999)}, {"votes": _entrees(999)}],
    }), encoding="utf-8")

    releve = compter_listes(chemin)

    assert releve["votes"] == 3
    assert releve["mandats"] == 2


def test_le_comptage_ne_materialise_pas_les_entrees(tmp_path):
    """Le corpus réel pèse 4,3 Go de profils bruts et ce script tourne AVANT le
    commit : s'il meurt, rien n'est publié (#460). Le relevé ne doit porter que
    des longueurs, jamais le contenu."""
    chemin = tmp_path / "gros.json"
    chemin.write_text(json.dumps({
        "amendements": [{"texte": "x" * 50} for _ in range(200)],
    }), encoding="utf-8")

    releve = compter_listes(chemin)

    assert releve == {"amendements": 200}


def test_un_champ_absent_vaut_zero(tmp_path):
    """Indistinct d'une liste vide, et c'est voulu : dans les deux cas le
    document ne porte aucune entrée."""
    raw_dir, pivot_dir = _corpus(tmp_path, {
        "minimal": ({"mandat_europeen": {"mandats_europeens": _entrees(2)}},
                    {"mandats": _entrees(2)}),
    })

    rapport = auditer(raw_dir, pivot_dir)

    assert rapport["bloquant"] is False
    votes = next(r for r in rapport["relations"] if r["champ_pivot"] == "votes")
    assert (votes["collecte"], votes["publie"]) == (0, 0)


# ---------------------------------------------------------------------------
# CLI, codes de retour, annotations
# ---------------------------------------------------------------------------

def test_main_sort_en_erreur_sur_un_deficit(tmp_path, capsys):
    raw_dir, pivot_dir = _corpus(tmp_path, {
        "gabriel-attal": ({"interventions": _entrees(3351)},
                          {"interventions": _entrees(17)}),
    })

    code = audit_main(["--raw-dir", str(raw_dir), "--pivot-dir", str(pivot_dir)])

    assert code == 1
    assert "gabriel-attal" in capsys.readouterr().err


def test_main_sort_a_zero_sur_un_corpus_sain(tmp_path):
    raw_dir, pivot_dir = _corpus(tmp_path, {
        "alice": ({"votes": _entrees(3)}, {"votes": _entrees(3)}),
    })

    assert audit_main(["--raw-dir", str(raw_dir), "--pivot-dir", str(pivot_dir)]) == 0


def test_la_tolerance_ne_masque_pas_le_constat(tmp_path, capsys):
    """`--tolerer-ecarts` rend 0 mais continue de nommer : une perte déclarée
    reste une perte relevée."""
    raw_dir, pivot_dir = _corpus(tmp_path, {
        "gabriel-attal": ({"interventions": _entrees(3351)},
                          {"interventions": _entrees(17)}),
    })

    code = audit_main(["--raw-dir", str(raw_dir), "--pivot-dir", str(pivot_dir),
                       "--tolerer-ecarts"])

    assert code == 0
    assert "gabriel-attal" in capsys.readouterr().err


def test_l_annotation_nomme_les_profils_et_les_deux_comptes(tmp_path, capsys, monkeypatch):
    """#518 : « Process completed with exit code 1 » ne dit rien. L'annotation
    est le seul canal qui survit à la fermeture d'un run."""
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    raw_dir, pivot_dir = _corpus(tmp_path, {
        "gabriel-attal": ({"interventions": _entrees(3351)},
                          {"interventions": _entrees(17)}),
    })

    audit_main(["--raw-dir", str(raw_dir), "--pivot-dir", str(pivot_dir)])

    sortie = capsys.readouterr().out
    annotation = next(l for l in sortie.split("\n") if l.startswith("::error::"))
    assert "COLLECTE_VS_PUBLIE" in annotation
    assert "gabriel-attal" in annotation
    assert "3351" in annotation and "17" in annotation
    # Le total de ce qui est publié nulle part, pas seulement un nombre de
    # couples : c'est la grandeur qui dit la gravité.
    assert "3334" in annotation


def test_l_annotation_de_tolerance_est_un_avertissement(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    raw_dir, pivot_dir = _corpus(tmp_path, {
        "alice": ({"interventions": _entrees(10)}, {"interventions": _entrees(1)}),
    })

    audit_main(["--raw-dir", str(raw_dir), "--pivot-dir", str(pivot_dir),
                "--tolerer-ecarts"])

    sortie = capsys.readouterr().out
    assert "::warning::" in sortie
    assert "::error::" not in sortie


def test_une_liste_sans_relation_declaree_part_en_annotation(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    raw_dir, pivot_dir = _corpus(tmp_path, {
        "alice": ({"votes": _entrees(2), "questions_ecrites": _entrees(9)},
                  {"votes": _entrees(2)}),
    })

    code = audit_main(["--raw-dir", str(raw_dir), "--pivot-dir", str(pivot_dir)])

    sortie = capsys.readouterr().out
    assert code == 0
    assert "::warning::" in sortie
    assert "questions_ecrites" in sortie


def test_les_rapports_sont_ecrits_ou_on_les_demande(tmp_path):
    raw_dir, pivot_dir = _corpus(tmp_path, {
        "alice": ({"votes": _entrees(3)}, {"votes": _entrees(3)}),
    })
    md = tmp_path / "rapports" / "collecte-vs-publie.md"
    js = tmp_path / "rapports" / "collecte-vs-publie.json"

    audit_main(["--raw-dir", str(raw_dir), "--pivot-dir", str(pivot_dir),
                "--out", str(md), "--out-json", str(js)])

    assert "Collecté vs publié" in md.read_text(encoding="utf-8")
    assert json.loads(js.read_text(encoding="utf-8"))["nb_profils_compares"] == 1


def test_le_rapport_expose_la_table_de_relations(tmp_path):
    """La table est ce qui distingue ce contrôle d'un compteur naïf : elle doit
    être lisible dans le rapport, pas seulement dans le code."""
    raw_dir, pivot_dir = _corpus(tmp_path, {
        "alice": ({"votes": _entrees(3)}, {"votes": _entrees(3)}),
    })

    markdown = generate_markdown_report(auditer(raw_dir, pivot_dir))

    assert "Relations attendues" in markdown
    for relation in RELATIONS:
        assert f"`{relation.champ_pivot}`" in markdown
        assert f"`{relation.libelle_sources}`" in markdown


# ---------------------------------------------------------------------------
# #888 — la réduction nommée : des entrées collectées qui n'en font qu'une
# ---------------------------------------------------------------------------

def _paire_europeenne(organisation, debut, fin):
    """La forme exacte que le portail européen publie en double (#879).

    L'une classée (`EU_INSTITUTION`, rôle générique), l'autre non (`AUTRE`,
    rôle explicite). Même organisation, même période : c'est **une**
    appartenance, écrite deux fois par la source.
    """
    return [
        {"type": "EU_INSTITUTION", "organisation_nom": organisation,
         "debut": debut, "fin": fin, "role": "MEMBER", "role_label": "Membre"},
        {"type": "AUTRE", "organisation_nom": organisation,
         "debut": debut, "fin": fin, "role": "MEMBER_PARLIAMENT",
         "role_label": "Membre du Parlement européen"},
    ]


def test_un_doublon_du_portail_europeen_n_est_pas_un_deficit(tmp_path):
    """Le run `34712936188` a bloqué sur 29 profils et 45 entrées, toutes sur
    `mandats`, sans qu'aucune donnée soit perdue : le brut porte les deux
    moitiés d'une paire que `dedupliquer_appartenances` réduit à une (#879).

    Le compte collecté est celui des entrées **distinctes**. Pas une tolérance :
    la même fonction, rejouée sur le brut.
    """
    raw_dir, pivot_dir = _corpus(tmp_path, {
        "jordan-bardella": (
            {"mandats": [],
             "mandat_europeen": {"mandats_europeens":
                                 _paire_europeenne("Mandat de député européen",
                                                   "2019-07-02", "2024-07-15")
                                 + _paire_europeenne("Mandat de député européen",
                                                     "2024-07-16", None)}},
            {"mandats": _entrees(2)},
        ),
    })

    rapport = auditer(raw_dir, pivot_dir)

    assert rapport["bloquant"] is False
    assert rapport["nb_deficits"] == 0
    assert rapport["nb_excedents"] == 0
    relation = next(r for r in rapport["relations"] if r["champ_pivot"] == "mandats")
    assert relation["collecte"] == 2


def test_la_reduction_ne_couvre_pas_une_vraie_perte(tmp_path):
    """La contrepartie, et c'est elle qui fait du correctif autre chose qu'un
    `allow_declared_losses` déguisé : une entrée qui n'est le doublon de rien
    reste un déficit."""
    raw_dir, pivot_dir = _corpus(tmp_path, {
        "jordan-bardella": (
            {"mandats": [],
             "mandat_europeen": {"mandats_europeens":
                                 _paire_europeenne("Mandat de député européen",
                                                   "2019-07-02", "2024-07-15")
                                 + [{"type": "COMMITTEE_PARLIAMENTARY_STANDING",
                                     "organisation_nom": "Commission des pétitions",
                                     "debut": "2019-07-02", "fin": None,
                                     "role": "MEMBER"}]}},
            {"mandats": _entrees(1)},
        ),
    })

    rapport = auditer(raw_dir, pivot_dir)

    assert rapport["bloquant"] is True
    assert rapport["deficits"][0]["delta"] == -1


def test_deux_appartenances_classees_ne_sont_jamais_reduites(tmp_path):
    """Le critère de #879 est étroit, et ce contrôle ne l'élargit pas : membre
    et vice-président d'une même commission sur la même période sont **deux**
    faits, et les confondre en perdrait un (§2 règle 2)."""
    raw_dir, pivot_dir = _corpus(tmp_path, {
        "jean-louis-bourlanges": (
            {"mandats": [],
             "mandat_europeen": {"mandats_europeens": [
                 {"type": "COMMITTEE_PARLIAMENTARY_STANDING",
                  "organisation_nom": "Commission des budgets",
                  "debut": "1999-07-20", "fin": "2004-07-19", "role": "MEMBER"},
                 {"type": "COMMITTEE_PARLIAMENTARY_STANDING",
                  "organisation_nom": "Commission des budgets",
                  "debut": "1999-07-20", "fin": "2004-07-19", "role": "CHAIR_VICE"},
             ]}},
            {"mandats": _entrees(1)},
        ),
    })

    rapport = auditer(raw_dir, pivot_dir)

    assert rapport["bloquant"] is True
    assert rapport["deficits"][0]["delta"] == -1


def test_la_reduction_se_lit_dans_le_rapport(tmp_path):
    """Un garde-fou qui soustrait doit dire ce qu'il soustrait, et pourquoi —
    sinon la soustraction est indistinguable d'une marge tolérée."""
    raw_dir, pivot_dir = _corpus(tmp_path, {
        "alice": ({"votes": _entrees(3)}, {"votes": _entrees(3)}),
    })

    rapport = auditer(raw_dir, pivot_dir)
    markdown = generate_markdown_report(rapport)

    assert "doublons du portail européen (#879)" in markdown
    relation = next(r for r in rapport["relations"] if r["champ_pivot"] == "mandats")
    assert "deux fois" in relation["justification"]


def test_une_seule_relation_porte_une_reduction():
    """Quatre relations sur cinq ne retirent rien, et `None` le dit : une
    réduction qu'on ajouterait ailleurs sans la mesurer serait exactement la
    marge non attribuée que #545 refuse."""
    avec_reduction = [r.champ_pivot for r in RELATIONS if r.reduction is not None]

    assert avec_reduction == ["mandats"]
    for relation in RELATIONS:
        if relation.reduction is not None:
            assert relation.reduction.justification
            assert relation.reduction.libelle in relation.libelle_sources
