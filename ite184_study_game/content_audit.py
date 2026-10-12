"""Read-only content quality checks; no quiz, save writes or network access.

Run: py -B -m ite184_study_game.content_audit
Near-text and excessive choice-set reuse are review warnings, not proof of
duplication. Sharing a topic is deliberately never a quality failure.
"""

from collections import Counter, defaultdict
from difflib import SequenceMatcher
import json
import re

if __package__:
    from .question_bank import get_all_questions, validate_question_bank
    from .scorer import normalize_answer, analyze_written_answer
else:
    from question_bank import get_all_questions, validate_question_bank
    from scorer import normalize_answer, analyze_written_answer


VALID_TOPICS = {
    1: {"Basic Concepts", "Ethical Theories", "Legal Maxims", "Professional Ethics", "Law vs Ethics"},
    2: {"Types of Computer Crime", "Sexually-Related Laws", "Cybercrime", "Hacking", "Malware",
        "Hacker Ethics", "Professional Constraints", "IT Laws", "Access Device Fraud", "Data Privacy",
        "Espionage", "Hacking Cases", "Malware Cases", "Supplemental Laws"},
}


def audit_question_bank(questions=None, choice_reuse_limit=8):
    """Return schema/content errors and review warnings for a supplied pool.

The optional pool supports audit regression tests without mutating globals.
Exact prompt/scenario duplicates and invalid models are errors. Similarity
uses wording rather than shared topics and is only a human-review signal.
"""
    if questions is None:
        questions = get_all_questions()
        _, schema_errors = validate_question_bank()
    else:
        schema_errors = []
    errors = list(schema_errors)
    warnings = []
    prompts = defaultdict(list)
    choice_sets = defaultdict(list)
    ids = Counter()
    texts = []
    written_count = 0
    for index, question in enumerate(questions):
        if not isinstance(question, dict):
            errors.append(f"Entry {index}: not a question dictionary.")
            continue
        question_id = question.get("id", f"entry {index}")
        if not isinstance(question_id, str):
            errors.append(f"Entry {index}: invalid ID.")
            continue
        ids[question_id] += 1
        if not re.fullmatch(r"M[12]_(?:MCQ|WR)_\d{3}", question_id):
            errors.append(f"{question_id}: ID does not follow the permanent-ID pattern.")
        else:
            expected_type = "mcq" if "_MCQ_" in question_id else "written"
            if question.get("module") != int(question_id[1]) or question.get("type") != expected_type:
                errors.append(f"{question_id}: ID/module/type mismatch.")
        if question.get("topic") not in VALID_TOPICS.get(question.get("module"), set()):
            errors.append(f"{question_id}: noncanonical topic.")
        field = "scenario" if question.get("type") == "written" else "question"
        prompt = question.get(field)
        if not isinstance(prompt, str) or not prompt.strip():
            errors.append(f"{question_id}: missing prompt/scenario.")
        else:
            normalized = normalize_answer(prompt)
            prompts[normalized].append(question_id)
            texts.append((question_id, normalized))
        if question.get("type") == "mcq":
            choices = question.get("choices")
            if (not isinstance(choices, list) or len(choices) != 4
                    or not all(isinstance(c, str) and c.strip() for c in choices)):
                errors.append(f"{question_id}: malformed four-choice set.")
            else:
                normalized_choices = tuple(sorted(normalize_answer(c) for c in choices))
                if len(set(normalized_choices)) != 4:
                    errors.append(f"{question_id}: duplicate choices.")
                if question.get("answer") not in choices:
                    errors.append(f"{question_id}: answer missing from choices.")
                choice_sets[normalized_choices].append(question_id)
        elif question.get("type") == "written":
            written_count += 1
            groups = question.get("keyword_groups")
            valid_groups = (isinstance(groups, list) and bool(groups)
                            and all(isinstance(g, list) and bool(g)
                                    and all(isinstance(p, str) and p.strip() for p in g) for g in groups))
            if not valid_groups:
                errors.append(f"{question_id}: malformed keyword groups.")
                continue
            seen_phrases = {}
            for group_index, group in enumerate(groups):
                for phrase in group:
                    key = normalize_answer(phrase)
                    if not key:
                        errors.append(f"{question_id}: empty normalized keyword.")
                    elif key in seen_phrases and seen_phrases[key] != group_index:
                        errors.append(f"{question_id}: same synonym appears in different concept groups ({phrase}).")
                    seen_phrases[key] = group_index
            optional = question.get("optional_keywords")
            model = question.get("model_answer")
            if (not isinstance(model, str) or not model.strip() or not isinstance(optional, list)
                    or not all(isinstance(p, str) and p.strip() for p in optional)):
                errors.append(f"{question_id}: missing model or malformed optional keywords.")
                continue
            grade = analyze_written_answer(question, model)
            if grade["missed_groups"]:
                missed = ", ".join(g["label"] for g in grade["missed_groups"])
                errors.append(f"{question_id}: model misses required concepts: {missed}.")
    for question_id, count in ids.items():
        if count > 1:
            errors.append(f"Duplicate ID: {question_id} ({count} occurrences).")
    for matching_ids in prompts.values():
        if len(matching_ids) > 1:
            errors.append("Duplicate prompt/scenario: " + ", ".join(matching_ids))
    reused = [matching_ids for matching_ids in choice_sets.values() if len(matching_ids) > choice_reuse_limit]
    for matching_ids in reused:
        warnings.append("Excessive identical choice-set reuse: " + ", ".join(matching_ids))
    similar = []
    for index, (first_id, first) in enumerate(texts):
        for second_id, second in texts[index + 1:]:
            if first == second or min(len(first), len(second)) < 40:
                continue
            # Fast length/token screens before the more expensive text ratio.
            if min(len(first), len(second)) / max(len(first), len(second)) < 0.8:
                continue
            first_words, second_words = set(first.split()), set(second.split())
            if len(first_words & second_words) / len(first_words | second_words) < 0.68:
                continue
            similarity = SequenceMatcher(None, first, second).ratio()
            if similarity >= 0.86:
                similar.append({"ids": [first_id, second_id], "similarity": round(similarity, 3)})
                warnings.append(f"Review similar wording: {first_id}, {second_id} ({similarity:.1%}).")
    return {"errors": errors, "warnings": warnings, "near_duplicates": similar,
            "questions": len(questions), "written_models_checked": written_count,
            "maximum_choice_set_reuse": max((len(v) for v in choice_sets.values()), default=0)}


def main():
    report = audit_question_bank()
    print(json.dumps(report, indent=2))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
