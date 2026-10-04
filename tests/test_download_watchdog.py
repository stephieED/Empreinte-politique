"""Tests pour download_watchdog.download_with_watchdog (#370)."""

import sys
import time as _time
from pathlib import Path
from unittest.mock import patch

import pytest

# Les modules testés vivent dans src/, à côté du dossier tests/.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from download_watchdog import download_with_watchdog


def test_download_with_watchdog_aborts_hung_request(tmp_path):
    """Un téléchargement qui pend au-delà du budget mur lève TimeoutError au
    lieu de bloquer indéfiniment, et n'écrit jamais dest_path — même principe
    que le watchdog de _get_payload (candidate_profile.py), généralisé aux
    téléchargements de fichier."""

    def hung_get(*args, **kwargs):
        _time.sleep(5)
        raise AssertionError("ne devrait jamais retourner : le watchdog doit abandonner avant")

    dest = tmp_path / "dump.zip"

    with patch("download_watchdog.requests.get", side_effect=hung_get):
        start = _time.monotonic()
        with pytest.raises(TimeoutError):
            download_with_watchdog(
                "https://example.test/hung.zip", dest, headers={}, timeout=0.1, hard_timeout_seconds=0.2
            )
        elapsed = _time.monotonic() - start

    assert elapsed < 5
    assert not dest.exists()


def test_download_with_watchdog_writes_dest_path_on_success(tmp_path):
    """En cas de succès, le fichier temporaire est renommé vers dest_path
    (pas de fichier .part résiduel, contenu complet écrit)."""

    class FakeResp:
        status_code = 200

        def raise_for_status(self):
            pass

        def iter_content(self, chunk_size):
            yield b"contenu-du-fichier"

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    dest = tmp_path / "dump.zip"

    with patch("download_watchdog.requests.get", return_value=FakeResp()):
        download_with_watchdog("https://example.test/ok.zip", dest, headers={}, timeout=15)

    assert dest.read_bytes() == b"contenu-du-fichier"
    assert not dest.with_name(dest.name + ".part").exists()


def test_download_with_watchdog_propagates_request_exception(tmp_path):
    """Une erreur réseau normale (pas un blocage) est relayée telle quelle,
    pas transformée en TimeoutError."""
    import requests

    dest = tmp_path / "dump.zip"

    with patch("download_watchdog.requests.get", side_effect=requests.ConnectionError("boom")):
        with pytest.raises(requests.ConnectionError):
            download_with_watchdog("https://example.test/error.zip", dest, headers={}, timeout=15)

    assert not dest.exists()


# ---------------------------------------------------------------------------
# #1202 — reprise d'un transfert coupé en cours de route
# ---------------------------------------------------------------------------
#
# Le run `37200491118` (04/10/2026) a vu l'archive Syceron de la XVe rompue dans
# dix jobs sur dix, après 2 à 40 Mo sur 149 : « Connection broken:
# IncompleteRead(22066130 bytes read, 126888739 more expected) ». Le faux serveur
# ci-dessous RESPECTE l'en-tête `Range` qu'il reçoit — un faux qui l'ignorerait
# rendrait les tests verts quel que soit le code.

import requests as _requests

CONTENU = bytes(range(256)) * 40          # 10 240 octets, non répétitifs par bloc


class _Serveur:
    """Sert `CONTENU`, coupe aux essais demandés, honore ou non `Range`."""

    def __init__(self, coupures, *, honore_range=True, annonce=True):
        self.coupures = list(coupures)    # octets servis avant rupture, par essai
        self.honore_range = honore_range
        self.annonce = annonce
        self.ranges = []

    def get(self, url, *, headers, timeout, stream):
        plage = headers.get("Range")
        self.ranges.append(plage)
        debut = int(plage[len("bytes="):-1]) if plage and self.honore_range else 0
        coupe = self.coupures.pop(0) if self.coupures else None
        return _Reponse(debut, coupe, partiel=bool(plage and self.honore_range),
                        annonce=self.annonce)


class _Reponse:
    def __init__(self, debut, coupe, *, partiel, annonce):
        self.debut, self.coupe = debut, coupe
        self.status_code = 206 if partiel else 200
        self.headers = {}
        if annonce:
            self.headers["Content-Length"] = str(len(CONTENU) - debut)
        if partiel:
            self.headers["Content-Range"] = f"bytes {debut}-{len(CONTENU) - 1}/{len(CONTENU)}"

    def raise_for_status(self):
        pass

    def iter_content(self, chunk_size):
        reste = CONTENU[self.debut:]
        if self.coupe is None:
            yield reste
            return
        yield reste[:self.coupe]
        raise _requests.exceptions.ChunkedEncodingError("Connection broken: IncompleteRead")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def _telecharger(serveur, dest, **kwargs):
    with patch("download_watchdog.requests.get", side_effect=serveur.get):
        download_with_watchdog("https://example.test/a.zip", dest, headers={"User-Agent": "t"},
                               timeout=15, **kwargs)


def test_un_transfert_coupe_reprend_la_ou_il_s_est_arrete(tmp_path):
    serveur = _Serveur([3000, 2500])       # deux coupures, puis la fin
    dest = tmp_path / "a.zip"
    _telecharger(serveur, dest, reprises=8)
    assert dest.read_bytes() == CONTENU
    assert serveur.ranges == [None, "bytes=3000-", "bytes=5500-"]
    assert not dest.with_name("a.zip.part").exists()


def test_sans_reprise_la_coupure_reste_une_erreur(tmp_path):
    """Le défaut des appelants existants ne change pas."""
    serveur = _Serveur([3000])
    dest = tmp_path / "a.zip"
    with pytest.raises(_requests.exceptions.ChunkedEncodingError):
        _telecharger(serveur, dest)
    assert not dest.exists()
    assert serveur.ranges == [None]


def test_les_reprises_sont_bornees(tmp_path):
    serveur = _Serveur([100] * 10)
    dest = tmp_path / "a.zip"
    with pytest.raises(_requests.exceptions.ChunkedEncodingError):
        _telecharger(serveur, dest, reprises=2)
    assert len(serveur.ranges) == 3        # l'essai initial et deux reprises
    assert not dest.exists()


def test_un_serveur_qui_ignore_range_fait_repartir_de_zero(tmp_path):
    """Une réponse `200` à une requête `Range` porte le fichier ENTIER : l'ajouter
    à ce qui est déjà écrit publierait une archive corrompue."""
    serveur = _Serveur([3000], honore_range=False)
    dest = tmp_path / "a.zip"
    _telecharger(serveur, dest, reprises=8)
    assert dest.read_bytes() == CONTENU


def test_un_fichier_plus_court_qu_annonce_n_est_pas_publie(tmp_path):
    """Un transfert qui se termine sans erreur mais sans tous ses octets."""

    class _Tronque(_Serveur):
        def get(self, url, *, headers, timeout, stream):
            reponse = super().get(url, headers=headers, timeout=timeout, stream=stream)
            reponse.iter_content = lambda chunk_size: iter([CONTENU[:4000]])
            return reponse

    dest = tmp_path / "a.zip"
    with pytest.raises(_requests.exceptions.ChunkedEncodingError):
        _telecharger(_Tronque([]), dest, reprises=1)
    assert not dest.exists()


def test_syceron_demande_des_reprises():
    import syceron_debates

    assert syceron_debates.SYCERON_REPRISES_TELECHARGEMENT >= 1
