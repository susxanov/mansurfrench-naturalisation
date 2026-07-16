from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from telegram import Bot

from bot.database import Database
from bot.models import Question

LOGGER = logging.getLogger(__name__)


def _clip(text: str, limit: int) -> str:
    clean = " ".join(text.split())
    if len(clean) <= limit:
        return clean
    return clean[: max(1, limit - 1)].rstrip() + "…"


def _poll_question(question: Question) -> str:
    combined = f"{question.question_fr}\n\n{question.question_ru}"
    return _clip(combined, 300)


def _poll_options(question: Question) -> list[str]:
    return [
        _clip(f"{option['fr']} — {option['ru']}", 100)
        for option in question.options
    ]


def _poll_explanation(question: Question) -> str:
    return _clip(question.explanation_ru, 200)


@dataclass
class Publisher:
    bot: Bot
    chat_id: str
    db: Database
    bank: dict[str, list[Question]]
    collection_order: tuple[str, ...]
    cycle_mode: str

    def _next_question(self, state: dict) -> tuple[Question | None, dict]:
        collection_index = int(state["collection_index"])
        question_index = int(state["question_index"])
        cycle_number = int(state["cycle_number"])

        while collection_index < len(self.collection_order):
            collection_name = self.collection_order[collection_index]
            items = self.bank[collection_name]

            if question_index < len(items):
                question = items[question_index]
                next_state = {
                    "collection_index": collection_index,
                    "question_index": question_index + 1,
                    "cycle_number": cycle_number,
                }
                return question, next_state

            collection_index += 1
            question_index = 0

        if self.cycle_mode == "stop":
            return None, {
                "collection_index": collection_index,
                "question_index": 0,
                "cycle_number": cycle_number,
            }

        return self._next_question(
            {
                "collection_index": 0,
                "question_index": 0,
                "cycle_number": cycle_number + 1,
            }
        )

    async def publish_block(self, *, count: int, block_name: str) -> int:
        published = 0

        for _ in range(count):
            state = self.db.get_state()
            question, next_state = self._next_question(state)
            if question is None:
                LOGGER.warning("Question bank is exhausted and CYCLE_MODE=stop")
                break

            message = await self.bot.send_poll(
                chat_id=self.chat_id,
                question=_poll_question(question),
                options=_poll_options(question),
                type="quiz",
                correct_option_ids=[question.correct_option_index],
                explanation=_poll_explanation(question),
                is_anonymous=True,
                allows_multiple_answers=False,
            )

            self.db.log_publication(
                question_id=question.id,
                collection_name=question.collection,
                cycle_number=int(next_state["cycle_number"]),
                block_name=block_name,
                telegram_message_id=message.message_id,
            )
            self.db.set_state(**next_state)
            published += 1

            # Small pause to avoid bursts and keep the channel readable.
            await asyncio.sleep(1.2)

        return published
