"""Font-measured text wrapping, including words longer than the panel."""

import pygame


def wrap_text(text: str, font, width: int) -> list[str]:
    """Break paragraphs into lines whose rendered widths fit the panel."""
    width = max(1, width)
    lines = []
    for paragraph in text.split("\n"):
        line = ""
        for word in paragraph.split():
            # Split an unusually long word instead of letting it leave the card.
            pieces = []
            piece = ""
            for character in word:
                if piece and font.size(piece + character)[0] > width:
                    pieces.append(piece)
                    piece = ""
                piece += character
            pieces.append(piece)
            for index, piece in enumerate(pieces):
                candidate = f"{line} {piece}" if line else piece
                if line and font.size(candidate)[0] > width:
                    lines.append(line)
                    line = piece
                else:
                    line = candidate
                if index < len(pieces) - 1:
                    lines.append(line)
                    line = ""
        lines.append(line)
    return lines


def draw_wrapped(surface, text, font, color, rect, scroll: int = 0, gap: int = 4) -> int:
    """Draw visible lines and return the maximum scroll distance in pixels."""
    rect = pygame.Rect(rect)
    lines = wrap_text(text, font, rect.width)
    spacing = font.get_linesize() + gap
    maximum = max(0, len(lines) * spacing - rect.height)
    scroll = max(0, min(scroll, maximum))
    previous_clip = surface.get_clip()
    surface.set_clip(rect)
    for index, line in enumerate(lines):
        y = rect.y + index * spacing - scroll
        if y + spacing >= rect.top and y < rect.bottom:
            surface.blit(font.render(line, True, color), (rect.x, y))
    surface.set_clip(previous_clip)
    return maximum
