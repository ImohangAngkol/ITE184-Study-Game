"""Phase 3 regression checks using only the standard-library unittest module."""

from contextlib import redirect_stdout
from copy import deepcopy
from io import StringIO
from pathlib import Path
import random
import subprocess
import sys
import unittest
from unittest.mock import patch

from ite184_study_game import game
from ite184_study_game import question_bank as bank
from ite184_study_game import quiz_engine as engine
from ite184_study_game.tests.starter_fixture import use_starter_bank


class QuizEngineTests(unittest.TestCase):
    """Exercise calculations, input flow, and the real starter question bank."""

    def setUp(self):
        use_starter_bank(self)
        self.original_bank = deepcopy(bank.QUESTION_BANK)
        self.output = StringIO()
        self.capture = redirect_stdout(self.output)
        self.capture.__enter__()
        self.addCleanup(self.capture.__exit__, None, None, None)

    def tearDown(self):
        self.assertEqual(bank.QUESTION_BANK, self.original_bank)

    def play(self, module, setup, outcomes):
        """Control answer outcomes while exercising the rest of the quiz flow."""
        with patch("builtins.input", side_effect=setup + [""] * len(outcomes)), \
                patch.object(engine, "ask_mcq_question", side_effect=outcomes):
            return engine.run_mcq_quiz(module)

    def test_module_1_easy_requested_five_uses_three(self):
        results = self.play(1, ["1", "1"], [True, True, True])
        self.assertEqual(results["answered"], 3)
        self.assertEqual(results["correct"], 3)
        self.assertIn("Only 3 matching questions", self.output.getvalue())
        self.assertIn("Starting a 3-question quiz.", self.output.getvalue())

    def test_module_2_all_ten(self):
        results = self.play(2, ["4", "2"], [True] * 10)
        self.assertEqual(results["answered"], 10)
        self.assertEqual(results["modules"], {2: {"correct": 10, "answered": 10}})

    def test_both_all_available(self):
        results = self.play(None, ["4", "4"], [True] * 16)
        self.assertEqual(results["answered"], 16)
        self.assertEqual(results["modules"][1]["answered"], 6)
        self.assertEqual(results["modules"][2]["answered"], 10)
        self.assertIn("Module Breakdown:", self.output.getvalue())

    def test_requested_twenty_uses_six(self):
        results = self.play(1, ["4", "3"], [False] * 6)
        self.assertEqual(results["answered"], 6)
        self.assertIn("Only 6 matching questions", self.output.getvalue())

    def test_invalid_setup_then_valid(self):
        with patch("builtins.input", side_effect=["", "hello", "5", " 2 "]):
            self.assertEqual(engine.select_difficulty(), "medium")
        with patch("builtins.input", side_effect=["20", "no", "", " 3 "]):
            self.assertEqual(engine.select_question_count(), 20)
        self.assertEqual(self.output.getvalue().count("Please enter 1, 2, 3, 4, or Q."), 6)

    def test_back_from_either_setup_prompt(self):
        for inputs in ([" Q "], ["1", "q"]):
            with self.subTest(inputs=inputs), patch("builtins.input", side_effect=inputs):
                self.assertIsNone(engine.run_mcq_quiz(1))
        self.assertNotIn("QUESTION 1 /", self.output.getvalue())

    def test_invalid_answer_then_valid(self):
        question = bank.get_question_by_id("M1_MCQ_001")
        choices = dict(zip("ABCD", question["choices"]))
        with patch("builtins.input", side_effect=["hello", "5", "AA", "", " a "]):
            self.assertTrue(engine.ask_mcq_question(question, 1, 1, choices))
        self.assertEqual(self.output.getvalue().count("Please enter A, B, C, D, or Q."), 4)

    def test_all_uppercase_and_lowercase_answers(self):
        question = bank.get_question_by_id("M1_MCQ_001")
        for position in range(4):
            texts = [text for text in question["choices"] if text != question["answer"]]
            texts.insert(position, question["answer"])
            choices = dict(zip("ABCD", texts))
            for answer in ("ABCD"[position], "abcd"[position]):
                with self.subTest(answer=answer), patch("builtins.input", return_value=answer):
                    self.assertTrue(engine.ask_mcq_question(question, 1, 1, choices))

    def test_wrong_answer_returns_false(self):
        question = bank.get_question_by_id("M1_MCQ_001")
        choices = dict(zip("ABCD", question["choices"]))
        with patch("builtins.input", return_value="b"):
            self.assertIs(engine.ask_mcq_question(question, 1, 1, choices), False)

    def test_question_quit_cancel_then_continue(self):
        question = bank.get_question_by_id("M1_MCQ_001")
        choices = dict(zip("ABCD", question["choices"]))
        with patch("builtins.input", side_effect=["q", "invalid", " N ", "A"]):
            self.assertTrue(engine.ask_mcq_question(question, 1, 1, choices))

    def test_question_quit_confirm_y_or_q(self):
        question = bank.get_question_by_id("M1_MCQ_001")
        choices = dict(zip("ABCD", question["choices"]))
        for confirmation in (" Y ", "q"):
            with self.subTest(confirmation=confirmation), \
                    patch("builtins.input", side_effect=["Q", confirmation]):
                self.assertIsNone(engine.ask_mcq_question(question, 1, 1, choices))

    def test_feedback_pause_validation_and_quit(self):
        with patch("builtins.input", side_effect=["bad", "q", "n", ""]):
            self.assertTrue(engine.wait_to_continue())
        with patch("builtins.input", side_effect=["q", "y"]):
            self.assertFalse(engine.wait_to_continue())

    def test_partial_quiz_uses_answered_denominator(self):
        results = self.play(1, ["4", "4"], [True, False, None])
        self.assertEqual((results["answered"], results["correct"], results["incorrect"]), (2, 1, 1))
        self.assertTrue(results["ended_early"])
        self.assertIn("QUIZ ENDED EARLY", self.output.getvalue())
        self.assertIn("Percentage: 50.0%", self.output.getvalue())

    def test_quitting_before_answering_has_safe_zero_summary(self):
        results = self.play(None, ["4", "4"], [None])
        self.assertEqual(results["answered"], 0)
        self.assertIn("Percentage: 0.0%", self.output.getvalue())
        self.assertIn("Performance: No answers yet", self.output.getvalue())

    def test_quitting_at_feedback_counts_the_answer(self):
        with patch("builtins.input", side_effect=["4", "4", "q", "y"]), \
                patch.object(engine, "ask_mcq_question", return_value=True):
            results = engine.run_mcq_quiz(1)
        self.assertEqual(results["answered"], 1)
        self.assertTrue(results["ended_early"])

    def test_quitting_after_last_answer_is_complete(self):
        # Module 1 Hard has exactly one MCQ, making this the last feedback pause.
        with patch("builtins.input", side_effect=["3", "4", "q", "y"]), \
                patch.object(engine, "ask_mcq_question", return_value=True):
            results = engine.run_mcq_quiz(1)
        self.assertFalse(results["ended_early"])
        self.assertIn("QUIZ COMPLETE", self.output.getvalue())

    def test_questions_shuffle_without_duplicates(self):
        expected_ids = [q["id"] for q in bank.get_questions_by_type("mcq")]
        orders = []
        for seed in (1, 2, 3):
            with patch.object(engine.random, "shuffle", side_effect=random.Random(seed).shuffle):
                questions = engine.prepare_mcq_questions(None, "all", "all")
            ids = [q["id"] for q in questions]
            self.assertCountEqual(ids, expected_ids)
            self.assertEqual(len(ids), len(set(ids)))
            orders.append(ids)
        self.assertNotEqual(orders[0], orders[1])
        self.assertNotEqual(orders[0], expected_ids)

    def test_choices_shuffle_and_answer_text_remains_correct(self):
        question = bank.get_question_by_id("M1_MCQ_001")
        original = deepcopy(question)
        with patch.object(engine.random, "shuffle", side_effect=lambda items: items.reverse()):
            choices = engine.shuffle_choices(question)
        self.assertEqual(list(choices.values()), list(reversed(question["choices"])))
        correct_letter = next(letter for letter, text in choices.items() if text == question["answer"])
        with patch("builtins.input", return_value=correct_letter.lower()):
            self.assertTrue(engine.ask_mcq_question(question, 1, 1, choices))
        self.assertEqual(question, original)

    def test_all_pool_filters_and_requested_counts(self):
        for module in (1, 2, None):
            for difficulty in ("easy", "medium", "hard", "all"):
                expected = bank.filter_questions(module=module, question_type="mcq",
                    difficulty=None if difficulty == "all" else difficulty)
                for count in (5, 10, 20, "all"):
                    with self.subTest(module=module, difficulty=difficulty, count=count):
                        selected = engine.prepare_mcq_questions(module, difficulty, count)
                        expected_count = len(expected) if count == "all" else min(count, len(expected))
                        self.assertEqual(len(selected), expected_count)
                        self.assertTrue(all(q["id"] in {e["id"] for e in expected} for q in selected))
                        self.assertEqual(len(selected), len({q["id"] for q in selected}))

    def test_streaks_and_topic_module_breakdowns(self):
        results = engine.create_quiz_results(None, "all", 6)
        questions = [bank.get_question_by_id(key) for key in
                     ("M1_MCQ_001", "M1_MCQ_002", "M2_MCQ_001")]
        outcomes = [True, True, False, True, True, True]
        for index, outcome in enumerate(outcomes):
            engine.record_answer(results, questions[index % 3], outcome)
        self.assertEqual((results["correct"], results["incorrect"]), (5, 1))
        self.assertEqual((results["current_streak"], results["best_streak"]), (3, 3))
        self.assertEqual(results["topics"]["Cybercrime"], {"correct": 1, "answered": 2})
        self.assertEqual(results["modules"], {
            1: {"correct": 4, "answered": 4}, 2: {"correct": 1, "answered": 2}})
        engine.display_results(results)
        self.assertIn("Percentage: 83.3%", self.output.getvalue())
        self.assertIn("Performance: Very Good", self.output.getvalue())
        self.assertNotIn("Legal Maxims", self.output.getvalue())

    def test_percentage_and_performance_boundaries(self):
        self.assertEqual(engine.calculate_percentage(0, 0), 0.0)
        self.assertEqual(engine.calculate_percentage(4, 5), 80.0)
        for percentage, label in ((100, "Excellent"), (90, "Excellent"),
                (89.9, "Very Good"), (80, "Very Good"), (79.9, "Good"),
                (70, "Good"), (69.9, "Needs Review"), (60, "Needs Review"),
                (59.9, "Needs More Study"), (0, "Needs More Study")):
            self.assertEqual(engine.get_performance_label(percentage), label)

    def test_feedback_shows_shuffled_letter_keywords_and_counters(self):
        question = bank.get_question_by_id("M1_MCQ_001")
        with patch.object(engine.random, "shuffle", side_effect=lambda items: items.reverse()):
            choices = engine.shuffle_choices(question)
        results = engine.create_quiz_results(1, "easy", 1)
        engine.record_answer(results, question, True)
        engine.display_answer_feedback(question, choices, True, results)
        text = self.output.getvalue()
        self.assertIn("[CORRECT]", text)
        self.assertIn("Correct answer: D. Ethics", text)
        self.assertIn(question["explanation"], text)
        self.assertIn("Important keywords:", text)
        self.assertIn("Current score: 1 / 1", text)
        engine.display_answer_feedback(question, choices, False, results)
        self.assertIn("[INCORRECT]", self.output.getvalue())

    def test_no_matching_pool_and_invalid_bank_return_safely(self):
        with patch("builtins.input", side_effect=["1", "1"]), \
                patch.object(engine, "filter_questions", return_value=[]):
            self.assertIsNone(engine.run_mcq_quiz(1))
        self.assertIn("No matching MCQ", self.output.getvalue())
        with patch.object(engine, "validate_question_bank", return_value=(False, ["Bad ID"])):
            self.assertIsNone(engine.run_mcq_quiz(1))
        self.assertIn("Bad ID", self.output.getvalue())
        self.assertEqual(bank.validate_question_bank(), (True, []))

    def test_real_menu_quiz_then_placeholders_and_exit(self):
        # No-op shuffling makes the real one-question hard quiz deterministic.
        with patch.object(engine.random, "shuffle"), \
                patch("builtins.input", side_effect=["invalid", "1", "3", "4", "b", "", "4", "5", "6"]):
            game.run()
        text = self.output.getvalue()
        self.assertIn("QUIZ COMPLETE", text)
        self.assertIn("Score: 1 / 1", text)
        self.assertIn("Review Previous Mistakes is available in the desktop game.", text)
        self.assertIn("Saved statistics are available in the desktop game.", text)
        self.assertIn("Goodbye!", text)
        self.assertGreaterEqual(text.count("ITE184 STUDY GAME"), 4)

    def test_menu_returns_after_setup_back_and_question_quit(self):
        with patch("builtins.input", side_effect=["2", "q", "3", "4", "4", "q", "y", "q"]):
            game.run()
        self.assertIn("QUIZ ENDED EARLY", self.output.getvalue())
        self.assertGreaterEqual(self.output.getvalue().count("ITE184 STUDY GAME"), 3)

    def test_ctrl_c_and_eof_at_each_quiz_prompt_exit_cleanly(self):
        prefixes = ([], ["1"], ["1", "4"], ["1", "4", "4"],
                    ["1", "4", "4", "q"], ["1", "4", "4", "a"])
        for exception in (KeyboardInterrupt, EOFError):
            for prefix in prefixes:
                with self.subTest(exception=exception, prefix=prefix), \
                        patch("builtins.input", side_effect=prefix + [exception()]), \
                        patch.object(engine.random, "shuffle"):
                    game.run()
        self.assertEqual(self.output.getvalue().count("Study game closed. Goodbye!"), 12)

    def test_import_does_not_start_quiz(self):
        root = Path(__file__).resolve().parents[2]
        result = subprocess.run(
            [sys.executable, "-B", "-c", "import ite184_study_game.quiz_engine; print('Import OK')"],
            cwd=root, capture_output=True, text=True, timeout=5,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "Import OK")
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
