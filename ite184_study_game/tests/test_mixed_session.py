"""Mode selection and point-accounting checks using the unmodified starter bank."""

from collections import Counter
from copy import deepcopy
import unittest

from ite184_study_game.question_bank import QUESTION_BANK
from ite184_study_game.question_selection import get_mode_questions, prepare_questions
from ite184_study_game.quiz_engine import calculate_percentage
from ite184_study_game.ui.session import QuizSession
from ite184_study_game.tests.starter_fixture import use_starter_bank


class MixedSessionTests(unittest.TestCase):
    def setUp(self):
        use_starter_bank(self)
        self.original = deepcopy(QUESTION_BANK)

    def tearDown(self):
        self.assertEqual(QUESTION_BANK, self.original)

    def test_written_pools_filter_and_limit(self):
        for module, count in ((1, 4), (2, 6), (None, 10)):
            questions = prepare_questions(module, "all", 20, "written")
            self.assertEqual(len(questions), count)
            self.assertTrue(all(q["type"] == "written" for q in questions))
        hard = prepare_questions(1, "hard", 20, "written")
        self.assertEqual(len(hard), 1)

    def test_balanced_even_and_odd_mixed_subsets(self):
        for count in (5, 10, 15):
            questions = prepare_questions(None, "all", count, "mixed")
            types = Counter(q["type"] for q in questions)
            self.assertLessEqual(abs(types["mcq"] - types["written"]), 1)
            self.assertEqual(len(questions), count)
            self.assertEqual(len({q["id"] for q in questions}), count)

    def test_short_written_pool_fills_with_mcqs(self):
        questions = prepare_questions(2, "easy", 5, "mixed")
        self.assertEqual(Counter(q["type"] for q in questions), {"mcq": 4, "written": 1})

    def test_short_mcq_pool_fills_with_written(self):
        questions = prepare_questions(2, "hard", 5, "mixed")
        self.assertEqual(Counter(q["type"] for q in questions), {"mcq": 1, "written": 4})

    def test_all_available_contains_every_question_once(self):
        questions = prepare_questions(None, "all", "all", "mixed")
        self.assertEqual(len(questions), 26)
        self.assertEqual(len({q["id"] for q in questions}), 26)
        quiz = QuizSession(mode="mixed")
        self.assertEqual(quiz.results["possible_points"], 66)

    def test_mixed_points_streaks_and_breakdowns(self):
        quiz = QuizSession(None, "all", 10, "mixed")
        self.assertEqual(quiz.results["possible_points"], 30)
        while True:
            question = quiz.current_question
            if question["type"] == "mcq":
                correct = next(k for k, v in quiz.choices.items() if v == question["answer"])
                quiz.submit(correct)
            else:
                # All required concepts plus an optional phrase earns five.
                answer = " ".join(group[0] for group in question["keyword_groups"])
                if question["optional_keywords"]:
                    answer += " " + question["optional_keywords"][0]
                self.assertTrue(quiz.submit_written(answer))
                self.assertFalse(quiz.submit_written("another answer"))
            if not quiz.advance():
                break
        stats = quiz.results
        self.assertEqual(stats["earned_points"], 30)
        self.assertEqual(stats["best_streak"], 10)
        self.assertEqual(stats["type_points"], {
            "mcq": {"earned": 5, "possible": 5}, "written": {"earned": 25, "possible": 25}})
        for key in ("point_topics", "point_modules"):
            self.assertEqual(sum(c["earned"] for c in stats[key].values()), 30)
            self.assertEqual(sum(c["possible"] for c in stats[key].values()), 30)
        self.assertEqual(calculate_percentage(23, 30), 76.66666666666667)
        for record in quiz.answers:
            self.assertTrue({"id", "type", "module", "topic", "subtopic", "possible_points",
                             "earned_points", "answer", "grading"}.issubset(record))

    def test_written_success_threshold_and_blank_locking(self):
        quiz = QuizSession(2, "easy", "all", "written")
        self.assertFalse(quiz.submit_written(" \n "))
        self.assertFalse(quiz.submit("A"))
        self.assertTrue(quiz.submit_written("RA 10175 illegal access"))
        self.assertEqual(quiz.results["earned_points"], 4)
        self.assertEqual(quiz.results["current_streak"], 1)
        self.assertFalse(quiz.submit_written("RA 10175 illegal access without permission"))
        self.assertEqual(quiz.results["answered"], 1)

    def test_partial_written_answer_resets_streak(self):
        quiz = QuizSession(2, "easy", "all", "written")
        quiz.results["current_streak"] = 3
        quiz.submit_written("RA 10175")
        self.assertEqual(quiz.results["earned_points"], 3)
        self.assertEqual(quiz.results["current_streak"], 0)

    def test_invalid_modes_and_counts(self):
        with self.assertRaises(ValueError):
            get_mode_questions(mode="invalid")
        for count in (0, -1, True, "invalid"):
            with self.assertRaises(ValueError):
                prepare_questions(question_count=count)


if __name__ == "__main__":
    unittest.main()
