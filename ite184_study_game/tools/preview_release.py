"""Capture public v1.0 screenshots from real screens using temporary progress.

Run: py -B -m ite184_study_game.tools.preview_release
No private player saves, developer preview images or external assets are read.
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
from ..version import __version__


def main():
    output = Path(__file__).resolve().parents[2] / "screenshots"
    output.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        store = StatsStore(Path(temporary) / "stats.json")
        app = App(stats_store=store)
        captured = []

        def capture(name, *, scroll_to_bottom=False):
            app.render()
            if scroll_to_bottom:
                for key, _, maximum in app.scroll_zones:
                    app.scroll[key] = maximum
                app.render()
            pygame.image.save(app.canvas, str(output / (name + ".png")))
            captured.append(name)

        def action(name, value=None):
            app.dispatch((name, value))
            app.render()

        def study(identifier):
            question = get_question_by_id(identifier)
            app.session = QuizSession(module=question["module"], mode=question["type"],
                                      stats_store=store, questions=[question])
            app.state = "QUIZ"
            app.reset_textbox()
            app.scroll.clear()
            app.last_reward = None
            app.achievement_queue.clear()

        try:
            capture("home")
            action("about")
            capture("about")
            action("back")
            action("play"); action("module", None)
            capture("study_mode")

            study("M2_MCQ_003")
            capture("mcq")
            wrong = next(k for k, value in app.session.choices.items() if value != app.session.current_question["answer"])
            action("answer", wrong); action("next")

            study("M2_WR_001")
            capture("written")
            app.textbox.insert(app.session.current_question["model_answer"])
            action("submit_written")
            capture("written_feedback")
            action("next")

            # Another wrong attempt makes a real weak-topic record in this demo.
            study("M2_MCQ_003")
            wrong = next(k for k, value in app.session.choices.items() if value != app.session.current_question["answer"])
            action("answer", wrong); action("next")
            action("home"); action("statistics")
            capture("statistics")
            action("mistakes")
            capture("review_mistakes")

            action("home"); action("exam")
            capture("exam_setup")
            action("exam_preset"); action("exam_start")
            exam = app.exam.session
            index = next(i for i, question in enumerate(exam.questions) if question["type"] == "mcq")
            app.exam.jump(index)
            letter = next(iter(exam.current_question["exam_choices"]))
            action("exam_select", letter)
            capture("exam")
            # Final answers remain ungraded until the genuine confirmation path.
            for index, question in enumerate(exam.questions[:20]):
                app.exam.jump(index)
                exam.set_answer(question.get("answer", question.get("model_answer", "")))
            action("exam_submit"); action("exam_confirm_submit")
            capture("exam_results")
            action("exam_review")
            index = next(i for i, question in enumerate(exam.questions) if question["type"] == "written")
            app.exam.review_position = index
            capture("exam_review")
            print(f"v{__version__}: {len(captured)} public release screenshots saved to {output}")
            print("All pictured progress is temporary demonstration data.")
        finally:
            pygame.quit()


if __name__ == "__main__":
    main()
