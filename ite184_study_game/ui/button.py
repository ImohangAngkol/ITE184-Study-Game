"""A reusable mouse/keyboard button with rounded drawing and hover easing."""

import pygame

from . import theme
from .text import wrap_text


class Button:
    """Keep geometry, action, appearance, and keyboard shortcuts together."""

    def __init__(self, rect, text, action, *, subtitle="", enabled=True,
                 primary=False, keys=(), status=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.action = action
        self.subtitle = subtitle
        self.enabled = enabled
        self.primary = primary
        self.keys = keys
        self.status = status
        self.hover = 0.0

    def update(self, mouse, dt):
        """Ease the hover brightness; dt is seconds since the previous frame."""
        target = float(self.enabled and self.rect.collidepoint(mouse))
        self.hover += (target - self.hover) * min(1.0, dt * 14)

    def activated(self, event, mouse) -> bool:
        """Accept left-clicks and registered shortcuts only when enabled."""
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(mouse)
        return event.type == pygame.KEYDOWN and event.key in self.keys

    def draw(self, surface, fonts):
        """Draw a rounded button; fit multiline labels within its rectangle."""
        normal = theme.PURPLE if self.primary else theme.CARD
        hover = theme.PURPLE_HOVER if self.primary else theme.CARD_HOVER
        fill = tuple(int(a + (b - a) * self.hover) for a, b in zip(normal, hover))
        border = theme.BORDER
        if self.status == "correct":
            fill, border = (31, 65, 55), theme.SUCCESS
        elif self.status == "wrong":
            fill, border = (68, 33, 49), theme.ERROR
        pygame.draw.rect(surface, fill, self.rect, border_radius=14)
        pygame.draw.rect(surface, border, self.rect, width=1, border_radius=14)
        color = theme.TEXT if self.enabled or self.status else theme.MUTED_TEXT
        size = 22
        font = fonts["button"]
        available_height = self.rect.height - (34 if self.subtitle else 16)
        lines = wrap_text(self.text, font, self.rect.width - 40)
        while len(lines) * font.get_linesize() > available_height and size > 12:
            size -= 1
            font = pygame.font.SysFont("segoeui", size, bold=True)
            lines = wrap_text(self.text, font, self.rect.width - 40)
        y = self.rect.y + ((8 if self.rect.height < 70 else 14) if self.subtitle else
                          (self.rect.height - len(lines) * font.get_linesize()) // 2)
        for line in lines:
            surface.blit(font.render(line, True, color), (self.rect.x + 20, y))
            y += font.get_linesize()
        if self.subtitle:
            surface.blit(fonts["small"].render(self.subtitle, True, theme.TEXT if self.primary else theme.MUTED_TEXT),
                         (self.rect.x + 20, self.rect.bottom - 25))
