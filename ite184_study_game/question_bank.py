"""ITE184 course question data, filters, validation, and a developer preview.

Run this file to inspect the bank. Importing it never starts a quiz.
Phase 8 extends the original 26 questions without changing their IDs/content.
"""

from copy import deepcopy
from pprint import pprint
from typing import Any


# Each dictionary mixes strings, numbers, and lists, so values use Any.
Question = dict[str, Any]
VALID_MODULES = (1, 2)
VALID_TYPES = ("mcq", "written")
VALID_DIFFICULTIES = ("easy", "medium", "hard")


QUESTION_BANK: list[Question] = [
    # MODULE 1: six multiple-choice questions.
    {
        "id": "M1_MCQ_001",
        "module": 1,
        "type": "mcq",
        "difficulty": "easy",
        "topic": "Basic Concepts",
        "subtopic": "Ethics and Law",
        "question": (
            "Which field studies morally right and wrong behavior and asks 'What should I do?'?"
        ),
        "choices": ["Ethics", "Law", "Computer Ethics", "Professional Ethics"],
        "answer": "Ethics",
        "keywords": ["morally right and wrong", "should"],
        "explanation": (
            "Ethics studies moral behavior generally. Law concerns government-enforced rules. "
            "Computer ethics applies moral questions to computing; professional ethics concerns"
            " professional responsibilities."
        ),
    },
    {
        "id": "M1_MCQ_002",
        "module": 1,
        "type": "mcq",
        "difficulty": "easy",
        "topic": "Ethical Theories",
        "subtopic": "Utilitarianism vs Consequentialism",
        "question": (
            "Which theory specifically seeks the greatest overall good, rather than referring "
            "to consequences in general?"
        ),
        "choices": ["Consequentialism", "Utilitarianism", "Deontology", "Virtue Ethics"],
        "answer": "Utilitarianism",
        "keywords": ["greatest overall good", "overall benefit"],
        "explanation": (
            "Utilitarianism is a consequentialist theory focused on overall welfare. "
            "Consequentialism is the broader family of theories that evaluates actions by their"
            " outcomes."
        ),
    },
    {
        "id": "M1_MCQ_003",
        "module": 1,
        "type": "mcq",
        "difficulty": "easy",
        "topic": "Ethical Theories",
        "subtopic": "Deontology",
        "question": (
            "Which ethical theory emphasizes moral duties and obligations rather than judging "
            "only by results?"
        ),
        "choices": ["Utilitarianism", "Cultural Relativism", "Deontology", "Consequentialism"],
        "answer": "Deontology",
        "keywords": ["duty", "obligation"],
        "explanation": (
            "Deontology emphasizes duties and obligations. Cultural relativism relates moral "
            "judgments to cultural standards; consequentialism emphasizes outcomes."
        ),
    },
    {
        "id": "M1_MCQ_004",
        "module": 1,
        "type": "mcq",
        "difficulty": "hard",
        "topic": "Ethical Theories",
        "subtopic": "Kantianism",
        "question": (
            "A company could profit by deceiving users. An engineer rejects the plan because "
            "its rule cannot be universalized and it treats people merely as tools. Which "
            "theory most specifically fits?"
        ),
        "choices": ["Contractarianism", "Kantianism", "Utilitarianism", "Divine Command Theory"],
        "answer": "Kantianism",
        "keywords": ["universal rule", "ends not merely means", "respect persons"],
        "explanation": (
            "Kantianism is a duty-based approach that tests universal rules and respects "
            "persons as ends. Divine command theory instead grounds morality in God's commands."
        ),
    },
    {
        "id": "M1_MCQ_005",
        "module": 1,
        "type": "mcq",
        "difficulty": "medium",
        "topic": "Ethical Theories",
        "subtopic": "Virtue Ethics",
        "question": (
            "A developer asks what an honest, courageous, and responsible person would do when "
            "a defect is discovered. Which theory guides this question?"
        ),
        "choices": ["Virtue Ethics", "Deontology", "Contractarianism", "Cultural Relativism"],
        "answer": "Virtue Ethics",
        "keywords": ["character", "honesty", "responsibility"],
        "explanation": (
            "Virtue ethics emphasizes good character and virtues such as honesty and courage, "
            "rather than only duties, agreements, or local cultural approval."
        ),
    },
    {
        "id": "M1_MCQ_006",
        "module": 1,
        "type": "mcq",
        "difficulty": "medium",
        "topic": "Ethical Theories",
        "subtopic": "Contractarianism",
        "question": (
            "An IT team justifies its rules as terms rational people would mutually accept to "
            "cooperate fairly. Which ethical theory fits?"
        ),
        "choices": ["Divine Command Theory", "Cultural Relativism", "Virtue Ethics", "Contractarianism"],
        "answer": "Contractarianism",
        "keywords": ["agreement", "cooperation", "mutually acceptable rules"],
        "explanation": (
            "Contractarianism emphasizes mutually acceptable agreements. Divine command theory "
            "appeals to God; cultural relativism appeals to a culture's moral standards; virtue"
            " ethics emphasizes character."
        ),
    },
    # MODULE 1: four written/scenario questions.
    {
        "id": "M1_WR_001",
        "module": 1,
        "type": "written",
        "difficulty": "easy",
        "topic": "Legal Maxims",
        "subtopic": "Ignorance of the Law",
        "scenario": (
            "A student says, 'I did not know hacking was illegal, so I should be excused.' "
            "Identify the legal maxim and explain its meaning."
        ),
        "keyword_groups": [
            ["ignorantia legis neminem excusat", "ignorantia legis"],
            ["ignorance of the law excuses no one", "ignorance is no excuse", "not knowing the law is no excuse"],
        ],
        "optional_keywords": ["legal responsibility", "ignorance"],
        "model_answer": (
            "Ignorantia legis neminem excusat: ignorance of the law excuses no one. Merely not "
            "knowing the applicable law does not excuse its violation."
        ),
        "explanation": (
            "This maxim addresses ignorance of an existing law. It differs from the requirement"
            " that a criminal law exist when conduct occurs."
        ),
    },
    {
        "id": "M1_WR_002",
        "module": 1,
        "type": "written",
        "difficulty": "medium",
        "topic": "Legal Maxims",
        "subtopic": "No Crime Without Law",
        "scenario": (
            "Conduct was not criminal under any applicable law when committed. A new law later "
            "criminalizes it, and prosecutors propose applying the new offense backward. "
            "Identify the relevant maxim and principle."
        ),
        "keyword_groups": [
            ["nullum crimen nulla poena sine lege", "nullum crimen", "nulla poena sine lege"],
            ["no crime no punishment without law", "no crime without law", "non retroactivity", "cannot apply retroactively"],
        ],
        "optional_keywords": ["law existed", "legal gap", "iloveyou"],
        "model_answer": (
            "Nullum crimen, nulla poena sine lege means no crime and no punishment without law."
            " A newly created offense cannot retroactively criminalize conduct that was not an "
            "offense when committed."
        ),
        "explanation": (
            "The maxim concerns legality and the prohibition of retroactive criminalization. "
            "The ILOVEYOU incident is a course example of a legal-gap discussion; the maxim "
            "does not excuse conduct already criminal under another applicable law."
        ),
    },
    {
        "id": "M1_WR_003",
        "module": 1,
        "type": "written",
        "difficulty": "medium",
        "topic": "Legal Maxims",
        "subtopic": "Harshness of the Law",
        "scenario": (
            "Someone admits that a valid law applies but argues, 'The law is too harsh, so it "
            "should simply be ignored.' Identify the legal maxim and explain it."
        ),
        "keyword_groups": [
            ["dura lex sed lex", "dura lex"],
            ["the law is harsh but it is the law", "harsh but still the law", "harshness does not remove applicability"],
        ],
        "optional_keywords": ["law reform", "applicable law"],
        "model_answer": (
            "Dura lex, sed lex: the law may be harsh, but it is the law. Harshness alone does "
            "not remove the applicability of a valid law."
        ),
        "explanation": (
            "This maxim concerns an applicable law's perceived severity. It does not forbid "
            "lawful challenges to a law or efforts to reform it."
        ),
    },
    {
        "id": "M1_WR_004",
        "module": 1,
        "type": "written",
        "difficulty": "hard",
        "topic": "Professional Ethics",
        "subtopic": "Authorization and Responsible Disclosure",
        "scenario": (
            "A developer notices a flaw that could reveal private customer records. They can "
            "exploit it but have no permission to test that system. Describe the responsible "
            "professional response, including authorization, disclosure, and protection of "
            "users."
        ),
        "keyword_groups": [
            ["obtain authorization", "written permission", "technical ability does not equal permission", "do not exploit without permission"],
            ["responsible disclosure", "report privately", "report the vulnerability privately"],
            ["protect privacy", "maintain confidentiality", "avoid harm", "protect customer records"],
        ],
        "optional_keywords": ["honesty", "scope", "secure systems"],
        "model_answer": (
            "Obtain authorization before testing. Report the vulnerability privately through "
            "responsible disclosure, maintain confidentiality, and avoid harm to customers. "
            "Technical ability does not equal permission."
        ),
        "explanation": (
            "Professional ethics requires permission, privacy, confidentiality, and care for "
            "others. Curiosity or good intentions alone do not authorize access to private "
            "data."
        ),
    },
    # MODULE 2: ten multiple-choice questions.
    {
        "id": "M2_MCQ_001",
        "module": 2,
        "type": "mcq",
        "difficulty": "easy",
        "topic": "Cybercrime",
        "subtopic": "Illegal Access",
        "question": (
            "Under RA 10175, which offense focuses on accessing all or part of a computer "
            "system without right?"
        ),
        "choices": ["Illegal Access", "Illegal Interception", "Data Interference", "System Interference"],
        "answer": "Illegal Access",
        "keywords": ["enter", "access without right", "ra 10175"],
        "explanation": (
            "Illegal Access concerns entry without right. Altering data or disrupting the "
            "system is not required for this offense."
        ),
    },
    {
        "id": "M2_MCQ_002",
        "module": 2,
        "type": "mcq",
        "difficulty": "medium",
        "topic": "Cybercrime",
        "subtopic": "Illegal Interception",
        "question": (
            "An attacker secretly captures non-public login credentials during network "
            "transmission without right but never logs in. Which RA 10175 offense most directly"
            " fits?"
        ),
        "choices": ["Illegal Access", "Illegal Interception", "Data Interference", "System Interference"],
        "answer": "Illegal Interception",
        "keywords": ["capture", "during transmission", "non public data"],
        "explanation": (
            "Illegal Interception concerns capturing non-public computer data in transmission "
            "by technical means without right. Capturing transmitted data differs from logging "
            "into a system."
        ),
    },
    {
        "id": "M2_MCQ_003",
        "module": 2,
        "type": "mcq",
        "difficulty": "medium",
        "topic": "Cybercrime",
        "subtopic": "Data Interference",
        "question": (
            "Someone intentionally deletes a school's grade records without right while its "
            "server continues operating. Which RA 10175 offense specifically describes the "
            "deletion?"
        ),
        "choices": ["System Interference", "Illegal Interception", "Misuse of Devices", "Data Interference"],
        "answer": "Data Interference",
        "keywords": ["change data", "delete data", "without right"],
        "explanation": (
            "Data Interference includes intentionally or recklessly altering, damaging, or "
            "deleting data without right. The focus here is changed data rather than disrupted "
            "system operation."
        ),
    },
    {
        "id": "M2_MCQ_004",
        "module": 2,
        "type": "mcq",
        "difficulty": "medium",
        "topic": "Cybercrime",
        "subtopic": "System Interference",
        "question": (
            "An attacker floods a server without authority until legitimate users cannot use "
            "it. Which RA 10175 offense best describes the disruption?"
        ),
        "choices": ["Illegal Access", "Data Interference", "System Interference", "Illegal Interception"],
        "answer": "System Interference",
        "keywords": ["disrupt system", "ddos", "availability"],
        "explanation": (
            "System Interference concerns hindering or interfering with computer or network "
            "functioning without right or authority. A denial-of-service attack targets "
            "availability."
        ),
    },
    {
        "id": "M2_MCQ_005",
        "module": 2,
        "type": "mcq",
        "difficulty": "hard",
        "topic": "Cybercrime",
        "subtopic": "Misuse of Devices",
        "question": (
            "A programmer claims to be a researcher but produces, without right, software "
            "designed primarily to steal passwords for cybercrime and supplies it to offenders."
            " Which RA 10175 offense most directly concerns producing this tool?"
        ),
        "choices": ["Misuse of Devices", "Illegal Interception", "System Interference", "Data Interference"],
        "answer": "Misuse of Devices",
        "keywords": ["tool", "password", "designed for cybercrime", "without right"],
        "explanation": (
            "Misuse of Devices includes producing without right a program designed or adapted "
            "primarily for offenses under the Act. A tool's criminal purpose matters; "
            "possession of an ordinary legitimate security tool alone is not this scenario."
        ),
    },
    {
        "id": "M2_MCQ_006",
        "module": 2,
        "type": "mcq",
        "difficulty": "medium",
        "topic": "Sexually-Related Laws",
        "subtopic": "Safe Spaces Act",
        "question": (
            "An adult receives repeated unwanted sexual messages and gender-based "
            "cyberstalking. No intimate recording is involved. Which law specifically addresses"
            " gender-based online sexual harassment?"
        ),
        "choices": ["RA 9995", "RA 11313", "RA 11930", "RA 8484"],
        "answer": "RA 11313",
        "keywords": ["safe spaces act", "gender based online sexual harassment", "cyberstalking"],
        "explanation": (
            "RA 11313, the Safe Spaces Act, addresses gender-based online sexual harassment, "
            "including relevant unwanted sexual remarks, threats, and cyberstalking."
        ),
    },
    {
        "id": "M2_MCQ_007",
        "module": 2,
        "type": "mcq",
        "difficulty": "easy",
        "topic": "Sexually-Related Laws",
        "subtopic": "OSAEC and CSAEM",
        "question": (
            "Which law addresses online sexual abuse or exploitation of children and child "
            "sexual abuse or exploitation materials, and repealed RA 9775?"
        ),
        "choices": ["RA 8792", "RA 9995", "RA 11930", "RA 11313"],
        "answer": "RA 11930",
        "keywords": ["osaec", "csaem", "child exploitation"],
        "explanation": (
            "RA 11930 addresses OSAEC and CSAEM, including online child exploitation. It "
            "repealed RA 9775, the older Anti-Child Pornography Act."
        ),
    },
    {
        "id": "M2_MCQ_008",
        "module": 2,
        "type": "mcq",
        "difficulty": "medium",
        "topic": "IT Laws",
        "subtopic": "Electronic Commerce Act",
        "question": (
            "Which law recognizes electronic documents and transactions, supports electronic "
            "commerce, and contains an early Philippine hacking/cracking provision?"
        ),
        "choices": ["RA 10173", "RA 8484", "RA 11313", "RA 8792"],
        "answer": "RA 8792",
        "keywords": ["electronic commerce act", "electronic documents", "electronic transactions"],
        "explanation": (
            "RA 8792 is the Electronic Commerce Act. Its substance includes recognition of "
            "electronic documents and transactions and an early hacking/cracking provision. No "
            "State Policy section number is tested."
        ),
    },
    {
        "id": "M2_MCQ_009",
        "module": 2,
        "type": "mcq",
        "difficulty": "easy",
        "topic": "Access Device Fraud",
        "subtopic": "Access Devices Regulation Act",
        "question": (
            "Which law is the Access Devices Regulation Act, associated with cards, account "
            "numbers, and PINs, and later amended by RA 11449?"
        ),
        "choices": ["RA 8484", "RA 10173", "RA 9995", "RA 8792"],
        "answer": "RA 8484",
        "keywords": ["card", "account", "pin", "access device"],
        "explanation": (
            "RA 8484 regulates access devices and access-device fraud. RA 11449 amended it with"
            " additional prohibitions and increased penalties."
        ),
    },
    {
        "id": "M2_MCQ_010",
        "module": 2,
        "type": "mcq",
        "difficulty": "easy",
        "topic": "Malware",
        "subtopic": "Worm vs Virus",
        "question": (
            "Which malicious program is standalone, self-replicates, and can spread across "
            "networks without attaching itself to a host file?"
        ),
        "choices": ["Virus", "Trojan Horse", "Worm", "Logic Bomb"],
        "answer": "Worm",
        "keywords": ["standalone", "self replicating", "network spread"],
        "explanation": (
            "A worm is standalone and self-replicating. A virus attaches to a host; a Trojan "
            "disguises malicious functionality as something legitimate; a logic bomb activates "
            "when a condition is met."
        ),
    },
    # MODULE 2: six written/scenario questions.
    {
        "id": "M2_WR_001",
        "module": 2,
        "type": "written",
        "difficulty": "easy",
        "topic": "Cybercrime",
        "subtopic": "Illegal Access",
        "scenario": (
            "A student obtains a professor's password and logs into the grading system without "
            "permission but changes nothing. Identify the law, offense, and reason it may "
            "apply."
        ),
        "keyword_groups": [
            ["ra 10175", "cybercrime prevention act"],
            ["illegal access", "access without right", "unauthorized access"],
        ],
        "optional_keywords": ["without permission", "no changes required", "password"],
        "model_answer": (
            "The act may constitute Illegal Access under RA 10175 because the student accessed "
            "a computer system without right. No alteration of data is required."
        ),
        "explanation": (
            "The relevant distinction is entering without right versus changing data. Merely "
            "viewing information does not create authorization."
        ),
    },
    {
        "id": "M2_WR_002",
        "module": 2,
        "type": "written",
        "difficulty": "hard",
        "topic": "Cybercrime",
        "subtopic": "Illegal Access and Data Interference",
        "scenario": (
            "A student uses a stolen password to enter the registrar's system without "
            "permission and changes a grade from 72 to 92. The server remains available. "
            "Identify the law and both offenses, and distinguish the two actions."
        ),
        "keyword_groups": [
            ["ra 10175", "cybercrime prevention act"],
            ["illegal access", "access without right", "unauthorized access"],
            ["data interference", "altering data", "changing data"],
            ["entry and alteration", "entered without permission and changed the grade", "unauthorized entry and data modification"],
        ],
        "optional_keywords": ["integrity", "grade", "system remains available"],
        "model_answer": (
            "RA 10175 may apply to Illegal Access and Data Interference: unauthorized entry and"
            " data modification are distinct actions. Entering without right is Illegal Access;"
            " changing the grade without right is Data Interference."
        ),
        "explanation": (
            "An incident can include more than one offense. Data modification is the "
            "interference described here; server availability alone does not make that "
            "modification authorized."
        ),
    },
    {
        "id": "M2_WR_003",
        "module": 2,
        "type": "written",
        "difficulty": "medium",
        "topic": "Sexually-Related Laws",
        "subtopic": "Recording vs Distribution Consent",
        "scenario": (
            "Two adults consent to recording an intimate video in private. After their breakup,"
            " one publishes it without the other's written consent. Identify the relevant law "
            "and explain why permission to record is insufficient."
        ),
        "keyword_groups": [
            ["ra 9995", "anti photo and video voyeurism act", "anti photo video voyeurism act"],
            ["consent to recording does not equal consent to distribution", "separate consent to distribute", "no written consent to publish"],
        ],
        "optional_keywords": ["intimate video", "privacy", "without consent"],
        "model_answer": (
            "RA 9995, the Anti-Photo and Video Voyeurism Act, is relevant. Consent to recording"
            " does not equal consent to distribution; publishing the intimate video without the"
            " required written consent is a separate issue."
        ),
        "explanation": (
            "RA 9995 distinguishes permission for recording from permission for copying, "
            "distribution, or publication. Recording consent does not automatically permit "
            "sharing."
        ),
    },
    {
        "id": "M2_WR_004",
        "module": 2,
        "type": "written",
        "difficulty": "hard",
        "topic": "Access Device Fraud",
        "subtopic": "49 vs 50 Cards",
        "scenario": (
            "An offender fraudulently skims 50 payment cards without hacking a bank system. "
            "Compare this with an otherwise identical case involving 49 cards and no other "
            "economic-sabotage circumstance. Identify the amendment and explain the threshold; "
            "is 49 automatically lawful?"
        ),
        "keyword_groups": [
            ["ra 11449", "amendment to ra 8484"],
            ["economic sabotage"],
            ["50 or more", "fifty or more", "50 card threshold"],
            ["49 is still unlawful", "49 can still be access device fraud", "below threshold does not mean legal"],
        ],
        "optional_keywords": ["skimming", "bank hacking", "payment cards"],
        "model_answer": (
            "RA 11449 amends RA 8484. Skimming 50 or more payment cards meets the stated "
            "economic sabotage circumstance. Below threshold does not mean legal: 49 can still "
            "be access device fraud. Bank-system hacking is a separate economic-sabotage "
            "circumstance."
        ),
        "explanation": (
            "The 50-card threshold is one route to economic sabotage, not a minimum for all "
            "access-device offenses. The comparison excludes other economic-sabotage "
            "circumstances so the card count is the distinguishing fact."
        ),
    },
    {
        "id": "M2_WR_005",
        "module": 2,
        "type": "written",
        "difficulty": "hard",
        "topic": "Espionage",
        "subtopic": "Corporate Espionage and Scope",
        "scenario": (
            "An employee can use the normal company network but bypasses restrictions "
            "protecting a confidential R&D repository and sells source code to a competitor. "
            "They argue their staff account authorized everything. Classify the espionage, "
            "identify a possible cybercrime law and offense, and explain the authorization "
            "issue."
        ),
        "keyword_groups": [
            ["industrial espionage", "corporate espionage"],
            ["ra 10175", "cybercrime prevention act"],
            ["illegal access", "access without right", "unauthorized access"],
            ["exceeds scope of authorization", "scope of authorization", "network access is not repository permission"],
        ],
        "optional_keywords": ["confidential", "trade secrets", "nda", "source code"],
        "model_answer": (
            "This is industrial/corporate espionage involving confidential source code. Illegal"
            " Access under RA 10175 may apply because the employee exceeds scope of "
            "authorization: normal network access does not grant permission to the restricted "
            "repository."
        ),
        "explanation": (
            "Espionage classifies the purpose and information involved. A possible Illegal "
            "Access offense concerns how that information was obtained. Corporate espionage "
            "concerns business secrets; government and military espionage concern government "
            "and national-defense information respectively."
        ),
    },
    {
        "id": "M2_WR_006",
        "module": 2,
        "type": "written",
        "difficulty": "hard",
        "topic": "Data Privacy",
        "subtopic": "Multiple Applicable Laws",
        "scenario": (
            "An outsider enters a school database without right, copies students' personal "
            "records, and publicly discloses them without a lawful basis. No data is altered. "
            "Identify the law and offense concerning entry and the additional law relevant to "
            "the personal-information disclosure."
        ),
        "keyword_groups": [
            ["ra 10175", "cybercrime prevention act"],
            ["illegal access", "access without right", "unauthorized access"],
            ["ra 10173", "data privacy act"],
            ["unauthorized disclosure", "disclosure without lawful basis", "unlawful disclosure of personal information"],
        ],
        "optional_keywords": ["personal information", "multiple laws", "confidentiality"],
        "model_answer": (
            "Illegal Access under RA 10175 concerns the entry without right. RA 10173, the Data"
            " Privacy Act, may also apply to the unauthorized disclosure of students' personal "
            "information. One incident can involve multiple laws."
        ),
        "explanation": (
            "Cybercrime and data-privacy issues can overlap. Illegal entry is distinct from "
            "unlawful personal-information disclosure; changing data is not required for either"
            " issue described here."
        ),
    },
]


