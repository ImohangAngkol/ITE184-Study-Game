> Historical development notes for Phases 1–9. For current installation and release information, see [the public README](../README.md). Earlier phase counts and setup messages describe their development stage.

# ITE184 Study Game - Phases 1–9

A Python terminal reviewer for Social, Legal, and Professional Issues in
Computing. Phase 1 provides the basic menu; Phase 2 adds standalone question
data and inspection helpers. Phase 3 adds multiple-choice quizzes to options 1–3.
Phase 4 adds a separate Pygame desktop interface. Terminal mode uses only the
standard library; visual mode needs Pygame. Both run offline after installation.
Phase 5 adds written-scenario grading, balanced mixed quizzes, point totals,
and a review screen for answers in the current visual session.
Phase 6 adds XP, levels, ranks, lives, and achievements for each quiz.
Phase 7 now saves cumulative XP, achievements, performance, high scores,
and active mistakes in one local JSON file. Hearts and current streak reset
for each quiz; answer rewards and session summaries remain separate.
Phase 8 expands the shared bank to **261 questions** using the supplied course
notes. The current counts, content files, audits and checks are in
[Phase 8 — Full ITE184 Question Bank](#phase-8--full-ite184-question-bank).
Earlier phase sections retain their historical starter-bank counts.
Phase 9 adds a separate **Exam Mode** with editable answers, navigation,
flags, optional timers, deferred grading and permanent exam statistics.
The main visual command remains `py .\ite184_study_game\pygame_main.py`.

## Run on Windows or in VS Code

You need a working Python 3.10 or newer installation. In VS Code, open the
`ITE184_REVIEWER` folder and select **Terminal > New Terminal**.

From `<project-root>`, run:

```powershell
python .\ite184_study_game\main.py
```

If your computer uses the Windows Python launcher instead, run:

```powershell
py .\ite184_study_game\main.py
```

If both commands are unavailable, install Python 3 or select an existing
Python interpreter in VS Code before running the game.

## Files and where the code belongs

```text
ite184_study_game/
    main.py
    pygame_main.py
    generate_audio.py
    game.py
    quiz_engine.py
    scorer.py
    question_bank.py
    question_selection.py
    progression.py
    achievements.py
    stats.py
    ui/
        __init__.py
        app.py
        session.py
        screens.py
        button.py
        text.py
        theme.py
        audio.py
        textbox.py
        written_screens.py
        rewards.py
        stats_screens.py
    assets/
        music/background.wav
        sounds/click.wav
        sounds/correct.wav
        sounds/wrong.wav
        images/
    data/
        stats.json
    tests/
        test_quiz_engine.py
        test_visual_session.py
        test_pygame_ui.py
        test_scorer.py
        test_mixed_session.py
        test_written_ui.py
        test_progression.py
        test_progression_ui.py
        test_stats.py
        test_stats_ui.py
    README.md
```

These files are already created; you do not need to paste any code.
For manual recreation, put each file's complete contents into the same
relative path shown above.

| File | Purpose in this phase |
| --- | --- |
| `main.py` | Imports and starts the menu. Run this file. |
| `game.py` | Holds the menu, input validation, placeholders, and exit handling. |
| `quiz_engine.py` | Runs MCQ setup, questions, feedback, and session summaries. |
| `question_bank.py` | Holds 26 starter questions, filters, validation, and a developer preview. |
| `scorer.py` | Pure offline normalization, keyword-group matching, and 0–5 scoring. |
| `stats.py` | Versioned JSON persistence, cumulative statistics, mistake retrieval, and reset. |
| `data/stats.json` | The visual game's local save; older placeholders are automatically migrated. |

## Understand the functions

Read `game.py` from top to bottom, then `main.py`.

- `display_menu()` prints the title and options. It reads each key/value
  pair from the `MENU_OPTIONS` dictionary with a `for` loop.
- `get_menu_choice()` uses a `while True` loop to ask until input is valid.
  `input()` returns text, so the menu keys are strings such as `"1"`.
  `.strip().lower()` lets inputs such as ` Q ` work. `return` sends the
  valid choice back to the caller.
- `show_placeholder(choice)` displays the selected option and explains
  when its feature will arrive. `if` and `elif` select the message.
- `run()` repeats the menu, calls the other functions, and exits on `6`
  or `q`. `try`/`except` catches Ctrl+C (`KeyboardInterrupt`) and closed
  input (`EOFError`) so the program ends without an error traceback.

`MENU_OPTIONS` is a **dictionary**: each number maps to a menu label.
The uppercase name is a convention for a value we intend to keep fixed.
An **f-string**, such as `f"[{number}] {label}"`, inserts variable values
into text. **Type hints**, such as `choice: str`, `-> str`, and `-> None`,
describe expected inputs and returns; they do not enforce input validation.
Triple-quoted **docstrings** describe a file or function, and `#` comments
explain important decisions.

In `main.py`, `from game import run` reuses a function from another file.
The `if __name__ == "__main__":` guard starts the program when `main.py`
is run directly. Importing it from another Python file will not start a menu.
There are no classes yet: functions are enough for this small first phase.

## Try the menu

1. Run the command above. All six menu options should appear.
2. Enter `hello`, `0`, `7`, or a blank line. You should see an invalid-choice
   message and another prompt.
3. Enter `1`, `2`, or `3`. Each now opens MCQ setup. Enter `q` there to
   return to the menu, or select a difficulty and question count to play.
4. Enter `4` and `5`. Each should show its future-phase message.
5. Enter `6` to exit. Run again and try `q`, uppercase `Q`, or Ctrl+C.

At the main menu, `q` exits. At quiz setup, `q` returns to the menu.
During questions or feedback, `q` asks for confirmation before returning.
Written answers, mixed mode, XP, saving, and mistakes arrive in later phases.

## Next stages

1. Project files and basic menu (complete).
2. Question data structures (complete).
3. Multiple-choice engine (complete).
4. Pygame interface and visual MCQs (complete; revised Phase 4 scope).
5. Written/scenario input, keyword scoring, and mixed mode (complete).
6. Session XP, levels, ranks, lives, and achievements (complete).
7. Persistent progress, statistics, high scores, and Review Mistakes (complete).
8. Full ITE184 question-bank expansion (next; revised phase scope).

## Phase 2 — Question Data Structures

All Phase 2 Python additions belong in `ite184_study_game/question_bank.py`.
They are already saved; no pasting is needed. Read the data first, then the
helper functions below it. Phase 2 preserved the other Python files and
`data/stats.json`; Phase 3 now routes options 1–3 from `game.py` into the
separate MCQ engine. Written scoring and persistence arrive in later phases.

### Understand the stored data

A **list** stores several items in order. `QUESTION_BANK` is a list of 26
questions. A **dictionary** stores named fields for one question, such as
`"module": 1` and `"difficulty": "easy"`. Read a field with
`question["module"]`. Each question has a topic and a more specific subtopic.

A **question ID**, such as `M2_WR_001`, uniquely identifies one question.
Keep IDs stable when correcting wording so future statistics and mistake
reviews can find the same question. Do not reuse an ID for a different question.

MCQs store four choice strings and the answer's full text, rather than a
letter. Later, choices can be shuffled without making the stored answer wrong.
They also store `question`, `keywords`, and `explanation`.

Written questions store `scenario`, `keyword_groups`, `optional_keywords`,
`model_answer`, and `explanation`. A **nested list** is a list containing
other lists. For example:

```python
keyword_groups = [
    ["ra 10175", "cybercrime prevention act"],
    ["illegal access", "access without right", "unauthorized access"],
]
```

Each inner list holds alternative phrases for one required concept. A future
scorer can accept any phrase in the first group for the law and any phrase
in the second for the offense. Different groups represent different concepts;
optional keywords provide extra detail. Phase 2 stores this information only.

The bank covers a sample of the course, including ethical theories, all three
legal maxims, authorization, RA 10175 offense distinctions, relevant IT laws,
malware, consent, corporate espionage, and overlapping privacy issues. It is
not the full course bank.

| Module | MCQ | Written | Total |
| --- | ---: | ---: | ---: |
| 1 | 6 | 4 | 10 |
| 2 | 10 | 6 | 16 |
| Total | 16 | 10 | 26 |

Difficulty totals: **9 easy, 10 medium, 7 hard**. Both question types and both
modules include every difficulty.

### Understand the helper functions

| Function | Purpose |
| --- | --- |
| `get_all_questions()` | Returns all questions as independent copies. |
| `get_questions_by_module(module)` | Selects Module 1 or Module 2. |
| `get_questions_by_type(question_type)` | Selects `"mcq"` or `"written"`. |
| `get_questions_by_difficulty(difficulty)` | Selects `"easy"`, `"medium"`, or `"hard"`. |
| `filter_questions(...)` | Combines module, type, difficulty, and topic filters. |
| `get_question_by_id(question_id)` | Returns one question or `None` if not found. |
| `validate_question_bank()` | Returns a validity flag and all detected data errors. |
| `get_question_bank_summary()` | Counts a valid bank by module, type, difficulty, and topic. |

**Filtering** means selecting only items that meet your conditions. All
provided conditions must match. Text filters match exactly, including case:
use `"written"`, not `"Written"`, and `"Cybercrime"`, not `"cybercrime"`.
An unknown filter value returns an empty list. A single module filter must
be the integer `1` or `2`; omitting it includes both modules.

```python
from ite184_study_game.question_bank import filter_questions, get_question_by_id

questions = filter_questions(module=2, question_type="written", difficulty="hard")
print(len(questions))  # 4
print(get_question_by_id("M2_WR_001")["subtopic"])  # Illegal Access
print(get_question_by_id("NOT_FOUND"))  # None
```

Run this example from the workspace root. If your terminal is inside
`ite184_study_game`, import from `question_bank` instead.

**None** represents the absence of a value. An **optional parameter** has a
default value, so you can leave it out of a function call. In
`filter_questions`, `module=None` means no restriction on modules; it does
not mean questions must have a missing module. Calling `filter_questions()`
with no arguments returns all questions.

A **list comprehension** builds a list using a loop and a condition. The
comprehension in `filter_questions()` keeps questions satisfying all active
filters. For example, this smaller version selects Module 1:

```python
module_1 = [question for question in QUESTION_BANK if question["module"] == 1]
```

`deepcopy()` from the standard library also copies nested lists. The public
retrieval functions use it so changing returned choices or keyword groups
does not change `QUESTION_BANK`. Edit `QUESTION_BANK` itself when you intend
to change the stored content.

### Understand validation

**Validation** checks whether data follows the agreed structure. It does not
decide whether a student's answer is correct or verify the factual truth of
a question. Use it after adding or editing questions, before filtering or
summarizing the bank.

```python
valid, errors = validate_question_bank()
# A valid bank returns (True, []).
# A malformed bank returns (False, ["error message", ...]).
```

The validator checks dictionary entries, unique nonblank IDs, integer modules,
supported types/difficulties, and nonblank topic, subtopic, and explanation.
MCQs need nonblank prompts, exactly four nonblank unique choices, an answer
matching a choice exactly, and a keywords list. Choice uniqueness ignores
case and outside spaces to reject visually duplicate options.

Written questions need nonblank scenarios and model answers, at least one
keyword group, nonempty lists of nonblank strings in every group, and an
optional-keywords list. `keywords` and `optional_keywords` may be empty lists
but must still be present. Mixed strings and nonstrings are rejected.

The private helpers `_is_nonempty_text()` and `_is_text_list()` reuse small
checks. A leading underscore means a helper is intended for internal use.
`isinstance()` checks a value's type before string/list operations;
`dictionary.get()` safely reads fields that might be absent. A **set** tracks
IDs already seen so duplicates can be reported. The validator accumulates
errors instead of stopping at the first malformed question.

The developer preview calls validation first. If data is invalid, it prints
the errors and exits with status 1 rather than running summary/filter helpers
on malformed data. `_run_developer_preview()` prints the successful summary
and filter examples; the `__main__` guard keeps that output from running on import.

Data and game logic live separately so you can add course questions without
changing how the menu or quiz works. The same IDs and metadata can later
support mistakes, statistics, and topic recommendations. `Question` is a
type alias for dictionaries; `Any` allows their values to have different types.
These hints describe the structure; the validator enforces it.

### Run and verify Phase 2

From `<project-root>`, run:

```powershell
py .\ite184_study_game\question_bank.py
```

Expect `Question bank validation PASSED`, followed by the summary:
26 total, 10 Module 1, 16 Module 2, 16 MCQ, 10 written, 9 easy, 10 medium,
and 7 hard. Topic counts also print. The filter demonstrations show 10
Module 1 questions, 6 Module 2 written questions, and 7 hard questions.

Check that importing produces no developer-preview output:

```powershell
py -c "from ite184_study_game.question_bank import QUESTION_BANK, filter_questions; print(len(QUESTION_BANK))"
```

This should print only `26`. Check a combined filter:

```powershell
py -c "from ite184_study_game.question_bank import filter_questions; print(len(filter_questions(module=2, question_type='written', difficulty='hard')))"
```

This should print `4`. Finally, run the original menu and try options 1–5,
invalid input, and 6 or q:

```powershell
py .\ite184_study_game\main.py
```

### Legal references used for the starter data

The questions are written for study scenarios. References are documentation;
the game never downloads them and runs offline.

- [RA 10175](https://elibrary.judiciary.gov.ph/thebookshelf/showdocs/2/50264)
  supplies the access, interception, data/system interference, and misuse-of-devices distinctions.
- [RA 9995](https://lawphil.net/statutes/repacts/ra2010/ra_9995_2010.html)
  distinguishes recording consent from consent to sharing or publication.
- [RA 11313](https://lawphil.net/statutes/repacts/ra2019/ra_11313_2019.html)
  addresses gender-based online sexual harassment.
- [RA 11930](https://elibrary.judiciary.gov.ph/thebookshelf/showdocs/2/95572)
  addresses OSAEC/CSAEM and repeals RA 9775.
- [RA 8792](https://lawphil.net/statutes/repacts/ra2000/ra_8792_2000.html)
  concerns electronic commerce and includes an early hacking/cracking provision.
- [RA 8484](https://lawphil.net/statutes/repacts/ra1998/ra_8484_1998.html)
  concerns access devices and access-device fraud.
- [RA 11449](https://lawphil.net/statutes/repacts/ra2019/ra_11449_2019.html)
  includes the 50-or-more-card skimming circumstance for economic sabotage.
  Below that threshold does not mean skimming is lawful; bank-system hacking
  is a separate economic-sabotage circumstance.
- [RA 10173](https://officialgazette.gov.ph/2012/08/15/republic-act-no-10173/)
  addresses personal-information processing and disclosure.

## Phase 3 — Multiple-Choice Quiz Engine

The new file is `ite184_study_game/quiz_engine.py`. The small edit to
`game.py` routes menu choices 1–3 to `run_mcq_quiz()`. `main.py` still starts
the menu, and `question_bank.py` still owns all course questions. No code
needs to be pasted: the files are already saved.

### Play a quiz

From `<project-root>`, run:

```powershell
py .\ite184_study_game\main.py
```

Choose Module 1, Module 2, or both. Then choose Easy, Medium, Hard, or All
Difficulties, followed by 5, 10, 20, or All Available. These are numbered
menus: enter `1` to request five questions, for example.

The playable starter pool is **16 MCQs**: 6 from Module 1 and 10 from Module 2.
Written questions stay in the bank for later phases. A difficulty filter can
make the available MCQ pool smaller:

| Module | Easy | Medium | Hard | All |
| --- | ---: | ---: | ---: | ---: |
| 1 | 3 | 2 | 1 | 6 |
| 2 | 4 | 5 | 1 | 10 |
| Both | 7 | 7 | 2 | 16 |

When you request more than are available, the game tells you how many match
and uses all of them. It never repeats a question in the same quiz.

Answer with `A`, `B`, `C`, or `D`; lowercase and surrounding spaces work too.
After each answer, read the explanation and keywords, then press Enter.
Invalid inputs prompt again without changing your score.

At either setup prompt, `q` returns directly to the menu. During a question
or the feedback pause, `q` asks `Return to main menu? (y/n):`. Enter `y` to
leave or `n` to resume the current question/pause. `q` at that confirmation
also returns to the menu. Ctrl+C or closed input exits the whole application
cleanly through the existing exception handling in `game.run()`.

Completed quizzes print a final summary. Quitting during gameplay prints a
partial summary: only answered questions count toward the score, percentage,
and breakdowns. Quitting before answering any question displays 0.0% and
`No answers yet`. All counters reset when you start another quiz.

### Understand every new function

| Function | Responsibility |
| --- | --- |
| `select_difficulty()` | Validates the numbered difficulty menu; returns a name, `"all"`, or `None` for Back. |
| `select_question_count()` | Validates the count menu; returns 5, 10, 20, `"all"`, or `None` for Back. |
| `prepare_mcq_questions()` | Filters MCQ copies, shuffles their order, and slices the requested amount. |
| `shuffle_choices()` | Copies choices, shuffles them, and maps letters to answer text. |
| `confirm_return_to_menu()` | Validates the quit confirmation and returns a boolean. |
| `ask_mcq_question()` | Displays metadata and choices; returns `True` for correct, `False` for wrong, or `None` for quit. |
| `create_quiz_results()` | Creates fresh session counters and empty breakdown dictionaries. |
| `record_answer()` | Updates answered/correct/incorrect counters, streaks, and topic/module totals. |
| `display_answer_feedback()` | Prints the correct shuffled letter, explanation, keywords, and live counters. |
| `wait_to_continue()` | Waits for Enter, or handles a confirmed quit during the feedback pause. |
| `calculate_percentage()` | Returns correct divided by answered times 100, with safe handling of zero answers. |
| `get_performance_label()` | Converts a percentage to the temporary Phase 3 performance description. |
| `display_results()` | Prints a complete or partial session summary and breakdowns. |
| `run_mcq_quiz()` | Connects setup, question selection, answering, feedback, and results. |

`run_mcq_quiz()` returns its results dictionary so tests can inspect it. It
returns `None` when setup is cancelled, no questions match, or bank validation
fails. Nothing is saved to JSON. Options 4 and 5 remain their original placeholders.

### Python concepts in this phase

`random.shuffle(a_list)` changes that list's order **in place** and returns
`None`; do not write `a_list = random.shuffle(a_list)`. Question retrieval
already gives us deep copies. For choices, `.copy()` creates another list
before shuffling, protecting even the retrieved question's choice order.
The strings themselves are immutable, so a shallow choice-list copy is enough.

`random.sample(a_list, k)` is another standard-library way to select `k`
items without repetition, but `k` cannot exceed the pool size. This engine
uses `shuffle()` followed by a **slice**, `questions[:question_count]`.
Slicing safely returns all available items if the requested number is too large.
Both methods can avoid repetition when the source has unique questions.

`zip("ABCD", choices)` pairs each letter with a choice; `dict(...)` turns
those pairs into a lookup table. We compare the chosen **text** with the
stored answer text, so changing its letter does not break correctness.
`enumerate(questions, start=1)` gives each question its display number.

A **counter** is a number we update, often with `+= 1`. An incorrect answer
resets `current_streak` to zero; a correct answer increases it. `max()` keeps
the largest streak in `best_streak`. Every MCQ earns either 1 point or 0 points.

Breakdowns use nested dictionaries, for example:

```python
topics = {"Cybercrime": {"correct": 3, "answered": 4}}
```

`record_answer()` creates a topic or module entry the first time it is needed.
Only topics with answered questions print. For both-module quizzes, the
summary also shows each represented module's correct/answered counts.

The percentage formula is `correct / answered * 100`. A zero denominator
needs a special case to avoid division by zero. `{percentage:.1f}` displays
one decimal place. Performance uses the actual percentage: 90+ Excellent,
80+ Very Good, 70+ Good, 60+ Needs Review, and below 60 Needs More Study.

An **early return** leaves a function immediately. Here, returning `None`
from setup or an answer prompt lets the caller stop or return to the menu.
The test `is_correct is None` matters: an incorrect answer is `False`, which
must still be counted rather than mistaken for quitting. `break` ends the
question loop so the partial summary can print.

Input/output functions handle terminal interaction; calculation and counter
functions can be checked independently. The engine imports data helpers;
it does not duplicate question content. Conditional imports support both
normal `main.py` execution and package imports used by the tests. Importing
`quiz_engine.py` never starts gameplay.

### Verify Phase 3

Try these flows from the main menu:

1. Module 1 → Easy → 5: expect the availability message and 3 questions.
2. Module 2 → All Difficulties → 10: expect 10 questions.
3. Both → All Difficulties → All Available: expect 16 unique questions.
4. Module 1 → All Difficulties → 20: expect the availability message and 6 questions.
5. Try blank/invalid setup inputs, `hello` or `AA` as an answer, lowercase
   answers, and quit confirmations with both `n` and `y`.

Recheck the unchanged bank:

```powershell
py .\ite184_study_game\question_bank.py
```

Confirm importing the engine does not start a quiz:

```powershell
py -c "import ite184_study_game.quiz_engine; print('Import OK')"
```

Run the standard-library automated tests from the workspace root:

```powershell
py -m unittest discover -s .\ite184_study_game\tests -v
```

`tests/test_quiz_engine.py` uses controlled inputs and randomization so checks
are repeatable. The tests cover all three module selections, small pools,
invalid inputs, quit/resume behavior, copied data, shuffled answer correctness,
score/streak calculations, breakdowns, imports, and menu return/exit behavior.
These checks use no third-party packages.

## Phase 4 — Pygame Interface

The desktop game is a second frontend for the same question bank and pure
quiz helpers. The terminal version remains available with its original
commands. The latest Phase 4 scope is **Pygame + MCQs**; written answers,
keyword grading, and model answers are deferred to Phase 5. The old Phase 4
placeholder in `scorer.py` has no active functionality.

### Launch the game

From `<project-root>`:

```powershell
py .\ite184_study_game\pygame_main.py
```

If Pygame is unavailable, the launcher displays a short message with:

```powershell
py -m pip install pygame
```

No other libraries or external fonts are needed. Audio files are bundled and
were generated locally as original synthesized tones. The game does not
download music, question content, or any other assets.

The window is titled **ITE184 Reviewer**, starts at 1280 x 720, and targets
60 FPS. Resizing scales the interface proportionally and uses letterbox
margins when the window has a different aspect ratio. The mouse position is
converted back to the original canvas coordinates so buttons stay clickable.

### Screens and controls

The screens follow this flow: Home → Module → Difficulty → Count → Question
→ Feedback → next Question or Results. Play Again starts a freshly shuffled
quiz with the same settings. Change Settings returns to module selection;
Main Menu returns home. Settings is an overlay accessible throughout the game.

- Click an answer or press `A`–`D` / `1`–`4`. Setup cards also support
  numbered shortcuts. Enter on Home starts setup.
- After answering, read the feedback. Click Next Question or press Enter or
  Space. On the last question, the same control opens results.
- Escape goes back during setup, closes settings/confirmation overlays, or
  opens quit confirmation during a quiz.
- Home / Quit Quiz opens a confirmation. Yes discards the session; Cancel
  preserves the question, choices, counters, and answer lock. `Y` and `N`
  work in the confirmation.
- Scroll the mouse wheel over a question or feedback panel when its
  `Scroll here to read more` hint appears. Long text remains accessible
  inside its panel rather than leaving the card or covering controls.
- Music ON/OFF is available at the top of study screens. Settings controls
  background music and sound effects independently. Settings last for this
  application launch only.
- The window's X and the Home Quit button close cleanly.

Review Mistakes and Statistics are disabled with Coming Soon labels. They
do not create or load permanent progress.

### Where each piece belongs

All files have already been saved; no pasting is needed. New Python code is
split into small files so you can read one responsibility at a time.

| File | What to learn from it |
| --- | --- |
| `pygame_main.py` | Optional dependency detection, imports, cleanup with `finally`, and the main guard. |
| `ui/session.py` | A Pygame-free `QuizSession` class stores copied questions, answer history, and session results. |
| `ui/app.py` | The `App` class owns the window and one event loop, translates actions into state changes, and scales mouse coordinates. |
| `ui/screens.py` | Small functions draw Home, selection screens, quiz/feedback, results, and modal overlays. |
| `ui/button.py` | A reusable `Button` class keeps bounds, text, shortcuts, enabled state, hover animation, and drawing together. |
| `ui/text.py` | Font-measured wrapping and bounded scrolling handle long text and long individual words. |
| `ui/theme.py` | Shared colors, dimensions, FPS, and default/system font sizes. |
| `ui/audio.py` | `AudioManager` handles loading, looping music, cues, toggles, and absent audio devices/files. |
| `generate_audio.py` | Standard-library WAV generation using sine waves, fades, and PCM samples. |
| `tests/test_visual_session.py` | Model tests that work without Pygame. |
| `tests/test_pygame_ui.py` | Pygame event/render tests with dummy display and audio devices; skipped if Pygame is absent. |

`QuizSession.submit()` rejects invalid choices and repeated submissions,
then calls the existing `record_answer()` helper. `advance()` requires an
answered question, clears its lock, and shuffles choices for the next one.
Properties `current_question` and `is_last_question` provide convenient
read-only views derived from the current index.

`App.dispatch()` handles named actions such as `("module", 2)` and
`("answer", "B")`. `handle_event()` interprets device events; `render()`
draws the active screen; `present()` scales it into the window. `go_back()`
defines Escape behavior, `start_quiz()` builds a session, and
`matching_count()` reports available questions before starting.

### Pygame and Python concepts

[Pygame](https://www.pygame.org/docs/) provides graphics, input, and audio
for Python games. A **game loop** repeatedly reads events, updates state,
and draws a frame. `pygame.time.Clock().tick(60)` limits the loop to about
60 frames per second. **FPS** measures how often the image is redrawn;
the quiz itself has no time limit. Dividing milliseconds by 1000 gives the
seconds used for gentle hover and background animations.

An **event** describes something that happened, such as a click, key press,
resize, or close request. `pygame.event.get()` drains the event queue every
frame so the window stays responsive. Mouse events supply a position;
keyboard events supply a key constant. The GUI never calls `input()`.
See the [Pygame event reference](https://www.pygame.org/docs/ref/event.html).

A **Surface** is an image you can draw onto. We draw into a 1280x720 canvas
Surface, then scale and copy it into the display Surface. `blit()` copies
pixels between surfaces; `pygame.display.flip()` presents the frame. A
**Rect** describes a rectangle's position and size. `collidepoint()` tests
whether the mouse is inside a button. Drawing functions create rounded
cards, outlines, the progress bar, and small animated background dots.

An **application state** says which screen is active, such as `QUIZ` or
`RESULTS`. Changing state replaces the drawing and active controls without
starting another while loop. An overlay draws over the current screen and
owns all input until dismissed. It does not accidentally allow clicks or
answer shortcuts through to the covered screen.

A **class** groups related data and behavior. `App`, `Button`, `QuizSession`,
and `AudioManager` each own a different responsibility. `self` refers to
the current instance. For example, each Button's `self.rect` describes only
that button. Buttons are reused between frames so their hover transitions
do not reset. Disabled answer buttons also display text markers for correct
and selected wrong answers, rather than relying only on color.

`wrap_text()` measures text with `font.size()` before placing it on a line.
It also splits a single word if that word is wider than the panel. Wrapped
lines are drawn within a temporary clipping rectangle; scrolling moves the
text, and the original clipping rectangle is restored afterward. Answer
labels can reduce their font size when needed to fit their buttons.

Backend logic is kept separate from graphics: `ui/session.py` imports the
existing pure helpers for filtering, shuffling, counters, and streaks. It
does not import Pygame. The same score formula and performance labels drive
both frontends, and the model can be tested without opening a window.

### Gameplay and results

The bank still contains 26 starter questions, including **16 playable MCQs**.
Module 1 has 6 MCQs, Module 2 has 10, and Both includes all 16. Difficulty
selection filters those pools; excessive question-count requests use all
matching questions and show the actual available/playable count on setup.

Question order is shuffled after retrieving deep copies; choice order is
shuffled on a separate list copy. Correctness compares answer text, so the
correct letter can change safely. The original bank is not modified.

After submission, the correct choice gets a success outline and `[CORRECT]`
marker. A selected wrong choice gets an error outline and `[YOUR ANSWER]`
marker. Feedback shows CORRECT/INCORRECT, the correct answer, the stored
explanation, and important keywords. Further answer submissions are locked.

Each MCQ earns 1 or 0 points. Score, correct/incorrect counts, current/best
streaks, and answer history exist only for the current session. Results show
percentage, performance, score, incorrect count, best streak, module,
difficulty, topic totals, and both-module totals when appropriate. No XP,
ranks, history, or high scores are saved.

### Original audio

The bundled files are `assets/music/background.wav` and
`assets/sounds/click.wav`, `correct.wav`, and `wrong.wav`. The music is a
short original repeating melody. The cues use different pitches for clicks,
correct answers, and incorrect answers.

[pygame.mixer](https://www.pygame.org/docs/ref/mixer.html) loads the audio.
`music.play(-1)` repeats the background track. Sound effects use separate
Sound objects. Music can pause/resume independently of sound effects.
Missing or corrupt files and unavailable audio devices are caught so the
game continues silently instead of crashing.

To regenerate absent files:

```powershell
py .\ite184_study_game\generate_audio.py
```

The utility uses only `wave`, `math`, `struct`, and `pathlib`. Frequencies
become sine-wave samples, fade envelopes soften note edges, and WAV files
store the samples as mono 16-bit audio. Existing files are preserved, so
custom replacements are not overwritten. You can replace the four WAVs
with your own files at the same paths; the game loads them on its next launch.

### Verification commands

```powershell
# Visual game
py .\ite184_study_game\pygame_main.py

# Original terminal version
py .\ite184_study_game\main.py

# All automated tests
py -m unittest discover -s .\ite184_study_game\tests -v

# Original question-bank validation
py .\ite184_study_game\question_bank.py
```

All **44 tests passed** during Phase 4 verification: the original 27 plus
7 Pygame-free session/launcher tests and 10 Pygame UI/audio tests. UI tests
use dummy drivers, synthesize clicks/keys, and exercise real drawing/event
functions. They cover module selection, locking, feedback, navigation,
replay, results, resize mapping, wrapping, audio fallback, and toggles.
They also verify that the bank is unchanged after each test.

Rendered Home, selection, quiz, feedback, settings, and result screens were
visually inspected. The Windows display launch/close and terminal regression
checks are separate from dummy-driver tests. Audio loading and controls were
verified programmatically; listening quality depends on your speakers and
preferences. Adjust either toggle in Settings while you study.

The Phase 4 scope above describes the visual MCQ foundation. Phase 5 now
adds written and mixed gameplay as documented below; permanent progress
features remain deferred.

## Phase 5 — Written Scenario Grading

Run the same desktop command from the workspace root:

```powershell
py .\ite184_study_game\pygame_main.py
```

The setup flow is now **Home → Module → Game Mode → Difficulty → Count → Quiz**.
Choose Multiple Choice, Written Scenarios, or Mixed Mode. Existing audio,
scaling, keyboard MCQ shortcuts, and quit confirmations remain available.
Terminal mode still runs its original MCQ flow.

| Module | MCQs | Written | Mixed / All Available |
| --- | ---: | ---: | ---: |
| 1 | 6 | 4 | 10 |
| 2 | 10 | 6 | 16 |
| Both | 16 | 10 | 26 |

Difficulty further reduces these pools. The current bank has one Module 1
Hard written scenario, so asking for 20 uses that one question. Setup shows
the actual available count and the number each count option will play.
The original 26 questions have not been edited or expanded.

### Type and submit an answer

Click the answer box to focus it; a new written question also focuses it
automatically. Type the law, offense, theory, and relevant reasoning in your
own words. Numbers, spaces, punctuation, and Unicode text are accepted.

- Enter submits; Shift+Enter adds a newline without submitting.
- Backspace deletes before the caret; Delete deletes after it.
- Left/Right move the caret. Home/End move to the beginning/end of the answer.
- The maximum is 1000 characters. Wrapped text and the caret stay within
  the answer box. Mouse-wheel scrolling over the box lets you reread long answers.
- Blank or whitespace-only answers show `Type an answer before submitting.`
- Submitting locks the textbox and records the original answer unchanged.
  After grading, Enter moves to the next question or results.
- Mouse-wheel scrolling over scenario and feedback panels reveals long
  text while the textbox and navigation controls remain visible.
- Escape opens the usual quit confirmation; cancelling retains your answer.
  Audio settings overlays also block text from leaking into the answer.

### Learn the scorer functions

The new scoring code belongs in `scorer.py`. These are **pure functions**:
they return results from their arguments without changing question data,
opening a window, requesting keyboard input, or using the internet.

| Function | Purpose |
| --- | --- |
| `normalize_answer(text)` | Lowercases and standardizes whitespace/punctuation while preserving numbers. |
| `match_keyword_group(answer, group)` | Returns whether any one synonym identifies that concept. |
| `calculate_written_score(...)` | Applies the consistent coverage/detail rules below. |
| `analyze_written_answer(question, user_answer)` | Returns points, labels, detected/missed concepts, optional matches, normalized text, and percentage. |

**Normalization** makes harmless formatting differences comparable. For example,
`RA 10175 - Illegal Access!!` becomes `ra 10175 illegal access`. Commas,
periods, and hyphens act as separators; extra spaces collapse. `RA10175`
and `R.A. 10175` also match the conventional law-number spelling. Numbers
such as 9995, 10175, 11449, and 50 remain meaningful tokens.

Exact whole-sentence matching would reject many useful answers because wording
and punctuation vary. Instead, **keyword groups** represent required concepts.
Every synonym inside a group is an alternative way to identify the same
concept, so matching two synonyms never counts as two required concepts.

The matcher surrounds normalized phrases with spaces before searching. This
enforces **token boundaries**: `law` matches a word `law`, while `lawful`
does not satisfy it. Multiword phrases still match. A small `PHRASE_ALIASES`
dictionary accepts equivalent consent wording and existing model-answer
variations without modifying the stored question bank.

Grading uses the normalized copy; the displayed answer retains the player's
original spelling, punctuation, spacing, and line breaks. Matching is
deterministic. It recognizes the configured phrases and aliases; it does
not interpret negation, contradictions, or the overall quality of an essay.
Use the model and explanation to check your reasoning after each answer.

### Partial-credit algorithm

Every written scenario is worth 5 points. Let the coverage ratio be the
number of matched required groups divided by the number of required groups.

| Points | Rule | Feedback label |
| --- | --- | --- |
| 5 | All required groups plus at least one optional/detail keyword; also all required groups when no optional keywords are defined. | EXCELLENT |
| 4 | All required groups, with optional detail defined but none detected. | GREAT |
| 3 | At least half of required groups, with some still missing. | PARTIALLY CORRECT |
| 2 | Some required groups, but less than half. | NEEDS MORE DETAIL |
| 1 | Optional keywords only; no required groups detected. | RELATED IDEA |
| 0 | No meaningful configured match. | INCORRECT |

The algorithm handles one, two, three, or more groups consistently. Optional
matches do not replace missing required concepts. For the two-group Illegal
Access question, identifying just the law earns 3; adding the offense earns
4; adding `without permission` earns 5. Naming only a Latin maxim earns
partial credit when its question also requests the meaning.

```python
from ite184_study_game.question_bank import get_question_by_id
from ite184_study_game.scorer import analyze_written_answer

question = get_question_by_id("M2_WR_001")
grade = analyze_written_answer(question, "RA 10175 illegal access without permission")
print(grade["score"])  # 5
print(grade["label"])  # EXCELLENT
```

Each detected/missed group carries one representative label, and a detected
group records the matching phrase. The UI does not list every synonymous
phrase as a separate missed concept. Feedback includes detected concepts,
missed concepts or `All required concepts identified.`, detail suggestions
for 4/5 answers, the model answer, and the explanation. Scroll the feedback
panel to read all its sections.

### Mixed questions and points

`question_selection.py` filters copied questions by module, mode, and
difficulty. For a limited mixed quiz, it aims for half MCQs and half written
questions. Odd counts differ by at most one when both pools are sufficient;
the extra type is chosen randomly. A shortage in one pool is filled from
the other. The final selection is shuffled so question types are interleaved
randomly, with no repeated IDs. All Available includes the entire matching
pool, even when its two type counts differ.

MCQ choice order is still shuffled independently. Written keyword groups
remain in their original order. Every selection uses copied data, so the
original question bank is preserved.

**Earned points** are the points awarded. **Possible points** are the maximum
available, with 1 per MCQ and 5 per scenario. Five of each gives a 30-point
quiz. An earned 23/30 displays **76.7%**. All 26 starter questions together
are worth 66 points: 16 MCQ points plus 50 written points.

Visual results now show point-based totals overall, by question type, by
topic, and by module. They also show questions answered and best streak.
The existing final percentage labels remain unchanged. A written score of
4–5 increases the streak and plays the correct cue; 0–3 resets it. Scores
0–2 play the wrong cue, and 3 uses no grading cue.

`QuizSession` retains the existing successful-answer counters for compatibility
and stores point totals separately. Each answer record contains ID, type,
module, topic, subtopic, earned/possible points, original answer, and written
grading details. These records exist only in the current session.

The Results **Review Answers** button opens the recorded questions and your
answers beside the correct/model answers, points, and explanations. Previous
and Next browse that session; Escape or Back to Results returns to the summary.
Review does not regrade or permanently save anything.

### Files and reusable components

All changes are already saved; no pasting is needed.

- Created `question_selection.py`, `ui/textbox.py`, `ui/written_screens.py`,
  and three test files: `test_scorer.py`, `test_mixed_session.py`, `test_written_ui.py`.
- Updated `scorer.py`, `ui/session.py`, `ui/app.py`, `ui/screens.py`, this README,
  and the existing GUI test's setup navigation to include the new mode screen.
- The terminal engine, terminal menu, main entry point, original question bank,
  audio assets, and JSON statistics file retain their earlier contents.

`TextBox` is a reusable class that owns text, cursor position, focus, scroll,
and lock state. [Pygame TEXTINPUT](https://www.pygame.org/docs/ref/key.html)
supplies typed text, including Windows keyboard translation. KEYDOWN handles
editing and Enter. Focused typing consumes letter/number events so they cannot
trigger MCQ shortcuts. Focus starts/stops text-input events, and the renderer
uses original character offsets to wrap lines and position a blinking caret.

`ui/written_screens.py` draws scenario, feedback, and review layouts using
the existing cards, buttons, and scrollable text panels. The application
still uses one main loop. Scoring stays outside the UI, which makes it
possible to test every grade without Pygame installed.

### Verify Phase 5

```powershell
py .\ite184_study_game\pygame_main.py
py -m unittest discover -s .\ite184_study_game\tests -v
py .\ite184_study_game\question_bank.py
py .\ite184_study_game\main.py
```

All **84 tests pass**: the previous 44 checks plus 19 scorer tests, 9 mixed
session/selection tests, and 12 written GUI tests. Two earlier GUI navigation
paths now choose Multiple Choice on the new mode screen; their regression
assertions remain intact.

Try Module 2 → Written → Easy → All Available. Enter `RA 10175 illegal access`
for 4/5, then replay with `RA 10175 illegal access without permission` for
5/5. Try a blank answer, Shift+Enter, Backspace, long text, feedback scrolling,
cancelled quitting, and resizing. Then select Both → Mixed → All → 10 and
complete a 30-point quiz, including both type transitions and answer review.

The bank still validates. The terminal MCQ mode remains available. Permanent
statistics, saved mistakes, XP, levels, ranks, and achievements are deferred.
Phase 6 is implemented below. Permanent progression remains reserved for Phase 7.

## Phase 6 — Game Progression

The visual quiz now awards XP and achievements, displays levels/ranks, and
starts with three motivational hearts. **A session means one quiz.** Play
Again and a newly started quiz reset XP, lives, unlocks, and bonus thresholds.
Returning from Review Answers or XP & Rewards preserves the same session.
Confirmed quitting discards it. Nothing is saved to `data/stats.json`.

### Play and view rewards

```powershell
py .\ite184_study_game\pygame_main.py
```

The shared top HUD shows score, total XP, level, rank, streak, three drawn
hearts, and a lives count. It appears during MCQ, written, and mixed gameplay,
including feedback. The XP bar shows progress toward the next level.

Answer XP floats briefly beside the question number. Streak bonuses have a
separate line. Heart changes briefly highlight the lives area. Achievement
notifications appear in a small passive card and expire after 2.4 seconds
each; they never pause gameplay or capture typing/button events.

Results show XP earned, final level/rank, remaining hearts, and achievement
count alongside the existing point-based summary. **XP & Rewards** opens a
detailed breakdown of answer, streak, achievement, and total XP, plus a
scrollable list of achievement names and descriptions. Back to Results,
Review Answers, Play Again, Change Settings, and Main Menu still work.

### XP rules

XP is a separate reward from quiz points. It never changes written grades,
point percentages, topic totals, or the final performance labels.

| Answer | Base XP |
| --- | ---: |
| Correct MCQ | 10 |
| Incorrect MCQ | 0 |
| Written 5/5 | 25 |
| Written 4/5 | 20 |
| Written 3/5 | 12 |
| Written 2/5 | 6 |
| Written 1/5 | 2 |
| Written 0/5 | 0 |

A successful answer is a correct MCQ or a written score of 4–5. Successful
streaks pay **+10 XP at 3**, **+20 at 5**, and **+50 at 10**. Each threshold
pays only once per quiz, including after a streak resets and reaches it again.
A failed answer still resets the existing current-streak counter.

Total XP is calculated from three separate counters:

```python
total_xp = base_xp + streak_xp + achievement_xp
```

Keeping these counters separate makes the reward ledger easy to explain and
test. A repeated submission does not add points, XP, or another popup.

### Levels and ranks

```python
level = total_xp // 100 + 1
level_progress = total_xp % 100
```

**Integer division** (`//`) gives the number of complete 100-XP blocks.
For 145 XP, `145 // 100` is 1, so the level is 2. The **remainder** operator
(`%`) gives 45, so the progress bar shows 45/100 toward level 3. At exactly
100 XP, level 2 begins and the bar returns to 0/100. Levels are not capped.

| Level | Rank |
| --- | --- |
| 1 | IT Apprentice |
| 2 | Cyber Student |
| 3 | Security Analyst |
| 4 | Ethical Hacker |
| 5 | Cyber Law Specialist |
| 6+ | Cyber Law Master |

These progression ranks use XP levels. The existing results labels such as
Excellent and Very Good continue to use quiz-point percentage.

### Hearts and recovery

Every quiz begins with 3 hearts. An incorrect MCQ loses one. Written scores
0–2 lose one, 3 loses none, and 4–5 are safe. Lives remain between 0 and 3.

At zero, the HUD says **NO HEARTS LEFT - KEEP STUDYING!**. It allows the next
question, continued scoring, and eventual results. There is no Survival Mode
or early game-over rule in Phase 6.

The optional recovery rule is included: a successful answer at streak 3, 6,
9, and so on restores one heart when below 3. This recovery can happen more
than once during a quiz, while each XP threshold and achievement still pays
only once. Recovery never exceeds three hearts and displays `+1 HEART`.

Hearts use drawing primitives so font support for heart symbols is unnecessary.
The accompanying `Lives n/3` text also makes the value clear.

### Achievements

| Achievement | Unlock condition | XP |
| --- | --- | ---: |
| FIRST BLOOD | First successful answer in the quiz. | 25 |
| ON FIRE | Reach a 3-answer streak. | 25 |
| UNSTOPPABLE | Reach a 5-answer streak. | 50 |
| PERFECT ANSWER | Earn 5/5 on a written scenario. | 25 |
| LAW STUDENT | Successfully answer a Legal Maxims question. | 25 |
| CYBER DEFENDER | Successfully answer Cybercrime or RA 10175 material. | 25 |
| MALWARE HUNTER | Successfully answer a Malware question. | 25 |
| PERFECT RUN | Finish with all possible quiz points. | 50 |
| COMEBACK | Recover a heart after losing one. | 25 |
| MIXED MASTER | Complete a mixed quiz. | 50 |

Each unlock occurs once per quiz. A successful written answer for subject
achievements means 4/5 or 5/5. PERFECT RUN requires actual 100% of quiz points;
answers all graded 4/5 can maintain a streak while falling short of that reward.

Completion achievements are awarded when you move from the last feedback
screen to Results, after every question has been answered. Leaving early
does not unlock PERFECT RUN or MIXED MASTER. Perfect results also display
**PERFECT SCORE!** and use the existing positive audio cue. Audio toggles and
missing-file/device fallback continue to apply; no new sound asset is required.

### New files and functions to learn

All files are already saved; no pasting is needed. Read the two pure modules
first, then the visual integration.

| File | Responsibility |
| --- | --- |
| `achievements.py` | Central catalog of stable IDs, names, descriptions, XP amounts, and eligibility conditions. |
| `progression.py` | Pure answer XP, levels/ranks, heart updates, and a `Progression` object for one quiz. |
| `ui/rewards.py` | Shared HUD, passive XP/achievement popups, and the detailed reward screen. |
| `tests/test_progression.py` | Reward calculations, duplicate prevention, and quiz-session integration. |
| `tests/test_progression_ui.py` | HUD, toast timing, recovery, reward navigation, resizing, and reset checks. |

`calculate_xp()` maps points to base XP. `calculate_level()` uses integer
division; `get_rank()` looks up a title and keeps the final title for higher
levels. `update_lives()` returns a bounded life count using score and streak.
They can run without Pygame or terminal input.

`Progression.reward_answer()` adds the answer reward, pays any newly reached
streak thresholds, updates lives, and unlocks eligible achievements. It
returns a dictionary of XP gains, heart changes, and new unlocks so rendering
can show effects without deciding the rules. `complete_quiz()` handles final
rewards once. Properties expose total XP, level, rank, level progress, and
copied achievement data without requiring callers to duplicate formulas.

A **set** stores unique values. `awarded_streaks` records threshold numbers;
`unlocked_ids` records achievement IDs; `answered_ids` protects against
repeated question rewards. Membership checks such as `identifier not in
unlocked_ids` decide whether a reward is new. An additional list keeps
achievement display order consistent while the set enforces uniqueness.

`QuizSession._record()` continues to update quiz points and streaks, then
passes the result into progression. Each answer record includes its reward
deltas. `finish()` verifies full completion before granting finishing rewards.
The application queues popups and advances their timers without changing XP.
Drawing the HUD, revisiting results, or reviewing an answer never earns XP.

Keeping rules outside Pygame makes calculations independently testable.
The renderer reads progress values; it draws bars, hearts, text, and fading
effects. Session reset creates a fresh object instead of clearing many
individual fields by hand.

Changed existing files: `ui/session.py`, `ui/app.py`, `ui/screens.py`, and
this README. Existing scoring, question selection/data, audio assets,
terminal files, previous tests, and statistics storage are preserved.

### Verification

```powershell
py -m unittest discover -s .\ite184_study_game\tests -v
py .\ite184_study_game\question_bank.py
py .\ite184_study_game\main.py
```

All **115 tests pass**, including the earlier 84, 24 new pure progression/session
tests, and 7 new UI tests. Checks cover every XP mapping, level boundaries,
ranks, one-time threshold/achievement payouts, capped lives, zero-life
continuation, recovery, completion-only rewards, ledger consistency, passive
toast expiry, replay reset, existing modes, and unmodified question data.

To try the motivational-life behavior, start Module 2 → Multiple Choice →
All Difficulties → All Available. Answer three questions incorrectly and
continue at zero hearts. Then answer three correctly to recover one heart.
Watch the XP bar, rank, streak bonus, and recovery popup. Complete a quiz and
open XP & Rewards, then Review Answers. Play Again should start at level 1,
0 XP, and three hearts.

Rendered zero-life, recovery, written HUD, results, and reward screens were
visually inspected. Window launch/close, terminal gameplay, bank validation,
and unchanged JSON storage are checked separately from dummy-driver UI tests.

The Phase 6 section describes the original session-only foundation. Phase 7
now adds the persistence behavior documented below.

## Phase 7 — Persistent Progress

Launch the visual game with its usual command:

```powershell
py .\ite184_study_game\pygame_main.py
```

The Home player card now shows saved XP, level, rank, completed games, best
streak, and progress toward the next level. Review Mistakes shows the number
of active questions to review; Statistics opens your cumulative study record.
The original 26-question bank is unchanged.

### What is saved and when

The only active save is `ite184_study_game/data/stats.json`. Its path is
resolved relative to `stats.py`, so changing the terminal's working directory
does not create another profile. The game loads it at startup and saves
after each graded answer. It does not write on every animation frame.

Every graded answer records attempts, quiz points, mistakes, base/streak XP,
new achievement rewards, and best streak immediately. If you quit the quiz,
close the window, or interrupt afterward, those answered questions remain
counted. Unanswered questions do not affect cumulative accuracy.

Moving from the last feedback screen to Results marks normal completion.
That step additionally saves finishing achievements, increments
`games_played`, and updates applicable high scores. Leaving before that step
does not count a completed game or create a high score, even if the last
answer was already graded. Answer XP is not added again at completion.

### Save schema, version 2

The readable UTF-8 JSON contains:

- `version`, `games_played`, `total_xp`, `best_streak`, and `questions_answered`.
- `total_points_earned` / `total_points_possible`.
- `mcq`: answered and correct counts.
- `written`: answered, earned/possible points, and perfect-answer count.
- `modules`: point totals keyed by `"1"` and `"2"`.
- `topics`: earned/possible points and attempt counts.
- `question_stats`: attempts, successes, and point totals keyed by stable ID.
- `mistake_ids`: unique active review IDs.
- `achievements`: permanently unlocked achievement IDs.
- `high_scores`: best overall, Module 1, Module 2, and mixed quiz percentages.
- `high_score_counts`: qualifying completed quizzes for each high-score category,
  distinguishing N/A from a legitimate completed 0% score.
- `recent_event_ids`: the most recent 512 save-event IDs, preventing duplicate
  answer/completion credit during retries.

**JSON persistence** means converting Python data to text on disk, then
reading it into Python again next launch. This conversion is called
**serialization**. JSON objects become dictionaries and JSON arrays become
lists. `json.dump(..., ensure_ascii=False, indent=2)` keeps Unicode readable
and formats the file for inspection.

### Safe loading, migration, and saving

A **schema version** identifies the data format. **Migration** fills fields
that older saves lack. The previous `{}` placeholder needs no manual deletion:
it becomes clean version-2 defaults on launch. Known legacy counts, XP,
high-score values, and `wrong_question_ids` are migrated where possible.

`migrate_stats()` checks nested types, resets invalid values to safe defaults,
keeps counts nonnegative, caps implausibly huge counters, and rejects NaN or
infinite percentages. Missing fields and malformed nested data cannot feed
unsafe types into screen rendering. Each default call builds independent
containers so different profiles/tests cannot share mutable data accidentally.

An empty, invalid JSON, invalid-encoding, or non-object save is recovered
without a traceback. Its original bytes are copied to
`stats.corrupt.<unique-id>.json` where possible before fresh defaults are
written. Unsupported newer versions are preserved in a `stats.future.*.json`
backup before known fields are migrated. These backups are recovery artifacts,
not additional active profiles. Helpful warnings go to the console and UI.

**Atomic saving** writes a complete JSON document to a temporary `.tmp` file
in the same directory, flushes it, closes it, then uses `os.replace()` to
replace `stats.json`. Closing first matters on Windows. A failed replacement
leaves the previous save intact; temporary files are cleaned up. This reduces
the risk of leaving a half-written JSON document.

If the folder/file cannot be read or written, gameplay continues. A failed
write keeps updated progress in memory for the current run and shows a short
warning. The next answer/retry can save that accumulated state. A failed
reset retains the current progress and reports that it was kept.

### Permanent XP and achievements

Each quiz still tracks its own answer, streak, and newly earned achievement
XP. The save accumulates these rewards after each answer, plus any final
achievement XP at completion. Home and the gameplay HUD show permanent XP
and derive permanent level/rank using the existing functions:

```python
level = total_xp // 100 + 1
rank = get_rank(level)
```

Results show both `+session XP earned` and permanent total XP/level. The
session remembers the level before the quiz; if the permanent level rises,
Results displays `LEVEL UP! old -> new`.

New sessions are seeded with saved achievement IDs. Already unlocked
achievements grant no additional achievement XP or unlock popup. The save
manager independently checks uniqueness as well. They can appear as
Previously unlocked in XP & Rewards, and the Statistics achievement viewer
shows all ten rewards with UNLOCKED/LOCKED labels. Answer and once-per-quiz
streak XP still reward future study, including Review Mistakes quizzes.

Hearts, current streak, answer text, and the current quiz itself stay local
to that quiz. Closing does not resume an unfinished quiz; its graded attempts
and earned rewards have already been saved.

### Mistake history and Review Mistakes

A **dictionary keyed by question ID** keeps historical attempts attached to
the same question despite shuffling. Successful attempts mean a correct MCQ
or a written score of at least 4; actual earned points are retained separately.

Incorrect MCQs and written scores 0–3 add their ID to `mistake_ids`. A later
successful answer removes it from the active review pool, including ordinary
practice. Its historical `question_stats` entry remains. Set membership and
deduplication prevent repeated IDs in the active pool.

Review Mistakes offers Review All, Module 1, Module 2, MCQ Only, and Written
Only. Stable IDs are looked up through the original question bank, copied,
and shuffled. Deleted/unknown IDs are safely ignored. The ordinary MCQ and
written screens handle review answers; there is no second grading engine.
Both types automatically form a mixed review when present.

A successful review answer briefly displays **MASTERED! Removed from Review
Mistakes**. The removal is saved immediately. Replaying a review uses the
remaining active mistakes; when none remain, the caught-up screen appears.
Completed reviews count as completed quizzes and can update the relevant
high scores. Achievement XP remains one-time across the profile.

### Statistics, topics, and high scores

Statistics shows permanent player totals, overall points, MCQ accuracy,
written points/perfect answers, module percentages, review count, and high
scores. With no applicable attempts/qualifying quizzes, percentages show
**N/A** instead of dividing by zero.

```python
overall = total_points_earned / total_points_possible * 100
mcq_accuracy = mcq_correct / mcq_answered * 100
written_score = written_points_earned / written_points_possible * 100
```

`get_accuracy()` returns `None` when the denominator is zero; the UI formats
that as N/A. **Cumulative statistics** add every saved attempt, including
review and abandoned-quiz answers, rather than averaging quiz percentages.

Topic Stats sorts topics from lowest point performance upward. Weak Areas
highlights topics below 70% only after at least two graded attempts, so one
miss does not immediately label a topic weak. The view displays points and
attempt counts alongside percentages and NEEDS REVIEW markers.

High scores only improve after a completed quiz. Overall includes all
completed selections; module-specific records require that module alone;
mixed records require Mixed Mode. They use quiz earned/possible points and
are separate from cumulative performance.

### Reset confirmation

Statistics → Reset Statistics opens **RESET ALL PROGRESS?** and explains
the permanent erase. Cancel and Escape retain the save. Reset atomically
replaces only the active statistics file with defaults, clearing XP,
achievements, high scores, attempts, and active mistakes. It does not modify
`question_bank.py`, audio, or any other course content. Recovery backups are
retained independently.

### Files and functions to study

Everything is already saved; no pasting is needed.

| File | Role |
| --- | --- |
| `stats.py` | Defaults, migration, atomic file operations, cumulative metrics, active mistakes, and `StatsStore`. |
| `ui/stats_screens.py` | Statistics, Topic Stats, Achievements, and Review Mistakes setup. |
| `ui/session.py` | Saves graded answers and completion once; accepts an optional review pool/store. |
| `progression.py` | Seeds known achievements while retaining the per-quiz XP ledger. |
| `ui/app.py` | Loads the profile, navigates persistent views/review, and confirms reset. |
| `ui/screens.py`, `ui/rewards.py` | Saved Home card, badge, permanent HUD, session/total results, level-up/mastered messages, and reset overlay. |

`create_default_stats()`, `migrate_stats()`, `load_stats()`, and `save_stats()`
handle storage. `get_topic_stats()`, `get_weak_topics()`, and
`get_active_mistakes()` produce useful review data. `StatsStore.record_answer()`
adds one attempt and its rewards; `record_completed_quiz()` handles finishing
totals/high scores. `StatsStore.reset()` commits clean defaults only when
the write succeeds.

New test files are `tests/test_stats.py` and `tests/test_stats_ui.py`.
Three existing GUI test files now inject temporary `StatsStore` paths so
tests cannot change real progress. The earlier disabled-button test still
checks disabled controls with a fixture; Home's review/statistics buttons
are now correctly enabled. The other original regression checks are preserved.

### Verify Phase 7

```powershell
py .\ite184_study_game\pygame_main.py
py -m unittest discover -s .\ite184_study_game\tests -v
py .\ite184_study_game\question_bank.py
py .\ite184_study_game\main.py
```

All **161 tests pass**: the previous 115 checks, 34 storage/business tests,
and 12 persistent UI tests. They cover migration, corrupted backups, UTF-8,
atomic replacement/failure, retry deduplication, permanent XP/achievements,
question history, point statistics, high scores, active review, reopening,
weak areas, reset confirmation/failure, audio, and resizing.

Try answering incorrectly and exiting midway. Reopen the visual game: XP,
attempts, and the review badge remain, while completed games/high scores have
not increased. Review that question successfully, reopen again, and check
that it leaves the active pool while its attempts remain in statistics.
Finish a full quiz to update games/high scores, then inspect Topic Stats and
Achievements. Use a confirmed reset only when you intend to erase progress.

The terminal MCQ frontend remains available with its existing behavior;
its statistics/mistake menu placeholders are unchanged. Permanent progression
and review are implemented in the visual frontend. At the end of Phase 7,
the original bank contained 26 questions; Phase 8 below adds the full content.

## Phase 8 — Full ITE184 Question Bank

The shared terminal/Pygame bank now contains **261 questions**, including the
original 26 dictionaries unchanged. This exceeds the 260-question minimum by
one additional ILOVEYOU attachment/attribution exercise.

| Module | MCQ | Written | Total |
| --- | ---: | ---: | ---: |
| Module 1 | 45 | 30 | 75 |
| Module 2 | 110 | 76 | 186 |
| **Total** | **155** | **106** | **261** |

| Difficulty | Module 1 | Module 2 | Total | Share |
| --- | ---: | ---: | ---: | ---: |
| Easy | 22 | 56 | 78 | 29.9% |
| Medium | 30 | 74 | 104 | 39.8% |
| Hard | 23 | 56 | 79 | 30.3% |

### Topics and saved statistics

Topic names remain consistent. Three starter names are deliberately retained:
**Basic Concepts** covers Ethics Basics; **IT Laws** covers RA 8792; and
**Espionage** covers Computer Espionage. Keeping these names preserves the
meaning of existing saved topic totals. Supplemental laws use one shared
topic, with individual statutes named in subtopics.

| Module | Topic | Questions |
| --- | --- | ---: |
| 1 | Basic Concepts | 7 |
| 1 | Ethical Theories | 34 |
| 1 | Legal Maxims | 12 |
| 1 | Professional Ethics | 14 |
| 1 | Law vs Ethics | 8 |
| 2 | Types of Computer Crime | 14 |
| 2 | Sexually-Related Laws | 19 |
| 2 | Cybercrime | 25 |
| 2 | Hacking | 10 |
| 2 | Malware | 30 |
| 2 | Hacker Ethics | 9 |
| 2 | Professional Constraints | 7 |
| 2 | IT Laws | 8 |
| 2 | Access Device Fraud | 13 |
| 2 | Data Privacy | 6 |
| 2 | Espionage | 7 |
| 2 | Hacking Cases | 20 |
| 2 | Malware Cases | 13 |
| 2 | Supplemental Laws | 5 |

Coverage includes all eight ethical theories, all three legal maxims,
professional responsibilities, law versus ethics, all eight major crime
categories, hacking terminology, the five RA 10175 offense distinctions,
malware types, hacker ethics, professional constraints and espionage types.
Hard scenarios combine acts, laws, consent, authorization scope and ethical
reasoning. They distinguish 49 from 50 cards without suggesting that fewer
than 50 makes skimming lawful, and distinguish favorable intent from actual
consequences.

**Hacking cases:** Kevin Mitnick, Raphael Gray, Masters of Deception,
Mafiaboy, Legion of Doom, Robert Tappan Morris/Morris Worm, and Anonymous
Philippines. LOD's main defendants and Craig Neidorf's separate prosecution
remain distinct. COMELEC defacement does not establish attribution for every
later Comeleak release action.

**Malware cases:** Nimda, ILOVEYOU, Melissa, Code Red, Anna Kournikova, and
Mydoom. The Morris Worm is also studied in the hacking-case section.
Melissa and Morris exercises include the supplied mechanisms, outcomes and
ethical issues; damage/computer-count estimates remain labeled as estimates.

**Laws:** RA 8792, RA 10175, RA 10173, RA 9995, RA 11313, RA 11930,
historical RA 9775, RA 8484, RA 11449, RA 8293, RA 11055, RA 11934, and
RA 11479. RA 9775 is described as replaced by RA 11930. RA 11449 is the
access-device amendment; RA 11479 is the Anti-Terrorism Act. Supplemental
laws stay within the supplied identification/application facts.

### Content files and editing

`question_bank.py` retains the original dictionaries and the public filters,
lookup, summary and validator. It appends explicitly authored content from:

| File | Added content |
| --- | --- |
| `questions/module1.py` | Ethics, theories, maxims and professional scenarios. |
| `questions/module2_crimes.py` | Crime categories, hacking labels and cybercrime distinctions. |
| `questions/module2_laws.py` | Philippine laws, consent, thresholds and overlapping issues. |
| `questions/module2_malware.py` | Malware definitions, comparisons and multi-feature scenarios. |
| `questions/module2_cases.py` | Hacking and malware case facts and assignment exercises. |
| `questions/module2_ethics.py` | Hacker ethics, professional constraints and espionage. |
| `questions/builders.py` | Converts compact authored entries into the existing dictionary schema. |
| `content_audit.py` | Read-only content quality checks and a command-line report. |

The builders use pipes between MCQ options and semicolons between synonyms
inside a written concept group. The first authored MCQ option is correct;
the existing engine shuffles choices and maps their answer letters at runtime.
IDs are explicit, independent of list position or quiz order.

**Never rename or remove an existing question ID.** Saved attempts and active
mistakes depend on those IDs. New content adds `M1_MCQ_007` through `045`,
`M1_WR_005` through `030`, `M2_MCQ_011` through `110`, and `M2_WR_007` through
`076`. Existing save schema, XP rules, engines and game design remain as before.

Written scoring still uses the existing deterministic **keyword groups**.
One synonym satisfies one concept; every synonym is not required. Distinct
groups represent the requested concepts, while optional keywords add detail.
Every stored model answer matches all its required groups and earns at least
4/5. This grader recognizes phrases rather than interpreting an essay's full
reasoning, so use the requested law/offense/theory names and explain their
relevance. No AI or network grading was added.

### Validation and duplicate audit

The final bank passes `validate_question_bank()`. The content audit reports
**0 errors and 0 review warnings**, including no duplicate IDs, normalized
prompts or scenarios, malformed groups, inconsistent topics, or model answers
missing required concepts. No near-text pairs were flagged; the maximum reuse
of an identical four-choice set is **3**, below the warning threshold of 8.
Sharing a topic is never treated as duplication. Similar wording and excessive
choice-set reuse are review warnings rather than automatic proof of duplication.

```powershell
py -B .\ite184_study_game\question_bank.py
py -B -m ite184_study_game.content_audit
py -B -m unittest discover -s .\ite184_study_game\tests -v
py .\ite184_study_game\pygame_main.py
py .\ite184_study_game\main.py
```

**211 automated tests pass:** all 161 previous checks remain, plus 42 bank/audit
tests and 8 full-bank Pygame integration tests. Tests with starter-pool count
assertions use the original 26-question fixture; their assertions are retained.
The new tests independently exercise the actual expanded pool, every
module/mode/difficulty/count combination, all 261 rendered questions and
feedback screens, model-answer grading, mixed-point accounting and old-save
compatibility. Scorer model checks also run against the full bank.

Phase 7 save compatibility is checked by reopening a temporary profile with
all 26 old mistake IDs, old question history, XP and topic totals, then saving
a new question attempt. Old IDs and history still resolve. Review tests reopen
both old and new mistakes, master them and retain their attempt history. Tests
and previews use temporary profiles; the player's save is not used for practice.

### Visual study checks

Pygame event/render checks cover Module 1 / Hard / Written, Module 2 / Hard /
Mixed, Both / All Difficulties / 20 questions, and Review Mistakes. Model
answers and explanations scroll, long scenarios respond to the mouse wheel,
choice labels and metadata fit the existing controls, all topic statistics
scroll, and XP/statistics survive reopening. Screenshots were inspected at
1280×720; this is a scripted render/event review, not a live manual desktop run.

Optional screenshot regeneration:

```powershell
py -B -m ite184_study_game.tools.preview_phase8
```

Review PNGs are in `artifacts/phase8/`, covering written entry/feedback, long
MCQ choices/feedback, mixed results, mistake review and topic statistics.
The preview's progress exists only in a temporary profile.

### Source boundaries

All additions use only the supplied Phase 8 notes and the original bank; no
web research or unsupported trivia was added. The conflicting RA 8792 State
Policy section number is deliberately omitted. No unsupplied law sections,
supplemental-law penalties, detailed terrorism/SIM/PhilSys provisions, or
additional case sentences/prosecution outcomes are invented. Onel de Guzman
remains ILOVEYOU's **main suspect**; Nimda, Code Red and Mydoom creators remain
not conclusively identified. Neidorf is not merged into the main LOD defendants,
and later Comeleak attribution is not assumed. Legal scenarios use cautious
phrasing where the supplied facts do not establish every element.

Phase 8 is complete; Phase 9 follows below.

## Phase 9 — Exam Mode

Home now offers **STUDY MODE** and **EXAM MODE**, alongside Review Mistakes,
Statistics, Settings and Quit. Study Mode retains immediate grading,
explanations, keyword feedback, answer locks, hearts, streaks and rewards.
Exam Mode stores editable answers in memory and grades the final selection
only after submission. Both use the same unchanged 261-question bank and
the same written scorer.

### Setup and Atty Long Quiz

Choose Exam Mode, then **ATTY LONG QUIZ** or **CUSTOM EXAM**. Custom setup runs
through module → question type → difficulty → count → timer → instructions.
No timer starts on the setup/instructions screens; START EXAM begins it.

| Setting | Options |
| --- | --- |
| Module | Module 1, Module 2, Both modules |
| Question type | Multiple choice, Written, Mixed |
| Difficulty | Easy, Medium, Hard, All difficulties, Long Quiz Mix |
| Count | 10, 20, 30, 50, All Available, Custom |
| Timer | No Timer, 15, 30, 45, 60 minutes, Custom 1–180 minutes |

Custom counts must be positive whole numbers. A request larger than the
matching pool shows its available count and asks whether to use that count;
it does not silently start a shorter exam. Cancel returns to count selection.
The pure preparation function clamps overlarge requests, while the UI owns
the required confirmation.

The **Atty Long Quiz** preset uses Both modules, Mixed, Long Quiz Mix,
30 questions and 45 minutes. With the current full bank it selects:

| Dimension | Distribution |
| --- | --- |
| Modules | 10 Module 1 / 20 Module 2 |
| Question types | 15 MCQ / 15 Written |
| Difficulty | 6 Easy / 12 Medium / 12 Hard |
| Possible points | 15 MCQ points + 75 Written points = 90 |

Long Quiz Mix targets 20% easy, 40% medium and 40% hard. Mixed mode targets
approximately half MCQ and half written. Both modules targets one third
Module 1 and two thirds Module 2, ensuring both appear when feasible.
Preparation respects available difficulty/type/module cells, redistributes
shortages and chooses the closest feasible balance when targets conflict.
All Available includes every matching question. No question ID is duplicated.
Question order is shuffled and source dictionaries remain unchanged.

### Answers, navigation and controls

Each exam owns a prepared snapshot. Every MCQ's choices are shuffled once and
its A–D mapping stays identical when revisiting. The selected **answer text**
is stored by stable question ID. Written responses retain exact typed text,
including spaces, punctuation and line breaks, and update in memory as you
type. Navigating away does not erase an answer.

| Control | Behavior |
| --- | --- |
| Click an MCQ choice; A–D or 1–4 | Select or change an answer; selected choices show `[SELECTED]`. |
| Written textbox | Edit a response up to 1,000 characters; ordinary editing keys work. |
| Enter / Shift+Enter in written exams | Add a line; never grade or submit an individual answer. |
| Previous / Next | Navigate without grading. Left/right arrows also navigate MCQs. |
| Clear Answer | Remove the current response and mark the question unanswered. |
| Flag for Review / Unflag | Toggle a flag; flags do not affect scoring. |
| Questions | Open the palette and jump to any question. |
| Submit Exam | Open the final confirmation; it does not immediately submit. |
| Escape | Close a panel or confirm abandoning the active exam. |
| Window close | Confirm abandonment before closing an active exam. |
| Mouse wheel | Scroll long questions, written responses, results and review panels. |

The palette shows every question using pages of 40. Labels use **A** for
answered, **?** for unanswered, **F** for flagged and **\*** for current,
along with a highlighted current border/button. State is readable without
relying only on color. Answered, unanswered and flagged totals stay visible.

Opening settings or the palette does not allow typing through the overlay.
Submit confirmation shows answer/flag counts and time remaining. **Review
Unanswered** and **Review Flagged** jump to the first matching question.
Cancel returns to answering; Submit Anyway grades unanswered slots as zero.
Final submission locks answer edits, flags and navigation.

### Timer and abandonment

`ExamSession` uses `time.monotonic()` to calculate duration minus real elapsed
time, rather than decrementing a counter each frame. Remaining time is
displayed as MM:SS. No Timer has no deadline. Settings, question palette,
submission confirmation and window focus loss never pause a timed exam.
Small five-minute/one-minute warnings do not interrupt answering.

When time reaches zero, the exam submits automatically once, closes any
open panel, and shows **TIME IS UP / EXAM COMPLETE**. The latest stored
written draft is included. An input arriving after the deadline is not
accepted as a last-second answer. Reported time used freezes at submission
and is capped at the configured duration for an expired exam.

Escape or closing the window opens **EXIT EXAM?** with Continue and Exit
choices. Abandoning discards the session without grading, XP, mistakes,
completed-exam counts, history or high-score changes. Active-exam crash
recovery is deliberately deferred: answers are kept in memory only. A process
crash or forced termination can lose an unsubmitted exam.

### Deferred grading and results

During an active exam, screens display only the prompt, choices or editable
response, topic, timer, navigation and answer/flag counts. Answer keys,
subtopics that could identify the answer, explanations, models and keyword
groups are excluded from the player-facing question projection. There is no
score, XP, heart, streak, achievement or correctness animation while answering.
Only music and ordinary click cues play; correct/wrong cues occur after final
grading. Permanent attempt/reward statistics do not change while navigating.

After submission, MCQs earn 0/1. Written answers reuse `scorer.py` unchanged
and retain its 0–5 keyword-group partial-credit rules. Unanswered MCQs earn
0/1 and unanswered/whitespace-only written responses earn 0/5. Exam percentage
is total earned points divided by total possible points; it is not an average
of per-question percentages. Existing performance labels are reused.

Results include score, percentage/label, total/answered/unanswered questions,
flags at submission, time used, per-module and per-type points, the five lowest
topic percentages, best streak, XP and newly unlocked achievements. Breakdowns
and long review content scroll. Streak/reward calculation follows final
question order only after grading. Exam progression disables life changes and
heart-recovery achievements; Study's life/reward behavior remains the default.

**Review Exam** shows each original question/scenario, the player's exact
answer, correct/model answer, earned points, explanation and important
keywords. Written review also shows matched and missed required concepts.
Filters are All, Incorrect / Partial, Flagged and Unanswered. A written 4/5
appears in Partial review even though it counts as successful mastery.
Full exam review is available for the current submitted session; saved history
contains summaries rather than a permanent copy of all responses.

### Permanent statistics, mistakes and migration

The save schema is now **version 3**. On the next normal launch, existing
version 2 saves migrate automatically, preserving XP, achievements, question
history, active mistake IDs, topic/module totals and Study high scores. New
defaults add `exams` and `exam_history`; no real player data was used for tests.

`StatsStore.record_exam()` applies all final attempts/rewards and the exam
summary, then saves once using the existing atomic replacement mechanism.
There is no partially saved list of graded exam questions. Submission and save
retries are deduplicated; a failed save retains progress in memory, displays
the warning and offers **Retry Save** without granting points or XP again.

The counting rule is consistent: **every submitted slot counts as one attempt,
including unanswered slots with zero points**. These attempts contribute to
existing cumulative question, MCQ/written, module, topic and best-streak totals.
The general `questions_answered` counter therefore includes submitted blank
exam slots; the exam result/history separately records answered versus
unanswered counts. Unsubmitted/abandoned slots contribute nothing.

Existing mastery rules apply after submission: wrong/unanswered MCQs and
written scores 0–3 join Review Mistakes; correct MCQs and written scores 4–5
remove an existing active mistake while retaining attempt history. Mistake IDs
remain unique. Review Mistakes uses the existing Study review path.

Exam completions and highs are separate from Study games/high scores. The
`exams` record tracks completed count, best, average, last percentage, percentage
sum, and Module 1/Module 2/Both bests plus their completion counts. Average is
the arithmetic mean of completed exam percentages. Completion counts distinguish
a real 0% score from **N/A**. Statistics includes **EXAM PERFORMANCE** in the
scrollable Modules / High Scores panel, with an **EXAM HISTORY** button.

History retains the last ten completed summaries: UTC date, exam ID, selection,
question count, earned/possible points, percentage, answer/flag counts and time
used. It stores no duplicate question dictionaries or full answers. Confirmed
Reset Statistics also clears exam totals/history along with existing progress.

### Files and validation

| New file | Responsibility |
| --- | --- |
| `exam_engine.py` | Copied pools, constrained distributions, stable MCQ snapshots and pure final grading. |
| `exam_session.py` | Answers, flags, visited IDs, navigation, monotonic time and submission locks. |
| `ui/exam_controller.py` | Exam setup, custom inputs, draft persistence, overlays and result/review navigation. |
| `ui/exam_screens.py` | Exam-only question, palette, confirmation, results, review and history layouts. |
| `tests/test_exam.py` | 74 preparation/session/grading/persistence checks. |
| `tests/test_exam_ui.py` | 30 real Pygame event/render checks. |
| `tools/preview_phase9.py` | Repeatable screenshots using temporary progress and a fake clock. |

Changed files are `ui/app.py`, `ui/screens.py`, `ui/button.py`,
`ui/stats_screens.py`, `stats.py`, `progression.py`, this README and three
schema-version assertions in `tests/test_stats.py`. The existing 211 tests and
their behavior checks remain. The question bank, written scorer, terminal quiz
engine and terminal entry files are unchanged.

```powershell
py .\ite184_study_game\pygame_main.py
py -B -m unittest discover -s .\ite184_study_game\tests -v
py -B .\ite184_study_game\question_bank.py
py -B -m ite184_study_game.content_audit
py -B -m ite184_study_game.tools.preview_phase9
py .\ite184_study_game\main.py
```

**315 automated tests pass**: the original 211 plus 104 Phase 9 checks. New
coverage includes quotas/shortages, both-module weighting, stable shuffled
choices, exact answer edits, flags, navigation bounds, no pre-submit grading or
progress writes, deadline handling under settings/palette/focus loss, auto-submit,
unanswered scoring, filtered review, mistakes/mastery, atomic save retry,
averages/highs/history, v2 migration, resize/audio and Study regression behavior.
The 261-question bank still validates and its content audit remains clean.

Screenshots in `artifacts/phase9/` cover Home, setup/preset instructions,
MCQ selection, written drafts, flags/palette, confirmation, results, review
filters, mistakes, exam statistics/history, timeout, abandonment and resizing.
Pygame event tests and inspected screenshots verify these flows; they are
scripted visual checks, not a live manual desktop run. The preview uses an
isolated profile and never changes the real `data/stats.json`.

Active-exam crash recovery and permanent detailed answer-review storage remain
deferred. Phase 9 is complete; Phase 10 has not been started.
