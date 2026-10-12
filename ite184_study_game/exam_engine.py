"""Offline exam preparation and final grading; no Pygame or storage side effects."""

from collections import Counter, defaultdict
from copy import deepcopy
import random

if __package__:
    from .question_bank import filter_questions, validate_question_bank
    from .scorer import analyze_written_answer
    from .quiz_engine import calculate_percentage, get_performance_label
    from .progression import Progression
else:
    from question_bank import filter_questions, validate_question_bank
    from scorer import analyze_written_answer
    from quiz_engine import calculate_percentage, get_performance_label
    from progression import Progression

DIFFICULTIES = ("easy", "medium", "hard")
ATTY_PRESET = {"module": None, "mode": "mixed", "difficulty": "long_quiz",
               "question_count": 30, "timer_minutes": 45}


def exam_pool(module=None, mode="mixed", difficulty="all", questions=None):
    if module is not None and (type(module) is not int or module not in (1, 2)):
        raise ValueError("Module must be 1, 2, or both.")
    if mode not in ("mcq", "written", "mixed"):
        raise ValueError("Choose MCQ, written, or mixed.")
    if difficulty not in (*DIFFICULTIES, "all", "long_quiz"):
        raise ValueError("Choose a valid exam difficulty.")
    if questions is None:
        valid, errors = validate_question_bank()
        if not valid:
            raise ValueError("Question bank validation failed: " + "; ".join(errors))
        pool = filter_questions(module, None if mode == "mixed" else mode,
                                difficulty if difficulty in DIFFICULTIES else None)
    else:
        pool = deepcopy([q for q in questions if (module is None or q["module"] == module)
                         and (mode == "mixed" or q["type"] == mode)
                         and (difficulty not in DIFFICULTIES or q["difficulty"] == difficulty)])
    # Safely collapse repeated supplied IDs; bank validation rejects source duplicates.
    return list({q["id"]: q for q in pool}.values())


def allocate_counts(total, weights, capacities):
    """Largest-deficit allocation with capacity-aware shortage redistribution."""
    counts = dict.fromkeys(weights, 0)
    weight_sum = sum(weights.values()) or 1
    ideals = {key: total * value / weight_sum for key, value in weights.items()}
    for _ in range(min(total, sum(capacities.values()))):
        available = [key for key in counts if counts[key] < capacities.get(key, 0)]
        key = max(available, key=lambda k: ideals[k] - counts[k])
        counts[key] += 1
    return counts


