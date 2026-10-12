"""Exam-only navigation/input controller, leaving Study session flow intact."""

import pygame
from .textbox import TextBox

if "." in __package__:
    from ..exam_engine import ATTY_PRESET, exam_pool
    from ..exam_session import ExamSession, validate_timer
else:
    from exam_engine import ATTY_PRESET, exam_pool
    from exam_session import ExamSession, validate_timer


class ExamController:
    def __init__(self, app, clock=None):
        self.app, self.clock = app, clock
        self.session = None
        self.config = dict(ATTY_PRESET)
        self.input = TextBox((76, 328, 1128, 100), max_characters=12)
        self.response = TextBox((64, 422, 1152, 160))
        self.custom_field = None
        self.pending_count = None
        self.palette_page = 0
        self.review_filter, self.review_position = "all", 0
        self.close_after_abandon = False
        self.result_announced = False

    @property
    def active(self):
        return self.session is not None and not self.session.submitted and not self.session.abandoned

    def available(self):
        return len(exam_pool(self.config["module"], self.config["mode"], self.config["difficulty"]))

    def open(self):
        self.session = None
        self.app.session = None
        self.app.overlay = None
        self.app.notice = ""
        self.app.achievement_queue.clear()
        self.app.last_reward = None
        self.config = dict(ATTY_PRESET)
        self.app.state = "EXAM_MENU"

    def start(self):
        try:
            self.session = ExamSession(**self.config, stats_store=self.app.stats_store, clock=self.clock)
        except ValueError as error:
            self.app.notice = str(error)
            return
        self.result_announced = False
        self.app.overlay = None
        self.app.state = "EXAM_QUESTION"
        self.app.notice = ""
        self.load_response()

    def load_response(self):
        self.response.set_focus(False)
        self.response = TextBox((64, 422, 1152, 160))
        question = self.session.current_question
        self.response.insert(self.session.answers.get(question["id"], ""))
        self.response.set_focus(question["type"] == "written")
        self.app.scroll.clear()

    def update(self):
        if self.active:
            self.session.tick()
        if self.session is not None and self.session.submitted and not self.result_announced:
            self.result_announced = True
            self.response.set_focus(False)
            self.app.overlay = None
            self.app.state = "EXAM_RESULTS"
            self.app.scroll.clear()
            self.app.audio.play("correct" if self.session.results["percentage"] >= 70 else "wrong")

    def jump(self, index):
        if self.session.jump(index):
            self.app.overlay = None
            self.load_response()

    def go_back(self):
        app = self.app
        if app.overlay:
            app.overlay = None
        elif self.active:
            self.request_exit()
        else:
            app.state = {"EXAM_MENU": "HOME", "EXAM_MODULE": "EXAM_MENU", "EXAM_TYPE": "EXAM_MODULE",
                         "EXAM_DIFFICULTY": "EXAM_TYPE", "EXAM_COUNT": "EXAM_DIFFICULTY",
                         "EXAM_TIMER": "EXAM_COUNT", "EXAM_INSTRUCTIONS": "EXAM_TIMER",
                         "EXAM_CUSTOM": "EXAM_COUNT" if self.custom_field == "count" else "EXAM_TIMER",
                         "EXAM_RESULTS": "HOME", "EXAM_REVIEW": "EXAM_RESULTS",
                         "EXAM_HISTORY": "STATISTICS"}.get(app.state, "HOME")
            self.input.set_focus(False)
            app.notice = ""
            app.scroll.clear()

    def request_exit(self, close_app=False):
        self.close_after_abandon = close_app
        self.app.overlay = "EXAM_EXIT"

    def choose_count(self, value):
        available = self.available()
        if available == 0:
            self.app.notice = "No questions match this selection. Choose another difficulty or type."
        elif type(value) is int and value > available:
            self.pending_count = value
            self.app.overlay = "EXAM_COUNT_LIMIT"
            self.input.set_focus(False)
        else:
            self.config["question_count"] = value
            self.input.set_focus(False)
            self.app.notice = ""
            self.app.state = "EXAM_TIMER"

    def handle_action(self, name, value):
        app = self.app
        if name == "exam":
            self.open()
        elif name == "exam_preset":
            self.config = dict(ATTY_PRESET)
            app.state = "EXAM_INSTRUCTIONS"
        elif name == "exam_custom_setup":
            app.state = "EXAM_MODULE"
        elif name == "exam_module":
            self.config["module"] = value
            app.state = "EXAM_TYPE"
        elif name == "exam_type":
            self.config["mode"] = value
            app.state = "EXAM_DIFFICULTY"
        elif name == "exam_difficulty":
            self.config["difficulty"] = value
            app.state = "EXAM_COUNT"
        elif name == "exam_count":
            self.choose_count(value)
        elif name == "exam_accept_count":
            app.overlay = None
            self.choose_count(self.available())
        elif name == "exam_timer":
            validate_timer(value)
            self.config["timer_minutes"] = value
            app.state = "EXAM_INSTRUCTIONS"
        elif name == "exam_custom":
            self.custom_field = value
            self.input = TextBox((76, 328, 1128, 100), max_characters=12)
            self.input.set_focus(True)
            app.state = "EXAM_CUSTOM"
            app.notice = ""
        elif name == "exam_apply_custom":
            text = self.input.text.strip()
            if not text.isdecimal() or int(text) < 1:
                app.notice = "Enter a positive whole number."
            elif self.custom_field == "timer" and not 1 <= int(text) <= 180:
                app.notice = "Time must be 1–180 minutes."
            elif self.custom_field == "count":
                self.choose_count(int(text))
            else:
                self.config["timer_minutes"] = int(text)
                self.input.set_focus(False)
                app.state = "EXAM_INSTRUCTIONS"
                app.notice = ""
        elif name == "exam_start":
            self.start()
        elif name == "exam_select" and self.active:
            self.session.select_choice(value)
        elif name == "exam_clear" and self.active:
            self.session.set_answer("")
            self.load_response()
        elif name == "exam_move" and self.active:
            self.jump(self.session.current_question_index + value)
        elif name == "exam_jump" and self.active:
            self.jump(value)
        elif name == "exam_flag" and self.active:
            self.session.toggle_flag()
        elif name == "exam_palette" and self.active:
            self.palette_page = self.session.current_question_index // 40
            app.overlay = "EXAM_PALETTE"
        elif name == "exam_palette_page" and self.active:
            self.palette_page = max(0, min((self.session.question_count - 1) // 40, self.palette_page + value))
        elif name == "exam_submit" and self.active:
            app.overlay = "EXAM_SUBMIT"
        elif name == "exam_review_pending" and self.active:
            identifiers = self.session.unanswered_ids if value == "unanswered" else self.session.flagged_ids
            if identifiers:
                self.jump(next(i for i, q in enumerate(self.session.questions) if q["id"] == identifiers[0]))
        elif name == "exam_confirm_submit" and self.active:
            self.session.submit()
            self.update()
        elif name == "exam_abandon" and self.active:
            self.session.abandon()
            self.response.set_focus(False)
            self.session = None
            app.overlay = None
            app.state = "HOME"
            if self.close_after_abandon:
                app.running = False
        elif name == "exam_review" and self.session is not None and self.session.submitted:
            self.review_filter, self.review_position = "all", 0
            app.state = "EXAM_REVIEW"
            app.scroll.clear()
        elif name == "exam_review_filter":
            self.review_filter, self.review_position = value, 0
            app.scroll.clear()
        elif name == "exam_review_move":
            count = len(self.session.review_indices(self.review_filter))
            self.review_position = max(0, min(count - 1, self.review_position + value))
            app.scroll.clear()
        elif name == "exam_results":
            app.state = "EXAM_RESULTS"
        elif name == "exam_again":
            self.response.set_focus(False)
            self.session = None
            app.state = "EXAM_INSTRUCTIONS"
        elif name == "exam_history":
            app.state = "EXAM_HISTORY"
            app.scroll.clear()
        elif name == "exam_retry_save" and self.session is not None and self.session.submitted:
            self.session.submit()
        self.update()

    def handle_event(self, event):
        app = self.app
        if app.overlay:
            return False
        box = (self.input if app.state == "EXAM_CUSTOM" else
               self.response if app.state == "EXAM_QUESTION" and self.session.current_question["type"] == "written" else None)
        if box is not None and not (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            mouse = app.canvas_position(getattr(event, "pos", pygame.mouse.get_pos()))
            handled = box.handle_event(event, mouse)
            if handled:
                if app.state == "EXAM_CUSTOM" and handled == "submit":
                    self.handle_action("exam_apply_custom", None)
                elif app.state == "EXAM_QUESTION":
                    # Enter adds a line in exams; it never submits a question/exam.
                    if handled == "submit":
                        box.insert("\n")
                    self.session.set_answer(box.text)
                app.render()
                return True
        if app.state == "EXAM_QUESTION" and event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                self.handle_action("exam_move", -1 if event.key == pygame.K_LEFT else 1)
                app.render()
                return True
        return False
