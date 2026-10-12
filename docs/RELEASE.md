# v1.0.0 source release preparation

Recommended GitHub repository name: **ITE184-Study-Game**.

Description:

> Interactive Python/Pygame reviewer for computer ethics, Philippine IT laws,
> cybercrime, and scenario-based exam practice.

Topics: `python`, `pygame`, `pygame-ce`, `quiz-game`, `educational-game`,
`cybersecurity`, `cybercrime`, `computer-ethics`, `philippine-law`, `study-tool`.

## Repository boundary and first commit

The project folder does not yet have its own `.git` directory. Inspection found
an existing repository in a parent user directory. Initialize this project
separately before staging; do not run the following commands from that parent.
No repository was initialized, no commit was created and nothing was pushed
during release preparation.

Open PowerShell in the folder containing this README and `requirements.txt`:

```powershell
git init -b main
git rev-parse --show-toplevel
git check-ignore -v --no-index ite184_study_game/data/stats.json
git add README.md requirements.txt .gitignore LICENSE CHANGELOG.md run_game.bat run_tests.bat ite184_study_game docs screenshots
git status --short
git diff --cached --stat
git commit -m "release: prepare ITE184 Study Game v1.0.0"
```

Check that the reported root is the project folder and that personal saves do
not appear in staged files. `.gitignore` protects runtime JSON (including corrupt
and future-format backups), virtual environments, local editor files, QA output,
generated developer previews and logs. Source, question fixtures, audio and
public screenshots remain eligible for Git.

Remote creation, remote configuration, pushing and tagging can be performed
later when explicitly requested. No GitHub API connection is needed here.

## Dependencies and distribution

The source release requires Python 3.10+ and `pygame-ce>=2.5.8,<3` for the desktop
frontend. Terminal mode uses only the standard library. A fresh virtual
environment was tested with Python 3.14.2 and pygame-ce 2.5.8; the working
interpreter was not downgraded or modified.

Executable packaging was **not attempted**. PyInstaller was not installed in
the inspected environment, and v1.0 is a verified source release. This is not a
claim that a particular PyInstaller/Python combination is unsupported. No EXE,
installer or packaging compatibility guarantee is included.

Active-exam crash recovery and persistent detailed exam response history remain
deferred. The current ten-summary history is retained. Existing warning logging
is sufficient; no extra file logger was added.

## Maintainer checks

```powershell
py -B -m unittest discover -s ite184_study_game/tests -v
py -B -m ite184_study_game.content_audit
py -B -m ite184_study_game.tools.release_check
py -B -m ite184_study_game.tools.preview_release
```

`release_check` inventories eligible source files, scans for likely secrets and
absolute developer paths, and launches a runtime-only temporary copy from an
unrelated working directory. That copy omits saves, screenshots, tests, tools,
docs and developer artifacts. Its fresh profile exercises Study, Exam,
mistakes/mastery, analytics, About, reopening and old-save migration.
Temporary QA data are never part of the release inventory.

Privacy scans are heuristic checks, not a mathematical guarantee that any future
file is safe. Keep personal records in ignored runtime data, and review the staged
file list before committing. Current content consists of hypothetical study
scenarios, historical case references and explicitly credited authorship metadata.
