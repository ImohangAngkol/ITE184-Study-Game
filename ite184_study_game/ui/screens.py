"""Screen layouts use shared buttons, drawing primitives, and wrapped text."""

from math import sin
import pygame

from . import theme
from .text import draw_wrapped

if "." in __package__:
    from ..quiz_engine import calculate_percentage, get_performance_label
    from ..question_selection import get_mode_questions
    from ..version import PROJECT_NAME, __version__, DEVELOPER
else:
    from quiz_engine import calculate_percentage, get_performance_label
    from question_selection import get_mode_questions
    from version import PROJECT_NAME, __version__, DEVELOPER


def label(app, text, position, style="body", color=theme.TEXT):
    """Draw one line using a named shared font."""
    app.canvas.blit(app.fonts[style].render(text, True, color), position)


def card(app, rect, color=theme.CARD):
    """Draw one rounded panel and its subtle outline."""
    pygame.draw.rect(app.canvas, color, rect, border_radius=20)
    pygame.draw.rect(app.canvas, theme.BORDER, rect, width=1, border_radius=20)


def text_panel(app, key, text, rect, style="body", color=theme.TEXT, gap=4):
    """Wrap text inside a viewport and expose mouse-wheel scrolling if needed."""
    rect = pygame.Rect(rect)
    maximum = draw_wrapped(app.canvas, text, app.fonts[style], color, rect,
                           app.scroll.get(key, 0), gap=gap)
    app.scroll[key] = max(0, min(app.scroll.get(key, 0), maximum))
    app.scroll_zones.append((key, rect, maximum))
    if maximum:
        label(app, "Scroll here to read more", (rect.x, rect.bottom + 3), "tiny", theme.ORANGE)


def module_name(module):
    return "Both modules" if module is None else f"Module {module}"


def background(app):
    """Draw a restrained moving grid and an orange accent."""
    app.canvas.fill(theme.BACKGROUND)
    for x in range(0, 1280, 80):
        pygame.draw.line(app.canvas, (22, 22, 37), (x, 0), (x, 720))
    for y in range(0, 720, 80):
        pygame.draw.line(app.canvas, (22, 22, 37), (0, y), (1280, y))
    for index in range(9):
        x = 780 + index * 51
        y = 70 + int(sin(app.elapsed * 0.5 + index) * 14)
        pygame.draw.circle(app.canvas, (72, 55, 103), (x, y), 2)
    pygame.draw.rect(app.canvas, theme.PURPLE, (40, 40, 8, 24), border_radius=4)
    label(app, "ITE184  /  REVIEWER", (62, 39), "small")
    if app.state != "HOME":
        app.button("audio_global", (955, 32, 155, 42),
                   "Music ON" if app.audio.music_enabled else "Music OFF", ("music", None))
        app.button("settings_global", (1120, 32, 120, 42), "Settings", ("settings", None))


