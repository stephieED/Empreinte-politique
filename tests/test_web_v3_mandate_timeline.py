import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
RENDER_JS = ROOT / "web" / "old" / "v3" / "js" / "render.js"
APP_JS = ROOT / "web" / "old" / "v3" / "js" / "app.js"
CSS = ROOT / "web" / "old" / "v3" / "design-tokens.css"


class MandateTimelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.render_js = RENDER_JS.read_text(encoding="utf-8")
        cls.app_js = APP_JS.read_text(encoding="utf-8")
        cls.css = CSS.read_text(encoding="utf-8")

    def run_builder(self, mandates):
        start = self.render_js.index("export function buildMandateTimeline(profile) {")
        end = self.render_js.index("\n\nexport function renderMandateTimeline(profile", start)
        function_source = self.render_js[start:end].replace("export function", "function", 1)
        script = f"""
        function toDateMs(value) {{ return value ? new Date(value).getTime() : 0; }}
        {function_source}
        process.stdout.write(JSON.stringify(buildMandateTimeline({{
          pivot_mandats: {json.dumps(mandates)}
        }})));
        """
        result = subprocess.run(
            ["node", "-e", script],
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(result.stdout)

    def test_builder_only_merges_truly_contiguous_periods(self):
        mandates = [
            {
                "label": "Commission A",
                "categorie": "commission",
                "fonction": "membre",
                "debut": "2023-01-01",
                "fin": "2023-01-31",
                "actif": False,
                "source_url": "https://example.test/1",
            },
            {
                "label": "Commission A",
                "categorie": "commission",
                "fonction": "membre",
                "debut": "2023-02-01",
                "fin": "2023-02-28",
                "actif": False,
                "source_url": "https://example.test/2",
            },
            {
                "label": "Commission A",
                "categorie": "commission",
                "fonction": "membre",
                "debut": "2023-03-02",
                "fin": "2023-03-31",
                "actif": False,
                "source_url": "javascript:alert(1)",
            },
            {
                "label": "Mandat récent",
                "categorie": "mandat_electif",
                "fonction": "député",
                "debut": "2024-01-01",
                "fin": None,
                "actif": True,
                "source_url": None,
            },
            {
                "label": "Date inconnue",
                "categorie": "commission",
                "fonction": "membre",
                "debut": None,
                "fin": None,
                "actif": True,
                "source_url": None,
            },
        ]

        result = self.run_builder(mandates)

        self.assertEqual([item["label"] for item in result], [
            "Mandat récent", "Commission A", "Commission A", "Date inconnue",
        ])
        self.assertEqual(result[1]["debut"], "2023-03-02")
        self.assertEqual(result[2]["debut"], "2023-01-01")
        self.assertEqual(result[2]["fin"], "2023-02-28")
        self.assertEqual(result[2]["sourceUrls"], [
            "https://example.test/1", "https://example.test/2",
        ])
        self.assertEqual(result[1]["sourceUrls"], [])

    def test_primary_view_and_mobile_layout_are_explicit(self):
        self.assertIn('mandateView: "timeline"', self.app_js)
        self.assertIn("<h2>Mandats documentés", self.render_js)
        self.assertIn('["timeline", "Chronologie"], ["responsibilities", "Responsabilités"]', self.render_js)
        self.assertIn('["all", "Tous"], ["elective", "Électifs"], ["responsibilities", "Responsabilités"], ["groups", "Groupes"]', self.render_js)
        self.assertIn("grid-template-columns: 56px minmax(0, 1fr)", self.css)
        self.assertIn('"date non renseignée"', self.render_js)


if __name__ == "__main__":
    unittest.main()
