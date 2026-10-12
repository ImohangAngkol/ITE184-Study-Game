"""Pygame-free XP, levels, ranks, lives, and achievements for one quiz."""

if __package__:
    from .achievements import ACHIEVEMENTS, answer_achievements, completion_achievements
    from .achievements import is_successful
else:
    from achievements import ACHIEVEMENTS, answer_achievements, completion_achievements
    from achievements import is_successful


WRITTEN_XP = (0, 2, 6, 12, 20, 25)
STREAK_BONUSES = {3: 10, 5: 20, 10: 50}
RANKS = ("IT Apprentice", "Cyber Student", "Security Analyst", "Ethical Hacker",
         "Cyber Law Specialist", "Cyber Law Master")
MAX_LIVES = 3


def calculate_xp(question_type: str, score: int) -> int:
    """Convert answer points into base XP using the Phase 6 reward table."""
    if question_type == "mcq" and score in (0, 1):
        return score * 10
    if question_type == "written" and 0 <= score <= 5:
        return WRITTEN_XP[score]
    raise ValueError("Expected MCQ score 0-1 or written score 0-5.")


def calculate_level(total_xp: int) -> int:
    """Each 100 XP starts another level, beginning at level 1."""
    return max(0, total_xp) // 100 + 1


def get_rank(level: int) -> str:
    """Levels 6 and above share the final rank title."""
    return RANKS[min(max(level, 1), len(RANKS)) - 1]


def update_lives(lives: int, question_type: str, score: int, streak: int) -> int:
    """Clamp lives and recover one at streak 3, 6, 9... after success."""
    lives = max(0, min(MAX_LIVES, lives))
    loses_heart = score == 0 if question_type == "mcq" else score <= 2
    if loses_heart:
        return max(0, lives - 1)
    if is_successful(question_type, score) and streak > 0 and streak % 3 == 0:
        return min(MAX_LIVES, lives + 1)
    return lives


class Progression:
    """Keep rewards local to a quiz; sets prevent repeated payouts/unlocks."""

    def __init__(self, unlocked_ids=(), *, track_lives=True):
        self.track_lives = track_lives
        self.base_xp = 0
        self.streak_xp = 0
        self.achievement_xp = 0
        self.lives = MAX_LIVES
        self.awarded_streaks = set()
        self.achievement_order = list(dict.fromkeys(identifier for identifier in unlocked_ids
                                                    if identifier in ACHIEVEMENTS))
        self.unlocked_ids = set(self.achievement_order)
        self.previously_unlocked = set(self.unlocked_ids)
        self.answered_ids = set()
        self.completed = False

    @property
    def total_xp(self) -> int:
        return self.base_xp + self.streak_xp + self.achievement_xp

    @property
    def level(self) -> int:
        return calculate_level(self.total_xp)

    @property
    def rank(self) -> str:
        return get_rank(self.level)

    @property
    def level_progress(self) -> int:
        return self.total_xp % 100

    @property
    def achievements(self) -> list[dict]:
        """Return display copies in the order they were unlocked."""
        return [{**ACHIEVEMENTS[identifier], "already_unlocked": identifier in self.previously_unlocked}
                for identifier in self.achievement_order]

    def _unlock(self, eligible: list[str]) -> list[dict]:
        unlocked = []
        for identifier in eligible:
            if identifier not in self.unlocked_ids:
                self.unlocked_ids.add(identifier)
                self.achievement_order.append(identifier)
                achievement = dict(ACHIEVEMENTS[identifier])
                self.achievement_xp += achievement["xp"]
                unlocked.append(achievement)
        return unlocked

    def reward_answer(self, question: dict, score: int, streak: int) -> dict:
        """Award exactly once per question and return animation-friendly deltas."""
        reward = {"base_xp": 0, "streak_xp": 0, "achievement_xp": 0,
                  "total_xp": 0, "heart_delta": 0, "achievements": []}
        if question["id"] in self.answered_ids or self.completed:
            return reward
        base = calculate_xp(question["type"], score)
        self.answered_ids.add(question["id"])
        self.base_xp += base
        reward["base_xp"] = base
        if is_successful(question["type"], score):
            for threshold, bonus in STREAK_BONUSES.items():
                if streak >= threshold and threshold not in self.awarded_streaks:
                    self.awarded_streaks.add(threshold)
                    self.streak_xp += bonus
                    reward["streak_xp"] += bonus
        new_lives = update_lives(self.lives, question["type"], score, streak) if self.track_lives else self.lives
        reward["heart_delta"] = new_lives - self.lives
        self.lives = new_lives
        reward["achievements"] = self._unlock(answer_achievements(
            question, score, streak, reward["heart_delta"] > 0))
        reward["achievement_xp"] = sum(item["xp"] for item in reward["achievements"])
        reward["total_xp"] = base + reward["streak_xp"] + reward["achievement_xp"]
        return reward

    def complete_quiz(self, earned: int, possible: int, mode: str) -> dict:
        """Unlock finishing rewards once; callers verify the quiz is complete."""
        reward = {"base_xp": 0, "streak_xp": 0, "achievement_xp": 0,
                  "total_xp": 0, "heart_delta": 0, "achievements": []}
        if self.completed or possible <= 0:
            return reward
        self.completed = True
        reward["achievements"] = self._unlock(completion_achievements(earned, possible, mode))
        reward["achievement_xp"] = sum(item["xp"] for item in reward["achievements"])
        reward["total_xp"] = reward["achievement_xp"]
        return reward
