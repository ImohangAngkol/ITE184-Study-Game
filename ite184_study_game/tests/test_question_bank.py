"""Phase 8 coverage against the real expanded bank (no starter-pool patch)."""

from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from ite184_study_game import question_bank as bank
from ite184_study_game.content_audit import VALID_TOPICS, audit_question_bank
from ite184_study_game.question_selection import prepare_questions
from ite184_study_game.quiz_engine import prepare_mcq_questions
from ite184_study_game.scorer import analyze_written_answer, normalize_answer
from ite184_study_game.stats import StatsStore, create_default_stats
from ite184_study_game.tests.starter_fixture import STARTER_QUESTIONS
from ite184_study_game.ui.session import QuizSession


class FullQuestionBankTests(unittest.TestCase):
    def setUp(self):
        self.questions = bank.get_all_questions()

    def content(self, topic=None):
        return normalize_answer(" ".join(
            " ".join(str(q.get(key, "")) for key in
                     ("subtopic", "question", "scenario", "answer", "model_answer", "explanation"))
            for q in self.questions if topic is None or q["topic"] == topic))

    def test_minimum_final_count(self):
        self.assertGreaterEqual(len(self.questions), 260)

    def test_module_one_target(self):
        self.assertGreaterEqual(len(bank.get_questions_by_module(1)), 75)

    def test_module_two_target(self):
        self.assertGreaterEqual(len(bank.get_questions_by_module(2)), 185)

    def test_module_mcq_targets(self):
        for module, target in ((1, 45), (2, 110)):
            with self.subTest(module=module):
                self.assertGreaterEqual(len(bank.filter_questions(module, "mcq")), target)

    def test_module_written_targets(self):
        for module, target in ((1, 30), (2, 75)):
            with self.subTest(module=module):
                self.assertGreaterEqual(len(bank.filter_questions(module, "written")), target)

    def test_ids_are_unique(self):
        self.assertEqual(len(self.questions), len({q["id"] for q in self.questions}))

    def test_all_old_ids_preserved(self):
        self.assertEqual(len(STARTER_QUESTIONS), 26)
        self.assertTrue({q["id"] for q in STARTER_QUESTIONS} <= {q["id"] for q in self.questions})

    def test_original_dictionaries_unchanged(self):
        for original in STARTER_QUESTIONS:
            with self.subTest(question=original["id"]):
                self.assertEqual(bank.get_question_by_id(original["id"]), original)

    def test_topics_are_canonical(self):
        for question in self.questions:
            self.assertIn(question["topic"], VALID_TOPICS[question["module"]])

    def test_all_canonical_topics_have_content(self):
        for module, expected in VALID_TOPICS.items():
            actual = {q["topic"] for q in bank.get_questions_by_module(module)}
            self.assertEqual(actual, expected)

    def test_four_unique_choices_per_mcq(self):
        for question in bank.get_questions_by_type("mcq"):
            with self.subTest(question=question["id"]):
                self.assertEqual(len(question["choices"]), 4)
                self.assertEqual(len({normalize_answer(c) for c in question["choices"]}), 4)

    def test_every_mcq_answer_exists(self):
        for question in bank.get_questions_by_type("mcq"):
            self.assertIn(question["answer"], question["choices"], question["id"])

    def test_nonempty_written_groups(self):
        for question in bank.get_questions_by_type("written"):
            self.assertTrue(question["keyword_groups"], question["id"])
            for group in question["keyword_groups"]:
                self.assertTrue(group)
                self.assertTrue(all(isinstance(p, str) and p.strip() for p in group))

    def test_nonempty_written_models(self):
        for question in bank.get_questions_by_type("written"):
            self.assertTrue(question["model_answer"].strip(), question["id"])

    def test_all_models_match_required_concepts(self):
        for question in bank.get_questions_by_type("written"):
            with self.subTest(question=question["id"]):
                grade = analyze_written_answer(question, question["model_answer"])
                self.assertEqual(grade["missed_groups"], [])
                self.assertGreaterEqual(grade["score"], 4)

    def test_difficulty_balance(self):
        counts = Counter(q["difficulty"] for q in self.questions)
        for difficulty, target in (("easy", .30), ("medium", .40), ("hard", .30)):
            self.assertAlmostEqual(counts[difficulty] / len(self.questions), target, delta=.03)

    def test_every_module_type_has_each_difficulty(self):
        for module in (1, 2):
            for kind in ("mcq", "written"):
                self.assertEqual({q["difficulty"] for q in bank.filter_questions(module, kind)},
                                 {"easy", "medium", "hard"})

    def test_both_modules_represented(self):
        self.assertEqual({q["module"] for q in self.questions}, {1, 2})

    def test_eight_crime_categories_covered(self):
        text = self.content("Types of Computer Crime")
        for category in ("harassment", "unauthorized access", "theft of goods", "forgery and piracy",
                         "theft of computer time", "computer espionage", "fraud", "identity theft"):
            self.assertIn(category, text)

    def test_all_supplied_laws_covered(self):
        text = self.content()
        for law in (8792, 10175, 10173, 9995, 11313, 11930, 9775, 8484, 11449, 8293, 11055, 11934, 11479):
            self.assertIn(f"ra {law}", text)

    def test_all_hacking_cases_covered(self):
        text = self.content("Hacking Cases")
        for case in ("kevin mitnick", "raphael gray", "masters of deception", "mafiaboy",
                     "legion of doom", "morris", "anonymous philippines"):
            self.assertIn(case, text)

    def test_all_malware_cases_covered(self):
        text = self.content("Malware Cases")
        for case in ("nimda", "iloveyou", "melissa", "code red", "anna kournikova", "mydoom"):
            self.assertIn(case, text)

    def test_all_three_maxims_covered(self):
        text = self.content("Legal Maxims")
        for maxim in ("ignorantia legis neminem excusat", "nullum crimen nulla poena sine lege", "dura lex sed lex"):
            self.assertIn(maxim, text)

    def test_all_eight_theories_covered(self):
        text = self.content("Ethical Theories")
        for theory in ("divine command", "cultural relativism", "virtue ethics", "contractarianism",
                       "utilitarianism", "consequentialism", "deontology", "kantian"):
            self.assertIn(theory, text)

    def test_all_malware_types_covered(self):
        text = self.content("Malware")
        for kind in ("virus", "worm", "trojan", "logic bomb", "time bomb", "backdoor", "trapdoor",
                     "spyware", "keylogger", "ransomware", "botnet", "dos", "ddos", "rootkit"):
            self.assertIn(kind, text)

    def test_validator_passes(self):
        self.assertEqual(bank.validate_question_bank(), (True, []))

    def test_full_quality_audit_passes_without_warnings(self):
        report = audit_question_bank()
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["warnings"], [])
        self.assertEqual(report["written_models_checked"], len(bank.get_questions_by_type("written")))

    def test_summary_matches_actual_counts(self):
        summary = bank.get_question_bank_summary()
        self.assertEqual(summary["total"], summary["mcq"] + summary["written"])
        self.assertEqual(summary["total"], summary["module_1"] + summary["module_2"])
        self.assertEqual(summary["total"], sum(summary[k] for k in ("easy", "medium", "hard")))
        self.assertEqual(summary["topics"], dict(Counter(q["topic"] for q in self.questions)))

    def test_copies_protect_expansion_nested_data(self):
        original = bank.get_question_by_id("M2_WR_075")
        copy = bank.get_question_by_id("M2_WR_075")
        copy["keyword_groups"][0].append("local edit")
        self.assertEqual(bank.get_question_by_id("M2_WR_075"), original)
        selected = bank.filter_questions(1, "mcq")
        selected[-1]["choices"].append("local edit")
        self.assertEqual(len(bank.get_question_by_id(selected[-1]["id"])["choices"]), 4)

    def test_all_mode_filter_and_count_combinations(self):
        for module in (1, 2, None):
            for difficulty in ("easy", "medium", "hard", "all"):
                for mode in ("mcq", "written", "mixed"):
                    for count in (5, 10, 20, "all"):
                        with self.subTest(module=module, difficulty=difficulty, mode=mode, count=count):
                            pool = bank.filter_questions(module, None if mode == "mixed" else mode,
                                                         None if difficulty == "all" else difficulty)
                            selected = prepare_questions(module, difficulty, count, mode)
                            self.assertEqual(len(selected), len(pool) if count == "all" else min(count, len(pool)))
                            self.assertEqual(len(selected), len({q["id"] for q in selected}))
                            self.assertTrue({q["id"] for q in selected} <= {q["id"] for q in pool})

    def test_expanded_terminal_mcq_pools(self):
        for module, target in ((1, 45), (2, 110), (None, 155)):
            selected = prepare_mcq_questions(module, "all", "all")
            self.assertEqual(len(selected), target)

    def test_balanced_twenty_question_mixed_quiz(self):
        for module in (1, 2, None):
            selected = prepare_questions(module, "all", 20, "mixed")
            self.assertEqual(Counter(q["type"] for q in selected), {"mcq": 10, "written": 10})

    def test_complete_expanded_mixed_quiz_point_accounting(self):
        quiz = QuizSession(mode="mixed")
        original = bank.get_all_questions()
        for _ in range(len(quiz.questions)):
            if quiz.current_question["type"] == "written":
                quiz.submit_written(quiz.current_question["model_answer"])
            else:
                quiz.submit(next(k for k, v in quiz.choices.items() if v == quiz.current_question["answer"]))
            quiz.advance()
        self.assertEqual(quiz.results["answered"], len(self.questions))
        expected_points = sum(5 if q["type"] == "written" else 1 for q in self.questions)
        self.assertEqual(quiz.results["possible_points"], expected_points)
        self.assertGreaterEqual(quiz.results["earned_points"], expected_points - len(bank.get_questions_by_type("written")))
        self.assertTrue(quiz.progression.completed)
        self.assertEqual(bank.get_all_questions(), original)

    def test_phase_seven_save_reopens_with_old_and_new_mistakes(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "stats.json"
            old_save = create_default_stats()
            old_save["total_xp"] = 321
            old_save["games_played"] = 2
            old_save["mistake_ids"] = [q["id"] for q in STARTER_QUESTIONS]
            old_save["topics"]["Basic Concepts"] = {"earned": 0, "possible": 1, "attempts": 1}
            old_save["question_stats"]["M1_MCQ_001"] = {
                "attempts": 1, "successes": 0, "points_earned": 0, "points_possible": 1}
            path.write_text(json.dumps(old_save), encoding="utf-8")
            store = StatsStore(path)
            self.assertEqual(len(store.get_active_mistakes()), 26)
            quiz = QuizSession(mode="written", stats_store=store,
                               questions=[bank.get_question_by_id("M2_WR_075")])
            quiz.submit_written("I don't know")
            quiz.advance()
            reopened = StatsStore(path)
            self.assertGreaterEqual(reopened.data["total_xp"], 321)
            self.assertEqual(reopened.data["games_played"], 3)
            self.assertEqual(reopened.data["question_stats"]["M1_MCQ_001"], old_save["question_stats"]["M1_MCQ_001"])
            self.assertTrue({q["id"] for q in STARTER_QUESTIONS} <= set(reopened.data["mistake_ids"]))
            self.assertIn("M2_WR_075", reopened.data["mistake_ids"])
            self.assertEqual(reopened.data["topics"]["Basic Concepts"], old_save["topics"]["Basic Concepts"])


class ContentAuditTests(unittest.TestCase):
    def test_duplicate_id_and_normalized_prompt_detected(self):
        first = bank.get_question_by_id("M1_MCQ_007")
        second = deepcopy(first)
        second["question"] = first["question"].upper() + "!!"
        errors = audit_question_bank([first, second])["errors"]
        self.assertTrue(any("Duplicate ID" in e for e in errors))
        self.assertTrue(any("Duplicate prompt" in e for e in errors))

    def test_duplicate_written_scenarios_detected(self):
        first = bank.get_question_by_id("M1_WR_005")
        second = deepcopy(first)
        second["id"] = "M1_WR_999"
        self.assertTrue(any("Duplicate prompt/scenario" in e for e in audit_question_bank([first, second])["errors"]))

    def test_excessive_choice_set_reuse_is_a_review_warning(self):
        pool = []
        for index in range(9):
            question = bank.get_question_by_id("M1_MCQ_007")
            question["id"] = f"M1_MCQ_{900 + index}"
            question["question"] = f"Unique content audit exercise {index}"
            pool.append(question)
        report = audit_question_bank(pool)
        self.assertEqual(report["errors"], [])
        self.assertTrue(any("Excessive" in w for w in report["warnings"]))

    def test_malformed_keyword_groups_do_not_crash_audit(self):
        for groups in (None, [], [[]], [["  "]], ["not a group"], [[123]]):
            question = bank.get_question_by_id("M1_WR_005")
            question["keyword_groups"] = groups
            self.assertTrue(any("malformed keyword groups" in e for e in audit_question_bank([question])["errors"]))

    def test_cross_group_synonym_reuse_detected(self):
        question = bank.get_question_by_id("M1_WR_005")
        question["keyword_groups"] = [["moral"], ["MORAL!"]]
        self.assertTrue(any("different concept groups" in e for e in audit_question_bank([question])["errors"]))

    def test_model_missing_required_concept_detected(self):
        question = bank.get_question_by_id("M1_WR_005")
        question["model_answer"] = "I do not know."
        self.assertTrue(any("model misses" in e for e in audit_question_bank([question])["errors"]))

    def test_shared_topics_are_not_failures(self):
        pool = bank.filter_questions(2, topic="Cybercrime")
        self.assertGreater(len(pool), 8)
        self.assertEqual(audit_question_bank(pool)["errors"], [])

    def test_invalid_topic_and_id_mismatch_detected(self):
        question = bank.get_question_by_id("M1_MCQ_007")
        question["topic"] = "Cyber Crime"
        question["id"] = "M2_WR_999"
        errors = audit_question_bank([question])["errors"]
        self.assertTrue(any("noncanonical topic" in e for e in errors))
        self.assertTrue(any("ID/module/type mismatch" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