def prepare_exam(module=None, mode="mixed", difficulty="all", question_count=30,
                 *, rng=None, questions=None):
    """Prepare a copied, stable question/choice snapshot without grading.

Difficulty/type quotas are solved across six cells. Module quotas are then
allocated within those cells. Capacity constraints redistribute shortages;
when margins conflict, the closest feasible type/module balance is used.
The UI confirms a reduced count before calling this function.
"""
    pool = exam_pool(module, mode, difficulty, questions)
    if not pool:
        raise ValueError("No questions match this exam selection.")
    if question_count != "all" and (type(question_count) is not int or question_count < 1):
        raise ValueError("Question count must be a positive whole number or all.")
    count = len(pool) if question_count == "all" else min(question_count, len(pool))
    rng = rng or random
    capacities = Counter(q["difficulty"] for q in pool)
    weights = dict(zip(DIFFICULTIES, (1, 2, 2))) if difficulty == "long_quiz" else {
        key: capacities[key] for key in DIFFICULTIES}
    quotas = allocate_counts(count, weights, capacities)
    cells = defaultdict(list)
    for question in pool:
        cells[(question["difficulty"], question["type"], question["module"])].append(question)
    bounds = {}
    for tier in DIFFICULTIES:
        mcq_capacity = sum(len(cells[tier, "mcq", mod]) for mod in (1, 2))
        written_capacity = sum(len(cells[tier, "written", mod]) for mod in (1, 2))
        bounds[tier] = (max(0, quotas[tier] - written_capacity), min(quotas[tier], mcq_capacity))
    target_mcq = (count if mode == "mcq" else 0 if mode == "written" else
                  count // 2 + (count % 2 if rng.choice((True, False)) else 0))
    target_m1 = count if module == 1 else 0 if module == 2 else max(1, round(count / 3))
    if module is None and count > 1:
        target_m1 = min(count - 1, target_m1)
    best, best_score = [], None
    # Small bounded quota search; no question-by-question combinatorial search.
    for easy_mcq in range(bounds["easy"][0], bounds["easy"][1] + 1):
        for medium_mcq in range(bounds["medium"][0], bounds["medium"][1] + 1):
            for hard_mcq in range(bounds["hard"][0], bounds["hard"][1] + 1):
                mcqs = dict(zip(DIFFICULTIES, (easy_mcq, medium_mcq, hard_mcq)))
                allocation = {(tier, kind): mcqs[tier] if kind == "mcq" else quotas[tier] - mcqs[tier]
                              for tier in DIFFICULTIES for kind in ("mcq", "written")}
                lower = {cell: max(0, amount - len(cells[cell + (2,)])) for cell, amount in allocation.items()}
                upper = {cell: min(amount, len(cells[cell + (1,)])) for cell, amount in allocation.items()}
                m1_target = max(sum(lower.values()), min(target_m1, sum(upper.values())))
                score = (abs(sum(mcqs.values()) - target_mcq), abs(m1_target - target_m1),
                         sum(abs(mcqs[tier] - quotas[tier] * target_mcq / count) for tier in DIFFICULTIES))
                if best_score is None or score < best_score:
                    best, best_score = [(allocation, lower, upper, m1_target)], score
                elif score == best_score:
                    best.append((allocation, lower, upper, m1_target))
    allocation, m1, upper, target = rng.choice(best)
    while sum(m1.values()) < target:
        available = [cell for cell in allocation if m1[cell] < upper[cell]]
        cell = max(available, key=lambda c: allocation[c] * target_m1 / count - m1[c])
        m1[cell] += 1
    selected = []
    for cell, amount in allocation.items():
        for mod, take in ((1, m1[cell]), (2, amount - m1[cell])):
            selected.extend(rng.sample(cells[cell + (mod,)], take))
    rng.shuffle(selected)
    for question in selected:
        if question["type"] == "mcq":
            rng.shuffle(question["choices"])
            question["exam_choices"] = dict(zip("ABCD", question["choices"]))
    return selected


def grade_exam(questions, answers, flags=(), *, unlocked_ids=()):
    """Grade final answers once; caller controls submission and persistence."""
    progress = Progression(unlocked_ids, track_lives=False)
    records = []
    modules, topics, types = {}, {}, {}
    earned = possible = answered = streak = best_streak = 0
    for question in questions:
        raw = answers.get(question["id"], "")
        is_answered = bool(raw.strip())
        grading = analyze_written_answer(question, raw) if question["type"] == "written" else None
        points = grading["score"] if grading is not None else int(raw == question["answer"])
        if not is_answered:
            points = 0
        maximum = 5 if question["type"] == "written" else 1
        successful = points >= 4 if maximum == 5 else points == 1
        streak = streak + 1 if successful else 0
        best_streak = max(streak, best_streak)
        reward = progress.reward_answer(question, points, streak)
        records.append({"id": question["id"], "type": question["type"], "module": question["module"],
                        "topic": question["topic"], "answer": raw, "unanswered": not is_answered,
                        "flagged": question["id"] in flags, "earned_points": points,
                        "possible_points": maximum, "correct": successful, "grading": grading,
                        "reward": reward})
        earned += points
        possible += maximum
        answered += is_answered
        for breakdown, key in ((modules, question["module"]), (topics, question["topic"]), (types, question["type"])):
            row = breakdown.setdefault(key, {"earned": 0, "possible": 0, "attempts": 0})
            row["earned"] += points
            row["possible"] += maximum
            row["attempts"] += 1
    completion = progress.complete_quiz(earned, possible, "mixed" if len(types) > 1 else next(iter(types)))
    percentage = calculate_percentage(earned, possible)
    weak = sorted(({"topic": topic, **row, "percentage": calculate_percentage(row["earned"], row["possible"])}
                   for topic, row in topics.items()), key=lambda r: (r["percentage"], r["topic"]))
    return {"question_count": len(questions), "answered": answered, "unanswered": len(questions) - answered,
            "flagged": sum(r["flagged"] for r in records), "earned_points": earned, "possible_points": possible,
            "percentage": percentage, "label": get_performance_label(percentage), "modules": modules,
            "topics": topics, "type_points": types, "weakest_topics": weak[:5], "best_streak": best_streak,
            "answers": records, "completion_reward": completion, "xp": progress.total_xp,
            "achievements": [a for a in progress.achievements if not a["already_unlocked"]]}
