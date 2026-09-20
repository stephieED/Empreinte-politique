"""Tests for issue #128 — Aperçu panel scaffold in web/v3."""
from pathlib import Path

ROOT = Path(__file__).parents[1]
CONFIG_JS = (ROOT / "web" / "old" / "v3" / "js" / "config.js").read_text(encoding="utf-8")
APP_JS = (ROOT / "web" / "old" / "v3" / "js" / "app.js").read_text(encoding="utf-8")
RENDER_JS = (ROOT / "web" / "old" / "v3" / "js" / "render.js").read_text(encoding="utf-8")
CSS = (ROOT / "web" / "old" / "v3" / "design-tokens.css").read_text(encoding="utf-8")


def test_apercu_in_panel_order():
    assert '"apercu"' in CONFIG_JS
    assert 'PANEL_ORDER = ["apercu"' in CONFIG_JS


def test_apercu_panel_meta():
    assert 'apercu: { label: "Aperçu"' in CONFIG_JS


def test_panel_order_has_seven_panels():
    # Extract the PANEL_ORDER array literal
    import re
    m = re.search(r'PANEL_ORDER\s*=\s*\[([^\]]+)\]', CONFIG_JS)
    assert m, "PANEL_ORDER not found"
    entries = [e.strip().strip('"') for e in m.group(1).split(",") if e.strip()]
    assert len(entries) == 7
    assert entries[0] == "apercu"


def test_apercu_state_fields_in_app():
    assert "apercuView" in APP_JS
    assert "apercuFilter" in APP_JS


def test_apercu_state_reset_on_select_candidate():
    # After selectCandidate the state resets apercuView and apercuFilter
    assert 'state.apercuView = "synthese"' in APP_JS
    assert 'state.apercuFilter = "all"' in APP_JS


def test_apercu_event_bindings_in_app():
    assert "[data-apercu-view]" in APP_JS
    assert "[data-apercu-filter]" in APP_JS


def test_render_apercu_function_exists():
    assert "export function renderApercu" in RENDER_JS


def test_render_apercu_wired_in_render_page():
    assert "renderApercu(profile, state)" in RENDER_JS


def test_panel_indicator_grid_supports_seven():
    assert "repeat(7, 1fr)" in CSS
