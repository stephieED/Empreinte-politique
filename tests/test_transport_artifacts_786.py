"""Une panne de transport ne doit plus se lire comme une source absente (#786).

Ce que ces tests tiennent, c'est la **distinction**, pas la mécanique de
téléchargement. Chacun correspond à un état du monde que le run `34241352524` a
confondu avec un autre :

- le run n'a rien publié → silence, comme avant ;
- le run a publié et tout est arrivé → rien à dire ;
- le run a publié et rien n'est arrivé → panne, rattrapage puis échec ;
- l'API ne répond pas → on ne sait pas, et on ne fabrique pas de constat.
"""

import subprocess
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

import verifier_transport_artifacts as transport  # noqa: E402


def _reponse(code=0, sortie=""):
    return subprocess.CompletedProcess(args=[], returncode=code, stdout=sortie, stderr="")


class Faux:
    """Un exécuteur qui répond à `gh api` puis à `gh run download`."""

    def __init__(self, noms=None, api_ok=True, download_ok=True, depose=None):
        self.noms = noms or []
        self.api_ok = api_ok
        self.download_ok = download_ok
        self.depose = depose or []
        self.appels = []

    def __call__(self, commande):
        self.appels.append(list(commande))
        if commande[1] == "api":
            if not self.api_ok:
                return _reponse(1)
            return _reponse(0, "\n".join(self.noms))
        # gh run download --dir <tampon>
        tampon = Path(commande[commande.index("--dir") + 1])
        if not self.download_ok:
            return _reponse(1)
        for nom in self.depose:
            cible = tampon / "un-artifact" / nom
            cible.parent.mkdir(parents=True, exist_ok=True)
            cible.write_text("{}", encoding="utf-8")
        return _reponse(0)


UNE_SOURCE = transport.Source(
    "AN", "raw-profiles-an-", "", shards=True, bloquant=True
)


def _source(repertoire, **kwargs):
    champs = dict(
        libelle="AN",
        prefixe="raw-profiles-an-",
        repertoire=str(repertoire),
        shards=True,
        bloquant=True,
    )
    champs.update(kwargs)
    return transport.Source(**champs)


# ---------------------------------------------------------------------------
# Reconnaître les artifacts d'une source
# ---------------------------------------------------------------------------


def test_une_source_shardee_reconnait_ses_shards():
    an = UNE_SOURCE
    assert an.reconnait("raw-profiles-an-marine-le-pen")
    assert not an.reconnait("raw-profiles-roster-groupes-3")
    assert an.motif == "raw-profiles-an-*"


def test_une_source_unique_exige_le_nom_exact():
    """`raw-profiles-ue-officiel` ne doit pas attraper un homonyme préfixé."""
    ue = transport.Source("UE", "raw-profiles-ue-officiel", "", shards=False, bloquant=True)
    assert ue.reconnait("raw-profiles-ue-officiel")
    assert not ue.reconnait("raw-profiles-ue-officiel-bis")
    assert ue.motif == "raw-profiles-ue-officiel"


def test_les_quatre_sources_du_workflow_sont_couvertes():
    libelles = {s.libelle for s in transport.SOURCES}
    assert libelles == {"AN", "UE", "ParlTrack", "roster"}
    bloquantes = {s.libelle for s in transport.SOURCES if s.bloquant}
    assert bloquantes == {"AN", "UE", "roster"}, (
        "ParlTrack a un repli déclaré que le portail §5 mesure : le rendre "
        "bloquant ferait échouer un run pour une dégradation déjà publiée."
    )


# ---------------------------------------------------------------------------
# Les quatre états du monde
# ---------------------------------------------------------------------------


def test_rien_de_publie_reste_silencieux(tmp_path, capsys):
    """Une source qui n'a rien produit n'est pas une panne (#412 §2.1)."""
    faux = Faux(noms=["parltrack-dumps"])
    code = transport.controler([_source(tmp_path / "an")], "d/r", "1", faux, lambda _: None)
    assert code == 0
    sortie = capsys.readouterr().out
    assert "aucun artifact publié" in sortie
    assert "::error::" not in sortie
    assert not any(a[1] == "run" for a in faux.appels), "rien à rattraper"


def test_publie_et_arrive_ne_declenche_rien(tmp_path, capsys):
    repertoire = tmp_path / "an"
    repertoire.mkdir()
    (repertoire / "marine-le-pen.json").write_text("{}", encoding="utf-8")
    faux = Faux(noms=["raw-profiles-an-marine-le-pen"])
    code = transport.controler([_source(repertoire)], "d/r", "1", faux, lambda _: None)
    assert code == 0
    assert "::error::" not in capsys.readouterr().out
    assert not any(a[1] == "run" for a in faux.appels)


def test_publie_et_non_arrive_est_rattrape(tmp_path, capsys):
    repertoire = tmp_path / "an"
    faux = Faux(noms=["raw-profiles-an-marine-le-pen"], depose=["marine-le-pen.json"])
    code = transport.controler([_source(repertoire)], "d/r", "1", faux, lambda _: None)
    assert code == 0
    sortie = capsys.readouterr().out
    assert "TRANSPORT_ARTIFACTS_RATTRAPAGE" in sortie
    assert "::error::" not in sortie
    assert (repertoire / "marine-le-pen.json").is_file(), (
        "gh range chaque artifact dans son dossier ; sans recollement à plat, "
        "`merge_raw_dirs` ne verrait rien"
    )


