"""Pure Phase 6 reward rules plus integration with existing quiz sessions."""

from copy import deepcopy
import unittest

from ite184_study_game.achievements import ACHIEVEMENTS
from ite184_study_game.progression import (
    Progression, calculate_xp, calculate_level, get_rank, update_lives,
)
from ite184_study_game.question_bank import QUESTION_BANK
from ite184_study_game.tests.starter_fixture import use_starter_bank
from ite184_study_game.ui.session import QuizSession


def question(identifier, kind="mcq", topic="Basic Concepts"):
    """Small metadata fixture: no question-bank edits are needed for reward rules."""
    return {"id": identifier, "type": kind, "topic": topic}


class ProgressionTests(unittest.TestCase):
    def test_mcq_xp_correct_and_wrong(self):
        self.assertEqual(calculate_xp("mcq", 1), 10)
        self.assertEqual(calculate_xp("mcq", 0), 0)

    def test_written_xp_mapping(self):
        self.assertEqual([calculate_xp("written", score) for score in range(6)],
                         [0, 2, 6, 12, 20, 25])

    def test_invalid_xp_inputs(self):
        for kind, score in (("mcq", 2), ("written", -1), ("written", 6), ("unknown", 1)):
            with self.assertRaises(ValueError):
                calculate_xp(kind, score)

    def test_level_boundaries(self):
        for xp, level in ((0, 1), (99, 1), (100, 2), (199, 2), (200, 3), (250, 3), (600, 7)):
            self.assertEqual(calculate_level(xp), level)

    def test_rank_titles_and_level_six_plus(self):
        names = ["IT Apprentice", "Cyber Student", "Security Analyst", "Ethical Hacker",
                 "Cyber Law Specialist", "Cyber Law Master"]
        for level, name in enumerate(names, start=1):
            self.assertEqual(get_rank(level), name)
        self.assertEqual(get_rank(100), "Cyber Law Master")

    def test_fresh_progression_starts_empty_and_three_lives(self):
        progress = Progression()
        self.assertEqual((progress.total_xp, progress.level, progress.rank, progress.lives),
                         (0, 1, "IT Apprentice", 3))
        self.assertFalse(progress.unlocked_ids)
        self.assertFalse(progress.completed)

    def test_streak_thresholds_pay_once_at_three_five_ten(self):
        progress = Progression()
        payouts = [progress.reward_answer(question(str(index)), 1, index)["streak_xp"]
                   for index in range(1, 12)]
        self.assertEqual(payouts, [0, 0, 10, 0, 20, 0, 0, 0, 0, 50, 0])
        self.assertEqual(progress.streak_xp, 80)

    def test_restart_streak_does_not_repeat_threshold(self):
        progress = Progression()
        for streak in range(1, 4):
            progress.reward_answer(question(f"first{streak}"), 1, streak)
        progress.reward_answer(question("wrong"), 0, 0)
        for streak in range(1, 4):
            reward = progress.reward_answer(question(f"second{streak}"), 1, streak)
        self.assertEqual(reward["streak_xp"], 0)
        self.assertEqual(progress.streak_xp, 10)

    def test_wrong_answer_loses_one_life_never_below_zero(self):
        progress = Progression()
        for index in range(5):
            progress.reward_answer(question(str(index)), 0, 0)
            self.assertEqual(progress.lives, max(0, 2 - index))

    def test_written_life_policy(self):
        for score in range(6):
            self.assertEqual(update_lives(3, "written", score, 0), 2 if score <= 2 else 3)

    def test_heart_recovery_at_three_six_and_maximum(self):
        self.assertEqual(update_lives(1, "mcq", 1, 3), 2)
        self.assertEqual(update_lives(2, "written", 4, 6), 3)
        self.assertEqual(update_lives(3, "mcq", 1, 9), 3)
        self.assertEqual(update_lives(0, "mcq", 1, 2), 0)
        self.assertEqual(update_lives(0, "written", 3, 3), 0)

    def test_comeback_unlocks_after_recovery_once(self):
        progress = Progression()
        progress.reward_answer(question("wrong"), 0, 0)
        for streak in range(1, 4):
            reward = progress.reward_answer(question(str(streak)), 1, streak)
        self.assertEqual(reward["heart_delta"], 1)
        self.assertIn("comeback", progress.unlocked_ids)
        self.assertEqual(progress.lives, 3)
        self.assertEqual([a["id"] for a in progress.achievements].count("comeback"), 1)

    def test_first_success_and_duplicate_submission_guard(self):
        progress = Progression()
        progress.reward_answer(question("incorrect"), 0, 0)
        first = progress.reward_answer(question("correct"), 1, 1)
        self.assertIn("first_blood", [a["id"] for a in first["achievements"]])
        total = progress.total_xp
        repeat = progress.reward_answer(question("correct"), 1, 1)
        self.assertEqual(repeat["total_xp"], 0)
        self.assertEqual(progress.total_xp, total)
        self.assertFalse(repeat["achievements"])

    def test_on_fire_unstoppable_and_perfect_answer(self):
        progress = Progression()
        for streak in range(1, 6):
            progress.reward_answer(question(str(streak), "written"), 5, streak)
        self.assertTrue({"first_blood", "on_fire", "unstoppable", "perfect_answer"}
                        .issubset(progress.unlocked_ids))
        self.assertEqual(progress.achievement_xp, 125)

    def test_subject_achievements_require_success(self):
        progress = Progression()
        for index, (topic, achievement) in enumerate((
            ("Legal Maxims", "law_student"), ("Cybercrime", "cyber_defender"),
            ("Malware", "malware_hunter"))):
            progress.reward_answer(question(f"bad{index}", "written", topic), 3, 0)
            self.assertNotIn(achievement, progress.unlocked_ids)
            progress.reward_answer(question(f"good{index}", "written", topic), 4, 1)
            self.assertIn(achievement, progress.unlocked_ids)

    def test_ra_10175_achievement_for_other_topic(self):
        progress = Progression()
        item = question("privacy", "written", "Data Privacy")
        item["keyword_groups"] = [["ra 10175"], ["ra 10173"]]
        progress.reward_answer(item, 4, 1)
        self.assertIn("cyber_defender", progress.unlocked_ids)

    def test_completion_perfect_and_mixed_rewards_once(self):
        progress = Progression()
        reward = progress.complete_quiz(30, 30, "mixed")
        self.assertEqual({a["id"] for a in reward["achievements"]}, {"perfect_run", "mixed_master"})
        self.assertEqual(reward["achievement_xp"], 100)
        self.assertEqual(progress.complete_quiz(30, 30, "mixed")["total_xp"], 0)

    def test_nonperfect_and_zero_question_completion(self):
        progress = Progression()
        reward = progress.complete_quiz(23, 30, "mixed")
        self.assertEqual([a["id"] for a in reward["achievements"]], ["mixed_master"])
        self.assertNotIn("perfect_run", progress.unlocked_ids)
        self.assertEqual(Progression().complete_quiz(0, 0, "mixed")["total_xp"], 0)

    def test_xp_ledger_and_level_progress_are_consistent(self):
        progress = Progression()
        for streak in range(1, 11):
            progress.reward_answer(question(str(streak)), 1, streak)
        self.assertEqual((progress.base_xp, progress.streak_xp, progress.achievement_xp), (100, 80, 100))
        self.assertEqual(progress.total_xp, 280)
        self.assertEqual((progress.level, progress.level_progress), (3, 80))
        progress.complete_quiz(10, 10, "mcq")
        self.assertEqual(progress.total_xp, 330)
        self.assertEqual((progress.level, progress.rank), (4, "Ethical Hacker"))

    def test_achievement_display_copies_do_not_mutate_catalog(self):
        progress = Progression()
        progress.reward_answer(question("first"), 1, 1)
        progress.achievements[0]["name"] = "changed"
        self.assertEqual(ACHIEVEMENTS["first_blood"]["name"], "FIRST BLOOD")


