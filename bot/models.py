from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Question:
    id: str
    collection: str
    question_fr: str
    question_ru: str
    options: tuple[dict[str, str], ...]
    correct_option_index: int
    explanation_ru: str

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Question":
        options = tuple(raw.get("options", []))
        idx = raw.get("correct_option_index")
        if len(options) != 4:
            raise ValueError(f"{raw.get('id')}: exactly four options required")
        if not isinstance(idx, int) or not 0 <= idx <= 3:
            raise ValueError(f"{raw.get('id')}: invalid correct_option_index")
        return cls(
            id=str(raw["id"]),
            collection=str(raw["collection"]),
            question_fr=str(raw["question_fr"]).strip(),
            question_ru=str(raw["question_ru"]).strip(),
            options=options,
            correct_option_index=idx,
            explanation_ru=str(raw.get("explanation_ru", "")).strip(),
        )
