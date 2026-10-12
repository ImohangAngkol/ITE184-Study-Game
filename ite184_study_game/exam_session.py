"""Mutable exam answers/navigation and monotonic deadlines; grading is deferred."""

from copy import deepcopy
import math
import time
from uuid import uuid4

if __package__:
    from .exam_engine import prepare_exam, grade_exam
else:
    from exam_engine import prepare_exam, grade_exam


def validate_timer(minutes):
    if minutes is not None and (type(minutes) is not int or not 1 <= minutes <= 180):
        raise ValueError("Timer must be a whole number from 1 to 180 minutes, or no timer.")
    return None if minutes is None else minutes * 60


def format_time(seconds):
    if seconds is None:
        return "No timer"
    seconds = max(0, math.ceil(seconds))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


class ExamSession:
    def __init__(self, module=None, mode="mixed", difficulty="all", question_count=30,
                 timer_minutes=None, stats_store=None, *, clock=None, rng=None, questions=None):
        self.timer_duration = validate_timer(timer_minutes)
        self.module, self.mode, self.difficulty = module, mode, difficulty
        self.questions = prepare_exam(module, mode, difficulty, question_count, rng=rng, questions=questions)
        self.question_count = len(self.questions)
        self.exam_id = uuid4().hex
        self.clock = clock or time.monotonic
        self.start_time = self.clock()
        self.current_question_index = 0
        self.answers, self.flags = {}, set()
        self.visited_ids = {self.questions[0]["id"]}
        self.submitted = self.abandoned = self.auto_submitted = False
        self.results = None
        self.stats_store = stats_store
        self.finished_elapsed = None

    @property
    def current_question(self):
        return self.questions[self.current_question_index]

    @property
    def player_question(self):
        """Only visible fields: no answer, model, subtopic, explanation or keywords."""
        question = self.current_question
        return deepcopy({key: question[key] for key in
                         ("id", "module", "type", "topic", "question", "scenario", "exam_choices") if key in question})

    @property
    def elapsed(self):
        return self.finished_elapsed if self.finished_elapsed is not None else max(0, self.clock() - self.start_time)

    @property
    def remaining_time(self):
        return None if self.timer_duration is None else max(0, self.timer_duration - self.elapsed)

    @property
    def unanswered_ids(self):
        return [q["id"] for q in self.questions if not self.answers.get(q["id"], "").strip()]

    @property
    def flagged_ids(self):
        return [q["id"] for q in self.questions if q["id"] in self.flags]

    def confirmation(self):
        return {"answered": self.question_count - len(self.unanswered_ids), "unanswered": len(self.unanswered_ids),
                "flagged": len(self.flags), "total": self.question_count, "remaining_time": self.remaining_time}

    def tick(self):
        if not self.submitted and not self.abandoned and self.timer_duration is not None and self.remaining_time <= 0:
            self.submit(auto=True)
            return True
        return False

    def set_answer(self, answer):
        self.tick()
        if self.submitted or self.abandoned or not isinstance(answer, str):
            return False
        if self.current_question["type"] == "mcq" and answer and answer not in self.current_question["choices"]:
            return False
        self.answers[self.current_question["id"]] = answer
        return True

    def select_choice(self, letter):
        choice = self.current_question.get("exam_choices", {}).get(letter)
        return self.set_answer(choice) if choice is not None else False

    def jump(self, index):
        self.tick()
        if self.submitted or self.abandoned or type(index) is not int or not 0 <= index < self.question_count:
            return False
        self.current_question_index = index
        self.visited_ids.add(self.current_question["id"])
        return True

    def previous(self):
        return self.jump(self.current_question_index - 1)

    def next(self):
        return self.jump(self.current_question_index + 1)

    def toggle_flag(self):
        self.tick()
        if self.submitted or self.abandoned:
            return False
        identifier = self.current_question["id"]
        if identifier in self.flags:
            self.flags.remove(identifier)
        else:
            self.flags.add(identifier)
        return True

    def abandon(self):
        if self.submitted:
            return False
        self.abandoned = True
        self.finished_elapsed = self.elapsed
        return True

    def submit(self, auto=False):
        if self.abandoned:
            return None
        if self.submitted:
            # Retry an atomic save without grading or granting rewards twice.
            if self.stats_store:
                self.stats_store.record_exam(self.results, event_id=self.exam_id)
            return self.results
        elapsed = self.elapsed
        self.finished_elapsed = min(elapsed, self.timer_duration) if self.timer_duration is not None else elapsed
        result = grade_exam(self.questions, self.answers, self.flags,
                            unlocked_ids=self.stats_store.data["achievements"] if self.stats_store else ())
        result.update({"exam_id": self.exam_id, "module": self.module, "mode": self.mode,
                       "difficulty": self.difficulty, "time_used": self.finished_elapsed,
                       "timer_duration": self.timer_duration, "auto_submitted": auto})
        self.results, self.submitted, self.auto_submitted = result, True, auto
        if self.stats_store:
            self.stats_store.record_exam(result, event_id=self.exam_id)
        return result

    def review_indices(self, filter_name="all"):
        if not self.submitted:
            return []
        if filter_name not in ("all", "partial", "flagged", "unanswered"):
            raise ValueError("Unknown exam review filter.")
        return [index for index, answer in enumerate(self.results["answers"])
                if filter_name == "all" or (filter_name == "partial" and answer["earned_points"] < answer["possible_points"])
                or (filter_name == "flagged" and answer["flagged"])
                or (filter_name == "unanswered" and answer["unanswered"])]
