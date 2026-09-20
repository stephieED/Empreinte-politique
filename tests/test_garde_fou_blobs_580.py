"""Garde-fou sur la taille du plus gros fichier versionné (#580, volet A).

Le seuil de 50 Mo était la quatrième clause du critère de sortie de #429. Il
n'a jamais été un critère : il a été franchi le jour même de son écriture, et
l'avertissement de GitHub au push est passé inaperçu **parce que rien ne disait
quoi en faire**.

Ces tests exigent donc les deux moitiés de la correction :

  - le contrôle **se déclenche** — il avertit à 50 Mo, il **bloque** à 80 ;
  - il **dit quoi faire** — la conduite à tenir sort avec le constat, et elle
    ne comporte ni « relever le seuil » ni « supprimer de la donnée ».
"""

import pytest

import garde_fou_blobs as gf
from garde_fou_blobs import (
    CONDUITE_A_TENIR,
    LIMITE_DURE_OCTETS,
    SEUIL_AVERTISSEMENT_OCTETS,
    SEUIL_BLOQUANT_OCTETS,
    evaluer,
    inventorier,
    rapport,
)


def _fichier(dossier, nom, octets):
    chemin = dossier / nom
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_bytes(b"x" * octets)
    return chemin


# ---------------------------------------------------------------------------
# Les seuils
# ---------------------------------------------------------------------------

def test_les_seuils_sont_ordonnes():
    """Un garde-fou qui bloquerait avant d'avertir n'avertirait jamais, et un
    garde-fou qui n'alerterait qu'à la limite dure alerterait quand le blob est
    déjà committé."""
    assert SEUIL_AVERTISSEMENT_OCTETS < SEUIL_BLOQUANT_OCTETS < LIMITE_DURE_OCTETS
    assert SEUIL_AVERTISSEMENT_OCTETS == 50 * 1024 * 1024
    assert LIMITE_DURE_OCTETS == 100 * 1024 * 1024


def test_seuils_inverses_refuses(tmp_path):
    with pytest.raises(ValueError, match="avant d'avertir"):
        evaluer([tmp_path], seuil_avertissement=100, seuil_bloquant=10)


# ---------------------------------------------------------------------------
# Le déclenchement
# ---------------------------------------------------------------------------

def test_sous_le_seuil_rien_ne_se_declenche(tmp_path):
    _fichier(tmp_path, "petit.json", 500)
    constat = evaluer([tmp_path], seuil_avertissement=1000, seuil_bloquant=2000)

    erreurs, avertissements, console, md = rapport(constat)
    assert not erreurs and not avertissements
    assert constat["plus_gros"] is None
    # Pas de conduite à tenir quand il n'y a rien à faire : un contrôle qui
    # récite sa procédure à chaque run cesse d'être lu.
    assert CONDUITE_A_TENIR[0] not in console


def test_entre_les_deux_seuils_avertit_sans_bloquer(tmp_path):
    _fichier(tmp_path, "moyen.json", 1500)
    constat = evaluer([tmp_path], seuil_avertissement=1000, seuil_bloquant=2000)

    erreurs, avertissements, console, md = rapport(constat)
    assert not erreurs
    assert len(avertissements) == 1
    assert "moyen.json" in avertissements[0]
    assert constat["bloquant"] is False


def test_au_dessus_du_seuil_bloquant_echoue(tmp_path):
    _fichier(tmp_path, "enorme.json", 3000)
    constat = evaluer([tmp_path], seuil_avertissement=1000, seuil_bloquant=2000)

    erreurs, avertissements, console, md = rapport(constat)
    assert constat["bloquant"] is True
    assert len(erreurs) == 1
    assert "enorme.json" in erreurs[0]
    # Le message dit de combien on est du refus de push : c'est ce chiffre-là
    # qui décide s'il faut agir maintenant ou au prochain cycle.
    assert "du refus de push" in erreurs[0]


def test_le_constat_nomme_le_fichier_et_son_poids(tmp_path):
    _fichier(tmp_path, "gros.json", 3000)
    _fichier(tmp_path, "petit.json", 10)
    constat = evaluer([tmp_path], seuil_avertissement=1000, seuil_bloquant=2000)

    assert constat["plus_gros"]["chemin"].endswith("gros.json")
    assert constat["plus_gros"]["octets"] == 3000
    _, _, console, md = rapport(constat)
    assert "gros.json" in console and "gros.json" in md


# ---------------------------------------------------------------------------
# La conduite à tenir
# ---------------------------------------------------------------------------

def test_la_conduite_a_tenir_sort_avec_le_constat(tmp_path):
    """C'est ce qui manquait en #429 : le chiffre sans la suite à donner."""
    _fichier(tmp_path, "gros.json", 3000)
    _, _, console, md = rapport(
        evaluer([tmp_path], seuil_avertissement=1000, seuil_bloquant=2000)
    )
    for etape in CONDUITE_A_TENIR:
        assert etape in console
        assert etape in md


def test_la_conduite_a_tenir_interdit_les_deux_fausses_sorties():
    texte = " ".join(CONDUITE_A_TENIR)
    assert "NE PAS relever le seuil" in texte
    assert "NE PAS supprimer de données" in texte
    # Et elle nomme la sortie qui, elle, a été mesurée.
    assert "Partitionner" in texte
    assert "56,0 → 23,4 Mo" in texte


