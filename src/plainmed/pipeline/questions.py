"""Understanding checks and clinician questions.

Both are generated deterministically from validated, parsed content only -
never from raw model text - so a wrong answer can always be traced back to a
real report line.
"""

from __future__ import annotations

import hashlib
import random
from typing import List, Optional

from plainmed.glossary import Glossary
from plainmed.schemas import (
    ATTENTION_STATUSES,
    ClinicianQuestion,
    ComprehensionQuestion,
    LabValue,
    ReportDocument,
    ValueStatus,
)

_MAX_CLINICIAN_QUESTIONS = 8

# Short status phrases for sentences that already establish whose report it is.
_STATUS_PHRASES = {
    ValueStatus.flagged_high: "marked high",
    ValueStatus.flagged_low: "marked low",
    ValueStatus.flagged_abnormal: "marked abnormal",
    ValueStatus.above_range: "above the listed reference range",
    ValueStatus.below_range: "below the listed reference range",
    ValueStatus.within_range: "within the listed reference range",
    ValueStatus.no_range: "listed without a reference range",
}


def _value_phrase(value: LabValue) -> str:
    phrase = f"{value.analyte} at {value.raw_value}"
    if value.unit:
        phrase += f" {value.unit}"
    if value.ref_raw:
        phrase += f" (listed reference range {value.ref_raw})"
    return phrase


def build_clinician_questions(
    doc: ReportDocument, glossary: Glossary
) -> List[ClinicianQuestion]:
    questions: List[ClinicianQuestion] = []

    for value in doc.values:
        if value.status in ATTENTION_STATUSES:
            label = _STATUS_PHRASES[value.status]
            questions.append(
                ClinicianQuestion(
                    text=(
                        f"My report shows {_value_phrase(value)}, which is "
                        f"{label}. What does this mean in my situation, and is "
                        "any follow-up needed?"
                    ),
                    span_ids=[value.span_id],
                )
            )

    for value in doc.values:
        if value.status == ValueStatus.no_range and value.flag is None:
            questions.append(
                ClinicianQuestion(
                    text=(
                        f"My report lists {value.analyte} without a reference "
                        "range. What range applies to me, and is this result "
                        "where you would expect it?"
                    ),
                    span_ids=[value.span_id],
                )
            )

    for value in doc.values:
        if glossary.lookup(value.analyte) is None:
            questions.append(
                ClinicianQuestion(
                    text=(
                        f"My report mentions “{value.analyte}”, which I "
                        "could not find an explanation for. What does this test "
                        "measure?"
                    ),
                    span_ids=[value.span_id],
                )
            )

    if doc.unparsed_span_ids:
        questions.append(
            ClinicianQuestion(
                text=(
                    "Some parts of my report were hard to read. Could we go "
                    "through the report together to make sure I have not missed "
                    "anything important?"
                ),
                span_ids=list(doc.unparsed_span_ids),
            )
        )

    if not questions and doc.values:
        questions.append(
            ClinicianQuestion(
                text=(
                    "Is any follow-up or repeat testing needed based on these "
                    "results, and when should they next be checked?"
                ),
                span_ids=[v.span_id for v in doc.values],
            )
        )

    return questions[:_MAX_CLINICIAN_QUESTIONS]


def _stable_rng(doc: ReportDocument) -> random.Random:
    digest = hashlib.sha256(doc.raw_text.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def _attention_question(
    doc: ReportDocument, rng: random.Random
) -> Optional[ComprehensionQuestion]:
    attention = [v for v in doc.values if v.status in ATTENTION_STATUSES]
    if not attention or len(doc.values) < 2:
        return None
    target = attention[0]
    distractors = [
        v.analyte
        for v in doc.values
        if v.analyte != target.analyte and v.status not in ATTENTION_STATUSES
    ]
    if not distractors:
        return None
    rng.shuffle(distractors)
    options = distractors[:3] + [target.analyte]
    rng.shuffle(options)
    span = doc.span_by_id(target.span_id)
    return ComprehensionQuestion(
        question=(
            "According to your report, which of these results is "
            f"{_STATUS_PHRASES[target.status]}?"
        ),
        options=options,
        answer_index=options.index(target.analyte),
        span_ids=[target.span_id],
        explanation=f"The report line reads: “{span.text.strip()}”",
    )


def _value_recall_question(
    doc: ReportDocument, rng: random.Random, exclude_span: Optional[str]
) -> Optional[ComprehensionQuestion]:
    candidates = [
        v
        for v in doc.values
        if v.span_id != exclude_span and v.value is not None
    ]
    if not candidates:
        return None
    target = rng.choice(candidates)
    unit = f" {target.unit}" if target.unit else ""
    correct = f"{target.raw_value}{unit}"
    distractors = []
    for other in doc.values:
        option = f"{other.raw_value}{unit}"
        if other.span_id != target.span_id and option != correct:
            distractors.append(option)
    if not distractors:
        return None
    rng.shuffle(distractors)
    options = distractors[:3] + [correct]
    rng.shuffle(options)
    span = doc.span_by_id(target.span_id)
    return ComprehensionQuestion(
        question=f"What value does your report list for {target.analyte}?",
        options=options,
        answer_index=options.index(correct),
        span_ids=[target.span_id],
        explanation=f"The report line reads: “{span.text.strip()}”",
    )


def build_comprehension_questions(doc: ReportDocument) -> List[ComprehensionQuestion]:
    """Up to two short questions, each grounded in a single report line."""
    rng = _stable_rng(doc)
    questions: List[ComprehensionQuestion] = []

    first = _attention_question(doc, rng)
    if first is not None:
        questions.append(first)

    exclude = first.span_ids[0] if first is not None else None
    second = _value_recall_question(doc, rng, exclude_span=exclude)
    if second is not None:
        questions.append(second)

    if len(questions) < 2:
        extra = _value_recall_question(
            doc, rng, exclude_span=questions[0].span_ids[0] if questions else None
        )
        if extra is not None and all(
            q.question != extra.question for q in questions
        ):
            questions.append(extra)

    return questions[:2]
