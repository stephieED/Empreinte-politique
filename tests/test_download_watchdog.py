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
