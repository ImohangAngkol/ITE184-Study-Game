"""Exam layouts: active screens read only the safe player-question projection."""

import pygame
from . import theme
from .screens import label, card, text_panel, module_name

if "." in __package__:
    from ..exam_session import format_time
else:
    from exam_session import format_time


def difficulty_name(value):
    return {"all": "All difficulties", "long_quiz": "Long Quiz Mix"}.get(value, value.title())


def header(app, title, subtitle=""):
    label(app, "ITE184 LONG QUIZ SIMULATOR", (76, 122), "small", theme.ORANGE)
    label(app, title, (72, 156), "title")
    if subtitle:
        text_panel(app, "exam_subtitle", subtitle, (76, 215, 1128, 52), "body", theme.MUTED_TEXT)


def back(app):
    app.button("exam_back", (76, 638, 180, 52), "< BACK", ("back", None))
    if app.notice:
        text_panel(app, "exam_notice", app.notice, (280, 638, 924, 52), "small", theme.ERROR)


def setup(app):
    exam, state = app.exam, app.state
    config = exam.config
    if state == "EXAM_MENU":
        header(app, "EXAM MODE", "Choose the course preset or build your own exam. Results appear after submission.")
        app.button("atty_preset", (76, 296, 1128, 108), "ATTY LONG QUIZ", ("exam_preset", None), primary=True,
                   subtitle="Both modules / Mixed / Long Quiz Mix / 30 questions / 45 minutes")
        app.button("custom_exam", (76, 428, 1128, 108), "CUSTOM EXAM", ("exam_custom_setup", None),
                   subtitle="Choose modules, type, difficulty, count and timer")
    elif state in ("EXAM_MODULE", "EXAM_TYPE"):
        header(app, "CHOOSE MODULE" if state == "EXAM_MODULE" else "CHOOSE QUESTION TYPE")
        options = [(1, "MODULE 1"), (2, "MODULE 2"), (None, "BOTH MODULES")] if state == "EXAM_MODULE" else [
            ("mcq", "MULTIPLE CHOICE"), ("written", "WRITTEN"), ("mixed", "MIXED")]
        action = "exam_module" if state == "EXAM_MODULE" else "exam_type"
        for index, (value, text) in enumerate(options):
            app.button(f"exam_option_{index}", (76, 284 + index * 102, 1128, 82), text, (action, value))
    elif state == "EXAM_DIFFICULTY":
        header(app, "CHOOSE DIFFICULTY", f"{module_name(config['module'])} / {config['mode'].upper()}")
        for index, value in enumerate(("easy", "medium", "hard", "all", "long_quiz")):
            x, y = 76 + index % 2 * 576, 288 + index // 2 * 106
            app.button(f"exam_difficulty_{index}", (x, y, 552, 88), difficulty_name(value).upper(),
                       ("exam_difficulty", value), primary=value == "long_quiz",
                       subtitle="20% easy / 40% medium / 40% hard" if value == "long_quiz" else "")
    elif state == "EXAM_COUNT":
        header(app, "NUMBER OF QUESTIONS", f"{exam.available()} questions available for this selection.")
        for index, value in enumerate((10, 20, 30, 50, "all", "custom")):
            x, y = 76 + index % 2 * 576, 288 + index // 2 * 106
            text = "ALL AVAILABLE" if value == "all" else str(value).upper()
            action = ("exam_custom", "count") if value == "custom" else ("exam_count", value)
            app.button(f"exam_count_{index}", (x, y, 552, 88), text, action)
    elif state == "EXAM_TIMER":
        header(app, "EXAM TIMER", "Timer continues during settings, question review and loss of window focus.")
        for index, value in enumerate((None, 15, 30, 45, 60, "custom")):
            x, y = 76 + index % 2 * 576, 288 + index // 2 * 106
            text = "NO TIMER" if value is None else "CUSTOM" if value == "custom" else f"{value} MINUTES"
            action = ("exam_custom", "timer") if value == "custom" else ("exam_timer", value)
            app.button(f"exam_timer_{index}", (x, y, 552, 88), text, action)
    elif state == "EXAM_CUSTOM":
        count = exam.custom_field == "count"
        header(app, "CUSTOM QUESTION COUNT" if count else "CUSTOM TIMER",
               f"Enter 1–{exam.available()} questions. Larger requests need confirmation." if count else "Enter 1–180 minutes.")
        exam.input.draw(app.canvas, app.fonts["question"], app.elapsed)
        app.button("apply_custom", (76, 478, 1128, 72), "CONTINUE", ("exam_apply_custom", None), primary=True)
    elif state == "EXAM_INSTRUCTIONS":
        header(app, "EXAM INSTRUCTIONS")
        count = exam.available() if config["question_count"] == "all" else config["question_count"]
        minutes = config["timer_minutes"]
        text = (f"{module_name(config['module'])} / {config['mode'].upper()} / {difficulty_name(config['difficulty'])}\n"
                f"Questions: {count}   |   Time: {'No timer' if minutes is None else str(minutes) + ' minutes'}\n\n"
                "No immediate feedback, explanations or keyword hints.\n"
                "Move backward/forward, change answers, and flag questions.\n"
                "Unanswered questions receive zero points.\n"
                "Written responses use the same keyword-group scorer after submission.\n"
                "The timer starts when you click START EXAM. Time expiry submits automatically.\n"
                "Settings and question palette do not pause the timer.\n"
                "Your answers are kept in memory. Leaving abandons this exam without grading.")
        card(app, (76, 234, 1128, 354))
        text_panel(app, "exam_instructions", text, (100, 254, 1080, 300), "small", gap=2)
        app.button("exam_begin", (280, 638, 924, 52), "START EXAM", ("exam_start", None), primary=True)
    back(app)


