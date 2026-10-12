"""Versioned, fault-tolerant JSON persistence and cumulative study statistics."""

import json
import logging
import math
import os
from pathlib import Path
import shutil
import tempfile
from datetime import datetime, timezone
from uuid import uuid4

if __package__:
    from .achievements import ACHIEVEMENTS
    from .progression import calculate_level, get_rank
    from .question_bank import get_question_by_id
else:
    from achievements import ACHIEVEMENTS
    from progression import calculate_level, get_rank
    from question_bank import get_question_by_id


SAVE_PATH = Path(__file__).resolve().parent / "data" / "stats.json"
SCHEMA_VERSION = 3


def create_default_stats() -> dict:
    """Return fresh dictionaries/lists each time, with no shared mutable state."""
    return {
        "version": SCHEMA_VERSION, "games_played": 0, "total_xp": 0,
        "best_streak": 0, "questions_answered": 0,
        "total_points_earned": 0, "total_points_possible": 0,
        "mcq": {"answered": 0, "correct": 0},
        "written": {"answered": 0, "points_earned": 0, "points_possible": 0, "perfect_answers": 0},
        "modules": {"1": {"earned": 0, "possible": 0}, "2": {"earned": 0, "possible": 0}},
        "topics": {}, "question_stats": {}, "mistake_ids": [], "achievements": [],
        "high_scores": {"overall_percentage": 0.0, "module_1_percentage": 0.0,
                        "module_2_percentage": 0.0, "mixed_percentage": 0.0},
        "high_score_counts": {"overall_percentage": 0, "module_1_percentage": 0,
                              "module_2_percentage": 0, "mixed_percentage": 0},
        # A bounded retry log prevents crediting a saved answer/completion twice.
        "recent_event_ids": [],
        "exams": {"completed": 0, "best_percentage": 0.0, "average_percentage": 0.0,
                  "total_percentage_sum": 0.0, "module_1_best": 0.0, "module_2_best": 0.0,
                  "both_best": 0.0, "last_score": 0.0, "module_1_completed": 0,
                  "module_2_completed": 0, "both_completed": 0},
        "exam_history": [],
    }


def _integer(value, default=0):
    # Implausibly large corrupted counters must not produce huge UI text/images.
    return min(value, 10**12) if type(value) is int and value >= 0 else default


def _mapping(value):
    return value if isinstance(value, dict) else {}


def _finite_number(value, maximum=100.0):
    if type(value) not in (int, float):
        return 0.0
    try:
        return min(maximum, max(0.0, float(value))) if math.isfinite(value) else 0.0
    except OverflowError:
        return 0.0


def _unique_strings(value):
    if not isinstance(value, list):
        return []
    return list(dict.fromkeys(item.strip() for item in value
                              if isinstance(item, str) and item.strip()))


def _points(value, attempts=False):
    value = _mapping(value)
    possible = _integer(value.get("possible"))
    result = {"earned": min(_integer(value.get("earned")), possible), "possible": possible}
    if attempts:
        result["attempts"] = _integer(value.get("attempts"))
    return result


