"""#885 — lire l'open data du Sénat sans base, et refuser ce qu'on ne publiera pas.

Trois choses sont gelées ici, et chacune a coûté quelque chose :

1. **Un export vide n'est pas un corpus vide.** L'archive publiée par
   `data.senat.fr` le 13/09/2026 à 03 h 33 faisait 444 octets et ne portait
   **aucune table** — avec un HTTP 200 et un `Content-Type: application/zip`.
   Republiée saine à 12 h 42. Un collecteur qui aurait tourné entre les deux
   aurait vidé les fiches sénatoriales sans rien signaler.
2. **`activite_senateur` ne se collecte pas** (§2 règle 3). Le refus est à
   l'entrée, pas à l'affichage : un filtre à l'affichage laisserait ses 11 069
   lignes de présence individuelle dans `raw_data/`, où la fusion additive les
   garderait (#729).
3. **Une sentinelle n'est pas une date.** 23 des 49 libellés de groupe portent
   `1899-12-31` ou `1900-01-01` pour dire « depuis toujours ». Publiée telle
   quelle, une sentinelle ferait commencer un groupe au XIXe siècle.

Toutes les doublures sont écrites dans `tmp_path` : aucun test ne lit l'export
réel, ne touche le réseau, ni ne lit le corpus publié (AGENTS.md §3, #457/#473/#488).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from senat_opendata import (  # noqa: E402
    COLONNE_NOMINATIVE,
    DUMP_TABLES_UTILES,
    SENTINELLES_DATE,
    TABLES_REFUSEES,
    ExportSenatVide,
    colonnes_des_tables,
    date_publiable,
    lire_tables,
    tables_nominatives_non_declarees,
    periodes_se_recouvrent,
    tables_manquantes,
)

ENTETE = """--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
"""


def _dump(tmp_path, blocs, nom="export_sens.sql"):
    """Un dump `pg_dump` texte. `blocs` : {table: (colonnes, [lignes])}."""
    morceaux = [ENTETE]
    for table, (colonnes, lignes) in blocs.items():
        morceaux.append(f"COPY {table} ({', '.join(colonnes)}) FROM stdin;\n")
        for ligne in lignes:
            morceaux.append("\t".join("\\N" if v is None else str(v) for v in ligne) + "\n")
        morceaux.append("\\.\n\n")
    chemin = tmp_path / nom
    chemin.write_text("".join(morceaux), encoding="utf-8")
    return chemin


# ---------------------------------------------------------------------------
# L'export vide — le cas qu'aucun code HTTP ne signale
# ---------------------------------------------------------------------------

def test_un_export_sans_aucune_table_est_refuse(tmp_path):
    """C'est l'état exact du 13/09/2026 à 03 h 33 : un dump valide, des `GRANT`,
    et rien d'autre. Poursuivre viderait les fiches en silence."""
    chemin = tmp_path / "vide.sql"
    chemin.write_text(ENTETE + "REVOKE ALL ON SCHEMA public FROM PUBLIC;\n", encoding="utf-8")

    with pytest.raises(ExportSenatVide) as echec:
        lire_tables(chemin)

    assert "aucune des tables attendues" in str(echec.value)


def test_le_refus_nomme_l_incident_qui_l_a_motive(tmp_path):
    """Un garde-fou qui bloque doit dire de quoi il tient sa règle, sinon le
    prochain lecteur le prend pour de la superstition."""
    chemin = tmp_path / "vide.sql"
    chemin.write_text(ENTETE, encoding="utf-8")

    with pytest.raises(ExportSenatVide) as echec:
        lire_tables(chemin)

    message = str(echec.value)
    assert "444" in message and "13/09/2026" in message, message


def test_une_table_vide_n_est_pas_un_export_vide(tmp_path):
    """Zéro ligne est une **mesure** ; l'absence de la table n'en est pas une
    (§2 règle 5). Confondre les deux ferait échouer un run sur un Sénat en
    vacances."""
    chemin = _dump(tmp_path, {"sen": (["senmat"], [])})

    tables = lire_tables(chemin, tables={"sen"})

    assert tables == {"sen": []}


# ---------------------------------------------------------------------------
# Ce qui ne se collecte pas
# ---------------------------------------------------------------------------

def test_activite_senateur_n_est_jamais_chargee(tmp_path):
    """§2 règle 3 : aucun taux de présence individuel n'est publié. Le refus est
    à l'entrée — demandée explicitement, la table n'est pas rendue."""
    chemin = _dump(tmp_path, {
        "sen": (["senmat"], [["86039K"]]),
        "activite_senateur": (["senmat", "nbseance"], [["86039K", "42"]]),
    })

    tables = lire_tables(chemin, tables={"sen", "activite_senateur"})

    assert "activite_senateur" not in tables
    assert tables["sen"] == [{"senmat": "86039K"}]


