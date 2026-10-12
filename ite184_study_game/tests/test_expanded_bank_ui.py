"""Real Pygame rendering/events with the full bank and isolated saved profiles."""

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
    from ite184_study_game.ui.text import wrap_text

from ite184_study_game.question_bank import get_all_questions, get_question_by_id
from ite184_study_game.stats import StatsStore
from ite184_study_game.ui.session import QuizSession


@unittest.skipUnless(HAS_PYGAME, "Optional Pygame is unavailable")
class ExpandedBankUITests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "stats.json"
        self.store = StatsStore(self.path)
        self.app = App(stats_store=self.store)
        self.addCleanup(pygame.quit)
        self.app.render()

    def click(self, action, value=None):
        self.app.render()
        button = next(b for b in self.app.buttons if b.action == (action, value))
        self.app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                                pos=button.rect.center))

    def start(self, module, mode, difficulty, count):
        self.click("play")
        self.click("module", module)
        self.click("mode", mode)
        self.click("difficulty", difficulty)
        self.click("count", count)
        self.assertEqual(self.app.state, "QUIZ")

    def answer(self, correct=True):
        quiz = self.app.session
        question = quiz.current_question
        if question["type"] == "written":
            self.app.handle_event(pygame.event.Event(
                pygame.TEXTINPUT, text=question["model_answer"] if correct else "I don't know"))
            self.click("submit_written")
        else:
            letter = next(k for k, v in quiz.choices.items() if (v == question["answer"]) == correct)
            self.click("answer", letter)
        self.assertEqual(self.app.state, "FEEDBACK")

    def complete(self):
        for _ in range(len(self.app.session.questions)):
            self.answer()
            self.click("next")
        self.assertEqual(self.app.state, "RESULTS")
        reopened = StatsStore(self.path)
        self.assertGreater(reopened.data["total_xp"], 0)
        self.assertEqual(reopened.data["questions_answered"], len(self.app.session.questions))
        self.assertEqual(reopened.data["games_played"], 1)
        self.assertFalse(reopened.data["mistake_ids"])
        self.assertEqual(reopened.data, self.store.data)

    def test_module_one_hard_written_full_quiz(self):
        self.start(1, "written", "hard", "all")
        self.assertGreaterEqual(len(self.app.session.questions), 10)
        self.complete()
        self.assertTrue(all(a["earned_points"] >= 4 for a in self.app.session.answers))

    def test_module_two_hard_mixed_twenty_quiz(self):
        self.start(2, "mixed", "hard", 20)
        self.assertEqual(sum(q["type"] == "written" for q in self.app.session.questions), 10)
        self.assertTrue(all(q["difficulty"] == "hard" for q in self.app.session.questions))
        self.complete()

    def test_both_modules_all_difficulties_twenty_quiz(self):
        self.start(None, "mixed", "all", 20)
        self.assertEqual(len(self.app.session.questions), 20)
        self.complete()
        self.click("review")
        self.assertEqual(self.app.state, "REVIEW")
        self.assertTrue(any(key == "review_answer" for key, _, _ in self.app.scroll_zones))

    def test_old_and_new_mistakes_survive_reopen_and_are_mastered(self):
        pool = [get_question_by_id("M2_WR_006"), get_question_by_id("M2_WR_075"),
                get_question_by_id("M1_MCQ_045")]
        self.app.session = QuizSession(mode="mixed", stats_store=self.store, questions=pool)
        self.app.state = "QUIZ"
        self.app.reset_textbox()
        for _ in pool:
            self.answer(False)
            self.click("next")
        before = self.store.data["total_xp"]
        self.app.stats_store = StatsStore(self.path)
        self.app.start_review()
        self.assertTrue(self.app.session.is_review)
        self.assertEqual({q["id"] for q in self.app.session.questions}, {q["id"] for q in pool})
        for _ in pool:
            self.answer()
            self.click("next")
        reopened = StatsStore(self.path)
        self.assertFalse(reopened.get_active_mistakes())
        self.assertGreater(reopened.data["total_xp"], before)
        for question in pool:
            self.assertEqual(reopened.data["question_stats"][question["id"]]["attempts"], 2)
        self.assertEqual(set(reopened.data["topics"]), {q["topic"] for q in pool})

    def test_long_scenario_and_feedback_scroll_with_mouse(self):
        question = get_question_by_id("M2_WR_075")
        self.app.session = QuizSession(mode="written", stats_store=self.store, questions=[question])
        self.app.state = "QUIZ"
        self.app.reset_textbox()
        self.app.render()
        key, rect, maximum = next(zone for zone in self.app.scroll_zones if zone[0] == "scenario")
        self.assertGreater(maximum, 0)
        with patch("pygame.mouse.get_pos", return_value=rect.center):
            self.app.handle_event(pygame.event.Event(pygame.MOUSEWHEEL, y=-100))
        self.app.render()
        self.assertEqual(self.app.scroll[key], maximum)
        self.answer()
        key, rect, maximum = next(zone for zone in self.app.scroll_zones if zone[0] == "written_feedback")
        self.assertGreater(maximum, 0)
        with patch("pygame.mouse.get_pos", return_value=rect.center):
            self.app.handle_event(pygame.event.Event(pygame.MOUSEWHEEL, y=-100))
        self.app.render()
        self.assertEqual(self.app.scroll[key], maximum)
        self.assertTrue(any(b.action == ("next", None) for b in self.app.buttons))

    def test_all_new_choices_and_metadata_fit_existing_controls(self):
        font = pygame.font.SysFont("segoeui", 12, bold=True)
        for question in get_all_questions():
            with self.subTest(question=question["id"]):
                for field in ("topic", "subtopic"):
                    prefix = "Topic: " if field == "topic" else "Subtopic: "
                    self.assertLessEqual(self.app.fonts["small"].size(prefix + question[field])[0], 696)
                if question["type"] == "mcq":
                    for choice in question["choices"]:
                        # Longest feedback suffix, at the existing renderer's minimum size.
                        lines = wrap_text("A   " + choice + "  [YOUR ANSWER]", font, 696)
                        self.assertLessEqual(len(lines) * font.get_linesize(), 36)

    def test_all_bank_questions_and_feedback_render(self):
        # Full-bank smoke rendering checks both types without writing fake progress.
        for question in get_all_questions():
            with self.subTest(question=question["id"]):
                quiz = QuizSession(mode=question["type"], questions=[question])
                self.app.session = quiz
                self.app.state = "QUIZ"
                self.app.reset_textbox()
                self.app.render()
                if question["type"] == "written":
                    self.app.textbox.text = question["model_answer"]
                    quiz.submit_written(question["model_answer"])
                else:
                    quiz.submit(next(k for k, v in quiz.choices.items() if v == question["answer"]))
                self.app.state = "FEEDBACK"
                self.app.render()
                self.assertTrue(any(b.action == ("next", None) for b in self.app.buttons))
                for key, _, maximum in self.app.scroll_zones:
                    self.app.scroll[key] = maximum
                self.app.render()
        self.assertEqual(self.store.data["questions_answered"], 0)

    def test_topic_statistics_scroll_with_all_topics(self):
        for question in get_all_questions():
            self.store.data["topics"].setdefault(question["topic"], {"earned": 0, "possible": 10, "attempts": 2})
        self.click("statistics")
        self.click("topics")
        self.assertEqual(self.app.state, "TOPICS")
        self.assertGreater(next(maximum for key, _, maximum in self.app.scroll_zones if key == "topic_statistics"), 0)


if __name__ == "__main__":
    unittest.main()