def migrate_stats(raw) -> dict:
    """Fill missing fields and sanitize malformed nested values without trusting types."""
    raw = _mapping(raw)
    data = create_default_stats()
    for key in ("games_played", "total_xp", "best_streak", "questions_answered"):
        data[key] = _integer(raw.get(key))
    mcq = _mapping(raw.get("mcq"))
    # The original course schema had only general MCQ counters.
    legacy_count = data["questions_answered"] if "mcq" not in raw and "correct_answers" in raw else 0
    answered = _integer(mcq.get("answered"), legacy_count)
    data["mcq"] = {"answered": answered,
                   "correct": min(_integer(mcq.get("correct"), _integer(raw.get("correct_answers"))), answered)}
    written = _mapping(raw.get("written"))
    answered = _integer(written.get("answered"))
    possible = _integer(written.get("points_possible"), answered * 5)
    data["written"] = {"answered": answered, "points_possible": possible,
                       "points_earned": min(_integer(written.get("points_earned")), possible),
                       "perfect_answers": min(_integer(written.get("perfect_answers")), answered)}
    data["questions_answered"] = max(data["questions_answered"], data["mcq"]["answered"] + answered)
    possible = _integer(raw.get("total_points_possible"), data["mcq"]["answered"] + possible)
    earned = _integer(raw.get("total_points_earned"), data["mcq"]["correct"] + data["written"]["points_earned"])
    data["total_points_possible"] = possible
    data["total_points_earned"] = min(earned, possible)
    modules = _mapping(raw.get("modules"))
    for key in ("1", "2"):
        data["modules"][key] = _points(modules.get(key, modules.get(int(key))))
    for topic, counts in _mapping(raw.get("topics")).items():
        if isinstance(topic, str) and topic.strip():
            data["topics"][topic] = _points(counts, attempts=True)
    for identifier, counts in _mapping(raw.get("question_stats")).items():
        if not isinstance(identifier, str) or not identifier.strip():
            continue
        counts = _mapping(counts)
        attempts = _integer(counts.get("attempts"))
        possible = _integer(counts.get("points_possible"))
        data["question_stats"][identifier] = {
            "attempts": attempts, "successes": min(_integer(counts.get("successes")), attempts),
            "points_earned": min(_integer(counts.get("points_earned")), possible), "points_possible": possible,
        }
    data["mistake_ids"] = _unique_strings(raw.get("mistake_ids", raw.get("wrong_question_ids", [])))
    data["achievements"] = [item for item in _unique_strings(raw.get("achievements")) if item in ACHIEVEMENTS]
    highs = _mapping(raw.get("high_scores"))
    for key in data["high_scores"]:
        value = highs.get(key, raw.get("high_score", 0) if key == "overall_percentage" else 0)
        if type(value) in (int, float):
            try:
                if math.isfinite(value):
                    data["high_scores"][key] = min(100.0, max(0.0, float(value)))
            except OverflowError:
                pass
        fallback_count = data["games_played"] if key == "overall_percentage" else 0
        fallback_count = max(fallback_count, int(data["high_scores"][key] > 0))
        data["high_score_counts"][key] = _integer(_mapping(raw.get("high_score_counts")).get(key), fallback_count)
    data["recent_event_ids"] = _unique_strings(raw.get("recent_event_ids"))[-512:]
    exams = _mapping(raw.get("exams"))
    for key in ("completed", "module_1_completed", "module_2_completed", "both_completed"):
        data["exams"][key] = _integer(exams.get(key))
    for key in ("best_percentage", "module_1_best", "module_2_best", "both_best", "last_score"):
        data["exams"][key] = _finite_number(exams.get(key))
    count = data["exams"]["completed"]
    total = _finite_number(exams.get("total_percentage_sum"), count * 100.0)
    data["exams"]["total_percentage_sum"] = total
    data["exams"]["average_percentage"] = total / count if count else 0.0
    history = raw.get("exam_history", [])
    if isinstance(history, list):
        for row in history[-10:]:
            if not isinstance(row, dict):
                continue
            # Keep only summary fields; never retain question dictionaries/answers.
            data["exam_history"].append({
                "exam_id": str(row.get("exam_id", ""))[:64], "date": str(row.get("date", ""))[:40],
                "module": row.get("module") if type(row.get("module")) is int and row["module"] in (1, 2) else "both",
                "mode": row.get("mode") if row.get("mode") in ("mcq", "written", "mixed") else "mixed",
                "difficulty": row.get("difficulty") if row.get("difficulty") in ("easy", "medium", "hard", "all", "long_quiz") else "all",
                "score_earned": _integer(row.get("score_earned")), "score_possible": _integer(row.get("score_possible")),
                "percentage": _finite_number(row.get("percentage")), "question_count": _integer(row.get("question_count")),
                "answered": _integer(row.get("answered")), "unanswered": _integer(row.get("unanswered")),
                "flagged": _integer(row.get("flagged")), "time_used": _finite_number(row.get("time_used"), 10**12),
            })
    return data


