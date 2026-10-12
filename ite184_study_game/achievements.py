"""Session achievement definitions and pure unlock conditions."""


ACHIEVEMENTS = {
    "first_blood": {"id": "first_blood", "name": "FIRST BLOOD", "xp": 25,
                    "description": "Earn your first successful answer."},
    "on_fire": {"id": "on_fire", "name": "ON FIRE", "xp": 25,
                "description": "Reach a 3-answer streak."},
    "unstoppable": {"id": "unstoppable", "name": "UNSTOPPABLE", "xp": 50,
                    "description": "Reach a 5-answer streak."},
    "perfect_answer": {"id": "perfect_answer", "name": "PERFECT ANSWER", "xp": 25,
                       "description": "Earn 5/5 on a written scenario."},
    "law_student": {"id": "law_student", "name": "LAW STUDENT", "xp": 25,
                    "description": "Successfully answer a legal-maxim question."},
    "cyber_defender": {"id": "cyber_defender", "name": "CYBER DEFENDER", "xp": 25,
                       "description": "Successfully answer Cybercrime or RA 10175 material."},
    "malware_hunter": {"id": "malware_hunter", "name": "MALWARE HUNTER", "xp": 25,
                       "description": "Successfully answer a malware question."},
    "perfect_run": {"id": "perfect_run", "name": "PERFECT RUN", "xp": 50,
                    "description": "Finish a quiz with 100% of its points."},
    "comeback": {"id": "comeback", "name": "COMEBACK", "xp": 25,
                 "description": "Recover a heart after losing one."},
    "mixed_master": {"id": "mixed_master", "name": "MIXED MASTER", "xp": 50,
                     "description": "Complete a Mixed Mode quiz."},
}


def is_successful(question_type: str, score: int) -> bool:
    """A correct MCQ or written score of 4-5 counts as successful."""
    return score == 1 if question_type == "mcq" else score >= 4


def answer_achievements(question: dict, score: int, streak: int, recovered: bool) -> list[str]:
    """Return eligible IDs; Progression handles duplicate prevention and XP."""
    eligible = []
    if is_successful(question["type"], score):
        eligible.append("first_blood")
        if streak >= 3:
            eligible.append("on_fire")
        if streak >= 5:
            eligible.append("unstoppable")
        topic = question["topic"].casefold()
        if topic == "legal maxims":
            eligible.append("law_student")
        text = " ".join(str(question.get(field, "")) for field in
                        ("question", "scenario", "keywords", "keyword_groups")).casefold()
        if topic == "cybercrime" or "ra 10175" in text:
            eligible.append("cyber_defender")
        if topic == "malware":
            eligible.append("malware_hunter")
    if question["type"] == "written" and score == 5:
        eligible.append("perfect_answer")
    if recovered:
        eligible.append("comeback")
    return eligible


def completion_achievements(earned: int, possible: int, mode: str) -> list[str]:
    """Call only for a fully answered quiz, regardless of lives remaining."""
    eligible = []
    if possible > 0 and earned == possible:
        eligible.append("perfect_run")
    if mode == "mixed":
        eligible.append("mixed_master")
    return eligible