def test_publie_non_arrive_et_non_rattrapable_fait_echouer(tmp_path, capsys):
    """C'est le run `34241352524` : 636 profils qui n'atteignent pas la fusion."""
    faux = Faux(noms=["raw-profiles-an-marine-le-pen"], download_ok=False)
    code = transport.controler(
        [_source(tmp_path / "an")], "d/r", "1", faux, lambda _: None
    )
    assert code == 1
    sortie = capsys.readouterr().out
    assert "::error::TRANSPORT_ARTIFACTS_PERDUS" in sortie
    tentatives = [a for a in faux.appels if a[1] == "run"]
    assert len(tentatives) == transport.TENTATIVES


def test_une_source_non_bloquante_avertit_sans_faire_echouer(tmp_path, capsys):
    faux = Faux(noms=["parltrack-dumps"], download_ok=False)
    source = _source(
        tmp_path / "pt", libelle="ParlTrack", prefixe="parltrack-dumps",
        shards=False, bloquant=False,
    )
    code = transport.controler([source], "d/r", "1", faux, lambda _: None)
    assert code == 0
    sortie = capsys.readouterr().out
    assert "TRANSPORT_ARTIFACTS_PERDUS" in sortie
    assert "::error::" not in sortie


def test_un_inventaire_illisible_ne_fabrique_pas_de_constat(tmp_path, capsys):
    """« Je ne peux pas vérifier » n'est pas « il n'y a rien » (§2 règle 5)."""
    faux = Faux(api_ok=False)
    code = transport.controler(
        [_source(tmp_path / "an")], "d/r", "1", faux, lambda _: None
    )
    assert code == 0
    sortie = capsys.readouterr().out
    assert "TRANSPORT_INVENTAIRE_INDISPONIBLE" in sortie
    assert "::error::" not in sortie
    assert not any(a[1] == "run" for a in faux.appels)


def test_un_artifact_expire_ne_compte_pas_comme_publie():
    """Le filtre vit dans la requête ; ce test le fige à cet endroit."""
    faux = Faux(noms=[])
    transport.inventaire("d/r", "1", faux)
    requete = " ".join(faux.appels[0])
    assert "select(.expired == false)" in requete


# ---------------------------------------------------------------------------
# Le recollement à plat
# ---------------------------------------------------------------------------


def test_aplatir_recolle_les_sous_repertoires(tmp_path):
    source = tmp_path / "tampon"
    (source / "artifact-a").mkdir(parents=True)
    (source / "artifact-b").mkdir(parents=True)
    (source / "artifact-a" / "un.json").write_text("1", encoding="utf-8")
    (source / "artifact-b" / "deux.json").write_text("2", encoding="utf-8")
    poses = transport.aplatir(source, tmp_path / "cible")
    assert poses == 2
    assert sorted(p.name for p in (tmp_path / "cible").iterdir()) == [
        "deux.json",
        "un.json",
    ]


def test_fichiers_compte_a_toute_profondeur(tmp_path):
    assert transport.fichiers(tmp_path / "absent") == 0
    (tmp_path / "a" / "b").mkdir(parents=True)
    (tmp_path / "a" / "b" / "x.json").write_text("{}", encoding="utf-8")
    assert transport.fichiers(tmp_path) == 1


# ---------------------------------------------------------------------------
# Sa place dans le workflow
# ---------------------------------------------------------------------------


WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"


def _lignes_sans_commentaires():
    return [
        ligne
        for ligne in WORKFLOW.read_text(encoding="utf-8").splitlines()
        if not ligne.lstrip().startswith("#")
    ]


def _indice(aiguille):
    for i, ligne in enumerate(_lignes_sans_commentaires()):
        if aiguille in ligne:
            return i
    raise AssertionError(f"introuvable dans le workflow : {aiguille!r}")


def test_le_controle_suit_les_telechargements_et_precede_la_fusion():
    """Avant, il n'aurait rien à constater ; après, la fusion aurait déjà menti."""
    assert _indice("path: _artifacts/roster") < _indice(
        "src/verifier_transport_artifacts.py"
    ) < _indice("src/merge_profile.py")


def test_le_controle_recoit_un_token():
    """Sans lui, `gh api` échoue et l'inventaire est réputé illisible à chaque run."""
    lignes = _lignes_sans_commentaires()
    debut = _indice("src/verifier_transport_artifacts.py")
    entete = "\n".join(lignes[max(0, debut - 6): debut + 1])
    assert "GH_TOKEN" in entete


def test_le_jeton_du_run_ne_sert_jamais_a_pousser():
    """L'autre moitié du garde-fou #508, que le décompte des `secrets.` ne voit
    pas.

    Ce job pousse sous UNE identité, la clé de déploiement, seule que le
    ruleset puisse exempter. Le jeton du run est admis ici pour lire
    l'inventaire des artifacts — jamais pour pousser, jamais dans un checkout.
    """
    import re

    bloc = "\n".join(_lignes_sans_commentaires())
    debut = bloc.index("\n  merge-and-pivot:")
    suite = re.search(r"^  [a-z][a-z0-9-]*:\s*$", bloc[debut + 20:], flags=re.MULTILINE)
    job = bloc[debut: debut + 20 + suite.start()] if suite else bloc[debut:]
    usages = re.findall(r"^\s*(\S+):\s*\$\{\{\s*github\.token\s*\}\}", job, re.MULTILINE)
    assert set(usages) == {"GH_TOKEN"}, (
        f"`github.token` ne doit servir qu'à `GH_TOKEN` dans ce job ; trouvé : {sorted(set(usages))}"
    )
    assert len(usages) == 2, (
        "deux usages attendus : le déclenchement de deploy-pages (#416) et la "
        f"lecture de l'inventaire des artifacts (#786) ; trouvés : {len(usages)}"
    )
