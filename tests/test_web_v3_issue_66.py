from pathlib import Path


ROOT = Path(__file__).parents[1]
RENDER_JS = (ROOT / "web" / "old" / "v3" / "js" / "render.js").read_text(encoding="utf-8")
CSS = (ROOT / "web" / "old" / "v3" / "design-tokens.css").read_text(encoding="utf-8")


def test_mandate_legend_and_role_tones_present():
    assert "export function mandateRoleTone" in RENDER_JS
    assert "renderMandateLegend" in RENDER_JS
    assert "Mandat actif" in RENDER_JS
    assert ".deconstructed .mandate-legend" in CSS
    assert ".deconstructed .mandate-live-tag" in CSS


def test_textes_view_has_four_scope_bars_and_scroll_layout():
    assert "Activité ministérielle" in RENDER_JS
    assert 'scope: "gouvernement"' in RENDER_JS
    assert "Les amendements ne sont pas classés par activité ministérielle" in RENDER_JS
    assert "legislative-layout" in RENDER_JS
    assert ".legislative-scroll-frame" in CSS
    assert ".scope-bar-row" in CSS
