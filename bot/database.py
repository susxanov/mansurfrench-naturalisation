from __future__ import annotations

import psycopg
from psycopg.rows import dict_row


SCHEMA = """
CREATE TABLE IF NOT EXISTS bot_state (
    singleton BOOLEAN PRIMARY KEY DEFAULT TRUE CHECK (singleton),
    collection_index INTEGER NOT NULL DEFAULT 0,
    question_index INTEGER NOT NULL DEFAULT 0,
    cycle_number INTEGER NOT NULL DEFAULT 1,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO bot_state (singleton)
VALUES (TRUE)
ON CONFLICT (singleton) DO NOTHING;

CREATE TABLE IF NOT EXISTS publication_log (
    id BIGSERIAL PRIMARY KEY,
    question_id TEXT NOT NULL,
    collection_name TEXT NOT NULL,
    cycle_number INTEGER NOT NULL,
    block_name TEXT NOT NULL,
    telegram_message_id BIGINT,
    published_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS publication_log_question_idx
ON publication_log (question_id, cycle_number);
"""


class Database:
    def __init__(self, database_url: str):
        self.database_url = database_url

    def connect(self):
        return psycopg.connect(self.database_url, row_factory=dict_row)

    def initialize(self) -> None:
        with self.connect() as conn:
            conn.execute(SCHEMA)
            conn.commit()

    def get_state(self) -> dict:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT collection_index, question_index, cycle_number "
                "FROM bot_state WHERE singleton = TRUE"
            ).fetchone()
            if row is None:
                raise RuntimeError("bot_state was not initialized")
            return dict(row)

    def set_state(
        self,
        *,
        collection_index: int,
        question_index: int,
        cycle_number: int,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE bot_state
                SET collection_index = %s,
                    question_index = %s,
                    cycle_number = %s,
                    updated_at = NOW()
                WHERE singleton = TRUE
                """,
                (collection_index, question_index, cycle_number),
            )
            conn.commit()

    def log_publication(
        self,
        *,
        question_id: str,
        collection_name: str,
        cycle_number: int,
        block_name: str,
        telegram_message_id: int | None,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO publication_log (
                    question_id, collection_name, cycle_number,
                    block_name, telegram_message_id
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    question_id,
                    collection_name,
                    cycle_number,
                    block_name,
                    telegram_message_id,
                ),
            )
            conn.commit()

    def count_published(self, cycle_number: int) -> int:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS count FROM publication_log WHERE cycle_number = %s",
                (cycle_number,),
            ).fetchone()
            return int(row["count"])

    def reset(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE bot_state
                SET collection_index = 0,
                    question_index = 0,
                    cycle_number = cycle_number + 1,
                    updated_at = NOW()
                WHERE singleton = TRUE
                """
            )
            conn.commit()
