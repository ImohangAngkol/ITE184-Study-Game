"""Persistent statistics, weak topics, achievements, and mistake review setup."""

from . import theme
from .screens import label, card, text_panel

if "." in __package__:
    from ..stats import get_accuracy, get_topic_stats, get_weak_topics
    from ..achievements import ACHIEVEMENTS
else:
    from stats import get_accuracy, get_topic_stats, get_weak_topics
    from achievements import ACHIEVEMENTS


def percentage(earned, possible):
    value = get_accuracy(earned, possible)
    return "N/A" if value is None else f"{value:.1f}%"


def statistics(app):
    store, data = app.stats_store, app.stats_store.data
    label(app, "YOUR SAVED STUDY RECORD", (76, 124), "small", theme.ORANGE)
    label(app, "STATISTICS", (72, 158), "title")
    panels = [
        ("PLAYER", f"Level: {store.level}\nRank: {store.rank}\nTotal XP: {data['total_xp']}\n"
         f"Games played: {data['games_played']}\nQuestions answered: {data['questions_answered']}\n"
         f"Best streak: {data['best_streak']}\n\nMistakes to review: {len(store.get_active_mistakes())}"),
        ("PERFORMANCE", f"Overall points: {data['total_points_earned']} / {data['total_points_possible']}\n"
         f"Overall: {percentage(data['total_points_earned'], data['total_points_possible'])}\n\n"
         f"MCQ: {data['mcq']['correct']} / {data['mcq']['answered']}\n"
         f"Accuracy: {percentage(data['mcq']['correct'], data['mcq']['answered'])}\n\n"
         f"Written: {data['written']['points_earned']} / {data['written']['points_possible']}\n"
         f"Score: {percentage(data['written']['points_earned'], data['written']['points_possible'])}\n"
         f"Perfect answers: {data['written']['perfect_answers']}"),
        ("MODULES / HIGH SCORES", "\n".join(
            f"Module {key}: {percentage(counts['earned'], counts['possible'])}"
            for key, counts in data["modules"].items()) + "\n\nBest completed quiz\n" + "\n".join(
            f"{name}: {data['high_scores'][key]:.1f}%" if data['high_score_counts'][key] else f"{name}: N/A"
            for name, key in zip(("Overall", "Module 1", "Module 2", "Mixed"), data["high_scores"]))),
    ]
    exams = data["exams"]
    exam_text = f"\n\nEXAM PERFORMANCE\nExams completed: {exams['completed']}\n"
    for name, key in (("Best", "best_percentage"), ("Average", "average_percentage"), ("Last exam", "last_score")):
        exam_text += f"{name}: " + (f"{exams[key]:.1f}%" if exams["completed"] else "N/A") + "\n"
    for name, prefix in (("Module 1 best", "module_1"), ("Module 2 best", "module_2"), ("Both modules best", "both")):
        exam_text += f"{name}: " + (f"{exams[prefix + '_best']:.1f}%" if exams[prefix + "_completed"] else "N/A") + "\n"
    title, text = panels[2]
    panels[2] = (title, text + exam_text)
    for index, (title, text) in enumerate(panels):
        x = 76 + index * 384
        card(app, (x, 238, 360, 344))
        label(app, title, (x + 20, 260), "small", theme.PURPLE)
        text_panel(app, f"stats_{index}", text, (x + 20, 306, 320, 246), "small", theme.MUTED_TEXT)
    for index, (title, action) in enumerate((
        ("REVIEW MISTAKES", "mistakes"), ("TOPIC STATS", "topics"),
        ("ACHIEVEMENTS", "achievements"), ("RESET STATISTICS", "reset_stats"),
    )):
        app.button(f"stats_action_{index}", (76 + index * 288, 606, 264, 48), title, (action, None))
    app.button("stats_back", (76, 666, 170, 38), "< Back", ("back", None))
    app.button("exam_history", (268, 666, 300, 38), "EXAM HISTORY", ("exam_history", None))
    notice = store.warning or app.notice
    if notice:
        text_panel(app, "stats_notice", notice, (596, 666, 608, 40), "tiny", theme.ORANGE)


