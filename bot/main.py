from __future__ import annotations

import logging
from datetime import datetime

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from bot.config import Settings, load_settings
from bot.data_loader import load_question_bank
from bot.database import Database
from bot.publisher import Publisher


logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
LOGGER = logging.getLogger(__name__)


def _is_admin(update: Update, settings: Settings) -> bool:
    return bool(
        update.effective_user
        and update.effective_user.id == settings.admin_user_id
    )


async def status_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    settings: Settings = context.application.bot_data["settings"]
    if not _is_admin(update, settings):
        return

    db: Database = context.application.bot_data["db"]
    state = db.get_state()
    collections = settings.active_collections
    collection_index = int(state["collection_index"])
    current = (
        collections[collection_index]
        if collection_index < len(collections)
        else "completed"
    )
    published = db.count_published(int(state["cycle_number"]))

    text = (
        "Статус бота\n\n"
        f"Цикл: {state['cycle_number']}\n"
        f"Текущая коллекция: {current}\n"
        f"Позиция в коллекции: {state['question_index']}\n"
        f"Опубликовано в этом цикле: {published}\n"
        f"Время сервера: {datetime.now(settings.timezone):%Y-%m-%d %H:%M}"
    )
    await update.effective_message.reply_text(text)


async def force_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    settings: Settings = context.application.bot_data["settings"]
    if not _is_admin(update, settings):
        return

    count = settings.questions_per_block
    if context.args:
        try:
            count = int(context.args[0])
        except ValueError:
            await update.effective_message.reply_text("Используй: /force 5")
            return
    count = max(1, min(count, 10))

    publisher: Publisher = context.application.bot_data["publisher"]
    sent = await publisher.publish_block(count=count, block_name="manual")
    await update.effective_message.reply_text(f"Отправлено вопросов: {sent}")


async def reset_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    settings: Settings = context.application.bot_data["settings"]
    if not _is_admin(update, settings):
        return

    db: Database = context.application.bot_data["db"]
    db.reset()
    await update.effective_message.reply_text(
        "Цикл сброшен. Следующая публикация начнётся с первого официального вопроса."
    )


async def scheduled_publish(
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    publisher: Publisher = context.application.bot_data["publisher"]
    settings: Settings = context.application.bot_data["settings"]
    block_name = str(context.job.data)
    sent = await publisher.publish_block(
        count=settings.questions_per_block,
        block_name=block_name,
    )
    LOGGER.info("Scheduled block %s: sent %s questions", block_name, sent)


def main() -> None:
    settings = load_settings()
    bank = load_question_bank(settings.active_collections)

    db = Database(settings.database_url)
    db.initialize()

    application = Application.builder().token(settings.bot_token).build()
    publisher = Publisher(
        bot=application.bot,
        chat_id=settings.chat_id,
        db=db,
        bank=bank,
        collection_order=settings.active_collections,
        cycle_mode=settings.cycle_mode,
    )

    application.bot_data["settings"] = settings
    application.bot_data["db"] = db
    application.bot_data["publisher"] = publisher

    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("force", force_command))
    application.add_handler(CommandHandler("reset_cycle", reset_command))

    # Monday=0 ... Saturday=5. Sunday is excluded.
    weekdays = (0, 1, 2, 3, 4, 5)
    application.job_queue.run_daily(
        scheduled_publish,
        time=settings.morning_time.replace(tzinfo=settings.timezone),
        days=weekdays,
        data="morning",
        name="morning",
    )
    application.job_queue.run_daily(
        scheduled_publish,
        time=settings.evening_time.replace(tzinfo=settings.timezone),
        days=weekdays,
        data="evening",
        name="evening",
    )

    LOGGER.info(
        "Bot started. Collections=%s, schedule=%s/%s, timezone=%s",
        settings.active_collections,
        settings.morning_time,
        settings.evening_time,
        settings.timezone,
    )
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