def home(app):
    label(app, "LEARN. TEST. LEVEL UP YOUR UNDERSTANDING.", (76, 166), "small", theme.ORANGE)
    label(app, "ITE184", (72, 200), "hero")
    label(app, "REVIEWER", (72, 276), "hero", theme.PURPLE)
    text_panel(app, "home_subtitle", "Social, Legal and Professional Issues in Computing",
               (76, 374, 510, 68), "body", theme.MUTED_TEXT)
    app.button("play", (76, 454, 240, 70), "STUDY MODE", ("play", None),
               subtitle="Immediate feedback", keys=(pygame.K_RETURN,))
    app.button("exam_home", (332, 454, 240, 70), "EXAM MODE", ("exam", None), primary=True,
               subtitle="Long Quiz Simulation")
    mistake_count = len(app.stats_store.get_active_mistakes())
    app.button("mistakes", (76, 532, 240, 56), f"Review mistakes ({mistake_count})", ("mistakes", None))
    app.button("statistics", (332, 532, 240, 56), "Statistics", ("statistics", None))
    app.button("settings_home", (76, 604, 240, 52), "Settings", ("settings", None))
    app.button("quit_home", (332, 604, 240, 52), "Quit", ("quit", None))

    y = 186 + int(sin(app.elapsed * 0.7) * 5)
    card(app, (716, y, 488, 382))
    store = app.stats_store
    label(app, "YOUR SAVED PROGRESS", (748, y + 30), "small", theme.ORANGE)
    label(app, f"LEVEL {store.level}", (748, y + 70), "large")
    label(app, store.rank, (748, y + 148), "button", theme.PURPLE)
    label(app, f"XP: {store.data['total_xp']}", (748, y + 198), "body")
    pygame.draw.rect(app.canvas, theme.BORDER, (748, y + 240, 422, 7), border_radius=3)
    pygame.draw.rect(app.canvas, theme.PURPLE,
                     (748, y + 240, round(422 * (store.data['total_xp'] % 100) / 100), 7), border_radius=3)
    label(app, f"Next level: {store.data['total_xp'] % 100} / 100", (748, y + 258), "small", theme.MUTED_TEXT)
    label(app, f"Games: {store.data['games_played']}   |   Best streak: {store.data['best_streak']}",
          (748, y + 298), "small", theme.MUTED_TEXT)
    label(app, "Module 1 + Module 2 Study Game", (748, y + 338), "small", theme.MUTED_TEXT)
    label(app, "Study with feedback or take a timed long quiz.", (720, 588), "small", theme.MUTED_TEXT)
    app.button("about_home", (716, 624, 488, 48), "ABOUT / CREDITS", ("about", None))
    if store.warning:
        text_panel(app, "save_warning", store.warning, (76, 676, 1128, 32), "tiny", theme.ORANGE)


def about(app):
    """Release information and credits; no player data or external resources."""
    label(app, "ABOUT / CREDITS", (76, 124), "small", theme.ORANGE)
    label(app, PROJECT_NAME.upper(), (72, 158), "title")
    card(app, (76, 238, 1128, 366))
    text = (f"Version {__version__}\nDeveloper: {DEVELOPER}\n\n"
            "Built with Python and Pygame Community Edition.\n"
            "Interactive reviewer for ITE184 — Social, Legal and Professional Issues in Computing.\n\n"
            "261 questions / Study Mode / Exam Mode / Written scenario grading / Learning analytics\n\n"
            "Audio effects and background tones were programmatically generated for this project.\n"
            "Third-party libraries retain their own licenses. Original project code uses the MIT License.\n\n"
            "Educational project. Course content is for study purposes, not legal advice.")
    text_panel(app, "about_credits", text, (100, 262, 1080, 304), "small", gap=0)
    app.button("about_back", (76, 638, 1128, 52), "< BACK TO HOME", ("back", None))


def selection_header(app, title, subtitle, step):
    label(app, f"SET UP YOUR QUIZ  /  STEP {step} OF 4", (76, 128), "small", theme.ORANGE)
    label(app, title, (72, 164), "title")
    label(app, subtitle, (76, 222), "body", theme.MUTED_TEXT)
    app.button("back", (76, 626, 170, 52), "<  Back", ("back", None))


def module_select(app):
    selection_header(app, "CHOOSE MODULE", "Choose the material you want to practice.", 1)
    options = [
        (1, "MODULE 1", "Ethics, Moral Theories & Legal Maxims"),
        (2, "MODULE 2", "Computer Crimes, Hacking & IT Laws"),
        (None, "BOTH MODULES", "Mixed Review"),
    ]
    for index, (module, title, subtitle) in enumerate(options):
        app.button(f"module_{index}", (76, 284 + index * 104, 1128, 86), title,
                   ("module", module), subtitle=subtitle, keys=(pygame.K_1 + index,))


def mode_select(app):
    selection_header(app, "CHOOSE GAME MODE", "Choose how you want to practice.", 2)
    modes = [("mcq", "MULTIPLE CHOICE", "Choose from four answers"),
             ("written", "WRITTEN SCENARIOS", "Type the law, offense, theory, or reasoning yourself"),
             ("mixed", "MIXED MODE", "Combination of MCQ and written scenarios")]
    for index, (mode, title, subtitle) in enumerate(modes):
        app.button(f"mode_{index}", (76, 284 + index * 104, 1128, 86), title,
                   ("mode", mode), subtitle=subtitle, keys=(pygame.K_1 + index,))


