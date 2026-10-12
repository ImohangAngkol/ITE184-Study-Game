"""Phase 9 pure preparation/session/grading/persistence regressions."""

from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from ite184_study_game import exam_engine as engine, stats
from ite184_study_game.exam_session import ExamSession, validate_timer, format_time
from ite184_study_game.question_bank import get_all_questions, get_question_by_id
from ite184_study_game.scorer import analyze_written_answer


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def small_pool():
    return [get_question_by_id(identifier) for identifier in
            ("M1_MCQ_001", "M2_MCQ_001", "M1_WR_001", "M2_WR_001")]


def answer_all(session, correct=True):
    for index, question in enumerate(session.questions):
        session.jump(index)
        session.set_answer(question["model_answer"] if question["type"] == "written" and correct else
                           question["answer"] if question["type"] == "mcq" and correct else
                           "I don't know" if question["type"] == "written" else
                           next(c for c in question["choices"] if c != question["answer"]))


class ExamPreparationTests(unittest.TestCase):
    def prepare(self, **kwargs):
        return engine.prepare_exam(rng=random.Random(19), **kwargs)

    def test_module_one(self):
        self.assertEqual({q["module"] for q in self.prepare(module=1)}, {1})

    def test_module_two(self):
        self.assertEqual({q["module"] for q in self.prepare(module=2)}, {2})

    def test_both_modules(self):
        self.assertEqual({q["module"] for q in self.prepare()}, {1, 2})

    def test_mcq_type(self):
        self.assertEqual({q["type"] for q in self.prepare(mode="mcq")}, {"mcq"})

    def test_written_type(self):
        self.assertEqual({q["type"] for q in self.prepare(mode="written")}, {"written"})

    def test_mixed_balance(self):
        self.assertEqual(Counter(q["type"] for q in self.prepare()), {"mcq": 15, "written": 15})

    def test_specific_difficulties(self):
        for tier in engine.DIFFICULTIES:
            self.assertEqual({q["difficulty"] for q in self.prepare(difficulty=tier)}, {tier})

    def test_long_quiz_mix_distribution(self):
        for seed in range(10):
            questions = engine.prepare_exam(difficulty="long_quiz", rng=random.Random(seed))
            self.assertEqual(Counter(q["difficulty"] for q in questions), {"easy": 6, "medium": 12, "hard": 12})
            self.assertEqual(Counter(q["type"] for q in questions), {"mcq": 15, "written": 15})
            self.assertEqual(Counter(q["module"] for q in questions), {1: 10, 2: 20})

    def test_custom_count(self):
        self.assertEqual(len(self.prepare(question_count=17)), 17)

    def test_count_exceeds_pool_clamps_in_engine(self):
        self.assertEqual(len(self.prepare(module=1, mode="written", difficulty="hard", question_count=1000)), 11)

    def test_all_available_is_complete_bank(self):
        questions = self.prepare(question_count="all")
        self.assertEqual(len(questions), 261)
        self.assertEqual({q["id"] for q in questions}, {q["id"] for q in get_all_questions()})

    def test_no_duplicate_ids(self):
        for count in (1, 10, 20, 30, 50, "all"):
            questions = self.prepare(difficulty="long_quiz", question_count=count)
            self.assertEqual(len(questions), len({q["id"] for q in questions}))

    def test_choices_shuffled_and_answers_preserved(self):
        questions = self.prepare(mode="mcq")
        self.assertTrue(any(q["choices"] != get_question_by_id(q["id"])["choices"] for q in questions))
        for question in questions:
            self.assertIn(question["answer"], question["choices"])
            self.assertCountEqual(question["choices"], get_question_by_id(question["id"])["choices"])
            self.assertEqual(question["answer"], get_question_by_id(question["id"])["answer"])
            self.assertEqual(list(question["exam_choices"].values()), question["choices"])

    def test_source_bank_unchanged(self):
        original = get_all_questions()
        prepared = self.prepare()
        prepared[0]["topic"] = "local edit"
        self.assertEqual(get_all_questions(), original)

    def test_difficulty_shortages_redistributed(self):
        pool = [q for q in get_all_questions() if q["module"] == 1 and q["difficulty"] == "easy"]
        questions = self.prepare(questions=pool, difficulty="long_quiz", question_count=10)
        self.assertEqual(len(questions), 10)
        self.assertEqual({q["difficulty"] for q in questions}, {"easy"})

    def test_type_shortages_redistributed(self):
        questions = self.prepare(questions=[q for q in get_all_questions() if q["type"] == "mcq"], question_count=10)
        self.assertEqual(len(questions), 10)
        self.assertEqual({q["type"] for q in questions}, {"mcq"})

    def test_module_shortages_redistributed(self):
        questions = self.prepare(questions=[q for q in get_all_questions() if q["module"] == 2], question_count=10)
        self.assertEqual(len(questions), 10)
        self.assertEqual({q["module"] for q in questions}, {2})

    def test_joint_quota_conflicts_remain_safe(self):
        pool = [q for q in get_all_questions() if
                (q["difficulty"] == "easy" and q["type"] == "mcq") or
                (q["difficulty"] == "hard" and q["type"] == "written")]
        questions = self.prepare(questions=pool, difficulty="long_quiz", question_count=30)
        self.assertEqual(len(questions), 30)
        self.assertEqual(len({q["id"] for q in questions}), 30)

    def test_both_module_weighting_for_counts(self):
        for count in (10, 20, 30, 50):
            questions = self.prepare(question_count=count)
            self.assertEqual(sum(q["module"] == 1 for q in questions), round(count / 3))

    def test_preset_and_custom_timer_validation(self):
        self.assertEqual(engine.ATTY_PRESET, {"module": None, "mode": "mixed", "difficulty": "long_quiz", "question_count": 30, "timer_minutes": 45})
        for invalid in (-1, 0, 181, True, 1.5, "15"):
            with self.assertRaises(ValueError):
                validate_timer(invalid)
        self.assertEqual(validate_timer(180), 10800)
        self.assertIsNone(validate_timer(None))

    def test_invalid_setup_values(self):
        for kwargs in ({"module": True}, {"module": 3}, {"mode": "essay"}, {"difficulty": "tricky"},
                       {"question_count": 0}, {"question_count": -1}, {"question_count": True}, {"question_count": 2.5}):
            with self.assertRaises(ValueError):
                self.prepare(**kwargs)

    def test_empty_pool_helpful_error(self):
        with self.assertRaisesRegex(ValueError, "No questions"):
            self.prepare(questions=[])

    def test_repeated_supplied_ids_do_not_duplicate_questions(self):
        pool = small_pool()
        self.assertEqual(len(self.prepare(questions=pool + pool, question_count="all")), 4)


class ExamSessionTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.exam = ExamSession(questions=small_pool(), clock=self.clock, rng=random.Random(9))

    def go_type(self, kind):
        self.exam.jump(next(i for i, q in enumerate(self.exam.questions) if q["type"] == kind))

    def test_mcq_answer_persists(self):
        self.go_type("mcq")
        index = self.exam.current_question_index
        self.exam.select_choice("A")
        chosen = self.exam.current_question["exam_choices"]["A"]
        self.exam.jump((index + 1) % 4)
        self.exam.jump(index)
        self.assertEqual(self.exam.answers[self.exam.current_question["id"]], chosen)

    def test_mcq_answer_can_change(self):
        self.go_type("mcq")
        self.exam.select_choice("A")
        self.exam.select_choice("B")
        self.assertEqual(self.exam.answers[self.exam.current_question["id"]], self.exam.current_question["exam_choices"]["B"])

    def test_invalid_mcq_ignored(self):
        self.go_type("mcq")
        self.assertFalse(self.exam.select_choice("Z"))
        self.assertFalse(self.exam.set_answer("invented option"))
        self.assertFalse(self.exam.set_answer(None))

    def test_written_exact_text_persists(self):
        self.go_type("written")
        index = self.exam.current_question_index
        text = "  RA10175!!\n\nMy answer  "
        self.exam.set_answer(text)
        self.exam.jump((index + 1) % 4)
        self.exam.jump(index)
        self.assertEqual(self.exam.answers[self.exam.current_question["id"]], text)

    def test_written_answer_can_change(self):
        self.go_type("written")
        self.exam.set_answer("first")
        self.exam.set_answer("second")
        self.assertEqual(self.exam.answers[self.exam.current_question["id"]], "second")

    def test_unanswered_and_whitespace(self):
        self.assertEqual(len(self.exam.unanswered_ids), 4)
        self.go_type("written")
        self.exam.set_answer(" \n ")
        self.assertEqual(len(self.exam.unanswered_ids), 4)
        self.exam.set_answer("attempt")
        self.assertEqual(len(self.exam.unanswered_ids), 3)

    def test_clear_answer_becomes_unanswered(self):
        self.go_type("mcq")
        self.exam.select_choice("A")
        self.exam.set_answer("")
        self.assertIn(self.exam.current_question["id"], self.exam.unanswered_ids)

    def test_flag_and_unflag(self):
        identifier = self.exam.current_question["id"]
        self.exam.toggle_flag()
        self.assertEqual(self.exam.flagged_ids, [identifier])
        self.exam.toggle_flag()
        self.assertEqual(self.exam.flagged_ids, [])

    def test_flags_unique_and_do_not_score(self):
        for _ in range(3):
            self.exam.toggle_flag()
        self.assertEqual(len(self.exam.flagged_ids), 1)
        self.assertEqual(self.exam.submit()["earned_points"], 0)

    def test_previous_and_next(self):
        self.assertTrue(self.exam.next())
        self.assertEqual(self.exam.current_question_index, 1)
        self.assertTrue(self.exam.previous())
        self.assertEqual(self.exam.current_question_index, 0)

    def test_direct_jump_and_visited_ids(self):
        self.exam.jump(3)
        self.exam.jump(3)
        self.assertEqual(self.exam.current_question_index, 3)
        self.assertEqual(len(self.exam.visited_ids), 2)

    def test_navigation_boundaries_safe(self):
        self.assertFalse(self.exam.previous())
        self.assertFalse(self.exam.jump(-1))
        self.assertFalse(self.exam.jump(4))
        self.assertFalse(self.exam.jump(True))
        self.exam.jump(3)
        self.assertFalse(self.exam.next())

    def test_choices_stable_on_revisit(self):
        self.go_type("mcq")
        index = self.exam.current_question_index
        original = deepcopy(self.exam.current_question["exam_choices"])
        for other in range(4):
            self.exam.jump(other)
        self.exam.jump(index)
        self.assertEqual(self.exam.current_question["exam_choices"], original)

    def test_player_projection_has_no_answers_or_hints(self):
        for index in range(4):
            self.exam.jump(index)
            for key in ("answer", "model_answer", "keywords", "keyword_groups", "subtopic", "explanation"):
                self.assertNotIn(key, self.exam.player_question)

    def test_no_grading_before_submission(self):
        with patch("ite184_study_game.exam_session.grade_exam") as grader, patch.object(engine, "analyze_written_answer") as scorer:
            answer_all(self.exam)
            self.exam.toggle_flag()
            self.assertIsNone(self.exam.results)
            grader.assert_not_called()
            scorer.assert_not_called()

    def test_confirmation_unanswered_flagged(self):
        self.exam.toggle_flag()
        self.assertEqual(self.exam.confirmation()["unanswered"], 4)
        self.assertEqual(self.exam.confirmation()["flagged"], 1)

    def test_timer_calculation(self):
        exam = ExamSession(questions=small_pool(), timer_minutes=15, clock=self.clock)
        self.clock.now += 42.25
        self.assertEqual(exam.remaining_time, 857.75)
        self.assertEqual(format_time(exam.remaining_time), "14:18")

    def test_no_timer(self):
        self.clock.now += 999999
        self.assertIsNone(self.exam.remaining_time)
        self.assertFalse(self.exam.tick())
        self.assertEqual(format_time(None), "No timer")

    def test_timer_expiry_auto_submits_once(self):
        exam = ExamSession(questions=small_pool(), timer_minutes=1, clock=self.clock)
        self.clock.now += 61
        self.assertTrue(exam.tick())
        self.assertTrue(exam.auto_submitted)
        self.assertEqual(exam.remaining_time, 0)
        self.assertEqual(exam.results["time_used"], 60)
        self.assertFalse(exam.tick())

    def test_answer_after_deadline_is_not_accepted(self):
        exam = ExamSession(mode="mcq", question_count=1, timer_minutes=1, clock=self.clock)
        self.clock.now += 60
        self.assertFalse(exam.select_choice("A"))
        self.assertEqual(exam.results["unanswered"], 1)

    def test_elapsed_freezes_after_submission(self):
        self.clock.now += 10
        self.exam.submit()
        self.clock.now += 50
        self.assertEqual(self.exam.elapsed, 10)

    def test_unanswered_mcq_and_written_zero(self):
        result = self.exam.submit()
        self.assertEqual(result["possible_points"], 12)
        self.assertEqual(result["earned_points"], 0)
        self.assertEqual(result["unanswered"], 4)
        self.assertTrue(all(a["earned_points"] == 0 for a in result["answers"]))

    def test_mcq_correctness_on_final_choice(self):
        self.go_type("mcq")
        question = self.exam.current_question
        self.exam.set_answer(next(c for c in question["choices"] if c != question["answer"]))
        self.exam.set_answer(question["answer"])
        result = self.exam.submit()
        record = next(a for a in result["answers"] if a["id"] == question["id"])
        self.assertEqual(record["earned_points"], 1)

    def test_written_scorer_reused_and_partial_credit(self):
        self.go_type("written")
        question = self.exam.current_question
        raw = question["keyword_groups"][0][0]
        expected = analyze_written_answer(question, raw)
        self.exam.set_answer(raw)
        with patch.object(engine, "analyze_written_answer", wraps=analyze_written_answer) as scorer:
            result = self.exam.submit()
            self.assertEqual(scorer.call_count, 2)
        actual = next(a for a in result["answers"] if a["id"] == question["id"])
        self.assertEqual(actual["grading"], expected)

    def test_total_points_percentage_and_labels(self):
        answer_all(self.exam)
        result = self.exam.submit()
        self.assertEqual(result["possible_points"], 12)
        self.assertEqual(result["earned_points"], sum(a["earned_points"] for a in result["answers"]))
        self.assertEqual(result["percentage"], result["earned_points"] / 12 * 100)
        self.assertEqual(result["label"], "Excellent")

    def test_points_example_54_of_70(self):
        questions = engine.prepare_exam(mode="mcq", question_count=20, rng=random.Random(1))
        questions += engine.prepare_exam(mode="written", question_count=10, rng=random.Random(2))
        answers = {q["id"]: q["answer"] if q["type"] == "mcq" else "student essay" for q in questions}
        scores = iter([4] * 8 + [2] + [0])
        with patch.object(engine, "analyze_written_answer", side_effect=lambda q, a: {"score": next(scores)}):
            result = engine.grade_exam(questions, answers)
        self.assertEqual(result["earned_points"], 54)
        self.assertEqual(result["possible_points"], 70)
        self.assertAlmostEqual(result["percentage"], 77.1428571429)

    def test_module_type_topic_breakdowns(self):
        result = self.exam.submit()
        self.assertEqual(sum(row["possible"] for row in result["modules"].values()), 12)
        self.assertEqual(result["type_points"]["mcq"]["possible"], 2)
        self.assertEqual(result["type_points"]["written"]["possible"], 10)
        self.assertTrue(result["weakest_topics"])

    def test_post_submit_rewards_and_ordered_streaks(self):
        answer_all(self.exam)
        result = self.exam.submit()
        self.assertEqual(result["best_streak"], 4)
        self.assertGreater(result["xp"], 0)
        self.assertTrue(result["achievements"])
        self.assertNotIn("comeback", {a["id"] for a in result["achievements"]})

    def test_submit_locks_answers_flags_and_navigation(self):
        self.exam.submit()
        self.assertFalse(self.exam.set_answer("new"))
        self.assertFalse(self.exam.toggle_flag())
        self.assertFalse(self.exam.next())
        self.assertFalse(self.exam.abandon())

    def test_repeated_submission_does_not_regrade(self):
        result = self.exam.submit()
        with patch("ite184_study_game.exam_session.grade_exam") as grader:
            self.assertIs(self.exam.submit(), result)
            grader.assert_not_called()

    def test_abandon_does_not_grade(self):
        with patch("ite184_study_game.exam_session.grade_exam") as grader:
            self.exam.abandon()
            self.assertIsNone(self.exam.submit())
            grader.assert_not_called()
        self.assertFalse(self.exam.tick())

    def test_review_hidden_before_submission(self):
        self.assertEqual(self.exam.review_indices(), [])

    def test_review_exposes_correct_and_model_after_submission(self):
        self.exam.submit()
        self.assertEqual(len(self.exam.review_indices()), 4)
        self.assertTrue(all("answer" in q or "model_answer" in q for q in self.exam.questions))

    def test_review_filters(self):
        self.go_type("mcq")
        self.exam.set_answer(self.exam.current_question["answer"])
        answered_index = self.exam.current_question_index
        self.exam.toggle_flag()
        self.exam.submit()
        self.assertEqual(self.exam.review_indices("flagged"), [answered_index])
        self.assertEqual(len(self.exam.review_indices("partial")), 3)
        self.assertEqual(len(self.exam.review_indices("unanswered")), 3)


class ExamPersistenceTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "stats.json"
        self.store = stats.StatsStore(self.path)

    def make_exam(self, **kwargs):
        return ExamSession(questions=small_pool(), stats_store=self.store, **kwargs)

    def test_no_xp_achievements_stats_or_mistakes_before_submit(self):
        original = deepcopy(self.store.data)
        saved = self.path.read_bytes()
        with patch.object(self.store, "save") as save:
            exam = self.make_exam()
            answer_all(exam)
            exam.toggle_flag()
            exam.previous()
            save.assert_not_called()
        self.assertEqual(self.store.data, original)
        self.assertEqual(self.path.read_bytes(), saved)

    def test_submission_updates_permanent_stats(self):
        exam = self.make_exam()
        answer_all(exam)
        result = exam.submit()
        reopened = stats.StatsStore(self.path)
        self.assertEqual(reopened.data["exams"]["completed"], 1)
        self.assertEqual(reopened.data["questions_answered"], 4)
        self.assertEqual(reopened.data["total_xp"], result["xp"])
        self.assertEqual(reopened.data["total_points_possible"], 12)

    def test_unanswered_counts_as_zero_attempt_and_mistake(self):
        self.make_exam().submit()
        self.assertEqual(self.store.data["questions_answered"], 4)
        self.assertEqual(len(self.store.get_active_mistakes()), 4)
        self.assertTrue(all(row["attempts"] == 1 for row in self.store.data["question_stats"].values()))

    def test_abandonment_changes_no_permanent_data(self):
        original = deepcopy(self.store.data)
        saved = self.path.read_bytes()
        exam = self.make_exam()
        answer_all(exam)
        exam.abandon()
        exam.submit()
        self.assertEqual(self.store.data, original)
        self.assertEqual(self.path.read_bytes(), saved)

    def test_exam_highs_and_average(self):
        percentages = []
        for correct in (True, False, True):
            exam = self.make_exam()
            answer_all(exam, correct)
            percentages.append(exam.submit()["percentage"])
        data = stats.StatsStore(self.path).data["exams"]
        self.assertEqual(data["best_percentage"], max(percentages))
        self.assertEqual(data["average_percentage"], sum(percentages) / 3)
        self.assertEqual(data["last_score"], percentages[-1])

    def test_module_specific_exam_highs(self):
        for module in (1, 2, None):
            exam = self.make_exam(module=module)
            answer_all(exam)
            exam.submit()
        for prefix in ("module_1", "module_2", "both"):
            self.assertEqual(self.store.data["exams"][prefix + "_completed"], 1)
            self.assertGreater(self.store.data["exams"][prefix + "_best"], 0)

    def test_study_games_and_highs_stay_separate(self):
        original = deepcopy(self.store.data["high_scores"])
        exam = self.make_exam()
        answer_all(exam)
        exam.submit()
        self.assertEqual(self.store.data["games_played"], 0)
        self.assertEqual(self.store.data["high_scores"], original)

    def test_history_capped_and_summary_only(self):
        for _ in range(12):
            self.make_exam().submit()
        history = stats.StatsStore(self.path).data["exam_history"]
        self.assertEqual(len(history), 10)
        self.assertEqual(len({row["exam_id"] for row in history}), 10)
        self.assertTrue(all("questions" not in row and "answers" not in row for row in history))

    def test_schema_two_migration_preserves_all_old_fields(self):
        exam = self.make_exam()
        answer_all(exam)
        exam.submit()
        old = deepcopy(self.store.data)
        old["version"] = 2
        old.pop("exams")
        old.pop("exam_history")
        self.path.write_text(json.dumps(old), encoding="utf-8")
        migrated = stats.StatsStore(self.path).data
        self.assertEqual(migrated["version"], 3)
        self.assertEqual(migrated["exams"]["completed"], 0)
        for key, value in old.items():
            if key != "version":
                self.assertEqual(migrated[key], value, key)
        self.assertEqual(json.loads(self.path.read_text())["version"], 3)

    def test_corrupt_exam_fields_sanitized(self):
        for invalid in (None, [], "bad", True, 99):
            self.assertEqual(stats.migrate_stats({"exams": invalid})["exams"], stats.create_default_stats()["exams"])
        data = stats.migrate_stats({"exams": {"completed": 2, "best_percentage": float("nan"),
                                  "total_percentage_sum": float("inf")}, "exam_history": ["bad", None]})
        self.assertEqual(data["exams"]["average_percentage"], 0)
        self.assertEqual(data["exam_history"], [])

    def test_wrong_mcq_and_partial_written_become_mistakes(self):
        exam = self.make_exam()
        answer_all(exam, False)
        exam.submit()
        self.assertEqual({q["id"] for q in self.store.get_active_mistakes()}, {q["id"] for q in small_pool()})

    def test_successful_answers_master_old_mistakes_without_duplicates(self):
        self.make_exam().submit()
        exam = self.make_exam()
        answer_all(exam)
        exam.submit()
        self.assertFalse(self.store.get_active_mistakes())
        self.assertTrue(all(row["attempts"] == 2 for row in self.store.data["question_stats"].values()))

    def test_single_atomic_save_for_entire_exam(self):
        exam = self.make_exam()
        with patch.object(stats, "save_stats", wraps=stats.save_stats) as save:
            exam.submit()
            self.assertEqual(save.call_count, 1)

    def test_failed_save_retry_has_no_double_credit(self):
        exam = self.make_exam()
        answer_all(exam)
        saved = self.path.read_bytes()
        with patch.object(stats, "save_stats", return_value=False):
            exam.submit()
        self.assertEqual(self.path.read_bytes(), saved)
        awarded = deepcopy(self.store.data)
        exam.submit()
        self.assertEqual(self.store.data, awarded)
        self.assertEqual(stats.StatsStore(self.path).data, awarded)

    def test_repeated_submission_has_no_double_stats_or_rewards(self):
        exam = self.make_exam()
        answer_all(exam)
        exam.submit()
        original = deepcopy(self.store.data)
        exam.submit()
        self.assertEqual(self.store.data, original)

    def test_preexisting_achievements_not_awarded_again(self):
        exam = self.make_exam()
        answer_all(exam)
        first = exam.submit()["xp"]
        exam = self.make_exam()
        answer_all(exam)
        second = exam.submit()["xp"]
        self.assertLess(second, first)

    def test_reset_clears_exam_stats_and_history(self):
        self.make_exam().submit()
        self.assertTrue(self.store.reset())
        self.assertEqual(self.store.data, stats.create_default_stats())


if __name__ == "__main__":
    unittest.main()
