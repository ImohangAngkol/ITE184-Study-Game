"""Read-only source audit and clean-copy launch/profile QA for the source release.

Run from the repository root: py -B -m ite184_study_game.tools.release_check
Only owned temporary copies/profiles are mutated. No network or Git writes.
"""

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from ..question_bank import get_all_questions, validate_question_bank
from ..version import __version__

ROOT = Path(__file__).resolve().parents[2]
IGNORED_PARTS = {"__pycache__", "artifacts", ".qa", ".venv", ".git"}


def bank_digest():
    bank = sorted(get_all_questions(), key=lambda q: q["id"])
    return hashlib.sha256(json.dumps(bank, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def release_files(root=ROOT, *, runtime_only=False):
    """An explicit release inventory; personal saves never enter this list."""
    root = Path(root)
    files = []
    for name in ("README.md", "requirements.txt", ".gitignore", "LICENSE", "CHANGELOG.md", "run_game.bat", "run_tests.bat"):
        path = root / name
        if path.is_file():
            files.append(path)
    folders = ("ite184_study_game",) if runtime_only else ("ite184_study_game", "docs", "screenshots")
    for folder in folders:
        for path in (root / folder).rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(root)
            if any(part in IGNORED_PARTS for part in relative.parts):
                continue
            if "data" in relative.parts and path.name != ".gitkeep":
                continue
            if runtime_only and any(part in ("tests", "tools") for part in relative.parts):
                continue
            if path.suffix in (".py", ".md", ".wav", ".png") or path.name == ".gitkeep" or (
                    path.suffix == ".json" and "fixtures" in relative.parts):
                files.append(path)
    return sorted(set(files))


def audit_release(root=ROOT):
    """Return paths/issue categories, never print possible credential values."""
    root = Path(root)
    errors = []
    patterns = {
        "private-key material": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        "possible API/token credential": re.compile(r"\b(?:ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|sk-[A-Za-z0-9]{30,}|AKIA[A-Z0-9]{16})\b"),
        "assigned secret": re.compile(r"(?:api[_-]?key|client[_-]?secret|access[_-]?token)\s*[:=]\s*['\"][A-Za-z0-9_/-]{16,}['\"]", re.I),
    }
    for path in release_files(root):
        if path.suffix not in (".py", ".md", ".json", ".txt") and path.name not in ("LICENSE", ".gitignore"):
            continue
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(root)
        for category, pattern in patterns.items():
            if pattern.search(text):
                errors.append(f"{relative}: {category}")
        if path.suffix == ".py" and not any(part in ("tests", "tools") for part in relative.parts):
            if re.search(r"[A-Za-z]:[/\\](?:Users|home)[/\\]", text.replace("\\\\", "\\"), re.I):
                errors.append(f"{relative}: absolute developer path")
    for path in release_files(root):
        relative = path.relative_to(root)
        if "data" in relative.parts and path.name != ".gitkeep":
            errors.append(f"{relative}: runtime player data in release inventory")
    return {"errors": errors, "files_checked": len(release_files(root)), "version": __version__}


LAUNCH_PROBE = r'''
import json, runpy, sys
from pathlib import Path
package = Path(sys.argv[1]).resolve() / "ite184_study_game"
sys.path.insert(0, str(package))
import pygame
from ui.app import App
from version import APP_TITLE
actual_run = App.run
def run_once(self):
    assert self.state == "HOME"
    assert pygame.display.get_caption()[0] == APP_TITLE
    assert self.stats_store.path == package / "data" / "stats.json"
    assert self.stats_store.data["total_xp"] == 0
    self.render()
    self.present()
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    actual_run(self)
App.run = run_once
try:
    runpy.run_path(str(package / "pygame_main.py"), run_name="__main__")
except SystemExit as result:
    assert result.code == 0
assert json.loads((package / "data" / "stats.json").read_text())["version"] == 3
print("Clean standalone launch and missing-save initialization passed")
'''

PROFILE_PROBE = r'''
import json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from ite184_study_game.ui.app import App
from ite184_study_game.ui.session import QuizSession
from ite184_study_game.stats import StatsStore, create_default_stats, load_stats
from ite184_study_game.question_bank import get_question_by_id
import pygame
store = StatsStore()
assert store.data == create_default_stats()
class Clock:
    now = 1000.0
    def __call__(self): return self.now
clock = Clock()
app = App(stats_store=store, exam_clock=clock)
for mode in ("mcq", "written", "mixed"):
    app.selected_mode, app.selected_module, app.question_count = mode, None, 5
    app.start_quiz()
    for _ in range(len(app.session.questions)):
        question = app.session.current_question
        if question["type"] == "written":
            app.textbox.insert(question["model_answer"])
            app.dispatch(("submit_written", None))
        else:
            app.dispatch(("answer", next(k for k,v in app.session.choices.items() if v==question["answer"])))
        assert app.state == "FEEDBACK"
        app.render()
        app.dispatch(("next", None))
    assert app.state == "RESULTS"
question = get_question_by_id("M2_MCQ_001")
app.session = QuizSession(mode="mcq", stats_store=store, questions=[question])
app.state = "QUIZ"
wrong = next(k for k,v in app.session.choices.items() if v != question["answer"])
app.dispatch(("answer", wrong)); app.dispatch(("next", None))
assert question["id"] in store.data["mistake_ids"]
app.start_review()
app.dispatch(("answer", next(k for k,v in app.session.choices.items() if v==question["answer"])))
app.dispatch(("next", None))
assert question["id"] not in store.data["mistake_ids"]
app.dispatch(("exam", None)); app.dispatch(("exam_preset", None)); app.dispatch(("exam_start", None))
exam = app.exam.session
assert len(exam.questions) == 30 and exam.timer_duration == 2700
before = store.path.read_bytes()
index = next(i for i,q in enumerate(exam.questions) if q["type"] == "written")
app.exam.jump(index)
app.handle_event(pygame.event.Event(pygame.TEXTINPUT,text=exam.current_question["model_answer"]))
app.dispatch(("exam_flag", None)); app.dispatch(("exam_palette", None)); app.render()
assert store.path.read_bytes() == before
app.dispatch(("close_overlay", None)); app.dispatch(("exam_submit", None))
assert not exam.submitted
app.dispatch(("exam_confirm_submit", None)); app.render()
assert app.state == "EXAM_RESULTS" and store.data["exams"]["completed"] == 1
app.dispatch(("exam_review", None)); app.render()
assert app.state == "EXAM_REVIEW"
app.dispatch(("exam_again", None)); app.dispatch(("exam_start", None))
clock.now += 2701
app.render()
assert app.exam.session.auto_submitted and store.data["exams"]["completed"] == 2
app.dispatch(("home", None)); app.dispatch(("statistics", None)); app.render()
app.dispatch(("topics", None)); app.render()
app.state = "STATISTICS"; app.dispatch(("achievements", None)); app.render()
app.dispatch(("home", None)); app.dispatch(("about", None)); app.render()
app.go_back(); assert app.state == "HOME"
assert StatsStore().data == store.data
legacy = create_default_stats(); legacy["version"] = 2
legacy.pop("exams"); legacy.pop("exam_history")
legacy["total_xp"] = 245; legacy["mistake_ids"] = ["M2_WR_001"]
legacy["topics"] = {"Cybercrime": {"earned": 4,"possible": 5,"attempts": 1}}
old_path = store.path.parent / "old_profile.json"
old_path.write_text(json.dumps(legacy),encoding="utf-8")
migrated = load_stats(old_path)
assert migrated["version"] == 3
for key,value in legacy.items():
    if key != "version": assert migrated[key] == value, key
print("Fresh MCQ/Written/Mixed, mistakes/mastery, exams/timer/review, analytics, About, reopen and v2 migration passed")
pygame.quit()
'''


def check_clean_install(root=ROOT):
    """Copy runtime files to an owned temporary tree, then launch from another cwd."""
    root = Path(root).resolve()
    qa = root / ".qa"
    qa.mkdir(exist_ok=True)
    assert qa.resolve().is_relative_to(root)
    with tempfile.TemporaryDirectory(prefix="release-clean-", dir=qa) as temporary:
        target = Path(temporary).resolve()
        assert target.is_relative_to(qa.resolve())
        project = target / "project"
        outside = target / "unrelated-working-directory"
        outside.mkdir()
        for source in release_files(root, runtime_only=True):
            destination = project / source.relative_to(root)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        # Verify startup also creates the data directory itself when absent.
        data = project / "ite184_study_game" / "data"
        assert data.resolve().is_relative_to(project.resolve())
        if data.exists():
            shutil.rmtree(data)
        assert not (project / "screenshots").exists()
        assert not (project / "ite184_study_game" / "tests").exists()
        environment = {**os.environ, "SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy",
                       "PYGAME_HIDE_SUPPORT_PROMPT": "1", "PYTHONDONTWRITEBYTECODE": "1"}
        outputs = []
        for probe in (LAUNCH_PROBE, PROFILE_PROBE):
            result = subprocess.run([sys.executable, "-B", "-c", probe, str(project)], cwd=outside,
                                    env=environment, capture_output=True, text=True, timeout=30)
            if result.returncode:
                raise RuntimeError(result.stderr or result.stdout)
            outputs.append(result.stdout.strip())
        return outputs


def main():
    valid, errors = validate_question_bank()
    audit = audit_release()
    if not valid or audit["errors"]:
        print(json.dumps({"bank_errors": errors, **audit}, indent=2))
        return 1
    for line in check_clean_install():
        print(line)
    print(json.dumps({**audit, "questions": len(get_all_questions()), "bank_sha256": bank_digest()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
