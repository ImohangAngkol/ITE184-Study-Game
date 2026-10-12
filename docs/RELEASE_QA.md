# v1.0.0 release QA

Release verification uses temporary profiles and copied source. Real player
progress is retained unchanged. The full question bank is frozen by a release
manifest containing all 261 IDs and a SHA-256 content digest.

## Environment and installation

- Windows; Python 3.14.2.
- Fresh `.qa/release-venv`, created without system-site packages.
- Installed `requirements.txt` successfully: pygame-ce 2.5.8.
- pygame-ce provides the `pygame` import; no standard-library requirements.
- Runtime syntax checked against the documented Python 3.10 minimum.

## Release checklist

- [x] Actual desktop entry point launches and exits cleanly in a clean copy.
- [x] Missing data directory/save initializes schema 3 defaults.
- [x] Launch from an unrelated working directory resolves code/assets/data correctly.
- [x] Screenshots, tests, developer tools and QA artifacts are unnecessary for runtime.
- [x] 261 questions validate; no content changes, ID changes or duplicate prompts.
- [x] MCQ, Written and Mixed Study Mode work with a fresh profile.
- [x] Study exit copy correctly describes saved graded attempts.
- [x] Review Mistakes, mastery removal, analytics, achievements and reset work.
- [x] Exam setup, Atty preset, timers, flags, submission and review work.
- [x] No exam grading, rewards or saved answer statistics before submission.
- [x] Reopening preserves progress and exam summaries.
- [x] Schema 2 migrates to 3 without erasing existing fields.
- [x] Corrupt/invalid saves recover with existing backup behavior.
- [x] Audio assets resolve relative to the source; missing audio/device remains safe.
- [x] Resizing, scrolling, selected states, focus and back navigation pass UI checks.
- [x] About/Credits and window title use shared v1.0.0 metadata.
- [x] Terminal MCQ frontend and desktop feature directions work.
- [x] Public README links point to release screenshots; development notes are preserved.
- [x] Dependency requirements, ignore rules, MIT license and changelog exist.
- [x] Release inventory excludes private player data and developer output.
- [x] Runtime path and likely-secret scans report no findings.

**340 tests pass in both the working interpreter and the fresh virtual
environment**, with no skipped checks. All 315 existing checks remain, plus
25 release checks. Existing title/message assertions were updated to reflect
shared version metadata and corrected desktop-feature directions; no behavior
tests were removed. Both complete runs finished successfully on 2026-10-12.

The source/secret audit inspected 88 eligible files with no findings. All 57
Python files passed a Python 3.10 syntax check. The question-bank validator
passes and its duplicate audit reports zero errors/warnings. The release
manifest verifies all original IDs and all 261 question dictionaries unchanged.
Git's actual ignore checks confirm saves, corrupt/future backups and QA output
are excluded, while source fixtures, audio, public screenshots and the data
placeholder remain included. The real save remains byte-for-byte unchanged.

**12 screenshots** in `screenshots/` are real renders from an isolated
demonstration profile; they are not private saves or copied developer QA images.

Visual verification uses Pygame events, dummy SDL video/audio drivers and inspected
renders at 1280×720, including resize tests. This verifies rendering, loading,
music/SFX controls and error handling; it is not a live manual desktop session
or a physical-speaker listening test.

## File summary

Created: root README, requirements, ignore rules, MIT license, changelog, optional
run scripts, shared `version.py`, `data/.gitkeep`, release regression tests and
question manifest, screenshot/clean-copy helpers, three documentation files,
and twelve public PNGs.

Updated: `pygame_main.py`, `game.py`, `ui/app.py`, `ui/screens.py`,
`ui/stats_screens.py`, the internal README, and the existing caption/terminal-copy
assertions in `test_pygame_ui.py` and `test_quiz_engine.py`. The original engines,
written scorer, progression, save schema and course bank were not rewritten.

Git preparation remains local-file work only: this folder has no independent
repository yet, the existing parent repository was left untouched, and no
staging, commit, remote creation or push was performed. See RELEASE.md for the
recommended project-level initialization and first commit.

## Release limits

Run from Python source. EXE packaging was not attempted. Active-exam crash
recovery and permanent detailed exam response history remain deferred; only
the last ten summary records persist. Written grading is phrase matching rather
than semantic essay evaluation. No additional game systems or logging framework
were introduced.