def active_question(app):
    session, controller = app.exam.session, app.exam
    question = session.player_question
    # Answer key, subtopic, model and keyword data are intentionally absent here.
    card(app, (318, 18, 620, 78))
    label(app, "EXAM IN PROGRESS", (338, 28), "small", theme.ORANGE)
    label(app, "Time remaining: " + format_time(session.remaining_time), (338, 57), "small")
    if session.remaining_time is not None and session.remaining_time <= 300:
        warning = "1 minute remaining" if session.remaining_time <= 60 else "5 minutes remaining"
        label(app, warning, (690, 57), "tiny", theme.ORANGE)
    label(app, f"{module_name(session.module)} / {session.mode.upper()}", (64, 116), "small", theme.ORANGE)
    label(app, f"Question {session.current_question_index + 1} / {session.question_count}", (64, 143), "title")
    flag = question["id"] in session.flags
    label(app, "[F] FLAGGED" if flag else "[ ] NOT FLAGGED", (860, 155), "small", theme.ORANGE if flag else theme.MUTED_TEXT)
    pygame.draw.rect(app.canvas, theme.BORDER, (64, 193, 1152, 5), border_radius=2)
    pygame.draw.rect(app.canvas, theme.PURPLE,
                     (64, 193, round(1152 * (session.question_count - len(session.unanswered_ids)) / session.question_count), 5), border_radius=2)
    card(app, (64, 211, 1152, 166))
    label(app, "Topic: " + question["topic"], (84, 229), "small", theme.PURPLE)
    text_panel(app, "exam_question", question.get("question", question.get("scenario", "")),
               (84, 268, 1112, 96), "question")
    if question["type"] == "mcq":
        selected = session.answers.get(question["id"])
        for index, (letter, text) in enumerate(question["exam_choices"].items()):
            is_selected = text == selected
            app.button(f"exam_answer_{letter}", (64, 391 + index * 53, 1152, 45),
                       f"{letter}   {text}" + ("  [SELECTED]" if is_selected else ""), ("exam_select", letter),
                       primary=is_selected, keys=(pygame.K_a + index, pygame.K_1 + index))
    else:
        label(app, "YOUR ANSWER / EDITABLE", (64, 394), "small", theme.ORANGE)
        controller.response.draw(app.canvas, app.fonts["question"], app.elapsed)
    count = session.question_count - len(session.unanswered_ids)
    label(app, f"Answered {count} / {session.question_count}  |  Unanswered {len(session.unanswered_ids)}  |  Flagged {len(session.flags)}",
          (64, 597), "small", theme.MUTED_TEXT)
    app.button("exam_clear", (986, 590, 230, 30), "CLEAR ANSWER", ("exam_clear", None))
    controls = [("PREVIOUS", ("exam_move", -1), 64, 180, session.current_question_index > 0),
                ("UNFLAG" if flag else "FLAG FOR REVIEW", ("exam_flag", None), 256, 244, True),
                ("NEXT", ("exam_move", 1), 512, 180, session.current_question_index < session.question_count - 1),
                ("QUESTIONS", ("exam_palette", None), 704, 192, True),
                ("SUBMIT EXAM", ("exam_submit", None), 908, 308, True)]
    for index, (text, action, x, width, enabled) in enumerate(controls):
        app.button(f"exam_navigation_{index}", (x, 641, width, 52), text, action,
                   enabled=enabled, primary=index == 4)


