"""Display the main menu and route selections to Phase 3 MCQ gameplay."""

if __package__:
    from .quiz_engine import run_mcq_quiz
else:
    from quiz_engine import run_mcq_quiz


MENU_OPTIONS = {
    "1": "Module 1",
    "2": "Module 2",
    "3": "Module 1 + Module 2",
    "4": "Review Previous Mistakes",
    "5": "View Statistics",
    "6": "Exit",
}


def display_menu() -> None:
    """Print the title and the six study-game options."""
    print("\n=================================")
    print("ITE184 STUDY GAME")
    print("Social, Legal, and Professional")
    print("Issues in Computing")
    print("=================================")
    for number, label in MENU_OPTIONS.items():
        print(f"[{number}] {label}")
    print("Type q to exit from the main menu.")


def get_menu_choice() -> str:
    """Keep asking until the user enters an option number or q."""
    while True:
        # strip() removes outside spaces; lower() accepts Q as well as q.
        choice = input("Choose an option: ").strip().lower()
        if choice in MENU_OPTIONS or choice == "q":
            return choice
        print("Invalid choice. Enter a number from 1 to 6, or q.")


def show_placeholder(choice: str) -> None:
    """Direct desktop-only features to the full visual frontend."""
    print(f"\nYou selected: {MENU_OPTIONS[choice]}")
    if choice in ("1", "2", "3"):
        print("Choose a module from the main menu to start an MCQ quiz.")
    elif choice == "4":
        print("Review Previous Mistakes is available in the desktop game.")
    elif choice == "5":
        print("Saved statistics are available in the desktop game.")
    if choice in ("4", "5"):
        print("Run: py .\\ite184_study_game\\pygame_main.py")
    print("Returning to the main menu...")


def run() -> None:
    """Repeat the menu until the user exits or input is interrupted."""
    try:
        while True:
            display_menu()
            choice = get_menu_choice()
            if choice in ("6", "q"):
                print("Goodbye! Keep studying ITE184.")
                return
            if choice in ("1", "2", "3"):
                # None means both modules: leave the module filter unrestricted.
                module = None if choice == "3" else int(choice)
                run_mcq_quiz(module)
            else:
                show_placeholder(choice)
    except (KeyboardInterrupt, EOFError):
        # Ctrl+C or closed input should end cleanly, without a traceback.
        print("\nStudy game closed. Goodbye!")
