"""Persistent UI behavior, reopen/review/reset flows, and isolated real rendering."""

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
    from ite184_study_game.ui.stats_screens import percentage

from ite184_study_game.stats import StatsStore, create_default_stats, load_stats
from ite184_study_game.question_bank import QUESTION_BANK, get_question_by_id
from ite184_study_game.tests.starter_fixture import use_starter_bank


@unittest.skipUnless(HAS_PYGAME, "Optional Pygame is unavailable")
class StatsUITests(unittest.TestCase):
    def setUp(self):
        use_starter_bank(self)
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "stats.json"
        self.original = deepcopy(QUESTION_BANK)
        self.store = StatsStore(self.path)
        self.app = App(stats_store=self.store)
        self.app.render()

    def tearDown(self):
        pygame.quit()
        self.assertEqual(QUESTION_BANK, self.original)

    def click(self, action, value=None):
        self.app.render()
        button = next(b for b in self.app.buttons if b.action == (action, value))
        viewport = self.app.viewport()
        pos = (round(viewport.x + button.rect.centerx * viewport.width / 1280),
               round(viewport.y + button.rect.centery * viewport.height / 720))
        self.app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))

    def start(self, mode="mcq", difficulty="easy"):
        self.click("play")
        self.click("module", 2)
        self.click("mode", mode)
        self.click("difficulty", difficulty)
        self.click("count", "all")

    def miss(self, kind="mcq"):
        if kind == "written":
            self.app.textbox.insert("RA 10175")
            self.click("submit_written")
        else:
            quiz = self.app.session
            wrong = next(k for k, v in quiz.choices.items() if v != quiz.current_question["answer"])
            self.click("answer", wrong)
        return self.app.session.current_question["id"]

    def test_home_buttons_enabled_and_empty_review(self):
        self.click("mistakes")
        self.assertEqual(self.app.state, "MISTAKES")
        self.assertNotIn("review_mistakes", {b.action[0] for b in self.app.buttons})
        self.click("back")
        self.click("statistics")
        self.assertEqual(self.app.state, "STATISTICS")
        self.assertEqual(percentage(0, 0), "N/A")

    def test_answer_saved_before_quitting_and_reopening(self):
        self.start("written")
        identifier = self.miss("written")
        self.app.dispatch(("home", None))
        self.app.dispatch(("confirm_quit", None))
        reopened = StatsStore(self.path)
        self.assertEqual(reopened.data["questions_answered"], 1)
        self.assertEqual(reopened.data["games_played"], 0)
        self.assertEqual(reopened.data["total_xp"], 12)
        self.assertIn(identifier, reopened.data["mistake_ids"])
        self.app = App(stats_store=reopened)
        self.app.render()
        badge = next(b.text for b in self.app.buttons if b.action[0] == "mistakes")
        self.assertIn("(1)", badge)

    def test_mcq_review_uses_existing_gameplay_and_removes_mastered(self):
        self.start()
        identifier = self.miss()
        self.app.dispatch(("home", None))
        self.app.dispatch(("confirm_quit", None))
        self.click("mistakes")
        self.click("review_mistakes", (None, "mcq"))
        self.assertTrue(self.app.session.is_review)
        self.assertEqual([q["id"] for q in self.app.session.questions], [identifier])
        correct = next(k for k, v in self.app.session.choices.items()
                       if v == self.app.session.current_question["answer"])
        self.click("answer", correct)
        self.assertTrue(self.app.session.answers[-1]["mastered"])
        self.assertEqual(self.app.mastered_age, 0)
        self.assertFalse(self.store.get_active_mistakes())
        self.click("next")
        self.assertEqual(self.app.state, "RESULTS")
        self.click("replay")
        self.assertEqual(self.app.state, "MISTAKES")

    def test_written_review_score_four_removes_mistake(self):
        self.start("written")
        identifier = self.miss("written")
        self.app.dispatch(("home", None))
        self.app.dispatch(("confirm_quit", None))
        self.click("mistakes")
        self.click("review_mistakes", (2, None))
        self.app.handle_event(pygame.event.Event(pygame.TEXTINPUT, text="RA 10175 illegal access"))
        self.click("submit_written")
        self.assertEqual(self.app.session.answers[-1]["earned_points"], 4)
        self.assertNotIn(identifier, load_stats(self.path)["mistake_ids"])

    def test_review_mix_contains_only_unique_saved_mistakes(self):
        self.store.data["mistake_ids"] = ["M1_MCQ_001", "M2_WR_001", "missing", "M2_WR_001"]
        self.store.save()
        self.click("mistakes")
        self.click("review_mistakes", (None, None))
        self.assertEqual(self.app.session.mode, "mixed")
        self.assertEqual({q["id"] for q in self.app.session.questions}, {"M1_MCQ_001", "M2_WR_001"})
        self.assertEqual(len(self.app.session.questions), 2)

    def test_review_filter_with_no_matching_questions_returns_safely(self):
        self.store.data["mistake_ids"] = ["M2_WR_001"]
        self.app.start_review(1, "mcq")
        self.app.render()
        self.assertEqual(self.app.state, "MISTAKES")
        self.assertIn("No matching", self.app.notice)

    def test_complete_quiz_reopen_preserves_xp_achievements_high_score(self):
        self.start("written")
        self.app.textbox.insert("RA 10175 illegal access without permission")
        self.click("submit_written")
        self.click("next")
        reopened = StatsStore(self.path)
        self.assertEqual(reopened.data["total_xp"], 150)
        self.assertEqual(reopened.level, 2)
        self.assertIn("perfect_run", reopened.data["achievements"])
        self.assertEqual(reopened.data["games_played"], 1)
        self.assertEqual(reopened.data["high_scores"]["module_2_percentage"], 100)

    def test_level_before_quiz_and_session_xp_remain_separate(self):
        self.store.data["total_xp"] = 95
        self.store.save()
        self.start("written")
        self.assertEqual(self.app.session.start_level, 1)
        self.app.textbox.insert("RA 10175 illegal access")
        self.click("submit_written")
        self.assertGreater(self.store.level, self.app.session.start_level)
        self.assertEqual(self.store.data["total_xp"] - 95, self.app.session.progression.total_xp)

    def test_statistics_topics_weak_areas_and_achievements_navigation(self):
        self.store.data["topics"]["Cybercrime"] = {"earned": 6, "possible": 10, "attempts": 2}
        self.store.save()
        self.click("statistics")
        self.click("topics")
        self.assertEqual(self.app.state, "TOPICS")
        self.assertIn("weak_topics", self.app.scroll)
        self.click("back")
        self.click("achievements")
        self.assertEqual(self.app.state, "ACHIEVEMENTS")
        self.assertIn("saved_achievements", self.app.scroll)

    def test_reset_confirmation_cancel_and_confirm(self):
        self.store.data["total_xp"] = 345
        self.store.save()
        self.click("statistics")
        self.click("reset_stats")
        self.assertEqual(self.app.overlay, "RESET")
        self.assertEqual({b.action[0] for b in self.app.buttons}, {"confirm_reset", "close_overlay"})
        self.click("close_overlay")
        self.assertEqual(self.store.data["total_xp"], 345)
        self.click("reset_stats")
        self.click("confirm_reset")
        self.assertEqual(load_stats(self.path), create_default_stats())
        self.assertEqual(self.app.state, "STATISTICS")

    def test_failed_reset_does_not_claim_success_or_erase_progress(self):
        self.store.data["total_xp"] = 345
        self.click("statistics")
        self.click("reset_stats")
        with patch("ite184_study_game.stats.save_stats", return_value=False):
            self.click("confirm_reset")
        self.assertEqual(self.store.data["total_xp"], 345)
        self.assertIn("kept", self.app.notice)

    def test_resize_and_audio_controls_work_on_statistics(self):
        self.click("statistics")
        self.app.handle_event(pygame.event.Event(pygame.VIDEORESIZE, size=(960, 600)))
        self.click("settings")
        self.click("music")
        self.assertFalse(self.app.audio.music_enabled)
        self.app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.assertIsNone(self.app.overlay)
        self.assertEqual(self.app.state, "STATISTICS")


if __name__ == "__main__":
    unittest.main()
