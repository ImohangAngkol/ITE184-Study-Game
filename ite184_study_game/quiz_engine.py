"""Phase 3: multiple-choice setup, gameplay, and session-only results."""

import random
from typing import Any

# Support both importing the package and running main.py from its folder.
if __package__:
    from .question_bank import Question, filter_questions, validate_question_bank
else:
    from question_bank import Question, filter_questions, validate_question_bank


ANSWER_LETTERS = "ABCD"


def select_difficulty() -> str | None:
    """Return a difficulty, 'all', or None when the user goes back."""
    print("\n=================================")
    print("QUIZ SETUP")
    print("=================================")
    print("Choose difficulty:")
    print("[1] Easy\n[2] Medium\n[3] Hard\n[4] All Difficulties\n[Q] Back")
    options = {"1": "easy", "2": "medium", "3": "hard", "4": "all"}
    while True:
        choice = input("Choose difficulty [1-4 or Q]: ").strip().lower()
        if choice == "q":
            return None
        if choice in options:
            return options[choice]
        print("Please enter 1, 2, 3, 4, or Q.")


def select_question_count() -> int | str | None:
    """Return 5, 10, 20, 'all', or None when the user goes back."""
    print("\nHow many questions?")
    print("[1] 5\n[2] 10\n[3] 20\n[4] All Available\n[Q] Back")
    options = {"1": 5, "2": 10, "3": 20, "4": "all"}
    while True:
        choice = input("Choose question count [1-4 or Q]: ").strip().lower()
        if choice == "q":
            return None
        if choice in options:
            return options[choice]
        print("Please enter 1, 2, 3, 4, or Q.")


def prepare_mcq_questions(
    module: int | None, difficulty: str, question_count: int | str
) -> list[Question]:
    """Filter MCQ copies, shuffle once, and limit the pool without repeats."""
    difficulty_filter = None if difficulty == "all" else difficulty
    questions = filter_questions(
        module=module, question_type="mcq", difficulty=difficulty_filter
    )
    random.shuffle(questions)
    if question_count == "all":
        return questions
    # Slicing safely returns fewer items when the pool is smaller than requested.
    return questions[:question_count]


def shuffle_choices(question: Question) -> dict[str, str]:
    """Map A-D to shuffled choice text without modifying the question."""
    choices = question["choices"].copy()
    random.shuffle(choices)
    return dict(zip(ANSWER_LETTERS, choices))


def confirm_return_to_menu() -> bool:
    """Confirm quitting; n resumes, while y or q returns to the main menu."""
    while True:
        choice = input("Return to main menu? (y/n): ").strip().lower()
        if choice in ("y", "q"):
            return True
        if choice == "n":
            return False
        print("Please enter Y or N. Q also returns to the main menu.")


def ask_mcq_question(
    question: Question, number: int, total: int, choices: dict[str, str]
) -> bool | None:
    """Display a question and return correctness, or None for confirmed quit."""
    print("\n=================================")
    print(f"QUESTION {number} / {total}")
    print(f"Module {question['module']} | {question['difficulty'].title()}")
    print(f"Topic: {question['topic']}")
    print(f"Subtopic: {question['subtopic']}")
    print("=================================")
    print(f"\n{question['question']}\n")
    for letter, text in choices.items():
        print(f"{letter}. {text}")

    while True:
        answer = input("Your answer [A-D or Q]: ").strip().upper()
        if answer == "Q":
            if confirm_return_to_menu():
                return None
            continue
        if answer in choices:
            # Compare TEXT, since its letter can change after shuffling.
            return choices[answer] == question["answer"]
        print("Please enter A, B, C, D, or Q.")


def create_quiz_results(
    module: int | None, difficulty: str, planned: int
) -> dict[str, Any]:
    """Create fresh counters and breakdown dictionaries for one quiz."""
    return {
        "module": module,
        "difficulty": difficulty,
        "planned": planned,
        "answered": 0,
        "correct": 0,
        "incorrect": 0,
        "current_streak": 0,
        "best_streak": 0,
        "ended_early": False,
        "topics": {},
        "modules": {},
    }


def record_answer(
    results: dict[str, Any], question: Question, is_correct: bool
) -> None:
    """Update counters, streaks, and topic/module totals after one answer."""
    results["answered"] += 1
    if is_correct:
        results["correct"] += 1
        results["current_streak"] += 1
        results["best_streak"] = max(results["best_streak"], results["current_streak"])
    else:
        results["incorrect"] += 1
        results["current_streak"] = 0

    for breakdown, key in (
        (results["topics"], question["topic"]),
        (results["modules"], question["module"]),
    ):
        if key not in breakdown:
            breakdown[key] = {"correct": 0, "answered": 0}
        breakdown[key]["answered"] += 1
        if is_correct:
            breakdown[key]["correct"] += 1


