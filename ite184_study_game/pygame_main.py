"""Launch the desktop frontend; main.py remains the terminal entry point."""

import os


def main() -> int:
    """Check the optional dependency and close Pygame even after interruption."""
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    try:
        import pygame
    except ImportError:
        print("The visual game needs Pygame. Install it with:")
        print("  py -m pip install -r requirements.txt")
        print("Or install the desktop dependency directly: py -m pip install pygame-ce")
        print("Terminal mode still works: py .\\ite184_study_game\\main.py")
        return 1

    try:
        if __package__:
            from .ui.app import App
        else:
            from ui.app import App
        App().run()
    except KeyboardInterrupt:
        pass
    except pygame.error as error:
        print(f"Pygame could not open the game: {error}")
        return 1
    finally:
        pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