def test_la_table_refusee_porte_sa_raison():
    """Un refus sans motif se lève au premier qui trouve la donnée utile."""
    assert "activite_senateur" in TABLES_REFUSEES
    assert "règle 3" in TABLES_REFUSEES["activite_senateur"]


def test_aucune_table_utile_n_est_aussi_refusee():
    """Les deux ensembles ne peuvent pas se recouper : une table à la fois
    voulue et refusée se lirait selon l'ordre des tests."""
    assert not DUMP_TABLES_UTILES & set(TABLES_REFUSEES)


# ---------------------------------------------------------------------------
# Les dates
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("sentinelle", sorted(SENTINELLES_DATE))
def test_une_sentinelle_ne_devient_jamais_une_date(sentinelle):
    """« Depuis toujours » n'est pas une date. Une borne fausse est pire qu'une
    borne absente : elle se compare, elle s'affiche, et elle a l'air vraie."""
    assert date_publiable(f"{sentinelle} 00:50:39") is None
    assert date_publiable(sentinelle) is None


def test_un_horodatage_perd_son_heure():
    """L'heure d'un mandat ne veut rien dire, et la publier invite à croire
    qu'elle en dit quelque chose."""
    assert date_publiable("2015-06-02 00:00:00") == "2015-06-02"
    assert date_publiable("2015-06-02") == "2015-06-02"


def test_une_absence_reste_une_absence():
    """§2 règle 5, et ce n'est pas un cas rare : **1 064 appartenances de groupe
    sur 3 213** n'ont pas de date de début."""
    assert date_publiable(None) is None
    assert date_publiable("") is None


def test_une_forme_inattendue_ne_fait_pas_tomber_le_pipeline():
    """Ce module lit une source tierce : une forme qu'on n'a pas prévue est une
    donnée manquante, pas une panne."""
    assert date_publiable("bientôt") is None
    assert date_publiable("31/12/1899") is None


# ---------------------------------------------------------------------------
# Le recouvrement de périodes — le nom d'un organe à la date
# ---------------------------------------------------------------------------

def test_le_nom_a_la_date_est_celui_dont_la_periode_recouvre_le_mandat():
    """Le cas de `jean-luc-melenchon` : son appartenance du 28/11/2008 au
    07/01/2010 recouvre le libellé « Groupe CRC-SPG » (28/11/2008 →
    30/09/2011), et non celui d'aujourd'hui. C'est ce que l'Assemblée ne sait
    pas rendre, et ce qui a fait échouer #878."""
    assert periodes_se_recouvrent("2008-11-28", "2010-01-07", "2008-11-28", "2011-09-30")
    assert not periodes_se_recouvrent("2004-10-01", "2008-11-27", "2008-11-28", "2011-09-30")


def test_un_mandat_peut_recouvrir_deux_libelles():
    """Le cas de `bruno-retailleau`, 07/11/2012 → 21/10/2024 : « Groupe UMP »
    jusqu'au 01/06/2015, « Groupe Les Républicains » depuis le 02/06. Deux
    entrées à publier, jamais une seule sous le nom le plus récent (#885 §5.3)."""
    mandat = ("2012-11-07", "2024-10-21")
    assert periodes_se_recouvrent(*mandat, "2002-12-11", "2015-06-01")
    assert periodes_se_recouvrent(*mandat, "2015-06-02", None)


def test_une_borne_absente_est_ouverte_jamais_zero():
    """Une fin inconnue se lit « toujours en cours », un début inconnu « depuis
    toujours ». C'est le seul endroit où une absence reçoit une valeur — et elle
    sert à comparer, jamais à publier."""
    assert periodes_se_recouvrent(None, None, "2008-11-28", "2011-09-30")
    assert periodes_se_recouvrent("2020-01-01", None, "2015-06-02", None)
    assert not periodes_se_recouvrent("2016-01-01", "2017-01-01", "2018-01-01", None)


def test_un_recouvrement_d_un_seul_jour_compte():
    """Les bornes sont inclusives des deux côtés : la source ferme un libellé le
    01/06 et ouvre le suivant le 02/06, sans trou."""
    assert periodes_se_recouvrent("2015-06-01", "2015-06-01", "2002-12-11", "2015-06-01")
    assert not periodes_se_recouvrent("2015-06-02", "2015-06-02", "2002-12-11", "2015-06-01")


# ---------------------------------------------------------------------------
# La lecture elle-même
# ---------------------------------------------------------------------------

def test_les_tables_non_demandees_sont_traversees_sans_etre_construites(tmp_path):
    """Le dump porte 93 tables pour 8 utiles. Les charger toutes coûterait 58 Mo
    de mémoire pour en utiliser huit."""
    chemin = _dump(tmp_path, {
        "sen": (["senmat"], [["86039K"]]),
        "adresse": (["id", "rue"], [["1", "15 rue de Vaugirard"]]),
        "elusen": (["senmat", "eludatdeb"], [["86039K", "1986-10-02 00:00:00"]]),
    })

    tables = lire_tables(chemin, tables={"sen", "elusen"})

    assert set(tables) == {"sen", "elusen"}
    assert tables["elusen"][0]["eludatdeb"] == "1986-10-02 00:00:00"


