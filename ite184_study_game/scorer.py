"""Offline, deterministic written grading. No Pygame, network, or NLP needed."""

import re
import unicodedata


# Small phrase equivalences augment synonyms without changing the course bank.
# They remain whole phrases: a lone 'sharing' never satisfies consent reasoning.
PHRASE_ALIASES = {
    "consent to recording does not equal consent to distribution": [
        "consent to recording does not mean consent to distribution",
        "consent to recording does not mean consent to sharing",
        "consent to recording does not automatically mean consent to distribution",
        "recording consent is not distribution consent",
    ],
    "non retroactivity": ["nonretroactivity"],
    "no crime no punishment without law": ["no crime and no punishment without law"],
    "the law is harsh but it is the law": ["the law may be harsh but it is the law"],
}

FEEDBACK_LABELS = {
    5: "EXCELLENT", 4: "GREAT", 3: "PARTIALLY CORRECT",
    2: "NEEDS MORE DETAIL", 1: "RELATED IDEA", 0: "INCORRECT",
}


def normalize_answer(text: str) -> str:
    """Lowercase and separate punctuation while preserving letters and numbers."""
    text = unicodedata.normalize("NFKC", text).lower()
    # Also accept RA10175 and R.A. 10175 as the conventional 'ra 10175'.
    text = re.sub(r"\br\s*\.?\s*a\s*\.?\s*(?=\d)", "ra ", text)
    text = "".join(character if character.isalnum() else " " for character in text)
    return " ".join(text.split())


def _find_phrase(normalized_answer: str, phrases: list[str]) -> str | None:
    """Return one matching synonym, using complete token/phrase boundaries."""
    padded_answer = f" {normalized_answer} "
    for phrase in phrases:
        canonical = normalize_answer(phrase)
        alternatives = [canonical] + [normalize_answer(alias)
                                      for alias in PHRASE_ALIASES.get(canonical, [])]
        if any(alternative and f" {alternative} " in padded_answer
               for alternative in alternatives):
            return phrase
    return None


def match_keyword_group(answer: str, group: list[str]) -> bool:
    """One synonym is enough; multiple matches in a group count only once."""
    return _find_phrase(normalize_answer(answer), group) is not None


def calculate_written_score(required_matched: int, required_total: int,
                            optional_matched: int, optional_total: int) -> int:
    """Award 0-5 points using required coverage and an optional-detail bonus.

    Complete coverage earns 4, or 5 with optional detail. If no optional detail
    is defined, complete coverage earns 5. Half-or-more coverage earns 3;
    smaller nonzero coverage earns 2. Optional-only earns at most 1.
    """
    if required_total > 0 and required_matched == required_total:
        return 5 if optional_matched > 0 or optional_total == 0 else 4
    if required_total > 0 and required_matched / required_total >= 0.5:
        return 3
    if required_matched > 0:
        return 2
    return 1 if optional_matched > 0 else 0


def analyze_written_answer(question: dict, user_answer: str) -> dict:
    """Return points and concept-level feedback without changing either input."""
    normalized = normalize_answer(user_answer)
    matched, missed = [], []
    groups = question.get("keyword_groups", [])
    optional = question.get("optional_keywords", [])
    for index, group in enumerate(groups):
        phrase = _find_phrase(normalized, group)
        detail = {"index": index, "label": group[0]}
        if phrase is not None:
            detail["matched_phrase"] = phrase
            matched.append(detail)
        else:
            missed.append(detail)
    matched_optional = [phrase for phrase in optional if _find_phrase(normalized, [phrase])]
    score = calculate_written_score(len(matched), len(groups), len(matched_optional), len(optional))
    return {
        "score": score, "max_score": 5, "label": FEEDBACK_LABELS[score],
        "matched_groups": matched, "missed_groups": missed,
        "matched_optional": matched_optional,
        "missed_optional": [phrase for phrase in optional if phrase not in matched_optional],
        "normalized_answer": normalized, "percentage": score / 5 * 100,
    }
