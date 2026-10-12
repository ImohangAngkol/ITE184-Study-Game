"""Pygame-free session model shared by UI events and automated tests."""

from copy import deepcopy
import random
from uuid import uuid4

# The parent differs when ui is imported by pygame_main.py as a script.
if "." in __package__:
    from ..quiz_engine import prepare_mcq_questions, shuffle_choices
    from ..quiz_engine import create_quiz_results, record_answer
    from ..question_bank import validate_question_bank
    from ..question_selection import prepare_questions, possible_points
    from ..scorer import analyze_written_answer
    from ..progression import Progression
else:
    from quiz_engine import prepare_mcq_questions, shuffle_choices
    from quiz_engine import create_quiz_results, record_answer
    from question_bank import validate_question_bank
    from question_selection import prepare_questions, possible_points
    from scorer import analyze_written_answer
    from progression import Progression


class QuizSession:
    """Own one quiz's copied questions, locked answer, counters, and history."""

    def __init__(self, module=None, difficulty="all", question_count="all", mode="mcq",
                 stats_store=None, questions=None, review=False):
        valid, errors = validate_question_bank()
        if not valid:
            raise ValueError("Question bank validation failed: " + "; ".join(errors))
        self.selected_module = module
        self.selected_difficulty = difficulty
        self.question_count = question_count
        self.mode = mode
        self.stats_store = stats_store
        self.session_id = uuid4().hex
        self.is_review = review
        self.start_level = stats_store.level if stats_store else 1
        # Preserve the existing MCQ path and its regression tests.
        self.questions = (deepcopy(questions) if questions is not None else
                          prepare_mcq_questions(module, difficulty, question_count)
                          if mode == "mcq" else
                          prepare_questions(module, difficulty, question_count, mode))
        if questions is not None:
            random.shuffle(self.questions)
        if not self.questions:
            kind = "MCQ" if mode == "mcq" else mode
            raise ValueError(f"No matching {kind} questions are currently available.")
        self.current_question_index = 0
        self.results = create_quiz_results(module, difficulty, len(self.questions))
        self.results.update({"mode": mode, "earned_points": 0, "answered_points": 0,
                             "possible_points": sum(possible_points(q) for q in self.questions),
                             "point_topics": {}, "point_modules": {},
                             "type_points": {"mcq": {"earned": 0, "possible": 0},
                                             "written": {"earned": 0, "possible": 0}}})
        self.answers = []
        self.progression = Progression(stats_store.data["achievements"] if stats_store else ())
        self.completion_reward = None
        self.selected_answer = None
        self.choices = self._prepare_choices()

    def _prepare_choices(self):
        """Written questions have no answer choices to shuffle."""
        return shuffle_choices(self.current_question) if self.current_question["type"] == "mcq" else {}

    @property
    def current_question(self):
        """Read the current question without duplicating index logic in screens."""
        return self.questions[self.current_question_index]

    @property
    def is_last_question(self) -> bool:
        return self.current_question_index == len(self.questions) - 1

    def submit(self, letter: str) -> bool:
        """Record one valid answer; repeated or invalid submissions do nothing."""
        letter = letter.strip().upper()
        if self.current_question["type"] != "mcq" or self.selected_answer is not None or letter not in self.choices:
            return False
        self.selected_answer = letter
        correct = self.choices[letter] == self.current_question["answer"]
        self._record(self.choices[letter], int(correct), 1, correct, letter=letter)
        return True

    def submit_written(self, answer: str) -> bool:
        """Reject blank/repeated answers; grade a copy and lock the original text."""
        if (self.current_question["type"] != "written" or self.selected_answer is not None
                or not answer.strip()):
            return False
        grading = analyze_written_answer(self.current_question, answer)
        self.selected_answer = answer
        self._record(answer, grading["score"], 5, grading["score"] >= 4, grading=grading)
        return True

    def _record(self, answer, earned, possible, successful, **details):
        """Keep legacy success counters and new point totals separately."""
        question = self.current_question
        record_answer(self.results, question, successful)
        self.results["earned_points"] += earned
        self.results["answered_points"] += possible
        for breakdown, key in ((self.results["point_topics"], question["topic"]),
                               (self.results["point_modules"], question["module"]),
                               (self.results["type_points"], question["type"])):
            counts = breakdown.setdefault(key, {"earned": 0, "possible": 0})
            counts["earned"] += earned
            counts["possible"] += possible
        self.answers.append({"id": question["id"], "type": question["type"],
                             "module": question["module"], "topic": question["topic"],
                             "subtopic": question["subtopic"], "possible_points": possible,
                             "earned_points": earned, "answer": answer, "correct": successful,
                             "grading": None, **details})
        self.answers[-1]["reward"] = self.progression.reward_answer(
            question, earned, self.results["current_streak"])
        if self.stats_store:
            self.answers[-1]["mastered"] = (self.is_review and successful
                and question["id"] in self.stats_store.data["mistake_ids"])
            self.stats_store.record_answer(self.answers[-1], self.results["best_streak"],
                                           f"{self.session_id}:{question['id']}")

    def advance(self) -> bool:
        """Move after feedback; return False when the completed quiz is finished."""
        if self.selected_answer is None:
            return False
        if self.is_last_question:
            self.finish()
            return False
        self.current_question_index += 1
        self.selected_answer = None
        self.choices = self._prepare_choices()
        return True

    def finish(self):
        """Finalize once after all questions are answered; never reward abandonment."""
        if self.results["answered"] == len(self.questions) and self.completion_reward is None:
            self.completion_reward = self.progression.complete_quiz(
                self.results["earned_points"], self.results["possible_points"], self.mode)
            if self.stats_store:
                self.stats_store.record_completed_quiz(self.results, self.completion_reward,
                                                       f"{self.session_id}:complete")
