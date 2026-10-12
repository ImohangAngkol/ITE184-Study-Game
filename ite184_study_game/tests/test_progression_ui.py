"""Progression UI checks use synthetic input and real dummy-driver rendering."""

from copy import deepcopy
import importlib.util
import os
import unittest
from pathlib import Path
import tempfile

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
HAS_PYGAME = importlib.util.find_spec("pygame") is not None
if HAS_PYGAME:
    import pygame
    from ite184_study_game.ui.app import App

from ite184_study_game.question_bank import QUESTION_BANK
from ite184_study_game.stats import StatsStore
from ite184_study_game.tests.starter_fixture import use_starter_bank


@unittest.skipUnless(HAS_PYGAME, "Optional Pygame is unavailable")
class ProgressionUITests(unittest.TestCase):
    def setUp(self):
        use_starter_bank(self)
        self.original = deepcopy(QUESTION_BANK)
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.app = App(stats_store=StatsStore(Path(folder.name) / "stats.json"))
        self.app.selected_module = 2
        self.app.selected_difficulty = "all"
        self.app.start_quiz()
        self.app.render()

    def tearDown(self):
        pygame.quit()
        self.assertEqual(QUESTION_BANK, self.original)

    def answer(self, correct):
        quiz = self.app.session
        letter = next(k for k, v in quiz.choices.items()
                      if (v == quiz.current_question["answer"]) == correct)
        self.app.dispatch(("answer", letter))
        self.app.render()

    def test_live_xp_level_rank_and_toast_are_nonblocking(self):
        self.answer(True)
        progress = self.app.session.progression
        self.assertEqual(progress.base_xp, 10)
        self.assertTrue(self.app.achievement_queue)
        self.assertIsNone(self.app.overlay)
        self.assertEqual(self.app.last_reward["base_xp"], 10)
        self.app.dispatch(("next", None))
        self.assertEqual(self.app.state, "QUIZ")
        for _ in range(4):
            self.answer(True)
            self.app.dispatch(("next", None))
        self.assertGreaterEqual(progress.level, 2)
        self.assertEqual(progress.level_progress, progress.total_xp % 100)
        self.assertIn("unstoppable", progress.unlocked_ids)

    def test_zero_hearts_continues_and_recovers_after_three_successes(self):
        for _ in range(3):
            self.answer(False)
            self.app.dispatch(("next", None))
        self.assertEqual(self.app.state, "QUIZ")
        self.assertEqual(self.app.session.progression.lives, 0)
        for _ in range(3):
            self.answer(True)
            self.app.dispatch(("next", None))
        self.assertEqual(self.app.session.progression.lives, 1)
        self.assertIn("comeback", self.app.session.progression.unlocked_ids)
        self.assertEqual(self.app.last_reward["heart_delta"], 1)

    def test_duplicate_answer_does_not_queue_rewards_twice(self):
        self.answer(True)
        count = len(self.app.achievement_queue)
        xp = self.app.session.progression.total_xp
        self.app.dispatch(("answer", "A"))
        self.assertEqual(len(self.app.achievement_queue), count)
        self.assertEqual(self.app.session.progression.total_xp, xp)

    def test_toast_timer_expires_without_changing_rewards(self):
        self.answer(True)
        xp = self.app.session.progression.total_xp
        initial = len(self.app.achievement_queue)
        self.app.update_rewards(2.5)
        self.assertEqual(len(self.app.achievement_queue), initial - 1)
        self.app.update_rewards(100)
        self.assertFalse(self.app.achievement_queue)
        self.assertEqual(self.app.session.progression.total_xp, xp)

    def test_results_rewards_review_and_replay(self):
        while self.app.state != "RESULTS":
            self.answer(True)
            self.app.dispatch(("next", None))
        progress = self.app.session.progression
        self.assertIn("perfect_run", progress.unlocked_ids)
        xp = progress.total_xp
        self.app.dispatch(("rewards", None))
        self.app.render()
        self.assertEqual(self.app.state, "REWARDS")
        self.assertIn("reward_achievements", self.app.scroll)
        self.app.dispatch(("rewards_done", None))
        self.app.dispatch(("review", None))
        self.app.render()
        self.assertEqual(self.app.state, "REVIEW")
        self.assertEqual(progress.total_xp, xp)
        self.app.dispatch(("review_done", None))
        self.app.dispatch(("replay", None))
        self.assertEqual(self.app.session.progression.total_xp, 0)
        self.assertEqual(self.app.session.progression.lives, 3)
        self.assertFalse(self.app.achievement_queue)

    def test_written_rewards_hud_and_resize(self):
        self.app.selected_mode = "written"
        self.app.selected_difficulty = "easy"
        self.app.start_quiz()
        self.app.textbox.insert("RA 10175 illegal access without permission")
        self.app.dispatch(("submit_written", None))
        self.assertEqual(self.app.session.progression.base_xp, 25)
        self.assertIn("perfect_answer", self.app.session.progression.unlocked_ids)
        self.app.handle_event(pygame.event.Event(pygame.VIDEORESIZE, size=(960, 600)))
        self.app.render()
        self.app.present()
        self.assertEqual(self.app.state, "FEEDBACK")

    def test_abandoned_quiz_does_not_unlock_completion_achievements(self):
        self.app.selected_mode = "mixed"
        self.app.start_quiz()
        progress = self.app.session.progression
        self.app.dispatch(("home", None))
        self.app.dispatch(("confirm_quit", None))
        self.assertEqual(self.app.state, "HOME")
        self.assertFalse(progress.completed)
        self.assertFalse({"perfect_run", "mixed_master"} & progress.unlocked_ids)


if __name__ == "__main__":
    unittest.main()