def display_answer_feedback(
    question: Question, choices: dict[str, str], is_correct: bool,
    results: dict[str, Any],
) -> None:
    """Show the correct shuffled answer, explanation, keywords, and live score."""
    print("\n[CORRECT]" if is_correct else "\n[INCORRECT]")
    for letter, text in choices.items():
        if text == question["answer"]:
            print(f"Correct answer: {letter}. {text}")
            break
    print(f"\nExplanation:\n{question['explanation']}")
    if question.get("keywords"):
        print("\nImportant keywords:")
        for keyword in question["keywords"]:
            print(f"- {keyword}")
    print(f"\nCurrent score: {results['correct']} / {results['answered']}")
    print(f"Correct: {results['correct']} | Incorrect: {results['incorrect']}")
    print(f"Current streak: {results['current_streak']} | Best: {results['best_streak']}")


def wait_to_continue() -> bool:
    """Return True for Enter; return False when the user confirms quitting."""
    while True:
        choice = input("\nPress Enter to continue (Q to return to menu): ").strip().lower()
        if choice == "":
            return True
        if choice == "q":
            if confirm_return_to_menu():
                return False
            continue
        print("Please press Enter or type Q.")


def calculate_percentage(correct: int, total: int) -> float:
    """Calculate accuracy; zero answers safely produces 0.0 percent."""
    return correct / total * 100 if total else 0.0


def get_performance_label(percentage: float) -> str:
    """Use the temporary Phase 3 performance bands, without XP or ranks."""
    if percentage >= 90:
        return "Excellent"
    if percentage >= 80:
        return "Very Good"
    if percentage >= 70:
        return "Good"
    if percentage >= 60:
        return "Needs Review"
    return "Needs More Study"


def display_results(results: dict[str, Any]) -> None:
    """Print the final or partial summary using only answered questions."""
    module = results["module"]
    module_label = "Module 1 + Module 2" if module is None else f"Module {module}"
    difficulty = results["difficulty"]
    difficulty_label = "All Difficulties" if difficulty == "all" else difficulty.title()
    percentage = calculate_percentage(results["correct"], results["answered"])

    print("\n=================================")
    print("QUIZ ENDED EARLY" if results["ended_early"] else "QUIZ COMPLETE")
    print("=================================")
    print(f"Module: {module_label}")
    print(f"Difficulty: {difficulty_label}")
    print(f"Questions answered: {results['answered']} / {results['planned']}")
    print(f"Correct: {results['correct']}")
    print(f"Incorrect: {results['incorrect']}")
    print(f"Score: {results['correct']} / {results['answered']}")
    print(f"Percentage: {percentage:.1f}%")
    print(f"Best Streak: {results['best_streak']}")
    performance = get_performance_label(percentage) if results["answered"] else "No answers yet"
    print(f"Performance: {performance}")

    print("\nTopic Breakdown:")
    if not results["topics"]:
        print("No questions answered.")
    for topic, counts in sorted(results["topics"].items()):
        print(f"{topic:<26} {counts['correct']} / {counts['answered']}")
    if module is None:
        print("\nModule Breakdown:")
        for module_number, counts in sorted(results["modules"].items()):
            print(f"Module {module_number}: {counts['correct']} / {counts['answered']}")
    print("=================================")
    print("Returning to the main menu...")


def run_mcq_quiz(module: int | None = None) -> dict[str, Any] | None:
    """Run one quiz; return session results, or None if setup is cancelled."""
    valid, errors = validate_question_bank()
    if not valid:
        print("Question bank validation FAILED. Quiz cannot start:")
        for error in errors:
            print(f"- {error}")
        return None

    difficulty = select_difficulty()
    if difficulty is None:
        return None
    question_count = select_question_count()
    if question_count is None:
        return None
    questions = prepare_mcq_questions(module, difficulty, question_count)
    if not questions:
        print("No matching MCQ questions are currently available.")
        return None
    if isinstance(question_count, int) and len(questions) < question_count:
        print(f"\nOnly {len(questions)} matching questions are currently available.")
        print(f"Starting a {len(questions)}-question quiz.")

    results = create_quiz_results(module, difficulty, len(questions))
    for number, question in enumerate(questions, start=1):
        choices = shuffle_choices(question)
        is_correct = ask_mcq_question(question, number, len(questions), choices)
        # None is a quit signal; False is a valid, incorrect answer.
        if is_correct is None:
            results["ended_early"] = True
            break
        record_answer(results, question, is_correct)
        display_answer_feedback(question, choices, is_correct, results)
        if not wait_to_continue():
            results["ended_early"] = results["answered"] < results["planned"]
            break

    display_results(results)
    return results
