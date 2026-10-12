"""Deterministic coverage of normalization, concept groups, and partial credit."""

from copy import deepcopy
import unittest

from ite184_study_game.scorer import (
    normalize_answer, match_keyword_group, calculate_written_score, analyze_written_answer,
)
from ite184_study_game.question_bank import get_question_by_id, get_questions_by_type


class ScorerTests(unittest.TestCase):
    def setUp(self):
        self.access = get_question_by_id("M2_WR_001")

    def test_punctuation_case_and_whitespace(self):
        self.assertEqual(normalize_answer("RA 10175 - Illegal Access!!"), "ra 10175 illegal access")
        self.assertEqual(normalize_answer("   Illegal   Access \n"), "illegal access")
        self.assertTrue(match_keyword_group("RA 10175!!!", ["ra 10175"]))

    def test_numbers_and_law_notation_remain_meaningful(self):
        self.assertEqual(normalize_answer("9995, 11449 / 50"), "9995 11449 50")
        for value in ("RA10175", "R.A. 10175", "ra-10175", "ＲＡ １０１７５"):
            self.assertTrue(match_keyword_group(value, ["ra 10175"]), value)

    def test_hyphenated_and_latin_phrases(self):
        self.assertTrue(match_keyword_group("access-without-right", ["access without right"]))
        self.assertTrue(match_keyword_group("Dura lex, sed lex!", ["dura lex sed lex"]))

    def test_whole_tokens_prevent_accidental_substrings(self):
        self.assertFalse(match_keyword_group("lawful claw", ["law"]))
        self.assertFalse(match_keyword_group("ra 101750", ["ra 10175"]))
        self.assertFalse(match_keyword_group("interceptionist", ["interception"]))
        self.assertFalse(match_keyword_group("illegal accessing", ["illegal access"]))
        self.assertFalse(match_keyword_group("anything", [""]))

    def test_one_synonym_satisfies_a_group(self):
        grade = analyze_written_answer(self.access, "Cybercrime Prevention Act unauthorized access")
        self.assertEqual(len(grade["matched_groups"]), 2)
        self.assertEqual(grade["missed_groups"], [])
        self.assertEqual(grade["score"], 4)

    def test_two_synonyms_do_not_double_count(self):
        grade = analyze_written_answer(self.access, "RA 10175 Cybercrime Prevention Act")
        self.assertEqual(len(grade["matched_groups"]), 1)
        self.assertEqual(len(grade["missed_groups"]), 1)
        self.assertLess(grade["score"], 4)

    def test_all_required_and_reasoning_is_five(self):
        grade = analyze_written_answer(self.access, "RA 10175 illegal access without permission")
        self.assertEqual(grade["score"], 5)
        self.assertEqual(grade["percentage"], 100)
        self.assertIn("without permission", grade["matched_optional"])

    def test_all_required_without_reasoning_is_four(self):
        grade = analyze_written_answer(self.access, "RA 10175 illegal access")
        self.assertEqual(grade["score"], 4)
        self.assertEqual(grade["label"], "GREAT")
        self.assertEqual(grade["percentage"], 80)

    def test_partial_coverage_and_other_group_counts(self):
        for matched, total, score in ((3, 4, 3), (2, 4, 3), (1, 4, 2), (1, 2, 3),
                                      (1, 1, 4), (0, 2, 0), (0, 0, 0)):
            self.assertEqual(calculate_written_score(matched, total, 0, 2), score)

    def test_no_optional_keywords_requires_no_bonus(self):
        question = {"keyword_groups": [["virtue ethics"]], "optional_keywords": []}
        self.assertEqual(analyze_written_answer(question, "Virtue ethics")["score"], 5)

    def test_optional_only_is_at_most_one(self):
        self.assertEqual(analyze_written_answer(self.access, "password without permission")["score"], 1)

    def test_unrelated_blank_or_punctuation_only_is_zero(self):
        for answer in ("I like bananas", "", " \n\t ", "!!!"):
            self.assertEqual(analyze_written_answer(self.access, answer)["score"], 0)

    def test_data_interference_and_multiple_required_offenses(self):
        question = {"keyword_groups": [["ra 10175"], ["data interference", "altering data"]],
                    "optional_keywords": ["without right"]}
        self.assertEqual(analyze_written_answer(question, "RA 10175 data interference")["score"], 4)
        # The real grade-changing scenario additionally requires Illegal Access and reasoning.
        grade = analyze_written_answer(get_question_by_id("M2_WR_002"), "RA 10175 data interference")
        self.assertEqual(grade["score"], 3)
        self.assertEqual(len(grade["missed_groups"]), 2)

    def test_voyeurism_reasonable_sharing_synonym(self):
        grade = analyze_written_answer(get_question_by_id("M2_WR_003"),
            "RA 9995 consent to recording does not mean consent to sharing")
        self.assertGreaterEqual(grade["score"], 4)
        self.assertFalse(grade["missed_groups"])
        self.assertFalse(match_keyword_group("sharing", ["consent to recording does not equal consent to distribution"]))

    def test_safe_spaces_course_example(self):
        # These laws currently have MCQs, so test a written schema fixture without editing the bank.
        question = {"keyword_groups": [["ra 11313", "safe spaces act"], ["online sexual harassment"]],
                    "optional_keywords": ["cyberstalking"]}
        self.assertEqual(analyze_written_answer(question,
            "RA 11313 online sexual harassment cyberstalking")["score"], 5)

    def test_osaec_course_example(self):
        question = {"keyword_groups": [["ra 11930"], ["online sexual exploitation of a child", "osaec"]],
                    "optional_keywords": []}
        self.assertEqual(analyze_written_answer(question,
            "RA 11930 online sexual exploitation of a child")["score"], 5)

    def test_all_three_latin_maxims_accept_punctuation(self):
        for question_id, answer in (("M1_WR_001", "Ignorantia legis neminem excusat!"),
            ("M1_WR_002", "Nullum crimen, nulla poena sine lege."),
            ("M1_WR_003", "Dura lex, sed lex!")):
            grade = analyze_written_answer(get_question_by_id(question_id), answer)
            self.assertEqual(grade["score"], 3)  # Name identified; requested meaning still missing.
            self.assertEqual(len(grade["matched_groups"]), 1)

    def test_stored_models_identify_all_required_concepts(self):
        for question in get_questions_by_type("written"):
            with self.subTest(question=question["id"]):
                grade = analyze_written_answer(question, question["model_answer"])
                self.assertFalse(grade["missed_groups"])
                self.assertGreaterEqual(grade["score"], 4)

    def test_original_question_and_answer_are_preserved(self):
        original = deepcopy(self.access)
        answer = "  RA 10175!! Illegal Access.  "
        analyze_written_answer(self.access, answer)
        self.assertEqual(self.access, original)
        self.assertEqual(answer, "  RA 10175!! Illegal Access.  ")


if __name__ == "__main__":
    unittest.main()
