"""Persistence tests use isolated folders; no test writes the player's real save."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ite184_study_game import stats
from ite184_study_game.question_bank import QUESTION_BANK, get_question_by_id
from ite184_study_game.ui.session import QuizSession
from ite184_study_game.tests.starter_fixture import use_starter_bank


def answer(kind="mcq", score=0, identifier=None, reward=None):
    question = get_question_by_id(identifier or ("M2_WR_001" if kind == "written" else "M2_MCQ_001"))
    return {"id": question["id"], "type": kind, "module": question["module"],
            "topic": question["topic"], "earned_points": score,
            "possible_points": 5 if kind == "written" else 1, "reward": reward or {}}


def completed(module=None, mode="mixed", earned=23, possible=30):
    return {"answered": 10, "planned": 10, "possible_points": possible,
            "earned_points": earned, "module": module, "mode": mode}


class StatsTests(unittest.TestCase):
    def setUp(self):
        use_starter_bank(self)
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "data" / "stats.json"
        self.original_bank = deepcopy(QUESTION_BANK)

    def tearDown(self):
        self.assertEqual(QUESTION_BANK, self.original_bank)

    def store(self):
        return stats.StatsStore(self.path)

    def test_missing_file_creates_versioned_defaults(self):
        self.assertEqual(stats.load_stats(self.path), stats.create_default_stats())
        self.assertTrue(self.path.exists())
        self.assertEqual(json.loads(self.path.read_text())["version"], stats.SCHEMA_VERSION)

    def test_defaults_have_independent_nested_containers(self):
        first, second = stats.create_default_stats(), stats.create_default_stats()
        first["mcq"]["answered"] = 1
        first["mistake_ids"].append("id")
        self.assertEqual(second["mcq"]["answered"], 0)
        self.assertFalse(second["mistake_ids"])

    def test_phase_one_empty_object_migrates(self):
        self.path.parent.mkdir()
        self.path.write_text("{}", encoding="utf-8")
        self.assertEqual(stats.load_stats(self.path), stats.create_default_stats())

    def test_legacy_counts_and_mistakes_are_preserved(self):
        data = stats.migrate_stats({"total_xp": 145, "questions_answered": 9,
            "correct_answers": 7, "wrong_question_ids": ["M2_MCQ_001", "M2_MCQ_001"], "high_score": 80})
        self.assertEqual(data["total_xp"], 145)
        self.assertEqual(data["mcq"], {"answered": 9, "correct": 7})
        self.assertEqual((data["total_points_earned"], data["total_points_possible"]), (7, 9))
        self.assertEqual(data["mistake_ids"], ["M2_MCQ_001"])
        self.assertEqual(data["high_scores"]["overall_percentage"], 80)

    def test_missing_nested_fields_fill_defaults(self):
        data = stats.migrate_stats({"written": {"answered": 2, "points_earned": 7},
                                   "modules": {"1": {"earned": 2, "possible": 3}}})
        self.assertEqual(data["written"]["points_possible"], 10)
        self.assertEqual(data["written"]["perfect_answers"], 0)
        self.assertEqual(data["modules"]["2"], {"earned": 0, "possible": 0})

    def test_malformed_nested_values_never_crash(self):
        for value in (None, "bad", [], 99, True):
            raw = {key: value for key in stats.create_default_stats()}
            data = stats.migrate_stats(raw)
            self.assertEqual(data["version"], stats.SCHEMA_VERSION)
            self.assertTrue(stats.save_stats(data, self.path))
        data = stats.migrate_stats({"topics": {"Cybercrime": "bad"},
            "question_stats": {"M2_WR_001": []}, "mistake_ids": [None, {}, " ", "M2_WR_001"]})
        self.assertEqual(data["topics"]["Cybercrime"]["earned"], 0)
        self.assertEqual(data["mistake_ids"], ["M2_WR_001"])

    def test_negative_boolean_nan_and_huge_counters_are_sanitized(self):
        data = stats.migrate_stats({"total_xp": 10**500, "best_streak": -2, "games_played": True,
            "high_scores": {"overall_percentage": float("nan"), "mixed_percentage": float("inf")}})
        self.assertLessEqual(data["total_xp"], 10**12)
        self.assertEqual(data["best_streak"], 0)
        self.assertEqual(data["games_played"], 0)
        self.assertEqual(data["high_scores"]["overall_percentage"], 0)
        self.assertTrue(stats.save_stats(data, self.path))

    def test_save_load_roundtrip_and_utf8(self):
        data = stats.create_default_stats()
        data["total_xp"] = 123
        data["topics"]["倫理 / Ethics"] = {"earned": 4, "possible": 5, "attempts": 1}
        self.assertTrue(stats.save_stats(data, self.path))
        self.assertIn("倫理", self.path.read_text(encoding="utf-8"))
        self.assertEqual(stats.load_stats(self.path), data)

    def test_empty_corrupt_invalid_root_and_invalid_encoding_recover(self):
        self.path.parent.mkdir()
        for contents in (b"", b"{broken", b"[]", b'"text"', b"\xff\xfe"):
            self.path.write_bytes(contents)
            with self.assertLogs(level="WARNING"):
                data = stats.load_stats(self.path)
            self.assertEqual(data, stats.create_default_stats())
            self.assertTrue(any(p.read_bytes() == contents for p in self.path.parent.glob("stats.corrupt.*.json")))

    def test_future_schema_preserved_before_migration(self):
        self.path.parent.mkdir()
        contents = json.dumps({"version": 99, "total_xp": 200, "future_field": "keep me"})
        self.path.write_text(contents)
        with self.assertLogs(level="WARNING"):
            data = stats.load_stats(self.path)
        self.assertEqual(data["total_xp"], 200)
        self.assertEqual(next(self.path.parent.glob("stats.future.*.json")).read_text(), contents)

    def test_atomic_replace_uses_complete_temp_in_same_directory(self):
        old = stats.create_default_stats()
        old["total_xp"] = 10
        stats.save_stats(old, self.path)
        real_replace = stats.os.replace

        def inspect(source, destination):
            self.assertEqual(Path(source).parent, self.path.parent)
            self.assertEqual(json.loads(Path(source).read_text())["total_xp"], 20)
            self.assertEqual(json.loads(self.path.read_text())["total_xp"], 10)
            return real_replace(source, destination)

        new = stats.create_default_stats()
        new["total_xp"] = 20
        with patch.object(stats.os, "replace", side_effect=inspect):
            self.assertTrue(stats.save_stats(new, self.path))
        self.assertEqual(stats.load_stats(self.path)["total_xp"], 20)
        self.assertFalse(list(self.path.parent.glob("*.tmp")))

    def test_failed_replace_keeps_old_file_and_cleans_temporary(self):
        store = self.store()
        original = self.path.read_bytes()
        store.data["total_xp"] = 100
        with patch.object(stats.os, "replace", side_effect=PermissionError("locked")), self.assertLogs(level="WARNING"):
            self.assertFalse(store.save())
        self.assertEqual(self.path.read_bytes(), original)
        self.assertFalse(list(self.path.parent.glob("*.tmp")))
        self.assertTrue(store.warning)

    def test_failed_read_is_reported_without_traceback(self):
        with patch.object(Path, "read_text", side_effect=PermissionError("blocked")), self.assertLogs(level="WARNING"):
            data = stats.load_stats(self.path)
        self.assertEqual(data["version"], stats.SCHEMA_VERSION)

    def test_answer_save_failure_keeps_in_memory_progress_and_retries(self):
        store = self.store()
        with patch.object(stats, "save_stats", return_value=False):
            self.assertFalse(store.record_answer(answer(score=1), event_id="attempt"))
        self.assertEqual(store.data["questions_answered"], 1)
        self.assertTrue(store.record_answer(answer(score=1), event_id="attempt"))
        self.assertEqual(stats.load_stats(self.path)["questions_answered"], 1)

    def test_xp_accumulates_and_level_rank_use_saved_total(self):
        store = self.store()
        for index in range(5):
            store.record_answer(answer(score=1, reward={"base_xp": 20}), event_id=str(index))
        reloaded = self.store()
        self.assertEqual(reloaded.data["total_xp"], 100)
        self.assertEqual((reloaded.level, reloaded.rank), (2, "Cyber Student"))

    def test_achievement_reward_is_permanent_and_paid_once(self):
        store = self.store()
        reward = {"base_xp": 10, "achievements": [{"id": "on_fire"}]}
        store.record_answer(answer(score=1, reward=reward), event_id="first")
        store = self.store()
        store.record_answer(answer(score=1, reward=reward), event_id="second")
        self.assertEqual(store.data["total_xp"], 45)
        self.assertEqual(store.data["achievements"], ["on_fire"])

    def test_loaded_achievements_seed_future_sessions(self):
        store = self.store()
        question = get_question_by_id("M2_MCQ_001")
        first = QuizSession(2, stats_store=store, questions=[question])
        first.submit(next(k for k, v in first.choices.items() if v == question["answer"]))
        first.advance()
        before = store.data["total_xp"]
        second = QuizSession(2, stats_store=self.store(), questions=[question])
        second.submit(next(k for k, v in second.choices.items() if v == question["answer"]))
        second.advance()
        self.assertEqual(second.progression.achievement_xp, 0)
        self.assertEqual(second.stats_store.data["total_xp"] - before, 10)

    def test_wrong_mcq_adds_unique_mistake_and_success_removes_it(self):
        store = self.store()
        store.record_answer(answer())
        store.record_answer(answer())
        self.assertEqual(store.data["mistake_ids"], ["M2_MCQ_001"])
        store.record_answer(answer(score=1))
        self.assertFalse(store.data["mistake_ids"])
        self.assertEqual(store.data["question_stats"]["M2_MCQ_001"]["attempts"], 3)

    def test_written_mistake_thresholds_and_actual_points(self):
        store = self.store()
        for score in range(4):
            store.record_answer(answer("written", score))
            self.assertIn("M2_WR_001", store.data["mistake_ids"])
        for score in (4, 5):
            store.record_answer(answer("written", score))
            self.assertNotIn("M2_WR_001", store.data["mistake_ids"])
        self.assertEqual(store.data["written"], {
            "answered": 6, "points_earned": 15, "points_possible": 30, "perfect_answers": 1})
        self.assertEqual(store.data["question_stats"]["M2_WR_001"]["successes"], 2)

    def test_duplicate_saved_event_is_not_applied_twice_after_reload(self):
        store = self.store()
        store.record_answer(answer(score=1, reward={"base_xp": 10}), event_id="same")
        reloaded = self.store()
        reloaded.record_answer(answer(score=1, reward={"base_xp": 10}), event_id="same")
        self.assertEqual(reloaded.data["questions_answered"], 1)
        self.assertEqual(reloaded.data["total_xp"], 10)

    def test_retry_log_is_bounded(self):
        data = stats.create_default_stats()
        data["recent_event_ids"] = [str(index) for index in range(800)]
        self.assertEqual(len(stats.migrate_stats(data)["recent_event_ids"]), 512)

    def test_partial_quiz_has_attempts_but_no_game_or_high_score(self):
        store = self.store()
        quiz = QuizSession(2, stats_store=store)
        quiz.submit(next(k for k, v in quiz.choices.items() if v == quiz.current_question["answer"]))
        quiz.finish()
        self.assertEqual(store.data["questions_answered"], 1)
        self.assertEqual(store.data["games_played"], 0)
        self.assertEqual(store.data["high_scores"]["overall_percentage"], 0)
        self.assertGreater(store.data["total_xp"], 0)

    def test_completion_increments_games_and_high_scores_once(self):
        store = self.store()
        store.record_completed_quiz(completed(), {}, event_id="quiz")
        self.assertEqual(store.data["games_played"], 1)
        self.assertAlmostEqual(store.data["high_scores"]["overall_percentage"], 76.6666666667)
        self.assertEqual(store.data["high_scores"]["mixed_percentage"], store.data["high_scores"]["overall_percentage"])
        store = self.store()
        store.record_completed_quiz(completed(), {}, event_id="quiz")
        self.assertEqual(store.data["games_played"], 1)

    def test_high_scores_only_improve_and_filter_modules(self):
        store = self.store()
        for module, score in ((1, 8), (1, 4), (2, 9)):
            store.record_completed_quiz(completed(module, "mcq", score, 10), {})
        self.assertEqual(store.data["high_scores"]["module_1_percentage"], 80)
        self.assertEqual(store.data["high_scores"]["module_2_percentage"], 90)
        self.assertEqual(store.data["high_scores"]["overall_percentage"], 90)

    def test_zero_percent_completion_is_distinct_from_no_completed_quiz(self):
        store = self.store()
        self.assertEqual(store.data["high_score_counts"]["overall_percentage"], 0)
        store.record_completed_quiz(completed(1, "mcq", 0, 10), {})
        self.assertEqual(store.data["high_scores"]["overall_percentage"], 0)
        self.assertEqual(store.data["high_score_counts"]["overall_percentage"], 1)
        self.assertEqual(store.data["high_score_counts"]["module_1_percentage"], 1)
        self.assertEqual(store.data["high_score_counts"]["module_2_percentage"], 0)

    def test_abandoned_completion_call_is_rejected(self):
        store = self.store()
        results = completed()
        results["answered"] = 9
        self.assertFalse(store.record_completed_quiz(results, {}))
        self.assertEqual(store.data["games_played"], 0)

    def test_cumulative_points_modules_and_topics(self):
        store = self.store()
        store.record_answer(answer("written", 4))
        store.record_answer(answer(score=1, identifier="M1_MCQ_001"))
        self.assertEqual((store.data["total_points_earned"], store.data["total_points_possible"]), (5, 6))
        self.assertEqual(store.data["modules"]["2"], {"earned": 4, "possible": 5})
        self.assertEqual(store.data["topics"]["Cybercrime"], {"earned": 4, "possible": 5, "attempts": 1})
        self.assertAlmostEqual(stats.get_accuracy(5, 6), 83.3333333333)

    def test_accuracy_and_zero_denominator(self):
        self.assertIsNone(stats.get_accuracy(0, 0))
        self.assertEqual(stats.get_accuracy(4, 5), 80)

    def test_weak_topics_need_two_attempts_and_sort_lowest_first(self):
        data = stats.create_default_stats()
        data["topics"] = {
            "Weak": {"earned": 1, "possible": 10, "attempts": 2},
            "Moderate": {"earned": 6, "possible": 10, "attempts": 3},
            "Too soon": {"earned": 0, "possible": 5, "attempts": 1},
            "Strong": {"earned": 9, "possible": 10, "attempts": 2},
        }
        self.assertEqual([row["topic"] for row in stats.get_weak_topics(data)], ["Weak", "Moderate"])
        self.assertEqual(stats.get_topic_stats(data)[0]["topic"], "Too soon")

    def test_review_ignores_unknown_ids_duplicates_and_returns_copies(self):
        data = stats.create_default_stats()
        data["mistake_ids"] = ["missing", "M2_WR_001", "M2_WR_001", None, "M1_MCQ_001"]
        questions = stats.get_active_mistakes(data)
        self.assertEqual(len(questions), 2)
        self.assertEqual(len(stats.get_active_mistakes(data, 2, "written")), 1)
        questions[0]["topic"] = "Changed"
        self.assertEqual(get_question_by_id("M2_WR_001")["topic"], "Cybercrime")

    def test_review_success_removes_active_id_keeps_history(self):
        store = self.store()
        store.record_answer(answer("written", 2))
        quiz = QuizSession(2, mode="written", stats_store=store,
                           questions=store.get_active_mistakes(), review=True)
        quiz.submit_written("RA 10175 illegal access")
        self.assertTrue(quiz.answers[-1]["mastered"])
        self.assertFalse(store.get_active_mistakes())
        self.assertEqual(store.data["question_stats"]["M2_WR_001"]["attempts"], 2)

    def test_reset_only_clears_save_data(self):
        store = self.store()
        store.record_answer(answer(), event_id="event")
        self.assertTrue(store.reset())
        self.assertEqual(stats.load_stats(self.path), stats.create_default_stats())

    def test_failed_reset_preserves_progress(self):
        store = self.store()
        store.data["total_xp"] = 200
        with patch.object(stats, "save_stats", return_value=False):
            self.assertFalse(store.reset())
        self.assertEqual(store.data["total_xp"], 200)

    def test_completed_session_does_not_add_answer_xp_twice(self):
        store = self.store()
        quiz = QuizSession(2, "easy", "all", "written", store)
        quiz.submit_written("RA 10175 illegal access without permission")
        self.assertEqual(store.data["total_xp"], 100)
        quiz.advance()
        self.assertEqual(store.data["total_xp"], 150)
        self.assertEqual(store.data["games_played"], 1)
        quiz.finish()
        self.assertEqual(store.data["total_xp"], 150)


if __name__ == "__main__":
    unittest.main()
