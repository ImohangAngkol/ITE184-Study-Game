"""Render exam screenshots with temporary statistics and an injected test clock.

Run: py -B -m ite184_study_game.tools.preview_phase9
The real player profile and question bank are never modified.
"""

import os
from pathlib import Path
import random
import tempfile

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from ..exam_engine import prepare_exam
from ..question_bank import get_question_by_id
from ..stats import StatsStore
from ..ui.app import App


class PreviewClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def main():
    folder = Path(__file__).resolve().parents[1] / "artifacts" / "phase9"
    folder.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary) / "stats.json"
        store, clock = StatsStore(path), PreviewClock()
        app = App(stats_store=store, exam_clock=clock)

        def capture(name):
            app.render()
            pygame.image.save(app.canvas, str(folder / (name + ".png")))

        def action(name, value=None):
            app.dispatch((name, value))
            app.render()

        def select_question(identifier):
            session = app.exam.session
            index = next((i for i, q in enumerate(session.questions) if q["id"] == identifier), None)
            if index is None:
                question = get_question_by_id(identifier)
                index = next(i for i, q in enumerate(session.questions)
                             if (q["module"], q["type"], q["difficulty"]) ==
                             (question["module"], question["type"], question["difficulty"]))
                session.questions[index] = prepare_exam(questions=[question], question_count=1,
                                                       rng=random.Random(3))[0]
            app.exam.jump(index)
            return index

        try:
            capture("home_study_and_exam")
            action("exam")
            capture("exam_setup")
            action("exam_preset")
            capture("atty_instructions")
            action("exam_start")
            before = path.read_bytes()
            index = select_question("M2_MCQ_028")
            capture("exam_mcq")
            action("exam_select", "A")
            capture("exam_selected_only")
            action("exam_flag")
            index = select_question("M2_WR_075")
            app.handle_event(pygame.event.Event(pygame.TEXTINPUT, text=(
                "The report needs careful attribution. A public good claim does not automatically grant "
                "authorization. Privacy and harm remain relevant.")))
            action("exam_flag")
            capture("exam_written_editable")
            action("exam_palette")
            capture("question_palette")
            action("close_overlay")
            action("exam_submit")
            capture("submit_confirmation")
            action("close_overlay")
            action("exam_review_pending", "unanswered")
            # Fill several final responses and leave the others unanswered.
            for position, question in enumerate(app.exam.session.questions[:15]):
                app.exam.jump(position)
                app.exam.session.set_answer(question.get("model_answer", question.get("answer", "")))
            assert path.read_bytes() == before, "Exam leaked a pre-submission save"
            clock.now += 420
            action("exam_submit")
            action("exam_confirm_submit")
            capture("exam_results")
            action("exam_review")
            capture("exam_review_all")
            action("exam_review_filter", "partial")
            capture("exam_review_partial")
            action("exam_review_filter", "flagged")
            capture("exam_review_flagged")
            action("exam_review_filter", "unanswered")
            capture("exam_review_unanswered")
            for key, _, maximum in app.scroll_zones:
                app.scroll[key] = maximum
            capture("exam_review_scrolled")
            action("exam_results")
            action("mistakes")
            capture("submitted_exam_mistakes")
            action("statistics")
            for key, _, maximum in app.scroll_zones:
                if key == "stats_2":
                    app.scroll[key] = maximum
            capture("exam_performance_statistics")
            action("exam_history")
            capture("exam_history")
            action("home")
            action("exam")
            action("exam_preset")
            action("exam_start")
            action("settings")
            clock.now += 2701
            capture("time_up_auto_submission")
            assert app.exam.session.auto_submitted
            action("exam_again")
            action("exam_start")
            app.go_back()
            capture("abandon_confirmation")
            action("close_overlay")
            app.handle_event(pygame.event.Event(pygame.VIDEORESIZE, size=(960, 600)))
            app.render()
            app.present()
            pygame.image.save(app.window, str(folder / "resized_exam.png"))
            action("exam_abandon")  # Discard the active preview exam without submission.
            reopened = StatsStore(path)
            print(f"Screenshots: {folder}")
            print(f"Temporary profile: schema {reopened.data['version']}, "
                  f"{reopened.data['exams']['completed']} submitted exams, "
                  f"{len(reopened.data['exam_history'])} summary records.")
            print("No pre-submission progress writes; real player save untouched.")
        finally:
            pygame.quit()


if __name__ == "__main__":
    main()
