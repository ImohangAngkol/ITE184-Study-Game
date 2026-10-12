"""One event/render loop controls every screen and modal overlay."""

import pygame

from . import theme, screens
from .audio import AudioManager
from .button import Button
from .session import QuizSession
from .textbox import TextBox
from .rewards import draw_hud, draw_popups
from .exam_controller import ExamController

if "." in __package__:
    from ..question_bank import filter_questions
    from ..question_selection import get_mode_questions
    from ..stats import StatsStore
    from ..version import APP_TITLE
else:
    from question_bank import filter_questions
    from question_selection import get_mode_questions
    from stats import StatsStore
    from version import APP_TITLE


class App:
    """Own the window, navigation, current session, and reusable UI controls."""

    def __init__(self, stats_store=None, exam_clock=None):
        pygame.display.init()
        pygame.font.init()
        self.window = pygame.display.set_mode(theme.SIZE, pygame.RESIZABLE)
        pygame.display.set_caption(APP_TITLE)
        self.canvas = pygame.Surface(theme.SIZE)
        self.clock = pygame.time.Clock()
        self.fonts = theme.make_fonts(pygame)
        self.audio = AudioManager()
        self.stats_store = stats_store if stats_store is not None else StatsStore()
        self.running = True
        self.state = "HOME"
        self.overlay = None
        self.selected_module = None
        self.selected_mode = "mcq"
        self.selected_difficulty = "all"
        self.question_count = "all"
        self.session = None
        self.notice = ""
        self.elapsed = 0.0
        self.feedback_age = 0.0
        self.buttons = []
        self.button_cache = {}
        self.scroll = {}
        self.scroll_zones = []
        self.textbox = TextBox((64, 452, 736, 148))
        self.review_index = 0
        self.last_reward = None
        self.reward_age = 999.0
        self.achievement_queue = []
        self.achievement_age = 0.0
        self.mastered_age = 999.0
        self.review_filter = (None, None)
        self.exam = ExamController(self, exam_clock)

    def button(self, key, rect, text, action, **kwargs):
        """Reuse button objects so their hover transition survives redraws."""
        if key not in self.button_cache:
            self.button_cache[key] = Button(rect, text, action, **kwargs)
        button = self.button_cache[key]
        button.rect = pygame.Rect(rect)
        button.text, button.action = text, action
        button.enabled = kwargs.get("enabled", True)
        button.primary = kwargs.get("primary", False)
        button.subtitle = kwargs.get("subtitle", "")
        button.keys = kwargs.get("keys", ())
        button.status = kwargs.get("status")
        button.update(self.canvas_position(pygame.mouse.get_pos()), self.frame_dt)
        button.draw(self.canvas, self.fonts)
        self.buttons.append(button)

    def viewport(self):
        """Keep the logical canvas's aspect ratio when the window is resized."""
        width, height = self.window.get_size()
        scale = min(width / theme.SIZE[0], height / theme.SIZE[1])
        size = (max(1, round(theme.SIZE[0] * scale)), max(1, round(theme.SIZE[1] * scale)))
        return pygame.Rect((width - size[0]) // 2, (height - size[1]) // 2, *size)

    def canvas_position(self, position):
        """Convert physical mouse coordinates into the 1280x720 drawing space."""
        viewport = self.viewport()
        if not viewport.collidepoint(position):
            return (-1000, -1000)
        return ((position[0] - viewport.x) * theme.SIZE[0] / viewport.width,
                (position[1] - viewport.y) * theme.SIZE[1] / viewport.height)

    def matching_count(self):
        """Count the available pool without randomizing it or starting a quiz."""
        return len(get_mode_questions(self.selected_module, self.selected_difficulty, self.selected_mode))

    def start_quiz(self):
        """Create a new session; report invalid/empty banks without crashing."""
        try:
            self.session = QuizSession(self.selected_module, self.selected_difficulty,
                                       self.question_count, self.selected_mode, self.stats_store)
        except ValueError as error:
            self.notice = str(error)
            self.state = "COUNT_SELECT"
            return
        self.notice = ""
        self.state = "QUIZ"
        self.scroll.clear()
        self.reset_textbox()
        self.last_reward = None
        self.reward_age = 999.0
        self.achievement_queue.clear()
        self.achievement_age = 0.0
        self.mastered_age = 999.0

    def start_review(self, module=None, question_type=None):
        """Feed copied active mistakes into the existing quiz session/screens."""
        questions = self.stats_store.get_active_mistakes(module, question_type)
        if not questions:
            self.notice = "No matching questions to review. You're caught up!"
            self.state = "MISTAKES"
            return
        kinds = {question["type"] for question in questions}
        self.selected_module = module
        self.selected_mode = "mixed" if len(kinds) > 1 else next(iter(kinds))
        self.selected_difficulty = "all"
        self.question_count = "all"
        self.review_filter = (module, question_type)
        try:
            self.session = QuizSession(module, "all", "all", self.selected_mode,
                                       self.stats_store, questions=questions, review=True)
        except ValueError as error:
            self.notice = str(error)
            self.state = "MISTAKES"
            return
        self.state = "QUIZ"
        self.notice = ""
        self.scroll.clear()
        self.reset_textbox()
        self.last_reward = None
        self.reward_age = self.mastered_age = 999.0
        self.achievement_queue.clear()
        self.achievement_age = 0.0

    def queue_reward(self, reward):
        """Expose XP/heart deltas and queue each newly unlocked achievement once."""
        if not reward:
            return
        self.last_reward = reward
        self.reward_age = 0.0
        if not self.achievement_queue:
            self.achievement_age = 0.0
        self.achievement_queue.extend(reward["achievements"])

    def update_rewards(self, dt):
        """Expire passive animation/toast state without pausing the quiz."""
        self.reward_age += dt
        self.mastered_age += dt
        if self.achievement_queue:
            self.achievement_age += dt
            while self.achievement_queue and self.achievement_age >= 2.4:
                self.achievement_queue.pop(0)
                self.achievement_age -= 2.4

    def reset_textbox(self):
        """Clear only when moving to a new question/session, never on cancel."""
        self.textbox.set_focus(False)
        self.textbox = TextBox((64, 452, 736, 148))
        if self.session.current_question["type"] == "written":
            self.textbox.set_focus(True)

    def show_feedback(self):
        """Lock text, play the relevant cue, and expose the feedback screen."""
        answer = self.session.answers[-1]
        self.queue_reward(answer["reward"])
        if answer.get("mastered"):
            self.mastered_age = 0.0
        if answer["type"] == "mcq" or answer["earned_points"] != 3:
            self.audio.play("correct" if answer["correct"] else "wrong")
        self.textbox.set_focus(False)
        self.textbox.locked = True
        self.state = "FEEDBACK"
        self.feedback_age = 0.0
        self.scroll.clear()
        self.notice = ""

    def go_back(self):
        """Escape closes a modal, confirms quiz exit, or navigates one step back."""
        if self.state.startswith("EXAM_"):
            self.exam.go_back()
            return
        if self.overlay:
            self.overlay = None
        elif self.state in ("QUIZ", "FEEDBACK"):
            self.overlay = "QUIT"
        else:
            self.state = {
                "HOME": "HOME", "MODULE_SELECT": "HOME",
                "MODE_SELECT": "MODULE_SELECT", "DIFFICULTY_SELECT": "MODE_SELECT",
                "COUNT_SELECT": "DIFFICULTY_SELECT",
                "RESULTS": "HOME", "REVIEW": "RESULTS", "REWARDS": "RESULTS",
                "STATISTICS": "HOME", "MISTAKES": "HOME", "TOPICS": "STATISTICS",
                "ACHIEVEMENTS": "STATISTICS",
                "ABOUT": "HOME",
            }[self.state]

    def dispatch(self, action):
        """Translate a button action into one small state/data change."""
        name, value = action
        if name == "exam" or name.startswith("exam_"):
            self.exam.handle_action(name, value)
        elif name == "play":
            self.exam.session = None
            self.exam.response.set_focus(False)
            self.state = "MODULE_SELECT"
        elif name == "statistics":
            self.state = "STATISTICS"
            self.scroll.clear()
        elif name == "about":
            self.state = "ABOUT"
            self.scroll.clear()
        elif name == "mistakes":
            self.notice = ""
            self.state = "MISTAKES"
            self.scroll.clear()
        elif name == "review_mistakes":
            self.start_review(*value)
        elif name == "topics":
            self.state = "TOPICS"
            self.scroll.clear()
        elif name == "achievements":
            self.state = "ACHIEVEMENTS"
            self.scroll.clear()
        elif name == "reset_stats":
            self.overlay = "RESET"
        elif name == "confirm_reset":
            if self.stats_store.reset():
                self.session = None
                self.last_reward = None
                self.achievement_queue.clear()
                self.overlay = None
                self.notice = "Progress reset. The question bank is unchanged."
                self.state = "STATISTICS"
            else:
                self.overlay = None
                self.notice = self.stats_store.warning
        elif name == "module":
            self.selected_module = value
            self.state = "MODE_SELECT"
        elif name == "mode":
            self.selected_mode = value
            self.state = "DIFFICULTY_SELECT"
        elif name == "difficulty":
            self.selected_difficulty = value
            self.notice = ""
            self.state = "COUNT_SELECT"
        elif name == "count":
            self.question_count = value
            self.start_quiz()
        elif name == "answer" and self.state == "QUIZ":
            if self.session.submit(value):
                self.show_feedback()
        elif name == "submit_written" and self.state == "QUIZ":
            if not self.textbox.text.strip():
                self.notice = "Type an answer before submitting."
            elif self.session.submit_written(self.textbox.text):
                self.show_feedback()
        elif name == "next" and self.state == "FEEDBACK":
            self.state = "QUIZ" if self.session.advance() else "RESULTS"
            self.scroll.clear()
            if self.state == "QUIZ":
                self.reset_textbox()
            else:
                self.queue_reward(self.session.completion_reward)
                if (self.session.results["earned_points"] == self.session.results["possible_points"]
                        or self.session.completion_reward["achievements"]):
                    self.audio.play("correct")
        elif name == "replay":
            if self.session.is_review:
                self.start_review(*self.review_filter)
            else:
                self.start_quiz()
        elif name == "review":
            self.review_index = 0
            self.scroll.clear()
            self.state = "REVIEW"
        elif name == "rewards":
            self.state = "REWARDS"
            self.scroll.clear()
        elif name == "rewards_done":
            self.state = "RESULTS"
        elif name == "review_move":
            self.review_index = max(0, min(len(self.session.answers) - 1, self.review_index + value))
            self.scroll.clear()
        elif name == "review_done":
            self.state = "RESULTS"
        elif name == "change":
            self.state = "MODULE_SELECT"
        elif name == "home":
            if self.exam.active:
                self.exam.request_exit()
            elif self.state in ("QUIZ", "FEEDBACK"):
                self.overlay = "QUIT"
            else:
                self.session = None
                self.state = "HOME"
        elif name == "settings":
            self.overlay = "SETTINGS"
        elif name == "close_overlay":
            self.overlay = None
        elif name == "confirm_quit":
            self.session = None
            self.overlay = None
            self.state = "HOME"
        elif name == "music":
            self.audio.toggle_music()
        elif name == "sfx":
            self.audio.toggle_sfx()
        elif name == "back":
            self.go_back()
        elif name == "quit":
            if self.exam.active:
                self.exam.request_exit(close_app=True)
            else:
                self.running = False

    def handle_event(self, event):
        """Process close, navigation, scrolling, and active button events."""
        before = self.state
        self.exam.update()
        if self.state != before:
            self.render()
        if event.type == pygame.QUIT:
            if self.exam.active:
                self.exam.request_exit(close_app=True)
                self.render()
            else:
                self.running = False
            return
        if self.state.startswith("EXAM_") and self.exam.handle_event(event):
            return
        # Modal controls own input, so written typing cannot leak through them.
        if (not self.overlay and self.state in ("QUIZ", "FEEDBACK")
                and self.session.current_question["type"] == "written"
                and not (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE)):
            mouse = self.canvas_position(getattr(event, "pos", pygame.mouse.get_pos()))
            handled = self.textbox.handle_event(event, mouse)
            if handled:
                if handled == "submit":
                    self.dispatch(("submit_written", None))
                self.render()
                return
        if event.type == pygame.VIDEORESIZE:
            self.window = pygame.display.set_mode(event.size, pygame.RESIZABLE)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.go_back()
            self.render()
            return
        elif event.type == pygame.MOUSEWHEEL and not self.overlay:
            mouse = self.canvas_position(pygame.mouse.get_pos())
            for key, rect, maximum in self.scroll_zones:
                if rect.collidepoint(mouse):
                    self.scroll[key] = max(0, min(maximum, self.scroll.get(key, 0) - event.y * 36))
        for button in self.buttons:
            position = self.canvas_position(getattr(event, "pos", pygame.mouse.get_pos()))
            if button.activated(event, position):
                self.audio.play("click")
                self.dispatch(button.action)
                # Rebuild enabled controls immediately: queued clicks cannot resubmit.
                self.render()
                break

    def render(self, dt=0.0):
        """Draw the current screen and optional modal onto the logical canvas."""
        self.exam.update()
        self.frame_dt = dt
        self.buttons = []
        self.scroll_zones = []
        screens.draw(self)
        draw_hud(self)
        draw_popups(self)
        if self.overlay:
            # The modal owns input; the covered screen's buttons are inactive.
            self.buttons = []
            if self.overlay.startswith("EXAM_"):
                from .exam_screens import overlay
                overlay(self)
            else:
                screens.draw_overlay(self)

    def present(self):
        """Scale the canvas into the actual window, with letterbox margins."""
        viewport = self.viewport()
        self.window.fill(theme.BACKGROUND)
        scaled = pygame.transform.smoothscale(self.canvas, viewport.size)
        self.window.blit(scaled, viewport)
        pygame.display.flip()

    def run(self):
        """Keep one responsive game loop, capped at 60 frames per second."""
        try:
            while self.running:
                dt = self.clock.tick(theme.FPS) / 1000
                self.elapsed += dt
                self.feedback_age += dt
                self.update_rewards(dt)
                self.render(dt)
                for event in pygame.event.get():
                    self.handle_event(event)
                self.present()
        finally:
            pygame.quit()