def test_la_conduite_a_tenir_renvoie_a_la_decision_ecrite():
    assert any(gf.REF_DECISION in etape for etape in CONDUITE_A_TENIR)


# ---------------------------------------------------------------------------
# L'inventaire
# ---------------------------------------------------------------------------

def test_inventorier_descend_dans_les_tranches(tmp_path):
    """Les tranches de #580 vivent un niveau plus bas que les socles : un
    garde-fou qui ne ferait qu'un `glob` non récursif ne verrait justement pas
    les fichiers qu'il est censé surveiller."""
    _fichier(tmp_path, "aline.json", 100)
    _fichier(tmp_path, "aline/16.json", 5000)

    blobs = inventorier([tmp_path])
    assert [b.octets for b in blobs] == [5000, 100]
    assert blobs[0].chemin.endswith("aline/16.json")


def test_repertoire_absent_ignore(tmp_path):
    assert inventorier([tmp_path / "nexiste-pas"]) == []


def test_repertoires_surveilles_couvrent_les_couches_versionnees():
    assert "raw_data/profiles" in gf.REPERTOIRES_SURVEILLES
    # `pivot_data/amendements` y est parce que son index `15.json` a été le plus
    # gros blob du dépôt jusqu'au 28/08/2026 : le garde-fou ne surveille pas
    # que les profils bruts.
    assert "pivot_data/amendements" in gf.REPERTOIRES_SURVEILLES


# ---------------------------------------------------------------------------
# Le câblage dans le quality gate : le garde-fou doit VRAIMENT bloquer
# ---------------------------------------------------------------------------

def _lancer_gate(monkeypatch, tmp_path, argv_extra):
    """Lance `check_quality_gate.main()` en NEUTRALISANT les autres sections.

    Depuis un `tmp_path` : les répertoires surveillés par défaut
    (`raw_data/profiles`…) sont absents, donc seuls ceux qu'on passe
    explicitement sont mesurés — le corpus réel n'est jamais lu par la suite de
    tests (#473). Et les quatre autres sections à échec dur sont rendues
    neutres : sans cela, leurs fichiers de configuration manquants feraient
    sortir 1 quoi qu'il arrive, et le test ne prouverait rien sur la §7.
    """
    import sys

    import check_quality_gate as gate

    monkeypatch.setattr(gate, "_report_incomplete_reads", lambda *a, **k: ("", "", 0))
    monkeypatch.setattr(gate, "_report_groupes", lambda *a, **k: ([], [], "", ""))
    monkeypatch.setattr(gate, "_report_lignees", lambda *a, **k: ([], [], "", ""))
    monkeypatch.setattr(gate, "_report_gouvernements", lambda *a, **k: ([], [], "", ""))
    monkeypatch.setattr(gate, "_report_correspondance_acteurs", lambda *a, **k: ([], "", ""))
    monkeypatch.setattr(gate, "_report_amendements_figes_format", lambda *a, **k: ([], "", ""))

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["check_quality_gate.py", *argv_extra])
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    return gate.main()


def _argv(tmp_path, raw, warn_octets, fail_octets):
    mio = 1024 * 1024
    return [
        "--raw-dir", str(raw),
        "--profiles-dir", str(tmp_path / "pivot"),
        "--candidats", str(tmp_path / "candidats.json"),
        "--blob-warn-mo", str(warn_octets / mio),
        "--blob-fail-mo", str(fail_octets / mio),
    ]


def test_le_gate_bloque_le_commit_au_dessus_du_seuil(monkeypatch, tmp_path, capsys):
    """C'est la moitié qui manquait en #429 : le constat sans effet. Ici il a
    un effet — le commit de données ne part pas. Les autres sections étant
    neutralisées, le 1 ne peut venir que de la §7."""
    raw = tmp_path / "raw"
    _fichier(raw, "gros.json", 3000)

    code = _lancer_gate(monkeypatch, tmp_path, _argv(tmp_path, raw, 1000, 2000))

    sortie = capsys.readouterr().out
    assert code == 1
    assert "COMMIT BLOQUÉ" in sortie
    assert "gros.json" in sortie
    assert CONDUITE_A_TENIR[3] in sortie      # « NE PAS relever le seuil »


def test_le_gate_avertit_sans_bloquer_entre_les_deux_seuils(monkeypatch, tmp_path, capsys):
    raw = tmp_path / "raw"
    _fichier(raw, "moyen.json", 1500)

    code = _lancer_gate(monkeypatch, tmp_path, _argv(tmp_path, raw, 1000, 2000))

    sortie = capsys.readouterr().out
    assert code == 0
    assert "COMMIT AUTORISÉ" in sortie
    assert "non bloquant, à traiter" in sortie
    assert "moyen.json" in sortie


def test_la_section_7_peut_etre_desactivee(monkeypatch, tmp_path, capsys):
    raw = tmp_path / "raw"
    _fichier(raw, "gros.json", 3000)

    code = _lancer_gate(monkeypatch, tmp_path, [
        "--raw-dir", str(raw),
        "--profiles-dir", str(tmp_path / "pivot"),
        "--candidats", str(tmp_path / "candidats.json"),
        "--blob-warn-mo", "0",
    ])

    assert code == 0
    assert "GARDE-FOU" not in capsys.readouterr().out