def test_le_marqueur_de_nul_devient_none(tmp_path):
    """`\\N` est le `NULL` de `pg_dump`. Le laisser en chaîne publierait « \\N »
    comme s'il s'agissait d'un libellé."""
    chemin = _dump(tmp_path, {
        "memgrppol": (["senmat", "memgrppoldatdeb"], [["86039K", None]]),
    })

    tables = lire_tables(chemin, tables={"memgrppol"})

    assert tables["memgrppol"][0]["memgrppoldatdeb"] is None


def test_les_tables_manquantes_sont_declarees_jamais_levees(tmp_path):
    """Une table absente d'un export par ailleurs valide est une information sur
    la source ; l'appelant décide si elle lui est vitale."""
    chemin = _dump(tmp_path, {"sen": (["senmat"], [["86039K"]])})

    tables = lire_tables(chemin, tables=DUMP_TABLES_UTILES)

    manquantes = tables_manquantes(tables)
    assert "elusen" in manquantes
    assert "sen" not in manquantes
    assert "activite_senateur" not in manquantes


def test_une_ligne_plus_courte_que_son_entete_ne_leve_pas(tmp_path):
    """Robustesse de lecture : les colonnes absentes manquent, elles ne cassent
    pas le passage."""
    chemin = tmp_path / "court.sql"
    chemin.write_text(
        ENTETE + "COPY sen (senmat, sennomuse, senprenomuse) FROM stdin;\n"
        "86039K\tMélenchon\n\\.\n", encoding="utf-8")

    tables = lire_tables(chemin, tables={"sen"})

    assert tables["sen"] == [{"senmat": "86039K", "sennomuse": "Mélenchon"}]


# ---------------------------------------------------------------------------
# #885 point 4 — refuser une table par son nom ne protège que du déjà-vu
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("table", sorted(TABLES_REFUSEES))
def test_les_trois_tables_de_presence_sont_refusees(table):
    """Il n'y en avait qu'une au premier passage. Mesuré ensuite :

      - `activite_senateur`, 11 069 lignes d'activité nominative ;
      - `activite_participant`, **675 839** lignes portant `typactparcod:
        PRESENT` sur 698 sénateurs — soixante fois plus, et c'est **le**
        registre de présence ;
      - `activite_delegation`, 3 049 délégations de vote `senmat` →
        `senmat_delegue`, c'est-à-dire de l'**absence** nominative.
    """
    assert table in TABLES_REFUSEES
    assert "règle 3" in TABLES_REFUSEES[table]


def test_aucune_table_d_activite_nominative_n_est_lue(tmp_path):
    """Demandées explicitement, aucune des trois n'est rendue."""
    chemin = _dump(tmp_path, {
        "sen": (["senmat"], [["04033B"]]),
        "activite_senateur": (["senmat", "libelle"], [["04033B", "Réunion"]]),
        "activite_participant": (["senmat", "typactparcod"], [["04033B", "PRESENT"]]),
        "activite_delegation": (["senmat", "senmat_delegue"], [["04033B", "86039K"]]),
    })

    tables = lire_tables(chemin, tables={"sen"} | set(TABLES_REFUSEES))

    assert set(tables) == {"sen"}


def test_une_table_nominative_non_declaree_est_signalee():
    """Refuser par le nom ne protège que de ce qu'on a déjà vu. Une table qui
    porte `senmat` décrit quelqu'un : elle est utile, refusée, ou signalée — la
    quatrième issue, l'oubli, est celle qui a laissé passer 675 839 lignes."""
    inventaire = {
        "sen": ["senmat", "sennomuse"],                  # utile
        "activite_participant": ["senmat", "actid"],     # refusée
        "activite_secrete": ["senmat", "presence"],      # ni l'un ni l'autre
        "dpt": ["dptnum", "dptlib"],                     # ne nomme personne
    }

    assert tables_nominatives_non_declarees(inventaire) == ["activite_secrete"]


def test_la_colonne_nominative_est_celle_du_jeu():
    """Si le Sénat renommait sa clé de personne, le contrôle deviendrait muet
    sans rien signaler — d'où une constante, lisible, plutôt qu'un littéral."""
    assert COLONNE_NOMINATIVE == "senmat"


def test_l_inventaire_ne_lit_aucune_ligne(tmp_path):
    """Inventorier 93 tables et 58 Mo ne doit pas coûter leur contenu."""
    chemin = _dump(tmp_path, {
        "sen": (["senmat", "sennomuse"], [["04033B", "Retailleau"]]),
        "activite_participant": (["senmat", "typactparcod"], [["04033B", "PRESENT"]]),
    })

    colonnes = colonnes_des_tables(chemin)

    assert colonnes == {"sen": ["senmat", "sennomuse"],
                        "activite_participant": ["senmat", "typactparcod"]}