# Keep the starter dictionaries above intact for existing progress/history.
# Explicit IDs in the content modules are permanent, independent of ordering.
if __package__:
    from .questions import module1, module2_crimes, module2_laws, module2_malware, module2_cases, module2_ethics
else:  # Also support: py ite184_study_game/question_bank.py
    from questions import module1, module2_crimes, module2_laws, module2_malware, module2_cases, module2_ethics

for content in (module1, module2_crimes, module2_laws, module2_malware, module2_cases, module2_ethics):
    QUESTION_BANK.extend(content.QUESTIONS)


def get_all_questions() -> list[Question]:
    """Return copies of every question, including their nested lists."""
    # Later choice shuffling must not modify the original stored questions.
    return deepcopy(QUESTION_BANK)


def get_questions_by_module(module: int) -> list[Question]:
    """Return questions for module 1 or 2; invalid modules return []."""
    return filter_questions(module=module)


def get_questions_by_type(question_type: str) -> list[Question]:
    """Return mcq or written questions using the combined filter."""
    return filter_questions(question_type=question_type)


def get_questions_by_difficulty(difficulty: str) -> list[Question]:
    """Return easy, medium, or hard questions using the combined filter."""
    return filter_questions(difficulty=difficulty)


def filter_questions(
    module: int | None = None,
    question_type: str | None = None,
    difficulty: str | None = None,
    topic: str | None = None,
) -> list[Question]:
    """Combine exact, case-sensitive filters; None leaves a field unrestricted.

    All supplied filters must match. With no filters, return the whole bank.
    Results are copies so callers can safely shuffle choices in later phases.
    """
    if module is not None and (type(module) is not int or module not in VALID_MODULES):
        return []
    matches = [
        question
        for question in QUESTION_BANK
        if (module is None or question["module"] == module)
        and (question_type is None or question["type"] == question_type)
        and (difficulty is None or question["difficulty"] == difficulty)
        and (topic is None or question["topic"] == topic)
    ]
    return deepcopy(matches)


