from __future__ import annotations

import json
from pathlib import Path

from bot.models import Question


FILENAMES = {
    "official": "official_questions_258_audited.json",
    "mise_en_situation": "mise_en_situation_100.json",
    "bonus_culture": "bonus_culture_60.json",
}


def _find_file(filename: str) -> Path:
    candidates = [
        Path("data") / filename,
        Path(filename),
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(
        f"Cannot find {filename}. Put it in the repository data/ folder."
    )


def load_question_bank(collections: tuple[str, ...]) -> dict[str, list[Question]]:
    bank: dict[str, list[Question]] = {}
    seen_ids: set[str] = set()

    for collection in collections:
        path = _find_file(FILENAMES[collection])
        raw_items = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw_items, list):
            raise ValueError(f"{path}: top-level JSON must be a list")

        items: list[Question] = []
        for raw in raw_items:
            question = Question.from_dict(raw)
            if question.id in seen_ids:
                raise ValueError(f"Duplicate question ID: {question.id}")
            if question.collection != collection:
                raise ValueError(
                    f"{question.id}: collection={question.collection}, expected {collection}"
                )
            seen_ids.add(question.id)
            items.append(question)

        if not items:
            raise ValueError(f"{path}: no questions found")
        bank[collection] = items

    return bank
