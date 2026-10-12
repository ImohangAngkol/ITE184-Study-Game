"""Freeze the original pool for regression tests whose counts describe Phase 1–7.

This fixture preserves all original questions and assertions. Expanded-bank
tests run separately against the real expanded pool, without this patch.
"""

from copy import deepcopy
import json
from pathlib import Path
from unittest.mock import patch

from ite184_study_game import question_bank

STARTER_QUESTIONS = json.loads(
    (Path(__file__).parent / "fixtures" / "starter_questions.json").read_text(encoding="utf-8")
)


def use_starter_bank(test_case):
    bank_patch = patch.object(question_bank, "QUESTION_BANK", deepcopy(STARTER_QUESTIONS))
    bank_patch.start()
    test_case.addCleanup(bank_patch.stop)