def get_question_by_id(question_id: str) -> Question | None:
    """Return a copy of the question with this stable ID, or None."""
    for question in QUESTION_BANK:
        if question["id"] == question_id:
            return deepcopy(question)
    return None


def _is_nonempty_text(value: Any) -> bool:
    """Check the type before calling strip(), which only strings provide."""
    return isinstance(value, str) and bool(value.strip())


def _is_text_list(value: Any, allow_empty: bool = True) -> bool:
    """Check that a value is a list containing only nonblank strings."""
    return (
        isinstance(value, list)
        and (allow_empty or bool(value))
        and all(_is_nonempty_text(item) for item in value)
    )


def validate_question_bank() -> tuple[bool, list[str]]:
    """Collect all schema errors without crashing on malformed questions."""
    errors: list[str] = []
    seen_ids: set[str] = set()
    if not isinstance(QUESTION_BANK, list):
        return False, ["QUESTION_BANK must be a list."]

    for index, question in enumerate(QUESTION_BANK, start=1):
        label = f"Question {index}"
        if not isinstance(question, dict):
            errors.append(f"{label}: must be a dictionary.")
            continue

        question_id = question.get("id")
        if not _is_nonempty_text(question_id):
            errors.append(f"{label}: id must be a nonblank string.")
        else:
            label += f" ({question_id})"
            if question_id in seen_ids:
                errors.append(f"{label}: duplicate id.")
            seen_ids.add(question_id)

        # bool is a subclass of int in Python; reject True as module 1.
        module = question.get("module")
        if type(module) is not int or module not in VALID_MODULES:
            errors.append(f"{label}: module must be the integer 1 or 2.")
        if question.get("difficulty") not in VALID_DIFFICULTIES:
            errors.append(f"{label}: difficulty must be easy, medium, or hard.")
        for field in ("topic", "subtopic", "explanation"):
            if not _is_nonempty_text(question.get(field)):
                errors.append(f"{label}: {field} must be a nonblank string.")

        question_type = question.get("type")
        if question_type not in VALID_TYPES:
            errors.append(f"{label}: type must be mcq or written.")
        elif question_type == "mcq":
            if not _is_nonempty_text(question.get("question")):
                errors.append(f"{label}: question must be a nonblank string.")
            choices = question.get("choices")
            if not isinstance(choices, list):
                errors.append(f"{label}: choices must be a list.")
            else:
                if len(choices) != 4:
                    errors.append(f"{label}: choices must contain exactly 4 items.")
                if not _is_text_list(choices, allow_empty=False):
                    errors.append(f"{label}: every choice must be a nonblank string.")
                else:
                    normalized_choices = [choice.strip().casefold() for choice in choices]
                    if len(set(normalized_choices)) != len(choices):
                        errors.append(f"{label}: choices must be unique, ignoring case and outside spaces.")
            answer = question.get("answer")
            if not _is_nonempty_text(answer):
                errors.append(f"{label}: answer must be a nonblank string.")
            if not isinstance(choices, list) or answer not in choices:
                errors.append(f"{label}: answer must match a choice exactly.")
            if not _is_text_list(question.get("keywords")):
                errors.append(f"{label}: keywords must be a list of nonblank strings.")
        elif question_type == "written":
            for field in ("scenario", "model_answer"):
                if not _is_nonempty_text(question.get(field)):
                    errors.append(f"{label}: {field} must be a nonblank string.")
            groups = question.get("keyword_groups")
            if not isinstance(groups, list) or not groups:
                errors.append(f"{label}: keyword_groups must be a nonempty list.")
            else:
                for group_index, group in enumerate(groups, start=1):
                    if not _is_text_list(group, allow_empty=False):
                        errors.append(f"{label}: keyword group {group_index} must be a nonempty list of nonblank strings.")
            if not _is_text_list(question.get("optional_keywords")):
                errors.append(f"{label}: optional_keywords must be a list of nonblank strings.")

    return not errors, errors


