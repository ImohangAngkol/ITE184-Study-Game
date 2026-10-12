"""Shared progression HUD, passive reward popups, and detailed reward results."""

import pygame
from . import theme
from .screens import label, card, text_panel


def draw_heart(surface, position, filled):
    """Draw a small heart with primitives so no special font is required."""
    x, y = position
    color = theme.ERROR if filled else theme.BORDER
    pygame.draw.circle(surface, color, (x + 5, y + 5), 5)
    pygame.draw.circle(surface, color, (x + 13, y + 5), 5)
    pygame.draw.polygon(surface, color, [(x, y + 6), (x + 18, y + 6), (x + 9, y + 18)])


def draw_hud(app):
    """Keep score, XP, rank, level, streak, and hearts visible across quiz types."""
    if app.state not in ("QUIZ", "FEEDBACK") or app.session is None:
        return
    progress = app.session.progression
    stats = app.session.results
    store = app.stats_store
    total_xp, level, rank = store.data["total_xp"], store.level, store.rank
    card(app, (318, 18, 620, 78))
    label(app, f"Score {stats['earned_points']} / {stats['possible_points']}", (334, 26), "small")
    label(app, f"XP {total_xp}", (486, 26), "small", theme.PURPLE)
    label(app, f"LVL {level}", (584, 26), "small")
    label(app, rank, (654, 29), "tiny", theme.ORANGE)
    label(app, f"Streak {stats['current_streak']}", (842, 29), "tiny", theme.ORANGE)
    for index in range(3):
        draw_heart(app.canvas, (334 + index * 24, 64), index < progress.lives)
    label(app, f"Lives {progress.lives}/3", (412, 62), "tiny", theme.MUTED_TEXT)
    if progress.lives == 0:
        label(app, "NO HEARTS LEFT - KEEP STUDYING!", (492, 62), "tiny", theme.ORANGE)
    if store.warning:
        text_panel(app, "save_status", store.warning, (848, 666, 356, 40), "tiny", theme.ORANGE)
    label(app, f"{total_xp % 100} / 100 to next level", (754, 52), "tiny", theme.MUTED_TEXT)
    pygame.draw.rect(app.canvas, theme.BORDER, (754, 80, 164, 5), border_radius=2)
    pygame.draw.rect(app.canvas, theme.PURPLE,
                     (754, 80, round(164 * (total_xp % 100) / 100), 5), border_radius=2)
    if app.reward_age < 0.6 and app.last_reward and app.last_reward["heart_delta"]:
        color = theme.ERROR if app.last_reward["heart_delta"] < 0 else theme.SUCCESS
        pygame.draw.rect(app.canvas, color, (328, 57, 155, 33), 2, border_radius=8)


def floating_label(app, text, position, color, age, style="button"):
    """Move and fade one short reward line; it never captures input."""
    image = app.fonts[style].render(text, True, color)
    image.set_alpha(max(0, int(255 * (1 - age / 2.2))))
    app.canvas.blit(image, (position[0], position[1] - int(age * 8)))


def draw_popups(app):
    """Draw nonblocking reward text and one queued achievement at a time."""
    if app.overlay or app.session is None or app.state not in ("QUIZ", "FEEDBACK", "RESULTS", "REWARDS"):
        return
    if app.last_reward and app.reward_age < 2.2 and app.state in ("QUIZ", "FEEDBACK"):
        reward = app.last_reward
        if reward["base_xp"]:
            floating_label(app, f"+{reward['base_xp']} XP", (448, 144), theme.PURPLE, app.reward_age)
        if reward["streak_xp"]:
            floating_label(app, f"STREAK BONUS +{reward['streak_xp']} XP", (448, 178), theme.ORANGE,
                           app.reward_age, "tiny")
        if reward["heart_delta"]:
            delta = reward["heart_delta"]
            floating_label(app, "+1 HEART" if delta > 0 else "-1 HEART", (654, 145),
                           theme.SUCCESS if delta > 0 else theme.ERROR, app.reward_age, "small")
    if app.mastered_age < 2.4:
        floating_label(app, "MASTERED! Removed from Review Mistakes", (848, 91), theme.SUCCESS,
                       app.mastered_age, "tiny")
    if app.achievement_queue:
        achievement = app.achievement_queue[0]
        card(app, (32, 6, 270, 104))
        pygame.draw.rect(app.canvas, theme.ORANGE, (32, 6, 270, 104), 1, border_radius=20)
        label(app, "ACHIEVEMENT UNLOCKED", (46, 12), "tiny", theme.ORANGE)
        label(app, achievement["name"], (46, 34), "small")
        text_panel(app, "achievement_toast", achievement["description"] + f"  +{achievement['xp']} XP",
                   (46, 62, 242, 42), "tiny", theme.MUTED_TEXT, gap=0)


def rewards_screen(app):
    """Display the separate XP ledger, final level/rank, and all unlocked rewards."""
    progress = app.session.progression
    label(app, "QUIZ REWARDS / THIS SESSION ONLY", (76, 124), "small", theme.ORANGE)
    label(app, f"+{progress.total_xp} XP EARNED", (72, 158), "title", theme.PURPLE)
    card(app, (76, 238, 436, 366))
    label(app, "XP BREAKDOWN", (104, 262), "button")
    for index, (name, value) in enumerate((
        ("Answer XP", progress.base_xp), ("Streak bonus", progress.streak_xp),
        ("Achievements", progress.achievement_xp), ("Total XP", progress.total_xp),
    )):
        label(app, f"{name:<16} {value}", (104, 314 + index * 34), "body")
    label(app, f"LEVEL {app.stats_store.level} / {app.stats_store.rank}", (104, 466), "small", theme.ORANGE)
    label(app, f"Hearts remaining: {progress.lives} / 3", (104, 510), "body")
    label(app, f"Permanent XP: {app.stats_store.data['total_xp']}", (104, 552), "small", theme.MUTED_TEXT)
    card(app, (536, 238, 668, 366))
    label(app, f"ACHIEVEMENTS / {len(progress.unlocked_ids)}", (564, 262), "button")
    details = "\n\n".join(f"{item['name']}  " + ("Previously unlocked" if item['already_unlocked'] else f"+{item['xp']} XP")
                          + f"\n{item['description']}"
                          for item in progress.achievements) or "Keep studying to unlock your first achievement."
    text_panel(app, "reward_achievements", details, (564, 310, 612, 264), "small", theme.MUTED_TEXT)
    app.button("rewards_back", (76, 624, 544, 56), "BACK TO RESULTS", ("rewards_done", None))
    app.button("rewards_home", (644, 624, 560, 56), "MAIN MENU", ("home", None))
