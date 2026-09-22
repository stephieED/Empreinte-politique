"""#1100 — la reprise d'une archive figée se borne en TEMPS, pas en cycles.

`data.assemblee-nationale.fr` ne tombe pas : il coupe par intermittence.
Remesuré le 22/09/2026 sur la plage qui avait fait échouer le run 35767700159
(offset 12 224 778, 4 194 192 octets) : 722 945 octets à la première tentative,
2 892 049 à la deuxième, la plage entière à la troisième. En CI, trois cycles de
trois tentatives ont abandonné après 5 minutes sur un job qui en a 30.

Le faux serveur ci-dessous reproduit ce comportement — il coupe un nombre donné
de fois, puis sert la suite —, et le téléchargeur est le vrai.
"""
from __future__ import annotations

import http.server
import sys
import threading
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))

import build_amendements_index as bai  # noqa: E402
import candidate_profile as cp  # noqa: E402

WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"
CORPS = bytes(range(256)) * 400  # 102 400 octets, contenu vérifiable


class _SourceQuiCoupe(http.server.BaseHTTPRequestHandler):
    """Sert `CORPS`, mais coupe la connexion les `coupures` premières fois.

    La coupure reproduit ce que fait le CDN de l'AN d'après le code appelé :
    en-têtes corrects — 200 ou 206, `Content-Length` de la taille attendue — puis
    zéro octet. Le nombre de tentatives par segment est laissé à son défaut dans
    les deux tests d'abandon : réduit à 1, la reprise ne passe pas par l'état 3
    et rien ne serait mesuré du budget.
    """

    coupures = 0
    servies = 0

    def log_message(self, *args):  # pragma: no cover - silence du serveur de test
        pass

    def _debut(self) -> int:
        plage = self.headers.get("Range")
        if not plage:
            return 0
        return int(plage.split("=")[1].split("-")[0])

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Length", str(len(CORPS)))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("ETag", '"essai-1100"')
        self.end_headers()

    def do_GET(self):
        type(self).servies += 1
        debut = self._debut()
        reste = CORPS[debut:]
        partiel = type(self).servies <= type(self).coupures
        if debut:
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {debut}-{len(CORPS) - 1}/{len(CORPS)}")
        else:
            self.send_response(200)
        self.send_header("Content-Length", str(len(reste)))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("ETag", '"essai-1100"')
        self.end_headers()
        # Une coupure : on annonce la taille entière et on n'envoie rien, ce que
        # fait le CDN de l'AN (206 + Content-Range correct, zéro octet).
        if not partiel:
            self.wfile.write(reste)


@pytest.fixture(autouse=True)
def sans_attente_entre_tentatives(monkeypatch):
    """Le backoff de 5 s entre deux tentatives de segment est réel et utile en
    production ; ici il ne mesurerait que la patience de la suite."""
    monkeypatch.setattr(cp, "AMENDEMENTS_DOWNLOAD_BACKOFF_SECONDS", 0)


@pytest.fixture
def source(request):
    """Un serveur local qui coupe `coupures` fois avant de servir."""
    _SourceQuiCoupe.coupures = getattr(request, "param", 0)
    _SourceQuiCoupe.servies = 0
    serveur = http.server.HTTPServer(("127.0.0.1", 0), _SourceQuiCoupe)
    fil = threading.Thread(target=serveur.serve_forever, daemon=True)
    fil.start()
    yield f"http://127.0.0.1:{serveur.server_port}/amendements.zip"
    serveur.shutdown()
    serveur.server_close()


@pytest.mark.parametrize("source", [4], indirect=True)
def test_la_reprise_continue_tant_qu_il_reste_du_budget(source, tmp_path):
    zip_path = tmp_path / "amendements.zip"

    cp._download_amendements_zip(source, zip_path, "14", stall_wait_seconds=0,
                                 max_attempts=1, budget_secondes=30)

    assert zip_path.read_bytes() == CORPS, "l'archive est complète après les coupures"


@pytest.mark.parametrize("source", [99], indirect=True)
def test_le_budget_epuise_nomme_les_octets_obtenus_et_le_temps(source, tmp_path):
    """Le message d'abandon disait « la source semble indisponible » — c'est
    cette phrase qui a fait conclure à tort à une panne le 22/09/2026."""
    with pytest.raises(cp.SourceAmendementsIndisponibleError) as erreur:
        cp._download_amendements_zip(source, tmp_path / "amendements.zip", "14",
                                     stall_wait_seconds=0, budget_secondes=0)

    message = str(erreur.value)
    assert "0 octet(s) obtenu(s) sur 102400" in message and "budget de" in message
    assert "épuisé" in message
    assert "COUPE par intermittence" in message


@pytest.mark.parametrize("source", [99], indirect=True)
def test_sans_budget_le_compte_de_cycles_borne_encore(source, tmp_path):
    """Hors CI, `budget_secondes` est absent : le comportement d'avant #1100
    reste, parce qu'attendre longtemps y est le seul remède qui marche."""
    with pytest.raises(cp.SourceAmendementsIndisponibleError) as erreur:
        cp._download_amendements_zip(source, tmp_path / "amendements.zip", "14",
                                     stall_wait_seconds=0, stall_max_cycles=2)

    assert "cycle(s) sans progrès" in str(erreur.value)


def test_le_budget_vient_du_temps_restant_du_job(monkeypatch):
    monkeypatch.setenv("JOB_START_EPOCH", "1000")

    # 6 minutes après le début du job : 30 min de plafond, 7 min de marge.
    assert bai.budget_telechargement_secondes(1000 + 360) == pytest.approx(
        30 * 60 - bai.MARGE_APRES_TELECHARGEMENT_SECONDES - 360)
    # 27 minutes après : il ne reste plus rien, le téléchargement n'est pas tenté.
    assert bai.budget_telechargement_secondes(1000 + 27 * 60) == 0.0


def test_sans_job_start_epoch_il_n_y_a_pas_de_borne(monkeypatch):
    monkeypatch.delenv("JOB_START_EPOCH", raising=False)

    assert bai.budget_telechargement_secondes() is None


def test_le_plafond_recopie_est_celui_du_yaml():
    """La constante est une copie : le YAML est lu sur le dépôt public et se
    publie à la main, donc il ne peut pas être la source à l'exécution. Ce test
    est ce qui empêche les deux de divulguer."""
    lignes = WORKFLOW.read_text(encoding="utf-8").splitlines()
    debut = next(i for i, l in enumerate(lignes) if l.startswith("  extract-amendements-an:"))
    plafond = next(int(l.split(":")[1]) for l in lignes[debut:debut + 12]
                   if l.strip().startswith("timeout-minutes:"))

    assert bai.JOB_TIMEOUT_MINUTES == plafond