def topics(app):
    data = app.stats_store.data
    label(app, "KNOW WHAT TO STUDY NEXT", (76, 124), "small", theme.ORANGE)
    label(app, "TOPIC STATISTICS", (72, 158), "title")
    card(app, (76, 238, 712, 370))
    card(app, (812, 238, 392, 370))
    label(app, "LOWEST PERFORMANCE FIRST", (100, 260), "button")
    lines = []
    for row in get_topic_stats(data):
        percent = "N/A" if row["percentage"] is None else f"{row['percentage']:.1f}%"
        weak = " - NEEDS REVIEW" if row["attempts"] >= 2 and row["percentage"] is not None and row["percentage"] < 70 else ""
        lines.append(f"{row['topic']}  /  {percent}{weak}\n"
                     f"{row['earned']} / {row['possible']} points - {row['attempts']} attempts")
    text_panel(app, "topic_statistics", "\n\n".join(lines) or "Answer some questions to build your topic record.",
               (100, 308, 664, 268), "small", theme.MUTED_TEXT)
    label(app, "WEAK AREAS", (836, 260), "button", theme.ORANGE)
    weak = get_weak_topics(data)
    text = "\n\n".join(f"{index}. {row['topic']}\n{row['percentage']:.1f}%"
                        for index, row in enumerate(weak[:5], 1)) or "No weak areas yet.\n\nA topic needs at least 2 attempts and a score below 70%."
    text_panel(app, "weak_topics", text, (836, 308, 344, 268), "small", theme.MUTED_TEXT)
    app.button("topics_back", (76, 636, 1128, 52), "BACK TO STATISTICS", ("back", None))


def achievements(app):
    unlocked = set(app.stats_store.data["achievements"])
    label(app, "PERMANENT UNLOCKS", (76, 124), "small", theme.ORANGE)
    label(app, f"ACHIEVEMENTS / {len(unlocked)} OF {len(ACHIEVEMENTS)}", (72, 158), "title")
    card(app, (76, 238, 1128, 370))
    text = "\n\n".join(f"{'[UNLOCKED]' if key in unlocked else '[LOCKED]'} {item['name']}\n"
                        f"{item['description']}  -  {item['xp']} XP once"
                        for key, item in ACHIEVEMENTS.items())
    text_panel(app, "saved_achievements", text, (100, 264, 1080, 312), "small", theme.MUTED_TEXT)
    app.button("achievements_back", (76, 636, 1128, 52), "BACK TO STATISTICS", ("back", None))


def mistakes(app):
    questions = app.stats_store.get_active_mistakes()
    label(app, "FOCUS ON WHAT YOU MISSED", (76, 124), "small", theme.ORANGE)
    label(app, "REVIEW MISTAKES" if questions else "NO QUESTIONS TO REVIEW", (72, 158), "title")
    if not questions:
        text_panel(app, "no_mistakes", "You're caught up!\n\nQuestions you answer incorrectly will appear here.",
                   (76, 260, 1128, 250), "body", theme.MUTED_TEXT)
    else:
        label(app, f"Questions to review: {len(questions)}", (76, 222), "body", theme.MUTED_TEXT)
        choices = [("REVIEW ALL", (None, None)), ("MODULE 1", (1, None)),
                   ("MODULE 2", (2, None)), ("MCQ ONLY", (None, "mcq")),
                   ("WRITTEN ONLY", (None, "written"))]
        for index, (title, filters) in enumerate(choices):
            count = len(app.stats_store.get_active_mistakes(*filters))
            x, y = 76 + index % 2 * 576, 280 + index // 2 * 104
            app.button(f"mistake_filter_{index}", (x, y, 552, 84), title,
                       ("review_mistakes", filters), subtitle=f"{count} question{'s' if count != 1 else ''}", enabled=count > 0)
    app.button("mistakes_back", (76, 626, 240, 52), "< Back", ("back", None))
    if app.notice:
        text_panel(app, "review_notice", app.notice, (340, 626, 864, 56), "small", theme.ORANGE)


def draw_stats_screen(app):
    {"STATISTICS": statistics, "TOPICS": topics, "ACHIEVEMENTS": achievements,
     "MISTAKES": mistakes}[app.state](app)
