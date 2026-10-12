"""Exam Mode event/render tests with real Pygame and temporary saved profiles."""

from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
HAS_PYGAME = importlib.util.find_spec("pygame") is not None
if HAS_PYGAME:
    import pygame
    from ite184_study_game.ui.app import App
    from ite184_study_game.ui import exam_screens

from ite184_study_game.stats import StatsStore
from ite184_study_game.question_bank import get_all_questions
from ite184_study_game.tests.test_exam import FakeClock


@unittest.skipUnless(HAS_PYGAME, "Optional Pygame is unavailable")
class ExamUITests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "stats.json"
        self.store = StatsStore(self.path)
        self.clock = FakeClock()
        self.app = App(stats_store=self.store, exam_clock=self.clock)
        self.addCleanup(pygame.quit)
        self.app.render()

    def click(self, action, value=None):
        self.app.render()
        button = next(b for b in self.app.buttons if b.action == (action, value))
        self.assertTrue(button.enabled)
        viewport = self.app.viewport()
        position = (round(viewport.x + button.rect.centerx * viewport.width / 1280),
                    round(viewport.y + button.rect.centery * viewport.height / 720))
        self.app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=position))

    def type_text(self, text):
        self.app.handle_event(pygame.event.Event(pygame.TEXTINPUT, text=text))

    def key(self, key):
        self.app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key))

    def setup_exam(self, module=None, mode="mixed", difficulty="long_quiz", count=10, timer=None):
        self.click("exam")
        self.click("exam_custom_setup")
        self.click("exam_module", module)
        self.click("exam_type", mode)
        self.click("exam_difficulty", difficulty)
        self.click("exam_count", count)
        self.click("exam_timer", timer)

    def start(self, **kwargs):
        self.setup_exam(**kwargs)
        self.click("exam_start")
        self.assertEqual(self.app.state, "EXAM_QUESTION")

    def go_type(self, kind):
        index = next(i for i, q in enumerate(self.app.exam.session.questions) if q["type"] == kind)
        self.app.exam.jump(index)
        self.app.render()

    def fill_exam(self):
        exam = self.app.exam.session
        for index, question in enumerate(exam.questions):
            self.app.exam.jump(index)
            self.app.render()
            if question["type"] == "written":
                self.type_text(question["model_answer"])
            else:
                self.click("exam_select", next(k for k, v in question["exam_choices"].items() if v == question["answer"]))

    def test_home_has_separate_study_and_exam_buttons(self):
        actions = {b.action[0]: b.text for b in self.app.buttons}
        self.assertEqual(actions["play"], "STUDY MODE")
        self.assertEqual(actions["exam"], "EXAM MODE")
        self.assertTrue({"mistakes", "statistics", "settings", "quit"} <= set(actions))

    def test_custom_setup_all_screens(self):
        self.setup_exam(module=1, mode="written", difficulty="hard", count=10, timer=30)
        self.assertEqual(self.app.state, "EXAM_INSTRUCTIONS")
        self.click("exam_start")
        self.assertEqual(self.app.exam.session.timer_duration, 1800)
        self.assertEqual(len(self.app.exam.session.questions), 10)

    def test_atty_preset_and_timer_starts_only_at_start(self):
        self.click("exam")
        self.click("exam_preset")
        self.clock.now += 500
        self.assertIsNone(self.app.exam.session)
        self.click("exam_start")
        exam = self.app.exam.session
        self.assertEqual(exam.remaining_time, 2700)
        self.assertEqual(exam.question_count, 30)
        self.assertEqual(sum(q["module"] == 1 for q in exam.questions), 10)

    def test_custom_count_input(self):
        self.setup_exam()
        self.click("back")
        self.click("back")
        self.click("exam_custom", "count")
        self.type_text("17")
        self.key(pygame.K_RETURN)
        self.assertEqual(self.app.exam.config["question_count"], 17)
        self.assertEqual(self.app.state, "EXAM_TIMER")

    def test_custom_count_invalid_input(self):
        self.setup_exam()
        self.click("back")
        self.click("back")
        self.click("exam_custom", "count")
        self.type_text("0")
        self.click("exam_apply_custom")
        self.assertIn("positive whole", self.app.notice)
        self.assertEqual(self.app.state, "EXAM_CUSTOM")

    def test_excess_count_requires_confirmation(self):
        self.click("exam")
        self.click("exam_custom_setup")
        self.click("exam_module", 1)
        self.click("exam_type", "written")
        self.click("exam_difficulty", "hard")
        self.click("exam_count", 50)
        self.assertEqual(self.app.overlay, "EXAM_COUNT_LIMIT")
        self.assertEqual(self.app.exam.pending_count, 50)
        self.click("close_overlay")
        self.assertEqual(self.app.state, "EXAM_COUNT")
        self.click("exam_count", 50)
        self.click("exam_accept_count")
        self.assertEqual(self.app.exam.config["question_count"], 11)

    def test_custom_timer_validation_and_acceptance(self):
        self.setup_exam()
        self.click("back")
        self.click("exam_custom", "timer")
        self.type_text("181")
        self.click("exam_apply_custom")
        self.assertIn("1–180", self.app.notice)
        self.app.exam.input.text = "7"
        self.click("exam_apply_custom")
        self.assertEqual(self.app.exam.config["timer_minutes"], 7)

    def test_mcq_selection_change_and_revisit(self):
        self.start(mode="mcq")
        exam = self.app.exam.session
        order = deepcopy(exam.current_question["exam_choices"])
        self.click("exam_select", "A")
        self.click("exam_select", "B")
        self.click("exam_move", 1)
        self.click("exam_move", -1)
        self.assertEqual(exam.current_question["exam_choices"], order)
        selected = [b for b in self.app.buttons if "[SELECTED]" in b.text]
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0].action, ("exam_select", "B"))

    def test_written_exact_text_persists_and_can_change(self):
        self.start(mode="written")
        exam = self.app.exam.session
        text = "  RA10175!!\nA response  "
        self.type_text(text)
        self.click("exam_move", 1)
        self.click("exam_move", -1)
        self.assertEqual(self.app.exam.response.text, text)
        self.type_text("extra")
        self.assertEqual(exam.answers[exam.current_question["id"]], text + "extra")

    def test_enter_adds_line_and_never_submits(self):
        self.start(mode="written")
        self.type_text("first line")
        self.key(pygame.K_RETURN)
        self.type_text("second line")
        self.assertEqual(self.app.exam.response.text, "first line\nsecond line")
        self.assertFalse(self.app.exam.session.submitted)

    def test_flags_palette_and_direct_jump(self):
        self.start()
        self.click("exam_flag")
        self.click("exam_palette")
        self.assertEqual(self.app.overlay, "EXAM_PALETTE")
        number = next(b for b in self.app.buttons if b.action == ("exam_jump", 0))
        self.assertIn("F", number.text)
        self.assertIn("?", number.text)
        self.assertIn("*", number.text)
        self.click("exam_jump", 4)
        self.assertEqual(self.app.exam.session.current_question_index, 4)
        self.assertIsNone(self.app.overlay)

    def test_all_available_palette_pagination(self):
        self.start(count="all", difficulty="all")
        self.click("exam_palette")
        self.assertEqual(len([b for b in self.app.buttons if b.action[0] == "exam_jump"]), 40)
        self.click("exam_palette_page", 1)
        self.click("exam_jump", 40)
        self.assertEqual(self.app.exam.session.current_question_index, 40)

    def test_submit_confirmation_cancel_and_pending_review(self):
        self.start()
        self.click("exam_flag")
        self.click("exam_move", 1)
        self.click("exam_submit")
        self.assertFalse(self.app.exam.session.submitted)
        self.assertEqual(self.app.exam.session.confirmation()["unanswered"], 10)
        self.click("exam_review_pending", "flagged")
        self.assertEqual(self.app.exam.session.current_question_index, 0)
        self.click("exam_submit")
        self.click("exam_review_pending", "unanswered")
        self.assertEqual(self.app.exam.session.current_question_index, 0)
        self.click("exam_submit")
        self.click("close_overlay")
        self.assertIsNone(self.app.exam.session.results)

    def test_submit_anyway_grades_unanswered_and_opens_results(self):
        self.start()
        self.click("exam_submit")
        self.click("exam_confirm_submit")
        self.assertEqual(self.app.state, "EXAM_RESULTS")
        self.assertEqual(self.app.exam.session.results["earned_points"], 0)
        self.assertEqual(self.store.data["exams"]["completed"], 1)
        self.assertEqual(len(self.store.get_active_mistakes()), 10)

    def test_no_early_sounds_rewards_grading_stats_or_hud(self):
        saved = self.path.read_bytes()
        with patch.object(self.app.audio, "play") as audio, \
                patch("ite184_study_game.exam_engine.analyze_written_answer") as scorer, \
                patch("ite184_study_game.ui.rewards.label") as reward_labels:
            self.start()
            self.go_type("mcq")
            self.click("exam_select", "A")
            self.go_type("written")
            self.type_text("A speculative answer")
            self.click("exam_flag")
            self.click("settings")
            self.click("close_overlay")
            self.click("exam_submit")
            self.click("close_overlay")
            self.assertTrue(all(call.args[0] == "click" for call in audio.call_args_list))
            scorer.assert_not_called()
            reward_labels.assert_not_called()
        self.assertEqual(self.path.read_bytes(), saved)
        self.assertEqual(self.store.data["total_xp"], 0)
        self.assertFalse(self.store.data["achievements"])
        self.assertIsNone(self.app.exam.session.results)
        self.assertTrue(all(b.status is None for b in self.app.buttons))

    def test_active_render_excludes_sensitive_panels(self):
        self.start()
        for kind in ("mcq", "written"):
            self.go_type(kind)
            with patch.object(exam_screens, "text_panel", wraps=exam_screens.text_panel) as panels:
                self.app.render()
                self.assertEqual({call.args[1] for call in panels.call_args_list}, {"exam_question"})

    def test_timer_continues_under_palette_and_auto_submits(self):
        self.start(timer=15)
        self.click("exam_palette")
        self.clock.now += 901
        self.app.render()
        self.assertEqual(self.app.state, "EXAM_RESULTS")
        self.assertIsNone(self.app.overlay)
        self.assertTrue(self.app.exam.session.auto_submitted)
        self.app.render()
        self.assertEqual(self.store.data["exams"]["completed"], 1)

    def test_timer_continues_under_settings_and_focus_loss(self):
        self.start(timer=15)
        self.click("settings")
        self.app.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
        self.clock.now += 100
        self.app.render()
        self.assertEqual(self.app.exam.session.remaining_time, 800)
        self.clock.now += 800
        self.app.render()
        self.assertEqual(self.app.state, "EXAM_RESULTS")

    def test_current_written_draft_included_in_auto_submission(self):
        self.start(mode="written", timer=15)
        question = self.app.exam.session.current_question
        self.type_text(question["model_answer"])
        self.clock.now += 901
        self.app.render()
        record = next(a for a in self.app.exam.session.results["answers"] if a["id"] == question["id"])
        self.assertEqual(record["answer"], question["model_answer"])
        self.assertGreaterEqual(record["earned_points"], 4)

    def test_escape_abandonment_confirmation_and_cancel(self):
        self.start()
        saved = self.path.read_bytes()
        self.key(pygame.K_ESCAPE)
        self.assertEqual(self.app.overlay, "EXAM_EXIT")
        self.click("close_overlay")
        self.assertEqual(self.app.state, "EXAM_QUESTION")
        self.key(pygame.K_ESCAPE)
        self.click("exam_abandon")
        self.assertEqual(self.app.state, "HOME")
        self.assertEqual(self.path.read_bytes(), saved)

    def test_window_close_requires_exam_exit_confirmation(self):
        self.start()
        self.app.handle_event(pygame.event.Event(pygame.QUIT))
        self.assertTrue(self.app.running)
        self.assertEqual(self.app.overlay, "EXAM_EXIT")
        self.click("exam_abandon")
        self.assertFalse(self.app.running)
        self.assertEqual(self.store.data["exams"]["completed"], 0)

    def test_results_review_filters_and_mistake_navigation(self):
        self.start()
        self.click("exam_flag")
        self.click("exam_submit")
        self.click("exam_confirm_submit")
        self.click("exam_review")
        for filter_name in ("partial", "flagged", "unanswered", "all"):
            self.click("exam_review_filter", filter_name)
            self.assertEqual(self.app.state, "EXAM_REVIEW")
            self.assertTrue(any(key == "exam_review_answer" for key, _, _ in self.app.scroll_zones))
        self.click("exam_results")
        self.click("mistakes")
        self.click("review_mistakes", (None, None))
        self.assertEqual(self.app.state, "QUIZ")
        self.assertTrue(self.app.session.is_review)

    def test_completed_exam_persists_xp_statistics_and_history(self):
        self.start()
        self.fill_exam()
        self.clock.now += 30
        self.click("exam_submit")
        self.click("exam_confirm_submit")
        reopened = StatsStore(self.path)
        self.assertGreater(reopened.data["total_xp"], 0)
        self.assertEqual(reopened.data["exams"]["completed"], 1)
        self.assertEqual(reopened.data["questions_answered"], 10)
        self.assertFalse(reopened.get_active_mistakes())
        self.assertEqual(reopened.data["exam_history"][0]["time_used"], 30)
        self.click("home")
        self.click("statistics")
        self.click("exam_history")
        self.assertEqual(self.app.state, "EXAM_HISTORY")
        self.assertIn("exam_history", self.app.scroll)

    def test_take_another_exam_resets_answers_and_flags(self):
        self.start()
        self.click("exam_flag")
        self.click("exam_submit")
        self.click("exam_confirm_submit")
        self.click("exam_again")
        self.assertEqual(self.app.state, "EXAM_INSTRUCTIONS")
        self.click("exam_start")
        self.assertFalse(self.app.exam.session.answers)
        self.assertFalse(self.app.exam.session.flags)

    def test_resize_music_and_exam_navigation(self):
        self.start(mode="mcq")
        self.app.handle_event(pygame.event.Event(pygame.VIDEORESIZE, size=(960, 600)))
        self.click("music")
        self.assertFalse(self.app.audio.music_enabled)
        self.click("exam_select", "A")
        self.click("exam_move", 1)
        self.assertEqual(self.app.exam.session.current_question_index, 1)

    def test_study_path_still_has_immediate_feedback(self):
        self.click("play")
        self.click("module", 1)
        self.click("mode", "mcq")
        self.click("difficulty", "all")
        self.click("count", 5)
        self.click("answer", "A")
        self.assertEqual(self.app.state, "FEEDBACK")
        self.assertEqual(self.store.data["questions_answered"], 1)
        self.assertEqual(self.store.data["exams"]["completed"], 0)

    def test_instructions_confirmation_and_result_summary_fit_without_scrolling(self):
        self.setup_exam()
        self.assertEqual(next(maximum for key, _, maximum in self.app.scroll_zones if key == "exam_instructions"), 0)
        self.click("exam_start")
        self.click("exam_submit")
        self.assertEqual(next(maximum for key, _, maximum in self.app.scroll_zones if key == "exam_confirm_summary"), 0)
        self.click("exam_confirm_submit")
        self.assertEqual(next(maximum for key, _, maximum in self.app.scroll_zones if key == "exam_result_summary"), 0)

    def test_failed_save_is_reported_and_retry_does_not_duplicate_exam(self):
        self.start()
        self.click("exam_submit")
        with patch("ite184_study_game.stats.save_stats", return_value=False):
            self.click("exam_confirm_submit")
        self.assertTrue(self.store.warning)
        self.assertTrue(any(b.action == ("exam_retry_save", None) for b in self.app.buttons))
        self.click("exam_retry_save")
        self.assertFalse(self.store.warning)
        self.assertEqual(StatsStore(self.path).data["exams"]["completed"], 1)

    def test_all_bank_active_screens_render_without_source_or_progress_changes(self):
        original = get_all_questions()
        saved = self.path.read_bytes()
        self.start(count="all", difficulty="all")
        for index in range(261):
            self.app.exam.jump(index)
            self.app.render()
            self.assertTrue(all(b.status is None for b in self.app.buttons))
            self.assertIsNone(self.app.exam.session.results)
        self.assertEqual(get_all_questions(), original)
        self.assertEqual(self.path.read_bytes(), saved)

    def test_timer_submits_while_confirmation_is_open(self):
        self.start(timer=15)
        self.click("exam_submit")
        self.clock.now += 901
        self.app.render()
        self.assertIsNone(self.app.overlay)
        self.assertEqual(self.app.state, "EXAM_RESULTS")
        self.assertTrue(self.app.exam.session.auto_submitted)
        self.assertEqual(self.store.data["exams"]["completed"], 1)


if __name__ == "__main__":
    unittest.main()
