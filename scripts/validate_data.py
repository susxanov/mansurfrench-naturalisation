#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

FILES = {
    "official": "official_questions_258_audited.json",
    "mise_en_situation": "mise_en_situation_100.json",
    "bonus_culture": "bonus_culture_60.json",
}

errors: list[str] = []

for collection, filename in FILES.items():
    candidates = [Path("data") / filename, Path(filename)]
    path = next((p for p in candidates if p.exists()), None)
    if path is None:
        errors.append(f"Missing: {filename}")
        continue

    items = json.loads(path.read_text(encoding="utf-8"))
    for position, q in enumerate(items, start=1):
        qid = q.get("id", f"{filename}:{position}")
        if q.get("collection") != collection:
            errors.append(f"{qid}: incorrect collection")
        options = q.get("options", [])
        if len(options) != 4:
            errors.append(f"{qid}: expected four options")
            continue
        idx = q.get("correct_option_index")
        if not isinstance(idx, int) or not 0 <= idx <= 3:
            errors.append(f"{qid}: invalid correct index")
        question = f"{q.get('question_fr', '')}\n\n{q.get('question_ru', '')}"
        if len(question) > 300:
            print(f"WARNING {qid}: poll question will be shortened ({len(question)} chars)")
        for option in options:
            text = f"{option.get('fr', '')} — {option.get('ru', '')}"
            if len(text) > 100:
                print(f"WARNING {qid}: option will be shortened ({len(text)} chars)")
        if len(q.get("explanation_ru", "")) > 200:
            print(f"WARNING {qid}: explanation will be shortened")

print(f"Errors: {len(errors)}")
for error in errors:
    print("ERROR:", error)
raise SystemExit(1 if errors else 0)
