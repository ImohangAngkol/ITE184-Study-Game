"""Written textbox and mixed screen transitions through real Pygame events."""

from copy import deepcopy
import importlib.util
import os
import unittest
from pathlib import Path
import tempfile
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
HAS_PYGAME = importlib.util.find_spec("pygame") is not None
if HAS_PYGAME:
    import pygame
    from ite184_study_game.ui.app import App
    from ite184_study_game.ui.textbox import TextBox
    from ite184_study_game.ui.written_screens import feedback_text

from ite184_study_game.question_bank import QUESTION_BANK
from ite184_study_game.stats import StatsStore
from ite184_study_game.tests.starter_fixture import use_starter_bank


@unittest.skipUnless(HAS_PYGAME, "Optional Pygame is unavailable")
class WrittenUITests(unittest.TestCase):
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
        pos = (round(viewport.x + button.rect.centerx * viewport.width / 1280),
               round(viewport.y + button.rect.centery * viewport.height / 720))
        self.app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))

    def key(self, key, mod=0):
        self.app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key, mod=mod))

    def type_text(self, text):
        self.app.handle_event(pygame.event.Event(pygame.TEXTINPUT, text=text))

    def start(self, mode="written", module=2, difficulty="easy", count="all"):
        self.click("play")
        self.click("module", module)
        self.assertEqual(self.app.state, "MODE_SELECT")
        self.click("mode", mode)
        self.click("difficulty", difficulty)
        self.click("count", count)

    def test_blank_answer_is_blocked(self):
        self.start()
        self.type_text("   ")
        self.key(pygame.K_RETURN)
        self.assertEqual(self.app.state, "QUIZ")
        self.assertEqual(self.app.notice, "Type an answer before submitting.")
        self.assertEqual(self.app.session.results["answered"], 0)

    def test_typing_backspace_delete_and_cursor_editing(self):
        self.start()
        self.type_text("RA 10175!")
        self.key(pygame.K_BACKSPACE)
        self.assertEqual(self.app.textbox.text, "RA 10175")
        self.key(pygame.K_LEFT)
        self.key(pygame.K_DELETE)
        self.assertEqual(self.app.textbox.text, "RA 1017")
        self.type_text("5")
        self.key(pygame.K_END)
        self.type_text(" illegal access")
        self.assertEqual(self.app.textbox.text, "RA 10175 illegal access")
        self.key(pygame.K_RETURN)
        self.assertEqual(self.app.state, "FEEDBACK")
        self.assertEqual(self.app.session.answers[-1]["earned_points"], 4)

    def test_shift_enter_newline_and_answer_shortcuts_do_not_submit(self):
        self.start()
        self.key(pygame.K_a)
        self.key(pygame.K_1)
        self.assertEqual(self.app.session.results["answered"], 0)
        self.type_text("RA 10175")
        self.key(pygame.K_RETURN, pygame.KMOD_SHIFT)
        self.type_text("illegal access without permission")
        self.assertIn("\n", self.app.textbox.text)
        self.assertEqual(self.app.state, "QUIZ")
        self.key(pygame.K_RETURN)
        self.assertEqual(self.app.session.answers[-1]["earned_points"], 5)

    def test_mouse_focus_and_submit_button(self):
        self.start()
        self.app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(500, 100)))
        self.assertFalse(self.app.textbox.focused)
        self.type_text("ignored")
        self.assertEqual(self.app.textbox.text, "")
        self.app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(100, 470)))
        self.assertTrue(self.app.textbox.focused)
        self.type_text("RA 10175 illegal access")
        self.click("submit_written")
        self.assertEqual(self.app.state, "FEEDBACK")

    def test_submitted_answer_locks_and_preserves_original(self):
        self.start()
        original = "RA 10175!!! Illegal Access."
        self.type_text(original)
        self.key(pygame.K_RETURN)
        self.assertTrue(self.app.textbox.locked)
        self.type_text("extra text")
        self.key(pygame.K_BACKSPACE)
        self.app.dispatch(("submit_written", None))
        self.assertEqual(self.app.textbox.text, original)
        self.assertEqual(self.app.session.answers[-1]["answer"], original)
        self.assertEqual(self.app.session.results["answered"], 1)

    def test_partial_feedback_detects_one_concept_and_uses_one_label(self):
        self.start()
        self.type_text("RA 10175")
        self.key(pygame.K_RETURN)
        answer = self.app.session.answers[-1]
        self.assertEqual(answer["earned_points"], 3)
        self.assertEqual(self.app.session.results["current_streak"], 0)
        text = feedback_text(self.app.session.current_question, answer["grading"])
        self.assertIn("MISSED / COULD IMPROVE", text)
        self.assertIn("Illegal access", text)
        self.assertNotIn("Unauthorized access", text)
        self.assertIn("MODEL ANSWER", text)
        self.assertIn("EXPLANATION", text)

    def test_long_answer_cap_wrap_scroll_and_visible_clip(self):
        self.start()
        self.type_text("Long answer with punctuation! " * 100)
        self.assertEqual(len(self.app.textbox.text), 1000)
        self.assertGreater(self.app.textbox.scroll, 0)
        font = self.app.fonts["question"]
        self.assertTrue(all(font.size(line)[0] <= self.app.textbox.rect.width - 32
                            for line, _, _ in self.app.textbox.layout(font)))
        old_scroll = self.app.textbox.scroll
        with patch.object(pygame.mouse, "get_pos", return_value=(100, 470)):
            self.app.handle_event(pygame.event.Event(pygame.MOUSEWHEEL, y=2))
        self.assertLess(self.app.textbox.scroll, old_scroll)
        self.assertEqual(self.app.canvas.get_clip(), self.app.canvas.get_rect())

    def test_long_scenario_and_feedback_scroll(self):
        self.start()
        self.app.session.current_question["scenario"] += " Extra long scenario." * 100
        self.app.render()
        with patch.object(pygame.mouse, "get_pos", return_value=(200, 320)):
            self.app.handle_event(pygame.event.Event(pygame.MOUSEWHEEL, y=-10))
        self.assertGreater(self.app.scroll["scenario"], 0)
        self.type_text("RA 10175")
        self.key(pygame.K_RETURN)
        with patch.object(pygame.mouse, "get_pos", return_value=(950, 340)):
            self.app.handle_event(pygame.event.Event(pygame.MOUSEWHEEL, y=-50))
        self.assertGreater(self.app.scroll["written_feedback"], 0)

    def test_next_written_question_clears_text_and_focuses(self):
        self.start(module=1, difficulty="all")
        self.type_text("a related idea")
        self.key(pygame.K_RETURN)
        self.key(pygame.K_RETURN)
        self.assertEqual(self.app.state, "QUIZ")
        self.assertEqual(self.app.session.current_question_index, 1)
        self.assertEqual(self.app.textbox.text, "")
        self.assertTrue(self.app.textbox.focused)

    def test_mixed_transitions_results_and_review(self):
        self.start(mode="mixed", module=None, difficulty="all", count=10)
        quiz = self.app.session
        # Alternate the already-selected copied questions to verify both directions.
        mcqs = [q for q in quiz.questions if q["type"] == "mcq"]
        written = [q for q in quiz.questions if q["type"] == "written"]
        quiz.questions = [q for pair in zip(mcqs, written) for q in pair]
        quiz.choices = quiz._prepare_choices()
        self.app.reset_textbox()
        self.app.render()
        for question in quiz.questions:
            if question["type"] == "mcq":
                letter = next(k for k, v in quiz.choices.items() if v == question["answer"])
                self.key(pygame.K_1 + "ABCD".index(letter))
            else:
                self.assertTrue(self.app.textbox.focused)
                answer = " ".join(g[0] for g in question["keyword_groups"])
                answer += " " + question["optional_keywords"][0]
                self.type_text(answer)
                self.key(pygame.K_RETURN)
            self.assertEqual(self.app.state, "FEEDBACK")
            self.key(pygame.K_RETURN)
        self.assertEqual(self.app.state, "RESULTS")
        self.assertEqual(quiz.results["earned_points"], 30)
        self.assertEqual(quiz.results["possible_points"], 30)
        self.click("review")
        self.assertEqual(self.app.state, "REVIEW")
        self.click("review_move", 1)
        self.assertEqual(self.app.review_index, 1)
        self.click("review_move", -1)
        self.assertEqual(self.app.review_index, 0)
        self.key(pygame.K_ESCAPE)
        self.assertEqual(self.app.state, "RESULTS")
        self.click("replay")
        self.assertEqual(self.app.session.mode, "mixed")
        self.assertEqual(self.app.session.results["earned_points"], 0)

    def test_overlay_blocks_typing_and_cancel_preserves_text(self):
        self.start()
        self.type_text("RA 10175")
        self.key(pygame.K_ESCAPE)
        self.type_text("blocked")
        self.assertEqual(self.app.textbox.text, "RA 10175")
        self.key(pygame.K_n)
        self.type_text(" illegal access")
        self.assertEqual(self.app.textbox.text, "RA 10175 illegal access")
        self.click("settings")
        self.click("music")
        self.assertFalse(self.app.audio.music_enabled)
        self.key(pygame.K_ESCAPE)
        self.assertEqual(self.app.state, "QUIZ")

    def test_written_resize_keyboard_entry_and_close(self):
        self.start()
        self.app.handle_event(pygame.event.Event(pygame.VIDEORESIZE, size=(900, 600)))
        self.type_text("RA 10175 illegal access")
        self.click("submit_written")
        self.assertEqual(self.app.state, "FEEDBACK")
        self.app.handle_event(pygame.event.Event(pygame.QUIT))
        self.assertFalse(self.app.running)


if __name__ == "__main__":
    unittest.main()