def save_stats(data: dict, path=SAVE_PATH) -> bool:
    """Write UTF-8 JSON in the same folder, then atomically replace the save."""
    path = Path(path)
    temporary = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix="stats-", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(migrate_stats(data), stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        # Close the temporary file first: Windows cannot replace an open file.
        os.replace(temporary, path)
        return True
    except (OSError, ValueError, TypeError, RecursionError) as error:
        logging.warning("Progress could not be saved to %s: %s", path, error)
        return False
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass


def load_stats(path=SAVE_PATH, messages=None) -> dict:
    """Recover absent/empty/corrupt saves, preserving damaged bytes where possible."""
    path = Path(path)
    notices = messages if messages is not None else []
    raw = None
    needs_save = False
    try:
        raw = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(raw, dict):
            raise ValueError("Save root must be a JSON object")
        if _integer(raw.get("version")) > SCHEMA_VERSION:
            # Preserve unsupported future data before reading known fields.
            backup = path.with_name(f"{path.stem}.future.{uuid4().hex[:8]}.json")
            shutil.copy2(path, backup)
            notices.append("A newer save format was preserved in a backup.")
        data = migrate_stats(raw)
        needs_save = data != raw
    except FileNotFoundError:
        data = create_default_stats()
        needs_save = True
    except (json.JSONDecodeError, UnicodeError, ValueError, RecursionError):
        data = create_default_stats()
        backup = path.with_name(f"{path.stem}.corrupt.{uuid4().hex[:8]}.json")
        try:
            shutil.copy2(path, backup)
        except OSError:
            pass
        notices.append("Recovered an unreadable save. A backup was kept where possible.")
        needs_save = True
    except OSError as error:
        data = migrate_stats(raw)
        notices.append("Save access is unavailable. Progress is retained for this run.")
        logging.warning("Could not access save %s: %s", path, error)
    if needs_save and not save_stats(data, path):
        notices.append("Progress could not be saved. Check the save folder permissions.")
    for notice in notices:
        logging.warning("%s", notice)
    return data


def get_accuracy(earned: int, possible: int) -> float | None:
    """None means N/A when there have been no attempts."""
    return earned / possible * 100 if possible > 0 else None


def get_topic_stats(data: dict) -> list[dict]:
    """Sort topic point performance from lowest to highest, with N/A last."""
    topics = [{"topic": topic, **counts, "percentage": get_accuracy(counts["earned"], counts["possible"])}
              for topic, counts in data["topics"].items()]
    return sorted(topics, key=lambda row: (row["percentage"] is None,
                                           row["percentage"] or 0, row["topic"]))


def get_weak_topics(data: dict, minimum_attempts=2, threshold=70) -> list[dict]:
    """Only highlight low performance after at least two graded attempts."""
    return [row for row in get_topic_stats(data) if row["attempts"] >= minimum_attempts
            and row["percentage"] is not None and row["percentage"] < threshold]


def get_active_mistakes(data: dict, module=None, question_type=None) -> list[dict]:
    """Look up stable IDs, ignore removed questions, and return independent copies."""
    questions = []
    for identifier in _unique_strings(data.get("mistake_ids", [])):
        question = get_question_by_id(identifier)
        if question is not None and (module is None or question["module"] == module) \
                and (question_type is None or question["type"] == question_type):
            questions.append(question)
    return questions


class StatsStore:
    """Manage one save path; injecting a temporary path keeps tests isolated."""

    def __init__(self, path=SAVE_PATH):
        self.path = Path(path)
        messages = []
        self.data = load_stats(self.path, messages)
        self.warning = messages[-1] if messages else ""

    @property
    def level(self):
        return calculate_level(self.data["total_xp"])

    @property
    def rank(self):
        return get_rank(self.level)

    def save(self):
        saved = save_stats(self.data, self.path)
        self.warning = "" if saved else "Progress could not be saved. It is retained for this run."
        return saved

    def _remember(self, event_id):
        if event_id:
            self.data["recent_event_ids"].append(event_id)
            self.data["recent_event_ids"] = self.data["recent_event_ids"][-512:]

    def _add_reward(self, reward):
        """Recheck permanent unlocks, even if a caller used an unseeded session."""
        xp = _integer(reward.get("base_xp")) + _integer(reward.get("streak_xp"))
        unlocked = set(self.data["achievements"])
        for item in reward.get("achievements", []):
            identifier = item.get("id") if isinstance(item, dict) else item
            if identifier in ACHIEVEMENTS and identifier not in unlocked:
                unlocked.add(identifier)
                self.data["achievements"].append(identifier)
                xp += ACHIEVEMENTS[identifier]["xp"]
        self.data["total_xp"] += xp

    def record_answer(self, answer: dict, best_streak=0, event_id=None):
        """Save one graded attempt immediately, including unfinished-quiz progress."""
        if event_id and event_id in self.data["recent_event_ids"]:
            return self.save()
        self._apply_answer(answer, best_streak)
        self._remember(event_id)
        return self.save()

    def _apply_answer(self, answer, best_streak=0):
        """Apply an existing graded-attempt rule; caller chooses the save boundary."""
        identifier, kind = answer["id"], answer["type"]
        earned, possible = answer["earned_points"], answer["possible_points"]
        successful = earned == 1 if kind == "mcq" else earned >= 4
        self.data["questions_answered"] += 1
        self.data["total_points_earned"] += earned
        self.data["total_points_possible"] += possible
        self.data["best_streak"] = max(self.data["best_streak"], best_streak)
        if kind == "mcq":
            self.data["mcq"]["answered"] += 1
            self.data["mcq"]["correct"] += int(successful)
        else:
            counts = self.data["written"]
            counts["answered"] += 1
            counts["points_earned"] += earned
            counts["points_possible"] += possible
            counts["perfect_answers"] += int(earned == 5)
        for counts in (
            self.data["modules"].setdefault(str(answer["module"]), {"earned": 0, "possible": 0}),
            self.data["topics"].setdefault(answer["topic"], {"earned": 0, "possible": 0, "attempts": 0}),
        ):
            counts["earned"] += earned
            counts["possible"] += possible
            if "attempts" in counts:
                counts["attempts"] += 1
        counts = self.data["question_stats"].setdefault(identifier,
                 {"attempts": 0, "successes": 0, "points_earned": 0, "points_possible": 0})
        counts["attempts"] += 1
        counts["successes"] += int(successful)
        counts["points_earned"] += earned
        counts["points_possible"] += possible
        mistakes = set(self.data["mistake_ids"])
        if successful:
            mistakes.discard(identifier)
        else:
            mistakes.add(identifier)
        self.data["mistake_ids"] = sorted(mistakes)
        self._add_reward(answer.get("reward", {}))

    def record_completed_quiz(self, results: dict, reward: dict, event_id=None):
        """Credit final rewards/games/high scores once; answer XP is already saved."""
        if event_id and event_id in self.data["recent_event_ids"]:
            return self.save()
        if results["answered"] != results["planned"] or results["planned"] <= 0 or results["possible_points"] <= 0:
            return False
        self.data["games_played"] += 1
        self._add_reward(reward)
        percentage = get_accuracy(results["earned_points"], results["possible_points"])
        keys = ["overall_percentage"]
        if results["module"] in (1, 2):
            keys.append(f"module_{results['module']}_percentage")
        if results["mode"] == "mixed":
            keys.append("mixed_percentage")
        for key in keys:
            self.data["high_scores"][key] = max(self.data["high_scores"][key], percentage)
            self.data["high_score_counts"][key] += 1
        self._remember(event_id)
        return self.save()

    def get_active_mistakes(self, module=None, question_type=None):
        return get_active_mistakes(self.data, module, question_type)

    def record_exam(self, result, event_id=None):
        """Commit a submitted exam's attempts/rewards/summary in one atomic save.

Unanswered slots count as zero-point attempts and follow the existing mistake
rules. Exam completions/highs are separate from Study games/high scores.
Retrying a failed save cannot apply any reward or attempt a second time.
"""
        event_id = "exam:" + (event_id or result["exam_id"])
        if event_id in self.data["recent_event_ids"]:
            return self.save()
        if not result.get("answers") or len(result["answers"]) != result["question_count"]:
            return False
        for answer in result["answers"]:
            self._apply_answer(answer, result["best_streak"])
        self._add_reward(result["completion_reward"])
        exams = self.data["exams"]
        exams["completed"] += 1
        percentage = result["percentage"]
        exams["last_score"] = percentage
        exams["best_percentage"] = max(exams["best_percentage"], percentage)
        exams["total_percentage_sum"] += percentage
        exams["average_percentage"] = exams["total_percentage_sum"] / exams["completed"]
        prefix = f"module_{result['module']}" if result["module"] in (1, 2) else "both"
        exams[prefix + "_best"] = max(exams[prefix + "_best"], percentage)
        exams[prefix + "_completed"] += 1
        self.data["exam_history"].append({
            "exam_id": result["exam_id"], "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "module": result["module"] if result["module"] in (1, 2) else "both",
            "mode": result["mode"], "difficulty": result["difficulty"],
            "score_earned": result["earned_points"], "score_possible": result["possible_points"],
            "percentage": percentage, "question_count": result["question_count"],
            "answered": result["answered"], "unanswered": result["unanswered"],
            "flagged": result["flagged"], "time_used": result["time_used"],
        })
        self.data["exam_history"] = self.data["exam_history"][-10:]
        self._remember(event_id)
        return self.save()

    def reset(self):
        """Only replace in-memory progress after its confirmed reset is saved."""
        defaults = create_default_stats()
        if save_stats(defaults, self.path):
            self.data = defaults
            self.warning = ""
            return True
        self.warning = "Reset could not be saved. Your progress was kept."
        return False
