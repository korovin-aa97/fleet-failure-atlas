import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import cast
from unittest import mock

import atlas


class AtlasValidationTests(unittest.TestCase):
    def test_public_collection_is_valid(self) -> None:
        self.assertEqual([], atlas.validate())

    def test_public_collection_passes_safety_scan(self) -> None:
        self.assertEqual([], atlas.safety_scan())

    def test_safety_scan_finds_private_markers_secrets_and_user_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "unsafe.txt").write_text(
                "corp."
                + "internal "
                + "sk-"
                + "abcdefghijklmnopqrstuvwxyz123456 /ho"
                + "me/example/project",
                encoding="utf-8",
            )
            with mock.patch.object(atlas, "ROOT", root):
                findings = atlas.safety_scan()
        self.assertTrue(any("private-topology marker" in finding for finding in findings))
        self.assertTrue(any("possible secret" in finding for finding in findings))
        self.assertTrue(any("absolute user path" in finding for finding in findings))

    def test_ids_and_slugs_are_unique(self) -> None:
        patterns = atlas.load_patterns()
        ids = [pattern["metadata"]["id"] for pattern in patterns]
        slugs = [pattern["metadata"]["slug"] for pattern in patterns]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(slugs), len(set(slugs)))

    def test_parser_rejects_unclosed_front_matter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            path = root / "pattern.md"
            path.write_text("---\nid: FFA-999\n", encoding="utf-8")
            with (
                mock.patch.object(atlas, "ROOT", root),
                self.assertRaisesRegex(atlas.AtlasError, "unclosed front matter"),
            ):
                atlas.parse_pattern(path)


class FixtureTests(unittest.TestCase):
    def test_every_mode_returns_evidence(self) -> None:
        results = atlas.run()
        self.assertEqual(len(atlas.load_patterns()) * 3, len(results))
        for result in results:
            self.assertEqual("pass", result["status"])
            self.assertTrue(result["evidence"])

    def test_unknown_pattern_is_rejected(self) -> None:
        with self.assertRaisesRegex(atlas.AtlasError, "unknown pattern"):
            atlas.run("FFA-999")

    def test_timeout_is_release_blocking(self) -> None:
        pattern = atlas.load_patterns()[0]
        with (
            mock.patch.object(
                atlas, "_execute_fixture", side_effect=atlas.AtlasError("exceeded 5s")
            ),
            self.assertRaisesRegex(atlas.AtlasError, "exceeded"),
        ):
            atlas.run_fixture(pattern, "reproduce")

    def test_non_object_json_is_rejected(self) -> None:
        pattern = atlas.load_patterns()[0]
        with (
            mock.patch.object(atlas, "_execute_fixture", return_value=(0, b"[]", b"")),
            self.assertRaisesRegex(atlas.AtlasError, "must be an object"),
        ):
            atlas.run_fixture(pattern, "reproduce")

    def test_non_utf8_output_is_rejected(self) -> None:
        pattern = atlas.load_patterns()[0]
        with (
            mock.patch.object(atlas, "_execute_fixture", return_value=(0, b"\xff", b"")),
            self.assertRaisesRegex(atlas.AtlasError, "not UTF-8"),
        ):
            atlas.run_fixture(pattern, "reproduce")

    def test_fixture_path_escape_is_rejected(self) -> None:
        original = atlas.load_patterns()[0]
        pattern = original.copy()
        pattern["metadata"] = original["metadata"] | {"fixture": "../outside.py"}
        with self.assertRaisesRegex(atlas.AtlasError, "unsafe or missing fixture path"):
            atlas.run_fixture(pattern, "reproduce")

    def test_output_limit_is_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = Path(temp_dir) / "noisy.py"
            fixture.write_text("import sys\nsys.stdout.write('x' * 70000)\n", encoding="utf-8")
            with self.assertRaisesRegex(atlas.AtlasError, "output bytes"):
                atlas._execute_fixture(fixture, "reproduce", temp_dir)

    def test_kill_process_tolerates_macos_exit_race(self) -> None:
        process_mock = mock.Mock(spec=subprocess.Popen)
        process_mock.pid = 1234
        process_mock.poll.side_effect = [None, 0]
        process = cast(subprocess.Popen[bytes], process_mock)
        with (
            mock.patch("atlas.os.name", "posix"),
            mock.patch("atlas.os.killpg", side_effect=PermissionError, create=True),
        ):
            atlas._kill_process(process)
        process_mock.kill.assert_not_called()

    def test_kill_process_falls_back_to_child_after_permission_error(self) -> None:
        process_mock = mock.Mock(spec=subprocess.Popen)
        process_mock.pid = 1234
        process_mock.poll.side_effect = [None, None]
        process = cast(subprocess.Popen[bytes], process_mock)
        with (
            mock.patch("atlas.os.name", "posix"),
            mock.patch("atlas.os.killpg", side_effect=PermissionError, create=True),
        ):
            atlas._kill_process(process)
        process_mock.kill.assert_called_once_with()

    def test_subprocess_environment_does_not_include_path_or_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = Path(temp_dir) / "env.py"
            fixture.write_text(
                "import json, os\nprint(json.dumps(sorted(os.environ)))\n",
                encoding="utf-8",
            )
            return_code, stdout, _ = atlas._execute_fixture(fixture, "reproduce", temp_dir)
        self.assertEqual(0, return_code)
        variables = set(json.loads(stdout))
        self.assertNotIn("PATH", variables)
        runner_variables = variables - {"LC_CTYPE", "SYSTEMROOT", "__CF_USER_TEXT_ENCODING"}
        self.assertEqual(
            {"ATLAS_FIXTURE_ROOT", "PYTHONIOENCODING", "PYTHONUNBUFFERED"},
            runner_variables,
        )
        self.assertIn("ATLAS_FIXTURE_ROOT", variables)


class SiteTests(unittest.TestCase):
    def test_checked_in_site_is_current(self) -> None:
        self.assertEqual([], atlas.build_site(check=True))

    def test_site_generation_has_one_page_per_pattern(self) -> None:
        files = atlas.site_files()
        pattern_pages = [path for path in files if path.parts[0] == "patterns"]
        self.assertEqual(len(atlas.load_patterns()), len(pattern_pages))
        self.assertIn(Path("index.html"), files)
        self.assertIn(Path("atlas.json"), files)

    def test_site_search_and_filters_include_full_public_metadata(self) -> None:
        index = atlas.site_files()[Path("index.html")]
        self.assertIn('data-search="stale green ci evidence ffa-001 hypothetical executable', index)
        self.assertIn('data-stages="verification|merge"', index)
        self.assertIn('id="result-count"', index)
        self.assertIn('id="empty-state"', index)
        self.assertIn("dataset.stages.split('|').includes(stage.value)", index)

    def test_renderer_joins_wrapped_prose_and_keeps_safe_markup(self) -> None:
        rendered = atlas._render_markdown("A wrapped\nparagraph with **proof**.\n")
        self.assertEqual("<p>A wrapped paragraph with <strong>proof</strong>.</p>", rendered)


if __name__ == "__main__":
    unittest.main()
