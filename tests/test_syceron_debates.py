import io
import sys
import zipfile
from pathlib import Path
from unittest.mock import patch

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from syceron_debates import (
    SYCERON_ZIP_NAME,
    ensure_syceron_downloaded,
    iter_syceron_xml_files,
)


def _make_syceron_zip(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buf.getvalue()


class DummyStreamResponse:
    def __init__(self, content: bytes, status_code: int = 200):
        self.content = content
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def iter_content(self, chunk_size: int = 1024 * 1024):
        for start in range(0, len(self.content), chunk_size):
            yield self.content[start:start + chunk_size]

    # download_with_watchdog (#370) utilise `with requests.get(...) as resp:`.
    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


def test_ensure_syceron_downloaded_from_local_zip(tmp_path):
    local_zip = tmp_path / "local-syceron.zip"
    local_zip.write_bytes(_make_syceron_zip({
        "xml/compteRendu/CRSANR5L15S001.xml": "<compteRendu/>",
    }))
    cache_dir = tmp_path / "cache"

    with patch("syceron_debates.SYCERON_CACHE_DIR", cache_dir):
        xml_dir = ensure_syceron_downloaded("15", local_zip_path=local_zip)

    assert xml_dir == cache_dir / "15" / "xml" / "compteRendu"
    assert (xml_dir / "CRSANR5L15S001.xml").is_file()
    assert (cache_dir / "15" / SYCERON_ZIP_NAME).is_file()


def test_ensure_syceron_downloaded_returns_none_for_unavailable_legislature(tmp_path):
    with patch("syceron_debates.SYCERON_CACHE_DIR", tmp_path / "cache"), \
         patch("syceron_debates.requests.get") as mock_get:
        xml_dir = ensure_syceron_downloaded("14")

    assert xml_dir is None
    mock_get.assert_not_called()


def test_ensure_syceron_downloaded_downloads_once_then_reuses_cache(tmp_path):
    zip_bytes = _make_syceron_zip({
        "xml/compteRendu/CRSANR5L17S001.xml": "<compteRendu/>",
    })
    cache_dir = tmp_path / "cache"

    with patch("syceron_debates.SYCERON_CACHE_DIR", cache_dir), \
         patch("syceron_debates.requests.get", return_value=DummyStreamResponse(zip_bytes)) as mock_get:
        first = ensure_syceron_downloaded("17")
        second = ensure_syceron_downloaded("17")

    assert first == second == cache_dir / "17" / "xml" / "compteRendu"
    assert (first / "CRSANR5L17S001.xml").is_file()
    assert mock_get.call_count == 1


def test_ensure_syceron_downloaded_returns_none_on_remote_404(tmp_path):
    cache_dir = tmp_path / "cache"

    with patch("syceron_debates.SYCERON_CACHE_DIR", cache_dir), \
         patch(
             "syceron_debates.requests.get",
             return_value=DummyStreamResponse(b"", status_code=404),
         ):
        xml_dir = ensure_syceron_downloaded("16", force_download=True)

    assert xml_dir is None
    assert not (cache_dir / "16" / "xml" / "compteRendu").exists()


def test_iter_syceron_xml_files_returns_empty_iterator_when_dataset_absent(tmp_path):
    with patch("syceron_debates.SYCERON_CACHE_DIR", tmp_path / "cache"):
        files = list(iter_syceron_xml_files("13"))

    assert files == []
