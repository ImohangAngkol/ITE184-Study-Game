"""Small schema builders for explicitly authored, permanently numbered questions.

Pipes separate choices; semicolons separate synonyms within a concept group.
IDs, difficulty and content are authored, never inferred from list positions.
The frontend still receives ordinary independent question dictionaries.
"""


def mcq(question_id, difficulty, topic, subtopic, prompt, choices, explanation):
    options = choices.split("|")
    return {
        "id": question_id, "module": int(question_id[1]), "type": "mcq",
        "difficulty": difficulty, "topic": topic, "subtopic": subtopic,
        "question": prompt, "choices": options, "answer": options[0],
        "keywords": [subtopic], "explanation": explanation,
    }


def written(question_id, difficulty, topic, subtopic, scenario, concepts,
            model, explanation, optional=""):
    return {
        "id": question_id, "module": int(question_id[1]), "type": "written",
        "difficulty": difficulty, "topic": topic, "subtopic": subtopic,
        "scenario": scenario,
        "keyword_groups": [[phrase.strip() for phrase in group.split(";")]
                           for group in concepts],
        "optional_keywords": [phrase.strip() for phrase in optional.split(";") if phrase.strip()],
        "model_answer": model, "explanation": explanation,
    }
