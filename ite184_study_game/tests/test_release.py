"""Release contracts, public assets and fresh-runtime reliability checks."""

import importlib.util
import json
import os
from pathlib import Path
import re
import struct
import tempfile
import unittest
from unittest.mock import patch
import wave

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
HAS_PYGAME = importlib.util.find_spec("pygame") is not None
if HAS_PYGAME:
    import pygame
    from ite184_study_game.ui.app import App
    from ite184_study_game.ui.audio import AudioManager

from ite184_study_game import stats
from ite184_study_game.question_bank import get_all_questions, validate_question_bank
from ite184_study_game.version import __version__, APP_TITLE, DEVELOPER
from ite184_study_game.tools.release_check import ROOT, audit_release, bank_digest, release_files, check_clean_install


class ReleaseFilesTests(unittest.TestCase):
    def manifest(self):
        return json.loads((Path(__file__).parent / "fixtures" / "release_question_manifest.json").read_text())

    def test_version_and_shared_metadata(self):
        self.assertEqual(__version__, self.manifest()["version"])
        self.assertRegex(__version__, r"^\d+\.\d+\.\d+$")
        self.assertIn(__version__, APP_TITLE)
        self.assertEqual(DEVELOPER, "Andrew Daniel C. Corpuz (AD)")

    def test_requirements_only_desktop_dependency(self):
        requirements = [line.strip() for line in (ROOT / "requirements.txt").read_text().splitlines()
                        if line.strip() and not line.startswith("#")]
        self.assertEqual(requirements, ["pygame-ce>=2.5.8,<3"])

    def test_runtime_path_and_secret_audit(self):
        self.assertEqual(audit_release()["errors"], [])

    def test_release_inventory_excludes_runtime_data_and_qa(self):
        files = [path.relative_to(ROOT) for path in release_files()]
        self.assertEqual([str(path) for path in files if "data" in path.parts],
                         [str(Path("ite184_study_game/data/.gitkeep"))])
        self.assertFalse(any(".qa" in path.parts or "artifacts" in path.parts for path in files))

    def test_gitignore_covers_actual_backup_names_and_preserves_source(self):
        text = (ROOT / ".gitignore").read_text()
        self.assertIn("ite184_study_game/data/*.json", text)
        self.assertIn(".qa/", text)
        self.assertIn("__pycache__/", text)
        self.assertIn("ite184_study_game/artifacts/", text)
        self.assertNotIn("screenshots/", text.split("# Generated")[0])
        self.assertNotIn("*.wav", text)
        self.assertNotIn("*.py\n", text)

    def test_readme_screenshot_links_exist_and_are_real_pngs(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        images = set(re.findall(r"\]\((screenshots/[^)]+\.png)\)", text))
        self.assertGreaterEqual(len(images), 10)
        for relative in images:
            with self.subTest(image=relative):
                data = (ROOT / relative).read_bytes()
                self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
                self.assertEqual(struct.unpack(">II", data[16:24]), (1280, 720))
        self.assertNotIn(".qa/", text)
        self.assertNotIn("artifacts/phase", text)

    def test_all_public_readme_local_links_exist(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for link in re.findall(r"\]\(([^)]+)\)", text):
            if "://" not in link and not link.startswith("#"):
                self.assertTrue((ROOT / link.split("#")[0]).exists(), link)

    def test_license_changelog_and_development_notes_preserved(self):
        self.assertIn("MIT License", (ROOT / "LICENSE").read_text())
        self.assertIn("Andrew Daniel C. Corpuz", (ROOT / "LICENSE").read_text())
        self.assertIn("[" + __version__ + "]", (ROOT / "CHANGELOG.md").read_text())
        development = (ROOT / "docs/DEVELOPMENT.md").read_text(encoding="utf-8")
        self.assertGreater(len(development.splitlines()), 1700)
        self.assertIn("Phase 9 — Exam Mode", development)
        self.assertIn("keyword_groups", development)

    def test_question_count_and_validation_unchanged(self):
        self.assertEqual(len(get_all_questions()), 261)
        self.assertEqual(validate_question_bank(), (True, []))

    def test_all_release_question_ids_unchanged(self):
        self.assertEqual(sorted(q["id"] for q in get_all_questions()), self.manifest()["ids"])

    def test_entire_question_content_unchanged(self):
        self.assertEqual(bank_digest(), self.manifest()["bank_sha256"])

    def test_data_and_original_audio_resolve_from_source(self):
        self.assertEqual(stats.SAVE_PATH, Path(stats.__file__).resolve().parent / "data/stats.json")
        for path in (ROOT / "ite184_study_game/assets").rglob("*.wav"):
            with wave.open(str(path), "rb") as audio:
                self.assertEqual(audio.getnchannels(), 1)
                self.assertEqual(audio.getframerate(), 22050)
                self.assertGreater(audio.getnframes(), 0)

    def test_run_scripts_resolve_their_own_folder(self):
        for name in ("run_game.bat", "run_tests.bat"):
            text = (ROOT / name).read_text()
            self.assertIn('cd /d "%~dp0"', text)
            self.assertIn(".venv\\Scripts\\python.exe", text)
            self.assertNotRegex(text, r"[A-Za-z]:[/\\]")

    def test_missing_save_and_directory_initialize_fresh_defaults(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "not-created-yet" / "stats.json"
            store = stats.StatsStore(path)
            self.assertEqual(store.data, stats.create_default_stats())
            self.assertEqual(json.loads(path.read_text())["version"], 3)
            self.assertEqual(store.data["total_xp"], 0)

    def test_v2_migration_keeps_old_progress(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "stats.json"
            old = stats.create_default_stats()
            old["version"] = 2
            old.pop("exams"); old.pop("exam_history")
            old["total_xp"] = 354
            old["mistake_ids"] = ["M2_WR_001"]
            old["achievements"] = ["first_blood"]
            old["question_stats"] = {"M2_WR_001": {"attempts": 1, "successes": 0,
                                     "points_earned": 3, "points_possible": 5}}
            path.write_text(json.dumps(old), encoding="utf-8")
            migrated = stats.StatsStore(path).data
            self.assertEqual(migrated["version"], 3)
            for key, value in old.items():
                if key != "version":
                    self.assertEqual(migrated[key], value, key)

    def test_secret_scan_reports_category_without_disclosing_value(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            secret = "ghp_" + "x" * 36  # Synthetic audit fixture; never a real token.
            (root / "README.md").write_text(secret)
            report = audit_release(root)
            self.assertTrue(report["errors"])
            self.assertNotIn(secret, str(report))


@unittest.skipUnless(HAS_PYGAME, "Optional pygame-ce is unavailable")
class ReleaseUITests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "data" / "stats.json"
        self.store = stats.StatsStore(self.path)
        self.app = App(stats_store=self.store)
        self.addCleanup(pygame.quit)
        self.app.render()

    def click(self, action):
        self.app.render()
        button = next(b for b in self.app.buttons if b.action == (action, None))
        viewport = self.app.viewport()
        pos = (round(viewport.x + button.rect.centerx * viewport.width / 1280),
               round(viewport.y + button.rect.centery * viewport.height / 720))
        self.app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))

    def test_release_window_title(self):
        self.assertEqual(pygame.display.get_caption()[0], APP_TITLE)

    def test_about_renders_and_returns_home(self):
        saved = self.path.read_bytes()
        self.click("about")
        self.assertEqual(self.app.state, "ABOUT")
        self.assertIn("about_credits", self.app.scroll)
        self.click("back")
        self.assertEqual(self.app.state, "HOME")
        self.assertEqual(self.path.read_bytes(), saved)

    def test_about_escape_resize_and_settings_navigation(self):
        self.click("about")
        self.app.handle_event(pygame.event.Event(pygame.VIDEORESIZE, size=(960, 600)))
        self.click("settings")
        self.app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.assertEqual(self.app.state, "ABOUT")
        self.app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.assertEqual(self.app.state, "HOME")

    def test_about_button_does_not_cover_home_save_warning(self):
        self.store.warning = "Progress could not be saved."
        self.app.render()
        button = next(b for b in self.app.buttons if b.action == ("about", None))
        warning = next(rect for key, rect, _ in self.app.scroll_zones if key == "save_warning")
        self.assertFalse(button.rect.colliderect(warning))

    def test_missing_audio_directory_safe(self):
        audio = AudioManager(assets=self.path.parent / "missing-assets")
        self.assertFalse(audio.music_loaded)
        self.assertFalse(audio.sounds)
        audio.play("correct")
        audio.toggle_music(); audio.toggle_sfx()
        self.app.render()

    def test_audio_initialization_failure_safe(self):
        with patch("pygame.mixer.get_init", return_value=None), \
                patch("pygame.mixer.init", side_effect=pygame.error("No audio device")):
            audio = AudioManager()
        self.assertFalse(audio.available)
        self.app.render()

    def test_assets_resolve_independently_of_working_directory(self):
        expected = ROOT / "ite184_study_game/assets"
        original = Path.cwd()
        try:
            os.chdir(self.path.parent)
            audio = AudioManager()
            self.assertEqual(audio.assets, expected)
            self.assertTrue(audio.music_loaded)
            self.assertEqual(set(audio.sounds), {"click", "correct", "wrong"})
        finally:
            os.chdir(original)

    def test_corrupt_fresh_profile_recovers_before_home(self):
        self.path.write_text("{broken", encoding="utf-8")
        with self.assertLogs(level="WARNING"):
            recovered = stats.StatsStore(self.path)
        self.assertEqual(recovered.data, stats.create_default_stats())
        self.app = App(stats_store=recovered)
        self.app.render()
        self.assertEqual(self.app.state, "HOME")
        self.assertTrue(list(self.path.parent.glob("stats.corrupt.*.json")))

    def test_clean_copy_launch_profile_and_migration_without_developer_files(self):
        outputs = check_clean_install()
        self.assertIn("Clean standalone launch", outputs[0])
        self.assertIn("v2 migration passed", outputs[1])


if __name__ == "__main__":
    unittest.main()
