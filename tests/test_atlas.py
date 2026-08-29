import tempfile
from pathlib import Path
import unittest
from unittest import mock

import atlas


class AtlasValidationTests(unittest.TestCase):
    def test_public_collection_is_valid(self):
        self.assertEqual([], atlas.validate())

    def test_public_collection_passes_safety_scan(self):
        self.assertEqual([], atlas.safety_scan())

    def test_safety_scan_finds_private_markers_and_secrets(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "unsafe.md").write_text(
                "internal " + "corp." + "internal path and " + "sk-" + "abcdefghijklmnopqrstuvwxyz123456",
                encoding="utf-8",
            )
            with mock.patch.object(atlas, "ROOT", root):
                findings = atlas.safety_scan()
        self.assertTrue(any("private-topology marker" in finding for finding in findings))
        self.assertTrue(any("possible secret" in finding for finding in findings))

    def test_ids_and_slugs_are_unique(self):
        patterns = atlas.load_patterns()
        ids = [pattern["metadata"]["id"] for pattern in patterns]
        slugs = [pattern["metadata"]["slug"] for pattern in patterns]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(slugs), len(set(slugs)))


class FixtureTests(unittest.TestCase):
    def test_every_mode_returns_evidence(self):
        results = atlas.run()
        self.assertEqual(len(atlas.load_patterns()) * 3, len(results))
        for result in results:
            self.assertEqual("pass", result["status"])
            self.assertTrue(result["evidence"])

    def test_unknown_pattern_is_rejected(self):
        with self.assertRaisesRegex(atlas.AtlasError, "unknown pattern"):
            atlas.run("FFA-999")

    def test_timeout_is_release_blocking(self):
        pattern = atlas.load_patterns()[0]
        with mock.patch.object(atlas.subprocess, "run", side_effect=atlas.subprocess.TimeoutExpired("fixture", 5)):
            with self.assertRaisesRegex(atlas.AtlasError, "exceeded"):
                atlas.run_fixture(pattern, "reproduce")


class SiteTests(unittest.TestCase):
    def test_checked_in_site_is_current(self):
        self.assertEqual([], atlas.build_site(check=True))

    def test_site_generation_has_one_page_per_pattern(self):
        files = atlas.site_files()
        pattern_pages = [path for path in files if path.parts[0] == "patterns"]
        self.assertEqual(len(atlas.load_patterns()), len(pattern_pages))
        self.assertIn(Path("index.html"), files)
        self.assertIn(Path("atlas.json"), files)

    def test_renderer_joins_wrapped_prose_and_keeps_safe_markup(self):
        rendered = atlas._render_markdown("A wrapped\nparagraph with **proof**.\n")
        self.assertEqual("<p>A wrapped paragraph with <strong>proof</strong>.</p>", rendered)


if __name__ == "__main__":
    unittest.main()
