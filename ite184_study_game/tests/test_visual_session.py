"""New frontend model tests require no Pygame or display device."""

from contextlib import redirect_stdout
from copy import deepcopy
from io import StringIO
import unittest
from unittest.mock import patch

from ite184_study_game import question_bank
from ite184_study_game import pygame_main
from ite184_study_game.ui import session
from ite184_study_game.tests.starter_fixture import use_starter_bank


class VisualSessionTests(unittest.TestCase):
    def setUp(self):
        use_starter_bank(self)
        self.original = deepcopy(question_bank.QUESTION_BANK)

    def tearDown(self):
        self.assertEqual(question_bank.QUESTION_BANK, self.original)

    def test_all_modules_and_pool_limits(self):
        for module, available in ((1, 6), (2, 10), (None, 16)):
            quiz = session.QuizSession(module, "all", 20)
            self.assertEqual(len(quiz.questions), available)
            self.assertEqual(len({q["id"] for q in quiz.questions}), available)
            self.assertTrue(all(q["type"] == "mcq" for q in quiz.questions))

    def test_invalid_answers_and_double_submission_do_not_count(self):
        quiz = session.QuizSession(1, "easy", 5)
        self.assertFalse(quiz.submit("invalid"))
        letter = next(k for k, v in quiz.choices.items() if v == quiz.current_question["answer"])
        self.assertTrue(quiz.submit(f" {letter.lower()} "))
        self.assertFalse(quiz.submit(letter))
        self.assertEqual(quiz.results["answered"], 1)
        self.assertEqual(quiz.results["correct"], 1)
        self.assertEqual(len(quiz.answers), 1)

    def test_advance_requires_answer_and_resets_lock(self):
        quiz = session.QuizSession(2, "all", 5)
        self.assertFalse(quiz.advance())
        quiz.submit("A")
        self.assertTrue(quiz.advance())
        self.assertEqual(quiz.current_question_index, 1)
        self.assertIsNone(quiz.selected_answer)
        self.assertCountEqual(quiz.choices.values(), quiz.current_question["choices"])

    def test_completed_quiz_streaks_breakdowns_and_history(self):
        quiz = session.QuizSession(None, "all", "all")
        for index in range(16):
            correct = index != 2
            letter = next(k for k, v in quiz.choices.items()
                          if (v == quiz.current_question["answer"]) == correct)
            self.assertTrue(quiz.submit(letter))
            self.assertEqual(quiz.advance(), index < 15)
        self.assertEqual(quiz.results["correct"], 15)
        self.assertEqual(quiz.results["incorrect"], 1)
        self.assertEqual(quiz.results["best_streak"], 13)
        self.assertEqual(quiz.results["modules"][1]["answered"], 6)
        self.assertEqual(quiz.results["modules"][2]["answered"], 10)
        self.assertEqual(sum(t["answered"] for t in quiz.results["topics"].values()), 16)
        self.assertEqual(len(quiz.answers), 16)
        self.assertTrue(quiz.is_last_question)

    def test_sessions_do_not_share_counters_or_choice_lists(self):
        first = session.QuizSession(1)
        first.submit("A")
        second = session.QuizSession(1)
        self.assertEqual(second.results["answered"], 0)
        first.questions[0]["choices"].append("local change")
        self.assertTrue(all(len(q["choices"]) == 4 for q in second.questions))

    def test_invalid_or_empty_bank_gives_helpful_error(self):
        with patch.object(session, "validate_question_bank", return_value=(False, ["Duplicate ID"])):
            with self.assertRaisesRegex(ValueError, "Duplicate ID"):
                session.QuizSession()
        with patch.object(session, "prepare_mcq_questions", return_value=[]):
            with self.assertRaisesRegex(ValueError, "No matching MCQ"):
                session.QuizSession()

    def test_missing_pygame_launcher_message(self):
        original_import = __import__

        def unavailable(name, *args, **kwargs):
            if name == "pygame":
                raise ImportError("Pygame missing")
            return original_import(name, *args, **kwargs)

        output = StringIO()
        with patch("builtins.__import__", side_effect=unavailable), redirect_stdout(output):
            self.assertEqual(pygame_main.main(), 1)
        self.assertIn("py -m pip install pygame", output.getvalue())
        self.assertIn("Terminal mode still works", output.getvalue())


if __name__ == "__main__":
    unittest.main()
