"""Shared visual constants; changing these updates every screen."""

SIZE = (1280, 720)
FPS = 60
BACKGROUND = (16, 16, 29)
CARD = (28, 28, 47)
CARD_HOVER = (42, 39, 66)
BORDER = (57, 54, 79)
PURPLE = (140, 103, 255)
PURPLE_HOVER = (160, 130, 255)
ORANGE = (255, 177, 99)
TEXT = (245, 244, 252)
MUTED_TEXT = (168, 166, 190)
SUCCESS = (107, 224, 173)
ERROR = (255, 125, 149)


def make_fonts(pygame):
    """Use installed system fonts with Pygame's built-in fallback."""
    return {
        "hero": pygame.font.SysFont("segoeui", 72, bold=True),
        "title": pygame.font.SysFont("segoeui", 38, bold=True),
        "large": pygame.font.SysFont("segoeui", 54, bold=True),
        "body": pygame.font.SysFont("segoeui", 23),
        "question": pygame.font.SysFont("segoeui", 20),
        "button": pygame.font.SysFont("segoeui", 22, bold=True),
        "small": pygame.font.SysFont("segoeui", 18),
        "tiny": pygame.font.SysFont("segoeui", 15),
    }