def difficulty_select(app):
    selection_header(app, "CHOOSE DIFFICULTY", f"{module_name(app.selected_module)} / {app.selected_mode.upper()} - pick your challenge.", 3)
    for index, (difficulty, subtitle) in enumerate([
        ("easy", "Definitions and recognition"), ("medium", "Short scenarios and distinctions"),
        ("hard", "More demanding scenarios"), ("all", "A little of everything"),
    ]):
        x, y = 76 + (index % 2) * 576, 302 + (index // 2) * 120
        title = "ALL DIFFICULTIES" if difficulty == "all" else difficulty.upper()
        app.button(f"difficulty_{index}", (x, y, 552, 100), title,
                   ("difficulty", difficulty), subtitle=subtitle, keys=(pygame.K_1 + index,))


def count_select(app):
    difficulty = "All difficulties" if app.selected_difficulty == "all" else app.selected_difficulty.title()
    selection_header(app, "HOW MANY QUESTIONS?", f"{module_name(app.selected_module)} / {app.selected_mode.upper()} / {difficulty}", 4)
    count = app.matching_count()
    kind = "MCQ" if app.selected_mode == "mcq" else app.selected_mode
    label(app, f"{count} {kind} questions available for this selection.", (76, 268), "body", theme.ORANGE)
    for index, value in enumerate((5, 10, 20, "all")):
        x, y = 76 + (index % 2) * 576, 326 + (index // 2) * 110
        subtitle = f"Play {count if value == 'all' else min(value, count)} questions"
        app.button(f"count_{index}", (x, y, 552, 92), "ALL AVAILABLE" if value == "all" else str(value),
                   ("count", value), subtitle=subtitle, enabled=count > 0, keys=(pygame.K_1 + index,))
    if app.notice:
        text_panel(app, "notice", app.notice, (280, 608, 924, 74), "small", theme.ERROR)


def quiz(app):
    if app.session.current_question["type"] == "written":
        from .written_screens import written_quiz
        written_quiz(app)
        return
    session = app.session
    question = session.current_question
    feedback = app.state == "FEEDBACK"
    mode_label = "MIXED - MCQ" if session.mode == "mixed" else "MCQ"
    label(app, f"MODULE {question['module']} / {question['difficulty'].upper()} / {mode_label}", (64, 112), "small", theme.ORANGE)
    label(app, f"Question {session.current_question_index + 1} / {len(session.questions)}", (64, 142), "title")
    pygame.draw.rect(app.canvas, theme.CARD, (64, 198, 736, 5), border_radius=2)
    progress = (session.current_question_index + 1) / len(session.questions)
    pygame.draw.rect(app.canvas, theme.PURPLE, (64, 198, round(736 * progress), 5), border_radius=2)
    card(app, (64, 219, 736, 196))
    label(app, f"Topic: {question['topic']}", (84, 234), "small", theme.PURPLE)
    label(app, f"Subtopic: {question['subtopic']}", (84, 261), "small", theme.MUTED_TEXT)
    text_panel(app, "question", question["question"], (84, 296, 696, 94), "question")
    for index, (letter, text) in enumerate(session.choices.items()):
        status = None
        suffix = ""
        if feedback:
            if text == question["answer"]:
                status, suffix = "correct", "  [CORRECT]"
            elif letter == session.selected_answer:
                status, suffix = "wrong", "  [YOUR ANSWER]"
        app.button(f"answer_{letter}", (64, 426 + index * 61, 736, 52),
                   f"{letter}   {text}{suffix}", ("answer", letter), enabled=not feedback,
                   status=status, keys=(pygame.K_a + index, pygame.K_1 + index))

    card(app, (832, 114, 384, 548))
    if feedback:
        correct = session.answers[-1]["correct"]
        color = theme.SUCCESS if correct else theme.ERROR
        # A brief fading outline gives feedback without delaying navigation.
        if app.feedback_age < 0.45:
            pygame.draw.rect(app.canvas, color, (832, 114, 384, 548), 2, border_radius=20)
        label(app, "CORRECT!" if correct else "INCORRECT", (856, 140), "title", color)
        label(app, "Correct answer", (856, 198), "small", theme.MUTED_TEXT)
        text_panel(app, "correct_answer", question["answer"], (856, 228, 336, 68), "button")
        detail = "Explanation\n" + question["explanation"]
        if question.get("keywords"):
            detail += "\n\nImportant keywords\n" + "\n".join("- " + k for k in question["keywords"])
        text_panel(app, "explanation", detail, (856, 316, 336, 190), "small")
        label(app, f"Score {session.results['earned_points']} / {session.results['answered_points']}   |   Streak {session.results['current_streak']}",
              (856, 542), "small", theme.MUTED_TEXT)
        app.button("next", (856, 586, 336, 52), "VIEW RESULTS" if session.is_last_question else "NEXT QUESTION  >",
                   ("next", None), primary=True, keys=(pygame.K_RETURN, pygame.K_SPACE))
    else:
        label(app, "SESSION SCORE", (860, 151), "small", theme.MUTED_TEXT)
        label(app, str(session.results["earned_points"]), (856, 192), "hero", theme.PURPLE)
        label(app, f"{session.results['answered']} answered", (860, 290), "body", theme.MUTED_TEXT)
        pygame.draw.line(app.canvas, theme.BORDER, (860, 347), (1188, 347))
        label(app, f"STREAK   {session.results['current_streak']}", (860, 382), "title", theme.ORANGE)
        label(app, f"Best streak: {session.results['best_streak']}", (860, 438), "body", theme.MUTED_TEXT)
        label(app, "Click an answer or press A-D / 1-4.", (860, 510), "small", theme.MUTED_TEXT)
        label(app, "Take your time. There is no timer.", (860, 540), "small", theme.MUTED_TEXT)
    app.button("quit_quiz", (64, 666, 220, 38), "Home / Quit quiz", ("home", None))


def results(app):
    session = app.session
    stats = session.results
    percentage = calculate_percentage(stats["earned_points"], stats["possible_points"])
    perfect = stats["possible_points"] > 0 and stats["earned_points"] == stats["possible_points"]
    label(app, "PERFECT SCORE!" if perfect else "QUIZ COMPLETE", (76, 125), "small", theme.ORANGE)
    label(app, "A little wiser already.", (72, 158), "title")
    difficulty_label = "All difficulties" if stats["difficulty"] == "all" else stats["difficulty"].title()
    label(app, f"{module_name(stats['module'])} / {difficulty_label} / {session.mode.upper()}",
          (76, 208), "small", theme.MUTED_TEXT)
    app.button("review_answers", (990, 146, 214, 54), "REVIEW ANSWERS", ("review", None))
    app.button("rewards", (754, 146, 214, 54), "XP & REWARDS", ("rewards", None))
    card(app, (76, 230, 392, 380))
    label(app, f"{percentage:.1f}%", (102, 250), "large", theme.PURPLE)
    label(app, get_performance_label(percentage).upper(), (106, 330), "button", theme.ORANGE)
    label(app, f"Score: {stats['earned_points']} / {stats['possible_points']}", (106, 374), "body")
    label(app, f"Questions: {stats['answered']}   |   Best streak: {stats['best_streak']}", (106, 416), "small", theme.MUTED_TEXT)
    for index, kind in enumerate(("mcq", "written")):
        points = stats["type_points"][kind]
        label(app, f"{kind.upper()}: {points['earned']} / {points['possible']} points",
              (106, 450 + index * 28), "small", theme.MUTED_TEXT)
    progress = session.progression
    label(app, f"+{progress.total_xp} XP earned", (106, 514), "button", theme.PURPLE)
    label(app, f"Total XP: {app.stats_store.data['total_xp']} / Level {app.stats_store.level}", (106, 548), "small", theme.ORANGE)
    label(app, f"Hearts: {progress.lives}/3   |   {app.stats_store.rank}", (106, 578), "small", theme.MUTED_TEXT)
    if app.stats_store.level > session.start_level:
        label(app, f"LEVEL UP! {session.start_level} -> {app.stats_store.level}", (850, 206), "small", theme.SUCCESS)

    card(app, (492, 230, 712, 358))
    label(app, "TOPIC BREAKDOWN", (520, 254), "button")
    breakdown = "\n".join(f"{topic}    {counts['earned']} / {counts['possible']}"
                          for topic, counts in sorted(stats["point_topics"].items()))
    if stats["module"] is None:
        breakdown += "\n\nMODULE BREAKDOWN\n" + "\n".join(
            f"Module {module}:    {counts['earned']} / {counts['possible']}"
            for module, counts in sorted(stats["point_modules"].items()))
    text_panel(app, "breakdown", breakdown, (520, 304, 656, 280), "small", theme.MUTED_TEXT, gap=0)
    app.button("replay", (76, 622, 348, 56), "PLAY AGAIN", ("replay", None), primary=True)
    app.button("change", (440, 622, 382, 56), "CHANGE SETTINGS", ("change", None))
    app.button("home_results", (838, 622, 366, 56), "MAIN MENU", ("home", None))


def draw(app):
    """Select a layout by state, without starting another event loop."""
    background(app)
    if app.state.startswith("EXAM_"):
        from .exam_screens import draw as draw_exam
        draw_exam(app)
        return
    if app.state in ("STATISTICS", "TOPICS", "ACHIEVEMENTS", "MISTAKES"):
        from .stats_screens import draw_stats_screen
        draw_stats_screen(app)
        return
    if app.state == "REWARDS":
        from .rewards import rewards_screen
        rewards_screen(app)
        return
    if app.state == "REVIEW":
        from .written_screens import review
        review(app)
        return
    {"HOME": home, "ABOUT": about, "MODULE_SELECT": module_select,
     "MODE_SELECT": mode_select,
     "DIFFICULTY_SELECT": difficulty_select, "COUNT_SELECT": count_select,
     "QUIZ": quiz, "FEEDBACK": quiz, "RESULTS": results}[app.state](app)


def draw_overlay(app):
    """Draw one modal over the current screen; only its buttons receive input."""
    shade = pygame.Surface(theme.SIZE, pygame.SRCALPHA)
    shade.fill((0, 0, 0, 185))
    app.canvas.blit(shade, (0, 0))
    card(app, (360, 184, 560, 352))
    if app.overlay == "RESET":
        label(app, "RESET ALL PROGRESS?", (396, 216), "button", theme.ERROR)
        text_panel(app, "reset_warning", "This permanently erases saved XP, levels, statistics, achievements, mistakes and high scores. Your questions stay intact.",
                   (396, 272, 488, 112), "small", theme.MUTED_TEXT)
        app.button("confirm_reset", (396, 414, 232, 62), "RESET", ("confirm_reset", None), primary=True)
        app.button("cancel_reset", (652, 414, 232, 62), "CANCEL", ("close_overlay", None))
    elif app.overlay == "QUIT":
        label(app, "Quit current quiz?", (396, 224), "title")
        notice = ("Leave this quiz? Graded answers remain in memory, but saving needs attention. " if app.stats_store.warning else
                  "Leave this quiz? Graded answers stay in your saved progress. ")
        text_panel(app, "study_quit_notice", notice + "The unfinished quiz will not count as a completed game.",
                   (396, 292, 488, 96), "small", theme.MUTED_TEXT)
        app.button("confirm_quit", (396, 414, 232, 62), "YES, QUIT", ("confirm_quit", None),
                   primary=True, keys=(pygame.K_y,))
        app.button("cancel_quit", (652, 414, 232, 62), "CANCEL", ("close_overlay", None),
                   keys=(pygame.K_n,))
    else:
        label(app, "Audio settings", (396, 220), "title")
        app.button("music_setting", (396, 296, 488, 58),
                   "Music: ON" if app.audio.music_enabled else "Music: OFF", ("music", None))
        app.button("sfx_setting", (396, 368, 488, 58),
                   "Sound effects: ON" if app.audio.sfx_enabled else "Sound effects: OFF", ("sfx", None))
        label(app, "Audio device unavailable - playing silently." if not app.audio.available
              else "Original synthesized tones. Settings last this launch.",
              (396, 443), "small", theme.MUTED_TEXT)
        app.button("close_settings", (396, 478, 488, 40), "DONE", ("close_overlay", None),
                   keys=(pygame.K_RETURN,))
