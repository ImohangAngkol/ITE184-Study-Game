"""Real Pygame event/render checks using dummy video/audio drivers in tests."""

from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
HAS_PYGAME = importlib.util.find_spec("pygame") is not None
if HAS_PYGAME:
    import pygame
    from ite184_study_game.ui.app import App
    from ite184_study_game.ui.audio import AudioManager
    from ite184_study_game.ui.text import wrap_text
    from ite184_study_game.ui.button import Button

from ite184_study_game.question_bank import QUESTION_BANK
from ite184_study_game.stats import StatsStore
from ite184_study_game.version import APP_TITLE
from ite184_study_game.tests.starter_fixture import use_starter_bank


@unittest.skipUnless(HAS_PYGAME, "Optional Pygame is not installed")
class PygameUITests(unittest.TestCase):
    def setUp(self):
        use_starter_bank(self)
        self.original = deepcopy(QUESTION_BANK)
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.app = App(stats_store=StatsStore(Path(folder.name) / "stats.json"))
        self.app.render()

    def tearDown(self):
        pygame.quit()
        self.assertEqual(QUESTION_BANK, self.original)

    def click(self, name, value=None):
        self.app.render()
        button = next(b for b in self.app.buttons if b.action == (name, value))
        viewport = self.app.viewport()
        position = (round(viewport.x + button.rect.centerx * viewport.width / 1280),
                    round(viewport.y + button.rect.centery * viewport.height / 720))
        self.app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=position))

    def key(self, key):
        self.app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key))

    def setup_quiz(self, module):
        self.click("play")
        self.click("module", module)
        self.click("mode", "mcq")
        self.click("difficulty", "all")
        self.click("count", "all")

    def test_home_locked_buttons_and_hover(self):
        self.assertEqual(pygame.display.get_caption()[0], APP_TITLE)
        # Phase 7 enables Home review/stats. Keep testing disabled button behavior
        # with an explicit fixture instead of expecting obsolete locked features.
        self.assertTrue(all(b.enabled for b in self.app.buttons
                            if b.action[0] in ("mistakes", "statistics")))
        locked = [Button((0, 0, 100, 40), "Disabled", ("none", None), enabled=False)]
        for button in locked:
            self.assertFalse(button.activated(
                pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1), button.rect.center))
        play = next(b for b in self.app.buttons if b.action[0] == "play")
        play.update(play.rect.center, 0.1)
        self.assertGreater(play.hover, 0)

    def test_all_module_flows(self):
        for module, count in ((1, 6), (2, 10), (None, 16)):
            self.app.state = "HOME"
            self.setup_quiz(module)
            self.assertEqual(self.app.state, "QUIZ")
            self.assertEqual(len(self.app.session.questions), count)
            self.app.render()

    def test_answer_lock_correct_wrong_and_next(self):
        self.setup_quiz(1)
        quiz = self.app.session
        letter = next(k for k, v in quiz.choices.items() if v == quiz.current_question["answer"])
        self.key(getattr(pygame, f"K_{letter.lower()}"))
        self.assertEqual(self.app.state, "FEEDBACK")
        self.assertEqual(quiz.results["correct"], 1)
        self.key(pygame.K_a)
        self.assertEqual(quiz.results["answered"], 1)
        correct_buttons = [b for b in self.app.buttons if b.status == "correct"]
        self.assertEqual(len(correct_buttons), 1)
        self.assertFalse(correct_buttons[0].enabled)
        self.key(pygame.K_RETURN)
        self.assertEqual(self.app.state, "QUIZ")
        wrong = next(k for k, v in quiz.choices.items() if v != quiz.current_question["answer"])
        self.click("answer", wrong)
        self.assertEqual(quiz.results["incorrect"], 1)
        self.assertEqual(quiz.results["current_streak"], 0)
        self.assertEqual(len([b for b in self.app.buttons if b.status == "wrong"]), 1)

    def test_results_replay_change_settings_and_home(self):
        self.setup_quiz(None)
        while self.app.state != "RESULTS":
            quiz = self.app.session
            letter = next(k for k, v in quiz.choices.items() if v == quiz.current_question["answer"])
            self.click("answer", letter)
            self.click("next")
        self.assertEqual(self.app.session.results["correct"], 16)
        self.assertEqual(set(self.app.session.results["modules"]), {1, 2})
        self.assertEqual(self.app.scroll.get("breakdown"), 0)
        self.click("replay")
        self.assertEqual(self.app.state, "QUIZ")
        self.assertEqual(self.app.session.results["answered"], 0)
        self.app.state = "RESULTS"
        self.click("change")
        self.assertEqual(self.app.state, "MODULE_SELECT")
        self.app.state = "RESULTS"
        self.click("home")
        self.assertEqual(self.app.state, "HOME")

    def test_escape_quit_confirmation_cancel_and_confirm(self):
        self.setup_quiz(2)
        original_session = self.app.session
        self.key(pygame.K_ESCAPE)
        self.assertEqual(self.app.overlay, "QUIT")
        self.assertEqual({b.action[0] for b in self.app.buttons}, {"confirm_quit", "close_overlay"})
        self.key(pygame.K_n)
        self.assertIs(self.app.session, original_session)
        self.assertIsNone(self.app.overlay)
        self.click("home")
        self.key(pygame.K_y)
        self.assertEqual(self.app.state, "HOME")
        self.assertIsNone(self.app.session)

    def test_back_from_setup_and_settings_preserve_state(self):
        self.click("play")
        self.click("module", 1)
        self.click("mode", "mcq")
        self.key(pygame.K_ESCAPE)
        self.assertEqual(self.app.state, "MODE_SELECT")
        self.key(pygame.K_ESCAPE)
        self.assertEqual(self.app.state, "MODULE_SELECT")
        self.click("settings")
        self.click("music")
        self.assertFalse(self.app.audio.music_enabled)
        self.click("sfx")
        self.assertFalse(self.app.audio.sfx_enabled)
        self.key(pygame.K_ESCAPE)
        self.assertIsNone(self.app.overlay)
        self.assertEqual(self.app.state, "MODULE_SELECT")

    def test_resize_mouse_mapping_and_window_close(self):
        self.app.handle_event(pygame.event.Event(pygame.VIDEORESIZE, size=(960, 600)))
        self.click("play")
        self.assertEqual(self.app.state, "MODULE_SELECT")
        self.assertEqual(self.app.canvas_position((0, 0)), (-1000, -1000))
        self.app.handle_event(pygame.event.Event(pygame.QUIT))
        self.assertFalse(self.app.running)

    def test_long_text_wraps_and_scrolls_within_panel(self):
        font = self.app.fonts["question"]
        lines = wrap_text("X" * 180 + "\n" + "long question " * 100, font, 300)
        self.assertTrue(all(font.size(line)[0] <= 300 for line in lines))
        self.setup_quiz(1)
        self.app.session.current_question["question"] = "Long question " * 200
        self.app.render()
        rect = next(rect for key, rect, maximum in self.app.scroll_zones if key == "question")
        maximum = next(maximum for key, rect, maximum in self.app.scroll_zones if key == "question")
        self.assertGreater(maximum, 0)
        with patch.object(pygame.mouse, "get_pos", return_value=rect.center):
            self.app.handle_event(pygame.event.Event(pygame.MOUSEWHEEL, y=-20))
        self.assertGreater(self.app.scroll["question"], 0)
        self.assertLessEqual(self.app.scroll["question"], maximum)
        self.assertEqual(self.app.canvas.get_clip(), self.app.canvas.get_rect())

    def test_original_wav_assets_load_and_mute(self):
        self.assertTrue(self.app.audio.music_loaded)
        self.assertCountEqual(self.app.audio.sounds, ("click", "correct", "wrong"))
        self.app.audio.play("correct")
        self.app.audio.toggle_music()
        self.assertFalse(self.app.audio.music_enabled)
        self.app.audio.toggle_music()
        self.assertTrue(self.app.audio.music_enabled)
        self.app.audio.toggle_sfx()
        self.assertFalse(self.app.audio.sfx_enabled)

    def test_missing_corrupt_audio_and_unavailable_device(self):
        with tempfile.TemporaryDirectory() as folder:
            audio = AudioManager(folder)
            self.assertFalse(audio.music_loaded)
            self.assertEqual(audio.sounds, {})
            audio.play("missing")
            audio.toggle_music()
            audio.toggle_sfx()
            music = Path(folder) / "music"
            music.mkdir()
            (music / "background.wav").write_text("not a WAV")
            self.assertFalse(AudioManager(folder).music_loaded)
        with patch.object(pygame.mixer, "get_init", return_value=None), \
                patch.object(pygame.mixer, "init", side_effect=pygame.error("No audio device")):
            self.assertFalse(AudioManager().available)


if __name__ == "__main__":
    unittest.main()
