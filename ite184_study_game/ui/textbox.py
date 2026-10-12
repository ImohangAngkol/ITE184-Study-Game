"""Reusable multiline text entry using TEXTINPUT, with bounded caret scrolling."""

import pygame
from . import theme


class TextBox:
    """Own editable text, cursor position, focus, scroll, and a submission lock."""

    def __init__(self, rect, max_characters=1000):
        self.rect = pygame.Rect(rect)
        self.max_characters = max_characters
        self.text = ""
        self.cursor = 0
        self.focused = False
        self.locked = False
        self.scroll = 0
        self.follow_caret = True
        self.font = None

    def set_focus(self, focused):
        """Request Windows text events only while this editable box has focus."""
        focused = focused and not self.locked
        if focused != self.focused:
            self.focused = focused
            if focused:
                pygame.key.start_text_input()
            else:
                pygame.key.stop_text_input()

    def insert(self, text):
        """Insert at the caret, keeping the original text and enforcing the cap."""
        if self.locked:
            return
        text = text[:max(0, self.max_characters - len(self.text))]
        self.text = self.text[:self.cursor] + text + self.text[self.cursor:]
        self.cursor += len(text)
        self.follow_caret = True

    def layout(self, font):
        """Wrap while retaining character offsets needed to draw an accurate caret."""
        width = self.rect.width - 32
        lines = []
        start = index = 0
        while index < len(self.text):
            if self.text[index] == "\n":
                lines.append((self.text[start:index], start, index))
                index += 1
                start = index
            elif index > start and font.size(self.text[start:index + 1])[0] > width:
                space = self.text.rfind(" ", start, index)
                end = space + 1 if space >= start else index
                lines.append((self.text[start:end], start, end))
                start = end
            else:
                index += 1
        lines.append((self.text[start:], start, len(self.text)))
        return lines

    def handle_event(self, event, mouse):
        """Return 'submit' or 'handled'; None lets other controls process an event."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            inside = self.rect.collidepoint(mouse)
            self.set_focus(inside)
            return "handled" if inside else None
        if event.type == pygame.MOUSEWHEEL and self.rect.collidepoint(mouse) and self.font:
            maximum = max(0, len(self.layout(self.font)) * (self.font.get_linesize() + 3)
                          - self.rect.height + 32)
            self.scroll = max(0, min(maximum, self.scroll - event.y * 36))
            self.follow_caret = False
            return "handled"
        if self.locked or not self.focused:
            return None
        if event.type == pygame.TEXTINPUT:
            self.insert(event.text)
            return "handled"
        if event.type != pygame.KEYDOWN:
            return None
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if getattr(event, "mod", 0) & pygame.KMOD_SHIFT:
                self.insert("\n")
                return "handled"
            return "submit"
        if event.key == pygame.K_BACKSPACE and self.cursor:
            self.text = self.text[:self.cursor - 1] + self.text[self.cursor:]
            self.cursor -= 1
        elif event.key == pygame.K_DELETE:
            self.text = self.text[:self.cursor] + self.text[self.cursor + 1:]
        elif event.key == pygame.K_LEFT:
            self.cursor = max(0, self.cursor - 1)
        elif event.key == pygame.K_RIGHT:
            self.cursor = min(len(self.text), self.cursor + 1)
        elif event.key == pygame.K_HOME:
            self.cursor = 0
        elif event.key == pygame.K_END:
            self.cursor = len(self.text)
        self.follow_caret = True
        # Typing A-D/1-4 must never activate quiz/setup shortcuts.
        return "handled"

    def draw(self, surface, font, elapsed):
        """Render wrapped text and a blinking caret inside the box's clip area."""
        self.font = font
        pygame.draw.rect(surface, theme.CARD, self.rect, border_radius=14)
        pygame.draw.rect(surface, theme.PURPLE if self.focused else theme.BORDER,
                         self.rect, 2, border_radius=14)
        inner = self.rect.inflate(-32, -32)
        lines = self.layout(font)
        spacing = font.get_linesize() + 3
        row = 0
        for index, (_, start, end) in enumerate(lines):
            if start <= self.cursor:
                row = index
        caret_y = row * spacing
        maximum = max(0, len(lines) * spacing - inner.height)
        if self.follow_caret:
            if caret_y < self.scroll:
                self.scroll = caret_y
            elif caret_y + spacing > self.scroll + inner.height:
                self.scroll = caret_y + spacing - inner.height
        self.scroll = max(0, min(maximum, self.scroll))
        previous = surface.get_clip()
        surface.set_clip(inner)
        if not self.text:
            surface.blit(font.render("Type your answer here...", True, theme.MUTED_TEXT), inner.topleft)
        for index, (line, start, end) in enumerate(lines):
            surface.blit(font.render(line, True, theme.TEXT),
                         (inner.x, inner.y + index * spacing - self.scroll))
        if self.focused and not self.locked and int(elapsed * 2) % 2 == 0:
            start = lines[row][1]
            caret_x = inner.x + font.size(self.text[start:self.cursor])[0]
            y = inner.y + caret_y - self.scroll
            pygame.draw.line(surface, theme.ORANGE, (caret_x, y), (caret_x, y + spacing - 3), 2)
        surface.set_clip(previous)
