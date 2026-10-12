"""Pure question selection for visual MCQ, written, and balanced mixed modes."""

import random

if __package__:
    from .question_bank import filter_questions
else:
    from question_bank import filter_questions


def get_mode_questions(module=None, difficulty="all", mode="mcq") -> list[dict]:
    """Return copied matching data; mixed mode permits both question types."""
    if mode not in ("mcq", "written", "mixed"):
        raise ValueError("Mode must be mcq, written, or mixed.")
    return filter_questions(module=module, difficulty=None if difficulty == "all" else difficulty,
                            question_type=None if mode == "mixed" else mode)


def prepare_questions(module=None, difficulty="all", question_count="all",
                      mode="written") -> list[dict]:
    """Balance mixed subsets when possible, fill shortages, and shuffle types."""
    pool = get_mode_questions(module, difficulty, mode)
    if question_count != "all" and (type(question_count) is not int or question_count < 1):
        raise ValueError("Question count must be positive or 'all'.")
    count = len(pool) if question_count == "all" else min(question_count, len(pool))
    random.shuffle(pool)
    if mode != "mixed" or count == len(pool):
        return pool[:count]
    mcqs = [question for question in pool if question["type"] == "mcq"]
    written = [question for question in pool if question["type"] == "written"]
    # Randomly choose the extra type for odd requests when both pools suffice.
    mcq_target = count // 2 + (count % 2 if random.choice((True, False)) else 0)
    selected = mcqs[:mcq_target] + written[:count - mcq_target]
    selected_ids = {question["id"] for question in selected}
    remaining = [question for question in pool if question["id"] not in selected_ids]
    selected.extend(remaining[:count - len(selected)])
    random.shuffle(selected)
    return selected


def possible_points(question: dict) -> int:
    """MCQ is one point; every written scenario is five."""
    return 5 if question["type"] == "written" else 1
