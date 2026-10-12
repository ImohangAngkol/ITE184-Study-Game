"""Render Phase 8 review screenshots using temporary progress, never player data.

Run from the workspace: py -B -m ite184_study_game.tools.preview_phase8
"""

import os
from pathlib import Path
import tempfile

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from ..question_bank import get_question_by_id
from ..stats import StatsStore
from ..ui.app import App
from ..ui.session import QuizSession


def capture(app, folder, name):
    app.render()
    pygame.image.save(app.canvas, str(folder / (name + ".png")))


def answer(app, correct=True):
    question = app.session.current_question
    if question["type"] == "written":
        app.textbox.text = question["model_answer"] if correct else "I don't know"
        app.dispatch(("submit_written", None))
    else:
        letter = next(k for k, v in app.session.choices.items() if (v == question["answer"]) == correct)
        app.dispatch(("answer", letter))


def main():
    folder = Path(__file__).resolve().parents[1] / "artifacts" / "phase8"
    folder.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        store = StatsStore(Path(temporary) / "stats.json")
        app = App(stats_store=store)
        try:
            # A full Module 1 / Hard / Written quiz; show its scope scenario.
            app.selected_module, app.selected_mode, app.selected_difficulty = 1, "written", "hard"
            app.start_quiz()
            index = next(i for i, q in enumerate(app.session.questions) if q["id"] == "M1_WR_026")
            app.session.questions.insert(0, app.session.questions.pop(index))
            capture(app, folder, "module1_hard_written")
            answer(app)
            capture(app, folder, "module1_written_feedback")

            app.selected_module, app.selected_mode, app.selected_difficulty, app.question_count = 2, "mixed", "hard", 20
            app.start_quiz()
            # Guarantee the long scenario is in this otherwise balanced random quiz.
            index = next(i for i, q in enumerate(app.session.questions) if q["type"] == "written")
            app.session.questions[index] = get_question_by_id("M2_WR_075")
            app.session.questions.insert(0, app.session.questions.pop(index))
            capture(app, folder, "module2_hard_mixed_scenario")
            answer(app)
            app.render()
            for key, _, maximum in app.scroll_zones:
                app.scroll[key] = maximum
            capture(app, folder, "module2_feedback_scrolled")

            app.session = QuizSession(mode="mcq", questions=[get_question_by_id("M2_MCQ_091")])
            app.state = "QUIZ"
            app.scroll.clear()
            capture(app, folder, "long_mcq_choices")
            answer(app)
            capture(app, folder, "long_mcq_feedback")

            app.selected_module, app.selected_mode, app.selected_difficulty = None, "mixed", "all"
            app.start_quiz()
            for _ in range(len(app.session.questions)):
                answer(app)
                app.dispatch(("next", None))
            capture(app, folder, "both_all_twenty_results")

            # Persistent old/new mistakes, reopen, review, then retained history.
            for identifier in ("M2_WR_006", "M2_WR_075", "M1_MCQ_045"):
                app.session = QuizSession(mode="mixed", stats_store=store,
                                          questions=[get_question_by_id(identifier)])
                app.state = "QUIZ"
                app.reset_textbox()
                answer(app, False)
                app.dispatch(("next", None))
            app.stats_store = StatsStore(store.path)
            app.state = "MISTAKES"
            capture(app, folder, "review_mistakes")
            app.start_review()
            for _ in range(len(app.session.questions)):
                answer(app)
                app.dispatch(("next", None))
            capture(app, folder, "review_mastered_results")
            app.state = "TOPICS"
            capture(app, folder, "topic_statistics")
            reopened = StatsStore(store.path)
            print(f"Screenshots: {folder}")
            print(f"Temporary profile: {reopened.data['total_xp']} XP, "
                  f"{reopened.data['questions_answered']} answers, "
                  f"{len(reopened.get_active_mistakes())} active mistakes.")
        finally:
            pygame.quit()


if __name__ == "__main__":
    main()