class SessionProgressionTests(unittest.TestCase):
    def setUp(self):
        use_starter_bank(self)
        self.original = deepcopy(QUESTION_BANK)

    def tearDown(self):
        self.assertEqual(QUESTION_BANK, self.original)

    def test_quiz_continues_after_zero_lives(self):
        quiz = QuizSession(1)
        for index in range(6):
            wrong = next(k for k, v in quiz.choices.items() if v != quiz.current_question["answer"])
            self.assertTrue(quiz.submit(wrong))
            self.assertEqual(quiz.progression.lives, max(0, 2 - index))
            self.assertEqual(quiz.advance(), index < 5)
        self.assertEqual(quiz.results["answered"], 6)
        self.assertTrue(quiz.progression.completed)

    def test_streak_resets_but_written_three_keeps_life(self):
        quiz = QuizSession(2, "easy", "all", "written")
        quiz.results["current_streak"] = 2
        quiz.submit_written("RA 10175")
        self.assertEqual(quiz.results["current_streak"], 0)
        self.assertEqual(quiz.progression.lives, 3)
        self.assertEqual(quiz.progression.base_xp, 12)

    def test_incomplete_session_cannot_finish_or_unlock_completion(self):
        quiz = QuizSession(mode="mixed")
        quiz.finish()
        self.assertFalse(quiz.progression.completed)
        self.assertIsNone(quiz.completion_reward)

    def test_complete_session_reward_and_replay_reset(self):
        quiz = QuizSession(2, "easy", "all", "written")
        quiz.submit_written("RA 10175 illegal access without permission")
        quiz.advance()
        self.assertIn("perfect_run", quiz.progression.unlocked_ids)
        total = quiz.progression.total_xp
        quiz.finish()
        quiz.advance()
        self.assertEqual(quiz.progression.total_xp, total)
        fresh = QuizSession(2, "easy", "all", "written")
        self.assertEqual(fresh.progression.total_xp, 0)
        self.assertEqual(fresh.progression.lives, 3)
        self.assertFalse(fresh.progression.unlocked_ids)


if __name__ == "__main__":
    unittest.main()
