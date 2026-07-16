from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import time
from zoneinfo import ZoneInfo


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _parse_clock(value: str, name: str) -> time:
    try:
        hour, minute = (int(x) for x in value.split(":", 1))
        return time(hour=hour, minute=minute)
    except Exception as exc:
        raise RuntimeError(f"{name} must use HH:MM format") from exc


@dataclass(frozen=True)
class Settings:
    bot_token: str
    chat_id: str
    admin_user_id: int
    database_url: str
    timezone: ZoneInfo
    morning_time: time
    evening_time: time
    questions_per_block: int
    active_collections: tuple[str, ...]
    cycle_mode: str


def load_settings() -> Settings:
    timezone_name = os.getenv("TIMEZONE", "Europe/Paris").strip()
    collections = tuple(
        item.strip()
        for item in os.getenv(
            "ACTIVE_COLLECTIONS",
            "official,mise_en_situation,bonus_culture",
        ).split(",")
        if item.strip()
    )
    allowed = {"official", "mise_en_situation", "bonus_culture"}
    unknown = set(collections) - allowed
    if unknown:
        raise RuntimeError(f"Unknown collections: {sorted(unknown)}")

    cycle_mode = os.getenv("CYCLE_MODE", "loop").strip().lower()
    if cycle_mode not in {"loop", "stop"}:
        raise RuntimeError("CYCLE_MODE must be loop or stop")

    per_block = int(os.getenv("QUESTIONS_PER_BLOCK", "5"))
    if not 1 <= per_block <= 10:
        raise RuntimeError("QUESTIONS_PER_BLOCK must be between 1 and 10")

    return Settings(
        bot_token=_required("BOT_TOKEN"),
        chat_id=_required("TELEGRAM_CHAT_ID"),
        admin_user_id=int(_required("ADMIN_USER_ID")),
        database_url=_required("DATABASE_URL"),
        timezone=ZoneInfo(timezone_name),
        morning_time=_parse_clock(os.getenv("MORNING_TIME", "09:00"), "MORNING_TIME"),
        evening_time=_parse_clock(os.getenv("EVENING_TIME", "19:30"), "EVENING_TIME"),
        questions_per_block=per_block,
        active_collections=collections,
        cycle_mode=cycle_mode,
    )
