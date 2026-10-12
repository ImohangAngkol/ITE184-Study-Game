"""Written gameplay and current-session review, using existing drawing helpers."""

import pygame
from . import theme
from .screens import label, card, text_panel


def readable(phrase):
    """Show one representative concept rather than every internal synonym."""
    return phrase.upper() if phrase.lower().startswith("ra ") else phrase.capitalize()


def feedback_text(question, grading):
    """Build readable sections for the scrollable written feedback panel."""
    detected = [readable(item["label"]) for item in grading["matched_groups"]]
    detected.extend(readable(item) for item in grading["matched_optional"])
    text = "DETECTED\n" + ("\n".join("- " + item for item in detected) or "No matching concepts yet.")
    if grading["missed_groups"]:
        text += "\n\nMISSED / COULD IMPROVE\n" + "\n".join(
            "- " + readable(item["label"]) for item in grading["missed_groups"])
    else:
        text += "\n\nAll required concepts identified."
    if grading["score"] == 4 and grading["missed_optional"]:
        text += "\nAdd relevant detail, such as: " + ", ".join(grading["missed_optional"][:3])
    text += "\n\nMODEL ANSWER\n" + question["model_answer"]
    text += "\n\nEXPLANATION\n" + question["explanation"]
    return text


def written_quiz(app):
    """Keep scenario, answer box, and submit/navigation visible together."""
    session = app.session
    question = session.current_question
    feedback = app.state == "FEEDBACK"
    mode_label = "MIXED - WRITTEN" if session.mode == "mixed" else "WRITTEN"
    label(app, f"MODULE {question['module']} / {question['difficulty'].upper()} / {mode_label}",
          (64, 112), "small", theme.ORANGE)
    label(app, f"Question {session.current_question_index + 1} / {len(session.questions)}", (64, 142), "title")
    pygame.draw.rect(app.canvas, theme.CARD, (64, 198, 736, 5), border_radius=2)
    progress = (session.current_question_index + 1) / len(session.questions)
    pygame.draw.rect(app.canvas, theme.PURPLE, (64, 198, round(736 * progress), 5), border_radius=2)
    card(app, (64, 219, 736, 202))
    label(app, f"Topic: {question['topic']}", (84, 232), "small", theme.PURPLE)
    label(app, f"Subtopic: {question['subtopic']}", (84, 258), "small", theme.MUTED_TEXT)
    text_panel(app, "scenario", question["scenario"], (84, 290, 696, 108), "question")
    label(app, "YOUR ANSWER" + ("  /  LOCKED" if feedback else ""), (64, 426), "small", theme.ORANGE)
    app.textbox.draw(app.canvas, app.fonts["question"], app.elapsed)
    label(app, f"Characters: {len(app.textbox.text)} / {app.textbox.max_characters}", (64, 604), "small", theme.MUTED_TEXT)
    hint = "Answer locked. Enter continues." if feedback else "Enter submits. Shift+Enter adds a line."
    label(app, hint, (388, 604), "small", theme.MUTED_TEXT)
    app.button("quit_written", (500, 642, 300, 52), "Home / Quit quiz", ("home", None))
    card(app, (832, 114, 384, 548))
    if feedback:
        grading = session.answers[-1]["grading"]
        color = theme.SUCCESS if grading["score"] >= 4 else theme.ORANGE if grading["score"] else theme.ERROR
        label(app, f"{grading['score']} / 5", (856, 140), "large", color)
        label(app, grading["label"], (856, 216), "button", color)
        text_panel(app, "written_feedback", feedback_text(question, grading),
                   (856, 268, 336, 282), "small")
        app.button("next", (856, 586, 336, 52), "VIEW RESULTS" if session.is_last_question else "NEXT QUESTION  >",
                   ("next", None), primary=True, keys=(pygame.K_RETURN, pygame.K_SPACE))
    else:
        label(app, "SESSION POINTS", (860, 151), "small", theme.MUTED_TEXT)
        label(app, str(session.results["earned_points"]), (856, 192), "hero", theme.PURPLE)
        label(app, f"of {session.results['answered_points']} answered points", (860, 290), "small", theme.MUTED_TEXT)
        label(app, f"STREAK   {session.results['current_streak']}", (860, 382), "title", theme.ORANGE)
        label(app, f"Best streak: {session.results['best_streak']}", (860, 438), "body", theme.MUTED_TEXT)
        text_panel(app, "writing_hint", "Name the law, offense or theory, then explain your reasoning. Each scenario is worth 5 points.",
                   (860, 496, 328, 132), "small", theme.MUTED_TEXT)
        app.button("submit_written", (64, 642, 420, 52), "SUBMIT ANSWER", ("submit_written", None), primary=True)
    if app.notice:
        # Keep validation beside the controls, without covering the scenario/input.
        label(app, app.notice, (64, 696), "tiny", theme.ERROR)


def review(app):
    """Browse the current quiz's original player answers and stored models."""
    index = app.review_index
    answer = app.session.answers[index]
    question = app.session.questions[index]
    label(app, "REVIEW ANSWERS", (76, 124), "small", theme.ORANGE)
    label(app, f"Question {index + 1} / {len(app.session.answers)}", (72, 158), "title")
    label(app, f"{answer['earned_points']} / {answer['possible_points']} points  |  {answer['type'].upper()}",
          (76, 214), "body", theme.PURPLE)
    card(app, (76, 264, 532, 328))
    card(app, (632, 264, 572, 328))
    label(app, "QUESTION", (100, 284), "button")
    text_panel(app, "review_question", question.get("scenario", question.get("question", "")),
               (100, 336, 484, 224), "question")
    label(app, "YOUR ANSWER / MODEL", (656, 284), "button")
    model = question.get("model_answer", question.get("answer", ""))
    detail = "Your answer\n" + answer["answer"] + "\n\nModel / correct answer\n" + model
    detail += "\n\nExplanation\n" + question["explanation"]
    text_panel(app, "review_answer", detail, (656, 336, 524, 224), "small")
    app.button("review_previous", (76, 624, 328, 56), "< PREVIOUS", ("review_move", -1), enabled=index > 0)
    app.button("review_results", (428, 624, 424, 56), "BACK TO RESULTS", ("review_done", None))
    app.button("review_next", (876, 624, 328, 56), "NEXT >", ("review_move", 1),
               enabled=index < len(app.session.answers) - 1)