def overlay(app):
    shade = pygame.Surface((1280, 720), pygame.SRCALPHA)
    shade.fill((0, 0, 0, 190))
    app.canvas.blit(shade, (0, 0))
    controller, session = app.exam, app.exam.session
    if app.overlay == "EXAM_PALETTE":
        card(app, (192, 100, 896, 586))
        label(app, "QUESTION PALETTE", (220, 120), "title")
        status = session.confirmation()
        label(app, f"Answered {status['answered']} / Unanswered {status['unanswered']} / Flagged {status['flagged']}", (220, 178), "small")
        label(app, "A = answered   ? = unanswered   F = flagged   * = current", (220, 208), "small", theme.ORANGE)
        offset = controller.palette_page * 40
        for position, index in enumerate(range(offset, min(offset + 40, session.question_count))):
            question = session.questions[index]
            state = "?" if question["id"] in session.unanswered_ids else "A"
            state += " F" if question["id"] in session.flags else ""
            state += " *" if index == session.current_question_index else ""
            app.button(f"exam_palette_{index}", (220 + position % 8 * 104, 248 + position // 8 * 61, 92, 48),
                       f"{index + 1} {state}", ("exam_jump", index), primary=index == session.current_question_index)
        pages = (session.question_count - 1) // 40 + 1
        label(app, f"Page {controller.palette_page + 1} / {pages} / timer keeps running", (220, 570), "small", theme.MUTED_TEXT)
        app.button("exam_palette_previous", (220, 608, 250, 48), "< PAGE", ("exam_palette_page", -1), enabled=controller.palette_page > 0)
        app.button("exam_palette_next", (482, 608, 250, 48), "PAGE >", ("exam_palette_page", 1), enabled=controller.palette_page < pages - 1)
        app.button("exam_palette_close", (744, 608, 300, 48), "CLOSE", ("close_overlay", None))
    elif app.overlay == "EXAM_SUBMIT":
        card(app, (254, 158, 772, 484))
        label(app, "SUBMIT EXAM?", (282, 186), "title")
        status = session.confirmation()
        text = (f"Answered: {status['answered']} / {status['total']}\nUnanswered: {status['unanswered']}\n"
                f"Flagged: {status['flagged']}\nTime remaining: {format_time(status['remaining_time'])}\n\n"
                + ("Unanswered questions receive zero points." if status["unanswered"] else "All questions have an answer.")
                + " Final answers will be graded and saved.")
        text_panel(app, "exam_confirm_summary", text, (282, 250, 716, 230), "body", gap=0)
        app.button("exam_review_unanswered", (282, 494, 346, 50), "REVIEW UNANSWERED", ("exam_review_pending", "unanswered"), enabled=status["unanswered"] > 0)
        app.button("exam_review_flagged", (652, 494, 346, 50), "REVIEW FLAGGED", ("exam_review_pending", "flagged"), enabled=status["flagged"] > 0)
        app.button("exam_final_submit", (282, 562, 346, 50), "SUBMIT ANYWAY" if status["unanswered"] else "SUBMIT EXAM", ("exam_confirm_submit", None), primary=True)
        app.button("exam_cancel_submit", (652, 562, 346, 50), "CANCEL", ("close_overlay", None))
    elif app.overlay == "EXAM_EXIT":
        card(app, (254, 186, 772, 390))
        label(app, "EXIT EXAM?", (282, 220), "title")
        text_panel(app, "exam_exit_text", "This exam will be abandoned. Your answers will not be graded or submitted. No exam rewards or statistics will be added.",
                   (282, 292, 716, 128), "body")
        app.button("exam_leave", (282, 466, 346, 70), "EXIT EXAM", ("exam_abandon", None), primary=True)
        app.button("exam_continue", (652, 466, 346, 70), "CONTINUE EXAM", ("close_overlay", None))
    elif app.overlay == "EXAM_COUNT_LIMIT":
        card(app, (254, 186, 772, 390))
        label(app, "AVAILABLE QUESTION LIMIT", (282, 220), "title")
        text_panel(app, "exam_count_warning", f"You requested {controller.pending_count} questions. This selection has {controller.available()} available. Use all {controller.available()} instead?",
                   (282, 292, 716, 128), "body")
        app.button("exam_reduce_count", (282, 466, 346, 70), "USE AVAILABLE COUNT", ("exam_accept_count", None), primary=True)
        app.button("exam_cancel_count", (652, 466, 346, 70), "CANCEL", ("close_overlay", None))


def results(app):
    result = app.exam.session.results
    subtitle = ("Final answers graded. Progress retained in memory; saving needs attention." if app.stats_store.warning else
                "Your exam has been submitted." if result["auto_submitted"] else "Final answers graded and saved.")
    header(app, "TIME IS UP / EXAM COMPLETE" if result["auto_submitted"] else "EXAM COMPLETE", subtitle)
    card(app, (76, 282, 416, 298))
    label(app, f"{result['percentage']:.1f}%", (104, 298), "large", theme.PURPLE)
    label(app, f"Score {result['earned_points']} / {result['possible_points']}", (104, 368), "body")
    label(app, result["label"].upper(), (104, 406), "button", theme.ORANGE)
    summary = (f"Questions: {result['question_count']} / Answered: {result['answered']}\n"
               f"Unanswered: {result['unanswered']} / Flagged: {result['flagged']}\n"
               f"Time used: {format_time(result['time_used'])}\nBest streak: {result['best_streak']} / +{result['xp']} XP")
    text_panel(app, "exam_result_summary", summary, (104, 452, 360, 104), "small", gap=0)
    card(app, (516, 282, 688, 298))
    details = "MODULE PERFORMANCE\n" + "\n".join(
        f"Module {key}: {row['earned']} / {row['possible']} ({row['earned'] / row['possible'] * 100:.1f}%)"
        for key, row in sorted(result["modules"].items()))
    details += "\nQUESTION TYPE\n" + "\n".join(
        f"{key.upper()}: {row['earned']} / {row['possible']}" for key, row in result["type_points"].items())
    details += "\nWEAKEST AREAS\n" + "\n".join(
        f"{index}. {row['topic']}: {row['percentage']:.1f}%" for index, row in enumerate(result["weakest_topics"], 1))
    details += "\n\nACHIEVEMENTS\n" + ("\n".join(a["name"] for a in result["achievements"]) or "No new unlocks this exam.")
    text_panel(app, "exam_result_breakdown", details, (540, 302, 640, 246), "small", gap=0)
    for index, (title, action) in enumerate((
            ("REVIEW EXAM", "exam_review"), ("REVIEW MISTAKES", "mistakes"),
            ("TAKE ANOTHER EXAM", "exam_again"), ("MAIN MENU", "home"))):
        app.button(f"exam_result_action_{index}", (76 + index * 288, 616, 264, 52), title, (action, None), primary=index == 0)
    if app.stats_store.warning:
        text_panel(app, "exam_save_warning", app.stats_store.warning, (76, 678, 844, 30), "tiny", theme.ORANGE)
        app.button("exam_retry_save", (948, 678, 256, 30), "RETRY SAVE", ("exam_retry_save", None))


def review(app):
    controller, session = app.exam, app.exam.session
    indices = session.review_indices(controller.review_filter)
    header(app, "EXAM ANSWER REVIEW")
    for index, (value, title) in enumerate((("all", "ALL"), ("partial", "INCORRECT / PARTIAL"),
                                          ("flagged", "FLAGGED"), ("unanswered", "UNANSWERED"))):
        app.button(f"exam_filter_{index}", (76 + index * 288, 218, 264, 46), title,
                   ("exam_review_filter", value), primary=controller.review_filter == value)
    if indices:
        original_index = indices[controller.review_position]
        question = session.questions[original_index]
        answer = session.results["answers"][original_index]
        label(app, f"Question {original_index + 1} / {session.question_count} / {answer['earned_points']} of {answer['possible_points']} points",
              (76, 283), "body", theme.ORANGE)
        card(app, (76, 328, 532, 266))
        card(app, (632, 328, 572, 266))
        text_panel(app, "exam_review_question", question.get("question", question.get("scenario", "")),
                   (100, 350, 484, 216), "question")
        detail = "YOUR ANSWER\n" + (answer["answer"] if not answer["unanswered"] else "Unanswered")
        detail += "\n\n" + ("MODEL ANSWER" if answer["type"] == "written" else "CORRECT ANSWER")
        detail += "\n" + question.get("model_answer", question.get("answer", ""))
        detail += "\n\nEXPLANATION\n" + question["explanation"]
        if answer["grading"] is not None:
            grade = answer["grading"]
            detail += "\n\nMATCHED CONCEPTS\n" + ("\n".join(g["label"] for g in grade["matched_groups"]) or "None")
            detail += "\n\nMISSED CONCEPTS\n" + ("\n".join(g["label"] for g in grade["missed_groups"]) or "None")
        keywords = question.get("keywords", [g[0] for g in question.get("keyword_groups", [])])
        detail += "\n\nIMPORTANT KEYWORDS\n" + "\n".join(keywords)
        text_panel(app, "exam_review_answer", detail, (656, 350, 524, 216), "small")
    else:
        text_panel(app, "exam_review_empty", "No questions match this review filter.", (76, 328, 1128, 230), "body")
    app.button("exam_review_previous", (76, 636, 328, 52), "< PREVIOUS", ("exam_review_move", -1), enabled=bool(indices) and controller.review_position > 0)
    app.button("exam_review_results", (428, 636, 424, 52), "BACK TO EXAM RESULTS", ("exam_results", None))
    app.button("exam_review_next", (876, 636, 328, 52), "NEXT >", ("exam_review_move", 1), enabled=bool(indices) and controller.review_position < len(indices) - 1)


def history(app):
    header(app, "EXAM HISTORY", "The last 10 submitted exam summaries. Detailed review is available for the current session.")
    text = "\n\n".join(
        f"{row['date']} / {module_name(None if row['module'] == 'both' else row['module'])}\n"
        f"{row['mode'].upper()} / {difficulty_name(row['difficulty'])} / {row['question_count']} questions\n"
        f"Score {row['score_earned']} / {row['score_possible']} / {row['percentage']:.1f}% / Time {format_time(row['time_used'])}"
        for row in reversed(app.stats_store.data["exam_history"])) or "No completed exams yet."
    card(app, (76, 286, 1128, 310))
    text_panel(app, "exam_history", text, (100, 310, 1080, 252), "small")
    back(app)


def draw(app):
    if app.state == "EXAM_QUESTION":
        active_question(app)
    elif app.state == "EXAM_RESULTS":
        results(app)
    elif app.state == "EXAM_REVIEW":
        review(app)
    elif app.state == "EXAM_HISTORY":
        history(app)
    else:
        setup(app)