def get_question_bank_summary() -> dict[str, Any]:
    """Count questions by module, type, difficulty, and topic in a valid bank."""
    summary: dict[str, Any] = {
        "total": len(QUESTION_BANK),
        "module_1": 0,
        "module_2": 0,
        "mcq": 0,
        "written": 0,
        "easy": 0,
        "medium": 0,
        "hard": 0,
        "topics": {},
    }
    for question in QUESTION_BANK:
        summary[f"module_{question['module']}"] += 1
        summary[question["type"]] += 1
        summary[question["difficulty"]] += 1
        topic = question["topic"]
        summary["topics"][topic] = summary["topics"].get(topic, 0) + 1
    return summary


def _run_developer_preview() -> None:
    """Validate first, then display counts and three filter examples."""
    valid, errors = validate_question_bank()
    if not valid:
        print("Question bank validation FAILED")
        for error in errors:
            print(f"- {error}")
        # Do not summarize/filter malformed data after validation fails.
        raise SystemExit(1)

    print("Question bank validation PASSED")

    if __package__:
        from .content_audit import audit_question_bank
    else:
        from content_audit import audit_question_bank
    audit = audit_question_bank(QUESTION_BANK)
    print(f"Content audit: {len(audit['errors'])} errors, {len(audit['warnings'])} review warnings")
    for issue in audit["errors"] + audit["warnings"]:
        print(f"- {issue}")
    if audit["errors"]:
        raise SystemExit(1)
    print("\nQuestion bank summary:")
    pprint(get_question_bank_summary(), sort_dicts=False)

    examples = {
        "Module 1 questions": get_questions_by_module(1),
        "Module 2 written questions": filter_questions(module=2, question_type="written"),
        "Hard questions": get_questions_by_difficulty("hard"),
    }
    for label, questions in examples.items():
        print(f"\n{label}: {len(questions)}")
        for question in questions[:8]:
            print(f"  {question['id']} - {question['subtopic']}")
        if len(questions) > 8:
            print(f"  ... {len(questions) - 8} more; use the filter helpers for the full list.")


if __name__ == "__main__":
    _run_developer_preview()
